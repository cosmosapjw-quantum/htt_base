"""L2-W1-B compile harness: snapshot exact source, run one frozen Lean argv, keep every attempt.

Usage: python3 run_compile.py <step> [<step> ...]
Steps: imp_bridge | imp_g08a | imp_p08a | imp_p08b | imp_l2w1a | main | audit
Each invocation gets the next global index NN (never overwriting earlier attempts) and writes
compile_NN_<step>.source.lean (pre-execution snapshot), .stdout, .stderr, .json receipts.
Modelled on CAS-10/g10a_restspace_positivity_v1_20261013/raw/run_compile.py and
PORT-CAS-08/ellipsoid_image_v1_20261013/raw/run_compile.py.
Reused reviewed sources are compiled UNCHANGED from their original paths into T/raw/imports;
the harness never writes outside T/raw.
"""
import hashlib, json, pathlib, re, shutil, subprocess, sys
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
IMP.mkdir(exist_ok=True)
DOCS = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program")
CAS08 = DOCS / "gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-08"
BRIDGE = CAS08 / "c01_c02_projection_bridge_v1_20261011" / "ProjectionBridge.lean"
G08A = CAS08 / "g08a_whitening_gls_v1_20261013" / "lean" / "G08AWhitening.lean"
P08 = DOCS / "theory_inference_port_20260930/local_execution/PORT-CAS-08"
P08A = P08 / "ellipsoid_fiber_mp_v1_20261013" / "lean" / "P08EllipsoidFiber.lean"
P08B = P08 / "ellipsoid_image_v1_20261013" / "lean" / "P08EllipsoidImage.lean"
L2W1A = DOCS / "typefree_loop2_closeout_20260928/l2w1a_kernel_bound_v1_20261013/lean/L2W1KernelBound.lean"
MAIN = T / "lean" / "L2W1FibreImage.lean"
AUDIT = RAW / "AxiomAudit.lean"
EXPECTED = {  # reviewed source hashes (RETURN.json of each unit)
    BRIDGE: "440e3820a53a1bc12465975eaed331db2e9b4f7fbdc4e97d9d5c58a4c1cc2219",
    G08A: "e62280213d23063cf4309aa8bdc814b2925f44f50cb81859f6b91bcb976bf045",
    P08A: "a69fb0ad3f476a0ece48dd77d9eca10930c8f8ee989c44f2f1e3bc5ff906c8ab",
    P08B: "0cb88696a6a07e8ae54aff8c2ea8b759b7aa4b24f1248039df6998cc1cc7cd0a",
    L2W1A: "5556288e5629bda32d7132841992935408690ecf42154963869558be96ab9f55",
}
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
TIMEOUT_S = 900
LP = f"LEAN_PATH={IMP}:$LEAN_PATH"


def olean_cmd(src, mod):
    return f"{LP} lean -R {src.parent} -o {IMP / (mod + '.olean')} {src}", IMP / (mod + ".olean")


STEPS = {
    "imp_bridge": (BRIDGE, *olean_cmd(BRIDGE, "ProjectionBridge")),
    "imp_g08a": (G08A, *olean_cmd(G08A, "G08AWhitening")),
    "imp_p08a": (P08A, *olean_cmd(P08A, "P08EllipsoidFiber")),
    "imp_p08b": (P08B, *olean_cmd(P08B, "P08EllipsoidImage")),
    "imp_l2w1a": (L2W1A, *olean_cmd(L2W1A, "L2W1KernelBound")),
    "main": (MAIN, *olean_cmd(MAIN, "L2W1FibreImage")),
    "audit": (AUDIT, f"{LP} lean -R {RAW} {AUDIT}", None),
}
h = lambda b: hashlib.sha256(b).hexdigest()


def import_hashes():
    return {str(p): h(p.read_bytes()) for p in sorted(IMP.glob("*.olean"))}


def next_index():
    used = [int(m.group(1)) for p in RAW.glob("compile_*.json")
            if (m := re.fullmatch(r"compile_(\d+)_\w+\.json", p.name))]
    return max(used, default=0) + 1


for name in sys.argv[1:]:
    src, cmd, olean = STEPS[name]
    data = src.read_bytes()
    if src in EXPECTED and h(data) != EXPECTED[src]:
        sys.exit(f"reused source hash mismatch: {src}")
    n = next_index()
    stem = f"compile_{n:02d}_{name}"
    (RAW / f"{stem}.source.lean").write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]
    before = import_hashes()
    t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=TIMEOUT_S)
        out, err, rc, to = r.stdout, r.stderr, r.returncode, False
    except subprocess.TimeoutExpired as e:
        out, err, rc, to = e.stdout or b"", e.stderr or b"", 124, True
    t1 = datetime.now(timezone.utc).isoformat()
    (RAW / f"{stem}.stdout").write_bytes(out)
    (RAW / f"{stem}.stderr").write_bytes(err)
    rec = {"index": n, "step": name, "argv": argv, "lake_resolved": shutil.which("lake"),
           "cwd": ORACLE, "started_utc": t0, "finished_utc": t1, "timeout_seconds": TIMEOUT_S,
           "timed_out": to, "exit_code": rc, "source_path": str(src),
           "source_snapshot": f"{stem}.source.lean", "source_sha256": h(data),
           "source_expected_sha256": EXPECTED.get(src), "stdout_sha256": h(out),
           "stderr_sha256": h(err), "olean_out": str(olean) if olean else None,
           "olean_sha256_after": h(olean.read_bytes()) if olean and rc == 0 and olean.exists() else None,
           "import_sha256_before": before, "import_sha256_after": import_hashes()}
    (RAW / f"{stem}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(f"{stem}: exit={rc} source_sha256={rec['source_sha256']}", flush=True)
    if rc or out:
        print(out.decode(errors="replace")[-12000:], err.decode(errors="replace")[-3000:])
    if rc:
        sys.exit(rc)
