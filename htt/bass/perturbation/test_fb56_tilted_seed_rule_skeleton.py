from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy.boost_kernel import boost_project_axisymmetric
from bass.perturbation.regular_adiabatic_ic import (
    make_camb_regular_adiabatic_seed,
    unpack_camb_regular_adiabatic_seed,
)
from bass.perturbation.tilted_seed_rule import apply_tilted_boost_seed_rule


def _seed_state(L_max: int = 6) -> np.ndarray:
    return make_camb_regular_adiabatic_seed(
        k_comoving=1.0e-3,
        eta_initial=0.2,
        a_initial=3.0e-7,
        L_max=L_max,
    )


def _m0_slice(tower) -> np.ndarray:
    return np.array(
        [tower.tensors[ell].components[ell] for ell in range(tower.L + 1)],
        dtype=np.float64,
    )


@pytest.mark.parametrize("L_max", (2, 4, 6, 8))
@pytest.mark.parametrize(
    "v_hat_e",
    ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.4, 0.5, 0.7)),
)
def test_fb56_beta_zero_is_byte_identical(
    L_max: int,
    v_hat_e: tuple[float, float, float],
) -> None:
    seed = _seed_state(L_max=L_max)
    boosted = apply_tilted_boost_seed_rule(seed, beta=0.0, v_hat_e=v_hat_e)
    assert np.array_equal(boosted, seed)


@pytest.mark.parametrize(
    ("label", "getter"),
    (
        ("photon_T", lambda state: _m0_slice(state["combined"].photon_T)),
        ("photon_E", lambda state: _m0_slice(state["combined"].photon_E.E)),
        ("neutrino", lambda state: np.asarray(state["combined"].neutrino_reduced, dtype=np.float64)),
        ("baryon_pair", lambda state: np.asarray(state["extras"][0:2], dtype=np.float64)),
        ("cdm_pair", lambda state: np.asarray(state["extras"][2:4], dtype=np.float64)),
        ("metric_pair", lambda state: np.asarray(state["extras"][4:6], dtype=np.float64)),
    ),
)
def test_fb56_boosted_slices_match_axisymmetric_kernel(
    label: str,
    getter,
) -> None:
    seed = _seed_state(L_max=6)
    boosted = apply_tilted_boost_seed_rule(
        seed,
        beta=1.0e-2,
        v_hat_e=(1.0, 0.0, 0.0),
    )
    unpacked_before = unpack_camb_regular_adiabatic_seed(seed, L_max=6)
    unpacked_after = unpack_camb_regular_adiabatic_seed(boosted, L_max=6)
    expected = boost_project_axisymmetric(
        getter(unpacked_before),
        1.0e-2,
        (1.0, 0.0, 0.0),
    )
    np.testing.assert_allclose(
        getter(unpacked_after),
        expected,
        rtol=1e-12,
        atol=1e-14,
        err_msg=label,
    )


@pytest.mark.parametrize(
    "v_hat_e",
    ((0.4, 0.5, 0.7), (1.0, 1.0, 0.0), (0.1, -0.2, 0.3)),
)
def test_fb56_off_axis_boost_is_reserved_to_fb52(
    v_hat_e: tuple[float, float, float],
) -> None:
    with pytest.raises(NotImplementedError, match="FB-5.2"):
        apply_tilted_boost_seed_rule(_seed_state(), beta=1.0e-2, v_hat_e=v_hat_e)


@pytest.mark.parametrize("beta", (-1.0e-3, -0.1, 1.0, 1.5))
def test_fb56_invalid_beta_raises(beta: float) -> None:
    with pytest.raises(ValueError, match="beta"):
        apply_tilted_boost_seed_rule(
            _seed_state(),
            beta=beta,
            v_hat_e=(1.0, 0.0, 0.0),
        )
