# Interrupted Pi handoff validation

**Date:** 2026-07-14  
**Evidence class:** supervised external fault-injection and handoff validation with synthetic input  
**Accepted result:** 2/2 tasks succeeded after one deliberate interruption

## Purpose

This gate tested the claims left open by the first Pi smoke run:

1. Can Nightwatch terminate an in-flight Pi attempt and preserve the failure?
2. Can it apply a bounded retry and complete the original task?
3. Can it persist a structured handoff tied to the immutable brief?
4. Can a new `--no-session` Pi invocation read the predecessor artifact?
5. Can the fresh reviewer identify a contradiction or ambiguity rather than merely echoing the plan?

The scenario remained fictional: Moonleaf defers notification permission until a user saves a plant and selects a care window.

## Safety boundary

This bounded external gate used:

- `openai-codex/gpt-5.6-luna`;
- read-only Pi tools: `read`, `grep`, `find`, `ls`;
- no Pi session persistence;
- context files, extensions, skills, and prompt templates disabled;
- synthetic data and a disposable workspace;
- explicit external-execution and fault-injection configuration;
- per-task acknowledgements and required-output phrases;
- 120-second task timeouts and a 300-second run limit.

The host workspace was not an operating-system sandbox. No private source, customer data, credentials, production system, deployment, or publication was involved.

## Fault and recovery path

The first `draft-remediation` attempt was deliberately terminated through the directly resolved Node CLI process tree. The fault event occurred **1.20s** after the attempt began, and the failed transition was persisted **0.25s** later:

```text
running
  → failed
  → retry_wait
  → queued
  → running
  → succeeded
```

The retry waited the configured `0.2s`, produced an acknowledged artifact, and persisted a schema-valid handoff.

## Continuation and fresh review

Nightwatch launched `fresh-review` as a new Pi process with `--no-session`. Its instruction supplied:

- the immutable original objective;
- the structured handoff;
- the predecessor path relative to the isolated workspace;
- an explicit requirement to use `read` before answering.

The Pi stream recorded **one review tool call** and persisted its sanitized path as `pi-handoff/remediation.md`. The controller rejects fresh reviews that do not read every declared predecessor artifact. The final review returned the required sections and found no direct contradiction while preserving the human validation gate.

## Accepted result

| Measure | Result |
|---|---:|
| Tasks | 2/2 succeeded |
| Attempts | 3 |
| Deliberately failed attempts | 1 |
| Retries | 1 |
| Persisted handoffs | 1 |
| Ordered Nightwatch events | 27 |
| Draft Pi stream events | 144 |
| Review Pi stream events | 123 |
| Review tool calls | 1 |
| Controller heartbeat sequence | 69, terminal `completed` |
| Worker heartbeat sequence | 71, terminal `completed` |
| Session/raw prompt retained | no |

Evidence:

- [`evidence/pi-handoff-run/manifest.json`](../evidence/pi-handoff-run/manifest.json)
- [`evidence/pi-handoff-run/execution.json`](../evidence/pi-handoff-run/execution.json)
- [`evidence/pi-handoff-run/summary.md`](../evidence/pi-handoff-run/summary.md)
- [`evidence/pi-handoff-run/handoffs/draft-remediation.json`](../evidence/pi-handoff-run/handoffs/draft-remediation.json)
- [`evidence/pi-handoff-run/workspace/pi-handoff/remediation.md`](../evidence/pi-handoff-run/workspace/pi-handoff/remediation.md)
- [`evidence/pi-handoff-run/workspace/pi-handoff/fresh-review.md`](../evidence/pi-handoff-run/workspace/pi-handoff/fresh-review.md)

## Failures found while making the gate repeatable

Three additional negative results were retained as lessons rather than accepted evidence:

1. The first successful handoff run left the final worker heartbeat labelled `pi-process-running`. The runner now writes terminal worker and supervisor heartbeats; that run was discarded.
2. A clean rerun produced a reviewer response without the required task acknowledgement. Nightwatch correctly closed as `completed_with_failures`. The review policy now permits one bounded retry for this transient protocol failure; the rejected run was discarded.
3. Terminating only the Windows `.CMD` wrapper did not prove its child Node process stopped at the threshold. Nightwatch now resolves the npm shim to the direct Node CLI and uses `taskkill /T /F` for Windows process-tree termination, failing closed if cleanup cannot be proven. The superseded evidence was discarded.

The accepted final run was launched directly through the normal command. Its process-tree fault event was observed near the configured threshold.

## What this proves

In this environment, Nightwatch can:

- deliberately terminate and classify a Pi attempt;
- retry within a configured budget;
- retain failure history after eventual success;
- resolve an explicit provider/model route;
- require task correlation and semantic output phrases;
- persist a controller-generated handoff tied to the produced artifact;
- launch a fresh no-session reviewer;
- expose and count a real predecessor-artifact read;
- terminate both controller and worker heartbeats cleanly;
- produce an operator-readable summary without retaining raw prompts or sessions.

## What this does not prove

- recovery from an uncontrolled host crash or provider outage;
- correct code implementation, testing, or deployment;
- operating-system isolation;
- repeatability across machines, providers, models, or real projects;
- user value, customer adoption, revenue, productivity improvement, or production reliability;
- general autonomous software engineering.

## Publication implication

The bounded orchestration claim now has both offline and supervised external evidence. Authorship, historical aggregate wording, provider/model disclosure, local source-path disclosure, license choice, and public repository publication decisions are recorded.

The next product-validation gate is a real but non-sensitive user-defined task with independently chosen acceptance criteria—not a broader autonomy claim.
