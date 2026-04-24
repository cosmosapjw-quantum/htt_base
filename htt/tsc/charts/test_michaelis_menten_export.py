"""Tests for :mod:`tsc.charts.michaelis_menten_export` (TSC-05)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from tsc.charts.michaelis_menten_export import (
    MichaelisMentenExport,
    ROUTE_B_C1,
    ROUTE_B_C2,
    ROUTE_B_D2_AT_SIGMA2_1EM8,
    SCHEMA_VERSION,
    T_CMB_K_MIRROR,
    assert_mirror_matches_bass_ssot,
    d2_route_b,
    export_as_dict,
    export_as_json,
    michaelis_menten_coefficients,
)


# ---------------------------------------------------------------------------
# §1 - SSOT literal sanity
# ---------------------------------------------------------------------------


class TestRouteBLiterals:
    def test_C1_is_1_753e7(self):
        assert ROUTE_B_C1 == pytest.approx(1.753e7, rel=0.0)

    def test_C2_is_6_825e5(self):
        assert ROUTE_B_C2 == pytest.approx(6.825e5, rel=0.0)

    def test_sentinel_derivation_is_exact_from_literals(self):
        expected = 1.753e7 * 1.0e-8 / (1.0 + 6.825e5 * 1.0e-8)
        assert ROUTE_B_D2_AT_SIGMA2_1EM8 == pytest.approx(
            expected, rel=0.0,
        )

    def test_sentinel_is_0_17408_microK2(self):
        # Numerically, 1.753e-1 / (1 + 6.825e-3) ≈ 0.17411...
        assert ROUTE_B_D2_AT_SIGMA2_1EM8 == pytest.approx(
            0.17411, abs=1e-4,
        )

    def test_T_CMB_is_fixsen(self):
        assert T_CMB_K_MIRROR == 2.72548

    def test_schema_version_is_tag(self):
        assert SCHEMA_VERSION == "TSC-05/v1"


# ---------------------------------------------------------------------------
# §2 - Evaluator
# ---------------------------------------------------------------------------


class TestD2RouteB:
    def test_at_zero_is_zero(self):
        assert d2_route_b(0.0) == 0.0

    def test_at_sigma2_1em8_matches_sentinel(self):
        assert d2_route_b(1.0e-8) == pytest.approx(
            ROUTE_B_D2_AT_SIGMA2_1EM8, rel=0.0,
        )

    def test_scalar_input_returns_float(self):
        out = d2_route_b(1.0e-9)
        assert isinstance(out, float)

    def test_array_input_returns_ndarray(self):
        out = d2_route_b(np.array([0.0, 1.0e-9, 1.0e-8]))
        assert isinstance(out, np.ndarray)
        assert out.shape == (3,)

    def test_array_matches_scalar_elementwise(self):
        s = np.array([1.0e-10, 5.0e-9, 1.0e-8, 2.5e-8])
        arr_out = d2_route_b(s)
        for i, x in enumerate(s):
            assert arr_out[i] == pytest.approx(d2_route_b(float(x)), rel=0.0)

    def test_monotonic_in_sigma_sq(self):
        s = np.logspace(-12, -5, 30)
        y = d2_route_b(s)
        assert np.all(np.diff(y) >= 0.0)

    def test_asymptote_at_large_sigma(self):
        # As Sigma^2 -> infinity: D_2 -> C_1 / C_2
        y = d2_route_b(1.0e6)
        assert y == pytest.approx(ROUTE_B_C1 / ROUTE_B_C2, rel=1e-3)

    def test_rejects_negative_sigma(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            d2_route_b(-1e-10)

    def test_rejects_non_finite(self):
        with pytest.raises(ValueError, match="finite"):
            d2_route_b(float("nan"))

    def test_rejects_negative_C1(self):
        with pytest.raises(ValueError, match="C1 must be > 0"):
            d2_route_b(1e-8, C1=-1.0, C2=ROUTE_B_C2)

    def test_rejects_negative_C2(self):
        with pytest.raises(ValueError, match="C2 must be > 0"):
            d2_route_b(1e-8, C1=ROUTE_B_C1, C2=0.0)

    def test_override_coefficients_accepted(self):
        out = d2_route_b(1e-8, C1=2.0e7, C2=5.0e5)
        expected = 2.0e7 * 1e-8 / (1.0 + 5.0e5 * 1e-8)
        assert out == pytest.approx(expected, rel=1e-14)


# ---------------------------------------------------------------------------
# §3 - Export constructor + dataclass
# ---------------------------------------------------------------------------


class TestMichaelisMentenExport:
    def test_constructor_echoes_frozen_literals(self):
        e = michaelis_menten_coefficients()
        assert e.C1 == ROUTE_B_C1
        assert e.C2 == ROUTE_B_C2
        assert e.D2_at_sigma2_1em8 == ROUTE_B_D2_AT_SIGMA2_1EM8
        assert e.T_CMB_K == T_CMB_K_MIRROR
        assert e.schema_version == SCHEMA_VERSION

    def test_dataclass_is_frozen(self):
        e = michaelis_menten_coefficients()
        with pytest.raises(Exception):
            e.C1 = 0.0  # type: ignore[misc]

    def test_provenance_round_trip(self):
        e = michaelis_menten_coefficients(
            provenance={"commit": "abc123", "stage": "W7D3"},
        )
        assert e.provenance["commit"] == "abc123"
        assert e.provenance["stage"] == "W7D3"


# ---------------------------------------------------------------------------
# §4 - JSON schema freeze (TSC-05 hero gate #3)
# ---------------------------------------------------------------------------


class TestJsonSchemaFreeze:
    def test_dict_has_expected_top_level_keys(self):
        d = export_as_dict()
        assert set(d.keys()) == {
            "schema_version", "ssot_source", "coefficients",
            "sentinel", "T_CMB_K", "provenance",
        }

    def test_coefficients_sub_schema(self):
        d = export_as_dict()
        assert set(d["coefficients"].keys()) == {"C1", "C2"}
        assert isinstance(d["coefficients"]["C1"], float)
        assert isinstance(d["coefficients"]["C2"], float)

    def test_sentinel_sub_schema(self):
        d = export_as_dict()
        assert set(d["sentinel"].keys()) == {"sigma_sq", "D2_microK_sq"}
        assert d["sentinel"]["sigma_sq"] == 1.0e-8

    def test_schema_version_tag_in_json(self):
        s = export_as_json()
        parsed = json.loads(s)
        assert parsed["schema_version"] == "TSC-05/v1"

    def test_json_round_trip(self, tmp_path: Path):
        path = tmp_path / "mm.json"
        s1 = export_as_json(path=path)
        s2 = path.read_text(encoding="utf-8")
        assert s1 == s2
        parsed = json.loads(s2)
        assert parsed["coefficients"]["C1"] == ROUTE_B_C1

    def test_json_keys_sorted(self):
        s = export_as_json()
        parsed = json.loads(s)
        # sort_keys=True produces deterministic ordering
        assert list(parsed["coefficients"].keys()) == ["C1", "C2"]


# ---------------------------------------------------------------------------
# §5 - Zero-drift regression (TSC-05 hero gate #2)
# ---------------------------------------------------------------------------


class TestZeroDriftFromBassSsot:
    def test_tsc_mm_constants_match_bass_ssot(self):
        """TSC-05 hero anchor: zero drift from bass.spectrum.cl_assembly."""
        # rtol=0.0 → bit-identity; any drift fires AssertionError.
        assert_mirror_matches_bass_ssot(rtol=0.0)

    def test_C1_matches_bass_literal(self):
        from bass.spectrum.cl_assembly import ROUTE_B_C1 as bass_C1
        assert ROUTE_B_C1 == bass_C1

    def test_C2_matches_bass_literal(self):
        from bass.spectrum.cl_assembly import ROUTE_B_C2 as bass_C2
        assert ROUTE_B_C2 == bass_C2

    def test_sentinel_matches_bass_literal(self):
        from bass.spectrum.cl_assembly import (
            ROUTE_B_D2_AT_SIGMA2_1EM8 as bass_D2,
        )
        assert ROUTE_B_D2_AT_SIGMA2_1EM8 == bass_D2

    def test_T_CMB_matches_planck_mes_bounds(self):
        from bass.observational.planck_mes_bounds import T_CMB_K as bass_T
        assert T_CMB_K_MIRROR == bass_T

    def test_drift_would_raise(self, monkeypatch):
        # Simulate bass-side drift and confirm the anchor fires.
        import bass.spectrum.cl_assembly as cl
        monkeypatch.setattr(cl, "ROUTE_B_C1", 2.000e7)
        with pytest.raises(AssertionError, match="drift"):
            assert_mirror_matches_bass_ssot(rtol=0.0)
