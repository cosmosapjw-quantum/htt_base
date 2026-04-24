#!/usr/bin/env python3
"""make_parallel_track_figures.py — BASS-independent figure gallery.

Generates every figure that can be produced *without* the BASS forward
solver: pure-algebra physics (three-bound hierarchy, tilted-FLRW
observables, Colin-β translation, MES scenario envelope), MIO coherence
diagnostics on the 5-probe SSOT, and real-observational plots backed by
``workdir/obs_bundle/`` (Planck PR3 power spectra, SMICA/Commander maps,
CF4 β variants, dipole-direction comparison).

Output: ``figures/parallel_track/`` — 10 PNG files + 1 combined contact
sheet. Wong 2011 colourblind palette, 300 DPI.

Run:
    venv/bin/python scripts/make_parallel_track_figures.py
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np

# ─── Path wiring — makes htt/, htt/src/, workdir/obs_bundle/ importable.
from figure_env import (
    OBS_BUNDLE_ROOT,
    REPO_ROOT,
    configure_repo_paths,
)

configure_repo_paths()

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

# Wong 2011 colourblind-safe palette (matches htt.core.plot_style).
WONG = {
    "blue":    "#0072B2",
    "orange":  "#E69F00",
    "green":   "#009E73",
    "red":     "#D55E00",
    "purple":  "#CC79A7",
    "yellow":  "#F0E442",
    "cyan":    "#56B4E9",
    "black":   "#000000",
    "grey":    "#888888",
}


# ─── Global rcParams ──────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":        "DejaVu Sans",
    "font.size":          9,
    "axes.titlesize":     10,
    "axes.labelsize":     10,
    "axes.grid":          True,
    "grid.alpha":         0.25,
    "grid.linestyle":     ":",
    "legend.frameon":     False,
    "legend.fontsize":    8,
    "xtick.direction":    "in",
    "ytick.direction":    "in",
    "xtick.top":          True,
    "ytick.right":        True,
    "savefig.dpi":        300,
    "savefig.bbox":       "tight",
    "figure.dpi":         120,
})


OUT_DIR = REPO_ROOT / "figures" / "parallel_track"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════
# Part A — Algebra-only (no external data)
# ═══════════════════════════════════════════════════════════════════════

def fig_01_mes_three_bounds() -> None:
    """B_σ > B_ω > B_u̇ as functions of ε₁ — Tier-C anchored."""
    from htt.core.bounds import B_accel, B_omega, B_sigma, B_sigma_corrected
    from htt.core.ssot import C

    e1 = np.logspace(-5, -1.5, 500)
    Bs  = np.array([B_sigma(e) for e in e1])
    Bw  = np.array([B_omega(e) for e in e1])
    Ba  = np.array([B_accel(e) for e in e1])
    Bsc = np.array([B_sigma_corrected(e) for e in e1])

    # Canonical scenarios
    scenarios = [
        ("S1",  1.233e-3, "o", WONG["blue"]),
        ("S2a", 1.476e-3, "s", WONG["orange"]),
        ("S2c", 3.296e-3, "^", WONG["red"]),
    ]

    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.plot(e1, Bs,  color=WONG["blue"],   lw=1.8, ls="-",  label=r"$B_\sigma$ (shear)")
    ax.plot(e1, Bw,  color=WONG["orange"], lw=1.8, ls="--", label=r"$B_\omega$ (vorticity)")
    ax.plot(e1, Ba,  color=WONG["red"],    lw=1.4, ls=(0, (4, 2, 1, 2)), label=r"$B_{\dot u}$ (acceleration)")
    ax.plot(e1, Bsc, color=WONG["grey"],   lw=1.0, ls=":",  label=r"$B_\sigma^{\rm corr}$ (VT-07)")

    for name, e1_s, m, c in scenarios:
        ax.plot(e1_s, B_sigma(e1_s), marker=m, color=c, ms=7, mec="black",
                mew=0.5, zorder=5, label=name)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Dipole amplitude $\varepsilon_1$ ($\Delta T/T$)")
    ax.set_ylabel(r"Upper bound")
    ax.set_title("MES three-bound hierarchy — CLAUDE.md §5 anchor")
    ax.legend(loc="upper left", ncol=2)
    fig.text(0.99, 0.01, f"T_CMB = {C.T0_K} K (Fixsen 2009)", ha="right",
             va="bottom", fontsize=7, color=WONG["grey"])
    _save(fig, "fig_01_mes_three_bounds.png")


def fig_02_tilted_flrw_dictionary() -> None:
    """Tilted-FLRW observables vs β (D26 anchor)."""
    from htt.core.tilted_flrw import (
        Delta_q, Omega_tilt, matter_acceleration, matter_vorticity,
        peculiar_jeans, q_matter, tilted_H_ratio, velocity_growth,
    )

    beta = np.logspace(-5, -2, 200)

    H_ratio        = np.array([tilted_H_ratio(b) for b in beta])
    Delta_q_100    = np.array([Delta_q(b, 100.0) for b in beta])
    omega_tilt     = np.array([Omega_tilt(b) for b in beta])
    mat_vor        = np.array([float(matter_vorticity(b, 1e-8)) for b in beta])
    mat_acc        = np.array([float(matter_acceleration(b)) for b in beta])
    vel_grow       = np.array([velocity_growth(0.1, b, model="GR_min") for b in beta])

    lam_pairs      = [peculiar_jeans(b, q_matter()) for b in beta]
    lam_J          = np.array([p[0] for p in lam_pairs])
    f_J            = np.array([p[1] for p in lam_pairs])

    BETA_ANCHOR = 1.360e-3

    fig, axes = plt.subplots(2, 3, figsize=(11.0, 6.0))

    def _panel(ax, y, ylabel, title, **kw):
        ax.plot(beta, y, color=WONG["blue"], lw=1.6, **kw)
        ax.axvline(BETA_ANCHOR, color=WONG["red"], ls=":", lw=1.0,
                   label=r"$\beta_{\rm anchor} = 1.36\times10^{-3}$")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel(r"$\beta$")
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=9)

    _panel(axes[0, 0], H_ratio - 1,   r"$H_{\rm tilt}/H - 1$",    "Hubble-rate tilt")
    _panel(axes[0, 1], Delta_q_100,    r"$\Delta q$ (100 Mpc)",    "Deceleration offset")
    _panel(axes[0, 2], omega_tilt,     r"$\Omega_{\rm tilt}$",     "Tilt density fraction")
    _panel(axes[1, 0], mat_vor,        r"$|\omega_{\rm matter}|$", r"Matter vorticity ($\Sigma^2=10^{-8}$)")
    _panel(axes[1, 1], mat_acc,        r"$|\dot u|$",              "Matter acceleration")
    _panel(axes[1, 2], vel_grow,       r"$v_{\rm grow}$ (z=0.1)", "Velocity growth (GR min)")

    axes[0, 0].legend(loc="upper left")
    fig.suptitle("Tilted-FLRW observables dictionary (D26) — pinned 2026-04-24",
                 fontsize=11, y=1.02)
    _save(fig, "fig_02_tilted_flrw_dictionary.png")


def fig_03_colin_beta_translation() -> None:
    """β_SNe(z) from Colin-Tsagas translation; CF4 band overlay."""
    from htt.core.tilted_flrw import beta_from_colin

    z_grid = np.linspace(0.01, 0.20, 200)
    beta_sne = np.array([beta_from_colin(z) for z in z_grid])

    # CF4 canonical: 1.334e-3 ± 0.267e-3 (ObsData default used in evidence_models)
    beta_cf4 = 1.334e-3
    sigma_cf4 = 0.267e-3

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(z_grid, beta_sne, color=WONG["blue"], lw=2.0,
            label=r"$\beta_{\rm SNe}(z)$ = Colin $\to$ Tsagas")
    ax.axhline(beta_cf4, color=WONG["orange"], lw=1.5, ls="-",
               label=fr"CF4: $\beta = {beta_cf4*1e3:.3f} \times 10^{{-3}}$")
    ax.fill_between(z_grid, beta_cf4 - sigma_cf4, beta_cf4 + sigma_cf4,
                    color=WONG["orange"], alpha=0.15, label=r"CF4 $\pm 1\sigma$")
    ax.fill_between(z_grid, beta_cf4 - 5*sigma_cf4, beta_cf4 + 5*sigma_cf4,
                    color=WONG["orange"], alpha=0.05, label=r"CF4 $\pm 5\sigma$")

    # Mark the three Colin reference z values pinned in the test
    for z_ref, beta_pin in [(0.03, 6.21e-4), (0.05, 1.340e-3), (0.10, 1.590e-3)]:
        ax.plot(z_ref, beta_pin, "o", ms=8, color=WONG["red"], mec="black",
                mew=0.5, zorder=5)
        ax.annotate(f"z={z_ref:.2f}", (z_ref, beta_pin), xytext=(5, 5),
                    textcoords="offset points", fontsize=8)

    ax.set_xlabel(r"Reference redshift $z_{\rm ref}$")
    ax.set_ylabel(r"$\beta_{\rm SNe}$")
    ax.set_title("Colin+2019 dipolar-$q$ $\\to$ $\\beta$ translation (D27 anchor)")
    ax.set_yscale("log")
    ax.set_ylim(1e-4, 3e-3)
    ax.legend(loc="lower right", fontsize=8)
    _save(fig, "fig_03_colin_beta_translation.png")


def fig_04_flrw_tilt_posterior() -> None:
    """FLRW_tilt β posterior from log_evidence_quadrature (lnB=26.40 anchor)."""
    from htt.core.evidence_models import FLRW, FLRW_tilt

    result = FLRW_tilt().log_evidence_quadrature(n_points=10000)
    betas = result["betas"]
    post = result["posterior"]

    lnZ_flrw = FLRW().log_evidence()
    lnB = result["lnZ"] - lnZ_flrw
    beta_mean = result["beta_mean"]
    beta_mode = result["beta_mode"]
    beta_lo, beta_hi = result["beta_68CI"]

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(betas, post, color=WONG["blue"], lw=1.8, label="posterior")
    ax.axvline(beta_mean, color=WONG["red"], ls="--", lw=1.4,
               label=fr"$\langle\beta\rangle = {beta_mean*1e3:.4f}\times10^{{-3}}$")
    ax.axvline(beta_mode, color=WONG["orange"], ls=":", lw=1.0,
               label=fr"mode = {beta_mode*1e3:.4f}$\times10^{{-3}}$")
    ax.axvspan(beta_lo, beta_hi, color=WONG["blue"], alpha=0.15,
               label=r"68% CI")

    # Overlay CF4 reference
    ax.axvline(1.334e-3, color=WONG["green"], ls="-.", lw=1.0, label=r"CF4 $\beta$")

    ax.set_xscale("log")
    ax.set_xlabel(r"$\beta$ (tilt rapidity)")
    ax.set_ylabel(r"posterior density (normalised)")
    ax.set_title(
        f"FLRW_tilt posterior — $\\ln B = {lnB:.2f}$ (CLAUDE.md §5: +26.40)",
        fontsize=10,
    )
    ax.legend(loc="upper left", fontsize=8)
    _save(fig, "fig_04_flrw_tilt_posterior.png")


def fig_05_filling_fraction_scenarios() -> None:
    """F_Bayes posteriors per scenario (CLAUDE.md §5: 0.093 ± 0.025)."""
    from htt.core.analysis_extended import FillingFraction

    ff = FillingFraction()
    scenarios = ["S1", "S2a", "S2b", "S2c", "S3"]
    colours = [WONG["blue"], WONG["orange"], WONG["green"], WONG["red"], WONG["purple"]]

    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    for scn, col in zip(scenarios, colours):
        F_samp, med, q16, q84, _, _ = ff.mc_posterior(
            scenario=scn, N=100_000, seed=42,
        )
        # histogram
        ax.hist(F_samp, bins=80, density=True, histtype="stepfilled",
                alpha=0.25, color=col)
        ax.hist(F_samp, bins=80, density=True, histtype="step",
                color=col, lw=1.5, label=f"{scn}: med={med:.3f}")

    # CLAUDE.md §5 anchor band
    ax.axvspan(0.093 - 0.025, 0.093 + 0.025, color=WONG["grey"], alpha=0.15,
               label="CLAUDE.md §5: 0.093 ± 0.025")
    ax.axvline(0.093, color=WONG["black"], ls=":", lw=1.0)

    ax.set_xlabel(r"$\mathcal{F} = x_V / x_{\rm max}$")
    ax.set_ylabel(r"posterior density")
    ax.set_title("Filling-fraction posteriors across scenarios (D5 anchor)")
    ax.set_xlim(0.0, 0.8)
    ax.legend(fontsize=8)
    _save(fig, "fig_05_filling_fraction_scenarios.png")


def fig_06_directional_probes_mollweide() -> None:
    """5-probe STANDARD_PROBES sky map (Mollweide, Galactic)."""
    from mio.coherence.directional import (
        STANDARD_PROBES,
        coherence_chi2,
        resultant_vector,
    )

    fig = plt.figure(figsize=(9.0, 5.2))
    ax = fig.add_subplot(111, projection="mollweide")

    # Galactic l,b → Mollweide longitude (−π, π), latitude (−π/2, π/2).
    # Galactic l ∈ [0, 360); wrap to [-π, π].
    def _to_radians(l_deg, b_deg):
        lon = np.radians(np.where(l_deg > 180.0, l_deg - 360.0, l_deg))
        lat = np.radians(b_deg)
        return lon, lat

    # 5 probes
    colours = [WONG["blue"], WONG["orange"], WONG["green"], WONG["red"], WONG["purple"]]
    for p, col in zip(STANDARD_PROBES, colours):
        lon, lat = _to_radians(p.l_deg, p.b_deg)
        # error cone approximated as a disk (small σ → point)
        sigma_rad = np.radians(p.sigma_cone_deg)
        theta = np.linspace(0, 2 * np.pi, 64)
        # tangent-plane circle (small-angle approx near point)
        ring_lon = lon + sigma_rad * np.cos(theta) / max(np.cos(lat), 1e-6)
        ring_lat = lat + sigma_rad * np.sin(theta)
        ax.plot(ring_lon, ring_lat, color=col, lw=0.8, alpha=0.5)
        ax.plot(lon, lat, "o", ms=8, color=col, mec="black", mew=0.5,
                label=f"{p.name} (σ={p.sigma_cone_deg:.1f}°)")

    # Resultant axis
    l_best, b_best, R = resultant_vector(STANDARD_PROBES)
    chi2, dof = coherence_chi2(STANDARD_PROBES)
    lon_r, lat_r = _to_radians(l_best, b_best)
    ax.plot(lon_r, lat_r, "*", ms=20, color=WONG["black"], mec="white",
            mew=0.8, label=f"Resultant $R={R:.3f}$", zorder=10)

    ax.set_title(
        f"Directional probes — $\\chi^2={chi2:.2f}/{dof}$ dof, "
        f"fit axis $(l, b)=({l_best:.1f}°, {b_best:.1f}°)$",
        fontsize=10,
    )
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=7)
    _save(fig, "fig_06_directional_probes_mollweide.png")


# ═══════════════════════════════════════════════════════════════════════
# Part B — Observational data from workdir/obs_bundle/
# ═══════════════════════════════════════════════════════════════════════

def _load_obs() -> Any:
    """Lazy-import the obs_loader from workdir/."""
    from obs_loader import ObsCatalog  # type: ignore[import-not-found]

    return ObsCatalog(str(OBS_BUNDLE_ROOT))


def fig_07_planck_pr3_tt() -> None:
    """Planck PR3 TT power spectrum (unbinned + binned + best-fit)."""
    cat = _load_obs()

    tt_full = cat.load("planck.pr3.tt_full")
    tt_bin  = cat.load("planck.pr3.tt_binned")
    bestfit = cat.load("planck.pr3.bestfit")

    fig, ax = plt.subplots(figsize=(8.5, 4.5))

    # Unbinned full (light grey ribbon)
    ax.errorbar(tt_full.ell, tt_full.dl,
                yerr=[tt_full.err_lo, tt_full.err_hi],
                fmt="o", ms=1.0, color=WONG["grey"], alpha=0.35,
                elinewidth=0.3, label="PR3 TT (unbinned)")

    # Binned (blue markers)
    ax.errorbar(tt_bin.ell, tt_bin.dl,
                yerr=[tt_bin.err_lo, tt_bin.err_hi],
                fmt="s", ms=3.5, color=WONG["blue"], mec="black", mew=0.3,
                elinewidth=0.8, capsize=2, label="PR3 TT (binned)")

    # Best-fit
    ax.plot(bestfit.ell, bestfit.dl_TT, color=WONG["red"], lw=1.2,
            label="Planck 2018 best-fit (ΛCDM)")

    ax.set_xlim(2, 2500)
    ax.set_xscale("log")
    ax.set_xlabel(r"Multipole $\ell$")
    ax.set_ylabel(r"$\mathcal{D}_\ell^{TT}$ [$\mu$K$^2$]")
    ax.set_title("Planck PR3 TT power spectrum (workdir/obs_bundle/)")
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "fig_07_planck_pr3_tt.png")


def fig_08_planck_pr3_tt_te_ee() -> None:
    """TT / TE / EE overview with best-fit ΛCDM theory."""
    cat = _load_obs()

    tt = cat.load("planck.pr3.tt_full")
    te = cat.load("planck.pr3.te_full")
    ee = cat.load("planck.pr3.ee_full")
    bf = cat.load("planck.pr3.bestfit")

    fig, axes = plt.subplots(3, 1, figsize=(8.5, 8.0), sharex=True)

    panels = [
        (axes[0], tt, bf.dl_TT, "TT",  WONG["blue"]),
        (axes[1], te, bf.dl_TE, "TE",  WONG["orange"]),
        (axes[2], ee, bf.dl_EE, "EE",  WONG["green"]),
    ]
    for ax, data, theory_cl, label, col in panels:
        ax.errorbar(data.ell, data.dl,
                    yerr=[data.err_lo, data.err_hi],
                    fmt="o", ms=1.4, color=col, alpha=0.5, elinewidth=0.3,
                    label=f"PR3 {label}")
        ax.plot(bf.ell, theory_cl, color=WONG["red"], lw=1.0, label="best-fit")
        ax.set_ylabel(fr"$\mathcal{{D}}_\ell^{{{label}}}$ [$\mu$K$^2$]")
        ax.legend(loc="upper right", fontsize=8)
        ax.set_xscale("log")

    axes[2].set_xlabel(r"Multipole $\ell$")
    axes[2].set_xlim(2, 2500)
    axes[0].set_title("Planck PR3 CMB power spectra (TT / TE / EE)", fontsize=10)
    _save(fig, "fig_08_planck_pr3_tt_te_ee.png")


def fig_09_planck_lowell_envelope() -> None:
    """Low-ℓ TT envelope with scenario D_2, D_3 anchors (Planck PR3 vs MES bounds)."""
    cat = _load_obs()
    tt = cat.load("planck.pr3.tt_full")

    mask = tt.ell <= 40
    ell = tt.ell[mask]
    dl  = tt.dl[mask]
    lo  = tt.err_lo[mask]
    hi  = tt.err_hi[mask]

    # Evidence_models reference values (ObsData + R03a LCDM).
    from htt.core.evidence_models_R03a import D2_LCDM, D3_LCDM

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.errorbar(ell, dl, yerr=[lo, hi], fmt="o", ms=5, color=WONG["blue"],
                mec="black", mew=0.3, elinewidth=0.7, capsize=2,
                label="Planck PR3")

    # D₂ and D₃ ΛCDM anchors
    ax.plot(2, D2_LCDM, "*", ms=18, color=WONG["red"], mec="black", mew=0.5,
            label=fr"$D_2^{{\Lambda CDM}} = {D2_LCDM}$ $\mu$K$^2$", zorder=5)
    ax.plot(3, D3_LCDM, "*", ms=18, color=WONG["orange"], mec="black", mew=0.5,
            label=fr"$D_3^{{\Lambda CDM}} = {D3_LCDM}$ $\mu$K$^2$", zorder=5)

    ax.set_xlim(0, 40)
    ax.set_ylim(0, 3500)
    ax.set_xlabel(r"Multipole $\ell$")
    ax.set_ylabel(r"$\mathcal{D}_\ell^{TT}$ [$\mu$K$^2$]")
    ax.set_title("Planck PR3 low-$\\ell$ TT vs LCDM $D_2$ / $D_3$ anchors")
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "fig_09_planck_lowell_envelope.png")


def fig_10_cf4_beta_variants() -> None:
    """CF4 β across catalogue generations — reads whichever obs_defaults
    files are materialised in the bundle, falling back to literature values.
    """
    import json as _json

    # The shipped obs_bundle/scalars contains only dipole_scalar_observations.json
    # (canonical) in this deployment. Supplement with literature values from
    # the research plan (§9.2) for the Watkins2023 / Courtois2025 variants.
    scalars_dir = OBS_BUNDLE_ROOT / "scalars"
    fallback_dir = REPO_ROOT / "htt" / "workspace" / "data"

    def _load_json(name: str) -> dict:
        for base in (scalars_dir, fallback_dir):
            path = base / name
            if path.exists():
                return _json.loads(path.read_text())
        return {}

    canonical = _load_json("dipole_scalar_observations.json") or \
                _load_json("obs_defaults.json")

    def _extract_cf4_beta(payload: dict) -> tuple[float, float]:
        beta = payload.get("beta")
        sigma = payload.get("beta_sigma")
        if beta is None:
            dip = payload.get("dipole_observations", {}) or {}
            for k, v in dip.items():
                if "cf4" in k.lower() and isinstance(v, dict) and "beta" in v:
                    beta = v.get("beta", beta)
                    sigma = v.get("sigma", sigma)
                    break
        return float(beta or 0.0), float(sigma or 0.0002)

    beta_canon, sigma_canon = _extract_cf4_beta(canonical)

    # Literature values from INDEX.json + research plan §9.2
    data = [
        ("canonical (Watkins2009)",   WONG["blue"],   beta_canon,  sigma_canon),
        ("Watkins2023 CF4 MVE",        WONG["orange"], 0.001318,    9.7e-05),
        ("Courtois2025 CF4++ HMC",     WONG["red"],    0.001051,    1.33e-4),
    ]

    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    y = np.arange(len(data))
    for i, (name, col, beta, sig) in enumerate(data):
        ax.errorbar(beta, y[i], xerr=sig, fmt="o", ms=8, color=col,
                    mec="black", mew=0.4, elinewidth=1.5, capsize=3)
        ax.annotate(f"β = ({beta*1e3:.3f}±{sig*1e3:.3f})×10⁻³",
                    (beta, y[i]), xytext=(10, 0), textcoords="offset points",
                    fontsize=8, va="center")

    # Also overlay the FLRW_tilt posterior mean as a vertical line
    from htt.core.evidence_models import FLRW_tilt
    beta_mean = FLRW_tilt().log_evidence_quadrature(n_points=10000)["beta_mean"]
    ax.axvline(beta_mean, color=WONG["purple"], ls="--", lw=1.4,
               label=fr"FLRW_tilt posterior $\langle\beta\rangle = {beta_mean*1e3:.3f}\times10^{{-3}}$")

    ax.set_yticks(y)
    ax.set_yticklabels([d[0] for d in data])
    ax.set_xlabel(r"Tilt rapidity $\beta$")
    ax.set_xlim(8e-4, 1.6e-3)
    ax.set_title("CF4 β across catalogue generations vs FLRW_tilt posterior")
    ax.legend(loc="lower right", fontsize=8)
    ax.invert_yaxis()
    _save(fig, "fig_10_cf4_beta_variants.png")


def fig_11_dipole_direction_comparison() -> None:
    """Dipole-direction comparison on the sky (CMB / CatWISE / Radio / CF4)."""
    import json as _json
    cat = _load_obs()
    scalars = cat.load("dipole_scalar_observations.consolidated")
    dip = scalars["dipole_observations"]

    probes = []
    for key, entry in dip.items():
        if not isinstance(entry, dict):
            continue
        if "l_deg" not in entry:
            continue
        probes.append((
            key.replace("_", " "),
            float(entry["l_deg"]),
            float(entry["b_deg"]),
            float(entry.get("sigma_stat", 2.0)),
        ))

    fig = plt.figure(figsize=(9.0, 5.2))
    ax = fig.add_subplot(111, projection="mollweide")

    colours = [WONG["blue"], WONG["orange"], WONG["green"], WONG["red"],
               WONG["purple"], WONG["cyan"]]

    def _to_rad(l_deg, b_deg):
        lon = np.radians(l_deg - 360.0 if l_deg > 180.0 else l_deg)
        lat = np.radians(b_deg)
        return lon, lat

    for (name, l, b, sig), col in zip(probes, colours):
        lon, lat = _to_rad(l, b)
        # sig is dimensionless ε₁ here — convert to a nominal cone of 3° for display
        ax.plot(lon, lat, "o", ms=10, color=col, mec="black", mew=0.5,
                label=f"{name} ({l:.0f}°, {b:.0f}°)")

    ax.set_title(
        "Dipole-direction literature compilation (workdir/obs_bundle/)",
        fontsize=10,
    )
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=3, fontsize=7)
    _save(fig, "fig_11_dipole_direction_comparison.png")


def fig_12_act_dr4_planck_combined() -> None:
    """Planck PR3 + ACT DR4 TT overview (ACT DR6 unavailable in this bundle)."""
    cat = _load_obs()
    pl_bin = cat.load("planck.pr3.tt_binned")

    # ACT DR4 compact: CMB-only TT at keys
    #   clcmb__act_dr4_01_D_ell_TT_cmbonly_txt  shape (40, 3) = (ell, D_ell, sigma)
    act_compact = cat.load("act.dr4.compact")
    act_tt = np.asarray(act_compact["clcmb__act_dr4_01_D_ell_TT_cmbonly_txt"])
    act_ell = act_tt[:, 0]
    act_dl  = act_tt[:, 1]
    act_err = act_tt[:, 2]

    fig, ax = plt.subplots(figsize=(9.0, 4.5))
    ax.errorbar(pl_bin.ell, pl_bin.dl,
                yerr=[pl_bin.err_lo, pl_bin.err_hi],
                fmt="s", ms=4, color=WONG["blue"], mec="black", mew=0.3,
                elinewidth=0.8, capsize=2, label="Planck PR3 TT (binned)")
    ax.errorbar(act_ell, act_dl, yerr=act_err,
                fmt="^", ms=4, color=WONG["red"], mec="black", mew=0.3,
                elinewidth=0.8, capsize=2, label="ACT DR4 TT (cmb-only)")

    ax.set_xscale("log")
    ax.set_xlim(30, 5000)
    ax.set_xlabel(r"Multipole $\ell$")
    ax.set_ylabel(r"$\mathcal{D}_\ell^{TT}$ [$\mu$K$^2$]")
    ax.set_title("Planck PR3 + ACT DR4 TT overview (high-$\\ell$ extension)")
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "fig_12_planck_act_dr4_combined.png")


# ═══════════════════════════════════════════════════════════════════════
# Dispatch
# ═══════════════════════════════════════════════════════════════════════

def _save(fig, name: str) -> None:
    path = OUT_DIR / name
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path.relative_to(REPO_ROOT)}")


_ALL_FIGS = [
    ("fig_01_mes_three_bounds",            fig_01_mes_three_bounds),
    ("fig_02_tilted_flrw_dictionary",      fig_02_tilted_flrw_dictionary),
    ("fig_03_colin_beta_translation",      fig_03_colin_beta_translation),
    ("fig_04_flrw_tilt_posterior",         fig_04_flrw_tilt_posterior),
    ("fig_05_filling_fraction_scenarios",  fig_05_filling_fraction_scenarios),
    ("fig_06_directional_probes_mollweide", fig_06_directional_probes_mollweide),
    ("fig_07_planck_pr3_tt",               fig_07_planck_pr3_tt),
    ("fig_08_planck_pr3_tt_te_ee",         fig_08_planck_pr3_tt_te_ee),
    ("fig_09_planck_lowell_envelope",      fig_09_planck_lowell_envelope),
    ("fig_10_cf4_beta_variants",           fig_10_cf4_beta_variants),
    ("fig_11_dipole_direction_comparison", fig_11_dipole_direction_comparison),
    ("fig_12_planck_act_dr4_combined",     fig_12_act_dr4_planck_combined),
]


def main() -> None:
    print(f"Writing parallel-track figures to {OUT_DIR.relative_to(REPO_ROOT)}")
    failures: list[tuple[str, str]] = []
    for name, fn in _ALL_FIGS:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures.append((name, f"{type(exc).__name__}: {exc}"))
            print(f"  FAILED {name}: {exc}")
    print(f"\nDone. {len(_ALL_FIGS) - len(failures)}/{len(_ALL_FIGS)} succeeded.")
    if failures:
        print("Failures:")
        for name, msg in failures:
            print(f"  {name}: {msg}")


if __name__ == "__main__":
    main()
