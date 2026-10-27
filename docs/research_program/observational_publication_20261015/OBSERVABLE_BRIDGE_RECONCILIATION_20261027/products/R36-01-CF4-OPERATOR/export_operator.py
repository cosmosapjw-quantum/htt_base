"""Source-bound, fixed-weight export of the original H03 four-window QR map.

This constructs A from the frozen selected rows. It does not invoke the H03
producer, refit sensitivity banks, or estimate an empirical CF4 likelihood.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.linalg import qr, solve_triangular, svdvals

REPO = Path(__file__).resolve().parents[6]
SOURCE = REPO / "docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz"
H03 = REPO / "docs/research_program/observational_publication_20261015/H03_20261016"
SAVED = H03 / "results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json"
GAUGE = H03 / "results/source_h03_v1/H03_MEAN_GAUGE.json"
EXPECTED = {
    SOURCE: "86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c",
    SAVED: "5d31e2ab4fea682c538c31c15181ae7b07e11efba98b36c66aff6feca88f8326",
    GAUGE: "c4ea98f7b80b0f47ee649a727999b5450373c554327e3b21412b2e6ab7d0a4c9",
    H03 / "src/h03_tomography.py": "1c7fe777e3f44183f501e599877964aa212912b0c8c78c905e0aa9404ac03d40",
    H03 / "src/run_h03.py": "dd6554623e18db399d310d0bdb17b3e393a3998f1b859779f15ff9e64703007c",
    H03 / "src/h03_method_gauge.py": "13f9dd8e5be1ae33cd9c1d438f4e46a74fbf6b5c73c7d83e021dd6c6ab6dcf14",
    H03 / "docs/H03_RUN_RECEIPT.json": "e13eaacbc23c5d44d517cae068bfd7e286fb9c9797b01da9f42b2dfb20edff06",
}
CENTERS = (0.025, 0.04, 0.06, 0.08)
METHODS = ("FP", "OTHER", "SN", "TF")
C_KM_S = 299792.458
STF = np.array([
    [[1, 0, 0], [0, -1, 0], [0, 0, 0]],
    [[1, 0, 0], [0, 1, 0], [0, 0, -2]],
    [[0, 1, 0], [1, 0, 0], [0, 0, 0]],
    [[0, 0, 1], [0, 0, 0], [1, 0, 0]],
    [[0, 0, 0], [0, 0, 1], [0, 1, 0]],
], dtype=float) / np.array([np.sqrt(2), np.sqrt(6), np.sqrt(2), np.sqrt(2), np.sqrt(2)])[:, None, None]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print("PASS", label, flush=True)


def source_arrays() -> dict:
    for path, expected in EXPECTED.items():
        check(path.is_file() and digest(path) == expected, "immutable source " + path.name)
    with np.load(SOURCE, allow_pickle=False) as z:
        keys = ("z_CMB", "dmzp", "e_dmzp", "n_J2000", "method_family", "group_id")
        check(set(keys) <= set(z.files), "source columns")
        a = {k: z[k].copy() for k in keys}
    z, mu, emu, n, method, ids = (a[k] for k in keys)
    check(z.shape == mu.shape == emu.shape == method.shape == ids.shape == (35970,)
          and n.shape == (35970, 3), "exact row count and shapes")
    check(len(np.unique(ids)) == len(ids), "unique ordered group IDs")
    check(all(np.isfinite(v).all() for v in (z, mu, emu, n))
          and np.all((z > 0) & (z < 0.2)) and np.all(emu > 0)
          and np.all((mu >= 20) & (mu <= 60)), "finite physical input bounds")
    check(np.max(np.abs(np.sum(n*n, axis=1)-1)) <= 5e-12, "ICRS unit directions")
    check(set(np.unique(method)) == set(METHODS), "four original methods")
    return a


def matrices(a: dict):
    z, mu, emu, n = (a[k] for k in ("z_CMB", "dmzp", "e_dmzp", "n_J2000"))
    d = 10.0**((mu-25.0)/5.0)
    sigma = np.hypot(250.0, 70.0*(np.log(10.0)/5.0)*d*emu)
    y = C_KM_S*z
    stf = np.einsum("ni,aij,nj->na", n, STF, n, optimize=True)
    X = d[:, None]*np.column_stack((np.ones(len(d)), n, stf))
    return d, sigma, y, X


def export(product: Path, external: Path) -> None:
    a = source_arrays()
    gram = np.einsum("aij,bij->ab", STF, STF)
    check(float(np.linalg.norm(gram-np.eye(5))) <= 1e-12, "STF basis Frobenius normalization")
    d, sigma, y, X = matrices(a)
    saved = json.loads(SAVED.read_text())
    gauge = json.loads(GAUGE.read_text())
    check(saved["source_SHA256"] == EXPECTED[SOURCE]
          and gauge["source_sha256"] == EXPECTED[SOURCE]
          and saved["source_groups"] == 35970, "saved source binding")
    check(tuple(saved["four_gaussian_window_centers"]) == CENTERS
          and saved["width_z"] == 0.012, "saved window binding")
    theta_ref = np.array([v["theta9"] for v in saved["monopole_dipole_STF2_windows"]]).reshape(36)
    C_ref = np.asarray(saved["joint_covariance_36x36"], float)
    blocks, qzs, identities, bulk_errors, gauge_rows = [], [], [], [], []
    for i, center in enumerate(CENTERS):
        w = np.exp(-0.5*((a["z_CMB"]-center)/0.012)**2)/sigma**2
        s = np.sqrt(w)
        q, r = qr(s[:, None]*X, mode="economic", check_finite=False)
        cond = svdvals(r)[0]/svdvals(r)[-1]
        check(np.isfinite(cond) and cond < 1e9, f"QR condition window {i}")
        A = solve_triangular(r, q.T, check_finite=False)*s[None, :]
        identity = float(np.max(np.abs(A@X-np.eye(9))))
        check(identity <= 1e-9, f"A X identity window {i}")
        identities.append(identity)
        check(np.allclose(A@y, theta_ref[i*9:(i+1)*9], rtol=1e-10, atol=1e-8),
              f"saved theta parity window {i}")
        bulk = A@a["n_J2000"]
        ref_bulk = np.asarray(saved["monopole_dipole_STF2_windows"][i]
                              ["bulk_velocity_design_response_9x3_per_Mpc"])
        err = float(np.max(np.abs(bulk-ref_bulk)))
        check(np.allclose(bulk, ref_bulk, rtol=1e-10, atol=1e-10),
              f"saved bulk response window {i}")
        bulk_errors.append(err)
        selector = np.zeros((9, 3)); selector[1:4, :] = np.eye(3)
        check(np.max(np.abs(A@(d[:, None]*a["n_J2000"])-selector)) <= 1e-9,
              f"distance-weighted dipole selector window {i}")
        Z = np.column_stack([d*(a["method_family"] == m) for m in METHODS])
        Qz, _ = qr(s[:, None]*Z, mode="economic", check_finite=False)
        joined = s[:, None]*np.column_stack((X, Z))
        joined_sv = svdvals(joined)
        projected = s[:, None]*X-Qz@(Qz.T@(s[:, None]*X))
        projected_sv = svdvals(projected)
        joined_rank = int(np.sum(joined_sv > joined_sv[0]*1e-10))
        projected_rank = int(np.sum(projected_sv > projected_sv[0]*1e-10))
        residual = float(np.linalg.norm(X[:, 0]-Z.sum(axis=1))/max(1, np.linalg.norm(X[:, 0])))
        check(joined_rank == 12 and projected_rank == 8 and residual <= 1e-12,
              f"separate four-method gauge window {i}")
        check(gauge["windows"][i]["mean_design_rank"] == joined_rank
              and gauge["windows"][i]["remaining_theta_rank"] == projected_rank,
              f"saved gauge parity window {i}")
        gauge_rows.append({"center": center, "joined_rank": joined_rank,
                           "projected_theta_rank": projected_rank,
                           "monopole_method_identity_relative": residual,
                           "nuisance_representation": "Pperp(v)=v-Qz@(Qz.T@v) in whitened row space"})
        blocks.append(A); qzs.append(Qz)
    A = np.concatenate(blocks, axis=0)
    AN = A@a["n_J2000"]
    C = (A*sigma[None, :])@(A*sigma[None, :]).T
    C = 0.5*(C+C.T)
    theta = A@y
    check(np.allclose(theta, theta_ref, rtol=1e-10, atol=1e-8), "full saved theta36 parity")
    check(np.allclose(C, C_ref, rtol=1e-9, atol=1e-10), "full saved covariance36 parity")
    cross = C[:9, 9:18]
    check(np.max(np.abs(cross)) > 1e-6, "nonzero inherited cross-window covariance")
    eig = np.linalg.eigvalsh(C)
    psd_tol = 64*np.finfo(float).eps*36*max(1, np.linalg.norm(C, 2))
    check(float(eig[0]) >= -psd_tol, "full covariance PSD at roundoff bound")
    response = np.column_stack((AN, -AN))
    h = np.array([17.0, -23.0, 31.0])  # deterministic velocity control, km/s
    check(np.max(np.abs(response@np.r_[h,h])) <= 1e-12
          and np.allclose(response@np.r_[h,np.zeros(3)], AN@h, rtol=0, atol=1e-12)
          and np.allclose(response@np.r_[np.zeros(3),h], -(AN@h), rtol=0, atol=1e-12)
          and np.linalg.matrix_rank(response) == np.linalg.matrix_rank(AN),
          "opposite source/observer response has common-mode null")
    # A stale operator must reject a different row order even when y retains its values.
    permuted = y[::-1]
    permuted_delta = float(np.max(np.abs(A@permuted-theta_ref)))
    check(not np.allclose(A@permuted, theta_ref, rtol=1e-10, atol=1e-8),
          "permuted source rows falsify saved parity")
    product.mkdir(parents=True, exist_ok=True)
    external.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(external/"A_RAW_36x35970.npz", A_raw=A, AN=AN,
        Qz_whitened=np.stack(qzs), group_id=a["group_id"], theta36=theta,
        covariance36=C, sigma=sigma,
        source_sha256=np.array(EXPECTED[SOURCE]))
    artifact = external/"A_RAW_36x35970.npz"
    result = {
        "schema": "htt.r36.cf4_exact_operator/1", "task_id": "R36-01-CF4-OPERATOR",
        "status": "PROPOSED_PENDING_INDEPENDENT_REVIEW", "owner": "obsstat",
        "claim_tier": "DIAGNOSTIC_ONLY_CONDITIONAL_FIXED_WEIGHT",
        "transfer_source": "empirical_proxy", "source_groups": 35970,
        "source_row_order": "unchanged NPZ order; all unique group_id retained externally",
        "source_sha256": EXPECTED[SOURCE], "source_bindings": {str(p.relative_to(REPO)): v for p,v in EXPECTED.items()},
        "artifact_path": str(artifact), "artifact_sha256": digest(artifact),
        "artifact_bytes": artifact.stat().st_size,
        "operator_shape": [36, 35970], "operator_units": "Mpc^-1",
        "theta_units": "km/s/Mpc", "covariance_units": "(km/s/Mpc)^2",
        "frames": {"direction": "outward ICRS J2000 n", "redshift": "z_CMB released metadata",
                   "metric_signature": "(-,+,+,+)", "speed_of_light_km_s": C_KM_S},
        "working_model": "d=10^((dmzp-25)/5) Mpc; y=c*z_CMB km/s; X=d*[1,n,STF(n*n)]; sigma=hypot(250,70*ln(10)/5*d*e_dmzp); w=Gaussian(z_CMB,center,0.012)/sigma^2",
        "window_centers": list(CENTERS), "theta4x9": theta.reshape(4,9).tolist(),
        "covariance36x36": C.tolist(), "AN_36x3_inverse_Mpc": AN.tolist(),
        "source_bulk_response": "+AN", "observer_velocity_response": "-AN",
        "source_observer_identifiability": "Only source minus observer radial bulk at fixed d,w,n is identified; (h,h) is null.",
        "nuisance": {"raw_theta": "identity/no method projection", "separate_first_order_four_method_gauge": gauge_rows,
                     "whitened_Qz_in_external_artifact": True, "anchored_monopole": "NOT_IDENTIFIED"},
        "validation": {"theta_max_abs": float(np.max(np.abs(theta-theta_ref))),
                       "covariance_max_abs": float(np.max(np.abs(C-C_ref))),
                       "A_X_identity_max_abs": max(identities),
                       "AN_saved_max_abs": max(bulk_errors),
                       "covariance_min_eigenvalue": float(eig[0]),
                       "covariance_psd_roundoff_bound": float(psd_tol),
                       "cross_window_01_max_abs": float(np.max(np.abs(cross))),
                       "permuted_rows_theta_max_abs": permuted_delta},
        "tolerances": {"theta": {"atol": 1e-8, "rtol": 1e-10},
                       "covariance": {"atol": 1e-10, "rtol": 1e-9},
                       "A_X_max_abs": 1e-9, "n_unit_abs": 5e-12,
                       "scaled_rank": 1e-10},
        "caveats": ["Fixed-distance, fixed-weight additive radial-velocity response only; redshift/window/distance/aberration derivatives require a separate full estimator derivative.",
                    "The diagonal working sigma excludes empirical method/calibration covariance, CF4 selection and peculiar-velocity field law.",
                    "z_CMB metadata does not establish a full observer-frame correction. No physical H(z), Bianchi-family identification, or original DAG acceptance follows."],
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
    }
    (product/"RESULT.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    with (product/"TABLE.csv").open("w") as f:
        f.write("z_center,H_working_km_s_Mpc,dipole_norm_km_s_Mpc,STF_frobenius_km_s_Mpc,conditional_H_std_km_s_Mpc\n")
        for i,c in enumerate(CENTERS):
            t=theta[i*9:(i+1)*9]
            f.write(f"{c},{t[0]:.12g},{np.linalg.norm(t[1:4]):.12g},{np.linalg.norm(t[4:]):.12g},{np.sqrt(C[i*9,i*9]):.12g}\n")
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    h = np.array([theta[i*9] for i in range(4)])
    se = np.sqrt(np.array([C[i*9,i*9] for i in range(4)]))
    ax.errorbar(CENTERS, h, yerr=se, fmt="o-", capsize=4)
    ax.set(xlabel="Gaussian z_CMB window center", ylabel="Working H coefficient (km s$^{-1}$ Mpc$^{-1}$)",
           title="CF4 H03 raw fixed-weight operator")
    ax.grid(alpha=.25); fig.tight_layout()
    fig.savefig(product/"FIGURE.png", dpi=180); plt.close(fig)
    (product/"INTERPRETATION.md").write_text(
        "# H03 exact raw operator\n\n"
        "The four plotted monopoles are coefficients of the released CF4 group redshift-distance working law. "
        "Their bars are conditional diagonal working-noise standard deviations; the windows reuse the same 35,970 rows "
        "and their full 36 by 36 covariance includes cross-window terms. They are not four independent expansion measurements.\n\n"
        "For a stipulated additive radial velocity at fixed distance, weights and outward ICRS directions, "
        "the response is A n for source bulk and -A n for observer velocity. The data identify their difference; "
        "a shared boost is a null direction. A physical observer-frame transformation would also alter the "
        "redshift/windows and possibly distance or direction, and is outside this derivative.\n\n"
        "The raw 36 coefficients have no method nuisance projection. The separate first-order four-method mean "
        "gauge has joined rank 12 of 13 and projected rank 8 of 9. Its monopole lacks an anchor. Neither map "
        "supplies an empirical CF4 selection, calibration or velocity-field law, a physical H(z), or family identification. "
        "This is a proposed source-conditional diagnostic pending independent review.\n")
    print(json.dumps({"artifact": str(artifact), "artifact_sha256": digest(artifact),
                      "theta_max_abs": result["validation"]["theta_max_abs"],
                      "covariance_max_abs": result["validation"]["covariance_max_abs"]}), flush=True)


def consume(product: Path) -> None:
    result = json.loads((product/"RESULT.json").read_text())
    a = source_arrays()
    d, sigma, y, X = matrices(a)
    artifact = Path(result["artifact_path"])
    check(digest(artifact) == result["artifact_sha256"], "artifact SHA256")
    with np.load(artifact, allow_pickle=False) as z:
        A, AN, Qz, ids = (z[k] for k in ("A_raw", "AN", "Qz_whitened", "group_id"))
        check(A.shape == (36,35970) and AN.shape == (36,3) and Qz.shape == (4,35970,4), "operator and gauge shapes")
        check(np.array_equal(ids, a["group_id"]), "operator source row identity")
        check(np.allclose((A@y).reshape(4,9), result["theta4x9"], atol=1e-8, rtol=1e-10), "consumer theta replay")
        check(np.allclose((A*sigma[None,:])@(A*sigma[None,:]).T,
                          result["covariance36x36"], atol=1e-10, rtol=1e-9), "consumer covariance replay")
        check(np.allclose(AN, A@a["n_J2000"], atol=1e-10, rtol=1e-10), "consumer physical response")
        check(np.max(np.abs(A@X-np.tile(np.eye(9),(4,1)))) <= 1e-9,
              "consumer nine-column identity")
        for i in range(4):
            check(np.max(np.abs(Qz[i].T@Qz[i]-np.eye(4))) <= 1e-12,
                  f"consumer gauge orthonormality {i}")


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode", choices=("export", "consume"))
    p.add_argument("--product", type=Path, default=Path(__file__).resolve().parent)
    p.add_argument("--external", type=Path, default=Path("/mnt/extdrive/workdir/htt_open_data/r36_cf4_exact_operator_actual"))
    args=p.parse_args()
    if args.mode == "export": export(args.product, args.external)
    else: consume(args.product)
