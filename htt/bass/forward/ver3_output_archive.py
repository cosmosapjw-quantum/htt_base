"""ver3 PR-10 output split and archive schema layer."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from common.contracts import SolverCoreOutput

__all__ = [
    "DEFAULT_HARMONIC_ORDERING",
    "observer_boost_output",
    "write_output_archive",
]


DEFAULT_HARMONIC_ORDERING = "ell_m_lexicographic"
_NUMERIC_RESIDUAL_KEYS = (
    "visibility_tau_reion",
    "source_builder_low_z_gpi_m0",
    "seed_k_comoving",
    "visibility_peak_eta_mpc",
)


def _lmax(output: SolverCoreOutput) -> int:
    return int(output.metadata.get("multipole_cutoff", 0))


def _alm_size(lmax: int) -> int:
    return (lmax + 1) ** 2


def _coerce_component(value: object, *, lmax: int, component: str) -> np.ndarray:
    target = _alm_size(lmax)
    if value is None:
        return np.zeros(target, dtype=np.float64)
    if isinstance(value, Mapping):
        if "values" not in value:
            raise ValueError(
                f"{component} mapping must contain 'values' for archive writing"
            )
        arr = np.asarray(value["values"], dtype=np.float64)
    else:
        arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(f"{component} must be 1-D for archive writing; got {arr.shape}")
    if arr.size != target:
        raise ValueError(
            f"{component} size {arr.size} does not match lmax={lmax} target {target}"
        )
    return np.array(arr, copy=True)


def _base_component_metadata(
    output: SolverCoreOutput,
    *,
    ordering: str,
    component_kind: str,
    boost_applied: bool,
    component_status: str,
) -> dict[str, Any]:
    return {
        "family": output.metadata.get("bianchi_type"),
        "branch": output.metadata.get("bianchi_branch", "orthogonal"),
        "backend": output.metadata.get("source_propagator_realization"),
        "ordering": ordering,
        "boost_applied": bool(boost_applied),
        "global_tilt_present": bool(output.metadata.get("tilt_enabled", False)),
        "component_kind": component_kind,
        "component_status": component_status,
        "local_boost_contract": output.metadata.get("local_boost_contract"),
        "global_tilt_contract": output.metadata.get("global_tilt_contract"),
    }


def observer_boost_output(
    output: SolverCoreOutput,
    *,
    ordering: str = DEFAULT_HARMONIC_ORDERING,
    alm_T: object | None = None,
    alm_E: object | None = None,
    alm_B: object | None = None,
) -> dict[str, Any]:
    """Return the output-only local-boost split payload.

    If no boost arrays are provided, this returns explicit zero arrays with
    ``boost_applied=false``. The helper never folds boost into the upstream
    deterministic component.
    """
    lmax = _lmax(output)
    any_component = any(value is not None for value in (alm_T, alm_E, alm_B))
    boost_T = _coerce_component(alm_T, lmax=lmax, component="boost alm_T")
    boost_E = _coerce_component(alm_E, lmax=lmax, component="boost alm_E")
    boost_B = _coerce_component(alm_B, lmax=lmax, component="boost alm_B")
    metadata = _base_component_metadata(
        output,
        ordering=ordering,
        component_kind="boost",
        boost_applied=any_component,
        component_status="observer_boost_applied" if any_component else "zero_filled_no_boost",
    )
    metadata["split_semantics"] = "output_only_local_boost"
    return {
        "lmax": lmax,
        "ordering": ordering,
        "alm_T": boost_T,
        "alm_E": boost_E,
        "alm_B": boost_B,
        "metadata_json": json.dumps(metadata, sort_keys=True),
    }


def _solver_summary(
    output: SolverCoreOutput,
    *,
    ordering: str,
    boost_applied: bool,
) -> dict[str, Any]:
    residual_summary: dict[str, Any] = {}
    for key in _NUMERIC_RESIDUAL_KEYS:
        if key in output.metadata and output.metadata[key] is not None:
            value = float(output.metadata[key])
            if not np.isfinite(value):
                raise ValueError(f"non-finite residual metadata at {key}")
            residual_summary[key] = value
    gate_status = {
        "output_split_gate": "open",
        "fitting_gate": "closed",
        "boost_split_present": True,
        "manifest_claim_tier": output.manifest.claim_tier,
        "manifest_production_status": output.manifest.production_status,
    }
    return {
        "family": output.metadata.get("bianchi_type"),
        "branch": output.metadata.get("bianchi_branch", "orthogonal"),
        "backend": output.metadata.get("source_propagator_realization"),
        "ic_mode": output.metadata.get("seed_injection_mode", "unspecified"),
        "lmax_dev": _lmax(output),
        "lmax_prod": _lmax(output),
        "ordering": ordering,
        "boost_applied": bool(boost_applied),
        "global_tilt_present": bool(output.metadata.get("tilt_enabled", False)),
        "residual_summary": residual_summary,
        "gate_status": gate_status,
    }


def _component_payload(
    output: SolverCoreOutput,
    *,
    ordering: str,
    component_kind: str,
    alm_T: object,
    alm_E: object,
    alm_B: object,
    boost_applied: bool,
    component_status: str,
) -> dict[str, Any]:
    lmax = _lmax(output)
    metadata = _base_component_metadata(
        output,
        ordering=ordering,
        component_kind=component_kind,
        boost_applied=boost_applied,
        component_status=component_status,
    )
    return {
        "lmax": lmax,
        "ordering": ordering,
        "alm_T": _coerce_component(alm_T, lmax=lmax, component=f"{component_kind} alm_T"),
        "alm_E": _coerce_component(alm_E, lmax=lmax, component=f"{component_kind} alm_E"),
        "alm_B": _coerce_component(alm_B, lmax=lmax, component=f"{component_kind} alm_B"),
        "metadata_json": json.dumps(metadata, sort_keys=True),
    }


def _write_npz(path: Path, payload: Mapping[str, Any]) -> None:
    np.savez(
        path,
        lmax=int(payload["lmax"]),
        ordering=str(payload["ordering"]),
        alm_T=np.asarray(payload["alm_T"], dtype=np.float64),
        alm_E=np.asarray(payload["alm_E"], dtype=np.float64),
        alm_B=np.asarray(payload["alm_B"], dtype=np.float64),
        metadata_json=str(payload["metadata_json"]),
    )


def write_output_archive(
    output: SolverCoreOutput,
    outdir: str | Path,
    *,
    ordering: str = DEFAULT_HARMONIC_ORDERING,
    stochastic_alm_T: object | None = None,
    stochastic_alm_E: object | None = None,
    stochastic_alm_B: object | None = None,
    boost_alm_T: object | None = None,
    boost_alm_E: object | None = None,
    boost_alm_B: object | None = None,
) -> dict[str, str]:
    """Write the ver3 PR-10 archive surface.

    The function writes ``solver_summary.json`` plus the mandatory
    ``alm_det.npz``, ``alm_stoch.npz``, and ``alm_boost.npz`` files.
    """
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)

    det_payload = _component_payload(
        output,
        ordering=ordering,
        component_kind="deterministic",
        alm_T=output.alm_T,
        alm_E=output.alm_E,
        alm_B=output.alm_B,
        boost_applied=False,
        component_status="forward_model_component",
    )
    stoch_payload = _component_payload(
        output,
        ordering=ordering,
        component_kind="stochastic",
        alm_T=stochastic_alm_T,
        alm_E=stochastic_alm_E,
        alm_B=stochastic_alm_B,
        boost_applied=False,
        component_status="zero_filled_no_stochastic_component"
        if all(v is None for v in (stochastic_alm_T, stochastic_alm_E, stochastic_alm_B))
        else "stochastic_component_present",
    )
    boost_payload = observer_boost_output(
        output,
        ordering=ordering,
        alm_T=boost_alm_T,
        alm_E=boost_alm_E,
        alm_B=boost_alm_B,
    )
    summary = _solver_summary(
        output,
        ordering=ordering,
        boost_applied=json.loads(str(boost_payload["metadata_json"]))["boost_applied"],
    )

    summary_path = root / "solver_summary.json"
    det_path = root / "alm_det.npz"
    stoch_path = root / "alm_stoch.npz"
    boost_path = root / "alm_boost.npz"

    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _write_npz(det_path, det_payload)
    _write_npz(stoch_path, stoch_payload)
    _write_npz(boost_path, boost_payload)
    return {
        "solver_summary.json": str(summary_path),
        "alm_det.npz": str(det_path),
        "alm_stoch.npz": str(stoch_path),
        "alm_boost.npz": str(boost_path),
    }
