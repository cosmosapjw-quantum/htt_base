"""VER2 anisotropic source-propagator surfaces for the BASS S3 lane."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from bass.background.bianchi_types import StructureConstants
from bass.runtime.ver2_execution import FeatureStatus
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator
from bass.spectrum.off_diagonal_covariance import assemble_bianchi_spectrum_covariance

__all__ = [
    "PropagatorMode",
    "ObserverFrameMetadata",
    "SourcePropagatorConfig",
    "SourcePropagator",
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
    return SourcePropagator(
        config=config,
        transfer_bundle=transfer_bundle,
        covariance_bundle=covariance_bundle,
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
