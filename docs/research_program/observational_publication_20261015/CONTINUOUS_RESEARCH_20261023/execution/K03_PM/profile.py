"""K03 conditional six-amplitude proper-motion diagnostic.

One retained-row pass adds H moments to the frozen A22-05 sufficient statistics.
This is a tangent calculation on reported Quaia redshifts, not a physical fit.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve, solve_triangular

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").exists())
OLD_DIR = ROOT / "docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/astrometry"
DATA = Path("/mnt/extdrive/workdir/htt_open_data/a22_20261023")
CACHE = DATA / "quaia_join/quaia_gaia_full_join.npz"
STATS = DATA / "astrometry/full_stats.npz"
STATS_RECEIPT = DATA / "astrometry/stats_receipt.json"
NEW_CACHE = Path("/mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz")
EXPECTED = {
    CACHE: "4cd83b1e8bb9f71f89aacfc2db5daba87f9a79f2af8ccd2e7e94b0be57252dae",
    STATS: "4d9406de69546e72dff79d4fc611703e8eb450944c4dcc254f8484c98a22d5da",
    STATS_RECEIPT: "c0fb5225d65e21c2e0da752fa343017afb26c650a395cdca4ca3edf1db97d162",
    OLD_DIR / "model.py": "c132f01d9d35e267aa67e8465987bb8cfbab94f46e4f8adc32e9c793f5b74659",
    OLD_DIR / "CONFIG.json": "196774e641c0ee85b356762fcb6397c1592f0d701ccc99b587f5ce417c175fc2",
}
R = 7499.25
RAD = 1e-4
KH = 14.76646685987891
TAU = 1e-10


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_inputs() -> dict[str, str]:
    actual = {str(p): digest(p) for p in EXPECTED}
    bad = {str(p): (EXPECTED[p], actual[str(p)]) for p in EXPECTED if actual[str(p)] != EXPECTED[p]}
    if bad:
        raise RuntimeError(f"IMMUTABLE_INPUT_HOLD: {bad}")
    return actual


def old_model():
    spec = importlib.util.spec_from_file_location("frozen_a22_model", OLD_DIR / "model.py")
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    return model


def kernels(z, r=RAD):
    z = np.asarray(z, dtype=float)
    if not np.isfinite(z).all() or np.any(z <= 0):
        raise ValueError("positive finite reported z required")
    q = np.sqrt((1 + z) * (1 + r * z))
    kb = z / 2 * (1 + (1 + r + r * z) / (q + 1))
    kell = -(1 + z + q) / (2 * z)
    return kb, kell


def nuisance_transform():
    t = np.zeros((102, 96))
    t[18:102, :84] = np.eye(84)
    for j, index in enumerate((3, 4, 5, 9, 10, 11, 15, 16, 17)):
        t[index, 84 + j] = 1
    for j in range(3):
        t[[j, 6 + j, 12 + j], 93 + j] = 1
    return t


def response(e, z):
    kb, kell = kernels(z)
    return np.concatenate((kb[:, None, None] * e, kell[:, None, None] * e), axis=2)


def accumulate():
    """The only full 755850-row pass; frozen old G and b are never recomputed."""
    model = old_model()
    receipt = json.loads(STATS_RECEIPT.read_text())
    ref = (np.asarray(receipt["reference_center"]),
           np.asarray(receipt["reference_scale"]),
           np.asarray(receipt["vector_column_RMS"]))
    names = ["source_id", "redshift_quaia", "ra", "dec", "pmra_uasyr", "pmdec_uasyr",
             "pmra_error_uasyr", "pmdec_error_uasyr", "gaia_pmra_pmdec_corr"]
    names += ["template_" + name for name in model.CONFIG["templates"]]
    with np.load(CACHE, allow_pickle=False) as f:
        a = {name: f[name] for name in names}
    n = len(a["source_id"])
    if n != 755850:
        raise ValueError(f"unexpected retained row count {n}")
    A = np.zeros((6, 6)); K = np.zeros((6, 102)); qh = np.zeros(6)
    zmin = math.inf; zmax = -math.inf
    start_time = time.monotonic()
    for start in range(0, n, 4096):
        sl = slice(start, min(start + 4096, n))
        z = a["redshift_quaia"][sl]
        if not np.isfinite(z).all() or np.any(z <= 0):
            raise ValueError(f"invalid z in rows {start}:{sl.stop}")
        zmin = min(zmin, float(z.min())); zmax = max(zmax, float(z.max()))
        ra, dec = a["ra"][sl], a["dec"][sl]
        temp = np.column_stack([a["template_" + name][sl] for name in model.CONFIG["templates"]])
        x, _ = model.design(ra, dec, z, temp, ref)
        e = model.dipole(ra, dec)[:, :, :3]
        h = response(e, z)
        y = np.column_stack((a["pmra_uasyr"][sl], a["pmdec_uasyr"][sl]))
        sa = a["pmra_error_uasyr"][sl]
        sd = a["pmdec_error_uasyr"][sl]
        rho = a["gaia_pmra_pmdec_corr"][sl]
        if not all(np.isfinite(v).all() for v in (sa, sd, rho, y)) or np.any(sa <= 0) or np.any(sd <= 0) or np.any(np.abs(rho) >= 1):
            raise ValueError(f"invalid PM covariance/data in rows {start}:{sl.stop}")
        wx, wy = model.whiten(x, y, sa, sd, rho)
        wh, _ = model.whiten(h, y, sa, sd, rho)
        A += wh.T @ wh
        K += wh.T @ wx
        qh += wh.T @ wy
    np.savez_compressed(NEW_CACHE, A=A, K=K, qH=qh, n=n, zmin=zmin, zmax=zmax)
    return dict(A=A, K=K, qH=qh, n=n, zmin=zmin, zmax=zmax,
                seconds=time.monotonic() - start_time, new_moments_sha256=digest(NEW_CACHE))


def scaled_spectrum(m):
    d = np.diag(m)
    if not np.isfinite(m).all() or np.any(d <= 0):
        raise ArithmeticError("nonfinite or nonpositive diagonal")
    norm = m / np.sqrt(np.outer(d, d))
    eig = np.linalg.eigvalsh((norm + norm.T) / 2)
    rank = int(np.sum(eig > TAU * eig[-1]))
    condition = float(eig[-1] / eig[0]) if eig[0] > 0 else math.inf
    return norm, eig, rank, condition


def symmetry(m):
    residual = float(np.linalg.norm(m - m.T) / max(np.linalg.norm(m), 1))
    if residual > TAU:
        raise ArithmeticError(f"asymmetric moments {residual}")
    return (m + m.T) / 2, residual


def normalized_solver(m):
    """Cholesky solve in unit-diagonal coordinates, with no explicit inverse."""
    d = np.sqrt(np.diag(m))
    cf = cho_factor(m / np.outer(d, d), lower=True, check_finite=True)
    def solve(rhs):
        rhs = np.asarray(rhs)
        scaled = rhs / d if rhs.ndim == 1 else rhs / d[:, None]
        answer = cho_solve(cf, scaled)
        return answer / d if rhs.ndim == 1 else answer / d[:, None]
    return solve


def fit(moment):
    with np.load(STATS, allow_pickle=False) as old:
        G = old["G"].copy(); b = old["b"].copy()
        if int(old["n"]) != int(moment["n"]):
            raise ValueError("old and new row count differ")
    t = nuisance_transform()
    A, a_sym = symmetry(moment["A"])
    G, g_sym = symmetry(G)
    N, n_sym = symmetry(t.T @ G @ t)
    J = moment["K"] @ t
    bU = t.T @ b
    Nbar, ne, nr, nc = scaled_spectrum(N)
    if ne[0] <= 0 or nc > 1e10 or nr != 96:
        raise ArithmeticError(f"nuisance NUMERICALLY_UNRESOLVED: min={ne[0]}, condition={nc}, rank={nr}")
    nsolve = normalized_solver(N)
    NJt = nsolve(J.T)
    Nb = nsolve(bU)
    F, f_sym = symmetry(A - J @ NJt)
    s = moment["qH"] - J @ Nb
    Fbar, fe, fr, fc = scaled_spectrum(F)
    if fe[0] <= 0 or fc > 1e10 or fr != 6:
        raise ArithmeticError(f"six-profile NUMERICALLY_UNRESOLVED: min={fe[0]}, condition={fc}, rank={fr}")
    fsolve = normalized_solver(F)
    theta = fsolve(s)
    cov = fsolve(np.eye(6))
    cov, cov_sym = symmetry(cov)
    fbb, fbe, fee = F[:3, :3], F[:3, 3:], F[3:, 3:]
    fb = fbb - fbe @ normalized_solver(fee)(fbe.T)
    fb, fb_sym = symmetry(fb)
    cb = normalized_solver(fb)(np.eye(3))
    cb, cb_sym = symmetry(cb)
    cb_parity = float(np.linalg.norm(cb - cov[:3, :3]) / np.linalg.norm(cov[:3, :3]))
    # R Gaug R^T = F and covariance of its score estimator.
    Rmat = np.concatenate((np.eye(6), -NJt.T), axis=1)
    Gaug = np.block([[A, J], [J.T, N]])
    algebra = Rmat @ Gaug @ Rmat.T
    algebra_err = float(np.linalg.norm(algebra - F) / np.linalg.norm(F))
    cov_err = float(np.linalg.norm(cov @ algebra @ cov - cov) / np.linalg.norm(cov))
    # Fixed-design nuisance and H injection score shifts, no new row pass.
    shifts = [np.eye(96)[j] * (j + 1) / 7 for j in (0, 35, 83, 84, 90, 93, 95)]
    shift_errs = []
    for c in shifts:
        delta = fsolve((moment["K"] @ t) @ c - J @ nsolve(N @ c))
        shift_errs.append(float(np.linalg.norm(delta) / (1 + np.linalg.norm(theta))))
    signal = np.array([1.1, -2.2, 0.7, 3.3, -0.4, 1.2])
    recover = fsolve(F @ signal)
    signal_err = float(np.linalg.norm(recover - signal) / (1 + np.linalg.norm(signal)))
    annihilate = float(np.linalg.norm(Rmat @ np.concatenate((J, N), axis=0)) /
                       max(np.linalg.norm(Rmat) * np.linalg.norm(np.concatenate((J, N), axis=0)), 1))
    if max(cb_parity, algebra_err, cov_err, annihilate) > 1e-10 or max(shift_errs + [signal_err]) > 1e-9:
        raise ArithmeticError("estimator algebra/control failure")
    return dict(theta=theta, covariance=cov, F=F, score=s, Fbar=Fbar, Nbar=Nbar,
                normalized_F_eigenvalues=fe, normalized_N_eigenvalues=ne,
                normalized_F_condition=fc, normalized_N_condition=nc,
                normalized_F_rank=fr, normalized_N_rank=nr, profiled_b_information=fb,
                profiled_b_covariance=cb,
                controls=dict(A_symmetry=a_sym, old_G_symmetry=g_sym, N_symmetry=n_sym,
                              F_symmetry=f_sym, covariance_symmetry=cov_sym,
                              profiled_b_information_symmetry=fb_sym,
                              profiled_b_covariance_symmetry=cb_sym,
                              profiled_b_covariance_parity=cb_parity,
                              nuisance_annihilation=annihilate,
                              nuisance_shift_errors=shift_errs,
                              signal_recovery_error=signal_err,
                              score_covariance_identity=algebra_err,
                              estimator_covariance_identity=cov_err))


def angles(F):
    d = np.sqrt(np.diag(F)); f = F / np.outer(d, d)
    bb, be, ee = f[:3, :3], f[:3, 3:], f[3:, 3:]
    _, eb, rb, cb = scaled_spectrum(bb)
    _, el, rl, cl = scaled_spectrum(ee)
    _, ej, rj, cj = scaled_spectrum(f)
    result = dict(normalized_F6=f, marginal_b_eigenvalues=eb,
                  marginal_ell_eigenvalues=el, joint_eigenvalues=ej,
                  history_marginal_rank=rb, local_marginal_rank=rl, joint_rank=rj,
                  condition_marginal_b=cb, condition_marginal_ell=cl,
                  condition_column_normalized_F6=cj, numerical_rank_tau=TAU)
    if rb != 3 or rl != 3 or cb > 1e10 or cl > 1e10 or eb[0] <= 0 or el[0] <= 0:
        result["status"] = "PRINCIPAL_ANGLES_NOT_EVALUABLE_FOR_FULL_THREE_DIMENSIONAL_BLOCKS"
        return result
    rb_chol = np.linalg.cholesky(bb)
    re_chol = np.linalg.cholesky(ee)
    S = solve_triangular(rb_chol, be, lower=True)
    S = solve_triangular(re_chol, S.T, lower=True).T
    sv = np.linalg.svd(S, compute_uv=False)
    if np.any(sv < -TAU) or np.any(sv > 1 + TAU):
        result.update(status="NUMERICALLY_UNRESOLVED", principal_cosines_raw=sv)
        return result
    show = np.clip(sv, 0, 1)
    radians = np.arctan2(np.sqrt(np.maximum(0, (1 - show) * (1 + show))), show)
    schur = bb - be @ cho_solve(cho_factor(ee, lower=True), be.T)
    retention = np.linalg.eigvalsh(solve_triangular(rb_chol, solve_triangular(rb_chol, schur, lower=True).T, lower=True).T)
    retention_matrix = solve_triangular(rb_chol, solve_triangular(rb_chol, schur, lower=True).T, lower=True).T
    target_retention = np.eye(3) - S @ S.T
    identity_err = float(np.linalg.norm(retention_matrix - target_retention) / max(np.linalg.norm(target_retention), 1))
    orth_b = float(np.linalg.norm(solve_triangular(rb_chol, solve_triangular(rb_chol, bb, lower=True).T, lower=True).T - np.eye(3)))
    orth_e = float(np.linalg.norm(solve_triangular(re_chol, solve_triangular(re_chol, ee, lower=True).T, lower=True).T - np.eye(3)))
    result.update(status="ROUND_OFF_LIMITED" if 1 - sv[0] <= TAU or sv[0] > 1 else "EVALUATED",
                  principal_cosines_raw=sv, principal_cosines_display=show,
                  principal_angles_radians=radians, principal_angles_degrees=np.degrees(radians),
                  information_retention_factors=1 - sv**2,
                  retention_eigenvalues=retention,
                  condition_canonical_pair=None if 1 - sv[0] <= TAU else float((1 + sv[0]) / (1 - sv[0])),
                  canonical_pair_denominator_raw=float(1 - sv[0]),
                  orthonormality_residual_b=orth_b, orthonormality_residual_ell=orth_e,
                  schur_retention_residual=identity_err)
    if max(identity_err, orth_b, orth_e) > TAU:
        result["status"] = "NUMERICALLY_UNRESOLVED"
    return result


def physical_domain(theta, cov, zmax):
    ab, al = theta[:3], theta[3:]
    return dict(R_norm_ab_over_KH=float(R * np.linalg.norm(ab) / KH),
                one_plus_zmax_norm_ab_over_KH=float((1 + zmax) * np.linalg.norm(ab) / KH),
                observer_norm_ab_plus_al_over_KH=float(np.linalg.norm(ab + al) / KH),
                R_sigma_max_b_over_KH=float(R * np.sqrt(np.linalg.eigvalsh(cov[:3, :3])[-1]) / KH),
                formal_b=ab / KH, formal_ell=al / KH,
                interpretation="formal tangent coordinates only; no physical beta bound or posterior")


def serializable(obj):
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, (np.integer, np.floating)): return obj.item()
    if isinstance(obj, dict): return {k: serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [serializable(v) for v in obj]
    return obj


def main(reuse_moments=False):
    hashes = verify_inputs()
    if reuse_moments:
        with np.load(NEW_CACHE, allow_pickle=False) as f:
            moment = {k: f[k].copy() for k in f.files}
        moment["new_moments_sha256"] = digest(NEW_CACHE)
        moment["seconds"] = json.loads((HERE / "RUN_STDOUT.txt").read_text())["seconds"]
    else:
        moment = accumulate()
    fitted = fit(moment)
    angle = angles(fitted["F"])
    result = dict(owner="htt", packet_id="28d91672c82058fd380e24d6cd0281384e83a58df329159ad7fd72ae4979a88a",
                  task_id="K03", input_identity="sha256:cab18c33b87e10d5903a5babc763ff0bb59568d5290eb4bd7b6baabc6c2927d2",
                  claim_tier="C0_DERIVED_CONDITIONAL", transfer_source="analytic external-literature FLRW two-ray specialization; no native transfer",
                  sky_support_status="fixed 755850 selected Quaia Gaia-matched reported-z rows",
                  covariance_status="per-source 2x2 working blocks; residual cross-source spatial covariance unknown",
                  null_mock_status="small algebra controls only; no empirical coverage", original_K03_acceptance_met=False,
                  scientific_admission="HOLD", source_hashes=hashes, moments={k: v for k, v in moment.items() if k not in ("A", "K", "qH")},
                  fit=fitted, principal_angles=angle,
                  physical_domain=physical_domain(fitted["theta"], fitted["covariance"], moment["zmax"]))
    (HERE / "RESULT.json").write_text(json.dumps(serializable(result), indent=2, allow_nan=False) + "\n")
    print(json.dumps({"n": int(moment["n"]), "seconds": moment["seconds"], "theta": fitted["theta"].tolist(),
                      "F_condition": fitted["normalized_F_condition"], "angles_deg": serializable(angle.get("principal_angles_degrees")),
                      "physical_domain": serializable(result["physical_domain"]),
                      "new_moments_sha256": moment["new_moments_sha256"]}, allow_nan=False))


if __name__ == "__main__": main(reuse_moments="--reuse-moments" in sys.argv)
