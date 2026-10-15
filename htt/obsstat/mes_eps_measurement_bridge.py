"""SAG(1997) covariant-CMB multipole norm vs observational harmonic images.

This is a same-sky measurement/normalization calculation. In particular
neither a beam-smoothed masked Planck map nor a simulation ensemble identifies
the MES Copernican derivative bounds, observer radiation-frame dipole, or
global Bianchi geometry shear.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.linalg import cho_factor, cho_solve

T0_MICROK = 2.72548e6
T0_SOURCE = "Legacy HTT/CMB T0=2.72548 K, same as Loop6 and Loop7"
MES_PR124_GEODESIC_SHEAR = (5 / 3, 3, 3 / 7)
MES_PR124_GEODESIC_VORTICITY = (10 / 3, 2 / 15, 0)


class EpsilonBridgeError(ValueError):
    pass


def pstf_norm_factor(ell: int) -> float:
    """sqrt(tau_A tau^A) / [sqrt(C_ell)/T0], using SAG Eq. (15,17).

    C_l = (1/(2l+1)) sum_m |a_lm|^2, with orthonormal spherical Y_lm.
    Exact relation tau_A tau^A = (2l+1)(2l)!/[2^l(l!)^2] *
                                  (sum_m |a_lm|^2)/(4pi T0^2).
    """
    if not isinstance(ell, (int, np.integer)) or not 1 <= ell <= 30:
        raise EpsilonBridgeError("ell is an integer in [1,30]")
    return (2 * ell + 1) * math.sqrt(
        math.factorial(2 * ell) / (
            4 * math.pi * 2 ** ell * math.factorial(ell) ** 2
        )
    )


def eps_from_real_multipole(row, ell: int, *, t0_uK: float = T0_MICROK) -> dict:
    """One l=2 or l=3 band in orthonormal real m0, sqrt2(Re), sqrt2(Im)."""
    a = np.asarray(row)
    if (np.iscomplexobj(a) or a.shape != (2 * ell + 1,)
        or not np.isfinite(a).all()
        or not np.isfinite(t0_uK) or t0_uK <= 0
        or ell not in (2, 3)):
        raise EpsilonBridgeError("real orthonormal fixed-ell band and positive CMB T0 expected")
    power = float(a @ a / (2 * ell + 1))
    eps_cl = math.sqrt(power) / t0_uK
    norm = pstf_norm_factor(ell) * eps_cl
    return {
        "ell": ell,
        "C_ell_microK2": power,
        "sqrtCl_over_T0": eps_cl,
        "DeltaT_l_over_T0": math.sqrt(
            (2 * ell + 1) * power / (4 * math.pi)
        ) / t0_uK,
        "SAG_eq17_covariant_rms_tensor_norm": norm,
        "sag_vs_sqrtCl_factor": pstf_norm_factor(ell),
    }


def eps_from_retained(row, *, t0_uK: float = T0_MICROK) -> dict:
    a = np.asarray(row)
    if np.iscomplexobj(a) or a.shape != (32,) or not np.isfinite(a).all():
        raise EpsilonBridgeError("orthonormal-real l=2..5 32D row expected")
    return {"2": eps_from_real_multipole(a[:5], 2, t0_uK=t0_uK),
            "3": eps_from_real_multipole(a[5:12], 3, t0_uK=t0_uK)}


def geodesic_algebraic_sector_ceiling(eps2: float, eps3: float,
                                      *, eps1: float = 0) -> dict:
    """Algebraic sensitivity only; does not certify C1/C2 Copernican bounds."""
    eps = np.array((eps1, eps2, eps3), float)
    if np.iscomplexobj(eps2) or np.iscomplexobj(eps3) or not np.isfinite(eps).all() or np.any(eps < 0):
        raise EpsilonBridgeError("nonnegative real covariant multipole parameters")
    s = float(np.dot(MES_PR124_GEODESIC_SHEAR, eps))
    w = float(np.dot(MES_PR124_GEODESIC_VORTICITY, eps))
    return {"B_sigma_over_Theta": s, "B_omega_over_Theta": w,
            "Sigma2_anchor_only_if_conditions_met": 1.5*s*s,
            "W2_anchor_only_if_conditions_met": 1.5*w*w,
            "geodesic_acceleration_status": "ZERO_STRUCTURAL_NOT_ESTIMATED",
            "curvature_status": "NO_MES_ANCHOR",
            "derivative_condition": "UNVERIFIED_C1_C2",
            "observer_residual_dipole": "ASSUMED_FOR_ALGEBRA_ONLY"}


def fixed_ols_operator(design, mask):
    """Finite same-sky response R=(X_M^TX_M)^-1 X_M^T; no full pixel covariance."""
    x = np.asarray(design, float)
    m = np.asarray(mask, bool)
    if (x.ndim != 2 or x.shape[0] != len(m) or
        not np.isfinite(x).all() or np.count_nonzero(m) <= x.shape[1]):
        raise EpsilonBridgeError("finite overdetermined design/mask required")
    xx = x[m]
    g = xx.T @ xx
    try:
        c = cho_factor(g, check_finite=False)
        R = cho_solve(c, xx.T, check_finite=False)
    except (np.linalg.LinAlgError, ValueError) as e:
        raise EpsilonBridgeError("masked design not positive definite") from e
    err = float(np.max(np.abs(R @ xx - np.eye(x.shape[1]))))
    if err > 1e-9:
        raise EpsilonBridgeError("masked low-ell response identity failed")
    return R, {"selected_n": int(m.sum()), "design_columns": int(x.shape[1]),
               "design_condition": float(np.linalg.cond(xx)),
               "contained_band_identity_maxabs": err}


def fit_rows_of_simulated_maps(maps, selected, operator, *, count=None, chunk=20):
    """Streaming fixed 36-mode map projection with small 20 x 49k work buffers.

    Caller must provide actual data arrays, paired IDs, and a source-specific
    mask. The kernel makes no noise-independence or exchangeability assumption.
    """
    arr = np.asarray(maps)
    if (arr.ndim != 2 or arr.shape[1] != len(selected)
        or arr.dtype.kind not in "f" or not np.isfinite(arr).all()):
        raise EpsilonBridgeError("finite two-dimensional simulation maps expected")
    n = len(arr) if count is None else int(count)
    if n < 1 or n > len(arr) or chunk < 1:
        raise EpsilonBridgeError("valid map count/chunk expected")
    out = np.empty((n, operator.shape[0]), dtype=float)
    for k in range(0, n, chunk):
        block = arr[k:min(n, k+chunk), :][:, selected]
        out[k:k+len(block)] = block @ operator.T
    return out


def eps_arrays(coefficients, *, t0_uK=T0_MICROK):
    rows = np.asarray(coefficients, float)
    if rows.ndim != 2 or rows.shape[1] not in (12, 32, 36) or not np.isfinite(rows).all():
        raise EpsilonBridgeError("finite l2/3 or l2..5 band coefficient matrix expected")
    # Input has already had monopole/dipole removed when 32 or 12;
    # a 36-column full l0..5 fit includes four nuisance modes.
    band = rows[:, 4:16] if rows.shape[1] == 36 else rows[:, :12]
    out = np.empty((len(band),2),float)
    for k,(ell,start,stop) in enumerate(((2,0,5),(3,5,12))):
        C=np.sum(band[:,start:stop]**2,axis=1)/(2*ell+1)
        out[:,k]=pstf_norm_factor(ell)*np.sqrt(C)/t0_uK
    return out


def gaussian_beam_l(ell: int, fwhm_arcmin: float):
    """Declared illustrative circular Gaussian only, not measured Planck transfer."""
    if fwhm_arcmin <= 0 or not np.isfinite(fwhm_arcmin):
        raise EpsilonBridgeError("finite positive beam FWHM expected")
    sigma_rad=np.deg2rad(fwhm_arcmin/60)/np.sqrt(8*np.log(2))
    return float(np.exp(-.5*ell*(ell+1)*sigma_rad**2))



def nested_children_coverage_to_ring(fine_mask, *, nside_in: int, nside_out: int):
    """Rebin a native NESTED mask to RING coarse coverage without pixel mixing."""
    import healpy as hp
    f = np.asarray(fine_mask)
    if (f.dtype.kind != 'b' or
        not isinstance(nside_in, int) or not isinstance(nside_out, int) or
        not hp.isnsideok(nside_in) or not hp.isnsideok(nside_out) or
        nside_in < nside_out or nside_in % nside_out or
        f.shape != (hp.nside2npix(nside_in),)):
        raise EpsilonBridgeError('native nested fine boolean mask and matching HEALPix resolutions required')
    children = (nside_in // nside_out) ** 2
    return hp.reorder(f.reshape(hp.nside2npix(nside_out),children).mean(axis=1),n2r=True)
