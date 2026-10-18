"""Bind the actually observed L01 execution and the reviewable local package."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys


def identity(path):
    path = Path(path)
    b = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists(): raise FileExistsError(args.out)
    package = Path(__file__).resolve().parent
    programme = package.parents[1]
    repo = programme.parents[2]
    sys.path.insert(0, str(programme/"L01_R8_C8_TWO_MASK_STABILITY_20261017/src"))
    import l01_matched_split_stream as native_module
    import l01_smica_processed_bands
    import numpy, scipy, healpy, pytest
    native = json.loads(args.native.read_text())
    observed_sources = {}
    for name, expected in native["dependency_sha256"].items():
        item = identity(importlib.import_module(name).__file__)
        if item["sha256"] != expected: raise ValueError("EXECUTED_DEPENDENCY_DRIFT_"+name)
        observed_sources[name] = item
    driver = identity(native_module.__file__)
    if driver["sha256"] != native["code_sha256"]:
        raise ValueError("EXECUTED_DRIVER_SOURCE_DRIFT")
    files = [identity(p) for p in sorted(package.rglob("*")) if p.is_file()
             and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts
             and p.suffix in (".py", ".md", ".txt", ".json", ".npz", ".png", ".pdf")
             and p.resolve() != args.out.resolve()]
    git = lambda *cmd: subprocess.check_output(["git", "-C", str(repo), *cmd], text=True).strip()
    result = {"schema": "htt.L01_native_execution_receipt/1", "owner": "obsstat",
              "status": "EXECUTED_PENDING_INDEPENDENT_REVIEW", "claim_tier": "C0",
              "execution_base_head": "1e095a2749cce9b28e45aac043a82218c21f84e5",
              "execution_ref": "origin/research/htt-sixpaper-goals-robustness-20261018",
              "guard": "PASS_EXACT_HEAD_CLEAN_IMPORTS", "first_failure": "FIRST_FAILURE.txt",
              "actual_native_stream_runs": 1, "helper_invocations": 2,
              "parent_parallel_lane_head_at_receipt": git("rev-parse", "HEAD"),
              "branch_at_receipt": git("branch", "--show-current"),
              "runtime": {"python": sys.version, "executable": sys.executable,
                          "numpy": numpy.__version__, "scipy": scipy.__version__,
                          "healpy": healpy.__version__, "pytest": pytest.__version__,
                          "requested_model": "gpt-6.1-sol", "requested_effort": "high",
                          "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN"},
              "native_output": identity(args.native), "native_status": native["status"],
              "driver": driver, "executed_dependency_sources": observed_sources,
              "validation": {"existing_matched_stream_suite": {"distinct_tests": 39, "result": "PASS"},
                             "new_analysis_and_support_suites": {"distinct_tests": 20, "result": "PASS"},
                             "native_high_injections": 2, "native_low_injections": 1,
                             "original_support_L128_products": 5,
                             "whole_repository": "NOT_RUN", "plot_visual_inspection": "TWO_PNG_CHECKED"},
              "commands": "EXECUTION_LOG.txt and REPORT_KO.md; generators have --help",
              "node_acceptance": "AUTHOR_DOES_NOT_ADMIT_NODE; FRESH_INDEPENDENT_REVIEW_REQUIRED",
              "publication": "NO_CHILD_COMMIT_OR_PUSH", "paper_gate": "NOT_READY_TO_SUBMIT",
              "files_consumed_by_parent_and_independent_review": files}
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps({"out": str(args.out), "native_output": result["native_output"],
                      "local_review_files": len(files)}, indent=2))


if __name__ == "__main__": main()
