import {historyReport} from './history.mjs';
import {screenHistory} from './anomaly.mjs';
import {MAX_BUNDLE} from './facility.mjs';

const ID='[A-Za-z0-9][A-Za-z0-9_-]{0,63}';
const EXPLAIN=new RegExp('^explain ('+ID+')$');
const DAILY=new RegExp('^day ('+ID+') (\\d{4}-\\d{2}-\\d{2})$');
const messages={ABOVE_BASELINE_MAX:'The target share strictly exceeded all 19 baseline shares.',NOT_ABOVE_BASELINE_MAX:'The target share did not strictly exceed every baseline share.',INSUFFICIENT_BASELINE:'The screening abstained because there were fewer than 19 complete baseline dates or no complete target date.',INSUFFICIENT_OBSERVATIONS:'The screening abstained because at least one required date contained fewer than five eligible point rows.'};
const limits='Archived observation descriptions only. No safety, hazard probability, causal, predictive or statistical significance conclusion is supported.';
export function validateQuery(q){if(typeof q!=='string'||!/^[\x20-\x7e]{1,160}$/.test(q)||q.includes('\n')||q.includes('\r'))throw Error('Query must contain 1-160 printable ASCII characters.');}
export function answerHistory(h,q){
  validateQuery(q);const s=screenHistory(h),facts=[];
  let outcome='ANSWERED',reason='',message='';
  const abstain=(r,m)=>{outcome='ABSTAINED';reason=r;message=m;};
  const fact=(label,report,pointer,value)=>facts.push({label,report,pointer,value});
  if(q==='summary'){
    reason='FACILITY_SUMMARY';message='Screening statuses for every facility in the retained window.';
    s.facilities.forEach((f,i)=>{fact('Facility','screening','/facilities/'+i+'/id',f.id);fact('Status','screening','/facilities/'+i+'/status',f.status);});
  }else if(q==='provenance'){
    reason='SOURCE_PROVENANCE';message='The original retained input is identified below; authenticity is not established.';
    for(const [label,key] of [['Bundle SHA-256','bundleSha256'],['Source SHA-256','sourceSha256'],['Declared snapshot kind','snapshotKind'],['Coverage','coverage'],['Window start UTC','startUtc'],['Window end UTC','endUtc'],['Radius (km)','radiusKm']])fact(label,'history','/'+key,h[key]);
  }else if(q==='limits'){
    reason='METHOD_LIMITS';message=limits;
  }else{
    const explain=EXPLAIN.exec(q),daily=DAILY.exec(q);
    if(!explain&&!daily)abstain('UNSUPPORTED_QUERY','Unsupported question. Use one of the five exact query types.');
    else{
      const id=(explain||daily)[1],i=h.facilities.findIndex(f=>f.id===id);
      if(i<0)abstain('FACILITY_NOT_FOUND','The requested facility is not in the retained bundle.');
      else if(explain){
        const f=s.facilities[i];reason='SCREENING_EXPLANATION';message=messages[f.status];
        fact('Screening policy','screening','/policy',s.policy);fact('Facility screening record','screening','/facilities/'+i,f);
        if(f.rankNumerator===null){outcome='ABSTAINED';reason=f.status;}
      }else{
        const j=h.facilities[i].days.findIndex(d=>d.date===daily[2]);
        if(j<0)abstain('DATE_NOT_FOUND','The requested UTC date is not in the retained window.');
        else{const row=h.facilities[i].days[j];reason='DAILY_RECORD';message=row.state==='NO_ELIGIBLE_POINTS'?'No eligible point rows were recorded for this date; this is not evidence of safety.':'The available, matching and distinct-event counts are shown for the requested UTC date.';fact('Facility','history','/facilities/'+i+'/id',id);fact('Daily observation record','history','/facilities/'+i+'/days/'+j,row);}
      }
    }
  }
  return {schema:'gaia-research-answer-v0.9',query:q,bundleSha256:h.bundleSha256,sourceSha256:h.sourceSha256,snapshotKind:h.snapshotKind,coverage:'unknown',sourceAuthenticated:false,scientificValidityEstablished:false,outcome,reason,message,facts};
}
export async function researchAnswer(bytes,q,anchor=''){validateQuery(q);return answerHistory(await historyReport(bytes,anchor),q);}
function startUI(){
  const $=id=>document.getElementById(id),file=$('research-file'),anchor=$('research-anchor'),query=$('research-query'),status=$('research-status'),facts=$('research-facts');let revision=0,history=null,answer=null;
  const node=(tag,value)=>{const el=document.createElement(tag);el.textContent=value;return el;};
  function resetAnswer(){answer=null;$('research-result').hidden=true;$('research-export').disabled=true;facts.replaceChildren();}
  function clear(message){revision++;history=null;resetAnswer();$('research-ask').disabled=true;$('research-context').textContent='';status.textContent=message;return revision;}
  async function load(get,expected){const rev=clear('Checking original evidence bundle...');try{const h=await historyReport(await get(),expected);if(rev!==revision)return;history=h;$('research-context').textContent=(h.snapshotKind==='synthetic-demo'?'Synthetic demonstration: fictional observations and facilities. ':'Imported observations: source authenticity unverified. ')+h.facilities.map(f=>f.id).join(', ');$('research-ask').disabled=false;status.textContent='Browser replay matched; independent Python verification not performed.';}catch(e){if(rev===revision)clear('Bundle rejected: '+String(e.message).slice(0,180));}}
  $('research-demo').addEventListener('click',()=>{file.value='';anchor.value='';load(async()=>{const r=await fetch('data/earth-evidence-synthetic.json',{cache:'no-store'});if(!r.ok)throw Error('Demo unavailable');return new Uint8Array(await r.arrayBuffer());},'');});
  $('research-load').addEventListener('click',()=>{const f=file.files[0];load(async()=>{if(!f||f.size>MAX_BUNDLE)throw Error('Select a bundle no larger than 26 MB');return new Uint8Array(await f.arrayBuffer());},anchor.value.trim());});
  for(const el of [file,anchor])el.addEventListener('input',()=>clear('Evidence input changed. Inspect again.'));
  query.addEventListener('input',resetAnswer);
  $('research-clear').addEventListener('click',()=>{file.value='';anchor.value='';clear('No bundle loaded.');});
  $('research-form').addEventListener('submit',e=>{e.preventDefault();resetAnswer();if(!history)return;try{answer=answerHistory(history,query.value);$('research-outcome').textContent=answer.outcome+' / '+answer.reason;$('research-message').textContent=answer.message;$('research-digest').textContent=answer.bundleSha256;for(const f of answer.facts){const row=document.createElement('article');row.append(node('h3',f.label),node('code',f.report+' '+f.pointer),node('pre',JSON.stringify(f.value,null,2)));facts.append(row);}$('research-result').hidden=false;$('research-export').disabled=false;}catch(e){status.textContent='Question rejected: '+String(e.message).slice(0,180);}});
  $('research-export').addEventListener('click',()=>{if(!answer)return;const url=URL.createObjectURL(new Blob([JSON.stringify(answer,null,2)+'\n'],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='gaia-research-answer.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
}
if(typeof document!=='undefined'&&document.getElementById('research-file'))startUI();
