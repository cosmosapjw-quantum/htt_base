"""FB-7.3 skeleton — HTT decomposition and P0-triad contract.

This module deliberately ships no HTT decomposition physics during the
FB-META-7 rotation. The public surface below is a contract placeholder
only and must raise ``NotImplementedError`` until the directional
covariance can be decomposed into HTT-facing components with the P0
triad resolved explicitly.
"""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from bass.runtime.canonical_decision import CanonicalDecision
from tsc.diagnostics.tangency import TangencyResult


def build_htt_decomposition(
    *,
    directional_covariance: Mapping[str, np.ndarray],
    prior_alignment: Mapping[str, object],
    tangency_result: TangencyResult,
    beta_gate: CanonicalDecision,
) -> dict[str, object]:
    """Future FB-7.3 HTT decomposition with explicit P0-triad inputs.

    Contract only: this surface is reserved for the future HTT-facing
    decomposition that turns the anisotropic spectrum/covariance output
    into the components consumed by the likelihood stack, while
    resolving the P0 triad of prior alignment, tangency, and β-gate in
    one auditable place.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7``.
    - ``docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md``
      §2 (`D9`: HTT triad is resolved at FB-7.3 and consumed by FB-8).
    - ``bass/runtime/canonical_decision.py`` (existing β-gate /
      tangency gate SSOT).
    - ``tsc/diagnostics/tangency.py`` (existing `TangencyResult`
      contract).
    - Pontzen & Challinor 2007, arXiv:0706.2075 (corrected external
      Bianchi transfer/polarization anchor for the HTT-facing stage).
    - ``# TODO: citation needed`` exact on-disk Lowell ``§14.2`` locator;
      the prompt-supplied historical path is absent in this worktree and
      is recorded explicitly in the FB-META-7 audit.
    """
    raise NotImplementedError(
        "FB-7.3 skeleton only: HTT decomposition with P0-triad "
        "resolution is not implemented."
    )
