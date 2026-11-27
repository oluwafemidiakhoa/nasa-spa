# Gaia Observatory: provenance-aware knowledge architecture

Status: RC11 local candidate integrated into My Locations; not deployed to production. Baseline production revision: `8abf4bcd7f4207088d86e80dc7ae24c7457d6a05` (RC10). This architecture is for retained scientific investigations, not a validated hazard prediction system. It requires no database or model API in the prototype.

## Goal and bounded use cases

Return an exact history of the observations in retained reviews of a specified portfolio version and location. Answer which returned records appeared in only one of the two windows, while preserving missing and withheld results. Let the owner export the original evidence. Never infer a new disaster, safety, causal effect, change in hazard or event rate from these comparisons.

## Ingestion contract

| Entity | Identity and invariants | Local storage |
|---|---|---|
| Source receipt | Source schema, recorded retrieval time, source digest, original decoded bytes, source category and UTC query. Validate size, hashes and schema using existing bundle inspection. Authentication and completeness are unknown. | Inside retained bundles |
| Portfolio version | SHA-256 of UTF-8 JSON of the canonical `portfolio()` result: sorted IDs, coordinates, category and radius. The version prevents a renamed or moved site being compared across incompatible configurations. This digest is not an access credential. | In-memory catalog |
| Review | Recomputed `compare(previous,current)` result, derived report digest, and both bundle digests; review identity is SHA-256 of JSON array `["gaia-catalog-v1", previousBundleSha256, currentBundleSha256, reportSha256]`. Reject arbitrary reports, corrupted inputs, incompatible portfolios and reversed or nonadjacent windows. | In-memory catalog with exact bundle bytes |
| Fact | Typed value from a report JSON pointer, linked to the review ID and both bundle/source hashes. Null is not zero. | Derived on retrieval |

The catalog ingests only explicit user-selected bundle pairs. It never retrieves new data from the internet. Ingestion copies input bytes before asynchronous validation, rejects concurrent imports, limits storage to 20 reviews and 32,000,000 raw bytes, rejects over-capacity writes, and deduplicates identical pairs. The raw-byte budget is not a bound on JavaScript heap use. Revisions for the same window are kept separately. Source text remains data, not instructions.

## Retrieval architecture

`knowledge-catalog.mjs` exposes `createCatalog()`, `portfolioIdentity()`, `ingest()`, `list()`, `history()`, `evidence()`, `remove()`, `clear()`, and `stats()`. `history()` requires the exact portfolio digest, facility ID, inclusive date range for the recent query-window end, and a bounded result limit. It first filters the retained metadata, then selects the matching report row. Results are sorted by window end, retrieval time and identity, include an explicit truncation flag, and cite `/rows/{i}/{field}` pointers into the exact derived report. An absent match returns `NO_SUPPORTED_RECORDS`. There are no embeddings or generated narrative claims. Same-method browser replay establishes consistency, not authenticated origin or independent scientific validation.

Example question supported by this contract: 'What retained wildfire observation comparisons do I have for location A in November 2026, for this exact portfolio configuration?' A result is limited to retained observations. A question about a hazard probability, unexplored location, current conditions or unsupported category must abstain. No nearest-neighbor retrieval is used for numerical or geospatial facts.

## Access boundary and lifecycle

The prototype is an ephemeral per-instance in-memory workspace. Separate instances do not share objects or lookup results. No account authentication, durable persistence, cloud tenant access control or secure erasure is implemented. Deleting a review removes it from catalog retrieval and releases its retained references; previously downloaded or copied bytes cannot be recalled. Clearing the catalog invalidates an in-flight import. Do not use sensitive coordinates on shared devices.

Before multi-user use, derive the tenant and principal from server-verified authentication (never a client-provided tenant field); enforce owner/project membership before metadata enumeration, retrieval, export, search and cache lookup. Keep public source observations separate from private coordinates, user reports and notes. Use tenant-scoped database keys and row-level policies, encrypted private object storage, scoped audit events, and explicit quotas. Server-side checks must cover direct IDs, query filters, aggregate counts, downloads, index refresh, deletion, and caches. A source digest is identity, not authorization. Cross-tenant tests must exercise two authenticated accounts and deny unauthorized records even if an attacker knows the review ID. No server-side tenant claim is made by the prototype.

For durable storage, use immutable raw source objects plus versioned review records, a transactionally updated structured index, and delete/revoke operations that also invalidate indexes and caches. Retain deletion tombstones without private payloads only if a retention policy allows. Record capture time separately from observation time; do not silently replace revised observations. Reports should indicate data age and gaps. For semantic documents added later, chunk by source document and section/page, preserve passage hashes and source pointers, and use hybrid retrieval only after authorization. Treat retrieved scientific text as untrusted content.

## Acceptance evidence and next gates

- The focused baseline is 61 RC10 tests; nine new catalog tests bring the combined executed suite to 70 tests. The new tests use explicitly controlled synthetic transport fixtures, not NASA-acquired data. Eight fixed, labeled retrieval cases matched their expected ordered review IDs, including no-match cases, exact portfolio separation, dates and pagination. These are small deterministic contract checks, not a representative external retrieval benchmark.
- Tests check citation pointer resolution, source and report digests, mutation isolation (including Buffer input), alternative captures, zero vs missing, tampering, date order, count limits, separate instances, deletion and in-flight invalidation.
- The production browser audit has 15 cases and an explicit PASS/FAIL/BLOCKED report. Chromium launched but production navigation was blocked by administrator policy in this environment. Browser interaction acceptance remains incomplete. Python helper tests only validate parsing and digest behavior.
- Next: repair production FIRMS gating and solar imagery, finish actual browser acceptance, then wire the catalog into My Locations with explicit local import/export and deletion. Measure user task completion and time saved before introducing accounts or paid monitoring. A hosted catalog requires a separate tenant-security and persistence design, customer validation and release approval.

## RC11 browser integration

`portfolio-page.mjs` initializes the portfolio and catalog controllers only on the portfolio page. The current review is exposed to the catalog via a local getter; retention requires an explicit click and repeats evidence replay before insertion. `catalog-desk.mjs` uses DOM text nodes, never inserts source HTML, displays the exact portfolio digest, filters by location and inclusive date, distinguishes zero from null, exposes report JSON pointers and both source/bundle hashes, and exports the exact compact report serialization corresponding to its SHA-256. Changing filters clears old results. Removal and clear invalidate catalog retrieval. Closing or reloading discards retained reviews, not already exported copies. `workspace.mjs` now initializes only when the dedicated `workspace-page` marker is present.

The new tests include an actual portfolio-controller-to-catalog handoff under controlled transport, explicit retention, repeated review deduplication, exact portfolio isolation, null and zero, corrupted input rejection, report-byte digest, deletion, and the wrong-page auto-start collision. Combined focused suite: 75 tests passed on Node 22.16.0, plus four Python helpers. The controlled Playwright acceptance script and proposed CI job are authored; browser outcomes are not claimed from simulated DOM tests. Durable local persistence and authenticated tenant boundaries remain future work.
