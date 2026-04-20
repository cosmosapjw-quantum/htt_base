from __future__ import annotations

import numpy as np
import pytest

from bass.observer.adapters import apply_observer_boost
from bass.observer.composition import GlobalTiltState, compose_tilts
from bass.observer.discriminator import _tilt_spectra_signature
from bass.observer.observer_boost import ObserverBoost


def _spectra(L_max: int = 8) -> dict[str, np.ndarray]:
    ell = np.arange(L_max + 1, dtype=float)
    return {
        "TT": 5.0 / (ell + 1.0),
        "EE": 1.5 / (ell + 1.0),
        "TE": 0.7 / (ell + 1.0),
        "BB": np.zeros(L_max + 1, dtype=float),
    }


@pytest.mark.parametrize("rapidity", [0.0, 1.0e-5, 1.0e-3, 0.1, 0.5])
def test_fb84_global_tilt_state_velocity_matches_tanh(rapidity: float) -> None:
    tilt = GlobalTiltState(rapidity=rapidity)
    assert tilt.velocity == pytest.approx(float(np.tanh(rapidity)), rel=1.0e-15)


@pytest.mark.parametrize("bad_rapidity", [np.nan, np.inf, -np.inf, -1.0e-12, -0.5])
def test_fb84_global_tilt_rejects_nonfinite_or_negative_rapidity(bad_rapidity: float) -> None:
    with pytest.raises(ValueError):
        GlobalTiltState(rapidity=float(bad_rapidity))


@pytest.mark.parametrize(
    "bad_v_hat",
    [
        (),
        (1.0,),
        (1.0, 0.0),
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (0.5, 0.5, 0.5),
    ],
)
def test_fb84_global_tilt_rejects_invalid_directions(bad_v_hat: tuple[float, ...]) -> None:
    with pytest.raises(ValueError):
        GlobalTiltState(rapidity=1.0e-3, v_hat=bad_v_hat)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "tilt,boost,expected",
    [
        (
            GlobalTiltState(rapidity=0.0, v_hat=(1.0, 0.0, 0.0)),
            ObserverBoost(rapidity=0.0, v_hat=(0.0, 1.0, 0.0)),
            np.zeros(3),
        ),
        (
            GlobalTiltState(rapidity=1.0e-3, v_hat=(1.0, 0.0, 0.0)),
            ObserverBoost(rapidity=2.0e-3, v_hat=(0.0, 1.0, 0.0)),
            np.array([np.tanh(1.0e-3), np.tanh(2.0e-3), 0.0]),
        ),
        (
            GlobalTiltState(
                rapidity=5.0e-4,
                v_hat=(1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0),
            ),
            ObserverBoost(rapidity=5.0e-4, v_hat=(0.0, 0.0, 1.0)),
            np.array(
                [
                    np.tanh(5.0e-4) / np.sqrt(2.0),
                    np.tanh(5.0e-4) / np.sqrt(2.0),
                    np.tanh(5.0e-4),
                ]
            ),
        ),
    ],
)
def test_fb84_compose_tilts_returns_naive_vector_sum(
    tilt: GlobalTiltState,
    boost: ObserverBoost,
    expected: np.ndarray,
) -> None:
    observed = compose_tilts(tilt, boost)
    assert np.allclose(observed, expected, rtol=1.0e-12, atol=1.0e-15)


def test_fb84_compose_tilts_rejects_observer_boost_as_global_tilt() -> None:
    with pytest.raises(TypeError):
        compose_tilts(ObserverBoost(rapidity=1.0e-3), ObserverBoost(rapidity=0.0))


@pytest.mark.parametrize(
    "tilt,boost",
    [
        (
            GlobalTiltState(rapidity=1.0e-3, v_hat=(1.0, 0.0, 0.0)),
            ObserverBoost(rapidity=1.23e-3, v_hat=(0.0, 0.0, 1.0)),
        ),
        (
            GlobalTiltState(
                rapidity=8.0e-4,
                v_hat=(1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0),
            ),
            ObserverBoost(
                rapidity=1.1e-3,
                v_hat=(0.0, 1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)),
            ),
        ),
    ],
)
def test_fb84_tilt_signature_and_observer_boost_do_not_commute(
    tilt: GlobalTiltState,
    boost: ObserverBoost,
) -> None:
    spectra = _spectra()
    L_max = len(next(iter(spectra.values()))) - 1
    tilt_then_boost = apply_observer_boost(
        _tilt_spectra_signature(spectra, tilt),
        boost,
        L_max,
    )
    boost_then_tilt = _tilt_spectra_signature(
        apply_observer_boost(spectra, boost, L_max),
        tilt,
    )
    for key in ("TT", "EE", "TE"):
        assert not np.allclose(
            tilt_then_boost[key],
            boost_then_tilt[key],
            rtol=1.0e-12,
            atol=1.0e-15,
        )


def test_fb84_compose_tilts_docstring_keeps_diagnostic_only_pin() -> None:
    doc = compose_tilts.__doc__ or ""
    assert "Diagnostic-only" in doc
    assert "must never\n    be routed into the production path" in doc or "must never be routed into the production path" in doc
