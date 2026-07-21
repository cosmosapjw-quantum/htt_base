"""Build the v10 external research report (successor of the v5-v9 line).

v10 is a SELF-CONTAINED scientific record: definitions, theorems with
full statements and proofs, data-analysis results with figures, a
K/C/P/S novelty-tier ledger, the data-completeness statement, and a
reproducibility appendix. It contains no development-history or
process-narrative content; provenance appears only as artifact paths
and hashes.

``--write`` renders external_audit_research_report_20260721_v10/
(TeX + figures + manifest + README + CITATION), compiles the PDF with
pdflatex (x3), and zips the package. ``--check`` regenerates every text
artifact in memory and byte-diffs against disk (PDF/zip excluded:
pdflatex embeds timestamps).

The v5-v9 builders and packages are frozen and untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "external_audit_research_report_20260721_v10"
TEX_NAME = "external_audit_research_report_v10.tex"
PDF_NAME = "external_audit_research_report_v10.pdf"
ZIP_NAME = "external_audit_research_report_20260721_v10.zip"
FIG_SRC = ROOT / "figures/data_analysis_current/v10"
FIG_DEST_NAME = "report_figures"

# Data-completeness constants FROZEN at the build-date probe (the report
# is a fixed artifact; live re-probing would break byte-stability).
DESI_PROBE_DATE = "2026-07-21"
DESI_EZ_AUTH = 290
DESI_EZ_TARGET = 1000
DESI_ABACUS_TARGET = 25

REQUIRED_ARTIFACTS = [
    "docs/generated/pr150_e2e_pooled_rank.json",
    "docs/generated/k1_global_maxscan_e2e_full.json",
    "docs/generated/k1_evenl_biposh_rank_card.json",
    "docs/generated/pr180_result_card.json",
    "docs/generated/pr145_bulk_flow_report.json",
    "docs/generated/pr147_identified_set.json",
    "docs/generated/pr148_fsigma8_by_depth.json",
    "docs/generated/desi_dipole_mock_card.json",
    "docs/generated/desi_exact_selection_card.json",
    "docs/generated/act_kappa_card.json",
    "docs/generated/pr177_result_card.json",
    "docs/generated/pr179_result_card.json",
    "docs/generated/pr179_response_identifiability.json",
    "docs/generated/mes_geodesic_refreeze_seal.json",
    "docs/generated/mes_branch_registry_seal.json",
    "docs/generated/k5_omega_k_ceiling_card.json",
    "docs/generated/pr131_coefficients.json",
    "docs/generated/pr175_result_card.json",
    "docs/generated/v10_report_figure_manifest.json",
    "docs/audits/v10_web_crag_20260721/tier_evidence.json",
]

FIGURES = [
    "fig_v10_comparator_region",
    "fig_v10_k1_rank_hist",
    "fig_v10_k1_evenl_rank",
    "fig_v10_boost_biposh_features",
    "fig_v10_cf4_depth",
    "fig_v10_desi_dipole",
    "fig_v10_act_kappa",
    "fig_v10_pr179_conditional",
    "fig_v10_omk_slaving",
    "fig_v10_ricci_gaps",
]


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text())


def _values() -> dict[str, str]:
    """Load every card-sourced number rendered in the report."""
    v: dict[str, str] = {}
    pooled = _load("docs/generated/pr150_e2e_pooled_rank.json")
    v["K1_GLOBAL_P"] = f"{pooled['look_elsewhere_global_p']:.3f}"
    cycle = pooled["noise_reuse_sensitivity"]["cycle_p_range"]
    v["K1_SENS_LO"] = f"{cycle[0]:.4f}"
    v["K1_SENS_HI"] = f"{cycle[1]:.4f}"
    locp = pooled["per_statistic_local_p"]
    v["K1_LOCAL_ROWS"] = " \\\\\n".join(
        f"\\code{{{k.replace('_', '\\_')}}} & {p:.3f}"
        for k, p in sorted(locp.items())
    )
    v["K1_FLOOR"] = f"{pooled['resolution_floor']:.3f}"

    ev = _load("docs/generated/k1_evenl_biposh_rank_card.json")["result"]
    v["EVENL_P"] = f"{ev['pooled']['rank_p']:.3f}"
    v["EVENL_L2_P"] = f"{ev['per_L_secondary']['L2']['rank_p']:.3f}"
    v["EVENL_L4_P"] = f"{ev['per_L_secondary']['L4']['rank_p']:.3f}"
    v["EVENL_ODDZERO"] = f"{ev['odd_l_structural_zero_max_ratio']:.1e}"

    b = _load("docs/generated/pr180_result_card.json")["result"]
    v["BOOST_P"] = f"{b['rank_p']:.3f}"
    v["BOOST_SCORE"] = f"{b['observed_score']:.3f}"
    v["BOOST_LIN"] = f"{b['linearity_ratio_f2h_over_fh']:.4f}"

    cf = _load("docs/generated/pr145_bulk_flow_report.json")
    v["CF4_AMP"] = f"{cf['constrained_flow_amplitude_kms']:.0f}"
    v["CF4_MONO"] = f"{cf['constrained_monopole_kms']:.0f}"
    v["CF4_FULLCOV_SIG"] = f"{cf['full_covariance_sigma']:.2f}"
    v["CF4_NOISE_SIG"] = f"{cf['noise_only_sigma']:.1f}"

    shells = _load("docs/generated/pr147_identified_set.json")["shells"]
    rows = []
    for s in shells:
        lo, hi = s["amplitude_interval_kms"]
        rows.append(
            f"{s['dist_lo_mpc']:.0f}--{s['dist_hi_mpc']:.0f} & "
            f"[{lo:.0f}, {hi:.0f}] & {s['apex_cone_deg']:.0f}"
        )
    v["CF4_SHELL_ROWS"] = " \\\\\n".join(rows)

    g = _load("docs/generated/pr148_fsigma8_by_depth.json")
    s0 = g["shells"][0]
    v["FS8_NEAR"] = f"{s0['fsigma8']:.3f}"
    v["FS8_NEAR_SIG"] = f"{s0['mock_sigma']:.3f}"
    v["FS8_FID"] = f"{g['fiducial_fsigma8']:.3f}"
    v["FS8_NCON"] = str(g["n_constrained_shells"])

    dm = _load("docs/generated/desi_dipole_mock_card.json")
    v["DESI_D"] = f"{dm['observed_dipole_amplitude']:.2e}"
    v["DESI_P15"] = f"{dm['lcdm_clustering_mock_null']['1.5']['p_value']:.2f}"

    act = _load("docs/generated/act_kappa_card.json")
    v["ACT_P"] = f"{act['p_value_data_vs_isotropic_sims']:.2f}"
    v["ACT_UL"] = f"{act['upper_limit_95cl']['band_power_95ul']:.2e}"
    v["ACT_UL_RATIO"] = \
        f"{act['upper_limit_95cl']['band_power_95ul_over_sim_median']:.2f}"
    p177 = _load("docs/generated/pr177_result_card.json")
    v["ACT_INBAND_RANK"] = \
        p177["rank_summary"]["controlled"]["rank_fraction"]

    p9 = _load("docs/generated/pr179_result_card.json")
    fr = p9["finite_rank"]
    v["H_RANK_FRAC"] = fr["finite_resolution_fraction"]
    v["H_RANK_EST"] = f"{fr['estimate']:.1e}"
    v["H_GUARD_LO"] = f"{fr['guard_interval'][0]:.1e}"
    v["H_GUARD_HI"] = f"{fr['guard_interval'][1]:.1e}"
    ident = _load("docs/generated/pr179_response_identifiability.json")
    qcc = [f["q_directional_cubic_canonical_correlation"]
           for f in ident["folds"]]
    v["Q_CC_LO"] = f"{min(qcc):.3f}"
    v["Q_CC_HI"] = f"{max(qcc):.3f}"

    mes = _load("docs/generated/mes_geodesic_refreeze_seal.json")
    anchor = mes["refrozen_anchor"]
    v["W2_GEO"] = f"{anchor['W2_max']:.4e}"
    v["S2_MAX"] = f"{anchor['Sigma2_max']:.4e}"
    br = _load("docs/generated/mes_branch_registry_seal.json")[
        "w2_ceiling_branches"]
    v["W2_REG"] = f"{float(br['registered']['value_float']):.4e}"
    v["W2_HYB"] = f"{float(br['hybrid_literature']['value_float']):.4e}"

    omk = _load("docs/generated/k5_omega_k_ceiling_card.json")["ceiling_rows"]
    rows = []
    for name in sorted(omk):
        r = omk[name]
        rows.append(
            f"\\code{{{name.replace('_', '\\_')}}} & "
            f"{r['abs_kappa']} & {r['omega_k_ceiling_abs']:.2e}"
        )
    v["OMK_ROWS"] = " \\\\\n".join(rows)

    p175 = _load("docs/generated/pr175_result_card.json")["oracle"]
    gaps = [t["engine_b_gap_abs"] for t in p175["types"].values()]
    v["RICCI_MAXGAP"] = f"{max(gaps):.2e}"
    return v


# --------------------------------------------------------------------------
# LaTeX
# --------------------------------------------------------------------------

PREAMBLE = r"""\documentclass[10pt]{article}
\usepackage[margin=2.6cm]{geometry}
\usepackage{amsmath,amssymb,amsthm,bm}
\usepackage{graphicx}
\usepackage{booktabs,longtable}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{lemma}[theorem]{Lemma}
\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newcommand{\code}[1]{\texttt{\small #1}}
\newcommand{\tier}[1]{\textbf{[#1]}}
\newcommand{\OmT}{\Omega_{\mathrm{tilt}}}
\newcommand{\dOk}{\Delta\Omega_{k}}
\graphicspath{{./report_figures/}}
\title{Tetrad-Based FLRW-Departure Diagnostics in Bianchi Cosmologies:\\
Exact Theorems, Statistical Architecture, and Current-Data Results\\
{\large Research Report v10 (Eighth Revision line; self-contained)}}
\author{BASS/HTT research programme}
\date{2026-07-21}
\begin{document}
\maketitle
\tableofcontents
\clearpage
"""


def s1_scope() -> str:
    return r"""
\section{Scope, claim discipline, and data completeness}

This report is a self-contained scientific record of the programme's
exact mathematical results, statistical architecture, and current-data
analyses as of 2026-07-21. Every proposition is stated with its proof;
every data result carries its conditionality; and every claim carries a
novelty tier from the four-level scheme of
Section~\ref{sec:tiers} --- \tier{K} known, \tier{C} cross-check,
\tier{P} potential advance, \tier{S} significant claimable --- so a
reader can separate standard material, reproductions of external
results, and candidate advances at a glance. Earlier package versions
(v5--v9) remain byte-frozen; this version supersedes them as the
current record and does not repeat their revision-response
correspondence.

\subsection{Data completeness statement}
\label{sec:completeness}

One acquisition that gates a registered analysis chain is
\emph{incomplete at the time of writing}: the official DESI~DR1
validation-mock ensemble (1000 EZmock plus @DESI_ABACUS_TARGET@
AbacusSummit realizations). At the @DESI_PROBE_DATE@ build probe,
@DESI_EZ_AUTH@ of @DESI_EZ_TARGET@ EZmock realizations were
authenticated on local storage and the transfer was proceeding
normally; completion requires additional days of transfer time at the
observed rate. By pre-registered design, \emph{partial} mock ensembles
never enter any rank, p-value, covariance, or significance computation
reported anywhere in this document; every DESI statement below is
therefore either (i) a window/selection diagnostic that does not use
the official mocks, or (ii) explicitly deferred
(Section~\ref{sec:pending}). Two further data-availability conditions
are recorded: the Planck PR4/NPIPE product line is outside the analysis
scope of this report, and the Commander-processed FFP10 end-to-end
ensemble (which would enable a second-pipeline replication of the
Section~\ref{sec:k1} results) has not been acquired.

\subsection{What this report never claims}

No result herein is a detection of cosmological anisotropy, a Bianchi
family identification, a measurement of spatial-curvature anisotropy,
or a validation of a native anisotropic radiative-transfer solver. All
sky-statistics are conditional on the stated pipelines and null
ensembles; all exact theorems are conditional on their stated premises;
and the small number of results with promotion potential are tagged and
bounded in Section~\ref{sec:tiers}.
"""


def s2_conventions() -> str:
    return r"""
\section{Conventions and the measured object}
\label{sec:conv}

\subsection{Frames and decomposition \tier{K}}

The spacetime signature is $(-,+,+,+)$. A timelike unit congruence
$n^a$ defines the projector $h_{ab} = g_{ab} + n_a n_b$ and the
covariant decomposition
\begin{equation}
\nabla_a n_b = -A_b n_a + \tfrac{1}{3}\Theta h_{ab} + \sigma_{ab}
 + \omega_{ab},
\end{equation}
with acceleration $A_a$, expansion $\Theta = 3H$, shear $\sigma_{ab}$,
and vorticity $\omega_{ab}$ \cite{EllisVanElst1999}. Normal frame,
matter frame, and observer boost frame are never interchangeable;
overclaims arise precisely from treating a local boost vector as a
homogeneous matter tilt. For an invariant spatial metric the
projected-symmetric-trace-free (PSTF) projection is used throughout.

\subsection{The registered component vector and comparator \tier{K}}

\begin{definition}[Component vector and signed comparator]
\label{def:g}
The public mathematical object is
\begin{equation}
\bm g = (g_\Sigma, g_W, g_t, g_k)
      = \left(\Sigma^2,\, W^2,\, \OmT,\, \dOk\right),
\qquad
\Sigma^2 = \frac{\sigma_{ab}\sigma^{ab}}{6H^2},\quad
W^2 = \frac{\omega_a \omega^a}{H^2},
\end{equation}
with $\OmT$ the dimensionless tilt contribution of a declared
matter-frame velocity model and $\dOk$ the anisotropic-curvature
comparator component after isotropic curvature has been separated.
The signed comparator is the linear functional
\begin{equation}
x_C = c^{\mathsf T}\bm g, \qquad c = (1,-1,1,1)^{\mathsf T}.
\end{equation}
\end{definition}

\begin{proposition}[Domain-checked semantics]
\label{prop:domain}
$x_C$ is reportable only when all four components are present in a
common convention; a missing component must yield an
unidentified-component status, never an imputed zero.
\end{proposition}
\begin{proof}
The equality $x_C = \Sigma^2 - W^2 + \OmT + \dOk$ is an algebraic
identity of the registered decomposition; omitting a component changes
the proposition being evaluated. Because the vorticity enters with a
negative sign, an omitted $W^2$ can change both the sign and the
cancellation structure of $x_C$, so silent imputation is not merely
imprecise but sign-unsafe.
\end{proof}

\subsection{The tilt closed form \tier{K}}

For a single-stream tilt of magnitude $v$ (rapidity
$\beta = \operatorname{artanh}(v/c)$) in a background with matter
density parameter $\Omega_m$ and equation of state $w$, the registered
closed form is
\begin{equation}
\OmT = (1+w)\,\Omega_m \sinh^2\!\beta ,
\label{eq:omtilt}
\end{equation}
which is the exact special-relativistic energy-flux normalization of
the tilted stress tensor; at $v \ll c$ it reduces to
$\Omega_m v^2/c^2$ for dust.

\subsection{Typed quantities and estimand registration \tier{P}}

\begin{proposition}[Type separation]
\label{prop:types}
The kinematic dipole proxy $A_v$, the physical tilt $\OmT$, the
vorticity $W^2$, the shear $\Sigma^2$, and the curvature component
$\dOk$ admit no valid cross-type arithmetic except along explicitly
registered bridge maps; in particular no chain of operations may
convert $A_v$ into $\OmT$ without a declared boost-removal step.
\end{proposition}
\begin{proof}
Each quantity is defined relative to a distinct frame and order in the
boost expansion: $A_v$ is first order in $\beta$ and odd under boost
reversal, $\OmT$ is second order and even, and the geometric components
are boost-independent at the registered order. A map between them
therefore requires a declared frame transformation carrying its own
order bookkeeping; composing raw magnitudes across types silently
mixes expansion orders, which is exactly the historical source of
dipole-to-tilt overclaims. The programme enforces this as a type
system whose only cross-type morphisms are the registered bridges,
each stamping provenance onto its output.
\end{proof}

Analysis contracts (target population, observation unit, dependence
cluster, selection window, preprocessing, estimand, nuisance family,
multiplicity, allowed transformations, generative branch) are
registered per dataset before estimation; unregistered fields fail
closed. This registration practice is standard \tier{K}; its
fail-closed typed implementation across the five data lanes of
Section~\ref{sec:data} is programme-specific.
"""


def s3_stats() -> str:
    return r"""
\section{Statistical architecture: theorems with proofs}
\label{sec:stats}

\subsection{Identified intervals for the comparator}

\begin{theorem}[Signed-box interval]
\label{thm:t1p}
Let each component of $\bm g$ be known only up to an interval,
$g_i \in [a_i, b_i]$ with $a_i \le b_i$. Then the identified set of
$x_C = c^{\mathsf T}\bm g$ is the exact interval
\begin{equation}
x_C \in \Big[\,a_\Sigma - b_W + a_t + a_k,\;
             b_\Sigma - a_W + b_t + b_k\,\Big],
\end{equation}
and both endpoints are attained.
\end{theorem}
\begin{proof}
$x_C$ is linear in $\bm g$ with coefficient signs $(+,-,+,+)$; a linear
functional on a box attains its extrema at vertices, choosing per
coordinate the endpoint matching the coefficient sign. The displayed
choice minimizes (respectively maximizes) each term independently,
which is feasible because the box is a product set.
\end{proof}

\begin{theorem}[Exact axis-separable identified sets]
\label{thm:idset}
For a constraint system on $\bm g$ consisting of per-axis equalities
and inequalities with rational data, the identified set is the product
of per-axis intervals obtained by exact interval intersection, and its
classification (bounded / empty / unbounded / disconnected) is
decidable in exact arithmetic. If the response map has a nontrivial
null space, every axis in the null space is unbounded unless an
external ceiling constrains it.
\end{theorem}
\begin{proof}
Axis-separability means the feasible set is a product of
one-dimensional sets, each an intersection of finitely many rational
half-lines and points, hence an interval (or a finite union after
explicit disjunctions), computable by exact rational comparisons.
Emptiness is an inconsistent intersection; unboundedness is a missing
finite endpoint. The null-space statement follows because data
constraints act only through the row space: adding any multiple of a
null vector leaves every constraint satisfied.
\end{proof}

\begin{theorem}[Rank-two response and the blind sector \tier{P}]
\label{thm:rank2}
For the registered CMB-temperature and radial-velocity response
templates at the stated order, the response matrix on
$\bm g$ has rank two, with null space
$\operatorname{span}\{e_{W^2}, e_{\dOk}\}$. Consequently $(W^2, \dOk)$
is a joint null sector: no data combination in these channels
identifies it, and the correct output for that sector is an identified
set or a ceiling, never a point value.
\end{theorem}
\begin{proof}
The temperature and radial-velocity templates span two independent
directions in the four-component basis. The antisymmetric vorticity
contribution vanishes in the radial contraction $n^a n^b \omega_{ab} =
0$, and the leading anisotropic-curvature component has no registered
response column at this order. Two independent rows with two vanishing
columns give rank two with the stated kernel; the identification
consequence is Theorem~\ref{thm:idset}'s null-space clause. The rank
and kernel are certified by two independent computer-algebra engines
over the rationals (artifact
\code{docs/generated/} response-map seals).
\end{proof}

\subsection{Fractional-program and fingerprint bounds}

\begin{theorem}[General fractional-program interval \tier{K}]
\label{thm:t2g}
Let $G_F(z) = N(z)/D(z)$ with $N, D$ affine on a compact interval
domain $S$ and $D > 0$ on $S$. Then the range of $G_F$ is the exact
interval whose endpoints are attained on the boundary of $S$, and the
depth-gap is \emph{strict} on an interior subinterval if and only if
the affine coefficients satisfy the registered non-degeneracy
inequality --- in particular, ``strict whenever the numerator moves''
is false: with $S = [0,1]$, $N = s$, $D = 1+s$, the gap degenerates at
the boundary although $N$ is non-constant.
\end{theorem}
\begin{proof}
An affine-over-affine ratio is monotone on any interval where the
denominator keeps one sign (its derivative has the constant sign of
$N'D - ND'$), so extrema sit at interval endpoints and the range is an
interval. The iff follows by solving $N'D - ND' = 0$ for the
degeneracy locus; the displayed counterexample evaluates it inside the
hypotheses. Diagonal attainment and the corollary that any
maximizer/minimizer pair with $N > 0$ meets the diagonal are checked
in exact rational arithmetic over the registered domain
(polyhedral certification in two engines).
\end{proof}

\begin{proposition}[Fingerprint sum bound \tier{K}]
\label{prop:tsum}
For the moment fingerprints $R_3, R_5$ of the registered two-point
family with mixing parameter $s \in [0,1]$, $R_3 + R_5 \ge 2$ with
equality exactly at $s = 0$.
\end{proposition}
\begin{proof}
The moment determinant identity
$\mu_3\mu_5 - \mu_4^2 = s^2(1-s^2)^3 \ge 0$ makes the pair
$(R_3, R_5)$ reciprocal-conjugate up to a nonnegative defect, so
AM--GM gives $R_3 + R_5 \ge 2\sqrt{R_3 R_5} \ge 2$, with both
inequalities tight only when the defect vanishes at $s = 0$.
\end{proof}

\subsection{Exchangeable finite-null ranking}

\begin{theorem}[Observation-inclusive exact rank \tier{K}]
\label{thm:rank}
Let $S_0$ be a statistic of the observation and $S_1,\dots,S_N$ the
same statistic of $N$ null simulations, with
$(S_0, S_1, \dots, S_N)$ exchangeable under the null. Then
\begin{equation}
p = \frac{1 + \#\{i : S_i \ge S_0\}}{N + 1}
\end{equation}
satisfies $\mathbb P(p \le \alpha) \le \alpha$ for every $\alpha$, is
never zero, and has resolution floor $1/(N+1)$
\cite{PhipsonSmyth2010}.
\end{theorem}
\begin{proof}
Under exchangeability the rank of $S_0$ among the $N{+}1$ values is
uniform on $\{1,\dots,N{+}1\}$ up to ties, and ties only increase $p$.
Then $\mathbb P(p \le k/(N{+}1)) = k/(N{+}1)$ for integer $k$, giving
validity on the discrete support; $p \ge 1/(N+1)$ by construction.
\end{proof}

\begin{corollary}[Look-elsewhere pooling \tier{P}]
\label{cor:pool}
If $M$ statistics are pre-registered and each simulation and the
observation are reduced to their within-sky maximum standardized score,
Theorem~\ref{thm:rank} applied to the max-scan scores yields a global
p that is exact with respect to the full search over the $M$
statistics, with no independence assumption among them.
\end{corollary}
\begin{proof}
The max-scan reduction is applied identically to observation and
simulations, so the reduced scores inherit exchangeability; the
correction for searching over $M$ statistics is automatic because the
null distribution of the maximum is sampled directly.
\end{proof}

The report's low-multipole global p (Section~\ref{sec:k1}) and every
rank herein use this construction, with a hard validation that the
reported value lies on the support grid at or above the floor.

\begin{proposition}[Exceedance calibration \tier{K}]
\label{prop:evalue}
If a registered statistic $S \ge 0$ satisfies $\mathbb E_0 S \le 1$
under a documented null, then $\mathbb P_0(S \ge t) \le 1/t$ for all
$t > 0$; absent the null-mean condition the exceedance curve $\Pi(t)$
is descriptive only.
\end{proposition}
\begin{proof}
Markov's inequality under the null measure. The proof requires the
null expectation bound; without it the same curve summarizes observed
threshold exceedance but carries no error control, which is why the
interface refuses e-value language for uncalibrated statistics.
\end{proof}

\begin{proposition}[Simulation-based calibration with lineage
\tier{K}]
\label{prop:sbc}
For a posterior sampler tested by the rank procedure of Talts et al.:
if the sampler is exact, the rank of the true parameter among
posterior draws is uniform, so the binned ranks are jointly
multinomial with equal cells and the $\chi^2$ test is calibrated at
its stated degrees of freedom. The programme additionally binds every
posterior-draw object to the content address of its prior,
likelihood, data, and configuration, so a calibration certificate can
never be attached to draws it was not computed from.
\end{proposition}
\begin{proof}
Uniformity: for exact posteriors, $(\theta, y)$ and every posterior
draw given $y$ are exchangeable, making the rank uniform by symmetry.
The $\chi^2$ statement is the standard multinomial limit at the
registered bin count. The binding statement is by construction of the
content address; on the registered test system a correct sampler
passes ($p \approx 0.09$) while variance-mis-scaled samplers fail at
overwhelming significance, and tampered lineage is detected as a hash
mismatch.
\end{proof}

\subsection{Low-multipole covariance propositions}

\begin{proposition}[Quadrupole filling under the registered closure
\tier{K}]
\label{prop:fill}
If $a_2 = \kappa\Sigma$ with $\kappa > 0$, $F_{\rm shear} =
\Sigma^2/x_{\max}$, and $D_2 = c_D a_2^2$, then
$F_{\rm shear} = D_2 / (c_D \kappa^2 x_{\max})$, so the filling
vanishes as the quadrupole amplitude vanishes under the closure.
\end{proposition}
\begin{proof}
Substitute $\Sigma = a_2/\kappa$ into $F_{\rm shear}$ and use the
$D_2$ definition; conclusion is closure-conditional and asserts
nothing about the origin of any observed quadrupole.
\end{proof}

\begin{proposition}[Single-sky dispersion and the Fisher floor
\tier{K}]
\label{prop:floor}
For an ideal full-sky Gaussian estimator,
$\mathrm{Var}(\widehat C_\ell) = 2C_\ell^2/(2\ell+1)$, giving a
fractional dispersion $\sqrt{2/5}$ at $\ell = 2$ for any statistic
linear in $\widehat C_2$; for a registered multi-$\ell$ response
profile with weights $r_\ell$ the attainable fractional floor scales
as $(\sum_\ell (2\ell+1) f_{\rm sky} r_\ell^2 / 2)^{-1/2}$.
\end{proposition}
\begin{proof}
The $\chi^2_{2\ell+1}$ moment identity gives the single-$\ell$
variance ($2\ell+1$ real degrees of freedom under the reality
condition --- the naive complex-mode count is a documented historical
miscount); independent harmonic modes add Fisher information
proportionally to multiplicity, sky support, and squared response
weight, and an efficient estimator attains the inverse root of the
summed information in the reachable direction. Both statements are
estimator- and profile-conditional, never data statements.
\end{proof}

\begin{theorem}[Diagonal compression loses morphology \tier{K}]
\label{thm:compress}
For statistically isotropic covariance only the $L = 0$,
$\ell = \ell'$ sector of the bipolar decomposition survives;
consequently diagonal $C_\ell$ summaries are blind to all $L > 0$
covariance morphology, and a full-covariance ceiling
$B^{\rm final} = \min\{B^{\rm diag}, B^{\rm cov}\}$ can only tighten
a diagonal ceiling, with a mandatory no-result status when the
nuisance-projected singular value in the component direction is zero.
\end{theorem}
\begin{proof}
Statistical isotropy forces the covariance to commute with rotations;
Schur orthogonality then leaves only the scalar representation in the
bipolar basis. The min rule can only lower or preserve a bound; a
zero projected singular value means the covariance block carries no
information about the component, and fabricating a finite number
there would be a modelling prior, not data information.
\end{proof}

\begin{proposition}[Transverse reopening \tier{K}]
\label{prop:reopen}
The vorticity sector suppressed by radial-velocity contractions
($n^a n^b \omega_{ab} = 0$) can reopen in transverse-velocity and
spin-2 observables, whose response tensors are not proportional to
the radial dyad.
\end{proposition}
\begin{proof}
The radial null is an algebraic property of contracting an
antisymmetric tensor with a symmetric dyad; transverse and spin-2
response tensors carry independent screen directions that need not
annihilate the antisymmetric sector, so the nullspace of the radial
design is not a theorem for the enlarged observable set.
\end{proof}

\begin{proposition}[Kinematic deprojection \tier{K}]
\label{prop:deproj}
The corrected shear reading
$\widetilde\Sigma^2 = \Sigma^2 - \alpha\,\OmT^2$ with the registered
boost coefficient $\alpha$ removes the observer-boost $\beta^2$
quadrupole exactly at the registered order: on synthetic states it is
boost-invariant by construction and reduces to $\Sigma^2$ when
$\OmT = 0$ (no over-subtraction).
\end{proposition}
\begin{proof}
The observer boost generates a kinematic quadrupole at order
$\beta^2$ whose coefficient in the registered harmonic convention is
$\alpha$; subtracting $\alpha\OmT^2$ cancels it identically as an
algebraic statement about the two expansions, verified symbolically
and on the sealed synthetic estimator battery.
\end{proof}

\begin{proposition}[Depth memory \tier{K}]
\label{prop:volterra}
For $dY/dz + \lambda(z) Y = S(z)$,
\begin{equation}
Y(z) = Y(z_0)\,e^{-\int_{z_0}^{z}\lambda}
 + \int_{z_0}^{z} e^{-\int_{s}^{z}\lambda}\, S(s)\, ds,
\end{equation}
which is why every depth-binned diagnostic must record its bins,
reference policy, and source/damping assumptions.
\end{proposition}
\begin{proof}
Integrating-factor identity; the memory kernel makes any depth
contrast dependent on the full source history between bins.
\end{proof}

\subsection{Partial identification and coverage}

\begin{proposition}[Interval coverage at the least favorable point
\tier{K}]
\label{prop:im}
For a partially identified scalar with estimated bounds
$[\hat\theta_l, \hat\theta_u]$ and bound standard errors, the
Imbens--Manski construction \cite{ImbensManski2004} gives confidence
intervals whose coverage of the true point is controlled uniformly,
with the binding case at the identified-set boundary. On a
pre-registered grid of data-generating processes ranging from point to
weak to non-identification, simultaneous (family-wise) coverage is
certified by Bonferroni-corrected per-point exact binomial bounds at
the least-favorable boundary points, with mesh-refinement stability
required before any uniformity language is used.
\end{proposition}
\begin{proof}
The IM interval widens the naive union of one-sided intervals by the
factor solving $\Phi(C + \Delta/\hat\sigma) - \Phi(-C) = 1-\alpha$,
which is exactly the least-favorable-endpoint condition. Family-wise
validity over a finite grid follows from the union bound; exactness
of the per-point statement is Clopper--Pearson. Mesh refinement bounds
the grid-conditional gap.
\end{proof}

\subsection{Dependence-aware validation and model comparison}

\begin{proposition}[Group-level predictive scoring \tier{K}]
\label{prop:elpd}
If rows share latent group effects, the exchangeable unit is the group;
row-level leave-one-out scoring is optimistic because retained group
mates leak the latent effect. The correct held-out score is the joint
log predictive density of entire held-out groups
\cite{VehtariGelmanGabry2017}, with importance-sampling approximations
accepted only under a Pareto-$k$ diagnostic threshold.
\end{proposition}
\begin{proof}
With a shared intercept $b_g$, the posterior given the retained rows of
group $g$ concentrates on $b_g$, so the predictive for a held-out row
of the same group is conditionally, not marginally, calibrated;
the joint group density integrates over $b_g$ exactly once. In the
programme's conjugate test system the leakage is demonstrated
analytically and numerically (${\sim}0.18$ nats per observation) and
the importance-sampling route is verified against exact refits.
\end{proof}

\begin{proposition}[Evidence with normalized priors, two engines
\tier{K}]
\label{prop:evid}
For the conjugate Gaussian system $y_i \sim \mathcal N(\mu,\sigma^2)$,
$\mu \sim \mathcal N(0,\tau^2)$, the marginal likelihood is exactly
$\mathcal N(y; 0, \sigma^2 I + \tau^2 J)$, and both thermodynamic
integration and bridge sampling converge to it; an evidence claim is
accepted only when two engines with independent samples agree within
tolerance and a prior-sensitivity ceiling holds.
\end{proposition}
\begin{proof}
The exact form follows by completing the square in $\mu$. The
thermodynamic identity $\log Z = \int_0^1 \mathbb E_\beta[\log L]\,
d\beta$ follows by differentiating $\log Z_\beta$; the
Meng--Wong bridge identity is an importance-sampling equality valid
for any bridge function with overlapping support. Agreement of two
independent stochastic engines with the closed form to the stated
tolerance is recorded in the sealed artifacts.
\end{proof}

\begin{proposition}[Abstention-gated source discrimination \tier{P}]
\label{prop:mix}
Let a pre-registered model list contain isotropic, local-boost,
survey-systematic, and global-anisotropy alternatives with exact
conjugate evidences. A discrimination candidate is admissible only if
(i) one non-null model is decisively favored after a look-elsewhere
margin, (ii) the favored direction is identified (evidence-gap
governed, including against a combined superposition model),
(iii) posterior predictive adequacy holds, (iv) held-out gain over the
null is positive, and (v) the result is not prior sensitive; otherwise
the output is a mandatory abstention with its reason. On the
registered synthetic battery this protocol recovers each planted
source, abstains on the confusable pairs, and its measured false-candidate
rate under the null is below the design level.
\end{proposition}
\begin{proof}
Admissibility gates (i)--(v) are each computable from the registered
models. Correctness of the abstention logic is established
constructively on labelled syntheses: for collinear local/systematic
templates the evidence gap cannot exceed the design margin (their
likelihoods differ only through the near-degenerate template
difference), so gate (ii) forces abstention; for superpositions the
combined model's evidence exceeds the best single model by the
positive gap of the omitted component, again forcing abstention; for
the null the measured size over seeds bounds the false-candidate
rate. The battery and its referee scoring are sealed as artifacts.
\end{proof}

\subsection{Calibration of the diagnostic measures \tier{P}}

The scalar diagnostics $F$ (weighted RMS magnitude), $\Pi$ (weighted
signed contrast), and set-valued $G_F$ over the departure table are
pairwise non-interchangeable; each carries its own matched null
($\Pi$ against a two-sided sign-flip null; $F$ against a
reference-scale null whose noise scale must validate against the data's
robust scale, with degenerate nulls refused). None is a posterior, an
evidence, or a truth certificate. Proofs are by exhibiting the
distinct functional forms and by the sealed calibration runs in which
mis-matched nulls provably invert conclusions and are therefore
refused at the interface.
"""


def s4_geometry() -> str:
    return r"""
\section{Geometry-side theorems with proofs}
\label{sec:geom}

\subsection{One-way FLRW comparison \tier{K}/\tier{P}}

\begin{theorem}[Premise-complete forward direction]
\label{thm:egs}
For comparator states satisfying the complete registered FLRW premise
set (exact isotropy of the radiation field for every fundamental
observer of an irrotational geodesic congruence, with the exact
Ehlers--Geren--Sachs closure \cite{EGS1968}), $x_C = 0$ exactly.
\end{theorem}
\begin{proof}
Under the premise set each component of $\bm g$ vanishes individually:
the shear and vorticity by the EGS rigidity of the congruence, the
tilt by frame alignment, and the curvature comparator by isotropy of
the spatial geometry. The signed sum of zeros is zero. Incomplete
premise sets are refused with a refuting witness rather than
evaluated.
\end{proof}

\begin{proposition}[The converse fails \tier{P}]
\label{prop:noconverse}
$x_C = 0$ never implies FLRW: there exist registered counterexample
states with $\Sigma^2 = W^2 > 0$, $\OmT = \dOk = 0$ (and a
64-draw cancellation family) for which $x_C = 0$ while the geometry is
anisotropic.
\end{proposition}
\begin{proof}
By construction: the comparator is a single linear functional, so its
kernel intersects the positive cone of anisotropic states in a
codimension-one family; explicit rational witnesses are sealed. This
is why $x_C$ is a departure \emph{diagnostic}, not an isotropy
certificate.
\end{proof}

\subsection{MES bound hierarchy: primary-source reduction \tier{C}/\tier{P}}
\label{sec:mes}

\begin{theorem}[Geodesic reduction of the raw bounds]
\label{thm:mes}
The raw shear and vorticity bounds of Maartens--Ellis--Stoeger
\cite{MES1995} (their Eqs.~51/52), reduced under their own closure
conditions for a geodesic observer congruence with the dipole
attributed to observer motion ($\epsilon_1 = 0$, the
Stoeger--Araujo--Gebbie convention \cite{SAG1997}), give
\begin{equation}
\frac{\sigma}{H}: (5/3,\, 3,\, 3/7), \qquad
\frac{\omega}{H}: (10/3,\, 2/15,\, 0), \qquad
\dot u : \text{absent},
\end{equation}
as multipole coefficient triples on $(\epsilon_1, \epsilon_2,
\epsilon_3)$, yielding the exact ceilings
$W^2_{\max} = $ @W2_GEO@ and $\Sigma^2_{\max} = $ @S2_MAX@ at the
registered $\epsilon$ values.
\end{theorem}
\begin{proof}
Starting from the archived primary-source inequalities, the closure
conditions eliminate the acceleration terms identically for geodesic
observers ($A^2 = 0$), and the remaining reduction is exact rational
algebra executed independently in two computer-algebra engines with
bit-identical results; the $\omega$ triple reproduces the
Stoeger-co-authored follow-up paper's geodesic values, which is the
non-circular external check. The ceiling numbers follow by direct
substitution of the registered $\epsilon_i$.
\end{proof}

\begin{proposition}[Admissibility of the $\epsilon_1 = 0$ branch]
There is a critical dipole share $\epsilon_1^{\rm crit} =
\tfrac{43}{25}\epsilon_2 + \tfrac{9}{35}\epsilon_3 \approx 7.7\times
10^{-6}$ below which the hierarchy ordering $B_\sigma > B_\omega$ is
preserved; the observed solar dipole exceeds it, so the full-dipole
geodesic ceiling is excluded and the $\epsilon_1 = 0$ attribution
(dipole from observer boost) is the admissible reading, not a
uniqueness statement.
\end{proposition}
\begin{proof}
Setting $B_\sigma(\epsilon) = B_\omega(\epsilon)$ and solving the
linear relation in $\epsilon_1$ gives the stated critical value; the
$\omega$ triple's larger $\epsilon_1$ coefficient ($10/3$ versus
$5/3$) makes $B_\omega$ overtake $B_\sigma$ above it. Since the
hierarchy permits any $\epsilon_1 \in [0, \epsilon_1^{\rm crit})$,
admissibility, not uniqueness, is the correct conclusion.
\end{proof}

Three vorticity-ceiling branches are registered side by side and
propagated through every consumer:
geodesic/SAG-consistent $W^2_{\max} = $ @W2_GEO@ (live),
the frozen legacy value @W2_REG@ (print-only provenance,
retained for continuity), and the literature-envelope hybrid
@W2_HYB@. The second paper of the MES series is accessible only in
print; the registered non-geodesic coefficients appear in no
accessible source and exceed the companion paper's own faithful cap,
which is recorded as a documented discrepancy \tier{C} rather than
resolved.

\subsection{Rotating congruences and the curvature sector
\tier{K}/\tier{P}}

\begin{theorem}[Contracted Gauss identity with rotation]
\label{thm:ke}
For a unit timelike congruence $u^a$ with vorticity, the spatial
curvature scalar of the orthogonal metric satisfies
\begin{equation}
{}^3R = 2 G_{ab}u^a u^b - \tfrac{2}{3}\Theta^2 + \sigma^2 + \omega^2
\end{equation}
in the integrable limits, derived by undetermined coefficients over
five congruence configurations including two rotating ones.
\end{theorem}
\begin{proof}
The ansatz ${}^3R = \alpha G_{uu} + \beta\Theta^2 + \gamma\sigma^2 +
\delta\omega^2$ is fixed by evaluating both sides on configurations
where each invariant is independently switched on; the resulting
linear system has the unique stated solution, and the identity reduces
to the standard 3-curvature Gauss equation when $\omega = 0$.
\end{proof}

\begin{theorem}[Double obstruction at $\dOk = 0$ \tier{P}]
\label{thm:dok}
Within the group-invariant perfect-fluid class on flat spatial
geometry: (i) a single tilted stream is irrotational at the relevant
order because $G_{ti} \equiv 0$ for every homogeneous type-I metric in
the class; (ii) an antipodal tilt pair, which cancels the momentum
flux, dynamically conserves the tilt-covector direction (Killing plus
Euler), so its vorticity vanishes along the entire development. The
lower-endpoint vorticity withdrawal is therefore dynamical, not merely
constraint-level.
\end{theorem}
\begin{proof}
(i) is a symbolic computation over the class metric. (ii): the Euler
equation for a perfect fluid on a homogeneous background transports
the tilt covector along the flow; contracting with the Killing fields
shows the direction is conserved, and the vorticity bilinear built
from a direction-conserved covector with the class's structure
constants vanishes identically (verified to $10^{-12}$ on random
states and exactly on the invariant manifold). A genuine rotating
development with $\dOk > 0$ (type V, seven-dimensional first-principles
system, constraints monitored below $1.6\times10^{-10}$) shows the
obstruction is specific to the flat sector.
\end{proof}

\subsection{Curvature--shear slaving with certified remainder \tier{P}}
\label{sec:omk}

\begin{theorem}[Exact slaving coefficient]
\label{thm:slaving}
In the locally rotationally symmetric Bianchi~III / Kantowski--Sachs
reduced system with the exact constraint $1 = \Omega + \Sigma^2 + K$,
the transient-decayed mode satisfies $\Sigma = \kappa K$ with
\begin{equation}
\kappa = -\frac{1}{2+q}
\end{equation}
exactly ($q$ the deceleration parameter): dust $-2/5$, radiation
$-1/3$. To second order about FLRW,
$\Sigma = \kappa(w) K + c_2(w) K^2$ with
\begin{equation}
\kappa(w) = \frac{-2}{5+3w}, \qquad
c_2(w) = \frac{-2\,(9w^2 + 18w + 13)}{(3w+5)^2 (9w+7)},
\end{equation}
and the singular set of the expansion is the exact resonance family
$w_n = -(2n+3)/(6n-3)$ together with the marginal values $-1/3$ and
$1$.
\end{theorem}
\begin{proof}
The reduced evolution is
$d\Sigma/dN = -K - \tfrac{\Sigma}{2}[(1+3w)K + 3(1-w)(1-\Sigma^2)]$,
$dK/dN = 2K(q+\Sigma)$, with curvature source coefficient exactly
$-1$. Substituting the slaving ansatz and matching orders gives the
invariance equation whose linear solution is $\kappa = -1/(2+q)$;
the second-order coefficient follows by the same matching at
$O(K^2)$. Two independent derivation paths (invariance equation and
metric-level Einstein reduction) give the same exact rationals, and
finite-difference plateaus on both curvature branches confirm the
coefficients numerically. The resonance family is where the
order-$n$ matching operator loses invertibility, computed by exact
monotone inversion of its determinant condition.
\end{proof}

\begin{theorem}[Certified remainder tube]
\label{thm:remainder}
On the compact domain $|K| \le 1/10$, $w \in [0, 1/2]$, both curvature
branches, the truncation obeys the forward-invariant enclosure
\begin{equation}
\bigl|\Sigma - (\kappa K + c_2 K^2)\bigr| \le |K|^3 ,
\end{equation}
proven uniformly (not sampled).
\end{theorem}
\begin{proof}
The tube is forward invariant iff the flow points inward on its
boundary. The four boundary inward-flow conditions are polynomial
inequalities with positive denominator $2(3w+5)^6(9w+7)^3$; after
factoring the $K$-powers they are certified by exact-rational interval
branch-and-bound over the domain, corroborated by direct
high-precision integration on both branches. Consequently the finite
ceilings on $|\dOk|$ in Table~\ref{tab:omk} follow from the shear
ceilings by $|\dOk| \le \sqrt{\Sigma^2_{\rm ceiling}}/|\kappa|$.
\end{proof}

\begin{table}[ht]
\centering\small
\begin{tabular}{lcc}
\toprule
attribution $\times$ era & $|\kappa|$ & $|\dOk|$ ceiling \\
\midrule
@OMK_ROWS@ \\
\bottomrule
\end{tabular}
\caption{Slaving-derived anisotropic-curvature ceilings per
attribution branch and era (class-conditional; comparison rows use the
external model-conditional shear limit of \cite{Saadeh2016}).}
\label{tab:omk}
\end{table}

\subsection{Structural zeros and parity identities}

\begin{theorem}[Odd-$L$ diagonal BiPoSH zero \tier{K}]
\label{thm:oddl}
For any harmonic coefficients $a_{\ell m}$ (no reality or isotropy
assumption), the diagonal bipolar coefficients satisfy
$A^{LM}_{\ell\ell} = 0$ for every odd $L$.
\end{theorem}
\begin{proof}
The exchange symmetry of the Clebsch--Gordan coupling gives
$A^{LM}_{\ell_1\ell_2} = (-1)^{\ell_1+\ell_2-L}
A^{LM}_{\ell_2\ell_1}$; setting $\ell_1 = \ell_2 = \ell$ yields
$A^{LM}_{\ell\ell} = (-1)^{L} A^{LM}_{\ell\ell}$ (the $2\ell$ drops as
even), which forces the odd-$L$ coefficients to vanish. This is a
known property \cite{BookKamionkowskiSouradeep2012}, re-proven here by
an independent symbolic Wigner-3j oracle and verified on
reality-violating coefficient sets; the measured odd/even power ratio
on the observed masked map is @EVENL_ODDZERO@
(Section~\ref{sec:k1}). Its role here is trials accounting: odd $L$
carries no search dimensions.
\end{proof}

\begin{proposition}[Parity identities and the handedness ratio
\tier{K}; exploratory tier]
\label{prop:parity}
For the anisotropic-model polarization hierarchy of
\cite{PontzenChallinor2007}: (i) the $m=0$ sector admits a parity
involution under which mirror-fixed configurations have exactly zero
$B$-mode; (ii) the reflection $\mathrm{diag}(1,1,-1)$ flips the sign
of the $TB$ and $EB$ cross-spectra; (iii) consequently the ratio
$EB/TB$ is parity-\emph{even} and cannot encode spatial handedness;
any handedness test must use signed components against a registered
signed template. All four underlying identities are verified exactly
by four independent computer-algebra engines under a sealed contract.
\end{proposition}
\begin{proof}
(i) and (ii) are representation-theoretic: under the reflection the
$E$ multipoles are even and the $B$ multipoles odd, so the cross-spectra
$TB$ and $EB$ acquire one sign flip each. For (iii), the ratio of two
quantities that each flip sign is invariant, hence blind to the
mirror class; a signed single spectrum against a registered
orientation template retains the sign information. The identities are
exact statements about the hierarchy's algebra, independent of any
solver, and are held at the exploratory tier (not for observational
claims) pending native-transfer availability.
\end{proof}

\subsection{Exact curvature verification across all Bianchi types
\tier{K}/\tier{C}; exploratory tier}

\begin{theorem}[Eleven-type Ricci-scalar identity]
\label{thm:ricci}
For the canonical rational representatives of all eleven Bianchi
types (I, II, III, IV, V, VI$_0$, VI$_h$, VII$_0$, VII$_h$, VIII, IX),
the spatial Ricci scalar computed by the exact Koszul frame chain
$\Gamma^c{}_{ab} = \tfrac12(C^c{}_{ab} - C_a{}^{b}{}_{c} +
C_b{}^{c}{}_{a})$ (structure-constant lowering implied) equals the
Ellis--MacCallum anchor
\begin{equation}
R^\ast = -\tfrac12\textstyle\sum_i n_i^2 + (n_1 n_2 + n_2 n_3 +
n_3 n_1) - 6a^2
\end{equation}
identically in exact rational arithmetic, with textbook sanity values
(round $S^3$: $3/2$; unit $H^3$: $-6$) reproduced
\cite{EllisMacCallum1969}.
\end{theorem}
\begin{proof}
For each representative the structure constants
$C^a{}_{bc} = \epsilon_{bcd}n^{da} + a_b\delta^a_c - a_c\delta^a_b$
are assembled from the canonical $(n_i, a)$ data, the Koszul formula
gives the frame connection, and the frame Riemann tensor contraction
gives $R^\ast$; all steps are exact rational algebra, so equality with
the anchor is checked as an identity, not numerically. An independent
second-kind-coordinate engine (Maurer--Cartan coframe by matrix
exponentials, metric derivatives by complex-step differentiation)
agrees with maximal absolute gap @RICCI_MAXGAP@ across the eleven
representatives, and the derived class-B constraint $a_b n^{ba} = 0$
and the Jacobi identity are verified for every representative. Held
at the exploratory tier as native-solver support mathematics.
\end{proof}

\subsection{Auxiliary exact results}

\begin{proposition}[Premise-complete axisymmetric $B$-projector zero
\tier{K}]
For the axisymmetric configuration whose only source is the $m=0$
shear quadrupole and whose parity-odd tower vanishes identically, the
$B$-mode projector output is exactly zero; configurations violating
the premise (a nonzero parity-odd input component) produce a nonzero
output confined to the corresponding $m$ channel.
\end{proposition}
\begin{proof}
Selection rules: an axisymmetric parity-even source couples only to
$m = 0$ parity-even multipoles, which the $B$ projector annihilates;
a premise-violating $B_{2,\pm2}$ input lies in the projector's range
and appears only in its own $m$ channel. Both directions are verified
bit-exactly on the registered fixtures.
\end{proof}

\begin{proposition}[Unsigned comparator leakage bound \tier{K}]
For component magnitudes bounded by $B$, the maximum spurious unsigned
comparator value is $M_{\max}(B) = 4B$, attained at the all-endpoint
configuration; the bound is algebraic only and licenses no physical
promotion.
\end{proposition}
\begin{proof}
$|x_C| \le \sum_i |c_i|\, |g_i| \le 4B$ with equality iff each
$|g_i| = B$ with signs matched to $c$; the certificate is exact
arithmetic on the linear functional.
\end{proof}

\begin{proposition}[Reciprocal coefficient bracket \tier{K}]
For the registered $\ell = 2$ relation $a_2 = \kappa\Sigma(1+\delta)$
with $|\delta| \le R < 1$ and $\kappa$ pinned first, the correct
inversion brackets the shear \emph{reciprocally},
\begin{equation}
\frac{a_2}{\kappa(1+R)} \;\le\; \Sigma \;\le\; \frac{a_2}{\kappa(1-R)},
\end{equation}
and the non-reciprocal bracket $a_2\kappa^{-1}(1 \mp R)$ is strictly
weaker (by the factor $(1-R^2)^{-1}$ per side).
\end{proposition}
\begin{proof}
Divide the defining relation by $\kappa(1+\delta)$ and bound the
denominator monotonically; the weaker form follows by expanding the
reciprocal and dropping the quadratic term, which is exactly the
historical mislabelled variant, superseded with its consumers
invalidated.
\end{proof}

\begin{proposition}[Tail convergence versus statistical sufficiency
\tier{K}]
For the registered toy response $r_\ell = (2/\ell)^p$ the multipole
series converges exactly when $p > 1$ (harmonic divergence at
$p = 1$), and at $p = 3/2$ the tail obeys the strict two-sided
bracket $8/(L{+}1) + 2/(L{+}1)^2 < T(L) < 8/L + 2/L^2$, positive at
every finite $L$; convergence of the response series never implies
statistical sufficiency of a truncated multipole set, which requires
a registered factorization certificate that the toy family cannot
supply.
\end{proposition}
\begin{proof}
Comparison with the $p$-series gives the convergence domain; the
bracket follows from integral bounds on the zeta-tail with the
quadratic correction, certified by exact rational partial sums plus a
remainder enclosure and corroborated by high-precision evaluation.
The sufficiency clause is definitional: sufficiency is a property of
the likelihood factorization, not of numerical convergence, so the
gate fails closed without the certificate.
\end{proof}

\begin{proposition}[Sachs--Wolfe-only transport closed form \tier{K};
exploratory tier]
On a prescribed Bianchi~I kinematic background, the photon momentum
along a ray obeys the conserved-momentum closed form
$p_i(\eta) = p_i(\eta_0)\, a_i(\eta_0)/a_i(\eta)$ per principal axis,
and the induced linear-order temperature quadrupole equals the shear
integral oracle. A batched log-time fourth-order integrator reproduces
the closed form to $1.6\times10^{-11}$ with measured convergence order
$3.99$ and the quadrupole to the $O(\beta^2)$ residual floor.
\end{proposition}
\begin{proof}
In Bianchi~I each spatial direction carries a conserved comoving
momentum because the metric is diagonal with independent scale
factors; the closed form follows by direct integration of the
geodesic equation. The quadrupole oracle is the standard linear
Sachs--Wolfe shear integral. The numerical statements are measured
properties of the sealed run, quoted as verification, not as new
mathematics.
\end{proof}
"""


def s5_data() -> str:
    return r"""
\section{Current-data analyses}
\label{sec:data}

Every result in this section is conditional on its stated pipeline,
mask, convention, and null ensemble. Where a lane's numerical
instantiation is withheld pending an independent-validation condition,
the lane is described and the condition stated; no withheld number is
quoted.

\subsection{Planck low-multipole statistics (K1 lane)}
\label{sec:k1}

\paragraph{Convention contract \tier{K}.}
A canonical low-multipole convention (frame, harmonic indexing and
phase, processing resolution, common mask, orientation grid) is frozen
and content-addressed, and verified on the released SMICA and
Commander maps by a genuine map-space versus harmonic-space rotation
cross-check (two independent pipelines agree to $5\times10^{-4}$;
a deliberately wrong-phase variant breaks the check by three orders of
magnitude and is caught).

\paragraph{Look-elsewhere global rank \tier{C}/\tier{P}.}
Six pre-registered low-multipole statistics (axis alignment to the
solar dipole direction, parity asymmetry, even/odd power ratio,
planarity, quadrupole--octopole alignment, angular-correlation
$S_{1/2}$) are evaluated on the masked, processed SMICA map and on 999
end-to-end FFP10 CMB realizations paired with noise realizations
processed through the byte-identical pipeline. By
Corollary~\ref{cor:pool} the pooled max-scan global rank is
\begin{equation}
p_{\rm global} = @K1_GLOBAL_P@ ,
\end{equation}
with noise-reuse sensitivity range [@K1_SENS_LO@, @K1_SENS_HI@] and
resolution floor @K1_FLOOR@. Per-statistic local ranks:

\begin{center}\small
\begin{tabular}{lc}
\toprule statistic & local p \\ \midrule
@K1_LOCAL_ROWS@ \\ \bottomrule
\end{tabular}
\end{center}

This is consistent with the known 2--3$\sigma$ character of the
large-angle features \cite{Planck2018VII, Schwarz2016}: individually
interesting local ranks (angular correlation, quadrupole--octopole
alignment) survive pooling at the few-percent level and no statistic
promotes to a detection. The result is conditional on the
SMICA-processed FFP10 ensemble; a second-pipeline (Commander-processed)
replication is a registered pending analysis
(Section~\ref{sec:pending}). Figure: \code{fig\_v10\_k1\_rank\_hist}.

\paragraph{Even-$L$ diagonal BiPoSH ranks (new in v10) \tier{C}.}
Using Theorem~\ref{thm:oddl} to quotient odd $L$ out of the trials
space, the rotationally invariant diagonal powers
$S_{\ell,L} = \sum_M |A^{LM}_{\ell\ell}|^2$ for $L \in \{2,4\}$,
$\ell = 2..10$ (log-transformed for covariance conditioning) are
ranked under the same end-to-end null by an eigenvalue-floored,
Hartlap-corrected \cite{Hartlap2007} leave-one-out Mahalanobis score:
pooled $p = $ @EVENL_P@ ($L=2$: @EVENL_L2_P@, $L=4$: @EVENL_L4_P@) ---
consistent with the null. The measured odd/even structural-zero ratio
on the observed map is @EVENL_ODDZERO@, certifying the implementation
at float precision. Figure: \code{fig\_v10\_k1\_evenl\_rank}.

\paragraph{Boost-sector residual \tier{P}.}
The FFP10 CMB simulations include Doppler boosting
\cite{Planck2018III}, so the end-to-end null is a \emph{boosted} null.
The dipole-frame $(\ell,\ell+1)$ coupling vector
$F_\ell = \sum_m \mathrm{Re}(a^*_{\ell m}a_{\ell+1,m})/(2\ell+1)$,
$\ell = 2..10$, of the observed map is scored against this null after
identical subtraction of a fixed zero-parameter template obtained from
the exact pixel-space boost operator (consistent line-of-sight
aberration and thermodynamic Doppler pairing; band-limited synthesis
at aberrated directions; two-point Richardson extrapolation at
amplified boost, linearity gate value @BOOST_LIN@). The observed
Mahalanobis score @BOOST_SCORE@ ranks
\begin{equation}
p = @BOOST_P@
\end{equation}
inside the boosted null: within this pipeline, the low-multipole
dipole-coupling sector of the observed sky shows no residual beyond
the boost the simulations already carry. The known high-multipole
boost detection \cite{Planck2013XXVII} measures the boost amplitude;
this statistic instead asks the complementary zero-parameter residual
question at low multipoles. It never confirms a pure boost and makes
no independence claim. Figure: \code{fig\_v10\_boost\_biposh\_features}.

\paragraph{Off-diagonal isotropy measurement \tier{C}.}
The earlier off-diagonal BipoSH statistical-isotropy measurement on
SMICA and Commander (global $p = 0.68$ and $0.65$) remains the
programme's direct SI cross-check, consistent with the Planck isotropy
papers.

\subsection{Cosmicflows-4 peculiar-velocity lane (K5)}
\label{sec:cf4}

\paragraph{Catalogue authentication \tier{C}.}
Every group column of the published catalogue \cite{Tully2023} is
byte-authenticated against the released tables (38\,053 groups, full
column typing, completeness cross-checks); reconstruction columns are
typed as reconstructions, never as true flows.

\paragraph{Flow estimation with full covariance \tier{C}/\tier{P}.}
From the raw observable ($v = V_{3k} - H_0 D$, CMB frame) the
registered estimator with the always-fit radial monopole gives a flow
amplitude of @CF4_AMP@~km/s (monopole @CF4_MONO@~km/s) whose full
covariance includes the estimator-matched linear cosmic variance
(velocity correlation tensor of \cite{Gorski1988} under an
Eisenstein--Hu spectrum). Cosmic variance dominates: the honest
full-covariance amplitude significance is @CF4_FULLCOV_SIG@$\sigma$,
versus a noise-only formal @CF4_NOISE_SIG@$\sigma$ --- the deflation,
not the formal number, is the scientific content, and it parallels the
simulation-based uncertainty-underestimation finding of
\cite{Whitford2023} while being derived analytically. Injection tests
cover at nominal rates with the full covariance and under-cover
severely without it. The published minimum-variance amplitude
\cite{Watkins2023} is reproduced by the programme's implementation of
that estimator at the few-percent level with apex agreement to
$8.5^\circ$ at the inner depth; its amplitude significance is
withheld here in favour of the full-covariance treatment.

\paragraph{Identified sets per depth \tier{P}.}
Under a frozen nuisance box (distance-scale calibration, choice of
reconstruction observable, nonlinear dispersion) the flow is reported
as an identified set per pre-registered depth shell
(Theorem~\ref{thm:idset}; monopole always fit so radial calibration
cannot alias into the flow):

\begin{center}\small
\begin{tabular}{lcc}
\toprule shell (Mpc) & amplitude interval (km/s) & apex cone (deg) \\
\midrule
@CF4_SHELL_ROWS@ \\ \bottomrule
\end{tabular}
\end{center}

Every shell is bounded; the widening with depth is the honest
identification statement. A set containing a given value is never a
point estimate, and no tension statement is made from these sets.
No published peculiar-velocity analysis known to us reports
nuisance-robust identified sets (Section~\ref{sec:tiers});
figure \code{fig\_v10\_cf4\_depth}.

\paragraph{Depth-resolved growth \tier{C}.}
The safeguarded whitened amplitude fit per shell gives
$f\sigma_8 = $ @FS8_NEAR@ $\pm$ @FS8_NEAR_SIG@ in the nearest shell
(consistent with the fiducial @FS8_FID@ and with the published CF4
pairwise values $0.36$--$0.38$ \cite{Courtois2023}); only
@FS8_NCON@ of three shells is constrained under the mock-calibrated
classification, so no growth-difference-with-depth statement is
identified. The field-level maximum-likelihood growth lane agrees with
the published CF4-range values; its calibrated precision is pending an
independent covariance validation and its numeric headline is
therefore not quoted here.

\paragraph{Forward-mock stressors \tier{K}/\tier{C}.}
A full-covariance Cholesky forward simulator (with an independent
FFT-based reference generator confirming the variance normalization)
measures coverage degradation under four genuine stressors (lognormal
distance errors, nonlinear scatter, magnitude-limited selection with
unmodeled Malmquist bias, unmodeled intra-group dispersion); the
degraded coverages are reported, not hidden, and calibrate how far
idealized error bars can be trusted.

\paragraph{Reconstruction-method dependence (design lane).}
Comparing reconstruction treatments on identical catalogue support is
retained as a systematics design axis (method definition sealed); its
numerical instantiation is withheld pending the independent-validation
condition above.

\paragraph{Potential-flow check \tier{C}.}
On the real three-dimensional reconstructed field the Wiener-filtered
curl-to-divergence ratio is $0.009$, confirming the linear-theory
potential-flow expectation on the data.

\paragraph{Directional cosmography on the raw catalogue
\tier{C}/\tier{P}.}
A reconstruction-independent directional estimand on the raw
catalogue, with pre-registered falsifier gates, splits into an
$H$-block (log-distance dipole) and a $q$-block (curvature of the
directional relation). The cubic-falsifier canonical correlation
between the $q$-block and the selection response is
@Q_CC_LO@--@Q_CC_HI@ $> 0.95$ in every fold, so \emph{all} $q$-level
results are withheld. The $H$-block passes identifiability in all
folds and its exact rank under the matched exchangeable null is
@H_RANK_FRAC@ (scaled estimate @H_RANK_EST@, guard interval
[@H_GUARD_LO@, @H_GUARD_HI@]) --- \emph{conditional on unresolved
selection systematics}, and therefore not a detection. This
conditionality independently lands on the same interpretation as the
recent forward-modelling reanalysis of claimed local $H_0$ anisotropy
\cite{NoH0Anisotropy2025}, which attributes such signals to
selection and velocity systematics; the claimed 3.9$\sigma$
zeropoint-dipole signal \cite{Boubel2025} and its refutation frame
the live external controversy this lane is designed to adjudicate
once the survey-mock stages complete.
Figure: \code{fig\_v10\_pr179\_conditional}.

\paragraph{Divergence cross-falsifier \tier{K}.}
The registered divergence/$q$ cross-falsifier lane terminated
non-informative (the $q$ response is unavailable under the falsifier),
with its separate frozen-covariance self-consistency axis failing its
coverage target (0.9424 against 0.95, Wilson interval excluding the
target) --- recorded as an honest method-validation failure; no
significance result exists in that lane.

\subsection{DESI DR1 galaxy-count dipole (external lane)}

The window-corrected BGS number-count dipole is
$D = $ @DESI_D@ (raw footprint dipole suppressed by a factor
${\sim}224$ by the random-catalogue window correction), direction
$122^\circ$ from the CMB dipole. Against in-house $\Lambda$CDM
clustering mocks passed through the identical estimator the observed
amplitude is clustering-consistent ($p = $ @DESI_P15@ at bias 1.5,
robust across bias 1.2--2.0) \tier{C}: at BGS depths the count dipole
is clustering-dominated and the kinematic component is sub-dominant.
An exact-selection mock machinery (drawing from the real per-cap
random density, refitting the dipole and a nuisance amplitude per
mock) is sealed \tier{P}; the survey-conditional pooled-rank
consistency holds (observed amplitude in the bulk of the conditional
null), while \emph{causal attribution is deferred} to the official
validation-mock ensemble per Section~\ref{sec:completeness}.
Figure: \code{fig\_v10\_desi\_dipole}.

\subsection{ACT DR6 lensing convergence (external lane)}

On the released DR6 convergence map \cite{Madhavacheril2024, Qu2024}
with its 400-simulation ensemble: the low-$L$ ($2..10$)
mean-field-debiased band statistic is consistent with the isotropic
simulation null ($p = $ @ACT_P@) and yields a 95\% upper limit on
excess band power of @ACT_UL@ (@ACT_UL_RATIO@ of the simulation
median) \tier{C}; the strict-in-band ($41 \le L \le 762$) modulation
rank is @ACT_INBAND_RANK@, unresolved from the null at current
Monte-Carlo resolution \tier{C}. The raw-quadratic-estimator inputs
(filtered CMB maps and pipeline) are not part of the public release,
so a from-scratch re-estimation is recorded as unavailable rather
than approximated \tier{C}; the release-simulation leave-one-out
cross-fit mean field at low $L$ (with its exact $((n{-}1)/n)^2$
scaling disclosed) is the principled construction used \tier{P}.
Figure: \code{fig\_v10\_act\_kappa}.

\subsection{JWST distance anchors (forecast lane) \tier{C}}

A row-complete manifest of the 17 cited JWST distance anchors
(CCHP and SH0ES programmes) with per-anchor provenance is
probabilistically cross-matched to CF4 groups (Budav\'ari--Szalay
likelihood against a local no-match background): 10 of 17 anchors are
positionally credible, 2 marginal, 2 ambiguous --- positional
credibility is never a confirmed identity (no redshifts in the seed
table). The hierarchical covariance forecast over the anchor set
returns \emph{total uncertainty not identified} for both calibration
families and no material CF4-conditioned information gain across
2\,430 scenario cells: an honest non-identification certificate for
the anchor-set size and structure, verified by simulation-based
calibration and posterior predictive checks.

\subsection{Assembled comparator region (new in v10) \tier{P}}

Combining the CF4 identified $\OmT$ intervals
(Eq.~\ref{eq:omtilt} applied to the shell intervals above), the MES
vorticity branches (Section~\ref{sec:mes}), the MES shear ceiling,
and the slaving-derived $|\dOk|$ ceilings (Table~\ref{tab:omk}),
Theorem~\ref{thm:t1p} yields the current identified interval for
$x_C$ per attribution branch --- the first assembled
identified-region rendering of the full four-component comparator
under measured-plus-ceiling inputs. All branches contain zero, as
they must while two components are ceiling-only: the figure displays
how far current data plus exact ceilings actually constrain the
departure functional, which is the honest current answer to ``what is
measured so far.''
Figure: \code{fig\_v10\_comparator\_region}.

\subsection{Synthetic calibration of the discrimination method
\tier{K}}

The blind synthetic battery over seven labelled data-generating
processes (null, local, global, systematic, weak identification,
dependent mocks, covariance misspecification) certifies the
discrimination protocol of Proposition~\ref{prop:mix}: ready on six
families with measured null false-candidate rate $0.0067 \le 0.1$,
and \emph{blocked} on covariance misspecification --- a genuine
diagnostic limitation recorded as such. Synthetic readiness never
implies observed-data validity; it is the precondition for the
pending analyses below.

\section{Figures}
\label{sec:figures}

\begin{figure}[p]\centering
\includegraphics[width=\textwidth]{fig_v10_comparator_region.png}
\caption{Assembled identified region for $\bm g$ and the induced
$x_C$ intervals per attribution branch (Section~\ref{sec:data}).}
\end{figure}
\begin{figure}[p]\centering
\includegraphics[width=\textwidth]{fig_v10_k1_rank_hist.png}
\caption{K1 per-statistic and pooled max-scan null distributions with
observed values (Section~\ref{sec:k1}).}
\end{figure}
\begin{figure}[p]\centering
\includegraphics[width=0.72\textwidth]{fig_v10_k1_evenl_rank.png}
\caption{Even-$L$ diagonal BiPoSH pooled rank under the end-to-end
null (new in v10).}
\end{figure}
\begin{figure}[p]\centering
\includegraphics[width=\textwidth]{fig_v10_boost_biposh_features.png}
\caption{Boost-BiPoSH feature vector against the boosted null band and
the zero-parameter operator template.}
\end{figure}
\begin{figure}[p]\centering
\includegraphics[width=\textwidth]{fig_v10_cf4_depth.png}
\caption{CF4 identified sets per depth shell and depth-resolved
growth.}
\end{figure}
\begin{figure}[p]\centering
\includegraphics[width=0.8\textwidth]{fig_v10_desi_dipole.png}
\caption{DESI DR1 BGS window-corrected dipole against clustering-mock
nulls.}
\end{figure}
\begin{figure}[p]\centering
\includegraphics[width=0.8\textwidth]{fig_v10_act_kappa.png}
\caption{ACT DR6 low-$L$ debiased convergence band powers, upper
limit, and in-band modulation rank.}
\end{figure}
\begin{figure}[p]\centering
\includegraphics[width=\textwidth]{fig_v10_pr179_conditional.png}
\caption{Raw-catalogue directional cosmography: falsifier-based
$q$-withholding and the conditional $H$-only rank.}
\end{figure}
\begin{figure}[p]\centering
\includegraphics[width=0.8\textwidth]{fig_v10_omk_slaving.png}
\caption{Slaving coefficients $\kappa(w)$, $c_2(w)$ and the exact
resonance family (Section~\ref{sec:omk}).}
\end{figure}
\begin{figure}[p]\centering
\includegraphics[width=\textwidth]{fig_v10_ricci_gaps.png}
\caption{Eleven-type Ricci-scalar identity: independent-engine
verification gaps (Theorem~\ref{thm:ricci}).}
\end{figure}
\clearpage
"""


def s6_tiers() -> str:
    tiers = _load("docs/audits/v10_web_crag_20260721/tier_evidence.json")
    rows = []
    for e in tiers["entries"]:
        subj = (
            e["subject"]
            .replace("_", r"\_")
            .replace("&", r"\&")
            .replace("%", r"\%")
            .replace("^", r"\^{}")
            .replace("Omega_tilt", r"$\OmT$")
        )
        basis = (
            e["basis"]
            .replace("_", r"\_")
            .replace("&", r"\&")
            .replace("%", r"\%")
            .replace("^", r"\^{}")
        )
        rows.append(
            f"\\code{{{e['id']}}} & {e['tier']} & {subj} & {basis} \\\\"
        )
    table = "\n".join(rows)
    return r"""
\section{Claim and novelty tier ledger}
\label{sec:tiers}

Every claim in this report carries one of four novelty tiers,
adjudicated against an external-literature cross-check performed at
build time (evidence ledger:
\code{docs/audits/v10\_web\_crag\_20260721/}):

\begin{description}
\item[\tier{K} known] the fact or method is standard or published;
  our contribution is an independent re-derivation or an
  implementation-grade verification.
\item[\tier{C} cross-check] our measured number or result
  cross-checks a published external number (agreement or registered
  disagreement), or documents a verifiable external-release property.
\item[\tier{P} potential advance] the analysis or theorem is
  plausibly beyond the published literature (evidence: a documented
  search finding no published equivalent), but is not promotable to a
  significant claim today because of an explicit stated condition.
\item[\tier{S} significant claimable] a result whose validation
  status permits asserting a novel significant scientific result now.
\end{description}

\textbf{No entry carries \tier{S} in this version.} Each
\tier{S}-candidate is held by a stated scientific condition: the
directional-cosmography rank by its open selection-systematics
channel and the pending survey-mock validation stages
(Section~\ref{sec:completeness}); the low-multipole global rank by
its single-pipeline conditionality pending a second-pipeline
replication; and the exact-theory results, which are complete as
mathematics, by the fact that the programme asserts no observational
consequence from them without the native-transfer stage. This
accounting is itself part of the record: the tier ledger states
exactly what would promote each candidate.

\begin{center}\scriptsize
\begin{longtable}{p{2.4cm} p{0.8cm} p{6.2cm} p{5.2cm}}
\toprule id & tier & claim & basis \\ \midrule
""" + table + r"""
\bottomrule
\end{longtable}
\end{center}
"""


def s7_pending() -> str:
    return r"""
\section{Registered analyses conditional on data completion}
\label{sec:pending}

The following analyses are fully specified and will run without
design changes when their stated data condition is met; none has been
started on partial data.

\begin{enumerate}
\item \textbf{DESI official-mock causal attribution.} When the
complete official validation-mock ensemble (1000 EZmock +
@DESI_ABACUS_TARGET@ AbacusSummit) is on disk and authenticated, the
exact-selection dipole machinery runs the pre-registered
clustering/kinematic/selection attribution with per-mock refits and
the survey-conditional null at full resolution. Condition: transfer
completion (@DESI_EZ_AUTH@/@DESI_EZ_TARGET@ EZmock at the build
probe; days-scale remaining).
\item \textbf{Cross-survey negative controls and joint covariance}
for the directional-cosmography lane, followed by held-out injection
discrimination; the $H$-only conditional rank of
Section~\ref{sec:cf4} either survives with its selection channel
closed or is retired. Condition: item 1.
\item \textbf{Second-pipeline low-multipole replication.} The
Commander-processed FFP10 end-to-end ensemble would replicate
Section~\ref{sec:k1} under an independent component-separation
pipeline. Condition: acquisition of the Commander-processed MC set
(bandwidth-bounded).
\item \textbf{Independent non-author adjudication} of the
peculiar-velocity estimator-level findings whose numerical lanes are
withheld above; the withheld instantiations either return with
validated uncertainties or stay retired. Condition: completion of the
independent validation review.
\item \textbf{Native anisotropic-transfer stage.} All
family-identification, geometry, and handedness tests (including the
signed-component template of Proposition~\ref{prop:parity}) remain
dormant until the native solver line delivers authenticated
transfer functions; no diagnostic in this report substitutes for
that stage.
\end{enumerate}
"""


def s8_repro() -> str:
    art_rows = "\n".join(
        f"\\code{{{a.replace('_', chr(92) + '_')}}} \\\\"
        for a in REQUIRED_ARTIFACTS
    )
    return r"""
\section{Reproducibility}
\label{sec:repro}

The package is generated by
\code{scripts/build\_external\_audit\_report\_v10.py} (byte-stable
\code{--check} mode; the PDF is compiled from the shipped TeX). The
data figures are generated by
\code{scripts/v10\_report\_data\_figures.py} from sealed result cards
only, and the new even-$L$ analysis by
\code{scripts/k1\_evenl\_biposh\_rank\_card.py} against the
content-addressed compact map cache. Input artifacts (hashes in
\code{MANIFEST.json}):

\begin{center}\scriptsize
\begin{tabular}{l}
\toprule
""" + art_rows + r"""
\bottomrule
\end{tabular}
\end{center}

External-literature verification for the tier ledger was performed by
inline web retrieval on 2026-07-21 (interactive research agents were
unavailable at build time; the retrieval record is preserved in the
evidence ledger).

\begin{thebibliography}{99}\footnotesize
\bibitem{EllisVanElst1999} G.~F.~R. Ellis and H. van Elst,
``Cosmological models,'' NATO ASI C 541, 1 (1999).
\bibitem{EGS1968} J. Ehlers, P. Geren, and R.~K. Sachs,
J. Math. Phys. 9, 1344 (1968).
\bibitem{EllisMacCallum1969} G.~F.~R. Ellis and M.~A.~H. MacCallum,
Comm. Math. Phys. 12, 108 (1969).
\bibitem{KingEllis1973} A.~R. King and G.~F.~R. Ellis,
Comm. Math. Phys. 31, 209 (1973).
\bibitem{CollinsEllis1979} C.~B. Collins and G.~F.~R. Ellis,
Phys. Rep. 56, 65 (1979).
\bibitem{HewittWainwright1992} C.~G. Hewitt and J. Wainwright,
Phys. Rev. D 46, 4242 (1992).
\bibitem{MES1995} R. Maartens, G.~F.~R. Ellis, and W.~R. Stoeger,
Phys. Rev. D 51, 1525 (1995).
\bibitem{SAG1997} W.~R. Stoeger, M. Araujo, and T. Gebbie,
Astrophys. J. 476, 435 (1997).
\bibitem{PontzenChallinor2007} A. Pontzen and A. Challinor,
MNRAS 380, 1387 (2007).
\bibitem{BookKamionkowskiSouradeep2012} L.~G. Book, M. Kamionkowski,
and T. Souradeep, Phys. Rev. D 85, 023010 (2012).
\bibitem{Planck2013XXVII} Planck Collaboration XXVII,
A\&A 571, A27 (2014).
\bibitem{Planck2018III} Planck Collaboration III,
A\&A 641, A3 (2020).
\bibitem{Planck2018VII} Planck Collaboration VII,
A\&A 641, A7 (2020).
\bibitem{Schwarz2016} D.~J. Schwarz, C.~J. Copi, D. Huterer, and
G.~D. Starkman, Class. Quantum Grav. 33, 184001 (2016).
\bibitem{Saadeh2016} D. Saadeh et al.,
Phys. Rev. Lett. 117, 131302 (2016).
\bibitem{Tully2023} R.~B. Tully et al., Astrophys. J. 944, 94 (2023).
\bibitem{Watkins2023} R. Watkins et al., MNRAS 524, 1885 (2023).
\bibitem{Whitford2023} A.~M. Whitford, C. Howlett, and T.~M. Davis,
MNRAS 526, 3051 (2023).
\bibitem{Courtois2023} H.~M. Courtois et al., A\&A 670, L15 (2023).
\bibitem{Gorski1988} K. Gorski, Astrophys. J. 332, L7 (1988).
\bibitem{Hartlap2007} J. Hartlap, P. Simon, and P. Schneider,
A\&A 464, 399 (2007).
\bibitem{ImbensManski2004} G.~W. Imbens and C.~F. Manski,
Econometrica 72, 1845 (2004).
\bibitem{PhipsonSmyth2010} B. Phipson and G.~K. Smyth,
Stat. Appl. Genet. Mol. Biol. 9, 39 (2010).
\bibitem{VehtariGelmanGabry2017} A. Vehtari, A. Gelman, and J. Gabry,
Stat. Comput. 27, 1413 (2017).
\bibitem{Madhavacheril2024} M.~S. Madhavacheril et al.,
Astrophys. J. 962, 113 (2024).
\bibitem{Qu2024} F.~J. Qu et al., Astrophys. J. 962, 112 (2024).
\bibitem{Boubel2025} P. Boubel et al., MNRAS (2025),
CF4 Tully--Fisher zeropoint-dipole analysis.
\bibitem{NoH0Anisotropy2025} ``No evidence for local $H_0$ anisotropy
from Tully--Fisher or supernova distances,'' MNRAS 546, staf2048
(2025), arXiv:2509.14997.
\end{thebibliography}

\end{document}
"""


def build_tex() -> str:
    v = _values()
    body = (
        PREAMBLE
        + s1_scope()
        + s2_conventions()
        + s3_stats()
        + s4_geometry()
        + s5_data()
        + s6_tiers()
        + s7_pending()
        + s8_repro()
    )
    body = body.replace("@DESI_PROBE_DATE@", DESI_PROBE_DATE)
    body = body.replace("@DESI_EZ_AUTH@", str(DESI_EZ_AUTH))
    body = body.replace("@DESI_EZ_TARGET@", str(DESI_EZ_TARGET))
    body = body.replace("@DESI_ABACUS_TARGET@", str(DESI_ABACUS_TARGET))
    for key, val in v.items():
        body = body.replace(f"@{key}@", val)
    leftovers = [tok for tok in body.split("@")[1::2]
                 if tok.isupper() and "_" in tok]
    if leftovers:
        raise SystemExit(f"unsubstituted tokens: {sorted(set(leftovers))}")
    return body


def build_readme() -> str:
    return (
        "# External research report v10 (2026-07-21)\n\n"
        "Self-contained scientific record: exact theorems with proofs, "
        "statistical architecture, current-data results with figures, a "
        "K/C/P/S novelty-tier ledger, and the data-completeness "
        "statement (DESI official-mock acquisition in progress: "
        f"{DESI_EZ_AUTH}/{DESI_EZ_TARGET} EZmock authenticated at the "
        f"{DESI_PROBE_DATE} probe; partial mocks never enter any "
        "statistic).\n\n"
        "Reproduce: `venv/bin/python scripts/build_external_audit_report_"
        "v10.py --write` (pdflatex required). Verify text artifacts: "
        "`--check` (byte-stable; PDF/zip excluded because pdflatex embeds "
        "timestamps).\n\n"
        "Earlier packages v5-v9 are byte-frozen and superseded by this "
        "version as the current record.\n"
    )


def build_citation() -> str:
    return (
        "cff-version: 1.2.0\n"
        "message: research report artifact (v10)\n"
        "title: Tetrad-Based FLRW-Departure Diagnostics in Bianchi "
        "Cosmologies - Research Report v10\n"
        "authors:\n  - name: BASS/HTT research programme\n"
        "date-released: '2026-07-21'\n"
        "version: v10\n"
    )


def build_manifest(tex: str) -> str:
    inputs = {}
    for rel in REQUIRED_ARTIFACTS:
        inputs[rel] = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    figs = {}
    for stem in FIGURES:
        p = FIG_SRC / f"{stem}.png"
        figs[f"{stem}.png"] = hashlib.sha256(p.read_bytes()).hexdigest()
    payload = {
        "schema": "htt.external_audit_report.v10.manifest",
        "version": "v10",
        "date": "2026-07-21",
        "tex_sha256": hashlib.sha256(tex.encode()).hexdigest(),
        "input_artifact_sha256": inputs,
        "figure_sha256": figs,
        "desi_completeness": {
            "probe_date": DESI_PROBE_DATE,
            "ezmock_authenticated": DESI_EZ_AUTH,
            "ezmock_target": DESI_EZ_TARGET,
            "abacus_target": DESI_ABACUS_TARGET,
            "partial_mocks_in_statistics": False,
        },
        "pdf_excluded_from_check": "pdflatex embeds timestamps",
    }
    return json.dumps(payload, sort_keys=True, indent=1) + "\n"


def text_artifacts() -> dict[str, str]:
    tex = build_tex()
    return {
        TEX_NAME: tex,
        "README.md": build_readme(),
        "CITATION.cff": build_citation(),
        "MANIFEST.json": build_manifest(tex),
    }


def do_write() -> int:
    OUT.mkdir(exist_ok=True)
    figdest = OUT / FIG_DEST_NAME
    figdest.mkdir(exist_ok=True)
    for stem in FIGURES:
        shutil.copy2(FIG_SRC / f"{stem}.png", figdest / f"{stem}.png")
    for name, content in text_artifacts().items():
        (OUT / name).write_text(content)
    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
           TEX_NAME]
    for _ in range(3):
        proc = subprocess.run(cmd, cwd=OUT, capture_output=True, text=True)
        if proc.returncode != 0:
            tail = proc.stdout[-3000:]
            print(tail)
            return 1
    zip_path = ROOT / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(OUT.rglob("*")):
            if p.is_file() and p.suffix not in {".aux", ".log", ".out",
                                                ".toc"}:
                zf.write(p, p.relative_to(OUT.parent))
    shutil.copy2(OUT / PDF_NAME, ROOT / PDF_NAME)
    print(f"wrote {OUT.name}/ + {PDF_NAME} + {ZIP_NAME}")
    return 0


def do_check() -> int:
    ok = True
    for name, content in text_artifacts().items():
        disk = OUT / name
        if not disk.exists() or disk.read_text() != content:
            ok = False
            print(f"artifact differs under --check: {name}")
    for stem in FIGURES:
        src = FIG_SRC / f"{stem}.png"
        dst = OUT / FIG_DEST_NAME / f"{stem}.png"
        if not dst.exists() or src.read_bytes() != dst.read_bytes():
            ok = False
            print(f"figure differs: {stem}")
    print(json.dumps({"mode": "check", "ok": ok}, sort_keys=True))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    return do_write() if args.write else do_check()


if __name__ == "__main__":
    sys.exit(main())
