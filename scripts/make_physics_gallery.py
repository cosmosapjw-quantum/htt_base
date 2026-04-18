#!/usr/bin/env python3
"""make_physics_gallery.py — self-contained physics plot gallery.

Generates a structured directory of PNG plots covering every physical
quantity bass_py can currently produce at the post-LB-1 baseline
(species backgrounds, FLRW geometry, recombination / reionization via
HyRec fixture + tanh, Bianchi shear decay via Y-Block, tilt-boost
kinematics, Friedmann closure, and parameter sweeps).

Usage
-----
    venv/bin/python scripts/make_physics_gallery.py
    venv/bin/python scripts/make_physics_gallery.py --only 03_recombination
    venv/bin/python scripts/make_physics_gallery.py --list

All plots write to ``plots/physics_gallery/{topic}/`` with a top-level
``README.md`` index. No external cosmology code is imported (the LB-0
external-code policy applies to production code under ``bass_py/``;
this script uses only matplotlib, numpy, scipy, and bass_py itself).
"""
from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
GALLERY_ROOT = REPO_ROOT / "plots" / "physics_gallery"

# Make `bass.*` importable for the LB-1 species machinery.
sys.path.insert(0, str(REPO_ROOT / "bass_py"))

from bass.background.einstein_bianchi import (  # noqa: E402
    BianchiCosmology,
    solve_bianchi_background,
)
from bass.background.bianchi_types import (  # noqa: E402
    flrw_constants,
    type_i_constants,
    type_v_constants,
    type_vii0_constants,
)
from bass.recombination.recombination_ingest import (  # noqa: E402
    build_interpolators,
    load_recombination_table,
)
from bass.recombination.reionization import (  # noqa: E402
    ReionizationParameters,
    cosmology_from_metadata,
    extend_table_with_reionization,
    compute_reionization_tau,
)
from bass.species import (  # noqa: E402
    SpeciesBackgroundRegistry,
    SpeciesConstants,
    build_flrw_background_table,
    default_constants,
)
from bass.species.background_table import FLRWBackgroundTable  # noqa: E402
from bass.species.baryon import BaryonBackground  # noqa: E402
from bass.species.cdm import CDMBackground  # noqa: E402
from bass.species.lambda_ import LambdaBackground  # noqa: E402
from bass.species.neutrino import NeutrinoBackground  # noqa: E402
from bass.species.photon import PhotonBackground  # noqa: E402
from bass.hierarchy import (  # noqa: E402
    L_MAX_CACHED,
    T1_expansion,
    T3_divergence,
    T7_shear_up,  # stub — prefactor reference only
    T8_shear_same,
    T9_shear_down,
    stf_basis,
    sym_trace_free,
    pstf_pack,
    pstf_unpack,
    verify_pstf_invariants,
    zero_nabla_operator,
)
from bass.background.tetrad_state import axisymmetric_sigma_tensor  # noqa: E402
from htt.htt.core.plot_style import COLS, apply_style  # noqa: E402


# ════════════════════════════════════════════════════════════════════
# Shared style and helpers
# ════════════════════════════════════════════════════════════════════


SPECIES_COLOR = {
    "photon":   COLS["orange"],
    "neutrino": COLS["cyan"],
    "baryon":   COLS["blue"],
    "cdm":      COLS["purple"],
    "lambda":   COLS["green"],
}
SPECIES_LABEL = {
    "photon":   r"$\gamma$ (photon)",
    "neutrino": r"$\nu$ (neutrino)",
    "baryon":   r"$b$ (baryon)",
    "cdm":      r"$c$ (CDM)",
    "lambda":   r"$\Lambda$",
}
SPECIES_LS = {
    "photon":   "-",
    "neutrino": "--",
    "baryon":   "-",
    "cdm":      "-",
    "lambda":   ":",
}


def _save(fig: plt.Figure, name: str, topic: str) -> Path:
    """Save figure under plots/physics_gallery/{topic}/{name}.png."""
    out = GALLERY_ROOT / topic
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"  [ok] {topic}/{name}.png")
    return path


def _prepare_axes(ax, xlabel: str, ylabel: str,
                   title: str = "", xlog: bool = False,
                   ylog: bool = False) -> None:
    if xlog:
        ax.set_xscale("log")
    if ylog:
        ax.set_yscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=10)
    ax.grid(True, which="both", alpha=0.25, lw=0.5)


def _hyrec_fixture_path() -> Path:
    return (
        REPO_ROOT / "bass_py" / "bass" / "recombination" / "fixtures"
        / "recombination_ref_planck2018.csv"
    )


# ════════════════════════════════════════════════════════════════════
# Shared expensive objects (built once per script run)
# ════════════════════════════════════════════════════════════════════


class Shared:
    """Lazy singletons to avoid rebuilding on every plot function."""

    _bg: FLRWBackgroundTable = None
    _registry: SpeciesBackgroundRegistry = None
    _recomb = None
    _recomb_reion = None

    @classmethod
    def bg(cls) -> FLRWBackgroundTable:
        if cls._bg is None:
            cls._bg = build_flrw_background_table()
        return cls._bg

    @classmethod
    def registry(cls) -> SpeciesBackgroundRegistry:
        if cls._registry is None:
            cls._registry = SpeciesBackgroundRegistry.from_planck2018(
                bg_table=cls.bg(),
            )
        return cls._registry

    @classmethod
    def recomb(cls):
        if cls._recomb is None:
            table = load_recombination_table(_hyrec_fixture_path())
            cls._recomb = (table, build_interpolators(table))
        return cls._recomb

    @classmethod
    def recomb_reion(cls, reion: ReionizationParameters = None):
        reion = reion or ReionizationParameters()
        key = (reion.z_reion_H, reion.delta_z_H, reion.include_HeII,
                reion.z_reion_HeII, reion.delta_z_HeII)
        if cls._recomb_reion is None or cls._recomb_reion[0] != key:
            table, _ = cls.recomb()
            cosmo = cosmology_from_metadata(table.metadata)
            ext = extend_table_with_reionization(table, reion, cosmology=cosmo)
            cls._recomb_reion = (key, ext, build_interpolators(ext), cosmo)
        return cls._recomb_reion[1:]  # (ext_table, interp, cosmo)


# ════════════════════════════════════════════════════════════════════
# Topic 01 — Species background
# ════════════════════════════════════════════════════════════════════


TOPIC_01 = "01_species_background"


def plot_01_omega_evolution_log() -> None:
    """Ω_s(z) = ρ_s(z) / ρ_crit,0 across the full radiation-to-Λ range.

    x-range clipped at (1+z) = 10⁶ (early radiation era, pre-BBN) and
    y-range extended to 10²⁵ so the radiation branch has its full
    24-decade rise visible instead of piling into the upper-left
    corner of the panel.
    """
    bg = Shared.bg()
    reg = Shared.registry()
    z_grid = np.geomspace(1e-3, 1e6, 500)
    a_grid = 1.0 / (1.0 + z_grid)
    eta_grid = np.array([bg.eta_at_a(a) for a in a_grid])

    from bass.species.base import CANONICAL_ORDER, SpeciesLabel
    key_map = {
        SpeciesLabel.PHOTON: "photon",
        SpeciesLabel.NEUTRINO: "neutrino",
        SpeciesLabel.BARYON: "baryon",
        SpeciesLabel.CDM: "cdm",
        SpeciesLabel.LAMBDA: "lambda",
    }

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    for lab in CANONICAL_ORDER:
        rho = np.asarray(reg[lab].rho_rest(eta_grid))
        key = key_map[lab]
        ax.plot(1 + z_grid, rho,
                color=SPECIES_COLOR[key], ls=SPECIES_LS[key], lw=1.6,
                label=SPECIES_LABEL[key])

    c = reg.constants
    z_eq = c.Omega_m_0 / c.Omega_r_0 - 1.0
    ax.axvline(1 + z_eq, color="0.3", ls=":", lw=0.8)
    ax.text(1 + z_eq, 1e-2, f" $z_{{\\rm eq}} \\approx {z_eq:.0f}$",
             rotation=90, va="center", ha="left", fontsize=9, color="0.3")

    # Era-shading for orientation.
    ax.axvspan(1 + 3400, 1e6, alpha=0.05, color=COLS["orange"])
    ax.axvspan(2, 1 + 3400, alpha=0.05, color=COLS["blue"])
    ax.axvspan(1, 2, alpha=0.05, color=COLS["green"])
    ax.text(5e4, 5e-9, "radiation", color="0.4", fontsize=8,
             ha="center")
    ax.text(40, 5e-9, "matter", color="0.4", fontsize=8, ha="center")
    ax.text(1.2, 5e-9, "Λ", color="0.4", fontsize=8, ha="left")

    _prepare_axes(ax, r"$1 + z$",
                   r"$\Omega_s(z) = \rho_s(z)\,/\,\rho_{\rm crit,0}$",
                   title=r"Species energy-density evolution (log-log)",
                   xlog=True, ylog=True)
    ax.set_xlim(1, 1e6)
    ax.set_ylim(1e-10, 1e25)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9, ncol=1)
    _save(fig, "01_omega_evolution_log", TOPIC_01)


def plot_02_rho_invariance() -> None:
    """|ρ_s × a^{3(1+w_s)} / ⟨·⟩ − 1|  on log scale — machine-precision
    noise floor confirms the closed-form adiabats are exact.
    """
    bg = Shared.bg()
    reg = Shared.registry()
    eta_grid = bg.eta[1:]
    a = bg.a[1:]

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    from bass.species.base import SpeciesLabel
    tests = [
        (SpeciesLabel.PHOTON,   4.0, "photon",   r"$\rho_\gamma a^4$"),
        (SpeciesLabel.NEUTRINO, 4.0, "neutrino", r"$\rho_\nu a^4$"),
        (SpeciesLabel.BARYON,   3.0, "baryon",   r"$\rho_b a^3$"),
        (SpeciesLabel.CDM,      3.0, "cdm",      r"$\rho_c a^3$"),
        (SpeciesLabel.LAMBDA,   0.0, "lambda",   r"$\rho_\Lambda$"),
    ]
    for lab, p, key, text in tests:
        rho = np.asarray(reg[lab].rho_rest(eta_grid))
        inv = rho * a ** p
        mean = inv.mean()
        residual = np.abs(inv / mean - 1.0)
        ax.plot(a, np.clip(residual, 1e-18, None),
                color=SPECIES_COLOR[key], ls=SPECIES_LS[key], lw=1.2,
                label=f"{SPECIES_LABEL[key]} — {text}")
    ax.axhline(1e-14, color="0.5", ls=":", lw=0.6)
    ax.axhline(1e-12, color="0.5", ls=":", lw=0.6)
    _prepare_axes(ax, r"scale factor $a$",
                   r"$|\,\mathrm{invariant}/\langle\cdot\rangle - 1\,|$",
                   title=r"Invariance of $\rho_s\,a^{3(1+w_s)}$ — machine-precision noise",
                   xlog=True, ylog=True)
    ax.set_ylim(1e-17, 1e-10)
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "02_rho_invariance", TOPIC_01)


def plot_03_temperature_overlay() -> None:
    """T_γ(z), T_ν(z), T_m(z) overlaid — Compton decoupling visible."""
    bg = Shared.bg()
    reg = Shared.registry()
    table, recomb = Shared.recomb()

    z_grid = np.geomspace(1.0, 5000.0, 800)
    a_grid = 1.0 / (1.0 + z_grid)
    eta_grid = np.array([bg.eta_at_a(a) for a in a_grid])

    from bass.species.base import SpeciesLabel
    T_gamma = np.asarray(reg[SpeciesLabel.PHOTON].temperature(eta_grid))
    T_nu = np.asarray(reg[SpeciesLabel.NEUTRINO].temperature(eta_grid))
    T_m = recomb.query_T_m(z_grid)

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(1 + z_grid, T_gamma, color=SPECIES_COLOR["photon"], lw=1.6,
            label=r"$T_\gamma(z)$")
    ax.plot(1 + z_grid, T_nu, color=SPECIES_COLOR["neutrino"], ls="--", lw=1.4,
            label=r"$T_\nu(z)=(4/11)^{1/3}\,T_\gamma(z)$")
    ax.plot(1 + z_grid, T_m, color=SPECIES_COLOR["baryon"], lw=1.8,
            label=r"$T_{\rm m}(z)$ — HyRec")

    ax.axvspan(150 + 1, 500 + 1, alpha=0.08, color="0.3")
    ax.text(250, 2e3, "Compton decoupling", fontsize=8,
            color="0.3", ha="center")

    _prepare_axes(ax, r"$1 + z$", r"temperature  [K]",
                   title="Photon / neutrino / matter temperatures",
                   xlog=True, ylog=True)
    ax.set_xlim(1, 5000)
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "03_temperature_overlay", TOPIC_01)


def plot_04_equality_crossover() -> None:
    """Zoom around z_eq showing ρ_m and ρ_r crossing."""
    bg = Shared.bg()
    reg = Shared.registry()
    c = reg.constants
    z_eq = c.Omega_m_0 / c.Omega_r_0 - 1.0

    z_grid = np.geomspace(500, 50000, 400)
    a_grid = 1.0 / (1.0 + z_grid)
    eta_grid = np.array([bg.eta_at_a(a) for a in a_grid])

    from bass.species.base import SpeciesLabel
    rho_r = (np.asarray(reg[SpeciesLabel.PHOTON].rho_rest(eta_grid))
             + np.asarray(reg[SpeciesLabel.NEUTRINO].rho_rest(eta_grid)))
    rho_m = (np.asarray(reg[SpeciesLabel.BARYON].rho_rest(eta_grid))
             + np.asarray(reg[SpeciesLabel.CDM].rho_rest(eta_grid)))

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(1 + z_grid, rho_r, color=COLS["orange"], lw=1.6,
            label=r"$\rho_\gamma + \rho_\nu$")
    ax.plot(1 + z_grid, rho_m, color=COLS["blue"], lw=1.6,
            label=r"$\rho_b + \rho_c$")
    ax.axvline(1 + z_eq, color="0.3", ls=":", lw=1.0)
    ymid = np.sqrt(rho_r.min() * rho_r.max())
    ax.text(1 + z_eq, ymid, f"  $z_{{\\rm eq}}={z_eq:.0f}$",
             rotation=90, va="center", ha="left", fontsize=9, color="0.3")
    _prepare_axes(ax, r"$1 + z$", r"$\rho \,/\, \rho_{\rm crit,0}$",
                   title="Matter–radiation equality crossover",
                   xlog=True, ylog=True)
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "04_equality_crossover", TOPIC_01)


def plot_05_w_evolution() -> None:
    """Equation-of-state w_s(z) for each species."""
    bg = Shared.bg()
    reg = Shared.registry()
    z_grid = np.geomspace(1e-3, 1e6, 400)
    a_grid = 1.0 / (1.0 + z_grid)
    eta_grid = np.array([bg.eta_at_a(a) for a in a_grid])

    from bass.species.base import CANONICAL_ORDER, SpeciesLabel
    key_map = {
        SpeciesLabel.PHOTON: "photon",
        SpeciesLabel.NEUTRINO: "neutrino",
        SpeciesLabel.BARYON: "baryon",
        SpeciesLabel.CDM: "cdm",
        SpeciesLabel.LAMBDA: "lambda",
    }

    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    for lab in CANONICAL_ORDER:
        w = np.asarray(reg[lab].w(eta_grid))
        key = key_map[lab]
        ax.plot(1 + z_grid, w, color=SPECIES_COLOR[key], ls=SPECIES_LS[key],
                lw=1.4, label=SPECIES_LABEL[key])
    for y, txt in [(1 / 3, "radiation w=1/3"), (0, "dust w=0"),
                    (-1, "Λ w=−1")]:
        ax.axhline(y, color="0.5", lw=0.4, ls=":")
    _prepare_axes(ax, r"$1 + z$", r"$w_s = p_s / \rho_s$",
                   title="Species equation-of-state history",
                   xlog=True)
    ax.set_ylim(-1.15, 0.5)
    ax.legend(loc="center right", fontsize=9)
    _save(fig, "05_w_evolution", TOPIC_01)


def plot_06_rho_total_stack() -> None:
    """Stacked area plot of Ω_s(a) / Ω_total(a)."""
    bg = Shared.bg()
    reg = Shared.registry()
    a = bg.a[1:]
    eta = bg.eta[1:]

    from bass.species.base import CANONICAL_ORDER, SpeciesLabel
    key_map = {
        SpeciesLabel.PHOTON: "photon",
        SpeciesLabel.NEUTRINO: "neutrino",
        SpeciesLabel.BARYON: "baryon",
        SpeciesLabel.CDM: "cdm",
        SpeciesLabel.LAMBDA: "lambda",
    }
    rhos = {k: np.asarray(reg[lab].rho_rest(eta))
             for lab, k in key_map.items()}
    total = sum(rhos.values())
    fractions = {k: v / total for k, v in rhos.items()}

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    order = ["photon", "neutrino", "baryon", "cdm", "lambda"]
    stack = np.vstack([fractions[k] for k in order])
    ax.stackplot(a, stack,
                  colors=[SPECIES_COLOR[k] for k in order],
                  labels=[SPECIES_LABEL[k] for k in order],
                  alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlim(a.min(), 1.0)
    ax.set_ylim(0, 1)
    ax.set_xlabel(r"$a$")
    ax.set_ylabel(r"$\Omega_s(a) \,/\, \Omega_{\rm tot}(a)$")
    ax.set_title("Relative energy-density composition across history")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.8)
    ax.grid(True, which="both", alpha=0.25, lw=0.4)
    _save(fig, "06_rho_total_stack", TOPIC_01)


# ════════════════════════════════════════════════════════════════════
# Topic 02 — FLRW geometry
# ════════════════════════════════════════════════════════════════════


TOPIC_02 = "02_flrw_geometry"


def plot_02_01_a_of_eta() -> None:
    """a(η) with η_eq, η_*, η_0 markers."""
    bg = Shared.bg()
    reg = Shared.registry()
    c = reg.constants
    z_eq = c.Omega_m_0 / c.Omega_r_0 - 1.0
    eta_eq = bg.eta_at_a(1.0 / (1.0 + z_eq))
    eta_star = bg.eta_at_a(1.0 / (1.0 + 1089.94))

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    # log-η spreads the radiation era so η_eq (~400 Mpc) and η_*
    # (~283 Mpc) don't overlap; linear clustering is avoided.
    ax.plot(bg.eta[1:], bg.a[1:], color=COLS["blue"], lw=1.8)
    labels_meta = [
        (eta_star,     "η_* ≈ {:.0f} Mpc (last scattering)".format(eta_star),
         COLS["red"],    0.08),
        (eta_eq,       "η_eq ≈ {:.0f} Mpc (mat-rad equality)".format(eta_eq),
         COLS["orange"], 0.28),
        (bg.eta_today, "η_0 ≈ {:.0f} Mpc (today)".format(bg.eta_today),
         COLS["green"],  0.55),
    ]
    for eta_mark, label, col, y_text in labels_meta:
        ax.axvline(eta_mark, color=col, ls=":", lw=1.2)
        ax.text(eta_mark * 1.05, y_text, label,
                 rotation=90, va="bottom", ha="left", fontsize=9,
                 color=col, transform=ax.get_xaxis_transform())
    _prepare_axes(ax, r"conformal time $\eta$ [Mpc]",
                   r"scale factor $a(\eta)$",
                   title=f"Flat ΛCDM scale factor (log-η, η₀ = {bg.eta_today:.1f} Mpc)",
                   xlog=True, ylog=True)
    ax.set_xlim(bg.eta[1], bg.eta_today * 1.05)
    _save(fig, "01_scale_factor_vs_eta", TOPIC_02)


def plot_02_02_hubble_vs_a() -> None:
    """H(a) log-log with radiation/matter/Λ regime annotations."""
    bg = Shared.bg()
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(bg.a, bg.H_mpc, color=COLS["purple"], lw=1.6)
    # Asymptotic laws
    c = bg.constants
    H0 = bg.H0_mpc
    a_fit = bg.a
    ax.plot(a_fit, H0 * np.sqrt(c.Omega_r_0) / a_fit ** 2,
            color=COLS["orange"], ls=":", lw=1.0,
            label=r"$H_0\sqrt{\Omega_r}\,a^{-2}$ (radiation)")
    ax.plot(a_fit, H0 * np.sqrt(c.Omega_m_0) / a_fit ** 1.5,
            color=COLS["blue"], ls=":", lw=1.0,
            label=r"$H_0\sqrt{\Omega_m}\,a^{-3/2}$ (matter)")
    ax.axhline(H0 * np.sqrt(c.Omega_Lambda_0), color=COLS["green"], ls=":",
                lw=1.0, label=r"$H_0\sqrt{\Omega_\Lambda}$ (de Sitter)")
    _prepare_axes(ax, r"$a$", r"$H(a)$  [Mpc$^{-1}$]",
                   title="Hubble evolution with asymptotic scalings",
                   xlog=True, ylog=True)
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "02_hubble_vs_a", TOPIC_02)


def plot_02_03_conformal_hubble() -> None:
    """𝓗(η) = aH — monotone decreasing in radiation/matter era,
    turning over into the Λ-driven accelerating rise late on.
    """
    bg = Shared.bg()
    # 𝓗 has a *minimum* (not a peak) where matter→Λ transition begins.
    # Search only in the late-time half of the grid to avoid the radiation
    # endpoint which dominates 𝓗.
    late = bg.eta > bg.eta_today * 0.5
    idx_min_late = int(np.argmin(bg.calH_mpc[late]))
    eta_min = bg.eta[late][idx_min_late]
    calH_min = bg.calH_mpc[late][idx_min_late]

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(bg.eta[1:], bg.calH_mpc[1:], color=COLS["blue"], lw=1.6)
    ax.axvline(eta_min, color="0.4", ls=":", lw=0.7)
    ax.plot([eta_min], [calH_min], "o", color=COLS["orange"], ms=5)
    ax.annotate(
        f"minimum at η={eta_min:.0f} Mpc\n"
        r"$\mathcal{H}_{\min}$ = " + f"{calH_min:.2e}",
        xy=(eta_min, calH_min),
        xytext=(eta_min * 0.3, calH_min * 3),
        fontsize=8, color="0.25",
        arrowprops=dict(arrowstyle="->", color="0.5", lw=0.6),
    )
    _prepare_axes(ax, r"$\eta$ [Mpc]", r"$\mathcal{H} = a\,H$  [Mpc$^{-1}$]",
                   title=r"Conformal Hubble rate (log-log)",
                   xlog=True, ylog=True)
    _save(fig, "03_conformal_hubble", TOPIC_02)


def plot_02_04_eta_of_z() -> None:
    """η(z): comoving time from today, with CMB last-scattering marker."""
    bg = Shared.bg()
    z_plot = np.geomspace(0.01, 1e4, 400)
    a_plot = 1.0 / (1.0 + z_plot)
    eta_plot = np.array([bg.eta_at_a(a) for a in a_plot])
    # elapsed conformal time since today: η_0 − η(z)
    eta_elapsed = bg.eta_today - eta_plot

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(1 + z_plot, eta_elapsed, color=COLS["purple"], lw=1.6)
    z_star = 1089.94
    a_star = 1.0 / (1.0 + z_star)
    eta_to_cmb = bg.eta_today - bg.eta_at_a(a_star)
    ax.axvline(1 + z_star, color=COLS["red"], ls=":", lw=1.0)
    ax.axhline(eta_to_cmb, color=COLS["red"], ls=":", lw=0.6)
    ax.plot([1 + z_star], [eta_to_cmb], "o", color=COLS["red"], ms=5)
    ax.text(1 + z_star, eta_to_cmb * 0.92,
             f"  CMB: {eta_to_cmb:.0f} Mpc", fontsize=9, color=COLS["red"])
    _prepare_axes(ax, r"$1 + z$", r"$\eta_0 - \eta(z)$ [Mpc]",
                   title="Conformal distance to redshift z (flat ΛCDM)",
                   xlog=True)
    _save(fig, "04_eta_of_z", TOPIC_02)


def plot_02_05_H0_sensitivity() -> None:
    """η_0 and distance to CMB vs H_0."""
    h_values = np.linspace(0.60, 0.76, 9)
    eta_0_vals = []
    eta_cmb_vals = []
    for h in h_values:
        c_variant = dataclasses.replace(default_constants(), h=h,
                                          H0_km_s_mpc=h * 100.0)
        bg_v = build_flrw_background_table(constants=c_variant, n_eta=2000)
        eta_0_vals.append(bg_v.eta_today)
        a_star = 1.0 / (1.0 + 1089.94)
        eta_cmb_vals.append(bg_v.eta_today - bg_v.eta_at_a(a_star))

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(h_values * 100, eta_0_vals, "o-", color=COLS["blue"], lw=1.4,
            label=r"$\eta_0$ (today)")
    ax.plot(h_values * 100, eta_cmb_vals, "s--", color=COLS["red"], lw=1.4,
            label=r"$\eta_0 - \eta_*$ (to CMB)")
    ax.axvline(67.36, color="0.4", ls=":", lw=0.7)
    ax.text(67.36, max(eta_0_vals), "Planck 2018",
             fontsize=8, ha="right", va="top", color="0.3")
    _prepare_axes(ax, r"$H_0$ [km/s/Mpc]", r"conformal distance [Mpc]",
                   title=r"Conformal horizon sensitivity to $H_0$")
    ax.legend(loc="upper right", fontsize=9)
    _save(fig, "05_H0_sensitivity", TOPIC_02)


def plot_02_06_Omega_m_sensitivity() -> None:
    """η_0 and z_eq vs Ω_m (Ω_b fixed, Ω_c adjusted)."""
    Omega_m_values = np.linspace(0.26, 0.36, 9)
    eta_0_vals = []
    z_eq_vals = []
    base_c = default_constants()
    for Omega_m in Omega_m_values:
        Omega_c_new = Omega_m - base_c.Omega_b_0
        Omega_L_new = 1.0 - Omega_m - base_c.Omega_r_0
        c_variant = dataclasses.replace(
            base_c, Omega_c_0=Omega_c_new, Omega_Lambda_0=Omega_L_new,
        )
        bg_v = build_flrw_background_table(constants=c_variant, n_eta=2000)
        eta_0_vals.append(bg_v.eta_today)
        z_eq_vals.append(Omega_m / base_c.Omega_r_0 - 1.0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.8))
    ax1.plot(Omega_m_values, eta_0_vals, "o-", color=COLS["purple"], lw=1.4)
    _prepare_axes(ax1, r"$\Omega_m$", r"$\eta_0$ [Mpc]",
                   title=r"$\eta_0$ vs $\Omega_m$")
    ax2.plot(Omega_m_values, z_eq_vals, "s-", color=COLS["orange"], lw=1.4)
    _prepare_axes(ax2, r"$\Omega_m$", r"$z_{\rm eq}$",
                   title=r"$z_{\rm eq}$ vs $\Omega_m$")
    for a in (ax1, ax2):
        a.axvline(base_c.Omega_m_0, color="0.4", ls=":", lw=0.7)
    _save(fig, "06_Omega_m_sensitivity", TOPIC_02)


# ════════════════════════════════════════════════════════════════════
# Topic 03 — Recombination
# ════════════════════════════════════════════════════════════════════


TOPIC_03 = "03_recombination"


def plot_03_01_x_e_full() -> None:
    """x_e(z) from HyRec fixture across the full recombination range."""
    _, recomb = Shared.recomb()
    z = np.linspace(recomb.table.z_min, recomb.table.z_max, 3000)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(z, recomb.query_x_e(z), color=COLS["blue"], lw=1.6)
    # Regime annotations placed at fixed y-anchors (axis fraction) so
    # they stay inside the visible range regardless of x_e local value.
    ax.text(5500, 0.4, "fully ionised", fontsize=9, color="0.3", ha="center")
    ax.text(600, 5e-3, "recombining", fontsize=9, color="0.3", ha="center",
             rotation=-60)
    ax.text(100, 3e-4, "residual ionisation", fontsize=9, color="0.3",
             ha="center")
    ax.axvline(1089.94, color=COLS["red"], ls=":", lw=0.8)
    ax.text(1089.94, 0.2, r" $z_* = 1089.94$", fontsize=10,
             color=COLS["red"], rotation=90, ha="left", va="center")
    _prepare_axes(ax, r"$z$", r"$x_e(z)$",
                   title=r"HyRec-2 free-electron fraction (Planck 2018)",
                   ylog=True)
    ax.set_xlim(z.min(), z.max())
    ax.set_ylim(1e-4, 2.0)
    _save(fig, "01_x_e_full", TOPIC_03)


def plot_03_02_T_m_vs_T_gamma() -> None:
    """T_m(z) and T_γ(z) overlaid, showing Compton decoupling."""
    _, recomb = Shared.recomb()
    c = default_constants()
    z = np.linspace(recomb.table.z_min, recomb.table.z_max, 3000)
    T_gamma = c.T_gamma_0_K * (1 + z)
    T_m = recomb.query_T_m(z)
    ratio = T_m / T_gamma

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.5, 5.5), sharex=True,
                                     gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(z, T_gamma, color=SPECIES_COLOR["photon"], lw=1.6,
             label=r"$T_\gamma(z)=T_{\gamma,0}(1+z)$")
    ax1.plot(z, T_m, color=SPECIES_COLOR["baryon"], lw=1.6,
             label=r"$T_{\rm m}(z)$ [HyRec]")
    _prepare_axes(ax1, "", "temperature [K]",
                   title="Photon vs matter temperature", xlog=True, ylog=True)
    ax1.legend(loc="lower right", fontsize=9)

    ax2.plot(z, ratio, color=COLS["purple"], lw=1.4)
    ax2.axhline(1.0, color="0.4", lw=0.6, ls="--")
    _prepare_axes(ax2, r"$z$", r"$T_{\rm m} \,/\, T_\gamma$", xlog=True)
    ax2.set_ylim(0, 1.1)
    _save(fig, "02_T_m_vs_T_gamma", TOPIC_03)


def plot_03_03_tau_dot() -> None:
    """Differential optical depth τ̇(z) [Mpc⁻¹]."""
    _, recomb = Shared.recomb()
    z = np.linspace(recomb.table.z_min, recomb.table.z_max, 3000)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(z, recomb.query_tau_dot(z), color=COLS["red"], lw=1.6)
    ax.axvline(1089.94, color="0.3", ls=":", lw=0.8)
    _prepare_axes(ax, r"$z$",
                   r"$\dot\tau(z) = a\,n_e\,x_e\,\sigma_T$ [Mpc$^{-1}$]",
                   title=r"Thomson interaction rate $\dot\tau(z)$",
                   xlog=True, ylog=True)
    ax.set_xlim(z.min(), z.max())
    _save(fig, "03_tau_dot", TOPIC_03)


def plot_03_04_kappa_cumulative() -> None:
    """Cumulative optical depth κ(z) on log-log.

    log-y is essential: κ spans many orders from ~1e-6 at low z
    (reion era, but this plot is recomb-only) to ~10³ at z_max, and
    the physically relevant κ=1 surface at z_* is invisible on a
    linear axis.
    """
    _, recomb = Shared.recomb()
    z = np.linspace(recomb.table.z_min, recomb.table.z_max, 3000)
    k = recomb.query_kappa(z)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(z, np.clip(k, 1e-10, None), color=COLS["purple"], lw=1.6)
    ax.axhline(1.0, color="0.4", ls="--", lw=0.8)
    ax.text(2, 1.2, r"$\kappa = 1$ surface (last scattering)",
             color="0.3", fontsize=9)
    ax.axvline(1089.94, color=COLS["red"], ls=":", lw=0.8)
    ax.text(1089.94, 10.0, r" $z_* \approx 1090$",
             color=COLS["red"], fontsize=9, rotation=90,
             ha="left", va="center")
    _prepare_axes(ax, r"$z$", r"$\kappa(z) = \int_0^z \dot\tau\,d\eta'$",
                   title="Cumulative optical depth (log-log)",
                   xlog=True, ylog=True)
    ax.set_xlim(z.min(), z.max())
    _save(fig, "04_kappa_cumulative", TOPIC_03)


def plot_03_05_visibility_peak() -> None:
    """g(z) visibility function with peak annotation."""
    from bass.recombination.recombination_ingest import find_visibility_peak
    _, recomb = Shared.recomb()
    z = np.linspace(600, 1800, 3000)
    g = recomb.query_visibility(z)
    z_peak, g_peak = find_visibility_peak(recomb)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(z, g, color=COLS["green"], lw=1.6)
    ax.axvline(z_peak, color=COLS["red"], ls=":", lw=1.0)
    ax.plot([z_peak], [g_peak], "o", color=COLS["red"], ms=6)
    # Place annotation in upper-right interior, with arrow to the peak.
    ax.annotate(
        f"peak at $z = {z_peak:.1f}$\n"
        f"$g_{{\\rm peak}} = {g_peak:.3e}$ Mpc$^{{-1}}$",
        xy=(z_peak, g_peak),
        xytext=(z_peak + 350, g_peak * 0.75),
        fontsize=9, color=COLS["red"],
        arrowprops=dict(arrowstyle="->", color=COLS["red"], lw=0.8),
    )
    _prepare_axes(ax, r"$z$", r"$g(z) = \dot\tau\,e^{-\kappa}$ [Mpc$^{-1}$]",
                   title="Visibility function (surface of last scattering)")
    ax.set_xlim(z.min(), z.max())
    _save(fig, "05_visibility_peak", TOPIC_03)


def plot_03_06_visibility_eta() -> None:
    """g(η) in conformal-time space, zoomed around the recomb peak.

    Sort by η so the FWHM band and peak indexing are monotone-safe
    regardless of the z → η mapping direction.
    """
    bg = Shared.bg()
    _, recomb = Shared.recomb()
    z = np.linspace(recomb.table.z_min, 3000, 3000)
    a = 1.0 / (1.0 + z)
    eta = np.array([bg.eta_at_a(aa) for aa in a])
    g_z = recomb.query_visibility(z)
    # dz/dη = −(1+z)² × 𝓗; g_η(η) = g_z × |dz/dη|
    calH = bg.interp_calH(eta)
    g_eta = g_z * (1 + z) ** 2 * calH

    # Sort ascending in η.
    order = np.argsort(eta)
    eta = eta[order]
    g_eta = g_eta[order]

    idx_peak = int(np.argmax(g_eta))
    eta_peak = eta[idx_peak]
    g_peak = g_eta[idx_peak]

    # FWHM via half-max
    half = g_peak / 2.0
    above = np.where(g_eta > half)[0]
    fwhm = abs(eta[above[-1]] - eta[above[0]]) if len(above) else 0.0

    # Zoom to ±4×FWHM around the peak — the rest is essentially zero.
    zoom_width = max(fwhm * 6, 400.0)
    eta_lo = max(eta_peak - zoom_width, eta.min())
    eta_hi = min(eta_peak + zoom_width, eta.max())

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(eta, g_eta, color=COLS["green"], lw=1.6)
    if len(above):
        ax.axvspan(eta[above[0]], eta[above[-1]], alpha=0.15,
                    color=COLS["green"], label=f"FWHM ≈ {fwhm:.0f} Mpc")
    ax.axvline(eta_peak, color=COLS["red"], ls=":", lw=0.8)
    ax.plot([eta_peak], [g_peak], "o", color=COLS["red"], ms=5)
    ax.set_xlim(eta_lo, eta_hi)
    _prepare_axes(ax, r"conformal time $\eta$ [Mpc]",
                   r"$g(\eta) = g(z)\,(1+z)^2\,\mathcal{H}$ [Mpc$^{-1}$]",
                   title=f"Visibility in conformal-time space (zoom around η={eta_peak:.0f} Mpc)")
    ax.legend(loc="upper right", fontsize=9)
    _save(fig, "06_visibility_eta", TOPIC_03)


# ════════════════════════════════════════════════════════════════════
# Topic 04 — Reionization
# ════════════════════════════════════════════════════════════════════


TOPIC_04 = "04_reionization"


def plot_04_01_tanh_profile_sweep() -> None:
    """x_e^{reion}(z) for a sweep of z_rei_H."""
    z_rei_values = [6.0, 7.0, 7.67, 9.0, 11.0]
    _, base_interp = Shared.recomb()
    z = np.linspace(0.01, 20, 600)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    cmap = plt.get_cmap("viridis")
    for i, z_r in enumerate(z_rei_values):
        reion = ReionizationParameters(z_reion_H=z_r)
        ext_table, _, _ = Shared.recomb_reion(reion)
        interp_v = build_interpolators(ext_table)
        xe = interp_v.query_x_e(z)
        ax.plot(z, xe, color=cmap(i / (len(z_rei_values) - 1)), lw=1.3,
                label=f"$z_{{\\rm rei,H}}={z_r}$")
    _prepare_axes(ax, r"$z$", r"$x_e(z)$",
                   title=r"tanh reionization profile sweep ($\Delta z=0.5$)")
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 1.25)
    ax.legend(loc="center right", fontsize=9)
    _save(fig, "01_tanh_profile_sweep", TOPIC_04)


def plot_04_02_combined_xe() -> None:
    """Full x_e history: recomb + reion overlaid on baseline."""
    _, base_interp = Shared.recomb()
    ext_table, ext_interp, cosmo = Shared.recomb_reion()
    z = np.geomspace(0.01, 3000, 2000)
    # baseline (recomb only) clipped to its range
    z_base = z[z >= base_interp.table.z_min]
    xe_base = base_interp.query_x_e(z_base)
    xe_full = ext_interp.query_x_e(z)

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(z, xe_full, color=COLS["blue"], lw=1.6,
            label="recomb + reion (tanh H + HeII)")
    ax.plot(z_base, xe_base, color=COLS["gray"], ls="--", lw=1.1,
            label="recomb only (HyRec)")
    ax.axvspan(0, 8, alpha=0.08, color=COLS["orange"])
    ax.text(4, 0.5, "reion era", fontsize=9, color="0.3", ha="center")
    _prepare_axes(ax, r"$z$", r"$x_e(z)$",
                   title="Full ionisation history",
                   xlog=True, ylog=True)
    ax.set_xlim(0.1, 3000)
    ax.set_ylim(1e-4, 2.0)
    ax.legend(loc="lower right", fontsize=9)
    _save(fig, "02_combined_xe", TOPIC_04)


def plot_04_03_tau_reion_sweep() -> None:
    """τ_reion as a function of z_rei_H."""
    z_rei_values = np.linspace(5.5, 12.0, 14)
    table, _ = Shared.recomb()
    cosmo = cosmology_from_metadata(table.metadata)
    tau_vals = []
    for z_r in z_rei_values:
        reion = ReionizationParameters(z_reion_H=z_r)
        ext_table = extend_table_with_reionization(table, reion, cosmology=cosmo)
        tau_vals.append(compute_reionization_tau(ext_table, z_high_cutoff=30.0))

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(z_rei_values, tau_vals, "o-", color=COLS["red"], lw=1.4)
    ax.axhline(0.0544, color="0.3", ls="--", lw=0.8,
                label="Planck 2018: τ = 0.0544")
    ax.axhspan(0.0544 - 0.0073, 0.0544 + 0.0073, alpha=0.1, color="0.5")
    _prepare_axes(ax, r"$z_{\rm rei,H}$", r"$\tau_{\rm reion}$",
                   title=r"Reionization optical depth vs midpoint redshift")
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "03_tau_reion_sweep", TOPIC_04)


def plot_04_04_HeII_on_off() -> None:
    """Effect of HeII second reionization on x_e."""
    table, _ = Shared.recomb()
    cosmo = cosmology_from_metadata(table.metadata)
    reion_with = ReionizationParameters(include_HeII=True)
    reion_without = ReionizationParameters(include_HeII=False)
    ext_with = extend_table_with_reionization(table, reion_with, cosmology=cosmo)
    ext_without = extend_table_with_reionization(table, reion_without,
                                                   cosmology=cosmo)
    interp_with = build_interpolators(ext_with)
    interp_without = build_interpolators(ext_without)

    z = np.linspace(0, 15, 600)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(z, interp_with.query_x_e(z), color=COLS["red"], lw=1.6,
            label="H + HeII reion")
    ax.plot(z, interp_without.query_x_e(z), color=COLS["blue"], ls="--",
            lw=1.3, label="H only")
    ax.axhline(1.0, color="0.4", lw=0.6, ls=":")
    ax.axhline(1.0 + cosmo.f_He, color="0.4", lw=0.6, ls=":")
    ax.axhline(1.0 + 2 * cosmo.f_He, color="0.4", lw=0.6, ls=":")
    ax.text(0.3, 1.005, r"$1$ (no He ionisation)",
             fontsize=8, color="0.35", ha="left")
    ax.text(0.3, 1 + cosmo.f_He + 0.005, r"$1 + f_{\rm He}$  (HeI done)",
             fontsize=8, color="0.35", ha="left")
    ax.text(0.3, 1 + 2 * cosmo.f_He + 0.005, r"$1 + 2f_{\rm He}$  (HeII done)",
             fontsize=8, color="0.35", ha="left")
    _prepare_axes(ax, r"$z$", r"$x_e(z)$",
                   title=r"HeII second reionization effect")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_ylim(0, 1.25)
    ax.set_xlim(0, 15)
    _save(fig, "04_HeII_on_off", TOPIC_04)


def plot_04_05_visibility_with_reion() -> None:
    """g(z) including the reionization bump."""
    ext_table, ext_interp, _ = Shared.recomb_reion()
    z = np.geomspace(0.1, 3000, 3000)
    g = ext_interp.query_visibility(z)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(z, g, color=COLS["green"], lw=1.6)
    ax.axvspan(5, 10, alpha=0.12, color=COLS["orange"])
    ax.text(7.3, g.max() * 0.03, "reion bump", fontsize=8, color="0.3",
             ha="center")
    _prepare_axes(ax, r"$z$", r"$g(z) = \dot\tau\,e^{-\kappa}$ [Mpc$^{-1}$]",
                   title="Visibility with recombination + tanh reionization",
                   xlog=True, ylog=True)
    ax.set_xlim(0.5, 3000)
    ax.set_ylim(max(g.min(), 1e-8), g.max() * 2)
    _save(fig, "05_visibility_with_reion", TOPIC_04)


# ════════════════════════════════════════════════════════════════════
# Topic 05 — Bianchi shear
# ════════════════════════════════════════════════════════════════════


TOPIC_05 = "05_bianchi_shear"


def _bianchi_solve(structure, sigma_over_H_init: float = 1e-3,
                    sigma_pm_ratio: float = 0.0):
    """Bianchi solve with SSOT-consistent flat-ΛCDM constants.

    Post-audit: reads Ω values from ``bass.species.default_constants()``
    so the gallery's Bianchi shear plots use the same cosmology as the
    species background plots (flat closure Σ Ω = 1 exactly).
    """
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
    return solve_bianchi_background(cosmo, a_start=1e-6, a_end=1.0, n_pts=3000)


def plot_05_01_Sigma2_decay_types() -> None:
    """Σ²(a) for Bianchi I, V, VII_0 + deviation-from-Kasner panel.

    Structure-constant amplitudes are pushed large so the spatial-
    curvature source visibly separates the three types from the
    pure-Kasner (Type I) reference.
    """
    cases = [
        ("I",    type_i_constants(),                              COLS["blue"]),
        ("V",    type_v_constants(a_twist=5e-2),                  COLS["orange"]),
        ("VII₀", type_vii0_constants(n1=2e-2, n3=3e-2),           COLS["green"]),
    ]
    results = []
    for label, sc, color in cases:
        try:
            bg = _bianchi_solve(sc, sigma_over_H_init=1e-3)
        except Exception as exc:
            print(f"  [skip] Bianchi {label}: {exc}")
            continue
        Sig2 = (bg.sigma_plus ** 2 + bg.sigma_minus ** 2) / (6 * bg.calH ** 2)
        results.append((label, color, bg.a, np.clip(Sig2, 1e-30, None)))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for label, color, a, Sig2 in results:
        ax1.plot(a, Sig2, lw=1.5, color=color, label=f"Type {label}")
    _prepare_axes(
        ax1, r"$a$", r"$\Sigma^2 \equiv \sigma_{ab}\sigma^{ab}/(6H^2)$",
        title=r"Shear invariant decay",
        xlog=True, ylog=True,
    )
    ax1.legend(loc="upper right", fontsize=9)

    # Deviation from Type I (pure Kasner) makes the curvature source visible.
    if results:
        base_label, _, base_a, base_Sig2 = results[0]
        for label, color, a, Sig2 in results:
            ratio = np.interp(base_a, a, Sig2) / base_Sig2
            ax2.plot(base_a, ratio, lw=1.5, color=color,
                      label=f"Type {label}")
    ax2.axhline(1.0, color="0.4", ls=":", lw=0.6)
    _prepare_axes(
        ax2, r"$a$", r"$\Sigma^2(\mathrm{type}) \,/\, \Sigma^2(\mathrm{I})$",
        title=r"Deviation from pure Bianchi-I Kasner",
        xlog=True, ylog=True,
    )
    ax2.legend(loc="upper left", fontsize=9)
    _save(fig, "01_Sigma2_decay_types", TOPIC_05)


def plot_05_02_sigma_pm_timeseries() -> None:
    """|Σ_+(η)|, |Σ_-(η)| for Bianchi I with several (σ_-/σ_+) ratios."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.0), sharex=True)
    for pm_ratio, label, color in [
        (0.0, r"axisymmetric  $\sigma_-=0$", COLS["blue"]),
        (0.5, r"$\sigma_-/\sigma_+ = 0.5$",  COLS["orange"]),
        (1.0, r"$\sigma_-/\sigma_+ = 1.0$",  COLS["red"]),
    ]:
        bg = _bianchi_solve(type_i_constants(), sigma_over_H_init=1e-3,
                              sigma_pm_ratio=pm_ratio)
        ax1.plot(bg.eta[1:], np.clip(np.abs(bg.sigma_plus[1:]), 1e-30, None),
                  color=color, lw=1.3, label=label)
        ax2.plot(bg.eta[1:], np.clip(np.abs(bg.sigma_minus[1:]), 1e-30, None),
                  color=color, lw=1.3, label=label)
    _prepare_axes(ax1, r"$\eta$ [Mpc]", r"$|\Sigma_+|$ [Mpc$^{-1}$]",
                   title=r"Plus mode", xlog=True, ylog=True)
    _prepare_axes(ax2, r"$\eta$ [Mpc]", r"$|\Sigma_-|$ [Mpc$^{-1}$]",
                   title=r"Cross mode", xlog=True, ylog=True)
    ax1.legend(loc="lower left", fontsize=8)
    _save(fig, "02_sigma_pm_timeseries", TOPIC_05)


def plot_05_03_sigma_pm_phaseplane() -> None:
    """Σ_+ vs Σ_- phase-plane trajectory (Bianchi I)."""
    fig, ax = plt.subplots(figsize=(5.5, 5.0))
    for pm_ratio, color in [(0.2, COLS["blue"]), (0.5, COLS["orange"]),
                              (1.0, COLS["red"]),
                              (-0.3, COLS["purple"])]:
        bg = _bianchi_solve(type_i_constants(), sigma_over_H_init=1e-3,
                              sigma_pm_ratio=pm_ratio)
        ax.plot(bg.sigma_plus, bg.sigma_minus, color=color, lw=1.1,
                 label=f"σ_-/σ_+ = {pm_ratio}")
    _prepare_axes(ax, r"$\Sigma_+$ [Mpc$^{-1}$]", r"$\Sigma_-$ [Mpc$^{-1}$]",
                   title=r"Shear phase-plane trajectories (Bianchi I)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "03_sigma_pm_phaseplane", TOPIC_05)


def plot_05_04_a_minus_4_law() -> None:
    """Σ²(a) × a^n for various n to identify the actual power law."""
    bg = _bianchi_solve(type_i_constants(), sigma_over_H_init=1e-3)
    Sig2 = (bg.sigma_plus ** 2 + bg.sigma_minus ** 2) / (6 * bg.calH ** 2)

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    for n, color in zip([2, 3, 4, 5, 6], [COLS["blue"], COLS["orange"],
                                            COLS["red"], COLS["purple"],
                                            COLS["green"]]):
        product = Sig2 * bg.a ** n
        ax.plot(bg.a, product / product[-1], color=color, lw=1.2,
                label=f"$\\Sigma^2 \\, a^{n}$")
    ax.axhline(1.0, color="0.4", ls=":", lw=0.6)
    _prepare_axes(ax, r"$a$",
                   r"$\Sigma^2(a)\,a^n \,/\, \mathrm{normalisation}$",
                   title=r"Identifying the shear decay power law (Bianchi I)",
                   xlog=True, ylog=True)
    ax.legend(loc="lower right", fontsize=9)
    _save(fig, "04_a_minus_4_law", TOPIC_05)


def plot_05_05_seed_sweep() -> None:
    """Σ²(η) for different initial σ/H seeds (Bianchi I)."""
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    seeds = [1e-5, 1e-4, 1e-3, 1e-2, 5e-2]
    cmap = plt.get_cmap("plasma")
    for i, s in enumerate(seeds):
        bg = _bianchi_solve(type_i_constants(), sigma_over_H_init=s)
        Sig2 = (bg.sigma_plus ** 2 + bg.sigma_minus ** 2) / (6 * bg.calH ** 2)
        ax.plot(bg.a, np.clip(Sig2, 1e-30, None),
                color=cmap(i / (len(seeds) - 1)), lw=1.2,
                label=f"(σ/H)_i = {s:.0e}")
    _prepare_axes(ax, r"$a$", r"$\Sigma^2(a)$",
                   title=r"Initial-seed dependence of shear history (Bianchi I)",
                   xlog=True, ylog=True)
    ax.legend(loc="lower left", fontsize=8)
    _save(fig, "05_seed_sweep", TOPIC_05)


# ════════════════════════════════════════════════════════════════════
# Topic 06 — Tilt / boost kinematics
# ════════════════════════════════════════════════════════════════════


TOPIC_06 = "06_tilt_boost"


def plot_06_01_gamma_e_vs_beta() -> None:
    """Lorentz factor γ_e(β) = cosh β — non-perturbative."""
    beta = np.linspace(0, 1.5, 400)
    gamma_linear = 1.0 + 0.5 * beta ** 2
    gamma_exact = np.cosh(beta)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(beta, gamma_exact, color=COLS["blue"], lw=1.8,
            label=r"$\gamma_e = \cosh\beta$  (non-perturbative)")
    ax.plot(beta, gamma_linear, color=COLS["red"], ls="--", lw=1.3,
            label=r"$1 + \frac{1}{2}\beta^2$  (quadratic truncation)")
    ax.axvline(1e-3, color="0.4", ls=":", lw=0.6)
    ax.text(1e-3, 1.5, "CF4 regime", rotation=90, fontsize=8,
             color="0.3", va="center")
    _prepare_axes(ax, r"tilt rapidity $\beta_e$",
                   r"$\gamma_e$",
                   title=r"Lorentz factor vs rapidity — exact vs quadratic")
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "01_gamma_e_vs_beta", TOPIC_06)


def plot_06_02_boost_factor_heatmap() -> None:
    """B(β, cos θ) = cosh β + sinh β cos θ."""
    beta = np.linspace(0.0, 1.0, 120)
    cos_th = np.linspace(-1, 1, 120)
    B = np.cosh(beta)[:, None] + np.sinh(beta)[:, None] * cos_th[None, :]
    fig, ax = plt.subplots(figsize=(6.5, 4.4))
    im = ax.pcolormesh(cos_th, beta, B, cmap="RdBu_r",
                        shading="gouraud",
                        vmin=B.min(), vmax=B.max())
    fig.colorbar(im, ax=ax, label=r"$B(\beta, \cos\theta)$")
    ax.contour(cos_th, beta, B, levels=[1.0], colors=["black"],
                linewidths=0.8)
    ax.set_xlabel(r"$\cos\theta = \hat e \cdot \hat v_e$")
    ax.set_ylabel(r"rapidity $\beta_e$")
    ax.set_title(r"Tilted-visibility boost factor  $B = \cosh\beta + \sinh\beta \cos\theta$")
    _save(fig, "02_boost_factor_heatmap", TOPIC_06)


def plot_06_03_boost_directional_slice() -> None:
    """B(cos θ) at fixed β — direction slices."""
    cos_th = np.linspace(-1, 1, 400)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    for beta, color in [(0.05, COLS["cyan"]), (0.1, COLS["blue"]),
                         (0.3, COLS["orange"]), (0.6, COLS["red"]),
                         (1.0, COLS["purple"])]:
        B = np.cosh(beta) + np.sinh(beta) * cos_th
        ax.plot(cos_th, B, color=color, lw=1.4, label=f"β = {beta}")
    ax.axhline(1.0, color="0.4", ls=":", lw=0.6)
    _prepare_axes(ax, r"$\hat e \cdot \hat v_e$", r"$B(\beta, \cos\theta)$",
                   title=r"Forward/backward asymmetry of $\tilde\Gamma_T$")
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "03_boost_directional_slice", TOPIC_06)


def plot_06_04_linear_vs_exact() -> None:
    """Compare (1 + v·e) linearisation vs exact cosh+sinh."""
    beta = np.geomspace(1e-4, 1.5, 400)
    cos_th = 1.0  # head-on
    B_exact = np.cosh(beta) + np.sinh(beta) * cos_th
    B_linear = 1.0 + np.tanh(beta) * cos_th  # naive (1 + v·e)
    rel_err = (B_linear - B_exact) / B_exact

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.5, 5.5), sharex=True,
                                     gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(beta, B_exact, color=COLS["blue"], lw=1.8,
             label=r"exact: $\cosh\beta + \sinh\beta\,(\hat e \cdot \hat v)$")
    ax1.plot(beta, B_linear, color=COLS["red"], ls="--", lw=1.3,
             label=r"linearised: $1 + v \cdot e$ (BANNED)")
    _prepare_axes(ax1, "", "B", title="Why β must stay non-perturbative",
                   xlog=True, ylog=True)
    ax1.legend(loc="upper left", fontsize=9)

    ax2.plot(beta, rel_err, color=COLS["purple"], lw=1.4)
    ax2.axhline(0, color="0.4", lw=0.4, ls=":")
    ax2.axhline(-0.01, color="0.4", lw=0.4, ls=":")
    _prepare_axes(ax2, r"$\beta_e$",
                   r"$(B_{\rm lin} - B_{\rm exact})/B_{\rm exact}$",
                   xlog=True)
    _save(fig, "04_linear_vs_exact", TOPIC_06)


# ════════════════════════════════════════════════════════════════════
# Topic 07 — Friedmann closure
# ════════════════════════════════════════════════════════════════════


TOPIC_07 = "07_friedmann_closure"


def plot_07_01_residual_vs_eta() -> None:
    """Friedmann residual — relative and absolute, envelope-smoothed.

    At small a the total energy density is ≳ 10¹², so float64 roundoff
    gives an *absolute* residual of ≲ 10⁻⁴ while the *relative*
    residual stays at machine precision ≈ 10⁻¹⁵. Both are plotted; a
    moving-window envelope removes the rapid-oscillation visual
    clutter.
    """
    reg = Shared.registry()
    bg = Shared.bg()
    eta_grid = bg.eta[1:]
    a_grid = bg.a[1:]
    abs_res = np.abs(np.asarray(reg.friedmann_residual(eta_grid)))
    rho_total = np.asarray(reg.rho_total(eta_grid))
    rel_res = abs_res / np.maximum(rho_total, 1.0)

    # Moving-window max-envelope for visual clarity.
    def envelope(x, w=40):
        n = len(x)
        out = np.empty(n)
        for i in range(n):
            lo = max(0, i - w // 2)
            hi = min(n, i + w // 2)
            out[i] = np.max(x[lo:hi])
        return out

    abs_env = envelope(np.clip(abs_res, 1e-30, None))
    rel_env = envelope(np.clip(rel_res, 1e-30, None))

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(a_grid, abs_env, color=COLS["red"], lw=1.4,
            label=r"absolute $|H^2/H_0^2 - \Sigma\rho_s|$")
    ax.plot(a_grid, rel_env, color=COLS["blue"], lw=1.4,
            label=r"relative / $\rho_{\rm tot}(a)$")
    for y_ref, text in [(1e-10, r"$10^{-10}$"), (1e-14, r"$10^{-14}$")]:
        ax.axhline(y_ref, color="0.5", ls=":", lw=0.5)
        ax.text(a_grid.max() * 0.4, y_ref * 1.5, text, fontsize=8,
                 color="0.4", ha="left", va="bottom")
    ax.set_ylim(1e-17, 1e13)
    _prepare_axes(ax, r"$a$", r"residual",
                   title=r"Friedmann-constraint residual (max-envelope, w=40)",
                   xlog=True, ylog=True)
    ax.legend(loc="lower left", fontsize=9)
    _save(fig, "01_residual_vs_eta", TOPIC_07)


def plot_07_02_omega_sum_bar() -> None:
    """Ω_s(z=0) bar chart with sum annotation."""
    reg = Shared.registry()
    c = reg.constants
    from bass.species.base import SpeciesLabel
    vals = {
        r"$\gamma$":      c.Omega_gamma_0,
        r"$\nu$":         c.Omega_nu_0,
        r"$b$":           c.Omega_b_0,
        r"$c$":           c.Omega_c_0,
        r"$\Lambda$":     c.Omega_Lambda_0,
    }
    total = sum(vals.values())
    labels = list(vals.keys())
    values = list(vals.values())
    colors = [SPECIES_COLOR["photon"], SPECIES_COLOR["neutrino"],
              SPECIES_COLOR["baryon"], SPECIES_COLOR["cdm"],
              SPECIES_COLOR["lambda"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.bar(labels, values, color=colors, edgecolor="black", lw=0.5)
    ax1.set_ylabel(r"$\Omega_{s,0}$")
    ax1.set_title(f"Planck 2018 density fractions today (sum = {total:.8f})")
    ax1.grid(True, axis="y", alpha=0.3)

    ax2.bar(labels, values, color=colors, edgecolor="black", lw=0.5)
    ax2.set_yscale("log")
    ax2.set_ylabel(r"$\Omega_{s,0}$ (log)")
    ax2.set_title("Log scale — see γ, ν on the same plot")
    ax2.grid(True, axis="y", alpha=0.3, which="both")
    _save(fig, "02_omega_sum_bar", TOPIC_07)


# ════════════════════════════════════════════════════════════════════
# Topic 08 — Parameter sweeps
# ════════════════════════════════════════════════════════════════════


TOPIC_08 = "08_parameter_sweeps"


def plot_08_01_z_eq_vs_Omega_m() -> None:
    """z_eq = Ω_m / Ω_r − 1 sweep."""
    Omega_m_grid = np.linspace(0.20, 0.40, 41)
    c = default_constants()
    Omega_r = c.Omega_r_0
    z_eq = Omega_m_grid / Omega_r - 1.0
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(Omega_m_grid, z_eq, color=COLS["orange"], lw=1.6)
    ax.axvline(c.Omega_m_0, color="0.3", ls=":", lw=0.8)
    ax.axhline(c.Omega_m_0 / Omega_r - 1.0, color="0.3", ls=":", lw=0.8)
    ax.text(c.Omega_m_0, z_eq.max() * 0.92,
             f"Planck 2018\n$z_{{\\rm eq}}={c.Omega_m_0/Omega_r-1:.0f}$",
             fontsize=9, color="0.3", ha="left")
    _prepare_axes(ax, r"$\Omega_m$", r"$z_{\rm eq}$",
                   title=r"Equality redshift vs $\Omega_m$ (fixed $\Omega_r$)")
    _save(fig, "01_z_eq_vs_Omega_m", TOPIC_08)


def plot_08_02_eta_today_vs_H0() -> None:
    """η_0 and η_* sensitivity to H_0 for several Ω_m."""
    h_vals = np.linspace(0.60, 0.76, 17)
    Omega_m_vals = [0.28, 0.3153, 0.35]
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    cmap = plt.get_cmap("viridis")
    for i, Om in enumerate(Omega_m_vals):
        eta_0 = []
        for h in h_vals:
            Omega_L = 1.0 - Om - default_constants().Omega_r_0
            c_v = dataclasses.replace(
                default_constants(), h=h, H0_km_s_mpc=100 * h,
                Omega_c_0=Om - default_constants().Omega_b_0,
                Omega_Lambda_0=Omega_L,
            )
            bg_v = build_flrw_background_table(constants=c_v, n_eta=1500)
            eta_0.append(bg_v.eta_today)
        ax.plot(100 * h_vals, eta_0,
                 color=cmap(i / (len(Omega_m_vals) - 1)), lw=1.5,
                 marker="o", ms=3, label=f"Ω_m = {Om}")
    _prepare_axes(ax, r"$H_0$ [km/s/Mpc]", r"$\eta_0$ [Mpc]",
                   title=r"Conformal age vs $(H_0, \Omega_m)$")
    ax.legend(loc="upper right", fontsize=9)
    _save(fig, "02_eta_today_vs_H0", TOPIC_08)


def plot_08_03_tau_reion_vs_z_rei() -> None:
    """τ_reion sweep vs z_rei for three Δz values (with/without HeII)."""
    z_rei_vals = np.linspace(5.5, 12.0, 22)
    table, _ = Shared.recomb()
    cosmo = cosmology_from_metadata(table.metadata)

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    for dz, ls in [(0.3, ":"), (0.5, "-"), (0.8, "--")]:
        tau = []
        for z_r in z_rei_vals:
            reion = ReionizationParameters(z_reion_H=z_r, delta_z_H=dz,
                                              include_HeII=True)
            ext_table = extend_table_with_reionization(table, reion,
                                                         cosmology=cosmo)
            tau.append(compute_reionization_tau(ext_table, z_high_cutoff=30.0))
        ax.plot(z_rei_vals, tau, ls=ls, lw=1.4, marker="s", ms=3,
                 label=f"Δz = {dz}")
    ax.axhline(0.0544, color="0.3", ls=":", lw=0.8,
                label=r"Planck 2018: $\tau=0.0544$")
    ax.axhspan(0.0544 - 0.0073, 0.0544 + 0.0073, alpha=0.1, color="0.5")
    _prepare_axes(ax, r"$z_{\rm rei,H}$", r"$\tau_{\rm reion}$",
                   title=r"$\tau_{\rm reion}$ vs midpoint and width (HeII on)")
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "03_tau_reion_vs_z_rei", TOPIC_08)


# ════════════════════════════════════════════════════════════════════
# Topic 09 — PSTF multipole hierarchy (LB-2a)
# ════════════════════════════════════════════════════════════════════


TOPIC_09 = "09_pstf_hierarchy"


def _sym_basis_count(ell: int) -> int:
    """Number of independent rank-ℓ totally-symmetric tensors on 3-space."""
    return (ell + 1) * (ell + 2) // 2


def plot_09_01_stf_dim_vs_symmetric() -> None:
    """dim(PSTF)=2ℓ+1 vs dim(sym)=(ℓ+1)(ℓ+2)/2 for ℓ=0..8."""
    ells = np.arange(L_MAX_CACHED + 1)
    stf = 2 * ells + 1
    sym = np.array([_sym_basis_count(int(l)) for l in ells])
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(ells, sym, marker="s", color=COLS["purple"], lw=1.4,
             label=r"$\dim(\mathrm{Sym}_\ell)=(\ell+1)(\ell+2)/2$")
    ax.plot(ells, stf, marker="o", color=COLS["orange"], lw=1.4,
             label=r"$\dim(\mathrm{PSTF}_\ell)=2\ell+1$")
    ax.fill_between(ells, stf, sym, alpha=0.12, color=COLS["blue"],
                     label="traces removed by STF projection")
    for i, l in enumerate(ells):
        ax.annotate(f"{sym[i]-stf[i]}", (l, 0.5 * (stf[i] + sym[i])),
                     fontsize=7, ha="center", color=COLS["blue"])
    _prepare_axes(ax, r"multipole rank $\ell$",
                   r"number of independent components",
                   title=r"PSTF basis count (trace removal spectrum)")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_xticks(ells)
    _save(fig, "01_stf_dim_vs_symmetric", TOPIC_09)


def plot_09_02_roundtrip_precision() -> None:
    """Packed → full → packed round-trip error vs ℓ on random inputs."""
    rng = np.random.default_rng(2026)
    n_samples = 40
    ells = np.arange(L_MAX_CACHED + 1)
    max_err = np.zeros_like(ells, dtype=np.float64)
    mean_err = np.zeros_like(ells, dtype=np.float64)
    for i, ell in enumerate(ells):
        errs = []
        for _ in range(n_samples):
            c = rng.normal(size=2 * int(ell) + 1)
            T = pstf_unpack(c, int(ell))
            c_rt = pstf_pack(T)
            errs.append(float(np.max(np.abs(c - c_rt))))
        max_err[i] = max(np.max(errs), 1e-17)
        mean_err[i] = max(np.mean(errs), 1e-17)
    # Machine-precision × 3^ℓ reference line.
    ref = np.finfo(np.float64).eps * (3.0 ** ells)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.semilogy(ells, max_err, marker="o", color=COLS["orange"], lw=1.4,
                 label=r"max $\|c-c_{\rm rt}\|_\infty$")
    ax.semilogy(ells, mean_err, marker="s", color=COLS["blue"], lw=1.4,
                 label=r"mean $\|c-c_{\rm rt}\|_\infty$")
    ax.semilogy(ells, ref, color="0.3", ls=":", lw=1.0,
                 label=r"$\varepsilon_{\rm mach}\times 3^\ell$ reference")
    _prepare_axes(ax, r"multipole rank $\ell$",
                   r"round-trip error  [flat-basis coords]",
                   title=r"PSTF packed$\leftrightarrow$full round-trip precision")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_xticks(ells)
    _save(fig, "02_roundtrip_precision", TOPIC_09)


def plot_09_03_term_prefactors() -> None:
    """Analytic prefactors of the nine-term hierarchy vs ℓ."""
    ells = np.arange(2, L_MAX_CACHED + 1)
    T1_pre = np.full_like(ells, 4.0 / 3.0, dtype=np.float64)
    T3_pre = (ells + 1.0) / (2.0 * ells + 3.0)
    T7_pre = -((ells - 1.0) * (ells + 1.0) * (ells + 2.0)) / (
        (2.0 * ells + 3.0) * (2.0 * ells + 5.0)
    )
    T8_pre = 5.0 * ells / (2.0 * ells + 3.0)
    T9_pre = -(ells + 2.0)
    fig, ax = plt.subplots(figsize=(6.8, 4.3))
    ax.plot(ells, T1_pre, marker="o", color=COLS["orange"], lw=1.4,
             label=r"$T_1:\ (4/3)\Theta$")
    ax.plot(ells, T8_pre, marker="s", color=COLS["blue"], lw=1.4,
             label=r"$T_8:\ 5\ell/(2\ell+3)$ (shear stays)")
    ax.plot(ells, T9_pre, marker="D", color=COLS["purple"], lw=1.4,
             label=r"$T_9:\ -(\ell+2)$ (shear $\ell\!\to\!\ell-2$)")
    ax.plot(ells, T3_pre, marker="v", color=COLS["cyan"], lw=1.4,
             label=r"$T_3:\ (\ell+1)/(2\ell+3)$ (divergence)")
    ax.plot(ells, T7_pre, marker="^", color=COLS["green"], lw=1.4,
             label=r"$T_7:\ -(\ell-1)(\ell+1)(\ell+2)/[(2\ell+3)(2\ell+5)]$")
    ax.axhline(0.0, color="0.3", lw=0.6)
    _prepare_axes(ax, r"multipole rank $\ell$", "prefactor",
                   title="Nine-term hierarchy prefactors (LB-2a/b)")
    ax.legend(loc="lower left", fontsize=8)
    ax.set_xticks(ells)
    _save(fig, "03_term_prefactors", TOPIC_09)


def plot_09_04_stf_basis_ell2_tensors() -> None:
    """The five ℓ=2 orthonormal STF basis tensors as 3×3 heatmaps.

    Note: the columns of ``Q_ℓ`` come from the QR orthonormalisation of
    the null space of the trace operator, so their ordering is a
    basis-adapted convention — not the spherical-harmonic m ordering.
    Any rotation within the 5-D STF subspace would produce an
    equally-valid basis; the invariants (symmetry, trace-free,
    orthonormality) hold column-wise.
    """
    Q = stf_basis(2)  # (9, 5)
    fig, axes = plt.subplots(1, 5, figsize=(12.0, 2.8), constrained_layout=True)
    vmax = float(np.max(np.abs(Q)))
    for m_idx, ax in enumerate(axes):
        T = Q[:, m_idx].reshape(3, 3)
        im = ax.imshow(T, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        ax.set_title(rf"basis col {m_idx+1}/5", fontsize=10)
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["x", "y", "z"])
        ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["x", "y", "z"])
        ok, _ = verify_pstf_invariants(T, tol=1e-10)
        ax.text(0.5, -0.25, "PSTF ok" if ok else "violating",
                 ha="center", transform=ax.transAxes, fontsize=8,
                 color=(COLS["green"] if ok else COLS["orange"]))
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.85,
                         aspect=12, pad=0.02)
    cbar.set_label("amplitude (orthonormal basis)")
    fig.suptitle(
        r"$\ell=2$ PSTF orthonormal basis $Q_{2}$ — 5 independent components "
        "(QR-ordered)",
        fontsize=11,
    )
    path = GALLERY_ROOT / TOPIC_09
    path.mkdir(parents=True, exist_ok=True)
    out = path / "04_stf_basis_ell2_tensors.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"  [ok] {TOPIC_09}/04_stf_basis_ell2_tensors.png")


def plot_09_05_T9_shear_quadrupole() -> None:
    """T9 at ℓ=2 as a function of Σ_+ and Π_0 (shear-to-quadrupole injection)."""
    sigma_plus_grid = np.linspace(-0.10, 0.10, 41)
    Pi0_grid = np.array([0.25, 0.5, 1.0, 2.0])
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.5, 4.2))
    # Left: T9 trace-norm vs Σ_+ for a few monopole amplitudes.
    for k, pi0 in enumerate(Pi0_grid):
        norms = []
        for sp in sigma_plus_grid:
            sigma = axisymmetric_sigma_tensor(sigma_plus=float(sp),
                                                sigma_minus=0.0)
            T9 = T9_shear_down(ell=2,
                                Pi_ell_minus_2_full=np.array(float(pi0)),
                                sigma_tensor=sigma)
            norms.append(np.sqrt(np.sum(T9 ** 2)))
        ax_a.plot(sigma_plus_grid, norms, marker=".",
                   color=plt.get_cmap("viridis")(k / (len(Pi0_grid) - 1)),
                   lw=1.4, label=rf"$\Pi_0={pi0}$")
    ax_a.axhline(0.0, color="0.3", lw=0.6)
    _prepare_axes(ax_a, r"$\Sigma_+$ (axisymmetric shear)",
                   r"$\|T_9\|_{\rm F}=4|\Sigma_+\Pi_0|$",
                   title=r"$T_9$ norm vs $\Sigma_+$ at $\ell=2$")
    ax_a.legend(loc="upper center", fontsize=8)
    # Right: T9_ab entries at Σ_+=0.05, Π_0=1.0 decomposed over m.
    sigma = axisymmetric_sigma_tensor(sigma_plus=0.05, sigma_minus=0.0)
    T9 = T9_shear_down(ell=2, Pi_ell_minus_2_full=np.array(1.0),
                        sigma_tensor=sigma)
    Q2 = stf_basis(2)
    m_coefs = Q2.T @ T9.reshape(-1)
    idx = np.arange(1, 6)
    bar_colors = [
        COLS["purple"] if abs(v) > 0.5 * float(np.max(np.abs(m_coefs)))
        else COLS["blue"]
        for v in m_coefs
    ]
    ax_b.bar(idx, m_coefs, color=bar_colors)
    ax_b.axhline(0.0, color="0.3", lw=0.6)
    _prepare_axes(ax_b, r"PSTF basis column (QR-ordered, ${1..5}$)",
                   r"$c_i$  (packed amplitude)",
                   title=r"$T_9$ decomposition at $\Sigma_+=0.05,\ \Pi_0=1$")
    ax_b.set_xticks(idx)
    # Annotate the Frobenius-norm consistency check.
    norm_expected = 4.0 * 0.05 * 1.0
    norm_from_coefs = float(np.sqrt(np.sum(m_coefs ** 2)))
    ax_b.text(
        0.5, 0.94,
        rf"$\|T_9\|_{{\rm F}}=4|\Sigma_+||\Pi_0|={norm_expected:.3f}$"
        f"\n"
        rf"$\sqrt{{\sum c_i^2}}={norm_from_coefs:.3f}$"
        "  (QR-basis not axisymmetric-aligned)",
        transform=ax_b.transAxes, ha="center", va="top",
        fontsize=8, color="0.3",
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="0.7",
                   boxstyle="round,pad=0.3"),
    )
    fig.tight_layout()
    _save(fig, "05_T9_shear_quadrupole", TOPIC_09)


def plot_09_06_T8_shear_spectrum() -> None:
    """T8 norm scaled by prefactor vs ℓ with fixed σ and a random PSTF Π."""
    ells = np.arange(1, L_MAX_CACHED + 1)
    sigma = axisymmetric_sigma_tensor(sigma_plus=0.1, sigma_minus=0.0)
    rng = np.random.default_rng(999)
    # Fixed ||Π_ell||_F for fair comparison across ℓ.
    norms_raw = np.zeros_like(ells, dtype=np.float64)
    norms_full = np.zeros_like(ells, dtype=np.float64)
    prefactors = 5.0 * ells / (2.0 * ells + 3.0)
    for i, ell in enumerate(ells):
        c = rng.normal(size=2 * int(ell) + 1)
        c /= np.linalg.norm(c)  # ||Π||_F = 1 in the packed basis
        T = pstf_unpack(c, int(ell))
        T8 = T8_shear_same(ell=int(ell), Pi_ell_full=T, sigma_tensor=sigma)
        norms_full[i] = float(np.sqrt(np.sum(T8 ** 2)))
        # Subtract the prefactor so the remaining curve is the operator norm
        # of the bare sym-trace-free(σ-contraction).
        norms_raw[i] = norms_full[i] / prefactors[i]
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(ells, norms_full, marker="o", color=COLS["blue"], lw=1.4,
             label=r"$\|T_8\|_{\rm F}$")
    ax.plot(ells, norms_raw, marker="s", color=COLS["purple"], lw=1.4,
             label=r"$\|T_8\|_{\rm F} / (5\ell/(2\ell+3))$ (bare)")
    ax.axhline(float(np.sqrt(np.sum(sigma ** 2))), color="0.3", ls=":", lw=0.8,
                label=r"$\|\sigma\|_{\rm F}$")
    _prepare_axes(ax, r"multipole rank $\ell$",
                   r"Frobenius norm",
                   title=r"$T_8$ shear-stays-at-$\ell$ on normalised random $\Pi_\ell$")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_xticks(ells)
    _save(fig, "06_T8_shear_spectrum", TOPIC_09)


def plot_09_07_T1_damping_history() -> None:
    """(4/3)Θ(η) damping rate across cosmological history."""
    bg = Shared.bg()
    Theta = bg.Theta
    # Use z = 1/a - 1 for the x-axis; clip to the CMB-era+inflation viewport.
    z = 1.0 / np.maximum(bg.a, 1e-300) - 1.0
    mask = z <= 2.0e4  # back to shortly after BBN
    z_m = z[mask]
    damp = (4.0 / 3.0) * Theta[mask]
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.5, 4.0))
    # Left: damping rate vs z on log-log.
    ax_a.loglog(1 + z_m, damp, color=COLS["orange"], lw=1.6)
    ax_a.axvline(1 + 1089.94, color="0.3", ls=":", lw=0.7)
    ax_a.text(1 + 1089.94, damp.max() * 0.2, r" $z_*$",
                fontsize=9, color="0.3")
    ax_a.axvline(1 + 3400.0, color="0.3", ls=":", lw=0.7)
    ax_a.text(1 + 3400.0, damp.max() * 0.05, r" $z_{\rm eq}$",
                fontsize=9, color="0.3")
    _prepare_axes(ax_a, r"$1+z$",
                   r"$(4/3)\Theta\ [\mathrm{Mpc}^{-1}]$",
                   title=r"$T_1$ expansion damping rate (BBN $\to$ today)")
    # Right: apply T1 to a unit-norm Π_2 and track resulting norm.
    Pi2 = axisymmetric_sigma_tensor(1.0, 0.0)
    Pi2 /= np.sqrt(np.sum(Pi2 ** 2))
    T1_norm = np.array([
        float(np.sqrt(np.sum(T1_expansion(2, Pi2, float(th)) ** 2)))
        for th in Theta[mask]
    ])
    ax_b.loglog(1 + z_m, T1_norm, color=COLS["blue"], lw=1.6,
                 label=r"$\|T_1(\Pi_2)\|_{\rm F}$, unit $\Pi_2$")
    ax_b.axvline(1 + 1089.94, color="0.3", ls=":", lw=0.7)
    ax_b.axvline(1 + 3400.0, color="0.3", ls=":", lw=0.7)
    _prepare_axes(ax_b, r"$1+z$",
                   r"$\|T_1\|_{\rm F}\ [\mathrm{Mpc}^{-1}]$",
                   title=r"Damping applied to normalised $\Pi_2$")
    ax_b.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    _save(fig, "07_T1_damping_history", TOPIC_09)


def plot_09_08_shear_injection_over_time() -> None:
    """T9 at ℓ=2 over Bianchi-I history with a decaying Σ_+.

    Uses the Y-Block ``solve_bianchi_background`` with Bianchi I seed
    to obtain Σ_+(η); the quadrupole source from a unit monopole is
    then ``-4 Σ_+(η)/a(η) × diag(-2,1,1)/√6``. This is the structural
    shear-to-CMB-quadrupole injection in proper-time units.
    """
    # Reuse the logic from Topic 05: Bianchi I with a moderate initial seed.
    sigma_over_H_seed = 5e-3
    cosmo = BianchiCosmology(
        structure=type_i_constants(),
        sigma_over_H_init=sigma_over_H_seed,
        sigma_pm_ratio=0.0,
    )
    bg = solve_bianchi_background(cosmo, n_pts=1500)
    a = np.asarray(bg.a)
    Sigma_plus = np.asarray(bg.sigma_plus)
    # Convert conformal Σ_+ (Pontzen convention) to proper σ_+ via 1/a.
    sigma_plus_proper = Sigma_plus / np.maximum(a, 1e-30)
    # Compute ||T9||_F as a function of η with Π_0 = 1 (monopole = 1).
    T9_norm = np.zeros_like(a)
    for i, sp in enumerate(sigma_plus_proper):
        sigma = axisymmetric_sigma_tensor(float(sp), 0.0)
        T9 = T9_shear_down(ell=2, Pi_ell_minus_2_full=np.array(1.0),
                            sigma_tensor=sigma)
        T9_norm[i] = float(np.sqrt(np.sum(T9 ** 2)))
    z = 1.0 / np.maximum(a, 1e-300) - 1.0
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.5, 4.0))
    # Left: proper σ_+(η) and |Σ_+(η)| side-by-side.
    ax_a.loglog(1 + z, np.abs(Sigma_plus), color=COLS["orange"], lw=1.4,
                 label=r"$|\Sigma_+|$ (dimensionless)")
    ax_a.loglog(1 + z, np.abs(sigma_plus_proper), color=COLS["blue"], lw=1.4,
                 label=r"$|\sigma_+|=|\Sigma_+|/a\ [\mathrm{Mpc}^{-1}]$")
    _prepare_axes(ax_a, r"$1+z$",
                   "shear amplitude",
                   title=r"Bianchi I shear history (seed $\sigma/H=5\times10^{-3}$)")
    ax_a.legend(loc="lower left", fontsize=8)
    # Right: ||T9|| at ℓ=2 with unit monopole.
    ax_b.loglog(1 + z, T9_norm, color=COLS["purple"], lw=1.6)
    ax_b.axvline(1 + 1089.94, color="0.3", ls=":", lw=0.7)
    ax_b.text(1 + 1089.94, T9_norm.max() * 0.3, r"$z_*$",
                fontsize=9, color="0.3")
    _prepare_axes(ax_b, r"$1+z$",
                   r"$\|T_9\|_{\rm F}\ [\mathrm{Mpc}^{-1}]$",
                   title=r"$T_9$ injected quadrupole $(\Pi_0=1)$")
    fig.tight_layout()
    _save(fig, "08_shear_injection_over_time", TOPIC_09)


# ════════════════════════════════════════════════════════════════════
# Catalog
# ════════════════════════════════════════════════════════════════════


CATALOG: Dict[str, List[Tuple[str, Callable[[], None], str]]] = {
    TOPIC_01: [
        ("01_omega_evolution_log", plot_01_omega_evolution_log,
         "Ω_s(z) on log-log for all 5 species."),
        ("02_rho_invariance", plot_02_rho_invariance,
         "ρ_s × a^{3(1+w)} invariance sanity check."),
        ("03_temperature_overlay", plot_03_temperature_overlay,
         "T_γ, T_ν, T_m(HyRec) overlay — Compton decoupling visible."),
        ("04_equality_crossover", plot_04_equality_crossover,
         "Radiation-matter equality zoom."),
        ("05_w_evolution", plot_05_w_evolution,
         "Equation of state w_s(z) per species."),
        ("06_rho_total_stack", plot_06_rho_total_stack,
         "Stacked Ω_s(a)/Ω_tot(a) composition history."),
    ],
    TOPIC_02: [
        ("01_scale_factor_vs_eta", plot_02_01_a_of_eta,
         "a(η) with η_eq, η_*, η_0 markers."),
        ("02_hubble_vs_a", plot_02_02_hubble_vs_a,
         "H(a) vs asymptotic radiation / matter / Λ scalings."),
        ("03_conformal_hubble", plot_02_03_conformal_hubble,
         "Conformal Hubble 𝓗(η) with peak."),
        ("04_eta_of_z", plot_02_04_eta_of_z,
         "Conformal distance η_0 − η(z) with CMB marker."),
        ("05_H0_sensitivity", plot_02_05_H0_sensitivity,
         "η_0 and η_0 − η_* sweep over H_0."),
        ("06_Omega_m_sensitivity", plot_02_06_Omega_m_sensitivity,
         "η_0 and z_eq sensitivity to Ω_m."),
    ],
    TOPIC_03: [
        ("01_x_e_full", plot_03_01_x_e_full,
         "HyRec-2 free-electron fraction over full z range."),
        ("02_T_m_vs_T_gamma", plot_03_02_T_m_vs_T_gamma,
         "Matter vs photon temperature + ratio panel."),
        ("03_tau_dot", plot_03_03_tau_dot,
         "Differential optical depth τ̇(z)."),
        ("04_kappa_cumulative", plot_03_04_kappa_cumulative,
         "Cumulative κ(z) and z_*."),
        ("05_visibility_peak", plot_03_05_visibility_peak,
         "g(z) visibility with peak annotation."),
        ("06_visibility_eta", plot_03_06_visibility_eta,
         "g(η) in conformal-time space with FWHM."),
    ],
    TOPIC_04: [
        ("01_tanh_profile_sweep", plot_04_01_tanh_profile_sweep,
         "Reionization x_e profile across z_rei_H sweep."),
        ("02_combined_xe", plot_04_02_combined_xe,
         "Recomb + reion overlay."),
        ("03_tau_reion_sweep", plot_04_03_tau_reion_sweep,
         "τ_reion vs z_rei_H with Planck 2018 band."),
        ("04_HeII_on_off", plot_04_04_HeII_on_off,
         "HeII second reionization effect on x_e."),
        ("05_visibility_with_reion", plot_04_05_visibility_with_reion,
         "g(z) including reionization bump."),
    ],
    TOPIC_05: [
        ("01_Sigma2_decay_types", plot_05_01_Sigma2_decay_types,
         "Σ²(a) for Bianchi I, V, VII₀."),
        ("02_sigma_pm_timeseries", plot_05_02_sigma_pm_timeseries,
         "Σ_+(η), Σ_-(η) for different σ_-/σ_+ ratios."),
        ("03_sigma_pm_phaseplane", plot_05_03_sigma_pm_phaseplane,
         "Phase-plane trajectories in (Σ_+, Σ_-)."),
        ("04_a_minus_4_law", plot_05_04_a_minus_4_law,
         "Σ² × a^n vs a for n ∈ {2,3,4,5,6}."),
        ("05_seed_sweep", plot_05_05_seed_sweep,
         "Initial σ/H seed dependence."),
    ],
    TOPIC_06: [
        ("01_gamma_e_vs_beta", plot_06_01_gamma_e_vs_beta,
         "Non-perturbative γ_e(β) vs quadratic truncation."),
        ("02_boost_factor_heatmap", plot_06_02_boost_factor_heatmap,
         "B(β, cos θ) = cosh β + sinh β cos θ heatmap."),
        ("03_boost_directional_slice", plot_06_03_boost_directional_slice,
         "Forward/backward asymmetry slices."),
        ("04_linear_vs_exact", plot_06_04_linear_vs_exact,
         "Non-perturbative vs (1 + v·e) linearisation error."),
    ],
    TOPIC_07: [
        ("01_residual_vs_eta", plot_07_01_residual_vs_eta,
         "Friedmann residual across history."),
        ("02_omega_sum_bar", plot_07_02_omega_sum_bar,
         "Ω_s(0) bar chart in linear + log scale."),
    ],
    TOPIC_08: [
        ("01_z_eq_vs_Omega_m", plot_08_01_z_eq_vs_Omega_m,
         "z_eq vs Ω_m parameter sweep."),
        ("02_eta_today_vs_H0", plot_08_02_eta_today_vs_H0,
         "η_0 vs H_0 for multiple Ω_m."),
        ("03_tau_reion_vs_z_rei", plot_08_03_tau_reion_vs_z_rei,
         "τ_reion sensitivity to z_rei and Δz."),
    ],
    TOPIC_09: [
        ("01_stf_dim_vs_symmetric", plot_09_01_stf_dim_vs_symmetric,
         "PSTF independent-component count (2ℓ+1) vs symmetric (ℓ+1)(ℓ+2)/2."),
        ("02_roundtrip_precision", plot_09_02_roundtrip_precision,
         "Packed ↔ full-tensor round-trip error vs ℓ with ε·3^ℓ reference."),
        ("03_term_prefactors", plot_09_03_term_prefactors,
         "T1/T3/T7/T8/T9 analytic prefactors as functions of ℓ."),
        ("04_stf_basis_ell2_tensors", plot_09_04_stf_basis_ell2_tensors,
         "The five ℓ=2 orthonormal STF basis tensors as 3×3 heatmaps."),
        ("05_T9_shear_quadrupole", plot_09_05_T9_shear_quadrupole,
         "T9 shear-to-quadrupole injection sweep in (Σ_+, Π_0) + m-spectrum."),
        ("06_T8_shear_spectrum", plot_09_06_T8_shear_spectrum,
         "T8 shear-stays-at-ℓ norm on normalised random Π_ℓ across ℓ."),
        ("07_T1_damping_history", plot_09_07_T1_damping_history,
         "(4/3)Θ(η) damping rate + its action on a unit Π_2 over history."),
        ("08_shear_injection_over_time", plot_09_08_shear_injection_over_time,
         "Bianchi I Σ_+(η) → proper σ_+(η) → ||T9|| at ℓ=2 with Π_0=1."),
    ],
}


def run(topics: List[str] = None) -> None:
    apply_style()
    matplotlib.rcParams.update({
        "axes.titlesize": 10,
        "axes.labelsize": 10,
        "legend.fontsize": 8,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
    })
    GALLERY_ROOT.mkdir(parents=True, exist_ok=True)
    selected = topics if topics else list(CATALOG.keys())
    total = sum(len(CATALOG[t]) for t in selected)
    print(f"Rendering {total} plots across {len(selected)} topics to "
           f"{GALLERY_ROOT.relative_to(REPO_ROOT)}/")
    for topic in selected:
        print(f"\n[{topic}]")
        for name, fn, desc in CATALOG[topic]:
            try:
                fn()
            except Exception as exc:  # pragma: no cover - diagnostic
                print(f"  [FAIL] {name}: {type(exc).__name__}: {exc}")


def list_catalog() -> None:
    print(f"Gallery output root: {GALLERY_ROOT.relative_to(REPO_ROOT)}/")
    for topic, entries in CATALOG.items():
        print(f"\n{topic}/")
        for name, _, desc in entries:
            print(f"  {name}.png — {desc}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--only", nargs="*",
                    help="subset of topic directories (e.g. 01_species_background)")
    p.add_argument("--list", action="store_true",
                    help="list catalog and exit")
    args = p.parse_args()
    if args.list:
        list_catalog()
        return
    topics = args.only if args.only else None
    run(topics)


if __name__ == "__main__":
    main()
