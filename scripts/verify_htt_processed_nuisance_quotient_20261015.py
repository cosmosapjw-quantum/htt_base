#!/usr/bin/env python3
"""Finite-pixel high-multipole nuisance image witness for existing Planck OLS.

Only the fixed NSIDE64 cache-stage masked OLS and free harmonic ell6..12
coefficient model; not an upstream Planck-beam/compsep/source physics no-go.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
from scipy.linalg import qr
from obsstat.r7_cmb_product_response import pixel_fit_geometry
from obsstat.processed_boost_theory_bridge import (
    first_order_sky_generator, processed_boost_jacobian,
    real_harmonics_with_gradients)
from run_smica_reboot_pilot import build_ols_projector

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz'
DIPOLE=ROOT/'docs/observational_reboot_20261014/results/physical_dipole_v2/result.json'

def run():
    started=time.perf_counter()
    with np.load(CACHE,allow_pickle=False) as f:
        mask=np.asarray(f['common_mask'],float)
        observed=np.asarray(f['observed_map'],float)
    beta=np.array(json.loads(DIPOLE.read_text())['beta_xyz'],float)
    n,_=pixel_fit_geometry()
    y,dt,dp=real_harmonics_with_gradients(n,lmax=12)
    rows=[]
    for cut in (.5,.8):
        selected,p5,met=build_ols_projector(y[:,:36],(mask>cut).astype(float))
        k=p5[4:36]@y[selected,36:169]
        s=np.linalg.svd(k,compute_uv=False)
        _,r,pivot=qr(k,pivoting=True,mode='economic')
        diag=np.abs(np.diag(r))
        rank=int(np.linalg.matrix_rank(k,tol=s[0]*1e-10))
        qr_rank=int(np.sum(diag>diag[0]*1e-10))
        if rank!=32 or qr_rank!=32:
            raise RuntimeError('finite pixel high-mode image not full row rank at declared tolerance')
        sim=np.linalg.pinv(k,rcond=1e-13)
        check=float(np.linalg.norm(k@sim-np.eye(32),ord=2))
        if check>1e-8:
            raise RuntimeError('high-mode full-row-rank inverse residual too large')
        for L in (5,8,12):
            q=(L+1)**2
            _,sp,_=build_ols_projector(y[:,:q],(mask>cut).astype(float))
            coeff=sp@observed[selected]
            generator=first_order_sky_generator(n,(y[:,:q],dt[:,:q],dp[:,:q]),coeff)
            j=processed_boost_jacobian(generator,selected,p5)
            shift=j@beta
            witness=-sim@shift
            resid=shift+k@witness
            projector=j-k@(sim@j)
            rows.append({
                'mask_threshold':cut,'source_cutoff_L':L,
                'target_output_dimension':32,'high_mode_ell_range':[6,12],
                'high_mode_input_dimension':133,
                'svd_image_rank_1e_minus_10':rank,
                'pivoted_qr_rank_1e_minus_10':qr_rank,
                'smallest_singular':float(s[-1]),
                'largest_singular':float(s[0]),
                'smallest_over_largest':float(s[-1]/s[0]),
                'condition_number':float(s[0]/s[-1]),
                'projector_identity_operator_residual':check,
                'boost_direction_tangent_rank':int(np.linalg.matrix_rank(j,tol=np.linalg.norm(j,2)*1e-10)),
                'observed_source_increment_shift_norm_microK':float(np.linalg.norm(shift)),
                'minimal_high_mode_compensator_norm_microK':float(np.linalg.norm(witness)),
                'minimal_compensator_max_abs_coefficient_microK':float(np.max(np.abs(witness))),
                'compensated_residual_norm_microK':float(np.linalg.norm(resid)),
                'all_three_boost_columns_quotient_norm_microK_per_beta':float(np.linalg.norm(projector)),
                'quotient_to_original_J_norm':float(np.linalg.norm(projector)/np.linalg.norm(j))
            })
    return {'schema':'htt.discrete-high-mode-nuisance-image-witness/1',
            'scope':'FIXED_SMICA_CACHE_STAGE_MASKED_NSIDE64_OLS_LINEAR_MAP_ONLY',
            'user_raw_observation_modified':False,
            'not':'not physical full transfer no-go, no matter/Einstein solution, no physical high-mode bound or observational detection',
            'counterfactual_high_mode_law':'all ell6..12 independent signed real harmonic coefficients free, with no amplitude/physical prior or correlated covariance restriction',
            'physical_extra_inputs_required':'actual accepted physical high-mode distribution, Planck beam and frequency/compsep processing, E2E null',
            'source_branch':'obs/solver-free-dossier-20261014',
            'elapsed_seconds':time.perf_counter()-started,'records':rows}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    p=parser.parse_args()
    if p.output.exists():raise ValueError('fresh output required')
    res=run()
    p.output.parent.mkdir(exist_ok=True,parents=True)
    p.output.write_text(json.dumps(res,indent=2)+'\n')
    print(json.dumps({'scope':res['scope'],'runs':len(res['records']),
       'summary':[{k:rec[k] for k in ('mask_threshold','source_cutoff_L',
                 'smallest_singular','smallest_over_largest','minimal_high_mode_compensator_norm_microK',
                 'compensated_residual_norm_microK','quotient_to_original_J_norm')}
                for rec in res['records']]},indent=2))
