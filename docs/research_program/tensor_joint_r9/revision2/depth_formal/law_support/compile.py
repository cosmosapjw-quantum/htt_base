#!/usr/bin/env python3
"""Host-only, source-bound compile of the D3 law/support bridge."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

PIN = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path,
                        default=Path("/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[6]
    formal = root / "formal"
    source = formal / "R9Depth/LawSupport.lean"
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    mathlib = args.cache / "packages/mathlib"
    toolchain = (formal / "lean-toolchain").read_text().strip()
    if (mathlib / "lean-toolchain").read_text().strip() != toolchain:
        raise RuntimeError("mathlib and repository Lean toolchain differ")
    commit = subprocess.check_output(["git", "-C", str(mathlib), "rev-parse", "HEAD"], text=True).strip()
    if commit != PIN:
        raise RuntimeError("shared mathlib source differs from pinned commit")
    paths = sorted(str(p.resolve()) for p in args.cache.glob("packages/*/.lake/build/lib/lean"))
    started = time.monotonic()
    records: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="r9-law-support-") as td:
        module_root = Path(td)
        (module_root / "R9Depth").mkdir()
        env = dict(os.environ, LEAN_PATH=os.pathsep.join([str(module_root), *paths]))
        for dep in ("BlockBridge", "Covariance"):
            argv = ["lake", "env", "lean", "-o", str(module_root / f"R9Depth/{dep}.olean"),
                    str(formal / f"R9Depth/{dep}.lean")]
            proc = subprocess.run(argv, cwd=formal, env=env, text=True,
                                  capture_output=True, timeout=120)
            records.append({"argv": argv, "exit_code": proc.returncode,
                            "stdout": proc.stdout, "stderr": proc.stderr})
            if proc.returncode != 0:
                break
        if all(r["exit_code"] == 0 for r in records):
            argv = ["lake", "env", "lean", str(source)]
            proc = subprocess.run(argv, cwd=formal, env=env, text=True,
                                  capture_output=True, timeout=120)
            records.append({"argv": argv, "exit_code": proc.returncode,
                            "stdout": proc.stdout, "stderr": proc.stderr})
        else:
            proc = None
    final = records[-1]
    stdout = "\n".join(str(r["stdout"]) for r in records)
    stderr = "\n".join(str(r["stderr"]) for r in records)
    execution = {
        "argv": final["argv"], "dependency_argv": [r["argv"] for r in records[:-1]],
        "cwd": str(formal), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "mathlib_commit": commit, "lean_toolchain": toolchain, "LEAN_PATH": paths,
        "exit_code": final["exit_code"], "stdout": stdout, "stderr": stderr,
        "elapsed_seconds": time.monotonic() - started,
        "axiom_check": {"sorryAx_present": "sorryAx" in stdout or "sorryAx" in stderr,
                         "source_print_axioms_present": "#print axioms" in source.read_text()},
    }
    (out / "execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    shutil.copyfile(source, out / "source.lean")
    print(json.dumps({"exit_code": execution["exit_code"],
                      "source_sha256": execution["source_sha256"],
                      "elapsed_seconds": execution["elapsed_seconds"],
                      "output": str(out)}))
    return 0 if execution["exit_code"] == 0 and not execution["axiom_check"]["sorryAx_present"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
