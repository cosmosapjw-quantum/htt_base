from __future__ import annotations

import numpy as np
import pytest

from obsstat import draw_correlated_real_shell_alms


def test_seeded_shell_draw_is_reproducible_with_declared_shape() -> None:
    covariance = np.array(
        [
            [1.0, 0.25],
            [0.25, 2.0],
        ]
    )

    first = draw_correlated_real_shell_alms(
        ell=3,
        shell_covariance=covariance,
        seed=252,
    )
    repeated = draw_correlated_real_shell_alms(
        ell=3,
        shell_covariance=covariance,
        seed=252,
    )
    changed_seed = draw_correlated_real_shell_alms(
        ell=3,
        shell_covariance=covariance,
        seed=253,
    )

    assert first.shape == (2, 7)
    assert first.dtype == np.complex128
    assert np.array_equal(first, repeated)
    assert not np.array_equal(first, changed_seed)


@pytest.mark.parametrize("ell", range(1, 6))
def test_every_shell_obeys_real_map_reality(ell: int) -> None:
    covariance = np.array(
        [
            [1.0, -0.2, 0.3],
            [-0.2, 0.8, 0.1],
            [0.3, 0.1, 1.2],
        ]
    )
    coefficients = draw_correlated_real_shell_alms(
        ell=ell,
        shell_covariance=covariance,
        seed=10 + ell,
    )

    assert np.array_equal(coefficients[:, ell].imag, np.zeros(3))
    for m in range(1, ell + 1):
        assert np.array_equal(
            coefficients[:, ell - m],
            ((-1) ** m) * np.conj(coefficients[:, ell + m]),
        )


def test_rank_one_covariance_preserves_cross_shell_constraints() -> None:
    shell_weights = np.array([1.0, -0.5, 2.0])
    covariance = np.outer(shell_weights, shell_weights)

    coefficients = draw_correlated_real_shell_alms(
        ell=4,
        shell_covariance=covariance,
        seed=17,
    )

    np.testing.assert_allclose(
        coefficients[1],
        -0.5 * coefficients[0],
        rtol=2e-14,
        atol=2e-14,
    )
    np.testing.assert_allclose(
        coefficients[2],
        2.0 * coefficients[0],
        rtol=2e-14,
        atol=2e-14,
    )


@pytest.mark.parametrize(
    ("covariance", "message"),
    [
        (np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]), "square"),
        (np.array([[1.0, 0.2], [0.1, 1.0]]), "symmetric"),
        (np.array([[1.0, 2.0], [2.0, 1.0]]), "positive semidefinite"),
        (np.array([[1.0, 1.0j], [-1.0j, 1.0]]), "real"),
        (np.array([[1.0, np.nan], [np.nan, 1.0]]), "finite"),
    ],
)
def test_invalid_shell_covariance_is_rejected(
    covariance: np.ndarray,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        draw_correlated_real_shell_alms(
            ell=2,
            shell_covariance=covariance,
            seed=1,
        )


@pytest.mark.parametrize(("ell", "seed"), [(0, 1), (2, -1), (1.5, 1)])
def test_invalid_draw_identity_is_rejected(ell: object, seed: int) -> None:
    covariance = np.eye(2)
    with pytest.raises(ValueError):
        draw_correlated_real_shell_alms(
            ell=ell,  # type: ignore[arg-type]
            shell_covariance=covariance,
            seed=seed,
        )
