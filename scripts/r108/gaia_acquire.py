"""R108 gaia lane: catalogue and archive acquisition through astroquery / pyvo (no hand-written HTTP).

Purpose
  D08  ICRF3 S/X positions (Charlot et al. 2020, A&A 644, A159; VizieR J/A+A/644/A159/table10,
       4,536 sources) through astroquery.vizier on a reachable VizieR mirror (the CDS ftp tree and
       TAPVizieR were unreachable on 2026-11-24, see the lane log).
  D10  Gaia DR3 AGN cross-identifications joined with gaia_source astrometry, the manifest ADQL of
       scripts/r107_cloud/acquisition.py item D10, run verbatim as an async job on the ESA Gaia TAP
       (https://gea.esac.esa.int/tap-server/tap) through pyvo; the row count is checked against an
       archive COUNT of the same join.
  D10S Supplement (same service): gaiadr3.gaia_crf3_xm external-catalogue membership flags and the
       position covariance (ra_error, dec_error, ra_dec_corr), ruwe and astrometric_params_solved of
       gaia_source for every Gaia-CRF3 source; used for the ICRF3 centroid offsets and the catalogue
       split of the R106 Quaia sample.
Each product goes into its own new directory under --directory, is never overwritten, and gets one
receipt line in <directory>/RECEIPTS.jsonl with id, name, url (service), final_url (job URL),
query, job_id, rows, bytes, sha256, status and fetched_at_utc.
Inputs: none (network services only). Units: as served (deg, mas, mas/yr, mag).
Usage (repository root, .venv interpreter):
  python -m scripts.r108.gaia_acquire icrf3 --directory ~/Downloads/htt_r108/gaia
  python -m scripts.r108.gaia_acquire agn --directory ~/Downloads/htt_r108/gaia
  python -m scripts.r108.gaia_acquire crf3flags --directory ~/Downloads/htt_r108/gaia
  python -m scripts.r108.gaia_acquire icrf3gaia --directory ~/Downloads/htt_r108/gaia
D10 / D10S large joins are split into source_id ranges because the anonymous ESA async execution limit
is 60 s; D08G is the small Gaia DR3 counterpart table of the ICRF3 S/X sources (gaia_crf3_xm.icrf3sx).
Deterministic: no random numbers.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path
import sys
import time

GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap"
VIZIER_MIRROR = "vizier.idia.ac.za"
ICRF3_TABLE = "J/A+A/644/A159/table10"
ICRF3_EXPECTED_ROWS = 4536
D10_ADQL = ("SELECT a.source_id, a.catalogue_name, a.source_name_in_catalogue, g.ra, g.dec, g.pmra, g.pmdec, "
            "g.pmra_error, g.pmdec_error, g.pmra_pmdec_corr, g.phot_g_mean_mag, g.bp_rp FROM gaiadr3.agn_cross_id AS a "
            "JOIN gaiadr3.gaia_source AS g USING (source_id)")
D10_COUNT_ADQL = ("SELECT COUNT(*) AS n_rows, COUNT(DISTINCT a.source_id) AS n_sources FROM gaiadr3.agn_cross_id AS a "
                  "JOIN gaiadr3.gaia_source AS g USING (source_id)")
AGN_COUNT_ADQL = "SELECT COUNT(*) AS n_rows FROM gaiadr3.agn_cross_id"
FLAGS = ("icrf3sx", "icrf3k", "icrf3xka", "ocars", "aw15", "r90", "m65", "c75", "dr14q", "lqac5", "lamost5", "lqrf",
         "cat2qz", "bzcat5", "cat2whspj", "alma19", "guw", "b19")
D10S_ADQL = ("SELECT x.source_id, x.icrf_name, x.iers_name, " + ", ".join(f"x.{f}" for f in FLAGS)
             + ", g.ref_epoch, g.ra, g.dec, g.ra_error, g.dec_error, g.ra_dec_corr, g.ruwe, g.astrometric_params_solved, "
               "g.nu_eff_used_in_astrometry FROM gaiadr3.gaia_crf3_xm AS x JOIN gaiadr3.gaia_source AS g USING (source_id)")
D10F_ADQL = "SELECT x.source_id, x.icrf_name, " + ", ".join(f"x.{f}" for f in FLAGS) + " FROM gaiadr3.gaia_crf3_xm AS x"
D10F_COUNT_ADQL = "SELECT COUNT(*) AS n_rows, COUNT(DISTINCT x.source_id) AS n_sources FROM gaiadr3.gaia_crf3_xm AS x"
ICRF3_GAIA_ADQL = D10S_ADQL + " WHERE x.icrf3sx = 'true'"
ICRF3_GAIA_COUNT_ADQL = ("SELECT COUNT(*) AS n_rows FROM gaiadr3.gaia_crf3_xm AS x JOIN gaiadr3.gaia_source AS g "
                         "USING (source_id) WHERE x.icrf3sx = 'true'")
D10S_COUNT_ADQL = "SELECT COUNT(*) AS n_rows FROM gaiadr3.gaia_crf3_xm AS x JOIN gaiadr3.gaia_source AS g USING (source_id)"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def now():
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def new_dir(directory: Path, name: str) -> Path:
    d = directory / name
    if d.exists():
        raise FileExistsError(f"product directory exists, refusing to overwrite: {d}")
    d.mkdir(parents=True)
    return d


def fits_safe(tab):
    """Variable-length char columns (object dtype) -> fixed-width unicode, masked/None -> ''; FITS cannot hold them."""
    import numpy as np

    for c in tab.colnames:
        if tab[c].dtype == object:
            vals = ["" if (v is None or v is np.ma.masked) else str(v) for v in tab[c]]
            tab[c] = np.array(vals, dtype=str)
    return tab


def append_receipt(directory: Path, rec: dict) -> None:
    with open(directory / "RECEIPTS.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def icrf3(directory: Path) -> dict:
    from astroquery.vizier import Vizier
    import astroquery

    out = new_dir(directory, "D08_icrf3_sx_vizier")
    v = Vizier(columns=["**"], row_limit=-1, vizier_server=VIZIER_MIRROR, timeout=300)
    t0 = time.monotonic()
    tl = v.get_catalogs(ICRF3_TABLE)
    if len(tl) != 1:
        raise RuntimeError(f"expected one table for {ICRF3_TABLE}, got {len(tl)}")
    tab = tl[0]
    path = out / "icrf3_sx_table10.vot"
    tab.write(path, format="votable")
    rows = len(tab)
    rec = {"id": "D08", "name": path.name, "url": f"https://{VIZIER_MIRROR}/viz-bin/votable",
           "final_url": f"https://{VIZIER_MIRROR}/viz-bin/votable?-source={ICRF3_TABLE}&-out=**&-out.max=unlimited",
           "query": {"tool": f"astroquery {astroquery.__version__} Vizier(columns=['**'], row_limit=-1, "
                             f"vizier_server='{VIZIER_MIRROR}').get_catalogs('{ICRF3_TABLE}')"},
           "job_id": None, "rows": rows, "expected_rows": ICRF3_EXPECTED_ROWS, "columns": tab.colnames,
           "table_description": tab.meta.get("description"), "bytes": path.stat().st_size, "sha256": sha256_file(path),
           "status": "FETCHED" if rows == ICRF3_EXPECTED_ROWS else "ROW_COUNT_MISMATCH",
           "fetched_at_utc": now(), "wall_s": time.monotonic() - t0,
           "citation": "Charlot et al. 2020, A&A 644, A159 (ICRF3), VizieR J/A+A/644/A159 table10",
           "route_note": "cdsarc.cds.unistra.fr/ftp and TAPVizieR unreachable; VizieR mirror served the table"}
    (out / "RECEIPT.json").write_text(json.dumps(rec, indent=1) + "\n")
    append_receipt(directory, rec)
    if rows != ICRF3_EXPECTED_ROWS:
        raise SystemExit(f"ICRF3 S/X row count {rows} != {ICRF3_EXPECTED_ROWS}")
    return rec


def _sync_scalar(svc, adql):
    r = svc.run_sync(adql)
    t = r.to_table()
    return {c: int(t[c][0]) for c in t.colnames}


SOURCE_ID_MAX = 12 * 4 ** 12 * 2 ** 35  # Gaia source_id < 12 * 4^12 * 2^35 (HEALPix level 12 nested index * 2^35)


def _run_chunk(svc, adql, lo, hi, alias, maxrec):
    """One async job restricted to lo <= source_id < hi; returns (table or None, job record)."""
    import pyvo

    q = f"{adql} WHERE {alias}.source_id >= {lo} AND {alias}.source_id < {hi}"
    job = svc.submit_job(q, maxrec=maxrec, language="ADQL")
    rec = {"lo": lo, "hi": hi, "query": q, "job_url": job.url, "job_id": job.job_id, "submitted_utc": now()}
    job.run()
    try:
        job.wait(phases=["COMPLETED", "ERROR", "ABORTED"], timeout=900)
    except pyvo.dal.DALServiceError:
        pass
    rec["phase"] = job.phase
    if rec["phase"] != "COMPLETED":
        es = job._job.errorsummary
        rec["error"] = es.message.content if es is not None and es.message is not None else None
        tab = None
    else:
        res = job.fetch_result()
        tab = res.to_table()
        rec["rows"] = len(tab)
        rec["query_status"] = getattr(res, "query_status", None)
    try:
        job.delete()
    except Exception:  # housekeeping only
        pass
    return tab, rec


def tap_single(directory: Path, item: str, subdir: str, fname: str, adql: str, count_adql: str) -> dict:
    """One async job (small products); the row count is checked against the archive COUNT."""
    import pyvo

    out = new_dir(directory, subdir)
    svc = pyvo.dal.TAPService(GAIA_TAP)
    t0 = time.monotonic()
    counts = _sync_scalar(svc, count_adql)
    tab, job = _run_chunk_query(svc, adql, 3_000_000)
    (out / "JOBS.jsonl").write_text(json.dumps(job) + "\n")
    if tab is None:
        raise RuntimeError(f"{item}: job failed: {job}")
    path = out / fname
    fits_safe(tab).write(path, format="fits")
    ok = len(tab) == counts["n_rows"]
    rec = {"id": item, "name": path.name, "url": GAIA_TAP, "final_url": job["job_url"], "job_id": job["job_id"],
           "query": adql, "count_query": count_adql, "archive_count": counts, "rows": len(tab), "columns": tab.colnames,
           "bytes": path.stat().st_size, "sha256": sha256_file(path), "status": "FETCHED" if ok else "ROW_COUNT_MISMATCH",
           "fetched_at_utc": now(), "wall_s": time.monotonic() - t0, "tool": f"pyvo {pyvo.__version__} async TAP (anonymous)"}
    (out / "RECEIPT.json").write_text(json.dumps(rec, indent=1) + "\n")
    append_receipt(directory, rec)
    if not ok:
        raise SystemExit(f"{item}: {len(tab)} rows != archive count {counts}")
    return rec


def _run_chunk_query(svc, q, maxrec):
    import pyvo

    job = svc.submit_job(q, maxrec=maxrec, language="ADQL")
    rec = {"query": q, "job_url": job.url, "job_id": job.job_id, "submitted_utc": now()}
    job.run()
    try:
        job.wait(phases=["COMPLETED", "ERROR", "ABORTED"], timeout=900)
    except pyvo.dal.DALServiceError:
        pass
    rec["phase"] = job.phase
    tab = None
    if rec["phase"] != "COMPLETED":
        es = job._job.errorsummary
        rec["error"] = es.message.content if es is not None and es.message is not None else None
    else:
        res = job.fetch_result()
        tab = res.to_table()
        rec["rows"] = len(tab)
        rec["query_status"] = getattr(res, "query_status", None)
    try:
        job.delete()
    except Exception:  # housekeeping only
        pass
    return tab, rec


def tap_product(directory: Path, item: str, subdir: str, fname: str, adql: str, count_adql: str, alias: str,
                nchunks: int) -> dict:
    """Manifest ADQL split into source_id ranges (the anonymous ESA async limit is 60 s of execution, which
    aborted the single-job attempt 1); a range that aborts is bisected. The union is checked against the
    archive COUNT of the unsplit query."""
    import pyvo
    from astropy.table import vstack

    out = new_dir(directory, subdir)
    svc = pyvo.dal.TAPService(GAIA_TAP)
    t0 = time.monotonic()
    counts = _sync_scalar(svc, count_adql)
    expected = counts["n_rows"]
    print(json.dumps({"item": item, "archive_count": counts}), flush=True)
    edges = [SOURCE_ID_MAX * k // nchunks for k in range(nchunks + 1)]
    todo = list(zip(edges[:-1], edges[1:]))
    tabs, jobs = [], []
    while todo:
        lo, hi = todo.pop(0)
        tab, rec = _run_chunk(svc, adql, lo, hi, alias, 3_000_000)
        jobs.append(rec)
        with open(out / "JOBS.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(json.dumps({k: rec.get(k) for k in ("lo", "hi", "phase", "rows", "job_id")}), flush=True)
        if tab is None:
            if hi - lo < SOURCE_ID_MAX // 4096 or rec["phase"] != "ABORTED":
                raise RuntimeError(f"{item}: chunk [{lo},{hi}) failed: {rec}")
            mid = (lo + hi) // 2
            todo[:0] = [(lo, mid), (mid, hi)]
            continue
        if rec.get("query_status") == "OVERFLOW":
            raise RuntimeError(f"{item}: chunk [{lo},{hi}) overflowed maxrec")
        (out / "chunks").mkdir(exist_ok=True)
        fits_safe(tab).write(out / "chunks" / f"chunk_{lo:020d}_{hi:020d}.fits", format="fits")
        tabs.append(tab)
    tab = vstack(tabs, metadata_conflicts="silent")
    path = out / fname
    fits_safe(tab).write(path, format="fits")
    rows = len(tab)
    n_unique = int(len(set(tab["source_id"].tolist())))
    ok = rows == expected and ("n_sources" not in counts or n_unique == counts["n_sources"])
    rec = {"id": item, "name": path.name, "url": GAIA_TAP, "final_url": [j["job_url"] for j in jobs if j["phase"] == "COMPLETED"],
           "job_id": [j["job_id"] for j in jobs if j["phase"] == "COMPLETED"], "query": adql,
           "query_split": f"{adql} WHERE {alias}.source_id >= lo AND {alias}.source_id < hi (ranges in JOBS.jsonl)",
           "n_jobs_completed": sum(j["phase"] == "COMPLETED" for j in jobs),
           "n_jobs_aborted_and_bisected": sum(j["phase"] == "ABORTED" for j in jobs),
           "count_query": count_adql, "archive_count": counts, "rows": rows, "unique_source_id": n_unique,
           "columns": tab.colnames, "bytes": path.stat().st_size, "sha256": sha256_file(path),
           "jobs_jsonl_sha256": sha256_file(out / "JOBS.jsonl"),
           "status": "FETCHED" if ok else "ROW_COUNT_MISMATCH", "fetched_at_utc": now(),
           "wall_s": time.monotonic() - t0, "tool": f"pyvo {pyvo.__version__} async TAP (anonymous)",
           "saved_format": "FITS binary table written by astropy from the vstacked pyvo result VOTables"}
    if item == "D10":
        rec["agn_cross_id_count"] = _sync_scalar(svc, AGN_COUNT_ADQL)
    (out / "RECEIPT.json").write_text(json.dumps(rec, indent=1) + "\n")
    append_receipt(directory, rec)
    if not ok:
        raise SystemExit(f"{item}: {rows} rows ({n_unique} unique) != archive count {counts}")
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=("icrf3", "agn", "crf3flags", "crf3flagsonly", "icrf3gaia"))
    ap.add_argument("--directory", type=Path, required=True)
    ap.add_argument("--chunks", type=int, default=48, help="initial number of source_id ranges per TAP product")
    ap.add_argument("--attempt", type=int, default=1, help="product subdirectory suffix for a retried TAP job")
    a = ap.parse_args(argv)
    a.directory = a.directory.expanduser()
    a.directory.mkdir(parents=True, exist_ok=True)
    if a.what == "icrf3":
        rec = icrf3(a.directory)
    elif a.what == "agn":
        sfx = "" if a.attempt == 1 else f"_attempt{a.attempt}"
        rec = tap_product(a.directory, "D10", "D10_agn_cross_id_gaia_source" + sfx, "agn_cross_id_gaia_source.fits",
                          D10_ADQL, D10_COUNT_ADQL, "a", a.chunks)
    elif a.what == "crf3flagsonly":
        # D10S attempt 2: the joined supplement hit the 60 s limit in dense regions; flags need no gaia_source join.
        rec = tap_product(a.directory, "D10F", "D10F_gaia_crf3_xm_flags_only", "gaia_crf3_xm_flags.fits",
                          D10F_ADQL, D10F_COUNT_ADQL, "x", a.chunks)
    elif a.what == "icrf3gaia":
        sfx = "" if a.attempt == 1 else f"_attempt{a.attempt}"
        rec = tap_single(a.directory, "D08G", "D08G_icrf3sx_gaia_dr3_counterparts" + sfx, "icrf3sx_gaia_dr3_astrometry.fits",
                         ICRF3_GAIA_ADQL, ICRF3_GAIA_COUNT_ADQL)
    else:
        sfx = "" if a.attempt == 1 else f"_attempt{a.attempt}"
        rec = tap_product(a.directory, "D10S", "D10S_gaia_crf3_xm_flags" + sfx, "gaia_crf3_xm_flags_astrometry.fits",
                          D10S_ADQL, D10S_COUNT_ADQL, "x", a.chunks)
    print(json.dumps({k: rec[k] for k in ("id", "name", "rows", "sha256", "status")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
