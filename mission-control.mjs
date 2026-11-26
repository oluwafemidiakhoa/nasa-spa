import {fetchStudy,recentDates} from './workspace.mjs';
const MAX=1_000_000;
export function apodSummary(data){
  if(!data||typeof data.title!=='string'||!data.title.trim()||data.title.length>500||typeof data.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(data.date)||!Number.isFinite(Date.parse(data.date+'T00:00:00Z'))||new Date(data.date+'T00:00:00Z').toISOString().slice(0,10)!==data.date)throw Error('APOD response has no valid title/date');
  return {title:data.title,date:data.date,fallback:data.fallback_used===true};
}
export function donkiCount(data){if(!Array.isArray(data)||data.length>5000||data.some(x=>!x||typeof x!=='object'||Array.isArray(x)))throw Error('Invalid DONKI record collection');return data.length;}
export async function readFeed(type,transport=fetch){
  if(!['apod','cme','flr','gst'].includes(type))throw Error('Unknown collection');
  const r=await transport('/api/nasa?type='+type,{cache:'no-store',signal:AbortSignal.timeout(20000)});
  if(!r.ok||!r.body)throw Error('Source unavailable (HTTP '+r.status+')');
  const reader=r.body.getReader(),chunks=[];let n=0;try{while(true){const {done,value}=await reader.read();if(done)break;n+=value.byteLength;if(n>MAX)throw Error('Response exceeds display limit');chunks.push(value);}}finally{try{await reader.cancel();}catch{}}
  const bytes=new Uint8Array(n);let i=0;for(const c of chunks){bytes.set(c,i);i+=c.length;}const data=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));return type==='apod'?apodSummary(data):donkiCount(data);
}
// Reuse the unchanged, bounded screening and archive validation path. The public
// reference coordinate is only used locally; overview counts describe all returned events.
export async function readEarth(transport=fetch,now=Date.now()){
  const dates=recentDates(now),x={...dates,category:'wildfires',radiusKm:50,facilities:[{id:'LOS-ANGELES',coordinates:[-118.2437,34.0522]}]};
  const {model}=await fetchStudy(x,transport),c=model.results[0].coverage;
  return {...dates,count:c.events,eligible:c.eligiblePoints,capturedAt:model.capturedAt,capReached:c.events===200,events:model.snapshot.events.slice(0,6).map(e=>e.title.slice(0,300))};
}
export function startMissionControl(doc=document,transport=fetch,now=Date.now()){
  const $=id=>doc.getElementById(id);let version=0;
  for(const id of ['apod','donki','earth-refresh'])$(id).disabled=false;
  async function earth(time=Date.now()){
    if($('earth-refresh').disabled)return;$('earth-refresh').disabled=true;$('earth-result').hidden=true;$('earth-events').replaceChildren();$('earth-status').textContent='Retrieving EONET wildfires...';
    try{const v=await readEarth(transport,time);$('earth-count').textContent=v.count+' returned event records | '+v.eligible+' eligible point rows';$('earth-window').textContent='Global wildfire query: '+v.start+' through '+v.end+' UTC.';$('earth-capture').textContent='Recorded retrieval: '+v.capturedAt+(v.capReached?' | 200-event limit reached.':'');for(const title of v.events){const li=doc.createElement('li');li.textContent=title;$('earth-events').append(li);}$('earth-result').hidden=false;$('earth-status').textContent='Browser consistency check matched. Showing up to six returned event titles; coverage and authenticity unknown.';}catch(e){$('earth-status').textContent='No observations accepted: '+String(e.message).slice(0,120);}finally{$('earth-refresh').disabled=false;}
  }
  async function apod(){if($('apod').disabled)return;$('apod').disabled=true;$('apod-result').hidden=true;$('apod-status').textContent='Retrieving APOD...';try{const v=await readFeed('apod',transport);$('apod-title').textContent=v.title;$('apod-date').textContent='Recorded date: '+v.date+(v.fallback?' (API fallback date)':'');$('apod-result').hidden=false;$('apod-status').textContent='Record received. Not independently verified.';}catch(e){$('apod-status').textContent='No record accepted: '+String(e.message).slice(0,120);}finally{$('apod').disabled=false;}}
  async function donki(){if($('donki').disabled)return;const run=++version,type=$('donki-type').value;$('donki').disabled=true;$('donki-result').hidden=true;$('donki-status').textContent='Retrieving DONKI collection...';try{const n=await readFeed(type,transport);if(run!==version)return;$('donki-count').textContent=n+' returned records ('+type.toUpperCase()+')';$('donki-result').hidden=false;$('donki-status').textContent='Record collection received. Coverage unknown.';}catch(e){if(run===version)$('donki-status').textContent='No collection accepted: '+String(e.message).slice(0,120);}finally{if(run===version)$('donki').disabled=false;}}
  $('earth-refresh').addEventListener('click',()=>earth());$('apod').addEventListener('click',apod);$('donki').addEventListener('click',donki);
  $('donki-type').addEventListener('change',()=>{version++;$('donki-result').hidden=true;$('donki-status').textContent='Collection changed. Retrieve records again.';$('donki').disabled=false;});
  return Promise.allSettled([earth(now),apod(),donki()]);
}
if(typeof document!=='undefined'&&document.getElementById('apod'))startMissionControl();
