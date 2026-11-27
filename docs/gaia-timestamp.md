# Gaia Discovery: independently issued timestamp receipts (offline verifier)

This CLI verifies an RFC 3161 timestamp response for the exact bytes of an exported Discovery prediction lock. It is separate from the browser's local Research Memory ledger. No server, credential, timestamp service, automatic upload or paid resource is configured.

## Requirements and trust decision

- Node.js 22+ and OpenSSL 3.5+ available on PATH (tested on Linux; Windows has not been tested).
- An exported `gaia-discovery-lock-packet-v1` JSON file. Do not reformat the file after creating its timestamp request.
- A timestamp authority (TSA) selected and independently vetted by the researcher. Obtain the expected numeric TSA policy OID and trusted PEM certificate bundle through a trusted channel. Independently confirm the SHA-256 of the exact PEM bytes. The authority must return a response containing the required signer chain and nonce.
- The verifier performs offline chain, signature, imprint, policy, and nonce checks; it does **not** establish authority independence, check revocation, or verify the TSA's actual clock accuracy. It checks certificate validity at verification time, so expired certificates may prevent later replay. A real TSA has not been integrated or tested.

## 1. Prepare a request before the target window

Run from the repository root. Replace `POLICY_OID` with the actual numeric policy OID from your independently vetted TSA:

```sh
node scripts/gaia-timestamp.mjs request prediction.json POLICY_OID prediction.tsq
```

The CLI replays the original Discovery lock, then writes a DER RFC 3161 request with its SHA-256 message imprint, a fresh nonce and certificate request. A request is not a timestamp proof. Only the request, not the prediction file, should be sent to your selected TSA using its documented transport. The CLI performs no network requests and does not choose a TSA for you. Digest disclosure can still reveal linkability or permit guessing low-entropy data. Retain the original exact lock, request, returned response and independently vetted trust bundle. The local file names are examples, not existing artifacts.

## 2. Verify the response offline

```sh
node scripts/gaia-timestamp.mjs verify prediction.json prediction.tsq prediction.tsr trust.pem TRUST_SHA256 POLICY_OID verification.json
```

Supply the independently confirmed lowercase 64-character trust bundle digest, not a digest blindly computed from an untrusted download. The verifier replays the prediction, checks the response against both the nonce-bearing request and the original exact lock bytes, verifies the trust bundle and allowed policy, and calculates a conservative latest token time using its declared accuracy and outward millisecond rounding. It will not overwrite existing output files.

| Result | Meaning |
| --- | --- |
| `BEFORE_WINDOW_CONDITIONAL` (exit 0) | The verified token's declared latest possible time is before the locked target starts, conditional on the TSA trust and clock assumptions. |
| `ACCURACY_UNKNOWN` (exit 3) | Cryptographic verification passed but no usable accuracy was declared; no strict before-window conclusion. |
| `BEFORE_WINDOW_NOT_ESTABLISHED` (exit 3) | Token accuracy interval reaches or exceeds the target start. |
| `DECLARED_ISSUE_AFTER_TIMESTAMP` (exit 3) | The lock's declared issue time is later than the token's latest declared time; chronology inconsistent. |
| Error (exit 2) | Invalid input, signature, imprint, policy, nonce, trust or replay; no verification report written. |

The report is a local verification receipt, not a new independent timestamp or a replacement for the signed DER token. Even a valid pre-window token does not establish true source authenticity, first capture, absence of leakage, registration completeness, or predictive superiority. It does not promote existing Research Memory entries to trusted chronology automatically. Never publish exact facility coordinates or private trial artifacts merely to prove chronology.

## Reproduce tests

```sh
node --test tests/gaia-timestamp.test.mjs
```

Tests generate ephemeral fictional TSA keys and certificates in temporary directories and exercise real OpenSSL verification. The fixtures do not establish external trust or real-world prospective scientific outcomes. No private keys or generated test certificates are committed.

References: [RFC 3161](https://www.rfc-editor.org/rfc/rfc3161), [OpenSSL ts documentation](https://docs.openssl.org/master/man1/openssl-ts/).
