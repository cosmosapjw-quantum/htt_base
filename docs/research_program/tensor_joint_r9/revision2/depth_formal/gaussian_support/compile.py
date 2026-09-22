#!/usr/bin/env python3
"""Compile only the D2 support component against the existing pinned cache."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path,
                        default=Path("/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[6]
    formal = root / "formal"
    source = formal / "R9Depth/GaussianSupport.lean"
    helper_path = Path(__file__).resolve().parent.parent / "law_support/compile.py"
    helper = runpy.run_path(str(helper_path))
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    raw = source.read_bytes()
    (out / "source.lean").write_bytes(raw)
    mathlib = args.cache / "packages/mathlib"
    toolchain = (formal / "lean-toolchain").read_text().strip()
    commit = subprocess.check_output(
        ["git", "-C", str(mathlib), "rev-parse", "HEAD"], text=True).strip()
    if commit != helper["PIN"]:
        raise RuntimeError("shared mathlib differs from the fixed source pin")
    if (mathlib / "lean-toolchain").read_text().strip() != toolchain:
        raise RuntimeError("shared mathlib and project toolchain differ")
    paths = sorted(str(p.resolve()) for p in args.cache.glob("packages/*/.lake/build/lib/lean"))
    env = dict(os.environ, LEAN_PATH=os.pathsep.join(paths))
    version = subprocess.check_output(
        ["lake", "env", "lean", "--version"], cwd=formal, env=env, text=True).strip()
    result = helper["_compile"](["lake", "env", "lean", str(source)], formal, env)
    result.update(
        cwd=str(formal), source_sha256=hashlib.sha256(raw).hexdigest(),
        source_changed=source.read_bytes() != raw, mathlib_commit=commit,
        lean_toolchain=toolchain, lean_version=version, LEAN_PATH=paths,
        runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        helper_sha256=hashlib.sha256(helper_path.read_bytes()).hexdigest(),
        head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        authorship="HOST_CODEX", scope="D2_SUPPORT_COMPONENT_ONLY",
    )
    output = str(result["stdout"]) + str(result["stderr"])
    result["axiom_check"] = {
        "sorryAx_present": "sorryAx" in output,
        "printed_declarations": sum("depends on axioms:" in line for line in output.splitlines()),
        "expected_declarations": raw.count(b"#print axioms "),
    }
    checks = result["axiom_check"]
    passed = (result["exit_code"] == 0 and not result["source_changed"]
              and not checks["sorryAx_present"] and checks["expected_declarations"] > 0
              and checks["printed_declarations"] == checks["expected_declarations"])
    result["status"] = "HOST_LEAN_COMPILED_SCOPED" if passed else "NON_PASS"
    (out / "execution.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "output": str(out),
                      "source_sha256": result["source_sha256"]}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
