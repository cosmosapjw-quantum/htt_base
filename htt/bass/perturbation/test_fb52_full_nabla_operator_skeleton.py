from __future__ import annotations

import numpy as np
import pytest

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
from bass.hierarchy.nabla_dispatch import HarmonicMode, make_nabla_tilde
from bass.perturbation.full_nabla_operator import (
    _rotation_matrix_zyz,
    make_full_mode_nabla_tilde_operator,
)


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


def _canonical_mode(label: str, k: float = 0.2) -> HarmonicMode:
    if label == "VII_0":
        return HarmonicMode(label, np.array([0.0, k, 0.0], dtype=np.float64))
    if label in {"II", "VIII"}:
        return HarmonicMode(label, np.array([k, 0.0, 0.0], dtype=np.float64))
    if label in {"III", "IV", "VI_0", "VI_h", "VII_h"}:
        return HarmonicMode(label, np.array([k, 0.0, 0.5 * k], dtype=np.float64))
    if label == "IX":
        ell = 4
        return HarmonicMode(
            label,
            np.array([np.sqrt(ell * (ell + 2)), 0.0, 0.0], dtype=np.float64),
            ell=ell,
        )
    return HarmonicMode(label, np.array([k, 0.0, 0.0], dtype=np.float64))


@pytest.mark.parametrize("label", tuple(_STRUCTURE_FACTORIES))
def test_fb52_identity_euler_angles_reduce_to_axis_aligned_dispatch(
    label: str,
) -> None:
    structure = _STRUCTURE_FACTORIES[label]()
    mode = _canonical_mode(label)
    op_full = make_full_mode_nabla_tilde_operator(
        structure,
        mode,
        euler_angles=(0.0, 0.0, 0.0),
    )
    op_base = make_nabla_tilde(structure, mode)
    tensor = np.array([[1.0, -2.0, 0.5], [0.0, 1.5, -1.0], [2.0, -0.5, 3.0]])
    np.testing.assert_allclose(
        op_full(tensor, kind="gradient"),
        op_base(tensor, kind="gradient"),
        rtol=1e-12,
        atol=1e-14,
    )


@pytest.mark.parametrize(
    ("label", "angles"),
    (
        ("II", (0.4, 0.7, -0.2)),
        ("VI_0", (0.2, 0.5, 0.3)),
        ("III", (-0.3, 0.6, 0.1)),
        ("VII_h", (0.1, 0.9, -0.4)),
        ("IX", (-0.2, 0.8, 0.5)),
    ),
)
def test_fb52_rotated_scalar_gradient_tracks_physical_wavevector(
    label: str,
    angles: tuple[float, float, float],
) -> None:
    structure = _STRUCTURE_FACTORIES[label]()
    canonical_mode = _canonical_mode(label)
    rotation = _rotation_matrix_zyz(*angles)
    physical_mode = HarmonicMode(
        label,
        rotation @ canonical_mode.k_vec,
        ell=canonical_mode.ell,
    )
    op = make_full_mode_nabla_tilde_operator(
        structure,
        physical_mode,
        euler_angles=angles,
    )
    scalar = np.array(2.5)
    grad = op(scalar, kind="gradient")
    np.testing.assert_allclose(
        grad,
        1j * physical_mode.k_vec * scalar,
        rtol=1e-12,
        atol=1e-14,
    )


@pytest.mark.parametrize(
    ("label", "angles"),
    (
        ("II", (0.4, 0.7, -0.2)),
        ("VI_0", (0.2, 0.5, 0.3)),
        ("III", (-0.3, 0.6, 0.1)),
        ("VII_h", (0.1, 0.9, -0.4)),
        ("IX", (-0.2, 0.8, 0.5)),
    ),
)
def test_fb52_rotated_vector_divergence_tracks_physical_wavevector(
    label: str,
    angles: tuple[float, float, float],
) -> None:
    structure = _STRUCTURE_FACTORIES[label]()
    canonical_mode = _canonical_mode(label)
    rotation = _rotation_matrix_zyz(*angles)
    physical_mode = HarmonicMode(
        label,
        rotation @ canonical_mode.k_vec,
        ell=canonical_mode.ell,
    )
    op = make_full_mode_nabla_tilde_operator(
        structure,
        physical_mode,
        euler_angles=angles,
    )
    vector = np.array([1.2, -0.4, 0.7], dtype=np.float64)
    div = op(vector, kind="divergence")
    expected = 1j * float(np.dot(physical_mode.k_vec, vector))
    np.testing.assert_allclose(div, expected, rtol=1e-12, atol=1e-14)


def test_fb52_rejects_label_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match"):
        make_full_mode_nabla_tilde_operator(
            type_i_constants(),
            HarmonicMode("V", np.array([0.2, 0.0, 0.0])),
            euler_angles=(0.0, 0.0, 0.0),
        )


def test_fb52_rejects_invalid_euler_angles() -> None:
    with pytest.raises(ValueError, match="euler_angles"):
        make_full_mode_nabla_tilde_operator(
            type_i_constants(),
            HarmonicMode("I", np.array([0.2, 0.0, 0.0])),
            euler_angles=(0.0, np.nan, 0.0),
        )
