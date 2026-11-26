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
class AcquisitionError extends Error {
  constructor(code){super(code);this.code=code;}
}
function fail(code){throw new AcquisitionError(code);}
function networkCode(e){
  const code=e?.cause?.code || e?.code;
  if(e?.name==='TimeoutError'||e?.name==='AbortError'||['ETIMEDOUT','UND_ERR_CONNECT_TIMEOUT','UND_ERR_HEADERS_TIMEOUT','UND_ERR_BODY_TIMEOUT'].includes(code))return 'UPSTREAM_TIMEOUT';
  if(['ENOTFOUND','EAI_AGAIN'].includes(code))return 'UPSTREAM_DNS';
  if(['CERT_HAS_EXPIRED','UNABLE_TO_VERIFY_LEAF_SIGNATURE','SELF_SIGNED_CERT_IN_CHAIN','ERR_TLS_CERT_ALTNAME_INVALID','DEPTH_ZERO_SELF_SIGNED_CERT'].includes(code))return 'UPSTREAM_TLS';
  return 'UPSTREAM_NETWORK';
}
async function retrieve(requestUrl, transport=fetch) {
  let r;
  try{r=await transport(requestUrl,{redirect:'error',signal:AbortSignal.timeout(12000),headers:{Accept:'application/json','Accept-Encoding':'identity','User-Agent':'Gaia-Observatory/1.0'}});}catch(e){fail(networkCode(e));}
  if(r.status!==200)fail(Number.isInteger(r.status)&&r.status>=100&&r.status<=599?'UPSTREAM_HTTP_'+r.status:'UPSTREAM_STATUS');
  const mime=(r.headers.get('content-type')||'').split(';')[0].trim().toLowerCase();
  const jsonMime=mime==='application/json'||/^application\/[a-z0-9.+-]+\+json$/.test(mime);
  // Node fetch decodes HTTP content encodings. Content-Length describes the
  // encoded representation, so only compare it to decoded bytes for identity.
  const encoding=(r.headers.get('content-encoding')||'identity').trim().toLowerCase();
  if(!['identity','gzip','deflate','br'].includes(encoding))fail('UPSTREAM_ENCODING');
  const length=r.headers.get('content-length');
  if(length!==null&&(!/^\d+$/.test(length)||Number(length)>MAX))fail('UPSTREAM_SIZE');
  const reader=r.body?.getReader();if(!reader)fail('UPSTREAM_EMPTY');
  let size=0;const chunks=[];
  try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>MAX)fail('UPSTREAM_SIZE');chunks.push(value);}}
  catch(e){if(e instanceof AcquisitionError)throw e;const code=networkCode(e);fail(code==='UPSTREAM_NETWORK'?'UPSTREAM_BODY':code);}
  finally{try{await reader.cancel();}catch{}}
  if(!size)fail('UPSTREAM_EMPTY');
  if(encoding==='identity'&&length!==null&&Number(length)!==size)fail('UPSTREAM_TRUNCATED');
  const raw=Buffer.concat(chunks,size);let parsed;
  try{const {strictJSON}=await import('../facility.mjs');parsed=strictJSON(raw);}catch{fail(jsonMime?'UPSTREAM_JSON':'UPSTREAM_CONTENT_TYPE');}
  if(!Array.isArray(parsed?.events)||parsed.events.length>200)fail(jsonMime?'UPSTREAM_SCHEMA':'UPSTREAM_CONTENT_TYPE');
  if(!jsonMime){
    // MIME is not evidence of content validity. A mislabeled response is accepted
    // only if it has the complete official EONET envelope and valid observation data.
    try{
      const link=new URL(parsed.link);
      if(parsed.title!=='EONET Events'||typeof parsed.description!=='string'||link.origin!=='https://eonet.gsfc.nasa.gov'||link.pathname!=='/api/v3/events'||link.username||link.password||link.hash)throw Error('Unexpected envelope');
      const {screen}=await import('../earth.mjs');screen(parsed,{facility:[0,0],asOf:'2000-01-02T00:00:00Z',hours:24,radiusKm:1});
    }catch{fail('UPSTREAM_CONTENT_TYPE');}
  }
  return {requestUrl,capturedAt:new Date().toISOString(),sourceSha256:createHash('sha256').update(raw).digest('hex'),bodyBase64:raw.toString('base64')};
}
async function handler(req,res){
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
  if(req.method!=='GET'){res.setHeader('Allow','GET');return res.status(405).json({error:'GET required'});}
  if(!['preview','production'].includes(process.env.VERCEL_ENV))return res.status(403).json({error:'Live retrieval is enabled only on Vercel Preview and Production.'});
  let target;try{target=url(req.query);}catch(e){return res.status(400).json({error:e.message});}
  try{const result=await retrieve(target);if(process.env.VERCEL_ENV==='production')res.setHeader('Vercel-CDN-Cache-Control','public, s-maxage=180');return res.status(200).json(result);}catch(e){const code=e instanceof AcquisitionError?e.code:'UPSTREAM_INTERNAL';console.warn('GAIA_EONET_FAILURE '+code);return res.status(502).json({error:'NASA retrieval failed or returned invalid data. No observation was accepted.',code});}
}
module.exports=handler;
module.exports.url=url;
module.exports.retrieve=retrieve;
