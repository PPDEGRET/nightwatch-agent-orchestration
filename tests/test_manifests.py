from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from nightwatch.errors import ValidationError
from nightwatch.storage import RunStore
from tests.helpers import brief

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class ManifestTests(unittest.TestCase):
    def test_manifest_records_safety_and_attempt_counters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            store.initialize(brief(), "synthetic", NOW)
            manifest = store.manifest()
            self.assertTrue(manifest["synthetic_demonstration"])
            self.assertFalse(manifest["external_services_enabled"])
            self.assertEqual(manifest["counters"]["attempts"], 0)
            store.transition("task-one", "planned", "queued", NOW, "ready")
            store.transition("task-one", "queued", "running", NOW, "claimed")
            store.start_attempt("task-one", NOW)
            updated = store.manifest()
            self.assertEqual(updated["counters"]["attempts"], 1)
            self.assertEqual(updated["counters"]["tasks_started"], 1)

    def test_atomic_writes_leave_no_temporary_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            store.initialize(brief(), "synthetic", NOW)
            store.set_run_status("running", NOW)
            leftovers = [path for path in store.root.rglob(".*") if path.is_file()]
            self.assertEqual(leftovers, [])

    def test_malformed_event_log_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            store.initialize(brief(), "synthetic", NOW)
            with store.events_path.open("a", encoding="utf-8") as handle:
                handle.write("not-json\n")
            with self.assertRaisesRegex(ValidationError, "invalid event JSON.*:2"):
                store.events()

    def test_events_have_monotonic_sequence_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = RunStore(Path(temporary) / "run")
            store.initialize(brief(), "synthetic", NOW)
            store.set_run_status("running", NOW)
            store.append_event(NOW, "test_event", {"safe": True})
            self.assertEqual([event["sequence"] for event in store.events()], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
