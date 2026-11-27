// Presentation adapter. Exact coordinates remain browser-local and are never sent by this module.
import {parseLocations} from './portfolio.mjs';
export {parseLocations} from './portfolio.mjs';
const NS='http://www.w3.org/2000/svg';
const require=(ok,message)=>{if(!ok)throw Error(message);};
export function addLocation(raw,id,lon,lat){
 require(typeof id==='string'&&id.trim()&&typeof lon==='string'&&lon.trim()&&typeof lat==='string'&&lat.trim(),'Enter a location ID, longitude and latitude.');
 const existing=parseLocations(raw);
 require(!existing.some(f=>f.id===id.trim()),'That location ID is already present.');
 // Validate the complete updated set with the same scientific portfolio contract.
 const next=existing.map(f=>[f.id,...f.coordinates].join(', ')).concat([id.trim(),lon.trim(),lat.trim()].join(', ')).join('\n');
 return formatLocations(parseLocations(next));
}
export function formatLocations(facilities){return facilities.map(f=>[f.id,...f.coordinates].join(', ')).join('\n');}
export function coordinatesOnMap(lon,lat){require(Number.isFinite(lon)&&Number.isFinite(lat)&&Math.abs(lon)<=180&&Math.abs(lat)<=90,'Invalid coordinates');return [2*(lon+180),2*(90-lat)];}
export function startLocationTools(doc=document){
 const $=id=>doc.getElementById(id),rows=$('locations'),status=$('location-editor-status'),list=$('location-list'),points=$('location-points');
 const svg=(tag,attrs,txt)=>{const e=doc.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));if(txt!==undefined)e.textContent=txt;return e;};
 const node=(tag,txt)=>{const e=doc.createElement(tag);e.textContent=txt;return e;};
 function update(value){rows.value=value;rows.dispatchEvent(new Event('input',{bubbles:true}));sync();}
 function sync(){
   list.replaceChildren();points.replaceChildren();
   try{const locations=parseLocations(rows.value);$('location-count').textContent=locations.length+' / 25 locations';$('location-empty').hidden=locations.length>0;
     for(const f of locations){
       const [x,y]=coordinatesOnMap(...f.coordinates),dot=svg('circle',{cx:x,cy:y,r:5,class:'location-dot'});dot.append(svg('title',{},f.id));points.append(dot);
       const li=doc.createElement('li'),info=doc.createElement('div'),name=node('strong',f.id),coord=node('small',String(f.coordinates[0])+' longitude, '+String(f.coordinates[1])+' latitude');info.append(name,coord);
       const remove=node('button','Remove');remove.type='button';remove.setAttribute('aria-label','Remove '+f.id);remove.addEventListener('click',()=>{try{update(formatLocations(parseLocations(rows.value).filter(r=>r.id!==f.id)));status.textContent=f.id+' removed.';$('location-id').focus();}catch(e){status.textContent=e.message;}});li.append(info,remove);list.append(li);
     }
     status.textContent=locations.length?locations.length+' valid reference '+(locations.length===1?'location.':'locations.'):'No locations entered.';
     return locations;
   }catch(e){$('location-count').textContent='Invalid locations';$('location-empty').hidden=true;status.textContent='Check coordinate rows: '+e.message;return null;}
 }
 function add(){try{const id=$('location-id'),lon=$('location-lon'),lat=$('location-lat');const next=addLocation(rows.value,id.value,lon.value,lat.value);const name=id.value.trim();update(next);id.value=lon.value=lat.value='';status.textContent=name+' added.';id.focus();}catch(e){status.textContent=e.message;}}
 $('location-add').addEventListener('click',add);
 for(const id of ['location-id','location-lon','location-lat'])$(id).addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();add();}});
 // Keep native and batch edits synchronized. The controller clears any stale result.
 rows.addEventListener('input',sync);
 sync();return Object.freeze({sync});
}
