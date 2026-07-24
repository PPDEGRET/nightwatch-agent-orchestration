from __future__ import annotations

from typing import Any


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_summary(manifest: dict[str, Any], events: list[dict[str, Any]]) -> str:
    counters = manifest["counters"]
    transitions = [event for event in events if event["type"] == "task_transition"]
    recovered = [event for event in transitions if event["data"]["to"] == "retry_wait"]
    creative = [event for event in events if event["type"] == "creative_iteration"]
    if manifest["synthetic_demonstration"] and not manifest["external_services_enabled"]:
        evidence_banner = "> **Synthetic demonstration.** No external agent, model, account, or network service was called."
    else:
        evidence_banner = "> **Operator review required.** This run may contain externally generated output; inspect provenance before sharing."
    lines = [
        "# Nightwatch morning summary",
        "",
        evidence_banner,
        "",
        f"**Run:** `{manifest['run_id']}`  ",
        f"**Status:** `{manifest['status']}`  ",
        f"**Runner:** `{manifest['runner']}`  ",
        f"**External services enabled:** `{str(manifest['external_services_enabled']).lower()}`",
        "",
        "## Original objective",
        "",
        manifest["objective"],
        "",
        "## Task evidence",
        "",
        "| Task | Kind | Status | Attempts | Route | Declared outputs |",
        "|---|---|---|---:|---|---|",
    ]
    for task in manifest["tasks"]:
        outputs = "<br>".join(f"`{_cell(path)}`" for path in task["outputs"])
        execution = task.get("execution")
        route = (
            f"{execution['provider']}/{execution['model']}"
            if isinstance(execution, dict)
            else task["model_route"]
        )
        lines.append(
            f"| {_cell(task['title'])} | `{task['kind']}` | `{task['status']}` | {task['attempts']} | "
            f"`{_cell(route)}` | {outputs} |"
        )
    lines.extend(
        [
            "",
            "## Recovery and continuity",
            "",
            f"- Attempts: **{counters['attempts']}** across **{counters['tasks_started']}** started tasks.",
            f"- Recovered retry transitions: **{len(recovered)}**.",
            f"- Failed attempts: **{counters['failed_attempts']}**; timed-out attempts: **{counters['timed_out_attempts']}**.",
            f"- Persisted continuation handoffs: **{counters['handoffs']}**.",
            f"- Synthetic creative iterations: **{counters['creative_iterations']}**.",
        ]
    )
    if recovered:
        lines.extend(["", "### Recovered attempts", ""])
        for event in recovered:
            data = event["data"]
            lines.append(f"- `{data['task_id']}`: {data['detail']}")
    if creative:
        scores = ", ".join(str(event["data"]["score"]) for event in creative)
        threshold = creative[-1]["data"]["threshold"]
        lines.extend(
            [
                "",
                "### Creative loop",
                "",
                f"Fixture scores by iteration: **{scores}**. Stop threshold: **{threshold}**.",
                "These values demonstrate the control loop; they are not aesthetic validation or model accuracy.",
            ]
        )
    if (
        manifest["status"] == "completed"
        and manifest["external_services_enabled"]
        and counters["retries"] >= 1
        and counters["handoffs"] >= 1
    ):
        next_gate = (
            "The interrupted handoff gate passed. Next, use a real but non-sensitive user-defined task with external "
            "acceptance criteria; do not broaden the claim to autonomous engineering."
        )
    elif manifest["external_services_enabled"]:
        next_gate = (
            "Have a human compare the externally generated artifact with the immutable brief, then repeat with one deliberate "
            "interruption in an isolated workspace before making any broader reliability claim."
        )
    else:
        next_gate = (
            "Compare this offline baseline with the supervised interruption-and-handoff evidence. The next product "
            "gate is a real but non-sensitive user-defined task with acceptance criteria fixed before execution."
        )
    lines.extend(
        [
            "",
            "## Human review boundary",
            "",
            "Nightwatch records state and evidence; it does not certify that the work is correct, useful, secure, or ready to ship. "
            "A human should inspect the declared artifacts, the handoff, and any visible failure before accepting the result.",
            "",
            "## Next validation gate",
            "",
            next_gate,
            "",
        ]
    )
    return "\n".join(lines)
