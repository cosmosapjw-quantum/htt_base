from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy.ic import zero_IC
from bass.perturbation.k_zero_limit_gate import (
    assert_k_zero_limit_matches_background,
)
from bass.perturbation.regular_adiabatic_ic import (
    make_camb_regular_adiabatic_seed,
)


@pytest.mark.parametrize("L_max", (2, 3, 4, 5, 6))
def test_fb54_exact_k_zero_seed_passes_byte_identity_gate(L_max: int) -> None:
    background = zero_IC(L_max=L_max, a_initial=1.0e-6)
    perturbation = make_camb_regular_adiabatic_seed(
        k_comoving=0.0,
        eta_initial=0.2,
        a_initial=1.0e-6,
        L_max=L_max,
    )
    assert_k_zero_limit_matches_background(
        k_comoving=0.0,
        background_state=background,
        perturbation_state=perturbation,
        atol=0.0,
        rtol=0.0,
    )


@pytest.mark.parametrize("index", (0, 1, 2, 3, 10))
def test_fb54_prefix_mismatch_at_k_zero_raises(index: int) -> None:
    background = zero_IC(L_max=4, a_initial=1.0e-6)
    perturbation = np.concatenate([background.copy(), np.zeros(6, dtype=np.float64)])
    perturbation[index] += 1.0e-12
    with pytest.raises(AssertionError, match="byte-identical"):
        assert_k_zero_limit_matches_background(
            k_comoving=0.0,
            background_state=background,
            perturbation_state=perturbation,
            atol=0.0,
            rtol=0.0,
        )


@pytest.mark.parametrize("extra_index", range(6))
def test_fb54_nonzero_extra_tail_at_k_zero_raises(extra_index: int) -> None:
    background = zero_IC(L_max=4, a_initial=1.0e-6)
    perturbation = np.concatenate([background.copy(), np.zeros(6, dtype=np.float64)])
    perturbation[background.size + extra_index] = 1.0e-15
    with pytest.raises(AssertionError, match="identically zero"):
        assert_k_zero_limit_matches_background(
            k_comoving=0.0,
            background_state=background,
            perturbation_state=perturbation,
            atol=0.0,
            rtol=0.0,
        )


@pytest.mark.parametrize("delta", (1.0e-12, 3.0e-12, 1.0e-11, 3.0e-11))
def test_fb54_positive_k_allclose_gate_accepts_small_prefix_deltas(delta: float) -> None:
    background = zero_IC(L_max=4, a_initial=1.0e-6)
    perturbation = np.concatenate([background.copy(), np.zeros(6, dtype=np.float64)])
    perturbation[: background.size] += delta
    assert_k_zero_limit_matches_background(
        k_comoving=1.0e-3,
        background_state=background,
        perturbation_state=perturbation,
        atol=5.0e-11,
        rtol=0.0,
    )


@pytest.mark.parametrize(
    ("kwargs", "match"),
    (
        ({"k_comoving": -1.0, "background_state": np.zeros(3), "perturbation_state": np.zeros(3), "atol": 0.0, "rtol": 0.0}, "k_comoving"),
        ({"k_comoving": 0.0, "background_state": np.zeros(3), "perturbation_state": np.zeros(3), "atol": -1.0, "rtol": 0.0}, "atol"),
    ),
)
def test_fb54_invalid_scalar_inputs_raise(kwargs: dict[str, object], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        assert_k_zero_limit_matches_background(**kwargs)


def test_fb54_non_1d_states_raise() -> None:
    with pytest.raises(ValueError, match="1-D"):
        assert_k_zero_limit_matches_background(
            k_comoving=0.0,
            background_state=np.zeros((2, 2)),
            perturbation_state=np.zeros(4),
            atol=0.0,
            rtol=0.0,
        )


def test_fb54_non_finite_states_raise() -> None:
    background = zero_IC(L_max=4, a_initial=1.0e-6)
    perturbation = np.concatenate([background.copy(), np.zeros(6, dtype=np.float64)])
    perturbation[0] = np.nan
    with pytest.raises(AssertionError, match="finite"):
        assert_k_zero_limit_matches_background(
            k_comoving=0.0,
            background_state=background,
            perturbation_state=perturbation,
            atol=0.0,
            rtol=0.0,
        )


def test_fb54_shorter_perturbation_state_raises() -> None:
    background = zero_IC(L_max=4, a_initial=1.0e-6)
    with pytest.raises(AssertionError, match="shorter"):
        assert_k_zero_limit_matches_background(
            k_comoving=0.0,
            background_state=background,
            perturbation_state=background[:-1],
            atol=0.0,
            rtol=0.0,
        )
