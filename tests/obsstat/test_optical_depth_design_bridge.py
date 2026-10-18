"""Source-identifiability theorem checks, not cosmological claims."""
from __future__ import annotations
import numpy as np
import pytest
from obsstat.optical_depth_design_bridge import (
    OpticalDepthDesignError, angular_optical_design, optical_depth_capability,
)


def _n(seed=4, count=70):
    rng=np.random.default_rng(seed)
    sky=rng.normal(size=(count,3))
    return sky/np.linalg.norm(sky,axis=1,keepdims=True)


def test_equal_shell_only_9_angular_degrees():
    n=_n()
    r=np.full(len(n),140.)
    x=optical_depth_capability(n,r,distance_reference=140.)
    assert x['design_rank']==9
    assert x['weakest_principal_sine']<1e-7
    assert x['intercept_rank']==4
    assert x['slope_rank']==9


def test_duplicated_directions_at_two_distances_full13_rank():
    n=_n(count=30)
    r=np.r_[np.full(30,80.),np.full(30,180.)]
    x=optical_depth_capability(np.r_[n,n],r,distance_reference=120.)
    assert x['design_rank']==13
    assert x['weakest_principal_sine']>.2


def test_free_method_zero_points_remove_intercept_one_degree():
    n=_n(count=75)
    r=np.linspace(60.,260.,75)
    methods=np.array(['FP']*25+['TF']*25+['SN']*25)
    x=optical_depth_capability(n,r,distance_reference=140.,
        row_weights=np.linspace(.8,1.2,75),method_groups=methods)
    assert x['design_rank']==13
    assert x['method_projected_rank']==12
    assert x['method_projection_max_constant_residual']<1e-12


def test_global_positive_reweighting_preserves_rank_and_angles():
    n=_n(count=75)
    r=np.linspace(60,240,75)
    w=np.linspace(.5,1.5,75)
    a=optical_depth_capability(n,r,distance_reference=125.,row_weights=w)
    b=optical_depth_capability(n,r,distance_reference=125.,row_weights=20*w)
    assert a['design_rank']==b['design_rank']==13
    np.testing.assert_allclose(a['principal_cosines'],b['principal_cosines'],atol=2e-14)


def test_bad_weights_fail_closed():
    n=_n(count=75)
    r=np.linspace(60,240,75)
    w=np.ones(75)
    w[-1]=0.
    with pytest.raises(OpticalDepthDesignError):
        optical_depth_capability(n,r,distance_reference=125.,row_weights=w)
