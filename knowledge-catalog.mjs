// Local, ephemeral retrieval over replayed portfolio reviews. No network or LLM.
import {compare,portfolio} from './portfolio.mjs';
import {sha,MAX_BUNDLE} from './facility.mjs';
const enc=new TextEncoder(), clone=x=>structuredClone(x);
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const date=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&Number.isFinite(Date.parse(x+'T00:00:00Z'))&&new Date(x+'T00:00:00Z').toISOString().slice(0,10)===x;
const require=(v,m)=>{if(!v)throw Error(m);};
const digest=x=>sha(enc.encode(JSON.stringify(x)));
const MAX_BYTES=32_000_000,MAX_REVIEWS=20;
export async function portfolioIdentity(p){return digest(portfolio(p));}
export function createCatalog(){
  // Each instance is an isolated local workspace, not a multi-tenant ACL.
  const rows=new Map();let total=0,epoch=0,busy=false;
  async function ingest(previous,current){
    require(!busy,'Another import is in progress');
    require(previous instanceof Uint8Array&&current instanceof Uint8Array&&previous.byteLength>0&&current.byteLength>0&&previous.byteLength<=MAX_BUNDLE&&current.byteLength<=MAX_BUNDLE,'Invalid evidence input');
    const size=previous.byteLength+current.byteLength;require(size<=MAX_BYTES,'Evidence exceeds catalog capacity');
    const version=epoch;busy=true;
    try{
      // Snapshot mutable input before asynchronous verification.
      const a=new Uint8Array(previous),b=new Uint8Array(current),report=await compare(a,b);
      const portfolioId=await portfolioIdentity(report.portfolio),reportSha256=await digest(report);
      const reviewId=await digest(['gaia-catalog-v1',report.previous.bundleSha256,report.current.bundleSha256,reportSha256]);
      require(version===epoch,'Catalog changed during import');
      if(rows.has(reviewId))return clone(rows.get(reviewId).meta);
      require(rows.size<MAX_REVIEWS&&total+size<=MAX_BYTES,'Catalog capacity reached; remove retained reviews first');
      const meta={reviewId,portfolioId,reportSha256,previous:report.previous,current:report.current,comparison:report.comparison,limitations:report.limitations};
      rows.set(reviewId,{meta,report,previous:a,current:b,size});total+=size;
      return clone(meta);
    }finally{busy=false;}
  }
  function list(){return [...rows.values()].map(v=>clone(v.meta)).sort((a,b)=>b.current.end.localeCompare(a.current.end)||b.current.capturedAt.localeCompare(a.current.capturedAt)||a.reviewId.localeCompare(b.reviewId));}
  function history(q){
    require(q&&typeof q==='object'&&!Array.isArray(q)&&Object.keys(q).sort().join(',')==='facilityId,from,limit,portfolioId,to'&&hex(q.portfolioId)&&typeof q.facilityId==='string'&&q.facilityId.length>0&&q.facilityId.length<=80&&date(q.from)&&date(q.to)&&q.from<=q.to&&Number.isInteger(q.limit)&&q.limit>=1&&q.limit<=MAX_REVIEWS,'Invalid history query');
    // Filter exact portfolio/version and date before retrieving report rows.
    const matching=list().filter(m=>m.portfolioId===q.portfolioId&&m.current.end>=q.from&&m.current.end<=q.to).flatMap(m=>{
      const item=rows.get(m.reviewId),i=item.report.rows.findIndex(r=>r.id===q.facilityId);
      if(i<0)return [];
      const row=item.report.rows[i],fields=['previousCount','currentCount','onlyCurrent','onlyPrevious','nearestCurrentKm'];
      const facts=fields.map(k=>({pointer:'/rows/'+i+'/'+k,value:clone(row[k])}));
      return [{...m,facilityId:q.facilityId,facts}];
    });
    return {schema:'gaia-catalog-history-v1',outcome:matching.length?'SUPPORTED_RETURNED_RECORDS':'NO_SUPPORTED_RECORDS',query:clone(q),totalMatches:matching.length,truncated:matching.length>q.limit,records:matching.slice(0,q.limit),limitations:'Local retained reviews only. Dates refer to query windows, not event occurrence. Null and withheld results remain distinct from zero. Same-method replay does not authenticate sources or establish hazard risk.'};
  }
  function evidence(id){require(hex(id),'Invalid review ID');const item=rows.get(id);return item?{report:clone(item.report),previous:item.previous.slice(),current:item.current.slice()}:null;}
  function remove(id){require(hex(id),'Invalid review ID');epoch++;const item=rows.get(id);if(!item)return false;total-=item.size;rows.delete(id);return true;}
  function clear(){epoch++;rows.clear();total=0;}
  return Object.freeze({ingest,list,history,evidence,remove,clear,stats:()=>({reviews:rows.size,retainedBytes:total,maxReviews:MAX_REVIEWS,maxBytes:MAX_BYTES})});
}
