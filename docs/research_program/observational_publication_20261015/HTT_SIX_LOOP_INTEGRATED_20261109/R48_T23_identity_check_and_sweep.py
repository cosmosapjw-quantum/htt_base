"""R48-T23: independent identity checks and a bounded sensitivity sweep for the Bianchi-to-HTT mock. SYNTHETIC only.

Identities are re-derived from first principles (structure constants -> connection -> momentum constraint and 3-Ricci), NOT
copied from scripts/r48/bianchi_fivevar_identifiability_mock.py; the mock's closed forms are then compared with them.
  I1  class-A momentum constraint M_a = D_b sigma^b_a  versus momentum_A(n, S)
  I2  3-Ricci eigenvalues from the connection versus ricci_A(n) (types I, II, VI0/VII0-like, IX samples)
  I3  det J_B symbolic versus the closed form; rank/kernel of J_A
  I4  tilt inversion beta(M) versus Gamma^2 beta = |M|/w
  I5  LLR / binary-label information for the Gaussian curvature oracle (closed form vs quadrature vs Monte Carlo)
Sweep (bounded): noise scale, enthalpy w, shear amplitude, kinematic correlation mix, prior sd -> posterior sd of the tilt amplitude and
curvature-label information. Run: python3 R48_T23_identity_check_and_sweep.py --repo <repo root> --out result.json
"""
import argparse, importlib.util, json, math, time, warnings
import numpy as np, sympy as sp
from scipy.stats import norm
warnings.filterwarnings("ignore")

def load_mock(repo):
    spec = importlib.util.spec_from_file_location("mock48", f"{repo}/scripts/r48/bianchi_fivevar_identifiability_mock.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def connection(C):
    """orthonormal frame, [e_a,e_b] = C^c_ab e_c ; returns G[c,a,b] = g(e_c, nabla_{e_a} e_b), antisymmetric in (c,b)."""
    G = np.zeros((3, 3, 3))
    for c in range(3):
        for a in range(3):
            for b in range(3):
                G[c, a, b] = 0.5 * (C[c, a, b] - C[a, b, c] + C[b, c, a])
    assert np.abs(G + G.transpose(2, 1, 0)).max() < 1e-12, "metric compatibility failed"
    assert np.abs(G - G.transpose(0, 2, 1) - C).max() < 1e-12, "torsion-free failed"
    return G

def classA_structure(n):                                # C^c_ab = eps_abd n^{dc},  n diagonal
    eps = np.zeros((3, 3, 3)); eps[0, 1, 2] = eps[1, 2, 0] = eps[2, 0, 1] = 1; eps[0, 2, 1] = eps[2, 1, 0] = eps[1, 0, 2] = -1
    N = np.diag(n); C = np.zeros((3, 3, 3))
    for c in range(3):
        for a in range(3):
            for b in range(3):
                C[c, a, b] = sum(eps[a, b, d] * N[d, c] for d in range(3))
    return C

def momentum_from_structure(n, S):
    G = connection(classA_structure(n))                  # G[c,a,b] = Gamma^c_{ab}
    M = np.zeros(3)                                      # (D_b S)^b_a = Gamma^b_{bc} S^c_a - Gamma^c_{ba} S^b_c  (constant components)
    for a in range(3):
        M[a] = sum(G[b, b, c] * S[c, a] for b in range(3) for c in range(3)) - sum(G[c, b, a] * S[b, c] for b in range(3) for c in range(3))
    return M

def ricci_from_structure(C):
    G = connection(C)                                    # G[m,c,b] = Gamma^m_{cb}
    R = np.zeros((3, 3))
    for b in range(3):
        for d in range(3):
            tot = 0.0
            for c in range(3):                           # R^c_{b c d} = Gamma^m_{db} Gamma^c_{cm} - Gamma^m_{cb} Gamma^c_{dm} - C^m_{cd} Gamma^c_{mb}
                for mm in range(3):
                    tot += G[mm, d, b] * G[c, c, mm] - G[mm, c, b] * G[c, d, mm] - C[mm, c, d] * G[c, mm, b]
            R[b, d] = tot
    return R

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); t0 = time.time(); m = load_mock(a.repo); rng = np.random.default_rng(20261111); out = {}
    # ---- I1
    errs = []
    for _ in range(50):
        n = rng.normal(size=3); S = m.stf(rng.normal(size=5))
        Mm = m.momentum_A(n, S); Md = momentum_from_structure(n, S)
        errs.append((np.abs(Mm - Md).max(), np.abs(Mm + Md).max()))
    out["I1_momentum_constraint"] = {"max_abs_diff_mock_minus_derived": max(e[0] for e in errs), "max_abs_diff_mock_plus_derived": max(e[1] for e in errs),
                                    "note": "agreement up to an overall sign (structure-constant orientation convention) if only the second is small"}
    # ---- I2
    r2 = {}
    for k, n in {"I": [0, 0, 0], "II": [1, 0, 0], "VI0/VII0_like": [1, 1, 0], "IX": [1, 1, 1], "IX_aniso": [2, 1, 1], "VIII_like": [1, 1, -1]}.items():
        n = np.array(n, float); Rd_full = ricci_from_structure(classA_structure(n))
        Rm = np.sort(m.ricci_A(n)); Rd = np.sort(np.linalg.eigvalsh(0.5 * (Rd_full + Rd_full.T)))
        r2[k] = {"mock": Rm.tolist(), "derived": Rd.tolist(), "max_abs_diff": float(np.abs(Rm - Rd).max()), "antisymmetric_part_norm": float(np.linalg.norm(0.5 * (Rd_full - Rd_full.T)))}
    out["I2_ricci_spectra"] = r2
    # ---- I3
    S11, S12, S13, S22, S23, S33 = sp.symbols("S11 S12 S13 S22 S23 S33", real=True)
    JB = sp.Matrix([[3 * S11, S23, -S23], [3 * S12, 0, S13], [3 * S13, -S12, 0]]); detJB = sp.expand(JB.det())
    claimed = sp.expand(3 * (S11 * S12 * S13 + S23 * (S12 ** 2 + S13 ** 2)))
    JA = sp.Matrix([[0, S23, -S23], [-S13, 0, S13], [S12, -S12, 0]])
    out["I3_JB_determinant_matches_closed_form"] = bool(sp.simplify(detJB - claimed) == 0)
    out["I3_JB_det_symbolic"] = str(detJB)
    out["I3_JA_kernel_contains_(1,1,1)"] = bool(sp.simplify(JA * sp.Matrix([1, 1, 1])) == sp.zeros(3, 1))
    Sg = m.stf(rng.normal(size=5)); out["I3_JA_generic_rank"] = int(np.linalg.matrix_rank(m.JA(Sg))); out["I3_JB_generic_rank"] = int(np.linalg.matrix_rank(m.JB(Sg)))
    # ---- I4
    r4 = []
    for _ in range(200):
        M = rng.normal(size=3) * 10 ** rng.uniform(-3, 1); w = 10 ** rng.uniform(-1, 1); b = m.beta_from_M(M, w); bn = np.linalg.norm(b)
        r4.append(abs(bn / (1 - bn ** 2) - np.linalg.norm(M) / w) / max(1e-12, np.linalg.norm(M) / w))
    out["I4_tilt_inversion_max_rel_err"] = float(max(r4))
    # ---- I5
    Cr = np.eye(3) * 0.375; delta = np.array(m.ricci_A([2, 1, 1])) - np.array(m.ricci_A([1, 0, 0])); mah = float(delta @ np.linalg.solve(Cr, delta)); mu = mah / 2
    xs = np.linspace(-14, 14, 40001)
    tot = 0.0
    for sgn in (+1, -1):                                  # LLR ~ N(+-mah/2, mah); p1 = sigmoid(LLR)
        pdf = norm.pdf(xs, sgn * mu, math.sqrt(mah)); p1 = 1 / (1 + np.exp(-np.clip(xs, -700, 700)))
        hh = -(p1 * np.log(np.maximum(p1, 1e-300)) + (1 - p1) * np.log(np.maximum(1 - p1, 1e-300)))
        tot += 0.5 * np.trapezoid(pdf * hh, xs)
    L = rng.normal(size=400000) * math.sqrt(mah) + mu; pm = 1 / (1 + np.exp(-L)); H = -(pm * np.log(pm) + (1 - pm) * np.log(1 - pm))
    out["I5_curvature_oracle"] = {"mahalanobis_sq_separation": mah, "MI_nats_quadrature": math.log(2) - tot, "MI_nats_monte_carlo_h1_only": float(math.log(2) - H.mean()),
                                  "MAP_accuracy_closed_form": float(norm.cdf(math.sqrt(mah) / 2))}
    # ---- sweep
    S0 = m.stf([.2, -.05, .1, .08, .06]); M0 = m.momentum_A([1., 0., 0.], S0); g = np.linspace(0, 1.75, 701)
    def posterior(noise, w, shear, corr_mix, prior_sd):
        std = np.array([.075] * 3 + [.065] * 3 + [.05] * 15) * noise
        r = np.random.default_rng(20261110).normal(size=(21, 21)); aa = r @ r.T; d = np.sqrt(np.diag(aa)); cr = aa / np.outer(d, d)
        corr = (1 - corr_mix) * np.eye(21) + corr_mix * cr; C = std[:, None] * corr * std[None, :]
        Mx = shear * M0; means = []
        for lam in g:
            bt = m.beta_from_M(lam * Mx, w); means.append(np.r_[-m.COUNT_RESPONSE_MOCK * bt, -m.GAIA_E1_RESPONSE_MOCK * bt, np.tile(lam * shear * m.chart(S0), 3)])
        means = np.array(means); p = np.exp(-.5 * ((g - 1) / prior_sd) ** 2); p /= p.sum()
        y = means[np.argmin(abs(g - 1))]                     # noise-free data at lambda = 1 -> posterior width only
        wgt = m.posterior_lambda(y, g, p, means, C); lm = (wgt * g).sum(); sd_l = math.sqrt((wgt * (g - lm) ** 2).sum())
        bn = np.array([np.linalg.norm(m.beta_from_M(x * Mx, w)) for x in g]); bm = (wgt * bn).sum(); sd_b = math.sqrt((wgt * (bn - bm) ** 2).sum())
        return {"posterior_sd_lambda": sd_l, "posterior_sd_beta_norm": sd_b, "beta_norm_at_lambda1": float(bn[np.argmin(abs(g - 1))])}
    base = dict(noise=1.0, w=1.0, shear=1.0, corr_mix=0.45, prior_sd=0.25); sweep = {}
    for key, vals in (("noise", [0.5, 1.0, 2.0, 4.0]), ("w", [0.25, 1.0, 4.0]), ("shear", [0.25, 1.0, 2.0]), ("corr_mix", [0.0, 0.45, 0.9]), ("prior_sd", [0.1, 0.25, 0.5])):
        sweep[key] = [dict(value=v, **posterior(**{**base, key: v})) for v in vals]
    out["sweep_base"] = base; out["sweep_posterior_width_at_lambda1"] = sweep
    csw = {}
    for sc in (0.25, 0.5, 1.0, 2.0, 4.0):                    # curvature-sensor noise scale (sigma^2 = 0.375 * sc^2)
        Cx = np.eye(3) * 0.375 * sc ** 2; mh = float(delta @ np.linalg.solve(Cx, delta)); csw[str(sc)] = {"mahalanobis_sq": mh, "MAP_accuracy": float(norm.cdf(math.sqrt(mh) / 2))}
    out["sweep_curvature_noise_scale"] = csw
    jw = np.linalg.solve(np.linalg.cholesky(Cr), delta)
    out["nuisance_projection_residual_norm_parallel_unbounded"] = float(np.linalg.norm((np.eye(3) - np.outer(jw, jw) / (jw @ jw)) @ jw))
    out["elapsed_s"] = time.time() - t0; out["versions"] = {"numpy": np.__version__, "sympy": sp.__version__}
    json.dump(out, open(a.out, "w"), indent=1, sort_keys=True)

if __name__ == "__main__":
    main()
