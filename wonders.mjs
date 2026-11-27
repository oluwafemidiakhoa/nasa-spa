// Presentation only. Never substitute an image, model, or stale result for a live observation.
export const GIBS_URL='https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?version=1.3.0&service=WMS&request=GetMap&format=image/jpeg&STYLES=default&bbox=-90,-180,90,180&CRS=EPSG:4326&HEIGHT=720&WIDTH=1440&layers=BlueMarble_NextGeneration';
const NS='http://www.w3.org/2000/svg';
export const PLANETS=Object.freeze([
 ['Mercury',88,34,3.8,'#b8b0a5',.23],['Venus',224.7,66,6,'#e4be83',2.65],['Earth',365.2,100,6.5,'#51aee4',.82],['Mars',687,135,5,'#d97349',4.5],['Jupiter',4331,175,13,'#dbb58e',1.55],['Saturn',10747,218,11,'#e1c99c',3.35],['Uranus',30589,260,8,'#8ed3d3',5.2],['Neptune',59800,306,8,'#6e87dd',2.1]
].map(x=>Object.freeze(x)));
export function orbitPositions(days){
 if(!Number.isFinite(days)||days<0||days>365250)throw Error('Invalid simulation day');
 return PLANETS.map(([name,period,radius,size,color,phase])=>{const a=phase+2*Math.PI*(days%period)/period;return {name,period,radius,size,color,x:360+radius*Math.cos(a),y:165+.44*radius*Math.sin(a)};});
}
export function readout({earthStatus='',events='',eligible='',thermalStatus='',thermalCount='',apodStatus='',apodTitle='',apodDate='',donkiStatus='',donkiCount=''}={}){
 const num=v=>typeof v==='string'&&/^\d{1,5}$/.test(v),clean=v=>typeof v==='string'?v.slice(0,160):'';
 let earth='Waiting for environmental observations';
 if(earthStatus.startsWith('SYNTHETIC'))earth='Synthetic example selected (not live)';
 else if(earthStatus.startsWith('Retained evidence'))earth='Retained observations (not live)';
 else if(earthStatus.startsWith('NASA response received')&&num(events)&&num(eligible))earth=events+' returned events / '+eligible+' eligible points';
 else if(earthStatus.startsWith('No observations accepted'))earth='Environmental source unavailable';
 let thermal='FIRMS awaiting retrieval';
 if(thermalStatus.includes('Source SHA-256 matched')&&num(thermalCount))thermal=thermalCount+' regional thermal rows';
 else if(thermalStatus.includes('not available in this preview')||thermalStatus.includes('not available in this deployment'))thermal='FIRMS connection not configured';
 else if(thermalStatus.includes('Public satellite data is not enabled'))thermal='Public FIRMS data not enabled';
 else if(thermalStatus&&!/^(Waiting|Retrieving)/.test(thermalStatus))thermal='FIRMS unavailable';
 const cosmic=apodStatus.startsWith('Record received')&&apodTitle?clean(apodTitle)+' / '+clean(apodDate):apodStatus.startsWith('No record accepted')?'APOD unavailable':'Waiting for the daily astronomy record';
 const space=donkiStatus.startsWith('Collection received')&&/^\d{1,5} returned (?:CME|FLR|GST) records$/.test(donkiCount)?donkiCount:donkiStatus.startsWith('No collection accepted')?'DONKI unavailable':'Waiting for space-weather records';
 return {earth:earth+' | '+thermal,cosmic,space};
}
function svg(doc,tag,attrs={},text){const e=doc.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=text;return e;}
export function drawOrrery(doc,target,days,selected='Earth',labels=true){
 target.replaceChildren();target.append(svg(doc,'rect',{width:720,height:330,fill:'#040a13'}));
 // Fixed decorative stars, not an astronomical sky chart.
 for(let i=0;i<65;i++)target.append(svg(doc,'circle',{cx:(i*127+13)%719,cy:(i*83+41)%329,r:i%7===0?1.3:.65,fill:'#b4c7df',opacity:.35+(i%4)*.12}));
 const positions=orbitPositions(days);
 for(const p of positions)target.append(svg(doc,'ellipse',{cx:360,cy:165,rx:p.radius,ry:p.radius*.44,fill:'none',stroke:p.name===selected?'#b5e6de':'#577184','stroke-width':p.name===selected?1.5:.75,opacity:.82}));
 target.append(svg(doc,'circle',{cx:360,cy:165,r:25,fill:'#f4a13d',opacity:.17}),svg(doc,'circle',{cx:360,cy:165,r:16,fill:'#ffbc52'}),svg(doc,'circle',{cx:356,cy:160,r:8,fill:'#ffe2a3',opacity:.7}));
 for(const p of positions){if(p.name==='Saturn')target.append(svg(doc,'ellipse',{cx:p.x,cy:p.y,rx:19,ry:5,fill:'none',stroke:'#dec597','stroke-width':2,transform:`rotate(-18 ${p.x} ${p.y})`}));if(p.name===selected)target.append(svg(doc,'circle',{cx:p.x,cy:p.y,r:p.size+4,fill:'none',stroke:'#f5ffff','stroke-width':1.2}));target.append(svg(doc,'circle',{cx:p.x,cy:p.y,r:p.size,fill:p.color,stroke:'#e8f0ff','stroke-opacity':.4,'stroke-width':.6}));if(labels&&p.name===selected)target.append(svg(doc,'text',{x:p.x,y:p.y-p.size-9,fill:'#eefaff','font-size':12,'text-anchor':'middle'},p.name));}
}
export function startWonders(doc=document,{Observer=MutationObserver,ImageCtor=Image}={}){
 const $=id=>doc.getElementById(id),text=(id,v)=>{$(id).textContent=v;};
 const inputs={'earth-status':'earthStatus',events:'events',eligible:'eligible','thermal-status':'thermalStatus','thermal-count':'thermalCount','apod-status':'apodStatus','apod-title':'apodTitle','apod-date':'apodDate','donki-status':'donkiStatus','donki-count':'donkiCount'};
 function sync(){const v=readout(Object.fromEntries(Object.entries(inputs).map(([id,k])=>[k,$(id).textContent])));text('wonders-earth',v.earth);text('wonders-cosmic',v.cosmic);text('wonders-space',v.space);const group=$('wonders-markers');group.replaceChildren();for(const e of $('markers').children){const cx=e.getAttribute('cx'),cy=e.getAttribute('cy');if(cx===null||cy===null||cx===''||cy==='')continue;const x=Number(cx),y=Number(cy);if(Number.isFinite(x)&&Number.isFinite(y)&&x>=0&&x<=720&&y>=0&&y<=360)group.append(svg(doc,'circle',{cx:x,cy:y,r:3.2,fill:'#ffc273',stroke:'#08121f','stroke-width':.9}));}}
 const obs=new Observer(sync);for(const id of [...Object.keys(inputs),'markers'])obs.observe($(id),{childList:true,characterData:true,subtree:true});sync();
 for(const id of ['wonders-sun-image','wonders-webb-image']){const im=$(id);let attempt=0;const failed=()=>{if(id==='wonders-sun-image'){attempt++;if(attempt===1){im.src='https://svs.gsfc.nasa.gov/vis/a000000/a004200/a004259/April2012Eruption_304A_stand.HD1080i.00590_print.jpg';return;}if(attempt===2){im.alt='Illustrative Sun texture, not a solar observation';text('wonders-sun-caption','Solar surface illustration · Historical SDO image unavailable');$('wonders-sun-texture-credit').hidden=false;im.src='assets/textures/2k_sun.jpg';return;}text('wonders-sun-caption','Historical SDO image unavailable');$('wonders-sun-texture-credit').hidden=true;}im.hidden=true;$(id+'-fallback').hidden=false;};im.addEventListener('error',failed);if(im.complete&&im.naturalWidth===0)failed();}
 const layers=['wonders-gibs','earth-gibs'];$('thermal-gibs').setAttribute('hidden','');let ready=false,visible=false;
 const toggle=$('basemap-toggle');function apply(){for(const id of layers){if(visible)$(id).removeAttribute('hidden');else $(id).setAttribute('hidden','');}toggle.setAttribute('aria-pressed',String(visible));toggle.textContent=visible?'Use geographic outlines':'Use satellite mosaic';text('basemap-status',visible?'Historical Blue Marble mosaic (NASA GIBS); not current satellite conditions.':'Natural Earth geographic outlines.');text('wonders-earth-image-credit',visible?'NASA GIBS / Blue Marble historical mosaic':'Natural Earth geographic outlines');}
 toggle.disabled=true;toggle.addEventListener('click',()=>{if(ready){visible=!visible;apply();}});apply();const preload=new ImageCtor();preload.referrerPolicy='no-referrer';preload.onload=()=>{if(!preload.naturalWidth||!preload.naturalHeight)return;ready=true;visible=true;for(const id of layers)$(id).setAttribute('href',GIBS_URL);toggle.disabled=false;apply();};preload.onerror=()=>{ready=false;visible=false;apply();text('basemap-status','Satellite mosaic unavailable; geographic outlines remain available.');};preload.src=GIBS_URL;
 const slider=$('orbit-days'),select=$('orbit-planet');const update=()=>{const day=Number(slider.value),planet=select.value;if(!Number.isInteger(day)||day<0||day>3650||!PLANETS.some(p=>p[0]===planet))return;drawOrrery(doc,$('orbit-model'),day,planet,true);text('orbit-time',day+' simulated Earth days');const p=PLANETS.find(x=>x[0]===planet);text('orbit-detail',planet+' takes approximately '+p[1].toLocaleString('en-US')+' Earth days to orbit the Sun.');};slider.addEventListener('input',update);select.addEventListener('change',update);$('orbit-reset').addEventListener('click',()=>{slider.value='0';select.value='Earth';update();});drawOrrery(doc,$('wonders-orbits'),0,'Earth',false);update();return {sync,update};
}
if(typeof document!=='undefined'&&document.getElementById('wonders-grid'))startWonders();
