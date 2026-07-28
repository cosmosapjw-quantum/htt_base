"""Active BASS solver-output surfaces.

Historical T_eff and MES-correction helpers are no longer imported eagerly or
listed in ``__all__``.  Attribute access remains reproducible through a
deprecated lazy compatibility path, but those objects are not active anchors.
"""
from __future__ import annotations

from importlib import import_module
import warnings

from bass.forward.ver2_solver_output import (
    BassReleaseMetadata,
    build_solver_core_output,
    build_solver_core_output_from_execution_bundle,
    build_solver_core_output_from_native_result,
    build_solver_core_output_from_lowell_result,
    solver_core_output_from_payload,
    solver_core_output_to_payload,
)
from bass.forward.ver3_output_archive import (
    BoostArchive,
    DEFAULT_HARMONIC_ORDERING,
    alm_power_by_l,
    observer_boost_output,
    observer_boost_output_from_components,
    resolve_output_gate_registry,
    validate_alm_archive,
    write_output_archive,
)
from bass.ver3_contracts import OutputMetadata


_LEGACY_EXPORTS = {
    "TeffBianchiForward": ("bass.forward.teff_forward", "TeffBianchiForward"),
    "theta4_coefficients": ("bass.forward.teff_forward", "theta4_coefficients"),
    "theta4_coefficients_vec": (
        "bass.forward.teff_forward",
        "theta4_coefficients_vec",
    ),
    "monopole_gauge_check": ("bass.forward.teff_forward", "monopole_gauge_check"),
    "teff_backward_linear": (
        "bass.forward.teff_backward",
        "teff_backward_linear",
    ),
    "teff_backward_lsq": ("bass.forward.teff_backward", "teff_backward_lsq"),
    "teff_backward_projection": (
        "bass.forward.teff_backward",
        "teff_backward_projection",
    ),
    "TeffBianchiBackward": (
        "bass.forward.teff_backward",
        "TeffBianchiBackward",
    ),
    "DopplerBoostCorrection": (
        "bass.forward.doppler_boost",
        "DopplerBoostCorrection",
    ),
    "analytical_c1": ("bass.forward.doppler_boost", "analytical_c1"),
    "delta_eps_boost": ("bass.forward.doppler_boost", "delta_eps_boost"),
    "TeffMESBounds": ("bass.forward.teff_mes_bounds", "TeffMESBounds"),
    "VN04_SCENARIOS": ("bass.forward.teff_mes_bounds", "VN04_SCENARIOS"),
}


def __getattr__(name: str):
    target = _LEGACY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    warnings.warn(
        f"bass.forward.{name} is a legacy reproduction export",
        DeprecationWarning,
        stacklevel=2,
    )
    module_name, attribute = target
    return getattr(import_module(module_name), attribute)


__all__ = [
    "BassReleaseMetadata",
    "build_solver_core_output",
    "build_solver_core_output_from_execution_bundle",
    "build_solver_core_output_from_native_result",
    "build_solver_core_output_from_lowell_result",
    "solver_core_output_to_payload",
    "solver_core_output_from_payload",
    "OutputMetadata",
    "BoostArchive",
    "DEFAULT_HARMONIC_ORDERING",
    "alm_power_by_l",
    "observer_boost_output",
    "observer_boost_output_from_components",
    "resolve_output_gate_registry",
    "validate_alm_archive",
    "write_output_archive",
]
