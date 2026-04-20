from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from generate_cf4_targets_from_desi import (
    BenchmarkModel,
    CatalogSlice,
    candidate_resolutions,
    choose_sampling_plan,
    emit_rows,
    load_required_grid,
)


def make_catalog(cap: str, ix: list[int]) -> CatalogSlice:
    n = len(ix)
    return CatalogSlice(
        cap=cap,
        tracer="BGS_ANY",
        source=f"{cap}.npz",
        ra=np.linspace(10.0, 20.0, n),
        dec=np.linspace(-5.0, 5.0, n),
        z=np.linspace(0.03, 0.06, n),
        weight=np.ones(n, dtype=np.float64),
        sgx=np.zeros(n, dtype=np.float64),
        sgy=np.zeros(n, dtype=np.float64),
        sgz=np.zeros(n, dtype=np.float64),
        ix=np.asarray(ix, dtype=np.int16),
        iy=np.zeros(n, dtype=np.int16),
        iz=np.zeros(n, dtype=np.int16),
    )


def test_candidate_resolutions_tracks_grid_divisors() -> None:
    assert candidate_resolutions(8) == [8, 4]
    assert candidate_resolutions(16) == [16, 8, 4]


def test_choose_sampling_plan_coarsens_when_full_resolution_exceeds_budget() -> None:
    catalogs = [
        make_catalog("NGC", [0, 1, 4, 5]),
        make_catalog("SGC", [0, 1, 4, 5]),
    ]
    benchmark = BenchmarkModel(
        fixed_overhead_s=0.0,
        queries_per_second=8.0,
        sample_points=8,
        repeats=1,
        timings_s=((8, 1.0),),
    )

    plan = choose_sampling_plan(
        catalogs,
        benchmark,
        n_grid=8,
        z_min=0.03,
        z_max=0.06,
        target_runtime_s=0.6,
        runtime_safety=1.0,
    )

    assert plan.chosen_resolution == 4
    assert plan.n_queries == 4


def test_emit_rows_returns_one_representative_per_group() -> None:
    catalogs = [
        make_catalog("NGC", [0, 0, 4, 4]),
        make_catalog("SGC", [1, 1]),
    ]
    plan = choose_sampling_plan(
        catalogs,
        BenchmarkModel(
            fixed_overhead_s=0.0,
            queries_per_second=1000.0,
            sample_points=6,
            repeats=1,
            timings_s=((6, 0.01),),
        ),
        n_grid=8,
        z_min=0.03,
        z_max=0.06,
        target_runtime_s=1.0,
        runtime_safety=1.0,
    )

    rows = emit_rows(catalogs, plan, n_grid=8)

    assert len(rows) == 3
    assert {row["cap"] for row in rows} == {"NGC", "SGC"}
    assert all(row["coarse_resolution"] == plan.chosen_resolution for row in rows)
    assert all(row["label"].startswith("BGS_") for row in rows)


def test_load_required_grid_requires_real_file(tmp_path: Path) -> None:
    missing = tmp_path / "CF4pp_mean_std_grids.npz"

    try:
        load_required_grid(missing)
    except SystemExit as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected SystemExit for missing CF4 grid")

    assert "synthetic fallback is disabled" in message
    assert str(missing) in message
