"""FB-11.2 skeleton — emcee driver and reproducibility contract.

The future third-party `emcee` import is intentionally confined to this
module path. The FB-META-11 skeleton plants the public contract without
importing `emcee` yet, so no production surface silently acquires a
runtime dependency before the actual-work phase.

References
----------
- `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
  §3.
- Foreman-Mackey et al. 2013, `arXiv:1202.3665`.
- Goodman & Weare 2010, CAMCoS 5(1), 65-80.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from bass.inference.priors import Prior


LikelihoodFn = Callable[[np.ndarray], float]


@dataclass(frozen=True)
class PosteriorSample:
    """Future FB-11.2 posterior container.

    Determinism contract: once implemented, two calls to
    `run_posterior(..., seed=42)` on the same machine with the same
    likelihood, priors, and sampler config must return byte-identical
    `samples`, `log_prob`, and `diagnostics`.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §3.1-§3.2.
    - Foreman-Mackey et al. 2013, `arXiv:1202.3665`.
    """

    samples: np.ndarray
    log_prob: np.ndarray
    seed: int
    sampler: str
    config: dict[str, Any]
    diagnostics: dict[str, Any]


def run_posterior(
    likelihood: LikelihoodFn,
    priors: dict[str, Prior],
    *,
    seed: int,
    n_walkers: int = 64,
    n_steps: int = 5000,
    burnin: int = 1000,
    parallel: bool = False,
) -> PosteriorSample:
    """Reserve the emcee-backed posterior driver.

    Determinism contract: once implemented,
    `run_posterior(..., seed=42, parallel=False)` must return a
    `PosteriorSample` whose `samples`, `log_prob`, and `diagnostics` are
    byte-identical across two runs on the same machine. The documented
    `parallel=True` path is explicitly non-default because thread-pool
    nondeterminism is the pinned failure mode in the FB-11 SDD.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §3.1-§3.5.
    - Foreman-Mackey et al. 2013, `arXiv:1202.3665`, §2.
    - Goodman & Weare 2010, CAMCoS 5(1), 65-80, §3.
    """
    raise NotImplementedError(
        "FB-11.2 skeleton only: run_posterior is reserved for the "
        "future emcee-backed deterministic driver implementation."
    )
