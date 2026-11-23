import unittest
import numpy as np
from scripts.r103.gaia_frame_curvature import curvature_rows, shared_patch_refits
from scripts.r105.gaia_frame_parity import joint_modes, frame_shifted_rhs, MAG, ELE
from scripts.r105.radio_matched_refits import paired_covariance, selection_fit
from htt.htt.infer.r65_count_quotient import RingLikelihood, shared_maps, fit_joint


class FrameAndCovarianceTests(unittest.TestCase):
    def test_known_conditional_gaussian_factorization(self):
        rng=np.random.default_rng(420)
        A=rng.normal(size=(16,16))/8
        B=np.eye(16)+A@A.T
        c=np.eye(32)
        c[np.ix_(MAG,MAG)]=B
        c[np.ix_(MAG,ELE)]=A
        c[np.ix_(ELE,MAG)]=A.T
        y=rng.normal(size=32)
        res=joint_modes(y,c)
        v=y[MAG]-A@y[ELE]
        self.assertAlmostEqual(res["magnetic_given_zero_mean_electric_working_quadratic"],v@v,places=11)
        self.assertAlmostEqual(res["joint_working_quadratic"],y@np.linalg.solve(c,y),places=11)
        with self.assertRaises(np.linalg.LinAlgError):
            joint_modes(y,np.zeros((32,32)))

    def test_frame_shift_passes_through_every_shared_deletion(self):
        rnd=np.random.default_rng(859)
        f=rnd.normal(size=(4,6,30,16))
        f=np.einsum("spai,spaj->spij",f,f)
        s=rnd.normal(size=(4,6,16))
        z=np.array([.4,.8,1.4,2.5])
        left=shared_patch_refits(f,s)
        right=shared_patch_refits(f,frame_shifted_rhs(f,s,z))
        for a,b in zip(left[:3],right[:3]):
            np.testing.assert_allclose(curvature_rows(z)@(a-b),0,atol=1e-10)

    def test_common_count_reduction_and_overlap(self):
        rng=np.random.default_rng(47)
        f=rng.normal(size=(240,6))
        y=rng.poisson(4,size=(3,240))
        r=np.repeat(np.arange(12),20)
        ex=[RingLikelihood(row,f[:,:2],r) for row in y]
        maps,off=shared_maps(3,2)
        np.testing.assert_allclose(selection_fit(y,f,r,2),fit_joint(ex,maps,off)["estimate"],atol=1e-12)
        x=rng.normal(size=(20,2))
        _,zero=paired_covariance(np.column_stack((x,x)))
        np.testing.assert_allclose(zero,0,atol=1e-12)
        y=x+rng.normal(scale=.1,size=(20,2))
        _,cov=paired_covariance(np.column_stack((x,y)))
        centered=(y-x)-(y-x).mean(axis=0)
        np.testing.assert_allclose(cov,.95*(centered.T@centered),atol=1e-13)


if __name__=="__main__":
    unittest.main()
