#!/usr/bin/env python3
"""Fixed-model redshift contrasts and finite nuisance quotient; no sky/ODE solver.

Summary mode consumes A22's published GLS/posterior moments. Stats mode consumes
its retained weighted normal equations, never reconstructing individual rows.
All probability statements remain conditional on the declared Gaussian experiment.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

SIGNAL_DIM = 18
PRIOR_VARIANCE = 10000.0  # (microarcsec/year)^2


def sym(a):
    return (a + a.T) / 2


def contrast_matrices():
    common = np.zeros((18, 3))
    low_high = np.zeros((3, 18))
    both = np.zeros((6, 18))
    for j in range(3):
        common[[j, j+6, j+12], j] = 1
        low_high[j, j] = 1
        low_high[j, j+12] = -1
        both[j, j] = 1
        both[j, j+12] = -1
        both[j+3, j+6] = 1
        both[j+3, j+12] = -1
    return common, low_high, both


def shifted_mixture(grid, delta, prior_variance=PRIOR_VARIANCE):
    """Exact fixed-design y -> y + D delta counterfactual, including weights.

    Derived by completing the Gaussian square with common N(0,p I) signal
    prior. Rows, covariance hypergrid, selection and prior are held fixed.
    """
    mu = np.array([m['posterior_mean_uasyr'] for m in grid])
    cov = np.array([m['posterior_cov_uas2yr2'] for m in grid])
    weights = np.array([m['posterior_hyper_weight'] for m in grid])
    if not np.all(weights > 0) or not np.isclose(weights.sum(), 1):
        raise ValueError('positive normalized original weights required')
    mu_shift = mu + delta - np.einsum('mij,j->mi', cov, delta)/prior_variance
    logw = (np.log(weights) - mu @ delta/prior_variance +
            np.einsum('i,mij,j->m', delta, cov, delta)/(2*prior_variance**2))
    neww = np.exp(logw-logw.max()); neww /= neww.sum()
    return neww @ mu_shift, neww


def summary_analysis(data):
    common, low_high, both = contrast_matrices()
    cohorts = []
    for cohort in data['cohorts']:
        grid = cohort['conditional_grid']
        baseline = next(m for m in grid if m['tau_angular'] == 0 and m['tau_template'] == 0)
        vb = np.array(baseline['conditional_gls_cov_uas2yr2'])
        fixed = []
        for m in grid:
            v = np.array(m['conditional_gls_cov_uas2yr2']); mean = np.array(m['conditional_gls_mean_uasyr'])
            pc = np.array(m['posterior_cov_uas2yr2']); pm = np.array(m['posterior_mean_uasyr'])
            # independent recovery from posterior moments, not zero-prior substitution
            f = sym(np.linalg.inv(pc)-np.eye(18)/PRIOR_VARIANCE)
            recovered = np.linalg.solve(f, np.linalg.solve(pc, pm))
            vc = np.linalg.inv(f)
            leak = low_high @ (np.eye(18)-pc/PRIOR_VARIANCE) @ common
            fixed.append(dict(lmax=m['lmax'], tau_angular=m['tau_angular'], tau_template=m['tau_template'],
                              low_minus_high_E1_uasyr=(low_high@mean).tolist(),
                              covariance_uas2yr2=(low_high@v@low_high.T).tolist(),
                              two_E1_contrasts_uasyr=(both@mean).tolist(),
                              two_E1_contrasts_covariance_uas2yr2=(both@v@both.T).tolist(),
                              common_E1_leakage_operator=leak.tolist(),
                              common_E1_leakage_spectral_norm=float(np.linalg.norm(leak, 2)),
                              deshrink_mean_max_error=float(np.max(np.abs(mean-recovered))),
                              deshrink_cov_max_error=float(np.max(np.abs(v-vc)))))
        representative = next(m for m in grid if m['lmax']==3 and m['tau_angular']==10 and m['tau_template']==10)
        diff = sym(np.array(representative['conditional_gls_cov_uas2yr2'])-vb)
        ev = np.linalg.eigvalsh(diff); ec = np.linalg.eigvalsh(sym(both@diff@both.T))
        shifted, neww = shifted_mixture(grid, common@np.array([100., 0., 0.]))
        original = np.array([m['posterior_hyper_weight'] for m in grid]) @ np.array([m['posterior_mean_uasyr'] for m in grid])
        centers=np.array([m['low_minus_high_E1_uasyr'] for m in fixed])
        halfwidth=np.array([np.sqrt(7.814727903251179*np.diag(m['covariance_uas2yr2'])) for m in fixed])
        cohorts.append(dict(cohort=cohort['cohort'], n=cohort['n'], fixed_models=fixed,
            fixed_family_union_95=dict(chi2_df=3,chi2_threshold=7.814727903251179,
                coordinate_envelope_low=(centers-halfwidth).min(axis=0).tolist(),
                coordinate_envelope_high=(centers+halfwidth).max(axis=0).tolist(),
                condition='At least one fixed grid model is the true zero-mean Gaussian experiment; same selected design.',
                geometry='union of 32 full-covariance ellipsoids; coordinate envelope is only its bounding box'),
            fixed_GLS_common_E1_leakage=float(np.linalg.norm(low_high@common)),
            mixture_counterfactual=dict(common_E1_shift_uasyr=[100.,0.,0.],
                low_minus_high_shift_uasyr=(low_high@(shifted-original)).tolist(),
                hyperweight_L1_shift=float(np.abs(neww-np.array([m['posterior_hyper_weight'] for m in grid])).sum())),
            nuisance_information_loss=dict(reference=[3,10,10], covariance_difference_eigenvalues=ev.tolist(),
                two_E1_contrasts_eigenvalues=ec.tolist(),
                rank_18=int(np.count_nonzero(ev>ev[-1]*1e-9)),
                rank_6=int(np.count_nonzero(ec>ec[-1]*1e-9)),relative_rank_tolerance=1e-9)))
    return dict(owner='htt', claim_tier='C1', status='CONDITIONAL', artifact_mode='summary_algebra_diagnostic',
        transfer_source='none', units='microarcsecond/year', sky_support_status='fixed A22 selected rows; no new sky',
        null_mock_status='not an empirical coverage calibration',
        covariance_status='published fixed-model Gaussian GLS and proper-prior posterior covariances',
        allowed_use='contrast invariance audit and finite-nuisance repair design',
        forbidden_uses=['cosmic acceleration detection','global tilt identification','native Bianchi family identification',
                        'replacement for failed l4/template stress coverage'],
        caveats=['Same selected rows and design only; selection is not re-executed.',
                 'Exact GLS common-E1 cancellation does not annihilate arbitrary angular or selection-template means.',
                 'No original scientific DAG node is promoted by this result.',
                 'Covariance-difference rank only constrains contrasts of the baseline compressed GLS estimator.',
                 'Known-cut Q from the Gaussian-field experiment cannot be reused for unrestricted nuisance means.'],
        cohorts=cohorts)


def psd_inverse(a, rtol=1e-10, atol=1e-12):
    a = sym(np.asarray(a, dtype=float))
    e, u = np.linalg.eigh(a)
    tol = max(atol, rtol*max(0., e[-1]))
    if e[0] < -10*tol:
        raise ValueError('matrix is not positive semidefinite at declared tolerance')
    keep = e > tol
    inv = (u[:,keep]/e[keep])@u[:,keep].T
    return inv, u[:,keep]@u[:,keep].T, e, tol


def finite_nuisance_quotient(gram, score, signal_dim=18, contrasts=None, rtol=1e-10):
    """Conditional finite-mean quotient, with column-normalized rank decisions.

    Numerical null spaces are assumed exact at the stated roundoff tolerance.
    Partial-rank outputs use the Euclidean geometry of the supplied physical
    signal coordinates; unreliable transport to those coordinates fails closed.
    """
    g = np.asarray(gram, dtype=float); b = np.asarray(score, dtype=float)
    if (g.ndim != 2 or g.shape[0] != g.shape[1] or b.shape != (g.shape[0],)
            or not isinstance(signal_dim, (int, np.integer))
            or not 0 < signal_dim < g.shape[0]):
        raise ValueError('incompatible normal-equation dimensions')
    if not np.isfinite(rtol) or not 0 < rtol < 1:
        raise ValueError('finite 0 < rtol < 1 required')
    if not np.all(np.isfinite(g)) or not np.all(np.isfinite(b)):
        raise ValueError('finite normal equations required')
    diagonal = np.diag(g)
    if np.any(diagonal < 0):
        raise ValueError('negative Gram diagonal')
    zero = diagonal == 0
    if np.any(g[zero, :] != 0) or np.any(g[:, zero] != 0) or np.any(b[zero] != 0):
        raise ValueError('zero Gram diagonal requires exact zero row, column and score')
    scale = np.ones(len(b)); scale[~zero] = np.sqrt(diagonal[~zero])
    # Sequential division avoids overflow in the product of column scales.
    gb = g / scale[:, None] / scale[None, :]; bb = b / scale
    if not np.all(np.isfinite(gb)) or not np.all(np.isfinite(bb)):
        raise ValueError('normalization overflow')
    eps = np.finfo(float).eps; size = len(b); n = signal_dim
    roundoff = 32 * eps * max(1, size)
    normg = np.linalg.norm(gb, 2)
    if np.linalg.norm(gb-gb.T, 2) > roundoff * max(1., normg):
        raise ValueError('normalized Gram is not symmetric')
    gb = sym(gb)
    if np.linalg.eigvalsh(gb)[0] < -roundoff * max(1., normg):
        raise ValueError('normalized Gram is not positive semidefinite')
    a, j, c = gb[:n, :n], gb[:n, n:], gb[n:, n:]
    bh = bb[n:]; nh = size-n
    ce, cu = np.linalg.eigh(c)
    epsc = 32 * eps * max(1, nh) * max(1., np.linalg.norm(c, 2))
    rankc = max(epsc, rtol * max(1., ce[-1]))
    if ce[0] < -epsc:
        raise ValueError('negative normalized nuisance eigenvalue')
    if np.any((ce > epsc) & (ce <= rankc)):
        raise ValueError('ambiguous positive nuisance rank')
    retainc = ce > rankc; nullc = np.abs(ce) <= epsc
    u0 = cu[:, nullc]
    if np.linalg.norm(j @ u0) > roundoff * max(1., normg):
        raise ValueError('nuisance null cross block is incompatible')
    if np.linalg.norm(u0.T @ bh) > roundoff * np.linalg.norm(bb):
        raise ValueError('nuisance null score is incompatible')
    urc = cu[:, retainc]; cr = ce[retainc]
    t = (j @ urc) / np.sqrt(cr)
    z = (urc.T @ bh) / np.sqrt(cr)
    f = sym(a-t @ t.T); q = bb[:n]-t @ z
    jcplus = ((j @ urc) / cr) @ urc.T
    epsf = roundoff * max(1., normg) * (1+np.linalg.norm(jcplus, 2))**2
    tau = max(rtol * max(1., np.linalg.norm(a, 2)), epsf)
    eigenvalues, u = np.linalg.eigh(f)
    if eigenvalues[0] < -epsf:
        raise ValueError('negative normalized quotient eigenvalue')
    keep = eigenvalues > tau; ur = u[:, keep]; lam = eigenvalues[keep]
    score_tol = roundoff * (np.linalg.norm(bb[:n])+np.linalg.norm(t, 2)*np.linalg.norm(z))
    if np.linalg.norm(u[:, ~keep].T @ q) > score_tol:
        raise ValueError('quotient score outside retained range')
    sd = scale[:n]; rank = len(lam)
    coeff = (ur.T @ q) / np.sqrt(lam)
    transport_eta = None
    transport_branch = 'full_rank' if rank == n else 'rank_zero' if rank == 0 else 'partial_rank'
    if rank == n:
        projector = np.eye(n)
        l = (ur / sd[:, None]) / np.sqrt(lam)
    elif rank == 0:
        projector = np.zeros((n, n)); l = np.zeros((n, 0))
    else:
        gap = np.min(lam)-np.max(eigenvalues[~keep])
        transport_eta = (np.max(sd)/np.min(sd)) * epsf/gap if gap > 0 else np.inf
        if not np.isfinite(transport_eta) or transport_eta > 1e-7:
            raise ValueError('unreliable partial-rank physical projection')
        physical_q, physical_r = np.linalg.qr(sd[:, None]*ur, mode='reduced')
        l = physical_q @ np.linalg.solve(physical_r.T, np.diag(1/np.sqrt(lam)))
        projector = physical_q @ physical_q.T
    vi = l @ l.T; estimate = l @ coeff
    if contrasts is None:
        contrasts = np.eye(n)
    k = np.asarray(contrasts, dtype=float)
    if k.ndim != 2 or k.shape[1] != n or not np.all(np.isfinite(k)):
        raise ValueError('finite contrast rows with signal_dim columns required')
    kb = k / sd
    if not np.all(np.isfinite(kb)):
        raise ValueError('contrast normalization overflow')
    if np.any((k != 0) & (kb == 0)):
        raise ValueError('contrast normalization underflow')
    # Scale each nonzero row before taking norms: scalar changes cannot turn
    # a nonestimable contrast into an identified zero (including tiny rows).
    maxima = np.max(np.abs(kb), axis=1)
    kn = np.zeros_like(kb); nonzero = maxima != 0
    kn[nonzero] = kb[nonzero] / maxima[nonzero, None]
    leakage = np.linalg.norm(kn-(kn @ ur) @ ur.T, axis=1)
    relative = np.zeros(len(k)); relative[nonzero] = leakage[nonzero]/np.linalg.norm(kn[nonzero], axis=1)
    estimable = relative <= 1e-7
    direct_l = (kb @ ur) / np.sqrt(lam)
    direct_estimate = direct_l @ coeff
    # For unestimable rows report the physical projected-coordinate covariance.
    # Estimable rows use the normalized quotient directly, avoiding transport loss.
    contrast_l = k @ l
    contrast_l[estimable] = direct_l[estimable]
    with np.errstate(over='ignore', under='ignore', invalid='ignore'):
        contrast_covariance = contrast_l @ contrast_l.T
    # A nonzero estimable row has strictly positive variance in the retained
    # quotient. A zero or nonfinite diagonal cannot represent that uncertainty.
    variance = np.diag(contrast_covariance)
    if np.any(estimable & nonzero & ((variance <= 0) | ~np.isfinite(variance))):
        raise ValueError('nonzero estimable contrast variance outside floating-point range')
    return dict(signal_rank=rank, signal_dim=n,
                fisher_eigenvalues=eigenvalues.tolist(), eigenvalue_tolerance=float(tau),
                fisher_coordinate_system='column-normalized signal coordinates',
                numerical_diagnostics=dict(
                    column_scales=scale.tolist(),
                    nuisance_rank=int(np.count_nonzero(retainc)),
                    nuisance_roundoff_tolerance=float(epsc),
                    nuisance_rank_tolerance=float(rankc),
                    quotient_roundoff_tolerance=float(epsf),
                    quotient_rank_tolerance=float(tau),
                    contrast_relative_tolerance=1e-7,
                    physical_projector_transport=dict(
                        branch=transport_branch,
                        eta=None if transport_eta is None else float(transport_eta),
                        eta_threshold=1e-7,
                        status='not_applicable' if transport_eta is None else 'accepted_conservative_guard',
                        interpretation='numerical diagnostic, not a rigorous error certificate')),
                estimable_projector=projector.tolist(), projected_signal_estimate=estimate.tolist(),
                projected_signal_covariance=vi.tolist(),
                contrast_estimable=estimable.tolist(), nonestimability_norm=relative.tolist(),
                nonestimability_norm_status='relative normalized-coordinate row residual; zero row is exactly estimable',
                contrast_estimate=[float(x) if ok else None for x, ok in zip(direct_estimate, estimable)],
                contrast_covariance=contrast_covariance.tolist(),
                contrast_covariance_status='conditional covariance; unestimable rows are physical projected coordinates only',
                covariance_status='conditional supplied W=C^-1; empirical correlated residual covariance not supplied',
                claim_status='DIAGNOSTIC_ONLY; projected coordinates only; no empirical coverage or cosmic A claim')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    s=sub.add_parser('summary'); s.add_argument('--input',type=Path,required=True);s.add_argument('--output',type=Path,required=True)
    t=sub.add_parser('stats');t.add_argument('--input',type=Path,required=True);t.add_argument('--expected-sha256',required=True);t.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); raw=args.input.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    if args.mode=='summary':
        result=summary_analysis(json.loads(raw))
    else:
        if sha!=args.expected_sha256:raise ValueError('cached sufficient-statistics SHA mismatch')
        with np.load(args.input,allow_pickle=False) as z:
            if z['G'].shape!=(102,102):raise ValueError('expected A22 18 signal + 84 nuisance columns')
            result=finite_nuisance_quotient(z['G'],z['b'],contrasts=contrast_matrices()[2])
        result.update(owner='htt',transfer_source='none',claim_tier='C1',
            finite_nuisance_columns='l2+l3 E/B, 7 selection templates x E/B l1, l4 E/B',
            caveats=['Conditional noise model only. Unrestricted fixed means invalidate old Gaussian-field cut-Q bound.',
                     'Unmodelled higher fields, selection, measurement covariance and redshift errors remain.'])
    result['input_sha256']=sha
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':
    main()
