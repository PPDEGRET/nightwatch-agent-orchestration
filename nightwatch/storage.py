from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .clock import isoformat, parse_time
from .errors import InvalidTransition, ValidationError
from .models import Brief, TaskSpec, resolve_allowed_path

QUEUE_STATES = (
    "planned",
    "queued",
    "running",
    "retry_wait",
    "succeeded",
    "failed",
    "timed_out",
    "cancelled",
    "skipped",
)

ALLOWED_TRANSITIONS = {
    "planned": {"queued", "cancelled", "skipped"},
    "queued": {"running", "cancelled", "skipped"},
    "running": {"succeeded", "failed", "timed_out", "cancelled"},
    "failed": {"retry_wait"},
    "timed_out": {"retry_wait"},
    "retry_wait": {"queued", "cancelled"},
    "succeeded": set(),
    "cancelled": set(),
    "skipped": set(),
}


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"required record not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON record {path}: line {exc.lineno}, column {exc.colno}") from exc


class RunStore:
    """Single-controller filesystem state with explicit, inspectable transitions."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.queue_root = self.root / "queue"
        self.workspace = self.root / "workspace"
        self.heartbeats = self.root / "heartbeats"
        self.handoffs = self.root / "handoffs"
        self.manifest_path = self.root / "manifest.json"
        self.events_path = self.root / "events.jsonl"
        self.brief_path = self.root / "brief.json"
        self.summary_path = self.root / "summary.md"
        self.stop_path = self.root / "STOP"

    def initialize(self, brief: Brief, runner_name: str, created_at: datetime) -> None:
        if self.manifest_path.exists():
            raise ValidationError(f"run already exists: {self.root}")
        self.root.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.heartbeats.mkdir(parents=True, exist_ok=True)
        self.handoffs.mkdir(parents=True, exist_ok=True)
        for state in QUEUE_STATES:
            (self.queue_root / state).mkdir(parents=True, exist_ok=True)
        timestamp = isoformat(created_at)
        atomic_write_json(self.brief_path, brief.as_dict())
        tasks: list[dict[str, Any]] = []
        for task in brief.tasks:
            record = self._task_record(task, timestamp)
            atomic_write_json(self.task_path("planned", task.id), record)
            tasks.append(record)
        manifest = {
            "schema_version": 1,
            "run_id": brief.run_id,
            "title": brief.title,
            "objective": brief.objective,
            "status": "created",
            "runner": runner_name,
            "synthetic_demonstration": brief.synthetic_demonstration,
            "external_services_enabled": False,
            "created_at": timestamp,
            "updated_at": timestamp,
            "completed_at": None,
            "stop_reason": None,
            "summary_path": None,
            "counters": {
                "tasks_started": 0,
                "attempts": 0,
                "failed_attempts": 0,
                "timed_out_attempts": 0,
                "retries": 0,
                "handoffs": 0,
                "creative_iterations": 0,
            },
            "tasks": tasks,
        }
        atomic_write_json(self.manifest_path, manifest)
        self.append_event(created_at, "run_created", {"runner": runner_name, "synthetic": brief.synthetic_demonstration})

    @staticmethod
    def _task_record(task: TaskSpec, timestamp: str) -> dict[str, Any]:
        return {
            "id": task.id,
            "title": task.title,
            "kind": task.kind,
            "status": "planned",
            "attempts": 0,
            "max_attempts": task.retry.max_attempts,
            "timeout_seconds": task.timeout_seconds,
            "model_route": task.model_route,
            "depends_on": list(task.depends_on),
            "outputs": list(task.outputs),
            "handoff_from": task.handoff_from,
            "fresh_context": task.fresh_context,
            "history": [{"at": timestamp, "from": None, "to": "planned", "detail": "brief accepted"}],
        }

    def task_path(self, state: str, task_id: str) -> Path:
        if state not in QUEUE_STATES:
            raise ValidationError(f"unknown queue state: {state}")
        return self.queue_root / state / f"{task_id}.json"

    def manifest(self) -> dict[str, Any]:
        return read_json(self.manifest_path)

    def brief(self) -> dict[str, Any]:
        return read_json(self.brief_path)

    def task_record(self, task_id: str) -> dict[str, Any]:
        manifest = self.manifest()
        for task in manifest["tasks"]:
            if task["id"] == task_id:
                return task
        raise ValidationError(f"task is not in manifest: {task_id}")

    def _replace_task(self, manifest: dict[str, Any], replacement: dict[str, Any]) -> None:
        for index, task in enumerate(manifest["tasks"]):
            if task["id"] == replacement["id"]:
                manifest["tasks"][index] = replacement
                return
        raise ValidationError(f"task is not in manifest: {replacement['id']}")

    def transition(self, task_id: str, from_state: str, to_state: str, at: datetime, detail: str) -> None:
        if to_state not in ALLOWED_TRANSITIONS.get(from_state, set()):
            raise InvalidTransition(f"invalid transition for {task_id}: {from_state} -> {to_state}")
        source = self.task_path(from_state, task_id)
        destination = self.task_path(to_state, task_id)
        record = read_json(source)
        if record.get("status") != from_state:
            raise InvalidTransition(
                f"task file state mismatch for {task_id}: expected {from_state}, found {record.get('status')}"
            )
        timestamp = isoformat(at)
        record["status"] = to_state
        record["history"].append({"at": timestamp, "from": from_state, "to": to_state, "detail": detail})
        atomic_write_json(source, record)
        os.replace(source, destination)
        manifest = self.manifest()
        self._replace_task(manifest, record)
        manifest["updated_at"] = timestamp
        atomic_write_json(self.manifest_path, manifest)
        self.append_event(at, "task_transition", {"task_id": task_id, "from": from_state, "to": to_state, "detail": detail})

    def start_attempt(self, task_id: str, at: datetime) -> int:
        path = self.task_path("running", task_id)
        record = read_json(path)
        record["attempts"] += 1
        attempt = record["attempts"]
        atomic_write_json(path, record)
        manifest = self.manifest()
        self._replace_task(manifest, record)
        manifest["updated_at"] = isoformat(at)
        manifest["counters"]["attempts"] += 1
        if attempt == 1:
            manifest["counters"]["tasks_started"] += 1
        atomic_write_json(self.manifest_path, manifest)
        self.append_event(at, "task_attempt_started", {"task_id": task_id, "attempt": attempt})
        return attempt

    def record_task_execution(self, task_id: str, execution: dict[str, Any], at: datetime) -> None:
        path = self.task_path("running", task_id)
        record = read_json(path)
        record["execution"] = execution
        atomic_write_json(path, record)
        manifest = self.manifest()
        self._replace_task(manifest, record)
        manifest["updated_at"] = isoformat(at)
        atomic_write_json(self.manifest_path, manifest)
        self.append_event(at, "task_execution_recorded", {"task_id": task_id, **execution})

    def increment_counter(self, name: str, at: datetime, amount: int = 1) -> None:
        manifest = self.manifest()
        if name not in manifest["counters"]:
            raise ValidationError(f"unknown manifest counter: {name}")
        manifest["counters"][name] += amount
        manifest["updated_at"] = isoformat(at)
        atomic_write_json(self.manifest_path, manifest)

    def set_run_status(
        self,
        status: str,
        at: datetime,
        *,
        stop_reason: str | None = None,
        completed: bool = False,
    ) -> None:
        manifest = self.manifest()
        previous = manifest["status"]
        manifest["status"] = status
        manifest["updated_at"] = isoformat(at)
        manifest["stop_reason"] = stop_reason
        if completed:
            manifest["completed_at"] = isoformat(at)
        atomic_write_json(self.manifest_path, manifest)
        self.append_event(at, "run_status", {"from": previous, "to": status, "reason": stop_reason})

    def set_summary(self, content: str, at: datetime) -> None:
        atomic_write_text(self.summary_path, content)
        manifest = self.manifest()
        manifest["summary_path"] = "summary.md"
        manifest["updated_at"] = isoformat(at)
        atomic_write_json(self.manifest_path, manifest)
        self.append_event(at, "summary_written", {"path": "summary.md"})

    def write_workspace_files(self, files: dict[str, str], allowed_paths: tuple[str, ...]) -> list[str]:
        validated: list[tuple[str, Path, str]] = []
        for relative, content in sorted(files.items()):
            if not isinstance(content, str):
                raise ValidationError(f"runner output for {relative!r} must be text")
            validated.append((relative, resolve_allowed_path(self.root, relative, allowed_paths), content))
        written: list[str] = []
        for relative, target, content in validated:
            atomic_write_text(target, content)
            written.append(relative)
        return written

    def append_event(self, at: datetime, event_type: str, data: dict[str, Any]) -> None:
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        sequence = 1
        if self.events_path.exists():
            with self.events_path.open("r", encoding="utf-8") as handle:
                sequence += sum(1 for line in handle if line.strip())
        event = {"sequence": sequence, "at": isoformat(at), "type": event_type, "data": data}
        with self.events_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def events(self) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line_number, line in enumerate(
            self.events_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    f"invalid event JSON at {self.events_path}:{line_number}"
                ) from exc
            if not isinstance(event, dict):
                raise ValidationError(
                    f"event record must be an object at {self.events_path}:{line_number}"
                )
            events.append(event)
        return events

    def write_heartbeat(
        self,
        component: str,
        at: datetime,
        *,
        status: str,
        task_id: str | None = None,
        attempt: int | None = None,
    ) -> None:
        current_path = self.heartbeats / f"{component}.json"
        sequence = 1
        if current_path.exists():
            previous = read_json(current_path)
            sequence = int(previous.get("sequence", 0)) + 1
        heartbeat = {
            "schema_version": 1,
            "run_id": self.manifest()["run_id"],
            "component": component,
            "sequence": sequence,
            "observed_at": isoformat(at),
            "status": status,
            "task_id": task_id,
            "attempt": attempt,
        }
        atomic_write_json(current_path, heartbeat)

    def heartbeat_age_seconds(self, component: str, now: datetime) -> float:
        heartbeat = read_json(self.heartbeats / f"{component}.json")
        if heartbeat.get("schema_version") != 1 or heartbeat.get("component") != component:
            raise ValidationError(f"invalid {component} heartbeat")
        return max(0.0, (now - parse_time(heartbeat["observed_at"])).total_seconds())

    def write_handoff(self, handoff: dict[str, Any], at: datetime) -> str:
        validated = validate_handoff(handoff)
        relative = f"handoffs/{validated['from_task']}.json"
        atomic_write_json(self.root / relative, validated)
        self.increment_counter("handoffs", at)
        self.append_event(at, "handoff_written", {"from_task": validated["from_task"], "path": relative})
        return relative

    def load_handoff(self, from_task: str) -> dict[str, Any]:
        handoff = validate_handoff(read_json(self.handoffs / f"{from_task}.json"))
        if handoff["from_task"] != from_task:
            raise ValidationError(f"handoff source mismatch: expected {from_task!r}")
        return handoff

    def request_stop(self, reason: str, at: datetime) -> None:
        atomic_write_json(self.stop_path, {"requested_at": isoformat(at), "reason": reason})
        self.append_event(at, "stop_requested", {"reason": reason})

    def stop_request(self) -> dict[str, Any] | None:
        if not self.stop_path.exists():
            return None
        value = read_json(self.stop_path)
        if not isinstance(value.get("reason"), str) or not value["reason"].strip():
            raise ValidationError("STOP record must include a reason")
        return value


def validate_handoff(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError("handoff must be an object")
    required_strings = ("from_task", "completed", "next_step", "created_at")
    errors: list[str] = []
    if value.get("schema_version") != 1:
        errors.append("handoff.schema_version must be 1")
    for key in required_strings:
        if not isinstance(value.get(key), str) or not value[key].strip():
            errors.append(f"handoff.{key} must be a non-empty string")
    for key in ("artifacts", "risks"):
        if not isinstance(value.get(key), list) or not all(isinstance(item, str) for item in value.get(key, [])):
            errors.append(f"handoff.{key} must be a list of strings")
    if errors:
        raise ValidationError(errors)
    return value
