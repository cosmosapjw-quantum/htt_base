"""PA-10 cross-channel non-leakage regression.

The audit (R17-P3) found the deterministic / stochastic / boost split
is *structurally* present in :mod:`bass.forward.ver3_output_archive`
but lacked a regression that pins the **cross-channel non-leakage**
invariant: providing a boost array on disk must not silently fold into
the deterministic channel, and vice versa.

This file pins three load-bearing invariants that any future
optimization must preserve:

1. **Deterministic byte-identity** — ``alm_det.npz`` is byte-identical
   to the solver's ``alm_{T,E,B}`` fields, irrespective of whether
   stochastic or boost components are passed.
2. **Boost isolation** — non-zero ``boost_alm_*`` arguments populate
   only ``alm_boost.npz``; ``alm_det.npz`` and ``alm_stoch.npz`` remain
   bit-for-bit unaffected.
3. **Stochastic isolation** — non-zero ``stochastic_alm_*`` arguments
   populate only ``alm_stoch.npz``; ``alm_det.npz`` remains
   bit-for-bit unaffected.

A failure on any of these invariants indicates that an "optimization"
or refactor folded one channel into another — exactly the
release-honesty failure the audit flagged.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from common.contracts import ArtifactManifest, SolverCoreOutput

from bass.forward import write_output_archive
from bass.validation import GATE_LADDER, make_gate_bundle


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.test.split_non_leakage",
        artifact_path="artifacts/bass/test_split",
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


def _solver_output(*, lmax: int = 2) -> SolverCoreOutput:
    size = (lmax + 1) ** 2
    rng = np.random.default_rng(0xBA55)
    metadata = {
        "bianchi_type": "I",
        "bianchi_branch": "orthogonal",
        "harmonic_basis": "m_explicit",
        "eb_sign_convention": "cmb",
        "multipole_cutoff": lmax,
        "tilt_enabled": False,
        "thomson_mode": "electron_frame_projected",
        "source_propagator_realization": "axis_aligned_plane_wave",
        "seed_injection_mode": "adiabatic_regular",
        "visibility_tau_reion": 0.054,
        "map_output_support": "not_implemented",
    }
    payload_T = {
        "representation": "ver2_native_pstf_sphere_reconstruction",
        "coefficient_representation": "ver2_native_pstf_final_slice",
        "ell_max": lmax,
        "values": rng.standard_normal(size).astype(np.float64),
        "sphere_samples": rng.standard_normal(15).astype(np.float64),
    }
    payload_E = {
        **payload_T,
        "values": rng.standard_normal(size).astype(np.float64),
    }
    payload_B = {
        **payload_T,
        "values": np.zeros(size, dtype=np.float64),  # FLRW B is zero
    }
    return SolverCoreOutput(
        alm_T=payload_T,
        alm_E=payload_E,
        alm_B=payload_B,
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
            family="I",
            branch="orthogonal",
            backend="axis_aligned_plane_wave",
            truncation={"ell_max": 2},
            residual_summary={"max_residual": 1.0e-8},
            known_limit_checks={"status": "passed"},
            forbidden_shortcut_checks={"no_fake_support": True},
            metadata={"artifact": f"{gate}.json"},
        )
        for gate in GATE_LADDER[:-1]
    }


def _read_alm(path: Path, field: str) -> np.ndarray:
    return np.load(path, allow_pickle=False)[field]


def test_deterministic_channel_is_bit_identical_to_solver_alms(tmp_path: Path) -> None:
    """``alm_det.npz`` must byte-match the solver's ``alm_{T,E,B}`` fields."""
    output = _solver_output()
    write_output_archive(output, tmp_path, gate_registry=_gate_registry())
    np.testing.assert_array_equal(
        _read_alm(tmp_path / "alm_det.npz", "alm_T"),
        np.asarray(output.alm_T["values"], dtype=np.float64),
    )
    np.testing.assert_array_equal(
        _read_alm(tmp_path / "alm_det.npz", "alm_E"),
        np.asarray(output.alm_E["values"], dtype=np.float64),
    )
    np.testing.assert_array_equal(
        _read_alm(tmp_path / "alm_det.npz", "alm_B"),
        np.asarray(output.alm_B["values"], dtype=np.float64),
    )


def test_boost_input_does_not_leak_into_deterministic(tmp_path: Path) -> None:
    """A non-zero boost argument must never appear in ``alm_det.npz``."""
    output = _solver_output()
    boost_T = np.full((3 + 1) ** 2 - 9 + 9, 7.0, dtype=np.float64)
    # Coerce to expected size for lmax=2.
    boost_T = boost_T[:9]
    write_output_archive(
        output,
        tmp_path,
        gate_registry=_gate_registry(),
        boost_alm_T=boost_T,
    )
    np.testing.assert_array_equal(
        _read_alm(tmp_path / "alm_det.npz", "alm_T"),
        np.asarray(output.alm_T["values"], dtype=np.float64),
    )
    np.testing.assert_array_equal(
        _read_alm(tmp_path / "alm_boost.npz", "alm_T"), boost_T
    )
    boost_meta = json.loads(
        _read_alm(tmp_path / "alm_boost.npz", "metadata_json").item()
    )
    assert boost_meta["component_kind"] == "boost"
    assert boost_meta["boost_applied"] is True


def test_stochastic_input_does_not_leak_into_deterministic(tmp_path: Path) -> None:
    """A non-zero stochastic argument must never appear in ``alm_det.npz``."""
    output = _solver_output()
    stoch_T = np.full(9, 3.0, dtype=np.float64)
    write_output_archive(
        output,
        tmp_path,
        gate_registry=_gate_registry(),
        stochastic_alm_T=stoch_T,
    )
    np.testing.assert_array_equal(
        _read_alm(tmp_path / "alm_det.npz", "alm_T"),
        np.asarray(output.alm_T["values"], dtype=np.float64),
    )
    np.testing.assert_array_equal(
        _read_alm(tmp_path / "alm_stoch.npz", "alm_T"), stoch_T
    )
    stoch_meta = json.loads(
        _read_alm(tmp_path / "alm_stoch.npz", "metadata_json").item()
    )
    assert stoch_meta["component_kind"] == "stochastic"
    assert stoch_meta["stochastic_channel_status"] == "implemented"


def test_boost_and_stochastic_do_not_cross_contaminate(tmp_path: Path) -> None:
    """Boost and stochastic inputs must remain in their own NPZ files."""
    output = _solver_output()
    boost_T = np.full(9, 7.0, dtype=np.float64)
    stoch_E = np.full(9, 3.0, dtype=np.float64)
    write_output_archive(
        output,
        tmp_path,
        gate_registry=_gate_registry(),
        boost_alm_T=boost_T,
        stochastic_alm_E=stoch_E,
    )
    # boost.alm_T has the boost; stoch.alm_T must remain zero
    np.testing.assert_array_equal(
        _read_alm(tmp_path / "alm_boost.npz", "alm_T"), boost_T
    )
    np.testing.assert_allclose(_read_alm(tmp_path / "alm_stoch.npz", "alm_T"), 0.0)
    # stoch.alm_E has the stochastic; boost.alm_E must remain zero
    np.testing.assert_array_equal(
        _read_alm(tmp_path / "alm_stoch.npz", "alm_E"), stoch_E
    )
    np.testing.assert_allclose(_read_alm(tmp_path / "alm_boost.npz", "alm_E"), 0.0)


def test_no_boost_or_stochastic_yields_zero_filled_files(tmp_path: Path) -> None:
    """When no auxiliary channels are provided, both files must be zero."""
    output = _solver_output()
    write_output_archive(output, tmp_path, gate_registry=_gate_registry())
    for component in ("alm_T", "alm_E", "alm_B"):
        np.testing.assert_allclose(
            _read_alm(tmp_path / "alm_stoch.npz", component), 0.0
        )
        np.testing.assert_allclose(
            _read_alm(tmp_path / "alm_boost.npz", component), 0.0
        )


def test_archive_files_are_exactly_four(tmp_path: Path) -> None:
    """Schema lock — the archive must produce exactly four artifacts."""
    output = _solver_output()
    write_output_archive(output, tmp_path, gate_registry=_gate_registry())
    actual = sorted(p.name for p in tmp_path.iterdir())
    assert actual == [
        "alm_boost.npz",
        "alm_det.npz",
        "alm_stoch.npz",
        "solver_summary.json",
    ]


def test_metadata_kind_is_distinct_per_file(tmp_path: Path) -> None:
    """Each component file must declare a distinct ``component_kind``."""
    output = _solver_output()
    write_output_archive(output, tmp_path, gate_registry=_gate_registry())
    kinds = {
        json.loads(_read_alm(tmp_path / "alm_det.npz", "metadata_json").item())[
            "component_kind"
        ],
        json.loads(_read_alm(tmp_path / "alm_stoch.npz", "metadata_json").item())[
            "component_kind"
        ],
        json.loads(_read_alm(tmp_path / "alm_boost.npz", "metadata_json").item())[
            "component_kind"
        ],
    }
    assert kinds == {"deterministic", "stochastic", "boost"}
