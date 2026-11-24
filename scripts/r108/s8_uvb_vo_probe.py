"""R108 lane s8 step 3 support: look for machine-readable z < 4 UV-background / quasar-emissivity tables in VO services.

Purpose
  The feasibility note for lifting the rei_bianchi z >= 4 guard names published UV-background
  syntheses and quasar emissivities.  This probe asks VO services (astroquery.vizier on the CDS and
  CfA VizieR servers; pyvo RegTAP registry and TAPVizieR) whether the corresponding tables are
  available as VizieR catalogues.  Metadata only: no table rows are downloaded.

Inputs: none (network).  Output: REI/S8_UVB_VO_PROBE.json (service outcome per query, catalogue ids and
  descriptions as returned).  No randomness.  Interpreter: an environment with astroquery and pyvo
  (the repository .venv: astroquery 0.4.11, pyvo 1.10.0 at the time of writing).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

HTT_BASE = Path(__file__).resolve().parents[2]
DEFAULT_OUT = HTT_BASE / ("docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/"
                          "REI/S8_UVB_VO_PROBE.json")
VIZIER_SERVERS = ("vizier.cds.unistra.fr", "vizier.cfa.harvard.edu")
# Keyword searches (VizieR find_catalogs) and bibcode-derived catalogue ids of the named publications.
KEYWORDS = ("Haardt Madau", "UV background", "ionizing background", "Faucher-Giguere", "Puchwein",
            "Khaire Srianand", "quasar luminosity function", "mean free path ionizing photons", "HeII Lyman alpha forest")
CATALOG_IDS = {"HM12 ApJ 746, 125": "J/ApJ/746/125", "FG20 MNRAS 493, 1614": "J/MNRAS/493/1614",
               "P19 MNRAS 485, 47": "J/MNRAS/485/47", "KS19 MNRAS 484, 4174": "J/MNRAS/484/4174",
               "Kulkarni+2019 MNRAS 488, 1035": "J/MNRAS/488/1035", "Shen+2020 MNRAS 495, 3252": "J/MNRAS/495/3252",
               "Becker+2021 MNRAS 508, 1853": "J/MNRAS/508/1853", "Worseck+2014 MNRAS 445, 1745": "J/MNRAS/445/1745"}
REGTAP_KEYWORDS = ("UV background", "ionizing background")
TAPVIZIER = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap"


def attempt(fn):
    t0 = time.time()
    try:
        out = fn()
        return {"ok": True, "result": out, "wall_s": round(time.time() - t0, 3)}
    except Exception as exc:  # network outcomes are data here, recorded verbatim
        return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:300]}", "wall_s": round(time.time() - t0, 3)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--timeout", type=float, default=30.0)
    args = ap.parse_args(argv)
    import astroquery
    import pyvo
    from astroquery.vizier import Vizier
    result = {"schema": "htt.r108.s8.uvb_vo_probe/1", "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "script": {"path": str(Path(__file__).resolve()),
                         "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              "versions": {"astroquery": astroquery.__version__, "pyvo": pyvo.__version__, "python": sys.version},
              "vizier": {}, "regtap": {}, "tapvizier": {}}
    for server in VIZIER_SERVERS:
        viz = Vizier(vizier_server=server, timeout=args.timeout)
        block = {"connectivity_get_catalogs_II_246": attempt(
            lambda: [str(t.meta.get("name", "")) for t in Vizier(vizier_server=server, timeout=args.timeout,
                                                                 row_limit=1).get_catalogs("II/246")])}
        block["find_catalogs"] = {}
        for kw in KEYWORDS:
            def find(kw=kw):
                r = viz.find_catalogs(kw, max_catalogs=20)
                return None if r is None else {k: v.description for k, v in r.items()}
            block["find_catalogs"][kw] = attempt(find)
        block["catalog_ids"] = {}
        for label, cid in CATALOG_IDS.items():
            def get(cid=cid):
                r = viz.find_catalogs(cid, max_catalogs=5)
                return None if r is None else {k: v.description for k, v in r.items()}
            block["catalog_ids"][label] = {"id": cid, **attempt(get)}
        result["vizier"][server] = block
    for kw in REGTAP_KEYWORDS:
        result["regtap"][kw] = attempt(lambda kw=kw: [(r.ivoid, r.res_title) for r in
                                                      list(pyvo.registry.search(keywords=[kw]))[:30]])
    result["tapvizier"]["tables_of_named_catalogues"] = attempt(lambda: [
        tuple(row) for row in pyvo.dal.TAPService(TAPVIZIER).run_sync(
            "SELECT TOP 50 table_name, description FROM tap_schema.tables WHERE " + " OR ".join(
                f"table_name LIKE '{cid}%'" for cid in CATALOG_IDS.values())).to_table().iterrows()])
    found = sorted({k for srv in result["vizier"].values() for blk in ("find_catalogs", "catalog_ids")
                    for q in srv[blk].values() if q.get("ok") and isinstance(q.get("result"), dict)
                    for k in q["result"] if isinstance(k, str)})
    result["summary"] = {
        "vizier_server_reachable": {s: result["vizier"][s]["connectivity_get_catalogs_II_246"]["ok"]
                                    for s in VIZIER_SERVERS},
        "regtap_ok": {k: v["ok"] for k, v in result["regtap"].items()},
        "tapvizier_ok": result["tapvizier"]["tables_of_named_catalogues"]["ok"],
        "vizier_catalogue_ids_returned": found,
        "named_catalogue_ids_found": {label: any(cid in k for k in found) for label, cid in CATALOG_IDS.items()}}
    result["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps(result["summary"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
