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

from common.contracts import PreferredAxis, SkySupport
from common.mock_calibration import AxisMockCalibrationReport
from htt.zoa.axis_promotion import AxisPromotionRecord, require_axis_for_harmonic_synthesis

__all__ = ["PreferredAxis", "restore_full_a2m"]


def restore_full_a2m(
    axis: PreferredAxis,
    a20_seed: complex,
    *,
    sky_support: SkySupport | None = None,
    promotion_record: AxisPromotionRecord | None = None,
    mock_calibration_report: AxisMockCalibrationReport | None = None,
) -> Dict[int, complex]:
    """Rotate a20 into the full {a_{2m}} tuple under the given axis.

    Parameters
    ----------
    axis : PreferredAxis
        Must pass the HTT harmonic synthesis promotion lock.
    a20_seed : complex
        Seed a_{20} in the axis-aligned frame.

    Returns
    -------
    dict mapping m ∈ {-2, -1, 0, 1, 2} → a_{2m} (complex).

    Raises
    ------
    RuntimeError
        If the axis, sky support, or promotion provenance does not pass the
        PR-042 harmonic synthesis lock. This blocks diagnostic axes
        (raw/ZoA-masked/selection-aware-only) and hand-flipped production flags
        from leaking into the a_{ℓm} restoration path.
    """
    require_axis_for_harmonic_synthesis(
        axis,
        sky_support=sky_support,
        promotion_record=promotion_record,
        mock_calibration_report=mock_calibration_report,
        target="a_2m",
    )
    raise NotImplementedError(
        "Rotation body pending; HTT-P0-AJ only lands the production gate."
    )
