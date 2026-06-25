import unittest
import numpy as np
from bass.background.bi_continuation import SpeciesPrimitive
from htt.integration.pr04_canonical_bridge import bianchi_i_moment_state

class IntegrationTests(unittest.TestCase):
    def test_bridge(self):
        species=(SpeciesPrimitive(.4,0,np.array([.2,0,0])),SpeciesPrimitive(.4,0,np.array([-.2,0,0])))
        state=bianchi_i_moment_state(species,H=1.0,sigma=np.diag([.02,-.01,-.01]),epoch='t0')
        self.assertEqual(state.names,('J_tilt','Pi_tilt','Omega_tilt','sigma'))
        self.assertEqual(state.dimension,14)
        self.assertLess(np.linalg.norm(state.block('J_tilt').value),1e-14)
        self.assertEqual(state.metadata['branch'],'restricted_bianchi_i_multifluid')

if __name__ == '__main__': unittest.main()
