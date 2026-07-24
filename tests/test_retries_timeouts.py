from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from nightwatch.clock import DemoClock
from nightwatch.controller import NightwatchController
from nightwatch.models import RetryPolicy
from nightwatch.runner import SyntheticRunner
from nightwatch.storage import RunStore
from tests.helpers import brief, task


class RetryAndTimeoutTests(unittest.TestCase):
    def run_brief(self, tasks, *, max_failures: int = 10):
        temporary = tempfile.TemporaryDirectory()
        store = RunStore(Path(temporary.name) / "run")
        controller = NightwatchController(
            store,
            SyntheticRunner(),
            DemoClock(),
            sleep=lambda _seconds: None,
        )
        result = controller.run(
            brief(
                tasks=tasks,
                stop_conditions={"max_tasks": 10, "max_failures": max_failures, "max_runtime_seconds": 1000},
            )
        )
        return temporary, store, result

    def test_transient_failure_retries_then_succeeds(self) -> None:
        tasks = [
            task(
                retry={"max_attempts": 2, "backoff_seconds": 0},
                settings={
                    "fail_attempts": [1],
                    "fixture_content": "A deterministic fixture result.",
                },
            )
        ]
        temporary, store, result = self.run_brief(tasks)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.status, "completed")
        self.assertEqual(store.task_record("task-one")["attempts"], 2)
        self.assertEqual(store.manifest()["counters"]["failed_attempts"], 1)
        self.assertEqual(store.manifest()["counters"]["retries"], 1)
        artifact = (store.workspace / "out" / "task-one.md").read_text(encoding="utf-8")
        self.assertIn("## Fixture output", artifact)
        self.assertIn("A deterministic fixture result.", artifact)

    def test_timeout_retries_then_succeeds(self) -> None:
        tasks = [
            task(
                retry={"max_attempts": 2, "backoff_seconds": 0},
                settings={"timeout_attempts": [1]},
            )
        ]
        temporary, store, result = self.run_brief(tasks)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.status, "completed")
        self.assertEqual(store.manifest()["counters"]["timed_out_attempts"], 1)
        history = store.task_record("task-one")["history"]
        self.assertIn("timed_out", [item["to"] for item in history])
        self.assertIn("retry_wait", [item["to"] for item in history])

    def test_exhausted_attempts_remain_visible(self) -> None:
        tasks = [
            task(
                retry={"max_attempts": 2, "backoff_seconds": 0},
                settings={"fail_attempts": [1, 2]},
            )
        ]
        temporary, store, result = self.run_brief(tasks, max_failures=5)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.status, "completed_with_failures")
        self.assertEqual(store.task_record("task-one")["status"], "failed")
        self.assertEqual(store.task_record("task-one")["attempts"], 2)

    def test_backoff_is_bounded(self) -> None:
        policy = RetryPolicy(max_attempts=5, backoff_seconds=2, multiplier=3, max_backoff_seconds=10)
        self.assertEqual([policy.delay_for_retry(attempt) for attempt in (1, 2, 3, 4)], [2, 6, 10, 10])


if __name__ == "__main__":
    unittest.main()
