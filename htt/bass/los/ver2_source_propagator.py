"""VER2 anisotropic source-propagator surfaces for the BASS S3 lane."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from bass.background.bianchi_types import StructureConstants
from bass.runtime.ver2_execution import FeatureStatus
from bass.spectrum.lowell_los import (
    apply_type_ii_nilpotent_transfer_coupling,
    apply_type_iii_hyperbolic_transfer_coupling,
    apply_type_iv_solvable_transfer_coupling,
    apply_type_v_open_hyperbolic_transfer_envelope,
    apply_type_vi0_directional_transfer_coupling,
    apply_type_vih_negative_h_transfer_coupling,
    apply_type_viih_open_helical_transfer_rotation,
    apply_type_viii_sl2r_noncompact_transfer_coupling,
    apply_type_vii0_helical_transfer_rotation,
    apply_type_ix_compact_su2_transfer_coupling,
    build_lowell_line_of_sight_propagator,
)
from bass.spectrum.off_diagonal_covariance import assemble_bianchi_spectrum_covariance

__all__ = [
    "PropagatorMode",
    "ObserverFrameMetadata",
    "SourcePropagatorConfig",
    "SourcePropagator",
    "PropagatorEvidence",
    "propagator_evidence_for_config",
    "assert_publication_ready_propagator",
    "select_propagator_kernel_family",
    "build_source_propagator",
    "SourcePropagatorStub",
    "build_source_propagator_stub",
]


class PropagatorMode(str, Enum):
    """Declared source-to-observer propagator mode."""

    ANISOTROPIC_FORWARD = "anisotropic_forward"
    ANISOTROPIC_ADJOINT = "anisotropic_adjoint"
    FLRW_VALIDATION = "flrw_validation"


@dataclass(frozen=True)
class PropagatorEvidence:
    """Machine-readable LoS exactness and claim-readiness evidence.

    A propagator can be executable without being a publication-grade
    anisotropic transport owner. This object makes that distinction
    explicit at the point where the source-to-observer kernel is built.
    """

    family: str
    kernel_family: str
    mode: PropagatorMode
    temperature_transport: str
    polarization_rotation: str
    exactness: str
    output_claim_allowed: bool
    statistics_claim_allowed: bool
    block_reason: str | None = None

    def as_payload(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "kernel_family": self.kernel_family,
            "mode": self.mode.value,
            "temperature_transport": self.temperature_transport,
            "polarization_rotation": self.polarization_rotation,
            "exactness": self.exactness,
            "output_claim_allowed": bool(self.output_claim_allowed),
            "statistics_claim_allowed": bool(self.statistics_claim_allowed),
            "block_reason": self.block_reason,
        }


@dataclass(frozen=True)
class ObserverFrameMetadata:
    """Observer-frame and convention metadata for neutral exports."""

    observer_frame: str = "normal_tetrad"
    screen_basis_convention: str = "explicit_screen_basis"
    harmonic_basis: str = "spin_weighted_or_pstf_explicit"
    eb_sign_convention: str = "explicit_solver_state"

    def __post_init__(self) -> None:
        if not self.observer_frame:
            raise ValueError("observer_frame must be non-empty")
        if not self.screen_basis_convention:
            raise ValueError("screen_basis_convention must be non-empty")
        if not self.harmonic_basis:
            raise ValueError("harmonic_basis must be non-empty")
        if not self.eb_sign_convention:
            raise ValueError("eb_sign_convention must be non-empty")


@dataclass(frozen=True)
class SourcePropagatorConfig:
    """Anisotropic propagator policy and metadata."""

    mode: PropagatorMode
    temperature_transport: FeatureStatus
    polarization_rotation: FeatureStatus
    flrw_validation_only: bool = False
    kernel_family: str = "anisotropic_green_function"
    carries_statistics: bool = False
    observer_frame: ObserverFrameMetadata = field(default_factory=ObserverFrameMetadata)

    def __post_init__(self) -> None:
        if self.carries_statistics:
            raise ValueError("BASS propagators must remain observer-neutral")
        if self.mode is PropagatorMode.FLRW_VALIDATION:
            if not self.flrw_validation_only:
                raise ValueError(
                    "FLRW validation mode must set flrw_validation_only=True"
                )
            if self.kernel_family != "flrw_scalar_validation":
                raise ValueError(
                    "FLRW validation mode must use the explicit validation kernel family"
                )
        else:
            if self.flrw_validation_only:
                raise ValueError(
                    "FLRW scalar kernels are allowed only in explicit validation mode"
                )
            if self.kernel_family == "flrw_scalar_validation":
                raise ValueError(
                    "production propagators may not use the FLRW validation kernel family"
                )


@dataclass(frozen=True)
class SourcePropagator:
    """Executable observer-neutral source-to-observer propagator bundle."""

    config: SourcePropagatorConfig
    transfer_bundle: Mapping[str, object]
    covariance_bundle: Mapping[str, object]
    evidence: Mapping[str, object] = field(default_factory=dict)
    ready: bool = True
    observer_neutral: bool = True
    mode_coupling_expected: bool = True

    def __post_init__(self) -> None:
        if not self.ready:
            raise ValueError("SourcePropagator must be ready=True")
        if not self.observer_neutral:
            raise ValueError("BASS propagators must remain observer-neutral")
        if self.config.mode is PropagatorMode.FLRW_VALIDATION and self.mode_coupling_expected:
            raise ValueError("FLRW validation mode should not advertise anisotropic mode coupling")
        transfer_T = np.asarray(self.transfer_bundle["transfer_T"], dtype=np.float64)
        transfer_E = np.asarray(self.transfer_bundle["transfer_E"], dtype=np.float64)
        transfer_B = np.asarray(self.transfer_bundle["transfer_B"], dtype=np.float64)
        if transfer_T.ndim != 3 or transfer_E.shape != transfer_T.shape or transfer_B.shape != transfer_T.shape:
            raise ValueError("transfer bundles must expose matching 3-D T/E/B arrays")
        ell = np.asarray(self.covariance_bundle["ell"], dtype=np.int64)
        if transfer_T.shape[1] != ell.size:
            raise ValueError("transfer/covariance ell dimensions must agree")
        object.__setattr__(self, "evidence", dict(self.evidence))


@dataclass(frozen=True)
class SourcePropagatorStub:
    """Non-executable propagator shell for later runtime binding."""

    config: SourcePropagatorConfig
    ready: bool = False
    observer_neutral: bool = True
    mode_coupling_expected: bool = True
    reason: str = (
        "The S3 packet freezes anisotropic source-to-observer metadata only; "
        "live propagator numerics remain a later implementation task."
    )

    def __post_init__(self) -> None:
        if not self.observer_neutral:
            raise ValueError("propagator shell must remain observer-neutral")
        if self.config.mode is PropagatorMode.FLRW_VALIDATION and self.mode_coupling_expected:
            raise ValueError("FLRW validation mode should not advertise anisotropic mode coupling")


_TYPEI_MODE_LABELS = ("m0", "m+2", "m-2")
_TYPEI_MODE_SUFFIXES = {
    "m0": ("_m0", ""),
    "m+2": ("_m_plus2", "_m2", "_plus2"),
    "m-2": ("_m_minus2", "_mneg2", "_minus2"),
}
_NON_TYPE_I_KERNEL_FAMILIES = frozenset(
    {
        "class_a_axis_matrix_approx",
        "class_a_helical_matrix_approx",
        "class_a_semisimple_matrix_approx",
        "class_a_compact_matrix_approx",
        "class_b_open_matrix_approx",
        "class_b_twist_axis_matrix_approx",
        "class_b_helical_matrix_approx",
        "type_vii0_helical_projection",
        "type_v_open_hyperbolic_projection",
        "type_ii_nilpotent_projection",
        "type_iii_hyperbolic_projection",
        "type_iv_solvable_projection",
        "type_vi0_directional_projection",
        "type_vih_negative_h_projection",
        "type_viih_open_helical_projection",
        "type_viii_sl2r_noncompact_projection",
        "type_ix_compact_su2_projection",
    }
)


def propagator_evidence_for_config(
    config: SourcePropagatorConfig,
    *,
    structure: StructureConstants,
) -> PropagatorEvidence:
    """Classify a propagator config against the supplied family structure.

    This is intentionally stricter than "can execute": approximate
    algebra-aware kernels can support diagnostic output, but they do not
    open exact non-FLRW publication or statistics claims.
    """

    family = str(structure.label)
    kernel = str(config.kernel_family)
    temp_status = str(config.temperature_transport.value)
    pol_status = str(config.polarization_rotation.value)
    if config.mode is PropagatorMode.FLRW_VALIDATION:
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="flrw_scalar_validation_only",
            output_claim_allowed=False,
            statistics_claim_allowed=False,
            block_reason="FLRW validation kernels are recovery tests, not non-FLRW production propagators",
        )
    if (
        family == "I"
        and kernel == "bianchi_i_matrix_exact"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.DISABLED
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="exact_type_i_matrix",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason="exact Type-I transport is output-ready but statistics still require the fitting gate",
        )
    if (
        family == "VII_0"
        and kernel == "type_vii0_helical_projection"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.EXACT
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="type_vii0_helical_projection_transport",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason=(
                "Type VII_0 helical low-ell transport is output-ready; "
                "statistics still require the fitting gate"
            ),
        )
    if (
        family == "II"
        and kernel == "type_ii_nilpotent_projection"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.EXACT
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="type_ii_nilpotent_projection_transport",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason=(
                "Type II nilpotent low-ell transport is output-ready; "
                "statistics still require the fitting gate"
            ),
        )
    if (
        family == "V"
        and kernel == "type_v_open_hyperbolic_projection"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.DISABLED
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="type_v_open_hyperbolic_projection_transport",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason=(
                "Type V open-hyperbolic low-ell transport is output-ready; "
                "statistics still require the fitting gate"
            ),
        )
    if (
        family == "VI_0"
        and kernel == "type_vi0_directional_projection"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.EXACT
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="type_vi0_directional_projection_transport",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason=(
                "Type VI_0 directional low-ell transport is output-ready; "
                "statistics still require the fitting gate"
            ),
        )
    if (
        family == "VI_h"
        and kernel == "type_vih_negative_h_projection"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.EXACT
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="type_vih_negative_h_projection_transport",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason=(
                "Type VI_h negative-h low-ell transport is output-ready; "
                "statistics still require the fitting gate"
            ),
        )
    if (
        family == "III"
        and kernel == "type_iii_hyperbolic_projection"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.EXACT
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="type_iii_hyperbolic_projection_transport",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason=(
                "Type III hyperbolic h=-1 low-ell transport is output-ready; "
                "statistics still require the fitting gate"
            ),
        )
    if (
        family == "IV"
        and kernel == "type_iv_solvable_projection"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.EXACT
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="type_iv_solvable_projection_transport",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason=(
                "Type IV solvable low-ell transport is output-ready; "
                "statistics still require the fitting gate"
            ),
        )
    if (
        family == "VII_h"
        and kernel == "type_viih_open_helical_projection"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.EXACT
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="type_viih_open_helical_projection_transport",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason=(
                "Type VII_h open-helical low-ell transport is output-ready; "
                "statistics still require the fitting gate"
            ),
        )
    if (
        family == "VIII"
        and kernel == "type_viii_sl2r_noncompact_projection"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.EXACT
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="type_viii_sl2r_noncompact_projection_transport",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason=(
                "Type VIII SL(2,R) noncompact low-ell transport is output-ready; "
                "statistics still require the fitting gate"
            ),
        )
    if (
        family == "IX"
        and kernel == "type_ix_compact_su2_projection"
        and config.temperature_transport is FeatureStatus.EXACT
        and config.polarization_rotation is FeatureStatus.EXACT
    ):
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="type_ix_compact_su2_projection_transport",
            output_claim_allowed=True,
            statistics_claim_allowed=False,
            block_reason=(
                "Type IX compact-SU(2) low-ell transport is output-ready; "
                "statistics still require the fitting gate"
            ),
        )
    if kernel in _NON_TYPE_I_KERNEL_FAMILIES:
        return PropagatorEvidence(
            family=family,
            kernel_family=kernel,
            mode=config.mode,
            temperature_transport=temp_status,
            polarization_rotation=pol_status,
            exactness="algebraic_proxy_family_kernel",
            output_claim_allowed=False,
            statistics_claim_allowed=False,
            block_reason=(
                "non-Type-I propagator is an executable algebra-aware proxy; "
                "full family-specific collocation/Wigner transport evidence is not present"
            ),
        )
    return PropagatorEvidence(
        family=family,
        kernel_family=kernel,
        mode=config.mode,
        temperature_transport=temp_status,
        polarization_rotation=pol_status,
        exactness="unclassified_kernel",
        output_claim_allowed=False,
        statistics_claim_allowed=False,
        block_reason="propagator kernel is not classified as publication-ready",
    )


def assert_publication_ready_propagator(
    config: SourcePropagatorConfig,
    *,
    structure: StructureConstants,
) -> PropagatorEvidence:
    """Return evidence or raise when a propagator is not claim-ready."""

    evidence = propagator_evidence_for_config(config, structure=structure)
    if not evidence.output_claim_allowed:
        raise ValueError(
            "propagator is not publication-output-ready: "
            f"{evidence.block_reason}"
        )
    return evidence


def _source_sample_scalar(sample: Mapping[str, object], names: tuple[str, ...]) -> float:
    for name in names:
        if name in sample:
            value = np.asarray(sample[name], dtype=float)
            if value.ndim != 0:
                raise ValueError(f"source_builder key {name!r} must map to a scalar")
            return float(value)
    return 0.0


def _source_mode_aliases(base: str, mode: str, *, include_generic: bool) -> tuple[str, ...]:
    suffixes = _TYPEI_MODE_SUFFIXES[mode]
    aliases = [f"{base}{suffix}" for suffix in suffixes if suffix]
    if mode == "m0" or include_generic:
        aliases.append(base)
    return tuple(aliases)


def _interp_eta_callable(eta_grid: np.ndarray, values: np.ndarray):
    eta = np.asarray(eta_grid, dtype=np.float64)
    series = np.asarray(values, dtype=np.float64)

    def fn(eval_eta):
        query = np.asarray(eval_eta, dtype=np.float64)
        out = np.interp(query, eta, series)
        if np.ndim(out) == 0:
            return float(out)
        return np.asarray(out, dtype=np.float64)

    return fn


def select_propagator_kernel_family(structure: StructureConstants) -> str:
    """Select the bounded non-Type-I family from algebra data alone."""
    if structure.label == "I":
        return "bianchi_i_matrix_exact"
    if structure.label == "II":
        return "type_ii_nilpotent_projection"
    if structure.label == "III":
        return "type_iii_hyperbolic_projection"
    if structure.label == "IV":
        return "type_iv_solvable_projection"
    if structure.label == "V":
        return "type_v_open_hyperbolic_projection"
    if structure.label == "VI_0":
        return "type_vi0_directional_projection"
    if structure.label == "VI_h":
        return "type_vih_negative_h_projection"
    if structure.label == "VII_0":
        return "type_vii0_helical_projection"
    if structure.label == "VII_h":
        return "type_viih_open_helical_projection"
    if structure.label == "VIII":
        return "type_viii_sl2r_noncompact_projection"
    if structure.label == "IX":
        return "type_ix_compact_su2_projection"
    n_diag = np.asarray(structure.n_diag, dtype=np.float64)
    zero_count = int(np.count_nonzero(np.isclose(n_diag, 0.0, atol=1.0e-15)))
    positive = int(np.count_nonzero(n_diag > 0.0))
    negative = int(np.count_nonzero(n_diag < 0.0))
    if structure.is_class_a:
        if zero_count == 1 and positive == 2:
            return "class_a_helical_matrix_approx"
        if zero_count == 0 and positive == 3:
            return "class_a_compact_matrix_approx"
        if zero_count == 0 and positive == 2 and negative == 1:
            return "class_a_semisimple_matrix_approx"
        return "class_a_axis_matrix_approx"
    if zero_count == 3:
        return "class_b_open_matrix_approx"
    if float(structure.n1) * float(structure.n3) > 0.0:
        return "class_b_helical_matrix_approx"
    return "class_b_twist_axis_matrix_approx"


def _kernel_family_modifiers(kernel_family: str) -> dict[str, float]:
    table = {
        "class_a_axis_matrix_approx": {
            "anisotropy_scale": 1.00,
            "rotation_scale": 0.00,
            "ell_slope": 0.018,
            "bmix_scale": 0.00,
        },
        "type_ii_nilpotent_projection": {
            "anisotropy_scale": 1.00,
            "rotation_scale": 0.00,
            "ell_slope": 0.018,
            "bmix_scale": 0.00,
        },
        "type_iii_hyperbolic_projection": {
            "anisotropy_scale": 1.02,
            "rotation_scale": 0.80,
            "ell_slope": 0.021,
            "bmix_scale": 0.80,
        },
        "type_iv_solvable_projection": {
            "anisotropy_scale": 1.06,
            "rotation_scale": 0.70,
            "ell_slope": 0.023,
            "bmix_scale": 0.70,
        },
        "type_v_open_hyperbolic_projection": {
            "anisotropy_scale": 0.00,
            "rotation_scale": 0.00,
            "ell_slope": 0.000,
            "bmix_scale": 0.00,
        },
        "type_vi0_directional_projection": {
            "anisotropy_scale": 1.00,
            "rotation_scale": 0.00,
            "ell_slope": 0.020,
            "bmix_scale": 0.00,
        },
        "type_vih_negative_h_projection": {
            "anisotropy_scale": 1.04,
            "rotation_scale": 0.76,
            "ell_slope": 0.023,
            "bmix_scale": 0.72,
        },
        "type_vii0_helical_projection": {
            "anisotropy_scale": 1.05,
            "rotation_scale": 0.08,
            "ell_slope": 0.022,
            "bmix_scale": 0.08,
        },
        "type_viih_open_helical_projection": {
            "anisotropy_scale": 1.08,
            "rotation_scale": 1.12,
            "ell_slope": 0.024,
            "bmix_scale": 1.10,
        },
        "type_viii_sl2r_noncompact_projection": {
            "anisotropy_scale": 1.14,
            "rotation_scale": 0.92,
            "ell_slope": 0.026,
            "bmix_scale": 0.88,
        },
        "type_ix_compact_su2_projection": {
            "anisotropy_scale": 0.00,
            "rotation_scale": 0.00,
            "ell_slope": 0.000,
            "bmix_scale": 0.00,
        },
        "class_a_helical_matrix_approx": {
            "anisotropy_scale": 1.05,
            "rotation_scale": 0.08,
            "ell_slope": 0.022,
            "bmix_scale": 0.08,
        },
        "class_a_semisimple_matrix_approx": {
            "anisotropy_scale": 1.12,
            "rotation_scale": 0.14,
            "ell_slope": 0.026,
            "bmix_scale": 0.14,
        },
        "class_a_compact_matrix_approx": {
            "anisotropy_scale": 1.18,
            "rotation_scale": 0.18,
            "ell_slope": 0.028,
            "bmix_scale": 0.18,
        },
        "class_b_open_matrix_approx": {
            "anisotropy_scale": 0.95,
            "rotation_scale": 0.00,
            "ell_slope": 0.018,
            "bmix_scale": 0.00,
        },
        "class_b_twist_axis_matrix_approx": {
            "anisotropy_scale": 1.04,
            "rotation_scale": 1.00,
            "ell_slope": 0.022,
            "bmix_scale": 1.00,
        },
        "class_b_helical_matrix_approx": {
            "anisotropy_scale": 1.08,
            "rotation_scale": 1.12,
            "ell_slope": 0.024,
            "bmix_scale": 1.10,
        },
    }
    if kernel_family not in table:
        raise ValueError(f"unsupported kernel_family {kernel_family!r}")
    return table[kernel_family]


def _structure_features(
    structure: StructureConstants,
    *,
    kernel_family: str,
) -> dict[str, object]:
    raw_axis = np.array(
        [
            structure.n1 - structure.n3,
            structure.a_twist,
            structure.trace_n + (1.0 if structure.label == "IX" else 0.0),
        ],
        dtype=np.float64,
    )
    axis_norm = float(np.linalg.norm(raw_axis))
    preferred_axis = (
        raw_axis / axis_norm
        if axis_norm > 1.0e-30 and np.all(np.isfinite(raw_axis))
        else np.array([0.0, 0.0, 1.0], dtype=np.float64)
    )

    geom_norm = (
        abs(float(structure.n1))
        + abs(float(structure.n2))
        + abs(float(structure.n3))
        + abs(float(structure.a_twist))
    )
    h_abs = abs(float(structure.h_parameter))
    modifiers = _kernel_family_modifiers(kernel_family)
    anisotropy_strength = min(
        0.35,
        modifiers["anisotropy_scale"] * (8.0 * geom_norm + 0.05 * h_abs),
    )
    if structure.no_flrw_limit:
        anisotropy_strength = max(anisotropy_strength, 0.08)
    if structure.label == "I":
        anisotropy_strength = 0.0

    rotation_strength = 0.0
    if modifiers["rotation_scale"] > 0.0:
        rotation_strength = min(
            0.30,
            modifiers["rotation_scale"]
            * (
                0.45 * anisotropy_strength
                + 6.0 * abs(float(structure.a_twist))
                + (0.03 if kernel_family in {"class_b_helical_matrix_approx", "class_a_compact_matrix_approx"} else 0.0)
            ),
        )

    if (not structure.no_flrw_limit) and anisotropy_strength < 1.0e-4:
        rotation_strength = 0.0

    return {
        "preferred_axis": preferred_axis,
        "anisotropy_strength": anisotropy_strength,
        "rotation_strength": rotation_strength,
    }


def _mode_coupling_matrix(
    *,
    preferred_axis: np.ndarray,
    anisotropy_strength: float,
) -> np.ndarray:
    if anisotropy_strength <= 0.0:
        return np.eye(3, dtype=np.float64)
    axis_x, axis_y, axis_z = np.asarray(preferred_axis, dtype=np.float64)
    return np.array(
        [
            [
                1.0,
                0.15 * anisotropy_strength * axis_z,
                -0.15 * anisotropy_strength * axis_z,
            ],
            [
                0.10 * anisotropy_strength * axis_x,
                1.0 + 0.25 * anisotropy_strength,
                0.05 * anisotropy_strength * axis_y,
            ],
            [
                -0.10 * anisotropy_strength * axis_x,
                -0.05 * anisotropy_strength * axis_y,
                1.0 - 0.25 * anisotropy_strength,
            ],
        ],
        dtype=np.float64,
    )


def _build_type_i_matrix_transfer_bundle(
    structure: StructureConstants,
    *,
    eta_grid_mpc: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell_max: int,
    visibility_fn: Callable[[float], float],
    source_builder: Callable[[float, float], Mapping[str, object]],
) -> dict[str, object]:
    from bass.los.bianchi_propagator import (
        BianchiProjectorConfig,
        BianchiSourceTerms,
        matrix_propagator_m0_m2,
    )
    from bass.los.flrw_bessel_projector import FLRWSourceTerms

    eta_grid = np.asarray(eta_grid_mpc, dtype=np.float64)
    k_grid = np.asarray(k_grid_mpc, dtype=np.float64)
    visibility = np.asarray([float(visibility_fn(float(eta))) for eta in eta_grid], dtype=np.float64)
    if np.any(~np.isfinite(visibility)):
        raise ValueError("visibility_fn returned non-finite values")

    transfer_T = np.zeros((k_grid.size, ell_max + 1, 3), dtype=np.float64)
    transfer_E = np.zeros_like(transfer_T)
    transfer_B = np.zeros_like(transfer_T)
    propagator_matrix = np.repeat(
        np.eye(3, dtype=np.float64)[None, None, :, :],
        k_grid.size * (ell_max + 1),
        axis=0,
    ).reshape(k_grid.size, ell_max + 1, 3, 3)
    projector_config = BianchiProjectorConfig(
        ell_max=int(ell_max),
        eta_0_mpc=float(eta_grid[-1]),
    )
    visibility_g = _interp_eta_callable(eta_grid, visibility)

    for ik, k in enumerate(k_grid):
        samples = [source_builder(float(eta), float(k)) for eta in eta_grid]
        if not all(isinstance(sample, Mapping) for sample in samples):
            raise TypeError("source_builder must return a mapping for each (eta, k)")
        if any(
            any(
                key == base or key.startswith(f"{base}_")
                for base in ("temperature", "polarization", "b_mode")
                for key in sample
            )
            for sample in samples
        ):
            raise ValueError(
                "bianchi_i_matrix_exact requires decomposed LOS ingredients; "
                "direct assembled temperature/polarization sources must use the proxy backend"
            )

        kappa = np.asarray(
            [
                _source_sample_scalar(sample, ("kappa", "optical_depth"))
                for sample in samples
            ],
            dtype=np.float64,
        )
        kappa_of_eta = _interp_eta_callable(eta_grid, kappa)

        def build_mode_source(mode: str) -> FLRWSourceTerms:
            include_generic = mode != "m0"
            theta_0 = np.asarray(
                [
                    _source_sample_scalar(sample, _source_mode_aliases("theta_0", mode, include_generic=include_generic))
                    for sample in samples
                ],
                dtype=np.float64,
            )
            psi = np.asarray(
                [
                    _source_sample_scalar(sample, _source_mode_aliases("psi", mode, include_generic=include_generic))
                    for sample in samples
                ],
                dtype=np.float64,
            )
            pi = np.asarray(
                [
                    _source_sample_scalar(sample, _source_mode_aliases("pi", mode, include_generic=include_generic))
                    for sample in samples
                ],
                dtype=np.float64,
            )
            isw = np.asarray(
                [
                    _source_sample_scalar(
                        sample,
                        _source_mode_aliases("phi_dot_plus_psi_dot", mode, include_generic=include_generic),
                    )
                    for sample in samples
                ],
                dtype=np.float64,
            )
            v_b = np.asarray(
                [
                    _source_sample_scalar(sample, _source_mode_aliases("v_b", mode, include_generic=include_generic))
                    for sample in samples
                ],
                dtype=np.float64,
            )
            return FLRWSourceTerms(
                theta_0=_interp_eta_callable(eta_grid, theta_0),
                psi=_interp_eta_callable(eta_grid, psi),
                phi_dot_plus_psi_dot=_interp_eta_callable(eta_grid, isw),
                v_b=_interp_eta_callable(eta_grid, v_b),
                pi=_interp_eta_callable(eta_grid, pi),
            )

        tf = matrix_propagator_m0_m2(
            float(k),
            1.0,
            BianchiSourceTerms(
                sources_m0=build_mode_source("m0"),
                sources_m_plus2=build_mode_source("m+2"),
                sources_m_minus2=build_mode_source("m-2"),
            ),
            visibility_g,
            kappa_of_eta,
            eta_grid,
            projector_config,
        )
        transfer_T[ik, :, 0] = tf.delta_T_m0
        transfer_T[ik, :, 1] = tf.delta_T_m_plus2
        transfer_T[ik, :, 2] = tf.delta_T_m_minus2
        transfer_E[ik, :, 0] = tf.delta_E_m0
        transfer_E[ik, :, 1] = tf.delta_E_m_plus2
        transfer_E[ik, :, 2] = tf.delta_E_m_minus2
        transfer_B[ik, :, 0] = tf.delta_B_all_zero
        transfer_B[ik, :, 1] = tf.delta_B_all_zero
        transfer_B[ik, :, 2] = tf.delta_B_all_zero

    return {
        "structure": structure,
        "structure_label": structure.label,
        "mode_labels": _TYPEI_MODE_LABELS,
        "ell": np.arange(ell_max + 1, dtype=int),
        "eta_grid_mpc": eta_grid.copy(),
        "eta_0_mpc": float(eta_grid[-1]),
        "k_grid_mpc": k_grid.copy(),
        "visibility": visibility,
        "transfer_T": transfer_T,
        "transfer_E": transfer_E,
        "transfer_B": transfer_B,
        "raw_transfer_T": transfer_T.copy(),
        "raw_transfer_E": transfer_E.copy(),
        "raw_transfer_B": transfer_B.copy(),
        "propagator_matrix": propagator_matrix,
        "mode_coupling_matrix": np.eye(3, dtype=np.float64),
        "preferred_axis": np.array([0.0, 0.0, 1.0], dtype=np.float64),
        "anisotropy_strength": 0.0,
        "rotation_strength": 0.0,
    }


def _build_non_type_i_matrix_transfer_bundle(
    structure: StructureConstants,
    *,
    kernel_family: str,
    eta_grid_mpc: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell_max: int,
    visibility_fn: Callable[[float], float],
    source_builder: Callable[[float, float], Mapping[str, object]],
) -> dict[str, object]:
    base_bundle = _build_type_i_matrix_transfer_bundle(
        structure,
        eta_grid_mpc=eta_grid_mpc,
        k_grid_mpc=k_grid_mpc,
        ell_max=ell_max,
        visibility_fn=visibility_fn,
        source_builder=source_builder,
    )
    features = _structure_features(structure, kernel_family=kernel_family)
    modifiers = _kernel_family_modifiers(kernel_family)
    preferred_axis = np.asarray(features["preferred_axis"], dtype=np.float64)
    anisotropy_strength = float(features["anisotropy_strength"])
    rotation_strength = float(features["rotation_strength"])
    mode_coupling = _mode_coupling_matrix(
        preferred_axis=preferred_axis,
        anisotropy_strength=anisotropy_strength,
    )

    raw_transfer_T = np.asarray(base_bundle["raw_transfer_T"], dtype=np.float64)
    raw_transfer_E = np.asarray(base_bundle["raw_transfer_E"], dtype=np.float64)
    raw_transfer_B = np.asarray(base_bundle["raw_transfer_B"], dtype=np.float64)
    nil_metadata: dict[str, object] = {}
    typeiii_metadata: dict[str, object] = {}
    typeiv_metadata: dict[str, object] = {}
    typev_metadata: dict[str, object] = {}
    vi0_metadata: dict[str, object] = {}
    vih_metadata: dict[str, object] = {}
    viih_metadata: dict[str, object] = {}
    typeviii_metadata: dict[str, object] = {}
    typeix_metadata: dict[str, object] = {}
    helical_metadata: dict[str, object] = {}
    if structure.label == "II":
        raw_transfer_T, raw_transfer_E, raw_transfer_B, nil_metadata = (
            apply_type_ii_nilpotent_transfer_coupling(
                structure,
                transfer_T=raw_transfer_T,
                transfer_E=raw_transfer_E,
                transfer_B=raw_transfer_B,
                k_grid_mpc=k_grid_mpc,
                ell=np.arange(raw_transfer_T.shape[1], dtype=np.float64),
                eta_grid_mpc=eta_grid_mpc,
            )
        )
    if structure.label == "III":
        raw_transfer_T, raw_transfer_E, raw_transfer_B, typeiii_metadata = (
            apply_type_iii_hyperbolic_transfer_coupling(
                structure,
                transfer_T=raw_transfer_T,
                transfer_E=raw_transfer_E,
                transfer_B=raw_transfer_B,
                k_grid_mpc=k_grid_mpc,
                ell=np.arange(raw_transfer_T.shape[1], dtype=np.float64),
                eta_grid_mpc=eta_grid_mpc,
            )
        )
    if structure.label == "IV":
        raw_transfer_T, raw_transfer_E, raw_transfer_B, typeiv_metadata = (
            apply_type_iv_solvable_transfer_coupling(
                structure,
                transfer_T=raw_transfer_T,
                transfer_E=raw_transfer_E,
                transfer_B=raw_transfer_B,
                k_grid_mpc=k_grid_mpc,
                ell=np.arange(raw_transfer_T.shape[1], dtype=np.float64),
                eta_grid_mpc=eta_grid_mpc,
            )
        )
    if structure.label == "V":
        raw_transfer_T, raw_transfer_E, raw_transfer_B, typev_metadata = (
            apply_type_v_open_hyperbolic_transfer_envelope(
                structure,
                transfer_T=raw_transfer_T,
                transfer_E=raw_transfer_E,
                transfer_B=raw_transfer_B,
                k_grid_mpc=k_grid_mpc,
            )
        )
        mode_coupling = np.eye(3, dtype=np.float64)
        anisotropy_strength = 0.0
        rotation_strength = 0.0
    if structure.label == "VI_0":
        raw_transfer_T, raw_transfer_E, raw_transfer_B, vi0_metadata = (
            apply_type_vi0_directional_transfer_coupling(
                structure,
                transfer_T=raw_transfer_T,
                transfer_E=raw_transfer_E,
                transfer_B=raw_transfer_B,
                k_grid_mpc=k_grid_mpc,
                ell=np.arange(raw_transfer_T.shape[1], dtype=np.float64),
                eta_grid_mpc=eta_grid_mpc,
            )
        )
    if structure.label == "VI_h":
        raw_transfer_T, raw_transfer_E, raw_transfer_B, vih_metadata = (
            apply_type_vih_negative_h_transfer_coupling(
                structure,
                transfer_T=raw_transfer_T,
                transfer_E=raw_transfer_E,
                transfer_B=raw_transfer_B,
                k_grid_mpc=k_grid_mpc,
                ell=np.arange(raw_transfer_T.shape[1], dtype=np.float64),
                eta_grid_mpc=eta_grid_mpc,
            )
        )
    if structure.label == "VII_h":
        raw_transfer_T, raw_transfer_E, raw_transfer_B, viih_metadata = (
            apply_type_viih_open_helical_transfer_rotation(
                structure,
                transfer_T=raw_transfer_T,
                transfer_E=raw_transfer_E,
                transfer_B=raw_transfer_B,
                k_grid_mpc=k_grid_mpc,
                ell=np.arange(raw_transfer_T.shape[1], dtype=np.float64),
                eta_grid_mpc=eta_grid_mpc,
            )
        )
    if structure.label == "VIII":
        raw_transfer_T, raw_transfer_E, raw_transfer_B, typeviii_metadata = (
            apply_type_viii_sl2r_noncompact_transfer_coupling(
                structure,
                transfer_T=raw_transfer_T,
                transfer_E=raw_transfer_E,
                transfer_B=raw_transfer_B,
                k_grid_mpc=k_grid_mpc,
                ell=np.arange(raw_transfer_T.shape[1], dtype=np.float64),
                eta_grid_mpc=eta_grid_mpc,
            )
        )
    if structure.label == "VII_0":
        raw_transfer_T, raw_transfer_E, raw_transfer_B, helical_metadata = (
            apply_type_vii0_helical_transfer_rotation(
                structure,
                transfer_T=raw_transfer_T,
                transfer_E=raw_transfer_E,
                transfer_B=raw_transfer_B,
                k_grid_mpc=k_grid_mpc,
                ell=np.arange(raw_transfer_T.shape[1], dtype=np.float64),
                eta_grid_mpc=eta_grid_mpc,
            )
        )
    if structure.label == "IX":
        raw_transfer_T, raw_transfer_E, raw_transfer_B, typeix_metadata = (
            apply_type_ix_compact_su2_transfer_coupling(
                structure,
                transfer_T=raw_transfer_T,
                transfer_E=raw_transfer_E,
                transfer_B=raw_transfer_B,
                k_grid_mpc=k_grid_mpc,
                ell=np.arange(raw_transfer_T.shape[1], dtype=np.float64),
                eta_grid_mpc=eta_grid_mpc,
            )
        )
        mode_coupling = np.eye(3, dtype=np.float64)
        anisotropy_strength = 0.0
        rotation_strength = 0.0
    transfer_T = np.zeros_like(raw_transfer_T)
    transfer_E = np.zeros_like(raw_transfer_E)
    transfer_B = np.zeros_like(raw_transfer_B)
    propagator_matrix = np.zeros(
        (raw_transfer_T.shape[0], raw_transfer_T.shape[1], 3, 3),
        dtype=np.float64,
    )
    ell_values = np.arange(raw_transfer_T.shape[1], dtype=np.float64)
    ell_weight = 1.0 + modifiers["ell_slope"] * anisotropy_strength * ell_values

    for ik in range(raw_transfer_T.shape[0]):
        for iell, weight in enumerate(ell_weight):
            propagator = float(weight) * mode_coupling
            propagator_matrix[ik, iell] = propagator
            mixed_T = propagator @ raw_transfer_T[ik, iell]
            mixed_E = propagator @ raw_transfer_E[ik, iell]
            rotation_drive = modifiers["bmix_scale"] * rotation_strength * np.array(
                [0.0, raw_transfer_E[ik, iell, 1], -raw_transfer_E[ik, iell, 2]],
                dtype=np.float64,
            )
            transfer_T[ik, iell] = mixed_T
            transfer_E[ik, iell] = mixed_E
            transfer_B[ik, iell] = propagator @ (raw_transfer_B[ik, iell] + rotation_drive)

    bundle = dict(base_bundle)
    bundle.update(
        {
            "transfer_T": transfer_T,
            "transfer_E": transfer_E,
            "transfer_B": transfer_B,
            "raw_transfer_T": raw_transfer_T,
            "raw_transfer_E": raw_transfer_E,
            "raw_transfer_B": raw_transfer_B,
            "propagator_matrix": propagator_matrix,
            "mode_coupling_matrix": mode_coupling,
            "preferred_axis": preferred_axis,
            "anisotropy_strength": anisotropy_strength,
            "rotation_strength": rotation_strength,
            **nil_metadata,
            **typeiii_metadata,
            **typeiv_metadata,
            **typev_metadata,
            **vi0_metadata,
            **vih_metadata,
            **viih_metadata,
            **typeviii_metadata,
            **typeix_metadata,
            **helical_metadata,
        }
    )
    return bundle


def build_source_propagator(
    config: SourcePropagatorConfig,
    *,
    structure: StructureConstants,
    eta_grid_mpc: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell_max: int,
    visibility_fn: Callable[[float], float],
    source_builder: Callable[[float, float], Mapping[str, object]],
    limber_eta_sp_sign: str = "integrator",
    off_diagonal_strategy: str = "m_decoupled_blocks",
) -> SourcePropagator:
    """Build the executable VER2 propagator from LOS and covariance operators.

    This is a bounded research-grade path: it remains observer-neutral and
    carries no posterior/statistical semantics, but it is now fully executable
    and no longer a shell-only placeholder.
    """
    eta_grid = np.asarray(eta_grid_mpc, dtype=np.float64)
    k_grid = np.asarray(k_grid_mpc, dtype=np.float64)
    evidence = propagator_evidence_for_config(config, structure=structure)
    if config.kernel_family == "bianchi_i_matrix_exact" and structure.label != "I":
        raise ValueError("bianchi_i_matrix_exact may only be used with Bianchi Type I")
    if structure.label == "I" and config.kernel_family == "bianchi_i_matrix_exact":
        transfer_bundle = _build_type_i_matrix_transfer_bundle(
            structure,
            eta_grid_mpc=eta_grid,
            k_grid_mpc=k_grid,
            ell_max=int(ell_max),
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
    elif config.kernel_family in _NON_TYPE_I_KERNEL_FAMILIES:
        if structure.label == "I":
            raise ValueError(
                f"{config.kernel_family} is reserved for non-Type-I structures"
            )
        transfer_bundle = _build_non_type_i_matrix_transfer_bundle(
            structure,
            kernel_family=config.kernel_family,
            eta_grid_mpc=eta_grid,
            k_grid_mpc=k_grid,
            ell_max=int(ell_max),
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
    else:
        transfer_bundle = build_lowell_line_of_sight_propagator(
            structure,
            eta_grid_mpc=eta_grid,
            k_grid_mpc=k_grid,
            ell_max=int(ell_max),
            visibility_fn=visibility_fn,
            source_builder=source_builder,
            limber_eta_sp_sign=limber_eta_sp_sign,  # type: ignore[arg-type]
        )
    covariance_bundle = assemble_bianchi_spectrum_covariance(
        transfer_bundle=transfer_bundle,
        k_grid_mpc=k_grid,
        ell_max=int(ell_max),
        off_diagonal_strategy=off_diagonal_strategy,  # type: ignore[arg-type]
    )
    transfer_bundle = dict(transfer_bundle)
    transfer_bundle.update(
        {
            "propagator_exactness": evidence.exactness,
            "publication_output_claim_allowed": bool(evidence.output_claim_allowed),
            "statistics_claim_allowed": bool(evidence.statistics_claim_allowed),
            "propagator_block_reason": evidence.block_reason,
            "propagator_evidence": evidence.as_payload(),
        }
    )
    return SourcePropagator(
        config=config,
        transfer_bundle=transfer_bundle,
        covariance_bundle=covariance_bundle,
        evidence=evidence.as_payload(),
        mode_coupling_expected=(config.mode is not PropagatorMode.FLRW_VALIDATION),
    )


def build_source_propagator_stub(
    config: SourcePropagatorConfig,
) -> SourcePropagatorStub:
    """Return the S3 propagator contract stub."""
    return SourcePropagatorStub(
        config=config,
        mode_coupling_expected=(config.mode is not PropagatorMode.FLRW_VALIDATION),
    )
