"""Fixed, conditional nonlinear optical quotient on the sealed 274 rows."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
EXEC = HERE.parent
ROOT = HERE.parents[4]
INPUT = EXEC / "R24-OPTICAL-NONLINEAR-QUOTIENT_INPUT.json"
ROWS = EXEC.parent / "CONTINUOUS_RESEARCH_20261023/execution/R23-DISTANCE/RELEASED_ROWS.csv"
JOIN = EXEC / "distance/DIRECTION_JOIN.csv"
INPUT_SHA = "2267073c3678dc98ae63508efd80473ace82d150f7aa1c36246783110786ffa0"
STF = np.array([
    np.diag([1., -1., 0.]) / math.sqrt(2),
    np.diag([-1., -1., 2.]) / math.sqrt(6),
    [[0., 1/math.sqrt(2), 0.], [1/math.sqrt(2), 0., 0.], [0., 0., 0.]],
    [[0., 0., 1/math.sqrt(2)], [0., 0., 0.], [1/math.sqrt(2), 0., 0.]],
    [[0., 0., 0.], [0., 0., 1/math.sqrt(2)], [0., 1/math.sqrt(2), 0.]],
])
AMPLITUDES = (0., .01, .03, .1, .2, .3)
TAUS = (.5, 1., 2., 4.)
RADII = (0., 1e-4, 1e-3, 1e-2, .1, 1.)
ALPHA = .05
K = 5 / math.log(10)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources() -> dict:
    if sha(INPUT) != INPUT_SHA:
        raise ValueError("frozen input identity mismatch")
    task = json.loads(INPUT.read_text())
    observed = {}
    for source in task["sources"]:
        path = ROOT / source["path"]
        digest = sha(path)
        size = path.stat().st_size
        if digest != source["sha256"] or size != source["bytes"]:
            raise ValueError(f"frozen source identity mismatch: {source['path']}")
        observed[source["path"]] = {"sha256": digest, "bytes": size}
    return observed


def read_design() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], dict]:
    rows = list(csv.DictReader(ROWS.open(newline="")))
    joined = list(csv.DictReader(JOIN.open(newline="")))
    if len(rows) != 274 or len(joined) != 274:
        raise ValueError("274-row cache count mismatch")
    ids = [int(r["pgc"]) for r in rows]
    jids = [int(r["pgc"]) for r in joined]
    if len(set(ids)) != 274 or len(set(jids)) != 274 or set(ids) != set(jids):
        raise ValueError("PGC identity/uniqueness mismatch")
    lookup = {int(r["pgc"]): r for r in joined}
    ordered = [lookup[i] for i in ids]
    for r, j in zip(rows, ordered):
        expected_group = f"CF4:{r['group_label']}" if r["group_label"] != "UNASSIGNED" else f"UNASSIGNED_PGC:{r['pgc']}"
        if (j["group"] != expected_group or j["outcome"] != r["outcome"] or
                float(j["Vcmb_km_s"]) != float(r["vcmb_km_s"])):
            raise ValueError(f"cached join field mismatch PGC {r['pgc']}")
    if float(rows[ids.index(9031)]["vcmb_km_s"]) != 317:
        raise ValueError("PGC9031 velocity changed")
    angle = np.radians(np.array([[float(j["ra_J2000_deg"]), float(j["dec_J2000_deg"])] for j in ordered]))
    n = np.column_stack((np.cos(angle[:, 1])*np.cos(angle[:, 0]),
                         np.cos(angle[:, 1])*np.sin(angle[:, 0]), np.sin(angle[:, 1])))
    if np.max(np.abs(np.sum(n*n, axis=1)-1)) > 1e-12:
        raise ValueError("nonunit J2000 direction")
    if (np.max(np.abs(np.einsum("aij,bij->ab", STF, STF)-np.eye(5))) > 1e-12 or
            np.max(np.abs(np.trace(STF, axis1=1, axis2=2))) > 1e-12):
        raise ValueError("STF basis failed")
    v = np.array([float(r["vcmb_km_s"]) for r in rows])
    s = np.array([float(r["e_DMbest_mag"]) for r in rows])
    w = np.array([float(r["logWmxi"]) for r in rows])
    ew = np.array([float(r["e_logWmxi"]) for r in rows])
    if not (np.isfinite(v).all() and np.isfinite(s).all() and np.isfinite(w).all()
            and np.isfinite(ew).all() and np.all(v > 0) and np.all(s > 0)):
        raise ValueError("invalid covariate or modulus-error scale")
    stf = np.einsum("ni,aij,nj->na", n, STF, n)
    X = np.column_stack((np.ones(274), np.log10(v), w, ew, n, stf))
    X[:, 1:4] -= X[:, 1:4].mean(axis=0)
    scale = np.sqrt(np.mean(X*X, axis=0))
    if np.any(scale <= 0):
        raise ValueError("zero nuisance column scale")
    X /= scale
    meta = {"released_rows": len(rows), "selected_marks": 628, "undefined_moduli": 354,
            "selected_mark_count_source": "frozen R24 distance cohort contract; only released rows are read",
            "PGC9031_Vcmb_km_s": 317., "direction_sources": sorted(set(j["direction_source"] for j in ordered)),
            "nuisance_columns": ["1", "centered_log10_Vcmb", "centered_logWmxi", "centered_e_logWmxi",
                                 "n_x", "n_y", "n_z", "STF_1", "STF_2", "STF_3", "STF_4", "STF_5"],
            "column_RMS_before_scaling": scale.tolist()}
    return X, n, s, [j["group"] for j in ordered], meta


def fixed_directions() -> list[tuple[str, np.ndarray]]:
    diag = np.ones(3)/math.sqrt(3)
    vectors = [("+ex", np.array([1., 0., 0.])), ("-ex", np.array([-1., 0., 0.])),
               ("+ey", np.array([0., 1., 0.])), ("-ey", np.array([0., -1., 0.])),
               ("+ez", np.array([0., 0., 1.])), ("-ez", np.array([0., 0., -1.])),
               ("+diag", diag), ("-diag", -diag)]
    if max(abs(np.linalg.norm(d)-1) for _, d in vectors) > 1e-12:
        raise ValueError("fixed direction not unit")
    return vectors


def project(Q: np.ndarray, z: np.ndarray) -> np.ndarray:
    return z-Q@(Q.T@z)


def calculation() -> dict:
    source = sources()
    X, n, s, groups, cohort = read_design()
    directions = fixed_directions()
    x_all = [(name, n@d) for name, d in directions]
    scenarios = []
    controls = {"max_linear_scaled_projection": 0., "max_quadratic_scaled_projection": 0.,
                "max_cubic_legendre_scaled_difference": 0., "max_eigen_reference_abs_difference_d0sq": 0.,
                "max_antipodal_sum_abs_difference_mag": 0., "max_small_amplitude_bound_ratio": 0.,
                "factorizations_cholesky": 0, "templates": 0}
    z_alpha = float(norm.ppf(ALPHA))
    z80 = float(norm.ppf(.8))
    for ac, bc in ((0., 0.), (0., .29), (.055, 0.), (.055, .29)):
        V = np.diag(s*s-ac*ac)+ac*ac*np.ones((274, 274)) + bc*bc*np.equal.outer(groups, groups)
        if np.max(np.abs(np.diag(V)-(s*s+bc*bc))) > 1e-12:
            raise ValueError("covariance diagonal accounting")
        L = np.linalg.cholesky(V)
        controls["factorizations_cholesky"] += 1
        WX = solve_triangular(L, X, lower=True, check_finite=True)
        U, singular, _ = np.linalg.svd(WX, full_matrices=False)
        ranks = {str(t): int(np.sum(singular > t*singular[0])) for t in (1e-8, 1e-10, 1e-12)}
        if any(r != 12 for r in ranks.values()):
            raise ValueError(f"nuisance rank changed: {ranks}")
        Q = U[:, :12]
        eig, EV = np.linalg.eigh(V)
        if eig[0] <= 0:
            raise ValueError("covariance not SPD")
        Wnorm = 1/math.sqrt(float(eig[0]))
        rows = []
        for name, x in x_all:
            def pw(y: np.ndarray) -> np.ndarray:
                return project(Q, solve_triangular(L, y, lower=True, check_finite=False))
            p1, p2 = pw(x), pw(x*x)
            p3 = pw(x*x*x)
            legendre3 = (5*x*x*x-3*x)/2
            legendre_error = float(np.linalg.norm(p3-(2/5)*pw(legendre3))/max(1., np.linalg.norm(p3)))
            lin_error = float(np.linalg.norm(p1)/max(1., np.linalg.norm(solve_triangular(L, x, lower=True))))
            quad_error = float(np.linalg.norm(p2)/max(1., np.linalg.norm(solve_triangular(L, x*x, lower=True))))
            controls["max_linear_scaled_projection"] = max(controls["max_linear_scaled_projection"], lin_error)
            controls["max_quadratic_scaled_projection"] = max(controls["max_quadratic_scaled_projection"], quad_error)
            controls["max_cubic_legendre_scaled_difference"] = max(controls["max_cubic_legendre_scaled_difference"], legendre_error)
            if max(lin_error, quad_error) > 1e-10 or legendre_error > 1e-10:
                raise ValueError("linear/quadratic absorption or cubic identity failed")
            small = []
            for a in (.001, .002):
                sf = pw(-K*np.log1p(-a*x))
                cubic = (K*a**3/3)*p3
                error = float(np.linalg.norm(sf-cubic))
                bound = Wnorm*math.sqrt(274)*K*a**4/(4*(1-a))+1e-12*max(1., np.linalg.norm(sf))
                if error > bound:
                    raise ValueError("small-amplitude cubic remainder bound failed")
                controls["max_small_amplitude_bound_ratio"] = max(controls["max_small_amplitude_bound_ratio"], error/bound)
                small.append({"amplitude": a, "d0": float(np.linalg.norm(sf)),
                              "cubic_leading_d0": float(np.linalg.norm(cubic)),
                              "cubic_error": error, "rigorous_remainder_bound": bound,
                              "d0_over_a_cubed": float(np.linalg.norm(sf))/a**3})
            for a in AMPLITUDES:
                q = a*x
                if np.min(1-q) < .7-1e-14:
                    raise ValueError("finite-q positivity domain failed")
                f = -K*np.log1p(-q)
                sf = pw(f)
                d0 = float(np.linalg.norm(sf))
                e = L@sf
                reference_weighted = (EV/np.sqrt(eig)) @ EV.T
                ref_X = reference_weighted@X
                ref_U, ref_s, _ = np.linalg.svd(ref_X, full_matrices=False)
                if int(np.sum(ref_s > 1e-10*ref_s[0])) != 12:
                    raise ValueError("independent eigen-whitening rank changed")
                ref_z = reference_weighted@f
                ref_dsq = float(np.linalg.norm(project(ref_U[:, :12], ref_z))**2)
                d2 = d0*d0
                diff = abs(ref_dsq-d2)
                controls["max_eigen_reference_abs_difference_d0sq"] = max(controls["max_eigen_reference_abs_difference_d0sq"], diff)
                if not np.isclose(ref_dsq, d2, rtol=1e-9, atol=1e-10):
                    raise ValueError("independent eigen-whitening reference mismatch")
                noise = [{"tau": tau, "oracle_power": float(norm.cdf(z_alpha+d0/tau)),
                          "remainder_power": [{"rho": rho,
                              "maximin_power": float(norm.cdf(z_alpha+max(0., d0-2*rho)/tau))}
                                              for rho in RADII]}
                         for tau in TAUS]
                if a == 0 and (d0 > 1e-12 or any(abs(item["oracle_power"]-.05) > 1e-12 for item in noise)):
                    raise ValueError("zero-signal size failed")
                for item in noise:
                    powers = [b["maximin_power"] for b in item["remainder_power"]]
                    if (any(powers[i+1] > powers[i]+1e-12 for i in range(len(powers)-1)) or
                            powers[0] < .05-1e-12 or powers[-1] > item["oracle_power"]+1e-12):
                        raise ValueError("remainder monotonicity failed")
                if any(noise[i+1]["oracle_power"] > noise[i]["oracle_power"]+1e-12 for i in range(3)):
                    raise ValueError("noise monotonicity failed")
                midpoint = .5*sf
                if max(np.linalg.norm(midpoint), np.linalg.norm(sf-midpoint)) > d0/2+1e-12:
                    raise ValueError("shared midpoint overlap witness failed")
                rows.append({"direction": name, "amplitude": a, "d0": d0,
                             "d0_squared": d2, "eigen_reference_d0_squared": ref_dsq,
                             "residual_fraction": float(d0/np.linalg.norm(solve_triangular(L, f, lower=True))) if a else 0.,
                             "e_RMS_mag": float(np.sqrt(np.mean(e*e))),
                             "e_max_abs_mag": float(np.max(np.abs(e))),
                             "tau80": d0/(z80-z_alpha), "noise": noise,
                             "overlap_rho_star": d0/2,
                             "shared_midpoint_witness": {"projected_whitened_midpoint": midpoint.tolist(),
                                  "definition": "s_f/2; null remainder +midpoint, alternative remainder -midpoint",
                                  "null_remainder_norm": float(np.linalg.norm(midpoint)),
                                  "alternative_remainder_norm": float(np.linalg.norm(midpoint-sf)),
                                  "benchmark_maximin_power_at_overlap": .05},
                             "cubic_leading_d0": float(np.linalg.norm((K*a**3/3)*p3)),
                             "small_amplitude_controls": small if a == .01 else None})
                controls["templates"] += 1
        scenarios.append({"calibration_ac_mag": ac, "group_bc_mag": bc,
                          "covariance_min_eigenvalue": float(eig[0]),
                          "covariance_diag_max_error": float(np.max(np.abs(np.diag(V)-(s*s+bc*bc)))),
                          "nuisance_ranks": ranks, "nuisance_singular_values": singular.tolist(), "rows": rows})
    controls["unique_fixed_templates"] = 48
    if controls["factorizations_cholesky"] != 4 or controls["templates"] != 48*4:
        raise ValueError("factorization/template accounting failed")
    # Antipodal scalar identity at q=0.1, for source direction exactly parallel to d.
    anti = -K*(math.log1p(-.1)+math.log1p(.1))
    controls["antipodal_q01_sum_mag"] = anti
    controls["max_antipodal_sum_abs_difference_mag"] = abs(anti-.021824027012250224)
    if controls["max_antipodal_sum_abs_difference_mag"] > 1e-12:
        raise ValueError("antipodal nonlinear witness failed")
    return {"task_id": "R24-OPTICAL-NONLINEAR-QUOTIENT", "input_sha256": INPUT_SHA,
            "source_identities": source, "cohort": cohort,
            "owner": "HTT conditional observational design", "claim_tier": "C0_CONDITIONAL",
            "response": "exact in q within leading-low-z zero-shear law; no finite-z physical remainder bound",
            "law": "Y=Xbeta+f+epsilon, epsilon~N(0,tau^2 V), tau hypothetical known",
            "covariance": "V=diag(s^2-ac^2)+ac^2 11T+bc^2 GGt",
            "cubic": "P_X W x=P_X W x^2=0; P_X W x^3=(2/5)P_X W P3(x); s_f=(2 K a^3/15)P_X W P3(x)+O(a^4)",
            "remainder": "same projected whitened Euclidean ball of radius rho under each hypothesis; rho scenarios are not measured physical bounds",
            "physical_remainder_status": "UNRESTRICTED; PHYSICAL_ATTRIBUTION_VACUOUS",
            "original_acceptance_promoted": False, "original_acceptance": "UNCHANGED_17_OF_42_EXTERNAL_OR_18_OF_42_ANALYTIC_ALTERNATE",
            "transfer_source": "none", "alpha_one_sided": ALPHA,
            "directions": [name for name, _ in directions], "amplitudes": list(AMPLITUDES),
            "tau_hypothetical": list(TAUS), "rho_hypothetical": list(RADII),
            "scenarios": scenarios, "controls": controls,
            "environment": {"python": platform.python_version(), "executable": sys.executable,
                            "numpy": np.__version__}}


def main() -> None:
    result = calculation()
    (HERE/"RESULT.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"scenarios": len(result["scenarios"]), "controls": result["controls"]}, indent=2))


if __name__ == "__main__":
    main()
