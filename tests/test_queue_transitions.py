from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from nightwatch.errors import InvalidTransition
from nightwatch.storage import RunStore
from tests.helpers import brief

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class QueueTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.store = RunStore(Path(self.temporary.name) / "run")
        self.store.initialize(brief(), "synthetic", NOW)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_success_path_moves_one_task_record(self) -> None:
        self.store.transition("task-one", "planned", "queued", NOW, "ready")
        self.store.transition("task-one", "queued", "running", NOW, "claimed")
        self.assertEqual(self.store.start_attempt("task-one", NOW), 1)
        self.store.transition("task-one", "running", "succeeded", NOW, "done")
        self.assertTrue(self.store.task_path("succeeded", "task-one").exists())
        self.assertFalse(self.store.task_path("running", "task-one").exists())
        self.assertEqual(self.store.task_record("task-one")["status"], "succeeded")

    def test_retry_path_is_explicit(self) -> None:
        self.store.transition("task-one", "planned", "queued", NOW, "ready")
        self.store.transition("task-one", "queued", "running", NOW, "claimed")
        self.store.start_attempt("task-one", NOW)
        self.store.transition("task-one", "running", "timed_out", NOW, "timeout")
        self.store.transition("task-one", "timed_out", "retry_wait", NOW, "retry")
        self.store.transition("task-one", "retry_wait", "queued", NOW, "ready again")
        self.assertTrue(self.store.task_path("queued", "task-one").exists())

    def test_invalid_transition_fails_without_moving_record(self) -> None:
        with self.assertRaises(InvalidTransition):
            self.store.transition("task-one", "planned", "succeeded", NOW, "skip work")
        self.assertTrue(self.store.task_path("planned", "task-one").exists())


if __name__ == "__main__":
    unittest.main()
