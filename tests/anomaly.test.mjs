import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {screenHistory,anomalyReport} from '../anomaly.mjs';
import {sha} from '../facility.mjs';
const DAY=86400000;
function fixture(){const days=Array.from({length:21},(_,i)=>({date:new Date(Date.UTC(2025,0,1)+i*DAY).toISOString().slice(0,10),availablePointRows:5,matchingPointRows:i===19?2:1}));return {startUtc:'2025-01-01T00:00:00.000Z',endUtc:'2025-01-21T00:00:00.000Z',bundleSha256:'a'.repeat(64),sourceSha256:'b'.repeat(64),snapshotKind:'synthetic-demo',radiusKm:100,facilities:[{id:'A',days}]};}
test('latest complete day excludes partial final date and target from baseline',()=>{const h=fixture();h.facilities[0].days[20].matchingPointRows=5;const r=screenHistory(h);assert.equal(r.targetDate,'2025-01-20');assert.equal(r.baselineDates.length,19);assert.equal(r.baselineDates.at(-1),'2025-01-19');assert.equal(r.facilities[0].rankNumerator,1);assert.equal(r.facilities[0].status,'ABOVE_BASELINE_MAX');});
test('exact cross-product ties are conservative',()=>{const h=fixture();Object.assign(h.facilities[0].days[0],{availablePointRows:10,matchingPointRows:4});const f=screenHistory(h).facilities[0];assert.equal(f.rankNumerator,2);assert.equal(f.status,'NOT_ABOVE_BASELINE_MAX');});
test('all tied days rank 20/20, not anomalous',()=>{const h=fixture();h.facilities[0].days[19].matchingPointRows=1;assert.equal(screenHistory(h).facilities[0].rankNumerator,20);});
test('partial first date makes baseline insufficient',()=>{const h=fixture();h.startUtc='2025-01-01T00:00:00.001Z';const f=screenHistory(h).facilities[0];assert.equal(f.status,'INSUFFICIENT_BASELINE');assert.equal(f.rankNumerator,null);});
test('any low-observation day abstains, including target',()=>{for(const i of [0,19]){const h=fixture();h.facilities[0].days[i].availablePointRows=4;const f=screenHistory(h).facilities[0];assert.equal(f.status,'INSUFFICIENT_OBSERVATIONS');assert.equal(f.rankDenominator,null);}});
test('original short bundle abstains and anchor is enforced',async()=>{const bytes=await readFile(new URL('../data/earth-evidence-synthetic.json',import.meta.url));const r=await anomalyReport(bytes,await sha(bytes));assert.equal(r.facilities.length,3);assert(r.facilities.every(f=>f.status==='INSUFFICIENT_BASELINE'));await assert.rejects(anomalyReport(bytes,'0'.repeat(64)),/digest mismatch/);});
