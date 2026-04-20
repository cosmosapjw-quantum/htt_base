"""PR13AJ: a_{2m} restoration guarded by a `PreferredAxis` production gate.

Scope (HTT-P0-AJ, INDEPENDENT_TRACKS_PLAN.md §2.3):
---------------------------------------------------
Introduces the frozen ``PreferredAxis`` dataclass with v2 provenance fields
(source, weight_mode, selection_mode, production_allowed, provenance_hash) and
wires ``restore_full_a2m`` so that it refuses to run on any diagnostic axis.

The restoration kernel itself is intentionally minimal — the v2 plan gates
the *entry point*, not the rotation internals. The rotation body raises
``NotImplementedError`` as a placeholder until the full a_{ℓm} rotation logic
is ported. The point of this module is to block diagnostic axes long before
they reach any rotation stage.
"""
from __future__ import annotations

from typing import Dict

from common.contracts import PreferredAxis

__all__ = ["PreferredAxis", "restore_full_a2m"]


def restore_full_a2m(axis: PreferredAxis, a20_seed: complex) -> Dict[int, complex]:
    """Rotate a20 into the full {a_{2m}} tuple under the given axis.

    Parameters
    ----------
    axis : PreferredAxis
        Must satisfy ``axis.production_allowed is True``.
    a20_seed : complex
        Seed a_{20} in the axis-aligned frame.

    Returns
    -------
    dict mapping m ∈ {-2, -1, 0, 1, 2} → a_{2m} (complex).

    Raises
    ------
    RuntimeError
        If ``axis.production_allowed`` is False. This blocks diagnostic axes
        (raw/ZoA-masked/selection-aware-only) from leaking into the a_{ℓm}
        restoration path, which was the root defect in the legacy code.
    """
    if not axis.production_allowed:
        raise RuntimeError(
            "PreferredAxis "
            f"(source={axis.source}, selection_mode={axis.selection_mode}, "
            f"weight_mode={axis.weight_mode}) "
            "is diagnostic-only. a20 → full a2m restoration forbidden."
        )
    raise NotImplementedError(
        "Rotation body pending; HTT-P0-AJ only lands the production gate."
    )
