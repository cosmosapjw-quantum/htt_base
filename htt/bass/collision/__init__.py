"""BASS collision surfaces.

The package holds the older Thomson kernels plus the VER2 S2 electron-frame
ownership and rate-factor contracts.
"""

from bass.collision.electron_frame import (
    AngularStokesThomsonSource,
    AngularStokesTemperatureCollision,
    ElectronFrameRate,
    ElectronFrameThomsonContext,
    ExactThomsonSource,
    FullStokesMuellerKernel,
    FullStokesTemperatureKernel,
    ProjectedThomsonSource,
    SourceTerms,
    build_full_stokes_mueller_kernel,
    build_full_stokes_temperature_kernel,
    electron_frame_rate_factor,
    exact_thomson_source,
    exact_thomson_gate_bundle,
    full_stokes_mueller_collision,
    full_stokes_temperature_collision,
    full_stokes_thomson_source,
    project_thomson_source,
    rotate_screen_basis,
    rotate_stokes_samples,
)

__all__ = [
    "AngularStokesThomsonSource",
    "AngularStokesTemperatureCollision",
    "ElectronFrameRate",
    "ElectronFrameThomsonContext",
    "ExactThomsonSource",
    "FullStokesMuellerKernel",
    "FullStokesTemperatureKernel",
    "ProjectedThomsonSource",
    "SourceTerms",
    "build_full_stokes_mueller_kernel",
    "build_full_stokes_temperature_kernel",
    "electron_frame_rate_factor",
    "exact_thomson_source",
    "exact_thomson_gate_bundle",
    "full_stokes_mueller_collision",
    "full_stokes_temperature_collision",
    "full_stokes_thomson_source",
    "project_thomson_source",
    "rotate_screen_basis",
    "rotate_stokes_samples",
]
