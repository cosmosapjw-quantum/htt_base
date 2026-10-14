#!/usr/bin/env python3
"""Prepare fresh observation-analysis runs from the current R1/R2 ports.

This checks inputs/runtime and emits commands and a readable readiness report.
It does not fit observations or infer scientific eligibility from file existence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PLAN = "docs/observational_analysis_20261014/ANALYSIS_PLAN.json"


def probe_runtime(executable: str, modules: list[str], root: Path) -> dict:
    code = """import importlib,json,platform,sys
out={'executable':sys.executable,'version':platform.python_version(),'modules':{}}
for name in json.loads(sys.argv[1]):
 try:
  mod=importlib.import_module(name)
  out['modules'][name]={'available':True,'version':getattr(mod,'__version__',None)}
 except Exception as exc:
  status='PACKAGE_MISSING' if isinstance(exc,ModuleNotFoundError) else 'EXECUTION_FAILED'
  out['modules'][name]={'available':False,'status':status,'error':type(exc).__name__+': '+str(exc)}
print(json.dumps(out))
"""
    try:
        run = subprocess.run([executable, "-B", "-c", code, json.dumps(modules)],
                             cwd=root, text=True, capture_output=True, timeout=30)
        if run.returncode != 0:
            return {"available": False, "status": "EXECUTION_FAILED", "executable": executable,
                    "exit_code": run.returncode, "error": run.stderr[-2000:]}
        value = json.loads(run.stdout)
        value["available"] = all(v["available"] for v in value["modules"].values())
        failures = [v.get("status") for v in value["modules"].values() if not v["available"]]
        value["status"] = ("PYTHON_PASS" if value["available"] else
                           "EXECUTION_FAILED" if "EXECUTION_FAILED" in failures else "PACKAGE_MISSING")
        return value
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return {"available": False, "status": "EXECUTION_FAILED", "executable": executable,
                "error": type(exc).__name__ + ": " + str(exc)}


def inspect_input(root: Path, relative: str) -> dict:
    path = root / relative
    try:
        info = path.stat()
        return {"path": relative, "resolved_path": str(path.resolve()),
                "exists": path.is_file(), "bytes": info.st_size,
                "identity_level": "PATH_SIZE_ONLY; owning reader validates content"}
    except OSError as exc:
        return {"path": relative, "exists": False, "error": str(exc)}


def build_preparation(root: Path, plan: dict, runtimes: dict, output: Path) -> dict:
    products = []
    for product in plan["products"]:
        inputs = [inspect_input(root, p) for p in product["inputs"]]
        runner = root / product["entrypoint"]
        runtime = runtimes[product["runtime"]]
        runnable = all(p["exists"] for p in inputs) and runner.is_file() and runtime["available"]
        tokens = [runtime["executable"], "-B", product["entrypoint"]]
        for token in product["arguments"]:
            tokens.append(token.replace("{RUN_ROOT}", str(output / "runs")))
        products.append({"id": product["id"], "scope": product["scope"],
                         "auto_run": product.get("auto_run", True),
                         "inputs": inputs, "runner_exists": runner.is_file(),
                         "runtime": product["runtime"], "runnable_input_check": runnable,
                         "scientific_fit_status": product["scientific_fit_status"],
                         "next_physical_inputs": product["next_physical_inputs"],
                         "command": shlex.join(tokens),
                         "command_scope": "Must validate input contents in owning reader; does not promote a scientific claim"})
    def git(*args):
        run = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
        return run.stdout.strip() if run.returncode == 0 else None
    return {"schema": "htt.observational-preparation/1", "owner": "htt",
            "scope": "Current inputs/runtime and executable continuation, not a data fit",
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_root": str(root), "head": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"), "runtimes": runtimes,
            "products": products, "continuation_tasks": plan["tasks"],
            "assumption": "File presence/runtime availability is not an observation-law validation",
            "historical_state": "Existing proof and campaign verdicts are unchanged"}


def render_report(result: dict) -> str:
    lines = ["# 관측 분석 실행 준비", "", f"기준 HEAD: `{result['head']}`", "",
             "입력 접근과 실행 환경을 확인한 결과다. 관측법칙·공분산의 타당성 판정은 각 분석의 별도 결과를 따른다.", "",
             "| 경로 | 입력·환경 | 현재 가능한 산출물 | 실제 적합 상태 |", "|---|---|---|---|"]
    for row in result["products"]:
        state = "실행 입력 준비됨" if row["runnable_input_check"] else "입력 또는 환경 보완 필요"
        lines.append(f"| {row['id']} | {state} | {row['scope']} | {row['scientific_fit_status']} |")
    for row in result["products"]:
        lines += ["", "## " + row["id"], "", "```bash", row["command"], "```", ""]
        if not row["auto_run"]:
            lines.append("- 기존 검증 결과 재사용이 기본이다. 위 명령은 해당 입력이나 코드가 바뀐 경우에만 실행한다.")
        lines += ["- " + x for x in row["next_physical_inputs"]]
        for inp in row["inputs"]:
            if not inp["exists"]:
                lines.append("- 접근 실패: `" + inp["path"] + "`")
    lines += ["", "전체 후속 작업은 ANALYSIS_PLAN.json과 CODEX_HANDOFF_KO.md를 따른다. 기존 검증 로그를 덮어쓰지 않는다.", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--desi-python", default="/home/cosmosapjw/venv/bin/python")
    parser.add_argument("--cmb-python", default="/usr/bin/python")
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    output = args.output_dir.resolve()
    if output.exists():
        parser.error("output directory exists; choose a fresh run directory")
    plan = json.loads((args.plan or root / PLAN).read_text())
    paths = {"desi_cf4": args.desi_python, "cmb": args.cmb_python}
    runtimes = {key: probe_runtime(paths[key], modules, root)
                for key, modules in plan["runtime_modules"].items()}
    result = build_preparation(root, plan, runtimes, output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "runs").mkdir()
    (output / "readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (output / "PREPARATION_REPORT.md").write_text(render_report(result))
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", "cd " + shlex.quote(str(root)),
             "export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1",
             "export PYTHONPATH=htt:htt/htt:htt/src", "",
             "# Only currently runnable entrypoints are active; physical inference is not auto-promoted."]
    for row in result["products"]:
        lines += ["", "# " + row["id"] + ": " + row["scope"],
                  (row["command"] if row["auto_run"] else "# REUSE_EXISTING_RESULT: " + row["command"])
                  if row["runnable_input_check"] else "# INPUT_OR_RUNTIME_MISSING: " + row["command"]]
    (output / "run_ready_diagnostics.sh").write_text("\n".join(lines) + "\n")
    print(json.dumps({"output": str(output), "runnable": [r["id"] for r in result["products"] if r["runnable_input_check"]],
                      "status": "PREPARATION_RECORDED_NOT_SCIENCE_ADMISSION"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
