# Interface audit and redesign decisions

## Inspection and scope

Inspected the existing production screenshot (user-provided, showing Gaia Observatory, returned Earth observations and an unavailable solar image), the exact production main revision and Vercel deployment metadata, and local RC11 application source. Production main: `8abf4bcd7f4207088d86e80dc7ae24c7457d6a05`; production tree: `f243f3956c5507133718a97aa5d8554c338f1316`. Vercel reports READY for that revision. The local baseline contains the prior staged RC11 startup fix and catalog, not the entire repository. The current task is a local, reversible UI change; no GitHub writes, production mutations, new paid services, or new upstream credentials.

## Observed shortcomings and dispositions

| Finding | Evidence | Disposition |
|---|---|---|
| Decorative imagery dominated the initial viewport, while My Locations was a small secondary link | Production screenshot and dashboard HTML | Move the observation map and register to the first screen; make the review action primary. Keep reference imagery below operational workflows. |
| Solar image was unavailable, creating a large unproductive tile | Production screenshot | Reduce the reference image's priority and retain an explicit failure message. Delivery itself is still unresolved. |
| FIRMS public data not enabled | Production screenshot and existing `api/gaia-firms.js` gate | Keep truthful disabled/unavailable state. Do not bypass key, quota or production policy. |
| Location setup required manually formatted CSV-like rows | RC11 portfolio HTML | Add labeled ID/coordinate controls, validated add/remove, map and list. Preserve optional batch entry. |
| Reopening a retained bundle left the existing editor configuration displayed | RC11 portfolio controller | Restore the verified bundle's actual configuration on review; new regression covers mismatch and stale result clearing. |
| Null counts could be described as no matching observations | RC11 result rendering | Distinguish no eligible observations from a returned zero; withhold comparisons when needed. |
| The inherited atlas selector specificity would produce dark status boxes with dark text under a new light palette | CSS inspection during implementation | Explicitly override the inherited status and hover color rules. |
| Independent raw-coordinate parsers could disagree on malformed inputs | First implementation review | Centralize parsing and reuse the scientific portfolio validator. Invalid input fails before transport. |
| Research catalog is ephemeral | RC11 catalog contract | Show tab-only retention and export guidance. Persistent multi-device history is not implemented. |

## Design system and rationale

Design concept: a cartographic field desk. The memorable feature is the real observation map, not a hero photograph or a synthetic KPI. The design uses an analytical light work surface and dark geographic canvas rather than another dark four-card gallery. Core colors: paper `#f1f6f7`, white `#ffffff`, deep map `#102f40`, ink `#183344`, action `#145e70`, rules `#c6d7de`; amber points denote returned observations or entered references only, not hazard severity. Humanist Segoe UI/Aptos/Arial stack, tabular numerical summaries, deliberate heading hierarchy, left-aligned copy. No external font or UI libraries.

Homepage: brand/navigation; short task-oriented introduction and primary location action; world observation map and register; thermal, astronomy and space measurements; reference imagery and education. Location page: explicit review settings and coordinate editor; map and entered coordinates; observation comparison, evidence export, and retained investigation search. At narrow widths, stack the editor, map and results. Visually separate source status and scientific limits from measurements.

Accessibility improvements: skip links, main landmark target, labeled inputs, visible focus, minimum target sizes, reduced-motion CSS, keyboard-accessible controls and a text equivalent for map coordinates. Static checks found no unlabeled inputs or invalid in-page anchors on the two changed pages. This is not a WCAG conformance claim. Computed contrast, real focus navigation, visual hierarchy, reflow and screen-reader behavior require browser review.

## Evidence and verdict

Baseline 75/75 targeted JavaScript tests. Final 81/81 targeted JavaScript tests and 4/4 Python helper tests. New tests check coordinate normalization and boundaries, invalid/duplicate inputs, real controller/map DOM-adapter interactions, evidence reopening, stale state, shared parser rejection and markup hierarchy. They use controlled inputs and DOM mocks, not an actual rendered browser. Source/API algorithms have not been changed. Static inspection: 93 unique IDs on the dashboard, 61 unique IDs on My Locations; zero missing local anchors; zero unlabeled inputs/selects/textareas. All 13 linked local destination files exist in the exact production Git tree; this is not a full HTTP navigation pass.

Playwright was executed against a normal loopback server with installed Chromium 144.0.7559.96. The browser launched but navigation failed with `ERR_BLOCKED_BY_ADMINISTRATOR`. The final script returned 2; no candidate screenshots were produced. The earlier actual production screenshot was inspected. No fresh screenshot inspection, actual interaction acceptance, live feed success, or commercial readiness is claimed for the candidate. No browser policy was modified or bypassed.

**Release gate: INCOMPLETE / do not deploy.** Run the controlled browser acceptance on an authorized machine, inspect all five actual screenshots, correct any visual/functional defects and rerun. Independently verify live source delivery and public FIRMS configuration before enabling the latter. Keep the commercial pilot focused on repeated location reviews and useful evidence; no validated customer willingness-to-pay or retention metrics exist yet. The prior production deployment remains unchanged.
