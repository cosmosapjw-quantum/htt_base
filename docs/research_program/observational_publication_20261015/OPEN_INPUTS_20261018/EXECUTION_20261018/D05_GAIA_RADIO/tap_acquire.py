"""Public ARI UWS acquisition. Each named query is submitted at most once.

Job identity is committed to disk before RUN, polling, or result collection.
An interrupted collector restarts against that identity, never a replacement job.
Raw row products live outside Git. No authentication or resume is attempted.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, shutil, urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET

ROOT = Path('/mnt/extdrive/workdir/htt_open_data/gaia/d05_full_20261018')
BASE = 'https://gaia.ari.uni-heidelberg.de/tap'
CAP = 2 * 1024**3

def request(url, data=None):
    body = None if data is None else urllib.parse.urlencode(data).encode()
    try:
        return urllib.request.urlopen(urllib.request.Request(url, data=body, headers={
            'User-Agent':'HTT-D05-public-research/1', 'Accept-Encoding':'identity'}), timeout=45)
    except urllib.error.HTTPError as exc:
        detail=exc.read().decode(errors='replace')
        ROOT.mkdir(parents=True,exist_ok=True)
        p=ROOT/('http_failure_'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S%f')+'.txt')
        p.write_text(url+'\n'+detail)
        raise RuntimeError(str(exc)+' '+detail[:2000]) from exc

def save_json(p, obj):
    with p.open('w') as f:
        json.dump(obj, f, indent=2); f.write('\n'); f.flush()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('--query',type=Path)
    ap.add_argument('--collect',action='store_true'); args=ap.parse_args()
    ROOT.mkdir(parents=True,exist_ok=True)
    meta=ROOT/(args.name+'.job.json')
    if meta.exists():
        record=json.loads(meta.read_text())
    else:
        if not args.query: raise SystemExit('A new job needs an explicit query file')
        query=args.query.read_text().strip()
        # PENDING creation ensures identity survives before any database work starts.
        with request(BASE+'/async',dict(REQUEST='doQuery',LANG='ADQL',QUERY=query,
                     FORMAT='votable/b2',MAXREC='2500000',RUNID='HTT_D05_'+args.name)) as r:
            job=r.geturl().rstrip('/')
            content=r.read().decode()
        if '/async/' not in job: raise RuntimeError('No durable UWS job URL: '+job+' '+content[:500])
        record=dict(job_url=job,job_id=job.rsplit('/',1)[-1],query=query,
                    query_sha256=hashlib.sha256(query.encode()).hexdigest(),
                    created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    format='votable/b2',maxrec=2500000,phase='CREATED_NOT_STARTED')
        save_json(meta,record)
        print(json.dumps(record),flush=True)
        with request(job+'/phase',{'PHASE':'RUN'}) as r: r.read()
    job=record['job_url']
    with request(job) as r: body=r.read()
    (ROOT/(args.name+'.uws.xml')).write_bytes(body)
    node=ET.fromstring(body); phase=node.findtext('{*}phase'); record['phase']=phase
    save_json(meta,record); print(args.name,phase,job,flush=True)
    if phase=='ERROR':
        with request(job+'/error') as r: err=r.read()
        (ROOT/(args.name+'.error.xml')).write_bytes(err)
        print(err.decode()[:4000]); return 1
    if args.collect and phase=='COMPLETED':
        result=node.find('.//{*}result')
        url=result.get('{http://www.w3.org/1999/xlink}href')
        target=ROOT/(args.name+'.vot'); part=ROOT/(args.name+'.vot.part')
        if target.exists(): print('EXISTING_RESULT',target); return 0
        if part.exists(): raise SystemExit('Partial preserved; inspect before a fresh collection')
        if shutil.disk_usage(ROOT).free < CAP+2*1024**3: raise RuntimeError('Disk reserve')
        h=hashlib.sha256(); n=0
        with request(url) as r, part.open('xb') as out:
            headers=dict(r.headers); expected=r.headers.get('Content-Length')
            while block:=r.read(1024**2):
                n+=len(block)
                if n>CAP: raise RuntimeError('Batch cap exceeded')
                h.update(block);out.write(block)
        if expected is not None and n!=int(expected): raise RuntimeError('HTTP length mismatch')
        part.rename(target)
        record.update(result_url=url,result_path=str(target),bytes=n,sha256=h.hexdigest(),headers=headers)
        save_json(meta,record); print('COLLECTED',n,h.hexdigest(),flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
