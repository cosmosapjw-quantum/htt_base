"""
htt/tests/test_infer.py — HTT Inference Module Tests
======================================================
C-07 deliverable. Tests matched to actual API signatures.
"""
import pytest
import numpy as np


class TestLatentAxis:

    def test_dipole_projection(self):
        from htt.infer.latent_axis import dipole_projection
        proj = dipole_projection(np.array([0, 0, 1]), np.array([0, 0, 1]), 1.0)
        assert proj == pytest.approx(1.0)

    def test_projection_orthogonal(self):
        from htt.infer.latent_axis import dipole_projection
        proj = dipole_projection(np.array([1, 0, 0]), np.array([0, 1, 0]), 1.0)
        assert proj == pytest.approx(0.0, abs=1e-10)

    def test_params_dataclass(self):
        from htt.infer.latent_axis import LatentAxisParams
        p = LatentAxisParams(l_deg=264.0, b_deg=48.0, A=1e-3)
        assert p.l_deg == 264.0
        assert p.A == 1e-3


class TestDipoleVectorLikelihood:

    def _load_obs(self):
        import json
        from pathlib import Path
        p = Path(__file__).resolve().parent.parent.parent / 'workspace' / 'data' / 'obs_defaults.json'
        if not p.exists():
            pytest.skip("obs_defaults.json not found")
        with open(p) as f:
            return json.load(f)

    def test_construction_with_data(self):
        from htt.infer.dipole_vector_likelihood import DipoleVectorLikelihood
        obs = self._load_obs()
        dvl = DipoleVectorLikelihood(obs_data=obs)
        assert dvl is not None

    def test_has_log_likelihood(self):
        from htt.infer.dipole_vector_likelihood import DipoleVectorLikelihood
        obs = self._load_obs()
        dvl = DipoleVectorLikelihood(obs_data=obs)
        assert hasattr(dvl, 'directional_log_likelihood')


class TestSharedCause:

    def test_result_structure(self):
        from htt.infer.shared_cause import SharedCauseResult
        r = SharedCauseResult(
            lnB_S2_vs_null=3.0, S2_preferred=True,
            survives_ablation=True,
            direction_l=264.0, direction_b=48.0,
            amplitude=1e-3, classification='physical'
        )
        assert r.lnB_S2_vs_null == 3.0
        assert r.S2_preferred is True

    def test_run_function_exists(self):
        from htt.infer.shared_cause import run_shared_cause_test
        assert callable(run_shared_cause_test)


class TestControlRegistry:

    def test_four_controls(self):
        from htt.infer.control_registry import CONTROLS
        assert len(CONTROLS) == 4
        assert set(CONTROLS.keys()) == {'C0', 'C1', 'C2', 'C3'}

    def test_C0_baseline(self):
        from htt.infer.control_registry import get_control
        c0 = get_control('C0')
        assert c0.code == 'C0'
        assert c0.name == 'baseline'

    def test_control_spec_has_fields(self):
        from htt.infer.control_registry import CONTROLS
        for code, spec in CONTROLS.items():
            assert hasattr(spec, 'code')
            assert hasattr(spec, 'name')
            assert hasattr(spec, 'n_total')

    def test_complexity_increases(self):
        """C0 <= C1 <= C2 <= C3 in total parameter count."""
        from htt.infer.control_registry import CONTROLS
        counts = [CONTROLS[f'C{i}'].n_total for i in range(4)]
        for i in range(1, 4):
            assert counts[i] >= counts[i-1], f"C{i} ({counts[i]}) < C{i-1} ({counts[i-1]})"


class TestMatchedComplexity:

    def test_enforce_function_exists(self):
        from htt.infer.matched_complexity import enforce_matched_complexity
        assert callable(enforce_matched_complexity)

    def test_report_structure(self):
        from htt.infer.matched_complexity import MatchedComplexityReport
        r = MatchedComplexityReport(
            controls_checked=['C0', 'C1'],
            amplitude_matched=True, nuisance_matched=True,
            prior_width_matched=True, overall_pass=True, violations=[]
        )
        assert r.overall_pass is True
        assert len(r.violations) == 0


class TestEstimators:

    def test_tilt_velocity(self):
        from htt.infer.estimators import tilt_velocity
        result = tilt_velocity(beta=2.0e-4, z=0.0)
        assert hasattr(result, 'value')
        assert result.value > 0

    def test_delta_H(self):
        from htt.infer.estimators import delta_H
        result = delta_H(beta=2.0e-4, d_Mpc=100.0)
        assert hasattr(result, 'value')
        assert result.value > 0

    def test_delta_q(self):
        from htt.infer.estimators import delta_q
        result = delta_q(beta=2.0e-4, d_Mpc=100.0)
        assert result is not None

    def test_lambda_J(self):
        from htt.infer.estimators import lambda_J_pec
        result = lambda_J_pec(beta=2.0e-4)
        assert hasattr(result, 'value')
        assert result.value > 100  # ~297 Mpc

    def test_bridge_result_has_status(self):
        from htt.infer.estimators import BridgeResult
        assert hasattr(BridgeResult, '__dataclass_fields__')
        assert 'status' in BridgeResult.__dataclass_fields__

    def test_bridge_results_exploratory(self):
        """All bridge estimators should be tagged EXPLORATORY."""
        from htt.infer.estimators import tilt_velocity, delta_H
        r = tilt_velocity(beta=2.0e-4)
        assert r.status == 'EXPLORATORY'
        r2 = delta_H(beta=2.0e-4, d_Mpc=100.0)
        assert r2.status == 'EXPLORATORY'
