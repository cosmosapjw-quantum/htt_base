import numpy as np
import pytest

from obsstat.r8_field_controls import GridField, galactic_positions, sample_field


def fixture_field(radius=None):
    axis = np.arange(-2., 3.)
    x, y, z = np.meshgrid(axis, axis, axis, indexing="ij")
    return GridField("fixture", (x+2*y, 3*y+z, 5*z-x), -2., 1., radius,
                     {"coordinate_frame": "GALACTIC_CARTESIAN", "velocity_frame": "CMB", "units": "km/s"})


def test_constant_field_outward_sign_and_h_conversion():
    l, b = np.array([0., 90., 180., 45.]), np.array([0., 0., 0., 30.])
    positions, directions = galactic_positions(l, b, np.ones(4), units="Mpc", h=.7)
    assert np.allclose(np.linalg.norm(positions, axis=1), .7)
    values = (np.ones((5,5,5)), np.zeros((5,5,5)), np.zeros((5,5,5)))
    field = GridField("constant", values, -2., 1., None,
                      {"coordinate_frame": "GALACTIC_CARTESIAN", "velocity_frame": "CMB", "units": "km/s"})
    result = sample_field(field, list("abcd"), positions, directions)
    assert result.sample_ids == tuple("abcd") and result.available.all()
    assert np.allclose(result.radial_km_s, np.cos(np.deg2rad(b))*np.cos(np.deg2rad(l)))
    with pytest.raises(ValueError):
        galactic_positions(l,b,np.ones(4),units="Mpc")


def test_affine_xyz_interpolation_and_row_permutation():
    p=np.array([[.2,.3,.4],[-1.3,.4,.7],[.4,-.3,-.2]])
    n=p/np.linalg.norm(p,axis=1)[:,None]
    out=sample_field(fixture_field(), ['a','b','c'],p,n)
    expected=np.column_stack((p[:,0]+2*p[:,1],3*p[:,1]+p[:,2],5*p[:,2]-p[:,0]))
    assert np.allclose(out.velocity_km_s,expected)
    assert np.allclose(out.radial_km_s,np.einsum('ij,ij->i',n,expected))
    order=np.array([2,0,1]); perm=sample_field(fixture_field(),np.array(['a','b','c'])[order],p[order],n[order])
    assert np.allclose(perm.radial_km_s,out.radial_km_s[order])


def test_missing_support_preserves_rows_and_never_zero_fills():
    p=np.array([[.1,.1,.1],[1.9,0,0],[3.,0,0],[np.nan,0,0]])
    out=sample_field(fixture_field(radius=2.),['ok','corner','cube','invalid'],p,np.tile([1.,0,0],(4,1)))
    assert out.available.tolist()==[True,False,False,False]
    assert out.rows()[1]['velocity_km_s'] is None
    assert len(out.rows())==4
    assert out.status[1]=='INTERPOLATION_CORNERS_OUTSIDE_SUPPORT'
    with pytest.raises(ValueError):
        sample_field(fixture_field(),['dup','dup'],p[:2],np.tile([1.,0,0],(2,1)))


def test_nan_corner_and_wrong_frame_are_refused():
    f=fixture_field(); f.components[0][2,2,2]=np.nan
    out=sample_field(f,['a'],np.array([[.1,.1,.1]]),np.array([[1.,0,0]]))
    assert not out.available[0] and out.rows()[0]['radial_km_s'] is None
    with pytest.raises(ValueError):
        GridField('bad',f.components,-2.,1.,None,{'coordinate_frame':'SUPERGALACTIC','velocity_frame':'CMB','units':'km/s'})
