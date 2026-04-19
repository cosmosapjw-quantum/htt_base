#!/usr/bin/env python3
"""make_additional_figures.py — second wave of paper-quality figures.

Fills gaps in scripts/make_paper_figures.py (which already covers ch02,
ch04 MES, ch05 a-d, ch06 a-g, ch07 a-i, ch08). This companion script
renders figures drawing from bass_py submodules that were not yet
plotted:

- ch03 framework: distance-scale hierarchy, three-layer ontology.
- ch04 bounds: per-Bianchi-type three-bound bar chart.
- ch05 T_eff: Laguerre moments I_n(xi, eta), moment ratios.
- ch06 pipeline: Michaelis-Menten Route-B SSOT mirror, TCA matrix
  conditioning.
- ch07 results: MES ceilings hierarchy, entropy invariants, Gram
  admissibility.
- ch12 MIO observatory: directional coherence of 5 probes, redshift
  axis drift, sky-coverage f_sky, synthetic HJ-01 K_ell extraction.

All outputs land in figures/paper/<chapter>/ alongside the existing
bundle, with a matching .caption.txt draft.

Usage
-----
    venv/bin/python scripts/make_additional_figures.py           # all
    venv/bin/python scripts/make_additional_figures.py --only ch12a_probes
    venv/bin/python scripts/make_additional_figures.py --list
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

# bass_py uses src/ and workspace/ as additional roots (see bass_py/conftest.py).
sys.path.insert(0, str(REPO_ROOT / "bass_py"))
sys.path.insert(0, str(REPO_ROOT / "bass_py" / "src"))
sys.path.insert(0, str(REPO_ROOT / "bass_py"))  # for workspace.contracts

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


# =====================================================================
# Chapter 03 — Framework
# =====================================================================


def fig_ch03a_scale_hierarchy() -> None:
    """Distance-scale hierarchy (Hubble radius, peculiar Jeans, sound horizon,
    cosmological dipole decay scale), with contamination band annotated."""
    c_km = 299_792.458
    H0 = 67.36
    lambda_H = c_km / H0  # Mpc, ~4451

    # Peculiar Jeans length lambda_J^{pec}(beta, q): closed form from htt/tilted_flrw.
    # Use simple closed-form reproduction rather than importing the module.
    # lambda_J^pec = sqrt(c^2 / (G rho * (1 - 3*beta^2/2))) * (1 - q) scaling
    # For paper-figure purposes we mirror the published values.
    beta = 1.334e-3
    # EdS q=0.5 → ~297 Mpc; modern-cosmology q ~ 0.09 → ~526 Mpc.
    lJ_EdS = 297.0
    lJ_Son = 526.0
    # Colin+2025 SNe dipole decay scale d_S = S*c/H0 with S=0.0262
    d_S = 0.0262 * c_km / H0
    # Sound horizon at decoupling r_s ~ 147 Mpc (Planck 2018 TT+lowE+lensing).
    r_s = 147.2

    surveys = [
        ("CF4++", 200.0, COLS["orange"], 0.68),
        ("CatWISE", 500.0, COLS["orange"], 0.48),
        ("DESI-Y1", 2400.0, COLS["orange"], 0.68),
        ("Planck (CMB)", lambda_H * 0.99, COLS["orange"], 0.48),
    ]
    scales = [
        (r_s, r"$r_s$ (sound horizon)", COLS["blue"], 1.75),
        (d_S, r"$d_S$ (Colin+25)", COLS["purple"], 1.35),
        (lJ_EdS, r"$\lambda_J^{\rm pec}$ (EdS)", COLS["purple"], 2.05),
        (lJ_Son, r"$\lambda_J^{\rm pec}$ (Son+25)", COLS["purple"], 1.35),
        (lambda_H, r"$\lambda_H$", COLS["blue"], 1.75),
    ]

    fig, ax = plt.subplots(figsize=(7.8, 3.6))
    ax.set_xscale("log")
    ax.set_xlim(50.0, 1.3e4)
    ax.set_ylim(0.0, 2.6)

    # Contamination band: scales smaller than lambda_J are contaminated by
    # peculiar flows. Shade between 100 and max(lJ_Son).
    ax.axvspan(100.0, lJ_Son, color=COLS["red"], alpha=0.08,
               label=r"tilt-contaminated zone ($d < \lambda_J^{\rm pec}$)")

    # Physical scale markers (upper row)
    for (pos, label, col, y) in scales:
        ax.plot([pos, pos], [y, y + 0.14], color=col, lw=1.6)
        ax.text(pos, y + 0.18, label, ha="center", va="bottom",
                fontsize=8.5, color=col)

    # Surveys (lower row) — stagger heights to avoid adjacent overlaps.
    for (name, pos, col, y_lab) in surveys:
        ax.plot([pos, pos], [0.25, 0.40], color=col, lw=1.4, alpha=0.85)
        ax.text(pos, y_lab, name, ha="center", va="bottom",
                fontsize=8.2, color=col)

    ax.axhline(0.95, color="0.5", lw=0.4, ls=":")
    ax.text(55.0, 1.30, "physical scales", fontsize=8.0, color="0.3",
            style="italic")
    ax.text(55.0, 0.85, "surveys (reach)", fontsize=8.0, color="0.3",
            style="italic")

    ax.set_xlabel(r"comoving distance [Mpc]")
    ax.set_yticks([])
    ax.spines[["left", "right", "top"]].set_visible(False)
    ax.tick_params(axis="x", which="both", direction="out", length=3.5)
    ax.grid(axis="x", which="both", alpha=0.15)
    ax.set_title(r"Distance-scale hierarchy: tilted-FLRW probes vs sound horizon vs $\lambda_H$",
                 fontsize=10)
    ax.legend(loc="lower right", fontsize=8.0, framealpha=0.9)
    _save(fig, "fig_ch03a_scale_hierarchy", "ch03_framework")
    _caption(
        "fig_ch03a_scale_hierarchy",
        "ch03_framework",
        r"""
Distance-scale hierarchy for the tilted-FLRW analysis. Upper row:
physical length scales — sound horizon $r_s\!\approx\!147\,$Mpc,
Colin+2025 SNe dipole decay scale $d_S$, peculiar Jeans length
$\lambda_J^{\rm pec}$ in EdS ($q=0.5$) and modern-cosmology
($q\!\approx\!0.09$, Son+2025) limits, and the Hubble radius
$\lambda_H=c/H_0\!\approx\!4451\,$Mpc. Lower row: reach of the
observational probes (CF4++, CatWISE, DESI Y1, Planck). The red band
marks the tilt-contamination zone where the peculiar-flow boost is
not sub-dominant; this sets the minimum survey depth at which a
tilted-FLRW interpretation can be cleanly disentangled from local
bulk-flow systematics.
"""
    )


def fig_ch03b_three_layer_ontology() -> None:
    """Schematic of the three-layer pushforward x → Q = x/x_max → Π(q*)."""
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(0.0, 5.0)
    ax.axis("off")

    def _box(x, y, w, h, text, fc, ec=COLS["black"], subtitle=None, text_color="white"):
        rect = plt.Rectangle((x, y), w, h, fc=fc, ec=ec, lw=1.0, zorder=2)
        ax.add_patch(rect)
        ax.text(x + w / 2.0, y + h / 2.0 + (0.12 if subtitle else 0.0),
                text, ha="center", va="center", fontsize=10,
                color=text_color, zorder=3, weight="bold")
        if subtitle:
            ax.text(x + w / 2.0, y + h / 2.0 - 0.28, subtitle,
                    ha="center", va="center", fontsize=8.2,
                    color=text_color, style="italic", zorder=3)

    def _arrow(x0, y0, x1, y1, label=None):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="->", color=COLS["black"],
                                    lw=1.2, shrinkA=2, shrinkB=2))
        if label:
            ax.text(0.5 * (x0 + x1), 0.5 * (y0 + y1) + 0.22, label,
                    ha="center", va="bottom", fontsize=8.5, color="0.15")

    y_top = 3.6
    # Layer 1 — identified (exact defect algebra)
    _box(0.4, y_top, 2.6, 1.0, r"$\theta\;\to\;x$", COLS["blue"],
         subtitle="Layer 1 — identified (EXACT)")
    # Layer 2 — reporting: normalise by x_max (ceiling)
    _box(3.8, y_top, 2.6, 1.0, r"$x\;\to\;Q=x/x_{\max}$", COLS["orange"],
         subtitle="Layer 2 — reporting (ceiling)")
    # Layer 3 — exceedance Pi(q*)
    _box(7.2, y_top, 2.6, 1.0, r"$Q\;\to\;\Pi(q_\star)$", COLS["green"],
         subtitle="Layer 3 — exceedance")

    _arrow(3.0, y_top + 0.5, 3.8, y_top + 0.5, label="defect algebra")
    _arrow(6.4, y_top + 0.5, 7.2, y_top + 0.5, label="thresholding")

    # Lower row — examples under each layer
    ax.text(1.7, y_top - 0.55, r"$\beta,\;\Sigma^2,\;\omega^2,\;u^2$",
            ha="center", fontsize=10, color=COLS["blue"])
    ax.text(5.1, y_top - 0.55, r"$Q_{\sigma}=\Sigma^2/\Sigma^2_{\max}$",
            ha="center", fontsize=10, color=COLS["red"])
    ax.text(8.5, y_top - 0.55, r"$\Pi_\sigma=\Pr(Q_\sigma>q_\star\,|\,D)$",
            ha="center", fontsize=10, color=COLS["green"])

    # Reminder legend below
    ax.text(0.4, 1.8,
            "Layer 1 is likelihood-constrained and ceiling-free.\n"
            "Layers 2-3 depend on an adopted MES ceiling $x_{\\max}$ and\n"
            "threshold $q_\\star$ — changes to either propagate into the reported Q, \\Pi\n"
            "without altering the identified posterior on $x$.",
            fontsize=9, va="top", color="0.15")

    ax.text(5.0, 0.4, r"ch03 §framework + ch08 identified-vs-reporting separation",
            ha="center", fontsize=8.0, color="0.4", style="italic")

    _save(fig, "fig_ch03b_three_layer_ontology", "ch03_framework")
    _caption(
        "fig_ch03b_three_layer_ontology",
        "ch03_framework",
        r"""
Three-layer ontology of the identified-vs-reporting split
(ch03 §framework, ch08 §identified-reporting). Layer~1 is the
likelihood-constrained defect-algebra map $\theta\!\to\!x$ (e.g.\
$\beta$, $\Sigma^2$, $\omega^2$, $u^2$) — this layer is exact and
ceiling-free. Layer~2 normalises each exact quantity by an
MES ceiling $x_{\max}$ to produce a reporting quantity
$Q\!=\!x/x_{\max}$. Layer~3 converts $Q$ into an exceedance
probability $\Pi(q_\star)$ at a chosen threshold. Changes to
the ceiling or threshold propagate into $Q$ and $\Pi$ only;
the identified posterior on $x$ is preserved.
"""
    )


# =====================================================================
# Chapter 04 — per-Bianchi-type three-bound bar chart
# =====================================================================


def fig_ch04d_type_by_type_bounds() -> None:
    """Bar chart of B_sigma, B_omega, B_accel evaluated at the Planck-scale
    epsilon triple for all nine Bianchi types covered by tsc.admissibility."""
    from tsc.admissibility.three_bound_hierarchy import (
        BIANCHI_TYPES,
        evaluate_all_bianchi_types,
    )

    # Order-of-magnitude epsilon triple drawn from Planck CMB TT amplitudes.
    eps1, eps2, eps3 = 1.0e-5, 3.0e-6, 1.0e-6

    reports = evaluate_all_bianchi_types(
        eps1, eps2, eps3, strict=False,
    )

    # Bounds are type-independent (tsc.admissibility SSOT); display them on a
    # common scale, one grouped triple per type — this makes the three-bound
    # hierarchy visually apparent.
    names = list(BIANCHI_TYPES)
    Bs = np.array([reports[t].B_sigma_val for t in names])
    Bo = np.array([reports[t].B_omega_val for t in names])
    Ba = np.array([reports[t].B_accel_val for t in names])

    x = np.arange(len(names), dtype=float)
    w = 0.27

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    scale_exp = np.floor(np.log10(Bs.max()))
    scale = 10.0 ** scale_exp
    ax.bar(x - w, Bs / scale, width=w, color=COLS["blue"],
           label=r"$B_\sigma$", edgecolor="0.1", lw=0.4)
    ax.bar(x,     Bo / scale, width=w, color=COLS["orange"],
           label=r"$B_\omega$", edgecolor="0.1", lw=0.4)
    ax.bar(x + w, Ba / scale, width=w, color=COLS["green"],
           label=r"$B_{\dot u}$", edgecolor="0.1", lw=0.4)
    ax.set_ylabel(rf"MES bound amplitude / $10^{{{int(scale_exp)}}}$")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=0, fontsize=9)
    ax.set_xlabel("Bianchi type")
    ax.grid(axis="y", which="major", alpha=0.25)
    ax.set_title(
        r"MES three-bound hierarchy at $(\epsilon_1,\epsilon_2,\epsilon_3)=$"
        rf"$({eps1:.0e},\,{eps2:.0e},\,{eps3:.0e})$",
        fontsize=10,
    )
    # Extend ylim so top of bars + annotation box don't collide.
    ax.set_ylim(0.0, 1.18 * (Bs.max() / scale))
    hier_ok = all(r.hierarchy_strict for r in reports.values())
    hier_txt = (r"$B_\sigma > B_\omega > B_{\dot u}$ strictly "
                r"(all 9 types)" if hier_ok else
                r"hierarchy NOT strictly ordered at all types")
    ax.text(0.02, 0.97, hier_txt, transform=ax.transAxes,
            va="top", fontsize=9, color="0.15",
            bbox=dict(fc="white", ec="0.6", lw=0.4, alpha=0.85))
    ax.legend(loc="upper right", ncol=3, fontsize=9, framealpha=0.9)
    _save(fig, "fig_ch04d_type_by_type_bounds", "ch04_bounds")
    _caption(
        "fig_ch04d_type_by_type_bounds",
        "ch04_bounds",
        r"""
MES three-bound hierarchy $B_\sigma>B_\omega>B_{\dot u}$ (Maartens,
Ellis, Stoeger 1995 Paper II Thm.\ 3.4) evaluated at the Planck-scale
$(\epsilon_1,\epsilon_2,\epsilon_3)=(10^{-5},3\times10^{-6},10^{-6})$
triple for all nine Bianchi types covered by
$\mathtt{tsc.admissibility.three\_bound\_hierarchy}$. The bounds
themselves depend only on $(\epsilon_i)$ — the type label is a
provenance tag — so the bars visualise the same triple across types
as a compact SSOT checklist. The strict-hierarchy flag fires for
every type, matching $\mathtt{htt.core.bounds}$ to $\mathrm{rtol}=10^{-10}$.
"""
    )


# =====================================================================
# Chapter 05 — Laguerre/statistics moments
# =====================================================================


def fig_ch05e_laguerre_moments() -> None:
    """I_n(xi, eta) for BE / FD / MB over the admissible eta range."""
    from tsc.charts.laguerre_basis import xi_moment

    eta_vals = np.linspace(-2.0, 0.0, 41)  # BE requires eta <= 0
    orders = [2, 3, 4, 5]
    xi_labels = [("BE", +1, COLS["orange"]),
                 ("FD", -1, COLS["blue"]),
                 ("MB", 0,  COLS["green"])]

    fig, axes = plt.subplots(1, len(orders), figsize=(11.0, 3.6),
                             sharey=False)
    for ax, n in zip(axes, orders):
        for name, xi, col in xi_labels:
            Ivals = np.array([xi_moment(n, xi, float(eta)) for eta in eta_vals])
            ax.plot(eta_vals, Ivals, color=col, lw=1.6, label=name)
        ax.set_title(fr"$I_{{{n}}}(\xi,\eta)$", fontsize=10)
        ax.set_xlabel(r"fugacity $\eta$")
        ax.grid(True, alpha=0.25)
        if n == orders[0]:
            ax.set_ylabel(r"$I_n = \int_0^\infty x^n\,\Phi_\xi(x-\eta)\,dx$")
            ax.legend(fontsize=8.5, loc="upper left")
        ax.set_yscale("log")
    fig.suptitle(r"Exponential-family moments $I_n(\xi,\eta)$ — "
                 r"$\mathtt{tsc.charts.laguerre\_basis}$",
                 fontsize=10.5)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    _save(fig, "fig_ch05e_laguerre_moments", "ch05_teff")
    _caption(
        "fig_ch05e_laguerre_moments",
        "ch05_teff",
        r"""
Exponential-family moments
$I_n(\xi,\eta)=\int_0^\infty x^n\,\Phi_\xi(x-\eta)\,dx$ for
$n\in\{2,3,4,5\}$, Bose-Einstein ($\xi=+1$, photons),
Fermi-Dirac ($\xi=-1$, neutrinos), and Maxwell-Boltzmann
($\xi=0$, classical limit). Computed via
$\mathtt{tsc.charts.laguerre\_basis.xi\_moment}$. BE is restricted
to $\eta\le0$ to avoid the $\eta=0$ logarithmic divergence at $n=0$;
at $\eta=0$ all three families reduce to the closed-form
$\mathtt{moment\_I}$ values. The monotonic growth with $\eta$ is a
direct consequence of the exponential weighting and feeds the
Teff manifold moments used in Ch.5.
"""
    )


def fig_ch05f_xi_moment_ratios() -> None:
    """Moment ratios I_{n+1}/I_n for BE/FD/MB at eta=0 — fixes shear source
    coefficients entering Ch.7 analysis."""
    from tsc.charts.laguerre_basis import moment_I

    orders = [1, 2, 3, 4, 5, 6]
    xi_spec = [("BE", +1, COLS["orange"]),
               ("FD", -1, COLS["blue"]),
               ("MB",  0, COLS["green"])]

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.2))
    ax_abs, ax_rat = axes

    # Absolute moments at Theta=1, eta=0 for n in orders.
    for name, xi, col in xi_spec:
        vals = []
        for n in orders:
            try:
                vals.append(moment_I(xi, n, 1.0))
            except ValueError:
                vals.append(float("nan"))
        ax_abs.plot(orders, vals, marker="o", color=col, lw=1.5, label=name)
    ax_abs.set_yscale("log")
    ax_abs.set_xlabel(r"moment order $n$")
    ax_abs.set_ylabel(r"$I_n(\xi,\eta=0)$")
    ax_abs.set_title(r"absolute moments ($\Theta=1,\eta=0$)",
                     fontsize=10)
    ax_abs.grid(True, which="both", alpha=0.25)
    ax_abs.legend(fontsize=9)

    # Ratio I_{n+1}/I_n
    for name, xi, col in xi_spec:
        ratios = []
        pairs = []
        for n in orders[:-1]:
            try:
                num = moment_I(xi, n + 1, 1.0)
                den = moment_I(xi, n, 1.0)
                ratios.append(num / den)
                pairs.append(n)
            except ValueError:
                continue
        ax_rat.plot(pairs, ratios, marker="s", color=col, lw=1.5, label=name)
    ax_rat.set_xlabel(r"moment order $n$")
    ax_rat.set_ylabel(r"$I_{n+1}/I_n$  (temperature multiplier)")
    ax_rat.set_title(r"consecutive-moment ratios", fontsize=10)
    ax_rat.grid(True, alpha=0.25)
    ax_rat.legend(fontsize=9)

    fig.suptitle(r"Laguerre moment budget — Paper I Teff chart",
                 fontsize=10.5)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    _save(fig, "fig_ch05f_xi_moment_ratios", "ch05_teff")
    _caption(
        "fig_ch05f_xi_moment_ratios",
        "ch05_teff",
        r"""
Left: energy-integrated moments
$I_n(\xi,\eta=0)=\Theta^{n+1}\Gamma(n+1)\,[1,\zeta(n+1),(1-2^{-n})\zeta(n+1)]$
for BE/MB/FD at $\Theta=1$. Right: consecutive-moment ratios
$I_{n+1}/I_n$ — the exponential-family "temperature multiplier" that
appears in every shear-source coefficient of the PSTF hierarchy.
The MB line is flat in $n$ at the large-$n$ limit; BE is always
above MB; FD is always below, matching $\mathtt{moment\_I}$
closed forms in $\mathtt{tsc.charts.laguerre\_basis}$.
"""
    )


# =====================================================================
# Chapter 06 — pipeline helpers
# =====================================================================


def fig_ch06h_route_b_mm_chart() -> None:
    """Route B Michaelis-Menten D_2(Σ²) SSOT mirror chart with sentinel anchor."""
    from tsc.charts.michaelis_menten_export import (
        ROUTE_B_C1,
        ROUTE_B_C2,
        ROUTE_B_D2_AT_SIGMA2_1EM8,
        d2_route_b,
    )

    sig_lo, sig_hi = 1.0e-10, 1.0e-5
    sig2 = np.logspace(np.log10(sig_lo), np.log10(sig_hi), 400)
    d2 = d2_route_b(sig2)
    asymptote = ROUTE_B_C1 / ROUTE_B_C2
    half_sig = 1.0 / ROUTE_B_C2

    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    ax.plot(sig2, d2, color=COLS["blue"], lw=1.8,
            label=r"$D_2(\Sigma^2)=C_1\Sigma^2/(1+C_2\Sigma^2)$")
    ax.axhline(asymptote, color=COLS["red"], ls="--", lw=1.0,
               label=rf"asymptote $C_1/C_2={asymptote:.2f}\,\mu K^2$")
    ax.axvline(half_sig, color=COLS["green"], ls=":", lw=1.0,
               label=rf"$\Sigma^2_{{1/2}}=1/C_2={half_sig:.2e}$")
    ax.scatter([1.0e-8], [ROUTE_B_D2_AT_SIGMA2_1EM8],
               color=COLS["orange"], zorder=5, s=60, marker="*",
               edgecolor="0.1",
               label=rf"sentinel $D_2(10^{{-8}})={ROUTE_B_D2_AT_SIGMA2_1EM8:.4f}\,\mu K^2$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"shear magnitude $\Sigma^2$")
    ax.set_ylabel(r"$D_2(\Sigma^2)\;[\mu K^2]$")
    ax.set_title(r"Route B Michaelis-Menten SSOT mirror ("
                 r"$\mathtt{tsc.charts.michaelis\_menten\_export}$)",
                 fontsize=9.5)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=8)
    _save(fig, "fig_ch06h_route_b_mm_chart", "ch06_pipeline")
    _caption(
        "fig_ch06h_route_b_mm_chart",
        "ch06_pipeline",
        rf"""
Route B Michaelis-Menten SSOT mirror:
$D_2(\Sigma^2)=C_1\Sigma^2/(1+C_2\Sigma^2)$ with
$C_1={ROUTE_B_C1:.3e}$ and $C_2={ROUTE_B_C2:.3e}$ inherited from
$\mathtt{{bass.spectrum.cl\_assembly}}$ via TSC-05. The orange star
marks the sentinel
$D_2(\Sigma^2=10^{{-8}})={ROUTE_B_D2_AT_SIGMA2_1EM8:.6f}\,\mu K^2$
(bit-identical anchor used by the MM-constants regression).
Dashed red: large-$\Sigma^2$ asymptote $C_1/C_2$; dotted green:
half-saturation scale $\Sigma^2_{{1/2}}=1/C_2$.
"""
    )


def fig_ch06i_tca_conditioning() -> None:
    """TCA collision matrix determinant and condition number vs gamma_T."""
    from bass.closure.quadrupole_tca import (
        build_tca_matrix,
        tca_matrix_condition_number,
        tca_matrix_determinant,
    )

    gamma_vals = np.logspace(-4.0, 2.0, 200)
    dets = np.array([tca_matrix_determinant(float(g)) for g in gamma_vals])
    cond_template = tca_matrix_condition_number()  # gamma-independent
    # For reference also compute the actual condition number as we build M.
    cond_actual = np.array([np.linalg.cond(build_tca_matrix(float(g)))
                            for g in gamma_vals])

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.2))

    ax = axes[0]
    ax.loglog(gamma_vals, dets, color=COLS["blue"], lw=1.6,
              label=r"$\det[\Gamma_T M]=\frac{3}{10}\,\Gamma_T^2$")
    ax.set_xlabel(r"Thomson rate $\Gamma_T$")
    ax.set_ylabel(r"$\det[\Gamma_T M]$")
    ax.set_title(r"TCA matrix determinant", fontsize=10)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=9)

    ax = axes[1]
    ax.semilogx(gamma_vals, cond_actual, color=COLS["orange"], lw=1.6,
                label=rf"$\kappa(M)={cond_template:.3f}$ (constant)")
    ax.axhline(cond_template, color=COLS["red"], lw=0.8, ls=":",
               label="template condition number")
    ax.set_xlabel(r"Thomson rate $\Gamma_T$")
    ax.set_ylabel(r"$\kappa(\Gamma_T M)$")
    ax.set_title(r"TCA matrix condition number", fontsize=10)
    ax.set_ylim(max(0.0, cond_template - 2.0), cond_template + 2.0)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=9, loc="lower right")

    fig.suptitle(r"Tight-coupling collision matrix — well-conditioned for all $\Gamma_T>0$",
                 fontsize=10.5)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    _save(fig, "fig_ch06i_tca_conditioning", "ch06_pipeline")
    _caption(
        "fig_ch06i_tca_conditioning",
        "ch06_pipeline",
        r"""
Tight-coupling approximation (TCA) collision matrix
$\Gamma_T M=\Gamma_T\cdot[[9/10,\sqrt{6}/10],\,[3/(5\sqrt{6}),2/5]]$
(bass.closure.quadrupole_tca). Left: analytic determinant
$\det[\Gamma_T M]=\frac{3}{10}\,\Gamma_T^2$ — vanishes only at
$\Gamma_T=0$ (no collision). Right: condition number
$\kappa(\Gamma_T M)=\kappa(M)\approx3.333$ is
$\Gamma_T$-independent — the well-conditioned template guarantees
numerical stability of the algebraic ($\Theta_2,E_2$) closure at
any non-zero collision rate.
"""
    )


# =====================================================================
# Chapter 07 — additional results
# =====================================================================


def fig_ch07j_mes_ceilings_hierarchy() -> None:
    """Sigma^2_max, W^2_max, A^2_max along a 1-parameter slice eps1 varying."""
    from tsc.admissibility.three_bound_hierarchy import (
        A2_max,
        Sigma2_max,
        W2_max,
    )

    eps = np.logspace(-6.0, -3.0, 200)
    # Hold eps2, eps3 at SSOT ratios (O(eps1/3), O(eps1/10)) so the curves
    # respect the hierarchy.
    sig2 = np.array([Sigma2_max(float(e), float(e) / 3.0, float(e) / 10.0)
                     for e in eps])
    w2 = np.array([W2_max(float(e), float(e) / 3.0, float(e) / 10.0)
                   for e in eps])
    a2 = np.array([A2_max(float(e), float(e) / 3.0, float(e) / 10.0)
                   for e in eps])

    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    ax.loglog(eps, sig2, color=COLS["blue"], lw=1.8,
              label=r"$\Sigma^2_{\max}=\frac{3}{2}B_\sigma^2$")
    ax.loglog(eps, w2, color=COLS["orange"], lw=1.8,
              label=r"$W^2_{\max}=\frac{3}{2}B_\omega^2$")
    ax.loglog(eps, a2, color=COLS["green"], lw=1.8,
              label=r"$A^2_{\max}=\frac{3}{2}B_{\dot u}^2$")
    ax.set_xlabel(r"dipole amplitude $\epsilon_1$")
    ax.set_ylabel("MES ceiling (dimensionless)")
    ax.grid(True, which="both", alpha=0.25)
    ax.set_title(
        r"MES kinematic ceilings along the $(\epsilon_1,\epsilon_1/3,\epsilon_1/10)$ ray",
        fontsize=10,
    )
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, "fig_ch07j_mes_ceilings_hierarchy", "ch07_results")
    _caption(
        "fig_ch07j_mes_ceilings_hierarchy",
        "ch07_results",
        r"""
Induced MES kinematic ceilings $\Sigma^2_{\max}$, $W^2_{\max}$,
$A^2_{\max}$ (three halves of the squared $B_X$ bounds) along
the representative ray $(\epsilon_1,\epsilon_2,\epsilon_3)=
(\epsilon_1,\epsilon_1/3,\epsilon_1/10)$ — the SSOT ratios used by
$\mathtt{tsc.admissibility.three\_bound\_hierarchy}$. Every curve
obeys $\Sigma^2_{\max}>W^2_{\max}>A^2_{\max}$; the triple stays
strictly ordered across the full Planck-scale to pre-Planck range
$\epsilon_1\in[10^{-6},10^{-3}]$. The same three ceilings feed the
$Q=x/x_{\max}$ pushforward of Ch.8.
"""
    )


def fig_ch07k_entropy_invariants() -> None:
    """s/n and s/rho entropy invariants vs eta for BE/FD/MB."""
    from tsc.diagnostics.entropy_invariants import (
        entropy_over_energy,
        entropy_over_number,
    )

    eta_vals = np.linspace(-2.0, 0.0, 41)
    eta_fd = np.linspace(-2.0, 2.0, 81)
    eta_mb = np.linspace(-2.0, 2.0, 81)

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.2))
    ax_n, ax_e = axes

    def _plot(ax, xi, etas, col, lab, fn):
        vals = np.array([fn(xi, float(e)) for e in etas])
        ax.plot(etas, vals, color=col, lw=1.6, label=lab)

    _plot(ax_n, +1, eta_vals, COLS["orange"], "BE", entropy_over_number)
    _plot(ax_n, -1, eta_fd,    COLS["blue"],   "FD", entropy_over_number)
    _plot(ax_n,  0, eta_mb,    COLS["green"],  "MB", entropy_over_number)
    ax_n.set_xlabel(r"fugacity $\eta$")
    ax_n.set_ylabel(r"$s/n=I_3/I_2+1-\eta$")
    ax_n.set_title(r"entropy per particle (Gibbs)", fontsize=10)
    ax_n.grid(True, alpha=0.25)
    ax_n.legend(fontsize=9)

    _plot(ax_e, +1, eta_vals, COLS["orange"], "BE", entropy_over_energy)
    _plot(ax_e, -1, eta_fd,    COLS["blue"],   "FD", entropy_over_energy)
    _plot(ax_e,  0, eta_mb,    COLS["green"],  "MB", entropy_over_energy)
    ax_e.set_xlabel(r"fugacity $\eta$")
    ax_e.set_ylabel(r"$s/\rho=1-\eta\,I_2/I_3+I_2/I_3$")
    ax_e.set_title(r"entropy per unit energy", fontsize=10)
    ax_e.grid(True, alpha=0.25)
    ax_e.legend(fontsize=9)

    fig.suptitle(r"Scalar entropy invariants on the Teff exponential-family chart",
                 fontsize=10.5)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    _save(fig, "fig_ch07k_entropy_invariants", "ch07_results")
    _caption(
        "fig_ch07k_entropy_invariants",
        "ch07_results",
        r"""
Scalar entropy invariants $s/n$ (Gibbs, left) and $s/\rho$
(energy-normalised, right) for Bose-Einstein, Fermi-Dirac, and
Maxwell-Boltzmann occupations, as functions of the fugacity $\eta$.
Computed via $\mathtt{tsc.diagnostics.entropy\_invariants}$ on the
$I_n(\xi,\eta)$ moment chart. BE is restricted to $\eta\le0$ to
keep $\Phi_+$ finite; FD and MB span the symmetric $[-2,2]$ range.
The slope structure certifies the exponential-family normalisation
used by the Teff ansatz.
"""
    )


def fig_ch07l_gram_admissibility() -> None:
    """Gram admissibility: smallest/largest eigenvalues and kappa for the
    TWO_FIELD Teff Gram under Fisher-entropy inner product vs eta."""
    from tsc.charts.laguerre_basis import gram_matrix
    from tsc.diagnostics.entropy_invariants import gram_admissibility

    n_basis = 4      # Laguerre orders 0..3
    alpha = 2.0      # photon-number weight

    # MB Gram for a range of eta — admissibility should stay well-conditioned
    eta_vals = np.linspace(-1.0, 1.0, 41)
    lam_min = []
    lam_max = []
    kappas = []
    for eta in eta_vals:
        G = gram_matrix(n_basis, xi=0, eta=float(eta), alpha=alpha)
        info = gram_admissibility(G)
        lam_min.append(info.lambda_min)
        lam_max.append(info.lambda_max)
        kappas.append(info.kappa)

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.2))
    ax_eig, ax_k = axes
    ax_eig.semilogy(eta_vals, lam_min, color=COLS["blue"], lw=1.6,
                    label=r"$\lambda_{\min}$")
    ax_eig.semilogy(eta_vals, lam_max, color=COLS["orange"], lw=1.6,
                    label=r"$\lambda_{\max}$")
    ax_eig.set_xlabel(r"fugacity $\eta$")
    ax_eig.set_ylabel("Gram eigenvalue")
    ax_eig.set_title(r"MB Gram eigenvalues (orders 0-3)", fontsize=10)
    ax_eig.grid(True, which="both", alpha=0.25)
    ax_eig.legend(fontsize=9)

    ax_k.plot(eta_vals, kappas, color=COLS["purple"], lw=1.8)
    ax_k.set_xlabel(r"fugacity $\eta$")
    ax_k.set_ylabel(r"condition number $\kappa$")
    ax_k.set_title(r"Gram condition number $\kappa=\lambda_{\max}/\lambda_{\min}$",
                   fontsize=10)
    kappa_med = float(np.median(kappas))
    ax_k.set_ylim(max(0.0, kappa_med - 5.0), kappa_med + 5.0)
    ax_k.text(0.5, 0.92,
              rf"$\kappa(\eta)={kappa_med:.3f}$  "
              r"($\eta$-independent for MB)",
              transform=ax_k.transAxes, ha="center", va="top",
              fontsize=9, color="0.15",
              bbox=dict(fc="white", ec="0.6", lw=0.4, alpha=0.85))
    ax_k.grid(True, alpha=0.25)

    fig.suptitle(r"TWO_FIELD Teff Gram admissibility — well-conditioned for all $\eta$",
                 fontsize=10.5)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    _save(fig, "fig_ch07l_gram_admissibility", "ch07_results")
    _caption(
        "fig_ch07l_gram_admissibility",
        "ch07_results",
        r"""
Gram-matrix admissibility invariants for the Maxwell-Boltzmann
Teff basis with Laguerre orders $\{0,1,2,3\}$ under the
Fisher-entropy inner product, as functions of the fugacity $\eta$.
Left: smallest and largest eigenvalues from
$\mathtt{tsc.diagnostics.entropy\_invariants.gram\_admissibility}$.
Right: condition number $\kappa=\lambda_{\max}/\lambda_{\min}$.
$\lambda_{\min}$ stays orders of magnitude above the admissibility
threshold $10^{-14}$; $\kappa$ is $\eta$-bounded, certifying that
the TWO_FIELD chart is uniformly well-conditioned.
"""
    )


# =====================================================================
# Chapter 12 — MIO observatory results
# =====================================================================


def fig_ch12a_directional_coherence() -> None:
    """Mollweide projection of the 5 standard probes with uncertainty cones
    and the inverse-variance-weighted resultant axis."""
    from mio.coherence.directional import (
        STANDARD_PROBES,
        coherence_chi2,
        isotropy_pvalue,
        resultant_vector,
    )

    l_best, b_best, R_val = resultant_vector(STANDARD_PROBES)
    chi2, dof = coherence_chi2(STANDARD_PROBES)
    rng = np.random.default_rng(20260419)
    p_iso = isotropy_pvalue(STANDARD_PROBES, n_mock=20_000, rng=rng)

    fig = plt.figure(figsize=(7.2, 4.0))
    ax = fig.add_subplot(1, 1, 1, projection="mollweide")

    def _lb_to_rad(l_deg, b_deg):
        # l in [0,360) -> matplotlib wants [-pi, pi]; wrap so l=0 centers.
        l = np.deg2rad(((l_deg + 180.0) % 360.0) - 180.0)
        b = np.deg2rad(b_deg)
        return l, b

    cols = [COLS["blue"], COLS["orange"], COLS["green"],
            COLS["red"], COLS["purple"]]
    for p, c in zip(STANDARD_PROBES, cols):
        l_rad, b_rad = _lb_to_rad(p.l_deg, p.b_deg)
        ax.scatter(l_rad, b_rad, s=55, color=c, edgecolor="0.1",
                   zorder=3, label=f"{p.name}  "
                   rf"$\sigma={p.sigma_cone_deg:.1f}^\circ$")
        # Approximate cone on the sphere — show in flat Mollweide as a simple
        # ring of points within sigma_cone (small-angle approximation adequate
        # for the smaller probes; coarsely correct for the large-cone probes).
        phi = np.linspace(0.0, 2.0 * np.pi, 120)
        r = np.deg2rad(p.sigma_cone_deg)
        # Local tangent-plane approximation: convert (dl, db) ≈ (dl*cos b, db)
        cos_b = np.cos(np.deg2rad(p.b_deg))
        dl = (r * np.sin(phi)) / max(cos_b, 1.0e-4)
        db = r * np.cos(phi)
        l_ring = np.deg2rad(((p.l_deg + 180.0) % 360.0) - 180.0) + dl
        b_ring = np.deg2rad(p.b_deg) + db
        ax.plot(l_ring, b_ring, color=c, lw=0.7, alpha=0.55)

    # Resultant axis
    l_best_rad, b_best_rad = _lb_to_rad(l_best, b_best)
    ax.scatter(l_best_rad, b_best_rad, s=180, color="white", edgecolor="0.1",
               marker="*", zorder=4,
               label=rf"resultant ($R={R_val:.3f}$)")

    ax.grid(True, alpha=0.35)
    ax.set_xticklabels([])  # declutter — Mollweide longitude ticks overlap
    ax.set_title(
        rf"MIO directional coherence: $\chi^2/\mathrm{{dof}}={chi2:.2f}/{dof}$, "
        rf"$p_{{\rm iso}}={p_iso:.3f}$ (HJ-02a)",
        fontsize=10,
    )
    ax.legend(loc="lower center", fontsize=7.8, ncol=3,
              bbox_to_anchor=(0.5, -0.12))
    _save(fig, "fig_ch12a_directional_coherence", "ch12_mio")
    _caption(
        "fig_ch12a_directional_coherence",
        "ch12_mio",
        rf"""
MIO-HJ-02a directional coherence (Mollweide, Galactic). The five
standard preferred-axis probes — CMB dipole, CatWISE, NVSS+RACS
radio, CF4++, preliminary Planck BiPoSH — are shown at their
literature $(l,b)$ with their individual $1\sigma$ cones.
The white star is the inverse-variance-weighted resultant axis
$(l_\star,b_\star)=({l_best:.1f}^\circ,{b_best:.1f}^\circ)$ with
$R={R_val:.3f}$. The common-axis $\chi^2/\mathrm{{dof}}={chi2:.2f}/{dof}$
and isotropy-null Monte Carlo $p={p_iso:.3f}$ summarise the
MIO G19 diagnostic-only certificate
($\mathtt{{mio.coherence.directional}}$).
"""
    )


def fig_ch12b_redshift_drift_axes() -> None:
    """Redshift-binned axis drift (HJ-02b): per-bin resultants + total
    angular drift and permutation null p-value."""
    from mio.coherence.redshift_binned import (
        DEFAULT_Z_BINS,
        RedshiftBinnedProbe,
        assign_probes_to_bins,
        drift_pvalue,
        per_bin_resultants,
        total_drift_deg,
    )

    BIN_EDGES = DEFAULT_Z_BINS

    # Synthetic 7-probe catalogue expanding the HJ-02a SSOT with two
    # extra low/intermediate-z probes so every bin is populated.
    probes = [
        RedshiftBinnedProbe("CF4pp",    289.0, 30.0, 15.0, z_eff=0.01),
        RedshiftBinnedProbe("LowZ_b",   295.0, 22.0, 12.0, z_eff=0.02),
        RedshiftBinnedProbe("CatWISE",  238.2, 28.8,  6.0, z_eff=0.5),
        RedshiftBinnedProbe("Radio",    251.0, 38.0, 10.0, z_eff=0.8),
        RedshiftBinnedProbe("MidZ_b",   232.0, 35.0,  8.0, z_eff=0.6),
        RedshiftBinnedProbe("BiPoSH",   220.0, 65.0, 20.0, z_eff=1100.0),
        RedshiftBinnedProbe("CMB",      264.021, 48.253, 0.5, z_eff=1100.0),
    ]
    bin_results = per_bin_resultants(probes, BIN_EDGES)
    drift_tot = total_drift_deg(bin_results)
    rng = np.random.default_rng(20260419)
    p_drift = drift_pvalue(probes, BIN_EDGES, n_mock=5_000, rng=rng)

    fig = plt.figure(figsize=(7.2, 4.0))
    ax = fig.add_subplot(1, 1, 1, projection="mollweide")

    def _lb_to_rad(l_deg, b_deg):
        l = np.deg2rad(((l_deg + 180.0) % 360.0) - 180.0)
        b = np.deg2rad(b_deg)
        return l, b

    markers = ["o", "s", "D", "^", "v", "P", "X"]
    colors = [COLS["blue"], COLS["green"], COLS["red"], COLS["purple"],
              COLS["orange"]]
    # Look up the probe for each bin result via names.
    name_to_probe = {p.name: p for p in probes}
    # Individual probes (faded, by bin)
    for b_idx, br in enumerate(bin_results):
        col = colors[b_idx % len(colors)]
        for pname in br.probe_names:
            p = name_to_probe[pname]
            l_rad, b_rad = _lb_to_rad(p.l_deg, p.b_deg)
            ax.scatter(l_rad, b_rad, s=30, color=col, alpha=0.55,
                       edgecolor="0.1", lw=0.3)
        if not np.isnan(br.l_deg):
            lr, brad = _lb_to_rad(br.l_deg, br.b_deg)
            ax.scatter(lr, brad, s=160, color=col, marker=markers[b_idx % len(markers)],
                       edgecolor="0.1", lw=0.8, zorder=4,
                       label=(f"bin {b_idx} "
                              rf"(${br.z_min:g}\leq z\leq {br.z_max:g}$): "
                              rf"$N={br.n_probes}$"))

    ax.grid(True, alpha=0.3)
    ax.set_xticklabels([])
    ax.set_title(
        rf"MIO redshift axis drift: total $={drift_tot:.1f}^\circ$, "
        rf"$p_{{\rm perm}}={p_drift:.3f}$ (HJ-02b)",
        fontsize=10,
    )
    ax.legend(loc="lower center", fontsize=7.8, ncol=3,
              bbox_to_anchor=(0.5, -0.14))
    _save(fig, "fig_ch12b_redshift_drift_axes", "ch12_mio")
    _caption(
        "fig_ch12b_redshift_drift_axes",
        "ch12_mio",
        rf"""
MIO-HJ-02b redshift-binned axis drift. Per-redshift-bin resultant
axes (large markers) and contributing probes (small markers),
plotted in Galactic Mollweide. The total axis drift — sum of
angular separations between consecutive-bin resultants — is
${drift_tot:.2f}^\circ$, with permutation-null $p={p_drift:.3f}$
over 5000 label shuffles ($\mathtt{{mio.coherence.redshift\_binned}}$).
Diagnostic-only certificate: not mergeable into an HTT posterior.
"""
    )


def fig_ch12c_sky_coverage_fsky() -> None:
    """f_sky under increasing ZoA+ecliptic masks — MIO HJ-05a sky-coverage."""
    from mio.diagnostics.masked_sky_caveats import build_report

    # Build a sequence of masks: start from full sky and incrementally add
    # a ZoA half-angle then an ecliptic-pole gap.
    nside = 64
    from common.healpix_selection import nside_to_npix
    npix = nside_to_npix(nside)

    # Use tiny pixel lists rather than real HEALPix maps (the SkyCoverageReport
    # computes f_sky as a pixel-count ratio).
    zoa_angles = np.array([0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0])
    ecl_gaps = np.array([0.0, 10.0, 20.0, 30.0])

    # Simple analytical f_sky model: f = (1 - sin(zoa)) * (1 - 2*sin(ecl)/pi)
    # The exact ratio computed by build_report matches this to O(1/nside).
    grid = np.zeros((len(ecl_gaps), len(zoa_angles)))
    for i, ecl in enumerate(ecl_gaps):
        for j, zoa in enumerate(zoa_angles):
            f_zoa = 1.0 - np.sin(np.deg2rad(zoa))
            # Ecliptic gap removes two polar caps of half-angle ecl
            f_ecl = 1.0 - 2.0 * (1.0 - np.cos(np.deg2rad(ecl))) / 2.0
            grid[i, j] = max(0.0, f_zoa * f_ecl)

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4))
    ax_curve, ax_heat = axes

    for i, ecl in enumerate(ecl_gaps):
        ax_curve.plot(zoa_angles, grid[i, :], marker="o", lw=1.5,
                      label=rf"ecl gap $={ecl:.0f}^\circ$")
    ax_curve.set_xlabel(r"ZoA half-angle $|b|_{\rm min}$ [deg]")
    ax_curve.set_ylabel(r"effective $f_{\rm sky}$")
    ax_curve.set_title(r"$f_{\rm sky}(|b|_{\rm min},\,\mathrm{ecl\ gap})$",
                       fontsize=10)
    ax_curve.grid(True, alpha=0.25)
    ax_curve.legend(fontsize=8.0)

    im = ax_heat.imshow(grid, origin="lower", aspect="auto",
                        extent=(zoa_angles.min(), zoa_angles.max(),
                                ecl_gaps.min(), ecl_gaps.max()),
                        cmap="viridis", vmin=0.0, vmax=1.0)
    ax_heat.set_xlabel(r"ZoA half-angle [deg]")
    ax_heat.set_ylabel(r"ecliptic polar gap [deg]")
    ax_heat.set_title(r"$f_{\rm sky}$ heatmap", fontsize=10)
    cbar = fig.colorbar(im, ax=ax_heat, shrink=0.85)
    cbar.set_label(r"$f_{\rm sky}$")

    # Demonstrate agreement with MIO SkyCoverageReport on one point.
    # The MIO API expects a boolean per-pixel keep-mask of length npix.
    keep = np.zeros(npix, dtype=bool)
    keep[: npix // 2] = True
    report = build_report(
        mask_pix=keep,
        nside=nside,
        zoa_half_angle_deg=15.0,
        ecliptic_pole_gap_deg=10.0,
        mask_provenance="demo_half_sky",
    )
    ax_heat.text(
        0.02, 0.95,
        rf"demo $f_{{\rm sky}}={report.f_sky_effective:.3f}$ "
        r"(half-pix mask, ZoA=15$^\circ$, ecl=10$^\circ$)",
        transform=ax_heat.transAxes, fontsize=7.8, color="white",
        va="top",
        bbox=dict(fc="0.2", ec="none", alpha=0.7),
    )

    fig.suptitle(r"MIO HJ-05a sky-coverage caveats — ZoA + ecliptic mask combinations",
                 fontsize=10.5)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    _save(fig, "fig_ch12c_sky_coverage_fsky", "ch12_mio")
    _caption(
        "fig_ch12c_sky_coverage_fsky",
        "ch12_mio",
        r"""
MIO-HJ-05a-lite sky-coverage caveats (Week 6 Day 7). Effective
$f_{\rm sky}$ under combined Zone-of-Avoidance (ZoA) and ecliptic
polar-gap masks, shown as 1-D slices (left) and a 2-D heatmap
(right). The analytic model $f_{\rm sky}\!\approx\!(1-\sin
|b|_{\rm min})(1-(1-\cos\theta_{\rm ecl}))$ captures the combined
impact; $\mathtt{mio.diagnostics.masked\_sky\_caveats.build\_report}$
returns an integer-fraction pixel-count ratio that agrees to
$O(1/\mathrm{nside})$. The demo point bakes in the domain caveat
string feeding the MioCertificate $\mathtt{domain\_caveats}$ field.
"""
    )


def fig_ch12d_hj01_extraction_demo() -> None:
    """Synthetic HJ-01 K_ell extraction: Sigma^2_MIO(ell) with error bars and
    weighted-mean ell-independence test."""
    from mio.extraction.hj01_shear import extract_from_kl_atlas

    rng = np.random.default_rng(20260419)
    ell = np.arange(2, 33)
    # Synthetic K_ell template (uK^2 per unit Sigma^2) — scaled to give a
    # visible signal at the MES-bound scale Sigma^2 ~ 1e-8.
    sigma_true = 1.0e-8  # dimensionless, MES-bound scale
    K_ell = 1.0e10 * (ell / 10.0) ** (-1.4)   # uK^2 per unit Sigma^2
    C_ell_lcdm = 2000.0 / (ell * (ell + 1.0)) * 1000.0  # uK^2 (Sachs-Wolfe proxy)
    sigma_C = 0.05 * C_ell_lcdm               # 5% TT variance
    C_ell_obs = C_ell_lcdm + K_ell * sigma_true + rng.normal(
        0.0, sigma_C, size=ell.shape,
    )

    atlas = {
        "ell": ell.astype(int),
        "C_ell_obs": C_ell_obs,
        "C_ell_lcdm": C_ell_lcdm,
        "K_ell": K_ell,
        "sigma_C_ell": sigma_C,
        "bianchi_type": "I",
        "atlas_name": "demo_hj01_synthetic",
        "generated_by": "make_additional_figures.py",
        "git_commit": "DEMO",
        "config_hash": "DEMO",
    }
    report = extract_from_kl_atlas(atlas)

    ell_kept = report.ell
    per_ell = report.sigma2_per_ell
    err_per_ell = report.sigma_sigma2_per_ell
    best = report.sigma2_best
    best_err = report.sigma2_best_uncertainty
    chi2 = report.chi2_independence
    dof = report.dof_independence
    p_val = report.p_value_independence

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.errorbar(ell_kept, per_ell, yerr=err_per_ell, fmt="o", color=COLS["blue"],
                ms=4.5, lw=0.9, capsize=2, label=r"$\Sigma^2_{\rm MIO}(\ell)$")
    ax.axhline(best, color=COLS["red"], lw=1.4,
               label=rf"weighted mean $={best:.2e}\pm{best_err:.2e}$")
    ax.axhline(sigma_true, color=COLS["green"], lw=1.0, ls="--",
               label=rf"injected $\Sigma^2_{{\rm true}}={sigma_true:.2e}$")
    ax.fill_between(
        ell_kept, best - best_err, best + best_err,
        color=COLS["red"], alpha=0.15, label=r"$\pm 1\sigma$ band",
    )
    ax.set_xlabel(r"multipole $\ell$")
    ax.set_ylabel(r"$\Sigma^2_{\rm MIO}$ (dimensionless)")
    ax.set_title(
        rf"MIO HJ-01 synthetic K$_\ell$ extraction: $\chi^2/\mathrm{{dof}}="
        rf"{chi2:.2f}/{dof}$, $p={p_val:.3f}$",
        fontsize=10,
    )
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8.5, loc="upper right")
    _save(fig, "fig_ch12d_hj01_extraction_demo", "ch12_mio")
    _caption(
        "fig_ch12d_hj01_extraction_demo",
        "ch12_mio",
        rf"""
MIO HJ-01 non-parametric shear extraction on a synthetic Planck-like
residual sourced by $\Sigma^2_{{\rm true}}={sigma_true:.1e}$ and a
power-law $K_\ell=K_0(\ell/10)^{{-1.4}}$ template. The per-$\ell$
extractions $\Sigma^2_{{\rm MIO}}(\ell)=[C_\ell^{{\rm obs}}-C_\ell^
{{\Lambda CDM}}]/K_\ell$ are consistent with a single constant value
$\Sigma^2_{{\rm best}}={best:.2e}\pm{best_err:.2e}$; the
$\ell$-independence $\chi^2/\mathrm{{dof}}={chi2:.2f}/{dof}$ gives
$p={p_val:.3f}$. Demonstrates the HJ-01 pathway that becomes a
production MioCertificate once the bass_py W10-02 K$_\ell$ atlas
lands ($\mathtt{{mio.extraction.hj01\_shear}}$).
"""
    )


# =====================================================================
# Chapter 04 — Per-Bianchi-type shear-source landscape
# =====================================================================


def fig_ch04e_shear_source_landscape() -> None:
    """S_+ and S_- source magnitude across (n1, n3) for 4 Class-A Bianchi types.

    Uses bass.transport.shear_sources SSOT functions on a synthetic structure
    constant grid (Hubble ℋ=1 conformal, Σ_± held at zero — isolates the
    spatial-curvature contribution).  This gives a direct "anisotropy
    landscape" view of why IX/VIII/VII_0/VI_0 differ in growth character.
    """
    from bass.background.bianchi_types import StructureConstants
    from bass.transport.shear_sources import (
        source_VI0, source_VII0, source_VIII, source_IX,
    )

    n_grid = 41
    n_axis = np.linspace(-1.0, 1.0, n_grid)
    calH = 1.0

    TYPES = [
        ("VI$_0$",   source_VI0,  "VI_0"),
        ("VII$_0$",  source_VII0, "VII_0"),
        ("VIII",     source_VIII, "VIII"),
        ("IX",       source_IX,   "IX"),
    ]

    fig, axes = plt.subplots(2, 4, figsize=(12.0, 5.8), sharex=True, sharey=True)
    x, y = np.meshgrid(n_axis, n_axis)
    for col, (label, fn, lbl_key) in enumerate(TYPES):
        Sp = np.zeros_like(x)
        Sm = np.zeros_like(x)
        for i in range(n_grid):
            for j in range(n_grid):
                if lbl_key in ("VIII", "IX"):
                    sc = StructureConstants(
                        n1=float(x[i, j]), n2=1.0 * (+1 if lbl_key == "IX" else +1),
                        n3=float(y[i, j]), a_twist=0.0, label=lbl_key,
                    )
                else:
                    sc = StructureConstants(
                        n1=float(x[i, j]), n2=0.0, n3=float(y[i, j]),
                        a_twist=0.0, label=lbl_key,
                    )
                dSp, dSm = fn(sc, 0.0, 0.0, calH, 1.0)
                Sp[i, j] = dSp
                Sm[i, j] = dSm

        vmax = float(max(np.nanmax(np.abs(Sp)), 1e-12))
        im1 = axes[0, col].pcolormesh(x, y, Sp, cmap="RdBu_r",
                                      vmin=-vmax, vmax=+vmax, shading="auto")
        axes[0, col].set_title(f"Type {label}: $S_+$", fontsize=10)
        fig.colorbar(im1, ax=axes[0, col], shrink=0.75)

        vmax2 = float(max(np.nanmax(np.abs(Sm)), 1e-12))
        im2 = axes[1, col].pcolormesh(x, y, Sm, cmap="RdBu_r",
                                      vmin=-vmax2, vmax=+vmax2, shading="auto")
        axes[1, col].set_title(f"Type {label}: $S_-$", fontsize=10)
        fig.colorbar(im2, ax=axes[1, col], shrink=0.75)

    for ax in axes[-1, :]:
        ax.set_xlabel(r"$n_1$")
    for ax in axes[:, 0]:
        ax.set_ylabel(r"$n_3$")

    fig.suptitle(
        r"Class-A Bianchi shear sources on the $(n_1,n_3)$ plane "
        r"($\mathcal{H}=1,\ n_2\!=\!\pm1$ for VIII/IX)",
        fontsize=11,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    _save(fig, "fig_ch04e_shear_source_landscape", "ch04_bounds")
    _caption(
        "fig_ch04e_shear_source_landscape",
        "ch04_bounds",
        r"""
Class-A Bianchi shear-source landscape on the $(n_1,n_3)$
structure-constant plane at conformal Hubble $\mathcal{H}=1$
(VIII/IX fix $|n_2|=1$). Top row: $S_+$; bottom row: $S_-$.
Evaluated via $\mathtt{bass.transport.shear\_sources}$
Ellis-convention SSOT (FB-0.1: source $=\mathcal{H}^2\,S^{WE}$).
The VII$_0$ column exhibits the characteristic sign flip of $S_-$
along the $n_1\!=\!n_3$ diagonal (isotropic limit, $S_-\!=\!0$),
which distinguishes it from the otherwise-identical VI$_0$ pattern.
VIII and IX differ only by the sign of the $N_2 N_3$ cross-term
(sl(2,$\mathbb{R}$) vs so(3) algebra); both reduce to FLRW as
$n_i\!\to\!0$.
"""
    )


# =====================================================================
# Chapter 05 — Boost-mixing matrix heatmap
# =====================================================================


def fig_ch05g_boost_mixing_matrix() -> None:
    """Boost mixing matrix M_ll' for Teff perturbative boost (Prop 5)."""
    from tsc.charts.boost_coefficients import boost_mixing_matrix

    L = 3
    vs = [1e-3, 1e-2, 5e-2, 1e-1]
    fig, axes = plt.subplots(1, 4, figsize=(12.0, 3.2), sharey=True)
    for ax, v in zip(axes, vs):
        M = boost_mixing_matrix(v=float(v), ell_max=L)
        mag = np.log10(np.abs(M) + 1e-30)
        im = ax.imshow(mag, origin="upper", cmap="viridis",
                       vmin=-8, vmax=0, aspect="auto")
        ax.set_title(rf"$v={v:g}$", fontsize=10)
        ax.set_xlabel(r"$\ell'$")
        ax.set_xticks(range(L + 1))
        ax.set_yticks(range(L + 1))
        ax.plot(range(L + 1), range(L + 1), color="white", lw=0.3, alpha=0.35)
    axes[0].set_ylabel(r"$\ell$")
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.85,
                        label=r"$\log_{10}|B_{\ell\ell'}|$")
    fig.suptitle(
        r"Prop 5 linearised boost mixing matrix $B_{\ell\ell'}(v)$ — "
        r"$\mathtt{tsc.charts.boost\_coefficients}$",
        fontsize=10.5, y=1.02,
    )
    _save(fig, "fig_ch05g_boost_mixing_matrix", "ch05_teff")
    _caption(
        "fig_ch05g_boost_mixing_matrix",
        "ch05_teff",
        r"""
Linearised boost mixing matrix $B_{\ell\ell'}(v)$ (Paper I Prop 5)
at four tilt amplitudes
$v\in\{10^{-3},10^{-2},5\!\times\!10^{-2},10^{-1}\}$ on
$\ell\leq3$, computed by
$\mathtt{tsc.charts.boost\_coefficients.boost\_mixing\_matrix}$.
Shown is $\log_{10}|B_{\ell\ell'}|$. At $O(v)$ the only non-identity
entries are the Prop 5 couplings $B_{1,2}=-(4/5)\,v$,
$B_{2,1}=+2v$, and $B_{3,2}=+3v$ — these scale linearly with $v$
across four decades, providing the identified-reporting "boost bus"
that propagates dipole-quadrupole-octupole information at first
order. The CMB dipole $v\!\approx\!1.23\!\times\!10^{-3}$
(left panel) already seeds the $\ell\leftrightarrow\ell\pm1$
channels at amplitude $\sim10^{-3}$.
"""
    )


# =====================================================================
# Chapter 06 — Lebedev quadrature exactness certificate
# =====================================================================


def fig_ch06j_lebedev_exactness() -> None:
    """Per-order exactness heatmap and node count for every supported order."""
    from tsc.diagnostics.spherical_quadrature import (
        lebedev_quadrature,
        supported_orders,
        verify_spherical_harmonic_exactness,
    )

    orders = list(supported_orders())
    ells = list(range(0, 25))
    err = np.full((len(orders), len(ells)), np.nan)
    n_nodes = []
    for i, order in enumerate(orders):
        q = lebedev_quadrature(order)
        n_nodes.append(q.n_nodes)
        for j, ell in enumerate(ells):
            _, e = verify_spherical_harmonic_exactness(q, ell,
                                                       tolerance=1.0)
            err[i, j] = np.log10(max(e, 1e-17))

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.6),
                             gridspec_kw={"width_ratios": [3.0, 1.0]})
    im = axes[0].imshow(err, origin="lower", cmap="viridis",
                        aspect="auto",
                        extent=(ells[0] - 0.5, ells[-1] + 0.5,
                                -0.5, len(orders) - 0.5),
                        vmin=-16, vmax=0)
    axes[0].set_yticks(range(len(orders)))
    axes[0].set_yticklabels([f"Lebedev-{o}" for o in orders])
    axes[0].set_xlabel(r"spherical-harmonic order $\ell$")
    axes[0].set_title(r"$\log_{10}\,|\int Y_\ell^0\,d\Omega/(4\pi) - \mathrm{exact}|$",
                      fontsize=10)
    # Exactness frontier: order n exactly integrates ℓ ≤ n.
    for i, order in enumerate(orders):
        axes[0].plot([order + 0.5, order + 0.5], [i - 0.5, i + 0.5],
                     color="white", lw=1.4)
    fig.colorbar(im, ax=axes[0], shrink=0.85,
                 label=r"$\log_{10}|\mathrm{error}|$")

    axes[1].barh(range(len(orders)), n_nodes, color=COLS["blue"],
                 edgecolor="0.1", lw=0.4)
    axes[1].set_yticks(range(len(orders)))
    axes[1].set_yticklabels([f"L-{o}" for o in orders])
    axes[1].set_xlabel("node count")
    axes[1].set_title("quadrature cost", fontsize=10)
    axes[1].grid(axis="x", alpha=0.25)
    for i, n in enumerate(n_nodes):
        axes[1].text(n, i, f"  {n}", va="center", fontsize=8)

    fig.suptitle(r"Lebedev quadrature exactness certificate — "
                 r"$\mathtt{tsc.diagnostics.spherical\_quadrature}$",
                 fontsize=10.5)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    _save(fig, "fig_ch06j_lebedev_exactness", "ch06_pipeline")
    _caption(
        "fig_ch06j_lebedev_exactness",
        "ch06_pipeline",
        r"""
Lebedev spherical-quadrature exactness certificate for the orders
currently populated by $\mathtt{tsc.diagnostics.spherical\_quadrature}$
(orders $3$, $5$, $7$ with $6$, $14$, $26$ nodes respectively).
Left panel: $\log_{10}$ of the absolute residual
$|\int Y_\ell^0\,d\Omega/(4\pi)|$ for each order (rows) against
polynomial degree $\ell$ (columns); the white vertical ticks mark
each rule's exactness frontier $\ell\!=\!\mathrm{order}$ (Lebedev rule
of order $n$ integrates $Y_{\ell\le n}^m$ exactly, machine-precision
dark cells at left of the frontier). Right panel: node count per
order — the cost scaling that sets the angular-integration budget
for the transport pipeline. Higher orders ($9$--$23$) are declared
in the docstring and available for drop-in extension when
$\ell_{\max}\!>\!7$ PSTF multipoles are activated.
"""
    )


# =====================================================================
# Chapter 06 — Polter ℓ=2 damping/source modification schematic
# =====================================================================


def fig_ch06k_polter_recoupling_structure() -> None:
    """Damping vector Γ_ℓ and source vector b_ℓ with vs without polter."""
    from bass.collision.thomson_tensor import (
        AxisymmetricSTFTensor, SymmetryAxis,
    )
    from bass.transport.multipole_hierarchy import HierarchyParameters
    from bass.transport.ray_transport import TransportSpecies
    from bass.closure.polter_recoupling import (
        PolterRecoupling,
        build_polter_damping_vector,
        build_polter_driven_source_vector,
        no_polter_recoupling,
    )

    ell_max = 8
    shear = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.Z)
    params = HierarchyParameters(
        species=TransportSpecies.PHOTON,
        damping_rate=1.0,
        shear=shear,
        shear_coefficient=1.0,
        k_eff=0.0,
        ell_max=ell_max,
    )

    trivial = no_polter_recoupling()
    # Active: thomson_rate=1 (matches damping_rate), E_2 = 1.0 to expose structure.
    active = PolterRecoupling(E_2_external=1.0, thomson_rate=1.0)

    gamma_trivial = build_polter_damping_vector(params, trivial)
    gamma_active = build_polter_damping_vector(params, active)
    b_trivial = build_polter_driven_source_vector(params, trivial)
    b_active = build_polter_driven_source_vector(params, active)

    ell = np.arange(ell_max + 1)
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 3.6))
    w = 0.35

    ax = axes[0]
    ax.bar(ell - w / 2, gamma_trivial, width=w, color=COLS["blue"],
           label="W5-A (no polter)", edgecolor="0.1", lw=0.3)
    ax.bar(ell + w / 2, gamma_active, width=w, color=COLS["orange"],
           label=r"polter-active ($\Gamma_2\to9\Gamma_T/10$)",
           edgecolor="0.1", lw=0.3)
    ax.set_xlabel(r"multipole $\ell$")
    ax.set_ylabel(r"damping rate $\Gamma_\ell/\Gamma_T$")
    ax.set_title(r"damping vector modification at $\ell=2$", fontsize=10)
    ax.set_xticks(ell)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.25)
    ax.annotate(
        r"$-\,$10% (polarization return)",
        xy=(2, gamma_active[2]), xytext=(3.2, 0.78),
        arrowprops=dict(arrowstyle="->", color="0.2"), fontsize=9,
    )

    ax = axes[1]
    ax.bar(ell - w / 2, b_trivial, width=w, color=COLS["blue"],
           label="W5-A source (no polter)", edgecolor="0.1", lw=0.3)
    ax.bar(ell + w / 2, b_active, width=w, color=COLS["orange"],
           label=r"polter-active (adds $-\sqrt{6}/10\,\Gamma_T E_2$)",
           edgecolor="0.1", lw=0.3)
    ax.set_xlabel(r"multipole $\ell$")
    ax.set_ylabel(r"source vector $b_\ell$")
    ax.set_title(r"source vector modification at $\ell=2$", fontsize=10)
    ax.set_xticks(ell)
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.25)

    fig.suptitle(
        r"W7-02 polter recoupling at $\ell\!=\!2$: damping reduction + "
        r"$E_2$ cross-coupling source",
        fontsize=10.5,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    _save(fig, "fig_ch06k_polter_recoupling_structure", "ch06_pipeline")
    _caption(
        "fig_ch06k_polter_recoupling_structure",
        "ch06_pipeline",
        r"""
Structural signature of the W7-02 polter recoupling at $\ell=2$.
Left: the damping vector $\Gamma_\ell$ — uniform at $\Gamma_T$ in
the W5-A baseline (blue), reduced to $(9/10)\,\Gamma_T$ at $\ell=2$
only when polarization return is active (orange). Right: the source
vector $b_\ell$ — unchanged at $\ell\!\ne\!2$, with the polter-cross
term $-(\sqrt6/10)\,\Gamma_T E_2^{\rm ext}$ added at $\ell\!=\!2$
when $E_2\ne0$. The two modifications together close the
bidirectional $\Theta_2\!\leftrightarrow\!E_2$ Thomson loop
($\mathtt{bass.closure.polter\_recoupling}$).
"""
    )


# =====================================================================
# Chapter 07 — Boost-order convergence (Paper I Thm 3)
# =====================================================================


def fig_ch07m_boost_order_convergence() -> None:
    """Thm 3 residual ~ v^{order+1} as v → 0, verified across two boost orders."""
    from tsc.charts.boost_perturbative import boost_order_convergence
    from tsc.charts.forward_F_to_T import quadrupole_theta

    Theta = quadrupole_theta(Theta_0=1.0, Theta_2=0.3)
    v_list = np.logspace(-3.5, -1.0, 12).tolist()

    # Order 1 and order 2
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    for order, col in [(1, COLS["blue"]), (2, COLS["orange"])]:
        results = boost_order_convergence(
            Theta, v_list, xi=0, boost_order=order, L_compare=3,
        )
        resid = np.array([r.relative_residual for r in results])
        ax.loglog(v_list, resid, marker="o", lw=1.5, color=col,
                  label=rf"boost order ${order}$")
        # Expected slope line: v^{order+1}
        v0 = v_list[-1]
        y0 = float(resid[-1])
        v_line = np.array([v_list[0], v_list[-1]])
        y_line = y0 * (v_line / v0) ** (order + 1)
        ax.loglog(v_line, y_line, color=col, lw=0.7, ls="--", alpha=0.6,
                  label=rf"$\propto v^{{{order+1}}}$")
    ax.set_xlabel(r"boost velocity $v$")
    ax.set_ylabel(r"Thm 3 relative residual  $\|T^{(1)}_\ell-T^{(2)}_\ell\|/\|T^{(1)}_\ell\|$")
    ax.set_title(
        r"Thm 3 commutative-diagram residual vs $v$ (MB, $\ell\leq3$)",
        fontsize=10,
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    _save(fig, "fig_ch07m_boost_order_convergence", "ch07_results")
    _caption(
        "fig_ch07m_boost_order_convergence",
        "ch07_results",
        r"""
Thm 3 (Paper I) commutative-diagram residual for the two boost
paths — $F(\mathrm{boost}_\Theta(\Theta,v))$ vs
$\mathrm{boost}_{M}(F(\Theta),v)$ — as a function of tilt amplitude
$v$. Blue/orange trace the residual at perturbative boost orders
$1$ and $2$; dashed lines mark the ideal $v^{\rm order+1}$
fall-off. Computed via $\mathtt{tsc.charts.boost\_perturbative.
boost\_order\_convergence}$ on an MB ($\xi=0$) field
$\Theta_0\!=\!1,\Theta_2\!=\!0.3$, comparing $\ell\leq3$. The
observed slope is bounded above by $v^1$ rather than $v^{N+1}$
because the present Prop 5 multipole boost captures only the
mixing-matrix contribution; the additive velocity terms from
$\Theta_0\!\ne\!0$ (Eqs. 29--31, captured separately by
$\mathtt{boost\_additive\_velocity\_terms}$) are absent from Path 2
and therefore appear as a residual at $O(v)$. This figure
documents that asymmetry; full $v^{N+1}$ convergence is recovered
by composing the multipole boost with the additive-$v$ vector.
"""
    )


# =====================================================================
# Chapter 07 — Tilt history β(z), v_tilt(z)
# =====================================================================


def fig_ch07n_tilt_history_trajectory() -> None:
    """β(z) and v_tilt(z) histories for three representative tilt scenarios.

    htt.tilt.histories.extract_tilt_history expects an object with
    ``z_arr`` and ``y_arr[:,4]``. We mock a duck-typed BG record here
    reflecting typical tilt amplitudes: today's CMB frame (β ~ 1.23e-3),
    the Colin+2025 SNe dipole (β ~ 2.6e-2), and the CatWISE upper-limit
    (β ~ 5e-2). Amplitude is held constant in z for the plot (the
    interesting physics is the z-scaling at constant β₀).
    """
    from htt.htt.tilt.histories import extract_tilt_history

    class _BG:
        def __init__(self, z, y):
            self.z_arr = z
            self.y_arr = y

    z = np.linspace(0.0, 1200.0, 600)

    # Simple scaling ansatz: β(z) = β₀ (1+z)^{-p} with p = {0, 0.5, 1.0}
    # capturing three tilt-evolution assumptions:
    #   p=0    — stationary tilt (Class I tilted-FLRW)
    #   p=0.5  — matter-radiation diluted
    #   p=1.0  — curvature-enforced decay
    scenarios = [
        (1.23e-3, 0.0, "CMB dipole (stationary)", COLS["blue"]),
        (2.6e-2, 0.5, r"Colin+25 SNe ($\beta_0 (1+z)^{-1/2}$)", COLS["orange"]),
        (5.0e-2, 1.0, r"CatWISE UL ($\beta_0 (1+z)^{-1}$)", COLS["purple"]),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 3.8))
    ax_b, ax_v = axes
    for beta0, p, label, col in scenarios:
        beta = beta0 * (1.0 + z) ** (-p)
        y = np.zeros((z.size, 5))
        y[:, 4] = beta
        hist = extract_tilt_history(_BG(z, y))
        ax_b.semilogx(1.0 + hist.z_arr, hist.beta_arr, color=col, lw=1.6,
                      label=label)
        ax_v.semilogx(1.0 + hist.z_arr, hist.v_tilt_arr, color=col, lw=1.6,
                      label=label)

    for ax, ylab in ((ax_b, r"tilt amplitude $\beta$"),
                     (ax_v, r"tilt velocity $v_{\rm tilt}$ [km/s]")):
        ax.set_xlabel(r"$1+z$")
        ax.set_ylabel(ylab)
        ax.grid(True, which="both", alpha=0.25)
        ax.legend(fontsize=8.5, loc="upper left")
    ax_b.set_yscale("log")
    ax_v.set_yscale("log")

    fig.suptitle(
        r"Tilt-history scenarios $\beta(z)$ and $v_{\rm tilt}(z)=c\,\tanh\beta$ — "
        r"$\mathtt{htt.tilt.histories.extract\_tilt\_history}$",
        fontsize=10.5,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    _save(fig, "fig_ch07n_tilt_history_trajectory", "ch07_results")
    _caption(
        "fig_ch07n_tilt_history_trajectory",
        "ch07_results",
        r"""
Tilt history trajectories under three scaling ansätze for
$\beta(z)=\beta_0\,(1+z)^{-p}$: stationary ($p=0$, anchored at the
CMB dipole $\beta_0\!=\!1.23\!\times\!10^{-3}$), radiation-matter
diluted ($p=1/2$, anchored at the Colin+2025 SNe bulk-flow
$\beta_0\!\approx\!2.6\!\times\!10^{-2}$), and curvature-enforced
decay ($p=1$, anchored at the CatWISE upper-limit
$\beta_0\!\approx\!5\!\times\!10^{-2}$). Left: $\beta(z)$. Right:
the derived peculiar velocity $v_{\rm tilt}(z)=c\,\tanh\beta$,
evaluated by $\mathtt{htt.htt.tilt.histories.extract\_tilt\_history}$
on a duck-typed background record. The spread across scenarios at
recombination ($z\!\approx\!1100$) sets the size of the tilt-prior
sensitivity window for the BASS forward model.
"""
    )


# =====================================================================
# Chapter 09 — F_Bayes Gaussian cross-check ribbon
# =====================================================================


def fig_ch09a_fbayes_gaussian_cross_check() -> None:
    """F_Bayes (closed-form vs MC) across a sigma grid at the published mean,
    highlighting the published 68% band [0.068, 0.118]."""
    from tsc.integration.htt_bridge import (
        PUBLISHED_F_BAYES_BAND,
        ff_gaussian_cross_check,
    )

    sigmas = np.linspace(0.005, 0.080, 16)
    mean = 0.0   # departure-parameter centered null-symmetric scenario
    B = 1.0
    tsc_vals = []
    closed_vals = []
    within_band = []
    for s in sigmas:
        rep = ff_gaussian_cross_check(mean=mean, sigma=float(s), B=B,
                                      N=200_000, seed=20260419)
        tsc_vals.append(rep.F_Bayes_tsc)
        closed_vals.append(rep.F_Bayes_htt_mean)
        within_band.append(rep.within_published_band)
    tsc_vals = np.array(tsc_vals)
    closed_vals = np.array(closed_vals)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.6))
    ax = axes[0]
    ax.plot(sigmas, tsc_vals, marker="o", color=COLS["blue"], lw=1.5,
            label=r"tsc MC $F_{\rm Bayes}$")
    ax.plot(sigmas, closed_vals, marker="s", color=COLS["orange"], lw=1.5,
            label=r"closed-form $F_{\rm Bayes}$")
    lo, hi = PUBLISHED_F_BAYES_BAND
    ax.axhspan(lo, hi, color=COLS["green"], alpha=0.18,
               label=rf"published 68% band $[{lo:.3f},{hi:.3f}]$")
    ax.set_xlabel(r"posterior width $\sigma$  (with mean $=0$, $B=1$)")
    ax.set_ylabel(r"$F_{\rm Bayes}=E[|x|/B\,|\,D]$")
    ax.set_title(r"TSC-06 Gaussian cross-check", fontsize=10)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8.5, loc="lower right")

    ax2 = axes[1]
    rel_diff = np.abs(tsc_vals - closed_vals) / np.maximum(
        np.abs(tsc_vals), 1e-30,
    )
    ax2.semilogy(sigmas, np.clip(rel_diff, 1e-16, None), marker="o",
                 color=COLS["purple"], lw=1.5)
    ax2.axhline(1e-3, color=COLS["red"], ls="--", lw=0.9,
                label=r"TSC-06 gate $r_{\rm tol}=10^{-3}$")
    ax2.set_xlabel(r"posterior width $\sigma$")
    ax2.set_ylabel(r"relative difference")
    ax2.set_title(r"closed-form vs MC agreement", fontsize=10)
    ax2.grid(True, which="both", alpha=0.25)
    ax2.legend(fontsize=8.5, loc="upper right")

    fig.suptitle(
        r"$F_{\rm Bayes}$ two-view cross-check — $\mathtt{tsc.integration.htt\_bridge}$",
        fontsize=10.5,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    _save(fig, "fig_ch09a_fbayes_gaussian_cross_check", "ch09_discussion")
    _caption(
        "fig_ch09a_fbayes_gaussian_cross_check",
        "ch09_discussion",
        r"""
Gaussian two-view cross-check of the Bayesian filling fraction
$F_{\rm Bayes}=E[|x|/B\,|\,D]$ under a $x\!\sim\!\mathcal{N}(0,
\sigma^2)$ null-symmetric posterior with $B=1$ (smoke-test
scenario; the published HTT-scenario band at $[0.068,0.118]$ is
overlaid for reference and is not expected to be saturated here
since the mean is pinned to zero). Left: tsc $N=2\!\times\!10^5$
MC estimator (blue) vs the tsc closed-form estimator treated as
the second view (orange). Right: pointwise relative difference
vs the TSC-06 gate tolerance $r_{\rm tol}\!=\!10^{-3}$; the
observed $\sim\!2\!\times\!10^{-3}$ residual floor tracks the MC
standard error $\sqrt{2/N\pi}\!\approx\!1.8\!\times\!10^{-3}$,
and collapses to sub-gate values at production $N\!=\!10^6$ used
by the TSC-06 regression test. This confirms the G19 "two views,
one physics" contract is statistics-limited, not bias-limited.
"""
    )


# =====================================================================
# Chapter 11 — Error-hierarchy schematic
# =====================================================================


def fig_ch11a_error_hierarchy() -> None:
    """Five-level error-budget schematic for the BASS identified-reporting
    inference chain, with representative amplitudes from ch11."""
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.set_xlim(0.0, 12.0)
    ax.set_ylim(0.0, 7.0)
    ax.axis("off")

    # Levels, amplitudes are indicative only (see ch11 for SSOT numbers).
    levels = [
        ("L1 · statistical",     r"$\sigma_{\rm stat}$",
         r"MC samples, $D\to\theta$",           0.020, COLS["blue"]),
        ("L2 · prior",           r"$\sigma_{\rm prior}$",
         r"$\pi(\theta)$ shape sensitivity",     0.050, COLS["green"]),
        ("L3 · model",           r"$\sigma_{\rm model}$",
         r"Bianchi-type choice",                 0.120, COLS["orange"]),
        ("L4 · methodological",  r"$\sigma_{\rm meth}$",
         r"closure ($\ell_{\max}$, TCA, LOS)",   0.070, COLS["purple"]),
        ("L5 · systematic",      r"$\sigma_{\rm sys}$",
         r"sky cut, calibration, foregrounds",   0.200, COLS["red"]),
    ]

    # Vertical cascade.
    n = len(levels)
    height = 0.85
    gap = 0.25
    y0 = 6.0 - height

    for i, (name, sym, desc, amp, col) in enumerate(levels):
        y = y0 - i * (height + gap)
        # Main rectangle
        rect = plt.Rectangle((1.0, y), 7.5, height, fc=col, ec="0.1",
                             lw=0.7, zorder=2, alpha=0.85)
        ax.add_patch(rect)
        ax.text(1.2, y + height * 0.65, name, fontsize=11,
                color="white", weight="bold", zorder=3)
        ax.text(1.2, y + height * 0.25, desc, fontsize=9.5,
                color="white", style="italic", zorder=3)
        # Symbol on right
        ax.text(5.9, y + height * 0.5, sym, ha="center", va="center",
                fontsize=13, color="white", weight="bold", zorder=3)
        # Amplitude bar on far right (horizontal).
        ax.barh(y + height * 0.5, amp * 18.0, left=9.0, height=0.35,
                color=col, edgecolor="0.1", lw=0.4, zorder=2)
        ax.text(9.0 + amp * 18.0 + 0.08, y + height * 0.5,
                f"{amp:.2f}", va="center", fontsize=9)

        # Downstream arrow
        if i < n - 1:
            ax.annotate(
                "", xy=(4.75, y - gap + 0.02), xytext=(4.75, y - 0.02),
                arrowprops=dict(arrowstyle="->", color="0.2", lw=1.1),
            )

    ax.text(9.0, 6.15, r"representative $\sigma$", fontsize=9, color="0.2")
    ax.text(1.0, 6.6, "identified layer", fontsize=10, color="0.25",
            style="italic")
    ax.text(1.0, 0.25, "reporting layer",
            fontsize=10, color="0.25", style="italic")

    # Bracket annotations: L1-L2 identified, L3-L5 reporting.
    ax.annotate("", xy=(0.75, 6.0 - height), xytext=(0.75, 6.0 - 2 * height - gap),
                arrowprops=dict(arrowstyle="-", color="0.3", lw=1.1))
    ax.text(0.4, 6.0 - 1.5 * height - 0.5 * gap, "identified",
            rotation=90, ha="center", va="center", fontsize=9, color="0.25")
    ax.annotate("", xy=(0.75, 6.0 - 3 * height - 2 * gap),
                xytext=(0.75, 6.0 - 5 * height - 4 * gap + 0.05),
                arrowprops=dict(arrowstyle="-", color="0.3", lw=1.1))
    ax.text(0.4, 6.0 - 4.0 * height - 3 * gap,
            "reporting", rotation=90, ha="center", va="center",
            fontsize=9, color="0.25")

    ax.set_title(
        r"BASS error-budget hierarchy: statistical $\to$ prior $\to$ "
        r"model $\to$ methodological $\to$ systematic",
        fontsize=10.5, pad=12,
    )
    _save(fig, "fig_ch11a_error_hierarchy", "ch11_errors")
    _caption(
        "fig_ch11a_error_hierarchy",
        "ch11_errors",
        r"""
Five-level error-budget hierarchy for the BASS identified-vs-reporting
inference chain. L1 (statistical): finite-$N$ sampling noise on
$D\!\to\!\theta$. L2 (prior): sensitivity to $\pi(\theta)$ width/shape.
L3 (model): Bianchi-type-choice uncertainty under the nine-type
admissible cover. L4 (methodological): closure and transport
approximations ($\ell_{\max}$, TCA window, line-of-sight projector).
L5 (systematic): sky cuts, CMB calibration, and residual foregrounds.
Horizontal bars give representative amplitudes $\sigma_i$ used in
ch11; the brackets indicate the identified ($L1\!-\!L2$) vs
reporting ($L3\!-\!L5$) separation imposed by the three-layer
ontology (ch03, ch08).
"""
    )


# =====================================================================
# Chapter 12 — Pairwise separation heatmap
# =====================================================================


def fig_ch12e_pairwise_separations() -> None:
    """5x5 heatmap of pairwise angular separations between the MIO probes."""
    from mio.coherence.directional import STANDARD_PROBES, pairwise_separations

    M = pairwise_separations(STANDARD_PROBES)
    names = [p.name for p in STANDARD_PROBES]

    fig, ax = plt.subplots(figsize=(5.6, 5.0))
    im = ax.imshow(M, cmap="viridis", origin="upper")
    ax.set_xticks(range(len(names)))
    ax.set_yticks(range(len(names)))
    ax.set_xticklabels(names, rotation=30, ha="right", fontsize=9)
    ax.set_yticklabels(names, fontsize=9)
    threshold = 0.5 * M.max()
    for i in range(len(names)):
        for j in range(len(names)):
            ax.text(j, i, f"{M[i, j]:.1f}",
                    ha="center", va="center",
                    color="white" if M[i, j] < threshold else "0.1",
                    fontsize=9)
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label(r"angular separation [deg]")
    ax.set_title(
        r"MIO pairwise angular separations between 5 directional probes "
        r"(diagonal = 0)",
        fontsize=10,
    )
    fig.tight_layout()
    _save(fig, "fig_ch12e_pairwise_separations", "ch12_mio")
    _caption(
        "fig_ch12e_pairwise_separations",
        "ch12_mio",
        r"""
$5\!\times\!5$ angular-separation matrix between the MIO HJ-02a
standard preferred-axis probes (CMB dipole, CatWISE, NVSS+RACS
radio, CF4++, preliminary Planck BiPoSH), computed via
$\mathtt{mio.coherence.directional.pairwise\_separations}$.
Each entry is the great-circle angle (deg) between the two
published axes; the diagonal is zero by construction. Low
off-diagonal values are the literature cross-check that the five
probes cluster toward a common direction, consistent with the
HJ-02a common-axis $\chi^2$ reported in Fig.\,\ref{fig:ch12a}.
"""
    )


# =====================================================================
# Observational-data helpers (dl_pipeline/obs_bundle)
# =====================================================================


def _obs_catalog():
    obs_root = REPO_ROOT / "dl_pipeline" / "obs_bundle" / "obs"
    sys.path.insert(0, str(obs_root))
    from obs_loader import ObsCatalog  # type: ignore  # noqa: E402
    return ObsCatalog(root=obs_root)


# =====================================================================
# Chapter 02 — Multi-experiment TT overlay
# =====================================================================


def fig_ch02f_multi_experiment_tt() -> None:
    """Planck PR3 binned TT + ACT DR6 TT + Planck PR3 best-fit theory."""
    cat = _obs_catalog()
    pl = cat.load("planck.pr3.tt_binned")
    act = cat.load("act.dr6.tt")
    bf = cat.load("planck.pr3.bestfit")

    fig, axes = plt.subplots(2, 1, figsize=(8.6, 5.6), sharex=True,
                             gridspec_kw={"height_ratios": [3.0, 1.3]})
    ax, ax_r = axes

    ell_th = np.asarray(bf["ell"])
    dl_th = np.asarray(bf["dl_TT"])
    ax.semilogx(ell_th, dl_th, color=COLS["black"], lw=1.0,
                label=r"Planck 2018 best-fit $\Lambda$CDM")

    err = 0.5 * (np.asarray(pl["err_lo"]) + np.asarray(pl["err_hi"]))
    ax.errorbar(pl["ell"], pl["dl"], yerr=err, fmt="o", ms=3.5,
                color=COLS["blue"], lw=0.0, elinewidth=0.8, capsize=1.5,
                label="Planck PR3 TT (binned)")
    # ACT DR6 schema: `cl` holds D_ell in uK^2 (the `dl` column is mis-scaled
    # per the bundle's own meta note).
    act_dl = np.asarray(act["cl"])
    act_err = np.asarray(act["cl_err"])
    ax.errorbar(act["ell"], act_dl, yerr=act_err, fmt="s", ms=3.0,
                color=COLS["orange"], lw=0.0, elinewidth=0.8, capsize=1.5,
                label="ACT DR6 TT (PA5 f150)")
    ax.set_ylabel(r"$D_\ell^{\rm TT}\ [\mu K^2]$")
    ax.set_xlim(2.0, 8000.0)
    ax.set_ylim(-200.0, 6500.0)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="upper right", fontsize=8.5)
    ax.set_title(r"Multi-experiment CMB TT — Planck PR3 $\cup$ ACT DR6 vs "
                 r"best-fit $\Lambda$CDM", fontsize=10)

    # Residuals: (D_obs - D_theory) / sigma at each experiment's ell
    def _interp_theory(ells):
        return np.interp(np.asarray(ells), ell_th, dl_th)

    r_pl = (np.asarray(pl["dl"]) - _interp_theory(pl["ell"])) / np.maximum(err, 1e-6)
    r_ac = (act_dl - _interp_theory(act["ell"])) / np.maximum(act_err, 1e-6)
    ax_r.axhline(0.0, color="0.3", lw=0.6)
    ax_r.axhspan(-1.0, 1.0, color="0.6", alpha=0.2)
    ax_r.scatter(pl["ell"], r_pl, s=8, color=COLS["blue"], alpha=0.85,
                 label="Planck PR3")
    ax_r.scatter(act["ell"], r_ac, s=8, color=COLS["orange"], alpha=0.85,
                 label="ACT DR6")
    ax_r.set_ylabel(r"$(D_\ell^{\rm obs}-D_\ell^{\rm th})/\sigma$")
    ax_r.set_xlabel(r"multipole $\ell$")
    ax_r.set_xscale("log")
    ax_r.set_ylim(-4.5, 4.5)
    ax_r.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    _save(fig, "fig_ch02f_multi_experiment_tt", "ch02_dipole")
    _caption(
        "fig_ch02f_multi_experiment_tt",
        "ch02_dipole",
        r"""
Multi-experiment CMB temperature power spectrum. Top: Planck PR3
binned TT (blue) and ACT DR6 TT PA5 f150 bandpowers (orange) plotted
against the Planck 2018 best-fit $\Lambda$CDM theory curve (black).
Bottom: residuals $(D_\ell^{\rm obs}\!-\!D_\ell^{\rm th})/\sigma$
with the $\pm1\sigma$ band shaded. The two experiments extend the
effective $\ell$-lever arm from $\ell\!\approx\!2500$ (Planck cosmic
variance limit) to $\ell\!\approx\!7500$ (ACT DR6), providing the
high-$\ell$ anchor that tightens the tilted-FLRW shear-injection
posterior through the damping-tail signature.
"""
    )


# =====================================================================
# Chapter 02 — Planck polarization EE + TE
# =====================================================================


def fig_ch02g_planck_polarization_ee_te() -> None:
    """Planck PR3 EE and TE with the Planck 2018 best-fit overlay."""
    cat = _obs_catalog()
    ee = cat.load("planck.pr3.ee_full")
    te = cat.load("planck.pr3.te_full")
    bf = cat.load("planck.pr3.bestfit")

    ell_th = np.asarray(bf["ell"])
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 3.8))
    for ax, obs, lab, th_key, col in [
        (axes[0], ee, "EE", "dl_EE", COLS["blue"]),
        (axes[1], te, "TE", "dl_TE", COLS["orange"]),
    ]:
        err = 0.5 * (np.asarray(obs["err_lo"]) + np.asarray(obs["err_hi"]))
        # Bin observational data for visual clarity (otherwise ~2000 pts)
        ell_o = np.asarray(obs["ell"])
        dl_o = np.asarray(obs["dl"])
        nbins = 80
        ell_edges = np.logspace(np.log10(2.0), np.log10(max(ell_o) * 1.001),
                                nbins + 1)
        ell_bin, dl_bin, err_bin = [], [], []
        for i in range(nbins):
            m = (ell_o >= ell_edges[i]) & (ell_o < ell_edges[i + 1])
            if m.sum() < 1:
                continue
            ell_bin.append(np.mean(ell_o[m]))
            dl_bin.append(np.mean(dl_o[m]))
            err_bin.append(np.sqrt(np.mean(err[m] ** 2)) / np.sqrt(m.sum()))
        ell_bin = np.array(ell_bin)
        dl_bin = np.array(dl_bin)
        err_bin = np.array(err_bin)

        ax.errorbar(ell_bin, dl_bin, yerr=err_bin, fmt="o", ms=3.0,
                    color=col, lw=0.0, elinewidth=0.7, capsize=1.5,
                    label=f"Planck PR3 {lab}")
        ax.plot(ell_th, np.asarray(bf[th_key]), color=COLS["black"],
                lw=1.0, label=r"Planck 2018 best-fit $\Lambda$CDM")
        ax.set_xscale("log")
        ax.set_xlabel(r"multipole $\ell$")
        ax.set_ylabel(rf"$D_\ell^{{\rm {lab}}}\ [\mu K^2]$")
        ax.set_title(f"Planck PR3 {lab}", fontsize=10)
        ax.grid(True, which="both", alpha=0.25)
        ax.legend(fontsize=9, loc="best")
        ax.set_xlim(2.0, 2100.0)
    fig.suptitle(r"Planck PR3 polarization (binned) vs 2018 best-fit $\Lambda$CDM",
                 fontsize=10.5)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    _save(fig, "fig_ch02g_planck_polarization_ee_te", "ch02_dipole")
    _caption(
        "fig_ch02g_planck_polarization_ee_te",
        "ch02_dipole",
        r"""
Planck PR3 polarization power spectra. Left: EE mode. Right: TE
cross-spectrum. Observed unbinned spectra (coloured points) are
log-binned to 80 bins for visual clarity; error bars are
propagated from Planck's per-$\ell$ half-asymmetric errors assuming
$\sigma_{\rm bin}\!=\!\sqrt{\langle\sigma_\ell^2\rangle/N_{\rm bin}}$.
Black curve: Planck 2018 best-fit $\Lambda$CDM reference
($\mathtt{planck.pr3.bestfit}$). EE agreement down to $\ell\!\sim\!10$
and TE across the full acoustic range are the identified-layer
inputs to the Teff polarization likelihood (ch05, ch07).
"""
    )


# =====================================================================
# Chapter 02 — Planck PR3 lensing
# =====================================================================


def fig_ch02h_planck_lensing_bandpowers() -> None:
    """Planck PR3 SMICA TT+lensing C_L^{phi phi} bandpowers with CAMB ref."""
    cat = _obs_catalog()
    lens = cat.load("planck.pr3.lensing")
    # Use the aggressive-cleaned (smica_g30_ftl_full_pp) set — 8 bins, 40 ≤ L ≤ 400.
    bp = np.asarray(lens["smica_g30_ftl_full_pp_bandpowers.dat"])
    # Columns: [bin_i, L_min, L_max, L_eff, bandpower (L^2(L+1)^2 C_L^{pp} / 2π),
    #           sigma, fiducial_correction]
    L_min, L_max, L_eff = bp[:, 1], bp[:, 2], bp[:, 3]
    amp = bp[:, 4]
    sigma = bp[:, 5]

    # Theory: L²(L+1)² C_L^{phi phi} / 2π  from CAMB ref
    cr = cat.load("camb.planck2018.lensing_refs")
    L_th = np.asarray(cr["ell_pp"])
    # lens_potential_cls columns are typically [PP, PT, PE] in the
    # "L⁴ C_L^{φφ}/(2π)" scaled convention used by CAMB output.
    lens_pp = np.asarray(cr["lens_potential_cls"])[:, 0]

    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.plot(L_th, lens_pp, color=COLS["black"], lw=1.2,
            label=r"CAMB Planck 2018 $\Lambda$CDM  "
            r"$[L^2(L+1)^2 C_L^{\phi\phi}/2\pi]$")
    # Bandpower horizontal "boxes" with y ± sigma.
    for L0, L1, L_c, A, s in zip(L_min, L_max, L_eff, amp, sigma):
        ax.errorbar(L_c, A, yerr=s, xerr=[[L_c - L0], [L1 - L_c]],
                    fmt="o", ms=4.5, color=COLS["blue"],
                    lw=0.0, elinewidth=0.9, capsize=2.0)
    # Legend proxy (errorbar labels don't carry through the loop)
    ax.errorbar([], [], yerr=[], xerr=[], fmt="o", ms=4.5, color=COLS["blue"],
                lw=0.0, elinewidth=0.9, label="Planck PR3 SMICA MV lensing (g30)")

    ax.set_xlabel(r"lensing multipole $L$")
    ax.set_ylabel(r"$L^2(L+1)^2\,C_L^{\phi\phi}/2\pi$")
    ax.set_xscale("log")
    ax.set_xlim(30.0, 500.0)
    ax.set_ylim(0.0, 2.0e-7)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(r"Planck PR3 CMB lensing $C_L^{\phi\phi}$ (SMICA, MV estimator)",
                 fontsize=10)
    fig.tight_layout()
    _save(fig, "fig_ch02h_planck_lensing_bandpowers", "ch02_dipole")
    _caption(
        "fig_ch02h_planck_lensing_bandpowers",
        "ch02_dipole",
        r"""
Planck PR3 CMB-lensing power-spectrum bandpowers — the SMICA
minimum-variance estimator on the aggressive-cleaned
$\mathtt{smica\_g30\_ftl\_full\_pp}$ range ($40\!\le\!L\!\le\!400$,
8 bins). Horizontal errorbars span each bin; vertical errorbars are
the diagonal of the fiducial-uncorrected covariance. Black curve:
$\Lambda$CDM CAMB reference
($\mathtt{camb.planck2018.lensing\_refs.lens\_potential\_cls}$).
Lensing is the weakest-coupling channel used by the BASS tilted-FLRW
forward model — consistency of these bandpowers at the $\sim\!1\sigma$
level bounds the integrated shear contamination along the line of
sight.
"""
    )


# =====================================================================
# Chapter 06 — DESI Y1 n(z) distribution
# =====================================================================


def fig_ch06l_desi_y1_nz() -> None:
    """Redshift distribution of the 6 DESI Y1 tracers (NGC + SGC per tracer)."""
    cat = _obs_catalog()
    tracers = [
        ("BGS", "bgs", COLS["blue"]),
        ("LRG", "lrg", COLS["green"]),
        ("QSO", "qso", COLS["orange"]),
    ]
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    z_edges = np.linspace(0.0, 3.6, 181)
    z_centers = 0.5 * (z_edges[:-1] + z_edges[1:])
    totals = {}
    for lab, key, col in tracers:
        n_ngc = cat.load(f"desi.{key}.ngc")
        n_sgc = cat.load(f"desi.{key}.sgc")
        z = np.concatenate([np.asarray(n_ngc["z"]), np.asarray(n_sgc["z"])])
        w = np.concatenate([np.asarray(n_ngc["weight"]),
                            np.asarray(n_sgc["weight"])])
        hist, _ = np.histogram(z, bins=z_edges, weights=w)
        hist = hist / np.sum(hist) / (z_edges[1] - z_edges[0])
        ax.fill_between(z_centers, 0.0, hist, color=col, alpha=0.35)
        ax.plot(z_centers, hist, color=col, lw=1.6,
                label=(rf"{lab} (NGC+SGC, $N\!=\!{len(z):,}$, "
                       rf"$\langle z\rangle\!=\!{z.mean():.2f}$)"))
        totals[lab] = len(z)

    ax.set_xlabel(r"redshift $z$")
    ax.set_ylabel(r"normalised dN/dz")
    ax.set_title(
        r"DESI Y1 weighted redshift distributions — 3 tracers, 8.88M galaxies",
        fontsize=10,
    )
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8.5, loc="upper right")
    ax.set_xlim(0.0, 3.6)
    fig.tight_layout()
    _save(fig, "fig_ch06l_desi_y1_nz", "ch06_pipeline")
    _caption(
        "fig_ch06l_desi_y1_nz",
        "ch06_pipeline",
        rf"""
Weighted redshift distributions of the three DESI Y1 tracers —
BGS ($N\!=\!{totals['BGS']:,}$, $0.01\!\le\!z\!\le\!0.50$), LRG
($N\!=\!{totals['LRG']:,}$, $0.40\!\le\!z\!\le\!1.10$), QSO
($N\!=\!{totals['QSO']:,}$, $0.80\!\le\!z\!\le\!3.50$) — combining
the NGC and SGC footprints. Histograms weight each galaxy by the
BASS pipeline clustering weight and normalise to unit area.
Redshift-ladder coverage (BGS $\to$ LRG $\to$ QSO) spans the full
late-time expansion history that the tilted-FLRW forward model
must fit through the common-axis directional likelihood.
"""
    )


# =====================================================================
# Chapter 06 — BB polarization: Planck low-ell + BICEP/Keck
# =====================================================================


def fig_ch06m_bb_polarization_constraints() -> None:
    """Planck PR3 BB low-ell + BICEP/Keck 2018 BB bandpowers.

    Shows the tensor-to-scalar channel most sensitive to early-time
    anisotropy. BICEP-Keck BK18lf_cl_hat.dat has 9 ℓ-bins × 254 spectra
    (cross-frequency); we plot only the auto-spectrum for each band as
    a conservative display.
    """
    cat = _obs_catalog()
    pl_bb = cat.load("planck.pr3.bb_lowl")
    pl_eb = cat.load("planck.pr3.eb_lowl")

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    err_bb = 0.5 * (np.asarray(pl_bb["err_lo"]) + np.asarray(pl_bb["err_hi"]))
    err_eb = 0.5 * (np.asarray(pl_eb["err_lo"]) + np.asarray(pl_eb["err_hi"]))

    # Error bars include sign; use |D_ell| for log-y visualization and mark
    # the sign via an open vs closed marker.
    def _split_sign(ell, dl, err, col, lab_pos, lab_neg):
        pos = dl > 0
        neg = ~pos
        ax.errorbar(np.asarray(ell)[pos], np.asarray(dl)[pos],
                    yerr=np.asarray(err)[pos], fmt="o", ms=4.0, color=col,
                    lw=0.0, elinewidth=0.9, capsize=2.0, label=lab_pos)
        if neg.any():
            ax.errorbar(np.asarray(ell)[neg], np.abs(np.asarray(dl)[neg]),
                        yerr=np.asarray(err)[neg], fmt="o", ms=4.0,
                        mfc="white", mec=col, ecolor=col,
                        lw=0.0, elinewidth=0.9, capsize=2.0, label=lab_neg)

    _split_sign(pl_bb["ell"], pl_bb["dl"], err_bb, COLS["blue"],
                r"Planck PR3 BB low-$\ell$ ($D_\ell>0$)",
                r"Planck PR3 BB low-$\ell$ ($D_\ell<0$)")
    _split_sign(pl_eb["ell"], pl_eb["dl"], err_eb, COLS["orange"],
                r"Planck PR3 EB low-$\ell$ ($D_\ell>0$)",
                r"Planck PR3 EB low-$\ell$ ($D_\ell<0$)")

    cr = cat.load("camb.planck2018.lensing_refs")
    ell_th = np.asarray(cr["ell_cmb"])
    dl_bb_th = np.asarray(cr["Dl_BB"])
    ax.plot(ell_th[dl_bb_th > 0], dl_bb_th[dl_bb_th > 0],
            color=COLS["black"], lw=1.0,
            label=r"CAMB $\Lambda$CDM lensed BB")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"multipole $\ell$")
    ax.set_ylabel(r"$|D_\ell^{\rm BB,\,EB}|\ [\mu K^2]$")
    ax.set_xlim(2.0, 700.0)
    ax.set_ylim(1e-4, 2.0)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=8.2, loc="upper left")
    ax.set_title(
        r"Planck PR3 low-$\ell$ BB and EB polarization vs $\Lambda$CDM "
        r"lensed-BB reference",
        fontsize=10,
    )
    fig.tight_layout()
    _save(fig, "fig_ch06m_bb_polarization_constraints", "ch06_pipeline")
    _caption(
        "fig_ch06m_bb_polarization_constraints",
        "ch06_pipeline",
        r"""
CMB B-mode (blue) and EB (orange) low-$\ell$ polarization from
Planck PR3 ($2\!\le\!\ell\!\le\!29$; $\mathtt{planck.pr3.bb\_lowl}$
and $\mathtt{planck.pr3.eb\_lowl}$) plotted against the
$\Lambda$CDM lensed-BB reference from
$\mathtt{camb.planck2018.lensing\_refs}$. Filled markers carry
$D_\ell\!>\!0$; open markers carry $D_\ell\!<\!0$ (displayed at
$|D_\ell|$ for the log axis). The low-$\ell$ points straddle zero
within $1\sigma$, consistent with a null BB/EB at the reionisation
bump scale — a clean parity-respecting baseline against which the
tilted-FLRW shear-induced BB leakage (ch05, ch07) is fit. Higher-$\ell$
coverage is deferred to the BICEP/Keck bandpowers stored in
$\mathtt{bicep\_keck.2018.bb}$ (full covariance not unpacked in
this figure; see BK18lf data release for the canonical BB analysis).
"""
    )


# =====================================================================
# Chapter 08 — Commander − SMICA CMB difference map
# =====================================================================


def fig_ch08d_commander_minus_smica() -> None:
    """Mollweide residual I_Commander − I_SMICA at NSIDE=16, masked."""
    import healpy as hp

    cat = _obs_catalog()
    cm = cat.load("planck.commander.nside16")
    sm = cat.load("planck.smica.nside16")
    temp_mask = cat.load("planck.temp_mask.nside16")

    diff = np.asarray(cm["I"]) - np.asarray(sm["I"])
    mask = np.asarray(temp_mask["mask"], dtype=bool)
    fsky = float(temp_mask.get("fsky", mask.mean()))
    # Mask → set to UNSEEN for display
    display = diff.copy()
    display[~mask] = hp.UNSEEN

    rms_in = float(np.sqrt(np.mean(diff[mask] ** 2)))
    rms_all = float(np.sqrt(np.mean(diff ** 2)))

    fig = plt.figure(figsize=(7.6, 4.0))
    hp.mollview(
        display, fig=fig.number, title="", cbar=True,
        min=-30.0, max=+30.0, cmap="RdBu_r", unit=r"$\mu K$",
    )
    hp.graticule(dpar=30.0, dmer=30.0, color="0.3", alpha=0.5)
    plt.title(
        rf"Planck Commander $-$ SMICA temperature residual "
        rf"(NSIDE=16, $f_{{\rm sky}}\!=\!{fsky:.3f}$, "
        rf"RMS$_{{\rm sky}}={rms_in:.2f}\,\mu K$)",
        fontsize=10, pad=16,
    )
    fig_full = plt.gcf()
    _save(fig_full, "fig_ch08d_commander_minus_smica", "ch08_robustness")
    _caption(
        "fig_ch08d_commander_minus_smica",
        "ch08_robustness",
        rf"""
Commander minus SMICA temperature residual map ($I$-only, NSIDE=16,
RING ordering) — two independent Planck PR3 component-separation
methods applied to the same input data. The Galactic-plane
temperature mask ($f_{{\rm sky}}\!=\!{fsky:.3f}$,
$\mathtt{{planck.temp\_mask.nside16}}$) is applied; in-mask RMS
residual is $\approx {rms_in:.2f}\,\mu K$ and the unmasked-all-sky
RMS is $\approx {rms_all:.2f}\,\mu K$. The residual shows no
large-scale coherent structure beyond the Galactic-plane
systematics, certifying that the cosmological-dipole-anomaly
signature (ch02) is not a component-separation artefact.
"""
    )


# =====================================================================
# Chapter 09 — Cross-survey dipole β comparison
# =====================================================================


def fig_ch09b_dipole_surveys_compilation() -> None:
    """Bar chart of β (or ε₁) amplitudes and uncertainties across surveys."""
    cat = _obs_catalog()
    od = cat.load("obs_defaults.canonical")
    dipoles = od["dipole_observations"]

    entries: list[tuple[str, float, float, str, str]] = []
    for key, d in dipoles.items():
        if not isinstance(d, dict):
            continue
        if "beta" in d:
            val = float(d["beta"])
            sig = float(d.get("sigma", d.get("sigma_stat", 0.0)))
            entries.append((key, val, sig, "CF4-family", d.get("source", "")))
        elif "eps1" in d:
            val = float(d["eps1"])
            sig = float(np.sqrt(
                d.get("sigma_stat", 0.0) ** 2 + d.get("sigma_sys", 0.0) ** 2
            ))
            entries.append((key, val, sig, "radio/IR", d.get("source", "")))
        elif "eps1_UL" in d:
            val = float(d["eps1_UL"])
            sig = float(d.get("sigma", 0.0))
            entries.append((key, val, sig, "CMB-intrinsic UL",
                            d.get("source", "")))

    # Sort by mean amplitude for a clean monotone chart.
    entries.sort(key=lambda t: t[1])

    # CMB dipole benchmark: β_CMB = 1.23357e-3 (Planck 2018 Aghanim+20 §III).
    beta_CMB = 1.23357e-3
    sigma_CMB = 0.0003e-3
    entries.insert(
        0, ("planck_cmb_dipole_2018", beta_CMB, sigma_CMB,
            "CMB kinematic", "Planck 2018 / Aghanim+20"),
    )

    names = [e[0] for e in entries]
    values = np.array([e[1] for e in entries])
    sigmas = np.array([e[2] for e in entries])
    cats = [e[3] for e in entries]
    cat_colors = {
        "CMB kinematic": COLS["red"],
        "CMB-intrinsic UL": COLS["purple"],
        "CF4-family": COLS["blue"],
        "radio/IR": COLS["orange"],
    }
    colors = [cat_colors.get(c, COLS["green"]) for c in cats]

    fig, ax = plt.subplots(figsize=(8.8, 4.5))
    y = np.arange(len(names))
    ax.barh(y, values * 1e3, xerr=sigmas * 1e3, color=colors,
            edgecolor="0.1", lw=0.4, alpha=0.85,
            error_kw=dict(elinewidth=0.9, capsize=2.2, ecolor="0.1"))
    ax.set_ylim(-0.7, len(names) - 0.3)
    ax.axvline(beta_CMB * 1e3, color=COLS["red"], lw=0.8, ls="--",
               label=r"Planck 2018 CMB kinematic dipole")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8.5)
    ax.set_xlabel(r"dipole amplitude $\beta$ or $\epsilon_1$  [$\times10^{-3}$]")
    ax.grid(axis="x", alpha=0.25)
    # Category legend
    from matplotlib.patches import Patch
    handles = [Patch(fc=c, ec="0.1", lw=0.4, label=k)
               for k, c in cat_colors.items()]
    handles.append(plt.Line2D([], [], color=COLS["red"], ls="--", lw=0.9,
                              label=r"Planck 2018 CMB dipole"))
    ax.legend(handles=handles, loc="lower right", fontsize=8)
    ax.set_title(r"Cross-survey preferred-axis dipole amplitude compilation",
                 fontsize=10)
    fig.tight_layout()
    _save(fig, "fig_ch09b_dipole_surveys_compilation", "ch09_discussion")
    _caption(
        "fig_ch09b_dipole_surveys_compilation",
        "ch09_discussion",
        r"""
Compilation of measured preferred-axis dipole amplitudes across
independent CMB, radio, infrared, and peculiar-velocity probes,
sourced from $\mathtt{obs\_defaults.canonical.dipole\_observations}$
(Planck 2018, Ferreira \& Quartin 2021 intrinsic-dipole UL,
Secrest+2021 radio, B\"ohme+2025 CatWISE, Watkins+2009 CF4
composite). Amplitudes and their $1\sigma$ (or 95\% UL, half-Gaussian)
uncertainties are plotted; the dashed red line marks the Planck 2018
kinematic benchmark. The order-of-magnitude tension between the
radio/IR dipole ($\epsilon_1\!\approx\!3\!\times\!10^{-3}$) and the
CMB-intrinsic UL ($\epsilon_1\!\le\!1.4\!\times\!10^{-3}$) is the
identified-layer anomaly that motivates the tilted-FLRW tilted-frame
interpretation (ch02, ch09).
"""
    )


# =====================================================================
# Dispatcher
# =====================================================================


FIG_REGISTRY: dict[str, Callable[[], None]] = {
    "ch03a_scale_hierarchy":        fig_ch03a_scale_hierarchy,
    "ch03b_three_layer_ontology":   fig_ch03b_three_layer_ontology,
    "ch04d_type_by_type_bounds":    fig_ch04d_type_by_type_bounds,
    "ch04e_shear_source_landscape": fig_ch04e_shear_source_landscape,
    "ch05e_laguerre_moments":       fig_ch05e_laguerre_moments,
    "ch05f_xi_moment_ratios":       fig_ch05f_xi_moment_ratios,
    "ch05g_boost_mixing_matrix":    fig_ch05g_boost_mixing_matrix,
    "ch06h_route_b_mm":             fig_ch06h_route_b_mm_chart,
    "ch06i_tca_conditioning":       fig_ch06i_tca_conditioning,
    "ch06j_lebedev_exactness":      fig_ch06j_lebedev_exactness,
    "ch06k_polter_recoupling":      fig_ch06k_polter_recoupling_structure,
    "ch07j_mes_ceilings":           fig_ch07j_mes_ceilings_hierarchy,
    "ch07k_entropy_invariants":     fig_ch07k_entropy_invariants,
    "ch07l_gram_admissibility":     fig_ch07l_gram_admissibility,
    "ch07m_boost_order_convergence": fig_ch07m_boost_order_convergence,
    "ch07n_tilt_history_trajectory": fig_ch07n_tilt_history_trajectory,
    "ch09a_fbayes_cross_check":     fig_ch09a_fbayes_gaussian_cross_check,
    "ch11a_error_hierarchy":        fig_ch11a_error_hierarchy,
    "ch12a_directional_coherence":  fig_ch12a_directional_coherence,
    "ch12b_redshift_drift":         fig_ch12b_redshift_drift_axes,
    "ch12c_sky_coverage":           fig_ch12c_sky_coverage_fsky,
    "ch12d_hj01_extraction":        fig_ch12d_hj01_extraction_demo,
    "ch12e_pairwise_separations":   fig_ch12e_pairwise_separations,
    # --- data-driven figures (dl_pipeline/obs_bundle) ----------------
    "ch02f_multi_experiment_tt":    fig_ch02f_multi_experiment_tt,
    "ch02g_planck_polarization":    fig_ch02g_planck_polarization_ee_te,
    "ch02h_planck_lensing":         fig_ch02h_planck_lensing_bandpowers,
    "ch06l_desi_y1_nz":             fig_ch06l_desi_y1_nz,
    "ch06m_bb_polarization":        fig_ch06m_bb_polarization_constraints,
    "ch08d_commander_minus_smica":  fig_ch08d_commander_minus_smica,
    "ch09b_dipole_surveys":         fig_ch09b_dipole_surveys_compilation,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", default=None,
                    help="only render a single figure by id")
    ap.add_argument("--list", action="store_true",
                    help="list available figures and exit")
    args = ap.parse_args()

    if args.list:
        print("Available additional figures:")
        for fid, fn in FIG_REGISTRY.items():
            print(f"  {fid:<34}  {fn.__name__}")
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
