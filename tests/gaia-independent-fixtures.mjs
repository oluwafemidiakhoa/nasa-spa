// Synthetic cross-runtime fixtures. The Python verifier does not execute this code.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {makeProof} from '../gaia-proof.mjs';
import {createBundle,study} from '../workspace.mjs';
import {sha} from '../facility.mjs';
const output=resolve(process.argv[2]);await mkdir(output,{recursive:true});
const enc=x=>new TextEncoder().encode(JSON.stringify(x)),date='2026-11-25T12:00:00Z',R=6371.0088;
const defaults={facilityId:'REFERENCE',siteToleranceKm:10,radiusToleranceKm:5,threshold:2,deletionBudget:1};
function dest([lon,lat],d,b){const r=Math.PI/180,a=lat*r,t=lon*r,c=d/R,g=b*r,p=Math.asin(Math.sin(a)*Math.cos(c)+Math.cos(a)*Math.sin(c)*Math.cos(g)),q=t+Math.atan2(Math.sin(g)*Math.sin(c)*Math.cos(a),Math.cos(c)-Math.sin(a)*Math.sin(p));return [((q/r+540)%360)-180,p/r];}
const point=(coordinates,stamp=date)=>({type:'Point',coordinates,date:stamp});
const event=(id,geometry)=>({id,title:'Fictional '+id,geometry});
async function make(center,events,extras={},sites=[]){const x={start:'2026-11-19',end:'2026-11-25',category:'wildfires',radiusKm:100,facilities:[{id:'REFERENCE',coordinates:center},...sites]};const bytes=enc({events}),b=await createBundle({requestUrl:'https://eonet.gsfc.nasa.gov/api/v3/events?'+new URLSearchParams(study(x).query),capturedAt:'2026-11-26T16:00:00.000Z',sourceSha256:await sha(bytes),bodyBase64:Buffer.from(bytes).toString('base64')},x);return makeProof(b.bytes,{...defaults,...extras});}
const manifest=[];
async function add(id,packet,expected,options=[]){const raw=typeof packet==='string'?Buffer.from(packet):enc(packet);await writeFile(resolve(output,id+'.json'),raw);manifest.push({id,expected,options});}
const demo=await makeProof(await readFile(new URL('../data/boundary-demo.json',import.meta.url)),{...defaults,facilityId:'FICTIONAL-REFERENCE'}),sh=demo.report.source.sourceSha256,ph=await sha(enc(demo));
await add('demo',demo,0);await add('anchored',demo,0,['--source-sha256',sh,'--packet-sha256',ph]);
const center=[179.95,20],near=[10,20,30,200].map((d,i)=>event('robust-'+i,[point(dest(center,d,90*i))]));
await add('robust',await make(center,near),0);await add('far',await make([0,0],[event('far',[point([5,5])])]),0);await add('empty',await make([0,0],[]),0);
await add('multipoint',await make([0,0],[event('multi',[point([0,0.2]),point([0,3]),point([0,0.1],'2026-01-01T00:00:00Z'),{type:'Polygon'}]),event('missing',[])]),0);
await add('polar',await make([25,89.8],[event('p1',[point(dest([25,89.8],20,45))]),event('p2',[point(dest([25,89.8],120,90))])]),0);
await add('multi-site',await make(center,near,{},[{id:'OTHER',coordinates:[-110,10]}]),0);
await add('capped',await make([0,0],Array.from({length:200},(_,i)=>event('cap-'+i,[point([0,2+i/1000])]))),0);
await add('all-deleted',await make([0,0],[event('one',[point([0,0.1])])],{threshold:1,deletionBudget:1}),0);
await add('boundary',await make([0,0],[event('edge',[point(dest([0,0],100,0))])]),2);
await add('guard-boundary',await make([0,0],[event('edge',[point(dest([0,0],84.999,0))])]),2);
for(const [id,mutate] of [['claim',p=>p.report.claim.nominalCount++],['bounds',p=>p.report.claim.jointCountBounds[0]=2],['boundary-class',p=>p.report.boundary.rows[0].classification='GUARANTEED_IN'],['point',p=>p.report.boundary.rows[0].nearest.coordinates=[0,0]],['witness',p=>p.report.ablation.scopes[0].witness.removedEventIds[0]='DEMO-6'],['source-status',p=>p.report.checks.sourceAuthenticity='VERIFIED'],['bundle-digest',p=>p.bundle.sha256='0'.repeat(64)],['parameters',p=>p.report.parameters.threshold=4],['missing-row',p=>p.report.boundary.rows.pop()],['bad-distance',p=>p.report.boundary.rows[0].nearest.distanceKm+=0.1]]){const p=structuredClone(demo);mutate(p);await add(id,p,1);}
await add('wrong-source-anchor',demo,1,['--source-sha256','0'.repeat(64)]);await add('wrong-packet-anchor',demo,1,['--packet-sha256','0'.repeat(64)]);await add('duplicate-key',JSON.stringify(demo).replace('"schema":"gaia-proof-packet-v1"','"schema":"gaia-proof-packet-v1","schema":"gaia-proof-packet-v1"'),1);
await add('malformed','{"schema":1',1);
const alternate=await make([0,0],[event('alternate',[point([0,0.2])])]);await add('alternate-unanchored',alternate,0);await add('alternate-anchored',alternate,1,['--source-sha256',sh]);
// Recompute nested report and bundle hashes after modifying a batch result. The independent verifier must inspect membership itself.
const tamper=structuredClone(demo),b=JSON.parse(Buffer.from(tamper.bundle.base64,'base64')),r=JSON.parse(Buffer.from(b.files.report.base64,'base64'));r.results[0].matches.pop();const rb=enc(r);b.files.report={sha256:await sha(rb),bytes:rb.length,base64:Buffer.from(rb).toString('base64')};const bb=enc(b),bh=await sha(bb);tamper.bundle={sha256:bh,bytes:bb.length,base64:Buffer.from(bb).toString('base64')};for(const s of [tamper.report.source,tamper.report.boundary.source,tamper.report.ablation.source])s.bundleSha256=bh;await add('rehashed-batch',tamper,1);
let seed=20261127;const random=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/2**32);
for(let i=0;i<60;i++){const site=[[0,0],[179.9,20],[10,89.5]][i%3],distances=[10,25,70,90,97,103,109,180];const events=distances.map((d,j)=>event('e'+j,[point(dest(site,d+random()*0.1,360*random()))]));await add('grid-'+String(i).padStart(2,'0'),await make(site,events,{threshold:1+i%5,deletionBudget:i%3}),0);}
await writeFile(resolve(output,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify({fixtures:manifest.length,accepted:manifest.filter(x=>x.expected===0).length,rejected:manifest.filter(x=>x.expected===1).length,inconclusive:manifest.filter(x=>x.expected===2).length}));
