from __future__ import annotations

import argparse
from datetime import datetime, timezone
from importlib.resources import files
import json
from pathlib import Path
import shutil
import sys
from typing import Sequence

from .clock import DemoClock, SystemClock
from .config import load_config
from .controller import NightwatchController
from .errors import NightwatchError, ValidationError
from .health import heartbeat_report
from .models import load_brief
from .runner import PiJsonRunner, SyntheticRunner
from .storage import RunStore

DEFAULT_DEMO_BRIEF = files("nightwatch.data").joinpath("synthetic-brief.json")
DEFAULT_DEMO_OUTPUT = Path("evidence") / "synthetic-run"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nightwatch",
        description="Offline-first demonstration of bounded agent orchestration.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate a structured brief")
    validate.add_argument("brief", type=Path)

    demo = subparsers.add_parser("demo", help="run the deterministic offline synthetic cycle")
    demo.add_argument("--output", type=Path, default=DEFAULT_DEMO_OUTPUT)
    demo.add_argument("--clean", action="store_true", help="replace a previous synthetic output")

    run = subparsers.add_parser("run", help="run a brief with an explicitly selected runner")
    run.add_argument("brief", type=Path)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--runner", choices=("synthetic", "pi"), default=None)
    run.add_argument("--config", type=Path)
    run.add_argument("--enable-external", action="store_true")

    status = subparsers.add_parser("status", help="print a concise run status")
    status.add_argument("run", type=Path)

    stop = subparsers.add_parser("stop", help="write a cooperative stop request")
    stop.add_argument("run", type=Path)
    stop.add_argument("--reason", default="operator requested stop")

    watchdog = subparsers.add_parser("watchdog", help="inspect structured heartbeat freshness")
    watchdog.add_argument("run", type=Path)
    watchdog.add_argument("--stale-after", type=float, default=30.0)
    return parser


def _safe_clean(path: Path) -> None:
    resolved = path.resolve()
    protected = {Path.cwd().resolve(), Path.home().resolve(), Path(resolved.anchor).resolve()}
    if resolved in protected:
        raise ValidationError(f"refusing to clean protected path: {resolved}")
    if not resolved.exists():
        return
    if not resolved.is_dir():
        raise ValidationError(f"output exists and is not a directory: {resolved}")
    entries = list(resolved.iterdir())
    if entries:
        manifest_path = resolved / "manifest.json"
        if not manifest_path.exists():
            raise ValidationError("--clean only replaces a previous Nightwatch synthetic run")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("synthetic_demonstration") is not True:
            raise ValidationError("--clean refuses to remove a non-synthetic run")
    shutil.rmtree(resolved)


def _run_controller(brief_path: Path, output: Path, runner, clock, *, skip_retry_delays: bool = False) -> int:
    brief = load_brief(brief_path)
    store = RunStore(output)
    controller_options = {"sleep": (lambda _seconds: None)} if skip_retry_delays else {}
    result = NightwatchController(store, runner, clock, **controller_options).run(brief)
    print(f"Nightwatch {result.status}: {store.root}")
    print(f"Summary: {store.summary_path}")
    return 0 if result.status == "completed" else 1


def command_validate(path: Path) -> int:
    brief = load_brief(path)
    print(f"Valid brief: {brief.run_id} ({len(brief.tasks)} tasks, {len(brief.allowed_paths)} allowed paths)")
    return 0


def command_demo(output: Path, clean: bool) -> int:
    if clean:
        _safe_clean(output)
    elif output.exists() and any(output.iterdir()):
        raise ValidationError(f"output is not empty; pass --clean for a prior synthetic run: {output}")
    return _run_controller(
        DEFAULT_DEMO_BRIEF,
        output,
        SyntheticRunner(),
        DemoClock(),
        skip_retry_delays=True,
    )


def command_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    runner_name = args.runner or config["runner"]["default"]
    if args.output.exists() and any(args.output.iterdir()):
        raise ValidationError(f"output is not empty: {args.output}")
    if runner_name == "synthetic":
        runner = SyntheticRunner()
    else:
        runner = PiJsonRunner(config, cli_external_approval=args.enable_external)
    return _run_controller(args.brief, args.output, runner, SystemClock())


def command_status(run: Path) -> int:
    manifest = RunStore(run).manifest()
    counters = manifest["counters"]
    print(f"{manifest['run_id']}: {manifest['status']}")
    print(
        f"tasks={counters['tasks_started']} attempts={counters['attempts']} retries={counters['retries']} "
        f"handoffs={counters['handoffs']} creative_iterations={counters['creative_iterations']}"
    )
    if manifest.get("stop_reason"):
        print(f"stop_reason={manifest['stop_reason']}")
    return 0


def command_stop(run: Path, reason: str) -> int:
    if not reason.strip():
        raise ValidationError("stop reason must be non-empty")
    store = RunStore(run)
    store.manifest()
    store.request_stop(reason.strip(), SystemClock().now())
    print(f"Stop requested for {store.root}")
    return 0


def command_watchdog(run: Path, stale_after: float) -> int:
    report = heartbeat_report(run, datetime.now(timezone.utc), stale_after)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["healthy"] else 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return command_validate(args.brief)
        if args.command == "demo":
            return command_demo(args.output, args.clean)
        if args.command == "run":
            return command_run(args)
        if args.command == "status":
            return command_status(args.run)
        if args.command == "stop":
            return command_stop(args.run, args.reason)
        if args.command == "watchdog":
            return command_watchdog(args.run, args.stale_after)
        parser.error("unknown command")
    except (NightwatchError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2
