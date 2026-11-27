// User-triggered screening only. Three bounded global queries; no new model or forecast.
export const LAYERS=Object.freeze(['wildfires','severeStorms','volcanoes']);
export const LABELS=Object.freeze({wildfires:'Wildfires',severeStorms:'Severe storms',volcanoes:'Volcanoes'});
export const PACKET_LIMIT=24_000_000;
const DAY=86400000, MAX_BUNDLE=26_000_000, SITE='BRIEFING-REFERENCE';
const LIMITATIONS='Descriptive screening of returned global EONET point records only; coverage and source authenticity are unknown. Points are not hazard footprints, severity, forecasts, warnings or proof of safety. Consult official local authorities for operational decisions.';
const ok=(v,m)=>{if(!v)throw Error(m);};
const hex=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const tidy=(s,n=180)=>String(s).replace(/[\x00-\x1f\x7f]/g,' ').slice(0,n);
function utcDay(s){ok(typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s),'Invalid date');const t=Date.parse(s+'T00:00:00Z');ok(Number.isFinite(t)&&new Date(t).toISOString().slice(0,10)===s,'Invalid date');return t;}
function normalize(site,dates){
 const p=site?.coordinates,r=site?.radiusKm;
 ok(Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=180&&Math.abs(p[1])<=90,'Enter valid longitude and latitude.');
 ok(Number.isFinite(r)&&r>=1&&r<=1000,'Enter a radius from 1 to 1,000 km.');
 const a=utcDay(dates?.start),b=utcDay(dates?.end);ok(b-a===6*DAY,'Expected seven complete UTC dates');
 return {coordinates:p.slice(),radiusKm:r,start:dates.start,end:dates.end,asOf:new Date(b+DAY).toISOString()};
}
async function digest(bytes){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');}
function safeError(e){const m=String(e?.message||'').match(/^Request failed \(HTTP [1-5]\d{2}(?:; UPSTREAM_[A-Z0-9_]+)?\)$/);return m?m[0]:'Retrieval or evidence validation failed.';}
async function accept(v,q,category){
 const m=v?.model,r=m?.results?.[0],p=r?.parameters,b=v?.bytes;
 ok(m?.mode==='https-eonet'&&m.kind==='user-import-unverified'&&m.results.length===1&&r.facilityId===SITE,'Expected a retrieved evidence bundle');
 ok(p?.asOf===q.asOf&&p.hours===168&&p.radiusKm===q.radiusKm&&Array.isArray(p.facility)&&p.facility.length===2&&p.facility.every((x,i)=>x===q.coordinates[i]),'Evidence parameters differ');
 ok(hex(m.sourceHash)&&hex(m.digest)&&b instanceof Uint8Array&&b.length>0&&b.length<=MAX_BUNDLE&&await digest(b)===m.digest,'Evidence digest mismatch');
 // The existing fetchStudy path verifies the acquisition URL and replays the bundle.
 // Check the archived query as well, so a mislabeled source cannot enter the briefing.
 const pack=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(b));
 const archive=JSON.parse(atob(pack.files.archive.base64)),receipt=archive.receipt,query=receipt.query;
 ok(query?.category===category&&query.start===q.start&&query.end===q.end&&query.limit===200&&query.status==='all'&&receipt.sourceSha256===m.sourceHash&&receipt.capturedAt===m.capturedAt,'Evidence query differs');
 const c=r.coverage,n=r.matches.length,status=r.status;
 ok(Number.isSafeInteger(c.events)&&c.events>=0&&c.events<=200&&Number.isSafeInteger(c.eligiblePoints)&&c.eligiblePoints>=0&&n<=c.events&&receipt.limitReached===(c.events===200),'Invalid coverage');
 ok(status===(n?'POINTS_WITHIN_RADIUS':c.eligiblePoints?'NO_MATCH_IN_AVAILABLE_POINTS':'NO_ELIGIBLE_POINTS'),'Inconsistent observation status');
 const nearest=r.matches[0];
 return {row:{category,status,matchingEvents:status==='NO_ELIGIBLE_POINTS'?null:n,nearest:nearest?{eventId:tidy(nearest.eventId),title:tidy(nearest.title),observedAt:nearest.observedAt,distanceKm:nearest.distanceKm}:null,coverage:{...c,limitReached:receipt.limitReached},capturedAt:m.capturedAt,sourceSha256:m.sourceHash,bundleSha256:m.digest,bundleBytes:b.length,reportPointer:'/results/0'},bytes:b};
}
export async function buildSiteBriefing(site,dates,load,now=Date.now()){
 const q=normalize(site,dates);ok(typeof load==='function'&&Number.isFinite(now),'Invalid briefing request');
 const requestedAt=new Date(now).toISOString();
 const results=await Promise.all(LAYERS.map(async category=>{try{
   const v=await load({start:q.start,end:q.end,category,radiusKm:q.radiusKm,facilities:[{id:SITE,coordinates:q.coordinates.slice()}]});
   return await accept(v,q,category);
 }catch(e){return {row:{category,status:'SOURCE_UNAVAILABLE',matchingEvents:null,nearest:null,coverage:null,error:safeError(e)},bytes:null};}}));
 const accepted=results.filter(v=>v.bytes!==null).length;
 return {report:{schema:'gaia-site-briefing-v1',requestedAt,site:{coordinates:q.coordinates,radiusKm:q.radiusKm},window:{start:q.start,end:q.end,asOf:q.asOf,hours:168},state:accepted===3?'ALL_SOURCES_ACCEPTED':accepted?'PARTIAL_SOURCES_ACCEPTED':'NO_SOURCES_ACCEPTED',acceptedSources:accepted,totalSources:3,layers:results.map(v=>v.row),limitations:LIMITATIONS},bundles:results.filter(v=>v.bytes!==null).map(v=>({category:v.row.category,sha256:v.row.bundleSha256,bytes:v.bytes}))};
}
export function statusLabel(row){switch(row.status){case 'POINTS_WITHIN_RADIUS':return 'Matching observations';case 'NO_MATCH_IN_AVAILABLE_POINTS':return 'No matches in returned points';case 'NO_ELIGIBLE_POINTS':return 'No eligible point observations';default:return 'Source unavailable';}}
export function briefingText(report){const p=report.site,w=report.window;
 return ['GAIA OBSERVATORY | Site observation briefing','',`Location (longitude, latitude): ${p.coordinates.join(', ')} | ${p.radiusKm} km`,`UTC dates queried: ${w.start} through ${w.end}`,`Accepted sources: ${report.acceptedSources} of ${report.totalSources} | ${report.state}`,'',...report.layers.flatMap(r=>[LABELS[r.category]+': '+statusLabel(r),r.matchingEvents===null?'Matching count unavailable':`Matching events: ${r.matchingEvents}`,r.nearest?`Nearest retained point: ${r.nearest.title} | ${r.nearest.distanceKm} km | ${r.nearest.observedAt}`:'Nearest matching point not reported',r.coverage?`Global returned records: ${r.coverage.events}; eligible points: ${r.coverage.eligiblePoints}; source limit reached: ${r.coverage.limitReached?'yes':'no'}`:r.error,r.bundleSha256?'Source SHA-256: '+r.sourceSha256+'\nEvidence bundle SHA-256: '+r.bundleSha256+'\nCapture: '+r.capturedAt:'No accepted evidence bundle','']),report.limitations,'The companion evidence packet contains the accepted original bundle bytes. Exact coordinates are included in these downloads.'].join('\n');}
function base64(bytes){let s='';for(let i=0;i<bytes.length;i+=16384)s+=String.fromCharCode(...bytes.subarray(i,i+16384));return btoa(s);}
export function canPackage(v){return v.bundles.length>0&&v.bundles.reduce((n,b)=>n+b.bytes.length,0)<=PACKET_LIMIT;}
export function evidencePacket(v){ok(canPackage(v),'No accepted bundles or package size limit exceeded');return {schema:'gaia-site-briefing-packet-v1',report:v.report,evidence:v.bundles.map(b=>({category:b.category,sha256:b.sha256,bytes:b.bytes.length,base64:base64(b.bytes)}))};}
export function startSiteBriefing(doc=document,{load,dates,clock=()=>Date.now(),download,onClear=()=>{},onResult=()=>{}}={}){
 if(!doc.querySelector?.('#site-briefing'))return null;
 const $=id=>doc.getElementById(id),node=(tag,t)=>{const el=doc.createElement(tag);el.textContent=t;return el;};let revision=0,busy=false,current=null;
 const save=download||((data,name,type)=>{const url=URL.createObjectURL(new Blob([data],{type})),a=doc.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 function clear(message){onClear();revision++;current=null;$('briefing-result').hidden=true;$('briefing-rows').replaceChildren();$('briefing-status').textContent=message;$('briefing-text').disabled=true;$('briefing-packet').disabled=true;}
 function render(v){current=v;const r=v.report;$('briefing-window').textContent=`${r.window.start} through ${r.window.end} UTC | ${r.site.coordinates.join(', ')} | ${r.site.radiusKm} km`;
  $('briefing-status').textContent=r.acceptedSources===3?'Three source collections accepted; geographic coverage remains unknown.':`${r.acceptedSources} of 3 source collections accepted. Missing collections are not zero observations.`;
  for(const row of r.layers){const tr=doc.createElement('tr'),header=node('th',LABELS[row.category]);header.scope='row';tr.append(header);
   tr.append(node('td',statusLabel(row)),node('td',row.matchingEvents===null?'Unavailable':String(row.matchingEvents)),node('td',row.nearest?`${row.nearest.title} | ${row.nearest.distanceKm.toFixed(1)} km | ${row.nearest.observedAt}`:'Not reported'));
   const evidence=node('td',row.coverage?`${row.coverage.events} global events / ${row.coverage.eligiblePoints} eligible points${row.coverage.limitReached?' | SOURCE LIMIT REACHED':''}`:row.error);
   const b=v.bundles.find(x=>x.category===row.category);if(b){const button=node('button','Download source bundle');button.type='button';button.addEventListener('click',()=>{if(current===v)save(b.bytes,`gaia-${row.category}-${b.sha256.slice(0,12)}.json`,'application/json');});evidence.append(button);}tr.append(evidence);$('briefing-rows').append(tr);
  }
  $('briefing-result').hidden=false;$('briefing-text').disabled=false;$('briefing-packet').disabled=!canPackage(v);$('briefing-export-status').textContent=canPackage(v)?'The packet includes the exact accepted evidence bundles; coordinates are included in both downloads.':v.bundles.length?'Combined evidence exceeds the package limit. Download the individual bundles.':'No evidence bundles accepted; only the attempt summary can be downloaded.';
 }
 async function run(){if(busy)return;clear('Retrieving and checking three NASA EONET collections…');const token=revision;busy=true;$('briefing-run').disabled=true;
  try{const lon=$('local-lon').value.trim(),lat=$('local-lat').value.trim();ok(lon&&lat,'Enter both coordinates.');const t=clock(),v=await buildSiteBriefing({coordinates:[Number(lon),Number(lat)],radiusKm:Number($('local-radius').value)},dates(t),load,t);if(token===revision){render(v);onResult(v);}}
  catch(e){if(token===revision)clear(tidy(e.message));}finally{busy=false;$('briefing-run').disabled=false;}
 }
 $('briefing-run').addEventListener('click',run);
 for(const [id,event] of [['local-city','change'],['local-lon','input'],['local-lat','input'],['local-radius','change']])$(id).addEventListener(event,()=>clear(busy?'Location changed. The previous request is finishing; run again afterward.':'Location changed. Run a new briefing.'));
 $('briefing-text').addEventListener('click',()=>{if(current)save(briefingText(current.report),`gaia-site-briefing-${current.report.window.end}.txt`,'text/plain');});
 $('briefing-packet').addEventListener('click',()=>{if(current&&canPackage(current))save(JSON.stringify(evidencePacket(current)),`gaia-site-evidence-${current.report.window.end}.json`,'application/json');});
 clear('Choose a location and radius, then run the three-category briefing.');$('briefing-run').disabled=false;return {run};
}
