const {createHash}=require('node:crypto');
const BASE='https://firms.modaps.eosdis.nasa.gov/api/area/csv/';
// The credential is used only in the fixed upstream HTTPS path; never log the URL,
// original exception, credential, or upstream error text. No redirect following.
async function retrieve(id,key,transport=fetch){
 const {region,SOURCE,MAX_CSV,parseFirms}=await import('../firms-core.mjs');
 const {bounds}=region(id);if(typeof key!=='string'||! /^[A-Za-z0-9_-]{16,128}$/.test(key))throw Error('KEY_NOT_CONFIGURED');
 const target=BASE+encodeURIComponent(key)+'/'+SOURCE+'/'+bounds.join(',')+'/1';
 let r;try{r=await transport(target,{redirect:'error',signal:AbortSignal.timeout(12000),headers:{Accept:'text/csv, application/csv, text/plain','Accept-Encoding':'identity','User-Agent':'Gaia-Observatory/1.0'}});}catch{throw Error('UPSTREAM_NETWORK');}
 if(r.status!==200)throw Error('UPSTREAM_HTTP');
 const ct=r.headers.get('content-type')?.split(';')[0].trim().toLowerCase();if(!['text/csv','application/csv','text/plain','application/octet-stream'].includes(ct))throw Error('UPSTREAM_CONTENT');
 const len=r.headers.get('content-length');if(len!==null&&(!/^\d+$/.test(len)||Number(len)>MAX_CSV))throw Error('UPSTREAM_LIMIT');
 const enc=(r.headers.get('content-encoding')||'identity').trim().toLowerCase();if(!['identity','gzip','deflate','br'].includes(enc))throw Error('UPSTREAM_CONTENT');
 const reader=r.body?.getReader();if(!reader)throw Error('UPSTREAM_BODY');let n=0;const chunks=[];
 try{while(true){const {done,value}=await reader.read();if(done)break;n+=value.byteLength;if(n>MAX_CSV)throw Error('UPSTREAM_LIMIT');chunks.push(value);}}catch(e){throw Error(e.message==='UPSTREAM_LIMIT'?'UPSTREAM_LIMIT':'UPSTREAM_BODY');}finally{try{await reader.cancel();}catch{}}
 if(!n||(enc==='identity'&&len!==null&&Number(len)!==n))throw Error('UPSTREAM_BODY');const bytes=Buffer.concat(chunks,n);
 // Only accepted CSV is released; even a credential reflected in a valid-looking
 // response is rejected. No response URL or response headers are returned.
 if(bytes.includes(Buffer.from(key)))throw Error('UPSTREAM_DATA');
 try{parseFirms(bytes,id);}catch{throw Error('UPSTREAM_DATA');}
 return {schema:'gaia-firms-v1',region:id,source:SOURCE,dayRange:1,capturedAt:new Date().toISOString(),sourceSha256:createHash('sha256').update(bytes).digest('hex'),bodyBase64:bytes.toString('base64'),coverage:'unknown',sourceAuthenticated:false};
}
async function handler(req,res){
 res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
 if(req.method!=='GET'){res.setHeader('Allow','GET');return res.status(405).json({code:'METHOD_NOT_ALLOWED'});}
 if(process.env.VERCEL_ENV!=='preview')return res.status(403).json({code:'PREVIEW_ONLY'});
 try{const {region}=await import('../firms-core.mjs');if(!req.query||Object.keys(req.query).length!==1||!Object.hasOwn(req.query,'region'))throw Error();region(req.query.region);}catch{return res.status(400).json({code:'INVALID_REGION'});}
 try{return res.status(200).json(await retrieve(req.query.region,process.env.FIRMS_MAP_KEY));}catch(e){const code=['KEY_NOT_CONFIGURED','UPSTREAM_NETWORK','UPSTREAM_HTTP','UPSTREAM_CONTENT','UPSTREAM_LIMIT','UPSTREAM_BODY','UPSTREAM_DATA'].includes(e.message)?e.message:'UPSTREAM_INTERNAL';return res.status(code==='KEY_NOT_CONFIGURED'?503:502).json({code});}
}
module.exports=handler;module.exports.retrieve=retrieve;
