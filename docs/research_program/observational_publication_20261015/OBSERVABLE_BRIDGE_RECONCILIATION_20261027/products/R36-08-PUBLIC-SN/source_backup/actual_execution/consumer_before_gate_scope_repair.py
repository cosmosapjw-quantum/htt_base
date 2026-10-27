#!/usr/bin/env python3
"""Reproduce the frozen R36-08 released-magnitude conditional comparator.

Only NumPy/SciPy quadrature and linear algebra are used.  No cosmological ODE,
native Bianchi solver, added error diagonal, or fitted H0 enters this consumer.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.linalg import solve_triangular
from scipy.stats import chi2


HERE = Path(__file__).resolve().parent
DATA = Path('/mnt/extdrive/workdir/htt_open_data/bridge20261027/pantheon')
SCRATCH = Path('/mnt/extdrive/workdir/htt_open_data/r36_public_sn_actual')
FILES = {
    'table': (DATA / 'Pantheon+SH0ES.dat', 579283,
              '1cb0fc379ef066afdc2ffd1857681cc478024570d8a3eba284fb645775198cf8',
              'cce857db0c15e9ce7a0e0ce77452b6ff62af969a'),
    'covariance': (DATA / 'Pantheon+SH0ES_STAT+SYS.cov', 33284960,
                   'abf806d966485e64afdb359c87bffc0ecc00d05eff0a31ced66f247385df0fdc',
                   'd1a1498154e7ba826df14bdbef35ebcb7f5efba1'),
}
NAMES = ('CID IDSURVEY RA DEC zHD zHDERR zCMB zCMBERR zHEL zHELERR '
         'm_b_corr IS_CALIBRATOR USED_IN_SH0ES_HF VPEC VPECERR').split()
E = np.zeros((5, 3, 3))
E[0] = np.diag([1., -1., 0.]) / math.sqrt(2)
E[1] = np.diag([1., 1., -2.]) / math.sqrt(6)
for k, (i, j) in enumerate(((0, 1), (0, 2), (1, 2)), 2):
    E[k, i, j] = E[k, j, i] = 1 / math.sqrt(2)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def identity(path, size, sha256, blob):
    raw = path.read_bytes()
    actual = {'path': str(path), 'bytes': len(raw),
              'sha256': hashlib.sha256(raw).hexdigest(),
              'git_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode()
                                             + b'\0' + raw).hexdigest()}
    check((actual['bytes'], actual['sha256'], actual['git_blob_sha1']) ==
          (size, sha256, blob), f'input identity mismatch: {path}')
    return actual


def reference(z_hd, z_hel, order):
    nodes, weights = np.polynomial.legendre.leggauss(order)
    t = z_hd[:, None] * (nodes[None, :] + 1) / 2
    integral = z_hd * np.sum(weights[None, :] /
        np.sqrt(.3153 * (1 + t)**3 + .6847), axis=1) / 2
    check(np.all(integral > 0) and np.all(1 + z_hel > 0), 'distance domain')
    return 5 * np.log10((1 + z_hel) * integral), integral


def design(ra, dec, high):
    r, d = np.deg2rad(ra), np.deg2rad(dec)
    n = np.stack((np.cos(d)*np.cos(r), np.cos(d)*np.sin(r), np.sin(d)), axis=1)
    check(np.max(np.abs(np.sum(n*n, axis=1)-1)) < 1e-14, 'unit sky directions')
    angular = np.column_stack((n, np.einsum('ni,kij,nj->nk', n, E, n)))
    nuisance = np.column_stack((np.ones(len(high)), high.astype(float)))
    signal = np.column_stack((angular*(~high)[:, None], angular*high[:, None]))
    return n, nuisance, signal


def fit(y, C, nuisance, signal, rank_tol=1e-10):
    L = np.linalg.cholesky(C)
    yw = solve_triangular(L, y, lower=True, check_finite=False)
    nw = solve_triangular(L, nuisance, lower=True, check_finite=False)
    sw = solve_triangular(L, signal, lower=True, check_finite=False)
    qn, rn = np.linalg.qr(nw, mode='reduced')
    check(np.linalg.matrix_rank(rn) == nuisance.shape[1], 'nuisance rank')
    yp = yw - qn @ (qn.T @ yw)
    sp = sw - qn @ (qn.T @ sw)
    scale = np.linalg.norm(sp, axis=0)
    check(np.all(scale > 0), 'zero signal column')
    u, s, vh = np.linalg.svd(sp / scale, full_matrices=False)
    rank = int(np.sum(s > rank_tol*s[0]))
    if rank != signal.shape[1]:
        return {'rank': rank, 'singular_values': s.tolist(),
                'nullspace_scaled': vh[rank:].tolist(), 'status': 'RANK_HOLD'}
    coeff = (vh.T @ ((u.T @ yp)/s)) / scale
    cov = (vh.T @ np.diag(1/s**2) @ vh) / scale[:, None] / scale[None, :]
    nuisance_coeff = np.linalg.solve(rn, qn.T @ (yw-sw@coeff))
    residual = yw - nw @ nuisance_coeff - sw @ coeff
    t = float(residual@residual)
    null_t = float(yp@yp)
    projection = sp@coeff
    delta = float(projection@projection)
    check(abs((null_t-t)-delta) < 1e-7*max(1, null_t), 'orthogonal likelihood identity')
    # Diagonal whitened hat leverage is descriptive and includes nuisances.
    qfull, _ = np.linalg.qr(np.column_stack((nw, sw)), mode='reduced')
    leverage = np.sum(qfull*qfull, axis=1)
    return {'status':'FULL_RANK', 'n':len(y), 'rank':rank,
            'nuisance_rank':len(nuisance_coeff), 'singular_values':s.tolist(),
            'coefficients_mag':coeff.tolist(), 'covariance_mag2':cov.tolist(),
            'nuisance_coefficients_mag':nuisance_coeff.tolist(),
            'T_null':null_t, 'T_full':t, 'delta_T':delta,
            'p_chi2_conditional':float(chi2.sf(delta,rank)),
            'threshold_0p05':float(chi2.isf(.05,rank)),
            'max_whitened_leverage':float(np.max(leverage)),
            'median_whitened_leverage':float(np.median(leverage)),
            'whitened_residual_rms':float(np.sqrt(t/len(y)))}


def subset_fit(rows, full_cov, lower):
    z = rows['zHD']
    mask = (rows['IS_CALIBRATOR'] == 0) & (z >= lower) & (z <= .15)
    for col in NAMES[2:]:
        mask &= np.isfinite(rows[col])
    idx = np.flatnonzero(mask)
    sub = rows[idx]
    C = full_cov[np.ix_(idx, idx)]
    high = sub['zHD'] >= .06
    mu32, integ32 = reference(sub['zHD'], sub['zHEL'], 32)
    mu64, integ64 = reference(sub['zHD'], sub['zHEL'], 64)
    qerr = float(np.max(np.abs(integ32-integ64)/integ64))
    check(qerr <= 1e-10, 'quadrature 32/64 agreement')
    n, nuisance, angular = design(sub['RA'], sub['DEC'], high)
    y = sub['m_b_corr'] - mu64
    selected_sym = float(np.max(np.abs(C-C.T)))
    threshold = float(64*np.finfo(float).eps*len(C)*np.max(np.abs(C)))
    check(np.all(np.isfinite(C)), 'selected covariance finite')
    check(selected_sym <= threshold, 'selected covariance symmetry')
    eigen_min = float(np.linalg.eigvalsh(C)[0])
    check(eigen_min > 0, 'selected covariance positive definite')
    fits = {}
    for name, s in [('null', angular[:, :0]),
                    ('dipole', angular[:, [0,1,2,8,9,10]]),
                    ('full', angular)]:
        if s.shape[1] == 0:
            L = np.linalg.cholesky(C)
            yw = solve_triangular(L,y,lower=True,check_finite=False)
            nw = solve_triangular(L,nuisance,lower=True,check_finite=False)
            q,_ = np.linalg.qr(nw,mode='reduced')
            fits[name] = {'T':float(np.linalg.norm(yw-q@(q.T@yw))**2), 'rank':2}
        else:
            fits[name] = fit(y,C,nuisance,s)
    f = fits['full']
    check(f['status']=='FULL_RANK', f'rank hold at lower={lower}')
    check(all(np.sum(np.array(f['singular_values'])>tol*f['singular_values'][0])==16
              for tol in (1e-12,1e-10,1e-8)), 'rank threshold sensitivity')
    coeff = np.array(f['coefficients_mag']); cov = np.array(f['covariance_mag2'])
    contrast = np.column_stack((-np.eye(8),np.eye(8)))
    d = contrast@coeff; dc = contrast@cov@contrast.T
    joint_ellipsoid = float(chi2.isf(.05,16))
    chart = 10*np.log10(1+sub['zHEL'])
    ystar = (sub['m_b_corr']-chart)-(mu64-chart)
    chart_error = float(np.max(np.abs(ystar-y)))
    check(chart_error < 1e-12, 'two-sided observer chart residual invariance')
    one_sided_error = float(np.max(np.abs((sub['m_b_corr']-chart)-mu64-y)))
    check(one_sided_error > 1e-3, 'one-sided chart must fail equivalence')
    ids = sub['CID'].tolist()
    duplicate_rows = int(len(ids)-len(set(ids)))
    surveys, counts = np.unique(sub['IDSURVEY'],return_counts=True)
    survey_counts = {str(k):int(v) for k,v in zip(surveys,counts)}
    diag = np.sqrt(np.diag(C))  # display diagnostics only; never enters a fit
    return {'selection_lower_zHD':lower,'original_indices':idx.tolist(),
            'row_key_sha256':hashlib.sha256('\n'.join(
                f'{int(i)}|{rows["CID"][i]}|{rows["IDSURVEY"][i]}'
                for i in idx).encode()).hexdigest(),
            'n_low':int(np.sum(~high)),'n_high':int(np.sum(high)),
            'duplicate_CID_rows':duplicate_rows, 'survey_counts':survey_counts,
            'HF_flag_counts':{str(k):int(v) for k,v in zip(*np.unique(sub['USED_IN_SH0ES_HF'],return_counts=True))},
            'covariance':{'dimension':len(idx),'max_symmetry_residual':selected_sym,
              'symmetry_tolerance':threshold,'min_eigenvalue_mag2':eigen_min,
              'cross_depth_nonzero_count':int(np.count_nonzero(C[np.ix_(~high, high)])),
              'cross_depth_max_abs_mag2':float(np.max(np.abs(C[np.ix_(~high, high)]))),
              'display_only_diag_sigma_range_mag':[float(diag.min()),float(diag.max())]},
            'quadrature_max_relative_32_vs_64':qerr,
            'fits':fits,'low_8_mag':coeff[:8].tolist(),'high_8_mag':coeff[8:].tolist(),
            'full_16x16_covariance_mag2':cov.tolist(),
            'high_minus_low_8_mag':d.tolist(),
            'high_minus_low_8x8_covariance_mag2':dc.tolist(),
            'simultaneous_95pct_16D_ellipsoid_squared_radius':joint_ellipsoid,
            'chart_both_side_max_residual_difference_mag':chart_error,
            'chart_one_side_falsifier_max_difference_mag':one_sided_error,
            'plot':{'zHD':sub['zHD'].tolist(),'RA':sub['RA'].tolist(),'DEC':sub['DEC'].tolist(),
                    'magnitude_residual':y.tolist(),'display_sigma':diag.tolist(),
                    'high':high.tolist()}}


def main():
    ids = {key:identity(*spec) for key,spec in FILES.items()}
    rows = np.genfromtxt(FILES['table'][0],names=True,dtype=None,encoding='utf-8')
    check(len(rows)==1701 and all(k in rows.dtype.names for k in NAMES), 'table schema')
    cov_raw = np.loadtxt(FILES['covariance'][0])
    check(len(cov_raw)==1+1701**2 and int(cov_raw[0])==1701, 'covariance schema')
    check(np.all(np.isfinite(cov_raw)), 'full covariance finite')
    C = cov_raw[1:].reshape(1701,1701)
    all_keys = hashlib.sha256('\n'.join(
        f'{i}|{rows["CID"][i]}|{rows["IDSURVEY"][i]}'
        for i in range(len(rows))).encode()).hexdigest()
    check(all_keys=='e596dae2a5349778c28e247854a9876c7eb9dd4f6337fe4c2ea1b7215837d0fe',
          'full released row key order')
    sym = float(np.max(np.abs(C-C.T)))
    symtol = float(64*np.finfo(float).eps*1701*np.max(np.abs(C)))
    check(sym<=symtol, 'full covariance symmetry')
    primary = subset_fit(rows,C,.0233)
    sensitivity = subset_fit(rows,C,.01)
    result = {'schema':'htt.r36_public_sn_released_magnitude/1',
      'owner':'htt','claim_tier':'C1','status':'PROPOSED_PENDING_INDEPENDENT_REVIEW',
      'scope':'Conditional released-magnitude anisotropy GLS with fixed background; source chart only',
      'source':{'release_commit':'c447f0fea703fcd0fff57de5000947b5ca81286b',
                'inputs':ids,'rows':1701,'covariance_entries':1701**2,'row_key_sha256':all_keys,
                'all_duplicate_CID_rows':int(1701-len(set(rows['CID'].tolist()))),
                'calibrator_counts':{str(k):int(v) for k,v in zip(*np.unique(rows['IS_CALIBRATOR'],return_counts=True))},
                'HF_flag_counts':{str(k):int(v) for k,v in zip(*np.unique(rows['USED_IN_SH0ES_HF'],return_counts=True))},
                'covariance_max_symmetry_residual':sym,'covariance_symmetry_tolerance':symtol},
      'model':{'signature':'(-,+,+,+)','c_m_per_s':299792458,
               'Omega_m_fixed':.3153,'Omega_Lambda_fixed':.6847,
               'redshifts':'zHD for dimensionless integral; zHEL for (1+zHEL); zCMB retained only',
               'VPEC':'released zHD correction and total covariance; no additional PV term',
               'basis':'H03 Frobenius [xx-yy,xx+yy-2zz,xy,xz,yz] normalized',
               'angular_axes':'released RA/DEC Cartesian chart; physical frame UNKNOWN',
               'covariance':'released full STAT+SYS magnitude covariance, used once; no rescale'},
      'primary':primary,'lower_z_sensitivity':sensitivity,
      'law':'Conditional fixed-design Gaussian with known released total C; p is chi-square_16 upper tail, nominal threshold only',
      'caveats':['No nominal SALT2 training parity or absolute H0',
                 'No physical congruence or sky-frame identification from released RA/DEC',
                 'No CF4 joint law without object-overlap and shared-PV covariance',
                 'No Bianchi family, physical shear or acceleration inference',
                 'Overlapping lower-z cohort is sensitivity, not independent confirmation',
                 'Selection, peculiar velocity and population effects are not established absent'],
      'unknown_sectors':{'physical_sky_frame':'UNKNOWN','physical_boost_response':'UNKNOWN',
          'raw_to_congruence_response':'UNKNOWN','CF4_shared_PV_law':'UNKNOWN',
          'nominal_SALT2_training_parity':'UNKNOWN','empirical_null_coverage':'UNKNOWN'}}
    SCRATCH.mkdir(parents=True,exist_ok=True)
    (SCRATCH/'RESULT_RAW.json').write_text(json.dumps(result,indent=2)+'\n')
    # Small result omits row arrays and plot vectors; full raw data stay on external scratch.
    for label in ('primary','lower_z_sensitivity'):
        result[label].pop('plot')
        result[label].pop('original_indices')
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'primary_n':primary['fits']['full']['n'],
       'primary_delta_T':primary['fits']['full']['delta_T'],
       'primary_p':primary['fits']['full']['p_chi2_conditional'],
       'sensitivity_n':sensitivity['fits']['full']['n'],
       'sensitivity_delta_T':sensitivity['fits']['full']['delta_T']}))


if __name__=='__main__':
    main()
