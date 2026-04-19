"""FB-8.6 skeleton — observer-frame likelihood adapter contract.

This module deliberately ships no observer-frame likelihood-composition
physics during the FB-META-8 rotation. The public surface below is a
contract placeholder only and must raise ``NotImplementedError`` until
the FB-7 cosmological-frame likelihood is wrapped by the FB-8 observer
stack.
"""
from __future__ import annotations

from typing import Protocol, TypeVar

from bass.likelihood.cosmological_frame import CosmologicalFrameLikelihood
from bass.observer.observer_boost import ObserverBoost

T = TypeVar("T")


class Prior(Protocol[T]):
    """Placeholder protocol for the future prior carrier."""

    def log_prob(self, value: T) -> float: ...


class ObserverFrameLikelihood:
    """Future FB-8.6 observer-frame likelihood wrapper.

    Contract only: this class wraps an FB-7 cosmological-frame
    likelihood so that observer-frame boost parameters can be layered on
    top as a separate axis. It must not fold observer boosts back into
    the cosmological-frame class itself.

    References
    ----------
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §7 (canonical likelihood-stack ingest contract).
    - ``bass.likelihood.cosmological_frame`` (the FB-7 cosmological-only
      base surface this adapter composes over).
    - Kosowsky & Kahniashvili 2011, arXiv:1007.4539 (observer-motion
      signal scale and recoverability context for the boost prior).
    - ``# TODO: citation needed`` exact on-disk Lowell ``§14`` locator;
      the prompt-supplied historical Lowell reference is absent in this
      worktree and remains an explicit audit gap rather than an invented
      citation.
    """

    def __init__(
        self,
        *,
        cosmo_likelihood: CosmologicalFrameLikelihood,
        boost_prior: Prior[ObserverBoost],
    ) -> None:
        raise NotImplementedError(
            "FB-8.6 skeleton only: observer-frame likelihood wrapping is "
            "not implemented."
        )

    def log_prob(self, params: dict[str, object]) -> float:
        """Evaluate the future observer-frame log-likelihood."""
        raise NotImplementedError(
            "FB-8.6 skeleton only: observer-frame log_prob is not "
            "implemented."
        )

    def marginalise_boost(self, params: dict[str, object]) -> float:
        """Marginalise the future observer-frame likelihood over boosts."""
        raise NotImplementedError(
            "FB-8.6 skeleton only: observer-frame boost marginalisation "
            "is not implemented."
        )

    def profile_boost(
        self, params: dict[str, object]
    ) -> tuple[float, ObserverBoost]:
        """Profile the future observer-frame likelihood over boosts."""
        raise NotImplementedError(
            "FB-8.6 skeleton only: observer-frame boost profiling is "
            "not implemented."
        )
