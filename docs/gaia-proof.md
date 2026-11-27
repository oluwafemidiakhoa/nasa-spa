# Gaia Proof v1 — conditional scientific count certificates

Open `gaia-proof.html` in the Observatory Preview. Choose the fictional demonstration, or download an **original EONET evidence bundle** from the single-category location workspace and enter the retained facility ID. A consolidated Sentinel summary is not an original bundle. Set the minimum distinct-event count K, maximum reference-site displacement, radius tolerance, and whole-event deletion budget B. Demo uses the fictional reference site and the numerical inputs. No raw private file is uploaded; only the explicit fictional demo action fetches the bundled example. The output contains private coordinates; retain it locally.

## Method and scope

The existing evidence verifier recomputes the original point-event screening report from archived bytes. Boundary Intelligence computes conservative bounds [L,U] for eligible distinct returned event IDs on the fixed records. Whole-event ablation supplies replayed deletion witnesses. For up to B deletions, the combined conservative bounds are [max(0,L-B), U]; zero deletions are allowed, so U is unchanged. At least K is conditionally supported if max(0,L-B) >= K. U < K excludes that count threshold on the retained records only. Otherwise the claim is not certified. When no eligible records exist, the verdict is unavailable. A lower-bound witness is a counterexample to the lower-bound guarantee, not necessarily a real-world counterexample. Source caps and unknown coverage remain visible. Upper and lower bounds need not be jointly achievable; existing spherical distance and numerical guard are not formal floating-point proof.

Export the full packet and keep its SHA-256 independently if later consistency checking is important. Reopen the packet to replay every report field. A coherent forgery of raw records and derived findings may pass same-method replay: neither source authenticity nor trusted chronology is established by this module. No live hazard or safety inference is supported. Cross-source contradiction, independent end-to-end reproduction and timestamp authority integration are **not** part of this certificate. This is not a trained scientific predictor.

## Verification

Use Node.js 22 in a repository checkout:

```sh
node --test tests/gaia-proof.test.mjs
```

The 15 tests use fictional evidence, including the exact existing six-point demo, positive and negative count claims, rehashed report manipulation, coherent alternative inputs, capped coverage, duplicate keys, controller export/reopen and stale-input suppression. The finite-grid oracle uses an independently coded vector/atan2 distance to check the joint-bound calculation in 1,134 scenarios; an additional 120 scenarios test a positive nonzero-deletion guarantee. This is finite, designed software evaluation, not an independent scientific or externally blinded benchmark. Test receipt records the exact executed files and local dependency core fingerprints. Full repository regression and browser acceptance are separate gates.
