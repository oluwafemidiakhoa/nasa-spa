import {open} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {screen,MAX_BYTES} from '../earth.mjs';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const exactKeys = (x, keys) => x && typeof x === 'object' && !Array.isArray(x) && Object.keys(x).length === keys.length && keys.every(k=>Object.hasOwn(x,k));
const validPoint = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite) && Math.abs(p[0]) <= 180 && Math.abs(p[1]) <= 90;
async function readBounded(path, limit) {
  const f = await open(path,'r');
  try {
    if (!(await f.stat()).isFile()) throw Error('Expected regular file');
    const buf=Buffer.alloc(limit+1);let n=0;
    while(n<buf.length){const {bytesRead}=await f.read(buf,n,buf.length-n,null);if(!bytesRead)break;n+=bytesRead;}
    if(!n || n>limit)throw Error('Empty or oversized input');
    return buf.subarray(0,n);
  } finally { await f.close(); }
}
function parse(bytes) { return JSON.parse(new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes)); }
function batch(snapshotBytes,configBytes) {
  const raw=parse(snapshotBytes), c=parse(configBytes);
  if(!exactKeys(c,['snapshotKind','asOf','hours','radiusKm','facilities']) || !['synthetic-demo','user-import-unverified'].includes(c.snapshotKind) || !Array.isArray(c.facilities) || c.facilities.length<1 || c.facilities.length>25)throw Error('Invalid batch configuration');
  const ids=new Set();
  for(const f of c.facilities){if(!exactKeys(f,['id','coordinates']) || typeof f.id!=='string' || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(f.id) || ids.has(f.id) || !validPoint(f.coordinates))throw Error('Invalid facility or duplicate ID');ids.add(f.id);}
  const results=c.facilities.slice().sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0).map(f=>({facilityId:f.id,...screen(raw,{facility:f.coordinates,asOf:c.asOf,hours:c.hours,radiusKm:c.radiusKm})}));
  return {schema:'gaia-earth-batch-v0.3',snapshot:{kind:c.snapshotKind,sha256:sha(snapshotBytes),bytes:snapshotBytes.length,authenticity:'unverified'},configuration:{sha256:sha(configBytes),bytes:configBytes.length},results};
}
try {
  if(process.argv.length!==4)throw Error('Usage: node scripts/earth-batch.mjs SNAPSHOT.json CONFIG.json');
  const result=batch(await readBounded(process.argv[2],MAX_BYTES),await readBounded(process.argv[3],32768));
  const output=JSON.stringify(result,null,2)+'\n';
  if(Buffer.byteLength(output)>16_000_000)throw Error('Report exceeds replay size limit');
  process.stdout.write(output);
} catch(e) { console.error('Batch rejected: '+e.message);process.exitCode=1; }
