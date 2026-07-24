# Nightwatch

**A portable case study in bounded overnight coding-agent orchestration—and the failures that shaped Crab/Pi.**

> **Synthetic demonstration:** the default run makes no model, account, agent, or network call. Historical evidence is aggregate-only and clearly labeled.

Nightwatch began as my custom local controller for turning a structured overnight brief into queued agent work, continuation handoffs, visual iterations, and a next-morning review. This public repository is a new Python reimplementation—not the exact historical Bash runtime. It preserves the operating thesis while replacing the brittle migration snapshot with a deterministic, standard-library implementation.

It does **not** claim general autonomous software engineering, distributed durability, secure sandboxing, production adoption, or superiority to Temporal or Hatchet.

## The case in one minute

| Question | Answer |
|---|---|
| **Who has the problem?** | A founder-operator delegating bounded coding work overnight. |
| **What goes wrong?** | Processes hang, paths drift, servers go stale, and successor agents lose the original intent. |
| **My thesis** | Reliable unattended work needs both process recovery and semantic-continuity controls. |
| **Intervention** | Immutable brief → explicit queue → bounded attempts → handoff → fresh review → visual loop → morning summary. |
| **Working evidence** | 51 focused tests; deterministic baseline; separate fake-task run; acknowledged Pi smoke; process-tree-fault-injected two-task Pi handoff. All tests pass on the validated Windows environment. |
| **Measured result** | The handoff gate completes 2/2 tasks in 3 attempts after one deliberate failure, with one persisted handoff and one reviewer artifact-read tool call. |
| **Critical limitation** | The scenario and acceptance criteria are synthetic; one controlled recovery does not establish production reliability or implementation ability. |
| **Next gate** | A real but non-sensitive task defined by another person with acceptance criteria fixed before execution. |

## Why this is not Temporal or Hatchet

Temporal and Hatchet already provide much stronger general workflow infrastructure:

- [Temporal](https://docs.temporal.io/workflows) provides durable workflow execution, event history, retries, and activity failure detection.
- [Hatchet](https://docs.hatchet.run/v1/durable-tasks) provides Postgres-backed durable tasks and explicitly addresses AI-agent workloads.

Nightwatch's narrower contribution is the **operator protocol above the queue**: preserve the brief, make context handoffs explicit, use a fresh reviewer, treat provider windows as operational state, inspect visual output iteratively, and prepare morning evidence.

See [the market thesis](docs/problem-and-market.md) and [architecture diagrams](docs/architecture.md).

## Run the safe demonstration

Requires Python 3.11+; no installation or dependency download is required.

```bash
python -m nightwatch validate examples/synthetic-brief.json
python -m nightwatch demo --output evidence/synthetic-run --clean
python -m nightwatch status evidence/synthetic-run
```

Expected status:

```text
synthetic-nightwatch-cycle: completed
tasks=5 attempts=7 retries=2 handoffs=3 creative_iterations=5
```

The run intentionally simulates:

1. one transient implementation failure;
2. one continuation timeout;
3. two successful bounded retries;
4. three persisted handoffs;
5. a fresh-context review;
6. five screenshot-loop iterations with fixture scores `54 → 66 → 77 → 86 → 92`.

Inspect the [morning summary](evidence/synthetic-run/summary.md), [manifest](evidence/synthetic-run/manifest.json), [ordered events](evidence/synthetic-run/events.jsonl), and [creative report](evidence/synthetic-run/workspace/creative/report.md).

### Separate fake-task smoke run

A second brief exercises the normal `run` command rather than the built-in demo:

```bash
python -m nightwatch validate examples/fake-task-brief.json
python -m nightwatch run examples/fake-task-brief.json --runner synthetic --output evidence/fake-task-run
```

The fictional Moonleaf task identifies an early notification-permission risk, deliberately recovers one failed attempt after a real `0.1s` backoff, persists two handoffs, and runs a fresh-context review. It completed **3 tasks in 4 attempts** with external services disabled. Inspect its [summary](evidence/fake-task-run/summary.md) and [review artifact](evidence/fake-task-run/workspace/fake-task/review/fresh-eyes.md).

## Run the focused tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q nightwatch tests
```

Coverage includes:

- brief validation and dependency cycles;
- component-aware allowed paths and resolved containment;
- queue transitions;
- manifests and atomic writes;
- controller/worker heartbeats;
- retries, backoff, timeouts, and exhausted attempts;
- handoffs and fresh-context review inputs;
- task, failure, runtime, operator-stop, and external-execution conditions;
- deterministic end-to-end output.

## How the packaged controller works

```text
brief.json
    ↓ validate + freeze
manifest / planned queue
    ↓ dependency-ready claim
Runner interface
    ├── SyntheticRunner  ← default, deterministic, offline
    └── PiJsonRunner     ← optional, dual opt-in, not a sandbox
    ↓
artifacts + handoffs + heartbeats + events
    ↓
fresh-eyes review + creative loop
    ↓
summary.md → human acceptance
```

Every task declares dependencies, outputs, timeout, retry policy, logical model route, and optional handoff behavior. Queue state is represented by inspectable JSON files under `queue/<state>/`. Nightwatch validates every synthetic output against component-aware allowed paths before writing.

The full lifecycle and four required diagrams are in [`docs/architecture.md`](docs/architecture.md).

## What changed from the migration snapshot

The read-only snapshot contained valuable design work but conflicting execution paths. The portfolio package:

- replaces former hardcoded Windows/Git-Bash roots with CLI paths and relative configuration;
- gives the controller—not prose or a hidden direct orchestrator—ownership of state transitions;
- creates `brief.json`, manifests, handoffs, and queue records in one run root;
- enforces configured retry and stop limits;
- separates controller and worker heartbeats;
- represents fresh-eyes review as an explicit task property;
- treats allowed paths as validation, never as a host sandbox;
- uses new public synthetic instructions rather than source raw prompts;
- repairs the migration README by replacing it with this reproducible case study.

The original was not edited. See [`PROVENANCE.md`](PROVENANCE.md).

## Optional Pi execution

Pi is the proposed worker transport—the equivalent boundary to a structured `codex exec` invocation—not Nightwatch's scheduler or state store. The local Pi build documents print, JSON, RPC, and SDK modes; JSON mode fits bounded fresh-context attempts.

The inspected Pi JSON-mode documentation is pinned to upstream revision [`1f9e846`](https://github.com/earendil-works/pi/blob/1f9e846c84f7d53356e7904e53f67b479d6f9c86/packages/coding-agent/docs/json.md). The adapter cannot run unless **both** controls are present:

1. `external_services.enabled` is changed to `true` in a local configuration;
2. `--enable-external` is passed on the command line.

An explicit provider/model route is also required:

```bash
python -m nightwatch run examples/your-brief.json --runner pi --config path/to/local-config.json --enable-external --output .nightwatch/supervised-run
```

**Do not run this on a sensitive host workspace.** Pi runs with the user's permissions; Nightwatch's allowlist is not isolation. Use a disposable workspace or container.

## Supervised Pi JSON validation

One bounded external smoke test used `openai-codex/gpt-5.6-luna`, read-only tools, an isolated synthetic workspace, no saved Pi session, and explicit dual opt-in.

The accepted run:

- completed **1/1 task in one attempt**;
- persisted a useful 990-character review artifact;
- recorded **8 ordered events**, **77 controller heartbeats**, and **75 worker heartbeats**;
- retained no raw JSON stream, generated prompt, session, or transcript;
- required an exact task acknowledgement before accepting output.

The validation first exposed and fixed Windows `.CMD` resolution, quiet-process supervision, and a false-positive unacknowledged response. Those failures are part of the evidence, not omitted history.

Inspect the [validation record](docs/pi-smoke-validation.md), [execution metadata](evidence/pi-smoke-run/execution.json), [morning summary](evidence/pi-smoke-run/summary.md), and [Pi-produced assessment](evidence/pi-smoke-run/workspace/pi-smoke/assessment.md).

### Interrupted handoff gate

A second bounded external run deliberately terminated the first Pi attempt, recovered through the configured retry, persisted a structured handoff, and launched a fresh `--no-session` reviewer. The reviewer made one recorded `read` tool call against the predecessor artifact.

- **2/2 tasks succeeded** in **3 attempts**;
- **1 deliberate failure**, **1 retry**, and **1 handoff** remained visible;
- both task responses were acknowledged and met required output phrases;
- controller and worker heartbeats ended at `completed`;
- no raw prompts, Pi sessions, transcripts, credentials, or private project data were retained.

Read [`docs/pi-handoff-validation.md`](docs/pi-handoff-validation.md) and inspect [`evidence/pi-handoff-run/`](evidence/pi-handoff-run/).

## Historical evidence, honestly scoped

I supplied three aggregate historical outcomes:

- one Nightwatch run reported as **7/7 tasks complete**;
- one build reported as spanning **multiple sessions**;
- one creative workflow reported as taking **five screenshot iterations**.

Raw prompts, runs, sessions, logs, private project details, and screenshots were excluded. The public cards in [`evidence/historical/`](evidence/historical/) are sanitized reconstructions, not independent verification.

See [`docs/evidence-and-limitations.md`](docs/evidence-and-limitations.md) for the complete evidence hierarchy.

## Failures that shaped Crab

Nightwatch's strongest evidence is negative evidence:

- **Zombie watchers:** a living PID or stale shared heartbeat did not prove progress.
- **Path bugs:** machine-specific roots and string-prefix checks could target the wrong workspace.
- **Stale servers:** a valid screenshot could still show the wrong running revision.
- **Handoff drift:** a successor could preserve activity while losing the original intent.

Each failure now maps to a controller rule and a later Crab/Pi operating principle. Read [`docs/failures-that-shaped-crab.md`](docs/failures-that-shaped-crab.md).

## View the case-study page

```bash
python -m http.server 8000 --directory .
```

Open <http://localhost:8000/site/>. The page uses no external scripts, fonts, analytics, or assets.

A concise recording walkthrough is in [`docs/demo-script.md`](docs/demo-script.md). The completed desktop/mobile, keyboard, console, network, and local-link checks are recorded in [`docs/browser-validation.md`](docs/browser-validation.md).

## Repository map

```text
ACKNOWLEDGMENTS.md           upstream authorship and tooling credits
LICENSE                      Apache License 2.0
PUBLISH_CHECKLIST.md         completed release-readiness record
nightwatch/                  portable controller and runner adapters
examples/                   offline, fake-task, and Pi validation briefs
config/                      portable example configuration
schemas/                     brief, manifest, heartbeat, and handoff schemas
tests/                       focused standard-library test suite
evidence/synthetic-run/      deterministic offline baseline
evidence/fake-task-run/      separate synthetic CLI smoke run
evidence/pi-smoke-run/       supervised acknowledged Pi JSON evidence
evidence/pi-handoff-run/     fault-injected recovery and fresh-review evidence
evidence/historical/         sanitized reported-outcome cards
docs/                        market thesis, architecture, failures, evidence, demo, browser/Pi QA
site/                        accessible static case-study page
screenshots/                 synthetic and supervised Pi evidence captures
```

## Acknowledgments and license

The installed Pi package metadata credits **Mario Zechner** as author, with Pi's current repository/package home under **Earendil Works**. Installed metadata credits **Nico Bailon** for `pi-subagents`, `pi-interactive-shell`, `pi-mcp-adapter`, `pi-prompt-template-model`, and `pi-web-access`.

See [`ACKNOWLEDGMENTS.md`](ACKNOWLEDGMENTS.md) for the full attribution boundary.

Nightwatch is licensed under the [Apache License 2.0](LICENSE), which I selected explicitly. Upstream projects retain their own authorship and licenses.

## Important limitations

- single local controller, not distributed execution;
- no database, replay engine, leases, or multi-host recovery;
- no host sandbox;
- one controlled Pi interruption/retry/handoff succeeded, but no uncontrolled outage, code implementation, deployment, or real-project Pi evidence;
- no general metric for semantic correctness;
- no customer, adoption, revenue, or production evidence;
- historical outcomes are reported aggregates only;
- cross-file state is inspectable but not transactionally atomic.

## Status

**Portfolio status:** published as a public-source case study. Technical gates, Apache-2.0 licensing, upstream attribution, and hosted CI are recorded in [`PUBLISH_CHECKLIST.md`](PUBLISH_CHECKLIST.md). No deployment has been authorized.

**Next validation gate:** a real but non-sensitive task defined by another person, with acceptance criteria fixed before execution. This is product validation—not permission to deploy or claim general autonomy.
