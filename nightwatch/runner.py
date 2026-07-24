from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import html
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from typing import Any, Callable, Protocol

from .clock import isoformat
from .config import resolve_pi_route
from .errors import (
    ExternalExecutionDisabled,
    RunnerCleanupFailure,
    RunnerFailure,
    RunnerStopped,
    RunnerTimeout,
    ValidationError,
)
from .models import Brief, TaskSpec


@dataclass(frozen=True)
class TaskContext:
    brief: Brief
    task: TaskSpec
    attempt: int
    workspace_root: Path
    prior_artifacts: tuple[str, ...]
    handoff: dict[str, Any] | None
    fresh_context: bool
    now: Callable[[], datetime]
    heartbeat: Callable[[str], None]
    supervisor_heartbeat: Callable[[str], None]
    emit: Callable[[str, dict[str, Any]], None]
    should_stop: Callable[[], str | None]


@dataclass(frozen=True)
class RunResult:
    files: dict[str, str]
    summary: str
    handoff: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Runner(Protocol):
    name: str
    external_services_enabled: bool

    def execute(self, context: TaskContext) -> RunResult: ...


class SyntheticRunner:
    name = "synthetic"
    external_services_enabled = False

    def execute(self, context: TaskContext) -> RunResult:
        task = context.task
        stop_reason = context.should_stop()
        if stop_reason:
            raise RunnerStopped(stop_reason)
        context.heartbeat("accepted")
        context.supervisor_heartbeat("runner-accepted")
        fail_attempts = self._attempt_set(task.settings.get("fail_attempts", []), "fail_attempts")
        timeout_attempts = self._attempt_set(task.settings.get("timeout_attempts", []), "timeout_attempts")
        if context.attempt in timeout_attempts:
            context.heartbeat("simulated-timeout")
            context.supervisor_heartbeat("runner-reported-timeout")
            raise RunnerTimeout(f"synthetic timeout on attempt {context.attempt}")
        if context.attempt in fail_attempts:
            context.heartbeat("simulated-failure")
            context.supervisor_heartbeat("runner-reported-failure")
            raise RunnerFailure(f"synthetic transient failure on attempt {context.attempt}")
        if task.handoff_from and context.handoff is None:
            raise RunnerFailure(f"required handoff is missing: {task.handoff_from}")
        if task.kind == "review" and not context.fresh_context:
            raise RunnerFailure("fresh-eyes review was not given a fresh context")

        if task.kind == "creative":
            result = self._creative_result(context)
        else:
            result = self._text_result(context)
        context.heartbeat("completed")
        context.supervisor_heartbeat("runner-completed")
        return result

    @staticmethod
    def _attempt_set(value: Any, label: str) -> set[int]:
        if not isinstance(value, list) or not all(isinstance(item, int) and item > 0 for item in value):
            raise ValidationError(f"synthetic task setting {label} must be a list of positive integers")
        return set(value)

    def _text_result(self, context: TaskContext) -> RunResult:
        task = context.task
        handoff_note = "None required."
        if context.handoff:
            handoff_note = (
                f"Loaded handoff from `{context.handoff['from_task']}` while retaining the original brief. "
                f"Next step: {context.handoff['next_step']}"
            )
        review_note = (
            "Fresh context confirmed: the review received the original brief, declared artifacts, and handoff only—no predecessor conversation."
            if task.fresh_context
            else "Task ran in an isolated synthetic attempt context."
        )
        fixture_content = task.settings.get("fixture_content")
        if fixture_content is not None:
            if not isinstance(fixture_content, str) or not fixture_content.strip():
                raise ValidationError("synthetic fixture_content must be a non-empty string")
            if len(fixture_content) > 10_000:
                raise ValidationError("synthetic fixture_content must be at most 10000 characters")
            fixture_section = f"## Fixture output\n\n{fixture_content.strip()}\n\n"
        else:
            fixture_section = ""
        body = (
            "# Synthetic task artifact\n\n"
            "> **Synthetic demonstration.** No model, network service, or external agent was called.\n\n"
            f"## Task\n\n**{task.title}** (`{task.id}`)\n\n"
            f"## Objective retained\n\n{context.brief.objective}\n\n"
            f"## Continuity\n\n{handoff_note}\n\n"
            f"## Context boundary\n\n{review_note}\n\n"
            f"{fixture_section}"
            f"## Result\n\nDeterministic fixture completed on attempt {context.attempt} using logical model route "
            f"`{task.model_route}`.\n"
        )
        files = {output: body for output in task.outputs}
        handoff = None
        if task.produce_handoff:
            handoff = {
                "schema_version": 1,
                "from_task": task.id,
                "completed": f"Completed {task.title} in the synthetic workflow.",
                "next_step": task.settings.get("next_step", "Review the declared artifacts against the original brief."),
                "artifacts": list(task.outputs),
                "risks": list(task.settings.get("risks", ["Synthetic evidence does not establish production reliability."])),
                "created_at": isoformat(context.now()),
            }
        return RunResult(files=files, summary=f"{task.title} completed", handoff=handoff)

    def _creative_result(self, context: TaskContext) -> RunResult:
        task = context.task
        scores = task.settings.get("scores")
        threshold = task.settings.get("quality_threshold")
        if not isinstance(scores, list) or not scores or not all(isinstance(score, int) and 0 <= score <= 100 for score in scores):
            raise ValidationError("creative scores must be a non-empty list of integers from 0 to 100")
        if not isinstance(threshold, int) or not 0 <= threshold <= 100:
            raise ValidationError("creative quality_threshold must be an integer from 0 to 100")
        iteration_outputs = [path for path in task.outputs if path.lower().endswith(".svg")]
        report_outputs = [path for path in task.outputs if not path.lower().endswith(".svg")]
        expected_iterations = next(
            (index for index, score in enumerate(scores, start=1) if score >= threshold),
            len(scores),
        )
        if len(iteration_outputs) != expected_iterations or len(report_outputs) != 1:
            raise ValidationError(
                "creative task requires one SVG per expected iteration and exactly one report output"
            )

        files: dict[str, str] = {}
        completed_scores: list[int] = []
        for index, score in enumerate(scores, start=1):
            stop_reason = context.should_stop()
            if stop_reason:
                raise RunnerStopped(stop_reason)
            completed_scores.append(score)
            context.heartbeat(f"creative-iteration-{index}")
            context.supervisor_heartbeat(f"creative-iteration-{index}")
            context.emit(
                "creative_iteration",
                {"task_id": task.id, "iteration": index, "score": score, "threshold": threshold},
            )
            files[iteration_outputs[index - 1]] = self._iteration_svg(index, score, threshold)
            if score >= threshold:
                break
        report = [
            "# Synthetic creative loop",
            "",
            "> **Synthetic demonstration.** Scores are deterministic fixture values, not model evaluation or user research.",
            "",
            "| Iteration | Fixture score | Decision |",
            "|---:|---:|---|",
        ]
        for index, score in enumerate(completed_scores, start=1):
            report.append(f"| {index} | {score} | {'threshold reached' if score >= threshold else 'revise'} |")
        report.extend(
            [
                "",
                f"The loop stopped after {len(completed_scores)} iterations at a fixture threshold of {threshold}.",
                "Each SVG is a locally generated synthetic screenshot card.",
            ]
        )
        files[report_outputs[0]] = "\n".join(report) + "\n"
        return RunResult(
            files=files,
            summary=f"Creative loop completed {len(completed_scores)} iterations",
            metadata={"iterations": len(completed_scores), "scores": completed_scores, "threshold": threshold},
        )

    @staticmethod
    def _iteration_svg(iteration: int, score: int, threshold: int) -> str:
        progress = max(0, min(100, score)) * 5.2
        status = "Threshold reached" if score >= threshold else "Revise and inspect again"
        accent = "#2dd4bf" if score >= threshold else "#f4b860"
        safe_status = html.escape(status)
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="420" viewBox="0 0 720 420" role="img" aria-labelledby="title desc">
  <title id="title">Synthetic creative iteration {iteration}</title>
  <desc id="desc">A synthetic screenshot card with fixture quality score {score} out of 100.</desc>
  <rect width="720" height="420" rx="24" fill="#0b1016"/>
  <rect x="36" y="36" width="648" height="348" rx="18" fill="#121a23" stroke="#263646"/>
  <text x="72" y="92" fill="#8fa3b8" font-family="Arial, sans-serif" font-size="15" letter-spacing="2">SYNTHETIC DEMONSTRATION</text>
  <text x="72" y="145" fill="#f5f7fa" font-family="Arial, sans-serif" font-size="32" font-weight="700">Creative pass {iteration:02d}</text>
  <text x="72" y="190" fill="#aebdca" font-family="Arial, sans-serif" font-size="18">Screenshot → critique → revision</text>
  <rect x="72" y="238" width="520" height="14" rx="7" fill="#263646"/>
  <rect x="72" y="238" width="{progress:.1f}" height="14" rx="7" fill="{accent}"/>
  <text x="72" y="302" fill="{accent}" font-family="Arial, sans-serif" font-size="52" font-weight="700">{score}</text>
  <text x="160" y="302" fill="#8fa3b8" font-family="Arial, sans-serif" font-size="18">/ 100 fixture score</text>
  <text x="72" y="346" fill="#f5f7fa" font-family="Arial, sans-serif" font-size="17">{safe_status}</text>
</svg>
'''


class PiJsonRunner:
    """Optional Pi worker transport. It is deliberately not a sandbox."""

    name = "pi-json"
    external_services_enabled = True

    def __init__(self, config: dict[str, Any], *, cli_external_approval: bool):
        if cli_external_approval is not True or config["external_services"]["enabled"] is not True:
            raise ExternalExecutionDisabled(
                "Pi execution requires both --enable-external and external_services.enabled=true"
            )
        self.config = config
        self.pi_config = config["runner"]["pi"]
        self.fault_injection_enabled = config.get("fault_injection", {}).get("enabled", False)

    def execute(self, context: TaskContext) -> RunResult:
        provider, model = resolve_pi_route(self.config, context.task.model_route)
        if len(context.task.outputs) != 1:
            raise ValidationError("Pi JSON tasks currently require exactly one declared output")
        interrupt_after = self._fault_interrupt_after(context)
        if context.task.produce_handoff:
            self._validate_handoff_settings(context.task)
        prompt = self._public_instruction(context)
        command = [
            *self._resolve_command(self.pi_config["command"]),
            "--mode",
            "json",
            "--no-session",
            "--no-approve",
            "--no-context-files",
            "--no-extensions",
            "--no-skills",
            "--no-prompt-templates",
            "--tools",
            ",".join(self.pi_config["tools"]),
            "--provider",
            provider,
            "--model",
            model,
            prompt,
        ]
        started = time.monotonic()
        context.heartbeat("pi-process-started")
        process_options: dict[str, Any] = {}
        if os.name == "nt":
            process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            process_options["start_new_session"] = True
        try:
            process = subprocess.Popen(
                command,
                cwd=context.workspace_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                **process_options,
            )
        except OSError as exc:
            raise RunnerFailure(f"could not start Pi: {exc}") from exc
        context.emit(
            "pi_process_started",
            {
                "task_id": context.task.id,
                "attempt": context.attempt,
                "provider": provider,
                "model": model,
                "fault_interrupt_after_seconds": interrupt_after,
            },
        )
        stdout = ""
        stderr = ""
        while True:
            reason = context.should_stop()
            if reason:
                self._terminate_process(process)
                raise RunnerStopped(reason)
            elapsed = time.monotonic() - started
            if interrupt_after is not None and elapsed >= interrupt_after:
                context.heartbeat("fault-injection-interrupt")
                context.supervisor_heartbeat("fault-injection-interrupt")
                context.emit(
                    "fault_injection_interrupt",
                    {
                        "task_id": context.task.id,
                        "attempt": context.attempt,
                        "after_seconds": interrupt_after,
                    },
                )
                self._terminate_process(process)
                raise RunnerFailure(
                    f"fault injection deliberately interrupted Pi attempt {context.attempt} "
                    f"after {interrupt_after:g}s"
                )
            if elapsed >= context.task.timeout_seconds:
                self._terminate_process(process)
                raise RunnerTimeout(f"Pi exceeded {context.task.timeout_seconds:g}s timeout")
            try:
                stdout, stderr = process.communicate(timeout=min(0.5, context.task.timeout_seconds - elapsed))
                break
            except subprocess.TimeoutExpired:
                context.heartbeat("pi-process-running")
                context.supervisor_heartbeat("waiting-for-pi")
        if process.returncode != 0:
            tail = stderr.strip().splitlines()[-1] if stderr.strip() else "no stderr detail"
            raise RunnerFailure(f"Pi exited with {process.returncode}: {tail}")
        acknowledgement = f"NIGHTWATCH_TASK_ACK:{context.task.id}"
        text = self._extract_final_text(stdout, acknowledgement)
        self._validate_required_phrases(context.task, text)
        stream_metrics = self._stream_metrics(stdout, context)
        context.emit(
            "pi_result_validated",
            {
                "task_id": context.task.id,
                "attempt": context.attempt,
                "provider": provider,
                "model": model,
                **stream_metrics,
            },
        )
        handoff = self._build_handoff(context) if context.task.produce_handoff else None
        context.heartbeat("completed")
        context.supervisor_heartbeat("runner-completed")
        return RunResult(
            files={context.task.outputs[0]: text + "\n"},
            summary="Pi JSON task completed",
            handoff=handoff,
            metadata={
                "provider": provider,
                "model": model,
                "task_acknowledged": True,
                **stream_metrics,
            },
        )

    def _fault_interrupt_after(self, context: TaskContext) -> float | None:
        specification = context.task.settings.get("fault_injection")
        if specification is None:
            return None
        if not self.fault_injection_enabled:
            raise ValidationError("task fault injection requires fault_injection.enabled=true")
        if not isinstance(specification, dict):
            raise ValidationError("task fault_injection must be an object")
        attempts = specification.get("interrupt_attempts")
        after_seconds = specification.get("after_seconds")
        if not isinstance(attempts, list) or not attempts or not all(
            isinstance(attempt, int) and not isinstance(attempt, bool) and attempt > 0
            for attempt in attempts
        ):
            raise ValidationError("fault_injection.interrupt_attempts must be positive integers")
        if (
            not isinstance(after_seconds, (int, float))
            or isinstance(after_seconds, bool)
            or not 0.1 <= after_seconds <= 30
        ):
            raise ValidationError("fault_injection.after_seconds must be from 0.1 to 30")
        return float(after_seconds) if context.attempt in attempts else None

    @staticmethod
    def _validate_required_phrases(task: TaskSpec, artifact: str) -> None:
        phrases = task.settings.get("required_output_phrases", [])
        if not isinstance(phrases, list) or not all(
            isinstance(phrase, str) and phrase.strip() and len(phrase) <= 200 for phrase in phrases
        ):
            raise ValidationError("required_output_phrases must be strings of 1 to 200 characters")
        folded = artifact.casefold()
        missing = [phrase for phrase in phrases if phrase.casefold() not in folded]
        if missing:
            raise RunnerFailure(f"Pi artifact missing required phrase(s): {missing}")

    @staticmethod
    def _stream_metrics(stdout: str, context: TaskContext) -> dict[str, Any]:
        event_count = 0
        tool_calls = 0
        raw_read_paths: list[str] = []
        for event in PiJsonRunner._json_events(stdout):
            event_count += 1
            if event.get("type") != "tool_execution_start":
                continue
            tool_calls += 1
            if event.get("toolName") != "read":
                continue
            args = event.get("args")
            if not isinstance(args, dict) or not isinstance(args.get("path"), str):
                raise RunnerFailure("Pi read event did not include a valid path")
            raw_read_paths.append(args["path"])

        workspace_root = context.workspace_root.resolve()
        read_paths: list[str] = []
        for raw_path in raw_read_paths:
            candidate = Path(raw_path)
            resolved = candidate.resolve() if candidate.is_absolute() else (workspace_root / candidate).resolve()
            try:
                relative = resolved.relative_to(workspace_root).as_posix()
            except ValueError as exc:
                raise RunnerFailure(f"Pi read outside the isolated workspace: {raw_path!r}") from exc
            read_paths.append(relative)
        read_paths = sorted(set(read_paths))
        if context.fresh_context:
            required = sorted(PiJsonRunner._workspace_relative(path) for path in context.prior_artifacts)
            missing = [path for path in required if path not in read_paths]
            if missing:
                raise RunnerFailure(f"fresh review did not read predecessor artifact(s): {missing}")
        return {
            "stream_events": event_count,
            "tool_calls": tool_calls,
            "read_paths": read_paths,
        }

    @staticmethod
    def _validate_handoff_settings(task: TaskSpec) -> tuple[str, list[str]]:
        next_step = task.settings.get("next_step")
        risks = task.settings.get(
            "risks", ["External model output requires independent human review."]
        )
        if not isinstance(next_step, str) or not next_step.strip():
            raise ValidationError("Pi task producing a handoff requires settings.next_step")
        if not isinstance(risks, list) or not all(isinstance(risk, str) and risk.strip() for risk in risks):
            raise ValidationError("Pi handoff risks must be a list of non-empty strings")
        return next_step.strip(), risks

    @staticmethod
    def _build_handoff(context: TaskContext) -> dict[str, Any]:
        next_step, risks = PiJsonRunner._validate_handoff_settings(context.task)
        return {
            "schema_version": 1,
            "from_task": context.task.id,
            "completed": f"Pi produced an acknowledged artifact for {context.task.title}.",
            "next_step": next_step,
            "artifacts": list(context.task.outputs),
            "risks": risks,
            "created_at": isoformat(context.now()),
        }

    @staticmethod
    def _resolve_command(command: str) -> list[str]:
        resolved = shutil.which(command)
        if not resolved:
            raise RunnerFailure(f"Pi command was not found on PATH: {command!r}")
        resolved_path = Path(resolved)
        if os.name == "nt" and resolved_path.suffix.lower() in {".cmd", ".bat"}:
            npm_root = resolved_path.parent
            node = npm_root / "node.exe"
            node_command = str(node) if node.is_file() else shutil.which("node")
            package_candidates = (
                "@earendil-works/pi-coding-agent",
                "@mariozechner/pi-coding-agent",
            )
            if node_command:
                for package in package_candidates:
                    cli = npm_root / "node_modules" / package / "dist" / "cli.js"
                    if cli.is_file():
                        return [node_command, str(cli)]
        return [resolved]

    @staticmethod
    def _terminate_process(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            process.communicate()
            return
        cleanup_error = False
        if os.name == "nt":
            try:
                result = subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                    check=False,
                )
                cleanup_error = result.returncode != 0 and process.poll() is None
            except (OSError, subprocess.TimeoutExpired):
                cleanup_error = True
        else:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except (OSError, ProcessLookupError):
                cleanup_error = process.poll() is None
        if cleanup_error:
            process.kill()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            cleanup_error = True
            if os.name == "nt":
                process.kill()
            else:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except (OSError, ProcessLookupError):
                    process.kill()
            process.communicate()
        if cleanup_error:
            raise RunnerCleanupFailure("could not prove runner process-tree termination; retry blocked")

    @staticmethod
    def _public_instruction(context: TaskContext) -> str:
        acknowledgement = f"NIGHTWATCH_TASK_ACK:{context.task.id}"
        handoff = json.dumps(context.handoff, sort_keys=True, separators=(",", ":")) if context.handoff else "none"
        objective = " ".join(context.brief.objective.split())
        title = " ".join(context.task.title.split())
        prior_artifacts = [PiJsonRunner._workspace_relative(path) for path in context.prior_artifacts]
        predecessor_context = json.dumps(prior_artifacts, separators=(",", ":")) if prior_artifacts else "none"
        review_instruction = (
            "This is a fresh-context review: use the read tool to inspect each available predecessor artifact "
            "before answering, and identify the reviewed path in the artifact."
            if context.fresh_context and prior_artifacts
            else "Use only the original objective and declared evidence."
        )
        return (
            f"Start your response with exactly {acknowledgement} on its own line, then complete one bounded "
            f"Nightwatch task. Original objective: {objective} | Task: {title} | Nightwatch output record: "
            f"{context.task.outputs[0]} (return content only; do not write the file) | Available predecessor "
            f"artifacts relative to your current workspace: {predecessor_context} | Continuation handoff "
            f"(its artifact paths are run-root-relative): "
            f"{handoff} | {review_instruction} Return concise Markdown for the declared output. Do not infer "
            "permission beyond that output. Nightwatch will persist the result."
        )

    @staticmethod
    def _workspace_relative(path: str) -> str:
        prefix = "workspace/"
        if not path.startswith(prefix) or len(path) == len(prefix):
            raise ValidationError(f"workspace artifact path is invalid: {path!r}")
        return path[len(prefix):]

    @staticmethod
    def _json_events(stdout: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for line_number, line in enumerate(stdout.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RunnerFailure(f"Pi JSON stream is malformed at line {line_number}") from exc
            if not isinstance(event, dict):
                raise RunnerFailure(f"Pi JSON event must be an object at line {line_number}")
            events.append(event)
        return events

    @staticmethod
    def _extract_final_text(stdout: str, expected_acknowledgement: str) -> str:
        final = ""
        for event in PiJsonRunner._json_events(stdout):
            if event.get("type") != "message_end":
                continue
            message = event.get("message")
            if not isinstance(message, dict) or message.get("role") != "assistant":
                continue
            parts = message.get("content")
            if not isinstance(parts, list):
                continue
            text_parts = [
                part["text"]
                for part in parts
                if isinstance(part, dict)
                and part.get("type") == "text"
                and isinstance(part.get("text"), str)
            ]
            if text_parts:
                final = "\n".join(text_parts).strip()
        if not final:
            raise RunnerFailure("Pi JSON stream contained no final assistant message")
        lines = final.splitlines()
        if not lines or lines[0].strip() != expected_acknowledgement:
            raise RunnerFailure("Pi response did not acknowledge the bounded Nightwatch task")
        artifact = "\n".join(lines[1:]).strip()
        if not artifact:
            raise RunnerFailure("Pi acknowledged the task but returned no artifact content")
        return artifact
