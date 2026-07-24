"""PR-138 lineage-bound posterior draws, SBC, and replicated-data PPC.

Conjugate Gaussian toy: ``theta ~ N(0, tau2)``, ``y_i ~ N(theta, sig2)``
for i = 1..n. The exact posterior is ``theta | y ~ N(post_var *
sum(y)/sig2, post_var)`` with ``post_var = 1/(1/tau2 + n/sig2)``.

Posterior draws are content-addressed to the normalized prior, the
likelihood, the data, the config, the transfer, and the sampler
diagnostics (a lineage hash); a PPC/SBC run on a posterior whose lineage
does not verify, or whose posterior is invalid (non-finite variance), is
refused. Simulation-based calibration (Talts et al., arXiv:1804.06788)
tests rank uniformity of the prior draw among the posterior draws: the
known-GOOD exact-conjugate model passes the chi-square rank-uniformity
test, and known-BAD models (deflated/inflated posterior variance) FAIL.
Replicated-data PPCs compute Bayesian p-values for MULTIPLE
pre-registered (content-addressed, FROZEN) discrepancies that can never
be swapped after a failure. A caller-supplied prediction/p-value is
never accepted as a PPC receipt, and the plug-in residual stays a
SEPARATE residual_check type.

A PPC pass is model/transfer-conditional predictive adequacy, NOT model
truth; a failure is inadequacy, not a threshold-tuning opportunity; SBC
is computation calibration, not observed-fit validation.
roadmap_rescue_v1:C2.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Mapping

SCHEMA_VERSION = "pr138.sbc_ppc.v1"


class SbcPpcError(ValueError):
    """Raised on any lineage / SBC / PPC / type violation."""


class InadequateModelError(SbcPpcError):
    """The fail-closed inadequate/blocked verdict."""


# ---------------------------------------------------------------------------
# Conjugate Gaussian model + lineage
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GaussianModel:
    tau2: Fraction        # prior variance
    sig2: Fraction        # likelihood variance
    n_obs: int
    var_scale: Fraction = Fraction(1)   # 1 = exact; != 1 = known-bad

    def __post_init__(self) -> None:
        if self.tau2 <= 0 or self.sig2 <= 0 or self.n_obs < 1:
            raise SbcPpcError("invalid model parameters")

    def posterior(self, y_sum: float) -> tuple[float, float]:
        """Exact posterior (mean, variance). The mean always uses the
        TRUE precision; only the reported variance is scaled by
        var_scale (var_scale != 1 is the miscalibrated known-bad model
        used for SBC failure demonstration)."""
        tau2, sig2 = float(self.tau2), float(self.sig2)
        true_var = 1.0 / (1.0 / tau2 + self.n_obs / sig2)
        post_mean = true_var * (y_sum / sig2)
        post_var = true_var * float(self.var_scale)
        if not math.isfinite(post_var) or post_var <= 0:
            raise SbcPpcError("posterior variance is not finite/positive")
        return post_mean, post_var

    def lineage_inputs(self) -> dict:
        return {
            "prior": {"family": "normal", "mean": "0",
                      "var": str(self.tau2)},
            "likelihood": {"family": "normal", "var": str(self.sig2),
                           "n_obs": self.n_obs},
            "sampler": "exact_conjugate",
            "var_scale": str(self.var_scale),
        }


def lineage_hash(model: GaussianModel, data_hash: str, config: Mapping,
                 diagnostics: Mapping) -> str:
    """Content-address the posterior to (normalized prior, likelihood,
    data, config, transfer, sampler diagnostics)."""
    payload = {
        "inputs": model.lineage_inputs(),
        "data_hash": data_hash,
        "config": dict(sorted(config.items())),
        "transfer": "none",
        "diagnostics": dict(sorted(diagnostics.items())),
    }
    canonical = json.dumps(payload, sort_keys=True)
    return "lin-" + hashlib.sha256(canonical.encode()).hexdigest()[:16]


def sbc_lineage_hash(model: GaussianModel, config: Mapping) -> str:
    """SBC content-addresses the COMPUTATION (prior, likelihood, sampler,
    config) — there is no observed data, since SBC calibrates the
    computation, not an observed fit."""
    payload = {
        "inputs": model.lineage_inputs(),
        "config": dict(sorted(config.items())),
        "purpose": "computation_calibration_no_observed_data",
    }
    canonical = json.dumps(payload, sort_keys=True)
    return "sbclin-" + hashlib.sha256(canonical.encode()).hexdigest()[:16]


def verify_sbc_lineage(claimed_hash: str, model: GaussianModel,
                       config: Mapping) -> None:
    actual = sbc_lineage_hash(model, config)
    if claimed_hash != actual:
        raise SbcPpcError(
            f"SBC computation lineage hash {claimed_hash} != {actual} — "
            "lineage mismatch refused")


def verify_lineage(claimed_hash: str, model: GaussianModel,
                   data_hash: str, config: Mapping,
                   diagnostics: Mapping) -> None:
    """A posterior draw whose lineage hash does not match its declared
    inputs is rejected."""
    actual = lineage_hash(model, data_hash, config, diagnostics)
    if claimed_hash != actual:
        raise SbcPpcError(
            f"posterior lineage hash {claimed_hash} != the hash {actual} "
            "of its declared inputs — lineage mismatch refused")


def require_valid_posterior(post_var: float) -> None:
    """A PPC/SBC on an invalid (non-finite/non-positive variance)
    posterior is refused."""
    if not math.isfinite(post_var) or post_var <= 0:
        raise SbcPpcError(
            "posterior variance is not finite/positive; a PPC on an "
            "invalid posterior is refused")


# ---------------------------------------------------------------------------
# Simulation-based calibration (Talts et al.)
# ---------------------------------------------------------------------------

def _require_positive_count(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise SbcPpcError(f"{label} must be a positive integer")


def _data_hash(y) -> str:
    import numpy as np

    return hashlib.sha256(np.asarray(y, dtype=np.float64).tobytes()
                          ).hexdigest()[:16]


def run_sbc(model: GaussianModel, *, n_simulations: int,
            n_draws: int, seed: int, n_bins: int, lineage_hash: str,
            config: Mapping) -> dict:
    """SBC: draw theta0 ~ prior, y ~ likelihood(theta0), sample the
    posterior, rank theta0 among the posterior draws; under a calibrated
    model+sampler the ranks are uniform on {0..n_draws}. The computation
    lineage is MANDATORY and verified before the run. The rank histogram
    is binned into ``n_bins`` equal-width bins (Talts et al. recommend
    binning coarser than the raw rank grid); the chi-square uniformity
    test uses dof = n_bins - 1."""
    import numpy as np

    verify_sbc_lineage(lineage_hash, model, config)
    _require_positive_count(n_simulations, "n_simulations")
    _require_positive_count(n_draws, "n_draws")
    _require_positive_count(n_bins, "n_bins")
    if not (2 <= n_bins <= n_draws + 1):
        raise SbcPpcError(
            f"n_bins {n_bins} must be in [2, n_draws+1={n_draws + 1}]")
    if (n_draws + 1) % n_bins != 0:
        raise SbcPpcError(
            f"n_bins {n_bins} must divide n_draws+1={n_draws + 1} for "
            "equal-width rank bins")
    rng = np.random.Generator(np.random.PCG64(seed))
    tau, sig = math.sqrt(float(model.tau2)), math.sqrt(float(model.sig2))
    ranks = np.empty(n_simulations, dtype=np.int64)
    for i in range(n_simulations):
        theta0 = rng.normal(0.0, tau)
        y = rng.normal(theta0, sig, model.n_obs)
        pm, pv = model.posterior(float(np.sum(y)))
        require_valid_posterior(pv)
        draws = rng.normal(pm, math.sqrt(pv), n_draws)
        ranks[i] = int(np.sum(draws < theta0))
    raw = np.bincount(ranks, minlength=n_draws + 1)
    per_bin = (n_draws + 1) // n_bins
    counts = raw.reshape(n_bins, per_bin).sum(axis=1)
    expected = n_simulations / n_bins
    chi2 = float(np.sum((counts - expected) ** 2 / expected))
    dof = n_bins - 1
    pvalue = float(_chi2_sf(chi2, dof))
    return {
        "n_simulations": n_simulations,
        "n_draws": n_draws,
        "n_bins": n_bins,
        "rank_histogram_binned": counts.tolist(),
        "chi_square": chi2,
        "dof": dof,
        "uniformity_pvalue": pvalue,
        "var_scale": str(model.var_scale),
        "lineage_verified": lineage_hash,
    }


def sbc_verdict(sbc: dict, pvalue_floor: float) -> str:
    """A calibrated model PASSES (uniform ranks, p > floor); a
    miscalibrated one FAILS (p <= floor) and is INADEQUATE."""
    return "calibrated" if sbc["uniformity_pvalue"] > pvalue_floor \
        else "inadequate_sbc_failed"


def require_sbc_calibrated(sbc: dict, pvalue_floor: float,
                          claim: str = "sbc_pass") -> None:
    """A claim of SBC pass is refuted if the rank-uniformity test fails
    (the known-bad model cannot claim calibration)."""
    if "pass" in claim and sbc["uniformity_pvalue"] <= pvalue_floor:
        raise InadequateModelError(
            f"SBC rank-uniformity p-value {sbc['uniformity_pvalue']:.4g} "
            f"<= {pvalue_floor}; the model+sampler is INADEQUATE and "
            "cannot claim SBC calibration")


# ---------------------------------------------------------------------------
# Frozen discrepancy registry + replicated-data PPC
# ---------------------------------------------------------------------------

def _discrepancy(name: str) -> Callable:
    import numpy as np

    table = {
        "sample_variance": lambda y: float(np.var(y, ddof=1)),
        "sample_max": lambda y: float(np.max(y)),
        "sample_range": lambda y: float(np.max(y) - np.min(y)),
    }
    if name not in table:
        raise SbcPpcError(f"unknown discrepancy {name!r}")
    return table[name]


def freeze_discrepancies(names) -> dict:
    """Content-address the frozen discrepancy set BEFORE the data; the
    hash pins the set so it can never be swapped after a failure."""
    names = list(names)
    if not names:
        raise SbcPpcError("at least one frozen discrepancy is required")
    for n in names:
        _discrepancy(n)   # validate each exists
    canonical = json.dumps(sorted(names), sort_keys=True)
    return {"discrepancies": names,
            "frozen_hash": "disc-" + hashlib.sha256(
                canonical.encode()).hexdigest()[:16]}


def require_frozen_discrepancies(frozen: dict, current_names) -> None:
    """Swapping a frozen discrepancy (a content-address change) after a
    failure is rejected."""
    current_names = list(current_names)
    if not current_names:
        raise SbcPpcError("at least one frozen discrepancy is required")
    canonical = json.dumps(sorted(current_names), sort_keys=True)
    current_hash = "disc-" + hashlib.sha256(
        canonical.encode()).hexdigest()[:16]
    if current_hash != frozen["frozen_hash"]:
        raise SbcPpcError(
            "the discrepancy set was changed after freezing (hash "
            f"{current_hash} != frozen {frozen['frozen_hash']}); "
            "swapping a discrepancy after a failure is refused")


def run_ppc(model: GaussianModel, y_obs, frozen: dict, *,
            n_predictive: int, seed: int, lineage: dict,
            fit_sig2: float | None = None) -> dict:
    """Replicated-data PPC: draw theta from the posterior, y_rep from the
    posterior predictive, and compute the Bayesian p-value
    P(T(y_rep) >= T(y_obs)) for each frozen discrepancy. The posterior
    ``lineage`` is MANDATORY and verified against the ACTUAL fitting
    model before the run. ``fit_sig2`` overrides the likelihood variance
    used in FITTING (a mis-specified fit for the known-bad
    demonstration)."""
    import numpy as np

    require_frozen_discrepancies(frozen, frozen["discrepancies"])
    _require_positive_count(n_predictive, "n_predictive")
    y_obs = np.asarray(y_obs, dtype=np.float64)
    if y_obs.ndim != 1 or y_obs.size != model.n_obs:
        raise SbcPpcError(
            f"observed data must be a one-dimensional array of length "
            f"{model.n_obs}")
    if not np.all(np.isfinite(y_obs)):
        raise SbcPpcError("observed data must contain only finite values")
    actual_data_hash = _data_hash(y_obs)
    if lineage.get("data_hash") != actual_data_hash:
        raise SbcPpcError(
            "posterior lineage data hash does not match the actual "
            "observed data")
    fit_model = model if fit_sig2 is None else GaussianModel(
        model.tau2, Fraction(fit_sig2).limit_denominator(10 ** 9),
        model.n_obs, model.var_scale)
    # lineage binds the ACTUAL posterior inputs (the fit model), and is
    # mandatory — a PPC on an unverified lineage is refused.
    verify_lineage(lineage["claimed_hash"], fit_model,
                   actual_data_hash, lineage["config"],
                   lineage["diagnostics"])
    pm, pv = fit_model.posterior(float(np.sum(y_obs)))
    require_valid_posterior(pv)
    rng = np.random.Generator(np.random.PCG64(seed))
    sig = math.sqrt(float(fit_model.sig2))
    rows = []
    for name in frozen["discrepancies"]:
        T = _discrepancy(name)
        t_obs = T(y_obs)
        greater = 0
        for _ in range(n_predictive):
            theta = rng.normal(pm, math.sqrt(pv))
            y_rep = rng.normal(theta, sig, model.n_obs)
            if T(y_rep) >= t_obs:
                greater += 1
        p = greater / n_predictive
        rows.append({"discrepancy": name, "t_obs": t_obs,
                     "bayesian_p": p})
    return {
        "frozen_hash": frozen["frozen_hash"],
        "n_predictive": n_predictive,
        "lineage_verified": lineage["claimed_hash"],
        "fit_sig2": None if fit_sig2 is None else str(fit_sig2),
        "discrepancy_results": rows,
    }


def ppc_verdict(ppc: dict, two_sided_reject: float) -> str:
    """A PPC passes if no Bayesian p-value is below the reject threshold
    or above its complement; a pass is model-CONDITIONAL adequacy, never
    model truth."""
    results = ppc["discrepancy_results"]
    if not isinstance(results, list) or not results:
        raise SbcPpcError(
            "a PPC verdict requires non-empty discrepancy results")
    if (
        not math.isfinite(two_sided_reject)
        or not 0.0 < two_sided_reject < 0.5
    ):
        raise SbcPpcError(
            "the two-sided PPC reject threshold must be finite and in "
            "(0, 0.5)")
    for r in results:
        p = r["bayesian_p"]
        if not math.isfinite(p) or not 0.0 <= p <= 1.0:
            raise SbcPpcError("a Bayesian p-value must be finite and in [0, 1]")
        if p < two_sided_reject or p > 1.0 - two_sided_reject:
            return "inadequate_ppc_extreme"
    return "adequate_conditional"


# ---------------------------------------------------------------------------
# Receipt-type guard + residual_check separation
# ---------------------------------------------------------------------------

def require_ppc_receipt(receipt: Mapping) -> None:
    """A PPC receipt must carry replicated-data discrepancy results and
    a frozen-discrepancy hash. A caller-supplied point prediction or a
    bare p-value is NOT a PPC receipt."""
    if receipt.get("kind") == "caller_prediction" or \
            "point_prediction" in receipt or \
            ("bayesian_p" in receipt and
             "discrepancy_results" not in receipt):
        raise SbcPpcError(
            "a caller-supplied point prediction or p-value is not a PPC "
            "receipt; a PPC receipt requires replicated-data discrepancy "
            "results with a frozen-discrepancy hash")
    if "frozen_hash" not in receipt or "discrepancy_results" not in \
            receipt:
        raise SbcPpcError("a PPC receipt needs a frozen hash and "
                          "replicated-data discrepancy results")
    if "lineage_verified" not in receipt:
        raise SbcPpcError("a PPC receipt must record the verified "
                          "posterior lineage hash")
    results = receipt["discrepancy_results"]
    if not isinstance(results, list) or not results:
        raise SbcPpcError(
            "a PPC receipt needs non-empty replicated-data discrepancy "
            "results")
    for result in results:
        p = result.get("bayesian_p")
        if (
            not isinstance(p, (int, float))
            or isinstance(p, bool)
            or not math.isfinite(p)
            or not 0.0 <= p <= 1.0
        ):
            raise SbcPpcError(
                "a PPC receipt Bayesian p-value must be finite and in [0, 1]")


def standardized_residual_check(model: GaussianModel, y_obs,
                                theta_hat: float) -> dict:
    """The old plug-in residual r = (y - theta_hat)/sig — a SEPARATE
    residual_check type, explicitly NOT a posterior-predictive check."""
    import numpy as np

    y_obs = np.asarray(y_obs, dtype=np.float64)
    sig = math.sqrt(float(model.sig2))
    resid = (y_obs - theta_hat) / sig
    return {
        "type": "residual_check",
        "is_ppc": False,
        "standardized_residuals": resid.tolist(),
        "note": "plug-in standardized residual; NOT a posterior-"
                "predictive check (no replicated data, no lineage)",
    }


def require_not_ppc(check: Mapping) -> None:
    """A residual_check may never be labeled a PPC."""
    if check.get("type") == "residual_check" and check.get("is_ppc"):
        raise SbcPpcError(
            "the plug-in residual_check is not a posterior-predictive "
            "check and may not be labeled is_ppc=True")


# ---------------------------------------------------------------------------
# Chi-square survival function (Wilson-Hilferty-free, series/CF)
# ---------------------------------------------------------------------------

def _chi2_sf(x: float, k: int) -> float:
    """Upper tail of the chi-square distribution with k dof via the
    regularized upper incomplete gamma Q(k/2, x/2)."""
    if x <= 0:
        return 1.0
    return _gammaincc(k / 2.0, x / 2.0)


def _gammaincc(a: float, x: float) -> float:
    """Regularized upper incomplete gamma Q(a, x) (Numerical Recipes:
    series below x < a+1, continued fraction above)."""
    if x < 0 or a <= 0:
        raise SbcPpcError("invalid gammaincc arguments")
    if x == 0:
        return 1.0
    if x < a + 1.0:
        return 1.0 - _gser(a, x)
    return _gcf(a, x)


def _gser(a: float, x: float) -> float:
    gln = math.lgamma(a)
    ap = a
    total = 1.0 / a
    delta = total
    for _ in range(1000):
        ap += 1.0
        delta *= x / ap
        total += delta
        if abs(delta) < abs(total) * 1e-15:
            break
    return total * math.exp(-x + a * math.log(x) - gln)


def _gcf(a: float, x: float) -> float:
    gln = math.lgamma(a)
    tiny = 1e-30
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - gln) * h


# ---------------------------------------------------------------------------
# Caption gate
# ---------------------------------------------------------------------------

_FORBIDDEN_PHRASES = tuple(
    a + b for a, b in (
        ("ppc pass proves", " the model"),
        ("caller p-value accepted", " as ppc"),
        ("swapped the discrepancy", " after"),
        ("sbc validates", " the observed fit"),
        ("residual is", " the ppc"),
        ("shear", " detected"), ("isotropy", " established"),
        ("bianchi geometry", " detected"),
        ("bianchi family", " identified"), ("finding", " rescued"),
        ("validated as", " native"),
    )
)


def lint_caption(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_PHRASES:
        if phrase.lower() in lowered:
            raise SbcPpcError(
                "caption carries forbidden ppc-truth/caller/swap/sbc-fit/"
                "residual/over-claim language")


def generate_caption(good_pvalue: float, bad_verdicts: list,
                     ppc_verdict_label: str) -> str:
    text = (
        "[sbc_ppc] Conjugate-Gaussian toy: known-good model passes the "
        f"SBC rank-uniformity test (p = {good_pvalue:.3f}), and the "
        f"known-bad models are {bad_verdicts}. The replicated-data PPC "
        f"over frozen discrepancies is {ppc_verdict_label} (model/"
        "transfer-conditional adequacy, NOT model truth). SBC is "
        "computation calibration; the residual check is a separate "
        "plug-in type. No detection."
    )
    lint_caption(text)
    return text
