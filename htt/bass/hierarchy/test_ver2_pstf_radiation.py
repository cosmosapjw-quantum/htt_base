from __future__ import annotations

import numpy as np
import pytest

from bass.collision.polarization import PolarizationHierarchyState
from bass.hierarchy import (
    PSTFHierarchyState,
    PSTFTensor,
    TruncationMetadata,
    make_radiation_state,
    project_from_angular_samples,
    reconstruct_on_sphere,
    zero_pstf,
)
from bass.hierarchy.pstf_radiation import RadiationPSTFState


def test_truncation_metadata_rejects_hidden_l2_promotion() -> None:
    with pytest.raises(ValueError, match="L=2"):
        TruncationMetadata(L=2)


def test_make_radiation_state_records_explicit_override() -> None:
    state = make_radiation_state(
        2,
        diagnostic_only=True,
        closure_name="diagnostic_cutoff",
    )
    assert state.L == 2
    assert state.truncation.diagnostic_only is True
    assert state.truncation.closure_name == "diagnostic_cutoff"
    assert state.frame_metadata.transport_frame == "n_frame"


def test_make_radiation_state_builds_matching_towers() -> None:
    state = make_radiation_state(4, allow_L2_override=False, closure_name="explicit_unset")
    assert state.I.L == 4
    assert state.E.L == 4
    assert state.B.L == 4


def _tensor_product_sphere_rule(L: int) -> tuple[np.ndarray, np.ndarray]:
    mu, mu_weights = np.polynomial.legendre.leggauss(2 * L + 3)
    n_phi = 4 * L + 5
    phi = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False)
    directions = []
    weights = []
    for mu_i, w_i in zip(mu, mu_weights):
        sin_theta = float(np.sqrt(max(0.0, 1.0 - mu_i * mu_i)))
        for phi_j in phi:
            directions.append(
                [
                    sin_theta * float(np.cos(phi_j)),
                    sin_theta * float(np.sin(phi_j)),
                    float(mu_i),
                ]
            )
            weights.append(float(w_i) * (2.0 * np.pi / float(n_phi)))
    return np.asarray(directions, dtype=np.float64), np.asarray(weights, dtype=np.float64)


def _random_hierarchy(L: int, *, seed: int, zero_low_ranks: bool = False) -> PSTFHierarchyState:
    rng = np.random.default_rng(seed)
    tensors = []
    for ell in range(L + 1):
        if zero_low_ranks and ell < 2:
            tensors.append(zero_pstf(ell))
            continue
        tensors.append(PSTFTensor(ell=ell, components=rng.normal(size=2 * ell + 1)))
    return PSTFHierarchyState(L=L, tensors=tensors)


def _random_radiation_state(L: int) -> RadiationPSTFState:
    return RadiationPSTFState(
        I=_random_hierarchy(L, seed=11),
        E=PolarizationHierarchyState(E=_random_hierarchy(L, seed=17, zero_low_ranks=True)),
        B=_random_hierarchy(L, seed=23, zero_low_ranks=True),
        truncation=TruncationMetadata(L=L, closure_name="quadrature_projection"),
    )


def test_projection_reconstruction_roundtrip_is_exact_for_polynomial_content() -> None:
    L = 4
    directions, weights = _tensor_product_sphere_rule(L)
    state = _random_radiation_state(L)
    samples = reconstruct_on_sphere(state, directions)
    recovered = project_from_angular_samples(
        samples,
        directions,
        weights,
        L=L,
        truncation=state.truncation,
    )
    assert np.allclose(recovered.I.as_flat(), state.I.as_flat(), rtol=0.0, atol=1e-10)
    assert np.allclose(recovered.E.E.as_flat(), state.E.E.as_flat(), rtol=0.0, atol=1e-10)
    assert np.allclose(recovered.B.as_flat(), state.B.as_flat(), rtol=0.0, atol=1e-10)


def test_projection_rejects_nonorthogonal_quadrature_rule() -> None:
    directions, weights = _tensor_product_sphere_rule(3)
    samples = {"I": np.ones(directions.shape[0], dtype=np.float64)}
    broken = weights.copy()
    broken[0] *= 1.05
    broken *= (4.0 * np.pi) / float(np.sum(broken))
    with pytest.raises(ValueError, match="quadrature"):
        project_from_angular_samples(samples, directions, broken, L=3)


def test_reconstruction_requires_unit_sphere_directions() -> None:
    state = _random_radiation_state(3)
    bad_dirs = np.array([[1.0, 0.0, 0.0], [0.2, 0.3, 0.4]], dtype=np.float64)
    with pytest.raises(ValueError, match="unit sphere"):
        reconstruct_on_sphere(state, bad_dirs)


def test_projection_rejects_forbidden_low_rank_polarization_support() -> None:
    directions, weights = _tensor_product_sphere_rule(3)
    samples = {
        "I": np.zeros(directions.shape[0], dtype=np.float64),
        "E": np.ones(directions.shape[0], dtype=np.float64),
        "B": np.zeros(directions.shape[0], dtype=np.float64),
    }
    with pytest.raises(ValueError, match="ell<2 support"):
        project_from_angular_samples(samples, directions, weights, L=3)
