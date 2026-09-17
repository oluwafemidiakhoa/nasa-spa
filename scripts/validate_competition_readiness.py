#!/usr/bin/env python3
"""Fail-fast structural checks for the 2026 Moon→Mars Mission Trainer build."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "moon_to_mars_revision_c.json"
TRAINER_PATH = ROOT / "trainer.html"
INDEX_PATH = ROOT / "index.html"
NAV_PATH = ROOT / "navigator.html"
SUBMISSION_PATH = ROOT / "SUBMISSION.md"
ALIGNMENT_PATH = ROOT / "CHALLENGE_ALIGNMENT.md"
VERCEL_PATH = ROOT / "vercel.json"
RELEASE_PATH = ROOT / "release.json"


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)
    print(f"ERROR: {message}")


def ok(message: str) -> None:
    print(f"PASS: {message}")


def warn(message: str) -> None:
    print(f"BLOCKER: {message}")


def require_markers(text: str, markers: dict[str, str], label: str, errors: list[str]) -> None:
    for description, marker in markers.items():
        if marker not in text:
            fail(f"{label} missing {description}: {marker}", errors)
        else:
            ok(f"{label} contains {description}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-traceability", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []

    required = (DATA_PATH, TRAINER_PATH, INDEX_PATH, NAV_PATH, SUBMISSION_PATH, ALIGNMENT_PATH, VERCEL_PATH, RELEASE_PATH)
    for path in required:
        if not path.exists():
            fail(f"Required competition file missing: {path.relative_to(ROOT)}", errors)
    if errors:
        return 1

    dataset = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    trainer = TRAINER_PATH.read_text(encoding="utf-8")
    index = INDEX_PATH.read_text(encoding="utf-8")
    navigator = NAV_PATH.read_text(encoding="utf-8")
    submission = SUBMISSION_PATH.read_text(encoding="utf-8")
    alignment = ALIGNMENT_PATH.read_text(encoding="utf-8")
    vercel = json.loads(VERCEL_PATH.read_text(encoding="utf-8"))
    release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))

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
    if meta.get("generated_from_official_xlsx") is not True:
        fail("Production competition dataset must be generated from official NASA XLSX products", errors)
    else:
        ok("Dataset is marked generated_from_official_xlsx")
    if len(gaps) < 16:
        fail(f"Expected at least 16 technology gaps; found {len(gaps)}", errors)
    else:
        ok(f"Technology-gap inventory loaded: {len(gaps)}")

    ids = [str(g.get("id", "")) for g in gaps]
    if len(ids) != len(set(ids)):
        fail("Technology gap IDs are not unique", errors)
    if any(not re.fullmatch(r"\d{4}", gid) for gid in ids):
        fail("Every technology gap ID must be a four-digit ESDMD identifier", errors)
    else:
        ok("Technology gap IDs are normalized")

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

    verified = [g for g in gaps if g.get("detail_status") == "verified" and (g.get("segments") or g.get("subarchitectures"))]
    rank_only = [g for g in gaps if g not in verified]
    coverage = (len(verified) / len(gaps) * 100) if gaps else 0.0
    print(f"TRACEABILITY COVERAGE: {len(verified)}/{len(gaps)} gaps ({coverage:.1f}%) have detailed loaded architecture mappings")
    if rank_only:
        warn("Detailed NASA traceability is incomplete for: " + ", ".join(f"#{g.get('priority_rank')} {g.get('id')}" for g in rank_only[:12]) + (" ..." if len(rank_only) > 12 else ""))
        if args.strict_traceability:
            fail("Strict traceability requested but not all gaps are fully mapped", errors)
    else:
        ok("All loaded technology gaps have detailed architecture traceability")

    trainer_markers = {
        "product-first hero": "NASA ARCHITECTURE · INTERACTIVE MISSION TRAINING",
        "challenge metadata retained": "Build a Junior Astronaut Mission Trainer",
        "lunar scenario": "Lunar South Pole Outpost",
        "Mars scenario": "Mars Surface Outpost",
        "limited training credits": "MAX_CREDITS=10",
        "NASA gap resolver": "function resolveGap(def)",
        "residual graph debrief": "function runDebrief(scroll=true)",
        "real timed judge demo": "const demoStages=[",
        "30-second runtime": "elapsed>=30000",
        "demo data readiness gate": "$('#demoBtn').disabled=false",
        "direct per-gap 3D handoff": "🌐 VIEW IN 3D",
        "debrief 3D handoff": "🌐 OPEN IN 3D",
        "Atlas handoff": "/atlas?gap=",
        "3D URL handoff": "/navigator?gap=",
        "NASA source handoff": "NASA SOURCE",
        "no invented readiness claim": "does not calculate mission survival probability",
    }
    require_markers(trainer, trainer_markers, "Trainer", errors)

    if "2026 Challenge · Build a Junior Astronaut Mission Trainer" in trainer:
        fail("Trainer hero still exposes the challenge title as product branding", errors)
    else:
        ok("Trainer hero is product-first rather than challenge-title-first")

    atlas_markers = {
        "residual dependency engine": "function residualForGap",
        "residual analysis UI": "Residual dependency check",
        "selected-gap 3D action": "OPEN THIS GAP IN 3D",
        "selected-gap URL persistence": "history.replaceState(null,'','?gap='",
        "source provenance UI": "Provenance",
    }
    require_markers(index, atlas_markers, "Atlas", errors)

    nav_markers = {
        "3D core embedding": "navigator_core.html",
        "gap-aware URL input": "const initialGap=params.get('gap')",
        "round-trip back link": "$('#backLink').href='/atlas?gap='",
        "phase control bridge": "w.setPhase(currentPhase)",
        "fallback phase inference": "function inferProfile(g)",
    }
    require_markers(navigator, nav_markers, "3D Navigator", errors)

    release_id = str(release.get("release", "")).strip()
    if not release_id:
        fail("release.json must contain a non-empty release identifier", errors)
    else:
        ok(f"Production release fingerprint present: {release_id}")

    redirects = vercel.get("redirects", [])
    rewrites = vercel.get("rewrites", [])
    redirects = vercel.get("redirects", [])
    rewrites = vercel.get("rewrites", [])
    redirects = vercel.get("redirects", [])
    rewrites = vercel.get("rewrites", [])
    root_redirects_to_trainer = any(
        r.get("source") == "/" and str(r.get("destination", "")).startswith("/trainer?release=") and r.get("permanent") is False
        for r in redirects
    )
    atlas_rewrite = any(r.get("source") == "/atlas" and r.get("destination") == "/index.html" for r in rewrites)
    legacy_index_redirect = any(r.get("source") == "/index.html" and r.get("destination") == "/atlas" for r in redirects)
    navigator_rewrite = any(r.get("source") == "/navigator" and r.get("destination") == "/navigator.html" for r in rewrites)
    trainer_rewrite = any(r.get("source") == "/trainer" and r.get("destination") == "/trainer.html" for r in rewrites)
    if not root_redirects_to_trainer:
        fail("Vercel root must explicitly redirect to a versioned /trainer URL", errors)
    else:
        ok("Public root explicitly redirects to versioned Mission Trainer")
    if not atlas_rewrite or not legacy_index_redirect:
        fail("Public Atlas routing must be /atlas -> index.html with legacy /index.html redirect", errors)
    else:
        ok("Public Atlas route is stable at /atlas and legacy index.html redirects")
    if not navigator_rewrite or not trainer_rewrite:
        fail("Trainer/Navigator clean public routes must be explicit rewrites", errors)
    else:
        ok("Trainer and Navigator public routes are explicit")

    stale_story_markers = ["# Solar Storyline", "Challenge alignment is intentionally pending", "Exact official 2026 challenge statement selected"]
    stale_hits = [marker for marker in stale_story_markers if marker in submission]
    if stale_hits:
        fail(f"SUBMISSION.md still contains stale competition narrative: {stale_hits}", errors)
    else:
        ok("Submission narrative is locked to the selected 2026 challenge")

    required_submission_phrases = ["Moon→Mars Mission Trainer", "Build a Junior Astronaut Mission Trainer", "NASA", "Revision C", "technology gap", "training credits", "provenance", "3D"]
    for phrase in required_submission_phrases:
        if phrase.lower() not in submission.lower():
            fail(f"SUBMISSION.md missing required competition concept: {phrase}", errors)
    if all(phrase.lower() in submission.lower() for phrase in required_submission_phrases):
        ok("Competition narrative contains the required current-product concepts")

    if "Requirement → implementation" not in alignment or "Build a Junior Astronaut Mission Trainer" not in alignment:
        fail("CHALLENGE_ALIGNMENT.md is incomplete", errors)
    else:
        ok("Challenge alignment matrix is present")

    print("\n=== COMPETITION READINESS SUMMARY ===")
    print(f"Integrity errors: {len(errors)}")
    print(f"Detailed traceability: {len(verified)}/{len(gaps)}")
    print("Challenge alignment: LOCKED — Build a Junior Astronaut Mission Trainer")
    print(f"Judge-facing root: / -> /trainer?release={release_id}")
    print(f"Production release: {release_id}")
    print("Timed judge demo: 30 seconds")
    print("Evidence engine: /atlas -> index.html")
    print("3D context: navigator.html")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
