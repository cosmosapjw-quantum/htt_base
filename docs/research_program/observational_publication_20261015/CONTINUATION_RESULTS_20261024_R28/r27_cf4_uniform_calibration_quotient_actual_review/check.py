#!/usr/bin/env python3
"""One independent QR/source-array check; never imports the candidate consumer."""
import time
START = time.monotonic_ns()
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import numpy as np
import scipy.linalg as la

HERE = Path(__file__).resolve().parent
NUM = HERE.parent / 'r27_cf4_uniform_calibration_quotient_numeric'
PROD = NUM / 'actual_run/products'
EXPECTED = {
    NUM / 'INPUT.json': '570383ac224808090c57b356ee21cc7f114a27d712ee725c5c42850bf00d61fd',
    NUM / 'consume.py': 'd8c3a7526f97f196bcc29b5fbd0ead26aadb1a0230268ea9f2736074c8fcf798',
    PROD / 'RESULT.json': 'c5148c206e6ec7d5f0e69cbc3ab8dc2c0c2f815d3b304431e0aa0cd16e91883d',
    PROD / 'CARRIER.npz': '21763a9722c8375d593c1f0dcd68d42f31cb1952f22a4140a0df1eea285d6c28',
    PROD / 'INFORMATION_AND_CONTRASTS.png': '8afbf2e1dc285a8d2be423f44c090541713765a0b275b9ca7362a05a7325a6fe',
}
report = {'status': 'STARTED', 'method': 'Source-array alignment; normalized pivoted QR nuisance projection and triangular signal solve; compact identities; no candidate import or old campaign replay', 'checks': {}, 'numerical_checks_are_not_exact_certificates': True}

def require(name, condition, value=None):
    report['checks'][name] = {'pass': bool(condition), 'value': value}
    if not condition:
        raise AssertionError(name)

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def residual(name, value, scale, tolerance=1e-10):
    raw = float(np.linalg.norm(value))
    scale = max(float(scale), np.finfo(float).tiny)
    scaled = raw / scale
    require(name, np.isfinite(scaled) and scaled <= tolerance,
            {'raw_frobenius_or_euclidean': raw, 'denominator': scale, 'scaled': scaled, 'tolerance': tolerance})

def load(p):
    with np.load(p, allow_pickle=False) as f:
        return {k: f[k] for k in f.files}

try:
    for p, h in EXPECTED.items():
        require('sealed:' + p.name, digest(p) == h, h)
    inp = json.loads((NUM / 'INPUT.json').read_text())
    for role, item in {**inp['inputs'], **inp['contract_binding']}.items():
        require('input:' + role, Path(item['path']).stat().st_size == item['bytes'] and digest(item['path']) == item['sha256'])
    out = json.loads((PROD / 'RESULT.json').read_text())
    car = load(PROD / 'CARRIER.npz')
    src = load(inp['inputs']['selected_source']['path'])
    op = load(inp['inputs']['group_operator']['path'])
    ids = car['group_id']; active = car['active_singleton_mask']; mixed = car['mixed_zero_leverage_mask']
    support = car['selected_support_7']; C = car['C']; B = car['B']; N = car['N']; d = car['d']; y = car['y']; K = car['K']
    require('full_cohort_order', len(ids) == 35970 and np.array_equal(ids, src['group_id']) and np.array_equal(ids, op['selected_pgc']) and hashlib.sha256(ids.astype('<i8').tobytes()).hexdigest() == inp['selected_id_sha256_little_endian_int64'])
    require('support_masks', np.array_equal(active, support.sum(1) == 1) and np.array_equal(mixed, ~active) and int(mixed.sum()) == 944 and np.all(support.sum(1) > 0))
    require('C_exact_definition', np.array_equal(C[active], support[active].astype(float)) and np.count_nonzero(C[mixed]) == 0)
    require('exact_mixed_K_columns', np.count_nonzero(K[:, mixed]) == 0)
    require('row_lists_and_leverage', np.array_equal(car['mixed_group_id'], ids[mixed]) and np.array_equal(car['active_group_id'], ids[active]) and np.array_equal(car['leverage'], np.linalg.norm(K, axis=0)))
    require('direct_ids_support', set(ids[support[:, 6]].tolist()) == {20679, 59927} and np.all(active[support[:, 6]]))
    maps = {'nominal': op['selected_nominal_A7'], 'round_nearest': op['selected_witness_A7'][:, 0], 'one_place_outer': op['selected_witness_A7'][:, 1]}
    for label, A in maps.items():
        require('source_map:' + label, np.isfinite(A).all() and np.all(A >= 0) and np.array_equal(A > 0, support) and np.array_equal(A[active], C[active]) and np.max(abs(A.sum(1) - 1)) <= 1e-14)
        residual('KA:' + label, K @ A, np.linalg.norm(K) * np.linalg.norm(A))

    path = Path(inp['inputs']['e1_design']['path'])
    spec = importlib.util.spec_from_file_location('review_sealed_e1_design', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    require('model_resolved_exact_source', Path(module.__file__).resolve() == path.resolve())
    model = module.model_matrix(src['z_CMB'], src['n_J2000'], src['method_family'], H0=74.6, omega_m=.3153, include_method_slope=True, include_bulk=True, include_angular_dipole=True)
    X = model['design']; sl = model['slices']['shear']
    require('B_full_cohort_source', np.array_equal(B, X[:, sl]))
    require('N_full_cohort_source', np.array_equal(N, np.delete(X, np.arange(sl.start, sl.stop), axis=1)))
    ds = src['e_dmzp'] ** 2 + .15 ** 2 + (250 * model['redshift_velocity_width_basis_mag_per_kms']) ** 2
    require('D_source_and_direct_errors', np.array_equal(d, ds), {'direct_e_dmzp': src['e_dmzp'][support[:, 6]].tolist(), 'direct_d': d[support[:, 6]].tolist()})
    require('y_reference_source', np.array_equal(y, src['dmzp'] - model['reference_mu_mag']))
    E = np.zeros((5, 3, 3)); E[0] = np.diag([1, -1, 0]) / np.sqrt(2); E[1] = np.diag([1, 1, -2]) / np.sqrt(6)
    for k, (i,j) in enumerate(((0,1), (0,2), (1,2)), 2): E[k,i,j] = E[k,j,i] = 1/np.sqrt(2)
    require('STF_basis_source_and_order', np.array_equal(E, car['STF_basis_5x3x3']) and np.array_equal(E, module.stf2_orthonormal()))
    w = 1 / np.sqrt(d); Bw = w[:, None] * B; Nw = w[:, None] * N
    U = np.column_stack((Nw[active], w[active, None] * C[active]))
    norms = np.linalg.norm(U, axis=0); Uscaled = U[:, norms > 0] / norms[norms > 0]
    qfull, ru, piv = la.qr(Uscaled, mode='economic', pivoting=True)
    us = la.svdvals(ru); thresholds = (1e-12, 1e-10, 1e-8)
    ranks = [int(np.count_nonzero(us > t * us[0])) for t in thresholds]
    require('independent_nuisance_rank', ranks == [19,19,19], {'counts': ranks, 'spectrum': us.tolist(), 'pivots': piv.tolist()})
    Q = qfull[:, :19]
    def project(arr): return arr - Q @ (Q.T @ arr)
    Ra = project(Bw[active]); ta = project(w[active] * y[active])
    residual('independent_R_vs_carrier', Ra-car['R'][active], np.linalg.norm(Ra))
    residual('independent_t_vs_carrier', ta-car['t'][active], np.linalg.norm(ta))
    residual('nuisance_span_Q_vs_stored', Q-car['Q_active'] @ (car['Q_active'].T @ Q), np.linalg.norm(Q))
    external = float(la.svdvals(Bw)[0]); rs = la.svdvals(Ra)
    signal_ranks = [int(np.count_nonzero(rs > t * external)) for t in thresholds]
    require('independent_signal_rank_external_scale', signal_ranks == [5,5,5], {'counts': signal_ranks, 'external_scale': external, 'spectrum': rs.tolist()})
    residual('external_scale_saved', np.asarray(external-out['signal']['external_preprojection_target_scale']), external)
    qr, rr = la.qr(Ra, mode='economic')
    b_alt = la.solve_triangular(rr, qr.T @ ta)
    inv_rr = la.solve_triangular(rr, np.eye(5))
    cw_alt = inv_rr @ inv_rr.T
    K_alt_active = la.solve_triangular(rr, qr.T - (qr.T @ Q) @ Q.T) * w[active]
    residual('independent_K', K_alt_active-K[:,active], np.linalg.norm(K[:,active]))
    residual('independent_b', b_alt-car['b_min'], np.linalg.norm(b_alt))
    residual('independent_working_covariance', cw_alt-car['C_work_id'], np.linalg.norm(cw_alt))
    residual('stored_K_y_vs_b', K @ y-car['b_min'], np.linalg.norm(car['b_min']))
    F_alt = Ra.T @ Ra
    residual('independent_Fstar', F_alt-car['F_star'], np.linalg.norm(F_alt))
    residual('KN', K @ N, np.linalg.norm(K) * np.linalg.norm(N))
    residual('KC', K @ C, np.linalg.norm(K) * np.linalg.norm(C))
    residual('KB_minus_Pid', K @ B-car['P_identified'], np.linalg.norm(car['P_identified']))
    residual('KDKt_vs_Cwork', (K*d) @ K.T-car['C_work_id'], np.linalg.norm(car['C_work_id']))
    residual('projector_orthogonality', Q.T @ Q-np.eye(19), np.sqrt(19))
    residual('projector_idempotence_on_B', project(Ra)-Ra, np.linalg.norm(Ra))
    # Weighted group-mean elimination verifies the seven singleton-channel factors.
    H = (w[active,None]*C[active]); H /= np.linalg.norm(H,axis=0)
    centered = Bw[active]-H @ (H.T @ Bw[active])
    residual('channel_centering_preserves_final_response', project(centered)-Ra, np.linalg.norm(Ra))
    old_result = json.loads(Path(inp['inputs']['e1_result']['path']).read_text())['source_comparisons']['all']
    F_old = np.asarray(old_result['schur_fisher'])
    qo, _ = la.qr(Nw/np.linalg.norm(Nw,axis=0),mode='economic')
    ro = Bw-qo @ (qo.T @ Bw)
    require('saved_E1_Fisher_design_only', np.allclose(ro.T@ro,F_old,rtol=1e-9,atol=1e-10), float(np.max(abs(ro.T@ro-F_old))))
    eig_delta = la.eigvalsh(F_old-F_alt); frac = la.eigh(F_alt,F_old,eigvals_only=True)
    require('information_monotonicity', eig_delta[0] >= -1e-9*max(1,np.linalg.norm(F_old,2)) and frac.min() >= -1e-9 and frac.max() <= 1+1e-9, {'difference_eigenvalues':eig_delta.tolist(),'generalized_unclipped':frac.tolist()})
    residual('information_eigenvalues_saved',frac-np.asarray(out['generalized_information_eigenvalues_raw_ascending']),np.linalg.norm(frac))
    V = car['V_identified']; Pid=car['P_identified']
    require('full_five_coordinate_and_null_shapes', V.shape == (5,5) and car['V_complement'].shape == (5,0))
    residual('identified_projector',V@V.T-Pid,np.sqrt(5))
    residual('signed_contrasts',V.T@b_alt-np.asarray(out['identified_signed_contrasts']),np.linalg.norm(b_alt))
    residual('saved_old_contrasts',V.T@np.asarray(old_result['apparent_stf_coefficients'])-np.asarray(out['saved_old_signed_contrasts_in_new_basis']),np.linalg.norm(old_result['apparent_stf_coefficients']))
    residual('tensor_decode',np.einsum('a,aij->ij',b_alt,E)-np.asarray(out['complete_3x3_tensor']),np.linalg.norm(b_alt))
    report['numeric_summary']={'source_rows':len(ids),'active_rows':int(active.sum()),'structurally_zero_mixed_rows':int(mixed.sum()),'b_independent':b_alt.tolist(),'information_fractions':frac.tolist(),'raw_KC_frobenius':float(np.linalg.norm(K@C)),'exact_binary_annihilation':'NOT_ESTABLISHED','unbounded_Gamma_protection':'NOT_ESTABLISHED','actual_covariance':'UNKNOWN','physical_H02_H03_H04':'UNCHANGED'}
    report['status']='ALL_INDEPENDENT_CHECKS_PASSED'
except Exception as e:
    report['status']='FIRST_INDEPENDENT_CHECK_FAILURE'; report['exception']=repr(e)
finally:
    report['elapsed_before_report_persistence_seconds']=(time.monotonic_ns()-START)/1e9
    with (HERE/'NUMERIC_CHECK.json').open('x') as f:
        json.dump(report,f,indent=2,allow_nan=False); f.write('\n'); f.flush(); os.fsync(f.fileno())
    print(json.dumps({'status':report['status'],'elapsed_after_report_fsync_seconds':(time.monotonic_ns()-START)/1e9}),flush=True)
raise SystemExit(0 if report['status']=='ALL_INDEPENDENT_CHECKS_PASSED' else 1)
