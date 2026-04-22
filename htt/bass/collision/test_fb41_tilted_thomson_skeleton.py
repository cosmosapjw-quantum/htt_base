from __future__ import annotations

import numpy as np
import pytest

from bass.collision._tilted_layer_b_common import signed_axisymmetric_boost
from bass.collision.polarization import (
    PolarizationHierarchyState,
    zero_polarization_hierarchy,
)
from bass.collision.thomson_pstf import ThomsonAux, ThomsonPSTFCollisionOperator
from bass.collision.tilted_thomson_layer_b import (
    evaluate_tilted_thomson_pstf_collision,
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
        out = np.ones_like(arr)
        return _squeeze_if_scalar(out, scalar)

    def p_rest(self, eta):
        arr, scalar = _as_1d(eta)
        out = np.zeros_like(arr)
        return _squeeze_if_scalar(out, scalar)

    def dot_rho(self, eta):
        arr, scalar = _as_1d(eta)
        out = np.zeros_like(arr)
        return _squeeze_if_scalar(out, scalar)

    def _a_of_eta(self, eta):
        arr, scalar = _as_1d(eta)
        out = np.ones_like(arr)
        return _squeeze_if_scalar(out, scalar)


def _make_temperature_state() -> PSTFHierarchyState:
    st = zero_hierarchy(L=4)
    st.tensors[0].components[:] = [0.4]
    st.tensors[1].components[:] = [0.1, -0.3, 0.2]
    st.tensors[2].components[:] = [0.05, -0.02, 0.4, 0.11, -0.06]
    st.tensors[3].components[:] = np.linspace(-0.4, 0.4, 7)
    st.tensors[4].components[:] = np.linspace(0.3, -0.3, 9)
    return st


def _make_axisymmetric_temperature_state() -> PSTFHierarchyState:
    st = zero_hierarchy(L=4)
    st.tensors[1].components[1] = 0.12
    st.tensors[2].components[2] = 0.35
    st.tensors[3].components[3] = -0.18
    st.tensors[4].components[4] = 0.08
    return st


def _make_polarization_state() -> PolarizationHierarchyState:
    e_state = zero_polarization_hierarchy(L=4)
    e_state.tensors[2].components[:] = [0.02, -0.03, 0.15, 0.04, -0.01]
    e_state.tensors[3].components[:] = np.linspace(0.25, -0.25, 7)
    e_state.tensors[4].components[:] = np.linspace(-0.2, 0.2, 9)
    return e_state


def _make_axisymmetric_polarization_state() -> PolarizationHierarchyState:
    e_state = zero_polarization_hierarchy(L=4)
    e_state.tensors[2].components[2] = -0.07
    e_state.tensors[3].components[3] = 0.05
    e_state.tensors[4].components[4] = -0.03
    return e_state


def _make_tilt(
    beta: float,
    v_hat_e: tuple[float, float, float] = (1.0, 0.0, 0.0),
) -> TiltedSpeciesBackground:
    return TiltedSpeciesBackground(
        base=_DummySpecies(),
        beta=beta,
        v_hat_e=v_hat_e,
    )


def _assert_sym_trace_free_round_trip(tensor) -> None:
    full = tensor.to_full_tensor()
    repacked = pstf_from_tensor(sym_trace_free(full))
    np.testing.assert_allclose(repacked.components, tensor.components, atol=1e-12)


def _capture_anchor_fixture() -> dict[int, np.ndarray]:
    op = ThomsonPSTFCollisionOperator()
    temperature_state = _make_temperature_state()
    polarization_state = _make_polarization_state()
    aux = ThomsonAux(
        E_state=polarization_state,
        v_b_real_sph=np.array([0.2, -0.1, 0.05], dtype=np.float64),
        Gamma_T=1.7,
    )
    return {
        ell: op.evaluate(ell, temperature_state, aux).components.copy()
        for ell in range(temperature_state.L + 1)
    }


FB41_ANCHOR_FIXTURE = _capture_anchor_fixture()


@pytest.mark.parametrize("ell", [0, 1, 2, 3, 4])
def test_fb41_beta_zero_matches_anchor_fixture(ell: int) -> None:
    result = evaluate_tilted_thomson_pstf_collision(
        ell=ell,
        temperature_state=_make_temperature_state(),
        polarization_state=_make_polarization_state(),
        eta=12.0,
        v_b_real_sph=np.array([0.2, -0.1, 0.05], dtype=np.float64),
        Gamma_T=1.7,
        tilted_electron=_make_tilt(0.0),
    )
    assert np.array_equal(result.components, FB41_ANCHOR_FIXTURE[ell])


@pytest.mark.parametrize("beta", [0.01, 0.1, 0.3])
@pytest.mark.parametrize("ell", [1, 2, 3, 4])
def test_fb41_beta_sweep_is_finite_and_pstf(beta: float, ell: int) -> None:
    result = evaluate_tilted_thomson_pstf_collision(
        ell=ell,
        temperature_state=_make_temperature_state(),
        polarization_state=_make_polarization_state(),
        eta=8.0,
        v_b_real_sph=np.array([0.0, 0.03, -0.02], dtype=np.float64),
        Gamma_T=2.1,
        tilted_electron=_make_tilt(beta),
    )
    assert np.all(np.isfinite(result.components))
    _assert_sym_trace_free_round_trip(result)


@pytest.mark.parametrize("ell", [1, 3])
def test_fb41_tilt_generates_neighbor_coupling_from_pure_quadrupole(ell: int) -> None:
    result = evaluate_tilted_thomson_pstf_collision(
        ell=ell,
        temperature_state=_make_axisymmetric_temperature_state(),
        polarization_state=_make_axisymmetric_polarization_state(),
        eta=5.0,
        v_b_real_sph=np.zeros(3, dtype=np.float64),
        Gamma_T=1.0,
        tilted_electron=_make_tilt(0.1),
    )
    assert abs(result.components[ell]) > 0.0


def test_fb41_linear_challinor_m0_recurrence_matches_manual_axisymmetric_build() -> None:
    temperature_state = _make_axisymmetric_temperature_state()
    polarization_state = _make_axisymmetric_polarization_state()
    beta = 0.05
    v_b = np.zeros(3, dtype=np.float64)
    Gamma_T = 1.3

    boosted_temperature = temperature_state.copy()
    boosted_polarization = polarization_state.copy()
    temp_slice = signed_axisymmetric_boost(
        [temperature_state.tensors[ell].components[ell] for ell in range(5)],
        beta=beta,
        v_hat_e=(1.0, 0.0, 0.0),
    )
    pol_slice = signed_axisymmetric_boost(
        [polarization_state.tensors[ell].components[ell] for ell in range(5)],
        beta=beta,
        v_hat_e=(1.0, 0.0, 0.0),
    )
    for ell in range(5):
        boosted_temperature.tensors[ell].components[ell] = temp_slice[ell]
        boosted_polarization.tensors[ell].components[ell] = pol_slice[ell]

    tower = ThomsonPSTFCollisionOperator().evaluate_tower(
        boosted_temperature,
        boosted_polarization,
        v_b,
        Gamma_T,
    )
    expected_slice = signed_axisymmetric_boost(
        [tower.tensors[ell].components[ell] for ell in range(5)],
        beta=-beta,
        v_hat_e=(1.0, 0.0, 0.0),
    )

    for ell in range(1, 5):
        result = evaluate_tilted_thomson_pstf_collision(
            ell=ell,
            temperature_state=_make_axisymmetric_temperature_state(),
            polarization_state=_make_axisymmetric_polarization_state(),
            eta=5.0,
            v_b_real_sph=v_b,
            Gamma_T=Gamma_T,
            tilted_electron=_make_tilt(beta),
        )
        assert result.components[ell] == pytest.approx(expected_slice[ell], abs=1e-14)


def test_fb41_none_tilt_matches_anchor_operator() -> None:
    temperature_state = _make_temperature_state()
    polarization_state = _make_polarization_state()
    v_b = np.array([0.1, 0.0, -0.04], dtype=np.float64)
    Gamma_T = 0.7
    aux = ThomsonAux(
        E_state=polarization_state,
        v_b_real_sph=v_b,
        Gamma_T=Gamma_T,
    )
    anchor = ThomsonPSTFCollisionOperator().evaluate(2, temperature_state, aux)
    result = evaluate_tilted_thomson_pstf_collision(
        ell=2,
        temperature_state=temperature_state,
        polarization_state=polarization_state,
        eta=7.0,
        v_b_real_sph=v_b,
        Gamma_T=Gamma_T,
        tilted_electron=None,
    )
    np.testing.assert_array_equal(result.components, anchor.components)


def test_fb41_off_axis_direction_is_supported() -> None:
    result = evaluate_tilted_thomson_pstf_collision(
        ell=2,
        temperature_state=_make_temperature_state(),
        polarization_state=_make_polarization_state(),
        eta=4.0,
        v_b_real_sph=np.zeros(3, dtype=np.float64),
        Gamma_T=1.0,
        tilted_electron=_make_tilt(
            0.1,
            v_hat_e=(1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0),
        ),
    )
    assert np.all(np.isfinite(result.components))
    assert np.linalg.norm(np.delete(result.components, 2)) > 0.0


def test_fb41_superluminal_beta_rejected() -> None:
    with pytest.raises(ValueError, match="0 ≤ β < 1"):
        _make_tilt(1.01)


def test_fb41_malformed_direction_rejected() -> None:
    with pytest.raises(ValueError, match="unit vector"):
        _make_tilt(0.1, v_hat_e=(1.0, 1.0, 1.0))
