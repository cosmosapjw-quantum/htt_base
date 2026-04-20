#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from cf4_grid_adapter import (
    CLIGHT,
    GRID_BOX_SIZE_MPC,
    coords_to_supergalactic,
    load_grid,
    query_loaded_grid,
    to_grid_index,
)


@dataclass(frozen=True)
class BenchmarkModel:
    fixed_overhead_s: float
    queries_per_second: float
    sample_points: int
    repeats: int
    timings_s: tuple[tuple[int, float], ...]


@dataclass(frozen=True)
class SamplingPlan:
    chosen_resolution: int
    chosen_stride: int
    n_queries: int
    estimated_runtime_s: float
    z_min: float
    z_max: float
    available_memory_gib: float
    cpu_count: int


@dataclass(frozen=True)
class CatalogSlice:
    cap: str
    tracer: str
    source: str
    ra: np.ndarray
    dec: np.ndarray
    z: np.ndarray
    weight: np.ndarray
    sgx: np.ndarray
    sgy: np.ndarray
    sgz: np.ndarray
    ix: np.ndarray
    iy: np.ndarray
    iz: np.ndarray


def available_memory_gib() -> float:
    try:
        pages = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, ValueError, OSError):
        return float("nan")
    return float(pages * page_size) / float(1024 ** 3)


def safe_z_max_from_grid(*, safety_fraction: float = 0.9) -> float:
    half_box_mpc = 0.5 * GRID_BOX_SIZE_MPC * safety_fraction
    return half_box_mpc * 100.0 / CLIGHT


def find_bgs_npz(desi_dir: Path, cap: str) -> Path:
    candidates = [
        desi_dir / f"BGS_ANY_{cap}_clustering_extended.npz",
        desi_dir / f"BGS_ANY_{cap}_clustering_minimal.npz",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"No BGS compact NPZ found for {cap} under {desi_dir}")


def candidate_resolutions(n_grid: int, min_resolution: int = 4) -> list[int]:
    out: list[int] = []
    res = n_grid
    while res >= min_resolution:
        if n_grid % res == 0:
            out.append(res)
        res //= 2
    if not out:
        out.append(n_grid)
    return out


def evenly_spaced_indices(n_items: int, n_take: int) -> np.ndarray:
    if n_take >= n_items:
        return np.arange(n_items, dtype=np.int64)
    return np.linspace(0, n_items - 1, n_take, dtype=np.int64)


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    if len(values) == 1:
        return float(values[0])
    order = np.argsort(values)
    values_sorted = values[order]
    weights_sorted = weights[order]
    cutoff = 0.5 * float(np.sum(weights_sorted))
    return float(values_sorted[np.searchsorted(np.cumsum(weights_sorted), cutoff)])


def weighted_spherical_centroid(ra_deg: np.ndarray, dec_deg: np.ndarray,
                                weights: np.ndarray) -> tuple[float, float]:
    if len(ra_deg) == 1:
        return float(ra_deg[0]), float(dec_deg[0])
    ra = np.deg2rad(ra_deg)
    dec = np.deg2rad(dec_deg)
    cos_dec = np.cos(dec)
    x = np.average(cos_dec * np.cos(ra), weights=weights)
    y = np.average(cos_dec * np.sin(ra), weights=weights)
    z = np.average(np.sin(dec), weights=weights)
    norm = math.sqrt(x * x + y * y + z * z)
    if norm == 0.0:
        return float(ra_deg[0]), float(dec_deg[0])
    x /= norm
    y /= norm
    z /= norm
    return float(np.rad2deg(np.arctan2(y, x)) % 360.0), float(np.rad2deg(np.arcsin(z)))


def angular_separation_deg(ra_deg: np.ndarray, dec_deg: np.ndarray,
                           ra0_deg: float, dec0_deg: float) -> np.ndarray:
    ra = np.deg2rad(ra_deg)
    dec = np.deg2rad(dec_deg)
    ra0 = math.radians(ra0_deg)
    dec0 = math.radians(dec0_deg)
    cos_sep = (
        np.sin(dec) * math.sin(dec0)
        + np.cos(dec) * math.cos(dec0) * np.cos(ra - ra0)
    )
    return np.rad2deg(np.arccos(np.clip(cos_sep, -1.0, 1.0)))


def choose_representative(local_ra: np.ndarray, local_dec: np.ndarray,
                          local_z: np.ndarray, local_weight: np.ndarray) -> int:
    if len(local_ra) == 1:
        return 0
    ra0, dec0 = weighted_spherical_centroid(local_ra, local_dec, local_weight)
    z0 = weighted_median(local_z, local_weight)
    ang = angular_separation_deg(local_ra, local_dec, ra0, dec0)
    zdev = np.abs(local_z - z0)
    ang_scale = max(float(np.sqrt(np.average(ang * ang, weights=local_weight))), 1e-6)
    z_scale = max(float(np.sqrt(np.average(zdev * zdev, weights=local_weight))), 1e-6)
    weight_bonus = np.asarray(local_weight, dtype=np.float64)
    if np.max(weight_bonus) > 0.0:
        weight_bonus = weight_bonus / np.max(weight_bonus)
    score = (ang / ang_scale) ** 2 + (zdev / z_scale) ** 2 - 1e-3 * weight_bonus
    return int(np.argmin(score))


def build_catalog_slice(path: Path, cap: str, grid, *, z_min: float,
                        z_max: float) -> CatalogSlice:
    x = np.load(path)
    ra = np.asarray(x["ra"], dtype=np.float64)
    dec = np.asarray(x["dec"], dtype=np.float64)
    z = np.asarray(x["z"], dtype=np.float64)
    weight = np.asarray(x["weight"], dtype=np.float64)
    mask = np.isfinite(ra) & np.isfinite(dec) & np.isfinite(z) & np.isfinite(weight)
    mask &= (z >= z_min) & (z <= z_max)
    if not np.any(mask):
        raise ValueError(f"No BGS rows survive z-range selection for {path}")

    ra = ra[mask]
    dec = dec[mask]
    z = z[mask]
    weight = weight[mask]

    sgx, sgy, sgz = coords_to_supergalactic(
        ra, dec, z,
        coord_type="equatorial",
        unit_type="degrees",
        distance_type="redshift",
    )
    n_grid = int(np.asarray(grid["d_mean_CF4pp"]).shape[0])
    delta = GRID_BOX_SIZE_MPC / float(n_grid)
    ix = to_grid_index(np.asarray(sgx), delta, N=n_grid, L=GRID_BOX_SIZE_MPC)
    iy = to_grid_index(np.asarray(sgy), delta, N=n_grid, L=GRID_BOX_SIZE_MPC)
    iz = to_grid_index(np.asarray(sgz), delta, N=n_grid, L=GRID_BOX_SIZE_MPC)

    return CatalogSlice(
        cap=cap,
        tracer="BGS_ANY",
        source=path.name,
        ra=ra,
        dec=dec,
        z=z,
        weight=weight,
        sgx=np.asarray(sgx, dtype=np.float64),
        sgy=np.asarray(sgy, dtype=np.float64),
        sgz=np.asarray(sgz, dtype=np.float64),
        ix=np.asarray(ix, dtype=np.int16),
        iy=np.asarray(iy, dtype=np.int16),
        iz=np.asarray(iz, dtype=np.int16),
    )


def build_benchmark_arrays(catalogs: list[CatalogSlice], max_points: int = 32768
                           ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    total = sum(len(cat.ra) for cat in catalogs)
    if total == 0:
        raise ValueError("No eligible DESI targets available for benchmarking")
    take_per_catalog = max(1, max_points // max(len(catalogs), 1))

    ra_parts: list[np.ndarray] = []
    dec_parts: list[np.ndarray] = []
    z_parts: list[np.ndarray] = []
    for cat in catalogs:
        idx = evenly_spaced_indices(len(cat.ra), min(len(cat.ra), take_per_catalog))
        ra_parts.append(cat.ra[idx])
        dec_parts.append(cat.dec[idx])
        z_parts.append(cat.z[idx])
    return (
        np.concatenate(ra_parts),
        np.concatenate(dec_parts),
        np.concatenate(z_parts),
    )


def benchmark_query_model(grid, catalogs: list[CatalogSlice], *,
                          repeats: int = 3) -> BenchmarkModel:
    bench_ra, bench_dec, bench_z = build_benchmark_arrays(catalogs)
    sample_points = len(bench_ra)
    candidate_sizes = []
    for size in (512, 2048, 8192, 32768):
        size = min(size, sample_points)
        if size > 0 and size not in candidate_sizes:
            candidate_sizes.append(size)
    if not candidate_sizes:
        candidate_sizes = [sample_points]

    query_loaded_grid(
        grid,
        bench_ra[: candidate_sizes[0]],
        bench_dec[: candidate_sizes[0]],
        bench_z[: candidate_sizes[0]],
        coord_type="equatorial",
        unit_type="degrees",
        distance_type="redshift",
    )

    timings: list[tuple[int, float]] = []
    for size in candidate_sizes:
        trial_times = []
        for _ in range(repeats):
            t0 = time.perf_counter()
            query_loaded_grid(
                grid,
                bench_ra[:size],
                bench_dec[:size],
                bench_z[:size],
                coord_type="equatorial",
                unit_type="degrees",
                distance_type="redshift",
            )
            trial_times.append(time.perf_counter() - t0)
        timings.append((size, float(np.median(trial_times))))

    points = np.asarray([n for n, _ in timings], dtype=np.float64)
    elapsed = np.asarray([t for _, t in timings], dtype=np.float64)
    if len(points) == 1:
        qps = float(points[0] / max(elapsed[0], 1e-9))
        overhead = 0.0
    else:
        slope, intercept = np.polyfit(points, elapsed, deg=1)
        if slope <= 0.0:
            slope = elapsed[-1] / max(points[-1], 1.0)
            intercept = 0.0
        qps = float(1.0 / max(slope, 1e-12))
        overhead = float(max(intercept, 0.0))

    return BenchmarkModel(
        fixed_overhead_s=overhead,
        queries_per_second=qps,
        sample_points=sample_points,
        repeats=repeats,
        timings_s=tuple(timings),
    )


def coarse_keys(cat: CatalogSlice, *, resolution: int, n_grid: int) -> np.ndarray:
    stride = max(1, n_grid // resolution)
    ix = np.asarray(cat.ix, dtype=np.int64) // stride
    iy = np.asarray(cat.iy, dtype=np.int64) // stride
    iz = np.asarray(cat.iz, dtype=np.int64) // stride
    return ((ix * resolution) + iy) * resolution + iz


def choose_sampling_plan(catalogs: list[CatalogSlice], benchmark: BenchmarkModel, *,
                         n_grid: int, z_min: float, z_max: float,
                         target_runtime_s: float, runtime_safety: float) -> SamplingPlan:
    effective_runtime_limit = target_runtime_s * runtime_safety
    chosen_resolution = None
    chosen_n_queries = None
    chosen_estimated_runtime = None

    for resolution in candidate_resolutions(n_grid):
        n_queries = 0
        for cat in catalogs:
            n_queries += int(np.unique(coarse_keys(cat, resolution=resolution, n_grid=n_grid)).size)
        est_runtime = benchmark.fixed_overhead_s + (n_queries / max(benchmark.queries_per_second, 1e-9))
        if est_runtime <= effective_runtime_limit:
            chosen_resolution = resolution
            chosen_n_queries = n_queries
            chosen_estimated_runtime = est_runtime
            break

    if chosen_resolution is None:
        resolution = candidate_resolutions(n_grid)[-1]
        chosen_resolution = resolution
        chosen_n_queries = 0
        for cat in catalogs:
            chosen_n_queries += int(np.unique(coarse_keys(cat, resolution=resolution, n_grid=n_grid)).size)
        chosen_estimated_runtime = benchmark.fixed_overhead_s + (
            chosen_n_queries / max(benchmark.queries_per_second, 1e-9)
        )

    return SamplingPlan(
        chosen_resolution=chosen_resolution,
        chosen_stride=max(1, n_grid // chosen_resolution),
        n_queries=int(chosen_n_queries),
        estimated_runtime_s=float(chosen_estimated_runtime),
        z_min=float(z_min),
        z_max=float(z_max),
        available_memory_gib=available_memory_gib(),
        cpu_count=os.cpu_count() or 1,
    )


def emit_rows(catalogs: list[CatalogSlice], plan: SamplingPlan, *, n_grid: int
              ) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    stride = plan.chosen_stride
    resolution = plan.chosen_resolution
    for cat in catalogs:
        keys = coarse_keys(cat, resolution=resolution, n_grid=n_grid)
        order = np.argsort(keys, kind="mergesort")
        ordered_keys = keys[order]
        bounds = np.flatnonzero(np.diff(ordered_keys)) + 1
        starts = np.concatenate(([0], bounds))
        stops = np.concatenate((bounds, [len(order)]))

        for group_number, (start, stop) in enumerate(zip(starts, stops), start=1):
            idx = order[start:stop]
            choice_local = choose_representative(
                cat.ra[idx],
                cat.dec[idx],
                cat.z[idx],
                cat.weight[idx],
            )
            chosen = idx[choice_local]
            rows.append({
                "label": f"BGS_{cat.cap}_auto_r{resolution}_{group_number:05d}",
                "tracer": cat.tracer,
                "cap": cat.cap,
                "ra": float(cat.ra[chosen]),
                "dec": float(cat.dec[chosen]),
                "z": float(cat.z[chosen]),
                "bin_lo": float(np.min(cat.z[idx])),
                "bin_hi": float(np.max(cat.z[idx])),
                "n_in_bin": int(len(idx)),
                "selected_weight": float(cat.weight[chosen]),
                "coarse_resolution": int(resolution),
                "coarse_stride": int(stride),
                "grid_ix": int(cat.ix[chosen]),
                "grid_iy": int(cat.iy[chosen]),
                "grid_iz": int(cat.iz[chosen]),
                "sgx": float(cat.sgx[chosen]),
                "sgy": float(cat.sgy[chosen]),
                "sgz": float(cat.sgz[chosen]),
                "selection_note": (
                    "Hardware-adaptive CF4 target selected from DESI BGS after "
                    "benchmarking local query throughput and grouping occupied "
                    f"CF4 voxels at effective resolution {resolution}^3."
                ),
                "source_catalog": cat.source,
            })
    rows.sort(key=lambda row: (str(row["cap"]), float(row["z"]), str(row["label"])))
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("No rows available to write")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path | None, *, benchmark: BenchmarkModel,
                 plan: SamplingPlan, catalogs: list[CatalogSlice],
                 out_csv: Path) -> None:
    if path is None:
        return
    payload = {
        "benchmark": asdict(benchmark),
        "plan": asdict(plan),
        "catalogs": [
            {
                "cap": cat.cap,
                "source": cat.source,
                "n_rows": int(len(cat.ra)),
                "z_min": float(np.min(cat.z)),
                "z_max": float(np.max(cat.z)),
            }
            for cat in catalogs
        ],
        "output_csv": str(out_csv),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def load_required_grid(grid_path: Path) -> dict[str, np.ndarray]:
    if not grid_path.exists():
        raise SystemExit(
            "CF4 grid file not found:\n"
            f"  {grid_path}\n"
            "This target generator requires the real CF4 grid; synthetic fallback is disabled.\n"
            "Re-download the file first, then rerun this command.\n"
            "The canonical download URL is:\n"
            "  https://projets.ip2i.in2p3.fr//cosmicflows/CF4pp_mean_std_grids.npz\n"
            "To let the pipeline fetch it automatically, run:\n"
            "  bash dl_pipeline/run_all.sh ./workdir\n"
            "Or with an explicit override:\n"
            "  CF4_GRID_URL=\"https://projets.ip2i.in2p3.fr//cosmicflows/CF4pp_mean_std_grids.npz\" bash dl_pipeline/run_all.sh ./workdir\n"
            "Or place CF4pp_mean_std_grids.npz at the path above and rerun."
        )
    return load_grid(grid_path)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate a hardware-adaptive CF4 target CSV from DESI BGS compact products."
    )
    ap.add_argument("--desi-dir", required=True,
                    help="Directory containing BGS_ANY_{NGC,SGC}_clustering_{extended|minimal}.npz")
    ap.add_argument("--grid", required=True, help="Path to CF4pp_mean_std_grids.npz")
    ap.add_argument("--out", required=True, help="Output CSV path")
    ap.add_argument("--report-out", default=None, help="Optional JSON benchmark/report output path")
    ap.add_argument("--z-min", type=float, default=0.03,
                    help="Minimum DESI BGS redshift to include (default 0.03)")
    ap.add_argument("--z-max", type=float, default=None,
                    help="Maximum DESI BGS redshift to include. Defaults to the CF4 safe-box ceiling.")
    ap.add_argument("--safe-radius-fraction", type=float, default=0.9,
                    help="Fraction of the CF4 half-box radius used to derive the default z_max (default 0.9)")
    ap.add_argument("--target-runtime-s", type=float, default=0.25,
                    help="Target wall-clock budget for the eventual CF4 batch query (default 0.25 s)")
    ap.add_argument("--runtime-safety", type=float, default=0.8,
                    help="Conservative multiplier applied to the target runtime when choosing resolution (default 0.8)")
    ap.add_argument("--benchmark-repeats", type=int, default=3,
                    help="Number of timing repeats for throughput benchmarking (default 3)")
    args = ap.parse_args()

    desi_dir = Path(args.desi_dir)
    grid_path = Path(args.grid)
    out_csv = Path(args.out)
    report_path = Path(args.report_out) if args.report_out else None

    grid = load_required_grid(grid_path)
    n_grid = int(np.asarray(grid["d_mean_CF4pp"]).shape[0])
    z_max = args.z_max
    if z_max is None:
        z_max = safe_z_max_from_grid(safety_fraction=args.safe_radius_fraction)

    catalogs = [
        build_catalog_slice(find_bgs_npz(desi_dir, cap), cap, grid, z_min=args.z_min, z_max=z_max)
        for cap in ("NGC", "SGC")
    ]
    benchmark = benchmark_query_model(grid, catalogs, repeats=args.benchmark_repeats)
    plan = choose_sampling_plan(
        catalogs,
        benchmark,
        n_grid=n_grid,
        z_min=args.z_min,
        z_max=z_max,
        target_runtime_s=args.target_runtime_s,
        runtime_safety=args.runtime_safety,
    )
    rows = emit_rows(catalogs, plan, n_grid=n_grid)
    write_csv(out_csv, rows)
    write_report(report_path, benchmark=benchmark, plan=plan, catalogs=catalogs, out_csv=out_csv)

    print(f"[cf4-targets] wrote {len(rows)} rows → {out_csv}")
    print(f"[cf4-targets] grid={n_grid}^3  z-range=[{args.z_min:.4f}, {z_max:.4f}]")
    print(
        "[cf4-targets] benchmark: "
        f"{benchmark.queries_per_second:.0f} queries/s "
        f"(fixed overhead {benchmark.fixed_overhead_s:.4f} s)"
    )
    print(
        "[cf4-targets] chosen coarse resolution: "
        f"{plan.chosen_resolution}^3 "
        f"(stride={plan.chosen_stride}, est runtime {plan.estimated_runtime_s:.4f} s)"
    )
    if report_path is not None:
        print(f"[cf4-targets] report → {report_path}")


if __name__ == "__main__":
    main()
