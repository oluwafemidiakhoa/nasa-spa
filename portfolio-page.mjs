import {startPortfolio} from './portfolio.mjs';
import {startCatalogDesk} from './catalog-desk.mjs';
import {startLocationTools} from './location-tools.mjs';
import {indexedHistory,openSavedCatalog} from './saved-history.mjs';
if(typeof document!=='undefined'&&document.getElementById('portfolio-page')){
 let tools;
 const controller=startPortfolio(document,fetch,()=>localStorage,()=>Date.now(),()=>tools?.sync());
 tools=startLocationTools(document);
 // Until history is verified, never offer a button that appears to save it.
 const status=document.getElementById('catalog-status');
 const keep=document.getElementById('catalog-keep');keep.disabled=true;
 (async()=>{let store;try{store=indexedHistory(globalThis.indexedDB);const catalog=await openSavedCatalog(store);startCatalogDesk(document,controller.getReview,catalog);}catch{store?.close();startCatalogDesk(document,controller.getReview);status.textContent='Saved history unavailable or could not be verified. Existing saved data was not overwritten. Retain reviews in this tab and export them before leaving.';}})();
 document.getElementById('reopen-shortcut').addEventListener('click',()=>{document.getElementById('reopen-panel').open=true;});
}
