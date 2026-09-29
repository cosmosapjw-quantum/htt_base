"""Dependence-aware descriptive summaries of fixed CF4 reconstruction queries."""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def summarize_cf4_queries(arrays: dict[str, Any], *, dataset_id: str, depth_edges_mpc_h: Sequence[float], half_box_mpc_h: float = 500.0) -> dict[str, Any]:
    required = {"sgx", "sgy", "sgz", "grid_index", "vxyz_mean", "vxyz_std"}
    missing = required - arrays.keys()
    if missing:
        raise ValueError(f"missing CF4 query fields: {sorted(missing)}")
    xyz = np.column_stack([np.asarray(arrays[key], dtype=float) for key in ("sgx", "sgy", "sgz")])
    grid = np.asarray(arrays["grid_index"], dtype=int)
    velocity = np.asarray(arrays["vxyz_mean"], dtype=float)
    marginal_std = np.asarray(arrays["vxyz_std"], dtype=float)
    n = len(xyz)
    if xyz.shape != (n, 3) or grid.shape != (n, 3) or velocity.shape != (n, 3) or marginal_std.shape != (n, 3):
        raise ValueError("CF4 query fields must be aligned N x 3 arrays")
    if not all(np.isfinite(item).all() for item in (xyz, velocity, marginal_std)) or np.any(marginal_std < 0):
        raise ValueError("CF4 query fields must be finite with nonnegative marginal std")
    outside = np.any(np.abs(xyz) > half_box_mpc_h, axis=1)
    if np.any(outside):
        raise ValueError("query coordinates outside released grid; boundary clipping refused")
    cells, inverse, counts = np.unique(grid, axis=0, return_inverse=True, return_counts=True)
    depth = np.linalg.norm(xyz, axis=1)
    edges = np.asarray(depth_edges_mpc_h, dtype=float)
    if edges.ndim != 1 or len(edges) < 2 or np.any(np.diff(edges) <= 0):
        raise ValueError("depth edges must be strictly increasing")
    summaries = []
    for low, high in zip(edges[:-1], edges[1:]):
        selected = (depth >= low) & (depth < high)
        selected_cells = np.unique(inverse[selected]) if np.any(selected) else np.asarray([], dtype=int)
        cell_velocities = np.asarray([velocity[selected & (inverse == cell)].mean(axis=0) for cell in selected_cells])
        summaries.append({"depth_min_mpc_h": float(low), "depth_max_mpc_h": float(high), "query_rows": int(selected.sum()),
                          "unique_cells": int(len(selected_cells)),
                          "mean_reconstructed_velocity": cell_velocities.mean(axis=0).tolist() if len(cell_velocities) else None,
                          "aggregation": "WITHIN_CELL_MEAN_THEN_EQUAL_CELL_MEAN"})
    return {
        "schema": "htt.owned_cf4_query_analysis/v1", "dataset_id": dataset_id, "query_rows": n,
        "unique_grid_cells": int(len(cells)), "duplicate_query_rows": int(n - len(cells)),
        "cell_counts": [{"grid_index": cell.tolist(), "query_rows": int(count)} for cell, count in zip(cells, counts)],
        "depth_summaries": summaries, "field_role": "RECONSTRUCTED_GRID_QUERY_NOT_RAW_GALAXY",
        "marginal_std_role": "PER_QUERY_MARGINAL_NOT_JOINT_COVARIANCE", "joint_field_law": "UNAVAILABLE",
        "independent_sample_count": None, "claim_ceiling": "mean-field and dependence diagnostics only",
    }
