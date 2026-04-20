from __future__ import annotations

import numpy as np
import pytest

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


def _beta_gate(allow: bool, tangency: TangencyResult):
    return make_canonical_decision((allow, {}), (True, {}), tangency)


def _directional_covariance(
    *,
    axis: np.ndarray | None = None,
    offdiag_strength: float = 0.25,
) -> dict[str, object]:
    preferred = np.asarray(axis if axis is not None else np.array([0.0, 0.0, 1.0]), dtype=float)
    preferred = preferred / np.linalg.norm(preferred)
    tensor = offdiag_strength * np.outer(preferred, preferred)
    tensor -= np.trace(tensor) * np.eye(3) / 3.0
    ell = np.arange(9, dtype=int)
    return {
        "ell": ell,
        "preferred_axis": preferred,
        "anisotropy_tensor": tensor,
        "offdiag_strength": offdiag_strength,
        "C_ell": {
            "TT": np.linspace(10.0, 3.0, ell.size),
            "EE": np.linspace(1.0, 0.2, ell.size),
            "TE": np.linspace(0.8, 0.1, ell.size),
            "BB": np.zeros(ell.size),
        },
    }


def test_fb73_htt_decomposition_contract_is_callable() -> None:
    assert callable(build_htt_decomposition)


def test_fb73_requires_anisotropy_tensor() -> None:
    with pytest.raises(KeyError, match="anisotropy_tensor"):
        build_htt_decomposition(
            directional_covariance={},
            prior_alignment={},
            tangency_result=_tangency(),
            beta_gate=_beta_gate(True, _tangency()),
        )


def test_fb73_rejects_wrong_tensor_shape() -> None:
    with pytest.raises(ValueError, match="shape"):
        build_htt_decomposition(
            directional_covariance={"anisotropy_tensor": np.zeros((2, 2))},
            prior_alignment={},
            tangency_result=_tangency(),
            beta_gate=_beta_gate(True, _tangency()),
        )


def test_fb73_resolved_axis_is_unit_normalised() -> None:
    tangency = _tangency()
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(),
        prior_alignment={"axis_vector": np.array([0.0, 0.0, 2.0])},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    assert np.linalg.norm(result["resolved_axis"]) == pytest.approx(1.0, rel=1.0e-12)


def test_fb73_prior_locked_when_aligned_and_tangent() -> None:
    tangency = _tangency(rel_res=1.0e-8, fraction=1.0)
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(axis=np.array([0.0, 0.0, 1.0])),
        prior_alignment={"axis_vector": np.array([0.0, 0.0, 1.0])},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    assert result["triad_status"] == "prior_locked"


def test_fb73_tangent_realigned_when_prior_misaligned_but_tangent() -> None:
    tangency = _tangency(rel_res=1.0e-8, fraction=0.6)
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(axis=np.array([0.0, 0.0, 1.0])),
        prior_alignment={"axis_vector": np.array([1.0, 0.0, 0.0])},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    assert result["triad_status"] == "tangent_realigned"


def test_fb73_dominant_fallback_when_tangency_fails() -> None:
    tangency = _tangency(rel_res=0.5, fraction=0.2)
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(axis=np.array([0.0, 1.0, 0.0])),
        prior_alignment={"axis_vector": np.array([1.0, 0.0, 0.0])},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    assert result["triad_status"] == "dominant_fallback"


def test_fb73_beta_gate_blocked_zeroes_effective_amplitude() -> None:
    tangency = _tangency()
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(offdiag_strength=0.3),
        prior_alignment={"axis_vector": np.array([0.0, 0.0, 1.0])},
        tangency_result=tangency,
        beta_gate=_beta_gate(False, tangency),
    )
    assert result["triad_status"] == "beta_gate_blocked"
    assert result["effective_amplitude"] == pytest.approx(0.0, abs=0.0)


@pytest.mark.parametrize("fraction", [0.2, 0.5, 1.0])
def test_fb73_effective_amplitude_scales_with_tangency_fraction(fraction: float) -> None:
    tangency = _tangency(rel_res=1.0e-8, fraction=fraction)
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(offdiag_strength=0.2),
        prior_alignment={"axis_vector": np.array([0.0, 0.0, 1.0])},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    assert result["effective_amplitude"] == pytest.approx(0.2 * fraction)


@pytest.mark.parametrize(
    "prior_axis, expected_min_alignment",
    [
        (np.array([0.0, 0.0, 1.0]), 0.999),
        (np.array([0.0, 1.0, 0.0]), 0.0),
        (np.array([1.0, 1.0, 0.0]), 0.0),
    ],
)
def test_fb73_alignment_cosine_tracks_prior_axis(prior_axis, expected_min_alignment: float) -> None:
    tangency = _tangency()
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(axis=np.array([0.0, 0.0, 1.0])),
        prior_alignment={"axis_vector": prior_axis},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    assert result["alignment_cosine"] >= expected_min_alignment


def test_fb73_direction_grid_vectors_are_unit_norm() -> None:
    tangency = _tangency()
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(),
        prior_alignment={"direction_grid_size": 48},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    norms = np.linalg.norm(result["direction_grid_unit_vectors"], axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1.0e-12)


def test_fb73_direction_grid_scores_match_grid_length() -> None:
    tangency = _tangency()
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(),
        prior_alignment={"direction_grid_size": 32},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    assert result["direction_grid_scores"].shape == (32,)


def test_fb73_spectra_reference_is_forwarded() -> None:
    tangency = _tangency()
    directional_covariance = _directional_covariance()
    result = build_htt_decomposition(
        directional_covariance=directional_covariance,
        prior_alignment={},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    assert set(result["spectra_reference"]) == {"TT", "EE", "TE", "BB"}


def test_fb73_resolution_sequence_is_explicit() -> None:
    tangency = _tangency()
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(),
        prior_alignment={},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    assert result["resolution_sequence"] == (
        "prior_alignment",
        "tangency",
        "beta_gate",
    )


def test_fb73_beta_gate_diagnostics_are_copied() -> None:
    tangency = _tangency()
    beta_gate = _beta_gate(True, tangency)
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(),
        prior_alignment={},
        tangency_result=tangency,
        beta_gate=beta_gate,
    )
    assert isinstance(result["beta_gate_diagnostics"], dict)


def test_fb73_missing_prior_axis_falls_back_to_preferred_axis() -> None:
    tangency = _tangency()
    directional_covariance = _directional_covariance(axis=np.array([0.0, 1.0, 0.0]))
    result = build_htt_decomposition(
        directional_covariance=directional_covariance,
        prior_alignment={},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    np.testing.assert_allclose(
        result["prior_axis"], directional_covariance["preferred_axis"], atol=1.0e-14
    )


def test_fb73_axis_precision_is_positive() -> None:
    tangency = _tangency()
    result = build_htt_decomposition(
        directional_covariance=_directional_covariance(offdiag_strength=0.3),
        prior_alignment={},
        tangency_result=tangency,
        beta_gate=_beta_gate(True, tangency),
    )
    assert result["axis_precision"] > 0.0

