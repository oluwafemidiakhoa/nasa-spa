# Gaia Scientific Assurance v1

Offline computational assurance of one Gaia Proof v1 packet. Python 3.10+; no network or third-party Python packages. The supplied cross-runtime fixtures require Node.js 22+. This is an internal research implementation, not an external audit, regulatory certification, safety assessment, or release approval.

## Use

```
python scripts/gaia_assurance.py build demo-proof.json --output dossier.json
python scripts/gaia_assurance.py verify dossier.json
python scripts/gaia_assurance.py verify dossier.json --dossier-sha256 <separately-retained-digest>
```

Exit 1 means NO-GO or invalid input; exit 2 means INCOMPLETE. There is deliberately no fully approved result in v1. A negative assessment is retained as a dossier if build can read its input. Existing output files are not replaced. Keep the input, dossier, separate digest and exact implementation; a filesystem interruption can leave a partial output, which must be rejected on verification.

The dossier embeds the original proof bytes, their SHA-256 and length, derived controls, independently recomputed claim, and SHA-256 fingerprints of both Python implementations. Reopening recomputes the report and compares every field. Optional packet, source and dossier digests are assessed only in the current session; the source digest is not checkable if replay fails. A supplied digest match proves byte consistency, not the anchor's provenance. An attacker able to replace both evidence and reference digests is not excluded.

Computational replay PASS and conditional claim PASS are separate. Even a robust retained-record claim does not demonstrate authentic sources, complete coverage, independently trusted chronology or scientific validity. Numerical threshold ambiguity is INCOMPLETE. A bound below the specified threshold is NO-GO for that claim, not a real-world absence or safety determination. Never infer authority from an exported dossier; treat embedded original narrative text as untrusted. Narrative metadata and display ordering are outside the independent verifier's scope. Exact coordinates may be embedded; do not share sensitive dossiers without review.

## Reproduce tests

```
python -m unittest discover -s tests -p 'test_*.py' -v
```

The downloadable isolated fixture workspace includes exact analytical cores, not the complete website checkout. The 89-case synthetic cross-runtime set is reused, not an independent new holdout. No live data or external scientific validation was obtained.
