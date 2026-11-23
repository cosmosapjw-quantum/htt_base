"""Recover immutable BASS inputs and hash-qualified public HYREC atomic tables.

No checkout/worktree, recursive download, overwrite, or scientific promotion.
Default is git-only. --fetch-atomic requests five bounded HTTPS downloads.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
MAX_TABLE_BYTES = 4_000_000


def install_exact(destination: Path, payload: bytes, expected: str):
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        return {"status": "HASH_MISMATCH", "sha256": actual, "expected_sha256": expected,
                "bytes": len(payload), "installed": False}
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise ValueError(f"refusing nonregular destination: {destination}")
        if hashlib.sha256(destination.read_bytes()).hexdigest() != expected:
            raise ValueError(f"refusing to overwrite differing input: {destination}")
        state = "EXACT_PRESENT"
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as handle:
            handle.write(payload)
        state = "EXACT_BYTES_RECOVERED"
    return {"status": state, "sha256": actual, "expected_sha256": expected,
            "bytes": len(payload), "installed": True, "path": str(destination)}


def recover(config: dict, bass_repo: Path, output: Path, fetch_atomic=False):
    result = {"schema": "htt.r101.legacy_recovery_receipt/1", "inputs": [],
              "baselines": [], "physics_qualified": False,
              "qualification_note": "Identity recovery only. H is normal-frame expansion; historic tilted chemistry clock is conditional."}
    for commit in config["baseline_commits"]:
        p = subprocess.run(["git", "-C", str(bass_repo), "cat-file", "-e", commit+"^{commit}"], capture_output=True)
        result["baselines"].append({"commit": commit, "available": p.returncode == 0,
                                    "error": p.stderr.decode(errors="replace") if p.returncode else None})
    for item in config["git_files"]:
        p = subprocess.run(["git", "-C", str(bass_repo), "show", config["bass_commit"]+":"+item["path"]], capture_output=True)
        entry = {"source": "git", "commit": config["bass_commit"], "member": item["path"]}
        if p.returncode:
            entry.update(status="BLOCKED_SOURCE", error=p.stderr.decode(errors="replace"))
        else:
            entry.update(install_exact(output / "bass" / Path(item["path"]).name, p.stdout, item["sha256"]))
        result["inputs"].append(entry)
    for item in config["atomic_tables"]:
        url = f'https://raw.githubusercontent.com/{config["hyrec_repo"]}/{config["hyrec_commit"]}/{item["name"]}'
        entry = {"source": "https", "url": url, "expected_sha256": item["sha256"], "name": item["name"]}
        dest = output / "hyrec_atomic" / item["name"]
        if dest.exists():
            if dest.is_symlink() or not dest.is_file():
                raise ValueError(f"refusing nonregular destination: {dest}")
            entry.update(install_exact(dest, dest.read_bytes(), item["sha256"]))
        elif not fetch_atomic:
            entry.update(status="DOWNLOAD_PREPARED", max_bytes=MAX_TABLE_BYTES)
        else:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "HTT-R101-recovery"})
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status != 200:
                        entry.update(status="DEFERRED_EXTERNAL", http_status=response.status)
                    else:
                        size = response.headers.get("Content-Length")
                        if size is not None and int(size) > MAX_TABLE_BYTES:
                            raise ValueError("declared download exceeds per-table byte budget")
                        payload = response.read(MAX_TABLE_BYTES+1)
                        if len(payload) > MAX_TABLE_BYTES:
                            raise ValueError("download exceeds per-table byte budget")
                        entry.update(install_exact(dest, payload, item["sha256"]))
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                entry.update(status="BLOCKED_NETWORK", error=str(exc))
        result["inputs"].append(entry)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bass-repo", type=Path, default=Path.home()/"bass")
    ap.add_argument("--output", type=Path, default=ROOT/"data/external/r101_legacy_recovery")
    ap.add_argument("--config", type=Path, default=ROOT/"configs/r101/legacy_recovery.json")
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--fetch-atomic", action="store_true")
    args = ap.parse_args(argv)
    result = recover(json.loads(args.config.read_text()), args.bass_repo, args.output, args.fetch_atomic)
    text = json.dumps(result, indent=2, allow_nan=False)+"\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text)
    print(text, end="")
    return 0 if all(x.get("installed", False) or x["status"] == "DOWNLOAD_PREPARED" for x in result["inputs"]) else 3


if __name__ == "__main__":
    raise SystemExit(main())
