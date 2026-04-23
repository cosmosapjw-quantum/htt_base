"""Unit tests for ``bass.statistics``.

Covers:

* χ² / log-Gaussian bit-identity vs the inlined forms that previously
  lived in ``cosmological_frame._harmonic_log_prob`` /
  ``_spectral_log_prob``.
* ``ResidualPack`` dataclass semantics (pass/fail, tolerance violations,
  required-residual tracking, dict-shape round-trip).
* ``CovariancePack`` dict round-trip.
* ``merge_residual_packs`` namespacing.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.statistics import (
    CovariancePack,
    ResidualPack,
    build_covariance_pack,
    build_residual_pack,
    chi_squared,
    chi_squared_by_mode,
    log_gaussian,
    merge_residual_packs,
)


# =============================================================================
# χ² bit-identity
# =============================================================================

def test_chi_squared_matches_inline_quadratic():
    rng = np.random.default_rng(20260424)
    n = 7
    residual = rng.normal(size=n)
    a = rng.normal(size=(n, n))
    cov_inv = a @ a.T + np.eye(n)
    expected = float(residual @ cov_inv @ residual)
    assert chi_squared(residual, cov_inv) == expected


def test_chi_squared_by_mode_matches_inline_sum():
    rng = np.random.default_rng(1)
    residual = rng.normal(size=12)
    sigma = 0.5 + rng.uniform(size=12)
    expected = float(np.sum((residual / sigma) ** 2))
    assert chi_squared_by_mode(residual, sigma) == expected


def test_log_gaussian_is_minus_half_chi_squared():
    residual = np.array([1.0, -2.0, 3.0])
    cov_inv = np.diag([1.0, 0.5, 2.0])
    q = chi_squared(residual, cov_inv)
    assert log_gaussian(residual, cov_inv) == -0.5 * q


def test_log_gaussian_with_log_det_cov_adds_minus_half_ln_det():
    residual = np.array([1.0, -2.0, 3.0])
    cov_inv = np.diag([1.0, 0.5, 2.0])
    q = chi_squared(residual, cov_inv)
    log_det = 1.234
    expected = -0.5 * q - 0.5 * log_det
    assert log_gaussian(residual, cov_inv, log_det_cov=log_det) == expected


# =============================================================================
# ResidualPack
# =============================================================================

def test_residual_pack_passed_when_within_tolerance():
    pack = build_residual_pack(
        family="FLRW",
        branch="base",
        backend="flrw_scalar_validation",
        residual_values={"isotropic_anchor_limit": 1.0e-13, "seed_regularity": 1.0e-14},
        tolerance={"isotropic_anchor_limit": 1.0e-12, "seed_regularity": 1.0e-12},
        required_residuals=("isotropic_anchor_limit", "seed_regularity"),
    )
    assert pack.passed is True
    assert pack.recomputed_passed() is True
    assert pack.missing_residuals == ()
    assert pack.violated_tolerances == ()


def test_residual_pack_fails_on_tolerance_violation():
    pack = build_residual_pack(
        family="III",
        branch="class_b_special",
        backend="class_b_hyperbolic_template",
        residual_values={"hyperbolic_cutoff": 5.0e-3},
        tolerance={"hyperbolic_cutoff": 1.0e-3},
        required_residuals=("hyperbolic_cutoff",),
    )
    assert pack.passed is False
    assert pack.violated_tolerances == ("hyperbolic_cutoff",)


def test_residual_pack_fails_on_missing_required():
    pack = build_residual_pack(
        family="II",
        branch="base",
        backend="nil_intrinsic_template",
        residual_values={"nil_chart_regularity": 0.0},
        tolerance={"nil_chart_regularity": 1.0e-6},
        required_residuals=("nil_chart_regularity", "label_translator_roundtrip"),
    )
    assert pack.passed is False
    assert pack.missing_residuals == ("label_translator_roundtrip",)


def test_residual_pack_fails_on_forbidden_shortcut_violation():
    pack = build_residual_pack(
        family="IV",
        branch="base",
        backend="solvable_group_template",
        residual_values={"chart_order": 0.0, "edge_anisotropy": 0.0, "seed_regularity": 0.0},
        tolerance={"chart_order": 1.0, "edge_anisotropy": 1.0, "seed_regularity": 1.0},
        required_residuals=("chart_order", "edge_anisotropy", "seed_regularity"),
        forbidden_shortcuts=("no_chart_swap_without_translator_update",),
        forbidden_shortcut_violations=("no_chart_swap_without_translator_update",),
    )
    assert pack.passed is False


def test_residual_pack_nonfinite_value_is_violation():
    pack = build_residual_pack(
        family="I",
        branch="base",
        backend="bianchi_i_matrix_exact",
        residual_values={"cartesian_anchor_limit": math.inf},
        tolerance={"cartesian_anchor_limit": 1.0},
        required_residuals=("cartesian_anchor_limit",),
    )
    assert pack.passed is False
    assert pack.violated_tolerances == ("cartesian_anchor_limit",)


def test_residual_pack_as_payload_roundtrip():
    pack = build_residual_pack(
        family="IX",
        branch="base",
        backend="class_a_compact_matrix_approx",
        residual_values={"compact_anchor_limit": 1.0e-8},
        tolerance={"compact_anchor_limit": 1.0e-6},
        required_residuals=("compact_anchor_limit",),
        metadata={"verification_reference": "docs/…/crosscheck_results.json"},
        verification_crosscheck_pass=True,
    )
    payload = pack.as_payload()
    assert payload["family"] == "IX"
    assert payload["residual_values"]["compact_anchor_limit"] == 1.0e-8
    assert payload["passed"] is True
    assert payload["verification_crosscheck_pass"] is True
    assert payload["missing_residuals"] == []
    assert payload["violated_tolerances"] == []


def test_residual_pack_is_frozen():
    pack = build_residual_pack(
        family="I",
        branch="base",
        backend="bianchi_i_matrix_exact",
        residual_values={"cartesian_anchor_limit": 0.0},
        tolerance={"cartesian_anchor_limit": 1.0},
        required_residuals=("cartesian_anchor_limit",),
    )
    with pytest.raises(Exception):  # FrozenInstanceError subclasses AttributeError
        pack.family = "II"  # type: ignore[misc]


# =============================================================================
# merge_residual_packs
# =============================================================================

def test_merge_residual_packs_namespaces_labels():
    a = build_residual_pack(
        family="I",
        branch="base",
        backend="bianchi_i_matrix_exact",
        residual_values={"cartesian_anchor_limit": 1.0e-14},
        tolerance={"cartesian_anchor_limit": 1.0e-12},
        required_residuals=("cartesian_anchor_limit",),
    )
    b = build_residual_pack(
        family="IX",
        branch="base",
        backend="class_a_compact_matrix_approx",
        residual_values={"compact_anchor_limit": 1.0e-8},
        tolerance={"compact_anchor_limit": 1.0e-6},
        required_residuals=("compact_anchor_limit",),
    )
    merged = merge_residual_packs([a, b])
    assert merged.passed is True
    assert "I:cartesian_anchor_limit" in merged.residual_values
    assert "IX:compact_anchor_limit" in merged.residual_values
    assert merged.family == "I+IX"


def test_merge_residual_packs_short_circuits_on_empty():
    with pytest.raises(ValueError):
        merge_residual_packs([])


# =============================================================================
# CovariancePack
# =============================================================================

def test_covariance_pack_roundtrip():
    support = ({"ell": 2, "m": 0, "mode_label": "m0", "flat_index": 4},)
    dense_blocks = {
        "TT": np.array([[1.0]]),
        "EE": np.array([[2.0]]),
        "TE": np.array([[0.1]]),
        "BB": np.array([[3.0]]),
    }
    payload = {
        "representation": "low_ell_harmonic_dense_gaussian",
        "harmonic_basis": "real_pstf_packed",
        "support": list(support),
        "subspace_size": 1,
        "dense_blocks": dense_blocks,
        "invalid_mode_residual": 0.0,
        "structure_label": "test",
        "preferred_axis": None,
        "anisotropy_tensor": None,
        "offdiag_strength": 0.0,
        "rotation_strength": 0.0,
    }
    pack = build_covariance_pack(payload, psd_guard={"psd_pass": True})
    assert isinstance(pack, CovariancePack)
    assert pack.subspace_size == 1
    round_trip = pack.as_payload()
    assert round_trip["dense_blocks"]["TT"][0, 0] == 1.0
    assert round_trip["psd_guard"] == {"psd_pass": True}


# =============================================================================
# Integration: CosmologicalFrameLikelihood still produces identical values
# =============================================================================

def test_cosmological_frame_likelihood_bit_identical_after_consolidation():
    """Regression guard — ensures the χ² refactor did not move log_prob.

    Exercises both paths:

    * harmonic Gaussian path (dense covariance inverse) via
      ``_harmonic_log_prob`` → ``chi_squared``
    * spectral path via ``_spectral_log_prob`` →
      ``chi_squared_by_mode``
    """
    from bass.likelihood.cosmological_frame import CosmologicalFrameLikelihood

    rng = np.random.default_rng(42)
    n_ell = 10
    ell = np.arange(n_ell, dtype=int)

    # Harmonic-Gaussian path: build a dense covariance and matching alm_reference.
    size = 4
    a = rng.normal(size=(size, size))
    tt = a @ a.T + np.eye(size)
    ee = a @ a.T + 2.0 * np.eye(size)
    bb = a @ a.T + 3.0 * np.eye(size)
    te = 0.1 * (a + a.T)
    htt_dec = {
        "resolved_axis": np.array([0.0, 0.0, 1.0]),
        "axis_precision": 4.0,
        "effective_amplitude": 0.0,
        "anisotropy_tensor": np.zeros((3, 3)),
        "spectra_reference": {
            "TT": np.zeros(n_ell),
            "EE": np.zeros(n_ell),
            "TE": np.zeros(n_ell),
            "BB": np.zeros(n_ell),
        },
        "directional_covariance": {"ell": ell},
        "alm_reference": {
            "T": np.zeros(size),
            "E": np.zeros(size),
            "B": np.zeros(size),
        },
        "harmonic_covariance": {"dense_blocks": {"TT": tt, "EE": ee, "TE": te, "BB": bb}},
    }
    lik = CosmologicalFrameLikelihood(htt_decomposition=htt_dec, tier="low_ell")
    assert lik.harmonic_gaussian_ready is True

    alm_T = rng.normal(size=size)
    alm_E = rng.normal(size=size)
    alm_B = rng.normal(size=size)
    logp = lik.log_prob({"alm_T": alm_T, "alm_E": alm_E, "alm_B": alm_B})

    # Reconstruct inline form for bit-identity check.
    joint = np.block(
        [
            [tt, te, np.zeros_like(tt)],
            [te.T, ee, np.zeros_like(tt)],
            [np.zeros_like(tt), np.zeros_like(tt), bb],
        ]
    )
    joint = 0.5 * (joint + joint.T)
    scale = max(
        float(np.max(np.abs(np.diag(tt)))),
        float(np.max(np.abs(np.diag(ee)))),
        float(np.max(np.abs(np.diag(bb)))),
        1.0e-12,
    )
    joint += 1.0e-9 * scale * np.eye(joint.shape[0])
    joint_inv = np.linalg.inv(joint)
    residual = np.concatenate([alm_T, alm_E, alm_B])
    expected = -0.5 * float(residual @ joint_inv @ residual)
    assert logp == expected


def test_cosmological_frame_spectral_path_bit_identical():
    from bass.likelihood.cosmological_frame import CosmologicalFrameLikelihood

    n_ell = 13
    ell = np.arange(n_ell, dtype=int)
    rng = np.random.default_rng(11)
    ref = {
        "TT": rng.uniform(1.0, 10.0, size=n_ell),
        "EE": rng.uniform(1.0, 10.0, size=n_ell),
        "TE": rng.uniform(0.1, 1.0, size=n_ell),
        "BB": rng.uniform(0.1, 1.0, size=n_ell),
    }
    htt_dec = {
        "resolved_axis": np.array([0.0, 0.0, 1.0]),
        "axis_precision": 4.0,
        "effective_amplitude": 0.5,
        "anisotropy_tensor": np.zeros((3, 3)),
        "spectra_reference": ref,
        "directional_covariance": {"ell": ell},
    }
    lik = CosmologicalFrameLikelihood(htt_decomposition=htt_dec, tier="low_ell")
    assert lik.harmonic_gaussian_ready is False

    model = {key: ref[key] * 1.05 for key in ref}
    params = {
        f"spectra_{key}": model[key] for key in ref
    }
    logp = lik.log_prob(params)

    # Inline replay of _spectral_log_prob + other terms.
    tier_max_ell = 12
    mask = (ell >= 2) & (ell <= tier_max_ell)
    noise_fraction = 0.08
    spectral = 0.0
    for key in ("TT", "EE", "TE", "BB"):
        ref_sel = ref[key][:n_ell][mask]
        model_sel = model[key][:n_ell][mask]
        sigma = noise_fraction * np.maximum(np.abs(ref_sel), 1.0e-6)
        residual = model_sel - ref_sel
        spectral += -0.5 * float(np.sum((residual / sigma) ** 2))
    # Non-spectral terms: axis/amplitude; at default axis+amplitude, match lik internals.
    axis = np.array([0.0, 0.0, 1.0])
    angular_term = 4.0 * float(np.clip(np.dot(axis, axis), -1.0, 1.0))
    quadratic_term = float(axis @ np.zeros((3, 3)) @ axis)
    amp_sigma = max(0.05, 0.35 * max(0.5, 0.05))
    amplitude_term = -0.5 * ((0.5 - 0.5) / amp_sigma) ** 2
    expected = float(angular_term + quadratic_term + amplitude_term + spectral)
    assert logp == expected
