from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

replacements = [
    (
        ".statusRibbon.resolved{color:var(--green);border-color:#2c7659;background:#0a1511}\n.roadmap",
        ".statusRibbon.resolved{color:var(--green);border-color:#2c7659;background:#0a1511}.node.residual,.segment.residual{border-color:#6e5625;color:#f0d58d;background:#17140c;box-shadow:0 0 20px rgba(243,200,98,.06)}\n.roadmap"
    ),
    (
        ".reach .s{font-size:.67rem;color:var(--muted);margin-top:3px}\n.reverseGraph",
        ".reach .s{font-size:.67rem;color:var(--muted);margin-top:3px}.residualPanel{margin-top:12px;border-top:1px solid var(--line);padding-top:13px}.residualSummary{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.residualSummary h3{font:700 .82rem var(--display)}.residualSummary p{font-size:.68rem;color:var(--muted);margin-top:4px;line-height:1.45}.residualBadge{font:700 .55rem var(--mono);color:var(--gold);border:1px solid #5a4b27;border-radius:999px;padding:5px 7px;white-space:nowrap}.residualGrid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:10px}.residualCard{border:1px solid var(--line);border-radius:9px;background:#0a1018;padding:10px}.residualCard.cleared{border-color:#285b46;background:#0a1511}.residualCard.exposed{border-color:#5a4b27;background:#15130c}.residualCard .rk{font:700 .53rem var(--mono);color:var(--muted);letter-spacing:.08em;text-transform:uppercase}.residualCard h4{font:700 .73rem var(--display);margin-top:4px}.residualCard .remaining{margin-top:7px;display:grid;gap:4px}.residualCard .remaining div{font-size:.65rem;color:var(--soft);line-height:1.35}.residualCard.cleared .remaining div{color:var(--green)}\n.reverseGraph"
    ),
    (
        "function mappedGapsForArchitecture(name){return gaps().filter(g=>(g.subarchitectures||[]).includes(name)||(g.segments||[]).includes(name))}\nfunction allArchitectureChoices()",
        "function mappedGapsForArchitecture(name){return gaps().filter(g=>(g.subarchitectures||[]).includes(name)||(g.segments||[]).includes(name))}\nfunction residualGapsForNode(name,excludeId){return mappedGapsForArchitecture(name).filter(g=>g.id!==excludeId)}\nfunction residualForGap(g){return uniq([...(g.subarchitectures||[]),...(g.segments||[])]).map(name=>({name,remaining:residualGapsForNode(name,g.id)}))}\nfunction allArchitectureChoices()"
    ),
    (
        "function renderGapGraph(g){const resolved=gapState==='resolved',subs=g.subarchitectures||[],segs=g.segments||[];",
        "function renderGapGraph(g){const resolved=gapState==='resolved',subs=g.subarchitectures||[],segs=g.segments||[],residual=residualForGap(g),residualMap=new Map(residual.map(r=>[r.name,r]));"
    ),
    (
        "${subs.includes(n)?(resolved?'resolved':'hit'):''}",
        "${subs.includes(n)?(resolved?(residualMap.get(n)?.remaining.length?'residual':'resolved'):'hit'):''}"
    ),
    (
        "${resolved&&subs.includes(n)?'✓ ':''}${esc(shortSub[n]||n)}",
        "${resolved&&subs.includes(n)?(residualMap.get(n)?.remaining.length?'⚠ '+residualMap.get(n).remaining.length+' remain · ':'✓ '):''}${esc(shortSub[n]||n)}"
    ),
    (
        "${segs.includes(n)?(resolved?'resolved':'hit'):''}",
        "${segs.includes(n)?(resolved?(residualMap.get(n)?.remaining.length?'residual':'resolved'):'hit'):''}"
    ),
    (
        "${resolved&&segs.includes(n)?'✓ ':''}${esc(n)}",
        "${resolved&&segs.includes(n)?(residualMap.get(n)?.remaining.length?'⚠ '+residualMap.get(n).remaining.length+' remain · ':'✓ '):''}${esc(n)}"
    ),
    (
        "${resolved?'THIS ONE DOCUMENTED DEFICIENCY IS MARKED ADDRESSED · OTHER GAPS REMAIN':'CURRENT NASA-DOCUMENTED GAP REACH'}",
        "${resolved?('SELECTED GAP ADDRESSED · '+residual.reduce((s,r)=>s+r.remaining.length,0)+' OTHER LOADED CONNECTIONS REMAIN ACROSS '+residual.filter(r=>r.remaining.length).length+' AFFECTED NODES'):'CURRENT NASA-DOCUMENTED GAP REACH'}"
    ),
    (
        "<div class=\"s\">${subs.length} sub-architectures + ${segs.length} segments</div></div></div></section>`;",
        "<div class=\"s\">${subs.length} sub-architectures + ${segs.length} segments</div></div></div>${resolved?renderResidualPanel(g,residual):''}</section>`;"
    ),
    (
        "requestAnimationFrame(()=>drawGapLines(resolved))}\nfunction drawGapLines",
        "requestAnimationFrame(()=>drawGapLines(resolved))}\nfunction renderResidualPanel(g,residual){const exposed=residual.filter(r=>r.remaining.length),cleared=residual.filter(r=>!r.remaining.length),connectionCount=exposed.reduce((s,r)=>s+r.remaining.length,0);return `<div class=\"residualPanel\"><div class=\"residualSummary\"><div><div class=\"eyebrow\">Residual dependency check</div><h3>What still touches these systems after #${esc(g.priority_rank??'—')} is addressed?</h3><p>This is deterministic graph subtraction: remove only the selected gap, then inspect the other loaded NASA gap mappings that still touch the same architecture nodes.</p></div><span class=\"residualBadge\">${connectionCount} REMAINING CONNECTION${connectionCount===1?'':'S'}</span></div><div class=\"residualGrid\">${residual.map(r=>`<div class=\"residualCard ${r.remaining.length?'exposed':'cleared'}\"><div class=\"rk\">${r.remaining.length?'STILL EXPOSED':'NO OTHER LOADED GAPS'}</div><h4>${esc(shortSub[r.name]||r.name)}</h4><div class=\"remaining\">${r.remaining.length?r.remaining.slice(0,4).map(x=>`<div>#${x.priority_rank??'—'} · ${esc(x.title)}</div>`).join(''):'<div>✓ Selected deficiency removed; no other loaded gap mapping touches this node.</div>'}${r.remaining.length>4?`<div>+ ${r.remaining.length-4} more loaded gaps</div>`:''}</div></div>`).join('')}</div><div class=\"dataNote\">No readiness score is computed. Counts reflect only relationships present in the currently loaded NASA dataset.</div></div>`}\nfunction drawGapLines"
    ),
    (
        "Address this one gap: dependency lines visibly change, but mission readiness is not implied.",
        "Address this gap: now see which affected systems still carry other loaded NASA technology gaps."
    ),
]

for old, new in replacements:
    if old not in text:
        raise SystemExit(f'Patch anchor not found: {old[:160]}')
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('Residual dependency engine patch applied')
