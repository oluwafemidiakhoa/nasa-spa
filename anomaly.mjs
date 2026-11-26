import {historyReport} from './history.mjs';
import {MAX_BUNDLE} from './facility.mjs';
const DAY=86400000, BASELINE=19, MIN_ROWS=5;
export function screenHistory(h){
  const start=Date.parse(h.startUtc),end=Date.parse(h.endUtc);
  const full=h.facilities[0].days.filter(d=>{const t=Date.parse(d.date+'T00:00:00Z');return t>=start&&t+DAY-1<=end;}).map(d=>d.date);
  const target=full.at(-1)??null,baseline=full.slice(0,-1).slice(-BASELINE);
  const fields=d=>({date:d.date,availablePointRows:d.availablePointRows,matchingPointRows:d.matchingPointRows});
  const facilities=h.facilities.map(f=>{
    const byDate=new Map(f.days.map(d=>[d.date,d]));
    const current=target?fields(byDate.get(target)):null,prior=baseline.map(d=>fields(byDate.get(d)));
    let status='INSUFFICIENT_BASELINE',rankNumerator=null,rankDenominator=null;
    if(current&&prior.length===BASELINE){
      if([current,...prior].some(d=>d.availablePointRows<MIN_ROWS))status='INSUFFICIENT_OBSERVATIONS';
      else{rankNumerator=1+prior.filter(d=>d.matchingPointRows*current.availablePointRows>=current.matchingPointRows*d.availablePointRows).length;rankDenominator=BASELINE+1;status=rankNumerator===1?'ABOVE_BASELINE_MAX':'NOT_ABOVE_BASELINE_MAX';}
    }
    return {id:f.id,target:current,baseline:prior,rankNumerator,rankDenominator,status};
  });
  return {schema:'gaia-earth-anomaly-v0.8',policy:'daily-point-share-19-full-days-min5-v1',bundleSha256:h.bundleSha256,sourceSha256:h.sourceSha256,snapshotKind:h.snapshotKind,coverage:'unknown',targetDate:target,baselineDates:baseline,radiusKm:h.radiusKm,facilities};
}
export async function anomalyReport(bytes,anchor=''){return screenHistory(await historyReport(bytes,anchor));}
function startUI(){
  const $=id=>document.getElementById(id),file=$('anomaly-file'),anchor=$('anomaly-anchor'),select=$('anomaly-facility'),rows=$('anomaly-rows'),status=$('anomaly-status');let revision=0,report=null;
  const node=(tag,value)=>{const el=document.createElement(tag);el.textContent=value;return el;};
  function clear(message){revision++;report=null;$('anomaly-results').hidden=true;$('anomaly-export').disabled=true;rows.replaceChildren();select.replaceChildren();status.textContent=message;return revision;}
  function render(){if(!report)return;const f=report.facilities[Number(select.value)];if(!f)return;rows.replaceChildren();$('anomaly-rank').textContent=f.rankNumerator===null?'Abstained: '+f.status:f.status+' | upper-tail rank '+f.rankNumerator+'/'+f.rankDenominator+' (descriptive only)';for(const [d,role] of [...f.baseline.map(x=>[x,'Baseline']),...(f.target?[[f.target,'Target']]:[])]){const tr=document.createElement('tr');for(const v of [d.date,role,d.availablePointRows,d.matchingPointRows,d.availablePointRows?((100*d.matchingPointRows/d.availablePointRows).toFixed(1)+'%'):'Unavailable'])tr.append(node('td',v));rows.append(tr);}}
  async function load(get,expected){const rev=clear('Checking evidence and screening the fixed baseline...');try{const r=await anomalyReport(await get(),expected);if(rev!==revision)return;report=r;$('anomaly-kind').textContent=r.snapshotKind==='synthetic-demo'?'Synthetic demonstration: fictional observations and facilities':'Imported observations: source authenticity unverified';$('anomaly-window').textContent=(r.targetDate??'No complete target date')+' | '+r.baselineDates.length+' of 19 required baseline dates | '+r.radiusKm+' km radius';$('anomaly-hash').textContent=r.bundleSha256;for(const [i,f] of r.facilities.entries()){const opt=node('option',f.id);opt.value=i;select.append(opt);}render();$('anomaly-results').hidden=false;$('anomaly-export').disabled=false;status.textContent='Browser replay matched. Independent Python replay not performed.';}catch(e){if(rev===revision)clear('Screening rejected: '+String(e.message).slice(0,180));}}
  $('anomaly-demo').addEventListener('click',()=>{file.value='';anchor.value='';load(async()=>{const r=await fetch('data/earth-evidence-synthetic.json',{cache:'no-store'});if(!r.ok)throw Error('Demo unavailable');return new Uint8Array(await r.arrayBuffer());},'');});
  $('anomaly-load').addEventListener('click',()=>{const f=file.files[0];load(async()=>{if(!f||f.size>MAX_BUNDLE)throw Error('Select a bundle no larger than 26 MB');return new Uint8Array(await f.arrayBuffer());},anchor.value.trim());});
  for(const el of [file,anchor])el.addEventListener('input',()=>clear('Input changed. Inspect again.'));
  select.addEventListener('change',render);$('anomaly-clear').addEventListener('click',()=>{file.value='';anchor.value='';clear('No bundle loaded.');});
  $('anomaly-export').addEventListener('click',()=>{if(!report)return;const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='gaia-earth-anomaly.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
}
if(typeof document!=='undefined'&&document.getElementById('anomaly-file'))startUI();
