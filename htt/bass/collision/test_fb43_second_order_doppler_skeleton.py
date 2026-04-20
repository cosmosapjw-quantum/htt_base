from __future__ import annotations

import numpy as np
import pytest

from bass.collision.polarization import zero_polarization_hierarchy
from bass.collision.thomson_pstf import ThomsonAux, ThomsonPSTFCollisionOperator
from bass.collision.tilted_doppler_second_order import (
    evaluate_tilted_second_order_doppler_correction,
)
from bass.hierarchy.contractions import sym_trace_free
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    pstf_from_tensor,
    zero_hierarchy,
)
from bass.species.base import (
    SpeciesBackground,
    SpeciesLabel,
    _as_1d,
    _squeeze_if_scalar,
)
from bass.species.tilted import TiltedSpeciesBackground


class _DummySpecies(SpeciesBackground):
    label = SpeciesLabel.BARYON

    def rho_rest(self, eta):
        arr, scalar = _as_1d(eta)
        return _squeeze_if_scalar(np.ones_like(arr), scalar)

    def p_rest(self, eta):
        arr, scalar = _as_1d(eta)
        return _squeeze_if_scalar(np.zeros_like(arr), scalar)

    def dot_rho(self, eta):
        arr, scalar = _as_1d(eta)
        return _squeeze_if_scalar(np.zeros_like(arr), scalar)

    def _a_of_eta(self, eta):
        arr, scalar = _as_1d(eta)
        return _squeeze_if_scalar(np.ones_like(arr), scalar)


def _make_tilt(
    beta: float,
    v_hat_e: tuple[float, float, float] = (1.0, 0.0, 0.0),
) -> TiltedSpeciesBackground:
    return TiltedSpeciesBackground(
        base=_DummySpecies(),
        beta=beta,
        v_hat_e=v_hat_e,
    )


def _make_temperature_state() -> PSTFHierarchyState:
    st = zero_hierarchy(L=4)
    st.tensors[0].components[:] = [0.2]
    st.tensors[1].components[:] = [0.06, -0.02, 0.04]
    st.tensors[2].components[:] = [0.01, -0.03, 0.18, 0.05, -0.02]
    st.tensors[3].components[:] = np.linspace(-0.15, 0.15, 7)
    st.tensors[4].components[:] = np.linspace(0.11, -0.11, 9)
    return st


def _capture_anchor_fixture() -> dict[int, np.ndarray]:
    state = _make_temperature_state()
    aux = ThomsonAux(
        E_state=zero_polarization_hierarchy(state.L),
        v_b_real_sph=np.array([0.03, -0.01, 0.02], dtype=np.float64),
        Gamma_T=1.6,
    )
    op = ThomsonPSTFCollisionOperator()
    return {
        ell: op.evaluate(ell, state, aux).components.copy()
        for ell in range(state.L + 1)
    }


FB43_ANCHOR = _capture_anchor_fixture()


def _assert_sym_trace_free_round_trip(tensor) -> None:
    full = tensor.to_full_tensor()
    repacked = pstf_from_tensor(sym_trace_free(full))
    np.testing.assert_allclose(repacked.components, tensor.components, atol=1e-12)


@pytest.mark.parametrize("ell", [0, 1, 2, 3, 4])
def test_fb43_beta_zero_returns_exact_zero(ell: int) -> None:
    result = evaluate_tilted_second_order_doppler_correction(
        ell=ell,
        temperature_state=_make_temperature_state(),
        eta=3.0,
        v_b_real_sph=np.array([0.03, -0.01, 0.02], dtype=np.float64),
        Gamma_T=1.6,
        tilted_electron=_make_tilt(0.0),
    )
    assert np.array_equal(result.components, np.zeros_like(result.components))


@pytest.mark.parametrize("beta", [0.01, 0.1, 0.3])
@pytest.mark.parametrize("ell", [1, 2, 3, 4])
def test_fb43_beta_sweep_is_finite_and_pstf(beta: float, ell: int) -> None:
    result = evaluate_tilted_second_order_doppler_correction(
        ell=ell,
        temperature_state=_make_temperature_state(),
        eta=2.0,
        v_b_real_sph=np.array([0.03, -0.01, 0.02], dtype=np.float64),
        Gamma_T=1.6,
        tilted_electron=_make_tilt(beta),
    )
    assert np.all(np.isfinite(result.components))
    _assert_sym_trace_free_round_trip(result)


@pytest.mark.parametrize("beta", [0.01, 0.1, 0.3])
@pytest.mark.parametrize("ell", [1, 2, 3])
def test_fb43_quadratic_prefactor_matches_gamma_sq_minus_one(beta: float, ell: int) -> None:
    result = evaluate_tilted_second_order_doppler_correction(
        ell=ell,
        temperature_state=_make_temperature_state(),
        eta=4.0,
        v_b_real_sph=np.array([0.03, -0.01, 0.02], dtype=np.float64),
        Gamma_T=1.6,
        tilted_electron=_make_tilt(beta),
    )
    expected = (_make_tilt(beta).gamma_sq - 1.0) * FB43_ANCHOR[ell]
    np.testing.assert_allclose(result.components, expected, atol=1e-12)


def test_fb43_small_beta_matches_beta_squared_closed_form() -> None:
    beta = 1.0e-4
    result = evaluate_tilted_second_order_doppler_correction(
        ell=2,
        temperature_state=_make_temperature_state(),
        eta=1.0,
        v_b_real_sph=np.array([0.03, -0.01, 0.02], dtype=np.float64),
        Gamma_T=1.6,
        tilted_electron=_make_tilt(beta),
    )
    expected = (beta * beta) * FB43_ANCHOR[2]
    np.testing.assert_allclose(result.components, expected, rtol=1.0e-6, atol=1.0e-12)


def test_fb43_correction_is_monotone_in_beta_norm() -> None:
    norms = []
    for beta in (0.01, 0.1, 0.3):
        corr = evaluate_tilted_second_order_doppler_correction(
            ell=2,
            temperature_state=_make_temperature_state(),
            eta=2.0,
            v_b_real_sph=np.array([0.03, -0.01, 0.02], dtype=np.float64),
            Gamma_T=1.6,
            tilted_electron=_make_tilt(beta),
        )
        norms.append(np.linalg.norm(corr.components))
    assert norms[0] < norms[1] < norms[2]


def test_fb43_none_tilt_is_zero() -> None:
    result = evaluate_tilted_second_order_doppler_correction(
        ell=3,
        temperature_state=_make_temperature_state(),
        eta=2.0,
        v_b_real_sph=np.array([0.03, -0.01, 0.02], dtype=np.float64),
        Gamma_T=1.6,
        tilted_electron=None,
    )
    np.testing.assert_array_equal(result.components, np.zeros(7))


def test_fb43_superluminal_beta_rejected() -> None:
    with pytest.raises(ValueError, match="0 ≤ β < 1"):
        _make_tilt(1.0)


def test_fb43_malformed_direction_rejected() -> None:
    with pytest.raises(ValueError, match="unit vector"):
        _make_tilt(0.1, v_hat_e=(1.0, 1.0, 1.0))
