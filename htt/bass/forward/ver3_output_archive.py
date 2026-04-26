"""ver3 PR-10 output split and archive schema layer."""
from __future__ import annotations

import json
from collections.abc import Iterator, Mapping as AbcMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from bass.validation import (
    GateBundle,
    collect_gate_bundles,
    make_gate_bundle,
    score_branch_readiness,
    summarize_gate_status,
)
from bass.ver3_contracts import OutputMetadata
from common.contracts import SolverCoreOutput

__all__ = [
    "DEFAULT_HARMONIC_ORDERING",
    "BoostArchive",
    "observer_boost_output",
    "observer_boost_output_from_components",
    "output_split_gate_bundle",
    "resolve_output_gate_registry",
    "write_output_archive",
    "write_family_residual_archive",
]


DEFAULT_HARMONIC_ORDERING = "ell_m_lexicographic"
_NUMERIC_RESIDUAL_KEYS = (
    "visibility_tau_reion",
    "source_builder_low_z_gpi_m0",
    "seed_k_comoving",
    "visibility_peak_eta_mpc",
)


@dataclass(frozen=True)
class BoostArchive(AbcMapping[str, Any]):
    """Output-only boost archive with mapping compatibility."""

    lmax: int
    ordering: str
    alm_T: np.ndarray
    alm_E: np.ndarray
    alm_B: np.ndarray
    metadata_json: str

    def __post_init__(self) -> None:
        for name in ("alm_T", "alm_E", "alm_B"):
            arr = np.asarray(getattr(self, name), dtype=np.float64)
            if arr.ndim != 1:
                raise ValueError(f"{name} must be 1-D, got {arr.shape}")
            object.__setattr__(self, name, arr)
        if not self.ordering:
            raise ValueError("BoostArchive.ordering must be non-empty")
        json.loads(self.metadata_json)

    def as_payload(self) -> dict[str, Any]:
        return {
            "lmax": int(self.lmax),
            "ordering": self.ordering,
            "alm_T": np.array(self.alm_T, copy=True),
            "alm_E": np.array(self.alm_E, copy=True),
            "alm_B": np.array(self.alm_B, copy=True),
            "metadata_json": self.metadata_json,
        }

    def __getitem__(self, key: str) -> Any:
        return self.as_payload()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.as_payload())

    def __len__(self) -> int:
        return len(self.as_payload())


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
    return OutputMetadata.from_solver_output(
        output,
        ordering=ordering,
        component_kind=component_kind,
        component_status=component_status,
        boost_applied=boost_applied,
    ).as_dict()


def observer_boost_output(
    output: SolverCoreOutput | object,
    *args,
    ordering: str = DEFAULT_HARMONIC_ORDERING,
    alm_T: object | None = None,
    alm_E: object | None = None,
    alm_B: object | None = None,
) -> BoostArchive:
    """Return the output-only local-boost split payload.

    If no boost arrays are provided, this returns explicit zero arrays with
    ``boost_applied=false``. The helper never folds boost into the upstream
    deterministic component.
    """
    if isinstance(output, SolverCoreOutput):
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
        return BoostArchive(
            lmax=lmax,
            ordering=ordering,
            alm_T=boost_T,
            alm_E=boost_E,
            alm_B=boost_B,
            metadata_json=json.dumps(metadata, sort_keys=True),
        )
    if len(args) != 3:
        raise TypeError(
            "component-form observer_boost_output expects "
            "(alm_det, alm_stoch, boost_params, metadata)"
        )
    return observer_boost_output_from_components(output, args[0], args[1], args[2])


def observer_boost_output_from_components(
    alm_det: object,
    alm_stoch: object,
    boost_params: Mapping[str, object],
    metadata: Mapping[str, object],
) -> BoostArchive:
    """Document-level component signature for output-only boost separation."""

    if not isinstance(boost_params, Mapping):
        raise ValueError("boost_params must be a mapping")
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping")
    lmax = int(boost_params.get("lmax", metadata.get("multipole_cutoff", 0)))
    if lmax < 0:
        raise ValueError("lmax must be non-negative")
    ordering = str(boost_params.get("ordering", metadata.get("ordering", DEFAULT_HARMONIC_ORDERING)))
    det_component = None if alm_det is None else alm_det
    stoch_component = None if alm_stoch is None else alm_stoch
    any_component = any(
        key in boost_params for key in ("alm_T", "alm_E", "alm_B")
    )
    boost_T = _coerce_component(boost_params.get("alm_T"), lmax=lmax, component="boost alm_T")
    boost_E = _coerce_component(boost_params.get("alm_E"), lmax=lmax, component="boost alm_E")
    boost_B = _coerce_component(boost_params.get("alm_B"), lmax=lmax, component="boost alm_B")
    payload_metadata = {
        "family": metadata.get("family"),
        "branch": metadata.get("branch", "orthogonal"),
        "backend": metadata.get("backend"),
        "ordering": ordering,
        "boost_applied": any_component,
        "global_tilt_present": bool(metadata.get("global_tilt_present", False)),
        "component_kind": "boost",
        "component_status": "observer_boost_applied" if any_component else "zero_filled_no_boost",
        "local_boost_contract": metadata.get("local_boost_contract"),
        "global_tilt_contract": metadata.get("global_tilt_contract"),
        "split_semantics": "output_only_local_boost",
        "det_component_present": det_component is not None,
        "stoch_component_present": stoch_component is not None,
    }
    return BoostArchive(
        lmax=lmax,
        ordering=ordering,
        alm_T=boost_T,
        alm_E=boost_E,
        alm_B=boost_B,
        metadata_json=json.dumps(payload_metadata, sort_keys=True),
    )


def _solver_summary(
    output: SolverCoreOutput,
    *,
    ordering: str,
    boost_applied: bool,
    gate_registry: Mapping[str, object],
) -> dict[str, Any]:
    residual_summary: dict[str, Any] = {}
    for key in _NUMERIC_RESIDUAL_KEYS:
        if key in output.metadata and output.metadata[key] is not None:
            value = float(output.metadata[key])
            if not np.isfinite(value):
                raise ValueError(f"non-finite residual metadata at {key}")
            residual_summary[key] = value
    bundle_gates = collect_gate_bundles(gate_registry)
    gate_status = summarize_gate_status(gate_registry)
    summary_metadata = OutputMetadata.from_solver_output(
        output,
        ordering=ordering,
        component_kind="solver_summary",
        component_status="solver_summary",
        boost_applied=boost_applied,
        gate_registry=gate_registry,
        residual_summary=residual_summary,
    )
    return {
        "family": summary_metadata.family,
        "branch": summary_metadata.branch,
        "backend": summary_metadata.backend,
        "ic_mode": output.metadata.get("seed_injection_mode", "unspecified"),
        "lmax_dev": _lmax(output),
        "lmax_prod": _lmax(output),
        "ordering": summary_metadata.ordering,
        "boost_applied": bool(summary_metadata.boost_applied),
        "global_tilt_present": bool(summary_metadata.global_tilt_present),
        "propagator_readiness": output.metadata.get("propagator_readiness"),
        "propagator_exactness": output.metadata.get("propagator_exactness"),
        "covariance_readiness": output.metadata.get("covariance_readiness"),
        "tilt_background_owner": output.metadata.get("tilt_background_owner"),
        "requested_integrator_family": output.metadata.get("requested_integrator_family"),
        "resolved_solver_method": output.metadata.get("resolved_solver_method"),
        "executor_realization": output.metadata.get("executor_realization"),
        "residual_summary": residual_summary,
        "gate_status": {
            **gate_status,
            "boost_split_present": True,
            "manifest_claim_tier": summary_metadata.manifest_claim_tier,
            "manifest_production_status": summary_metadata.manifest_production_status,
        },
        "gate_score": score_branch_readiness(gate_registry),
        "bundle_gates": [gate for gate in gate_status if gate in bundle_gates],
    }


def output_split_gate_bundle(
    output: SolverCoreOutput,
    *,
    ordering: str = DEFAULT_HARMONIC_ORDERING,
    stochastic_alm_T: object | None = None,
    stochastic_alm_E: object | None = None,
    stochastic_alm_B: object | None = None,
    boost_alm_T: object | None = None,
    boost_alm_E: object | None = None,
    boost_alm_B: object | None = None,
) -> GateBundle:
    """Emit the machine-readable PR-10 output-split gate bundle."""

    lmax = _lmax(output)
    det_T = _coerce_component(output.alm_T, lmax=lmax, component="deterministic alm_T")
    det_E = _coerce_component(output.alm_E, lmax=lmax, component="deterministic alm_E")
    det_B = _coerce_component(output.alm_B, lmax=lmax, component="deterministic alm_B")
    stoch_T = _coerce_component(stochastic_alm_T, lmax=lmax, component="stochastic alm_T")
    stoch_E = _coerce_component(stochastic_alm_E, lmax=lmax, component="stochastic alm_E")
    stoch_B = _coerce_component(stochastic_alm_B, lmax=lmax, component="stochastic alm_B")
    boost = observer_boost_output(
        output,
        ordering=ordering,
        alm_T=boost_alm_T,
        alm_E=boost_alm_E,
        alm_B=boost_alm_B,
    )
    boost_metadata = json.loads(str(boost.metadata_json))
    # P-05 wiring: surface the b_mode_output_support flag on the gate
    # bundle so downstream consumers cannot mistake the FLRW-zero
    # ``alm_B`` column for a true B-mode prediction. The flag is
    # *opt-in*: tests that bypass ``build_solver_core_output`` and
    # populate ``alm_B`` directly stay unaffected unless they declare
    # ``b_mode_output_support = "flrw_zero_only"`` explicitly.
    b_mode_support = str(output.metadata.get("b_mode_output_support", "unknown"))
    b_mode_block_reason = str(
        output.metadata.get(
            "b_mode_block_reason",
            "flrw_bessel_projector_zeros_b_by_construction",
        )
    )
    det_b_norm = float(np.linalg.norm(det_B))
    stoch_b_norm = float(np.linalg.norm(stoch_B))
    boost_b_norm = float(np.linalg.norm(boost.alm_B))
    b_zero_only = b_mode_support == "flrw_zero_only"
    # Honest contract: when only the FLRW projector is wired, the deterministic
    # B column must be identically zero. Stochastic / boost contributions are
    # output-side and may carry energy.
    b_mode_zero_consistent = (not b_zero_only) or det_b_norm == 0.0
    map_support = str(output.metadata.get("map_output_support", "not_implemented"))
    return make_gate_bundle(
        "output_split_gate",
        family=str(output.metadata.get("bianchi_type", "unknown")),
        branch=str(output.metadata.get("bianchi_branch", "orthogonal")),
        backend=str(output.metadata.get("source_propagator_realization", "unknown")),
        truncation={"ell_max": lmax, "ordering": ordering},
        residual_summary={
            "det_norm": float(np.linalg.norm(np.concatenate([det_T, det_E, det_B]))),
            "stoch_norm": float(np.linalg.norm(np.concatenate([stoch_T, stoch_E, stoch_B]))),
            "boost_norm": float(np.linalg.norm(np.concatenate([boost.alm_T, boost.alm_E, boost.alm_B]))),
            "det_alm_b_norm": det_b_norm,
            "stoch_alm_b_norm": stoch_b_norm,
            "boost_alm_b_norm": boost_b_norm,
        },
        known_limit_checks={
            "det_component_present": True,
            "stoch_component_present": True,
            "boost_component_present": True,
            "boost_metadata_valid": bool(boost_metadata["split_semantics"] == "output_only_local_boost"),
            "b_mode_zero_consistent_with_support_flag": bool(b_mode_zero_consistent),
        },
        forbidden_shortcut_checks={
            "no_local_boost_merged_into_global_tilt": bool(
                output.metadata.get("tilt_boost_separation") == "explicit_nonmerged"
            ),
            "observer_neutral_solver_output": bool(output.metadata.get("observer_neutral", False)),
            "no_flrw_zero_b_marketed_as_prediction": bool(
                (not b_zero_only) or det_b_norm == 0.0
            ),
            "no_unpopulated_map_marketed_as_output": bool(
                (map_support != "not_implemented")
                or (output.map_T is None and output.map_Q is None and output.map_U is None)
            ),
        },
        metadata={
            "global_tilt_present": bool(output.metadata.get("tilt_enabled", False)),
            "boost_applied": bool(boost_metadata["boost_applied"]),
            "component_ordering": ordering,
            "b_mode_output_support": b_mode_support,
            "b_mode_block_reason": b_mode_block_reason,
            "map_output_support": map_support,
        },
        passed=bool(b_mode_zero_consistent),
        opened_claim="output split gate frozen, local boost kept output-only",
    )


def resolve_output_gate_registry(
    output: SolverCoreOutput,
    *,
    ordering: str = DEFAULT_HARMONIC_ORDERING,
    gate_registry: Mapping[str, object] | None = None,
    stochastic_alm_T: object | None = None,
    stochastic_alm_E: object | None = None,
    stochastic_alm_B: object | None = None,
    boost_alm_T: object | None = None,
    boost_alm_E: object | None = None,
    boost_alm_B: object | None = None,
) -> dict[str, object]:
    """Return the output-aware gate registry merged with embedded runtime bundles."""

    registry: dict[str, object] = {}
    embedded = output.metadata.get("gate_registry")
    if isinstance(embedded, Mapping):
        registry.update(dict(embedded))
    if gate_registry is not None:
        registry.update(dict(gate_registry))
    registry["output_split_gate"] = output_split_gate_bundle(
        output,
        ordering=ordering,
        stochastic_alm_T=stochastic_alm_T,
        stochastic_alm_E=stochastic_alm_E,
        stochastic_alm_B=stochastic_alm_B,
        boost_alm_T=boost_alm_T,
        boost_alm_E=boost_alm_E,
        boost_alm_B=boost_alm_B,
    )
    return registry


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
    gate_registry: Mapping[str, object] | None = None,
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
    registry = resolve_output_gate_registry(
        output,
        ordering=ordering,
        gate_registry=gate_registry,
        stochastic_alm_T=stochastic_alm_T,
        stochastic_alm_E=stochastic_alm_E,
        stochastic_alm_B=stochastic_alm_B,
        boost_alm_T=boost_alm_T,
        boost_alm_E=boost_alm_E,
        boost_alm_B=boost_alm_B,
    )
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
        gate_registry=registry,
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


def write_family_residual_archive(
    family_residual_packs: Mapping[str, Any],
    outdir: str | Path,
    *,
    filename: str = "family_residuals.json",
) -> str:
    """Sidecar writer for the v5 PR-08 family-backend_gate evidence.

    Accepts a mapping ``{family: ResidualPack}`` (as returned by
    ``bass.los.families.residual_report.build_family_residual_packs``)
    and writes a JSON file next to the other archive outputs. Each
    pack is serialized via ``ResidualPack.as_payload()``.

    The file is emitted separately from ``write_output_archive`` so that
    callers with no family-backend surface can skip it without forcing
    a contract change on ``SolverCoreOutput``.

    Returns
    -------
    str
        Absolute path of the written JSON file.
    """
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / filename
    payload = {
        family: (
            pack.as_payload() if hasattr(pack, "as_payload") else dict(pack)
        )
        for family, pack in family_residual_packs.items()
    }
    summary = {
        "family_count": len(payload),
        "all_passed": all(
            bool(entry.get("passed", False)) for entry in payload.values()
        ),
        "families": sorted(payload),
    }
    path.write_text(
        json.dumps({"summary": summary, "packs": payload}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return str(path)
