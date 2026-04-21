"""bass.forward — Forward/backward T_eff closure and MES-bound corrections.

Provides the T_eff angular dependence Θ(ê) = 1 + A·P₁(cosθ) + Q·P₂(cosθ)
and its Θ⁴ Legendre expansion (C-14 Gaunt algebra), plus the two-layer
correction hierarchy to MES kinematic bounds (C-09b Doppler boost × C-14
Gaunt nonlinearity).

Modules
-------
teff_forward       Closed-form Θ⁴ Legendre coefficients a₀..a₈(A, Q).
teff_backward      Inversion a_ℓ → (A, Q) — linear / least-squares / exact
                   Gauss-Legendre projection.
doppler_boost      O(β) aberration+modulation kernel → R_σ^{boost}.
teff_mes_bounds    Two-layer R_σ, R_ω, R_u̇ combined corrections plus F
                   invariance breakdown and VN-04 cross-check scenarios.

Migrated from legacy/bass/bass/forward (v8.3.0). Non-perturbative tilt
(sinh β, cosh β) is preserved throughout; the Θ(ê) angular expansion is
independent of the β evolution and uses (A, Q) as its closure parameters.
"""
from bass.forward.teff_forward import (
    TeffBianchiForward,
    theta4_coefficients,
    theta4_coefficients_vec,
    monopole_gauge_check,
)
from bass.forward.teff_backward import (
    teff_backward_linear,
    teff_backward_lsq,
    teff_backward_projection,
    TeffBianchiBackward,
)
from bass.forward.doppler_boost import (
    DopplerBoostCorrection,
    analytical_c1,
    delta_eps_boost,
)
from bass.forward.teff_mes_bounds import (
    TeffMESBounds,
    VN04_SCENARIOS,
)
from bass.forward.ver2_solver_output import (
    BassReleaseMetadata,
    build_solver_core_output,
    build_solver_core_output_from_native_result,
    build_solver_core_output_from_lowell_result,
    solver_core_output_from_payload,
    solver_core_output_to_payload,
)

__all__ = [
    # Forward
    'TeffBianchiForward',
    'theta4_coefficients',
    'theta4_coefficients_vec',
    'monopole_gauge_check',
    # Backward (new in bass_py)
    'teff_backward_linear',
    'teff_backward_lsq',
    'teff_backward_projection',
    'TeffBianchiBackward',
    # Doppler boost
    'DopplerBoostCorrection',
    'analytical_c1',
    'delta_eps_boost',
    # MES bounds
    'TeffMESBounds',
    'VN04_SCENARIOS',
    # VER2 S3 solver output
    'BassReleaseMetadata',
    'build_solver_core_output',
    'build_solver_core_output_from_native_result',
    'build_solver_core_output_from_lowell_result',
    'solver_core_output_to_payload',
    'solver_core_output_from_payload',
]
