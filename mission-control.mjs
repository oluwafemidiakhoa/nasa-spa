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
function start(){
  const $=id=>document.getElementById(id);let version=0;
  for(const type of ['apod','donki']){$(type).disabled=false;$(type+'-status').textContent='Ready to request records.';}
  $('apod').addEventListener('click',async()=>{if($('apod').disabled)return;$('apod').disabled=true;$('apod-result').hidden=true;$('apod-status').textContent='Retrieving APOD...';try{const v=await readFeed('apod');$('apod-title').textContent=v.title;$('apod-date').textContent='Recorded date: '+v.date+(v.fallback?' (API fallback date)':'');$('apod-result').hidden=false;$('apod-status').textContent='Record received. Not independently verified.';}catch(e){$('apod-status').textContent='No record accepted: '+String(e.message).slice(0,120);}finally{$('apod').disabled=false;}});
  $('donki-type').addEventListener('change',()=>{version++;$('donki-result').hidden=true;$('donki-status').textContent='Collection changed. Retrieve records again.';$('donki').disabled=false;});
  $('donki').addEventListener('click',async()=>{if($('donki').disabled)return;const run=++version,type=$('donki-type').value;$('donki').disabled=true;$('donki-result').hidden=true;$('donki-status').textContent='Retrieving DONKI collection...';try{const n=await readFeed(type);if(run!==version)return;$('donki-count').textContent=n+' returned records ('+type.toUpperCase()+')';$('donki-result').hidden=false;$('donki-status').textContent='Record collection received. Coverage unknown.';}catch(e){if(run===version)$('donki-status').textContent='No collection accepted: '+String(e.message).slice(0,120);}finally{if(run===version)$('donki').disabled=false;}});
}
if(typeof document!=='undefined'&&document.getElementById('apod'))start();
