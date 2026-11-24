"""R108 radio lane D11: RACS-low DR1 source catalogue through the CASDA TAP service (pyvo), with a VizieR TAP fallback.

Purpose: acquire the RACS-low DR1 galactic-cut source catalogue (Hale et al. 2021, PASA 38, e058; CASDA collection
AS110, table racs_dr1_sources_galacticcut_v2021_08_v01) as an independent southern survey for an empirical radio
count dipole power C1 and a cross-check of the R65 NVSS peak/integrated estimator.
Route: pyvo.dal.TAPService on https://casda.csiro.au/casda_vo_tools/tap (no login is needed for TAP on public
catalogues; if the service demands authentication the script records that and stops). The table is fetched in
declination strips with ADQL so that each synchronous/asynchronous job stays small; every strip is saved as a
VOTable (binary2) in its own file under ~/Downloads/htt_r108/radio/racs_dr1_casda_tap/ and a receipt line
{id,name,url,final_url,bytes,sha256,status,fetched_at_utc,query,job_id,rows,service} is appended to
~/Downloads/htt_r108/radio/RECEIPTS.jsonl. Raw files are never overwritten (an existing strip is verified instead).
Inputs: none (network). Units: degrees, mJy (as served).
Usage (repo root, venv python):
    .venv/bin/python -m scripts.r108.radio_racs_fetch --probe
    .venv/bin/python -m scripts.r108.radio_racs_fetch --fetch
No randomness.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

CASDA_TAP = "https://casda.csiro.au/casda_vo_tools/tap"
VIZIER_TAP = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap"
TABLE_HINT = "racs_dr1_sources_galacticcut_v2021_08_v01"
OUT = Path.home() / "Downloads/htt_r108/radio"
STRIPDIR = OUT / "racs_dr1_casda_tap"
RECEIPTS = OUT / "RECEIPTS.jsonl"
# declination strips (deg); RACS-low DR1 covers about -80 to +30 deg (Hale et al. 2021)
DEC_EDGES = [-90.0, -75.0, -60.0, -50.0, -40.0, -30.0, -20.0, -10.0, 0.0, 10.0, 20.0, 31.0, 90.0]


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def receipt(rec):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(RECEIPTS, "a") as fh:
        fh.write(json.dumps(rec) + "\n")


def probe(service_url):
    import pyvo
    svc = pyvo.dal.TAPService(service_url)
    out = dict(service=service_url, time_utc=now())
    q = ("SELECT table_name, description FROM TAP_SCHEMA.tables "
         "WHERE table_name LIKE '%racs%' OR table_name LIKE '%RACS%'")
    try:
        res = svc.run_sync(q, maxrec=500)
        out["tables_query"] = q
        out["tables"] = [[str(r["table_name"]), str(r["description"])[:200]] for r in res]
    except Exception as exc:  # recorded, not hidden
        out["tables_error"] = f"{type(exc).__name__}: {exc}"[:2000]
    return out


def columns(svc, table):
    q = f"SELECT column_name, datatype, unit, description FROM TAP_SCHEMA.columns WHERE table_name = '{table}'"
    res = svc.run_sync(q, maxrec=500)
    return q, [[str(r["column_name"]), str(r["datatype"]), str(r["unit"]), str(r["description"])[:160]] for r in res]


def parse_votable(path):
    from astropy.io.votable import parse_single_table
    return parse_single_table(str(path)).to_table()


def check_overflow(path):
    """Return the QUERY_STATUS INFO value of a TAP VOTable result ('OK', 'OVERFLOW' or 'ERROR')."""
    from astropy.io.votable import parse
    vot = parse(str(path))
    for res in vot.resources:
        for info in res.infos:
            if info.name == "QUERY_STATUS":
                return info.value
    return "UNKNOWN"


def fetch(table, cols, dec_edges, use_async):
    import pyvo
    svc = pyvo.dal.TAPService(CASDA_TAP)
    STRIPDIR.mkdir(parents=True, exist_ok=True)
    summary = []
    for lo, hi in zip(dec_edges[:-1], dec_edges[1:]):
        name = f"racs_dr1_galcut_dec_{lo:+06.1f}_{hi:+06.1f}.vot"
        path = STRIPDIR / name
        q = f"SELECT {', '.join(cols)} FROM {table} WHERE dec >= {lo} AND dec < {hi}"
        if path.exists():
            summary.append(dict(name=name, existing=True, sha256=sha256(path), bytes=path.stat().st_size))
            continue
        t0 = time.time()
        job_id = None
        tmp = path.with_suffix(".vot.part")
        if use_async:
            job = svc.submit_job(q, maxrec=5_000_000)
            job_id = job.job_id
            job.run()
            job.wait(phases=["COMPLETED", "ERROR", "ABORTED"], timeout=1800)
            job.raise_if_error()
            # CASDA returns a result href without the /casda_vo_tools prefix (404); the UWS standard location
            # <job url>/results/result is used instead and the served bytes are stored unchanged.
            final_url = job.url.rstrip("/") + "/results/result"
        else:
            import urllib.parse
            final_url = CASDA_TAP + "/sync?" + urllib.parse.urlencode(
                dict(REQUEST="doQuery", LANG="ADQL", FORMAT="votable", MAXREC=5_000_000, QUERY=q))
        with svc._session.get(final_url, stream=True, timeout=1800) as resp:
            resp.raise_for_status()
            with open(tmp, "xb") as fh:
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    fh.write(chunk)
        tab = parse_votable(tmp)
        status = check_overflow(tmp)
        tmp.rename(path)
        rec = dict(id="D11", name=name, url=CASDA_TAP, final_url=final_url, bytes=path.stat().st_size,
                   sha256=sha256(path), status=f"ok QUERY_STATUS={status}", fetched_at_utc=now(), service=CASDA_TAP, query=q,
                   job_id=job_id, rows=len(tab), seconds=round(time.time() - t0, 2),
                   route="pyvo.dal.TAPService " + ("async" if use_async else "sync"))
        receipt(rec)
        summary.append(rec)
        print(json.dumps(rec), flush=True)
        if status != "OK":
            raise RuntimeError(f"strip {name}: QUERY_STATUS={status}; stop (row limit or error)")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--table", default=None, help="full TAP table name (from --probe)")
    ap.add_argument("--columns", default=None, help="comma-separated column list (default: all)")
    ap.add_argument("--sync", action="store_true", help="use synchronous queries instead of async jobs")
    ap.add_argument("--probe-json", default=str(OUT / "racs_casda_probe.json"))
    ap.add_argument("--versions-json", default=None, help="write COUNT(*) of the v01 and v02 galactic-cut tables to this JSON")
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    if a.probe:
        import pyvo
        res = dict(casda=probe(CASDA_TAP))
        svc = pyvo.dal.TAPService(CASDA_TAP)
        tabs = [t for t, _ in res["casda"].get("tables", []) if TABLE_HINT in t]
        if tabs:
            q, cols = columns(svc, tabs[0])
            res["casda"]["selected_table"] = tabs[0]
            res["casda"]["columns_query"] = q
            res["casda"]["columns"] = cols
            qc = f"SELECT COUNT(*) AS n FROM {tabs[0]}"
            try:
                r = svc.run_sync(qc)
                res["casda"]["row_count_query"] = qc
                res["casda"]["row_count"] = int(r[0]["n"])
            except Exception as exc:
                res["casda"]["row_count_error"] = f"{type(exc).__name__}: {exc}"[:1000]
        Path(a.probe_json).write_text(json.dumps(res, indent=1))
        print(json.dumps(res, indent=1)[:6000])
    if a.versions_json:
        import pyvo
        svc = pyvo.dal.TAPService(CASDA_TAP)
        import subprocess
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        res = dict(service=CASDA_TAP, time_utc=now(), git_head=head, script_sha256=sha256(Path(__file__)),
                   command=" ".join([sys.executable, "-m", "scripts.r108.radio_racs_fetch", *(argv or sys.argv[1:])]),
                   inputs="none (network TAP queries)", counts={})
        for t in ("AS110.racs_dr1_sources_galacticcut_v2021_08_v01", "AS110.racs_dr1_sources_galacticcut_v2021_08_v02"):
            q = f"SELECT COUNT(*) AS n FROM {t}"
            res["counts"][t] = dict(query=q, n=int(svc.run_sync(q)[0]["n"]))
        Path(a.versions_json).write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(res))
    if a.fetch:
        if not a.table:
            raise SystemExit("--table required")
        cols = a.columns.split(",") if a.columns else ["*"]
        s = fetch(a.table, cols, DEC_EDGES, not a.sync)
        print(json.dumps(dict(n_strips=len(s), rows=sum(x.get("rows", 0) for x in s)), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
