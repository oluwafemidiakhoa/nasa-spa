// A deterministic briefing derived from a retained, replayed review; no AI claims.
import {sha} from './facility.mjs';
const enc=new TextEncoder();
export async function buildBrief(catalog,id){
 const meta=catalog.list().find(m=>m.reviewId===id),e=meta&&catalog.evidence(id);
 if(!meta||!e)throw Error('Select a retained review');
 const r=e.report,digest=await sha(enc.encode(JSON.stringify(r)));
 if(digest!==meta.reportSha256)throw Error('Retained report digest mismatch');
 const comparable=r.comparison==='COMPARABLE_RETURNED_RECORDS';
 const facts=r.rows.map((row,i)=>({id:row.id,previousCount:row.previousCount,currentCount:row.currentCount,onlyCurrent:row.onlyCurrent,onlyPrevious:row.onlyPrevious,nearestCurrentKm:row.nearestCurrentKm,pointers:Object.fromEntries(['id','previousCount','currentCount','onlyCurrent','onlyPrevious','nearestCurrentKm'].map(k=>[k,`/rows/${i}/${k}`]))}));
 const result={schema:'gaia-review-brief-v1',reviewId:id,portfolioId:meta.portfolioId,reportSha256:digest,category:r.portfolio.category,radiusKm:r.portfolio.radiusKm,previous:r.previous,current:r.current,comparison:r.comparison,summary:{locations:facts.length,recentMatchesAtLocations:facts.filter(x=>x.currentCount!==null&&x.currentCount>0).length,recentCountUnavailable:facts.filter(x=>x.currentCount===null).length,locationsWithReturnedSetDifferences:comparable?facts.filter(x=>x.onlyCurrent.length||x.onlyPrevious.length).length:null},locations:facts,limitations:r.limitations};
 return result;
}
export function briefText(b){
 const show=v=>v===null?'Unavailable / withheld':Array.isArray(v)?(v.length?v.join(', '):'None in returned set'):String(v);
 const lines=['Gaia Observatory | Observation briefing',`Category: ${b.category} | Reference radius: ${b.radiusKm} km`,`Earlier UTC window: ${b.previous.start} to ${b.previous.end}`,`Recent UTC window: ${b.current.start} to ${b.current.end}`,`Locations reviewed: ${b.summary.locations}`,`Locations with recent returned matches: ${b.summary.recentMatchesAtLocations}`,`Locations with unavailable recent counts: ${b.summary.recentCountUnavailable}`,`Locations with returned-set differences: ${show(b.summary.locationsWithReturnedSetDifferences)}`,'',b.comparison==='COMPARABLE_RETURNED_RECORDS'?'Compare returned record sets, not incident onset or worsening conditions.':'Set comparison withheld: insufficient observations or source limit.',''];
 for(const f of b.locations){lines.push(f.id,`  Earlier matches: ${show(f.previousCount)} [${f.pointers.previousCount}]`,`  Recent matches: ${show(f.currentCount)} [${f.pointers.currentCount}]`,`  Only in recent returned set: ${show(f.onlyCurrent)} [${f.pointers.onlyCurrent}]`,`  Only in earlier returned set: ${show(f.onlyPrevious)} [${f.pointers.onlyPrevious}]`,`  Nearest recent point (km): ${show(f.nearestCurrentKm)} [${f.pointers.nearestCurrentKm}]`,'');}
 lines.push('Evidence',`Review: ${b.reviewId}`,`Report SHA-256: ${b.reportSha256}`,`Earlier bundle SHA-256: ${b.previous.bundleSha256}`,`Earlier source SHA-256: ${b.previous.sourceSha256}`,`Recent bundle SHA-256: ${b.current.bundleSha256}`,`Recent source SHA-256: ${b.current.sourceSha256}`,'',b.limitations);
 return lines.join('\n');
}
