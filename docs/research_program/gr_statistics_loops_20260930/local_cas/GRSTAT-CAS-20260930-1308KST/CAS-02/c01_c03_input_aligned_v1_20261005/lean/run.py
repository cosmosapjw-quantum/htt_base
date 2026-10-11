#!/usr/bin/python3.12
"""Frozen CAS-02 Lean axis entrypoint; writes one immutable evidence directory per attempt."""

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
import time
import uuid


REPO = Path(__file__).resolve().parents[8]
AXIS = Path(__file__).resolve().parent
TASK = AXIS.parent
FORMAL = REPO / "formal_mathlib"
SOURCE = AXIS / "Cas02.lean"
CONTRACT = TASK / "EXECUTION_CONTRACT.json"
INPUTS = TASK / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
TOOLCHAIN = FORMAL / "lean-toolchain"
MANIFEST = FORMAL / "lake-manifest.json"
PINNED = {
    CONTRACT: "f1df856a0da477256e8adfbb889001d75fd659dda6f834ea72e87f314ff844a8",
    INPUTS: "e7cfe79d7ad075899ee75f166687f40363e207ba334da3d8733fa2ab5a4b82bd",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    TOOLCHAIN: "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    MANIFEST: "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed",
}
TARGETS = (
    "Cas02.C01", "Cas02.metric_frob_norm", "Cas02.C02_anchor_second",
    "Cas02.C02_anchor_first", "Cas02.C03_hasFDerivAt", "Cas02.chartJac_apply",
    "Cas02.C03_gram", "Cas02.C03_gram_action", "Cas02.C03_transverse_iff",
    "Cas02.C03_longitudinal_span", "Cas02.C03_eigenvalue_only",
    "Cas02.C03_longitudinal_iff",
    "Cas02.C03_zero_repeated", "Cas02.C03_rapidity_bound",
    "Cas02.C03_transverse_dimension", "Cas02.C03_longitudinal_dimension",
    "Cas02.C03_zero_dimension", "Cas02.C03_transverse_eigen_exists",
    "Cas02.C03_euclidean_component_norm", "Cas02.C03_chart_future_unit",
)
CORE_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def run_command(argv: list[str], cwd: Path, timeout: int, logs: Path, name: str) -> dict:
    started = utc()
    tick = time.monotonic()
    try:
        completed = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout)
        code = completed.returncode
        out, err = completed.stdout, completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        code = None
        out, err = exc.stdout or b"", exc.stderr or b""
        timed_out = True
    except OSError as exc:
        code = None
        out, err = b"", repr(exc).encode()
        timed_out = False
    (logs / f"{name}.stdout").write_bytes(out)
    (logs / f"{name}.stderr").write_bytes(err)
    return {
        "argv": argv, "cwd": str(cwd), "timeout_seconds": timeout,
        "started_at": started, "completed_at": utc(),
        "wall_seconds": time.monotonic() - tick, "exit_code": code,
        "timed_out": timed_out,
        "stdout_path": str(logs / f"{name}.stdout"),
        "stderr_path": str(logs / f"{name}.stderr"),
    }


def main() -> int:
    if Path.cwd().resolve() != REPO:
        raise SystemExit(f"FROZEN_CWD_MISMATCH: {Path.cwd()} != {REPO}")
    attempt = AXIS / "attempts" / (dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex)
    attempt.mkdir(parents=True, exist_ok=False)
    logs = attempt / "logs"
    logs.mkdir()
    sources = attempt / "sources"
    sources.mkdir()
    snapshots = [SOURCE, Path(__file__).resolve()]
    before = {str(p.relative_to(REPO)): digest(p) for p in [*PINNED, *snapshots]}
    for p in snapshots:
        target = sources / p.name
        target.write_bytes(p.read_bytes())
        target.chmod(0o444)
    source_text = SOURCE.read_text()
    forbidden = re.findall(r"\b(?:sorry|admit|axiom)\b", re.sub(r"/-(?:.|\n)*?-|--[^\n]*", "", source_text))
    commands: list[dict] = []
    commands.append(run_command(["lake", "--version"], FORMAL, 30, logs, "lake_version"))
    commands.append(run_command(["lake", "env", "lean", "--version"], FORMAL, 30, logs, "lean_version"))
    commands.append(run_command(["git", "rev-parse", "HEAD"], FORMAL / ".lake/packages/mathlib", 30, logs, "mathlib_revision"))
    engine = ["lake", "env", "lean", str(SOURCE)]
    telemetry = shutil.which("cuhg-telemetry")
    engine_argv = ([telemetry, "run", "--project", str(REPO), "--task",
        "GRSTAT-CAS-20260930-1308KST-CAS-02", "--", *engine] if telemetry else engine)
    commands.append(run_command(engine_argv, FORMAL, 3500, logs, "proof"))
    raw = (logs / "proof.stdout").read_text(errors="replace") + (logs / "proof.stderr").read_text(errors="replace")
    # A telemetry transport failure without Lean output must not suppress the computation.
    if telemetry and commands[-1]["exit_code"] != 0 and not any(
        token in raw for token in ("depends on axioms:", ": error:", "error(lean.")
    ):
        commands.append(run_command(engine, FORMAL, 3500, logs, "proof_direct_fallback"))
        raw = (logs / "proof_direct_fallback.stdout").read_text(errors="replace") + \
              (logs / "proof_direct_fallback.stderr").read_text(errors="replace")
    final_engine = commands[-1]
    found_axioms: dict[str, list[str]] = {}
    for theorem in TARGETS:
        match = re.search(r"'" + re.escape(theorem) + r"' depends on axioms: \[([^\]]*)\]", raw)
        if match:
            found_axioms[theorem] = [a.strip() for a in match.group(1).split(",") if a.strip()]
    after = {str(p.relative_to(REPO)): digest(p) for p in [*PINNED, *snapshots]}
    input_seals_ok = all(before[str(p.relative_to(REPO))] == expected for p, expected in PINNED.items())
    source_stable = before == after
    versions_ok = (commands[0]["exit_code"] == commands[1]["exit_code"] == commands[2]["exit_code"] == 0
        and "Lean (version 4.31.0" in (logs / "lean_version.stdout").read_text(errors="replace")
        and "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f" in
            (logs / "mathlib_revision.stdout").read_text(errors="replace"))
    axioms_ok = len(found_axioms) == len(TARGETS) and all(set(v) <= CORE_AXIOMS for v in found_axioms.values())
    passed = (input_seals_ok and source_stable and versions_ok and not forbidden
        and final_engine["exit_code"] == 0 and axioms_ok)
    result = {
        "axis": "lean", "status": "PASS" if passed else "BLOCKED",
        "evidence_class": "exact", "contract_sha256": digest(CONTRACT),
        "completed_at": utc(), "commands": commands,
        "attempt_dir": str(attempt), "source_sha256": digest(SOURCE),
        "input_hashes_before": before, "input_hashes_after": after,
        "input_seals_ok": input_seals_ok, "source_stable": source_stable,
        "toolchain_bindings_ok": versions_ok, "forbidden_shortcuts": forbidden,
        "found_axioms": found_axioms, "axioms_ok": axioms_ok,
        "component_status": {c: ("PASS" if passed else "OPEN_LEMMA") for c in
            ("CAS-02-C01", "CAS-02-C02", "CAS-02-C03")},
        "scope": "C01-C03 specified finite mathematical components only; C04 NEEDS_OWNER_DECISION; science HOLD",
        "independence": "blind to sibling axes; shared GPT-family correlation disclosed; no stronger independence claimed",
        "author_runtime_observation": "Host observer records actual model/effort separately",
        "first_error": next((line for line in raw.splitlines() if ": error:" in line or "error(lean." in line), None),
    }
    (attempt / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (AXIS / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (attempt / "result.json").chmod(0o444)
    print(json.dumps({"checks": {k: value == "PASS" for k, value in result["component_status"].items()},
        "domain_assumption_diff": [], "counterexample": None, "first_gap": result["first_error"]}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
