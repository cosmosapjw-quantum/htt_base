#!/usr/bin/env python3
"""Bounded public bare-Commander T pilot; preserve raw unit ambiguity.

The initial 16-file concurrent attempt failed with premature HTTP responses.
This repaired command defaults to cached-only content inspection of ID0200.
An explicit --download flag permits sequential acquisition; no automatic retry.
Retain immutable raw files/hashes, transform RING4096 to mask-first
NESTED parents, and never infer a physical unit from numerical amplitude.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import requests
import numpy as np
import healpy as hp
from astropy.io import fits

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/r66'))
import extract_r66_commander as ex
from htt.htt.infer import r66_radiation_quotient as rq
OUT=ex.OUT
CACHE=Path('/mnt/extdrive/workdir/htt_open_data/r66_temperature_actual')
EXPECTED_BYTES=1610622720
IDS=list(range(200,216))


def url(i):return 'https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID='+f'npipe6v20_commander_cmb_mc_{i:04d}.fits'
def path(i):return CACHE/f'npipe6v20_commander_cmb_mc_{i:04d}.fits'


def download(i):
    p=path(i);receipt=Path(str(p)+'.r66_verified.json')
    if p.exists():
        if p.stat().st_size!=EXPECTED_BYTES:raise ValueError('unexpected existing length')
        digest=ex.sha(p)
    else:
        if i==200 and Path(str(p)+'.partial').exists():
            raise RuntimeError('external 0200 download must finish before pilot consumes it')
        partial=Path(str(p)+'.r66_partial');h=hashlib.sha256();n=0;start=time.monotonic()
        with requests.get(url(i),stream=True,timeout=(20,90)) as r:
            r.raise_for_status()
            with partial.open('wb') as f:
                for chunk in r.iter_content(4<<20):
                    if chunk:f.write(chunk);h.update(chunk);n+=len(chunk)
        if n!=EXPECTED_BYTES:raise ValueError(f'wrong HTTP payload length {i}: {n}')
        os.replace(partial,p);digest=h.hexdigest()
        print(json.dumps({'download_complete':i,'bytes':n,'seconds':time.monotonic()-start}),flush=True)
    obj={'id':i,'path':str(p),'public_url':url(i),'bytes':EXPECTED_BYTES,'sha256':digest,
         'product_bank':'bare scalar Commander temperature 0200..0299',
         'unit_binding':'UNRESOLVED: TUNIT1 blank; raw values remain native numeric units'}
    ex.save_json(receipt,obj)
    return obj


def ring_coarse(p,mask,native=4096,target=128,mask_nside=2048,chunk_pixels=1<<20):
    totals=np.zeros(hp.nside2npix(target));counts=np.zeros(len(totals),np.int64)
    with fits.open(p,memmap=True) as h:
        hd=h[1].header
        if hd['NSIDE']!=native or hd['ORDERING'].strip()!='RING':raise ValueError('unexpected pixel operator')
        if hd.get('TFIELDS')!=1 or h[1].columns[0].name.lower()!='i_stokes':raise ValueError('expected scalar intensity')
        raw=np.asarray(h[1].data.field(0)).reshape(-1)
        if len(raw)!=hp.nside2npix(native):raise ValueError('wrong map length')
        hdr={'NSIDE':hd['NSIDE'],'ORDERING':hd['ORDERING'],'TUNIT1':hd.get('TUNIT1',''),
             'COORDSYS':hd.get('COORDSYS',''),'assumed_coordinates':'Galactic product-family convention; absent header not silently bound'}
        squares=0.;maximum=-np.inf;minimum=np.inf
        for a in range(0,len(raw),chunk_pixels):
            b=min(a+chunk_pixels,len(raw));pix=hp.ring2nest(native,np.arange(a,b))
            valid=mask[pix//((native//mask_nside)**2)];v=np.asarray(raw[a:b],float)
            if not np.isfinite(v[valid]).all() or np.any(abs(v[valid])>1e10):raise ValueError('invalid pixels')
            selected=v[valid]
            if not selected.size:continue  # a fully masked RING chunk has no extrema
            par=pix[valid]//((native//target)**2)
            totals+=np.bincount(par,weights=selected,minlength=len(totals))
            counts+=np.bincount(par,minlength=len(totals))
            squares+=float(selected@selected)
            maximum=max(maximum,float(selected.max()));minimum=min(minimum,float(selected.min()))
        if squares==0:raise ValueError('all-zero intensity is not a temperature reference')
        hdr.update({'retained_raw_rms':(squares/counts.sum())**.5,'retained_raw_min':minimum,'retained_raw_max':maximum})
    return totals/np.maximum(counts,1),counts,hdr


def run():
    ap=argparse.ArgumentParser();ap.add_argument('--count',type=int,default=1)
    ap.add_argument('--download',action='store_true');args=ap.parse_args()
    if not 1<=args.count<=100:raise ValueError('count must lie in1..100')
    ids=list(range(200,200+args.count))
    CACHE.mkdir(exist_ok=True,parents=True);OUT.mkdir(exist_ok=True,parents=True)
    start=time.monotonic()
    record={'schema':'htt.r66.bare_temperature_content/2','status':'RUNNING','ids_selected':ids,
            'selection':'sequential public scalar-T IDs; content qualification only',
            'max_parallel_downloads':1,'download_enabled':args.download,
            'unit_binding':'UNRESOLVED','coordinate_binding':'conditional product-family Galactic assumption',
            'source_code_sha256':ex.sha(Path(__file__)),'sources':[],'completed_ids':[]}
    ex.save_json(OUT/'TEMPERATURE_CONTENT_PILOT.json',record)
    mask=ex.mask2048();moments,count=ex.native_moments(4096,mask);operators={}
    for nside,lmax in ex.SPECS:
        key=f'n{nside}_l{lmax}';m,cn=ex.downgrade_moments(moments,count,nside)
        n=np.column_stack(hp.pix2vec(nside,np.arange(hp.nside2npix(nside)),nest=True))
        h,labels=rq.harmonic_design(n,lmax);h[:,1:9]=m
        operators[key]=rq.estimator(h,cn/((4096//nside)**2)>=.995,labels)
    del moments
    rows={}
    for i in ids:
        try:
            if not path(i).exists() and not args.download:raise RuntimeError('cached-only mode; complete raw file unavailable')
            receipt=download(i);x,c,hdr=ring_coarse(Path(receipt['path']),mask)
            if not np.array_equal(c,count):raise ValueError('RING/NESTED mask count mismatch')
            rows[i]={}
            for nside,lmax in ex.SPECS:
                key=f'n{nside}_l{lmax}'
                rows[i][key]=operators[key].extract(ex.coarse_map(x,c,nside))
            receipt['header_and_content']=hdr;record['sources'].append(receipt)
            record['completed_ids']=sorted(rows);record['elapsed_seconds']=time.monotonic()-start
            payload={'mc_ids':np.array(sorted(rows))}
            payload.update({f'MC_{k}':np.array([rows[j][k] for j in sorted(rows)]) for k in operators})
            np.savez_compressed(OUT/'temperature_content_native_units.npz',**payload)
            ex.save_json(OUT/'TEMPERATURE_CONTENT_PILOT.json',record)
            print(json.dumps({'extracted':i,'rows':len(rows),'seconds':record['elapsed_seconds']}),flush=True)
        except Exception as e:
            record.update({'status':'BLOCKED_CONTENT_OR_ACQUISITION','failed_id':i,'error_type':type(e).__name__,
                           'error':str(e),'completed_rows':len(rows),'automatic_retry':False})
            ex.save_json(OUT/'TEMPERATURE_CONTENT_PILOT.json',record)
            raise
    record.update({'status':'COMPLETE_NATIVE_UNIT_CONTENT_PILOT',
        'carrier_sha256':ex.sha(OUT/'temperature_content_native_units.npz'),
        'completed_rows':len(rows),'qualified_physical_reference_rows':0,
        'use':'content/operator diagnostic only; no covariance or PTE estimated from this pilot',
        'elapsed_seconds':time.monotonic()-start})
    ex.save_json(OUT/'TEMPERATURE_CONTENT_PILOT.json',record)
    print(json.dumps({'status':record['status'],'rows':len(rows),'seconds':record['elapsed_seconds']}),flush=True)

if __name__=='__main__':run()
