export const MAX_BYTES = 2_000_000;
const R = 6371.0088;
const validPoint = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite) && Math.abs(p[0]) <= 180 && Math.abs(p[1]) <= 90;
function time(s) {
  if (typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(s)) throw Error('Expected UTC timestamp');
  const t = Date.parse(s);
  if (!Number.isFinite(t) || new Date(t).toISOString() !== (s.length === 20 ? s.slice(0,-1)+'.000Z' : s)) throw Error('Invalid UTC timestamp');
  return t;
}
export function distanceKm(a, b) {
  if (!validPoint(a) || !validPoint(b)) throw Error('Invalid longitude/latitude');
  const rad = Math.PI / 180;
  const h = Math.sin((b[1]-a[1])*rad/2)**2 + Math.cos(a[1]*rad)*Math.cos(b[1]*rad)*Math.sin((b[0]-a[0])*rad/2)**2;
  return 2*R*Math.asin(Math.sqrt(Math.min(1, Math.max(0,h))));
}
const cmp = (a,b) => a < b ? -1 : a > b ? 1 : 0;
export function screen(snapshot, {facility, asOf, hours, radiusKm}) {
  const end = time(asOf);
  if (!validPoint(facility) || !Number.isInteger(hours) || hours < 1 || hours > 720 || !Number.isFinite(radiusKm) || radiusKm < 1 || radiusKm > 1000) throw Error('Invalid screening parameters');
  if (!snapshot || !Array.isArray(snapshot.events) || snapshot.events.length > 2000) throw Error('Invalid or oversized event array');
  const start = end-hours*3600000, seen = new Set(), matches = [];
  const coverage = {events: snapshot.events.length, eligiblePoints: 0, unsupportedGeometries: 0, outsideWindow: 0, eventsWithoutGeometry: 0};
  let total = 0;
  for (const e of snapshot.events) {
    if (!e || typeof e.id !== 'string' || !e.id.trim() || typeof e.title !== 'string' || !e.title.trim() || seen.has(e.id) || !Array.isArray(e.geometry)) throw Error('Invalid event or duplicate ID');
    seen.add(e.id);
    if (!e.geometry.length) coverage.eventsWithoutGeometry++;
    let closest = null;
    for (const g of e.geometry) {
      if (++total > 20000 || !g || typeof g.type !== 'string') throw Error('Invalid or oversized geometry array');
      if (g.type !== 'Point') { coverage.unsupportedGeometries++; continue; }
      const observed = time(g.date);
      if (!validPoint(g.coordinates)) throw Error('Invalid point coordinates');
      if (observed < start || observed > end) { coverage.outsideWindow++; continue; }
      coverage.eligiblePoints++;
      const d = distanceKm(facility,g.coordinates);
      if (d > radiusKm) continue;
      const point = {eventId:e.id,title:e.title,observedAt:new Date(observed).toISOString(),coordinates:g.coordinates.slice(),distanceKm:d};
      if (!closest || d < closest.distanceKm || (d === closest.distanceKm && (cmp(point.observedAt,closest.observedAt) || cmp(point.coordinates[0],closest.coordinates[0]) || cmp(point.coordinates[1],closest.coordinates[1])) < 0)) closest = point;
    }
    if (closest) matches.push(closest);
  }
  matches.sort((a,b) => a.distanceKm-b.distanceKm || cmp(a.eventId,b.eventId));
  return {method:'spherical-point-screen-v0.2',parameters:{facility:facility.slice(),asOf:new Date(end).toISOString(),hours,radiusKm},coverage,status:matches.length?'POINTS_WITHIN_RADIUS':coverage.eligiblePoints?'NO_MATCH_IN_AVAILABLE_POINTS':'NO_ELIGIBLE_POINTS',matches:matches.map(m=>({...m,distanceKm:Number(m.distanceKm.toFixed(3))})),limitations:'No match is not safety. Points are not hazard footprints; coverage, source authenticity, and actual facility exposure are unverified.'};
}
export async function makeReport(bytes, parameters, kind) {
  if (!(bytes instanceof Uint8Array) || !bytes.length || bytes.length > MAX_BYTES || !['synthetic-demo','user-import-unverified'].includes(kind)) throw Error('Invalid snapshot input');
  const hash = await crypto.subtle.digest('SHA-256',bytes);
  const digest = Array.from(new Uint8Array(hash),v=>v.toString(16).padStart(2,'0')).join('');
  const raw = JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  return {snapshot:{kind,sha256:digest,bytes:bytes.length,authenticity:'unverified'},...screen(raw,parameters)};
}
