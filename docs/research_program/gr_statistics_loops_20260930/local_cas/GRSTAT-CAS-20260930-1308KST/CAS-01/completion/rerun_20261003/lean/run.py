#!/usr/bin/env python3
"""Execute the independent pinned Lean CAS-01 axis and preserve raw evidence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
FORMAL = REPO / "formal_mathlib"
CONTRACT_REL = Path("docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-01/EXECUTION_CONTRACT.json")
COMMON_REL = Path("docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md")
EXPECTED = {
    CONTRACT_REL: "edc2df3348528a699b987ae1893ab76630e96b9915d11117db7916d005c406f1",
    COMMON_REL: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    Path("formal/lean-toolchain"): "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    Path("formal_mathlib/lean-toolchain"): "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    Path("formal_mathlib/lake-manifest.json"): "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed",
}
THEOREMS = {
    "CAS-01-C01": ["B_unit", "B_shift", "null_cone_kernel", "B_symmetric"],
    "CAS-01-C02": ["Q_right_null", "Q_symmetric_part", "Q_left_acceleration",
                   "C02_from_symmetric_source",
                   "D_spatial", "sigma_spatial", "sigma_tracefree", "projected_eq_D"],
    "CAS-01-C03": ["rest_H_decomposition", "C03_B_rest",
                   "general_sourceward_harmonics",
                   "traceg_rest", "cov_rest"],
    "CAS-01-C04": ["fullNormalized_origin", "fullNormalized_coordinate_derivative",
                   "C04_from_symmetric_source"],
}
HEAD = "bfdb1ef6f9767c06e4fb610fd572a41990e2a26f"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(argv: list[str], cwd: Path, label: str, timeout: int = 120) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    try:
        p = subprocess.run(argv, cwd=cwd, text=True, capture_output=True,
                           timeout=timeout, check=False)
        stdout, stderr, code, timed_out = p.stdout, p.stderr, p.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        code, timed_out = None, True
    (HERE / f"{label}.stdout").write_text(stdout)
    (HERE / f"{label}.stderr").write_text(stderr)
    (HERE / f"{label}.exit").write_text("TIMEOUT\n" if timed_out else f"{code}\n")
    return {"argv": argv, "cwd": str(cwd), "started_at": started,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "exit_code": code, "timed_out": timed_out,
            "stdout_path": f"{label}.stdout", "stderr_path": f"{label}.stderr",
            "stdout_sha256": sha256(HERE / f"{label}.stdout"),
            "stderr_sha256": sha256(HERE / f"{label}.stderr")}


def main() -> None:
    if not (REPO / ".git").exists() or not HERE.is_relative_to(REPO):
        raise RuntimeError("frozen repository/worktree identity mismatch")
    hashes = {str(path): sha256(REPO / path) for path in EXPECTED}
    source_hashes = {"Main.lean": sha256(HERE / "Main.lean"),
                     "run.py": sha256(HERE / "run.py")}
    identity = execute(["git", "rev-parse", "HEAD"], REPO, "git_head")
    version = execute(["lake", "env", "lean", "--version"], FORMAL, "lean_version")
    manifests_ok = all(hashes[str(path)] == expected for path, expected in EXPECTED.items())
    head_ok = identity["exit_code"] == 0 and (HERE / "git_head.stdout").read_text().strip() == HEAD
    version_ok = version["exit_code"] == 0 and "version 4.31.0" in (HERE / "lean_version.stdout").read_text()
    commands = [identity, version]
    compile_ok = False
    parsed: dict[str, set[str]] = {}
    if manifests_ok and head_ok and version_ok:
        source_arg = str((HERE / "Main.lean").relative_to(FORMAL)) if HERE.is_relative_to(FORMAL) else str(HERE / "Main.lean")
        compiler = execute(["lake", "env", "lean", source_arg], FORMAL, "lean", timeout=3600)
        commands.append(compiler)
        stdout = (HERE / "lean.stdout").read_text()
        compile_ok = compiler["exit_code"] == 0 and not compiler["timed_out"]
        for name, axioms in re.findall(
            r"'GRSTATCAS01\.([A-Za-z0-9_]+)' depends on axioms: \[([^]]*)\]", stdout
        ):
            parsed[name] = {item.strip() for item in axioms.split(",") if item.strip()}
    else:
        (HERE / "lean.stdout").write_text("")
        (HERE / "lean.stderr").write_text("Frozen identity or toolchain mismatch; compiler not invoked.\n")
        (HERE / "lean.exit").write_text("NOT_RUN\n")
    checks = {
        component: compile_ok and all(name in parsed and parsed[name] <= ALLOWED_AXIOMS
                                      for name in names)
        for component, names in THEOREMS.items()
    }
    domain_diff = [] if manifests_ok and head_ok and version_ok else [
        "frozen repository, contract, common specification, or toolchain mismatch"
    ]
    payload = {"checks": checks, "domain_assumption_diff": domain_diff,
               "counterexample": None}
    status = "PASS" if all(checks.values()) and not domain_diff else (
        "MISALIGNED_ASSUMPTIONS" if domain_diff else "INCONCLUSIVE"
    )
    receipt = {
        "axis": "lean", "status": status,
        "contract_sha256": hashes[str(CONTRACT_REL)], "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "run_id": "GRSTAT-CAS-20260930-1308KST",
        "task_id": "GRSTAT-CAS-20260930-1308KST-CAS-01-lean",
        "child_id": None,
        "execution_origin": "Host deterministic rerun of inherited independent Lean source",
        "inherited_author_child_id": "01a0f9ba-def0-7731-9a31-7c410ebae1a7",
        "repo_root": str(REPO), "head_commit": HEAD,
        "author_model_observed": None,
        "independence_mode": "inherited-independent-source; Host post-adjudication rerun",
        "commands": commands, "input_sha256": hashes,
        "source_sha256": source_hashes,
        "required_theorems_by_component": THEOREMS,
        "printed_axioms": {name: sorted(items) for name, items in parsed.items()},
        "payload": payload,
        "remaining_analytic_obligations": [
            "Jacobi vertex Taylor order and screen invariance",
            "smooth timelike neighborhood, local flow, and source extension",
        ],
        "claim_ceiling": "specified finite/local mathematical components only; no scientific admission",
    }
    (HERE / "AXIS_RESULT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, separators=(",", ":")))


if __name__ == "__main__":
    main()
