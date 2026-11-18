import numpy as np
import pytest
from scripts.r67.likelihood_contract import GaussianProbe,source_joint_ready,nuisance_profile_fisher


def probe(name,physical,source,qualified=True):
    return GaussianProbe(name=name,physical_parameter=physical,frame="ICRS",
                         epoch="2026",source_group=source,
                         covariance_qualified=qualified,response_qualified=qualified,
                         C=np.eye(2),J=np.eye(2))


def test_incompatible_physical_targets_not_fused():
    p=probe("Gaia","observer_acceleration","gaia")
    q=probe("CF4","matter_velocity","cf4")
    assert source_joint_ready([p,q])["status"]=="INCOMPATIBLE_PHYSICAL_REFERENT"


def test_same_sky_requires_full_covariance():
    p=probe("CommanderPR3","radiation_stress","cmb")
    q=probe("CommanderPR4","radiation_stress","cmb")
    assert source_joint_ready([p,q])["status"]=="SHARED_SOURCE_CROSS_COVARIANCE_REQUIRED"
    C=np.eye(4);C[0,2]=C[2,0]=.4
    assert source_joint_ready([p,q],C)["status"]=="JOINT_COVARIANCE_PROVENANCE_REQUIRED"
    assert source_joint_ready([p,q],C,joint_covariance_qualified=True,
                              provenance="trusted same-sky cross-covariance")["status"]=="JOINT_COVARIANCE_EXPLICIT"


def test_nuisance_projection_exact():
    J=np.eye(3);C=np.eye(3);N=np.ones((3,1))
    v=nuisance_profile_fisher(J,C,N)
    assert v["rank"]==2
    np.testing.assert_allclose(v["F"]@np.ones(3),0,atol=1e-13)


def test_missing_source_response_blocks():
    a=probe("Gaia","observer_acceleration","gaia")
    b=probe("VLBA","observer_acceleration","vlba",False)
    assert source_joint_ready([a,b])["status"]=="UNQUALIFIED_RESPONSE_OR_COVARIANCE"


def test_frame_epoch_must_match():
    a=probe("A","shear","one")
    b=GaussianProbe("B","shear","Galactic","CMB","two",True,True,np.eye(2),np.eye(2))
    assert source_joint_ready([a,b])["status"]=="INCOMPATIBLE_PHYSICAL_REFERENT"


def test_not_claimed_physical_equivalence():
    a=probe("R65Radio","count_dipole","radio")
    b=probe("R63CF4","count_dipole","cf4")
    assert source_joint_ready([a,b])["status"]=="INDEPENDENCE_NOT_ESTABLISHED"
    assert source_joint_ready([a,b],independence_qualified=True,
                              provenance="operator-provided source-overlap study")["status"]=="BLOCK_DIAGONAL_CONDITIONALLY_ALLOWED"
    # Caller assertion alone is not scientific evidence. Do not set it automatically.

def test_joint_covariance_inconsistent_diagonal_blocks_rejected():
    p=GaussianProbe("A","observable","ICRS","2026","shared",True,True,4*np.eye(2),np.eye(2))
    q=GaussianProbe("B","observable","ICRS","2026","shared",True,True,4*np.eye(2),np.eye(2))
    bad=np.eye(4)
    with pytest.raises(ValueError,match="conflicts"):
        source_joint_ready([p,q],bad,joint_covariance_qualified=True,
                           provenance="even a false label must fail structural checks")


def test_unqualified_joint_covariance_still_blocked():
    a=probe("A","observable","one")
    b=probe("B","observable","two")
    assert source_joint_ready([a,b],np.eye(4))["status"]=="JOINT_COVARIANCE_PROVENANCE_REQUIRED"
