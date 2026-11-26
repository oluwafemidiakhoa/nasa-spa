import {screen,MAX_BYTES} from './earth.mjs';
import {inspectBundle,strictJSON,sha,MAX_BUNDLE} from './facility.mjs';
const BASE='https://eonet.gsfc.nasa.gov/api/v3/events',DAY=86400000;
const METHODS={'earth.mjs':'a1ce541de7aa9d49e934fa8c642782741828aad3c8893bb2e29b9465b14df0bc','scripts/earth-batch.mjs':'6b0b64c3f384a3d40d77afbb1cf5744cdac75307535f886a730762e3b28061ba','scripts/eonet_archive.py':'24010b808d080126964c809a37a1a354037340f3a990108b0096fb74831c007b','scripts/verify_earth_batch.py':'693f59bd3351e1544a58c624148cc77ea92e08990d7cf12153c56be0f6ac9ed4'};
const req=(ok,m)=>{if(!ok)throw Error(m);};
const encode=o=>new TextEncoder().encode(JSON.stringify(o)+'\n');
const keys=(o,k)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).length===k.length&&k.every(x=>Object.hasOwn(o,x));
function day(s){req(typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&s>='0001-01-01'&&s<'9999-12-31','Invalid UTC date');const t=Date.parse(s+'T00:00:00Z');req(Number.isFinite(t)&&new Date(t).toISOString().slice(0,10)===s,'Invalid UTC date');return t;}
export function study(x){
  req(keys(x,['start','end','category','radiusKm','facilities']),'Invalid study fields');const a=day(x.start),b=day(x.end),n=(b-a)/DAY+1;
  req(n>=1&&n<=30&&['wildfires','severeStorms','volcanoes'].includes(x.category),'Choose 1-30 UTC dates and a supported category');
  req(Number.isFinite(x.radiusKm)&&x.radiusKm>=1&&x.radiusKm<=1000&&Array.isArray(x.facilities)&&x.facilities.length>=1&&x.facilities.length<=25,'Invalid radius or number of locations');
  const ids=new Set();for(const f of x.facilities){req(keys(f,['id','coordinates'])&&typeof f.id==='string'&&/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(f.id)&&!ids.has(f.id)&&Array.isArray(f.coordinates)&&f.coordinates.length===2&&f.coordinates.every(Number.isFinite)&&Math.abs(f.coordinates[0])<=180&&Math.abs(f.coordinates[1])<=90,'Invalid or duplicate location');ids.add(f.id);}
  return {query:{status:'all',start:x.start,end:x.end,category:x.category,limit:200},config:{snapshotKind:'user-import-unverified',asOf:new Date(b+DAY).toISOString(),hours:n*24,radiusKm:x.radiusKm,facilities:x.facilities}};
}
function base64(bytes){let s='';for(let i=0;i<bytes.length;i+=16384)s+=String.fromCharCode(...bytes.subarray(i,i+16384));return btoa(s);}
async function component(bytes,max){req(bytes.length>0&&bytes.length<=max,'Component too large');return {sha256:await sha(bytes),bytes:bytes.length,base64:base64(bytes)};}
export async function createBundle(response,x){
  const {query,config}=study(x);req(keys(response,['requestUrl','capturedAt','sourceSha256','bodyBase64'])&&response.requestUrl===BASE+'?'+new URLSearchParams(query)&&typeof response.bodyBase64==='string'&&response.bodyBase64.length<=4*Math.ceil(MAX_BYTES/3),'Invalid acquisition envelope');
  const s=atob(response.bodyBase64);req(s.length>0&&s.length<=MAX_BYTES&&btoa(s)===response.bodyBase64,'Invalid source bytes');const source=Uint8Array.from(s,c=>c.charCodeAt(0));const digest=await sha(source);req(response.sourceSha256===digest,'Source digest mismatch');const raw=strictJSON(source);
  req(Array.isArray(raw?.events)&&raw.events.length<=200,'Unexpected event count');
  const results=[...config.facilities].sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0).map(f=>({facilityId:f.id,...screen(raw,{facility:f.coordinates,asOf:config.asOf,hours:config.hours,radiusKm:config.radiusKm})}));
  const cov=results[0].coverage,receipt={mode:'https-eonet',capturedAt:response.capturedAt,requestUrl:response.requestUrl,query,httpStatus:200,limitReached:cov.events===200,coverage:'unknown',sourceAuthenticated:false,sourceSha256:digest,sourceBytes:source.length,eventCount:cov.events,pointCount:cov.eligiblePoints+cov.outsideWindow,nonPointCount:cov.unsupportedGeometries,eventsWithoutGeometry:cov.eventsWithoutGeometry};
  const archive=await component(encode({schema:'gaia-eonet-archive-v0.4',receipt,bodyBase64:response.bodyBase64}),3_000_000),configuration=await component(encode(config),32768);
  const report=await component(encode({schema:'gaia-earth-batch-v0.3',snapshot:{kind:config.snapshotKind,sha256:digest,bytes:source.length,authenticity:'unverified'},configuration:{sha256:configuration.sha256,bytes:configuration.bytes},results}),16_000_000);
  const bytes=encode({schema:'gaia-earth-evidence-v0.5',methods:METHODS,files:{archive,configuration,report}});return {bytes,model:await inspectBundle(bytes)};
}
async function readResponse(r,max){req(r.ok,'Request failed (HTTP '+r.status+')');const reader=r.body?.getReader();req(reader,'No response body');let n=0;const chunks=[];try{while(true){const {done,value}=await reader.read();if(done)break;n+=value.byteLength;req(n<=max,'Response exceeds size limit');chunks.push(value);}}finally{try{await reader.cancel();}catch{}}const out=new Uint8Array(n);let i=0;for(const c of chunks){out.set(c,i);i+=c.length;}return out;}
export function recentDates(now=Date.now()){
  const t=Math.floor(now/DAY)*DAY;
  return {start:new Date(t-7*DAY).toISOString().slice(0,10),end:new Date(t-DAY).toISOString().slice(0,10)};
}
export async function fetchStudy(x,transport=fetch){
  study(x);
  const q=new URLSearchParams({start:x.start,end:x.end,category:x.category});
  const r=await transport('/api/gaia-eonet?'+q,{cache:'no-store',signal:AbortSignal.timeout(20000)});
  return createBundle(strictJSON(await readResponse(r,3_000_000)),x);
}
export function startWorkspace(doc=document,transport=fetch,now=Date.now()){
  const $=id=>doc.getElementById(id),text=(id,v)=>{$(id).textContent=String(v);},node=(tag,v)=>{const e=doc.createElement(tag);e.textContent=v;return e;};let revision=0,current=null,page=0,busy=false;
  const labels={POINTS_WITHIN_RADIUS:'Matching points found',NO_MATCH_IN_AVAILABLE_POINTS:'No matching points in available observations',NO_ELIGIBLE_POINTS:'No eligible observations'};
  function buttons(){for(const id of ['fetch','open','demo'])$(id).disabled=busy;}
  function clear(message){revision++;current=null;page=0;busy=false;$('results').hidden=true;$('facility').replaceChildren();$('rows').replaceChildren();$('plot').replaceChildren();text('status',message);buttons();return revision;}
  function input(){const facilities=$('locations').value.split(/\r?\n/).filter(s=>s.trim()).map(s=>{const f=s.split(',').map(x=>x.trim());req(f.length===3&&f.every(Boolean),'Use ID, longitude, latitude');return {id:f[0],coordinates:f.slice(1).map(Number)};});return {start:$('start').value,end:$('end').value,category:$('category').value,radiusKm:Number($('radius').value),facilities};}
  const svg=(tag,attrs,v)=>{const e=doc.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,x] of Object.entries(attrs))e.setAttribute(k,String(x));if(v!==undefined)e.textContent=v;return e;};
  function detail(){if(!current)return;const r=current.model.results[Number($('facility').value)];if(!r)return;const p=r.parameters;const c=r.coverage;text('window',new Date(Date.parse(p.asOf)-p.hours*3600000).toISOString()+' to '+p.asOf+' inclusive | '+p.radiusKm+' km');text('match-state',labels[r.status]+' | '+r.matches.length+' distinct matching events. '+c.outsideWindow+' point rows outside the window. '+c.unsupportedGeometries+' non-point geometries excluded.');const plot=$('plot');plot.replaceChildren();for(const f of [.5,1])plot.append(svg('circle',{cx:160,cy:160,r:132*f,fill:'none',stroke:'#48617b'}));plot.append(svg('path',{d:'M28 160H292 M160 28V292',stroke:'#48617b','stroke-dasharray':'3 4'}));for(const [x,y,v] of [[160,18,'N'],[306,164,'E'],[160,312,'S'],[14,164,'W']])plot.append(svg('text',{x,y,'text-anchor':'middle','font-size':12,fill:'#b2c6d8'},v));const [lon,lat]=p.facility.map(x=>x*Math.PI/180);for(const m of r.matches){const [a,b]=m.coordinates.map(x=>x*Math.PI/180),d=a-lon,bearing=Math.atan2(Math.sin(d)*Math.cos(b),Math.cos(lat)*Math.sin(b)-Math.sin(lat)*Math.cos(b)*Math.cos(d)),dist=132*Math.min(1,m.distanceKm/p.radiusKm);const dot=svg('circle',{cx:160+dist*Math.sin(bearing),cy:160-dist*Math.cos(bearing),r:4,fill:'#91e0cb'});dot.append(svg('title',{},m.title+' | '+m.distanceKm+' km'));plot.append(dot);}plot.append(svg('circle',{cx:160,cy:160,r:5,fill:'#e8f3fc'}));$('rows').replaceChildren();for(const m of r.matches.slice(page*50,page*50+50)){const tr=doc.createElement('tr');for(const v of [m.eventId,m.title,m.observedAt,m.distanceKm.toFixed(3)])tr.append(node('td',v));$('rows').append(tr);}text('page',r.matches.length?(page*50+1)+'-'+Math.min(r.matches.length,page*50+50)+' of '+r.matches.length:'No matching records.');$('prev').disabled=page===0;$('next').disabled=(page+1)*50>=r.matches.length;}
  async function run(work){const id=clear('Checking evidence and calculating observations...');busy=true;buttons();try{const v=await work();if(id!==revision)return;current=v;const m=v.model;text('kind',m.kind==='synthetic-demo'?'Synthetic example — fictional observations':'Retrieved or imported observations — authenticity unverified');text('events',m.results[0].coverage.events);text('points',m.results[0].coverage.eligiblePoints);text('sites',m.results.filter(r=>r.matches.length).length+' / '+m.results.length);text('digest',m.digest);text('source',m.sourceHash);text('capture',m.mode+' | '+m.capturedAt+' | '+(m.anchorChecked?'Retained digest matched.':'No independently retained digest checked.'));for(const [i,r] of m.results.entries()){const o=node('option',r.facilityId);o.value=String(i);$('facility').append(o);}detail();$('results').hidden=false;text('status','Browser consistency replay matched. Independent Python replay not performed.');}catch(e){if(id===revision)clear('No result accepted: '+String(e.message).slice(0,200));}finally{if(id===revision){busy=false;buttons();}}}
  function runLive(){if(!busy)return run(async()=>fetchStudy(input(),transport));}
  $('run').addEventListener('submit',e=>{e.preventDefault();runLive();});
  $('open').addEventListener('click',()=>{if(busy)return;const f=$('file').files[0],a=$('anchor').value.trim();run(async()=>{req(f&&f.size<=MAX_BUNDLE,'Choose an evidence bundle up to 26 MB');const bytes=new Uint8Array(await f.arrayBuffer());return {bytes,model:await inspectBundle(bytes,a)};});});
  $('demo').addEventListener('click',()=>{if(busy)return;run(async()=>{const bytes=await readResponse(await fetch('data/earth-evidence-synthetic.json',{cache:'no-store'}),MAX_BUNDLE);return {bytes,model:await inspectBundle(bytes)};});});
  $('clear').addEventListener('click',()=>clear('No study loaded.'));for(const id of ['start','end','category','radius','locations','file','anchor'])$(id).addEventListener('input',()=>clear('Input changed. Run or reopen a study.'));
  function setRecent(time){const dates=recentDates(time);$('start').value=dates.start;$('end').value=dates.end;}
  $('recent').addEventListener('click',()=>{setRecent(Date.now());clear('Dates updated. Run the study.');});
  $('facility').addEventListener('change',()=>{page=0;detail();});$('prev').addEventListener('click',()=>{if(page>0){page--;detail();}});$('next').addEventListener('click',()=>{if(current&&(page+1)*50<current.model.results[Number($('facility').value)].matches.length){page++;detail();}});
  $('download').addEventListener('click',()=>{if(!current)return;const u=URL.createObjectURL(new Blob([current.bytes],{type:'application/json'})),a=doc.createElement('a');a.href=u;a.download='gaia-earth-'+current.model.digest.slice(0,12)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
  clear('Loading recent NASA observations...');
  setRecent(now);
  return runLive();
}
if(typeof document!=='undefined'&&document.getElementById('run'))startWorkspace();
