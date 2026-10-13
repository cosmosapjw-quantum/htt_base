"""common.bulkflow_likelihood — Layer C Bayesian bulk-flow inference (COMMON-D).

Implements the likelihood, prior, and dynesty adapter used to sample the
posterior over the bulk-flow vector :math:`\\mathbf V \\in \\mathbb R^3`
(BASS_PY_HTT_TSC_RESEARCH_PLAN §4.2 Layer C, §6.4).

Model
-----
The default survey likelihood is the normalized Gaussian ``u ~ N(X V, C)``.
``C`` is supplied explicitly or built as ``diag(sigma**2 + sigma_star**2)``.
Native/selection factors select rows when their product is zero; positive
factors do not manufacture precision or shrink the Gaussian normalization.
The explicit ``'precision'`` legacy mode uses
``diag((sigma**2 + sigma_star**2)/(native * selection))`` instead.

Priors
------
Component-wise uniform on :math:`V_x, V_y, V_z \\in [-V_{\\max}, +V_{\\max}]`.
The ``prior_transform`` maps the dynesty-native unit cube :math:`U \\in
[0,1]^3` to that range.

Dynesty adapter
---------------
:func:`run_dynesty` lazily imports ``dynesty`` (it is not a hard dependency
of the package). Tests that exercise the likelihood + prior in isolation
never need dynesty; only :func:`run_dynesty` does.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

import numpy as np

from common.bulkflow_covariance import SamplingCovariance, as_sampling_covariance
from common.contracts import DynestyResult

__all__ = [
    "BulkFlowConfig",
    "BulkFlowLikelihood",
    "prior_transform",
    "make_prior_transform",
    "run_dynesty",
]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BulkFlowConfig:
    """Priors + sampler knobs for the Layer C run.

    ``V_max_kmps`` bounds the uniform prior on each Cartesian component
    (conservative default ``2000`` km/s covers the largest published
    bulk-flow claims). ``sigma_star_kmps`` is the intrinsic-scatter term
    added in quadrature to the catalogue's ``sigma`` column.
    """

    V_max_kmps: float = 2000.0
    sigma_star_kmps: float = 0.0
    nlive: int = 500
    dlogz: float = 0.01
    seed: int = 0
    sampler: str = "static"    # 'static' | 'dynamic'

    def __post_init__(self) -> None:
        if self.V_max_kmps <= 0.0:
            raise ValueError(f"V_max_kmps must be > 0; got {self.V_max_kmps}")
        if self.sigma_star_kmps < 0.0:
            raise ValueError(
                f"sigma_star_kmps must be ≥ 0; got {self.sigma_star_kmps}"
            )
        if self.nlive <= 0:
            raise ValueError(f"nlive must be > 0; got {self.nlive}")
        if self.dlogz <= 0.0:
            raise ValueError(f"dlogz must be > 0; got {self.dlogz}")
        if self.sampler not in {"static", "dynamic"}:
            raise ValueError(
                f"sampler must be 'static' or 'dynamic'; got {self.sampler!r}"
            )


# ---------------------------------------------------------------------------
# Likelihood
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BulkFlowLikelihood:
    """Weighted-Gaussian log-likelihood for the bulk-flow vector.

    Parameters
    ----------
    n_hat
        Per-source unit vectors, shape ``(N, 3)``.
    u
        Per-source radial velocities (km/s), shape ``(N,)``.
    sigma
        Per-source velocity uncertainty (km/s), shape ``(N,)``.
    w_native, w_selection
        Three-factor decomposition inputs (see ``bulkflow_estimator``).
        Sources with ``w_native * w_selection = 0`` are dropped.
    sigma_star_kmps
        Additional intrinsic-scatter term added in quadrature.
    """

    n_hat: np.ndarray
    u: np.ndarray
    sigma: np.ndarray
    w_native: np.ndarray
    w_selection: np.ndarray
    sigma_star_kmps: float = 0.0
    sampling_covariance: SamplingCovariance | np.ndarray | None = None
    weight_semantics: str = "survey"
    _active: np.ndarray = field(init=False, repr=False)
    _C: SamplingCovariance = field(init=False, repr=False)
    _const: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        n_hat = np.asarray(self.n_hat, dtype=float)
        u = np.asarray(self.u, dtype=float)
        sigma = np.asarray(self.sigma, dtype=float)
        w_native = np.asarray(self.w_native, dtype=float)
        w_selection = np.asarray(self.w_selection, dtype=float)
        if n_hat.ndim != 2 or n_hat.shape[1] != 3:
            raise ValueError(f"n_hat must be (N, 3); got {n_hat.shape}")
        N = n_hat.shape[0]
        for name, arr in (
            ("u", u), ("sigma", sigma),
            ("w_native", w_native), ("w_selection", w_selection),
        ):
            if arr.shape != (N,):
                raise ValueError(
                    f"{name} shape {arr.shape} incompatible with N={N}"
                )
        norms = np.linalg.norm(n_hat, axis=1)
        if not np.allclose(norms, 1.0, atol=1e-6):
            raise ValueError("n_hat rows must be unit vectors")
        if np.any(sigma <= 0.0):
            raise ValueError("sigma entries must all be > 0")
        if self.sigma_star_kmps < 0.0:
            raise ValueError(
                f"sigma_star_kmps must be ≥ 0; got {self.sigma_star_kmps}"
            )
        if self.weight_semantics not in {"survey", "precision"}:
            raise ValueError("weight_semantics must be 'survey' or 'precision'")
        for name, weights in (("w_native", w_native), ("w_selection", w_selection)):
            if not np.all(np.isfinite(weights)) or np.any(weights < 0.0):
                raise ValueError(f"{name} entries must be finite and ≥ 0")
        # Do not form w_native * w_selection merely to identify exclusions:
        # finite large source weights can overflow despite both factors being
        # valid. Exact zero remains the only source-weight exclusion.
        active = (w_native > 0.0) & (w_selection > 0.0)
        if int(active.sum()) < 4:
            raise ValueError(
                f"only {int(active.sum())} active sources — need ≥ 4 for a "
                "non-degenerate 3-D bulk-flow posterior"
            )
        if self.sampling_covariance is not None:
            if self.weight_semantics == "precision":
                raise ValueError("explicit sampling_covariance is incompatible with legacy precision weights")
            C_full = as_sampling_covariance(self.sampling_covariance)
            if C_full.size != N:
                raise ValueError("sampling_covariance size must equal the catalogue size")
            C = C_full.subset(active)
        else:
            sigma_eff2 = sigma ** 2 + float(self.sigma_star_kmps) ** 2
            diagonal = sigma_eff2[active]
            if self.weight_semantics == "precision":
                diagonal = diagonal / (w_native[active] * w_selection[active])
            C = SamplingCovariance(diagonal=diagonal)
        # Selection/native factors only choose rows in survey mode.  They do
        # not shrink the normalized Gaussian variance or normalization.
        const = -0.5 * (C.size * np.log(2.0 * np.pi) + C.logdet())
        # Re-store the exact ndarrays (so frozen dataclass doesn't convert view).
        object.__setattr__(self, "n_hat", n_hat)
        object.__setattr__(self, "u", u)
        object.__setattr__(self, "sigma", sigma)
        object.__setattr__(self, "w_native", w_native)
        object.__setattr__(self, "w_selection", w_selection)
        object.__setattr__(self, "_active", active)
        object.__setattr__(self, "_C", C)
        object.__setattr__(self, "_const", const)

    @property
    def n_active(self) -> int:
        return int(self._active.sum())

    def log_likelihood(self, theta: np.ndarray) -> float:
        """Log-likelihood at ``theta = (V_x, V_y, V_z)`` (km/s)."""
        theta = np.asarray(theta, dtype=float)
        if theta.shape != (3,):
            raise ValueError(f"theta must be shape (3,); got {theta.shape}")
        a = self._active
        resid = self.u[a] - self.n_hat[a] @ theta
        chi2 = float(resid @ self._C.solve(resid))
        return self._const - 0.5 * chi2

    def __call__(self, theta: np.ndarray) -> float:   # dynesty convenience
        return self.log_likelihood(theta)


# ---------------------------------------------------------------------------
# Prior transform (unit cube → θ)
# ---------------------------------------------------------------------------

def prior_transform(u: np.ndarray, V_max_kmps: float = 2000.0) -> np.ndarray:
    """Uniform prior on each component in ``[-V_max, +V_max]``.

    Accepts dynesty-style unit-cube input ``u ∈ [0, 1]^3`` and returns
    ``theta = 2 V_max (u - 0.5)``.
    """
    u = np.asarray(u, dtype=float)
    if u.shape != (3,):
        raise ValueError(f"u must be shape (3,); got {u.shape}")
    if V_max_kmps <= 0.0:
        raise ValueError(f"V_max_kmps must be > 0; got {V_max_kmps}")
    return 2.0 * float(V_max_kmps) * (u - 0.5)


def make_prior_transform(V_max_kmps: float) -> Callable[[np.ndarray], np.ndarray]:
    """Bind ``V_max_kmps`` into a dynesty-compatible prior_transform(u)."""
    Vm = float(V_max_kmps)

    def _pt(u: np.ndarray) -> np.ndarray:
        return prior_transform(u, V_max_kmps=Vm)

    return _pt


# ---------------------------------------------------------------------------
# Dynesty adapter (Layer C entry)
# ---------------------------------------------------------------------------

def run_dynesty(
    likelihood: BulkFlowLikelihood,
    prior: Callable[[np.ndarray], np.ndarray],
    config: BulkFlowConfig,
    *,
    dynesty_module: Any | None = None,
) -> DynestyResult:
    """Run dynesty's nested sampler and return a :class:`DynestyResult`.

    ``dynesty_module`` is an injection point for tests — pass a stub that
    exposes ``NestedSampler`` / ``DynamicNestedSampler`` with the usual
    dynesty interface. When omitted, the real ``dynesty`` package is
    imported lazily; it is not a hard dependency of this module.
    """
    if dynesty_module is None:
        try:
            import dynesty as dynesty_module  # type: ignore
        except ImportError as exc:   # pragma: no cover — env-specific
            raise RuntimeError(
                "run_dynesty requires the dynesty package; install it with "
                "`pip install dynesty` or inject a stub via dynesty_module="
            ) from exc

    rng = np.random.default_rng(config.seed)
    if config.sampler == "dynamic":
        sampler_cls = dynesty_module.DynamicNestedSampler
    else:
        sampler_cls = dynesty_module.NestedSampler

    sampler = sampler_cls(
        loglikelihood=likelihood.log_likelihood,
        prior_transform=prior,
        ndim=3,
        nlive=config.nlive,
        rstate=rng,
    )
    sampler.run_nested(dlogz=config.dlogz, print_progress=False)
    results = sampler.results

    samples = np.asarray(results.samples, dtype=float)
    logwt = np.asarray(results.logwt, dtype=float)
    logz = float(results.logz[-1]) if np.ndim(results.logz) else float(results.logz)
    ncall = int(getattr(results, "ncall", 0) if not np.ndim(
        getattr(results, "ncall", 0)) else np.sum(results.ncall))

    return DynestyResult(
        samples=samples,
        logwt=logwt,
        logz=logz,
        ncall=ncall,
        config={
            "V_max_kmps": config.V_max_kmps,
            "sigma_star_kmps": config.sigma_star_kmps,
            "nlive": config.nlive,
            "dlogz": config.dlogz,
            "sampler": config.sampler,
            "seed": config.seed,
        },
    )
