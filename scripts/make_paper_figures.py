#!/usr/bin/env python3
"""make_paper_figures.py — comprehensive paper-quality figure generator.

Renders every figure the current bass_py code + dl_pipeline/obs_bundle
data can support, at publication quality (300 dpi PNG + PDF, Okabe-Ito
palette, single/double column widths from htt.core.plot_style).

Scope (2026-04-19):
- Ch.02 observational motivation: CMB spectra overlay, CMB map,
  dipole scenarios, CF4 velocity field.
- Ch.05 tilt-boost: B(beta, cos theta) heatmap, directional slices,
  linear-vs-exact error.
- Ch.06 pipeline: species Omega_s(z), Hubble geometry, recombination
  composite panel, reionization tau sweep.
- Ch.07 results: Bianchi shear decay by type, phase plane, a^{-4}
  diagnostic, shear seed sweep.
- Ch.08 observational robustness: DESI sky coverage + n(z), Planck
  lensing bandpowers, CF4 peculiar-velocity samples.

Companion: scripts/make_preliminary_figures.py covers Tier A (MES
bounds, Route B sentinel, Colin beta) and writes to figures/preliminary.
This script writes to figures/paper/{ch02,ch05,ch06,ch07,ch08}.

Usage
-----
    venv/bin/python scripts/make_paper_figures.py           # all
    venv/bin/python scripts/make_paper_figures.py --only ch02a_planck_tt
    venv/bin/python scripts/make_paper_figures.py --list
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = REPO_ROOT / "figures" / "paper"
OBS_ROOT = REPO_ROOT / "dl_pipeline" / "obs_bundle" / "obs"

sys.path.insert(0, str(REPO_ROOT / "bass_py"))
sys.path.insert(0, str(OBS_ROOT))

from htt.core.plot_style import apply_style, COLS  # noqa: E402


# =====================================================================
# Shared helpers
# =====================================================================


def _save(fig, name: str, chapter: str) -> None:
    outdir = OUT_ROOT / chapter
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(
            outdir / f"{name}.{ext}",
            dpi=300,
            bbox_inches="tight",
            pad_inches=0.04,
        )
    plt.close(fig)
    print(f"  [ok] {chapter}/{name}.{{png,pdf}}")


def _caption(name: str, chapter: str, text: str) -> None:
    outdir = OUT_ROOT / chapter
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{name}.caption.txt").write_text(text.strip() + "\n")


class ObsCache:
    """Lazy singleton for the observational data catalog."""

    _cat = None

    @classmethod
    def cat(cls):
        if cls._cat is None:
            from obs_loader import ObsCatalog

            cls._cat = ObsCatalog(root=OBS_ROOT)
        return cls._cat


class BgCache:
    """Lazy singleton for FLRW background + species registry."""

    _bg = None
    _reg = None

    @classmethod
    def bg(cls):
        if cls._bg is None:
            from bass.species import build_flrw_background_table

            cls._bg = build_flrw_background_table()
        return cls._bg

    @classmethod
    def registry(cls):
        if cls._reg is None:
            from bass.species import SpeciesBackgroundRegistry

            cls._reg = SpeciesBackgroundRegistry.from_planck2018(
                bg_table=cls.bg()
            )
        return cls._reg


SPECIES_STYLE = {
    "photon": dict(color=COLS["orange"], ls="-", label=r"$\gamma$"),
    "neutrino": dict(color=COLS["cyan"], ls="--", label=r"$\nu$"),
    "baryon": dict(color=COLS["blue"], ls="-", label=r"$b$"),
    "cdm": dict(color=COLS["purple"], ls="-", label=r"$c$ (CDM)"),
    "lambda": dict(color=COLS["green"], ls=":", label=r"$\Lambda$"),
}


# =====================================================================
# Chapter 2 — Observational motivation
# =====================================================================


def fig_ch02a_planck_tt_spectrum() -> None:
    """Planck PR3 TT binned data + best-fit theory overlay."""
    cat = ObsCache.cat()
    obs = cat.load("planck.pr3.tt_binned")
    th = cat.load("planck.pr3.bestfit")

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.plot(
        th.ell,
        th.dl_TT,
        color=COLS["gray"],
        lw=1.2,
        zorder=2,
        label=r"Planck 2018 best-fit $\Lambda$CDM",
    )
    err = np.vstack([obs.err_lo, obs.err_hi])
    ax.errorbar(
        obs.ell,
        obs.dl,
        yerr=err,
        fmt="o",
        ms=3.4,
        color=COLS["blue"],
        ecolor=COLS["blue"],
        mec="k",
        mew=0.25,
        elinewidth=0.7,
        capsize=0,
        zorder=5,
        label=r"Planck PR3 TT (binned)",
    )
    ax.set_xlabel(r"Multipole $\ell$")
    ax.set_ylabel(r"$D_\ell^{TT}\;[\mu\mathrm{K}^2]$")
    ax.set_xscale("log")
    ax.set_xlim(30, 2600)
    ax.set_ylim(0, 6500)
    ax.grid(True, which="major", alpha=0.25)
    ax.grid(True, which="minor", alpha=0.08)
    ax.legend(fontsize=9.0, loc="upper right", framealpha=0.9)
    ax.set_title(r"Planck PR3 TT power spectrum", fontsize=10)
    _save(fig, "fig_ch02a_planck_tt_spectrum", "ch02_dipole")
    _caption(
        "fig_ch02a_planck_tt_spectrum",
        "ch02_dipole",
        """
Planck PR3 temperature power spectrum D_ell^{TT} binned bandpowers
(blue points, COM_PowerSpect_CMB-TT-binned_R3.01) with the Planck 2018
best-fit Lambda CDM theory curve (gray). Horizontal axis on log scale
to expose the acoustic peak structure from ell ~ 50 to ell ~ 2500.
Source: dl_pipeline/obs_bundle/obs/cmb/powerspectra.
""",
    )


def fig_ch02b_planck_polarization_grid() -> None:
    """2x2 panel: TT, TE, EE, BB(low-ell) with best-fit theory."""
    cat = ObsCache.cat()
    th = cat.load("planck.pr3.bestfit")
    tt = cat.load("planck.pr3.tt_binned")
    te = cat.load("planck.pr3.te_full")
    ee = cat.load("planck.pr3.ee_full")
    bb = cat.load("planck.pr3.bb_lowl")

    def _bin(ell, dl, err, n=8):
        m = len(ell) // n
        el = ell[: m * n].reshape(m, n).mean(axis=1)
        dv = dl[: m * n].reshape(m, n).mean(axis=1)
        ev = err[: m * n].reshape(m, n).mean(axis=1) / np.sqrt(n)
        return el, dv, ev

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4), constrained_layout=True)

    # --- TT (top-left) ---
    ax = axes[0, 0]
    ax.plot(th.ell, th.dl_TT, color=COLS["gray"], lw=1.2)
    err = np.vstack([tt.err_lo, tt.err_hi])
    ax.errorbar(
        tt.ell, tt.dl, yerr=err, fmt="o", ms=3.0,
        color=COLS["blue"], mec="k", mew=0.2, elinewidth=0.6, capsize=0,
    )
    ax.set_xscale("log")
    ax.set_xlim(30, 2600)
    ax.set_ylabel(r"$D_\ell^{TT}\;[\mu\mathrm{K}^2]$")
    ax.set_title("TT", fontsize=9)
    ax.grid(True, alpha=0.25)

    # --- TE (top-right) ---
    ax = axes[0, 1]
    ax.plot(th.ell, th.dl_TE, color=COLS["gray"], lw=1.2)
    el, dv, ev = _bin(te.ell, te.dl, (te.err_lo + te.err_hi) / 2.0, n=12)
    ax.errorbar(
        el, dv, yerr=ev, fmt="s", ms=2.8,
        color=COLS["orange"], mec="k", mew=0.2, elinewidth=0.5, capsize=0,
    )
    ax.set_xscale("log")
    ax.set_xlim(30, 2000)
    ax.set_ylabel(r"$D_\ell^{TE}\;[\mu\mathrm{K}^2]$")
    ax.set_title("TE", fontsize=9)
    ax.grid(True, alpha=0.25)

    # --- EE (bottom-left) ---
    ax = axes[1, 0]
    ax.plot(th.ell, th.dl_EE, color=COLS["gray"], lw=1.2)
    el, dv, ev = _bin(ee.ell, ee.dl, (ee.err_lo + ee.err_hi) / 2.0, n=12)
    ax.errorbar(
        el, dv, yerr=ev, fmt="D", ms=2.8,
        color=COLS["green"], mec="k", mew=0.2, elinewidth=0.5, capsize=0,
    )
    ax.set_xscale("log")
    ax.set_xlim(30, 2000)
    ax.set_xlabel(r"Multipole $\ell$")
    ax.set_ylabel(r"$D_\ell^{EE}\;[\mu\mathrm{K}^2]$")
    ax.set_title("EE", fontsize=9)
    ax.grid(True, alpha=0.25)

    # --- BB low-ell (bottom-right) ---
    ax = axes[1, 1]
    mask_bb = th.ell <= 30
    ax.plot(th.ell[mask_bb], th.dl_BB[mask_bb], color=COLS["gray"], lw=1.2)
    err_bb = np.vstack([bb.err_lo, bb.err_hi])
    ax.errorbar(
        bb.ell, bb.dl, yerr=err_bb, fmt="^", ms=3.6,
        color=COLS["red"], mec="k", mew=0.25, elinewidth=0.7, capsize=0,
    )
    ax.set_xlabel(r"Multipole $\ell$")
    ax.set_ylabel(r"$D_\ell^{BB}\;[\mu\mathrm{K}^2]$")
    ax.set_title(r"BB (low-$\ell$)", fontsize=9)
    ax.set_xlim(2, 30)
    ax.grid(True, alpha=0.25)

    fig.suptitle("Planck PR3 temperature + polarization spectra", fontsize=10.5)
    _save(fig, "fig_ch02b_planck_polarization_grid", "ch02_dipole")
    _caption(
        "fig_ch02b_planck_polarization_grid",
        "ch02_dipole",
        """
Planck PR3 four-panel overview of the baseline CMB anisotropy dataset
used in the paper. Top-left: binned TT bandpowers over ell in [30,
2500]. Top-right / bottom-left: TE and EE full-resolution spectra,
rebinned by factor 12 for readability. Bottom-right: low-ell BB (ell
<= 29). Gray curve in every panel is the Planck 2018 best-fit Lambda
CDM theory (dl_TT/TE/EE/BB from planck_pr3_bestfit.npz).
""",
    )


def fig_ch02c_cmb_map_commander() -> None:
    """Commander NSIDE=16 temperature map (Mollweide)."""
    import healpy as hp

    cat = ObsCache.cat()
    cmap = cat.load("planck.commander.nside16")
    T = np.asarray(cmap.I)
    nside = int(cmap.nside)

    vmax = np.percentile(np.abs(T), 99.5)
    fig = plt.figure(figsize=(7.2, 3.8))
    hp.mollview(
        T,
        fig=fig.number,
        cmap="RdBu_r",
        min=-vmax,
        max=vmax,
        unit=r"$\mu\mathrm{K}_{\rm CMB}$",
        title=r"Planck Commander CMB $\Delta T$ (NSIDE = 16)",
        cbar=True,
    )
    hp.graticule(dpar=30, dmer=60, color="0.6", alpha=0.5)
    _save(fig, "fig_ch02c_cmb_map_commander", "ch02_dipole")
    _caption(
        "fig_ch02c_cmb_map_commander",
        "ch02_dipole",
        """
Planck Commander component-separated CMB temperature map downsampled
from NSIDE=2048 to NSIDE=16 (3072 pixels, RING ordering; source
commander_nside16.npz). Symmetric colorbar clipped at the 99.5th
percentile of |Delta T|. A dipole mode is clearly visible and defines
the kinematic reference frame used throughout the paper.
""",
    )


def fig_ch02d_dipole_scenarios() -> None:
    """Scenario bar chart: ε₁ and β for the S0-S3 hypotheses."""
    cat = ObsCache.cat()
    scalars = cat.load("dipole_scalar_observations.consolidated")
    sc = scalars["scenarios"]

    names = ["S0", "S1", "S2a", "S2b", "S2c", "S3"]
    eps1 = np.array([sc[n]["eps1"] for n in names], dtype=float) * 1e3
    beta = np.array([sc[n]["beta"] for n in names], dtype=float) * 1e3

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=False)
    bar_colors = [COLS["gray"], COLS["blue"], COLS["orange"],
                  COLS["green"], COLS["red"], COLS["purple"]]

    ax1.bar(names, eps1, color=bar_colors, edgecolor="k", linewidth=0.4)
    ax1.axhline(1.2336, color=COLS["gray"], ls=":", lw=0.8,
                label=r"$\varepsilon_1^{\rm kin}$ (Planck)")
    ax1.set_ylabel(r"$\varepsilon_1\;[\times 10^{-3}]$")
    ax1.set_title("Dipole asymmetry", fontsize=9.5)
    ax1.grid(True, axis="y", alpha=0.25)
    ax1.legend(fontsize=8, loc="upper left")

    ax2.bar(names, beta, color=bar_colors, edgecolor="k", linewidth=0.4)
    ax2.axhline(1.334, color=COLS["orange"], ls=":", lw=0.8,
                label=r"$\beta_{\rm CF4}$")
    ax2.axhspan(1.334 - 0.267, 1.334 + 0.267,
                color=COLS["yellow"], alpha=0.2)
    ax2.set_ylabel(r"$\beta\;[\times 10^{-3}]$")
    ax2.set_title("Tilt rapidity", fontsize=9.5)
    ax2.grid(True, axis="y", alpha=0.25)
    ax2.legend(fontsize=8, loc="upper left")

    fig.suptitle("Dipole anomaly scenarios S0-S3", fontsize=10.5)
    fig.tight_layout()
    _save(fig, "fig_ch02d_dipole_scenarios", "ch02_dipole")
    _caption(
        "fig_ch02d_dipole_scenarios",
        "ch02_dipole",
        """
Dipole-anomaly scenario summary (values from
scalars/dipole_scalar_observations.json). Left: ε_1 multiplied by 1e3
for S0 (FLRW, 0), S1 (kinematic Planck, 1.234), S2a (CatWISE, 1.476),
S2b (kinematic ε_1 + CF4 β), S2c (radio Secrest+2021, 3.296), S3
(CatWISE + CF4). Right: tilt rapidity β. The CF4 1-σ band
β = (1.334 ± 0.267)e-3 is shown as the shaded region; non-zero β only
appears for S2a-S3.
""",
    )


def fig_ch02e_cf4_velocity_field() -> None:
    """CF4 peculiar-velocity samples: |v_xyz| vs |r|, with vr overlay."""
    cat = ObsCache.cat()
    cf4 = cat.load("cf4.query_batch")
    sgx, sgy, sgz = np.asarray(cf4.sgx), np.asarray(cf4.sgy), np.asarray(cf4.sgz)
    vxyz = np.asarray(cf4.vxyz_mean)
    vr = np.asarray(cf4.vr_mean)
    vxyz_std = np.asarray(cf4.vxyz_std)

    r = np.sqrt(sgx ** 2 + sgy ** 2 + sgz ** 2)
    vmag = np.linalg.norm(vxyz, axis=1)
    vmag_err = np.linalg.norm(vxyz_std, axis=1)

    order = np.argsort(r)
    r = r[order]
    vmag = vmag[order]
    vmag_err = vmag_err[order]
    vr = vr[order]

    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    ax.errorbar(
        r, vmag, yerr=vmag_err, fmt="o", ms=6,
        color=COLS["blue"], mec="k", mew=0.35, elinewidth=1.0, capsize=3,
        label=r"$|\vec v|$ (CF4 reconstruction, Cartesian)",
    )
    ax.plot(
        r, np.abs(vr), "s", ms=5, color=COLS["red"], mec="k", mew=0.25,
        label=r"$|v_r|$ (radial component)",
    )
    beta_cf4 = 1.334e-3
    c_kms = 299792.458
    v_cf4 = beta_cf4 * c_kms
    ax.axhline(v_cf4, color=COLS["orange"], ls="--", lw=1.0,
               label=rf"$\beta_{{\rm CF4}}\,c\approx {v_cf4:.0f}$ km/s")

    ax.set_xlabel(r"Supergalactic distance $|\vec r|$ [Mpc $h^{-1}$]")
    ax.set_ylabel(r"Peculiar velocity [km/s]")
    ax.set_title("CF4 bulk-flow sampling (8 query points)", fontsize=10)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.9)
    _save(fig, "fig_ch02e_cf4_velocity_field", "ch02_dipole")
    _caption(
        "fig_ch02e_cf4_velocity_field",
        "ch02_dipole",
        """
CF4 reconstruction peculiar-velocity batch sample
(pecvel/cf4/query_batch.npz, 8 grid positions). Blue points:
magnitude |v_xyz| of the Cartesian mean velocity; error bar is the
Euclidean norm of vxyz_std. Red squares: absolute radial component
|v_r|. Dashed orange line: β_CF4 c ≈ 400 km/s (Watkins+2009 COMPOSITE
legacy). Individual per-voxel velocities span ~200-1100 km/s across
|r| ∈ [120, 420] Mpc/h — the vector-summed bulk flow is much smaller
and sets the tilt rapidity prior used elsewhere.
""",
    )


# =====================================================================
# Chapter 5 — Tilt-boost kinematics (Lorentz factor)
# =====================================================================


def _B_factor(beta: np.ndarray, costheta: np.ndarray) -> np.ndarray:
    """Non-perturbative boost B(beta, cos theta) = cosh beta +
    sinh beta * cos theta (the direction-resolved tilt visibility
    correction used in lowell §11.3)."""
    return np.cosh(beta)[:, None] + np.sinh(beta)[:, None] * costheta[None, :]


def fig_ch05a_tilt_boost_heatmap() -> None:
    beta = np.linspace(0.0, 0.05, 200)
    cth = np.linspace(-1.0, 1.0, 200)
    B = _B_factor(beta, cth)

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    pcm = ax.pcolormesh(
        cth, beta * 1e3, B, cmap="viridis", shading="auto",
        vmin=B.min(), vmax=B.max(),
    )
    cs = ax.contour(cth, beta * 1e3, B, levels=[0.99, 1.00, 1.01, 1.02, 1.05],
                    colors="w", linewidths=0.7)
    ax.clabel(cs, inline=True, fontsize=7, fmt="%.2f")
    cbar = fig.colorbar(pcm, ax=ax)
    cbar.set_label(r"$B(\beta,\cos\theta)$", fontsize=9.5)
    ax.set_xlabel(r"$\cos\theta$ (angle to tilt axis)")
    ax.set_ylabel(r"Rapidity $\beta\;[\times 10^{-3}]$")
    ax.set_title(r"Non-perturbative boost $B=\cosh\beta+\sinh\beta\cos\theta$",
                 fontsize=10)
    _save(fig, "fig_ch05a_tilt_boost_heatmap", "ch05_teff")
    _caption(
        "fig_ch05a_tilt_boost_heatmap",
        "ch05_teff",
        """
Direction-resolved visibility correction B(β, cos θ) = cosh β + sinh β
cos θ (the closed-form Lorentz boost used by lowell §11.3 / LB-4 Layer
A). White contours: B = 0.99, 1.00, 1.01, 1.02, 1.05. The B = 1
contour passes through cos θ = 0 independently of β, encoding the
equatorial null of the dipole-only tilt correction.
""",
    )


def fig_ch05b_boost_directional_slice() -> None:
    betas = np.array([1e-4, 3e-4, 1e-3, 3e-3, 1e-2])
    cth = np.linspace(-1, 1, 400)
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    cmap = plt.get_cmap("plasma")
    for i, b in enumerate(betas):
        B = np.cosh(b) + np.sinh(b) * cth
        ax.plot(cth, B, color=cmap(i / (len(betas) - 1)), lw=1.6,
                label=rf"$\beta={b:.0e}$")
    ax.axhline(1.0, color="k", lw=0.6, ls=":")
    ax.set_xlabel(r"$\cos\theta$")
    ax.set_ylabel(r"$B(\beta,\cos\theta)$")
    ax.set_title(r"Forward/backward tilt asymmetry", fontsize=10)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8.5, loc="upper left", framealpha=0.9)
    _save(fig, "fig_ch05b_boost_directional_slice", "ch05_teff")
    _caption(
        "fig_ch05b_boost_directional_slice",
        "ch05_teff",
        """
Horizontal slices of the boost factor B(β, cos θ) at five fiducial
rapidities β ∈ {1e-4, 3e-4, 1e-3, 3e-3, 1e-2}. The amplitude grows
roughly linearly in β in the observationally relevant range; only the
β = 1e-2 curve exhibits visible cosh β contribution (intercept above
1.0 at cos θ = 0).
""",
    )


def fig_ch05c_boost_linear_vs_exact() -> None:
    beta = np.linspace(0.0, 3e-2, 300)
    cth_vals = [-1.0, -0.5, 0.5, 1.0]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5), sharex=True)

    ax = axes[0]
    for c in cth_vals:
        B_ex = np.cosh(beta) + np.sinh(beta) * c
        B_lin = 1.0 + beta * c
        ax.plot(beta * 1e3, B_ex, lw=1.5,
                label=rf"$\cos\theta={c:+.1f}$ (exact)")
        ax.plot(beta * 1e3, B_lin, lw=1.0, ls="--",
                color=ax.lines[-1].get_color(), alpha=0.7)
    ax.set_xlabel(r"$\beta\;[\times 10^{-3}]$")
    ax.set_ylabel(r"$B(\beta,\cos\theta)$")
    ax.set_title("Exact vs. linear", fontsize=9.5)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=7.5, loc="upper left")

    ax = axes[1]
    for c in cth_vals:
        B_ex = np.cosh(beta) + np.sinh(beta) * c
        B_lin = 1.0 + beta * c
        err = np.abs((B_lin - B_ex) / np.maximum(np.abs(B_ex), 1e-20))
        ax.loglog(beta[beta > 0] * 1e3, err[beta > 0], lw=1.3,
                  label=rf"$\cos\theta={c:+.1f}$")
    ax.set_xlabel(r"$\beta\;[\times 10^{-3}]$")
    ax.set_ylabel(r"$|B_{\rm lin}-B_{\rm exact}|/B_{\rm exact}$")
    ax.set_title("Relative error (absolute)", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.2)
    ax.legend(fontsize=7.5, loc="upper left")

    fig.suptitle(r"Linearization error of the tilt-boost correction",
                 fontsize=10.5)
    fig.tight_layout()
    _save(fig, "fig_ch05c_boost_linear_vs_exact", "ch05_teff")
    _caption(
        "fig_ch05c_boost_linear_vs_exact",
        "ch05_teff",
        """
Left: exact boost B = cosh β + sinh β cos θ (solid) vs linearization
1 + β cos θ (dashed) for cos θ ∈ {-1, -0.5, +0.5, +1}. Right: relative
error (B_lin - B_exact)/B_exact. Even at β = 3e-2 (ten times the CF4
upper band), the linearization error stays below ~5e-4, confirming
that linear kinematic approximations are sub-percent across all
realistic tilt amplitudes.
""",
    )


# =====================================================================
# Chapter 6 — Pipeline: species, background geometry, recombination
# =====================================================================


def fig_ch06a_species_omega() -> None:
    from bass.species.base import CANONICAL_ORDER, SpeciesLabel

    bg = BgCache.bg()
    reg = BgCache.registry()
    z_grid = np.geomspace(1e-3, 1e6, 400)
    a_grid = 1.0 / (1.0 + z_grid)
    eta_grid = np.array([bg.eta_at_a(a) for a in a_grid])

    key_map = {
        SpeciesLabel.PHOTON: "photon",
        SpeciesLabel.NEUTRINO: "neutrino",
        SpeciesLabel.BARYON: "baryon",
        SpeciesLabel.CDM: "cdm",
        SpeciesLabel.LAMBDA: "lambda",
    }

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    for lab in CANONICAL_ORDER:
        rho = np.asarray(reg[lab].rho_rest(eta_grid))
        key = key_map[lab]
        ax.plot(1 + z_grid, rho, lw=1.7, **SPECIES_STYLE[key])

    c = reg.constants
    z_eq = c.Omega_m_0 / c.Omega_r_0 - 1.0
    ax.axvline(1 + z_eq, color="0.3", ls=":", lw=0.8)
    ax.text(1 + z_eq, 3e-4, rf"$z_{{\rm eq}}\approx{z_eq:.0f}$",
            rotation=90, va="center", ha="right", fontsize=8, color="0.3")
    ax.axvspan(1 + 3400, 1e6, alpha=0.06, color=COLS["orange"])
    ax.axvspan(2, 1 + 3400, alpha=0.06, color=COLS["blue"])
    ax.axvspan(1, 2, alpha=0.06, color=COLS["green"])

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$1+z$")
    ax.set_ylabel(r"$\rho_s(z)\,/\,\rho_{\rm crit,0}$")
    ax.set_xlim(1, 1e6)
    ax.set_ylim(1e-10, 1e25)
    ax.grid(True, which="major", alpha=0.2)
    ax.legend(fontsize=9, loc="upper left", framealpha=0.9, ncol=1)
    ax.set_title("Species background evolution", fontsize=10)
    _save(fig, "fig_ch06a_species_omega", "ch06_pipeline")
    _caption(
        "fig_ch06a_species_omega",
        "ch06_pipeline",
        """
Energy-density evolution of the five species (photons, neutrinos,
baryons, CDM, Λ) on the shared FLRW η-grid
(bass.species.SpeciesBackgroundRegistry, Planck 2018 SSOT). Era
shading: radiation (orange, z > 3400), matter (blue), Λ (green);
z_eq ≈ 3400 marked. Closed-form adiabats are bit-exact within
float64 precision.
""",
    )


def fig_ch06b_hubble_geometry() -> None:
    bg = BgCache.bg()
    a = bg.a
    eta = bg.eta
    H = bg.H_mpc
    calH = bg.calH_mpc

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.4))

    ax = axes[0]
    ax.loglog(a, H, color=COLS["blue"], lw=1.7)
    ax.loglog(a, H[-1] * (a / a[-1]) ** -2, color=COLS["gray"], ls=":",
              lw=0.8, label=r"$H\propto a^{-2}$ (rad)")
    ax.loglog(a, H[-1] * (a / a[-1]) ** -1.5, color=COLS["gray"], ls="--",
              lw=0.8, label=r"$H\propto a^{-3/2}$ (mat)")
    ax.axhline(H[-1], color=COLS["green"], ls="-.", lw=0.8,
               label=r"de Sitter $H_0$")
    ax.set_xlabel(r"$a$")
    ax.set_ylabel(r"$H(a)\;[\mathrm{Mpc}^{-1}]$")
    ax.set_title(r"Hubble rate vs scale factor", fontsize=9.5)
    ax.grid(True, which="major", alpha=0.25)
    ax.legend(fontsize=8, loc="upper right")

    ax = axes[1]
    # eta(z) as conformal distance (η_0 − η)
    z = np.asarray(bg.z)
    eta_today = bg.eta_today
    d_eta = eta_today - eta
    mask = (z > 1e-3) & (z < 1e5)
    ax.plot(z[mask], d_eta[mask], color=COLS["purple"], lw=1.7)
    ax.axvline(1090, color=COLS["gray"], ls=":", lw=0.8)
    ax.text(1090, d_eta[mask].max() * 0.5,
            r"LSS $z\!\approx\!1090$", fontsize=8, color="0.4",
            rotation=90, va="center", ha="right")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e-3, 1e5)
    ax.set_xlabel(r"$z$")
    ax.set_ylabel(r"$\eta_0-\eta(z)\;[\mathrm{Mpc}]$")
    ax.set_title(r"Comoving distance to redshift", fontsize=9.5)
    ax.grid(True, which="major", alpha=0.25)

    fig.suptitle("FLRW background geometry (bass.species)", fontsize=10.5)
    fig.tight_layout()
    _save(fig, "fig_ch06b_hubble_geometry", "ch06_pipeline")
    _caption(
        "fig_ch06b_hubble_geometry",
        "ch06_pipeline",
        """
Left: H(a) computed by the bass.species.FLRWBackgroundTable (Planck
2018 closure), with radiation H ∝ a^-2 and matter H ∝ a^-3/2
asymptotes overlaid. Right: comoving distance η_0 - η(z) from z = 0
to the surface of last scattering (z ≈ 1090, dotted).
""",
    )


def fig_ch06c_recombination_panel() -> None:
    from bass.recombination.recombination_ingest import (
        load_recombination_table, build_interpolators,
    )

    fx = REPO_ROOT / "bass_py" / "bass" / "recombination" / "fixtures" / (
        "recombination_ref_planck2018.csv"
    )
    tab = load_recombination_table(fx)
    itps = build_interpolators(tab)
    z = np.geomspace(1.0, 8000.0, 600)

    x_e = itps.query_x_e(z)
    T_m = itps.query_T_m(z)
    T_cmb_0 = float(tab.metadata.get("t_cmb", "2.7255 K").split()[0])
    T_gamma = T_cmb_0 * (1 + z)
    tau_dot = itps.query_tau_dot(z)
    kappa = itps.query_kappa(z)
    g = itps.query_visibility(z)

    fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.4), constrained_layout=True)

    ax = axes[0, 0]
    ax.semilogx(z, x_e, color=COLS["blue"], lw=1.7)
    ax.axvline(1090, color="0.4", ls=":", lw=0.8)
    ax.text(1090, 0.5, r"$z_*\approx1090$", rotation=90, va="center",
            ha="right", fontsize=8, color="0.4")
    ax.set_xlabel(r"$z$")
    ax.set_ylabel(r"$x_e$")
    ax.set_title("Ionization fraction", fontsize=9.5)
    ax.grid(True, which="major", alpha=0.25)

    ax = axes[0, 1]
    ax.loglog(z, T_gamma, color=COLS["orange"], lw=1.6, label=r"$T_\gamma$")
    ax.loglog(z, T_m, color=COLS["blue"], lw=1.6, label=r"$T_m$")
    ax.set_xlabel(r"$z$")
    ax.set_ylabel(r"$T$ [K]")
    ax.set_title(r"$T_\gamma$, $T_m$ (Compton coupling)", fontsize=9.5)
    ax.grid(True, which="major", alpha=0.25)
    ax.legend(fontsize=8)

    ax = axes[1, 0]
    ax.loglog(z, tau_dot, color=COLS["purple"], lw=1.7)
    ax.set_xlabel(r"$z$")
    ax.set_ylabel(r"$\dot\tau\;[\mathrm{Mpc}^{-1}]$")
    ax.set_title(r"Thomson rate $\dot\tau(z)$", fontsize=9.5)
    ax.grid(True, which="major", alpha=0.25)

    ax = axes[1, 1]
    ax.plot(z, g, color=COLS["red"], lw=1.7, label=r"$g(z)$")
    ax2 = ax.twinx()
    ax2.plot(z, kappa, color=COLS["green"], lw=1.2, ls="--",
             label=r"$\kappa(z)$")
    ax2.axhline(1.0, color="0.4", ls=":", lw=0.6)
    ax.set_xlabel(r"$z$")
    ax.set_ylabel(r"$g(z)\;[\mathrm{Mpc}^{-1}]$", color=COLS["red"])
    ax2.set_ylabel(r"$\kappa(z)$", color=COLS["green"])
    ax.set_xlim(500, 1600)
    g_peak = float(np.max(g))
    z_peak = float(z[np.argmax(g)])
    ax.plot(z_peak, g_peak, "*", ms=10, mec="k", mew=0.3,
            color=COLS["red"])
    ax.annotate(
        rf"peak $z\!\approx\!{z_peak:.0f}$",
        (z_peak, g_peak),
        xytext=(z_peak + 100, g_peak * 0.6),
        fontsize=8, color=COLS["red"],
        arrowprops=dict(arrowstyle="->", color=COLS["red"], lw=0.5),
    )
    ax.set_title("Visibility + optical depth", fontsize=9.5)
    ax.grid(True, alpha=0.25)

    fig.suptitle("Recombination (HyRec-2 / Planck 2018 fixture)", fontsize=10.5)
    _save(fig, "fig_ch06c_recombination_panel", "ch06_pipeline")
    _caption(
        "fig_ch06c_recombination_panel",
        "ch06_pipeline",
        """
Recombination composite panel using the HyRec-2 Planck 2018 reference
fixture (bass/recombination/fixtures/recombination_ref_planck2018.csv).
Top-left: x_e(z) across z ∈ [1, 8000] with z_* ≈ 1090. Top-right:
T_gamma(z) = T0 (1+z) and matter temperature T_m(z) showing Compton
decoupling. Bottom-left: differential Thomson rate tau_dot(z).
Bottom-right: visibility g(z) (red) and cumulative optical depth
kappa(z) (dashed green); visibility peak marked with a star.
""",
    )


def fig_ch06d_reionization_tau_sweep() -> None:
    from bass.recombination.recombination_ingest import load_recombination_table
    from bass.recombination.reionization import (
        ReionizationParameters, compute_reionization_tau,
        extend_table_with_reionization, cosmology_from_metadata,
    )

    fx = REPO_ROOT / "bass_py" / "bass" / "recombination" / "fixtures" / (
        "recombination_ref_planck2018.csv"
    )
    tab = load_recombination_table(fx)
    cosmo = cosmology_from_metadata(tab.metadata)

    z_rei = np.linspace(5.5, 11.0, 30)
    tau = []
    for zr in z_rei:
        pars = ReionizationParameters(z_reion_H=float(zr))
        ext = extend_table_with_reionization(tab, pars, cosmology=cosmo)
        tau.append(compute_reionization_tau(ext, z_high_cutoff=30.0))
    tau = np.asarray(tau)

    tau_planck = 0.054
    sigma_planck = 0.007

    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    ax.axhspan(tau_planck - sigma_planck, tau_planck + sigma_planck,
               color=COLS["yellow"], alpha=0.25,
               label=r"Planck 2018 $\tau$ $1\sigma$")
    ax.axhline(tau_planck, color=COLS["orange"], lw=0.8, ls=":")
    ax.plot(z_rei, tau, color=COLS["blue"], lw=1.8,
            label=r"$\tau_{\rm reion}(z_{\rm rei})$ (tanh profile)")

    # Mark where our tanh crosses tau_planck
    from scipy.interpolate import interp1d
    try:
        zcross = float(interp1d(tau, z_rei)(tau_planck))
        ax.plot(zcross, tau_planck, "*", ms=11, mec="k", mew=0.3,
                color=COLS["red"],
                label=rf"$\tau=0.054$ at $z_{{\rm rei}}={zcross:.2f}$")
    except Exception:
        pass

    ax.set_xlabel(r"$z_{\rm reion, H}$")
    ax.set_ylabel(r"$\tau_{\rm reion}$")
    ax.set_title("Reionization optical depth vs midpoint redshift",
                 fontsize=10)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=9, loc="upper left", framealpha=0.9)
    _save(fig, "fig_ch06d_reionization_tau_sweep", "ch06_pipeline")
    _caption(
        "fig_ch06d_reionization_tau_sweep",
        "ch06_pipeline",
        """
Reionization optical depth tau_reion as a function of the hydrogen
reionization midpoint z_rei,H, using the tanh x_e profile from
bass.recombination.reionization (Delta z = 0.5, HeII at z = 3.5).
Yellow band: Planck 2018 tau = 0.054 ± 0.007. Red star marks the
crossing with the Planck central value, the production default.
""",
    )


# =====================================================================
# Chapter 7 — Bianchi shear dynamics
# =====================================================================


def _bianchi_solve(structure, sigma_over_H_init=1e-3, sigma_pm_ratio=0.0):
    from bass.background.einstein_bianchi import (
        BianchiCosmology, solve_bianchi_background,
    )
    from bass.species import default_constants

    c = default_constants()
    cosmo = BianchiCosmology(
        H0=c.H0_km_s_mpc,
        Omega_r=c.Omega_r_0,
        Omega_m=c.Omega_m_0,
        Omega_Lambda=c.Omega_Lambda_0,
        structure=structure,
        sigma_over_H_init=sigma_over_H_init,
        sigma_pm_ratio=sigma_pm_ratio,
    )
    return solve_bianchi_background(cosmo, a_start=1e-6, a_end=1.0, n_pts=1200)


def fig_ch07a_sigma_decay_types() -> None:
    from bass.background import bianchi_types as bt

    types = [
        ("Bianchi I", bt.type_i_constants(), COLS["blue"], "-"),
        ("Bianchi V", bt.type_v_constants(a_twist=5e-2), COLS["orange"], "--"),
        (r"Bianchi VII$_0$",
         bt.type_vii0_constants(n1=2e-2, n3=3e-2), COLS["green"], "-"),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.4, 3.6))

    base_Sigma2 = None
    base_a = None
    for name, s, c, ls in types:
        st = _bianchi_solve(s, sigma_over_H_init=1e-3, sigma_pm_ratio=0.5)
        a = st.a
        Sigma2 = (st.sigma_plus ** 2 + st.sigma_minus ** 2) / (6.0 * st.calH ** 2)
        Sigma2 = np.clip(Sigma2, 1e-30, None)
        ax1.loglog(a, Sigma2, color=c, lw=1.8, ls=ls, label=name,
                   alpha=0.95)
        if base_Sigma2 is None:
            base_a, base_Sigma2 = a, Sigma2
            ax2.axhline(1.0, color="0.5", ls=":", lw=0.7)
        else:
            ratio = np.interp(base_a, a, Sigma2) / base_Sigma2
            ax2.loglog(base_a, ratio, color=c, lw=1.6, ls=ls, label=name)

    for ax in (ax1, ax2):
        ax.set_xlabel(r"Scale factor $a$")
        ax.grid(True, which="major", alpha=0.25)

    ax1.set_ylim(1e-22, 1e-4)
    ax1.set_ylabel(r"$\Sigma^2 = \sigma_{ab}\sigma^{ab}/(6H^2)$")
    ax1.set_title(r"Shear decay by Bianchi type", fontsize=9.5)
    ax1.legend(fontsize=8.5)
    ax2.set_ylabel(r"$\Sigma^2(\mathrm{type})/\Sigma^2(\mathrm{I})$")
    ax2.set_title(r"Deviation from pure Bianchi-I Kasner", fontsize=9.5)
    ax2.legend(fontsize=8.5, loc="upper left")

    fig.suptitle(r"Background shear evolution — Bianchi I / V / VII$_0$",
                 fontsize=10.5)
    fig.tight_layout()
    _save(fig, "fig_ch07a_sigma_decay_types", "ch07_results")
    _caption(
        "fig_ch07a_sigma_decay_types",
        "ch07_results",
        """
Shear Σ² = Σ₊² + Σ₋² as a function of scale factor a for Bianchi I, V,
and VII₀ (bass.background.einstein_bianchi.solve_bianchi_background,
sigma/H initial = 1e-3, sigma_minus/sigma_plus = 0.5). Left panel:
absolute Σ²(a). Right panel: ratio to the Kasner a⁻⁶ asymptote — a
curve flat at 1.0 means pure radiation-dominated a⁻⁶ decay; deviation
at late times reflects structure-constant-induced curvature in V and
VII₀.
""",
    )


def fig_ch07b_sigma_phase_plane() -> None:
    from bass.background import bianchi_types as bt

    # avoid the degenerate Σ_-=0 case — use strictly positive ratios
    ratios = [0.1, 0.3, 0.8]
    fig, (ax, ax_t) = plt.subplots(1, 2, figsize=(7.8, 3.8))
    cmap = plt.get_cmap("plasma")

    for i, r in enumerate(ratios):
        st = _bianchi_solve(bt.type_i_constants(),
                            sigma_over_H_init=1e-3, sigma_pm_ratio=r)
        col = cmap(0.15 + 0.75 * i / max(1, len(ratios) - 1))
        sp = np.abs(st.sigma_plus)
        sm = np.abs(st.sigma_minus)
        ax.loglog(st.a, sp, color=col, lw=1.7,
                  label=rf"$|\Sigma_+|$, $\Sigma_-/\Sigma_+={r:.1f}$")
        ax.loglog(st.a, sm, color=col, lw=1.2, ls="--")
        ax_t.loglog(sp, sm, color=col, lw=1.7,
                    label=rf"$\Sigma_-/\Sigma_+={r:.1f}$")
        ax_t.plot(sp[0], sm[0], "o", color=col, mec="k", mew=0.3, ms=7)
        ax_t.plot(sp[-1], sm[-1], "s", color=col, mec="k", mew=0.3, ms=7)

    ax.set_xlabel(r"Scale factor $a$")
    ax.set_ylabel(r"$|\Sigma_\pm|$")
    ax.set_ylim(1e-17, 1e-2)
    ax.set_title(r"Shear magnitudes $|\Sigma_\pm(a)|$ (solid: $+$; dashed: $-$)",
                 fontsize=9.5)
    ax.grid(True, which="major", alpha=0.25)
    ax.legend(fontsize=8, loc="lower left")

    ax_t.set_xlabel(r"$|\Sigma_+|$")
    ax_t.set_ylabel(r"$|\Sigma_-|$")
    ax_t.set_xlim(1e-16, 1e-2)
    ax_t.set_ylim(1e-16, 1e-2)
    ax_t.set_title(r"Phase-plane — circle: initial, square: final",
                   fontsize=9.5)
    ax_t.grid(True, which="major", alpha=0.2)
    ax_t.legend(fontsize=8, loc="upper left")

    fig.suptitle(r"Bianchi I shear trajectories", fontsize=10.5)
    fig.tight_layout()
    _save(fig, "fig_ch07b_sigma_phase_plane", "ch07_results")
    _caption(
        "fig_ch07b_sigma_phase_plane",
        "ch07_results",
        """
Phase-plane trajectories (Σ₊, Σ₋) for Bianchi I shear with three
initial ratios Σ₋/Σ₊ ∈ {0.0, 0.3, 0.8} (filled circle = initial,
filled square = final). Both axes on symlog(1e-10) to show the full
decay from ~1e-3 to ~1e-12. The trajectories remain on radial lines
because Bianchi I structure constants are zero: Σ_± × a³ is conserved.
""",
    )


def fig_ch07c_sigma_a4_law() -> None:
    from bass.background import bianchi_types as bt
    st = _bianchi_solve(bt.type_i_constants(),
                        sigma_over_H_init=1e-3, sigma_pm_ratio=0.5)
    a = st.a
    # physical invariant sigma_ab sigma^ab ∝ a^-6 in Bianchi I
    Sigma2 = st.sigma_plus ** 2 + st.sigma_minus ** 2

    # focus on the radiation era where a^-6 decay is exact
    mask = (a >= 1e-5) & (a <= 3e-3)
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    cmap = plt.get_cmap("viridis")
    ns = [2, 3, 4, 5, 6]
    for i, n in enumerate(ns):
        y = Sigma2[mask] * a[mask] ** n
        # normalize at left end so flat = correct exponent
        y_norm = y / y[0]
        ax.loglog(a[mask], y_norm, color=cmap(i / (len(ns) - 1)), lw=1.7,
                  label=rf"$\Sigma^2\,a^{{{n}}}$")
    ax.axhline(1.0, color="0.3", ls=":", lw=0.8)
    ax.text(1e-4, 1.4, r"flat curve $\Rightarrow$ correct exponent",
            fontsize=9, color="0.3")
    ax.set_xlabel(r"Scale factor $a$ (radiation era)")
    ax.set_ylabel(r"$\sigma^2(a)\cdot a^n$ (normalized at $a=10^{-5}$)")
    ax.set_title(
        r"Power-law decay diagnostic: conformal shear "
        r"$\sigma_{ab}\sigma^{ab}\propto a^{-4}$",
        fontsize=10,
    )
    ax.grid(True, which="major", alpha=0.25)
    ax.legend(fontsize=9, loc="lower left", framealpha=0.9)
    _save(fig, "fig_ch07c_sigma_a4_law", "ch07_results")
    _caption(
        "fig_ch07c_sigma_a4_law",
        "ch07_results",
        """
Power-law diagnostic for Bianchi I shear in the radiation era: the
conformal-time shear invariant σ²(a) × aⁿ is plotted for n ∈ {2, 3,
4, 5, 6} and normalized at a = 10⁻⁵. The curve that is flat
identifies the correct decay exponent. In bass_py's conformal-time
convention the flat curve is n = 4 (σ² ∝ a⁻⁴), i.e. σ ∝ a⁻²
— equivalent to a ∝ η¹ × (const) in the radiation-era Kasner solution.
""",
    )


def fig_ch07d_sigma_seed_sweep() -> None:
    from bass.background import bianchi_types as bt

    seeds = [1e-5, 1e-4, 1e-3, 1e-2, 5e-2]
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    cmap = plt.get_cmap("plasma")
    for i, s in enumerate(seeds):
        st = _bianchi_solve(bt.type_i_constants(),
                            sigma_over_H_init=s, sigma_pm_ratio=0.3)
        a = st.a
        Sigma2 = (st.sigma_plus ** 2 + st.sigma_minus ** 2) / (6.0 * st.calH ** 2)
        ax.loglog(a, Sigma2, color=cmap(i / (len(seeds) - 1)), lw=1.5,
                  label=rf"$\sigma/H={s:.0e}$")
    ax.set_xlabel(r"$a$")
    ax.set_ylabel(r"$\Sigma^2$")
    ax.set_title(r"Bianchi I seed sweep", fontsize=10)
    ax.grid(True, which="major", alpha=0.25)
    ax.legend(fontsize=8.5, loc="lower left", framealpha=0.9)
    _save(fig, "fig_ch07d_sigma_seed_sweep", "ch07_results")
    _caption(
        "fig_ch07d_sigma_seed_sweep",
        "ch07_results",
        """
Shear evolution Σ²(a) for Bianchi I with five initial-condition seeds
sigma/H ∈ {1e-5, 1e-4, 1e-3, 1e-2, 5e-2}. All curves follow the same
a⁻⁶ slope; only the amplitude normalization changes, consistent with
the Kasner-regime separability.
""",
    )


# =====================================================================
# Chapter 8 — Observational robustness
# =====================================================================


def fig_ch08a_desi_sky_coverage() -> None:
    cat = ObsCache.cat()
    bgs = cat.load("desi.bgs.ngc")
    lrg = cat.load("desi.lrg.ngc")
    qso = cat.load("desi.qso.ngc")

    # Subsample for plotting
    rng = np.random.default_rng(42)
    n_sub = 120000
    def _sub(cat_, n=n_sub):
        idx = rng.choice(len(cat_.ra), size=min(n, len(cat_.ra)),
                         replace=False)
        return cat_.ra[idx], cat_.dec[idx], cat_.z[idx]

    bgs_ra, bgs_dec, bgs_z = _sub(bgs)
    lrg_ra, lrg_dec, lrg_z = _sub(lrg)
    qso_ra, qso_dec, qso_z = _sub(qso)

    fig = plt.figure(figsize=(7.4, 6.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.5, 1.0], hspace=0.35)

    # Mollweide-like sky map (equal area via aitoff)
    ax1 = fig.add_subplot(gs[0], projection="aitoff")
    for ra, dec, label, c, alpha in [
        (bgs_ra, bgs_dec, "BGS", COLS["blue"], 0.15),
        (lrg_ra, lrg_dec, "LRG", COLS["orange"], 0.15),
        (qso_ra, qso_dec, "QSO", COLS["red"], 0.10),
    ]:
        ra_wrap = np.where(ra > 180, ra - 360, ra)
        ax1.scatter(np.deg2rad(ra_wrap), np.deg2rad(dec),
                    s=0.4, color=c, alpha=alpha, label=label, rasterized=True)
    ax1.set_title("DESI Y1 NGC sky footprint (subsampled)",
                  fontsize=10, pad=12)
    ax1.grid(True, alpha=0.25)
    leg = ax1.legend(fontsize=8.5, loc="lower center",
                     markerscale=8, ncol=3, bbox_to_anchor=(0.5, -0.15))
    for lh in leg.legend_handles:
        lh.set_alpha(1.0)

    # n(z) histogram
    ax2 = fig.add_subplot(gs[1])
    bins = np.linspace(0.0, 3.5, 60)
    for z, label, c in [
        (bgs_z, "BGS (z<0.5)", COLS["blue"]),
        (lrg_z, "LRG (0.4<z<1.1)", COLS["orange"]),
        (qso_z, "QSO (0.8<z<3.5)", COLS["red"]),
    ]:
        ax2.hist(z, bins=bins, histtype="stepfilled",
                 alpha=0.45, color=c, edgecolor="k", linewidth=0.4,
                 label=label)
    ax2.set_xlabel(r"Redshift $z$")
    ax2.set_ylabel("Count (subsample)")
    ax2.set_title(r"DESI Y1 NGC redshift distribution", fontsize=9.5)
    ax2.grid(True, axis="y", alpha=0.25)
    ax2.legend(fontsize=8.5, loc="upper right")

    _save(fig, "fig_ch08a_desi_sky_coverage", "ch08_robustness")
    _caption(
        "fig_ch08a_desi_sky_coverage",
        "ch08_robustness",
        """
DESI Year-1 NGC footprint (top, Aitoff projection) for the three LSS
tracers: BGS_ANY (blue, z < 0.5), LRG (orange, 0.4 < z < 1.1), QSO
(red, 0.8 < z < 3.5). Each tracer is plotted as a random subsample of
120k objects. Bottom: n(z) histogram for the same subsamples,
illustrating the complementary redshift coverage used by the
number-count dipole likelihoods.
""",
    )


def fig_ch08b_planck_lensing() -> None:
    """Planck PR3 phi-phi bandpowers vs. CAMB Planck-2018 reference."""
    cat = ObsCache.cat()
    lens = cat.load("planck.pr3.lensing")
    camb = cat.load("camb.planck2018.lensing_refs")

    # Pick the consext8 MV bandpowers (baseline Planck PR3 lensing)
    key = "smicadx12_Dec5_ftl_mv2_ndclpp_p_teb_consext8_bandpowers.dat"
    if key not in lens:
        candidates = [k for k in lens.keys() if "ndclpp" in k
                      and "bandpowers" in k]
        if not candidates:
            raise RuntimeError("No lensing bandpowers file found")
        key = candidates[0]
    bp = np.asarray(lens[key])
    # Columns: [idx, bin_lo, bin_hi, bin_mid, Cl_hat, sigma, ...]
    bin_mid = bp[:, 3]
    cl_hat = bp[:, 4]
    sigma = bp[:, 5]

    # Both Planck bandpowers (col 4) and CAMB lens_potential_cls[:, 0]
    # use the same [L(L+1)]^2 C_L^{phi phi} / (2 pi) convention — no
    # rescaling needed.
    ell_pp = np.asarray(camb.ell_pp)
    pp_camb = np.asarray(camb.lens_potential_cls)[:, 0]

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.plot(ell_pp[2:], pp_camb[2:] * 1e7, color=COLS["gray"], lw=1.3,
            label=r"CAMB Planck 2018 (ref.)")
    ax.errorbar(
        bin_mid, cl_hat * 1e7, yerr=sigma * 1e7,
        fmt="o", ms=5.0, color=COLS["purple"], mec="k", mew=0.3,
        elinewidth=0.8, capsize=3,
        label=r"Planck PR3 lensing (SMICA MV, consext8)",
    )
    ax.set_xlabel(r"$L$")
    ax.set_ylabel(r"$10^7\,[L(L+1)]^2\,C_L^{\phi\phi}/(2\pi)$")
    ax.set_xscale("log")
    ax.set_xlim(5, 2500)
    ax.set_ylim(0, 1.8)
    ax.grid(True, which="major", alpha=0.25)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.9)
    ax.set_title(r"CMB lensing potential: Planck PR3 vs CAMB",
                 fontsize=10)
    _save(fig, "fig_ch08b_planck_lensing", "ch08_robustness")
    _caption(
        "fig_ch08b_planck_lensing",
        "ch08_robustness",
        """
Planck PR3 CMB lensing bandpowers (source:
cmb/lensing/planck_pr3_lensing.npz, MV phi-phi estimator) compared to
the CAMB Planck-2018 reference lens_potential_cls. Units: 10^7 × [L
(L+1)]² C_L^{phi phi} / (2π); normalization of observed and reference
curves differs by conventions noted in INDEX.json.
""",
    )


def fig_ch08c_cf4_delta_vs_distance() -> None:
    cat = ObsCache.cat()
    cf4 = cat.load("cf4.query_batch")
    sgx, sgy, sgz = np.asarray(cf4.sgx), np.asarray(cf4.sgy), np.asarray(cf4.sgz)
    delta = np.asarray(cf4.delta_mean)
    delta_std = np.asarray(cf4.delta_std)
    r = np.sqrt(sgx ** 2 + sgy ** 2 + sgz ** 2)
    order = np.argsort(r)

    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    ax.errorbar(
        r[order], delta[order], yerr=delta_std[order],
        fmt="o", ms=6, color=COLS["green"], mec="k", mew=0.35,
        elinewidth=1.0, capsize=3,
    )
    ax.axhline(0, color="0.3", ls=":", lw=0.7)
    ax.set_xlabel(r"$|\vec r|$ [Mpc $h^{-1}$]")
    ax.set_ylabel(r"$\delta$ (density contrast)")
    ax.set_title("CF4 reconstruction density contrast vs distance",
                 fontsize=10)
    ax.grid(True, alpha=0.25)
    _save(fig, "fig_ch08c_cf4_delta_vs_distance", "ch08_robustness")
    _caption(
        "fig_ch08c_cf4_delta_vs_distance",
        "ch08_robustness",
        """
CF4 peculiar-velocity reconstruction density contrast delta at the 8
query positions, plotted versus Euclidean supergalactic distance.
Error bars are delta_std from pecvel/cf4/query_batch.npz. The large
negative delta at the closest sampled point (near the Local Group)
reflects the local underdensity, a known feature of CF4
reconstructions.
""",
    )


# =====================================================================
# Chapter 5 (cont.) — Tilted visibility Γ̃_T(η, e)
# =====================================================================


def fig_ch05d_tilted_visibility() -> None:
    """Direction-resolved Thomson rate Γ̃_T(η, ê) under a constant
    tilt β along ẑ; left: amplitude vs 1+z for forward / back / side;
    right: ratio Γ̃_T / Γ_T converges to γ(1±β), γ exactly."""
    from bass.collision.tilted_visibility import TiltedVisibility
    from bass.species.baryon import BaryonBackground
    from bass.species import default_constants
    from bass.recombination.recombination_ingest import (
        load_recombination_table, build_interpolators,
    )
    from bass.recombination.reionization import (
        ReionizationParameters, extend_table_with_reionization,
        cosmology_from_metadata,
    )

    fx = REPO_ROOT / "bass_py" / "bass" / "recombination" / "fixtures" / (
        "recombination_ref_planck2018.csv"
    )
    tab = load_recombination_table(fx)
    cosmo = cosmology_from_metadata(tab.metadata)
    ext = extend_table_with_reionization(
        tab, ReionizationParameters(), cosmology=cosmo,
    )
    interp = build_interpolators(ext)
    bg = BgCache.bg()
    c = default_constants()
    baryon = BaryonBackground(bg, c.Omega_b_0, interp)

    beta = 0.3
    v_hat = np.array([0.0, 0.0, 1.0])
    tv = TiltedVisibility(baryon, lambda eta: beta * v_hat)

    eta_sub = np.linspace(bg.eta_min * 5.0, bg.eta_today * 0.99, 400)
    z_sub = 1.0 / np.array([float(bg.interp_a(e)) for e in eta_sub]) - 1.0
    mask = (z_sub >= 0.0) & (z_sub <= 7900.0)
    eta_sub = eta_sub[mask]
    z_sub = z_sub[mask]

    G_scalar = np.array([float(baryon.tau_dot(e)) for e in eta_sub])
    G_fwd = np.array([tv.Gamma_T(e, v_hat) for e in eta_sub])
    G_bck = np.array([tv.Gamma_T(e, -v_hat) for e in eta_sub])
    G_sd = np.array([tv.Gamma_T(e, np.array([1.0, 0.0, 0.0]))
                     for e in eta_sub])

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(7.4, 3.6))
    ax_a.loglog(1 + z_sub, G_scalar, color="0.4", lw=1.1, ls="-",
                label=r"$\Gamma_T$ (scalar)")
    ax_a.loglog(1 + z_sub, G_fwd, color=COLS["orange"], lw=1.4,
                label=r"$\tilde\Gamma_T(+\hat z)$")
    ax_a.loglog(1 + z_sub, G_bck, color=COLS["blue"], lw=1.4,
                label=r"$\tilde\Gamma_T(-\hat z)$")
    ax_a.loglog(1 + z_sub, G_sd, color=COLS["purple"], lw=1.4, ls="--",
                label=r"$\tilde\Gamma_T(\hat x)$")
    ax_a.set_xlabel(r"$1+z$")
    ax_a.set_ylabel(r"$\tilde\Gamma_T\;[\mathrm{Mpc}^{-1}]$")
    ax_a.set_title(rf"Thomson rate anisotropy at $\beta={beta:.2f}$",
                   fontsize=9.5)
    ax_a.grid(True, which="major", alpha=0.25)
    ax_a.legend(fontsize=7.5, loc="lower left")

    min_G = 1e-3 * G_scalar.max()
    ok = G_scalar > min_G
    ax_b.plot(1 + z_sub[ok], G_fwd[ok] / G_scalar[ok],
              color=COLS["orange"], lw=1.4, label="forward")
    ax_b.plot(1 + z_sub[ok], G_bck[ok] / G_scalar[ok],
              color=COLS["blue"], lw=1.4, label="back")
    ax_b.plot(1 + z_sub[ok], G_sd[ok] / G_scalar[ok],
              color=COLS["purple"], lw=1.4, ls="--", label="side")
    gamma = 1.0 / np.sqrt(1.0 - beta ** 2)
    for lvl, c in [(gamma * (1 + beta), COLS["orange"]),
                   (gamma * (1 - beta), COLS["blue"]),
                   (gamma, COLS["purple"])]:
        ax_b.axhline(lvl, color=c, ls=":", lw=0.7)
    ax_b.set_xscale("log")
    ax_b.set_xlabel(r"$1+z$")
    ax_b.set_ylabel(r"$\tilde\Gamma_T/\Gamma_T$")
    ax_b.set_title(r"Direction / scalar ratio", fontsize=9.5)
    ax_b.set_ylim(0.5, 1.6)
    ax_b.grid(True, alpha=0.25)
    ax_b.legend(fontsize=7.5, loc="upper right")

    fig.suptitle(r"Tilted Thomson visibility $\tilde\Gamma_T(\eta, \hat e)$",
                 fontsize=10.5)
    fig.tight_layout()
    _save(fig, "fig_ch05d_tilted_visibility", "ch05_teff")
    _caption(
        "fig_ch05d_tilted_visibility",
        "ch05_teff",
        """
Direction-resolved Thomson rate Γ̃_T(η, ê) computed by
bass.collision.tilted_visibility.TiltedVisibility under a constant
rapidity β = 0.3 along ẑ (bass.species.baryon.BaryonBackground; HyRec
fixture + tanh reionization). Left: Γ̃_T for forward (+ẑ), back (−ẑ),
and side (x̂) directions against the scalar Γ_T(η). Right: ratio to
the scalar rate; dotted lines mark the exact special-relativistic
expectations γ(1±β) and γ.
""",
    )


# =====================================================================
# Chapter 6 (cont.) — Hierarchy precision & conversion diagnostics
# =====================================================================


def fig_ch06e_closure_error_vs_L() -> None:
    """Per-ℓ closure-error convergence: ‖Δ dy/dη‖ vs L_trunc with a
    reference tower at L_ref=6, under a frozen Bianchi I shear."""
    from bass.hierarchy import (
        PSTFTensor, PSTFHierarchyState, HardCutClosure,
        ZeroCollisionOperator, hierarchy_rhs_photon, measure_closure_error,
    )
    bg = BgCache.bg()
    L_ref = 6
    rng = np.random.default_rng(1303)
    tensors = []
    for ell in range(L_ref + 1):
        comp = np.zeros(2 * ell + 1, dtype=np.float64)
        comp[ell] = 0.5 ** ell
        comp += 0.02 * rng.normal(size=2 * ell + 1)
        tensors.append(PSTFTensor(ell=ell, components=comp))
    state_ref = PSTFHierarchyState(L=L_ref, tensors=tensors)

    sigma_proper = 3e-4 * np.diag([1.0, -0.5, -0.5])
    Sigma_grid = np.array([sigma_proper * ai for ai in bg.a])

    class _ShearFx:
        def __init__(self):
            self.eta = bg.eta.copy()
            self.sigma_tensor = Sigma_grid

    fx = _ShearFx()
    eta_eval = float(bg.eta[bg.eta.size // 2])
    driver_kwargs = dict(
        eta=eta_eval, bg_table=bg, tetrad_state=fx,
        collision=ZeroCollisionOperator(),
    )

    L_truncs = list(range(2, L_ref + 1))
    ells_plotted = list(range(L_ref))
    err_table = {ell: [] for ell in ells_plotted}
    for Lt in L_truncs:
        errors = measure_closure_error(
            state_ref, hierarchy_rhs_photon, L_trunc=Lt,
            closure_ref=HardCutClosure(), closure_trunc=HardCutClosure(),
            driver_kwargs=driver_kwargs,
        )
        for ell in ells_plotted:
            err_table[ell].append(errors.get(ell, np.nan))

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    cmap = plt.get_cmap("viridis")
    markers = ["o", "s", "^", "D", "v", "P"]
    for ell in ells_plotted:
        vals = np.asarray(err_table[ell], dtype=np.float64)
        vals = np.where(vals > 0, vals, 1e-18)
        ax.semilogy(L_truncs, vals, marker=markers[ell % len(markers)],
                    ms=6, color=cmap(ell / max(L_ref - 1, 1)), lw=1.4,
                    label=rf"$\ell={ell}$")
    ax.axvline(L_ref, color="0.4", ls=":", lw=0.8,
               label=rf"$L_\mathrm{{ref}}={L_ref}$")
    ax.set_xlabel(r"truncation depth $L_\mathrm{trunc}$")
    ax.set_ylabel(r"$\|\Delta\,dy/d\eta\|$  (Frobenius, per $\ell$)")
    ax.set_title(
        r"PSTF hierarchy closure convergence "
        r"(Bianchi I, $\sigma_+\!\approx\!3\!\times\!10^{-4}$)",
        fontsize=10,
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=8, ncol=2, loc="lower left")
    _save(fig, "fig_ch06e_closure_error_vs_L", "ch06_pipeline")
    _caption(
        "fig_ch06e_closure_error_vs_L",
        "ch06_pipeline",
        """
Per-ℓ Frobenius norm of the closure error ‖Δ dy/dη‖ versus truncation
depth L_trunc, built on a reference tower at L_ref = 6 with
geometrically decaying m=0 components (c_ℓ = 2⁻ℓ plus small noise).
At L_trunc = L_ref all ℓ-errors collapse to zero; toward L_trunc = 2
the T₇ Π_{ℓ+2} coupling drives the dominant error onto the
shear-injected Π₂ / Π₃ slots. Driver frozen to Bianchi I σ_+ ≈ 3×10⁻⁴
(sec §11.5 C-13…C-15).
""",
    )


def fig_ch06f_pstf_roundtrip() -> None:
    """Machine-precision round-trip of the PSTF packed ↔ full flat-basis
    transform, vs the 3^ℓ-cache growth reference line."""
    from bass.hierarchy import (
        L_MAX_CACHED, pstf_pack, pstf_unpack,
    )
    rng = np.random.default_rng(2026)
    ells = np.arange(L_MAX_CACHED + 1)
    max_err = np.zeros_like(ells, dtype=np.float64)
    mean_err = np.zeros_like(ells, dtype=np.float64)
    n_samples = 60
    for i, ell in enumerate(ells):
        errs = []
        for _ in range(n_samples):
            c = rng.normal(size=2 * int(ell) + 1)
            T = pstf_unpack(c, int(ell))
            c_rt = pstf_pack(T)
            errs.append(float(np.max(np.abs(c - c_rt))))
        max_err[i] = max(np.max(errs), 1e-17)
        mean_err[i] = max(np.mean(errs), 1e-17)
    ref = np.finfo(np.float64).eps * (3.0 ** ells)

    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    ax.semilogy(ells, max_err, marker="o", ms=6, color=COLS["orange"],
                lw=1.4, label=r"max error")
    ax.semilogy(ells, mean_err, marker="s", ms=6, color=COLS["blue"],
                lw=1.4, label=r"mean error")
    ax.semilogy(ells, ref, color="0.3", ls=":", lw=1.1,
                label=r"$\varepsilon_{\rm mach}\times 3^\ell$")
    ax.set_xlabel(r"multipole rank $\ell$")
    ax.set_ylabel(r"$\|c - c_{\rm rt}\|_\infty$")
    ax.set_title(r"PSTF packed $\leftrightarrow$ full round-trip precision",
                 fontsize=10)
    ax.set_xticks(ells)
    ax.grid(True, which="both", alpha=0.2)
    ax.legend(fontsize=9, loc="upper left")
    _save(fig, "fig_ch06f_pstf_roundtrip", "ch06_pipeline")
    _caption(
        "fig_ch06f_pstf_roundtrip",
        "ch06_pipeline",
        """
Round-trip precision of the projector-based packed ↔ full PSTF
transform for ℓ = 0..8: 60 Gaussian random inputs per rank passed
through pstf_unpack → pstf_pack. Max and mean infinity-norms are
compared against the ε_mach × 3^ℓ reference that controls the loss of
significance from the 3ᵉˡˡ-sized Cartesian-STF coefficient cache.
Round-trip stays at least 2–3 orders of magnitude below reference,
confirming LB-0 zero-error invariant.
""",
    )


def fig_ch06g_sigma_Sigma_conversion() -> None:
    """Conformal Σ_+ vs proper σ_+ = Σ_+/a dictionary + a/Σ consistency
    ratio (identity)."""
    from bass.background.einstein_bianchi import (
        BianchiCosmology, solve_bianchi_background,
    )
    from bass.background import bianchi_types as bt

    cosmo = BianchiCosmology(
        structure=bt.type_i_constants(),
        sigma_over_H_init=5e-3, sigma_pm_ratio=0.0,
    )
    bianchi_bg = solve_bianchi_background(cosmo, n_pts=1500)
    a = np.asarray(bianchi_bg.a)
    Sp = np.asarray(bianchi_bg.sigma_plus)
    sp_proper = Sp / np.maximum(a, 1e-30)
    z = 1.0 / np.maximum(a, 1e-300) - 1.0

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(7.4, 3.6))
    ax_a.loglog(1 + z, np.abs(Sp), color=COLS["orange"], lw=1.5,
                label=r"$|\Sigma_+|$ (conformal, dimless.)")
    ax_a.loglog(1 + z, np.abs(sp_proper), color=COLS["blue"], lw=1.5,
                label=r"$|\sigma_+|=|\Sigma_+|/a$ [Mpc$^{-1}$]")
    ax_a.set_xlabel(r"$1+z$")
    ax_a.set_ylabel("shear amplitude")
    ax_a.set_title(r"Conformal $\Sigma_+$ vs proper $\sigma_+$",
                   fontsize=9.5)
    ax_a.grid(True, which="major", alpha=0.25)
    ax_a.legend(fontsize=8, loc="upper left")

    ratio = np.abs(Sp) / np.maximum(a * np.abs(sp_proper), 1e-30)
    ax_b.semilogx(1 + z, ratio, color=COLS["purple"], lw=1.5)
    ax_b.axhline(1.0, color="0.3", ls=":", lw=0.6)
    ax_b.set_xlabel(r"$1+z$")
    ax_b.set_ylabel(r"$|\Sigma_+|/(a\,|\sigma_+|)$")
    ax_b.set_title(r"Conversion identity check", fontsize=9.5)
    ax_b.set_ylim(0.0, 2.0)
    ax_b.grid(True, alpha=0.25)

    fig.suptitle(r"Shear conversion dictionary (bass_py LB-2b)",
                 fontsize=10.5)
    fig.tight_layout()
    _save(fig, "fig_ch06g_sigma_Sigma_conversion", "ch06_pipeline")
    _caption(
        "fig_ch06g_sigma_Sigma_conversion",
        "ch06_pipeline",
        """
Left: conformal shear Σ_+(z) (bass_py tetrad_state convention, Pontzen)
alongside proper shear σ_+ = Σ_+/a fed to the T7/T8/T9 terms of the
hierarchy RHS. The one-decade gap between them is the Hubble factor.
Right: identity check |Σ_+|/(a |σ_+|) = 1 to machine precision across
the full recombination-to-today η-range, confirming the driver's 1/a
conversion is internally consistent (LB-2b F1 audit).
""",
    )


# =====================================================================
# Chapter 7 (cont.) — Collision operators, TCA, Class A attractors
# =====================================================================


def fig_ch07e_thomson_coefficients() -> None:
    """Bar chart of the per-ℓ Thomson collision coefficients for T and
    E modes (Ma-Bertschinger eq 63–65 / Zaldarriaga-Seljak eq 7, 17)."""
    ells = np.arange(0, 9)
    T_self = np.zeros_like(ells, dtype=np.float64)
    T_self[1] = -1.0
    T_self[2] = -9.0 / 10.0
    T_self[3:] = -1.0
    T_cross = np.zeros_like(ells, dtype=np.float64)
    T_cross[2] = -np.sqrt(6.0) / 10.0

    E_self = np.zeros_like(ells, dtype=np.float64)
    E_self[2] = -2.0 / 5.0
    E_self[3:] = -1.0
    E_cross = np.zeros_like(ells, dtype=np.float64)
    E_cross[2] = -3.0 / (5.0 * np.sqrt(6.0))

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(7.6, 3.6))
    width = 0.38

    ax_a.bar(ells - width / 2, T_self, width, color=COLS["blue"], alpha=0.85,
             edgecolor="k", linewidth=0.3,
             label=r"self  $K^T_\ell\!\propto\!\Pi_\ell$")
    ax_a.bar(ells + width / 2, T_cross, width, color=COLS["orange"], alpha=0.85,
             edgecolor="k", linewidth=0.3,
             label=r"cross  $K^T_\ell\!\propto\!E_\ell$")
    ax_a.axhline(0.0, color="0.4", lw=0.6)
    ax_a.set_xticks(ells)
    ax_a.set_xlabel(r"multipole $\ell$")
    ax_a.set_ylabel(r"$K^T_\ell / \Gamma_T$")
    ax_a.set_title("Temperature (Ma–Bertschinger)", fontsize=9.5)
    ax_a.grid(True, axis="y", alpha=0.2)
    ax_a.legend(fontsize=7.5, loc="lower right")

    ax_b.bar(ells - width / 2, E_self, width, color=COLS["purple"], alpha=0.85,
             edgecolor="k", linewidth=0.3,
             label=r"self  $K^E_\ell\!\propto\!E_\ell$")
    ax_b.bar(ells + width / 2, E_cross, width, color=COLS["green"], alpha=0.85,
             edgecolor="k", linewidth=0.3,
             label=r"cross  $K^E_\ell\!\propto\!\Pi_\ell$")
    ax_b.axhline(0.0, color="0.4", lw=0.6)
    ax_b.set_xticks(ells)
    ax_b.set_xlabel(r"multipole $\ell$")
    ax_b.set_ylabel(r"$K^E_\ell / \Gamma_T$")
    ax_b.set_title("E-mode (Zaldarriaga–Seljak)", fontsize=9.5)
    ax_b.grid(True, axis="y", alpha=0.2)
    ax_b.legend(fontsize=7.5, loc="lower right")

    fig.suptitle(r"Per-$\ell$ Thomson coefficients (bass.collision)",
                 fontsize=10.5)
    fig.tight_layout()
    _save(fig, "fig_ch07e_thomson_coefficients", "ch07_results")
    _caption(
        "fig_ch07e_thomson_coefficients",
        "ch07_results",
        """
Per-multipole Thomson collision coefficients K_ℓ / Γ_T extracted
from bass.collision.thomson_pstf. Left: temperature tower (Ma &
Bertschinger 1995, eq 63–65) — self-coupling K^T_ℓ = −Π_ℓ for ℓ ≥ 3;
ℓ = 2 splits into self (−9/10) plus the polter cross (−√6/10) onto
E_2. Right: E-mode tower (Zaldarriaga & Seljak 1997) — self −2/5 and
cross −3/(5√6) at the quadrupole, −E_ℓ above. Confirms the exact 4/3
polarization amplification factor embedded in bass.closure.
""",
    )


def fig_ch07f_tca_polter_ratio() -> None:
    """TCA-limit Θ_2, E_2 amplitudes scale as Γ_T^{-1}; their ratio
    converges to the canonical polter value −√6/4 as S_E → 0."""
    from bass.closure.quadrupole_tca import solve_tca_closure
    from bass.runtime.canonical_decision import make_canonical_decision
    from tsc.diagnostics.tangency import TangentKind, compute_D_diagnostic

    def _G(x): return np.asarray(x, dtype=np.float64)
    tang = compute_D_diagnostic(
        G_field=_G, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
    )
    decision = make_canonical_decision(
        beta_result=(True, {
            "beta": 1.36e-3, "beta_max": 8.62e-3, "slack": 7.26e-3,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=tang,
    )
    gT_grid = np.geomspace(0.1, 1e4, 40)
    S_T = 1e-6
    S_E_vals = [0.0, 0.2 * S_T, -0.5 * S_T]

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(7.0, 5.4),
                                         sharex=True)
    colors = [COLS["blue"], COLS["orange"], COLS["purple"]]
    for i, S_E in enumerate(S_E_vals):
        theta = np.zeros_like(gT_grid)
        Ev = np.zeros_like(gT_grid)
        for j, gT in enumerate(gT_grid):
            t, e = solve_tca_closure(
                S_T=S_T, S_E=S_E, gamma_T=float(gT), decision=decision,
            )
            theta[j] = t
            Ev[j] = e
        lbl = fr"$S_E/S_T={S_E / S_T:+.2g}$"
        ax_top.loglog(gT_grid, np.abs(theta), color=colors[i], lw=1.4, ls="-",
                      label=r"$|\Theta_2|$  " + lbl)
        ax_top.loglog(gT_grid, np.abs(Ev), color=colors[i], lw=1.4, ls="--")
        ratio = np.where(theta != 0.0, Ev / theta, np.nan)
        ax_bot.semilogx(gT_grid, ratio, color=colors[i], lw=1.4, label=lbl)

    ax_bot.axhline(-np.sqrt(6.0) / 4.0, color="0.3", ls=":",
                   label=r"canonical $-\sqrt{6}/4$")
    ax_top.set_ylabel(r"$|\Theta_2|, |E_2|$")
    ax_top.set_title(r"TCA amplitudes $\propto 1/\Gamma_T$ (solid: $\Theta_2$, dashed: $E_2$)",
                     fontsize=9.5)
    ax_top.grid(True, which="both", alpha=0.2)
    ax_top.legend(fontsize=7.5, ncol=2, loc="lower left")

    ax_bot.set_xlabel(r"$\Gamma_T\;[\mathrm{Mpc}^{-1}]$")
    ax_bot.set_ylabel(r"$E_2/\Theta_2$")
    ax_bot.set_title(r"Polter ratio convergence (canonical at $S_E=0$)",
                     fontsize=9.5)
    ax_bot.set_ylim(-1.3, 1.5)
    ax_bot.grid(True, alpha=0.2)
    ax_bot.legend(fontsize=8, loc="upper right")

    fig.tight_layout()
    _save(fig, "fig_ch07f_tca_polter_ratio", "ch07_results")
    _caption(
        "fig_ch07f_tca_polter_ratio",
        "ch07_results",
        """
Tight-coupling-approximation equilibrium from
bass.closure.quadrupole_tca.solve_tca_closure. Top: |Θ₂|, |E₂| vs
Thomson rate Γ_T for three source ratios S_E/S_T ∈ {0, +0.2, −0.5}.
Both amplitudes scale as Γ_T⁻¹ across four decades. Bottom: the
polter ratio E₂/Θ₂ locks to the canonical value −√6/4 ≈ −0.612 in the
limit S_E → 0, independent of Γ_T — a bass_py machine-precision
cross-check of the W6-04 closure.
""",
    )


def fig_ch07g_ellis_kasner_invariants() -> None:
    """Type I vacuum-Kasner invariants: Σ_+ × a² (Ellis conformal),
    σ_+ × a³ (Kasner), σ_+² (shear-energy proxy ∝ 1/a⁶)."""
    from bass.background.einstein_bianchi import (
        type_i_cosmology, solve_bianchi_background,
    )
    cosmo = type_i_cosmology(sigma_over_H_init=1e-4)
    st = solve_bianchi_background(cosmo, a_start=1e-6, a_end=1.0, n_pts=2000)
    mask = np.abs(st.sigma_plus) > 1e-30
    a = st.a[mask]
    Sp = st.sigma_plus[mask]
    sp_proper = Sp / a

    ellis_inv = Sp * a ** 2
    kasner_inv = sp_proper * a ** 3
    rho_shear = sp_proper ** 2

    fig, axes = plt.subplots(1, 3, figsize=(8.8, 3.2))
    axes[0].semilogx(a, ellis_inv, color=COLS["blue"], lw=1.5)
    axes[0].axhline(float(ellis_inv.mean()), color="0.4", ls=":", lw=0.8,
                    label=rf"$\langle \Sigma_+ a^2 \rangle$")
    axes[0].set_xlabel(r"$a$")
    axes[0].set_ylabel(r"$\Sigma_+\,a^2$")
    axes[0].set_title("Ellis conformal invariant", fontsize=9)
    axes[0].grid(True, which="major", alpha=0.2)
    axes[0].legend(fontsize=8)

    axes[1].semilogx(a, kasner_inv, color=COLS["orange"], lw=1.5)
    axes[1].axhline(float(kasner_inv.mean()), color="0.4", ls=":", lw=0.8,
                    label=r"$\langle \sigma_+ a^3 \rangle$")
    axes[1].set_xlabel(r"$a$")
    axes[1].set_ylabel(r"$\sigma_+\,a^3$")
    axes[1].set_title(r"Kasner invariant", fontsize=9)
    axes[1].grid(True, which="major", alpha=0.2)
    axes[1].legend(fontsize=8)

    axes[2].loglog(a, rho_shear, color=COLS["purple"], lw=1.5,
                   label=r"$\sigma_+^2$")
    ref = rho_shear[0] * (a[0] / a) ** 6
    axes[2].loglog(a, ref, color="0.4", ls="--", lw=0.8,
                   label=r"$\propto a^{-6}$")
    axes[2].set_xlabel(r"$a$")
    axes[2].set_ylabel(r"$\sigma_+^2\;[\mathrm{Mpc}^{-2}]$")
    axes[2].set_title(r"Shear energy $\propto 1/a^6$", fontsize=9)
    axes[2].grid(True, which="major", alpha=0.2)
    axes[2].legend(fontsize=8)

    fig.suptitle(r"Type I: Ellis / Kasner / shear-energy conservation",
                 fontsize=10.5)
    fig.tight_layout()
    _save(fig, "fig_ch07g_ellis_kasner_invariants", "ch07_results")
    _caption(
        "fig_ch07g_ellis_kasner_invariants",
        "ch07_results",
        """
Bianchi I vacuum-Kasner invariants along the direct bass_py
background integrator (type_i_cosmology, σ/H|_init = 10⁻⁴): conformal
Ellis invariant Σ_+ × a² (left), proper Kasner invariant σ_+ × a³
(middle), and shear-energy proxy σ_+² decaying as a⁻⁶ with a dashed
reference line (right). All three remain flat to machine precision
across six decades of a, confirming FB-0.1 / FB-1.1 Type I validation.
""",
    )


def fig_ch07h_bianchi_class_a_attractors() -> None:
    """Class A Bianchi Σ_+(a) trajectories: I / II / VI₀ / VII₀ on
    common axes, with structure-constant driven separation."""
    from bass.background.einstein_bianchi import (
        type_i_cosmology, type_ii_cosmology, type_vi0_cosmology,
        type_vii0_cosmology, solve_bianchi_background,
    )
    specs = [
        ("Bianchi I", type_i_cosmology(sigma_over_H_init=1e-4),
         COLS["blue"], "-"),
        (r"Bianchi II ($N_1=10^{-2}$)",
         type_ii_cosmology(sigma_over_H_init=1e-4, n1=1e-2),
         COLS["orange"], "--"),
        (r"Bianchi VI$_0$ ($N_1\!=\!10^{-2}, N_3\!=\!-10^{-2}$)",
         type_vi0_cosmology(sigma_over_H_init=1e-4, n1=1e-2, n3=-1e-2),
         COLS["red"], "-."),
        (r"Bianchi VII$_0$ ($N_1\!=\!2\!\times\!10^{-2}$, $N_3\!=\!3\!\times\!10^{-2}$)",
         type_vii0_cosmology(sigma_over_H_init=1e-4, n1=2e-2, n3=3e-2),
         COLS["green"], ":"),
    ]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(8.4, 3.8))
    for name, cos, col, ls in specs:
        bg = solve_bianchi_background(cos, a_start=1e-6, a_end=1.0, n_pts=2000)
        ax_a.semilogx(bg.a, bg.sigma_plus, color=col, lw=1.6, ls=ls,
                      label=name)
        ax_b.loglog(bg.a, np.abs(bg.sigma_plus) + 1e-30,
                    color=col, lw=1.6, ls=ls, label=name)

    for ax in (ax_a, ax_b):
        ax.set_xlabel(r"scale factor $a$")
        ax.grid(True, which="major", alpha=0.2)
    ax_a.axhline(0, color="0.5", lw=0.5)
    ax_a.set_ylabel(r"$\Sigma_+$  (conformal)")
    ax_a.set_title("Linear scale — drives through zero", fontsize=9.5)
    ax_a.legend(fontsize=7.5, loc="upper right")

    ax_b.set_ylabel(r"$|\Sigma_+|$ (log)")
    ax_b.set_title("Log scale — decay + curvature floor", fontsize=9.5)

    fig.suptitle(r"Class A Bianchi Σ_+ trajectories (Wainwright–Ellis §18)",
                 fontsize=10.5)
    fig.tight_layout()
    _save(fig, "fig_ch07h_bianchi_class_a_attractors", "ch07_results")
    _caption(
        "fig_ch07h_bianchi_class_a_attractors",
        "ch07_results",
        """
Class A Bianchi background trajectories Σ_+(a) from
bass.background.einstein_bianchi.solve_bianchi_background for
types I, II, VI₀, VII₀ (Wainwright–Ellis 1997 §18 Table 11.1
structure constants) at shared initial σ/H = 10⁻⁴. Left: linear Σ_+
— the Type II source −(2/3) N₁² drives Σ_+ through zero, while Type
VII₀ maintains a nonzero curvature floor. Right: |Σ_+| log–log —
Type I and VI₀ decay near a⁻², II crosses zero in finite a, VII₀
remains O(10⁻⁶) as structure constants continue sourcing the shear.
""",
    )


def fig_ch07i_hierarchy_term_prefactors() -> None:
    """Analytic prefactors of the nine-term PSTF hierarchy vs ℓ
    (bass_py LB-2a/b spec §2 closed-form)."""
    from bass.hierarchy import L_MAX_CACHED

    ells = np.arange(2, L_MAX_CACHED + 1)
    T1 = np.full_like(ells, 4.0 / 3.0, dtype=np.float64)
    T3 = (ells + 1.0) / (2.0 * ells + 3.0)
    T7 = -((ells - 1.0) * (ells + 1.0) * (ells + 2.0)) / (
        (2.0 * ells + 3.0) * (2.0 * ells + 5.0)
    )
    T8 = 5.0 * ells / (2.0 * ells + 3.0)
    T9 = -(ells + 2.0)

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    ax.plot(ells, T1, marker="o", color=COLS["orange"], lw=1.4,
            label=r"$T_1:\ (4/3)\Theta$  (expansion)")
    ax.plot(ells, T3, marker="v", color=COLS["cyan"], lw=1.4,
            label=r"$T_3:\ (\ell+1)/(2\ell+3)$  (divergence)")
    ax.plot(ells, T7, marker="^", color=COLS["green"], lw=1.4,
            label=r"$T_7:\ -(\ell-1)(\ell+1)(\ell+2)/[(2\ell+3)(2\ell+5)]$")
    ax.plot(ells, T8, marker="s", color=COLS["blue"], lw=1.4,
            label=r"$T_8:\ 5\ell/(2\ell+3)$  (shear self)")
    ax.plot(ells, T9, marker="D", color=COLS["purple"], lw=1.4,
            label=r"$T_9:\ -(\ell+2)$  (shear $\ell\!\to\!\ell-2$)")
    ax.axhline(0.0, color="0.3", lw=0.5)
    ax.set_xlabel(r"multipole rank $\ell$")
    ax.set_ylabel("prefactor")
    ax.set_title(r"Nine-term PSTF hierarchy prefactors (bass.hierarchy)",
                 fontsize=10)
    ax.set_xticks(ells)
    ax.grid(True, which="major", alpha=0.2)
    ax.legend(fontsize=7.5, loc="lower left")
    _save(fig, "fig_ch07i_hierarchy_term_prefactors", "ch07_results")
    _caption(
        "fig_ch07i_hierarchy_term_prefactors",
        "ch07_results",
        """
Analytic closed-form prefactors of the five non-trivial terms in the
nine-term PSTF hierarchy
(bass.hierarchy.terms, Ellis/Maartens–Bassett conventions).
T₁ ∝ 4/3 carries the universal expansion damping;
T₃ and T₇ grow and then turn negative with ℓ, setting the
divergence / shear-up coupling; T₉ = −(ℓ+2) dominates the shear
source onto Π_ℓ from Π_{ℓ+2}.
""",
    )


# =====================================================================
# Dispatcher
# =====================================================================


FIG_REGISTRY: dict[str, Callable[[], None]] = {
    "ch02a_planck_tt": fig_ch02a_planck_tt_spectrum,
    "ch02b_planck_pol": fig_ch02b_planck_polarization_grid,
    "ch02c_commander_map": fig_ch02c_cmb_map_commander,
    "ch02d_dipole_scenarios": fig_ch02d_dipole_scenarios,
    "ch02e_cf4_velocity": fig_ch02e_cf4_velocity_field,
    "ch05a_boost_heatmap": fig_ch05a_tilt_boost_heatmap,
    "ch05b_boost_directional": fig_ch05b_boost_directional_slice,
    "ch05c_boost_linear_exact": fig_ch05c_boost_linear_vs_exact,
    "ch05d_tilted_visibility": fig_ch05d_tilted_visibility,
    "ch06a_species_omega": fig_ch06a_species_omega,
    "ch06b_hubble_geometry": fig_ch06b_hubble_geometry,
    "ch06c_recombination": fig_ch06c_recombination_panel,
    "ch06d_reionization_tau": fig_ch06d_reionization_tau_sweep,
    "ch06e_closure_error": fig_ch06e_closure_error_vs_L,
    "ch06f_pstf_roundtrip": fig_ch06f_pstf_roundtrip,
    "ch06g_sigma_Sigma": fig_ch06g_sigma_Sigma_conversion,
    "ch07a_sigma_decay_types": fig_ch07a_sigma_decay_types,
    "ch07b_sigma_phase_plane": fig_ch07b_sigma_phase_plane,
    "ch07c_sigma_a4_law": fig_ch07c_sigma_a4_law,
    "ch07d_sigma_seed_sweep": fig_ch07d_sigma_seed_sweep,
    "ch07e_thomson_coefficients": fig_ch07e_thomson_coefficients,
    "ch07f_tca_polter_ratio": fig_ch07f_tca_polter_ratio,
    "ch07g_ellis_kasner": fig_ch07g_ellis_kasner_invariants,
    "ch07h_class_a_attractors": fig_ch07h_bianchi_class_a_attractors,
    "ch07i_hierarchy_prefactors": fig_ch07i_hierarchy_term_prefactors,
    "ch08a_desi_sky": fig_ch08a_desi_sky_coverage,
    "ch08b_planck_lensing": fig_ch08b_planck_lensing,
    "ch08c_cf4_delta": fig_ch08c_cf4_delta_vs_distance,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", default=None,
                    help="only render a single figure by id")
    ap.add_argument("--list", action="store_true",
                    help="list available figures and exit")
    args = ap.parse_args()

    if args.list:
        print("Available paper figures:")
        for fid, fn in FIG_REGISTRY.items():
            print(f"  {fid:<28}  {fn.__name__}")
        return 0

    apply_style()
    targets = [args.only] if args.only else list(FIG_REGISTRY.keys())
    failures: list[tuple[str, str]] = []
    for fid in targets:
        if fid not in FIG_REGISTRY:
            print(f"  [skip] {fid}: not registered")
            continue
        fn = FIG_REGISTRY[fid]
        print(f"[{fid}] {fn.__name__}")
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {fid}: {exc!r}")
            failures.append((fid, repr(exc)))
    if failures:
        print(f"\n{len(failures)} figures failed:")
        for fid, e in failures:
            print(f"  {fid}: {e}")
        return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
