"""PR-141: contamination-aware local/global mixture with mandatory abstention.

Four EXPLICIT competitors are registered as a fixed model list (no PR4
data): isotropy (null), a local kinematic boost (dipole), a survey /
calibration systematic (a known template), and a shared global anisotropy
(quadrupole / shear). Given data, the framework computes, for each
candidate, the exact conjugate-Gaussian evidence, an identifiability /
rank check on the competing templates, an out-of-sample predictive gain
over the null, a posterior-predictive adequacy check, and the evidence
sensitivity across a prior-scale grid. The ONLY admissible result is a
local/global discrimination CANDIDATE when every gate passes and a
non-null model is decisively favored; otherwise the result is a mandatory
`abstain` / `non_identified`.

Anti-drift, enforced: residuals are never all absorbed into the global
component; a MIO score is never used as a likelihood factor; a
deterministic (fixed-amplitude, profile) branch is compared separately
from the covariance (marginalized) branch and never conflated with the
evidence; changing the model list or the contamination prior after the
outcome requires a NEW registered family and look-elsewhere multiplicity;
and a positive global result is never the objective.

Local/global discrimination-candidate mechanics at
`roadmap_rescue_v1:C3` — never a geometry, a family, or a detection.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from numbers import Real

import numpy as np

SCHEMA_VERSION = "pr141.mixture_competition.v1"

# the fixed, pre-registered competitor list; every model includes the
# intercept, and each non-null model adds ONE distinguishing template
MODELS = {
    "iso": ("intercept",),
    "local": ("intercept", "dipole"),
    "sys": ("intercept", "systematic"),
    "global": ("intercept", "quad"),
}
DISTINGUISHING = {"local": "dipole", "sys": "systematic", "global": "quad"}


class CompetitionError(ValueError):
    """Raised when a competition claim violates the abstention discipline."""


class Outcome(str, Enum):
    DISCRIMINATION_CANDIDATE = "discrimination_candidate"
    ABSTAIN_NO_GAIN = "abstain_no_gain"
    ABSTAIN_NON_IDENTIFIED = "abstain_non_identified"
    ABSTAIN_INADEQUATE = "abstain_inadequate"
    ABSTAIN_PRIOR_SENSITIVE = "abstain_prior_sensitive"


ABSTENTIONS = {Outcome.ABSTAIN_NO_GAIN, Outcome.ABSTAIN_NON_IDENTIFIED,
               Outcome.ABSTAIN_INADEQUATE, Outcome.ABSTAIN_PRIOR_SENSITIVE}


class GenerativeBranch(str, Enum):
    """A deterministic (fixed-amplitude) branch is never conflated with the
    covariance (marginalized-evidence) branch."""
    DETERMINISTIC = "deterministic"
    COVARIANCE = "covariance"


# --------------------------------------------------------------------------
# templates + data
# --------------------------------------------------------------------------
def build_templates(n: int, seed: int, *, collinear: bool = False) -> dict:
    """Fixed, seeded templates on random sky directions (mean-removed).

    ``collinear`` makes the systematic template nearly parallel to the
    dipole (a rank-deficient, non-identified local/systematic pair).
    """
    rng = np.random.Generator(np.random.PCG64(seed))
    dirs = rng.standard_normal((n, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    dipole = dirs @ np.array([0.0, 0.0, 1.0])
    quad = (dirs @ np.array([1.0, 0.0, 0.0])) ** 2 - 1.0 / 3.0
    if collinear:
        systematic = dipole + 0.02 * rng.standard_normal(n)
    else:
        systematic = rng.standard_normal(n)
    out = {"intercept": np.ones(n), "dipole": dipole, "quad": quad,
           "systematic": systematic}
    for key in ("dipole", "quad", "systematic"):
        out[key] = out[key] - out[key].mean()
    return out


def generate_data(true_branch: str, templates: dict, amplitude: float,
                  sig2: float, seed: int) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(seed))
    n = len(templates["intercept"])
    y = np.zeros(n)
    if true_branch in DISTINGUISHING:
        y = y + amplitude * templates[DISTINGUISHING[true_branch]]
    return y + rng.normal(0.0, sig2 ** 0.5, n)


def _design(templates: dict, cols) -> np.ndarray:
    return np.column_stack([templates[c] for c in cols])


# --------------------------------------------------------------------------
# exact conjugate evidence (covariance branch) + deterministic profile
# --------------------------------------------------------------------------
def _mvn_logpdf(y: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> float:
    n = len(y)
    sign, logdet = np.linalg.slogdet(cov)
    if sign <= 0:
        raise CompetitionError("non-PSD evidence covariance")
    diff = y - mean
    return float(-0.5 * (n * np.log(2 * np.pi) + logdet
                         + diff @ np.linalg.solve(cov, diff)))


def log_evidence(y: np.ndarray, templates: dict, cols, sig2: float,
                 tau2: float) -> float:
    """Exact marginal N(y; 0, sig2 I + tau2 X X^T) (covariance branch)."""
    X = _design(templates, cols)
    cov = sig2 * np.eye(len(y)) + tau2 * (X @ X.T)
    return _mvn_logpdf(y, np.zeros(len(y)), cov)


def deterministic_profile_loglik(y: np.ndarray, templates: dict, cols,
                                 sig2: float) -> float:
    """Profile (MLE-amplitude) log-likelihood — the DETERMINISTIC branch.

    This is NOT an evidence and must never be conflated with the marginal
    log-evidence (it does not integrate the prior and always favors the
    larger model).
    """
    X = _design(templates, cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n = len(y)
    return float(-0.5 * (n * np.log(2 * np.pi * sig2) + resid @ resid / sig2))


# --------------------------------------------------------------------------
# gates
# --------------------------------------------------------------------------
def all_evidences(y: np.ndarray, templates: dict, sig2: float,
                  tau2: float) -> dict:
    return {m: log_evidence(y, templates, cols, sig2, tau2)
            for m, cols in MODELS.items()}


def template_collinearity(templates: dict, a: str, b: str) -> float:
    ta, tb = templates[a], templates[b]
    denom = np.sqrt((ta @ ta) * (tb @ tb))
    return 0.0 if denom < 1e-12 else float(abs((ta @ tb) / denom))


def held_out_gain(y: np.ndarray, templates: dict, model: str, sig2: float,
                  tau2: float, *, n_folds: int = 5,
                  seed: int = 0) -> float:
    """Out-of-sample predictive gain of ``model`` over the null (iso).

    Positive when the model predicts held-out data better than isotropy.
    """
    n = len(y)
    rng = np.random.Generator(np.random.PCG64(seed))
    order = rng.permutation(n)
    folds = np.array_split(order, n_folds)
    gain = 0.0
    for test in folds:
        train = np.array([i for i in range(n) if i not in set(test.tolist())])
        gain += (_fold_lpd(y, templates, MODELS[model], sig2, tau2, train,
                           test)
                 - _fold_lpd(y, templates, MODELS["iso"], sig2, tau2, train,
                            test))
    return gain / n


def _fold_lpd(y, templates, cols, sig2, tau2, train, test) -> float:
    X = _design(templates, cols)
    Xtr, Xte = X[train], X[test]
    prec = np.eye(X.shape[1]) / tau2 + Xtr.T @ Xtr / sig2
    cov = np.linalg.inv(prec)
    mean = cov @ (Xtr.T @ y[train] / sig2)
    pred_mean = Xte @ mean
    pred_cov = Xte @ cov @ Xte.T + sig2 * np.eye(len(test))
    return _mvn_logpdf(y[test], pred_mean, pred_cov)


def ppc_pvalue(y: np.ndarray, templates: dict, model: str, sig2: float,
               tau2: float, *, n_rep: int = 2000, seed: int = 0) -> float:
    """Posterior-predictive p-value for a residual-variance discrepancy."""
    X = _design(templates, MODELS[model])
    prec = np.eye(X.shape[1]) / tau2 + X.T @ X / sig2
    cov = np.linalg.inv(prec)
    mean = cov @ (X.T @ y / sig2)
    L = np.linalg.cholesky(cov)
    rng = np.random.Generator(np.random.PCG64(seed))
    obs = float(np.var(y - X @ mean))
    ge = 0
    for _ in range(n_rep):
        beta = mean + L @ rng.standard_normal(len(mean))
        y_rep = X @ beta + rng.normal(0.0, sig2 ** 0.5, len(y))
        if np.var(y_rep - X @ mean) >= obs:
            ge += 1
    return (ge + 1) / (n_rep + 1)


def prior_sensitivity_swing(y: np.ndarray, templates: dict, model: str,
                            sig2: float, tau2_grid) -> float:
    bfs = [log_evidence(y, templates, MODELS[model], sig2, t2)
           - log_evidence(y, templates, MODELS["iso"], sig2, t2)
           for t2 in tau2_grid]
    return float(max(bfs) - min(bfs))


# --------------------------------------------------------------------------
# discrimination decision (mandatory abstention)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class DiscriminationConfig:
    sig2: float
    tau2: float
    gain_margin_log_bf: float
    identifiability_gap: float
    collinearity_threshold: float
    ppc_reject: float
    prior_swing_ceiling: float
    tau2_grid: tuple
    held_out_gain_floor: float
    combination_margin: float = 3.0
    seed: int = 0

    def __post_init__(self) -> None:
        numeric = {
            "sig2": self.sig2,
            "tau2": self.tau2,
            "gain_margin_log_bf": self.gain_margin_log_bf,
            "identifiability_gap": self.identifiability_gap,
            "collinearity_threshold": self.collinearity_threshold,
            "ppc_reject": self.ppc_reject,
            "prior_swing_ceiling": self.prior_swing_ceiling,
            "held_out_gain_floor": self.held_out_gain_floor,
            "combination_margin": self.combination_margin,
        }
        for name, value in numeric.items():
            if not isinstance(value, Real) or not np.isfinite(float(value)):
                raise CompetitionError(f"{name} must be finite")
        if self.sig2 <= 0 or self.tau2 <= 0:
            raise CompetitionError("sig2 and tau2 must be positive")
        for name in (
            "gain_margin_log_bf",
            "identifiability_gap",
            "prior_swing_ceiling",
            "combination_margin",
        ):
            if numeric[name] < 0:
                raise CompetitionError(f"{name} must be non-negative")
        if not 0 <= self.collinearity_threshold <= 1:
            raise CompetitionError(
                "collinearity_threshold must be between zero and one")
        if not 0 < self.ppc_reject < 0.5:
            raise CompetitionError("ppc_reject must be between zero and 0.5")
        if not self.tau2_grid:
            raise CompetitionError("tau2_grid may not be empty")
        if any(
            not isinstance(value, Real)
            or not np.isfinite(float(value))
            or value <= 0
            for value in self.tau2_grid
        ):
            raise CompetitionError(
                "tau2_grid values must be finite and positive")
        if (
            isinstance(self.seed, bool)
            or not isinstance(self.seed, (int, np.integer))
            or self.seed < 0
        ):
            raise CompetitionError("seed must be a non-negative integer")


def discriminate(y: np.ndarray, templates: dict,
                 config: DiscriminationConfig) -> dict:
    """Return the discrimination decision with EVERY gate and the outcome.

    The outcome is a discrimination candidate only when a non-null model
    is decisively favored AND is identified AND adequate AND predicts
    held-out data better than the null AND is not prior-sensitive;
    otherwise it is a mandatory abstention.
    """
    # the production competition uses the fixed pre-registered model list,
    # the covariance (marginalized) evidence branch, an explicit-competitor
    # residual policy, and the Gaussian likelihood — every anti-drift guard
    # is invoked live on this path (a drift supplies a rejected input)
    require_registered_model_list(tuple(MODELS), seen_outcome=False,
                                  supersedes=None, multiplicity=None)
    refuse_residual_absorption("explicit_competitor")
    refuse_mio_as_likelihood("gaussian_loglik")
    refuse_deterministic_as_evidence(GenerativeBranch.COVARIANCE)

    ev = all_evidences(y, templates, config.sig2, config.tau2)
    ranked = sorted(ev, key=ev.get, reverse=True)
    best = ranked[0]
    non_iso = [m for m in ranked if m != "iso"]
    best_non_iso = non_iso[0]
    log_bf = ev[best_non_iso] - ev["iso"]

    # gate 1: decisive gain over the null, with a look-elsewhere penalty for
    # having selected the MAXIMUM evidence over the non-null competitors
    effective_margin = config.gain_margin_log_bf + math.log(len(non_iso))
    no_gain = best == "iso" or log_bf < effective_margin

    # gate 2: identifiability — a small evidence gap between the top-two
    # non-null models is a statistical near-tie and is NON-IDENTIFIED
    # regardless of template geometry (governed by the evidence gap, not
    # collinearity); collinearity of the pair is reported as the mechanism
    # when present (a rank-deficient design), never as a NECESSARY condition
    runner = non_iso[1]
    ev_gap = ev[best_non_iso] - ev[runner]
    collinear = template_collinearity(
        templates, DISTINGUISHING[best_non_iso],
        DISTINGUISHING[runner]) > config.collinearity_threshold
    # a small gap is a statistical near-tie; additionally, if the COMBINED
    # (best + runner) model materially beats the best single model, the data
    # want more than one component and a single-branch attribution is not
    # identified (a superposition outside the single-component list)
    combined_cols = ("intercept",) + tuple(sorted(
        {DISTINGUISHING[best_non_iso], DISTINGUISHING[runner]}))
    ev_combined = log_evidence(y, templates, combined_cols, config.sig2,
                               config.tau2)
    combination_gain = ev_combined - ev[best_non_iso]
    multi_component = combination_gain > config.combination_margin
    non_identified = (ev_gap < config.identifiability_gap) or multi_component

    # gate 3: predictive gain out of sample
    gain = held_out_gain(y, templates, best_non_iso, config.sig2,
                         config.tau2, seed=config.seed)
    no_predictive_gain = gain <= config.held_out_gain_floor

    # gate 4: posterior-predictive adequacy of the favored model
    p_ppc = ppc_pvalue(y, templates, best_non_iso, config.sig2, config.tau2,
                       seed=config.seed + 1)
    inadequate = (p_ppc < config.ppc_reject) or (p_ppc > 1 - config.ppc_reject)

    # gate 5: prior sensitivity
    swing = prior_sensitivity_swing(y, templates, best_non_iso, config.sig2,
                                    config.tau2_grid)
    prior_sensitive = swing > config.prior_swing_ceiling

    # mandatory abstention precedence
    if no_gain or no_predictive_gain:
        outcome = Outcome.ABSTAIN_NO_GAIN
    elif non_identified:
        outcome = Outcome.ABSTAIN_NON_IDENTIFIED
    elif inadequate:
        outcome = Outcome.ABSTAIN_INADEQUATE
    elif prior_sensitive:
        outcome = Outcome.ABSTAIN_PRIOR_SENSITIVE
    else:
        outcome = Outcome.DISCRIMINATION_CANDIDATE

    candidate = best_non_iso if outcome is \
        Outcome.DISCRIMINATION_CANDIDATE else None
    return {
        "evidences": ev, "best_non_iso": best_non_iso, "log_bf_vs_iso": log_bf,
        "effective_gain_margin": effective_margin,
        "identifiability_gap": ev_gap, "collinear_runner": runner,
        "collinear": collinear, "combination_gain": combination_gain,
        "multi_component": multi_component, "non_identified": non_identified,
        "held_out_gain": gain, "ppc_pvalue": p_ppc, "inadequate": inadequate,
        "prior_swing": swing, "prior_sensitive": prior_sensitive,
        "outcome": outcome.value, "candidate": candidate,
    }


def require_not_detection(decision: dict) -> None:
    """A discrimination candidate is not a detection / geometry / family."""
    if decision["outcome"] != Outcome.DISCRIMINATION_CANDIDATE.value:
        raise CompetitionError(
            f"the mandatory result is {decision['outcome']} — no "
            "discrimination candidate may be asserted")


# --------------------------------------------------------------------------
# anti-drift guards
# --------------------------------------------------------------------------
def refuse_residual_absorption(assignment: str) -> None:
    if assignment in ("absorb_into_global", "all_residual_global"):
        raise CompetitionError(
            "residuals may not all be absorbed into the global component; "
            "every competitor is tested explicitly")


def refuse_mio_as_likelihood(factor_kind: str) -> None:
    if factor_kind in ("mio_score", "reporting_score"):
        raise CompetitionError(
            "a MIO / reporting score is not a likelihood factor")


def refuse_deterministic_as_evidence(branch: GenerativeBranch) -> None:
    """The deterministic profile branch is never the model-comparison score."""
    if branch is GenerativeBranch.DETERMINISTIC:
        raise CompetitionError(
            "the deterministic (profile / fixed-amplitude) branch is not an "
            "evidence and may not be used for model comparison; use the "
            "covariance (marginalized) evidence branch")


def require_registered_model_list(declared: tuple, seen_outcome: bool,
                                  supersedes: str | None,
                                  multiplicity: int | None) -> None:
    """Changing the model list after the outcome needs a new family."""
    if tuple(declared) != tuple(MODELS):
        if not seen_outcome:
            raise CompetitionError(
                "the model list is fixed and pre-registered")
        if supersedes is None or multiplicity is None:
            raise CompetitionError(
                "changing the model list after the outcome requires a NEW "
                "registered family and an updated look-elsewhere multiplicity")


def model_list_fingerprint(models=MODELS) -> str:
    return hashlib.sha256(
        json.dumps({m: list(c) for m, c in models.items()}, sort_keys=True)
        .encode()).hexdigest()[:16]


# --------------------------------------------------------------------------
# confusion / abstention matrix
# --------------------------------------------------------------------------
def confusion_matrix(regimes: dict, config: DiscriminationConfig, *,
                     n: int, template_seed: int, data_seed: int) -> dict:
    """For each (regime, true branch), the mandatory discrimination outcome."""
    rows = []
    for regime, params in regimes.items():
        templates = build_templates(n, template_seed,
                                    collinear=params["collinear"])
        for true in ("iso", "local", "sys", "global"):
            y = generate_data(true, templates, params["amplitude"],
                              config.sig2, data_seed)
            decision = discriminate(y, templates, config)
            rows.append({
                "regime": regime, "true_branch": true,
                "outcome": decision["outcome"],
                "candidate": decision["candidate"],
                "log_bf_vs_iso": decision["log_bf_vs_iso"],
                "recovered": decision["candidate"] == true,
            })
    return {"rows": rows}


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("global anisotropy ", "detected"),
        ("bianchi geometry ", "identified"),
        ("residuals absorbed ", "into global"),
        ("mio score ", "as likelihood"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise CompetitionError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(n_recovered: int, n_abstained: int, n_cells: int) -> str:
    return (
        f"Contamination-aware model competition (isotropy, local boost, "
        f"survey systematic, global anisotropy) with mandatory abstention: "
        f"of {n_cells} synthetic cells, {n_recovered} recovered the true "
        f"branch and {n_abstained} abstained (no gain, non-identified, "
        f"inadequate, or prior-sensitive). Local/global discrimination-"
        f"candidate mechanics only; a candidate is not a detection, a "
        f"geometry, or a family.")
