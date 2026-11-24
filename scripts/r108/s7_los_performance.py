"""R108 S7: line-of-sight performance at Nside 128 (single process versus process-chunked rays).

Trigger: in the S1 atlas the Nside-128 line of sight took 1932-2014 s per 384-cell family
run (S1_ATLAS.json, ten concurrent workers), above the 30-minute handoff threshold.  This
script re-solves the S1 VII_h (+1) ell_max 8 384-cell case with the S1 settings, then
times ``los_sky`` (one process) and ``los_sky_parallel`` (``--workers`` processes) on
HEALPix Nside 128 and reports the maximum map difference (acceptance <= 1e-12 relative)
and the difference of the HEALPix alm to the S1 atlas product of the same run.

Usage: PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 python -m scripts.r108.s7_los_performance --workers 12
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from scripts.r108.common import OUT_DIR, maxrss_mb, sha256_file, solver_identity, write_json
from scripts.r108.s1_family_atlas import CAP, EPSILON, WORK, tag_of


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--nside", type=int, default=128)
    args = ap.parse_args()
    from bass.transport.coupled_einstein_boltzmann import CoupledSolverConfig, solve_coupled_einstein_boltzmann
    from bass.transport.general_lie_stokes import GeneralLieStokesOperator
    from bass.transport.hybrid_los_parallel import los_sky_parallel
    from bass.transport.hybrid_los_transfer import healpix_directions, history_from_coupled_result, los_alm_healpix, los_sky

    identity = solver_identity()
    identity["sources"]["htt/bass/transport/hybrid_los_parallel.py"] = sha256_file(
        Path(__file__).resolve().parents[2] / "htt/bass/transport/hybrid_los_parallel.py")
    op = GeneralLieStokesOperator(8)
    cfg = CoupledSolverConfig(n_cells=384, ell_max=8, n_picard=4, epsilon=EPSILON, handedness=1,
                              max_substep_depth=CAP, record_history=True)
    t0 = time.perf_counter()
    res = solve_coupled_einstein_boltzmann("VII_h", cfg, lie_op=op)
    solve_s = time.perf_counter() - t0
    hist = history_from_coupled_result(res, op=op)
    # source band limit: relative emission norm beyond ell = 2 and ell = 3 (max over nodes), as los_sky measures it
    from bass.transport.hybrid_los_transfer import _ell_norms, _layout

    idx, _ = _layout(hist.ell_max_native)
    norms = [_ell_norms(np.asarray(e), idx) for e in hist.emission]
    total = max(sum(v.values()) for v in norms)
    beyond = {L: max(float(np.sqrt(sum(val for ell, val in v.items() if ell > L) / total)) for v in norms) for L in (2, 3)}
    d = healpix_directions(args.nside)
    t1 = time.perf_counter()
    ref = los_sky(hist, d, max_step=0.02)
    single_s = time.perf_counter() - t1
    par = los_sky_parallel(hist, d, workers=args.workers, max_step=0.02)
    scale = max(float(np.max(np.abs(ref.T))), float(np.max(np.abs(ref.Q))), float(np.max(np.abs(ref.U))))
    diff = max(float(np.max(np.abs(a - b))) for a, b in ((ref.T, par.T), (ref.Q, par.Q), (ref.U, par.U), (ref.V, par.V)))
    lmax = 2 * args.nside
    alm = los_alm_healpix(par, args.nside, lmax)
    atlas_rec = json.loads((WORK / "runs" / f"{tag_of('VII_h', 1, 8, 384)}.json").read_text())
    prod = atlas_rec["products"][f"ns{args.nside}_st0.02"]
    atlas = np.load(prod["npz"])
    alm_diff = {ch: float(np.max(np.abs(alm[ch] - atlas[ch])) / max(float(np.max(np.abs(atlas[ch]))), 1e-300))
                for ch in ("T", "E", "B")}
    write_json(OUT_DIR / "SOLVER" / "S7_LOS_PERFORMANCE.json", {
        "schema": "htt.r108.s7_los_performance.1", "identity": identity, "case": "VII_h +1, ell_max 8, 384 cells, S1 settings",
        "nside": args.nside, "n_rays": int(d.shape[0]), "n_source_nodes": int(hist.N.size), "solve_seconds": solve_s,
        "single_process_seconds": single_s, "parallel_seconds": par.diagnostics["seconds"],
        "parallel_workers": par.diagnostics["workers"], "parallel_chunks": par.diagnostics["chunks"],
        "parallel_chunk_seconds_sum": par.diagnostics["chunk_seconds_sum"], "speedup": single_s / par.diagnostics["seconds"],
        "max_abs_map_difference": diff, "max_relative_map_difference": diff / scale,
        "alm_relative_difference_to_S1_atlas_product": alm_diff, "atlas_npz_sha256": prod["npz_sha256"],
        "atlas_los_seconds_concurrent": prod["los_seconds"], "acceptance": "maps identical to <= 1e-12 relative",
        "accepted": bool(diff / scale <= 1e-12), "maxrss_MB": maxrss_mb(),
        "source_relative_norm_beyond_ell": {str(k): v for k, v in beyond.items()},
        "closed_cartesian_ell_le_2_admissible": bool(beyond[2] <= 1e-8),
        "note": "los_sky fails closed when the emission beyond source_ell_max exceeds 1e-8 of the total"})


if __name__ == "__main__":
    main()
