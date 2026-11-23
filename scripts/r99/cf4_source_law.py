"""CF4 conditional finite-z, inclusion and covariance experiments on the R98 cohort."""
from __future__ import annotations

import json
import math
import os
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import quad
from scipy.linalg import cho_factor, cho_solve
from scipy.special import log_ndtr, logsumexp, ndtri_exp, roots_hermitenorm

from htt.obsstat.mv_bulkflow import pair_velocity_covariance
from scripts.r98 import cf4_p1 as old

C = old.C
LOG2PI = math.log(2 * math.pi)
OUT = old.PUB / "R99_FIFTH_BLOCKER_RESOLUTION_20261123" / "CF4_RESULTS.json"
TYPES = {"background_proxy": 1, "native_comoving": 0, "bolometric": -1}


def _distance(sci, z):
    shape = z.shape
    return (C / sci.H0 * sci.distance_integral(z.ravel(), 24)).reshape(shape)


def finite_shift(sci, z, rapidity, observable):
    """Natural log of D(z,0)/D(z,r), with outward radial rapidity r."""
    coeff = TYPES[observable]
    z, rapidity = np.broadcast_arrays(np.asarray(z, float), np.asarray(rapidity, float))
    if not np.all(np.isfinite(z) & (z > 0) & np.isfinite(rapidity)):
        raise ValueError("finite positive observed z and finite rapidity required")
    gap = np.log1p(z) - rapidity
    if np.any(gap <= 0):
        raise ValueError("background redshift must be positive")
    zb = np.expm1(gap)
    return np.log(_distance(sci, z) / _distance(sci, zb)) + coeff * rapidity


def hermite_moments(sci, z, sigma, order):
    """Three distance types for a truncated-rapidity-marginal Gaussian copula.

    Shape [type,source,4] = mean, first, second orthonormal coefficient,
    variance beyond first. Evaluate the last as residual norm to avoid cancellation.
    """
    z, sigma = np.broadcast_arrays(np.asarray(z, float), np.asarray(sigma, float))
    if z.ndim != 1 or not np.all(np.isfinite(z) & (z > 0) & np.isfinite(sigma) & (sigma >= 0)):
        raise ValueError("positive finite 1D z and nonnegative finite sigma required")
    if order < 3:
        raise ValueError("use at least three quadrature nodes")
    positive = sigma > 0
    if not np.all(positive):
        # At zero dispersion r=0 and every distance-type log displacement is zero.
        result = np.zeros((len(TYPES), len(z), 4))
        if np.any(positive):
            result[:, positive] = hermite_moments(sci, z[positive], sigma[positive], order)
        return result
    x, w = roots_hermitenorm(order)
    w /= math.sqrt(2 * math.pi)
    h2 = (x*x - 1) / math.sqrt(2)
    out = np.empty((len(TYPES), len(z), 4))
    for lo in range(0, len(z), 512):
        sl = slice(lo, lo + 512)
        zg = z[sl, None]
        sr = sigma[sl, None] / C
        ell = np.log1p(zg)
        cap = ell / sr
        r = sr * ndtri_exp(log_ndtr(x) + log_ndtr(cap))
        gap = ell - r
        # Endpoint separation lost in subtraction. The omitted normal tail
        # gives delta_r = sr*Phi(cap)*Phi(-x)/phi(cap) to relative O(cap*delta_r/sr).
        close = gap <= 32 * np.finfo(float).eps * ell
        log_zb = np.empty_like(gap)
        with np.errstate(divide="ignore", invalid="ignore"):
            log_zb[~close] = np.log(np.expm1(gap[~close]))
        if np.any(close):
            small_loggap = np.log(sr) + log_ndtr(cap) + log_ndtr(-x) + (cap**2 + LOG2PI)/2
            log_zb[close] = small_loggap[close]
        zb = np.exp(log_zb)
        # chi(zb) / zb tends to c/H0. Retain log_zb if zb underflows.
        chi = _distance(sci, zb)
        ratio = np.divide(chi, zb, out=np.full_like(zb, C/sci.H0), where=zb > 0)
        L = np.log(_distance(sci, zg)) - log_zb - np.log(ratio)
        for k, coeff in enumerate(TYPES.values()):
            f = L + coeff*r
            mean = f @ w
            first = f @ (w*x)
            residual = f - mean[:, None] - first[:, None]*x
            out[k, sl] = np.column_stack((mean, first, f @ (w*h2), residual**2 @ w))
    return out


def inclusion_logs(y, mean, sigma, limit, softness):
    """Return log detected-mark density per mag and log inclusion per target."""
    y, mean, sigma, limit, softness = np.broadcast_arrays(y, mean, sigma, limit, softness)
    if not all(np.all(np.isfinite(a)) for a in (y, mean, sigma, limit, softness)):
        raise ValueError("finite marks and scenario parameters required")
    if np.any(sigma <= 0) or np.any(softness <= 0):
        raise ValueError("sigma and softness must be positive")
    log_mark = -0.5*((y-mean)/sigma)**2 - np.log(sigma) - LOG2PI/2
    return log_mark + log_ndtr((limit-y)/softness), log_ndtr((limit-mean)/np.hypot(sigma, softness))


def joint_selected_logpdf(y, field_means, sigma, limit, softness, probabilities):
    """Finite shared-field prior, conditional on identified x and ALL targets included."""
    means = np.asarray(field_means, float)
    p = np.asarray(probabilities, float)
    if means.ndim != 2 or np.shape(y) != (means.shape[1],) or p.shape != (len(means),):
        raise ValueError("field-by-source means, source marks and field probabilities required")
    if not np.all(np.isfinite(p)) or np.any(p <= 0) or abs(p.sum()-1) > 1e-12:
        raise ValueError("positive, normalized field weights required")
    num, det = inclusion_logs(y, means, sigma, limit, softness)
    ln = logsumexp(np.log(p) + num.sum(axis=1))
    terms = np.log(p) + det.sum(axis=1)
    ld = logsumexp(terms)
    return dict(log_density=float(ln-ld), log_joint_inclusion=float(ld),
                included_field_weights=np.exp(terms-ld))


def gamma_bounds(p, gamma):
    if not (np.isfinite(p) and 0 <= p <= 1 and np.isfinite(gamma) and gamma >= 1):
        raise ValueError("0 <= p <= 1 and finite Gamma >= 1 required")
    return [p/(p+gamma*(1-p)), gamma*p/(1-p+gamma*p)]


def depth_design(W, sigma, mu):
    w = W / sigma[:, None]**2
    totals = w.sum(axis=0)
    if np.any(totals <= 0):
        raise ValueError("missing reference method support")
    center = (w*mu[:, None]).sum(axis=0)/totals
    var = (w*(mu[:, None]-center)**2).sum(axis=0)/totals
    scale = np.where(var > 1e-6, np.sqrt(var), mu.std())
    if np.any(scale <= 0):
        raise ValueError("constant modulus does not define a standardized depth")
    return W*(mu[:, None]-center)/scale


def schur(y, cov):
    """Universal-kriging predictive score, with nine unknown shared means."""
    D = np.tile(np.eye(9), (2, 1))
    C11 = cho_factor(cov[:18, :18], lower=True)
    cross = cov[18:, :18]
    precision_D = cho_solve(C11, D)
    coef = cho_factor(D.T @ precision_D, lower=True)
    beta = cho_solve(coef, precision_D.T @ y[:18])
    pred = D @ beta + cross @ cho_solve(C11, y[:18] - D @ beta)
    H = D - cross @ precision_D
    cond = cov[18:, 18:] - cross @ cho_solve(C11, cross.T) + H @ cho_solve(coef, H.T)
    L = np.linalg.cholesky((cond+cond.T)/2)
    residual = np.linalg.solve(L, y[18:]-pred)
    chi2 = float(residual@residual)
    return dict(chi2=chi2, loglik=float(-(18*LOG2PI+2*np.log(L.diagonal()).sum()+chi2)/2))


def stages(sci):
    with np.load(old.TARGET_INV, allow_pickle=False) as inv:
        targets = inv["target"]
        _, _, _, wu = sci.angular_rule(53)
        stages_out = {}
        for label, order in (("B", 16), ("C", 32)):
            bands = []
            for index, limits in enumerate(sci.BANDS):
                k, wk = sci.cc_rule(order, *limits)
                bands.append(dict(k=k, wk=wk, wu=wu/(4*math.pi), indices=inv[f"{label}{index}"]))
            stages_out[label] = bands
    return targets, stages_out


def projection(sci, finufft, targets, bands, amp, R, pos, n, growth_q, A):
    modes = old._finufft_log_modes(finufft, targets, pos, n, [growth_q], A)[0]
    probe = [0, len(targets)//3, len(targets)//2, len(targets)-1]
    direct = old._direct_fourier_modes(targets[probe], pos, n, growth_q, A)
    parity = np.max(abs(modes[probe]-direct))/np.max(abs(direct))
    sums = {}
    for stage, rule in bands.items():
        blocks, _ = old._cov_from_projected_modes(rule, modes, amp, sci, np.array([R]))
        sums[stage] = sum(blocks)
    err = np.linalg.norm(sums["B"]-sums["C"])/np.linalg.norm(sums["C"])
    if parity > 1e-7 or err > 1e-7:
        raise ArithmeticError(f"mode/radial quadrature parity {parity}, {err}")
    return sums["C"], dict(direct_mode_rel=parity, radial_quadrature_rel=err)


def pair_validation(sci, targets, bands, pos, n, g, amp, R):
    # Reuse Gorski implementation whose public input convention is h/Mpc.
    h = sci.H
    def pk_h(kh):
        k = h*kh
        return h**3*sci.power(k, amp)*np.exp(-(k*R)**2)
    subset = np.linspace(0, len(n)-1, 20, dtype=int)
    gsub = g[subset]
    closed = pair_velocity_covariance(h*pos[subset], n[subset], pk_h, 1/h**2,
                na=1201, nk=1500, kmin=.005, kmax=.05) * np.outer(gsub, gsub)
    # Independent of the Gorski Bessel route: use explicit finite angular Fourier sum.
    direction = targets[:, 1:]
    F = (direction @ n[subset].T) * np.exp(1j*targets[:, :1]*(direction @ pos[subset].T)) * gsub
    discrete = np.zeros_like(closed)
    for band in bands["C"]:
        for ik, k in enumerate(band["k"]):
            groups = F[band["indices"][ik]]
            weight = band["wk"][ik]*sci.power(k, amp)*np.exp(-(k*R)**2)*band["wu"]/(2*math.pi**2)
            discrete += ((groups.T * weight) @ groups.conj()).real
    return dict(selected_indexes=subset, n_sources=len(subset),
                rel_fro=np.linalg.norm(closed-discrete)/np.linalg.norm(closed),
                max_abs_kms2=np.max(abs(closed-discrete)),
                diag_rel=np.max(abs(closed.diagonal()/discrete.diagonal()-1)))

def source_design(prev):
    H = old.r95._load_h03()
    cat = old.catalog()
    ids, mu, emu, cz, v, _, _, _, n, _ = cat
    selected = (cz/old.C >= .01) & (cz/old.C <= .10)
    idx = np.flatnonzero(selected)
    idx = idx[np.argsort(ids[idx])]
    source = H.source(old.r95.SELECT)
    if not np.array_equal(ids[idx], source.ids) or not np.array_equal(mu[idx], source.mu):
        raise ValueError("selected identity or modulus drift")
    W = old.magnitude_weights(old.r97._parse_complete_table3_for_selected(ids))[idx]
    _, _, sigma, A, _, b = old.tomography(H, n[idx], cz[idx], v[idx], mu[idx], emu[idx])
    b = b.ravel()
    previous_b = np.asarray(prev["fit"]["selected_log_coefficients_4x9"]).ravel()
    if np.max(abs(b-previous_b)) > 1e-12:
        raise ValueError("archived coefficient drift")
    G = depth_design(W, sigma, mu[idx])
    J = A@G
    d = np.array([.011, -.021, .031, -.041, .051, -.061, .071])
    shifted = old.tomography(H, n[idx], cz[idx], v[idx], mu[idx]+G@d, emu[idx])[-1].ravel()-b
    test = dict(perturbation_mag=d, actual_peak=np.max(abs(shifted)),
                corrected_max_error=np.max(abs(shifted+old.MAG*J@d)),
                historical_max_error=np.max(abs(shifted-J@d)))
    if test["corrected_max_error"] > 1e-12 or test["historical_max_error"] < 1e-3:
        raise ArithmeticError("fixed-source finite magnitude response failed")
    positive = (cz > 0) & (v > 0)
    cut = []
    for extra in (cz/C < .01, cz/C > .10):
        mask = selected | (positive & extra)
        cut.append(old.tomography(H, n[mask], cz[mask], v[mask], mu[mask], emu[mask])[-1].ravel()-b)
    C_cut = np.array(cut).T@np.array(cut)
    old_tilt = .05**2 * J@J.T
    mag_tilt = old.MAG**2 * old_tilt
    T = -old.MAG*A@W
    cal = np.full((7, 7), .087**2)
    cal[1:6, 1:6] += np.array(prev["fit"]["relative_cov_5x5_mag2"])
    cal[6, 6] += .5**2
    C_cal = T @ cal @ T.T
    return (ids[idx], mu[idx], emu[idx], cz[idx]/C, v[idx], n[idx], A, b,
            C_cal+C_cut, old_tilt, mag_tilt, dict(finite_shift=test,
            trace_cut=np.trace(C_cut), trace_calibration=np.trace(C_cal),
            trace_tilt_log_units=np.trace(old_tilt), trace_tilt_mag_units=np.trace(mag_tilt),
            matrix_mag_tilt=mag_tilt, boundary_columns=np.array(cut).T))


def likelihood_examples(mu, emu, z, sci):
    # Full fixed-design illustrative field +/-100 km/s, fixed thresholds defined at zero field.
    # Zero point H_ref is the same for every field and threshold. No fit to catalogue selection.
    mean0 = 25 + 5*np.log10((1+z)*_distance(sci, z)*sci.H0/old.HREF)
    fields = np.array([-100., 100.])
    means = np.array([mean0 - finite_shift(sci, z, np.arctanh(u/C), "bolometric")/old.MAG
                      for u in fields])
    log_density = joint_selected_logpdf(mu, means, emu, mean0+.5, .25, [.5,.5])
    single = joint_selected_logpdf(mu, mean0[None, :], emu, mean0+.5, .25, [1.])
    empirical_p = float(np.mean(mu > mean0))
    return dict(label="fixed-cohort demonstration; registered marks treated as bolometric in scenario only",
                design="two deterministic uniform radial field values, threshold mean0+0.5 mag, softness 0.25 mag",
                field_kms=fields, selected_field_mixture=log_density, zero_field=single,
                empirical_mark_event="released group mu exceeds fiducial FLRW mean0; selected-cohort descriptive fraction",
                empirical_mark_fraction=empirical_p,
                pooled_support_bounds={str(G):gamma_bounds(empirical_p, G) for G in [1,1.5,2,4]},
                pooled_bound_assumption="single pooled mark distribution; global relative inverse inclusion <=Gamma and support overlap")


def compute():
    prev_sha = old.r97._sha(old.OUT)
    if prev_sha != "436630f094950d1d21d82ab61a9b587df788cc4f28c3976f5ff2b677a5350591":
        raise ValueError("R98 archived result identity changed")
    prev = json.loads(old.OUT.read_text())
    sci, _, _, finufft = old._load_r30_and_bridge()
    hashes = {"R98_result":prev_sha, "R98_code":old.r97._sha(Path(old.__file__)),
              "R30_science":old.r97._sha(Path(sci.__file__)), "R99_code":old.r97._sha(Path(__file__))}
    for key in ("table3.dat", "table4.dat", "selected", "R36_targets"):
        record = prev["inputs"][key]
        h = old.r97._sha(Path(record["path"]))
        if h != record["sha256"]:
            raise ValueError(f"baseline input changed: {key}")
        hashes[key] = h
    ids, mu, emu, z, v, n, A, b, systematic, oldtilt, magtilt, selection = source_design(prev)
    targets, bands = stages(sci)
    amp, _ = sci.power_amplitude()
    R = 5 / sci.H
    chi, growth, jac, _, _ = sci.background(z, 64)
    pos = chi[:, None] * n
    def radial_integral(klo, khi):
        return quad(lambda k: sci.power(k, amp)*np.exp(-(k*R)**2)/(6*math.pi**2),
                    klo*sci.H, khi*sci.H, epsrel=1e-10)[0]
    band_integral = radial_integral(.005, .05)
    nl = 150.
    sigma = np.sqrt(growth**2 * band_integral + nl**2)
    q_wf = (1+v/C)/v
    coherent_wf, modecheck = projection(sci, finufft, targets, bands, amp, R, pos, n, growth*q_wf, A)
    def diagonal_projection(variance):
        return (A*variance) @ A.T
    noise_meas = diagonal_projection((old.MAG*emu)**2)
    base_wf = systematic + coherent_wf + noise_meas + diagonal_projection((nl*q_wf)**2)
    before = schur(b, base_wf + oldtilt)
    historical = prev["correlated_source_and_selection_extension"]["transport_covariance_models_36d"]["correlated_WF_R5_nl150_cal087_sel"]
    historic_error = max(abs(before["chi2"]-historical["inner_to_outer_18dof_schur_chi2"]),
                         abs(before["loglik"]-historical["inner_to_outer_18dof_schur_loglik"]))
    if historic_error > 1e-7:
        raise ArithmeticError(f"old score failed paired replay: {historic_error}")
    selection.update(schur_historical=before, schur_replay_max_abs=historic_error,
                     schur_corrected=schur(b, base_wf+magtilt), wf_nufft=modecheck)
    # Same fiducial source coordinates and field spectrum for all observable responses.
    coarse = hermite_moments(sci, z, sigma, 16)
    moments = hermite_moments(sci, z, sigma, 32)
    convergence = np.max(abs(moments-coarse), axis=(0,1))
    if np.any(convergence > 1e-8):
        raise ArithmeticError(f"Hermite 16 vs 32 absolute drift: {convergence}")
    family = {}
    K = (1+z)/(sci.H0*sci.e_z(z)*chi)
    r_fd = np.arctanh(1/C)
    for i,(label, coeff) in enumerate(TYPES.items()):
        mean, first, second, residual = moments[i].T
        q = K + coeff/C
        fd = (finite_shift(sci,z,r_fd,label)-finite_shift(sci,z,-r_fd,label))/2
        derivative_rel = float(np.max(np.abs(fd/q-1)))
        if derivative_rel > 2e-7:
            raise ArithmeticError(f"{label} signed derivative drift")
        q1 = first/sigma
        coherent, check = projection(sci, finufft, targets, bands, amp, R, pos, n, growth*q1, A)
        independent = diagonal_projection((nl*q1)**2)
        C1 = coherent + independent
        projected_mean = A @ mean
        envelope = (abs(A)@np.sqrt(residual))**2
        if np.linalg.eigvalsh(C1).min() < -1e-10 or np.min(residual) < 0:
            raise ArithmeticError("negative variance")
        family[label] = dict(q_zero_kms_inv_range=[q.min(), q.max()], fd_rel_max=derivative_rel,
              first_response_ratio_range=[min(q1/q),max(q1/q)], projected_mean_36=projected_mean,
              mean_log_shift_range=[mean.min(),mean.max()], first_chaos_covariance_36=C1,
              coherent_and_independent_trace=[np.trace(coherent),np.trace(independent)],
              residual_var_fraction_max=np.max(residual/(first**2+residual)),
              second_chaos_row_variance_max=np.max(second**2),
              projected_residual_variance_upper_36=envelope, min_eig_C1=np.linalg.eigvalsh(C1).min(),
              nufft=check)
    pair = pair_validation(sci, targets, bands, pos, n, growth, amp, R)
    if pair["rel_fro"] > 2e-4 or pair["diag_rel"] > 1e-4:
        raise ArithmeticError(f"angular-Bessel independent variance parity: {pair}")
    small = radial_integral(.0001,.005)
    large = radial_integral(.05,1.)
    return dict(schema="htt.r99.cf4.conditional_source_law/v1", baseline="575ff4811b6a5ae12d7c14bf7cd8ecadef7e58aa",
        inputs_sha256=hashes, selected=dict(N=len(ids),z_range=[min(z),max(z)],first_last_group=ids[[0,-1]]),
        software=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
            finufft=finufft.__version__,threads={k:os.getenv(k) for k in ["OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"]}),
        magnitude_tilt_correction=selection,
        velocity_design=dict(description="shared standardized Gaussian copula plus independent Gaussian 150 km/s latent dispersion; truncated-rapidity marginal, fixed z and geometry",
             H0=sci.H0, Omega_m=sci.OM, sigma8=sci.SIGMA8, n_s=sci.NS, H_ref_catalog=old.HREF,
             smoothing_Mpc_over_h=5, band_h_per_Mpc=[.005,.05], target_count=len(targets),
             sigma_latent_kms_range=[sigma.min(), sigma.max()], max_truncated_upper_mass=float(np.exp(log_ndtr(-C*np.log1p(z)/sigma)).max()),
             integral_variance_fractions_R5_linear_comparator=dict(domain_h_per_Mpc=[.0001,1.],
                 low_k=small/(small+band_integral+large), inherited_band=band_integral/(small+band_integral+large),
                 above_band=large/(small+band_integral+large)),
             derivative_R98_background_max_abs=np.max(abs((K+1/C)+old.MAG*jac))),
        moment_convergence_16_32_max_abs=convergence, scenarios=family, pair_Bessel_check=pair,
        selected_likelihood=likelihood_examples(mu,emu,z,sci), physical_Pi=None,
        status="CONDITIONAL_OBSERVABLE_SCENARIOS; upstream calibration, catalogue inclusion and joint physical null open")


if __name__ == "__main__":
    result = compute()
    payload = json.dumps(result, default=old.json_default, indent=2, allow_nan=False)
    OUT.write_text(payload+"\n")
    print(f"wrote {OUT}; selected={result['selected']['N']}")
