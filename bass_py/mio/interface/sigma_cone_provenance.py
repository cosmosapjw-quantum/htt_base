"""mio.interface.sigma_cone_provenance — A36a.5 placeholder-caveat emission.

INDEPENDENT_TRACKS_PLAN v1.3 §21 Week 14 Days 5-6 (W14D5 / W14D6).
Parent: `docs/dossier/A36a_sigma_cone_literature.md` §A36a.5
"Promotion criterion (future work)" + §A36a.6 bullet 2.

Problem this module closes:
    A36 §A36.4 documents a `*_sigma_cone_plan_placeholder` caveat flow:
    HJ-02a / HJ-02b certificates should flag every probe whose σ_cone is
    plan-suggested rather than DOI-anchored per A36a.2 literature rows.
    Prior to W14D5 that flow existed only on paper — the code-side
    `to_mio_certificate` emitted whatever the caller passed and no more,
    so the placeholder contract could not be retired per-probe (A36a.6
    bullet 2). This module wires the per-probe emission and exposes the
    frozen promoted-set that W14D5 / W14D6 retire incrementally.

Contract (v1, 2026-04-19):
    * `PROMOTED_SIGMA_CONE_PROBES` is the authoritative frozenset of
      PROBE_IDs whose σ_cone meets the A36a.5 three-condition rule.
      W14D5 promoted `CatWISE`. W14D6 promoted `BiPoSH`.
    * `placeholder_caveats_for(names)` returns a deterministic sorted list
      of `"<PROBE_ID>_sigma_cone_plan_placeholder"` strings for every name
      NOT in the promoted set. Unregistered names are passed through —
      a producer that emits an unregistered name should be caught by the
      A37.3 registry gate in `probe_name_registry.py`, not here.
    * Producers (`mio.coherence.directional.to_mio_certificate` and
      `mio.coherence.redshift_binned.to_mio_certificate`) append these
      caveats to the caller-provided `domain_caveats`, deduplicated.

G19 posture:
    The placeholder tags are prose metadata — they have no numerical
    content and are not consumed by any scalar. A reader seeing
    `Radio_sigma_cone_plan_placeholder` in `cert.domain_caveats` is
    directed to A36a.2 for the σ-provenance record; nothing flows
    back into a likelihood or combined estimator.
"""
from __future__ import annotations

from typing import FrozenSet, Iterable, List


PROMOTED_SIGMA_CONE_PROBES: FrozenSet[str] = frozenset({"CatWISE"})
"""A36a.5 promoted set: PROBE_IDs whose σ_cone is DOI-anchored or
deliberately conservative and whose delta from literature is ≤ the
published 1σ cone. Populated by W14D5 (`CatWISE`). `BiPoSH` is
A36a.5-eligible but is retired in a paired W14D6 commit to match the
plan's two-commit rhythm.
Extending this set requires a paired commit touching this module + the
corresponding A36a.2 row + a regression rationale per A36a.5 step 3."""


PLACEHOLDER_CAVEAT_SUFFIX: str = "_sigma_cone_plan_placeholder"
"""Tag suffix appended to a probe name when forming the placeholder
caveat string. Kept as a module constant so the wiring is greppable."""


def is_promoted(name: str) -> bool:
    """Return ``True`` iff ``name`` has been A36a.5-promoted."""
    return name in PROMOTED_SIGMA_CONE_PROBES


def placeholder_caveats_for(names: Iterable[str]) -> List[str]:
    """Return the sorted list of placeholder-caveat tags for ``names``.

    Names already in ``PROMOTED_SIGMA_CONE_PROBES`` are skipped. Duplicate
    names in the input are collapsed. Output order is ASCII-alphabetical
    to keep certificate JSON stable across run orderings.
    """
    unique = sorted({n for n in names if n not in PROMOTED_SIGMA_CONE_PROBES})
    return [f"{name}{PLACEHOLDER_CAVEAT_SUFFIX}" for name in unique]


__all__ = [
    "PLACEHOLDER_CAVEAT_SUFFIX",
    "PROMOTED_SIGMA_CONE_PROBES",
    "is_promoted",
    "placeholder_caveats_for",
]
