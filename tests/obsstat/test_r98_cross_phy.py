"""Algebraic sign/normalization tests and conditional full-device regressions."""
import numpy as np
import pytest
from scripts.r98 import cross_phy as x


def test_positive_sky_dipole_and_measure():
    _,_,nh,w = x.bh.r97.gl_sphere_grid(16)
    b=np.array([-.18,.08,.13])
    m,S,V=x.moments(1+nh@b,nh,w)
    np.testing.assert_allclose(m,b/3,atol=5e-15)
    np.testing.assert_allclose(S,np.eye(3)/3,atol=5e-15)
    assert np.linalg.eigvalsh(V)[0]>0
    with pytest.raises(ValueError):
        x.moments(np.zeros_like(w),nh,w)


def test_finite_boost_energy_moment():
    _,_,nh,w=x.bh.r97.gl_sphere_grid(32)
    beta=np.array([-.16,.29,-.22])
    D=np.sqrt(1-beta@beta)/(1-nh@beta)
    m,_,_=x.moments(D**4,nh,w)
    np.testing.assert_allclose(m,4*beta/(3+beta@beta),atol=4e-14,rtol=0)


def test_grouped_law_rejects_split_noise_identity():
    rows={"a":[2,0,1,1,1,0,2,3],"b":[2,1,2,2,2,0,3,4]}
    with pytest.raises(ValueError,match="split"):
        x.grouped_cmb({"oof_by_cmb_id":rows})


def test_signed_codazzi_and_rank_stratum():
    v=x.codazzi_route()
    assert [k["rank"] for k in v["near_exception"]]==[3,2,3]
    for item in v["near_exception"]:
        assert item["R90_same_n_difference"]>1e-3
        assert item["R90_flipped_n_difference"]<1e-18
    assert v["compensated_Codazzi_initial_norm"]<1e-18


@pytest.fixture(scope="module")
def full():
    if not (x.cf.r97.RAW_CF4/"table4.dat").exists():
        pytest.skip("device CF4 full input unavailable")
    return x.compute()


def test_CF4_omitted_variable_identities(full):
    for r1,r7 in zip(full["PHY01"]["windows"],full["PHY07"]["windows"]):
        assert np.shape(r1["operator_4x5"])==(4,5)
        assert r1["closed_refit_error"]<1e-12
        assert r7["rank12"]["rank"]==12 and r7["fixed_radius_100_Mpc"]["rank"]==9
        assert r7["identity_error"]<1e-12 and r7["weighted_residual_gain"]>0


def test_full_sky_and_three_source_laws(full):
    p=full["PHY02"]
    assert p["max_abs_second_moment_32_vs_40"]<1e-12
    for case in p["conditional_bolometric_sky"].values():
        assert abs(case["trace_S"]-1)<1e-12 and case["min_covariance_eigenvalue"]>0
    assert p["observed_CMB_distinct_experiment"]["pairs"]==999
    assert p["observed_CMB_distinct_experiment"]["noise_groups"]==300
    cuts=[r for survey in full["PHY03"].values() for r in survey]
    assert len(cuts)==19 and max(r["analytic_difference_norm"] for r in cuts)<1e-12


def test_observed_and_ideal_tangent_Gaia(full):
    d=full["PHY04"]
    assert d["analytic_I_over_5_max_error"]<1e-12
    assert len(d["fits"])==10
    for r in d["fits"].values():
        assert np.shape(r["crf3_all_contrast_cov_microasyr2"])==(10,10)
        assert r["observed_weighted_gram_max_EB_abs_corr"]>.01
        assert r["shared_covariance_check_max"]<1e-11


def test_eigenframes_are_source_histories(full):
    d=full["PHY06"]
    assert set(d)=={"I","V","VII_h","VI_h"}
    assert d["VI_h"]["maximum_commutator_norm"]>.4
    for v in d.values():
        assert v["common_rotation_chi_error"]<1e-12
        assert v["minimum_top_spectral_gap"]>.04
