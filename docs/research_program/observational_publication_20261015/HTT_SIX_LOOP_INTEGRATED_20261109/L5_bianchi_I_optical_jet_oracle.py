"""L5 oracle: first-order directional Hubble law and exact Bianchi-I luminosity-distance jet. SYNTHETIC only (no data).

A  Algebra: k^a k^b nabla_a u_b = E^2 (Theta/3 + sigma_ab e^a e^b + A.e)  (vorticity drops out), random tensors, orthonormal frame.
B  Exact Bianchi I, a_i = t^{p_i}, comoving observer and sources, observer at t0=1, p_i = n_i (E0=1):
   * z/(lookback time) -> H(n) = sum_i n_i^2 H_i = Theta/3 + sigma_nn   as the lookback time -> 0
   * sky average of H(n) = Theta/3
C  Exact area distance from geodesic deviation (neighbouring geodesics at equal affine parameter, projection on the screen
   orthogonal to u and k), d_L = (1+z)^2 d_A.  FLRW limit (equal p_i) checked against the exact power-law formula.
D  Jet coefficient c0(n) = lim_{z->0} (d_L H(n)/z - 1)/z  (Richardson), its real-harmonic content (even l only expected; l<=4).
Run: python3 L5_bianchi_I_optical_jet_oracle.py
"""
import json, math, time, warnings
import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import sph_harm_y
warnings.filterwarnings("ignore")
rng = np.random.default_rng(20261111)
out = {}

# ---------------- A: algebraic identity ----------------
def algebra_check(ntrial=200):
    err = 0.0
    for _ in range(ntrial):
        Th = rng.normal(); S = rng.normal(size=(3, 3)); S = 0.5 * (S + S.T); S -= np.trace(S) / 3 * np.eye(3)
        W = rng.normal(size=(3, 3)); W = W - W.T; A = rng.normal(size=3)
        e = rng.normal(size=3); e /= np.linalg.norm(e); E = abs(rng.normal()) + 0.5
        # nabla_a u_b in the orthonormal frame, u^a=(1,0,0,0): nabla_i u_j = sigma+omega+Th/3 delta ; nabla_0 u_j = A_j
        D = np.zeros((4, 4)); D[1:, 1:] = S + W + Th / 3 * np.eye(3); D[0, 1:] = A
        k = E * np.r_[1.0, e]
        err = max(err, abs(k @ D @ k - E ** 2 * (Th / 3 + e @ S @ e + A @ e)))
    return err
out["A_algebra_identity_max_abs_err_200_random_tensors"] = algebra_check()

# ---------------- B/C/D: exact Bianchi I ----------------
def make_model(pv):
    pv = np.asarray(pv, float)
    def Efun(t, p):                       # energy measured by comoving observers, E^2 = sum p_i^2 / a_i^2
        return math.sqrt(np.sum(p ** 2 / t ** (2 * pv)))
    def rhs(s, y, p):                     # backward integration in s = -lambda
        t = y[0]; E = Efun(t, p)
        return np.r_[-E, -p / t ** (2 * pv)]
    return pv, Efun, rhs

def trace(pv, n, z):
    """central geodesic from observer (t0=1,x=0) until E = 1+z; returns s_end, y_end."""
    pv, Efun, rhs = make_model(pv); p = np.asarray(n, float)          # E0 = 1 -> p_i = n_i (a_i(t0)=1)
    ev = lambda s, y, p: Efun(y[0], p) - (1.0 + z)
    ev.terminal = True; ev.direction = 1
    sol = solve_ivp(rhs, (0, 50), np.r_[1.0, 0, 0, 0], args=(p,), events=ev, rtol=1e-12, atol=1e-14, method="DOP853")
    return sol.t_events[0][0], sol.y_events[0][0]

def d_lum(pv, n, z, delta=1e-4):
    pv, Efun, rhs = make_model(pv); n = np.asarray(n, float); n = n / np.linalg.norm(n)
    s_end, yc = trace(pv, n, z)
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(n, a); e1 /= np.linalg.norm(e1); e2 = np.cross(n, e1)
    xi = []
    for ev_ in (e1, e2):
        ys = []
        for sgn in (+1, -1):
            nn = n + sgn * delta * ev_; nn /= np.linalg.norm(nn)
            sol = solve_ivp(rhs, (0, s_end), np.r_[1.0, 0, 0, 0], args=(nn,), rtol=1e-12, atol=1e-14, method="DOP853")
            ys.append(sol.y[:, -1])
        xi.append((ys[0] - ys[1]) / (2 * delta))                    # d y / d(angle) at equal affine parameter
    te = yc[0]; G = np.diag(np.r_[-1.0, te ** (2 * pv)])
    E = Efun(te, n); u = np.r_[1.0, 0, 0, 0]
    ehat = np.r_[0.0, n / te ** (2 * pv) / E]                       # spatial unit propagation vector at the source
    dot = lambda a_, b_: a_ @ G @ b_
    scr = [x_ + u * dot(u, x_) - ehat * dot(ehat, x_) for x_ in xi]  # screen projection orthogonal to u and e
    M = np.array([[dot(scr[i], scr[j]) for j in range(2)] for i in range(2)])
    return (1 + z) ** 2 * np.linalg.det(M) ** 0.25                  # d_A^2 = sqrt(det M) per unit solid angle

# C: FLRW limit check, a = t^p, p_i = p
res_flrw = []
for p in (0.6667, 0.5):
    pv = [p, p, p]; n = np.array([0.3, -0.5, 0.81]); n /= np.linalg.norm(n)
    for z in (0.05, 0.2):
        s_end, y = trace(pv, n, z); te = y[0]
        chi = (1 - te ** (1 - p)) / (1 - p)
        dL_exact = (1 + z) ** 2 * te ** p * chi
        res_flrw.append({"p": p, "z": z, "rel_err": abs(d_lum(pv, n, z) / dL_exact - 1)})
out["C_flrw_limit_exact_formula_rel_err"] = res_flrw
out["C_flrw_limit_max_rel_err"] = max(r["rel_err"] for r in res_flrw)

# B: first-order law
pv = np.array([0.80, 0.60, 0.40]); H = pv / 1.0; Theta3 = H.mean()
firstorder = []
for _ in range(6):
    n = rng.normal(size=3); n /= np.linalg.norm(n)
    Hn = float(np.sum(n ** 2 * H)); sig_nn = Hn - Theta3
    row = {"Hn": Hn, "Theta_over_3_plus_sigma_nn": Theta3 + sig_nn}
    for z in (1e-3, 1e-4):
        s_end, y = trace(pv, n, z); row[f"z_over_lookback_z{z}"] = z / (1.0 - y[0])
    firstorder.append(row)
out["B_first_order"] = {"H_i": H.tolist(), "samples": firstorder,
                        "max_rel_dev_z1e-4": max(abs(r["z_over_lookback_z0.0001"] / r["Hn"] - 1) for r in firstorder)}
GLn, GLw = np.polynomial.legendre.leggauss(40)
ph = np.arange(80) * 2 * np.pi / 80
xs = np.outer(np.sqrt(1 - GLn ** 2), np.cos(ph)); ys_ = np.outer(np.sqrt(1 - GLn ** 2), np.sin(ph)); zs = np.outer(GLn, np.ones(80))
Hs = xs ** 2 * H[0] + ys_ ** 2 * H[1] + zs ** 2 * H[2]
out["B_sky_average_H_minus_Theta_over_3"] = float((Hs * GLw[:, None]).sum() / (2 * 80) - Theta3)

# D: jet coefficient and harmonic content
def c0(pv, n):
    Hn = float(np.sum(np.asarray(n) ** 2 * (np.asarray(pv) / 1.0)))
    f = lambda z: (d_lum(pv, n, z) * Hn / z - 1) / z
    return 2 * f(0.004) - f(0.008)
pv_a = np.array([0.80, 0.60, 0.40])
dirs = rng.normal(size=(160, 3)); dirs /= np.linalg.norm(dirs, axis=1)[:, None]
t0_ = time.time(); vals = np.array([c0(pv_a, n) for n in dirs]); out["D_runtime_s"] = time.time() - t0_
th = np.arccos(dirs[:, 2]); phi = np.arctan2(dirs[:, 1], dirs[:, 0])
cols, labels = [], []
for l in range(0, 9):
    for m in range(-l, l + 1):
        Y = sph_harm_y(l, abs(m), th, phi)
        cols.append(Y.real * math.sqrt(2) if m > 0 else (Y.imag * math.sqrt(2) if m < 0 else Y.real)); labels.append(l)
A = np.array(cols).T; labels = np.array(labels)
Hdir = (dirs ** 2) @ H                                              # H(n) on the sampled directions
# With lookback time D: d_L = D(1 + a1 D), z = H D + b2 D^2 (a1, b2 polynomial in n) => c0 = a1/H - b2/H^2 => c0*H^2 = a1 H - b2 is polynomial.
for name, target in (("c0", vals), ("c0_times_Hn", vals * Hdir), ("c0_times_Hn2", vals * Hdir ** 2)):
    coef, *_ = np.linalg.lstsq(A, target, rcond=None)
    out[f"D_{name}_harmonic_amplitudes_by_l"] = {int(l): float(np.sqrt(np.sum(coef[labels == l] ** 2))) for l in range(0, 9)}
    out[f"D_{name}_fit_residual_rms"] = float(np.sqrt(np.mean((A @ coef - target) ** 2)))
    out[f"D_{name}_rms"] = float(np.sqrt(np.mean(target ** 2)))
out["D_model"] = {"p_i": pv_a.tolist(), "H_i_over_mean_rms": float(np.sqrt(np.mean(((H - H.mean()) / H.mean()) ** 2))),
                  "flrw_reference_c0_for_p0.6": 0.5 * (2 - 1 / 0.6)}
# E: truncation window. Ratio of the second-order l=2 amplitude to the first-order l=2 amplitude, for small anisotropy.
def l_amp(dirs_, vals_, l):
    th_, ph_ = np.arccos(dirs_[:, 2]), np.arctan2(dirs_[:, 1], dirs_[:, 0]); cs = []
    for ll in range(0, 7):
        for m in range(-ll, ll + 1):
            Y = sph_harm_y(ll, abs(m), th_, ph_)
            cs.append(Y.real * math.sqrt(2) if m > 0 else (Y.imag * math.sqrt(2) if m < 0 else Y.real))
    lab = np.array([ll for ll in range(0, 7) for m in range(-ll, ll + 1)])
    cf, *_ = np.linalg.lstsq(np.array(cs).T, vals_, rcond=None)
    return float(np.sqrt(np.sum(cf[lab == l] ** 2)))
dirs_s = rng.normal(size=(80, 3)); dirs_s /= np.linalg.norm(dirs_s, axis=1)[:, None]
window = []
for pbar, delta in ((0.5, 0.01), (0.6667, 0.03), (0.6667, 0.01), (0.9, 0.01), (0.6, 0.10), (0.6, 0.03), (0.6, 0.01)):
    pv_s = np.array([pbar + delta, pbar, pbar - delta]); Hs_ = (dirs_s ** 2) @ pv_s
    cvals = np.array([c0(pv_s, n) for n in dirs_s])
    a1 = l_amp(dirs_s, Hs_, 2)                                          # first-order l=2 amplitude of H(n)
    # second-order term of H_eff = z/d_L:  H_eff = H (1 - c0 z) -> l=2 part of (c0 * H) times z; c0*H = polynomial/H, so use c0*H directly
    a2 = l_amp(dirs_s, cvals * Hs_, 2)
    a0 = l_amp(dirs_s, cvals * Hs_, 0)
    window.append({"p_bar": pbar, "q0_isotropic": 1 / pbar - 1, "delta_p": delta, "H_i_spread_over_mean": delta / pbar, "l2_first_order_amp": a1, "l2_second_order_amp_(c0*H)": a2,
                   "ratio_l2_second_over_first_per_unit_z": a2 / a1, "l0_second_order_amp_(c0*H)": a0})
out["E_truncation_window"] = window
# F: remainder of the truncated jet against the exact distance, anisotropic model (p_bar=2/3, delta=0.03), 24 directions
pv_f = np.array([0.6667 + 0.03, 0.6667, 0.6667 - 0.03]); dirs_f = dirs_s[:24]; Hf = (dirs_f ** 2) @ pv_f
c0f = np.array([c0(pv_f, n) for n in dirs_f]); rem = []
for zz in (0.01, 0.03, 0.1, 0.2, 0.3):
    dl = np.array([d_lum(pv_f, n, zz) for n in dirs_f])
    e1 = np.abs(dl * Hf / zz - 1); e2 = np.abs(dl * Hf / (zz * (1 + c0f * zz)) - 1)
    rem.append({"z": zz, "first_order_max_rel_err": float(e1.max()), "second_order_max_rel_err": float(e2.max()),
                "first_order_aniso_part_rel_err_(max-min)": float(e1.max() - e1.min())})
out["F_truncation_remainder_pbar_0.6667_delta_0.03"] = rem
import scipy
out["versions"] = {"numpy": np.__version__, "scipy": scipy.__version__}
print(json.dumps(out, indent=1))
