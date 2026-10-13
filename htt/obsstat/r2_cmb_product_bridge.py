"""CMB released-product controls and conditional finite dipole/STF statistics.

Monopole/dipole removal follows each product's explicitly supplied processing
convention. Residual fitted ell=1 is never a restored physical dipole. No
covariance, posterior or independence is inferred from same-sky differences.
"""
from __future__ import annotations

import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np

from common.r7_contracts import finite_array
from htt.core.teff_invariants import (
    fourth_moment, fourth_moment_coordinate_jacobian,
    sufficient_positivity_margin,
)
from .planck_lowell_irrep_projection import real_harmonic_l2_to_stf
from .r7_cmb_product_response import build_product_response, real_to_stored


def _kelvin(value, units):
    if units not in {"K", "microK"}:
        raise ValueError("temperature units must be K or microK")
    result = finite_array(value) * (1.0 if units == "K" else 1e-6)
    if not np.all(np.isfinite(result)):
        raise ValueError("temperature conversion overflow")
    return result


def dipole_stf_from_real_harmonics(dipole, quadrupole, *, units="K"):
    """Orthonormal real m0,cos,sin coordinates -> dimensional d_K,S_K.

    Condon--Shortley: Y10=sqrt(3/4pi)z, sqrt2 ReY11=-sqrt(3/4pi)x,
    sqrt2 ImY11=-sqrt(3/4pi)y. Dipole input must be explicitly restored.
    """
    c1 = finite_array(_kelvin(dipole, units), shape=(3,))
    c2 = finite_array(_kelvin(quadrupole, units), shape=(5,))
    d = np.sqrt(3 / (4 * np.pi)) * np.array([-c1[1], -c1[2], c1[0]])
    return d, real_harmonic_l2_to_stf(real_to_stored(c2, 2))


def finite_ansatz_statistic(*, T0, dipole, quadrupole, units="K",
                            source_id, frame, omitted_sup_norm=None):
    """Conditional full-sphere F4 of 1+d.n+n.S.n, never actual full-field F4.

    T0 is supplied angular-mean temperature. Dipole and quadrupole are
    dimensional Cartesian temperature coefficients in one explicit frame.
    Optional omitted_sup_norm bounds |T_rest/T0| over the entire sphere.
    Unknown omission remains unknown, rather than a zero completion.
    """
    if not source_id or not frame:
        raise ValueError("source identity and common frame required")
    t0 = float(_kelvin(T0, units))
    if not np.isfinite(t0) or t0 <= 0:
        raise ValueError("positive finite explicit angular-mean T0 required")
    d = finite_array(_kelvin(dipole, units), shape=(3,)) / t0
    S = finite_array(_kelvin(quadrupole, units), shape=(3, 3)) / t0
    f4 = fourth_moment(d, S)
    margin = sufficient_positivity_margin(d, S)
    if margin <= 0 or not np.isfinite(f4):
        raise ValueError("finite ansatz lacks sufficient positive-temperature certificate")
    envelope = None
    if omitted_sup_norm is not None:
        r = float(omitted_sup_norm)
        if not np.isfinite(r) or r < 0:
            raise ValueError("omitted full-sphere sup norm must be finite and nonnegative")
        M = 1 + np.linalg.norm(d) + np.max(np.abs(np.linalg.eigvalsh(S)))
        envelope = float(4 * (M + r)**3 * r)
        if not np.isfinite(envelope):
            raise ValueError("omitted-mode envelope overflow")
    return {
        "scope": "CONDITIONAL_FINITE_DIPOLE_STF_FULL_SPHERE_ANSATZ",
        "source_id": source_id, "frame": frame, "T0_K": t0,
        "dimensionless_d": d.tolist(), "temperature_STF_S": S.tolist(),
        "F4": f4, "Tbol_K": t0 * f4**0.25,
        "positivity_margin": margin,
        "coordinate_jacobian": fourth_moment_coordinate_jacobian(d, S).tolist(),
        "omitted_modes_sup_norm": omitted_sup_norm,
        "full_field_F4_absolute_error_bound": envelope,
        "full_field_F4_status": "HOLD_OMITTED_MODES_UNKNOWN" if envelope is None else "CONDITIONAL_SUP_NORM_ENVELOPE",
        "posterior_status": "HOLD_JOINT_MEASUREMENT_LAW_UNAVAILABLE",
        "caveats": ["S is temperature quadrupole, not dimensional velocity shear",
                    "Tbol is intensity-equivalent temperature, distinct from directional temperature and T0",
                    "polynomial exactness is conditional on the finite ansatz; no physical closure inferred"],
    }


def released_product_response(product, source, beta, processing):
    """Bind a supplied complete release processor to the existing R7 pullback.

    Caller supplies actual beam/pixel/removal operator and mask; identities
    cannot substitute for its implementation. The source is absolute K.
    This is a response calculation and creates no observation likelihood.
    """
    for key in ("map_source_id", "mask_source_id", "pixel_policy", "dipole_removal"):
        if not product.get(key):
            raise ValueError(f"released product requires {key}")
    if product.get("channel_convention") != "SIGNED_TEMPERATURE_ANISOTROPY":
        raise ValueError("released signed anisotropy convention required")
    if not callable(processing.get("pixel_processor")):
        raise ValueError("actual release beam/pixel/monopole/dipole processor unavailable")
    if processing.get("mask_weights") is None or not processing.get("mask_source_id"):
        raise ValueError("explicit released-product mask and identity required")
    if processing["mask_source_id"] != product["mask_source_id"]:
        raise ValueError("mask identity mismatch")
    if source.get("frame") != product.get("frame"):
        raise ValueError("absolute source and released product must share frame")
    if source.get("temperature_convention") != "ABSOLUTE_THERMODYNAMIC_TEMPERATURE":
        raise ValueError("explicit absolute temperature source convention required")
    return build_product_response(product, source, beta, processing)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def reduced_same_sky_diagnostic(npz_path, metadata_path, *, T0_K=None,
                                dipole_K=None, dipole_source_id=None,
                                frame="GALACTIC", omitted_sup_norm=None):
    """Descriptive R8 coefficient contrasts and optional explicit sensitivity."""
    meta = json.loads(Path(metadata_path).read_text())
    policy = meta["processing"]
    if policy.get("id") != "R8_SAME_SKY_PIXEL_CONTROL_V1":
        raise ValueError("unknown reduced-control processing")
    with np.load(npz_path, allow_pickle=False) as data:
        ids = data["sample_ids"].astype(str).tolist()
        Q = finite_array(data["Q"], shape=(len(ids), 3, 3))
        retained = finite_array(data["retained_K"], shape=(len(ids), 32))
        mask = data["common_mask"]
    if ids != policy["input_products"] or len(ids) != len(set(ids)):
        raise ValueError("control product identity/order mismatch")
    if mask.shape != (49152,) or int(np.count_nonzero(mask)) != policy["valid_pixels"]:
        raise ValueError("reduced mask support mismatch")
    for i in range(len(ids)):
        expected = real_harmonic_l2_to_stf(real_to_stored(retained[i, :5], 2))
        if not np.allclose(Q[i], expected, rtol=2e-13, atol=2e-18):
            raise ValueError("stored tensor/harmonic crosswalk mismatch")
    contrasts = [{"products": [ids[i], ids[j]],
                  "retained_difference_norm_K": float(np.linalg.norm(retained[i]-retained[j])),
                  "quadrupole_difference_frobenius_K": float(np.linalg.norm(Q[i]-Q[j]))}
                 for i, j in combinations(range(len(ids)), 2)]
    result = {
        "owner": "obsstat", "claim_tier": "C0", "scope": "DESCRIPTIVE_REDUCED_SAME_SKY_CONTROL",
        "source_release": "Planck PR3 https://doi.org/10.5270/esa-zfx8b4s",
        "source_identities": {str(npz_path): sha256_file(npz_path), str(metadata_path): sha256_file(metadata_path)},
        "processing": policy, "contrasts": contrasts,
        "product_independence": False, "cross_product_covariance": None,
        "coverage": {"nside": 64, "common_valid_pixels": int(np.count_nonzero(mask)),
                     "pixel_count": len(mask), "retained_ells": [2, 5]},
        "full_field_F4_status": "HOLD_RELEASE_PROCESSOR_AND_PHYSICAL_DIPOLE_AND_OMITTED_MODES",
        "posterior_status": "HOLD_SHARED_SKY_CROSS_PRODUCT_MEASUREMENT_LAW",
        "interpretation": "coefficient differences are descriptive statistics; not bias estimates or independent constraints",
        "conditional_sensitivity": None,
    }
    if (T0_K is None) != (dipole_K is None):
        raise ValueError("conditional sensitivity needs both explicit T0 and physical dipole")
    if T0_K is not None:
        if not dipole_source_id or frame != "GALACTIC":
            raise ValueError("explicit dipole source identity and Galactic common frame required")
        result["conditional_sensitivity"] = [
            dict(product_id=pid, **finite_ansatz_statistic(
                T0=T0_K, dipole=dipole_K, quadrupole=Q[i],
                source_id=dipole_source_id, frame=frame, omitted_sup_norm=omitted_sup_norm))
            for i, pid in enumerate(ids)]
    return result
