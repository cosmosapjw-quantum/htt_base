#!/usr/bin/env python3
"""Acquire source-bearing JWST distance-scale papers and verify their tables.

The publisher MRT URL previously used by this stage returns 404 and the old
fallback downloaded arXiv abstract HTML, which is not analytical data.  This
version downloads the author-submitted arXiv e-print archives, opens the LaTeX
members, verifies registered table markers, and records exact hashes.  A
source-checked host transcriptions plus two published-aggregate transcriptions
are committed under ``dl_pipeline/data``. Exact numerical cell markers, source
member hashes, CSV hashes, and per-dataset cell receipts are all required.

Targets (real, published):
  * Freedman et al. 2025, ApJ 985, 203  (CCHP JWST TRGB/JAGB), doi:10.3847/1538-4357/adce78
  * Riess et al. 2024/2025 (SH0ES JWST Cepheids)
  * Li et al. 2024 (8-host JWST TRGB/HST Cepheid comparison), arXiv:2408.00065
  * Li et al. 2025 (complete 35-SN TRGB compilation), arXiv:2504.08921
  * Riess et al. 2024 (additional SH0ES source context), arXiv:2401.04773

The resulting PR-153 measurement is conditional on those published tables; no
H0 fit, CF4-conditioned precision forecast, or geometry claim is authorized.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import shutil
import subprocess
import tarfile

# These scripts are run as files and are also loaded by path from repo-root
# tests, so the sibling import needs this directory on sys.path either way.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from external_store import ensure_data_dir

REPO = Path(__file__).resolve().parents[2]
SEED = REPO / "dl_pipeline/data/jwst_distances_seed.csv"
COMPARISON_TABLE = REPO / "dl_pipeline/data/jwst_host_distance_comparisons.csv"
AGGREGATE_TABLE = REPO / "dl_pipeline/data/jwst_published_aggregate_comparisons.csv"

# Author-submitted source archives.  The required member and marker pair make a
# successful HTTP transfer insufficient: the actual table-bearing source must
# be present and parseable.
TARGETS = [
    {"label": "cchp_freedman2025_source_table", "arxiv": "2408.06153",
     "member": "Ho2024.tex", "markers": ["Galaxy Distance Moduli", "tab:distances"],
     "cell_markers": [
         "2011fe & M101 & 29.151 & 0.042 & 29.208 & 0.045",
         "2012fr & N1365 & 31.366 & 0.069 & 31.384 & 0.039",
         "2015F & N2442 & 31.646 & 0.097 & 31.605 & 0.044",
         "1981B & N4536 & 30.923 & 0.052 & 30.971 & 0.034",
         "1990N & N4639 & 31.774 & 0.073 & 31.733 & 0.039",
         "2013aa & N5643 & 30.643 & 0.071 & 30.582 & 0.038",
         "2013dy & N7250 & 31.629 & 0.047 & 31.592 & 0.043",
     ],
     "analysis_table_ingested": True},
    {"label": "shoes_riess2025_source_table", "arxiv": "2509.01667",
     "member": "main.tex", "markers": ["Distance moduli and uncertainties", "tab:moduli"],
     "cell_markers": [
         "3147     & 32.92 & 0.05 & 33.07 & 0.13",
         "2525 & 31.94 & 0.03 & 32.04 & 0.07",
         "5861     & 32.11 & 0.04 & 32.21 & 0.08",
         "3370     & 32.22 & 0.03 & 32.23 & 0.06",
         "5643 & 30.49 & 0.02 & 30.55 & 0.06",
         "7250     & 31.49 & 0.05 & 31.64 & 0.13",
         "4536     & 30.92 & 0.03 & 30.87 & 0.06",
         "3972     & 31.70 & 0.04 & 31.64 & 0.09",
         "4424     & 31.05 & 0.13 & 30.85 & 0.13",
         "4639     & 31.79 & 0.05 & 31.82 & 0.09",
         "M101   & 29.13 & 0.02 & 29.19 & 0.05",
         "2442     & 31.44 & 0.03 & 31.46 & 0.07",
         "1365     & 31.31 & 0.03 & 31.38 & 0.06",
     ],
     "analysis_table_ingested": True},
    {"label": "jwst_trgb_li2024_source_table", "arxiv": "2408.00065",
     "member": "sample631.tex", "markers": ["TRGB", "Cepheid"],
     "cell_markers": [
         "8 hosts of 10 Type Ia supernovae",
         "textbf{0.007} & \\textbf{0.037}",
     ],
     "analysis_table_ingested": True},
    {"label": "complete_hst_jwst_trgb_li2025_source_table", "arxiv": "2504.08921",
     "member": "main.tex", "markers": ["35", "TRGB"],
     "cell_markers": [
         "complete sample of hosts of 35 SNe~Ia",
         "$-$0.003 $\\pm$ 0.021 (stat)~mag",
         "$N=20$ objects",
     ],
     "analysis_table_ingested": True},
    {"label": "shoes_riess2024_source_table", "arxiv": "2401.04773",
     "member": "cycle1_resultsv2.tex", "markers": ["Cepheid", "JWST"],
     "analysis_table_ingested": False},
]


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _download(url: str, dst: Path) -> bool:
    if dst.exists() and dst.stat().st_size > 0:
        return True
    ensure_data_dir(dst.parent)
    if shutil.which("curl"):
        part = dst.with_name(dst.name + ".part")
        rc = subprocess.run(["curl", "-sS", "-L", "--fail", "--retry", "4",
                             "--retry-delay", "5", "--max-time", "300",
                             "-C", "-", "-o", str(part), url]).returncode
        if rc == 0 and part.exists() and part.stat().st_size > 0:
            part.replace(dst)
        return rc == 0 and dst.exists() and dst.stat().st_size > 0
    return False


def _verify_source_table(path: Path, member: str, markers: list[str],
                         cell_markers: list[str]) -> dict:
    try:
        with tarfile.open(path, mode="r:gz") as archive:
            handle = archive.extractfile(member)
            if handle is None:
                return {"ok": False, "reason": f"missing member {member}"}
            text = handle.read().decode("utf-8", errors="replace")
    except (tarfile.TarError, OSError) as exc:
        return {"ok": False, "reason": f"invalid e-print archive: {exc}"}
    absent = [marker for marker in markers if marker not in text]
    absent_cells = [marker for marker in cell_markers if marker not in text]
    cell_receipt = "sha256:" + hashlib.sha256(json.dumps(
        cell_markers, ensure_ascii=False, separators=(",", ":"),
    ).encode()).hexdigest()
    return {"ok": not absent and not absent_cells, "member": member,
            "required_markers": markers,
            "missing_markers": absent,
            "required_cell_markers": cell_markers,
            "missing_cell_markers": absent_cells,
            "cell_markers_verified": not absent_cells,
            "cell_receipt_sha256": cell_receipt,
            "member_sha256": "sha256:" + hashlib.sha256(text.encode()).hexdigest()}


def _csv_rows(path: Path) -> list[dict]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    return list(csv.DictReader(lines))


_TRANSCRIPTION_CONTRACTS = [
    {"dataset": "cchp_trgb_jagb", "source_label":
     "cchp_freedman2025_source_table", "table": "comparison", "row_count": 7,
     "fields": ["dataset", "host", "method_a", "mu_a_mag", "sigma_a_mag",
                "method_b", "mu_b_mag", "sigma_b_mag", "source_arxiv",
                "source_table"]},
    {"dataset": "shoes_jwst_hst", "source_label":
     "shoes_riess2025_source_table", "table": "comparison", "row_count": 13,
     "fields": ["dataset", "host", "method_a", "mu_a_mag", "sigma_a_mag",
                "method_b", "mu_b_mag", "sigma_b_mag", "source_arxiv",
                "source_table"]},
    {"dataset": "li2024_jwst_trgb_hst_cepheid", "source_label":
     "jwst_trgb_li2024_source_table", "table": "aggregate", "row_count": 1,
     "fields": ["dataset", "source_arxiv", "source_locator",
                "parent_sn_calibrator_count", "parent_count_unit",
                "paired_object_count", "paired_count_unit",
                "paired_sample_definition", "method_a", "method_b",
                "mean_delta_mag", "stat_standard_error_mag", "delta_definition"]},
    {"dataset": "li2025_complete_trgb_hst_cepheid", "source_label":
     "complete_hst_jwst_trgb_li2025_source_table", "table": "aggregate",
     "row_count": 1,
     "fields": ["dataset", "source_arxiv", "source_locator",
                "parent_sn_calibrator_count", "parent_count_unit",
                "paired_object_count", "paired_count_unit",
                "paired_sample_definition", "method_a", "method_b",
                "mean_delta_mag", "stat_standard_error_mag", "delta_definition"]},
]


def _transcription_receipts(fetched: list[dict]) -> list[dict]:
    tables = {"comparison": _csv_rows(COMPARISON_TABLE),
              "aggregate": _csv_rows(AGGREGATE_TABLE)}
    by_source = {row["label"]: row for row in fetched}
    receipts = []
    for contract in _TRANSCRIPTION_CONTRACTS:
        rows = [row for row in tables[contract["table"]]
                if row.get("dataset") == contract["dataset"]]
        exact_cells = [
            {field: row.get(field) for field in contract["fields"]}
            for row in rows
        ]
        source = by_source.get(contract["source_label"], {})
        verification = source.get("verification") or {}
        verified = bool(
            len(rows) == contract["row_count"]
            and verification.get("ok") is True
            and verification.get("cell_markers_verified") is True
            and not verification.get("missing_markers")
            and not verification.get("missing_cell_markers")
        )
        receipts.append({
            "dataset": contract["dataset"],
            "source_label": contract["source_label"],
            "source_arxiv": source.get("arxiv"),
            "source_member": verification.get("member"),
            "source_archive_sha256": source.get("sha256"),
            "source_member_sha256": verification.get("member_sha256"),
            "source_cell_receipt_sha256": verification.get("cell_receipt_sha256"),
            "transcription_csv": str((COMPARISON_TABLE if contract["table"] ==
                                      "comparison" else AGGREGATE_TABLE)
                                     .relative_to(REPO)),
            "transcription_csv_sha256": _sha256(
                COMPARISON_TABLE if contract["table"] == "comparison"
                else AGGREGATE_TABLE),
            "registered_row_count": contract["row_count"],
            "observed_row_count": len(rows),
            "exact_cells_sha256": "sha256:" + hashlib.sha256(json.dumps(
                exact_cells, sort_keys=True, separators=(",", ":"),
            ).encode()).hexdigest(),
            "exact_cells": exact_cells,
            "verified": verified,
        })
    return receipts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-dir", type=Path, default=REPO / "workdir/raw/jwst_anchors")
    args = ap.parse_args(argv)
    raw = args.raw_dir
    ensure_data_dir(raw)

    fetched, missing = [], []
    for target in TARGETS:
        label = target["label"]
        arxiv = target["arxiv"]
        url = f"https://export.arxiv.org/e-print/{arxiv}"
        dst = raw / f"arxiv_{arxiv}.src.tar.gz"
        if _download(url, dst):
            verification = _verify_source_table(
                dst, target["member"], list(target["markers"]),
                list(target.get("cell_markers", [])))
            if not verification["ok"]:
                missing.append({"label": label, "url": url,
                                "reason": verification["reason"] if "reason" in verification
                                else f"missing markers {verification['missing_markers']}"})
                continue
            fetched.append({"label": label, "url": url, "path": dst.name,
                            "arxiv": arxiv, "sha256": _sha256(dst),
                            "content_verified_data_table": True,
                            "analysis_table_ingested": target["analysis_table_ingested"],
                            "verification": verification})
        else:
            missing.append({"label": label, "url": url})

    seed_present = SEED.is_file()
    table_present = COMPARISON_TABLE.is_file()
    aggregate_present = AGGREGATE_TABLE.is_file()
    receipts = (_transcription_receipts(fetched)
                if table_present and aggregate_present else [])
    receipts_verified = (len(receipts) == len(_TRANSCRIPTION_CONTRACTS)
                         and all(row["verified"] for row in receipts))
    manifest = {
        "schema": "htt.jwst_source_table_acquisition.v4",
        "product": "JWST published host-distance source tables",
        "fetched": fetched,
        "missing": missing,
        "seed_csv": str(SEED.relative_to(REPO)) if seed_present else None,
        "seed_sha256": _sha256(SEED) if seed_present else None,
        "source_checked_comparison_csv": (str(COMPARISON_TABLE.relative_to(REPO))
                                           if table_present else None),
        "source_checked_comparison_csv_sha256": (_sha256(COMPARISON_TABLE)
                                                   if table_present else None),
        "source_checked_aggregate_csv": (str(AGGREGATE_TABLE.relative_to(REPO))
                                           if aggregate_present else None),
        "source_checked_aggregate_csv_sha256": (_sha256(AGGREGATE_TABLE)
                                                  if aggregate_present else None),
        "transcription_receipts": receipts,
        "status": ("source_tables_and_exact_cells_verified"
                   if len(fetched) == len(TARGETS) and receipts_verified
                   else "partial_source_tables_verified" if fetched else "offline"),
        "note": ("arXiv e-print archives are verified by table-bearing LaTeX members; "
                 "abstract HTML is never counted as data. The committed host table and "
                 "published-aggregate transcription support distance-method consistency "
                 "measurements only; no H0 fit, "
                 "CF4-conditioned precision forecast, or geometry claim."),
    }
    (raw / "jwst_anchors_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"JWST anchors: fetched {len(fetched)}, missing {len(missing)}, "
          f"seed={'present' if seed_present else 'ABSENT'} -> {raw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
