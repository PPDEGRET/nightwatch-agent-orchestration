# Supervised Pi JSON validation

**Date:** 2026-07-14  
**Evidence class:** supervised external smoke test with synthetic input  
**Result:** completed after one acknowledged task attempt

## Scope and controls

One Pi-backed validation ran after the offline package was complete. The task reviewed a fictional Moonleaf notification-permission proposal. It contained no private project data, customer information, raw source prompts, credentials, or production material.

The run used:

- provider/model: `openai-codex/gpt-5.6-luna`;
- Pi JSON event-stream mode;
- read-only tools: `read`, `grep`, `find`, `ls`;
- `--no-session`;
- context files, extensions, skills, and prompt templates disabled;
- one declared output beneath `evidence/pi-smoke-run/workspace/`;
- a 120-second task timeout and 180-second run limit;
- both the configuration opt-in and `--enable-external` CLI flag.

The workspace was disposable and contained only synthetic run state. It was **not** an operating-system sandbox.

## Failures found before the accepted run

The validation exposed three useful integration failures. Their partial run directories were removed after inspection; the lessons and fixes are retained here.

### 1. Windows command-shim resolution

Python `subprocess` could not launch the portable command name `pi` directly because the installed executable was a Windows `pi.CMD` shim. Nightwatch recorded a controlled task failure rather than hanging.

**Fix:** resolve the configured command through `shutil.which()` before launch. A focused test now covers both found and missing executable paths.

### 2. Quiet-process supervision

The first retry was launched through a dispatch wrapper configured to auto-exit after quiet output. Nightwatch intentionally emits no terminal output while Pi is working, so the wrapper killed the in-flight process even though heartbeats were advancing.

**Fix:** supervised external runs disable quiet-time auto-exit and rely on Nightwatch's own timeout/heartbeat boundary. The partial running state was removed before retry.

### 3. Structurally valid but uncorrelated output

The next transport attempt completed, but Pi returned a generic message saying no bounded task had been supplied. The Windows command shim had not safely preserved the multiline prompt. Nightwatch initially accepted the structurally valid assistant message as success; human review correctly rejected it.

**Fixes:**

- generated Pi instructions are now one physical command-line line;
- every instruction requires an exact `NIGHTWATCH_TASK_ACK:<task-id>` first response line;
- Nightwatch strips the marker before persistence;
- missing, mismatched, or content-free acknowledgement is a typed task failure;
- focused tests cover accepted and rejected acknowledgements.

This was the most important result of the validation: process success and valid JSON are not sufficient evidence that the model received the intended task.

## Accepted run result

After the earlier rejected validation attempts were removed, the accepted run completed independently in approximately 40 seconds with one task attempt:

| Measure | Result |
|---|---:|
| Tasks | 1/1 succeeded |
| Attempts | 1 |
| Failed or timed-out attempts | 0 |
| Ordered Nightwatch events | 8 |
| Controller heartbeat sequence | 77 |
| Worker heartbeat sequence | 75 |
| External services | enabled |
| Session/raw prompt retained | no |

Evidence:

- [`evidence/pi-smoke-run/manifest.json`](../evidence/pi-smoke-run/manifest.json)
- [`evidence/pi-smoke-run/execution.json`](../evidence/pi-smoke-run/execution.json)
- [`evidence/pi-smoke-run/summary.md`](../evidence/pi-smoke-run/summary.md)
- [`evidence/pi-smoke-run/workspace/pi-smoke/assessment.md`](../evidence/pi-smoke-run/workspace/pi-smoke/assessment.md)

The final artifact addressed all four requested elements: alignment, one important risk, acceptance criteria, and the next human validation gate. It did not claim research, production evidence, or measured impact.

## What this proves

On this machine and configuration, Nightwatch can:

- resolve and start Pi's Windows command shim;
- select an explicit provider/model route;
- keep controller and worker heartbeats advancing during a silent model call;
- parse the JSON event stream;
- reject an unacknowledged response;
- persist one acknowledged external artifact beneath a declared path;
- close queue and manifest state cleanly.

## What this does not prove

- implementation or code-editing capability;
- safe host isolation;
- reliable retries across provider failures;
- continuation or fresh-eyes behavior across multiple Pi sessions;
- recovery from deliberate interruption;
- production durability, semantic correctness, adoption, or productivity gains.

## Gate completion update

The proposed follow-up was completed on 2026-07-14: Nightwatch recovered from one deliberate Pi interruption, persisted a handoff, and launched a fresh reviewer that made one recorded predecessor-artifact read. See [`pi-handoff-validation.md`](pi-handoff-validation.md).
