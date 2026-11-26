# Gaia Observatory v0.5 — portable Earth evidence

An offline bundle retains the exact v0.4 archive, configuration and v0.3 report bytes, alongside SHA-256 and byte counts for each. The original observations are retained inside the archive; they are never regenerated from parsed JSON. The existing JavaScript screening algorithm and independent Python replay algorithm are unchanged. Every pack runs replay before a no-clobber atomic file write. Every verify repeats the archive checks and independent replay without running the generator. A fixed schema and strict JSON/base64 checks reject ambiguous or malformed inputs. Component limits: archive 3 MB, config 32 KiB, report 16 MB, complete bundle 26 MB (decimal except config). Local worker timeout: 20 seconds per step. Temporary files are removed on normal success or failure. Filesystems without hard links are unsupported; power-loss durability and forced-process termination cleanup are not established.

The bundle records SHA-256 of the local archive, screening, batch generator and replay implementation. Replay requires matching implementation bytes; retain the Git revision as well. The bundle does not contain executable code. Its digest is unsigned; retain it independently if you need to detect complete replacement. Neither a digest nor a replay proves NASA authenticity, completeness, scientific accuracy or facility safety. An archived acquisition claim is not authenticated by this tool. Configuration labels are user declarations. A claimed HTTPS archive cannot be labelled synthetic. Do not publish private facility coordinates or bundles containing them.

## Local example (Python 3.10+, Node 22+ for pack)

From the repository root, use new output names:

```sh
python scripts/eonet_archive.py import data/earth-observatory-synthetic.json synthetic-archive.json
python scripts/earth_evidence.py pack synthetic-archive.json data/earth-facilities-synthetic.json evidence.json
python scripts/earth_evidence.py verify evidence.json
```

Retain the printed `bundleSha256` independently; repeat `verify evidence.json --expected-sha256 DIGEST` with that exact digest. For pack, `--expected-archive-sha256 DIGEST` optionally checks the previously retained archive digest. Verification needs Python and the matching source files but does not execute Node, call the network, or need API keys. A rejected replay or output collision exits nonzero and never publishes a replacement file. A successful result is `REPLAY_MATCH`, with `sourceAuthenticated` and `scientificValidityEstablished` both false.

## Acceptance criteria

The supplied synthetic fixture must produce exactly three facility results, two with matching points and one without. Packing and replay must preserve source bytes, reject independently modified archive/config/report, recomputed component hashes with altered results, duplicate keys, invalid encodings, extra fields, oversized inputs, a changed implementation fingerprint, wrong independent digest, and existing output paths. No live source or production readiness is implied by passing these tests.

```sh
python -m unittest discover -s tests -p 'test_earth_evidence.py' -v
```
