const {createHash} = require('node:crypto');
const BASE = 'https://eonet.gsfc.nasa.gov/api/v3/events';
const MAX = 2_000_000;
const DAY = 86400000;
const categories = new Set(['wildfires','severeStorms','volcanoes']);
function date(s) {
  if (typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(s)) throw Error('Invalid UTC date');
  const t = Date.parse(s+'T00:00:00Z');
  if (!Number.isFinite(t) || new Date(t).toISOString().slice(0,10)!==s || s<'0001-01-01' || s>='9999-12-31') throw Error('Invalid UTC date');
  return t;
}
function url(q) {
  if (!q || Object.keys(q).length!==3 || !['start','end','category'].every(k=>Object.hasOwn(q,k)) || !categories.has(q.category)) throw Error('Invalid query');
  const delta=date(q.end)-date(q.start);
  if (delta<0 || delta>29*DAY) throw Error('Choose 1-30 UTC dates');
  return BASE+'?'+new URLSearchParams({status:'all',start:q.start,end:q.end,category:q.category,limit:'200'});
}
async function retrieve(requestUrl, transport=fetch) {
  const r=await transport(requestUrl,{redirect:'error',signal:AbortSignal.timeout(12000),headers:{Accept:'application/json','Accept-Encoding':'identity'}});
  if (r.status!==200 || r.headers.get('content-type')?.split(';')[0].trim().toLowerCase()!=='application/json' || ![null,'identity'].includes(r.headers.get('content-encoding'))) throw Error('Invalid upstream response');
  const length=r.headers.get('content-length');
  if (length!==null && (!/^\d+$/.test(length)||Number(length)>MAX)) throw Error('Source exceeds size limit');
  const reader=r.body?.getReader();if(!reader)throw Error('Missing upstream body');
  let size=0;const chunks=[];
  try {while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>MAX)throw Error('Source exceeds size limit');chunks.push(value);}}
  finally {try{await reader.cancel();}catch{}}
  if(!size || (length!==null&&Number(length)!==size))throw Error('Incomplete upstream body');
  const raw=Buffer.concat(chunks,size), parsed=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));
  if(!Array.isArray(parsed?.events)||parsed.events.length>200)throw Error('Invalid event response');
  return {requestUrl,capturedAt:new Date().toISOString(),sourceSha256:createHash('sha256').update(raw).digest('hex'),bodyBase64:raw.toString('base64')};
}
async function handler(req,res){
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
  if(req.method!=='GET'){res.setHeader('Allow','GET');return res.status(405).json({error:'GET required'});}
  if(process.env.VERCEL_ENV!=='preview')return res.status(403).json({error:'Live retrieval is enabled only for preview deployments.'});
  let target;try{target=url(req.query);}catch(e){return res.status(400).json({error:e.message});}
  try{return res.status(200).json(await retrieve(target));}catch{return res.status(502).json({error:'NASA retrieval failed or returned invalid data. No observation was accepted.'});}
}
module.exports=handler;
module.exports.url=url;
module.exports.retrieve=retrieve;
