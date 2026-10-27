"""Static massless entropy projection toy. No physical ODE or solver.

Axisymmetric positive brightness w=I/I0=1+.3 P2+.2 P4+.15 P6.
Fit beta_L in span{P0,P2,...,PL}, w_L=beta_L**(-4), matching
energy moments. This is the full entropy fit through L by symmetry/uniqueness.
Report L_operator/rho0, rho0=4*pi*I0, and DeltaS/Siso.
"""
from pathlib import Path
import json, platform, time
import numpy as np
from numpy.polynomial import legendre as LG
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
TARGET = np.array([1., 0., .3, 0., .2, 0., .15])

def poly_range(coef):
    critical = LG.legroots(LG.legder(coef))
    interior = [r.real for r in critical if abs(r.imag) < 1e-11 and -1 < r.real < 1]
    values = LG.legval(np.array([-1., 1.] + interior), coef)
    return float(values.min()), float(values.max())

def quad(n):
    mu, weight = LG.leggauss(n)
    return mu, weight/2

def fit(L, n):
    mu, weights = quad(n)
    degrees = np.arange(0, L+1, 2)
    p = LG.legvander(mu, L)[:, degrees]
    target = LG.legval(mu, TARGET)
    moments = p.T @ (weights*target)
    b = np.zeros(len(degrees)); b[0] = 1.
    def coeff(bb):
        c = np.zeros(L+1); c[degrees] = bb
        return c
    def objective(bb):
        beta = p@bb
        return np.dot(weights, beta**(-3))/3+np.dot(bb, moments)
    history = []
    for iteration in range(40):
        beta = p@b
        predicted = p.T@(weights*beta**(-4))
        gradient = moments-predicted
        residual = float(np.max(np.abs(gradient)))
        history.append(residual)
        if residual < 3e-14:
            break
        hessian = 4*p.T@((weights*beta**(-5))[:, None]*p)
        step = np.linalg.solve(hessian, -gradient)
        alpha = 1.
        old = objective(b)
        # Both full polynomial positivity and Armijo descent are enforced.
        while alpha > 2**(-30):
            proposal = b+alpha*step
            minimum, _ = poly_range(coeff(proposal))
            if (minimum > .05 and
                objective(proposal) <= old+1e-4*alpha*np.dot(gradient, step)+1e-15):
                b = proposal
                break
            alpha /= 2
        else:
            raise RuntimeError("Line search failed")
    else:
        raise RuntimeError("Newton iteration limit")
    beta_coef = coeff(b)
    return beta_coef, history

rt2, rt6 = np.sqrt(2), np.sqrt(6)
BASIS = np.array([
    np.diag([1, -1, 0])/rt2,
    np.diag([1, 1, -2])/rt6,
    np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]])/rt2,
    np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]])/rt2,
    np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0]])/rt2])

def operator(wfun, n=160, nphi=12):
    mu, weights = quad(n)
    ph = 2*np.pi*np.arange(nphi)/nphi
    direction = np.stack(np.broadcast_arrays(
        np.sqrt(1-mu[:, None]**2)*np.cos(ph)[None, :],
        np.sqrt(1-mu[:, None]**2)*np.sin(ph)[None, :],
        mu[:, None]), axis=-1)
    # <S_i, B_e S_j>=2(S_i e).(S_j e)-(e.S_i.e)(e.S_j.e).
    se = np.einsum("aij,npj->npai", BASIS, direction)
    ese = np.einsum("npi,npai->npa", direction, se)
    kernel = 2*np.einsum("npai,npbi->npab", se, se)
    kernel -= np.einsum("npa,npb->npab", ese, ese)
    return np.einsum("n,nab,n->ab", weights,
                     kernel.mean(axis=1), wfun(mu))

def evaluate(beta_coef, n=256):
    mu, weights = quad(n)
    w = LG.legval(mu, TARGET)
    beta = LG.legval(mu, beta_coef)
    projected = beta**(-4)
    full_degree = len(beta_coef)-1
    p = LG.legvander(mu, max(6, full_degree))
    moment_errors = p[:, :full_degree+1].T@(weights*(w-projected))
    delta_s = float(np.dot(weights, projected**.75-w**.75))
    # Bregman value for h(w)=-w^.75, including the tangent term.
    bregman = float(np.dot(weights,
        projected**.75-w**.75+.75*beta*(w-projected)))
    l2_error = float(np.sqrt(np.dot(weights, (w-projected)**2)))
    wmax = max(poly_range(TARGET)[1], poly_range(beta_coef)[0]**(-4))
    orig_op = operator(lambda m: LG.legval(m, TARGET), n=n)
    fitted_op = operator(lambda m: LG.legval(m, beta_coef)**(-4), n=n)
    operator_error = float(np.linalg.norm(orig_op-fitted_op, ord=2))
    # For L=2, exact residual operator depends only on c4 mismatch.
    dc4 = float(9*np.dot(weights, (w-projected)*p[:, 4]))
    axis_exact_error = abs(dc4)*4/105
    curvature_bound = np.sqrt(256/945*wmax**1.25*max(bregman, 0))
    if full_degree >= 4:
        structural_bound = 0.
    else:
        structural_bound = float(curvature_bound)
    sigma_true = np.ones(5)/np.sqrt(5)
    minus_residual = orig_op@sigma_true
    sigma_fitted = np.linalg.solve(fitted_op, minus_residual)
    shear_error = float(np.linalg.norm(sigma_fitted-sigma_true))
    lambda_fit = float(np.linalg.eigvalsh(fitted_op)[0])
    shear_bound = (structural_bound*np.linalg.norm(sigma_fitted)/
                   (lambda_fit-structural_bound))
    return {
        "L": full_degree, "beta_legendre_coefficients": beta_coef.tolist(),
        "beta_range": list(poly_range(beta_coef)),
        "brightness_upper_bound_W": wmax,
        "max_abs_retained_moment_residual": float(np.max(np.abs(moment_errors))),
        "entropy_defect_over_Siso": delta_s,
        "reduced_bregman_over_4pi_C_I0power": bregman,
        "bregman_entropy_cancellation_error": abs(delta_s-bregman),
        "brightness_l2_average_error": l2_error,
        "operator_error_over_rho0": operator_error,
        "axisymmetric_exact_operator_error": axis_exact_error,
        "omitted_P4_coefficient": dc4,
        "curvature_bound_over_rho0": float(curvature_bound),
        "structural_L4_bound_over_rho0": structural_bound,
        "same_residual_shear_error_over_sigma_ref": shear_error,
        "same_residual_shear_bound_over_sigma_ref": float(shear_bound),
        "operator_eigenvalues_over_rho0": np.linalg.eigvalsh(fitted_op).tolist(),
        "original_operator_eigenvalues_over_rho0": np.linalg.eigvalsh(orig_op).tolist()}

def main():
    start = time.perf_counter()
    fits = {}
    rows = []
    for L in [2, 4]:
        coef, history = fit(L, 96)
        coef_refined, history_refined = fit(L, 192)
        row = evaluate(coef, 256)
        refined = evaluate(coef_refined, 320)
        row["fit_iterations"] = len(history)-1
        row["newton_residual_history"] = history
        row["quadrature_coefficient_max_difference"] = float(np.max(np.abs(coef-coef_refined)))
        row["quadrature_entropy_difference"] = abs(row["entropy_defect_over_Siso"]-refined["entropy_defect_over_Siso"])
        row["quadrature_operator_error_difference"] = abs(row["operator_error_over_rho0"]-refined["operator_error_over_rho0"])
        assert row["max_abs_retained_moment_residual"] < 2e-12
        assert row["bregman_entropy_cancellation_error"] < 2e-12
        assert row["entropy_defect_over_Siso"] > 0
        assert row["quadrature_coefficient_max_difference"] < 2e-12
        assert row["quadrature_operator_error_difference"] < 2e-12
        assert abs(row["operator_error_over_rho0"]-row["axisymmetric_exact_operator_error"]) < 2e-12
        assert row["operator_error_over_rho0"] <= row["curvature_bound_over_rho0"]+2e-12
        assert row["same_residual_shear_error_over_sigma_ref"] <= row["same_residual_shear_bound_over_sigma_ref"]+2e-12
        if L == 4:
            assert row["operator_error_over_rho0"] < 2e-12
        rows.append(row); fits[L] = coef
    # The original target is retained with exact coefficient identity.
    original_target = TARGET.copy()
    # Separate analytic isotropic quadrature check.
    iso_error = float(np.linalg.norm(operator(lambda m: np.ones_like(m))-8*np.eye(5)/15, ord=2))
    assert iso_error < 1e-13
    result = {"status": "PASS_SCOPED", "scope": "static analytic toy; no measured CMB, physical ODE or transport residual",
              "input_brightness_legendre_coefficients": original_target.tolist(),
              "brightness_range": list(poly_range(TARGET)),
              "normalization": "w=I/I0, rho0=4*pi*I0, all operators divided by rho0; entropy difference divided by Siso",
              "projection": "wL=betaL^(-4); full harmonic fit reduces to even axisymmetric modes by uniqueness",
              "fit_quadrature_nodes": [96, 192],
              "evaluation_quadrature_nodes": [256, 320],
              "azimuthal_nodes": 12,
              "isotropic_operator_error": iso_error,
              "rows": rows,
              "elapsed_seconds": time.perf_counter()-start,
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "matplotlib": matplotlib.__version__}}
    out = ROOT/"cas"/"entropic_shear_results.json"
    out.write_text(json.dumps(result, indent=2)+"\n")
    plot(rows, fits)
    print(json.dumps(result, indent=2))

def plot(rows, fits):
    mu = np.linspace(-1, 1, 600)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                        "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8), constrained_layout=True)
    ax = axes[0]
    ax.plot(mu, LG.legval(mu, TARGET), color="#282C34", lw=2, label="Target brightness")
    for L, color in [(2, "#2369A4"), (4, "#BD6425")]:
        ax.plot(mu, LG.legval(mu, fits[L])**(-4), color=color, lw=1.9, label=f"Entropy fit L={L}")
    ax.set(xlabel=r"Propagation cosine $\mu$", ylabel=r"Brightness $I/I_0$", title="Angular reconstruction")
    ax.legend(frameon=False, fontsize=8)
    xx = [2, 4]
    ax = axes[1]
    ax.plot(xx, [r["entropy_defect_over_Siso"] for r in rows], "o-", color="#705792")
    ax.set(xlabel="Retained angular cutoff L", ylabel=r"Entropy defect $\Delta S/S_{\rm iso}$",
           title="Positive unresolved entropy", xticks=xx)
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    ax = axes[2]
    ax.plot(xx, [r["curvature_bound_over_rho0"] for r in rows], "s--", color="#626A73", label="Curvature estimate")
    ax.plot(xx, [max(r["operator_error_over_rho0"], 1e-16) for r in rows], "o-", color="#2369A4", label="Computed operator error")
    ax.set(xlabel="Retained angular cutoff L", ylabel=r"Operator error / $\rho_0$",
           title="L=4 preserves the response", xticks=xx, yscale="log", ylim=(1e-16, 1e-1))
    ax.text(2.08, 1e-12, "Exact L=4 structural error: 0\nComputed: roundoff", ha="left", fontsize=8)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    for ax in axes:
        ax.grid(axis="y", color="#E3E6EA", lw=.6)
    fig.suptitle("Static entropy projection: analytical radiation example, no measured CMB", fontsize=12)
    (ROOT/"figures").mkdir(exist_ok=True)
    fig.savefig(ROOT/"figures"/"entropic_shear_projection.pdf")
    fig.savefig(ROOT/"figures"/"entropic_shear_projection.png", dpi=180)
    plt.close(fig)

if __name__ == "__main__":
    main()
