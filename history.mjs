import {inspectBundle,MAX_BUNDLE} from './facility.mjs';
import {distanceKm} from './earth.mjs';
const DAY=86400000;
const iso=t=>new Date(t).toISOString();
export async function historyReport(bytes,anchor=''){
  const m=await inspectBundle(bytes,anchor), p=m.results[0].parameters;
  const end=Date.parse(p.asOf),start=end-p.hours*3600000,first=Math.floor(start/DAY)*DAY,last=Math.floor(end/DAY)*DAY;
  if(start<Date.parse('0001-01-01T00:00:00Z')||last-first>30*DAY)throw Error('Unsupported history interval');
  const bins=[];
  for(let t=first;t<=last;t+=DAY)bins.push({date:iso(t).slice(0,10),available:0,points:[]});
  for(const e of m.snapshot.events)for(const g of e.geometry){
    if(g.type!=='Point')continue;
    const t=Date.parse(g.date);
    if(t<start||t>end)continue;
    const bin=bins[Math.floor((t-first)/DAY)];bin.available++;bin.points.push({id:e.id,coordinates:g.coordinates});
  }
  const facilities=m.results.map(r=>({id:r.facilityId,coordinates:r.parameters.facility,days:bins.map(b=>{
    const matching=b.points.filter(x=>distanceKm(r.parameters.facility,x.coordinates)<=p.radiusKm);
    return {date:b.date,availablePointRows:b.available,matchingPointRows:matching.length,matchingEvents:new Set(matching.map(x=>x.id)).size,state:b.available?'OBSERVATIONS_AVAILABLE':'NO_ELIGIBLE_POINTS'};
  })}));
  return {schema:'gaia-earth-history-v0.7',bundleSha256:m.digest,sourceSha256:m.sourceHash,snapshotKind:m.kind,coverage:'unknown',startUtc:iso(start),endUtc:iso(end),radiusKm:p.radiusKm,facilities};
}
function startUI(){
  const $=id=>document.getElementById(id),file=$('history-file'),anchor=$('history-anchor'),select=$('history-facility'),rows=$('history-rows'),status=$('history-status');let revision=0,report=null;
  const node=(tag,value)=>{const el=document.createElement(tag);el.textContent=value;return el;};
  function clear(message){revision++;report=null;$('history-results').hidden=true;$('history-export').disabled=true;rows.replaceChildren();select.replaceChildren();status.textContent=message;return revision;}
  function renderDays(){if(!report)return;const f=report.facilities[Number(select.value)];if(!f)return;rows.replaceChildren();const max=Math.max(1,...f.days.map(d=>d.availablePointRows));for(const d of f.days){const tr=document.createElement('tr');tr.append(node('th',d.date),node('td',d.availablePointRows),node('td',d.matchingPointRows),node('td',d.matchingEvents));const td=document.createElement('td'),bar=document.createElement('meter');bar.min=0;bar.max=max;bar.value=d.matchingPointRows;bar.setAttribute('aria-label','Matching point rows: '+d.matchingPointRows);td.append(bar,node('small',d.state==='NO_ELIGIBLE_POINTS'?'No eligible observations':'Available observations'));tr.append(td);rows.append(tr);}}
  async function load(get,expected){const rev=clear('Checking original bundle and building UTC history...');try{const r=await historyReport(await get(),expected);if(rev!==revision)return;report=r;$('history-kind').textContent=r.snapshotKind==='synthetic-demo'?'Synthetic demonstration: fictional events and facilities':'Imported observations: source authenticity unverified';$('history-window').textContent=r.startUtc+' through '+r.endUtc+' (inclusive) | '+r.radiusKm+' km radius';$('history-hash').textContent=r.bundleSha256;for(const [i,f] of r.facilities.entries()){const opt=node('option',f.id);opt.value=i;select.append(opt);}renderDays();$('history-results').hidden=false;$('history-export').disabled=false;status.textContent='Browser consistency replay matched. Independent Python replay not performed.';}catch(e){if(rev===revision)clear('History rejected: '+String(e.message).slice(0,180));}}
  $('history-demo').addEventListener('click',()=>{file.value='';anchor.value='';load(async()=>{const r=await fetch('data/earth-evidence-synthetic.json',{cache:'no-store'});if(!r.ok)throw Error('Demo unavailable');return new Uint8Array(await r.arrayBuffer());},'');});
  $('history-load').addEventListener('click',()=>{const f=file.files[0];load(async()=>{if(!f||f.size>MAX_BUNDLE)throw Error('Select a bundle no larger than 26 MB');return new Uint8Array(await f.arrayBuffer());},anchor.value.trim());});
  for(const el of [file,anchor])el.addEventListener('input',()=>clear('Input changed. Inspect again.'));
  select.addEventListener('change',renderDays);
  $('history-clear').addEventListener('click',()=>{file.value='';anchor.value='';clear('No bundle loaded.');});
  $('history-export').addEventListener('click',()=>{if(!report)return;const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='gaia-earth-history.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
}
if(typeof document!=='undefined'&&document.getElementById('history-file'))startUI();
