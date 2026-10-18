#!/usr/bin/env python3
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import patch_atlas_3d_roundtrip as patch


UNPATCHED_HTML = """<div class="modebar"><div class="modes"><button class="modeBtn active" data-view="gap">GAP → ARCHITECTURE</button><button class="modeBtn" data-view="reverse">ARCHITECTURE → GAPS</button><button class="modeBtn" data-view="compare">COMPARE GAPS</button></div><button class="judgeBtn" id="judgeBtn">▶ 30-SECOND JUDGE MODE</button></div>
<script>
async function boot(){DATA=await r.json();selected=gapById('0801');if(!selected)selected=gaps()[0];}
function renderGapView(){const g=selected||gaps()[0];}
function renderGapDetail(g){return `<a class="archiveLink" href="navigator.html">Technical archive: legacy 3D navigator ↗</a>`}
</script>
"""

PARTIALLY_PATCHED_HTML = """<div class="modebar"><div class="modes"><button class="modeBtn active" data-view="gap">GAP → ARCHITECTURE</button><button class="modeBtn" data-view="reverse">ARCHITECTURE → GAPS</button><button class="modeBtn" data-view="compare">COMPARE GAPS</button></div><button class="judgeBtn" id="judgeBtn">▶ 30-SECOND JUDGE MODE</button></div>
<script>
const note = "OPEN SELECTED GAP IN 3D";
async function boot(){DATA=await r.json();selected=gapById('0801');if(!selected)selected=gaps()[0];}
function renderGapView(){const g=selected||gaps()[0];}
function renderGapDetail(g){return `<a class="archiveLink" href="navigator.html">Technical archive: legacy 3D navigator ↗</a>`}
</script>
"""


def run_script(html):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "index.html"
        path.write_text(html, encoding="utf-8")
        original_cwd = Path.cwd()
        os.chdir(path.parent)
        try:
            patch.main()
            return path.read_text(encoding="utf-8")
        finally:
            os.chdir(original_cwd)


def main():
    updated = run_script(UNPATCHED_HTML)
    assert "OPEN SELECTED GAP IN 3D" in updated
    assert "requestedGap=new URLSearchParams" in updated
    assert "navigator.html?gap=${encodeURIComponent(g.id)}" in updated

    partial = run_script(PARTIALLY_PATCHED_HTML)
    assert 'const note = "OPEN SELECTED GAP IN 3D";' in partial
    assert partial.count("requestedGap=new URLSearchParams") == 1
    assert partial.count("navigator.html?gap=${encodeURIComponent(g.id)}") == 1

    rerun = run_script(updated)
    assert rerun == updated
    print("Atlas 3D round-trip patch tests: PASS")


if __name__ == "__main__":
    main()
