from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable

from .errors import RunnerCleanupFailure, RunnerFailure, RunnerStopped, RunnerTimeout, ValidationError
from .models import Brief, TaskSpec, normalize_relative_path
from .runner import RunResult, Runner, TaskContext
from .storage import RunStore, validate_handoff
from .summary import render_summary


@dataclass(frozen=True)
class ControllerResult:
    status: str
    stop_reason: str | None


class NightwatchController:
    def __init__(
        self,
        store: RunStore,
        runner: Runner,
        clock,
        *,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.store = store
        self.runner = runner
        self.clock = clock
        self.sleep = sleep
        self._started_monotonic = 0.0
        self._brief: Brief | None = None

    def run(self, brief: Brief) -> ControllerResult:
        self._brief = brief
        self._started_monotonic = self.clock.monotonic()
        created_at = self.clock.now()
        self.store.initialize(brief, self.runner.name, created_at)
        self._set_external_service_flag(self.runner.external_services_enabled)
        self.store.set_run_status("running", self.clock.now())
        self._controller_heartbeat("running")

        stopped_reason: str | None = None
        for task in self._ordered_tasks(brief):
            stopped_reason = self._stop_reason()
            if stopped_reason:
                self._cancel_remaining(stopped_reason)
                break
            dependency_states = {dependency: self.store.task_record(dependency)["status"] for dependency in task.depends_on}
            if any(state != "succeeded" for state in dependency_states.values()):
                detail = "dependency did not succeed: " + ", ".join(
                    f"{task_id}={state}" for task_id, state in sorted(dependency_states.items())
                )
                self.store.transition(task.id, "planned", "skipped", self.clock.now(), detail)
                continue
            if self.store.manifest()["counters"]["tasks_started"] >= brief.stop_conditions.max_tasks:
                stopped_reason = f"max_tasks reached ({brief.stop_conditions.max_tasks})"
                self._cancel_remaining(stopped_reason)
                break
            self.store.transition(task.id, "planned", "queued", self.clock.now(), "dependencies satisfied")
            outcome = self._run_task(task)
            if outcome == "cleanup_failure":
                stopped_reason = f"runner process-tree cleanup failed for {task.id}"
                self._cancel_remaining(stopped_reason)
                break
            if outcome == "stopped" or (outcome == "terminal_failure" and self._failure_limit_reached()):
                stopped_reason = self._stop_reason() or "runner stopped"
                self._cancel_remaining(stopped_reason)
                break

        manifest = self.store.manifest()
        task_states = [task["status"] for task in manifest["tasks"]]
        if stopped_reason:
            final_status = "stopped"
        elif any(state in {"failed", "timed_out", "cancelled"} for state in task_states):
            final_status = "completed_with_failures"
        elif any(state == "skipped" for state in task_states):
            final_status = "completed_with_failures"
        else:
            final_status = "completed"
        self.store.set_run_status(
            final_status,
            self.clock.now(),
            stop_reason=stopped_reason,
            completed=True,
        )
        self._controller_heartbeat(final_status)
        summary = render_summary(self.store.manifest(), self.store.events())
        self.store.set_summary(summary, self.clock.now())
        return ControllerResult(final_status, stopped_reason)

    def _run_task(self, task: TaskSpec) -> str:
        while True:
            stop_reason = self._stop_reason()
            if stop_reason:
                current = self.store.task_record(task.id)["status"]
                if current in {"queued", "retry_wait"}:
                    self.store.transition(task.id, current, "cancelled", self.clock.now(), stop_reason)
                return "stopped"
            self.store.transition(task.id, "queued", "running", self.clock.now(), "worker claimed task")
            attempt = self.store.start_attempt(task.id, self.clock.now())
            self._controller_heartbeat("task-running", task.id, attempt)
            self.store.write_heartbeat("worker", self.clock.now(), status="starting", task_id=task.id, attempt=attempt)
            try:
                handoff = self.store.load_handoff(task.handoff_from) if task.handoff_from else None
                context = TaskContext(
                    brief=self._brief,
                    task=task,
                    attempt=attempt,
                    workspace_root=self.store.workspace,
                    prior_artifacts=self._prior_artifacts(task),
                    handoff=handoff,
                    fresh_context=task.fresh_context,
                    now=self.clock.now,
                    heartbeat=lambda status: self.store.write_heartbeat(
                        "worker", self.clock.now(), status=status, task_id=task.id, attempt=attempt
                    ),
                    supervisor_heartbeat=lambda status: self._controller_heartbeat(
                        status, task.id, attempt
                    ),
                    emit=lambda event_type, data: self.store.append_event(self.clock.now(), event_type, data),
                    should_stop=self._stop_reason,
                )
                result = self.runner.execute(context)
                self._persist_result(task, result)
            except RunnerStopped as exc:
                self.store.write_heartbeat(
                    "worker", self.clock.now(), status="cancelled", task_id=task.id, attempt=attempt
                )
                self.store.transition(task.id, "running", "cancelled", self.clock.now(), str(exc))
                return "stopped"
            except RunnerCleanupFailure as exc:
                self.store.increment_counter("failed_attempts", self.clock.now())
                self.store.write_heartbeat(
                    "worker", self.clock.now(), status="cleanup-failed", task_id=task.id, attempt=attempt
                )
                self.store.transition(task.id, "running", "failed", self.clock.now(), str(exc))
                return "cleanup_failure"
            except RunnerTimeout as exc:
                self.store.increment_counter("timed_out_attempts", self.clock.now())
                self.store.write_heartbeat(
                    "worker", self.clock.now(), status="timed-out", task_id=task.id, attempt=attempt
                )
                self.store.transition(task.id, "running", "timed_out", self.clock.now(), str(exc))
                if not self._schedule_retry(task, "timed_out", attempt, str(exc)):
                    return "stopped" if self._stop_reason() else "terminal_failure"
            except (RunnerFailure, ValidationError) as exc:
                self.store.increment_counter("failed_attempts", self.clock.now())
                self.store.write_heartbeat(
                    "worker", self.clock.now(), status="failed", task_id=task.id, attempt=attempt
                )
                self.store.transition(task.id, "running", "failed", self.clock.now(), str(exc))
                if not self._schedule_retry(task, "failed", attempt, str(exc)):
                    return "stopped" if self._stop_reason() else "terminal_failure"
            else:
                self.store.write_heartbeat(
                    "worker", self.clock.now(), status="completed", task_id=task.id, attempt=attempt
                )
                self.store.transition(task.id, "running", "succeeded", self.clock.now(), result.summary)
                self._controller_heartbeat("task-succeeded", task.id, attempt)
                return "succeeded"

    def _persist_result(self, task: TaskSpec, result: RunResult) -> None:
        declared = set(task.outputs)
        returned = set(result.files)
        if declared != returned:
            missing = sorted(declared - returned)
            unexpected = sorted(returned - declared)
            raise RunnerFailure(f"runner output mismatch; missing={missing}, unexpected={unexpected}")
        validated_handoff = None
        if task.produce_handoff:
            if result.handoff is None:
                raise RunnerFailure("task promised a continuation handoff but returned none")
            validated_handoff = validate_handoff(result.handoff)
            if validated_handoff.get("from_task") != task.id:
                raise RunnerFailure("runner handoff source does not match the current task")
            if set(validated_handoff["artifacts"]) != declared:
                raise RunnerFailure("runner handoff artifacts do not match the task's declared outputs")
        elif result.handoff is not None:
            raise RunnerFailure("runner returned an undeclared handoff")
        iterations = result.metadata.get("iterations", 0)
        if iterations and (not isinstance(iterations, int) or isinstance(iterations, bool) or iterations < 0):
            raise RunnerFailure("runner returned an invalid creative iteration count")
        execution_keys = {
            "provider",
            "model",
            "task_acknowledged",
            "stream_events",
            "tool_calls",
            "read_paths",
        }
        has_execution_metadata = any(key in result.metadata for key in execution_keys)
        execution = None
        if has_execution_metadata:
            execution = {key: result.metadata.get(key) for key in execution_keys}
            if not isinstance(execution["provider"], str) or not execution["provider"].strip():
                raise RunnerFailure("runner execution metadata requires a provider")
            if not isinstance(execution["model"], str) or not execution["model"].strip():
                raise RunnerFailure("runner execution metadata requires a model")
            if execution["task_acknowledged"] is not True:
                raise RunnerFailure("runner execution metadata must confirm task acknowledgement")
            for key in ("stream_events", "tool_calls"):
                value = execution[key]
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    raise RunnerFailure(f"runner execution metadata {key} must be a non-negative integer")
            read_paths = execution["read_paths"]
            if not isinstance(read_paths, list) or not all(isinstance(path, str) for path in read_paths):
                raise RunnerFailure("runner execution metadata read_paths must be a list of strings")
            normalized_reads = [normalize_relative_path(path, "runner read path") for path in read_paths]
            if normalized_reads != read_paths or len(read_paths) != len(set(read_paths)):
                raise RunnerFailure("runner execution metadata read_paths must be normalized and unique")
        elif self.runner.external_services_enabled:
            raise RunnerFailure("external runner returned no execution metadata")

        if execution is not None:
            self.store.record_task_execution(task.id, execution, self.clock.now())
        self.store.write_workspace_files(result.files, self._brief.allowed_paths)
        if validated_handoff is not None:
            self.store.write_handoff(validated_handoff, self.clock.now())
        if iterations:
            self.store.increment_counter("creative_iterations", self.clock.now(), iterations)

    def _schedule_retry(self, task: TaskSpec, failed_state: str, attempt: int, detail: str) -> bool:
        if attempt >= task.retry.max_attempts:
            self._controller_heartbeat("task-terminal-failure", task.id, attempt)
            return False
        if self._failure_limit_reached():
            self._controller_heartbeat("failure-limit-reached", task.id, attempt)
            return False
        self.store.transition(task.id, failed_state, "retry_wait", self.clock.now(), f"retry after: {detail}")
        self.store.increment_counter("retries", self.clock.now())
        delay = task.retry.delay_for_retry(attempt)
        self.store.append_event(
            self.clock.now(),
            "retry_scheduled",
            {"task_id": task.id, "completed_attempts": attempt, "delay_seconds": delay},
        )
        remaining = delay
        while remaining > 0:
            if self._stop_reason():
                return False
            interval = min(0.1, remaining)
            self.sleep(interval)
            remaining -= interval
        if self._stop_reason():
            return False
        self.store.transition(task.id, "retry_wait", "queued", self.clock.now(), f"retry delay complete ({delay:g}s)")
        return True

    def _failure_limit_reached(self) -> bool:
        counters = self.store.manifest()["counters"]
        failures = counters["failed_attempts"] + counters["timed_out_attempts"]
        return failures >= self._brief.stop_conditions.max_failures

    def _stop_reason(self) -> str | None:
        request = self.store.stop_request()
        if request:
            return f"operator stop: {request['reason']}"
        elapsed = self.clock.monotonic() - self._started_monotonic
        if elapsed >= self._brief.stop_conditions.max_runtime_seconds:
            return f"max_runtime_seconds reached ({self._brief.stop_conditions.max_runtime_seconds:g})"
        if self._failure_limit_reached():
            return f"max_failures reached ({self._brief.stop_conditions.max_failures})"
        return None

    def _cancel_remaining(self, reason: str) -> None:
        manifest = self.store.manifest()
        for task in manifest["tasks"]:
            if task["status"] in {"planned", "queued", "retry_wait"}:
                self.store.transition(task["id"], task["status"], "cancelled", self.clock.now(), reason)

    def _prior_artifacts(self, current_task: TaskSpec) -> tuple[str, ...]:
        dependencies = set(current_task.depends_on)
        paths: list[str] = []
        for task in self.store.manifest()["tasks"]:
            if task["id"] in dependencies and task["status"] == "succeeded":
                paths.extend(task["outputs"])
        return tuple(paths)

    def _controller_heartbeat(self, status: str, task_id: str | None = None, attempt: int | None = None) -> None:
        self.store.write_heartbeat("controller", self.clock.now(), status=status, task_id=task_id, attempt=attempt)

    def _set_external_service_flag(self, enabled: bool) -> None:
        manifest = self.store.manifest()
        manifest["external_services_enabled"] = enabled
        from .storage import atomic_write_json

        atomic_write_json(self.store.manifest_path, manifest)

    @staticmethod
    def _ordered_tasks(brief: Brief) -> list[TaskSpec]:
        remaining = list(brief.tasks)
        ordered: list[TaskSpec] = []
        resolved: set[str] = set()
        while remaining:
            ready = [task for task in remaining if set(task.depends_on) <= resolved]
            if not ready:
                raise ValidationError("task dependency graph could not be ordered")
            for task in ready:
                ordered.append(task)
                resolved.add(task.id)
                remaining.remove(task)
        return ordered
