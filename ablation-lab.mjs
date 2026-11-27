import {screen} from './earth.mjs';
import {inspectBundle,strictJSON,MAX_BUNDLE} from './facility.mjs';
import {deriveCertificate,verifyBoundaryPacket} from './boundary-lab.mjs';
export const MAX_PACKET=40_000_000;
export const SCOPES=['nominal','lower','upper'];
const LABELS={nominal:'Nominal matching count',lower:'Conservative guaranteed lower bound',upper:'Conservative upper bound'};
const LIMIT='Exact minimum whole-event deletions for these count thresholds on the retained fixed records. Removing records is a hypothetical sensitivity experiment, not evidence that an event is false. Lower-bound failure loses a guarantee, not necessarily the claim. Upper bounds need not be attainable. Zero remaining eligible records means unavailable evidence, not safety. No hazard or source-authenticity inference.';
const ok=(v,m)=>{if(!v)throw Error(m);};
const keys=(x,k)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===k.length&&k.every(y=>Object.hasOwn(x,y));
const equal=(a,b)=>a===b||(Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>equal(v,b[i])))||(a&&b&&typeof a==='object'&&typeof b==='object'&&!Array.isArray(a)&&!Array.isArray(b)&&keys(b,Object.keys(a))&&Object.keys(a).every(k=>equal(a[k],b[k])));
const counts=c=>({nominal:c.nominalCount,lower:c.countBounds?.[0]??null,upper:c.countBounds?.[1]??null});
function included(row,scope){return scope==='nominal'?row.nominal:scope==='lower'?row.classification==='GUARANTEED_IN':row.classification!=='GUARANTEED_OUT';}
export function deriveAblation(model,facilityId,u,v,k,budget=0){
 ok(Number.isInteger(k)&&k>=1&&k<=2000&&Number.isInteger(budget)&&budget>=0&&budget<=2000,'Threshold must be 1–2000; deletion budget 0–2000 whole events');
 const c=deriveCertificate(model,facilityId,u,v),base=counts(c),eligible=c.rows.length;
 const scopes=SCOPES.map(scope=>{
  const m=base[scope],label=LABELS[scope];
  if(m===null)return {scope,label,count:null,state:'NO_ELIGIBLE_POINTS',minimumRemovals:null,worstCaseAfterBudget:null,survivesBudget:null,witness:null};
  const worst=Math.max(0,m-budget),min=Math.max(0,m-k+1);
  if(!min)return {scope,label,count:m,state:'ALREADY_BELOW_THRESHOLD',minimumRemovals:0,worstCaseAfterBudget:worst,survivesBudget:false,witness:null};
  // Any whole-event deletion removes at most one distinct ID from this set.
  const ids=c.rows.filter(x=>included(x,scope)).map(x=>x.eventId).sort().slice(0,min),removed=new Set(ids);
  ok(ids.length===min,'Invalid deletion witness');
  const snapshot={...model.snapshot,events:model.snapshot.events.filter(e=>!removed.has(e.id))},p=model.results.find(r=>r.facilityId===facilityId).parameters;
  const retained={...model,snapshot,results:[{facilityId,...screen(snapshot,p)}]};
  const after=deriveCertificate(retained,facilityId,u,v),afterCounts=counts(after),remaining=after.rows.length;
  ok(remaining===eligible-min&&(afterCounts[scope]??0)===m-min&&m-min===k-1,'Deletion witness did not replay');
  return {scope,label,count:m,state:'AT_OR_ABOVE_THRESHOLD',minimumRemovals:min,worstCaseAfterBudget:worst,survivesBudget:worst>=k,witness:{removedEventIds:ids,remainingEligibleEventIds:remaining,replayedCounts:afterCounts,mathematicalCountAfter:m-min,outcome:remaining?'BELOW_THRESHOLD':'NO_ELIGIBLE_POINTS_REMAIN'}};
 });
 return {schema:'gaia-evidence-ablation-v1',source:c.source,parameters:{...c.parameters,threshold:k,deletionBudget:budget},coverage:c.coverage,scopes,method:'distinct-whole-event-deletion-v1',minimality:'One deletion can reduce a distinct-event count by at most one; deleting exactly count-threshold+1 contributing IDs attains the minimum. Witnesses are replayed on a filtered copy of the original snapshot.',limitations:LIMIT};
}
function base64(bytes){let s='';for(let i=0;i<bytes.length;i+=16384)s+=String.fromCharCode(...bytes.subarray(i,i+16384));return btoa(s);}
export async function makeAblationPacket(bytes,facilityId,u,v,k,budget){
 const model=await inspectBundle(bytes),report=deriveAblation(model,facilityId,u,v,k,budget);
 return {schema:'gaia-ablation-packet-v1',bundle:{sha256:model.digest,bytes:bytes.length,base64:base64(bytes)},report};
}
export async function verifyAblationPacket(p){
 const b=p?.bundle,r=p?.report;
 ok(keys(p,['schema','bundle','report'])&&p.schema==='gaia-ablation-packet-v1'&&keys(b,['sha256','bytes','base64'])&&typeof b.sha256==='string'&&/^[a-f0-9]{64}$/.test(b.sha256)&&Number.isSafeInteger(b.bytes)&&b.bytes>0&&b.bytes<=MAX_BUNDLE&&typeof b.base64==='string'&&b.base64.length===4*Math.ceil(b.bytes/3),'Invalid ablation packet');
 const raw=atob(b.base64);ok(raw.length===b.bytes&&btoa(raw)===b.base64,'Invalid bundle encoding');
 const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0)),model=await inspectBundle(bytes,b.sha256),q=r?.parameters;
 const report=deriveAblation(model,q?.facilityId,q?.siteToleranceKm,q?.radiusToleranceKm,q?.threshold,q?.deletionBudget);ok(equal(report,r),'Ablation finding does not replay');return {bytes,model,report};
}
export function startAblation(doc=document,{fetchDemo=()=>fetch('data/boundary-demo.json',{cache:'no-store'}),save}={}){
 const $=id=>doc.getElementById(id),node=(tag,t)=>{const e=doc.createElement(tag);e.textContent=String(t);return e;};let revision=0,busy=false,accepted=null,report=null;
 const download=save||((bytes,name)=>{const url=URL.createObjectURL(new Blob([bytes],{type:'application/json'})),a=doc.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 function clear(s){report=null;$('ablation-result').hidden=true;$('ablation-rows').replaceChildren();$('ablation-export').disabled=true;$('ablation-status').textContent=s;}
 function numeric(id){const s=$(id).value.trim();ok(s,'Enter all four numeric assumptions');return Number(s);}
 function render(){clear('Open evidence first.');if(!accepted)return;try{
  const r=deriveAblation(accepted.model,$('ablation-site').value,numeric('ablation-u'),numeric('ablation-v'),numeric('ablation-k'),numeric('ablation-budget'));report=r;const p=r.parameters;
  $('ablation-context').textContent=(r.source.kind==='synthetic-demo'?'SYNTHETIC DEMONSTRATION — fictional records':'Retained observations — authenticity unverified')+' | '+p.facilityId+' | '+p.facility.join(', ')+' | radius '+p.radiusKm+' km | '+p.hours+' h ending '+p.asOf+' | threshold '+p.threshold+' | removal budget '+p.deletionBudget+' | bundle '+r.source.bundleSha256;
  for(const s of r.scopes){const tr=doc.createElement('tr'),h=node('th',s.label);h.scope='row';const witness=s.witness?('Remove '+s.witness.removedEventIds.slice(0,10).join(', ')+(s.witness.removedEventIds.length>10?' … (all IDs in packet)':'')+' | '+(s.witness.outcome==='NO_ELIGIBLE_POINTS_REMAIN'?'No eligible evidence remains.':'Replayed count: '+s.witness.mathematicalCountAfter)):'None required or available';tr.append(h,node('td',s.count??'Unavailable'),node('td',s.minimumRemovals??'Unavailable'),node('td',s.worstCaseAfterBudget??'Unavailable'),node('td',witness));$('ablation-rows').append(tr);}
  $('ablation-status').textContent=r.coverage.eligibleEventIds?'Three exact deletion thresholds calculated for the selected evidence model.':'No eligible records. Deletion thresholds withheld.';$('ablation-result').hidden=false;$('ablation-export').disabled=false;
 }catch(e){clear('Analysis unavailable: '+String(e.message).slice(0,140));}}
 function install(v){accepted=v;$('ablation-site').replaceChildren();for(const r of v.model.results){const o=node('option',r.facilityId);o.value=r.facilityId;$('ablation-site').append(o);}const p=v.report?.parameters;$('ablation-site').value=p?.facilityId??v.model.results[0].facilityId;if(p){$('ablation-u').value=String(p.siteToleranceKm);$('ablation-v').value=String(p.radiusToleranceKm);if(p.threshold!==undefined)$('ablation-k').value=String(p.threshold);if(p.deletionBudget!==undefined)$('ablation-budget').value=String(p.deletionBudget);}render();}
 async function run(work){if(busy)return;accepted=null;$('ablation-site').replaceChildren();clear('Checking original evidence...');const token=++revision;busy=true;$('ablation-open').disabled=true;$('ablation-demo').disabled=true;try{const v=await work();if(token===revision)install(v);}catch(e){if(token===revision)clear('Evidence unavailable: '+String(e.message).slice(0,160));}finally{busy=false;$('ablation-open').disabled=false;$('ablation-demo').disabled=false;}}
 $('ablation-open').addEventListener('click',()=>run(async()=>{const f=$('ablation-file').files[0];ok(f&&f.size>0&&f.size<=MAX_PACKET,'Choose an evidence JSON file up to 40 MB');const bytes=new Uint8Array(await f.arrayBuffer()),p=strictJSON(bytes);if(p?.schema==='gaia-ablation-packet-v1')return verifyAblationPacket(p);if(p?.schema==='gaia-boundary-packet-v1')return verifyBoundaryPacket(p);return {bytes,model:await inspectBundle(bytes)};}));
 $('ablation-demo').addEventListener('click',()=>run(async()=>{const r=await fetchDemo();ok(r.ok,'Fictional demonstration unavailable');const bytes=new Uint8Array(await r.arrayBuffer()),model=await inspectBundle(bytes);ok(model.kind==='synthetic-demo','Expected fictional demonstration');return {bytes,model,report:{parameters:{facilityId:model.results[0].facilityId,siteToleranceKm:10,radiusToleranceKm:5,threshold:2,deletionBudget:1}}};}));
 for(const id of ['ablation-site','ablation-u','ablation-v','ablation-k','ablation-budget'])$(id).addEventListener('change',render);
 $('ablation-file').addEventListener('input',()=>{revision++;accepted=null;$('ablation-site').replaceChildren();clear('File changed. Open evidence again.');});
 $('ablation-export').addEventListener('click',async()=>{if(!accepted||!report)return;const token=revision,r=report,v=accepted,p=r.parameters;try{const packet=await makeAblationPacket(v.bytes,p.facilityId,p.siteToleranceKm,p.radiusToleranceKm,p.threshold,p.deletionBudget);if(token!==revision||report!==r)return;const bytes=new TextEncoder().encode(JSON.stringify(packet));ok(bytes.length<=MAX_PACKET,'Packet exceeds 40 MB; retain original bundle');download(bytes,'gaia-ablation-'+r.source.bundleSha256.slice(0,12)+'.json');}catch(e){if(token===revision&&report===r)$('ablation-status').textContent='Export unavailable: '+String(e.message).slice(0,140);}});
 clear('Open a retained evidence packet or the fictional demonstration.');$('ablation-open').disabled=false;$('ablation-demo').disabled=false;return {render};
}
if(typeof document!=='undefined'&&document.getElementById('ablation-open'))startAblation();
