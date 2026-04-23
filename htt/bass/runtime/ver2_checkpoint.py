"""Checkpoint helpers for the VER2 native Tier-B runtime."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from bass.hierarchy.ver2_native_integrator import NativeTierBRestartState

__all__ = [
    "TierBCheckpointRecord",
    "checkpoint_path_from_template",
    "write_tier_b_restart_checkpoint",
    "load_tier_b_restart_checkpoint",
]

_SCHEMA_VERSION = "ver2-tier-b-checkpoint-v1"


@dataclass(frozen=True)
class TierBCheckpointRecord:
    """On-disk checkpoint record for native Tier-B restart."""

    schema_version: str
    bianchi_type: str
    structure_label: str
    structure_n_diag: np.ndarray
    structure_a_twist: float
    tilt_rapidity: float
    tilt_direction: np.ndarray
    direction_convention: str
    eta_initial_mpc: float
    eta_final_mpc: float
    n_output: int
    solver_method: str
    L_max: int
    step_index: int
    eta_restart: float
    state_vector: np.ndarray
    eta_prefix: np.ndarray
    photon_T_prefix: np.ndarray
    photon_E_prefix: np.ndarray
    photon_B_prefix: np.ndarray
    neutrino_tower_prefix: np.ndarray
    baryon_local_prefix: np.ndarray
    cdm_local_prefix: np.ndarray
    source_local_prefix: np.ndarray
    residual_local_prefix: np.ndarray
    residual_harmonic_prefix: np.ndarray
    residual_source_prefix: np.ndarray

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(f"unsupported checkpoint schema: {self.schema_version}")
        if not self.bianchi_type:
            raise ValueError("bianchi_type must be non-empty")
        if not self.structure_label:
            raise ValueError("structure_label must be non-empty")
        if self.L_max < 2:
            raise ValueError("L_max must be >= 2")
        if self.n_output < 10:
            raise ValueError("n_output must be >= 10")
        if not self.solver_method:
            raise ValueError("solver_method must be non-empty")
        structure_n_diag = np.asarray(self.structure_n_diag, dtype=np.float64)
        if structure_n_diag.shape != (3,):
            raise ValueError("structure_n_diag must have shape (3,)")
        tilt_direction = np.asarray(self.tilt_direction, dtype=np.float64)
        if tilt_direction.shape != (3,):
            raise ValueError("tilt_direction must have shape (3,)")
        if not np.isfinite(float(self.structure_a_twist)):
            raise ValueError("structure_a_twist must be finite")
        if not np.isfinite(float(self.tilt_rapidity)):
            raise ValueError("tilt_rapidity must be finite")
        if not np.isfinite(float(self.eta_initial_mpc)) or not np.isfinite(float(self.eta_final_mpc)):
            raise ValueError("eta_initial_mpc and eta_final_mpc must be finite")
        if not self.direction_convention:
            raise ValueError("direction_convention must be non-empty")
        eta_prefix = np.asarray(self.eta_prefix, dtype=np.float64)
        if eta_prefix.ndim != 1:
            raise ValueError("eta_prefix must be 1-D")
        for name, value in (
            ("photon_T_prefix", self.photon_T_prefix),
            ("photon_E_prefix", self.photon_E_prefix),
            ("photon_B_prefix", self.photon_B_prefix),
            ("neutrino_tower_prefix", self.neutrino_tower_prefix),
            ("baryon_local_prefix", self.baryon_local_prefix),
            ("cdm_local_prefix", self.cdm_local_prefix),
            ("source_local_prefix", self.source_local_prefix),
            ("residual_local_prefix", self.residual_local_prefix),
            ("residual_harmonic_prefix", self.residual_harmonic_prefix),
            ("residual_source_prefix", self.residual_source_prefix),
        ):
            arr = np.asarray(value, dtype=np.float64)
            if arr.ndim != 2 or arr.shape[0] != eta_prefix.size:
                raise ValueError(f"{name} must have shape (len(eta_prefix), n_state)")

    def to_restart_state(self) -> NativeTierBRestartState:
        return NativeTierBRestartState(
            step_index=int(self.step_index),
            eta_restart=float(self.eta_restart),
            state_vector=np.asarray(self.state_vector, dtype=np.float64),
            eta_prefix=np.asarray(self.eta_prefix, dtype=np.float64),
            photon_T_prefix=np.asarray(self.photon_T_prefix, dtype=np.float64),
            photon_E_prefix=np.asarray(self.photon_E_prefix, dtype=np.float64),
            photon_B_prefix=np.asarray(self.photon_B_prefix, dtype=np.float64),
            neutrino_tower_prefix=np.asarray(self.neutrino_tower_prefix, dtype=np.float64),
            baryon_local_prefix=np.asarray(self.baryon_local_prefix, dtype=np.float64),
            cdm_local_prefix=np.asarray(self.cdm_local_prefix, dtype=np.float64),
            source_local_prefix=np.asarray(self.source_local_prefix, dtype=np.float64),
            residual_local_prefix=np.asarray(self.residual_local_prefix, dtype=np.float64),
            residual_harmonic_prefix=np.asarray(self.residual_harmonic_prefix, dtype=np.float64),
            residual_source_prefix=np.asarray(self.residual_source_prefix, dtype=np.float64),
        )


def checkpoint_path_from_template(
    path_template: str,
    *,
    step: int,
    eta: float,
) -> Path:
    path = Path(path_template.format(step=int(step), eta=f"{float(eta):.12g}"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_tier_b_restart_checkpoint(
    path: str | Path,
    *,
    bianchi_type: str,
    structure_label: str,
    structure_n_diag: np.ndarray,
    structure_a_twist: float,
    tilt_rapidity: float,
    tilt_direction: np.ndarray,
    direction_convention: str,
    eta_initial_mpc: float,
    eta_final_mpc: float,
    n_output: int,
    solver_method: str,
    L_max: int,
    restart_state: NativeTierBRestartState,
) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        schema_version=np.array(_SCHEMA_VERSION),
        bianchi_type=np.array(str(bianchi_type)),
        structure_label=np.array(str(structure_label)),
        structure_n_diag=np.asarray(structure_n_diag, dtype=np.float64),
        structure_a_twist=np.array(float(structure_a_twist), dtype=np.float64),
        tilt_rapidity=np.array(float(tilt_rapidity), dtype=np.float64),
        tilt_direction=np.asarray(tilt_direction, dtype=np.float64),
        direction_convention=np.array(str(direction_convention)),
        eta_initial_mpc=np.array(float(eta_initial_mpc), dtype=np.float64),
        eta_final_mpc=np.array(float(eta_final_mpc), dtype=np.float64),
        n_output=np.array(int(n_output), dtype=np.int64),
        solver_method=np.array(str(solver_method)),
        L_max=np.array(int(L_max), dtype=np.int64),
        step_index=np.array(int(restart_state.step_index), dtype=np.int64),
        eta_restart=np.array(float(restart_state.eta_restart), dtype=np.float64),
        state_vector=np.asarray(restart_state.state_vector, dtype=np.float64),
        eta_prefix=np.asarray(restart_state.eta_prefix, dtype=np.float64),
        photon_T_prefix=np.asarray(restart_state.photon_T_prefix, dtype=np.float64),
        photon_E_prefix=np.asarray(restart_state.photon_E_prefix, dtype=np.float64),
        photon_B_prefix=np.asarray(restart_state.photon_B_prefix, dtype=np.float64),
        neutrino_tower_prefix=np.asarray(restart_state.neutrino_tower_prefix, dtype=np.float64),
        baryon_local_prefix=np.asarray(restart_state.baryon_local_prefix, dtype=np.float64),
        cdm_local_prefix=np.asarray(restart_state.cdm_local_prefix, dtype=np.float64),
        source_local_prefix=np.asarray(restart_state.source_local_prefix, dtype=np.float64),
        residual_local_prefix=np.asarray(restart_state.residual_local_prefix, dtype=np.float64),
        residual_harmonic_prefix=np.asarray(restart_state.residual_harmonic_prefix, dtype=np.float64),
        residual_source_prefix=np.asarray(restart_state.residual_source_prefix, dtype=np.float64),
    )
    return out


def load_tier_b_restart_checkpoint(path: str | Path) -> TierBCheckpointRecord:
    with np.load(Path(path), allow_pickle=False) as data:
        eta_prefix = np.asarray(data["eta_prefix"], dtype=np.float64)
        l_max = int(np.asarray(data["L_max"]).item())
        tower_size = (l_max + 1) ** 2
        base_state_size = 4 * tower_size + 6
        state_vector = np.asarray(data["state_vector"], dtype=np.float64)
        residual_local_prefix = (
            np.asarray(data["residual_local_prefix"], dtype=np.float64)
            if "residual_local_prefix" in data
            else np.zeros((eta_prefix.shape[0], max(int(state_vector.size) - base_state_size, 0)), dtype=np.float64)
        )
        residual_width = max(int(state_vector.size) - base_state_size - int(residual_local_prefix.shape[1]), 0)
        residual_harmonic_prefix = (
            np.asarray(data["residual_harmonic_prefix"], dtype=np.float64)
            if "residual_harmonic_prefix" in data
            else np.zeros((eta_prefix.shape[0], residual_width), dtype=np.float64)
        )
        residual_source_width = max(
            int(state_vector.size)
            - base_state_size
            - int(residual_local_prefix.shape[1])
            - int(residual_harmonic_prefix.shape[1]),
            0,
        )
        return TierBCheckpointRecord(
            schema_version=str(np.asarray(data["schema_version"]).item()),
            bianchi_type=str(np.asarray(data["bianchi_type"]).item()),
            structure_label=str(np.asarray(data["structure_label"]).item()),
            structure_n_diag=np.asarray(data["structure_n_diag"], dtype=np.float64),
            structure_a_twist=float(np.asarray(data["structure_a_twist"]).item()),
            tilt_rapidity=float(np.asarray(data["tilt_rapidity"]).item()),
            tilt_direction=np.asarray(data["tilt_direction"], dtype=np.float64),
            direction_convention=str(np.asarray(data["direction_convention"]).item()),
            eta_initial_mpc=float(np.asarray(data["eta_initial_mpc"]).item()),
            eta_final_mpc=float(np.asarray(data["eta_final_mpc"]).item()),
            n_output=int(np.asarray(data["n_output"]).item()),
            solver_method=str(np.asarray(data["solver_method"]).item()),
            L_max=l_max,
            step_index=int(np.asarray(data["step_index"]).item()),
            eta_restart=float(np.asarray(data["eta_restart"]).item()),
            state_vector=state_vector,
            eta_prefix=eta_prefix,
            photon_T_prefix=np.asarray(data["photon_T_prefix"], dtype=np.float64),
            photon_E_prefix=np.asarray(data["photon_E_prefix"], dtype=np.float64),
            photon_B_prefix=(
                np.asarray(data["photon_B_prefix"], dtype=np.float64)
                if "photon_B_prefix" in data
                else np.zeros(
                    (
                        eta_prefix.shape[0],
                        tower_size,
                    ),
                    dtype=np.float64,
                )
            ),
            neutrino_tower_prefix=np.asarray(data["neutrino_tower_prefix"], dtype=np.float64),
            baryon_local_prefix=(
                np.asarray(data["baryon_local_prefix"], dtype=np.float64)
                if "baryon_local_prefix" in data
                else np.zeros((eta_prefix.shape[0], 4), dtype=np.float64)
            ),
            cdm_local_prefix=(
                np.asarray(data["cdm_local_prefix"], dtype=np.float64)
                if "cdm_local_prefix" in data
                else np.zeros((eta_prefix.shape[0], 2), dtype=np.float64)
            ),
            source_local_prefix=(
                np.asarray(data["source_local_prefix"], dtype=np.float64)
                if "source_local_prefix" in data
                else np.zeros((eta_prefix.shape[0], 3), dtype=np.float64)
            ),
            residual_local_prefix=residual_local_prefix,
            residual_harmonic_prefix=residual_harmonic_prefix,
            residual_source_prefix=(
                np.asarray(data["residual_source_prefix"], dtype=np.float64)
                if "residual_source_prefix" in data
                else np.zeros((eta_prefix.shape[0], residual_source_width), dtype=np.float64)
            ),
        )
