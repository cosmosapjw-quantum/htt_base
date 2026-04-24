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

__all__ = [
    "assemble_bianchi_spectrum_covariance",
    "build_dense_harmonic_covariance",
    "extract_supported_harmonic_subspace",
    "compute_covariance_invariant_guard",
    "build_sparse_covariance_entries",
    "build_sparse_harmonic_entries",
    "compute_covariance_psd_guard",
    "compute_covariance_symmetry_guard",
]

_MODE_LABELS = ("m0", "m+2", "m-2")
_MODE_TO_M = {"m0": 0, "m+2": 2, "m-2": -2}
_T_CMB_K = 2.72548
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


def _dense_views_from_result(
    covariance_result: Mapping[str, object],
) -> dict[str, np.ndarray]:
    dense = covariance_result.get("dense_covariance")
    if isinstance(dense, Mapping):
        return {
            spec: np.asarray(dense[spec], dtype=float)
            for spec in ("TT", "EE", "TE", "BB")
        }
    return _dense_from_blocks(
        blocks=covariance_result["off_diagonal_blocks"],  # type: ignore[arg-type]
        diagonal_by_mode=covariance_result["diagonal_by_mode"],  # type: ignore[arg-type]
    )


def build_sparse_covariance_entries(
    covariance_result: Mapping[str, object],
    *,
    threshold: float = 0.0,
) -> dict[str, list[dict[str, object]]]:
    """Return a sparse off-diagonal covariance view with unique indices."""
    if threshold < 0.0:
        raise ValueError("threshold must be non-negative")
    sparse = covariance_result.get("wigner_d_sparse")
    if not isinstance(sparse, Mapping):
        sparse = _sparse_from_blocks(
            blocks=covariance_result["off_diagonal_blocks"],  # type: ignore[arg-type]
        )

    out: dict[str, list[dict[str, object]]] = {}
    for spec in ("TT", "EE", "TE", "BB"):
        seen: set[tuple[int, int, str]] = set()
        entries: list[dict[str, object]] = []
        for row in sparse.get(spec, []):  # type: ignore[union-attr]
            value = float(row["value"])
            if abs(value) <= threshold:
                continue
            key = (int(row["ell"]), int(row["ell_prime"]), str(row["mode"]))
            if key in seen:
                raise ValueError(
                    f"duplicate sparse covariance index for {spec}: {key}"
                )
            seen.add(key)
            entries.append(
                {
                    "ell": key[0],
                    "ell_prime": key[1],
                    "mode": key[2],
                    "value": value,
                }
            )
        out[spec] = entries
    return out


def _packed_flat_index(ell: int, m: int) -> int:
    return ell * ell + (m + ell)


def build_dense_harmonic_covariance(
    covariance_result: Mapping[str, object],
    *,
    threshold: float = 0.0,
) -> dict[str, object]:
    """Return a dense low-ell harmonic covariance payload on the supported subspace.

    The underlying covariance bundle is stored in the audited ``m in {0, +/-2}``
    support. This helper removes invalid low-ell ``|m| > ell`` rows, maps the
    remaining basis states onto the packed real-harmonic ordering used by the
    PSTF hierarchy, and exposes a dense covariance object suitable for a
    low-ell Gaussian likelihood on that supported harmonic subspace.
    """
    if threshold < 0.0:
        raise ValueError("threshold must be non-negative")
    dense = _dense_views_from_result(covariance_result)
    ell_values = np.asarray(covariance_result.get("ell", ()), dtype=int)
    mode_labels = tuple(
        str(label) for label in covariance_result.get("mode_labels", _MODE_LABELS)
    )
    if any(label not in _MODE_TO_M for label in mode_labels):
        raise ValueError("mode_labels must map to explicit harmonic m values")
    n_mode = len(mode_labels)
    if any(matrix.shape[0] != ell_values.size * n_mode for matrix in dense.values()):
        raise ValueError("dense covariance views do not match ell/mode dimensions")

    keep: list[int] = []
    support: list[dict[str, object]] = []
    invalid_mode_residual = 0.0
    for ell in ell_values.tolist():
        for mode_index, mode_label in enumerate(mode_labels):
            matrix_index = int(ell) * n_mode + mode_index
            m_value = _MODE_TO_M[mode_label]
            if abs(m_value) <= int(ell):
                keep.append(matrix_index)
                support.append(
                    {
                        "ell": int(ell),
                        "m": int(m_value),
                        "mode_label": mode_label,
                        "flat_index": _packed_flat_index(int(ell), int(m_value)),
                    }
                )
                continue
            for spec in ("TT", "EE", "TE", "BB"):
                matrix = np.asarray(dense[spec], dtype=float)
                invalid_mode_residual = max(
                    invalid_mode_residual,
                    float(np.max(np.abs(matrix[matrix_index]))),
                    float(np.max(np.abs(matrix[:, matrix_index]))),
                )

    if invalid_mode_residual > threshold:
        raise ValueError(
            "covariance bundle carries non-negligible support in invalid low-ell "
            f"mode slots (residual={invalid_mode_residual:.3e}, threshold={threshold:.3e})"
        )

    keep_arr = np.asarray(keep, dtype=int)
    sliced = {
        spec: np.asarray(matrix, dtype=float)[np.ix_(keep_arr, keep_arr)]
        for spec, matrix in dense.items()
    }
    return {
        "representation": "low_ell_harmonic_dense_gaussian",
        "harmonic_basis": "real_pstf_packed",
        "support": support,
        "subspace_size": int(len(support)),
        "dense_blocks": sliced,
        "invalid_mode_residual": float(invalid_mode_residual),
        "structure_label": covariance_result.get("structure_label", "unknown"),
        "preferred_axis": None
        if covariance_result.get("preferred_axis") is None
        else np.asarray(covariance_result["preferred_axis"], dtype=float),
        "anisotropy_tensor": None
        if covariance_result.get("anisotropy_tensor") is None
        else np.asarray(covariance_result["anisotropy_tensor"], dtype=float),
        "offdiag_strength": float(covariance_result.get("offdiag_strength", 0.0)),
        "rotation_strength": float(covariance_result.get("rotation_strength", 0.0)),
    }


def extract_supported_harmonic_subspace(
    alm_payload: Mapping[str, object] | np.ndarray,
    support: list[Mapping[str, object]] | tuple[Mapping[str, object], ...],
) -> np.ndarray:
    """Extract the supported harmonic subspace in the covariance order."""
    if isinstance(alm_payload, Mapping):
        if "values" not in alm_payload:
            raise KeyError("alm payload must contain 'values'")
        values = np.asarray(alm_payload["values"], dtype=float)
    else:
        values = np.asarray(alm_payload, dtype=float)
    if values.ndim != 1:
        raise ValueError(f"alm payload must be 1-D, got {values.shape}")
    extracted = np.zeros(len(support), dtype=float)
    for idx, row in enumerate(support):
        flat_index = int(row["flat_index"])
        if flat_index < 0 or flat_index >= values.size:
            raise ValueError(
                f"flat_index={flat_index} outside harmonic payload of size {values.size}"
            )
        extracted[idx] = float(values[flat_index])
    return extracted


def build_sparse_harmonic_entries(
    covariance_result: Mapping[str, object],
    *,
    threshold: float = 0.0,
) -> dict[str, list[dict[str, object]]]:
    """Return a sparse explicit `(ell,m; ell',m')` harmonic covariance view.

    This is still a low-`ell` basis reduction rather than a full BiPoSH
    inversion, but it removes the `m`-block proxy representation and exposes
    the actual harmonic support carried by the audited covariance bundle.
    """
    if threshold < 0.0:
        raise ValueError("threshold must be non-negative")
    dense = _dense_views_from_result(covariance_result)
    mode_labels = tuple(
        str(label) for label in covariance_result.get("mode_labels", _MODE_LABELS)
    )
    if any(label not in _MODE_TO_M for label in mode_labels):
        raise ValueError("mode_labels must map to explicit harmonic m values")
    n_mode = len(mode_labels)

    def _decode(index: int) -> tuple[int, int]:
        ell = index // n_mode
        mode_label = mode_labels[index % n_mode]
        return ell, _MODE_TO_M[mode_label]

    out: dict[str, list[dict[str, object]]] = {}
    for spec in ("TT", "EE", "TE", "BB"):
        matrix = np.asarray(dense[spec], dtype=float)
        rows: list[dict[str, object]] = []
        for i in range(matrix.shape[0]):
            for j in range(i + 1, matrix.shape[1]):
                value = float(matrix[i, j])
                if abs(value) <= threshold:
                    continue
                ell, m = _decode(i)
                ell_prime, m_prime = _decode(j)
                rows.append(
                    {
                        "ell": int(ell),
                        "m": int(m),
                        "ell_prime": int(ell_prime),
                        "m_prime": int(m_prime),
                        "value": value,
                    }
                )
        out[spec] = rows
    return out


def compute_covariance_psd_guard(
    covariance_result: Mapping[str, object],
    *,
    atol: float = 1.0e-12,
) -> dict[str, object]:
    """Check PSD-style guards for TT/EE/BB and the joint T/E block."""
    if atol < 0.0:
        raise ValueError("atol must be non-negative")
    dense = _dense_views_from_result(covariance_result)
    tt = np.asarray(dense["TT"], dtype=float)
    ee = np.asarray(dense["EE"], dtype=float)
    bb = np.asarray(dense["BB"], dtype=float)
    te = np.asarray(dense["TE"], dtype=float)
    te_joint = np.block([[tt, te], [te.T, ee]])

    def _min_eig(matrix: np.ndarray) -> float:
        sym = 0.5 * (matrix + matrix.T)
        return float(np.min(np.linalg.eigvalsh(sym)))

    tt_min = _min_eig(tt)
    ee_min = _min_eig(ee)
    bb_min = _min_eig(bb)
    te_joint_min = _min_eig(te_joint)
    return {
        "tolerance": float(atol),
        "tt_min_eig": tt_min,
        "ee_min_eig": ee_min,
        "bb_min_eig": bb_min,
        "te_joint_min_eig": te_joint_min,
        "passed": (
            tt_min >= -atol
            and ee_min >= -atol
            and bb_min >= -atol
            and te_joint_min >= -atol
        ),
    }


def compute_covariance_symmetry_guard(
    covariance_result: Mapping[str, object],
    *,
    atol: float = 1.0e-12,
) -> dict[str, object]:
    """Check that all dense covariance views are symmetric within tolerance."""
    if atol < 0.0:
        raise ValueError("atol must be non-negative")
    dense = _dense_views_from_result(covariance_result)

    def _max_asymmetry(matrix: np.ndarray) -> float:
        return float(np.max(np.abs(matrix - matrix.T)))

    tt = _max_asymmetry(np.asarray(dense["TT"], dtype=float))
    ee = _max_asymmetry(np.asarray(dense["EE"], dtype=float))
    bb = _max_asymmetry(np.asarray(dense["BB"], dtype=float))
    te = _max_asymmetry(np.asarray(dense["TE"], dtype=float))
    return {
        "tolerance": float(atol),
        "tt_max_asymmetry": tt,
        "ee_max_asymmetry": ee,
        "bb_max_asymmetry": bb,
        "te_max_asymmetry": te,
        "passed": max(tt, ee, bb, te) <= atol,
    }


def compute_covariance_invariant_guard(
    covariance_result: Mapping[str, object],
    *,
    atol: float = 1.0e-12,
) -> dict[str, object]:
    """Check preferred-axis and anisotropy-tensor consistency metadata."""
    if atol < 0.0:
        raise ValueError("atol must be non-negative")
    preferred_axis = covariance_result.get("preferred_axis")
    axis_norm = None
    axis_unit = None
    if preferred_axis is not None:
        axis = np.asarray(preferred_axis, dtype=float)
        axis_norm = float(np.linalg.norm(axis))
        axis_unit = bool(abs(axis_norm - 1.0) <= atol)

    tensor = covariance_result.get("anisotropy_tensor")
    trace = None
    symmetric = None
    tracefree = None
    if tensor is not None:
        arr = np.asarray(tensor, dtype=float)
        trace = float(np.trace(arr))
        symmetric = bool(np.max(np.abs(arr - arr.T)) <= atol)
        tracefree = bool(abs(trace) <= atol)

    offdiag_strength = float(covariance_result.get("offdiag_strength", 0.0))
    rotation_strength = float(covariance_result.get("rotation_strength", 0.0))
    nonnegative_strengths = bool(offdiag_strength >= -atol and rotation_strength >= -atol)
    passed = nonnegative_strengths
    if axis_unit is False:
        passed = False
    if symmetric is False or tracefree is False:
        passed = False
    return {
        "tolerance": float(atol),
        "preferred_axis_norm": axis_norm,
        "preferred_axis_is_unit": axis_unit,
        "anisotropy_tensor_trace": trace,
        "anisotropy_tensor_symmetric": symmetric,
        "anisotropy_tensor_tracefree": tracefree,
        "offdiag_strength_nonnegative": nonnegative_strengths,
        "rotation_strength_nonnegative": bool(rotation_strength >= -atol),
        "passed": passed,
    }


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
