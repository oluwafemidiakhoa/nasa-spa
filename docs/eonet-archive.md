# Gaia Observatory v0.4 — EONET acquisition and archive

Contract: deterministic byte retention and integrity checks, not scientific validation. The official EONET v3 events endpoint documents date range, category, status and limit: https://eonet.gsfc.nasa.gov/docs/v3. Use a fixed HTTPS host and path, explicit inclusive dates (maximum 31 days), status=all, one category and 1–200 events. No credentials, redirect following, proxies, paid services or automatic retries. The worker has a 25-second subprocess deadline and a 10-second socket timeout; reject non-200 responses, non-JSON media, non-identity encoding and bodies over 2,000,000 bytes. Preserve exact response bytes; do not claim event coverage from a capped query. Reject malformed JSON, duplicate keys and IDs, invalid point coordinates/timestamps, missing geometry arrays and excessive event/geometry counts. Count non-point geometries without analyzing them. The archive stores one receipt and base64-encoded source body, with an optional independently retained archive digest for stronger integrity checking. Offline import has no asserted request URL, HTTP status or NASA provenance. Verification recomputes the source hash, counts and metadata consistency; it cannot authenticate retrieval history or detect replacement of the whole archive without an independent anchor. Writes are no-clobber via an atomic hard link in the destination directory; a filesystem without hard links is unsupported. No network connection is needed for import, verify or export.

## Usage (Python 3.10+)

From the repository root, with a new output filename for each command:

```sh
python scripts/eonet_archive.py fetch --start 2025-01-07 --end 2025-01-15 --category wildfires --limit 10 archive.json
python scripts/eonet_archive.py verify archive.json
python scripts/eonet_archive.py export archive.json original-events.json
python scripts/eonet_archive.py import data/earth-observatory-synthetic.json synthetic-archive.json
python scripts/eonet_archive.py verify synthetic-archive.json
python -m unittest discover -s tests -p 'test_eonet_archive.py' -v
```

Save the printed `archiveSha256` separately and pass it to `verify` or `export` with `--expected-sha256`. For the v0.3 batch CLI, use the exported snapshot bytes and a separately retained configuration with `snapshotKind` set to `user-import-unverified` for real or unknown data (synthetic-demo only for synthetic inputs). See [batch method](earth-batch.md). No claim of live source compatibility until an actual successful retrieval and replay. No alerts or risk scores.
