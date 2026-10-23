"""R24 conditional same-cohort angular/velocity-response geometry.

The response dictionary is fixed from directions and velocities before reading
the modulus vector. No column in this file is an observer-frame transformation.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import solve_triangular
from scipy.stats import chi2, ncx2

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
DISTANCE = PARENT / "distance"
INPUT = PARENT / "R24-BOOST-ACCELERATION_INPUT.json"
INPUT_SHA = "feafebb499efb65f229cf015f8cf6478120cf86d2964d15d52206a3741670a2d"
PACKET = "047ec280a16abca82ba9e122a7b16664db1f8c905dae0ec55f3611c78427997f"
TASK = "R24-BOOST-ACCELERATION"
THRESHOLDS = (1e-8, 1e-10, 1e-12)
SCENARIOS = ((0.0, 0.0), (0.0, 0.29), (0.055, 0.0), (0.055, 0.29))

EXPECTED = {
    INPUT: INPUT_SHA,
    PARENT / "ADVISED_CONTRACTS.json": "9bd712d298f572e797731b359e8810ab89f902d9c5bd2879810b49895951b4bf",
    DISTANCE / "ARTIFACT_MANIFEST.json": "1e1e0b6fabdc535bae1060b1ba3d1c61b2b1302001119c67d4a43f035dec521b",
    DISTANCE / "RESULT.json": "330066f4a8605caa9874f192a938d4ef1d84cf8933bdd3e6059a40b011c28bd0",
    DISTANCE / "DIRECTION_JOIN.csv": "4e6e9c991ecdf2fda2a403f68a4ea5d744e244c73478eef1c70efbf007852b9a",
    DISTANCE / "OOF_ROWS.csv": "6fd8356e041e1ece186b79bf1506b04af5411e17e6c31a489a1f66da977a3c40",
    PARENT / "DISTANCE_REVIEW_RAW.json": "4305359f1f25203ecd8bc4a184a18703e4ac63785837686e3f8ce61d8e4e8a1d",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def checked_sources():
    for path, expected in EXPECTED.items():
        actual = digest(path)
        if actual != expected:
            raise ValueError(f"frozen source identity mismatch: {path}: {actual}")
    manifest = json.loads((DISTANCE / "ARTIFACT_MANIFEST.json").read_text())
    for entry in manifest["files"]:
        path = DISTANCE / entry["path"]
        if digest(path) != entry["sha256"]:
            raise ValueError(f"distance artifact identity mismatch: {path}")
    spec = importlib.util.spec_from_file_location("r24_distance_analysis", DISTANCE / "analyze.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def normalized_qr(x):
    q, r = np.linalg.qr(x, mode="reduced")
    if np.min(np.abs(np.diag(r))) <= 1e-12 * np.linalg.norm(x, ord=2):
        raise ValueError("non-full-rank block in normalized QR")
    return q


def residual(x, q):
    return x - q @ (q.T @ x)


def svd_report(x, names):
    scales = np.linalg.norm(x, axis=0)
    if np.any(scales == 0):
        raise ValueError("zero nuisance-profiled response column")
    _, s, vh = np.linalg.svd(x / scales, full_matrices=False)
    ranks = {f"{t:g}": int(np.sum(s > t * s[0])) for t in THRESHOLDS}
    rank = ranks["1e-10"]
    return {"columns": names, "column_norms_whitened_profiled": scales.tolist(),
            "singular_values_column_normalized": s.tolist(), "rank": rank,
            "rank_sensitivity": ranks, "nullspace_column_normalized": vh[rank:].tolist(),
            "null_residual_norm_max": float(np.linalg.norm((x / scales) @ vh[rank:].T, axis=0).max()) if rank < len(names) else 0.0}


def conditional_fit(yw, base_q, block, names):
    z = residual(block, base_q)
    yr = residual(yw, base_q)
    beta = np.linalg.lstsq(z, yr, rcond=1e-12)[0]
    info = z.T @ z
    cov = np.linalg.inv(info)
    improvement = float(beta @ info @ beta)
    return {"columns": names, "coefficient_raw_units": beta.tolist(),
            "coefficient_covariance_fixed_working_V": cov.tolist(),
            "information_conditional": info.tolist(),
            "delta_working_chi2": improvement,
            "normal_residual_relative": float(np.linalg.norm(z.T @ (yr-z@beta)) / max(1., np.linalg.norm(z)*np.linalg.norm(yr)))}


def canonical_angles(a, b):
    qa, qb = normalized_qr(a), normalized_qr(b)
    cosine = np.linalg.svd(qa.T @ qb, compute_uv=False)
    cosine = np.clip(cosine, 0, 1)
    return {"cosine": cosine.tolist(), "degrees": np.degrees(np.arccos(cosine)).tolist()}


def t1_synthetic_witness():
    c = 299792458.0
    epsilon = 2.0  # synthetic energy density, J/m^3
    p = np.diag([0.5, 1.0, 3.0])  # J/m^3; PSD
    g = np.array([1.0, -2.0, 0.7]) * 1e-27  # J/m^4
    dp = np.diag([0.04, -0.03, 0.02])
    dg = np.array([0.02, -0.01, 0.03]) * 1e-27
    m = epsilon*np.eye(3)+p
    a = -c*c*np.linalg.solve(m, g)
    shifted = -c*c*np.linalg.solve(m+dp, g+dg)
    minimum = float(np.linalg.eigvalsh(m).min())
    eta = float(np.linalg.norm(dp, 2))
    radius = float(np.linalg.norm(dg))
    bound = c*c*(radius/(minimum-eta)+eta*np.linalg.norm(g)/(minimum*(minimum-eta)))
    error = float(np.linalg.norm(shifted-a))
    if not (np.linalg.eigvalsh(p).min() >= 0 and eta < minimum and error <= bound*(1+1e-12)):
        raise AssertionError("T1 synthetic bound failed")
    return {"status": "SYNTHETIC_ALGEBRAIC_WITNESS_ONLY", "frame": "conserved_energy_frame_q_zero",
            "epsilon_J_m3": epsilon, "P_J_m3": p.tolist(), "g_J_m4": g.tolist(),
            "delta_P_J_m3": dp.tolist(), "delta_g_J_m4": dg.tolist(),
            "A_m_s2": a.tolist(), "perturbation_error_m_s2": error,
            "perturbation_bound_m_s2": bound, "epsilon_plus_P_min_eigen_J_m3": minimum}


def compute():
    distance = checked_sources()
    rows, ledger, ids, groups, folds, _, coords, n = distance.load()
    y, errors, v, features = distance.features(rows, n)
    if len(rows) != 274 or len(ledger) != 628 or min(v) != 317.0:
        raise ValueError("frozen 274/628 cohort or 317 km/s row changed")
    # Frozen response basis. Depth is velocity, not a source-fitted kernel.
    vref = float(np.median(v))
    t = np.log10(v / vref)
    angular = n
    flow = (-5.0/(math.log(10.0)*v))[:,None]*n
    depth = np.column_stack((n, t[:,None]*n, (t*t)[:,None]*n))
    stf = np.column_stack([features[name] for name in distance.STF_NAMES])
    nuisance = np.column_stack((np.ones(274), np.log10(v),
                                features["measured_logWmxi"], features["e_logWmxi"], stf))
    nuisance_names = distance.BASE_NAMES + distance.STF_NAMES
    c_names = [f"constant_n_{x}" for x in "xyz"]
    k_names = [f"K_n_{x}_km_s" for x in "xyz"]
    d_names = [f"t_power_{power}_n_{x}" for power in range(3) for x in "xyz"]
    unique = np.column_stack((nuisance, angular, flow, depth[:,3:]))
    unique_names = nuisance_names+c_names+k_names+d_names[3:]
    out = {
        "task_id": TASK, "packet_id": PACKET, "input_identity": f"sha256:{INPUT_SHA}",
        "owner": "HTT observational method", "scope": "same 274-row conditional response quotient",
        "claim_tier": "C0_CONDITIONAL_DIAGNOSTIC", "transfer_source": "none",
        "scientific_admission": "HOLD", "original_acceptance": "UNCHANGED_17_OF_42_EXTERNAL_18_OF_42_ANALYTIC_ALTERNATE",
        "cohort": {"released": 274, "selected": 628, "undefined": 354,
                   "min_Vcmb_km_s": float(min(v)), "max_Vcmb_km_s": float(max(v)),
                   "PGC_9031_present": ids.count(9031) == 1, "covariance_scenarios": 4},
        "response_dictionary_fixed_before_y": {"n_frame": "J2000_equatorial_unit_source_direction",
            "V_frame": "CMB_frame_released_radial_velocity_km_s",
            "constant": "n_i; coefficient mag",
            "flow": "K_i n_i, K_i=-5/(ln(10) Vcmb_i); coefficient km/s, low-z conditional",
            "depth": "[n_i,t_i n_i,t_i^2 n_i], t_i=log10(Vcmb_i/median(Vcmb)); coefficients mag",
            "v_reference_median_km_s": vref,
            "nuisance": nuisance_names,
            "STF": "five Frobenius-orthonormal n:S_a:n columns; profiled with all baseline nuisance",
            "velocity_only_is_not_full_observer_boost": True},
        "exact_optical_relation": {"premises": "one smooth source/emitter energy congruence, regular low-z vertex, fixed positive H, source-pointing n, same frame",
            "delta_mu_acceleration": "(5/ln(10))*A.n/(c*H)",
            "angular_calibration_equivalent": "d.n with d=(5/ln(10))*A/(c*H) mag",
            "identifiability": "EXACTLY_DEGENERATE_AT_FIXED_H; do not jointly estimate d and A",
            "units": "A m/s^2, c m/s, H 1/s, d mag; dimensionless ratio multiplied by magnitude coefficient",
            "H_input": "MISSING; no physical A estimate"},
        "t1": t1_synthetic_witness(), "scenarios": {},
        "required_observable": {"energy_frame_epsilon_P_g": "MISSING",
            "tracer_to_matter_map": "MISSING", "finite_z_remainder": "MISSING",
            "full_observer_boost_redshift_distance_angle_map": "MISSING",
            "physically_qualified_calibration_PV_covariance": "MISSING"},
    }
    for a,b in SCENARIOS:
        cov = distance.covariance(errors, groups, a, b)
        L = np.linalg.cholesky(cov)
        white = lambda x: solve_triangular(L, x, lower=True, check_finite=False)
        nw, cw, kw, dw = map(white, (nuisance, angular, flow, depth))
        yw = white(y)
        nq = normalized_qr(nw)
        cr, kr, dr = (residual(block, nq) for block in (cw, kw, dw))
        cq = normalized_qr(cr)
        dq = normalized_qr(dr)
        union = np.column_stack((cr,kr,dr))
        s = svd_report(union,c_names+k_names+d_names)
        if s["rank_sensitivity"] != {"1e-08": 12, "1e-10": 12, "1e-12": 12}:
            raise AssertionError(f"unexpected full response rank: {s['rank_sensitivity']}")
        full = white(unique)
        fu, fs, fvh = np.linalg.svd(full, full_matrices=False)
        if fs[-1] <= 1e-12*fs[0]:
            raise AssertionError("full unique model nonidentifiable")
        full_beta = fvh.T @ ((fu.T @ yw)/fs)
        full_cov = (fvh.T/(fs*fs))@fvh
        full_residual = yw-full@full_beta
        if np.linalg.norm(full.T@full_residual)/max(1.,np.linalg.norm(full)*np.linalg.norm(yw)) > 1e-10:
            raise AssertionError("full normal equations failed")
        fit_c = conditional_fit(yw,nq,cw,c_names)
        fit_k = conditional_fit(yw,nq,kw,k_names)
        fit_d = conditional_fit(yw,nq,dw,d_names)
        fit_k_c = conditional_fit(yw,np.column_stack((nq,cq)),kw,k_names)
        fit_k_d = conditional_fit(yw,np.column_stack((nq,dq)),kw,k_names)
        kc = np.array(fit_k_c["information_conditional"])
        kd = np.array(fit_k_d["information_conditional"])
        cutoff = float(chi2.ppf(.95,3))
        def power(info):
            eigen = np.linalg.eigvalsh(info)
            lam = (30.0**2)*eigen
            return {"amplitude_km_s": 30.0, "min_to_max_eigen_ncp": lam.tolist(),
                    "power_range_alpha_0p05": [float(ncx2.sf(cutoff,3,x)) for x in (lam[0],lam[-1])],
                    "status": "WORKING_GAUSSIAN_ONLY_NO_PHYSICAL_POWER_OR_COVERAGE"}
        key = f"a_{a:.3f}_b_{b:.3f}"
        out["scenarios"][key] = {"covariance": {"a_mag":a,"b_mag":b,
              "min_cholesky_pivot_mag":float(np.diag(L).min())},
          "nuisance_profiled_response_svd": s,
          "exact_nullspace_relation": "constant_n_x/y/z equals depth t_power_0_n_x/y/z",
          "canonical_K_vs_constant": canonical_angles(kr,cr),
          "canonical_K_vs_depth": canonical_angles(kr,dr),
          "conditional_fits": {"constant_given_nuisance":fit_c,"K_given_nuisance":fit_k,
                               "depth_given_nuisance":fit_d,
                               "K_given_constant_and_nuisance":fit_k_c,
                               "K_given_depth_and_nuisance":fit_k_d},
          "full_unique_joint_fit": {"columns":unique_names,"coefficient_raw_units":full_beta.tolist(),
              "coefficient_covariance_fixed_working_V":full_cov.tolist(),
              "full_vector_STF_and_crossblocks_retained":True,
              "minimum_relative_singular_value_raw_whitened":float(fs[-1]/fs[0])},
          "conditional_30km_s_K_power": {"after_constant":power(kc),"after_depth":power(kd)}}
    return out


def figure(result):
    scenarios = list(result["scenarios"])
    fig, axes = plt.subplots(1,2,figsize=(11,4.3),layout="constrained")
    x = np.arange(len(scenarios))
    for label,field,color in (("K vs constant","canonical_K_vs_constant","#245f87"),
                              ("K vs fixed depth","canonical_K_vs_depth","#a23b33")):
        angles = [min(result["scenarios"][s][field]["degrees"]) for s in scenarios]
        axes[0].plot(x,angles,"o-",label=label,color=color)
    axes[0].set_ylabel("smallest canonical angle (degrees)")
    axes[0].set_title("After baseline and full STF profiling")
    axes[0].legend()
    for label,field,color in (("after constant","after_constant","#245f87"),
                              ("after fixed depth","after_depth","#a23b33")):
        lo=[result["scenarios"][s]["conditional_30km_s_K_power"][field]["power_range_alpha_0p05"][0] for s in scenarios]
        hi=[result["scenarios"][s]["conditional_30km_s_K_power"][field]["power_range_alpha_0p05"][1] for s in scenarios]
        axes[1].fill_between(x,lo,hi,alpha=.18,color=color)
        axes[1].plot(x,lo,"o-",color=color,label=label+" minimum")
    axes[1].set_ylim(.045,.10)
    axes[1].set_ylabel("conditional level-0.05 Gaussian power")
    axes[1].set_title("30 km/s response scenario; physical law HOLD")
    for ax in axes:
        ax.set_xticks(x,scenarios,rotation=20,ha="right")
        ax.grid(alpha=.25)
    axes[1].legend(fontsize=8)
    fig.savefig(HERE/"RESPONSE_GEOMETRY.png",dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    answer=compute()
    (HERE/"RESULT.json").write_text(json.dumps(answer,indent=2,allow_nan=False)+"\n")
    figure(answer)
    print(json.dumps({"task":TASK,"cohort":answer["cohort"],
        "angles_and_power":{s:{"K_constant_deg":r["canonical_K_vs_constant"]["degrees"],
                                "K_depth_deg":r["canonical_K_vs_depth"]["degrees"],
                                "power_after_constant":r["conditional_30km_s_K_power"]["after_constant"]["power_range_alpha_0p05"],
                                "power_after_depth":r["conditional_30km_s_K_power"]["after_depth"]["power_range_alpha_0p05"]}
                            for s,r in answer["scenarios"].items()}},indent=2))
