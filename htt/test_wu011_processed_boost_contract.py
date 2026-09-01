"""Test-first contracts for PMG-WU-011 processed local-boost response.

The authority/basis slice was observed RED at commit ``902e6959`` and GREEN
at ``69933d07``.  The positive-sky tests below define the next RED boundary
without requiring the optional ``healpy`` dependency.
"""

from __future__ import annotations

import math

import numpy as np
import pytest


pytestmark = pytest.mark.fast


EXPECTED_WU010_CLOSEOUT_HEAD = "29427a1f7f2c5d46e43ffe03053c4ac13e969228"
EXPECTED_JOINT_ESTIMATOR_ID = (
    "joint_weighted_real_harmonic_l0_l5_retain_l2_l5:v1"
)
EXPECTED_PROCESSING_ORDER = (
    "FINITE_OR_LINEAR_BOOST",
    "SOURCE_BEAM_PIXEL_TRANSFER",
    "HEALPIX_SYNTHESIS",
    "WEIGHTED_JOINT_L0_L5_SOLVE",
    "POSTFIT_TARGET_SOURCE_COMMONIZATION",
    "RETAIN_L2_L5",
)
EXPECTED_TERMINALS = {
    "PASS_SYNTHETIC_PROCESSED_RESPONSE",
    "BLOCKED_BY_MOVED_AUTHORITY",
    "BLOCKED_BY_BASIS_MISMATCH",
    "BLOCKED_BY_MISSING_ABSOLUTE_T",
    "BLOCKED_BY_OPERATOR_IDENTITY_MISMATCH",
    "BLOCKED_BY_REPLAY_MISMATCH",
    "BLOCKED_BY_LINEARIZATION_FAILURE",
    "BLOCKED_BY_SIGN_MUTATION_SURVIVAL",
    "BLOCKED_BY_RANK_DEFICIENCY",
    "BLOCKED_BY_CONDITION_CEILING",
    "BLOCKED_BY_TRANSFER_UNRESOLVED",
    "BLOCKED_BY_NUISANCE_DEFINITION",
    "BLOCKED_BY_ALIAS_UNCONTROLLED",
    "BLOCKED_BY_HISTORICAL_PARITY_FAILURE",
    "BLOCKED_BY_NULL_EXCHANGEABILITY_FAILURE",
    "NO_ADMISSIBLE_NEW_RESULT",
}


def _api():
    try:
        from obsstat import processed_boost_response as api
    except ImportError as exc:
        pytest.fail(f"WU-011 API missing: {exc}", pytrace=False)
    return api


def _unit_rows(seed: int = 20260902, count: int = 64) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rows = rng.normal(size=(count, 3))
    return rows / np.linalg.norm(rows, axis=1, keepdims=True)


def test_wu011_authority_and_processing_order_are_frozen() -> None:
    """The implementation must bind the reviewed predecessor and real call order."""

    api = _api()
    assert api.WU010_CLOSEOUT_HEAD == EXPECTED_WU010_CLOSEOUT_HEAD
    assert api.JOINT_ESTIMATOR_ID == EXPECTED_JOINT_ESTIMATOR_ID
    assert api.PROCESSING_ORDER == EXPECTED_PROCESSING_ORDER
    assert api.SOURCE_LMAX == 6
    assert api.FIT_LMAX == 5
    assert api.RETAINED_LMIN == 2


def test_wu011_terminal_registry_is_explicit_and_complete() -> None:
    """Every planned fail-closed state is typed before output code exists."""

    api = _api()
    assert {item.value for item in api.ProcessedBoostTerminal} == EXPECTED_TERMINALS


def test_wu011_scientific_and_joint_real_bases_roundtrip_at_roundoff() -> None:
    """The irrational sqrt(2) adapter is invertible to declared roundoff."""

    api = _api()
    rng = np.random.default_rng(20260902)
    scientific = rng.normal(size=49)
    internal = api.scientific_to_joint_real(scientific, lmin=0, lmax=6)
    replayed = api.joint_to_scientific_real(internal, lmin=0, lmax=6)
    np.testing.assert_allclose(replayed, scientific, rtol=0.0, atol=5.0e-16)


def test_wu011_basis_adapter_refuses_wrong_or_nonfinite_shape() -> None:
    """No short, long, or nonfinite carrier may be silently projected."""

    api = _api()
    for invalid in (np.zeros(48), np.zeros(50), np.full(49, np.nan), 1.0):
        with pytest.raises((TypeError, ValueError), match="stored-real|finite|shape"):
            api.scientific_to_joint_real(invalid, lmin=0, lmax=6)
        with pytest.raises((TypeError, ValueError), match="joint-real|finite|shape"):
            api.joint_to_scientific_real(invalid, lmin=0, lmax=6)


def test_wu011_basis_adapter_refuses_invalid_band() -> None:
    api = _api()
    with pytest.raises(ValueError, match="band"):
        api.scientific_to_joint_real(np.zeros(1), lmin=2, lmax=1)


def test_wu011_positive_sky_uses_an_analytic_full_sphere_certificate() -> None:
    """The declared lower bound must follow the harmonic addition theorem."""

    api = _api()
    coefficients = np.zeros(48)
    coefficients[0] = 0.2  # ell=1, m=0
    spec = api.PositiveAbsoluteSkySpec(
        monopole_temperature=2.7255,
        scientific_coefficients=coefficients,
        source_lmax=6,
        units="K_CMB",
    )
    expected_bound = math.sqrt(3.0 / (4.0 * math.pi)) * 0.2
    assert spec.anisotropy_supremum_bound == pytest.approx(expected_bound)
    assert spec.certified_temperature_margin == pytest.approx(2.7255 - expected_bound)
    assert spec.certified_temperature_margin > 0.0


def test_wu011_positive_sky_is_positive_on_independent_directions() -> None:
    api = _api()
    rng = np.random.default_rng(811)
    coefficients = 0.01 * rng.normal(size=48)
    spec = api.PositiveAbsoluteSkySpec(
        monopole_temperature=2.7255,
        scientific_coefficients=coefficients,
        source_lmax=6,
        units="K_CMB",
    )
    values = spec.evaluate(_unit_rows())
    assert values.shape == (64,)
    assert float(np.min(values)) >= spec.certified_temperature_margin - 2.0e-14
    assert np.all(values > 0.0)


def test_wu011_positive_sky_refuses_an_uncertified_or_malformed_domain() -> None:
    api = _api()
    unsafe = np.zeros(48)
    unsafe[0] = 10.0
    with pytest.raises(api.ProcessedBoostError, match="strictly positive"):
        api.PositiveAbsoluteSkySpec(
            monopole_temperature=1.0,
            scientific_coefficients=unsafe,
            source_lmax=6,
            units="K_CMB",
        )
    for invalid in (
        dict(monopole_temperature=0.0, scientific_coefficients=np.zeros(48)),
        dict(monopole_temperature=np.nan, scientific_coefficients=np.zeros(48)),
        dict(monopole_temperature=2.7, scientific_coefficients=np.zeros(47)),
        dict(monopole_temperature=2.7, scientific_coefficients=np.full(48, np.nan)),
    ):
        with pytest.raises((TypeError, ValueError), match="positive|finite|shape"):
            api.PositiveAbsoluteSkySpec(
                source_lmax=6,
                units="K_CMB",
                **invalid,
            )


def test_wu011_positive_sky_content_is_immutable_and_identity_bound() -> None:
    api = _api()
    coefficients = np.zeros(48)
    first = api.PositiveAbsoluteSkySpec(2.7255, coefficients, 6, "K_CMB")
    second = api.PositiveAbsoluteSkySpec(2.7255, coefficients.copy(), 6, "K_CMB")
    assert first.content_id == second.content_id
    with pytest.raises(ValueError):
        first.scientific_coefficients[0] = 1.0
