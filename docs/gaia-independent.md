# Gaia Independent Verifier v1

## Purpose
Verify the enumerated computational fields of a Gaia Proof v1 JSON export using Python's standard library, without importing the JavaScript implementation or contacting any service. The vector cross-product/dot-product `atan2` spherical distance calculation is different from the browser's haversine calculation. Both methods intentionally use the same Earth radius and observation semantics.

## Run locally
Requires Python 3.10+ (tested with Python 3.13.5 on Linux). From the repository root:

```bash
python scripts/verify_gaia_proof.py path/to/gaia-proof-export.json
```

Optionally supply independently retained fingerprints:

```bash
python scripts/verify_gaia_proof.py path/to/gaia-proof-export.json --source-sha256 YOUR_SOURCE_DIGEST --packet-sha256 YOUR_PACKET_DIGEST
```

Use an actual original digest; the value copied from a suspect packet is not independent evidence. Exit 0 = CROSS_RUNTIME_MATCH for enumerated fields; 1 = REJECTED; 2 = INCONCLUSIVE_NUMERICAL_BOUNDARY. Always inspect the result and limitations. No node installation is needed to verify a packet. No external dependencies or network access.

## Verification scope
- Exact packet, bundle, archive, configuration, original report and source component hashes, canonical base64, strict JSON, bounded sizes, supported schemas and acquisition metadata.
- Recomputed original batch membership and coverage for all retained facilities, nearest eligible point identity and rounded distance.
- Selected facility's nominal, lower and upper distinct-event sets, radius witnesses, coverage, bounds, and joint claim.
- Exact deletion thresholds, event IDs and post-deletion counts by set difference, without trusting the supplied deletion calculation.
- The declared verification-status fields must remain unverified where applicable. Source and complete packet digests are separate optional anchors.

Raw geometric distances use 0.000001 km comparison tolerance; original displayed distances use half a meter rounding plus that tolerance. If a decision is within 0.000001 km of a cutoff, return inconclusive rather than force a binary verdict. Near-tied nearest points are checked against eligible observations; display ordering and narrative metadata are not independently verified. This is not a formal floating-point proof. Extreme numerical edge cases can produce conservative rejection or abstention. A cross-runtime match is not an endorsement of the original narrative, scientific safety, completeness, source authenticity, or trusted chronology. A coherent alternative source may pass without an independently retained anchor. Python/JavaScript implementation independence does not imply independent authorship or scientific replication.

## Reproduce the experiment
The case generator uses Node.js to make fictional Gaia Proof packets, and the Python verifier consumes them. No live observations or private facility coordinates are used. The protocol was written before the fixture outcomes were evaluated, but fixtures and verifier were co-developed; this is a designed regression exercise, not a blinded external benchmark.

```bash
python -m unittest discover -s tests -p 'test_verify_gaia_proof.py' -v
node --test tests/gaia-proof.test.mjs tests/gaia-adversary.test.mjs
```

Expected observed run: 89 cases (71 matches, 16 rejections, 2 inconclusive); four Python test methods, including CLI and nonregular input checks; 25 existing focused Node tests. See independent-test-receipt.json for versions and fingerprints. Do not interpret these counts as population accuracy. No full repository, browser or production test was performed.
