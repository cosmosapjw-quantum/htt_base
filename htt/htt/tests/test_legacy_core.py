"""
htt/tests/test_legacy_core.py — HTT Legacy Core Tests
========================================================
C-05 deliverable. Tests:
  1. HPD intervals: normal, skewed, bimodal weighted samples
  2. T_eff quadrupole mapping
  3. MES hierarchy B_σ > B_ω ≥ B_u̇
  4. SSOT constants
  5. Conversion roundtrips
  6. PipelineConfig
  7. Bounds consistency
  8. Evidence model structure
"""
import pytest
import numpy as np

SYNTHETIC_BETA = 2.0e-4
SYNTHETIC_INPUT_MODE = "synthetic"

# ═══════════════════════════════════════════════════════════
# 1. HPD intervals
# ═══════════════════════════════════════════════════════════

class TestWeightedHPD:
    """weighted_hpd must find shortest credible interval."""

    def test_normal_symmetric(self):
        """Normal distribution: HPD should be symmetric around mean."""
        from htt.core.departure_posteriors import weighted_hpd
        rng = np.random.default_rng(42)
        vals = rng.normal(5.0, 1.0, 5000)
        w = np.ones_like(vals)
        lo, hi = weighted_hpd(vals, w, 0.68)
        # For N(5,1), 68% HPD ≈ [4, 6]
        assert lo == pytest.approx(4.0, abs=0.15)
        assert hi == pytest.approx(6.0, abs=0.15)
        # Interval should contain the mean
        assert lo < 5.0 < hi

    def test_skewed_distribution(self):
        """Skewed distribution: HPD should be shorter than equal-tail."""
        from htt.core.departure_posteriors import weighted_hpd, weighted_quantile
        rng = np.random.default_rng(42)
        vals = rng.lognormal(0, 0.5, 10000)
        w = np.ones_like(vals)
        lo_hpd, hi_hpd = weighted_hpd(vals, w, 0.68)
        # Equal-tail interval
        lo_eq = weighted_quantile(vals, 0.16, w)
        hi_eq = weighted_quantile(vals, 0.84, w)
        # HPD should be narrower than equal-tail for skewed distributions
        hpd_width = hi_hpd - lo_hpd
        eq_width = hi_eq - lo_eq
        assert hpd_width <= eq_width * 1.05  # allow 5% tolerance

    def test_bimodal_weighted(self):
        """Bimodal: HPD should find the mode with more weight."""
        from htt.core.departure_posteriors import weighted_hpd
        rng = np.random.default_rng(42)
        # Mode 1: centered at 1, low weight
        v1 = rng.normal(1.0, 0.1, 200)
        w1 = np.ones(200) * 0.2
        # Mode 2: centered at 5, high weight
        v2 = rng.normal(5.0, 0.1, 800)
        w2 = np.ones(800) * 1.0
        vals = np.concatenate([v1, v2])
        weights = np.concatenate([w1, w2])
        lo, hi = weighted_hpd(vals, weights, 0.68)
        # Should capture the dominant mode near 5
        assert lo > 3.0, f"HPD lower bound {lo} should be > 3 (near mode 2)"
        assert hi < 6.0

    def test_uniform_samples(self):
        """Uniform: 68% HPD should span ~68% of the range."""
        from htt.core.departure_posteriors import weighted_hpd
        vals = np.linspace(0, 10, 1000)
        w = np.ones(1000)
        lo, hi = weighted_hpd(vals, w, 0.68)
        width = hi - lo
        assert width == pytest.approx(6.8, abs=0.2)

    def test_95_wider_than_68(self):
        """95% interval must contain the 68% interval."""
        from htt.core.departure_posteriors import weighted_hpd
        rng = np.random.default_rng(42)
        vals = rng.normal(0, 1, 5000)
        w = np.ones(5000)
        lo68, hi68 = weighted_hpd(vals, w, 0.68)
        lo95, hi95 = weighted_hpd(vals, w, 0.95)
        assert lo95 <= lo68
        assert hi95 >= hi68


# ═══════════════════════════════════════════════════════════
# 2. T_eff quadrupole mapping
# ═══════════════════════════════════════════════════════════

class TestTeffQuadrupole:
    """T_eff nonlinear correction structure."""

    def test_nonlinear_correction_exists(self):
        """NonlinearCorrection class should be importable."""
        from htt.core.teff_extended import NonlinearCorrection
        nc = NonlinearCorrection()
        assert hasattr(nc, 'R_sigma')

    def test_R_sigma_at_zero(self):
        """R_σ(ε₁=0) = 1."""
        from htt.core.teff_extended import NonlinearCorrection
        nc = NonlinearCorrection()
        R = nc.R_sigma(0.0)
        assert R == pytest.approx(1.0, abs=1e-10)

    def test_R_sigma_positive_correction(self):
        """R_σ > 1 for ε₁ > 0."""
        from htt.core.teff_extended import NonlinearCorrection
        nc = NonlinearCorrection()
        R = nc.R_sigma(SYNTHETIC_BETA)
        assert R > 1.0


# ═══════════════════════════════════════════════════════════
# 3. MES hierarchy B_σ > B_ω ≥ B_u̇
# ═══════════════════════════════════════════════════════════

class TestMESHierarchy:
    """The MES bound hierarchy must be preserved."""

    def test_hierarchy_at_eps1_kin(self):
        """B_σ > B_ω > B_u̇ at ε₁ = ε₁_kin."""
        from tsc_legacy.htt_core_bounds import B_sigma, B_omega, B_accel
        from htt.core.ssot import C
        e1 = C.eps1_kin
        bs = B_sigma(e1)
        bo = B_omega(e1)
        ba = B_accel(e1)
        assert bs > bo > ba, f"Hierarchy violated: B_σ={bs}, B_ω={bo}, B_u̇={ba}"

    def test_hierarchy_across_range(self):
        """Hierarchy holds for ε₁ from 10⁻⁶ to 10⁻²."""
        from tsc_legacy.htt_core_bounds import B_sigma, B_omega, B_accel
        for e1 in np.geomspace(1e-6, 1e-2, 20):
            bs = B_sigma(e1)
            bo = B_omega(e1)
            ba = B_accel(e1)
            assert bs >= bo >= ba, f"Hierarchy violated at ε₁={e1:.2e}"

    def test_Sig2_max_positive(self):
        """Σ²_max from MES should be positive."""
        from tsc_legacy.htt_core_bounds import Sig2_max_MES
        from htt.core.ssot import C
        s2max = Sig2_max_MES(C.eps1_kin)
        assert s2max > 0

    def test_B_sigma_corrected_ge_B_sigma(self):
        """Corrected bound ≥ linear bound."""
        from tsc_legacy.htt_core_bounds import B_sigma, B_sigma_corrected
        from htt.core.ssot import C
        e1 = C.eps1_kin
        assert B_sigma_corrected(e1) >= B_sigma(e1)


# ═══════════════════════════════════════════════════════════
# 4. SSOT constants
# ═══════════════════════════════════════════════════════════

class TestSSOT:
    """Single Source of Truth constants must match canonical values."""

    def test_eps1_kin(self):
        from htt.core.ssot import C
        assert C.eps1_kin == pytest.approx(1.2336e-3, rel=1e-3)

    def test_Omega_m(self):
        from htt.core.ssot import C
        assert C.Omega_m == pytest.approx(0.3153, rel=1e-4)

    def test_eta_udot(self):
        from htt.core.ssot import C
        assert C.eta_udot == pytest.approx(1/12, rel=1e-10)

    def test_H0(self):
        from htt.core.ssot import C
        assert C.h == pytest.approx(0.6736, rel=1e-4)

    def test_T0(self):
        from htt.core.ssot import C
        assert C.T0_K == pytest.approx(2.72548, rel=1e-4)


# ═══════════════════════════════════════════════════════════
# 5. Conversion roundtrips
# ═══════════════════════════════════════════════════════════

class TestConversions:

    def test_eps_D_roundtrip(self):
        """eps_ell → D_ell → eps_ell should be identity."""
        from htt.core.ssot import eps_ell, D_ell_from_eps, C
        for ell in [2, 3]:
            D = C.D2_obs if ell == 2 else C.D3_obs
            e = eps_ell(D, ell)
            D_rt = D_ell_from_eps(e, ell)
            assert D_rt == pytest.approx(D, rel=1e-10)

    def test_sigma_H_roundtrip(self):
        """sigma_H_from_Sig2 → Sig2_from_sigmaH should roundtrip."""
        from htt.core.ssot import sigma_H_from_Sig2, Sig2_from_sigmaH
        Sig2 = 1.5e-6
        sH = sigma_H_from_Sig2(Sig2)
        Sig2_rt = Sig2_from_sigmaH(sH)
        assert Sig2_rt == pytest.approx(Sig2, rel=1e-12)


# ═══════════════════════════════════════════════════════════
# 6. PipelineConfig
# ═══════════════════════════════════════════════════════════

class TestPipelineConfig:

    def test_default_config(self):
        from htt.core.pipeline_config import PipelineConfig
        cfg = PipelineConfig()
        assert cfg.cf4_version == 'wfh2009'
        assert cfg.quick is False

    def test_obs_file_mapping(self):
        from htt.core.pipeline_config import PipelineConfig
        assert PipelineConfig(cf4_version='wfh2009').obs_file == 'obs_defaults.json'
        assert PipelineConfig(cf4_version='watkins2023').obs_file == 'obs_defaults_watkins2023.json'
        assert PipelineConfig(cf4_version='courtois2025').obs_file == 'obs_defaults_CF4pp.json'

    def test_custom_path_overrides(self):
        from htt.core.pipeline_config import PipelineConfig
        cfg = PipelineConfig(obs_defaults_path='/custom/path.json')
        assert cfg.obs_file == '/custom/path.json'


# ═══════════════════════════════════════════════════════════
# 7. Bounds consistency
# ═══════════════════════════════════════════════════════════

class TestBoundsConsistency:

    def test_x_defect_pure_shear(self):
        """x = Σ² for pure shear (no tilt, no curvature, no vorticity)."""
        from tsc_legacy.htt_core_bounds import x_defect
        x = x_defect(Sig2=1e-6)
        assert x == pytest.approx(1e-6)

    def test_x_defect_with_tilt(self):
        from tsc_legacy.htt_core_bounds import x_defect, Omega_tilt
        beta = SYNTHETIC_BETA
        Ot = Omega_tilt(beta)
        x = x_defect(Sig2=1e-6, Omega_tilt=Ot)
        assert x > 1e-6  # tilt adds positive contribution

    def test_filling_fraction_bounded(self):
        from tsc_legacy.htt_core_bounds import filling_fraction
        ff = filling_fraction(1e-6, 1e-3)
        assert 0 <= ff <= 1

    def test_BV_Sigma2_momentum(self):
        """BV momentum constraint should give large Σ²."""
        from tsc_legacy.htt_core_bounds import Sig2_BV
        from htt.core.ssot import C
        S2 = Sig2_BV(beta=SYNTHETIC_BETA, Omega_K=0.01)
        # Should be large (overproduction)
        assert S2 > 1e-8


# ═══════════════════════════════════════════════════════════
# 8. Evidence model structure
# ═══════════════════════════════════════════════════════════

class TestEvidenceModels:

    def test_model_registry(self):
        """evidence_models_R03a should define model classes."""
        from htt.core import evidence_models_R03a as em
        assert hasattr(em, 'FLRW')
        assert hasattr(em, 'FLRW_tilt')

    def test_inactive_parameter_audit(self):
        """MODEL_AUDIT should flag inactive parameters."""
        from htt.core.evidence_models_R03a import MODEL_AUDIT
        assert isinstance(MODEL_AUDIT, dict)
        # BII_orth should have inactive n1
        if 'BII_orth' in MODEL_AUDIT:
            assert 'inactive' in str(MODEL_AUDIT['BII_orth']).lower() or \
                   len(MODEL_AUDIT['BII_orth'].get('inactive_params', [])) > 0
