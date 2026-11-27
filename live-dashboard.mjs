import {fetchStudy,recentDates} from './workspace.mjs';
import {inspectBundle,strictJSON,MAX_BUNDLE} from './facility.mjs';
import {apodSummary,donkiCount} from './mission-control.mjs';
import {startLocalScreen} from './local-screen.mjs';
const HISTORY_LIMIT=20000, TABLE_LIMIT=100;
const DAY=86400000, NS='http://www.w3.org/2000/svg';
const req=(ok,message)=>{if(!ok)throw Error(message);};
export function project([lon,lat]){req(Number.isFinite(lon)&&Number.isFinite(lat)&&Math.abs(lon)<=180&&Math.abs(lat)<=90,'Invalid coordinate');return [2*(lon+180),2*(90-lat)];}
export function mapRecords(model){
  const p=model.results[0].parameters,start=Date.parse(p.asOf)-p.hours*3600000,end=Date.parse(p.asOf),records=[];
  let eligible=0;
  for(const event of model.snapshot.events){let latest=null;for(const g of event.geometry){if(g.type!=='Point')continue;const t=Date.parse(g.date);if(t<start||t>end)continue;eligible++;project(g.coordinates);if(!latest||t>latest.t||(t===latest.t&&(g.coordinates[0]<latest.coordinates[0]||(g.coordinates[0]===latest.coordinates[0]&&g.coordinates[1]<latest.coordinates[1]))))latest={t,coordinates:g.coordinates};}if(latest)records.push({id:event.id,title:event.title,coordinates:latest.coordinates,date:new Date(latest.t).toISOString()});}
  req(eligible===model.results[0].coverage.eligiblePoints,'Observation count mismatch');records.sort((a,b)=>b.date.localeCompare(a.date)||a.id.localeCompare(b.id));
  return {total:model.snapshot.events.length,eligible,eventCount:records.length,records:records.slice(0,300),start:new Date(start).toISOString(),end:p.asOf};
}
// An observation history is not a forecast or an inferred continuous track.
// Only storm observations with unique, increasing times may be joined; never
// draw across the entire map at the antimeridian or through ambiguous ties.
export function observationHistory(model,id){
  const p=model.results[0].parameters,end=Date.parse(p.asOf),start=end-p.hours*3600000;
  const event=model.snapshot.events.find(e=>e.id===id);req(event,'Unknown event');
  const points=[];
  for(const g of event.geometry){if(g.type!=='Point')continue;const t=Date.parse(g.date);if(t<start||t>end)continue;project(g.coordinates);points.push({t,date:new Date(t).toISOString(),coordinates:g.coordinates.slice()});req(points.length<=HISTORY_LIMIT,'History limit exceeded');}
  points.sort((a,b)=>a.t-b.t||a.coordinates[0]-b.coordinates[0]||a.coordinates[1]-b.coordinates[1]);
  const storm=Array.isArray(event.categories)&&event.categories.some(c=>c?.id==='severeStorms');
  const segments=[];
  if(storm)for(let i=1;i<points.length;i++){const a=points[i-1],b=points[i];if(a.t===b.t||points[i-2]?.t===a.t||points[i+1]?.t===b.t||Math.abs(a.coordinates[0]-b.coordinates[0])>180)continue;segments.push([a.coordinates,b.coordinates]);}
  return {points,segments,storm};
}
export function plainCredit(value){
  if(typeof value!=='string')return '';
  return value.slice(0,2000).replace(/<[^>]*>/g,' ').replace(/&(?:amp|quot|apos|nbsp|lt|gt|#39);/g,m=>({'&amp;':'&','&quot;':'"','&apos;':"'",'&nbsp;':' ','&lt;':'<','&gt;':'>','&#39;':"'"})[m]).replace(/\s+/g,' ').trim().slice(0,500);
}
export function safeNasaImage(data){if((data.media_kind||data.media_type)!=='image'||typeof data.media_url!=='string')return null;try{const u=new URL(data.media_url);if(u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&(u.hostname==='nasa.gov'||u.hostname.endsWith('.nasa.gov')))return u.href;}catch{}return null;}
export function timeline(data,type){
  const count=donkiCount(data),days=new Map(),field=type==='flr'?'peakTime':'startTime';let undated=0;
  for(const record of data){const s=record[field];if(typeof s!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z$/.test(s)||!Number.isFinite(Date.parse(s))||new Date(Date.parse(s)).toISOString().slice(0,10)!==s.slice(0,10)){undated++;continue;}const day=s.slice(0,10);days.set(day,(days.get(day)||0)+1);}
  const rows=[...days].sort((a,b)=>a[0].localeCompare(b[0]));return {count,undated,days:rows.slice(-14),omittedDays:Math.max(0,rows.length-14),field};
}
async function getBytes(r,max){req(r.ok,'HTTP '+r.status);const reader=r.body?.getReader();req(reader,'No response body');const chunks=[];let n=0;try{while(true){const {done,value}=await reader.read();if(done)break;n+=value.byteLength;req(n<=max,'Response size limit');chunks.push(value);}}finally{try{await reader.cancel();}catch{}}const out=new Uint8Array(n);let i=0;for(const c of chunks){out.set(c,i);i+=c.length;}return out;}
async function nasa(type,transport){req(['apod','cme','flr','gst'].includes(type),'Unknown collection');return strictJSON(await getBytes(await transport('/api/nasa?type='+type,{signal:AbortSignal.timeout(20000),cache:'no-store'}),1_000_000));}
export function startDashboard(doc=document,transport=fetch,now=Date.now()){
 const $=id=>doc.getElementById(id),text=(id,v)=>{$(id).textContent=String(v);},svg=(tag,attrs,v)=>{const e=doc.createElementNS(NS,tag);for(const [k,x] of Object.entries(attrs))e.setAttribute(k,String(x));if(v!==undefined)e.textContent=v;return e;};let earthRev=0,spaceRev=0,current=null,selected=null,zoomed=false;
 const local=startLocalScreen(doc);
 for(const id of ['earth-refresh','import','demo','apod-refresh','donki-refresh'])$(id).disabled=false;
 function mapGuide(){text('map-guide',!current?'Observation zoom is unavailable until records are loaded.':!selected?($('register').children.length?'Select an event in the register or a map marker to enable zoom.':'No eligible points to select for this query.'):zoomed?'Focused view. Choose another event to move the map, or select World view.':'Event selected. Use Zoom to selected to focus the map.');$('zoom').disabled=!selected||zoomed;$('reset').disabled=!zoomed;}
 function resetMap(){zoomed=false;$('map').setAttribute('viewBox','0 0 720 360');mapGuide();}
 function focusMap(){if(!selected)return;const [x,y]=project(selected.record.coordinates);$('map').setAttribute('viewBox',Math.max(0,Math.min(480,x-120))+' '+Math.max(0,Math.min(240,y-60))+' 240 120');zoomed=true;mapGuide();}
 function clearEarth(message){local.clear(message);current=null;selected=null;for(const id of ['events','eligible','mapped'])text(id,'—');for(const id of ['markers','register','history-points','history-segments','history-rows'])$(id).replaceChildren();$('history-panel').hidden=true;for(const id of ['zoom','download'])$(id).disabled=true;resetMap();text('window','No accepted observations yet.');text('digest','');text('detail','Select an observation to inspect its date and coordinates.');text('earth-status',message);}
 function showHistory(record){
   const h=observationHistory(current.model,record.id);$('history-points').replaceChildren();$('history-segments').replaceChildren();$('history-rows').replaceChildren();
   // Use one SVG path per layer, bounded by the existing geometry limit.
   const lines=h.segments.map(([a,b])=>{const [x,y]=project(a),[u,v]=project(b);return 'M'+x+' '+y+'L'+u+' '+v;}).join(' ');
   if(lines)$('history-segments').append(svg('path',{d:lines,class:'history-line','pointer-events':'none'}));
   const dots=h.points.map(p=>{const [x,y]=project(p.coordinates);return 'M'+(x-1.4)+' '+y+'a1.4 1.4 0 1 0 2.8 0a1.4 1.4 0 1 0 -2.8 0';}).join(' ');
   if(dots)$('history-points').append(svg('path',{d:dots,class:'history-dot','pointer-events':'none'}));
   text('history-summary',h.points.length+' retained point rows | '+h.segments.length+' chronological segments. '+(h.storm?'Segments link only unambiguous successive storm observations, not a forecast or continuous measured path.':'Only observed points shown; movement is not inferred.')+' Table shows latest '+Math.min(TABLE_LIMIT,h.points.length)+' rows.');
   for(const p of h.points.slice(-TABLE_LIMIT).reverse()){const tr=doc.createElement('tr');for(const v of [p.date,p.coordinates[1].toFixed(4),p.coordinates[0].toFixed(4)]){const td=doc.createElement('td');td.textContent=v;tr.append(td);}$('history-rows').append(tr);}
   $('history-panel').hidden=false;
 }
 function select(record,marker,button){if(selected){selected.marker.setAttribute('class','marker');selected.button.setAttribute('aria-pressed','false');}selected={record,marker,button};marker.setAttribute('class','marker selected');button.setAttribute('aria-pressed','true');text('detail',record.title+' | '+record.date+' | '+record.coordinates[1].toFixed(4)+' latitude, '+record.coordinates[0].toFixed(4)+' longitude | '+record.id);showHistory(record);if(zoomed)focusMap();else mapGuide();}
 function render(v,mode){const m=v.model,r=mapRecords(m);current=v;text('events',r.total);text('eligible',r.eligible);text('mapped',r.records.length);text('window',r.start+' through '+r.end+' (inclusive UTC). '+r.eventCount+' events with eligible points.'+(r.eventCount>r.records.length?' Latest 300 plotted.':''));text('digest','Bundle SHA-256: '+m.digest);text('earth-status',(m.kind==='synthetic-demo'?'SYNTHETIC — fictional observations':mode==='live'?'NASA response received — global query, coverage and authenticity unknown':'Retained evidence — not live')+' | '+m.capturedAt+' | browser replay matched; no independent Python replay.');if(mode==='live'&&r.total===200)$('earth-status').textContent+=' Event limit reached.';
 for(const rec of r.records){const [cx,cy]=project(rec.coordinates),dot=svg('circle',{cx,cy,r:4,class:'marker',tabindex:0,role:'button','aria-label':rec.title.slice(0,300)}),li=doc.createElement('li'),b=doc.createElement('button');b.textContent=rec.title.slice(0,300)+' — '+rec.date.slice(0,10);b.setAttribute('aria-pressed','false');const click=()=>select(rec,dot,b);dot.append(svg('title',{},rec.title.slice(0,300)));dot.addEventListener('click',click);dot.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();click();}});b.addEventListener('click',click);li.append(b);$('markers').append(dot);$('register').append(li);}$('download').disabled=false;mapGuide();local.accept(m,mode,$('category').value);}
 async function runEarth(work,mode){const id=++earthRev;clearEarth('Retrieving or validating observations...');for(const k of ['earth-refresh','category','import','demo'])$(k).disabled=true;try{const v=await work();if(id===earthRev)render(v,mode);}catch(e){if(id===earthRev)clearEarth('No observations accepted: '+String(e.message).slice(0,180));}finally{if(id===earthRev)for(const k of ['earth-refresh','category','import','demo'])$(k).disabled=false;}}
 function live(time=Date.now()){const x={...recentDates(time),category:$('category').value,radiusKm:50,facilities:[{id:'PUBLIC-REFERENCE',coordinates:[0,0]}]};return runEarth(()=>fetchStudy(x,transport),'live');}
 $('earth-refresh').addEventListener('click',()=>live());$('category').addEventListener('change',()=>live());$('reset').addEventListener('click',resetMap);$('zoom').addEventListener('click',focusMap);
 $('demo').addEventListener('click',()=>runEarth(async()=>{const bytes=await getBytes(await transport('data/earth-evidence-synthetic.json'),MAX_BUNDLE);const model=await inspectBundle(bytes);req(model.kind==='synthetic-demo','Not a synthetic example');return {bytes,model};},'demo'));
 $('import').addEventListener('click',()=>runEarth(async()=>{const f=$('bundle').files[0];req(f&&f.size>0&&f.size<=MAX_BUNDLE,'Choose an evidence JSON up to 26 MB');const bytes=new Uint8Array(await f.arrayBuffer());return {bytes,model:await inspectBundle(bytes)};},'import'));
 $('download').addEventListener('click',()=>{if(!current)return;const u=URL.createObjectURL(new Blob([current.bytes],{type:'application/json'})),a=doc.createElement('a');a.href=u;a.download='gaia-earth-'+current.model.digest.slice(0,12)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
 async function apod(){if($('apod-refresh').disabled)return;$('apod-refresh').disabled=true;$('apod-result').hidden=true;const image=$('apod-image');image.hidden=true;image.removeAttribute('src');text('apod-status','Retrieving APOD...');try{const d=await nasa('apod',transport),s=apodSummary(d),url=safeNasaImage(d);text('apod-title',s.title);text('apod-date','Recorded date: '+s.date+(s.fallback?' (fallback date)':''));const credit=plainCredit(d.copyright);text('apod-credit',credit?'Credit: '+credit:'Credit not supplied in response; consult the NASA record.');text('apod-text',typeof d.explanation==='string'?d.explanation.slice(0,3000):'No explanation provided.');image.alt=s.title;image.hidden=!url;if(url)image.src=url;$('apod-result').hidden=false;text('apod-status',url?'Record received. Image provided by the NASA-hosted record.':'Record received. No eligible NASA-hosted still image; use the NASA collection.');}catch(e){text('apod-status','No record accepted: '+String(e.message).slice(0,120));}finally{$('apod-refresh').disabled=false;}}
 $('apod-image').addEventListener('error',()=>{$('apod-image').hidden=true;text('apod-status','Record received, but the image failed to load.');});$('apod-refresh').addEventListener('click',apod);
 async function space(){const rev=++spaceRev,type=$('donki-type').value;$('donki-refresh').disabled=true;$('donki-type').disabled=true;$('donki-result').hidden=true;$('chart').replaceChildren();text('donki-status','Retrieving DONKI records...');try{const t=timeline(await nasa(type,transport),type);if(rev!==spaceRev)return;text('donki-count',t.count+' returned '+type.toUpperCase()+' records');text('donki-dates',t.undated+' records lack usable '+t.field+' UTC timestamps. '+(t.omittedDays?'Latest 14 observed dates shown; earlier dates omitted. ':'')+(t.days.length?t.days.map(([d,n])=>d+': '+n).join(' | '):t.count===0?'No records returned for this query.':'No usable dated records to plot.'));const c=$('chart'),max=Math.max(1,...t.days.map(x=>x[1])),step=432/Math.max(1,t.days.length);c.append(svg('path',{d:'M32 160H464',stroke:'#49677a',fill:'none'}));if(!t.days.length)c.append(svg('text',{x:240,y:100,'text-anchor':'middle',fill:'#b7cddd','font-size':14},t.count===0?'No records returned':'No usable dated records'));t.days.forEach(([day,n],i)=>{const x=32+i*step+step*.15,h=120*n/max,w=step*.7;c.append(svg('rect',{x,y:160-h,width:w,height:h,fill:'#91e0cb'}),svg('text',{x:x+w/2,y:154-h,fill:'#e9f4fc','font-size':11,'text-anchor':'middle'},String(n)),svg('text',{x:x+w/2,y:178,fill:'#b7cddd','font-size':9,'text-anchor':'middle'},day.slice(5)));});$('donki-result').hidden=false;text('donki-status','Collection received; coverage unknown.');}catch(e){if(rev===spaceRev)text('donki-status','No collection accepted: '+String(e.message).slice(0,120));}finally{if(rev===spaceRev){$('donki-refresh').disabled=false;$('donki-type').disabled=false;}}}
 $('donki-refresh').addEventListener('click',space);$('donki-type').addEventListener('change',space);return Promise.allSettled([live(now),apod(),space()]);
}
if(typeof document!=='undefined'&&document.getElementById('markers'))startDashboard();
