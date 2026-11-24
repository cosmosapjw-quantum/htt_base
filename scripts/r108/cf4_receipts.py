"""R108 lane cf4: verify every receipt in ~/Downloads/htt_r108/cf4/RECEIPTS.jsonl against the bytes on disk and write a
small acquisition summary (per item: fetched files with SHA-256, row counts, failures with their error text, and the
pre-existing inputs the lane read).

Pre-existing inputs (review RCPT-1).  The cf4 scripts (cf4_kband_contrast, cf4_cf3_table3_overlap, cf4_2mpp_field)
read files that R108 did not fetch: the R100 6dFGSv intake, the R104 2MRS velocity grid, the R105 CORAS draws and
donor checkout, the R106 crosstable, the R98/R97 CF4 raw files on /mnt/extdrive and repository reference JSONs.  Each
script accepts --trace-opens LOG; install_open_trace() then records every file the run opens (a sys.addaudithook
'open' hook, inherited by forked workers) as JSON lines.  `--add-pre-existing LOG ...` reads those logs, keeps the
read-only opens of data files (code, interpreter, library and config files, files the same run wrote, the R108 cf4
downloads that already carry a FETCHED receipt, and RECEIPTS.jsonl itself are dropped) and appends one
PRE_EXISTING_INPUT line per (path, sha256) to RECEIPTS.jsonl: path, sha256, bytes, mtime, originating round (from the
path), origin pointers (earlier-round repository records or scripts that already carry the same SHA-256), git
tracking and the R108 scripts that read it.  A line is never rewritten; a changed file gets a new line.

Inputs: RECEIPTS.jsonl (written by scripts.r108.cf4_acquire, scripts.r107_cloud.acquisition, two hand-appended
failure lines for routes outside those tools, and the PRE_EXISTING_INPUT lines written here) and the files it names.
Units: bytes, rows.
Usage (repo root):
  python -B -m scripts.r108.cf4_receipts --add-pre-existing ~/Downloads/htt_r108/cf4/input_trace/*.jsonl
  python -B -m scripts.r108.cf4_receipts --output docs/.../R108_LOS_ATLAS_DATA_20261124/CF4/ACQUISITION.json
Deterministic apart from the recorded_at_utc stamp of new lines.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

from scripts.r108.common import git_state, sha256_file, write_json

DL = Path.home() / "Downloads/htt_r108/cf4"
ROOT = Path(__file__).resolve().parents[2]
OUT_DEFAULT = ROOT / "docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/CF4/ACQUISITION.json"
PRE_ID, PRE_STATUS = "PRE_EXISTING", "PRE_EXISTING_INPUT"
CODE_SUFFIXES = {".py", ".pyc", ".pyo", ".pyd", ".so", ".pth", ".pyi", ".typed"}
SKIP_PREFIXES = ("/usr/", "/proc/", "/sys/", "/dev/", "/etc/", "/lib/", "/lib64/", "/opt/", "/run/", "/snap/")
SKIP_HOME_DIRS = (".astropy", ".cache", ".config", ".local", ".matplotlib", ".ipython", ".numba")
SKIP_PARTS = ("/site-packages/", "/dist-packages/", "/.git/", "/__pycache__/", "/.venv/")
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
ORIGIN_DOCS = ROOT / "docs/research_program/observational_publication_20261015"
ORIGIN_SUFFIXES = (".json", ".jsonl", ".md", ".tsv", ".txt", ".csv", ".py", ".json.gz")
ORIGIN_MAX_BYTES = 60_000_000


# --------------------------------------------------------------------------- open() trace (written by the run itself)

def install_open_trace(log_path, label):
    """Record every file opened by this process (and forked workers) as JSON lines in log_path.

    The first line is a header (label, argv, pid, UTC start); each later line is one distinct (pid, path, mode,
    flags) open event.  Writes go through a pre-opened O_APPEND descriptor, so the hook opens no file itself."""
    log_path = Path(log_path).expanduser().resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.write(fd, (json.dumps(dict(trace_header=True, label=label, argv=sys.argv, pid=os.getpid(), cwd=os.getcwd(),
                                  started_utc=_dt.datetime.now(_dt.timezone.utc).isoformat())) + "\n").encode())
    seen: set = set()
    busy = [False]

    def hook(event, args):
        if event != "open" or busy[0] or not args:
            return
        p = args[0]
        if p is None or isinstance(p, int):
            return
        busy[0] = True
        try:
            s = os.path.abspath(os.fsdecode(p))
            mode = args[1] if len(args) > 1 else None
            flags = args[2] if len(args) > 2 else None
            key = (os.getpid(), s, mode, flags)
            if key not in seen:
                seen.add(key)
                os.write(fd, (json.dumps(dict(pid=os.getpid(), path=s, mode=mode, flags=flags)) + "\n").encode())
        except Exception:   # never let tracing change the run
            pass
        finally:
            busy[0] = False

    sys.addaudithook(hook)
    return log_path


def is_write(mode, flags):
    if isinstance(mode, str) and any(c in mode for c in "wax+"):
        return True
    return isinstance(flags, int) and mode is None and bool(flags & WRITE_FLAGS)


def is_data_path(path, home=None, prefixes=None):
    """True for a regular data file: not code, interpreter, library, config or system file."""
    home = str(home or Path.home())
    s = str(path)
    if any(s.endswith(x) for x in CODE_SUFFIXES):
        return False
    if s.startswith(SKIP_PREFIXES) or any(part in s for part in SKIP_PARTS):
        return False
    if any(s.startswith(f"{home}/{d}/") for d in SKIP_HOME_DIRS):
        return False
    for pre in prefixes if prefixes is not None else {sys.prefix, sys.base_prefix, sys.exec_prefix}:
        if pre and pre != "/" and s.startswith(pre.rstrip("/") + "/"):
            return False
    return True


def read_trace(log):
    """(header, read-only data paths, written paths) of one trace log."""
    header, reads, writes = None, [], set()
    for line in Path(log).read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("trace_header"):
            header = header or rec
            continue
        if is_write(rec.get("mode"), rec.get("flags")):
            writes.add(rec["path"])
        else:
            reads.append(rec["path"])
    return header, reads, writes


def originating_round(path):
    """Round label encoded in the path (htt_rNNN download folders, RNNN_ repository folders), else a store label."""
    s = str(path)
    m = re.search(r"/htt_r(\d+)", s)
    if m:
        return f"R{int(m.group(1))}"
    m = re.search(r"/(R\d+)[-_][A-Z0-9]", s)
    if m:
        return m.group(1)
    if s.startswith("/mnt/extdrive/"):
        return "pre-R108 external raw store (/mnt/extdrive); round not encoded in the path"
    return "pre-R108; round not encoded in the path"


def origin_candidates(root=ROOT, max_round=107):
    """Earlier-round record files that may carry an input SHA-256: R<=max_round docs folders and scripts/r<=max_round."""
    out = []
    for d in sorted(ORIGIN_DOCS.glob("R*")):
        m = re.match(r"R(\d+)[-_]", d.name)
        if d.is_dir() and m and int(m.group(1)) <= max_round:
            out += [p for p in sorted(d.rglob("*")) if p.is_file() and str(p).endswith(ORIGIN_SUFFIXES)]
    for d in sorted((root / "scripts").glob("r*")):
        m = re.fullmatch(r"r(\d+)", d.name)
        if d.is_dir() and m and int(m.group(1)) <= max_round:
            out += sorted(d.glob("*.py"))
    return out


def origin_pointers(shas, candidates, limit=5):
    """sha -> up to `limit` repository-relative files (earliest round first) whose text contains that SHA-256."""
    hits = {s: [] for s in shas}
    for p in candidates:
        try:
            if p.stat().st_size > ORIGIN_MAX_BYTES:
                continue
            text = (gzip.open(p, "rt", errors="replace").read() if str(p).endswith(".gz")
                    else p.read_text(errors="replace"))
        except OSError:
            continue
        for s in shas:
            if s in text and len(hits[s]) < limit:
                hits[s].append(str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p))
    return hits


def sibling_records(paths):
    """Run/receipt/manifest JSONs next to the inputs (e.g. a CORAS draw directory's run.json, which carries the
    SHA-256 of every draw file)."""
    out = set()
    for d in {Path(p).parent for p in paths}:
        for q in d.glob("*.json"):
            n = q.name.lower()
            if n == "run.json" or "receipt" in n or "manifest" in n:
                out.add(q)
    return sorted(out)


def git_tracked(path):
    p = Path(path)
    if not p.is_relative_to(ROOT):
        return False
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(p.relative_to(ROOT))], cwd=ROOT,
                       capture_output=True, text=True, check=False)
    return r.returncode == 0


def git_head_blob_matches(path):
    """For a tracked file: does the working-tree content equal the HEAD blob?  None when untracked."""
    p = Path(path)
    if not git_tracked(p):
        return None
    rel = str(p.relative_to(ROOT))
    run = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()
    head = run("rev-parse", f"HEAD:{rel}")
    return bool(head) and head == run("hash-object", rel)


def load_receipts(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()] if Path(path).is_file() else []


def pre_existing_lines(logs, receipts_path, download_dir=DL, candidates=None):
    """New PRE_EXISTING_INPUT receipt lines for the data files read in the traced runs (no line is duplicated)."""
    receipts = load_receipts(receipts_path)
    fetched_sha = {r.get("sha256") for r in receipts if r.get("status") == "FETCHED" and r.get("sha256")}
    have = {(r.get("path"), r.get("sha256")) for r in receipts if r.get("status") == PRE_STATUS}
    reads: dict = {}
    for log in logs:
        header, rd, wr = read_trace(log)
        label = (header or {}).get("label", Path(log).stem)
        for p in rd:
            if p in wr or not is_data_path(p) or not Path(p).is_file():
                continue
            if Path(p).resolve() == Path(receipts_path).resolve():
                continue
            rec = reads.setdefault(p, dict(read_by=set(), trace_logs=set()))
            rec["read_by"].add(label)
            rec["trace_logs"].add(str(Path(log).resolve()))
    rows, covered = [], []
    sha = {p: sha256_file(p) for p in sorted(reads)}
    if candidates is None:
        candidates = origin_candidates() + sibling_records(reads)
    pointers = origin_pointers(sorted(set(sha.values())), candidates)
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    for p in sorted(reads):
        if Path(p).is_relative_to(Path(download_dir)) and sha[p] in fetched_sha:
            covered.append(p)
            continue
        if (p, sha[p]) in have:
            continue
        st = Path(p).stat()
        rows.append(dict(
            id=PRE_ID, status=PRE_STATUS, name=Path(p).name, path=p, sha256=sha[p], bytes=int(st.st_size),
            mtime_utc=_dt.datetime.fromtimestamp(st.st_mtime, _dt.timezone.utc).isoformat(),
            originating_round=originating_round(p), origin_pointers=pointers.get(sha[p], []),
            in_repository=Path(p).is_relative_to(ROOT), git_tracked=git_tracked(p),
            git_head_blob_matches=git_head_blob_matches(p),
            read_by=sorted(reads[p]["read_by"]), trace_logs=sorted(reads[p]["trace_logs"]), recorded_at_utc=now,
            note="not fetched in R108: read from local storage by the R108 cf4 lane (open() audit trace of the run); "
                 "sha256/bytes measured when this line was written; origin_pointers are earlier-round records, "
                 "scripts or run/receipt JSONs next to the file whose text carries the same SHA-256 (empty: none "
                 "found; git_tracked files are versioned by git)"))
    return rows, covered


# --------------------------------------------------------------------------- summary

def summarize(path, directory):
    items: dict = {}
    for line in path.read_text().splitlines():
        rec = json.loads(line)
        it = items.setdefault(rec["id"], dict(fetched=[], failed=[], probes=[], pre_existing=[]))
        if str(rec.get("name", "")).startswith("probe:"):
            it["probes"].append({k: rec.get(k) for k in ("name", "status", "dns_addresses", "dns_canonical", "error",
                                                         "fetched_at_utc")})
            continue
        if rec.get("status") == PRE_STATUS:
            f = Path(rec["path"])
            on_disk = sha256_file(f) if f.is_file() else None
            it["pre_existing"].append(dict({k: rec.get(k) for k in (
                "name", "path", "sha256", "bytes", "originating_round", "origin_pointers", "in_repository",
                "git_tracked", "git_head_blob_matches", "read_by", "recorded_at_utc")}, sha256_on_disk_matches=on_disk == rec.get("sha256")))
            continue
        if rec.get("status") == "FETCHED":
            f = Path(rec["path"]) if rec.get("path") else directory / rec["id"] / rec["name"]
            on_disk = sha256_file(f) if f.is_file() else None
            it["fetched"].append(dict(name=rec["name"], path=str(f), url=rec.get("url"), final_url=rec.get("final_url"),
                                      route=rec.get("route"), query=rec.get("query"), job_id=rec.get("job_id"),
                                      rows=rec.get("rows"), bytes=rec.get("bytes"), sha256=rec.get("sha256"),
                                      sha256_on_disk_matches=on_disk == rec.get("sha256"),
                                      fetched_at_utc=rec.get("fetched_at_utc")))
        else:
            it["failed"].append({k: rec.get(k) for k in ("name", "url", "route", "status", "error", "note", "query",
                                                         "fetched_at_utc")})
    for it in items.values():
        if not it["pre_existing"]:
            del it["pre_existing"]
    return items


def input_coverage(result_dir, receipts):
    """Every input_sha256 entry of the cf4 result JSONs (code files excluded) must match a FETCHED or
    PRE_EXISTING_INPUT receipt SHA-256 (review RCPT-1)."""
    shas = {r.get("sha256") for r in receipts if r.get("status") in ("FETCHED", PRE_STATUS) and r.get("sha256")}
    out = {}
    for f in sorted(Path(result_dir).glob("*.json")):
        if f.name == Path(OUT_DEFAULT).name:
            continue
        d = json.loads(f.read_text())
        ins, paths = d.get("input_sha256") or {}, d.get("input_paths") or {}
        code = {k for k in ins if k == "code" or str(paths.get(k, "")).endswith(".py")}
        missing = {k: v for k, v in ins.items() if k not in code and v not in shas}
        out[f.name] = dict(n_inputs_checked=len(ins) - len(code), missing=missing)
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--directory", type=Path, default=DL)
    p.add_argument("--output", type=Path, default=OUT_DEFAULT)
    p.add_argument("--add-pre-existing", nargs="+", type=Path, default=None, metavar="TRACE_LOG",
                   help="append PRE_EXISTING_INPUT lines for the data files read in these trace logs, then exit")
    a = p.parse_args(argv)
    path = a.directory / "RECEIPTS.jsonl"
    if a.add_pre_existing:
        rows, covered = pre_existing_lines(a.add_pre_existing, path, a.directory)
        with open(path, "a") as fh:
            for r in rows:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
        print(json.dumps(dict(receipts=str(path), appended=len(rows), covered_by_fetch_receipts=len(covered),
                              by_round={k: sum(r["originating_round"] == k for r in rows)
                                        for k in sorted({r["originating_round"] for r in rows})}), indent=1))
        return 0
    items = summarize(path, a.directory)
    pre = [f for it in items.values() for f in it.get("pre_existing", [])]
    coverage = input_coverage(Path(a.output).parent, load_receipts(path))
    payload = dict(schema="htt.r108.cf4.acquisition/2", git=git_state(),
                   script=dict(path=str(Path(__file__).relative_to(ROOT)), sha256=sha256_file(Path(__file__))),
                   classification=dict(label="NUMERICAL", scope="download and input receipts with on-disk SHA-256 "
                                                                 "verification; no scientific claim"),
                   command=" ".join(shlex.quote(x) for x in [sys.executable, "-B", "-m", "scripts.r108.cf4_receipts",
                                                             *sys.argv[1:]]),
                   receipts_path=str(path), receipts_sha256=sha256_file(path), items=items,
                   all_fetched_files_verified=all(f["sha256_on_disk_matches"] for it in items.values()
                                                  for f in it["fetched"]),
                   n_pre_existing_inputs=len(pre),
                   all_pre_existing_inputs_verified=all(f["sha256_on_disk_matches"] for f in pre),
                   result_input_coverage=coverage,
                   all_result_inputs_receipted=all(not v["missing"] for v in coverage.values()))
    write_json(a.output, payload)
    print(json.dumps(dict(output=str(a.output), verified=payload["all_fetched_files_verified"],
                          pre_existing=dict(n=len(pre), verified=payload["all_pre_existing_inputs_verified"]),
                          result_inputs_receipted=payload["all_result_inputs_receipted"],
                          items={k: dict(fetched=len(v["fetched"]), failed=len(v["failed"])) for k, v in items.items()})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
