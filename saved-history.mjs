// Explicitly saved, origin-local history. No network, account sync or secret access.
import {createCatalog} from './knowledge-catalog.mjs';
import {MAX_BUNDLE} from './facility.mjs';
const DB='gaia-observatory-history-v1', STORE='archive', KEY='reviews';
const CAP=32_000_000, COUNT=20;
const check=(ok,message)=>{if(!ok)throw Error(message);};
const empty=()=>({schema:'gaia-saved-history-v1',revision:0,records:[]});
const exact=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
export function validateSnapshot(x){
 check(exact(x,['schema','revision','records'])&&x.schema==='gaia-saved-history-v1'&&Number.isSafeInteger(x.revision)&&x.revision>=0&&x.revision<Number.MAX_SAFE_INTEGER&&Array.isArray(x.records)&&x.records.length<=COUNT,'Invalid saved history');
 let bytes=0;const seen=new Set();
 for(const r of x.records){check(exact(r,['reviewId','previous','current'])&&hex(r.reviewId)&&!seen.has(r.reviewId),'Invalid saved review identity');seen.add(r.reviewId);for(const k of ['previous','current']){check(r[k] instanceof Uint8Array&&r[k].byteLength>0&&r[k].byteLength<=MAX_BUNDLE,'Invalid saved evidence bytes');bytes+=r[k].byteLength;check(bytes<=CAP,'Saved history exceeds capacity');}}
 return x;
}
export async function replaySnapshot(x){
 validateSnapshot(x);const c=createCatalog();
 for(const r of x.records){const meta=await c.ingest(r.previous,r.current);check(meta.reviewId===r.reviewId,'Saved review identity does not match replayed evidence');}
 return c;
}
function snapshot(c,revision){return {schema:'gaia-saved-history-v1',revision,records:c.list().map(m=>{const e=c.evidence(m.reviewId);return {reviewId:m.reviewId,previous:e.previous,current:e.current};})};}
// A single transactional record allows revision checks across tabs. Persist a new
// revision even when clearing, preventing a stale tab from resurrecting history.
export function indexedHistory(factory){
 let database;
 async function open(){
  if(database)return database;
  check(factory&&typeof factory.open==='function','Browser history storage unavailable');
  database=await new Promise((resolve,reject)=>{
   let settled=false;const request=factory.open(DB,1);
   const fail=message=>{settled=true;reject(Error(message));};
   request.onupgradeneeded=()=>{if(!request.result.objectStoreNames.contains(STORE))request.result.createObjectStore(STORE);};
   request.onerror=()=>fail('Browser history storage unavailable');
   request.onblocked=()=>fail('History database blocked by another tab');
   request.onsuccess=()=>{if(settled){request.result.close();return;}settled=true;resolve(request.result);};
  });
  database.onversionchange=()=>{database.close();database=undefined;};return database;
 }
 async function read(){const db=await open();return new Promise((resolve,reject)=>{
  const tx=db.transaction(STORE,'readonly'),r=tx.objectStore(STORE).get(KEY);
  tx.oncomplete=()=>resolve(r.result===undefined?empty():r.result);
  tx.onabort=()=>reject(Error('History read failed'));tx.onerror=()=>reject(Error('History read failed'));
 });}
 async function commit(expected,next){validateSnapshot(next);check(next.revision===expected+1,'Invalid next history revision');const db=await open();return new Promise((resolve,reject)=>{
  const tx=db.transaction(STORE,'readwrite'),s=tx.objectStore(STORE),r=s.get(KEY);let reason='History write failed or storage quota exceeded';
  r.onsuccess=()=>{try{const current=validateSnapshot(r.result===undefined?empty():r.result);check(current.revision===expected,'History changed in another tab. Reload before saving or deleting.');s.put(next,KEY);}catch(e){reason=e.message;tx.abort();}};
  tx.oncomplete=()=>resolve();tx.onabort=()=>reject(Error(reason));
 });}
 return Object.freeze({read,commit,close:()=>{database?.close();database=undefined;}});
}
// No partial restoration, no overwrite after a failed read, and no optimistic
// UI claim: publish a new in-memory view only after commit completion.
export async function openSavedCatalog(store){
 let raw=await store.read(), inner=await replaySnapshot(raw),revision=raw.revision,busy=false;raw=null;
 async function mutate(action){
  check(!busy,'Another history operation is in progress');busy=true;
  try{
   const next=await replaySnapshot(snapshot(inner,revision)),result=await action(next);
   // Check revision even for duplicate saves or empty clears: a stale tab
   // must not claim a saved review that another tab has since removed.
   const state=snapshot(next,revision+1);await store.commit(revision,state);
   inner=next;revision=state.revision;return result;
  }finally{busy=false;}
 }
 return Object.freeze({mode:'saved',ingest:(a,b)=>{
  // Snapshot before any asynchronous operation or copy of the existing catalog.
  check(a instanceof Uint8Array&&b instanceof Uint8Array&&a.length>0&&b.length>0&&a.length<=MAX_BUNDLE&&b.length<=MAX_BUNDLE&&a.length+b.length<=CAP,'Invalid evidence input');
  const previous=new Uint8Array(a),current=new Uint8Array(b);return mutate(c=>c.ingest(previous,current));
 },list:()=>inner.list(),history:q=>inner.history(q),evidence:id=>inner.evidence(id),stats:()=>inner.stats(),remove:id=>mutate(c=>c.remove(id)),clear:()=>mutate(c=>c.clear()),close:()=>store.close?.()});
}
