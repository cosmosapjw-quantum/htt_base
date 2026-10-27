"""Phase 6 validation checks for the HTT observable-bridge research run.

T-01  HTT optical law vs Heinesen (2021) effective Hubble parameter: symbolic identity and
      magnitude field f = -kappa*log(1+q) from d_L = cz/H_u(n).
T-02  Leading quadrupole/octupole of f and the R32-01 remainder bounds; reproduction of the
      R32-01 Table I row family d = a(1,2,3)/sqrt(14), S = a*diag(0.6,-0.2,-0.4).
T-03  Normalisation bridge between an axisymmetric STF eigenvalue, the Legendre l=2 coefficient
      of log10(z/d_L) (Kalbouneh 2026 eta_2) and the Frobenius norm used by HTT.
T-04  Proper-motion (direction-drift) E2 response of a shear S: rms and peak in muas/yr for
      ||S||_F = 0.0327 and H0 = 15.2 muas/yr (Darling 2014 scale).
T-05  Linear-theory LambdaCDM expectation of (a) the smoothed velocity-shear at the observer
      and (b) the apparent Hubble quadrupole of radial-velocity shells, as ||S||_F-equivalent,
      for the CF4 windows z_c = 0.025, 0.040, 0.060, 0.080 (s_z = 0.012).
T-06  Heinesen Q monopole reduces to the FLRW deceleration parameter.
T-07  R32-07 Bianchi I kinematic degeneracy ratio 9/5.

Everything here is a toy/consistency computation; no catalogue or map is read.
"""
import json
import numpy as np
import sympy as sp
from scipy import integrate, special

out = {}

# ---------------------------------------------------------------- T-01
H, c, z = sp.symbols('H c z', positive=True)
A1, A2, A3 = sp.symbols('A1 A2 A3', real=True)
n1, n2, n3 = sp.symbols('n1 n2 n3', real=True)
s11, s12, s13, s22, s23 = sp.symbols('s11 s12 s13 s22 s23', real=True)
s33 = -s11 - s22  # trace-free
S = sp.Matrix([[s11, s12, s13], [s12, s22, s23], [s13, s23, s33]])
n = sp.Matrix([n1, n2, n3])
A = sp.Matrix([A1, A2, A3])
# HTT local optical law (R32-01 eq. 21) and Heinesen eq. (4.1) with theta = 3H (c=1 units)
Hu = H - (A.dot(n)) / c + (n.T * S * n)[0]
theta = 3 * H
heinesen = theta / 3 - (A.dot(n)) / c + (n.T * S * n)[0]
out['T01_identity_HTT_vs_Heinesen'] = sp.simplify(Hu - heinesen) == 0
kappa = 5 / sp.log(10)
d = -A / (c * H)
q = (d.dot(n)) + (n.T * (S / H) * n)[0]
dL_lead = c * z / Hu
f_mu = 5 * sp.log(dL_lead / (c * z / H), 10)
out['T01_f_equals_minus_kappa_log1pq'] = sp.simplify(sp.expand_log(f_mu, force=True) + kappa * sp.log(1 + q)) == 0

# ---------------------------------------------------------------- T-02 (numerical, R32-01 conventions)
def stf3(T):
    """Symmetric trace-free projection of a rank-3 tensor (full index convention)."""
    T = (T + np.transpose(T, (0, 2, 1)) + np.transpose(T, (1, 0, 2)) + np.transpose(T, (1, 2, 0))
         + np.transpose(T, (2, 0, 1)) + np.transpose(T, (2, 1, 0))) / 6.0
    delta = np.eye(3)
    tr = np.einsum('ijj->i', T)  # vector of traces
    corr = (np.einsum('ij,k->ijk', delta, tr) + np.einsum('ik,j->ijk', delta, tr) + np.einsum('jk,i->ijk', delta, tr)) / 5.0
    return T - corr

def L_Q(Q, w):
    """R32-01 eq. (6): (L_Q w)_{ijk} = (w_i Q_jk + w_j Q_ik + w_k Q_ij)/3 - (2/15)[d_ij (Qw)_k + d_ik (Qw)_j + d_jk (Qw)_i]."""
    Qw = Q @ w
    delta = np.eye(3)
    t1 = (np.einsum('i,jk->ijk', w, Q) + np.einsum('j,ik->ijk', w, Q) + np.einsum('k,ij->ijk', w, Q)) / 3.0
    t2 = (np.einsum('ij,k->ijk', delta, Qw) + np.einsum('ik,j->ijk', delta, Qw) + np.einsum('jk,i->ijk', delta, Qw)) * (2.0 / 15.0)
    return t1 - t2

def sphere_grid(nth=60, nph=120):
    """Gauss-Legendre nodes in cos(theta) (exact for polynomials of degree <= 2*nth-1) x uniform phi."""
    xg, wg = np.polynomial.legendre.leggauss(nth)
    ph = (np.arange(nph) + 0.5) * 2 * np.pi / nph
    MU, PH = np.meshgrid(xg, ph, indexing='ij')
    WG, _ = np.meshgrid(wg, ph, indexing='ij')
    st = np.sqrt(1 - MU**2)
    nvec = np.stack([st * np.cos(PH), st * np.sin(PH), MU], axis=-1)
    w = WG * (2 * np.pi / nph) / (4 * np.pi)  # normalised angular weights, sum = 1
    return nvec, w

KAPPA = 5.0 / np.log(10.0)
nvec, wgt = sphere_grid()
def multipoles_of_f(dv, Sm):
    qf = nvec @ dv + np.einsum('abi,ij,abj->ab', nvec, Sm, nvec)
    f = -KAPPA * np.log1p(qf)
    # Q_mu = (15/2) < f (n_a n_b - d_ab/3) >, O_mu = (35/2) < f n_<abc> >
    nn = np.einsum('abi,abj->abij', nvec, nvec)
    Qmu = 7.5 * np.einsum('ab,abij->ij', f * wgt, nn - np.eye(3) / 3.0)
    nnn = np.einsum('abi,abj,abk->abijk', nvec, nvec, nvec)
    Omu = 17.5 * stf3(np.einsum('ab,abijk->ijk', f * wgt, nnn))
    return Qmu, Omu, np.max(np.abs(qf))

rows = []
for a in [2.0e-3, 6.6874e-3, 2.23607e-2, 7.47674e-2, 2.5e-1]:
    dv = a * np.array([1.0, 2.0, 3.0]) / np.sqrt(14.0)
    Sm = a * np.diag([0.6, -0.2, -0.4])
    Qmu, Omu, qmax = multipoles_of_f(dv, Sm)
    quad_pred = KAPPA * L_Q(Sm, dv)              # eq. (26) leading term kappa L_S d
    eps = np.linalg.norm(dv) + np.max(np.abs(np.linalg.eigvalsh(Sm)))
    E3 = np.sqrt(35 / 2) * KAPPA * eps**3 / (3 * (1 - eps))
    E2 = np.sqrt(15 / 2) * KAPPA * eps**2 / (2 * (1 - eps))
    rows.append({
        'a': a, 'eps': eps,
        'O_exact_F': float(np.linalg.norm(Omu)),
        'O_quadratic_F': float(np.linalg.norm(quad_pred)),
        'O_remainder_F': float(np.linalg.norm(Omu - quad_pred)),
        'O_bound_E3': float(E3),
        'Q_remainder_F': float(np.linalg.norm(Qmu + KAPPA * Sm)),
        'Q_bound_E2': float(E2),
        'remainders_within_bounds': bool(np.linalg.norm(Omu - quad_pred) <= E3 and np.linalg.norm(Qmu + KAPPA * Sm) <= E2),
    })
out['T02_R32_01_table_family'] = rows
# R32-01 Table I reference values for a = 0.25: exact 7.44586e-2, quadratic 6.68558e-2, remainder 1.04112e-2, bound 3.22984e-1
ref = {'O_exact_F': 7.44586e-2, 'O_quadratic_F': 6.68558e-2, 'O_remainder_F': 1.04112e-2, 'O_bound_E3': 3.22984e-1}
out['T02_a025_relative_error_vs_R32_01'] = {k: float(abs(rows[-1][k] - v) / v) for k, v in ref.items()}

# Global chirality bound witness (eq. 16): Q* = diag(-1/sqrt2, 0, 1/sqrt2), w* = (sqrt10/4, 1, sqrt10/4), O* = L_{Q*} w*
Qs = np.diag([-1 / np.sqrt(2), 0.0, 1 / np.sqrt(2)])
ws = np.array([np.sqrt(10) / 4, 1.0, np.sqrt(10) / 4])
Os = L_Q(Qs, ws)
v = np.einsum('ijk,jk->i', Os, Qs)
chi = np.linalg.det(np.stack([v, Qs @ v, Qs @ Qs @ v], axis=1))
out['T02_chirality_witness'] = {'chi': float(chi), 'bound_4sqrt2_over_135': float(4 * np.sqrt(2) / 135),
                                 'normQ_F': float(np.linalg.norm(Qs)), 'normO_F': float(np.linalg.norm(Os)),
                                 'ratio_chi_over_bound_times_norms': float(abs(chi) / (4 * np.sqrt(2) / 135 * np.linalg.norm(Qs)**6 * np.linalg.norm(Os)**3))}

# ---------------------------------------------------------------- T-03 normalisation bridge
s = sp.symbols('s', positive=True)
mu = sp.symbols('mu', real=True)  # cos(theta)
S_ax = s * sp.diag(-sp.Rational(1, 2), -sp.Rational(1, 2), 1)
n_ax = sp.Matrix([sp.sqrt(1 - mu**2), 0, mu])
Snn = sp.simplify((n_ax.T * S_ax * n_ax)[0])
P2 = sp.legendre(2, mu)
out['T03_axisymmetric_Snn_equals_s_P2'] = sp.simplify(Snn - s * P2) == 0
out['T03_FrobeniusNorm_axisymmetric_over_s'] = float(sp.sqrt(sp.Rational(3, 2)))
# eta = log10(z/d_L) - monopole = log10(H_u(n)/H) ~ (S:nn)/ln10 at first order -> eta_2 (Legendre coeff) = s/ln10
eta2_kalbouneh = [1.45e-2, 1.12e-2, 1.58e-2, 1.17e-2]
out['T03_s_from_eta2'] = [float(e * np.log(10)) for e in eta2_kalbouneh]
out['T03_normS_F_from_eta2'] = [float(e * np.log(10) * np.sqrt(1.5)) for e in eta2_kalbouneh]
out['T03_normS_F_if_H2overH0_is_P2_coefficient'] = float(0.028 * np.sqrt(1.5))
out['T03_HTT_normS_F'] = 0.03265680189
# angular rms of S:nn relative to ||S||_F: <(S:nn)^2> = (2/15)||S||_F^2
out['T03_rms_Snn_over_normS'] = float(np.sqrt(2 / 15))
out['T03_HTT_directional_rms_check'] = float(0.03265680189 * np.sqrt(2 / 15))  # compare 0.0119246

# ---------------------------------------------------------------- T-04 proper-motion E2 response
H0_muas = 15.2  # muas/yr for H0 = 72 (Darling 2014); 70 -> 14.8
Shtt = np.array([[-0.01737217048, 0.00642017243, 0.01454248664],
                 [0.00642017243, 0.00395564447, 0.00563999318],
                 [0.01454248664, 0.00563999318, 0.01341652601]])
Sn = nvec @ Shtt
perp = Sn - np.einsum('abi,ab->abi', nvec, np.einsum('abi,abi->ab', nvec, Sn))
mu_field = H0_muas * np.linalg.norm(perp, axis=-1)
out['T04_normS_F'] = float(np.linalg.norm(Shtt))
out['T04_rms_mu_muas_per_yr'] = float(np.sqrt(np.sum(wgt * mu_field**2)))
out['T04_peak_mu_muas_per_yr'] = float(np.max(mu_field))
out['T04_analytic_rms_factor_sqrt_1_over_5'] = float(np.sqrt(1 / 5))
out['T04_rms_check'] = float(H0_muas * np.linalg.norm(Shtt) * np.sqrt(1 / 5))
out['T04_mu_for_10pct_axisymmetric_shear'] = float(H0_muas * 0.1 * np.sqrt(1.5) * np.sqrt(1 / 5))  # compare Darling '~1.5 muas/yr'
# Curl check: the field -perp(S n) is a gradient on the sphere of -(1/2) n.S.n -> zero curl
out['T04_E2_is_gradient_of_minus_half_nSn'] = True  # analytic: grad_sphere(n.S.n) = 2 perp(S n)

# ---------------------------------------------------------------- T-05 LambdaCDM linear theory
Om, h, ns, s8 = 0.315, 0.674, 0.965, 0.811
Ob = 0.049
f_growth = Om**0.55

def T_EH98_nowiggle(k):
    """Eisenstein & Hu 1998 zero-baryon-oscillation transfer function; k in h/Mpc."""
    theta = 2.7255 / 2.7
    omh2 = Om * h**2
    obh2 = Ob * h**2
    s_eh = 44.5 * np.log(9.83 / omh2) / np.sqrt(1 + 10 * obh2**0.75)  # Mpc
    alpha = 1 - 0.328 * np.log(431 * omh2) * (Ob / Om) + 0.38 * np.log(22.3 * omh2) * (Ob / Om)**2
    kMpc = k * h
    gamma_eff = Om * h * (alpha + (1 - alpha) / (1 + (0.43 * kMpc * s_eh)**4))
    q_eh = kMpc * theta**2 / gamma_eff / h  # as in EH98 eq. 28 with k in h/Mpc: q = k theta^2 / Gamma_eff
    L0 = np.log(2 * np.e + 1.8 * q_eh)
    C0 = 14.2 + 731 / (1 + 62.5 * q_eh)
    return L0 / (L0 + C0 * q_eh**2)

kk = np.logspace(-4, 2, 4000)
Pk_unnorm = kk**ns * T_EH98_nowiggle(kk)**2
def W_th(x):
    return 3 * (np.sin(x) - x * np.cos(x)) / x**3
sig8_unnorm2 = integrate.simpson(Pk_unnorm * W_th(kk * 8.0)**2 * kk**2, x=kk) / (2 * np.pi**2)
Pk = Pk_unnorm * s8**2 / sig8_unnorm2

def sigma_R(R):
    return np.sqrt(integrate.simpson(Pk * W_th(kk * R)**2 * kk**2, x=kk) / (2 * np.pi**2))

# (a) smoothed tidal shear at the observer: rms ||sigma/H||_F = f sqrt(2/3) sigma_R (top hat R)
out['T05a_rms_normS_F_tidal_at_observer'] = {str(R): float(f_growth * np.sqrt(2 / 3) * sigma_R(R)) for R in [50, 75, 100, 150, 200, 240]}

# (b) apparent Hubble quadrupole of a radial-velocity shell with Gaussian window in r (Mpc/h)
def j2prime(x):
    return special.spherical_jn(2, x, derivative=True)

def shell_quadrupole_normS(rc, sr):
    rr = np.linspace(max(rc - 4 * sr, 5.0), rc + 4 * sr, 161)
    Wr = np.exp(-0.5 * ((rr - rc) / sr)**2)
    Wr /= integrate.simpson(Wr, x=rr)
    # window-weighted (v_r/(H r)) kernel: K(k) = int dr W(r) j2'(k r)/r ; H0 cancels because v ~ f H0 and divide by H0 r
    K = np.array([integrate.simpson(Wr * j2prime(k * rr) / rr, x=rr) for k in kk])
    C2 = f_growth**2 * (2 / np.pi) * integrate.simpson(Pk * K**2 * kk**2 / kk**2, x=kk)  # (2/pi) int dk P(k) K(k)^2
    sum_a2m_sq = 5 * C2
    normS_eq = np.sqrt(sum_a2m_sq * 15 / (8 * np.pi))
    return float(normS_eq)

cz_windows = {0.025: 7500.0, 0.040: 12000.0, 0.060: 18000.0, 0.080: 24000.0}
res_b = {}
for zc, czv in cz_windows.items():
    rc = czv / 100.0            # Mpc/h
    sr = 0.012 * 299792.458 / 100.0  # s_z = 0.012 -> Mpc/h
    res_b[str(zc)] = {'r_c_Mpc_h': rc, 's_r_Mpc_h': sr, 'rms_normS_F_equiv': shell_quadrupole_normS(rc, sr)}
out['T05b_shell_apparent_quadrupole_normS_equiv'] = res_b
out['T05_params'] = {'Om': Om, 'h': h, 'ns': ns, 'sigma8': s8, 'f_growth': float(f_growth), 'transfer': 'EH98 no-wiggle'}
out['T05_note'] = ('Linear theory, Gaussian radial window, isotropic sky coverage, no selection, no observer-boost term; '
                   'quantity (b) is the rms Frobenius-equivalent of the l=2 part of v_r/(H r) over the shell. Toy estimate (INFERENCE).')

# ---------------------------------------------------------------- T-06 Heinesen Q monopole in FLRW
t = sp.symbols('t', positive=True)
a_scale = sp.Function('a')(t)
Hf = sp.diff(a_scale, t) / a_scale
theta_f = 3 * Hf
q0 = sp.diff(theta_f, t) / 3   # monopole with a=0, sigma=0
Qfrak = -1 - q0 / Hf**2
q_decel = -sp.diff(a_scale, t, 2) * a_scale / sp.diff(a_scale, t)**2
out['T06_Heinesen_monopole_equals_FLRW_q'] = sp.simplify(Qfrak - q_decel) == 0

# ---------------------------------------------------------------- T-07 Bianchi I degeneracy ratio
tau, alpha = sp.symbols('tau alpha', positive=True)
BA = tau
BB = (1 - alpha) * tau + alpha * tau**2
same_final = sp.simplify(BA.subs(tau, 1) - BB.subs(tau, 1)) == 0
ratio = sp.simplify(sp.diff(BB, tau).subs(tau, 1) / sp.diff(BA, tau).subs(tau, 1))
out['T07_same_final_deformation'] = same_final
out['T07_shear_ratio_at_tf'] = str(ratio)
out['T07_ratio_alpha_4_5'] = str(ratio.subs(alpha, sp.Rational(4, 5)))

with open('/home/claude/htt_obs_bridge_run/validation/results.json', 'w') as fh:
    json.dump(out, fh, indent=2, default=str)
print(json.dumps(out, indent=2, default=str))
