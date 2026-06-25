"""PR07-003 gate: independent Bianchi-I conservation + constraint transport."""
import unittest
import numpy as np

from bass.background.bi_continuation import SpeciesPrimitive, BIState
from bass.background.bi_continuation.verification import (
    random_species_audit,
    constraint_transport_residual,
)


class ConservationTests(unittest.TestCase):
    def test_random_species_chain_rule(self):
        r = random_species_audit(samples=1000, seed=20260625)
        self.assertTrue(r['passed'])
        self.assertLess(r['max_energy_residual'], 1e-10)
        self.assertLess(r['max_momentum_residual'], 1e-10)

    def test_constraint_transport_balanced_pair(self):
        pair = (
            SpeciesPrimitive(0.55, 0.0, np.array([0.18, 0.0, 0.0])),
            SpeciesPrimitive(0.55, 0.0, np.array([-0.18, 0.0, 0.0])),
        )
        sigma = np.diag([0.03, -0.012, -0.018])
        from bass.background.bi_continuation.moments import total_projection
        p = total_projection(pair)
        sigma2 = 0.5 * np.sum(sigma * sigma)
        H = np.sqrt((p.mu + sigma2) / 3.0)
        state = BIState(1.0, H, sigma, pair)
        r = constraint_transport_residual(state)
        self.assertLess(abs(r['gauss_transport_residual']), 2e-12)
        self.assertLess(np.linalg.norm(r['codazzi_transport_residual']), 2e-12)


if __name__ == '__main__':
    unittest.main()
