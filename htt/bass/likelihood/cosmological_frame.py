"""FB-7.4 skeleton — cosmological-frame likelihood contract.

This module deliberately ships no likelihood evaluation physics during
the FB-META-7 rotation. The public surface below is a contract
placeholder only and must raise ``NotImplementedError`` until the FB-7
direction-dependent likelihood is wired to the HTT decomposition.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Literal


class CosmologicalFrameLikelihood:
    """Future FB-7.4 direction-dependent likelihood in the cosmological frame.

    Scope pin: this output is **cosmological-frame only**. FB-8 composes
    the observer-frame layer on top via
    ``bass.likelihood.observer_frame_adapter``; this class must not
    silently absorb observer-frame boost parameters.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7``.
    - ``htt/docs/lowell_bianchi_solver_reference_PR_WBS.md §4`` (local
      observer-side output / covariance / likelihood framing).
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §1.1 and §7 (FB-8 consumes this cosmological-frame likelihood via
      `observer_frame_adapter` rather than reopening the FB-7 scope).
    - Planck Collaboration 2018 V, arXiv:1907.12875 (likelihood-era
      CMB spectra and likelihood context).
    - ``# TODO: citation needed`` exact on-disk Lowell ``§14.3`` locator;
      the prompt-supplied historical path is absent in this worktree and
      is recorded explicitly in the FB-META-7 audit.
    """

    def __init__(
        self,
        *,
        htt_decomposition: Mapping[str, object],
        tier: Literal["low_ell", "hybrid", "full"] = "low_ell",
    ) -> None:
        raise NotImplementedError(
            "FB-7.4 skeleton only: cosmological-frame likelihood "
            "construction is not implemented."
        )

    def log_prob(self, params: Mapping[str, object]) -> float:
        """Evaluate the future cosmological-frame log-likelihood."""
        raise NotImplementedError(
            "FB-7.4 skeleton only: cosmological-frame likelihood "
            "evaluation is not implemented."
        )
