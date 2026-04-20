from __future__ import annotations

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from bass.background.bianchi_types import (
    flrw_constants,
    type_i_constants,
    type_ii_constants,
    type_iii_constants,
    type_iv_constants,
    type_ix_constants,
    type_v_constants,
    type_vi0_constants,
    type_vih_constants,
    type_vii0_constants,
    type_viih_constants,
    type_viii_constants,
)
from bass.hierarchy.closure import HardCutClosure
from bass.hierarchy.collision_interface import ZeroCollisionOperator
from bass.hierarchy.nabla_dispatch import HarmonicMode, scalar_laplacian_eigenvalue
from bass.hierarchy.pstf_tensor import pack_hierarchy, zero_hierarchy
from bass.perturbation.harmonic_modes import make_harmonic_mode_rhs_context
from bass.species.background_table import build_flrw_background_table


_STRUCTURE_FACTORIES = {
    "FLRW": flrw_constants,
    "I": type_i_constants,
    "II": type_ii_constants,
    "III": type_iii_constants,
    "IV": type_iv_constants,
    "V": type_v_constants,
    "VI_0": type_vi0_constants,
    "VI_h": type_vih_constants,
    "VII_0": type_vii0_constants,
    "VII_h": type_viih_constants,
    "VIII": type_viii_constants,
    "IX": type_ix_constants,
}
_MODE_FAMILY = {
    "FLRW": "plane_wave",
    "I": "plane_wave",
    "II": "center_line",
    "III": "class_b_abelian_plane",
    "IV": "class_b_abelian_plane",
    "V": "hyperbolic",
    "VI_0": "abelian_plane",
    "VI_h": "class_b_abelian_plane",
    "VII_0": "helical_axis",
    "VII_h": "spiral",
    "VIII": "cartan_axis",
    "IX": "discrete_s3",
}


def _representative_mode(label: str, k: float = 0.1) -> HarmonicMode:
    if label == "VII_0":
        return HarmonicMode(label, np.array([0.0, k, 0.0], dtype=np.float64))
    if label in {"II", "VIII"}:
        return HarmonicMode(label, np.array([k, 0.0, 0.0], dtype=np.float64))
    if label in {"III", "IV", "VI_0", "VI_h", "VII_h"}:
        return HarmonicMode(label, np.array([k, 0.0, 0.5 * k], dtype=np.float64))
    if label == "IX":
        ell = 3
        return HarmonicMode(
            label,
            np.array([np.sqrt(ell * (ell + 2)), 0.0, 0.0], dtype=np.float64),
            ell=ell,
        )
    return HarmonicMode(label, np.array([k, 0.0, 0.0], dtype=np.float64))


@pytest.fixture(scope="module")
def bg_table():
    return build_flrw_background_table(n_eta=400)


@pytest.mark.parametrize("label", tuple(_STRUCTURE_FACTORIES))
def test_fb51_context_metadata_matches_dispatch_ssot(label: str) -> None:
    structure = _STRUCTURE_FACTORIES[label]()
    mode = _representative_mode(label)
    context = make_harmonic_mode_rhs_context(structure, mode, L_max=4)
    assert context["structure"] is structure
    assert context["mode"] == mode
    assert context["L_max"] == 4
    assert context["state_dtype"] == np.dtype(np.complex128)
    assert context["mode_family"] == _MODE_FAMILY[label]
    assert context["spectrum_kind"] == ("discrete" if label == "IX" else "continuous")
    assert callable(context["nabla_operator"])
    assert callable(context["photon_rhs"])
    assert context["requires_full_operator"] is False
    assert context["laplacian_eigenvalue"] == pytest.approx(
        scalar_laplacian_eigenvalue(structure, mode),
        rel=1e-12,
        abs=1e-14,
    )
    assert context["k_magnitude"] == pytest.approx(
        float(np.linalg.norm(mode.k_vec)),
        rel=1e-12,
        abs=1e-14,
    )
    if label in {"V", "III", "IV", "VI_h", "VII_h"}:
        meta = context["mode_quantization"]
        assert meta["type_label"] == label
        assert meta["effective_eigenvalue"] > 0.0
    else:
        assert "mode_quantization" not in context
    if label == "IX":
        assert context["discrete_ell"] == 3
    else:
        assert "discrete_ell" not in context


@pytest.mark.parametrize("label", ("FLRW", "I", "II", "VII_0", "IX"))
def test_fb51_photon_rhs_returns_complex_finite_gradient_response(
    label: str,
    bg_table,
) -> None:
    structure = _STRUCTURE_FACTORIES[label]()
    mode = _representative_mode(label, k=0.08)
    context = make_harmonic_mode_rhs_context(structure, mode, L_max=3)

    state = zero_hierarchy(3)
    state.tensors[0].components[0] = 1.0
    y0 = pack_hierarchy(state).astype(np.complex128)
    eta_eval = 10.0
    dy = context["photon_rhs"](
        eta_eval,
        y0,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    assert dy.shape == y0.shape
    assert np.iscomplexobj(dy)
    assert np.all(np.isfinite(dy.real))
    assert np.all(np.isfinite(dy.imag))
    assert np.linalg.norm(dy[1:4]) > 0.0


@pytest.mark.parametrize("k_value", (0.04, 0.06, 0.1))
def test_fb51_high_k_complex_rhs_short_integration_stays_finite(
    k_value: float,
    bg_table,
) -> None:
    structure = type_i_constants()
    mode = HarmonicMode("I", np.array([k_value, 0.0, 0.0], dtype=np.float64))
    context = make_harmonic_mode_rhs_context(structure, mode, L_max=3)

    state = zero_hierarchy(3)
    state.tensors[0].components[0] = 1.0
    state.tensors[1].components[1] = 1.0e-8
    y0 = pack_hierarchy(state).astype(np.complex128)

    def rhs(eta: float, y: np.ndarray) -> np.ndarray:
        return context["photon_rhs"](
            eta,
            y,
            bg_table=bg_table,
            tetrad_state=None,
            closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )

    sol = solve_ivp(rhs, (10.0, 11.0), y0, max_step=0.02, rtol=1e-8, atol=1e-10)
    assert sol.success
    assert np.all(np.isfinite(sol.y.real))
    assert np.all(np.isfinite(sol.y.imag))
    assert np.max(np.abs(sol.y)) < 10.0


def test_fb51_context_rejects_negative_lmax() -> None:
    with pytest.raises(ValueError, match="L_max"):
        make_harmonic_mode_rhs_context(
            type_i_constants(),
            HarmonicMode("I", np.array([0.1, 0.0, 0.0])),
            L_max=-1,
        )


def test_fb51_context_rejects_label_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match"):
        make_harmonic_mode_rhs_context(
            type_i_constants(),
            HarmonicMode("V", np.array([0.1, 0.0, 0.0])),
            L_max=3,
        )
