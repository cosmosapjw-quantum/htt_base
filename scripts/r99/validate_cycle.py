"""Reproduce the bounded R99 verification without rerunning large source products."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/research_program/observational_publication_20261015"
OUT = BASE / "R99_FIFTH_BLOCKER_RESOLUTION_20261123"
PY = str(ROOT / ".venv/bin/python")
TESTS = [
    "tests/obsstat/test_r99_cf4_source_law.py",
    "tests/obsstat/test_r99_optical.py",
    "tests/obsstat/test_r99_gaia_shared_field.py",
    "tests/obsstat/test_r99_acquisition.py",
    "tests/obsstat/test_r99_program_preparation.py",
]
PRODUCERS = [
    "scripts/r99/cf4_source_law.py",
    "scripts/r99/optical.py",
    "htt/bass/transport/finite_redshift_optics.py",
    "scripts/r99/gaia_shared_field.py",
    "scripts/r99/acquisition.py",
    "scripts/r99/program_preparation.py",
    "scripts/r99/validate_cycle.py",
]
RESULTS = [
    "CF4_RESULTS.json", "OPTICAL_RESULTS.json",
    "GAIA_SHARED_FIELD_RESULTS.json", "GAIA_SHARED_FIELD_COVARIANCES.npz",
    "ACQUISITION_PLAN.json", "ACQUISITION_RESULTS.json",
    "inputs/lotss_outer_exposure_nside16.npz",
    "NODE60_EXECUTION_PREPARATION.json", "BLOCKER_ACTIONS.md",
]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=".:htt",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
    commands = [
        ("targeted_pytest", [PY,"-B","-m","pytest","-q","-p","no:cacheprovider",*TESTS], 0, 120),
        ("strict_science_authority", [PY,"-B",str(BASE/"R78_UNIFIED_SCIENCE_DAG_20261119/validate_unified.py"),
                                      "--strict-authority"], 0, 30),
        ("current_preparation_identity", [PY,"-B","-m","scripts.r99.program_preparation","--check"], 0, 30),
        ("expected_science_block", [PY,"-B","-m","scripts.r99.program_preparation","science",
                                    "--node","SQ-CF4"], 3, 30),
        ("bounded_acquisition_plan", [PY,"-B","-m","scripts.r99.acquisition","plan",
                                     "--ids","sdss_pv_v1_1","sixdf_pv_table1",
                                     "--max-bytes","22000000"], 0, 30),
    ]
    sources = {p:sha(ROOT/p) for p in PRODUCERS + TESTS}
    artifacts = {p:sha(OUT/p) for p in RESULTS}
    dag = BASE/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
    receipt = {
        "schema":"htt.r99.bounded_validation/1",
        "started_at_utc":datetime.now(timezone.utc).isoformat(),
        "checkout":str(ROOT),
        "head_before_verification":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "scope":"Current R99 numerical and integration tests; DAG/source identity. No full historical regression or new science promotion.",
        "code_and_tests_sha256":sources,
        "result_artifact_sha256":artifacts,
        "science_authority_sha256":sha(dag),
        "environment":{"python":sys.version.split()[0],
                       **{x:version(x) for x in ("numpy","scipy","healpy")},
                       "threads":{x:env[x] for x in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS",
                                                   "MKL_NUM_THREADS","NUMEXPR_NUM_THREADS")}},
        "runs":[],
    }
    for name, argv, expected, budget in commands:
        start = time.perf_counter()
        try:
            result = subprocess.run(argv,cwd=ROOT,env=env,text=True,capture_output=True,timeout=budget)
            stdout, stderr, code = result.stdout,result.stderr,result.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout,bytes): stdout=stdout.decode(errors="replace")
            if isinstance(stderr,bytes): stderr=stderr.decode(errors="replace")
            code, timed_out = None, True
        log = OUT/f"validation_{name}.log"
        log.write_text(stdout + ("\nSTDERR:\n"+stderr if stderr else ""))
        run = dict(label=name,argv=argv,expected_exit_code=expected,exit_code=code,
                   timeout_seconds=budget,timed_out=timed_out,
                   elapsed_seconds=time.perf_counter()-start,log=log.name,
                   log_sha256=sha(log),matched_expected_exit=(code==expected and not timed_out))
        if name=="targeted_pytest":
            match = re.search(r"(\d+) passed",stdout)
            run["reported_passed_tests"] = int(match.group(1)) if match else None
        if name in ("strict_science_authority","current_preparation_identity",
                    "expected_science_block","bounded_acquisition_plan") and code==expected:
            try:
                run["summary"] = json.loads(stdout)
            except json.JSONDecodeError:
                run["summary_parse_error"] = True
                run["matched_expected_exit"] = False
        receipt["runs"].append(run)
        print(name, "exit",code,"expected",expected,flush=True)
    receipt["sources_unchanged_during_verification"] = all(sha(ROOT/p)==s for p,s in sources.items())
    receipt["result_artifacts_unchanged_during_verification"] = all(sha(OUT/p)==s for p,s in artifacts.items())
    receipt["bounded_verification_pass"] = (
        all(r["matched_expected_exit"] for r in receipt["runs"])
        and receipt["sources_unchanged_during_verification"]
        and receipt["result_artifacts_unchanged_during_verification"])
    receipt["new_science_nodes_promoted"] = 0
    receipt["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (OUT/"VALIDATION.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"bounded_verification_pass":receipt["bounded_verification_pass"],
                      "unit_tests":receipt["runs"][0].get("reported_passed_tests"),
                      "source_and_result_identity":receipt["sources_unchanged_during_verification"]
                        and receipt["result_artifacts_unchanged_during_verification"]}))
    return 0 if receipt["bounded_verification_pass"] else 1

if __name__=="__main__":
    sys.exit(main())
