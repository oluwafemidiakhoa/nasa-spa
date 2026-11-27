import {inspectBundle,strictJSON,sha} from './facility.mjs';
import {verifyPacket as verifySeismic} from './seismic.mjs';
import {inspectReceipt as verifyWeather} from './nws-alerts.mjs';
export const MAX_PAIR=24_000_000,MAX_PACKET=34_000_000;
const LIMIT='Logical conflict concerns user-declared count predicates on identical retained evidence and scope, not real-world scientific truth. Different source semantics or snapshots do not establish contradiction. Source completeness and authenticity are unverified; missing records do not establish absence or safety.';
const ok=(v,m)=>{if(!v)throw Error(m);};
const keys=(o,k)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).length===k.length&&k.every(x=>Object.hasOwn(o,x));
const same=(a,b)=>a===b||(Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>same(v,b[i])))||(a&&b&&typeof a==='object'&&typeof b==='object'&&!Array.isArray(a)&&!Array.isArray(b)&&keys(b,Object.keys(a))&&Object.keys(a).every(k=>same(a[k],b[k])));
const sorted=a=>[...a].sort();
const claim=c=>{ok(keys(c,['facilityId','operator','threshold'])&&typeof c.facilityId==='string'&&c.facilityId.length<=64&&['atLeast','below'].includes(c.operator)&&Number.isInteger(c.threshold)&&c.threshold>=1&&c.threshold<=5001,'Invalid count claim');return {...c};};
export function exclusive(a,b){const x=claim(a),y=claim(b);return x.operator!==y.operator&&(x.operator==='atLeast'?x.threshold>=y.threshold:y.threshold>=x.threshold);}
function verdict(count,c){return count===null?'INSUFFICIENT_RECORDS':(c.operator==='atLeast'?count>=c.threshold:count<c.threshold)?'SUPPORTED_BY_REPLAY':'REFUTED_BY_REPLAY';}
async function load(bytes,c){
 ok(bytes instanceof Uint8Array&&bytes.length>0&&bytes.length<=MAX_PAIR,'Invalid evidence size');const p=strictJSON(bytes),artifactSha256=await sha(bytes);let domain,sourceSha256,capturedAt,count,ids,coverage;
 if(p?.schema==='gaia-earth-evidence-v0.5'){
  const m=await inspectBundle(bytes),r=c.facilityId?m.results.find(x=>x.facilityId===c.facilityId):m.results.length===1?m.results[0]:null;ok(r,'Specify a valid facility ID for multi-site evidence');
  const a=strictJSON(Uint8Array.from(atob(p.files.archive.base64),x=>x.charCodeAt(0))).receipt,q=a.query,t=r.parameters;
  domain={source:'EONET',metric:'distinct-eligible-point-event-ids',kind:m.kind,query:a.requestUrl,category:q?.category??null,window:[new Date(Date.parse(t.asOf)-t.hours*3600000).toISOString(),t.asOf],geography:{coordinates:t.facility,radiusKm:t.radiusKm},method:r.method};
  sourceSha256=m.sourceHash;capturedAt=m.capturedAt;count=r.coverage.eligiblePoints?r.matches.length:null;ids=r.matches.map(x=>x.eventId);coverage={...r.coverage,limitReached:a.limitReached};
 }else if(p?.schema==='gaia-seismic-packet-v1'){
  ok(!c.facilityId,'Facility ID applies to EONET bundles only');const r=await verifySeismic(p);
  domain={source:'USGS',metric:'distinct-M2.5+-earthquake-ids',kind:'retained-unverified',query:p.receipt.sourceUrl,category:'earthquakes',window:[r.window.start,r.window.end],geography:r.site,method:'gaia-seismic-screen-v1'};
  sourceSha256=r.sourceSha256;capturedAt=r.capturedAt;count=r.matchingEvents;ids=r.matches.map(x=>x.id);coverage={...r.coverage,freshness:r.freshness};
 }else if(p?.schema==='gaia-nws-alerts-v1'){
  ok(!c.facilityId,'Facility ID applies to EONET bundles only');const w=await verifyWeather(p,p.city);
  domain={source:'NWS',metric:'returned-alert-record-ids',kind:'retained-unverified',query:p.sourceUrl,category:'official-alert-records',window:[p.capturedAt,p.capturedAt],geography:{city:p.city},method:'gaia-nws-alerts-v1'};
  sourceSha256=p.sourceSha256;capturedAt=p.capturedAt;count=w.alerts.length;ids=w.alerts.map(x=>x.id);coverage={returned:count,scope:'public city-center point'};
 }else throw Error('Unsupported evidence: open an original EONET bundle, seismic packet or NWS receipt');
 ok(new Set(ids).size===ids.length&&(count===null?ids.length===0:count===ids.length),'Count and distinct IDs differ');return {artifactSha256,sourceSha256,capturedAt,domain,coverage,claim:c,count,verdict:verdict(count,c),ids:sorted(ids)};
}
export async function compareClaims(left,right,leftClaim,rightClaim){
 ok(left instanceof Uint8Array&&right instanceof Uint8Array&&left.length+right.length<=MAX_PAIR,'Combined evidence exceeds 24 MB');const a=await load(left,claim(leftClaim)),b=await load(right,claim(rightClaim));
 const mismatches=Object.keys(a.domain).filter(k=>!same(a.domain[k],b.domain[k]));const identicalSource=a.sourceSha256===b.sourceSha256;let status,logicalRelation='NOT_ESTABLISHED',delta=null;
 if(mismatches.length)status='INCOMPARABLE_SCOPE';
 else if(!identicalSource&&a.domain.query===null)status='UNKNOWN_OFFLINE_SCOPE';
 else if(a.count===null||b.count===null)status='INSUFFICIENT_RECORDS';
 else if(!identicalSource){status='DIFFERENT_RETAINED_SNAPSHOTS';const x=new Set(a.ids),y=new Set(b.ids);delta={leftOnly:a.ids.filter(id=>!y.has(id)),rightOnly:b.ids.filter(id=>!x.has(id)),shared:a.ids.filter(id=>y.has(id)).length,countDifference:b.count-a.count};}
 else{ok(a.count===b.count&&same(a.ids,b.ids),'Identical evidence yielded inconsistent replay');logicalRelation=exclusive(a.claim,b.claim)?'MUTUALLY_EXCLUSIVE':'NOT_MUTUALLY_EXCLUSIVE';status=logicalRelation==='MUTUALLY_EXCLUSIVE'?'LOGICAL_CONFLICT_ON_SAME_EVIDENCE':'NO_LOGICAL_CONFLICT_ESTABLISHED';}
 return {schema:'gaia-contradiction-report-v1',status,logicalRelation,mismatches,identicalSource,sourceAuthenticated:false,left:a,right:b,delta,limitations:LIMIT};
}
function base64(bytes){let s='';for(let i=0;i<bytes.length;i+=16384)s+=String.fromCharCode(...bytes.subarray(i,i+16384));return btoa(s);}
async function pack(bytes){return {sha256:await sha(bytes),bytes:bytes.length,base64:base64(bytes)};}
async function unpack(e){ok(keys(e,['sha256','bytes','base64'])&&typeof e.sha256==='string'&&/^[a-f0-9]{64}$/.test(e.sha256)&&Number.isSafeInteger(e.bytes)&&e.bytes>0&&e.bytes<=MAX_PAIR&&typeof e.base64==='string'&&e.base64.length===4*Math.ceil(e.bytes/3),'Invalid retained artifact');const raw=atob(e.base64);ok(raw.length===e.bytes&&btoa(raw)===e.base64,'Invalid retained bytes');const b=Uint8Array.from(raw,x=>x.charCodeAt(0));ok(await sha(b)===e.sha256,'Artifact digest mismatch');return b;}
export async function makeComparisonPacket(left,right,a,b){const report=await compareClaims(left,right,a,b);return {schema:'gaia-contradiction-packet-v1',left:await pack(left),right:await pack(right),report};}
export async function verifyComparisonPacket(p){ok(keys(p,['schema','left','right','report'])&&p.schema==='gaia-contradiction-packet-v1'&&Number.isSafeInteger(p.left?.bytes)&&Number.isSafeInteger(p.right?.bytes)&&p.left.bytes+p.right.bytes<=MAX_PAIR,'Invalid comparison packet');const left=await unpack(p.left),right=await unpack(p.right),report=await compareClaims(left,right,p.report?.left?.claim,p.report?.right?.claim);ok(same(report,p.report),'Comparison report does not replay');return {left,right,report};}
const LABELS={INCOMPARABLE_SCOPE:'Different scientific scope: comparison withheld',UNKNOWN_OFFLINE_SCOPE:'Different offline inputs with unknown query scope',INSUFFICIENT_RECORDS:'Insufficient eligible records: no conflict conclusion',DIFFERENT_RETAINED_SNAPSHOTS:'Different retained snapshots: not a scientific contradiction',LOGICAL_CONFLICT_ON_SAME_EVIDENCE:'Mutually exclusive claims on identical retained evidence',NO_LOGICAL_CONFLICT_ESTABLISHED:'No logical conflict established'};
export function startContradiction(doc=document,{fetchDemo=()=>fetch('data/boundary-demo.json',{cache:'no-store'}),save}={}){
 const $=id=>doc.getElementById(id),node=(tag,t)=>{const e=doc.createElement(tag);e.textContent=String(t);return e;};let rev=0,busy=false,current=null;
 const download=save||((data,name)=>{const u=URL.createObjectURL(new Blob([data],{type:'application/json'})),a=doc.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
 function clear(s){rev++;current=null;$('conflict-result').hidden=true;$('conflict-rows').replaceChildren();$('conflict-export').disabled=true;$('conflict-status').textContent=s;}
 function render(v){current=v;const r=v.report;$('conflict-status').textContent=LABELS[r.status];$('conflict-scope').textContent=r.mismatches.length?'Different fields: '+r.mismatches.join(', '):'Scope fields match; source bytes '+(r.identicalSource?'match.':'differ.');$('conflict-delta').textContent=r.delta?'Matching IDs only in A: '+r.delta.leftOnly.length+' | only in B: '+r.delta.rightOnly.length+' | shared: '+r.delta.shared+' | exact IDs in report.':'No record-set delta asserted.';for(const [label,x] of [['A',r.left],['B',r.right]]){const tr=doc.createElement('tr'),h=node('th',label);h.scope='row';tr.append(h,node('td',x.domain.source+' | '+x.domain.metric+' | '+x.domain.kind),node('td',x.claim.operator+' '+x.claim.threshold),node('td',x.count??'Unavailable'),node('td',x.verdict),node('td',JSON.stringify(x.domain)+' | capture '+x.capturedAt+' | SHA-256 '+x.sourceSha256));$('conflict-rows').append(tr);}$('conflict-result').hidden=false;$('conflict-export').disabled=false;}
 async function run(work){if(busy)return;clear('Checking evidence and comparing declared claims...');const token=rev;busy=true;for(const id of ['conflict-run','conflict-demo','conflict-open'])$(id).disabled=true;try{const v=await work();if(token===rev)render(v);}catch(e){if(token===rev)clear('Comparison unavailable: '+String(e.message).slice(0,180));}finally{busy=false;for(const id of ['conflict-run','conflict-demo','conflict-open'])$(id).disabled=false;}}
 function from(side){const k=$('conflict-k-'+side).value.trim();ok(k,'Enter a claim threshold');return {facilityId:$('conflict-site-'+side).value.trim(),operator:$('conflict-op-'+side).value,threshold:Number(k)};}
 async function read(f,max){ok(f&&f.size>0&&f.size<=max,'Select a supported file within the size limit');return new Uint8Array(await f.arrayBuffer());}
 async function review(a,b,x,y){return {left:a,right:b,report:await compareClaims(a,b,x,y)};}
 $('conflict-run').addEventListener('click',()=>run(async()=>{const a=$('conflict-file-a').files[0],b=$('conflict-file-b').files[0];ok(a&&b&&a.size+b.size<=MAX_PAIR,'Choose two files totaling at most 24 MB');return review(await read(a,MAX_PAIR),await read(b,MAX_PAIR),from('a'),from('b'));}));
 $('conflict-demo').addEventListener('click',()=>run(async()=>{const r=await fetchDemo();ok(r.ok,'Fictional demonstration unavailable');const b=new Uint8Array(await r.arrayBuffer()),m=await inspectBundle(b);ok(m.kind==='synthetic-demo','Expected fictional evidence');return review(b,b,{facilityId:'',operator:'atLeast',threshold:3},{facilityId:'',operator:'below',threshold:3});}));
 $('conflict-open').addEventListener('click',()=>run(async()=>verifyComparisonPacket(strictJSON(await read($('conflict-packet').files[0],MAX_PACKET)))));
 for(const id of ['conflict-file-a','conflict-file-b','conflict-site-a','conflict-site-b','conflict-op-a','conflict-op-b','conflict-k-a','conflict-k-b','conflict-packet'])$(id).addEventListener('input',()=>clear('Inputs changed. Run a new comparison.'));
 $('conflict-export').addEventListener('click',async()=>{if(!current)return;const v=current,token=rev;try{const p=await makeComparisonPacket(v.left,v.right,v.report.left.claim,v.report.right.claim),bytes=new TextEncoder().encode(JSON.stringify(p));ok(bytes.length<=MAX_PACKET,'Comparison packet exceeds 34 MB');if(token===rev&&current===v)download(bytes,'gaia-contradiction-'+v.report.left.artifactSha256.slice(0,12)+'.json');}catch(e){if(token===rev)$('conflict-status').textContent='Export unavailable: '+String(e.message).slice(0,140);}});clear('Open two supported evidence artifacts or use the fictional example.');for(const id of ['conflict-run','conflict-demo','conflict-open'])$(id).disabled=false;return {clear};
}
if(typeof document!=='undefined'&&document.getElementById('conflict-run'))startContradiction();
