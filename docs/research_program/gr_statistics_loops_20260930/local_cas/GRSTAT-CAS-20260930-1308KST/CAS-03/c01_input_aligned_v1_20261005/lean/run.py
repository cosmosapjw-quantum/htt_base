#!/usr/bin/python3.12
"""Pinned, source-bound Lean execution for the frozen CAS-03-C01 component."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
HERE = ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-03/c01_input_aligned_v1_20261005/lean"
FORMAL = ROOT / "formal_mathlib"
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUTS = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = HERE / "C01.lean"
EXPECTED = {
    CONTRACT: "4d3a35a731ce79d47490d54843239a5bf3f7c670015916356b95504cf5be6f3f",
    INPUTS: "a5189ee52fc769c284c604a4caf29051f0256973d5c5bf9dc0f439a4acecdb46",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    FORMAL / "lean-toolchain": "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    FORMAL / "lake-manifest.json": "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed",
}
THEOREMS = (
    "toMatrix_fromMatrix", "b_zero_iff_eigen", "metric_coefficient_unique",
    "rest_time_column", "rest_block", "phi_future", "fibre_chart",
    "phi_injective", "spatial_inverse", "qFull_fibre", "qLine_fibre",
    "qPoint_fibre",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(label: str, argv: list[str], cwd: Path, timeout: int) -> dict:
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        stdout, stderr, code = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        stderr += f"\nTIMEOUT after {timeout} seconds\n"
        code = 124
    out_path, err_path = HERE / f"{label}.stdout.log", HERE / f"{label}.stderr.log"
    out_path.write_text(stdout)
    err_path.write_text(stderr)
    return {
        "argv": argv, "cwd": str(cwd), "exit_code": code,
        "stdout_log": str(out_path.relative_to(ROOT)),
        "stderr_log": str(err_path.relative_to(ROOT)),
        "stdout_sha256": sha(out_path), "stderr_sha256": sha(err_path),
    }


def main() -> int:
    commands = []
    input_hashes = {str(path.relative_to(ROOT)): sha(path) for path in EXPECTED}
    hashes_ok = all(sha(path) == wanted for path, wanted in EXPECTED.items())
    source_before = sha(SOURCE)
    source_text = SOURCE.read_text()
    forbidden = re.findall(r"\b(?:sorry|admit|axiom)\b", source_text)
    for i in range(1, 8):
        name = f"attempt{i:02d}"
        hfile, lfile, efile = (HERE / f"{name}.{suffix}" for suffix in ("sha256", "log", "exit"))
        if not all(p.exists() for p in (hfile, lfile, efile)):
            continue
        commands.append({
            "argv": ["timeout", "180", "env", "ELAN_TOOLCHAIN=leanprover/lean4:v4.31.0",
                     "lake", "env", "lean", str(Path("..") / SOURCE.relative_to(ROOT))],
            "cwd": str(FORMAL), "exit_code": int(efile.read_text().strip()),
            "combined_raw_log": str(lfile.relative_to(ROOT)),
            "combined_raw_log_sha256": sha(lfile),
            "source_binding": hfile.read_text().split()[0],
            "source_snapshot_available": False,
        })
    commands.append(run_command("lean_version", ["env", "ELAN_TOOLCHAIN=leanprover/lean4:v4.31.0",
                                              "lean", "--version"], ROOT, 30))
    commands.append(run_command("mathlib_revision", ["git", "rev-parse", "HEAD"],
                                FORMAL / ".lake/packages/mathlib", 30))
    compile_cmd = ["env", "ELAN_TOOLCHAIN=leanprover/lean4:v4.31.0", "lake", "env", "lean", str(SOURCE)]
    commands.append(run_command("final_compile", compile_cmd, FORMAL, 3000))
    output = (HERE / "final_compile.stdout.log").read_text() + (HERE / "final_compile.stderr.log").read_text()
    source_after = sha(SOURCE)
    axiom_lines = re.findall(r"'CAS03C01\.([^']+)' depends on axioms: \[([^]]*)\]", output)
    expected_axioms = {"propext", "Classical.choice", "Quot.sound"}
    axioms_ok = (len(axiom_lines) == len(THEOREMS)
                 and {name for name, _ in axiom_lines} == set(THEOREMS)
                 and all(set(a.split(", ")) <= expected_axioms for _, a in axiom_lines))
    version_ok = "Lean (version 4.31.0" in (HERE / "lean_version.stdout.log").read_text()
    mathlib_ok = (HERE / "mathlib_revision.stdout.log").read_text().strip() == "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
    passed = (hashes_ok and not forbidden and source_before == source_after
              and commands[-1]["exit_code"] == 0 and axioms_ok and version_ok and mathlib_ok)
    result = {
        "axis": "lean", "status": "PASS" if passed else "FAIL",
        "contract_sha256": EXPECTED[CONTRACT], "evidence_class": "exact",
        "checks": {"CAS-03-C01": bool(passed)},
        "domain_assumption_diff": [], "counterexample": None, "witness": None,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256_before": source_before, "source_sha256_after": source_after,
        "input_sha256": input_hashes, "commands": commands,
        "axioms": {name: a.split(", ") for name, a in axiom_lines},
        "statement_alignment": (
            "Arbitrary symmetric real 4x4 covariant S is represented by its time-time, "
            "time-space, symmetric space-space blocks. Fixed diag(-1,1,1,1) metric; "
            "s_t=-u^T S u on the future unit mass shell. Proved Bu=0 iff raised S eigen "
            "equation, unique eigen coefficient, derived zero time row/column at e0, "
            "trace-free rest D assumption, exact positive-root future kernel chart and "
            "inverse/injectivity, and frozen full/line/singleton diagonal controls."
        ),
        "limitations": [
            "Finite CAS-03-C01 component only; no universal timelike eigenline existence, "
            "smooth field, physical realization, other CAS03 components, or scientific admission.",
            "Earlier development attempts preserve hash and raw compiler output; their former source bytes were not snapshotted."
        ],
        "author_runtime": "registered native Codex child; observed model metadata not available to runner",
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
