from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

replacements = [
    (
        '</div><button class="judgeBtn" id="judgeBtn">▶ 30-SECOND JUDGE MODE</button></div>',
        '</div><div style="display:flex;gap:8px;align-items:center"><a class="judgeBtn" id="open3D" href="navigator.html?gap=0801">🌐 OPEN SELECTED GAP IN 3D</a><button class="judgeBtn" id="judgeBtn">▶ 30-SECOND JUDGE MODE</button></div></div>'
    ),
    (
        "DATA=await r.json();selected=gapById('0801');if(!selected)selected=gaps()[0];",
        "DATA=await r.json();const requestedGap=new URLSearchParams(location.search).get('gap');selected=gapById(requestedGap||'0801');if(!selected)selected=gaps()[0];"
    ),
    (
        "function renderGapView(){const g=selected||gaps()[0];",
        "function renderGapView(){const g=selected||gaps()[0];history.replaceState(null,'','?gap='+encodeURIComponent(g.id));const open3D=$('#open3D');if(open3D)open3D.href='navigator.html?gap='+encodeURIComponent(g.id);"
    ),
    (
        '<a class="archiveLink" href="navigator.html">Technical archive: legacy 3D navigator ↗</a>',
        '<a class="archiveLink" href="navigator.html?gap=${encodeURIComponent(g.id)}" style="color:var(--cyan);font-size:.64rem">🌐 OPEN THIS GAP IN 3D ↗</a>'
    ),
]

for old, new in replacements:
    if old not in text:
        raise SystemExit(f'Expected Atlas patch anchor not found: {old[:100]}')
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('Atlas 3D round-trip patch applied')
