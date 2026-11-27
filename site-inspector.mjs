import {inspectBundle,strictJSON,sha,MAX_BUNDLE} from './facility.mjs';
import {buildSiteBriefing,LAYERS,LABELS,PACKET_LIMIT} from './site-briefing.mjs';
import {compareSiteChange} from './site-change.mjs';
import {verifyPacket as verifySeismicPacket} from './seismic.mjs';
export const MAX_PACKET_BYTES=36_000_000;
const ok=(v,m)=>{if(!v)throw Error(m);};
const hex=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const keys=(x,ks)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===ks.length&&ks.every(k=>Object.hasOwn(x,k));
const equal=(a,b)=>a===b||(Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>equal(v,b[i])))||(a&&b&&typeof a==='object'&&typeof b==='object'&&!Array.isArray(a)&&!Array.isArray(b)&&keys(b,Object.keys(a))&&Object.keys(a).every(k=>equal(a[k],b[k])));
function timestamp(s){const n=Date.parse(s);ok(typeof s==='string'&&Number.isFinite(n)&&new Date(n).toISOString()===s,'Invalid declared request timestamp');return n;}
function decode(e){ok(Number.isSafeInteger(e.bytes)&&e.bytes>0&&e.bytes<=MAX_BUNDLE&&typeof e.base64==='string'&&e.base64.length===4*Math.ceil(e.bytes/3),'Invalid evidence length');const raw=atob(e.base64);ok(raw.length===e.bytes&&btoa(raw)===e.base64,'Invalid evidence encoding');return Uint8Array.from(raw,c=>c.charCodeAt(0));}
export async function inspectPacket(bytes,anchor=''){
 ok(bytes instanceof Uint8Array&&bytes.length>0&&bytes.length<=MAX_PACKET_BYTES,'Choose a supported JSON packet up to 36 MB');
 ok(anchor===''||hex(anchor),'Expected a lowercase SHA-256 digest');const packetSha256=await sha(bytes);ok(!anchor||anchor===packetSha256,'Packet digest mismatch');
 const p=strictJSON(bytes),change=p?.schema==='gaia-site-change-packet-v1';
 if(p?.schema==='gaia-seismic-packet-v1'){ok(keys(p,['schema','receipt','report']),'Invalid seismic packet fields');const finding=await verifySeismicPacket(p);return {schema:'gaia-packet-inspection-v1',packetSha256,anchorChecked:!!anchor,sourceAuthenticated:false,packetType:'seismic',outcome:'ALL_LAYERS_REPLAY_MATCH',layers:[{category:'earthquakes',outcome:'REPLAY_MATCH',finding}],limitations:'Same-method offline seismic screening replay. Catalog completeness, source authenticity and real-world shaking or safety are not verified.'};}
 ok(keys(p,['schema','report','evidence'])&&(change||p.schema==='gaia-site-briefing-packet-v1'),'Unsupported packet schema');
 const r=p.report,now=timestamp(r?.requestedAt);
 ok(r.schema===(change?'gaia-site-change-v1':'gaia-site-briefing-v1')&&Array.isArray(r.layers)&&r.layers.length===3&&r.layers.every((v,i)=>v?.category===LAYERS[i]),'Invalid report layers');
 ok(Array.isArray(p.evidence)&&p.evidence.length>0&&p.evidence.length<=(change?6:3),'Invalid evidence count');
 let total=0;const indexed=new Map();
 for(const e of p.evidence){
  ok(keys(e,change?['category','window','sha256','bytes','base64']:['category','sha256','bytes','base64'])&&LAYERS.includes(e.category)&&(!change||['earlier','recent'].includes(e.window))&&hex(e.sha256),'Invalid evidence entry');
  const key=(change?e.window:'recent')+':'+e.category;ok(!indexed.has(key),'Duplicate evidence entry');
  ok(Number.isSafeInteger(e.bytes)&&e.bytes>0&&(total+=e.bytes)<=PACKET_LIMIT,'Combined evidence limit exceeded');
  const raw=decode(e),model=await inspectBundle(raw,e.sha256);indexed.set(key,{bytes:raw,model});
 }
 if(change)for(const category of LAYERS)ok(indexed.has('earlier:'+category)===indexed.has('recent:'+category),'Unpaired change evidence');
 const load=window=>async x=>{const v=indexed.get(window+':'+x.category);if(!v)throw Error('Evidence not retained');return v;};
 const recent=await buildSiteBriefing(r.site,change?r.windows?.current:r.window,load('recent'),now);
 const actual=change?await compareSiteChange(recent,load('earlier'),now):recent;
 const {layers:declared,...declaredHeader}=r,{layers:replayed,...replayedHeader}=actual.report;
 ok(equal(declaredHeader,replayedHeader)&&actual.bundles.length===indexed.size,'Report header, source count or window does not replay');
 const layers=LAYERS.map((category,i)=>{
  const d=declared[i],a=replayed[i];
  if(indexed.has('recent:'+category)){ok(equal(d,a),'Finding does not replay: '+category);return {category,outcome:'REPLAY_MATCH',finding:a};}
  // The historical retrieval failure itself cannot be reproduced from absent evidence.
  if(change)ok(keys(d,['category','status','reason','previousCount','currentCount','onlyCurrent','onlyPrevious','sharedCount'])&&['PAIR_UNAVAILABLE','REPLAY_REJECTED'].includes(d.status)&&typeof d.reason==='string'&&d.reason.length<=180&&['previousCount','currentCount','onlyCurrent','onlyPrevious','sharedCount'].every(k=>d[k]===null),'Unsupported change claim without evidence');
  else ok(keys(d,['category','status','matchingEvents','nearest','coverage','error'])&&d.status==='SOURCE_UNAVAILABLE'&&d.matchingEvents===null&&d.nearest===null&&d.coverage===null&&typeof d.error==='string'&&d.error.length<=180,'Unsupported observation claim without evidence');
  return {category,outcome:'NOT_REPLAYABLE_NO_EVIDENCE',finding:null};
 });
 return {schema:'gaia-packet-inspection-v1',packetSha256,anchorChecked:!!anchor,sourceAuthenticated:false,packetType:change?'change':'briefing',outcome:layers.every(x=>x.outcome==='REPLAY_MATCH')?'ALL_LAYERS_REPLAY_MATCH':'PARTIAL_REPLAY_MATCH',layers,limitations:'Same-method offline replay from included bytes. A matching digest without a trusted external anchor does not authenticate origin; source completeness, retrieval time and real-world conclusions are not verified. Missing evidence cannot prove the claimed failure.'};
}
export function startInspector(doc=document,{inspect=inspectPacket,download}={}){
 const $=id=>doc.getElementById(id),node=(tag,t)=>{const n=doc.createElement(tag);n.textContent=t;return n;};let revision=0,busy=false,result=null;
 const save=download||((data,name)=>{const url=URL.createObjectURL(new Blob([data],{type:'application/json'})),a=doc.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 function clear(message){revision++;result=null;$('inspect-result').hidden=true;$('inspect-rows').replaceChildren();$('inspect-export').disabled=true;$('inspect-status').textContent=message;$('inspect-run').disabled=busy;}
 async function run(){if(busy)return;clear('Checking packet bytes and recomputing findings locally...');const token=revision;busy=true;$('inspect-run').disabled=true;
  try{const f=$('inspect-file').files[0];ok(f&&f.size>0&&f.size<=MAX_PACKET_BYTES,'Select a JSON packet up to 36 MB');const out=await inspect(new Uint8Array(await f.arrayBuffer()),$('inspect-anchor').value.trim());if(token!==revision)return;
   result=out;$('inspect-status').textContent=out.outcome==='ALL_LAYERS_REPLAY_MATCH'?'All included findings replayed.':'Included findings replayed; missing layers could not be verified.';$('inspect-digest').textContent=out.packetSha256;$('inspect-anchor-result').textContent=out.anchorChecked?'Supplied digest matched.':'No external digest supplied.';
   for(const row of out.layers){const tr=doc.createElement('tr');const h=node('th',LABELS[row.category]||'Earthquakes');h.scope='row';tr.append(h,node('td',row.outcome==='REPLAY_MATCH'?'Replayed':'No evidence to replay'),node('td',row.finding?JSON.stringify(row.finding,null,2):'No finding verified'));$('inspect-rows').append(tr);}$('inspect-result').hidden=false;$('inspect-export').disabled=false;
  }catch(e){if(token===revision)clear('Packet not accepted: '+String(e.message).slice(0,180));}finally{busy=false;$('inspect-run').disabled=false;}}
 $('inspect-run').addEventListener('click',run);for(const id of ['inspect-file','inspect-anchor'])$(id).addEventListener('input',()=>clear('Input changed. Inspect again.'));
 $('inspect-export').addEventListener('click',()=>{if(result)save(JSON.stringify(result,null,2),'gaia-inspection-'+result.packetSha256.slice(0,12)+'.json');});clear('Select a site briefing, change or seismic evidence packet.');return {run};
}
if(typeof document!=='undefined'&&document.getElementById('inspect-run'))startInspector();
