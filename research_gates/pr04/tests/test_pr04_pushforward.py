import unittest
import numpy as np
from common.statistical_foundations import ScalarRange
from mio.formalism.physical_pushforward import (
    legacy_signed_defect_pushforward, ratio_pushforward, matrix_budget_radius,
)

class PushforwardTests(unittest.TestCase):
    def test_active_bare_denominator_is_blocked(self):
        s={'Sigma_standard':np.array([.1,.2]),'W_standard':np.array([.01,.02]),
           'Omega_tilt':np.array([.03,.04]),'Omega_k_aniso':np.array([.0,.0])}
        out=legacy_signed_defect_pushforward(s,x_max=.5)
        self.assertEqual(out['x_C'].status,'OK')
        self.assertEqual(out['Q'].status,'BLOCKED_UNTYPED_DENOMINATOR')
        self.assertAlmostEqual(out['x_C'].summary['mean'],.17)

    def test_full_legacy_contract_requires_explicit_reproduction(self):
        s={'Sigma_standard':np.array([.1,.2]),'W_standard':np.array([.01,.02]),
           'Omega_tilt':np.array([.03,.04]),'Omega_k_aniso':np.array([.0,.0])}
        out=legacy_signed_defect_pushforward(
            s,x_max=.5,legacy_reproduction=True,
        )
        self.assertEqual(out['x_C'].status,'OK')
        self.assertEqual(out['Q'].status,'OK')
        self.assertAlmostEqual(out['x_C'].summary['mean'],.17)
        self.assertAlmostEqual(out['Q'].summary['mean'],.34)

    def test_missing_component_blocks(self):
        out=legacy_signed_defect_pushforward({'Sigma_standard':np.array([.1])})
        self.assertEqual(out['x_C'].status,'BLOCKED_UNIDENTIFIED_COMPONENTS')
        self.assertIn('Omega_tilt',out['x_C'].missing_components)

    def test_active_raw_ratio_is_blocked(self):
        out=ratio_pushforward('G',np.ones(2),np.array([1.,0.]),'G_v1')
        self.assertEqual(out.status,'BLOCKED_UNTYPED_DENOMINATOR')

    def test_legacy_zero_containing_interval_is_unidentified(self):
        out=ratio_pushforward(
            'G',
            np.ones(2),
            np.array([1.,0.]),
            'G_v1',
            denominator_interval=ScalarRange(0.0,1.0),
            atol=0.0,
            rtol=0.0,
            legacy_reproduction=True,
        )
        self.assertEqual(out.status,'RATIO_UNIDENTIFIED')

    def test_matrix_budget(self):
        x=np.array([[1.,2.],[2.,0.]])
        r=matrix_budget_radius(x,np.diag([2.,4.]))
        self.assertTrue(np.allclose(r,[1.5,2.]))

if __name__ == '__main__': unittest.main()
