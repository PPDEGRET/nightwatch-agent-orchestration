# Acknowledgments

Nightwatch is my local orchestration concept and case study. I developed and packaged it using an open-source agent-tooling ecosystem whose authorship remains separate from my work.

## Pi coding agent

The installed package metadata for `@earendil-works/pi-coding-agent@0.80.6` lists **Mario Zechner** as author. The current package namespace and repository home are maintained under **Earendil Works**:

- <https://github.com/earendil-works/pi>

Nightwatch uses Pi's documented JSON CLI mode as an optional worker transport. I do not claim authorship of Pi, its core packages, providers, model integrations, or CLI tooling.

## Nico Bailon's Pi extensions

Installed package metadata lists **Nico Bailon** as author of:

- [`pi-subagents`](https://github.com/nicobailon/pi-subagents) — subagent delegation, chains, and parallel execution;
- [`pi-interactive-shell`](https://github.com/nicobailon/pi-interactive-shell) — supervised interactive and background agent processes;
- [`pi-mcp-adapter`](https://github.com/nicobailon/pi-mcp-adapter) — Model Context Protocol integration for Pi;
- [`pi-prompt-template-model`](https://github.com/nicobailon/pi-prompt-template-model) — prompt-template model selection and execution;
- [`pi-web-access`](https://github.com/nicobailon/pi-web-access) — web research and content retrieval tools.

These packages were part of the working Pi harness used to research, review, or validate this portfolio closure. Their source code is not copied into Nightwatch, and I do not claim authorship of them.

## Workflow comparisons

Nightwatch documentation references, but does not copy or claim authorship of:

- [Temporal](https://temporal.io/) and its durable workflow model;
- [Hatchet](https://hatchet.run/) and its durable task/AI workflow model.

## Browser validation

The static case-study interface was validated locally through Playwright browser automation. No Playwright source or generated dependency is included in this repository.

## Attribution and license boundary

Upstream package licenses apply to their respective upstream projects. No third-party source is vendored here, and upstream MIT licenses do **not** govern Nightwatch itself.

I explicitly selected the **Apache License 2.0** for Nightwatch on 2026-07-14. See [`LICENSE`](LICENSE). That selection applies to Nightwatch's repository contents; it does not alter any upstream project's license or attribution.
