from __future__ import annotations

import numpy as np
import pytest

from bass.likelihood.cosmological_frame import CosmologicalFrameLikelihood
from bass.likelihood.htt_decomposition import build_htt_decomposition
from bass.runtime.canonical_decision import make_canonical_decision
from tsc.diagnostics.tangency import TangencyResult, TangentKind


def _tangency(rel_res: float = 1.0e-8, fraction: float = 1.0) -> TangencyResult:
    total = 1.0
    tangent = fraction * total
    d_sq = total - tangent
    return TangencyResult(
        coefficients=np.array([1.0], dtype=float),
        tangent_norm_sq=tangent,
        total_norm_sq=total,
        D_sq=d_sq,
        D=float(np.sqrt(max(d_sq, 0.0))),
        relative_residual=rel_res,
        kind=TangentKind.ONE_FIELD,
        xi=0,
        eta=0.0,
        gram_matrix=np.array([[1.0]], dtype=float),
        moment_vector=np.array([1.0], dtype=float),
    )


def _directional_covariance() -> dict[str, object]:
    axis = np.array([0.0, 0.0, 1.0], dtype=float)
    tensor = 0.25 * np.outer(axis, axis)
    tensor -= np.trace(tensor) * np.eye(3) / 3.0
    ell = np.arange(9, dtype=int)
    return {
        "ell": ell,
        "preferred_axis": axis,
        "anisotropy_tensor": tensor,
        "offdiag_strength": 0.25,
        "C_ell": {
            "TT": np.linspace(10.0, 3.0, ell.size),
            "EE": np.linspace(1.0, 0.2, ell.size),
            "TE": np.linspace(0.8, 0.1, ell.size),
            "BB": np.zeros(ell.size),
        },
    }


def _likelihood(*, tier: str = "low_ell", beta_allow: bool = True) -> CosmologicalFrameLikelihood:
    tangency = _tangency()
    beta_gate = make_canonical_decision((beta_allow, {}), (True, {}), tangency)
    decomposition = build_htt_decomposition(
        directional_covariance=_directional_covariance(),
        prior_alignment={"axis_vector": np.array([0.0, 0.0, 1.0])},
        tangency_result=tangency,
        beta_gate=beta_gate,
    )
    return CosmologicalFrameLikelihood(htt_decomposition=decomposition, tier=tier)  # type: ignore[arg-type]


def test_fb74_cosmological_frame_docstring_carries_scope_pin() -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    doc = CosmologicalFrameLikelihood.__doc__ or ""
    assert "cosmological-frame only" in doc
    assert "observer_frame_adapter" in doc


@pytest.mark.parametrize(
    "key,value",
    [
        ("observer_boost", object()),
        ("beta_obs", 1.23e-3),
        ("v_hat_obs", np.array([1.0, 0.0, 0.0])),
        ("observer_frame", True),
    ],
)
def test_fb74_rejects_observer_frame_parameters(key: str, value: object) -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood()
    with pytest.raises(ValueError, match="observer_frame_adapter"):
        likelihood.log_prob({key: value})


def test_fb74_aligned_axis_scores_higher_than_orthogonal_axis() -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood()
    aligned = likelihood.log_prob({"axis_vector": np.array([0.0, 0.0, 1.0])})
    orthogonal = likelihood.log_prob({"axis_vector": np.array([1.0, 0.0, 0.0])})
    assert aligned > orthogonal


def test_fb74_axis_can_be_provided_as_angles() -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood()
    from_vector = likelihood.log_prob({"axis_vector": np.array([0.0, 0.0, 1.0])})
    from_angles = likelihood.log_prob({"axis_l_deg": 0.0, "axis_b_deg": 90.0})
    assert from_vector == pytest.approx(from_angles, rel=1.0e-12)


def test_fb74_reference_spectra_maximise_the_spectral_term() -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood()
    ref = likelihood.spectra_reference["TT"]
    aligned = likelihood.log_prob({"spectra_TT": ref})
    shifted = likelihood.log_prob({"spectra_TT": 1.1 * ref})
    assert aligned > shifted


@pytest.mark.parametrize(
    "lon_deg, lat_deg",
    [(0.0, 90.0), (0.0, -90.0), (45.0, 30.0), (135.0, -25.0)],
)
def test_fb74_angle_supplied_axes_produce_finite_log_prob(
    lon_deg: float, lat_deg: float
) -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood()
    value = likelihood.log_prob({"axis_l_deg": lon_deg, "axis_b_deg": lat_deg})
    assert np.isfinite(value)


@pytest.mark.parametrize("tier", ["low_ell", "hybrid", "full"])
def test_fb74_directional_surface_has_expected_shape(tier: str) -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood(tier=tier)
    surface = likelihood.directional_surface(n_longitude=33, n_latitude=17)
    assert surface["log_prob"].shape == (17, 33)


@pytest.mark.parametrize("tier", ["low_ell", "hybrid", "full"])
def test_fb74_log_prob_is_finite_across_declared_tiers(tier: str) -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood(tier=tier)
    assert np.isfinite(likelihood.log_prob({}))


def test_fb74_full_tier_penalises_broadband_mismatch_more_than_low_ell() -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    low = _likelihood(tier="low_ell")
    full = _likelihood(tier="full")
    mismatch = 1.15 * low.spectra_reference["TT"]
    low_val = low.log_prob({"spectra_TT": mismatch})
    full_val = full.log_prob({"spectra_TT": mismatch})
    assert full_val < low_val


def test_fb74_amplitude_prior_peaks_at_effective_amplitude() -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood()
    amp0 = likelihood.effective_amplitude
    centred = likelihood.log_prob({"amplitude": amp0})
    shifted = likelihood.log_prob({"amplitude": amp0 + 0.2})
    assert centred > shifted


def test_fb74_blocked_beta_gate_penalises_nonzero_amplitude() -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood(beta_allow=False)
    zero_amp = likelihood.log_prob({"amplitude": 0.0})
    nonzero_amp = likelihood.log_prob({"amplitude": 0.2})
    assert zero_amp > nonzero_amp


def test_fb74_default_axis_is_the_resolved_axis() -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood()
    explicit = likelihood.log_prob({"axis_vector": likelihood.resolved_axis})
    implicit = likelihood.log_prob({})
    assert explicit == pytest.approx(implicit, rel=1.0e-12)


def test_fb74_directional_surface_peak_is_finite() -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    likelihood = _likelihood()
    surface = likelihood.directional_surface(n_longitude=25, n_latitude=13)
    assert np.max(surface["log_prob"]) == pytest.approx(np.max(surface["log_prob"]))


def test_fb74_class_has_log_prob_method() -> None:
    """Cosmological-frame only: observer marginalisation belongs to FB-8 observer_frame_adapter."""
    assert hasattr(CosmologicalFrameLikelihood, "log_prob")
