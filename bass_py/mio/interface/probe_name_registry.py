"""mio.interface.probe_name_registry — A37.3 PROBE_ID single-source-of-truth.

INDEPENDENT_TRACKS_PLAN v1.3 §21 Week 13 Day 2 (W12 F3 / W13 R2).
Parent: `docs/dossier/A37_mio_probe_name_schema.md` §A37.3 "Registered PROBE_IDs (v1)".

Problem this module closes (W12 F3):
    A37.3 lists five PROBE_IDs (``CMB``, ``CatWISE``, ``Radio``, ``CF4pp``,
    ``BiPoSH``) in markdown only. The A37.2 grammar regex accepts any
    12-char-alnum string, so a new unregistered probe name would pass the
    producer-side grammar test without ever being audited against the
    dossier. W12 FM3 tagged this as P3 coverage; W13 R2 promotes the
    dossier row to a code-side frozen tuple with a parity test.

Contract (frozen v1, 2026-04-19):
    * ``REGISTERED_PROBE_IDS`` is the authoritative tuple; mutation at
      runtime is forbidden (tuple is immutable; value is bound at import).
    * Adding a new probe is a **three-file commit**: (1) extend this
      tuple, (2) extend the A37.3 markdown table, (3) extend the
      ``STANDARD_PROBES`` / ``STANDARD_Z_PROBES`` sequences in
      ``mio.coherence.directional`` / ``mio.coherence.redshift_binned``.
      The test ``test_probe_name_registry_matches_a37_dossier`` enforces
      (1)↔(2) parity; the W12D1 A37.6 grammar suite covers (3).

G19 posture:
    ``PROBE_ID`` is metadata — never a statistical scalar. The registry
    does not permit numerical coupling; ``is_registered_probe_id`` only
    returns a bool.
"""
from __future__ import annotations

from typing import Tuple


REGISTERED_PROBE_IDS: Tuple[str, ...] = (
    "BiPoSH",
    "CF4pp",
    "CMB",
    "CatWISE",
    "Radio",
)
"""Frozen A37.3 v1 PROBE_ID catalogue (alphabetical; mirrors the five
rows of the A37.3 markdown table)."""


def is_registered_probe_id(name: str) -> bool:
    """Return ``True`` iff ``name`` is in the A37.3 v1 registry.

    Strict equality (case-sensitive). Use this as the gate in any new
    MIO producer that needs to reject typos before the grammar regex
    (which would silently accept ``"cmb"`` as a legal ``PROBE_ID``).
    """
    return name in REGISTERED_PROBE_IDS


__all__ = ["REGISTERED_PROBE_IDS", "is_registered_probe_id"]
