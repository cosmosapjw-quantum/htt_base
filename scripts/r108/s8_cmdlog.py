"""R108 lane s8: run one command under /usr/bin/time and append a JSON line to the lane command log.

Purpose: provenance for every command executed in lane s8 (R108 rule: each command is recorded
as {cmd, rc, wall_s, maxrss_kB, started_utc} in ~/Downloads/htt_r108/logs/s8_COMMANDS.jsonl, with
its combined stdout/stderr in ~/Downloads/htt_r108/logs/s8_<tag>.log).
Inputs: the command after "--"; no data inputs. Units: seconds, kB.
Usage (repo root):
    python -m scripts.r108.s8_cmdlog --tag tau -- python -m scripts.r108.s8_lowz_tau ...
No randomness.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

LOGDIR = Path.home() / "Downloads/htt_r108/logs"
JSONL = LOGDIR / "s8_COMMANDS.jsonl"
TIME_FMT = "%C|rc=%x|wall=%e|maxrss_kB=%M"


def parse_time_line(text: str) -> dict | None:
    """Parse the last '%C|rc=%x|wall=%e|maxrss_kB=%M' line written by /usr/bin/time -f."""
    lines = [ln for ln in text.strip().splitlines() if "|rc=" in ln and "|wall=" in ln]
    if not lines:
        return None
    head, rest = lines[-1].rsplit("|rc=", 1)
    rc, rest = rest.split("|wall=", 1)
    wall, rss = rest.split("|maxrss_kB=", 1)
    return dict(cmd=head, rc=int(rc), wall_s=float(wall), maxrss_kB=int(rss))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" not in argv:
        raise SystemExit("usage: s8_cmdlog --tag TAG -- command ...")
    cut = argv.index("--")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    a = ap.parse_args(argv[:cut])
    cmd = argv[cut + 1:]
    LOGDIR.mkdir(parents=True, exist_ok=True)
    log = LOGDIR / f"s8_{a.tag}.log"
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    with tempfile.NamedTemporaryFile("r+", suffix=".time", delete=False) as tf:
        tpath = tf.name
    with open(log, "a") as lf:
        lf.write(f"\n### started_utc={started} cwd={os.getcwd()}\n### cmd={shlex.join(cmd)}\n")
        lf.flush()
        proc = subprocess.run(["/usr/bin/time", "-f", TIME_FMT, "-o", tpath, *cmd], stdout=lf, stderr=subprocess.STDOUT)
    rec = parse_time_line(Path(tpath).read_text()) or dict(rc=proc.returncode, wall_s=None, maxrss_kB=None)
    os.unlink(tpath)
    rec["cmd"] = shlex.join(cmd)
    rec["started_utc"] = started
    rec["cwd"] = os.getcwd()
    rec["log"] = str(log)
    rec["tag"] = a.tag
    with open(JSONL, "a") as jf:
        jf.write(json.dumps(rec) + "\n")
    print(json.dumps(rec))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
