import unittest
import numpy as np
from numpy.testing import assert_allclose
from scripts.r105.cf4_coras_marks import fold_score


class TestCompiledFields(unittest.TestCase):
    def test_joint_train_test_conditioning_with_competing_fields(self):
        # Each row gives the train evidence, heldout marks+pattern evidence,
        # and heldout inclusion pattern probability for one empirical field.
        vals=np.array([[.10,.15,.7],[.4,.08,.2],[.3,.025,.25]])
        use=np.array([False,True,True])
        got=fold_score(np.log(vals),use)
        a,b,c=vals[use].T
        assert_allclose(np.exp(got["logscore"]),(a@b)/(a@c))
        assert_allclose(got["effective_training_components"],sum(a)**2/(a@a))

    def test_single_field_cancels_its_train_evidence(self):
        data=np.array([[-9999.,-15.,-9.],[-8000.,-4.,-3.]])
        assert_allclose(fold_score(data,[True,False])["logscore"],-6.)
