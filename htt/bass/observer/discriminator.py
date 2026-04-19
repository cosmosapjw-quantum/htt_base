"""FB-8.5 skeleton — local-boost-vs-global-tilt discriminator contract.

This module deliberately ships no discriminator physics during the
FB-META-8 rotation. The public surface below is a contract placeholder
only and must raise ``NotImplementedError`` until the observer-frame
discriminator is wired to the FB-7 cosmological-frame likelihood and the
FB-8 observer adapters.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from bass.observer.composition import GlobalTilt
from bass.observer.observer_boost import ObserverBoost


@runtime_checkable
class ObservedDataset(Protocol):
    """Placeholder protocol for the future FB-8 observed-data carrier."""


@runtime_checkable
class CosmologicalHypothesis(Protocol):
    """Placeholder protocol for the future FB-8 hypothesis templates."""


@dataclass(frozen=True)
class DiscriminatorResult:
    """Future FB-8.5 discriminator output schema."""

    Lambda: float
    p_value: float
    ln_ratio: float
    boost_MLE: ObserverBoost
    tilt_MLE: GlobalTilt
    dof: int
    converged: bool


def likelihood_ratio(
    data: ObservedDataset,
    boost_model: CosmologicalHypothesis,
    tilt_model: CosmologicalHypothesis,
    *,
    seed: int,
) -> DiscriminatorResult:
    """Future FB-8.5 observer-vs-cosmological discriminator.

    Contract only: this surface is reserved for the operational
    likelihood-ratio statistic
    `Lambda(data; H_obs, H_cosmo) = 2 [ln L_max(H_cosmo) - ln
    L_max(H_obs)]`. It compares observer-frame and cosmological-frame
    hypotheses without collapsing their parameter axes.

    References
    ----------
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §6 (operational-core contract and result schema).
    - ``bass.observer.adapters`` and ``bass.likelihood.cosmological_frame``
      (the observer-frame discriminator composes on top of the FB-7
      cosmological-frame likelihood; it does not replace it).
    - Kosowsky & Kahniashvili 2011, arXiv:1007.4539 (observer-motion
      signature and Planck-era recoverability of the off-diagonal
      signal).
    - ``# TODO: citation needed`` exact accessible primary source for
      the asymptotic likelihood-ratio calibration; the prompt-supplied
      `Wald 1984` locator could not be verified cleanly in-session and
      is recorded as an explicit gap in the FB-META-8 audit.
    """
    raise NotImplementedError(
        "FB-8.5 skeleton only: local-boost-vs-global-tilt discriminator "
        "is not implemented."
    )
