"""Selection-honest descriptive summaries for owned DESI compact catalogs."""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def summarize_desi(
    arrays: dict[str, Any], *, dataset_id: str, tracer: str, cap: str,
    z_edges: Sequence[float], primary_weight: str = "weight",
) -> dict[str, Any]:
    required = {"ra", "dec", "z", primary_weight}
    missing = required - arrays.keys()
    if missing:
        raise ValueError(f"missing DESI columns: {sorted(missing)}")
    ra, dec, z, weight = (np.asarray(arrays[key], dtype=float) for key in ("ra", "dec", "z", primary_weight))
    if not (ra.ndim == dec.ndim == z.ndim == weight.ndim == 1 and len({len(ra), len(dec), len(z), len(weight)}) == 1):
        raise ValueError("DESI columns must be aligned vectors")
    if not all(np.isfinite(item).all() for item in (ra, dec, z, weight)) or np.any(weight < 0):
        raise ValueError("DESI rows and primary weights must be finite and nonnegative")
    edges = np.asarray(z_edges, dtype=float)
    if edges.ndim != 1 or len(edges) < 2 or np.any(np.diff(edges) <= 0):
        raise ValueError("z_edges must be strictly increasing")
    radians, declination = np.deg2rad(ra), np.deg2rad(dec)
    nhat = np.column_stack([np.cos(declination) * np.cos(radians), np.cos(declination) * np.sin(radians), np.sin(declination)])
    targetid = np.asarray(arrays["targetid"]) if "targetid" in arrays and arrays["targetid"] is not None else None
    if targetid is not None and targetid.shape != ra.shape:
        raise ValueError("targetid must align with catalog rows")
    bins = []
    for low, high in zip(edges[:-1], edges[1:]):
        selected = (z >= low) & (z < high)
        total = float(weight[selected].sum())
        vector = (weight[selected, None] * nhat[selected]).sum(axis=0) / total if total > 0 else np.full(3, np.nan)
        bins.append({"z_min": float(low), "z_max": float(high), "row_count": int(selected.sum()), "weight_sum": total,
                     "weighted_mean_direction": vector.tolist() if total > 0 else None})
    components = sorted(key for key in ("weight_fkp", "weight_sys", "weight_zfail", "weight_comp") if key in arrays and arrays[key] is not None)
    return {
        "schema": "htt.owned_desi_analysis/v1", "dataset_id": dataset_id, "tracer": tracer, "cap": cap,
        "row_count": len(ra), "unique_target_count": int(len(np.unique(targetid))) if targetid is not None else None,
        "duplicate_target_rows": int(len(targetid) - len(np.unique(targetid))) if targetid is not None else None,
        "primary_weight": primary_weight, "available_weight_components": components,
        "weight_combination": "NO_ADDITIONAL_MULTIPLICATION", "redshift_bins": bins,
        "selection_correction": "UNAVAILABLE", "random_catalog": "UNAVAILABLE", "covariance": "UNAVAILABLE",
        "claim_ceiling": "weighted and unweighted descriptive statistics; no corrected cosmological dipole significance",
    }
