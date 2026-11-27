import {buildSiteBriefing,LAYERS,LABELS,PACKET_LIMIT} from './site-briefing.mjs';
import {compare,periods} from './portfolio.mjs';
const ok=(v,m)=>{if(!v)throw Error(m);};
const LIMIT='Differences describe returned matching event IDs, not new or resolved incidents, trends in hazard risk, or proof of safety. Geographic coverage and source authenticity remain unknown. Adjacent screening windows share their midnight endpoint. Same-method browser replay only.';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export async function compareSiteChange(recent,load,now=Date.now()){
 const r=recent?.report,w=r?.window,site=r?.site;
 ok(r?.schema==='gaia-site-briefing-v1'&&w?.hours===168&&Array.isArray(recent.bundles)&&recent.bundles.length>0&&recent.bundles.length<=3,'Run a site briefing with accepted evidence first.');
 const t=Date.parse(w.asOf);ok(Number.isFinite(t)&&new Date(t).toISOString()===w.asOf,'Invalid retained window');
 const windows=periods(t);ok(w.start===windows.current.start&&w.end===windows.current.end,'Retained dates differ');
 ok(new Set(recent.bundles.map(b=>b.category)).size===recent.bundles.length&&recent.bundles.every(b=>LAYERS.includes(b.category)),'Invalid retained categories');
 const earlier=await buildSiteBriefing(site,windows.previous,load,now);
 const rows=[],bundles=[];
 for(const category of LAYERS){
  const a=earlier.bundles.find(b=>b.category===category),b=recent.bundles.find(b=>b.category===category);
  const missing=[];if(!a)missing.push('earlier');if(!b)missing.push('recent');
  const withheld=(status,reason)=>({category,status,reason,previousCount:null,currentCount:null,onlyCurrent:null,onlyPrevious:null,sharedCount:null});
  if(missing.length){rows.push(withheld('PAIR_UNAVAILABLE','Missing accepted '+missing.join(' and ')+' evidence.'));continue;}
  try{
   const c=await compare(a.bytes,b.bytes),x=c.rows[0];
   ok(c.portfolio.category===category&&c.portfolio.radiusKm===site.radiusKm&&c.rows.length===1&&x.id==='BRIEFING-REFERENCE'&&same(x.coordinates,site.coordinates),'Site or category mismatch');
   ok(c.previous.start===windows.previous.start&&c.previous.end===windows.previous.end&&c.current.start===windows.current.start&&c.current.end===windows.current.end&&c.previous.bundleSha256===a.sha256&&c.current.bundleSha256===b.sha256,'Window or evidence mismatch');
   const comparable=c.comparison==='COMPARABLE_RETURNED_RECORDS';
   rows.push({category,status:c.comparison,reason:comparable?'Returned event ID sets compared.':c.previous.limitReached||c.current.limitReached?'Source record limit reached.':'At least one window has no eligible point observations.',previousCount:x.previousCount,currentCount:x.currentCount,onlyCurrent:comparable?x.currentMatches.filter(m=>x.onlyCurrent.includes(m.eventId)):null,onlyPrevious:x.onlyPrevious,sharedCount:comparable?x.currentCount-x.onlyCurrent.length:null,previous:c.previous,current:c.current});
   bundles.push({...a,window:'earlier'},{...b,window:'recent'});
  }catch{rows.push(withheld('REPLAY_REJECTED','Evidence replay or site/window validation failed.'));}
 }
 return {report:{schema:'gaia-site-change-v1',requestedAt:new Date(now).toISOString(),site:{coordinates:site.coordinates.slice(),radiusKm:site.radiusKm},windows,pairedSources:bundles.length/2,comparableSources:rows.filter(r=>r.status==='COMPARABLE_RETURNED_RECORDS').length,layers:rows,limitations:LIMIT},bundles};
}
export function canPackChange(v){return v.bundles.length>0&&v.bundles.reduce((n,b)=>n+b.bytes.length,0)<=PACKET_LIMIT;}
function base64(bytes){let s='';for(let i=0;i<bytes.length;i+=16384)s+=String.fromCharCode(...bytes.subarray(i,i+16384));return btoa(s);}
export function changePacket(v){ok(canPackChange(v),'No replayed pairs or combined evidence size limit exceeded');return {schema:'gaia-site-change-packet-v1',report:v.report,evidence:v.bundles.map(b=>({category:b.category,window:b.window,sha256:b.sha256,bytes:b.bytes.length,base64:base64(b.bytes)}))};}
export function startSiteChange(doc=document,{load,clock=()=>Date.now(),download}={}){
 if(!doc.querySelector?.('#site-change'))return {clear(){},accept(){}};
 const $=id=>doc.getElementById(id),node=(tag,t)=>{const e=doc.createElement(tag);e.textContent=t;return e;};let rev=0,busy=false,recent=null,result=null;
 const save=download||((data,name,type)=>{const url=URL.createObjectURL(new Blob([data],{type})),a=doc.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 function buttons(){$('change-run').disabled=busy||!recent;}
 function clear(){rev++;recent=null;result=null;$('change-result').hidden=true;$('change-rows').replaceChildren();$('change-report').disabled=true;$('change-packet').disabled=true;$('change-status').textContent='Run a site briefing first.';buttons();}
 function accept(v){clear();if(v.bundles.length){recent=v;$('change-status').textContent='Compare the accepted recent window with the preceding seven UTC dates. Three additional source requests.';buttons();}}
 function render(v){result=v;const r=v.report,w=r.windows;$('change-window').textContent=`Earlier ${w.previous.start} through ${w.previous.end} | Recent ${w.current.start} through ${w.current.end} UTC`;
  $('change-status').textContent=`${r.comparableSources} of 3 categories support a returned-record comparison; ${r.pairedSources} evidence pairs replayed.`;
  for(const row of r.layers){const tr=doc.createElement('tr'),h=node('th',LABELS[row.category]);h.scope='row';tr.append(h,node('td',row.previousCount??'Unavailable'),node('td',row.currentCount??'Unavailable'));
   const recentCell=node('td',row.onlyCurrent===null?'Withheld':String(row.onlyCurrent.length));if(row.onlyCurrent?.length){const list=doc.createElement('ul');for(const m of row.onlyCurrent.slice(0,10))list.append(node('li',`${m.title} | ${m.distanceKm.toFixed(1)} km | ${m.observedAt}`));recentCell.append(list);if(row.onlyCurrent.length>10)recentCell.append(node('p','Additional matches in report.'));}
   const earlierCell=node('td',row.onlyPrevious===null?'Withheld':String(row.onlyPrevious.length));if(row.onlyPrevious?.length)earlierCell.append(node('p','Event IDs in report.'));
   const evidence=node('td',row.reason);for(const b of v.bundles.filter(b=>b.category===row.category)){const button=node('button','Download '+b.window+' bundle');button.type='button';button.addEventListener('click',()=>{if(result===v)save(b.bytes,`gaia-${b.category}-${b.window}-${b.sha256.slice(0,12)}.json`,'application/json');});evidence.append(button);}
   tr.append(recentCell,earlierCell,node('td',row.sharedCount??'Withheld'),evidence);$('change-rows').append(tr);
  }
  $('change-result').hidden=false;$('change-report').disabled=false;$('change-packet').disabled=!canPackChange(v);$('change-export-status').textContent=canPackChange(v)?'Evidence packet contains the exact replayed pairs. Downloads include coordinates.':v.bundles.length?'Package exceeds the size limit; download individual bundles.':'No replayed evidence pairs; only the attempt report is available.';
 }
 async function run(){if(busy||!recent)return;const token=++rev,v=recent;result=null;$('change-result').hidden=true;$('change-rows').replaceChildren();$('change-report').disabled=true;$('change-packet').disabled=true;busy=true;buttons();$('change-status').textContent='Retrieving earlier observations and replaying evidence pairs…';
  try{const out=await compareSiteChange(v,load,clock());if(token===rev)render(out);}catch{if(token===rev)$('change-status').textContent='Comparison unavailable. Run the recent briefing again.';}finally{busy=false;buttons();}}
 $('change-run').addEventListener('click',run);$('change-report').addEventListener('click',()=>{if(result)save(JSON.stringify(result.report,null,2),'gaia-site-change.json','application/json');});$('change-packet').addEventListener('click',()=>{if(result&&canPackChange(result))save(JSON.stringify(changePacket(result)),'gaia-site-change-evidence.json','application/json');});clear();return {clear,accept,run};
}
