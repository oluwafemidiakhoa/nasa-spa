const SOURCE='https://svs.gsfc.nasa.gov/vis/a000000/a004200/a004259/April2012Eruption_304A.00590_print.jpg';
const LIMIT=1_000_000;
async function retrieve(transport=fetch){
 const response=await transport(SOURCE,{redirect:'error',signal:AbortSignal.timeout(10000),headers:{Accept:'image/jpeg','Accept-Encoding':'identity'}});
 if(response.status!==200||response.headers.get('content-type')?.split(';')[0].trim().toLowerCase()!=='image/jpeg')throw Error('UPSTREAM_IMAGE');
 const len=response.headers.get('content-length');if(len!==null&&(!/^\d+$/.test(len)||Number(len)>LIMIT))throw Error('UPSTREAM_LIMIT');
 const reader=response.body?.getReader();if(!reader)throw Error('UPSTREAM_IMAGE');let size=0;const chunks=[];
 try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>LIMIT)throw Error('UPSTREAM_LIMIT');chunks.push(value);}}finally{try{await reader.cancel();}catch{}}
 const bytes=Buffer.concat(chunks,size);
 if(size<4||bytes[0]!==255||bytes[1]!==216||bytes[size-2]!==255||bytes[size-1]!==217)throw Error('UPSTREAM_IMAGE');
 const encoding=(response.headers.get('content-encoding')||'identity').toLowerCase();if(!['identity','gzip','br','deflate'].includes(encoding)||encoding==='identity'&&len!==null&&size!==Number(len))throw Error('UPSTREAM_IMAGE');
 return bytes;
}
async function handler(req,res){
 res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
 if(req.method!=='GET'){res.setHeader('Allow','GET');return res.status(405).json({code:'METHOD_NOT_ALLOWED'});}
 if(!['preview','production'].includes(process.env.VERCEL_ENV))return res.status(403).json({code:'ENVIRONMENT_NOT_ENABLED'});
 if(Object.keys(req.query||{}).length)return res.status(400).json({code:'INVALID_QUERY'});
 try{const bytes=await retrieve();res.setHeader('Content-Type','image/jpeg');res.setHeader('Vercel-CDN-Cache-Control','public, s-maxage=86400');res.setHeader('Cache-Control','public, max-age=3600');return res.status(200).send(bytes);}catch{return res.status(502).json({code:'UPSTREAM_IMAGE_UNAVAILABLE'});}
}
module.exports=handler;module.exports.retrieve=retrieve;module.exports.SOURCE=SOURCE;
