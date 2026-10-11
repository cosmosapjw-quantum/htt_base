"""Stdlib entrypoint for the frozen CAS-07 M03 Sage/Singular axis.

The aggregate runner invokes ordinary Python. This wrapper launches the actual
Sage interpreter for sage_check.py and the pinned Singular executable for
kernel.sing, preserving their raw output before emitting one JSON document.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
CONTRACT = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/volterra_scalar_majorant_v1_20261007/EXECUTION_CONTRACT.json"
INPUTS = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/volterra_scalar_majorant_v1_20261007/ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED = {
    str(CONTRACT): "6c840eaffac0744da3d1b2f9c7de3f8b1c45af2d949ba4831b5e90d4ec9a51ae",
    str(INPUTS): "bbb0f93dc43ddd3ee96cdee065f8173ccac44007a6908ae66714f25e3214661d",
    str(COMMON): "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    str(SINGULAR): "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_capture(argv, stem, timeout=120):
    proc = subprocess.run(argv, cwd=HERE, capture_output=True, text=True, timeout=timeout)
    evidence = HERE / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / f"{stem}.stdout").write_text(proc.stdout)
    (evidence / f"{stem}.stderr").write_text(proc.stderr)
    return proc


def result_base():
    return {
        "axis": "sage_singular",
        "contract_id": "GRSTAT-20260930-CAS-07-M03-SCALAR-VOLTERRA-V1",
        "checks": {"CAS-07-M03-SCALAR-VOLTERRA": False},
        "domain_assumption_diff": [],
        "counterexample": None,
        "evidence_class": "exact",
        "global_launch_id": None,
        "global_authority": "UNAVAILABLE_OWNER_AUTHORIZED_DIRECT_LOCAL_EXCEPTION",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "scientific_admission": "HOLD",
        "result_scope": "universal scalar functional comparison only",
        "proof_file": "proof.md",
    }


def main():
    out = result_base()
    observed = {path: sha(path) for path in EXPECTED}
    out.update({
        "contract_sha256": observed[str(CONTRACT)],
        "admitted_inputs_sha256": observed[str(INPUTS)],
        "hashes": {"expected": EXPECTED, "observed": observed},
    })
    if observed != EXPECTED:
        raise RuntimeError("frozen contract/input/toolchain hash mismatch")

    sage_path = shutil.which("sage")
    if not sage_path:
        raise RuntimeError("Sage executable unavailable")
    sage = run_capture([sage_path, "-python", str(HERE / "sage_check.py")], "sage", timeout=120)
    singular_version = run_capture([str(SINGULAR), "--version"], "singular_version", timeout=30)
    singular = run_capture([str(SINGULAR), "-q", str(HERE / "kernel.sing")], "singular", timeout=120)

    sage_data = None
    try:
        sage_data = json.loads(sage.stdout)
    except json.JSONDecodeError:
        pass
    sage_ok = (sage.returncode == 0 and not sage.stderr.strip()
               and isinstance(sage_data, dict) and sage_data.get("ok") is True
               and str(sage_data.get("sage_version", "")).startswith("10.9"))
    version_ok = (singular_version.returncode == 0 and not singular_version.stderr.strip()
                  and "version 4.4.1 (44100" in singular_version.stdout)
    expected_lines = ([f"PASS kernel n={n}" for n in range(1, 9)]
                      + [f"PASS seed n={n}" for n in range(9)]
                      + ["ALL_POLYNOMIAL_IDENTITIES_PASS"])
    singular_ok = (singular.returncode == 0 and not singular.stderr.strip()
                   and singular.stdout.splitlines() == expected_lines)
    ok = bool(sage_ok and version_ok and singular_ok)
    out.update({
        "checks": {"CAS-07-M03-SCALAR-VOLTERRA": ok},
        "tool_versions": {"sage": sage_data.get("sage_version") if sage_ok else "UNKNOWN",
                          "singular": "4.4.1/44100" if version_ok else "UNKNOWN"},
        "executables": {"entry_python": sys.executable, "sage_launcher": sage_path,
                        "sage_python": sage_data.get("python_executable") if sage_ok else "UNKNOWN",
                        "singular": str(SINGULAR), "singular_sha256": observed[str(SINGULAR)]},
        "source_files": ["run.py", "sage_check.py", "kernel.sing", "proof.md"],
        "source_sha256": {name: sha(HERE / name) for name in
                          ("run.py", "sage_check.py", "kernel.sing", "proof.md")},
        "raw_execution": {"sage_exit_code": sage.returncode,
                          "singular_exit_code": singular.returncode,
                          "singular_version_exit_code": singular_version.returncode,
                          "sage_stdout": "evidence/sage.stdout", "sage_stderr": "evidence/sage.stderr",
                          "singular_stdout": "evidence/singular.stdout", "singular_stderr": "evidence/singular.stderr",
                          "singular_version_stdout": "evidence/singular_version.stdout",
                          "singular_version_stderr": "evidence/singular_version.stderr"},
        "raw_sha256": {name: sha(HERE / "evidence" / name) for name in
                       ("sage.stdout", "sage.stderr", "singular.stdout", "singular.stderr",
                        "singular_version.stdout", "singular_version.stderr")},
        "sage_exact_checks": sage_data if sage_ok else None,
    })
    print(json.dumps(out, sort_keys=True, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        failure = result_base()
        failure["error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(failure, sort_keys=True, indent=2))
        raise SystemExit(1)
