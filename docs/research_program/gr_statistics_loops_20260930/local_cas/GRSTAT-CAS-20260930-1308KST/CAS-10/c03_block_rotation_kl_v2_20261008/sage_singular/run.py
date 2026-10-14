"""Execute the frozen CAS-10-C03 v2 Sage/Singular axis and write its result."""

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUT = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED = {
    CONTRACT: "d64d348c940ea7b37c522fb1043eaa29a6558798104d953fe554b3844ca9811e",
    INPUT: "d538b90a28b749702209c68e0c73444607295e4b66f2c55d1640d9bd75cf5e53",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SINGULAR: "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in EXPECTED.items():
    actual = digest(path)
    if actual != expected:
        raise RuntimeError(f"frozen input/tool identity mismatch: {path}: {actual}")

contract = json.loads(CONTRACT.read_text())
assert contract["identity"]["contract_id"] == "GRSTAT-20260930-CAS-10-C03-BLOCK-ROTATION-KL-V2"
assert contract["independence"]["mode"] == "blind-results-and-derivations"


def execute(name, argv, *, timeout=1800):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout, check=False)
    stdout = HERE / f"{name}.stdout.log"
    stderr = HERE / f"{name}.stderr.log"
    stdout.write_bytes(result.stdout)
    stderr.write_bytes(result.stderr)
    return {
        "name": name,
        "argv": argv,
        "cwd": str(ROOT),
        "exit_code": result.returncode,
        "stdout_path": str(stdout.relative_to(ROOT)),
        "stdout_sha256": digest(stdout),
        "stderr_path": str(stderr.relative_to(ROOT)),
        "stderr_sha256": digest(stderr),
    }


commands = [
    execute("sage_version", ["sage", "--version"], timeout=30),
    execute("singular_version", [str(SINGULAR), "--version"], timeout=30),
    execute("sage", ["sage", "-python", str(HERE / "verify.sage.py")]),
    execute("singular", [str(SINGULAR), "-q", str(HERE / "verify.sing")]),
]
logs = {name: (HERE / f"{name}.stdout.log").read_text() for name in ("sage", "singular")}
stderrs = {name: (HERE / f"{name}.stderr.log").read_text() for name in ("sage", "singular")}
singular_diagnostics = re.findall(r"(?im)^\s*(?://\s*\*\*|\?|error\b|\*\*\s*error)", logs["singular"] + stderrs["singular"])
required_sage = (
    "R_ORTHOGONAL=true DET_R=1",
    "DIRECT_SUM_ORDER=Z0,Z1,m,p,T DIRECT_SUM_ORTHOGONAL=true UNCHANGED_IDENTITY=true DET_B=1",
    *(f"BLOCK_NORM_{i}=equal" for i in range(1, 6)),
    "COVARIANCE_INVERSE=true",
    "CONTROL_H0_KL=0 CONTROL_H1_SP1_KL=225/64",
    "SAGE_EXACT_PASS=true",
)
required_singular = (*required_sage[:-1], "SINGULAR_EXACT_PASS=true", "ROTATED_MEAN=true")
exact_pass = all(c["exit_code"] == 0 for c in commands)
exact_pass &= not any(stderrs.values()) and not singular_diagnostics
exact_pass &= all(marker in logs["sage"] for marker in required_sage)
exact_pass &= all(marker in logs["singular"] for marker in required_singular)
exact_pass &= "SageMath version 10.9" in (HERE / "sage_version.stdout.log").read_text()
exact_pass &= "version 4.4.1 (44100" in (HERE / "singular_version.stdout.log").read_text()

payload = {
    "checks": {"CAS-10-C03": bool(exact_pass)},
    "domain_assumption_diff": [],
    "counterexample": None,
}
payload_text = json.dumps(payload, separators=(",", ":"))
source_paths = [HERE / "run.py", HERE / "verify.sage.py", HERE / "verify.sing"]
axis_result = {
    "axis": "sage_singular",
    "status": "PASS" if exact_pass else "FAIL",
    "contract_id": contract["identity"]["contract_id"],
    "contract_sha256": EXPECTED[CONTRACT],
    "input_sha256": EXPECTED[INPUT],
    "common_spec_sha256": EXPECTED[COMMON],
    "evidence_class": "exact",
    "exact_obligation_results": payload["checks"],
    "component_results": payload["checks"],
    "domain_assumption_diff": [],
    "counterexample": None,
    "commands": commands,
    "versions": {
        "sage": "10.9",
        "singular": "4.4.1 (44100)",
        "singular_binary_path": str(SINGULAR),
        "singular_binary_sha256": EXPECTED[SINGULAR],
    },
    "singular_stderr_inspected": True,
    "singular_diagnostics": singular_diagnostics,
    "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in source_paths},
    "result_payload_sha256": hashlib.sha256(payload_text.encode()).hexdigest(),
    "launch_id": None,
    "global_authority": "UNAVAILABLE",
    "observed_model": "UNKNOWN",
    "observed_effort": "UNKNOWN",
    "independence_mode": "blind-results-and-derivations",
    "statement_alignment": "Exact finite/local C03: ordered blocks (Z0,Z1,m,p,T), p fourth; H real; all five scales positive; common block covariance; no limits; KL algebra only.",
    "remaining_analytical_obligations": ["compressed probability-law equality", "test-power conclusion", "science"],
    "scientific_admission": "HOLD",
    "completed_at": datetime.now(timezone.utc).isoformat(),
}
(HERE / "axis_result.json").write_text(json.dumps(axis_result, indent=2, sort_keys=True) + "\n")
print(payload_text)
if not exact_pass:
    raise SystemExit(1)
