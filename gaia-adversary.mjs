import {inspectBundle,strictJSON,sha,MAX_BUNDLE} from './facility.mjs';
import {screen} from './earth.mjs';
import {makeProof,verifyProof,MAX_PACKET} from './gaia-proof.mjs';
const ok=(v,m)=>{if(!v)throw Error(m);};
const enc=x=>new TextEncoder().encode(JSON.stringify(x));
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const LIMIT='Replay checks consistency, not truth. A matching separately supplied digest binds bytes only; its provenance and authority must be established independently. A source digest does not bind a chosen claim, site, parameters or report. No source authentication, completeness, hazard or safety determination.';
export async function assessProof(bytes,{sourceAnchor='',packetAnchor=''}={}){
 ok(bytes instanceof Uint8Array&&bytes.length>0&&bytes.length<=MAX_PACKET,'Invalid proof size');
 ok((sourceAnchor===''||hex(sourceAnchor))&&(packetAnchor===''||hex(packetAnchor)),'Expected lowercase SHA-256 digests');
 let v;try{v=await verifyProof(bytes);}catch{return {replay:'REJECT',sourceBinding:'NOT_CHECKED',packetBinding:'NOT_CHECKED',sourceAuthenticated:false,verdict:'REPLAY_REJECTED',limitations:LIMIT};}
 const r=v.packet.report,source=r.source.sourceSha256,packet=v.packetSha256;
 const binding=(a,d)=>!a?'NOT_SUPPLIED':a===d?'MATCH':'MISMATCH';
 const s=binding(sourceAnchor,source),p=binding(packetAnchor,packet);
 return {replay:'ACCEPT',sourceBinding:s,packetBinding:p,sourceAuthenticated:false,verdict:s==='MISMATCH'||p==='MISMATCH'?'ANCHOR_MISMATCH':p==='MATCH'?'PACKET_DIGEST_MATCH':s==='MATCH'?'SOURCE_DIGEST_MATCH_ONLY':'UNANCHORED_REPLAY_ONLY',sourceSha256:source,packetSha256:packet,claim:r.claim,limitations:LIMIT};
}
function decode(s){const raw=atob(s);return Uint8Array.from(raw,c=>c.charCodeAt(0));}
function base64(bytes){let s='';for(let i=0;i<bytes.length;i+=16384)s+=String.fromCharCode(...bytes.subarray(i,i+16384));return btoa(s);}
async function component(x){const b=enc(x);return {sha256:await sha(b),bytes:b.length,base64:base64(b)};}
// Deliberately restricted to the explicitly fictional, offline demo. Never modify a live or user-imported source.
async function fictionalAlternative(original,mutate){
 const model=await inspectBundle(original);ok(model.kind==='synthetic-demo'&&model.mode==='offline-import','Fictional offline evidence only');
 const bundle=strictJSON(original),archive=strictJSON(decode(bundle.files.archive.base64)),config=strictJSON(decode(bundle.files.configuration.base64)),report=strictJSON(decode(bundle.files.report.base64));
 const source=structuredClone(model.snapshot);mutate(source.events);const bytes=enc(source),digest=await sha(bytes);
 const results=config.facilities.slice().sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0).map(f=>({facilityId:f.id,...screen(source,{facility:f.coordinates,asOf:config.asOf,hours:config.hours,radiusKm:config.radiusKm})}));const c=results[0].coverage;
 Object.assign(archive.receipt,{sourceSha256:digest,sourceBytes:bytes.length,eventCount:c.events,pointCount:c.eligiblePoints+c.outsideWindow,nonPointCount:c.unsupportedGeometries,eventsWithoutGeometry:c.eventsWithoutGeometry});archive.bodyBase64=base64(bytes);
 report.snapshot.sha256=digest;report.snapshot.bytes=bytes.length;report.results=results;
 bundle.files.archive=await component(archive);bundle.files.report=await component(report);const out=enc(bundle);await inspectBundle(out);return out;
}
export async function runFictionalChallenge(original){
 ok(original instanceof Uint8Array&&original.length<=MAX_BUNDLE,'Invalid demonstration');ok(await sha(original)==='f616c0b715bf43775a062b591dbd8cb76fe97a6575e258352c8be11ce2bb5bd0','Only the pinned fictional demonstration can be changed');const m=await inspectBundle(original);ok(m.kind==='synthetic-demo'&&m.mode==='offline-import'&&m.results.length===1&&m.snapshot.events.length===6,'Expected six fictional demo events');
 const parameters={facilityId:m.results[0].facilityId,siteToleranceKm:10,radiusToleranceKm:5,threshold:2,deletionBudget:1};
 const base=await makeProof(original,parameters),baseline=enc(base),anchor={sourceAnchor:m.sourceHash,packetAnchor:await sha(baseline)};
 const cases=[];async function add(name,bytes){const v=await assessProof(bytes,anchor);cases.push({name,...v});}
 await add('original',baseline);
 const bad=structuredClone(base);bad.report.claim.nominalCount++;await add('report-only',enc(bad));
 const variants=[['source-record-added',es=>{const e=structuredClone(es[0]);e.id='DEMO-EXTRA';e.title='Fictional extra event';es.push(e);}],['source-record-removed',es=>es.shift()],['source-coordinate-changed',es=>{es[0].geometry[0].coordinates=[150,0];}]];
 for(const [name,mutate] of variants)await add(name,enc(await makeProof(await fictionalAlternative(original,mutate),parameters)));
 await add('same-source-new-threshold',enc(await makeProof(original,{...parameters,threshold:3})));
 return {schema:'gaia-adversary-demo-v1',fictional:true,baselineSourceSha256:anchor.sourceAnchor,baselinePacketSha256:anchor.packetAnchor,cases,limitations:LIMIT};
}
async function readDemo(r){ok(r.ok&&r.body,'Demo unavailable');const reader=r.body.getReader(),chunks=[];let n=0;try{while(true){const {done,value}=await reader.read();if(done)break;n+=value.length;ok(n<=MAX_BUNDLE,'Demo size limit');chunks.push(value);}}finally{try{await reader.cancel();}catch{}}const bytes=new Uint8Array(n);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}return bytes;}
export function startAdversary(doc=document,{demo=()=>fetch('data/boundary-demo.json',{cache:'no-store',signal:AbortSignal.timeout(10000)})}={}){
 const $=id=>doc.getElementById(id),node=(tag,s)=>{const e=doc.createElement(tag);e.textContent=String(s);return e;};let revision=0,busy=false;
 function clear(message){revision++;$('adversary-rows').replaceChildren();$('adversary-status').textContent=message;$('adversary-result').hidden=true;}
 function show(rows){for(const r of rows){const tr=doc.createElement('tr');for(const value of [r.name,r.replay,r.sourceBinding,r.packetBinding,r.claim?.nominalCount??'Not reported',r.verdict,r.sourceSha256?'Source: '+r.sourceSha256+' | Packet: '+r.packetSha256:'Not available'])tr.append(node('td',value));$('adversary-rows').append(tr);}$('adversary-result').hidden=false;}
 async function run(work,message){if(busy)return;clear('Verifying evidence...');const token=revision;busy=true;$('adversary-run').disabled=true;$('adversary-demo').disabled=true;try{const rows=await work();if(token===revision){show(rows);$('adversary-status').textContent=message;}}catch(e){if(token===revision)clear('Not accepted: '+String(e.message).slice(0,150));}finally{busy=false;$('adversary-run').disabled=false;$('adversary-demo').disabled=false;}}
 $('adversary-run').addEventListener('click',()=>run(async()=>{const f=$('adversary-file').files[0];ok(f&&f.size>0&&f.size<=MAX_PACKET,'Choose a proof packet up to 40 MB');return [{name:'Imported proof',...await assessProof(new Uint8Array(await f.arrayBuffer()),{sourceAnchor:$('adversary-source').value.trim(),packetAnchor:$('adversary-packet').value.trim()})}];},'Local replay and supplied digest checks complete. Authenticity is not established.'));
 $('adversary-demo').addEventListener('click',()=>run(async()=>{return (await runFictionalChallenge(await readDemo(await demo()))).cases;},'FICTIONAL demonstration: baseline digests simulate separately retained anchors.'));
 for(const id of ['adversary-file','adversary-source','adversary-packet'])$(id).addEventListener('input',()=>clear('Input changed. Run verification again.'));
 clear('Import a proof packet or run the fictional challenge. No evidence is uploaded.');$('adversary-run').disabled=false;$('adversary-demo').disabled=false;
}
if(typeof document!=='undefined'&&document.getElementById('adversary-run'))startAdversary();
