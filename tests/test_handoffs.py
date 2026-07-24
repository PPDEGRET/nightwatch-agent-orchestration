from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from nightwatch.clock import DemoClock, isoformat
from nightwatch.controller import NightwatchController
from nightwatch.errors import ValidationError
from nightwatch.runner import RunResult, TaskContext
from nightwatch.storage import RunStore, validate_handoff
from tests.helpers import brief, task


class CapturingRunner:
    name = "capture"
    external_services_enabled = False

    def __init__(self) -> None:
        self.contexts: list[TaskContext] = []

    def execute(self, context: TaskContext) -> RunResult:
        self.contexts.append(context)
        handoff = None
        if context.task.produce_handoff:
            handoff = {
                "schema_version": 1,
                "from_task": context.task.id,
                "completed": "bounded work completed",
                "next_step": "perform an independent review",
                "artifacts": list(context.task.outputs),
                "risks": ["fixture only"],
                "created_at": isoformat(context.now()),
            }
        return RunResult(
            files={path: "Synthetic demonstration\n" for path in context.task.outputs},
            summary="captured",
            handoff=handoff,
        )


class HandoffTests(unittest.TestCase):
    def test_handoff_record_requires_complete_shape(self) -> None:
        with self.assertRaisesRegex(ValidationError, "next_step"):
            validate_handoff(
                {
                    "schema_version": 1,
                    "from_task": "task-one",
                    "completed": "done",
                    "artifacts": [],
                    "risks": [],
                    "created_at": "2026-01-01T00:00:00Z",
                }
            )

    def test_missing_handoff_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            source = task("task-one", produce_handoff=True)
            review = task(
                "task-two",
                kind="review",
                depends_on=["task-one"],
                handoff_from="task-one",
                fresh_context=True,
            )
            value = brief(tasks=[source, review])
            store.initialize(value, "synthetic", DemoClock().now())
            with self.assertRaisesRegex(ValidationError, "not found"):
                store.load_handoff("task-one")

    def test_fresh_review_gets_brief_handoff_and_artifacts_without_session_history(self) -> None:
        tasks = [
            task("task-one", produce_handoff=True),
            task(
                "task-two",
                kind="review",
                depends_on=["task-one"],
                handoff_from="task-one",
                fresh_context=True,
            ),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            runner = CapturingRunner()
            result = NightwatchController(store, runner, DemoClock(), sleep=lambda _seconds: None).run(
                brief(tasks=tasks)
            )
            self.assertEqual(result.status, "completed")
            review_context = runner.contexts[1]
            self.assertTrue(review_context.fresh_context)
            self.assertEqual(review_context.handoff["from_task"], "task-one")
            self.assertEqual(review_context.brief.objective, "Exercise one bounded synthetic orchestration path.")
            self.assertEqual(review_context.prior_artifacts, ("workspace/out/task-one.md",))
            self.assertFalse(hasattr(review_context, "messages"))


if __name__ == "__main__":
    unittest.main()
