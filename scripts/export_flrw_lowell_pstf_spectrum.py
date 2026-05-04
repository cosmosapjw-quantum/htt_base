#!/usr/bin/env python3
"""Export a real BASS PSTF FLRW low-ell spectrum archive.

This script runs the existing BASS Python PSTF FLRW pipeline and writes
an ``.npz`` file with the same schema consumed by
``plot_flrw_lowell_camb_comparison.py``:

    ell, k_grid_mpc, cl_tt, cl_ee, cl_te, d_tt, d_ee, d_te

No CAMB transfer functions, fitted calibration constants, analytic
surrogate spectra, or synthetic sources are used.  CAMB remains an
external comparison oracle handled by tests and plotting scripts.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from dataclasses import replace as dc_replace

# Prevent process-level k parallelism from being multiplied by BLAS thread
# pools.  This changes scheduling only; the physics path and tolerances are
# controlled by the pipeline config below.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

REPO_ROOT = Path(__file__).resolve().parents[1]
HTT_ROOT = REPO_ROOT / "htt"
HTT_SRC = HTT_ROOT / "src"
if str(HTT_SRC) not in sys.path:
    sys.path.insert(0, str(HTT_SRC))
if str(HTT_ROOT) not in sys.path:
    sys.path.insert(0, str(HTT_ROOT))

import numpy as np

from bass.los.bianchi_propagator import BianchiTransferFunctions
from bass.species.registry import SpeciesBackgroundRegistry
from bass.spectrum.cl_assembly import (
    CLAssemblyConfig,
    assemble_cl_TT_EE_TE_isotropic_from_grid,
    compute_dl,
)
from bass.spectrum.flrw_pipeline import (
    FLRWPipelineConfig,
    compute_flrw_d_ell,
    compute_flrw_d_ell_linear_probe,
    compute_transfer_function_grid,
)


def _positive_int(value: str) -> int:
    out = int(value)
    if out <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("figures/validation/flrw_lowell_pstf_spectrum.npz"),
        help="output .npz archive path",
    )
    parser.add_argument(
        "--mode",
        choices=("linear-probe", "direct"),
        default="linear-probe",
        help=(
            "linear-probe extracts the linear response with bias subtraction; "
            "direct runs the canonical seed-amplitude path"
        ),
    )
    parser.add_argument("--ell-max", type=int, default=30)
    parser.add_argument("--l-max", type=int, default=30)
    parser.add_argument("--n-k", type=_positive_int, default=65)
    parser.add_argument("--log10-k-min", type=float, default=-4.0)
    parser.add_argument("--log10-k-max", type=float, default=-1.5)
    parser.add_argument(
        "--quadrature",
        choices=("trapezoid", "simpson"),
        default="simpson",
    )
    parser.add_argument("--n-workers", type=int, default=None)
    parser.add_argument("--probe-b-k-sq", type=float, default=1.0)
    parser.add_argument("--rtol", type=float, default=1.0e-6)
    parser.add_argument("--atol", type=float, default=1.0e-9)
    parser.add_argument("--max-step-factor", type=int, default=1000)
    parser.add_argument(
        "--co-evolve-scalar-metric",
        action="store_true",
        help=(
            "opt into native Tier-B MB95 (etak,sigma) coevolution; runtime "
            "routes this path to full-RHS BDF until the scalar-metric IMEX "
            "block is validated"
        ),
    )
    parser.add_argument(
        "--co-evolve-scalar-streaming",
        action="store_true",
        help=(
            "also opt into the MB95 scalar m=0 photon/neutrino "
            "free-streaming recursion; this is a development-envelope "
            "physics path until full-range stability is validated"
        ),
    )
    parser.add_argument(
        "--flrw-source-frame",
        choices=("legacy_newtonian_constraint", "mb95_synchronous_effective"),
        default="legacy_newtonian_constraint",
        help="source frame passed to the FLRW source extractor",
    )
    parser.add_argument(
        "--z-injection",
        type=float,
        default=1089.94,
        help="nominal injection redshift passed to the BASS FLRW pipeline",
    )
    parser.add_argument(
        "--pre-recombination-margin-mpc",
        type=float,
        default=20.0,
        help="η margin subtracted from η(z_injection)",
    )
    parser.add_argument(
        "--superhorizon-x-max-at-start",
        type=float,
        default=None,
        help=(
            "optional per-k resolver enforcing k*eta_initial <= x_max; "
            "disables shared-background k chunking because z_injection "
            "becomes k-dependent"
        ),
    )
    parser.add_argument(
        "--chunk-index",
        type=int,
        default=None,
        help=(
            "compute only one zero-based k-grid chunk and save transfer arrays; "
            "requires --chunk-count"
        ),
    )
    parser.add_argument(
        "--chunk-count",
        type=_positive_int,
        default=None,
        help="number of k-grid chunks used with --chunk-index",
    )
    parser.add_argument(
        "--combine-chunks",
        type=Path,
        nargs="+",
        default=None,
        help=(
            "combine previously exported transfer chunks into a final spectrum "
            "archive; no solver calls are made"
        ),
    )
    return parser


def _metadata_from_args(
    args: argparse.Namespace,
    elapsed_s: float,
    *,
    artifact_kind: str = "spectrum",
) -> dict[str, Any]:
    return {
        "producer": "BASS Python PSTF FLRW low-ell export",
        "artifact_kind": artifact_kind,
        "physics_path": (
            "compute_flrw_d_ell_linear_probe"
            if args.mode == "linear-probe"
            else "compute_flrw_d_ell"
        ),
        "mode": args.mode,
        "ell_max": int(args.ell_max),
        "L_max_tower": int(args.l_max),
        "n_k": int(args.n_k),
        "log10_k_min": float(args.log10_k_min),
        "log10_k_max": float(args.log10_k_max),
        "quadrature": args.quadrature,
        "probe_b_k_sq": float(args.probe_b_k_sq),
        "rtol": float(args.rtol),
        "atol": float(args.atol),
        "max_step_factor": int(args.max_step_factor),
        "co_evolve_scalar_metric": bool(args.co_evolve_scalar_metric),
        "co_evolve_scalar_streaming": bool(args.co_evolve_scalar_streaming),
        "flrw_source_frame": str(args.flrw_source_frame),
        "z_injection": float(args.z_injection),
        "pre_recombination_margin_mpc": float(args.pre_recombination_margin_mpc),
        "superhorizon_x_max_at_start": (
            None
            if args.superhorizon_x_max_at_start is None
            else float(args.superhorizon_x_max_at_start)
        ),
        "n_workers": None if args.n_workers is None else int(args.n_workers),
        "elapsed_seconds": float(elapsed_s),
        "calibration_factor": 1.0,
        "calibration_policy": (
            "fixed at 1.0; no fitted multiplicative CAMB calibration is "
            "applied by this exporter"
        ),
        "comparison_readiness": (
            "spectrum archive is output-ready; statistics-ready only after "
            "the external CAMB TT/EE/TE xfail gate is made strict and passes"
        ),
    }


def _scale_transfer_function(
    tf: BianchiTransferFunctions,
    factor: float,
) -> BianchiTransferFunctions:
    return BianchiTransferFunctions(
        delta_T_m0=tf.delta_T_m0 * factor,
        delta_T_m_plus2=tf.delta_T_m_plus2 * factor,
        delta_T_m_minus2=tf.delta_T_m_minus2 * factor,
        delta_E_m0=tf.delta_E_m0 * factor,
        delta_E_m_plus2=tf.delta_E_m_plus2 * factor,
        delta_E_m_minus2=tf.delta_E_m_minus2 * factor,
        delta_B_all_zero=tf.delta_B_all_zero * factor,
    )


def _compute_transfer_list(
    *,
    species: SpeciesBackgroundRegistry,
    k_grid: np.ndarray,
    pipeline_cfg: FLRWPipelineConfig,
    mode: str,
    probe_b_k_sq: float,
    n_workers: int | None,
) -> list[BianchiTransferFunctions]:
    if mode == "direct":
        return compute_transfer_function_grid(
            species,
            k_grid,
            config=pipeline_cfg,
            bianchi_type="I",
            n_workers=n_workers,
        )

    probe_cfg = dc_replace(
        pipeline_cfg,
        primordial_b_k_sq=float(probe_b_k_sq),
        primordial_b_k_sq_fn=None,
        bias_subtraction=True,
        unit_amplitude_normalization=False,
    )
    raw_diffs = compute_transfer_function_grid(
        species,
        k_grid,
        config=probe_cfg,
        bianchi_type="I",
        n_workers=n_workers,
    )
    inv_probe = 1.0 / float(probe_b_k_sq)
    return [_scale_transfer_function(tf, inv_probe) for tf in raw_diffs]


def _field_stack(
    transfers: list[BianchiTransferFunctions],
    name: str,
) -> np.ndarray:
    return np.stack(
        [np.asarray(getattr(tf, name), dtype=np.float64) for tf in transfers],
        axis=0,
    )


def _transfer_arrays(transfers: list[BianchiTransferFunctions]) -> dict[str, np.ndarray]:
    return {
        name: _field_stack(transfers, name)
        for name in (
            "delta_T_m0",
            "delta_T_m_plus2",
            "delta_T_m_minus2",
            "delta_E_m0",
            "delta_E_m_plus2",
            "delta_E_m_minus2",
            "delta_B_all_zero",
        )
    }


def _decode_metadata(data: dict[str, np.ndarray]) -> dict[str, Any]:
    if "metadata_json" not in data:
        return {}
    raw = data["metadata_json"]
    try:
        text = str(raw.item()) if raw.shape == () else str(raw.ravel()[0])
        decoded = json.loads(text)
    except Exception:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _transfers_from_arrays(data: dict[str, np.ndarray]) -> list[BianchiTransferFunctions]:
    required = _transfer_arrays(
        [
            BianchiTransferFunctions(
                delta_T_m0=np.zeros(1),
                delta_T_m_plus2=np.zeros(1),
                delta_T_m_minus2=np.zeros(1),
                delta_E_m0=np.zeros(1),
                delta_E_m_plus2=np.zeros(1),
                delta_E_m_minus2=np.zeros(1),
                delta_B_all_zero=np.zeros(1),
            )
        ]
    ).keys()
    missing = [name for name in required if name not in data]
    if missing:
        raise ValueError(f"transfer chunk missing fields: {missing}")
    n_k = int(np.asarray(data["delta_T_m0"]).shape[0])
    return [
        BianchiTransferFunctions(
            delta_T_m0=np.asarray(data["delta_T_m0"][i], dtype=np.float64),
            delta_T_m_plus2=np.asarray(data["delta_T_m_plus2"][i], dtype=np.float64),
            delta_T_m_minus2=np.asarray(data["delta_T_m_minus2"][i], dtype=np.float64),
            delta_E_m0=np.asarray(data["delta_E_m0"][i], dtype=np.float64),
            delta_E_m_plus2=np.asarray(data["delta_E_m_plus2"][i], dtype=np.float64),
            delta_E_m_minus2=np.asarray(data["delta_E_m_minus2"][i], dtype=np.float64),
            delta_B_all_zero=np.asarray(data["delta_B_all_zero"][i], dtype=np.float64),
        )
        for i in range(n_k)
    ]


def _assemble_and_write_spectrum(
    *,
    out: Path,
    args: argparse.Namespace,
    k_grid: np.ndarray,
    transfers: list[BianchiTransferFunctions],
    elapsed_s: float,
    metadata_extra: dict[str, Any] | None = None,
) -> None:
    assembly_cfg = CLAssemblyConfig(
        ell_max=int(args.ell_max),
        k_grid=np.asarray(k_grid, dtype=np.float64),
        quadrature=args.quadrature,
    )
    cl_tt, cl_ee, cl_te = assemble_cl_TT_EE_TE_isotropic_from_grid(
        transfers, assembly_cfg
    )
    ell = np.arange(int(args.ell_max) + 1, dtype=np.int64)
    metadata = _metadata_from_args(args, elapsed_s, artifact_kind="spectrum")
    if metadata_extra:
        metadata.update(metadata_extra)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out,
        ell=ell,
        k_grid_mpc=np.asarray(k_grid, dtype=np.float64),
        cl_tt=np.asarray(cl_tt, dtype=np.float64),
        cl_ee=np.asarray(cl_ee, dtype=np.float64),
        cl_te=np.asarray(cl_te, dtype=np.float64),
        d_tt=compute_dl(cl_tt, T_CMB_K=float(assembly_cfg.T_CMB_K)),
        d_ee=compute_dl(cl_ee, T_CMB_K=float(assembly_cfg.T_CMB_K)),
        d_te=compute_dl(cl_te, T_CMB_K=float(assembly_cfg.T_CMB_K)),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    print(out)
    print(json.dumps(metadata, indent=2, sort_keys=True))


def _write_transfer_chunk(
    *,
    out: Path,
    args: argparse.Namespace,
    full_k_grid: np.ndarray,
    chunk_indices: np.ndarray,
    transfers: list[BianchiTransferFunctions],
    elapsed_s: float,
) -> None:
    metadata = _metadata_from_args(args, elapsed_s, artifact_kind="transfer_chunk")
    metadata.update(
        {
            "chunk_index": int(args.chunk_index),
            "chunk_count": int(args.chunk_count),
            "chunk_size": int(chunk_indices.size),
            "k_index_start": int(np.min(chunk_indices)),
            "k_index_stop_exclusive": int(np.max(chunk_indices) + 1),
        }
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out,
        k_grid_mpc=np.asarray(full_k_grid[chunk_indices], dtype=np.float64),
        full_k_grid_mpc=np.asarray(full_k_grid, dtype=np.float64),
        k_indices=np.asarray(chunk_indices, dtype=np.int64),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
        **_transfer_arrays(transfers),
    )
    print(out)
    print(json.dumps(metadata, indent=2, sort_keys=True))


def _combine_chunks(args: argparse.Namespace) -> int:
    assert args.combine_chunks is not None
    loaded = []
    for path in args.combine_chunks:
        data = np.load(path, allow_pickle=True)
        loaded.append((path, {key: np.asarray(data[key]) for key in data.files}))
    if not loaded:
        raise ValueError("no chunks supplied")

    chunk_metadata = [_decode_metadata(data) for _, data in loaded]
    first_metadata = chunk_metadata[0]
    for field in (
        "mode",
        "ell_max",
        "L_max_tower",
        "quadrature",
        "probe_b_k_sq",
        "rtol",
        "atol",
        "max_step_factor",
        "co_evolve_scalar_metric",
        "co_evolve_scalar_streaming",
        "flrw_source_frame",
        "z_injection",
        "pre_recombination_margin_mpc",
        "superhorizon_x_max_at_start",
        "n_k",
    ):
        if field in first_metadata:
            attr = "l_max" if field == "L_max_tower" else field
            setattr(args, attr, first_metadata[field])

    full_k_grid = np.asarray(loaded[0][1]["full_k_grid_mpc"], dtype=np.float64)
    rows: list[tuple[int, BianchiTransferFunctions]] = []
    for path, data in loaded:
        candidate_full = np.asarray(data["full_k_grid_mpc"], dtype=np.float64)
        if not np.array_equal(candidate_full, full_k_grid):
            raise ValueError(f"{path} has a different full_k_grid_mpc")
        indices = np.asarray(data["k_indices"], dtype=np.int64)
        transfers = _transfers_from_arrays(data)
        if indices.size != len(transfers):
            raise ValueError(
                f"{path} index count {indices.size} != transfer count {len(transfers)}"
            )
        rows.extend((int(idx), tf) for idx, tf in zip(indices, transfers))

    rows.sort(key=lambda item: item[0])
    indices = np.asarray([idx for idx, _ in rows], dtype=np.int64)
    expected = np.arange(full_k_grid.size, dtype=np.int64)
    if not np.array_equal(indices, expected):
        missing = sorted(set(expected.tolist()).difference(indices.tolist()))
        duplicates = sorted(
            idx for idx in set(indices.tolist()) if list(indices).count(idx) > 1
        )
        raise ValueError(
            "chunk set does not cover the full k-grid exactly: "
            f"missing={missing[:8]}, duplicates={duplicates[:8]}"
        )

    t0 = time.perf_counter()
    _assemble_and_write_spectrum(
        out=args.out,
        args=args,
        k_grid=full_k_grid,
        transfers=[tf for _, tf in rows],
        elapsed_s=time.perf_counter() - t0,
        metadata_extra={
            "artifact_kind": "spectrum_from_chunks",
            "chunk_files": [str(path) for path, _ in loaded],
            "chunk_elapsed_seconds_total": float(
                sum(float(meta.get("elapsed_seconds", 0.0)) for meta in chunk_metadata)
            ),
            "chunk_count_observed": len(loaded),
        },
    )
    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.combine_chunks is not None:
        return _combine_chunks(args)

    if args.ell_max > args.l_max:
        parser.error("--ell-max must be <= --l-max")
    if args.quadrature == "simpson" and args.n_k % 2 == 0:
        parser.error("--quadrature simpson requires an odd --n-k")
    if args.mode == "linear-probe" and args.probe_b_k_sq <= 0.0:
        parser.error("--probe-b-k-sq must be positive")
    if args.z_injection <= 0.0:
        parser.error("--z-injection must be positive")
    if args.pre_recombination_margin_mpc < 0.0:
        parser.error("--pre-recombination-margin-mpc must be non-negative")
    if (
        args.superhorizon_x_max_at_start is not None
        and args.superhorizon_x_max_at_start <= 0.0
    ):
        parser.error("--superhorizon-x-max-at-start must be positive when supplied")
    if (args.chunk_index is None) ^ (args.chunk_count is None):
        parser.error("--chunk-index and --chunk-count must be supplied together")
    if args.chunk_index is not None:
        if args.chunk_index < 0 or args.chunk_index >= args.chunk_count:
            parser.error("--chunk-index must be in [0, --chunk-count)")

    k_grid = np.logspace(args.log10_k_min, args.log10_k_max, args.n_k)
    pipeline_cfg = FLRWPipelineConfig(
        L_max_tower=int(args.l_max),
        ell_max_transfer=int(args.ell_max),
        rtol=float(args.rtol),
        atol=float(args.atol),
        max_step_factor=int(args.max_step_factor),
        co_evolve_scalar_metric=bool(args.co_evolve_scalar_metric),
        co_evolve_scalar_streaming=bool(args.co_evolve_scalar_streaming),
        flrw_source_frame=str(args.flrw_source_frame),
        z_injection=float(args.z_injection),
        pre_recombination_margin_mpc=float(args.pre_recombination_margin_mpc),
        superhorizon_x_max_at_start=(
            None
            if args.superhorizon_x_max_at_start is None
            else float(args.superhorizon_x_max_at_start)
        ),
    )
    assembly_cfg = CLAssemblyConfig(
        ell_max=int(args.ell_max),
        k_grid=k_grid,
        quadrature=args.quadrature,
    )

    t0 = time.perf_counter()
    species = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )
    if args.chunk_index is not None:
        chunks = np.array_split(np.arange(k_grid.size, dtype=np.int64), args.chunk_count)
        chunk_indices = np.asarray(chunks[int(args.chunk_index)], dtype=np.int64)
        if chunk_indices.size == 0:
            raise ValueError("selected chunk is empty")
        transfers = _compute_transfer_list(
            species=species,
            k_grid=k_grid[chunk_indices],
            pipeline_cfg=pipeline_cfg,
            mode=args.mode,
            probe_b_k_sq=float(args.probe_b_k_sq),
            n_workers=args.n_workers,
        )
        _write_transfer_chunk(
            out=args.out,
            args=args,
            full_k_grid=k_grid,
            chunk_indices=chunk_indices,
            transfers=transfers,
            elapsed_s=time.perf_counter() - t0,
        )
        return 0

    if args.mode == "linear-probe":
        bundle = compute_flrw_d_ell_linear_probe(
            species,
            k_grid_mpc=k_grid,
            pipeline_config=pipeline_cfg,
            assembly_config=assembly_cfg,
            probe_b_k_sq=float(args.probe_b_k_sq),
            calibration_factor=1.0,
            n_workers=args.n_workers,
        )
    else:
        bundle = compute_flrw_d_ell(
            species,
            k_grid_mpc=k_grid,
            pipeline_config=pipeline_cfg,
            assembly_config=assembly_cfg,
            n_workers=args.n_workers,
        )
    elapsed_s = time.perf_counter() - t0

    metadata = _metadata_from_args(args, elapsed_s, artifact_kind="spectrum")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        args.out,
        ell=np.arange(int(args.ell_max) + 1, dtype=np.int64),
        k_grid_mpc=np.asarray(bundle["k_grid_mpc"], dtype=np.float64),
        cl_tt=np.asarray(bundle["cl_tt"], dtype=np.float64),
        cl_ee=np.asarray(bundle["cl_ee"], dtype=np.float64),
        cl_te=np.asarray(bundle["cl_te"], dtype=np.float64),
        d_tt=np.asarray(bundle["d_tt"], dtype=np.float64),
        d_ee=np.asarray(bundle["d_ee"], dtype=np.float64),
        d_te=np.asarray(bundle["d_te"], dtype=np.float64),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    print(args.out)
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
