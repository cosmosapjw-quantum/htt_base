"""Pointwise Euler versus integrated kinetic momentum derivative at finite tilt."""
import unittest

import numpy as np

from bass.background.convention_bridge import build_structure_tensor_with_sign
from bass.background.tilted_bianchi_state import build_4d_bianchi_connection
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry, vector_to_stokes_maps
from bass.transport.moving_collision_stage import initial_radiation_stokes


class TestBolometricFluxIdentity(unittest.TestCase):
    def test_shear_and_curvature_independent_flux_derivatives(self):
        op = GeneralLieStokesOperator(6)
        n, w = op._grid[2], op._grid[3]
        p = -n
        beta = np.array([.1, -.07, .12])
        b2 = beta @ beta
        # Independent normal momentum tensor from a continuous boosted thermal sky.
        j = (1-b2)**3/((1+b2/3)*(1+n@beta)**4)
        k = np.concatenate([np.ones(p.shape[:-1]+(1,)), p], axis=-1)
        T = np.einsum("ij,ijc,ijd->cd", j*w, k, k)/(4*np.pi)
        q_ratio = T[0, 1:]/T[0, 0]
        state = initial_radiation_stokes(op, beta)
        for a, N, sigma in (
            (np.array([.1,.02,.03]), np.zeros((3,3)), np.zeros((3,3))),
            (np.zeros(3), np.diag([.1,.03,.13]), np.zeros((3,3))),
            (np.zeros(3), np.zeros((3,3)), np.diag([.1,-.07,-.03])),
        ):
            geom = LieGeometry(sigma, a, N)
            connection = build_4d_bianchi_connection(1., sigma, build_structure_tensor_with_sign(a,N,a_sign=1))
            dT = -(np.einsum('aca,cb->b',connection,T) + np.einsum('bca,ac->b',connection,T))
            reference = (dT[1:] - q_ratio*dT[0])/T[0,0]
            rate = (op.base_operator(geom) + op.bolometric_redshift_operator(geom)) @ state
            rate += op.shear_source_vector(sigma)
            jdot = 4*vector_to_stokes_maps(rate,op.idx,L=op.L,n_gl_theta=op.n_gl_theta)[...,0]
            # d/dr of A/B; isotropic a^-4 cancels in the ratio.
            angular = (np.einsum("ij,ijc->c", jdot*w,p)-q_ratio*np.sum(jdot*w))/(4*np.pi)
            np.testing.assert_allclose(angular,reference,atol=5e-13,rtol=5e-12)
