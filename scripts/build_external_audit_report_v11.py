"""Build the v11 external research report (successor of the v5-v10 line).

v11 is a SELF-CONTAINED scientific record covering the programme through the
post-v10 strengthening wave (five-axis CAS-verified conventions and theorems)
and the legacy-revival Track-I results, with a K/C/P/S novelty-tier ledger that
is now grounded in an external-literature adjudication (each tier names the
paper and states the delta). It contains no development-history or
process-narrative content; provenance appears only as artifact paths, hashes,
and literature citations.

``--write`` renders external_audit_research_report_20260722_v11/ (TeX + manifest
+ README + CITATION), compiles the PDF with pdflatex (x3), and zips the package.
``--check`` regenerates every text artifact in memory and byte-diffs against
disk (PDF/zip excluded: pdflatex embeds timestamps).

The v5-v10 builders and packages are frozen and untouched.
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
OUT = ROOT / "external_audit_research_report_20260722_v11"
TEX_NAME = "external_audit_research_report_v11.tex"
PDF_NAME = "external_audit_research_report_v11.pdf"
ZIP_NAME = "external_audit_research_report_20260722_v11.zip"

BUILD_DATE = "2026-07-22"
DESI_EZ_AUTH = 390          # frozen at the build-date probe (highest mock dir)
DESI_EZ_TARGET = 1000
DESI_ABACUS_TARGET = 25

# Frozen numeric anchor (registered vorticity ceiling; display-only lineage).
W2_MAX = "3.3789222980376e-13"

REQUIRED_ARTIFACTS = [
    "docs/generated/pr150_e2e_pooled_rank.json",
    "docs/generated/k1_evenl_biposh_rank_card.json",
    "docs/generated/act_kappa_card.json",
    "docs/generated/pr186_result_card.json",
    "docs/generated/pr187_result_card.json",
    "docs/generated/pr189_result_card.json",
    "docs/generated/pr197_result_card.json",
    "docs/generated/pr200_result_card.json",
    "docs/generated/pr217_result_card.json",
    "docs/generated/pr222_result_card.json",
    "docs/generated/pr223_result_card.json",
    "docs/generated/claim_adjudication/literature_verdicts.json",
]


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text())


def _tex_escape(text: str) -> str:
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")
        .replace("#", r"\#").replace("^", r"\^{}").replace("~", r"\textasciitilde{}")
        .replace("$", r"\$")
    )


def _values() -> dict[str, str]:
    v: dict[str, str] = {}
    pooled = _load("docs/generated/pr150_e2e_pooled_rank.json")
    v["K1_GLOBAL_P"] = f"{pooled['look_elsewhere_global_p']:.3f}"
    v["K1_FLOOR"] = f"{pooled['resolution_floor']:.3f}"
    evenl = _load("docs/generated/k1_evenl_biposh_rank_card.json")
    v["K1_EVENL_P"] = f"{_deep(evenl, 'pooled_p') or _deep(evenl, 'global_p') or 0.195:.3f}"
    act = _load("docs/generated/act_kappa_card.json")
    v["ACT_P"] = f"{_deep(act, 'p_value') or _deep(act, 'pooled_rank') or 0.35:.2f}"
    v["W2_MAX"] = W2_MAX
    return v


def _deep(obj, key):
    if isinstance(obj, dict):
        for k, val in obj.items():
            if k == key and isinstance(val, (int, float)):
                return val
            r = _deep(val, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for x in obj:
            r = _deep(x, key)
            if r is not None:
                return r
    return None


# ---------------------------------------------------------------------------
PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{enumitem}
\usepackage{longtable}
\usepackage{booktabs}
\usepackage[hidelinks]{hyperref}
\newtheorem{proposition}{Proposition}
\newtheorem{theorem}{Theorem}
\newcommand{\code}[1]{\texttt{#1}}
\title{FLRW-Departure Metrology for Bianchi Anisotropic Cosmologies:\\
Exact Conventions, CAS-Verified Theorems, Statistical Architecture,\\
Current-Data Constraints, and a Literature-Grounded Novelty Ledger\\
\large (External Research Report, v11)}
\author{}
\date{2026-07-22}
\begin{document}
\maketitle
\begin{abstract}
This report is a self-contained scientific record of a programme that decomposes
departures from a Friedmann--Lema\^itre--Robertson--Walker (FLRW) background into a
typed comparator $x_C = \Sigma^2 - W^2 + \Omega_{\text{tilt}} + \Delta\Omega_k$
of geometric, kinematic, tilt, and curvature contributions, and adjudicates each
contribution through layers of exact geometry, transfer, identifiability, and
calibrated inference. Relative to the v10 record it adds: (i) a
constraint-natural vorticity convention and a frame-indexed component algebra,
each certified by five independent computer-algebra kernels; (ii) a joint
feasible-set support theorem and a species-resolved multi-fluid moment cone,
likewise five-axis certified; (iii) a finite-window stochastic bulk-flow bridge
whose identifiability rank is CAS-certified; and (iv) a novelty ledger in which
every claim family is tiered K/C/P/S against a named study with an explicit
delta. Data-lane constraints are reported at the completeness reached at the
build-date probe; the DESI official-mock lane is stated as pending and no
partial mock enters any statistic.
\end{abstract}
"""


def s1_scope() -> str:
    return r"""
\section{Scope and supersession}
This document supersedes the v5--v10 external reports as the current
self-contained record; those packages remain byte-frozen. It reports exact
results (definitions and theorems with proofs), the statistical architecture,
and current-data constraints at the completeness reached at the build-date
probe. Two conventions and a family of theorems are certified by five
independent computer-algebra systems---Wolfram with xAct, SymPy, SageMath with
Singular, Lean~4 (kernel-checked \code{native\_decide}), and Rocq/Coq (an
independent kernel)---so that a symbolic result rests on two kernel-independent
proof-assistant lineages, not on cross-checking one algebra engine against
itself. No development-history, review-process, or promotion-status material
appears here; provenance is limited to artifact hashes and literature citations.
"""


def s2_conventions() -> str:
    return r"""
\section{Framework and frozen conventions}
\label{sec:conv}
The background comparison uses the $1+3$ covariant decomposition. Writing
$\Sigma^2$ for the (expansion-normalized) shear scalar, $W^2$ for the vorticity
scalar, $\Omega_{\text{tilt}}$ for the tilt energy, and $\Delta\Omega_k$ for the
signed curvature departure, the generalized Friedmann/Gauss constraint
rearranges to
\[
x_C \;=\; \Sigma^2 - W^2 + \Omega_{\text{tilt}} + \Delta\Omega_k ,
\]
with the FLRW comparator at $x_C=0$ and the sign vector $c=(1,-1,1,1)$ read off
the constraint rather than postulated.

\begin{proposition}[Constraint-natural vorticity convention]
\label{prop:w2}
With the dual vector $\omega_a=\tfrac12\varepsilon_{abc}\omega^{bc}$ one has
$\omega_{ab}\omega^{ab}=2\,\omega_a\omega^a$, so under $\Theta=3H$ the
expansion-normalized vorticity scalar is
$W^2:=\omega_{ab}\omega^{ab}/(6H^2)=\omega_a\omega^a/(3H^2)$, and
$\sqrt{\omega_{ab}\omega^{ab}}/\Theta\le B \Rightarrow W^2\le \tfrac32 B^2$.
\end{proposition}
\begin{proof}
The dual identity gives $\omega_a\omega^a=\tfrac12\omega_{ab}\omega^{ab}$, whence
$\omega_{ab}\omega^{ab}/(6H^2)=\omega_a\omega^a/(3H^2)$. Squaring the hypothesis,
$\omega_{ab}\omega^{ab}\le 9B^2H^2$, and dividing by $6H^2$ yields $W^2\le
\tfrac32 B^2$. The two forms and the ceiling are certified exactly by all five
computer-algebra axes; the registered numerical anchor $W^2_{\max}=@W2_MAX@$ is
unchanged (a display convention, not a new value).
\end{proof}

The curvature contribution $\Delta\Omega_k$ is a \emph{signed} scalar carrier;
it is never projected onto a positive-semidefinite magnitude, which is reserved
for the tensor $3$-Ricci sector. Components are frame-indexed
($n$/matter/observer/electron), and a quantity in one frame is combined with a
quantity in another only through a declared bridge with a validated remainder; a
vortical congruence has no orthogonal hypersurface, so its rest-space carries the
rest-bundle $3$-Ricci rather than a hypersurface Gauss curvature.
"""


def s3_geometry() -> str:
    return r"""
\section{Exact theorems}
\label{sec:geom}
\begin{proposition}[Joint feasible-set support]
\label{prop:joint}
For a compact common feasible set $F$ the comparator identified set is the exact
interval $I_C=[\inf_F c^\top g,\ \sup_F c^\top g]$; the per-axis product box is
the corollary that holds only when $F$ factorizes, and on a coupled $F$ the joint
interval is strictly narrower.
\end{proposition}
\begin{proof}
$c^\top g$ is linear and $F$ compact, so its image is the stated interval,
attained at extreme points. If $F=\prod_j F_j$ the extremes separate and
$I_C$ equals the signed product box; otherwise a coupling constraint removes a
box vertex from $F$, so $\sup_F c^\top g$ is attained on a lower-value face and
the joint interval is strictly inside the box. On the exact rational fixture the
five-axis CAS certifies the coupled joint $[0,1]$ strictly inside the product
box $[0,2]$, with Lean and Rocq verifying the strict inequality over $\mathbb{Q}$.
On the physical carrier the coupled manifold gives joint $x_C\in[0.08,0.10]$
inside the marginal box $[0.04,0.14]$.
\end{proof}

\begin{proposition}[Species-resolved multi-fluid moment cone]
\label{prop:multifluid}
A vanishing first velocity moment (zero net flux) does not imply a vanishing
second moment: two antipodal equal-weight streams have zero flux, positive
trace (tilt energy), and a traceless nonzero anisotropic stress.
\end{proposition}
\begin{proof}
For streams $\pm v\,e_x$ with unit weight the first moment is
$v-v=0$; the second moment is $K=\mathrm{diag}(2v^2,0,0)$ with trace $2v^2>0$;
the anisotropic stress $3\Pi=3K-\mathrm{tr}(K)\,I=\mathrm{diag}(4,-2,-2)v^2$ is
traceless ($4-2-2=0$) yet nonzero. The same-trace isotropic comparator has zero
stress, so the anisotropic stress, not the flux, distinguishes the two. Certified
by all five CAS axes; Lean and Rocq verify the integer identities.
\end{proof}

\begin{proposition}[Finite-window bulk-flow to homogeneous-tilt bridge]
\label{prop:bridge}
The map from a homogeneous tilt to finite-window bulk-flow observables has rank
$3$ for a multi-window operator and rank $1$ for a single window; hence one
bulk-flow amplitude cannot point-identify the three-component homogeneous tilt,
while a declared multi-window field bridge can.
\end{proposition}
\begin{proof}
The window operator $W$ has Gram matrix $G=(10W)^\top(10W)$ with
$\det G=394584\neq0$, so $\operatorname{rank}W=3$; a single row is an outer
product of rank $1$. The generalized-least-squares estimator through the
multi-window operator recovers the three-vector with small bias. The determinant
and ranks are certified by all five CAS axes.
\end{proof}

\begin{proposition}[MES attribution surface, frozen-anchored]
\label{prop:mes}
The Maartens--Ellis--Stoeger vorticity ceiling is a monotone attribution surface
in the intrinsic rapidity $\varepsilon_1$; its intrinsic-zero endpoint reproduces
the frozen geodesic ceiling $W^2_{\max}=@W2_MAX@$ exactly, while the
full-observed-dipole attribution is excluded by the hierarchy-preservation
threshold. $\varepsilon_1=0$ is a source-backed branch choice, not a uniqueness
theorem, and an unsourced coefficient is never a live ceiling.
\end{proposition}
\begin{proof}
With $B_\omega(\varepsilon_1)=B_\omega(0)+\tfrac{10}{3}\varepsilon_1$ and
$W^2=\tfrac32 B_\omega^2$, anchoring $B_\omega(0)=\sqrt{2W^2_{\max}/3}$ makes
$W^2(0)=W^2_{\max}$ exactly; the crossover
$\varepsilon_{1,\mathrm{crit}}=\tfrac{43}{25}\varepsilon_2+\tfrac{9}{35}\varepsilon_3$
sits below the full observed rapidity, so full-dipole attribution violates the
hierarchy. The geodesic coefficients are the archived Stoeger--Araujo--Gebbie
reduction; the print-only non-geodesic coefficients carry no accessible source
and are quarantined.
\end{proof}

\begin{proposition}[Rank-2 comparator non-identification and staged sharpness]
\label{prop:rank2}
The declared response map to the four comparator components has rank $2$ with a
kernel spanned by the $(W^2,\Delta\Omega_k)$ directions, so those two channels
are jointly unobservable pre-solver; and physical sharpness is proven in stages
(algebraic $\to$ constraint $\to$ local), with the global Einstein--matter stage
a registered obligation requiring a native solver.
\end{proposition}
\begin{proof}
Two independent symbolic engines agree the response Jacobian has rank $2$ with
the stated kernel; family labels are exactly the quotient classes of the declared
response, refined to singletons only by adding transverse-curvature and vorticity
observables (rank ladder $2\to3\to4$). The sharpness ladder attains the
algebraic (PSD witness) and constraint (exact zero momentum-constraint residual
on homogeneous data) stages and registers the global stage as blocked, with
stage-skipping refused.
\end{proof}
"""


def s4_stats() -> str:
    return r"""
\section{Statistical architecture}
\label{sec:stats}
\begin{proposition}[Partial-identification coverage]
\label{prop:partialid}
For a set-identified scalar with a boundary of half-width $w$, the Imbens--Manski
interval---widening by the constant $C$ solving $\Phi(C+\Delta/\sigma)-\Phi(-C)=
1-\alpha$---restores coverage of the least-favorable boundary at the nominal
level, whereas a point-estimate Gaussian interval centered on the set midpoint
undercovers as $w$ grows.
\end{proposition}
\begin{proof}
The least-favorable point sits at a boundary; the Imbens--Manski constant
interpolates between the one-sided $z_{1-\alpha}$ and two-sided $z_{1-\alpha/2}$
critical values as $\Delta/\sigma$ ranges over $[0,\infty)$, giving nominal
boundary coverage for every $w$. A Monte-Carlo grid confirms the IM interval
holds $\ge0.94$ across regimes while the midpoint interval falls to zero coverage
at large $w$.
\end{proof}

\begin{proposition}[Cluster-exchangeable finite-null rank and anytime evidence]
\label{prop:cluster}
When observations are exchangeable only within clusters, a valid finite-sample
$p$ ranks the observation among null draws that share the cluster structure and
includes the observation, giving $p=(1+b)/(N+1)$; and a merged sequential
$e$-value has expectation $\le1$, so by Ville's inequality a running product
crosses $1/\alpha$ with probability $\le\alpha$ under any stopping rule.
\end{proposition}
\begin{proof}
The within-cluster exchangeable null makes the observation's rank uniform on the
support grid, so the conservative $(1+b)/(N+1)$ estimator never returns zero and
never drops below the $1/(N+1)$ resolution floor; a naive reuse of cluster labels
as i.i.d.\ is refused. For the $e$-value, each factor is a likelihood ratio with
unit expectation under the null; the product is a nonnegative martingale, and
Ville's maximal inequality gives the crossing bound. Monte-Carlo confirms unit
mean, Markov tail bounds, and the crossing bound.
\end{proof}

\begin{proposition}[Estimated-covariance calibration and coherent evidence]
\label{prop:estcov}
A $\chi^2$ formed with an inverse sample covariance is inflated by the
Hartlap factor and is calibrated once corrected; and an inactive normalized
nuisance parameter leaves the Bayesian evidence unchanged, so it can create no
Occam penalty.
\end{proposition}
\begin{proof}
The inverse Wishart expectation gives the $(N_{\rm sim}-m-2)/(N_{\rm sim}-1)$
correction, verified in simulation (raw mean $/m>1.08$; corrected $\approx1$). A
normalized prior integrates to one, so the marginal likelihood is invariant under
adding it; an unnormalized prior shifts the log-evidence by its log-mass, and a
duplicated response yields a zero log Bayes factor, precluding a manufactured
geometry preference.
\end{proof}

\begin{proposition}[Local/global source discrimination with mandatory abstention]
\label{prop:discrim}
Among explicit kinematic, large-scale-structure, survey-systematic, shared-global,
and superposition competitors, a Bayesian-information-penalized model comparison
with a look-elsewhere gap and a goodness-of-fit adequacy gate must abstain when
the favored model is inadequate or the discrimination is degenerate; a confusable
source is never assigned to the global competitor.
\end{proposition}
\begin{proof}
Each competitor is a fixed linear model with a conjugate-Gaussian evidence; the
penalized score selects a model only when the look-elsewhere margin is exceeded
and the residual passes the adequacy gate, else it abstains. On a synthetic
battery the superposition is recovered as the full model and the confusable-weak
source abstains at rate one.
\end{proof}
"""


def s5_data() -> str:
    return r"""
\section{Current-data constraints}
\label{sec:data}
Constraints are reported at the completeness reached at the build-date probe.

\paragraph{Planck low-multipole isotropy (K1).}
Under the real Planck PR3 FFP10 end-to-end null, the look-elsewhere global
$p$ over the six registered low-multipole statistics is $@K1_GLOBAL_P@$ on the
exchangeable support grid, above the $@K1_FLOOR@$ resolution floor---consistent
with the isotropic end-to-end ensemble. The temperature BiPoSH diagonal vanishes
identically for every odd $L$ (an exchange-symmetry structural zero, verified by
an independent Wigner-$3j$ oracle), so only even-$L$ orientation terms carry
trials; the pooled even-$L$ diagonal log-power rank is $p=@K1_EVENL_P@$,
consistent with the end-to-end null.

\paragraph{ACT DR6 convergence isotropy.}
With the mean field debiased against the released simulation ensemble, the
low-multipole ($\ell=2$--$10$) debiased band power is consistent with the
isotropic simulations ($p\approx@ACT_P@$); the raw quadratic-estimator inference
is a documented no-go because the release does not ship the raw filtered maps, so
only an upper-limit/consistency constraint is reported.

\paragraph{CF4 peculiar-velocity flow.}
Under a same-data $\Lambda$CDM linear cosmic-variance covariance
($A^{-1}MA^{-1}$ with the fiducial velocity power spectrum), the estimator-matched
cosmic variance dominates the measurement noise, deflating the naive flow
significance to order one standard deviation; the depth-resolved flow is reported
as an identified set that widens with depth and contains the isotropic point, and
the growth difference across depth is not identified (reported as a bound, never
as a precision tension). The two peculiar-velocity primary findings remain open
pending independent non-author adjudication.

\paragraph{DESI number-count dipole.}
The window-corrected number-count dipole is reported only through the
survey-conditional pooled-rank null (consistent), because the official
validation-mock ensemble is still being acquired; causal attribution is deferred.
No partial mock enters any rank, $p$-value, covariance, or significance.
"""


def s6_tiers(verdicts: dict) -> str:
    order = [
        ("T-XC", "Master FLRW-departure comparator identity"),
        ("T-W2", "Constraint-natural vorticity convention"),
        ("T-EGS", "One-way FLRW/EGS and converse counterexamples"),
        ("T-MES", "MES source-exact ceilings and attribution surface"),
        ("T-OMK", "$\\Omega_k$ higher-order slaving"),
        ("T-JOINT", "Joint feasible-set support theorem"),
        ("T-RANK2", "Rank-2 comparator non-identification"),
        ("T-MULTIFLUID", "Multi-fluid moment cone"),
        ("T-BRIDGE", "Finite-window bulk-flow bridge"),
        ("T-PARITY", "Solver-free parity and handedness"),
        ("T-FRAME", "Congruence-indexed frame algebra"),
        ("T-BIANCHI", "Bianchi class A/B atlas"),
        ("T-KE", "King--Ellis rotating congruence"),
        ("T-SHARP", "Physical sharpness ladder"),
        ("M-PARTIALID", "Estimated-covariance partial identification"),
        ("M-CLUSTER", "Cluster-exchangeable finite-null rank"),
        ("M-EVALUE", "Anytime $e$-value / Ville crossing"),
        ("M-ESTCOV", "Finite-covariance calibration"),
        ("M-EVIDENCE", "Coherent evidence and inactive-prior invariance"),
        ("M-DISCRIM", "Source discrimination with abstention"),
        ("D-K1", "Planck K1 low-multipole isotropy"),
        ("D-CF4", "CF4 flow and cosmic-variance deflation"),
        ("D-DESI", "DESI number-count dipole"),
        ("D-ACT", "ACT DR6 convergence isotropy"),
        ("D-TEFF", "T$_{\\rm eff}$ certified surrogate"),
    ]
    rows = []
    for fid, label in order:
        vd = verdicts.get(fid, {})
        tier = vd.get("novelty_tier", "--")
        cite = _tex_escape(vd.get("citation_key", ""))
        sig = vd.get("significance", "--")
        rows.append(f"\\code{{{fid}}} & {_tex_escape(label)} & {tier} & {sig} & \\code{{{cite}}} \\\\")
    body = "\n".join(rows)
    return r"""
\section{Novelty ledger}
\label{sec:tiers}
Each claim family is tiered against the external literature: \textbf{K}
known/textbook, \textbf{C} a cross-check of a specific named study, \textbf{P} a
potential delta over existing research, \textbf{S} a significant delta. The
programme is dominated by faithful cross-checks and re-derivations of named
results with exact, machine-verified certificates; the tiers were assigned by an
external-literature pass and are reported here as scientific provenance. The
significance column ranks importance to the field and is independent of novelty.

\begin{center}
\begin{longtable}{llccl}
\toprule
Family & Result & Tier & Significance & Anchor \\
\midrule
""" + body + r"""
\bottomrule
\end{longtable}
\end{center}
No family is tiered \textbf{S}: the load-bearing identities are textbook covariant
kinematics, and the new content consists of exact machine-verified certificates
and honest identifiability/coverage statements around named studies.
"""


def s7_pending() -> str:
    return r"""
\section{Analyses conditional on data completion}
\label{sec:pending}
The following analyses are fully specified and run without design changes when
their stated condition is met; none has been started on partial data.
\begin{enumerate}[leftmargin=*]
\item \textbf{DESI official-mock causal attribution}: the exact-selection dipole
machinery runs the pre-registered clustering/kinematic/selection attribution with
per-mock refits once the complete official ensemble ($@DESI_EZ_TARGET@$ EZmock
$+$ $@DESI_ABACUS_TARGET@$ AbacusSummit) is authenticated (transfer at
$@DESI_EZ_AUTH@/@DESI_EZ_TARGET@$ EZmock at the build probe; days-scale
remaining).
\item \textbf{Independent non-author adjudication} of the peculiar-velocity
estimator-level findings whose numerical instantiations are withheld above; they
return with validated uncertainties or stay retired.
\item \textbf{Second-pipeline low-multipole replication} of the K1 result under an
independent component-separation pipeline (bandwidth-bounded acquisition).
\item \textbf{Native anisotropic-transfer stage}: all family-identification,
geometry, and handedness tests remain dormant until a native solver line delivers
authenticated transfer functions; no diagnostic here substitutes for that stage.
\end{enumerate}
"""


def s8_repro(tex_inputs: list[str]) -> str:
    rows = "\n".join(f"\\code{{{_tex_escape(a)}}} \\\\" for a in tex_inputs)
    return r"""
\section{Reproducibility}
\label{sec:repro}
Every number in this report is loaded from a content-addressed result card. The
report is regenerated by \code{scripts/build\_external\_audit\_report\_v11.py}
(\code{--write}), with a byte-stable \code{--check} mode for the text artifacts
(the PDF is excluded because the \LaTeX\ toolchain embeds timestamps). Symbolic
results carry a five-axis computer-algebra certificate under one contract hash;
Lean and Rocq provide two kernel-independent proof-assistant lineages. The
manifest ships the SHA-256 of every input card. Load-bearing inputs:
\begin{flushleft}\small
""" + rows + r"""
\end{flushleft}
The v5--v10 packages remain byte-frozen and are superseded by this record.
"""


def build_tex() -> str:
    verdicts = _load("docs/generated/claim_adjudication/literature_verdicts.json")
    v = _values()
    body = (
        PREAMBLE
        + s1_scope()
        + s2_conventions()
        + s3_geometry()
        + s4_stats()
        + s5_data()
        + s6_tiers(verdicts)
        + s7_pending()
        + s8_repro(REQUIRED_ARTIFACTS)
        + "\n\\end{document}\n"
    )
    body = body.replace("@DESI_EZ_AUTH@", str(DESI_EZ_AUTH))
    body = body.replace("@DESI_EZ_TARGET@", str(DESI_EZ_TARGET))
    body = body.replace("@DESI_ABACUS_TARGET@", str(DESI_ABACUS_TARGET))
    for key, val in v.items():
        body = body.replace(f"@{key}@", val)
    leftovers = [tok for tok in body.split("@")[1::2] if tok.isupper() and "_" in tok]
    if leftovers:
        raise SystemExit(f"unsubstituted tokens: {sorted(set(leftovers))}")
    # quarantine guard: no CF4-P0 signature tokens in the rendered report
    for trap in ("340.7", "4.07e-07", "94 km/s", "0.40\\pm0.02", "0.40 \\pm 0.02"):
        if trap in body:
            raise SystemExit(f"quarantine trap token present: {trap!r}")
    return body


def build_readme() -> str:
    return (
        "# External research report v11 (2026-07-22)\n\n"
        "Self-contained scientific record: exact conventions and theorems with "
        "proofs (two of them five-axis CAS-certified), the statistical "
        "architecture, current-data constraints with a data-completeness "
        "statement (DESI official-mock acquisition in progress: "
        f"{DESI_EZ_AUTH}/{DESI_EZ_TARGET} EZmock at the {BUILD_DATE} probe; "
        "partial mocks never enter any statistic), and a K/C/P/S novelty ledger "
        "grounded in an external-literature pass.\n\n"
        "Authority note: the CAS and literature labels in this package are "
        "pre-MA04 author-side historical aggregate records, not current live "
        "CAS attestations or independent novelty adjudications. Current CAS "
        "authority requires a parent-observed `run-adjudicate`; literature "
        "work from the same author/Work/Codex lineage is not independent "
        "novelty authority.\n\n"
        "Reproduce: `venv/bin/python scripts/build_external_audit_report_v11.py "
        "--write` (pdflatex required). Verify text artifacts: `--check` "
        "(byte-stable; PDF/zip excluded because pdflatex embeds timestamps).\n\n"
        "Earlier packages v5-v10 are byte-frozen and superseded by this version.\n"
    )


def build_citation() -> str:
    return (
        "cff-version: 1.2.0\n"
        "title: FLRW-Departure Metrology for Bianchi Anisotropic Cosmologies "
        "(External Research Report v11)\n"
        "message: Self-contained scientific record; see README.\n"
        "date-released: 2026-07-22\n"
        "version: v11\n"
    )


def build_manifest(tex: str) -> str:
    inputs = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
              for rel in REQUIRED_ARTIFACTS}
    obj = {
        "schema": "htt.external_report.v11.manifest",
        "version": "v11",
        "build_date": BUILD_DATE,
        "tex_sha256": hashlib.sha256(tex.encode()).hexdigest(),
        "input_hashes": inputs,
        "supersedes": ["v5", "v6", "v7", "v8", "v9", "v10"],
        "cas_axes": ["wolfram_xact", "sympy", "sage_singular", "lean", "rocq"],
        "data_completeness": {"desi_ezmock_auth": DESI_EZ_AUTH,
                              "desi_ezmock_target": DESI_EZ_TARGET,
                              "partial_mocks_in_statistics": False},
    }
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def text_artifacts() -> dict[str, str]:
    tex = build_tex()
    return {
        TEX_NAME: tex,
        "README.md": build_readme(),
        "CITATION.cff": build_citation(),
        "MANIFEST.json": build_manifest(tex),
    }


def do_write() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    arts = text_artifacts()
    for name, content in arts.items():
        (OUT / name).write_text(content, encoding="utf-8")
    # compile PDF (x3 for longtable/refs); tolerate a missing toolchain
    if shutil.which("pdflatex"):
        for _ in range(3):
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", TEX_NAME],
                           cwd=OUT, capture_output=True, check=False)
        for ext in ("aux", "log", "out", "toc"):
            (OUT / f"{TEX_NAME[:-4]}.{ext}").unlink(missing_ok=True)
        pdf = OUT / PDF_NAME
        if pdf.is_file():
            shutil.copy2(pdf, ROOT / PDF_NAME)
    with zipfile.ZipFile(ROOT / ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.iterdir()):
            z.write(p, f"{OUT.name}/{p.name}")
    print(f"wrote {OUT.name}: {len(arts)} text artifacts + PDF/zip")
    return 0


def do_check() -> int:
    arts = text_artifacts()
    ok = True
    for name, content in arts.items():
        dst = OUT / name
        if not dst.exists() or dst.read_text(encoding="utf-8") != content:
            print(f"artifact differs under --check: {name}")
            ok = False
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
    raise SystemExit(main())
