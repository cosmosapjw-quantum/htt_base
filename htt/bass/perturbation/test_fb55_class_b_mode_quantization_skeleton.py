from __future__ import annotations

import pytest

from bass.background.bianchi_types import (
    type_i_constants,
    type_ii_constants,
    type_iii_constants,
    type_iv_constants,
    type_v_constants,
    type_vih_constants,
    type_viih_constants,
    type_vii0_constants,
    type_viii_constants,
)
from bass.perturbation.class_b_mode_quantization import (
    quantise_class_b_mode,
)


_SUPPORTED = {
    "V": type_v_constants,
    "III": type_iii_constants,
    "IV": type_iv_constants,
    "VI_h": type_vih_constants,
    "VII_h": type_viih_constants,
}


@pytest.mark.parametrize("label", tuple(_SUPPORTED))
@pytest.mark.parametrize("branch", ("principal", "supplementary"))
def test_fb55_quantization_metadata_fields_are_consistent(
    label: str,
    branch: str,
) -> None:
    structure = _SUPPORTED[label]()
    meta = quantise_class_b_mode(structure, eigenvalue=0.5, branch=branch)
    assert meta["type_label"] == label
    assert meta["branch"] == branch
    assert meta["spectrum_kind"] == "continuous"
    assert meta["laplacian_eigenvalue"] == pytest.approx(-0.5)
    assert meta["effective_eigenvalue"] == pytest.approx(0.5)
    assert meta["base_wavenumber"] ** 2 == pytest.approx(meta["base_wavenumber_sq"])
    assert meta["quantised_label"].startswith(f"{label}:{branch}:")
    expected_twist = (
        structure.a_twist ** 2
        if label == "V"
        else structure.a_twist ** 2 / (1.0 + abs(structure.h_parameter))
    )
    assert meta["twist_offset"] == pytest.approx(expected_twist)


@pytest.mark.parametrize("label", tuple(_SUPPORTED))
def test_fb55_base_wavenumber_tracks_twist_offset(label: str) -> None:
    structure = _SUPPORTED[label]()
    meta = quantise_class_b_mode(structure, eigenvalue=0.9)
    expected = max(0.9 - float(meta["twist_offset"]), 0.0)
    assert meta["base_wavenumber_sq"] == pytest.approx(expected)
    assert meta["base_wavenumber"] >= 0.0


@pytest.mark.parametrize(
    "structure",
    (
        type_i_constants(),
        type_ii_constants(),
        type_vii0_constants(),
        type_viii_constants(),
    ),
)
def test_fb55_unsupported_types_raise(structure) -> None:
    with pytest.raises(ValueError, match="supports only"):
        quantise_class_b_mode(structure, eigenvalue=0.5)


def test_fb55_non_positive_eigenvalue_raises() -> None:
    with pytest.raises(ValueError, match="positive"):
        quantise_class_b_mode(type_v_constants(), eigenvalue=0.0)


def test_fb55_invalid_branch_raises() -> None:
    with pytest.raises(ValueError, match="branch"):
        quantise_class_b_mode(type_v_constants(), eigenvalue=0.5, branch="bad")
