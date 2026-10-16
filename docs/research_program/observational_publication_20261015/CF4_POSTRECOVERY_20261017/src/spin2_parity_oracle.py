"""Exact non-full-sky spin-2 leakage oracle for ell=m=2 and W=1+epsilon*cos(theta).

Conventions: spin +2 and -2 Y22 squared magnitudes are proportional to
(1-x)^4 and (1+x)^4, x=cos(theta), respectively. This toy axisymmetric
mask supplies a discriminating E->B coupling oracle, not measured Planck mixing.
"""
from __future__ import annotations
import numpy as np

def diagonal_spin2_response(epsilon=0.2,n=128):
    if not np.isfinite(epsilon) or abs(epsilon)>1:
        raise ValueError('require nonnegative synthetic mask W=1+eps cos(theta)')
    if n<6:raise ValueError('underresolved quadrature')
    x,w=np.polynomial.legendre.leggauss(n)
    mask=1+epsilon*x
    a_plus=(1-x)**4; a_minus=(1+x)**4
    kp=(w*mask*a_plus).sum()/(w*a_plus).sum()
    km=(w*mask*a_minus).sum()/(w*a_minus).sum()
    # E/B diagonal mixing proportional to i/2(K_plus-K_minus)
    leak=0.5*abs(kp-km)
    return {'schema':'htt.ell2_m2_spin2_mask_oracle/1','mask':'1+epsilon*cos(theta)',
            'epsilon':float(epsilon),'n_gauss':n,'spin_plus_response':float(kp),
            'spin_minus_response':float(km),'abs_E_to_B_amplitude':float(leak),
            'theory_abs_E_to_B':float(2*abs(epsilon)/3),
            'reproduction':'NUMERIC_L2_AXISYMMETRIC_MASK_NOT_ACTUAL_PLANCK_MASK_E2E'}
