"""Regression anchors for ``htt.core.evidence_models_R03a``.

The R03a module (976L) is the actively-developed primary evidence framework;
the sibling ``evidence_models.py`` carries a ``DEPRECATED`` header. The two
implementations share physics and should produce bit-identical results on
the FLRW_tilt posterior — this file pins that consistency, the audit
output, and R03a-specific utilities (bass_shear_to_D2 sentinel, AniCLASS
comparison table).

Scope
-----
* Cross-consistency: R03a ≡ deprecated evidence_models.py on the CLAUDE.md
  §5 anchors (ln B, β_mean, F_Bayes).
* ``audit_inactive_parameters()`` output frozen (inactive params,
  duplicate models, equivalence classes).
* ``bass_shear_to_D2`` sentinel at Σ² ∈ {1e-8, 1e-9} and
  ``bass_vs_aniclass_comparison`` scaling sanity.
* ``ALL_MODELS`` registry (16 entries = 15 evidence models + FLRW null).
"""
from __future__ import annotations

import pytest

from htt.core import evidence_models as DEPR
from htt.core import evidence_models_R03a as R03a


# ═══════════════════════════════════════════════════════════════════════
# Part 1 — Cross-consistency R03a vs deprecated (bit-identical)
# ═══════════════════════════════════════════════════════════════════════
def test_R03a_flrw_log_evidence_matches_deprecated():
    """FLRW evidence identical across the two implementations."""
    assert R03a.FLRW().log_evidence() == DEPR.FLRW().log_evidence()


def test_R03a_flrw_tilt_lnZ_matches_deprecated():
    """FLRW_tilt log-evidence (quadrature) identical."""
    r_a = R03a.FLRW_tilt().log_evidence_quadrature(n_points=10000)["lnZ"]
    r_d = DEPR.FLRW_tilt().log_evidence_quadrature(n_points=10000)["lnZ"]
    assert r_a == r_d


def test_R03a_flrw_tilt_beta_mean_matches_deprecated():
    """Posterior-mean β identical across implementations."""
    r_a = R03a.FLRW_tilt().log_evidence_quadrature(n_points=10000)["beta_mean"]
    r_d = DEPR.FLRW_tilt().log_evidence_quadrature(n_points=10000)["beta_mean"]
    assert r_a == r_d


def test_R03a_pins_same_claude_md_anchors():
    """R03a also satisfies the CLAUDE.md §5 production anchors bit-exact."""
    res = R03a.FLRW_tilt().log_evidence_quadrature(n_points=10000)
    lnZ_flrw = R03a.FLRW().log_evidence()
    assert res["lnZ"] - lnZ_flrw == pytest.approx(26.3966094015, abs=1e-9)
    assert res["beta_mean"]       == pytest.approx(1.3597868670e-03, abs=1e-12)


# ═══════════════════════════════════════════════════════════════════════
# Part 2 — Model registry + identifiability audit
# ═══════════════════════════════════════════════════════════════════════
_EXPECTED_ALL_MODELS = {
    "FLRW", "FLRW_tilt",
    "BI_orth", "BVII0_orth", "BII_orth", "BVI0_orth",
    "BVIII_orth", "BIX_orth", "BVIIh_orth", "BVIIh_orth_grow",
    "BI_tilt", "BV_tilt", "BIII_tilt", "BIX_tilt",
    "BVIIh_tilt", "BVIIh_tilt_grow",
}


def test_R03a_ALL_MODELS_registry_pinned():
    """Registry contains exactly 16 named models (1 null + 1 tilted FLRW + 14 Bianchi)."""
    assert set(R03a.ALL_MODELS.keys()) == _EXPECTED_ALL_MODELS
    assert len(R03a.ALL_MODELS) == 16


def test_R03a_ALL_MODELS_matches_deprecated():
    """The deprecated module should register the same 15 evidence-ranked models
    (its registry omits FLRW as 'null' but contains FLRW_tilt + 14 Bianchi)."""
    # R03a adds FLRW to the ranked registry; deprecated module also includes it.
    assert set(DEPR.ALL_MODELS.keys()) == _EXPECTED_ALL_MODELS


_EXPECTED_INACTIVE = {
    "BII_orth": ["n1"],
    "BVI0_orth": ["a1"],
    "BVIII_orth": ["Omega_k"],
    "BIX_orth": ["Omega_k"],
    "BIII_tilt": ["Omega_k"],
    "BIX_tilt": ["Omega_k"],
}
_EXPECTED_DUPLICATES = {
    "BVII0_orth": "BI_orth",
    "BII_orth":   "BI_orth",
    "BVI0_orth":  "BI_orth",
    "BVIII_orth": "BI_orth",
    "BIX_orth":   "BI_orth",
    "BIII_tilt":  "BI_tilt",
    "BIX_tilt":   "BI_tilt",
}
_EXPECTED_EQUIV_CLASSES = {
    "orth_1D":   {"BI_orth", "BVII0_orth", "BII_orth", "BVI0_orth",
                  "BVIII_orth", "BIX_orth"},
    "tilt_flat": {"BI_tilt", "BIII_tilt", "BIX_tilt"},
}


def test_audit_inactive_parameters_output_pinned():
    """``audit_inactive_parameters()`` output is a stable CA-07/CA-08 anchor."""
    report = R03a.audit_inactive_parameters()
    assert report["inactive_parameters"] == _EXPECTED_INACTIVE


def test_audit_duplicate_models_pinned():
    """Identifiability audit catches that BII/BVI0/BVIII/BIX orth all collapse
    onto BI_orth (identical Σ² posteriors under this likelihood)."""
    report = R03a.audit_inactive_parameters()
    assert report["duplicate_models"] == _EXPECTED_DUPLICATES


def test_audit_equivalence_classes_pinned():
    """Non-trivial equivalence classes (|class| > 1) pinned."""
    report = R03a.audit_inactive_parameters()
    classes = {k: set(v) for k, v in report["equivalence_classes"].items()}
    assert classes == _EXPECTED_EQUIV_CLASSES


def test_audit_matches_deprecated_module():
    """Both modules must report the same identifiability audit structure."""
    r_a = R03a.audit_inactive_parameters()
    r_d = DEPR.audit_inactive_parameters()
    assert r_a["inactive_parameters"] == r_d["inactive_parameters"]
    assert r_a["duplicate_models"]    == r_d["duplicate_models"]
    assert {k: set(v) for k, v in r_a["equivalence_classes"].items()} == \
           {k: set(v) for k, v in r_d["equivalence_classes"].items()}


# ═══════════════════════════════════════════════════════════════════════
# Part 3 — R03a-specific: BASS shear sentinel + AniCLASS comparison
# ═══════════════════════════════════════════════════════════════════════
def test_bass_shear_to_D2_sentinel_at_1em8():
    """Route B sentinel from R03a side: D_2(Σ²=1e-8) ≈ 0.2262 μK².

    Note the value differs from the bass_rs Route B lookup
    `D_2(Σ²=1e-8) = 0.1741 μK²` (ROUTE_B_D2_AT_SIGMA2_1EM8) because the
    R03a `bass_shear_to_D2` uses the AniCLASS-calibrated transfer
    T₂_decay=2.75e4 with Σ²→σ/H mapping, not the Michaelis-Menten fit.
    Both coexist by design; the comparison is exercised by
    `bass_vs_aniclass_comparison`.
    """
    assert R03a.bass_shear_to_D2(1e-8) == pytest.approx(
        2.261544546812e-01, abs=1e-12
    )


def test_bass_shear_to_D2_sentinel_at_1em9():
    """D_2(Σ²=1e-9) bit-identical — second sentinel away from 1e-8."""
    assert R03a.bass_shear_to_D2(1e-9) == pytest.approx(
        2.508448254918e-02, abs=1e-14
    )


def test_bass_shear_to_D2_mild_subquadratic():
    """D_2 scaling between Σ²=1e-8 and Σ²=1e-9 reflects the f₂(x) interpolation.

    With x = √h/√Ω_K at Ω_K = 7e-4, σ/H = √(6 Σ²), the f₂ vector-mode
    interpolator rises steeply across x ∈ [0.1, 0.3] so the scaling is
    slightly sub-quadratic (measured ratio ≈ 9.02 vs naive 10.0). Pin the
    ratio here — if f₂(x) is retuned, this test fires.
    """
    d2_8 = R03a.bass_shear_to_D2(1e-8)
    d2_9 = R03a.bass_shear_to_D2(1e-9)
    assert d2_8 / d2_9 == pytest.approx(9.0157113760, abs=1e-8)


def test_bass_vs_aniclass_comparison_schema():
    """Comparison dict schema is a stable diagnostic anchor."""
    out = R03a.bass_vs_aniclass_comparison(1e-8)
    assert set(out.keys()) == {
        "Sigma2", "D2_bass_uK2", "D2_aniclass_uK2",
        "ratio_ani_over_bass", "log10_ratio",
        "bass_valid", "note",
    }
    assert out["Sigma2"] == 1e-8
    assert out["D2_bass_uK2"] == pytest.approx(0.2262, abs=5e-4)
    # AniCLASS amplitude calibration is >14 orders of magnitude different —
    # pin the log10 ratio at a tight tolerance to catch any accidental
    # factor-10 drift in either calibration.
    assert float(out["log10_ratio"]) == pytest.approx(14.199, abs=1e-2)
    assert out["bass_valid"] is True


# ═══════════════════════════════════════════════════════════════════════
# Part 4 — ObsData constants pinned (shared between R03a and deprecated)
# ═══════════════════════════════════════════════════════════════════════
def test_obsdata_default_values_pinned():
    """Default ObsData fixtures pin the Planck PR3 + scenario observations."""
    obs = R03a.ObsData()
    # Planck PR3 Commander
    assert obs.D2_obs == 225.9
    assert obs.D3_obs == 936.9
    # Ferreira-Quartin kinematic dipole upper limit
    assert obs.e1_FQ_UL == 1.358e-3
    # CatWISE 2020 (Secrest et al.)
    assert obs.e1_CW == 1.476e-3
    # Radio (NVSS+RACS)
    assert obs.e1_rad == 3.296e-3
    # CF4 bulk flow
    assert obs.b_CF4 == 1.334e-3
    # Saadeh vorticity (internal convention omH = (√2/3)(ω/H))
    assert obs.omH_UL == 2.45e-11


def test_R03a_T0_uses_canonical_fixsen_value():
    """R03a T0 constant must match CLAUDE.md §5 canonical 2.72548 K."""
    assert R03a.T0 == 2.72548
    assert R03a.T0_UK == 2.72548e6
