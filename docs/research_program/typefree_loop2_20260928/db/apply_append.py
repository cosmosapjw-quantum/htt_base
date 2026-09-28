#!/usr/bin/env python3
"""Append Loop 2 evidence to a byte-verified *copy* of the Loop 1 SQLite.

Never accepts the original source path or a previously migrated database.
"""
import argparse
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parents[1]
BASE_SHA = "6587bf88aa161ff2bd345610cdc8485c5e50095c750643359e2de4851537a4cc"
BASE_COUNTS = {"original_items": 40282, "normalized_claims": 40467,
               "loop_claims": 13, "occurrences": 104780}

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db-copy", type=Path, required=True)
    args = p.parse_args()
    db = args.db_copy.resolve(strict=True)
    if db == (ROOT / "THEORY_INHERITANCE.sqlite").resolve():
        raise SystemExit("refusing original database path")
    if sha(db) != BASE_SHA:
        raise SystemExit("copy is not the exact verified Loop 1 SQLite")
    contract = HERE / "CLAIM_CONTRACT.json"
    contract_sha = sha(contract)
    entries = [
        ("TF-P2", "wolfram", "EXACT_FINITE_ALGEBRA_HAND_DG_BRIDGE",
         "wolfram/tf_p2_raw.txt", "rest-frame matrix identity exact; geometric eigenvector differentiation remains handwritten"),
        ("TF-P3", "wolfram_xact", "EXACT_POINT_JET_VERIFIED",
         "wolfram/tf_p3_xact_raw.txt", "local total Einstein source, finite-lambda neighborhood only"),
        ("TF-S2", "lean_mathlib", "KERNEL_PROVED_SET_COMPONENT",
         "lean/lean_raw.txt", "joint event inclusion and measure monotonicity only; typed unavailable branch not formalized"),
        ("TF-S4", "lean_mathlib", "KERNEL_PROVED_COMPONENTS",
         "lean/lean_raw.txt", "bounded-set diameter event and real union-bound algebra; full statistical law bridge remains handwritten"),
        ("TF-C1", "sage_singular", "SYMBOLIC_EXAMPLE_ONLY",
         "sage/sage_raw.txt", "Jacobi ideal and rational image example; no universal real feasibility theorem"),
        ("TF-W1", "analytic", "SPECIFIED_INPUT_UNAVAILABLE",
         "TF_W1_INPUT_KO.md", "no observed source/moment time law"),
    ]
    lineage_names = [
        "RESEARCH_ARCHITECTURE_KO.md", "ADJUDICATED_AMENDMENTS_KO.md",
        "INDEPENDENT_DECISION.json", "INHERITANCE_MAP.json",
        "DELIVERABLE_MANIFEST.json", "QUERY_EXAMPLES.sql",
    ]
    con = sqlite3.connect(db)
    try:
        before = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                  for t in BASE_COUNTS}
        if before != BASE_COUNTS:
            raise SystemExit(f"historical counts differ: {before}")
        con.execute("BEGIN IMMEDIATE")
        con.execute("""
          CREATE TABLE loop2_evidence (
            claim_id TEXT NOT NULL, engine TEXT NOT NULL, status TEXT NOT NULL,
            artifact_path TEXT NOT NULL, artifact_sha256 TEXT NOT NULL,
            contract_sha256 TEXT NOT NULL, caveat TEXT NOT NULL,
            PRIMARY KEY (claim_id, engine))
        """)
        con.execute("""
          CREATE TABLE loop2_source_lineage (
            source_path TEXT PRIMARY KEY, source_sha256 TEXT NOT NULL,
            source_role TEXT NOT NULL)
        """)
        for claim, engine, status, rel, caveat in entries:
            path = HERE / rel
            con.execute("INSERT INTO loop2_evidence VALUES (?,?,?,?,?,?,?)",
                        (claim, engine, status, str(path.relative_to(ROOT)),
                         sha(path), contract_sha, caveat))
        for name in lineage_names:
            path = HERE / "source" / name
            con.execute("INSERT INTO loop2_source_lineage VALUES (?,?,?)",
                        (str(path.relative_to(ROOT)), sha(path), "Loop 1 source bytes"))
        r2 = ROOT / "docs/research_program/mes_verified_checkpoints_20260928/I1/recovery/research/readable_research/MES_GENERALIZED_TENSOR_R2/agent_kinematics.md"
        con.execute("INSERT INTO loop2_source_lineage VALUES (?,?,?)",
                    (str(r2.relative_to(ROOT)), sha(r2), "R2 exact brightness weak law"))
        con.commit()
        after = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                 for t in BASE_COUNTS}
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        if after != before or integrity != "ok":
            raise SystemExit(f"post-append historical count/integrity failure: {after}, {integrity}")
    finally:
        con.close()
    out = HERE / "db" / "THEORY_INHERITANCE_LOOP2.sqlite.gz"
    if out.exists():
        raise SystemExit(f"refusing overwrite: {out}")
    with out.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as gz:
            with db.open("rb") as src:
                for chunk in iter(lambda: src.read(4 * 1024 * 1024), b""):
                    gz.write(chunk)
    report = {
        "source_db_sha256": BASE_SHA, "migrated_db_sha256": sha(db),
        "migrated_gzip_sha256": sha(out), "migrated_gzip_bytes": out.stat().st_size,
        "contract_sha256": contract_sha, "historical_counts_before": before,
        "historical_counts_after": after, "integrity_check": integrity,
        "loop2_evidence_rows": len(entries), "source_lineage_rows": len(lineage_names) + 1,
        "original_db_overwritten": False,
    }
    (HERE / "db" / "MIGRATION_RESULT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
