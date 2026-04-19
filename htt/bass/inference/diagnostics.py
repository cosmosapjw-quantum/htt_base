"""FB-11.4 skeleton — convergence diagnostics and thresholds.

This module reserves the public diagnostics surface for posterior
convergence checks. During the FB-META-11 skeleton cycle, the functions
document the threshold policy and then raise `NotImplementedError`.

References
----------
- `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
  §5.
- Gelman & Rubin 1992, *Statistical Science* 7, 457-472.
- Geweke 1992 / 1991 technical report lineage for spectral convergence
  diagnostics.
- Vehtari et al. 2021, `arXiv:1903.08008` (improved modern `R-hat`
  context for the stricter project threshold).
"""
from __future__ import annotations

from typing import Any

import numpy as np


def r_hat(samples: np.ndarray) -> np.ndarray:
    """Reserve the per-dimension `R-hat` diagnostic.

    Contract only: the future implementation computes a per-dimension
    convergence diagnostic whose project acceptance threshold is
    `R-hat < 1.01`. The original Gelman-Rubin statistic tends to 1 at
    convergence, while the stricter `1.01` cutoff is a later operational
    policy pinned by the FB-11 SDD rather than a claim about the 1992
    paper itself.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §5.1-§5.3.
    - Gelman & Rubin 1992, §2.
    - Vehtari et al. 2021.
    """
    raise NotImplementedError(
        "FB-11.4 skeleton only: r_hat is reserved for the future "
        "convergence-diagnostic implementation."
    )


def ess(samples: np.ndarray) -> np.ndarray:
    """Reserve the per-dimension effective sample size diagnostic.

    Contract only: the project threshold is `ESS > 400` per dimension,
    matching the FB-11 SDD policy. The skeleton plants the threshold
    contract without computing any autocorrelation estimate yet.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §5.2.
    - Foreman-Mackey et al. 2013, `arXiv:1202.3665`.
    """
    raise NotImplementedError(
        "FB-11.4 skeleton only: ess is reserved for the future "
        "effective-sample-size implementation."
    )


def geweke(
    samples: np.ndarray,
    *,
    first: float = 0.1,
    last: float = 0.5,
) -> np.ndarray:
    """Reserve the Geweke split-window `z` diagnostic.

    Contract only: the future implementation compares the first `10 %`
    and last `50 %` windows of each chain and treats `|z| < 2` as the
    default acceptance threshold.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §5.1-§5.2.
    - Geweke 1992 / 1991 technical-report lineage.
    """
    raise NotImplementedError(
        "FB-11.4 skeleton only: geweke is reserved for the future "
        "split-window convergence-diagnostic implementation."
    )


def trace_plot_data(samples: np.ndarray) -> dict[str, Any]:
    """Reserve the trace-plot payload helper for the future CLI/report."""
    raise NotImplementedError(
        "FB-11.4 skeleton only: trace_plot_data is reserved for the "
        "future diagnostics-report implementation."
    )
