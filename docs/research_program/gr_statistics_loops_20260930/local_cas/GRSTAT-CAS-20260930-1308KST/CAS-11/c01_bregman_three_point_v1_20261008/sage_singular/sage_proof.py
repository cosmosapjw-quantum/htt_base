#!/usr/bin/env sage -python
"""Existing exact Sage proof, invoked by the standard-Python run.py wrapper.

Its polynomial checks and pinned Singular call retain the original axis work.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from sage.all import PolynomialRing, QQ
from sage.version import version as sage_version


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[7]
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUT = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED = {
    CONTRACT: "3e0adbd4b1a31163e58c13d48e1ebe703a6d7daa55cdb8d247f6c1a41bd4b16a",
    INPUT: "c65019a54a477d4d75738579741c33ace4e19db42142e0bde0c20b013cd79e55",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SINGULAR: "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_generic(n: int, k: int) -> dict[str, bool | int]:
    names = ["Hf", "Hg", "Hh"]
    for stem in ("f", "g", "h", "Gg", "Gh"):
        names += [f"{stem}{i}" for i in range(n)]
    names += [f"v{i}_{j}" for i in range(n) for j in range(k)]
    names += [f"l{j}" for j in range(k)]
    ring = PolynomialRing(QQ, names=names)
    vals = dict(zip(names, ring.gens()))
    Hf, Hg, Hh = (vals[s] for s in ("Hf", "Hg", "Hh"))
    f, g, h, Gg, Gh = ([vals[f"{s}{i}"] for i in range(n)] for s in ("f", "g", "h", "Gg", "Gh"))
    Dfg = Hf - Hg - sum(Gg[i] * (f[i] - g[i]) for i in range(n))
    Dfh = Hf - Hh - sum(Gh[i] * (f[i] - h[i]) for i in range(n))
    Dhg = Hh - Hg - sum(Gg[i] * (h[i] - g[i]) for i in range(n))
    target = sum((Gh[i] - Gg[i]) * (f[i] - h[i]) for i in range(n))
    identity_residual = Dfg - Dfh - Dhg - target
    V = [[vals[f"v{i}_{j}"] for j in range(k)] for i in range(n)]
    lambdas = [vals[f"l{j}"] for j in range(k)]
    substituted_cross = sum(
        sum(V[i][j] * lambdas[j] for j in range(k)) * (f[i] - h[i])
        for i in range(n)
    )
    moments = [sum(V[i][j] * (f[i] - h[i]) for i in range(n)) for j in range(k)]
    transpose_residual = substituted_cross - sum(lambdas[j] * moments[j] for j in range(k))
    ideal_remainder = ring.ideal(moments).reduce(substituted_cross)
    result = {
        "n": n,
        "k": k,
        "identity_residual_zero": identity_residual == 0,
        "transpose_residual_zero": transpose_residual == 0,
        "moment_ideal_remainder_zero": ideal_remainder == 0,
    }
    assert all(value is True for key, value in result.items() if key.endswith("_zero")), result
    return result


def main() -> int:
    for path, expected in EXPECTED.items():
        observed = sha256(path)
        assert observed == expected, f"SHA mismatch {path}: {observed} != {expected}"
    assert sage_version.startswith("10.9"), sage_version
    source = HERE / "bregman_c01.sing"
    version_cmd = [str(SINGULAR), "--version"]
    version_proc = subprocess.run(version_cmd, cwd=HERE, text=True, capture_output=True, timeout=60)
    (HERE / "singular.version.stdout.log").write_text(version_proc.stdout)
    (HERE / "singular.version.stderr.log").write_text(version_proc.stderr)
    assert version_proc.returncode == 0, "Singular version command failed"
    assert "version 4.4.1 (44100" in version_proc.stdout, "Singular version mismatch"
    singular_cmd = [str(SINGULAR), "-q", str(source)]
    env = os.environ.copy()
    env["PATH"] = str(SINGULAR.parent) + os.pathsep + env.get("PATH", "")
    proc = subprocess.run(singular_cmd, cwd=HERE, env=env, text=True, capture_output=True, timeout=300)
    (HERE / "singular.stdout.log").write_text(proc.stdout)
    (HERE / "singular.stderr.log").write_text(proc.stderr)
    assert proc.returncode == 0, "Singular execution failed"
    assert not proc.stderr.strip(), "Singular stderr is nonempty"
    assert "?" not in proc.stdout and "FAIL" not in proc.stdout, "Singular reported an engine or assertion error"
    required_markers = (
        "PASS identity_residual=0",
        "PASS transpose_residual=0 quotient_remainder=0",
        "PASS orientation=4/3,5/3 approximate_residual=1/10",
        "CAS-11-C01=true",
    )
    assert all(marker in proc.stdout for marker in required_markers), "Singular omitted a required certificate marker"
    exact_cases = [exact_generic(n, k) for n, k in ((1, 1), (2, 2), (3, 2), (4, 3))]
    f, g = QQ(2), QQ(1)
    H = lambda x: x**3 / 3
    G = lambda x: x**2
    forward = H(f) - H(g) - G(g) * (f - g)
    reverse = H(g) - H(f) - G(f) * (g - f)
    approximate_residual = QQ(1) / 10
    assert (forward, reverse, approximate_residual) == (QQ(4) / 3, QQ(5) / 3, QQ(1) / 10)
    details = {
        "sage_version": sage_version,
        "singular_version": "4.4.1/44100",
        "singular_binary": str(SINGULAR),
        "singular_binary_sha256": sha256(SINGULAR),
        "singular_version_argv": version_cmd,
        "singular_version_exit": version_proc.returncode,
        "singular_execution_argv": singular_cmd,
        "singular_execution_exit": proc.returncode,
        "input_sha256": {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): v for p, v in EXPECTED.items()},
        "sage_exact_cases": exact_cases,
        "singular_exact": True,
        "orientation_control": {"D_H(f||g)": "4/3", "D_H(g||f)": "5/3"},
        "approximate_matching_residual": "1/10",
    }
    (HERE / "execution_detail.json").write_text(json.dumps(details, indent=2, sort_keys=True) + "\n")
    payload = {"CAS-11-C01": True}
    (HERE / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
