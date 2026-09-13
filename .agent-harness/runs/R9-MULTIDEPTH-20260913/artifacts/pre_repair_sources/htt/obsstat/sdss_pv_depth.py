"""Depth features from the SDSS PV release, not a physical observation law.

The response is to additive log-distance angular fields in redshift shells.
It is not an observer-boost, global-tilt or radiation-jet response. Quoted
per-galaxy errors never supply an independent-row covariance in this module.
"""
from dataclasses import dataclass
import io
import re

import numpy as np

from common.depth_path import DepthRepresentation


BASIS = ("monopole", "dipole_x", "dipole_y", "dipole_z", "stf_xx",
         "stf_yy", "stf_xy", "stf_xz", "stf_yz")


@dataclass(frozen=True)
class Catalogue:
    ids: np.ndarray
    ra: np.ndarray
    dec: np.ndarray
    redshift: np.ndarray
    logdist: np.ndarray
    mask: np.ndarray
    control: np.ndarray | None = None
    truth: np.ndarray | None = None
    source_ids: np.ndarray | None = None


def read_catalogue(payload, *, mock=False):
    """Read the source's named columns; preserve integer identities as strings."""
    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    header, body = text.split("\n", 1)
    delimiter = "," if mock else None
    names = header.lstrip("# ").strip().split(delimiter)
    wanted = (["ID", "RA", "Dec", "z_obs", "logdist", "logdist_true"] if mock else
              ["objid", "RA", "Dec", "zcmb", "logdist", "in_mask", "logdist_corr"])
    if len(names) != len(set(names)) or any(name not in names for name in wanted):
        raise ValueError("missing or duplicate release column")
    dtype = [(wanted[0], "U32")] + [(name, float) for name in wanted[1:]]
    rows = np.loadtxt(io.StringIO(body), delimiter=delimiter,
                      usecols=[names.index(name) for name in wanted], dtype=dtype, ndmin=1)
    source_ids = rows[wanted[0]]
    # Mock ID is not a unique row key in the public archive. Preserve all
    # occurrences; a member name plus row number identifies a mock observation.
    ids = (np.array([f"row:{i}|ID:{value}" for i, value in enumerate(source_ids)])
           if mock else source_ids)
    if len(rows) == 0 or len(set(ids)) != len(rows):
        raise ValueError("empty catalogue or duplicate row identities")
    if any(not np.all(np.isfinite(rows[name])) for name in wanted[1:]):
        raise ValueError("nonfinite catalogue values; no silent row deletion")
    if np.any((rows["RA"] < 0) | (rows["RA"] >= 360) | (np.abs(rows["Dec"]) > 90)):
        raise ValueError("invalid equatorial coordinates")
    if not mock and not np.all(np.isin(rows["in_mask"], [0, 1])):
        raise ValueError("nonbinary mask")
    return Catalogue(ids, rows["RA"], rows["Dec"], rows[wanted[3]], rows["logdist"],
                     np.ones(len(rows), dtype=bool) if mock else rows["in_mask"] == 1,
                     None if mock else rows["logdist_corr"],
                     rows["logdist_true"] if mock else None, source_ids)


def mock_identity(name):
    match = re.fullmatch(r"(?:mocks/)?MOCK_HAMHOD_SDSS_v5_R19(\d{3})\.([0-7])_err_corr", name)
    if match is None:
        raise ValueError("unexpected SDSS mock member identity")
    return tuple(map(int, match.groups()))


def angular_basis(ra, dec):
    ra, dec = np.deg2rad(ra), np.deg2rad(dec)
    x, y, z = np.cos(dec)*np.cos(ra), np.cos(dec)*np.sin(ra), np.sin(dec)
    return np.column_stack((np.ones(len(x)), x, y, z, x*x-z*z, y*y-z*z,
                            2*x*y, 2*x*z, 2*y*z))


def representation(maxima):
    ids = tuple(f"z<{z:g}:{b}" for z in maxima for b in BASIS)
    return DepthRepresentation((9,)*len(maxima), (np.eye(9),)*(len(maxima)-1), ids,
                               "SDSS_PV_single_FP_unit_weight_cumulative_z_v1")


def extract_depth(cat, *, z_min, maxima, rank_tol=1e-10):
    """Refit all depth projections on one complete catalogue.

    Every cumulative window has its own measured sky response. The returned
    response multiplies 9 independent additive eta coefficients per disjoint
    redshift shell; it includes the overlap between shells and windows.
    """
    maxima = np.asarray(maxima, dtype=float)
    if (maxima.ndim != 1 or len(maxima) < 2 or not np.all(np.isfinite(maxima))
            or not np.isfinite(z_min) or maxima[0] <= z_min
            or np.any(np.diff(maxima) <= 0) or not 0 < rank_tol < 1):
        raise ValueError("ordered depth windows and rank tolerance required")
    x = angular_basis(cat.ra, cat.dec)
    shell = np.searchsorted(maxima, cat.redshift, side="right")
    eligible = cat.mask & (cat.redshift > z_min)
    values, counts, spectra, responses, controls, truths = [], [], [], [], [], []
    for j, maximum in enumerate(maxima):
        selected = eligible & (cat.redshift < maximum)
        design = x[selected]
        u, s, vt = np.linalg.svd(design, full_matrices=False)
        if len(s) != 9 or s[-1] <= rank_tol*s[0]:
            raise ValueError(f"unresolved angular response at depth {j}; retain failed mock")
        operator = (vt.T / s) @ u.T
        values.append(operator @ cat.logdist[selected])
        counts.append(int(np.sum(selected)))
        spectra.append(s)
        responses.append(np.hstack([operator @ (design * (shell[selected] == k)[:, None])
                                    for k in range(len(maxima))]))
        if cat.control is not None:
            controls.append(operator @ cat.control[selected])
        if cat.truth is not None:
            truths.append(operator @ cat.truth[selected])
    return {"Y": np.concatenate(values), "counts": np.array(counts),
            "singular_values": np.array(spectra), "response": np.vstack(responses),
            "control": np.concatenate(controls) if controls else None,
            "truth": np.concatenate(truths) if truths else None}


def ensemble_summary(features, box_ids, rep):
    """Estimate full moments on training boxes, with no Gaussian promotion.

    All eight observers from a box stay together. The covariance is the
    descriptive sample covariance of released mock vectors, not a certified
    population covariance or a confidence law. No iid claim is made.
    """
    y = np.asarray(features, dtype=float)
    boxes = np.asarray(box_ids)
    if (y.ndim != 2 or y.shape[1] != len(rep.feature_ids) or boxes.shape != (len(y),)
            or not np.all(np.isfinite(y)) or not np.issubdtype(boxes.dtype, np.integer)):
        raise ValueError("complete aligned feature vectors and integer box IDs required")
    training = boxes % 2 == 0
    if np.sum(training) <= y.shape[1] or np.sum(~training) < 2:
        raise ValueError("insufficient box-split mock vectors")
    train = y[training]
    mean = train.mean(axis=0)
    covariance = np.cov(train, rowvar=False, ddof=1)
    h, t = rep.H, rep.T
    return {"mean": mean, "covariance": covariance,
            "contrast_mean": h @ mean, "contrast_covariance": h @ covariance @ h.T,
            "anchored_mean": t @ mean, "anchored_covariance": t @ covariance @ t.T,
            "training_mask": training,
            "evaluation_residuals": y[~training] - mean,
            "evaluation_contrasts": (y[~training] - mean) @ h.T,
            "law_status": "ESTIMATED_MOMENTS_ONLY", "probability": None,
            "physical_confidence_image": "UNAVAILABLE"}
