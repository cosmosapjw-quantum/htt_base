"""R108 FRAME lane: receipt lines for pre-existing inputs (review-2 RCPT-1).

Purpose
    Every raw file the FRAME lane reads that was not fetched in R108 gets a 'pre_existing_input' line in
    ~/Downloads/htt_r108/frame/RECEIPTS.jsonl, so that an audit of the lane's receipts covers every raw input.
    Repository result files from earlier rounds that the lane reads get a 'pre_existing_repository_input'
    line. Each line carries path, SHA-256, bytes, mtime, the lane scripts that read the file, the R108
    outputs that record the file's SHA-256 (with a match flag), sidecar acquisition manifests next to the
    file (with their recorded SHA-256 when present) and repository files that record the same SHA-256
    (git grep; the originating round's manifest or receipt). Nothing is downloaded. Lines are appended
    only for a (path, sha256) pair that has no line yet (idempotent). Files fetched in R108 already have
    fetch receipts and are not listed here.

Inputs
    the lane's input lists below (the constants of frame_registry_build.py, frame_cf4_joint.py,
    frame_lie_flux.py, frame_w1tf_joint.py) and the R108 FRAME outputs that record input SHA-256.

Usage
    PYTHONPATH=.:htt:htt/src .venv/bin/python -m scripts.r108.frame_input_receipts \
        --receipts ~/Downloads/htt_r108/frame/RECEIPTS.jsonl
    Deterministic apart from the recorded_at_utc stamp.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path

from scripts.r108.common import OUT_DIR, REPO, sha256_file

HOME = Path.home()
RECEIPTS = HOME / "Downloads/htt_r108/frame/RECEIPTS.jsonl"
PUB = REPO / "docs/research_program/observational_publication_20261015"
FRAME_OUTPUTS = [OUT_DIR / "FRAME" / n for n in ("CATALOGUE_FRAME_REGISTRY.json", "CF4_BULK_HDIPOLE_JOINT.json",
                                                 "LIE_FLUX_FRAMES.json", "W1TF_BULK_HDIPOLE_JOINT.json",
                                                 "W1TF_CATALOGUE_PROBE.json")]
_SIDECAR_SUFFIXES = (".manifest.json", ".download.json")
_DIR_MANIFESTS = ("manifest.jsonl", "MANIFEST_MD5.csv", "MANIFEST.json", "SHA256SUMS", "SHA256SUMS.txt")


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lane_inputs() -> dict[str, dict]:
    """{path: {"kind", "read_by"}} for every pre-existing input of the FRAME lane scripts."""
    from scripts.r108 import frame_registry_build as frb
    out: dict[str, dict] = {}

    def add(p: Path, kind: str, script: str) -> None:
        e = out.setdefault(str(Path(p)), {"kind": kind, "read_by": []})
        if script not in e["read_by"]:
            e["read_by"].append(script)

    reg = "scripts/r108/frame_registry_build.py"
    for p in (frb.CF4_DIR / "ReadMe", frb.CF4_DIR / "table4.dat", frb.SIXDF_DR3_DIR / "ReadMe",
              frb.SIXDF_DR3_DIR / "6dfgs.dat.gz", frb.SIXDFV_TABLE1, frb.NVSS_README, frb.ICRF3_SX, frb.COMMANDER,
              frb.QUAIA):
        add(p, "pre_existing_input", reg)
    cf4 = "scripts/r108/frame_cf4_joint.py"
    raw_cf4 = Path("/mnt/extdrive/workdir/raw/cf4_full")  # scripts.r97.cf4_genealogy_and_partial_id.RAW_CF4
    for n in ("table3.dat", "table4.dat", "ReadMe"):
        add(raw_cf4 / n, "pre_existing_input", cf4)
    for p in (REPO / "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz",
              PUB / "R98_FOURTH_RESEARCH_CYCLE_20261123/CF4_P1_RESULTS.json",
              PUB / "R105_RESEARCH_20261124/CF4_H05_AXES.json",
              PUB / "H03_20261016/src/h03_tomography.py"):
        add(p, "pre_existing_repository_input", cf4)
    lie = "scripts/r108/frame_lie_flux.py"
    for p in (PUB / "R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_RESULT.json",
              PUB / "R105_RESEARCH_20261124/RADIO_MATCHED_REFITS.json",
              PUB / "R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json",
              PUB / "R105_RESEARCH_20261124/CROSS_RESULTS.json"):
        add(p, "pre_existing_repository_input", lie)
    w1 = "scripts/r108/frame_w1tf_joint.py"
    for p in (PUB / "R105_RESEARCH_20261124/CF4_H05_AXES.json", PUB / "H03_20261016/src/h03_tomography.py"):
        add(p, "pre_existing_repository_input", w1)
    return out


def _recorded_in(path: str, sha: str) -> list[dict]:
    """R108 FRAME outputs that record this path with a SHA-256 (match flag)."""
    rp = str(Path(path).resolve())
    hits = []

    def walk(obj, where, out_name):
        if isinstance(obj, dict):
            p, s = obj.get("path"), obj.get("sha256")
            if isinstance(p, str) and isinstance(s, str):
                cand = Path(p) if Path(p).is_absolute() else REPO / p
                if str(cand.resolve()) == rp:
                    hits.append({"output": out_name, "field": where, "sha256_recorded": s, "matches": s == sha})
            for k, v in obj.items():
                walk(v, f"{where}/{k}", out_name)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{where}[{i}]", out_name)

    for f in FRAME_OUTPUTS:
        if f.exists():
            walk(json.loads(f.read_text()), "", str(f.relative_to(REPO)))
    return hits


def _sidecars(p: Path, sha: str) -> list[dict]:
    out = []
    for suf in _SIDECAR_SUFFIXES:
        s = Path(str(p) + suf)
        if s.exists():
            rec = {"path": str(s), "sha256_of_sidecar": sha256_file(s)}
            try:
                d = json.loads(s.read_text())
                if isinstance(d, dict):
                    rec.update({k: d.get(k) for k in ("url", "final_url", "fetched_utc", "sha256", "bytes") if k in d})
                    if "sha256" in d:
                        rec["sha256_matches"] = d["sha256"] == sha
            except (ValueError, UnicodeDecodeError):
                pass
            out.append(rec)
    for name in _DIR_MANIFESTS:
        s = p.parent / name
        if s.exists() and s != p:
            text = s.read_text(errors="replace")
            out.append({"path": str(s), "sha256_of_sidecar": sha256_file(s), "lists_file_name": p.name in text,
                        "lists_sha256": sha in text})
    return out


def _git_pointers(sha: str, limit: int = 6) -> list[str]:
    r = subprocess.run(["git", "grep", "-l", sha, "--", "docs", "scripts", "htt"], cwd=REPO, capture_output=True,
                       text=True, check=False, timeout=120)
    hits = [h for h in r.stdout.splitlines() if h.strip() and "R108_LOS_ATLAS_DATA_20261124" not in h]
    key = ("MANIFEST", "RECEIPT", "INVENTORY", "SHA256SUMS", "INTAKE")
    hits.sort(key=lambda h: (not any(k in Path(h).name.upper() for k in key), h))
    return hits[:limit]


def _git_tracked(p: Path) -> dict:
    try:
        rel = str(p.resolve().relative_to(REPO))
    except ValueError:
        return {}
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=REPO, capture_output=True,
                             check=False).returncode == 0
    status = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=REPO, capture_output=True, text=True,
                            check=False).stdout.strip()
    return {"repo_path": rel, "git_tracked": tracked, "git_status": status or "clean"}


def receipt_line(path: str, kind: str, read_by: list[str]) -> dict:
    p = Path(path)
    sha = sha256_file(p)
    st = p.stat()
    line = {"kind": kind, "id": f"{kind}:{p.name}", "name": "pre-existing input, not fetched in R108",
            "path": str(p), "sha256": sha, "bytes": int(st.st_size),
            "mtime_utc": _dt.datetime.fromtimestamp(st.st_mtime, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "read_by": sorted(read_by), "recorded_in": _recorded_in(path, sha),
            "sidecar_manifests": _sidecars(p, sha), "origin_pointers_git_grep_sha256": _git_pointers(sha),
            "recorded_at_utc": now_utc(), "fetched_at_utc": None, "status": "pre_existing"}
    line.update(_git_tracked(p))
    return line


def existing_pairs(receipts: Path) -> set[tuple[str, str]]:
    if not receipts.exists():
        return set()
    out = set()
    for ln in receipts.read_text().splitlines():
        if ln.strip():
            r = json.loads(ln)
            if str(r.get("kind", "")).startswith("pre_existing"):
                out.add((r["path"], r["sha256"]))
    return out


def record_pre_existing(receipts: Path, entries: dict[str, dict]) -> list[dict]:
    """Append one line per (path, sha256) without a line yet; return the lines for every entry (new or existing)."""
    have = existing_pairs(receipts)
    lines, new = [], []
    for path, e in sorted(entries.items()):
        line = receipt_line(path, e["kind"], e["read_by"])
        lines.append(line)
        if (line["path"], line["sha256"]) not in have:
            new.append(line)
            have.add((line["path"], line["sha256"]))
    if new:
        receipts.parent.mkdir(parents=True, exist_ok=True)
        with receipts.open("a") as fh:
            for line in new:
                fh.write(json.dumps(line, sort_keys=True) + "\n")
    for line in lines:
        line["appended_now"] = line in new
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--receipts", type=Path, default=RECEIPTS)
    a = ap.parse_args(argv)
    lines = record_pre_existing(a.receipts.expanduser(), lane_inputs())
    summary = [{"path": l["path"], "kind": l["kind"], "sha256": l["sha256"][:16], "appended_now": l["appended_now"],
                "recorded_in_match": [r["matches"] for r in l["recorded_in"]],
                "sidecars": [s["path"] for s in l["sidecar_manifests"]],
                "origin": l["origin_pointers_git_grep_sha256"][:2]} for l in lines]
    print(json.dumps({"receipts": str(a.receipts), "n": len(lines),
                      "appended": sum(l["appended_now"] for l in lines), "lines": summary}, indent=1))
    bad = [l["path"] for l in lines if any(not r["matches"] for r in l["recorded_in"])]
    if bad:
        print(json.dumps({"sha_mismatch_with_recorded_outputs": bad}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
