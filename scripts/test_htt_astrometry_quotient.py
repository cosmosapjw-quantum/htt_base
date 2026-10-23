import unittest
import numpy as np
from htt_astrometry_quotient import contrast_matrices, finite_nuisance_quotient, shifted_mixture


class QuotientTests(unittest.TestCase):
    def test_common_offset_contrast(self):
        a,l,k=contrast_matrices()
        np.testing.assert_array_equal(k@a,np.zeros((6,3)))
        np.testing.assert_array_equal(l@a,np.zeros((3,3)))

    def test_unrestricted_mean_removed_using_joint_statistics(self):
        rng=np.random.default_rng(831); d=rng.normal(size=(200,4));h=rng.normal(size=(200,7));h[:,0]+=d[:,0]
        x=np.column_stack([d,h]);beta=np.arange(4.);theta=rng.normal(size=7)*100
        g=x.T@x;r=finite_nuisance_quotient(g,x.T@(d@beta+h@theta),signal_dim=4)
        np.testing.assert_allclose(r['projected_signal_estimate'],beta,atol=1e-10)
        self.assertTrue(all(r['contrast_estimable']))
        # Compare to direct residualized-row least squares, independent implementation.
        p=np.eye(200)-h@np.linalg.pinv(h);direct=np.linalg.inv(d.T@p@d)
        np.testing.assert_allclose(r['projected_signal_covariance'],direct,atol=1e-12)

    def test_rank_loss_cannot_be_zero_filled(self):
        rng=np.random.default_rng(1);d=rng.normal(size=(40,3));h=d[:,:1]
        x=np.column_stack([d,h]);r=finite_nuisance_quotient(x.T@x,x.T@(d@np.ones(3)),signal_dim=3)
        self.assertEqual(r['signal_rank'],2);self.assertFalse(r['contrast_estimable'][0]);self.assertIsNone(r['contrast_estimate'][0])

    def test_singular_redundant_nuisance(self):
        rng=np.random.default_rng(2);d=rng.normal(size=(50,2));h=rng.normal(size=(50,1));x=np.column_stack([d,h,h])
        r=finite_nuisance_quotient(x.T@x,x.T@(d@np.array([3.,4.])+9*h[:,0]),signal_dim=2)
        np.testing.assert_allclose(r['projected_signal_estimate'],[3,4],atol=1e-10)

    def test_bad_statistics_fail(self):
        with self.assertRaises(ValueError):finite_nuisance_quotient(np.diag([1.,-2.]),np.zeros(2),signal_dim=1)
        with self.assertRaises(ValueError):finite_nuisance_quotient(np.diag([1.,0.]),np.ones(2),signal_dim=1)

    def test_nuisance_units_preserve_span_and_mean(self):
        d=np.array([[1.,0],[0,1],[0,0],[0,0]])
        h=np.array([[1.,0],[0,0],[1,0],[0,1]])
        y=d@np.array([1.,2.])+h@np.array([10.,20.])
        for units in ([1.,1.],[1e-6,1.],[1e-6,1e6],[1e6,1e-6]):
            with self.subTest(units=units):
                x=np.column_stack([d,h*np.array(units)])
                r=finite_nuisance_quotient(x.T@x,x.T@y,signal_dim=2)
                np.testing.assert_allclose(r['projected_signal_estimate'],[1,2],atol=1e-12)
                diag=r['numerical_diagnostics']
                self.assertEqual(diag['nuisance_rank'],2)
                self.assertEqual(diag['physical_projector_transport']['branch'],'full_rank')
                self.assertIsNone(diag['physical_projector_transport']['eta'])
                self.assertGreater(diag['nuisance_rank_tolerance'],0)
                self.assertGreater(diag['quotient_roundoff_tolerance'],0)
                np.testing.assert_allclose(diag['column_scales'],np.sqrt(np.diag(x.T@x)))
                # Independent row-space projection; normalize only for SVD rank.
                hu=h*np.array(units); uh,_,_=np.linalg.svd(hu/np.linalg.norm(hu,axis=0),full_matrices=False)
                dr=d-uh@(uh.T@d)
                np.testing.assert_allclose(r['projected_signal_covariance'],np.linalg.inv(dr.T@dr),atol=1e-12)

    def test_contrast_scale_cannot_change_estimability(self):
        x=np.array([[1.,0,1],[0,1,0]]);y=np.array([3.,4.])
        k=np.array([[1.,0],[1e-8,0],[1e-200,0],[0,1],[0,1e-8],[0,0]])
        r=finite_nuisance_quotient(x.T@x,x.T@y,signal_dim=2,contrasts=k)
        self.assertEqual(r['contrast_estimable'],[False,False,False,True,True,True])
        self.assertEqual(r['contrast_estimate'][:3],[None,None,None])
        np.testing.assert_allclose(r['contrast_estimate'][3:],[4,4e-8,0],atol=1e-20)
        np.testing.assert_array_equal(np.array(r['contrast_covariance'])[-1],np.zeros(6))

    def test_partial_rank_analytic_physical_reference_and_units(self):
        v=np.array([1.,2.,3.]);t=7.
        # Nuisance affects the second row only: residual signal is v.
        d=np.array([v,[2.,-1.,1.]]);h=np.array([[0.],[1.]])
        y=np.array([t,11.]); k=np.array([v,[1.,0,0]])
        for units in ([1.,1.,1.],[.5,2.,3.]):
            units=np.array(units);w=v*units
            x=np.column_stack([d*units,h])
            r=finite_nuisance_quotient(x.T@x,x.T@y,signal_dim=3,contrasts=k*units)
            diag=r['numerical_diagnostics'];transport=diag['physical_projector_transport']
            self.assertEqual(transport['branch'],'partial_rank')
            self.assertLessEqual(transport['eta'],transport['eta_threshold'])
            self.assertEqual(diag['contrast_relative_tolerance'],1e-7)
            vv=w@w
            np.testing.assert_allclose(r['estimable_projector'],np.outer(w,w)/vv,atol=2e-14)
            np.testing.assert_allclose(r['projected_signal_estimate'],w*t/vv,atol=2e-14)
            np.testing.assert_allclose(r['projected_signal_covariance'],np.outer(w,w)/vv**2,atol=2e-14)
            self.assertEqual(r['contrast_estimable'],[True,False])
            self.assertAlmostEqual(r['contrast_estimate'][0],t)
            self.assertIsNone(r['contrast_estimate'][1])
            p=np.array(r['estimable_projector']);cov=np.array(r['projected_signal_covariance'])
            np.testing.assert_allclose(p@p,p,atol=2e-14)
            np.testing.assert_allclose(p,p.T,atol=2e-14)
            np.testing.assert_allclose(p@cov,cov,atol=2e-14)
            self.assertAlmostEqual(r['contrast_covariance'][0][0],1.)

    def test_contrast_normalization_underflow_rejected(self):
        x=np.array([[1e150,0.,1.],[0.,1e150,0.]])
        y=np.array([3.,4.]);k=np.array([[1.,0.],[1e-200,0.]])
        # Both rows target the same confounded coordinate; normalization must
        # not turn the tiny nonzero row into an estimable exact zero.
        with self.assertRaisesRegex(ValueError,'contrast normalization underflow'):
            finite_nuisance_quotient(x.T@x,x.T@y,signal_dim=2,contrasts=k)

    def test_nonzero_estimable_variance_float_range_rejected(self):
        # In this independent unit design Var(k*g)=k**2 is strictly positive.
        for k in (1e-200,1e200):
            with self.subTest(k=k):
                with self.assertRaisesRegex(ValueError,'contrast variance outside floating-point range'):
                    finite_nuisance_quotient(np.eye(2),np.zeros(2),signal_dim=1,contrasts=[[k]])
        r=finite_nuisance_quotient(np.eye(2),np.zeros(2),signal_dim=1,contrasts=[[0.]])
        self.assertEqual(r['contrast_estimable'],[True])
        self.assertEqual(r['contrast_estimate'],[0.])
        self.assertEqual(r['contrast_covariance'],[[0.]])

    def test_unreliable_partial_physical_projection_rejected(self):
        d=np.array([[1.,1.],[1,0],[0,1]]);h=d[:,:1]
        y=d@np.array([3.,4.])+10*h[:,0]
        x=np.column_stack([d*np.array([1e6,1e-6]),h])
        with self.assertRaisesRegex(ValueError,'unreliable partial-rank'):
            finite_nuisance_quotient(x.T@x,x.T@y,signal_dim=2)

    def test_ambiguous_nuisance_rank_rejected(self):
        # Unit diagonal nuisance Gram with eigenvalues 1e-11 and 2-1e-11.
        g=np.eye(3);g[1,2]=g[2,1]=1-1e-11
        with self.assertRaisesRegex(ValueError,'ambiguous positive nuisance rank'):
            finite_nuisance_quotient(g,np.zeros(3),signal_dim=1)

    def test_degenerate_zero_and_fully_confounded_designs(self):
        cases=[(np.array([[1.,0,0],[0,1,0]]),[2.,3.],2),
               (np.array([[0.,1.],[0,2.]]),[2.,4.],1),
               (np.zeros((2,3)),[0.,0.],2),
               (np.array([[1.,1.],[2,2.]]),[3.,6.],1)]
        for x,y,n in cases:
            r=finite_nuisance_quotient(x.T@x,x.T@np.array(y),signal_dim=n)
            expected=n if np.any(x[:,:n]) and not np.any(x[:,n:]) else 0
            self.assertEqual(r['signal_rank'],expected)
            if expected==0:
                self.assertEqual(r['numerical_diagnostics']['physical_projector_transport']['branch'],'rank_zero')
                self.assertIsNone(r['numerical_diagnostics']['physical_projector_transport']['eta'])
                np.testing.assert_array_equal(r['projected_signal_estimate'],np.zeros(n))
                np.testing.assert_array_equal(r['projected_signal_covariance'],np.zeros((n,n)))
                self.assertEqual(r['contrast_estimate'],[None]*n)
        g=np.diag([1.,0.]);g[0,1]=g[1,0]=1e-30
        with self.assertRaisesRegex(ValueError,'zero Gram diagonal'):
            finite_nuisance_quotient(g,np.zeros(2),signal_dim=1)
        with self.assertRaisesRegex(ValueError,'zero Gram diagonal'):
            finite_nuisance_quotient(np.diag([1.,0.]),[0,1e-30],signal_dim=1)

    def test_full_rank_row_reference_signal_and_nuisance_units(self):
        rng=np.random.default_rng(125);d=rng.normal(size=(30,3));h=rng.normal(size=(30,2))
        y=rng.normal(size=30)
        qh,_=np.linalg.qr(h);dr=d-qh@(qh.T@d);yr=y-qh@(qh.T@y)
        base_cov=np.linalg.inv(dr.T@dr);base_est=np.linalg.lstsq(dr,yr,rcond=None)[0]
        k=np.array([[1.,-2.,3.]])
        for sd,sh in [(np.array([1e-6,1.,1e6]),np.array([1e6,1e-6])),
                      (np.array([1e6,1e-6,1.]),np.array([1e-6,1e6]))]:
            x=np.column_stack([d*sd,h*sh])
            r=finite_nuisance_quotient(x.T@x,x.T@y,signal_dim=3,contrasts=k*sd)
            np.testing.assert_allclose(r['projected_signal_estimate'],base_est/sd,rtol=1e-12,atol=1e-12)
            np.testing.assert_allclose(r['projected_signal_covariance'],base_cov/sd[:,None]/sd,rtol=1e-12,atol=1e-12)
            np.testing.assert_allclose(r['contrast_estimate'],k@base_est,atol=1e-12)
            np.testing.assert_allclose(r['contrast_covariance'],k@base_cov@k.T,atol=1e-12)
            np.testing.assert_array_equal(r['estimable_projector'],np.eye(3))

    def test_normalized_validation_and_relative_score_checks(self):
        for rtol in (0,1,-1,np.nan,np.inf):
            with self.assertRaises(ValueError):
                finite_nuisance_quotient(np.eye(2),np.zeros(2),signal_dim=1,rtol=rtol)
        # Tiny incompatible scores must not be forgiven by an absolute unit floor.
        g=np.ones((2,2))
        with self.assertRaisesRegex(ValueError,'quotient score outside'):
            finite_nuisance_quotient(g,[1e-100,0],signal_dim=1)
        g=np.eye(3);g[1:,1:]=1
        with self.assertRaisesRegex(ValueError,'nuisance null score'):
            finite_nuisance_quotient(g,[0,1e-100,-1e-100],signal_dim=1)
        g=np.eye(3);g[1:,1:]=1;g[0,1]=g[1,0]=.1
        with self.assertRaises(ValueError):
            finite_nuisance_quotient(g,np.zeros(3),signal_dim=1)
        g=np.eye(2);g[0,1]=.1
        with self.assertRaisesRegex(ValueError,'symmetric'):
            finite_nuisance_quotient(g,np.zeros(2),signal_dim=1)

    def test_adaptive_mixture_against_direct_gaussian_refit(self):
        rng=np.random.default_rng(21);x=rng.normal(size=(12,3));y=rng.normal(size=12);delta=np.array([2.,-1.,.5]);p=4.
        cs=[np.eye(12),np.diag(np.linspace(.5,3,12))]
        def refit(data):
            rows=[];logw=[]
            for c in cs:
                ci=np.linalg.inv(c);v=np.linalg.inv(x.T@ci@x+np.eye(3)/p);m=v@x.T@ci@data
                s=c+p*x@x.T;logw.append(-.5*(np.linalg.slogdet(s)[1]+data@np.linalg.solve(s,data)))
                rows.append(dict(posterior_mean_uasyr=m.tolist(),posterior_cov_uas2yr2=v.tolist()))
            w=np.exp(np.array(logw)-max(logw));w/=w.sum()
            for row,weight in zip(rows,w):row['posterior_hyper_weight']=weight
            return rows,w@np.array([r['posterior_mean_uasyr'] for r in rows]),w
        rows,_,_=refit(y);_,direct,weights=refit(y+x@delta)
        reconstructed,reweights=shifted_mixture(rows,delta,p)
        np.testing.assert_allclose(reconstructed,direct,atol=1e-12)
        np.testing.assert_allclose(reweights,weights,atol=1e-12)

    def test_conditional_covariance_monte_carlo(self):
        rng=np.random.default_rng(87);x=rng.normal(size=(60,7));g=x.T@x
        r=finite_nuisance_quotient(g,np.zeros(7),signal_dim=3);v=np.array(r['projected_signal_covariance'])
        # Score-space Monte Carlo tests the estimator covariance, not empirical sky coverage.
        e=rng.normal(size=(12000,60));hi=np.linalg.inv(g[3:,3:]);a=np.column_stack([np.eye(3),-g[:3,3:]@hi])
        estimates=e@x@a.T@v
        np.testing.assert_allclose(np.diag(np.cov(estimates,rowvar=False)),np.diag(v),rtol=.04)


if __name__=='__main__':unittest.main()
