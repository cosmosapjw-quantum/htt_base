"""R107 cloud: manifest-driven data acquisition for the data-limited nodes of the 60-node DAG.

The manifest (``ITEMS``) is the hand-written source of truth; ``manifest`` writes it as
JSON.  Nothing is downloaded unless ``fetch --execute`` is given with an explicit
``--max-bytes`` budget.  Semantics follow scripts/r101/acquire.py: no clobbering,
exact length when the provider states it, SHA-256 (and MD5 when published) on the
fly, atomic publication by hard link from a private temporary directory, and one JSON
receipt line per product in ``RECEIPTS.jsonl``.  Products that already have a
dedicated fetcher (Manticore, Commander) are listed with that command instead.

Usage (repository root):
  python -m scripts.r107_cloud.acquisition list
  python -m scripts.r107_cloud.acquisition plan --items D01 D11 --max-bytes 50000000
  python -m scripts.r107_cloud.acquisition fetch --items D01 --directory ~/Downloads/htt_r107 --max-bytes 5000000 --execute
  python -m scripts.r107_cloud.acquisition verify --directory ~/Downloads/htt_r107
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SCHEMA = "htt.r107.acquisition/1"
CHECKED = "2026-11-24 web search (listing or catalogue page seen); byte size and digest are recorded at download"
HYREC = "https://raw.githubusercontent.com/nanoomlee/HYREC-2/038dc8d71baed5c30a4fdd55576b97637ba5b879/"
CDS = "https://cdsarc.cds.unistra.fr/ftp/"

ITEMS: list[dict] = [
    {"id": "D00", "priority": "P0", "kind": "https_file", "nodes": ["SQ-NATIVE", "B02"],
     "purpose": "HYREC-2 atomic tables required by bass.recombination.tilted_hyrec (coupled solver, LoS integration test).",
     "target_subdir": "data/external/r101_legacy_recovery/hyrec_atomic",
     "files": [{"name": n, "url": HYREC + src, "expected_bytes": b, "sha256": s} for n, src, b, s in (
         ("Alpha_inf.dat", "Alpha_inf.dat", 272000, "357101049c9382e90e5e1e896961407d3b465b61b78de9750b852c05ea4d1023"),
         ("R_inf.dat", "R_inf.dat", 1700, "ce914f4b552ba55ba00f7916f36b0986f19adfdb638e5aefae91f7b2d05a8112"),
         ("fit_swift.dat", "fit_swift.dat", 17797, "46a644d7d2633b8f13080f9062df9b72a2e5adfa956d70d32ad1d7f4ec0a4641"),
         ("two_photon_tables.dat", "two_photon_tables.dat", 25191, "93d23871e21c40f5b72a6ef9acf3eb7be054735c8aee9401e455736c1d9d8cf9"),
         ("two_photon_tables_hires.dat", "two_photon_tables_hires.dat", 103017, "db201c729a38c7919172cf080c8ba44cdf8e6b131a6eaa8adcbc9e58fd4d0c93"))],
     "citation": "Lee & Ali-Haimoud 2020 (HYREC-2); pinned commit as in R101 RESOURCE_RECOVERY.json",
     "verification": "SHA-256 equals bass.recombination.tilted_hyrec.HYREC_EXPECTED_SHA256", "checked": "R101 receipts"},
    {"id": "D01", "priority": "P0", "kind": "https_file", "nodes": ["SQ-CF4", "H02", "H05"],
     "purpose": "Cosmicflows-3 galaxy table (17,669 rows) for CF3 calibration-window overlap and method attribution (R106 used CF4 table2 as proxy).",
     "files": [{"name": "J_AJ_152_50_ReadMe", "url": CDS + "J/AJ/152/50/ReadMe", "expected_bytes": None, "sha256": None},
               {"name": "J_AJ_152_50_table3.dat.gz", "url": CDS + "J/AJ/152/50/table3.dat.gz", "expected_bytes": None, "sha256": None},
               {"name": "J_AJ_152_50_table2.dat.gz", "url": CDS + "J/AJ/152/50/table2.dat.gz", "expected_bytes": None, "sha256": None}],
     "citation": "Tully, Courtois & Sorce 2016, AJ 152, 50; VizieR J/AJ/152/50",
     "verification": "table3 row count 17669 against ReadMe; byte layout per ReadMe", "checked": CHECKED},
    {"id": "D02", "priority": "P0", "kind": "https_file", "nodes": ["SQ-CF4", "H02"],
     "purpose": "6dFGSv peculiar-velocity table (Springob et al. 2014) for ID and FP cross-match of the 8,885 positions.",
     "files": [{"name": "J_MNRAS_445_2677_ReadMe", "url": CDS + "cats/J/other/MNRAS/445/2677/ReadMe", "expected_bytes": None, "sha256": None},
               {"name": "J_MNRAS_445_2677_table1.dat.gz", "url": CDS + "cats/J/other/MNRAS/445/2677/table1.dat.gz", "expected_bytes": None, "sha256": None}],
     "citation": "Springob et al. 2014, MNRAS 445, 2677; VizieR J/MNRAS/445/2677",
     "verification": "row count per ReadMe; join on 6dFGS name with the R105 8,885 positions", "checked": CHECKED},
    {"id": "D03", "priority": "P0", "kind": "portal", "nodes": ["SQ-CF4"],
     "purpose": "6dFGS DR3 K-band (2MASS XSC) magnitudes for 6dFGSv objects that are not 2MRS tracers (R106 mark zero-point confound).",
     "portal": "https://vizier.cds.unistra.fr/viz-bin/VizieR-2?-source=VII/259",
     "instruction": "Read CDS VII/259 ReadMe, download the 6dfgs table (all rows, columns name, RAJ2000, DEJ2000, Kmag, z, quality); record file names and SHA-256 with this script's verify.",
     "citation": "Jones et al. 2009, MNRAS 399, 683; VizieR VII/259", "verification": "125071 catalogue galaxies per abstract", "checked": CHECKED},
    {"id": "D04", "priority": "P1", "kind": "portal", "nodes": ["H02", "SQ-CF4"],
     "purpose": "Independent mean 2M++ density/velocity field (Carrick et al. 2015, beta*=0.43, V_ext=[89,-131,17] km/s) as a non-CF3 calibration and field route.",
     "portal": "https://git.aquila-consortium.org/guilhem_lavaux/cosmicflows-deployer/raw/branch/main/download/index.html",
     "instruction": "Use the France or Canada mirror named on the download page; files twompp_density.npy and twompp_velocity.npy (257^3, Galactic Cartesian, LG at cell 128,128,128).",
     "citation": "Carrick et al. 2015, MNRAS 450, 317", "verification": "array shapes (257,257,257) and (3,257,257,257); LG velocity from README sample code", "checked": CHECKED},
    {"id": "D05", "priority": "P1", "kind": "existing_fetcher", "nodes": ["H02"],
     "purpose": "Manticore-Local posterior velocity fields (draws 0, 1) for inter-group posterior covariance.",
     "command": "env -u PYTHONPATH \"$field_py\" -B -m scripts.r103.manticore_cf4_pv fetch --indices 0 1 --directory \"$HOME/Downloads/htt_r103/manticore\" --max-bytes 800000000",
     "citation": "McAlpine et al. 2025, MNRAS, doi:10.1093/mnras/staf767", "verification": "as in R105 MANTICORE_ROUTES_KO.md", "checked": "R105 route probe (IAP timeouts)"},
    {"id": "D06", "priority": "P0", "kind": "existing_fetcher", "nodes": ["SQ-CMB-NULL", "L03", "B03"],
     "purpose": "Commander PR3/FFP10 CMB+noise pairs 00007..00299 (R106 inventory: 356,352,825,600 new bytes).",
     "command": "\"$PY\" -m scripts.r105.commander_ensemble batch --start 7 --stop 300 --directory \"$HOME/Downloads/htt_r105_commander/reductions\" --max-download-bytes <budget>",
     "citation": "Planck 2018 results IV and VII; FFP10", "verification": "per-pair input SHA, same 15-coefficient estimator and beam/mask SHA as R106", "checked": "R105 COMMANDER_DOWNLOAD_PLAN.json"},
    {"id": "D07", "priority": "P0", "kind": "portal", "nodes": ["SQ-CMB-NULL", "L03"],
     "purpose": "Commander half-mission (HM1/HM2) and odd-even (OE1/OE2) observed maps and the matching FFP10 noise splits for split-difference nulls (R106: split products absent).",
     "portal": "https://pla.esac.esa.int/pla/",
     "instruction": "Planck 2018 VII states 300 noise realizations per frequency for full-mission, HM and OE splits, processed through component separation. Resolve the exact Commander split file IDs in the PLA (Maps > CMB maps for data; Simulations > component-separated noise for sims), then fetch 00000..00006 HM1/HM2 first through product-action URLs with this script (add them to ITEMS as https_file with expected_bytes from the PLA listing).",
     "citation": "Planck 2018 results VII (arXiv:1906.02552) section 4", "verification": "same Nside, beam and mask as R106 Commander pairs; HM1-HM2 half difference has zero signal", "checked": CHECKED},
    {"id": "D08", "priority": "P0", "kind": "https_file", "nodes": ["SQ-GAIA", "K03", "PHY-04"],
     "purpose": "ICRF3 S/X (4,536 VLBI positions) for the AGN optical-radio centroid control of the Gaia/Quaia shells.",
     "files": [{"name": "J_A+A_644_A159_ReadMe", "url": CDS + "J/A+A/644/A159/ReadMe", "expected_bytes": None, "sha256": None},
               {"name": "J_A+A_644_A159_table10.dat.gz", "url": CDS + "J/A+A/644/A159/table10.dat.gz", "expected_bytes": None, "sha256": None}],
     "citation": "Charlot et al. 2020, A&A 644, A159", "verification": "4536 rows in table10", "checked": CHECKED},
    {"id": "D09", "priority": "P1", "kind": "https_file", "nodes": ["SQ-GAIA", "K03"],
     "purpose": "Gaia (E)DR3 commanded scanning law for scan-law mocks of the proper-motion vector-spherical-harmonic nulls.",
     "files": [{"name": "CommandedScanLaw_001.csv.gz", "url": "https://cdn.gea.esac.esa.int/Gaia/gedr3/auxiliary/commanded_scan_law/CommandedScanLaw_001.csv.gz", "expected_bytes": 569780480, "sha256": None},
               {"name": "CommandedScanLaw_MD5SUM.txt", "url": "https://cdn.gea.esac.esa.int/Gaia/gedr3/auxiliary/commanded_scan_law/_MD5SUM.txt", "expected_bytes": None, "sha256": None}],
     "citation": "Gaia Collaboration, GEDR3 auxiliary data", "verification": "MD5 against _MD5SUM.txt", "checked": CHECKED},
    {"id": "D10", "priority": "P1", "kind": "tap_query", "nodes": ["SQ-GAIA", "K03"],
     "purpose": "Gaia DR3 AGN cross-identifications (Gaia-CRF3 sources) to separate AGN-centroid systematics from frame terms.",
     "service": "https://gea.esac.esa.int/tap-server/tap",
     "adql": "SELECT a.source_id, a.catalogue_name, a.source_name_in_catalogue, g.ra, g.dec, g.pmra, g.pmdec, g.pmra_error, g.pmdec_error, g.pmra_pmdec_corr, g.phot_g_mean_mag, g.bp_rp FROM gaiadr3.agn_cross_id AS a JOIN gaiadr3.gaia_source AS g USING (source_id)",
     "citation": "Gaia Collaboration, Klioner et al. 2022 (Gaia-CRF3)", "verification": "row count equals the archive count of agn_cross_id after the join; store query, job id and SHA-256", "checked": "table name per Gaia DR3 data model (verify at run time)"},
    {"id": "D11", "priority": "P1", "kind": "portal", "nodes": ["SQ-RADIO", "PHY-03", "V04"],
     "purpose": "RACS-low DR1 source catalogue (2.1M sources, dec < +30) as an independent survey for the C1 (LSS dipole power) prior and a southern cross-check of the NVSS estimator.",
     "portal": "https://doi.org/10.25919/8zyw-5w85",
     "instruction": "CASDA collection AS110 DR1: racs_dr1_sources_galacticcut_v2021_08_v01 (|b|>5 deg). Download through CASDA (astroquery.casda or the DAP page), record file names, sizes and SHA-256.",
     "citation": "Hale et al. 2021, PASA 38, e058", "verification": "about 2.1 million rows; declination coverage -80 to +30 deg", "checked": CHECKED},
]

KINDS = {"https_file", "existing_fetcher", "portal", "tap_query"}


def manifest() -> dict:
    return {"schema": SCHEMA, "generated_utc": None, "items": ITEMS,
            "policy": "dry-run by default; --execute and --max-bytes are required for any transfer; no product is overwritten"}


def _items(ids):
    table = {it["id"]: it for it in ITEMS}
    missing = [i for i in ids if i not in table]
    if missing:
        raise SystemExit(f"unknown item ids {missing}")
    return [table[i] for i in ids]


def plan(ids, max_bytes):
    """Return the files a fetch would transfer, with the known byte total and budget verdict."""
    rows, known = [], 0
    for it in _items(ids):
        if it["kind"] != "https_file":
            rows.append({"id": it["id"], "kind": it["kind"], "action": it.get("command") or it.get("instruction") or it.get("adql")})
            continue
        for f in it["files"]:
            rows.append({"id": it["id"], "file": f["name"], "url": f["url"], "expected_bytes": f["expected_bytes"]})
            known += f["expected_bytes"] or 0
    return {"rows": rows, "known_bytes": known, "max_bytes": max_bytes,
            "within_budget_for_known_sizes": max_bytes is not None and known <= max_bytes}


def _digest_file(path: Path) -> dict:
    sha, md5, n = hashlib.sha256(), hashlib.md5(), 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
            md5.update(chunk)
            n += len(chunk)
    return {"bytes": n, "sha256": sha.hexdigest(), "md5": md5.hexdigest()}


def fetch_file(spec: dict, destination: Path, budget: int, *, allow_file_urls: bool = False, timeout: float = 120.0) -> dict:
    """Fetch one file under the byte budget; never overwrite; return a receipt dictionary."""
    name = spec["name"]
    if Path(name).name != name or name in {".", ".."}:
        raise ValueError(f"invalid basename {name!r}")
    scheme = urlparse(spec["url"]).scheme
    if scheme != "https" and not (allow_file_urls and scheme == "file"):
        raise ValueError(f"refusing non-https URL {spec['url']}")
    target = destination / name
    receipt = {"name": name, "url": spec["url"], "expected_bytes": spec.get("expected_bytes"), "expected_sha256": spec.get("sha256")}
    if target.exists() or target.is_symlink():
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"nonregular existing path {target}")
        dig = _digest_file(target)
        ok = (spec.get("expected_bytes") in (None, dig["bytes"])) and (spec.get("sha256") in (None, dig["sha256"]))
        if not ok:
            raise FileExistsError(f"preserved conflicting product {target}")
        return dict(receipt, **dig, status="REUSED_EXISTING", downloaded=False)
    cap = budget if spec.get("expected_bytes") is None else min(budget, int(spec["expected_bytes"]))
    if spec.get("expected_bytes") is not None and budget < int(spec["expected_bytes"]):
        raise ValueError(f"budget {budget} below expected size of {name}")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".r107-intake-", dir=destination) as work:
        tmp = Path(work) / name
        sha, md5, n = hashlib.sha256(), hashlib.md5(), 0
        req = Request(spec["url"], headers={"Accept-Encoding": "identity", "User-Agent": "htt-r107-acquisition"})
        with urlopen(req, timeout=timeout) as resp, open(tmp, "wb") as out:
            status = getattr(resp, "status", None)
            headers = {k.lower(): v for k, v in resp.headers.items()} if getattr(resp, "headers", None) else {}
            while True:
                chunk = resp.read(min(1 << 20, cap + 1 - n))
                if not chunk:
                    break
                n += len(chunk)
                if n > cap:
                    raise ValueError(f"{name}: transfer exceeded the cap of {cap} bytes")
                sha.update(chunk)
                md5.update(chunk)
                out.write(chunk)
        if spec.get("expected_bytes") is not None and n != int(spec["expected_bytes"]):
            raise ValueError(f"{name}: received {n} bytes, expected {spec['expected_bytes']}")
        if spec.get("sha256") is not None and sha.hexdigest() != spec["sha256"]:
            raise ValueError(f"{name}: SHA-256 mismatch")
        os.link(tmp, target)
    return dict(receipt, bytes=n, sha256=sha.hexdigest(), md5=md5.hexdigest(), status="FETCHED", downloaded=True,
                http_status=status, etag=headers.get("etag"), last_modified=headers.get("last-modified"),
                fetched_at_utc=_dt.datetime.now(_dt.timezone.utc).isoformat())


def fetch(ids, directory: Path, max_bytes: int, *, allow_file_urls: bool = False) -> list[dict]:
    receipts, budget = [], int(max_bytes)
    for it in _items(ids):
        if it["kind"] != "https_file":
            receipts.append({"id": it["id"], "status": "NOT_A_FILE_ITEM", "kind": it["kind"]})
            continue
        sub = directory / it["id"]
        for f in it["files"]:
            rec = dict(id=it["id"], **fetch_file(f, sub, budget, allow_file_urls=allow_file_urls))
            budget -= rec["bytes"] if rec.get("downloaded") else 0
            receipts.append(rec)
            with open(directory / "RECEIPTS.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return receipts


def verify(directory: Path) -> list[dict]:
    out = []
    path = directory / "RECEIPTS.jsonl"
    if not path.is_file():
        raise SystemExit(f"no receipts in {directory}")
    for line in path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if "name" not in rec:
            continue
        f = directory / rec["id"] / rec["name"]
        dig = _digest_file(f) if f.is_file() else None
        out.append({"id": rec["id"], "name": rec["name"], "present": dig is not None,
                    "sha256_matches": dig is not None and dig["sha256"] == rec["sha256"]})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("manifest")
    m.add_argument("--output", type=Path, required=True)
    sub.add_parser("list")
    p = sub.add_parser("plan")
    p.add_argument("--items", nargs="+", required=True)
    p.add_argument("--max-bytes", type=int)
    f = sub.add_parser("fetch")
    f.add_argument("--items", nargs="+", required=True)
    f.add_argument("--directory", type=Path, required=True)
    f.add_argument("--max-bytes", type=int, required=True)
    f.add_argument("--execute", action="store_true")
    v = sub.add_parser("verify")
    v.add_argument("--directory", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.cmd == "manifest":
        a.output.write_text(json.dumps(manifest(), indent=1, sort_keys=False) + "\n", encoding="utf-8")
    elif a.cmd == "list":
        for it in ITEMS:
            print(f"{it['id']} {it['priority']} {it['kind']:16s} {','.join(it['nodes']):28s} {it['purpose'][:90]}")
    elif a.cmd == "plan":
        print(json.dumps(plan(a.items, a.max_bytes), indent=1))
    elif a.cmd == "fetch":
        if not a.execute:
            print(json.dumps(plan(a.items, a.max_bytes), indent=1))
            print("dry run: add --execute to transfer", file=sys.stderr)
            return 0
        print(json.dumps(fetch(a.items, a.directory.expanduser(), a.max_bytes), indent=1))
    elif a.cmd == "verify":
        print(json.dumps(verify(a.directory.expanduser()), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
