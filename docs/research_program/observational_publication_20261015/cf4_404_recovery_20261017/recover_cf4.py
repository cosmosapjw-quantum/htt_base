#!/usr/bin/env python3
"""Recover CF4 CDS fixed-width originals, or preserve honest VizieR representations.

Requires Python >=3.10, standard library only. Network requires a local HTTPS connection.
There is NO conversion from the VizieR `groups` table to byte-identical table3/4.
HTTP 404 is terminal for that candidate (never retried); HTTP 429/5xx retry once.
Verified existing files are never overwritten. The original Planck tree is untouched.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from urllib import error, request, parse
from datetime import datetime, timezone

CAT = 'J/ApJ/944/94'
ROOT = 'cf4/J_ApJ_944_94'
RECS = {'table2': (55877, 190), 'table3': (38053, 190), 'table4': (38053, 157)}
HOSTS = {'cdsarc.cds.unistra.fr', 'cdsarc.u-strasbg.fr',
         'vizier.cds.unistra.fr', 'vizier.cfa.harvard.edu', 'vizier.nao.ac.jp'}
RAW_BASES = [
    'https://cdsarc.cds.unistra.fr/ftp/J/ApJ/944/94',
    'https://cdsarc.cds.unistra.fr/ftp/cats/J/ApJ/944/94',
    'https://cdsarc.u-strasbg.fr/ftp/pub/cats/J/ApJ/944/94',
]
VIZIER_BASES = ['https://vizier.cds.unistra.fr/viz-bin/asu-tsv',
                'https://vizier.cfa.harvard.edu/viz-bin/asu-tsv',
                'https://vizier.nao.ac.jp/viz-bin/asu-tsv']
CHUNK = 1024*1024


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(CHUNK), b''):
            h.update(b)
    return h.hexdigest()


def write_json(p:Path, value):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp = p.with_suffix(p.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    os.replace(temp,p)


def check_target(root:Path, rel:str)->Path:
    p = Path(rel)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('destination traversal rejected')
    root = root.resolve()
    dest = root.joinpath(*p.parts)
    if any(x.is_symlink() for x in [dest,*[parent for parent in dest.parents if root in [parent,*parent.parents]]]):
        raise ValueError('symlink path rejected')
    if not dest.resolve(strict=False).is_relative_to(root):
        raise ValueError('path escaped root')
    return dest


def check_url(url: str):
    u = parse.urlsplit(url)
    if u.scheme != 'https' or u.hostname not in HOSTS or u.username or u.password:
        raise ValueError('URL origin not allowlisted')


def fetch(url: str, out: Path, *, timeout=90, retries=1):
    """Atomic destination via .part; rejects HTML Anubis/errors and wrong redirects."""
    check_url(url)
    out.parent.mkdir(parents=True,exist_ok=True)
    part = out.with_name(out.name+'.part')
    if out.exists():
        raise FileExistsError(f'refuse overwrite: {out}')
    for attempt in range(retries+1):
        off = part.stat().st_size if part.exists() else 0
        headers={'User-Agent':'HTT-CF4-source-recovery/1.1 (scientific reproducibility)',
                 'Accept-Encoding':'identity'}
        if off:
            headers['Range']=f'bytes={off}-'
        try:
            with request.urlopen(request.Request(url,headers=headers),timeout=timeout) as resp:
                check_url(resp.geturl())
                typ=resp.headers.get('Content-Type','').lower()
                if 'text/html' in typ or 'application/xhtml' in typ:
                    raise ValueError('HTML anti-bot/error body, not data')
                if off and resp.status==206:
                    cr=resp.headers.get('Content-Range','')
                    if not re.match(r'^bytes '+str(off)+r'-[0-9]+/[0-9]+$',cr):
                        raise ValueError('unsafe Content-Range '+cr)
                    mode='ab'
                elif resp.status==200:
                    mode='wb'  # server ignored range, start again
                else:
                    raise ValueError(f'HTTP {resp.status}')
                with part.open(mode) as f:
                    while True:
                        b=resp.read(CHUNK)
                        if not b:break
                        f.write(b)
                    f.flush();os.fsync(f.fileno())
            with part.open('rb') as f:
                first=f.read(512)
            if not first or first.lstrip().lower().startswith((b'<html',b'<!doctype',b'<?xml')):
                raise ValueError('empty or HTML/XML error response')
            os.replace(part,out)
            return
        except error.HTTPError as exc:
            if exc.code in (400,401,403,404,410):
                raise  # terminal for this URL; NEVER retry a 404
            if attempt>=retries:raise
            time.sleep(1.0*(attempt+1))
        except (error.URLError,TimeoutError,ConnectionError,OSError) as exc:
            if attempt>=retries:raise
            time.sleep(1.0*(attempt+1))


def fixed_width_rows(p:Path,name:str)->dict:
    expected, width=RECS[name]
    n=0; smallest=1000000; largest=0; example_id=None
    with p.open('rb') as f:
        for line in f:
            row=line.rstrip(b'\n').rstrip(b'\r')
            n+=1;smallest=min(smallest,len(row));largest=max(largest,len(row))
            if b'\x00' in row or not 30<=len(row)<=width:
                raise ValueError(f'{name}: invalid fixed-width record line {n}, size={len(row)}, target Lrecl={width}')
            if not row[:7].strip().isdigit():
                raise ValueError(f'{name}: first ID invalid on line {n}')
            if example_id is None:example_id=int(row[:7])
    if n!=expected:
        raise ValueError(f'{name}: got {n}, expected {expected} catalog rows')
    return {'rows':n,'lrecl_max':largest,'lrecl_min':smallest,'example_id':example_id}


def decode_gzip_into(gz:Path,dat:Path,name:str)->dict:
    temp=dat.with_name(dat.name+'.inflating')
    if dat.exists():raise FileExistsError(dat)
    try:
        with gzip.open(gz,'rb') as inp, temp.open('wb') as out:
            written=0
            while True:
                chunk=inp.read(CHUNK)
                if not chunk:break
                written+=len(chunk)
                if written>30_000_000:
                    raise ValueError('fixed-width CF4 output over 30MB maximum')
                out.write(chunk)
        meta=fixed_width_rows(temp,name)
        dat.parent.mkdir(parents=True,exist_ok=True)
        os.replace(temp,dat)
        return meta
    finally:
        temp.unlink(missing_ok=True)


def vizier_url(base:str,table:str)->str:
    cat=parse.quote(CAT+'/'+table,safe='/')
    return f'{base}?-source={cat}&-out.max=unlimited&-out.all'


def vizier_rows(p:Path,table:str)->dict:
    expected=55877 if table=='table2' else 38053
    n=0;tabs=0;seen_first=False
    with p.open('rb') as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith((b'#',b'!',b'--')):continue
            if b'\x00' in line:raise ValueError('binary data in TSV')
            if b'\t' not in line:continue
            first=line.split(b'\t',1)[0].strip()
            if re.fullmatch(rb'[1-9][0-9]*',first):
                n+=1;seen_first=True;tabs=max(tabs,line.count(b'\t'))
    if n!=expected:
        raise ValueError(f'VizieR {table}: counted {n} ID rows, expected {expected}. No acceptance of truncated/limited export.')
    if tabs<4 or not seen_first:
        raise ValueError('VizieR TSV lacks expected columns')
    return {'rows':n,'columns_min':tabs+1,'identity':CAT+'/'+table,'format':'VIZIER_TSV_NOT_FIXED_WIDTH_ORIGINAL'}


def record_raw(root:Path,name:str,meta:dict,source_url:str,arch:Path,raw:Path):
    p=root/'provenance'/'DOWNLOAD_RECEIPTS.json'
    r=json.loads(p.read_text()) if p.is_file() else {}
    id='cf4_'+name+'_dat'
    old=r.get(id)
    if old and (old.get('sha256')!=sha256(raw) or old.get('status')!='downloaded'):
        raise ValueError('existing original receipt mismatch; refuse overwrite')
    r[id]={
        'status':'downloaded', 'sha256':sha256(raw), 'bytes':raw.stat().st_size,
        'url_requested':source_url,'url_resolved':source_url,'downloaded_at_utc':datetime.now(timezone.utc).isoformat(),
        'format':'ascii','relative_path':str(raw.relative_to(root)),
        'compressed_archive_sha256':sha256(arch),'compressed_archive_path':str(arch.relative_to(root)),
        'catalogue_layout':'CDS_FIXED_WIDTH', 'fixed_width_validation':meta,
        'source_validation':'transport_and_fixed_width_rows_verified_NOT_selection_covariance_or_physics'
    }
    write_json(p,r)


def recover_raw(root:Path,name:str,timeout=90):
    rel=f'{ROOT}/{name}.dat'
    raw=check_target(root,rel)
    rep=root/'provenance'/'DOWNLOAD_RECEIPTS.json'
    receipt=json.loads(rep.read_text()) if rep.is_file() else {}
    if raw.exists():
        if receipt.get('cf4_'+name+'_dat',{}).get('sha256')==sha256(raw):
            meta=fixed_width_rows(raw,name)
            return {'status':'RAW_ALREADY_VERIFIED','sha256':sha256(raw),'rows':meta['rows']}
        raise ValueError('raw present without matching original receipt: '+str(raw))
    gz=check_target(root,f'{ROOT}/{name}.dat.gz')
    if gz.exists():
        if gz.is_symlink():raise ValueError('unsafe existing gzip symlink')
        try:
            meta=decode_gzip_into(gz,raw,name)
            src=receipt.get('cf4_'+name+'_dat',{}).get('url_requested') or 'PREEXISTING_GZIP_VERIFY_ORIGIN_INDEPENDENTLY'
            record_raw(root,name,meta,src,gz,raw)
            return {'status':'RAW_RECOVERED_FROM_EXISTING_GZIP','sha256':sha256(raw),'rows':meta['rows']}
        except (OSError,ValueError) as exc:
            raise ValueError(f'existing gzip is not valid: {exc}')
    for base in RAW_BASES:
        # Official CDS paths are candidates, not claimed HTTP-200 verified.
        url=base+'/'+name+'.dat.gz'
        try:
            fetch(url,gz,timeout=timeout,retries=1)
            with gz.open('rb') as f:
                if f.read(2)!=b'\x1f\x8b':
                    gz.unlink(missing_ok=True)
                    raise ValueError('response is not gzip')
            meta=decode_gzip_into(gz,raw,name)
            record_raw(root,name,meta,url,gz,raw)
            return {'status':'RAW_RECOVERED_AND_VERIFIED','sha256':sha256(raw),'rows':meta['rows'],'url':url}
        except (error.HTTPError,error.URLError,OSError,ValueError) as exc:
            print(f'RAW CANDIDATE {name}: {url}: {exc}',file=sys.stderr)
            # Range resume MUST NOT cross different candidate URLs.
            partial=gz.with_name(gz.name+'.part')
            if partial.exists():
                quarantine=partial.with_name(partial.name+'.candidate'+str(RAW_BASES.index(base)))
                if not quarantine.exists():os.replace(partial,quarantine)
            if gz.is_file():
                # Response may be corrupt but original archive is provenance evidence;
                # move it aside, never silently use it as accepted raw.
                bad=gz.with_name(gz.name+'.invalid')
                if not bad.exists():os.replace(gz,bad)
            # Remove incomplete .part only on 404, not on interrupted transient download.
            if isinstance(exc,error.HTTPError) and exc.code in (400,401,403,404,410):
                gz.with_name(gz.name+'.part').unlink(missing_ok=True)
    return {'status':'RAW_CDS_UNAVAILABLE','raw_file':str(raw.relative_to(root)),
            'reason':'no verified fixed-width gzip archive from tried public CDS URLs'}


def recover_vizier(root:Path,table:str,timeout=90):
    dest=check_target(root,f'{ROOT}/vizier/{table}.tsv')
    receipt_path=root/'provenance'/'CF4_VIZIER_RECEIPTS.json'
    receipt=json.loads(receipt_path.read_text()) if receipt_path.is_file() else {}
    if dest.exists():
        meta=vizier_rows(dest,table)
        if receipt.get(table,{}).get('sha256')!=sha256(dest):
            raise ValueError(f'{table}: existing VizieR file has no matching receipt; preserve it')
        return {'status':'VIZIER_ALREADY_VERIFIED',**meta,'sha256':sha256(dest)}
    for base in VIZIER_BASES:
        url=vizier_url(base,table)
        try:
            fetch(url,dest,timeout=timeout,retries=1)
            meta=vizier_rows(dest,table)
            obj={'sha256':sha256(dest),'bytes':dest.stat().st_size,'url':url,
                 'relative_path':str(dest.relative_to(root)),**meta}
            receipt[table]=obj
            write_json(receipt_path,receipt)
            return {'status':'VIZIER_REPRESENTATION_VERIFIED',**obj}
        except (error.HTTPError,error.URLError,ValueError,OSError) as exc:
            print(f'VIZIER CANDIDATE {table}: {base}: {exc}',file=sys.stderr)
            partial=dest.with_name(dest.name+'.part')
            if partial.exists():
                quarantine=partial.with_name(partial.name+'.candidate'+str(VIZIER_BASES.index(base)))
                if not quarantine.exists():os.replace(partial,quarantine)
            if dest.exists():
                bad=dest.with_name(dest.name+'.invalid')
                if not bad.exists():os.replace(dest,bad)
            if isinstance(exc,error.HTTPError) and exc.code in (400,401,403,404,410):
                dest.with_name(dest.name+'.part').unlink(missing_ok=True)
    return {'status':'VIZIER_UNAVAILABLE'}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('/mnt/extdrive/workdir/htt_open_data'))
    ap.add_argument('--mode',choices=['auto','raw-only','vizier-only'],default='auto')
    ap.add_argument('--timeout',type=int,default=90)
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args(argv)
    if args.timeout<1:ap.error('timeout must be >0')
    root=args.root.resolve()
    if args.dry_run:
        for name in RECS:
            print(name,'raw .dat.gz candidates:')
            for b in RAW_BASES:print(' ',b+'/'+name+'.dat.gz')
        for table in ('table2','groups'):
            print(table,'official VizieR:')
            for b in VIZIER_BASES:print(' ',vizier_url(b,table))
        return 0
    root.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(root).free < 512*1024**2:
        ap.error('at least 512MB free required')
    result={'schema':'htt.cf4_cds_404_recovery/1',
            'source_catalogue':CAT,
            'original_fixed_width':{},'vizier_alternative':{},
            'warnings':['VizieR groups combines CDS table3 and table4 in a different representation; TSV != byte-identical .dat',
                        'Existing Planck FITS are preserved and not touched',
                        'Transport/rows checks never certify a physical selection or calibration law']}
    if args.mode!='vizier-only':
        for name in RECS:
            try:result['original_fixed_width'][name]=recover_raw(root,name,args.timeout)
            except Exception as e:result['original_fixed_width'][name]={'status':'ERROR','reason':str(e)}
    if args.mode=='vizier-only' or (args.mode=='auto' and any(x['status'] in ('RAW_CDS_UNAVAILABLE','ERROR') for x in result['original_fixed_width'].values())):
        for table in ('table2','groups'):
            try:result['vizier_alternative'][table]=recover_vizier(root,table,args.timeout)
            except Exception as e:result['vizier_alternative'][table]={'status':'ERROR','reason':str(e)}
    result['fixed_width_complete']=all(x.get('status','').startswith('RAW_RECOVERED') or x.get('status')=='RAW_ALREADY_VERIFIED' for x in result['original_fixed_width'].values()) if result['original_fixed_width'] else False
    result['vizier_alternative_complete']=all(result['vizier_alternative'].get(t,{}).get('status') in ('VIZIER_ALREADY_VERIFIED','VIZIER_REPRESENTATION_VERIFIED') for t in ('table2','groups'))
    write_json(root/'provenance'/'CF4_RECOVERY_AUDIT.json',result)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    if result['fixed_width_complete']:
        print('PASS original fixed-width CF4 3 files; original htt_data_fetch --verify --group cf4 may now pass.')
        return 0
    if result['vizier_alternative_complete']:
        print('PARTIAL PASS VizieR table2/groups: valid catalogue representation but NOT raw table3.dat/table4.dat. Do not use raw-only consumers without an explicit adapter.')
        return 0
    print('FAIL: neither complete original raw triplet nor valid alternative pair',file=sys.stderr)
    return 2
if __name__=='__main__':raise SystemExit(main())
