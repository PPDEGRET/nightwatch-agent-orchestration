# Publication readiness checklist

## Current recommendation

**Ready for public repository publication. All preparation gates and publication decisions are recorded.**

Nightwatch now has deterministic offline evidence, a separate synthetic CLI run, one acknowledged Pi smoke task, and one supervised two-task Pi recovery/handoff run. The public claim must remain bounded to local agent orchestration and its operational lessons.

## Automated and reproducible gates

- [x] Source repository remained read-only.
- [x] Curated destination contains no recursively copied source tree.
- [x] Portable Python 3.11+ implementation has no runtime dependencies.
- [x] Structured brief validation covers unsafe paths, dependencies, cycles, and controller-state protection.
- [x] Queue, manifest, heartbeat, retry, timeout, handoff, fresh-context, stop, and Pi-runner behavior have focused tests.
- [x] Default synthetic run completes without external services.
- [x] Separate fake-task run completes through the normal CLI.
- [x] Pi JSON command resolution and task acknowledgement are externally validated.
- [x] Windows npm shim resolves to the direct Node CLI; process-tree cleanup fails closed before retry.
- [x] Fault-injected Pi attempt is preserved and recovered by a bounded retry near the configured threshold.
- [x] Structured handoff is consumed by a fresh no-session reviewer.
- [x] Review stream records and validates the exact predecessor-artifact `read` path.
- [x] Controller and worker heartbeats end in terminal `completed` state.
- [x] Offline wheel build/install/demo works without dependency downloads.
- [x] Static case-study page passes desktop/mobile, keyboard, overflow, console, network, and local-link checks.
- [x] Public screenshots and SVGs contain synthetic or sanitized evidence only.
- [x] No raw prompts, sessions, transcripts, credentials, caches, dependencies, or private source evidence are retained.
- [x] Claims distinguish reproduced, supervised external, reported historical, and unvalidated evidence.
- [x] No deployment, outreach, or production action was performed.

## Final automated verification — 2026-07-14

- **Tests:** 51 run; 51 passed. The path-escape test used the Windows directory-junction fallback because symbolic-link privileges were unavailable.
- **Static checks:** Python compilation and Ruff passed.
- **Briefs/runs:** all four briefs validated; offline baseline, fake-task, Pi smoke, and Pi handoff runs are terminal `completed`.
- **Recovery evidence:** process-tree fault event at 1.20s; failed transition 0.25s later; 2/2 tasks succeeded in 3 attempts.
- **Continuity evidence:** one handoff; fresh reviewer read path recorded as `pi-handoff/remediation.md`.
- **Package:** Apache-2.0 metadata and canonical license text verified; wheel contains 20 expected files including `LICENSE`, has no runtime dependencies, installs offline, and runs the demo outside the repository.
- **Content integrity:** 46 JSON files parsed; 66 local Markdown links, 23 site references, and 17 fragment IDs resolved.
- **External references:** Temporal, Hatchet, and pinned Pi documentation fetched successfully; Pi and Nico Bailon repository/author links match installed package metadata.
- **Browser:** desktop/mobile, keyboard entry, console, same-origin network, responsive overflow, and image alternatives passed.
- **Privacy/security scan:** zero credential patterns, sensitive files, symlinks, script-bearing SVGs, or PNG textual metadata; only `PROVENANCE.md` contains the required machine-local source path.

## Publication decisions recorded — 2026-07-14

- [x] **Authorship and ecosystem attribution:** Pi credited to Mario Zechner with its current home under Earendil Works; the five named Pi extensions credited to Nico Bailon.
- [x] **Historical claims:** aggregate wording fixed for the reported 7/7 run, multi-session build, and five-iteration creative loop.
- [x] **External evidence:** `openai-codex/gpt-5.6-luna` and the supervised Pi evidence artifacts may be disclosed publicly.
- [x] **Source path:** exact machine-local source path retained in `PROVENANCE.md`.
- [x] **License:** Apache License 2.0 selected; root `LICENSE` committed and package metadata updated.
- [x] **Repository settings:** public `nightwatch-agent-orchestration` settings recorded in [`docs/repository-settings.md`](docs/repository-settings.md).
- [x] **Final visual review:** site, four screenshots, README presentation, and Mermaid diagrams reviewed.
- [x] **Claim review:** bounded claims and explicit non-claims fixed for publication.

No preparation blocker remains. Public repository publication was authorized on 2026-07-23; deployment remains unauthorized.

## Recommended public claim

> Nightwatch is a local, brief-driven controller I built to explore bounded overnight coding-agent work. The packaged case study demonstrates explicit queue state, heartbeats, retries, structured handoffs, fresh-context review, and screenshot iteration. A supervised synthetic-input Pi run recovered from one deliberate interruption and produced a reviewed handoff. It is not a distributed workflow engine, host sandbox, production reliability claim, or general autonomous engineer.

## Do not publish as

- a Temporal or Hatchet replacement;
- production-grade durable execution;
- autonomous software engineering;
- a secure sandbox;
- customer, adoption, revenue, or productivity evidence;
- proof that one model/provider will behave consistently elsewhere.

## Post-publication validation gate

Use a real but non-sensitive task defined by another person, with acceptance criteria chosen before execution. Preserve failures and compare the result with the immutable brief. This is product validation, not permission to deploy or act on external systems.
