# Recommended repository settings

Publication configuration for the Nightwatch case study.

## Repository identity

- **Name:** `nightwatch-agent-orchestration`
- **Visibility:** public
- **Default branch:** `main`
- **Description:** `A bounded overnight coding-agent orchestration case study: retries, heartbeats, handoffs, fresh-context review, visual iteration, and the failures that shaped Crab/Pi.`
- **Website:** leave blank; deployment is not authorized
- **Social preview:** `screenshots/nightwatch-overview.png`

## Suggested topics

```text
agent-orchestration
ai-agents
human-in-the-loop
workflow
python
pi-coding-agent
agent-evaluation
case-study
```

## Suggested feature settings

- Issues: enabled
- Discussions: disabled initially
- Wiki: disabled
- Projects: disabled
- Sponsorships: disabled
- Preserve this repository: disabled
- Require signed commits: optional; do not block the initial portfolio release
- Dependabot: unnecessary for runtime code because there are no runtime dependencies; reassess build tooling if CI is added

## Suggested release state

- Publish the repository source first; do not create a release tag until the README and provenance render correctly on the host.
- Do not enable GitHub Pages or another deployment; repository publication does not authorize hosting.
- Do not add badges for coverage, downloads, stars, production status, or package publication unless independently true.

## About text

> Nightwatch is my local, brief-driven experiment in bounded overnight coding-agent work. The packaged case study demonstrates explicit queue state, retries, heartbeats, structured handoffs, fresh-context review, and screenshot iteration—with both negative evidence and one controlled Pi recovery/handoff run.

## License

- **Selected:** Apache License 2.0 (`Apache-2.0`)
- Configure the host platform to detect the committed root [`LICENSE`](../LICENSE) file.
- Do not replace it with an upstream Pi extension's MIT license; upstream attribution remains separate in [`ACKNOWLEDGMENTS.md`](../ACKNOWLEDGMENTS.md).
