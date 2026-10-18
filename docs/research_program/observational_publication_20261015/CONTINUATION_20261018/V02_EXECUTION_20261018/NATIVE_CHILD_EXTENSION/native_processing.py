"""Source-defined finite V02 extension: native child means then centre OLS.

No physical covariance, source refit, Planck upstream inversion or solver.
"""
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
from astropy.io import fits

HERE = Path(__file__).resolve().parent
CENTRE = HERE.parent
sys.path.insert(0, str(CENTRE))
from v02_response import (beam_layout, design, finite_modes, fit_operator,
                          nuisance_projected_response, sphere_rule)
import run_v02 as prior


def real_to_alm(coeff):
    c = np.asarray(coeff, float)
    lmax = int(np.sqrt(c.size))-1
    if c.shape != ((lmax+1)**2,) or not np.isfinite(c).all():
        raise ValueError('FINITE_SQUARE_REAL_COEFFICIENTS')
    a = np.zeros(hp.Alm.getsize(lmax), complex)
    for ell in range(lmax+1):
        a[hp.Alm.getidx(lmax, ell, 0)] = c[ell*ell]
        for m in range(1, ell+1):
            k = ell*ell+2*m-1
            a[hp.Alm.getidx(lmax, ell, m)] = (c[k]-1j*c[k+1])/np.sqrt(2.)
    return a


def ring_reduce(field, valid_nest, selected_ring, nside_in=2048, nside_out=64,
                chunk=262144):
    """Fixed original-source-valid native child means, streamed in RING order.

    Unlike L03's simulated-source reducer, validity is exactly the original
    observed I finite/>-1e20 validity intersected with original AND TMASK.
    Values are synthesized finite perturbations; never change their fixed mask.
    """
    nin, nout = hp.nside2npix(nside_in), hp.nside2npix(nside_out)
    if (nside_in < nside_out or nside_in % nside_out or
            np.shape(field) != (nin,) or np.shape(valid_nest) != (nin,) or
            np.asarray(valid_nest).dtype != bool or
            np.shape(selected_ring) != (nout,) or np.asarray(selected_ring).dtype != bool):
        raise ValueError('FIXED_NATIVE_GEOMETRY')
    child = (nside_in//nside_out)**2
    sel = hp.reorder(selected_ring, r2n=True)
    sums, count = np.zeros(nout), np.zeros(nout, np.int64)
    for start in range(0, nin, chunk):
        stop = min(nin, start+chunk)
        nn = hp.ring2nest(nside_in, np.arange(start, stop))
        pp = nn//child
        use = valid_nest[nn] & sel[pp]
        v = np.asarray(field[start:stop])
        if not np.isfinite(v[use]).all():
            raise ValueError('NONFINITE_SYNTHESIZED_FIELD')
        sums += np.bincount(pp[use], weights=v[use], minlength=nout)
        count += np.bincount(pp[use], minlength=nout)
    if np.any(count[sel] == 0):
        raise ValueError('EMPTY_SELECTED_PARENT')
    coarse = np.zeros(nout)
    coarse[sel] = sums[sel]/count[sel]
    return hp.reorder(coarse, n2r=True), hp.reorder(count, n2r=True)


def explicit_parent_means(field, valid, parents, nside_in=2048, nside_out=64):
    child = (nside_in//nside_out)**2
    nn = np.asarray(parents)[:, None]*child+np.arange(child)
    vv = field[hp.nest2ring(nside_in, nn)]
    mask = valid[nn]
    return np.sum(np.where(mask, vv, 0.), axis=1)/mask.sum(axis=1)


def main():
    start = time.monotonic()
    out = HERE/'results'
    if out.exists():
        raise FileExistsError('CREATE_ONLY_NATIVE_RESULTS_EXIST')
    out.mkdir()
    # This snapshot is consumed by independent review to prove old evidence intact.
    preserved = {str(p.relative_to(CENTRE)): prior.digest(p) for p in CENTRE.rglob('*')
                 if p.is_file() and HERE not in p.parents and '__pycache__' not in p.parts}
    with (HERE/'PRESERVED_CENTRE_IDENTITIES.json').open('x') as f:
        json.dump(preserved, f, indent=2)
    old = json.loads((CENTRE/'results/V02_FINITE_RESPONSE.json').read_text())
    identities = [prior.identity(prior.SOURCE, '900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459'),
                  prior.identity(prior.CACHE, old['source_identities'][1]['sha256']),
                  prior.identity(prior.MAP, old['source_identities'][2]['sha256'])]
    with np.load(CENTRE/'results/V02_FINITE_RESPONSE.npz', allow_pickle=False) as z:
        source = z['defined_source_microK'].copy()
        a_fit = z['retained_source_fit_microK'][:, 0].copy()
        old_selected = z['selected_mask_ring64'].copy()
        beam = z['actual_INT_BEAM'].copy()
        centre_transfer = z['transfer_low32_full289'].copy()
        old_j = z['jacobian_microK_per_beta'].copy()
    fine = None
    for path, expected in zip(prior.MASKS, prior.EXPECTED):
        identities.append(prior.identity(path, expected))
        with fits.open(path, memmap=True) as f:
            if f[1].header['NSIDE'] != 2048 or f[1].header['ORDERING'] != 'NESTED':
                raise ValueError('ORIGINAL_NATIVE_MASK_GEOMETRY')
            m = (np.asarray(f[1].data['TMASK']).reshape(-1) > .5)
            fine = m if fine is None else fine & m
    child = 1024
    tm_count = fine.reshape(49152, child).sum(axis=1)
    with np.load(prior.CACHE, allow_pickle=False) as z:
        selected = (z['common_mask'] > .5) & (hp.reorder(tm_count/child, n2r=True) >= .995)
    mask_sha = hashlib.sha256(selected.astype(np.uint8).tobytes()).hexdigest()
    if (selected.sum() != 26846 or not np.array_equal(selected, old_selected) or
            mask_sha != '98c90cbd186aceed02f6692ef83685b44d0f7f22569f218ea2936dcfafcedfbf'):
        raise ValueError('SAVED_T26846_SUPPORT_CHANGED')
    # One inspection of actual native I validity; no values fitted or retained.
    invalid_in_tmask = 0
    with fits.open(prior.MAP, memmap=True) as f:
        h = f[1]
        if h.header['NSIDE'] != 2048 or h.header['ORDERING'] != 'NESTED' or h.header['TUNIT1'] != 'K_CMB':
            raise ValueError('SOURCE_I_NATIVE_GEOMETRY')
        values = h.data['I_STOKES']
        for lo in range(0, len(fine), 1<<20):
            hi = min(len(fine), lo+(1<<20))
            v = np.asarray(values[lo:hi], float)
            valid = np.isfinite(v) & (v > -1e20)
            invalid_in_tmask += int(np.sum(fine[lo:hi] & ~valid))
            fine[lo:hi] &= valid
        if not np.array_equal(np.asarray(f[2].data['INT_BEAM'], float)[:17], beam):
            raise ValueError('ORIGINAL_INT_BEAM_CHANGED')
    counts_nest = fine.reshape(49152, child).sum(axis=1)
    selected_nest = hp.reorder(selected, r2n=True)
    min_coverage = float(np.min(counts_nest[selected_nest]/child))
    if min_coverage < .995:
        raise ValueError('ORIGINAL_SELECTED_VALUE_COVERAGE_BELOW_FLOOR')
    np.savez_compressed(out/'FIXED_NATIVE_VALIDITY.npz', valid_packed=np.packbits(fine),
                        native_pixel_count=np.array(len(fine)), counts_nest=counts_nest,
                        selected_ring64=selected)
    print(json.dumps({'phase':'FIXED_NATIVE_VALIDITY_BOUND','minimum_selected_coverage':min_coverage,
                      'TMASK_valid_but_I_invalid':invalid_in_tmask}), flush=True)
    ring = np.column_stack(hp.pix2vec(64, np.flatnonzero(selected)))
    low = design(ring, 5)
    op = fit_operator(low, np.ones(len(ring), bool))[4:]
    opnorm = float(np.linalg.norm(op, 2))
    envelope_factor = opnorm*np.sqrt(len(ring))*17/np.sqrt(4*np.pi)
    hist_paths = ['scripts/run_htt_planck_multisplit_spin_20261015.py',
                  'htt/obsstat/planck_split_joint_law.py', 'htt/obsstat/processed_boost_theory_bridge.py']
    hist = {p:subprocess.check_output(['git','show',prior.GIT_SOURCE+':'+p],cwd=prior.REPO) for p in hist_paths}
    ns = {'__name__':'historical_V02_analytic_generator'}
    exec(compile(hist[hist_paths[-1]], hist_paths[-1], 'exec'), ns)
    n,w = sphere_rule(32)
    y = design(n, 16)
    n48,w48 = sphere_rule(48)
    y48 = design(n48, 16)
    generator = ns['first_order_sky_generator'](n, ns['real_harmonics_with_gradients'](n,lmax=5), source[:,0])
    generator_modes = y.T@(w[:,None]*generator)
    if np.linalg.norm(generator_modes[49:]) > 1e-8:
        raise ValueError('ANALYTIC_GENERATOR_NOT_ELL6_FINITE')
    generator_modes[49:] = 0. # exact analytic ell<=6 sector, observed roundoff recorded below
    bl = beam_layout(beam,16)
    source16 = np.pad(source[:,0], (0,289-36))
    zero_coeff = bl*(finite_modes(source,np.zeros(3),n,w,y)[:,0]-source16)
    zero_bound = float(envelope_factor*np.linalg.norm(zero_coeff))
    if zero_bound > 1e-9:
        raise ValueError('ZERO_INCREMENT_PROPAGATION_BOUND')
    direction = np.array([1.,2.,3.])/np.sqrt(14.)
    betas = np.array([.00123*direction,.000615*direction])
    finite = np.column_stack([finite_modes(source,b,n,w,y)[:,0]-source16 for b in betas])
    refined = np.column_stack([finite_modes(source,b,n48,w48,y48)[:,0]-source16 for b in betas])
    fields = bl[:,None]*np.column_stack([source16,generator_modes,finite])
    if fields.shape != (289,6):
        raise ValueError('EXACT_SIX_FIELDS_REQUIRED')
    # Deterministic native selected child samples include a partially masked parent.
    selected_parents = np.flatnonzero(selected_nest)
    partial = selected_parents[counts_nest[selected_parents] < 1024]
    if not len(partial):
        raise ValueError('PARTIALLY_MASKED_CONTROL_PARENT_UNAVAILABLE')
    parents = np.unique(np.r_[selected_parents[0], selected_parents[len(selected_parents)//2],
                               selected_parents[-1], partial[0]])
    samples = (parents[:,None]*1024 + np.array([0,1,17,127,513,777,1023])).ravel()
    sample_ring = hp.nest2ring(2048, samples)
    sample_y = design(np.column_stack(hp.pix2vec(2048,sample_ring)),16)
    coarse_fields, field_controls = [], []
    for i in range(6):
        t = time.monotonic()
        field = hp.alm2map(real_to_alm(fields[:,i]),2048,lmax=16,pol=False,pixwin=False,fwhm=0.)
        direct = sample_y@fields[:,i]
        synthesis_error = float(np.max(np.abs(field[sample_ring]-direct)))
        coarse, counts = ring_reduce(field,fine,selected)
        if not np.array_equal(counts[selected],hp.reorder(counts_nest,n2r=True)[selected]):
            raise ValueError('SOURCE_VALIDITY_CHILD_COUNTS_CHANGED')
        explicit = explicit_parent_means(field,fine,parents)
        reducer_error = float(np.max(np.abs(hp.reorder(coarse,r2n=True)[parents]-explicit)))
        if synthesis_error > 1e-9 or reducer_error > 1e-9:
            raise ValueError('NATIVE_SYNTHESIS_OR_EXPLICIT_REDUCTION_CONTROL')
        coarse_fields.append(coarse[selected])
        del field
        field_controls.append({'field':i,'hp_vs_direct_samples_max_microK':synthesis_error,
                               'stream_vs_explicit_child_sum_max_microK':reducer_error,
                               'seconds':time.monotonic()-t})
        print(json.dumps({'phase':'NATIVE_FIELD_COMPLETED',**field_controls[-1]}),flush=True)
    coarse_fields = np.column_stack(coarse_fields)
    projected = op@coarse_fields
    baseline_mismatch = projected[:,0]-a_fit
    jac = projected[:,1:4]
    increments = projected[:,4:6].T
    residual = increments-betas@jac.T
    fwl,_ = nuisance_projected_response(low,np.ones(len(low),bool),coarse_fields[:,1:4])
    fwl_error = float(np.max(np.abs(fwl-jac)))
    constant_error = float(np.max(np.abs(op@np.ones(len(low)))))
    if fwl_error > 1e-8 or constant_error > 1e-9:
        raise ValueError('NATIVE_FWL_OR_CONSTANT_NUISANCE_CONTROL')
    centre_projected = centre_transfer@fields
    centre_jac = centre_projected[:,1:4]
    comparison = increments-centre_projected[:,4:6].T
    comparison_remainders = residual-(centre_projected[:,4:6].T-betas@centre_jac.T)
    rows=[]
    for i,beta in enumerate(betas):
        dc=bl*(refined[:,i]-finite[:,i])
        cut=fields[:,i+4].copy();cut[:169]=0.
        rows.append({'beta':beta.tolist(),'speed':float(np.linalg.norm(beta)),
            'increment_norm_microK':float(np.linalg.norm(increments[i])),
            'finite_minus_linear_norm_microK':float(np.linalg.norm(residual[i])),
            'finite_minus_linear_over_beta2_microK':float(np.linalg.norm(residual[i])/(beta@beta)),
            'native_minus_matched_centre_increment_norm_microK':float(np.linalg.norm(comparison[i])),
            'native_minus_matched_centre_remainder_norm_microK':float(np.linalg.norm(comparison_remainders[i])),
            'quadrature32_vs48_finite_comparison_envelope_microK':float(envelope_factor*np.linalg.norm(dc)),
            'ell12_vs16_finite_comparison_envelope_microK':float(envelope_factor*np.linalg.norm(cut))})
    result={'schema':'htt.V02_native_child_finite_source_processing/1','owner':'obsstat','claim_tier':'C0',
        'status':'EXECUTED_PENDING_FRESH_INDEPENDENT_REVIEW','non_claim_bearing':True,
        'scope':'Source-defined signed finite SMICA_FULL ell2..5 perturbation through original native-child mean and centre OLS',
        'transfer_source':'empirical_proxy','sky_support_status':'ORIGINAL_T26846_EXACT','null_mock_status':'NOT_QUALIFIED',
        'source_definition':'saved a_fit/b_INT on ell2..5; no refit; same finite source as centre candidate',
        'operator':'retain2..5 OLS0..5 on selected RING64 centres AFTER fixed-valid NESTED2048 child mean of 1024 children',
        'increment_definition':'d_native(beta)=A_native B_INT [P16 U_beta s-s]; apply a_fit+d_native(beta)',
        'harmonics':'real orthonormal Condon-Shortley m0,cos,sin; alm=(cos-i sin)/sqrt2; microK_CMB',
        'conventions':{'metric':'(-,+,+,+)','directions':'outward/sourceward','Doppler_weight':1,'beta':'v/c'},
        'processing_order':['defined s','exact scalar finite boost','P16','actual INT_BEAM once','native2048 synthesis',
                            'fixed-original-valid masked child mean','T26846 selection','centre ell0..5 OLS','retain2..5'],
        'source_identities':identities,'historical_producer':{'commit':prior.GIT_SOURCE,
            'files':{p:hashlib.sha256(c).hexdigest() for p,c in hist.items()}},
        'mask':{'sha256':mask_sha,'selected_count':int(selected.sum()),'selection':'cache confidence>.5 AND TMASK child coverage>=.995',
            'child_value_validity':'AND TMASK & finite(original I_STOKES) & original I_STOKES>-1e20',
            'native_validity_sha256':hashlib.sha256(fine.tobytes()).hexdigest(),
            'minimum_selected_actual_value_coverage':min_coverage,'TMASK_valid_but_I_invalid_count':invalid_in_tmask},
        'beam':{'values_ell0_16':beam.tolist(),'applied_once':True,'healpy_pixwin':False,'additional_gaussian':False},
        'controls':{'zero_increment_propagated_bound_microK':zero_bound,
            'nuisance_FWL_vs_joint_fit_max_microK_per_beta':fwl_error,
            'constant_pixel_to_retained_max_microK':constant_error,'native_field_controls':field_controls,
            'explicit_parent_nest64_ids':parents.tolist(),'sample_native_nest_ids':samples.tolist(),
            'analytic_centre_vs_saved_finite_difference_relative':float(np.linalg.norm(centre_jac-old_j,2)/np.linalg.norm(centre_jac,2))},
        'baseline_mismatch_norm_microK':float(np.linalg.norm(baseline_mismatch)),
        'baseline_mismatch_max_abs_microK':float(np.max(np.abs(baseline_mismatch))),
        'native_jacobian_singular_values_microK_per_beta':np.linalg.svd(jac,compute_uv=False).tolist(),
        'matched_centre_jacobian_singular_values_microK_per_beta':np.linalg.svd(centre_jac,compute_uv=False).tolist(),
        'native_minus_centre_jacobian_operator_norm_microK_per_beta':float(np.linalg.norm(jac-centre_jac,2)),
        'finite_comparison_envelope':{'formula':'||P_retained||2 sqrt(26846) (L+1)/sqrt(4pi) ||delta_c_after_beam||2',
            'L':16,'P_retained_operator_norm':opnorm,'factor':envelope_factor,
            'scope':'two declared finite coefficient comparisons only; not infinite Lorentz tail, physical covariance or physical uncertainty'},
        'experiments':rows,'native_projected_fields':6,'existing_seven_centre_experiments_rerun':False,
        'physical_upstream_response':'UNKNOWN','physical_covariance':'UNKNOWN','physical_identified_rank':'UNKNOWN',
        'caveats':['finite defined source only','unknown physical upstream response is outside finite operation',
                   'no local/global discrimination, posterior, p-value, velocity or Bianchi family admission'],
        'requested_model':'gpt-6.1-sol','requested_effort':'high','observed_model':'UNKNOWN','observed_effort':'UNKNOWN',
        'runtime':{'python':platform.python_version(),'numpy':np.__version__,'healpy':hp.__version__,
            'threads':{k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}},
        'base_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=prior.REPO,text=True).strip(),
        'seconds':time.monotonic()-start}
    np.savez_compressed(out/'NATIVE_RESPONSE.npz',a_fit_microK=a_fit,defined_source_microK=source,
        beam_applied_six_fields_coeff_microK=fields,selected_coarse_six_fields_microK=coarse_fields,
        jacobian_microK_per_beta=jac,matched_centre_jacobian_microK_per_beta=centre_jac,
        betas=betas,increments_microK=increments,applied_fit_microK=a_fit[None,:]+increments,
        finite_minus_linear_microK=residual,native_minus_centre_increment_microK=comparison,
        native_minus_centre_remainder_microK=comparison_remainders,baseline_mismatch_microK=baseline_mismatch,
        quadrature_refined_minus_base_after_beam_microK=bl[:,None]*(refined-finite),
        selected_mask_ring64=selected)
    after={name:prior.digest(CENTRE/name) for name in preserved}
    if after != preserved:
        raise ValueError('EXISTING_CENTRE_EVIDENCE_CHANGED')
    result['centre_evidence_preserved']=True
    with (out/'NATIVE_RESPONSE.json').open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'phase':'COMPLETED_PENDING_REVIEW','seconds':result['seconds'],
                      'controls':result['controls'],'experiments':rows}),flush=True)


if __name__=='__main__':
    main()
