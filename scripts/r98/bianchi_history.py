"""R98 prescribed homogeneous polarized test radiation on an evolved tilted R49 IVP.

The early-time data define a model. The measured sky and primordial perturbations
are not inputs. Use with python -m scripts.r98.bianchi_history.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy
from scipy.integrate import simpson, solve_ivp
from scipy.interpolate import CubicSpline
from scipy.sparse import bmat, csc_matrix
from scipy.sparse.linalg import expm_multiply

from scripts.r97 import bianchi_coupled_m_transport as r97
from bass.background.bianchi_types import build_bianchi_algebra
from bass.background.convention_bridge import exact_momentum_divergence, exact_spatial_ricci_from_compact
from bass.background.tilted_bianchi_state import (
    SpeciesFluidCongruence, construct_admissible_tilted_state,
)
from bass.recombination.reionization import compute_tau_dot_conformal_Mpc

Z_INITIAL = 1600.0
N_INITIAL = -np.log1p(Z_INITIAL)
FAMILIES = ("FLRW", "I", "V", "VII_h", "VI_h")
SHEAR_SHAPE = np.array([[-1.0, .4, -.3], [.4, .3, .2], [-.3, .2, .7]])
TILT_SHAPE = np.array([1.0, -.5, .25])


@lru_cache(maxsize=1)
def optics():
    table = r97.load_recombination_table(r97.HYREC_CSV)
    cosmo = r97.cosmology_from_metadata(table.metadata)
    model = r97.ReionizationParameters(z_reion_H=7.67, delta_z_H=.5, z_reion_HeII=3.5,
                                       delta_z_HeII=.5, include_HeII=True)
    extended = r97.extend_table_with_reionization(table, model, cosmology=cosmo, z_low=0., n_low_points=400)
    return cosmo, r97.build_interpolators(extended)


def early_state(family, epsilon=1e-5):
    """Rest densities in units Href_i^2/(8 pi G), c-dependent energy units geometrized by R49."""
    if family not in FAMILIES or not np.isfinite(epsilon) or epsilon < 0:
        raise ValueError("invalid family or epsilon")
    cosmo, _ = optics()
    u = 1.0 + Z_INITIAL
    href = float(cosmo.H_of_z(Z_INITIAL))
    density_scale = 3.0 * (cosmo.H_0_SI / href)**2
    baryon = density_scale * cosmo.Omega_b * u**3
    dark = density_scale * (cosmo.Omega_m - cosmo.Omega_b) * u**3
    radiation = density_scale * cosmo.Omega_r * u**4
    vacuum = density_scale * cosmo.Omega_Lambda
    # Physical model parameters at the initial hypersurface, in Href_i units.
    curvature = 3e-4
    kwargs = {"V": dict(a_twist=curvature),
              "VII_h": dict(a_twist=.5*curvature, n1=curvature, n3=curvature),
              "VI_h": dict(a_twist=2*curvature/3, n1=curvature, n3=-4*curvature)}
    algebra = build_bianchi_algebra("I" if family == "FLRW" else family, **kwargs.get(family, {}))
    amplitude = 0. if family == "FLRW" else epsilon
    sigma = amplitude * SHEAR_SHAPE
    rad = SpeciesFluidCongruence(species="radiation", eps_hat=radiation, p_hat=radiation/3.,
                                 v_vec=.1*amplitude*TILT_SHAPE)
    flux = -exact_momentum_divergence(sigma, algebra.a, algebra.n, a_sign=1) - rad.to_projected_state().q
    cdm = SpeciesFluidCongruence(species="cdm", eps_hat=dark, p_hat=0.,
                                 v_vec=2*flux/(dark+np.hypot(dark,2*np.linalg.norm(flux))))
    bar = SpeciesFluidCongruence(species="baryon", eps_hat=baryon, p_hat=0., v_vec=np.zeros(3))
    return construct_admissible_tilted_state(family=family, algebra=algebra, sigma_ab=sigma,
                                             species=[rad, cdm, bar], lambda_value=vacuum, kappa=1.)


def background(family, epsilon=1e-5, samples=641):
    if samples < 5:
        raise ValueError("need at least five trajectory samples")
    state = early_state(family, epsilon)
    traj = r97.evolve_general_tilted_bianchi(state, config=r97.TiltedEvolutionConfig(
        N_start=N_INITIAL, N_end=0., n_eval=samples, rtol=2e-12, atol=3e-16,
        constraint_abort_tol=1e-7))
    return state, traj


def background_checks(state, trajectory):
    """Relative constraints without a unity floor at late times in Href_i units."""
    t = trajectory
    cosmo, _ = optics()
    href = float(cosmo.H_of_z(Z_INITIAL))
    n = t.N_grid
    hs = t.H_grid
    sig = t.sigma_ab_grid
    gs = np.c_[sig[:,0,0],sig[:,1,1],sig[:,0,1],sig[:,0,2],sig[:,1,2],
               t.a_grid, t.n_grid[:,0,0],t.n_grid[:,1,1],t.n_grid[:,2,2],
               t.n_grid[:,0,1],t.n_grid[:,0,2],t.n_grid[:,1,2]] / hs[:,None]
    ham, cod, jac, jac_h, h_values = [], [], [], [], []
    for j, (H,S,A,B) in enumerate(zip(hs,sig,t.a_grid,t.n_grid)):
        rho, flux, flux_scale = 0., np.zeros(3), 0.
        for sp in t.species_specs:
            v = t.species_v_grid[sp.species][j]
            w = sp.K_eos
            energy = t.species_eps_hat_grid[sp.species][j]
            enthalpy = energy*(1+w)/(1-v@v)
            rho += enthalpy - w*energy
            flux += enthalpy*v
            flux_scale += np.linalg.norm(enthalpy*v)
        _, curvature, _ = exact_spatial_ricci_from_compact(A,B,a_sign=1)
        shear = .5*np.sum(S*S)
        residual = 3*H*H + .5*curvature - shear - rho - t.lambda_value
        ham.append(abs(residual)/(3*H*H))
        divergence = exact_momentum_divergence(S,A,B,a_sign=1)
        cod.append(np.linalg.norm(divergence+flux)/max(flux_scale+np.linalg.norm(divergence),1e-300))
        # Type V has n analytically zero; cosine-angle normalization is singular there.
        defect = np.linalg.norm(B@A)
        jac.append(defect/max(A@A + np.sum(B*B),1e-300))
        jac_h.append(defect/H**2)
        if state.family in ("VI_h","VII_h"):
            product = .5*(np.trace(B)**2 - np.trace(B@B))
            h_values.append(float((A@A)/product))
    eta_mpc = t.eta_grid[-1]/(href*r97.SEC_PER_MPC)
    d_eta = np.exp(-n)/(hs*href*r97.SEC_PER_MPC)
    return gs, {
        "N_initial":float(n[0]), "N_final":float(n[-1]), "rhs_evals":t.n_rhs_evals,
        "H_reference_initial_s_inv":href, "H_final_km_s_Mpc":float(hs[-1]*href*r97.SEC_PER_MPC*299792.458),
        "max_relative_H_vs_reference_FLRW":float(np.max(abs(hs*href/cosmo.H_of_z(np.expm1(-n))-1))),
        "hamiltonian_abs_over_3H2":float(max(ham)), "codazzi_relative_to_uncancelled_flux":float(max(cod)),
        "jacobi_relative":float(max(jac)), "jacobi_over_H2":float(max(jac_h)), "r49_codazzi_relative":float(t.max_codazzi_residual_rel),
        "max_species_speed_over_c":float(t.max_speed_over_trajectory),
        "max_normal_baryon_speed_over_c":float(np.linalg.norm(t.species_v_grid["baryon"],axis=1).max()),
        "elapsed_proper_time_Gyr":float(simpson(1/(hs*href),x=n)/(365.25*86400*1e9)),
        "conformal_distance_Mpc":float(eta_mpc),
        "conformal_simpson_vs_ivp_relative":float(abs(simpson(d_eta,x=n)/eta_mpc-1)),
        "max_shear_over_H":float(np.max(np.linalg.norm(sig,axis=(1,2))/hs)),
        "initial_geometry_coordinates":gs[0].tolist(), "final_geometry_coordinates":gs[-1].tolist(),
        "h_range":[min(h_values),max(h_values)] if h_values else None,
    }

def unpack_geometry(row):
    xx, yy, xy, xz, yz, ax, ay, az, nxx, nyy, nzz, nxy, nxz, nyz = row
    sig = np.array([[xx,xy,xz],[xy,yy,yz],[xz,yz,-xx-yy]])
    structure = np.array([[nxx,nxy,nxz],[nxy,nyy,nyz],[nxz,nyz,nzz]])
    return sig, np.array([ax,ay,az]), structure


class Angular:
    """Fourteen real coordinates span STF shear, structure vector and symmetric n.

    Project once per basis vector. Each lookup assembles the affine operator
    appropriate to its own time sample. The final state coordinate is constant 1.
    """
    def __init__(self, L, n_gl=None):
        if not 2 <= L <= 24:
            raise ValueError("bounded work range is 2 <= L <= 24")
        self.L = L
        self.m = tuple(range(-L,L+1))
        self.idx, dim = r97._mode_index_table(L,self.m)
        self.dim = dim
        _, K = r97._build_diag_stream_and_thomson(L,self.m,self.idx,dim,0.)
        angular_size = max(L+8,16) if n_gl is None else n_gl
        if angular_size < L+4:
            raise ValueError("angular quadrature is undersampled")
        th = r97.gl_sphere_grid(angular_size)[0][:,0]
        basis = r97._build_spin_basis_theta(L,self.m,th)
        operators = []
        zero = csc_matrix((1,1),dtype=complex)
        for coord in np.eye(14):
            sig,a,n = unpack_geometry(coord)
            projected = r97._project_gamma4_to_coupled_m_operators(
                L,self.m,self.idx,dim,sig,a,n,basis_theta=basis,n_gl_theta=angular_size)
            operators.append(projected["M_geo_exact"])
        self.sources = np.zeros((dim,14),complex)
        for j in range(5):
            sig,_,_ = unpack_geometry(np.eye(14)[j])
            for m,coeff in r97.stf_source_harmonics(sig).items():
                self.sources[self.idx["T"][(2,m)],j] = -coeff
        # Build a single sorted union of nonzeros; changes at each time step
        # are small vector contractions, without reprojecting a spherical grid.
        size = dim+1
        augmented = [bmat([[op,csc_matrix((dim,1))],[None,zero]],format="coo")
                     for op in [*operators,K]]
        for j in range(5):
            augmented.append(bmat([[csc_matrix((dim,dim)),csc_matrix(self.sources[:,j,None])],
                                   [None,zero]],format="coo"))
        indices = [op.row.astype(np.int64)*size + op.col for op in augmented]
        slots = np.unique(np.concatenate(indices))
        self.coeff = np.zeros((len(slots),len(augmented)),complex)
        for j,(keys,op) in enumerate(zip(indices,augmented)):
            self.coeff[np.searchsorted(slots,keys),j] = op.data
        self.template = csc_matrix((np.arange(1,len(slots)+1,dtype=float),
                                    (slots//size,slots%size)),shape=(size,size))
        # CSC sorts entries column-major. Align coefficient rows with its data.
        self.coeff = self.coeff[self.template.data.astype(int)-1]
        self.template = self.template.astype(complex)

    def matrix(self,geometry,source,opacity):
        values = self.coeff @ np.r_[geometry,opacity,source[:5]]
        return csc_matrix((values,self.template.indices,self.template.indptr),
                          shape=self.template.shape,copy=False)


def timeline(trajectory,geometry,refinement):
    if not isinstance(refinement,int) or refinement < 1:
        raise ValueError("refinement must be a positive integer")
    # Same knots as the R95 fixture, subdivided in the actual evolution variable N.
    z_knots = np.unique(np.r_[np.linspace(0,12,35),np.linspace(12,200,25),
                       np.linspace(200,850,20),np.linspace(850,1300,65),np.linspace(1300,1600,15)])
    nodes = -np.log1p(z_knots[::-1])
    grid = np.r_[np.linspace(nodes[:-1],nodes[1:],refinement,endpoint=False).T.ravel(),nodes[-1]]
    if grid[0] < trajectory.N_grid[0] or grid[-1] > trajectory.N_grid[-1]:
        raise ValueError("transport would extrapolate beyond actual trajectory")
    dN = np.diff(grid)
    mid = .5*(grid[:-1]+grid[1:])
    bg = CubicSpline(trajectory.N_grid,geometry,axis=0,extrapolate=False)(mid)
    cosmo, interp = optics()
    href = float(cosmo.H_of_z(Z_INITIAL))
    H = np.exp(CubicSpline(trajectory.N_grid,np.log(trajectory.H_grid),extrapolate=False)(mid))*href
    dchi_dN = np.exp(-mid)/(H*r97.SEC_PER_MPC)
    z = np.expm1(-mid)
    xe = interp.query_x_e(z)
    opacity = compute_tau_dot_conformal_Mpc(z,xe,cosmo)*dchi_dN
    return dN,bg,opacity


def evolve(angular,trajectory,geometry,refinement=1,*,freeze_geometry=False,collision=True):
    dN,bg,opacity = timeline(trajectory,geometry,refinement)
    y = np.zeros(angular.dim+1,complex)
    y[-1] = 1.
    for step,sample,rate in zip(dN,bg,opacity):
        geom = geometry[-1] if freeze_geometry else sample
        matrix = angular.matrix(geom,sample,rate if collision else 0.)
        y = expm_multiply(step*matrix,y)
    if any(~np.isfinite(y)) or abs(y[-1]-1.) > 2e-12:
        raise FloatingPointError("nonfinite transport or loss of affine invariant")
    return y[:-1],float(dN@opacity) if collision else 0.


def low_modes(angular,y,channel,ell_max=5):
    return np.array([y[angular.idx[channel][ell,m]]
                     for ell in range(2,min(angular.L,ell_max)+1) for m in range(-ell,ell+1)])


def comparison(a,y,b,v):
    diff = {}
    for ch in ("T","E","B"):
        ref = low_modes(b,v,ch)
        delta = low_modes(a,y,ch)-ref
        diff[ch] = {"abs":float(np.linalg.norm(delta)),
                    "rel_to_reference":float(np.linalg.norm(delta)/np.linalg.norm(ref)) if np.linalg.norm(ref) else None}
    return diff


def endpoint(angular,y):
    report = {}
    for ch in ("T","E","B"):
        values = angular.idx[ch]
        parity = max(abs(y[i] - (-1.)**m*y[values[ell,-m]].conjugate())
                     for (ell,m),i in values.items())
        coeff = low_modes(angular,y,ch)
        report[ch] = {"norm_l2_to_5":float(np.linalg.norm(coeff)), "max_reality_error":float(parity),
                      "signed_ell2_m0_to_2":[[float(y[values[2,m]].real),float(y[values[2,m]].imag)] for m in range(3)],
                      "alm_rows_ell_ascending_entries_m_minus_ell_to_plus_ell_Re_Im":[
                          [[float(y[values[ell,m]].real),float(y[values[ell,m]].imag)]
                           for m in range(-ell,ell+1)]
                          for ell in range(0 if ch=="T" else 2,angular.L+1)]}
    return report


def rays(angular,trajectory,y,steps=512):
    th,ph,nh,w = r97.gl_sphere_grid(10)
    ray = r97.integrate_polarized_geodesics(nh,family=trajectory.family,trajectory=trajectory,n_steps=steps)
    # Isotropic emission and collisionless log-temperature: log(a_o/a_e)-log(E_e/E_o).
    log_temperature = trajectory.N_grid[-1]-trajectory.N_grid[0]-ray.ln_E_emit
    coeff = r97._fast_scalar_alm_from_gl(log_temperature,10,5)
    ref = np.array([coeff[ell,m] for ell in range(2,6) for m in range(-ell,ell+1)])
    delta = low_modes(angular,y,"T")-ref
    return {"ray_steps":steps,"n_theta":len(th),"max_null_error":float(ray.max_null_err),
            "max_screen_orthogonality_error":float(ray.max_screen_ortho_err),"abs_difference":float(np.linalg.norm(delta)),
            "relative_difference_T_l2_to_5":float(np.linalg.norm(delta)/np.linalg.norm(ref))}


def hydrogen_window(trajectory):
    """Independent one-way scalar effective H recombination at 1200 >= z_volume >= 1000.

    Reuses the explicit REI-REC-BASS-SYNC02 expanding Peebles oracle rate law.
    Retains physical n_H and T from the fixture. Compares two H owners with
    identical initial x_H and identical atomic model. No splicing into the sky.
    """
    from bass.recombination.reionization import C_LIGHT, SIGMA_T
    cosmo, xe = optics()
    href = float(cosmo.H_of_z(Z_INITIAL))
    logH = CubicSpline(trajectory.N_grid,np.log(trajectory.H_grid),extrapolate=False)
    lo,hi = -np.log1p(1200.),-np.log1p(1000.)
    x0 = float(xe.query_x_e(1200.))  # adopt this numerical value as conditional x_H
    def integrate(H_at,rtol):
        def rhs(N,y):
            x = y[0]
            u = np.exp(-N)
            H = H_at(N)
            nh = cosmo.n_H_today*u**3
            T = cosmo.T_cmb*u
            TeV = 8.617343e-5*T
            alpha = 4.309e-19*(T/1e4)**(-.6166)/(1+.6703*(T/1e4)**.5300)
            beta = alpha*3.016103031869581e27*TeV**1.5*np.exp(-13.598286071938324/(4*TeV))
            escape = 4.662899067555897e21*H/(nh*(1-x))
            C = (8.2206+3*escape)/(8.2206+3*escape+beta)
            dx = -C*(nh*alpha*x*x-beta*(1-x)*np.exp(-10.198714553953742/TeV))/H
            return dx,C_LIGHT*SIGMA_T*nh*x/H
        sol = solve_ivp(rhs,(lo,hi),(x0,0.),method="DOP853",rtol=rtol,atol=rtol*1e-3,
                        t_eval=np.linspace(lo,hi,33))
        if not sol.success or not np.all((sol.y[0]>0)&(sol.y[0]<1)):
            raise ArithmeticError("hydrogen window failed or left physical domain")
        return sol.y
    H_model = lambda N: href*np.exp(logH(N))
    H_reference = lambda N: float(cosmo.H_of_z(np.expm1(-N)))
    model = integrate(H_model,2e-11)
    tighter = integrate(H_model,2e-13)
    ref = integrate(H_reference,2e-13)
    return {"redshift_volume_start_end":[1200,1000],"x_H_start":x0,
            "x_H_end":float(tighter[0,-1]),"tau_window":float(tighter[1,-1]),
            "model_minus_same_chemistry_reference_x_H_end":float(tighter[0,-1]-ref[0,-1]),
            "model_minus_same_chemistry_reference_tau":float(tighter[1,-1]-ref[1,-1]),
            "max_abs_x_H_rtol_refinement":float(np.max(abs(tighter[0]-model[0]))),
            "max_abs_tau_rtol_refinement":float(np.max(abs(tighter[1]-model[1]))),
            "HyRec_fixture_x_e_end":float(xe.query_x_e(1000.)),"fed_into_harmonic_sky":False}

def compute():
    import os
    import resource
    start = time.perf_counter()
    inputs = [Path(__file__).resolve(),Path(r97.__file__).resolve(),r97.HYREC_CSV,
              *(r97.ROOT/p for p in ("htt/bass/background/general_tilted_evolution.py",
                   "htt/bass/background/tilted_bianchi_state.py","htt/bass/transport/general_bianchi_transfer.py",
                   "htt/bass/recombination/reionization.py","scripts/r95/bianchi_polarized_hierarchy.py",
                   "scripts/r96/spin2_mblock_extension.py"))]
    def hashes():
        return {str(p.relative_to(r97.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    initial_hashes = hashes()
    base = Angular(12)
    rows = {}
    for family in FAMILIES:
        state,traj = background(family)
        geometry,checks = background_checks(state,traj)
        y,tau = evolve(base,traj,geometry,2)
        row = {"background":checks,"optical_depth_to_initial":tau,"L":12,"refinement":2,
               "midpoint_steps":len(timeline(traj,geometry,2)[0]),"sky":endpoint(base,y)}
        rows[family] = row
        row["independent_hydrogen_chemistry_window"] = hydrogen_window(traj)
        if family in ("VII_h","VI_h"):
            frozen,_ = evolve(base,traj,geometry,2,freeze_geometry=True)
            row["frozen_geometry_minus_evolving_same_source"] = comparison(base,frozen,base,y)
        if family == "VII_h":
            coarse,tau1 = evolve(base,traj,geometry,1)
            fine,tau4 = evolve(base,traj,geometry,4)
            row["time_refinement"] = {"1_vs_2":comparison(base,coarse,base,y),
                                      "2_vs_4":comparison(base,y,base,fine),"tau_r1_r2_r4":[tau1,tau,tau4]}
            angular_fine = Angular(16)
            high,_ = evolve(angular_fine,traj,geometry,2)
            row["L12_vs_16_all_m"] = comparison(base,y,angular_fine,high)
            del angular_fine
            collisionless,_ = evolve(base,traj,geometry,4,collision=False)
            row["collisionless_4D_ray_oracle"] = rays(base,traj,collisionless)
            dense_state,dense_traj = background(family,samples=1281)
            dense_geo,_ = background_checks(dense_state,dense_traj)
            dense,_ = evolve(base,dense_traj,dense_geo,2)
            row["background_641_vs_1281"] = comparison(base,y,base,dense)
            more_rays,_ = evolve(base,dense_traj,dense_geo,8,collision=False)
            row["refined_collisionless_4D_ray_oracle"] = rays(base,dense_traj,more_rays,steps=1024)
            half_state,half_traj = background(family,epsilon=5e-6)
            half_geo,_ = background_checks(half_state,half_traj)
            half,_ = evolve(base,half_traj,half_geo,2)
            row["amplitude_test_twice_half_epsilon_minus_full"] = comparison(base,2*half,base,y)
    if initial_hashes != hashes():
        raise RuntimeError("source changed during computation")
    return {"schema":"r98_evolved_bianchi_test_radiation_v1","run_status":"completed",
            "scope":"conditional k=0 test radiation; prescribed xe(volume a); passive photon moments",
            "physical_calibration":False,"full_einstein_boltzmann":False,"SQ_NATIVE":False,
            "inputs_sha256":initial_hashes,"python":platform.python_version(),"numpy":np.__version__,
            "scipy":scipy.__version__,"processor":platform.machine(),"threads":{k:os.getenv(k) for k in
            ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS")},"elapsed_seconds":time.perf_counter()-start,
            "max_RSS_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"families":rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    result = compute()
    encoded = json.dumps(result,indent=2,allow_nan=False)+"\n"
    args.output.write_text(encoded,encoding="utf-8")
    print(f"{len(result['families'])} families in {result['elapsed_seconds']:.1f}s; {args.output}")
