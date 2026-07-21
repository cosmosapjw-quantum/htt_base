"""PR-186 five-axis CAS runner: Wolfram/xAct, SymPy, Sage+Singular, Lean, Rocq.

Runs each engine sequentially (no subagents), writes a per-axis result
envelope bound to the contract hash, then adjudicates via the harness
cas_gate. Lean and Rocq are kernel-independent proof-assistant lineages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CAS_DIR = REPO / "docs/generated/pr187_cas"
CONTRACT = CAS_DIR / "CAS_CONTRACT_PR187_FRAME_ORDER.json"
LEAN_TOOLCHAIN = (REPO / "formal_pr187/lean-toolchain").read_text().strip()

AXES = ("wolfram_xact", "sympy", "sage_singular", "lean", "rocq")
_PASS_TOKEN = {
    "wolfram_xact": "PR187_WOLFRAM_PASS",
    "sympy": "PR187_SYMPY_PASS",
    "sage_singular": "PR187_SAGE_PASS",
    "lean": "PR187_LEAN_PASS",
    "rocq": "coqc_exit_0",  # kernel-checked .vo, no printed token
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout, check=False)
    return proc.returncode, (proc.stdout + proc.stderr)


def _axis_cmd(axis: str) -> tuple[list[str], Path, int]:
    if axis == "wolfram_xact":
        return (["wolframscript", "-file", "wolfram/pr187_frame_order.wls"], REPO, 240)
    if axis == "sympy":
        return ([str(REPO / "venv/bin/python"), "-B",
                 "wolfram/pr187_frame_order_sympy.py"], REPO, 180)
    if axis == "sage_singular":
        return (["sage", "sage/pr187_frame_order.sage"], REPO, 420)
    if axis == "lean":
        return (["env", f"ELAN_TOOLCHAIN={LEAN_TOOLCHAIN}", "lake", "exe",
                 "pr187frame"], REPO / "formal_pr187", 420)
    if axis == "rocq":
        return (["rocq", "compile", "formal_rocq/pr187_frame_order.v"], REPO, 180)
    raise ValueError(axis)


def run_axis(axis: str, contract_sha: str) -> dict:
    cmd, cwd, timeout = _axis_cmd(axis)
    code, out = _run(cmd, cwd, timeout)
    if axis == "rocq":
        vo = REPO / "formal_rocq/pr187_frame_order.vo"
        passed = code == 0 and vo.is_file()
    else:
        passed = code == 0 and _PASS_TOKEN[axis] in out
    return {
        "schema_version": 1,
        "axis": axis,
        "status": "PASS" if passed else "FAIL",
        "contract_sha256": contract_sha,
        "evidence_class": "exact",
        "commands": [{"cmd": " ".join(cmd), "exit": code}],
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "transcript_tail": out[-1200:],
        "kernel_independent_lineage": axis in ("lean", "rocq"),
    }


def adjudicate(contract_sha: str) -> dict:
    result_paths = []
    for axis in AXES:
        env = run_axis(axis, contract_sha)
        p = CAS_DIR / f"axis_result_{axis}.json"
        p.write_text(json.dumps(env, indent=1, sort_keys=True) + "\n")
        result_paths.append(str(p.relative_to(REPO)))
        print(f"{axis}: {env['status']}")
    out_rel = "docs/generated/pr187_cas/adjudication.json"
    cmd = [str(REPO / "venv/bin/python"), "-B",
           ".agent-harness/scripts/cas_gate.py", "adjudicate",
           "--contract", str(CONTRACT.relative_to(REPO)),
           "--results", *result_paths, "--out", out_rel]
    code, out = _run(cmd, REPO, 120)
    adj = json.loads((REPO / out_rel).read_text())
    return adj


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    contract_sha = _sha(CONTRACT)
    adj = adjudicate(contract_sha)
    aggregate = adj["aggregate_status"]
    print(json.dumps({"aggregate_status": aggregate,
                      "required_axes": adj.get("required_axes"),
                      "axis_statuses": adj["axis_statuses"]}, sort_keys=True))
    ok = aggregate == "CAS_5AXIS_PASS"
    if args.check:
        return 0 if ok else 1
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
