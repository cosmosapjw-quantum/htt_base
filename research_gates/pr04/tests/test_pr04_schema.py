import unittest
import numpy as np
from htt.common.stf_canonical import (
    CANONICAL_STF_BASIS, coeffs_to_stf, stf_to_coeffs,
    directional_hubble_design, basis_change_matrix,
)
from htt.common.multicomponent_blocks import BlockSpec, StateBlock, MulticomponentState

class SchemaTests(unittest.TestCase):
    def test_stf_roundtrip(self):
        c = np.array([0.3,-0.2,0.1,0.4,-0.5])
        self.assertTrue(np.allclose(stf_to_coeffs(coeffs_to_stf(c)), c, atol=1e-13))

    def test_basis_change(self):
        source = CANONICAL_STF_BASIS[[1,0,2,4,3]]
        m = basis_change_matrix(source)
        c = np.arange(1.,6.)
        self.assertTrue(np.allclose(coeffs_to_stf(m@c), np.einsum('a,aij->ij', c, source)))

    def test_hubble_rank(self):
        rng = np.random.default_rng(2)
        n = rng.normal(size=(300,3))
        self.assertEqual(np.linalg.matrix_rank(directional_hubble_design(n)), 9)

    def test_state_hash_and_metadata(self):
        b = StateBlock(BlockSpec('a','vector','1','frame','u','owner'), np.array([1.,2.,3.]), np.eye(3))
        s = MulticomponentState([b])
        self.assertEqual(s.dimension, 3)
        self.assertEqual(s.stable_hash(), s.stable_hash())

    def test_covariance_fail_closed(self):
        with self.assertRaises(ValueError):
            StateBlock(BlockSpec('a','vector','1','f','u','o'), np.zeros(3), np.diag([1,1,-1]))

if __name__ == '__main__': unittest.main()
