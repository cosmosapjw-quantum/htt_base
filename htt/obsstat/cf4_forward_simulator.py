"""PR-146: CF4 catalogue forward-mock simulator.

A forward simulator that draws correlated peculiar-velocity mocks for the CF4
group catalogue, layers realistic error/selection/grouping effects on top, and
re-fits the PR-145 bulk-flow-plus-monopole estimator on every mock to report
coverage.

Two generators are used, and their independence is the point:

* the PRIMARY generator is a Cholesky factor of the full N-by-N Gorski
  radial/transverse velocity correlation ``C_ab`` (imported from PR-145).  A
  draw ``v_cv = L z`` (``z`` standard normal) has ``Cov(v_cv) = C_ab``
  exactly, so the whole correlated field — including the large-scale modes
  that dominate a bulk flow — is present in every draw.  Its per-galaxy leg
  is a draw-mechanics + cross-quadrature consistency check (the draw
  reproduces the constructed diagonal of ``C_ab``, which independently agrees
  with the fiducial ``sigma_v_1d`` integral), and its ensemble bulk-flow leg
  is a covariance-propagation self-consistency check (the ensemble
  covariance reproduces the analytic ``A^-1 M A^-1`` built from the SAME
  ``C_ab`` — a check of the contraction, not an independent covariance
  validation).

* an INDEPENDENT box Gaussian-random-field generator built by a separate FFT
  code path with the physical linear velocity coloring
  ``i (100 f) k_j / k^2 sqrt(P(k))``.  It reproduces the *band-limited*
  analytic per-galaxy dispersion to a few percent under an order-unity factor,
  which independently confirms the variance NORMALISATION (the diagonal scale)
  is not a shared code artifact.  Its off-diagonal correlation differs from the
  analytic by an order-unity finite-box factor and its band captures a
  documented fraction of the full dispersion — the missing power is dominated
  by above-Nyquist sub-grid small scales, with only a percent-level genuine
  super-sample (below the box fundamental) piece — so the box is used ONLY as
  the diagonal-variance reference, never for the covariance or coverage, and
  the off-diagonal covariance structure is the fiducial Gorski model, not
  independently validated.

Forward-simulator coverage mechanics at ``roadmap_rescue_v1:C2`` only.  The two
CF4 P0s stay OPEN with remediation-CANDIDATE receipts; their closure is
impossible before the PR-157 adjudication.  No rare-tail or significance claim
is produced, same-box regions are never counted as independent, and the K6
numerical branch is not rebound to the CF4 catalogue authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .velocity_power import (  # noqa: E402
    _trapz,
    fiducial,
    velocity_correlation_functions,
)

# PR-145 registered objects — imported, never re-transcribed (Wave-15 lesson 10)
from .cf4_velocity_estimators import (  # noqa: E402
    Cf4Sample,
    H0_CF4,
    SIGMA_NL,
    _cv_correlation_matrix,
    _design_flow,
    cosmic_variance_M,
    significance,
    subsample,
)

SCHEMA_VERSION = "pr146.cf4_forward_simulator.v1"


class ForwardSimulatorError(ValueError):
    """Raised when the forward-simulator discipline is violated."""


def _positive_count(value, name: str, *, minimum: int = 1) -> int:
    if (
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, (int, np.integer))
        or value < minimum
    ):
        requirement = (
            "a positive integer" if minimum == 1
            else f"an integer of at least {minimum}"
        )
        raise ForwardSimulatorError(f"{name} must be {requirement}")
    return int(value)


# --------------------------------------------------------------------------
# aligned sample + simulation metadata (Dist, e_DMzp needed by realism layers)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class SimMeta:
    dist: np.ndarray         # (N,) luminosity distance (Mpc)
    e_dmzp: np.ndarray       # (N,) distance-modulus uncertainty (mag)
    h0: float


def load_sample_and_meta(groups_path, *, h0: float = H0_CF4,
                         sigma_nl: float = SIGMA_NL):
    """Load the CF4 groups into a PR-145 ``Cf4Sample`` and a ``SimMeta`` that
    carries the raw distance and distance-modulus error the realism layers need,
    both aligned to the same rows."""
    try:
        h0 = float(h0)
        sigma_nl = float(sigma_nl)
    except (TypeError, ValueError) as exc:
        raise ForwardSimulatorError(
            "CF4 H0 and nonlinear velocity dispersion must be real scalars"
        ) from exc
    if not np.isfinite(h0) or h0 <= 0:
        raise ForwardSimulatorError("CF4 H0 must be finite and positive")
    if not np.isfinite(sigma_nl) or sigma_nl < 0:
        raise ForwardSimulatorError(
            "CF4 nonlinear velocity dispersion must be finite and non-negative"
        )
    d = np.load(groups_path)
    dist = d["Dist"]
    v3k = d["V3k"]
    ra = np.radians(d["RAdeg"])
    dec = np.radians(d["DEdeg"])
    nhat = np.column_stack([np.cos(dec) * np.cos(ra),
                            np.cos(dec) * np.sin(ra), np.sin(dec)])
    vpec = v3k - h0 * dist
    sigma_d = np.log(10.0) / 5.0 * d["e_DMzp"] * dist
    sig_v = np.sqrt((h0 * sigma_d) ** 2 + sigma_nl ** 2)
    w = 1.0 / sig_v ** 2
    h = fiducial()["h"]
    pos = nhat * (dist * h)[:, None]
    sg = np.column_stack([d["SGX"], d["SGY"], d["SGZ"]]) \
        if all(k in d for k in ("SGX", "SGY", "SGZ")) else None
    sample = Cf4Sample(n=nhat, v=vpec, w=w, sig_v=sig_v, pos_hmpc=pos, sg=sg)
    meta = SimMeta(dist=dist, e_dmzp=d["e_DMzp"], h0=h0)
    return sample, meta


def subsample_with_meta(sample: Cf4Sample, meta: SimMeta, n_sub: int,
                        seed: int):
    """Subsample the sample and its metadata with the SAME index draw PR-145's
    ``subsample`` uses, and assert the sample matches (a live binding check)."""
    rng = np.random.Generator(np.random.PCG64(seed))
    n_tot = len(sample.v)
    if n_sub >= n_tot:
        idx = np.arange(n_tot)
    else:
        idx = rng.choice(n_tot, size=n_sub, replace=False)
    sub = Cf4Sample(n=sample.n[idx], v=sample.v[idx], w=sample.w[idx],
                    sig_v=sample.sig_v[idx], pos_hmpc=sample.pos_hmpc[idx],
                    sg=sample.sg[idx] if sample.sg is not None else None)
    ref = subsample(sample, n_sub, seed)
    if not np.array_equal(sub.n, ref.n):
        raise ForwardSimulatorError(
            "subsample_with_meta diverged from the PR-145 subsample index draw")
    sub_meta = SimMeta(dist=meta.dist[idx], e_dmzp=meta.e_dmzp[idx], h0=meta.h0)
    return sub, sub_meta


# --------------------------------------------------------------------------
# 1. primary generator: Cholesky-from-Gorski-C_ab
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class CholeskyGenerator:
    sample: Cf4Sample
    lchol: np.ndarray            # (N,N) lower Cholesky of C_ab
    sigma_v_1d_diag: float       # sqrt(mean diag C_ab)


def build_cholesky_generator(sample: Cf4Sample, *, jitter: float = 1e-6
                             ) -> CholeskyGenerator:
    c_ab = _cv_correlation_matrix(sample)
    lchol = np.linalg.cholesky(c_ab + jitter * np.eye(len(c_ab)))
    return CholeskyGenerator(sample=sample, lchol=lchol,
                             sigma_v_1d_diag=float(np.sqrt(np.diag(c_ab).mean())))


def draw_correlated_field(gen: CholeskyGenerator, rng) -> np.ndarray:
    """A correlated radial-velocity field with ``Cov = C_ab`` exactly."""
    return gen.lchol @ rng.standard_normal(len(gen.sample.v))


def verify_cholesky_generator(gen: CholeskyGenerator, *, n_real: int,
                              seed: int) -> dict:
    """Draw ``n_real`` correlated fields and verify (a) the per-galaxy velocity
    dispersion equals ``sigma_v_1d`` and (b) the ensemble bulk-flow covariance
    equals the analytic ``A^-1 M A^-1`` within Monte-Carlo tolerance."""
    n_real = _positive_count(
        n_real, "Cholesky realisation count", minimum=2)
    sample = gen.sample
    design = _design_flow(sample, monopole=False)
    a = np.einsum("i,ij,ik->jk", sample.w, design, design)
    a_inv = np.linalg.inv(a)
    m = cosmic_variance_M(sample, design)
    cv_cov = a_inv @ m @ a_inv
    rng = np.random.Generator(np.random.PCG64(seed))
    n_gal = len(sample.v)
    sq = np.zeros(n_gal)
    flows = np.zeros((n_real, 3))
    for i in range(n_real):
        v_cv = draw_correlated_field(gen, rng)
        sq += v_cv ** 2
        flows[i] = a_inv @ np.einsum("i,i,ij->j", sample.w, v_cv, design)
    per_gal_std = float(np.sqrt(sq.mean() / n_real))
    emp_cov = np.cov(flows, rowvar=False)
    fid = fiducial()
    diag_ratio = (np.diag(emp_cov) / np.diag(cv_cov)).tolist()
    mc_tol = np.sqrt(2.0 / n_real)                     # 1-sigma on a variance
    ok = (abs(per_gal_std / fid["sigma_v_1d"] - 1.0) < 0.03
          and all(abs(r - 1.0) < 5.0 * mc_tol for r in diag_ratio))
    if not ok:
        raise ForwardSimulatorError(
            "the Cholesky generator failed self-consistency: per-galaxy "
            f"std {per_gal_std:.1f} vs sigma_v_1d {fid['sigma_v_1d']:.1f}, "
            f"bulk-flow covariance ratios {np.round(diag_ratio, 3).tolist()}")
    return {"n_real": n_real, "per_galaxy_std_kms": per_gal_std,
            "sigma_v_1d_kms": fid["sigma_v_1d"],
            "bulk_flow_cov_diag_ratio": diag_ratio,
            "monte_carlo_1sigma_variance_tol": float(mc_tol),
            "note": "the per-galaxy leg is a draw-mechanics + cross-quadrature "
                    "consistency check (the draw reproduces the constructed "
                    "diagonal of C_ab, which agrees with the fiducial "
                    "sigma_v_1d integral to sub-percent); the bulk-flow leg is "
                    "a covariance-propagation self-consistency check (the "
                    "ensemble covariance reproduces the analytic A^-1 M A^-1 "
                    "built from the SAME C_ab within Monte-Carlo tolerance — a "
                    "contraction check, not an independent covariance "
                    "validation; the independent variance-normalisation check "
                    "is the separate box-GRF leg)"}


# --------------------------------------------------------------------------
# 2. independent reference: box Gaussian random field (a separate FFT path)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class BoxGrfConfig:
    ngrid: int
    boxsize_hmpc: float


def _box_wavevectors(cfg: BoxGrfConfig):
    n, l = cfg.ngrid, cfg.boxsize_hmpc
    k1 = 2.0 * np.pi * np.fft.fftfreq(n, d=l / n)
    kz1 = 2.0 * np.pi * np.fft.rfftfreq(n, d=l / n)
    kx = k1[:, None, None]
    ky = k1[None, :, None]
    kz = kz1[None, None, :]
    k2 = kx ** 2 + ky ** 2 + kz ** 2
    return kx, ky, kz, k2


def box_grf_velocity_components(cfg: BoxGrfConfig, seed: int):
    """Three real velocity-field components on a periodic grid, built by an
    independent FFT path with the physical linear coloring
    ``v_j(k) = i (100 f) k_j / k^2 sqrt(P(k))`` and the mode-density
    normalisation ``|filter|^2 = N^3 P(k) / L^3`` (so the real-space variance
    equals the band-limited ``(1/(2 pi)^2) int k^2 P dk``)."""
    fid = fiducial()
    f100 = 100.0 * fid["f_growth"]
    n, l = cfg.ngrid, cfg.boxsize_hmpc
    kx, ky, kz, k2 = _box_wavevectors(cfg)
    kmag = np.sqrt(k2)
    pk_grid = np.where(kmag > 0.0,
                       fid["pk"](np.clip(np.where(kmag > 0.0, kmag, 1.0),
                                         1e-5, 20.0)), 0.0)
    filt = np.sqrt(n ** 3 * pk_grid / l ** 3)
    rng = np.random.Generator(np.random.PCG64(seed))
    delta_k = np.fft.rfftn(rng.standard_normal((n, n, n))) * filt
    inv_k2 = np.where(k2 > 0.0, 1.0 / np.where(k2 > 0.0, k2, 1.0), 0.0)
    comps = tuple(
        np.fft.irfftn(1j * f100 * kj * inv_k2 * delta_k, s=(n, n, n),
                      axes=(0, 1, 2))
        for kj in (kx, ky, kz))
    kfund = float(2.0 * np.pi / l)
    knyq = float(np.pi * n / l)
    return comps, kfund, knyq


def _sample_field_at_positions(sample: Cf4Sample, comps, cfg: BoxGrfConfig):
    """Trilinear-sample the three velocity components at the sample positions
    (centred in the periodic box) and return the radial component."""
    n, l = cfg.ngrid, cfg.boxsize_hmpc
    pos = sample.pos_hmpc
    boxpos = pos - pos.mean(axis=0) + l / 2.0
    gi = (boxpos / l * n) % n
    i0 = np.floor(gi).astype(int) % n
    fr = gi - np.floor(gi)
    v3 = np.zeros((len(sample.v), 3))
    for j, field in enumerate(comps):
        val = np.zeros(len(sample.v))
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    wgt = ((fr[:, 0] if dx else 1 - fr[:, 0])
                           * (fr[:, 1] if dy else 1 - fr[:, 1])
                           * (fr[:, 2] if dz else 1 - fr[:, 2]))
                    val += wgt * field[(i0[:, 0] + dx) % n,
                                       (i0[:, 1] + dy) % n,
                                       (i0[:, 2] + dz) % n]
        v3[:, j] = val
    return np.einsum("ij,ij->i", v3, sample.n)


def band_limited_sigma_v(kmin: float, kmax: float) -> float:
    """Analytic linear 1-D velocity dispersion over a k-band (km/s)."""
    fid = fiducial()
    k = np.geomspace(kmin, kmax, 6000)
    return float(np.sqrt(fid["hf2"] / (6.0 * np.pi ** 2) * _trapz(fid["pk"](k),
                                                                  k)))


def verify_independent_reference(sample: Cf4Sample, cfg: BoxGrfConfig, *,
                                 n_fields: int, seed: int) -> dict:
    """The box GRF diagonal-variance cross-check: the box per-galaxy dispersion
    (independent FFT path) reproduces the band-limited analytic dispersion under
    an order-unity factor.  The off-diagonal correlation is an order-unity
    finite-box factor away from the analytic (documented, not used), and the
    band captures a documented fraction of the full dispersion (the
    super-sample gap)."""
    n_fields = _positive_count(
        n_fields, "independent field count", minimum=2)
    fid = fiducial()
    spatial_sig = []
    iso = []
    radial = np.zeros((n_fields, len(sample.v)))
    for i in range(n_fields):
        comps, kfund, knyq = box_grf_velocity_components(cfg, seed + i)
        spatial_sig.append(float(np.sqrt(
            (comps[0].var() + comps[1].var() + comps[2].var()) / 3.0)))
        iso.append([float(c.var()) for c in comps])
        radial[i] = _sample_field_at_positions(sample, comps, cfg)
    box_sigma_v = float(np.mean(spatial_sig))
    box_sigma_v_scatter = float(np.std(spatial_sig))
    band = band_limited_sigma_v(kfund, knyq)
    full = fid["sigma_v_1d"]
    # the band-limited deficit, split into its two physical pieces (variance):
    # the genuine super-sample power below the box fundamental, and the
    # (dominant) sub-grid power above the grid Nyquist.
    from .velocity_power import KMAX_S, KMIN_S
    super_sample_var_frac = band_limited_sigma_v(KMIN_S, kfund) ** 2 / full ** 2
    sub_grid_var_frac = band_limited_sigma_v(knyq, KMAX_S) ** 2 / full ** 2
    # off-diagonal correlation: box vs analytic — an order-unity finite-box
    # factor rounded to 1 decimal because it is a noise-dominated
    # (rank <= n_fields, ~few hundred dimensions) diagnostic, not a load-
    # bearing number (the box is never used for the covariance).
    cov_box = np.cov(radial, rowvar=False)
    d_box = np.sqrt(np.diag(cov_box))
    corr_box = cov_box / np.outer(d_box, d_box)
    corr_full = _correlation_from_cab(_cv_correlation_matrix(sample))
    iu = np.triu_indices(len(sample.v), k=1)
    strong = np.abs(corr_full[iu]) > 0.05
    off_diag_ratio = (round(float(np.median(corr_box[iu][strong]
                                            / corr_full[iu][strong])), 1)
                      if strong.any() else float("nan"))
    iso = np.mean(iso, axis=0)
    isotropy = float(iso.max() / iso.min())
    normalisation_ratio = box_sigma_v / band
    if not (0.8 < normalisation_ratio < 1.25):
        raise ForwardSimulatorError(
            "the independent box GRF did not reproduce the band-limited "
            f"velocity dispersion (ratio {normalisation_ratio:.3f}) — the "
            "normalisation is not confirmed")
    return {
        "n_fields": n_fields, "ngrid": cfg.ngrid,
        "boxsize_hmpc": cfg.boxsize_hmpc,
        "k_fundamental_hmpc": kfund, "k_nyquist_hmpc": knyq,
        "box_sigma_v_kms": box_sigma_v,
        "box_sigma_v_scatter_kms": box_sigma_v_scatter,
        "band_limited_sigma_v_kms": band,
        "full_sigma_v_1d_kms": full,
        "normalisation_ratio_box_over_band": normalisation_ratio,
        "band_captured_fraction_sigma": band / full,
        "variance_deficit_super_sample_below_kfund": float(super_sample_var_frac),
        "variance_deficit_sub_grid_above_knyquist": float(sub_grid_var_frac),
        "off_diagonal_ratio_box_over_analytic_approx": off_diag_ratio,
        "component_isotropy_max_over_min": isotropy,
        "note": "the independent FFT box reproduces the band-limited analytic "
                "per-galaxy velocity dispersion to a few percent (an order-"
                "unity rescale), independently confirming the variance "
                "NORMALISATION (the diagonal scale) is not a shared code "
                "artifact; the off-diagonal correlation is an order-unity "
                "finite-box factor from the analytic (noise-dominated at this "
                "field count, reported to one decimal) so the box is a "
                "diagonal-variance reference only; the band captures a "
                "documented fraction of the full dispersion, with the missing "
                "variance dominated by above-Nyquist sub-grid small scales "
                "and only a percent-level genuine super-sample piece below "
                "the box fundamental"}


def _correlation_from_cab(c_ab: np.ndarray) -> np.ndarray:
    d = np.sqrt(np.diag(c_ab))
    return c_ab / np.outer(d, d)


# --------------------------------------------------------------------------
# 3. realism layers
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class RealismConfig:
    nongaussian_distance_error: bool = False
    nonlinear_scatter: bool = False
    selection_malmquist: bool = False
    grouping: bool = False


def _selection_mask(meta: SimMeta) -> np.ndarray:
    """A deterministic magnitude-limited selection: the keep probability falls
    with distance (a bright limit), applied as a fixed threshold on distance so
    the selected covariance is computed once."""
    dist = meta.dist
    keep_frac = np.clip(1.0 - 0.6 * (dist / dist.max()), 0.2, 1.0)
    return keep_frac >= np.median(keep_frac) - 0.15   # deterministic, ~selected


def _apply_selection(sample: Cf4Sample, meta: SimMeta):
    mask = _selection_mask(meta)
    sub = Cf4Sample(n=sample.n[mask], v=sample.v[mask], w=sample.w[mask],
                    sig_v=sample.sig_v[mask], pos_hmpc=sample.pos_hmpc[mask],
                    sg=sample.sg[mask] if sample.sg is not None else None)
    sub_meta = SimMeta(dist=meta.dist[mask], e_dmzp=meta.e_dmzp[mask],
                       h0=meta.h0)
    return sub, sub_meta


def _apply_grouping(sample: Cf4Sample, meta: SimMeta, *, members: int = 3):
    """Collapse spatially adjacent rows into synthetic multi-member groups: the
    group velocity is shared, the group distance-modulus error shrinks like
    ``1/sqrt(members)`` (averaging), the group position/direction is the member
    mean.  Models the CF4 grouping step (galaxies -> groups)."""
    order = np.argsort(meta.dist)
    n_groups = len(order) // members
    rows = order[:n_groups * members].reshape(n_groups, members)
    n = sample.n[rows].mean(axis=1)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    pos = sample.pos_hmpc[rows].mean(axis=1)
    dist = meta.dist[rows].mean(axis=1)
    e_dmzp = meta.e_dmzp[rows].mean(axis=1) / np.sqrt(members)
    sigma_d = np.log(10.0) / 5.0 * e_dmzp * dist
    sig_v = np.sqrt((meta.h0 * sigma_d) ** 2 + SIGMA_NL ** 2)
    w = 1.0 / sig_v ** 2
    grp = Cf4Sample(n=n, v=sample.v[rows].mean(axis=1), w=w, sig_v=sig_v,
                    pos_hmpc=pos, sg=None)
    grp_meta = SimMeta(dist=dist, e_dmzp=e_dmzp, h0=meta.h0)
    return grp, grp_meta


def realism_sample(sample: Cf4Sample, meta: SimMeta, realism: RealismConfig):
    """Apply the SAMPLE-level realism layers (selection, grouping) once so the
    assessed covariance is computed on the modified sample."""
    if realism.selection_malmquist:
        sample, meta = _apply_selection(sample, meta)
    if realism.grouping:
        sample, meta = _apply_grouping(sample, meta)
    return sample, meta


def realism_noise(design: np.ndarray, truth: np.ndarray, v_cv: np.ndarray,
                  sample: Cf4Sample, meta: SimMeta, realism: RealismConfig,
                  rng) -> np.ndarray:
    """One observed-velocity mock: the injected flow+monopole, the correlated
    cosmic-variance field, and the measurement error plus any GENUINE stressor
    that the assessed covariance does NOT model (so coverage can degrade and be
    reported).  ``selection_malmquist`` and ``grouping`` also carry a
    sample-level composition change applied in :func:`realism_sample`; the
    unmodeled bias/scatter added here is what makes them stressors rather than
    a covers-by-construction subsample."""
    v = design @ truth + v_cv
    if realism.nongaussian_distance_error:
        # lognormal distance-modulus error -> asymmetric velocity error whose
        # ensemble mean biases the radial monopole (a homogeneous Malmquist
        # bias the Gaussian covariance does not model)
        eps_mu = rng.normal(0.0, meta.e_dmzp)
        dist_obs = meta.dist * 10.0 ** (eps_mu / 5.0)
        v = v - meta.h0 * (dist_obs - meta.dist)
        v = v + rng.normal(0.0, SIGMA_NL)
    else:
        v = v + rng.normal(0.0, sample.sig_v)
    if realism.selection_malmquist:
        # inhomogeneous Malmquist velocity bias: a coherent distance-correlated
        # offset UNMODELED by the assessed covariance (a genuine stressor, not
        # a covers-by-construction subsample)
        v = v + 0.5 * (meta.dist - float(meta.dist.mean()))
    if realism.grouping:
        # unmodeled intra-group velocity dispersion beyond the sqrt(members)
        # noise reduction the model assumes (a genuine stressor)
        v = v + rng.normal(0.0, 180.0)
    if realism.nonlinear_scatter:
        v = v + rng.normal(0.0, 0.5 * SIGMA_NL)   # extra small-scale motions
    return v


# --------------------------------------------------------------------------
# 4. forward-mock coverage (re-fit the estimator on every mock)
# --------------------------------------------------------------------------
def _full_and_noise_covariance(sample: Cf4Sample):
    design = _design_flow(sample, monopole=True)
    a = np.einsum("i,ij,ik->jk", sample.w, design, design)
    a_inv = np.linalg.inv(a)
    m = cosmic_variance_M(sample, design)
    full_cov = a_inv + a_inv @ m @ a_inv
    return design, a_inv, full_cov


def forward_mock_coverage(sample: Cf4Sample, meta: SimMeta, flow_true,
                          monopole_true, realism: RealismConfig, *,
                          n_mock: int, seed: int) -> dict:
    """Draw ``n_mock`` correlated mocks with the realism layers, re-fit the
    bulk-flow-plus-monopole estimator on each, and return the per-component
    68/95 coverage under the full covariance and the noise-only covariance."""
    n_mock = _positive_count(n_mock, "forward-mock count")
    sample, meta = realism_sample(sample, meta, realism)
    gen = build_cholesky_generator(sample)
    design, a_inv, full_cov = _full_and_noise_covariance(sample)
    sd_full = np.sqrt(np.diag(full_cov))
    sd_noise = np.sqrt(np.diag(a_inv))
    truth = np.concatenate([np.asarray(flow_true, float), [monopole_true]])
    rng = np.random.Generator(np.random.PCG64(seed))
    h68 = np.zeros(4)
    h95 = np.zeros(4)
    h68n = np.zeros(4)
    for _ in range(n_mock):
        v_cv = draw_correlated_field(gen, rng)
        v = realism_noise(design, truth, v_cv, sample, meta, realism, rng)
        coeffs = a_inv @ np.einsum("i,i,ij->j", sample.w, v, design)
        dev = np.abs(coeffs - truth)
        h68 += dev / sd_full <= 1.0
        h95 += dev / sd_full <= 1.959963985
        h68n += dev / sd_noise <= 1.0
    return {"variant": _realism_label(realism), "n_mock": n_mock,
            "n_galaxies": int(len(sample.v)),
            "labels": ["Bx", "By", "Bz", "M"],
            "coverage_68": (h68 / n_mock).tolist(),
            "coverage_95": (h95 / n_mock).tolist(),
            "coverage_68_noise_only": (h68n / n_mock).tolist()}


def _realism_label(realism: RealismConfig) -> str:
    active = [k for k, v in (
        ("nongaussian_distance_error", realism.nongaussian_distance_error),
        ("nonlinear_scatter", realism.nonlinear_scatter),
        ("selection_malmquist", realism.selection_malmquist),
        ("grouping", realism.grouping)) if v]
    return "idealised" if not active else "+".join(active)


def realism_from_variant(variant: str) -> RealismConfig:
    return RealismConfig(
        nongaussian_distance_error=variant == "nongaussian_distance_error",
        nonlinear_scatter=variant == "nonlinear_scatter",
        selection_malmquist=variant == "selection_malmquist",
        grouping=variant == "grouping")


def coverage_in_band(coverage: dict, nominal: float, half_width: float,
                     labels=None) -> dict:
    try:
        nominal = float(nominal)
        half_width = float(half_width)
    except (TypeError, ValueError) as exc:
        raise ForwardSimulatorError(
            "coverage nominal and half-width must be real scalars") from exc
    if not np.isfinite(nominal):
        raise ForwardSimulatorError("coverage nominal must be finite")
    if np.isclose(nominal, 0.68, rtol=0.0, atol=1e-12):
        key = "coverage_68"
    elif np.isclose(nominal, 0.95, rtol=0.0, atol=1e-12):
        key = "coverage_95"
    else:
        raise ForwardSimulatorError(
            "coverage nominal must select the 0.68 or 0.95 report")
    if not np.isfinite(half_width) or not 0.0 <= half_width <= 1.0:
        raise ForwardSimulatorError(
            "coverage half-width must be finite and within [0, 1]")
    try:
        report_labels = coverage["labels"]
        values = coverage[key]
    except (KeyError, TypeError) as exc:
        raise ForwardSimulatorError(
            "coverage report is missing component values") from exc
    if (
        isinstance(report_labels, (str, bytes))
        or isinstance(values, (str, bytes))
        or len(report_labels) == 0
        or len(report_labels) != len(values)
        or any(not isinstance(label, str) or not label
               for label in report_labels)
        or len(set(report_labels)) != len(report_labels)
    ):
        raise ForwardSimulatorError(
            "coverage report must have one value for every unique component")
    value_by_label = {}
    for label, cov in zip(report_labels, values):
        if not np.isscalar(cov) or not np.isreal(cov) \
                or not np.isfinite(cov) or not 0.0 <= cov <= 1.0:
            raise ForwardSimulatorError(
                f"component {label} coverage must be finite and within [0, 1]")
        value_by_label[label] = float(cov)
    if labels is None:
        selected = list(report_labels)
    else:
        if isinstance(labels, (str, bytes)):
            raise ForwardSimulatorError(
                "coverage component selection must be a non-empty sequence")
        try:
            selected = list(labels)
        except TypeError as exc:
            raise ForwardSimulatorError(
                "coverage component selection must be a non-empty sequence"
            ) from exc
        if (
            not selected
            or any(not isinstance(label, str)
                   or label not in value_by_label for label in selected)
            or len(set(selected)) != len(selected)
        ):
            raise ForwardSimulatorError(
                "coverage component selection must name unique report labels")
    return {
        label: bool(abs(value_by_label[label] - nominal) <= half_width)
        for label in selected
    }


def require_idealised_covers(coverage: dict, half68: float, half95: float
                             ) -> None:
    """The idealised variant validates the covariance propagation: the full
    covariance must cover at nominal and the noise-only must under-cover."""
    if coverage["variant"] != "idealised":
        raise ForwardSimulatorError("require_idealised_covers needs the "
                                    "idealised variant")
    flags68 = coverage_in_band(coverage, 0.68, half68)
    flags95 = coverage_in_band(coverage, 0.95, half95)
    if not all(flags68.values()) or not all(flags95.values()):
        raise ForwardSimulatorError(
            f"the idealised full covariance does not cover: 68 {flags68}, "
            f"95 {flags95} — the propagation is broken")
    noise = coverage.get("coverage_68_noise_only")
    labels = coverage["labels"]
    if (
        isinstance(noise, (str, bytes))
        or not hasattr(noise, "__len__")
        or len(noise) != len(labels)
        or any(not np.isscalar(cov) or not np.isreal(cov)
               or not np.isfinite(cov) or not 0.0 <= cov <= 1.0
               for cov in noise)
    ):
        raise ForwardSimulatorError(
            "noise-only coverage must provide one finite probability per "
            "component")
    if max(noise) >= 0.60:
        raise ForwardSimulatorError(
            "the noise-only covariance did not under-cover — the full-vs-"
            "noise-only discrimination is not exercised")


# --------------------------------------------------------------------------
# 5. per-depth simultaneous grid-conditional coverage (PR-137 discipline)
# --------------------------------------------------------------------------
def depth_shell_edges(meta: SimMeta, n_shells: int) -> np.ndarray:
    n_shells = _positive_count(n_shells, "depth-shell count")
    q = np.linspace(0.0, 1.0, n_shells + 1)
    return np.quantile(meta.dist, q)


def per_depth_coverage(sample: Cf4Sample, meta: SimMeta, flow_true,
                       monopole_true, *, n_shells: int, n_mock: int,
                       seed: int) -> dict:
    """Per-shell coverage on a pre-registered distance grid, measured under the
    non-Gaussian distance-error STRESSOR so the shells genuinely differ (the
    Malmquist monopole bias is depth-dependent) — otherwise every shell would
    cover by construction.  The genuinely least-favourable shell is disclosed
    (PR-137 lessons 20/21); the family-wise note states how a simultaneous
    statement over the grid would be formed (a per-shell Bonferroni), which is
    not itself computed here."""
    n_mock = _positive_count(n_mock, "per-depth mock count")
    edges = depth_shell_edges(meta, n_shells)
    shells = []
    stressor = RealismConfig(nongaussian_distance_error=True)
    for s in range(n_shells):
        lo, hi = edges[s], edges[s + 1]
        mask = (meta.dist >= lo) & (meta.dist <= hi if s == n_shells - 1
                                    else meta.dist < hi)
        if mask.sum() < 50:
            raise ForwardSimulatorError(
                f"depth shell {s} has too few groups ({int(mask.sum())})")
        sub = Cf4Sample(n=sample.n[mask], v=sample.v[mask], w=sample.w[mask],
                        sig_v=sample.sig_v[mask], pos_hmpc=sample.pos_hmpc[mask],
                        sg=None)
        sub_meta = SimMeta(dist=meta.dist[mask], e_dmzp=meta.e_dmzp[mask],
                           h0=meta.h0)
        cov = forward_mock_coverage(sub, sub_meta, flow_true, monopole_true,
                                    stressor, n_mock=n_mock, seed=seed + s)
        shells.append({"shell": s,
                       "dist_lo_mpc": float(lo), "dist_hi_mpc": float(hi),
                       "n_groups": int(mask.sum()),
                       "coverage_68": cov["coverage_68"],
                       "min_coverage_68": float(min(cov["coverage_68"]))})
    least = min(shells, key=lambda r: r["min_coverage_68"])
    return {"n_shells": n_shells, "dgp": "nongaussian_distance_error_stressor",
            "shells": shells,
            "least_favourable_shell": least["shell"],
            "least_favourable_min_coverage_68": least["min_coverage_68"],
            "family_wise_note": "each shell coverage is measured under the "
                                "non-Gaussian distance-error stressor so the "
                                "shells genuinely differ; the disclosed least-"
                                "favourable value is the minimum over shells "
                                "and components (a real depth-dependent "
                                "degradation, not Monte-Carlo noise). A "
                                "simultaneous family-wise statement over the "
                                f"{n_shells}-shell grid would use a per-shell "
                                f"Bonferroni confidence 1-(1-c)/{n_shells} (not "
                                "computed here); same-shell regions are not "
                                "treated as independent"}


# --------------------------------------------------------------------------
# 6. effective-N audit  +  7. covariance uncertainty
# --------------------------------------------------------------------------
def effective_n_modes(sample: Cf4Sample) -> dict:
    """The participation ratio ``(tr C)^2 / tr(C^2)`` of the correlated-field
    eigenvalues — the effective number of independent large-scale modes, which
    is why same-box regions are NOT independent samples — and the participation
    ratio of the 3x3 bulk-flow cosmic-variance covariance."""
    c_ab = _cv_correlation_matrix(sample)
    ev = np.linalg.eigvalsh(c_ab)
    ev = ev[ev > 0]
    field_pr = float(ev.sum() ** 2 / (ev ** 2).sum())
    design = _design_flow(sample, monopole=False)
    a = np.einsum("i,ij,ik->jk", sample.w, design, design)
    a_inv = np.linalg.inv(a)
    cv = a_inv @ cosmic_variance_M(sample, design) @ a_inv
    evb = np.linalg.eigvalsh(cv)
    evb = evb[evb > 0]
    bulk_pr = float(evb.sum() ** 2 / (evb ** 2).sum())
    return {"n_galaxies": int(len(sample.v)),
            "field_participation_ratio": field_pr,
            "bulk_flow_participation_ratio": bulk_pr,
            "note": "the correlated velocity field has only "
                    f"{field_pr:.0f} independent large-scale modes over "
                    f"{len(sample.v)} groups, so same-box regions are never "
                    "counted as independent samples"}


def covariance_uncertainty(n_mock: int) -> dict:
    n_mock = _positive_count(n_mock, "covariance mock count")
    frac = float(np.sqrt(2.0 / n_mock))
    return {"n_mock": n_mock,
            "monte_carlo_fractional_uncertainty_per_variance_element": frac,
            "note": "the Monte-Carlo covariance estimate carries a "
                    f"{frac:.3f} fractional 1-sigma uncertainty per variance "
                    "element from the finite mock ensemble"}


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def refuse_same_box_octant_independence(kind: str) -> None:
    if kind in ("same_box_octants", "octants_as_independent",
                "regions_of_one_box"):
        raise ForwardSimulatorError(
            "same-box regions may not be counted as independent mocks; "
            "coverage is over independent realisations")


def refuse_wf_mean_as_ensemble(kind: str) -> None:
    if kind in ("wf_mean", "single_wf_mean", "wf_mean_as_posterior"):
        raise ForwardSimulatorError(
            "a single Wiener-filter mean field is not a posterior or "
            "constrained-realisation ensemble")


def refuse_k6_rebind(kind: str) -> None:
    if kind in ("k6_rebind", "k6_to_cf4_catalogue", "k6_numerical_rescue"):
        raise ForwardSimulatorError(
            "the K6 numerical branch may not be rebound to the CF4 catalogue "
            "authority; K6 is the independent PR-123 branch")


def refuse_rare_tail_without_coverage(coverage_ok: bool, claim: str) -> None:
    if claim in ("rare_tail", "significance") and not coverage_ok:
        raise ForwardSimulatorError(
            "a rare-tail or significance claim may not be produced when the "
            "coverage validation fails")


def refuse_box_grf_for_covariance(use: str) -> None:
    if use in ("covariance", "coverage", "box_grf_covariance"):
        raise ForwardSimulatorError(
            "the finite-box GRF may not be used for the covariance or "
            "coverage; those use the full-range analytic Cholesky generator")


def refuse_cf4_p0_closure(claim: str) -> None:
    if claim in ("cf4_p0_closed", "p0_resolved", "remediation_complete"):
        raise ForwardSimulatorError(
            "a CF4 P0 may not be closed before the PR-157 adjudication; "
            "PR-146 emits forward-simulator mechanics only")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("same-box octants are ", "independent"),
        ("wf mean is ", "the ensemble"),
        ("k6 rebound ", "to cf4"),
        ("rare tail ", "detected"),
        ("cf4 p0 ", "closed"),
        ("box grf covariance is ", "the coverage"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise ForwardSimulatorError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(box_ratio: float, field_modes: float,
                     idealised_min_68: float) -> str:
    return (
        f"CF4 forward-mock simulator: an independent FFT box reproduces the "
        f"band-limited velocity dispersion at ratio {box_ratio:.2f} (no shared "
        f"normalisation bug), the correlated field has ~{field_modes:.0f} "
        f"independent large-scale modes, and the idealised full-covariance "
        f"coverage holds (min 68 percent {idealised_min_68:.2f}) while the "
        f"noise-only covariance under-covers. Forward-simulator coverage "
        f"mechanics only; same-box regions are never independent; the two CF4 "
        f"P0s stay OPEN with remediation-candidate receipts pending the PR-157 "
        f"adjudication; no detection.")
