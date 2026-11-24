from pathlib import Path

import numpy as np
import pytest
from scripts.r109.material_bridge import (C_SIGMA_T, MATERIAL_HEADER, conservative_material, material_stream,
                                         r105_quadrupoles, validate_cells)
from scripts.r109.native_material_sky import read_table, read_modes


def rows():
    a = np.zeros((3,len(MATERIAL_HEADER)))
    a[:,0] = [0.,1.,3.]
    a[:,1:3] = 1.
    a[:,8] = 1.
    a[:,9] = [-1.,-.5,0.]
    return a


def test_rate_is_bare_and_chart_checked():
    a=rows()
    a[:,3]=.6
    np.testing.assert_allclose(material_stream(a,np.ones(3))[:,1]/C_SIGMA_T,1.)
    a[1,9]=1.
    with pytest.raises(ValueError):
        material_stream(a,np.ones(3))


def test_rei_flrw_fixed_ray_has_no_quadrupole():
    z=np.array([0.,.2,.6])
    a=rows()
    mono,quad=r105_quadrupoles(a[:,9],a[:,10],np.array([1.,.5,0.]),z,24)
    np.testing.assert_allclose(mono,np.log1p(z),rtol=1e-14)
    np.testing.assert_allclose(quad,0.,atol=1e-15)
    with pytest.raises(ValueError):
        r105_quadrupoles(a[:,9],a[:,10],np.ones(3),np.array([3.]))


def test_strictly_positive_thin_native_bins():
    a=rows()
    a[:,1]=1.e-8/C_SIGMA_T
    tau=np.array([3e-8,2e-8,0.])
    dtau=tau[:-1]-tau[1:]
    mass=np.exp(-tau[1:])*(-np.expm1(-dtau))
    values=np.column_stack((a[1:,0],a[:-1,0],dtau,tau[1:],tau[:-1],mass))
    names='near_t_s far_t_s delta_tau tau_near tau_far visibility_mass'
    table=read_table(names+'\n'+'\n'.join(' '.join(map(str,line)) for line in values[::-1]))
    got,info=validate_cells(a,table)
    np.testing.assert_array_equal(got,tau)
    assert info["survival_plus_visibility_error"]<2.e-16
    table['tau_near'][0] = .1
    with pytest.raises(ValueError):
        validate_cells(a,table)


def test_distinct_real_multiplicity_recovers_negative_TE(tmp_path:Path):
    pairs=("TT","TE","TB","EE","EB","BB")
    header=['ell','m']+[x+k for x in "TEB" for k in ('_re','_im')]+[x+k for x in pairs for k in ('_re','_im')]
    body=[' '.join(header)]
    for ell,m,T,E in ((0,0,0,0),(1,-1,-2,1),(1,0,0,0),(1,1,2,-1)):
        x={'T':T,'E':E,'B':0}
        prod=[v for ab in pairs for v in (x[ab[0]]*x[ab[1]],0)]
        body.append(' '.join(map(str,[ell,m,T,0,E,0,0,0,*prod])))
    (tmp_path/'modes.tsv').write_text('\n'.join(body)+'\n')
    (tmp_path/'cl.tsv').write_text('ell TT TE TB EE EB BB\n0 0 0 0 0 0 0\n1 '+f'{8/3} {-4/3} 0 {2/3} 0 0\n')
    _,cl=read_modes(tmp_path,1)
    assert cl["TE"][1]==-4/3
    (tmp_path/'cl.tsv').write_text('ell TT TE TB EE EB BB\n0 0 0 0 0 0 0\n1 0 0 0 0 0 0\n')
    with pytest.raises(ValueError):
        read_modes(tmp_path,1)


def test_rec_cell_depth_conserved_by_positive_bass_midpoint():
    knots=np.array([[0.,1.,0,0,0],[.5,2.,0,0,0],[1.,3.,0,0,0]])
    dtau=np.array([.7,1.2])
    result,stats=conservative_material(knots,dtau)
    np.testing.assert_array_equal(result[::2],knots)
    assert stats["max_abs_cell_depth_error"]<1.e-15
    with pytest.raises(ValueError):
        conservative_material(knots,np.array([0.,1.2]))
