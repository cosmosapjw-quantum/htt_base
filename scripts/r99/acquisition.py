"""R99 bounded source intake and independent LoTSS outer geometric exposure.

Only metadata, small provider documentation, and bounded catalogue prefixes are
retrieved. Product jobs are dry-run plans; this module has no bulk downloader or
tape-staging operation. Scientific input files and R78/R98 evidence are untouched.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import healpy as hp
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research_program/observational_publication_20261015/R99_FIFTH_BLOCKER_RESOLUTION_20261123"
INPUTS = OUT / "inputs"
CACHE = Path("/home/cosmosapjw/Downloads/htt_r99")
R98_CACHE = Path("/home/cosmosapjw/Downloads/htt_r98_full_data")
R98 = ROOT / "docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123"
SOURCE_BASELINE = "eee33d7ed33e1af10d7c6a3c453810ecb227e461"
RADIO_MAP_SHA = "989a0f9a6d5c30b4c2468bf2d159d8b644b137e654104e32714a58201e68f6bd"
RADIO_RECEIPT_SHA = "156bf2dd62acbadba451d55738a2673a39085b24e1c77e765eb2300541649398"
MOSAIC_SHA = "8671fa69f744a32f71904a2cc89919a3cf1021d7d030816d0adb218b34227572"
R89_READER = ROOT / "docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G04_RADIO_FRAME/run_g04_solver_free_research.py"
MOSAIC_QUERY = (
    "SELECT mosaic_id,centeralpha,centerdelta,coverage,wcs_projection,"
    "wcs_refpixel,wcs_refvalues,wcs_cdmatrix,pixelsize,record_id,md5,"
    "accsize,related_products FROM lotss_dr3.mosaics"
)
MOSAIC_URL = "https://vo.astron.nl/tap/sync?" + urlencode(
    dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", MAXREC=10000, QUERY=MOSAIC_QUERY)
)
ZENODO = "https://zenodo.org/api/records/6824749"
SOURCES = {
    "sdss_record.json": (ZENODO, 100_000, "metadata"),
    "sdss_data_description.pdf": (ZENODO + "/files/data_description.pdf/content", 100_000, "documentation"),
    "sdss_mock_description.pdf": (ZENODO + "/files/mock_description.pdf/content", 100_000, "documentation"),
    "sdss_pv_prefix.txt": (ZENODO + "/files/SDSS_PV_public.dat/content", 8192, "prefix"),
    "sdss_random_prefix.txt": (ZENODO + "/files/SDSS_randoms_public.dat/content", 1024, "prefix"),
    "sixdf_release.html": ("https://www.mso.anu.edu.au/6dfgs/vfield/3dvfield.html", 50_000, "metadata"),
    "sixdf_table1_prefix.txt": ("https://www.mso.anu.edu.au/6dfgs/vfield/table1.txt", 8192, "prefix"),
    "sixdf_mock_index.html": ("https://www.mso.anu.edu.au/6dfgs/mocks/", 50_000, "metadata"),
    "lotss_mosaics.csv": (MOSAIC_URL, 2_000_000, "metadata"),
    "lotss_mosaic_schema.csv": ("https://vo.astron.nl/tap/sync?" + urlencode(
        dict(REQUEST="doQuery", LANG="ADQL", FORMAT="csv", QUERY=
             "SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='lotss_dr3.mosaics'")
    ), 30_000, "metadata"),
    "lotss_hp1078.json": ("https://repository.surf.nl/api/records/zxsna-nk223", 80_000, "metadata"),
    "lotss_hp355.json": ("https://repository.surf.nl/api/records/9syjm-kpz72", 80_000, "metadata"),
    "lotss_hp264_datalink.xml": (
        "https://vo.astron.nl/lotss_dr3/q/dlmosaic/dlmeta?"
        "ID=ivo%3A%2F%2Fastron.nl%2F~%3FLoTSS-DR3%2FHP-264", 30_000, "metadata"),
}
# These are actual R2 observations, not fresh availability promises. No signed
# redirect URL is retained. HTTP HEAD did not read any science payload.
PRIOR_HTTP_OBSERVATIONS = [
    dict(id="lotss_aux_1078", method="HEAD", http_status=202,
         content_type="application/json", response_bytes=349,
         observation="R99 R2, 2026-11-23; remote process 3846847",
         explicit_staging_request_sent=False,
         status="DEFERRED_HTTP_202", whole_product_hash_verified=False),
    dict(id="lotss_aux_355", method="HEAD", http_status=200,
         content_type="application/octet-stream", content_length=6025820160,
         accept_ranges="bytes",
         observation="R99 R2, 2026-11-23; remote process 3846847",
         page_online_labels=3, status="ONLINE_AT_HEAD_OBSERVATION",
         whole_product_hash_verified=False),
    dict(id="sixdf_reconstruction_mocks", method="HEAD", http_status=200,
         content_length=17344070928, accept_ranges="bytes",
         last_modified="Thu, 08 Mar 2018 00:13:45 GMT",
         observation="R99 R2, 2026-11-23; remote process 3847596",
         whole_product_hash_verified=False),
]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(2**20), b""):
            h.update(b)
    return h.hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


class DeferredProduct(RuntimeError):
    pass


def validate_product_response(status, headers, expected_bytes, *, start=None, count=None):
    """Validate an eventual science transfer response, without making a request.

    In particular HTTP 202 JSON is not a file. A future downloader must stop and
    retain deferred state; this function does not request tape staging.
    """
    h = {k.lower(): str(v) for k, v in headers.items()}
    if status == 202:
        raise DeferredProduct("HTTP 202 is deferred availability, not science payload")
    if any(t in h.get("content-type", "").lower() for t in ("json", "html", "xml")):
        raise ValueError("non-scientific response content type")
    if start is None:
        if status != 200 or int(h.get("content-length", -1)) != int(expected_bytes):
            raise ValueError("full-response status/size mismatch")
    else:
        if count is None or start < 0 or count <= 0 or start + count > expected_bytes:
            raise ValueError("invalid requested byte interval")
        wanted = f"bytes {start}-{start + count - 1}/{expected_bytes}"
        if status != 206 or h.get("content-range") != wanted:
            raise ValueError("Range must be honored exactly before resuming")
        if int(h.get("content-length", -1)) != count:
            raise ValueError("partial-response size mismatch")
    return True


def exact_identifier(token):
    """Parse an explicitly integral decimal lexeme without an IEEE-754 roundtrip."""
    if isinstance(token, (float, np.floating)):
        raise ValueError("IDs must arrive as string/integer, never floating point")
    try:
        d = Decimal(str(token))
    except InvalidOperation as exc:
        raise ValueError("invalid identifier") from exc
    if not d.is_finite() or d != d.to_integral_value() or d < 0:
        raise ValueError("identifier is not a nonnegative integer")
    return int(d)


def mock_genealogy(filename):
    """Keep box identity distinct from its eight observer viewpoints."""
    m = re.search(r"R19(\d{3})\.([0-7])_err_corr(?:$|[.])", Path(filename).name)
    if m is None:
        raise ValueError("filename does not have the documented SDSS box/observer syntax")
    return {"simulation_box": int(m.group(1)), "observer": int(m.group(2)),
            "independent_holdout_group": f"box:{m.group(1)}"}


def capture_sources():
    """Persist the exact small source responses; reuse already hashed snapshots."""
    INPUTS.mkdir(parents=True, exist_ok=True)
    receipt_path = INPUTS / "source_receipts.json"
    receipts = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    for name, (url, cap, kind) in SOURCES.items():
        path = INPUTS / name
        if name in receipts and path.exists():
            if sha(path) != receipts[name]["sha256"]:
                raise ValueError(f"saved source bytes changed: {name}")
            continue
        headers = {"User-Agent": "htt-r99-metadata/1", "Accept-Encoding": "identity"}
        if kind == "prefix":
            headers["Range"] = f"bytes=0-{cap - 1}"
        before = utc()
        with urlopen(Request(url, headers=headers), timeout=25) as response:
            status = response.status
            if status == 202:
                raise DeferredProduct(f"metadata request unexpectedly deferred: {name}")
            if status not in ((200, 206) if kind == "prefix" else (200,)):
                raise ValueError(f"unexpected metadata status {status}: {name}")
            body = response.read(cap if kind == "prefix" else cap + 1)
            if kind != "prefix" and len(body) > cap:
                raise ValueError(f"metadata cap exceeded: {name}")
            rh = {k.lower(): v for k, v in response.headers.items()}
            if kind == "prefix" and status == 206:
                cr = re.fullmatch(r"bytes 0-(\d+)/(\d+)", rh.get("content-range", ""))
                if not cr or int(cr.group(1)) != cap - 1 or len(body) != cap:
                    raise ValueError(f"wrong prefix Content-Range: {name}")
            # Retain stable source URL only; provider redirect may be signed.
            metadata = {
                "url": url, "http_status": status, "fetched_at_utc": before,
                "bytes_read": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                "kind": kind, "full_science_payload": False,
                "headers": {k: rh[k] for k in ("content-type", "content-length",
                    "content-range", "etag", "last-modified", "accept-ranges") if k in rh},
            }
        path.write_bytes(body)
        receipts[name] = metadata
        write_json(receipt_path, receipts)
        print("CAPTURED", name, len(body), status, flush=True)
    return receipts


def _job(job_id, url, size, checksum, purpose, status="PREPARED_MANIFEST_ONLY", **extra):
    p = urlparse(url)
    if p.scheme != "https" or "X-Amz-" in url or "token=" in url:
        raise ValueError("use a stable public HTTPS source URL")
    return dict(id=job_id, url=url, expected_bytes=int(size), checksum=checksum,
                purpose=purpose, status=status, full_payload_downloaded=False,
                full_payload_hash_verified=False, **extra)


def build_plan():
    record = json.loads((INPUTS / "sdss_record.json").read_text())
    if record["metadata"]["version"] != "1.1.0":
        raise ValueError("SDSS version changed; inspect before use")
    fs = {x["key"]: x for x in record["files"]}
    jobs = []
    for name, jid, purpose in [
        ("SDSS_PV_public.dat", "sdss_pv_v1_1", "Upstream SDSS FP/log-distance subset before CF4 intercalibration"),
        ("SDSS_randoms_public.dat", "sdss_randoms_v1_1", "SDSS-only angular/radial selection and clustering reference"),
        ("mocks.tar.gz", "sdss_mocks_v1_1", "256 simulation boxes with 8 observers each; hold out by box"),
    ]:
        f = fs[name]
        jobs.append(_job(jid, f["links"]["self"], f["size"], f["checksum"], purpose,
                         "PREFIX_HTTP_206_PREPARED" if jid != "sdss_mocks_v1_1" else "PREPARED_MANIFEST_ONLY",
                         release="10.5281/zenodo.6824749 v1.1.0"))
    receipts = json.loads((INPUTS / "source_receipts.json").read_text())
    h = receipts["sixdf_table1_prefix.txt"]["headers"]
    total = int(h["content-range"].split("/")[-1])
    jobs.append(_job("sixdf_pv_table1", SOURCES["sixdf_table1_prefix.txt"][0], total, None,
                     "6dFGSv log-distance ratio/error/skew, galaxy/group CMB cz; raw FP and full selection are separate",
                     "PREFIX_HTTP_206_PREPARED", source_checksum_available=False))
    jobs.append(_job("sixdf_reconstruction_mocks",
        "https://www.mso.anu.edu.au/6dfgs/mocks/6dFGSRecon_Files.tar.gz", 17344070928, None,
        "Public reconstruction mocks; internal content and PV/FP matching NOT YET QUALIFIED",
        "HEAD_200_PREPARED_UNQUALIFIED_CONTENT", source_checksum_available=False))
    for n, rec in [(1078, "zxsna-nk223"), (355, "9syjm-kpz72")]:
        d = json.loads((INPUTS / f"lotss_hp{n}.json").read_text())
        f = d["files"]["entries"][f"HP-misc-{n}.tar"]
        jobs.append(_job(f"lotss_aux_{n}", f["links"]["content"], f["size"], f["checksum"],
            "PyBDSF source mask/model/residual/RMS and high/low resolution mosaic weights",
            "DEFERRED_HTTP_202" if n == 1078 else "HEAD_200_AT_R2_PREPARED",
            record_id=rec, metadata_storage_class=f.get("storage_class"),
            internal_archive_names_verified=False, availability_requires_fresh_check=True))
    # Reuse the R98 exact product allowlist rather than inventing a new release.
    from scripts.r98.acquisition_preflight import archive_job
    cmd = archive_job("dx12_v3_commander_noise_mc_00000_raw.fits")
    jobs.append(_job("commander_pr3_ffp10_noise_00000", cmd["url"], cmd["bytes"], None,
        "Match existing PR3/FFP10 Commander fullmission signal ID00000; no PR4/NPIPE substitution",
        "R98_HEADER_VERIFIED_PREPARED", release="Planck PR3/FFP10 dx12_v3 Commander fullmission",
        source_checksum_available=False, full_null_qualified=False))
    plan = {
        "schema": "htt.r99.acquisition_plan/1", "source_baseline": SOURCE_BASELINE,
        "owner": "obsstat", "claim_tier": "C1", "status": "PREPARATION_ONLY",
        "transfer_source": "none",
        "user_scope": "download preparation; no full science payload or tape staging",
        "metadata_snapshot_sha256": {n: r["sha256"] for n, r in receipts.items()},
        "jobs": jobs, "prior_http_observations": PRIOR_HTTP_OBSERVATIONS,
        "producer_path": str(Path(__file__).resolve()), "producer_sha256": sha(__file__),
        "reused_commander_allowlist_path": str(ROOT / "scripts/r98/acquisition_preflight.py"),
        "reused_commander_allowlist_sha256": sha(ROOT / "scripts/r98/acquisition_preflight.py"),
        "suggested_bounded_first_subset": ["sdss_pv_v1_1", "sixdf_pv_table1"],
        "suggested_subset_expected_bytes": fs["SDSS_PV_public.dat"]["size"] + total,
        "budgets": {"metadata_max_bytes_per_response": 2_000_000,
                    "maximum_concurrent_product_jobs": 1, "threads": 1,
                    "full_science_payload_bytes_executed_this_module": 0,
                    "saved_science_prefix_bytes": sum(r["bytes_read"] for r in receipts.values() if r["kind"] == "prefix"),
                    "saved_source_response_bytes": sum(r["bytes_read"] for r in receipts.values()),
                    "dry_run_requires_explicit_ids_and_byte_budget": True},
        "scientific_obligations": [
            "SDSS logdist_corr zero point must be calibrated at group level, not independent galaxies",
            "SDSS mean/std with skew are not skew-normal location/scale parameters",
            "CF4 joint seven-method upstream calibration remains unavailable from these products alone",
            "SDSS randoms/weights are not the union CF4 selection denominator",
            "Mock observations in the same simulation box are not independent holdout groups",
            "LoTSS polygon is outer geometry only; valid weight/RMS holes and completeness remain",
            "Commander one pair does not calibrate a matched joint null",
        ],
    }
    write_json(OUT / "ACQUISITION_PLAN.json", plan)
    return plan


def select_jobs(plan, ids, max_bytes):
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("specify a nonempty unique subset of job IDs")
    lookup = {j["id"]: j for j in plan["jobs"]}
    if any(x not in lookup for x in ids):
        raise ValueError("unknown product job ID")
    jobs = [lookup[x] for x in ids]
    total = sum(j["expected_bytes"] for j in jobs)
    if max_bytes < total:
        raise ValueError(f"explicit product budget {max_bytes} < required {total} bytes")
    deferred = [j["id"] for j in jobs if j["status"].startswith("DEFERRED")]
    return dict(mode="DRY_RUN_ONLY", selected_ids=ids, expected_bytes=total,
                max_bytes=max_bytes, deferred_ids=deferred,
                ready_for_explicit_future_fetch=not deferred,
                downloaded_bytes=0, stable_urls=[j["url"] for j in jobs])


def polygon_vectors(coverage):
    vals = np.fromstring(coverage.strip().strip("[]"), sep=" ")
    if vals.size != 8 or not np.all(np.isfinite(vals)):
        raise ValueError("expected four finite RA/Dec coverage corners")
    a = vals.reshape(4, 2)
    if np.any(np.abs(a[:, 1]) > 90):
        raise ValueError("invalid coverage declination")
    return np.asarray(hp.ang2vec(np.mod(a[:, 0], 360), a[:, 1], lonlat=True))


def load_polygons(path):
    with Path(path).open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or len({r["mosaic_id"] for r in rows}) != len(rows):
        raise ValueError("missing/duplicated mosaic IDs")
    return rows, [polygon_vectors(r["coverage"]) for r in rows]


def polygon_union(polygons, nside):
    """Union of convex great-circle polygons, using HEALPix center inclusion."""
    if not hp.isnsideok(nside, nest=True):
        raise ValueError("nested NSIDE must be a positive power of two")
    mask = np.zeros(hp.nside2npix(nside), dtype=bool)
    for i, p in enumerate(polygons):
        p = np.asarray(p, float)
        if p.ndim != 2 or p.shape[1] != 3 or len(p) < 3 or not np.all(np.isfinite(p)):
            raise ValueError(f"invalid polygon {i}")
        norm = np.linalg.norm(p, axis=1)
        if np.any(norm <= 0):
            raise ValueError("zero polygon vertex")
        p = p / norm[:, None]
        mask[hp.query_polygon(nside, p, nest=True, inclusive=False)] = True
    return mask


def aggregate_exposure(mask_nested, fine_nside, target_nside):
    if fine_nside < target_nside or fine_nside % target_nside or not hp.isnsideok(target_nside, nest=True):
        raise ValueError("target NSIDE must divide the finer nested NSIDE")
    x = np.asarray(mask_nested)
    if x.dtype != bool or x.shape != (hp.nside2npix(fine_nside),):
        raise ValueError("wrong fine mask dtype/shape")
    factor = (fine_nside // target_nside) ** 2
    f_nested = x.reshape(hp.nside2npix(target_nside), factor).mean(axis=1)
    return hp.reorder(f_nested, n2r=True)


def independent_union_membership(polygons, directions):
    """Independent spherical halfspace test; no HEALPix polygon query."""
    v = np.asarray(directions, float)
    inside = np.zeros(len(v), bool)
    for p in polygons:
        p = np.asarray(p)
        edges = np.cross(p, np.roll(p, -1, axis=0))
        center = p.sum(axis=0)
        orientation = np.sign(edges @ center)
        if np.any(orientation == 0):
            raise ValueError("degenerate polygon orientation")
        normals = edges * orientation[:, None]
        inside |= np.all(v @ normals.T >= -2e-14, axis=1)
    return inside


def count_offset(fraction, nside, counts=None):
    """Known geometric offset: mu_p = Omega_p f_p exp(X_p beta)."""
    f = np.asarray(fraction, float)
    if f.shape != (hp.nside2npix(nside),) or np.any(~np.isfinite(f)) or np.any((f < 0) | (f > 1)):
        raise ValueError("invalid exposure fraction")
    area = hp.nside2pixarea(nside) * f
    support = area > 0
    if counts is not None:
        c = np.asarray(counts)
        if c.shape != f.shape or np.any(~np.isfinite(c)) or np.any(c < 0):
            raise ValueError("invalid source counts")
        if np.any((c > 0) & ~support):
            raise ValueError("positive counts outside supplied geometric support")
    offset = np.full_like(f, -np.inf)
    offset[support] = np.log(area[support])
    return area, offset, support


def locked_radio_cache():
    mp = R98_CACHE / "radio_full_maps.npz"
    rp = R98_CACHE / "radio_full_maps_sources.json"
    fp = R98_CACHE / "radio_full_maps_fingerprints.json"
    seal = json.loads(fp.read_text())
    source_receipt = json.loads(rp.read_text())
    if sha(R89_READER) != source_receipt["reader_sha256"]:
        raise ValueError("R89 source reader changed since cached maps were built")
    if sha(mp) != RADIO_MAP_SHA or sha(rp) != RADIO_RECEIPT_SHA:
        raise ValueError("R98 cached map/source receipt identity changed")
    if seal["maps_sha256"] != RADIO_MAP_SHA or seal["receipt_sha256"] != RADIO_RECEIPT_SHA:
        raise ValueError("R98 cache seal binding changed")
    for path, recorded in seal["fingerprints"].items():
        s = Path(path).stat()
        if dict(bytes=s.st_size, mtime_ns=s.st_mtime_ns, inode=s.st_ino) != recorded:
            raise ValueError(f"R98 source storage identity changed: {path}")
    with np.load(mp, allow_pickle=False) as data:
        counts = {float(k.split("__")[-1]): data[k].copy()
                  for k in data.files if k.startswith("map__LoTSS_DR3__")}
        old_mask = data["mask__LoTSS_DR3_int1500"].astype(bool)
    return counts, old_mask, {
        "maps_path": str(mp), "maps_sha256": RADIO_MAP_SHA,
        "source_receipt_path": str(rp), "source_receipt_sha256": RADIO_RECEIPT_SHA,
        "fingerprint_path": str(fp), "fingerprint_sha256": sha(fp),
        "reader_path": str(R89_READER), "reader_sha256": source_receipt["reader_sha256"],
        "source_verification": "inherited full hashes plus unchanged storage fingerprints; no raw rescan",
    }


def run_footprint(fine_nsides=(64, 128, 256), target_nside=16):
    t = time.perf_counter()
    if list(fine_nsides) != sorted(set(fine_nsides)) or len(fine_nsides) < 2:
        raise ValueError("need at least two strictly increasing fine NSIDEs")
    if target_nside != 16:
        raise ValueError("R98 source counts are fixed at NSIDE16; aggregate to target_nside=16")
    csv_path = INPUTS / "lotss_mosaics.csv"
    if sha(csv_path) != MOSAIC_SHA:
        raise ValueError("mosaic snapshot differs from R99 inspected source; review the new census")
    rows, polygons = load_polygons(csv_path)
    if len(rows) != 1580:
        raise ValueError("mosaic census changed from the inspected R2 1580; inspect the new release")
    CACHE.mkdir(parents=True, exist_ok=True)
    counts, old_mask, old_provenance = locked_radio_cache()
    arrays, summaries, previous = {}, [], None
    for ns in fine_nsides:
        before = time.perf_counter()
        union = polygon_union(polygons, ns)
        fraction = aggregate_exposure(union, ns, target_nside)
        mask_path = CACHE / f"lotss_outer_union_nside{ns}_nested.npy"
        np.save(mask_path, union, allow_pickle=False)
        sample = np.random.default_rng(9905).choice(len(union), min(4096, len(union)), replace=False)
        vectors = np.asarray(hp.pix2vec(ns, sample, nest=True)).T
        direct = independent_union_membership(polygons, vectors)
        mismatches = int(np.count_nonzero(direct != union[sample]))
        if mismatches:
            raise ArithmeticError(f"independent spherical membership mismatch at NSIDE {ns}: {mismatches}")
        area, offset, support = count_offset(fraction, target_nside)
        arrays[f"fraction_fine{ns}"] = fraction
        summary = dict(fine_nside=int(ns), area_sr=float(area.sum()),
            area_square_deg=float(area.sum() * (180 / np.pi)**2),
            fsky=float(area.sum() / (4 * np.pi)),
            nonzero_target_cells=int(support.sum()),
            fractional_target_cells=int(np.count_nonzero((fraction > 0) & (fraction < 1))),
            nested_union_path=str(mask_path), nested_union_sha256=sha(mask_path),
            independent_sampled_centers=len(sample), independent_membership_mismatches=mismatches,
            runtime_seconds=time.perf_counter() - before)
        if previous is not None:
            delta = fraction - previous
            summary.update(
                refinement_area_change_sr=float(delta.sum() * hp.nside2pixarea(target_nside)),
                refinement_l1_area_change_sr=float(np.abs(delta).sum() * hp.nside2pixarea(target_nside)),
                refinement_max_cell_fraction_change=float(np.max(np.abs(delta))))
        summaries.append(summary)
        previous = fraction
        print("FOOTPRINT", ns, summary["area_square_deg"], summary["nonzero_target_cells"], flush=True)
    best = previous
    area, offset, support = count_offset(best, target_nside)
    arrays.update(fraction=best, exposure_sr=area, log_exposure_sr=offset,
                  support=support, original_density_mask=old_mask,
                  target_nside=np.array(target_nside), fine_nside=np.array(fine_nsides[-1]))
    comparisons = {}
    for cut, c in counts.items():
        arrays[f"counts_flux{cut:g}mJy"] = c
        comparisons[str(cut)] = dict(
            total_cached_sources=int(c.sum()), occupied_cached_cells=int(np.count_nonzero(c)),
            sources_inside_outer_support=int(c[support].sum()),
            positive_count_cells_outside_outer_support=int(np.count_nonzero((c > 0) & ~support)),
            sources_outside_outer_support=int(c[~support].sum()),
            observed_zero_cells_inside_outer_support=int(np.count_nonzero(support & (c == 0))),
            sources_on_old_mask=int(c[old_mask].sum()),
            sources_on_outer_support_excluded_by_old_mask=int(c[support & ~old_mask].sum()),
            supports_future_count_offset=not bool(np.any((c > 0) & ~support)))
    npz = INPUTS / f"lotss_outer_exposure_nside{target_nside}.npz"
    np.savez_compressed(npz, **arrays)
    result = {
        "schema": "htt.r99.lotss_outer_exposure/1", "owner": "obsstat",
        "claim_tier": "C1", "status": "IMPLEMENTATION_VERIFIED_GEOMETRIC_PREPARATION",
        "transfer_source": "none", "source_baseline": SOURCE_BASELINE,
        "csv_path": str(csv_path), "csv_sha256": sha(csv_path),
        "mosaic_count": len(rows), "frame": "ICRS", "output_ordering": "RING",
        "target_nside": target_nside, "fine_nsides": list(fine_nsides),
        "polygon_interpretation": "great-circle edges between official four image corners; outer image support",
        "overlap_handling": "Boolean union, no sum of repeat sky",
        "rasterization": "fine nested HEALPix pixel-center inclusion; equal-area child average, then RING",
        "resolution_checks": summaries, "original_cache": old_provenance,
        "comparison_to_original_density_mask": {
            "old_mask_name": "LoTSS_DR3_int1500",
            "old_mask_cells": int(old_mask.sum()),
            "old_mask_cells_with_zero_outer_fraction": int(np.count_nonzero(old_mask & ~support)),
            "outer_cells_not_in_old_mask": int(np.count_nonzero(support & ~old_mask)),
            "minimum_outer_fraction_inside_old_mask": float(best[old_mask].min()),
            "old_mask_uses_density_cut": True,
            "old_mask_also_includes_galactic_NHI_cuts": True,
        },
        "counts_comparison": comparisons,
        "output_npz": str(npz), "output_npz_sha256": sha(npz),
        "likelihood_offset": "mu_p=exposure_sr[p]*exp(X_p beta); additive log_exposure_sr, no fitted offset coefficient",
        "caveats": [
            "Outer mosaic rectangle may contain valid-weight holes; not a completed RMS footprint",
            "Source-size/flux completeness, association, SED and LSS models remain",
            "Different fine NSIDE compares boundary discretization only, not these systematic errors",
            "Count comparison uses existing all-sky cut maps, without rescanning catalogue rows",
            "No cosmological null, p-value, physical Pi or GF is produced",
        ],
        "physical_Pi": None, "runtime_seconds": time.perf_counter() - t,
        "producer_path": str(Path(__file__).resolve()), "producer_sha256": sha(__file__),
        "python_version": sys.version.split()[0], "numpy_version": np.__version__,
        "healpy_version": hp.__version__,
        "thread_environment": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "finished_at_utc": utc(),
    }
    write_json(OUT / "ACQUISITION_RESULTS.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "footprint", "all", "plan"))
    parser.add_argument("--ids", nargs="+")
    parser.add_argument("--max-bytes", type=int, default=0)
    parser.add_argument("--fine-nsides", nargs="+", type=int, default=[64, 128, 256])
    parser.add_argument("--target-nside", type=int, default=16)
    args = parser.parse_args(argv)
    if args.mode in ("prepare", "all"):
        capture_sources()
        p = build_plan()
        print(json.dumps({"prepared_jobs": len(p["jobs"]), "full_science_bytes_downloaded": 0}))
    if args.mode in ("footprint", "all"):
        result = run_footprint(tuple(args.fine_nsides), args.target_nside)
        print(json.dumps({"output": result["output_npz"], "sha256": result["output_npz_sha256"]}))
    if args.mode == "plan":
        p = json.loads((OUT / "ACQUISITION_PLAN.json").read_text())
        selection = select_jobs(p, args.ids, args.max_bytes)
        print(json.dumps(selection, indent=2))


if __name__ == "__main__":
    main()
