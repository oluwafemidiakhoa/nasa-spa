# Saved-history and briefing acceptance contract

## Product/design decisions

The new capability belongs in the existing Retained investigations section, not in another navigation destination. Use the established light field-desk palette and a readable document surface for the briefing. Its primary action explicitly says save on this browser; the tab-only fallback states that export is necessary. Retention is distinct from ordinary review execution. The briefing is for one selected review across all its reference locations, not the date/location search filter, and has plain text and explicit source pointers. No risk rankings, exposure estimates or inferred events are introduced.

## Ingestion and retrieval

Storage boundary: origin and browser profile; this is not a multi-tenant authorization system. IndexedDB database `gaia-observatory-history-v1`, store `archive`, singleton key `reviews`. Exact schema `gaia-saved-history-v1` with safe integer revision and records containing only review ID and earlier/recent evidence byte arrays. Bounds: 20 reviews, 32 MB total evidence, existing 26 MB per bundle limit. The existing comparison verifier reconstructs each report and recomputes its review ID; a bad record blocks publication of the entire restored catalog. No silent repair or auto-overwrite of corrupted data.

Mutations construct a temporary replayed catalog and commit one transaction with revision comparison before replacing the visible in-memory view. Duplicate saves still check revision. Empty clear advances revision. A conflicting tab must reload; it may retain older data in memory until then. Quota/transaction failures surface to the user without optimistic success. Deletion does not erase exported or open-tab copies. Clearing all reviews prompts confirmation in the browser. Database absence or unreadable stored data produces explicit tab-only fallback. No cloud sync, authentication, durable cross-device retention, encryption or automatic refresh.

Retrieval uses exact normalized portfolio identity and location plus review window date, not similarity scores. Each briefing verifies the report hash against its retained metadata and copies fact values from the report with JSON pointers. Source hashes are consistency evidence, not source authentication. Distinct zero, unknown and withheld values remain intact. Two adjacent windows share their boundary instant. No new scientific method or paid resource.

## Acceptance evidence

| Requirement | Local evidence | Browser status |
|---|---|---|
| Save and replay across a reopened catalog; exact bytes and deduplication | PASS, controlled store | INCOMPLETE |
| Failed write leaves original data and UI unchanged | PASS, simulated quota failure | INCOMPLETE |
| Stale concurrent save cannot resurrect deletion | PASS, revision-conflict adapter | INCOMPLETE |
| Clearing and reopening, corrupted identity and source bytes, bounds, copy semantics | PASS, controlled store | INCOMPLETE |
| Unavailable storage does not claim persistence | PASS, unavailable factory check | INCOMPLETE |
| Briefing counts, withheld states, pointers, and digest consistency | PASS, controlled bundles | INCOMPLETE |
| Selected briefing export and removal disable stale download | PASS, DOM adapter | INCOMPLETE |
| Real IndexedDB persistence, screenshots, reflow and actual click flow | Script implemented and attempted | BLOCKED (administrator policy) |

The test suite verifies the persistence coordination logic against a controlled adapter, not browser storage transaction behavior or production endpoints. The actual browser gate is still required. Rollback: discard this separate local overlay; no live deployment or repository changes were made. The previous local design candidate remains unchanged.
