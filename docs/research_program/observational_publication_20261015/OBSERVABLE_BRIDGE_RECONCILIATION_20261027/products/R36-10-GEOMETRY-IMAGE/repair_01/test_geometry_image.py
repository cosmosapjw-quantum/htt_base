"""Focused contract falsifiers for the repaired instantaneous geometry consumer."""
import json
from pathlib import Path
import numpy as np
import pytest

from geometry_image import B, E, TOL, center_shear, class_a_ric, derivatives, frame, joint, svec, unsvec


def test_matched_scalar_does_not_fix_tensor_and_flat_presentation():
    ii = np.diag([1., 0, 0]); vii = np.diag([0., 2, 1])
    a = np.zeros(3); s = np.diag([.1, -.05, -.05]); e = 4697/400
    one = frame(ii,a,2.,s,e,a)
    two = frame(vii,a,2.,s,e,a)
    assert abs(one["scalar"]-two["scalar"]) <= TOL
    assert np.linalg.norm(one["ricci"]-two["ricci"]) > 1
    for n in (np.zeros((3,3)),np.diag([0.,1,1])):
        assert np.array_equal(frame(n,a,2.,np.zeros((3,3)),12.,a)["riemann"], np.zeros((3,3,3,3)))


def test_invalid_jacobi_is_rejected_at_tiny_si_scale():
    n = np.diag([1.,.7,1.1]); a = np.array([.3,0,0])
    with pytest.raises(ValueError,match="INVALID_JACOBI"):
        frame(n,a,2.,np.zeros((3,3)),12.,np.zeros(3))
    valid = frame(np.diag([0.,.7,1.1]),a,2.,np.zeros((3,3)),12.,np.zeros(3))
    assert np.isclose(valid["ricci"][1,2],-.12)


def test_codazzi_signed_flux_and_adm_identity():
    a = np.array([.4,0,0]); s = np.diag([.2,-.1,-.1])
    got = frame(np.zeros((3,3)),a,2.,s,11.,np.zeros(3))
    assert np.isclose(got["momentum"][0],6*.4*.1)
    assert np.linalg.norm(got["momentum"]-got["codazzi"]) <= TOL
    assert abs(got["adm_residual"]-2*got["hamiltonian_residual"]) <= TOL


def test_quadratic_hessian_recovers_direct_map_and_complex_step():
    z = np.r_[svec(np.diag([0.,2,1])),2.,[.1/np.sqrt(2),.15/np.sqrt(6),0,0,0]]
    j,h = derivatives(z)
    delta = np.arange(12)*.001
    direct = joint(z+delta)
    exact = joint(z)+j@delta+.5*np.einsum("i,kij,j->k",delta,h,delta)
    assert np.linalg.norm(direct-exact) <= TOL*np.linalg.norm(direct)
    assert np.isclose(np.linalg.norm(unsvec(z[:6])),np.linalg.norm(z[:6]))
    assert len(B)==5 and E[0,1,2]==1


def test_saved_flat_centers_and_type_i_joint_derivative_repair():
    here = Path(__file__).resolve().parent
    table = json.loads((here / "TABLE.json").read_text())
    base = json.loads((here.parent / "TABLE.json").read_text())
    assert np.array_equal(center_shear("I"),np.zeros((3,3)))
    assert np.array_equal(center_shear("flatVII0"),np.zeros((3,3)))
    for name in ("I","flatVII0"):
        center = table["images"][name]
        canonical = table["controls"][name]
        assert np.array_equal(np.array(center["z0"])[7:],np.zeros(5))
        assert center["Y0"][6] == canonical["density_bar"] == 12
        assert np.array_equal(np.array(center["center_S_bar"]),np.zeros((3,3)))
        assert np.array_equal(np.array(canonical["S_bar"]),np.zeros((3,3)))
        assert np.array_equal(np.array(canonical["extrinsic"]),-2*np.eye(3))
        assert np.array_equal(np.array(center["joint_H"]),np.array(base["images"][name]["joint_H"]))
        assert center["geometry_J"] == base["images"][name]["geometry_J"]
        assert np.array_equal(np.array(center["Y0"])[:6],np.array(base["images"][name]["Y0"])[:6])
    only_h=np.zeros((10,12)); only_h[6,6]=12
    assert np.linalg.norm(np.array(table["images"]["I"]["joint_J"])-only_h) <= TOL*12
    assert table["images"]["I"]["joint_svd"]["rank"] == 1
    assert [table["images"][n]["joint_svd"]["rank"] for n in ("II","VII0matched","I","flatVII0")] == [9,10,1,6]
    assert abs(table["matched_orbit_separation"]-base["matched_orbit_separation"]) <= TOL*max(1,base["matched_orbit_separation"])
    for name in ("II","VII0matched"):
        assert np.array_equal(np.array(table["images"][name]["Y0"]),np.array(base["images"][name]["Y0"]))
        assert np.array_equal(np.array(table["images"][name]["geometry_J"]),np.array(base["images"][name]["geometry_J"]))


def test_ricci_probe_parity_and_matched_full_image_preservation():
    here = Path(__file__).resolve().parent
    old = here.parent / "UNCERTAINTY_PROBES.jsonl"
    new = here / "UNCERTAINTY_PROBES.jsonl"
    with old.open() as a, new.open() as b:
        pairs = list(zip(a,b,strict=True))
    assert len(pairs) == 4*577
    for old_line,new_line in pairs:
        o,n=json.loads(old_line),json.loads(new_line)
        assert (o["center"],o["probe"],o["xi"]) == (n["center"],n["probe"],n["xi"])
        assert o["z"][:7] == n["z"][:7]
        assert o["directY"][:6] == n["directY"][:6]
        if o["center"] in ("II","VII0matched"):
            assert o["directY"] == n["directY"]
