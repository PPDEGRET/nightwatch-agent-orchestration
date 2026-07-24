# Nightwatch Showcase Plan

## Closure decision

**Closure type: Package.** Preserve Nightwatch's original operational insight, replace its brittle migration snapshot with a portable and testable controller, and document the failures that informed Crab/Pi. This is not an attempt to turn Nightwatch into a production workflow engine.

## Core promise

Nightwatch demonstrates a bounded local control loop for unattended coding-agent work:

> A structured brief becomes queued work, recoverable attempts, explicit continuation handoffs, fresh-context review, visual iterations, and a morning summary that a human can verify.

The public demonstration must run without accounts, credentials, model calls, network access, or external agents.

## Intended audience

- founders and operators evaluating practical AI workflow judgment;
- product and technical hiring managers interested in agent-control systems;
- engineers comparing lightweight local orchestration with durable workflow platforms;
- peers interested in the operational lessons that led from Nightwatch to Crab/Pi.

## Market and user problem

Long coding-agent sessions can appear productive while silently losing alignment, stalling behind dead processes, writing to the wrong workspace, or handing incomplete context to a successor. Generic queues handle process state; they do not automatically preserve a human's intent or make model output reviewable the next morning.

Nightwatch's thesis was that bounded overnight work needed both conventional control-plane primitives and LLM-specific operating protocols:

- an immutable original brief;
- explicit allowed paths;
- visible queue and manifest state;
- heartbeats, timeouts, retries, and stop conditions;
- continuation handoffs that do not replace the brief;
- a fresh-eyes review boundary;
- screenshot-based iteration for visual work;
- a concise human-review summary.

## Positioning against Temporal and Hatchet

Temporal and Hatchet are stronger general durable-execution platforms. Nightwatch will not claim to replace or outperform them. The case study will distinguish:

- **infrastructure overlap:** queues, retries, timeouts, heartbeats, task state, recovery;
- **Nightwatch's application-layer focus:** quota-aware local agent runs, semantic continuity, visual review, and morning operator evidence.

Pi will be treated as an optional agent executor, not as Nightwatch's state store or scheduler.

## Current source state

The read-only source snapshot contains a Bash/Git-Bash controller, CLI, watchdog, continuation utilities, configuration, and operator documentation. The inspected implementation has useful concepts but material contradictions:

- the CLI's initial queued brief is not clearly launched as the documented direct orchestrator;
- continuation expects a run-local brief that start does not reliably create;
- configured generic retries, timeouts, and model routing are not consistently enforced;
- the watcher blocks on a child while also serving as the liveness heartbeat source;
- allowed-path checks are described more strongly than their actual isolation guarantees;
- fresh-eyes review is designed but not reliably represented as a controller invariant;
- the migration README is a backup notice rather than usable public documentation.

The source remains permanently read-only.

## Evidence already available

### Historical aggregate evidence I supplied

- a run reported as completing 7 of 7 tasks;
- a build spanning multiple sessions;
- a creative workflow reported as using five screenshot iterations.

Raw runs, prompts, sessions, logs, private project details, and unapproved screenshots are excluded. Public evidence cards will describe these as **reported historical outcomes** and will not imply independent reproduction.

### Reproducible evidence to create here

- passing focused tests;
- a deterministic offline synthetic orchestration run;
- generated manifests, events, handoffs, heartbeats, visual iterations, and summary;
- locally captured screenshots of the synthetic case-study interface.

## Planned implementation

Use Python 3.11+ and the standard library for the canonical portable controller.

1. Define validated brief, task, manifest, handoff, and heartbeat records.
2. Use atomic filesystem writes and explicit queue-state directories.
3. Implement a deterministic controller with retry, timeout, heartbeat, handoff, review, and stop-condition boundaries.
4. Provide a `SyntheticRunner` as the default and only runner used by tests and evidence generation.
5. Provide a generic runner interface and an optional `PiJsonRunner`.
6. Reject Pi execution unless both configuration and the CLI explicitly enable external execution.
7. Never describe allowed paths as a host sandbox; recommend a container for any real external agent run.
8. Write new public synthetic task instructions rather than inspect or copy source raw prompts.

## Planned public artifacts

- `README.md`
- `SHOWCASE_PLAN.md`
- `PROVENANCE.md`
- portable `nightwatch/` implementation
- schemas and synthetic fixture
- focused `tests/`
- deterministic `evidence/synthetic-run/`
- historical aggregate evidence cards
- `docs/problem-and-market.md`
- `docs/architecture.md` with four required lifecycle diagrams
- `docs/failures-that-shaped-crab.md`
- `docs/evidence-and-limitations.md`
- `docs/demo-script.md`
- an accessible static case-study page
- two to four locally captured screenshots

## Privacy, safety, and attribution risks

- Do not inspect or copy `luxus`, private run contents, raw prompts, private screenshots, sessions, logs, archives, credentials, caches, or generated dependencies.
- Do not claim that path validation is sandboxing.
- Do not claim general autonomous software engineering.
- Do not convert reported aggregate results into reproduced or production evidence.
- Distinguish my original orchestration design from the AI-assisted portfolio rewrite.
- Attribute Temporal, Hatchet, and Pi accurately; no third-party code will be copied.
- Use the recorded Apache-2.0 license; do not alter it without a new decision.
- Do not publish, deploy, or launch an external agent.

## Definition of done

- A clean checkout can run the synthetic cycle with Python only.
- External execution is disabled by default and covered by a gating test.
- Briefs and allowed paths reject unsafe inputs.
- Queue transitions are explicit and tested.
- Manifests and heartbeats are written atomically and tested.
- Retries and timeouts produce visible attempt history.
- Continuation requires a valid handoff and retains the original brief.
- Fresh-eyes review receives a fresh task context rather than predecessor conversation state.
- Stop markers and configured limits stop safely and visibly.
- The synthetic run creates five visual iterations and a morning summary.
- Documentation distinguishes implemented, synthetic, reported, and unproven claims.
- Screenshots contain synthetic data only.

## Planned validation commands

```bash
python -m unittest discover -s tests -v
python -m nightwatch validate examples/synthetic-brief.json
python -m nightwatch demo --output evidence/synthetic-run --clean
python -m nightwatch status evidence/synthetic-run
python -m compileall -q nightwatch tests
python -m http.server 8000 --directory .
```

Browser validation will cover desktop and mobile layouts, keyboard focus, local links, and console errors. A repository scan will check for hardcoded former paths, accidental secrets, private-source references beyond provenance, and prohibited copied artifacts.

## External validation gate — completed 2026-07-14

One supervised Pi JSON review used synthetic input, read-only tools, an isolated workspace, and explicit dual opt-in. The accepted run completed one acknowledged task in one attempt. It also exposed and led to fixes for Windows command-shim resolution and unacknowledged output being mistaken for success. See `docs/pi-smoke-validation.md`.

## Recovery/handoff validation gate — completed 2026-07-14

A second supervised Pi gate deliberately terminated the first attempt, recovered through one bounded retry, persisted a structured handoff, and launched a fresh `--no-session` reviewer that made one recorded predecessor-artifact read. See `docs/pi-handoff-validation.md`.

## Next product validation gate

Use a real but non-sensitive task defined by another person, with acceptance criteria fixed before execution. This remains separate from publication and does not authorize deployment or broader autonomy claims.
