#!/usr/bin/python3.12
"""Run the independent CAS-07-C02 Wolfram+xAct certificate and retain raw evidence."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
VERSION = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/c02_input_aligned_v1_20261005"
HERE = VERSION / "wolfram_xact"
CONTRACT = VERSION / "EXECUTION_CONTRACT.json"
INPUTS = VERSION / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = HERE / "proof.wl"
EXPECTED = {
    str(CONTRACT.relative_to(REPO)): "367ea2b4221c2ef10c93d1c49ef75d40d0f030bf79ec429a0fe1dbfeb44c219a",
    str(INPUTS.relative_to(REPO)): "84e20f628abcc4879446c6987dec21416934dece1c94e23076d6ce491939e6b0",
    str(COMMON.relative_to(REPO)): "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
MARKERS = (
    "xact_nonzero_gram", "gram_quadratic_form", "gram_determinant",
    "cauchy_lagrange_identity", "norm_expansion", "universal_rayleigh_bounds",
    "homotopy_endpoints", "homotopy_determinant_polynomial",
    "homotopy_strict_scalar_gap", "positive_sqrt_product_bound",
)


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_hashes() -> dict[str, str]:
    return {name: hash_file(REPO / name) for name in EXPECTED}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def immutable_write(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
    path.chmod(0o444)


def main() -> int:
    attempt = HERE / "attempts" / (dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:12])
    attempt.mkdir(parents=True, exist_ok=False)
    started = now()
    before = input_hashes()
    source_hash = hash_file(SOURCE)
    immutable_write(attempt / "proof.wl", SOURCE.read_bytes())
    for label, path in (("EXECUTION_CONTRACT", CONTRACT), ("ADMITTED_INPUTS", INPUTS), ("COMMON_SPEC", COMMON)):
        immutable_write(attempt / (label + path.suffix), path.read_bytes())
    argv = [shutil.which("wolframscript") or "wolframscript", "-file", str(attempt / "proof.wl")]
    proc: subprocess.CompletedProcess[bytes] | None = None
    run_error: str | None = None
    try:
        proc = subprocess.run(argv, cwd=REPO, capture_output=True, timeout=1800, check=False)
        stdout, stderr = proc.stdout, proc.stderr
        exit_code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        exit_code = None
        run_error = "wolframscript timeout after 1800 seconds"
    except OSError as exc:
        stdout, stderr = b"", repr(exc).encode()
        exit_code = None
        run_error = repr(exc)
    immutable_write(attempt / "stdout.raw", stdout)
    immutable_write(attempt / "stderr.raw", stderr)
    after = input_hashes()
    decoded = stdout.decode("utf-8", errors="replace")
    markers = {name: f"CHECK:{name}:TRUE" in decoded for name in MARKERS}
    versions = {
        "wolfram_engine": next((line.split("=", 1)[1] for line in decoded.splitlines() if line.startswith("ENGINE_VERSION=")), None),
        "xact_xtensor": next((line.split("=", 1)[1] for line in decoded.splitlines() if line.startswith("XTENSOR_VERSION=")), None),
    }
    source_ok = before == after == EXPECTED
    full = (source_ok and exit_code == 0 and all(markers.values())
            and "CAS07_C02_FULL_SCOPE_CERTIFIED=TRUE" in decoded
            and versions["wolfram_engine"] is not None and versions["xact_xtensor"] is not None)
    status = "PASS" if full else "INCONCLUSIVE"
    details = {
        "statement_alignment": "Conditional on s>0, 0<=eta<1, real arbitrary 2x2 D, and Euclidean induced ||D-sI||op<=s eta. No symmetry or determinant sign premise.",
        "proof_chain": [
            "Set E=D-sI and q=s eta. The operator norm definition implies ||Ev||2<=q||v||2 for every real v; homogeneity covers v=0. Euclidean Cauchy-Schwarz implies |<v,Ev>|<=||v||2||Ev||2, with its exact two-dimensional Lagrange identity checked in Wolfram.",
            "Wolfram real quantifier elimination certifies (s-q)^2||v||2^2<=||Dv||2^2<=(s+q)^2||v||2^2 for every vector norm u and error norm w satisfying the premise. The exact Gram expansion and determinant identity are separately checked; xAct performs a nonzero Euclidean Gram index contraction.",
            "The real symmetric positive-semidefinite Gram matrix D^T D has an orthonormal eigenbasis. Evaluating the universal Rayleigh bounds on each eigenvector puts both nonnegative singular values in [s-q,s+q]. This uses the standard finite-dimensional Euclidean spectral theorem, not a different matrix norm.",
            "For t in [0,1], D_t=sI+tE. If D_t v=0, s||v||2<=tq||v||2, impossible for v!=0 because tq<s; the strict scalar gap is machine checked. The exact determinant polynomial is continuous, never zero, and begins at s^2>0, so det D>0 by the intermediate-value theorem. This derives the positive branch.",
            "det(D^T D)=det(D)^2 and detD>0 yield detD=sigma1 sigma2. A final universal real quantifier-elimination certificate bounds sqrt(sigma1 sigma2) between s-q and s+q. Substitute q=s eta. The eta=0 boundary is included; eta=1 is excluded.",
        ],
        "subchecks": markers,
        "raw_evidence_directory": str(attempt.relative_to(REPO)),
        "input_sha256_before": before,
        "input_sha256_after": after,
        "input_sha256_expected": EXPECTED,
        "source_sha256": source_hash,
        "actual_versions": versions,
        "run_error": run_error,
    }
    result = {
        "axis": "wolfram_xact",
        "status": status,
        "contract_sha256": EXPECTED[str(CONTRACT.relative_to(REPO))],
        "checks": {"CAS-07-C02": full},
        "domain_assumption_diff": [] if source_ok else ["Frozen input hash changed during run"],
        "counterexample": None,
        "commands": [{"argv": argv, "cwd": str(REPO), "exit_code": exit_code,
                      "stdout_path": str((attempt / "stdout.raw").relative_to(REPO)),
                      "stderr_path": str((attempt / "stderr.raw").relative_to(REPO)),
                      "timeout_seconds": 1800}],
        "evidence_class": "exact",
        "started_at": started,
        "completed_at": now(),
        "details": details,
    }
    result_bytes = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    immutable_write(attempt / "result.json", result_bytes)
    (HERE / "result.json").write_bytes(result_bytes)
    print(json.dumps(result, sort_keys=True))
    return 0 if full else 2


if __name__ == "__main__":
    sys.exit(main())
