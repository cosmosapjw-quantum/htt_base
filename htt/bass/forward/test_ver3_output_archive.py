from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from common.contracts import ArtifactManifest, SolverCoreOutput

from bass.forward import (
    BoostArchive,
    DEFAULT_HARMONIC_ORDERING,
    alm_power_by_l,
    observer_boost_output,
    observer_boost_output_from_components,
    validate_alm_archive,
    write_output_archive,
)
from bass.validation import GATE_LADDER, make_gate_bundle


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.ver3.output.archive",
        artifact_path="artifacts/bass/ver3_output_archive",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="deadbeef",
        config_hash="cfg-hash",
        input_hashes=["seed"],
        code_version="0.0-test",
        schema_version="ver3-v0",
    )


def _solver_output(*, with_nan_residual: bool = False) -> SolverCoreOutput:
    lmax = 2
    size = (lmax + 1) ** 2
    metadata = {
        "bianchi_type": "V",
        "bianchi_branch": "orthogonal",
        "harmonic_basis": "m_explicit",
        "eb_sign_convention": "cmb",
        "multipole_cutoff": lmax,
        "tilt_enabled": False,
        "thomson_mode": "electron_frame_projected",
        "source_propagator_realization": "class_b_open_matrix_approx",
        "seed_injection_mode": "continued_anchor",
        "visibility_tau_reion": np.nan if with_nan_residual else 0.054,
        "map_output_support": "not_implemented",
    }
    payload = {
        "representation": "ver2_native_pstf_sphere_reconstruction",
        "coefficient_representation": "ver2_native_pstf_final_slice",
        "ell_max": lmax,
        "values": np.linspace(1.0e-6, 9.0e-6, size),
        "sphere_samples": np.linspace(0.1, 0.9, 15),
    }
    return SolverCoreOutput(
        alm_T=payload,
        alm_E={**payload, "values": np.linspace(2.0e-6, 1.0e-5, size)},
        alm_B={**payload, "values": np.linspace(0.0, 8.0e-6, size)},
        map_T=None,
        map_Q=None,
        map_U=None,
        deterministic_template={"kind": "test"},
        anisotropic_covariance=None,
        metadata=metadata,
        manifest=_manifest(),
    )


def _gate_registry() -> dict[str, object]:
    return {
        gate: make_gate_bundle(
            gate,
            family="V",
            branch="orthogonal",
            backend="class_b_open_matrix_approx",
            truncation={"ell_max": 2},
            residual_summary={"max_residual": 1.0e-8},
            known_limit_checks={"status": "passed"},
            forbidden_shortcut_checks={"no_fake_support": True},
            metadata={"artifact": f"{gate}.json"},
        )
        for gate in GATE_LADDER[:-1]
    }


def test_observer_boost_output_is_zero_filled_when_not_applied() -> None:
    payload = observer_boost_output(_solver_output())
    assert isinstance(payload, BoostArchive)
    assert payload["lmax"] == 2
    assert payload["ordering"] == DEFAULT_HARMONIC_ORDERING
    np.testing.assert_allclose(payload["alm_T"], 0.0)
    np.testing.assert_allclose(payload["alm_E"], 0.0)
    np.testing.assert_allclose(payload["alm_B"], 0.0)
    metadata = json.loads(payload["metadata_json"])
    assert metadata["boost_applied"] is False
    assert metadata["global_tilt_present"] is False


def test_write_output_archive_writes_required_schema(tmp_path: Path) -> None:
    output = _solver_output()
    written = write_output_archive(output, tmp_path, gate_registry=_gate_registry())
    assert sorted(written) == [
        "alm_boost.npz",
        "alm_det.npz",
        "alm_stoch.npz",
        "solver_summary.json",
    ]
    summary = json.loads((tmp_path / "solver_summary.json").read_text(encoding="utf-8"))
    assert summary["family"] == "V"
    assert summary["branch"] == "orthogonal"
    assert summary["backend"] == "class_b_open_matrix_approx"
    assert summary["ordering"] == DEFAULT_HARMONIC_ORDERING
    assert summary["boost_applied"] is False
    assert summary["global_tilt_present"] is False
    assert summary["family_backend_status"] is None
    assert summary["stochastic_channel_status"] == "placeholder"
    assert summary["b_mode_output_support"] == "unknown"
    assert summary["production_cutoff_status"] == "production_candidate"
    assert summary["fitting_allowed"] is True
    assert summary["diagnostic_only"] is False
    assert summary["gate_status"]["output_split_gate"] == "open"
    assert summary["gate_status"]["fitting_gate"] == "closed"
    assert summary["gate_score"] == 8
    assert "output_split_gate" in summary["bundle_gates"]

    det = np.load(tmp_path / "alm_det.npz", allow_pickle=False)
    stoch = np.load(tmp_path / "alm_stoch.npz", allow_pickle=False)
    boost = np.load(tmp_path / "alm_boost.npz", allow_pickle=False)
    assert int(det["lmax"]) == 2
    assert det["ordering"].item() == DEFAULT_HARMONIC_ORDERING
    assert det["alm_T"].shape == (9,)
    assert stoch["alm_E"].shape == (9,)
    np.testing.assert_allclose(stoch["alm_T"], 0.0)
    np.testing.assert_allclose(boost["alm_B"], 0.0)
    det_meta = json.loads(det["metadata_json"].item())
    stoch_meta = json.loads(stoch["metadata_json"].item())
    boost_meta = json.loads(boost["metadata_json"].item())
    assert det_meta["component_kind"] == "deterministic"
    assert stoch_meta["component_status"] == "placeholder_zero_filled_no_stochastic_component"
    assert stoch_meta["stochastic_channel_status"] == "placeholder"
    assert stoch_meta["stochastic_block_reason"] == (
        "stochastic_lcdm_realization_injection_not_implemented"
    )
    assert boost_meta["component_kind"] == "boost"

    validated = validate_alm_archive(tmp_path, require_fitting_ready=True)
    assert validated["archive_valid"] is True
    assert validated["lmax"] == 2
    assert validated["component_kinds"] == {
        "deterministic": "deterministic",
        "stochastic": "stochastic",
        "boost": "boost",
    }
    assert validated["fitting_allowed"] is True
    np.testing.assert_allclose(validated["power_by_l"]["boost_T"], 0.0)


def test_alm_power_by_l_uses_ell_m_blocks() -> None:
    alm = np.arange(9, dtype=np.float64)
    power = alm_power_by_l(alm, lmax=2)
    assert power.shape == (3,)
    assert power[0] == pytest.approx(0.0)
    assert power[1] == pytest.approx(np.mean(np.array([1.0, 2.0, 3.0]) ** 2))
    assert power[2] == pytest.approx(np.mean(np.array([4.0, 5.0, 6.0, 7.0, 8.0]) ** 2))


def test_validate_alm_archive_rejects_shape_tamper(tmp_path: Path) -> None:
    write_output_archive(_solver_output(), tmp_path, gate_registry=_gate_registry())
    np.savez(
        tmp_path / "alm_boost.npz",
        lmax=2,
        ordering=DEFAULT_HARMONIC_ORDERING,
        alm_T=np.zeros(8),
        alm_E=np.zeros(8),
        alm_B=np.zeros(8),
        metadata_json=json.dumps(
            {
                "component_kind": "boost",
                "split_semantics": "output_only_local_boost",
            }
        ),
    )
    with pytest.raises(ValueError, match="shape"):
        validate_alm_archive(tmp_path)


def test_component_form_observer_boost_output_returns_boost_archive() -> None:
    archive = observer_boost_output(
        np.zeros(9),
        None,
        {"lmax": 2, "alm_T": np.ones(9)},
        {"family": "V", "branch": "orthogonal", "multipole_cutoff": 2},
    )
    assert isinstance(archive, BoostArchive)
    assert archive["lmax"] == 2
    np.testing.assert_allclose(archive["alm_T"], 1.0)


def test_component_helper_observer_boost_output_matches_component_signature() -> None:
    archive = observer_boost_output_from_components(
        np.zeros(9),
        None,
        {"lmax": 2},
        {"family": "V", "branch": "orthogonal", "multipole_cutoff": 2},
    )
    assert isinstance(archive, BoostArchive)
    np.testing.assert_allclose(archive["alm_E"], 0.0)


def test_write_output_archive_rejects_nonfinite_residual_summary(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-finite residual metadata"):
        write_output_archive(_solver_output(with_nan_residual=True), tmp_path)


def test_write_output_archive_keeps_output_gate_closed_without_registry(tmp_path: Path) -> None:
    write_output_archive(_solver_output(), tmp_path)
    summary = json.loads((tmp_path / "solver_summary.json").read_text(encoding="utf-8"))
    assert summary["gate_status"]["authority_freeze"] == "closed"
    assert summary["gate_status"]["output_split_gate"] == "unavailable"
    assert summary["gate_status"]["fitting_gate"] == "unavailable"
    assert summary["gate_score"] == 0


def test_write_output_archive_uses_embedded_upstream_gate_registry(tmp_path: Path) -> None:
    output = _solver_output()
    output.metadata["gate_registry"] = _gate_registry()
    write_output_archive(output, tmp_path)
    summary = json.loads((tmp_path / "solver_summary.json").read_text(encoding="utf-8"))
    assert summary["gate_status"]["authority_freeze"] == "open"
    assert summary["gate_status"]["output_split_gate"] == "open"
    assert "authority_freeze" in summary["bundle_gates"]
