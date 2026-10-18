"""Run the actual-source, finite-sector V02 processing counterfactual once."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import healpy as hp
import numpy as np
import scipy
from astropy.io import fits

from v02_response import (beam_layout, defined_source, design, finite_modes,
                          fit_operator, nuisance_projected_response, sphere_rule)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
RAW = Path('/mnt/extdrive/workdir/raw')
GIT_SOURCE = 'c2889730d2b5e5b778951f15e8f09afd55bed4e3'
SOURCE = REPO/'docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz'
CACHE = REPO/'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz'
MAP = RAW/'planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits'
MASKS = [RAW/'planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits',
         RAW/'planck_pr3_smica_hm_20261015/COM_Mask_CMB-HM-Misspix-Mask-Int_2048_R3.00.fits',
         RAW/'planck_pr3_targeted_inputs_20261015/COM_Mask_CMB-OE-Misspix-Mask-Int_2048_R3.00.fits']
EXPECTED = ['23f49a3479073408b83a7f1bb2cca490d9be7f934b2e0e891524b6a1d06a5fc4',
            'f4fd909734d80fb80214018b3ef9b44a378a4d04418337786c48f6d388dfb2a0',
            'ecb39152ad5b93ea309baf396aad404a062edd6745a30c0b941b3556ca28aff9']


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8<<20), b''): h.update(block)
    return h.hexdigest()


def identity(path, expected=None):
    h = digest(path)
    if expected is not None and h != expected: raise ValueError(f'IMMUTABLE_SOURCE_CHANGED:{path}:{h}')
    return {'path': str(path), 'sha256': h, 'bytes': Path(path).stat().st_size}


def main():
    started = time.monotonic()
    out = HERE/'results'
    if out.exists(): raise FileExistsError('CREATE_ONLY_RESULTS_ALREADY_EXIST')
    sources = [identity(SOURCE, '900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459'),
               identity(CACHE, '86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb'),
               identity(MAP, '60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac')]
    fine = None
    for path, expected in zip(MASKS, EXPECTED):
        sources.append(identity(path, expected))
        with fits.open(path, memmap=True) as f:
            if f[1].header['NSIDE'] != 2048 or f[1].header['ORDERING'] != 'NESTED':
                raise ValueError('NATIVE_MASK_GEOMETRY')
            valid = np.asarray(f[1].data['TMASK']) > .5
            fine = valid if fine is None else fine & valid
    coverage = hp.reorder(fine.reshape(49152, 1024).sum(axis=1)/1024., n2r=True)
    del fine
    with np.load(CACHE, allow_pickle=False) as z: confidence = np.asarray(z['common_mask'], float)
    selected = (confidence > .5) & (coverage >= .995)
    if selected.sum() != 26846: raise ValueError('ACTUAL_T_SUPPORT_MISMATCH')
    with np.load(SOURCE, allow_pickle=False) as z:
        retained = np.asarray(z['coeff_T'][z['names_T'].tolist().index('SMICA_FULL')], float)[:, None]
    with fits.open(MAP, memmap=True) as f:
        if f[2].header['LMIN'] != 0 or f[2].header['LMAX_I'] != 4096:
            raise ValueError('ACTUAL_INT_BEAM_INDEX')
        beam = np.asarray(f[2].data['INT_BEAM'], float)
    source = defined_source(retained, beam)
    ring = np.column_stack(hp.pix2vec(64, np.arange(49152)))
    yr = design(ring[selected], 16)
    # Construct the operator on selected rows, preserving precisely the original mask.
    op = fit_operator(yr[:, :36], np.ones(selected.sum(), dtype=bool))
    transfer = op[4:]@yr
    prior_path = 'docs/research_program/theory_obs_application_20261015/loop9_smica_finite_response/results/response_v1/baseline_response_matrices.npz'
    prior_bytes = subprocess.check_output(['git', 'show', GIT_SOURCE+':'+prior_path], cwd=REPO)
    if hashlib.sha256(prior_bytes).hexdigest() != 'a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007':
        raise ValueError('PRIOR_FINITE_RESPONSE_CHANGED')
    with np.load(io.BytesIO(prior_bytes), allow_pickle=False) as z:
        prior_error = float(np.max(np.abs(transfer[:, 36:]-z['K_ell2to5_32x253'])))
    if prior_error > 1e-10: raise ValueError('ORIGINAL_T_MODE_LEAKAGE_NOT_REPRODUCED')
    print(json.dumps({'phase':'SOURCE_MASK_BEAM_BOUND', 'pixels':int(selected.sum()), 'prior_K_max_delta':prior_error}), flush=True)
    n, w = sphere_rule(32); yq = design(n, 16)
    n2, w2 = sphere_rule(48); yq2 = design(n2, 16)
    bl = beam_layout(beam, 16)
    def modes(beta, refined=False, delivered=False):
        a = source*beam_layout(beam, 5)[:, None] if delivered else source
        return finite_modes(a, beta, n2 if refined else n, w2 if refined else w, yq2 if refined else yq)
    def processed(beta, refined=False): return (transfer@(bl[:, None]*modes(beta, refined)))[:, 0]
    zero = processed(np.zeros(3))
    zero_error = float(np.max(np.abs(zero-retained[:, 0])))
    if zero_error > 1e-9: raise ValueError('SOURCE_SURROGATE_ZERO_BOOST_REPLAY')
    h, h2 = 1e-5, 5e-6
    mode_jac = np.column_stack([((modes(h*np.eye(3)[i])-modes(-h*np.eye(3)[i]))/(2*h))[:, 0] for i in range(3)])
    mode_jac2 = np.column_stack([((modes(h2*np.eye(3)[i])-modes(-h2*np.eye(3)[i]))/(2*h2))[:, 0] for i in range(3)])
    jac = transfer@(bl[:, None]*mode_jac2)
    pixels = yr@(bl[:, None]*mode_jac2)
    fwl, residual_pixel = nuisance_projected_response(yr[:, :36], np.ones(selected.sum(), bool), pixels)
    fwl_error = float(np.max(np.abs(fwl-jac)))
    derivative_delta = float(np.linalg.norm(transfer@(bl[:, None]*(mode_jac-mode_jac2)), 2))
    if fwl_error > 1e-8 or derivative_delta > 1e-4: raise ValueError('DERIVATIVE_OR_NUISANCE_QUOTIENT_UNSTABLE')
    sv = np.linalg.svd(jac, compute_uv=False)
    rows, saved = [], {}
    direction = np.array([1., 2., 3.])/np.sqrt(14.)
    experiments = [('generic', b*direction) for b in (.0003, .00123, .003, .01)]
    experiments += [(axis, .00123*np.eye(3)[i]) for i, axis in enumerate(('x', 'y', 'z'))]
    for label, beta in experiments:
        m = modes(beta); bm = bl[:, None]*m
        full = (transfer@bm)[:, 0]
        difference = full-zero
        remainder = difference-jac@beta
        refined = processed(beta, True)
        cut12 = (transfer[:, :169]@bm[:169])[:, 0]
        leaked = (transfer[:, 36:]@bm[36:])[:, 0]
        wrong = (transfer@modes(beta, delivered=True))[:, 0]
        key = label+'_'+str(float(np.linalg.norm(beta)))
        saved[key] = np.stack((difference, remainder, leaked, wrong-full, refined-full, cut12-full))
        rows.append({'label': label, 'beta': beta.tolist(), 'speed': float(np.linalg.norm(beta)),
            'injection_norm_microK': float(np.linalg.norm(difference)),
            'finite_minus_linear_norm_microK': float(np.linalg.norm(remainder)),
            'remainder_over_beta_squared_microK': float(np.linalg.norm(remainder)/(beta@beta)),
            'finite_mode_leakage_ell6_16_to_fit2_5_microK': float(np.linalg.norm(leaked)),
            'wrong_boost_after_beam_delta_microK': float(np.linalg.norm(wrong-full)),
            'quadrature_32_vs48_delta_microK': float(np.linalg.norm(refined-full)),
            'cutoff12_vs16_delta_microK': float(np.linalg.norm(cut12-full)),
            'beam_output_mode_norm_above12_microK': float(np.linalg.norm(bm[169:]))})
    # Full-sky projection differs from the finite actual-mask fit via leaked high modes.
    nuisance_leak = float(np.max(np.abs(op[4:]@yr[:, :4])))
    result = {'schema':'htt.V02_delivered_fit_finite_boost_counterfactual/1',
        'owner':'obsstat', 'scope':'SMICA_FULL delivered-fit ell2..5 source surrogate on original T26846 support',
        'status':'DIAGNOSTIC_ONLY', 'claim_tier':'C0', 'non_claim_bearing':True,
        'transfer_source':'empirical_proxy', 'sky_support_status':'ORIGINAL_T26846_RECONSTRUCTED',
        'null_mock_status':'NOT_QUALIFIED', 'physical_observer_response':None,
        'physical_sampling_covariance':None, 'physical_response_uncertainty':None,
        'p_value':None, 'inferred_velocity':None, 'independent_sky_count':1,
        'source_definition':'s_lm=a_delivered_fit_lm/b_l for ell2..5 only; a defined signed finite perturbation, not intrinsic source reconstruction',
        'processing_order':['defined finite source s','exact weight-one scalar U_beta','actual SMICA INT_BEAM once','RING64 pixel synthesis','actual T26846 selection','simultaneous unweighted ell0..5 fit','retain ell2..5'],
        'physical_monopole_dipole_high_modes_assumed_zero':False,
        'physical_pipeline_reproduced':False, 'native_child_coarsening_reproduced':False,
        'beam':{'column':'INT_BEAM', 'hdu_zero_based':2, 'values_ell0_16':beam[:17].tolist(),
                'source_sector_inverse_condition':float(np.max(beam[2:6])/np.min(beam[2:6])),
                'double_beam_applied':False, 'component_separation_inverted':False},
        'mask':{'nside':64,'order':'RING','pixels':int(selected.sum()),
                'rule':'K1_confidence>0.5 AND native_AND(TMASK_common,TMASK_HM,TMASK_OE)_parent_fraction>=0.995',
                'sha256':hashlib.sha256(selected.astype(np.uint8).tobytes()).hexdigest()},
        'harmonic_convention':'orthonormal real Condon-Shortley ell,m0,sqrt2 ReY,sqrt2 ImY; coefficient sine=-sqrt2 Im(alm)',
        'units':'microK_CMB; beta=v/c; response microK_CMB per beta',
        'conventions':{'metric':'(-,+,+,+)','directions':'sourceward/outward','frame':'defined local observer chart','Doppler_weight':1},
        'controls':{'original_mode_leakage_max_abs_delta':prior_error, 'zero_beta_fit_replay_max_microK':zero_error,
            'nuisance_FWL_vs_joint_fit_max_microK_per_beta':fwl_error,
            'monopole_dipole_to_retained_operator_max':nuisance_leak,
            'derivative_h1e5_vs_h5e6_operator_delta_microK_per_beta':derivative_delta,
            'finite_quadrature_rule':[32,64], 'refined_rule':[48,96],
            'output_lmax':16, 'cutoff_comparison_lmax':12},
        'geometric_response':{'shape':[32,3], 'singular_values_microK_per_beta':sv.tolist(),
            'rank_numerical':int(np.linalg.matrix_rank(jac)), 'physical_identifiable_rank':'UNKNOWN',
            'covariance_whitened':False, 'nuisance_scope':'pixel monopole/dipole only; no foreground/calibration nuisance image supplied'},
        'experiments':rows,
        'upstream_physical_mapping_missing':['frequency/bandpass dependent observer injection tied to released component-separation/calibration weights and frame conventions',
             'intrinsic or admitted physical all-sector source including monopole/dipole and high modes',
             'source-matched signal+noise+foreground/systematics simulation law and nuisance/covariance response'],
        'runnable_processing_extension':'Native-child masked averaging of the defined surrogate is unexecuted here, not an unavailable external input; existing L01 finite response can support this separately.',
        'unbounded_sectors':['physical source modes outside defined ell2..5 surrogate','spin polarization response','physical upstream component-separation remainder'],
        'numerical_limit':'32-vs48 quadrature and l12-vs16 differences are empirical diagnostics, not certified infinite-tail/error bounds.',
        'node_acceptance':'V02_ORIGINAL_PHYSICAL_ACCEPTANCE_HOLD; FINITE_COUNTERFACTUAL_PREPARATION_EXECUTED_PENDING_REVIEW',
        'paper_gate':'NOT_READY_TO_SUBMIT', 'source_identities':sources,
        'prior_response':{'commit':GIT_SOURCE,'path':prior_path,'sha256':hashlib.sha256(prior_bytes).hexdigest()},
        'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__, 'healpy':hp.__version__,
                   'requested_model':'gpt-6.1-sol','requested_effort':'high','observed_model':'UNKNOWN','observed_effort':'UNKNOWN',
                   'threads':{k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}},
        'base_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        'generating_code':{p.name:digest(p) for p in (HERE/'v02_response.py', Path(__file__))},
        'seconds':time.monotonic()-started}
    out.mkdir()
    with (out/'V02_FINITE_RESPONSE.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    with (out/'V02_FINITE_RESPONSE.npz').open('xb') as stream:
        np.savez_compressed(stream, retained_source_fit_microK=retained, defined_source_microK=source,
            selected_mask_ring64=selected, jacobian_microK_per_beta=jac, nuisance_projected_pixel_jacobian=residual_pixel,
            actual_INT_BEAM=beam[:17], transfer_low32_full289=transfer,
            experiment_keys=np.array(list(saved)), experiment_vectors_microK=np.stack(list(saved.values())))
    print(json.dumps({'seconds':result['seconds'], 'controls':result['controls'], 'geometric_response':result['geometric_response'], 'experiments':rows},indent=2))


if __name__ == '__main__': main()
