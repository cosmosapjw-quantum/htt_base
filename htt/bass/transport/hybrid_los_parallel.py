"""Process-parallel evaluation of ``hybrid_los_transfer.los_sky`` over chunks of directions (R108 S7).

Rays are independent in the formal solution: every direction carries its own geodesic,
redshift, Sachs rotation and depth accumulation, and the per-node source synthesis is
evaluated per direction.  Splitting the directions into chunks and evaluating them in
separate processes therefore reproduces the single-process maps; the R108 test and
S7_LOS_PERFORMANCE.json measure the difference (required <= 1e-12 relative).

The closed Cartesian ell <= 2 source synthesis suggested by the R107 handoff is not used:
on coupled-solver histories the moving-electron emission beyond ell = 2 has relative
norm ~1e-5 (> the 1e-8 truncation bound of ``los_sky``), so the source needs ell <= 3.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from bass.transport.hybrid_los_transfer import LosSky, LosSourceHistory, los_sky

__all__ = ["los_sky_parallel"]


def _chunk(args) -> LosSky:
    history, directions, kwargs = args
    return los_sky(history, directions, **kwargs)


def los_sky_parallel(history: LosSourceHistory, directions: np.ndarray, *, workers: int | None = None,
                     chunks: int | None = None, **kwargs) -> LosSky:
    """``los_sky`` over ``chunks`` direction blocks in ``workers`` processes; same arguments otherwise."""
    d = np.asarray(directions, dtype=np.float64)
    if d.ndim != 2 or d.shape[1] != 3:
        raise ValueError("directions must have shape (n, 3)")
    n_workers = int(workers or os.cpu_count() or 1)
    n_chunks = int(chunks or 4 * n_workers)
    if n_workers <= 1 or d.shape[0] < 2 * n_chunks:
        sky = los_sky(history, d, **kwargs)
        diag = dict(sky.diagnostics)
        diag.update(workers=1, chunks=1, chunk_seconds_sum=float(diag["seconds"]))
        return LosSky(directions=sky.directions, T=sky.T, Q=sky.Q, U=sky.U, V=sky.V, diagnostics=diag)
    t0 = time.perf_counter()
    blocks = [b for b in np.array_split(np.arange(d.shape[0]), n_chunks) if b.size]
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        parts = list(ex.map(_chunk, [(history, d[b], kwargs) for b in blocks]))
    diag = dict(parts[0].diagnostics)
    diag.update(n_directions=int(d.shape[0]), seconds=time.perf_counter() - t0, workers=n_workers,
                chunks=len(blocks), min_total_depth=min(p.diagnostics["min_total_depth"] for p in parts),
                initial_state_weight_max=max(p.diagnostics["initial_state_weight_max"] for p in parts),
                chunk_seconds_sum=float(sum(p.diagnostics["seconds"] for p in parts)))
    for key in ("source_ell_max", "max_source_truncation", "top_shell_relative_norm"):
        if any(p.diagnostics[key] != diag[key] for p in parts):
            raise RuntimeError(f"chunk diagnostics disagree on {key}")
    return LosSky(directions=d, T=np.concatenate([p.T for p in parts]), Q=np.concatenate([p.Q for p in parts]),
                  U=np.concatenate([p.U for p in parts]), V=np.concatenate([p.V for p in parts]), diagnostics=diag)
