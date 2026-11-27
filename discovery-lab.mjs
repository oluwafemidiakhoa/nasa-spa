import {inspectBundle,strictJSON,sha} from './facility.mjs';
import {study,fetchStudy} from './workspace.mjs';
export const MAX_PAIR=24_000_000, MAX_PACKET=34_000_000;
const DAY=86400000, ID='TRIAL-REFERENCE';
const LIMIT='This trial concerns distinct returned EONET event IDs, not actual incident occurrence, exposure, hazards, or safety. Coverage and source authenticity are unknown. A locally recorded digest and declared times do not prove chronological registration, source authenticity, or first capture. A single scored trial cannot establish predictive superiority. No trained model is supplied.';
const ok=(v,m)=>{if(!v)throw Error(m);};
const keys=(x,k)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===k.length&&k.every(y=>Object.hasOwn(x,y));
const same=(a,b)=>a===b||(Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>same(v,b[i])))||(a&&b&&typeof a==='object'&&typeof b==='object'&&!Array.isArray(a)&&!Array.isArray(b)&&keys(b,Object.keys(a))&&Object.keys(a).every(k=>same(a[k],b[k])));
const enc=o=>new TextEncoder().encode(JSON.stringify(o));
const iso=t=>new Date(t).toISOString();
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
function time(x){const t=Date.parse(x);ok(typeof x==='string'&&Number.isFinite(t)&&iso(t)===x,'Invalid declared UTC timestamp');return t;}
function validClock(n){ok(Number.isSafeInteger(n)&&n>=Date.UTC(2000,0,1)&&n<Date.UTC(9998,0,1),'Invalid clock');return n;}
const date=t=>iso(t).slice(0,10);
export function trialWindows(now){const t=Math.floor(validClock(now)/DAY)*DAY;return {baseline:{start:date(t-7*DAY),end:date(t-DAY),asOf:iso(t)},target:{start:date(t+DAY),end:date(t+7*DAY),asOf:iso(t+8*DAY),captureDeadline:iso(t+10*DAY)}};}
export function trialInput(x){
 ok(keys(x,['category','coordinates','radiusKm','threshold','probability']),'Invalid trial fields');
 ok(Number.isInteger(x.threshold)&&x.threshold>=1&&x.threshold<=200&&Number.isFinite(x.probability)&&x.probability>=0&&x.probability<=1,'Threshold must be 1-200 and probability 0-1');
 const site={category:x.category,coordinates:Array.isArray(x.coordinates)?x.coordinates.slice():x.coordinates,radiusKm:x.radiusKm,threshold:x.threshold,probability:x.probability};
 study(studyInput(site,{start:'2026-01-01',end:'2026-01-07'}));return site;
}
export function studyInput(site,window){return {start:window.start,end:window.end,category:site.category,radiusKm:site.radiusKm,facilities:[{id:ID,coordinates:site.coordinates.slice()}]};}
function b64(bytes){let s='';for(let i=0;i<bytes.length;i+=16384)s+=String.fromCharCode(...bytes.subarray(i,i+16384));return btoa(s);}
function decode(s,max){ok(typeof s==='string'&&s.length>0&&s.length<=4*Math.ceil(max/3),'Invalid evidence encoding');const raw=atob(s);ok(raw.length>0&&raw.length<=max&&btoa(raw)===s,'Invalid evidence encoding');return Uint8Array.from(raw,c=>c.charCodeAt(0));}
async function pack(bytes){ok(bytes instanceof Uint8Array&&bytes.length>0&&bytes.length<=MAX_PAIR,'Invalid evidence size');return {sha256:await sha(bytes),bytes:bytes.length,base64:b64(bytes)};}
async function unpack(x){ok(keys(x,['sha256','bytes','base64'])&&hex(x.sha256)&&Number.isSafeInteger(x.bytes)&&x.bytes>0&&x.bytes<=MAX_PAIR&&typeof x.base64==='string'&&x.base64.length===4*Math.ceil(x.bytes/3),'Invalid retained artifact');const b=decode(x.base64,MAX_PAIR);ok(b.length===x.bytes&&await sha(b)===x.sha256,'Artifact digest mismatch');return b;}
async function inspectWindow(bytes,site,window){
 ok(bytes instanceof Uint8Array&&bytes.length>0&&bytes.length<=MAX_PAIR,'Evidence size limit');
 const m=await inspectBundle(bytes),p=strictJSON(bytes),a=strictJSON(decode(p.files.archive.base64,3_000_000)),r=a.receipt;
 const expected=study(studyInput(site,window));
 ok(m.mode==='https-eonet'&&m.kind==='user-import-unverified'&&same(r.query,expected.query)&&m.results.length===1,'Evidence acquisition scope differs');
 const row=m.results[0],q=row.parameters;
 ok(row.facilityId===ID&&q.hours===168&&q.asOf===window.asOf&&q.radiusKm===site.radiusKm&&same(q.facility,site.coordinates),'Evidence screening scope differs');
 const captured=time(m.capturedAt);
 ok(m.snapshot.events.every(e=>e.geometry.every(g=>g.type!=='Point'||Date.parse(g.date)<=captured)),'Evidence contains a point dated after capture');
 return {captured,summary:{bundleSha256:m.digest,sourceSha256:m.sourceHash,capturedAt:m.capturedAt,coverage:row.coverage,limitReached:r.limitReached,count:row.status==='NO_ELIGIBLE_POINTS'?null:row.matches.length},matches:row.matches.map(x=>x.eventId)};
}
export function brier(probability,y){ok(Number.isFinite(probability)&&probability>=0&&probability<=1&&(y===0||y===1),'Invalid Brier inputs');return (probability-y)**2;}
export async function freezeTrial(input,baselineBytes,now=Date.now()){
 const site=trialInput(input),issued=validClock(now),windows=trialWindows(issued),base=await inspectWindow(baselineBytes,site,windows.baseline);
 ok(base.captured>=time(windows.baseline.asOf)&&base.captured<=issued,'Baseline capture outside allowed period');
 ok(base.summary.count!==null&&!base.summary.limitReached,'Baseline unavailable or capped; trial not locked');
 const manifest={schema:'gaia-discovery-lock-v1',issuedAt:iso(issued),chronology:'DECLARED_CLOCK_ONLY',sourceAuthenticated:false,site,windows,baseline:base.summary,persistenceProbability:base.summary.count>=site.threshold?1:0,metric:'paired-brier-loss-v1',capturePolicy:'accept-one-retained-snapshot-within-48h; first capture not independently established',limitations:LIMIT};
 return {schema:'gaia-discovery-lock-packet-v1',manifest,manifestSha256:await sha(enc(manifest)),baselineArtifact:await pack(baselineBytes)};
}
export async function verifyLock(lock,anchor=''){
 ok(keys(lock,['schema','manifest','manifestSha256','baselineArtifact'])&&lock.schema==='gaia-discovery-lock-packet-v1'&&hex(lock.manifestSha256)&&(!anchor||hex(anchor)),'Invalid trial lock');
 ok(!anchor||anchor===lock.manifestSha256,'Independently retained manifest digest mismatch');
 const bytes=await unpack(lock.baselineArtifact),expected=await freezeTrial(lock.manifest?.site,bytes,time(lock.manifest?.issuedAt));
 ok(same(expected,lock),'Locked prediction or baseline does not replay');return {lock:expected,baselineBytes:bytes,anchorMatched:!!anchor};
}
export async function evaluateTrial(lock,outcomeBytes,{now=Date.now(),anchor=''}={}){
 const v=await verifyLock(lock,anchor),m=v.lock.manifest,t=validClock(now),start=time(m.windows.target.asOf),deadline=time(m.windows.target.captureDeadline);
 ok(t>=start,'Outcome window has not finished');ok(outcomeBytes instanceof Uint8Array&&v.baselineBytes.length+outcomeBytes.length<=MAX_PAIR,'Combined evidence exceeds limit');
 const x=await inspectWindow(outcomeBytes,m.site,m.windows.target);
 ok(x.captured>=start&&x.captured<=deadline&&x.captured<=t,'Outcome capture outside locked period');
 ok(x.summary.sourceSha256!==m.baseline.sourceSha256,'Baseline source bytes reused as outcome');
 const reason=x.summary.limitReached?'SOURCE_LIMIT_REACHED':x.summary.count===null?'NO_ELIGIBLE_POINTS':null;
 const y=reason?null:x.summary.count>=m.site.threshold?1:0;
 const candidate=y===null?null:brier(m.site.probability,y),persistence=y===null?null:brier(m.persistenceProbability,y);
 return {schema:'gaia-discovery-evaluation-v1',manifestSha256:v.lock.manifestSha256,evaluatedAt:iso(t),chronology:'DECLARED_CLOCK_ONLY',sourceAuthenticated:false,status:reason?'WITHHELD':'SCORED_RETAINED_RECORDS',withheldReason:reason,outcome:x.summary,matchingEventIds:x.matches,threshold:m.site.threshold,candidateProbability:m.site.probability,persistenceProbability:m.persistenceProbability,observedBinary:y,candidateBrier:candidate,persistenceBrier:persistence,lossDifference:candidate===null?null:candidate-persistence,limitations:LIMIT};
}
export async function makeEvaluationPacket(lock,bytes,options){const report=await evaluateTrial(lock,bytes,options);return {schema:'gaia-discovery-evaluation-packet-v1',lock,outcomeArtifact:await pack(bytes),report};}
export async function verifyEvaluationPacket(p,anchor=''){
 ok(keys(p,['schema','lock','outcomeArtifact','report'])&&p.schema==='gaia-discovery-evaluation-packet-v1','Invalid evaluation packet');
 const b=await unpack(p.outcomeArtifact);
 // A digest supplied by the verifier is checked separately; never trust an archived claim of external anchoring.
 const report=await evaluateTrial(p.lock,b,{now:time(p.report?.evaluatedAt),anchor});
 ok(same(report,p.report),'Evaluation report does not replay');return {packet:p,report,anchorMatched:!!anchor};
}
export function startDiscovery(doc=document,{load=fetchStudy,clock=()=>Date.now(),save}={}){
 const $=id=>doc.getElementById(id);let rev=0,busy=false,current=null,result=null;
 const download=save||((data,name)=>{const url=URL.createObjectURL(new Blob([data],{type:'application/json'})),a=doc.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 function buttons(){for(const id of ['trial-freeze','trial-open','trial-reopen-eval'])$(id).disabled=busy;for(const id of ['trial-export-lock','trial-evaluate-file','trial-fetch-outcome'])$(id).disabled=busy||!current;$('trial-export-eval').disabled=busy||!result;}
 function clearResult(){result=null;$('trial-eval-result').hidden=true;$('trial-eval-summary').textContent='';buttons();}
 function reset(s){rev++;current=null;clearResult();$('trial-lock-result').hidden=true;$('trial-lock-summary').textContent='';$('trial-status').textContent=s;buttons();}
 function num(id){const v=$(id).value.trim();ok(v,'Enter all numeric assumptions');return Number(v);}
 function input(){return trialInput({category:$('trial-category').value,coordinates:[num('trial-lon'),num('trial-lat')],radiusKm:num('trial-radius'),threshold:num('trial-threshold'),probability:num('trial-probability')});}
 function install(v,anchorMatched=false){current=v;const m=v.manifest;$('trial-lock-summary').textContent='Manifest SHA-256: '+v.manifestSha256+'\nDeclared issue: '+m.issuedAt+'\nReference: '+m.site.coordinates.join(', ')+' | '+m.site.radiusKm+' km | '+m.site.category+'\nClaim: count >= '+m.site.threshold+'\nCandidate probability: '+m.site.probability+' | persistence probability: '+m.persistenceProbability+' (baseline count '+m.baseline.count+')\nTarget UTC dates: '+m.windows.target.start+' through '+m.windows.target.end+'\nCapture allowed: '+m.windows.target.asOf+' through '+m.windows.target.captureDeadline+'\n'+(anchorMatched?'Supplied digest matched. ':'No separately supplied digest checked. ')+'Chronology and source authenticity NOT verified.';$('trial-lock-result').hidden=false;buttons();}
 function showEvaluation(p,anchorMatched){result=p;const r=p.report;$('trial-eval-summary').textContent='Status: '+r.status+'\nOutcome capture: '+r.outcome.capturedAt+'\nReturned matching count: '+(r.outcome.count??'Unavailable')+'\n'+(r.status==='WITHHELD'?'No score: '+r.withheldReason:'Observed binary: '+r.observedBinary+'\nCandidate Brier: '+r.candidateBrier.toFixed(6)+'\nPersistence Brier: '+r.persistenceBrier.toFixed(6)+'\nDifference (candidate minus persistence): '+r.lossDifference.toFixed(6))+'\n'+(anchorMatched?'Supplied digest matched. ':'No separately supplied digest checked in this session. ')+'Declared chronology only; no inference of predictive skill.';$('trial-eval-result').hidden=false;buttons();}
 async function read(id,max){const f=$(id).files[0];ok(f&&f.size>0&&f.size<=max,'Select an evidence JSON file within size limit');return new Uint8Array(await f.arrayBuffer());}
 function exportFile(p,name){const bytes=enc(p);ok(bytes.length<=MAX_PACKET,'Packet too large');download(bytes,name);}
 async function run(work,apply,{keep=false}={}){if(busy)return;if(!keep)reset('Checking trial evidence...');else {clearResult();$('trial-status').textContent='Checking outcome evidence...';}const token=++rev;busy=true;buttons();try{const v=await work();if(token===rev){apply(v);$('trial-status').textContent='Evidence replay accepted. Declared timing only.';}}catch(e){if(token===rev)$('trial-status').textContent='Not accepted: '+String(e.message).slice(0,180);}finally{busy=false;buttons();}}
 $('trial-freeze').addEventListener('click',()=>run(async()=>{const site=input(),window=trialWindows(clock()).baseline,v=await load(studyInput(site,window));return freezeTrial(site,v.bytes,clock());},v=>install(v)));
 $('trial-open').addEventListener('click',()=>run(async()=>verifyLock(strictJSON(await read('trial-lock-file',MAX_PACKET)),$('trial-anchor').value.trim()),v=>install(v.lock,v.anchorMatched)));
 $('trial-evaluate-file').addEventListener('click',()=>{const v=current;if(v)return run(async()=>makeEvaluationPacket(v,await read('trial-outcome-file',MAX_PAIR),{now:clock(),anchor:$('trial-anchor').value.trim()}),p=>showEvaluation(p,!!$('trial-anchor').value.trim()),{keep:true});});
 $('trial-fetch-outcome').addEventListener('click',()=>{const v=current;if(v)return run(async()=>{const m=v.manifest,now=clock();await verifyLock(v,$('trial-anchor').value.trim());ok(now>=time(m.windows.target.asOf)&&now<=time(m.windows.target.captureDeadline),'Live capture outside locked outcome period');const o=await load(studyInput(m.site,m.windows.target));return makeEvaluationPacket(v,o.bytes,{now:clock(),anchor:$('trial-anchor').value.trim()});},p=>showEvaluation(p,!!$('trial-anchor').value.trim()),{keep:true});});
 $('trial-reopen-eval').addEventListener('click',()=>run(async()=>verifyEvaluationPacket(strictJSON(await read('trial-eval-file',MAX_PACKET)),$('trial-anchor').value.trim()),v=>{install(v.packet.lock,v.anchorMatched);showEvaluation(v.packet,v.anchorMatched);}));
 $('trial-export-lock').addEventListener('click',()=>{if(current)try{exportFile(current,'gaia-trial-'+current.manifestSha256.slice(0,12)+'.json');}catch(e){$('trial-status').textContent=String(e.message);}});
 $('trial-export-eval').addEventListener('click',()=>{if(result)try{exportFile(result,'gaia-trial-result-'+result.report.manifestSha256.slice(0,12)+'.json');}catch(e){$('trial-status').textContent=String(e.message);}});
 for(const id of ['trial-category','trial-lon','trial-lat','trial-radius','trial-threshold','trial-probability','trial-lock-file','trial-anchor','trial-eval-file'])$(id).addEventListener('input',()=>reset('Input changed. Create a new lock or reopen the original.'));
 $('trial-outcome-file').addEventListener('input',()=>{rev++;clearResult();$('trial-status').textContent='Outcome changed. Evaluate again.';});
 reset('Set a trial or reopen a previously exported lock. No data requested.');return {getLock:()=>current,getEvaluation:()=>result};
}
if(typeof document!=='undefined'&&document.getElementById('trial-freeze'))startDiscovery();
