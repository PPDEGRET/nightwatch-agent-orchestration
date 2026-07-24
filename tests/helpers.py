from __future__ import annotations

from copy import deepcopy
from typing import Any

from nightwatch.models import Brief


def task(
    task_id: str = "task-one",
    *,
    kind: str = "analysis",
    outputs: list[str] | None = None,
    depends_on: list[str] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "id": task_id,
        "title": task_id.replace("-", " ").title(),
        "kind": kind,
        "outputs": outputs or [f"workspace/out/{task_id}.md"],
        "depends_on": depends_on or [],
        "timeout_seconds": 5,
        "retry": {"max_attempts": 1},
        "model_route": "routine",
        "settings": {},
    }
    value.update(overrides)
    return value


def brief_data(
    *,
    tasks: list[dict[str, Any]] | None = None,
    allowed_paths: list[str] | None = None,
    stop_conditions: dict[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": 1,
        "run_id": "test-run",
        "title": "Test run",
        "objective": "Exercise one bounded synthetic orchestration path.",
        "synthetic_demonstration": True,
        "allowed_paths": allowed_paths or ["workspace/out"],
        "stop_conditions": stop_conditions
        or {"max_tasks": 10, "max_failures": 5, "max_runtime_seconds": 1000},
        "tasks": tasks or [task()],
    }
    value.update(overrides)
    return value


def brief(**kwargs: Any) -> Brief:
    return Brief.from_dict(deepcopy(brief_data(**kwargs)))
