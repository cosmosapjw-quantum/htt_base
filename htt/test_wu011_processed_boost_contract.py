"""RED-first contracts for PMG-WU-011 processed local-boost response.

This commit deliberately contains no production implementation.  The tests
must fail because ``obsstat.processed_boost_response`` does not exist yet.
The failure records the TDD boundary before any processed-response code is
introduced.
"""

from __future__ import annotations

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


def _api():
    try:
        from obsstat import processed_boost_response as api
    except ImportError as exc:
        pytest.fail(f"WU-011 API missing: {exc}", pytrace=False)
    return api


def test_wu011_authority_and_processing_order_are_frozen() -> None:
    """The implementation must bind the reviewed predecessor and real call order."""

    api = _api()
    assert api.WU010_CLOSEOUT_HEAD == EXPECTED_WU010_CLOSEOUT_HEAD
    assert api.JOINT_ESTIMATOR_ID == EXPECTED_JOINT_ESTIMATOR_ID
    assert api.PROCESSING_ORDER == EXPECTED_PROCESSING_ORDER
    assert api.SOURCE_LMAX == 6
    assert api.FIT_LMAX == 5
    assert api.RETAINED_LMIN == 2


def test_wu011_scientific_and_joint_real_bases_roundtrip_exactly() -> None:
    """The scientific stored-real and internal sqrt(2) bases cannot drift."""

    api = _api()
    rng = np.random.default_rng(20260902)
    scientific = rng.normal(size=49)
    internal = api.scientific_to_joint_real(scientific, lmin=0, lmax=6)
    replayed = api.joint_to_scientific_real(internal, lmin=0, lmax=6)
    np.testing.assert_array_equal(replayed, scientific)


def test_wu011_basis_adapter_refuses_wrong_or_nonfinite_shape() -> None:
    """No short, long, or nonfinite carrier may be silently projected."""

    api = _api()
    for invalid in (np.zeros(48), np.zeros(50), np.full(49, np.nan), 1.0):
        with pytest.raises((TypeError, ValueError), match="stored-real|finite|shape"):
            api.scientific_to_joint_real(invalid, lmin=0, lmax=6)
