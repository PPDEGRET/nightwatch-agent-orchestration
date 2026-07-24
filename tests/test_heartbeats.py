from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from nightwatch.errors import ValidationError
from nightwatch.health import heartbeat_report
from nightwatch.storage import RunStore, atomic_write_json
from tests.helpers import brief

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class HeartbeatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.store = RunStore(Path(self.temporary.name) / "run")
        self.store.initialize(brief(), "synthetic", NOW)
        self.store.set_run_status("running", NOW)
        self.store.write_heartbeat("controller", NOW, status="running")
        self.store.write_heartbeat("worker", NOW, status="running", task_id="task-one", attempt=1)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_fresh_heartbeats_are_healthy(self) -> None:
        report = heartbeat_report(self.store.root, NOW + timedelta(seconds=5), 10)
        self.assertTrue(report["healthy"])
        self.assertEqual(report["components"]["worker"]["age_seconds"], 5)

    def test_stale_running_heartbeat_is_unhealthy(self) -> None:
        report = heartbeat_report(self.store.root, NOW + timedelta(seconds=11), 10)
        self.assertFalse(report["healthy"])
        self.assertTrue(report["components"]["controller"]["stale"])

    def test_terminal_run_treats_staleness_as_informational(self) -> None:
        self.store.set_run_status("completed", NOW, completed=True)
        report = heartbeat_report(self.store.root, NOW + timedelta(hours=1), 10)
        self.assertTrue(report["healthy"])
        self.assertIn("terminal", report["note"])

    def test_malformed_heartbeat_is_rejected(self) -> None:
        atomic_write_json(self.store.heartbeats / "worker.json", {"schema_version": 9, "component": "worker"})
        with self.assertRaises(ValidationError):
            heartbeat_report(self.store.root, NOW, 10)


if __name__ == "__main__":
    unittest.main()
