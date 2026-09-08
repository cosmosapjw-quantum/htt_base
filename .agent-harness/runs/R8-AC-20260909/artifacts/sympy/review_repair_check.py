"""Independent numerical probes of the repairs, outside the CAS scope."""
import hashlib
import itertools
import json
from fractions import Fraction as F
from pathlib import Path
import mpmath as mp
import numpy as np
from htt.infer.r8_partial_law import (_normal_cdf_bounds,_normalizer_bounds,
                                    _chi_cdf_bounds,normal_critical_square)
from obsstat.r8_orbit_bounds import invariant_lower

mp.mp.dps=120
as_mp=lambda x:mp.mpf(x.numerator)/x.denominator
checks=[]
lo,hi=_normalizer_bounds()
assert as_mp(lo)<=mp.sqrt(2*mp.pi)<=as_mp(hi)
checks.append({'kind':'normalizer','passed':True})
for value in (F(-8),F(-1,10),F(0),F(1,10),F(1),F(2),F(4),F(8)):
    lo,hi=_normal_cdf_bounds(value)
    truth=(1+mp.erf(as_mp(value)/mp.sqrt(2)))/2
    assert as_mp(lo)<=truth<=as_mp(hi),(value,lo,hi,truth)
    checks.append({'kind':'normal_cdf','x':str(value),'passed':True})
for rank,value in itertools.product((1,2,3,5,12,32,64,128,256),(F(0),F(1,4),F(1),F(4),F(16),F(64))):
    lo,hi=_chi_cdf_bounds(value,rank)
    truth=mp.gammainc(mp.mpf(rank)/2,0,as_mp(value)/2,regularized=True)
    assert as_mp(lo)<=truth<=as_mp(hi),(rank,value,lo,hi,truth)
    checks.append({'kind':'chi_cdf','rank':rank,'x':str(value),'passed':True})
for alpha in (F(1,4),F(1,20),F(1,40),F(1,80),F(1,1000000),F(99,100)):
    lo,hi=normal_critical_square(alpha)
    truth=2*mp.erfinv(1-as_mp(alpha))**2
    assert as_mp(lo)<=truth<=as_mp(hi)
    checks.append({'kind':'normal_quantile_square','alpha':str(alpha),'passed':True})
o=np.zeros((3,3,3));o[0,0,0]=2e200
for idx in ((0,1,1),(0,2,2)):
    for p in set(itertools.permutations(idx)):o[p]=-1e200
try:
    invariant_lower((np.eye(3)*1e-200,o),(np.zeros((3,3)),np.zeros((3,3,3))))
    disparate='ACCEPTED_NON_STF'
except ValueError:
    disparate='REFUSED_NON_STF'
root=Path(__file__).resolve().parents[5]
paths=('htt/htt/htt/infer/r8_partial_law.py','htt/obsstat/r8_orbit_bounds.py')
print(json.dumps({'status':'PASS' if disparate=='REFUSED_NON_STF' else 'FAIL',
    'cdf_checks':checks,'disparate_scale_domain_case':disparate,
    'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},
    'mpmath_version':mp.__version__,'precision_digits':mp.mp.dps,
    'scope':'Independent high precision repair checks; not part of five-obligation CAS admission'},indent=2))
