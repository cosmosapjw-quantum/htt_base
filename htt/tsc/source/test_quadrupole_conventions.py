from __future__ import annotations

import pytest

from tsc.source.quadrupole_conventions import (
    from_legendre_q,
    linear_intensity_quadrupole_from_parameter,
    quadrupole_convention_metadata,
    to_legendre_q,
)


def test_mu2_minus_one_third_metadata_matches_re2_plan():
    metadata = quadrupole_convention_metadata("mu2_minus_one_third")

    assert metadata.quadrupole_parameter_name == "Q_mu"
    assert metadata.conversion_to_legendre_q == pytest.approx(2.0 / 3.0)


def test_legendre_p2_metadata_is_identity_conversion():
    metadata = quadrupole_convention_metadata("legendre_P2")

    assert metadata.quadrupole_parameter_name == "q"
    assert metadata.conversion_to_legendre_q == pytest.approx(1.0)


def test_q_mu_to_legendre_q_conversion_and_inverse_roundtrip():
    q_mu = 0.15
    q = to_legendre_q(q_mu, "mu2_minus_one_third")

    assert q == pytest.approx(0.10)
    assert from_legendre_q(q, "mu2_minus_one_third") == pytest.approx(q_mu)


def test_linear_intensity_quadrupole_matches_both_conventions():
    q_mu = 0.15
    q = 0.10

    assert linear_intensity_quadrupole_from_parameter(
        q_mu,
        "mu2_minus_one_third",
    ) == pytest.approx(0.400)
    assert linear_intensity_quadrupole_from_parameter(
        q,
        "legendre_P2",
    ) == pytest.approx(0.400)
