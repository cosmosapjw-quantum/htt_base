"""No-argument CAS-13-C02 Sage/Singular runner; writes only this axis's artifacts."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[8]
HERE = Path(__file__).resolve().parent
CONTRACT = ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/c02_two_node_v1_20261008/EXECUTION_CONTRACT.json"
INPUT = CONTRACT.with_name("ADMITTED_INPUTS.json")
TEFF = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md"
COMMON = TEFF.with_name("COMMON_SPEC.md")
SAGE = Path("/usr/local/bin/sage")
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call(argv, prefix):
    try:
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=1800)
        out, err, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        err += "\nTIMEOUT after 1800 seconds\n"
        code = 124
    except Exception as exc:
        out, err, code = "", f"RUNNER_EXCEPTION: {type(exc).__name__}: {exc}\n", 125
    (HERE / f"{prefix}.stdout.log").write_text(out)
    (HERE / f"{prefix}.stderr.log").write_text(err)
    return {"argv": [str(a) for a in argv], "cwd": str(ROOT), "exit_code": code,
            "stdout_log": f"{prefix}.stdout.log", "stderr_log": f"{prefix}.stderr.log",
            "stdout": out, "stderr": err}


def main():
    expected = {
        CONTRACT: "66b839cb44573842f36f73c234c4b5b6c8cca639465c58e525b86be8aea754b0",
        INPUT: "83bb552d9cbc733c58bd57bef88a53ac060261b343b6e9596181586104a68725",
        TEFF: "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe",
        COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    }
    observed = {str(p.relative_to(ROOT)): sha(p) for p in expected}
    seals_ok = all(sha(p) == h for p, h in expected.items())
    versions = {}
    for name, argv in (("sage", [SAGE, "--version"]), ("singular", [SINGULAR, "--version"])):
        receipt = call(argv, name + ".version")
        versions[name] = {"argv": receipt["argv"], "exit_code": receipt["exit_code"],
                          "first_line": (receipt["stdout"] or receipt["stderr"]).splitlines()[:1]}
    version_ok = ("SageMath version 10.9" in versions["sage"]["first_line"][0]
                  and "version 4.4.1" in versions["singular"]["first_line"][0]
                  and versions["sage"]["exit_code"] == 0
                  and versions["singular"]["exit_code"] == 0)
    commands = []
    if seals_ok and version_ok:
        commands.append(call([SAGE, "-python", HERE / "check_two_node.sage.py"], "sage"))
        commands.append(call([SINGULAR, "-q", HERE / "check_two_node.sing"], "singular"))
    else:
        (HERE / "sage.stdout.log").write_text("")
        (HERE / "singular.stdout.log").write_text("")
        (HERE / "sage.stderr.log").write_text("INPUT_SEAL_OR_TOOL_VERSION_MISMATCH\n")
        (HERE / "singular.stderr.log").write_text("INPUT_SEAL_OR_TOOL_VERSION_MISMATCH\n")
    passed = (seals_ok and version_ok and len(commands) == 2
              and all(c["exit_code"] == 0 for c in commands)
              and "CAS-13-C02 Sage exact real algebra and algebraic-root vectors PASS" in commands[0]["stdout"]
              and "CAS-13-C02 Singular exact cleared identities PASS" in commands[1]["stdout"]
              and not any("error" in (c["stdout"] + c["stderr"]).lower() for c in commands))
    result = {
        "axis": "sage_singular", "status": "PASS" if passed else "INCONCLUSIVE",
        "claim_id": "CAS-13-C02", "contract_sha256": expected[CONTRACT],
        "source_input_hashes": observed, "input_seals_match": seals_ok,
        "checks": {"CAS-13-C02": passed}, "domain_assumption_diff": [], "counterexample": None,
        "evidence_class": "exact", "versions": versions,
        "commands": [{k: v for k, v in c.items() if k not in ("stdout", "stderr")} for c in commands],
        "executable_artifacts": {str(p): sha(p) for p in (Path(os.path.realpath(SAGE)), SINGULAR)},
        "source_artifacts": {p.name: sha(p) for p in (HERE / "run.py", HERE / "check_two_node.sage.py", HERE / "check_two_node.sing")},
        "raw_logs": ["sage.version.stdout.log", "sage.version.stderr.log", "singular.version.stdout.log",
                     "singular.version.stderr.log", "sage.stdout.log", "sage.stderr.log",
                     "singular.stdout.log", "singular.stderr.log",
                     "first_failure.singular.stdout.log", "first_failure.axis_result.json"],
        "first_failure": {"status": "INCONCLUSIVE", "exit_code": 1,
                          "cause": "Singular parser error at derivative factor syntax",
                          "receipt": "first_failure.axis_result.json",
                          "raw_stdout": "first_failure.singular.stdout.log"},
        "launch_id": None, "lifecycle": "BLOCKED",
        "scope": "strict S121 interior and separate limit measures; two-node feasibility only",
        "excluded": ["general-p extremality", "C03", "C04", "bandpass", "scientific admission"],
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    (HERE / "axis_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": {"CAS-13-C02": passed}, "domain_assumption_diff": [], "counterexample": None}, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
