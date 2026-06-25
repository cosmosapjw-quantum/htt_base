import unittest
import numpy as np
from mio.formalism.physical_pushforward import (
    legacy_signed_defect_pushforward, ratio_pushforward, matrix_budget_radius,
)

class PushforwardTests(unittest.TestCase):
    def test_full_legacy_contract(self):
        s={'Sigma_standard':np.array([.1,.2]),'W_standard':np.array([.01,.02]),
           'Omega_tilt':np.array([.03,.04]),'Omega_k_aniso':np.array([.0,.0])}
        out=legacy_signed_defect_pushforward(s,x_max=.5)
        self.assertEqual(out['x_C'].status,'OK')
        self.assertEqual(out['Q'].status,'OK')
        self.assertAlmostEqual(out['x_C'].summary['mean'],.17)

    def test_missing_component_blocks(self):
        out=legacy_signed_defect_pushforward({'Sigma_standard':np.array([.1])})
        self.assertEqual(out['x_C'].status,'BLOCKED_UNIDENTIFIED_COMPONENTS')
        self.assertIn('Omega_tilt',out['x_C'].missing_components)

    def test_ratio_zero_branch(self):
        out=ratio_pushforward('G',np.ones(2),np.array([1.,0.]),'G_v1')
        self.assertEqual(out.status,'BLOCKED_ZERO_DENOMINATOR_BRANCH')

    def test_matrix_budget(self):
        x=np.array([[1.,2.],[2.,0.]])
        r=matrix_budget_radius(x,np.diag([2.,4.]))
        self.assertTrue(np.allclose(r,[1.5,2.]))

if __name__ == '__main__': unittest.main()
