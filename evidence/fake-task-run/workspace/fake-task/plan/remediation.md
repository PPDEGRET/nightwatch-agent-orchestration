# Synthetic task artifact

> **Synthetic demonstration.** No model, network service, or external agent was called.

## Task

**Draft a bounded remediation plan** (`draft-fake-plan`)

## Objective retained

Prepare a reviewable launch-readiness note for Moonleaf, a fictional nocturnal plant-care app: identify one onboarding risk, propose a bounded remediation plan, and independently review that plan against this original brief.

## Continuity

Loaded handoff from `inspect-fake-brief` while retaining the original brief. Next step: Draft one bounded remediation plan for the identified onboarding risk.

## Context boundary

Task ran in an isolated synthetic attempt context.

## Fixture output

### Bounded intervention

1. Defer the notification prompt until the user saves a first plant and selects a preferred care window.
2. Show a short pre-permission explanation using the selected plant and window.
3. Keep a visible skip path and allow reminders to be enabled later in settings.

### Acceptance criteria

- No notification prompt appears before a plant is saved.
- Skipping never blocks onboarding.
- The selected care window is retained without requiring notification access.
- A human reviews the copy and permission timing before release.

## Result

Deterministic fixture completed on attempt 2 using logical model route `implementation`.
