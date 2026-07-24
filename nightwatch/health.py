from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .storage import RunStore


def heartbeat_report(run_root: Path, now: datetime, stale_after_seconds: float) -> dict[str, Any]:
    if stale_after_seconds <= 0:
        raise ValidationError("stale_after_seconds must be positive")
    store = RunStore(run_root)
    manifest = store.manifest()
    report: dict[str, Any] = {
        "run_id": manifest["run_id"],
        "run_status": manifest["status"],
        "healthy": True,
        "components": {},
    }
    if manifest["status"] in {"completed", "completed_with_failures", "stopped"}:
        report["note"] = "terminal run; heartbeat freshness is informational"
    for component in ("controller", "worker"):
        path = store.heartbeats / f"{component}.json"
        if not path.exists():
            report["components"][component] = {"present": False, "stale": True, "age_seconds": None}
            if manifest["status"] == "running":
                report["healthy"] = False
            continue
        age = store.heartbeat_age_seconds(component, now)
        stale = age > stale_after_seconds
        report["components"][component] = {
            "present": True,
            "stale": stale,
            "age_seconds": age,
        }
        if stale and manifest["status"] == "running":
            report["healthy"] = False
    return report
