#!/usr/bin/env python3
"""Fail-fast structural checks for the Moon→Mars Decision Atlas competition build.

This validator intentionally distinguishes *integrity* from *completeness*:
- Integrity failures exit non-zero (broken provenance, IDs, 3D handoff, stale story, etc.).
- Incomplete NASA traceability is reported as a competition blocker but does not
  fail normal CI until --strict-traceability is requested.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "moon_to_mars_revision_c.json"
INDEX_PATH = ROOT / "index.html"
NAV_PATH = ROOT / "navigator.html"
SUBMISSION_PATH = ROOT / "SUBMISSION.md"


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)
    print(f"ERROR: {message}")


def ok(message: str) -> None:
    print(f"PASS: {message}")


def warn(message: str) -> None:
    print(f"BLOCKER: {message}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict-traceability",
        action="store_true",
        help="Fail unless every loaded technology gap has detailed architecture traceability.",
    )
    args = parser.parse_args()

    errors: list[str] = []

    for path in (DATA_PATH, INDEX_PATH, NAV_PATH, SUBMISSION_PATH):
        if not path.exists():
            fail(f"Required competition file missing: {path.relative_to(ROOT)}", errors)
    if errors:
        return 1

    dataset = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    index = INDEX_PATH.read_text(encoding="utf-8")
    navigator = NAV_PATH.read_text(encoding="utf-8")
    submission = SUBMISSION_PATH.read_text(encoding="utf-8")

    meta = dataset.get("dataset", {})
    gaps = dataset.get("technology_gaps", [])
    segments = set(dataset.get("segments", []))
    subarchitectures = set(dataset.get("subarchitectures", []))

    if meta.get("document_id") != "20250010956":
        fail("NASA Revision C document_id must remain 20250010956", errors)
    else:
        ok("NASA Revision C document ID is pinned")

    if meta.get("revision") != "C":
        fail("Dataset revision must be C", errors)
    else:
        ok("Dataset revision is C")

    if len(gaps) < 16:
        fail(f"Expected at least 16 prioritized technology gaps; found {len(gaps)}", errors)
    else:
        ok(f"Prioritized gap inventory loaded: {len(gaps)}")

    ids = [str(g.get("id", "")) for g in gaps]
    if len(ids) != len(set(ids)):
        fail("Technology gap IDs are not unique", errors)
    if any(not re.fullmatch(r"\d{4}", gid) for gid in ids):
        fail("Every technology gap ID must be a four-digit ESDMD identifier", errors)
    if not errors:
        ok("Technology gap IDs are unique and normalized")

    ranks = [g.get("priority_rank") for g in gaps]
    nonnull_ranks = [r for r in ranks if isinstance(r, int)]
    if len(nonnull_ranks) != len(set(nonnull_ranks)):
        fail("NASA priority ranks are duplicated", errors)
    else:
        ok("NASA priority ranks are unique")

    unknown_segments: list[tuple[str, str]] = []
    unknown_subs: list[tuple[str, str]] = []
    for gap in gaps:
        gid = str(gap.get("id", "?"))
        for value in gap.get("segments", []) or []:
            if value not in segments:
                unknown_segments.append((gid, value))
        for value in gap.get("subarchitectures", []) or []:
            if value not in subarchitectures:
                unknown_subs.append((gid, value))
    if unknown_segments:
        fail(f"Unknown campaign segment mappings: {unknown_segments}", errors)
    if unknown_subs:
        fail(f"Unknown sub-architecture mappings: {unknown_subs}", errors)
    if not unknown_segments and not unknown_subs:
        ok("All architecture mappings resolve to declared NASA taxonomy nodes")

    verified = [
        g
        for g in gaps
        if g.get("detail_status") == "verified"
        and (g.get("segments") or g.get("subarchitectures"))
    ]
    rank_only = [g for g in gaps if g not in verified]
    coverage = (len(verified) / len(gaps) * 100) if gaps else 0.0
    print(
        f"TRACEABILITY COVERAGE: {len(verified)}/{len(gaps)} gaps "
        f"({coverage:.1f}%) have detailed loaded architecture mappings"
    )
    if rank_only:
        warn(
            "Detailed NASA traceability is still incomplete for: "
            + ", ".join(f"#{g.get('priority_rank')} {g.get('id')}" for g in rank_only)
        )
        if args.strict_traceability:
            fail("Strict traceability requested but not all gaps are fully mapped", errors)
    else:
        ok("All prioritized gaps have detailed architecture traceability")

    atlas_markers = {
        "residual dependency engine": "function residualForGap",
        "residual analysis UI": "Residual dependency check",
        "selected-gap 3D action": "OPEN THIS GAP IN 3D",
        "selected-gap URL persistence": "history.replaceState(null,'','?gap='",
        "source provenance UI": "Provenance",
    }
    for label, marker in atlas_markers.items():
        if marker not in index:
            fail(f"Atlas missing {label}: {marker}", errors)
        else:
            ok(f"Atlas contains {label}")

    nav_markers = {
        "3D core embedding": "navigator_core.html",
        "gap-aware URL input": "const initialGap=params.get('gap')",
        "round-trip back link": "$('#backLink').href='/?gap='",
        "phase control bridge": "w.setPhase(currentPhase)",
    }
    for label, marker in nav_markers.items():
        if marker not in navigator:
            fail(f"3D Navigator missing {label}: {marker}", errors)
        else:
            ok(f"3D Navigator contains {label}")

    missing_profiles = [gid for gid in ids if f"'{gid}':{{" not in navigator]
    if missing_profiles:
        fail(f"3D context profile missing for gap IDs: {', '.join(missing_profiles)}", errors)
    else:
        ok("All loaded technology gaps have explicit 3D context profiles")

    stale_story_markers = [
        "# Solar Storyline",
        "pilot, grid operator",
        "Live NASA cards ticking",
    ]
    stale_hits = [marker for marker in stale_story_markers if marker in submission]
    if stale_hits:
        fail(f"SUBMISSION.md still contains retired Solar Storyline narrative: {stale_hits}", errors)
    else:
        ok("Submission narrative is aligned to the current Atlas product")

    required_submission_phrases = [
        "Moon→Mars Decision Atlas",
        "NASA",
        "Revision C",
        "technology gap",
        "provenance",
        "3D",
        "official 2026 challenge",
    ]
    for phrase in required_submission_phrases:
        if phrase.lower() not in submission.lower():
            fail(f"SUBMISSION.md missing required competition concept: {phrase}", errors)
    if not errors:
        ok("Competition narrative contains the required current-product concepts")

    print("\n=== COMPETITION READINESS SUMMARY ===")
    print(f"Integrity errors: {len(errors)}")
    print(f"Detailed traceability: {len(verified)}/{len(gaps)}")
    print("Challenge alignment: PENDING until NASA publishes the official 2026 challenge statement")
    print("UI status: FROZEN except for bug fixes and evidence/completeness work")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
