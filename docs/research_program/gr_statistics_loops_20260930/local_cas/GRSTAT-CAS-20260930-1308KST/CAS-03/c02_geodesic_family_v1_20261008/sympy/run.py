#!/usr/bin/env python3
"""Independent SymPy axis for CAS-03-C02.

Permitted inputs are limited to EXECUTION_CONTRACT.json, ADMITTED_INPUTS.json,
and COMMON_SPEC.md.  The script proves the contracted family difference and
exhausts the chi=0 diagonal zero/nonzero rank strata, including repeated
nonzero and all-zero controls.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from itertools import product
from pathlib import Path

import sympy as sp


AXIS_DIR = Path(__file__).resolve().parent
RUN_ROOT = AXIS_DIR.parent
REPO_ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
CONTRACT = RUN_ROOT / "EXECUTION_CONTRACT.json"
ADMITTED = RUN_ROOT / "ADMITTED_INPUTS.json"
COMMON = REPO_ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
RESULT = AXIS_DIR / "result.json"

EXPECTED_HASHES = {
    "EXECUTION_CONTRACT.json": "feb9aa499860fe3beb6b2d671227c69fcad9cbafde2b6a7f806a95e80211da66",
    "ADMITTED_INPUTS.json": "14e2c2843ff9791656488613ced678198d9f37beb246d8c15b6fba6530af03d1",
    "COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def vector_strings(vectors: list[sp.Matrix]) -> list[list[str]]:
    return [[str(entry) for entry in vector] for vector in vectors]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    admitted = json.loads(ADMITTED.read_text(encoding="utf-8"))

    input_paths = {
        "EXECUTION_CONTRACT.json": CONTRACT,
        "ADMITTED_INPUTS.json": ADMITTED,
        "COMMON_SPEC.md": COMMON,
    }
    observed_hashes = {name: sha256(path) for name, path in input_paths.items()}
    require(observed_hashes == EXPECTED_HASHES, "frozen input hash mismatch")
    require(contract["identity"]["contract_id"] == "GRSTAT-20260930-CAS-03-C02-GEODESIC-FAMILY-V1", "contract identity mismatch")
    require(admitted["component"] == "CAS-03-C02", "admitted component mismatch")

    epsilon, b2, b3, chi, n1, n2, n3 = sp.symbols(
        "epsilon b2 b3 chi n1 n2 n3", real=True
    )
    s = sp.sinh(chi)
    c = sp.cosh(chi)
    K = sp.Matrix([-1, n1, n2, n3])
    rchi_flat = sp.Matrix([-s, c, 0, 0])
    e2_flat = sp.Matrix([0, 0, 1, 0])
    e3_flat = sp.Matrix([0, 0, 0, 1])
    B = (
        epsilon * (rchi_flat * rchi_flat.T)
        + b2 * (e2_flat * e2_flat.T)
        + b3 * (e3_flat * e3_flat.T)
    )
    B0 = B.subs(chi, 0)
    quadratic = sp.expand((K.T * B * K)[0])
    quadratic0 = sp.expand((K.T * B0 * K)[0])
    difference = sp.expand(quadratic - quadratic0)
    target = epsilon * (s**2 + 2 * s * c * n1 + s**2 * n1**2)
    difference_residual = sp.trigsimp(sp.expand(difference - target))
    require(difference_residual == 0, "family-difference residual is nonzero")

    spatial0 = B0.extract([1, 2, 3], [1, 2, 3])
    expected_spatial0 = sp.diag(epsilon, b2, b3)
    require(spatial0 == expected_spatial0, "chi=0 spatial block mismatch")

    nonzero = sp.symbols("epsilon_nz b2_nz b3_nz", real=True, nonzero=True)
    standard_basis = [sp.eye(3).col(index) for index in range(3)]
    strata = []
    for zero_mask in product([False, True], repeat=3):
        diagonal = [sp.Integer(0) if is_zero else nonzero[i] for i, is_zero in enumerate(zero_mask)]
        matrix = sp.diag(*diagonal)
        nullspace = matrix.nullspace()
        expected_kernel = [standard_basis[i] for i, is_zero in enumerate(zero_mask) if is_zero]
        rank = matrix.rank()
        expected_rank = 3 - sum(zero_mask)
        require(rank == expected_rank, f"rank mismatch for zero mask {zero_mask}")
        require(nullspace == expected_kernel, f"kernel mismatch for zero mask {zero_mask}")
        require(len(nullspace) == sum(zero_mask), f"nullity mismatch for zero mask {zero_mask}")
        strata.append(
            {
                "zero_mask_epsilon_b2_b3": list(zero_mask),
                "diagonal": [str(entry) for entry in diagonal],
                "rank": rank,
                "kernel_dimension": len(nullspace),
                "kernel_basis": vector_strings(nullspace),
            }
        )

    a, d = sp.symbols("a d", real=True, nonzero=True)
    repeated_cases = [
        ("all_three_equal_nonzero", sp.diag(a, a, a), 3, []),
        ("epsilon_b2_equal_nonzero", sp.diag(a, a, d), 3, []),
        ("epsilon_b2_equal_b3_zero", sp.diag(a, a, 0), 2, [standard_basis[2]]),
        ("epsilon_b3_equal_b2_zero", sp.diag(a, 0, a), 2, [standard_basis[1]]),
        ("b2_b3_equal_epsilon_zero", sp.diag(0, a, a), 2, [standard_basis[0]]),
        ("all_zero", sp.zeros(3), 0, standard_basis),
    ]
    repeated_controls = []
    for name, matrix, expected_rank, expected_kernel in repeated_cases:
        rank = matrix.rank()
        nullspace = matrix.nullspace()
        require(rank == expected_rank, f"rank mismatch for repeated control {name}")
        require(nullspace == expected_kernel, f"kernel mismatch for repeated control {name}")
        repeated_controls.append(
            {
                "name": name,
                "matrix": [[str(entry) for entry in row] for row in matrix.tolist()],
                "rank": rank,
                "kernel_dimension": len(nullspace),
                "kernel_basis": vector_strings(nullspace),
            }
        )

    require(len(strata) == 8, "zero/nonzero stratum enumeration is incomplete")
    require(strata[-1]["rank"] == 0 and strata[-1]["kernel_dimension"] == 3, "all-zero stratum failed")

    source_hash = sha256(Path(__file__).resolve())
    result = {
        "schema": "htt.cas.axis-result.v1",
        "axis": "sympy",
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": observed_hashes["EXECUTION_CONTRACT.json"],
        "status": "PASS",
        "checks": {"CAS-03-C02": True},
        "counterexample": None,
        "evidence_class": "exact",
        "statement_alignment": {
            "family_difference": "PASS",
            "chi0_spatial_block": "PASS",
            "complete_zero_nonzero_rank_kernel_strata": "PASS",
            "repeated_nonzero_controls": "PASS",
            "all_zero_control": "PASS",
        },
        "domain_assumption_diff": [],
        "proof": {
            "quadratic_form": str(quadratic),
            "chi0_quadratic_form": str(quadratic0),
            "difference_before_hyperbolic_reduction": str(difference),
            "contract_target": str(target),
            "exact_residual": str(difference_residual),
            "chi0_spatial_block": [[str(entry) for entry in row] for row in spatial0.tolist()],
            "rank_kernel_strata": strata,
            "repeated_and_all_zero_controls": repeated_controls,
            "sphere_relation_used": False,
            "sphere_relation_note": "The exact identity is independent of n2,n3 and therefore holds on the contracted unit sphere without using a weakened domain.",
        },
        "source_input_hashes": {
            "source": {"path": str(Path(__file__).resolve().relative_to(REPO_ROOT)), "sha256": source_hash},
            "inputs": [
                {"path": str(path.resolve().relative_to(REPO_ROOT)), "sha256": observed_hashes[name]}
                for name, path in input_paths.items()
            ],
        },
        "observed_toolchain": {
            "argv": [sys.executable, *sys.argv],
            "cwd": os.getcwd(),
            "exit_code": 0,
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
            "sympy_version": sp.__version__,
            "sympy_path": sp.__file__,
        },
        "runtime_identity": {
            "launch": None,
            "authority": "unavailable",
            "model": "UNKNOWN",
            "effort": "UNKNOWN",
        },
        "claim_ceiling": "CAS-03-C02 finite geodesic family only",
        "remaining_obligations": ["CAS03 C03", "eigenfield existence/IFT", "science"],
        "scientific_admission": "HOLD",
    }

    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    RESULT.write_text(serialized, encoding="utf-8")
    gate_envelope = {
        "status": result["status"],
        "checks": result["checks"],
        "domain_assumption_diff": result["domain_assumption_diff"],
        "counterexample": result["counterexample"],
        "result_path": str(RESULT.relative_to(REPO_ROOT)),
    }
    sys.stdout.write(json.dumps(gate_envelope, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
