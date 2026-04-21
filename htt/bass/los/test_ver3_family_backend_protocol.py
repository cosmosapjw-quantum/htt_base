from __future__ import annotations

import pytest

from bass.background import get_family_spec
from bass.los import (
    NativeLabelCard,
    SeedRequest,
    build_backend,
)


ALL_FAMILIES = ["FLRW", "I", "II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX"]


@pytest.mark.parametrize("family", ALL_FAMILIES)
def test_all_families_build_backend_contract(family: str) -> None:
    backend = build_backend(
        get_family_spec(family),
        truncation={"ell_max": 6, "k_max": 0.2},
    )
    metadata = backend.required_metadata()
    assert metadata["release_status"] == "backend-contract-complete"
    assert metadata["preferred_backend"] == get_family_spec(family).preferred_backend
    assert metadata["orthogonal_global_tilt_local_boost_split"] == "frozen"


def test_vi_h_label_translator_roundtrip_preserves_h_and_branch() -> None:
    backend = build_backend(
        get_family_spec("VI_h", h=-2.0),
        truncation={"ell_max": 4},
    )
    native = (
        NativeLabelCard(
            family="VI_h",
            native_label="mu_VIh_0",
            ell=2,
            m=1,
            sector="temperature",
            branch_flag="negative_h_branch",
            h_parameter=-2.0,
        ),
    )
    storage = backend.label_translator(native)
    assert storage[0]["h_parameter"] == pytest.approx(-2.0)
    assert storage[0]["branch_flag"] == "negative_h_branch"
    restored = backend.inverse_label_translator(storage)
    assert restored[0].h_parameter == pytest.approx(-2.0)
    assert restored[0].branch_flag == "negative_h_branch"
    assert restored[0].chart == "class_b_negative_h_chart"


def test_iv_label_translator_roundtrip_preserves_coordinate_order() -> None:
    backend = build_backend(
        get_family_spec("IV"),
        truncation={"ell_max": 4},
    )
    native = (
        NativeLabelCard(
            family="IV",
            native_label="mu_solv_0",
            ell=1,
            m=0,
            sector="temperature",
            coordinate_order=("x_noncompact", "y_shear", "z_twist"),
        ),
    )
    storage = backend.label_translator(native)
    assert storage[0]["coordinate_order"] == ("x_noncompact", "y_shear", "z_twist")
    restored = backend.inverse_label_translator(storage)
    assert restored[0].coordinate_order == ("x_noncompact", "y_shear", "z_twist")
    assert restored[0].branch_flag == "intrinsic"
    assert restored[0].chart == "solvable_group_chart"


def test_vi0_label_translator_roundtrip_preserves_directional_tag() -> None:
    backend = build_backend(get_family_spec("VI_0"), truncation={"ell_max": 4})
    native = (
        NativeLabelCard(
            family="VI_0",
            native_label="mu_VI0_0",
            ell=2,
            m=0,
            sector="temperature",
            directional_tag="mixed_sign_axes",
        ),
    )
    storage = backend.label_translator(native)
    assert storage[0]["directional_tag"] == "mixed_sign_axes"
    restored = backend.inverse_label_translator(storage)
    assert restored[0].directional_tag == "mixed_sign_axes"
    assert restored[0].branch_flag == "intrinsic"
    assert restored[0].chart == "class_a_solvable_intrinsic"


def test_intrinsic_family_seed_factory_rejects_flrw_like_regular() -> None:
    backend = build_backend(get_family_spec("II"), truncation={"ell_max": 4})
    with pytest.raises(ValueError, match="not allowed"):
        backend.seed_factory(
            SeedRequest(branch="intrinsic", seed_mode="flrw_like_regular")
        )


def test_isotropic_anchor_seed_factory_allows_regular_seed() -> None:
    backend = build_backend(get_family_spec("VII_0"), truncation={"ell_max": 4})
    seed = backend.seed_factory(
        SeedRequest(branch="orthogonal", seed_mode="flrw_like_regular", amplitude_reference=2.5)
    )
    assert seed.family == "VII_0"
    assert seed.seed_mode == "flrw_like_regular"
    assert seed.normalization["amp_ref"] == pytest.approx(2.5)


def test_operator_factory_maps_named_family_to_expected_kernel() -> None:
    backend = build_backend(get_family_spec("IX"), truncation={"ell_max": 6})
    ops = backend.operator_factory({"branch": "orthogonal", "state_tag": "named_branch"})
    assert ops.operator_kernel_family == "class_a_compact_matrix_approx"
    assert ops.backend_name == "wigner_d_compact_backend"
    assert ops.release_status == "backend-contract-complete"


def test_backend_residuals_reports_roundtrip_zero_when_translator_is_consistent() -> None:
    backend = build_backend(get_family_spec("VIII"), truncation={"ell_max": 4})
    native = (
        NativeLabelCard(
            family="VIII",
            native_label="mu_sl2r_0",
            ell=3,
            m=-1,
            sector="temperature",
            branch_flag="noncompact_branch",
        ),
    )
    residuals = backend.backend_residuals(native)
    assert residuals["translator_roundtrip_residual"] == 0
