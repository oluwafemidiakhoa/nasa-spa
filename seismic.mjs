import {strictJSON,sha} from './facility.mjs';
import {distanceKm} from './earth.mjs';
export const SOURCE='https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson';
export const MAX_BYTES=2000000;
const DAY=86400000, FRESH=900000, SKEW=300000;
const ok=(v,m)=>{if(!v)throw Error(m);};
const epoch=n=>Number.isSafeInteger(n)&&n>=0&&n<=8640000000000000;
const iso=n=>new Date(n).toISOString();
const point=p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=180&&Math.abs(p[1])<=90;
const LIMIT='Returned USGS M2.5+ global summary records only. Catalog coverage and event parameters may change. Distance is surface great-circle distance to the reported epicenter, not shaking, exposure, damage, probability, prediction or safety. Source authenticity is not independently established.';
export function parseCatalog(bytes){
 ok(bytes instanceof Uint8Array&&bytes.length>0&&bytes.length<=MAX_BYTES,'Catalog size limit');const c=strictJSON(bytes),m=c?.metadata;
 ok(c?.type==='FeatureCollection'&&m?.status===200&&epoch(m.generated)&&Array.isArray(c.features)&&c.features.length<=5000&&m.count===c.features.length,'Invalid USGS collection');
 const seen=new Set(),events=[];let excluded=0;
 for(const f of c.features){const p=f?.properties,g=f?.geometry,id=f?.id;
  ok(f?.type==='Feature'&&typeof id==='string'&&/^[A-Za-z0-9_-]{1,100}$/.test(id)&&!seen.has(id)&&p&&typeof p==='object'&&g?.type==='Point'&&Array.isArray(g.coordinates)&&g.coordinates.length===3&&point(g.coordinates.slice(0,2))&&Number.isFinite(g.coordinates[2])&&epoch(p.time)&&epoch(p.updated)&&typeof p.type==='string'&&(p.mag===null||Number.isFinite(p.mag))&&(p.place===null||typeof p.place==='string'&&p.place.length<=1000),'Invalid event record');seen.add(id);
  if(p.type!=='earthquake'||p.mag===null||p.mag<2.5||p.time<m.generated-7*DAY||p.time>m.generated){excluded++;continue;}
  events.push({id,place:p.place||'Place not supplied',coordinates:g.coordinates.slice(0,2),depthKm:g.coordinates[2],magnitude:p.mag,magType:typeof p.magType==='string'?p.magType.slice(0,30):null,observedAt:iso(p.time),updatedAt:iso(p.updated)});
 }
 return {generatedAt:iso(m.generated),returned:c.features.length,excluded,events};
}
export async function inspectReceipt(r){
 ok(r?.schema==='gaia-usgs-v1'&&r.sourceUrl===SOURCE&&typeof r.capturedAt==='string'&&Number.isFinite(Date.parse(r.capturedAt))&&iso(Date.parse(r.capturedAt))===r.capturedAt&&typeof r.sourceSha256==='string'&&/^[a-f0-9]{64}$/.test(r.sourceSha256)&&Number.isSafeInteger(r.sourceBytes)&&r.sourceBytes>0&&r.sourceBytes<=MAX_BYTES&&typeof r.bodyBase64==='string'&&r.bodyBase64.length===4*Math.ceil(r.sourceBytes/3),'Invalid source receipt');
 const raw=atob(r.bodyBase64);ok(raw.length===r.sourceBytes&&btoa(raw)===r.bodyBase64,'Invalid source encoding');const b=Uint8Array.from(raw,c=>c.charCodeAt(0));ok(await sha(b)===r.sourceSha256,'Source digest mismatch');const catalog=parseCatalog(b);ok(Date.parse(catalog.generatedAt)<=Date.parse(r.capturedAt)+SKEW,'Catalog generated after capture');return {receipt:r,catalog};
}
export function screenCatalog(v,coordinates,radiusKm,now=Date.now()){
 ok(point(coordinates)&&Number.isFinite(radiusKm)&&radiusKm>=1&&radiusKm<=1000&&epoch(now),'Invalid screening parameters');const {receipt:r,catalog:c}=v;const generated=Date.parse(c.generatedAt),captured=Date.parse(r.capturedAt);
 const freshness=now+SKEW<Math.max(generated,captured)?'CLOCK_UNCERTAIN':now-generated>FRESH?'STALE_SNAPSHOT':'WITHIN_15_MINUTES';
 const matches=c.events.map(e=>({...e,distanceKm:distanceKm(coordinates,e.coordinates)})).filter(e=>e.distanceKm<=radiusKm).sort((a,b)=>a.distanceKm-b.distanceKm||(a.id<b.id?-1:a.id>b.id?1:0)).map(e=>({...e,distanceKm:Number(e.distanceKm.toFixed(3))}));
 return {schema:'gaia-seismic-screen-v1',checkedAt:iso(now),site:{coordinates:coordinates.slice(),radiusKm},window:{start:iso(generated-7*DAY),end:c.generatedAt},capturedAt:r.capturedAt,sourceSha256:r.sourceSha256,freshness,coverage:{returned:c.returned,eligible:c.events.length,excluded:c.excluded},status:!c.events.length?'NO_ELIGIBLE_EVENTS':matches.length?'MATCHING_EVENTS':'NO_MATCHES_IN_RETURNED_EVENTS',matchingEvents:c.events.length?matches.length:null,nearest:matches[0]??null,largestMagnitude:matches.length?Math.max(...matches.map(e=>e.magnitude)):null,matches,limitations:LIMIT};
}
export function makePacket(v,coordinates,radiusKm,now){return {schema:'gaia-seismic-packet-v1',receipt:v.receipt,report:screenCatalog(v,coordinates,radiusKm,now)};}
export async function verifyPacket(p){ok(p?.schema==='gaia-seismic-packet-v1','Unsupported packet');const v=await inspectReceipt(p.receipt),r=p.report,expected=screenCatalog(v,r?.site?.coordinates,r?.site?.radiusKm,Date.parse(r?.checkedAt));ok(JSON.stringify(expected)===JSON.stringify(r),'Screening report does not replay');return expected;}
export async function fetchCatalog(transport=fetch){const r=await transport('/api/gaia-usgs',{cache:'no-store',signal:AbortSignal.timeout(18000)});ok(r.ok,'USGS retrieval failed (HTTP '+r.status+')');const reader=r.body?.getReader();ok(reader,'Missing response');let n=0;const chunks=[];try{while(true){const {done,value}=await reader.read();if(done)break;n+=value.byteLength;ok(n<=2800000,'Receipt size limit');chunks.push(value);}}finally{try{await reader.cancel();}catch{}}const b=new Uint8Array(n);let i=0;for(const c of chunks){b.set(c,i);i+=c.length;}return inspectReceipt(strictJSON(b));}
const CITIES=Object.freeze({Houston:[-95.3698,29.7604],'Los Angeles':[-118.2437,34.0522],Tokyo:[139.6917,35.6895],Lagos:[3.3792,6.5244],London:[-0.1276,51.5072]});
export function startSeismic(doc=document,{load=fetchCatalog,clock=()=>Date.now(),download}={}){
 if(!doc.querySelector?.('#usgs-panel'))return null;const $=id=>doc.getElementById(id),node=(tag,t)=>{const e=doc.createElement(tag);e.textContent=String(t);return e;};let busy=false,accepted=null,packet=null;
 const save=download||((data,name)=>{const u=URL.createObjectURL(new Blob([data],{type:'application/json'})),a=doc.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
 function clear(s){packet=null;$('seismic-result').hidden=true;$('seismic-rows').replaceChildren();$('seismic-export').disabled=true;$('seismic-status').textContent=s;}
 function render(){clear(busy?'Retrieving USGS records...':'Retrieve a USGS catalog first.');if(!accepted)return;try{const a=$('seismic-lon').value.trim(),b=$('seismic-lat').value.trim();ok(a&&b,'Enter both coordinates');const p=makePacket(accepted,[Number(a),Number(b)],Number($('seismic-radius').value),clock()),r=p.report;packet=p;
  $('seismic-status').textContent=(r.freshness==='WITHIN_15_MINUTES'?'Catalog within 15 minutes at screening time. ':r.freshness==='STALE_SNAPSHOT'?'Retained stale catalog (more than 15 minutes old). ':'Clock uncertain. ')+(r.matchingEvents===null?'No eligible global events; local count unavailable.':r.matchingEvents+' matching returned events; not a safety determination.');
  $('seismic-window').textContent='Catalog window: '+r.window.start+' through '+r.window.end+' | '+r.coverage.returned+' returned / '+r.coverage.eligible+' eligible / '+r.coverage.excluded+' excluded | captured '+r.capturedAt;
  $('seismic-nearest').textContent=r.nearest?r.nearest.distanceKm.toFixed(1)+' km':'Not available';$('seismic-largest').textContent=r.largestMagnitude===null?'Not available':String(r.largestMagnitude);
  for(const e of r.matches.slice(0,50)){const tr=doc.createElement('tr'),td=doc.createElement('td'),a=node('a',e.place);a.href='https://earthquake.usgs.gov/earthquakes/eventpage/'+encodeURIComponent(e.id)+'/executive';td.append(a);tr.append(td,node('td',e.observedAt),node('td',e.magnitude+' '+(e.magType||'')),node('td',e.depthKm),node('td',e.distanceKm.toFixed(1)));$('seismic-rows').append(tr);}
  $('seismic-result').hidden=false;$('seismic-export').disabled=false;
 }catch(e){clear('Screen unavailable: '+String(e.message).slice(0,150));}}
 async function run(){if(busy)return;busy=true;accepted=null;clear('Retrieving global USGS catalog...');$('seismic-refresh').disabled=true;try{accepted=await load();}catch{clear('USGS source unavailable. Check the official catalog; no absence conclusion.');return;}finally{busy=false;$('seismic-refresh').disabled=false;}render();}
 $('seismic-city').addEventListener('change',()=>{const k=$('seismic-city').value;if(Object.hasOwn(CITIES,k))[$('seismic-lon').value,$('seismic-lat').value]=CITIES[k].map(String);render();});for(const id of ['seismic-lon','seismic-lat'])$(id).addEventListener('input',()=>{$('seismic-city').value='custom';render();});$('seismic-radius').addEventListener('change',render);$('seismic-refresh').addEventListener('click',run);$('seismic-export').addEventListener('click',()=>{if(packet){render();if(packet)save(JSON.stringify(packet,null,2),'gaia-seismic-'+packet.report.sourceSha256.slice(0,12)+'.json');}});clear('Choose a reference site and retrieve the global catalog.');$('seismic-refresh').disabled=false;return {run};
}
if(typeof document!=='undefined'&&document.getElementById('usgs-panel'))startSeismic();
