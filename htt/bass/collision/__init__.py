"""BASS collision surfaces.

The package holds the older Thomson kernels plus the VER2 S2 electron-frame
ownership and rate-factor contracts.
"""

from bass.collision.electron_frame import (
    ElectronFrameRate,
    ElectronFrameThomsonContext,
    ExactThomsonSource,
    ProjectedThomsonSource,
    SourceTerms,
    electron_frame_rate_factor,
    exact_thomson_source,
    exact_thomson_gate_bundle,
    project_thomson_source,
)

__all__ = [
    "ElectronFrameRate",
    "ElectronFrameThomsonContext",
    "ExactThomsonSource",
    "ProjectedThomsonSource",
    "SourceTerms",
    "electron_frame_rate_factor",
    "exact_thomson_source",
    "exact_thomson_gate_bundle",
    "project_thomson_source",
]
