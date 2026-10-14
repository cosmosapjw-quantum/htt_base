import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
BASE = Path(__file__).resolve().parent.parent
ORACLE = Path("/home/cosmosapjw/lean_oracles/viii_oracle")
SOURCE = BASE / "ScalarWrapper.lean"
WEIGHTED = BASE.parent / "c02_weighted_thomson_moment_v1_20261011/WeightedMoment.lean"
CONTRACT = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-12.json"
ENV = dict(os.environ, ELAN_TOOLCHAIN="leanprover/lean4:v4.31.0")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(name, argv, cwd):
    start = time.time()
    result = subprocess.run(argv, cwd=cwd, env=ENV, capture_output=True, timeout=180)
    (BASE / "raw" / (name + ".stdout.log")).write_bytes(result.stdout)
    (BASE / "raw" / (name + ".stderr.log")).write_bytes(result.stderr)
    receipt = dict(argv=argv, cwd=str(cwd), exit_code=result.returncode,
                   wall_seconds=time.time() - start, source_sha256=sha(SOURCE))
    (BASE / "raw" / (name + ".execution.json")).write_text(json.dumps(receipt, indent=2) + "\n")
    if result.returncode:
        raise SystemExit(result.returncode)

bindings = dict(packet_sha256=sha(BASE / "DELEGATION_PACKET.json"),
                contract_sha256=sha(CONTRACT), weighted_source_sha256=sha(WEIGHTED),
                exact_literal_prefix=SOURCE.read_bytes().startswith(WEIGHTED.read_bytes()),
                scalar_source_sha256=sha(SOURCE))
assert bindings["packet_sha256"] == "07fa31d1c3f10fadb24c7ffb590e76686b8be1b73878cf8f9cbab61d6656ebe6"
assert bindings["weighted_source_sha256"] == "3d07b12c2e269bbc2c18ac248aff08d9bf2110d683d5fafda868fd3cf1972d2e"
assert bindings["contract_sha256"] == "5a6827166fe318e37ac9e503a91d6f729155cbef48f450cd9daf0896e47fa6ae"
assert bindings["exact_literal_prefix"]
(BASE / "raw/source_bindings.json").write_text(json.dumps(bindings, indent=2) + "\n")
run("lean_version", ["lake", "env", "lean", "--version"], ORACLE)
run("mathlib_identity", ["git", "rev-parse", "HEAD"], ORACLE / ".lake/packages/mathlib")
run("compile_02", ["lake", "env", "lean", str(SOURCE)], ORACLE)
run("axiom_audit", ["lake", "env", "lean", str(BASE / "raw/AxiomAudit.lean")], ORACLE)
