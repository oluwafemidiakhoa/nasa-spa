const TYPES={cme:{id:'activityID',time:'startTime'},flr:{id:'flrID',time:'peakTime'},gst:{id:'gstID',time:'startTime'}};
function timestamp(s){if(typeof s!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?Z$/.test(s))return null;const t=Date.parse(s);return Number.isFinite(t)&&new Date(t).toISOString().slice(0,16)===s.slice(0,16)?new Date(t).toISOString():null;}
function bounded(s){return typeof s==='string'&&s.trim()?s.trim().slice(0,180):null;}
function measurements(r,type){
 if(type==='flr')return typeof r.classType==='string'&&/^[ABCMX]\d+(?:\.\d+)?$/.test(r.classType)?'Reported flare class: '+r.classType:'Flare class not supplied';
 if(type==='cme'){const values=Array.isArray(r.cmeAnalyses)?r.cmeAnalyses.filter(x=>x&&Number.isFinite(x.speed)&&x.speed>0&&x.speed<=10000).map(x=>x.speed):[];return values.length?'Reported analysis speed: '+Math.min(...values)+'–'+Math.max(...values)+' km/s ('+values.length+' analyses; not arrival prediction)':'No usable reported analysis speed';}
 const values=Array.isArray(r.allKpIndex)?r.allKpIndex.filter(x=>x&&Number.isFinite(x.kpIndex)&&x.kpIndex>=0&&x.kpIndex<=9).map(x=>x.kpIndex):[];
 return values.length?'Maximum reported Kp: '+Math.max(...values)+' ('+values.length+' entries)':'No usable reported Kp';
}
export function eventRows(data,type){
 if(!Object.hasOwn(TYPES,type)||!Array.isArray(data)||data.length>5000||data.some(x=>!x||typeof x!=='object'||Array.isArray(x)))throw Error('Invalid event collection');
 const spec=TYPES[type];return data.map((r,i)=>({id:bounded(r[spec.id]),time:timestamp(r[spec.time]),detail:measurements(r,type),index:i})).sort((a,b)=>(b.time||'').localeCompare(a.time||'')||a.index-b.index);
}
export function startSpaceRecords(doc=document){
 if(!doc.querySelector?.('#space-records'))return {clear(){},accept(){}};
 const $=id=>doc.getElementById(id);let current=null;
 function clear(){current=null;$('space-rows').replaceChildren();$('space-record-status').textContent='Waiting for accepted records.';$('space-export').disabled=true;}
 function accept(data,type){clear();const rows=eventRows(data,type);current={data,type};$('space-record-status').textContent=rows.length?'Showing '+Math.min(50,rows.length)+' of '+rows.length+' returned records. Missing fields are not inferred.':'No records returned for this query.';
  for(const row of rows.slice(0,50)){const tr=doc.createElement('tr');for(const value of [row.id||'ID not supplied',row.time||'UTC time unavailable',row.detail]){const td=doc.createElement('td');td.textContent=value;tr.append(td);}$('space-rows').append(tr);}$('space-export').disabled=false;}
 $('space-export').addEventListener('click',()=>{if(!current)return;const u=URL.createObjectURL(new Blob([JSON.stringify(current.data,null,2)],{type:'application/json'})),a=doc.createElement('a');a.href=u;a.download='gaia-donki-'+current.type+'-returned.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});clear();return {clear,accept};
}
