# Evidence and limitations

## Evidence policy

This case study separates five evidence classes:

| Class | Meaning | Included here |
|---|---|---|
| Reproduced local | Executed successfully in this destination without external services | tests, deterministic synthetic run, fake-task run, local browser checks |
| Supervised external | Bounded model calls using synthetic input | acknowledged Pi smoke plus fault-injected two-task handoff/review |
| Generated | Produced locally from synthetic fixture data | manifests, events, handoffs, SVG creative iterations, screenshots |
| Reported historical | Aggregate outcome I supplied; raw private evidence excluded | 7/7 task run, multi-session build, five-iteration creative loop |
| Unvalidated | A hypothesis or future gate | uncontrolled outage recovery, real-project handoff quality, user demand, production durability |

A lower evidence class is never used to support a higher claim. A passing test is not customer validation. A synthetic run is not production usage. A screenshot is not proof of autonomy.

## Reproducible synthetic evidence

Run:

```bash
python -m nightwatch demo --output evidence/synthetic-run --clean
```

The committed deterministic run records:

- **5/5 synthetic tasks succeeded**;
- **7 total attempts**;
- **1 recovered synthetic failure**;
- **1 recovered synthetic timeout**;
- **2 explicit retry transitions**;
- **3 structured handoffs**;
- **1 fresh-context review task**;
- **5 generated SVG screenshot iterations**;
- **0 external service or model calls**.

Inspect:

- [`evidence/synthetic-run/manifest.json`](../evidence/synthetic-run/manifest.json)
- [`evidence/synthetic-run/events.jsonl`](../evidence/synthetic-run/events.jsonl)
- [`evidence/synthetic-run/summary.md`](../evidence/synthetic-run/summary.md)
- [`evidence/synthetic-run/handoffs/`](../evidence/synthetic-run/handoffs/)
- [`evidence/synthetic-run/workspace/creative/`](../evidence/synthetic-run/workspace/creative/)

The fixture scores `54, 66, 77, 86, 92` are deliberately deterministic. They demonstrate stop logic and iteration evidence, not visual quality.

### Separate fake-task smoke run

The normal `run` command also completed [`examples/fake-task-brief.json`](../examples/fake-task-brief.json), a fictional Moonleaf launch-readiness task:

- **3/3 tasks succeeded in 4 attempts**;
- **1 transient failure recovered** after the configured real `0.1s` backoff;
- **2 handoffs persisted**;
- **1 fresh-context review completed**;
- **0 external services enabled**;
- task artifacts contain explicitly authored fixture content rather than model output.

Inspect [`evidence/fake-task-run/summary.md`](../evidence/fake-task-run/summary.md) and the [`fresh-eyes.md`](../evidence/fake-task-run/workspace/fake-task/review/fresh-eyes.md) result. Runtime timestamps are real; outcomes and content remain controlled synthetic fixtures.

## Supervised external Pi evidence

Nightwatch completed one acknowledged read-only review using `openai-codex/gpt-5.6-luna` and a fictional Moonleaf brief:

- **1/1 task succeeded in one attempt**;
- **8 ordered events**;
- **77 controller and 75 worker heartbeat sequence values**;
- an exact task acknowledgement was required and removed before artifact persistence;
- the final artifact addressed alignment, risk, acceptance criteria, and a human gate;
- no Pi session, raw JSON stream, generated prompt, or transcript was retained.

The validation first exposed three failures—Windows command-shim resolution, quiet-process auto-termination, and unacknowledged output being mistaken for success. All were corrected or operationally bounded before accepting the final result.

See [`docs/pi-smoke-validation.md`](pi-smoke-validation.md) and [`evidence/pi-smoke-run/execution.json`](../evidence/pi-smoke-run/execution.json).

### Interrupted handoff evidence

A second supervised external gate deliberately terminated the first Pi attempt and then exercised the full continuation boundary:

- **2/2 tasks succeeded in 3 attempts**;
- **1 deliberate failure and 1 retry** remained in task history;
- **1 structured handoff** tied the successor to the predecessor artifact;
- the fresh `--no-session` reviewer made **1 recorded `read` tool call**;
- task records preserve provider/model, acknowledgement, stream-event, and tool-call metadata;
- controller and worker heartbeat records both ended at `completed`;
- no Pi session, raw JSON stream, generated prompt, transcript, or credential was retained.

The accepted result followed two rejected validation runs: one exposed a non-terminal worker heartbeat label; another omitted task acknowledgement and correctly closed with failure. Both issues were fixed or bounded before accepting the final evidence.

See [`docs/pi-handoff-validation.md`](pi-handoff-validation.md) and [`evidence/pi-handoff-run/execution.json`](../evidence/pi-handoff-run/execution.json).

## Focused test evidence

The standard-library suite covers:

- brief schema and dependency validation;
- component-aware allowed paths and resolved containment;
- queue transitions and invalid-state rejection;
- manifest counters and atomic file replacement;
- controller/worker heartbeat freshness;
- bounded retries, backoff, timeouts, and exhausted attempts;
- handoff shape, source matching, and fresh-context inputs;
- max-task, max-failure, runtime, operator-stop, and external-execution gates;
- deterministic end-to-end synthetic output.

Run:

```bash
python -m unittest discover -s tests -v
```

The live path-escape test uses a symbolic link where available and a non-admin Windows directory-junction fallback otherwise; it ran successfully in the validated environment.

Focused desktop/mobile browser, keyboard, console, network, and local-link results are recorded in [`docs/browser-validation.md`](browser-validation.md).

## Packaging smoke evidence

An offline wheel was built with `PIP_NO_INDEX=1`, installed into a temporary target without dependencies, and executed from outside the repository. The installed package validated the fixture and completed the same 5-task/7-attempt synthetic cycle. Temporary wheel, install, build, and run files were removed after validation.

## Sanitized historical evidence

### Reported 7/7 task run

I reported one historical Nightwatch run as completing all seven planned tasks. Raw task prompts, outputs, logs, project details, and screenshots are excluded. This portfolio does not independently reproduce the result.

### Reported multi-session build

I reported using continuation across multiple sessions to advance one build. The case study retains only the operational lesson: a successor needs the original brief plus a structured handoff. No private build content or session transcript is included.

### Reported five-iteration creative loop

I reported a visual workflow that took five screenshot/revision passes. The raw screenshots are excluded. The portfolio recreates the loop mechanics with explicitly synthetic SVG cards rather than presenting private imagery as public evidence.

See [`evidence/historical/`](../evidence/historical/) for compact sanitized reconstruction cards.

## What is implemented

- single-controller local task sequencing;
- structured brief validation;
- logical model-route recording;
- atomic individual JSON/text writes;
- explicit queue-state directories;
- separate controller and worker heartbeats;
- typed failure, timeout, retry, and cooperative-stop paths;
- structured continuation handoffs;
- fresh-context review inputs without predecessor conversation history;
- deterministic screenshot-loop artifacts;
- morning summary generation;
- dual opt-in gate, portable Windows command resolution, task acknowledgement, required output phrases, fault injection, execution metadata, and external handoff handling for Pi JSON execution.

## Important limitations

1. **Not distributed durability.** There is no database, event-history replay, leader election, worker lease, or multi-host recovery.
2. **One controller.** Concurrent writers are unsupported; JSONL append is designed for a single local controller.
3. **Not a sandbox.** Allowed paths constrain Nightwatch records and synthetic writes. They cannot prevent a host process from accessing other files.
4. **Controlled Pi evidence only.** One interruption/retry/handoff path succeeded under Nightwatch-controlled fault injection. No uncontrolled outage, host crash, code-editing workload, deployment, or real project was validated.
5. **No general semantic correctness metric.** Acknowledgements and required phrases establish bounded protocol compliance; human review—not the controller—judged the artifacts relevant to this synthetic brief.
6. **Fresh context is protocol-level.** It excludes predecessor conversation in this controller; an external provider may retain account-level behavior outside Nightwatch's control.
7. **Creative scores are fixtures.** They do not measure design quality, accessibility, preference, or conversion.
8. **Crash consistency is limited.** Individual moves/writes are atomic, but queue files, manifest, and event log are not one cross-file transaction.
9. **Historical evidence is aggregate only.** Private source evidence was intentionally not inspected or copied.
10. **No quota-window simulation.** Provider credit-reset handling is retained as a historical design lesson; the offline package neither calls a provider nor simulates account billing windows.
11. **Runner contract boundary.** The controller supplies timeout, heartbeat, and stop callbacks, but an arbitrary in-process runner could ignore them. The provided Pi adapter owns a process termination path; the synthetic runner exercises typed fixture outcomes.
12. **No adoption evidence.** There are no verified customers, users, revenue, or production outcomes.

## Safe claims

- I designed a local overnight coding-agent orchestration prototype.
- The prototype explored briefs, queues, heartbeats, retries, handoffs, fresh review, quota-aware continuation, and visual iteration.
- The packaged controller reproduces those control-loop ideas with deterministic synthetic data.
- One supervised Pi JSON smoke review completed, followed by a supervised two-task recovery/handoff run with a verified predecessor-artifact read.
- The failure modes informed later Crab/Pi operating principles.

## Claims not made

- general autonomous software engineering;
- production-grade durable execution;
- secure host isolation;
- superior reliability to Temporal, Hatchet, or other workflow systems;
- independent verification of historical aggregate outcomes;
- customer adoption, revenue, accuracy, or productivity improvement.

## Next validation gate

Use a real but non-sensitive task defined by another person, with acceptance criteria fixed before execution. Preserve failures and compare the result with the immutable brief; do not broaden the claim to general autonomy.
