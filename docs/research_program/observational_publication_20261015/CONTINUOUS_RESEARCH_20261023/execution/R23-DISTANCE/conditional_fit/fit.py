"""CONDITIONAL_GLS_V1: authored selected-cohort Gaussian experiment.

The fixed design and group partition condition on the observed 628 marks. This
is not a physical CF4 calibration, peculiar-velocity model, or parent selection
law. Only the 274 released moduli are Gaussian coordinates.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import integrate, stats
from scipy.linalg import solve_triangular

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
LEDGER = Path('/mnt/extdrive/workdir/htt_open_data/cf4/D02_HI_CF4_20261018/TARGET_JOIN_AND_OOF.csv')
RELEASED = PARENT / 'RELEASED_ROWS.csv'
CONTRACT = HERE / 'CONTRACT.json'
SOURCE_SHA = {
    LEDGER: 'c32885cd2f081ec1bcedfcb98ef18c8c53245c12ac4a5fabb64d68b27a75f48d',
    Path('/mnt/extdrive/workdir/htt_open_data/cf4/upstream_20261018/ReadMe'): '45fa3cca5346aff29bcf9785e7b08e8ab34b1d67e80b359c0d28bdbd18e42581',
    Path('/mnt/extdrive/workdir/htt_open_data/cf4/upstream_20261018/table1.dat'): 'ac679ab4548484b02dc17a1cc09bbe8f0a68f45bd5c44efc7302fcabc32d8926',
    Path('/mnt/extdrive/workdir/htt_open_data/cf4/upstream_20261018/table4.dat'): 'f4aa0ba0efe7d7a14f044a76ef37f5a033e2788923d586c2d15ed248939455f2',
    RELEASED: 'c7912bd7dd983cdcdf47408a89da9f2b76887a0cc37fd9b5a9a8e83e03d3fe20',
    PARENT / 'ARTIFACT_MANIFEST.json': '81182b06669521121ec386111ac669083c4e325c714c7f69322fda75d2034f90',
    PARENT / 'REPORT.md': '44247351b4709e80bfb8b8840d5cd701eb6264e39ba4a32048e3f92b4ba1ba11',
    CONTRACT: 'e0fc0047e27a7bdc71b8af121820d0948941c673c48cc5cfb8a8add227640cdd',
}
OUTCOMES = ('accepted', 'other_quality', 'confused', 'nondetection')
NAMES = ('intercept_mag', 'log_vcmb_mag_per_dex', 'measured_width_mag_per_dex',
         'width_error_mag_per_dex', 'other_quality_mag', 'confused_mag', 'nondetection_mag')


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def load_inputs():
    for path, expected in SOURCE_SHA.items():
        observed = sha256(path)
        if observed != expected:
            raise ValueError(f'immutable input SHA mismatch {path}: {observed} != {expected}')
    ledger = list(csv.DictReader(LEDGER.open(newline='')))
    rows = list(csv.DictReader(RELEASED.open(newline='')))
    ids = [r['pgc'] for r in ledger]
    if len(ids) != 628 or len(set(ids)) != 628 or len(rows) != 274:
        raise ValueError('selected/released size or unique PGC changed')
    by_id = {r['pgc']: r for r in ledger}
    present = {r['pgc'] for r in rows}
    if len(present) != 274 or not present.issubset(by_id):
        raise ValueError('released PGC join is not unique/subset')
    counts = [[sum(r['outcome'] == o and r['pgc'] not in present for r in ledger),
               sum(r['outcome'] == o and r['pgc'] in present for r in ledger)] for o in OUTCOMES]
    if counts != [[116,269],[21,1],[26,3],[191,1]]:
        raise ValueError('selected outcome/availability marks changed')
    groups_all = {}
    for row in ledger:
        raw = row['CF4_group']
        groups_all[row['pgc']] = f'CF4:{raw}' if raw else f'UNASSIGNED_PGC:{row["pgc"]}'
    for row in rows:
        source = by_id[row['pgc']]
        if row['outcome'] != source['outcome'] or row['group_label'] != (source['CF4_group'] or 'UNASSIGNED'):
            raise ValueError(f'released/ledger mark or group mismatch PGC {row["pgc"]}')
    names = [groups_all[r['pgc']] for r in rows]
    group_counts = Counter(names)
    if (len(group_counts), sum(v == 1 for v in group_counts.values()),
        sum(v == 2 for v in group_counts.values())) != (269,264,5):
        raise ValueError('observed group structure changed')
    return ledger, rows, groups_all, counts


def make_model(rows, groups_all):
    n = len(rows)
    y = np.array([float(r['DMbest_mag']) for r in rows])
    s = np.array([float(r['e_DMbest_mag']) for r in rows])
    v = np.array([float(r['vcmb_km_s']) for r in rows])
    width = np.array([float(r['logWmxi']) for r in rows])
    ew = np.array([float(r['e_logWmxi']) for r in rows])
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(s)) and np.all(s > 0)
            and np.all(np.isfinite(v)) and np.all(v > 0) and np.all(np.isfinite(width))
            and np.all(np.isfinite(ew)) and np.all(ew > 0)):
        raise ValueError('invalid released observed value/covariate/error')
    lv = np.log10(v)
    X = np.column_stack((np.ones(n), lv-lv.mean(), width-width.mean(), ew-ew.mean(),
                         *[(np.array([r['outcome'] == o for r in rows], dtype=float))
                           for o in OUTCOMES[1:]]))
    if np.linalg.matrix_rank(X) != 7 or n-X.shape[1] != 267:
        raise ValueError('design rank or residual degrees of freedom changed')
    a = 0.5 * s.min()
    b = float(np.median(s))
    labels = list(dict.fromkeys(groups_all[r['pgc']] for r in rows))
    index = {g: j for j, g in enumerate(labels)}
    G = np.zeros((n, len(labels)))
    for i, r in enumerate(rows):
        G[i, index[groups_all[r['pgc']]]] = 1.0
    d = s*s-a*a
    if np.any(d < .75*s*s - 1e-14):
        raise ValueError('calibration reallocation exceeds 25 percent variance')
    V = np.diag(d) + a*a*np.ones((n,n)) + b*b*(G@G.T)
    if not np.allclose(np.diag(V)-b*b, s*s, rtol=1e-12, atol=1e-14):
        raise ValueError('common calibration reallocation failed')
    L = np.linalg.cholesky(V)
    if np.any(~np.isfinite(np.diag(L))) or np.any(np.diag(L) <= 0):
        raise ValueError('nonpositive or nonfinite Cholesky pivot')
    Xw = solve_triangular(L, X, lower=True, check_finite=False)
    Q, R = np.linalg.qr(Xw, mode='reduced')
    if np.linalg.matrix_rank(R) != 7:
        raise ValueError('whitened design lost rank')
    Rinv = solve_triangular(R, np.eye(7), lower=False, check_finite=False)
    A = Rinv @ Rinv.T
    h = np.sum(Q*Q, axis=1)
    return dict(y=y,s=s,v=v,width=width,ew=ew,X=X,V=V,L=L,G=G,d=d,a=a,b=b,
                Xw=Xw,Q=Q,R=R,A=A,h=h,labels=labels)


def fit(model, y):
    """Fit one or many response columns using the same single total V."""
    Y = np.asarray(y, dtype=float)
    if Y.ndim == 1:
        Y = Y[:,None]
    yw = solve_triangular(model['L'], Y, lower=True, check_finite=False)
    beta = solve_triangular(model['R'], model['Q'].T @ yw, lower=False, check_finite=False)
    rw = yw-model['Xw']@beta
    rss = np.sum(rw*rw, axis=0)
    if np.any(~np.isfinite(rss)) or np.any(rss <= 0):
        raise ValueError('nonfinite/nonpositive residual sum of squares')
    s2 = rss/267
    delta = .1*beta[2]
    se = .1*np.sqrt(s2*model['A'][2,2])
    tcrit = stats.t.ppf(.975,267)
    diagnostic_mask=(1-model['h'])>1e-12
    if not np.any(diagnostic_mask):
        raise ValueError('no nonzero residual leverage coordinates')
    T = np.max(np.abs(rw[diagnostic_mask])/(np.sqrt(s2)[None,:]*
               np.sqrt(1-model['h'][diagnostic_mask])[:,None]),axis=0)
    return dict(beta=beta,rw=rw,rss=rss,s2=s2,delta=delta,se=se,
                lo=delta-tcrit*se,hi=delta+tcrit*se,T=T)


def validate_math(model, actual):
    # Whitened normal equation, exact intercept shift, and independent dense fixtures.
    normal = np.linalg.norm(model['Xw'].T @ actual['rw'][:,0])
    scale = max(1.0,np.linalg.norm(model['Xw'])*np.linalg.norm(
        solve_triangular(model['L'], model['y'], lower=True, check_finite=False)))
    if normal > 1e-10*scale:
        raise ValueError(f'whitened normal equation failed: {normal}/{scale}')
    shifted = fit(model,model['y']+1)
    if not (np.allclose(shifted['beta'][:,0]-actual['beta'][:,0],
                        [1,0,0,0,0,0,0],rtol=1e-10,atol=1e-10)
            and np.allclose(shifted['rw'],actual['rw'],rtol=1e-10,atol=1e-10)):
        raise ValueError('additive zero-point invariance failed')
    if not np.allclose(np.diag(model['V'])-model['b']**2,model['s']**2,rtol=1e-12,atol=1e-14):
        raise ValueError('calibration common budget double-counted')
    q2=np.array([[.13,.035],[.035,.19]])
    z2=np.array([.2,-.3]); m2=np.array([.1,.05]); l2=np.linalg.cholesky(q2)
    r2=solve_triangular(l2,z2-m2,lower=True)
    log2=-.5*(2*math.log(2*math.pi)+2*np.log(np.diag(l2)).sum()+r2@r2)
    if abs(log2-stats.multivariate_normal.logpdf(z2,mean=m2,cov=q2))>1e-10:
        raise ValueError('correlated Gaussian fixture failed')
    # Independent dense determinant and quadratic form for a small principal block.
    v3=model['V'][:3,:3]; z3=model['y'][:3]-model['X'][:3]@actual['beta'][:,0]
    l3=np.linalg.cholesky(v3); w3=solve_triangular(l3,z3,lower=True)
    sign,ld=np.linalg.slogdet(v3)
    if sign!=1 or not np.allclose(w3@w3,np.linalg.solve(v3,z3)@z3,rtol=1e-10,atol=1e-12) or abs(2*np.log(np.diag(l3)).sum()-ld)>1e-10:
        raise ValueError('dense covariance reference failed')
    # 1D normalization. The two excluded tails total < 1.3e-15.
    integral,error=integrate.quad(stats.norm.pdf,-8,8,epsabs=1e-12)
    if abs(integral-1)>1e-10 or error>1e-10 or 2*stats.norm.sf(8)>=1.3e-15:
        raise ValueError('Gaussian normalization fixture failed')
    return {'normal_equation_norm':float(normal),'normal_equation_limit':float(1e-10*scale),
            'one_dimensional_integral_pm8':integral,'one_dimensional_quad_error':error,
            'excluded_tail_bound':float(2*stats.norm.sf(8)),
            'two_row_logpdf_difference':float(log2-stats.multivariate_normal.logpdf(z2,mean=m2,cov=q2)),
            'intercept_shift_mag':float(shifted['beta'][0,0]-actual['beta'][0,0]),
            'dense_three_row_reference':'PASS', 'cholesky_normalization':'274 standard normals after z=L^-1(y-Xbeta)/sigma; Jacobian sigma^274 det(L) cancels'}


def run(seed=2026102302,mocks=4096):
    if seed!=2026102302 or mocks!=4096:
        raise ValueError('frozen seed/mock count changed')
    ledger,rows,groups_all,counts=load_inputs()
    m=make_model(rows,groups_all)
    actual=fit(m,m['y'])
    math_checks=validate_math(m,actual)
    rng=np.random.default_rng(seed)
    # Draw one common calibration and one latent value for every group in the
    # full selected cohort, then observe only the 274 released coordinates.
    all_groups=list(dict.fromkeys(groups_all[r['pgc']] for r in ledger))
    all_index={g:j for j,g in enumerate(all_groups)}
    observed_group_idx=np.array([all_index[groups_all[r['pgc']]] for r in rows])
    eps=rng.standard_normal((274,mocks))*np.sqrt(m['d'])[:,None]
    cal=rng.standard_normal(mocks)
    group=rng.standard_normal((len(all_groups),mocks))
    beta0=np.array([34.,5.,0.,0.,0.,0.,0.])
    Y=m['X']@beta0[:,None]+eps+m['a']*cal[None,:]+m['b']*group[observed_group_idx,:]
    mock=fit(m,Y)
    covered=(mock['lo']<=0)&(mock['hi']>=0)
    cover_count=int(np.sum(covered))
    lower=int(stats.binom.ppf(.005,mocks,.95)); upper=int(stats.binom.ppf(.995,mocks,.95))
    mock_T=mock['T']
    actual_T=float(actual['T'][0]); exceed=int(np.sum(mock_T>=actual_T))
    p=(1+exceed)/(mocks+1)
    residual=m['y']-m['X']@actual['beta'][:,0]
    sigma_ml2=float(actual['rss'][0]/274)
    logdet=float(2*np.log(np.diag(m['L'])).sum())
    loglike=-.5*(274*math.log(2*math.pi)+274*math.log(sigma_ml2)+logdet+274)
    result={
      'contract':'CONDITIONAL_GLS_V1','owner':'htt','claim_tier':'C0_AUTHORED_CONDITIONAL_DIAGNOSTIC',
      'transfer_source':'none','selected_count':628,'released_count':274,'undefined_distance_count':354,
      'undefined_distance_fraction':354/628,'outcome_by_missing_present':counts,
      'mark_only_descriptive_log_score':-834.3958584571346,
      'conditional_distance_log_likelihood_at_ml':loglike,
      'conditioned_on':'actual selected 628, all realized marks, released measured widths/errors and Vcmb, declared full selected group partition',
      'group_structure':{'observed_groups':len(m['labels']),'observed_singletons':264,'observed_pairs':5,'full_selected_groups':len(all_groups)},
      'covariance':{'a_common_mag':float(m['a']),'b_group_mag':float(m['b']),
                    'V_diagonal_min_mag2':float(np.diag(m['V']).min()),
                    'min_cholesky_pivot':float(np.diag(m['L']).min()),
                    'logdet_V':logdet,
                    'allocation':'diag(s_i^2-a^2)+a^2 11T+b^2 GGT; one total covariance; authored working allocation, not source empirical PV/calibration'},
      'fit':{'coefficient_names':NAMES,'coefficients':actual['beta'][:,0].tolist(),
             'delta_width_0p1_dex_mag':float(actual['delta'][0]),
             'delta_se_mag':float(actual['se'][0]),
             'delta_t95_interval_mag':[float(actual['lo'][0]),float(actual['hi'][0])],
             'rss_whitened':float(actual['rss'][0]),'nu':267,
             'residual_scale_unbiased_s2':float(actual['s2'][0]),
             'sigma_ml2':sigma_ml2},
      'mock':{'seed':seed,'B':mocks,'beta0':beta0.tolist(),'sigma0':1,
              'covered':cover_count,'nominal':.95,'acceptance_count_range':[lower,upper],
              'conditional_coverage_check':'PASS' if lower<=cover_count<=upper else 'FAIL',
              'binomial_exact_95_interval':list(map(float,stats.binomtest(cover_count,mocks).proportion_ci(.95,method='exact'))),
              'draw':'one common scalar, one scalar per full selected group, independent residuals; fixed marks and covariates; no distances drawn for 354 missing'},
      'diagnostic':{'T_actual':actual_T,'mock_exceedance_count':exceed,'p_plus_one':p,
                    'conditional_law_criticized':p<.01,
                    'T_mock_quantiles':np.quantile(mock_T,[.5,.9,.95,.99]).tolist(),
                    'zero_residual_leverage_PGCs':[rows[i]['pgc'] for i in range(274) if 1-m['h'][i]<=1e-12],
                    'zero_residual_leverage_count':int(np.sum(1-m['h']<=1e-12))},
      'math_checks':math_checks,'physical_admission':'HOLD','H02_S02':'HOLD',
      'physical_selection_and_joint_calibration_PV':'NOT_EVALUABLE',
      'unrestricted_common_zero_point':'width contrast invariant for every real additive common delta; no physical bound',
      'limitations':['authored conditional covariance allocation','actual cross-row calibration/PV covariance unavailable',
                     '354 undefined distances not imputed','parent inclusion law unknown','mock coverage is only under generated law']}
    with (HERE/'ROWS.csv').open('w',newline='') as f:
        fieldnames=['pgc','outcome','group_id','DMbest_mag','fitted_mean_mag','residual_mag','whitened_residual','e_DMbest_mag','logWmxi','e_logWmxi','vcmb_km_s']
        w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader()
        for i,r in enumerate(rows):
            w.writerow({'pgc':r['pgc'],'outcome':r['outcome'],'group_id':groups_all[r['pgc']],
                        'DMbest_mag':r['DMbest_mag'],'fitted_mean_mag':float((m['X']@actual['beta'][:,0])[i]),
                        'residual_mag':float(residual[i]),'whitened_residual':float(actual['rw'][i,0]),
                        'e_DMbest_mag':r['e_DMbest_mag'],'logWmxi':r['logWmxi'],
                        'e_logWmxi':r['e_logWmxi'],'vcmb_km_s':r['vcmb_km_s']})
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,default=2026102302)
    parser.add_argument('--mocks',type=int,default=4096)
    args=parser.parse_args()
    print(json.dumps(run(args.seed,args.mocks),indent=2))
