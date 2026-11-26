// NASA FIRMS VIIRS NOAA-20 NRT, documented numeric CSV fields.
// No inference of confirmed fires, exposure, severity, or complete coverage.
export const SOURCE='VIIRS_NOAA20_NRT';
export const MAX_CSV=1_500_000, MAX_ROWS=10000;
export const REGIONS=Object.freeze({west:Object.freeze({label:'Western United States',bounds:Object.freeze([-125,31,-113,43])}),texas:Object.freeze({label:'Texas and surrounding region',bounds:Object.freeze([-107,25,-93,37])}),africa:Object.freeze({label:'West Africa',bounds:Object.freeze([-15,5,5,17])}),brazil:Object.freeze({label:'Central Brazil',bounds:Object.freeze([-58,-19,-44,-7])})});
const ok=(v,m)=>{if(!v)throw Error(m);};
export function region(id){ok(typeof id==='string'&&Object.hasOwn(REGIONS,id),'Unknown region');return REGIONS[id];}
function decimal(s){ok(typeof s==='string'&&/^-?\d+(?:\.\d+)?$/.test(s)&&Number.isFinite(Number(s)),'Invalid numeric field');return Number(s);}
export function parseFirms(bytes,id){
 const {bounds:[w,s,e,n]}=region(id);ok(bytes instanceof Uint8Array&&bytes.length>0&&bytes.length<=MAX_CSV,'CSV size limit');
 const raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes);ok(!raw.includes('\u0000'),'Invalid CSV');
 const lines=raw.replace(/\r\n/g,'\n').replace(/\n$/,'').split('\n');ok(lines.length<=MAX_ROWS+1,'Observation row limit');
 const header=lines.shift().split(',');const needed=['latitude','longitude','acq_date','acq_time','satellite','instrument','confidence','frp'];
 ok(header.length<=24&&header.every(k=>/^[a-z][a-z0-9_]*$/.test(k))&&new Set(header).size===header.length&&needed.every(k=>header.includes(k)),'Unexpected FIRMS schema');
 const idx=Object.fromEntries(needed.map(k=>[k,header.indexOf(k)]));const records=[];
 for(const line of lines){const cells=line.split(',');ok(cells.length===header.length&&cells.every(v=>/^[A-Za-z0-9_.+-]*$/.test(v)&&v.length<=64),'Invalid CSV row');
 const lat=decimal(cells[idx.latitude]),lon=decimal(cells[idx.longitude]),frp=decimal(cells[idx.frp]),date=cells[idx.acq_date],clock=cells[idx.acq_time].padStart(4,'0');
 ok(lat>=s&&lat<=n&&lon>=w&&lon<=e&&frp>=0,'Observation outside region or invalid FRP');
 ok(/^\d{4}-\d{2}-\d{2}$/.test(date)&&Number.isFinite(Date.parse(date+'T00:00:00Z'))&&new Date(date+'T00:00:00Z').toISOString().slice(0,10)===date&&/^(?:[01]\d|2[0-3])[0-5]\d$/.test(clock)&&/^\d{1,4}$/.test(cells[idx.acq_time]),'Invalid acquisition time');
 const confidence=cells[idx.confidence];ok(['l','n','h'].includes(confidence)&&cells[idx.satellite]==='N20'&&cells[idx.instrument]==='VIIRS','Unexpected VIIRS record');
 records.push({lat,lon,frp,confidence,observedAt:date+'T'+clock.slice(0,2)+':'+clock.slice(2)+':00Z'});
 }
 return records;
}
export function summarize(records){const confidence={l:0,n:0,h:0};let latest=null;for(const r of records){confidence[r.confidence]++;if(latest===null||r.observedAt>latest)latest=r.observedAt;}return {count:records.length,confidence,latest};}
export function projectThermal(lon,lat){return [2*(lon+180),2*(90-lat)];}
export function regionView(id){const {bounds:[w,s,e,n]}=region(id);return [2*(w+180),2*(90-n),2*(e-w),2*(n-s)].join(' ');}
