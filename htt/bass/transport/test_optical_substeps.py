"""R105 opacity-based temporal resolution and a forced dipole independent limit."""
import math
import unittest

import numpy as np

from bass.recombination.opacity_history import OpacityHistory
from bass.transport.coupled_einstein_boltzmann import _advance_moving_photon_cell, _optical_substeps
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry


class TestOpticalSubsteps(unittest.TestCase):
    def test_piecewise_optical_integral_and_nested_midpoint(self):
        opac = OpacityHistory([-.8,-.58,-.5,-.35,-.19,-.1],[70.,1.,55.,.3,0.,.5])
        edges, depth = _optical_substeps(opac,-.8,-.1,2,1.)
        self.assertGreater(len(depth),2)
        self.assertIn(.5, np.round(edges,14))
        self.assertTrue(np.all(depth>=0.) and np.all(depth<=1.+1e-14))
        np.testing.assert_allclose(depth.sum(),opac.cells([-.8,-.1]).delta_tau[0],rtol=5e-15)
        clear=OpacityHistory([0.,1.],[0.,0.])
        e,d=_optical_substeps(clear,0.,1.,3,1.)
        np.testing.assert_allclose(e,np.linspace(0.,1.,4))
        np.testing.assert_array_equal(d,0.)
        e,d=_optical_substeps(opac,-.8,-.1,2,None)
        np.testing.assert_allclose(e,[0,.5,1])
        with self.assertRaises(ValueError):
            _optical_substeps(clear,0,1,2,-1.)

    def test_nonuniform_stages_resolve_analytic_baryon_layer(self):
        # For tiny beta=v_f(1-exp(-k*u)), a=-T10/sqrt(4pi/3) satisfies
        # a' = lambda*(beta-a)+O(beta^2), a(0)=0.
        op = GeneralLieStokesOperator(2,n_gl_theta=8)
        zero=LieGeometry(np.zeros((3,3)),np.zeros(3),np.zeros((3,3)))
        rate,k,vf=6.,5.,1e-6
        exact=vf*(1.+k/(rate-k)*math.exp(-rate)-rate/(rate-k)*math.exp(-k))
        opac=OpacityHistory([0,1],[rate,rate])
        errors=[]
        for cap in (None,1.,.5,.25):
            edges,ds=_optical_substeps(opac,0.,1.,2,cap)
            state=_advance_moving_photon_cell(op,np.zeros(op.dim,complex),1.,zero,
                np.zeros(op.dim,complex),ds,lambda u: np.array([0.,0.,vf*(-np.expm1(-k*u))]),
                sub_edges=edges)
            measured=-state[op.idx["T"][1,0]].real/np.sqrt(4*np.pi/3)
            errors.append(abs(measured-exact)/vf)
        self.assertGreater(errors[0],20*errors[-1])
        self.assertTrue(all(a>b for a,b in zip(errors,errors[1:])),errors)

    def test_nonuniform_abscissae_and_shared_clock(self):
        op=GeneralLieStokesOperator(2,n_gl_theta=8)
        zero=LieGeometry(np.zeros((3,3)),np.zeros(3),np.zeros((3,3)))
        edges=np.array([0,.125,.5,1])
        calls=[]
        def velocity(u):
            calls.append(u)
            return np.zeros(3)
        _advance_moving_photon_cell(op,np.zeros(op.dim,complex),1.,zero,
                                    np.zeros(op.dim,complex),[.6,.1,.02],velocity,sub_edges=edges)
        g=1-1/np.sqrt(2)
        expected=np.column_stack([edges[:-1]+g*np.diff(edges),edges[1:]]).ravel()
        np.testing.assert_allclose(calls,expected,atol=2e-16)
