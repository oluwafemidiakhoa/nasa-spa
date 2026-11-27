// Offline RFC 3161 request creation and verification for Gaia Discovery lock files.
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {open,readFile,writeFile,mkdtemp,mkdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {strictJSON} from '../facility.mjs';
import {verifyLock,MAX_PACKET} from '../discovery-lab.mjs';
const MAX_TSA=1_000_000,MAX_TRUST=500_000;
const LIMIT='Conditional evidence of existence of these exact lock bytes before the target window under the selected timestamp authority and declared accuracy. The trust bundle and policy must be independently vetted; revocation, authority independence, trusted local issue time, first capture and scientific source authenticity are not established. The verifier does not prove predictive skill or absence of leakage.';
const ok=(v,m)=>{if(!v)throw Error(m);};
const digest=b=>createHash('sha256').update(b).digest('hex');
const hex=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const policy=s=>typeof s==='string'&&s.length<=128&&/^[0-2]\.(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)){1,24}$/.test(s);
async function bounded(path,limit){const f=await open(path,'r');try{const s=await f.stat();ok(s.isFile()&&s.size>0&&s.size<=limit,'Invalid file size or type');const b=Buffer.alloc(s.size+1);let n=0;while(n<b.length){const r=await f.read(b,n,b.length-n,null);if(!r.bytesRead)break;n+=r.bytesRead;}ok(n===s.size,'File changed during read');return b.subarray(0,n);}finally{await f.close();}}
async function replay(bytes){ok(bytes instanceof Uint8Array&&bytes.length>0&&bytes.length<=MAX_PACKET,'Invalid lock bytes');return (await verifyLock(strictJSON(bytes))).lock;}
async function isolated(run){const dir=await mkdtemp(join(tmpdir(),'gaia-ts-'));try{await mkdir(join(dir,'empty'));await writeFile(join(dir,'empty.cnf'),'');const env={...process.env,LC_ALL:'C',LANG:'C',TZ:'UTC',OPENSSL_CONF:join(dir,'empty.cnf'),SSL_CERT_FILE:join(dir,'trust.pem'),SSL_CERT_DIR:join(dir,'empty')};delete env.OPENSSL_CONF_INCLUDE;delete env.OPENSSL_MODULES;const call=(args)=>{try{return execFileSync('openssl',args,{cwd:dir,env,timeout:15000,maxBuffer:1_000_000,stdio:['ignore','pipe','pipe']});}catch{throw Error('OpenSSL timestamp operation failed');}};return await run(dir,call);}finally{await rm(dir,{recursive:true,force:true});}}
function field(s,key){const lines=s.split(/\r?\n/).filter(x=>x.startsWith(key+':'));ok(lines.length===1,'Unexpected timestamp field: '+key);return lines[0].slice(key.length+1).trim();}
export function parseTimestampText(text){
 ok(field(text,'Status')==='Granted.'&&field(text,'Version')==='1'&&field(text,'Hash Algorithm')==='sha256','Unsupported timestamp status, version or imprint algorithm');
 const p=field(text,'Policy OID'),nonce=field(text,'Nonce');ok(policy(p)&&/^0x[0-9a-f]+$/i.test(nonce)&&BigInt(nonce)>0n,'Missing nonce or unsupported timestamp policy');
 const t=field(text,'Time stamp'),m=/^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}) (\d\d):(\d\d):(\d\d)(?:\.(\d{1,12}))? (\d{4}) GMT$/.exec(t);ok(m,'Unsupported timestamp time format');
 const mon='Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ').indexOf(m[1]),y=Number(m[7]),d=Number(m[2]),h=Number(m[3]),min=Number(m[4]),s=Number(m[5]);
 const whole=Date.UTC(y,mon,d,h,min,s),round=new Date(whole);ok(y>=2000&&y<=9997&&round.getUTCFullYear()===y&&round.getUTCMonth()===mon&&round.getUTCDate()===d&&round.getUTCHours()===h&&round.getUTCMinutes()===min&&round.getUTCSeconds()===s,'Invalid timestamp calendar date');
 const fraction=(m[6]||'').padEnd(3,'0'),floor=whole+Number(fraction.slice(0,3)),ceil=floor+(/[1-9]/.test(fraction.slice(3))?1:0);
 const a=field(text,'Accuracy');let accuracyMs=null;
 if(a!=='unspecified'){
  const match=/^(0x[0-9a-f]+|unspecified) seconds, (0x[0-9a-f]+|unspecified) millis, (0x[0-9a-f]+|unspecified) micros$/i.exec(a);ok(match,'Unsupported timestamp accuracy format');
  const parts=match.slice(1).map(x=>x==='unspecified'?0:Number(BigInt(x)));ok(parts.every(Number.isSafeInteger)&&parts[0]>=0&&parts[0]<=86400&&parts[1]>=0&&parts[1]<=999&&parts[2]>=0&&parts[2]<=999,'Invalid timestamp accuracy');
  if(match.slice(1).some(x=>x!=='unspecified'))accuracyMs=parts[0]*1000+parts[1]+Math.ceil(parts[2]/1000);
 }
 return {policy:p,nonce,time: new Date(floor).toISOString(),accuracyMs,earliestMs:accuracyMs===null?null:floor-accuracyMs,latestMs:accuracyMs===null?null:ceil+accuracyMs};
}
export async function createRequest(lockBytes,expectedPolicy){
 await replay(lockBytes);ok(policy(expectedPolicy),'Supply an explicit numeric TSA policy OID');
 return isolated(async(dir,call)=>{await writeFile(join(dir,'lock.json'),lockBytes);call(['ts','-query','-data','lock.json','-sha256','-cert','-tspolicy',expectedPolicy,'-out','request.tsq']);return bounded(join(dir,'request.tsq'),MAX_TSA);});
}
export async function verifyTimestamp(lockBytes,query,response,trust,pinnedTrustSha256,expectedPolicy){
 const lock=await replay(lockBytes);ok(policy(expectedPolicy)&&hex(pinnedTrustSha256),'Supply independently vetted trust digest and numeric TSA policy');
 for(const [b,max] of [[query,MAX_TSA],[response,MAX_TSA],[trust,MAX_TRUST]])ok(b instanceof Uint8Array&&b.length>0&&b.length<=max,'Timestamp input exceeds limit');
 ok(digest(trust)===pinnedTrustSha256,'Trust bundle digest mismatch');
 return isolated(async(dir,call)=>{
  for(const [name,bytes] of [['lock.json',lockBytes],['request.tsq',query],['response.tsr',response],['trust.pem',trust]])await writeFile(join(dir,name),bytes);
  const q=call(['ts','-query','-in','request.tsq','-text']).toString('utf8');
  ok(field(q,'Version')==='1'&&field(q,'Hash Algorithm')==='sha256'&&field(q,'Policy OID')===expectedPolicy&&/^0x[0-9a-f]+$/i.test(field(q,'Nonce'))&&BigInt(field(q,'Nonce'))>0n,'Unexpected timestamp request');
  const p=parseTimestampText(call(['ts','-reply','-in','response.tsr','-text']).toString('utf8'));
  ok(p.policy===expectedPolicy&&BigInt(p.nonce)===BigInt(field(q,'Nonce')),'Timestamp nonce or policy mismatch');
  const args=['ts','-verify','-in','response.tsr','-CAfile','trust.pem','-CApath','empty','-CAstore','trust.pem','-auth_level','2','-check_ss_sig','-verify_depth','5'];
  for(const target of [['-queryfile','request.tsq'],['-data','lock.json']])ok(call([...args,...target]).toString('utf8').trim()==='Verification: OK','Timestamp signature or imprint verification failed');
  const start=Date.parse(lock.manifest.windows.target.start+'T00:00:00.000Z'),issued=Date.parse(lock.manifest.issuedAt);
  const status=p.latestMs===null?'ACCURACY_UNKNOWN':p.latestMs<issued?'DECLARED_ISSUE_AFTER_TIMESTAMP':p.latestMs>=start?'BEFORE_WINDOW_NOT_ESTABLISHED':'BEFORE_WINDOW_CONDITIONAL';
  return {schema:'gaia-rfc3161-lock-verification-v1',status,manifestSha256:lock.manifestSha256,lockSha256:digest(lockBytes),querySha256:digest(query),responseSha256:digest(response),trustSha256:pinnedTrustSha256,tsaPolicy:expectedPolicy,tokenTimeFloor:p.time,accuracyRoundedUpMs:p.accuracyMs,earliestTokenTime:p.earliestMs===null?null:new Date(p.earliestMs).toISOString(),latestTokenTime:p.latestMs===null?null:new Date(p.latestMs).toISOString(),targetStartsAt:new Date(start).toISOString(),signatureAndImprintVerified:true,nonceMatched:true,revocationChecked:false,sourceAuthenticated:false,limitations:LIMIT};
 });
}
async function main(args){
 if(args[0]==='request'&&args.length===4){const b=await createRequest(await bounded(args[1],MAX_PACKET),args[2]);await writeFile(args[3],b,{flag:'wx',mode:0o600});process.stdout.write('RFC 3161 request created locally. Submit it only to your chosen TSA.\n');return;}
 if(args[0]==='verify'&&args.length===8){const r=await verifyTimestamp(await bounded(args[1],MAX_PACKET),await bounded(args[2],MAX_TSA),await bounded(args[3],MAX_TSA),await bounded(args[4],MAX_TRUST),args[5],args[6]);await writeFile(args[7],JSON.stringify(r,null,2)+'\n',{flag:'wx',mode:0o600});process.stdout.write(r.status+'\n');if(r.status!=='BEFORE_WINDOW_CONDITIONAL')process.exitCode=3;return;}
 throw Error('Usage: node scripts/gaia-timestamp.mjs request LOCK POLICY REQUEST.tsq | verify LOCK REQUEST.tsq RESPONSE.tsr TRUST.pem TRUST_SHA256 POLICY REPORT.json');
}
if(process.argv[1]&&resolve(process.argv[1])===resolve(fileURLToPath(import.meta.url)))main(process.argv.slice(2)).catch(e=>{process.stderr.write(String(e.message).slice(0,240)+'\n');process.exitCode=2;});
