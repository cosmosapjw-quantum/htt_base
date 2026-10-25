"""Independent bounded R6 checks. Reads carriers; imports no author functions.

Runs no catalogue analysis, ODE, Boltzmann solver, or map fit. Writes no files.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.optimize import brentq
from scipy.stats import chi2
from fractions import Fraction as F

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'sources/H03_SOURCE_TOMOGRAPHY.json'
j = json.loads(source.read_text())
wins = j['monopole_dipole_STF2_windows']
select = np.array([9*w + a for w in range(4) for a in (1, 2, 3)])
other = np.array([a for a in range(36) if a not in select])
cov36 = np.array(j['joint_covariance_36x36'])
y36 = np.concatenate([w['theta9'] for w in wins])
cov = cov36[np.ix_(select, select)]
y = y36[select]
response36 = np.vstack([w['bulk_velocity_design_response_9x3_per_Mpc'] for w in wins])
response = response36[select]
constant = np.tile(np.eye(3), (4, 1))
constant36 = np.zeros((36, 3)); constant36[select] = constant
nuisance36 = np.eye(36)[:, other]


def svd_gls(data, design, covariance):
    """Symmetric-eigensystem whitening + SVD, distinct from author Cholesky fit."""
    lam, vec = np.linalg.eigh(covariance)
    assert lam[0] > 0
    whitener = (vec / np.sqrt(lam)).T
    a = whitener @ design
    z = whitener @ data
    u, singular, vh = np.linalg.svd(a, full_matrices=False)
    rank = int(np.count_nonzero(singular > singular[0] * 1e-12))
    assert rank == design.shape[1]
    beta = vh.T @ ((u.T @ z) / singular)
    residual = z - a @ beta
    return beta, float(residual @ residual), rank, residual, whitener


designs = {'bulk': response, 'constant_rate_dipole': constant,
           'bulk_plus_constant_rate': np.c_[response, constant]}
full_designs = {'bulk': response36, 'constant_rate_dipole': constant36,
                'bulk_plus_constant_rate': np.c_[response36, constant36]}
published = json.loads((ROOT / 'output/physical_results.json').read_text())
fit_checks = {}
block = np.zeros_like(cov)
for w in range(4):
    block[3*w:3*w+3, 3*w:3*w+3] = cov[3*w:3*w+3, 3*w:3*w+3]
for name, design in designs.items():
    beta, statistic, rank, residual, whitener = svd_gls(y, design, cov)
    df = len(y)-rank
    cutoff = chi2.ppf(.95, df)
    eta = max(0., np.sqrt(statistic)-np.sqrt(cutoff))
    discrepancy = np.linalg.solve(whitener, residual * eta/np.sqrt(statistic))
    reached = svd_gls(y-discrepancy, design, cov)[1]
    assert abs(reached-cutoff) < 2e-10
    augmented = np.c_[full_designs[name], nuisance36]
    full_beta, full_stat, full_rank, _, _ = svd_gls(y36, augmented, cov36)
    assert abs(full_stat-statistic) < 1e-9
    assert np.max(abs(full_beta[:len(beta)]-beta)) < 1e-8
    tau = brentq(lambda t: svd_gls(y, design, cov+t*t*np.eye(12))[1]-cutoff,
                 0., 2., xtol=1e-14)
    expected = published['fits'][name]
    assert abs(statistic-expected['T']) < 1e-10
    assert np.max(abs(beta-expected['coef'])) < 1e-8
    assert abs(tau-expected['summary_covariance_tau95_km_s_Mpc']) < 1e-10
    fit_checks[name] = dict(coef=beta.tolist(), T=statistic, df=df,
                           tail_if_fixed_Gaussian=float(chi2.sf(statistic, df)),
                           minimum_whitened_discrepancy95=eta,
                           tau95=tau, full36_nuisance_profile_T=full_stat,
                           full36_rank=full_rank,
                           full36_coefficient_max_difference=float(np.max(abs(full_beta[:len(beta)]-beta))),
                           block_diagonal_T=svd_gls(y, design, block)[1])

# Independent finite-window WLS identity and nonisotropic slope calculation.
rng = np.random.default_rng(9032026)
n = rng.normal(size=(211, 3)); n /= np.linalg.norm(n, axis=1)[:, None]
n[:70, 2] += .7; n /= np.linalg.norm(n, axis=1)[:, None]
r = rng.uniform(20., 220., len(n)); weights = rng.uniform(.01, 1., len(n))
basis = np.zeros((5, 3, 3))
basis[0] = np.diag([1, -1, 0])/np.sqrt(2)
basis[1] = np.diag([1, 1, -2])/np.sqrt(6)
for a, (i, k) in enumerate(((0, 1), (0, 2), (1, 2)), 2):
    basis[a, i, k] = basis[a, k, i] = 1/np.sqrt(2)
angular = np.einsum('ni,aij,nj->na', n, basis, n)
row_design = r[:, None]*np.c_[np.ones(len(n)), n, angular]
left_inverse = np.linalg.solve(row_design.T@(weights[:, None]*row_design),
                               row_design.T*weights)
identity_error = float(np.max(abs(left_inverse@row_design-np.eye(9))))
bulk_response = left_inverse@n
rate_response = left_inverse@(r[:, None]*n)
target = np.zeros((9, 3)); target[1:4] = np.eye(3)
assert np.max(abs(rate_response-target)) < 1e-13
# A dipole-only fit differs because it omits jointly fitted monopole/STF columns.
only_d = row_design[:, 1:4]
naive_bulk = np.linalg.solve(only_d.T@(weights[:, None]*only_d), only_d.T@(weights[:, None]*n))
naive_difference = float(np.linalg.norm(naive_bulk-bulk_response[1:4]))
assert naive_difference > 1e-6
bulk = np.array([120., -80., 210.])
shear = np.einsum('a,aij->ij', rng.normal(size=5), basis)
theta = -.9; h_ref = 72.
radial = n@bulk+r*(h_ref+theta/3+np.einsum('ni,ij,nj->n', n, shear, n))
denom = np.sum(weights*r*r)
m = np.sum((weights*r)[:, None]*n, axis=0)/denom
q = np.einsum('n,ni,nj->ij', weights*r*r, n, n)/denom
delta_direct = np.sum(weights*r*radial)/denom-h_ref
delta_formula = bulk@m+theta/3+np.sum(shear*q)
assert abs(delta_direct-delta_formula) < 1e-12

# Sphere moments and norm/eigenvalue inequalities in Frobenius coordinates.
mu, weight_mu = np.polynomial.legendre.leggauss(7)
phi = np.arange(16)*2*np.pi/16
directions = np.array([[np.sqrt(1-z*z)*np.cos(p), np.sqrt(1-z*z)*np.sin(p), z]
                       for z in mu for p in phi])
skyweight = np.repeat(weight_mu, len(phi))/(2*len(phi))
moment_error = 0.
for w in wins:
    tensor = np.array(w['STF2_matrix_km_s_Mpc'])
    coeff = np.array(w['STF5_coefficients_km_s_Mpc'])
    assert np.linalg.norm(np.einsum('a,aij->ij', coeff, basis)-tensor) < 1e-14
    mean_square = np.sum(skyweight*np.einsum('ni,ij,nj->n', directions, tensor, directions)**2)
    moment_error = max(moment_error, abs(mean_square-2*np.sum(tensor*tensor)/15))
assert moment_error < 2e-14
max_bound_violation = 0.
for _ in range(100):
    qhat = np.einsum('a,aij->ij', rng.normal(size=5), basis)
    err = np.einsum('a,aij->ij', rng.normal(size=5), basis)
    err *= .4*rng.random()/np.linalg.norm(err)
    actual_h = 2.+.2*rng.uniform(-1, 1)
    actual_sigma = np.linalg.norm(qhat-err)/(np.sqrt(6)*actual_h)
    lo = max(0., np.linalg.norm(qhat)-.4)/(np.sqrt(6)*2.2)
    hi = (np.linalg.norm(qhat)+.4)/(np.sqrt(6)*1.8)
    max_bound_violation = max(max_bound_violation, lo-actual_sigma, actual_sigma-hi)
    assert np.max(abs(np.linalg.eigvalsh(qhat)-np.linalg.eigvalsh(qhat-err))) <= .4+1e-13
assert max_bound_violation == 0.

# Exact-rational connection contractions, reconstructed from the metric.
# Default and primary Python have no SymPy; no symbolic-CAS execution is claimed.
def zero_connection(dim):
    return [[[F(0) for _ in range(dim)] for _ in range(dim)] for _ in range(dim)]


def connection_ricci(gamma, deriv, a, b):
    dim = len(gamma)
    return sum(deriv[k][k][a][b]-deriv[b][k][a][k]
               +sum(gamma[k][a][b]*gamma[l][k][l]
                    -gamma[l][a][k]*gamma[k][b][l] for l in range(dim))
               for k in range(dim))


curvature_cases = 0
momentum_cases = 0
for aa, kk, xf, yf, hx, hy, cc in [(F(2),F(3,5),F(4),F(5),F(2,3),F(1,7),F(3)),
                                 (F(3),F(1,9),F(2),F(7),F(-2,5),F(4,9),F(2))]:
    # At r=0, h=diag(1,a^2,a^2); the only nonconstant connections
    # are Gamma^r_xx=Gamma^r_yy=k*a^2*exp(-2*k*r).
    gamma = zero_connection(3)
    deriv = [zero_connection(3) for _ in range(3)]
    for axis in (1, 2):
        gamma[0][axis][axis] = kk*aa*aa
        gamma[axis][0][axis] = gamma[axis][axis][0] = -kk
        deriv[0][0][axis][axis] = -2*kk*kk*aa*aa
    ric = [connection_ricci(gamma, deriv, a, a) for a in range(3)]
    scalar3 = ric[0]+(ric[1]+ric[2])/(aa*aa)
    assert scalar3 == -6*kk*kk
    curvature_cases += 1
    # For spacetime diag(-c^2,Y^2*e^-2Az,Y^2*e^-2Az,X^2), at z=0.
    gamma = zero_connection(4)
    for axis, rate, scale in ((1, hy, yf), (2, hy, yf), (3, hx, xf)):
        gamma[0][axis][axis] = rate*scale*scale/(cc*cc)
        gamma[axis][0][axis] = gamma[axis][axis][0] = rate
    for axis in (1, 2):
        gamma[axis][3][axis] = gamma[axis][axis][3] = -kk
        gamma[3][axis][axis] = kk*yf*yf/(xf*xf)
    # Both derivative terms in R_0z vanish: rates depend on t only,
    # Gamma^z_0z=HX, and Gamma^k_0k contains only HX,HY.
    deriv_zero_for_0z = [zero_connection(4) for _ in range(4)]
    r0z = connection_ricci(gamma, deriv_zero_for_0z, 0, 3)
    assert r0z == -2*kk*(hx-hy)
    momentum_cases += 1
root_error = 0.
for a in np.geomspace(1e-12, 1e5, 100):
    beta = 2*a/(1+np.sqrt(1+4*a*a))
    root_error = max(root_error, abs(a*beta*beta+beta-a)/max(a, 1e-20))
    assert 0 <= beta < 1
assert root_error < 1e-14

# Traceable R28 unit/basis chain; no producer module is executed or imported.
latest = ROOT/'sources/latest'
model = latest/'cf4_apparent_kinematic_distribution.py'
u = json.loads((latest/'R28/r27_cf4_uniform_calibration_quotient_numeric/actual_run/products/RESULT.json').read_text())
f = json.loads((latest/'R28/r27_cf4_exact_calibration_factor_numeric/metadata_repair_run/actual_run/products/RESULT.json').read_text())
source_hash = hashlib.sha256(model.read_bytes()).hexdigest()
assert source_hash == u['source_inputs']['e1_design']['sha256']
assert "register('shear',-KAPPA*response)" in model.read_text()
assert 'shear is dimensionless' in model.read_text()
recorded_tensor = np.array(f['complete_3x3_tensor_display_in_saved_basis'])
decoded = np.einsum('a,aij->ij', f['display_b_fact'], basis)
assert np.linalg.norm(decoded-recorded_tensor) < 1e-16

result = {
    'status': 'PASS for stated finite calculations; two explicit convention repairs in review',
    'independence': 'Own eigensystem/SVD implementation and metric construction; no author functions imported',
    'requested_runtime': 'gpt-6-astra/xhigh', 'observed_runtime': 'UNKNOWN',
    'H03_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'H03_dipole_covariance_min_eigenvalue': float(np.linalg.eigvalsh(cov)[0]),
    'fits': fit_checks,
    'joint_WLS_synthetic_identity_error': identity_error,
    'joint_vs_dipole_only_bulk_response_difference': naive_difference,
    'saved_constant_rate_identity_max': max(w['expansion_dipole_identity_max'] for w in wins),
    'weighted_slope_identity_error': float(abs(delta_direct-delta_formula)),
    'sphere_moment_error': float(moment_error),
    'response_bound_max_violation': max_bound_violation,
    'spatial_scalar_curvature': '-6*k^2; exact rational connection checks',
    'spacetime_R_0z': '-2*A0*(HX-HY); exact rational connection checks',
    'curvature_cases': curvature_cases, 'momentum_cases': momentum_cases,
    'stable_tilt_root_relative_polynomial_error': root_error,
    'R28_source_sha256': source_hash, 'R28_tensor_norm': float(np.linalg.norm(decoded)),
    'R28_directional_rms': float(np.sqrt(2/15)*np.linalg.norm(decoded)),
    'R28_Sigma_if_physical': float(np.linalg.norm(decoded)/np.sqrt(6)),
    'P11_unnormalized_g_counterexample': {'g_t0': 2, 'formula_Sigma_over_true_Sigma': .5},
}
print(json.dumps(result, indent=2, allow_nan=False))
