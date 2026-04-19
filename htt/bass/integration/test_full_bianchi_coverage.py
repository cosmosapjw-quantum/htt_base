"""FB-6.1 skeleton regression harness for full Bianchi coverage.

This module is intentionally a skeleton-only plant for the first FB-6
rotation. It commits the future 22-configuration regression matrix while
leaving the test skipped until the actual FB-6.1 implementation session
lands.

The explicit 22-row configuration table mirrors the 11-type registry in
``bass.background.bianchi_types`` but is written out flat so the future
coverage surface is reviewable without reconstructing a nested product.
Later FB-6 rotations extend this same module with the continuity-limit
and literature-oracle parametrizations.
"""
from __future__ import annotations

import pytest


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
