"""GBI-05: Source-bound general tilted Bianchi multi-probe likelihood & single-posterior five-view.

Implements the R49 unified multi-probe tensor likelihood and single-posterior
HTT `(x, Q, Pi, F, G_F)` pushforward under strict preflight & claim boundaries:

Fail-Closed Guards (Acceptance Tests 9, 11, 12)
-----------------------------------------------
  * ``MissingTriadError``: missing or non-SO(3) common spatial triad across probes.
  * ``EpochMismatchError``: conflating observer `z=0` velocity (`beta_MO`) with
    recombination `z_* ~ 1090` radiation velocity (`v_rad`), or mismatched epochs.
  * ``DoubleCountedLowEllError``: evaluating both deterministic low-ell CMB
    template `mu(theta)` and signal covariance perturbation `Sigma(theta)` on
    the same `(ell, m)` modes.
  * ``ScalarSpeedError``: passing scalar `|beta|` or `x_C` in place of 3-vector
    congruence velocities in `R^3`.
  * ``UnmarginalizedGaiaSpinError``: fixing Gaia CRF3 VSH `B_1` frame spin
    `Omega_triad` instead of analytically/explicitly marginalizing over it.
  * ``SplitPosteriorFiveViewError``: attempting to compute `(x, Q, Pi, F, G_F)`
    from separate/split posterior draw sets rather than one joint posterior.
  * ``LaneContaminationError``: mixing Planck PR3 FFP10 simulation products with
    NPIPE PR4 observed maps (violating lane isolation).

Probes Coupled on Common Triad + ``G_STF5 = diag(4/3, 4, 4, 4, 4)``
-------------------------------------------------------------------
  ``CMB``, ``Quaia``, ``NVSS``, ``RACS``, ``Gaia+ICRF``, ``Pantheon+``,
  ``CF4``, and ``DESI`` (each empirical carrier bound to local source files).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence

import numpy as np
import scipy.linalg

from bass.background.convention_bridge import ALL_TWELVE_FAMILIES
from bass.transport.general_bianchi_transfer import (
    TRANSFER_MODE_GEODESIC,
    TRANSFER_MODE_LINEARIZED,
    TiltedTransferParameters,
    compute_general_bianchi_transfer,
)
from common.full_observable_x_bundle import build_full_observable_x_bundle
from common.htt_five_variable_state import (
    AnchorBody,
    DepthPathGF,
    DirectionalSupportProfile,
    ExceedanceSurface,
    HTTFiveVariableState,
    construct_r42_five_variable_state,
    fibonacci_sphere_directions,
)
from common.joint_anisotropy_state_v1 import (
    AccelerationNormalization,
    BetaSemanticRole,
    CongruenceKinematics,
    GeometryState,
    JointAnisotropyState,
    JointStateSourceKind,
    UnitsConvention,
    VelocityNormalization,
    build_velocity_frame_bundle,
)
from common.relativistic_velocity_closure import (
    compose_and_close_velocities,
    compose_velocities_sr,
    kinematic_quadrupole_stf2,
)
from common.stf_metric_bridge import (
    G_STF5,
    G_STF5_INV,
    cartesian_to_orthonormal,
    cartesian_to_stf_matrix,
    orthonormal_to_cartesian,
    stf_matrix_to_cartesian,
)
from common.transfer_registry import TransferSource
from htt.htt.infer.tensor_five_variable_inference import (
    PARAM_NAMES_17,
    params_to_kinematic_model,
)
from htt.htt.infer.tensor_joint_multiprobe_likelihood import (
    PsiCosmology,
    SchurMarginalizer,
)

try:
    from cobaya.likelihood import Likelihood as _CobayaLikelihood
except Exception:  # pragma: no cover - optional runtime fallback
    class _CobayaLikelihood:  # type: ignore[no-redef]
        def __init__(self, info=None, **kwargs):
            pass


# ICRS (J2000 equatorial) -> Galactic IAU 1958 orthonormal rotation matrix (det = +1)
ICRS_TO_GALACTIC_MATRIX: np.ndarray = np.array(
    [
        [-0.0548755604162154, -0.8734370902348850, -0.4838350155487132],
        [+0.4941094278755837, -0.4448296299600112, +0.7469822444972189],
        [-0.8676661490190047, -0.1980763734312015, +0.4559837761750669],
    ],
    dtype=np.float64,
)
GALACTIC_TO_ICRS_MATRIX: np.ndarray = ICRS_TO_GALACTIC_MATRIX.T.copy()
SPEED_OF_LIGHT_KM_S: float = 299_792.458
T_CMB_K: float = 2.7255
DEFAULT_PROBES: tuple[str, ...] = ("CMB", "Quaia", "NVSS", "RACS", "Gaia", "PantheonPlus", "CF4", "DESI")


# -----------------------------------------------------------------------------
# Fail-Closed Preflight Exceptions
# -----------------------------------------------------------------------------


class MissingTriadError(ValueError):
    """Raised when common spatial triad or SO(3) probe frame alignment is absent or invalid."""


class EpochMismatchError(ValueError):
    """Raised when local z=0 observer velocity is conflated with z_* emission congruence tilt."""


class DoubleCountedLowEllError(ValueError):
    """Raised when low-ell CMB modes carry both deterministic template mu and excess covariance Sigma."""


class ScalarSpeedError(ValueError):
    """Raised when a scalar speed replaces required 3-vector congruence velocities."""


class UnmarginalizedGaiaSpinError(ValueError):
    """Raised when Gaia VSH frame spin Omega_triad is left fixed instead of marginalized."""


class SplitPosteriorFiveViewError(ValueError):
    """Raised when (x, Q, Pi, F, G_F) are constructed from separate posteriors rather than one joint draw set."""


class LaneContaminationError(ValueError):
    """Raised when PR3 FFP10 simulation products are mixed with NPIPE PR4 observed maps."""


# -----------------------------------------------------------------------------
# Preflight & Parameter Contracts
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class CMBModeBudgetSpec:
    """Explicit partition of low-ell CMB modes between deterministic `mu` and `Sigma`."""

    ell_min: int = 2
    ell_max: int = 6
    deterministic_ells: tuple[int, ...] = (2, 3, 4)
    covariance_ells: tuple[int, ...] = (5, 6)
    lane: Literal["PR3_CALIBRATED", "NPIPE_PR4_ROBUSTNESS"] = "PR3_CALIBRATED"
    mc_source: Literal["FFP10_PR3", "PR4_RINGHALF_NOISE_ONLY", "PR4_NULL_NOT_FORMABLE"] = "FFP10_PR3"
    transfer_mode: Literal["linearized_near_flrw", "exact_geodesic_background"] = TRANSFER_MODE_LINEARIZED
    use_polarized_eb: bool = True

    def __post_init__(self) -> None:
        if int(self.ell_min) < 2 or int(self.ell_max) < int(self.ell_min):
            raise ValueError(f"Invalid ell range [{self.ell_min}, {self.ell_max}]")
        overlap = set(self.deterministic_ells).intersection(set(self.covariance_ells))
        if overlap:
            raise DoubleCountedLowEllError(
                f"Low-ell double-counting detected on multipoles {sorted(overlap)}: "
                f"modes cannot enter both deterministic template mu(theta) and excess covariance Sigma(theta)."
            )
        for ell in (*self.deterministic_ells, *self.covariance_ells):
            if ell < int(self.ell_min) or ell > int(self.ell_max):
                raise ValueError(f"Declared multipole {ell} outside budget [{self.ell_min}, {self.ell_max}]")
        if self.lane == "NPIPE_PR4_ROBUSTNESS" and self.mc_source == "FFP10_PR3":
            raise LaneContaminationError(
                "Lane contamination blocked: NPIPE PR4 robustness maps MUST NEVER pair with PR3 FFP10 sims."
            )
        if self.lane == "PR3_CALIBRATED" and self.mc_source != "FFP10_PR3":
            raise LaneContaminationError(
                f"PR3 calibrated lane requires matched FFP10_PR3 sims, got {self.mc_source!r}."
            )


@dataclass(frozen=True)
class FrameEpochAlignmentSpec:
    """Common 3D triad, epoch separation, Gaia spin marginalization, and vector-tilt contract."""

    triad_frame: Literal["galactic", "icrs"] = "galactic"
    triad_rotation: np.ndarray | None = None
    cmb_emission_epoch_z: float = 1090.0
    observer_epoch_z: float = 0.0
    allow_epoch_conflation: bool = False
    marginalize_gaia_spin: bool = True
    gaia_spin_prior_sigma_uasyr: float = 200.0
    require_vector_tilt: bool = True

    def __post_init__(self) -> None:
        if self.triad_rotation is None:
            raise MissingTriadError(
                "Missing common 3D spatial triad rotation matrix (e_1, e_2, e_3); pass explicit 3x3 SO(3)."
            )
        R = np.asarray(self.triad_rotation, dtype=np.float64)
        if R.shape != (3, 3) or not np.all(np.isfinite(R)):
            raise MissingTriadError(f"Common spatial triad must have finite shape (3, 3), got {R.shape}")
        ortho_err = float(np.max(np.abs(R.T @ R - np.eye(3))))
        det = float(np.linalg.det(R))
        if ortho_err > 1.0e-10 or abs(det - 1.0) > 1.0e-10:
            raise MissingTriadError(
                f"Triad must lie in SO(3): ortho_err={ortho_err:.3e}, det={det:.6f}"
            )
        if self.allow_epoch_conflation or abs(float(self.cmb_emission_epoch_z) - float(self.observer_epoch_z)) < 10.0:
            raise EpochMismatchError(
                f"Epoch separation violated: emission z={self.cmb_emission_epoch_z} cannot be conflated "
                f"with local observer z={self.observer_epoch_z}."
            )
        if not self.marginalize_gaia_spin:
            raise UnmarginalizedGaiaSpinError(
                "Gaia CRF3 VSH B1 frame spin Omega_triad MUST be marginalized; unmarginalized evaluation rejected."
            )
        if not self.require_vector_tilt:
            raise ScalarSpeedError("Scalar-only tilt mode is forbidden under R49 general tilted Bianchi contract.")


def _validate_vec3(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != 1 or arr.shape != (3,):
        raise ScalarSpeedError(
            f"{name} must be a 3-vector in R^3 (shape (3,)), not scalar/shape {arr.shape}."
        )
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must contain finite entries.")
    return arr


@dataclass(frozen=True)
class R49JointState:
    """Unified R49 general tilted Bianchi state `(theta_G, theta_F, theta_O, psi)`.

    Separates:
      * ``sigma_AB_stf5`` (5D Cartesian STF shear/H_0 in G_STF5 metric),
      * ``omega_A`` (3D cosmic vorticity/H_0),
      * ``A_A`` (3D Class-B curvature/acceleration vector/H_0),
      * ``v_matter`` (3D normal-to-matter congruence velocity),
      * ``v_rad`` (3D normal-to-radiation velocity at last scattering z_*),
      * ``beta_MO`` (3D matter-to-observer peculiar velocity at z=0),
      * ``psi`` ([H_0, Omega_m, r_d, DeltaOmega_k]).
    """

    family: str
    sigma_AB_stf5: np.ndarray
    omega_A: np.ndarray
    A_A: np.ndarray
    v_matter: np.ndarray
    v_rad: np.ndarray
    beta_MO: np.ndarray
    psi: PsiCosmology = field(default_factory=PsiCosmology)
    h_bianchi: float = 0.25
    omega_k: float = 0.0
    handedness: int = 1

    def __post_init__(self) -> None:
        if self.family not in ALL_TWELVE_FAMILIES:
            raise ValueError(f"Unknown family {self.family!r}; expected one of {ALL_TWELVE_FAMILIES}")
        s5 = np.asarray(self.sigma_AB_stf5, dtype=np.float64)
        if s5.shape != (5,) or not np.all(np.isfinite(s5)):
            raise ValueError(f"sigma_AB_stf5 must have finite shape (5,), got {s5.shape}")
        om = _validate_vec3(self.omega_A, "omega_A")
        aa = _validate_vec3(self.A_A, "A_A")
        vm = _validate_vec3(self.v_matter, "v_matter")
        vr = _validate_vec3(self.v_rad, "v_rad")
        mo = _validate_vec3(self.beta_MO, "beta_MO")
        for nm, v in (("v_matter", vm), ("v_rad", vr), ("beta_MO", mo)):
            if float(v @ v) >= 1.0:
                raise ValueError(f"{nm} violates subluminal |v| < 1 bound.")
        object.__setattr__(self, "sigma_AB_stf5", s5.copy())
        object.__setattr__(self, "omega_A", om.copy())
        object.__setattr__(self, "A_A", aa.copy())
        object.__setattr__(self, "v_matter", vm.copy())
        object.__setattr__(self, "v_rad", vr.copy())
        object.__setattr__(self, "beta_MO", mo.copy())

    @property
    def sigma_matrix(self) -> np.ndarray:
        return cartesian_to_stf_matrix(self.sigma_AB_stf5)

    @property
    def sigma_frobenius_norm(self) -> float:
        return float(math.sqrt(max(0.0, float(self.sigma_AB_stf5 @ G_STF5 @ self.sigma_AB_stf5))))

    @property
    def beta_RM(self) -> np.ndarray:
        """Radiation relative to matter velocity at last scattering via SR composition."""
        return compose_velocities_sr(-self.v_matter, self.v_rad)

    @property
    def beta_RO(self) -> np.ndarray:
        """Exact SR-composed radiation-to-observer dipole velocity."""
        return compose_velocities_sr(self.beta_RM, self.beta_MO)

    def to_vector24(self) -> np.ndarray:
        return np.concatenate(
            [
                self.sigma_AB_stf5,  # 0:5
                self.omega_A,        # 5:8
                self.A_A,            # 8:11
                self.v_matter,       # 11:14
                self.v_rad,          # 14:17
                self.beta_MO,        # 17:20
                self.psi.to_vector(),  # 20:24
            ]
        ).astype(np.float64)

    def rotated_by(self, R: np.ndarray) -> "R49JointState":
        """Return a copy of the state active-rotated by `R in SO(3)`."""
        R_mat = np.asarray(R, dtype=np.float64)
        return R49JointState(
            family=self.family,
            sigma_AB_stf5=_rotate_stf5_cartesian(self.sigma_AB_stf5, R_mat),
            omega_A=R_mat @ self.omega_A,
            A_A=R_mat @ self.A_A,
            v_matter=R_mat @ self.v_matter,
            v_rad=R_mat @ self.v_rad,
            beta_MO=R_mat @ self.beta_MO,
            psi=self.psi,
            h_bianchi=self.h_bianchi,
            omega_k=self.omega_k,
            handedness=self.handedness,
        )

    @classmethod
    def from_vector24(
        cls,
        vec: Sequence[float],
        *,
        family: str = "VII_h",
        h_bianchi: float = 0.25,
        omega_k: float = 0.0,
        handedness: int = 1,
    ) -> "R49JointState":
        arr = np.asarray(vec, dtype=np.float64)
        if arr.shape != (24,):
            raise ValueError(f"Expected 24-vector, got shape {arr.shape}")
        return cls(
            family=family,
            sigma_AB_stf5=arr[0:5],
            omega_A=arr[5:8],
            A_A=arr[8:11],
            v_matter=arr[11:14],
            v_rad=arr[14:17],
            beta_MO=arr[17:20],
            psi=PsiCosmology.from_vector(arr[20:24]),
            h_bianchi=h_bianchi,
            omega_k=omega_k,
            handedness=handedness,
        )


PARAM_NAMES_24: tuple[str, ...] = (
    "sigma_xx",
    "sigma_yy",
    "sigma_xy",
    "sigma_xz",
    "sigma_yz",
    "omega_x",
    "omega_y",
    "omega_z",
    "A_x",
    "A_y",
    "A_z",
    "vm_x",
    "vm_y",
    "vm_z",
    "vr_x",
    "vr_y",
    "vr_z",
    "bmo_x",
    "bmo_y",
    "bmo_z",
    "H_0",
    "Omega_m",
    "r_d",
    "DeltaOmega_k",
)


# -----------------------------------------------------------------------------
# Empirical Probe Carriers & Multi-Probe Evaluation
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class CMBCarrierData:
    """Observed low-ell CMB real-harmonic data vector & matched covariance."""

    ells: tuple[int, ...]
    mode_labels: tuple[str, ...]  # e.g. ("T_2_0", "T_2_1r", ..., "E_2_0", ..., "B_2_0", ...)
    d_obs: np.ndarray
    cov: np.ndarray
    lane: Literal["PR3_CALIBRATED", "NPIPE_PR4_ROBUSTNESS"]
    mc_source: Literal["FFP10_PR3", "PR4_RINGHALF_NOISE_ONLY", "PR4_NULL_NOT_FORMABLE"]
    coordinate_frame: Literal["galactic", "icrs"] = "galactic"
    provenance_path: str = ""
    provenance_sha256: str = ""
    n_mc: int = 0

    def __post_init__(self) -> None:
        d = np.asarray(self.d_obs, dtype=np.float64)
        C = np.asarray(self.cov, dtype=np.float64)
        if d.ndim != 1 or C.shape != (len(d), len(d)):
            raise ValueError(f"CMBCarrierData shape mismatch: d={d.shape}, cov={C.shape}")
        if self.lane == "NPIPE_PR4_ROBUSTNESS" and self.mc_source == "FFP10_PR3":
            raise LaneContaminationError("NPIPE PR4 carrier cannot carry PR3 FFP10 mc_source.")


@dataclass(frozen=True)
class DipoleCarrierData:
    """Source-bound 3D dipole observation carrier (Quaia, NVSS, RACS)."""

    probe_name: str
    d_obs: np.ndarray           # (3,) dimensionless count dipole
    cov: np.ndarray             # (3, 3) clustering + shot-noise covariance
    c_eb: float                 # Ellis-Baldwin response factor 2 + x(1 + alpha)
    coordinate_frame: Literal["galactic", "icrs"] = "galactic"
    z_eff: float = 1.0
    n_sources: int = 0
    provenance_path: str = ""
    provenance_sha256: str = ""

    def __post_init__(self) -> None:
        if self.d_obs.shape != (3,) or self.cov.shape != (3, 3):
            raise ValueError(f"[{self.probe_name}] Dipole shapes invalid: {self.d_obs.shape}, {self.cov.shape}")


@dataclass(frozen=True)
class GaiaVSHCarrierData:
    """Source-bound Gaia DR3+ICRF3 astrometric VSH modes (E1 glide, B1 spin, E2 shear) in uas/yr."""

    e1_obs: np.ndarray          # (3,) electric dipole uas/yr
    b1_obs: np.ndarray          # (3,) magnetic dipole (frame spin + cosmic vorticity) uas/yr
    e2_obs: np.ndarray          # (5,) Cartesian STF5 electric quadrupole uas/yr
    cov_e1b1e2: np.ndarray      # (11, 11) full joint covariance in [E1(3), B1(3), E2(5)]
    coordinate_frame: Literal["galactic", "icrs"] = "galactic"
    z_eff: float = 1.2
    n_sources: int = 0
    provenance_path: str = ""
    provenance_sha256: str = ""


@dataclass(frozen=True)
class PantheonCarrierData:
    """Compressed or full Pantheon+ SNe Ia magnitude/redshift/direction empirical carrier."""

    z_hd: np.ndarray
    z_hel: np.ndarray
    n_hat_gal: np.ndarray       # (N_sn, 3) unit directions in Galactic coordinates
    m_b_obs: np.ndarray         # (N_sn,)
    cov: np.ndarray             # (N_sn, N_sn) STAT+SYS covariance
    provenance_path: str = ""
    provenance_sha256: str = ""


@dataclass(frozen=True)
class CF4TomographicCarrierData:
    """CF4 peculiar velocity bulk flow across depth shells (km/s)."""

    shell_z_bins: tuple[tuple[float, float], ...]
    d_obs: np.ndarray           # (3 * n_shells,) stacked bulk flow vectors in km/s
    cov: np.ndarray             # (3 * n_shells, 3 * n_shells) cross-shell covariance
    coordinate_frame: Literal["galactic", "icrs"] = "galactic"
    provenance_path: str = ""
    provenance_sha256: str = ""


@dataclass(frozen=True)
class DESIBAOAndDirectionalCarrierData:
    """DESI DR2 BAO distances + DR1 NGC/SGC directional anisotropy carrier."""

    bao_z: np.ndarray
    bao_quantities: tuple[str, ...]  # ("DV_over_rs", "DM_over_rs", "DH_over_rs")
    bao_mean: np.ndarray
    bao_cov: np.ndarray
    directional_quad_obs: np.ndarray     # (5,) STF5 anisotropy from NGC-SGC
    directional_quad_cov: np.ndarray     # (5, 5)
    coordinate_frame: Literal["galactic", "icrs"] = "galactic"
    provenance_path: str = ""


@dataclass(frozen=True)
class R49MultiProbeDataset:
    """Complete empirical carrier container across all 8 probes."""

    cmb: CMBCarrierData
    quaia: DipoleCarrierData
    nvss: DipoleCarrierData
    racs: DipoleCarrierData
    gaia: GaiaVSHCarrierData
    pantheon: PantheonCarrierData
    cf4: CF4TomographicCarrierData
    desi: DESIBAOAndDirectionalCarrierData


def _rotate_stf5_cartesian(v5_cart: np.ndarray, R: np.ndarray) -> np.ndarray:
    M = cartesian_to_stf_matrix(v5_cart)
    return stf_matrix_to_cartesian(R @ M @ R.T)


def _stf5_rotation_matrix(R: np.ndarray) -> np.ndarray:
    """Return 5x5 transformation matrix mapping `v5_cart -> _rotate_stf5_cartesian(v5_cart, R)`."""
    M5 = np.empty((5, 5), dtype=np.float64)
    for k in range(5):
        ek = np.zeros(5, dtype=np.float64)
        ek[k] = 1.0
        M5[:, k] = _rotate_stf5_cartesian(ek, R)
    return M5


def _pack_transfer_modes(
    alm_T: Mapping[tuple[int, int], complex],
    alm_E: Mapping[tuple[int, int], complex],
    alm_B: Mapping[tuple[int, int], complex],
    mode_labels: tuple[str, ...],
) -> np.ndarray:
    """Extract real-harmonic vector from complex `alm_{T,E,B}` ordered by `mode_labels`."""
    vals = np.empty(len(mode_labels), dtype=np.float64)
    maps = {"T": alm_T, "E": alm_E, "B": alm_B}
    sq2 = math.sqrt(2.0)
    for i, lbl in enumerate(mode_labels):
        # Format: "<P>_<ell>_<m>[r|i]" e.g. "T_2_0", "T_2_1r", "T_2_1i", "E_2_2r"
        pol, ell_s, m_s = lbl.split("_")
        ell = int(ell_s)
        dmap = maps[pol]
        if m_s.endswith("r"):
            m = int(m_s[:-1])
            c = dmap.get((ell, m), 0.0j)
            vals[i] = float(sq2 * np.real(c)) if m > 0 else float(np.real(c))
        elif m_s.endswith("i"):
            m = int(m_s[:-1])
            c = dmap.get((ell, m), 0.0j)
            vals[i] = float(-sq2 * np.imag(c))
        else:
            m = int(m_s)
            vals[i] = float(np.real(dmap.get((ell, m), 0.0j)))
    return vals


def standard_lowell_mode_labels(ells: Sequence[int], include_eb: bool = True) -> tuple[str, ...]:
    """Build deterministic real-harmonic mode labels for `(T, E, B)` across declared multipoles."""
    pols = ("T", "E", "B") if include_eb else ("T",)
    labels: list[str] = []
    for pol in pols:
        for ell in ells:
            labels.append(f"{pol}_{ell}_0")
            for m in range(1, ell + 1):
                labels.append(f"{pol}_{ell}_{m}r")
                labels.append(f"{pol}_{ell}_{m}i")
    return tuple(labels)


class R49GeneralBianchiLikelihood:
    """Unified multi-probe source-bound tensor likelihood for R49 general tilted Bianchi."""

    def __init__(
        self,
        dataset: R49MultiProbeDataset,
        *,
        mode_budget: CMBModeBudgetSpec | None = None,
        alignment: FrameEpochAlignmentSpec | None = None,
        active_probes: Sequence[str] = DEFAULT_PROBES,
        validate_preflight: bool = True,
    ) -> None:
        self.dataset = dataset
        self.mode_budget = CMBModeBudgetSpec(use_polarized_eb=True) if mode_budget is None else mode_budget
        self.alignment = (
            FrameEpochAlignmentSpec(triad_frame="galactic", triad_rotation=np.eye(3))
            if alignment is None
            else alignment
        )
        self.active_probes = tuple(active_probes)

        if validate_preflight:
            self._run_preflight_checks()

        self._precompute_probe_operators()

    def _run_preflight_checks(self) -> None:
        # 1. Lane consistency between budget and CMB data carrier
        if self.dataset.cmb.lane != self.mode_budget.lane:
            raise LaneContaminationError(
                f"CMB data lane {self.dataset.cmb.lane!r} != budget lane {self.mode_budget.lane!r}."
            )
        if self.dataset.cmb.lane == "NPIPE_PR4_ROBUSTNESS" and self.dataset.cmb.mc_source == "FFP10_PR3":
            raise LaneContaminationError("NPIPE PR4 robustness data paired with PR3 FFP10 simulations.")
        # 2. Check all probes declare known coordinate frames
        valid_frames = {"galactic", "icrs"}
        for nm, cr in (
            ("cmb", self.dataset.cmb),
            ("quaia", self.dataset.quaia),
            ("nvss", self.dataset.nvss),
            ("racs", self.dataset.racs),
            ("gaia", self.dataset.gaia),
            ("cf4", self.dataset.cf4),
            ("desi", self.dataset.desi),
        ):
            if cr.coordinate_frame not in valid_frames:
                raise MissingTriadError(f"Probe {nm} has invalid coordinate_frame {cr.coordinate_frame!r}")

    def _frame_rot_to_triad(self, probe_frame: str) -> np.ndarray:
        R_user = np.asarray(self.alignment.triad_rotation, dtype=np.float64)
        if probe_frame == "galactic":
            R_base = np.eye(3, dtype=np.float64)
        elif probe_frame == "icrs":
            R_base = ICRS_TO_GALACTIC_MATRIX
        else:
            raise MissingTriadError(f"Unknown probe frame {probe_frame!r}")
        if self.alignment.triad_frame == "icrs":
            R_base = GALACTIC_TO_ICRS_MATRIX @ R_base
        return R_user @ R_base

    def _precompute_probe_operators(self) -> None:
        # 1. CMB Cholesky & log-det + frame transform (triad -> cmb dataset frame)
        self._cmb_R_to_triad = self._frame_rot_to_triad(self.dataset.cmb.coordinate_frame)
        C_cmb = np.asarray(self.dataset.cmb.cov, dtype=np.float64)
        C_cmb = 0.5 * (C_cmb + C_cmb.T)
        self._cmb_chol = scipy.linalg.cholesky(C_cmb, lower=True)
        self._cmb_logdet = 2.0 * float(np.sum(np.log(np.diag(self._cmb_chol))))
        self._cmb_det_mask = np.array(
            [int(lbl.split("_")[1]) in set(self.mode_budget.deterministic_ells) for lbl in self.dataset.cmb.mode_labels],
            dtype=bool,
        )
        self._cmb_cov_mask = np.array(
            [int(lbl.split("_")[1]) in set(self.mode_budget.covariance_ells) for lbl in self.dataset.cmb.mode_labels],
            dtype=bool,
        )

        # 2. Dipoles: Quaia, NVSS, RACS rotated into common triad
        self._dipole_ops: dict[str, dict[str, Any]] = {}
        for key, car in (
            ("Quaia", self.dataset.quaia),
            ("NVSS", self.dataset.nvss),
            ("RACS", self.dataset.racs),
        ):
            R = self._frame_rot_to_triad(car.coordinate_frame)
            d_triad = R @ car.d_obs
            C_triad = R @ car.cov @ R.T
            C_triad = 0.5 * (C_triad + C_triad.T)
            L_triad = scipy.linalg.cholesky(C_triad, lower=True)
            logdet = 2.0 * float(np.sum(np.log(np.diag(L_triad))))
            self._dipole_ops[key] = {
                "d": d_triad,
                "L": L_triad,
                "logdet": logdet,
                "c_eb": float(car.c_eb),
                "z_eff": float(car.z_eff),
            }

        # 3. Gaia+ICRF3 with full covariance rotation + Schur marginalization over B1 frame spin Omega_triad
        g = self.dataset.gaia
        Rg = self._frame_rot_to_triad(g.coordinate_frame)
        R_gaia_11 = scipy.linalg.block_diag(Rg, Rg, _stf5_rotation_matrix(Rg))
        d_gaia = np.concatenate([Rg @ g.e1_obs, Rg @ g.b1_obs, _rotate_stf5_cartesian(g.e2_obs, Rg)])
        H_spin = np.zeros((11, 3), dtype=np.float64)
        H_spin[3:6, :] = np.eye(3, dtype=np.float64)
        C_g = R_gaia_11 @ (0.5 * (g.cov_e1b1e2 + g.cov_e1b1e2.T)) @ R_gaia_11.T
        C_g = 0.5 * (C_g + C_g.T)
        L_g = scipy.linalg.cholesky(C_g, lower=True)
        self._gaia_d = d_gaia
        self._gaia_schur = SchurMarginalizer(L_g, design_matrix=H_spin, name="GaiaVSH_SpinMarginalized")

        # 4. Pantheon+ with analytic Schur marginalization over Delta M_0
        p = self.dataset.pantheon
        L_p = scipy.linalg.cholesky(0.5 * (p.cov + p.cov.T), lower=True)
        H_M0 = np.ones((len(p.m_b_obs), 1), dtype=np.float64)
        self._pan_schur = SchurMarginalizer(L_p, design_matrix=H_M0, name="PantheonPlus_M0Marginalized")
        self._pan_n_triad = (self._frame_rot_to_triad("galactic") @ p.n_hat_gal.T).T

        # 5. CF4 tomographic depth shells rotated into common triad
        c4 = self.dataset.cf4
        R_cf4 = self._frame_rot_to_triad(c4.coordinate_frame)
        n_shells = len(c4.shell_z_bins)
        R_cf4_blk = scipy.linalg.block_diag(*([R_cf4] * n_shells)) if n_shells > 0 else np.eye(0)
        self._cf4_d_triad = R_cf4_blk @ np.asarray(c4.d_obs, dtype=np.float64)
        C_c4 = R_cf4_blk @ (0.5 * (c4.cov + c4.cov.T)) @ R_cf4_blk.T
        C_c4 = 0.5 * (C_c4 + C_c4.T)
        L_c4 = scipy.linalg.cholesky(C_c4, lower=True)
        self._cf4_L = L_c4
        self._cf4_logdet = 2.0 * float(np.sum(np.log(np.diag(L_c4))))

        # 6. DESI BAO + directional anisotropy rotated into common triad
        ds = self.dataset.desi
        L_bao = scipy.linalg.cholesky(0.5 * (ds.bao_cov + ds.bao_cov.T), lower=True)
        self._desi_bao_L = L_bao
        self._desi_bao_logdet = 2.0 * float(np.sum(np.log(np.diag(L_bao))))
        R_desi_5 = _stf5_rotation_matrix(self._frame_rot_to_triad(ds.coordinate_frame))
        self._desi_dq_obs_triad = R_desi_5 @ np.asarray(ds.directional_quad_obs, dtype=np.float64)
        C_dq = R_desi_5 @ (0.5 * (ds.directional_quad_cov + ds.directional_quad_cov.T)) @ R_desi_5.T
        C_dq = 0.5 * (C_dq + C_dq.T)
        L_dq = scipy.linalg.cholesky(C_dq, lower=True)
        self._desi_dq_L = L_dq
        self._desi_dq_logdet = 2.0 * float(np.sum(np.log(np.diag(L_dq))))

    @property
    def n_total_data(self) -> int:
        n = 0
        if "CMB" in self.active_probes:
            n += len(self.dataset.cmb.d_obs)
        for p in ("Quaia", "NVSS", "RACS"):
            if p in self.active_probes:
                n += 3
        if "Gaia" in self.active_probes:
            n += 8  # 11 - 3 marginalized spin DOF
        if "PantheonPlus" in self.active_probes:
            n += len(self.dataset.pantheon.m_b_obs) - 1
        if "CF4" in self.active_probes:
            n += len(self.dataset.cf4.d_obs)
        if "DESI" in self.active_probes:
            n += len(self.dataset.desi.bao_mean) + 5
        return n

    def _predict_cmb_vector(self, state: R49JointState) -> tuple[np.ndarray, np.ndarray]:
        """Return `(mu_cmb, excess_var_diag)` over `dataset.cmb.mode_labels`."""
        # Map triad-frame state tensors/vectors back into `dataset.cmb.coordinate_frame`
        R_to_cmb = self._cmb_R_to_triad.T
        sig_3x3 = R_to_cmb @ state.sigma_matrix @ R_to_cmb.T
        v_mat_cmb = R_to_cmb @ state.v_matter
        v_rad_cmb = R_to_cmb @ state.v_rad
        v_obs_cmb = R_to_cmb @ state.beta_MO
        lmax_need = max(int(self.mode_budget.ell_max), 2)
        tmode = self.mode_budget.transfer_mode
        if state.family not in {"FLRW", "I", "V", "VII_0", "VII_h", "IX"}:
            tmode = TRANSFER_MODE_GEODESIC
        out = compute_general_bianchi_transfer(
            TiltedTransferParameters(
                family=state.family,
                sigma_N=sig_3x3,
                v_matter=v_mat_cmb,
                v_rad=v_rad_cmb,
                v_obs=v_obs_cmb,
                h_bianchi=state.h_bianchi,
                omega_k=state.omega_k,
                handedness=state.handedness,
                ell_max=lmax_need,
                n_gl_theta=max(12, lmax_need + 4),
                transfer_mode=tmode,
                n_efolds_star=-1.0 if tmode == TRANSFER_MODE_GEODESIC else -2.5,
                n_geodesic_steps=48,
            )
        )
        # Convert dimensionless dT/T to uK for CMB comparison (standard Planck map units uK_CMB)
        full_pred = 1.0e6 * T_CMB_K * _pack_transfer_modes(
            out.alm_T,
            out.alm_E,
            out.alm_B,
            self.dataset.cmb.mode_labels,
        )
        mu = np.where(self._cmb_det_mask, full_pred, 0.0)
        # On covariance-budget modes ONLY (`_cmb_cov_mask`, disjoint from `_cmb_det_mask`),
        # allow variance contribution scaled by ell=5..6 transfer power attenuation (1e-8) * |Sigma|^2.
        sig_amp2 = float(state.sigma_AB_stf5 @ G_STF5 @ state.sigma_AB_stf5)
        cov_excess = np.where(self._cmb_cov_mask, 1.0e-8 * (1.0e6 * T_CMB_K) ** 2 * sig_amp2, 0.0)
        return mu, cov_excess

    def logp_by_probe(self, state: R49JointState) -> dict[str, float]:
        """Evaluate log-likelihood breakdown per probe under one common state."""
        if not isinstance(state, R49JointState):
            raise ScalarSpeedError("logp_by_probe requires a vector-valued R49JointState instance.")

        scores: dict[str, float] = {}

        if "CMB" in self.active_probes:
            mu_cmb, cov_excess = self._predict_cmb_vector(state)
            r = self.dataset.cmb.d_obs - mu_cmb
            if np.any(cov_excess > 0.0):
                C_eff = 0.5 * (self.dataset.cmb.cov + self.dataset.cmb.cov.T) + np.diag(cov_excess)
                L_eff = scipy.linalg.cholesky(C_eff, lower=True)
                logdet_eff = 2.0 * float(np.sum(np.log(np.diag(L_eff))))
                w = scipy.linalg.solve_triangular(L_eff, r, lower=True)
                chi2 = float(w @ w)
                scores["CMB"] = -0.5 * (chi2 + logdet_eff + len(r) * math.log(2.0 * math.pi))
            else:
                w = scipy.linalg.solve_triangular(self._cmb_chol, r, lower=True)
                scores["CMB"] = -0.5 * (float(w @ w) + self._cmb_logdet + len(r) * math.log(2.0 * math.pi))

        # Common composed radiation-observer and matter-observer boosts + A_A dipole shift
        # Note count dipoles respond to local observer motion wrt isotropic source rest frame beta_obs_src,
        # which in Bianchi Class B / tilted fluid picks up matter tilt (-v_matter) and observer boost (+beta_MO)
        # plus intrinsic curvature/acceleration A_A!
        beta_source_frame = state.beta_MO
        for key in ("Quaia", "NVSS", "RACS"):
            if key in self.active_probes:
                op = self._dipole_ops[key]
                pred_d = op["c_eb"] * (beta_source_frame + 0.1 * state.A_A)
                r = op["d"] - pred_d
                w = scipy.linalg.solve_triangular(op["L"], r, lower=True)
                scores[key] = -0.5 * (float(w @ w) + op["logdet"] + 3.0 * math.log(2.0 * math.pi))

        if "Gaia" in self.active_probes:
            # E1 aberration glide: ~ (1 / uas_to_rad) H0 [beta_MO_transverse + A_A]
            # Standard Secular Aberration Drift from v_obs wrt CRF: ~ 5.0 uas/yr at v ~ 370 km/s!
            # Using standard secular drift scale: a_gal / c ~ H0 * beta (or acceleration proxy A_A * c * H0_to_uasyr):
            H0_uasyr = (state.psi.H_0 * 1.0227e-12) * (180.0 * 3600.0e6 / math.pi)  # uas/yr
            e1_pred = H0_uasyr * (state.beta_MO + state.A_A)
            # B1 contains cosmic vorticity; frame spin Omega_triad is Schur-marginalized via _gaia_schur!
            b1_pred = H0_uasyr * state.omega_A
            # E2 optical shear & aberration quadrupole: sigma_AB * H0_uasyr + 0.5 Q(beta_MO)
            e2_pred = H0_uasyr * (state.sigma_AB_stf5 + 0.25 * stf_matrix_to_cartesian(kinematic_quadrupole_stf2(state.beta_MO)))
            pred_g = np.concatenate([e1_pred, b1_pred, e2_pred])
            _, logp_g, _ = self._gaia_schur.marginalize(self._gaia_d - pred_g)
            scores["Gaia"] = float(logp_g)

        if "PantheonPlus" in self.active_probes:
            pan = self.dataset.pantheon
            z_h = pan.z_hd
            # Vectorized flat/curved luminosity distance in Mpc via trapezoidal grid
            Om = state.psi.Omega_m
            Ok = state.psi.DeltaOmega_k
            Ode = 1.0 - Om - Ok
            H0 = state.psi.H_0
            s_grid = np.linspace(0.0, 1.0, 32)[None, :]
            zp = z_h[:, None] * s_grid
            Ez = np.sqrt(np.maximum(Om * (1.0 + zp) ** 3 + Ok * (1.0 + zp) ** 2 + Ode, 1.0e-12))
            dc = (SPEED_OF_LIGHT_KM_S / H0) * z_h * np.trapezoid(1.0 / Ez, s_grid[0], axis=1)
            if abs(Ok) < 1.0e-6:
                dm = dc
            elif Ok > 0.0:
                sk = math.sqrt(Ok)
                rh = SPEED_OF_LIGHT_KM_S / H0
                dm = (rh / sk) * np.sinh(sk * dc / rh)
            else:
                sk = math.sqrt(-Ok)
                rh = SPEED_OF_LIGHT_KM_S / H0
                dm = (rh / sk) * np.sin(sk * dc / rh)
            dL = (1.0 + pan.z_hel) * dm
            mu_iso = 5.0 * np.log10(np.maximum(dL, 1.0e-9)) + 25.0
            # First-order anisotropic luminosity distance modulation from dipole (beta_MO, A_A) & shear sigma_ab
            n_dot_dip = self._pan_n_triad @ (state.beta_MO - state.v_matter + 0.5 * state.A_A)
            n_sig_n = np.einsum("ni,ij,nj->n", self._pan_n_triad, state.sigma_matrix, self._pan_n_triad)
            delta_mu = -(5.0 / math.log(10.0)) * (n_dot_dip * (1.0 / np.maximum(z_h, 0.015)) - 0.5 * z_h * n_sig_n)
            _, logp_pan, _ = self._pan_schur.marginalize(pan.m_b_obs - (mu_iso + delta_mu))
            scores["PantheonPlus"] = float(logp_pan)

        if "CF4" in self.active_probes:
            c4 = self.dataset.cf4
            preds = []
            # Bulk velocity field in km/s: v_bulk(z_mid) = c * (-beta_MO + v_matter) + c * z_mid * sigma_trace_corr
            base_v_kms = SPEED_OF_LIGHT_KM_S * (state.v_matter - state.beta_MO)
            for z_lo, z_hi in c4.shell_z_bins:
                z_mid = 0.5 * (z_lo + z_hi)
                # Shear induces dipolar/quadrupolar weighted leakage proportional to z_mid * A_A
                preds.append(base_v_kms + SPEED_OF_LIGHT_KM_S * z_mid * 0.1 * state.A_A)
            r_c4 = self._cf4_d_triad - np.concatenate(preds)
            w_c4 = scipy.linalg.solve_triangular(self._cf4_L, r_c4, lower=True)
            scores["CF4"] = -0.5 * (float(w_c4 @ w_c4) + self._cf4_logdet + len(r_c4) * math.log(2.0 * math.pi))

        if "DESI" in self.active_probes:
            ds = self.dataset.desi
            bao_pred = np.empty(len(ds.bao_mean), dtype=np.float64)
            for idx, (zv, qty) in enumerate(zip(ds.bao_z, ds.bao_quantities)):
                if qty == "DM_over_rs":
                    bao_pred[idx] = state.psi.transverse_comoving_distance_Mpc(float(zv)) / state.psi.r_d
                elif qty == "DH_over_rs":
                    bao_pred[idx] = state.psi.hubble_distance_Mpc(float(zv)) / state.psi.r_d
                elif qty == "DV_over_rs":
                    bao_pred[idx] = state.psi.volume_distance_Mpc(float(zv)) / state.psi.r_d
                else:
                    raise ValueError(f"Unknown DESI BAO quantity {qty!r}")
            w_bao = scipy.linalg.solve_triangular(self._desi_bao_L, ds.bao_mean - bao_pred, lower=True)
            logp_bao = -0.5 * (float(w_bao @ w_bao) + self._desi_bao_logdet + len(bao_pred) * math.log(2.0 * math.pi))
            # Directional NGC-SGC quadrupole growth sensitivity to cosmic shear sigma_AB
            w_dq = scipy.linalg.solve_triangular(self._desi_dq_L, self._desi_dq_obs_triad - state.sigma_AB_stf5, lower=True)
            logp_dq = -0.5 * (float(w_dq @ w_dq) + self._desi_dq_logdet + 5.0 * math.log(2.0 * math.pi))
            scores["DESI"] = logp_bao + logp_dq

        return scores

    def logp(self, state: R49JointState) -> float:
        return float(sum(self.logp_by_probe(state).values()))


# -----------------------------------------------------------------------------
# Single-Posterior Five-View Derivation & Scalar x_C Ablation
# -----------------------------------------------------------------------------


def compute_r49_htt_five_views_from_posterior(
    posterior_draws24: np.ndarray,
    *,
    matched_null_samples_beta: np.ndarray | None = None,
    null_law_name: str = "MATCHED_NULL_FFP10_PR3",
    shell_redshift_bins: list[tuple[float, float]] | None = None,
    shell_data_vectors: list[np.ndarray] | None = None,
    cross_shell_data_cov: np.ndarray | None = None,
    split_draws_for_q: np.ndarray | None = None,
    split_draws_for_pi: np.ndarray | None = None,
    split_draws_for_f: np.ndarray | None = None,
    split_draws_for_gf: np.ndarray | None = None,
    n_quadrature_dirs: int = 100,
) -> dict[str, Any]:
    """Derive ALL FIVE HTT variables `(x, Q, Pi, F, G_F)` from ONE joint posterior draw ensemble.

    Passing separate posterior arrays for any of the views immediately raises
    ``SplitPosteriorFiveViewError`` (Acceptance Test 12).
    """
    if any(
        arg is not None
        for arg in (split_draws_for_q, split_draws_for_pi, split_draws_for_f, split_draws_for_gf)
    ):
        raise SplitPosteriorFiveViewError(
            "All five HTT variables (x, Q, Pi, F, G_F) MUST be derived from one common joint posterior."
        )

    if matched_null_samples_beta is not None:
        raise ValueError(
            "Unqualified beta null rejected: R49 cached quadrupole coordinates are not "
            "replications of the joint beta_MO estimator. Refit the same estimator "
            "under the same joint null and bind its source/selection contract first."
        )

    draws = np.asarray(posterior_draws24, dtype=np.float64)
    if draws.ndim != 2 or draws.shape[1] != 24 or draws.shape[0] < 4:
        raise ValueError(f"posterior_draws24 must have shape (N>=4, 24), got {draws.shape}")

    # Extract standard 17D kinetic block (sigma_5, omega_3, A_3, beta_RM_3, beta_MO_3)
    # from the 24D full tilted Bianchi draws so construct_r42_five_variable_state operates identically!
    sigma_draws = draws[:, 0:5]
    omega_draws = draws[:, 5:8]
    a_draws = draws[:, 8:11]
    vm_draws = draws[:, 11:14]
    vr_draws = draws[:, 14:17]
    bmo_draws = draws[:, 17:20]
    brm_draws = np.array([compose_velocities_sr(-vm_draws[i], vr_draws[i]) for i in range(len(draws))])
    mcmc_17 = np.hstack([sigma_draws, omega_draws, a_draws, brm_draws, bmo_draws])

    post_mean_17 = np.mean(mcmc_17, axis=0)
    b_rm_mean = tuple(float(v) for v in post_mean_17[11:14])
    b_mo_mean = tuple(float(v) for v in post_mean_17[14:17])
    b_ro_mean = tuple(float(v) for v in compose_velocities_sr(b_rm_mean, b_mo_mean))

    frame = "CMB_CONGRUENCE_FRAME"
    congruence = "CMB_REST_FRAME"
    epoch = "Z_RECOMBINATION"
    averaging = "HUBBLE_SCALE"
    basis = "TETRAD_A"
    units = UnitsConvention.EXPLICIT_C_THETA_NORMALIZED
    perturbative_order = "LINEAR_FIRST_ORDER"

    kinematics = CongruenceKinematics(
        sigma_stf5=tuple(float(v) for v in post_mean_17[0:5]),
        omega_axial3=tuple(float(v) for v in post_mean_17[5:8]),
        acceleration_polar3=tuple(float(v) for v in post_mean_17[8:11]),
        frame=frame,
        congruence_id=congruence,
        epoch_window=epoch,
        averaging_scale=averaging,
        basis=basis,
        units_convention=units,
        acceleration_normalization=AccelerationNormalization.A_OVER_C_THETA,
        velocity_normalization=VelocityNormalization.BETA_EQUALS_V_OVER_C,
        perturbative_order=perturbative_order,
    )
    velocities = build_velocity_frame_bundle(
        beta_RO=b_ro_mean,
        beta_RM=b_rm_mean,
        beta_MO=b_mo_mean,
        coordinate_frame=frame,
        radiation_frame_id="radiation-rest-frame",
        matter_frame_id="matter-rest-frame",
        observer_frame_id="observer-rest-frame",
        basis=basis,
        epoch_window=epoch,
        averaging_scale=averaging,
        first_order_beta_ceiling=0.1,
        source_decomposition_id="r49-general-tilted-bianchi-joint-posterior",
    )
    geometry = GeometryState(
        delta_omega_k=float(np.mean(draws[:, 23])),
        frame=frame,
        congruence_id=congruence,
        epoch_window=epoch,
        averaging_scale=averaging,
        basis=basis,
        units_convention=units,
        perturbative_order=perturbative_order,
    )
    joint_state = JointAnisotropyState(
        congruence_kinematics=kinematics,
        velocity_frames=velocities,
        geometry_state=geometry,
        frame=frame,
        congruence=congruence,
        epoch_window=epoch,
        averaging_scale=averaging,
        basis=basis,
        units_convention=units,
        perturbative_order=perturbative_order,
        beta_semantic_role=BetaSemanticRole.DIRECT_STATE,
        transfer_source=TransferSource.NONE,
        transfer_spec=None,
        source_kind=JointStateSourceKind.DIRECT,
        source_identity="r49-single-posterior-five-view-state",
    )
    bundle_x = build_full_observable_x_bundle(
        joint_state,
        params_to_kinematic_model(post_mean_17),
        expansion_scalar=0.21,
    )

    state_five = construct_r42_five_variable_state(
        bundle_x=bundle_x,
        mcmc_samples=mcmc_17,
        param_names=list(PARAM_NAMES_17),
        matched_null_samples=matched_null_samples_beta,
        null_law_name=null_law_name,
        n_quadrature_dirs=n_quadrature_dirs,
        shell_redshift_bins=shell_redshift_bins,
        shell_data_vectors=shell_data_vectors,
        cross_shell_data_cov=cross_shell_data_cov,
    )

    # Gram-metric tensor amplitude summary across draws
    gram_norms = np.sqrt(np.maximum(0.0, np.einsum("ni,ij,nj->n", sigma_draws, G_STF5, sigma_draws)))
    mo_norms = np.linalg.norm(bmo_draws, axis=1)
    rm_norms = np.linalg.norm(brm_draws, axis=1)
    dirs = state_five.support_profiles_F["BETA_MO"].evaluation_directions

    return {
        "schema_version": "r49_single_posterior_five_view_v1",
        "single_posterior_verified": True,
        "velocity_null_status": "UNAVAILABLE_SAME_ESTIMATOR_JOINT_NULL_REQUIRED",
        "shared_posterior_id": str(state_five.bundle_x.canonical_state_id),
        "n_draws": int(len(draws)),
        "source_posterior_shape": list(draws.shape),
        "x_summary": {
            "sigma_gram_norm_mean": float(np.mean(gram_norms)),
            "sigma_gram_norm_std": float(np.std(gram_norms)),
            "beta_MO_norm_mean": float(np.mean(mo_norms)),
            "beta_MO_norm_std": float(np.std(mo_norms)),
            "beta_RM_norm_mean": float(np.mean(rm_norms)),
            "stf5_gram_metric_diag": np.diag(G_STF5).tolist(),
        },
        "Q_anchors": {
            k: {
                "status": v.status,
                "metric": v.metric,
                "norm_bound": v.norm_bound,
                "gauge_margin": v.gauge_margin,
            }
            for k, v in state_five.anchors_Q.items()
        },
        "Pi_exceedance": {
            k: {
                "law_name": v.law_name,
                "critical_threshold_95": v.critical_threshold_95,
                "observed_score": v.observed_score,
                "observed_exceedance": v.observed_exceedance,
                "undefined_mass": v.undefined_mass,
            }
            for k, v in state_five.exceedance_surfaces_Pi.items()
        },
        "F_directional": {
            "n_directions": int(dirs.shape[0]),
            "beta_MO_max_support": float(np.max(state_five.support_profiles_F["BETA_MO"].support_values)),
            "beta_MO_max_occupancy": float(np.max(state_five.support_profiles_F["BETA_MO"].occupancy_ratios)),
            "sigma_max_support": float(np.max(state_five.support_profiles_F["SHEAR_SIGMA"].support_values)),
        },
        "G_F_depth": {
            "shells": [list(b) for b in state_five.depth_path_GF.shell_redshift_bins],
            "n_contrasts": len(state_five.depth_path_GF.relative_depth_contrasts),
            "cov_shape": list(state_five.depth_path_GF.cross_shell_covariance.shape),
            "cov_min_eig": float(np.min(np.linalg.eigvalsh(state_five.depth_path_GF.cross_shell_covariance))),
            "transport_model": state_five.depth_path_GF.transport_model,
        },
        "five_variable_state": state_five,
    }


def compute_scalar_xc_ablation_comparison(posterior_draws24: np.ndarray) -> dict[str, Any]:
    """Compare full vector/tensor R49 state against collapsed scalar-speed `x_C` ablation.

    Reports coordinate reduction only. Posterior covariance rank is not Fisher
    information, and dimension counts do not measure target information loss.
    """
    draws = np.asarray(posterior_draws24, dtype=np.float64)
    if draws.ndim != 2 or draws.shape[1] != 24 or draws.shape[0] < 4 or not np.isfinite(draws).all():
        raise ValueError("finite posterior_draws24 with shape (N>=4,24) required")
    # Full tensor covariance matrix over 14 anisotropic DOFs (sigma_5, omega_3, v_matter_3, beta_MO_3)
    X_full = np.hstack([draws[:, 0:5], draws[:, 5:8], draws[:, 11:14], draws[:, 17:20]])
    centered = X_full - np.mean(X_full, axis=0)
    scales = np.std(centered, axis=0)
    active = scales > 0
    rank_full = int(np.linalg.matrix_rank(centered[:, active] / scales[active])) if active.any() else 0
    # Scalar x_C collapse: replace vector velocities & shear with single scalar RSS speed amplitude
    x_C = np.sqrt(
        np.sum(draws[:, 17:20] ** 2, axis=1)
        + np.einsum("ni,ij,nj->n", draws[:, 0:5], G_STF5, draws[:, 0:5])
    )
    return {
        "ablation_role": "ABLATION_ONLY_FORBIDDEN_IN_PRODUCTION",
        "full_tensor_dof": int(X_full.shape[1]),
        "full_covariance_rank": rank_full,
        "scalar_xc_dof": 1,
        "scalar_xc_mean": float(np.mean(x_C)),
        "scalar_x_C_mean": float(np.mean(x_C)),
        "scalar_xc_std": float(np.std(x_C)),
        "vector_beta_MO_mean_norm": float(np.linalg.norm(np.mean(draws[:, 17:20], axis=0))),
        "coordinate_reduction_fraction": float(X_full.shape[1] - 1) / float(X_full.shape[1]),
        "information_loss_ratio_dof": None,
        "information_loss_status": "NOT_EVALUATED_REQUIRES_TARGET_AND_LIKELIHOOD",
        "rank_method": "centered_column_scaled_SVD_no_jitter",
    }


# -----------------------------------------------------------------------------
# Cobaya Adapter
# -----------------------------------------------------------------------------


class R49GeneralBianchiCobayaLikelihood(_CobayaLikelihood):  # pragma: no cover - integration surface
    """Cobaya Likelihood wrapper for R49 general tilted Bianchi multi-probe inference."""

    family: str = "VII_h"
    h_bianchi: float = 0.25
    omega_k: float = 0.0
    handedness: int = 1
    _r49_likelihood: R49GeneralBianchiLikelihood | None = None

    def bind_r49_likelihood(self, likelihood: R49GeneralBianchiLikelihood) -> None:
        self._r49_likelihood = likelihood

    def logp(self, **params_values: Any) -> float:
        if self._r49_likelihood is None:
            raise RuntimeError("Call bind_r49_likelihood() before evaluating Cobaya logp().")
        vec24 = [float(params_values[name]) for name in PARAM_NAMES_24]
        st = R49JointState.from_vector24(
            vec24,
            family=self.family,
            h_bianchi=self.h_bianchi,
            omega_k=self.omega_k,
            handedness=self.handedness,
        )
        return self._r49_likelihood.logp(st)
