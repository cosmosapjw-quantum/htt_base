"""Reference dynesty evidence driver for the FB-11 toy cross-check."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


LikelihoodFn = Callable[[np.ndarray], float]
PriorTransformFn = Callable[[np.ndarray], np.ndarray]


@dataclass(frozen=True)
class NestedEvidenceResult:
    ln_Z: float
    ln_Z_err: float
    sampler: str
    ncall: int


def run_nested_evidence(
    likelihood: LikelihoodFn,
    prior_transform: PriorTransformFn,
    ndim: int,
    *,
    seed: int,
    nlive: int = 300,
) -> NestedEvidenceResult:
    """Evaluate a reference nested-sampling evidence with dynesty."""
    import dynesty  # type: ignore

    sampler = dynesty.NestedSampler(
        loglikelihood=lambda theta: float(likelihood(np.asarray(theta, dtype=float))),
        prior_transform=lambda cube: np.asarray(prior_transform(np.asarray(cube, dtype=float)), dtype=float),
        ndim=int(ndim),
        nlive=int(nlive),
        sample="rwalk",
        bound="multi",
        rstate=np.random.default_rng(int(seed)),
    )
    sampler.run_nested(dlogz=0.01, print_progress=False)
    results = sampler.results
    return NestedEvidenceResult(
        ln_Z=float(results.logz[-1]),
        ln_Z_err=float(results.logzerr[-1]),
        sampler=f"dynesty-{getattr(dynesty, '__version__', 'unknown')}",
        ncall=int(np.sum(results.ncall)),
    )

