"""Shared provenance helpers for R108 scripts (input SHA-256, git state, runtime)."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124"

SOLVER_SOURCES = (
    "htt/bass/transport/coupled_einstein_boltzmann.py",
    "htt/bass/transport/hybrid_los_transfer.py",
    "htt/bass/transport/general_lie_stokes.py",
    "htt/bass/transport/moving_collision_stage.py",
    "htt/bass/transport/general_bianchi_transfer.py",
    "htt/bass/recombination/tilted_hyrec.py",
    "htt/bass/recombination/opacity_history.py",
)


def sha256_file(path: str | os.PathLike, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def git_state() -> dict:
    """HEAD, dirty code paths (porcelain, leading status columns kept), their SHA-256 and a hash of git diff HEAD."""

    def run(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=False).stdout

    lines = [ln for ln in run("status", "--porcelain", "-uall", "--", "htt", "scripts", "tests").split("\n") if ln.strip()]
    hashes = {}
    for ln in lines:
        rel = ln[3:].split(" -> ")[-1].strip()
        f = REPO / rel
        if f.is_file() and f.suffix == ".py":
            hashes[rel] = sha256_file(f)
    diff = run("diff", "HEAD", "--", "htt", "scripts", "tests").encode()
    return {"head": run("rev-parse", "HEAD").strip(), "dirty_code_paths": lines, "dirty_code_sha256": hashes,
            "diff_head_sha256": hashlib.sha256(diff).hexdigest()}


def hyrec_identity() -> dict:
    from bass.recombination.tilted_hyrec import DEFAULT_ATOMIC_DIR

    d = Path(DEFAULT_ATOMIC_DIR)
    return {p.name: sha256_file(p) for p in sorted(d.iterdir()) if p.is_file()}


def solver_identity() -> dict:
    return {"sources": {s: sha256_file(REPO / s) for s in SOLVER_SOURCES if (REPO / s).is_file()},
            "hyrec_tables": hyrec_identity(), "git": git_state(),
            "python": platform.python_version(), "machine": platform.machine(),
            "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS")}


def maxrss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def write_json(path: str | os.PathLike, payload: dict) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=1, sort_keys=True, default=_default) + "\n")
    return p


def _default(o):
    import numpy as np

    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, complex):
        return [o.real, o.imag]
    raise TypeError(f"not JSON serialisable: {type(o)}")
