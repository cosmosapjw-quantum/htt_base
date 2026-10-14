#!/usr/bin/env python3
"""Pinned, source-bound Lean execution for the adopted finite CAS-06 successor."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[9]
BASE = Path(__file__).resolve().parent
SUCCESSOR = BASE.parent
MATHLIB = ROOT / "formal_mathlib"
SCALAR = SUCCESSOR.parent / "lean" / "Proof.lean"
SOURCES = [BASE / f"{name}.lean" for name in
           ("CAS06ScalarAccepted", "CAS06Foundation", "C03Action", "CAS06Bundles", "Proof")]
MODULES = ["CAS06ScalarAccepted", "CAS06Foundation", "C03Action", "CAS06Bundles"]
CONTRACT = SUCCESSOR / "EXECUTION_CONTRACT.json"
ADMITTED = SUCCESSOR / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
RUNSPEC = SUCCESSOR / "RUN_SPEC.json"
TOOLCHAIN = ROOT / "formal/lean-toolchain"
MATHLIB_TOOLCHAIN = MATHLIB / "lean-toolchain"
MANIFEST = MATHLIB / "lake-manifest.json"
EXPECTED = {
    CONTRACT: "9936c95ac128126d34688bbd8ece9fb90c92aa7dfeea8fa7b41716ab449e88f3",
    ADMITTED: "711de321c374a85b4b0414d5df1f8a62b55368f73c2a3d31e502e209af8793eb",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    RUNSPEC: "98c3c3677a658518676da5b351fadc376cdbda4f9dee4a33b5b347b08f5a461c",
    SCALAR: "83352ea65bb391d2bd17bf4e25e6149dc5f1cff14f75c28de1a7f30b1d12f46e",
    TOOLCHAIN: "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    MATHLIB_TOOLCHAIN: "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee",
    MANIFEST: "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed",
}
PINNED_MATHLIB_REV = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
CORE_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
REQUIRED_PROOFS = {
    "CAS-06-C01": ["CAS06Bundles.C01_coordinate_riemann_from_metric",
                   "CAS06Bundles.C01_TOV_metric_bundle"],
    "CAS-06-C02": ["CAS06Bundles.C02_matched_riemann_from_metric",
                   "CAS06Bundles.C02_matched_full_bundle"],
    "CAS-06-C03": ["CAS06Action.actionDensity_metric_stress_variation",
                   "CAS06Action.actionDensity_scalar_hasDerivAt",
                   "CAS06Action.C03_action_event_bundle",
                   "CAS06Action.matched_action_tov_second_lapse_jet"],
    "CAS-06-C04": ["CAS06Bundles.C04_actual_family_positive_limit"],
}


def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def identity() -> dict[str, str | None]:
    return {str(path.relative_to(ROOT)): sha(path)
            for path in (*EXPECTED, *SOURCES, BASE / "run.py")}


def olean_identity() -> dict[str, str | None]:
    return {name: sha(BASE / f"{name}.olean") for name in MODULES}


def call(name: str, argv: list[str], cwd: Path, out: Path, timeout: int,
         deadline: float, env_extra: dict[str, str] | None = None) -> dict:
    env = dict(os.environ, ELAN_TOOLCHAIN="leanprover/lean4:v4.31.0")
    if env_extra:
        env.update(env_extra)
    allowed = max(1, min(timeout, int(deadline - time.monotonic())))
    p = subprocess.Popen(argv, cwd=cwd, env=env, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         start_new_session=True)
    try:
        stdout, stderr = p.communicate(timeout=allowed)
        status, timed_out = p.returncode, False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = p.communicate()
        status, timed_out = None, True
    stdout_path = out / f"{name}.stdout.log"
    stderr_path = out / f"{name}.stderr.log"
    stdout_path.write_text(stdout)
    stderr_path.write_text(stderr)
    return {"name": name, "argv": argv, "cwd": str(cwd),
            "env_overrides": {"ELAN_TOOLCHAIN": env["ELAN_TOOLCHAIN"],
                              "LEAN_PATH": env_extra.get("LEAN_PATH") if env_extra else None},
            "timeout_seconds": allowed, "exit_code": status, "timed_out": timed_out,
            "stdout_log": str(stdout_path.relative_to(ROOT)),
            "stderr_log": str(stderr_path.relative_to(ROOT))}


def axioms_from_log(log: str) -> dict[str, list[str]]:
    found = {}
    for name, words in re.findall(r"^'([^']+)' depends on axioms: \[([^\]]*)\]$", log, re.M):
        found[name] = [word.strip() for word in words.split(",") if word.strip()]
    return found


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        raise SystemExit("frozen runner requires repository-root cwd")
    started = dt.datetime.now(dt.timezone.utc)
    deadline = time.monotonic() + 3500
    out = BASE / "attempts" / started.strftime("%Y%m%dT%H%M%S%fZ")
    out.mkdir(parents=True, exist_ok=False)
    for source in SOURCES:
        shutil.copyfile(source, out / source.name)
    shutil.copyfile(BASE / "run.py", out / "run.py")
    before = identity()
    oleans_before = olean_identity()
    mismatches = {str(path.relative_to(ROOT)): [sha(path), wanted]
                  for path, wanted in EXPECTED.items() if sha(path) != wanted}
    accepted_copy_equal = sha(SOURCES[0]) == EXPECTED[SCALAR]
    source_declaration_violations = {
        source.name: re.findall(r"(?m)^\s*(?:axiom|constant|sorry|admit)\b", source.read_text())
        for source in SOURCES
        if re.search(r"(?m)^\s*(?:axiom|constant|sorry|admit)\b", source.read_text())
    }
    commands = []
    build_names = []
    if not mismatches and accepted_copy_equal and not source_declaration_violations:
        commands.append(call("lean_version", ["lean", "--version"], MATHLIB, out, 30, deadline))
        commands.append(call("lake_version", ["lake", "--version"], MATHLIB, out, 30, deadline))
        commands.append(call("mathlib_revision", ["git", "rev-parse", "HEAD"],
                             MATHLIB / ".lake/packages/mathlib", out, 30, deadline))
        commands.append(call("lake_lean_path", ["lake", "env", "printenv", "LEAN_PATH"],
                             MATHLIB, out, 30, deadline))
        versions_ok = all(c["exit_code"] == 0 and not c["timed_out"] for c in commands)
        observed_rev = (out / "mathlib_revision.stdout.log").read_text().strip()
        if versions_ok and observed_rev == PINNED_MATHLIB_REV:
            lean_path = str(BASE) + ":" + (out / "lake_lean_path.stdout.log").read_text().strip()
            for module in MODULES:
                cmd = call(f"compile_{module}",
                           ["lake", "env", "lean", "-j1", "-R", str(BASE),
                            "-o", str(BASE / f"{module}.olean"),
                            str(BASE / f"{module}.lean")],
                           MATHLIB, out, 700, deadline, {"LEAN_PATH": lean_path})
                commands.append(cmd)
                if cmd["exit_code"] != 0 or cmd["timed_out"]:
                    break
                shutil.copyfile(BASE / f"{module}.olean", out / f"{module}.olean")
                build_names.append(module)
            if len(build_names) == len(MODULES):
                commands.append(call("adopted_proof",
                                     ["lake", "env", "lean", "-j1", str(BASE / "Proof.lean")],
                                     MATHLIB, out, 700, deadline, {"LEAN_PATH": lean_path}))
    after = identity()
    oleans_after = olean_identity()
    drift = {p: [v, after.get(p)] for p, v in before.items() if after.get(p) != v}
    snapshot_olean_sha256 = {name: sha(out / f"{name}.olean") for name in MODULES}
    olean_binding = all(snapshot_olean_sha256[name] == oleans_after[name]
                        and snapshot_olean_sha256[name] is not None for name in MODULES)
    compiled = (len(build_names) == len(MODULES)
                and any(c["name"] == "adopted_proof" and c["exit_code"] == 0
                        and not c["timed_out"] for c in commands))
    all_logs = "\n".join((out / f"{c['name']}.stdout.log").read_text() + "\n" +
                         (out / f"{c['name']}.stderr.log").read_text() for c in commands)
    proof_log = ((out / "adopted_proof.stdout.log").read_text()
                 if (out / "adopted_proof.stdout.log").exists() else "")
    proof_axioms = axioms_from_log(proof_log)
    all_axioms = axioms_from_log(all_logs)
    bad_axioms = {name: words for name, words in all_axioms.items()
                  if not set(words).issubset(CORE_AXIOMS)}
    raw_errors = bool(re.search(r"(?:^|\n)[^\n]*\berror:|sorryAx", all_logs))
    commands_ok = bool(commands) and all(c["exit_code"] == 0 and not c["timed_out"]
                                        for c in commands)
    common_ok = (commands_ok and compiled and accepted_copy_equal and olean_binding
                 and not mismatches and not drift and not source_declaration_violations
                 and not raw_errors and not bad_axioms
                 and (out / "mathlib_revision.stdout.log").read_text().strip()
                     == PINNED_MATHLIB_REV)
    checks = {component: common_ok and all(name in proof_axioms and
                set(proof_axioms[name]).issubset(CORE_AXIOMS) for name in names)
              for component, names in REQUIRED_PROOFS.items()}
    passed = all(checks.values())
    result = {
        "axis": "lean", "status": "PASS" if passed else "INCONCLUSIVE",
        "evidence_class": "exact", "contract_sha256": EXPECTED[CONTRACT],
        "started_at": started.isoformat(),
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "attempt_dir": str(out.relative_to(ROOT)), "commands": commands,
        "checks": checks, "domain_assumption_diff": [],
        "counterexample": None, "witness": None,
        "source_input_toolchain_sha256_before": before,
        "source_input_toolchain_sha256_after": after,
        "compiled_olean_sha256_before": oleans_before,
        "compiled_olean_sha256_after": oleans_after,
        "snapshot_olean_sha256": snapshot_olean_sha256,
        "fresh_olean_source_binding": olean_binding,
        "accepted_scalar_copy_matches_admitted_sha256": accepted_copy_equal,
        "expected_identity_mismatches": mismatches,
        "during_run_hash_drift": drift,
        "source_declaration_violations": source_declaration_violations,
        "axioms_in_entrypoint": proof_axioms,
        "disallowed_axioms_in_raw_logs": bad_axioms,
        "raw_compiler_error_or_sorryAx": raw_errors,
        "toolchain": {
            "declared_lean": "4.31.0",
            "declared_mathlib_rev": PINNED_MATHLIB_REV,
            "observed_lean_version": (out / "lean_version.stdout.log").read_text().strip()
                if (out / "lean_version.stdout.log").exists() else None,
            "observed_lake_version": (out / "lake_version.stdout.log").read_text().strip()
                if (out / "lake_version.stdout.log").exists() else None,
            "observed_mathlib_rev": (out / "mathlib_revision.stdout.log").read_text().strip()
                if (out / "mathlib_revision.stdout.log").exists() else None,
        },
        "component_status": {component: "PROVED_FINITE_FORMAL_CANDIDATE"
                             if yes else "INCONCLUSIVE" for component, yes in checks.items()},
        "statement_alignment": "Finite/local conditional metric, curvature, action and actual-germ limit theorems only; analytic existence, persistence, whole-interval action/TOV identity and distinct-germ interpretation remain HOLD.",
        "first_full_contract_gap": None if passed else
            "One or more required source-bound Lean theorem checks or pinned execution conditions did not complete; inspect raw command logs and binding fields.",
        "scientific_admission": "HOLD",
    }
    payload = json.dumps(result, indent=2) + "\n"
    (out / "result.json").write_text(payload)
    (BASE / "result.json").write_text(payload)
    print(json.dumps({"status": result["status"], "checks": checks,
                      "result": str(BASE / "result.json"), "attempt": str(out),
                      "command_exits": {c["name"]: c["exit_code"] for c in commands}}, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
