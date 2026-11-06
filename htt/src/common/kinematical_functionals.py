"""Typed physical kinematics, mixed functionals, and the local optical response.

This module is a source-independent state/functional kernel. It does not
construct a cosmological spacetime, evolve Einstein-matter equations, or
supply survey likelihoods. The local optical map is the explicitly scoped
leading-order common-congruence response; source selection, covariance,
finite-distance remainders, and the catalogue observation operator belong
to the likelihood layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .kinematic_response import STF_BASIS
from .r7_contracts import content_id, finite_array
from .relativistic_kinematics import (
    METRIC,
    kinematics_from_velocity_jet,
    unit_timelike,
)


_C0 = 299_792_458.0
_STF2_BASIS = np.array(STF_BASIS, dtype=np.float64, copy=True)
_STF2_BASIS.setflags(write=False)
_EPSILON = np.zeros((3, 3, 3), dtype=np.float64)
_EPSILON[0, 1, 2] = _EPSILON[1, 2, 0] = _EPSILON[2, 0, 1] = 1.0
_EPSILON[0, 2, 1] = _EPSILON[2, 1, 0] = _EPSILON[1, 0, 2] = -1.0
_EPSILON.setflags(write=False)


class KinematicalStateError(ValueError):
    """The supplied kinematical state violates its declared type/convention."""


def _nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KinematicalStateError(f"{name} must be a nonempty identity")
    return value


def _finite_scalar(value: float, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise KinematicalStateError(f"{name} must be a real scalar, not bool")
    result = float(value)
    if not np.isfinite(result):
        raise KinematicalStateError(f"{name} must be finite")
    return result


def _validate_stf2(value: np.ndarray, name: str = "sigma") -> np.ndarray:
    tensor = finite_array(value, shape=(3, 3), name=name)
    scale = max(float(np.linalg.norm(tensor)), np.finfo(float).tiny)
    tol = 256.0 * np.finfo(float).eps * scale
    if np.linalg.norm(tensor - tensor.T) > tol:
        raise KinematicalStateError(f"{name} must be symmetric")
    if abs(float(np.trace(tensor))) > tol:
        raise KinematicalStateError(f"{name} must be trace free")
    return tensor


def stf2_components(tensor: np.ndarray) -> np.ndarray:
    """Return orthonormal real STF2 coordinates in the shared R38/R39 basis."""
    sigma = _validate_stf2(tensor)
    return finite_array(np.einsum("aij,ij->a", _STF2_BASIS, sigma), shape=(5,))


def stf2_from_components(components: np.ndarray) -> np.ndarray:
    """Reconstruct the STF2 tensor from the registered orthonormal five-vector."""
    values = finite_array(components, shape=(5,), name="STF2 components")
    return finite_array(np.einsum("a,aij->ij", values, _STF2_BASIS), shape=(3, 3))


@dataclass(frozen=True)
class FrameTransport:
    """Explicit orthogonal component map between two declared spatial bases.

    matrix maps polar components in source_basis_id to polar components in
    target_basis_id. An improper map is allowed and its determinant is used
    when the caller transports an axial vector.
    """

    source_basis_id: str
    target_basis_id: str
    matrix: np.ndarray
    transport_id: str

    def __post_init__(self) -> None:
        _nonempty(self.source_basis_id, "source_basis_id")
        _nonempty(self.target_basis_id, "target_basis_id")
        _nonempty(self.transport_id, "transport_id")
        if self.source_basis_id == self.target_basis_id:
            raise KinematicalStateError("identity basis transport should not be registered")
        matrix = finite_array(self.matrix, shape=(3, 3), name="frame transport")
        residual = matrix @ matrix.T - np.eye(3)
        if np.linalg.norm(residual) > 512.0 * np.finfo(float).eps:
            raise KinematicalStateError("frame transport must be orthogonal")
        det = float(np.linalg.det(matrix))
        if not np.isclose(abs(det), 1.0, rtol=0.0, atol=512.0*np.finfo(float).eps):
            raise KinematicalStateError("frame transport determinant must be +/-1")
        object.__setattr__(self, "matrix", matrix)

    @property
    def determinant(self) -> float:
        return float(np.linalg.det(self.matrix))

    def polar(self, value: np.ndarray) -> np.ndarray:
        return finite_array(self.matrix @ finite_array(value, shape=(3,)), shape=(3,))

    def axial(self, value: np.ndarray) -> np.ndarray:
        vector = finite_array(value, shape=(3,))
        return finite_array(self.determinant * (self.matrix @ vector), shape=(3,))


@dataclass(frozen=True)
class KinematicalState:
    """One typed sample/witness of the physical congruence kinematics.

    sigma is a physical STF2 tensor in s^-1; omega is the axial dual of the
    spatial vorticity two-form in s^-1; acceleration is physical A_A in
    m s^-2; beta_RM and beta_MO are dimensionless polar relative velocities.
    Missing blocks remain None and are never replaced by zeros.

    The beta components carry their own basis IDs. They may be contracted
    with congruence tensors only after an explicit FrameTransport to basis_id.
    """

    sample_id: str
    frame_id: str
    congruence_id: str
    epoch_window_id: str
    basis_id: str
    source_identity: str
    sigma: np.ndarray | None = None
    omega: np.ndarray | None = None
    acceleration: np.ndarray | None = None
    beta_RM: np.ndarray | None = None
    beta_MO: np.ndarray | None = None
    beta_RM_basis_id: str | None = None
    beta_MO_basis_id: str | None = None
    H: float | None = None
    perturbative_order: str = "DECLARED_KINEMATICAL_STATE"
    units_convention: str = "PHYSICAL_SI_EXPLICIT_C_V1"

    def __post_init__(self) -> None:
        for name in ("sample_id", "frame_id", "congruence_id", "epoch_window_id",
                     "basis_id", "source_identity", "perturbative_order",
                     "units_convention"):
            _nonempty(getattr(self, name), name)

        if self.units_convention != "PHYSICAL_SI_EXPLICIT_C_V1":
            raise KinematicalStateError("this implementation requires explicit-SI units with c retained")

        if self.sigma is not None:
            object.__setattr__(self, "sigma", _validate_stf2(self.sigma))
        if self.omega is not None:
            object.__setattr__(self, "omega", finite_array(self.omega, shape=(3,), name="omega axial vector"))
        if self.acceleration is not None:
            object.__setattr__(self, "acceleration", finite_array(self.acceleration, shape=(3,), name="physical acceleration"))

        for name in ("beta_RM", "beta_MO"):
            value = getattr(self, name)
            basis_name = f"{name}_basis_id"
            basis_id = getattr(self, basis_name)
            if value is None:
                if basis_id is not None:
                    raise KinematicalStateError(f"{basis_name} supplied without {name}")
                continue
            if basis_id is None:
                raise KinematicalStateError(f"{name} requires its component basis identity")
            _nonempty(basis_id, basis_name)
            vector = finite_array(value, shape=(3,), name=name)
            if float(vector @ vector) >= 1.0:
                raise KinematicalStateError(f"{name} must be strictly subluminal")
            object.__setattr__(self, name, vector)

        if self.H is not None:
            object.__setattr__(self, "H", _finite_scalar(self.H, "H"))

    @property
    def state_id(self) -> str:
        """Content identity of the whole typed sample, including missingness."""
        return content_id(self)

    @classmethod
    def from_velocity_jet(
        cls,
        *,
        u: Sequence[float],
        derivative_covariant: Sequence[Sequence[float]],
        spatial_triad: Sequence[Sequence[float]],
        speed_of_light: float,
        sample_id: str,
        frame_id: str,
        congruence_id: str,
        epoch_window_id: str,
        basis_id: str,
        source_identity: str,
        beta_RM: Sequence[float] | None = None,
        beta_MO: Sequence[float] | None = None,
        beta_RM_basis_id: str | None = None,
        beta_MO_basis_id: str | None = None,
        perturbative_order: str = "EXACT_LOCAL_VELOCITY_JET",
    ) -> "KinematicalState":
        """Project an admitted 4D velocity jet into a declared spatial triad.

        The jet API uses u=U/c with u.u=-1 and nabla_a u_b in inverse-length
        units. Its output is projected with the supplied orthonormal triad.
        This is a pointwise kinematic extraction, not spacetime evolution.
        """
        unit_u = unit_timelike(u)
        triad = finite_array(spatial_triad, shape=(3, 4), name="spatial triad")
        gram = triad @ METRIC @ triad.T
        orthogonal = triad @ METRIC @ unit_u
        if np.linalg.norm(gram - np.eye(3)) > 1e-10:
            raise KinematicalStateError("spatial_triad must be orthonormal")
        if np.linalg.norm(orthogonal) > 1e-10:
            raise KinematicalStateError("spatial_triad must be orthogonal to the congruence velocity")

        jet = kinematics_from_velocity_jet(
            unit_u,
            derivative_covariant,
            speed_of_light=speed_of_light,
            congruence=congruence_id,
            frame=frame_id,
        )
        sigma_spatial = triad @ jet.shear_covariant @ triad.T
        omega_twoform = triad @ jet.vorticity_covariant @ triad.T
        omega_axial = 0.5 * np.einsum("ABC,BC->A", _EPSILON, omega_twoform)
        acceleration_spatial = triad @ jet.acceleration_covariant
        return cls(
            sample_id=sample_id,
            frame_id=frame_id,
            congruence_id=congruence_id,
            epoch_window_id=epoch_window_id,
            basis_id=basis_id,
            source_identity=source_identity,
            sigma=sigma_spatial,
            omega=omega_axial,
            acceleration=acceleration_spatial,
            beta_RM=None if beta_RM is None else np.asarray(beta_RM, dtype=float),
            beta_MO=None if beta_MO is None else np.asarray(beta_MO, dtype=float),
            beta_RM_basis_id=beta_RM_basis_id,
            beta_MO_basis_id=beta_MO_basis_id,
            H=float(jet.expansion) / 3.0,
            perturbative_order=perturbative_order,
        )


@dataclass(frozen=True)
class FunctionalValue:
    """Typed value of one registered functional for one common state sample."""

    functional_id: str
    sample_id: str
    state_id: str
    representation: str
    dimension: int
    units: str
    parity: str
    basis_id: str
    status: str
    components: np.ndarray | None
    inputs: tuple[str, ...]
    normalization_id: str
    reason: str = ""

    def __post_init__(self) -> None:
        for name in ("functional_id", "sample_id", "state_id", "representation",
                     "units", "parity", "basis_id", "status", "normalization_id"):
            _nonempty(getattr(self, name), name)
        object.__setattr__(self, "inputs", tuple(self.inputs))
        if type(self.dimension) is not int or self.dimension < 0:
            raise KinematicalStateError("functional dimension must be a nonnegative integer")
        if self.status == "AVAILABLE":
            if self.components is None:
                raise KinematicalStateError("AVAILABLE functional requires components")
            object.__setattr__(
                self, "components",
                finite_array(self.components, shape=(self.dimension,), name=self.functional_id),
            )
        elif self.components is not None:
            raise KinematicalStateError("non-available functional must not carry numerical components")


def _value(
    state: KinematicalState,
    functional_id: str,
    value: np.ndarray | Sequence[float] | None,
    *,
    representation: str,
    units: str,
    parity: str,
    basis_id: str,
    inputs: tuple[str, ...],
    normalization_id: str = "RAW",
    status: str = "AVAILABLE",
    reason: str = "",
) -> FunctionalValue:
    if value is None:
        return FunctionalValue(
            functional_id, state.sample_id, state.state_id, representation,
            0, units, parity, basis_id, status, None, inputs, normalization_id,
            reason or "required component unavailable",
        )
    components = np.atleast_1d(np.asarray(value, dtype=float))
    return FunctionalValue(
        functional_id, state.sample_id, state.state_id, representation,
        int(components.size), units, parity, basis_id, status, components,
        inputs, normalization_id, reason,
    )


def _transport_beta(
    state: KinematicalState,
    name: str,
    transports: Mapping[tuple[str, str], FrameTransport],
) -> tuple[np.ndarray | None, str]:
    vector = getattr(state, name)
    if vector is None:
        return None, "UNAVAILABLE"
    source_basis = getattr(state, f"{name}_basis_id")
    if source_basis == state.basis_id:
        return vector, "AVAILABLE"
    transport = transports.get((source_basis, state.basis_id))
    if transport is None:
        return None, "FRAME_TRANSPORT_REQUIRED"
    if transport.source_basis_id != source_basis or transport.target_basis_id != state.basis_id:
        raise KinematicalStateError("frame transport key and payload disagree")
    return transport.polar(vector), "AVAILABLE"


def evaluate_kinematical_functionals(
    state: KinematicalState,
    *,
    speed_of_light: float = _C0,
    frame_transports: Mapping[tuple[str, str], FrameTransport] | None = None,
) -> tuple[FunctionalValue, ...]:
    """Evaluate direct and mixed x functionals without scalar collapse.

    A zero/unknown Hubble normalizer never creates a zero result. A velocity
    in another basis is contracted only after a registered orthogonal map.
    """
    c = _finite_scalar(speed_of_light, "speed_of_light")
    if c <= 0.0:
        raise KinematicalStateError("speed_of_light must be positive")
    transports = {} if frame_transports is None else frame_transports
    out: list[FunctionalValue] = []
    sigma = state.sigma
    omega = state.omega
    acceleration = state.acceleration
    beta_rm, beta_rm_status = _transport_beta(state, "beta_RM", transports)
    beta_mo, beta_mo_status = _transport_beta(state, "beta_MO", transports)
    H = state.H

    # Direct coordinates always remain in their own declared representation.
    out.append(_value(state, "SIGMA_RAW", None if sigma is None else stf2_components(sigma),
                      representation="STF2_POLAR", units="s^-1", parity="EVEN",
                      basis_id=state.basis_id, inputs=("sigma_AB",)))
    out.append(_value(state, "OMEGA_RAW", omega, representation="VECTOR_AXIAL",
                      units="s^-1", parity="PSEUDO", basis_id=state.basis_id,
                      inputs=("omega_A",)))
    out.append(_value(state, "ACCEL_RAW", acceleration, representation="VECTOR_POLAR",
                      units="m s^-2", parity="EVEN", basis_id=state.basis_id,
                      inputs=("A_A",)))
    for name, vector, basis_id in (
        ("BETA_RM", state.beta_RM, state.beta_RM_basis_id),
        ("BETA_MO", state.beta_MO, state.beta_MO_basis_id),
    ):
        out.append(_value(state, name, vector, representation="VECTOR_POLAR",
                          units="1", parity="EVEN", basis_id=basis_id or "UNAVAILABLE",
                          inputs=(name,)))

    # beta_RO is only a first-order closure view of the two independent relative velocities.
    if beta_rm is None or beta_mo is None:
        out.append(_value(state, "BETA_RO_FIRST_ORDER_VIEW", None,
                          representation="VECTOR_POLAR", units="1", parity="EVEN",
                          basis_id=state.basis_id, inputs=("beta_RM", "beta_MO"),
                          status="UNAVAILABLE", reason="both independent frame velocities are required"))
    else:
        beta_ro = beta_rm + beta_mo
        if float(beta_ro @ beta_ro) >= 1.0:
            out.append(_value(state, "BETA_RO_FIRST_ORDER_VIEW", None,
                              representation="VECTOR_POLAR", units="1", parity="EVEN",
                              basis_id=state.basis_id, inputs=("beta_RM", "beta_MO"),
                              status="UNRESOLVED", reason="first-order sum reaches/exceeds the subluminal boundary"))
        else:
            out.append(_value(state, "BETA_RO_FIRST_ORDER_VIEW", beta_ro,
                              representation="VECTOR_POLAR", units="1", parity="EVEN",
                              basis_id=state.basis_id, inputs=("beta_RM", "beta_MO"),
                              normalization_id="FIRST_ORDER_CLOSURE_ONLY",
                              status="CONDITIONAL_FIRST_ORDER",
                              reason="not an exact relativistic velocity composition"))

    if sigma is None:
        status_sigma, reason_sigma = "UNAVAILABLE", "sigma_AB not admitted"
    elif H is None:
        status_sigma, reason_sigma = "UNAVAILABLE", "Hubble normalization not admitted"
    elif H == 0.0:
        status_sigma, reason_sigma = "UNDEFINED", "H=0; Hubble-normalized shear is undefined"
    else:
        status_sigma, reason_sigma = "AVAILABLE", ""
    out.append(_value(state, "SIGMA_H",
                      None if status_sigma != "AVAILABLE" else stf2_components(sigma) / H,
                      representation="STF2_POLAR", units="1", parity="EVEN",
                      basis_id=state.basis_id, inputs=("sigma_AB", "H"),
                      normalization_id="DIVIDE_BY_H", status=status_sigma, reason=reason_sigma))

    if omega is None:
        status_omega, reason_omega = "UNAVAILABLE", "omega_A not admitted"
    elif H is None:
        status_omega, reason_omega = "UNAVAILABLE", "Hubble normalization not admitted"
    elif H == 0.0:
        status_omega, reason_omega = "UNDEFINED", "H=0; Hubble-normalized vorticity is undefined"
    else:
        status_omega, reason_omega = "AVAILABLE", ""
    out.append(_value(state, "OMEGA_H",
                      None if status_omega != "AVAILABLE" else omega / H,
                      representation="VECTOR_AXIAL", units="1", parity="PSEUDO",
                      basis_id=state.basis_id, inputs=("omega_A", "H"),
                      normalization_id="DIVIDE_BY_H", status=status_omega, reason=reason_omega))

    if acceleration is None:
        status_acc, reason_acc = "UNAVAILABLE", "A_A not admitted"
    elif H is None:
        status_acc, reason_acc = "UNAVAILABLE", "Hubble normalization not admitted"
    elif H == 0.0:
        status_acc, reason_acc = "UNDEFINED", "H=0; A/(cH) is undefined"
    else:
        status_acc, reason_acc = "AVAILABLE", ""
    out.append(_value(state, "ACCEL_C_H",
                      None if status_acc != "AVAILABLE" else acceleration / (c * H),
                      representation="VECTOR_POLAR", units="1", parity="EVEN",
                      basis_id=state.basis_id, inputs=("A_A", "H", "c"),
                      normalization_id="DIVIDE_BY_cH", status=status_acc, reason=reason_acc))

    mixed_ready = beta_rm is not None
    mixed_reason = "beta_RM unavailable" if state.beta_RM is None else (
        "explicit beta_RM frame transport to congruence basis required" if beta_rm_status != "AVAILABLE" else ""
    )
    if sigma is None or beta_rm is None:
        mixed_status, mixed_reason2 = "UNAVAILABLE", mixed_reason or "sigma_AB unavailable"
    elif H is None or H == 0.0:
        mixed_status = "UNDEFINED" if H == 0.0 else "UNAVAILABLE"
        mixed_reason2 = "H=0" if H == 0.0 else "Hubble normalization unavailable"
    else:
        mixed_status, mixed_reason2 = "AVAILABLE", ""
    out.append(_value(state, "SIGMA_CONTRACT_BETA",
                      None if mixed_status != "AVAILABLE" else np.array([beta_rm @ sigma @ beta_rm / H]),
                      representation="SCALAR", units="1", parity="EVEN", basis_id=state.basis_id,
                      inputs=("sigma_AB", "beta_RM", "H"),
                      normalization_id="BETA_SIGMA_BETA_OVER_H",
                      status=mixed_status, reason=mixed_reason2))

    if omega is None or beta_rm is None:
        mixed_status, mixed_reason2 = "UNAVAILABLE", mixed_reason or "omega_A unavailable"
    elif H is None or H == 0.0:
        mixed_status = "UNDEFINED" if H == 0.0 else "UNAVAILABLE"
        mixed_reason2 = "H=0" if H == 0.0 else "Hubble normalization unavailable"
    else:
        mixed_status, mixed_reason2 = "AVAILABLE", ""
    out.append(_value(state, "BETA_DOT_OMEGA",
                      None if mixed_status != "AVAILABLE" else np.array([beta_rm @ omega / H]),
                      representation="PSEUDOSCALAR", units="1", parity="ODD", basis_id=state.basis_id,
                      inputs=("beta_RM", "omega_A", "H"),
                      normalization_id="BETA_DOT_OMEGA_OVER_H",
                      status=mixed_status, reason=mixed_reason2))

    if sigma is None or beta_rm is None:
        mixed_status, mixed_reason2 = "UNAVAILABLE", mixed_reason or "sigma_AB unavailable"
    elif H is None or H == 0.0:
        mixed_status = "UNDEFINED" if H == 0.0 else "UNAVAILABLE"
        mixed_reason2 = "H=0" if H == 0.0 else "Hubble normalization unavailable"
    else:
        mixed_status, mixed_reason2 = "AVAILABLE", ""
    out.append(_value(state, "SIGMA_BETA_VECTOR",
                      None if mixed_status != "AVAILABLE" else (sigma @ beta_rm) / H,
                      representation="VECTOR_POLAR", units="1", parity="EVEN",
                      basis_id=state.basis_id, inputs=("sigma_AB", "beta_RM", "H"),
                      normalization_id="SIGMA_BETA_OVER_H",
                      status=mixed_status, reason=mixed_reason2))

    if omega is None or beta_rm is None:
        mixed_status, mixed_reason2 = "UNAVAILABLE", mixed_reason or "omega_A unavailable"
    elif H is None or H == 0.0:
        mixed_status = "UNDEFINED" if H == 0.0 else "UNAVAILABLE"
        mixed_reason2 = "H=0" if H == 0.0 else "Hubble normalization unavailable"
    else:
        mixed_status, mixed_reason2 = "AVAILABLE", ""
    out.append(_value(state, "BETA_CROSS_OMEGA",
                      None if mixed_status != "AVAILABLE" else np.cross(beta_rm, omega) / H,
                      representation="VECTOR_POLAR", units="1", parity="EVEN",
                      basis_id=state.basis_id, inputs=("beta_RM", "omega_A", "H"),
                      normalization_id="BETA_CROSS_OMEGA_OVER_H",
                      status=mixed_status, reason=mixed_reason2))

    if acceleration is None or beta_mo is None:
        mixed_status, mixed_reason2 = "UNAVAILABLE", (
            "beta_MO unavailable" if state.beta_MO is None else "A_A unavailable"
        )
    elif H is None or H == 0.0:
        mixed_status = "UNDEFINED" if H == 0.0 else "UNAVAILABLE"
        mixed_reason2 = "H=0" if H == 0.0 else "Hubble normalization unavailable"
    else:
        mixed_status, mixed_reason2 = "AVAILABLE", ""
    out.append(_value(state, "BETA_DOT_ACCEL",
                      None if mixed_status != "AVAILABLE" else np.array([beta_mo @ acceleration / (c * H)]),
                      representation="SCALAR", units="1", parity="EVEN", basis_id=state.basis_id,
                      inputs=("beta_MO", "A_A", "c", "H"),
                      normalization_id="BETA_DOT_A_OVER_cH",
                      status=mixed_status, reason=mixed_reason2))

    if sigma is None:
        status, reason = "UNAVAILABLE", "sigma_AB not admitted"
    elif H is None:
        status, reason = "UNAVAILABLE", "Hubble normalization not admitted"
    elif H == 0.0:
        status, reason = "UNDEFINED", "H=0; cubic shear invariant normalization is undefined"
    else:
        status, reason = "AVAILABLE", ""
    out.append(_value(state, "SIGMA_CUBIC",
                      None if status != "AVAILABLE" else np.array([np.trace(sigma @ sigma @ sigma) / H**3]),
                      representation="SCALAR", units="1", parity="EVEN", basis_id=state.basis_id,
                      inputs=("sigma_AB", "H"), normalization_id="TRACE_SIGMA_CUBIC_OVER_H3",
                      status=status, reason=reason))

    if omega is None:
        status, reason = "UNAVAILABLE", "omega_A not admitted"
    elif H is None:
        status, reason = "UNAVAILABLE", "Hubble normalization not admitted"
    elif H == 0.0:
        status, reason = "UNDEFINED", "H=0; vorticity stress normalization is undefined"
    else:
        status, reason = "AVAILABLE", ""
    out.append(_value(state, "OMEGA_STRESS",
                      None if status != "AVAILABLE" else np.array([omega @ omega / (6.0 * H**2)]),
                      representation="NONNEGATIVE_SCALAR", units="1", parity="EVEN",
                      basis_id=state.basis_id, inputs=("omega_A", "H"),
                      normalization_id="OMEGA_SQUARED_OVER_6H2", status=status, reason=reason))

    return tuple(out)


@dataclass(frozen=True)
class LocalOpticalPrediction:
    """Leading local radial-rate and angular-drift predictions for one state."""

    state_id: str
    directions: np.ndarray
    radial_rate_s_inv: np.ndarray | None
    fermi_walker_drift_s_inv: np.ndarray | None
    catalogue_drift_s_inv: np.ndarray | None
    radial_status: str
    transverse_status: str
    triad_rotation: np.ndarray | None
    clock_scale: float
    speed_of_light: float
    scope: str = "LOCAL_C3_COMMON_CONGRUENCE_BEFORE_CAUSTICS"

    def __post_init__(self) -> None:
        object.__setattr__(self, "directions", finite_array(self.directions, ndim=2, name="directions"))
        if self.radial_rate_s_inv is not None:
            object.__setattr__(self, "radial_rate_s_inv", finite_array(self.radial_rate_s_inv, shape=(len(self.directions),)))
        if self.fermi_walker_drift_s_inv is not None:
            object.__setattr__(self, "fermi_walker_drift_s_inv", finite_array(self.fermi_walker_drift_s_inv, shape=(len(self.directions), 3)))
        if self.catalogue_drift_s_inv is not None:
            object.__setattr__(self, "catalogue_drift_s_inv", finite_array(self.catalogue_drift_s_inv, shape=(len(self.directions), 3)))
        if self.triad_rotation is not None:
            object.__setattr__(self, "triad_rotation", finite_array(self.triad_rotation, shape=(3,)))


def local_optical_response(
    state: KinematicalState,
    directions: Sequence[Sequence[float]],
    *,
    triad_rotation: Sequence[float] | None,
    clock_scale: float = 1.0,
    speed_of_light: float = _C0,
) -> LocalOpticalPrediction:
    """Evaluate the common-congruence local optical map.

    Sourceward unit directions n are required. The leading radial rate is
        d(n) = H + sigma_ab n^a n^b - A_a n^a/c.
    In a Fermi-Walker triad the leading angular drift is
        mu_FW = P(n) sigma n + n x omega.
    In a catalogue triad rotating with angular velocity Omega,
        mu_cat = k [P(n) sigma n + n x (omega + Omega)].
    A missing triad-rotation vector does not silently mean Omega=0. The
    radial formula is local only and is not a finite-redshift transfer.
    """
    n = finite_array(directions, ndim=2, name="source directions")
    if n.shape[1] != 3 or len(n) == 0:
        raise KinematicalStateError("directions must have shape (N,3), N>0")
    norms = np.linalg.norm(n, axis=1)
    if np.max(np.abs(norms - 1.0)) > 1e-10:
        raise KinematicalStateError("all source directions must be unit vectors")
    c = _finite_scalar(speed_of_light, "speed_of_light")
    k = _finite_scalar(clock_scale, "clock_scale")
    if c <= 0.0 or k <= 0.0:
        raise KinematicalStateError("c and clock_scale must be positive")

    radial = None
    if state.H is not None and state.sigma is not None and state.acceleration is not None:
        radial = state.H + np.einsum("ni,ij,nj->n", n, state.sigma, n) - (n @ state.acceleration) / c
        radial_status = "AVAILABLE_LOCAL_OPTICAL_RATE"
    else:
        radial_status = "UNAVAILABLE_REQUIRED_H_SIGMA_OR_ACCELERATION"

    fermi = None
    catalogue = None
    rotation = None if triad_rotation is None else finite_array(triad_rotation, shape=(3,), name="triad_rotation")
    if state.sigma is None or state.omega is None:
        transverse_status = "UNAVAILABLE_REQUIRED_SIGMA_OR_VORTICITY"
    else:
        projected = state.sigma[None, :, :] @ n[:, :, None]
        sigma_n = projected[:, :, 0]
        sigma_n = sigma_n - n * np.einsum("ni,ni->n", n, sigma_n)[:, None]
        fermi = sigma_n + np.cross(n, state.omega[None, :])
        if rotation is None:
            transverse_status = "TRIAD_ROTATION_UNAVAILABLE_CATALOGUE_B1_UNRESOLVED"
        else:
            catalogue = k * (sigma_n + np.cross(n, (state.omega + rotation)[None, :]))
            transverse_status = "AVAILABLE_WITH_EXPLICIT_TRIAD_ROTATION_AND_CLOCK"
    return LocalOpticalPrediction(
        state_id=state.state_id,
        directions=n,
        radial_rate_s_inv=radial,
        fermi_walker_drift_s_inv=fermi,
        catalogue_drift_s_inv=catalogue,
        radial_status=radial_status,
        transverse_status=transverse_status,
        triad_rotation=rotation,
        clock_scale=k,
        speed_of_light=c,
    )


@dataclass(frozen=True)
class OpticalJacobian:
    """Unwhitened source-level derivative of the ideal local optical map."""

    matrix: np.ndarray
    parameter_names: tuple[str, ...]
    parameter_units: tuple[str, ...]
    row_labels: tuple[str, ...]
    observable_units: tuple[str, ...]
    scope: str = "IDEAL_LOCAL_OPTICAL_MAP_PRE_SELECTION_PRE_WHITENING"

    def __post_init__(self) -> None:
        object.__setattr__(self, "matrix", finite_array(self.matrix, ndim=2, name="optical Jacobian"))
        object.__setattr__(self, "parameter_names", tuple(self.parameter_names))
        object.__setattr__(self, "parameter_units", tuple(self.parameter_units))
        object.__setattr__(self, "row_labels", tuple(self.row_labels))
        object.__setattr__(self, "observable_units", tuple(self.observable_units))
        if self.matrix.shape != (len(self.row_labels), len(self.parameter_names)):
            raise KinematicalStateError("Jacobian dimensions do not match row/parameter labels")
        if len(self.parameter_units) != len(self.parameter_names):
            raise KinematicalStateError("parameter units do not match parameter labels")
        if len(self.observable_units) != len(self.row_labels):
            raise KinematicalStateError("observable units do not match row labels")


def local_optical_jacobian(
    directions: Sequence[Sequence[float]],
    tangent_basis: Sequence[Sequence[Sequence[float]]],
    *,
    clock_scale: float = 1.0,
    include_triad_rotation: bool = True,
) -> OpticalJacobian:
    """Build the ideal finite-source Jacobian for radial rates and angular drift.

    The acceleration parameter is A/c (s^-1), so all response coordinates
    share inverse-time units. Each source contributes one radial row and two
    tangent-plane angular-drift rows. If triad rotation is included, its three
    columns duplicate the physical-vorticity B1 columns exactly: an independent
    triad calibration is required before omega is separately identified.

    This is not yet the survey Jacobian: apply the real distance/sky window,
    source selection, systematic templates, covariance whitening and nuisance
    quotient before making observational identifiability claims.
    """
    n = finite_array(directions, ndim=2, name="source directions")
    t = finite_array(tangent_basis, ndim=3, name="tangent basis")
    if n.shape[1] != 3 or len(n) == 0 or t.shape != (len(n), 2, 3):
        raise KinematicalStateError("require directions (N,3) and tangent_basis (N,2,3)")
    if np.max(np.abs(np.linalg.norm(n, axis=1) - 1.0)) > 1e-10:
        raise KinematicalStateError("source directions must be unit vectors")
    for i in range(len(n)):
        if np.linalg.norm(t[i] @ n[i]) > 1e-10:
            raise KinematicalStateError("tangent basis must be orthogonal to source direction")
        if np.linalg.norm(t[i] @ t[i].T - np.eye(2)) > 1e-10:
            raise KinematicalStateError("two tangent basis vectors must be orthonormal")

    k = _finite_scalar(clock_scale, "clock_scale")
    if k <= 0.0:
        raise KinematicalStateError("clock_scale must be positive")

    parameter_names = (
        "H",
        *(f"sigma_stf5_{i}" for i in range(5)),
        *(f"A_over_c_{i}" for i in range(3)),
        *(f"omega_{i}" for i in range(3)),
    )
    parameter_units = ("s^-1",) * 12
    if include_triad_rotation:
        parameter_names += tuple(f"triad_rotation_{i}" for i in range(3))
        parameter_units += ("s^-1",) * 3

    matrix = np.zeros((3 * len(n), len(parameter_names)), dtype=float)
    rows: list[str] = []
    observable_units: list[str] = []
    for i, ni in enumerate(n):
        radial_row = 3 * i
        matrix[radial_row, 0] = 1.0
        matrix[radial_row, 1:6] = np.einsum("i,aij,j->a", ni, _STF2_BASIS, ni)
        matrix[radial_row, 6:9] = -ni
        rows.append(f"source[{i}].radial_rate")
        observable_units.append("s^-1")

        for a in range(2):
            tangent = t[i, a]
            row = radial_row + 1 + a
            matrix[row, 1:6] = k * np.einsum("i,aij,j->a", tangent, _STF2_BASIS, ni)
            rotation_coefficients = np.array([
                np.dot(tangent, np.cross(ni, np.eye(3)[j])) for j in range(3)
            ])
            matrix[row, 9:12] = k * rotation_coefficients
            if include_triad_rotation:
                matrix[row, 12:15] = k * rotation_coefficients
            rows.append(f"source[{i}].angular_tangent[{a}]")
            observable_units.append("s^-1")

    return OpticalJacobian(
        matrix=matrix,
        parameter_names=parameter_names,
        parameter_units=parameter_units,
        row_labels=tuple(rows),
        observable_units=tuple(observable_units),
    )


def transform_state_o3(
    state: KinematicalState,
    rotation: Sequence[Sequence[float]],
    *,
    new_basis_id: str,
) -> KinematicalState:
    """Return the same physical state in an orthogonally transformed basis.

    Polar vectors transform as Rv; the axial vorticity vector transforms as
    det(R) R omega; STF2 transforms as R sigma R^T. Both beta vectors must
    already be expressed in the source state basis so the complete state can
    be transformed without an implicit frame bridge.
    """
    R = finite_array(rotation, shape=(3, 3), name="orthogonal transformation")
    if np.linalg.norm(R @ R.T - np.eye(3)) > 512.0 * np.finfo(float).eps:
        raise KinematicalStateError("rotation must be orthogonal")
    determinant = float(np.linalg.det(R))
    if not np.isclose(abs(determinant), 1.0, rtol=0.0, atol=512.0*np.finfo(float).eps):
        raise KinematicalStateError("orthogonal transformation determinant must be +/-1")
    _nonempty(new_basis_id, "new_basis_id")
    for vector_name in ("beta_RM", "beta_MO"):
        vector = getattr(state, vector_name)
        basis_id = getattr(state, f"{vector_name}_basis_id")
        if vector is not None and basis_id != state.basis_id:
            raise KinematicalStateError(
                f"{vector_name} must be transported into the state basis before an O(3) action"
            )
    return KinematicalState(
        sample_id=state.sample_id,
        frame_id=state.frame_id,
        congruence_id=state.congruence_id,
        epoch_window_id=state.epoch_window_id,
        basis_id=new_basis_id,
        source_identity=state.source_identity,
        sigma=None if state.sigma is None else R @ state.sigma @ R.T,
        omega=None if state.omega is None else determinant * (R @ state.omega),
        acceleration=None if state.acceleration is None else R @ state.acceleration,
        beta_RM=None if state.beta_RM is None else R @ state.beta_RM,
        beta_MO=None if state.beta_MO is None else R @ state.beta_MO,
        beta_RM_basis_id=None if state.beta_RM is None else new_basis_id,
        beta_MO_basis_id=None if state.beta_MO is None else new_basis_id,
        H=state.H,
        perturbative_order=state.perturbative_order,
        units_convention=state.units_convention,
    )


__all__ = [
    "FrameTransport",
    "FunctionalValue",
    "KinematicalState",
    "KinematicalStateError",
    "LocalOpticalPrediction",
    "OpticalJacobian",
    "evaluate_kinematical_functionals",
    "local_optical_jacobian",
    "local_optical_response",
    "stf2_components",
    "stf2_from_components",
    "transform_state_o3",
]
