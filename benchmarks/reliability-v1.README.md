# Gaia Reliability Benchmark v1

This is a deterministic synthetic software benchmark of the EONET count-claim contradiction engine, not a benchmark of general AI or scientific discovery. The candidate is pinned to f6dc0c0ef66f70a4017a9662691ef3a72fbdd9aa. No network, external model, or paid resources are required.

## Reproduce from the repository

Use Node.js 22. In a clean copy of the benchmark-enabled repository (or copy the benchmark script and protocol to the pinned candidate checkout), run:

```sh
node scripts/gaia-reliability-benchmark.mjs --freeze
node scripts/gaia-reliability-benchmark.mjs --run 6ecb629efa01f438841aeda8cb32c79bc0b0c22e58752e188e59eceab7de45b5
```

Both commands refuse to overwrite existing output files. The first writes `benchmarks/reliability-v1.manifest.json`; the second writes `benchmarks/reliability-v1.results.json` with every case, classification, exception reason, and timing. The input manifest digest must match the separately retained digest in the receipt. Timings and raw-result file hashes vary by machine/run; classifications should match. The attached local evidence bundle includes the original manifest, raw results, and baseline log. It also includes the locally executed dependency subset, not a full checkout.

## Interpretation

The evaluation split contains 168 cases across 14 families (12 per family); the development split contains 56. The expected labels were set by construction before the candidate run. Fictional raw point geometries and expected report membership were constructed by an independent vector-distance implementation. The hash-and-scope baseline checks component and source digests, configuration, unique IDs, and count predicates, but trusts supplied spatial membership. It is not a state-of-the-art adversarial system. The candidate also replays spatial membership. Both classified all 120 valid evaluation comparisons correctly. Gaia rejected all 48 invalid comparisons; the baseline rejected 24. The 24 differences are confined to two designed families: rehashed report mutations and rehashed source geometry mutations. Explicit error reasons were inspected, not inferred merely from exceptions. This demonstrates a narrow software capability under the tested conditions. Neither replay nor hashing proves that source data are true; coherent forgery of original records and matching reports is outside the benchmark. No inference of generalization, statistical significance, real-world scientific reliability, or independence of the cases is supported. The protocol digest is local, not independently timestamped. Future versions should incorporate externally authored cases and independently authenticated observations.
