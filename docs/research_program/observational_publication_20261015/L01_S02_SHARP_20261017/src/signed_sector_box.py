"""Exact signed kinematic Gauss/MES box envelopes: algebra only, NOT a posterior.

Conventions (-+++): x_C=(sigma_ab sigma^ab-omega_ab omega^ab)/(6 H^2)
                        + Omega_tilt + DeltaOmega_k,
H=Theta/3>0; U_sigma=(3/2) B_sigma^2>0; Q=x_C/U_sigma may be signed.
All interval inputs are declared assumptions, NOT recovered from CF4.
"""
import json
from pathlib import Path
import numpy as np


def _interval(v,lower=None,name='interval'):
    a=np.asarray(v,dtype=float)
    if a.shape!=(2,) or not np.isfinite(a).all() or a[1]<a[0] or (lower is not None and a[0]<lower):
        raise ValueError('invalid '+name)
    return float(a[0]),float(a[1])


def bounds(H, sigma_sq, omega_sq, Omega_tilt, DeltaOmega_k, B_sigma):
    """Sharp attainable extrema if all six interval factors vary independently.

    H, sigma and omega share inverse-time units. Here sigma_sq/omega_sq units
    (km/s/Mpc)^2; H in km/s/Mpc; B_sigma is a positive dimensionless MES
    *bound*, not shear itself. Selection/calibration/geometry not inferred.
    """
    h=_interval(H,0,'H');sig=_interval(sigma_sq,0,'sigma_sq');om=_interval(omega_sq,0,'omega_sq')
    tilt=_interval(Omega_tilt,name='tilt');curv=_interval(DeltaOmega_k,name='curvature')
    B=_interval(B_sigma,0,'B_sigma')
    if h[0]<=0 or B[0]<=0:raise ValueError('positive H and B_sigma floor required')
    n=(sig[0]-om[1],sig[1]-om[0])
    terms=[q/(6*k*k) for q in n for k in h]
    x=(min(terms)+tilt[0]+curv[0], max(terms)+tilt[1]+curv[1])
    U=(1.5*B[0]**2,1.5*B[1]**2)
    ratios=[q/u for q in x for u in U]
    return {'x_C':list(x),'U_sigma':list(U),'Q':list((min(ratios),max(ratios))),
            'math_scope':'EXACT_FOR_INDEPENDENT_RECTANGULAR_SECTOR_DOMAIN',
            'source_admission':'NO_CF4_PHYSICAL_SECTOR_INPUT_PROVIDED'}


def run():
    # Numerical illustration only: artificial physical sector intervals.
    return {'schema':'htt.S02_signed_mes_sector_box_math/1',
            'manufactured_example':bounds([68,72],[0,16],[0,25],[0,.001],[-.002,.003],[.03,.05]),
            'physical_posterior':'NOT_CONSTRUCTED',
            'actual_CF4_physical_sector':'UNMEASURED',
            'physical_exceedance_unknown_mass':1.0}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',default='results/S02_SIGNED_MES_INTERVAL_THEOREM.json');a=p.parse_args()
 target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(json.dumps(run(),sort_keys=True,indent=2)+'\n');print(target)
