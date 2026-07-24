# Browser validation record

**Validation date:** 2026-07-14  
**Ephemeral QA endpoint:** `http://127.0.0.1:49407/site/`  
**Public demo command (port may be changed if occupied):** `python -m http.server 8000 --directory .`  
**Content class:** synthetic demonstrations, sanitized aggregate evidence, and one safe supervised Pi smoke result

## Checks performed

| Check | Result | Evidence |
|---|---|---|
| Desktop layout | Pass at 1440 × 1000 | [`screenshots/nightwatch-overview.png`](../screenshots/nightwatch-overview.png) |
| Creative-loop section | Pass at desktop width | [`screenshots/nightwatch-creative-loop.png`](../screenshots/nightwatch-creative-loop.png) |
| Pi validation card | Pass at desktop width | [`screenshots/nightwatch-pi-validation.png`](../screenshots/nightwatch-pi-validation.png) |
| Mobile layout | Pass at 390 × 844 | [`screenshots/nightwatch-mobile.png`](../screenshots/nightwatch-mobile.png) |
| Mobile horizontal overflow | Pass | document width did not exceed the 390 px viewport after the responsive fix |
| Mobile navigation | Pass | all four in-page links remained visible at 390 px |
| Keyboard entry | Pass | first `Tab` focused the visible “Skip to case study” link |
| Semantic structure | Pass in accessibility snapshot | one main landmark, labelled navigation, ordered heading hierarchy, labelled figures/table region |
| Image alternatives | Pass | all four HTML images have non-empty `alt` text; SVGs include titles/descriptions |
| Console | Pass | 0 errors, 0 warnings after favicon correction |
| Network boundary | Pass | six same-origin static requests; responses were 200 or cached 304; no external request |
| Local references | Pass | 23 HTML `href`/`src` references checked; 0 missing; 17 fragment IDs checked |

## Responsive correction made during validation

The first 390 px pass found seven pixels of document overflow caused by CSS grid items retaining their min-content width. `min-width: 0` was added to the architecture cards and scroll containers. A second pass reported no horizontal overflow.

The first mobile design also removed the navigation. The final stylesheet retains a compact, horizontally safe four-link navigation.

## Accessibility foundations verified

- document language is declared;
- skip link precedes site navigation;
- focus uses a visible high-contrast outline;
- navigation and comparison table regions are labelled;
- heading levels are ordered;
- color is not the only state cue in task/recovery labels;
- the page honors `prefers-reduced-motion` by disabling smooth scrolling;
- the comparison table remains keyboard-focusable and horizontally scrollable on narrow screens.

## Limits of this validation

- This is a focused manual browser smoke check, not a formal WCAG conformance audit.
- No screen-reader application or automated color-contrast engine was run.
- Mermaid diagrams are intended for Markdown renderers and were not rendered in the static page.
- Browser checks cover the static case-study interface; the Pi worker run was validated separately through its manifest, events, heartbeats, and artifact.
