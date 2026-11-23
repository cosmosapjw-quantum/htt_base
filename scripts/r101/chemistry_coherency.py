"""Compose clocked chemistry and exact Thomson propagation in one rest frame.

This runner validates the chemistry-to-collision interface. Its supplied finite
reaction network is a controlled fixture, not a calibrated HYREC replacement.
Streaming, moving electron frames and photon/chemistry feedback are absent.
The separate coherency_history runner consumes the actual repo HyRec history.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
import numpy as np

from bass.collision.coherency import ThomsonCoherencyPropagator
from bass.recombination.clocked_chemistry import ChemistryTangent, evolve_clocked_chemistry


def sphere_grid(n_mu=5, n_phi=12):
    """Product quadrature exact through degree four for the collision solver."""
    if not isinstance(n_mu, int) or isinstance(n_mu, bool) or n_mu < 3:
        raise ValueError("n_mu must be an integer >=3")
    if not isinstance(n_phi, int) or isinstance(n_phi, bool) or n_phi < 5:
        raise ValueError("n_phi must be an integer >=5")
    mu, wm = np.polynomial.legendre.leggauss(n_mu)
    phi = np.arange(n_phi)*(2*np.pi/n_phi)
    mm, pp = np.meshgrid(mu, phi, indexing="ij")
    n = np.stack((np.sqrt(1-mm*mm)*np.cos(pp), np.sqrt(1-mm*mm)*np.sin(pp), mm), axis=-1)
    return n.reshape(-1,3), np.repeat(wm, n_phi)*(2*np.pi/n_phi)


def evolve_rest_frame(directions, weights, initial_stokes, chemistry_kwargs,
                     initial_stokes_tangent=None):
    """Exact collision-only composition given cellwise supplied chemistry.

    A common electron rest frame is required. For changing frames, construct
    boosted redistribution and transport before using a multi-frame integrator.
    A single tilted ray opacity cannot be substituted for common angular depth.
    """
    beta = np.asarray(chemistry_kwargs["beta"])
    if not np.isrealobj(beta) or not np.all(np.isfinite(beta)) or np.any(beta != 0):
        raise ValueError("this common-frame composition requires beta == 0")
    tangent = chemistry_kwargs.get("tangent")
    if tangent is not None and tangent.beta is not None and np.any(np.asarray(tangent.beta) != 0):
        raise ValueError("boost-response requires a transformed collision operator")
    history = evolve_clocked_chemistry(**chemistry_kwargs)
    op = ThomsonCoherencyPropagator(directions, weights)
    depth = float(np.sum(history.delta_optical_depth))
    sky = op.advance(initial_stokes, depth)
    tangent_sky = None
    if history.tangent is not None or initial_stokes_tangent is not None:
        ds = np.zeros_like(sky) if initial_stokes_tangent is None else initial_stokes_tangent
        ddepth = 0. if history.tangent is None else float(np.sum(history.tangent.delta_optical_depth))
        tangent_sky = op.advance(ds, depth) + op.collision(sky)*ddepth
    return history, sky, tangent_sky


def fixture(cells=64, scale=1., with_tangent=True):
    edges = np.linspace(-np.log(1201.), -np.log(901.), cells+1)
    middle = (edges[:-1]+edges[1:])/2
    # H0 [s^-1], matter plus radiation normal expansion; fixed prescribed law.
    h0 = 67.4*1000/3.085677581491367e22
    hubble = h0*np.sqrt(.315*np.exp(-3*middle)+9.2e-5*np.exp(-4*middle)+.684908)
    base_rate = np.array([[-3., .08, 0.], [3., -1.08, 0.], [0., 1., 0.]])*1e-13
    return dict(N_edges=edges, initial_population=[1.,0.,0.], electron_yield=[1.,0.,0.],
                proper_generators_s=scale*base_rate, hubble_normal_s=hubble,
                beta=[0.,0.,0.], photon_direction=[0.,0.,1.], comoving_hydrogen_m3=.19,
                tangent=ChemistryTangent(proper_generators_s=base_rate) if with_tangent else None)


def run(cells=64):
    n,w = sphere_grid()
    initial = np.zeros((len(n),4))
    initial[:,0] = 1.+.1*(n[:,2]**2-1/3)
    initial[:,1] = .01*n[:,0]
    initial[:,2] = .01*n[:,1]
    initial[:,3] = .02*n[:,2]
    kwargs = fixture(cells)
    history, final, derivative = evolve_rest_frame(n,w,initial,kwargs)
    eps=1e-5
    plus=evolve_rest_frame(n,w,initial,fixture(cells,1+eps,False))[1]
    minus=evolve_rest_frame(n,w,initial,fixture(cells,1-eps,False))[1]
    finite_difference=(plus-minus)/(2*eps)
    op=ThomsonCoherencyPropagator(n,w)
    sequential=initial.copy()
    start=time.perf_counter()
    for d in history.delta_optical_depth:sequential=op.advance(sequential,float(d))
    sequential_seconds=time.perf_counter()-start
    start=time.perf_counter();fused=op.advance(initial,float(history.delta_optical_depth.sum()))
    fused_seconds=time.perf_counter()-start
    stf=np.einsum('n,ni,nj,n->ij',w,n,n,final[:,0])/(4*np.pi)-np.eye(3)*np.dot(w,final[:,0])/(12*np.pi)
    dstf=np.einsum('n,ni,nj,n->ij',w,n,n,derivative[:,0])/(4*np.pi)-np.eye(3)*np.dot(w,derivative[:,0])/(12*np.pi)
    return {"scope":"supplied-rate, fixed common rest frame, collision-only interface",
            "cells":cells,"directions":len(n),"total_optical_depth":float(history.delta_optical_depth.sum()),
            "depth_rate_response":float(history.tangent.delta_optical_depth.sum()),
            "rate_response_max_fd_error":float(np.max(abs(derivative-finite_difference))),
            "fused_vs_sequential_max_error":float(np.max(abs(fused-sequential))),
            "intensity_monopole_defect":float(abs(np.dot(w,final[:,0]-initial[:,0]))),
            "minimum_stokes_cone_margin":float(np.min(final[:,0]-np.linalg.norm(final[:,1:],axis=1))),
            "last_scatter_mass_defect":float(abs(history.visibility_bin_probability.sum()+np.exp(-history.optical_depth_to_observer[0])-1)),
            "signed_intensity_stf":stf.tolist(),"signed_intensity_stf_rate_response":dstf.tolist(),
            "timing_single_call_seconds":{"sequential":sequential_seconds,"fused":fused_seconds},
            "timing_scope":"one diagnostic call; not a general end-to-end benchmark",
            "physical_Pi":None,"physical_GF":None,"Bianchi_family_attribution":None}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path);p.add_argument('--cells',type=int,default=64)
    args=p.parse_args(argv)
    if args.cells<1:raise ValueError('cells must be positive')
    value=run(args.cells);text=json.dumps(value,indent=2,allow_nan=False)+'\n'
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
    print(text,end='')
    return 0


if __name__=='__main__':raise SystemExit(main())
