#!/usr/bin/env python3
"""R59-A: compare the native replay of R58 with the committed reference without changing any tolerance.

Every numeric leaf of OWNED_TENSOR_RESULT.json, FIVE_VIEW_RESULT.json and every float array of OWNED_TENSOR_CARRIERS.npz is
compared with rtol = 1e-7, atol = 1e-9 (LOCAL_AGENT_CONTRACT.json R59-A). Provenance strings (versions, heads, byte hashes) are
listed, never compared as science. One exception is reported, not hidden: `null_basis` is an orthonormal basis of an 11-dimensional
null space in scaled coordinates; LAPACK builds may return a different basis of the same subspace. Those leaves are compared as a
subspace (largest principal angle) and every elementwise difference is counted in the output.

    python scripts/r58/compare_r59_native_replay.py --root .
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from scipy.linalg import subspace_angles

PKG = "docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117"
RTOL, ATOL = 1e-7, 1e-9
ANGLE_TOL = 1e-9                       # radians; a basis of the same subspace differs only by roundoff
MARGINAL_TOL = 2e-7                    # acceptance of R59-A: frozen marginal error
PROVENANCE_KEYS = re.compile(r"(sha256|fingerprint_current|/implementation/|source_root_head|carrier_file)")


def leaves(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, obj


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def compare_json(ref: dict, rep: dict, basis_pattern: str | None = None) -> dict:
    a, b = dict(leaves(ref)), dict(leaves(rep))
    out = {"leaves_reference": len(a), "leaves_replay": len(b), "only_reference": sorted(set(a) - set(b)), "only_replay": sorted(set(b) - set(a)),
           "provenance_differences": {}, "nonnumeric_differences": {}, "numeric_leaves": 0, "numeric_outside_tolerance": [],
           "basis_leaves_elementwise_different": 0}
    for k in sorted(set(a) & set(b)):
        x, y = a[k], b[k]
        if PROVENANCE_KEYS.search(k):
            if x != y:
                out["provenance_differences"][k] = [x, y]
            continue
        if is_num(x) and is_num(y):
            out["numeric_leaves"] += 1
            if not abs(float(x) - float(y)) <= ATOL + RTOL * abs(float(x)):
                if basis_pattern and re.search(basis_pattern, k):
                    out["basis_leaves_elementwise_different"] += 1
                else:
                    out["numeric_outside_tolerance"].append([k, x, y])
        elif x != y:
            out["nonnumeric_differences"][k] = [x, y]
    return out


def allowed_repaired_hashes(root: Path) -> dict:
    """ALLOWED_REPAIRED_HASHES of the runner, read from its source (the runner is not imported: it checks pins at import)."""
    import ast
    tree = ast.parse((root / "scripts/r58/run_r58_owned_tensor.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "ALLOWED_REPAIRED_HASHES" for t in node.targets):
            return ast.literal_eval(node.value)
    raise SystemExit("ALLOWED_REPAIRED_HASHES not found in the runner")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = ap.parse_args()
    res = args.root / PKG / "RESULTS"
    rep = res / "NATIVE_REPLAY"
    owned_ref, owned_rep = (json.loads((d / "OWNED_TENSOR_RESULT.json").read_text()) for d in (res, rep))
    view_ref, view_rep = (json.loads((d / "FIVE_VIEW_RESULT.json").read_text()) for d in (res, rep))
    indep = json.loads((rep / "INDEPENDENT_CHECK.json").read_text())

    owned = compare_json(owned_ref, owned_rep)
    views = compare_json(view_ref, view_rep, basis_pattern=r"/x/physical_pullback/null_basis\[")
    angles = {}
    for m in view_ref["models"]:
        na = np.array(view_ref["models"][m]["x"]["physical_pullback"]["null_basis"], float)
        nb = np.array(view_rep["models"][m]["x"]["physical_pullback"]["null_basis"], float)
        angles[m] = float(subspace_angles(na, nb).max()) if na.shape == nb.shape else float("inf")
    views["null_subspace_max_principal_angle"] = angles

    za, zb = np.load(res / "OWNED_TENSOR_CARRIERS.npz", allow_pickle=False), np.load(rep / "OWNED_TENSOR_CARRIERS.npz", allow_pickle=False)
    npz_bad = [] if set(za.files) == set(zb.files) else [["key sets differ", sorted(set(za.files) ^ set(zb.files))]]
    for k in za.files:
        x, y = za[k], zb[k]
        if x.shape != y.shape:
            npz_bad.append([k, "shape"])
        elif x.dtype.kind in "fc":
            if not np.allclose(x, y, rtol=RTOL, atol=ATOL):
                npz_bad.append([k, float(np.max(np.abs(x - y)))])
        elif not np.array_equal(x, y):
            npz_bad.append([k, "nonnumeric"])

    allowed = allowed_repaired_hashes(args.root)       # review finding R59-RV-05: a changed input must be an allowlisted repair
    changed_inputs = {k: [owned_ref["inputs_sha256"][k], owned_rep["inputs_sha256"].get(k)] for k in owned_ref["inputs_sha256"]
                      if owned_ref["inputs_sha256"][k] != owned_rep["inputs_sha256"].get(k)}
    changed_inputs.update({k: [None, v] for k, v in owned_rep["inputs_sha256"].items() if k not in owned_ref["inputs_sha256"]})
    marg = max(abs(float(v)) for m in owned_rep["reproduction"].values() for v in m.values())
    ranks = {m: view_rep["models"][m]["x"]["physical_pullback"]["rank"] for m in view_rep["models"]}
    cache = [{k: c[k] for k in ("file", "model_key_equal", "row_labels_equal", "exact_operator_bytes")} for c in owned_rep["cache_reuse"]]
    acceptance = {
        "n_groups_35970": owned_rep["n_groups"] == 35970,
        "n_models_7": owned_rep["n_models"] == 7 and len(owned_rep["variants"]) == 7,
        "physical_rank_11_all_models": all(r == 11 for r in ranks.values()),
        "frozen_marginal_max_abs_error_below_2e-7": marg < MARGINAL_TOL,
        "owned_result_numeric_parity": not owned["numeric_outside_tolerance"] and not owned["only_reference"] and not owned["only_replay"] and not owned["nonnumeric_differences"],
        "five_view_numeric_parity_except_basis": not views["numeric_outside_tolerance"] and not views["only_reference"] and not views["only_replay"] and not views["nonnumeric_differences"],
        "null_subspaces_equal": all(a < ANGLE_TOL for a in angles.values()),
        "carrier_arrays_parity": not npz_bad,
        "cache_identity_labels_and_model_keys": all(c["model_key_equal"] and c["row_labels_equal"] for c in cache),
        "changed_inputs_are_allowlisted_repairs": all(new in allowed.get(k, ()) for k, (_, new) in changed_inputs.items()),
        "independent_checker_status": indep.get("status"),
    }
    accepted = all(v for k, v in acceptance.items() if k != "independent_checker_status") and str(indep.get("status", "")).startswith("IMPLEMENTATION_AND_FINITE_ASSERTION_VERIFIED")
    out = {
        "schema": "htt.r59.native_replay_parity/1",
        "tolerances": {"rtol": RTOL, "atol": ATOL, "null_subspace_angle_rad": ANGLE_TOL, "frozen_marginal_abs": MARGINAL_TOL},
        "acceptance": acceptance,
        "accepted": accepted,
        "frozen_marginal_max_abs_error": marg,
        "physical_ranks": ranks,
        "cache_reuse": cache,
        "changed_inputs": changed_inputs,
        "allowed_repaired_hashes": {k: list(v) for k, v in allowed.items()},
        "cache_note": "operator byte fingerprints differ (exact_operator_bytes false in reference and replay); accepted only with equal model keys, equal row labels and the numeric parity above (LOCAL_AGENT_CONTRACT.json R59-A)",
        "owned_result": owned,
        "five_view_result": views,
        "basis_note": "null_basis leaves that differ elementwise are a different orthonormal basis of the same null subspace (largest principal angle listed); no tolerance was changed",
        "carrier_arrays_outside_tolerance": npz_bad,
        "carrier_arrays_compared": len(za.files),
        "independent_check": {k: indep[k] for k in ("status", "max_wald_p", "distance_quad_rel") if k in indep},
        "files_sha256": {str(p.relative_to(args.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(rep.glob("*")) if p.name != "REFERENCE_PARITY.json"},
    }
    (rep / "REFERENCE_PARITY.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"accepted": accepted, **acceptance}, indent=1))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
