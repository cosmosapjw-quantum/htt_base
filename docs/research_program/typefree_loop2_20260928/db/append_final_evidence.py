#!/usr/bin/env python3
"""Append final proof/transcript revisions to the Loop 2 copied database."""
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parents[1]
DB = Path("/tmp/htt_typefree_inheritance_loop2.sqlite")
EXPECTED = "15072871f6154cd79cc52072fdffc38b00fd7427cef1a3836dbacd994b122862"

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

if sha(DB) != EXPECTED:
    raise SystemExit("refusing nonmatching migrated copy")
contract_hash = sha(HERE / "CLAIM_CONTRACT.json")
rows = [
    ("TF-P2", "lean_mathlib", "KERNEL_PROVED_DIAGONAL_COMPONENTS",
     "lean/lean_final_raw.txt", "3-column diagonal gap and explicit 3x3 decomposition only"),
    ("TF-S2", "lean_mathlib_final", "KERNEL_PROVED_SET_COMPONENT",
     "lean/lean_final_raw.txt", "same set proof; final axiom list"),
    ("TF-S4", "lean_mathlib_final", "KERNEL_PROVED_COMPONENTS",
     "lean/lean_final_raw.txt", "same diameter/union-bound components; final axiom list"),
    ("TF-P3", "wolfram_xact_final", "EXACT_POINT_JET_VERIFIED",
     "wolfram/tf_p3_xact_final_raw.txt", "includes xAct Riemann sign +1"),
    ("TF-P3", "sympy_host", "EXACT_POINT_CONNECTION_CROSSCHECK",
     "sympy/sympy_raw.json", "same host; no blinded independent CAS adjudication"),
]
con=sqlite3.connect(DB)
try:
    con.execute("BEGIN IMMEDIATE")
    for claim,engine,status,rel,caveat in rows:
        path=HERE/rel
        con.execute("INSERT INTO loop2_evidence VALUES (?,?,?,?,?,?,?)",
                    (claim,engine,status,str(path.relative_to(ROOT)),sha(path),
                     contract_hash,caveat))
    lean=ROOT/"formal_mathlib/Egs3V8Mathlib/TypefreeLoop2.lean"
    con.execute("INSERT INTO loop2_source_lineage VALUES (?,?,?)",
                (str(lean.relative_to(ROOT)),sha(lean),"Loop 2 kernel proof source"))
    con.commit()
    check=con.execute("PRAGMA integrity_check").fetchone()[0]
    count=con.execute("SELECT count(*) FROM loop2_evidence").fetchone()[0]
    before_after={t:con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        for t in ("original_items","normalized_claims","loop_claims","occurrences")}
    if check!="ok" or count!=11 or before_after!={
        "original_items":40282,"normalized_claims":40467,
        "loop_claims":13,"occurrences":104780}:
        raise SystemExit("post-append validation failure")
finally:
    con.close()
out=HERE/"db/THEORY_INHERITANCE_LOOP2_FINAL.sqlite.gz"
with out.open("xb") as raw:
    with gzip.GzipFile(filename="",mode="wb",fileobj=raw,mtime=0,compresslevel=6) as gz:
        with DB.open("rb") as f:
            for b in iter(lambda:f.read(4*1024*1024),b""):
                gz.write(b)
receipt={"previous_db_sha256":EXPECTED,"final_db_sha256":sha(DB),
         "final_gzip_sha256":sha(out),"final_gzip_bytes":out.stat().st_size,
         "integrity_check":check,"loop2_evidence_rows":count,
         "source_lineage_rows":8,"historical_counts":before_after,
         "original_db_overwritten":False}
(HERE/"db/MIGRATION_FINAL_RESULT.json").write_text(
    json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(receipt,ensure_ascii=False))
