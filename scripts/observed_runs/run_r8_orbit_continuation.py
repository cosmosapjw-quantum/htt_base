#!/usr/bin/env python3
"""One extra bounded checkpoint of each frozen saved mock1 pool."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT,ROOT/'htt',ROOT/'htt/src',ROOT/'htt/htt'):sys.path.insert(0,str(p))
from obsstat.r8_orbit_bounds import restore_pool,refine_pool,save_pool,load_pool
from htt.infer.r8_interval_rank import rank_envelope
from scripts.observed_runs.r8_mocks import write


def cell(args):
    oldpath, out = map(Path,args); old=json.loads(oldpath.read_text()); name=oldpath.stem
    receipt=out/(name+'.json')
    if receipt.exists():
        # A completed fixed continuation is never repeated by restarting driver.
        result=json.loads(receipt.read_text())
        if result['input_sha256']!=hashlib.sha256(oldpath.with_suffix('.npz').read_bytes()).hexdigest():
            raise ValueError('saved input changed')
        load_pool(out/'checkpoints'/(name+'.json'))
        return result
    started=time.monotonic();data=oldpath.with_suffix('.npz')
    with np.load(data,allow_pickle=False) as z:
        pool=restore_pool(zip(z['Q'],z['O']),tuple(z['sample_ids'].tolist()),z['pair_bounds'],old['checkpoint']['target_hash'],old['checkpoint']['total_splits'])
    initial=pool.bounds.copy(); previous_seconds=old['checkpoint']['elapsed_seconds']
    if pool.splits>=100000000 or previous_seconds>=14400:
        checkpoint={'new_splits':0,'elapsed_seconds':0.,'stopping_reason':'SCOPE_CAP_EXHAUSTED'}
    else:
        checkpoint=refine_pool(pool,split_budget=min(1000000,100000000-pool.splits),seconds=min(60.,14400-previous_seconds))
    assert np.all(pool.bounds[:,:,0]>=initial[:,:,0]) and np.all(pool.bounds[:,:,1]<=initial[:,:,1])
    rank=rank_envelope(pool.bounds,0,math.ceil(math.sqrt(len(pool.rows)-1)),F(1,20))
    indices=np.triu_indices(len(pool.rows),1)
    accounting={'previous_seconds':previous_seconds,'cumulative_refinement_seconds':previous_seconds+checkpoint['elapsed_seconds'],
                'legacy_pair_trees':'NOT_SAVED; prior bank retained; new trees started only for visited pairs',
                'old_metadata_sha256':hashlib.sha256(oldpath.read_bytes()).hexdigest()}
    save_pool(pool,out/'checkpoints'/(name+'.json'),accounting)
    result={'M':len(pool.rows),'pool':old['pool'],'input':str(data),'input_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),
            'target_hash':pool.target_hash,'checkpoint':checkpoint,'accounting':accounting,
            'rank':asdict(rank),'old_rank':old['rank']['decision'],
            'old_mean_width':float(np.mean((initial[:,:,1]-initial[:,:,0])[indices])),
            'mean_width':float(np.mean((pool.bounds[:,:,1]-pool.bounds[:,:,0])[indices])),
            'improved_pairs':int(np.count_nonzero((pool.bounds[:,:,1]<initial[:,:,1])[indices])),
            'total_seconds':time.monotonic()-started,'scope':'COMPUTED_STATISTIC_ONLY; no empirical pool law'}
    write(receipt,result)
    print(json.dumps({k:result[k] for k in ('M','pool','mean_width','improved_pairs','total_seconds')}),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--saved-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    paths=[a.saved_root/f'mock1_{m}'/f'mock1_M{m}_{i}.json' for m in (31,301,1000) for i in range(10)]
    if not all(p.is_file() for p in paths):raise SystemExit('fixed pool missing')
    with ProcessPoolExecutor(max_workers=4) as executor: results=list(executor.map(cell,[(str(p),str(a.out)) for p in paths]))
    write(a.out/'summary.json',{'cells':results,'scope':'ONE_FIXED_CONTINUATION_OF_30_EXISTING_POOLS',
        'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('htt/obsstat/r8_orbit_bounds.py','scripts/observed_runs/run_r8_orbit_continuation.py')},
        'scientific_admission':'NOT_ADMITTED; unresolved intervals and independent CAS obligations retained'})
