"""Pinned REC/REI material and independent checks for a finite normal-observer interval."""
from __future__ import annotations

import hashlib
import io
import subprocess
from pathlib import Path

import numpy as np

C_SIGMA_T = 299792458.0 * 6.6524587051e-29  # m^3/s, original REC/REI cross section
REC_REV = "4cffa8a0abdb104a40cac17cfc65593bec909fb3"
REC_PATH = ("research/rec_r3o_grid_frontiers_20261019/reused_h_trace_001/producer_inputs/"
            "independent_integer_z_history.csv")
REC_SHA = "c7c113af50fd49e7937a3bfef15ac2e295fe51cc161e83196bc921e0f02c98ce"
REI_REV = "56dc609ea9b801c88d3364aed3eee140b3a20d46"
REI_PATH = ("research/rei_igm_sync_20261116/approximation_validity/incremental_fifth/"
            "results_five/five_case_abundances.csv.gz")
REI_SHA = "f4bc0046d79faf2cd13ae7ed78135503306c7d76c11580e4601a757c407bc83d"
CASES = {"ZERO": 0., "SHEAR_PLUS": .01, "SHEAR_MINUS": -.01,
         "SHEAR_HALF_PLUS": .005, "SHEAR_HALF_MINUS": -.005}
MATERIAL_HEADER = ("normal_t_s n_reference_rest_m3 electrons_per_reference "
                   "beta_x beta_y beta_z dir_x dir_y dir_z N b").split()


def git_blob(repository: Path, revision: str, path: str, sha: str) -> bytes:
    data = subprocess.check_output(["git", "-C", str(repository), "show", f"{revision}:{path}"])
    if hashlib.sha256(data).hexdigest() != sha:
        raise ValueError(f"unrecognized material bytes at {revision}:{path}")
    return data


def rec_material(data: bytes) -> tuple[np.ndarray, np.ndarray]:
    """q=0 original HyRec 2012 material in 1200 >= z >= 1000 with its own source clock.

    The expansion/density constants are HyRec2012Cosmology at REC_REV, matching
    scripts/c_harness/original_hyrec_low_z_to_end_harness.c. xe is per H nucleus.
    """
    table = np.genfromtxt(io.BytesIO(data), names=True, delimiter=",")
    if table.shape != (8001,) or not np.array_equal(table["z"], np.arange(8000, -1, -1)):
        raise ValueError("expected the original 8001 integer redshifts")
    select = (table["z"] <= 1200) & (table["z"] >= 1000)
    u, xe = 1.0 + table["z"][select], table["xe"][select]
    N = -np.log(u)
    radiation = 4.48162687719e-7 * 2.7255**4 * (1.0 + .227107317660239 * 3.03821934419124)
    H = 3.2407792896393e-18 * np.sqrt(.14309694000000003*u**3 + .31113726660800006 + radiation*u**4)
    nh = 11.223846333047 * .0224 * (1 - .2454) * u**3
    time = np.r_[0., np.cumsum(np.diff(N) * (.5 / H[:-1] + .5 / H[1:]))]
    zeros = np.zeros_like(time)
    rows = np.column_stack((time, nh, xe, zeros, zeros, zeros, zeros, zeros,
                            np.ones_like(zeros), N, zeros))
    return rows, H


def rei_clock(N: np.ndarray, qref: float) -> np.ndarray:
    """AXBI's non-tilted, stress-free signed LRS-I scenario; qref defined at zbar=20."""
    a = np.exp(N)
    h0 = 67.4e5 / 3.0856775814913673e24
    def flrw2(scale):
        return h0**2 * (9.2e-5 / scale**4 + .315 / scale**3 + 1 - .315 - 9.2e-5)
    return np.sqrt(flrw2(a) + qref*qref * flrw2(1/21) / (21*a)**6)


def material_stream(rows: np.ndarray, H: np.ndarray) -> np.ndarray:
    """Bare rest-frame Thomson rate per normal d ln a. BASS applies its own Doppler factor."""
    if rows.ndim != 2 or rows.shape[1] != len(MATERIAL_HEADER) or len(rows) < 2:
        raise ValueError("invalid material records")
    if H.shape != (len(rows),) or not (np.isfinite(rows).all() and np.isfinite(H).all()):
        raise ValueError("invalid material/clock values")
    if (np.any(H <= 0) or np.any(rows[:, 1:3] < 0)
            or np.any(np.diff(rows[:, 0]) <= 0) or np.any(np.diff(rows[:, 9]) <= 0)
            or np.any(np.sum(rows[:, 3:6]**2, axis=1) >= 1)
            or not np.allclose(np.sum(rows[:, 6:9]**2, axis=1), 1, atol=1e-11, rtol=0)):
        raise ValueError("invalid chronology, density, tilt or propagation direction")
    return np.column_stack((rows[:, 9]-rows[0, 9], C_SIGMA_T * rows[:, 1] * rows[:, 2] / H, rows[:, 3:6]))


def validate_cells(rows: np.ndarray, csv_table: np.ndarray) -> tuple[np.ndarray, dict]:
    """Check all 1000 REI (or 200 REC) cells including thin-bin masses at the receiver."""
    near, far = (csv_table[k] for k in ("near_t_s", "far_t_s"))
    ix = np.argsort(far)
    if not (np.array_equal(far[ix], rows[:-1, 0]) and np.array_equal(near[ix], rows[1:, 0])):
        raise ValueError("REC times do not coincide with REI material knots")
    dtau, t_near, t_far, p = (csv_table[k][ix] for k in ("delta_tau", "tau_near", "tau_far", "visibility_mass"))
    # This validation lane uses only the physical non-tilted donors.
    if np.any(rows[:, 3:6] != 0):
        raise ValueError("comparison requires the donor non-tilted matter frame")
    # Independent Gauss rule for the original REC log-density × linear charge interpolant.
    u, w = np.polynomial.legendre.leggauss(8)
    u = (u+1)/2
    n0, n1 = rows[:-1,1,None], rows[1:,1,None]
    x0, x1 = rows[:-1,2,None], rows[1:,2,None]
    integrand = n0 * np.exp(u * np.log(n1/n0)) * ((1-u)*x0+u*x1)
    ref = .5*C_SIGMA_T * (integrand @ w) * np.diff(rows[:,0])
    cumulative = np.r_[np.cumsum(ref[::-1])[::-1], 0.]
    if not (np.isfinite(dtau).all() and np.all(dtau >= 0)
            and np.allclose(dtau, ref, rtol=3e-12, atol=1e-18)
            and np.allclose(t_far, cumulative[:-1], rtol=3e-12, atol=1e-16)
            and np.allclose(t_near, cumulative[1:], rtol=3e-12, atol=1e-16)
            and np.allclose(p, np.exp(-t_near)*(-np.expm1(-dtau)), rtol=3e-12, atol=1e-18)):
        raise ValueError("REC opacity cells failed proper-clock or finite-receiver comparison")
    taus = np.r_[t_far, t_near[-1]]
    norm_error = abs(float(np.sum(p) + np.exp(-taus[0]) - 1))
    if norm_error > 5e-13:
        raise ValueError("visibility did not telescope")
    return taus, {"proper_time_tau": float(taus[0]), "max_abs_cell_depth_error": float(np.max(abs(dtau-ref))),
                  "visibility_mass": float(np.sum(p)), "survival": float(np.exp(-taus[0])),
                  "survival_plus_visibility_error": norm_error}


def r105_quadrupoles(N: np.ndarray, b: np.ndarray, tau: np.ndarray, z: np.ndarray, order=48):
    """Use the conserved covariant photon momentum for ds_i = a(e^-b,e^-b,e^2b)_i dx^i."""
    mu, weights = np.polynomial.legendre.leggauss(order)
    P2 = (3*mu**2-1)/2
    d = b-b[-1]
    redshift = N[-1]-N + .5*np.log1p((1-mu[:,None]**2)*np.expm1(2*d)+mu[:,None]**2*np.expm1(-4*d))
    target = np.log1p(z)
    if (np.any(np.diff(redshift,axis=1) >= 0) or np.any(z < 0)
            or np.max(target) > np.min(redshift[:,0])):
        raise ValueError("redshift outside monotone common support")
    sky = np.array([np.interp(target, r[::-1], tau[::-1]) for r in redshift])
    mono = .5 * weights @ sky
    return mono, 2.5 * (weights * P2) @ (sky-mono)


def conservative_material(knots: np.ndarray, dtau: np.ndarray) -> tuple[np.ndarray, dict]:
    """Lift REC non-tilted cell exposures to BASS's continuous piecewise-linear rate.

    Preserve physical rates at original knots. One midpoint per cell is fixed by its
    exposure: integral q dN = h (q_L + 2 q_mid + q_R)/4. A negative midpoint would
    violate positivity and requires another material representation.
    """
    if dtau.shape != (len(knots)-1,) or np.any(knots[:,2:] != 0):
        raise ValueError("REC→BASS exposure reconstruction requires matching non-tilted material cells")
    width=np.diff(knots[:,0])
    midpoint_knots=(knots[:-1]+knots[1:])*.5
    raw=midpoint_knots[:,1].copy()
    midpoint_knots[:,1] = 2.*dtau/width - .5*(knots[:-1,1]+knots[1:,1])
    if (not np.isfinite(midpoint_knots).all() or np.any(midpoint_knots[:,1]<0)
            or np.any(dtau<0) or np.any(width<=0)):
        raise ValueError("no nonnegative single-midpoint conservative reconstruction")
    stream=np.empty((2*len(knots)-1,knots.shape[1]))
    stream[::2],stream[1::2] = knots,midpoint_knots
    recovered=np.sum((np.diff(stream[:,0])*.5*(stream[:-1,1]+stream[1:,1])).reshape(-1,2),axis=1)
    if not np.allclose(recovered,dtau,rtol=8e-12,atol=1e-18):
        raise ArithmeticError("tabulated BASS material fails REC cell exposure conservation")
    return stream, {"max_abs_cell_depth_error":float(np.max(abs(recovered-dtau))),
                    "max_midpoint_shift_vs_linear_endpoints_per_efold":float(np.max(abs(midpoint_knots[:,1]-raw))),
                    "min_rate_per_efold":float(np.min(stream[:,1])),
                    "integrated_depth_per_efold":float(np.sum(recovered))}
