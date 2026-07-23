"""PR-212: congruence-indexed frame and rest-space curvature functor (RESCUE).

The boost-order type algebra + five-axis CAS are closed in PR-187; the exact
vorticity classification is in KE-FRAME/KE-OBS. This module adds the congruence
geometry that PR-187 does not: a frame-indexed symbol registry over the PR-210
DefectBundle plus a Frobenius gate. A vortical congruence (omega != 0) is NOT
hypersurface-orthogonal, so its orthogonal-hypersurface Gauss curvature does not
exist -- only the rest-bundle 3-Ricci does. n-frame shear and u-frame W2 may not
be assembled into one quantity without a registered bridge.
"""

from __future__ import annotations

from dataclasses import dataclass

from common.revival_defect_bundle import Frame


class FrameFunctorError(TypeError):
    pass


@dataclass(frozen=True)
class FrameSymbol:
    """A physical symbol tagged with the congruence frame it lives in."""
    name: str
    frame: Frame
    tensor_type: str  # e.g. 'shear', 'vorticity_scalar', 'rest_3ricci'


# canonical frame-indexed symbol registry (which frame each carrier lives in)
REGISTRY: dict[str, FrameSymbol] = {
    "sigma_ab": FrameSymbol("sigma_ab", Frame.NORMAL, "shear"),
    "W2_n": FrameSymbol("W2_n", Frame.NORMAL, "vorticity_scalar"),
    "W2_u": FrameSymbol("W2_u", Frame.MATTER, "vorticity_scalar"),
    "R3_n": FrameSymbol("R3_n", Frame.NORMAL, "rest_3ricci"),
    "rest_curv_u": FrameSymbol("rest_curv_u", Frame.MATTER, "rest_3ricci"),
    "A_v": FrameSymbol("A_v", Frame.OBSERVER, "kinematic_dipole"),
}


def is_hypersurface_orthogonal(vorticity_sq: float, tol: float = 0.0) -> bool:
    """Frobenius theorem: a congruence is hypersurface-orthogonal iff omega = 0."""
    return abs(vorticity_sq) <= tol


def orthogonal_hypersurface_gauss_curvature(vorticity_sq: float, gauss_curvature: float) -> float:
    """Only defined when the congruence is hypersurface-orthogonal (Frobenius)."""
    if not is_hypersurface_orthogonal(vorticity_sq):
        raise FrameFunctorError(
            "vortical congruence has no orthogonal hypersurface; "
            "Gauss curvature of the rest space is undefined (use the rest-bundle 3-Ricci)")
    return gauss_curvature


def rest_bundle_3ricci(frame: Frame, value: float) -> FrameSymbol:
    """The rest-bundle 3-Ricci is always defined (vortical or not); it is NOT
    the orthogonal-hypersurface Gauss curvature."""
    return FrameSymbol(f"R3_{frame.value}", frame, "rest_3ricci")


def assemble(symbols: list[FrameSymbol], bridged: bool = False) -> Frame:
    """Frame-indexed assembly: all symbols must share a frame unless bridged."""
    frames = {s.frame for s in symbols}
    if len(frames) == 1:
        return next(iter(frames))
    if not bridged:
        raise FrameFunctorError(
            "cannot assemble symbols from different frames without a registered bridge "
            f"(frames={sorted(f.value for f in frames)})")
    return next(iter(frames))


def n_shear_u_w2_without_bridge_rejected() -> bool:
    """Decisive falsifier probe: n-frame shear + u-frame W2 without a bridge."""
    try:
        assemble([REGISTRY["sigma_ab"], REGISTRY["W2_u"]], bridged=False)
        return False
    except FrameFunctorError:
        return True
