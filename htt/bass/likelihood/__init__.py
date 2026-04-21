"""bass.likelihood — BASS-bound likelihood adapters.

BF-06 narrows the package-root surface to helpers that bind the legacy FB-7/8
scaffolding to live BASS `SolverCoreOutput` artifacts. Transitional surrogate
constructors remain available from their submodules for audited regression
work, but they are no longer presented as the canonical package API.
"""

from bass.likelihood.live_binding import (
    build_cosmological_frame_likelihood_from_solver_output,
    build_live_htt_decomposition_from_solver_output,
    build_observer_frame_likelihood_from_solver_output,
)

__all__ = [
    "build_live_htt_decomposition_from_solver_output",
    "build_cosmological_frame_likelihood_from_solver_output",
    "build_observer_frame_likelihood_from_solver_output",
]
