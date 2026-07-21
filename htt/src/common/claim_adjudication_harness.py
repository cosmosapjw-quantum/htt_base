"""Rolling claim-adjudication harness: unlock blocked gates / provenance.

Adjudicates every claim FAMILY of the HTT/BASS programme against the actual
external literature on four axes -- significance, novelty (K/C/P/S vs the named
paper), completeness, verification -- and classifies which blocked gate or
provenance can be UNLOCKED now versus what the real ceiling is. It is
incremental: it runs on the current committed cards + a literature-verdict input
(produced by the web-CRAG adjudication workflow), so promotion decisions do not
wait for every PR to finish.

Unlock semantics (what this harness can and cannot resolve):
  - PROVENANCE gates (a citation marked unverified/miscited) are resolvable by
    web-CRAG: a verified citation UNLOCKS provenance; a miscite stays blocked
    with a correction obligation.
  - NOVELTY tier (K/C/P/S) is resolvable by web-CRAG against the named paper.
  - SIGNIFICANCE informs the promotion ranking.
  - The INDEPENDENCE gate (a NON-AUTHOR principal re-deriving/reproducing) is a
    different, capacity-bound gate; this harness is author-side and NEVER
    fake-passes it. It only marks a claim "one non-author adjudication from
    VALIDATED" when all four axes pass author-side + literature-grounded.
  - DATA-acquisition (PR-151 DESI mocks) and NATIVE-SOLVER (Track II) blockers
    are hard and not literature-resolvable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
GEN = REPO / "docs/generated"

# blocker classes, ordered from most-resolvable to hardest
BLOCKER_INDEPENDENCE = "independence_only"       # author-side complete; needs non-author sign-off
BLOCKER_DATA = "data_acquisition_pr151"          # DESI official mocks still downloading
BLOCKER_NATIVE = "native_solver"                 # Track II; no native Boltzmann solver
BLOCKER_PROCESS = "process_only"                 # governance/state-machine; no literature axis

SIGNIFICANCE_ORDER = {"foundational": 3, "substantial": 2, "incremental": 1, "marginal": 0}
NOVELTY_ORDER = {"S": 3, "P": 2, "C": 1, "K": 0}

# Provenance flags that the adversarial-verify pass adjudicated: the underlying
# references.bib is correct; the value here is the auditable resolution.
PROVENANCE_OVERRIDES = {
    "T-EGS": "cited_correct: registry author string corrected Hsu->Lim "
             "(Nilsson, Uggla, Wainwright & Lim 1999, ApJL 522,L1); references.bib was already correct",
    "D-CF4": "cited_correct: adversarial verify confirmed references.bib Watkins2023 (MNRAS 524,1885) "
             "and Whitford2023 (arXiv:2306.11269); the lit-CRAG 'miscited' flag was a false positive",
}


@dataclass(frozen=True)
class Family:
    id: str
    title: str
    lane: str                 # theory / method / data / process
    pr_cards: tuple[str, ...]
    literature_anchor: str    # the named paper(s) the novelty is judged against
    structural_blocker: str
    note: str = ""


# The distinct scientific claim families of the programme (not one row per PR).
FAMILIES: tuple[Family, ...] = (
    # ---- theory ----
    Family("T-XC", "Master FLRW-departure identity x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k",
           "theory", ("PR-126", "PR-210", "PR-215"),
           "Ellis & van Elst 1999 (cosmological models, covariant 1+3); Maartens 1998",
           BLOCKER_INDEPENDENCE),
    Family("T-W2", "Constraint-natural vorticity convention W2 = omega_ab omega^ab/(6H^2)",
           "theory", ("PR-186", "PR-211"),
           "Ellis 1971 relativistic cosmology (covariant kinematics), textbook",
           BLOCKER_INDEPENDENCE),
    Family("T-MES", "MES source-exact shear/vorticity ceilings + attribution surface",
           "theory", ("PR-217",),
           "Maartens, Ellis & Stoeger 1995 PRD 51,1525; SAG 1997 astro-ph/9904346",
           BLOCKER_INDEPENDENCE),
    Family("T-EGS", "One-way FLRW/EGS + converse counterexample registry",
           "theory", ("PR-126",),
           "Clarkson & Barrett 1999 gr-qc/9906097; Nilsson-Uggla-Wainwright-Lim 1999 ApJL 522,L1 astro-ph/9904252",
           BLOCKER_INDEPENDENCE),
    Family("T-OMK", "Omega_k higher-order slaving Sigma = kappa K + c2 K^2",
           "theory", ("PR-131", "PR-132", "PR-192"),
           "Wainwright & Ellis 1997 dynamical systems in cosmology (LRS Bianchi)",
           BLOCKER_INDEPENDENCE),
    Family("T-JOINT", "Joint feasible-set support theorem (product box a corollary)",
           "theory", ("PR-189", "PR-215"),
           "Imbens & Manski 2004 Econometrica 72,1845 (identified sets)",
           BLOCKER_INDEPENDENCE),
    Family("T-RANK2", "Comparator rank-2 non-identification (W2/DeltaOmega_k joint null)",
           "theory", ("PR-127", "PR-219"),
           "PSTF/covariant moment problem; Ellis-MacCallum structure constants",
           BLOCKER_INDEPENDENCE),
    Family("T-MULTIFLUID", "Multi-fluid moment cone: zero flux does not imply zero stress",
           "theory", ("PR-223",),
           "relativistic kinetic theory (Israel-Stewart moment hierarchy)",
           BLOCKER_INDEPENDENCE),
    Family("T-BRIDGE", "Finite-window stochastic bulk-flow -> homogeneous-tilt rank bridge",
           "theory", ("PR-222",),
           "Kaiser 1988; minimum-variance bulk-flow estimator (Watkins-Feldman-Hudson)",
           BLOCKER_INDEPENDENCE),
    Family("T-PARITY", "Solver-free parity/handedness identities + reference registry",
           "theory", ("PR-182",),
           "Pontzen & Challinor 2007 MNRAS 380,1387 (Bianchi polarization)",
           BLOCKER_INDEPENDENCE),
    Family("T-FRAME", "Congruence-indexed frame algebra + signed carrier + Frobenius gate",
           "theory", ("PR-125", "PR-187", "PR-212"),
           "van Elst & Uggla 1997 (1+3 covariant frame formalism)",
           BLOCKER_INDEPENDENCE),
    Family("T-BIANCHI", "Bianchi class A/B structure-constant atlas",
           "theory", ("PR-214",),
           "Ellis & MacCallum 1969 CMP 12,108 (Bianchi classification)",
           BLOCKER_INDEPENDENCE),
    Family("T-KE", "King-Ellis rotating-congruence ten-item program",
           "theory", ("PR-181",),
           "King & Ellis 1973 CMP 31,209 (tilted cosmologies)",
           BLOCKER_INDEPENDENCE),
    Family("T-SHARP", "Physical sharpness ladder algebraic->constraint->local->global",
           "theory", ("PR-216",),
           "Einstein-constraint initial data (Choquet-Bruhat); endpoint attainability",
           BLOCKER_NATIVE, "global stage needs the native solver"),
    # ---- method ----
    Family("M-PARTIALID", "Estimated-cov partial-ID confidence set + continuum coverage",
           "method", ("PR-136", "PR-137", "PR-200", "PR-225"),
           "Imbens & Manski 2004; Stoye 2009 Econometrica 77,1299",
           BLOCKER_INDEPENDENCE),
    Family("M-CLUSTER", "Cluster-exchangeable finite-null rank",
           "method", ("PR-135", "PR-197"),
           "Phipson & Smyth 2010 SAGMB 9,39 (permutation p-values)",
           BLOCKER_INDEPENDENCE),
    Family("M-EVALUE", "Dependent-merge + anytime e-value / Ville crossing",
           "method", ("PR-225",),
           "Ramdas, Grunwald, Vovk & Shafer 2023 (game-theoretic statistics / e-values)",
           BLOCKER_INDEPENDENCE),
    Family("M-ESTCOV", "Finite-covariance Hartlap + Sellentin-Heavens t likelihood",
           "method", ("PR-142", "PR-225"),
           "Hartlap+ 2007 A&A 464,399; Sellentin & Heavens 2016 MNRAS 456,L132",
           BLOCKER_INDEPENDENCE),
    Family("M-EVIDENCE", "Coherent normalized evidence + inactive-prior invariance",
           "method", ("PR-129", "PR-140", "PR-220"),
           "MacKay 2003 (Occam factor); thermodynamic integration / bridge sampling",
           BLOCKER_INDEPENDENCE),
    Family("M-DISCRIM", "Contamination-aware local/global source discrimination + abstention",
           "method", ("PR-141", "PR-221"),
           "Bayesian model comparison; Secrest+ 2021 dipole competitors",
           BLOCKER_INDEPENDENCE),
    Family("M-DUALAXIS", "External-novelty x internal-readiness promotion state machine",
           "process", ("PR-185", "PR-213"),
           "n/a (governance state machine, no external-literature novelty axis)",
           BLOCKER_PROCESS),
    # ---- data ----
    Family("D-K1", "Planck K1 low-multipole BiPoSH structural zero + even-L rank",
           "data", ("PR-149", "PR-150"),
           "Pontzen & Challinor 2007; Planck 2018 VII isotropy",
           BLOCKER_INDEPENDENCE, "Planck PR3 on disk; author-side complete"),
    Family("D-CF4", "CF4 bulk flow + same-data LambdaCDM cosmic-variance deflation",
           "data", ("PR-145", "PR-146", "PR-147", "PR-148"),
           "Watkins+ 2023 MNRAS 524,1885; Whitford, Howlett & Davis 2023 arXiv:2306.11269",
           BLOCKER_INDEPENDENCE, "both CF4 P0s await PR-157 non-author adjudication"),
    Family("D-DESI", "DESI number-count dipole survey-conditional null",
           "data", ("PR-151", "PR-226"),
           "Secrest+ 2021 ApJL 908,L51; DESI DR1 (official EZmock/Abacus)",
           BLOCKER_DATA, "official-mock closure blocked on the PR-151 acquisition terminal"),
    Family("D-ACT", "ACT DR6 kappa low-ell isotropy upper limit",
           "data", ("PR-152", "PR-177"),
           "ACT DR6 lensing 2023 (Madhavacheril+ / Qu+)",
           BLOCKER_INDEPENDENCE, "raw-QE is a documented no-go; UL is author-side complete"),
    Family("D-TEFF", "Teff/BASS-lite certified surrogate contract",
           "data", ("PR-218",),
           "reduced-order surrogate modeling (generic); no native oracle available",
           BLOCKER_NATIVE, "surrogate authorizes no inference without a native solver"),
    # ---- provenance / legacy ----
    Family("P-LEGACY", "Legacy inventory hash-binding + mutation corpus + disposition",
           "process", ("PR-209", "PR-214", "PR-227"),
           "n/a (provenance mechanics; legacy archives are immutable fixtures)",
           BLOCKER_INDEPENDENCE),
    Family("II-NATIVE", "Native Bianchi Boltzmann solver observable-response claims",
           "theory", ("PR-229", "PR-230", "PR-231", "PR-232", "PR-233", "PR-234"),
           "Pontzen & Challinor 2007; Saadeh+ 2016 arXiv:1605.07178 (Planck Bianchi)",
           BLOCKER_NATIVE, "entire Track II; blocked until an authenticated native delivery"),
)


@dataclass
class Adjudication:
    family: Family
    significance: str | None = None
    novelty_tier: str | None = None
    novelty_rationale: str = ""
    completeness: str | None = None
    verification: str | None = None
    provenance_status: str | None = None
    literature_blocker: str | None = None      # blocker class the verdict assigns
    citation_key: str = ""
    verdict_survived_refutation: bool | None = None
    refutation: str = ""
    unlock_status: str = "PENDING_LITERATURE"
    rationale: str = ""


def _card_state(pr: str) -> dict:
    n = pr.split("-")[1]
    for name in (f"pr{n}_result_card.json",):
        p = GEN / name
        if p.is_file():
            c = json.loads(p.read_text())
            m = c.get("metadata", {})
            return {"terminal": c.get("terminal"),
                    "readiness": m.get("readiness_state"),
                    "independence": m.get("independence_gate"),
                    "public_use": m.get("public_use")}
    return {"terminal": "NO_CARD"}


def classify(family: Family, verdict: dict | None) -> Adjudication:
    """Combine the structural blocker with the literature verdict into an unlock
    status. Never fake-passes the Independence gate."""
    a = Adjudication(family=family)
    if verdict is None:
        a.unlock_status = "PENDING_LITERATURE"
        a.rationale = "awaiting web-CRAG literature verdict"
        return a
    a.significance = verdict.get("significance")
    a.novelty_tier = verdict.get("novelty_tier")
    a.novelty_rationale = verdict.get("novelty_rationale", "")
    a.completeness = verdict.get("completeness")
    a.verification = verdict.get("verification")
    a.provenance_status = verdict.get("provenance_status")
    a.literature_blocker = verdict.get("blocker_class")
    a.citation_key = verdict.get("citation_key", "")
    a.verdict_survived_refutation = verdict.get("verdict_survives")
    a.refutation = verdict.get("refutation", "")

    # The unlock status is DERIVED here from the axes, not read from either
    # agent's unlock_verdict string -- the workflow skeptics were observed
    # refuting against an earlier version of THIS harness, so their verdict
    # strings are advisory only. significance and novelty are RANKING axes and
    # never gate promotion; only completeness, verification, provenance and the
    # structural blocker gate it.
    override = PROVENANCE_OVERRIDES.get(family.id)
    if override:
        a.provenance_status = "cited_correct"
    provenance_ok = a.provenance_status in ("cited_correct", None)
    axes_ok = a.completeness == "complete" and a.verification == "verified"
    blocker = family.structural_blocker
    lit_blocker = a.literature_blocker

    if blocker == BLOCKER_PROCESS or lit_blocker == "process_only":
        a.unlock_status = "PROCESS_GATE_NO_LITERATURE_AXIS"
        a.rationale = "governance/state-machine card; no external-literature novelty axis"
    elif blocker == BLOCKER_NATIVE or lit_blocker == BLOCKER_NATIVE:
        a.unlock_status = "BLOCKED_ON_NATIVE_SOLVER"
        a.rationale = "requires an authenticated native Bianchi Boltzmann solver delivery (Track II)"
    elif blocker == BLOCKER_DATA or lit_blocker == BLOCKER_DATA:
        a.unlock_status = "BLOCKED_ON_DATA_PR151"
        a.rationale = "DESI official-mock acquisition (PR-151) not yet terminal"
    elif not provenance_ok:
        a.unlock_status = "PROVENANCE_CORRECTION_REQUIRED"
        a.rationale = f"citation issue: {a.provenance_status}"
    elif not axes_ok:
        missing = []
        if a.completeness != "complete":
            missing.append(f"completeness={a.completeness}")
        if a.verification != "verified":
            missing.append(f"verification={a.verification}")
        a.unlock_status = "GENUINELY_INCOMPLETE"
        a.rationale = "not yet complete+verified author-side: " + ", ".join(missing)
    else:
        # complete + verified + correctly cited author-side, not hard-blocked ->
        # the ONLY remaining gate is one non-author Independence adjudication.
        # This harness never fake-passes it; significance/novelty rank the queue.
        a.unlock_status = "PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION"
        a.rationale = ("complete + verified + cited-correct author-side; the only "
                       "remaining gate is one non-author Independence adjudication")
    if override:
        a.rationale += f" | provenance override: {override}"
    if a.verdict_survived_refutation is False:
        a.rationale += " | note: lit-CRAG unlock string was refuted (advisory); status re-derived from axes"
    return a


def promotion_rank(a: Adjudication) -> tuple[int, int]:
    """Rank promotable claims by significance then novelty (higher first)."""
    return (SIGNIFICANCE_ORDER.get(a.significance or "marginal", -1),
            NOVELTY_ORDER.get(a.novelty_tier or "K", -1))


def adjudicate_all(verdicts: dict[str, dict]) -> list[Adjudication]:
    return [classify(f, verdicts.get(f.id)) for f in FAMILIES]
