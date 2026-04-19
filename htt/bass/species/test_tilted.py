"""Tests for bass/species/tilted.py (FB-3.1).

Covers the non-negotiable invariants of the Phase FB-3 entry rotation:

- T-01..T-05 : β=0 bit-identical recovery across all four matter species
  + Λ (the full LB-1 canonical registry); ``v̂_e`` is swept across three
  directions to prove the β=0 short-circuit is truly v̂-independent.
- T-06 : β > 0 gives finite ``ρ̃ > ρ`` and ``γ > 1``.
- T-07 : β > 0 exact agreement with EMM §5.4 eqs (5.12)-(5.13).
- T-08 : β = 0 path returns zero 3-velocity (shape guard: scalar & array).
- T-09 : β ≥ 1 raises ``ValueError`` (superluminal guard).
- T-10 : β < 0 / non-finite raises ``ValueError``.
- T-11 : ``|v̂_e| ≠ 1`` raises ``ValueError``.
- T-12 : wrong-length ``v̂_e`` raises ``ValueError``.
- T-13 : FB02-F1 — ``V_HAT_E_DEFAULT`` matches ``BianchiCosmology``
  default (convention cross-reference).
- T-14 : ``gamma`` / ``gamma_sq`` identities on the orthogonal and
  mildly-tilted branches.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.einstein_bianchi import BianchiCosmology
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import (
    TiltedSpeciesBackground,
    V_HAT_E_DEFAULT,
    V_HAT_NORM_TOL,
)


# ──────────────────────────────────────────────────────────────────────
# Fixtures — one of each species from the canonical LB-1 registry.
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def registry() -> SpeciesBackgroundRegistry:
    return SpeciesBackgroundRegistry.from_planck2018()


@pytest.fixture(scope="module")
def eta_samples(registry: SpeciesBackgroundRegistry) -> np.ndarray:
    bg = registry.bg_table
    # Skip eta=0 (some species require in-range eta).
    return np.linspace(bg.eta_min, bg.eta_today, 25)[1:]


# ──────────────────────────────────────────────────────────────────────
# T-01..T-05 : β=0 bit-identical recovery per species, v̂_e swept.
#
# Three directions are probed on each species to prove that the
# short-circuit discards v̂_e entirely (as specified in 00_conventions
# §2 FB02-F1: v̂_e is irrelevant on the orthogonal path).
# ──────────────────────────────────────────────────────────────────────

_V_HAT_SWEEP = (
    (1.0, 0.0, 0.0),   # canonical default (FB02-F1 SSOT)
    (0.0, 1.0, 0.0),   # e_2 axis
    (0.0, 0.0, 1.0),   # e_3 axis
)


def _assert_bit_identical(tilted: TiltedSpeciesBackground,
                          base,
                          eta: np.ndarray) -> None:
    """Assert ρ̃ / p̃ match the base byte-for-byte on the β=0 path."""
    rho_tilde = np.asarray(tilted.rho_tilde(eta))
    p_tilde = np.asarray(tilted.p_tilde(eta))
    rho_base = np.asarray(base.rho_rest(eta))
    p_base = np.asarray(base.p_rest(eta))
    # np.array_equal compares element-wise with ``==``; NaN intolerant.
    # These arrays are analytic closed-forms (no NaN), so this is the
    # strongest possible equality check.
    assert np.array_equal(rho_tilde, rho_base), (
        f"ρ̃(β=0) must be bit-identical to base.rho_rest; "
        f"max |Δ| = {np.max(np.abs(rho_tilde - rho_base))!r}"
    )
    assert np.array_equal(p_tilde, p_base), (
        f"p̃(β=0) must be bit-identical to base.p_rest; "
        f"max |Δ| = {np.max(np.abs(p_tilde - p_base))!r}"
    )


@pytest.mark.parametrize("v_hat", _V_HAT_SWEEP)
def test_T01_photon_beta_zero_bit_identical(registry, eta_samples, v_hat):
    photon = registry[SpeciesLabel.PHOTON]
    tilted = TiltedSpeciesBackground(base=photon, beta=0.0, v_hat_e=v_hat)
    _assert_bit_identical(tilted, photon, eta_samples)


@pytest.mark.parametrize("v_hat", _V_HAT_SWEEP)
def test_T02_neutrino_beta_zero_bit_identical(registry, eta_samples, v_hat):
    neutrino = registry[SpeciesLabel.NEUTRINO]
    tilted = TiltedSpeciesBackground(base=neutrino, beta=0.0, v_hat_e=v_hat)
    _assert_bit_identical(tilted, neutrino, eta_samples)


@pytest.mark.parametrize("v_hat", _V_HAT_SWEEP)
def test_T03_baryon_beta_zero_bit_identical(registry, eta_samples, v_hat):
    baryon = registry[SpeciesLabel.BARYON]
    tilted = TiltedSpeciesBackground(base=baryon, beta=0.0, v_hat_e=v_hat)
    _assert_bit_identical(tilted, baryon, eta_samples)


@pytest.mark.parametrize("v_hat", _V_HAT_SWEEP)
def test_T04_cdm_beta_zero_bit_identical(registry, eta_samples, v_hat):
    cdm = registry[SpeciesLabel.CDM]
    tilted = TiltedSpeciesBackground(base=cdm, beta=0.0, v_hat_e=v_hat)
    _assert_bit_identical(tilted, cdm, eta_samples)


@pytest.mark.parametrize("v_hat", _V_HAT_SWEEP)
def test_T05_lambda_beta_zero_bit_identical(registry, eta_samples, v_hat):
    lambda_ = registry[SpeciesLabel.LAMBDA]
    tilted = TiltedSpeciesBackground(base=lambda_, beta=0.0, v_hat_e=v_hat)
    _assert_bit_identical(tilted, lambda_, eta_samples)


# ──────────────────────────────────────────────────────────────────────
# T-06 : β > 0 — finite, ρ̃ > ρ, γ > 1.
# ──────────────────────────────────────────────────────────────────────


def test_T06_beta_positive_finite_and_enhanced(registry, eta_samples):
    """β > 0: ρ̃ > ρ on the radiation species (ρ+p > 0, so γ² uplift bites)."""
    photon = registry[SpeciesLabel.PHOTON]
    tilted = TiltedSpeciesBackground(
        base=photon, beta=0.3, v_hat_e=V_HAT_E_DEFAULT,
    )
    rho_tilde = np.asarray(tilted.rho_tilde(eta_samples))
    rho_rest = np.asarray(photon.rho_rest(eta_samples))
    assert np.all(np.isfinite(rho_tilde))
    # γ² = 1/(1-0.09) ≈ 1.0989 > 1, and ρ+p = 4ρ/3 > 0, so ρ̃ > ρ strictly.
    assert np.all(rho_tilde > rho_rest)
    assert tilted.gamma > 1.0
    assert tilted.gamma_sq == pytest.approx(1.0 / (1.0 - 0.3 * 0.3), rel=1e-15)


# ──────────────────────────────────────────────────────────────────────
# T-07 : β > 0 — closed-form EMM §5.4 match.
# ──────────────────────────────────────────────────────────────────────


def test_T07_beta_positive_emm_5_12_5_13(registry, eta_samples):
    """Exact EMM eqs (5.12)-(5.13) — no small-β linearisation."""
    cdm = registry[SpeciesLabel.CDM]
    beta = 0.5
    tilted = TiltedSpeciesBackground(base=cdm, beta=beta, v_hat_e=V_HAT_E_DEFAULT)
    rho = np.asarray(cdm.rho_rest(eta_samples))
    p = np.asarray(cdm.p_rest(eta_samples))  # = 0 for CDM
    gamma_sq = 1.0 / (1.0 - beta * beta)
    expected_rho = gamma_sq * (rho + p) - p
    expected_p = p + (1.0 / 3.0) * gamma_sq * (rho + p) * beta * beta
    np.testing.assert_allclose(tilted.rho_tilde(eta_samples), expected_rho,
                                rtol=0.0, atol=0.0)
    np.testing.assert_allclose(tilted.p_tilde(eta_samples), expected_p,
                                rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# T-08 : v_vector shape + β=0 zero recovery.
# ──────────────────────────────────────────────────────────────────────


def test_T08_v_vector_shape_and_beta_zero(registry, eta_samples):
    photon = registry[SpeciesLabel.PHOTON]

    # β = 0 → zero velocity regardless of v̂_e.
    t0 = TiltedSpeciesBackground(base=photon, beta=0.0, v_hat_e=(0.6, 0.8, 0.0))
    v_scalar = t0.v_vector(float(eta_samples[0]))
    assert v_scalar.shape == (3,)
    np.testing.assert_array_equal(v_scalar, np.zeros(3))
    v_array = t0.v_vector(eta_samples)
    assert v_array.shape == (eta_samples.size, 3)
    np.testing.assert_array_equal(v_array, np.zeros_like(v_array))

    # β > 0 → v^a = β v̂_e broadcast.
    beta = 0.2
    v_hat = (0.0, 0.0, 1.0)
    t1 = TiltedSpeciesBackground(base=photon, beta=beta, v_hat_e=v_hat)
    v_scalar_t1 = t1.v_vector(float(eta_samples[0]))
    np.testing.assert_allclose(v_scalar_t1, (0.0, 0.0, beta), rtol=0, atol=0)
    v_array_t1 = t1.v_vector(eta_samples)
    assert v_array_t1.shape == (eta_samples.size, 3)
    for row in v_array_t1:
        np.testing.assert_allclose(row, (0.0, 0.0, beta), rtol=0, atol=0)


# ──────────────────────────────────────────────────────────────────────
# T-09..T-12 : Validation guards.
# ──────────────────────────────────────────────────────────────────────


def test_T09_superluminal_beta_raises(registry):
    photon = registry[SpeciesLabel.PHOTON]
    with pytest.raises(ValueError, match=r"superluminal"):
        TiltedSpeciesBackground(base=photon, beta=1.0)
    with pytest.raises(ValueError, match=r"superluminal"):
        TiltedSpeciesBackground(base=photon, beta=1.2)


def test_T10_negative_or_nonfinite_beta_raises(registry):
    photon = registry[SpeciesLabel.PHOTON]
    with pytest.raises(ValueError, match=r"non-negative"):
        TiltedSpeciesBackground(base=photon, beta=-0.1)
    with pytest.raises(ValueError, match=r"finite"):
        TiltedSpeciesBackground(base=photon, beta=float("nan"))
    with pytest.raises(ValueError, match=r"finite"):
        TiltedSpeciesBackground(base=photon, beta=float("inf"))


def test_T11_non_unit_v_hat_raises(registry):
    photon = registry[SpeciesLabel.PHOTON]
    # |v̂| = 2 — clearly off.
    with pytest.raises(ValueError, match=r"unit vector"):
        TiltedSpeciesBackground(base=photon, v_hat_e=(2.0, 0.0, 0.0))
    # |v̂|² = 2 (within float, nowhere near tolerance).
    with pytest.raises(ValueError, match=r"unit vector"):
        TiltedSpeciesBackground(
            base=photon, v_hat_e=(1.0, 1.0, 0.0),
        )
    # |v̂|² = 1 + 10·tol: should still trip.
    bad = (np.sqrt(1.0 + 10.0 * V_HAT_NORM_TOL), 0.0, 0.0)
    with pytest.raises(ValueError, match=r"unit vector"):
        TiltedSpeciesBackground(base=photon, v_hat_e=bad)


def test_T12_wrong_length_v_hat_raises(registry):
    photon = registry[SpeciesLabel.PHOTON]
    with pytest.raises(ValueError, match=r"three components"):
        TiltedSpeciesBackground(base=photon, v_hat_e=(1.0, 0.0))
    with pytest.raises(ValueError, match=r"three components"):
        TiltedSpeciesBackground(
            base=photon, v_hat_e=(1.0, 0.0, 0.0, 0.0),
        )


# ──────────────────────────────────────────────────────────────────────
# T-13 : FB02-F1 — convention default cross-reference.
# ──────────────────────────────────────────────────────────────────────


def test_T13_v_hat_default_matches_bianchi_cosmology_fb02_f1():
    """FB02-F1 cross-reference: ``V_HAT_E_DEFAULT`` == ``BianchiCosmology.v_hat_e`` default.

    This is the test that prevents the ``v̂_e`` default from drifting
    between the tilt wrapper and the cosmology carrier, which would
    split ``00_conventions §2`` into two silently-different SSOTs.
    """
    cosmo = BianchiCosmology()
    assert cosmo.v_hat_e == V_HAT_E_DEFAULT
    # And the wrapper's own default must also match the SSOT.
    from dataclasses import fields
    tilted_default = next(
        f.default for f in fields(TiltedSpeciesBackground) if f.name == "v_hat_e"
    )
    assert tilted_default == V_HAT_E_DEFAULT


# ──────────────────────────────────────────────────────────────────────
# T-14 : γ / γ² identity spot-checks.
# ──────────────────────────────────────────────────────────────────────


def test_T14_gamma_identities(registry):
    photon = registry[SpeciesLabel.PHOTON]
    t0 = TiltedSpeciesBackground(base=photon, beta=0.0)
    assert t0.gamma == 1.0
    assert t0.gamma_sq == 1.0
    assert t0.v_magnitude == 0.0

    for beta in (1e-6, 0.01, 0.1, 0.3, 0.7, 0.95):
        t = TiltedSpeciesBackground(base=photon, beta=beta)
        expected = 1.0 / np.sqrt(1.0 - beta * beta)
        assert t.gamma == pytest.approx(expected, rel=1e-15)
        assert t.gamma_sq == pytest.approx(expected * expected, rel=1e-15)
        assert t.v_magnitude == beta
