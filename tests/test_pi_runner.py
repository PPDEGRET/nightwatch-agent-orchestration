from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from nightwatch.clock import DemoClock, isoformat
from nightwatch.config import DEFAULT_CONFIG
from nightwatch.controller import NightwatchController
from nightwatch.errors import ExternalExecutionDisabled, RunnerCleanupFailure, RunnerFailure, ValidationError
from nightwatch.runner import PiJsonRunner, RunResult, TaskContext
from nightwatch.storage import RunStore
from tests.helpers import brief, task


def enabled_config(*, fault_injection: bool = False) -> dict:
    config = deepcopy(DEFAULT_CONFIG)
    config["external_services"]["enabled"] = True
    config["fault_injection"]["enabled"] = fault_injection
    return config


class ExternalWithoutMetadataRunner:
    name = "external-without-metadata"
    external_services_enabled = True

    def execute(self, context: TaskContext) -> RunResult:
        return RunResult(
            files={path: "Uncorrelated external content\n" for path in context.task.outputs},
            summary="external result",
        )


class CleanupFailureRunner:
    name = "cleanup-failure"
    external_services_enabled = False

    def execute(self, context: TaskContext) -> RunResult:
        raise RunnerCleanupFailure("could not prove runner process-tree termination; retry blocked")


class ExternalMetadataRunner:
    name = "external-metadata-fixture"
    external_services_enabled = True

    def __init__(self) -> None:
        self.contexts: list[TaskContext] = []

    def execute(self, context: TaskContext) -> RunResult:
        self.contexts.append(context)
        handoff = None
        if context.task.produce_handoff:
            handoff = {
                "schema_version": 1,
                "from_task": context.task.id,
                "completed": "Acknowledged external fixture completed.",
                "next_step": "Review the persisted predecessor artifact.",
                "artifacts": list(context.task.outputs),
                "risks": ["Fixture metadata is not model evidence."],
                "created_at": isoformat(context.now()),
            }
        return RunResult(
            files={path: "Acknowledged external fixture\n" for path in context.task.outputs},
            summary="acknowledged external result",
            handoff=handoff,
            metadata={
                "provider": "test-provider",
                "model": "test-model",
                "task_acknowledged": True,
                "stream_events": 4,
                "tool_calls": 1 if context.fresh_context else 0,
                "read_paths": ["out/build-task.md"] if context.fresh_context else [],
            },
        )


class PiRunnerTests(unittest.TestCase):
    def test_requires_dual_opt_in_and_resolves_windows_command_shim(self) -> None:
        with self.assertRaises(ExternalExecutionDisabled):
            PiJsonRunner(DEFAULT_CONFIG, cli_external_approval=True)
        config = enabled_config()
        with self.assertRaises(ExternalExecutionDisabled):
            PiJsonRunner(config, cli_external_approval=False)
        truthy_config = enabled_config()
        truthy_config["external_services"]["enabled"] = "true"
        with self.assertRaises(ExternalExecutionDisabled):
            PiJsonRunner(truthy_config, cli_external_approval=True)
        runner = PiJsonRunner(config, cli_external_approval=True)
        with patch("nightwatch.runner.shutil.which", return_value=None):
            with self.assertRaisesRegex(RunnerFailure, "not found on PATH"):
                runner._resolve_command("pi")
        with patch("nightwatch.runner.shutil.which", return_value="C:/tools/pi.CMD"):
            self.assertEqual(runner._resolve_command("pi"), ["C:/tools/pi.CMD"])
        with tempfile.TemporaryDirectory() as temporary:
            npm_root = Path(temporary)
            shim = npm_root / "pi.CMD"
            shim.write_text("@echo off", encoding="utf-8")
            cli = npm_root / "node_modules" / "@earendil-works" / "pi-coding-agent" / "dist" / "cli.js"
            cli.parent.mkdir(parents=True)
            cli.write_text("", encoding="utf-8")
            with (
                patch("nightwatch.runner.os.name", "nt"),
                patch(
                    "nightwatch.runner.shutil.which",
                    side_effect=lambda name: str(shim) if name == "pi" else "C:/tools/node.exe",
                ),
            ):
                self.assertEqual(runner._resolve_command("pi"), ["C:/tools/node.exe", str(cli)])

    def test_prompt_is_single_line_and_maps_predecessor_artifacts_to_workspace(self) -> None:
        runner = PiJsonRunner(enabled_config(), cli_external_approval=True)
        context = SimpleNamespace(
            brief=SimpleNamespace(objective="first line\nsecond line"),
            task=SimpleNamespace(
                id="review-task",
                title="Review\nartifact",
                outputs=("workspace/out/review.md",),
            ),
            prior_artifacts=("workspace/out/predecessor.md",),
            handoff={"from_task": "build-task", "artifacts": ["workspace/out/predecessor.md"]},
            fresh_context=True,
        )
        instruction = runner._public_instruction(context)
        self.assertNotIn("\n", instruction)
        self.assertIn("NIGHTWATCH_TASK_ACK:review-task", instruction)
        self.assertIn('predecessor artifacts relative to your current workspace: ["out/predecessor.md"]', instruction)
        self.assertIn("use the read tool", instruction)
        self.assertEqual(runner._workspace_relative("workspace/out/result.md"), "out/result.md")
        with self.assertRaises(ValidationError):
            runner._workspace_relative("manifest.json")

    def test_response_requires_acknowledgement_phrases_and_records_stream_metrics(self) -> None:
        runner = PiJsonRunner(enabled_config(), cli_external_approval=True)
        message = json.dumps(
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "NIGHTWATCH_TASK_ACK:test-task\n# Verdict\nReviewed artifact: out/result.md",
                        }
                    ],
                },
            }
        )
        stream = "\n".join(
            [
                json.dumps(
                    {
                        "type": "tool_execution_start",
                        "toolName": "read",
                        "args": {"path": "out/result.md"},
                    }
                ),
                message,
            ]
        )
        artifact = runner._extract_final_text(stream, "NIGHTWATCH_TASK_ACK:test-task")
        self.assertEqual(artifact, "# Verdict\nReviewed artifact: out/result.md")
        runner._validate_required_phrases(
            SimpleNamespace(settings={"required_output_phrases": ["Verdict", "out/result.md"]}),
            artifact,
        )
        with tempfile.TemporaryDirectory() as temporary:
            metrics_context = SimpleNamespace(
                workspace_root=Path(temporary),
                fresh_context=True,
                prior_artifacts=("workspace/out/result.md",),
            )
            self.assertEqual(
                runner._stream_metrics(stream, metrics_context),
                {"stream_events": 2, "tool_calls": 1, "read_paths": ["out/result.md"]},
            )
            with self.assertRaisesRegex(RunnerFailure, "must be an object"):
                runner._extract_final_text("[]", "NIGHTWATCH_TASK_ACK:test-task")
            with self.assertRaisesRegex(RunnerFailure, "malformed at line 1"):
                runner._extract_final_text("not-json", "NIGHTWATCH_TASK_ACK:test-task")
            malformed_message = json.dumps({"type": "message_end", "message": []})
            with self.assertRaisesRegex(RunnerFailure, "no final assistant"):
                runner._extract_final_text(malformed_message, "NIGHTWATCH_TASK_ACK:test-task")
        with self.assertRaisesRegex(RunnerFailure, "did not acknowledge"):
            runner._extract_final_text(stream, "NIGHTWATCH_TASK_ACK:other-task")
        with self.assertRaisesRegex(RunnerFailure, "missing required phrase"):
            runner._validate_required_phrases(
                SimpleNamespace(settings={"required_output_phrases": ["Acceptance criteria"]}),
                artifact,
            )

    def test_windows_termination_kills_the_command_shim_process_tree(self) -> None:
        runner = PiJsonRunner(enabled_config(), cli_external_approval=True)
        process = Mock()
        process.pid = 1234
        process.poll.return_value = None
        process.communicate.return_value = ("", "")
        result = SimpleNamespace(returncode=0)
        with (
            patch("nightwatch.runner.os.name", "nt"),
            patch("nightwatch.runner.subprocess.run", return_value=result) as run,
        ):
            runner._terminate_process(process)
        run.assert_called_once_with(
            ["taskkill", "/PID", "1234", "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        process.terminate.assert_not_called()
        process.communicate.assert_called_once_with(timeout=5)

        failed_process = Mock()
        failed_process.pid = 5678
        failed_process.poll.side_effect = [None, None]
        failed_process.communicate.return_value = ("", "")
        failed_result = SimpleNamespace(returncode=1)
        with (
            patch("nightwatch.runner.os.name", "nt"),
            patch("nightwatch.runner.subprocess.run", return_value=failed_result),
            self.assertRaisesRegex(RunnerCleanupFailure, "retry blocked"),
        ):
            runner._terminate_process(failed_process)
        failed_process.kill.assert_called_once()

    def test_fault_injection_is_disabled_by_default_and_attempt_scoped(self) -> None:
        context = SimpleNamespace(
            attempt=1,
            task=SimpleNamespace(
                settings={
                    "fault_injection": {
                        "interrupt_attempts": [1],
                        "after_seconds": 0.5,
                    }
                }
            ),
        )
        disabled = PiJsonRunner(enabled_config(), cli_external_approval=True)
        with self.assertRaisesRegex(ValidationError, "requires fault_injection.enabled"):
            disabled._fault_interrupt_after(context)
        enabled = PiJsonRunner(enabled_config(fault_injection=True), cli_external_approval=True)
        self.assertEqual(enabled._fault_interrupt_after(context), 0.5)
        context.attempt = 2
        self.assertIsNone(enabled._fault_interrupt_after(context))
        context.task.settings["fault_injection"]["after_seconds"] = 0
        with self.assertRaisesRegex(ValidationError, "from 0.1 to 30"):
            enabled._fault_interrupt_after(context)

    def test_pi_handoff_is_structured_from_controller_evidence(self) -> None:
        runner = PiJsonRunner(enabled_config(), cli_external_approval=True)
        context = SimpleNamespace(
            task=SimpleNamespace(
                id="build-task",
                title="Build task",
                outputs=("workspace/out/result.md",),
                settings={
                    "next_step": "Review the result independently.",
                    "risks": ["Synthetic scenario."],
                },
            ),
            now=lambda: datetime(2026, 7, 14, tzinfo=timezone.utc),
        )
        handoff = runner._build_handoff(context)
        self.assertEqual(handoff["from_task"], "build-task")
        self.assertEqual(handoff["artifacts"], ["workspace/out/result.md"])
        self.assertEqual(handoff["next_step"], "Review the result independently.")
        with self.assertRaisesRegex(ValidationError, "settings.next_step"):
            context.task.settings["next_step"] = ""
            runner._build_handoff(context)

    def test_cleanup_failure_stops_run_without_retrying(self) -> None:
        tasks = [task("task-one", retry={"max_attempts": 2}), task("task-two")]
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            result = NightwatchController(
                store,
                CleanupFailureRunner(),
                DemoClock(),
                sleep=lambda _seconds: None,
            ).run(brief(tasks=tasks))
            self.assertEqual(result.status, "stopped")
            self.assertIn("process-tree cleanup failed", result.stop_reason)
            self.assertEqual(store.task_record("task-one")["attempts"], 1)
            self.assertEqual(store.task_record("task-one")["status"], "failed")
            self.assertEqual(store.task_record("task-two")["status"], "cancelled")

    def test_controller_rejects_external_output_without_execution_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            result = NightwatchController(
                store,
                ExternalWithoutMetadataRunner(),
                DemoClock(),
                sleep=lambda _seconds: None,
            ).run(brief())
            self.assertEqual(result.status, "completed_with_failures")
            self.assertEqual(store.task_record("task-one")["status"], "failed")
            self.assertIn(
                "external runner returned no execution metadata",
                store.task_record("task-one")["history"][-1]["detail"],
            )

    def test_controller_persists_external_metadata_handoff_and_fresh_context(self) -> None:
        tasks = [
            task("build-task", produce_handoff=True),
            task(
                "review-task",
                kind="review",
                depends_on=["build-task"],
                handoff_from="build-task",
                fresh_context=True,
            ),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            runner = ExternalMetadataRunner()
            result = NightwatchController(
                store,
                runner,
                DemoClock(),
                sleep=lambda _seconds: None,
            ).run(brief(tasks=tasks))
            self.assertEqual(result.status, "completed")
            manifest = store.manifest()
            self.assertEqual(manifest["counters"]["handoffs"], 1)
            self.assertEqual(manifest["tasks"][0]["execution"]["model"], "test-model")
            self.assertEqual(manifest["tasks"][1]["execution"]["tool_calls"], 1)
            self.assertEqual(manifest["tasks"][1]["execution"]["read_paths"], ["out/build-task.md"])
            self.assertEqual(runner.contexts[1].handoff["from_task"], "build-task")
            self.assertEqual(runner.contexts[1].prior_artifacts, ("workspace/out/build-task.md",))
            self.assertTrue(runner.contexts[1].fresh_context)


if __name__ == "__main__":
    unittest.main()
