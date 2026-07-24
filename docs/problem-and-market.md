# Problem and market thesis

## Who experiences the problem?

Nightwatch was designed for a founder-operator or technical lead who wants to delegate a bounded block of implementation work overnight and inspect the result the next morning.

The user is not asking for unlimited autonomy. They are making a narrower operational decision:

> Can this brief be advanced unattended without losing intent, writing into the wrong workspace, or hiding a stalled process behind plausible-looking output?

## What the normal alternatives miss

A terminal command can launch an agent, but it does not create an operator-readable control loop. A task queue can retry a failed process, but it does not know whether a successor model understood the original objective. A screenshot proves that pixels rendered, but not that the right server or revision produced them.

General durable workflow systems such as Temporal and Hatchet provide stronger infrastructure primitives than Nightwatch. Their core concern is reliable execution of application workflows. Nightwatch explored an application-specific layer above those primitives:

- preserving the original human brief across context boundaries;
- making continuation a recorded protocol rather than an improvised prompt;
- treating provider quota windows as explicit pauses;
- requiring a fresh-context review after handoff;
- iterating visual work through captured output rather than prose alone;
- preparing a concise evidence package for morning review.

## My thesis

My working thesis was that unattended coding-agent work fails in two independent ways:

1. **Operational failure:** a process hangs, a watcher dies, a timeout is missed, a path is wrong, or a server is stale.
2. **Semantic failure:** the process remains active but the work drifts from the original brief, inherits a bad assumption, or treats an incomplete handoff as ground truth.

A credible overnight controller therefore needed both ordinary orchestration state and explicit intent-preservation boundaries.

## Designed intervention

Nightwatch represented the overnight run as an inspectable sequence:

1. validate and freeze the brief;
2. derive bounded tasks and declared output paths;
3. move each task through explicit queue states;
4. record attempts, heartbeats, timeouts, and retries;
5. persist a structured continuation handoff without replacing the brief;
6. run a fresh-context review against the brief and artifacts;
7. use screenshot-based iteration when visual quality matters;
8. produce a morning summary for human acceptance.

The portfolio implementation makes that intervention deterministic and runnable without any external service.

## Why not build on Temporal or Hatchet here?

For production durability, a mature workflow engine would usually be preferable to a filesystem queue. This case study is intentionally local because its purpose is to expose my agent-operation thesis and the failure evidence that shaped Crab/Pi—not to present a new distributed scheduler.

Adding a server, database, workers, or cloud control plane would make the demonstration harder to reproduce while doing little to strengthen the central insight.

## Commercial relevance

The underlying need is relevant anywhere an operator delegates consequential work to agents:

- small product teams running bounded maintenance or research tasks;
- agencies preparing next-morning drafts or audits;
- founders using overnight compute windows;
- internal AI-tooling teams designing reviewable agent workflows.

The commercial hypothesis remains unvalidated. There is no claim of customers, adoption, production usage, revenue, or willingness to pay.

## Trade-offs

- **Local state over distributed durability:** easier to inspect and reproduce, weaker under concurrent writers or machine failure.
- **Structured JSON over free-form prompts:** easier to validate and test, less expressive.
- **Fresh invocations over hidden continuity:** reduces inherited context, increases handoff burden.
- **Synthetic default over impressive live output:** safer and reproducible, not evidence of real model performance.
- **Human acceptance over automatic shipping:** slower, but appropriate for an unproven controller.

## Next validation gate

The supervised Pi gates now include acknowledged task correlation and a two-task recovery/handoff run with one deliberate interruption and one verified predecessor-artifact read. The next gate is a real but non-sensitive task defined by another person, with acceptance criteria fixed before execution.
