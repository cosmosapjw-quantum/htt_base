"""Targeted reproductions for the one independent R8 production review."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import warnings

import mpmath as mp
import numpy as np
import scipy
from scipy.special import ndtri
from htt.infer.r8_partial_law import gaussian_marginal
from obsstat.r8_orbit_bounds import invariant_lower

mp.mp.dps=100
alpha=Fraction(1,4)
observed=1.150349380376008
threshold=ndtri(1-float(alpha)/2)
reference=mp.sqrt(2)*mp.erfinv(1-mp.mpf(alpha.numerator)/alpha.denominator)
answer=gaussian_marginal(observed,lambda _:0.,1.,'independent exact-normal fixture').accept(None,alpha)
q=np.eye(3)*1e200
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    try:
        b=invariant_lower((q,np.zeros((3,3,3))),(np.zeros((3,3)),np.zeros((3,3,3))))
        stf={'outcome':'ACCEPTED_NON_STF','lo':str(b.lo),'hi':str(b.hi)}
    except ValueError as exc:
        stf={'outcome':'REFUSED_NON_STF','exception':str(exc)}
    except Exception as exc:
        stf={'outcome':'OTHER_EXCEPTION','exception_type':type(exc).__name__,'exception':str(exc)}
    stf['warnings']=[str(w.message) for w in caught]
root=Path(__file__).resolve().parents[5]
paths=['htt/htt/htt/infer/r8_partial_law.py','htt/obsstat/r8_orbit_bounds.py']
result={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'mpmath':mp.__version__,
    'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},
    'R8-REV-SYMPY-01':{'alpha':str(alpha),'observed':repr(observed),'production_threshold':repr(float(threshold)),
        'true_threshold_reference_100_digits':str(reference),'inside_by_high_precision_reference':bool(mp.mpf(observed)<reference),
        'membership':str(answer),'reproduced':str(answer)=='REJECT' and mp.mpf(observed)<reference,
        'reference_scope':'high precision diagnostic, not formally certified special-function enclosure'},
    'R8-REV-SYMPY-02':stf}
print(json.dumps(result,indent=2,sort_keys=True))
