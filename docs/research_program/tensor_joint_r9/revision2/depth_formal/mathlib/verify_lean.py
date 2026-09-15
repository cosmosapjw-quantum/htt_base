#!/usr/bin/env python3
"""Compile new R9 Lean sources against the existing pinned mathlib cache.

MLflow traces the actual compiler operation; raw evidence remains independently
readable in the output directory. Tracing and exit success are not admission.
Requires the isolated execution environment's mlflow-skinny==3.16.0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[6]
MATHLIB_COMMIT = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=["Recursion", "Covariance"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trace-store", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path(
        "/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0"))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    mathlib = args.cache / "packages/mathlib"
    pinned = (ROOT / "formal/lean-toolchain").read_text().strip()
    if (mathlib / "lean-toolchain").read_text().strip() != pinned:
        raise RuntimeError("Mathlib and repo Lean toolchain differ")
    commit = subprocess.check_output(
        ["git", "-C", str(mathlib), "rev-parse", "HEAD"], text=True).strip()
    if commit != MATHLIB_COMMIT:
        raise RuntimeError("Shared mathlib source differs from the inspected pin")
    paths = sorted(str(p.resolve()) for p in args.cache.glob(
        "packages/*/.lake/build/lib/lean"))
    source = ROOT / "formal/R9Depth" / f"{args.source}.lean"
    argv = ["lake", "env", "lean", f"R9Depth/{args.source}.lean"]
    env = dict(os.environ, LEAN_PATH=os.pathsep.join(paths))
    # Use a local, task-scoped trace store, with no server or external export.
    os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
    os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
    import mlflow

    mlflow.set_tracking_uri(args.trace_store.resolve().as_uri())
    experiment = mlflow.set_experiment("R9-DEPTH-MATHLIB-20260914")
    inputs = {"argv": argv, "cwd": str(ROOT / "formal"),
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "mathlib_commit": commit, "lean_toolchain": pinned, "LEAN_PATH": paths}
    with mlflow.start_span(name="r9_depth_validation", span_type="CHAIN") as outer:
        outer.set_inputs(inputs)
        with mlflow.start_span(name="lean_compile", span_type="TOOL") as inner:
            inner.set_inputs(inputs)
            started = time.monotonic()
            try:
                result = subprocess.run(argv, cwd=ROOT / "formal", env=env,
                                        text=True, capture_output=True, timeout=120)
                execution = {**inputs, "exit_code": result.returncode,
                             "stdout": result.stdout, "stderr": result.stderr,
                             "elapsed_seconds": time.monotonic() - started}
            except subprocess.TimeoutExpired as exc:
                execution = {**inputs, "exit_code": None, "timed_out": True,
                             "stdout": str(exc.stdout), "stderr": str(exc.stderr),
                             "elapsed_seconds": time.monotonic() - started}
            inner.set_outputs(execution)
            if execution["exit_code"] != 0:
                inner.set_status("ERROR")
        outer.set_outputs(execution)
        if execution["exit_code"] != 0:
            outer.set_status("ERROR")
        trace_id = outer.trace_id
    (output / "execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    (output / "source.lean").write_bytes(source.read_bytes())
    mlflow.flush_trace_async_logging()
    traces = mlflow.search_traces(locations=[experiment.experiment_id])
    trace = mlflow.get_trace(trace_id)
    assert trace is not None and len(trace.data.spans) == 2
    assert trace_id in set(traces["trace_id"])
    (output / "trace.json").write_text(json.dumps(trace.to_dict(), indent=2) + "\n")
    (output / "tracing.json").write_text(json.dumps({
        "mlflow_version": mlflow.__version__, "trace_id": trace_id,
        "experiment_id": experiment.experiment_id, "verified_traces": 1,
        "verified_spans": 2, "status": "PASS_OBSERVABILITY_ONLY"}, indent=2) + "\n")
    print(json.dumps({"exit_code": execution["exit_code"], "trace_id": trace_id,
                      "verified_spans": 2, "output": str(output)}))
    return 0 if execution["exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
