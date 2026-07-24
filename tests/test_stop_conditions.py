from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from nightwatch.clock import DemoClock
from nightwatch.controller import NightwatchController
from nightwatch.errors import RunnerFailure, RunnerStopped
from nightwatch.runner import RunResult, SyntheticRunner, TaskContext
from nightwatch.storage import RunStore
from tests.helpers import brief, task


class FailingRunner:
    name = "failing"
    external_services_enabled = False

    def execute(self, context: TaskContext) -> RunResult:
        raise RunnerFailure("fixture failure")


class StopDuringTaskRunner:
    name = "stop-during-task"
    external_services_enabled = False

    def execute(self, context: TaskContext) -> RunResult:
        store = RunStore(context.workspace_root.parent)
        store.request_stop("fixture operator stop", context.now())
        reason = context.should_stop()
        raise RunnerStopped(reason or "stop was not observed")


class StopConditionTests(unittest.TestCase):
    def run_controller(self, value, runner=None, clock=None):
        temporary = tempfile.TemporaryDirectory()
        store = RunStore(Path(temporary.name) / "run")
        result = NightwatchController(
            store,
            runner or SyntheticRunner(),
            clock or DemoClock(),
            sleep=lambda _seconds: None,
        ).run(value)
        return temporary, store, result

    def test_max_tasks_cancels_remaining_work(self) -> None:
        value = brief(
            tasks=[task("task-one"), task("task-two")],
            stop_conditions={"max_tasks": 1, "max_failures": 5, "max_runtime_seconds": 1000},
        )
        temporary, store, result = self.run_controller(value)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.status, "stopped")
        self.assertIn("max_tasks", result.stop_reason)
        self.assertEqual(store.task_record("task-two")["status"], "cancelled")

    def test_runtime_limit_stops_before_first_task(self) -> None:
        value = brief(stop_conditions={"max_tasks": 5, "max_failures": 5, "max_runtime_seconds": 0.5})
        temporary, store, result = self.run_controller(value, clock=DemoClock(tick_seconds=1))
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.status, "stopped")
        self.assertIn("max_runtime_seconds", result.stop_reason)
        self.assertEqual(store.task_record("task-one")["status"], "cancelled")

    def test_operator_stop_is_seen_during_task(self) -> None:
        value = brief()
        temporary, store, result = self.run_controller(value, runner=StopDuringTaskRunner())
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.status, "stopped")
        self.assertIn("operator stop", result.stop_reason)
        self.assertEqual(store.task_record("task-one")["status"], "cancelled")

    def test_operator_stop_interrupts_retry_backoff(self) -> None:
        value = brief(
            tasks=[task("task-one", retry={"max_attempts": 2, "backoff_seconds": 2})],
            stop_conditions={"max_tasks": 5, "max_failures": 5, "max_runtime_seconds": 1000},
        )
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            clock = DemoClock()
            sleep_calls: list[float] = []

            def request_stop_during_sleep(interval: float) -> None:
                sleep_calls.append(interval)
                store.request_stop("stop during retry delay", clock.now())

            result = NightwatchController(
                store,
                FailingRunner(),
                clock,
                sleep=request_stop_during_sleep,
            ).run(value)
            self.assertEqual(result.status, "stopped")
            self.assertEqual(sleep_calls, [0.1])
            self.assertEqual(store.task_record("task-one")["attempts"], 1)
            self.assertEqual(store.task_record("task-one")["status"], "cancelled")

    def test_failure_limit_stops_and_cancels_following_task(self) -> None:
        value = brief(
            tasks=[
                task("task-one", settings={"fail_attempts": [1]}),
                task("task-two"),
            ],
            stop_conditions={"max_tasks": 5, "max_failures": 1, "max_runtime_seconds": 1000},
        )
        temporary, store, result = self.run_controller(value)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.status, "stopped")
        self.assertIn("max_failures", result.stop_reason)
        self.assertEqual(store.task_record("task-one")["status"], "failed")
        self.assertEqual(store.task_record("task-two")["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
