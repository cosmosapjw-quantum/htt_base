"""Public-input diagnostic for the CF3--SDSS PV zero-point connection.

This HTT calibration component
does not promote the public catalogues to a replay of Howlett et al. (2022)
Eq. (25): the public CF3 table provides PGCs and the SDSS release provides
Tempel group fields, but this artifact has no released CF3-to-Tempel group
membership crosswalk.  In particular, group id zero is one singleton per row.

All calibration estimates require a caller-supplied *joint* covariance.  Row
errors only define group-consensus coefficients; they are never silently made
into an independent covariance model.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from htt.infer.r7_gaussian_law import decompose_covariance


@dataclass(frozen=True)
class JoinedIndividualRows:
    pgc: np.ndarray
    sdss_logdist: np.ndarray
    sdss_logdist_err: np.ndarray
    sdss_zcmb: np.ndarray
    cf3_distance_mpc: np.ndarray
    cf3_distance_modulus: np.ndarray
    cf3_distance_modulus_err: np.ndarray
    cf3_distance_source: np.ndarray
    cf3_vcmb_km_s: np.ndarray
    sdss_group_id: np.ndarray
    sdss_group_richness: np.ndarray


@dataclass(frozen=True)
class CalibrationEstimate:
    offset_cf3_minus_sdss_dex: float
    standard_error_dex: float
    differences_dex: np.ndarray
    difference_operator: np.ndarray
    consensus_operator: np.ndarray


def flat_comoving_distance_mpc(redshift: np.ndarray, *, h0_km_s_mpc: float = 75.0,
                               omega_m: float = 0.31) -> np.ndarray:
    """Flat-LambdaCDM line-of-sight comoving distance in physical Mpc.

    The CF3 ``Dist`` field is luminosity distance in Mpc.  Thus the corresponding
    distance-indicator comoving distance is ``Dist / (1 + z)`` in physical Mpc.
    This function also returns physical Mpc, using H0=75 as requested; no extra
    factor of ``h`` is admissible.  The SDSS paper's h^-1 Mpc convention is
    converted by exactly this physical-H0 evaluation before forming the ratio.
    """
    z = np.asarray(redshift, dtype=float)
    if (np.any(~np.isfinite(z)) or np.any(z < 0) or not np.isfinite(h0_km_s_mpc)
            or not np.isfinite(omega_m) or h0_km_s_mpc <= 0 or not 0 < omega_m < 1):
        raise ValueError("finite non-negative redshifts and flat cosmology required")
    # Fixed Gauss--Legendre quadrature is deterministic and adequate only for
    # this catalogue diagnostic; it is not an external cosmology code replay.
    nodes, weights = np.polynomial.legendre.leggauss(64)
    sample = z[..., None] * (nodes + 1.0) / 2.0
    inv_e = 1.0 / np.sqrt(omega_m * (1.0 + sample) ** 3 + (1.0 - omega_m))
    return 299792.458 / h0_km_s_mpc * z / 2.0 * np.sum(weights * inv_e, axis=-1)


def cf3_eta_from_luminosity_distance(cf3_distance_mpc: np.ndarray,
                                     individual_zcmb: np.ndarray) -> np.ndarray:
    """Return eta_CF3 = log10[D_com(z; H0=75)/(D_L,CF3/(1+z))]."""
    dl = np.asarray(cf3_distance_mpc, dtype=float)
    z = np.asarray(individual_zcmb, dtype=float)
    if dl.shape != z.shape or np.any(~np.isfinite(dl)) or np.any(dl <= 0) or np.any(z <= 0):
        raise ValueError("aligned positive CF3 luminosity distances and redshifts are required")
    return np.log10(flat_comoving_distance_mpc(z) / (dl / (1.0 + z)))


def cf3_eta_from_distance_modulus(cf3_distance_modulus: np.ndarray,
                                  individual_zcmb: np.ndarray) -> np.ndarray:
    """CF3 eta using its published individual distance modulus.

    ``D_L/Mpc = 10**((DM-25)/5)``.  This is the selected diagnostic convention;
    it avoids rounding ``Dist`` independently of the published modulus.
    """
    dm = np.asarray(cf3_distance_modulus, dtype=float)
    if np.any(~np.isfinite(dm)):
        raise ValueError("finite CF3 distance moduli required")
    return cf3_eta_from_luminosity_distance(10.0 ** ((dm - 25.0) / 5.0), individual_zcmb)


def _sdss_columns(path: str | Path) -> dict[str, np.ndarray]:
    names = Path(path).read_text(encoding="utf-8").splitlines()[0].lstrip("#").split()
    needed = ("PGC", "objid", "zcmb", "IDgroupT17", "NgroupT17", "logdist", "logdist_err",
              "logdist_corr", "logdist_corr_err")
    if any(n not in names for n in needed):
        raise ValueError("SDSS release is missing a required public field")
    data = np.genfromtxt(path, names=True, dtype=None, encoding="ascii")
    return {name: np.asarray(data[name]) for name in needed}


def read_public_pgc_join(sdss_path: str | Path, cf3_table3_path: str | Path,
                         *, corrected: bool = False) -> JoinedIndividualRows:
    """Exact PGC join of public SDSS PV and CF3 individual entries.

    ``corrected=False`` deliberately selects the unshifted single-FP SDSS
    ``logdist`` for the individual diagnostic.  ``corrected=True`` selects the
    released group-richness FP value but does not apply any zero-point shift.
    """
    sdss = _sdss_columns(sdss_path)
    log_name = "logdist_corr" if corrected else "logdist"
    err_name = "logdist_corr_err" if corrected else "logdist_err"
    by_pgc: dict[int, tuple[float, float, float, int, int]] = {}
    for pgc, value, error, zcmb, group, richness in zip(sdss["PGC"], sdss[log_name],
                                                  sdss[err_name], sdss["zcmb"],
                                                  sdss["IDgroupT17"], sdss["NgroupT17"], strict=True):
        key = int(pgc)
        if key in by_pgc:
            raise ValueError("SDSS PGC is not unique; no arbitrary duplicate resolution")
        by_pgc[key] = (float(value), float(error), float(zcmb), int(group), int(richness))
    cf3: dict[int, tuple[float, float, float, str, float]] = {}
    for line in Path(cf3_table3_path).read_text(encoding="ascii").splitlines():
        pgc = int(line[0:7])
        if pgc in cf3:
            raise ValueError("CF3 PGC is not unique; no arbitrary duplicate resolution")
        # VizieR J/AJ/152/50 table3: Dist (8-14) Mpc, e_DM (24-27) mag,
        # Vcmb (190-194) km/s.  These fixed-width fields are primary-source
        # definitions, not inferred columns.
        cf3[pgc] = (float(line[8:14]), float(line[17:22]), float(line[23:27]),
                    line[28:41].strip(), float(line[189:194]))
    shared = sorted(set(by_pgc).intersection(cf3))
    if not shared:
        raise ValueError("no exact PGC overlap")
    return JoinedIndividualRows(
        pgc=np.asarray(shared, dtype=int),
        sdss_logdist=np.asarray([by_pgc[x][0] for x in shared]),
        sdss_logdist_err=np.asarray([by_pgc[x][1] for x in shared]),
        sdss_zcmb=np.asarray([by_pgc[x][2] for x in shared]),
        cf3_distance_mpc=np.asarray([cf3[x][0] for x in shared]),
        cf3_distance_modulus=np.asarray([cf3[x][1] for x in shared]),
        cf3_distance_modulus_err=np.asarray([cf3[x][2] for x in shared]),
        cf3_distance_source=np.asarray([cf3[x][3] for x in shared]),
        cf3_vcmb_km_s=np.asarray([cf3[x][4] for x in shared]),
        sdss_group_id=np.asarray([by_pgc[x][3] for x in shared]),
        sdss_group_richness=np.asarray([by_pgc[x][4] for x in shared]),
    )


def group_consensus_operator(group_ids: Iterable[int], row_standard_errors: Iterable[float]) -> np.ndarray:
    """Map rows to inverse-variance consensus values with zero IDs as singletons."""
    raw_ids = np.asarray(tuple(group_ids), dtype=float)
    if np.any(~np.isfinite(raw_ids)) or np.any(raw_ids < 0) or np.any(raw_ids != np.floor(raw_ids)):
        raise ValueError("group IDs must be non-negative integers; zero means singleton")
    ids = raw_ids.astype(int)
    errors = np.asarray(tuple(row_standard_errors), dtype=float)
    if ids.ndim != 1 or errors.shape != ids.shape or np.any(~np.isfinite(errors)) or np.any(errors <= 0):
        raise ValueError("aligned positive row standard errors are required")
    labels = [("group", int(g)) if g != 0 else ("ungrouped_row", int(i))
              for i, g in enumerate(ids)]
    unique = list(dict.fromkeys(labels))
    operator = np.zeros((len(unique), len(ids)))
    for j, label in enumerate(unique):
        chosen = np.asarray([x == label for x in labels])
        weights = 1.0 / errors[chosen] ** 2
        operator[j, chosen] = weights / weights.sum()
    return operator


def calibrate_shared_offset(sdss_values: Iterable[float], cf3_values: Iterable[float],
                            joint_covariance: np.ndarray,
                            *, consensus_operator: np.ndarray | None = None) -> CalibrationEstimate:
    """Estimate CF3-minus-SDSS offset using explicit full joint covariance.

    The input vector is ordered ``[SDSS rows, CF3 rows]``.  If a consensus
    operator is supplied it acts on the shared row order on both catalogues;
    callers must establish that group alignment before calling.  This preserves
    covariance cross terms under ``L @ Sigma @ L.T`` and refuses an unknown or
    diagonal-only substitute.
    """
    sdss = np.asarray(tuple(sdss_values), dtype=float)
    cf3 = np.asarray(tuple(cf3_values), dtype=float)
    if sdss.ndim != 1 or cf3.shape != sdss.shape or not np.all(np.isfinite(sdss)) or not np.all(np.isfinite(cf3)):
        raise ValueError("finite aligned SDSS and CF3 values required")
    n = len(sdss)
    sigma = _validate_joint_covariance(joint_covariance, n)
    if consensus_operator is None:
        consensus = np.eye(n)
    else:
        consensus = np.asarray(consensus_operator, dtype=float)
        if (consensus.ndim != 2 or consensus.shape[1] != n or not np.all(np.isfinite(consensus))
                or np.any(consensus < 0) or np.any(consensus.sum(axis=1) == 0)
                or len(consensus) == 0 or not np.allclose(consensus.sum(axis=1), 1.0, rtol=0, atol=1e-12)):
            raise ValueError("consensus operator must act on each aligned catalogue row vector")
    difference_operator = np.hstack((-consensus, consensus))
    differences = difference_operator @ np.concatenate((sdss, cf3))
    cov = difference_operator @ sigma @ difference_operator.T
    one = np.ones(len(differences))
    precision_one = _precision_one(cov)
    norm = float(one @ precision_one)
    if not np.isfinite(norm) or norm <= 0:
        raise ValueError("difference covariance is not positive definite")
    weights = precision_one / norm
    return CalibrationEstimate(float(weights @ differences), float(np.sqrt(1.0 / norm)),
                               differences, difference_operator, consensus)


def shared_offset_coefficients(joint_covariance: np.ndarray, *, n_rows: int,
                               consensus_operator: np.ndarray | None = None) -> np.ndarray:
    """Return ``l`` such that delta_CF3-SDSS = ``l @ [SDSS, CF3]``.

    This is separated from the observed values so the same declared calibration
    law can be applied afresh to each full supplied realization.  It requires
    the full joint covariance and therefore cannot turn posterior widths into a
    confidence calculation.
    """
    if n_rows < 1:
        raise ValueError("at least one aligned row is required")
    if consensus_operator is None:
        consensus = np.eye(n_rows)
    else:
        consensus = np.asarray(consensus_operator, dtype=float)
        if (consensus.ndim != 2 or consensus.shape[1] != n_rows or len(consensus) == 0
                or not np.all(np.isfinite(consensus)) or np.any(consensus < 0)
                or not np.allclose(consensus.sum(axis=1), 1.0, rtol=0, atol=1e-12)):
            raise ValueError("consensus operator must act on each aligned catalogue row vector")
    sigma = _validate_joint_covariance(joint_covariance, n_rows)
    d = np.hstack((-consensus, consensus))
    diff_covariance = d @ sigma @ d.T
    one = np.ones(diff_covariance.shape[0])
    precision_one = _precision_one(diff_covariance)
    normalizer = float(one @ precision_one)
    if not np.isfinite(normalizer) or normalizer <= 0:
        raise ValueError("difference covariance is not positive definite")
    return (precision_one / normalizer) @ d


def _validate_joint_covariance(joint_covariance: np.ndarray, n_rows: int) -> np.ndarray:
    sigma = np.asarray(joint_covariance, dtype=float)
    if n_rows < 1 or sigma.shape != (2 * n_rows, 2 * n_rows):
        raise ValueError("explicit joint covariance for [SDSS, CF3] is required")
    decomposition = decompose_covariance(sigma)
    if not decomposition.resolved:
        raise ValueError("joint covariance singular rank unresolved; calibration unavailable")
    return decomposition.covariance


def _precision_one(covariance: np.ndarray) -> np.ndarray:
    """Require a supported positive-definite difference law without a ridge."""
    try:
        np.linalg.cholesky(covariance)
        return np.linalg.solve(covariance, np.ones(covariance.shape[0]))
    except np.linalg.LinAlgError as exc:
        raise ValueError("difference covariance is singular or unsupported; calibration unavailable") from exc


def depth_calibration_operator(depth_projection: np.ndarray, offset_coefficients: np.ndarray,
                               *, n_sdss_rows: int) -> np.ndarray:
    """Joint operator for calibration of a 36-depth (or general) SDSS vector.

    For a depth projection ``M`` acting on SDSS rows and offset coefficient
    ``l`` on ``[SDSS-anchor rows, CF3 rows]``, returns
    ``G=[M,0]+(M@1)[:,None] l[None,:]``.  A caller must provide a covariance
    for the exact input ordering before forming ``G C_joint G.T``.  Contrast
    operators whose rows sum to zero remove this shared additive term; the
    initial level does not, and must be retained.
    """
    m = np.asarray(depth_projection, dtype=float)
    l = np.asarray(offset_coefficients, dtype=float)
    if m.ndim != 2 or m.shape[1] != n_sdss_rows or not np.all(np.isfinite(m)):
        raise ValueError("finite depth projection with declared SDSS row count required")
    if l.ndim != 1 or l.size < n_sdss_rows or not np.all(np.isfinite(l)):
        raise ValueError("offset coefficient vector must include SDSS rows")
    base = np.zeros((m.shape[0], l.size))
    base[:, :n_sdss_rows] = m
    return base + (m @ np.ones(n_sdss_rows))[:, None] * l[None, :]
