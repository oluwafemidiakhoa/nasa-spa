import {screen} from './earth.mjs';
const CITIES=Object.freeze({Houston:[-95.3698,29.7604],'Los Angeles':[-118.2437,34.0522],Lagos:[3.3792,6.5244],London:[-0.1276,51.5072],Tokyo:[139.6917,35.6895]});
export function localReview(model,mode,category,facility,radiusKm){
 if(!model||!['live','demo','import'].includes(mode))throw Error('No accepted observation bundle');
 const p=model.results[0].parameters;
 const basis=model.kind==='synthetic-demo'?'SYNTHETIC (fictional)':mode==='live'?'Current retrieval (coverage unknown)':'Retained evidence (not live)';
 return {schema:'gaia-local-screen-v1',basis,category:mode==='live'?category:null,sourceBundleSha256:model.digest,sourceSha256:model.sourceHash,capturedAt:model.capturedAt,sourceLimitReached:mode==='live'?model.snapshot.events.length===200:null,...screen(model.snapshot,{facility,asOf:p.asOf,hours:p.hours,radiusKm})};
}
export function summarize(r){
 if(r.status==='NO_ELIGIBLE_POINTS')return 'Unavailable: no eligible point observations in the returned records. No absence or safety conclusion.';
 if(r.status==='NO_MATCH_IN_AVAILABLE_POINTS')return '0 matching events in available points. Coverage is unknown; this does not establish safety.';
 return r.matches.length+' matching event(s); nearest retained point '+r.matches[0].distanceKm.toFixed(1)+' km away. Inspect the observations below, not a hazard footprint.';
}
export function startLocalScreen(doc=document){
 if(!doc.querySelector?.('#local-screen'))return {clear(){},accept(){}};
 const $=id=>doc.getElementById(id);let accepted=null,report=null;
 function clear(message){accepted=null;report=null;$('local-result').textContent=message;$('local-source').textContent='';$('local-rows').replaceChildren();$('local-download').disabled=true;}
 function render(){
  report=null;$('local-download').disabled=true;$('local-rows').replaceChildren();$('local-source').textContent='';
  if(!accepted){$('local-result').textContent='Waiting for accepted observations. Refresh the selected Earth layer.';return;}
  try{
   const lon=$('local-lon').value.trim(),lat=$('local-lat').value.trim(),radius=Number($('local-radius').value);
   if(!lon||!lat)throw Error('Enter both longitude and latitude.');
   const r=localReview(accepted.model,accepted.mode,accepted.category,[Number(lon),Number(lat)],radius);
   report=r;$('local-result').textContent=summarize(r);
   $('local-source').textContent=r.basis+' | '+(r.category||'Category not asserted for retained/demo evidence')+' | '+r.coverage.eligiblePoints+' eligible global points | '+new Date(Date.parse(r.parameters.asOf)-r.parameters.hours*3600000).toISOString()+' to '+r.parameters.asOf+' UTC | captured '+r.capturedAt+(r.sourceLimitReached?' | SOURCE LIMIT REACHED':'');
   for(const m of r.matches.slice(0,10)){const li=doc.createElement('li');li.textContent=m.title+' | '+m.distanceKm.toFixed(1)+' km | '+m.observedAt; $('local-rows').append(li);}
   $('local-download').disabled=false;
  }catch(e){$('local-result').textContent='Screen unavailable: '+String(e.message).slice(0,160);}
 }
 $('local-city').addEventListener('change',()=>{const city=$('local-city').value;if(Object.hasOwn(CITIES,city)){[$('local-lon').value,$('local-lat').value]=CITIES[city].map(String);}render();});
 for(const id of ['local-lon','local-lat'])$(id).addEventListener('input',()=>{$('local-city').value='custom';render();});
 $('local-radius').addEventListener('change',render);
 $('local-download').addEventListener('click',()=>{if(!report)return;const u=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),a=doc.createElement('a');a.href=u;a.download='gaia-local-screen-'+report.sourceBundleSha256.slice(0,12)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
 clear('Waiting for accepted observations. Refresh the selected Earth layer.');
 return {clear,accept(model,mode,category){accepted={model,mode,category};render();}};
}
