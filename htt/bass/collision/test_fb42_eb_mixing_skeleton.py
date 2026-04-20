from __future__ import annotations

import numpy as np
import pytest

from bass.collision.polarization import (
    E_mode_collision_source,
    PolarizationHierarchyState,
    zero_polarization_hierarchy,
)
from bass.collision.tilted_eb_mixing import (
    evaluate_tilted_polarization_eb_collision,
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


def _make_e_state() -> PolarizationHierarchyState:
    state = zero_polarization_hierarchy(L=4)
    state.tensors[2].components[:] = [0.03, -0.04, 0.12, 0.02, -0.01]
    state.tensors[3].components[:] = np.linspace(-0.18, 0.18, 7)
    state.tensors[4].components[:] = np.linspace(0.14, -0.14, 9)
    return state


def _make_axisymmetric_e_state() -> PolarizationHierarchyState:
    state = zero_polarization_hierarchy(L=4)
    state.tensors[2].components[2] = 0.11
    state.tensors[3].components[3] = -0.06
    state.tensors[4].components[4] = 0.04
    return state


def _make_b_state() -> PSTFHierarchyState:
    state = zero_hierarchy(L=4)
    state.tensors[2].components[:] = [-0.01, 0.03, -0.02, 0.04, -0.05]
    state.tensors[3].components[:] = np.linspace(0.12, -0.12, 7)
    state.tensors[4].components[:] = np.linspace(-0.08, 0.08, 9)
    return state


def _assert_sym_trace_free_round_trip(tensor) -> None:
    full = tensor.to_full_tensor()
    repacked = pstf_from_tensor(sym_trace_free(full))
    np.testing.assert_allclose(repacked.components, tensor.components, atol=1e-12)


PI2_FIXTURE = np.array([0.05, -0.03, 0.2, 0.04, -0.02], dtype=np.float64)


def _capture_anchor_fixture() -> dict[int, np.ndarray]:
    e_state = _make_e_state()
    return {
        ell: E_mode_collision_source(
            ell=ell,
            E_state=e_state,
            Pi_2_packed=(PI2_FIXTURE if ell == 2 else None),
            Gamma_T=1.4,
        ).components.copy()
        for ell in range(e_state.L + 1)
    }


FB42_E_ANCHOR = _capture_anchor_fixture()


@pytest.mark.parametrize("ell", [0, 1, 2, 3, 4])
def test_fb42_beta_zero_matches_e_anchor_and_zero_b(ell: int) -> None:
    e_result, b_result = evaluate_tilted_polarization_eb_collision(
        ell=ell,
        e_state=_make_e_state(),
        eta=6.0,
        Pi_2_packed=PI2_FIXTURE,
        Gamma_T=1.4,
        b_state=None,
        tilted_electron=_make_tilt(0.0),
    )
    assert np.array_equal(e_result.components, FB42_E_ANCHOR[ell])
    assert np.array_equal(b_result.components, np.zeros_like(b_result.components))


@pytest.mark.parametrize("beta", [0.01, 0.1, 0.3])
@pytest.mark.parametrize("ell", [2, 3, 4])
def test_fb42_beta_sweep_is_finite_and_pstf(beta: float, ell: int) -> None:
    e_result, b_result = evaluate_tilted_polarization_eb_collision(
        ell=ell,
        e_state=_make_e_state(),
        eta=4.0,
        Pi_2_packed=PI2_FIXTURE,
        Gamma_T=1.9,
        b_state=_make_b_state(),
        tilted_electron=_make_tilt(beta),
    )
    assert np.all(np.isfinite(e_result.components))
    assert np.all(np.isfinite(b_result.components))
    _assert_sym_trace_free_round_trip(e_result)
    _assert_sym_trace_free_round_trip(b_result)


@pytest.mark.parametrize("beta", [0.01, 0.1, 0.3])
def test_fb42_e_only_input_generates_nonzero_b(beta: float) -> None:
    _, b_result = evaluate_tilted_polarization_eb_collision(
        ell=2,
        e_state=_make_axisymmetric_e_state(),
        eta=3.0,
        Pi_2_packed=PI2_FIXTURE,
        Gamma_T=1.0,
        b_state=zero_hierarchy(4),
        tilted_electron=_make_tilt(beta),
    )
    assert abs(b_result.components[2]) > 0.0


def test_fb42_none_b_state_matches_explicit_zero_b_state() -> None:
    args = dict(
        ell=3,
        e_state=_make_e_state(),
        eta=5.0,
        Pi_2_packed=PI2_FIXTURE,
        Gamma_T=1.1,
        tilted_electron=_make_tilt(0.1),
    )
    implicit = evaluate_tilted_polarization_eb_collision(
        **args,
        b_state=None,
    )
    explicit = evaluate_tilted_polarization_eb_collision(
        **args,
        b_state=zero_hierarchy(4),
    )
    np.testing.assert_allclose(implicit[0].components, explicit[0].components)
    np.testing.assert_allclose(implicit[1].components, explicit[1].components)


def test_fb42_beta_zero_b_mode_floor_is_exact() -> None:
    _, b_result = evaluate_tilted_polarization_eb_collision(
        ell=4,
        e_state=_make_e_state(),
        eta=5.0,
        Pi_2_packed=PI2_FIXTURE,
        Gamma_T=0.8,
        b_state=_make_b_state(),
        tilted_electron=None,
    )
    np.testing.assert_array_equal(b_result.components, np.zeros(9))


def test_fb42_off_axis_direction_raises() -> None:
    with pytest.raises(NotImplementedError, match="off-axis"):
        evaluate_tilted_polarization_eb_collision(
            ell=2,
            e_state=_make_e_state(),
            eta=2.0,
            Pi_2_packed=PI2_FIXTURE,
            Gamma_T=1.0,
            b_state=zero_hierarchy(4),
            tilted_electron=_make_tilt(0.1, v_hat_e=(1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0)),
        )


def test_fb42_b_state_depth_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="must match"):
        evaluate_tilted_polarization_eb_collision(
            ell=2,
            e_state=_make_e_state(),
            eta=1.0,
            Pi_2_packed=PI2_FIXTURE,
            Gamma_T=1.0,
            b_state=zero_hierarchy(3),
            tilted_electron=_make_tilt(0.1),
        )


def test_fb42_superluminal_beta_rejected() -> None:
    with pytest.raises(ValueError, match="0 ≤ β < 1"):
        _make_tilt(1.0)


def test_fb42_malformed_direction_rejected() -> None:
    with pytest.raises(ValueError, match="unit vector"):
        _make_tilt(0.1, v_hat_e=(1.0, 1.0, 1.0))
