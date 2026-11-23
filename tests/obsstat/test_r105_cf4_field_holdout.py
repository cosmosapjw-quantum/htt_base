"""Independent selected-mark integration and finite-field prediction checks."""
import unittest
import numpy as np
from numpy.testing import assert_allclose
from scipy.integrate import quad
from scipy.special import ndtr
from scipy.stats import norm

from scripts.r105.cf4_field_holdout import components, conditional_pit, overlap, predictive


class TestR105CF4(unittest.TestCase):
    def test_exact_mixture_and_rejected_test_indicator(self):
        mu=np.array([[.2,1.,-.2,.1],[1.,-.4,1.5,-.8]])
        y=np.array([.6,np.nan,-.1,np.nan])
        s=np.array([.8,.4,.9,.6])
        a=np.array([-.4,.1,.5,1.1])
        b=-1.2
        keep=np.isfinite(y)
        tr=np.array([1,1,0,0],bool)
        j,d=components(y,mu,s,a,b,keep)
        result=predictive(j,d,tr,np.array([True,True]))
        prior=np.ones(2)*.5
        tp=prior.copy()
        tt=np.ones(2)
        ii=np.ones(2)
        for k in range(2):
            q=np.array([quad(lambda v: norm.pdf(v)*ndtr(a[i]+b*(lo+s[i]*v)),
                             -10,10,epsabs=1e-13)[0] for i,lo in enumerate(mu[k])])
            tp[k] *= norm.pdf(y[0],mu[k,0],s[0])*ndtr(a[0]+b*y[0])*(1-q[1])
            tt[k] *= norm.pdf(y[2],mu[k,2],s[2])*ndtr(a[2]+b*y[2])*(1-q[3])
            ii[k] *= q[2]*(1-q[3])
        assert_allclose(result["shared"],np.log((tp@tt)/(tp@ii)),atol=2e-13)
        assert_allclose(result["fresh"],np.log((prior@tt)/(prior@ii)),atol=2e-13)
        assert_allclose(np.exp(result["prediction_logweights"]),tp*ii/(tp@ii),atol=2e-13)

    def test_pit_positive_and_negative_slopes(self):
        mu=np.array([[-.3,.2],[.4,-.75]])
        y=np.array([-.15,.6])
        s=np.array([.65,.8])
        a=np.array([-.15,.8])
        weights=np.array([.65,.35])
        for b in (-1.3,0.,.8):
            p=conditional_pit(y,mu,s,a,b,np.log(weights),order=96)
            expected=[]
            for i in range(2):
                val=0.
                for w,m in zip(weights,mu[:,i]):
                    fn=lambda t:norm.pdf(t)*ndtr(a[i]+b*(m+s[i]*t))
                    val+=w*quad(fn,-10,(y[i]-m)/s[i],epsabs=1e-13)[0]/quad(fn,-10,10,epsabs=1e-13)[0]
                expected.append(val)
            assert_allclose(p,expected,rtol=0,atol=1e-5)

    def test_folds_compared_up_to_permutation(self):
        a=np.tile(np.arange(5),3)
        b=(a+2)%5
        v=overlap(a,b)
        self.assertEqual(v["same_number_rows"],0)
        self.assertEqual(v["maximum_same_after_relabelling"],15)
