# Moonleaf Plan Review

**Alignment:** Strong. The plan delays notification permission until the user has saved a plant and selected a care window, explains the benefit briefly, preserves an explicit skip path, and supports enabling reminders later.

**Important risk:** The post-setup prompt could still feel coercive or be misunderstood if the explanation and skip action are not immediately clear.

**Acceptance criteria:**
- No permission prompt appears before the first plant is saved and a care window is selected.
- A short explanation appears before the OS permission prompt.
- Skip is visible, non-blocking, and completes the flow.
- Users who skip can enable reminders later from a clear location.
- Declining or dismissing does not prevent core plant-care use.

**Next human validation gate:** Run a scripted walkthrough covering save, care-window selection, allow, skip, decline, and later re-enable scenarios; confirm the sequence, copy, and recovery paths are understandable.
