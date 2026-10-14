"""Bounded BK18 fixed-fiducial HL falsifiers; no cosmological fit."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

PATH=Path(__file__).resolve().parents[2]/"scripts/reboot_bk18_fixed_fiducial.py"
spec=importlib.util.spec_from_file_location("bk18_fixed_fiducial_candidate",PATH)
bk=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=bk
spec.loader.exec_module(bk)


def pair_fixture():
    names=[f"map{i}_B" for i in range(11)]
    pairs=[(i,j) for i in range(11) for j in range(i,11)]
    order=[names[i]+"x"+names[j] for i,j in pairs]
    settings={name:" ".join(order) for name in
              ("cl_fiducial_order","cl_hat_order","cl_noise_order","covmat_cl","bin_window_in_order")}
    settings.update(map_names=" ".join(names),map_fields=" ".join(["B"]*11))
    return settings,names,order,pairs


def test_native_fiducial_zero_and_diagonal_closed_forms():
    F=np.diag(np.linspace(.3,3,11))
    X,Fhalf,lam=bk.hl_matrix(F,F)
    assert np.linalg.norm(X,ord="fro") <= 1e-13*np.linalg.norm(F,ord="fro")
    assert np.allclose(lam,1,rtol=1e-13,atol=1e-13)
    for alpha in (.8,1.2):
        X,Fhalf,_=bk.hl_matrix(F,alpha*F)
        g=np.sign(alpha-1)*np.sqrt(2*(alpha-np.log(alpha)-1))
        assert np.allclose(X,g*F,rtol=1e-9,atol=1e-12)
        parity=bk.native_transform_parity(F,alpha*F,Fhalf,X)
        assert parity["relative_to_native_fiducial_unit"]<1e-10


def test_11_map_pair_and_bin_order_and_no_sqrt2():
    settings,names,order,pairs=pair_fixture()
    got_names,got_order,got_pairs=bk.release_order(settings)
    assert (got_names,got_order,got_pairs)==(names,order,pairs)
    values=np.arange(1,67,dtype=float)
    matrix=bk.pair_matrix(values,pairs)
    assert np.array_equal(bk.pair_vector(matrix,pairs),values)
    cross=pairs.index((0,1))
    assert matrix[0,1]==values[cross]  # never multiply by sqrt(2)
    bins=np.arange(9*66).reshape(9,66)
    assert bins.reshape(-1)[66+cross]==bins[1,cross]
    wrong=dict(settings);wrong["covmat_cl"]=" ".join(order[::-1])
    with pytest.raises(ValueError,match="order mismatch"):
        bk.release_order(wrong)
    wrong=dict(settings);wrong["map_fields"]=" ".join(["B"]*10+["E"])
    with pytest.raises(ValueError,match="BB-only"):
        bk.release_order(wrong)


def test_joint_covariance_permutation_and_inconsistent_order():
    x=np.array([1.,2.,-1.,3.,.5,-2.])
    a=np.array([[2.,.1,0,0,0,0],[.1,1.8,.3,0,0,0],[0,.3,2.2,.2,0,0],
                [0,0,.2,1.7,.4,0],[0,0,0,.4,2.,.1],[0,0,0,0,.1,1.5]])
    cov=a@a.T
    p=np.array([2,0,5,3,1,4])
    q=bk.quadratic(x,cov)
    assert bk.quadratic(x[p],cov[np.ix_(p,p)])==pytest.approx(q,rel=1e-12)
    assert abs(bk.quadratic(x[p],cov)-q)>1e-5  # mismatched order is detectable


def test_nine_bin_joint_hl_vector_native_q_parity():
    _,names,order,pairs=pair_fixture()
    identity_pairs=np.array([1. if i==j else 0. for i,j in pairs])
    fid=np.tile(identity_pairs,(9,1))
    release={"fiducial":fid,"hat":1.2*fid,"noise":np.zeros_like(fid),
             "pairs":pairs,"map_names":names,"pair_order":order,
             "covariance":np.eye(594),"covariance_antisymmetry":0.,
             "window_tails":[{"bin":i+1,"nonzero_outside_ell_2_600":0,
                              "outside_abs_weight_fraction":0.,"outside_frobenius_fraction":0.}
                             for i in range(9)]}
    result,arrays=bk.evaluate(release)
    g=np.sign(.2)*np.sqrt(2*(1.2-np.log(1.2)-1))
    assert result["Q_HL"]==pytest.approx(9*11*g*g,rel=1e-9)
    assert result["Q_linear_residual_separate_gaussian_descriptor"]==pytest.approx(9*11*.2**2)
    assert result["native_vector_parity"]["absolute_Q_difference"]<=1e-8*(1+result["Q_HL"])
    assert result["native_vector_parity"]["whitened_vector_difference"]<=1e-6*(1+np.sqrt(result["Q_HL"]))
    assert arrays["x_HL_uK2"].shape==(9,66)
    release["hat"]=fid.copy()
    zero,_=bk.evaluate(release)
    assert zero["Q_HL"]<1e-8


def test_spd_complex_nonfinite_and_antisymmetry_rejection():
    f=np.eye(11)
    with pytest.raises(np.linalg.LinAlgError):
        bk.hl_matrix(f,np.diag([0.]+[1.]*10))
    with pytest.raises(ValueError,match="real"):
        bk.hl_matrix(f.astype(complex),f)
    bad=f.copy();bad[0,1]=.01
    with pytest.raises(ValueError,match="antisymmetry"):
        bk.hl_matrix(bad,f)
    with pytest.raises(ValueError,match="finite"):
        bk.pair_matrix(np.full(66,np.nan),pair_fixture()[3])
    with pytest.raises(ValueError,match="positive"):
        bk.hl_g(np.array([-.1,1.]))


def test_actual_bb_source_one_bin_native_parity_and_window_tail():
    root=Path.cwd()
    source=root/bk.RELEASE_REL/bk.DATA_REL/"BK18lf_dust.dataset"
    if not source.exists():
        pytest.skip("installed exact BK18 BB-only source absent")
    release=bk.load_release(root)
    assert len(release["map_names"])==11
    assert len(release["pair_order"])==66
    assert release["covariance"].shape==(594,594)
    assert release["covariance_antisymmetry"]<=1e-10
    assert release["window_tails"][0]["nonzero_outside_ell_2_600"]>0
    F=bk.pair_matrix(release["fiducial"][0]+release["noise"][0],release["pairs"])
    H=bk.pair_matrix(release["hat"][0]+release["noise"][0],release["pairs"])
    X,Fhalf,_=bk.hl_matrix(F,H)
    assert bk.native_transform_parity(F,H,Fhalf,X)["relative_to_native_fiducial_unit"]<1e-10
