#!/usr/bin/env python3
"""Bounded public bare-Commander T pilot; preserve raw unit ambiguity.

IDs 0200..0215 are a resource-bounded sequential pilot chosen before coefficient
inspection, not the complete 100-row temperature bank. Download at most four
at once, retain immutable raw files/hashes, transform RING4096 to mask-first
NESTED parents, and never infer a physical unit from numerical amplitude.
"""
from __future__ import annotations
import concurrent.futures as cf
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


def ring_coarse(p,mask):
    totals=np.zeros(hp.nside2npix(128));counts=np.zeros(len(totals),np.int64)
    with fits.open(p,memmap=True) as h:
        hd=h[1].header
        if hd['NSIDE']!=4096 or hd['ORDERING'].strip()!='RING':raise ValueError('unexpected pixel operator')
        if hd.get('TFIELDS')!=1 or h[1].columns[0].name.lower()!='i_stokes':raise ValueError('expected scalar intensity')
        raw=np.asarray(h[1].data.field(0)).reshape(-1)
        if len(raw)!=hp.nside2npix(4096):raise ValueError('wrong map length')
        hdr={'NSIDE':hd['NSIDE'],'ORDERING':hd['ORDERING'],'TUNIT1':hd.get('TUNIT1',''),
             'COORDSYS':hd.get('COORDSYS',''),'assumed_coordinates':'Galactic product-family convention; absent header not silently bound'}
        squares=0.;maximum=0.;minimum=0.
        for a in range(0,len(raw),1<<20):
            b=min(a+(1<<20),len(raw));pix=hp.ring2nest(4096,np.arange(a,b))
            valid=mask[pix//4];v=np.asarray(raw[a:b],float)
            if not np.isfinite(v[valid]).all() or np.any(abs(v[valid])>1e10):raise ValueError('invalid pixels')
            selected=v[valid];par=pix[valid]//1024
            totals+=np.bincount(par,weights=selected,minlength=len(totals))
            counts+=np.bincount(par,minlength=len(totals))
            squares+=float(selected@selected)
            maximum=max(maximum,float(selected.max()));minimum=min(minimum,float(selected.min()))
        if squares==0:raise ValueError('all-zero intensity is not a temperature reference')
        hdr.update({'retained_raw_rms':(squares/counts.sum())**.5,'retained_raw_min':minimum,'retained_raw_max':maximum})
    return totals/np.maximum(counts,1),counts,hdr


def run():
    CACHE.mkdir(exist_ok=True,parents=True);OUT.mkdir(exist_ok=True,parents=True)
    start=time.monotonic()
    record={'schema':'htt.r66.bare_temperature_pilot/1','status':'RUNNING','ids_predeclared':IDS,
            'selection':'first 16 public temperature IDs, chosen before coefficient inspection; bounded pilot, not all100',
            'max_parallel_downloads':4,'unit_binding':'UNRESOLVED','coordinate_binding':'conditional product-family Galactic assumption',
            'source_code_sha256':ex.sha(Path(__file__)),'sources':[],'completed_ids':[]}
    ex.save_json(OUT/'TEMPERATURE_PILOT.json',record)
    # Begin network work while constructing the identical 4096-native map operator.
    pool=cf.ThreadPoolExecutor(max_workers=4)
    futures={pool.submit(download,i):i for i in IDS if i!=200}
    mask=ex.mask2048();moments,count=ex.native_moments(4096,mask);operators={}
    for nside,lmax in ex.SPECS:
        key=f'n{nside}_l{lmax}';m,cn=ex.downgrade_moments(moments,count,nside)
        n=np.column_stack(hp.pix2vec(nside,np.arange(hp.nside2npix(nside)),nest=True))
        h,labels=rq.harmonic_design(n,lmax);h[:,1:9]=m
        operators[key]=rq.estimator(h,cn/((4096//nside)**2)>=.995,labels)
    del moments
    print('operators ready',flush=True)
    rows={};receipts={}
    def consume(receipt):
        i=receipt['id'];x,c,hdr=ring_coarse(Path(receipt['path']),mask)
        if not np.array_equal(c,count):raise ValueError('RING/NESTED mask count mismatch')
        coeff={}
        for nside,lmax in ex.SPECS:
            key=f'n{nside}_l{lmax}'
            coeff[key]=operators[key].extract(ex.coarse_map(x,c,nside))
        rows[i]=coeff;receipt['header_and_content']=hdr;receipts[i]=receipt
        record['sources']=[receipts[j] for j in sorted(receipts)]
        record['completed_ids']=sorted(rows);record['elapsed_seconds']=time.monotonic()-start
        payload={'mc_ids':np.array(sorted(rows))}
        payload.update({f'MC_{k}':np.array([rows[j][k] for j in sorted(rows)]) for k in operators})
        np.savez_compressed(OUT/'temperature_pilot_native_units.npz',**payload)
        ex.save_json(OUT/'TEMPERATURE_PILOT.json',record)
        print(json.dumps({'extracted':i,'rows':len(rows),'elapsed_seconds':record['elapsed_seconds']}),flush=True)
    # The first file was started before this bounded pilot was fixed.
    if path(200).exists():consume(download(200))
    for future in cf.as_completed(futures):
        consume(future.result())
        if 200 not in rows and path(200).exists():consume(download(200))
    pool.shutdown()
    if 200 not in rows:consume(download(200))
    if sorted(rows)!=IDS:raise ValueError('pilot is incomplete')
    record.update({'status':'COMPLETE_NATIVE_UNIT_PILOT','carrier_sha256':ex.sha(OUT/'temperature_pilot_native_units.npz'),
                   'completed_rows':len(rows),'elapsed_seconds':time.monotonic()-start})
    ex.save_json(OUT/'TEMPERATURE_PILOT.json',record)
    print(json.dumps({'status':record['status'],'rows':len(rows),'seconds':record['elapsed_seconds']}),flush=True)

if __name__=='__main__':run()
