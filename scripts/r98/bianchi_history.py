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
import math
from pathlib import Path
import platform
import tarfile
import time
import types

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


def timeline(trajectory,geometry,refinement,*,N_start=None):
    if not isinstance(refinement,int) or refinement < 1:
        raise ValueError("refinement must be a positive integer")
    # Same knots as the R95 fixture, subdivided in the actual evolution variable N.
    z_knots = np.unique(np.r_[np.linspace(0,12,35),np.linspace(12,200,25),
                       np.linspace(200,850,20),np.linspace(850,1300,65),np.linspace(1300,1600,15)])
    nodes = -np.log1p(z_knots[::-1])
    if N_start is not None:
        nodes = np.unique(np.r_[float(N_start), nodes[nodes > float(N_start)]])
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
    return dN,bg,opacity,grid


def evolve(angular,trajectory,geometry,refinement=1,*,freeze_geometry=False,collision=True,initial_moments=None,N_start=None,return_history=False):
    dN,bg,opacity,grid = timeline(trajectory,geometry,refinement,N_start=N_start)
    y = np.zeros(angular.dim+1,complex)
    if initial_moments is not None:
        y[:-1] = initial_moments
    y[-1] = 1.
    hist = [y[:-1].copy()] if return_history else None
    for step,sample,rate in zip(dN,bg,opacity):
        geom = geometry[-1] if freeze_geometry else sample
        matrix = angular.matrix(geom,sample,rate if collision else 0.)
        y = expm_multiply(step*matrix,y)
        if return_history:
            hist.append(y[:-1].copy())
    if any(~np.isfinite(y)) or abs(y[-1]-1.) > 2e-12:
        raise FloatingPointError("nonfinite transport or loss of affine invariant")
    tau = float(dN@opacity) if collision else 0.
    if return_history:
        return y[:-1], tau, np.asarray(hist), grid, dN, opacity
    return y[:-1], tau


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
    # Directional Sobolev escape-rate response induced by shear tensor Sigma_{ab} / H
    sig_interp = CubicSpline(trajectory.N_grid, trajectory.sigma_ab_grid / trajectory.H_grid[:, None, None], axis=0, extrapolate=False)
    n_check = np.linspace(lo, hi, 33)
    shear_rms = np.sqrt(np.mean(np.sum(sig_interp(n_check) ** 2, axis=(1, 2))))
    # Quadrupole angular RMS over the unit sphere of (n_a n_b Sigma_{ab} / H) = sqrt(2/15 * Tr(Sigma^2)/H^2)
    h_frac_rms = float(math.sqrt(2.0 / 15.0) * shear_rms)
    H_plus = lambda N: float(H_model(N) * (1.0 + math.sqrt(2.0 / 15.0) * np.linalg.norm(sig_interp(N))))
    pert = integrate(H_plus, 2e-13)
    return {"redshift_volume_start_end":[1200,1000],"x_H_start":x0,
            "x_H_end":float(tighter[0,-1]),"tau_window":float(tighter[1,-1]),
            "model_minus_same_chemistry_reference_x_H_end":float(tighter[0,-1]-ref[0,-1]),
            "model_minus_same_chemistry_reference_tau":float(tighter[1,-1]-ref[1,-1]),
            "max_abs_x_H_rtol_refinement":float(np.max(abs(tighter[0]-model[0]))),
            "max_abs_tau_rtol_refinement":float(np.max(abs(tighter[1]-model[1]))),
            "directional_shear_over_H_rms":float(shear_rms),
            "directional_escape_rate_rms_frac":h_frac_rms,
            "perturbative_escape_delta_x_H_end":float(pert[0,-1]-tighter[0,-1]),
            "perturbative_escape_delta_tau":float(pert[1,-1]-tighter[1,-1]),
            "HyRec_fixture_x_e_end":float(xe.query_x_e(1000.)),"fed_into_harmonic_sky":False}


def radiation_moment_operators():
    """Exact Gauss-Legendre spherical projection mapping T_{1m} -> q/(4 rho_g) and T_{2m} -> pi/(4 rho_g)."""
    th, ph, d, w = r97.gl_sphere_grid(8)
    w4 = (w / (4.0 * math.pi)).ravel()
    d_flat = d.reshape(-1, 3)
    m1 = (-1, 0, 1)
    M_dip = np.zeros((3, 3), dtype=np.complex128)
    for k, m in enumerate(m1):
        Y = r97.sph_harm_y(1, m, th, ph).ravel()
        M_dip[:, k] = np.sum(d_flat * (Y * w4)[:, None], axis=0)
    m2 = (-2, -1, 0, 1, 2)
    M_quad = np.zeros((3, 3, 5), dtype=np.complex128)
    nn_tf = (np.einsum("...i,...j->...ij", d, d) - np.eye(3) / 3.0).reshape(-1, 3, 3)
    for k, m in enumerate(m2):
        Y = r97.sph_harm_y(2, m, th, ph).ravel()
        M_quad[:, :, k] = np.sum(nn_tf * (Y * w4)[:, None, None], axis=0)
    return M_dip, M_quad


def radiation_feedback_audit(angular, trajectory, geometry, y_hist, grid, dN, opacity):
    """M08: Normal-frame photon-baryon momentum exchange conservation and 1-loop radiation shear backreaction."""
    M_dip, M_quad = radiation_moment_operators()
    mid = 0.5 * (grid[:-1] + grid[1:])
    y_mid = 0.5 * (y_hist[:-1] + y_hist[1:])

    idx_t1 = [angular.idx["T"][(1, m)] for m in (-1, 0, 1)]
    idx_t2 = [angular.idx["T"][(2, m)] for m in (-2, -1, 0, 1, 2)]

    # Interpolate radiation density, baryon velocity, H, a, n in R49 units along midpoints
    eps_rad_mid = CubicSpline(trajectory.N_grid, trajectory.species_eps_hat_grid["radiation"], extrapolate=False)(mid)
    v_rad_mid = CubicSpline(trajectory.N_grid, trajectory.species_v_grid["radiation"], axis=0, extrapolate=False)(mid)
    v_bar_mid = CubicSpline(trajectory.N_grid, trajectory.species_v_grid["baryon"], axis=0, extrapolate=False)(mid)
    H_mid = np.exp(CubicSpline(trajectory.N_grid, np.log(trajectory.H_grid), extrapolate=False)(mid))

    b2_r = np.sum(v_rad_mid * v_rad_mid, axis=1)
    rho_rad_mid = eps_rad_mid * (1.0 + b2_r / 3.0) / (1.0 - b2_r)

    y1 = y_mid[:, idx_t1]
    y2 = y_mid[:, idx_t2]
    q_gamma_norm = np.einsum("am,tm->ta", M_dip, y1).real
    pi_gamma_norm = np.einsum("abm,tm->tab", M_quad, y2).real
    q_gamma = 4.0 * rho_rad_mid[:, None] * q_gamma_norm
    pi_gamma = 4.0 * rho_rad_mid[:, None, None] * pi_gamma_norm

    # Photon-baryon Thomson momentum exchange: dq_b/dN = -dq_gamma/dN
    dq_gamma_dN_coll = -opacity[:, None] * (q_gamma - (4.0 / 3.0) * rho_rad_mid[:, None] * v_bar_mid)
    dq_b_dN_coll = -dq_gamma_dN_coll
    momentum_sum_defect = float(np.max(np.abs(dq_gamma_dN_coll + dq_b_dN_coll)))

    bg = CubicSpline(trajectory.N_grid, geometry, axis=0, extrapolate=False)(mid)
    # Tracefree Einstein shear source (kappa = 1 in R49 units): d(Delta sigma)/dN + 3 Delta sigma = kappa * pi_gamma / H
    src_ab = (trajectory.kappa * pi_gamma) / H_mid[:, None, None]
    delta_sig = np.zeros_like(src_ab)
    cur = np.zeros((3, 3), dtype=float)
    delta_geom = np.zeros((len(dN), 14), dtype=float)
    for j, step in enumerate(dN):
        damp = math.exp(-3.0 * step)
        avg = (1.0 - damp) / 3.0
        cur = cur * damp + avg * src_ab[j]
        delta_sig[j] = cur
        # Normalize by H_mid[j] matching Sigma/H input coordinates in Angular.matrix
        sh = cur / H_mid[j]
        delta_geom[j, :5] = [sh[0, 0], sh[1, 1], sh[0, 1], sh[0, 2], sh[1, 2]]

    # 1-loop induced perturbation to radiation sky via exact inhomogeneous exponential step driven by delta_geom
    y_fb = np.zeros(angular.dim + 1, complex)
    y_fb[-1] = 1.0
    zero_geom = np.zeros(14, float)
    for j, (step, rate) in enumerate(zip(dN, opacity)):
        geom_j = zero_geom if trajectory.family == "FLRW" else bg[j]
        matrix_j = angular.matrix(geom_j, delta_geom[j], rate)
        y_fb = expm_multiply(step * matrix_j, y_fb)
    if not np.all(np.isfinite(y_fb)) or abs(y_fb[-1] - 1.0) > 2e-12:
        raise FloatingPointError("1-loop radiation feedback transport failed")

    delta_sig_over_H = np.linalg.norm(delta_sig / H_mid[:, None, None], axis=(1, 2))
    return {
        "momentum_exchange_conservation_defect_max": momentum_sum_defect,
        "max_radiation_pi_over_rho_rad": float(np.max(np.linalg.norm(4.0 * pi_gamma_norm, axis=(1, 2)))),
        "max_1loop_delta_sigma_over_H": float(np.max(delta_sig_over_H)),
        "final_1loop_delta_sigma_over_H": float(delta_sig_over_H[-1]),
        "max_baryon_coll_force_norm_per_dN": float(np.max(np.linalg.norm(dq_b_dN_coll, axis=1))),
        "feedback_sky_delta_norm_T2_to_5": float(np.linalg.norm(low_modes(angular, y_fb[:-1], "T"))),
        "feedback_sky_delta_norm_E2_to_5": float(np.linalg.norm(low_modes(angular, y_fb[:-1], "E"))),
        "feedback_sky_delta_norm_B2_to_5": float(np.linalg.norm(low_modes(angular, y_fb[:-1], "B"))),
    }


ANILOS_ARCHIVE = Path("/mnt/extdrive/workdir/htt_open_data/r36_atlas_actual/downloads/anilos-0.1.0.tar.gz")
ANILOS_SHA256 = "399eee772ecc8efed11edf295c681f4db256a6ec2d7a1802cbcd1982a2aaca4c"


def _load_anilos_hierarchy_funcs():
    """Verify pinned AniLoS archive digest and extract kappa_array/zeta_factor_array safely."""
    import ast
    actual_sha = hashlib.sha256(ANILOS_ARCHIVE.read_bytes()).hexdigest()
    if actual_sha != ANILOS_SHA256:
        raise ValueError(f"AniLoS archive SHA-256 mismatch: {actual_sha}")
    with tarfile.open(ANILOS_ARCHIVE, "r:gz") as tf:
        src = tf.extractfile("anilos-0.1.0/src/anilos/hierarchy.py").read().decode("utf-8")
    tree = ast.parse(src, filename="anilos-0.1.0/src/anilos/hierarchy.py")
    tree.body = [
        node for node in tree.body
        if not (isinstance(node, ast.ImportFrom) and node.module in ("numba", "numba.types"))
    ]
    class _NumbaType:
        def __getitem__(self, item): return self
        def __call__(self, *args, **kwargs): return self
    nt = _NumbaType()
    ns = {"np": np, "njit": lambda *a, **kw: (lambda fn: fn), "c16": nt, "f8": nt, "i8": nt, "unicode_type": nt}
    exec(compile(tree, "anilos-0.1.0/src/anilos/hierarchy.py", "exec"), ns)
    return ns["kappa_array"], ns["zeta_factor_array"], ns["zetas_array"], actual_sha


def anilos_and_ic_atlas_audit(angular):
    """Compare pinned AniLoS near-isotropic recurrence coefficients vs R98/R96 spin coupling and build 3-IC atlas."""
    kappa_array, zeta_factor_array, _, archive_sha = _load_anilos_hierarchy_funcs()
    max_kappa_diff = 0.0
    for s in (0, 2):
        for m in range(-2, 3):
            ell0 = max(abs(s), abs(m)) + 1
            nu = 1.75 + 0.0j
            kap = kappa_array(ell0, 12, s, m, nu, 1.0e12)
            for idx, ell in enumerate(range(ell0, 13)):
                c_anilos = complex(kap[idx] / (nu * math.sqrt((2 * ell - 1) * (2 * ell + 1)))).real
                c_r98 = r97.c_spin(ell, s, m)
                max_kappa_diff = max(max_kappa_diff, abs(c_anilos - c_r98))
    # Check AniLoS VII_h spiral factor at our VII_h h = 0.25 (sqrth = 0.5)
    zf_m0 = zeta_factor_array(2, 8, 0.5, 0)
    zf_m1 = zeta_factor_array(2, 8, 0.5, 1)
    zf_minus1 = zeta_factor_array(2, 8, 0.5, -1)
    ells_z = np.arange(2, 9, dtype=float)
    zeta_m0_err = float(np.max(np.abs(zf_m0 - (-1j * np.sqrt((ells_z - 1.0) / (ells_z + 1.0))))))
    zeta_conj_err = float(np.max(np.abs(zf_minus1 + np.conj(zf_m1))))
    # Near-isotropic IC atlas: 3 canonical seeds on I, V, VII_h (kept separate from exceptional VI_{-1/9})
    ic_atlas = {}
    for fam in ("I", "V", "VII_h"):
        st, tr = background(fam, samples=321)
        geom, _ = background_checks(st, tr)
        y_zero, _ = evolve(angular, tr, geom, 2, N_start=-math.log1p(15.0))
        y_t2 = np.zeros(angular.dim, dtype=complex)
        y_t2[angular.idx["T"][(2, 0)]] = 1.0e-5
        y_t, _ = evolve(angular, tr, geom, 2, initial_moments=y_t2, N_start=-math.log1p(15.0))
        y_pol = np.zeros(angular.dim, dtype=complex)
        y_pol[angular.idx["E"][(2, 1)]] = 1.0e-5
        y_pol[angular.idx["E"][(2, -1)]] = -1.0e-5
        y_p, _ = evolve(angular, tr, geom, 2, initial_moments=y_pol, N_start=-math.log1p(15.0))
        dt = low_modes(angular, y_t - y_zero, "T")
        dp_e = low_modes(angular, y_p - y_zero, "E")
        dp_b = low_modes(angular, y_p - y_zero, "B")
        ic_atlas[fam] = {
            "window": "post_recombination_z15_to_z0",
            "shear_driven_T_l2_to_5_norm": float(np.linalg.norm(low_modes(angular, y_zero, "T"))),
            "T20_ic_1e5_residual_T_norm": float(np.linalg.norm(dt)),
            "T20_ic_generated_E_norm": float(np.linalg.norm(low_modes(angular, y_t - y_zero, "E"))),
            "E21_ic_1e5_residual_E_norm": float(np.linalg.norm(dp_e)),
            "E21_ic_1e5_helical_B_norm": float(np.linalg.norm(dp_b)),
        }
    return {
        "anilos_tarball_sha256": archive_sha,
        "anilos_git_commit_pin": "9b7a2611882dcca80a1491bcad2b8f05635faca7",
        "kappa_vs_r98_cspin_max_abs_diff": float(max_kappa_diff),
        "zeta_factor_m0_exact_max_err": zeta_m0_err,
        "zeta_factor_m_parity_max_err": zeta_conj_err,
        "zeta_factor_m1_sqrth_0p5_values": [[float(x.real), float(x.imag)] for x in zf_m1[:4]],
        "linearized_vs_finite_geometry_note": "AniLoS evolves linearized perturbations around near-FLRW Bianchi (I,V,VII_0,VII_h,IX); R98 evolves full non-axisymmetric M_geo(sigma,a,n) advection along evolved R49 trajectories and excludes exceptional VI_{-1/9} from linear extrapolation.",
        "primordial_ic_atlas_near_isotropic_I_V_VIIh": ic_atlas,
    }

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
        y,tau,y_hist,grid,dN,opacity = evolve(base,traj,geometry,2,return_history=True)
        row = {"background":checks,"optical_depth_to_initial":tau,"L":12,"refinement":2,
               "midpoint_steps":len(dN),"sky":endpoint(base,y)}
        rows[family] = row
        row["independent_hydrogen_chemistry_window"] = hydrogen_window(traj)
        row["radiation_feedback_1loop"] = radiation_feedback_audit(base,traj,geometry,y_hist,grid,dN,opacity)
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
    anilos_atlas = anilos_and_ic_atlas_audit(base)
    if initial_hashes != hashes():
        raise RuntimeError("source changed during computation")
    return {"schema":"r98_evolved_bianchi_test_radiation_v1","run_status":"completed",
            "scope":"conditional k=0 test radiation; prescribed xe(volume a); 1-loop radiation momentum/shear audit and near-isotropic AniLoS comparison",
            "physical_calibration":False,"full_einstein_boltzmann":False,"SQ_NATIVE":False,
            "inputs_sha256":initial_hashes,"python":platform.python_version(),"numpy":np.__version__,
            "scipy":scipy.__version__,"processor":platform.machine(),"threads":{k:os.getenv(k) for k in
            ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS")},"elapsed_seconds":time.perf_counter()-start,
            "max_RSS_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "anilos_near_isotropic_and_ic_atlas":anilos_atlas,"families":rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    result = compute()
    encoded = json.dumps(result,indent=2,allow_nan=False)+"\n"
    args.output.write_text(encoded,encoding="utf-8")
    print(f"{len(result['families'])} families in {result['elapsed_seconds']:.1f}s; {args.output}")
