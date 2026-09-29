from __future__ import annotations

import numpy as np
import pytest

from htt.obsstat.spectral_residual_analysis import (
    SpectralContractError, Spectrum, analyze_residuals, cl_to_dl, project_window,
    spectrum_from_npz, validate_spectrum,
)


def test_correlated_quadratic_is_not_diagonal_proxy() -> None:
    observed = Spectrum("two-bin", np.array([2., 3.]), np.array([2., 2.]), "TT", "Dl", "uK^2",
                        np.ones(2), np.ones(2), np.array([[1., .8], [.8, 1.]]))
    result = analyze_residuals(observed, [2., 3.], [1., 1.], theory_quantity="Dl")
    assert result["full_covariance_quadratic"] == pytest.approx(1.1111111111)
    assert result["diagonal_error_quadratic_proxy"] == pytest.approx(2.0)
    assert result["p_value"] is None


def test_cl_to_dl_transforms_full_covariance() -> None:
    ell = np.array([2., 3.])
    values, covariance = cl_to_dl(ell, np.array([1., -2.]), np.diag([4., 9.]))
    scale = ell * (ell + 1.) / (2. * np.pi)
    assert np.allclose(values, scale * np.array([1., -2.]))
    assert np.allclose(covariance, np.diag(scale) @ np.diag([4., 9.]) @ np.diag(scale))
    assert values[1] < 0


def test_asymmetric_errors_and_negative_te_are_preserved() -> None:
    item = validate_spectrum(Spectrum("te", np.array([2., 3.]), np.array([-4., 2.]), "TE", "Dl", "uK^2",
                                      np.array([1., 2.]), np.array([3., 4.])))
    result = analyze_residuals(item, [2., 3.], [0., 0.], theory_quantity="Dl")
    assert result["observed"][0] == -4.
    assert result["error_lo"] == [1., 2.]
    assert result["error_hi"] == [3., 4.]


def test_window_shape_mismatch_refuses_spt_style_truncation() -> None:
    with pytest.raises(SpectralContractError, match="window columns"):
        project_window(np.ones((39, 792)), np.ones(39))


def test_loader_rejects_non_spectral_reference(tmp_path) -> None:
    path = tmp_path / "thermal.npz"
    np.savez(path, a=np.arange(4), eta=np.arange(4))
    with pytest.raises(SpectralContractError, match="not the explicit"):
        spectrum_from_npz(path, dataset_id="reference.thermal", metadata={})


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", __file__]))
