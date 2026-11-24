"""R108 gaia lane: run one command under /usr/bin/time and append a JSON line to the gaia lane command log.

Purpose: provenance for every command executed in the gaia lane (R108 rule: each command is recorded as
{cmd, rc, wall_s, maxrss_kB, started_utc, cwd, log} in ~/Downloads/htt_r108/logs/gaia_COMMANDS.jsonl, with its combined
stdout/stderr in ~/Downloads/htt_r108/logs/gaia_<tag>.log). Same mechanics as scripts/r108/radio_cmdlog.py.
Inputs: the command after "--"; no data inputs. Units: seconds, kB.
Usage (repo root):
    python3 -m scripts.r108.gaia_cmdlog --tag frame_leakage_review2 -- .venv/bin/python -m scripts.r108.gaia_frame_leakage ...
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

from scripts.r108.radio_cmdlog import TIME_FMT, parse_time_line, signal_of

LOGDIR = Path.home() / "Downloads/htt_r108/logs"
JSONL = LOGDIR / "gaia_COMMANDS.jsonl"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" not in argv:
        raise SystemExit("usage: gaia_cmdlog --tag TAG [--note TEXT] -- command ...")
    cut = argv.index("--")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--note", default=None)
    a = ap.parse_args(argv[:cut])
    cmd = argv[cut + 1:]
    LOGDIR.mkdir(parents=True, exist_ok=True)
    log = LOGDIR / f"gaia_{a.tag}.log"
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    with tempfile.NamedTemporaryFile("r+", suffix=".time", delete=False) as tf:
        tpath = tf.name
    with open(log, "a") as lf:
        lf.write(f"\n### started_utc={started} cwd={os.getcwd()}\n### cmd={shlex.join(cmd)}\n")
        lf.flush()
        proc = subprocess.run(["/usr/bin/time", "-f", TIME_FMT, "-o", tpath, *cmd], stdout=lf, stderr=subprocess.STDOUT)
    ttext = Path(tpath).read_text()
    rec = parse_time_line(ttext) or dict(cmd=shlex.join(cmd), rc=proc.returncode, wall_s=None, maxrss_kB=None)
    sig = signal_of(ttext)
    if sig is not None:  # /usr/bin/time reports %x = 0 for a signalled child
        rec["rc"] = -sig
        rec["terminated_by_signal"] = sig
    os.unlink(tpath)
    rec["cmd"] = shlex.join(cmd)
    rec["started_utc"] = started
    rec["cwd"] = os.getcwd()
    rec["log"] = str(log)
    if a.note:
        rec["note"] = a.note
    with open(JSONL, "a") as jf:
        jf.write(json.dumps(rec) + "\n")
    print(json.dumps(rec))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
