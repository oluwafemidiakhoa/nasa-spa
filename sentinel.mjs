import {buildSiteBriefing,evidencePacket,canPackage,LABELS,statusLabel} from './site-briefing.mjs';
import {fetchStudy,recentDates} from './workspace.mjs';
import {fetchCatalog,inspectReceipt as inspectSeismic,makePacket} from './seismic.mjs';
import {CITIES as US_CITIES,fetchAlerts,inspectReceipt as inspectWeather} from './nws-alerts.mjs';
const ok=(v,m)=>{if(!v)throw Error(m);};
export const PLACES=Object.freeze({...Object.fromEntries(Object.entries(US_CITIES).map(([k,v])=>[k,Object.freeze({name:v.name,coordinates:Object.freeze(v.point.split(',').map(Number).reverse())})])),tokyo:Object.freeze({name:'Tokyo, Japan',coordinates:Object.freeze([139.6917,35.6895])}),lagos:Object.freeze({name:'Lagos, Nigeria',coordinates:Object.freeze([3.3792,6.5244])}),london:Object.freeze({name:'London, UK',coordinates:Object.freeze([-0.1276,51.5072])})});
const LIMIT='Source windows and coverage differ. Results describe returned records, not risk, exposure, safety, predictions or emergency notification. The NWS record count concerns an explicit public city-center point, not the screening radius. Source authenticity is not independently established.';
const missing=(source,scope,reason)=>({source,scope,status:'Unavailable',count:null,capturedAt:null,reason});
const samePoint=(a,b)=>a.length===2&&a.every((v,i)=>v===b[i]);
export function normalizeInput(x){
 const {coordinates:p,radiusKm:r,place,includeWeather}=x||{};
 ok(Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=180&&Math.abs(p[1])<=90,'Enter valid longitude and latitude.');
 ok(Number.isFinite(r)&&r>=1&&r<=1000,'Choose a radius between 1 and 1,000 km.');
 ok(typeof place==='string'&&(place==='custom'||Object.hasOwn(PLACES,place))&&typeof includeWeather==='boolean','Invalid location selection.');
 if(place!=='custom')ok(samePoint(p,PLACES[place].coordinates),'Public city selection does not match the coordinates.');
 ok(!includeWeather||Object.hasOwn(US_CITIES,place),'Official weather alerts require a supported public U.S. city center.');
 return {coordinates:p.slice(),radiusKm:r,place,includeWeather};
}
export async function reviewSite(input,{earth=fetchStudy,seismic=fetchCatalog,weather=fetchAlerts,clock=()=>Date.now()}={}){
 const site=normalizeInput(input),now=clock(),requestedAt=new Date(now).toISOString(),dates=recentDates(now);
 const earthJob=(async()=>{try{return await buildSiteBriefing(site,dates,earth,now);}catch{return null;}})();
 const seismicJob=(async()=>{try{const v=await seismic(),verified=await inspectSeismic(v.receipt);return makePacket(verified,site.coordinates,site.radiusKm,clock());}catch{return null;}})();
 const weatherJob=(async()=>{if(!site.includeWeather)return null;try{const v=await weather(site.place);return await inspectWeather(v.receipt,site.place);}catch{return null;}})();
 const [e,s,w]=await Promise.all([earthJob,seismicJob,weatherJob]);
 const rows=['wildfires','severeStorms','volcanoes'].map((category,i)=>{const layer=e?.report.layers[i],scope='Returned EONET points; '+dates.start+' through '+dates.end+' UTC';if(!layer||layer.status==='SOURCE_UNAVAILABLE')return missing(LABELS[category],scope,'Retrieval or evidence validation failed.');return {source:LABELS[category],scope,status:statusLabel(layer),count:layer.matchingEvents,capturedAt:layer.capturedAt,reason:layer.coverage.eligiblePoints+' eligible global point(s)'+(layer.coverage.limitReached?' | source limit reached':''),sourceSha256:layer.sourceSha256,bundleSha256:layer.bundleSha256,nearest:layer.nearest};});
 if(s){const r=s.report;rows.push({source:'USGS earthquakes',scope:'M2.5+; '+r.window.start+' through '+r.window.end,status:({MATCHING_EVENTS:'Matching earthquakes',NO_MATCHES_IN_RETURNED_EVENTS:'No matches in returned events',NO_ELIGIBLE_EVENTS:'No eligible earthquake records'})[r.status],count:r.matchingEvents,capturedAt:r.capturedAt,reason:({WITHIN_15_MINUTES:'Catalog within 15 minutes at screening',STALE_SNAPSHOT:'Stale catalog',CLOCK_UNCERTAIN:'Clock uncertain'})[r.freshness]+' | '+r.coverage.eligible+' eligible global earthquake(s)',freshness:r.freshness,sourceSha256:r.sourceSha256,nearest:r.nearest,largestMagnitude:r.largestMagnitude});}else rows.push(missing('USGS earthquakes','Global seven-day M2.5+ catalog','Retrieval or evidence validation failed.'));
 if(w)rows.push({source:'NWS official alerts',scope:'Public city-center point: '+US_CITIES[site.place].name,status:'Official alert records returned',count:w.alerts.length,capturedAt:w.receipt.capturedAt,reason:'Point query; not the selected radius. Follow official instructions.',sourceSha256:w.receipt.sourceSha256});
 else if(site.includeWeather)rows.push(missing('NWS official alerts','Public city-center point: '+US_CITIES[site.place].name,'Check weather.gov directly. No absence conclusion.'));
 else rows.push({source:'NWS official alerts',scope:'Public U.S. city center only',status:'Not requested',count:null,capturedAt:null,reason:'No weather request sent.'});
 const requested=site.includeWeather?5:4,accepted=(e?.report.acceptedSources??0)+(s?1:0)+(w?1:0);
 return {report:{schema:'gaia-sentinel-review-v1',requestedAt,finishedAt:new Date(clock()).toISOString(),site,requestedCollections:requested,acceptedCollections:accepted,rows,limitations:LIMIT},earth:e,seismic:s,weather:w};
}
export function startSentinel(doc=document,{review=reviewSite,download}={}){
 const $=id=>doc.getElementById(id),node=(tag,t)=>{const e=doc.createElement(tag);e.textContent=String(t);return e;};let revision=0,busy=false,current=null;
 const save=download||((data,name,type='application/json')=>{const u=URL.createObjectURL(new Blob([data],{type})),a=doc.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
 const json=(v,name)=>save(JSON.stringify(v,null,2),name);
 function weatherOption(){const valid=Object.hasOwn(US_CITIES,$('sentinel-place').value);$('sentinel-weather').disabled=!valid;if(!valid)$('sentinel-weather').checked=false;}
 function clear(message){revision++;current=null;$('sentinel-rows').replaceChildren();$('sentinel-alerts').replaceChildren();$('sentinel-evidence').replaceChildren();$('sentinel-result').hidden=true;$('sentinel-export').disabled=true;$('sentinel-status').textContent=message;}
 function button(parent,label,fn){const b=node('button',label);b.type='button';b.addEventListener('click',fn);parent.append(b);}
 function render(v){current=v;const r=v.report;$('sentinel-status').textContent=r.acceptedCollections+' of '+r.requestedCollections+' requested collections accepted. Missing collections are not zero observations.';$('sentinel-window').textContent='Requested '+r.requestedAt+' | completed '+r.finishedAt+' | '+r.site.coordinates.join(', ')+' | '+r.site.radiusKm+' km';
  for(const row of r.rows){const tr=doc.createElement('tr'),h=node('th',row.source);h.scope='row';tr.append(h,node('td',row.status),node('td',row.count??'Unavailable'),node('td',row.nearest?(row.nearest.title||row.nearest.place)+' | '+row.nearest.distanceKm.toFixed(1)+' km'+(row.largestMagnitude!==undefined?' | largest magnitude '+row.largestMagnitude:''):'Not reported'),node('td',row.scope+' | '+row.reason+(row.capturedAt?' | captured '+row.capturedAt:'')));$('sentinel-rows').append(tr);}
  const p=$('sentinel-evidence');if(v.earth&&canPackage(v.earth))button(p,'NASA evidence packet',()=>{if(current===v)json(evidencePacket(v.earth),'gaia-site-evidence.json');});else if(v.earth?.bundles.length)for(const b of v.earth.bundles)button(p,'NASA '+b.category+' bundle',()=>{if(current===v)save(b.bytes,'gaia-'+b.category+'.json');});
  if(v.seismic)button(p,'USGS seismic packet',()=>{if(current===v)json(v.seismic,'gaia-seismic.json');});if(v.weather)button(p,'NWS source receipt',()=>{if(current===v)json(v.weather.receipt,'gaia-nws.json');});
  for(const a of v.weather?.alerts||[]){const el=doc.createElement('article');el.append(node('h3',a.event),node('p',[a.status,a.messageType,a.severity,a.urgency,a.certainty].filter(Boolean).join(' | ')),node('p','Issued '+a.sent+' | Expires '+a.expires),node('p',a.areaDesc||'Area not supplied'),node('p',a.headline||''),node('p',a.description||'Description not supplied'),node('p',a.instruction||'No instructions supplied.'));$('sentinel-alerts').append(el);}
  $('sentinel-result').hidden=false;$('sentinel-export').disabled=false;
 }
 async function run(){if(busy)return;clear('Retrieving selected source collections...');const token=revision;busy=true;$('sentinel-run').disabled=true;try{const lon=$('sentinel-lon').value.trim(),lat=$('sentinel-lat').value.trim();ok(lon&&lat,'Enter both coordinates.');const v=await review({coordinates:[Number(lon),Number(lat)],radiusKm:Number($('sentinel-radius').value),place:$('sentinel-place').value,includeWeather:$('sentinel-weather').checked===true});if(token===revision)render(v);}catch(e){if(token===revision)clear('Review unavailable: '+String(e.message).slice(0,150));}finally{busy=false;$('sentinel-run').disabled=false;}}
 $('sentinel-place').addEventListener('change',()=>{const place=$('sentinel-place').value;if(Object.hasOwn(PLACES,place))[$('sentinel-lon').value,$('sentinel-lat').value]=PLACES[place].coordinates.map(String);weatherOption();clear('Location changed. Run a new review.');});
 for(const id of ['sentinel-lon','sentinel-lat'])$(id).addEventListener('input',()=>{$('sentinel-place').value='custom';weatherOption();clear('Coordinates changed. Run a new review.');});for(const id of ['sentinel-radius','sentinel-weather'])$(id).addEventListener('change',()=>clear('Review inputs changed. Run again.'));
 $('sentinel-run').addEventListener('click',run);$('sentinel-export').addEventListener('click',()=>{if(current)json(current.report,'gaia-sentinel-review.json');});weatherOption();clear('Choose a location and run the review.');$('sentinel-run').disabled=false;return {run};
}
if(typeof document!=='undefined'&&document.getElementById('sentinel-run'))startSentinel();
