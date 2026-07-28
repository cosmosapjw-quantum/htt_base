"""
htt/tests/test_integration.py — HTT Integration + Edge Case Tests
===================================================================
C-19 deliverable. Expands edge case coverage.
"""
import pytest
import numpy as np


class TestHPDEdgeCases:

    def test_hpd_delta_function(self):
        """HPD on a single repeated value → degenerate interval."""
        from htt.core.departure_posteriors import weighted_hpd
        vals = np.full(100, 5.0)
        w = np.ones(100)
        lo, hi = weighted_hpd(vals, w, 0.68)
        assert lo == 5.0
        assert hi == 5.0

    def test_hpd_two_point_mass(self):
        """Two point masses with unequal weights."""
        from htt.core.departure_posteriors import weighted_hpd
        vals = np.array([1.0, 10.0])
        w = np.array([0.8, 0.2])
        lo, hi = weighted_hpd(vals, w, 0.5)
        # 80% weight at 1.0 — HPD should capture the heavy point
        assert lo == 1.0

    def test_hpd_large_sample(self):
        """HPD with 10000 samples should be stable."""
        from htt.core.departure_posteriors import weighted_hpd
        rng = np.random.default_rng(42)
        vals = rng.normal(0, 1, 10000)
        w = np.ones(10000)
        lo, hi = weighted_hpd(vals, w, 0.68)
        assert abs((hi - lo) - 2.0) < 0.1


class TestSharedCauseDegeneracy:

    def test_beta_zero_is_flrw(self):
        """At β=0, there should be no tilt signal."""
        from htt.infer.estimators import tilt_velocity, delta_H
        r = tilt_velocity(beta=0.0)
        assert r.value == 0.0
        dH = delta_H(beta=0.0, d_Mpc=100.0)
        assert dH.value == 0.0


class TestBridgeExploratoryHardBan:

    def test_all_bridge_functions_tagged(self):
        """Every bridge estimator must return EXPLORATORY status."""
        from htt.bridge.estimators import (tilt_velocity, delta_H,
            delta_q, lambda_J_pec, BRIDGE_STATUS)
        beta = 2.0e-4  # explicit synthetic parameter
        for fn, args in [
            (tilt_velocity, (beta,)),
            (delta_H, (beta, 100.0)),
            (delta_q, (beta, 100.0)),
            (lambda_J_pec, (beta,)),
        ]:
            r = fn(*args)
            assert r.status == 'EXPLORATORY', \
                f"{fn.__name__} has status '{r.status}'"

    def test_bridge_bundle_status(self):
        from htt.bridge.runner import run_bridge_bundle
        from htt.core.cf4_observational_input import CF4InputQuarantined
        with pytest.raises(CF4InputQuarantined):
            run_bridge_bundle()
        bundle = run_bridge_bundle(beta=2.0e-4, input_mode='synthetic')
        assert bundle['status'] == 'EXPLORATORY'


class TestHTTIntegrationAdapters:

    def test_from_bass_ingestion(self):
        from htt.integration.from_bass import ingest_bass_directional
        # Mock bundle
        class MockBundle:
            f2_teff = 1.3e-3
            gauge_deviation = 1e-16
            families_scanned = 8
            family_results = {'BI_orth': {'R_sigma': 1.0}}
        result = ingest_bass_directional(MockBundle())
        assert result['ingested']
        assert result['f2_teff'] == 1.3e-3

    def test_to_mio_builds_bundle(self):
        from htt.integration.to_mio import build_posterior_bundle
        bundle = build_posterior_bundle(legacy_reproduction=True)
        assert bundle.x_median >= 0
        assert bundle.ln_B_total > 0  # Pipeline has positive evidence
        assert bundle.Pi_hpd68 == pytest.approx((0.05, 0.22))


class TestDirectionalLowell:

    def test_angular_separation_self(self):
        from htt.infer.directional_lowell import angular_separation
        assert angular_separation(100, 30, 100, 30) == 0.0

    def test_angular_separation_antipodal(self):
        from htt.infer.directional_lowell import angular_separation
        sep = angular_separation(0, 90, 0, -90)
        assert abs(sep - 180.0) < 0.01

    def test_alignment_probability(self):
        from htt.infer.directional_lowell import alignment_probability
        # p(theta < 90°) = 0.5
        assert abs(alignment_probability(90.0) - 0.5) < 0.01
        # p(theta < 180°) = 1.0
        assert abs(alignment_probability(180.0) - 1.0) < 0.01

    def test_lowell_evaluate(self):
        from htt.infer.directional_lowell import LowellLikelihood
        from htt.core.cf4_observational_input import CF4InputQuarantined
        with pytest.raises(CF4InputQuarantined):
            LowellLikelihood()
        ll = LowellLikelihood(lowz_l=120.0, lowz_b=10.0)
        result = ll.evaluate()
        assert result.sep_quad_oct < 10  # known tight alignment
        assert result.status == 'diagnostic_only'
        assert result.excluded_channels == ('c',)

    def test_lowell_info_gain_positive(self):
        from htt.infer.directional_lowell import LowellLikelihood
        ll = LowellLikelihood(lowz_l=120.0, lowz_b=10.0)
        gain = ll.information_gain(n_samples=2000)
        assert gain > 0


class TestLowzAblation:

    def test_ablation_runs(self):
        from htt.infer.lowz_ablation import run_lowz_ablation
        z = np.linspace(0.001, 0.05, 100)
        results = run_lowz_ablation(
            z_catalog=z,
            beta_catalog=np.full_like(z, 2.0e-4),
            lowz_axis=(120.0, 10.0),
        )
        assert len(results) == 5
        for r in results:
            assert r.n_remaining >= 0
            assert 0 <= r.fractional_loss <= 1

    def test_ablation_monotonic_loss(self):
        from htt.infer.lowz_ablation import run_lowz_ablation
        z = np.linspace(0.001, 0.05, 100)
        results = run_lowz_ablation(
            z_catalog=z,
            beta_catalog=np.full_like(z, 2.0e-4),
            lowz_axis=(120.0, 10.0),
        )
        losses = [r.fractional_loss for r in results]
        for i in range(len(losses) - 1):
            assert losses[i] <= losses[i+1] + 0.01  # monotonically increasing


class TestNullCompetition:

    def test_engine_creates(self):
        from htt.infer.null_competition import NullCompetitionEngine
        engine = NullCompetitionEngine(n_realizations=5, fpr_threshold=0.5)
        assert engine.n_realizations == 5

    def test_compete_single_family(self):
        from htt.infer.null_competition import NullCompetitionEngine
        engine = NullCompetitionEngine(n_realizations=5)
        result = engine.compete_family('scanning_law')
        assert result.family_name == 'scanning_law'
        assert result.n_realizations == 5
        assert 0 <= result.fpr <= 1
        assert result.status == 'diagnostic_only'

    def test_run_all_families(self):
        from htt.infer.null_competition import NullCompetitionEngine
        engine = NullCompetitionEngine(n_realizations=3)
        result = engine.run_all()
        assert result.families_tested == 5  # 5 null families
        assert result.families_robust + result.families_vulnerable == 5
        assert result.worst_family in [
            'scanning_law', 'mask_leakage', 'clustering',
            'selection_response', 'survey_axis']

    def test_convenience_function(self):
        from htt.infer.null_competition import run_null_competition
        result = run_null_competition(n_realizations=3, fpr_threshold=0.5)
        assert result.families_tested == 5


class TestSurveyNuisance:

    def test_registry_has_surveys(self):
        from htt.infer.survey_nuisance import SURVEY_REGISTRY
        assert set(SURVEY_REGISTRY) == {'CW', 'Radio'}
        assert 'CF4' not in SURVEY_REGISTRY

    def test_covariance_positive(self):
        from htt.infer.survey_nuisance import SURVEY_REGISTRY
        for name, s in SURVEY_REGISTRY.items():
            assert s.covariance.sigma_total > 0, f"{name} has non-positive sigma"

    def test_combined_covariance(self):
        from htt.infer.survey_nuisance import combined_covariance
        import numpy as np
        cov = combined_covariance()
        assert cov.shape == (2, 2)
        assert np.all(np.diag(cov) > 0)
        # Diagonal (no off-diagonal for now)
        assert np.all(cov - np.diag(np.diag(cov)) == 0)

    def test_nuisance_marginal_enlarges(self):
        from htt.infer.survey_nuisance import nuisance_marginal_correction, SURVEY_REGISTRY
        beta, sigma = nuisance_marginal_correction(2.0e-4, 'CW')
        assert beta == 2.0e-4  # mean unchanged for an explicit synthetic input
        assert sigma > SURVEY_REGISTRY['CW'].covariance.sigma_total

    def test_compatibility_test(self):
        from htt.infer.survey_nuisance import survey_compatibility_test
        # Consistent measurements
        result = survey_compatibility_test({'CW': 2.0e-4, 'Radio': 2.1e-4})
        assert 'chi2' in result
        assert 'p_value' in result
        assert result['dof'] == 1

    def test_compatibility_catches_discrepancy(self):
        from htt.infer.survey_nuisance import survey_compatibility_test
        # Wildly discrepant measurements
        result = survey_compatibility_test({'CW': 5.0e-3, 'Radio': 0.1e-3})
        assert result['chi2'] > 10  # should be large

    def test_cf4_nuisance_request_fails_closed(self):
        from htt.core.cf4_observational_input import CF4InputQuarantined
        from htt.infer.survey_nuisance import get_survey_nuisance

        with pytest.raises(CF4InputQuarantined, match='N-DATA-CF4-DOWNSTREAM'):
            get_survey_nuisance('CF4')
