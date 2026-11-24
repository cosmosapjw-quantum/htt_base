"""Manufactured tilted initial data at fixed H for the public Gauss/Codazzi closures."""
import argparse
import json
import math
from dataclasses import replace
from pathlib import Path

import numpy as np
from bass.background import build_bianchi_algebra, build_tilted_initial_conditions, rescale_bianchi_algebra
from bass.background.bianchi_types import build_structure_tensor
from bass.background.convention_bridge import exact_momentum_divergence
from bass.background.geometry import build_geometry, pstf_rank2
from bass.tilt.species_tilt import TiltedSpeciesParams, decompose_tilted_species


def audit(seed=109, draws=10):
    rng = np.random.default_rng(seed)
    kappa, rho_hat = .7, 4.
    algebras = {name: build_bianchi_algebra(name) for name in
                ("I","II","III","IV","V","VI_0","VI_h","VII_0","VII_h","VIII","IX")}
    algebras["VI_-1/9"] = build_bianchi_algebra("VI_h", a_twist=2/3, n1=1., n3=-4.)
    ix = algebras["IX"]
    n = np.diag([.85, 1., 1.15])
    algebras["IX_triaxial"] = replace(ix, n=n, C=build_structure_tensor(ix.a,n))
    results = []
    for family, algebra in algebras.items():
        algebra = rescale_bianchi_algebra(algebra, .35)
        d = np.column_stack([exact_momentum_divergence(pstf_rank2(e.reshape(3,3)),algebra.a,algebra.n)
                             for e in np.eye(9)])
        rank = int(np.linalg.matrix_rank(d))
        if rank == 0:
            results.append(dict(family=family, rank=rank, runs=0, reason="the divergence map is zero at this Lie point; the single dust component must have zero total normal flux"))
            continue
        ricci = build_geometry(algebra).ricci_scalar
        maxima = {"abs_gauss":0., "physical_codazzi_over_kq":0., "abs_jacobi":0.}
        for i in range(draws):
            s = pstf_rank2(rng.normal(size=(3,3))*.07)
            q = -exact_momentum_divergence(s,algebra.a,algebra.n)/kappa
            speed = 2*q/(rho_hat+math.hypot(rho_hat, 2*np.linalg.norm(q)))
            beam = decompose_tilted_species(TiltedSpeciesParams(rho_hat=rho_hat,p_hat=0.,v=speed,label="dust"))
            forced = (np.linalg.pinv(d) @ (-kappa*q)).reshape(3,3)
            free = s-forced
            for policy in ("project_shear_amplitude","solve_curvature_scale"):
                u = (.93 if i%2 else 1.07) if policy=="solve_curvature_scale" else 1.
                wanted = forced/u + free if policy=="solve_curvature_scale" else forced + (1.12 if i%2 else .88)*free
                H = math.sqrt((kappa*beam.mu+.5*np.sum(wanted*wanted)-.5*u*u*ricci)/3)
                ic = build_tilted_initial_conditions(algebra=algebra,species=[beam],sigma_ab=s,H=H,
                                                     closure=policy,kappa=kappa)
                div = exact_momentum_divergence(ic.sigma_ab,ic.algebra.a,ic.algebra.n)
                rr = float(np.linalg.norm(div + kappa*q)/np.linalg.norm(kappa*q))
                g = abs(3*H*H-kappa*beam.mu-.5*np.sum(ic.sigma_ab**2)+.5*ic.geometry.ricci_scalar)
                maxima["abs_gauss"]=max(maxima["abs_gauss"],float(g))
                maxima["physical_codazzi_over_kq"]=max(maxima["physical_codazzi_over_kq"],rr)
                maxima["abs_jacobi"]=max(maxima["abs_jacobi"],float(ic.algebra.jacobi_residual_norm))
                if not ic.metadata.gauss_admissible or not ic.metadata.codazzi_satisfied or rr>1e-10 or g>1e-10:
                    raise RuntimeError((family,i,policy,g,rr))
        results.append(dict(family=family,rank=rank,runs=2*draws,**maxima))
    return dict(seed=seed,draws_per_nonzero_rank_point=draws,source="normal physical dust flux q=-div(sigma)/kappa; nonzero shear, target curvature or null radius changed; signed analytic divergence tested on returned effective geometry",kappa=kappa,rest_density=rho_hat,cases=results)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    args=p.parse_args()
    result=audit()
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
