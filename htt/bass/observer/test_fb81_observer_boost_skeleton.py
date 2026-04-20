from __future__ import annotations

from dataclasses import is_dataclass

import numpy as np
import pytest

from bass.observer import ObserverBoost
from bass.species.tilted import V_HAT_E_DEFAULT


def test_fb81_observer_boost_is_a_dataclass() -> None:
    assert is_dataclass(ObserverBoost)


def test_fb81_observer_boost_docstring_keeps_type_distinct_pin() -> None:
    doc = ObserverBoost.__doc__ or ""
    assert "must\n    not subclass" in doc or "must not subclass" in doc


@pytest.mark.parametrize(
    "rapidity",
    [0.0, 1.0e-8, 1.0e-5, 1.0e-3, 0.05, 0.1, 0.5, 1.0],
)
def test_fb81_velocity_matches_tanh(rapidity: float) -> None:
    boost = ObserverBoost(rapidity=rapidity)
    assert boost.velocity == pytest.approx(float(np.tanh(rapidity)), rel=1.0e-15)


@pytest.mark.parametrize(
    "rapidity",
    [0.0, 1.0e-8, 1.0e-5, 1.0e-3, 0.05, 0.1, 0.5, 1.0],
)
def test_fb81_gamma_matches_cosh(rapidity: float) -> None:
    boost = ObserverBoost(rapidity=rapidity)
    assert boost.gamma == pytest.approx(float(np.cosh(rapidity)), rel=1.0e-15)


@pytest.mark.parametrize(
    "rapidity",
    [0.0, 1.0e-8, 1.0e-5, 1.0e-3, 0.05, 0.1, 0.5, 1.0],
)
def test_fb81_gamma_sq_matches_gamma_squared(rapidity: float) -> None:
    boost = ObserverBoost(rapidity=rapidity)
    assert boost.gamma_sq == pytest.approx(boost.gamma * boost.gamma, rel=1.0e-15)


def test_fb81_zero_rapidity_is_exact_zero_speed() -> None:
    boost = ObserverBoost(rapidity=0.0)
    assert boost.velocity == 0.0
    assert boost.gamma == 1.0
    assert boost.gamma_sq == 1.0


def test_fb81_default_direction_matches_shared_ssot() -> None:
    boost = ObserverBoost(rapidity=0.0)
    assert boost.v_hat == V_HAT_E_DEFAULT


@pytest.mark.parametrize("bad_rapidity", [np.nan, np.inf, -np.inf, -1.0e-12, -0.5])
def test_fb81_rejects_nonfinite_or_negative_rapidity(bad_rapidity: float) -> None:
    with pytest.raises(ValueError):
        ObserverBoost(rapidity=float(bad_rapidity))


@pytest.mark.parametrize(
    "bad_v_hat",
    [
        (),
        (1.0,),
        (1.0, 0.0),
        (1.0, 0.0, 0.0, 0.0),
    ],
)
def test_fb81_rejects_wrong_length_direction(bad_v_hat: tuple[float, ...]) -> None:
    with pytest.raises(ValueError):
        ObserverBoost(rapidity=1.0e-3, v_hat=bad_v_hat)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_v_hat",
    [
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (0.5, 0.5, 0.5),
        (1.0, 1.0e-4, 0.0),
        (1.0, 0.0, 1.0e-4),
        (0.7, 0.7, 0.0),
    ],
)
def test_fb81_rejects_non_unit_direction(bad_v_hat: tuple[float, float, float]) -> None:
    with pytest.raises(ValueError):
        ObserverBoost(rapidity=1.0e-3, v_hat=bad_v_hat)


@pytest.mark.parametrize(
    "v_hat",
    [
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (-1.0, 0.0, 0.0),
        (1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0),
    ],
)
def test_fb81_accepts_valid_unit_directions(v_hat: tuple[float, float, float]) -> None:
    boost = ObserverBoost(rapidity=1.0e-3, v_hat=v_hat)
    assert np.linalg.norm(boost.v_hat) == pytest.approx(1.0, rel=1.0e-12)


def test_fb81_instances_compare_by_value() -> None:
    lhs = ObserverBoost(rapidity=1.0e-3, v_hat=(1.0, 0.0, 0.0))
    rhs = ObserverBoost(rapidity=1.0e-3, v_hat=(1.0, 0.0, 0.0))
    assert lhs == rhs


def test_fb81_velocity_is_strictly_sub_luminal() -> None:
    boost = ObserverBoost(rapidity=4.0)
    assert 0.0 <= boost.velocity < 1.0
