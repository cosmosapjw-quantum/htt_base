#!/usr/bin/env python3
"""Reusable fixed-cohort Gaia operator geometry, without repository imports.

Only NumPy is needed for numerical output; Matplotlib is optional with --no-plots.
Raw M maps mas/year tangent biases to mas/year six-parameter shifts. K maps
one total whitened vector to the same shifts. This does not infer physical budgets.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np

NAMES = ['spin_x', 'spin_y', 'spin_z', 'glide_x', 'glide_y', 'glide_z']
FROZEN_INPUT_SHA = 'd5384f57138f4e8ea7b986153bf0133f846e9f7806bdf82b2cb7ac4d6a676c9f'
FROZEN_BASELINE_SHA = '7af1f6b3508826b69f7170891146536398104779962de76d9d4355c8b9e4415d'
UPSTREAM = '89621f4c9a6f63449813587a0fadeb13287f8e10'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite_array(value, name):
    if np.iscomplexobj(value):
        raise ValueError(f'{name} must be real')
    a = np.asarray(value, dtype=float)
    if not np.isfinite(a).all():
        raise ValueError(f'{name} must be finite')
    return a


def nonnegative(value, name):
    a = finite_array(value, name)
    if a.ndim or a < 0:
        raise ValueError(f'{name} must be a finite nonnegative scalar')
    return float(a)


def validate_operator(m, k, covariance, source_id):
    m = finite_array(m, 'M')
    k = finite_array(k, 'K')
    v = finite_array(covariance, 'covariance')
    ids = np.asarray(source_id)
    if m.ndim != 3 or m.shape[0] != 6 or m.shape[2] != 2 or m.shape[1] < 3:
        raise ValueError('M must have shape (6,N,2), N>=3')
    if k.shape != (6, 2 * m.shape[1]) or v.shape != (6, 6):
        raise ValueError('K or covariance shape mismatch')
    if ids.shape != (m.shape[1],) or ids.dtype.kind not in 'iu' or len(np.unique(ids)) != len(ids):
        raise ValueError('source_id must be distinct aligned integer IDs')
    if not np.allclose(v, v.T, rtol=1e-12, atol=0):
        raise ValueError('covariance must be symmetric')
    try:
        np.linalg.cholesky(v)
    except np.linalg.LinAlgError as exc:
        raise ValueError('covariance must be positive definite; no floor applied') from exc
    parity = float(np.linalg.norm(k @ k.T-v)/np.linalg.norm(v))
    if parity > 1e-10:
        raise ValueError('K K^T must equal covariance within 1e-10 relative norm')
    return m, k, v, ids, parity


def directions(value):
    u = finite_array(value, 'directions')
    if u.ndim == 1:
        u = u[None, :]
    if u.ndim != 2 or u.shape[1] != 6:
        raise ValueError('directions must have shape (D,6)')
    return u


def disk_support(m, u, bbar_mas):
    """Exact h(u)=bbar sum_i ||M_i^T u||2; not a coordinate box."""
    bbar = nonnegative(bbar_mas, 'bbar_mas')
    u = directions(u)
    return bbar * np.linalg.norm(np.einsum('dj,jna->dna', u, m), axis=2).sum(axis=1)


def box_support(m, u, bbar_mas):
    bbar = nonnegative(bbar_mas, 'bbar_mas')
    return bbar * np.abs(np.einsum('dj,jna->dna', directions(u), m)).sum(axis=(1, 2))


def disk_witness(m, u, bbar_mas):
    """Each nonzero block uses b_i=bbar M_i^T u / ||M_i^T u||2."""
    bbar = nonnegative(bbar_mas, 'bbar_mas')
    u = directions(u)
    if len(u) != 1:
        raise ValueError('witness takes exactly one direction')
    q = np.einsum('j,jna->na', u[0], m)
    norms = np.linalg.norm(q, axis=1)
    return bbar * np.divide(q, norms[:, None], out=np.zeros_like(q), where=norms[:, None] > 0)


def chi2_6_cdf(x):
    """Closed CDF for even df=6: 1-exp(-x/2)(1+x/2+x^2/8)."""
    x = nonnegative(x, 'chi-square coordinate')
    t = x / 2
    return 1-math.exp(-t)*(1+t+t*t/2)


def chi2_6_quantile(probability):
    p = float(probability)
    if not math.isfinite(p) or not 0 < p < 1:
        raise ValueError('probability must be in (0,1)')
    lo, hi = 0., 1.
    while chi2_6_cdf(hi) < p:
        hi *= 2
    for _ in range(100):
        mid = (lo+hi)/2
        if chi2_6_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2


def ellipsoid_witness(k, v, delta):
    """Minimum norm preimage z=K^T V^-1 delta, exact since KK^T=V."""
    delta = finite_array(delta, 'delta')
    if delta.shape != (6,):
        raise ValueError('delta must have shape (6,)')
    return k.T @ np.linalg.solve(v, delta)


def rotation_checks(m, u, bbar, rng):
    theta = rng.uniform(-np.pi, np.pi, m.shape[1])
    r = np.empty((m.shape[1], 2, 2))
    r[:, 0, 0] = r[:, 1, 1] = np.cos(theta)
    r[:, 0, 1] = -np.sin(theta)
    r[:, 1, 0] = np.sin(theta)
    rotated = np.einsum('jna,nab->jnb', m, r)
    before, after = disk_support(m, u, bbar), disk_support(rotated, u, bbar)
    witness = disk_witness(m, u[0], bbar)
    transformed = np.einsum('nab,na->nb', r, witness)
    shift = np.einsum('jna,na->j', m, witness)
    rotated_shift = np.einsum('jna,na->j', rotated, transformed)
    return {'independent_source_rotations': int(len(theta)),
            'support_max_abs_mas_year': float(np.max(np.abs(before-after))),
            'witness_shift_max_abs_mas_year': float(np.max(np.abs(shift-rotated_shift))),
            'box_changed_max_abs_microas_year': float(1000*np.max(np.abs(box_support(m,u,bbar)-box_support(rotated,u,bbar))))}


def coverage_stress(reps, seed, q, rho_grid):
    if isinstance(reps, bool) or not isinstance(reps, (int,np.integer)) or not 0 <= reps <= 50000:
        raise ValueError('MC repetitions must be integer between 0 and 50000')
    if reps == 0:
        return {'repetitions': 0, 'status': 'disabled'}
    rng = np.random.default_rng(seed)
    eps = rng.normal(size=(reps, 6))
    rows = []
    for rho in rho_grid:
        rho = nonnegative(rho, 'rho')
        # A known fixed maximal shift in whitened parameter space; direction is
        # irrelevant to the isotropic reference distribution.
        shifted = eps.copy()
        shifted[:,0] += rho
        lengths = np.linalg.norm(shifted, axis=1)
        rate = float(np.mean(lengths <= q+rho))
        rows.append({'known_fixed_bias_mahalanobis_norm': rho,
                     'unexpanded_q_region_coverage': float(np.mean(lengths <= q)),
                     'expanded_q_plus_rho_region_coverage': rate,
                     'expanded_binomial_standard_error': math.sqrt(rate*(1-rate)/reps),
                     'analytic_uniform_lower_bound': .95})
    return {'repetitions': int(reps), 'seed': int(seed),
            'status': 'synthetic_known_law_stress_only_not_empirical_Gaia_coverage', 'rows': rows}


def make_plots(out, m, v, coeff, result, bbar):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    labels = [n.replace('_',' ') for n in NAMES]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    ix = np.arange(6)
    axes[0].bar(ix-.18,result['disk']['component_support_microas_year'],.36,label='Per-source Euclidean disk')
    axes[0].bar(ix+.18,result['disk']['raw_coordinate_box_component_support_microas_year'],.36,label='Raw coordinate box')
    axes[0].set(ylabel='Directional support [microas/year]', title=f'Different bias sets at {1000*bbar:g} microas/year')
    axes[0].set_xticks(ix,labels,rotation=35,ha='right')
    axes[0].legend(fontsize=8)
    sigma=np.sqrt(np.diag(v))*1000
    q=result['simultaneous_gaussian']['central_radius']
    for offset, factor, name, color in [(-.2,1.959963984540054,'Marginal Gaussian 95%', 'C0'),(0,q,'Joint six-parameter 95%, rho=0','C1'),(.2,q+1,'Joint robust region, rho=1','C2')]:
        axes[1].errorbar(ix+offset,1000*coeff,yerr=factor*sigma,fmt='o',capsize=3,label=name,color=color,markersize=3)
    axes[1].axhline(0,color='black',linewidth=.6)
    axes[1].set(ylabel='Coefficient and projection interval [microas/year]',title='Conditional fixed-cohort Gaussian proxy')
    axes[1].set_xticks(ix,labels,rotation=35,ha='right')
    axes[1].legend(fontsize=8)
    fig.text(.5,.01,'HTT | DESCRIPTIVE_CONDITIONAL | exploratory operator application | transfer: N/A | saved block-independent covariance | synthetic null only | no physical Gaia coverage or geometry claim',ha='center',fontsize=6)
    fig.tight_layout(rect=(0,.04,1,1))
    for ext in ['svg','png']:
        fig.savefig(out/f'operator_geometry.{ext}',dpi=180)
    plt.close(fig)
    theta=np.linspace(0,2*np.pi,361)
    u=np.zeros((len(theta),6));u[:,0]=np.cos(theta);u[:,2]=np.sin(theta)
    fig,ax=plt.subplots(figsize=(7,4))
    ax.plot(theta*180/np.pi,1000*disk_support(m,u,bbar),label='Euclidean disk support')
    ax.plot(theta*180/np.pi,1000*box_support(m,u,bbar),label='Raw coordinate box support')
    ax.plot(theta*180/np.pi,1000*(q+1)*np.sqrt(np.einsum('di,ij,dj->d',u,v,u)),label='Simultaneous Gaussian + rho=1')
    ax.set(xlabel='Direction angle: spin x to spin z [degrees]',ylabel='Support / projection halfwidth [microas/year]',title='Support is a function of parameter direction')
    ax.grid(alpha=.25);ax.legend(fontsize=8)
    fig.text(.5,.01,'HTT | DESCRIPTIVE_CONDITIONAL | exploratory | transfer: N/A | block-independent proxy | synthetic null only | no physical coverage/geometry claim',ha='center',fontsize=5.5)
    fig.tight_layout(rect=(0,.04,1,1))
    for ext in ['svg','png']:
        fig.savefig(out/f'directional_support.{ext}',dpi=180)
    plt.close(fig)


def run(args):
    actual_input, actual_baseline = sha256(args.input), sha256(args.baseline)
    if actual_input != args.expected_input_sha or actual_baseline != args.expected_baseline_sha:
        raise ValueError('input or baseline SHA256 differs from explicit expected identity')
    with np.load(args.input, allow_pickle=False) as d:
        m,k,v,ids,parity=validate_operator(d['M'],d['K'],d['covariance'],d['source_id'])
    baseline=json.loads(Path(args.baseline).read_text())
    if baseline['coefficient_order'] != NAMES:
        raise ValueError('baseline coefficient order mismatch')
    if baseline.get('units') != 'coefficients/supports mas/year internally; displayed widths microas/year':
        raise ValueError('baseline units must explicitly identify mas/year internal coordinates')
    coeff=finite_array(baseline['coefficients_mas_year'],'coefficients')
    if coeff.shape != (6,):
        raise ValueError('six baseline coefficients required')
    saved_v=finite_array(baseline['sampling_covariance_mas2_year2'],'baseline covariance')
    if saved_v.shape != (6,6) or not np.allclose(v,saved_v,rtol=1e-10,atol=1e-15):
        raise ValueError('baseline covariance and operator covariance differ')
    bbar=nonnegative(args.bbar_microas,'bbar_microas')/1000
    rng=np.random.default_rng(args.seed)
    random_u=rng.normal(size=(128,6));random_u/=np.linalg.norm(random_u,axis=1)[:,None]
    u=np.vstack([np.eye(6),random_u])
    witness_errors=[];norm_excess=[]
    for direction in u:
        witness=disk_witness(m,direction,bbar)
        shift=np.einsum('jna,na->j',m,witness)
        witness_errors.append(abs(direction@shift-disk_support(m,direction,bbar)[0]))
        norm_excess.append(max(0.,float(np.max(np.linalg.norm(witness,axis=1)))-bbar))
    rotations=rotation_checks(m,u,bbar,rng)
    q=math.sqrt(chi2_6_quantile(.95));l=np.linalg.cholesky(v)
    distance=float(np.linalg.norm(np.linalg.solve(l,coeff)))
    rho_grid=[0.,.1,.25,.5,1.,2.,4.,8.]
    sigma=np.sqrt(np.diag(v))
    ellipsoid_errors=[];ellipsoid_norm_errors=[]
    # Arbitrary parameter-space boundary points, including all coordinate axes
    # in whitened space, must possess a preimage of precisely the same norm.
    for whitened in u:
        delta=l@whitened
        z=ellipsoid_witness(k,v,delta)
        ellipsoid_errors.append(float(np.linalg.norm(k@z-delta)))
        ellipsoid_norm_errors.append(abs(float(np.linalg.norm(z))-float(np.linalg.norm(whitened))))
    checks={'KKT_relative_error':parity,'disk_witness_max_abs_mas_year':max(witness_errors),
            'disk_witness_max_budget_excess_mas_year':max(norm_excess),
            'ellipsoid_preimage_max_abs_mas_year':max(ellipsoid_errors),
            'ellipsoid_preimage_norm_max_abs':max(ellipsoid_norm_errors),
            'rotation':rotations}
    if max(witness_errors)>1e-12 or max(norm_excess)>1e-12 or rotations['support_max_abs_mas_year']>1e-12 or rotations['witness_shift_max_abs_mas_year']>1e-12 or max(ellipsoid_errors)>1e-12 or max(ellipsoid_norm_errors)>1e-10:
        raise AssertionError('geometry validation failed')
    out=Path(args.output)
    if out.exists():
        raise ValueError('fresh output directory required')
    result={'task':'GAIA_FIXED_COHORT_BASIS_INVARIANT_AND_SIMULTANEOUS_GEOMETRY',
        'owner':'HTT','scope':'new operator application and numerical validation of standard convex/Gaussian identities',
        'claim_tier':'DESCRIPTIVE_CONDITIONAL','transfer_source':'not_applicable_observational_linear_operator',
        'upstream_commit':args.upstream_sha,
        'generating_procedure':'NumPy block operator supports, constructive witnesses, independent tangent rotations, analytical chi2_6 CDF inversion, optional fixed-law Monte Carlo',
        'generating_command':[sys.executable,str(Path(__file__).resolve()),'--input',str(args.input),'--baseline',str(args.baseline),'--output',str(args.output),'--bbar-microas',str(args.bbar_microas),'--seed',str(args.seed),'--mc-reps',str(args.mc_reps),'--expected-input-sha',args.expected_input_sha,'--expected-baseline-sha',args.expected_baseline_sha,'--upstream-sha',args.upstream_sha]+(['--no-plots'] if args.no_plots else []),
        'runtime':{'python':sys.version.split()[0],'numpy':np.__version__},
        'configuration':{'seed':args.seed,'mc_repetitions':args.mc_reps,'random_directions':128,'tangent_rotations':int(len(ids))},
        'source':{'operator_sha256':actual_input,'baseline_sha256':actual_baseline,
                  'source_release':baseline['source']['source_release'],'source_row_identity':baseline['source']['source_rows_csv_sha256']},
        'cohort_count':int(len(ids)),'coefficient_order':NAMES,'coefficients_microas_year':(1000*coeff).tolist(),
        'sky_support_status':'fixed upstream selected cohort; no direction-error model',
        'null_mock_status':'synthetic fixed Gaussian law stress only; empirical Gaia null unavailable',
        'units':'M dimensionless; K/coefficients internal mas/year; V mas^2/year^2; displayed supports microas/year',
        'disk':{'per_source_budget_microas_year':1000*bbar,
                'definition':'each physical tangent vector ||b_i||_2 <= bbar',
                'component_support_microas_year':(1000*disk_support(m,np.eye(6),bbar)).tolist(),
                'raw_coordinate_box_component_support_microas_year':(1000*box_support(m,np.eye(6),bbar)).tolist(),
                'disk_to_box_component_ratio':(disk_support(m,np.eye(6),bbar)/box_support(m,np.eye(6),bbar)).tolist() if bbar else None,
                'comparison':'different sets: disk is contained in chosen same-number coordinate box; no same-assumptions improvement claim',
                'direction_vectors':u.tolist(),'direction_support_microas_year':(1000*disk_support(m,u,bbar)).tolist()},
        'simultaneous_gaussian':{'confidence_probability':.95,'degrees_of_freedom':6,'chi2_quantile':q*q,'central_radius':q,
                'bias_budget':'one total whitened observation norm ||z||_2 <= rho, not RMS or per-source',
                'exact_bias_image':'delta^T V^-1 delta <= rho^2, because K K^T=V',
                'confidence_region':'(beta_hat-beta)^T V^-1 (beta_hat-beta) <= (q+rho)^2',
                'coverage_warrant':'exact 0.95 at rho=0 under the stated Gaussian law; at least 0.95 uniformly over admissible fixed biases for rho>0, generally conservative',
                'sampling_sigma_microas_year':(1000*sigma).tolist(),
                'marginal_95_projection_halfwidth_microas_year':(1000*1.959963984540054*sigma).tolist(),
                'rho_grid':rho_grid,'joint_projection_halfwidth_microas_year':(1000*np.outer(q+np.array(rho_grid),sigma)).tolist(),
                'joint_to_marginal_width_ratio_rho0':q/1.959963984540054,
                'coefficient_mahalanobis_distance':distance,
                'zero_contained_at_each_rho':[bool(distance <= q+r) for r in rho_grid],
                'smallest_rho_for_zero_containment':max(0.,distance-q),
                'interpretation':'conditional fixed-selected-cohort Gaussian proxy; not physical Gaia p-value or empirical coverage'},
        'numerical_checks':checks,'monte_carlo':coverage_stress(args.mc_reps,args.seed+1,q,[0.,1.,2.,4.]),
        'caveats':['Upstream cohort selection is outcome-dependent; conditioning does not repair selection bias.',
                   'Cross-source covariance is unavailable; V represents the saved block-independent covariance proxy.',
                   'Direction errors and physical bounds on bbar/rho are unavailable.',
                   'Standard support, ellipsoid-image and chi-square identities are not novel theorems.',
                   'No native solver, ODE, Bianchi family identification, or CAS07/Jacobi/MES bound is supplied.']}
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if not args.no_plots:
        make_plots(out,m,v,coeff,result,bbar)
    return result


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--baseline',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--expected-input-sha',default=FROZEN_INPUT_SHA)
    p.add_argument('--expected-baseline-sha',default=FROZEN_BASELINE_SHA)
    p.add_argument('--upstream-sha',default=UPSTREAM)
    p.add_argument('--bbar-microas',type=float,default=10.)
    p.add_argument('--seed',type=int,default=20261014)
    p.add_argument('--mc-reps',type=int,default=20000)
    p.add_argument('--no-plots',action='store_true')
    return p


if __name__ == '__main__':
    result=run(parser().parse_args())
    print(json.dumps({'cohort_count':result['cohort_count'],'checks':result['numerical_checks'],
                     'central_radius':result['simultaneous_gaussian']['central_radius'],
                     'coefficient_mahalanobis_distance':result['simultaneous_gaussian']['coefficient_mahalanobis_distance']},indent=2))
