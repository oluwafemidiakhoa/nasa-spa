import {study,fetchStudy,recentDates} from './workspace.mjs';
import {inspectBundle,strictJSON,MAX_BUNDLE} from './facility.mjs';
const DAY=86400000, KEY='gaia-portfolio-v1';
const req=(ok,msg)=>{if(!ok)throw Error(msg);};
const fields=(x,ks)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===ks.length&&ks.every(k=>Object.hasOwn(x,k));
export function portfolio(input){
  req(fields(input,['category','radiusKm','facilities']),'Invalid portfolio fields');
  study({...input,start:'2025-01-01',end:'2025-01-07'});
  return {category:input.category,radiusKm:input.radiusKm,facilities:input.facilities.map(f=>({id:f.id,coordinates:f.coordinates.slice()})).sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0)};
}
export function periods(now=Date.now()){
  const current=recentDates(now),t=Date.parse(current.start+'T00:00:00Z');
  const date=n=>new Date(t+n*DAY).toISOString().slice(0,10);
  return {previous:{start:date(-7),end:date(-1)},current};
}
export function restore(storage){const raw=storage.getItem(KEY);if(raw===null)return null;req(typeof raw==='string'&&raw.length<=12000,'Invalid saved portfolio size');return portfolio(JSON.parse(raw));}
export function save(storage,x){storage.setItem(KEY,JSON.stringify(portfolio(x)));}
export function forget(storage){storage.removeItem(KEY);}
async function verified(bytes){
  const m=await inspectBundle(bytes);
  const b=strictJSON(bytes),a=strictJSON(Uint8Array.from(atob(b.files.archive.base64),c=>c.charCodeAt(0)));
  const q=a.receipt.query;
  req(m.kind==='user-import-unverified'&&m.mode==='https-eonet'&&q&&q.limit===200,'Comparison requires two retained EONET retrieval bundles with limit 200');
  const p=m.results[0].parameters;
  req(p.hours===168&&Date.parse(q.end+'T00:00:00Z')-Date.parse(q.start+'T00:00:00Z')===6*DAY&&Date.parse(p.asOf)===Date.parse(q.end+'T00:00:00Z')+DAY,'Expected matching seven-day query and screening window');
  return {m,q,capped:a.receipt.limitReached,config:portfolio({category:q.category,radiusKm:p.radiusKm,facilities:m.results.map(r=>({id:r.facilityId,coordinates:r.parameters.facility}))})};
}
export async function compare(previous,current){
  const [a,b]=await Promise.all([verified(previous),verified(current)]);
  req(JSON.stringify(a.config)===JSON.stringify(b.config),'Portfolio, category or radius differs between bundles');
  req(Date.parse(b.q.start+'T00:00:00Z')-Date.parse(a.q.start+'T00:00:00Z')===7*DAY,'Windows must be adjacent, earlier bundle first');
  const source=x=>({bundleSha256:x.m.digest,sourceSha256:x.m.sourceHash,capturedAt:x.m.capturedAt,start:x.q.start,end:x.q.end,eligiblePoints:x.m.results[0].coverage.eligiblePoints,eventRecords:x.m.results[0].coverage.events,limitReached:x.capped});
  const comparable=!a.capped&&!b.capped&&a.m.results[0].coverage.eligiblePoints>0&&b.m.results[0].coverage.eligiblePoints>0;
  const rows=b.m.results.map((r,i)=>{const p=a.m.results[i],pa=new Set(p.matches.map(m=>m.eventId)),pb=new Set(r.matches.map(m=>m.eventId));return {id:r.facilityId,coordinates:r.parameters.facility,previousCount:p.status==='NO_ELIGIBLE_POINTS'?null:p.matches.length,currentCount:r.status==='NO_ELIGIBLE_POINTS'?null:r.matches.length,nearestCurrentKm:r.matches[0]?.distanceKm??null,currentMatches:r.matches,onlyCurrent:comparable?r.matches.filter(m=>!pa.has(m.eventId)).map(m=>m.eventId):null,onlyPrevious:comparable?p.matches.filter(m=>!pb.has(m.eventId)).map(m=>m.eventId):null};});
  return {schema:'gaia-portfolio-review-v1',portfolio:a.config,previous:source(a),current:source(b),comparison:comparable?'COMPARABLE_RETURNED_RECORDS':'INSUFFICIENT_OBSERVATIONS_OR_LIMIT',rows,limitations:'Descriptive comparison of returned point records, not new incidents, hazard risk, exposure or safety. Coverage and authenticity unknown. Adjacent screening windows share their midnight endpoint. Same-method browser replay only.'};
}
export async function review(input,transport=fetch,now=Date.now()){
  const p=portfolio(input),w=periods(now);
  // Two bounded global queries; no site coordinates are sent.
  const [a,b]=await Promise.all([fetchStudy({...p,...w.previous},transport),fetchStudy({...p,...w.current},transport)]);
  return {previous:a.bytes,current:b.bytes,report:await compare(a.bytes,b.bytes)};
}
export function startPortfolio(doc=document,transport=fetch,storage=()=>localStorage,now=()=>Date.now()){
  const $=id=>doc.getElementById(id),status=s=>{$('status').textContent=s;};let revision=0,result=null,busy=false;
  function input(){return portfolio({category:$('category').value,radiusKm:Number($('radius').value),facilities:$('locations').value.split(/\r?\n/).filter(s=>s.trim()).map(s=>{const v=s.split(',').map(x=>x.trim());req(v.length===3&&v.every(Boolean),'Use ID, longitude, latitude');return {id:v[0],coordinates:v.slice(1).map(Number)};})});}
  function fill(p){$('category').value=p.category;$('radius').value=String(p.radiusKm);$('locations').value=p.facilities.map(f=>[f.id,...f.coordinates].join(', ')).join('\n');}
  function clear(s){revision++;result=null;busy=false;$('results').hidden=true;$('rows').replaceChildren();$('run').disabled=false;$('reopen').disabled=false;status(s);return revision;}
  function render(v){result=v;const r=v.report;$('window').textContent=r.previous.start+' to '+r.previous.end+' vs '+r.current.start+' to '+r.current.end+' UTC';$('coverage').textContent=r.previous.eligiblePoints+' / '+r.current.eligiblePoints+' eligible global point rows (earlier / recent). '+(r.previous.limitReached||r.current.limitReached?'Source limit reached. ':'')+(r.comparison==='COMPARABLE_RETURNED_RECORDS'?'Returned record sets compared; coverage unknown.':'Comparison withheld: insufficient observations or source limit.');$('rows').replaceChildren();for(const row of r.rows){const tr=doc.createElement('tr');for(const value of [row.id,row.previousCount??'Unavailable',row.currentCount??'Unavailable',row.onlyCurrent?.length??'Withheld',row.nearestCurrentKm===null?'—':row.nearestCurrentKm+' km']){const td=doc.createElement('td');td.textContent=String(value);tr.append(td);}const td=doc.createElement('td');for(const m of row.currentMatches.slice(0,5)){const p=doc.createElement('p');p.textContent=m.title+' · '+m.observedAt+' · '+m.distanceKm+' km';td.append(p);}if(!row.currentMatches.length)td.textContent='No matching returned points';tr.append(td);$('rows').append(tr);}$('digests').textContent='Earlier bundle: '+r.previous.bundleSha256+' | Recent bundle: '+r.current.bundleSha256;$('results').hidden=false;status('Review ready. Download both original evidence bundles and the derived report.');}
  async function run(work){if(busy)return;const rev=clear('Retrieving or checking observations…');busy=true;$('run').disabled=true;$('reopen').disabled=true;try{const v=await work();if(rev===revision)render(v);}catch(e){if(rev===revision)clear('Review unavailable: '+String(e.message).slice(0,180));}finally{if(rev===revision){busy=false;$('run').disabled=false;$('reopen').disabled=false;}}}
  function download(bytes,name){const url=URL.createObjectURL(new Blob([bytes],{type:'application/json'})),a=doc.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  for(const id of ['category','radius','locations','previous-file','current-file'])$(id).addEventListener('input',()=>clear('Inputs changed. Run or reopen a review.'));
  $('save').addEventListener('click',()=>{try{save(storage(),input());status('Portfolio saved on this browser. Do not use sensitive site coordinates on shared devices.');}catch(e){status('Not saved: '+String(e.message).slice(0,140));}});
  $('forget').addEventListener('click',()=>{try{forget(storage());$('locations').value='';clear('Saved portfolio removed from this browser.');}catch{status('Could not remove browser storage.');}});
  $('example').addEventListener('click',()=>{fill({category:'wildfires',radiusKm:50,facilities:[{id:'LOS-ANGELES',coordinates:[-118.2437,34.0522]},{id:'PASADENA',coordinates:[-118.1445,34.1478]},{id:'SAN-DIEGO',coordinates:[-117.1611,32.7157]}]});clear('Public city-center examples loaded, not industrial sites.');});
  $('form').addEventListener('submit',e=>{e.preventDefault();run(()=>review(input(),transport,now()));});
  $('reopen').addEventListener('click',()=>run(async()=>{const files=[$('previous-file').files[0],$('current-file').files[0]];req(files.every(f=>f&&f.size>0&&f.size<=MAX_BUNDLE),'Choose two evidence bundles, each at most 26 MB');const [previous,current]=await Promise.all(files.map(async f=>new Uint8Array(await f.arrayBuffer())));return {previous,current,report:await compare(previous,current)};}));
  for(const [id,k] of [['download-previous','previous'],['download-current','current'],['download-report','report']])$(id).addEventListener('click',()=>{if(result)download(k==='report'?JSON.stringify(result.report,null,2)+'\n':result[k],'gaia-'+k+'.json');});
  clear('Enter locations or choose the public example. No data has been requested.');try{const p=restore(storage());if(p){fill(p);status('Saved portfolio restored. Run a new review for recent observations.');}}catch{status('Saved portfolio unavailable. Enter locations again.');}
}
if(typeof document!=='undefined'&&document.getElementById('portfolio-page'))startPortfolio();
