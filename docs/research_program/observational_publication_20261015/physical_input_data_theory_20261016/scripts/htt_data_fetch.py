#!/usr/bin/env python3
"""Fail-closed, resumable public astronomy download harness. Network NOT tested here.

All relative paths are under --root. No source data is downloaded by this tool in
its development sandbox. Reuse downloaded files only against our own verified receipt.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from urllib import error, request, parse

ALLOWED_HOSTS={"cdsarc.cds.unistra.fr", "cdsarc.u-strasbg.fr",
 "irsa.ipac.caltech.edu", "raw.githubusercontent.com",
 "edd.ifa.hawaii.edu", "data.desi.lbl.gov", "pla.esac.esa.int",
 "gea.esac.esa.int", "zenodo.org"}
CHUNK=4*1024*1024


def secure_dest(root:Path, relative:str)->Path:
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError(f"unsafe relative path: {relative}")
    root=root.resolve()
    out=root.joinpath(*p.parts)
    if out.is_symlink() or any(q.is_symlink() for q in list(out.parents) if q!=root and root in q.parents):
        raise ValueError(f"symlink path rejected: {relative}")
    if not out.resolve(strict=False).is_relative_to(root):
        raise ValueError(f"path outside root: {relative}")
    return out


def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(CHUNK),b''):
            h.update(block)
    return h.hexdigest()


def validate_url(url):
    u=parse.urlsplit(url)
    if u.scheme!='https' or u.hostname not in ALLOWED_HOSTS or u.username or u.password:
        raise ValueError(f"host/scheme not allowed for URL: {url!r}")


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save_json(path:Path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    os.replace(tmp,path)


def detect_payload(part:Path, fmt:str):
    with part.open('rb') as f:
        first=f.read(16384)
    if not first:
        raise ValueError("empty download")
    if first.lstrip().lower().startswith((b'<!doctype html',b'<html',b'<?xml')):
        raise ValueError("server returned HTML/XML/error payload, not source data")
    if fmt=='fits' and not(first.startswith(b'SIMPLE  =') or first.startswith(b'XTENSION=')):
        raise ValueError("FITS header magic mismatch")
    if fmt=='ascii' and (b'\x00' in first):
        raise ValueError("unexpected binary in ASCII catalogue")


def copy_fetch(item,root:Path,receipt:dict,retries:int,timeout:int):
    name=item['id']; url=item['url']; relative=item['path'];fmt=item['format']
    validate_url(url)
    dst=secure_dest(root,relative)
    existing=receipt.get(name)
    if dst.exists():
        if dst.is_symlink() or not dst.is_file():
            raise ValueError(f"not a regular file: {dst}")
        file_hash=digest(dst)
        if existing and existing.get('sha256')==file_hash and existing.get('status')=='downloaded':
            print(f"SKIP verified receipt {name} {file_hash[:12]} ({dst.stat().st_size} bytes)")
            return
        raise ValueError(f"present but not authenticated against receipt: {dst}. Preserve it; do not overwrite. Move manually if source changed.")
    dst.parent.mkdir(parents=True,exist_ok=True)
    part=dst.with_name(dst.name+'.part')
    for attempt in range(retries+1):
        try:
            offset=part.stat().st_size if part.exists() else 0
            headers={'User-Agent':'HTT-source-audit/1.0 (contact: local scientific user)', 'Accept-Encoding':'identity'}
            if offset:
                headers['Range']=f'bytes={offset}-'
            req=request.Request(url,headers=headers)
            with request.urlopen(req,timeout=timeout) as response:
                final=response.geturl();validate_url(final)
                code=response.status
                if offset and code==206:
                    cr=response.headers.get('Content-Range','')
                    if not cr.startswith(f'bytes {offset}-'):
                        raise ValueError(f'wrong Content-Range for resume: {cr!r}')
                    mode='ab'
                elif code==200:
                    # Server ignored range: restart, never append duplicate prefix.
                    mode='wb'
                else:
                    raise ValueError(f'HTTP status {code} not accepted')
                contenttype=response.headers.get('Content-Type','')
                if 'text/html' in contenttype.lower():
                    raise ValueError(f'HTML content type: {contenttype}')
                total=0
                with part.open(mode) as out:
                    while True:
                        block=response.read(CHUNK)
                        if not block:break
                        out.write(block)
                        total+=len(block)
                    out.flush();os.fsync(out.fileno())
                if total==0 and mode=='wb':
                    raise ValueError('zero-length body')
                detect_payload(part,fmt)
                min_b=item.get('min_bytes',1)
                if part.stat().st_size<min_b:
                    raise ValueError(f'truncated: below {min_b} bytes')
                sha=digest(part)
                expected=item.get('expected_sha256')
                if expected and sha!=expected:
                    raise ValueError(f'expected sha256 {expected}, got {sha}')
                os.replace(part,dst)
                receipt[name]={
                    'status':'downloaded','sha256':sha,'bytes':dst.stat().st_size,
                    'url_requested':url,'url_resolved':final,'downloaded_at_utc':stamp(),
                    'format':fmt,'relative_path':relative,
                    'source_validation':'transport_and_payload_checked; scientific survey law NOT validated'
                }
                save_json(root/'provenance'/'DOWNLOAD_RECEIPTS.json',receipt)
                print(f'DONE {name} {dst.stat().st_size} bytes sha256={sha}')
                return
        except (OSError,ValueError,error.HTTPError,error.URLError) as e:
            print(f'ATTEMPT {attempt+1}/{retries+1} {name}: {e}',file=sys.stderr)
            if attempt==retries:raise
            time.sleep(min(2**attempt,12))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('/mnt/extdrive/workdir/htt_open_data'))
    parser.add_argument('--registry',type=Path,default=Path(__file__).resolve().parents[1]/'DATA_REGISTRY.json')
    parser.add_argument('--group',action='append',default=[],help='repeatable group; default cf4+planck_masks')
    parser.add_argument('--id',action='append',default=[],help='specific ID(s), ignores --group')
    parser.add_argument('--list',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--retries',type=int,default=4)
    parser.add_argument('--timeout',type=int,default=120)
    parser.add_argument('--min-free-gib',type=float,default=2.0)
    args=parser.parse_args(argv)
    reg=json.loads(args.registry.read_text())
    if reg['schema']!='htt.open_source_download_registry/1':raise ValueError('unsupported registry schema')
    items=reg['items'];ids=[i['id'] for i in items]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate IDs')
    if args.id:
        unknown=set(args.id)-set(ids)
        if unknown:parser.error(f'unknown IDs {sorted(unknown)}')
        selected=[item for item in items if item['id'] in args.id]
    else:
        groups=args.group or ['cf4','planck_masks']
        selected=[item for item in items if set(item['groups']).intersection(groups)]
    if not selected:parser.error('empty dataset selection')
    for item in selected:
        validate_url(item['url']);secure_dest(args.root,item['path'])
    if args.list or args.dry_run:
        for item in selected:
            print(f"{item['id']:38s} {item['format']:6s} {item['path']}\n  {item['url']}")
        if args.dry_run or args.list:return 0
    root=args.root.resolve()
    root.mkdir(parents=True,exist_ok=True)
    rp=root/'provenance'/'DOWNLOAD_RECEIPTS.json'
    receipt=json.loads(rp.read_text()) if rp.exists() else {}
    if args.verify:
        failures=[]
        for item in selected:
            out=secure_dest(root,item['path'])
            expected=receipt.get(item['id'],{}).get('sha256') or item.get('expected_sha256')
            if not out.is_file() or not expected:
                failures.append((item['id'],'missing or no recorded digest'))
            else:
                got=digest(out)
                if got!=expected:failures.append((item['id'],f'{got} != {expected}'))
                else:print(f"PASS {item['id']} {got}")
        if failures:
            for p in failures:print('FAIL',*p,file=sys.stderr)
            return 2
        return 0
    if args.retries<0 or args.timeout<1:parser.error('invalid retry/timeout')
    if shutil.disk_usage(root).free < args.min_free_gib * 1024**3:
        raise OSError(f'Free disk space below {args.min_free_gib} GiB; change --min-free-gib only after checking dataset sizes')
    failed=[]
    for item in selected:
        try:copy_fetch(item,root,receipt,args.retries,args.timeout)
        except Exception as e:failed.append((item['id'],str(e)))
    if failed:
        for name,msg in failed:print(f'FAIL {name}: {msg}',file=sys.stderr)
        print('Partial .part files deliberately retained. Re-run the same command to resume.',file=sys.stderr)
        return 1
    print(f'Complete: {len(selected)} files. Check {rp}')
    return 0
if __name__=='__main__':raise SystemExit(main())
