import {strictJSON,sha} from './facility.mjs';
import {verifyLock,verifyEvaluationPacket,MAX_PACKET} from './discovery-lab.mjs';
export const MAX_ARTIFACT_BYTES=24_000_000,MAX_LEDGER_BYTES=34_000_000,MAX_ENTRIES=100;
const ZERO='0'.repeat(64),SCHEMA='gaia-research-memory-v1';
const LIMIT='Local append-only workflow, not immutable storage or a trusted timestamp. A separately retained head checks consistency only. All prediction and capture times are declared, source authenticity and independence are unverified. Scores are descriptive of retained trials; missing, withheld, duplicate and shared evidence must not establish predictive skill.';
const ok=(v,m)=>{if(!v)throw Error(m);};
const hex=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const keys=(x,k)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===k.length&&k.every(y=>Object.hasOwn(x,y));
const enc=x=>new TextEncoder().encode(JSON.stringify(x));
const hash=x=>sha(enc(x));
function b64(b){let s='';for(let i=0;i<b.length;i+=16384)s+=String.fromCharCode(...b.subarray(i,i+16384));return btoa(s);}
export function emptyLedger(){return {schema:SCHEMA,head:ZERO,entries:[]};}
async function decode(e){ok(Number.isSafeInteger(e.bytes)&&e.bytes>0&&e.bytes<=MAX_ARTIFACT_BYTES&&hex(e.artifactSha256)&&typeof e.base64==='string'&&e.base64.length===4*Math.ceil(e.bytes/3),'Invalid artifact envelope');const raw=atob(e.base64);ok(raw.length===e.bytes&&btoa(raw)===e.base64,'Invalid artifact encoding');const b=Uint8Array.from(raw,c=>c.charCodeAt(0));ok(await sha(b)===e.artifactSha256,'Artifact digest mismatch');return b;}
function body(e){return {seq:e.seq,previous:e.previous,kind:e.kind,trialId:e.trialId,artifactSha256:e.artifactSha256,bytes:e.bytes};}
function scope(m){const s=m.site,w=m.windows.target;return JSON.stringify([s.category,s.coordinates,s.radiusKm,s.threshold,w.start,w.end]);}
async function apply(bytes,state){
 const p=strictJSON(bytes);
 if(p?.schema==='gaia-discovery-lock-packet-v1'){
  const v=await verifyLock(p),m=v.lock.manifest,id=v.lock.manifestSha256,k=scope(m);
  ok(!state.trials.has(id),'Duplicate trial lock');ok(!state.scopes.has(k),'Trial claim and target window already registered');
  state.scopes.add(k);state.trials.set(id,{id,manifest:m,baselineHash:m.baseline.sourceSha256,lockArtifactSha256:await sha(bytes),evaluation:null});return {kind:'LOCK',trialId:id};
 }
 if(p?.schema==='gaia-discovery-evaluation-packet-v1'){
  const v=await verifyEvaluationPacket(p),id=p.lock.manifestSha256,t=state.trials.get(id);
  ok(t,'Register the original trial lock first');ok(!t.evaluation,'Trial already has a retained evaluation');
  t.evaluation=v.report;t.outcomeArtifactSha256=await sha(bytes);return {kind:'EVALUATION',trialId:id};
 }
 throw Error('Unsupported trial artifact');
}
function summarize(state,head,anchorChecked){
 const trials=[...state.trials.values()],scored=trials.filter(t=>t.evaluation?.status==='SCORED_RETAINED_RECORDS'),withheld=trials.filter(t=>t.evaluation?.status==='WITHHELD');
 const mean=k=>scored.length?scored.reduce((a,t)=>a+t.evaluation[k],0)/scored.length:null;
 const uses=new Map(),edges=[];function link(t,role,digest){if(!uses.has(digest))uses.set(digest,new Set());uses.get(digest).add(t.id);edges.push({from:'trial:'+t.id,to:'source:'+digest,type:role});}
 for(const t of trials){link(t,'BASELINE_DERIVED_FROM',t.baselineHash);edges.push({from:'trial:'+t.id,to:'artifact:'+t.lockArtifactSha256,type:'LOCKED_BY'});if(t.evaluation){link(t,'OUTCOME_DERIVED_FROM',t.evaluation.outcome.sourceSha256);edges.push({from:'trial:'+t.id,to:'artifact:'+t.outcomeArtifactSha256,type:'EVALUATED_BY'});}}
 let overlappingPairs=0;for(let i=0;i<trials.length;i++)for(let j=i+1;j<trials.length;j++){const a=trials[i].manifest,b=trials[j].manifest;if(a.site.category===b.site.category&&a.windows.target.start<=b.windows.target.end&&b.windows.target.start<=a.windows.target.end)overlappingPairs++;}
 return {schema:'gaia-research-summary-v1',head,anchorChecked,chronology:'DECLARED_CLOCK_ONLY',sourceAuthenticated:false,registered:trials.length,scored:scored.length,withheld:withheld.length,pending:trials.length-scored.length-withheld.length,better:scored.filter(t=>t.evaluation.lossDifference<0).length,worse:scored.filter(t=>t.evaluation.lossDifference>0).length,tied:scored.filter(t=>t.evaluation.lossDifference===0).length,meanCandidateBrier:mean('candidateBrier'),meanPersistenceBrier:mean('persistenceBrier'),meanPairedDifference:mean('lossDifference'),sharedSourceDigests:[...uses].filter(([,ids])=>ids.size>1).map(([digest,ids])=>({digest,trialIds:[...ids]})),sameCategoryOverlappingTargetPairs:overlappingPairs,graph:{trials:trials.map(t=>({id:t.id,site:t.manifest.site,window:t.manifest.windows.target,issuedAt:t.manifest.issuedAt,baselineSource:t.baselineHash,status:t.evaluation?.status??'PENDING',outcome:t.evaluation??null})),edges},limitations:LIMIT};
}
export async function verifyLedger(ledger,anchor=''){
 ok(keys(ledger,['schema','head','entries'])&&ledger.schema===SCHEMA&&hex(ledger.head)&&Array.isArray(ledger.entries)&&ledger.entries.length<=MAX_ENTRIES,'Invalid research ledger');ok(anchor===''||hex(anchor),'Expected a lowercase SHA-256 head');
 let prev=ZERO,total=0;const state={trials:new Map(),scopes:new Set()};
 for(let i=0;i<ledger.entries.length;i++){
  const e=ledger.entries[i];ok(keys(e,['seq','previous','kind','trialId','artifactSha256','bytes','base64','entryHash'])&&e.seq===i+1&&e.previous===prev&&hex(e.entryHash)&&hex(e.trialId)&&['LOCK','EVALUATION'].includes(e.kind),'Broken entry sequence or chain');
  ok(Number.isSafeInteger(e.bytes)&&e.bytes>0&&(total+=e.bytes)<=MAX_ARTIFACT_BYTES,'Combined evidence limit');const bytes=await decode(e);ok(await hash(body(e))===e.entryHash,'Entry hash mismatch');
  const actual=await apply(bytes,state);ok(actual.kind===e.kind&&actual.trialId===e.trialId,'Artifact does not match ledger entry');prev=e.entryHash;
 }
 ok(prev===ledger.head,'Ledger head mismatch');ok(!anchor||anchor===prev,'Separately retained head mismatch');return summarize(state,prev,!!anchor);
}
export async function appendArtifact(ledger,bytes){
 await verifyLedger(ledger);ok(bytes instanceof Uint8Array&&bytes.length>0&&bytes.length<=MAX_PACKET&&bytes.length<=MAX_ARTIFACT_BYTES,'Artifact size limit');ok(ledger.entries.length<MAX_ENTRIES&&ledger.entries.reduce((n,e)=>n+e.bytes,bytes.length)<=MAX_ARTIFACT_BYTES,'Registry capacity reached');
 const p=strictJSON(bytes),kind=p?.schema==='gaia-discovery-lock-packet-v1'?'LOCK':p?.schema==='gaia-discovery-evaluation-packet-v1'?'EVALUATION':null;ok(kind,'Unsupported trial artifact');
 const trialId=kind==='LOCK'?p.manifestSha256:p.lock?.manifestSha256;ok(hex(trialId),'Invalid trial ID');
 const e={seq:ledger.entries.length+1,previous:ledger.head,kind,trialId,artifactSha256:await sha(bytes),bytes:bytes.length,base64:b64(bytes)};e.entryHash=await hash(body(e));
 const next={schema:SCHEMA,head:e.entryHash,entries:[...ledger.entries,e]};await verifyLedger(next);ok(enc(next).length<=MAX_LEDGER_BYTES,'Registry export size limit');return next;
}
export function extendsLedger(current,incoming){return current.entries.length<=incoming.entries.length&&(current.entries.length===0||incoming.entries[current.entries.length-1]?.entryHash===current.head);}
export function startMemory(doc=document,{save}={}){
 const $=id=>doc.getElementById(id),node=(tag,s)=>{const e=doc.createElement(tag);e.textContent=String(s);return e;};let ledger=emptyLedger(),summary=null,busy=false,rev=0;
 const download=save||((bytes,name)=>{const url=URL.createObjectURL(new Blob([bytes],{type:'application/json'})),a=doc.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 function buttons(){for(const id of ['memory-open','memory-append'])$(id).disabled=busy;for(const id of ['memory-export','memory-summary'])$(id).disabled=busy||!summary;}
 function show(s){summary=s;$('memory-head').textContent=s.head;$('memory-counts').textContent=s.registered+' registered | '+s.scored+' scored | '+s.withheld+' withheld | '+s.pending+' pending';$('memory-loss').textContent=s.scored?'Mean Brier candidate '+s.meanCandidateBrier.toFixed(6)+' | persistence '+s.meanPersistenceBrier.toFixed(6)+' | paired difference '+s.meanPairedDifference.toFixed(6)+' | better/worse/tied '+[s.better,s.worse,s.tied].join('/'):'No scored trials';$('memory-dependency').textContent=s.sharedSourceDigests.length+' shared source digest(s); '+s.sameCategoryOverlappingTargetPairs+' same-category overlapping target pair(s). Independence not established.';$('memory-rows').replaceChildren();for(const t of s.graph.trials){const tr=doc.createElement('tr');tr.append(node('td',t.id),node('td',t.site.category+' | '+t.site.coordinates.join(', ')+' | '+t.site.radiusKm+' km'),node('td',t.window.start+' through '+t.window.end),node('td',t.status),node('td',t.outcome?.lossDifference??'Not scored'));$('memory-rows').append(tr);}$('memory-result').hidden=false;buttons();}
 async function read(id,max){const f=$(id).files[0];ok(f&&f.size>0&&f.size<=max,'Choose an evidence file within the size limit');return new Uint8Array(await f.arrayBuffer());}
 async function run(work){if(busy)return;const token=++rev;busy=true;buttons();$('memory-status').textContent='Replaying evidence...';try{const v=await work();if(token!==rev)return;ledger=v.ledger;show(v.summary);$('memory-status').textContent='Registry accepted. '+(v.summary.anchorChecked?'Separately supplied head matched. ':'No separately supplied head checked for this version. ')+'Export the registry to retain it; no trusted timestamp.';}catch(e){if(token===rev)$('memory-status').textContent='Not accepted; previous registry unchanged: '+String(e.message).slice(0,160);}finally{busy=false;buttons();}}
 $('memory-open').addEventListener('click',()=>run(async()=>{const incoming=strictJSON(await read('memory-file',MAX_LEDGER_BYTES)),s=await verifyLedger(incoming,$('memory-anchor').value.trim());ok(extendsLedger(ledger,incoming),'Imported history diverges or truncates the current registry');return {ledger:incoming,summary:s};}));
 $('memory-append').addEventListener('click',()=>run(async()=>{const next=await appendArtifact(ledger,await read('memory-artifact',MAX_ARTIFACT_BYTES));return {ledger:next,summary:await verifyLedger(next)};}));
 for(const id of ['memory-file','memory-anchor','memory-artifact'])$(id).addEventListener('input',()=>{rev++;$('memory-status').textContent='Input changed. Previously accepted registry remains unchanged.';});
 $('memory-export').addEventListener('click',()=>{if(summary&&!busy)download(enc(ledger),'gaia-research-memory-'+ledger.head.slice(0,12)+'.json');});$('memory-summary').addEventListener('click',()=>{if(summary&&!busy)download(enc(summary),'gaia-research-summary-'+ledger.head.slice(0,12)+'.json');});
 $('memory-result').hidden=true;$('memory-status').textContent='Empty registry. Reopen a saved registry or append a Discovery lock. Nothing is uploaded or automatically saved.';buttons();return {getLedger:()=>ledger};
}
if(typeof document!=='undefined'&&document.getElementById('memory-open'))startMemory();
