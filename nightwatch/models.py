from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .errors import ValidationError

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
TASK_KINDS = {"analysis", "implementation", "continuation", "review", "creative"}
WINDOWS_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
WINDOWS_INVALID_CHARS = set('<>:"|?*')


def normalize_relative_path(raw: str, label: str = "path") -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValidationError(f"{label} must be a non-empty string")
    raw = raw.strip()
    if "\\" in raw:
        raise ValidationError(f"{label} must use portable forward slashes: {raw!r}")
    if "\x00" in raw or re.match(r"^[A-Za-z]:", raw):
        raise ValidationError(f"{label} must be relative: {raw!r}")
    path = PurePosixPath(raw)
    invalid_part = any(
        part in {"", ".", ".."}
        or part.rstrip(". ") != part
        or any(character in WINDOWS_INVALID_CHARS or ord(character) < 32 for character in part)
        or part.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES
        for part in path.parts
    )
    if path.is_absolute() or not path.parts or invalid_part or path.as_posix() != raw:
        raise ValidationError(f"{label} must be a normalized portable relative path: {raw!r}")
    return path.as_posix()


def path_is_allowed(relative: str, allowed_paths: tuple[str, ...] | list[str]) -> bool:
    candidate = PurePosixPath(normalize_relative_path(relative))
    for raw_allowed in allowed_paths:
        allowed = PurePosixPath(normalize_relative_path(raw_allowed, "allowed path"))
        if candidate.parts[: len(allowed.parts)] == allowed.parts:
            return True
    return False


def resolve_allowed_path(root: Path, relative: str, allowed_paths: tuple[str, ...] | list[str]) -> Path:
    relative = normalize_relative_path(relative)
    if not path_is_allowed(relative, allowed_paths):
        raise ValidationError(f"output path is outside the brief allowlist: {relative!r}")
    resolved_root = root.resolve()
    target = (resolved_root / Path(*PurePosixPath(relative).parts)).resolve(strict=False)
    try:
        target.relative_to(resolved_root)
    except ValueError as exc:
        raise ValidationError(f"resolved output escapes the run workspace: {relative!r}") from exc
    return target


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    backoff_seconds: float = 0.0
    multiplier: float = 2.0
    max_backoff_seconds: float = 30.0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, label: str) -> "RetryPolicy":
        data = data or {}
        policy = cls(
            max_attempts=data.get("max_attempts", 1),
            backoff_seconds=data.get("backoff_seconds", 0.0),
            multiplier=data.get("multiplier", 2.0),
            max_backoff_seconds=data.get("max_backoff_seconds", 30.0),
        )
        errors: list[str] = []
        if not isinstance(policy.max_attempts, int) or not 1 <= policy.max_attempts <= 10:
            errors.append(f"{label}.max_attempts must be an integer from 1 to 10")
        for key, value in (
            ("backoff_seconds", policy.backoff_seconds),
            ("max_backoff_seconds", policy.max_backoff_seconds),
        ):
            if not isinstance(value, (int, float)) or value < 0:
                errors.append(f"{label}.{key} must be non-negative")
        if not isinstance(policy.multiplier, (int, float)) or policy.multiplier < 1:
            errors.append(f"{label}.multiplier must be at least 1")
        if errors:
            raise ValidationError(errors)
        return policy

    def delay_for_retry(self, completed_attempts: int) -> float:
        exponent = max(0, completed_attempts - 1)
        return min(self.max_backoff_seconds, self.backoff_seconds * (self.multiplier**exponent))


@dataclass(frozen=True)
class TaskSpec:
    id: str
    title: str
    kind: str
    outputs: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    timeout_seconds: float = 120.0
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    model_route: str = "routine"
    handoff_from: str | None = None
    produce_handoff: bool = False
    fresh_context: bool = False
    settings: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], index: int) -> "TaskSpec":
        label = f"tasks[{index}]"
        if not isinstance(data, dict):
            raise ValidationError(f"{label} must be an object")
        errors: list[str] = []
        task_id = data.get("id")
        title = data.get("title")
        kind = data.get("kind")
        outputs = data.get("outputs")
        depends_on = data.get("depends_on", [])
        timeout = data.get("timeout_seconds", 120)
        model_route = data.get("model_route", "routine")
        handoff_from = data.get("handoff_from")
        produce_handoff = data.get("produce_handoff", False)
        fresh_context = data.get("fresh_context", False)
        settings = data.get("settings", {})

        if not isinstance(task_id, str) or not ID_RE.fullmatch(task_id):
            errors.append(f"{label}.id must match {ID_RE.pattern}")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{label}.title must be a non-empty string")
        if kind not in TASK_KINDS:
            errors.append(f"{label}.kind must be one of {sorted(TASK_KINDS)}")
        if not isinstance(outputs, list) or not outputs:
            errors.append(f"{label}.outputs must be a non-empty list")
            normalized_outputs: tuple[str, ...] = ()
        else:
            normalized: list[str] = []
            for output_index, output in enumerate(outputs):
                try:
                    normalized.append(normalize_relative_path(output, f"{label}.outputs[{output_index}]"))
                except ValidationError as exc:
                    errors.extend(exc.errors)
            normalized_outputs = tuple(normalized)
        if not isinstance(depends_on, list) or not all(isinstance(item, str) for item in depends_on):
            errors.append(f"{label}.depends_on must be a list of task ids")
            depends_on = []
        if not isinstance(timeout, (int, float)) or not 0.05 <= timeout <= 86_400:
            errors.append(f"{label}.timeout_seconds must be from 0.05 to 86400")
        if not isinstance(model_route, str) or not ID_RE.fullmatch(model_route):
            errors.append(f"{label}.model_route must be a portable route id")
        if handoff_from is not None and not isinstance(handoff_from, str):
            errors.append(f"{label}.handoff_from must be a task id or null")
        if not isinstance(produce_handoff, bool):
            errors.append(f"{label}.produce_handoff must be boolean")
        if not isinstance(fresh_context, bool):
            errors.append(f"{label}.fresh_context must be boolean")
        if not isinstance(settings, dict):
            errors.append(f"{label}.settings must be an object")
            settings = {}
        if errors:
            raise ValidationError(errors)
        return cls(
            id=task_id,
            title=title.strip(),
            kind=kind,
            outputs=normalized_outputs,
            depends_on=tuple(depends_on),
            timeout_seconds=float(timeout),
            retry=RetryPolicy.from_dict(data.get("retry"), f"{label}.retry"),
            model_route=model_route,
            handoff_from=handoff_from,
            produce_handoff=produce_handoff,
            fresh_context=fresh_context,
            settings=settings,
        )


@dataclass(frozen=True)
class StopConditions:
    max_tasks: int
    max_failures: int
    max_runtime_seconds: float

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, task_count: int) -> "StopConditions":
        data = data or {}
        conditions = cls(
            max_tasks=data.get("max_tasks", max(1, task_count)),
            max_failures=data.get("max_failures", 1),
            max_runtime_seconds=data.get("max_runtime_seconds", 3600),
        )
        errors: list[str] = []
        if not isinstance(conditions.max_tasks, int) or conditions.max_tasks < 1:
            errors.append("stop_conditions.max_tasks must be a positive integer")
        if not isinstance(conditions.max_failures, int) or conditions.max_failures < 1:
            errors.append("stop_conditions.max_failures must be a positive integer")
        if not isinstance(conditions.max_runtime_seconds, (int, float)) or conditions.max_runtime_seconds <= 0:
            errors.append("stop_conditions.max_runtime_seconds must be positive")
        if errors:
            raise ValidationError(errors)
        return conditions


@dataclass(frozen=True)
class Brief:
    schema_version: int
    run_id: str
    title: str
    objective: str
    synthetic_demonstration: bool
    allowed_paths: tuple[str, ...]
    tasks: tuple[TaskSpec, ...]
    stop_conditions: StopConditions

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Brief":
        if not isinstance(data, dict):
            raise ValidationError("brief must be a JSON object")
        errors: list[str] = []
        if data.get("schema_version") != 1:
            errors.append("schema_version must be 1")
        run_id = data.get("run_id")
        if not isinstance(run_id, str) or not ID_RE.fullmatch(run_id):
            errors.append(f"run_id must match {ID_RE.pattern}")
        title = data.get("title")
        objective = data.get("objective")
        if not isinstance(title, str) or not title.strip():
            errors.append("title must be a non-empty string")
        if not isinstance(objective, str) or not objective.strip():
            errors.append("objective must be a non-empty string")
        elif len(objective) > 4000:
            errors.append("objective must be at most 4000 characters")
        synthetic = data.get("synthetic_demonstration")
        if not isinstance(synthetic, bool):
            errors.append("synthetic_demonstration must be boolean")
        allowed_raw = data.get("allowed_paths")
        allowed: list[str] = []
        if not isinstance(allowed_raw, list) or not allowed_raw:
            errors.append("allowed_paths must be a non-empty list")
        else:
            for index, raw in enumerate(allowed_raw):
                try:
                    normalized = normalize_relative_path(raw, f"allowed_paths[{index}]")
                    parts = PurePosixPath(normalized).parts
                    if len(parts) < 2 or parts[0] != "workspace":
                        errors.append(
                            f"allowed_paths[{index}] must name a subdirectory beneath 'workspace/'"
                        )
                    allowed.append(normalized)
                except ValidationError as exc:
                    errors.extend(exc.errors)
            if len(allowed) != len(set(allowed)):
                errors.append("allowed_paths must be unique")
        task_data = data.get("tasks")
        tasks: list[TaskSpec] = []
        if not isinstance(task_data, list) or not task_data:
            errors.append("tasks must be a non-empty list")
        else:
            for index, raw_task in enumerate(task_data):
                try:
                    tasks.append(TaskSpec.from_dict(raw_task, index))
                except ValidationError as exc:
                    errors.extend(exc.errors)
        if errors:
            raise ValidationError(errors)

        ids = [task.id for task in tasks]
        if len(ids) != len(set(ids)):
            errors.append("task ids must be unique")
        known_ids = set(ids)
        tasks_by_id = {task.id: task for task in tasks}
        for task in tasks:
            for dependency in task.depends_on:
                if dependency not in known_ids:
                    errors.append(f"task {task.id!r} depends on unknown task {dependency!r}")
                if dependency == task.id:
                    errors.append(f"task {task.id!r} cannot depend on itself")
            if task.handoff_from:
                if task.handoff_from not in known_ids:
                    errors.append(f"task {task.id!r} references unknown handoff task {task.handoff_from!r}")
                elif task.handoff_from not in task.depends_on:
                    errors.append(f"task {task.id!r} must depend on handoff source {task.handoff_from!r}")
                elif not tasks_by_id[task.handoff_from].produce_handoff:
                    errors.append(
                        f"task {task.id!r} requires a handoff from {task.handoff_from!r}, "
                        "but that source does not produce one"
                    )
            if task.fresh_context and task.kind != "review":
                errors.append(f"task {task.id!r} uses fresh_context but is not a review task")
            for output in task.outputs:
                if not path_is_allowed(output, allowed):
                    errors.append(f"task {task.id!r} output is outside allowed_paths: {output!r}")

        output_owners: dict[str, str] = {}
        for task in tasks:
            for output in task.outputs:
                previous = output_owners.get(output)
                if previous:
                    errors.append(
                        f"task output {output!r} is declared by both {previous!r} and {task.id!r}"
                    )
                else:
                    output_owners[output] = task.id

        graph = {task.id: task.depends_on for task in tasks}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                errors.append(f"task dependency cycle includes {node!r}")
                return
            if node in visited:
                return
            visiting.add(node)
            for dependency in graph.get(node, ()):
                if dependency in graph:
                    visit(dependency)
            visiting.remove(node)
            visited.add(node)

        for task_id in graph:
            visit(task_id)
        if errors:
            raise ValidationError(errors)
        return cls(
            schema_version=1,
            run_id=run_id,
            title=title.strip(),
            objective=objective.strip(),
            synthetic_demonstration=synthetic,
            allowed_paths=tuple(allowed),
            tasks=tuple(tasks),
            stop_conditions=StopConditions.from_dict(data.get("stop_conditions"), len(tasks)),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "title": self.title,
            "objective": self.objective,
            "synthetic_demonstration": self.synthetic_demonstration,
            "allowed_paths": list(self.allowed_paths),
            "stop_conditions": {
                "max_tasks": self.stop_conditions.max_tasks,
                "max_failures": self.stop_conditions.max_failures,
                "max_runtime_seconds": self.stop_conditions.max_runtime_seconds,
            },
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "kind": task.kind,
                    "outputs": list(task.outputs),
                    "depends_on": list(task.depends_on),
                    "timeout_seconds": task.timeout_seconds,
                    "retry": {
                        "max_attempts": task.retry.max_attempts,
                        "backoff_seconds": task.retry.backoff_seconds,
                        "multiplier": task.retry.multiplier,
                        "max_backoff_seconds": task.retry.max_backoff_seconds,
                    },
                    "model_route": task.model_route,
                    "handoff_from": task.handoff_from,
                    "produce_handoff": task.produce_handoff,
                    "fresh_context": task.fresh_context,
                    "settings": task.settings,
                }
                for task in self.tasks
            ],
        }


def load_brief(path: Path) -> Brief:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"brief not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"brief is not valid JSON: line {exc.lineno}, column {exc.colno}") from exc
    return Brief.from_dict(data)
