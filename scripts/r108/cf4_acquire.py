"""R108 lane cf4: receipted catalogue/archive acquisition through astroquery and pyvo (D01-D05).

Purpose
    Acquire the SQ-CF4 / H02 inputs named in scripts/r107_cloud/acquisition.py ITEMS:
    D01 Cosmicflows-3 (VizieR J/AJ/152/50 table2, table3), D02 6dFGSv (J/MNRAS/445/2677 table1),
    D03 6dFGS DR3 (VII/259 6dfgs) plus the 6dFGSv 2MASS photometry (J/MNRAS/443/1231 FPsample,
    Ktot = 2MASS k_m_ext) because VII/259 carries no K magnitude, D04 the 2M++ portal page and the
    files it names.  Catalogue access goes through astroquery.vizier (a reachable VizieR mirror set
    with VizierClass(vizier_server=...)) and pyvo (TAPVizieR, RegTAP); https files go through the
    R107 fetcher (scripts.r107_cloud.acquisition.fetch_file: https-only redirects, byte cap, never
    overwrite).  The CDS ftp tree returned HTML 404 pages on 2026-11-24, so no ReadMe is fetched from
    there; the CF3 ReadMe used for row-count checks is the earlier CDS copy kept under
    .agent-harness/runs/R9-SELECTED-LAW-20260913/ (SHA-256 recorded by the analysis scripts).

Inputs
    Network services only.  Each saved table is the raw VOTable byte stream returned by the service
    (no re-serialisation); its SHA-256, byte count, row count, service URL, query payload and, for TAP,
    the job id are appended to <directory>/RECEIPTS.jsonl (fields id,name,url,final_url,bytes,sha256,
    status,fetched_at_utc plus route,service,query,rows,job_id).

Units
    None (bytes, rows).

Usage (repo root, PYTHONPATH=.:htt:htt/src)
    python -m scripts.r108.cf4_acquire vizier --item D01 --source J/AJ/152/50/table3 --name cf3_table3.vot \
        --directory ~/Downloads/htt_r108/cf4 --servers vizier.cfa.harvard.edu vizier.idia.ac.za
    python -m scripts.r108.cf4_acquire tap --item D01 --name cf3_table3_tap.vot --query 'SELECT * FROM "J/AJ/152/50/table3"'
    python -m scripts.r108.cf4_acquire https --item D04 --name index.html --url https://...  --max-bytes 2000000
    python -m scripts.r108.cf4_acquire registry --item D01 --ivoid ivo://cds.vizier/j/aj/152/50 --name regtap_D01.vot

Deterministic: no random numbers.  Downloaded files are parsed only (never executed).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import io
import json
import re
import sys
import time
from pathlib import Path

RECEIPTS = "RECEIPTS.jsonl"
DEFAULT_DIR = Path.home() / "Downloads/htt_r108/cf4"
TAPVIZIER = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _append(directory: Path, rec: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory / RECEIPTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def _new_target(directory: Path, item: str, name: str) -> Path:
    if Path(name).name != name or name in {".", ".."}:
        raise ValueError(f"invalid basename {name!r}")
    sub = directory / item
    sub.mkdir(parents=True, exist_ok=True)
    target = sub / name
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"refusing to overwrite raw data {target}")
    return target


def votable_rows(data: bytes) -> dict:
    """Parse a VOTable byte stream (data only); return per-table row counts and the QUERY_STATUS text."""
    from astropy.io.votable import parse

    txt = data.decode("utf-8", "replace")
    status = re.findall(r'<INFO name="QUERY_STATUS" value="([^"]*)"[^>]*>([^<]*)', txt)
    vot = parse(io.BytesIO(data), verify="ignore")
    tables = {}
    for res in vot.iter_tables():
        tables[res.name or res.ID] = int(len(res.array))
    return dict(tables=tables, query_status=[[a, b.strip()[:400]] for a, b in status],
                stdb_error="STDB_ERR" in txt)


def cmd_vizier(a) -> int:
    from astroquery import cache_conf
    from astroquery.vizier import VizierClass
    import astroquery

    cache_conf.cache_active = False  # every answer is a fresh server response
    directory = a.directory.expanduser()
    target = _new_target(directory, a.item, a.name)
    last = None
    for attempt in range(a.attempts):
        for server in a.servers:
            t0 = time.time()
            rec = dict(id=a.item, name=a.name, route="astroquery.vizier", astroquery_version=astroquery.__version__,
                       service=f"https://{server}/viz-bin/votable", source=a.source, columns=a.columns,
                       attempt=attempt, started_utc=_now())
            try:
                v = VizierClass(vizier_server=server, columns=list(a.columns), row_limit=-1, timeout=a.timeout)
                payload = v._args_to_payload(catalog=a.source)
                resp = v.get_catalogs_async(a.source)
                data = resp.content
                rec.update(url=rec["service"], final_url=resp.url, http_status=resp.status_code, query=payload,
                           bytes=len(data), sha256=_sha(data), wall_s=round(time.time() - t0, 2))
                info = votable_rows(data)
                rec.update(rows=info["tables"], query_status=info["query_status"])
                if resp.status_code != 200 or info["stdb_error"] or not info["tables"]:
                    rec.update(status="FAILED_SERVICE_ERROR", fetched_at_utc=_now())
                    _append(directory, rec)
                    last = rec
                    continue
                target.write_bytes(data)
                rec.update(status="FETCHED", path=str(target), fetched_at_utc=_now())
                _append(directory, rec)
                print(json.dumps(rec, sort_keys=True, default=str))
                return 0
            except Exception as exc:  # noqa: BLE001 - recorded, then the next mirror is tried
                rec.update(status="FAILED_EXCEPTION", error=repr(exc)[:600], wall_s=round(time.time() - t0, 2),
                           fetched_at_utc=_now(), bytes=0, sha256=None, url=rec["service"], final_url=None)
                _append(directory, rec)
                last = rec
        time.sleep(a.backoff)
    print(json.dumps(dict(last or {}, final="FAILED_ALL_ATTEMPTS"), sort_keys=True, default=str))
    return 2


def cmd_tap(a) -> int:
    import pyvo
    import requests

    directory = a.directory.expanduser()
    target = _new_target(directory, a.item, a.name)
    rec = dict(id=a.item, name=a.name, route="pyvo.dal.TAPService", pyvo_version=pyvo.__version__, service=a.service,
               url=a.service, query=a.query, started_utc=_now())
    t0 = time.time()
    session = requests.Session()
    session.request = _with_timeout(session.request, a.timeout)
    try:
        svc = pyvo.dal.TAPService(a.service, session=session)
        job = svc.submit_job(a.query, maxrec=a.maxrec)
        rec["job_id"], rec["job_url"] = job.job_id, job.url
        job.run()
        job.wait(phases=["COMPLETED", "ERROR", "ABORTED"], timeout=a.timeout)
        job.raise_if_error()
        resp = session.get(job.result_uri, timeout=a.timeout)
        resp.raise_for_status()
        data = resp.content
        info = votable_rows(data)
        target.write_bytes(data)
        rec.update(final_url=job.result_uri, bytes=len(data), sha256=_sha(data), rows=info["tables"],
                   status="FETCHED", path=str(target), wall_s=round(time.time() - t0, 2), fetched_at_utc=_now())
        try:
            job.delete()
        except Exception:  # noqa: BLE001
            pass
        _append(directory, rec)
        print(json.dumps(rec, sort_keys=True, default=str))
        return 0
    except Exception as exc:  # noqa: BLE001
        rec.update(status="FAILED_EXCEPTION", error=repr(exc)[:600], wall_s=round(time.time() - t0, 2),
                   fetched_at_utc=_now(), bytes=0, sha256=None, final_url=None)
        _append(directory, rec)
        print(json.dumps(rec, sort_keys=True, default=str))
        return 2


def _with_timeout(fn, timeout):
    def wrapped(method, url, **kw):
        kw.setdefault("timeout", timeout)
        return fn(method, url, **kw)
    return wrapped


def cmd_registry(a) -> int:
    """RegTAP metadata (tables, descriptions, interfaces) for VizieR ivoids, saved as the raw VOTable answer."""
    import pyvo
    import requests
    from pyvo import registry

    directory = a.directory.expanduser()
    target = _new_target(directory, a.item, a.name)
    ids = ",".join("'" + i.lower() + "'" for i in a.ivoid)
    query = (f"SELECT t.ivoid, t.table_name, t.table_description, t.nrows FROM rr.res_table AS t "
             f"WHERE t.ivoid IN ({ids})")
    rec = dict(id=a.item, name=a.name, route="RegTAP sync at pyvo.registry.regtap.REGISTRY_BASEURL (raw bytes via requests)",
               service=registry.regtap.REGISTRY_BASEURL,
               url=registry.regtap.REGISTRY_BASEURL + "/sync", query=query, started_utc=_now())
    t0 = time.time()
    try:
        resp = requests.post(registry.regtap.REGISTRY_BASEURL + "/sync",
                             data=dict(REQUEST="doQuery", LANG="ADQL", QUERY=query), timeout=a.timeout)
        resp.raise_for_status()
        data = resp.content
        info = votable_rows(data)
        target.write_bytes(data)
        rec.update(final_url=resp.url, bytes=len(data), sha256=_sha(data), rows=info["tables"], status="FETCHED",
                   path=str(target), wall_s=round(time.time() - t0, 2), fetched_at_utc=_now(),
                   pyvo_version=pyvo.__version__)
    except Exception as exc:  # noqa: BLE001
        rec.update(status="FAILED_EXCEPTION", error=repr(exc)[:600], fetched_at_utc=_now(), bytes=0, sha256=None,
                   final_url=None)
    _append(directory, rec)
    print(json.dumps(rec, sort_keys=True, default=str))
    return 0 if rec["status"] == "FETCHED" else 2


def cmd_https(a) -> int:
    """One https file through the R107 fetcher (https-only redirects, byte cap, never overwrite)."""
    from scripts.r107_cloud.acquisition import fetch_file

    directory = a.directory.expanduser()
    spec = dict(name=a.name, url=a.url, expected_bytes=a.expected_bytes, sha256=a.sha256)
    t0 = time.time()
    try:
        rec = dict(id=a.item, route="scripts.r107_cloud.acquisition.fetch_file",
                   **fetch_file(spec, directory / a.item, a.max_bytes, timeout=a.timeout))
    except Exception as exc:  # noqa: BLE001
        rec = dict(id=a.item, name=a.name, url=a.url, final_url=None, bytes=0, sha256=None,
                   route="scripts.r107_cloud.acquisition.fetch_file", status="FAILED_EXCEPTION",
                   error=repr(exc)[:600], fetched_at_utc=_now())
    rec["wall_s"] = round(time.time() - t0, 2)
    _append(directory, rec)
    print(json.dumps(rec, sort_keys=True, default=str))
    return 0 if rec["status"] in ("FETCHED", "REUSED_EXISTING", "REUSED_UNVERIFIED") else 2


def cmd_probe(a) -> int:
    """DNS resolution and a TCP connect to port 443 for each host (no request sent); one receipt line per host."""
    import socket

    directory = a.directory.expanduser()
    bad = 0
    for host in a.hosts:
        t0 = time.time()
        rec = dict(id=a.item, name=f"probe:{host}", url=f"https://{host}/", final_url=None, bytes=0, sha256=None,
                   route="socket.getaddrinfo + socket.create_connection(443)", started_utc=_now())
        try:
            canon, aliases, addrs = socket.gethostbyname_ex(host)
            rec.update(dns_canonical=canon, dns_aliases=aliases, dns_addresses=addrs)
        except OSError as exc:
            rec.update(status="FAILED_DNS", error=repr(exc)[:300], fetched_at_utc=_now())
            _append(directory, rec)
            bad += 1
            continue
        try:
            with socket.create_connection((host, 443), timeout=a.timeout):
                rec.update(status="TCP_CONNECTED")
        except OSError as exc:
            rec.update(status="FAILED_TCP_CONNECT", error=repr(exc)[:300])
            bad += 1
        rec.update(wall_s=round(time.time() - t0, 2), fetched_at_utc=_now())
        _append(directory, rec)
        print(json.dumps(rec, sort_keys=True))
    return 0 if bad == 0 else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("probe")
    pr.add_argument("--item", required=True)
    pr.add_argument("--hosts", nargs="+", required=True)
    pr.add_argument("--directory", type=Path, default=DEFAULT_DIR)
    pr.add_argument("--timeout", type=float, default=20.)
    for name in ("vizier", "tap", "https", "registry"):
        p = sub.add_parser(name)
        p.add_argument("--item", required=True)
        p.add_argument("--name", required=True)
        p.add_argument("--directory", type=Path, default=DEFAULT_DIR)
        p.add_argument("--timeout", type=float, default=300.)
        if name == "vizier":
            p.add_argument("--source", required=True)
            p.add_argument("--columns", nargs="+", default=["**"])
            p.add_argument("--servers", nargs="+", default=["vizier.cfa.harvard.edu", "vizier.idia.ac.za"])
            p.add_argument("--attempts", type=int, default=2)
            p.add_argument("--backoff", type=float, default=20.)
        elif name == "tap":
            p.add_argument("--service", default=TAPVIZIER)
            p.add_argument("--query", required=True)
            p.add_argument("--maxrec", type=int, default=1000000)
        elif name == "https":
            p.add_argument("--url", required=True)
            p.add_argument("--max-bytes", type=int, required=True)
            p.add_argument("--expected-bytes", type=int)
            p.add_argument("--sha256")
        else:
            p.add_argument("--ivoid", nargs="+", required=True)
    a = ap.parse_args(argv)
    return dict(vizier=cmd_vizier, tap=cmd_tap, https=cmd_https, registry=cmd_registry, probe=cmd_probe)[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
