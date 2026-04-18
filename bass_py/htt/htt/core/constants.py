"""htt.core.constants — 3-tier ZoA / directional defaults (HTT-P0-ZOA20).

INDEPENDENT_TRACKS_PLAN.md §2.5 item 3 mandates a three-tier split for
Zone-of-Avoidance angular defaults so that `FLRW_tilt_zoa20_mean` (or any
equivalent single-value diagnostic default) cannot silently leak into the
production inference path:

  1. ``RECOMMENDED_ZOA_HALF_ANGLE_DEG``    — paper-grade default for new runs
  2. ``OPERATIONAL_DEFAULT_ZOA_HALF_ANGLE_DEG`` — legacy diagnostic default
  3. ``PRODUCTION_DEFAULT_AXIS``            — MUST remain ``None``; production
     axes come only from posterior-derived constructors.

The sweep documented in ``docs/audits/ZOA20_SWEEP_2026-04-19.md`` found zero
occurrences of the legacy ``zoa20_mean`` / ``FLRW_tilt_zoa20`` symbols in the
current snapshot, so this module lands the forward-looking scaffolding rather
than replacing any existing reference.
"""
from __future__ import annotations

from typing import Optional


RECOMMENDED_ZOA_HALF_ANGLE_DEG: float = 20.0
"""Paper-grade ZoA half-angle default (Kogut et al. 1993 WMAP/Planck
convention). New production analyses should declare this explicitly."""


OPERATIONAL_DEFAULT_ZOA_HALF_ANGLE_DEG: float = 20.0
"""Operational diagnostic default. Equal to the recommendation for now;
exists as a separate symbol to allow the diagnostic layer to drift without
silently perturbing production (they must be moved separately, by name)."""


PRODUCTION_DEFAULT_AXIS: Optional[object] = None
"""MUST be None. Production axes come exclusively from posterior-derived
constructors (e.g. ``common.posterior_summary.axis_from_posterior``). Any
attempt to set a non-None global default here is the very bug
HTT-P0-ZOA20 guards against."""
