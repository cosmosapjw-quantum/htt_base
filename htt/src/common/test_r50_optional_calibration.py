"""Missing calibration must stay absent in the shared five-view builder."""
import numpy as np
import pytest

from common.htt_five_variable_state import construct_r42_five_variable_state
from common.r39_identifiability import PARAM_NAMES_17
from tests.r42.test_five_variable_repair import make_test_joint_state_bundle_helper


def test_optional_null_is_absent_and_shear_anchor_consistent():
    _, _, bundle = make_test_joint_state_bundle_helper()
    out = construct_r42_five_variable_state(bundle, np.zeros((10,17)), PARAM_NAMES_17)
    assert set(out.exceedance_surfaces_Pi) == {"BETA_MO_NORM"}
    assert out.anchors_Q["shear_sigma"].norm_bound is None
    assert out.support_profiles_F["SHEAR_SIGMA"].occupancy_ratios is None


def test_empty_supplied_null_is_rejected():
    _, _, bundle = make_test_joint_state_bundle_helper()
    with pytest.raises(ValueError,match="N>=2"):
        construct_r42_five_variable_state(bundle,np.zeros((10,17)),PARAM_NAMES_17,
            matched_null_samples=np.empty((0,3)))
