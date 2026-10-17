"""Official-source allowlisted PR3 SMICA download with bounded HTTP 206 resumption.

Downloads are data-acquisition receipts, never scientific E/B or publisher-signed
hash admissions. The pre-existing .part file survives an interrupted transfer.
"""
from __future__ import annotations
import argparse
from http.client import IncompleteRead
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen
from l01_smica_fits_integrity import inspect_smica_fits

INDEX = 'https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html'
PREFIX = 'https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/maps/component-maps/cmb/'
NAME = 'COM_CMB_IQU-smica_2048_R3.00_'
PRODUCTS = ('full','hm1','hm2','oe1','oe2')
PIXELS = 12 * 2048**2
MIN_BYTES = {'full':40*PIXELS, **{p:12*PIXELS for p in PRODUCTS[1:]}}


def filename(product):
    if product not in PRODUCTS:
        raise ValueError('PRODUCT_NOT_IRSA_ALLOWLISTED')
    return NAME+product+'.fits'


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):
            h.update(b)
    return h.hexdigest()


def verify_local_file(path,product):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError('NOT_REGULAR_FITS')
    if p.stat().st_size<MIN_BYTES[product] or p.stat().st_size%2880:
        raise ValueError('FITS_SIZE_OR_PADDING')
    layout=inspect_smica_fits(p,product)
    return {'size_bytes':p.stat().st_size,'sha256_local':digest(p),
            'fits_hdu_status':layout['status'],
            'provenance':'DOWNLOADED_LOCAL_BYTES_NOT_PUBLISHER_SIGNED'}


def _resume_headers(start):
    h={'User-Agent':'htt_base-Planck-PR3-source/2', 'Accept-Encoding':'identity'}
    if start:
        h['Range']=f'bytes={start}-'
    return h


def transfer(product,root,*,timeout=120,chunk_mib=8,opener=None):
    if timeout<=0 or not(1<=chunk_mib<=128):
        raise ValueError('DOWNLOAD_PARAMETER')
    fname=filename(product)
    path=Path(root)/'planck/PR3/cmb'/fname
    url=PREFIX+fname
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_symlink():
        raise ValueError('TARGET_SYMLINK_REJECTED')
    if path.exists():
        return dict(verify_local_file(path,product),status='EXISTING_REUSED',path=str(path),url=url)
    tmp=Path(str(path)+'.part')
    if tmp.is_symlink() or (tmp.exists() and not tmp.is_file()):
        raise ValueError('PARTIAL_NOT_REGULAR_FILE')
    start=tmp.stat().st_size if tmp.exists() else 0
    connection=opener or (lambda req:urlopen(req,timeout=timeout))
    res=connection(Request(url,headers=_resume_headers(start)))
    expected_total=None
    try:
        status=getattr(res,'status',None)
        if status is None: status=res.getcode()
        if status==206:
            if not start:
                raise ValueError('UNREQUESTED_HTTP_PARTIAL_CONTENT')
            cr=str(res.headers.get('Content-Range','')).strip()
            m=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',cr)
            if not m or int(m.group(1))!=start or int(m.group(2))<start:
                raise ValueError('UNVERIFIED_HTTP_RANGE_RESUME')
            final=int(m.group(2));total=int(m.group(3))
            if final>=total:
                raise ValueError('INVALID_HTTP_CONTENT_RANGE_TOTAL')
            clen=str(res.headers.get('Content-Length','')).strip()
            if clen.isdigit() and int(clen)!=final-start+1:
                raise ValueError('HTTP_206_CONTENT_LENGTH_MISMATCH')
            mode='ab';expected_total=total
        elif status==200:
            if start:
                raise ValueError('HTTP_RANGE_IGNORED__PARTIAL_PRESERVED')
            clen=str(res.headers.get('Content-Length','')).strip()
            expected_total=int(clen) if clen.isdigit() else None
            mode='xb'
        else:
            raise ValueError(f'UNEXPECTED_HTTP_STATUS_{status}')
        with tmp.open(mode) as dst:
            while True:
                block=res.read(chunk_mib<<20)
                if not block:break
                dst.write(block)
            dst.flush();os.fsync(dst.fileno())
    finally:
        res.close()
    current=tmp.stat().st_size
    if expected_total is not None and current!=expected_total:
        raise ValueError('DOWNLOAD_INCOMPLETE')
    receipt=verify_local_file(tmp,product)
    # Atomic no-replacement install on the same filesystem as the partial.
    try:
        os.link(tmp,path,follow_symlinks=False)
    except FileExistsError as exc:
        raise ValueError('TARGET_RACED_NOT_OVERWRITTEN') from exc
    tmp.unlink()
    return dict(receipt,status='DOWNLOADED_FITS_FRAMING_VALID',path=str(path),url=url,irsa_index=INDEX)


def transfer_with_retry(product,root,*,attempts=3,transfer_fn=transfer,timeout=120):
    """Only retry a verified short transfer, resuming the preserved .part.

    HTTP 4xx, an ignored Range, wrong FITS headers and source mismatch are hard
    failures rather than a license for repeated full downloads.
    """
    if not 1<=attempts<=8:
        raise ValueError('DOWNLOAD_ATTEMPTS_RANGE_1_TO_8')
    for i in range(attempts):
        try:
            return transfer_fn(product,root,timeout=timeout)
        except (ValueError,IncompleteRead,ConnectionResetError,TimeoutError) as exc:
            transient=isinstance(exc,(IncompleteRead,ConnectionResetError,TimeoutError)) or str(exc)=='DOWNLOAD_INCOMPLETE'
            if not transient or i==attempts-1:
                raise


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',default='/mnt/extdrive/workdir/htt_open_data')
    ap.add_argument('--products',nargs='+',choices=PRODUCTS,default=['full'])
    ap.add_argument('--dry-run',action='store_true')
    ap.add_argument('--timeout',type=int,default=120)
    ap.add_argument('--attempts',type=int,default=3)
    args=ap.parse_args(argv)
    result={'schema':'htt.Planck_PR3_SMICA_source_fetch/2','data':[],
            'physical_simulation_admission':'NOT_ESTABLISHED'}
    failed=False
    for name in dict.fromkeys(args.products):
        if args.dry_run:
            record={'product':name,'url':PREFIX+filename(name),
                    'minimum_bytes':MIN_BYTES[name],'status':'DRY_RUN'}
        else:
            try:
                record=dict(product=name,**transfer_with_retry(name,args.root,attempts=args.attempts,timeout=args.timeout))
            except (ValueError,OSError,IncompleteRead,TimeoutError) as exc:
                failed=True
                record={'product':name,'status':'TRANSFER_NOT_ADMITTED',
                        'error_type':type(exc).__name__,'error':str(exc),
                        'partial_path':str(Path(args.root)/'planck/PR3/cmb'/(filename(name)+'.part')),
                        'next_action':'KEEP_PARTIAL__INSPECT_SOURCE_AND_RETRY_VERIFIED_HTTP_RANGE'}
        result['data'].append(record)
    print(json.dumps(result,indent=2,sort_keys=True))
    return 2 if failed else 0

if __name__=='__main__':raise SystemExit(main())
