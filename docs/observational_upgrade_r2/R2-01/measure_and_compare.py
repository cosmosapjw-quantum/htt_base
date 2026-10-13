"""Bounded synthetic measurement and archived package compatibility check."""
import hashlib
import json
import platform
from pathlib import Path
import resource
import time
import types
import zipfile
import numpy as np
from common.bulkflow_covariance import SamplingCovariance
from common.structured_inference import StructuredLinearModel

PACKAGE = Path('HTT_OBSERVATIONAL_UPGRADE_R2_20261013_PACKAGE.zip')
PREFIX = 'HTT_OBSERVATIONAL_UPGRADE_R2_20261013/'
with zipfile.ZipFile(PACKAGE) as archive:
    source = archive.read(PREFIX+'code/structured_inference.py')
    baseline = types.ModuleType('r2_package_baseline')
    import sys
    sys.modules[baseline.__name__] = baseline
    exec(compile(source, str(PACKAGE)+'/code/structured_inference.py', 'exec'), baseline.__dict__)
    input_hashes = {name:hashlib.sha256(archive.read(PREFIX+name)).hexdigest() for name in
                    ('NEXT_TASK.json','ANALYSIS_DAG.json','RESULTS.json','review/REVIEW_RESULT.json',
                     'code/structured_inference.py','research/STRUCTURED_DERIVATION.md','evidence/STRUCTURED_TESTS.json')}

def contract(p):
    return dict(observation_order_id='synthetic-seed-20261013',selection_id='all-fixed',
                observation_unit='km/s',coefficient_units=['km/s']*p)
rng=np.random.default_rng(20261013)
n=72; p=6
d=rng.uniform(.5,2,n); U=rng.normal(size=(n,4))*.2; F=rng.normal(size=(n,p)); N=rng.normal(size=(n,2)); y=rng.normal(size=n)
checks=[]
for name,design,nuisance in [('full',F,N),('dependent_nuisance',F,np.column_stack((N,N[:,0]))),
                             ('dependent_signal',np.column_stack((F[:,:5],F[:,0])),N),('complete_alias',N,N)]:
    old=baseline.StructuredLinearModel(design,baseline.DiagonalLowRankCovariance(d,U),nuisance=nuisance)
    new=StructuredLinearModel(design,SamplingCovariance(diagonal=d,low_rank=U),nuisance=nuisance,nuisance_units=["km/s"]*nuisance.shape[1],**contract(design.shape[1]))
    errors={field:float(np.max(np.abs(old.fit(y)[field]-new.fit(y)[field]))) for field in ('estimate','covariance')}
    assert old.rank==new.rank and max(errors.values())<2e-11
    aa=rng.normal(size=design.shape[1]); assert abs(old.compress(y).quadratic(aa)-new.compress(y).quadratic(aa))<2e-10
    checks.append(dict(case=name,rank=int(new.rank),max_abs_errors=errors,status='PASS'))
n,p,k,q=38053,13,8,4
d=rng.uniform(.5,2,n);U=.03*rng.normal(size=(n,k));F=rng.normal(size=(n,p));N=rng.normal(size=(n,q));y=rng.normal(size=n)
start=time.perf_counter()
model=StructuredLinearModel(F,SamplingCovariance(diagonal=d,low_rank=U),nuisance=N,nuisance_units=["km/s"]*q,**contract(p))
fit=model.fit(y); compressed=model.compress(y); influence=model.influence(np.eye(p)[0])
elapsed=time.perf_counter()-start
arrays=[value for value in vars(model).values() if isinstance(value,np.ndarray)]
assert all(a.shape!=(n,n) for a in arrays)
assert model.covariance_operator.dense is None and model.storage_bytes<50_000_000
assert elapsed<30
result=dict(scope='fixed-design synthetic integration; no actual CF4 fit',status='NUMERICALLY_CHECKED_SYNTHETIC',
            requested_executor='gpt-6.1-sol/medium',observed_runtime='UNKNOWN',
            python=platform.python_version(),numpy=np.__version__,package_sha256=hashlib.sha256(PACKAGE.read_bytes()).hexdigest(),
            package_input_sha256=input_hashes,baseline_equivalent_cases=checks,
            benchmark=dict(n=n,p=p,k=k,nuisance_columns=q,elapsed_seconds=elapsed,
                           persistent_model_bytes=model.storage_bytes,input_bytes=sum(a.nbytes for a in (d,U,F,N,y)),
                           dense_covariance_bytes_avoided=n*n*8,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                           memory_note='RSS is whole-process high water, includes baseline imports and prior small tests; persistent bytes sum owned arrays',
                           compressed_scalar_count=p*p+p+1,rank=int(model.rank)))
print(json.dumps(result,indent=2))
