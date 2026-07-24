# 75-second demo script

## Before recording

```bash
python -m unittest discover -s tests -v
python -m nightwatch demo --output evidence/synthetic-run --clean
python -m http.server 8000 --directory .
```

Open `http://localhost:8000/site/`. Keep the terminal and `evidence/synthetic-run/` available. No network service or external agent is needed.

## 0:00–0:12 — The problem

**Show:** case-study hero.

**Say:**

> Nightwatch was my attempt to make bounded overnight coding-agent work inspectable. The key risk was not only a dead process—it was a live agent drifting from the original brief.

## 0:12–0:25 — The control loop

**Show:** lifecycle section and the four metrics.

**Say:**

> A validated brief becomes explicit queue state, bounded attempts, declared artifacts, structured handoffs, a fresh-context review, and a morning summary. This demonstration is fully synthetic and makes zero external calls.

## 0:25–0:38 — Recovery evidence

**Show:** recovery rail, then `manifest.json` if useful.

**Say:**

> The fixture deliberately fails one implementation attempt and times out one continuation attempt. Both transitions remain visible. Five tasks complete in seven attempts with two bounded retries.

## 0:38–0:50 — Semantic continuity

**Show:** continuation/fresh-eyes section.

**Say:**

> A handoff never replaces the brief. The successor receives both, and the fresh reviewer receives the brief, declared artifacts, and handoff—but no predecessor conversation history.

## 0:50–1:02 — Creative loop

**Show:** five iteration markers and final synthetic SVG.

**Say:**

> Visual work follows a screenshot, critique, revision loop. These five scores are deterministic fixtures that prove stop logic, not design quality.

## 1:02–1:15 — Honest closure

**Show:** failures and boundaries.

**Say:**

> Zombie watchers, path bugs, stale servers, and handoff drift shaped the later Crab/Pi approach. A supervised Pi run now recovers from one deliberate interruption, persists a handoff, and launches a fresh reviewer that reads the predecessor artifact. Nightwatch is still not a Temporal competitor, a sandbox, or autonomous software engineering.

## Optional terminal close

```bash
python -m nightwatch status evidence/synthetic-run
```

Expected headline:

```text
synthetic-nightwatch-cycle: completed
tasks=5 attempts=7 retries=2 handoffs=3 creative_iterations=5
```
