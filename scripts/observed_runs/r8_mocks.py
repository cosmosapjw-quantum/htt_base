#!/usr/bin/env python3
"""Fixed R8 A/C numerical experiments; no actual product-law admission."""
from __future__ import annotations
import argparse
from dataclasses import asdict
from fractions import Fraction as F
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
from scipy.stats import beta
ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT/'htt',ROOT/'htt/src',ROOT/'htt/htt',ROOT):sys.path.insert(0,str(p))
from htt.infer.r8_interval_rank import rank_envelope
from htt.infer.r8_partial_law import gaussian_marginal,marginal_acceptance
from htt.infer.r8_simulator_calibration import ToyLocationLaw,AbsoluteResidual,candidate_rank
from obsstat.r8_orbit_bounds import initialize_pool,refine_pool

ALPHA=F(1,20)

def encode(x):
    if isinstance(x,F):return {'numerator':x.numerator,'denominator':x.denominator}
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,np.ndarray):return x.tolist()
    if hasattr(x,'__dataclass_fields__'):return asdict(x)
    raise TypeError(type(x).__name__)

def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,default=encode,indent=2,allow_nan=False)+'\n')

def upper_binomial(failures,n,delta):return 1. if failures==n else float(beta.ppf(1-delta,failures+1,n-failures))

def mock3():
    rng=np.random.default_rng(81005);n=10000;reject=0;conservative=0;unresolved=0
    for _ in range(n):
        y=rng.normal(size=31);d=np.abs(y[:,None]-y[None,:]);masked=d.copy();np.fill_diagonal(masked,np.inf)
        scores=np.partition(masked,5,axis=1)[:,5];exact=F(int(np.count_nonzero(scores>=scores[0])),31)
        b=np.stack([np.floor(d),np.ceil(d)+1.],axis=-1);b[np.arange(31),np.arange(31)]=0.
        broad=rank_envelope(b,0,6,ALPHA)
        assert broad.p_lower<=exact<=broad.p_upper
        # Fix only observation-incident exact distances; the rest remain wide.
        b[0,:,0]=b[0,:,1]=d[0];b[:,0]=b[0]
        refined=rank_envelope(b,0,6,ALPHA)
        assert broad.p_lower<=refined.p_lower<=exact<=refined.p_upper<=broad.p_upper
        assert refined.decision!='REJECT' or exact<=ALPHA
        reject+=exact<=ALPHA;conservative+=refined.decision=='REJECT';unresolved+=refined.decision=='UNRESOLVED'
    upper=upper_binomial(reject,n,.01)
    return dict(seed=81005,trials=n,M=31,k=6,exact_rejections=reject,interval_rejections=conservative,
                unresolved=unresolved,binomial_upper_99=upper,tolerance=.06,diagnostic_pass=upper<=.06,
                every_trial_rank_enclosed=True,scope='SCALAR_RANK_SOFTWARE_ONLY')

def mock4():
    streams=np.random.SeedSequence(81006).spawn(3);cells=[]
    for rho,seed in zip((-1,0,1),streams):
        rng=np.random.default_rng(seed);z=rng.normal(size=(10000,2))
        y=np.c_[z[:,0],rho*z[:,0]+math.sqrt(1-rho*rho)*z[:,1]]
        failures=0
        for a,b in y:
            blocks={'a':gaussian_marginal(a,float,1.,'KNOWN_STANDARD_NORMAL_MARGINAL'),
                    'b':gaussian_marginal(b,float,1.,'KNOWN_STANDARD_NORMAL_MARGINAL')}
            failures+=marginal_acceptance(blocks,0.,{'a':F(1,40),'b':F(1,40)})=='REJECT'
        upper=upper_binomial(failures,len(y),.01/3)
        cells.append(dict(rho=rho,trials=len(y),rejections=failures,binomial_upper=upper,
            failure_budget=.01/3,tolerance=.06,diagnostic_pass=upper<=.06,seed_spawn_key=seed.spawn_key,
            duplicate_semantics='rho +1 uses the same latent draw; rho -1 its negative'))
    return dict(seed=81006,cells=cells,scope='KNOWN_MARGINALS_WITH_ARBITRARY_COPULA; structural support separately exact-tested')

def mock5():
    cells=[]
    for kind,seed in zip(('student5','mixture','selected_normal'),(81007,81008,81009)):
        for mu,stream in zip((-1.,0.,1.),np.random.SeedSequence(seed).spawn(3)):
            rng=np.random.default_rng(stream);reject=0;unavailable=0
            prototype=ToyLocationLaw(kind,0.)
            for _ in range(1000):
                observed=float(prototype.sample(mu,1,rng)[0]);law=ToyLocationLaw(kind,observed)
                result=candidate_rank(law,mu,199,int(rng.integers(0,2**63)),AbsoluteResidual())
                if result.pvalue is None:unavailable+=1
                else:reject+=result.pvalue<=ALPHA
            upper=upper_binomial(reject,1000,.01/9)
            cells.append(dict(law=kind,mu=mu,seed=seed,spawn_key=stream.spawn_key,trials=1000,N=199,
                rejections=reject,unavailable=unavailable,binomial_upper=upper,failure_budget=.01/9,
                tolerance=.085,diagnostic_pass=upper<=.085 and unavailable==0))
    return dict(cells=cells,scope='NINE_FIXED_TOY_EXPERIMENTS_ONLY; no CF4/JWST simulator admission')

def stf_basis():
    from obsstat.planck_lowell_irrep_projection import stf2_components_to_tensor,stf3_components_to_tensor
    bases=[]
    for n,fn in ((5,stf2_components_to_tensor),(7,stf3_components_to_tensor)):
        raw=np.stack([fn(v).ravel() for v in np.eye(n)],axis=1)
        component_basis=np.linalg.inv(np.linalg.cholesky(raw.T@raw).T)
        orthonormal=np.stack([fn(v).ravel() for v in component_basis.T])
        assert np.allclose(orthonormal@orthonormal.T,np.eye(n),atol=2e-15,rtol=0)
        bases.append(orthonormal.reshape((n,)+(3,)*(2 if n==5 else 3)))
    return bases

def mock1(run_dir,oracle_path,size=None):
    spec=importlib.util.spec_from_file_location('independent_r8_oracle',oracle_path)
    oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    basis_q,basis_o=stf_basis();cells=[]
    for m,seed in ((31,81001),(301,81002),(1000,81003)):
        if size is not None and m!=size:continue
        for index,stream in enumerate(np.random.SeedSequence(seed).spawn(10)):
            started=time.monotonic();rng=np.random.default_rng(stream)
            q=np.einsum('na,aij->nij',rng.normal(size=(m,5))*1e-5,basis_q)
            o=np.einsum('na,aijk->nijk',rng.normal(size=(m,7))*1e-5,basis_o)
            # Decode unique STF coordinates once. QR/BLAS rounding must not
            # introduce unequal copies of nominally symmetric components.
            from obsstat.planck_lowell_irrep_projection import stf2_components_to_tensor,stf3_components_to_tensor
            q=np.stack([stf2_components_to_tensor([v[0,0],v[1,1],v[0,1],v[0,2],v[1,2]]) for v in q])
            o=np.stack([stf3_components_to_tensor([v[0,0,0],v[0,0,1],v[0,0,2],v[0,1,1],v[0,1,2],v[1,1,1],v[1,1,2]]) for v in o])
            rows=tuple(zip(q,o));ids=tuple(f'mock{m}:{index}:{i}' for i in range(m))
            pool=initialize_pool(rows,ids);initial_seconds=time.monotonic()-started
            refs=[]
            for i,j in itertools.islice(itertools.combinations(range(m),2),100):
                reference=oracle.reference_pair(rows[i],rows[j]);lo,hi=reference['lo'],reference['hi']
                assert F(pool.bounds[i,j,0])<=lo<=hi<=F(pool.bounds[i,j,1])
                refs.append(dict(i=i,j=j,lo=str(lo),hi=str(hi)))
            # One registered checkpoint, not a claim that the scope cap was used.
            checkpoint=refine_pool(pool,0,seconds=60.)
            rank=rank_envelope(pool.bounds,0,math.ceil(math.sqrt(m-1)),ALPHA)
            path=Path(run_dir)/f'mock1_M{m}_{index}.npz'
            np.savez_compressed(path,Q=q,O=o,pair_bounds=pool.bounds,sample_ids=ids)
            widths=pool.bounds[:,:,1]-pool.bounds[:,:,0];i,j=np.triu_indices(m,1)
            result=dict(M=m,pool=index,seed=seed,spawn_key=stream.spawn_key,k=rank.k,
                initial_seconds=initial_seconds,elapsed_seconds=time.monotonic()-started,
                initialized_pairs=m*(m-1)//2,positive_lowers=int(np.count_nonzero(pool.bounds[i,j,0]>0)),
                mean_width=float(widths[i,j].mean()),max_width=float(widths[i,j].max()),
                rank=rank,checkpoint=checkpoint,artifact=str(path),
                reference_intervals=refs,scope='COMPUTED_STATISTIC_ENCLOSURES; CAS acceptance separately recorded')
            write(Path(run_dir)/f'mock1_M{m}_{index}.json',result);cells.append(result)
            print(json.dumps({k:result[k] for k in ('M','pool','elapsed_seconds','initialized_pairs','positive_lowers','mean_width')}) ,flush=True)
    return dict(cells=cells,oracle_sha256=hashlib.sha256(Path(oracle_path).read_bytes()).hexdigest(),
                numpy_version=np.__version__,generator='NumPy PCG64 SeedSequence child streams',scope='30 RUNTIME_POOLS; NO SIZE_OR_POWER_CLAIM')

def main():
    p=argparse.ArgumentParser();p.add_argument('--mock',choices=('1','3','4','5'),required=True)
    p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--oracle',type=Path);p.add_argument('--size',type=int,choices=(31,301,1000));a=p.parse_args()
    a.run_dir.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    result=mock1(a.run_dir,a.oracle,a.size) if a.mock=='1' else globals()['mock'+a.mock]()
    result.update(elapsed_seconds=time.monotonic()-start,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  numpy_version=np.__version__,generator='PCG64')
    write(a.run_dir/f'mock{a.mock}.json',result)
    print(json.dumps({'mock':a.mock,'elapsed_seconds':result['elapsed_seconds'],'artifact':str(a.run_dir/f'mock{a.mock}.json')}),flush=True)
if __name__=='__main__':main()
