#!/usr/bin/env python3
from pathlib import Path


PATCH_MARKERS = (
    "OPEN SELECTED GAP IN 3D",
    "requestedGap=new URLSearchParams",
    "navigator.html?gap=${encodeURIComponent(g.id)}",
)

REPLACEMENTS = (
    (
        '</div><button class="judgeBtn" id="judgeBtn">▶ 30-SECOND JUDGE MODE</button></div>',
        '</div><div style="display:flex;gap:8px;align-items:center"><a class="judgeBtn" id="open3D" href="navigator.html?gap=0801">🌐 OPEN SELECTED GAP IN 3D</a><button class="judgeBtn" id="judgeBtn">▶ 30-SECOND JUDGE MODE</button></div></div>',
    ),
    (
        "DATA=await r.json();selected=gapById('0801');if(!selected)selected=gaps()[0];",
        "DATA=await r.json();const requestedGap=new URLSearchParams(location.search).get('gap');selected=gapById(requestedGap||'0801');if(!selected)selected=gaps()[0];",
    ),
    (
        "function renderGapView(){const g=selected||gaps()[0];",
        "function renderGapView(){const g=selected||gaps()[0];history.replaceState(null,'','?gap='+encodeURIComponent(g.id));const open3D=$('#open3D');if(open3D)open3D.href='navigator.html?gap='+encodeURIComponent(g.id);",
    ),
    (
        '<a class="archiveLink" href="navigator.html">Technical archive: legacy 3D navigator ↗</a>',
        '<a class="archiveLink" href="navigator.html?gap=${encodeURIComponent(g.id)}" style="color:var(--cyan);font-size:.64rem">🌐 OPEN THIS GAP IN 3D ↗</a>',
    ),
)


def apply_patch(text):
    if all(marker in text for marker in PATCH_MARKERS):
        return text, False

    updated = text
    changed = False
    for old, new in REPLACEMENTS:
        if new in updated:
            continue
        if old not in updated:
            raise SystemExit(f"Expected Atlas patch anchor not found: {old[:100]}")
        updated = updated.replace(old, new, 1)
        changed = True
    return updated, changed


def main():
    path = Path("index.html")
    text = path.read_text(encoding="utf-8")
    updated, changed = apply_patch(text)
    if changed:
        path.write_text(updated, encoding="utf-8")
        print("Atlas 3D round-trip patch applied")
        return
    print("Atlas 3D round-trip patch already present")


if __name__ == "__main__":
    main()
