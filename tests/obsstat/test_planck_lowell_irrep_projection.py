"""PMG-WU-006 analytic contracts for the observer-space l=2/3 STF bridge."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.special import sph_harm_y


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "htt" / "src"
PACKAGE_ROOT = ROOT / "htt"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from common.observable_irrep_state import (  # noqa: E402
    ObservableIrrepCarrier,
    ObservableIrrepRepresentation,
    ObservableIrrepState,
)


def _api():
    try:
        from obsstat import planck_lowell_irrep_projection as api
    except ImportError as exc:
        pytest.fail(f"PMG-WU-006 projection API is not implemented: {exc}", pytrace=False)
    return api


def _sha(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def _carrier(components: np.ndarray) -> ObservableIrrepCarrier:
    return ObservableIrrepCarrier(
        components=tuple(float(value) for value in components),
        frame="GALACTIC",
        basis="ORTHONORMAL_CONDON_SHORTLEY_REAL_L2_L5_V1",
        units="microK_CMB",
        source_identity=_sha("paired-300-carrier"),
        operator_identity=_sha("joint-cutsky-operator"),
        row_identity="SYNTHETIC-ROW",
    )


def _harmonic_value(block: np.ndarray, ell: int, direction: np.ndarray) -> float:
    x, y, z = direction
    theta = float(np.arccos(z))
    phi = float(np.arctan2(y, x) % (2.0 * np.pi))
    total = float(block[0] * sph_harm_y(ell, 0, theta, phi).real)
    cursor = 1
    for m in range(1, ell + 1):
        coefficient = complex(block[cursor], block[cursor + 1])
        total += float(2.0 * np.real(coefficient * sph_harm_y(ell, m, theta, phi)))
        cursor += 2
    return total


@pytest.mark.parametrize("ell", [2, 3])
def test_roundtrip_every_real_harmonic_basis_vector(ell: int) -> None:
    """Every registered real harmonic coordinate survives the STF bridge."""

    api = _api()
    dimension = 2 * ell + 1
    for index in range(dimension):
        harmonic = np.zeros(dimension, dtype=float)
        harmonic[index] = 1.0
        if ell == 2:
            tensor = api.real_harmonic_l2_to_stf(harmonic)
            replayed = api.stf2_to_real_harmonic(tensor)
        else:
            tensor = api.real_harmonic_l3_to_stf(harmonic)
            replayed = api.stf3_to_real_harmonic(tensor)
        np.testing.assert_allclose(replayed, harmonic, rtol=0.0, atol=2.0e-15)


@pytest.mark.parametrize("ell", [2, 3])
def test_roundtrip_reconstructs_condon_shortley_harmonic_polynomial(ell: int) -> None:
    """Cartesian contractions equal an independent SciPy harmonic evaluation."""

    api = _api()
    rng = np.random.default_rng(20260829 + ell)
    block = rng.normal(size=2 * ell + 1)
    tensor = (
        api.real_harmonic_l2_to_stf(block)
        if ell == 2
        else api.real_harmonic_l3_to_stf(block)
    )
    for direction in rng.normal(size=(32, 3)):
        direction /= np.linalg.norm(direction)
        expected = _harmonic_value(block, ell, direction)
        observed = (
            np.einsum("i,ij,j->", direction, tensor, direction)
            if ell == 2
            else np.einsum("i,j,k,ijk->", direction, direction, direction, tensor)
        )
        assert observed == pytest.approx(expected, rel=2.0e-14, abs=2.0e-14)


def test_projection_is_symmetric_trace_free_and_metadata_bound() -> None:
    """The exact carrier produces typed STF blocks without a physical state."""

    api = _api()
    values = np.linspace(-4.0, 7.0, 32)
    state = api.project_planck_carrier_to_observable_irreps(_carrier(values))

    assert type(state) is ObservableIrrepState
    assert state.basis == api.OBSERVABLE_STF_BASIS
    assert state.row_identity == "SYNTHETIC-ROW"
    assert state.claim_ceiling == "diagnostic_only_observer_space"
    assert tuple(block.representation for block in state.blocks) == (
        ObservableIrrepRepresentation.CARTESIAN_STF2_5,
        ObservableIrrepRepresentation.CARTESIAN_STF3_7,
    )
    q_tensor = api.stf2_components_to_tensor(state.blocks[0].components)
    o_tensor = api.stf3_components_to_tensor(state.blocks[1].components)
    np.testing.assert_allclose(q_tensor, q_tensor.T, rtol=0.0, atol=0.0)
    assert np.trace(q_tensor) == pytest.approx(0.0, abs=2.0e-15)
    for axis in range(3):
        assert np.trace(o_tensor, axis1=0, axis2=1)[axis] == pytest.approx(
            0.0, abs=2.0e-15
        )
    assert state.blocks[0].support.projection_identity == api.PROJECTION_IDENTITY
    assert state.blocks[1].support.projection_identity == api.PROJECTION_IDENTITY


def test_projection_refuses_scalar_short_carrier_and_nonfinite_content() -> None:
    """A scalar or malformed array cannot fabricate a direction or STF tensor."""

    api = _api()
    for invalid in (98 / 301, np.zeros(31), np.full(32, np.nan)):
        with pytest.raises((TypeError, ValueError), match="ObservableIrrepCarrier|carrier|finite"):
            api.project_planck_carrier_to_observable_irreps(invalid)


def test_component_tensor_layouts_roundtrip_without_hidden_trace_coordinate() -> None:
    api = _api()
    q_components = np.asarray([1.0, -2.0, 0.3, -0.4, 0.5])
    o_components = np.asarray([1.0, -2.0, 0.3, -0.4, 0.5, -0.6, 0.7])
    np.testing.assert_array_equal(
        api.stf2_tensor_to_components(api.stf2_components_to_tensor(q_components)),
        q_components,
    )
    np.testing.assert_array_equal(
        api.stf3_tensor_to_components(api.stf3_components_to_tensor(o_components)),
        o_components,
    )
