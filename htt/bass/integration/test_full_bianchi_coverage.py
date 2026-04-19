"""FB-6 skeleton regression harness for full Bianchi coverage.

This module is intentionally a skeleton-only plant for the first FB-6
rotation. It commits the future 22-configuration regression matrix and
the named continuity-limit tuples while leaving the tests skipped until
the actual FB-6 implementation sessions land.

The explicit 22-row configuration table mirrors the 11-type registry in
``bass.background.bianchi_types`` but is written out flat so the future
coverage surface is reviewable without reconstructing a nested product.
Later FB-6 rotations extend this same module with the continuity-limit
and literature-oracle parametrizations.
"""
from __future__ import annotations

from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[3]
_FB6_FIXTURE_ROOT = _REPO_ROOT / "tests" / "fixtures" / "fb6"


FB61_CONFIGURATION_CASES = [
    pytest.param("I", "orthogonal", "type_i_orthogonal", id="I-orthogonal"),
    pytest.param("I", "tilted", "type_i_tilted", id="I-tilted"),
    pytest.param("II", "orthogonal", "type_ii_orthogonal", id="II-orthogonal"),
    pytest.param("II", "tilted", "type_ii_tilted", id="II-tilted"),
    pytest.param("III", "orthogonal", "type_iii_orthogonal", id="III-orthogonal"),
    pytest.param("III", "tilted", "type_iii_tilted", id="III-tilted"),
    pytest.param("IV", "orthogonal", "type_iv_orthogonal", id="IV-orthogonal"),
    pytest.param("IV", "tilted", "type_iv_tilted", id="IV-tilted"),
    pytest.param("V", "orthogonal", "type_v_orthogonal", id="V-orthogonal"),
    pytest.param("V", "tilted", "type_v_tilted", id="V-tilted"),
    pytest.param("VI_0", "orthogonal", "type_vi0_orthogonal", id="VI_0-orthogonal"),
    pytest.param("VI_0", "tilted", "type_vi0_tilted", id="VI_0-tilted"),
    pytest.param("VI_h", "orthogonal", "type_vih_orthogonal", id="VI_h-orthogonal"),
    pytest.param("VI_h", "tilted", "type_vih_tilted", id="VI_h-tilted"),
    pytest.param("VII_0", "orthogonal", "type_vii0_orthogonal", id="VII_0-orthogonal"),
    pytest.param("VII_0", "tilted", "type_vii0_tilted", id="VII_0-tilted"),
    pytest.param("VII_h", "orthogonal", "type_viih_orthogonal", id="VII_h-orthogonal"),
    pytest.param("VII_h", "tilted", "type_viih_tilted", id="VII_h-tilted"),
    pytest.param("VIII", "orthogonal", "type_viii_orthogonal", id="VIII-orthogonal"),
    pytest.param("VIII", "tilted", "type_viii_tilted", id="VIII-tilted"),
    pytest.param("IX", "orthogonal", "type_ix_orthogonal", id="IX-orthogonal"),
    pytest.param("IX", "tilted", "type_ix_tilted", id="IX-tilted"),
]


FB62_CONTINUITY_LIMIT_CASES = [
    pytest.param("VII_h", "VII_0", "h", "0+", id="VII_h-to-VII_0-h->0+"),
    pytest.param("VI_h", "III", "h", "-1", id="VI_h-to-III-h->-1"),
    pytest.param("VII_0", "I", "n", "0", id="VII_0-to-I-n->0"),
    pytest.param("V", "I", "a_twist", "0", id="V-to-I-a->0"),
    pytest.param("IX", "IX_BKL_isotropic", "n", "0", id="IX-to-BKL-isotropic-n->0"),
]


FB63_ORACLE_FIXTURE_CASES = [
    pytest.param(
        "pc2009_fig1_vii_h_vector_temperature_grid",
        _FB6_FIXTURE_ROOT / "pontzen_challinor_2009_fig1_vii_h_vector_temperature_grid.npz",
        "literature",
        id="pc2009-fig1-vii_h-vector",
    ),
    pytest.param(
        "pc2009_fig3_vii_h_regular_mode_temperature_grid",
        _FB6_FIXTURE_ROOT / "pontzen_challinor_2009_fig3_vii_h_regular_mode_temperature_grid.npz",
        "literature",
        id="pc2009-fig3-vii_h-regular-mode",
    ),
    pytest.param(
        "pc2009_sec4_ix_closed_quadrupole_grid",
        _FB6_FIXTURE_ROOT / "pontzen_challinor_2009_sec4_ix_closed_quadrupole_grid.npz",
        "literature",
        id="pc2009-sec4-ix-quadrupole",
    ),
    pytest.param(
        "pc2009_vii_h_off_diagonal_ctt",
        _FB6_FIXTURE_ROOT / "pontzen_challinor_2009_vii_h_off_diagonal_ctt.npz",
        "literature",
        id="pc2009-vii_h-offdiag-ctt",
    ),
    pytest.param(
        "pc2009_ix_off_diagonal_ctt",
        _FB6_FIXTURE_ROOT / "pontzen_challinor_2009_ix_off_diagonal_ctt.npz",
        "literature",
        id="pc2009-ix-offdiag-ctt",
    ),
    pytest.param(
        "camb_planck2018_type_i_flrw_limit",
        _REPO_ROOT / "data" / "camb_ref_planck2018.npz",
        "camb",
        id="camb-type-i-flrw-limit",
    ),
    pytest.param(
        "camb_planck2018_type_v_flrw_limit",
        _REPO_ROOT / "data" / "camb_ref_planck2018.npz",
        "camb",
        id="camb-type-v-flrw-limit",
    ),
    pytest.param(
        "camb_planck2018_type_vii0_flrw_limit",
        _REPO_ROOT / "data" / "camb_ref_planck2018.npz",
        "camb",
        id="camb-type-vii0-flrw-limit",
    ),
    pytest.param(
        "camb_planck2018_type_viih_h0_limit",
        _REPO_ROOT / "data" / "camb_ref_planck2018.npz",
        "camb",
        id="camb-type-viih-h0-limit",
    ),
    pytest.param(
        "camb_planck2018_type_ix_bkl_limit",
        _REPO_ROOT / "data" / "camb_ref_planck2018.npz",
        "camb",
        id="camb-type-ix-bkl-limit",
    ),
]


@pytest.mark.parametrize(
    ("type_label", "tilt_state", "fixture_key"),
    FB61_CONFIGURATION_CASES,
)
def test_fb61_full_bianchi_configuration_matrix(
    type_label: str,
    tilt_state: str,
    fixture_key: str,
) -> None:
    _ = (type_label, tilt_state, fixture_key)
    pytest.skip(reason="pending FB-6.1 implementation — skeleton only")
    raise NotImplementedError("FB-6.1")


@pytest.mark.parametrize(
    ("source_type", "target_type", "limit_parameter", "limit_value"),
    FB62_CONTINUITY_LIMIT_CASES,
)
def test_fb62_cross_type_continuity_limits(
    source_type: str,
    target_type: str,
    limit_parameter: str,
    limit_value: str,
) -> None:
    _ = (source_type, target_type, limit_parameter, limit_value)
    pytest.skip(reason="pending FB-6.2 implementation — skeleton only")
    raise NotImplementedError("FB-6.2")


@pytest.mark.parametrize(
    ("oracle_name", "fixture_path", "oracle_family"),
    FB63_ORACLE_FIXTURE_CASES,
)
def test_fb63_literature_and_camb_oracle_fixtures(
    oracle_name: str,
    fixture_path: Path,
    oracle_family: str,
) -> None:
    _ = (oracle_name, fixture_path, oracle_family)
    pytest.skip(reason="pending FB-6.3 implementation — skeleton only")
    raise NotImplementedError("FB-6.3")
