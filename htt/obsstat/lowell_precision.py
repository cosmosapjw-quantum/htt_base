"""Higher-precision low-ell morphology statistics for the K1 E2E max-scan.

The frozen v1 path (`scripts/make_lowell_morphology_real_map.compute_map_statistics`)
extracts the six registered statistics at NSIDE=16, ell=2..8, full-sky. That is
Nyquist-sufficient for ell<=8 but leaves three precision levers on the table, all
realised here as an OPT-IN *re-registered* statistic set (v2), used only by the K1
E2E long-run paths -- the v1 frozen artifact is never touched:

  1. processing NSIDE (default 64): removes the <=1.3% NSIDE=16 pixel-window
     suppression at ell=6..8 (w_8: 0.987 -> 0.999); ceiling for ell<=8.
  2. ell_max (default 30): the ell-summed statistics (S_1/2, parity, planarity)
     use more multipoles -> a genuine information increase. The quadrupole-octupole
     alignment statistics are intrinsically ell=2,3 and are unchanged.
  3. galactic mask + diffuse inpainting: the common temperature mask is applied and
     the masked region diffuse-inpainted (iterative kept-neighbour averaging) BEFORE
     the SHT. Applied IDENTICALLY to the observed map and every simulation, so the
     mask/inpaint response is absorbed into the null and the look-elsewhere p-value
     stays valid (no per-statistic deconvolution claimed).

Same six keys as v1 (s_one_half, parity_even_over_odd_ratio, parity_asymmetry,
planarity_mean, qo_axis_alignment_deg, axis_to_cmb_dipole_deg), so the max-scan
directions/TAILS are reused unchanged. Diagnostic-only; no Bianchi family,
geometry, anisotropy-evidence, or native-solver claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import healpy as hp

from htt.obsstat.lowell_map_features import densify_alm, power_inertia_tensor
from htt.obsstat.scalar_lowell import summarize_lowell_scalars

DEFAULT_PROC_NSIDE = 64
DEFAULT_LMAX = 30
DEFAULT_ELL_MIN = 2
DEFAULT_INPAINT_ITERS = 40


@dataclass(frozen=True)
class PrecisionConfig:
    """The re-registered v2 statistic-set definition (bound into the config hash)."""
    proc_nside: int = DEFAULT_PROC_NSIDE
    lmax: int = DEFAULT_LMAX
    ell_min: int = DEFAULT_ELL_MIN
    masked: bool = True
    inpaint_iters: int = DEFAULT_INPAINT_ITERS

    def as_dict(self) -> dict:
        return {"statistic_set": "v2_precision", "proc_nside": self.proc_nside,
                "lmax": self.lmax, "ell_min": self.ell_min, "masked": self.masked,
                "inpaint_iters": self.inpaint_iters,
                "alignment_stats_ell": [2, 3],  # Q-O stats are intrinsically ell=2,3
                "mask_handling": "diffuse_inpaint_identical_on_obs_and_sims" if self.masked else "full_sky"}


def downgrade_mask(mask_hi: np.ndarray, nside_out: int, keep_threshold: float = 0.9) -> np.ndarray:
    """Downgrade a {0,1} temperature mask to ``nside_out`` and threshold the partial
    coverage. Returns a boolean KEEP mask (True = analysed pixel)."""
    frac = hp.ud_grade(np.asarray(mask_hi, dtype=float), nside_out=nside_out)
    return frac >= keep_threshold


def diffuse_inpaint(m: np.ndarray, keep: np.ndarray, n_iter: int = DEFAULT_INPAINT_ITERS) -> np.ndarray:
    """Diffuse-inpaint the masked region: iteratively replace each masked pixel with
    the mean of its (8) neighbours, holding the kept pixels fixed. Deterministic; no
    randomness. This is the standard low-ell mask treatment for phase-bearing
    statistics, applied identically to observed and simulated maps."""
    m = np.asarray(m, dtype=float).copy()
    keep = np.asarray(keep, dtype=bool)
    if keep.all():
        return m
    nside = hp.npix2nside(m.size)
    masked_idx = np.flatnonzero(~keep)
    neigh = hp.get_all_neighbours(nside, masked_idx)   # (8, n_masked); -1 where none
    m[masked_idx] = float(np.mean(m[keep]))            # seed with the kept-sky mean
    for _ in range(int(n_iter)):
        vals = np.where(neigh >= 0, m[neigh], np.nan)
        m[masked_idx] = np.nanmean(vals, axis=0)
    return m


def _filtered_axis(alm_packed: np.ndarray, keep_ells: set[int], lmax: int,
                   nside: int, pix_vectors: np.ndarray) -> np.ndarray:
    """Principal power axis of the map filtered to ``keep_ells`` (Q-O diagnostic)."""
    filtered = np.zeros_like(alm_packed)
    for ell in keep_ells:
        for mm in range(0, ell + 1):
            idx = hp.Alm.getidx(lmax, ell, mm)
            filtered[idx] = alm_packed[idx]
    fmap = hp.alm2map(filtered, nside=nside, lmax=lmax)
    tensor = power_inertia_tensor(fmap, pix_vectors)
    evals, evecs = np.linalg.eigh(tensor)
    axis = evecs[:, int(np.argmax(evals))]
    for c in axis:                                     # antipodal sign fix (as v1)
        if abs(c) > 1.0e-12:
            if c < 0:
                axis = -axis
            break
    return axis / np.linalg.norm(axis)


def _angle_deg(u: np.ndarray, v: np.ndarray) -> float:
    c = abs(float(np.dot(u, v))) / (np.linalg.norm(u) * np.linalg.norm(v))
    return float(np.degrees(np.arccos(np.clip(c, 0.0, 1.0))))


def precision_map_statistics(temp_map: np.ndarray, cmb_apex: np.ndarray,
                             cfg: PrecisionConfig,
                             keep_mask: np.ndarray | None = None,
                             pix_vectors: np.ndarray | None = None) -> dict[str, float]:
    """The six registered low-ell statistics under the v2 precision config.

    ``temp_map`` must already be at ``cfg.proc_nside`` (uK). ``keep_mask`` (boolean,
    proc_nside) is required iff ``cfg.masked``. Returns exactly the v1 six public keys.
    """
    nside, lmax = cfg.proc_nside, cfg.lmax
    if hp.npix2nside(np.asarray(temp_map).size) != nside:
        raise ValueError(f"temp_map must be at NSIDE={nside}")
    if pix_vectors is None:
        pix_vectors = np.asarray(hp.pix2vec(nside, np.arange(hp.nside2npix(nside)))).T

    work = np.asarray(temp_map, dtype=float)
    mask_status = "full_sky"
    if cfg.masked:
        if keep_mask is None:
            raise ValueError("cfg.masked=True requires keep_mask")
        work = diffuse_inpaint(work, keep_mask, cfg.inpaint_iters)
        mask_status = "diffuse_inpaint"

    alm = hp.map2alm(work, lmax=lmax, iter=3)
    dense = densify_alm(alm, lmax)
    summary = summarize_lowell_scalars(alm_by_lm=dense, ell_min=cfg.ell_min,
                                       ell_max=lmax, channel="TT", mask_status=mask_status)
    axis2 = _filtered_axis(alm, {2}, lmax, nside, pix_vectors)
    axis3 = _filtered_axis(alm, {3}, lmax, nside, pix_vectors)
    axis23 = _filtered_axis(alm, {2, 3}, lmax, nside, pix_vectors)
    return {
        "s_one_half": float(summary.s_one_half),
        "parity_even_over_odd_ratio": float(summary.parity["even_over_odd_ratio"]),
        "parity_asymmetry": float(summary.parity["asymmetry"]),
        "planarity_mean": float(summary.planarity["mean"]),
        "qo_axis_alignment_deg": _angle_deg(axis2, axis3),
        "axis_to_cmb_dipole_deg": _angle_deg(axis23, np.asarray(cmb_apex, dtype=float)),
    }
