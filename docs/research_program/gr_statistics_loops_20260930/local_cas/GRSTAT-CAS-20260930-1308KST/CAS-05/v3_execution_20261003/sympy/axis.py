"""Independent SymPy axis for the finite CAS-05 v3 components.

Only the three neutral, hash-bound mathematical inputs define the problem.
All curvature follows the stated R^a_bcd convention.  In C03 the metric
3-jet is sufficient for G(0) and its first derivatives; no assertion is
made about the nonlinear Einstein tensor away from the origin.
"""

import json
from pathlib import Path

import sympy as sp


X = t, x, y, z = sp.symbols("t x y z", real=True)
eta_sign = (-1, 1, 1, 1)
eta = sp.diag(*eta_sign)
b = sp.symbols("b", real=True, positive=True)
lam = sp.symbols("lambda", real=True)
Lambda = sp.symbols("Lambda", real=True)
kappa = sp.symbols("kappa", real=True, positive=True)
c = sp.symbols("c", real=True, positive=True)
s = sp.symbols("s", real=True)
ZERO = {v: 0 for v in X}


def clean(expr):
    return sp.factor(sp.cancel(sp.expand(expr)))


def same(a, b_):
    return clean(a - b_) == 0


def at0(expr):
    return expr.subs(ZERO)


def metric_einstein(metric, inverse):
    """Christoffel, Ricci and Einstein from metric, without target formula."""
    gamma = [[[None for _ in range(4)] for _ in range(4)] for _ in range(4)]
    for a in range(4):
        for d in range(4):
            for e in range(4):
                gamma[a][d][e] = clean(sp.Rational(1, 2) * sum(
                    inverse[a, h] * (sp.diff(metric[h, e], X[d])
                    + sp.diff(metric[h, d], X[e])
                    - sp.diff(metric[d, e], X[h])) for h in range(4)))
    ricci = sp.MutableDenseMatrix(4, 4, [0] * 16)
    for a in range(4):
        for d in range(4):
            ricci[a, d] = clean(sum(
                sp.diff(gamma[h][a][d], X[h])
                - sp.diff(gamma[h][a][h], X[d])
                + sum(gamma[h][h][j] * gamma[j][a][d]
                      - gamma[h][d][j] * gamma[j][a][h]
                      for j in range(4)) for h in range(4)))
    scalar = clean(sum(inverse[a, d] * ricci[a, d]
                       for a in range(4) for d in range(4)))
    einstein = sp.Matrix(4, 4, lambda a, d:
                         clean(ricci[a, d] - metric[a, d] * scalar / 2))
    return gamma, ricci, einstein


def conformal_metric(phi):
    e = sp.exp(2 * phi)
    return e * eta, sp.exp(-2 * phi) * eta


def formula_tensor(phi):
    dp = [sp.diff(phi, v) for v in X]
    box = sum(eta_sign[j] * sp.diff(phi, X[j], 2) for j in range(4))
    square = sum(eta_sign[j] * dp[j] ** 2 for j in range(4))
    return sp.Matrix(4, 4, lambda a, d:
                     -2 * sp.diff(phi, X[a], X[d])
                     + 2 * dp[a] * dp[d]
                     + 2 * eta[a, d] * box + eta[a, d] * square)


def c01_c02():
    phi = -b * t**2 - b * (x*x + y*y + z*z) / 2 + lam * t*t*x / 2
    metric, inverse = conformal_metric(phi)
    gamma, _, G = metric_einstein(metric, inverse)
    target = formula_tensor(phi)
    formula_residual = [clean(G[a, d] - target[a, d])
                        for a in range(4) for d in range(a, 4)]
    G0 = G.subs(ZERO)
    T = (G + Lambda * metric) / kappa
    T0 = T.subs(ZERO)
    Tmix = inverse * T
    dTmix = [Tmix.diff(v).subs(ZERO) for v in X]
    epsilon = clean(T0[0, 0])
    pressure = [clean(T0[j, j]) for j in range(1, 4)]
    gap = clean(epsilon + pressure[0])
    # Differentiate T^a_b u^b=-epsilon u^a.  At the origin u=(1,0,0,0).
    # Spatial equations determine du; temporal normalization gives du^0=0.
    du = sp.Matrix(4, 4, lambda mu, i:
                   0 if i == 0 else clean(-dTmix[mu][i, 0] / gap))
    eig_residual = []
    for mu in range(4):
        deps = clean(sp.diff(T[0, 0], X[mu]).subs(ZERO))
        eig_residual.append(clean(dTmix[mu][0, 0] + deps))
        for i in range(1, 4):
            eig_residual.append(clean(dTmix[mu][i, 0] + gap * du[mu, i]))
    norm_derivative = [clean(sp.diff(metric[0, 0], v).subs(ZERO)
                             + 2 * eta[0, 0] * du[mu, 0])
                       for mu, v in enumerate(X)]
    accel = [clean(c*c * (du[0, i] + gamma[i][0][0].subs(ZERO)))
             for i in range(1, 4)]
    # The ray quantity is an orthonormal-frame contraction, not an
    # eigenfield or continuation assertion.
    ray_sub = {t: 0, x: s, y: 0, z: 0}
    ray = clean((sp.exp(-2 * phi) * (G[0, 0] + G[2, 2])).subs(ray_sub))
    ray_target = sp.exp(b*s*s) * (6*b - 2*lam*s)
    d_eps_x = clean(sp.diff(T[0, 0], x).subs(ZERO))
    d_p2_x = clean(sp.diff(T[2, 2], x).subs(ZERO))
    checks1 = (all(r == 0 for r in formula_residual + eig_residual + norm_derivative)
               and G0 == sp.diag(6*b, 0, 0, 0)
               and same(epsilon, (6*b - Lambda)/kappa)
               and all(same(p, Lambda/kappa) for p in pressure)
               and same(gap, 6*b/kappa)
               and all(same(du[mu, i], lam/(3*b) if (mu, i) == (0, 1) else 0)
                       for mu in range(4) for i in range(4))
               and all(same(accel[i-1], c*c*lam/(3*b) if i == 1 else 0)
                       for i in range(1, 4))
               and d_eps_x == 0 and same(d_p2_x, -2*lam/kappa))
    checks2 = (same(ray, ray_target) and same(ray.subs(lam, 0),
                    6*b*sp.exp(b*s*s)) and
               same(ray.subs(s, 3*b/lam), 0))
    evidence = {
        "metric_curvature_formula_residuals": [str(v) for v in formula_residual],
        "G_origin": [[str(G0[i, j]) for j in range(4)] for i in range(4)],
        "epsilon": str(epsilon), "pressures": [str(v) for v in pressure],
        "gap": str(gap), "du_mu_i": [[str(du[mu, i]) for i in range(4)]
                                 for mu in range(4)],
        "eigen_equation_residuals": [str(v) for v in eig_residual],
        "normalization_residuals": [str(v) for v in norm_derivative],
        "acceleration_spatial": [str(v) for v in accel],
        "density_x_derivative": str(d_eps_x),
        "p2_x_derivative": str(d_p2_x),
        "ray_kappa_epsilon_plus_p2": str(ray),
        "ray_target_residual": str(clean(ray-ray_target)),
        "lambda_zero_ray": str(ray.subs(lam, 0)),
        "nonzero_lambda_radius_value": str(ray.subs(s, 3*b/lam)),
        "domain": "b>0, Lambda<3b, kappa>0, c>0, lambda arbitrary real; radius substitution only lambda!=0",
    }
    return checks1, checks2, evidence


def metric_jet_einstein(g):
    """Compute G(0), d_mu G(0) from metric derivatives through order three.

    Here g(0)=eta and dg(0)=0 are checked by caller.  Consequently Gamma(0)=0,
    and Ricci/dRicci are contractions of dGamma/ddGamma; all omitted products
    contain Gamma(0).  This is differentiation of the metric Christoffel and
    Ricci definitions, not use of a prewritten linearized-Einstein target.
    """
    A = {(a, i, j): at0(sp.diff(g[i, j], X[a]))
         for a in range(4) for i in range(4) for j in range(4)}
    B = {(a, d, i, j): at0(sp.diff(g[i, j], X[a], X[d]))
         for a in range(4) for d in range(4)
         for i in range(4) for j in range(4)}
    C = {(f, a, d, i, j): at0(sp.diff(g[i, j], X[f], X[a], X[d]))
         for f in range(4) for a in range(4) for d in range(4)
         for i in range(4) for j in range(4)}
    assert g.subs(ZERO) == eta
    assert all(v == 0 for v in A.values())
    def dgamm(a, h, i, j):
        return sp.Rational(1, 2) * eta_sign[h] * (
            B[a, i, h, j] + B[a, j, h, i] - B[a, h, i, j])
    def ddgamm(f, a, h, i, j):
        return sp.Rational(1, 2) * eta_sign[h] * (
            C[f, a, i, h, j] + C[f, a, j, h, i] - C[f, a, h, i, j])
    R0 = sp.Matrix(4, 4, lambda i, j: clean(sum(
        dgamm(h, h, i, j) - dgamm(j, h, i, h)
        for h in range(4))))
    dR = [sp.Matrix(4, 4, lambda i, j: clean(sum(
        ddgamm(f, h, h, i, j) - ddgamm(f, j, h, i, h)
        for h in range(4)))) for f in range(4)]
    scalar0 = clean(sum(eta_sign[i] * R0[i, i] for i in range(4)))
    dscalar = [clean(sum(eta_sign[i] * dR[f][i, i]
                         for i in range(4))) for f in range(4)]
    G0 = sp.Matrix(4, 4, lambda i, j: clean(R0[i, j] - eta[i, j]*scalar0/2))
    dG = [sp.Matrix(4, 4, lambda i, j:
                     clean(dR[f][i, j] - eta[i, j]*dscalar[f]/2))
          for f in range(4)]
    return G0, dG


def c03():
    spatial = (x, y, z)
    kval = {(mu, i): sp.symbols(f"k{mu}{i}", real=True)
            for mu in range(4) for i in range(1, 4)}
    q = {i: -6*b*kval[0, i] for i in range(1, 4)}
    M = {(i, j): -6*b*kval[j, i] for i in range(1, 4) for j in range(1, 4)}
    S = {(i, j): (M[i, j]+M[j, i])/2 for i in range(1, 4) for j in range(1, 4)}
    W = {(i, j): (M[i, j]-M[j, i])/2 for i in range(1, 4) for j in range(1, 4)}
    r2 = sum(v*v for v in spatial)
    scalarS = sum(S[i, j]*spatial[i-1]*spatial[j-1]
                  for i in range(1, 4) for j in range(1, 4))
    H = sp.zeros(4)
    for i in range(1, 4):
        H[i, i] = -t*scalarS/2
        H[0, i] = H[i, 0] = -t*r2*q[i]/2 - r2*sum(
            W[i, j]*spatial[j-1] for j in range(1, 4))/5
    jet2 = [clean(at0(sp.diff(H[i, j], *ds) if ds else H[i, j]))
            for i in range(4) for j in range(i, 4)
            for ds in [()] + [(v,) for v in X]
            + [(v, w) for v in X for w in X]]
    phi0 = -b*t*t - b*r2/2
    gbase = eta + 2*phi0*eta
    Gbase0, dGbase = metric_jet_einstein(gbase)
    G0, dG = metric_jet_einstein(gbase + H)
    delta = [sp.Matrix(4, 4, lambda i, j:
                       clean(dG[mu][i, j] - dGbase[mu][i, j]))
             for mu in range(4)]
    target0i = {(mu, i): q[i] if mu == 0 else M[i, mu]
                for mu in range(4) for i in range(1, 4)}
    map_residual = [clean(delta[mu][0, i] - target0i[mu, i])
                    for mu in range(4) for i in range(1, 4)]
    basis_names = [f"k{mu}{i}" for mu in range(4) for i in range(1, 4)]
    basis_images = {}
    basis_full40 = {}
    basis_substitutions = {}
    basis_residuals = []
    for mu in range(4):
        for i in range(1, 4):
            sub = {key: (1 if key == (mu, i) else 0)
                   for key in kval}
            substitution = {kval[key]: val for key, val in sub.items()}
            basis_substitutions[f"k{mu}{i}"] = substitution
            image = [[str(clean(delta[a][0, j].subs(substitution)))
                      for j in range(1, 4)] for a in range(4)]
            basis_images[f"k{mu}{i}"] = image
            basis_full40[f"k{mu}{i}"] = {
                "txyz"[a]: {f"{j}{l}": str(clean(delta[a][j, l].subs(substitution)))
                              for j in range(4) for l in range(j, 4)}
                for a in range(4)}
            basis_residuals.extend(clean(v.subs(substitution))
                                   for v in map_residual)
    # This verifies all forty coefficients are obtained by linear
    # superposition of the twelve independently substituted basis images.
    full_basis_reconstruction = [clean(delta[a][j, l] - sum(
        kval[mu, i] * sp.sympify(basis_full40[f"k{mu}{i}"]["txyz"[a]][f"{j}{l}"],
                                  locals={"b": b})
        for mu in range(4) for i in range(1, 4)))
        for a in range(4) for j in range(4) for l in range(j, 4)]
    # At the origin the stress gap is 6b/kappa, so differentiated
    # eigenvector equations give du_i=-dT^i_0/(epsilon+p_i).
    induced_du = [clean(-delta[mu][i, 0] / (6*b))
                  for mu in range(4) for i in range(1, 4)]
    induced_du_residuals = [clean(induced_du[3*mu+i-1] - kval[mu, i])
                            for mu in range(4) for i in range(1, 4)]
    bianchi = [clean(sum(eta_sign[a]*dG[a][a, j] for a in range(4)))
               for j in range(4)]
    bianchi_base = [clean(sum(eta_sign[a]*dGbase[a][a, j] for a in range(4)))
                    for j in range(4)]
    full40 = {"txyz"[mu]: {f"{i}{j}": str(dG[mu][i, j])
                             for i in range(4) for j in range(i, 4)}
              for mu in range(4)}
    delta40 = {"txyz"[mu]: {f"{i}{j}": str(delta[mu][i, j])
                              for i in range(4) for j in range(i, 4)}
               for mu in range(4)}
    checks = (all(v == 0 for v in jet2 + map_residual + basis_residuals
                  + full_basis_reconstruction + induced_du_residuals
                  + bianchi + bianchi_base)
              and G0 == Gbase0 == sp.diag(6*b, 0, 0, 0)
              and len(full40) == 4 and all(len(v) == 10 for v in full40.values()))
    evidence = {"H_upper_triangle": {f"{i}{j}": str(H[i, j])
                                     for i in range(4) for j in range(i, 4)},
                "H_2jet_residuals": [str(v) for v in jet2],
                "G_origin": [[str(G0[i, j]) for j in range(4)] for i in range(4)],
                "full_40_first_G_coefficients": full40,
                "delta_40_first_G_coefficients": delta40,
                "delta_G_0i_target_residuals": [str(v) for v in map_residual],
                "twelve_basis_order": basis_names,
                "twelve_basis_images_4x3": basis_images,
                "twelve_basis_images_full_40": basis_full40,
                "twelve_basis_residuals": [str(v) for v in basis_residuals],
                "full_40_basis_reconstruction_residuals": [str(v) for v in full_basis_reconstruction],
                "induced_du_mu_i": [str(v) for v in induced_du],
                "induced_du_right_inverse_residuals": [str(v) for v in induced_du_residuals],
                "four_bianchi_contractions": [str(v) for v in bianchi],
                "baseline_bianchi_contractions": [str(v) for v in bianchi_base],
                "right_inverse": "For arbitrary real k_mu_i, set q_i=-6*b*k_0i, M_ij=-6*b*k_ji, S=(M+M.T)/2, W=(M-M.T)/2, and H as listed. Since b>0, this is a universal explicit right inverse for all 12 k components.",
                "scope": "Finite metric 3-jet only; no away-from-origin nonlinear identity or neighborhood assertion."}
    return checks, evidence


def main():
    ok1, ok2, e12 = c01_c02()
    ok3, e3 = c03()
    result = {"checks": {"CAS-05-C01": bool(ok1), "CAS-05-C02": bool(ok2),
                          "CAS-05-C03": bool(ok3)},
              "domain_assumption_diff": [], "counterexample": None,
              "evidence": {"C01_C02": e12, "C03": e3},
              "sympy_version": sp.__version__}
    print(json.dumps(result, sort_keys=True))
    return 0 if all(result["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
