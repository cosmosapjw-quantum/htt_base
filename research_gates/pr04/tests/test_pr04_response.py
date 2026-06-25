import unittest
import numpy as np
from htt.departure.multicomponent_response import audit_response_blocks, principal_angles, rank_gain_ladder

class ResponseTests(unittest.TestCase):
    def test_full_and_duplicate_rank(self):
        rng=np.random.default_rng(3); a=rng.normal(size=(80,3)); b=rng.normal(size=(80,2)); c=np.eye(80)
        full=audit_response_blocks({'a':a,'b':b},c)
        self.assertEqual(full.rank,5)
        dup=audit_response_blocks({'a':a,'copy':a},c)
        self.assertEqual(dup.rank,3)
        self.assertEqual(dup.nullspace.shape[1],3)

    def test_nuisance_removes_exact_block(self):
        rng=np.random.default_rng(4); a=rng.normal(size=(50,3)); b=rng.normal(size=(50,2))
        out=audit_response_blocks({'a':a,'b':b},np.eye(50),nuisance=a)
        self.assertEqual(out.rank,2)

    def test_principal_angle_identical(self):
        rng=np.random.default_rng(5); a=rng.normal(size=(40,3))
        angles=principal_angles(a,a,np.eye(40))
        self.assertLess(np.max(np.abs(angles)),1e-7)

    def test_rank_ladder(self):
        rng=np.random.default_rng(6); blocks={'x':rng.normal(size=(60,2)),'y':rng.normal(size=(60,3))}
        ladder=rank_gain_ladder(blocks,np.eye(60))
        self.assertEqual([x['rank'] for x in ladder],[2,5])

if __name__ == '__main__': unittest.main()
