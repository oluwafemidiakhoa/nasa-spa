import {screen, MAX_BYTES} from './earth.mjs';
export const MAX_BUNDLE=26_000_000;
const LIMITS={archive:3_000_000,configuration:32768,report:16_000_000};
const METHODS={'earth.mjs':'a1ce541de7aa9d49e934fa8c642782741828aad3c8893bb2e29b9465b14df0bc','scripts/earth-batch.mjs':'6b0b64c3f384a3d40d77afbb1cf5744cdac75307535f886a730762e3b28061ba','scripts/eonet_archive.py':'24010b808d080126964c809a37a1a354037340f3a990108b0096fb74831c007b','scripts/verify_earth_batch.py':'693f59bd3351e1544a58c624148cc77ea92e08990d7cf12153c56be0f6ac9ed4'};
const fail=m=>{throw Error(m);};
const req=(ok,m)=>{if(!ok)fail(m);};
const keys=(o,k)=>o!==null&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).length===k.length&&k.every(x=>Object.hasOwn(o,x));
const hex=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const utc=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(s)&&Number.isFinite(Date.parse(s))&&new Date(s).toISOString()===(s.length===20?s.slice(0,-1)+'.000Z':s);
const day=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&utc(s+'T00:00:00Z');
const point=p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=180&&Math.abs(p[1])<=90;
const same=(a,b)=>a===b||(Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>same(v,b[i])))||(a!==null&&b!==null&&typeof a==='object'&&typeof b==='object'&&!Array.isArray(a)&&!Array.isArray(b)&&keys(b,Object.keys(a))&&Object.keys(a).every(k=>same(a[k],b[k])));
export async function sha(bytes){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');}
// Native JSON parser handles grammar; the bounded scanner rejects duplicate decoded keys and deep nesting.
export function strictJSON(bytes){
  const s=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes); let i=0;
  const ws=()=>{while(i<s.length&&' \r\n\t'.includes(s[i]))i++;};
  function str(){const start=i++;while(i<s.length){const c=s[i++];if(c==='\\'){i++;continue;}if(c==='"')return s.slice(start,i);}fail('Unterminated JSON string');}
  function value(depth){req(depth<=64,'JSON nesting limit');ws();const c=s[i];
    if(c==='{'){i++;ws();const seen=new Set();if(s[i]==='}'){i++;return;}while(true){ws();req(s[i]==='"','Expected JSON key');const k=JSON.parse(str());req(!seen.has(k),'Duplicate JSON key');seen.add(k);ws();req(s[i++]===':','Expected colon');value(depth+1);ws();const t=s[i++];if(t==='}')return;req(t===',','Expected comma');}}
    else if(c==='['){i++;ws();if(s[i]===']'){i++;return;}while(true){value(depth+1);ws();const t=s[i++];if(t===']')return;req(t===',','Expected comma');}}
    else if(c==='"')str();else{const start=i;while(i<s.length&&!(' \r\n\t,]}'.includes(s[i])))i++;req(i>start,'Missing JSON value');const n=JSON.parse(s.slice(start,i));req(typeof n!=='number'||Number.isFinite(n),'Nonfinite JSON number');}}
  value(0);ws();req(i===s.length,'Trailing JSON content');return JSON.parse(s);
}
function decode(s,max){req(typeof s==='string'&&s.length>0&&s.length<=4*Math.ceil(max/3),'Invalid base64 length');const raw=atob(s);req(raw.length>0&&raw.length<=max&&btoa(raw)===s,'Invalid base64 encoding');return Uint8Array.from(raw,c=>c.charCodeAt(0));}
async function component(o,max){req(keys(o,['sha256','bytes','base64'])&&hex(o.sha256)&&Number.isSafeInteger(o.bytes)&&o.bytes>0&&o.bytes<=max,'Invalid component');const raw=decode(o.base64,max);req(raw.length===o.bytes&&await sha(raw)===o.sha256,'Component digest mismatch');return raw;}
export async function inspectBundle(bytes,anchor=''){
  req(bytes instanceof Uint8Array&&bytes.length>0&&bytes.length<=MAX_BUNDLE,'Bundle size out of bounds');
  req(anchor===''||hex(anchor),'Expected lowercase SHA-256');const digest=await sha(bytes);req(!anchor||digest===anchor,'Bundle digest mismatch');
  const b=strictJSON(bytes);req(keys(b,['schema','methods','files'])&&b.schema==='gaia-earth-evidence-v0.5'&&same(b.methods,METHODS)&&keys(b.files,Object.keys(LIMITS)),'Unsupported bundle schema or method fingerprints');
  const a=strictJSON(await component(b.files.archive,LIMITS.archive)),c=strictJSON(await component(b.files.configuration,LIMITS.configuration)),r=strictJSON(await component(b.files.report,LIMITS.report));
  req(keys(a,['schema','receipt','bodyBase64'])&&a.schema==='gaia-eonet-archive-v0.4','Invalid archive schema');
  const receipt=a.receipt,src=decode(a.bodyBase64,MAX_BYTES),sourceHash=await sha(src),snapshot=strictJSON(src);
  req(keys(receipt,['mode','capturedAt','requestUrl','query','httpStatus','limitReached','coverage','sourceAuthenticated','sourceSha256','sourceBytes','eventCount','pointCount','nonPointCount','eventsWithoutGeometry'])&&receipt.sourceBytes===src.length&&receipt.sourceSha256===sourceHash&&receipt.sourceAuthenticated===false&&receipt.coverage==='unknown'&&['offline-import','https-eonet'].includes(receipt.mode)&&utc(receipt.capturedAt),'Archive receipt mismatch');
  if(receipt.mode==='offline-import')req([receipt.query,receipt.requestUrl,receipt.httpStatus,receipt.limitReached].every(v=>v===null),'Offline archive asserts retrieval');
  else{const q=receipt.query;req(keys(q,['status','start','end','category','limit'])&&q.status==='all'&&day(q.start)&&day(q.end)&&Date.parse(q.end)-Date.parse(q.start)>=0&&Date.parse(q.end)-Date.parse(q.start)<=30*86400000&&typeof q.category==='string'&&/^[A-Za-z][A-Za-z0-9]{0,39}$/.test(q.category)&&Number.isInteger(q.limit)&&q.limit>=1&&q.limit<=200&&receipt.httpStatus===200&&receipt.eventCount<=q.limit&&receipt.limitReached===(receipt.eventCount===q.limit),'Invalid acquisition claim');const params=new URLSearchParams([['status',q.status],['start',q.start],['end',q.end],['category',q.category],['limit',String(q.limit)]]);req(receipt.requestUrl==='https://eonet.gsfc.nasa.gov/api/v3/events?'+params,'Unexpected recorded request URL');}
  req(Array.isArray(snapshot?.events)&&snapshot.events.every(e=>Array.isArray(e?.geometry)&&e.geometry.every(g=>typeof g?.type==='string'&&g.type.length>0)),'Invalid archive geometry');
  req(keys(c,['snapshotKind','asOf','hours','radiusKm','facilities'])&&['synthetic-demo','user-import-unverified'].includes(c.snapshotKind)&&!(c.snapshotKind==='synthetic-demo'&&receipt.mode==='https-eonet')&&Array.isArray(c.facilities)&&c.facilities.length>=1&&c.facilities.length<=25,'Invalid configuration');
  const ids=new Set();for(const f of c.facilities){req(keys(f,['id','coordinates'])&&typeof f.id==='string'&&/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(f.id)&&!ids.has(f.id)&&point(f.coordinates),'Invalid facility');ids.add(f.id);}
  const results=[...c.facilities].sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0).map(f=>({facilityId:f.id,...screen(snapshot,{facility:f.coordinates,asOf:c.asOf,hours:c.hours,radiusKm:c.radiusKm})}));
  const cov=results[0].coverage;req(receipt.eventCount===cov.events&&receipt.pointCount===cov.eligiblePoints+cov.outsideWindow&&receipt.nonPointCount===cov.unsupportedGeometries&&receipt.eventsWithoutGeometry===cov.eventsWithoutGeometry,'Archive counts mismatch');
  const expected={schema:'gaia-earth-batch-v0.3',snapshot:{kind:c.snapshotKind,sha256:sourceHash,bytes:src.length,authenticity:'unverified'},configuration:{sha256:b.files.configuration.sha256,bytes:b.files.configuration.bytes},results};
  req(same(r,expected),'Browser replay mismatch');return {digest,anchorChecked:!!anchor,sourceHash,archiveHash:b.files.archive.sha256,kind:c.snapshotKind,capturedAt:receipt.capturedAt,mode:receipt.mode,results,snapshot};
}
const labels={POINTS_WITHIN_RADIUS:'Matching points',NO_MATCH_IN_AVAILABLE_POINTS:'No matching point',NO_ELIGIBLE_POINTS:'No eligible points'};
function start(){
  const $=id=>document.getElementById(id),status=$('status'),view=$('results'),select=$('facility'),table=$('matches'),file=$('bundle'),anchor=$('anchor');let rev=0,model=null,page=0;
  function clear(message){rev++;model=null;page=0;view.hidden=true;select.replaceChildren();table.replaceChildren();status.textContent=message;return rev;}
  function node(tag,text){const n=document.createElement(tag);n.textContent=text;return n;}
  function detail(){const r=model.results[Number(select.value)];if(!r)return;const p=r.parameters,c=r.coverage; $('selected').textContent=r.facilityId+' / '+labels[r.status];$('parameters').textContent=`${p.facility[1]}° latitude, ${p.facility[0]}° longitude | ${p.radiusKm} km | ${p.hours} h ending ${p.asOf}`;$('coverage').textContent=`${c.events} events; ${c.eligiblePoints} eligible points; ${c.unsupportedGeometries} excluded non-point geometries; ${c.outsideWindow} outside window; ${c.eventsWithoutGeometry} events without geometry.`;table.replaceChildren();for(const m of r.matches.slice(page*50,page*50+50)){const tr=document.createElement('tr');for(const t of [m.eventId,m.title,m.observedAt,m.coordinates.join(', '),m.distanceKm.toFixed(3)])tr.append(node('td',t));table.append(tr);}$('page').textContent=r.matches.length?`${page*50+1}–${Math.min(r.matches.length,page*50+50)} of ${r.matches.length} matching events`:'No matching events in available points.';$('prev').disabled=page===0;$('next').disabled=(page+1)*50>=r.matches.length;}
  function render(m){model=m;let n=m.results.filter(r=>r.status==='POINTS_WITHIN_RADIUS').length;$('source-kind').textContent=m.kind==='synthetic-demo'?'Synthetic demonstration — fictional events and facilities':'Imported observations — source authenticity unverified';$('total').textContent=m.results.length;$('matched').textContent=n;$('other').textContent=m.results.length-n;$('digest').textContent=m.digest;$('source-hash').textContent=m.sourceHash;$('archive-hash').textContent=m.archiveHash;$('capture').textContent=m.capturedAt+' (recorded, not authenticated)';$('mode').textContent=m.mode+' (declared)';$('anchor-state').textContent=m.anchorChecked?'Matches separately supplied digest':'Not checked against independent digest';for(const [i,r] of m.results.entries()){const opt=node('option',r.facilityId+' — '+labels[r.status]);opt.value=i;select.append(opt);}view.hidden=false;detail();status.textContent='Browser consistency and same-method replay matched. Independent Python replay not performed.';}
  async function load(get,expected){const run=clear('Checking bundle and replaying results…');try{const m=await inspectBundle(await get(),expected);if(run===rev)render(m);}catch(e){if(run===rev)clear('Bundle rejected: '+String(e.message).slice(0,180));}}
  $('import').addEventListener('click',()=>{const f=file.files[0];load(async()=>{req(f&&f.size<=MAX_BUNDLE,'Select a JSON bundle no larger than 26 MB');return new Uint8Array(await f.arrayBuffer());},anchor.value.trim());});
  $('demo').addEventListener('click',()=>{file.value='';anchor.value='';load(async()=>{const r=await fetch('data/earth-evidence-synthetic.json',{cache:'no-store'});req(r.ok,'Demo unavailable');return new Uint8Array(await r.arrayBuffer());},'');});
  for(const el of [file,anchor])el.addEventListener('input',()=>clear('Input changed. Inspect the bundle again.'));
  select.addEventListener('change',()=>{page=0;detail();});$('prev').addEventListener('click',()=>{if(page>0){page--;detail();}});$('next').addEventListener('click',()=>{if((page+1)*50<model.results[Number(select.value)].matches.length){page++;detail();}});$('clear').addEventListener('click',()=>{file.value='';anchor.value='';clear('No bundle loaded.');});
}
if(typeof document!=='undefined'&&document.getElementById('matches'))start();
