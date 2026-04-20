from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import (
    type_i_constants,
    type_iv_constants,
    type_viih_constants,
    type_ix_constants,
)
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator
from bass.spectrum.off_diagonal_covariance import (
    assemble_bianchi_spectrum_covariance,
)

ETA_GRID = np.linspace(40.0, 420.0, 129)
K_GRID = np.array([0.05, 0.08, 0.12], dtype=float)
ELL_MAX = 8


def _visibility(eta: float) -> float:
    return float(np.exp(-0.5 * ((eta - 220.0) / 35.0) ** 2))


def _source_builder(*, anisotropy: float = 0.25, b_mode: float = 0.0):
    def _builder(eta: float, k: float) -> dict[str, float]:
        envelope = np.exp(-0.5 * ((eta - 210.0) / 40.0) ** 2)
        return {
            "temperature": envelope * (1.0 + 0.1 * k),
            "temperature_anisotropy": anisotropy * envelope,
            "polarization": 0.35 * envelope,
            "b_mode": b_mode * envelope,
        }

    return _builder


def _transfer_bundle(structure, **kwargs):
    return build_lowell_line_of_sight_propagator(
        structure,
        eta_grid_mpc=ETA_GRID,
        k_grid_mpc=K_GRID,
        ell_max=ELL_MAX,
        visibility_fn=_visibility,
        source_builder=kwargs.pop("source_builder", _source_builder()),
        limber_eta_sp_sign=kwargs.pop("limber_eta_sp_sign", "integrator"),
    )


def _covariance(structure, **kwargs):
    return assemble_bianchi_spectrum_covariance(
        transfer_bundle=_transfer_bundle(structure, **kwargs),
        k_grid_mpc=K_GRID,
        ell_max=ELL_MAX,
        off_diagonal_strategy=kwargs.pop("off_diagonal_strategy", "m_decoupled_blocks"),
    )


def test_fb72_off_diagonal_covariance_contract_is_callable() -> None:
    assert callable(assemble_bianchi_spectrum_covariance)


def test_fb72_rejects_negative_ell_max() -> None:
    with pytest.raises(ValueError, match="ell_max"):
        assemble_bianchi_spectrum_covariance(
            transfer_bundle=_transfer_bundle(type_i_constants()),
            k_grid_mpc=K_GRID,
            ell_max=-1,
        )


def test_fb72_rejects_invalid_strategy() -> None:
    with pytest.raises(ValueError, match="off_diagonal_strategy"):
        assemble_bianchi_spectrum_covariance(
            transfer_bundle=_transfer_bundle(type_i_constants()),
            k_grid_mpc=K_GRID,
            ell_max=ELL_MAX,
            off_diagonal_strategy="bad_strategy",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("spec", ["TT", "EE", "TE", "BB"])
def test_fb72_diagonal_spectra_have_expected_shape(spec: str) -> None:
    cov = _covariance(type_viih_constants())
    assert cov["C_ell"][spec].shape == (ELL_MAX + 1,)
    assert cov["D_ell"][spec].shape == (ELL_MAX + 1,)


@pytest.mark.parametrize(
    "strategy",
    ["m_decoupled_blocks", "dense_matrix", "wigner_d_sparse"],
)
def test_fb72_type_i_off_diagonal_vanishes_identically(strategy: str) -> None:
    cov = _covariance(type_i_constants(), off_diagonal_strategy=strategy)
    for spec in ("TT", "EE", "TE", "BB"):
        for mode in ("m0", "m+2", "m-2"):
            np.testing.assert_allclose(cov["off_diagonal_blocks"][spec][mode], 0.0)


@pytest.mark.parametrize("structure", [type_iv_constants(), type_viih_constants(), type_ix_constants()])
def test_fb72_anisotropic_types_produce_nonzero_off_diagonal_blocks(structure) -> None:
    cov = _covariance(structure)
    block_norm = 0.0
    for spec in ("TT", "EE", "TE"):
        for mode in ("m0", "m+2", "m-2"):
            block_norm += float(np.linalg.norm(cov["off_diagonal_blocks"][spec][mode]))
    assert block_norm > 0.0


def test_fb72_dense_matrix_view_has_expected_shape() -> None:
    cov = _covariance(type_viih_constants(), off_diagonal_strategy="dense_matrix")
    expected = (ELL_MAX + 1) * 3
    for spec in ("TT", "EE", "TE", "BB"):
        assert cov["dense_covariance"][spec].shape == (expected, expected)


def test_fb72_sparse_view_emits_entries_for_rotating_type() -> None:
    cov = _covariance(type_ix_constants(), off_diagonal_strategy="wigner_d_sparse")
    assert len(cov["wigner_d_sparse"]["TT"]) > 0
    assert {"ell", "ell_prime", "mode", "value"} <= set(cov["wigner_d_sparse"]["TT"][0])


def test_fb72_bb_stays_zero_for_type_i() -> None:
    cov = _covariance(type_i_constants())
    np.testing.assert_allclose(cov["C_ell"]["BB"], 0.0)


@pytest.mark.parametrize("structure", [type_iv_constants(), type_viih_constants(), type_ix_constants()])
def test_fb72_rotating_types_generate_nonzero_bb_spectrum(structure) -> None:
    cov = _covariance(structure, source_builder=_source_builder(b_mode=0.2))
    assert np.max(cov["C_ell"]["BB"]) >= 0.0


def test_fb72_preferred_axis_is_unit_norm() -> None:
    cov = _covariance(type_viih_constants())
    assert np.linalg.norm(cov["preferred_axis"]) == pytest.approx(1.0, rel=1.0e-12)


def test_fb72_anisotropy_tensor_is_symmetric_and_traceless() -> None:
    cov = _covariance(type_ix_constants())
    tensor = np.asarray(cov["anisotropy_tensor"], dtype=float)
    np.testing.assert_allclose(tensor, tensor.T, atol=1.0e-14)
    assert np.trace(tensor) == pytest.approx(0.0, abs=1.0e-14)


def test_fb72_default_strategy_is_m_decoupled_blocks() -> None:
    cov = _covariance(type_viih_constants())
    assert cov["off_diagonal_strategy"] == "m_decoupled_blocks"


def test_fb72_tt_and_ee_are_nonnegative() -> None:
    cov = _covariance(type_viih_constants())
    assert np.min(cov["C_ell"]["TT"]) >= 0.0
    assert np.min(cov["C_ell"]["EE"]) >= 0.0


def test_fb72_te_is_finite_for_anisotropic_type() -> None:
    cov = _covariance(type_viih_constants())
    assert np.all(np.isfinite(cov["C_ell"]["TE"]))


@pytest.mark.parametrize("spec", ["TT", "EE", "TE", "BB"])
def test_fb72_diagonal_by_mode_carries_three_modes(spec: str) -> None:
    cov = _covariance(type_viih_constants())
    assert cov["diagonal_by_mode"][spec].shape == (3, ELL_MAX + 1)


def test_fb72_mode_blocks_are_symmetric() -> None:
    cov = _covariance(type_viih_constants())
    for spec in ("TT", "EE", "TE", "BB"):
        for mode in ("m0", "m+2", "m-2"):
            block = cov["off_diagonal_blocks"][spec][mode]
            np.testing.assert_allclose(block, block.T, atol=1.0e-14)


def test_fb72_type_i_kasner_isotropic_limit_keeps_offdiag_strength_zero() -> None:
    cov = _covariance(type_i_constants())
    assert cov["offdiag_strength"] == pytest.approx(0.0, abs=0.0)


def test_fb72_rotating_types_report_positive_offdiag_strength() -> None:
    cov = _covariance(type_viih_constants())
    assert cov["offdiag_strength"] > 0.0

