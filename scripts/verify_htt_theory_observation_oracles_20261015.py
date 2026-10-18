#!/usr/bin/env python3
"""Finite scientific verifiers for the HTT theory->observations run.

No full Planck physical transfer certification; verifies algebra/discretized
pixel projection against independent HEALPix harmonics and exact thermal pullback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

from obsstat.r7_cmb_product_response import pixel_fit_geometry,real_design
from obsstat.processed_boost_theory_bridge import (real_harmonics_with_gradients,
    first_order_sky_generator, processed_boost_jacobian)
from obsstat.lorentz_sky_pullback import pullback_thermodynamic_temperature_field
from run_smica_reboot_pilot import build_ols_projector

ROOT=Path(__file__).resolve().parents[1]


def verify():
    import healpy as hp
    ns=8
    n=np.column_stack(hp.pix2vec(ns,np.arange(hp.nside2npix(ns))))
    L=6
    y,dt,dp=real_harmonics_with_gradients(n,lmax=L)
    rng=np.random.default_rng(20261015)
    a=rng.normal(size=(L+1)**2)
    alm=np.zeros(hp.Alm.getsize(L),complex)
    j=0
    for ell in range(L+1):
        alm[hp.Alm.getidx(L,ell,0)]=a[j];j+=1
        for m in range(1,ell+1):
            alm[hp.Alm.getidx(L,ell,m)]=(a[j]-1j*a[j+1])/np.sqrt(2);j+=2
    sy,sdtheta,sdphi=hp.alm2map_der1(alm,ns,lmax=L)
    healpy_residual={
        'map':float(np.max(abs(sy-y@a))),
        'dtheta':float(np.max(abs(sdtheta-dt@a))),
        'dphi_over_sin':float(np.max(abs(sdphi-dp@a))),
    }
    if max(healpy_residual.values())>2e-11:
        raise ValueError('HEALPix/Scipy source derivative independent oracle failed')

    path=ROOT/'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz'
    with np.load(path,allow_pickle=False) as z:
        observed=z['observed_map'];mask=z['common_mask']
    directions,yd=pixel_fit_geometry()
    selected,operator,_=build_ols_projector(yd,(mask>.5).astype(float))
    coeff=operator@observed[selected]
    basis=real_harmonics_with_gradients(directions,lmax=5)
    G=first_order_sky_generator(directions,basis,coeff)
    J=processed_boost_jacobian(G,selected,operator)
    beta=np.array(json.loads((ROOT/'docs/observational_reboot_20261014/results/physical_dipole_v2/result.json').read_text())['beta_xyz'])
    axis=beta/np.linalg.norm(beta)
    positive_offset=1500.  # mathematical oracle only: not claimed to be actual T0.
    src=lambda dirs: positive_offset+real_design(dirs,ell_max=5)@coeff
    truth=J@axis
    errors=[]
    for h in (4e-4,2e-4,1e-4):
        plus=pullback_thermodynamic_temperature_field(directions,h*axis,src)
        minus=pullback_thermodynamic_temperature_field(directions,-h*axis,src)
        finite=(operator[4:36]@((plus[selected]-minus[selected])/(2*h)))
        errors.append({'finite_difference_beta_step':h,
                       'max_abs_residual_microk_per_unit_beta':float(np.max(abs(finite-truth))),
                       'relative_frobenius_residual':float(np.linalg.norm(finite-truth)/np.linalg.norm(truth))})
    if errors[-1]['relative_frobenius_residual']>3e-7:
        raise ValueError('observed-source exact Lorentz pullback derivative mismatch')
    if not (errors[0]['relative_frobenius_residual']>errors[1]['relative_frobenius_residual']>
            errors[2]['relative_frobenius_residual']):
        raise ValueError('second-order central finite difference convergence absent')

    cmb=json.loads((ROOT/'docs/research_program/theory_obs_application_20261015/results/cmb_processed_boost_v2/result.json').read_text())
    for item in cmb['records']:
        values=[f['fisher_trace'] for f in item['fisher_stress']]
        if any(after>before+1e-8 for before,after in zip(values,values[1:])):
            raise ValueError('Fisher nuisance monotonicity failed')
    return {
      'schema':'htt.theory-obs-oracles/1',
      'source_scope':'actual delivered observed SMICA and independent synthetic-harmonic oracle',
      'independent_harmonic_engine':'HEALPix alm2map_der1 versus SciPy sph_harm_y analytic derivatives',
      'healpy_residual_absolute_microk_when_unit_gaussian_coefficient':healpy_residual,
      'processed_actual_observed_map_source':str(path.relative_to(ROOT)),
      'processed_beta_axis':axis.tolist(),
      'analytic_response_unit_beta_norm_microk':float(np.linalg.norm(truth)),
      'central_exact_pullback_comparison':errors,
      'source_absolute_temperature_offset_microk':'1500, mathematical positive embedding; not physical T0',
      'fisher_stress_monotonicity_6cases':'PASS',
      'scientific_claim_scope':'local finite-pixel analytic/numeric equivalence; upstream transfer and true sky remain unverified',
    }


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    opts=parser.parse_args()
    if opts.output.exists():
        raise ValueError('fresh oracle evidence required')
    out=verify()
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out,ensure_ascii=False,indent=2))
