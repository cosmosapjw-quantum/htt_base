"""Actual retained Planck STF descriptors; no null ranks or scientific admission."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import sys

import numpy as np
import scipy
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "htt"))
from obsstat.reboot_tensor_features import tensors_from_real, tensor_shape_features

SOURCE = ROOT / "docs/research_program/htt_mes_eps_loop9_20261015/inputs"
SOURCE_SHA = "900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"
DEGENERACY_RTOL = 1e-10
METAMORPHIC_ATOL = 2e-11
SHAPE_NAMES = ("quadrupole_shape", "octupole_concentration", "QO_contraction", "chirality")
PARITY_SIGNS = {"T": (1, 1, 1, -1), "E": (1, 1, 1, -1), "B": (-1, 1, 1, 1)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized(tensor):
    a = np.asarray(tensor)
    if np.iscomplexobj(a) or not np.isfinite(a).all():
        raise ValueError("finite real tensor required")
    a = a.astype(float)
    maximum = float(np.max(np.abs(a)))
    if maximum == 0:
        return None
    scaled = a / maximum
    return scaled / np.linalg.norm(scaled)


def checked(q, o):
    q, o = np.asarray(q), np.asarray(o)
    if q.shape != (3, 3) or o.shape != (3, 3, 3):
        raise ValueError("STF tensor shapes required")
    qn, on = normalized(q), normalized(o)
    if qn is not None and (np.max(abs(qn-qn.T)) > 2e-12 or abs(np.trace(qn)) > 2e-12):
        raise ValueError("Q must be STF")
    if on is not None and (any(np.max(abs(on-on.transpose(p))) > 2e-12
                              for p in ((1, 0, 2), (2, 1, 0)))
                           or np.linalg.norm(np.einsum("iik->k", on)) > 2e-12):
        raise ValueError("O must be STF")
    return qn, on


def principal_projector(matrix):
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    scale = float(np.max(abs(eigenvalues)))
    gap = float(eigenvalues[-1]-eigenvalues[-2])
    if scale == 0 or gap <= DEGENERACY_RTOL*scale:
        return None, {"status": "UNKNOWN_DEGENERATE_AXIS", "relative_gap": 0. if scale == 0 else gap/scale}
    u = eigenvectors[:, -1]
    return np.outer(u, u), {"status": "RESOLVED", "relative_gap": gap/scale}


def descriptors(q, o, field):
    if field not in PARITY_SIGNS:
        raise ValueError("field must be T, E or B")
    q, o = checked(q, o)
    values = dict.fromkeys(SHAPE_NAMES)
    statuses = {name: "UNKNOWN_ZERO_TENSOR" for name in SHAPE_NAMES}
    p2 = p3 = None
    axis2 = axis3 = {"status": "UNKNOWN_ZERO_TENSOR", "relative_gap": None}
    if q is not None:
        values[SHAPE_NAMES[0]] = float(np.trace(q@q@q))
        statuses[SHAPE_NAMES[0]] = "RESOLVED"
        p2, axis2 = principal_projector(q@q)
    if o is not None:
        a = np.einsum("iab,jab->ij", o, o)
        values[SHAPE_NAMES[1]] = float(np.linalg.eigvalsh(a)[-1])
        statuses[SHAPE_NAMES[1]] = "RESOLVED"
        p3, axis3 = principal_projector(a)
    if q is not None and o is not None:
        values[SHAPE_NAMES[2]] = float(np.trace((q@q)@a))
        statuses[SHAPE_NAMES[2]] = "RESOLVED"
        v = np.einsum("ijk,jk->i", o, q)
        norms = np.array([np.linalg.norm(v), np.linalg.norm(q@v), np.linalg.norm(a@v)])
        if norms.min() > DEGENERACY_RTOL:
            # Reuse the registered feature kernel only on its defined domain.
            existing = tensor_shape_features(q, o)
            for name, value in zip(SHAPE_NAMES, existing):
                values[name], statuses[name] = float(value), "RESOLVED"
        else:
            statuses[SHAPE_NAMES[3]] = "UNKNOWN_DEGENERATE_CHIRALITY"
    o3 = {name: (None if value is None else float(abs(value) if sign == -1 else value))
          for (name, value), sign in zip(values.items(), PARITY_SIGNS[field])}
    # Keep the even signed T/E quadrupole shape; absolute s is also supplied
    # explicitly as the declared sign-insensitive O(3) summary.
    if o3[SHAPE_NAMES[0]] is not None:
        o3[SHAPE_NAMES[0]] = abs(o3[SHAPE_NAMES[0]])
    orientation = {
        "Q2_projector": None if p2 is None else p2.tolist(),
        "O3_projector": None if p3 is None else p3.tolist(),
        "Q2_axis_status": axis2, "O3_axis_status": axis3,
        "joint_axis_overlap_squared": None if p2 is None or p3 is None else float(np.trace(p2@p3)),
        "fixed_external_axes": "GALACTIC_CARTESIAN_X_Y_Z",
        "Q2_fixed_axis_squared_cosines": None if p2 is None else np.diag(p2).tolist(),
        "O3_fixed_axis_squared_cosines": None if p3 is None else np.diag(p3).tolist(),
    }
    return {"SO3_signed": values, "shape_status": statuses, "O3_summaries": o3, "orientation": orientation}


def transform(q, o, matrix, field):
    m = np.asarray(matrix, dtype=float)
    if field not in PARITY_SIGNS or m.shape != (3, 3) or not np.isfinite(m).all():
        raise ValueError("finite O(3) matrix and T/E/B field required")
    if not np.allclose(m@m.T, np.eye(3), rtol=0, atol=2e-12):
        raise ValueError("orthogonal transformation required")
    checked(q, o)
    intrinsic = float(np.linalg.det(m)) if field == "B" else 1.
    return (intrinsic*m@q@m.T,
            intrinsic*np.einsum("ia,jb,kc,abc->ijk", m, m, m, o))


def cross_features(q, o, p, t):
    q, o = checked(q, o)
    p, t = checked(p, t)
    output = {}
    for name, left, right in (("Q_normalized_overlap", q, p), ("O_normalized_overlap", o, t)):
        output[name] = None if left is None or right is None else float(np.sum(left*right))
        output[name+"_absolute"] = None if output[name] is None else abs(output[name])
    for name, left, right in (("Q_axis_overlap_squared", None if q is None else q@q, None if p is None else p@p),
                              ("O_axis_overlap_squared", None if o is None else np.einsum("iab,jab->ij", o, o),
                               None if t is None else np.einsum("iab,jab->ij", t, t))):
        pl = None if left is None else principal_projector(left)[0]
        pr = None if right is None else principal_projector(right)[0]
        output[name] = None if pl is None or pr is None else float(np.trace(pl@pr))
    return output


def load_source():
    archive = SOURCE / "retained_common_support_coefficients.npz"
    if sha(archive) != SOURCE_SHA:
        raise ValueError("immutable archived source SHA mismatch")
    metadata = json.loads((SOURCE / "planck_loop5_result.json").read_text())
    if (metadata["common_T_nside64_pixel_count"] != 26846
            or metadata["common_POL_nside64_pixel_count"] != 30021
            or not metadata["scalar_coefficients_description"].startswith("orthonormal real")):
        raise ValueError("source support/basis metadata mismatch")
    with np.load(archive, allow_pickle=False) as z:
        tnames = z["names_T"].tolist()
        pnames = z["names_EB"].tolist()
        tc, pc = z["coeff_T"].copy(), z["coeff_EB"].copy()
        layout = json.loads(z["column_spin_metadata_json"].item())
    if tc.shape != (9, 32) or pc.shape != (8, 64) or len(set(tnames)) != 9 or len(set(pnames)) != 8:
        raise ValueError("fixed product family mismatch")
    if tnames != list(metadata["source_file_identities"]) or pnames != [n for n in tnames if n != "SMICA_noSZ_FULL"]:
        raise ValueError("source product identities mismatch")
    if len(layout) != 64:
        raise ValueError("explicit E/B column layout required")
    rows = [(name, "T", row) for name, row in zip(tnames, tc)]
    for field in ("E", "B"):
        indices = [i for i, col in enumerate(layout) if col["E_or_B"] == field]
        expected = [{"ell": ell, "m": m, "phase": phase, "E_or_B": field}
                    for ell in range(2, 6) for m in range(ell+1)
                    for phase in (("m0",) if m == 0 else ("cos", "sin"))]
        if [layout[i] for i in indices] != expected:
            raise ValueError("E/B harmonic layout mismatch")
        rows.extend((name, field, row[indices]) for name, row in zip(pnames, pc))
    return rows, metadata


def finite_error(actual, expected):
    if actual is None or expected is None:
        if actual is not expected:
            raise AssertionError("UNKNOWN status was not preserved")
        return 0.
    return float(np.max(abs(np.asarray(actual)-np.asarray(expected))))


def metamorphic_checks(rows):
    rotations = Rotation.random(8, random_state=np.random.default_rng(20261018)).as_matrix()
    matrices = [("SO3", m) for m in rotations]
    matrices += [("O3_IMPROPER", -m) for m in rotations]
    matrices += [("INVERSION", -np.eye(3)), ("MIRROR_X", np.diag([-1., 1., 1.]))]
    errors = {"signed_shape": 0., "O3_summaries": 0., "projector_covariance": 0., "joint_axis": 0., "cross_fields": 0.}
    by_product = {}
    for name, field, row in rows:
        q, o = tensors_from_real(row)
        by_product.setdefault(name, {})[field] = (q, o)
        base = descriptors(q, o, field)
        for _, m in matrices:
            qt, ot = transform(q, o, m, field)
            moved = descriptors(qt, ot, field)
            improper = np.linalg.det(m) < 0
            for key, sign in zip(SHAPE_NAMES, PARITY_SIGNS[field]):
                wanted = base["SO3_signed"][key]
                wanted = None if wanted is None else wanted*(sign if improper else 1)
                errors["signed_shape"] = max(errors["signed_shape"], finite_error(moved["SO3_signed"][key], wanted))
                errors["O3_summaries"] = max(errors["O3_summaries"], finite_error(moved["O3_summaries"][key], base["O3_summaries"][key]))
            for key in ("Q2_projector", "O3_projector"):
                p = base["orientation"][key]
                wanted = None if p is None else m@np.asarray(p)@m.T
                errors["projector_covariance"] = max(errors["projector_covariance"], finite_error(moved["orientation"][key], wanted))
            errors["joint_axis"] = max(errors["joint_axis"], finite_error(moved["orientation"]["joint_axis_overlap_squared"], base["orientation"]["joint_axis_overlap_squared"]))
    cross_count = 0
    for fields in by_product.values():
        for left, right in (("T", "E"), ("T", "B"), ("E", "B")):
            if left not in fields or right not in fields:
                continue
            base = cross_features(*fields[left], *fields[right])
            for _, m in matrices:
                moved = cross_features(*transform(*fields[left], m, left), *transform(*fields[right], m, right))
                for key in base:
                    sign = -1 if np.linalg.det(m) < 0 and ((left == "B") != (right == "B")) and key in ("Q_normalized_overlap", "O_normalized_overlap") else 1
                    expected = None if base[key] is None else sign*base[key]
                    errors["cross_fields"] = max(errors["cross_fields"], finite_error(moved[key], expected))
                cross_count += 1
    if max(errors.values()) > METAMORPHIC_ATOL:
        raise AssertionError(f"metamorphic tolerance exceeded: {errors}")
    return {"status": "FINITE_METAMORPHIC_CHECKS_PASS", "field_row_transform_checks": len(rows)*len(matrices),
            "cross_pair_transform_checks": cross_count, "seed": 20261018, "absolute_tolerance": METAMORPHIC_ATOL,
            "maximum_absolute_errors": errors, "formal_all_input_proof": False}


def main():
    out = HERE / "results" / "L02_ACTUAL_STATISTICS.json"
    if out.exists():
        raise FileExistsError("create-only L02 numerical result already exists")
    rows, metadata = load_source()
    results, tensors = [], {}
    for product, field, row in rows:
        q, o = tensors_from_real(row)
        tensors[(product, field)] = (q, o)
        results.append({"product": product, "field": field, "sky_id": "ONE_PHYSICAL_PLANCK_SKY",
                        "C2_microK2": float(row[:5]@row[:5]/5), "C3_microK2": float(row[5:12]@row[5:12]/7),
                        **descriptors(q, o, field)})
    cross = []
    for product in metadata["source_file_identities"]:
        for left, right in (("T", "E"), ("T", "B"), ("E", "B")):
            if (product, left) in tensors and (product, right) in tensors:
                cross.append({"product": product, "fields": left+right,
                              "physical_O3_contraction_parity": -1 if "B" in (left, right) else 1,
                              **cross_features(*tensors[(product, left)], *tensors[(product, right)])})
    summary = {}
    for field in PARITY_SIGNS:
        selected = [row for row in results if row["field"] == field]
        summary[field] = {name: [min(v), max(v)] for name in SHAPE_NAMES
                          if (v := [r["SO3_signed"][name] for r in selected if r["SO3_signed"][name] is not None])}
        v = [r["orientation"]["joint_axis_overlap_squared"] for r in selected]
        summary[field]["joint_axis_overlap_squared"] = [min(v), max(v)] if all(x is not None for x in v) else None
    result = {
        "schema": "htt.L02_actual_statistic_family/1", "owner": "obsstat", "scope": "original common-support processed-map ell2/3 STF descriptors",
        "claim_tier": "C0", "claim_status": "DIAGNOSTIC_ONLY", "transfer_source": "none",
        "canonical_dependency_status": "L02_PENDING_UNTIL_L01_X03_ACCEPTANCE_AND_INDEPENDENT_REVIEW",
        "retrospective_application": True, "preregistration_claim": False,
        "source": {"path": str((SOURCE / "retained_common_support_coefficients.npz").relative_to(ROOT)), "sha256": SOURCE_SHA,
                   "metadata_path": str((SOURCE / "planck_loop5_result.json").relative_to(ROOT)),
                   "metadata_sha256": sha(SOURCE / "planck_loop5_result.json"),
                   "T_selected_NSIDE64_pixels": 26846, "EB_selected_NSIDE64_pixels": 30021,
                   "physical_sky_count": 1, "T_products": 9, "EB_products": 8,
                   "harmonic_basis": "ORTHONORMAL_REAL_M0_COS_SIN_CONDON_SHORTLEY", "units": "microK_CMB"},
        "specification_sha256": sha(HERE / "STATISTIC_FAMILY.md"),
        "generator_sha256": sha(Path(__file__)),
        "reused_code_sha256": {p: sha(ROOT / p) for p in ("htt/obsstat/reboot_tensor_features.py", "htt/obsstat/planck_lowell_irrep_projection.py", "htt/obsstat/r7_cmb_product_response.py")},
        "runtime": {"python": sys.executable, "python_version": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                    "requested_model": "gpt-6.1-sol", "requested_effort": "high", "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN",
                    "cwd": str(ROOT), "git_base": "1e095a2749cce9b28e45aac043a82218c21f84e5", "worktree": "dirty_disjoint_native_lane_outputs",
                    "thread_environment": {k: os.environ.get(k, "UNSET") for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")}},
        "method": {"degeneracy_relative_tolerance": DEGENERACY_RTOL, "physical_B_intrinsic_factor": "det(M)",
                   "SO3_shape_improper_parity_signs": PARITY_SIGNS, "external_axes": "GALACTIC_CARTESIAN_X_Y_Z", "axis_or_depth_optimization": False},
        "field_rows": results, "same_product_cross_fields": cross, "descriptive_same_sky_product_ranges": summary,
        "metamorphic": metamorphic_checks(rows), "null_law": "NOT_QUALIFIED", "p_value": None,
        "caveats": ["one shared sky; product ranges are not confidence intervals", "original estimator, not native matched estimator",
                    "finite cut-sky E/B coefficients with unmodeled high-ell leakage", "T/EB masks differ", "incomplete orbit signatures",
                    "no physical shear, vorticity, family identification, null-rank or readiness inference"],
    }
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"output": str(out.relative_to(ROOT)), "rows": len(results), "cross_fields": len(cross), "metamorphic": result["metamorphic"], "ranges": summary}, indent=2))


if __name__ == "__main__":
    main()
