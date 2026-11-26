# Earth Intelligence batch screening v0.3

## Method contract

This is deterministic computation, not a prediction or safety assessment. Input: saved EONET v3 events JSON (at most 2 MB), and a separately retained configuration JSON (at most 32 KB). Source documentation: https://eonet.gsfc.nasa.gov/docs/v3. The declared snapshot kind is not authenticated. The batch uses the v0.2 point-screening method unchanged, with the same explicit UTC cutoff, lookback (1-720 hours) and radius (1-1000 km) for each of 1-25 uniquely identified facilities. Longitude precedes latitude. Sort facilities by ASCII ID. Include the nearest in-window point per event within the unrounded radius, preserving the v0.2 tie and coverage rules. Exclude polygons and count exclusions. The report binds exact snapshot and configuration bytes with SHA-256 and includes every facility result. No match is not safety. No model, empirical forecast, hazard extent, or exposure probability is inferred.

Independent replay: a Python standard-library verifier recomputes every field (including all distances using an independently implemented spherical vector cross/dot formula). It requires the original snapshot and independently supplied original configuration, rejects extra or missing report fields, malformed JSON, duplicate JSON keys, incorrect hashes, altered results and coverage. Numeric boundary or tie differences between the two implementations can cause rejection; do not interpret rejection as proof of malicious tampering. A successful replay demonstrates agreement on these inputs, not data authenticity, hazard coverage, chain of custody, or scientific accuracy. Unsigned hashes cannot protect against replacement of all inputs and the report. Retain the inputs separately. Synthetic inputs cannot establish real-world performance.

Acceptance: reproduce the synthetic three-facility example with both implementations; reject modified hashes, results, coverage, parameters, missing results, duplicate facility identifiers, invalid coordinates and invalid timestamps. No live API or production write required. External NASA response retrieval was attempted but unavailable; live compatibility remains untested. Method digest is local and unsigned, not external preregistration.

## Run locally (Node.js 22+ and Python 3.10+)

From the repository root, using the provided synthetic snapshot and configuration:

```sh
node scripts/earth-batch.mjs data/earth-observatory-synthetic.json data/earth-facilities-synthetic.json > earth-batch-report.json
python scripts/verify_earth_batch.py data/earth-observatory-synthetic.json data/earth-facilities-synthetic.json earth-batch-report.json
python -m unittest discover -s tests -p 'test_earth_batch.py' -v
node --test tests/earth.test.mjs
```

The generator writes JSON to stdout and errors to stderr; the verifier exits 0 for exact agreement, 1 for rejection. Preserve report and both input files. Do not use shell redirection to overwrite a valuable report. Do not commit private facility coordinates. Example official archive query (open/download yourself): https://eonet.gsfc.nasa.gov/api/v3/events?status=all&start=2025-01-07&end=2025-01-15&category=wildfires&limit=10 . Save the original response bytes; use `user-import-unverified` in your separate configuration and set the explicit UTC cutoff to match your intended analysis window. A limit-restricted response is not complete coverage. Retrieval time, source URL and upstream identity need independent documentation for real-data studies.
