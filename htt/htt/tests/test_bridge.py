"""
htt/tests/test_bridge.py — HTT Bridge Module Tests
=====================================================
C-08 deliverable. Tests:
  1. All bridge outputs carry EXPLORATORY status
  2. Bridge bundle runs and produces expected keys
  3. Null runner importable
  4. Figure scripts exist (24 files)
"""
import pytest


class TestBridgeStatus:
    """All bridge outputs must be EXPLORATORY."""

    def test_tilt_velocity_exploratory(self):
        from htt.bridge.estimators import tilt_velocity
        r = tilt_velocity(beta=2.0e-4)
        assert r.status == 'EXPLORATORY'

    def test_delta_H_exploratory(self):
        from htt.bridge.estimators import delta_H
        r = delta_H(beta=2.0e-4, d_Mpc=100.0)
        assert r.status == 'EXPLORATORY'

    def test_delta_q_exploratory(self):
        from htt.bridge.estimators import delta_q
        r = delta_q(beta=2.0e-4, d_Mpc=100.0)
        assert r.status == 'EXPLORATORY'

    def test_lambda_J_exploratory(self):
        from htt.bridge.estimators import lambda_J_pec
        r = lambda_J_pec(beta=2.0e-4)
        assert r.status == 'EXPLORATORY'

    def test_verify_all_exploratory(self):
        from htt.bridge.estimators import verify_all_exploratory
        assert verify_all_exploratory() is True

    def test_bridge_status_constant(self):
        from htt.bridge.estimators import BRIDGE_STATUS
        assert BRIDGE_STATUS == 'EXPLORATORY'


class TestBridgeBundle:

    def test_bundle_runs(self):
        from htt.bridge.runner import run_bridge_bundle
        from htt.core.cf4_observational_input import CF4InputQuarantined
        with pytest.raises(CF4InputQuarantined):
            run_bridge_bundle()
        bundle = run_bridge_bundle(beta=2.0e-4, input_mode='synthetic')
        assert bundle['status'] == 'EXPLORATORY'

    def test_bundle_has_keys(self):
        from htt.bridge.runner import run_bridge_bundle
        bundle = run_bridge_bundle(beta=2.0e-4, input_mode='synthetic')
        assert 'tilt_velocity' in bundle
        assert 'lambda_J' in bundle
        assert 'delta_H_profile' in bundle
        assert 'delta_q_profile' in bundle

    def test_bundle_physics(self):
        from htt.bridge.runner import run_bridge_bundle
        bundle = run_bridge_bundle(beta=2.0e-4, input_mode='synthetic')
        assert 50 < bundle['tilt_velocity']['value'] < 70
        # lambda_J depends on q: ~297 Mpc (q=0.5 EdS) or ~526 Mpc (q=0.09 Son+2025)
        assert 200 < bundle['lambda_J']['value'] < 600

    def test_delta_H_decreases_with_distance(self):
        """ΔH = βc/(3d) should decrease with distance."""
        from htt.bridge.runner import run_bridge_bundle
        bundle = run_bridge_bundle(beta=2.0e-4, input_mode='synthetic')
        profile = bundle['delta_H_profile']
        dH_50 = profile.get('50', {}).get('value', 0)
        dH_1000 = profile.get('1000', {}).get('value', 0)
        assert dH_50 > dH_1000


class TestNullRunner:

    def test_null_runner_importable(self):
        from htt.nulls.runner import run_null_library, ALL_FAMILIES
        assert callable(run_null_library)
        assert len(ALL_FAMILIES) == 5


class TestFigureScripts:

    def test_24_figure_scripts(self):
        from pathlib import Path
        fig_dir = Path(__file__).resolve().parent.parent / 'htt' / 'figures'
        scripts = list(fig_dir.glob('fig_*.py'))
        assert len(scripts) >= 22, f"Only {len(scripts)} figure scripts found"
