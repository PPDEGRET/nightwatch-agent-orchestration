# Provenance

## Source identity

- **Read-only original:** `C:\Users\henri\Desktop\dev\nightwatch`
- **Source commit:** `bad02335427722d9a034636f0591bcbfeecbc62d`
- **Source branch:** `backup-2026-04-25`
- **Source status at inspection:** not clean; the reported modifications were confined to the explicitly excluded `luxus/` subtree. That subtree was not opened or copied.
- **Destination:** `C:\Users\henri\Desktop\dev\PORTFOLIO\07-nightwatch`
- **Destination starting state:** existing empty directory

The source repository's visible history contained only the sanitized migration-backup commit, so earlier chronology and commit-level authorship could not be reconstructed from this snapshot.

## Safe source material inspected

Only Nightwatch infrastructure material needed to understand the controller was inspected:

- migration README;
- sanitized runtime configuration;
- CLI, watcher, watchdog, continuation, task-status, queue, summary, notification, and usage scripts;
- Windows start/stop wrappers;
- operator, fresh-eyes-review, and cost-format documentation;
- safe Git identity/status metadata.

No source file was modified, formatted, executed, copied recursively, or used to generate state inside the original repository.

## Curated implementation policy

No original source file was copied verbatim into this destination. The source's portable orchestration concepts and state vocabulary were reimplemented as a small Python standard-library controller because:

- the migration snapshot embedded former-machine paths and Git-Bash assumptions;
- documented retries, timeouts, model routing, and fresh review were not consistently enforced;
- a direct copy would preserve contradictions rather than produce a portable case study;
- the destination needed deterministic tests and an offline demonstration.

The original Bash implementation remains only in the read-only source. The portfolio implementation must not be presented as the exact historical runtime.

## Authorship and contribution

### My contribution

I claim the following based on my project direction and the inspected source:

- the Nightwatch concept and overnight operator use case;
- brief-driven runs;
- watcher/watchdog and filesystem-queue approach;
- heartbeats, budgets, retries/timeouts, and quota-window continuation ideas;
- model-routing configuration concept;
- structured continuation and fresh-eyes-review thesis;
- screenshot-based creative iteration;
- the operational lessons connecting Nightwatch to Crab/Pi.

The backup snapshot alone does not independently resolve every file's original author or any collaborator contribution. I remain responsible for any collaborator attribution not resolved by that snapshot.

### AI-assisted portfolio work

Crab/Pi, operating under my direction, assisted with:

- source audit and contradiction analysis;
- Temporal/Hatchet/Pi comparison research;
- the Python portability rewrite;
- schemas, tests, synthetic fixture, and generated evidence;
- documentation, diagrams, static case-study interface, and screenshot preparation.

I retain responsibility for the claims, historical framing, and publication.

## Excluded material

The following was neither inspected nor copied:

- `luxus/` and unrelated project material;
- private run directories or run contents;
- raw prompts and prompt archives;
- sessions, transcripts, model histories, and agent logs;
- private or sensitive screenshots;
- credentials, tokens, cookies, auth state, environment files, or private keys;
- caches, generated dependencies, build outputs, and archives;
- private customer, application, recruiter, account, or personal data;
- source `.git` contents beyond safe read-only metadata commands.

## Historical evidence status

I supplied three aggregate outcomes:

1. one historical run reported as 7/7 tasks complete;
2. one build reported as spanning multiple sessions;
3. one creative workflow reported as taking five screenshot iterations.

The destination contains sanitized reconstruction cards based only on those aggregate statements. Raw evidence is excluded, and the outcomes are labeled **reported historical**, not reproduced or independently verified.

## Synthetic evidence

Public run contents under `evidence/synthetic-run/` and `evidence/fake-task-run/` were generated locally by the destination's `SyntheticRunner`. Their inputs are `examples/synthetic-brief.json` and `examples/fake-task-brief.json` respectively.

The synthetic runs:

- use controlled fixture outcomes; the canonical demo has deterministic timestamps while the separate smoke run records real local timestamps;
- do not invoke Pi, Codex, Claude, or any model;
- do not access an account or network service;
- contain no source project data;
- may be regenerated with the documented commands.

## Supervised external Pi evidence

Two bounded Pi JSON validations used synthetic briefs: the initial smoke test at `examples/pi-smoke-brief.json` and the fault-injected handoff test at `examples/pi-handoff-brief.json`. Accepted runs are stored under `evidence/pi-smoke-run/` and `evidence/pi-handoff-run/`.

- provider/model: `openai-codex/gpt-5.6-luna`;
- tools: read-only `read`, `grep`, `find`, `ls`;
- Pi session persistence: disabled;
- context files, extensions, skills, and prompt templates: disabled;
- generated prompt and raw JSON event stream: not retained;
- results: one acknowledged read-only smoke review, followed by a two-task run that recovered from one deliberate interruption, persisted a handoff, and recorded one reviewer artifact-read tool call;
- workspace: disposable synthetic directory, not an operating-system sandbox.

The validations exposed Windows command resolution, command-shim process-tree termination, quiet-process supervision, unacknowledged-response failures, and a non-terminal worker heartbeat label. Partial, rejected, and superseded output directories were removed after inspection. Accepted artifacts and sanitized execution metadata remain. See `docs/pi-smoke-validation.md` and `docs/pi-handoff-validation.md`.

No credential, token, account state, or Pi session was copied into the destination. The ignored local opt-in configuration was deleted after validation.

Site screenshots contain only synthetic inputs, sanitized aggregate cards, and safe supervised Pi validation results.

## Upstream projects and attribution

No third-party source code was copied.

- **Temporal** is referenced as a general durable-execution comparison: <https://docs.temporal.io/workflows>
- **Hatchet** is referenced as a durable task/AI workflow comparison: <https://docs.hatchet.run/v1/durable-tasks>
- **Pi coding agent:** installed `@earendil-works/pi-coding-agent@0.80.6` metadata lists **Mario Zechner** as author and the repository under **Earendil Works**. Pi is referenced as an optional execution transport. The inspected JSON-mode documentation is pinned to revision [`1f9e846`](https://github.com/earendil-works/pi/blob/1f9e846c84f7d53356e7904e53f67b479d6f9c86/packages/coding-agent/docs/json.md).
- **Nico Bailon:** installed package metadata credits Nico Bailon as author of `pi-subagents`, `pi-interactive-shell`, `pi-mcp-adapter`, `pi-prompt-template-model`, and `pi-web-access`.

Nightwatch's `PiJsonRunner` is my local integration code using Pi's documented CLI surface. The bounded smoke and recovery/handoff tasks are scoped by the evidence statement above. I do not claim authorship of Pi, Nico Bailon's extensions, their providers, or their tooling. See [`ACKNOWLEDGMENTS.md`](ACKNOWLEDGMENTS.md).

## External assets

- No external images, fonts, icons, or stock assets are included.
- Diagrams are original Mermaid descriptions written for this case study.
- SVG evidence cards and creative iterations are generated/original synthetic assets.
- Screenshots are local captures of the destination's static page.

## License

I explicitly selected the **Apache License 2.0** on 2026-07-14. The authoritative text is committed at [`LICENSE`](LICENSE). This selection applies to Nightwatch's repository contents and does not change the licenses or ownership of Pi, Nico Bailon's extensions, Temporal, Hatchet, Playwright, or any other upstream project.

## Publication decisions recorded

The following decisions were recorded on 2026-07-14:

- attribution of Pi to Mario Zechner, with its current repository/package home under Earendil Works;
- attribution of the five named Pi extensions to Nico Bailon;
- the aggregate historical 7/7, multi-session, and five-iteration wording;
- public disclosure of `openai-codex/gpt-5.6-luna` and the bounded supervised Pi evidence;
- retention of the exact machine-local source path in this provenance record;
- the bounded public claim, screenshots, repository settings, and final visual presentation.

## Publication preparation status

All requested attribution, evidence, source-path, claim, visual, repository-setting, and license decisions are recorded. Public repository publication was authorized on 2026-07-23 and completed on 2026-07-24 at <https://github.com/PPDEGRET/nightwatch-agent-orchestration>.
