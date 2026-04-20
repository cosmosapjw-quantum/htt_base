"""FB-7.2 diagonal plus off-diagonal spectrum assembly.

The default implementation follows the audited Phase-FB-META-7 choice:
work in explicit ``m in {0, +2, -2}`` blocks instead of materialising a
fully dense ``(ell, m)`` covariance engine by default.  The returned
bundle still exposes optional dense and sparse views derived from the
same block data so the later HTT and observer-frame layers can choose
their preferred representation without changing the underlying numbers.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

import numpy as np

_MODE_LABELS = ("m0", "m+2", "m-2")
_T_CMB_K = 2.7255
_SMALL_FLOAT = 1.0e-30


def _require_array(
    transfer_bundle: Mapping[str, object], key: str, ndim: int
) -> np.ndarray:
    if key not in transfer_bundle:
        raise KeyError(f"transfer_bundle is missing required key {key!r}")
    arr = np.asarray(transfer_bundle[key], dtype=float)
    if arr.ndim != ndim:
        raise ValueError(
            f"transfer_bundle[{key!r}] must have ndim={ndim} (got {arr.ndim})"
        )
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"transfer_bundle[{key!r}] must be finite")
    return arr


def _integrate_log_k(values_on_k: np.ndarray, k_grid_mpc: np.ndarray) -> np.ndarray:
    if k_grid_mpc.size == 1:
        return values_on_k[0].copy()
    return np.trapezoid(values_on_k, x=np.log(k_grid_mpc), axis=0)


def _primordial_power_spectrum(k_grid_mpc: np.ndarray) -> np.ndarray:
    return 2.1e-9 * np.power(k_grid_mpc / 0.05, 0.9649 - 1.0)


def _compute_dl(c_ell: np.ndarray) -> np.ndarray:
    ell = np.arange(c_ell.size, dtype=float)
    prefactor = ell * (ell + 1.0) / (2.0 * np.pi)
    return prefactor * c_ell * (_T_CMB_K * 1.0e6) ** 2


def _offdiag_mode_weights(
    *,
    offdiag_strength: float,
    preferred_axis: np.ndarray,
    mode_coupling_matrix: np.ndarray,
    structure_label: str,
) -> np.ndarray:
    if structure_label == "I" or offdiag_strength <= 0.0:
        return np.zeros(3, dtype=float)
    drift = np.linalg.norm(mode_coupling_matrix - np.eye(3), axis=1)
    axis_weight = np.array(
        [
            1.0 + 0.20 * abs(float(preferred_axis[2])),
            1.0 + 0.20 * abs(float(preferred_axis[0])),
            1.0 + 0.20 * abs(float(preferred_axis[1])),
        ],
        dtype=float,
    )
    return offdiag_strength * axis_weight * (0.25 + drift)


def _make_offdiag_blocks(
    *,
    diagonal_by_mode: Mapping[str, np.ndarray],
    offdiag_strength: float,
    rotation_strength: float,
    preferred_axis: np.ndarray,
    mode_coupling_matrix: np.ndarray,
    structure_label: str,
) -> dict[str, dict[str, np.ndarray]]:
    ell_max = diagonal_by_mode["TT"].shape[1] - 1
    blocks = {
        spec: {
            mode: np.zeros((ell_max + 1, ell_max + 1), dtype=float)
            for mode in _MODE_LABELS
        }
        for spec in ("TT", "EE", "TE", "BB")
    }
    mode_weights = _offdiag_mode_weights(
        offdiag_strength=offdiag_strength,
        preferred_axis=preferred_axis,
        mode_coupling_matrix=mode_coupling_matrix,
        structure_label=structure_label,
    )
    if np.all(mode_weights == 0.0):
        return blocks

    coherence = 1.5 + 8.0 * offdiag_strength + 4.0 * rotation_strength
    for spec in ("TT", "EE", "TE", "BB"):
        parity_seed = -1.0 if spec == "TE" else 1.0
        for imode, mode in enumerate(_MODE_LABELS):
            diag = diagonal_by_mode[spec][imode]
            block = blocks[spec][mode]
            for ell in range(ell_max + 1):
                for ell_prime in range(ell + 1, ell_max + 1):
                    delta_ell = ell_prime - ell
                    envelope = np.exp(-0.5 * (delta_ell / coherence) ** 2)
                    parity = 1.0
                    if structure_label in {"VIII", "IX"}:
                        parity = (-1.0) ** delta_ell
                    amplitude = mode_weights[imode] * envelope * np.sqrt(
                        max(abs(diag[ell] * diag[ell_prime]), 0.0)
                    )
                    sign = parity_seed
                    if mode == "m-2":
                        sign *= -1.0 if spec in {"TE", "BB"} else 1.0
                    value = sign * parity * amplitude
                    block[ell, ell_prime] = value
                    block[ell_prime, ell] = value
    return blocks


def _dense_from_blocks(
    *,
    blocks: Mapping[str, Mapping[str, np.ndarray]],
    diagonal_by_mode: Mapping[str, np.ndarray],
) -> dict[str, np.ndarray]:
    n_mode, n_ell = diagonal_by_mode["TT"].shape
    size = n_mode * n_ell
    dense = {
        spec: np.zeros((size, size), dtype=float)
        for spec in ("TT", "EE", "TE", "BB")
    }

    def _index(ell: int, mode_index: int) -> int:
        return ell * n_mode + mode_index

    for spec in ("TT", "EE", "TE", "BB"):
        for mode_index, mode in enumerate(_MODE_LABELS):
            diag = diagonal_by_mode[spec][mode_index]
            block = np.asarray(blocks[spec][mode], dtype=float)
            for ell in range(n_ell):
                idx = _index(ell, mode_index)
                dense[spec][idx, idx] = diag[ell]
                for ell_prime in range(n_ell):
                    if ell == ell_prime:
                        continue
                    idx_prime = _index(ell_prime, mode_index)
                    dense[spec][idx, idx_prime] = block[ell, ell_prime]
    return dense


def _sparse_from_blocks(
    *,
    blocks: Mapping[str, Mapping[str, np.ndarray]],
) -> dict[str, list[dict[str, object]]]:
    sparse: dict[str, list[dict[str, object]]] = {spec: [] for spec in ("TT", "EE", "TE", "BB")}
    for spec in ("TT", "EE", "TE", "BB"):
        for mode in _MODE_LABELS:
            block = np.asarray(blocks[spec][mode], dtype=float)
            nz = np.argwhere(np.abs(block) > 0.0)
            for ell, ell_prime in nz:
                sparse[spec].append(
                    {
                        "ell": int(ell),
                        "ell_prime": int(ell_prime),
                        "mode": mode,
                        "value": float(block[ell, ell_prime]),
                    }
                )
    return sparse


def assemble_bianchi_spectrum_covariance(
    *,
    transfer_bundle: Mapping[str, np.ndarray],
    k_grid_mpc: np.ndarray,
    ell_max: int,
    off_diagonal_strategy: Literal[
        "m_decoupled_blocks",
        "dense_matrix",
        "wigner_d_sparse",
    ] = "m_decoupled_blocks",
) -> dict[str, object]:
    """Assemble FB-7.2 diagonal spectra plus off-diagonal covariance.

    Parameters
    ----------
    transfer_bundle
        Output of :func:`bass.spectrum.lowell_los.build_lowell_line_of_sight_propagator`.
    k_grid_mpc
        Shared wavenumber grid used to build the transfer bundle.
    ell_max
        Highest multipole retained in the returned covariance products.
    off_diagonal_strategy
        ``"m_decoupled_blocks"`` is the audited default.  ``"dense_matrix"``
        and ``"wigner_d_sparse"`` expose derived views of the same block
        covariance instead of changing the underlying construction.
    """
    if ell_max < 0:
        raise ValueError(f"ell_max must be non-negative (got {ell_max})")
    if off_diagonal_strategy not in {
        "m_decoupled_blocks",
        "dense_matrix",
        "wigner_d_sparse",
    }:
        raise ValueError(
            "off_diagonal_strategy must be one of "
            "'m_decoupled_blocks', 'dense_matrix', 'wigner_d_sparse'"
        )

    k_grid = np.asarray(k_grid_mpc, dtype=float)
    if k_grid.ndim != 1 or k_grid.size < 2:
        raise ValueError("k_grid_mpc must be a 1-D array with at least 2 entries")
    if np.any(k_grid <= 0.0) or np.any(np.diff(k_grid) <= 0.0):
        raise ValueError("k_grid_mpc must be strictly positive and increasing")

    transfer_T = _require_array(transfer_bundle, "transfer_T", 3)
    transfer_E = _require_array(transfer_bundle, "transfer_E", 3)
    transfer_B = _require_array(transfer_bundle, "transfer_B", 3)
    if transfer_T.shape != transfer_E.shape or transfer_T.shape != transfer_B.shape:
        raise ValueError("transfer_T, transfer_E, and transfer_B must have identical shapes")
    if transfer_T.shape[0] != k_grid.size:
        raise ValueError("transfer bundle k dimension does not match k_grid_mpc")
    if transfer_T.shape[1] < ell_max + 1 or transfer_T.shape[2] != 3:
        raise ValueError("transfer bundle has incompatible ell or mode dimensions")

    transfer_T = transfer_T[:, : ell_max + 1, :]
    transfer_E = transfer_E[:, : ell_max + 1, :]
    transfer_B = transfer_B[:, : ell_max + 1, :]

    structure = transfer_bundle.get("structure")
    structure_label = str(transfer_bundle.get("structure_label", getattr(structure, "label", "unknown")))
    preferred_axis = np.asarray(
        transfer_bundle.get("preferred_axis", np.array([0.0, 0.0, 1.0])),
        dtype=float,
    )
    preferred_axis = preferred_axis / max(float(np.linalg.norm(preferred_axis)), _SMALL_FLOAT)
    mode_coupling_matrix = np.asarray(
        transfer_bundle.get("mode_coupling_matrix", np.eye(3)),
        dtype=float,
    )
    anisotropy_strength = float(transfer_bundle.get("anisotropy_strength", 0.0))
    rotation_strength = float(transfer_bundle.get("rotation_strength", 0.0))
    offdiag_strength = 0.0 if structure_label == "I" else anisotropy_strength + 0.5 * rotation_strength

    primordial = _primordial_power_spectrum(k_grid)[:, None]
    weight = 4.0 * np.pi * primordial

    diagonal_by_mode = {
        "TT": _integrate_log_k(weight[:, None, :] * transfer_T**2, k_grid).T,
        "EE": _integrate_log_k(weight[:, None, :] * transfer_E**2, k_grid).T,
        "TE": _integrate_log_k(weight[:, None, :] * transfer_T * transfer_E, k_grid).T,
        "BB": _integrate_log_k(weight[:, None, :] * transfer_B**2, k_grid).T,
    }

    c_ell = {
        spec: np.sum(diagonal_by_mode[spec], axis=0)
        for spec in ("TT", "EE", "TE", "BB")
    }
    d_ell = {spec: _compute_dl(c_ell[spec]) for spec in ("TT", "EE", "TE", "BB")}

    offdiag_blocks = _make_offdiag_blocks(
        diagonal_by_mode=diagonal_by_mode,
        offdiag_strength=offdiag_strength,
        rotation_strength=rotation_strength,
        preferred_axis=preferred_axis,
        mode_coupling_matrix=mode_coupling_matrix,
        structure_label=structure_label,
    )

    anisotropy_tensor = offdiag_strength * np.outer(preferred_axis, preferred_axis)
    anisotropy_tensor += rotation_strength * np.diag([1.0, -0.5, -0.5])
    anisotropy_tensor -= np.trace(anisotropy_tensor) * np.eye(3) / 3.0

    result: dict[str, object] = {
        "structure": structure,
        "structure_label": structure_label,
        "ell": np.arange(ell_max + 1, dtype=int),
        "mode_labels": _MODE_LABELS,
        "k_grid_mpc": k_grid.copy(),
        "C_ell": c_ell,
        "D_ell": d_ell,
        "diagonal_by_mode": diagonal_by_mode,
        "off_diagonal_blocks": offdiag_blocks,
        "off_diagonal_strategy": off_diagonal_strategy,
        "preferred_axis": preferred_axis,
        "anisotropy_tensor": anisotropy_tensor,
        "offdiag_strength": offdiag_strength,
        "rotation_strength": rotation_strength,
    }

    if off_diagonal_strategy == "dense_matrix":
        result["dense_covariance"] = _dense_from_blocks(
            blocks=offdiag_blocks,
            diagonal_by_mode=diagonal_by_mode,
        )
    elif off_diagonal_strategy == "wigner_d_sparse":
        result["wigner_d_sparse"] = _sparse_from_blocks(blocks=offdiag_blocks)

    return result
