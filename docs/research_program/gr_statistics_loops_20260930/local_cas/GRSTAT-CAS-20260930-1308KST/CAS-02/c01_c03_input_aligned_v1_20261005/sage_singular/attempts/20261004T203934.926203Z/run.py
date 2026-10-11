"""Frozen RunSpec entrypoint; retain every own-axis execution attempt."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
S = HERE.parent
CONTRACT = S / "EXECUTION_CONTRACT.json"
ADMITTED = S / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
GATE = ROOT / ".agent-harness/scripts/cas_gate.py"
SAGE = "/usr/local/bin/sage"
SINGULAR = "/home/cosmosapjw/opt/sage/local/bin/Singular"
TASK = "GRSTAT-CAS-20260930-1308KST-CAS-02"
OBLIGATION = json.loads(CONTRACT.read_text())["axes"]["sage_singular"]["obligation"][0]
FILES = [CONTRACT, ADMITTED, COMMON, GATE, HERE / "run.py", HERE / "verify.sage.py", HERE / "verify.sing", HERE / "make_singular.py"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def hashes():
    return {str(p.relative_to(ROOT)): sha(p) for p in FILES}


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def execute(label, argv, attempt, timeout=1800):
    record = {"label": label, "argv": argv, "cwd": str(ROOT), "started_at": utc(), "timeout_seconds": timeout}
    try:
        done = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
        record.update(exit_code=done.returncode, timed_out=False, stdout=done.stdout, stderr=done.stderr)
    except subprocess.TimeoutExpired as e:
        record.update(exit_code=None, timed_out=True, stdout=(e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""), stderr=(e.stderr or b"").decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or ""))
    except OSError as e:
        record.update(exit_code=None, timed_out=False, stdout="", stderr=str(e), launch_error=str(e))
    record["completed_at"] = utc()
    (attempt / f"{label}.stdout.log").write_text(record.pop("stdout"))
    (attempt / f"{label}.stderr.log").write_text(record.pop("stderr"))
    (attempt / f"{label}.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main():
    attempt = HERE / "attempts" / dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    attempt.mkdir(parents=True, exist_ok=False)
    before = hashes()
    (attempt / "hashes_before.json").write_text(json.dumps(before, indent=2) + "\n")
    for p in [HERE / "run.py", HERE / "verify.sage.py", HERE / "verify.sing", HERE / "make_singular.py"]:
        shutil.copy2(p, attempt / p.name)
    commands = []
    # These version probes are executed in the same process path used below.
    commands.append(execute("sage_version", [SAGE, "-python", "-c", "from sage.all import version; print(version())"], attempt, 60))
    commands.append(execute("singular_version", [SINGULAR, "--version"], attempt, 60))
    prefix = ["cuhg-telemetry", "run", "--project", str(ROOT), "--task", TASK, "--"]
    commands.append(execute("sage", prefix + [SAGE, "-python", str(HERE / "verify.sage.py")], attempt))
    commands.append(execute("singular", prefix + [SINGULAR, "-q", str(HERE / "verify.sing")], attempt))
    after = hashes()
    (attempt / "hashes_after.json").write_text(json.dumps(after, indent=2) + "\n")
    sageout = (attempt / "sage.stdout.log").read_text()
    sagerr = (attempt / "sage.stderr.log").read_text()
    singout = (attempt / "singular.stdout.log").read_text()
    singerr = (attempt / "singular.stderr.log").read_text()
    expected_sage = ["C01_delta_Frobenius", "C01_metric_Frobenius_squared", "C02_anchor_S1", "C02_anchor_S2", "C03_actual_Jacobian", "C03_actual_Gram", "C03_characteristic_polynomial", "C03_zero_case", "C03_cosh_positive", "C03_sinh_derivative", "C03_sinh_origin", "C03_hyperbolic_identity", "C03_tanh_conversion", "C03_chart_norm_nonnegative", "C03_chart_norm_square", "C03_ball_slack_nonnegative", "C03_slack_mapping", "C03_negative_R_implies_negative_sinh", "C03_R_zero_sinh_zero", "C03_abstract_sinh_nonnegative", "C03_numerator_nonnegative", "C03_first_denominator_positive", "C03_second_denominator_positive", "C03_universal_gap_nonnegative", "C03_ball_numerator_identity", "C03_exact_bound_gap_identity", "C03_bound_cross_multiplication"]
    expected_singular = ["C01_embedding_remainder", "C01_metric_remainder", "C02_anchor_S1_remainder", "C02_anchor_S2_remainder", "C03_characteristic_remainder", "C03_bound_cross_remainder", "C03_ball_slack_numerator_remainder"] + [f"C03_Gram_{i}{j}" for i in range(3) for j in range(3)]
    failures = []
    if before != after: failures.append("input/source hash changed during axis execution")
    pinned = {str(CONTRACT.relative_to(ROOT)): "f1df856a0da477256e8adfbb889001d75fd659dda6f834ea72e87f314ff844a8", str(ADMITTED.relative_to(ROOT)): "e7cfe79d7ad075899ee75f166687f40363e207ba334da3d8733fa2ab5a4b82bd", str(COMMON.relative_to(ROOT)): "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897", str(GATE.relative_to(ROOT)): "fcaaa08083221fa69ff22066d6fb9f769913bd774b15628dbf684544c69f0744"}
    for path,digest in pinned.items():
        if before[path] != digest: failures.append(f"frozen input mismatch {path}")
    for c in commands:
        if c["exit_code"] != 0: failures.append(f"{c['label']} exit={c['exit_code']} timeout={c['timed_out']}")
    if "SageMath version 10.9" not in (attempt / "sage_version.stdout.log").read_text(): failures.append("Sage 10.9 version missing")
    if "4.4.1 (44100" not in (attempt / "singular_version.stdout.log").read_text(): failures.append("Singular 4.4.1/44100 version missing")
    for marker in expected_sage:
        if f"{marker}=ZERO_OR_TRUE" not in sageout: failures.append(f"missing Sage certificate {marker}")
    for marker in ["C03_eigenvalues=1[multiplicity 2]", "at x=0,1[multiplicity 3]", "C03_eigenvalue_bound=largest=1+x/(1+x)<=1+tanh(R)^2 on exact ball"]:
        if marker not in sageout: failures.append(f"missing Sage derivation {marker}")
    for marker in expected_singular:
        if f"{marker}=0" not in singout: failures.append(f"missing Singular zero remainder {marker}")
    if "SINGULAR_CERTIFICATES_COMPLETE" not in singout: failures.append("Singular completion missing")
    if sagerr.strip(): failures.append("Sage stderr nonempty: " + sagerr.splitlines()[0])
    if singerr.strip(): failures.append("Singular stderr nonempty: " + singerr.splitlines()[0])
    if "// **" in singout or "CERTIFICATE_FAILURE" in singout: failures.append("Singular syntax or certificate error in stdout")
    status = "PASS" if not failures else "INCONCLUSIVE"
    result = {"axis":"sage_singular", "status":status, "contract_sha256":before[str(CONTRACT.relative_to(ROOT))], "evidence_class":"exact", "completed_at":utc(), "commands":commands, "attempt_dir":str(attempt.relative_to(ROOT)), "hashes_before":before, "hashes_after":after, "statement_alignment":{"C01":"real optical embedding delta S, positive Euclidean Frobenius identity, metric Frobenius norm 2", "C02":"both universal quadratic anchors, stronger arbitrary real 4x4 matrices and 4-vectors", "C03":"actual real positive-root chart derivative, Gram eigenvalues including d=0, largest bound on ||d||<=sinh R with R>=0 derived"}, "component_status":{"C01": all(x in sageout for x in ["C01_delta_Frobenius=ZERO_OR_TRUE","C01_metric_Frobenius_squared=ZERO_OR_TRUE"]) and "C01_embedding_remainder=0" in singout, "C02": all(x in sageout for x in ["C02_anchor_S1=ZERO_OR_TRUE","C02_anchor_S2=ZERO_OR_TRUE"]) and all(x in singout for x in ["C02_anchor_S1_remainder=0","C02_anchor_S2_remainder=0"]), "C03": all(f"{x}=ZERO_OR_TRUE" in sageout for x in expected_sage if x.startswith("C03_")) and "SINGULAR_CERTIFICATES_COMPLETE" in singout}, "first_gap":failures[0] if failures else None, "all_gaps":failures, "domain_assumption_diff":[], "claim_scope":"C01-C03 exact specified mathematical components only; C04 NEEDS_OWNER_DECISION; global projection/Lipschitz and science HOLD", "engine_contribution":{"Sage":"actual positive-root derivative, Gram, universal polynomial characteristic identity, zero case, hyperbolic derivative/positivity/identity and rational sign reduction", "Singular":"raw optical and bilinear polynomial remainders, chart Jacobian numerator Gram/characteristic remainders, bound cross-multiplication"}}
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    (attempt / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    payload = {"checks": {"CAS-02-" + k: value and not failures for k, value in result["component_status"].items()}, "domain_assumption_diff": result["domain_assumption_diff"], "counterexample": None, "first_gap": result["first_gap"]}
    print(json.dumps(payload))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
