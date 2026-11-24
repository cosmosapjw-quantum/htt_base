"""R108 radio lane: receipt lines for inputs that were not downloaded in R108 (RCPT-1 of the R108 review).

Purpose
    The lane RECEIPTS.jsonl must cover every raw input used. Inputs that pre-date R108 (R65 / R106 products) or that R108
    produced without a download (the CASDA TAP_SCHEMA probe response, the column cache derived from the receipted RACS
    strips) get one line each: {id, name, path, bytes, sha256, status, route, originating_round, origin, used_by,
    referenced_in (repository files that cite the SHA-256 outside R108), pinned_in_code, recorded_at_utc, recorded_by}, plus
    produced_by_command for R108-produced files. A line is appended only if no line with the same id and SHA-256 exists;
    the same id with another SHA-256 fails closed (the input changed since it was receipted).
Inputs (read, SHA-256 computed here)
    ~/Downloads/htt_r106_analysis/nvss/review_followup/C1ZERO_DRAWS.npz (R106), R106 NVSS_REVIEW_CORRECTIONS.json,
    R65 PROVIDER_NVSS_CARRIERS.npz and PROVIDER_NVSS_RESULT.json, ~/Downloads/htt_r108/radio/racs_casda_probe.json,
    ~/Downloads/htt_r108/radio/derived/racs_dr1_galcut_v01_columns.npz; ~/Downloads/htt_r108/logs/radio_COMMANDS.jsonl.
Units: bytes.
Usage (repo root): python3 -m scripts.r108.radio_input_receipts [--dry-run]
No randomness.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOCS = Path("docs/research_program/observational_publication_20261015")
R108_DOCS = DOCS / "R108_LOS_ATLAS_DATA_20261124"
RADIO_DL = Path.home() / "Downloads/htt_r108/radio"
LOGS = Path.home() / "Downloads/htt_r108/logs"
PRE = "PRE_EXISTING_INPUT"
ROUTE = "pre-existing input: not fetched in R108; identity by SHA-256 at receipt time"


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def _grep(sha, roots, exclude=()):
    """Repository files (relative paths) whose text contains the SHA-256, sorted; R108 outputs excluded."""
    proc = subprocess.run(["grep", "-rlF", "--include=*.json", "--include=*.md", "--include=*.py", "--include=*.yaml", sha,
                           *[str(r) for r in roots]], capture_output=True, text=True, cwd=REPO)
    hits = sorted(h for h in proc.stdout.splitlines() if h and not any(h.startswith(str(e)) for e in exclude))
    return hits


def entry(id_, path, status, originating_round, origin, used_by, **extra):
    """One receipt line for a local file (SHA-256 and size computed now)."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = REPO / p
    digest = sha256(p)
    rec = dict(id=id_, name=p.name, path=str(p), bytes=p.stat().st_size, sha256=digest, status=status, url=None, route=ROUTE,
               originating_round=originating_round, origin=origin, used_by=used_by,
               referenced_in=_grep(digest, [DOCS], exclude=[R108_DOCS]),
               pinned_in_code=_grep(digest, [Path("scripts"), Path("htt")], exclude=[Path("scripts/r108")]))
    rec.update(extra)
    return rec


def command_line(jsonl, needle):
    """First command-log line whose cmd contains the needle (the command that produced an R108 file)."""
    for line in Path(jsonl).read_text().splitlines():
        r = json.loads(line)
        if needle in r.get("cmd", ""):
            return r
    raise LookupError(f"no command containing {needle!r} in {jsonl}")


def append_receipts(receipts, entries, recorded_by, dry_run=False):
    """Append entries not yet present (same id and sha256); fail closed on an id whose SHA-256 changed."""
    receipts = Path(receipts)
    old = [json.loads(x) for x in receipts.read_text().splitlines() if x.strip()] if receipts.exists() else []
    have = {}
    for r in old:
        have.setdefault(r.get("id"), set()).add(r.get("sha256"))
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    new, skipped = [], []
    for e in entries:
        if e["id"] in have and e["sha256"] in have[e["id"]]:
            skipped.append(e["id"])
            continue
        if e["id"] in have:
            raise ValueError(f"receipt id {e['id']} exists with another SHA-256: input changed since it was receipted")
        new.append(dict(e, recorded_at_utc=now, recorded_by=recorded_by))
    if not dry_run and new:
        with open(receipts, "a") as fh:
            for e in new:
                fh.write(json.dumps(e, sort_keys=True) + "\n")
    return dict(appended=[e["id"] for e in new], skipped_already_present=skipped, receipts=str(receipts),
                receipts_sha256_after=sha256(receipts) if receipts.exists() else None)


def radio_entries():
    probe = RADIO_DL / "racs_casda_probe.json"
    probe_json = json.loads(probe.read_text())["casda"]
    return [
        entry("PRE:R106_C1ZERO_DRAWS", Path.home() / "Downloads/htt_r106_analysis/nvss/review_followup/C1ZERO_DRAWS.npz", PRE, "R106",
              "R106 NVSS review follow-up C1 = 0 common-random-number mock ensembles (outside the repository; SHA pinned in "
              "R106 NVSS_REVIEW_CORRECTIONS / C1ZERO / RUN_RECORD)", ["scripts/r108/radio_p_of_c1.py"]),
        entry("PRE:R106_NVSS_REVIEW_CORRECTIONS", DOCS / "R106_RESEARCH_20261124/NVSS/NVSS_REVIEW_CORRECTIONS.json", PRE, "R106",
              "R106 NVSS review corrections (observed delta, t_self, df, p-versus-C1 grid, crossings)", ["scripts/r108/radio_p_of_c1.py"]),
        entry("PRE:R65_PROVIDER_NVSS_CARRIERS", DOCS / "R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_CARRIERS.npz", PRE, "R65",
              "R65 NVSS carrier (joint peak x integrated class counts per NSIDE-64 pixel)",
              ["scripts/r108/radio_theory_c1.py", "scripts/r108/radio_racs_dipole.py"]),
        entry("PRE:R65_PROVIDER_NVSS_RESULT", DOCS / "R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_RESULT.json", PRE, "R65",
              "R65 NVSS contrast result (replay target)", ["scripts/r108/radio_racs_dipole.py"]),
        entry("R108:racs_casda_probe", probe, "R108_PROBE_OUTPUT", "R108",
              "CASDA TAP_SCHEMA probe response written by scripts/r108/radio_racs_fetch.py --probe (table list, columns, COUNT(*))",
              ["scripts/r108/radio_racs_fetch.py (table choice)", "scripts/r108/radio_racs_dipole.py (N_ROWS_EXPECTED)"],
              service=probe_json["service"], query=probe_json["row_count_query"], rows=probe_json["row_count"],
              fetched_at_utc=probe_json["time_utc"], produced_by_command=command_line(LOGS / "radio_COMMANDS.jsonl",
                                                                                       "radio_racs_fetch --probe")),
        entry("R108:racs_dr1_columns_cache", RADIO_DL / "derived/racs_dr1_galcut_v01_columns.npz", "R108_DERIVED_CACHE", "R108",
              "column cache concatenated from the receipted D11 strips (source_key = SHA-256 of the strip digests; rebuilt if "
              "any strip digest changes)", ["scripts/r108/radio_racs_dipole.py"],
              derived_from="D11 lines of this RECEIPTS.jsonl"),
    ]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipts", default=str(RADIO_DL / "RECEIPTS.jsonl"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    res = append_receipts(a.receipts, radio_entries(), "scripts/r108/radio_input_receipts.py (sha256 "
                          f"{sha256(Path(__file__))})", a.dry_run)
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
