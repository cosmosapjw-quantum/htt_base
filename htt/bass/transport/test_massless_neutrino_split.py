"""Contract of the optional homogeneous massless photon/neutrino split."""
import unittest

import numpy as np

from bass.transport.coupled_einstein_boltzmann import _species_thomson_forces, build_early_family_state


class TestMasslessNeutrinoSplit(unittest.TestCase):
    def test_initial_radiation_budget_and_velocity(self):
        unsplit, _, _ = build_early_family_state("VII_h", epsilon=2e-4)
        split, _, _ = build_early_family_state("VII_h", epsilon=2e-4, massless_neutrino_fraction=.4)
        by_species = {s.species:s for s in split.species_congruences}
        base = {s.species:s for s in unsplit.species_congruences}
        gamma, nu = by_species["radiation"], by_species["neutrino"]
        self.assertNotIn("neutrino", base)
        self.assertAlmostEqual(gamma.eps_hat + nu.eps_hat, base["radiation"].eps_hat, places=14)
        self.assertAlmostEqual(nu.eps_hat/base["radiation"].eps_hat, .4, places=14)
        np.testing.assert_array_equal(gamma.v_vec, nu.v_vec)
        np.testing.assert_allclose(gamma.to_projected_state().q + nu.to_projected_state().q,
                                   base["radiation"].to_projected_state().q, rtol=1e-14)
        np.testing.assert_allclose(split.H,unsplit.H,rtol=1e-14)

    def test_force_pair_and_invalid_fraction(self):
        forces = _species_thomson_forces(np.diag([1.,1/3,1/3,1/3]), [.2,0,0], .7, 4, 0, 2)
        self.assertGreater(np.linalg.norm(forces[0]),0.)
        np.testing.assert_array_equal(forces[3],0.)
        np.testing.assert_array_equal(forces[1],0.)
        np.testing.assert_array_equal(forces[0]+forces[2],0.)
        for invalid in [-.1, 1., np.inf, np.nan]:
            with self.assertRaises(ValueError):
                build_early_family_state("I", massless_neutrino_fraction=invalid)
