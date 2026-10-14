#!/usr/bin/env python3
"""RB10/11 Union3 22-node + DESI BGS qiso conditional Gaussian scenario.

A normalized joint density with a declared cross-covariance sensitivity, not
catalogue coverage, angular information, CF4 incorporation, or native solver work.
"""
from __future__ import annotations
import argparse
from dataclasses import replace
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits
from scipy.linalg import cho_factor, cho_solve
from scipy.special import logsumexp, roots_legendre

ROOT = Path(os.environ.get('HTT_REBOOT_SOURCE_ROOT', Path(__file__).resolve().parents[1]))
CODE_ROOT = Path(os.environ.get('HTT_REBOOT_CODE_ROOT', ROOT))
for path in (ROOT / 'htt/src', ROOT / 'htt', ROOT, CODE_ROOT / 'htt/htt'):
    sys.path.insert(0, str(path))
from htt.infer.conditional_legacy_pushforward import PosteriorDrawSource, posterior_distance_image, distance_state_digest

UNION = ROOT / 'workdir/rrss_observational_inputs/union3_release-main/mu_mat_union3_cosmo=2_mu.fits'
DESI = ROOT / 'docs/generated/tensor_joint_r7/delivery/nodes/R7-08/compressed_bao.json'
EXPECTED_DESI_SOURCE = 'DESI_DR1_FULLSHAPE_BGS_v1.2:836a2107c1edfb655f7a5c41701607dd8542efe4dae4309737658829cfe63ba3'
EXPECTED_UNION_SHA256 = 'ef98b7dde1025ee7134f3242aaea3f1f0ed3f2b29a718458c550a8e4e24d0349'
EXPECTED_DESI_JSON_SHA256 = 'c9382695890142c1b0917429f9606cd845fd36b5e3950b34d6bb336cff4a7465'
C_LIGHT = 299792.458
RHO = (0.0, 0.25, -0.25, 0.5, -0.5)
Z_IMAGE = np.array([0.1, 0.2952346949471036, 0.5, 1.0])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs(union=UNION, desi=DESI):
    if Path(union) == UNION and sha(union) != EXPECTED_UNION_SHA256:
        raise ValueError('frozen Union3 input identity mismatch')
    if Path(desi) == DESI and sha(desi) != EXPECTED_DESI_JSON_SHA256:
        raise ValueError('frozen DESI summary input identity mismatch')
    with fits.open(union, memmap=False) as f:
        raw = np.asarray(f[0].data, float)
    if raw.shape != (23, 23) or not np.isfinite(raw).all():
        raise ValueError('Union3 must be the finite released 22-node matrix')
    z = raw[0, 1:].copy()
    mu = raw[1:, 0].copy()
    p = (raw[1:, 1:] + raw[1:, 1:].T) / 2
    if np.any(z <= 0) or np.any(np.diff(z) <= 0):
        raise ValueError('Union3 redshift layout/domain')
    np.linalg.cholesky(p)
    payload = json.loads(Path(desi).read_text())
    if (payload['source_id'] != EXPECTED_DESI_SOURCE
            or payload['likelihood_name'] != 'gaussian_likelihood'
            or payload['parameter'] != 'qiso' or payload['window'] != [[1.0]]
            or len(payload['observed']) != 1 or len(payload['covariance']) != 1
            or len(payload['covariance'][0]) != 1):
        raise ValueError('unrecognized DESI summary conditioning')
    q = float(payload['observed'][0])
    variance = float(payload['covariance'][0][0])
    zeff = float(payload['zeff'])
    fid = float(payload['DV_over_rd_fid'])
    if not all(np.isfinite([q, variance, zeff, fid])) or variance <= 0 or zeff <= 0 or fid <= 0:
        raise ValueError('invalid DESI compressed scalar')
    return dict(z=z, mu=mu, precision=p, q=q, variance=variance,
                zeff=zeff, fid=fid, union_sha256=sha(union),
                desi_sha256=sha(desi), desi_source_id=payload['source_id'])


def radial(omega, z):
    """Vectorized fixed 96-point Gauss rule for smooth flat-LCDM integrals."""
    omega = np.asarray(omega, float).reshape(-1)
    z = np.asarray(z, float).reshape(-1)
    if np.any(omega <= 0) or np.any(omega >= 1) or np.any(z <= 0):
        raise ValueError('interior Omega and positive redshift required')
    x, wt = roots_legendre(96)
    t = z[:, None] * (x[None, :] + 1) / 2
    inv_e = 1 / np.sqrt(omega[:, None, None] * (1 + t[None, :, :])**3
                        + 1 - omega[:, None, None])
    return np.sum(inv_e * wt[None, None, :], axis=2) * z[None, :] / 2


def table(order, data, om_bounds=(0.01, 0.99), ar_bounds=(5000., 20000.)):
    x, w = roots_legendre(order)
    om = (om_bounds[1] + om_bounds[0]) / 2 + (om_bounds[1] - om_bounds[0]) * x / 2
    ar = (ar_bounds[1] + ar_bounds[0]) / 2 + (ar_bounds[1] - ar_bounds[0]) * x / 2
    prior_w = w / 2  # each transformed uniform prior integrates to one
    zi = np.concatenate([data['z'], [data['zeff']], Z_IMAGE])
    integrals = radial(om, zi)
    n = len(data['z'])
    iu = integrals[:, :n]
    ie = integrals[:, n]
    e_eff = np.sqrt(om * (1 + data['zeff'])**3 + 1 - om)
    s = 5 * np.log10((1 + data['z'][None, :]) * iu)
    qshape = C_LIGHT / data['fid'] * np.cbrt(data['zeff'] * ie**2 / e_eff)
    return dict(om=om, ar=ar, om_bounds=om_bounds, ar_bounds=ar_bounds, prior_w=prior_w, s=s, qshape=qshape,
                image_integrals=integrals[:, n + 1:])


def covariance(data, rho):
    if abs(rho) >= 1:
        raise ValueError('rho outside SPD range')
    p = data['precision']
    cu = np.linalg.inv(p)
    h = 1e-4
    z = data['z']
    d = (5 * np.log10((1 + z) * radial([0.3 + h], z)[0])
         - 5 * np.log10((1 + z) * radial([0.3 - h], z)[0])) / (2 * h)
    one = np.ones(len(z))
    v = d - one * ((one @ p @ d) / (one @ p @ one))
    w = v / np.sqrt(v @ p @ v)
    cross = rho * np.sqrt(data['variance']) * w
    c = np.empty((len(z) + 1, len(z) + 1))
    c[:-1, :-1] = cu
    c[:-1, -1] = cross
    c[-1, :-1] = cross
    c[-1, -1] = data['variance']
    np.linalg.cholesky(c)
    if not np.allclose(c[:-1, :-1], cu, rtol=1e-12, atol=1e-12) or c[-1, -1] != data['variance']:
        raise ArithmeticError('cross covariance changed a released marginal')
    return c, w


def fit_grid(data, tab, rho, y=None, m_prior=(43., 5.)):
    """Normalized density, analytic Gaussian M marginal, proper tensor prior."""
    c, w = covariance(data, rho)
    n = len(data['z'])
    a = np.r_[np.ones(n), 0.]
    cm = c + m_prior[1]**2 * np.outer(a, a)
    fac = cho_factor(cm, lower=True, check_finite=True)
    k = cho_solve(fac, np.eye(n + 1))
    sign, logdet = np.linalg.slogdet(cm)
    if sign != 1:
        raise ArithmeticError('marginal covariance not SPD')
    if y is None:
        y = np.r_[data['mu'], data['q']]
    y = np.asarray(y, float)
    if y.shape != (n + 1,) or not np.isfinite(y).all():
        raise ValueError('ordered 22+1 observation required')
    ru = y[:-1][None, :] - tab['s'] - m_prior[0]
    rq = y[-1] - tab['qshape'][:, None] / tab['ar'][None, :]
    ku = k[:-1, -1]
    uquad = np.einsum('ij,jk,ik->i', ru, k[:-1, :-1], ru)
    ulin = ru @ ku
    chi = uquad[:, None] + 2 * ulin[:, None] * rq + k[-1, -1] * rq**2
    ll = -.5 * (chi + logdet + (n + 1) * np.log(2 * np.pi))
    logjoint = ll + np.log(tab['prior_w'])[:, None] + np.log(tab['prior_w'])[None, :]
    logz = float(logsumexp(logjoint))
    weights = np.exp(logjoint - logz)
    if abs(float(weights.sum()) - 1) > 2e-12:
        raise ArithmeticError('posterior measure failed normalization')
    # Recover M from the original, UNMARGINALIZED C. The q residual contributes
    # when rho is nonzero; using C+25aa' here would double-marginalize M.
    cfac = cho_factor(c, lower=True)
    ca = cho_solve(cfac, a)
    mvar = 1 / (1 / m_prior[1]**2 + a @ ca)
    mmean = (m_prior[0] + mvar * (ru @ ca[:-1])[:, None]
             + mvar * ca[-1] * rq)
    return dict(rho=rho, c=c, w=w, cm=cm, logdet=logdet,
                likelihood_id='UNION3_22_PLUS_DESI_QISO_GAUSSIAN_RHO_%+.2f' % rho,
                prior_id='OM_U_%g_%g_AR_U_%g_%g_M_N_%g_%g' %
                         (*tab['om_bounds'], *tab['ar_bounds'], *m_prior),
                log_evidence=logz, weights=weights, mmean=mmean,
                msd=float(np.sqrt(mvar)), ll=ll)


def moments(fit, tab):
    w = fit['weights']
    def stat(x, extra=0.):
        mean = float(np.sum(w * x))
        var = float(np.sum(w * ((x - mean)**2 + extra)))
        return {'mean': mean, 'sd': float(np.sqrt(max(var, 0.)))}
    om = stat(tab['om'][:, None])
    ar = stat(tab['ar'][None, :])
    m = stat(fit['mmean'], fit['msd']**2)
    olo, ohi = tab['om_bounds']; alo, ahi = tab['ar_bounds']
    edge = ((tab['om'] < olo + .01*(ohi-olo)) |
            (tab['om'] > ohi - .01*(ohi-olo)))[:, None]
    edge_ar = ((tab['ar'] < alo + .01*(ahi-alo)) |
               (tab['ar'] > ahi - .01*(ahi-alo)))[None, :]
    return dict(Omega_m=om, H0_rd=ar, M=m,
                edge_prior_mass=float(np.sum(w * (edge | edge_ar))))


def convergence(previous, current):
    out = {}
    for key in ('Omega_m', 'H0_rd', 'M'):
        a, b = previous[key], current[key]
        out[key] = {'mean_delta_over_posterior_sd': abs(a['mean'] - b['mean']) / b['sd'],
                    'sd_relative_delta': abs(a['sd'] - b['sd']) / b['sd']}
    return out


def ppc(data, tab, fit, seed=17411, count=2048):
    rng = np.random.default_rng(seed)
    flat = fit['weights'].ravel()
    k = rng.choice(len(flat), size=count, p=flat)
    oi, ai = np.unravel_index(k, fit['weights'].shape)
    m = rng.normal(fit['mmean'][oi, ai], fit['msd'])
    predicted = np.column_stack([tab['s'][oi] + m[:, None],
                                 tab['qshape'][oi] / tab['ar'][ai]])
    observed = np.r_[data['mu'], data['q']]
    l = np.linalg.cholesky(fit['c'])
    delta = np.linalg.solve(l, (observed - predicted).T).T
    t_observed = np.einsum('ij,ij->i', delta, delta)
    replicate = predicted + rng.standard_normal((count, len(observed))) @ l.T
    drep = np.linalg.solve(l, (replicate - predicted).T).T
    t_rep = np.einsum('ij,ij->i', drep, drep)
    return {'seed': seed, 'replicates': count,
            'chi2_observed_posterior_mean': float(t_observed.mean()),
            'chi2_rep_mean': float(t_rep.mean()),
            'tail_fraction': float(np.mean(t_rep >= t_observed)),
            'target': 'SAME_THETA_M_JOINT_MEASUREMENT_C',
            'interpretation': 'conditional compressed-Gaussian posterior predictive diagnostic'}


def image_and_save(outdir, name, data, tab, fit):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    n = len(tab['om'])
    ids = tuple(f'{name}:o{i:03d}:a{j:03d}' for i in range(n) for j in range(n))
    source = PosteriorDrawSource(name,
        f"Union3:{data['union_sha256']}|{data['desi_source_id']}",
        fit['likelihood_id'], fit['prior_id'], ids,
        tuple(fit['weights'].ravel()), 'FLAT_LCDM_DISTANCE', 'DISTANCE_ONLY')
    source=replace(source,distance_state_sha256=distance_state_digest(source,np.repeat(tab['om'],n),np.tile(tab['ar'],n),Z_IMAGE,np.repeat(tab['image_integrals'],n,axis=0)))
    image = posterior_distance_image(source,
        np.repeat(tab['om'], n), np.tile(tab['ar'], n), redshift=Z_IMAGE,
        radial_integral=np.repeat(tab['image_integrals'], n, axis=0))
    arrays = {key: image[key] for key in ('E', 'q_deceleration', 'H0_DL_over_c',
                                         'H0_DA_over_c', 'DM_over_rd', 'DH_over_rd')}
    np.savez_compressed(outdir / f'{name}.npz', draw_ids=np.asarray(ids),
                        weights=fit['weights'].ravel(), Omega_m=np.repeat(tab['om'], n),
                        H0_rd=np.tile(tab['ar'], n), M_conditional_mean=fit['mmean'].ravel(),
                        M_conditional_sd=np.full(n*n, fit['msd']), redshift=Z_IMAGE,
                        **arrays)
    plt.figure(figsize=(7, 4))
    plt.plot(tab['om'], fit['weights'].sum(axis=1), label='Omega_m node mass')
    plt.xlabel('Omega_m'); plt.ylabel('Posterior node mass')
    plt.title(f'Union3 + DESI qiso, rho={fit["rho"]:+.2f}')
    plt.tight_layout()
    plt.savefig(outdir / f'{name}.png', dpi=160)
    plt.savefig(outdir / f'{name}.pdf')
    plt.close()
    return {'posterior_id': name, 'draw_count': n*n,
            'physical_sector': image['physical_sector'],
            'claim_status': image['claim_status'],
            'npz_sha256': sha(outdir / f'{name}.npz')}


def injections(data, tab, seed=37421):
    rng = np.random.default_rng(seed)
    c, _ = covariance(data, 0.)
    l = np.linalg.cholesky(c)
    states = ((.22, 9000., 42.8), (.32, 12000., 43.0), (.45, 15000., 43.3))
    rows = []
    for om, ar, m in states:
        ii = radial([om], np.r_[data['z'], data['zeff']])[0]
        s = 5 * np.log10((1 + data['z']) * ii[:-1])
        ez = np.sqrt(om * (1 + data['zeff'])**3 + 1 - om)
        q = C_LIGHT / ar / data['fid'] * np.cbrt(data['zeff'] * ii[-1]**2 / ez)
        y = np.r_[s + m, q] + l @ rng.standard_normal(23)
        fit = fit_grid(data, tab, 0., y)
        recovered = moments(fit, tab)
        standardized = {key: abs(value - recovered[key]['mean']) / recovered[key]['sd']
                        for key, value in (('Omega_m', om), ('H0_rd', ar), ('M', m))}
        rows.append({'injected': {'Omega_m': om, 'H0_rd': ar, 'M': m},
                     'recovered': recovered, 'standardized_error': standardized,
                     'recovery_status': ('RECOVERED_WITHIN_3SD'
                         if max(standardized.values()) < 3 else 'RECOVERY_DIAGNOSTIC_FAIL'),
                     'log_normalizer': fit['log_evidence']})
    return {'seed': seed, 'scenario': 'SAME_GAUSSIAN_LAW_SMALL_INJECTION_FIXTURE',
            'catalogue_coverage': 'NOT_EVALUATED', 'rows': rows}


def run(outdir, orders=(128, 256, 512), rhos=RHO):
    if (len(orders) < 2 or tuple(sorted(set(orders))) != tuple(orders)
            or orders[0] < 2 or orders[-1] > 512):
        raise ValueError('strict increasing quadrature orders with hard cap 512 required')
    if len(set(rhos)) != len(rhos) or any(abs(rho) >= 1 for rho in rhos):
        raise ValueError('unique SPD rho sensitivity values required')
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    data = load_inputs()
    by_order = {order: table(order, data) for order in orders}
    result = {'owner': 'HTT', 'scope': 'RB10_RB11_CONDITIONAL_RELEASED_COMPRESSED_GAUSSIAN_SCENARIO',
              'source': {'union_sha256': data['union_sha256'], 'desi_json_sha256': data['desi_sha256'],
                         'desi_source_id': data['desi_source_id']},
              'model': {'geometry': 'FLAT_MATTER_LAMBDA', 'Omega_m_prior': 'Uniform(0.01,0.99)',
                        'H0_rd_prior_km_s': 'Uniform(5000,20000)', 'M_prior_mag': 'Normal(43,5)',
                        'Union3_law': '22-node released compressed Gaussian scenario',
                        'DESI_law': 'published fixed Gaussian qiso syst alternative only',
                        'cross_covariance': 'rho*sigma_q*w, derivative residual orthogonal to offset',
                        'rho_values': list(rhos), 'M_integral': 'analytic, normalized log determinant retained',
                        'CF4': 'NOT_INCORPORATED', 'CMB_product_multiplication': 'NOT_PERFORMED'},
              'scenarios': {}, 'status': 'PENDING_QUADRATURE'}
    for rho in rhos:
        fits = {order: fit_grid(data, by_order[order], rho) for order in orders}
        stats = {order: moments(fits[order], by_order[order]) for order in orders}
        comparisons = {f'{a}_{b}': convergence(stats[a], stats[b])
                       for a, b in zip(orders[:-1], orders[1:])}
        final_order = orders[-1]
        final = fits[final_order]
        name = f'rho_{rho:+.2f}'.replace('+', 'p').replace('-', 'm')
        image = image_and_save(outdir, name, data, by_order[final_order], final)
        converged = all(v < 1e-3 for metric in comparisons[f'{orders[-2]}_{orders[-1]}'].values()
                        for v in metric.values())
        result['scenarios'][name] = {'rho': rho, 'moments': stats[final_order],
                                     'log_normalizer': final['log_evidence'],
                                     'convergence': comparisons, 'quadrature_status':
                                     'PASS' if converged else 'QUADRATURE_UNRESOLVED',
                                     'posterior_image': image,
                                     'PPC': ppc(data, by_order[final_order], final)}
        print(name, result['scenarios'][name]['quadrature_status'], flush=True)
    alt = table(orders[-1], data, (.05, .95), (6000., 18000.))
    result['bounded_proper_prior_sensitivity'] = {
        'prior': 'Omega_m~U(.05,.95), H0rd~U(6000,18000), M~N(43,3)',
        'rho_0_moments': moments(fit_grid(data, alt, 0., m_prior=(43., 3.)), alt)}
    result['injections'] = injections(data, by_order[orders[0]])
    result['status'] = ('CONDITIONAL_SCENARIO_QUADRATURE_PASS'
                        if all(s['quadrature_status'] == 'PASS' for s in result['scenarios'].values())
                        else 'QUADRATURE_UNRESOLVED')
    result['claim_limits'] = ['No raw Union3/DESI catalogue coverage claim',
        'rho is sensitivity, not measured cross-covariance',
        'No CF4 endpoint H to H0 bridge or overlap/calibration law',
        'No Bianchi/native transfer or family identification',
        'No physical MES sector inferred from flat-LCDM distances',
        'No competing model evidence from this single conditional model']
    (outdir / 'result.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    lines = ['# RB10/11 conditional joint distance fit', '',
             f"Status: `{result['status']}`. Union3 22-node compressed Gaussian + DESI BGS qiso.", '',
             'The rho grid is a cross-covariance sensitivity, not a measured covariance.',
             'The DESI syst alternative appears once. The common M offset is integrated once.', '',
             '| rho | Omega_m mean ± SD | H0 rd mean ± SD (km/s) | M mean ± SD | PPC tail | quadrature |',
             '|---:|---:|---:|---:|---:|---|']
    for row in result['scenarios'].values():
        s = row['moments']
        lines.append(f"| {row['rho']:+.2f} | {s['Omega_m']['mean']:.5f} ± {s['Omega_m']['sd']:.5f} | "
                     f"{s['H0_rd']['mean']:.2f} ± {s['H0_rd']['sd']:.2f} | "
                     f"{s['M']['mean']:.4f} ± {s['M']['sd']:.4f} | "
                     f"{row['PPC']['tail_fraction']:.4f} | {row['quadrature_status']} |")
    lines += ['', 'All final posterior node IDs, weights, conditional M laws, and distance images are in the matching NPZ files.',
              'Physical Sigma2, W2, tilt, curvature, x ceiling, x/Q/Pi/F/G are unavailable with unknown mass one.',
              'CF4 and CMB products are not incorporated. Model competition and catalogue coverage remain unavailable.', '']
    (outdir / 'report.md').write_text('\n'.join(lines))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', type=Path, required=True)
    parser.add_argument('--orders', type=int, nargs='+', default=[128, 256, 512])
    args = parser.parse_args()
    run(args.outdir, tuple(args.orders))
