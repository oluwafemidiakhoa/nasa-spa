import {createCatalog} from './knowledge-catalog.mjs';
import {buildBrief,briefText} from './review-brief.mjs';
const labels={previousCount:'Earlier matches',currentCount:'Recent matches',onlyCurrent:'Only in recent returned set',onlyPrevious:'Only in earlier returned set',nearestCurrentKm:'Nearest recent point (km)'};
const enc=new TextEncoder();
function describe(value){return value===null?'Unavailable / withheld':Array.isArray(value)?(value.length?value.join(', '):'None in returned set'):String(value);}
export function startCatalogDesk(doc,getReview,catalog=createCatalog(),download=(bytes,name,type='application/json')=>{
 const url=URL.createObjectURL(new Blob([bytes],{type})),a=doc.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}){
 const $=id=>doc.getElementById('catalog-'+id),status=s=>{$('status').textContent=s;};let pending=false,brief=null;const saved=catalog.mode==='saved',storageLabel=$('storage'),briefButton=$('brief'),briefOutput=$('brief-output'),briefDownload=$('brief-download');
 const controls=['select','location','from','to','search','forget','previous','current','report',...(briefButton?['brief']:[])];
 function resetBrief(){brief=null;if(briefOutput){briefOutput.textContent='';briefOutput.hidden=true;}if(briefDownload)briefDownload.disabled=true;}
 function lock(){pending=true;$('keep').disabled=true;for(const k of controls)$(k).disabled=true;$('clear').disabled=true;if(briefDownload)briefDownload.disabled=true;}
 function unlock(){pending=false;$('keep').disabled=false;enable(!!selected());if(briefDownload)briefDownload.disabled=!brief;}
 const option=(value,label)=>{const el=doc.createElement('option');el.value=value;el.textContent=label;return el;};
 function selected(){return catalog.list().find(m=>m.reviewId===$('select').value)||null;}
 function resetOutput(){$('results').replaceChildren();}
 function enable(has){for(const k of controls)$(k).disabled=!has;$('clear').disabled=!has;}
 function selection(){
  resetOutput();resetBrief();const m=selected();$('location').replaceChildren();
  if(!m){enable(false);$('from').value='';$('to').value='';return;}
  enable(true);const e=catalog.evidence(m.reviewId);for(const f of e.report.rows)$('location').append(option(f.id,f.id));
  $('location').value=e.report.rows[0]?.id||'';
  const days=catalog.list().filter(r=>r.portfolioId===m.portfolioId).map(r=>r.current.end).sort();$('from').value=days[0];$('to').value=days.at(-1);
  status('Selected portfolio '+m.portfolioId+'. Choose a location and date range.');
 }
 function refresh(id){
  const rows=catalog.list(),stats=catalog.stats();$('stats').textContent=stats.reviews+' / '+stats.maxReviews+' retained reviews; '+stats.retainedBytes.toLocaleString('en-US')+' / '+stats.maxBytes.toLocaleString('en-US')+' evidence bytes.';
  $('select').replaceChildren();for(const m of rows)$('select').append(option(m.reviewId,m.current.start+' to '+m.current.end+' | Portfolio '+m.portfolioId.slice(0,12)+' | Review '+m.reviewId.slice(0,12)));
  $('select').value=rows.some(m=>m.reviewId===id)?id:rows[0]?.reviewId||'';selection();
 }
 $('keep').addEventListener('click',async()=>{
  if(pending)return;const v=getReview();if(!v){status('Run or reopen a review before retaining it.');return;}
  lock();status('Replaying both evidence bundles…');
  try{const m=await catalog.ingest(v.previous,v.current);refresh(m.reviewId);status(saved?'Review saved on this browser. It will be replayed on reopening.':'Review retained in this tab. Download evidence to keep it after reload.');}catch(e){status('Review not retained: '+String(e.message).slice(0,140));}finally{unlock();}
 });
 $('select').addEventListener('change',selection);
 for(const k of ['location','from','to'])$(k).addEventListener('change',()=>{resetOutput();status('Filters changed. Find retained observations again.');});
 $('search').addEventListener('click',()=>{
  resetOutput();const m=selected();if(!m)return;
  try{const r=catalog.history({portfolioId:m.portfolioId,facilityId:$('location').value,from:$('from').value,to:$('to').value,limit:20});
   for(const row of r.records){const section=doc.createElement('article');section.className='catalog-record';const heading=doc.createElement('h3');heading.textContent=row.previous.start+'–'+row.previous.end+' vs '+row.current.start+'–'+row.current.end;section.append(heading);const mode=doc.createElement('p');mode.textContent=row.comparison==='COMPARABLE_RETURNED_RECORDS'?'Returned record sets compared; coverage unknown.':'Comparison withheld: insufficient observations or source limit.';section.append(mode);
    for(const fact of row.facts){const p=doc.createElement('p'),key=fact.pointer.split('/').at(-1);p.textContent=labels[key]+': '+describe(fact.value)+' ['+fact.pointer+']';section.append(p);}
    const provenance=doc.createElement('details'),summary=doc.createElement('summary'),code=doc.createElement('p');summary.textContent='Evidence and report digests';code.textContent='Review: '+row.reviewId+' | Report SHA-256: '+row.reportSha256+' | Earlier bundle: '+row.previous.bundleSha256+' | Earlier source: '+row.previous.sourceSha256+' | Recent bundle: '+row.current.bundleSha256+' | Recent source: '+row.current.sourceSha256;provenance.append(summary,code);section.append(provenance);$('results').append(section);
   }status(r.totalMatches?r.totalMatches+' retained review(s) match the exact portfolio and location.':'No supported retained records match these filters.');
  }catch(e){status('Invalid search: '+String(e.message).slice(0,140));}
 });
 $('forget').addEventListener('click',async()=>{const m=selected();if(!m||pending)return;lock();try{await catalog.remove(m.reviewId);refresh();status(saved?'Selected review removed from browser history.':'Selected review removed from this tab.');}catch(e){status('Review not removed: '+String(e.message).slice(0,140));}finally{unlock();}});
 $('clear').addEventListener('click',async()=>{if(pending)return;if(doc.defaultView&&!doc.defaultView.confirm('Remove every retained investigation from this history? Download evidence you need first.'))return;lock();try{await catalog.clear();refresh();status(saved?'Saved browser history cleared.':'All retained reviews removed from this tab.');}catch(e){status('History not cleared: '+String(e.message).slice(0,140));}finally{unlock();}});
 if(briefButton&&briefOutput&&briefDownload){
  briefButton.addEventListener('click',async()=>{const m=selected();if(!m||pending)return;resetBrief();lock();try{brief=await buildBrief(catalog,m.reviewId);briefOutput.textContent=briefText(brief);briefOutput.hidden=false;status('Briefing generated from the selected retained review.');}catch(e){status('Briefing unavailable: '+String(e.message).slice(0,140));}finally{unlock();}});
  briefDownload.addEventListener('click',()=>{if(!pending&&brief)download(enc.encode(briefText(brief)),'gaia-'+brief.reviewId.slice(0,12)+'-brief.txt','text/plain');});
 }
 for(const k of ['previous','current','report'])$(k).addEventListener('click',()=>{const m=selected();if(!m)return;const e=catalog.evidence(m.reviewId);download(k==='report'?enc.encode(JSON.stringify(e.report)):e[k],'gaia-'+m.reviewId.slice(0,12)+'-'+k+'.json');});
 if(storageLabel)storageLabel.textContent=saved?'Saved on this browser':'Current tab only';
 $('keep').textContent=saved?'Save current review on this browser':'Retain current review in this tab';
 $('clear').textContent=saved?'Clear saved browser history':'Clear retained reviews';
 refresh();$('keep').disabled=false;status(catalog.list().length?(saved?'Saved reviews restored and replayed. Select one to investigate.':'Retained reviews available.'): 'No reviews retained. Run or reopen a review, then save it.');
 return Object.freeze({stats:catalog.stats});
}
