#!/usr/bin/env python3
"""Offline cross-runtime check of Gaia Proof v1; no JS or network dependencies."""
import argparse
import base64
import hashlib
import json
import math
import os
import re
import stat
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

R, GUARD, EPS = 6371.0088, 0.001, 0.000001
MAX_PACKET, MAX_BUNDLE = 40_000_000, 26_000_000
METHODS = {'earth.mjs':'a1ce541de7aa9d49e934fa8c642782741828aad3c8893bb2e29b9465b14df0bc','scripts/earth-batch.mjs':'6b0b64c3f384a3d40d77afbb1cf5744cdac75307535f886a730762e3b28061ba','scripts/eonet_archive.py':'24010b808d080126964c809a37a1a354037340f3a990108b0096fb74831c007b','scripts/verify_earth_batch.py':'693f59bd3351e1544a58c624148cc77ea92e08990d7cf12153c56be0f6ac9ed4'}
CHECKS = dict(componentIntegrity='MATCHED', originalReportReplay='MATCHED_SAME_METHOD', boundary='COMPUTED_CONDITIONAL_BOUNDS', ablation='COMPUTED_REPLAYED_WITNESSES', sourceAuthenticity='UNVERIFIED', coverage='UNKNOWN', independentReproduction='NOT_PERFORMED', crossSourceContradiction='NOT_PERFORMED', trustedChronology='NOT_ESTABLISHED')
LIMIT = 'Checks retained records and enumerated computational fields only. No source authenticity, completeness, trusted chronology, scientific truth, or safety established. Separately supplied fingerprints establish byte binding only. Numerical decision margins within 1 mm are inconclusive. Narrative metadata and display ordering are not independently verified.'

class Inconclusive(ValueError):
    pass

def require(test, message):
    if not test:
        raise ValueError(message)

def number(x):
    return type(x) in (int, float) and math.isfinite(x)

def integer(x, low, high):
    return number(x) and low <= x <= high and int(x) == x

def fields(o, names):
    require(type(o) is dict and set(o) == set(names.split()), 'Unexpected object fields')

def same(a, b):
    if type(a) is dict and type(b) is dict:
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list and type(b) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if number(a) and number(b):
        return a == b
    return type(a) is type(b) and a == b

def check(a, b, message):
    require(same(a, b), message)

def unique(pairs):
    o = {}
    for k, v in pairs:
        require(k not in o, 'Duplicate JSON key')
        o[k] = v
    return o

def invalid_constant(_):
    raise ValueError('Nonfinite JSON constant')

def parse(raw, cap):
    require(0 < len(raw) <= cap, 'JSON size limit')
    obj = json.loads(raw.decode('utf-8'), object_pairs_hook=unique, parse_constant=invalid_constant)
    def walk(x, depth=0):
        require(depth <= 64, 'JSON depth limit')
        if isinstance(x, dict):
            for v in x.values(): walk(v, depth+1)
        elif isinstance(x, list):
            for v in x: walk(v, depth+1)
        elif type(x) in (int, float):
            require(number(x), 'Nonfinite JSON number')
    walk(obj)
    return obj

def sha(b):
    return hashlib.sha256(b).hexdigest()

def hexhash(s):
    return isinstance(s, str) and re.fullmatch(r'[a-f0-9]{64}', s) is not None

def decode(s, limit):
    require(isinstance(s, str) and 0 < len(s) <= 4*((limit+2)//3), 'Base64 size limit')
    b = base64.b64decode(s, validate=True)
    require(0 < len(b) <= limit and base64.b64encode(b).decode('ascii') == s, 'Invalid base64')
    return b

def component(o, limit):
    fields(o, 'sha256 bytes base64')
    require(hexhash(o['sha256']) and integer(o['bytes'], 1, limit), 'Invalid component envelope')
    b = decode(o['base64'], limit)
    require(len(b) == o['bytes'] and sha(b) == o['sha256'], 'Component digest mismatch')
    return b

def utc(s):
    require(isinstance(s, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z', s), 'Invalid UTC timestamp')
    return datetime.fromisoformat(s[:-1]+'+00:00')

def stamp(t):
    return t.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def point(p):
    return type(p) is list and len(p)==2 and all(number(x) for x in p) and abs(p[0])<=180 and abs(p[1])<=90

def vector(p):
    a,b=map(math.radians,p)
    return math.cos(b)*math.cos(a), math.cos(b)*math.sin(a), math.sin(b)

def distance(a,b):
    x,y,z=vector(a);u,v,w=vector(b)
    return R*math.atan2(math.hypot(y*w-z*v,z*u-x*w,x*v-y*u), x*u+y*v+z*w)

def stable(d, threshold):
    if abs(d-threshold) <= EPS:
        raise Inconclusive('Distance within 1 mm of decision threshold')
    return d <= threshold

def near(a,b,limit=EPS):
    require(number(a) and abs(a-b)<=limit, 'Distance or margin differs')

def idkey(s):
    return s.encode('utf-16-be', errors='surrogatepass')

def indexed(rows, label):
    require(isinstance(rows,list), 'Invalid '+label)
    result={}
    for r in rows:
        require(isinstance(r,dict) and isinstance(r.get('eventId'),str) and r['eventId'] not in result,'Duplicate or missing '+label+' ID')
        result[r['eventId']]=r
    return result

def load(raw):
    p=parse(raw,MAX_PACKET); fields(p,'schema bundle report');check(p['schema'],'gaia-proof-packet-v1','Unsupported proof schema')
    bb=component(p['bundle'],MAX_BUNDLE);b=parse(bb,MAX_BUNDLE);fields(b,'schema methods files');check(b['schema'],'gaia-earth-evidence-v0.5','Unsupported bundle schema');check(b['methods'],METHODS,'Method fingerprint mismatch')
    fields(b['files'],'archive configuration report');a,c,r=[component(b['files'][k],lim) for k,lim in [('archive',3_000_000),('configuration',32768),('report',16_000_000)]]
    archive=parse(a,3_000_000);fields(archive,'schema receipt bodyBase64');check(archive['schema'],'gaia-eonet-archive-v0.4','Unsupported archive');rec=archive['receipt'];fields(rec,'mode capturedAt requestUrl query httpStatus limitReached coverage sourceAuthenticated sourceSha256 sourceBytes eventCount pointCount nonPointCount eventsWithoutGeometry')
    src=decode(archive['bodyBase64'],2_000_000);source_hash=sha(src);check(rec['sourceSha256'],source_hash,'Source digest mismatch');check(rec['sourceBytes'],len(src),'Source length mismatch');check(rec['sourceAuthenticated'],False,'False authentication assertion');check(rec['coverage'],'unknown','Unsupported coverage assertion');utc(rec['capturedAt'])
    cfg=parse(c,32768);fields(cfg,'snapshotKind asOf hours radiusKm facilities');require(cfg['snapshotKind'] in ('synthetic-demo','user-import-unverified') and integer(cfg['hours'],1,720) and number(cfg['radiusKm']) and 1<=cfg['radiusKm']<=1000,'Invalid configuration');end=utc(cfg['asOf']);start=end-timedelta(hours=cfg['hours']);require(isinstance(cfg['facilities'],list) and 1<=len(cfg['facilities'])<=25,'Invalid facility count')
    sites={}
    for f in cfg['facilities']:
        fields(f,'id coordinates');require(isinstance(f['id'],str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',f['id']) and f['id'] not in sites and point(f['coordinates']),'Invalid facility');sites[f['id']]=f['coordinates']
    require(rec['mode'] in ('offline-import','https-eonet'),'Unknown source mode')
    if rec['mode']=='offline-import':
        require(all(rec[k] is None for k in ['query','requestUrl','httpStatus','limitReached']),'Invalid offline receipt')
    else:
        q=rec['query'];fields(q,'status start end category limit');require(cfg['snapshotKind']=='user-import-unverified' and q['status']=='all' and isinstance(q['category'],str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,39}',q['category']) and integer(q['limit'],1,200),'Invalid acquisition scope');qa,qb=(utc(q[k]+'T00:00:00Z') for k in ['start','end']);require(0<=(qb-qa).days<=30,'Invalid acquisition dates');check(rec['httpStatus'],200,'Invalid status');check(rec['requestUrl'],'https://eonet.gsfc.nasa.gov/api/v3/events?'+urlencode([(k,int(q[k]) if k=='limit' else q[k]) for k in ['status','start','end','category','limit']]),'Acquisition URL differs')
    snapshot=parse(src,2_000_000);events=snapshot.get('events');require(isinstance(events,list) and len(events)<=2000,'Invalid event list');cov=dict(events=len(events),eligiblePoints=0,unsupportedGeometries=0,outsideWindow=0,eventsWithoutGeometry=0);eligible={};seen=set();total=0
    for e in events:
        require(isinstance(e,dict) and all(isinstance(e.get(k),str) and e[k].strip() for k in ['id','title']) and e['id'] not in seen and isinstance(e.get('geometry'),list),'Invalid or duplicate event');seen.add(e['id']);points=[]
        if not e['geometry']:cov['eventsWithoutGeometry']+=1
        for g in e['geometry']:
            total+=1;require(total<=20000 and isinstance(g,dict) and isinstance(g.get('type'),str) and g['type'],'Invalid geometry')
            if g['type']!='Point':cov['unsupportedGeometries']+=1;continue
            t=utc(g['date']);require(point(g['coordinates']),'Invalid point')
            if start<=t<=end:cov['eligiblePoints']+=1;points.append((g['coordinates'],stamp(t)))
            else:cov['outsideWindow']+=1
        if points:eligible[e['id']]=(e['title'],points)
    for k,v in dict(eventCount=cov['events'],pointCount=cov['eligiblePoints']+cov['outsideWindow'],nonPointCount=cov['unsupportedGeometries'],eventsWithoutGeometry=cov['eventsWithoutGeometry']).items():check(rec[k],v,'Archive coverage differs')
    if rec['mode']=='https-eonet':require(len(events)<=rec['query']['limit'],'Source cap exceeded');check(rec['limitReached'],len(events)==rec['query']['limit'],'Source cap differs')
    orig=parse(r,16_000_000);fields(orig,'schema snapshot configuration results');check(orig['schema'],'gaia-earth-batch-v0.3','Unsupported batch');check(orig['snapshot'],dict(kind=cfg['snapshotKind'],sha256=source_hash,bytes=len(src),authenticity='unverified'),'Batch snapshot differs');check(orig['configuration'],dict(sha256=sha(c),bytes=len(c)),'Batch config digest differs')
    require(isinstance(orig['results'],list) and len(orig['results'])==len(sites),'Batch facility count differs')
    return p,bb,source_hash,rec,cfg,sites,cov,eligible,orig['results']

def nearest(site,events):
    return {eid:(title,[(distance(site,coord),coord,t) for coord,t in pts]) for eid,(title,pts) in events.items()}

def verify_nearest(row,title,pts,rounded=False):
    d=min(t[0] for t in pts);chosen=[x for x in pts if same(x[1],row['coordinates']) and x[2]==row['observedAt']];require(chosen and abs(chosen[0][0]-d)<=EPS,'Nearest point differs')
    if rounded:
        require(number(row['distanceKm']) and abs(row['distanceKm']*1000-round(row['distanceKm']*1000))<1e-6,'Invalid rounded distance');near(row['distanceKm'],chosen[0][0],0.0005+EPS)
    else:near(row['distanceKm'],chosen[0][0])
    return d

def verify(raw,source_anchor='',packet_anchor=''):
    require(not source_anchor or hexhash(source_anchor),'Invalid source anchor');require(not packet_anchor or hexhash(packet_anchor),'Invalid packet anchor');ph=sha(raw);require(not packet_anchor or ph==packet_anchor,'Packet anchor mismatch')
    p,bb,sh,rec,cfg,sites,cov,events,original=load(raw);require(not source_anchor or sh==source_anchor,'Source anchor mismatch');report=p['report'];fields(report,'schema parameters source claim checks boundary ablation limitations');check(report['schema'],'gaia-proof-report-v1','Unsupported report');check(report['checks'],CHECKS,'Unsupported verification claims');q=report['parameters'];fields(q,'facilityId siteToleranceKm radiusToleranceKm threshold deletionBudget');f,u,v,k,budget=(q[x] for x in ['facilityId','siteToleranceKm','radiusToleranceKm','threshold','deletionBudget']);require(isinstance(f,str) and f in sites and all(number(x) and 0<=x<=100 for x in [u,v]) and integer(k,1,2000) and integer(budget,0,2000),'Invalid proof parameters');radius=cfg['radiusKm'];lo,hi=max(0,radius-v),radius+v
    source=dict(bundleSha256=sha(bb),sourceSha256=sh,kind=cfg['snapshotKind'],mode=rec['mode'],capturedAt=rec['capturedAt'],recordedQuery=rec['query'],sourceLimitReached=rec['limitReached']);check(report['source'],source,'Proof source differs');seen=set();selected=None
    for row in original:
        fields(row,'facilityId method parameters coverage status matches limitations');fid=row['facilityId'];require(isinstance(fid,str) and fid in sites and fid not in seen,'Unknown or duplicate facility');seen.add(fid);data=nearest(sites[fid],events);params=dict(facility=sites[fid],asOf=stamp(utc(cfg['asOf'])),hours=cfg['hours'],radiusKm=radius);check(row['parameters'],params,'Batch parameters differ');check(row['method'],'spherical-point-screen-v0.2','Unsupported batch method');check(row['coverage'],cov,'Batch coverage differs');ids={eid for eid,(_,pts) in data.items() if stable(min(x[0] for x in pts),radius)};matches=indexed(row['matches'],'batch');check(sorted(matches),sorted(ids),'Batch membership differs');check(row['status'],'POINTS_WITHIN_RADIUS' if ids else 'NO_MATCH_IN_AVAILABLE_POINTS' if data else 'NO_ELIGIBLE_POINTS','Batch status differs')
        for eid,m in matches.items():
            fields(m,'eventId title observedAt coordinates distanceKm');title,pts=data[eid];check(m['title'],title,'Batch title differs');verify_nearest(m,title,pts,True)
        if fid==f:selected=data
    require(selected is not None,'Selected facility missing');bound=report['boundary'];fields(bound,'schema source parameters coverage nominalCount countBounds status radiusOnlyCounts nearestBoundary rows limitations');check(bound['schema'],'gaia-boundary-certificate-v1','Unsupported boundary schema');bs={k:source[k] for k in ['bundleSha256','sourceSha256','kind','capturedAt']};bs['sourceAuthenticated']=False;check(bound['source'],bs,'Boundary source differs');bp=dict(facilityId=f,facility=sites[f],asOf=stamp(utc(cfg['asOf'])),hours=cfg['hours'],radiusKm=radius,siteToleranceKm=u,radiusToleranceKm=v,radiusBoundsKm=[lo,hi],numericalGuardKm=GUARD);check(bound['parameters'],bp,'Boundary parameters differ');bc=dict(cov,eligibleEventIds=len(selected),coverage='unknown');check(bound['coverage'],bc,'Boundary coverage differs')
    rows=indexed(bound['rows'],'boundary');check(sorted(rows),sorted(selected),'Boundary event set differs');sets=[set(),set(),set()];distances={};ends=[0,0]
    for eid,row in rows.items():
        fields(row,'eventId title nearest nominal classification nominalMarginKm distanceBoundsKm radiusWitness');fields(row['nearest'],'coordinates observedAt distanceKm');title,pts=selected[eid];check(row['title'],title,'Boundary title differs');d=verify_nearest(row['nearest'],title,pts);distances[eid]=d;nom=stable(d,radius);inside=stable(d+u+GUARD,lo);outside=not stable(max(0,d-u-GUARD),hi);atlo=stable(d,lo);athi=stable(d,hi)
        if nom:sets[0].add(eid)
        if inside:sets[1].add(eid)
        if not outside:sets[2].add(eid)
        ends[0]+=atlo;ends[1]+=athi;check(row['nominal'],nom,'Nominal membership differs');check(row['classification'],'GUARANTEED_IN' if inside else 'GUARANTEED_OUT' if outside else 'BOUNDARY_SENSITIVE','Boundary class differs');near(row['nominalMarginKm'],abs(d-radius));require(isinstance(row['distanceBoundsKm'],list) and len(row['distanceBoundsKm'])==2,'Invalid distance bounds');near(row['distanceBoundsKm'][0],max(0,d-u-GUARD));near(row['distanceBoundsKm'][1],d+u+GUARD)
        w=dict(radiusKm=lo,nominalIncluded=True,perturbedIncluded=False) if nom and not atlo else dict(radiusKm=hi,nominalIncluded=False,perturbedIncluded=True) if not nom and athi else None;check(row['radiusWitness'],w,'Radius witness differs')
    n,lower,upper=[len(s) if selected else None for s in sets];bounds=[lower,upper] if selected else None;check(bound['nominalCount'],n,'Nominal count differs');check(bound['countBounds'],bounds,'Boundary bounds differ');check(bound['radiusOnlyCounts'],ends if selected else None,'Radius-only count differs');check(bound['status'],'NO_ELIGIBLE_POINTS' if not selected else 'STABLE_WITHIN_ASSUMPTIONS' if lower==upper else 'BOUNDARY_SENSITIVE','Boundary status differs');w=bound['nearestBoundary']
    if rows:require(isinstance(w,dict) and w.get('eventId') in rows and same(w,rows[w['eventId']]) and abs(distances[w['eventId']]-radius)<=min(abs(d-radius) for d in distances.values())+EPS,'Nearest boundary witness differs')
    else:check(w,None,'Unexpected boundary witness')
    a=report['ablation'];fields(a,'schema source parameters coverage scopes method minimality limitations');check(a['schema'],'gaia-evidence-ablation-v1','Unsupported ablation schema');check(a['source'],bs,'Ablation source differs');check(a['parameters'],dict(bp,threshold=k,deletionBudget=budget),'Ablation parameters differ');check(a['coverage'],bc,'Ablation coverage differs');check(a['method'],'distinct-whole-event-deletion-v1','Unsupported ablation method');require(isinstance(a['scopes'],list) and len(a['scopes'])==3,'Invalid ablation scopes')
    for scope,label,s,cnt,row in zip(['nominal','lower','upper'],['Nominal matching count','Conservative guaranteed lower bound','Conservative upper bound'],sets,[n,lower,upper],a['scopes']):
        minimum=max(0,cnt-k+1) if cnt is not None else None;worst=max(0,cnt-budget) if cnt is not None else None;witness=None
        if minimum:
            removed=sorted(s,key=idkey)[:minimum];remaining=len(selected)-minimum;counts={name:len(group-set(removed)) if remaining else None for name,group in zip(['nominal','lower','upper'],sets)};witness=dict(removedEventIds=removed,remainingEligibleEventIds=remaining,replayedCounts=counts,mathematicalCountAfter=cnt-minimum,outcome='BELOW_THRESHOLD' if remaining else 'NO_ELIGIBLE_POINTS_REMAIN')
        expected=dict(scope=scope,label=label,count=cnt,state='NO_ELIGIBLE_POINTS' if cnt is None else 'AT_OR_ABOVE_THRESHOLD' if minimum else 'ALREADY_BELOW_THRESHOLD',minimumRemovals=minimum,worstCaseAfterBudget=worst,survivesBudget=worst>=k if worst is not None else None,witness=witness);check(row,expected,'Ablation result or deletion witness differs')
    joint=max(0,lower-budget) if lower is not None else None;verdict='INSUFFICIENT_ELIGIBLE_RECORDS' if joint is None else 'CONDITIONALLY_SUPPORTED_AFTER_PERTURBATIONS' if joint>=k else 'UPPER_BOUND_BELOW_THRESHOLD_ON_RETAINED_RECORDS' if upper<k else 'NOT_CERTIFIED_UNDER_ASSUMPTIONS';claim=dict(predicate='AT_LEAST_DISTINCT_RETURNED_EVENT_IDS',threshold=k,verdict=verdict,nominalCount=n,nominalSatisfies=n>=k if n is not None else None,boundaryCountBounds=bounds,jointCountBounds=[joint,upper] if joint is not None else None,minimumGuaranteedSetRemovals=max(0,lower-k+1) if lower is not None else None);check(report['claim'],claim,'Claim differs')
    return dict(status='CROSS_RUNTIME_MATCH',packetSha256=ph,sourceSha256=sh,sourceAnchorMatched=bool(source_anchor),packetAnchorMatched=bool(packet_anchor),sourceAuthenticated=False,scientificValidityEstablished=False,claim=claim,facilities=len(sites),limitations=LIMIT)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('packet',type=Path);parser.add_argument('--source-sha256',default='');parser.add_argument('--packet-sha256',default='');args=parser.parse_args()
    try:
        fd=os.open(args.packet,os.O_RDONLY|getattr(os,'O_NONBLOCK',0)|getattr(os,'O_BINARY',0))
        with os.fdopen(fd,'rb') as f:
            require(stat.S_ISREG(os.fstat(f.fileno()).st_mode),'Expected regular file');raw=f.read(MAX_PACKET+1)
        require(0<len(raw)<=MAX_PACKET,'Packet size limit');out=verify(raw,args.source_sha256,args.packet_sha256);code=0
    except Inconclusive as e:out=dict(status='INCONCLUSIVE_NUMERICAL_BOUNDARY',reason=str(e),sourceAuthenticated=False,scientificValidityEstablished=False);code=2
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError,OSError) as e:out=dict(status='REJECTED',reason=str(e)[:180],sourceAuthenticated=False,scientificValidityEstablished=False);code=1
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return code

if __name__=='__main__':sys.exit(main())
