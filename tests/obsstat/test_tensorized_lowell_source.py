"""PR262 typed STF2/STF3 source channel, anchor and missing physics regressions."""
import numpy as np
import pytest

from common.typefree_functionals import evaluate_paired_anchor,anchor_support
from obsstat.tensorized_lowell_source import (
  TensorSourceError,empirical_irrep_anchor,record,empirical_gauge_image,
  physical_unmeasured_tensor_image,measured_directional_support
)

SHA="a"*64

def cohort(n=99,seed=8):
    rng=np.random.default_rng(seed)
    c=np.eye(12)*0.2+rng.normal(size=(12,12))*.08
    x=rng.standard_normal((n,12))@c
    return x,np.arange(n,dtype=np.int32)


@pytest.mark.parametrize("ell", [2,3])
def test_source_typed_tensor_ranks_and_exact_ellipsoid_gauge(ell):
    x,ids=cohort()
    sl=slice(0,5) if ell==2 else slice(5,12)
    body=empirical_irrep_anchor(x[:,sl],ell=ell,source_hash=SHA)
    assert body.spec.rank==ell
    assert body.spec.parity==("EVEN_STF2" if ell==2 else "ODD_STF3")
    v=x[0,sl]
    o=evaluate_paired_anchor(record(body,"one-same-source",v))
    assert o.status=="DEFINED"
    q=np.sqrt((v-body.source_mean)@body.invcovariance@(v-body.source_mean))
    assert o.gauge==pytest.approx(q,abs=2e-12)
    assert anchor_support(body.body,np.eye(2*ell+1)[0])==pytest.approx(
        np.sqrt(body.covariance[0,0]),abs=1e-13)
    f=measured_directional_support(body,v,np.ones(2*ell+1))
    assert np.isfinite(f["F_directional_support_ratio"])
    assert f["status"].startswith("EMPIRICAL")


def test_999_source_gauge_empirical_mass_is_not_physical_posterior():
    x,ids=cohort(999)
    a=empirical_irrep_anchor(x[:,:5],ell=2,source_hash=SHA)
    z=empirical_gauge_image(a,x[:,:5],ids,thresholds=(1.,2.,3.))
    assert z["source"].law_kind=="EMPIRICAL"
    assert len(z["gauge"])==999
    assert z["image"].undefined_mass==0
    assert z["tail"][0]["source_empirical_known_exceedance_mass"]>0
    assert all(t["status"].endswith("NOT_PLANCK_P_VALUE") for t in z["tail"])
    phys=physical_unmeasured_tensor_image(a,ids)
    assert phys["physical_tensor_image_undefined_mass"]==pytest.approx(1.)
    assert phys["physical_tensor_exceedance_outer"]==[0.,1.]


def test_source_channel_rejects_illegal_kinematic_imputation_and_duplicate_ids():
    x,ids=cohort()
    a=empirical_irrep_anchor(x[:,:5],ell=2,source_hash=SHA)
    with pytest.raises(TensorSourceError):
        empirical_irrep_anchor(x[:,:5],ell=4,source_hash=SHA)
    with pytest.raises(TensorSourceError):
        empirical_gauge_image(a,x[:,:5],np.zeros(len(ids)))
    with pytest.raises(TensorSourceError):
        measured_directional_support(a,x[0,:5],np.ones(7))
    with pytest.raises(TensorSourceError):
        physical_unmeasured_tensor_image(a,np.arange(len(ids)-1))
