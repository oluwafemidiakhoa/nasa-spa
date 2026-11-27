import {test} from 'node:test';
import assert from 'node:assert/strict';
import {sha} from '../facility.mjs';
import {study,createBundle} from '../workspace.mjs';
import {periods} from '../portfolio.mjs';
import {createCatalog,portfolioIdentity} from '../knowledge-catalog.mjs';
// Controlled synthetic observations emulate the existing EONET transport contract.
// They are NOT acquired NASA observations or production evidence.
const p={category:'wildfires',radiusKm:50,facilities:[{id:'A',coordinates:[-95,30]},{id:'B',coordinates:[0,0]}]};
const now=Date.parse('2026-11-26T23:00:00Z'),enc=new TextEncoder();
const ev=(id,date)=>({id,title:id,geometry:[{type:'Point',date:date+'T12:00:00Z',coordinates:[-95,30]}]});
async function pair({day=now,config=p,empty=false,suffix=''}={}){
 const w=periods(day);const create=async(period,events)=>{const x={...config,...period},bytes=enc.encode(JSON.stringify({events}));return (await createBundle({requestUrl:'https://eonet.gsfc.nasa.gov/api/v3/events?'+new URLSearchParams(study(x).query),capturedAt:new Date(day).toISOString(),sourceSha256:await sha(bytes),bodyBase64:Buffer.from(bytes).toString('base64')},x)).bytes;};
 return [await create(w.previous,empty?[]:[ev('old'+suffix,w.previous.start)]),await create(w.current,[ev('new'+suffix,w.current.start)])];
}
const query=(portfolioId,facilityId='A',overrides={})=>({portfolioId,facilityId,from:'2026-11-01',to:'2026-11-30',limit:20,...overrides});
function pointer(report,p){return p.split('/').slice(1).reduce((v,k)=>v[k],report);}
test('verified ingest, content identity, exact citations, immutable outputs',async()=>{
 const c=createCatalog(),[a,b]=await pair(),m=await c.ingest(a,b),pid=await portfolioIdentity(p);assert.equal(m.portfolioId,pid);assert.equal(m.previous.bundleSha256,await sha(a));assert.equal(m.current.bundleSha256,await sha(b));
 const r=c.history(query(pid)),e=c.evidence(m.reviewId);assert.equal(r.totalMatches,1);assert.equal(m.reportSha256,await sha(enc.encode(JSON.stringify(e.report))));for(const f of r.records[0].facts)assert.deepEqual(f.value,pointer(e.report,f.pointer));
 const m2=await c.ingest(a,b);assert.equal(m2.reviewId,m.reviewId);assert.equal(c.stats().reviews,1);m.current.end='bad';e.current[0]^=1;r.records[0].facts[0].value=999;assert.equal(c.list()[0].current.end,'2026-11-25');assert.equal(await sha(c.evidence(m2.reviewId).current),m2.current.bundleSha256);assert.equal(c.history(query(pid)).records[0].facts[0].value,1);
});
test('fixed labeled retrieval cases: exact portfolio, location, date range, ordering, limit',async()=>{
 const c=createCatalog(),a=await c.ingest(...await pair()),b=await c.ingest(...await pair({day:now-7*86400000})),other=await c.ingest(...await pair({config:{...p,radiusKm:60}}));
 const cases=[[query(a.portfolioId),[a.reviewId,b.reviewId]],[query(a.portfolioId,'B'),[a.reviewId,b.reviewId]],[query(a.portfolioId,'A',{from:'2026-11-19'}),[a.reviewId]],[query(other.portfolioId),[other.reviewId]],[query(a.portfolioId,'UNKNOWN'),[]],[query(a.portfolioId,'A',{to:'2026-11-10'}),[]],[query('0'.repeat(64)),[]],[query(a.portfolioId,'A',{limit:1}),[a.reviewId]]];
 for(const [q,expected] of cases){const r=c.history(q);assert.deepEqual(r.records.map(x=>x.reviewId),expected);assert.equal(r.outcome,expected.length?'SUPPORTED_RETURNED_RECORDS':'NO_SUPPORTED_RECORDS');}
 assert.equal(c.history(cases.at(-1)[0]).truncated,true);assert.equal(c.history(query(a.portfolioId,'B')).records[0].facts.find(x=>x.pointer.endsWith('/currentCount')).value,0);
});
test('preserve alternative captures for same window; do not overwrite evidence',async()=>{const c=createCatalog(),a=await c.ingest(...await pair()),b=await c.ingest(...await pair({suffix:'-revision'}));assert.notEqual(a.reviewId,b.reviewId);assert.equal(c.history(query(a.portfolioId)).totalMatches,2);});
test('unavailable is not zero; withhold unsupported comparison facts',async()=>{const c=createCatalog(),m=await c.ingest(...await pair({empty:true})),r=c.history(query(m.portfolioId)).records[0];assert.equal(r.comparison,'INSUFFICIENT_OBSERVATIONS_OR_LIMIT');assert.equal(r.facts.find(x=>x.pointer.endsWith('/previousCount')).value,null);assert.equal(r.facts.find(x=>x.pointer.endsWith('/onlyCurrent')).value,null);});
test('reject tampering, reversed windows, invalid queries; no partial insertion',async()=>{const c=createCatalog(),[a,b]=await pair(),bad=b.slice();bad[20]^=1;await assert.rejects(c.ingest(a,bad));await assert.rejects(c.ingest(b,a));assert.equal(c.stats().reviews,0);assert.throws(()=>c.history(query('0'.repeat(64),'A',{from:'2026-02-30'})));assert.throws(()=>c.history({...query('0'.repeat(64)),tenant:'other'}));assert.throws(()=>c.history(query('0'.repeat(64),'A',{limit:21})));});
test('isolated instances, explicit deletion, clear, no network or shared persistence',async()=>{const a=createCatalog(),b=createCatalog(),m=await a.ingest(...await pair());assert.equal(b.evidence(m.reviewId),null);assert.equal(b.history(query(m.portfolioId)).totalMatches,0);assert.equal(a.remove(m.reviewId),true);assert.equal(a.history(query(m.portfolioId)).totalMatches,0);assert.equal(a.stats().retainedBytes,0);await a.ingest(...await pair());a.clear();assert.equal(a.stats().reviews,0);});
test('clear invalidates in-flight import; reject oversized inputs',async()=>{const c=createCatalog(),[a,b]=await pair();const promise=c.ingest(a,b);c.clear();await assert.rejects(promise,/changed during import/);assert.equal(c.stats().reviews,0);await assert.rejects(c.ingest(new Uint8Array(0),b));await assert.rejects(c.ingest(new Uint8Array(26_000_001),b));});
test('Buffer input is copied rather than retaining a mutable view',async()=>{const c=createCatalog(),[a,b]=await pair(),x=Buffer.from(a),y=Buffer.from(b),expected=await sha(y);const promise=c.ingest(x,y);x.fill(0);y.fill(0);const m=await promise;assert.equal(await sha(c.evidence(m.reviewId).current),expected);});
test('one in-flight import and a hard review count budget',async()=>{const c=createCatalog(),[a,b]=await pair();const first=c.ingest(a,b);await assert.rejects(c.ingest(a,b),/in progress/);const original=await first;for(let i=1;i<20;i++)await c.ingest(...await pair({suffix:String(i)}));assert.equal(c.stats().reviews,20);await assert.rejects(c.ingest(...await pair({suffix:'overflow'})),/capacity/);assert.equal(c.stats().reviews,20);assert.equal((await c.ingest(a,b)).reviewId,original.reviewId);assert.equal(c.stats().reviews,20);});
