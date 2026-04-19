"""FB-11.3 skeleton — Bayes-factor contract and TI default.

The production-evidence surface is reserved here as a documented
contract only. During the FB-META-11 skeleton cycle, no thermodynamic
integration or nested-sampling calculation is executed.

References
----------
- `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
  §4.
- Lartillot & Philippe 2006, DOI `10.1080/10635150500433722`.
- Skilling 2006, DOI `10.1214/06-BA127`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bass.inference.drivers.emcee_driver import PosteriorSample


@dataclass(frozen=True)
class BayesFactorResult:
    """Future FB-11.3 Bayes-factor result carrier.

    Contract only: the future implementation returns the evidence ratio,
    an uncertainty estimate, the selected evidence method, and enough
    provenance to reproduce the calculation.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §4.1-§4.4.
    - Lartillot & Philippe 2006.
    """

    ln_B: float
    ln_B_err: float
    method: str
    provenance: dict[str, Any]


def bayes_factor(
    posterior_A: PosteriorSample,
    posterior_B: PosteriorSample,
) -> BayesFactorResult:
    """Reserve the Bayes-factor surface for FB-11.

    Contract only: thermodynamic integration is the documented default
    because the production sampler is `emcee`, while nested sampling via
    `dynesty` remains a reference-only cross-check path outside the CI
    default route.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §4.1-§4.5.
    - Lartillot & Philippe 2006, §2.
    - Skilling 2006, §4.
    """
    raise NotImplementedError(
        "FB-11.3 skeleton only: bayes_factor is reserved for the future "
        "thermodynamic-integration evidence implementation."
    )
