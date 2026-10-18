"""Sharp finite coefficient geometry from two distances to one shared anchor.

No covariance, independence, sky-axis rotation, confidence interval, infinite-tail
extrapolation, or physical contamination attribution is inferred. Bounds are
sharp in real dimension >= 3, subject to supplied moments and floating arithmetic.
"""
from __future__ import annotations

import math
import sys


def shared_anchor_bounds(anchor_norm, matched_norm, reconstructed_norm,
                         anchor_matched_distance, anchor_reconstructed_distance):
    """Bound matched/reconstructed geometry without inventing their missing dot.

    Normalize all lengths together to avoid overflow/underflow under a uniform
    unit change. Individual vector norms must be positive. Inconsistent triangles
    and dynamic ranges whose normalized square underflows are rejected.
    """
    raw = (anchor_norm, matched_norm, reconstructed_norm,
           anchor_matched_distance, anchor_reconstructed_distance)
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or
           not math.isfinite(x) or x < 0 for x in raw):
        raise ValueError("FINITE_NONNEGATIVE_LENGTHS_REQUIRED")
    if min(raw[:3]) <= 0:
        raise ValueError("NONZERO_VECTOR_NORMS_REQUIRED")
    scale = max(raw)
    a, b, c, p, q = (x / scale for x in raw)
    if min(a, b, c) < math.sqrt(sys.float_info.min):
        raise ValueError("NORMALIZED_DYNAMIC_RANGE_UNRESOLVED")
    tolerance = 128 * sys.float_info.epsilon

    def anchor_cosine(x, distance):
        if distance > a + x + tolerance or distance < abs(a - x) - tolerance:
            raise ValueError("INCONSISTENT_ANCHOR_TRIANGLE")
        cosine = math.fsum((a * a, x * x, -distance * distance)) / (2 * a * x)
        # A small rounded endpoint is allowed; this is not outward rounding.
        if not -1 - tolerance <= cosine <= 1 + tolerance:
            raise ValueError("ANCHOR_GRAM_NOT_PSD")
        return max(-1., min(1., cosine))

    cu, cv = anchor_cosine(b, p), anchor_cosine(c, q)
    su, sv = math.sqrt((1 - cu) * (1 + cu)), math.sqrt((1 - cv) * (1 + cv))
    center, radius = cu * cv, su * sv
    low_cos, high_cos = max(-1., center - radius), min(1., center + radius)
    along_difference = b * cu - c * cv
    low_distance = scale * math.hypot(along_difference, b * su - c * sv)
    high_distance = scale * math.hypot(along_difference, b * su + c * sv)
    best_positive_cos = max(0., high_cos)
    lower_scale_residual_fraction = math.sqrt((1 - best_positive_cos) * (1 + best_positive_cos))
    # Min_{alpha>=0} ||u-alpha*v||/||u|| is sqrt(1-max(cos,0)^2).
    return {
        "shared_anchor_cosines": {"matched": cu, "reconstructed": cv},
        "shared_anchor_angles_degrees": {
            "matched": math.degrees(math.acos(cu)),
            "reconstructed": math.degrees(math.acos(cv)),
        },
        "matched_reconstructed_cosine_interval": [low_cos, high_cos],
        "matched_reconstructed_angle_degrees_interval": [
            math.degrees(math.acos(high_cos)), math.degrees(math.acos(low_cos))],
        "matched_reconstructed_distance_interval": [low_distance, high_distance],
        "distance_over_matched_interval": [low_distance / matched_norm, high_distance / matched_norm],
        "best_nonnegative_scalar_residual_fraction_lower": lower_scale_residual_fraction,
        "best_nonnegative_scalar_residual_energy_fraction_lower": lower_scale_residual_fraction**2,
        "best_nonnegative_scalar_residual_norm_lower": matched_norm * lower_scale_residual_fraction,
        "best_scalar_gain_interval": [max(0., b / c * low_cos), max(0., b / c * high_cos)],
        "dimension_requirement": "REAL_COEFFICIENT_DIMENSION_AT_LEAST_3",
        "bound_type": "SHARP_CONDITIONAL_GEOMETRY_NOT_CONFIDENCE_OR_OUTWARD_ROUNDED_INTERVAL",
    }
