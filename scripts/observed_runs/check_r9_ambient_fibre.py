#!/usr/bin/env python3
"""Compare fixed ambient STF fibre targets across coordinate bases.

Numerical reproduction only: no physical confidence or four-axis admission.
The previous random-coordinate reference and its evidence are not modified.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import platform
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "htt/src"))
from common.tensor_functionals import fixed_contraction_support

ATOL = 1e-10  # Frozen R9 reference tolerance, not tuned to this comparison.
REFERENCE = ROOT / "docs/research_program/tensor_joint_r9/revision2/validate_revision2.py"


def stf3(tensor):
    """Orthogonal Cartesian STF projection with full Frobenius products."""
    tensor = np.asarray(tensor, float)
    if tensor.shape != (3, 3, 3) or not np.isfinite(tensor).all():
        raise ValueError("finite Cartesian rank-three tensor required")
    symmetric = sum(tensor.transpose(p) for p in itertools.permutations(range(3))) / 6
    trace = np.einsum("iik->k", symmetric)
    eye = np.eye(3)
    return symmetric - (np.einsum("ij,k->ijk", eye, trace)
                        + np.einsum("ik,j->ijk", eye, trace)
                        + np.einsum("jk,i->ijk", eye, trace)) / 5


def ambient_case():
    """Freeze the Cartesian functional before constructing any SVD basis."""
    raw = np.zeros((3, 3, 3))
    for index, value in [((0, 0, 0), 2), ((0, 1, 1), 3),
                         ((0, 1, 2), -1), ((1, 2, 2), 4), ((2, 2, 2), -2)]:
        raw[index] = value
    direction = stf3(raw)
    direction /= np.linalg.norm(direction)
    return np.diag([1., -1., 0.]) / np.sqrt(2), np.array([.1, .15, -.05]), direction


def cartesian_reference(q, v, direction):
    """Basis-free adjoint construction from the frozen F3 tensor formula."""
    metric = np.eye(3) + 6 * (q @ q) / 5
    def right(w):
        dual = np.linalg.solve(metric / 3, w)
        return stf3(np.einsum("i,jk->ijk", dual, q))
    center = right(v)
    null_direction = direction - right(np.einsum("ijk,jk->i", direction, q))
    eta = float(np.sum(center * center))
    radius = np.sqrt(1 - eta)
    witness = center + radius * null_direction / np.linalg.norm(null_direction)
    return {"support": float(np.sum(direction * center) + radius * np.linalg.norm(null_direction)),
            "eta": eta, "witness": witness}


def check_basis(basis, q, v, direction):
    basis = np.asarray(basis, float)
    if basis.shape != (7, 3, 3, 3) or not np.isfinite(basis).all():
        raise ValueError("finite orthonormal STF3 basis required")
    flat = basis.reshape(7, 27)
    if (np.max(np.abs(flat @ flat.T - np.eye(7))) > ATOL
            or max(np.max(np.abs(stf3(b) - b)) for b in basis) > ATOL):
        raise ValueError("basis must be orthonormal and STF in the ambient metric")
    operator = np.einsum("sijk,jk->is", basis, q)
    coordinates = np.einsum("sijk,ijk->s", basis, direction)
    result = fixed_contraction_support(operator, v, coordinates, q_is_fixed=True)
    if result["status"] != "NUMERICALLY_CHECKED_FIXED_FIBRE":
        raise ValueError("comparison requires a resolved interior fixed fibre")
    witness = np.einsum("s,sijk->ijk", result["witness"], basis)
    return {"support": result["support"], "eta": result["eta"], "witness": witness,
            "coordinates": coordinates,
            "contraction_error": float(np.linalg.norm(np.einsum("ijk,jk->i", witness, q) - v)),
            "norm_error": abs(float(np.linalg.norm(witness)) - 1),
            "objective_error": abs(float(np.sum(direction * witness)) - result["support"])}


def compare():
    # Import only the saved basis constructor; never call its experiment main().
    spec = importlib.util.spec_from_file_location("r9_frozen_reference", REFERENCE)
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    q, v, direction = ambient_case()
    base = reference.stf3_basis()
    oracle = cartesian_reference(q, v, direction)
    bases = {"original_svd": base,
             "sign_flip": base * np.array([-1, 1, -1, 1, -1, 1, -1])[:, None, None, None],
             "permutation": base[[6, 2, 4, 0, 5, 1, 3]]}
    # Same fixed ambient q,v,a; random numbers change only the representation.
    rng = np.random.default_rng(20260913)
    for i in range(32):
        rotation, _ = np.linalg.qr(rng.normal(size=(7, 7)))
        bases[f"orthogonal_{i:02d}"] = np.einsum("ab,bijk->aijk", rotation, base)
    rows = []
    for name, basis in bases.items():
        result = check_basis(basis, q, v, direction)
        row = {"basis": name, "support": result["support"], "eta": result["eta"],
               "support_error": abs(result["support"] - oracle["support"]),
               "ambient_witness_error": float(np.linalg.norm(result["witness"] - oracle["witness"])),
               **{k: result[k] for k in ("contraction_error", "norm_error", "objective_error")}}
        assert max(row[k] for k in row if k.endswith("error")) < ATOL, row
        rows.append(row)
    # The old comparison's failure mechanism: freezing coordinates changes a.
    original = check_basis(base, q, v, direction)
    other = bases["sign_flip"]
    wrong_direction = np.einsum("s,sijk->ijk", original["coordinates"], other)
    wrong = check_basis(other, q, v, wrong_direction)
    assert abs(wrong["support"] - original["support"]) > 100 * ATOL
    source_paths = [Path(__file__).resolve(), REFERENCE,
                    ROOT / "htt/src/common/tensor_functionals.py"]
    return {"status": "FIXED_AMBIENT_TARGET_NUMERICALLY_REPRODUCED", "owner": "common numerical validation",
            "claim_tier": "DIAGNOSTIC_ONLY", "transfer_source": "none", "tolerance": ATOL,
            "case": {"q": q.tolist(), "v": v.tolist(), "ambient_direction": direction.tolist()},
            "reference": {"support": oracle["support"], "eta": oracle["eta"],
                          "ambient_witness": oracle["witness"].tolist()},
            "basis_count": len(rows), "comparisons": rows,
            "negative_control": {"same_coordinates_change_ambient_target": True,
                                 "support_difference": wrong["support"] - original["support"]},
            "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in source_paths},
            "runtime": {"python": platform.python_version(), "numpy": np.__version__},
            "limits": ["New explicitly fixed ambient target; original 1.407526/1.113440 targets remain incomparable.",
                       "Floating point comparison with an analytic Cartesian reference; not interval certification or independent four-axis CAS.",
                       "Fixed q and interior fibre only; uncertain q and eta=1 refusal remain unchanged.",
                       "No observation law, physical confidence coverage or alpha consumption."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = compare()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "support": result["reference"]["support"],
                      "basis_count": result["basis_count"]}))


if __name__ == "__main__":
    main()
