# Gaia Earth history (v0.7)

## Method contract

This is retrospective descriptive screening of one retained v0.5 evidence bundle, not a forecast, event occurrence rate, or a measurement of actual exposure. Before generating a history, the browser checks the original bundle using the v0.6 same-method replay; the Python verifier independently replays the bundle using the v0.5 CLI logic. Use the original facility coordinates, radius, and inclusive UTC lookback window without modifying them. Divide the interval into UTC calendar dates. A point exactly at midnight belongs to that UTC date, including the final instant of the window; first/last dates may be partial. Include every date, even if no observations exist. At most 31 dates and 25 facilities.

For each date, count all eligible recorded point rows in the source (including repeated records), then count rows within the unrounded spherical radius and distinct matching event IDs. An event can contribute to more than one date; do not sum daily distinct-event counts as a total number of events. Non-point geometries are excluded. Rows are not independent detections. A zero with no eligible observations is different from zero matching rows among eligible observations; neither implies safety or complete coverage. There are no trend, causality, hazard probability, or scientific validity claims. The source may have been capped, revised or incomplete, and capture time is not observation time.

The JSON report binds the original bundle and source SHA-256, records exact UTC bounds, radius, source kind, all facility dates, and an explicit unknown-coverage label. The independent Python verifier requires the original bundle and recomputes every report field using the separate spherical-vector distance method. Exact threshold disagreements fail replay. An optional independently retained bundle digest detects complete replacement; a replay is not proof of source authenticity. No paid service, additional dependency, network acquisition, telemetry or persistent browser storage is added. Do not publish private facility coordinates or reports.

## Acceptance criteria

Reproduce the committed synthetic bundle: 4 UTC dates, 3 facilities, 3 available in-window point rows on November 1, two matching rows from one event for EXAMPLE-A, one matching row from one event for EXAMPLE-B, no matching row for EXAMPLE-C. Earlier dates have zero eligible rows. Test midnight and final-boundary handling, repeated event rows, out-of-window exclusions, no observations, geographic distance, tampered report and bad digest. No empirical trend validation is claimed; the fixture is already known and synthetic.

## Use

Run `python -m http.server 8000` at the repository root and open `http://localhost:8000/history.html`. Load the synthetic example or a v0.5 bundle. Inspect a facility's daily history, export JSON and retain the original bundle. Verify with `python scripts/verify_earth_history.py BUNDLE.json HISTORY.json --expected-sha256 DIGEST` (digest optional, but retain it separately). Run `node --test tests/history.test.mjs` and `python -m unittest discover -s tests -p 'test_earth_history.py' -v`. Browser history is a same-method check; Python replay is separate. The date and counts are descriptive, not operational warnings.
