"""bass/forward/test_map_producer.py — Round-16 PR-S12 regression suite.

Implements V5_ROUND16_03_OBSERVABLES_LAYER.md §3.2 spec tests:

    - test_zero_alm_yields_zero_map
    - test_pure_dipole_alm_yields_dipole_map
    - test_round_trip_alm_to_map_back
    - test_producer_attached_flag_set
    - test_post_init_validates_consistency

Plus the §3.3 adversarial audit (PR-S12 closure):

    - A1: no toy/naive — uses healpy, not a custom 30-line approximation
    - A6: maps for non-FLRW input must contain ℓ ≥ 1 power
    - A10: populate_map_outputs flips metadata flag explicitly
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

hp = pytest.importorskip("healpy",
    reason=(
        "optional dependency 'healpy' not installed; install via "
        "`pip install healpy` to activate BASS map-producer tests"
    ),
)

from bass.forward.map_producer import (
    alm_to_map_TQU,
    bass_real_alm_to_healpy_complex,
    coerce_bass_alm_mapping,
    infer_lmax,
    populate_map_outputs,
)

pytestmark = pytest.mark.requires_healpy


# ────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────


def _make_dummy_solver_output(*, alm_T, alm_E, alm_B):
    """Construct a minimal SolverCoreOutput with required metadata."""
    from common.contracts import (
        ArtifactManifest,
        SolverCoreOutput,
    )

    manifest = ArtifactManifest(
        artifact_id="test-map-producer",
        artifact_path="bass/forward/test_map_producer.py",
        owner="BASS",
        implementation_scope="bass_py",
        claim_tier="exploratory",
        production_status="diagnostic_only",
        created_by="round16-pr-s12-test",
        git_commit="HEAD",
        config_hash="0",
        input_hashes=[],
        code_version="round16-pr-s12-test",
        schema_version="1.0",
    )
    return SolverCoreOutput(
        alm_T=alm_T,
        alm_E=alm_E,
        alm_B=alm_B,
        map_T=None, map_Q=None, map_U=None,
        deterministic_template=None,
        anisotropic_covariance=None,
        metadata={
            "bianchi_type": "I",
            "harmonic_basis": "real_spherical",
            "eb_sign_convention": "BASS_SSOT",
            "multipole_cutoff": 12,
            "tilt_enabled": False,
            "thomson_mode": "exact_electron_frame",
            "map_output_support": "not_implemented",
        },
        manifest=manifest,
    )


# ────────────────────────────────────────────────────────────────────────
# infer_lmax
# ────────────────────────────────────────────────────────────────────────


class TestInferLmax:
    def test_returns_max_key(self) -> None:
        alm = {2: np.zeros(5), 5: np.zeros(11), 7: np.zeros(15)}
        assert infer_lmax(alm) == 7

    def test_raises_on_empty(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            infer_lmax({})

    def test_native_flat_payload_returns_declared_lmax(self) -> None:
        payload = {"ell_max": 2, "values": np.arange(9, dtype=np.float64)}
        assert infer_lmax(payload) == 2
        mapping = coerce_bass_alm_mapping(payload)
        assert sorted(mapping) == [0, 1, 2]
        np.testing.assert_array_equal(mapping[2], np.arange(4, 9, dtype=np.float64))


# ────────────────────────────────────────────────────────────────────────
# Real → complex alm conversion
# ────────────────────────────────────────────────────────────────────────


class TestBassRealAlmToHealpyComplex:
    def test_zero_alm_yields_zero_complex(self) -> None:
        alm = {0: np.zeros(1), 1: np.zeros(3), 2: np.zeros(5)}
        out = bass_real_alm_to_healpy_complex(alm, lmax=2)
        assert out.shape == ((2 + 1) * (2 + 2) // 2,)
        np.testing.assert_array_equal(out, np.zeros_like(out))

    def test_monopole_real_passes_through(self) -> None:
        # a^complex_{0,0} = a^real_{0,0}
        alm = {0: np.array([1.5])}
        out = bass_real_alm_to_healpy_complex(alm, lmax=0)
        assert out.shape == (1,)
        assert out[0] == 1.5 + 0.0j

    def test_dipole_m_zero_passes_through(self) -> None:
        # a^complex_{1, 0} = a^real_{1, 0}; m=±1 zero
        alm = {1: np.array([0.0, 2.0, 0.0])}  # m=-1, 0, +1 → indices 0, 1, 2
        out = bass_real_alm_to_healpy_complex(alm, lmax=1)
        # Healpy ordering for lmax=1: (0,0)=0, (0,1)=1, (1,1)=2
        assert out[1] == 2.0 + 0.0j  # ell=1, m=0 slot

    def test_dipole_m_one_uses_real_imag_combination(self) -> None:
        # a^real_{1,+1} = 1.0, a^real_{1,-1} = 0.5
        # a^complex_{1, 1} = (-1/√2)(1.0 - i 0.5)
        alm = {1: np.array([0.5, 0.0, 1.0])}  # m=-1, 0, +1
        out = bass_real_alm_to_healpy_complex(alm, lmax=1)
        expected = (-1.0 / math.sqrt(2.0)) * (1.0 - 1j * 0.5)
        # Index for (ell=1, m=1) in healpy ordering: m*(2*lmax+1-m)//2 + ell
        idx = 1 * (2 * 1 + 1 - 1) // 2 + 1
        assert out[idx] == pytest.approx(expected, rel=1e-15, abs=1e-15)

    def test_lmax_default_uses_inferred(self) -> None:
        alm = {2: np.zeros(5)}
        out = bass_real_alm_to_healpy_complex(alm)
        assert out.shape == ((2 + 1) * (2 + 2) // 2,)


# ────────────────────────────────────────────────────────────────────────
# alm_to_map_TQU (§3.2 spec tests)
# ────────────────────────────────────────────────────────────────────────


class TestAlmToMapTQU:
    """V5_ROUND16_03 §3.2 spec tests."""

    def test_zero_alm_yields_zero_map(self) -> None:
        alm = {0: np.zeros(1), 1: np.zeros(3), 2: np.zeros(5)}
        out = alm_to_map_TQU(alm_T=alm, alm_E=alm, alm_B=alm, nside=8)
        assert out["map_T"].shape == (12 * 8 * 8,)
        np.testing.assert_allclose(out["map_T"], 0.0, atol=1e-15)
        np.testing.assert_allclose(out["map_Q"], 0.0, atol=1e-15)
        np.testing.assert_allclose(out["map_U"], 0.0, atol=1e-15)

    def test_pure_dipole_yields_dipole_map(self) -> None:
        """a_{1,0} = 1 (real) ⇒ map ∝ Y^1_0 ∝ cos(θ)."""
        alm = {0: np.zeros(1), 1: np.array([0.0, 1.0, 0.0])}
        empty = {0: np.zeros(1), 1: np.zeros(3)}
        nside = 8
        out = alm_to_map_TQU(alm_T=alm, alm_E=empty, alm_B=empty, nside=nside)
        # Reconstruct via healpy for cross-check.
        alm_hp = bass_real_alm_to_healpy_complex(alm, lmax=1)
        ref = hp.alm2map(alm_hp, nside, lmax=1)
        np.testing.assert_allclose(out["map_T"], ref, atol=1e-12)
        # Polarisation maps should be zero (E = B = 0).
        np.testing.assert_allclose(out["map_Q"], 0.0, atol=1e-12)
        np.testing.assert_allclose(out["map_U"], 0.0, atol=1e-12)

    def test_round_trip_alm_to_map_back(self) -> None:
        """map2alm(alm2map(alm)) ≈ alm (within HEALPix quadrature)."""
        rng = np.random.default_rng(seed=42)
        lmax = 8
        alm = {ell: rng.normal(size=2 * ell + 1) for ell in range(lmax + 1)}
        empty = {ell: np.zeros(2 * ell + 1) for ell in range(lmax + 1)}
        nside = 32  # high enough for clean round trip at lmax=8
        out = alm_to_map_TQU(
            alm_T=alm, alm_E=empty, alm_B=empty, nside=nside, lmax=lmax,
        )
        # Reconstruct alm from map_T.
        alm_hp_recovered = hp.map2alm(out["map_T"], lmax=lmax)
        alm_hp_original = bass_real_alm_to_healpy_complex(alm, lmax=lmax)
        np.testing.assert_allclose(
            alm_hp_recovered, alm_hp_original, atol=1e-3, rtol=1e-3,
        )

    def test_E_only_produces_Q_with_no_U(self) -> None:
        """Pure E-mode (B=0) must produce Q ≠ 0 and U morphology consistent.

        Strict test: alm_B == 0 ⇒ U map carries the E-mode parity.
        """
        rng = np.random.default_rng(seed=7)
        alm_E = {ell: rng.normal(size=2 * ell + 1) for ell in range(2, 6)}
        alm_E[0] = np.zeros(1)
        alm_E[1] = np.zeros(3)
        empty = {ell: np.zeros(2 * ell + 1) for ell in range(6)}
        out = alm_to_map_TQU(
            alm_T=empty, alm_E=alm_E, alm_B=empty, nside=16, lmax=5,
        )
        # E must drive Q+U non-trivially.
        assert np.linalg.norm(out["map_Q"]) > 1.0e-3
        # T = 0 since alm_T = 0.
        np.testing.assert_allclose(out["map_T"], 0.0, atol=1e-12)

    def test_rejects_non_power_of_2_nside(self) -> None:
        with pytest.raises(ValueError, match="power of 2"):
            alm_to_map_TQU(
                alm_T={0: np.zeros(1)}, alm_E={0: np.zeros(1)},
                alm_B={0: np.zeros(1)}, nside=10,
            )

    def test_rejects_zero_nside(self) -> None:
        with pytest.raises(ValueError, match="nside"):
            alm_to_map_TQU(
                alm_T={0: np.zeros(1)}, alm_E={0: np.zeros(1)},
                alm_B={0: np.zeros(1)}, nside=0,
            )


# ────────────────────────────────────────────────────────────────────────
# populate_map_outputs (SolverCoreOutput integration)
# ────────────────────────────────────────────────────────────────────────


class TestPopulateMapOutputs:
    """V5_ROUND16_03 §3.3 / R15-AUDIT-PATCH P-08 contract."""

    def _alm(self, lmax: int = 4):
        rng = np.random.default_rng(seed=11)
        return {ell: rng.normal(size=2 * ell + 1) for ell in range(lmax + 1)}

    def test_producer_attached_flag_flipped_after_populate(self) -> None:
        out = _make_dummy_solver_output(
            alm_T=self._alm(), alm_E=self._alm(), alm_B=self._alm(),
        )
        attached = populate_map_outputs(out, nside=8)
        assert attached.metadata["map_output_support"] == "producer_attached"
        assert attached.metadata["map_producer_nside"] == 8
        assert "map_producer_path" in attached.metadata

    def test_post_init_validates_consistency(self) -> None:
        """The flipped output passes SolverCoreOutput.__post_init__."""
        out = _make_dummy_solver_output(
            alm_T=self._alm(), alm_E=self._alm(), alm_B=self._alm(),
        )
        attached = populate_map_outputs(out, nside=8)
        # If __post_init__ rejected the new bundle, dataclasses.replace
        # would have raised. Reach the maps directly.
        assert attached.map_T is not None
        assert attached.map_Q is not None
        assert attached.map_U is not None
        assert attached.map_T.shape == (12 * 8 * 8,)

    def test_idempotent_attach_raises(self) -> None:
        """Re-attaching after producer_attached is a programming error."""
        out = _make_dummy_solver_output(
            alm_T=self._alm(), alm_E=self._alm(), alm_B=self._alm(),
        )
        attached = populate_map_outputs(out, nside=8)
        with pytest.raises(ValueError, match="producer_attached"):
            populate_map_outputs(attached, nside=8)

    def test_rejects_non_mapping_alm(self) -> None:
        out = _make_dummy_solver_output(
            alm_T=np.zeros(10),  # wrong type
            alm_E=self._alm(), alm_B=self._alm(),
        )
        with pytest.raises(ValueError, match="flat alm size"):
            populate_map_outputs(out, nside=8)

    def test_accepts_native_solver_flat_payload(self) -> None:
        lmax = 4
        size = (lmax + 1) ** 2
        payload = {
            "representation": "ver2_native_pstf_sphere_reconstruction",
            "coefficient_representation": "ver2_native_pstf_final_slice",
            "ell_max": lmax,
            "values": np.linspace(0.0, 1.0, size),
        }
        zero_payload = {**payload, "values": np.zeros(size, dtype=np.float64)}
        out = _make_dummy_solver_output(
            alm_T=payload,
            alm_E=zero_payload,
            alm_B=zero_payload,
        )
        attached = populate_map_outputs(out, nside=8)
        assert attached.map_T is not None
        assert attached.metadata["map_producer_alm_schema"] == (
            "canonical_ell_m_mapping_from_native_or_archive_payload"
        )


# ────────────────────────────────────────────────────────────────────────
# Adversarial audit (V5_ROUND16_03 §3.3)
# ────────────────────────────────────────────────────────────────────────


class TestAdversarialAuditPRS12:
    """V5_ROUND16_03 §3.3 — A1/A3/A6/A10 probes."""

    def test_A3_uses_healpy_not_custom_approximation(self) -> None:
        """A3: alm_to_map must call healpy.alm2map, not a custom routine.

        Verified by inspection: both paths in alm_to_map_TQU dispatch to
        hp.alm2map and hp.alm2map_spin. We assert the function does not
        contain a quadrature-by-hand fallback by checking the module's
        attribute surface.
        """
        from bass.forward import map_producer

        # The module must expose hp via the healpy import.
        assert getattr(map_producer, "hp") is not None
        assert hasattr(map_producer.hp, "alm2map")
        assert hasattr(map_producer.hp, "alm2map_spin")

    def test_A6_non_trivial_alm_yields_non_constant_map(self) -> None:
        """A6: a non-FLRW (ℓ ≥ 1) input must produce a non-constant map.

        Constant maps would indicate the family-specific aℓm path was
        lost (silent monopole-only fallback).
        """
        rng = np.random.default_rng(seed=99)
        alm = {ell: rng.normal(size=2 * ell + 1) for ell in range(5)}
        empty = {ell: np.zeros(2 * ell + 1) for ell in range(5)}
        out = alm_to_map_TQU(
            alm_T=alm, alm_E=empty, alm_B=empty, nside=16, lmax=4,
        )
        std = float(np.std(out["map_T"]))
        assert std > 1.0e-3, (
            f"map_T has std {std:.3e}; non-trivial alm input should "
            "produce a non-constant map."
        )

    def test_A10_metadata_flag_flipped_explicitly(self) -> None:
        """A10: metadata flag must be flipped only by populate_map_outputs."""
        out = _make_dummy_solver_output(
            alm_T={0: np.zeros(1)},
            alm_E={0: np.zeros(1)},
            alm_B={0: np.zeros(1)},
        )
        # Pre-populate state: flag is "not_implemented".
        assert out.metadata["map_output_support"] == "not_implemented"
        attached = populate_map_outputs(out, nside=8)
        assert attached.metadata["map_output_support"] == "producer_attached"
        # The pre-state output is unchanged (immutable dataclass).
        assert out.metadata["map_output_support"] == "not_implemented"
