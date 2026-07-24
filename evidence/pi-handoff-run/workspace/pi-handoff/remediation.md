## Proposed intervention

In Moonleaf’s plant setup flow, defer the notification-permission request until the user has both saved a plant and selected a care window. Present the request only after those two actions.

## Acceptance criteria

- No notification-permission request appears before a plant is saved.
- No request appears after saving but before selecting a care window.
- After both actions are complete, the request is presented.

## Human validation gate

A human reviewer verifies the sequence in a fictional Moonleaf walkthrough and confirms that the request is absent until both required actions are complete.
