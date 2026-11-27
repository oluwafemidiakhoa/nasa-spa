# Gaia Adversary v1

Open `gaia-adversary.html` in Preview or use `node --test tests/gaia-adversary.test.mjs` from the repository root (Node 22+). No API keys, model inference, or new service is required.

## Workflow

1. Retain the original Gaia Proof packet and its SHA-256 digest separately through a trusted process before subsequent review. Retain the source digest independently from the original acquisition if available. Do not treat hashes copied from a questioned artifact as independent anchors.
2. Open Gaia Adversary and select the proof JSON file. Supply either or both separately retained digests.
3. Read replay, source binding, and full packet binding separately. A mismatch means bytes differ, not necessarily fraud; even harmless serialization changes alter the full packet digest.
4. Run the six fictional cases to see the limitations of replay. The demonstration is restricted to the pinned synthetic fixture and does not export alternative evidence.

## Scope

Replay is same-method verification, not independent scientific replication. A supplied hash is not automatically a trusted anchor. The verifier does not establish source authenticity, authority, chronology, catalog completeness, or environmental safety. It does not detect a coherent alternative if the reference hash was also replaced. Private proof files and entered digests are handled locally; the demonstration retrieves only the existing fictional fixture. No private coordinates or records are sent by the page's code.

## Reproduce

`node --test tests/gaia-proof.test.mjs tests/gaia-adversary.test.mjs`

The protocol describes six designed contrasts, not an external blinded benchmark. The test receipt records the isolated calculation-core environment and exact file hashes.
