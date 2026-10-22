"""G17-A pinned compile harness (modelled on CAS-10 g10a raw/run_compile.py and the
CAS-17 g17d / CAS-01 g01a successors).
Every attempt snapshots the exact source, records argv/cwd/exit/hashes/UTC times,
keeps stdout/stderr, never deletes attempts. Timeout 900 s.
Usage: python3 run_compile.py <step> [<step> ...]; probe steps: probe:<file under raw/probes>"""
import hashlib, json, pathlib, shutil, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP, PROBES = T / "raw", T / "raw" / "imports", T / "raw" / "probes"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
CAS17 = T.parent
CASROOT = CAS17.parent
C01 = CAS17 / "c01_gram_tilt_bridge_v1_20261010" / "lean" / "C01.lean"
M05_ORIG = CASROOT / "CAS-07" / "determinant_distance_bridge_v1_20261007" / "lean" / "Main.lean"
M05 = IMP / "CAS07M05Accepted.lean"
G01A = CASROOT / "CAS-01" / "g01a_jacobi_vertex_taylor_v1_20261014" / "lean" / "G01AJacobiVertex.lean"
CORE = T / "lean" / "G17ACore.lean"
OPT = T / "lean" / "G17AOptics.lean"
ORACLE_OLEANS = {  # reviewed accepted oracle oleans consumed by M05 (hashes from G01-A receipts)
    "CAS07M01Accepted.olean": "83acab45987909a490f90af775cc0f3ce538de3a5e04ed5a04abc311d9c15ca2",
    "CAS07M04Accepted.olean": "81e374aa492d6528188225df432f1036dd460f168f31aa15e544289b46c8182a",
    "CAS07C02Accepted.olean": "67344c6d91e2abfcdc8bae9329f55a3d659438bd61a34cb91d3670e3123bb2c0",
}
h = lambda b: hashlib.sha256(b).hexdigest()
def lp(cmd): return f"LEAN_PATH={IMP}:{ORACLE}:$LEAN_PATH {cmd}"
STEPS = {
  "imp_c01": (C01, lp(f"lean -R {C01.parent} -o {IMP}/C01.olean {C01}"), IMP / "C01.olean"),
  "imp_m05": (M05, lp(f"lean -R {IMP} -o {IMP}/CAS07M05Accepted.olean {M05}"), IMP / "CAS07M05Accepted.olean"),
  "imp_g01a": (G01A, lp(f"lean -R {G01A.parent} -o {IMP}/G01AJacobiVertex.olean {G01A}"), IMP / "G01AJacobiVertex.olean"),
  "core": (CORE, lp(f"lean -R {CORE.parent} -o {IMP}/G17ACore.olean {CORE}"), IMP / "G17ACore.olean"),
  "optics": (OPT, lp(f"lean -R {OPT.parent} -o {IMP}/G17AOptics.olean {OPT}"), IMP / "G17AOptics.olean"),
  "audit": (RAW / "AxiomAudit.lean", lp(f"lean -R {RAW} {RAW/'AxiomAudit.lean'}"), None),
}
def step(name):
    if name.startswith("probe:"):
        src = PROBES / name.split(":", 1)[1]
        return src, lp(f"lean -R {PROBES} {src}"), None, "probe_" + src.stem
    src, cmd, ol = STEPS[name]
    return src, cmd, ol, name
IMP.mkdir(parents=True, exist_ok=True)
for arg in sys.argv[1:]:
    extra = {}
    if arg == "imp_m05":
        shutil.copyfile(M05_ORIG, M05)
        assert h(M05_ORIG.read_bytes()) == h(M05.read_bytes())
        extra = {"copied_from": str(M05_ORIG), "copied_from_sha256": h(M05_ORIG.read_bytes())}
    for f, d in ORACLE_OLEANS.items():
        assert h(pathlib.Path(ORACLE, f).read_bytes()) == d, ("ORACLE_OLEAN_MISMATCH", f)
    src, cmd, olean, label = step(arg)
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{label}"
    data = src.read_bytes(); (RAW / (stem.name + ".source.lean")).write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]; t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900); out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    t1 = datetime.now(timezone.utc).isoformat()
    (RAW / (stem.name + ".stdout")).write_bytes(out); (RAW / (stem.name + ".stderr")).write_bytes(err)
    rec = {"step": label, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1, "exit_code": rc,
           "source_path": str(src), "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err),
           "oracle_oleans_sha256": ORACLE_OLEANS, **extra}
    if olean is not None and rc == 0 and olean.exists():
        rec["olean_path"] = str(olean); rec["olean_sha256"] = h(olean.read_bytes())
    (RAW / (stem.name + ".json")).write_text(json.dumps(rec, indent=1) + "\n")
    print(label, "exit", rc)
    txt = out.decode(errors="replace") + err.decode(errors="replace")
    for line in txt.splitlines():
        if "error:" in line: print("ERRLINE", line)
    if rc: print(txt[-6000:]); sys.exit(rc)
