import json
from pathlib import Path

import numpy as np
import pytest

from htt.core.teff_invariants import (
    fourth_moment, fourth_moment_gradient, legacy_coefficients,
    orthonormal_stf_basis,
)
from htt.core.teff_extended import TeffMomentMap
from obsstat.r2_cmb_product_bridge import (
    dipole_stf_from_real_harmonics, finite_ansatz_statistic,
    reduced_same_sky_diagnostic, released_product_response,
)
from obsstat.r7_cmb_product_response import real_design


def sphere():
    mu, w = np.polynomial.legendre.leggauss(24)
    phi = np.arange(40) * 2*np.pi/40
    mu, phi = np.meshgrid(mu, phi, indexing="ij")
    n = np.stack((np.sqrt(1-mu**2)*np.cos(phi),
                  np.sqrt(1-mu**2)*np.sin(phi), mu), axis=-1).reshape(-1, 3)
    return n, np.repeat(w/80, 40)


@pytest.mark.parametrize("seed", range(5))
def test_exact_quadrature_rotation_gradient(seed):
    rng = np.random.default_rng(seed)
    d = rng.normal(size=3)*.1
    S = np.einsum("a,aij->ij", rng.normal(size=5)*.08, orthonormal_stf_basis())
    n, weights = sphere()
    field = 1+n@d+np.einsum("ni,ij,nj->n", n, S, n)
    assert fourth_moment(d, S) == pytest.approx(weights@field**4, abs=4e-15)
    R, _ = np.linalg.qr(rng.normal(size=(3,3)))
    assert fourth_moment(R@d, R@S@R.T) == pytest.approx(fourth_moment(d,S), abs=2e-15)
    gd, gS = fourth_moment_gradient(d,S)
    dd = rng.normal(size=3)
    ds = np.einsum("a,aij->ij", rng.normal(size=5), orthonormal_stf_basis())
    h = 1e-5
    num = (fourth_moment(d+h*dd,S+h*ds)-fourth_moment(d-h*dd,S-h*ds))/(2*h)
    assert num == pytest.approx(gd@dd+np.sum(gS*ds), rel=1e-8, abs=1e-9)


def test_legacy_alpha_dispatch_only():
    obj = TeffMomentMap(24,40)
    args = (.12,-.04,.03,.09)
    d,S = legacy_coefficients(*args)
    n,w = sphere()
    assert obj.moment(*args) == fourth_moment(d,S)
    assert obj.moment(*args) == pytest.approx(w@(1+n@d+np.einsum("ni,ij,nj->n",n,S,n))**4, abs=3e-15)
    assert obj.moment(*args,alpha=3.2) == pytest.approx(np.sum(obj.theta_field(*args)**3.2*obj.weights))
    # Alpha4 dispatch does not consult the quadrature grid.
    obj.weights[:] = 0
    assert obj.moment(*args) == fourth_moment(d,S)
    assert obj.moment(*args,alpha=3) == 0


def test_harmonic_crosswalk_units_and_positive_domain():
    c1=np.array([.1,.2,-.04]);c2=np.array([.02,.05,.07,-.01,.03])
    d,S=dipole_stf_from_real_harmonics(c1,c2)
    d2,S2=dipole_stf_from_real_harmonics(c1*1e6,c2*1e6,units="microK")
    np.testing.assert_allclose(d,d2,atol=1e-17)
    np.testing.assert_allclose(S,S2,atol=1e-17)
    n,_=sphere()
    np.testing.assert_allclose(real_design(n,2)[:,1:]@np.r_[c1,c2], n@d+np.einsum("ni,ij,nj->n",n,S,n), atol=1e-15)
    a=finite_ansatz_statistic(T0=2.7,dipole=d,quadrupole=S,source_id="explicit",frame="GALACTIC")
    b=finite_ansatz_statistic(T0=2.7e6,dipole=d*1e6,quadrupole=S*1e6,units="microK",source_id="explicit",frame="GALACTIC")
    assert a["F4"]==b["F4"]
    assert a["full_field_F4_absolute_error_bound"] is None
    with pytest.raises(ValueError,match="positive-temperature"):
        finite_ansatz_statistic(T0=1,dipole=[2,0,0],quadrupole=np.zeros((3,3)),source_id="x",frame="G")


def test_omitted_nonlinear_envelope():
    n,w=sphere();d=np.array([.1,.03,0]);S=np.diag([.03,-.01,-.02]);r=.02
    a=finite_ansatz_statistic(T0=1,dipole=d,quadrupole=S,source_id="x",frame="G",omitted_sup_norm=r)
    field=1+n@d+np.einsum("ni,ij,nj->n",n,S,n)
    total=w@(field+r*np.sin(4*n[:,0]))**4
    assert abs(total-a["F4"])<=a["full_field_F4_absolute_error_bound"]


def test_release_processor_refusal_and_injection(monkeypatch):
    import obsstat.r7_cmb_product_response as response
    n,w=sphere();monkeypatch.setattr(response,"pixel_fit_geometry",lambda:(n,real_design(n)))
    d=np.array([.01,.02,.03]);S=np.diag([.03,-.01,-.02])
    temperature=lambda v:2.7+v@d+np.einsum("ni,ij,nj->n",v,S,v)
    product={"product_id":"CONTROL","release":"synthetic injection","frame":"GALACTIC","units":"K",
        "correction":"REMOVE_ELL01","channel_convention":"SIGNED_TEMPERATURE_ANISOTROPY","beam":"INJECTED_HALF",
        "map_source_id":"injection","mask_source_id":"mask-v1","pixel_policy":"test-sphere","dipole_removal":"explicit processor"}
    source={"source_id":"absolute-injection","units":"K","frame":"GALACTIC",
            "temperature_convention":"ABSOLUTE_THERMODYNAMIC_TEMPERATURE","temperature":temperature}
    with pytest.raises(ValueError,match="processor unavailable"):
        released_product_response(product,source,np.zeros(3),{})
    processing={"pixel_processor":lambda sky:.5*(sky-2.7-n@d),
                "processor_source_id":"remove01-half","mask_weights":(n[:,2]>-.6).astype(float),"mask_source_id":"mask-v1"}
    result=released_product_response(product,source,np.zeros(3),processing)
    qfield=.5*np.einsum("ni,ij,nj->n",n,S,n)
    np.testing.assert_allclose(real_design(n)@result.full_coefficients,qfield,atol=2e-15)
    assert result.fit_rank==36
    processing["mask_source_id"]="wrong"
    with pytest.raises(ValueError,match="identity mismatch"):
        released_product_response(product,source,np.zeros(3),processing)


def test_actual_reduced_controls_refuse_full_field():
    root=Path(__file__).resolve().parents[2]
    base=root/"docs/generated/tensor_joint_r8/owned_controls/cmb"
    out=reduced_same_sky_diagnostic(base/"cmb_controls.npz",base/"cmb.json")
    assert len(out["contrasts"])==6
    assert out["coverage"]["common_valid_pixels"]==36433
    assert not out["product_independence"]
    assert out["conditional_sensitivity"] is None
    assert out["full_field_F4_status"].startswith("HOLD")
    with pytest.raises(ValueError,match="both explicit"):
        reduced_same_sky_diagnostic(base/"cmb_controls.npz",base/"cmb.json",T0_K=2.7)
    out=reduced_same_sky_diagnostic(base/"cmb_controls.npz",base/"cmb.json",T0_K=2.72548,
        dipole_K=[.003,0,0],dipole_source_id="synthetic-sensitivity-not-measurement")
    assert len(out["conditional_sensitivity"])==4
    assert all(v["omitted_modes_sup_norm"] is None for v in out["conditional_sensitivity"])
