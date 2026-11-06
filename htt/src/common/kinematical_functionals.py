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

from .joint_anisotropy_state import (
    AccelerationNormalization,
    JointAnisotropyState,
    MissingComponent,
    UnitsConvention,
)
from .tensor_functionals_v1 import (
    TensorFunctionalOperator,
    TensorFunctionalResult,
    build_tensor_functional_spec,
    evaluate_tensor_functional,
)
from .orbit_nonlinearity import matrix_to_stf5, stf5_to_matrix
from .r7_contracts import content_id, finite_array
from .relativistic_kinematics import (
    METRIC,
    kinematics_from_velocity_jet,
    unit_timelike,
)


_C0 = 299_792_458.0
_STF2_BASIS = np.stack(
    [stf5_to_matrix(np.eye(5, dtype=np.float64)[i]) for i in range(5)],
    axis=0,
)
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
    """Return the canonical (Sxx,Syy,Sxy,Sxz,Syz) STF5 Cartesian coordinates."""
    sigma = _validate_stf2(tensor)
    return finite_array(matrix_to_stf5(sigma), shape=(5,))


def stf2_from_components(components: np.ndarray) -> np.ndarray:
    """Reconstruct an STF tensor from canonical STF5 Cartesian components."""
    values = finite_array(components, shape=(5,), name="STF5 Cartesian components")
    return finite_array(stf5_to_matrix(values), shape=(3, 3))


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

    beta_RM_frame_id and beta_MO_frame_id denote component coordinate frames,
    not the physical endpoint frame of each relative motion. In a canonical
    JointAnisotropyState, both are the common VelocityFrameBundle coordinate
    frame and basis. radiation/matter/observer endpoint IDs are separately
    retained in velocity_frame_ids. A 3D FrameTransport only changes spatial
    basis axes; it is not a Lorentz frame transformation.
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
    beta_RM_frame_id: str | None = None
    beta_MO_frame_id: str | None = None
    beta_RO: np.ndarray | None = None
    beta_RO_basis_id: str | None = None
    beta_RO_frame_id: str | None = None
    beta_semantic_role: str | None = None
    velocity_frame_ids: tuple[str, ...] = ()
    velocity_closure_status: str | None = None
    velocity_closure_residual: np.ndarray | None = None
    velocity_truncation_remainder_bound: float | None = None
    canonical_state_id: str | None = None
    canonical_geometry_id: str | None = None
    delta_omega_k: float | None = None
    canonical_units_convention: str | None = None
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
            frame_name = f"{name}_frame_id"
            basis_id = getattr(self, basis_name)
            physical_frame_id = getattr(self, frame_name)
            if value is None:
                if basis_id is not None or physical_frame_id is not None:
                    raise KinematicalStateError(
                        f"{basis_name}/{frame_name} supplied without {name}"
                    )
                continue
            if basis_id is None:
                raise KinematicalStateError(f"{name} requires its component basis identity")
            _nonempty(basis_id, basis_name)
            if physical_frame_id is not None:
                _nonempty(physical_frame_id, frame_name)
            vector = finite_array(value, shape=(3,), name=name)
            if float(vector @ vector) >= 1.0:
                raise KinematicalStateError(f"{name} must be strictly subluminal")
            object.__setattr__(self, name, vector)

        if self.beta_RO is not None:
            if self.beta_RO_basis_id is None or self.beta_RO_frame_id is None:
                raise KinematicalStateError("beta_RO requires component basis and coordinate-frame identity")
            _nonempty(self.beta_RO_basis_id, "beta_RO_basis_id")
            _nonempty(self.beta_RO_frame_id, "beta_RO_frame_id")
            beta_ro = finite_array(self.beta_RO, shape=(3,), name="beta_RO")
            if float(beta_ro @ beta_ro) >= 1.0:
                raise KinematicalStateError("beta_RO must be strictly subluminal")
            object.__setattr__(self, "beta_RO", beta_ro)
        elif self.beta_RO_basis_id is not None or self.beta_RO_frame_id is not None:
            raise KinematicalStateError("beta_RO metadata supplied without beta_RO")
        object.__setattr__(self, "velocity_frame_ids", tuple(self.velocity_frame_ids))
        if self.velocity_frame_ids and (
            len(self.velocity_frame_ids) != 3
            or len(set(self.velocity_frame_ids)) != 3
            or not all(isinstance(x, str) and x for x in self.velocity_frame_ids)
        ):
            raise KinematicalStateError("velocity_frame_ids must be three distinct frame identities")
        if self.beta_semantic_role is not None:
            _nonempty(self.beta_semantic_role, "beta_semantic_role")
        if self.velocity_closure_status is not None:
            _nonempty(self.velocity_closure_status, "velocity_closure_status")
        if self.velocity_closure_residual is not None:
            object.__setattr__(self, "velocity_closure_residual",
                               finite_array(self.velocity_closure_residual, shape=(3,)))
        if self.velocity_truncation_remainder_bound is not None:
            bound = _finite_scalar(self.velocity_truncation_remainder_bound, "velocity_truncation_remainder_bound")
            if bound < 0.0:
                raise KinematicalStateError("velocity truncation remainder bound must be nonnegative")
            object.__setattr__(self, "velocity_truncation_remainder_bound", bound)
        for name in ("canonical_state_id", "canonical_geometry_id"):
            value = getattr(self, name)
            if value is not None:
                _nonempty(value, name)
        if self.delta_omega_k is not None:
            object.__setattr__(self, "delta_omega_k", _finite_scalar(self.delta_omega_k, "delta_omega_k"))
        if self.canonical_units_convention is not None:
            _nonempty(self.canonical_units_convention, "canonical_units_convention")
        if self.H is not None:
            object.__setattr__(self, "H", _finite_scalar(self.H, "H"))

    @property
    def state_id(self) -> str:
        """Content identity of the whole typed sample, including missingness."""
        return content_id(self)


    @classmethod
    def from_joint_anisotropy_state(
        cls,
        joint_state: JointAnisotropyState,
        *,
        expansion_scalar: float,
        speed_of_light: float = _C0,
        sample_id: str | None = None,
    ) -> "KinematicalState":
        """Create a physical-SI optical evaluation view of the canonical state.

        The input JointAnisotropyState remains the SSOT. Its registered
        congruence coordinates are normalized by Theta=nabla_a U^a:
            sigma_hat = sigma/Theta,
            omega_hat = omega/Theta,
            A_hat = A/(c Theta)  [explicit-c branch].
        This adapter requires EXPLICIT_C_THETA_NORMALIZED and converts back
        to raw SI values for local_optical_response. In particular, an
        acceleration normalized in the c=1 convention is rejected until a
        separately justified unit conversion is supplied.

        VelocityFrameBundle stores beta_RO/RM/MO components in one common
        coordinate_frame and basis; radiation/matter/observer IDs describe
        the relative-frame roles, not separate component coordinate systems.
        The first-order closure status/residual and all three frame identities
        are preserved as view metadata. Geometry stays attached to the
        canonical_state_id and its own geometry content identity.
        """
        if type(joint_state) is not JointAnisotropyState:
            raise TypeError("joint_state must be an exact canonical JointAnisotropyState")
        theta = _finite_scalar(expansion_scalar, "expansion_scalar")
        c = _finite_scalar(speed_of_light, "speed_of_light")
        if theta == 0.0 or c <= 0.0:
            raise KinematicalStateError("expansion_scalar must be nonzero and c positive")
        if joint_state.units_convention is not UnitsConvention.EXPLICIT_C_THETA_NORMALIZED:
            raise KinematicalStateError(
                "only EXPLICIT_C_THETA_NORMALIZED can be converted to physical SI by this adapter"
            )

        kin = joint_state.congruence_kinematics
        velocity = joint_state.velocity_frames
        geometry = joint_state.geometry_state
        if kin.acceleration_polar3 is not None and type(kin.acceleration_polar3) is MissingComponent:
            acceleration = None
        elif kin.acceleration_polar3 is None:
            acceleration = None
        else:
            if kin.acceleration_normalization is not AccelerationNormalization.A_OVER_C_THETA:
                raise KinematicalStateError(
                    "canonical acceleration must declare A_OVER_C_THETA in explicit-c units"
                )
            acceleration = c * theta * finite_array(
                kin.acceleration_polar3, shape=(3,), name="canonical A/(c Theta)"
            )

        def component(value: object, name: str) -> np.ndarray | None:
            if type(value) is MissingComponent:
                return None
            return finite_array(value, shape=(3,), name=name)

        beta_rm = component(velocity.beta_RM, "canonical beta_RM")
        beta_mo = component(velocity.beta_MO, "canonical beta_MO")
        beta_ro = component(velocity.beta_RO, "canonical beta_RO")
        closure_residual = component(velocity.closure_residual, "canonical beta closure residual")
        sample = sample_id or f"canonical:{joint_state.content_id}"
        return cls(
            sample_id=sample,
            frame_id=joint_state.frame,
            congruence_id=joint_state.congruence,
            epoch_window_id=joint_state.epoch_window,
            basis_id=joint_state.basis,
            source_identity=joint_state.source_identity,
            sigma=theta * stf5_to_matrix(kin.sigma_stf5),
            omega=theta * finite_array(kin.omega_axial3, shape=(3,)),
            acceleration=acceleration,
            beta_RM=beta_rm,
            beta_MO=beta_mo,
            beta_RM_basis_id=None if beta_rm is None else velocity.basis,
            beta_MO_basis_id=None if beta_mo is None else velocity.basis,
            beta_RM_frame_id=None if beta_rm is None else velocity.coordinate_frame,
            beta_MO_frame_id=None if beta_mo is None else velocity.coordinate_frame,
            beta_RO=beta_ro,
            beta_RO_basis_id=None if beta_ro is None else velocity.basis,
            beta_RO_frame_id=None if beta_ro is None else velocity.coordinate_frame,
            beta_semantic_role=joint_state.beta_semantic_role.value,
            velocity_frame_ids=(
                velocity.radiation_frame_id,
                velocity.matter_frame_id,
                velocity.observer_frame_id,
            ),
            velocity_closure_status=velocity.status.value,
            velocity_closure_residual=closure_residual,
            velocity_truncation_remainder_bound=(
                None if type(velocity.truncation_remainder_bound) is MissingComponent
                else float(velocity.truncation_remainder_bound)
            ),
            canonical_state_id=joint_state.content_id,
            canonical_geometry_id=geometry.content_id,
            delta_omega_k=float(geometry.delta_omega_k),
            canonical_units_convention=joint_state.units_convention.value,
            H=theta / 3.0,
            perturbative_order=joint_state.perturbative_order,
        )

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
        beta_RM_frame_id: str | None = None,
        beta_MO_frame_id: str | None = None,
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
            beta_RM_frame_id=beta_RM_frame_id,
            beta_MO_frame_id=beta_MO_frame_id,
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
        value_statuses = {"AVAILABLE", "CONDITIONAL_FIRST_ORDER"}
        if self.status in value_statuses:
            if self.components is None:
                raise KinematicalStateError(f"{self.status} functional requires components")
            object.__setattr__(
                self, "components",
                finite_array(self.components, shape=(self.dimension,), name=self.functional_id),
            )
        elif self.components is not None:
            raise KinematicalStateError("non-available functional must not carry numerical components")


_REPRESENTATION_DIMENSIONS = {
    "STF2_POLAR": 5,
    "VECTOR_AXIAL": 3,
    "VECTOR_POLAR": 3,
    "SCALAR": 1,
    "PSEUDOSCALAR": 1,
    "NONNEGATIVE_SCALAR": 1,
}


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
    status: str | None = None,
    reason: str = "",
) -> FunctionalValue:
    if representation not in _REPRESENTATION_DIMENSIONS:
        raise KinematicalStateError(f"unregistered functional representation {representation!r}")
    resolved_status = ("UNAVAILABLE" if value is None else "AVAILABLE") if status is None else status
    if value is None:
        return FunctionalValue(
            functional_id, state.sample_id, state.canonical_state_id or state.state_id, representation,
            _REPRESENTATION_DIMENSIONS[representation], units, parity, basis_id,
            resolved_status, None, inputs, normalization_id,
            reason or "required component unavailable",
        )
    components = np.atleast_1d(np.asarray(value, dtype=float))
    return FunctionalValue(
        functional_id, state.sample_id, state.canonical_state_id or state.state_id, representation,
        int(components.size), units, parity, basis_id, resolved_status, components,
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
    source_frame = getattr(state, f"{name}_frame_id")
    if source_frame is None or source_frame != state.frame_id:
        return None, "RELATIVISTIC_FRAME_BRIDGE_REQUIRED"
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

    def _beta_reason(name: str, status: str) -> str:
        if status == "AVAILABLE":
            return ""
        if status == "UNAVAILABLE":
            return f"{name} unavailable"
        if status == "FRAME_TRANSPORT_REQUIRED":
            return f"explicit spatial basis transport for {name} is required"
        if status == "RELATIVISTIC_FRAME_BRIDGE_REQUIRED":
            return f"{name} uses a different component coordinate frame; a declared tetrad bridge is required"
        return f"{name} status is {status}"

    mixed_reason = _beta_reason("beta_RM", beta_rm_status)
    mixed_reason_mo = _beta_reason("beta_MO", beta_mo_status)

    # beta_RO is a derived first-order closure view. Preserve a separate
    # canonical beta_RO carrier and closure residual below.
    if beta_rm is None or beta_mo is None:
        closure_status = beta_rm_status if beta_rm is None else beta_mo_status
        closure_reason = mixed_reason or mixed_reason_mo or "both independent frame velocities are required"
        out.append(_value(state, "BETA_RO_FIRST_ORDER_VIEW", None,
                          representation="VECTOR_POLAR", units="1", parity="EVEN",
                          basis_id=state.basis_id, inputs=("beta_RM", "beta_MO"),
                          status=closure_status, reason=closure_reason))
    else:
        beta_ro_first_order = beta_rm + beta_mo
        if float(beta_ro_first_order @ beta_ro_first_order) >= 1.0:
            out.append(_value(state, "BETA_RO_FIRST_ORDER_VIEW", None,
                              representation="VECTOR_POLAR", units="1", parity="EVEN",
                              basis_id=state.basis_id, inputs=("beta_RM", "beta_MO"),
                              status="UNRESOLVED", reason="first-order sum reaches/exceeds the subluminal boundary"))
        else:
            out.append(_value(state, "BETA_RO_FIRST_ORDER_VIEW", beta_ro_first_order,
                              representation="VECTOR_POLAR", units="1", parity="EVEN",
                              basis_id=state.basis_id, inputs=("beta_RM", "beta_MO"),
                              normalization_id="FIRST_ORDER_CLOSURE_ONLY",
                              status="CONDITIONAL_FIRST_ORDER",
                              reason="first-order closure view only; not exact relativistic velocity composition"))

    if state.beta_RO is None:
        out.append(_value(state, "BETA_RO_CANONICAL_VIEW", None,
                          representation="VECTOR_POLAR", units="1", parity="EVEN",
                          basis_id=state.basis_id, inputs=("canonical_velocity_frames.beta_RO",),
                          status="UNAVAILABLE", reason="canonical beta_RO component is unavailable"))
    else:
        closure_status = state.velocity_closure_status or "UNASSESSED"
        out.append(_value(state, "BETA_RO_CANONICAL_VIEW", state.beta_RO,
                          representation="VECTOR_POLAR", units="1", parity="EVEN",
                          basis_id=state.beta_RO_basis_id or state.basis_id,
                          inputs=("canonical_velocity_frames.beta_RO", "canonical_closure_status"),
                          normalization_id="CANONICAL_VFB_RECORDED_CLOSURE_VIEW",
                          status="AVAILABLE",
                          reason=f"canonical VelocityFrameBundle carrier; recorded first-order closure status: {closure_status}; beta_RO is not an independent coordinate"))
    out.append(_value(state, "BETA_CLOSURE_RESIDUAL",
                      state.velocity_closure_residual,
                      representation="VECTOR_POLAR", units="1", parity="EVEN",
                      basis_id=state.basis_id,
                      inputs=("canonical_velocity_frames.closure_residual",),
                      normalization_id="FIRST_ORDER_CLOSURE_DIAGNOSTIC",
                      status=None if state.velocity_closure_residual is not None else "UNAVAILABLE",
                      reason="" if state.velocity_closure_residual is not None else "canonical closure residual unavailable"))
    out.append(_value(state, "DELTA_OMEGA_K_PHYSICAL_VIEW",
                      None if state.delta_omega_k is None else np.array([state.delta_omega_k]),
                      representation="SCALAR", units="1", parity="EVEN",
                      basis_id=state.basis_id,
                      inputs=("canonical_geometry_state.delta_omega_k",),
                      normalization_id="SIGNED_CURVATURE_BUDGET_DEPARTURE",
                      status=None if state.delta_omega_k is not None else "UNAVAILABLE",
                      reason="" if state.delta_omega_k is not None else "geometry state unavailable"))

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

    if sigma is None:
        mixed_status, mixed_reason2 = "UNAVAILABLE", "sigma_AB unavailable"
    elif beta_rm is None:
        mixed_status = beta_rm_status
        mixed_reason2 = mixed_reason or "beta_RM unavailable"
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

    if omega is None:
        mixed_status, mixed_reason2 = "UNAVAILABLE", "omega_A unavailable"
    elif beta_rm is None:
        mixed_status = beta_rm_status
        mixed_reason2 = mixed_reason or "beta_RM unavailable"
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

    if acceleration is None:
        mixed_status, mixed_reason2 = "UNAVAILABLE", "A_A unavailable"
    elif beta_mo is None:
        mixed_status = beta_mo_status
        mixed_reason2 = mixed_reason_mo or "beta_MO unavailable"
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
        status, reason = "UNDEFINED", "H=0; H-normalized axial-vector norm is undefined"
    else:
        status, reason = "AVAILABLE", ""
    out.append(_value(state, "OMEGA_VECTOR_NORM2_H",
                      None if status != "AVAILABLE" else np.array([omega @ omega / (6.0 * H**2)]),
                      representation="NONNEGATIVE_SCALAR", units="1", parity="EVEN",
                      basis_id=state.basis_id, inputs=("omega_A", "H"),
                      normalization_id="OMEGA_VECTOR_NORM_SQUARED_OVER_H2", status=status, reason=reason))

    return tuple(out)


@dataclass(frozen=True)
class LocalOpticalPrediction:
    """Leading local radial-rate and angular-drift predictions for one state."""

    state_id: str
    direction_basis_id: str
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
        _nonempty(self.direction_basis_id, "direction_basis_id")
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
    direction_basis_id: str,
    triad_rotation: Sequence[float] | None,
    triad_rotation_basis_id: str | None,
    basis_transport: FrameTransport | None = None,
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
    _nonempty(direction_basis_id, "direction_basis_id")
    c = _finite_scalar(speed_of_light, "speed_of_light")
    k = _finite_scalar(clock_scale, "clock_scale")
    if c <= 0.0 or k <= 0.0:
        raise KinematicalStateError("c and clock_scale must be positive")

    sigma = state.sigma
    omega = state.omega
    acceleration = state.acceleration
    if state.basis_id != direction_basis_id:
        if basis_transport is None:
            raise KinematicalStateError("explicit state-to-direction basis transport is required")
        if (basis_transport.source_basis_id, basis_transport.target_basis_id) != (state.basis_id, direction_basis_id):
            raise KinematicalStateError("basis_transport does not map the state basis to the direction basis")
        if sigma is not None:
            sigma = basis_transport.matrix @ sigma @ basis_transport.matrix.T
        if omega is not None:
            omega = basis_transport.axial(omega)
        if acceleration is not None:
            acceleration = basis_transport.polar(acceleration)
    elif basis_transport is not None:
        raise KinematicalStateError("basis_transport supplied although state and direction bases already match")

    if triad_rotation is None:
        if triad_rotation_basis_id is not None:
            raise KinematicalStateError("triad_rotation_basis_id supplied without triad_rotation")
        rotation = None
    else:
        _nonempty(triad_rotation_basis_id, "triad_rotation_basis_id")
        if triad_rotation_basis_id != direction_basis_id:
            raise KinematicalStateError("triad rotation must be expressed in the direction basis")
        rotation = finite_array(triad_rotation, shape=(3,), name="triad_rotation")

    radial = None
    if state.H is not None and sigma is not None and acceleration is not None:
        radial = state.H + np.einsum("ni,ij,nj->n", n, sigma, n) - (n @ acceleration) / c
        radial_status = "AVAILABLE_LOCAL_OPTICAL_RATE"
    else:
        radial_status = "UNAVAILABLE_REQUIRED_H_SIGMA_OR_ACCELERATION"

    fermi = None
    catalogue = None
    if sigma is None or omega is None:
        transverse_status = "UNAVAILABLE_REQUIRED_SIGMA_OR_VORTICITY"
    else:
        sigma_n = np.einsum("ij,nj->ni", sigma, n)
        sigma_n = sigma_n - n * np.einsum("ni,ni->n", n, sigma_n)[:, None]
        fermi = sigma_n + np.cross(n, omega[None, :])
        if rotation is None:
            transverse_status = "TRIAD_ROTATION_UNAVAILABLE_CATALOGUE_B1_UNRESOLVED"
        else:
            catalogue = k * (sigma_n + np.cross(n, (omega + rotation)[None, :]))
            transverse_status = "AVAILABLE_WITH_EXPLICIT_TRIAD_ROTATION_AND_CLOCK"
    return LocalOpticalPrediction(
        state_id=state.state_id,
        direction_basis_id=direction_basis_id,
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
    frame_id: str
    congruence_id: str
    basis_id: str
    parameter_names: tuple[str, ...]
    parameter_units: tuple[str, ...]
    row_labels: tuple[str, ...]
    observable_units: tuple[str, ...]
    scope: str = "IDEAL_LOCAL_OPTICAL_MAP_PRE_SELECTION_PRE_WHITENING"

    def __post_init__(self) -> None:
        _nonempty(self.frame_id, "frame_id")
        _nonempty(self.congruence_id, "congruence_id")
        _nonempty(self.basis_id, "basis_id")
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
    frame_id: str,
    congruence_id: str,
    basis_id: str,
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
        frame_id=frame_id,
        congruence_id=congruence_id,
        basis_id=basis_id,
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
        beta_RM_frame_id=state.beta_RM_frame_id,
        beta_MO_frame_id=state.beta_MO_frame_id,
        beta_RO=None if state.beta_RO is None else R @ state.beta_RO,
        beta_RO_basis_id=None if state.beta_RO is None else new_basis_id,
        beta_RO_frame_id=state.beta_RO_frame_id,
        beta_semantic_role=state.beta_semantic_role,
        velocity_frame_ids=state.velocity_frame_ids,
        velocity_closure_status=state.velocity_closure_status,
        velocity_closure_residual=None if state.velocity_closure_residual is None else R @ state.velocity_closure_residual,
        velocity_truncation_remainder_bound=state.velocity_truncation_remainder_bound,
        canonical_state_id=state.canonical_state_id,
        canonical_geometry_id=state.canonical_geometry_id,
        delta_omega_k=state.delta_omega_k,
        canonical_units_convention=state.canonical_units_convention,
        H=state.H,
        perturbative_order=state.perturbative_order,
        units_convention=state.units_convention,
    )



_CANONICAL_OPERATOR_IDENTITIES = (
    (TensorFunctionalOperator.SIGMA_STF5, "SIGMA_THETA_STF5", "SIGMA_OVER_THETA_STF5"),
    (TensorFunctionalOperator.OMEGA_AXIAL3, "OMEGA_THETA_AXIAL3", "OMEGA_OVER_THETA_AXIAL3"),
    (TensorFunctionalOperator.ACCELERATION_POLAR3, "ACCELERATION_C_THETA_POLAR3", "A_OVER_C_THETA"),
    (TensorFunctionalOperator.BETA_RM_POLAR3, "BETA_RM_POLAR3", "BETA_EQUALS_V_OVER_C"),
    (TensorFunctionalOperator.BETA_MO_POLAR3, "BETA_MO_POLAR3", "BETA_EQUALS_V_OVER_C"),
    (TensorFunctionalOperator.BETA_RO_POLAR3, "BETA_RO_POLAR3", "BETA_EQUALS_V_OVER_C"),
    (TensorFunctionalOperator.DELTA_OMEGA_K, "DELTA_OMEGA_K", "DIMENSIONLESS_SIGNED_BUDGET"),
    (TensorFunctionalOperator.TR_SIGMA2, "SIGMA_NORM2_THETA", "SIGMA_OVER_THETA_STF5"),
    (TensorFunctionalOperator.TR_SIGMA3, "SIGMA_CUBIC_THETA", "SIGMA_OVER_THETA_STF5"),
    (TensorFunctionalOperator.OMEGA2, "OMEGA_NORM2_THETA", "OMEGA_OVER_THETA_AXIAL3"),
    (TensorFunctionalOperator.BETA_RM2, "BETA_RM_NORM2", "BETA_EQUALS_V_OVER_C"),
    (TensorFunctionalOperator.BETA_RM_DOT_OMEGA, "BETA_RM_DOT_OMEGA_THETA", "BETA_EQUALS_V_OVER_C_X_OMEGA_OVER_THETA"),
    (TensorFunctionalOperator.BETA_RM_SIGMA_BETA_RM, "BETA_RM_SIGMA_BETA_RM_THETA", "BETA_EQUALS_V_OVER_C_X_SIGMA_OVER_THETA"),
)


def evaluate_canonical_tensor_functionals(
    joint_state: JointAnisotropyState,
    *,
    branch: str = "R39_CANONICAL_TENSOR_FUNCTIONAL_ADAPTER_V1",
    anchor_ids: Mapping[str, str] | None = None,
    anchors: Mapping[str, object] | None = None,
) -> tuple[TensorFunctionalResult, ...]:
    """Evaluate the existing HTT TensorFunctionalSpec/Result registry.

    The canonical JointAnisotropyState remains the sole source state. This
    adapter only declares/evaluates already registered v1 operators. New R39
    mixed functionals that are not in that closed operator vocabulary remain
    in the typed R39 functional registry and are not smuggled into v1.
    """
    if type(joint_state) is not JointAnisotropyState:
        raise TypeError("joint_state must be an exact canonical JointAnisotropyState")
    anchor_id_map = {} if anchor_ids is None else dict(anchor_ids)
    anchor_map = {} if anchors is None else dict(anchors)
    unknown_anchor_keys = set(anchor_map) - set(anchor_id_map.values())
    if unknown_anchor_keys:
        raise KinematicalStateError(
            "every supplied anchor must be named by one declared anchor_id"
        )
    results: list[TensorFunctionalResult] = []
    for operator, functional_id, normalization in _CANONICAL_OPERATOR_IDENTITIES:
        anchor_id = anchor_id_map.get(functional_id)
        spec = build_tensor_functional_spec(
            functional_id=functional_id,
            operator=operator,
            frame=joint_state.frame,
            congruence=joint_state.congruence,
            epoch_window=joint_state.epoch_window,
            averaging_scale=joint_state.averaging_scale,
            normalization=normalization,
            perturbative_order=joint_state.perturbative_order,
            branch=branch,
            anchor_id=anchor_id,
        )
        result = evaluate_tensor_functional(
            joint_state,
            spec,
            anchor=anchor_map.get(anchor_id) if anchor_id is not None else None,
        )
        if result.source_state_id != joint_state.content_id:
            raise KinematicalStateError(
                "canonical TensorFunctionalResult lost the source JointAnisotropyState identity"
            )
        results.append(result)
    return tuple(results)


@dataclass(frozen=True)
class KinematicalXBundle:
    """One x bundle combining canonical tensor results and physical-SI views."""

    canonical_state_id: str
    physical_view_state_id: str
    expansion_scalar: float
    speed_of_light: float
    canonical_functionals: tuple[TensorFunctionalResult, ...]
    physical_functionals: tuple[FunctionalValue, ...]

    def __post_init__(self) -> None:
        _nonempty(self.canonical_state_id, "canonical_state_id")
        _nonempty(self.physical_view_state_id, "physical_view_state_id")
        theta = _finite_scalar(self.expansion_scalar, "expansion_scalar")
        c = _finite_scalar(self.speed_of_light, "speed_of_light")
        if theta == 0.0 or c <= 0.0:
            raise KinematicalStateError("expansion_scalar must be nonzero and c positive")
        canonical = tuple(self.canonical_functionals)
        physical = tuple(self.physical_functionals)
        if any(type(value) is not TensorFunctionalResult for value in canonical):
            raise KinematicalStateError("canonical_functionals must be TensorFunctionalResult objects")
        if any(type(value) is not FunctionalValue for value in physical):
            raise KinematicalStateError("physical_functionals must be FunctionalValue objects")
        if any(value.source_state_id != self.canonical_state_id for value in canonical):
            raise KinematicalStateError("canonical functional escaped its JointAnisotropyState identity")
        if any(value.state_id != self.canonical_state_id for value in physical):
            raise KinematicalStateError("physical functional escaped its JointAnisotropyState identity")
        identifiers = [value.spec.functional_id for value in canonical]
        identifiers.extend(value.functional_id for value in physical)
        if len(identifiers) != len(set(identifiers)):
            raise KinematicalStateError("x functional IDs must be unique across both representations")
        object.__setattr__(self, "expansion_scalar", theta)
        object.__setattr__(self, "speed_of_light", c)
        object.__setattr__(self, "canonical_functionals", canonical)
        object.__setattr__(self, "physical_functionals", physical)


def build_kinematical_x_bundle(
    joint_state: JointAnisotropyState,
    *,
    expansion_scalar: float,
    speed_of_light: float = _C0,
    sample_id: str | None = None,
    frame_transports: Mapping[tuple[str, str], FrameTransport] | None = None,
    anchor_ids: Mapping[str, str] | None = None,
    anchors: Mapping[str, object] | None = None,
) -> KinematicalXBundle:
    """Build x from one canonical state, never from parallel parameter copies.

    canonical_functionals retain the registered theta-normalized HTT
    operators and their TensorFunctionalSpec/Result authority. The physical
    functionals are explicit-SI direct/mixed views derived from the same
    canonical_state_id after supplying Theta=3H and c. No likelihood term is
    formed here; this is the typed x construction stage.
    """
    if type(joint_state) is not JointAnisotropyState:
        raise TypeError("joint_state must be an exact canonical JointAnisotropyState")
    theta = _finite_scalar(expansion_scalar, "expansion_scalar")
    c = _finite_scalar(speed_of_light, "speed_of_light")
    view = KinematicalState.from_joint_anisotropy_state(
        joint_state,
        expansion_scalar=theta,
        speed_of_light=c,
        sample_id=sample_id,
    )
    physical_values = evaluate_kinematical_functionals(
        view,
        speed_of_light=c,
        frame_transports=frame_transports,
    )
    canonical_values = evaluate_canonical_tensor_functionals(
        joint_state,
        anchor_ids=anchor_ids,
        anchors=anchors,
    )
    return KinematicalXBundle(
        canonical_state_id=joint_state.content_id,
        physical_view_state_id=view.state_id,
        expansion_scalar=theta,
        speed_of_light=c,
        canonical_functionals=canonical_values,
        physical_functionals=physical_values,
    )


__all__ = [
    "FrameTransport",
    "FunctionalValue",
    "KinematicalState",
    "KinematicalStateError",
    "KinematicalXBundle",
    "LocalOpticalPrediction",
    "OpticalJacobian",
    "evaluate_canonical_tensor_functionals",
    "evaluate_kinematical_functionals",
    "build_kinematical_x_bundle",
    "local_optical_jacobian",
    "local_optical_response",
    "stf2_components",
    "stf2_from_components",
    "transform_state_o3",
]
