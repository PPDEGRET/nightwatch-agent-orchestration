from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from nightwatch.cli import DEFAULT_DEMO_BRIEF
from nightwatch.clock import DemoClock
from nightwatch.controller import NightwatchController
from nightwatch.models import load_brief
from nightwatch.runner import SyntheticRunner
from nightwatch.storage import RunStore, read_json

from tests.helpers import brief, task

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIEF = PROJECT_ROOT / "examples" / "synthetic-brief.json"


class SyntheticDemoTests(unittest.TestCase):
    def run_demo(self, root: Path) -> RunStore:
        store = RunStore(root)
        result = NightwatchController(store, SyntheticRunner(), DemoClock(), sleep=lambda _seconds: None).run(
            load_brief(BRIEF)
        )
        self.assertEqual(result.status, "completed")
        return store

    def test_demo_exercises_full_bounded_cycle_without_external_services(self) -> None:
        self.assertEqual(DEFAULT_DEMO_BRIEF.read_bytes(), BRIEF.read_bytes())
        with tempfile.TemporaryDirectory() as temporary:
            store = self.run_demo(Path(temporary) / "run")
            manifest = store.manifest()
            self.assertFalse(manifest["external_services_enabled"])
            self.assertEqual(manifest["counters"]["tasks_started"], 5)
            self.assertEqual(manifest["counters"]["attempts"], 7)
            self.assertEqual(manifest["counters"]["retries"], 2)
            self.assertEqual(manifest["counters"]["handoffs"], 3)
            self.assertEqual(manifest["counters"]["creative_iterations"], 5)
            self.assertTrue((store.workspace / "creative" / "iteration-05.svg").exists())
            self.assertIn("Synthetic demonstration", store.summary_path.read_text(encoding="utf-8"))
            controller_heartbeat = read_json(store.heartbeats / "controller.json")
            self.assertEqual(controller_heartbeat["status"], "completed")
            self.assertGreater(controller_heartbeat["sequence"], 7)

    def test_creative_loop_can_stop_before_the_score_list_ends(self) -> None:
        creative = task(
            "creative-task",
            kind="creative",
            outputs=[
                "workspace/out/iteration-01.svg",
                "workspace/out/iteration-02.svg",
                "workspace/out/report.md",
            ],
            model_route="creative",
            settings={"scores": [50, 95, 99], "quality_threshold": 90},
        )
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            result = NightwatchController(
                store,
                SyntheticRunner(),
                DemoClock(),
                sleep=lambda _seconds: None,
            ).run(brief(tasks=[creative]))
            self.assertEqual(result.status, "completed")
            self.assertEqual(store.manifest()["counters"]["creative_iterations"], 2)
            self.assertFalse((store.workspace / "out" / "iteration-03.svg").exists())

    def test_demo_outputs_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = self.run_demo(Path(temporary) / "first")
            second = self.run_demo(Path(temporary) / "second")
            for relative in (
                "manifest.json",
                "events.jsonl",
                "summary.md",
                "workspace/creative/iteration-05.svg",
                "handoffs/build-workflow.json",
            ):
                with self.subTest(relative=relative):
                    self.assertEqual(
                        (first.root / relative).read_bytes(),
                        (second.root / relative).read_bytes(),
                    )


if __name__ == "__main__":
    unittest.main()
