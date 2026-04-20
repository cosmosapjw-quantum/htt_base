"""BASS collision surfaces.

The package holds the older Thomson kernels plus the VER2 S2 electron-frame
ownership and rate-factor contracts.
"""

from bass.collision.electron_frame import (
    ElectronFrameRate,
    ElectronFrameThomsonContext,
    ThomsonProjectionStub,
    electron_frame_rate_factor,
    project_thomson_source_stub,
)

__all__ = [
    "ElectronFrameRate",
    "ElectronFrameThomsonContext",
    "ThomsonProjectionStub",
    "electron_frame_rate_factor",
    "project_thomson_source_stub",
]
