from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .errors import ValidationError

DEFAULT_CONFIG = {
    "schema_version": 1,
    "external_services": {"enabled": False},
    "fault_injection": {"enabled": False},
    "runner": {
        "default": "synthetic",
        "pi": {
            "command": "pi",
            "routes": {},
            "tools": ["read", "grep", "find", "ls"],
        },
    },
}


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        data = json.loads(json.dumps(DEFAULT_CONFIG))
    else:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValidationError(f"configuration not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ValidationError(f"configuration is invalid JSON: line {exc.lineno}, column {exc.colno}") from exc
    if data.get("schema_version") != 1:
        raise ValidationError("configuration schema_version must be 1")
    external = data.get("external_services")
    fault_injection = data.get("fault_injection", {"enabled": False})
    runner = data.get("runner")
    if not isinstance(external, dict) or not isinstance(external.get("enabled"), bool):
        raise ValidationError("configuration external_services.enabled must be boolean")
    if not isinstance(fault_injection, dict) or not isinstance(fault_injection.get("enabled"), bool):
        raise ValidationError("configuration fault_injection.enabled must be boolean")
    data["fault_injection"] = fault_injection
    if not isinstance(runner, dict) or runner.get("default") not in {"synthetic", "pi"}:
        raise ValidationError("configuration runner.default must be 'synthetic' or 'pi'")
    pi = runner.get("pi")
    if not isinstance(pi, dict):
        raise ValidationError("configuration runner.pi must be an object")
    pi["command"] = os.environ.get("NIGHTWATCH_PI_COMMAND", pi.get("command", "pi"))
    if not isinstance(pi["command"], str) or not pi["command"].strip():
        raise ValidationError("configuration runner.pi.command must be non-empty")
    if not isinstance(pi.get("routes", {}), dict):
        raise ValidationError("configuration runner.pi.routes must be an object")
    tools = pi.get("tools", [])
    if not isinstance(tools, list) or not tools or not all(isinstance(item, str) and item for item in tools):
        raise ValidationError("configuration runner.pi.tools must be a non-empty list")
    return data


def resolve_pi_route(config: dict[str, Any], route_name: str) -> tuple[str, str]:
    route = config["runner"]["pi"].get("routes", {}).get(route_name)
    if not isinstance(route, dict):
        raise ValidationError(f"Pi model route is not configured: {route_name!r}")
    provider = route.get("provider")
    model = route.get("model")
    if not isinstance(provider, str) or not provider or not isinstance(model, str) or not model:
        raise ValidationError(f"Pi model route {route_name!r} requires provider and model")
    return provider, model
