const {test}=require('node:test');const assert=require('node:assert/strict');const {createHash}=require('node:crypto');
const handler=require('../api/gaia-eonet.js');
const query={start:'2025-01-07',end:'2025-01-15',category:'wildfires'},url=handler.url(query);
const raw=Buffer.from('{"events":[]}\n');const response=(data=raw,headers={'content-type':'application/json'},status=200)=>new Response(data,{headers,status});
test('fixed NASA URL and no unexpected inputs',()=>{assert.equal(url,'https://eonet.gsfc.nasa.gov/api/v3/events?status=all&start=2025-01-07&end=2025-01-15&category=wildfires&limit=200');for(const q of [{...query,category:'https://bad'},{...query,facility:'A'},{...query,start:'2025-02-30'},{...query,end:'2025-02-07'},{...query,start:['2025-01-07']},{...query,end:'2025-01-06'}])assert.throws(()=>handler.url(q));});
test('exact source bytes and digest, bounded redirect policy',async()=>{const receipt=await handler.retrieve(url,async(u,o)=>{assert.equal(u,url);assert.equal(o.redirect,'error');assert(o.signal);return response();});assert.deepEqual(Buffer.from(receipt.bodyBase64,'base64'),raw);assert.equal(receipt.sourceSha256,createHash('sha256').update(raw).digest('hex'));assert.equal(receipt.requestUrl,url);});
test('upstream rejects errors, malformed data, excessive counts, truncated and oversized bodies',async()=>{for(const r of [response(raw,{'content-type':'text/html'}),response(raw,{'content-type':'application/json'},404),response('bad'),response(JSON.stringify({events:Array(201).fill({})})),response(raw,{'content-type':'application/json','content-length':'999'}),response(raw,{'content-type':'application/json','content-encoding':'unsupported'}),response(Buffer.alloc(2000001))])await assert.rejects(handler.retrieve(url,async()=>r));});
test('HTTP method and supported-environment checks',async()=>{const old=process.env.VERCEL_ENV;const out=()=>({code:0,setHeader(){},status(v){this.code=v;return this;},json(v){this.body=v;return this;}});try{process.env.VERCEL_ENV='development';let r=out();await handler({method:'GET',query},r);assert.equal(r.code,403);process.env.VERCEL_ENV='production';r=out();await handler({method:'GET',query:{...query,other:1}},r);assert.equal(r.code,400);process.env.VERCEL_ENV='preview';r=out();await handler({method:'POST',query},r);assert.equal(r.code,405);r=out();await handler({method:'GET',query:{...query,other:1}},r);assert.equal(r.code,400);}finally{if(old===undefined)delete process.env.VERCEL_ENV;else process.env.VERCEL_ENV=old;}});
const http=require('node:http');const {gzipSync}=require('node:zlib');
test('real HTTP gzip: preserve decoded JSON bytes, not compressed Content-Length',async()=>{
 const bytes=Buffer.from(JSON.stringify({events:[{id:'a',description:'x'.repeat(1000)}]}));const gz=gzipSync(bytes);
 assert.notEqual(gz.length,bytes.length);
 const server=http.createServer((req,res)=>{res.writeHead(200,{'content-type':'application/json','content-encoding':'gzip','content-length':gz.length});res.end(gz);});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 try{const receipt=await handler.retrieve(url,(_u,o)=>fetch('http://127.0.0.1:'+server.address().port,o));assert.deepEqual(Buffer.from(receipt.bodyBase64,'base64'),bytes);assert.equal(receipt.sourceSha256,createHash('sha256').update(bytes).digest('hex'));}finally{await new Promise(r=>server.close(r));}
});
test('real HTTP invalid gzip and decompressed oversize rejected',async()=>{
 const big=gzipSync(Buffer.from(JSON.stringify({events:[],text:'x'.repeat(2000001)})));const bad=Buffer.from('not gzip');
 const server=http.createServer((req,res)=>{const b=req.url==='/bad'?bad:big;res.writeHead(200,{'content-type':'application/json','content-encoding':'gzip','content-length':b.length});res.end(b);});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 try{for(const [path,code] of [['/bad','UPSTREAM_BODY'],['/big','UPSTREAM_SIZE']])await assert.rejects(handler.retrieve(url,(_u,o)=>fetch('http://127.0.0.1:'+server.address().port+path,o)),e=>e.code===code);}finally{await new Promise(r=>server.close(r));}
});
test('classify upstream failures without leaking network details',async()=>{
 for(const [cause,code] of [[{code:'ENOTFOUND'},'UPSTREAM_DNS'],[{code:'UND_ERR_CONNECT_TIMEOUT'},'UPSTREAM_TIMEOUT'],[{code:'CERT_HAS_EXPIRED'},'UPSTREAM_TLS'],[{code:'ECONNRESET'},'UPSTREAM_NETWORK']])await assert.rejects(handler.retrieve(url,async()=>{throw new Error('private detail',{cause});}),e=>e.message===code&&e.code===code);
 for(const [r,code] of [[response(raw,{'content-type':'application/json'},503),'UPSTREAM_HTTP_503'],[response(raw,{'content-type':'text/html'}),'UPSTREAM_CONTENT_TYPE'],[response('bad'),'UPSTREAM_JSON'],[response(raw,{'content-type':'application/json','content-length':'999'}),'UPSTREAM_TRUNCATED']])await assert.rejects(handler.retrieve(url,async()=>r),e=>e.code===code);
});
