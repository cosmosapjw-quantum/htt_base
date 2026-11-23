import unittest
import numpy as np
from scripts.r101.chemistry_coherency import evolve_rest_frame, sphere_grid, fixture, run


class TestChemistryCoherency(unittest.TestCase):
    def test_joint_tangent_and_conservation(self):
        result=run(24)
        self.assertLess(result['rate_response_max_fd_error'],1e-9)
        self.assertLess(result['fused_vs_sequential_max_error'],1e-12)
        self.assertLess(result['intensity_monopole_defect'],1e-12)
        self.assertLess(result['last_scatter_mass_defect'],1e-14)
        self.assertGreater(result['minimum_stokes_cone_margin'],0)

    def test_reject_single_tilted_ray_as_angular_collision(self):
        n,w=sphere_grid();s=np.zeros((len(n),4));s[:,0]=1
        k=fixture(3);k['beta']=[.1,0.,0.]
        with self.assertRaises(ValueError):evolve_rest_frame(n,w,s,k)
        k=fixture(3)
        from bass.recombination.clocked_chemistry import ChemistryTangent
        k['tangent']=ChemistryTangent(beta=[.1,0.,0.])
        with self.assertRaises(ValueError):evolve_rest_frame(n,w,s,k)


if __name__=='__main__':unittest.main()
