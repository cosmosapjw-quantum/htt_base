"""PR-140: normalized-prior coherent evidence with two independent engines.

A conjugate Gaussian evidence toy (no PR4 data) exercises a CORRECT
marginal-likelihood computation:

* the prior ``mu ~ N(0, tau2)`` is a NORMALIZED density whose family and
  hyperparameters are bound, with the likelihood hash, the data hash, the
  engine, its config, and its diagnostics, into ONE content-addressed
  receipt;
* two INDEPENDENT engines estimate the evidence — thermodynamic
  integration (path sampling over a power-posterior ladder) and bridge
  sampling (Meng-Wong, arXiv 1996) — each drawing its own samples
  (distinct seeds and method), and both are cross-checked against the
  EXACT evidence ``Z1 = N(y; 0, sig2 I + tau2 J)``;
* a fitted score, an unnormalized prior, or a caller-supplied scalar is
  NEVER accepted as a Bayes factor or evidence;
* the log Bayes factor is evaluated over a preregistered prior-scale /
  covariance grid; if the engines disagree, the MC diagnostics are
  insufficient, or the prior sensitivity exceeds the ceiling, the claim
  is ``indeterminate``.

Coherent model-comparison mechanics conditional on the registered
model/prior, at ``roadmap_rescue_v1:C3`` — never a detection, a geometry,
or a rescue. Evidence agreement is NOT generative-model correctness.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Callable

import numpy as np

SCHEMA_VERSION = "pr140.coherent_evidence.v1"

# quantities that are NOT an evidence ratio and must never be called one
NON_EVIDENCE_KINDS = ("fitted_score", "max_likelihood_ratio",
                      "caller_scalar", "profile_likelihood")


class EvidenceError(ValueError):
    """Raised when an evidence computation is incoherent or mislabeled."""


class EvidenceStatus(str, Enum):
    COHERENT = "coherent"
    INDETERMINATE = "indeterminate"


# --------------------------------------------------------------------------
# normalized prior
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class NormalPrior:
    """Normalized Gaussian prior ``mu ~ N(mean, var)``.

    ``normalized`` records whether the log-density includes the
    ``-0.5 log(2 pi var)`` normalizer; an unnormalized prior is refused
    because it corrupts the evidence integral.
    """

    mean: float
    var: float
    normalized: bool = True

    def __post_init__(self) -> None:
        if not np.isfinite(self.mean):
            raise EvidenceError("normal-prior mean must be finite")
        if not np.isfinite(self.var) or self.var <= 0:
            raise EvidenceError(
                "normal-prior variance must be finite and positive")
        if not isinstance(self.normalized, bool):
            raise EvidenceError("normal-prior normalized flag must be boolean")

    def log_density(self, mu: np.ndarray) -> np.ndarray:
        mu = np.atleast_1d(mu)
        quad = -0.5 * (mu - self.mean) ** 2 / self.var
        if self.normalized:
            return quad - 0.5 * np.log(2 * np.pi * self.var)
        return quad

    def normalizer_integral(self) -> float:
        """Numerically integrate exp(log_density) — 1.0 iff normalized."""
        grid = np.linspace(self.mean - 12 * self.var ** 0.5,
                           self.mean + 12 * self.var ** 0.5, 20001)
        vals = np.exp(self.log_density(grid))
        return float(np.trapezoid(vals, grid))

    def provenance(self) -> dict:
        return {"family": "normal", "mean": self.mean, "var": self.var,
                "normalized": self.normalized}


def require_normalized_prior(prior: NormalPrior) -> None:
    if not prior.normalized:
        raise EvidenceError(
            "the prior is unnormalized — the evidence integral is only "
            "defined for a normalized prior density")
    integral = prior.normalizer_integral()
    if not np.isfinite(integral) or abs(integral - 1.0) > 1e-4:
        raise EvidenceError(
            "the prior density does not integrate to one")


def require_evidence_kind(kind: str) -> None:
    """Refuse a non-evidence quantity offered as an evidence/Bayes factor."""
    if kind in NON_EVIDENCE_KINDS:
        raise EvidenceError(
            f"a {kind!r} is not a marginal-likelihood ratio and may not be "
            "called a Bayes factor or evidence")


# --------------------------------------------------------------------------
# model + exact evidence
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class GaussianEvidenceModel:
    y: np.ndarray
    sig2: float
    prior: NormalPrior

    @property
    def n(self) -> int:
        return len(self.y)

    def log_likelihood(self, mu: np.ndarray) -> np.ndarray:
        mu = np.atleast_1d(mu)
        sq = ((self.y[:, None] - mu[None, :]) ** 2).sum(axis=0)
        return -0.5 * (self.n * np.log(2 * np.pi * self.sig2) + sq / self.sig2)

    def exact_log_evidence(self) -> float:
        cov = self.sig2 * np.eye(self.n) + self.prior.var * np.ones(
            (self.n, self.n))
        mean = np.full(self.n, self.prior.mean)
        sign, logdet = np.linalg.slogdet(cov)
        diff = self.y - mean
        return float(-0.5 * (self.n * np.log(2 * np.pi) + logdet
                             + diff @ np.linalg.solve(cov, diff)))

    def exact_log_null_evidence(self) -> float:
        """Point null mu = prior.mean (here 0): p(y | mu = mean)."""
        return float(self.log_likelihood(np.array([self.prior.mean]))[0])

    def power_posterior(self, beta: float) -> tuple[float, float]:
        prec = beta * self.n / self.sig2 + 1.0 / self.prior.var
        mean = (beta * self.y.sum() / self.sig2
                + self.prior.mean / self.prior.var) / prec
        return mean, 1.0 / prec

    def posterior(self) -> tuple[float, float]:
        return self.power_posterior(1.0)


def data_hash(y: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(y, dtype=np.float64)
                          .tobytes()).hexdigest()[:16]


def likelihood_hash(model: GaussianEvidenceModel) -> str:
    payload = {"family": "gaussian_known_var", "sig2": model.sig2,
               "n": model.n}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()
                          ).hexdigest()[:16]


# --------------------------------------------------------------------------
# engine 1: thermodynamic integration
# --------------------------------------------------------------------------
def _sample_provenance(method: str, seed: int, n_samples: int) -> str:
    return hashlib.sha256(
        f"{method}:{seed}:{n_samples}".encode()).hexdigest()[:16]


def _digest_draws(*arrays: np.ndarray) -> str:
    """Content fingerprint of an engine's ACTUAL draws (data independence).

    Two engines that post-process the same sample set share this digest
    even under different method labels; genuinely independent draws do
    not.
    """
    h = hashlib.sha256()
    for arr in arrays:
        h.update(np.ascontiguousarray(arr, dtype=np.float64).tobytes())
    return h.hexdigest()[:16]


def thermodynamic_integration(model: GaussianEvidenceModel, *, n_beta: int,
                              beta_power: float, n_samples: int, seed: int,
                              n_bootstrap: int = 0,
                              boot_seed: int = 0) -> dict:
    """log Z via path sampling over a power-posterior beta-ladder."""
    u = np.linspace(0.0, 1.0, n_beta)
    betas = u ** beta_power
    rng = np.random.Generator(np.random.PCG64(seed))
    ebar = np.empty(n_beta)
    evar = np.empty(n_beta)
    samples = []
    for k, b in enumerate(betas):
        m, v = model.power_posterior(b)
        draws = rng.normal(m, v ** 0.5, n_samples)
        ll = model.log_likelihood(draws)
        ebar[k] = ll.mean()
        evar[k] = ll.var(ddof=1)
        samples.append(draws)
    log_evidence = float(np.trapezoid(ebar, betas))
    # analytic MC standard error of the trapezoidal path integral
    w = np.empty(n_beta)
    w[0] = 0.5 * (betas[1] - betas[0])
    w[-1] = 0.5 * (betas[-1] - betas[-2])
    w[1:-1] = 0.5 * (betas[2:] - betas[:-2])
    se = float(np.sqrt(np.sum(w ** 2 * evar / n_samples)))
    boot = _bootstrap_se(
        n_bootstrap, boot_seed,
        lambda bs: float(np.trapezoid(
            [model.log_likelihood(bs.choice(s, size=len(s))).mean()
             for s in samples], betas))) if n_bootstrap else se
    return {"method": "thermodynamic_integration", "log_evidence":
            log_evidence, "n_beta": n_beta, "beta_power": beta_power,
            "n_samples": n_samples, "seed": seed,
            "standard_error": se, "bootstrap_se": boot,
            "mc_standard_error_note": "the MC standard error omits the "
            "deterministic trapezoidal quadrature bias; the coherent verdict "
            "is governed by the bootstrap error and the analytic tolerance",
            "sample_provenance": _sample_provenance(
                "thermodynamic_integration", seed, n_samples * n_beta),
            "sample_digest": _digest_draws(*samples)}


# --------------------------------------------------------------------------
# engine 2: bridge sampling (Meng-Wong)
# --------------------------------------------------------------------------
def _log_unnorm_posterior(model: GaussianEvidenceModel,
                          mu: np.ndarray) -> np.ndarray:
    return model.log_likelihood(mu) + model.prior.log_density(mu)


def _bridge_iterate(l_post: np.ndarray, l_prop: np.ndarray, n1: int,
                    n2: int, max_iter: int) -> tuple[float, int]:
    from scipy.special import logsumexp
    s1 = np.log(n1 / (n1 + n2))
    s2 = np.log(n2 / (n1 + n2))
    logr = 0.0
    for it in range(max_iter):
        num = -np.log(n2) + logsumexp(
            l_prop - np.logaddexp(s1 + l_prop, s2 + logr))
        den = -np.log(n1) + logsumexp(
            -np.logaddexp(s1 + l_post, s2 + logr))
        new = num - den
        if abs(new - logr) < 1e-10:
            return new, it + 1
        logr = new
    return logr, max_iter


def bridge_sampling(model: GaussianEvidenceModel, *, n_posterior: int,
                    n_proposal: int, seed: int, max_iter: int,
                    n_bootstrap: int = 0, boot_seed: int = 0) -> dict:
    """log Z via the Meng-Wong optimal bridge estimator."""
    pm, pv = model.posterior()
    rng = np.random.Generator(np.random.PCG64(seed))
    post = rng.normal(pm, pv ** 0.5, n_posterior)
    g_std = (2.0 * pv) ** 0.5

    def log_g(mu: np.ndarray) -> np.ndarray:
        return -0.5 * (np.log(2 * np.pi * g_std ** 2)
                       + (mu - pm) ** 2 / g_std ** 2)

    prop = rng.normal(pm, g_std, n_proposal)
    l_post = _log_unnorm_posterior(model, post) - log_g(post)
    l_prop = _log_unnorm_posterior(model, prop) - log_g(prop)
    log_evidence, iters = _bridge_iterate(l_post, l_prop, n_posterior,
                                          n_proposal, max_iter)

    def _one(bs) -> float:
        pi = bs.choice(post, size=n_posterior)
        qi = bs.choice(prop, size=n_proposal)
        lp = _log_unnorm_posterior(model, pi) - log_g(pi)
        lq = _log_unnorm_posterior(model, qi) - log_g(qi)
        return _bridge_iterate(lp, lq, n_posterior, n_proposal, max_iter)[0]

    boot = _bootstrap_se(n_bootstrap, boot_seed, _one) if n_bootstrap else 0.0
    return {"method": "bridge_sampling", "log_evidence": log_evidence,
            "n_posterior": n_posterior, "n_proposal": n_proposal,
            "seed": seed, "iterations": iters, "bootstrap_se": boot,
            "sample_provenance": _sample_provenance(
                "bridge_sampling", seed, n_posterior + n_proposal),
            "sample_digest": _digest_draws(post, prop)}


def _bootstrap_se(n_bootstrap: int, seed: int,
                  estimator: Callable) -> float:
    if n_bootstrap <= 0:
        return 0.0
    bs = np.random.Generator(np.random.PCG64(seed))
    vals = np.array([estimator(bs) for _ in range(n_bootstrap)])
    return float(vals.std(ddof=1))


# --------------------------------------------------------------------------
# independence + coherence
# --------------------------------------------------------------------------
def require_independent_engines(e1: dict, e2: dict) -> None:
    if e1["method"] == e2["method"]:
        raise EvidenceError(
            "the two evidence engines use the same method — they are not "
            "independent")
    if e1["sample_provenance"] == e2["sample_provenance"]:
        raise EvidenceError(
            "the two evidence engines share the same sample provenance — "
            "post-processing one sample set twice is not two engines")
    d1, d2 = e1.get("sample_digest"), e2.get("sample_digest")
    if d1 is not None and d1 == d2:
        raise EvidenceError(
            "the two evidence engines drew identical samples (matching "
            "sample digest) — a data-independence check, not just a label "
            "check: post-processing one sample set twice is not two engines")


def compare_engines(engines: list[dict], analytic_log_evidence: float, *,
                    agreement_tol: float, analytic_tol: float,
                    se_ceiling: float) -> dict:
    if len(engines) != 2:
        raise EvidenceError(
            "coherent evidence requires exactly two independent engines")
    require_independent_engines(engines[0], engines[1])
    devs = {e["method"]: abs(e["log_evidence"] - analytic_log_evidence)
            for e in engines}
    gap = max(abs(a["log_evidence"] - b["log_evidence"])
              for a in engines for b in engines)
    standard_errors = []
    for engine in engines:
        value = engine.get("bootstrap_se")
        if isinstance(value, bool):
            continue
        try:
            standard_error = float(value)
        except (TypeError, ValueError):
            continue
        if np.isfinite(standard_error) and standard_error >= 0:
            standard_errors.append(standard_error)
    diagnostics_complete = len(standard_errors) == len(engines)
    max_se = max(standard_errors) if diagnostics_complete else None
    agree = gap <= agreement_tol
    analytic_ok = max(devs.values()) <= analytic_tol
    se_ok = (
        max_se is not None
        and np.isfinite(se_ceiling)
        and se_ceiling >= 0
        and max_se <= se_ceiling
    )
    status = (EvidenceStatus.COHERENT if (agree and analytic_ok and se_ok)
              else EvidenceStatus.INDETERMINATE)
    return {"deviation_vs_analytic": devs, "engine_gap": float(gap),
            "max_bootstrap_se": max_se, "engines_agree": bool(agree),
            "match_analytic": bool(analytic_ok), "diagnostics_ok": bool(se_ok),
            "status": status.value}


def require_coherent(comparison: dict) -> None:
    if comparison["status"] != EvidenceStatus.COHERENT.value:
        raise EvidenceError(
            "the evidence is indeterminate (engine disagreement or "
            "insufficient diagnostics) and may not be reported as a "
            "coherent Bayes factor")


# --------------------------------------------------------------------------
# prior sensitivity
# --------------------------------------------------------------------------
def sensitivity_grid(build_model: Callable[[float, float],
                                           GaussianEvidenceModel],
                     tau2_grid: list[float], sig2_scale_grid: list[float],
                     ) -> dict:
    """Exact log BF over the prior-scale / covariance grid."""
    if not tau2_grid or not sig2_scale_grid:
        raise EvidenceError("sensitivity grids may not be empty")
    rows = []
    for tau2 in tau2_grid:
        for sc in sig2_scale_grid:
            model = build_model(tau2, sc)
            log_bf = model.exact_log_evidence() - model.exact_log_null_evidence()
            if not np.isfinite(log_bf):
                raise EvidenceError(
                    "sensitivity grid produced a non-finite log Bayes factor")
            rows.append({"prior_tau2": tau2, "sig2_scale": sc,
                         "log_bf10": float(log_bf)})
    swing = (max(r["log_bf10"] for r in rows)
             - min(r["log_bf10"] for r in rows))
    return {"grid": rows, "log_bf_swing": float(swing)}


def require_within_ceiling(sensitivity: dict, ceiling: float) -> None:
    swing = sensitivity["log_bf_swing"]
    if not np.isfinite(swing) or swing < 0:
        raise EvidenceError(
            "the log Bayes-factor sensitivity swing must be finite and "
            "non-negative")
    if not np.isfinite(ceiling) or ceiling < 0:
        raise EvidenceError(
            "the log Bayes-factor sensitivity ceiling must be finite and "
            "non-negative")
    if swing > ceiling:
        raise EvidenceError(
            f"the log Bayes factor swings {swing:.3f} "
            f"across the prior/covariance grid (> {ceiling}) — the result "
            "is prior-sensitive and the decisive claim is indeterminate")


# --------------------------------------------------------------------------
# receipt
# --------------------------------------------------------------------------
def evidence_receipt(model: GaussianEvidenceModel, engines: list[dict],
                     comparison: dict) -> dict:
    require_normalized_prior(model.prior)
    inputs = {
        "prior": model.prior.provenance(),
        "likelihood_hash": likelihood_hash(model),
        "data_hash": data_hash(model.y),
        "engines": sorted(e["method"] for e in engines),
        "engine_configs": {e["method"]: {k: v for k, v in e.items()
                                         if k not in ("log_evidence",
                                                      "sample_provenance")}
                           for e in engines},
    }
    receipt_hash = hashlib.sha256(
        json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    return {"schema": "pr140.receipt.v1", "receipt_hash": receipt_hash,
            "inputs": inputs, "status": comparison["status"],
            "note": "the evidence is bound to a normalized prior, the "
                    "likelihood, the data, and two independent engines with "
                    "their diagnostics; evidence agreement is not "
                    "generative-model correctness"}


def caller_scalar_is_not_a_receipt(obj: dict) -> None:
    required_inputs = {
        "prior",
        "likelihood_hash",
        "data_hash",
        "engines",
        "engine_configs",
    }
    inputs = obj.get("inputs")
    if (
        obj.get("schema") != "pr140.receipt.v1"
        or not isinstance(inputs, dict)
        or not required_inputs.issubset(inputs)
    ):
        raise EvidenceError(
            "a caller-supplied scalar is not an evidence receipt — a "
            "receipt binds the normalized prior, likelihood, data, and "
            "engine diagnostics")
    receipt_hash = obj.get("receipt_hash")
    expected = hashlib.sha256(
        json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    if receipt_hash != expected:
        raise EvidenceError(
            "the evidence receipt hash does not match its bound inputs")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("fitted score ", "is the bayes factor"),
        ("unnormalized ", "prior evidence"),
        ("caller scalar ", "is the evidence"),
        ("two engines share ", "the same samples"),
        ("evidence agreement ", "proves the model"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise EvidenceError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(log_bf: float, gap: float, swing: float,
                     status: str) -> str:
    return (
        f"Coherent evidence (two independent engines, thermodynamic "
        f"integration and bridge sampling, cross-checked against the exact "
        f"conjugate-Gaussian evidence): log BF10 {log_bf:.4f}; the engines "
        f"agree to {gap:.4f} in log-evidence and the prior/covariance grid "
        f"swings the log BF by {swing:.4f}. Status {status}. Model-"
        f"comparison mechanics conditional on the registered model and "
        f"prior only; evidence agreement is not model truth; no detection.")
