"""Physical forward mocks for peculiar-velocity bulk-flow significance (REV-R197).

The rev-r196 MV card reports the CF4 |B| vs LambdaCDM tension as a
covariance-treatment-dependent RANGE (4.4-5.4 sigma) and withholds a single
headline, because the analytic linear-window covariance underestimates the true
scatter (Whitford+2023, MNRAS 526 3051: MV bulk-flow uncertainties are
underestimated ~4-6x in variance -> tension overestimated; credible tension
~2-3 sigma). The registered unblock was "release-matched CF4 mocks"
(BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP -- the Qin+2021 CF4TF L-PICOLA mocks are
request-only, not public). This module replaces the missing release mock with an
in-house PHYSICAL forward model that calibrates OUR estimator's actual sampling
distribution under LambdaCDM at the observed CF4 geometry + noise:

    u_n^mock = n_hat_n . v_GRF(x_n)         linear Gaussian-random-field velocity
             + n_hat_n . b_super            super-box (>box) near-uniform bulk mode
             + eps_NL,n                     nonlinear small-scale dispersion sigma_NL
             + eps_obs,n                    the pipeline's own per-group sigma_v,n

- v_GRF: a linear peculiar-velocity field on an FFT grid, v_j(k) = i (100 f)
  (k_j/k^2) delta(k), delta(k) a Gaussian field with the shared EH98 sigma_8-
  normalised P(k) (`velocity_power.make_pk`). The velocity 1-point variance and
  the pairwise Psi are dominated by LARGE scales, so they are insensitive to the
  grid small-scale cutoff (int P dk converges) and are validated against the
  closed-form sigma_v_1d.
- b_super: the variance in modes LARGER than the box, hf2/(6 pi^2) int_0^kf P dk
  per component, drawn once per (box, observer) as a uniform 3-vector -- the
  super-sample large-scale flow the finite box omits. This is what gives the
  survey bulk flow its full LambdaCDM cosmic variance.
- sigma_NL: nonlinear velocity dispersion added in quadrature per object (250
  km/s fiducial; 150/350 sensitivity), the standard PV-likelihood nuisance
  (Johnson+2014, Howlett+2017).

Honesty: this is a GRF-linear + sigma_NL, POSITIONS-CONDITIONAL forward model
(the observed CF4 positions are fixed; no survey-selection regeneration). It is
MORE realistic than the analytic linear-window covariance (it adds sigma_NL,
real per-group measurement noise, and the exact survey geometry sampled by the
estimator) but it is NOT the full nonlinear COLA/L-PICOLA suite (registered
residual). Diagnostic-only kinematic descriptor; no Bianchi family, geometry, or
observer-frame claim.
"""
from __future__ import annotations

import numpy as np


def _trapz(y, x):
    return np.trapz(y, x) if hasattr(np, "trapz") else np.trapezoid(y, x)


def super_box_variance(pk, hf2, box_hmpc, *, nk=4000):
    """Per-component 1-D velocity variance (km/s)^2 in the super-box modes k<kf
    the finite box omits: hf2/(6 pi^2) int_0^kf P(k) dk, kf = 2 pi/box.

    These wavelengths exceed the box, so they appear as a near-uniform bulk flow
    across the survey -- the super-sample large-scale mode. Drawn per observer as
    a uniform 3-vector N(0, sigma^2 I)."""
    kf = 2.0 * np.pi / float(box_hmpc)
    k = np.geomspace(1.0e-5, kf, nk)
    return float(hf2 / (6.0 * np.pi ** 2) * _trapz(pk(k), k))


def linear_velocity_grid(pk, hf2, box_hmpc, ngrid, seed):
    """Linear peculiar-velocity field on a periodic FFT grid, shape (3,n,n,n),
    km/s (Cartesian components). v_j(k) = i sqrt(hf2) (k_j/k^2) delta(k), delta a
    Gaussian field with power P(k). The DC (mean) mode is zeroed (the >box bulk
    flow is supplied separately by `super_box_variance`)."""
    n = int(ngrid)
    box = float(box_hmpc)
    cell = box / n
    V = box ** 3
    N = n ** 3
    rng = np.random.default_rng(seed)

    kx = 2.0 * np.pi * np.fft.fftfreq(n, d=cell)          # (n,)
    kz = 2.0 * np.pi * np.fft.rfftfreq(n, d=cell)         # (n//2+1,)
    KX, KY, KZ = np.meshgrid(kx, kx, kz, indexing="ij")
    k2 = KX * KX + KY * KY + KZ * KZ
    k2[0, 0, 0] = 1.0                                     # avoid div0; zeroed below
    kmag = np.sqrt(k2)

    # delta coefficient in the numpy irfftn convention: <|B_k|^2> = P(k) N/Vcell
    # -> B_k = (N/sqrt(2 V)) sqrt(P) (g1 + i g2)
    amp = (N / np.sqrt(2.0 * V)) * np.sqrt(np.maximum(pk(kmag), 0.0))
    shape = KX.shape
    dk = amp * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))
    dk[0, 0, 0] = 0.0                                     # no box-mean density

    pref = np.sqrt(hf2)                                   # 100 f
    vel = np.empty((3, n, n, n), dtype=np.float64)
    for j, Kj in enumerate((KX, KY, KZ)):
        vk = 1j * pref * (Kj / k2) * dk
        vel[j] = np.fft.irfftn(vk, s=(n, n, n))
    return vel


def sample_at_positions(vel, box_hmpc, pos_hmpc, observer_hmpc=None):
    """Trilinear-interpolate the (3,n,n,n) periodic velocity grid at world
    positions observer + pos (Mpc/h), returning (N,3) km/s. Periodic wrap."""
    from scipy.ndimage import map_coordinates
    n = vel.shape[1]
    cell = float(box_hmpc) / n
    pos = np.asarray(pos_hmpc, float)
    if observer_hmpc is not None:
        pos = pos + np.asarray(observer_hmpc, float)[None, :]
    idx = (pos / cell).T                                  # (3, N) grid-index coords
    out = np.empty((pos.shape[0], 3), float)
    for j in range(3):
        out[:, j] = map_coordinates(vel[j], idx, order=1, mode="grid-wrap")
    return out


def mock_los_velocities(vel, box_hmpc, pos_hmpc, n_hat, sigma_v, *, pk, hf2,
                        observer_hmpc, sigma_nl, rng):
    """One mock line-of-sight velocity vector (N,) km/s at the CF4 geometry:

        u_n = n_hat_n . [v_GRF(observer + x_n) + b_super]
              + N(0, sigma_nl) + N(0, sigma_v,n).

    b_super ~ N(0, super_box_variance * I) is drawn per call (per observer), the
    near-uniform >box bulk mode. sigma_nl adds the nonlinear dispersion in
    quadrature; sigma_v are the pipeline's per-group measurement errors."""
    v = sample_at_positions(vel, box_hmpc, pos_hmpc, observer_hmpc)      # (N,3)
    sig_super = np.sqrt(super_box_variance(pk, hf2, box_hmpc))
    b_super = rng.normal(0.0, sig_super, 3)
    u = np.einsum("ni,ni->n", n_hat, v + b_super[None, :])
    nn = pos_hmpc.shape[0]
    u = u + rng.normal(0.0, sigma_nl, nn) + rng.normal(0.0, 1.0, nn) * sigma_v
    return u


def octant_observers(box_hmpc, sep_frac=0.25):
    """8 observers at the octant centers of the box (+/- sep_frac*box on each
    axis), >= sep_frac*box*2 apart -- quasi-independent survey placements."""
    d = sep_frac * float(box_hmpc)
    c = 0.5 * float(box_hmpc)
    return np.array([[c + sx * d, c + sy * d, c + sz * d]
                     for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)],
                    float)
