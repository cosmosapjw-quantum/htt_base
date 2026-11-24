"""R108 A6 SQ-FRAME: build the catalogue frame registry (positions, epochs, redshift frames, velocity references).

Purpose
    For each catalogue release used in R98-R106 record the position frame, epoch/equinox,
    redshift frame(s) and the velocity reference with a locator, and recover from the
    release itself the frame velocity it used where the release carries the same objects
    in two velocity frames (CF4 table4 Vh/Vls/V3k; CF3 table3 HV/Vls/Vgsr/Vcmb; 6dFGSv
    czgal versus 6dFGS DR3 cz). Writes the registry consumed by
    htt/obsstat/catalogue_frame_registry.py.

Inputs (SHA-256 recorded at run time in the output JSON)
    local  /mnt/extdrive/workdir/raw/cf4_full/{ReadMe,table4.dat}            (J/ApJ/944/94)
    local  /mnt/extdrive/workdir/raw/new_acquisitions/optical/6dFGS_final/{ReadMe,6dfgs.dat.gz} (VII/259)
    local  ~/Downloads/htt_r100/source_intake/table1.txt                    (6dFGSv table 1)
    local  /mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/NVSS/ReadMe   (VIII/65)
    local  /mnt/extdrive/workdir/raw/icrf3_iers_20261110/icrf3sx.txt         (IERS ICRF3 S/X)
    local  /mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-commander_2048_R3.00_full.fits (header only)
    local  /mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/quaia_G20.0.fits (header only)
    remote astroquery.vizier (server vizier.cfa.harvard.edu): VOTable metadata of each VizieR table,
           and a column-limited full read of J/AJ/152/50/table3 (CF3 velocities)
    remote pyvo TAP https://gea.esac.esa.int/tap-server/tap (Gaia DR3 TAP_SCHEMA) and
           astroquery.gaia (ref_epoch rows); pyvo TAP https://casda.csiro.au/casda_vo_tools/tap (RACS)
    Every remote result is saved under ~/Downloads/htt_r108/frame/<source>/ with a line in
    ~/Downloads/htt_r108/frame/RECEIPTS.jsonl (service URL, query, job id, rows, SHA-256).
    --replay-receipts re-parses the saved remote results named by RECEIPTS.jsonl instead of fetching
    (SHA-256 of every saved file verified against its receipt; a call with no successful receipt replays
    as the recorded failure). Every local input gets a 'pre_existing_input' receipt line
    (scripts/r108/frame_input_receipts.py; idempotent).

Units
    velocities km/s; beta dimensionless (units of c), Galactic Cartesian; angles deg.

Usage (repo root; downloaded files are parsed only, never executed)
    PYTHONPATH=.:htt:htt/src .venv/bin/python -m scripts.r108.frame_registry_build \
        --downloads ~/Downloads/htt_r108/frame [--replay-receipts] \
        --output docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/FRAME/CATALOGUE_FRAME_REGISTRY.json
    No random numbers are drawn.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import io
import json
import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np

from obsstat import publication_frame_kinematics as pfk
from obsstat.catalogue_frame_registry import (
    C_KM_S, CatalogueRelease, FrameRegistry, VelocityReference, galactic_unit_vector,
    planck2018_solar_dipole_reference,
)
from scripts.r108.common import OUT_DIR, REPO, git_state, sha256_file, write_json

HOME = Path.home()
CF4_DIR = Path("/mnt/extdrive/workdir/raw/cf4_full")
SIXDF_DR3_DIR = Path("/mnt/extdrive/workdir/raw/new_acquisitions/optical/6dFGS_final")
SIXDFV_TABLE1 = HOME / "Downloads/htt_r100/source_intake/table1.txt"
NVSS_README = Path("/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/NVSS/ReadMe")
ICRF3_SX = Path("/mnt/extdrive/workdir/raw/icrf3_iers_20261110/icrf3sx.txt")
COMMANDER = Path("/mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-commander_2048_R3.00_full.fits")
QUAIA = Path("/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/quaia_G20.0.fits")
VIZIER_SERVER = "vizier.cfa.harvard.edu"
GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap"
CASDA_TAP = "https://casda.csiro.au/casda_vo_tools/tap"
OUTFILE = OUT_DIR / "FRAME/CATALOGUE_FRAME_REGISTRY.json"
CODE = ("scripts/r108/frame_registry_build.py", "scripts/r108/frame_input_receipts.py", "scripts/r108/common.py",
        "htt/obsstat/catalogue_frame_registry.py", "htt/obsstat/publication_frame_kinematics.py")
NO_UNMEASURED_BETA_RULE = (
    "every frame change names a registered VelocityReference key (never a raw velocity) and the release whose data it "
    "transforms (required release_id; FrameRegistry.conversion_reference). The release must have conversion_status "
    "'registered', and the key must be one of its own references, or the own reference of another registered release "
    "whose input frame (moving frame for *_to_rest, rest frame for *_to_moving) is a frame the data release states. "
    "Every transformation that names a release with conversion_status beta_not_stated or not_applicable, or an "
    "unregistered release, raises UnmeasuredBetaError. A reference is admitted with status published, "
    "recovered_from_release or measured_repository_estimate and a locator of at least 8 characters; the registry "
    "does not verify the locator's content.")


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------------------
# Frame-velocity recovery (pure functions, unit tested)
# --------------------------------------------------------------------------------------
def predict_to(v_from_kms: np.ndarray, n: np.ndarray, beta: np.ndarray, formula: str) -> np.ndarray:
    """Velocity cz in the target frame from cz in the source frame (n measured in source frame)."""
    z = np.asarray(v_from_kms, float) / C_KM_S
    bn = n @ beta
    if formula == "linear_cz_sum":
        return C_KM_S * (z + bn)
    g = pfk.gamma(beta)
    return C_KM_S * ((1.0 + z) / (g * (1.0 - bn)) - 1.0)


def fit_frame_velocity(v_from_kms, v_to_kms, n, formula: str = "exact_relativistic",
                       clip_kms: float = 10.0, iterations: int = 6) -> dict:
    """Least-squares frame velocity beta with v_to = F(v_from, n; beta).

    Starts from the linear solution, iterates Gauss-Newton (numerical Jacobian),
    clips |residual| > clip_kms once the fit has converged on the bulk of the rows,
    and reports residual statistics. Integer-rounded catalogue columns give
    residuals of order 0.4 km/s when the model is the one the release used.
    """
    v_from = np.asarray(v_from_kms, float)
    v_to = np.asarray(v_to_kms, float)
    n = np.asarray(n, float)
    if n.ndim != 2 or n.shape != (len(v_from), 3) or v_to.shape != v_from.shape:
        raise ValueError("shape mismatch")
    keep = np.isfinite(v_from) & np.isfinite(v_to) & np.isfinite(n).all(axis=1)
    beta = np.linalg.lstsq(n[keep], (v_to[keep] - v_from[keep]) / C_KM_S, rcond=None)[0]
    for _ in range(iterations):
        r = v_to - predict_to(v_from, n, beta, formula)
        mask = keep & (np.abs(r) <= max(clip_kms, 5 * np.std(r[keep])) if _ == 0 else keep & (np.abs(r) <= clip_kms))
        J = np.empty((int(mask.sum()), 3))
        h = 1e-9
        base = predict_to(v_from[mask], n[mask], beta, formula)
        for k in range(3):
            e = np.zeros(3); e[k] = h
            J[:, k] = (predict_to(v_from[mask], n[mask], beta + e, formula) - base) / h
        step = np.linalg.lstsq(J, v_to[mask] - base, rcond=None)[0]
        beta = beta + step
        if np.max(abs(step)) < 1e-15:
            break
    r = v_to - predict_to(v_from, n, beta, formula)
    mask = keep & (np.abs(r) <= clip_kms)
    J = np.empty((int(mask.sum()), 3))
    base = predict_to(v_from[mask], n[mask], beta, formula)
    for k in range(3):
        e = np.zeros(3); e[k] = 1e-9
        J[:, k] = (predict_to(v_from[mask], n[mask], beta + e, formula) - base) / 1e-9
    dof = max(1, int(mask.sum()) - 3)
    s2 = float(np.sum(r[mask] ** 2) / dof)
    cov = s2 * np.linalg.inv(J.T @ J)
    speed = float(np.linalg.norm(beta)) * C_KM_S
    l = math.degrees(math.atan2(beta[1], beta[0])) % 360.0
    b = math.degrees(math.asin(beta[2] / np.linalg.norm(beta)))
    return {
        "formula": formula, "beta_galactic": beta.tolist(), "covariance_galactic": cov.tolist(),
        "speed_kms": speed, "apex_l_deg": l, "apex_b_deg": b,
        "n_rows": int(keep.sum()), "n_used": int(mask.sum()), "n_clipped": int(keep.sum() - mask.sum()),
        "clip_kms": clip_kms, "residual_rms_kms": float(np.sqrt(np.mean(r[mask] ** 2))),
        "residual_max_abs_kms_used": float(np.max(np.abs(r[mask]))),
        "residual_fraction_le_1kms_all": float(np.mean(np.abs(r[keep]) <= 1.0)),
    }


def best_fit(v_from, v_to, n) -> dict:
    fits = {f: fit_frame_velocity(v_from, v_to, n, formula=f) for f in ("exact_relativistic", "linear_cz_sum")}
    best = min(fits, key=lambda f: (fits[f]["n_clipped"], fits[f]["residual_rms_kms"]))
    return {"fits": fits, "selected_formula": best}


# --------------------------------------------------------------------------------------
# Remote access (astroquery / pyvo) with receipts
# --------------------------------------------------------------------------------------
class Receipts:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = root / "RECEIPTS.jsonl"
        self.rows: list[dict] = []

    def add(self, **kw) -> dict:
        kw.setdefault("fetched_at_utc", now_utc())
        with self.path.open("a") as fh:
            fh.write(json.dumps(kw, sort_keys=True) + "\n")
        self.rows.append(kw)
        return kw


def _new_dir(root: Path, name: str) -> Path:
    d = root / name
    if d.exists():
        k = 2
        while (root / f"{name}_{k}").exists():
            k += 1
        d = root / f"{name}_{k}"
    d.mkdir(parents=True)
    return d


def votable_tables(content: bytes) -> tuple[list[dict], list]:
    """Tables (name, description, rows, COOSYS, fields) and QUERY_STATUS of a VizieR VOTable (parse only)."""
    from astropy.io.votable import parse
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vt = parse(io.BytesIO(content))
    status_info = [(i.name, (i.content or "")[:200]) for i in vt.infos if i.name in ("QUERY_STATUS",)]
    tables = []
    for res in vt.resources:
        coosys = [{"ID": c.ID, "system": c.system, "equinox": c.equinox, "epoch": c.epoch}
                  for c in res.coordinate_systems]
        for t in res.tables:
            tables.append({"name": t.name, "description": t.description, "rows": int(len(t.array)),
                           "coosys": coosys,
                           "fields": [{"name": f.name, "unit": None if f.unit is None else str(f.unit),
                                       "ucd": f.ucd, "description": f.description} for f in t.fields]})
    return tables, status_info


def vizier_votable(receipts: Receipts, root: Path, catalog: str, columns=("**",), row_limit: int = 1,
                   attempts: int = 2) -> dict:
    """astroquery.vizier VOTable fetch on the CfA mirror; raw bytes saved and parsed (parse only)."""
    from astroquery.vizier import Vizier

    slug = "vizier_" + catalog.replace("/", "_").replace("+", "p").replace(".", "_")
    errors = []
    for attempt in range(1, attempts + 1):
        try:
            viz = Vizier(columns=list(columns), row_limit=row_limit, vizier_server=VIZIER_SERVER, timeout=180)
            resp = viz.get_catalogs_async(catalog)
            content = resp.content
            d = _new_dir(root, slug)
            out = d / (slug + ".vot")
            out.write_bytes(content)
            body = resp.request.body
            query = body.decode() if isinstance(body, bytes) else str(body)
            tables, status_info = votable_tables(content)
            nrows = sum(t["rows"] for t in tables)
            rec = receipts.add(id=slug, name=f"astroquery.vizier {catalog}", url=f"https://{VIZIER_SERVER}/viz-bin/votable",
                               final_url=str(resp.url), query=query, job_id=None, rows=nrows,
                               bytes=len(content), sha256=sha_bytes(content), status=int(resp.status_code),
                               saved=str(out), attempt=attempt, query_status=status_info)
            if not tables:
                errors.append(f"attempt {attempt}: no table in VOTable; QUERY_STATUS={status_info}")
                time.sleep(5)
                continue
            return {"ok": True, "catalog": catalog, "tables": tables, "receipt": rec, "path": str(out),
                    "votable_bytes": content}
        except Exception as exc:  # noqa: BLE001 - recorded, never hidden
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {str(exc)[:300]}")
            time.sleep(5)
    receipts.add(id=slug, name=f"astroquery.vizier {catalog}", url=f"https://{VIZIER_SERVER}/viz-bin/votable",
                 final_url=None, bytes=0, sha256=None, status="failed", errors=errors)
    return {"ok": False, "catalog": catalog, "errors": errors}


def pyvo_tap(receipts: Receipts, root: Path, service_url: str, query: str, slug: str, attempts: int = 2) -> dict:
    import pyvo

    errors = []
    for attempt in range(1, attempts + 1):
        job = None
        try:
            svc = pyvo.dal.TAPService(service_url)
            job = svc.submit_job(query, maxrec=1000)
            job.run()
            job.wait(phases=["COMPLETED", "ERROR", "ABORTED"], timeout=300)
            job.raise_if_error()
            res = job.fetch_result()
            d = _new_dir(root, slug)
            out = d / (slug + ".vot")
            res.votable.to_xml(str(out))
            tab = res.to_table()
            rec = receipts.add(id=slug, name=f"pyvo TAP {service_url}", url=service_url, final_url=str(job.url),
                               query=query, job_id=str(job.job_id), rows=int(len(tab)), bytes=out.stat().st_size,
                               sha256=sha256_file(out), status="COMPLETED", saved=str(out), attempt=attempt)
            rows = [{c: (None if np.ma.is_masked(r[c]) else (r[c].item() if hasattr(r[c], "item") else str(r[c])))
                     for c in tab.colnames} for r in tab]
            try:
                job.delete()
            except Exception:  # noqa: BLE001
                pass
            return {"ok": True, "rows": rows, "receipt": rec}
        except Exception as exc:  # noqa: BLE001
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {str(exc)[:300]}")
            time.sleep(5)
    receipts.add(id=slug, name=f"pyvo TAP {service_url}", url=service_url, final_url=None, query=query,
                 bytes=0, sha256=None, status="failed", errors=errors)
    return {"ok": False, "errors": errors}


def gaia_astroquery(receipts: Receipts, root: Path, query: str, slug: str, attempts: int = 2) -> dict:
    errors = []
    for attempt in range(1, attempts + 1):
        try:
            from astroquery.gaia import Gaia
            job = Gaia.launch_job_async(query, dump_to_file=False, verbose=False)
            tab = job.get_results()
            d = _new_dir(root, slug)
            out = d / (slug + ".vot")
            tab.write(str(out), format="votable")
            rec = receipts.add(id=slug, name="astroquery.gaia", url=GAIA_TAP, final_url=str(getattr(job, "remoteLocation", "")),
                               query=query, job_id=str(job.jobid), rows=int(len(tab)), bytes=out.stat().st_size,
                               sha256=sha256_file(out), status="COMPLETED", saved=str(out), attempt=attempt)
            return {"ok": True, "rows": [{c: (r[c].item() if hasattr(r[c], "item") else str(r[c])) for c in tab.colnames}
                                         for r in tab], "receipt": rec}
        except Exception as exc:  # noqa: BLE001
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {str(exc)[:300]}")
            time.sleep(5)
    receipts.add(id=slug, name="astroquery.gaia", url=GAIA_TAP, query=query, bytes=0, sha256=None,
                 status="failed", errors=errors)
    return {"ok": False, "errors": errors}


class ReceiptReplay:
    """Offline replay of earlier remote results from RECEIPTS.jsonl (saved bytes, SHA-256 verified; parse only).

    A call replays the latest receipt with the same service name and query whose saved file verifies and
    parses to at least one table; when none does, it replays the latest recorded failure (its errors).
    """

    def __init__(self, receipts_path: Path):
        self.path = receipts_path
        self.rows = [json.loads(ln) for ln in receipts_path.read_text().splitlines() if ln.strip()]
        self.used: list[dict] = []

    def _remote(self):
        return [r for r in self.rows if not str(r.get("kind", "")).startswith("pre_existing")]

    def _verified_bytes(self, r: dict) -> bytes | None:
        saved = r.get("saved")
        if not saved or not r.get("sha256") or not Path(saved).is_file():
            return None
        b = Path(saved).read_bytes()
        if sha_bytes(b) != r["sha256"]:
            raise ValueError(f"replay: SHA-256 mismatch for {saved} (receipt {r['sha256'][:16]})")
        return b

    def _failure(self, name: str, slug: str) -> dict:
        fails = [r for r in self._remote() if r.get("name") == name and r.get("id") == slug and r.get("status") == "failed"]
        if fails:
            self.used.append(fails[-1])
            return {"ok": False, "errors": fails[-1].get("errors") or ["replay: recorded failure without errors"]}
        return {"ok": False, "errors": [f"replay: no receipt for {name} {slug}"]}

    def vizier(self, catalog: str, columns=("**",), row_limit: int = 1) -> dict:
        name = f"astroquery.vizier {catalog}"
        slug = "vizier_" + catalog.replace("/", "_").replace("+", "p").replace(".", "_")
        cols = [c for c in columns if not c.startswith("_")]
        tokens = [f"-source={catalog}\n", "-out.max=unlimited" if row_limit == -1 else f"-out.max={row_limit}\n",
                  "-out.all" if tuple(columns) == ("**",) else "-out=" + ",".join(cols)]
        cands = [r for r in self._remote() if r.get("name") == name and r.get("status") == 200
                 and all(t in (r.get("query") or "") for t in tokens)]
        for r in reversed(cands):
            content = self._verified_bytes(r)
            if content is None:
                continue
            tables, _ = votable_tables(content)
            if tables:
                self.used.append(r)
                return {"ok": True, "catalog": catalog, "tables": tables, "receipt": r, "path": r["saved"],
                        "votable_bytes": content}
        out = self._failure(name, slug)
        out["catalog"] = catalog
        return out

    def _table_rows(self, r: dict, masked_none: bool) -> list[dict]:
        from astropy.io.votable import parse
        content = self._verified_bytes(r)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tab = parse(io.BytesIO(content)).get_first_table().to_table()
        if masked_none:
            return [{c: (None if np.ma.is_masked(x[c]) else (x[c].item() if hasattr(x[c], "item") else str(x[c])))
                     for c in tab.colnames} for x in tab]
        return [{c: (x[c].item() if hasattr(x[c], "item") else str(x[c])) for c in tab.colnames} for x in tab]

    def tap(self, service_url: str, query: str, slug: str) -> dict:
        name = f"pyvo TAP {service_url}"
        cands = [r for r in self._remote() if r.get("name") == name and r.get("id") == slug
                 and r.get("query") == query and r.get("status") == "COMPLETED"]
        if cands:
            self.used.append(cands[-1])
            return {"ok": True, "rows": self._table_rows(cands[-1], masked_none=True), "receipt": cands[-1]}
        return self._failure(name, slug)

    def gaia(self, query: str, slug: str) -> dict:
        name = "astroquery.gaia"
        cands = [r for r in self._remote() if r.get("name") == name and r.get("id") == slug
                 and r.get("query") == query and r.get("status") == "COMPLETED"]
        if cands:
            self.used.append(cands[-1])
            return {"ok": True, "rows": self._table_rows(cands[-1], masked_none=False), "receipt": cands[-1]}
        return self._failure(name, slug)


# --------------------------------------------------------------------------------------
# Local parsers (parse only)
# --------------------------------------------------------------------------------------
def readme_lines(path: Path, needles: list[str]) -> list[dict]:
    lines = path.read_text(encoding="latin-1").splitlines()
    out = []
    for i, ln in enumerate(lines, start=1):
        if any(nd in ln for nd in needles):
            out.append({"line": i, "text": ln.rstrip()})
    return out


def cf4_table4() -> dict:
    rows = [ln for ln in (CF4_DIR / "table4.dat").read_text(encoding="ascii").splitlines() if ln.strip()]
    sl = lambda ln, a, b: ln[a - 1:b]  # ReadMe byte ranges (1-based, inclusive)
    vh = np.array([float(sl(ln, 28, 32)) for ln in rows])
    vls = np.array([float(sl(ln, 34, 38)) for ln in rows])
    v3k = np.array([float(sl(ln, 40, 44)) for ln in rows])
    glon = np.array([float(sl(ln, 102, 109)) for ln in rows])
    glat = np.array([float(sl(ln, 111, 118)) for ln in rows])
    return {"n": len(rows), "Vh": vh, "Vls": vls, "V3k": v3k, "glon": glon, "glat": glat}


def gal_n(glon_deg, glat_deg) -> np.ndarray:
    l, b = np.radians(glon_deg), np.radians(glat_deg)
    return np.column_stack((np.cos(b) * np.cos(l), np.cos(b) * np.sin(l), np.sin(b)))


def icrs_to_gal_n(ra_deg, dec_deg) -> np.ndarray:
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    g = SkyCoord(ra=np.asarray(ra_deg) * u.deg, dec=np.asarray(dec_deg) * u.deg, frame="icrs").galactic
    return gal_n(g.l.deg, g.b.deg)


def sixdf_crossmatch() -> dict:
    t1 = {}
    for ln in SIXDFV_TABLE1.read_text(encoding="ascii").splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        p = ln.split()
        t1[p[0]] = (float(p[1]), float(p[2]), float(p[3]))
    dr3 = {}
    with gzip.open(SIXDF_DR3_DIR / "6dfgs.dat.gz", "rt", encoding="ascii") as fh:
        for ln in fh:
            name = ln[0:15].strip()
            if name in t1:
                cz = ln[71:78].strip()
                if cz:
                    dr3[name] = float(cz)
    names = sorted(set(t1) & set(dr3))
    ra = np.array([t1[k][0] for k in names]); dec = np.array([t1[k][1] for k in names])
    czcmb = np.array([t1[k][2] for k in names]); czdr3 = np.array([dr3[k] for k in names])
    return {"n_table1": len(t1), "n_matched": len(names), "ra": ra, "dec": dec, "cz_cmb": czcmb, "cz_dr3": czdr3}


def fits_header_cards(path: Path, keys: tuple[str, ...]) -> list[dict]:
    from astropy.io import fits
    out = []
    with fits.open(path, memmap=True) as h:
        for i, hdu in enumerate(h[:3]):
            for card in hdu.header.cards:
                if card.keyword in keys or any(card.keyword.startswith(k) for k in keys if k.endswith("*")):
                    out.append({"hdu": i, "keyword": card.keyword, "value": str(card.value), "comment": card.comment})
    return out


# --------------------------------------------------------------------------------------
def field_locator(meta: dict, table: str, names: list[str]) -> str:
    if not meta.get("ok"):
        return ""
    for t in meta["tables"]:
        if t["name"] == table:
            parts = []
            for f in t["fields"]:
                if f["name"] in names:
                    parts.append(f"{f['name']}: '{f['description']}' (ucd {f['ucd']})")
            co = "; ".join(f"COOSYS {c['ID']} system={c['system']} equinox={c['equinox']} epoch={c['epoch']}" for c in t["coosys"])
            return (f"VizieR VOTable {table} via astroquery ({VIZIER_SERVER}), receipt sha256 "
                    f"{meta['receipt']['sha256'][:16]}: " + "; ".join(parts) + (f"; {co}" if co else ""))
    return ""


def run(downloads: Path, output: Path, replay: bool = False) -> dict:
    t_start = time.perf_counter()
    from scripts.r108.frame_input_receipts import record_pre_existing
    rc = Receipts(downloads)
    inputs = {}
    local = {"cf4_ReadMe": CF4_DIR / "ReadMe", "cf4_table4": CF4_DIR / "table4.dat",
             "sixdf_dr3_ReadMe": SIXDF_DR3_DIR / "ReadMe", "sixdf_dr3_dat": SIXDF_DR3_DIR / "6dfgs.dat.gz",
             "sixdfv_table1": SIXDFV_TABLE1, "nvss_ReadMe": NVSS_README, "icrf3_sx": ICRF3_SX,
             "commander_pr3": COMMANDER, "quaia_G20.0": QUAIA}
    for name, p in local.items():
        inputs[name] = {"path": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size}
    pre = record_pre_existing(rc.path, {str(p): {"kind": "pre_existing_input",
                                                 "read_by": ["scripts/r108/frame_registry_build.py"]}
                                        for p in local.values()})
    pre_receipts = [{"path": x["path"], "sha256": x["sha256"], "receipts": str(rc.path),
                     "appended_now": x["appended_now"]} for x in pre]

    # ---- remote metadata (astroquery / pyvo), or their offline replay from RECEIPTS.jsonl ----
    if replay:
        rp = ReceiptReplay(rc.path)
        viz_fn = lambda cat, **kw: rp.vizier(cat, **kw)  # noqa: E731
        tap_fn = lambda url, q, slug: rp.tap(url, q, slug)  # noqa: E731
        gaia_fn = lambda q, slug: rp.gaia(q, slug)  # noqa: E731
    else:
        viz_fn = lambda cat, **kw: vizier_votable(rc, downloads, cat, **kw)  # noqa: E731
        tap_fn = lambda url, q, slug: pyvo_tap(rc, downloads, url, q, slug)  # noqa: E731
        gaia_fn = lambda q, slug: gaia_astroquery(rc, downloads, q, slug)  # noqa: E731
    viz = {}
    for cat in ["J/ApJ/944/94/table2", "J/ApJ/944/94/table4", "J/MNRAS/445/2677/table1", "J/ApJS/199/26/table3",
                "J/AJ/152/50/table3", "VIII/65/nvss", "J/A+A/644/A159", "J/ApJ/964/69", "J/other/PASA/38.58",
                "VII/259/6dfgs"]:
        viz[cat] = viz_fn(cat)
    cf3_vel = viz_fn("J/AJ/152/50/table3", columns=("PGC", "HV", "Vgsr", "Vls", "Vcmb", "GLON", "GLAT"), row_limit=-1)
    gaia_cols = tap_fn(GAIA_TAP,
                       "SELECT column_name, description, unit, ucd FROM tap_schema.columns "
                       "WHERE table_name = 'gaiadr3.gaia_source' AND column_name IN "
                       "('ra', 'dec', 'ref_epoch', 'pmra', 'radial_velocity')", "gaia_tap_schema_gaia_source")
    gaia_epoch = gaia_fn("SELECT TOP 5 source_id, ref_epoch FROM gaiadr3.gaia_source", "gaia_astroquery_ref_epoch")
    casda_tabs = tap_fn(CASDA_TAP,
                        "SELECT table_name, description FROM tap_schema.tables WHERE table_name LIKE 'AS110%' OR table_name LIKE 'as110%'",
                        "casda_tap_as110_tables")
    casda_cols = None
    if casda_tabs.get("ok") and casda_tabs["rows"]:
        tnames = sorted(r["table_name"] for r in casda_tabs["rows"])
        pick = next((t for t in tnames if "gaussians" in t.lower()), tnames[0])
        casda_cols = tap_fn(CASDA_TAP,
                            "SELECT table_name, column_name, description, unit, ucd FROM tap_schema.columns "
                            f"WHERE table_name = '{pick}' AND column_name IN ('ra', 'dec', 'ra_deg_cont', 'dec_deg_cont')",
                            "casda_tap_racs_columns")

    # ---- velocity recoveries ----
    recov = {}
    t4 = cf4_table4()
    n4 = gal_n(t4["glon"], t4["glat"])
    recov["cf4_t4_helio_to_cmb"] = best_fit(t4["Vh"], t4["V3k"], n4)
    recov["cf4_t4_helio_to_localsheet"] = best_fit(t4["Vh"], t4["Vls"], n4)
    sx = sixdf_crossmatch()
    nsx = icrs_to_gal_n(sx["ra"], sx["dec"])
    recov["sixdfv_dr3cz_to_cmb"] = best_fit(sx["cz_dr3"], sx["cz_cmb"], nsx)
    recov["sixdfv_dr3cz_to_cmb"]["n_table1"] = sx["n_table1"]
    recov["sixdfv_dr3cz_to_cmb"]["n_matched"] = sx["n_matched"]
    if cf3_vel.get("ok"):
        from astropy.io.votable import parse
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tab = parse(io.BytesIO(cf3_vel["votable_bytes"])).get_first_table().to_table()
        hv = np.asarray(tab["HV"], float); n3 = gal_n(np.asarray(tab["GLON"], float), np.asarray(tab["GLAT"], float))
        for col, key in (("Vcmb", "cf3_t3_helio_to_cmb"), ("Vls", "cf3_t3_helio_to_localsheet"),
                         ("Vgsr", "cf3_t3_helio_to_gsr")):
            recov[key] = best_fit(hv, np.asarray(tab[col], float), n3)
            recov[key]["n_rows_fetched"] = int(len(tab))

    # ---- registry ----
    reg = FrameRegistry()
    reg.register_reference(planck2018_solar_dipole_reference())
    cf4_readme_hits = readme_lines(CF4_DIR / "ReadMe", ["J2000", "Vh ", "Vls ", "V3k ", "relative to", "cosmic microwave",
                                                        "Vcmb", "Systemic velocity", "the Sun", "Local Sheet",
                                                        "cosmic background"])
    loc_by = {
        "cf4_t4_helio_to_cmb": f"recovered from J/ApJ/944/94 table4 Vh (bytes 28-32) and V3k (40-44), ReadMe lines 257-262 "
                               f"(sha256 {inputs['cf4_ReadMe']['sha256'][:16]}), table4 sha256 {inputs['cf4_table4']['sha256'][:16]}",
        "cf4_t4_helio_to_localsheet": f"recovered from J/ApJ/944/94 table4 Vh (28-32) and Vls (34-38), ReadMe lines 257-260; "
                                      f"table4 sha256 {inputs['cf4_table4']['sha256'][:16]}",
        "sixdfv_dr3cz_to_cmb": f"recovered from J/MNRAS/445/2677 table1 czgal (CMB frame) x VII/259 6dfgs.dat cz (bytes 72-78) "
                               f"matched on 6dFGS name; table1 sha256 {inputs['sixdfv_table1']['sha256'][:16]}, "
                               f"6dfgs.dat.gz sha256 {inputs['sixdf_dr3_dat']['sha256'][:16]}",
    }
    if cf3_vel.get("ok"):
        for key, col in (("cf3_t3_helio_to_cmb", "Vcmb"), ("cf3_t3_helio_to_localsheet", "Vls"), ("cf3_t3_helio_to_gsr", "Vgsr")):
            loc_by[key] = (f"recovered from J/AJ/152/50/table3 HV and {col} via astroquery ({VIZIER_SERVER}), "
                           f"receipt sha256 {cf3_vel['receipt']['sha256'][:16]}; " + field_locator(viz['J/AJ/152/50/table3'],
                                                                                                 'J/AJ/152/50/table3', ['HV', col]))
    frames = {"cf4_t4_helio_to_cmb": ("solar_system_barycentre", "CF4_CMB_frame"),
              "cf4_t4_helio_to_localsheet": ("solar_system_barycentre", "CF4_Local_Sheet"),
              "sixdfv_dr3cz_to_cmb": ("6dFGS_DR3_cz_frame", "6dFGSv_CMB_frame"),
              "cf3_t3_helio_to_cmb": ("solar_system_barycentre", "CF3_CMB_frame"),
              "cf3_t3_helio_to_localsheet": ("solar_system_barycentre", "CF3_Local_Sheet"),
              "cf3_t3_helio_to_gsr": ("solar_system_barycentre", "CF3_Galactic_standard_of_rest")}
    accepted = {}
    for key, rec in recov.items():
        f = rec["fits"][rec["selected_formula"]]
        # Accept only if the release is reproduced at integer-rounding level for the bulk of rows.
        ok = f["residual_rms_kms"] < 1.0 and f["n_clipped"] <= 0.01 * f["n_rows"]
        rec["accepted_as_release_beta"] = bool(ok)
        rec["acceptance_rule"] = "selected-formula residual RMS < 1 km/s and <= 1% rows beyond 10 km/s"
        if ok:
            mov, rest = frames[key]
            reg.register_reference(VelocityReference(
                key=key, moving_frame=mov, rest_frame=rest, beta_galactic=tuple(f["beta_galactic"]),
                status="recovered_from_release", locator=loc_by[key],
                covariance_galactic=tuple(tuple(r) for r in f["covariance_galactic"]),
                formula=rec["selected_formula"],
                notes=f"rms {f['residual_rms_kms']:.3f} km/s over {f['n_used']} rows; covariance = LS with residual variance"))
            accepted[key] = True

    def L(**kw):
        return tuple(sorted((k, v) for k, v in kw.items() if v))

    rel = []
    cf4_pos = [h for h in cf4_readme_hits if "J2000" in h["text"]]
    rel.append(CatalogueRelease(
        release_id="CF4_groups_J_ApJ_944_94_table4", name="Cosmicflows-4 groups (Tully+2023) table4",
        position_frame="equatorial J2000 (RAdeg/DEdeg) and Galactic GLON/GLAT", epoch="not stated in ReadMe",
        equinox="J2000", redshift_frames=("heliocentric Vh", "Local Sheet Vls", "CMB V3k", "fV3k = f(z) V3k"),
        velocity_reference_keys=tuple(k for k in ("cf4_t4_helio_to_cmb", "cf4_t4_helio_to_localsheet") if k in accepted),
        conversion_status="registered" if accepted.get("cf4_t4_helio_to_cmb") else "beta_not_stated",
        locators=L(position_frame="J/ApJ/944/94 ReadMe lines " + ",".join(str(h["line"]) for h in cf4_pos if h["line"] > 250),
                   epoch="J/ApJ/944/94 ReadMe lines 275-276 ('(J2000)'); no epoch keyword",
                   redshift_frames="J/ApJ/944/94 ReadMe lines 257-266 (Vh 'relative to the Sun', Vls 'relative to Local Sheet', "
                                   "V3k 'relative to cosmic background', fV3k Note 6 lines 293-299)",
                   velocity_reference=("; ".join(loc_by[k] for k in ("cf4_t4_helio_to_cmb", "cf4_t4_helio_to_localsheet") if k in accepted)
                                       if accepted.get("cf4_t4_helio_to_cmb") else "")),
        notes="frame velocity not quoted in the ReadMe; recovered from the release's own Vh/V3k/Vls columns"))
    rel.append(CatalogueRelease(
        release_id="CF4_galaxies_J_ApJ_944_94_table2", name="Cosmicflows-4 galaxies (Tully+2023) table2",
        position_frame="equatorial J2000 (RAdeg/DEdeg)", epoch="not stated in ReadMe", equinox="J2000",
        redshift_frames=("CMB Vcmb only",), velocity_reference_keys=(), conversion_status="beta_not_stated",
        locators=L(position_frame="J/ApJ/944/94 ReadMe lines 162-163; " + field_locator(viz["J/ApJ/944/94/table2"], "J/ApJ/944/94/table2", ["RAJ2000", "DEJ2000"]),
                   epoch="J/ApJ/944/94 ReadMe lines 162-163 ('(J2000)')",
                   redshift_frames="J/ApJ/944/94 ReadMe line 134 and Note (2) lines 171-172 ('in the reference frame of the cosmic microwave background')"),
        notes="table2 carries only CMB-frame velocities; the galaxy-level conversion velocity is not stated (table4 recovery applies to group velocities)"))
    six_ok = accepted.get("sixdfv_dr3cz_to_cmb", False)
    rel.append(CatalogueRelease(
        release_id="6dFGSv_J_MNRAS_445_2677_table1", name="6dFGS peculiar velocities (Springob+2014) table1",
        position_frame="FK5 J2000 (VOTable COOSYS eq_FK5)", epoch="not stated", equinox="J2000",
        redshift_frames=("CMB czgal", "CMB czgr (group)"),
        velocity_reference_keys=("sixdfv_dr3cz_to_cmb",) if six_ok else (),
        conversion_status="registered" if six_ok else "beta_not_stated",
        locators=L(position_frame=field_locator(viz["J/MNRAS/445/2677/table1"], "J/MNRAS/445/2677/table1", ["RAJ2000", "DEJ2000"]) or "6dFGSv table1.txt header line '# 2 deg ra Right Ascension (J2000)'",
                   epoch="6dFGSv table1.txt header lines 5-6 ('(J2000)')",
                   redshift_frames=field_locator(viz["J/MNRAS/445/2677/table1"], "J/MNRAS/445/2677/table1", ["czgal", "czgr"]) or "6dFGSv table1.txt header lines 7-8 ('CMB frame galaxy redshift')",
                   velocity_reference=loc_by["sixdfv_dr3cz_to_cmb"] if six_ok else ""),
        notes="moving frame is the frame of VII/259 cz, which its ReadMe does not name (bytes 72-78 'Best available combined recession velocity')"))
    twomrs = viz["J/ApJS/199/26/table3"]
    if twomrs.get("ok"):
        t = twomrs["tables"][0]
        rel.append(CatalogueRelease(
            release_id="2MRS_J_ApJS_199_26_table3", name="2MASS Redshift Survey (Huchra+2012) table3",
            position_frame="; ".join(f"{c['system']} {c['equinox']}" for c in t["coosys"]) or "see fields",
            epoch="not stated", equinox="J2000",
            redshift_frames=tuple(f"{f['name']}: {f['description']}" for f in t["fields"]
                                  if "VELOC" in str(f["ucd"]).upper() or "REDSHIFT" in str(f["ucd"]).upper()) or ("see VOTable",),
            velocity_reference_keys=(), conversion_status="beta_not_stated",
            locators=L(position_frame=field_locator(twomrs, t["name"], ["RAJ2000", "DEJ2000"]),
                       epoch=field_locator(twomrs, t["name"], ["RAJ2000"]),
                       redshift_frames=field_locator(twomrs, t["name"], [f["name"] for f in t["fields"]
                                                                          if "VELOC" in str(f["ucd"]).upper() or "REDSHIFT" in str(f["ucd"]).upper()])),
            notes="2MRS frame velocity not recovered in R108"))
    cf3_ok = accepted.get("cf3_t3_helio_to_cmb", False)
    rel.append(CatalogueRelease(
        release_id="CF3_J_AJ_152_50_table3", name="Cosmicflows-3 (Tully+2016) table3",
        position_frame="FK5 J2000 (VOTable COOSYS eq_FK5) and Galactic", epoch="not stated", equinox="J2000",
        redshift_frames=("heliocentric HV", "Galactic standard of rest Vgsr", "Local Sheet Vls", "CMB Vcmb (Fixsen+1996)", "CMB adjusted Vcmba"),
        velocity_reference_keys=tuple(k for k in ("cf3_t3_helio_to_cmb", "cf3_t3_helio_to_localsheet", "cf3_t3_helio_to_gsr") if accepted.get(k)),
        conversion_status="registered" if cf3_ok else "beta_not_stated",
        locators=L(position_frame=field_locator(viz["J/AJ/152/50/table3"], "J/AJ/152/50/table3", ["RAJ2000", "DEJ2000", "GLON", "GLAT"]),
                   epoch=field_locator(viz["J/AJ/152/50/table3"], "J/AJ/152/50/table3", ["RAJ2000"]),
                   redshift_frames=field_locator(viz["J/AJ/152/50/table3"], "J/AJ/152/50/table3", ["HV", "Vgsr", "Vls", "Vcmb", "Vcmba"]),
                   velocity_reference="; ".join(loc_by[k] for k in ("cf3_t3_helio_to_cmb", "cf3_t3_helio_to_localsheet", "cf3_t3_helio_to_gsr") if accepted.get(k))),
        notes="Vcmb FIELD description cites Fixsen et al. 1996 ApJ 473 576 for the CMB frame"))
    nvss_hits = readme_lines(NVSS_README, ["J2000", "epoch of observation"])
    rel.append(CatalogueRelease(
        release_id="NVSS_VIII_65", name="NRAO VLA Sky Survey (Condon+1998)",
        position_frame="FK5 J2000 (VOTable COOSYS eq_FK5)", epoch="epoch of observation 1995+/-2", equinox="J2000",
        redshift_frames=("none (continuum counts)",), velocity_reference_keys=(), conversion_status="not_applicable",
        locators=L(position_frame="VIII/65 ReadMe lines " + ",".join(str(h["line"]) for h in nvss_hits if "J2000" in h["text"]) + "; " + field_locator(viz["VIII/65/nvss"], "VIII/65/nvss", ["RAJ2000", "DEJ2000"]),
                   epoch="VIII/65 ReadMe lines " + ",".join(str(h["line"]) for h in nvss_hits if "epoch" in h["text"]),
                   redshift_frames="VIII/65 field list (no redshift column)"),
        notes="R65 count dipoles are expressed in ICRS x,y; FK5 J2000 and ICRS differ by < 0.1 arcsec"))
    racs = viz["J/other/PASA/38.58"]
    if racs.get("ok") or (casda_cols and casda_cols.get("ok")):
        pos_loc = ""
        if racs.get("ok"):
            t = racs["tables"][0]
            pos_loc = field_locator(racs, t["name"], [f["name"] for f in t["fields"] if f["ucd"] and "POS_EQ" in str(f["ucd"]).upper()][:2])
        if casda_cols and casda_cols.get("ok"):
            pos_loc += ("; CASDA TAP_SCHEMA rows: " + "; ".join(f"{r['table_name']}.{r['column_name']}: '{r['description']}'" for r in casda_cols["rows"])
                        + f" (job {casda_cols['receipt']['job_id']})")
        rel.append(CatalogueRelease(
            release_id="RACS_low_DR1", name="RACS-low DR1 (Hale+2021)", position_frame="see locator (VizieR COOSYS / CASDA TAP_SCHEMA)",
            epoch="not stated", equinox="J2000/ICRS per locator", redshift_frames=("none (continuum counts)",),
            velocity_reference_keys=(), conversion_status="not_applicable",
            locators=L(position_frame=pos_loc, epoch=pos_loc, redshift_frames="no redshift column in RACS-low DR1"),
            notes="the R65 radio file 'Full_NVSS_combined_named.dat' is NVSS-only; RACS enters only through SQ-RADIO cross-checks"))
    if gaia_cols.get("ok"):
        g = {r["column_name"]: r for r in gaia_cols["rows"]}
        ep = sorted({r["ref_epoch"] for r in gaia_epoch["rows"]}) if gaia_epoch.get("ok") else []
        gloc = "; ".join(f"gaiadr3.gaia_source.{k}: '{v['description']}' [{v['unit']}]" for k, v in sorted(g.items()))
        rel.append(CatalogueRelease(
            release_id="GaiaDR3_gaia_source", name="Gaia DR3 gaia_source", position_frame="ICRS (Gaia-CRF3)",
            epoch=f"ref_epoch {ep}" if ep else "see locator", equinox="ICRS (no equinox)",
            redshift_frames=("barycentric radial_velocity (stars); no extragalactic redshift frame",),
            velocity_reference_keys=(), conversion_status="not_applicable",
            locators=L(position_frame=f"Gaia TAP_SCHEMA via pyvo (job {gaia_cols['receipt']['job_id']}): {gloc}",
                       epoch=(f"astroquery.gaia job {gaia_epoch['receipt']['job_id']} rows ref_epoch={ep}" if gaia_epoch.get("ok") else gloc),
                       redshift_frames=gloc)))
    quaia = viz["J/ApJ/964/69"]
    qh = fits_header_cards(QUAIA, ("TTYPE*",))
    rel.append(CatalogueRelease(
        release_id="Quaia_G20.0_J_ApJ_964_69", name="Quaia G<20.0 (Storey-Fisher+2024)",
        position_frame="ICRS (Gaia DR3 positions)", epoch="Ep=2016.0", equinox="ICRS",
        redshift_frames=("redshift_quaia (frame not stated by the release; VizieR UCD REDSHIFT_HC is a CDS annotation)",),
        velocity_reference_keys=(), conversion_status="beta_not_stated",
        locators=L(position_frame=field_locator(quaia, quaia["tables"][0]["name"], ["RA_ICRS", "DE_ICRS"]) if quaia.get("ok") else f"local FITS header TTYPE cards: {[c['value'] for c in qh][:8]}",
                   epoch=field_locator(quaia, quaia["tables"][0]["name"], ["RA_ICRS"]) if quaia.get("ok") else "Gaia DR3 ref_epoch",
                   redshift_frames=field_locator(quaia, quaia["tables"][0]["name"], ["zQuaia"]) if quaia.get("ok") else "local FITS header TTYPE3 redshift_quaia"),
        notes=f"local release FITS sha256 {inputs['quaia_G20.0']['sha256'][:16]}"))
    ch = fits_header_cards(COMMANDER, ("COORDSYS", "POLCCONV", "ORDERING", "NSIDE", "METHOD", "TUNIT1", "DATE"))
    rel.append(CatalogueRelease(
        release_id="Planck_PR3_Commander_2048_R3.00", name="Planck PR3 Commander CMB map (COM_CMB_IQU-commander_2048_R3.00_full)",
        position_frame="Galactic (HEALPix)", epoch="not stated in header", equinox="n/a",
        redshift_frames=("CMB temperature map; kinematic frame = barycentre in CMB frame",),
        velocity_reference_keys=("planck2018_solar_dipole",), conversion_status="registered",
        locators=L(position_frame="FITS header " + "; ".join(f"HDU{c['hdu']} {c['keyword']}={c['value']} ({c['comment']})" for c in ch if c["keyword"] in ("COORDSYS", "POLCCONV", "ORDERING")),
                   epoch="FITS header: no EPOCH/EQUINOX card in HDUs 0-2",
                   redshift_frames="FITS header TUNIT1=K_CMB; no dipole keyword in HDUs 0-2",
                   velocity_reference=planck2018_solar_dipole_reference().locator),
        notes="solar-dipole treatment of the released map is not stated in its header; the registered velocity is the published Planck 2018 solar dipole"))
    icrf_lines = readme_lines(ICRF3_SX, ["J2000.0", "Charlot"])
    icrf = viz["J/A+A/644/A159"]
    rel.append(CatalogueRelease(
        release_id="ICRF3_J_A+A_644_A159", name="ICRF3 (Charlot+2020) S/X, K, X/Ka",
        position_frame="ICRS (ICRF3 realisation)", epoch="Ep=2015.0", equinox="J2000.0 (designations)",
        redshift_frames=("none",), velocity_reference_keys=(), conversion_status="not_applicable",
        locators=L(position_frame=(field_locator(icrf, "J/A+A/644/A159/table10", ["RAICRS", "DEICRS"]) if icrf.get("ok") else "")
                   + "; IERS icrf3sx.txt lines " + ",".join(str(h["line"]) for h in icrf_lines),
                   epoch=field_locator(icrf, "J/A+A/644/A159/table10", ["RAICRS", "DEICRS"]) if icrf.get("ok") else "IERS icrf3sx.txt header",
                   redshift_frames="ICRF3 tables carry no redshift"),
        notes="galactic-aberration epoch from the VizieR COOSYS epoch and RAICRS description"))
    for r in rel:
        reg.register_release(r)
    reg.validate()

    # boost/inverse identity per release (numerical record; the unit test asserts it)
    rng = np.random.default_rng(20261124)
    roundtrip = {}
    for rid, key in reg.releases_with_conversions():
        b = rng.normal(size=(64, 3)); b *= (rng.uniform(0, 0.3, 64) / np.linalg.norm(b, axis=1))[:, None]
        ev = max(float(np.max(abs(reg.velocity_to_rest(key, reg.velocity_to_moving(key, x, release_id=rid),
                                                        release_id=rid) - x))) for x in b)
        n = rng.normal(size=(256, 3)); n /= np.linalg.norm(n, axis=1)[:, None]
        z = rng.uniform(0, 5, 256)
        zr, nr = reg.photon_to_rest(key, z, n, release_id=rid)
        zb, nb = reg.photon_to_moving(key, zr, nr, release_id=rid)
        roundtrip[f"{rid}|{key}"] = {"velocity_max_abs": ev, "z_max_abs": float(np.max(abs(zb - z))),
                                     "n_max_abs": float(np.max(abs(nb - n)))}

    planck = reg.references["planck2018_solar_dipole"]
    comparisons = {}
    for key in recov:
        f = recov[key]["fits"][recov[key]["selected_formula"]]
        b = np.array(f["beta_galactic"])
        comparisons[key] = {"minus_planck2018_kms": ((b - planck.beta) * C_KM_S).tolist(),
                            "speed_minus_planck2018_kms": float((np.linalg.norm(b) - np.linalg.norm(planck.beta)) * C_KM_S),
                            "angle_to_planck2018_deg": float(np.degrees(np.arccos(np.clip(b @ planck.beta / np.linalg.norm(b) / np.linalg.norm(planck.beta), -1, 1))))}

    payload = {
        "schema": "htt.r108.frame.catalogue_frame_registry/1",
        "node": "SQ-FRAME (handoff A6)",
        "label": "NUMERICAL (registry + release-recovered frame velocities); no physical tilt claim",
        "git": git_state(),
        "command": " ".join(sys.argv),
        "code_sha256": {c: sha256_file(REPO / c) for c in CODE},
        "inputs_local": inputs,
        "pre_existing_input_receipts": pre_receipts,
        "remote_mode": ("replayed from RECEIPTS.jsonl (saved bytes, SHA-256 verified; no network)" if replay
                        else "fetched (astroquery / pyvo)"),
        "remote_receipts": (rp.used if replay else rc.rows),
        "remote_metadata": {cat: ({k: v for k, v in m.items() if k not in ("votable_bytes",)} if m.get("ok") else m)
                            for cat, m in viz.items()},
        "gaia_tap_schema": gaia_cols, "gaia_ref_epoch_rows": gaia_epoch,
        "casda_tables": casda_tabs, "casda_columns": casda_cols,
        "cf4_readme_hits": cf4_readme_hits,
        "frame_velocity_recovery": recov,
        "recovered_minus_planck2018": comparisons,
        "roundtrip_identity": roundtrip,
        "registry": reg.to_dict(),
        "no_unmeasured_beta_rule": NO_UNMEASURED_BETA_RULE,
        "blocked": ([] if twomrs.get("ok") else [{"release": "2MRS J/ApJS/199/26", "reason": twomrs.get("errors"),
                                                  "missing_input": "2MRS table3 VOTable/ReadMe (CDS ftp HTML 404; CfA mirror Postgres error)"}]),
        "runtime_s": time.perf_counter() - t_start,
    }
    write_json(output, payload)
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--downloads", type=Path, default=HOME / "Downloads/htt_r108/frame")
    ap.add_argument("--output", type=Path, default=OUTFILE)
    ap.add_argument("--replay-receipts", action="store_true",
                    help="re-parse the saved remote results named by RECEIPTS.jsonl (no network)")
    a = ap.parse_args(argv)
    p = run(a.downloads.expanduser(), a.output, replay=a.replay_receipts)
    print(json.dumps({"releases": sorted(p["registry"]["releases"]), "references": sorted(p["registry"]["references"]),
                      "recovered": {k: {"formula": v["selected_formula"], "accepted": v["accepted_as_release_beta"],
                                        **{kk: v["fits"][v["selected_formula"]][kk] for kk in ("speed_kms", "apex_l_deg", "apex_b_deg", "residual_rms_kms", "n_clipped", "n_rows")}}
                                    for k, v in p["frame_velocity_recovery"].items()},
                      "roundtrip": p["roundtrip_identity"], "blocked": p["blocked"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
