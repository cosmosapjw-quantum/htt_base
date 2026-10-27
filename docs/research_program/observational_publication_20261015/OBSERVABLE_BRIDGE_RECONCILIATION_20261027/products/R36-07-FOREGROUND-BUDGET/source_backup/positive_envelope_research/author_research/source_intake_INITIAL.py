"""Public, unauthenticated source intake for the continuing R36-07 issue."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import time
import urllib.request

ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'source'
CACHE.mkdir(parents=True,exist_ok=True)
SOURCES=[
 'https://lambda.gsfc.nasa.gov/data/foregrounds/haslam_2014/haslam408_ds_Remazeilles2014.fits',
 'https://lambda.gsfc.nasa.gov/data/foregrounds/haslam/lambda_haslam408_nofilt.fits',
 'https://lambda.gsfc.nasa.gov/data/cobe/dirbe/aam/DIRBE_BAND10_AAM_P3B.FITS',
 'https://lambda.gsfc.nasa.gov/data/cobe/dirbe/ancil/spec_resp/DIRBE_SYSTEM_SPECTRAL_RESPONSE_TABLE.ASC',
 'https://lambda.gsfc.nasa.gov/data/cobe/dirbe/ancil/skyinfo/DIRBE_SKYMAP_INFO.FITS',
 'https://lambda.gsfc.nasa.gov/data/cobe/dirbe/ancil/beam_char/DIRBE_BEAM_CHARACTERISTICS_P3B.ASC',
 'https://lambda.gsfc.nasa.gov/data/cobe/dirbe/doc/des_v2_3.pdf',
 'https://lambda.gsfc.nasa.gov/product/foreground/fg_2014_haslam_408_info.html',
 'https://lambda.gsfc.nasa.gov/product/cobe/dirbe_products.html',
 'https://lambda.gsfc.nasa.gov/product/cobe/c_anual_avskymap.html',
 'https://lambda.gsfc.nasa.gov/product/cobe/dirbe_skymap_info.html',
 'https://arxiv.org/html/1411.3628',
]
receipt=ROOT/'SOURCE_INTAKE.json'
rows=json.loads(receipt.read_text()) if receipt.exists() else []
for url in SOURCES:
    name=url.rsplit('/',1)[-1]
    if '.' not in name:name+='\.html'
    dest=CACHE/name
    if dest.exists():
        print('CACHE',name,flush=True)
        continue
    started=time.monotonic()
    part=dest.with_name(dest.name+'.part')
    if part.exists():raise RuntimeError('Preserve and diagnose prior partial intake before replay: '+str(part))
    row={'url':url,'path':str(dest),'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(url,timeout=60) as r,part.open('wb') as f:
            row.update(status_code=r.status,final_url=r.url,content_length=r.headers.get('Content-Length'),last_modified=r.headers.get('Last-Modified'),etag=r.headers.get('ETag'))
            h=hashlib.sha256();size=0
            while True:
                block=r.read(1<<20)
                if not block:break
                stat=os.statvfs(CACHE)
                if stat.f_bavail*stat.f_frsize-len(block)<2*(1<<30):raise RuntimeError('Owner 2 GiB free reserve')
                f.write(block);h.update(block);size+=len(block)
        if row['content_length'] is not None and size!=int(row['content_length']):raise RuntimeError('HTTP_CONTENT_LENGTH_MISMATCH')
        part.rename(dest)
        row.update(status='ACQUIRED',bytes=size,sha256=h.hexdigest(),elapsed_seconds=time.monotonic()-started)
    except Exception as ex:
        row.update(status='FAILED_PRESERVED',exception_type=type(ex).__name__,message=str(ex),elapsed_seconds=time.monotonic()-started)
    rows.append(row)
    receipt.write_text(json.dumps(rows,indent=2)+'\n')
    print(row['status'],name,row.get('bytes'),flush=True)
