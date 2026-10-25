#!/usr/bin/env python3
"""One selected-source CF4 support-simplex calibration quotient.

The projector is defined by all singleton rows, all seven singleton-channel
indicators, and the inherited fourteen E1 nuisance columns.  Mixed rows are
retained in the carrier and saturated by their coordinate nuisance columns.
This is an apparent linear observable under a working metric, not a physical
covariance or a source selection law.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
INPUT = HERE / "INPUT.json"
THRESHOLDS = (1e-12, 1e-10, 1e-8)
CHANNELS = ("SNIa", "FP", "TFR", "SBFm", "SBFir", "SNII", "DirectCal")
DIRECT_IDS = {20679, 59927}


class Hold(RuntimeError):
    pass


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inputs():
    bound = json.loads(INPUT.read_text())
    for role, item in list(bound["inputs"].items()) + list(bound["contract_binding"].items()):
        path = Path(item["path"])
        if not path.is_file():
            raise Hold(f"MISSING_IMMUTABLE_INPUT role={role} path={path}")
        found_size = path.stat().st_size
        found_sha = sha(path)
        if (found_size, found_sha) != (item["bytes"], item["sha256"]):
            raise Hold(f"IMMUTABLE_INPUT_MISMATCH role={role} path={path} size={found_size} sha256={found_sha}")
    return bound


def sealed_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Hold(f"SEALED_SOURCE_IMPORT_FAILED {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != Path(path).resolve():
        raise Hold(f"SEALED_SOURCE_RESOLUTION_MISMATCH {module.__file__} != {path}")
    return module


def support_from_source(bound, ids, operator):
    """One read of table3 numeric pairs; no old reconstruction entrypoint."""
    parser = sealed_module(bound["inputs"]["operator_source"]["path"], "sealed_cf4_operator_parser")
    rows = parser.parse_table3(Path(bound["inputs"]["cf4_table3"]["path"]))
    by_id = {int(row["pgc"]): row for row in rows}
    if len(by_id) != len(rows):
        raise Hold("DUPLICATE_TABLE3_SELECTED_ID")
    support = np.zeros((len(ids), 7), dtype=bool)
    line_numbers = np.empty(len(ids), dtype=np.int64)
    for i, pgc in enumerate(ids):
        pgc = int(pgc)
        if pgc not in by_id:
            raise Hold(f"SELECTED_ID_MISSING_TABLE3 pgc={pgc}")
        row = by_id[pgc]
        line_numbers[i] = row["line"]
        for j, (dm, err) in enumerate(row["methods"]):
            if bool(dm) != bool(err):
                raise Hold(f"INCOMPLETE_NUMERIC_PAIR pgc={pgc} channel={CHANNELS[j]} line={row['line']}")
            if dm:
                try:
                    if not np.isfinite(float(dm)) or not np.isfinite(float(err)) or float(err) <= 0:
                        raise ValueError("nonpositive/nonfinite pair")
                except ValueError as exc:
                    raise Hold(f"INVALID_NUMERIC_PAIR pgc={pgc} channel={CHANNELS[j]} line={row['line']} dm={dm} err={err}") from exc
                support[i, j] = True
        if pgc in DIRECT_IDS:
            if support[i, :6].any() or not row["dmcal"] or not row["dmzp"]:
                raise Hold(f"DIRECT_BRANCH_UNRESOLVED pgc={pgc} line={row['line']}")
            support[i, 6] = True
        elif not support[i, :6].any():
            raise Hold(f"SELECTED_SUPPORT_EMPTY_OR_UNRESOLVED pgc={pgc} line={row['line']}")
    if set(ids[support[:, 6]].astype(int)) != DIRECT_IDS:
        raise Hold("DIRECT_CALIBRATOR_IDENTITY_CHANGED")
    if not np.array_equal(ids, operator["selected_pgc"].astype("<i8")):
        raise Hold("SELECTED_OPERATOR_ORDER_MISMATCH")
    if tuple(operator["channel_names"].astype(str)) != CHANNELS:
        raise Hold("CHANNEL_ORDER_MISMATCH")
    widths = tuple(operator["width_names"].astype(str))
    if widths != ("round_nearest", "one_place_outer"):
        raise Hold(f"WIDTH_ORDER_MISMATCH {widths}")
    op_ids = operator["pgc"].astype("<i8")
    if len(np.unique(op_ids)) != len(op_ids):
        raise Hold("DUPLICATE_GROUP_OPERATOR_ID")
    op_index = {int(v): k for k, v in enumerate(op_ids)}
    for i, pgc in enumerate(ids):
        state = tuple(operator["status"][op_index[int(pgc)]].astype(str))
        expected = "DIRECT_CALIBRATOR_COMPATIBLE" if pgc in DIRECT_IDS else "JOINT_COMPATIBLE"
        if state != (expected, expected):
            raise Hold(f"OPERATOR_STATUS_MISMATCH pgc={int(pgc)} line={int(line_numbers[i])} status={state}")
    maps = {
        "nominal": operator["selected_nominal_A7"],
        "witness_round_nearest": operator["selected_witness_A7"][:, 0, :],
        "witness_one_place_outer": operator["selected_witness_A7"][:, 1, :],
    }
    one = support.sum(axis=1) == 1
    for name, a in maps.items():
        if a.shape != support.shape or not np.isfinite(a).all() or np.any(a < 0):
            raise Hold(f"REPRESENTATIVE_DOMAIN_FAIL name={name}")
        if np.any(a[~support] != 0) or np.any(a[support] <= 0):
            bad = np.flatnonzero(np.any(np.where(support, a <= 0, a != 0), axis=1))
            raise Hold(f"REPRESENTATIVE_SIGN_SUPPORT_FAIL name={name} pgc={int(ids[bad[0]])}")
        error = np.max(np.abs(a.sum(axis=1) - 1))
        if error > 1e-14:
            raise Hold(f"REPRESENTATIVE_SIMPLEX_FAIL name={name} max_error={error}")
        if not np.array_equal(a[one], support[one].astype(float)):
            raise Hold(f"REPRESENTATIVE_SINGLETON_FAIL name={name}")
    return support, line_numbers, maps


def rank_counts(spectrum, scale):
    return {str(t): int(np.sum(spectrum > t * scale)) for t in THRESHOLDS}


def projector(active_n, weighted_nuisance, names):
    """Rank-revealing normalized SVD, including dependent columns."""
    if weighted_nuisance.shape[0] != active_n:
        raise Hold("PROJECTOR_ROW_SHAPE")
    norms = np.linalg.norm(weighted_nuisance, axis=0)
    kept = norms > 0
    if not kept.any():
        return np.zeros((active_n, 0)), {"rank_counts": {str(t): 0 for t in THRESHOLDS},
                                       "singular_values": [], "exact_zero_columns": list(names)}
    u, singular, _ = np.linalg.svd(weighted_nuisance[:, kept] / norms[kept], full_matrices=False)
    counts = rank_counts(singular, singular[0])
    info = {"rank_counts": counts, "singular_values": singular.tolist(),
            "exact_zero_columns": [names[j] for j in np.flatnonzero(~kept)],
            "column_norms": norms.tolist(), "relative_scale": float(singular[0]),
            "retained_column_names": [names[j] for j in np.flatnonzero(kept)]}
    if len(set(counts.values())) != 1:
        raise Hold("NUMERICAL_RANK_UNCERTAIN nuisance_spectrum=" + json.dumps(info))
    rank = counts[str(1e-10)]
    info["rank"] = rank
    info["discarded_nonzero_status"] = "UNRESOLVED_OR_DISCARDED_AT_TOLERANCE" if rank < len(singular) and np.any(singular[rank:] > 0) else None
    return u[:, :rank], info


def project(q, arr):
    return arr - q @ (q.T @ arr)


def scaled_residual(a, scale):
    return float(np.linalg.norm(a) / max(float(scale), np.finfo(float).tiny))


def response_fit(bw, y_w, active, q):
    """External preprojection scale determines rank; no target rescaling."""
    n = len(active)
    if bw.shape != (n, 5) or y_w.shape != (n,) or q.shape[0] != int(active.sum()):
        raise Hold("RESPONSE_SHAPE")
    target_singular = np.linalg.svd(bw, compute_uv=False)
    target_scale = float(target_singular[0])
    if not np.isfinite(target_scale) or target_scale <= 0:
        raise Hold("PREPROJECTION_TARGET_SCALE_INVALID")
    rj = project(q, bw[active])
    tj = project(q, y_w[active])
    left, singular, vt = np.linalg.svd(rj, full_matrices=False)
    counts = rank_counts(singular, target_scale)
    detail = {"signal_singular_values": singular.tolist(),
              "external_preprojection_target_scale": target_scale,
              "preprojection_singular_values": target_singular.tolist(),
              "ratios_to_external_scale": (singular / target_scale).tolist(),
              "ratios_to_projected_max_diagnostic_only": (singular / singular[0]).tolist() if singular[0] > 0 else None,
              "rank_counts": counts}
    if len(set(counts.values())) != 1:
        raise Hold("NUMERICAL_RANK_UNCERTAIN signal_spectrum=" + json.dumps(detail))
    rank = counts[str(1e-10)]
    v = vt.T
    vr, vn = v[:, :rank], v[:, rank:]
    pin = vr @ vr.T
    b_min = vr @ ((left[:, :rank].T @ tj) / singular[:rank]) if rank else None
    c_work = (vr / singular[:rank]) @ (vr / singular[:rank]).T if rank else None
    detail.update({"rank": rank,
                   "rank_scope": "TOLERANCE_DEFINED_NUMERICAL_RANK",
                   "discarded_nonzero_status": "UNRESOLVED_OR_DISCARDED_AT_TOLERANCE" if rank < 5 and np.any(singular[rank:] > 0) else None,
                   "response_exact_zero_witness": None})
    return rj, tj, vr, vn, pin, b_min, c_work, detail


def exact_decomposition_control():
    """Coefficientwise symbolic cancellation for arbitrary support variables."""
    supports = ((0,), (1,), (6,), (0, 1), (2, 3, 5))
    mixed = [i for i, s in enumerate(supports) if len(s) > 1]
    for i, s in enumerate(supports):
        for j in range(7):
            # A_ij is a formal variable for mixed i, or exact integer for J.
            a = ("w", i, j) if i in mixed and j in s else (int(j == s[0]) if i not in mixed else 0)
            c = int(i not in mixed and j == s[0])
            em = ("w", i, j) if i in mixed and j in s else 0
            if a != (em if c == 0 else c):
                raise Hold(f"EXACT_SUPPORT_DECOMPOSITION_FAIL row={i} channel={j}")
    return {"status": "EXACT_COEFFICIENTWISE_IDENTITY", "fixture_supports": supports,
            "formal_mixed_variables": sum(len(s) for s in supports if len(s) > 1)}


def load_source(bound):
    with np.load(bound["inputs"]["selected_source"]["path"], allow_pickle=False) as f:
        data = {k: f[k] for k in ("group_id", "z_CMB", "dmzp", "e_dmzp", "n_J2000", "method_family")}
    ids = np.asarray(data["group_id"], dtype="<i8")
    if len(ids) != 35970 or sha_bytes(ids.tobytes()) != bound["selected_id_sha256_little_endian_int64"]:
        raise Hold("SELECTED_COHORT_IDENTITY_CHANGED")
    if len(np.unique(ids)) != len(ids):
        raise Hold("DUPLICATE_SELECTED_ID")
    return data, ids


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def real_consumer(bound):
    data, ids = load_source(bound)
    with np.load(bound["inputs"]["group_operator"]["path"], allow_pickle=False) as f:
        operator = {k: f[k] for k in ("pgc", "selected_pgc", "selected_nominal_A7", "selected_witness_A7", "channel_names", "width_names", "status")}
    support, table_lines, maps = support_from_source(bound, ids, operator)
    active = support.sum(axis=1) == 1
    mixed = ~active
    c = np.zeros_like(support, dtype=float)
    c[active] = support[active]
    model = sealed_module(bound["inputs"]["e1_design"]["path"], "sealed_cf4_e1_design")
    if tuple(model.stf2_orthonormal().shape) != (5, 3, 3):
        raise Hold("STF_BASIS_SHAPE")
    design = model.model_matrix(data["z_CMB"], data["n_J2000"], data["method_family"],
                                H0=74.6, omega_m=.3153, include_method_slope=True,
                                include_bulk=True, include_angular_dipole=True)
    x, slices = design["design"], design["slices"]
    b = x[:, slices["shear"]]
    n = np.delete(x, np.arange(slices["shear"].start, slices["shear"].stop), axis=1)
    if b.shape != (35970, 5) or n.shape != (35970, 14):
        raise Hold(f"DESIGN_SHAPE_CHANGED B={b.shape} N={n.shape}")
    d = data["e_dmzp"] ** 2 + .15 ** 2 + (250.0 * design["redshift_velocity_width_basis_mag_per_kms"]) ** 2
    y = data["dmzp"] - design["reference_mu_mag"]
    if not np.isfinite(d).all() or np.any(d <= 0) or not np.isfinite(y).all():
        raise Hold("WORKING_METRIC_OR_OBSERVATION_DOMAIN")
    dsqrt = np.sqrt(d)
    bw, nw, yw = b / dsqrt[:, None], n / dsqrt[:, None], y / dsqrt
    # Read-only design identity check. This does not refit the old observation.
    qold, old_info = projector(len(ids), nw, [f"old_nuisance_{j}" for j in range(14)])
    old_f = (project(qold, bw).T @ project(qold, bw))
    old = json.loads(Path(bound["inputs"]["e1_result"]["path"]).read_text())["source_comparisons"]["all"]
    f_saved = np.asarray(old["schur_fisher"], float)
    if not np.allclose(old_f, f_saved, rtol=1e-9, atol=1e-10):
        raise Hold(f"SAVED_E1_FISHER_MISMATCH maxabs={np.max(abs(old_f-f_saved))}")
    uj = np.column_stack((nw[active], c[active] / dsqrt[active, None]))
    names = [f"E1_nuisance_{j}" for j in range(14)] + [f"singleton_{ch}" for ch in CHANNELS]
    q, nuisance_info = projector(int(active.sum()), uj, names)
    rj, tj, vr, vn, pin, b_min, c_work, signal_info = response_fit(bw, yw, active, q)
    rank = signal_info["rank"]
    fstar = (rj.T @ rj + (rj.T @ rj).T) / 2
    delta = (f_saved - fstar + (f_saved - fstar).T) / 2
    eig_delta = np.linalg.eigvalsh(delta)
    delta_scale = max(np.linalg.norm(f_saved, 2), 1.)
    if eig_delta[0] < -1e-9 * delta_scale:
        raise Hold(f"INFORMATION_MONOTONICITY_FAIL min_eigenvalue={eig_delta[0]}")
    import scipy.linalg as la
    generalized = la.eigh(fstar, f_saved, eigvals_only=True)
    if np.min(generalized) < -1e-9 or np.max(generalized) > 1 + 1e-9:
        raise Hold(f"GENERALIZED_INFORMATION_RANGE_FAIL {generalized.tolist()}")
    r = np.zeros_like(bw)
    t = np.zeros_like(y)
    r[active], t[active] = rj, tj
    k = np.zeros((5, len(ids)))
    if rank:
        # Reconstruct the retained left vectors from the *same* right basis
        # used for b_min, avoiding a second SVD with an arbitrary sign choice.
        singular = np.asarray(signal_info["signal_singular_values"])
        left = (rj @ vr) / singular[:rank]
        k[:, active] = (vr / singular[:rank]) @ (left[:, :rank].T / dsqrt[active][None, :])
    if not np.array_equal(k[:, mixed], np.zeros((5, int(mixed.sum())))):
        raise Hold("MIXED_ROW_NONZERO_ESTIMATOR_COLUMN")
    errors = {"KN": scaled_residual(k @ n, np.linalg.norm(k) * np.linalg.norm(n)),
              "KC": scaled_residual(k @ c, np.linalg.norm(k) * np.linalg.norm(c)),
              "KB_minus_Pid": scaled_residual(k @ b - pin, max(np.linalg.norm(pin), 1.)),
              "Q_orthogonality": scaled_residual(q.T @ q - np.eye(q.shape[1]), max(q.shape[1] ** .5, 1.)),
              "Q_on_mixed_exact_zero": 0.0}
    for name, a in maps.items():
        errors[f"KA_{name}"] = scaled_residual(k @ a, np.linalg.norm(k) * np.linalg.norm(a))
    if any(not np.isfinite(value) or value > 1e-10 for value in errors.values()):
        raise Hold(f"NUMERICAL_OPERATOR_RESIDUAL_FAIL {errors}")
    # The symbolic identity, rather than three finite examples, establishes all-A annihilation.
    proof = {
        "support_decomposition_status": "EXACT_MODEL_IDENTITY",
        "exact_identity": "A=C+E_M A[M,:] for every A in the fixed support-simplex",
        "ideal_operator_status": "SYMBOLIC_MODEL_IDENTITY",
        "ideal_operator_definition": "W=diag(d^-1/2); U_J=Z W [N,C]; P_star=Z-U_J U_J^+; R_star=P_star W B; K_star=R_star^+ P_star W",
        "ideal_annihilation": "P_star W A=0 and P_star W N=0; hence K_star A=K_star N=0 for every admitted A",
        "ideal_covariance_cancellation": "For K_star, calibration covariance and both residual-calibration cross terms vanish algebraically whenever joint moments exist",
        "ideal_exact_rank_evaluated": False,
        "computed_operator_name": "K_hat",
        "computed_operator_status": "NUMERICAL_RESIDUAL_CHECK_ONLY",
        "computed_operator_exact_calibration_annihilation": "NOT_ESTABLISHED",
        "computed_operator_unrestricted_Gamma_uniform_protection": "NOT_ESTABLISHED",
        "computed_operator_cross_term_cancellation": "NOT_ESTABLISHED",
        "computed_mixed_columns": "BIT_EXACT_ZERO_BY_CONSTRUCTION; K_hat A=K_hat C as serialized-real matrices, but K_hat C is only checked numerically",
        "unbounded_covariance_witness": "If E=K_hat A is nonzero, Gamma_t=t vv^T with Ev nonzero makes E Gamma_t E^T unbounded as t grows",
        "scope": "fixed released support and seven additive channel perturbations only; conservative envelope may lose extra information; no exact numerical evaluation/error bound of K_star"}
    old_b = np.asarray(old["apparent_stf_coefficients"], float)
    contrasts = vr.T @ b_min if rank else None
    old_contrasts = vr.T @ old_b if rank else None
    basis = model.stf2_orthonormal()
    tensor = np.einsum("t,tij->ij", b_min, basis) if rank == 5 else None
    if rank == 0:
        status = "NO_STF_COMBINATION_RETAINED_AT_DECLARED_TOLERANCE"
    elif rank < 5:
        status = "PARTIAL_APPARENT_STF_CONTRAST_ESTIMATOR"
    else:
        status = "FULL5_APPARENT_STF_ESTIMATOR"
    leverage = np.linalg.norm(k, axis=0)
    additional_zero = active & (leverage == 0)
    result = {
        "schema": "htt.cf4_support_simplex_calibration_quotient/1",
        "status": status,
        "claim_ceiling": "ideal support-model annihilator is symbolic; saved binary64 K_hat has numerical residual checks only and unrestricted-Gamma protection NOT_ESTABLISHED; selected-source apparent signed STF estimator under inherited diagonal D working metric, with physical covariance/PV/selection law UNKNOWN",
        "cohort": {"source_rows": len(ids), "mixed_saturated_rows": int(mixed.sum()),
                   "singleton_active_rows": int(active.sum()), "additional_exact_zero_leverage_rows": int(additional_zero.sum()),
                   "selected_id_sha256_little_endian_int64": sha_bytes(ids.tobytes()),
                   "direct_calibrator_ids": sorted(DIRECT_IDS), "table3_selected_line_minmax": [int(table_lines.min()), int(table_lines.max())]},
        "source_inputs": {role: {"path": item["path"], "sha256": item["sha256"], "bytes": item["bytes"]} for role, item in bound["inputs"].items()},
        "contract_binding": bound["contract_binding"],
        "fixed_model": {"H0": 74.6, "Omega_m": .3153, "method_slope": True, "bulk": True,
                        "angular_dipole": True, "D": "e_dmzp^2+0.15^2+(250*j_v)^2 working metric only",
                        "stf_basis": ["(xx-yy)/sqrt2", "(xx+yy-2zz)/sqrt6", "symmetric_xy/sqrt2", "symmetric_xz/sqrt2", "symmetric_yz/sqrt2"]},
        "proof": proof, "nuisance": nuisance_info, "signal": signal_info,
        "fisher_star": fstar.tolist(), "saved_fisher_E1": f_saved.tolist(),
        "saved_fisher_design_check_maxabs": float(np.max(abs(old_f - f_saved))),
        "information_difference_min_eigenvalue": float(eig_delta[0]),
        "generalized_information_eigenvalues_raw_ascending": generalized.tolist(),
        "identified_rank": rank, "identified_basis_5xr": vr.tolist(), "complement_basis_5x5_minus_r": vn.tolist(),
        "projector_identified_5x5": pin.tolist(),
        "minimum_norm_representative_b": b_min.tolist() if rank else None,
        "complete_3x3_tensor": tensor.tolist() if tensor is not None else None,
        "affine_fibre": "b=b_min+V_null z for the chosen tolerance-defined contrast estimator" if rank else "all five STF directions unreported at declared tolerance",
        "identified_signed_contrasts": contrasts.tolist() if rank else None,
        "saved_old_signed_contrasts_in_new_basis": old_contrasts.tolist() if rank else None,
        "contrast_difference_sampling_covariance": "UNKNOWN",
        "working_contrast_covariance_r_by_r": np.diag(1 / np.square(signal_info["signal_singular_values"][:rank])).tolist() if rank else None,
        "working_coordinate_covariance_5x5": c_work.tolist() if rank else None,
        "working_covariance_scope": "metric-derived only if D is adopted as an additional residual-error model; not empirical covariance or physical error bars",
        "actual_residual_covariance": "UNKNOWN; for arbitrary residual Sigma: K_hat Sigma K_hat^T",
        "operator_residuals_scaled_for_K_hat_only": errors,
        "numerical_carrier": "CARRIER.npz", "figure": "INFORMATION_AND_CONTRASTS.png",
        "exact_rank_claim": None,
    }
    carrier = dict(group_id=ids, selected_support_7=support, active_singleton_mask=active,
                   mixed_zero_leverage_mask=mixed, mixed_group_id=ids[mixed],
                   extra_zero_leverage_mask=additional_zero, channel_names=np.asarray(CHANNELS),
                   C=c, d=d, B=b, N=n, y=y, Q_active=q, active_group_id=ids[active],
                   R=r, t=t, F_star=fstar, F_E1=f_saved, K=k, leverage=leverage,
                   signal_singular_values=np.asarray(signal_info["signal_singular_values"]),
                   nuisance_singular_values=np.asarray(nuisance_info["singular_values"]),
                   generalized_information_eigenvalues=generalized, V_identified=vr, V_complement=vn,
                   P_identified=pin, b_min=b_min if rank else np.asarray([], dtype=float),
                   C_work_id=c_work if rank else np.asarray([], dtype=float),
                   STF_basis_5x3x3=basis)
    return result, carrier


def render(result, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    values = result["generalized_information_eigenvalues_raw_ascending"]
    axes[0].bar(np.arange(1, 6), values)
    axes[0].set(xlabel="Generalized STF mode", ylabel="F_star / F_E1 information fraction",
                title="Inherited D working metric")
    axes[0].axhline(0, color="black", linewidth=.5)
    new = result["identified_signed_contrasts"]
    old = result["saved_old_signed_contrasts_in_new_basis"]
    if new is None:
        axes[1].text(.5, .5, "No STF contrast retained\nat declared numerical tolerance", ha="center", va="center")
        axes[1].set_axis_off()
    else:
        x = np.arange(1, len(new) + 1)
        axes[1].plot(x, new, "o-", label="floating K_hat quotient")
        axes[1].plot(x, old, "s--", label="saved E1, same contrasts")
        axes[1].set(xlabel="Retained signed contrast", ylabel="Apparent STF coefficient",
                    title="Numerical selected-source estimator; significance unknown")
        axes[1].legend(fontsize=8)
    fig.suptitle(f"CF4 {result['cohort']['source_rows']} selected groups; {result['cohort']['mixed_saturated_rows']} support-saturated rows")
    fig.savefig(out / result["figure"], dpi=140)
    plt.close(fig)


def run():
    out = HERE / "actual_run" / "products"
    if out.exists():
        raise Hold(f"CREATE_ONLY_OUTPUT_EXISTS {out}")
    bound = inputs()
    result, carrier = real_consumer(bound)
    out.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(out / "CARRIER.npz", **carrier)
    render(result, out)
    result["product_sha256"] = {name: sha(out / name) for name in ("CARRIER.npz", result["figure"])}
    with (out / "RESULT.json").open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())
    return result


if __name__ == "__main__":
    try:
        print(json.dumps({"status": run()["status"]}), flush=True)
    except Hold as exc:
        failure = HERE / "actual_run" / "FIRST_FAILURE.json"
        if failure.parent.exists() and not failure.exists():
            with failure.open("x") as stream:
                json.dump({"status": str(exc).split(" ", 1)[0], "raw_failure": str(exc)}, stream, indent=2)
                stream.write("\n")
        raise
