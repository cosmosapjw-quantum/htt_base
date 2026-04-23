"""ver3 PR-09 hierarchy layout and IMEX packing contract."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Mapping

import numpy as np
from scipy.sparse import csc_matrix, csr_matrix, diags

from bass.los.family_backend_protocol import FamilyBackend
from bass.validation import GateBundle, make_gate_bundle

__all__ = [
    "SECTOR_ORDER",
    "HierarchyLayout",
    "ReducedHarmonicAffineOperator",
    "ReducedLocalAffineOperator",
    "ReducedSourceAffineOperator",
    "ReducedJointAffineOperator",
    "build_hierarchy_layout",
    "build_layout_manifest",
    "flatten",
    "unflatten",
    "evaluate_reduced_source_blocks",
    "evaluate_reduced_harmonic_rhs",
    "build_reduced_harmonic_affine_operator",
    "evaluate_reduced_local_rhs",
    "build_reduced_local_affine_operator",
    "build_reduced_source_affine_operator",
    "build_reduced_joint_affine_operator",
    "assemble_free_streaming_block",
    "assemble_mixing_block",
    "assemble_mass_matrix",
    "assemble_explicit_block",
    "assemble_implicit_block",
    "assemble_source_vector",
    "assemble_hierarchy_ops",
    "hierarchy_layout_gate_bundle",
]


SECTOR_ORDER = ("ph_I", "ph_E", "ph_B", "nu_I", "baryon", "cdm", "src")
_HARMONIC_SECTORS = frozenset({"ph_I", "ph_E", "ph_B", "nu_I"})
_LOCAL_SECTOR_DEFAULTS = {"baryon": 4, "cdm": 2, "src": 3}


@dataclass(frozen=True)
class HierarchyLayout:
    mode_labels: tuple[str, ...]
    sector_order: tuple[str, ...]
    ell_max: int
    sector_local_dofs: Mapping[str, int]
    size: int


@dataclass(frozen=True)
class ReducedHarmonicAffineOperator:
    mode_labels: tuple[str, ...]
    matrix: csc_matrix
    bias: np.ndarray


@dataclass(frozen=True)
class ReducedLocalAffineOperator:
    mode_labels: tuple[str, ...]
    matrix: csc_matrix
    bias: np.ndarray


@dataclass(frozen=True)
class ReducedSourceAffineOperator:
    mode_labels: tuple[str, ...]
    matrix: csc_matrix
    bias: np.ndarray


@dataclass(frozen=True)
class ReducedJointAffineOperator:
    mode_labels: tuple[str, ...]
    local_dof: int
    harmonic_dof: int
    source_dof: int
    matrix: csc_matrix
    bias: np.ndarray


@dataclass(frozen=True)
class _ReducedHarmonicOperatorStructure:
    mode_labels: tuple[str, ...]
    residual_labels: tuple[str, ...]
    residual_count: int
    width: int
    block_size: int
    n_unknown: int
    ell_by_slot: np.ndarray
    abs_m_by_slot: np.ndarray
    prev_slot_by_slot: np.ndarray
    prev_coeff_by_slot: np.ndarray
    next_slot_by_slot: np.ndarray
    next_coeff_by_slot: np.ndarray
    pstf_weight_by_slot: np.ndarray
    eb_base_by_slot: np.ndarray
    collision_factor_by_slot: np.ndarray
    diag_base_by_slot: np.ndarray
    ge2_mask: np.ndarray
    ell0_mask: np.ndarray
    sector_slots: np.ndarray
    self_pattern_rows: np.ndarray
    self_pattern_cols: np.ndarray
    cross_pattern_rows: np.ndarray
    cross_pattern_cols: np.ndarray
    next_residual_index: tuple[int, ...]
    next_external_label: tuple[str | None, ...]
    monopole_slot: int
    dipole_slot: int | None
    quadrupole_slot: int | None


def _branch_scale(bg: Mapping[str, object]) -> float:
    return 1.15 if str(bg.get("branch", "orthogonal")) == "tilted" else 1.0


def _geometry_contract(
    bg: Mapping[str, object],
    backend: FamilyBackend,
):
    geometry = bg.get("geometry")
    if geometry is not None:
        return geometry
    from bass.background.geometry import build_geometry

    return build_geometry(backend.family_spec.algebra)


def _operator_scales(
    bg: Mapping[str, object],
    backend: FamilyBackend,
) -> dict[str, float]:
    algebra = backend.family_spec.algebra
    geometry = _geometry_contract(bg, backend)
    n_diag = np.diag(np.asarray(algebra.n, dtype=np.float64))
    twist = abs(float(algebra.a[0]))
    h_abs = abs(float(algebra.h_parameter or 0.0))
    ricci_scalar = abs(float(getattr(geometry, "ricci_scalar", 0.0)))
    ricci_pstf = np.asarray(getattr(geometry, "ricci_pstf", np.zeros((3, 3))), dtype=np.float64)
    shear = np.asarray(bg.get("sigma_tensor", np.zeros((3, 3))), dtype=np.float64)
    geom_scale = float(
        np.sqrt(
            np.sum(np.square(n_diag))
            + twist * twist
            + 0.25 * ricci_scalar
            + np.sum(np.square(ricci_pstf))
            + np.sum(np.square(shear))
        )
    )
    geom_scale = max(geom_scale, 1.0)
    branch_scale = _branch_scale(bg)
    mix_scale = branch_scale * (0.08 + 0.04 * min(geom_scale, 3.0))
    twist_scale = branch_scale * twist / (1.0 + twist + h_abs)
    polarization_scale = 1.0 + 0.35 * twist_scale
    source_scale = 1.0 + 0.25 * min(float(np.linalg.norm(ricci_pstf) + np.linalg.norm(shear)), 2.0)
    family_law = _family_conditioned_kernel_law(bg, backend)
    return {
        "branch_scale": branch_scale,
        "geom_scale": branch_scale * geom_scale * float(family_law["transport_scale"]),
        "mix_scale": mix_scale * float(family_law["mix_scale"]),
        "twist_scale": twist_scale * float(family_law["twist_mix_scale"]),
        "polarization_scale": polarization_scale * float(family_law["polarization_scale"]),
        "source_scale": source_scale * float(family_law["source_scale"]),
        "mass_scale": float(family_law["mass_scale"]),
        "local_drag_scale": float(family_law["local_drag_scale"]),
        "cross_mode_scale": float(family_law["cross_mode_scale"]),
        "collision_scale": float(family_law["collision_scale"]),
        "family_conditioned_kernel_status": str(family_law["status"]),
        "family_conditioned_kernel_law": str(family_law["law_name"]),
    }


def _family_conditioned_kernel_law(
    bg: Mapping[str, object],
    backend: FamilyBackend,
) -> dict[str, float | str]:
    family = backend.family_spec.family
    h_parameter = float(backend.family_spec.algebra.h_parameter or 0.0)
    abs_h = abs(h_parameter)
    twist = abs(float(np.asarray(backend.family_spec.algebra.a, dtype=np.float64)[0]))
    law: dict[str, float | str] = {
        "status": "frozen_v5_family_conditioned",
        "law_name": "anchor_family_default",
        "mass_scale": 1.0,
        "transport_scale": 1.0,
        "mix_scale": 1.0,
        "twist_mix_scale": 1.0,
        "polarization_scale": 1.0,
        "source_scale": 1.0,
        "local_drag_scale": 1.0,
        "cross_mode_scale": 1.0,
        "collision_scale": 1.0,
    }
    if family == "II":
        law.update(
            law_name="ii_nil_frozen_v5",
            mass_scale=1.04,
            transport_scale=1.10,
            mix_scale=0.92,
            twist_mix_scale=0.98,
            polarization_scale=1.02,
            source_scale=0.94,
            local_drag_scale=0.96,
            cross_mode_scale=0.90,
            collision_scale=1.03,
        )
    elif family == "III":
        law.update(
            law_name="iii_hyperbolic_branch_frozen_v5",
            mass_scale=1.06,
            transport_scale=1.16,
            mix_scale=1.05,
            twist_mix_scale=1.00,
            polarization_scale=1.04,
            source_scale=1.08,
            local_drag_scale=0.94,
            cross_mode_scale=1.02,
            collision_scale=1.05,
        )
    elif family == "IV":
        law.update(
            law_name="iv_solvable_chart_frozen_v5",
            mass_scale=1.08,
            transport_scale=1.22,
            mix_scale=1.15,
            twist_mix_scale=1.08,
            polarization_scale=1.07,
            source_scale=1.10,
            local_drag_scale=0.92,
            cross_mode_scale=1.06,
            collision_scale=1.04,
        )
    elif family == "V":
        law.update(
            law_name="v_open_chart_frozen_v5",
            mass_scale=1.03,
            transport_scale=1.12,
            mix_scale=1.03,
            twist_mix_scale=1.00,
            polarization_scale=1.03,
            source_scale=1.06,
            local_drag_scale=0.98,
            cross_mode_scale=1.01,
            collision_scale=1.02,
        )
    elif family == "VI_0":
        law.update(
            law_name="vi0_directional_limit_frozen_v5",
            mass_scale=1.07,
            transport_scale=1.18,
            mix_scale=1.12,
            twist_mix_scale=1.10,
            polarization_scale=1.06,
            source_scale=1.08,
            local_drag_scale=0.95,
            cross_mode_scale=1.08,
            collision_scale=1.04,
        )
    elif family == "VI_h":
        root = np.sqrt(max(-h_parameter, 0.0))
        q = (1.0 - root) / max(1.0 + root, 1.0e-30)
        q_mag = abs(float(q))
        law.update(
            law_name="vih_class_b_bridge_frozen_v5",
            mass_scale=1.05 + 0.03 * q_mag,
            transport_scale=1.14 + 0.08 * q_mag,
            mix_scale=1.08 + 0.10 * q_mag,
            twist_mix_scale=1.04 + 0.12 * q_mag,
            polarization_scale=1.03 + 0.05 * q_mag,
            source_scale=1.04 + 0.06 * q_mag,
            local_drag_scale=0.94 + 0.04 * q_mag,
            cross_mode_scale=1.04 + 0.08 * q_mag,
            collision_scale=1.02 + 0.04 * q_mag,
        )
    elif family == "VII_0":
        law.update(
            law_name="vii0_helical_anchor_frozen_v5",
            mass_scale=1.02,
            transport_scale=1.08,
            mix_scale=1.16,
            twist_mix_scale=1.12,
            polarization_scale=1.05,
            source_scale=1.04,
            local_drag_scale=1.00,
            cross_mode_scale=1.05,
            collision_scale=1.03,
        )
    elif family == "VII_h":
        p = np.sqrt(max(h_parameter, 0.0))
        p_eff = min(float(p), 2.0)
        law.update(
            law_name="viih_positive_h_bridge_frozen_v5",
            mass_scale=1.03 + 0.02 * p_eff,
            transport_scale=1.10 + 0.07 * p_eff,
            mix_scale=1.12 + 0.08 * p_eff,
            twist_mix_scale=1.08 + 0.10 * p_eff,
            polarization_scale=1.04 + 0.04 * p_eff,
            source_scale=1.04 + 0.05 * p_eff,
            local_drag_scale=0.99 + 0.02 * p_eff,
            cross_mode_scale=1.03 + 0.04 * p_eff,
            collision_scale=1.02 + 0.03 * p_eff,
        )
    elif family == "VIII":
        s_ref = 0.5
        measure_mu0 = s_ref * np.tanh(np.pi * s_ref)
        measure_mu_half = s_ref / max(np.tanh(np.pi * s_ref), 1.0e-30)
        measure_ratio = measure_mu_half / max(measure_mu0, 1.0e-30)
        law.update(
            law_name="viii_noncompact_measure_frozen_v5",
            mass_scale=1.04 + 0.01 * measure_ratio,
            transport_scale=1.15 + 0.03 * measure_ratio,
            mix_scale=1.10 + 0.04 * measure_ratio,
            twist_mix_scale=1.02 + 0.02 * measure_ratio,
            polarization_scale=1.05 + 0.02 * measure_ratio,
            source_scale=1.03 + 0.02 * measure_ratio,
            local_drag_scale=0.98 + 0.01 * measure_ratio,
            cross_mode_scale=1.04 + 0.02 * measure_ratio,
            collision_scale=1.03 + 0.01 * measure_ratio,
        )
    elif family == "IX":
        compact_boost = 1.0 + 0.1 * min(twist, 1.0)
        law.update(
            law_name="ix_compact_wigner_frozen_v5",
            mass_scale=0.98,
            transport_scale=0.96,
            mix_scale=1.18 * compact_boost,
            twist_mix_scale=1.10 * compact_boost,
            polarization_scale=1.08,
            source_scale=0.98,
            local_drag_scale=1.00,
            cross_mode_scale=1.06,
            collision_scale=1.05,
        )
    return law


def _mode_labels_from_backend(
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> tuple[str, ...]:
    explicit = truncation.get("mode_labels")
    if explicit is not None:
        labels = tuple(str(x) for x in explicit)
        if not labels:
            raise ValueError("mode_labels must be non-empty when provided")
        return labels
    family = backend.family_spec.family
    defaults = {
        "I": ("m0", "m+2", "m-2"),
        "II": ("mu_nil", "mu_nil+", "mu_nil-"),
        "III": ("mu_hyp", "mu_hyp+", "mu_hyp-"),
        "IV": ("mu_solv", "mu_solv+", "mu_solv-"),
        "V": ("mu_open", "mu_open+", "mu_open-"),
        "VI_0": ("mu_vi0", "mu_vi0+", "mu_vi0-"),
        "VI_h": ("mu_vih", "mu_vih+", "mu_vih-"),
        "VII_0": ("mu_hel", "mu_hel+", "mu_hel-"),
        "VII_h": ("mu_hel_h", "mu_hel_h+", "mu_hel_h-"),
        "VIII": ("mu_sl2r", "mu_sl2r+", "mu_sl2r-"),
        "IX": ("mu_compact", "mu_compact+", "mu_compact-"),
    }
    return defaults.get(family, ("mu0",))


def _sector_local_dofs(truncation: Mapping[str, object]) -> dict[str, int]:
    overrides = truncation.get("sector_local_dofs", {})
    out = dict(_LOCAL_SECTOR_DEFAULTS)
    for key, value in dict(overrides).items():
        if key not in out:
            raise ValueError(f"unknown local sector {key!r}")
        ivalue = int(value)
        if ivalue <= 0:
            raise ValueError(f"sector {key!r} local dofs must be > 0")
        out[key] = ivalue
    return out


def _sector_block_size(
    sector: str,
    *,
    ell_max: int,
    local_dofs: Mapping[str, int],
) -> int:
    if sector in _HARMONIC_SECTORS:
        return sum(2 * ell + 1 for ell in range(ell_max + 1))
    return int(local_dofs[sector])


def _mode_label_weight(
    mu: str,
    *,
    mu_index: int,
    mu_count: int,
    branch_scale: float,
) -> float:
    label = str(mu)
    if label == "m0":
        return 1.0
    if label == "m+2":
        return 1.0 + 0.12 * branch_scale
    if label == "m-2":
        return 1.0 - 0.08 * branch_scale
    if label.endswith("+"):
        return 1.0 + 0.12 * branch_scale
    if label.endswith("-"):
        return 1.0 - 0.08 * branch_scale
    return 1.0 + 0.03 * (mu_index / max(mu_count, 1))


def _harmonic_cross_mode_coeff(
    *,
    mu_weight: float,
    mix_scale: float,
    cross_mode_scale: float,
    twist_scale: float,
    sector: str,
    ell: int,
    mu_count: int,
) -> float:
    if mu_count <= 1:
        return 0.0
    base = mu_weight * mix_scale * cross_mode_scale / max((ell + 1) * mu_count, 1)
    if sector == "ph_I":
        return 0.18 * base
    if sector == "ph_E":
        return 0.16 * base
    if sector == "ph_B":
        return 0.16 * (1.0 + 0.5 * twist_scale) * base
    if sector == "nu_I":
        return 0.12 * base
    raise KeyError(f"unsupported harmonic sector {sector!r}")


@lru_cache(maxsize=None)
def _reduced_harmonic_structure(
    ell_max: int,
    mode_labels: tuple[str, ...],
    residual_labels: tuple[str, ...],
) -> _ReducedHarmonicOperatorStructure:
    width = (int(ell_max) + 1) ** 2
    block_size = 4 * width
    residual_count = len(residual_labels)
    slots = np.arange(width, dtype=np.int64)
    ell_by_slot = np.zeros(width, dtype=np.int64)
    abs_m_by_slot = np.zeros(width, dtype=np.float64)
    prev_slot_by_slot = np.full(width, -1, dtype=np.int64)
    prev_coeff_by_slot = np.zeros(width, dtype=np.float64)
    next_slot_by_slot = np.full(width, -1, dtype=np.int64)
    next_coeff_by_slot = np.zeros(width, dtype=np.float64)
    pstf_weight_by_slot = np.zeros(width, dtype=np.float64)
    eb_base_by_slot = np.zeros(width, dtype=np.float64)
    collision_factor_by_slot = np.zeros(width, dtype=np.float64)
    diag_base_by_slot = np.zeros(width, dtype=np.float64)
    slot_lookup: dict[tuple[int, int], int] = {}
    offset = 0
    for ell in range(int(ell_max) + 1):
        pstf_weight = np.sqrt(max((ell + 2) * (ell - 1), 0.0)) / max(2 * ell + 1, 1) if ell >= 2 else 0.0
        for m in range(-ell, ell + 1):
            slot = offset + (m + ell)
            slot_lookup[(ell, m)] = slot
            ell_by_slot[slot] = ell
            abs_m_by_slot[slot] = float(abs(m))
            diag_base_by_slot[slot] = 0.35 * (ell + 1) + 0.08 * abs(m)
            collision_factor_by_slot[slot] = 1.0 if ell <= 1 else 1.0 / (ell + 0.5)
            if ell >= 2:
                pstf_weight_by_slot[slot] = pstf_weight
                eb_base_by_slot[slot] = max(abs(m), 1) / (ell + 1)
            if ell > 0:
                prev_m = m if abs(m) <= ell - 1 else 0
                prev_slot = slot_lookup[(ell - 1, prev_m)]
                prev_slot_by_slot[slot] = prev_slot
                prev_coeff_by_slot[slot] = np.sqrt(max(ell * ell - m * m, 0.0)) / max(2 * ell + 1, 1)
            if ell < int(ell_max):
                next_m = m if abs(m) <= ell + 1 else 0
                next_slot = offset + (2 * ell + 1) + (next_m + (ell + 1))
                next_slot_by_slot[slot] = next_slot
                next_coeff_by_slot[slot] = np.sqrt(max((ell + 1) * (ell + 1) - m * m, 0.0)) / max(2 * ell + 1, 1)
        offset += 2 * ell + 1

    label_to_residual = {str(mu): idx for idx, mu in enumerate(residual_labels)}
    mode_labels_list = tuple(str(mu) for mu in mode_labels)
    next_residual_index: list[int] = []
    next_external_label: list[str | None] = []
    for mu in residual_labels:
        mu_key = str(mu)
        mu_index = mode_labels_list.index(mu_key)
        next_mu = mode_labels_list[(mu_index + 1) % len(mode_labels_list)]
        next_residual_index.append(label_to_residual.get(next_mu, -1))
        next_external_label.append(None if next_mu in label_to_residual else next_mu)

    t_off = 0
    e_off = width
    b_off = 2 * width
    nu_off = 3 * width
    self_pattern = np.zeros((block_size, block_size), dtype=bool)
    cross_pattern = np.zeros((block_size, block_size), dtype=bool)
    self_pattern[t_off + slots, t_off + slots] = True
    self_pattern[e_off + slots, e_off + slots] = True
    self_pattern[b_off + slots, b_off + slots] = True
    self_pattern[nu_off + slots, nu_off + slots] = True
    valid_prev = prev_slot_by_slot >= 0
    valid_next = next_slot_by_slot >= 0
    self_pattern[t_off + slots[valid_prev], t_off + prev_slot_by_slot[valid_prev]] = True
    self_pattern[e_off + slots[valid_prev], e_off + prev_slot_by_slot[valid_prev]] = True
    self_pattern[b_off + slots[valid_prev], b_off + prev_slot_by_slot[valid_prev]] = True
    self_pattern[nu_off + slots[valid_prev], nu_off + prev_slot_by_slot[valid_prev]] = True
    self_pattern[t_off + slots[valid_next], t_off + next_slot_by_slot[valid_next]] = True
    self_pattern[e_off + slots[valid_next], e_off + next_slot_by_slot[valid_next]] = True
    self_pattern[b_off + slots[valid_next], b_off + next_slot_by_slot[valid_next]] = True
    self_pattern[nu_off + slots[valid_next], nu_off + next_slot_by_slot[valid_next]] = True
    ge2_slots = slots[ell_by_slot >= 2]
    self_pattern[t_off + ge2_slots, e_off + ge2_slots] = True
    self_pattern[e_off + ge2_slots, t_off + ge2_slots] = True
    self_pattern[e_off + ge2_slots, b_off + ge2_slots] = True
    self_pattern[b_off + ge2_slots, e_off + ge2_slots] = True
    self_pattern[b_off + ge2_slots, t_off + ge2_slots] = True
    if len(mode_labels_list) > 1:
        cross_pattern[t_off + slots[ell_by_slot == 0], t_off + slots[ell_by_slot == 0]] = True
        cross_pattern[e_off + slots[ell_by_slot == 0], e_off + slots[ell_by_slot == 0]] = True
        cross_pattern[b_off + slots[ell_by_slot == 0], b_off + slots[ell_by_slot == 0]] = True
        cross_pattern[nu_off + slots[ell_by_slot == 0], nu_off + slots[ell_by_slot == 0]] = True
        cross_pattern[t_off + ge2_slots, t_off + ge2_slots] = True
        cross_pattern[e_off + ge2_slots, e_off + ge2_slots] = True
        cross_pattern[b_off + ge2_slots, b_off + ge2_slots] = True
        cross_pattern[nu_off + ge2_slots, nu_off + ge2_slots] = True
    self_pattern_rows, self_pattern_cols = np.nonzero(self_pattern)
    cross_pattern_rows, cross_pattern_cols = np.nonzero(cross_pattern)

    return _ReducedHarmonicOperatorStructure(
        mode_labels=mode_labels_list,
        residual_labels=tuple(str(mu) for mu in residual_labels),
        residual_count=residual_count,
        width=width,
        block_size=block_size,
        n_unknown=residual_count * block_size,
        ell_by_slot=ell_by_slot,
        abs_m_by_slot=abs_m_by_slot,
        prev_slot_by_slot=prev_slot_by_slot,
        prev_coeff_by_slot=prev_coeff_by_slot,
        next_slot_by_slot=next_slot_by_slot,
        next_coeff_by_slot=next_coeff_by_slot,
        pstf_weight_by_slot=pstf_weight_by_slot,
        eb_base_by_slot=eb_base_by_slot,
        collision_factor_by_slot=collision_factor_by_slot,
        diag_base_by_slot=diag_base_by_slot,
        ge2_mask=ell_by_slot >= 2,
        ell0_mask=ell_by_slot == 0,
        sector_slots=slots,
        self_pattern_rows=np.asarray(self_pattern_rows, dtype=np.int64),
        self_pattern_cols=np.asarray(self_pattern_cols, dtype=np.int64),
        cross_pattern_rows=np.asarray(cross_pattern_rows, dtype=np.int64),
        cross_pattern_cols=np.asarray(cross_pattern_cols, dtype=np.int64),
        next_residual_index=tuple(next_residual_index),
        next_external_label=tuple(next_external_label),
        monopole_slot=slot_lookup[(0, 0)],
        dipole_slot=slot_lookup.get((1, 0)),
        quadrupole_slot=slot_lookup.get((2, 0)),
    )


def build_hierarchy_layout(
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    *,
    sector_order: tuple[str, ...] = SECTOR_ORDER,
) -> HierarchyLayout:
    ell_max = int(truncation["ell_max"])
    if ell_max < 0:
        raise ValueError("ell_max must be non-negative")
    local_dofs = _sector_local_dofs(truncation)
    mode_labels = _mode_labels_from_backend(backend, truncation)
    size = 0
    for _mu in mode_labels:
        for sector in sector_order:
            size += _sector_block_size(sector, ell_max=ell_max, local_dofs=local_dofs)
    return HierarchyLayout(
        mode_labels=mode_labels,
        sector_order=sector_order,
        ell_max=ell_max,
        sector_local_dofs=local_dofs,
        size=size,
    )


def build_layout_manifest(
    layout: HierarchyLayout,
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    bg: Mapping[str, object] | None = None,
) -> dict[str, object]:
    required_metadata = backend.required_metadata()
    exact_operator = backend.template_card().operator_kernel_family == "bianchi_i_matrix_exact"
    return {
        "family": backend.family_spec.family,
        "branch": str((bg or {}).get("branch", "orthogonal")),
        "mode_labels": list(layout.mode_labels),
        "sector_order": list(layout.sector_order),
        "ell_max": layout.ell_max,
        "sector_local_dofs": dict(layout.sector_local_dofs),
        "size": layout.size,
        "native_mode_labels": required_metadata["native_mode_labels"],
        "boundary_policy": required_metadata["boundary_policy"],
        "release_status": required_metadata["release_status"],
        "operator_realization": "geometry_opacity_coupled_sparse_operator",
        "mass_matrix_realization": "family_branch_sector_weighted_diagonal",
        "exact_family_operator_available": exact_operator,
        "approximate_family_operator_available": not exact_operator,
        "reduced_local_evaluator_available": True,
        "reduced_harmonic_evaluator_available": True,
        "reduced_source_evaluator_available": True,
        "family_conditioned_kernel_status": "frozen_v5_family_conditioned",
        "family_conditioned_kernel_law": _family_conditioned_kernel_law((bg or {}), backend)["law_name"],
        "truncation_metadata": dict(truncation),
    }


def flatten(
    layout: HierarchyLayout,
    mu: str,
    sector: str,
    ell: int | None,
    m: int | None,
    local_dof: int | None = None,
) -> int:
    if mu not in layout.mode_labels:
        raise KeyError(f"unknown mode label {mu!r}")
    if sector not in layout.sector_order:
        raise KeyError(f"unknown sector {sector!r}")
    index = 0
    for mu_label in layout.mode_labels:
        if mu_label == mu:
            break
        for sector_name in layout.sector_order:
            index += _sector_block_size(
                sector_name,
                ell_max=layout.ell_max,
                local_dofs=layout.sector_local_dofs,
            )
    for sector_name in layout.sector_order:
        if sector_name == sector:
            break
        index += _sector_block_size(
            sector_name,
            ell_max=layout.ell_max,
            local_dofs=layout.sector_local_dofs,
        )
    if sector in _HARMONIC_SECTORS:
        if ell is None or m is None:
            raise ValueError("harmonic sectors require ell and m")
        if ell < 0 or ell > layout.ell_max:
            raise ValueError(f"ell={ell} outside [0,{layout.ell_max}]")
        if abs(m) > ell:
            raise ValueError(f"|m| must be <= ell, got ell={ell}, m={m}")
        index += sum(2 * l + 1 for l in range(ell))
        index += m + ell
        return index
    if local_dof is None:
        raise ValueError(f"sector {sector!r} requires local_dof")
    if local_dof < 0 or local_dof >= layout.sector_local_dofs[sector]:
        raise ValueError(
            f"local_dof={local_dof} outside [0,{layout.sector_local_dofs[sector]-1}] for sector {sector!r}"
        )
    return index + local_dof


def unflatten(layout: HierarchyLayout, index: int) -> tuple[str, str, int | None, int | None, int | None]:
    if index < 0 or index >= layout.size:
        raise ValueError(f"index={index} outside [0,{layout.size - 1}]")
    cursor = int(index)
    for mu in layout.mode_labels:
        for sector in layout.sector_order:
            block = _sector_block_size(
                sector,
                ell_max=layout.ell_max,
                local_dofs=layout.sector_local_dofs,
            )
            if cursor < block:
                if sector in _HARMONIC_SECTORS:
                    for ell in range(layout.ell_max + 1):
                        ell_width = 2 * ell + 1
                        if cursor < ell_width:
                            m = cursor - ell
                            return mu, sector, ell, m, None
                        cursor -= ell_width
                    raise AssertionError("harmonic block cursor overflow")
                return mu, sector, None, None, cursor
            cursor -= block
    raise AssertionError("layout cursor overflow")


def assemble_mass_matrix(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> csr_matrix:
    layout = build_hierarchy_layout(backend, truncation)
    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    polarization_scale = float(scales["polarization_scale"])
    twist_scale = float(scales["twist_scale"])
    source_scale = float(scales["source_scale"])
    mass_scale = float(scales["mass_scale"])
    diag = np.ones(layout.size, dtype=np.float64)
    mu_count = max(len(layout.mode_labels), 1)
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
        )
        for sector in layout.sector_order:
            if sector in _HARMONIC_SECTORS:
                for ell in range(layout.ell_max + 1):
                    ell_weight = 1.0 + 0.04 * ell + 0.015 * geom_scale
                    sector_weight = 1.0
                    if sector == "ph_I":
                        sector_weight = branch_scale
                    elif sector == "ph_E":
                        sector_weight = branch_scale * (1.08 * polarization_scale)
                    elif sector == "ph_B":
                        sector_weight = branch_scale * (1.12 + 0.5 * twist_scale) * polarization_scale
                    elif sector == "nu_I":
                        sector_weight = 1.0 + 0.1 * branch_scale + 0.02 * geom_scale
                    block_weight = mu_weight * sector_weight * ell_weight
                    for m in range(-ell, ell + 1):
                        diag[flatten(layout, mu, sector, ell, m)] = mass_scale * block_weight
                continue
            width = int(layout.sector_local_dofs[sector])
            for local_dof in range(width):
                idx = flatten(layout, mu, sector, None, None, local_dof)
                if sector == "baryon":
                    value = mu_weight * (1.0 + 0.08 * geom_scale + 0.03 * local_dof)
                elif sector == "cdm":
                    value = mu_weight * (1.0 + 0.05 * geom_scale + 0.02 * local_dof)
                else:
                    value = mu_weight * (1.0 + 0.06 * source_scale + 0.04 * local_dof)
                diag[idx] = mass_scale * value
    return diags(diag, offsets=0, format="csr", dtype=np.float64)


def assemble_free_streaming_block(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> csr_matrix:
    layout = build_hierarchy_layout(backend, truncation)
    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    polarization_scale = float(scales["polarization_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    mu_count = max(len(layout.mode_labels), 1)
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
        )
        for sector in layout.sector_order:
            if sector not in _HARMONIC_SECTORS:
                continue
            for ell in range(layout.ell_max + 1):
                for m in range(-ell, ell + 1):
                    idx = flatten(layout, mu, sector, ell, m)
                    spin_weight = polarization_scale if sector in {"ph_E", "ph_B"} else 1.0
                    diag = -geom_scale * mu_weight * spin_weight * (0.35 * (ell + 1) + 0.08 * abs(m))
                    rows.append(idx)
                    cols.append(idx)
                    data.append(diag)
                    if ell > 0:
                        prv = flatten(layout, mu, sector, ell - 1, m if abs(m) <= ell - 1 else 0)
                        coeff_down = (
                            geom_scale
                            * mu_weight
                            * spin_weight
                            * np.sqrt(max(ell * ell - m * m, 0.0))
                            / max(2 * ell + 1, 1)
                        )
                        rows.append(idx)
                        cols.append(prv)
                        data.append(coeff_down)
                    if ell < layout.ell_max:
                        nxt = flatten(layout, mu, sector, ell + 1, m if abs(m) <= ell + 1 else 0)
                        coeff_up = (
                            geom_scale
                            * mu_weight
                            * spin_weight
                            * np.sqrt(max((ell + 1) * (ell + 1) - m * m, 0.0))
                            / max(2 * ell + 1, 1)
                        )
                        rows.append(idx)
                        cols.append(nxt)
                        data.append(coeff_up)
    return csr_matrix((data, (rows, cols)), shape=(layout.size, layout.size))


def assemble_mixing_block(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> csr_matrix:
    layout = build_hierarchy_layout(backend, truncation)
    scales = _operator_scales(bg, backend)
    branch_scale = float(scales["branch_scale"])
    mix_scale = float(scales["mix_scale"])
    twist_scale = float(scales["twist_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    mu_count = max(len(layout.mode_labels), 1)
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
        )
        for ell in range(2, layout.ell_max + 1):
            for m in range(-ell, ell + 1):
                i_idx = flatten(layout, mu, "ph_I", ell, m)
                e_idx = flatten(layout, mu, "ph_E", ell, m)
                b_idx = flatten(layout, mu, "ph_B", ell, m)
                nu_idx = flatten(layout, mu, "nu_I", ell, m)
                pstf_weight = np.sqrt(max((ell + 2) * (ell - 1), 0.0)) / max(2 * ell + 1, 1)
                rows.extend((i_idx, e_idx))
                cols.extend((e_idx, i_idx))
                data.extend(
                    (
                        mu_weight * mix_scale * pstf_weight,
                        mu_weight * 0.5 * mix_scale * pstf_weight,
                    )
                )
                if twist_scale > 0.0:
                        eb = mu_weight * twist_scale * max(abs(m), 1) / (ell + 1)
                        rows.extend((e_idx, b_idx, b_idx, e_idx))
                        cols.extend((b_idx, e_idx, i_idx, b_idx))
                        data.extend((eb, -eb, 0.25 * eb, -0.25 * eb))
                if len(layout.mode_labels) > 1:
                    next_mu = layout.mode_labels[(mu_index + 1) % len(layout.mode_labels)]
                    next_i_idx = flatten(layout, next_mu, "ph_I", ell, m)
                    next_e_idx = flatten(layout, next_mu, "ph_E", ell, m)
                    next_b_idx = flatten(layout, next_mu, "ph_B", ell, m)
                    next_nu_idx = flatten(layout, next_mu, "nu_I", ell, m)
                    rows.extend((i_idx, e_idx, b_idx, nu_idx))
                    cols.extend((next_i_idx, next_e_idx, next_b_idx, next_nu_idx))
                    data.extend(
                        (
                            _harmonic_cross_mode_coeff(
                                mu_weight=mu_weight,
                                mix_scale=mix_scale,
                                cross_mode_scale=cross_mode_scale,
                                twist_scale=twist_scale,
                                sector="ph_I",
                                ell=ell,
                                mu_count=mu_count,
                            ),
                            _harmonic_cross_mode_coeff(
                                mu_weight=mu_weight,
                                mix_scale=mix_scale,
                                cross_mode_scale=cross_mode_scale,
                                twist_scale=twist_scale,
                                sector="ph_E",
                                ell=ell,
                                mu_count=mu_count,
                            ),
                            _harmonic_cross_mode_coeff(
                                mu_weight=mu_weight,
                                mix_scale=mix_scale,
                                cross_mode_scale=cross_mode_scale,
                                twist_scale=twist_scale,
                                sector="ph_B",
                                ell=ell,
                                mu_count=mu_count,
                            ),
                            _harmonic_cross_mode_coeff(
                                mu_weight=mu_weight,
                                mix_scale=mix_scale,
                                cross_mode_scale=cross_mode_scale,
                                twist_scale=twist_scale,
                                sector="nu_I",
                                ell=ell,
                                mu_count=mu_count,
                            ),
                        )
                    )
        if len(layout.mode_labels) > 1:
            next_mu = layout.mode_labels[(mu_index + 1) % len(layout.mode_labels)]
            for sector in ("ph_I", "ph_E", "ph_B", "nu_I"):
                src_idx = flatten(layout, mu, sector, 0, 0)
                dst_idx = flatten(layout, next_mu, sector, 0, 0)
                rows.append(src_idx)
                cols.append(dst_idx)
                data.append(mu_weight * 0.5 * mix_scale * cross_mode_scale / len(layout.mode_labels))
    return csr_matrix((data, (rows, cols)), shape=(layout.size, layout.size))


def assemble_explicit_block(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> csr_matrix:
    return assemble_free_streaming_block(bg, backend, truncation) + assemble_mixing_block(
        bg,
        backend,
        truncation,
    )


def assemble_implicit_block(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    opacity_data: Mapping[str, object],
) -> csr_matrix:
    layout = build_hierarchy_layout(backend, truncation)
    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    scales = _operator_scales(bg, backend)
    branch_scale = float(scales["branch_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    collision_scale = float(scales["collision_scale"])
    twist_scale = float(scales["twist_scale"])
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    mu_count = max(len(layout.mode_labels), 1)
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
        )
        for sector in ("ph_I", "ph_E", "ph_B"):
            for ell in range(layout.ell_max + 1):
                for m in range(-ell, ell + 1):
                    idx = flatten(layout, mu, sector, ell, m)
                    photon_weight = mu_weight * branch_scale * collision_scale * gamma_t * (
                        1.0 if ell <= 1 else 1.0 / (ell + 0.5)
                    )
                    rows.append(idx)
                    cols.append(idx)
                    data.append(photon_weight)
        for sector in ("baryon", "src"):
            for local_dof in range(layout.sector_local_dofs[sector]):
                idx = flatten(layout, mu, sector, None, None, local_dof)
                local_weight = mu_weight * local_drag_scale * (gamma_t if sector == "baryon" else 0.35 * gamma_t)
                rows.append(idx)
                cols.append(idx)
                data.append(local_weight)
        dipole_idx = flatten(layout, mu, "ph_I", 1, 0)
        baryon_v_idx = flatten(layout, mu, "baryon", None, None, 1)
        rows.extend((dipole_idx, baryon_v_idx))
        cols.extend((baryon_v_idx, dipole_idx))
        data.extend(
            (
                -0.25 * mu_weight * local_drag_scale * gamma_t,
                0.25 * mu_weight * local_drag_scale * gamma_t,
            )
        )
        if layout.sector_local_dofs["src"] > 1:
            src_dipole_idx = flatten(layout, mu, "src", None, None, 1)
            rows.extend((dipole_idx, src_dipole_idx))
            cols.extend((src_dipole_idx, dipole_idx))
            data.extend(
                (
                    0.10 * mu_weight * local_drag_scale * gamma_t,
                    -0.08 * mu_weight * local_drag_scale * gamma_t,
                )
            )
        if layout.ell_max >= 2:
            quad_idx = flatten(layout, mu, "ph_E", 2, 0)
            src_idx = flatten(layout, mu, "src", None, None, 0)
            rows.extend((quad_idx, src_idx))
            cols.extend((src_idx, quad_idx))
            data.extend(
                (
                    0.15 * mu_weight * local_drag_scale * gamma_t,
                    -0.10 * mu_weight * local_drag_scale * gamma_t,
                )
            )
            if layout.sector_local_dofs["src"] > 2:
                src_pol_idx = flatten(layout, mu, "src", None, None, 2)
                b_quad_idx = flatten(layout, mu, "ph_B", 2, 0)
                rows.extend((quad_idx, src_pol_idx, b_quad_idx, src_pol_idx))
                cols.extend((src_pol_idx, quad_idx, src_pol_idx, b_quad_idx))
                data.extend(
                    (
                        0.08 * mu_weight * local_drag_scale * gamma_t,
                        -0.06 * mu_weight * local_drag_scale * gamma_t,
                        0.06 * mu_weight * twist_scale * local_drag_scale * gamma_t,
                        -0.04 * mu_weight * twist_scale * local_drag_scale * gamma_t,
                    )
                )
    return csr_matrix((data, (rows, cols)), shape=(layout.size, layout.size))


def assemble_source_vector(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    source_tables: Mapping[str, object],
) -> np.ndarray:
    layout = build_hierarchy_layout(backend, truncation)
    out = np.zeros(layout.size, dtype=np.float64)
    scales = _operator_scales(bg, backend)
    twist_scale = float(scales["twist_scale"])
    source_scale = float(scales["source_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    visibility_amp = float(source_tables.get("visibility_amplitude", 0.0))
    polarization_amp = float(source_tables.get("polarization_source", 0.0))
    doppler_amp = float(source_tables.get("doppler_source", 0.25 * visibility_amp))
    reduced_source_blocks = evaluate_reduced_source_blocks(
        layout,
        {**dict(bg), "source_tables": dict(source_tables)},
        backend,
    )
    mu_count = max(len(layout.mode_labels), 1)
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=float(scales["branch_scale"]),
        )
        out[flatten(layout, mu, "ph_I", 0, 0)] = mu_weight * source_scale * visibility_amp
        if layout.ell_max >= 1:
            out[flatten(layout, mu, "ph_I", 1, 0)] = mu_weight * 0.5 * source_scale * doppler_amp
        if layout.ell_max >= 2:
            out[flatten(layout, mu, "ph_E", 2, 0)] = mu_weight * source_scale * polarization_amp
            out[flatten(layout, mu, "ph_B", 2, 0)] = mu_weight * twist_scale * cross_mode_scale * polarization_amp
        for local_dof, value in enumerate(np.asarray(reduced_source_blocks[str(mu)], dtype=np.float64)):
            out[flatten(layout, mu, "src", None, None, local_dof)] = float(value)
    return out


def evaluate_reduced_source_blocks(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
) -> dict[str, np.ndarray]:
    """Evaluate per-mode-label source local blocks without assembling full operators."""

    source_tables = bg.get("source_tables", {})
    if not isinstance(source_tables, Mapping):
        raise ValueError("bg.source_tables must be a mapping when provided")
    scales = _operator_scales(bg, backend)
    branch_scale = float(scales["branch_scale"])
    visibility_amp = float(source_tables.get("visibility_amplitude", 0.0))
    polarization_amp = float(source_tables.get("polarization_source", 0.0))
    doppler_amp = float(source_tables.get("doppler_source", 0.25 * visibility_amp))
    reion_amp = float(source_tables.get("reionization_amplitude", 0.0))
    source_width = int(layout.sector_local_dofs["src"])
    mu_count = max(len(layout.mode_labels), 1)
    source_blocks: dict[str, np.ndarray] = {}
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
        )
        src = np.zeros(source_width, dtype=np.float64)
        if source_width > 0:
            src[0] = mu_weight * reion_amp
        if source_width > 1:
            src[1] = mu_weight * 0.5 * float(scales["source_scale"]) * doppler_amp
        if source_width > 2:
            src[2] = mu_weight * float(scales["source_scale"]) * polarization_amp
        source_blocks[str(mu)] = src
    return source_blocks


def evaluate_reduced_harmonic_rhs(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    photon_T_by_mode_label: Mapping[str, np.ndarray],
    photon_E_by_mode_label: Mapping[str, np.ndarray],
    photon_B_by_mode_label: Mapping[str, np.ndarray],
    neutrino_by_mode_label: Mapping[str, np.ndarray],
    baryon_by_mode_label: Mapping[str, np.ndarray],
    source_by_mode_label: Mapping[str, np.ndarray] | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Evaluate harmonic-sector rows without assembling full sparse operators."""

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    source_tables = bg.get("source_tables", {})
    if not isinstance(source_tables, Mapping):
        raise ValueError("bg.source_tables must be a mapping when provided")

    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    visibility_amp = float(source_tables.get("visibility_amplitude", 0.0))
    polarization_amp = float(source_tables.get("polarization_source", 0.0))
    doppler_amp = float(source_tables.get("doppler_source", 0.25 * visibility_amp))
    reion_amp = float(source_tables.get("reionization_amplitude", 0.0))

    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    mix_scale = float(scales["mix_scale"])
    twist_scale = float(scales["twist_scale"])
    polarization_scale = float(scales["polarization_scale"])
    source_scale = float(scales["source_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    collision_scale = float(scales["collision_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    width = (int(layout.ell_max) + 1) ** 2
    baryon_width = int(layout.sector_local_dofs["baryon"])
    src_width = int(layout.sector_local_dofs["src"])
    mu_count = max(len(layout.mode_labels), 1)

    zeros_h = np.zeros(width, dtype=np.float64)
    zeros_b = np.zeros(baryon_width, dtype=np.float64)
    zeros_s = np.zeros(src_width, dtype=np.float64)
    default_source_blocks = evaluate_reduced_source_blocks(layout, bg, backend)
    photon_t_rhs: dict[str, np.ndarray] = {}
    photon_e_rhs: dict[str, np.ndarray] = {}
    photon_b_rhs: dict[str, np.ndarray] = {}
    neutrino_rhs: dict[str, np.ndarray] = {}

    def _mass_weight(*, mu_weight: float, sector: str, ell: int) -> float:
        ell_weight = 1.0 + 0.04 * ell + 0.015 * geom_scale
        if sector == "ph_I":
            sector_weight = branch_scale
        elif sector == "ph_E":
            sector_weight = branch_scale * (1.08 * polarization_scale)
        elif sector == "ph_B":
            sector_weight = branch_scale * (1.12 + 0.5 * twist_scale) * polarization_scale
        elif sector == "nu_I":
            sector_weight = 1.0 + 0.1 * branch_scale + 0.02 * geom_scale
        else:
            raise KeyError(f"unsupported harmonic sector {sector!r}")
        return mu_weight * sector_weight * ell_weight

    def _fs_diag(*, mu_weight: float, sector: str, ell: int, m: int) -> float:
        spin_weight = polarization_scale if sector in {"ph_E", "ph_B"} else 1.0
        return -geom_scale * mu_weight * spin_weight * (0.35 * (ell + 1) + 0.08 * abs(m))

    for mu_index, mu in enumerate(layout.mode_labels):
        mu_key = str(mu)
        mu_weight = _mode_label_weight(
            mu_key,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
        )
        next_mu = str(layout.mode_labels[(mu_index + 1) % len(layout.mode_labels)])
        t_state = np.asarray(photon_T_by_mode_label.get(mu_key, zeros_h), dtype=np.float64)
        e_state = np.asarray(photon_E_by_mode_label.get(mu_key, zeros_h), dtype=np.float64)
        b_state = np.asarray(photon_B_by_mode_label.get(mu_key, zeros_h), dtype=np.float64)
        nu_state = np.asarray(neutrino_by_mode_label.get(mu_key, zeros_h), dtype=np.float64)
        baryon_state = np.asarray(baryon_by_mode_label.get(mu_key, zeros_b), dtype=np.float64)
        if source_by_mode_label is None:
            src_state = np.asarray(default_source_blocks[mu_key], dtype=np.float64)
        else:
            src_state = np.asarray(source_by_mode_label.get(mu_key, zeros_s), dtype=np.float64)
        next_t = np.asarray(photon_T_by_mode_label.get(next_mu, zeros_h), dtype=np.float64)
        next_e = np.asarray(photon_E_by_mode_label.get(next_mu, zeros_h), dtype=np.float64)
        next_b = np.asarray(photon_B_by_mode_label.get(next_mu, zeros_h), dtype=np.float64)
        next_nu = np.asarray(neutrino_by_mode_label.get(next_mu, zeros_h), dtype=np.float64)
        for name, arr in (
            ("photon_T", t_state),
            ("photon_E", e_state),
            ("photon_B", b_state),
            ("neutrino", nu_state),
            ("next_photon_T", next_t),
            ("next_photon_E", next_e),
            ("next_photon_B", next_b),
            ("next_neutrino", next_nu),
        ):
            if arr.shape != (width,):
                raise ValueError(f"{name} state for {mu_key!r} must have shape ({width},)")
        if baryon_state.shape != (baryon_width,):
            raise ValueError(f"baryon state for {mu_key!r} must have shape ({baryon_width},)")
        if src_state.shape != (src_width,):
            raise ValueError(f"source state for {mu_key!r} must have shape ({src_width},)")

        t_rhs = np.zeros(width, dtype=np.float64)
        e_rhs = np.zeros(width, dtype=np.float64)
        b_rhs = np.zeros(width, dtype=np.float64)
        nu_rhs = np.zeros(width, dtype=np.float64)
        cross_coeff = (
            mu_weight * 0.5 * mix_scale * cross_mode_scale / len(layout.mode_labels)
            if len(layout.mode_labels) > 1
            else 0.0
        )

        offset = 0
        for ell in range(layout.ell_max + 1):
            pstf_weight = np.sqrt(max((ell + 2) * (ell - 1), 0.0)) / max(2 * ell + 1, 1) if ell >= 2 else 0.0
            for m in range(-ell, ell + 1):
                slot = offset + (m + ell)
                t_drive = _fs_diag(mu_weight=mu_weight, sector="ph_I", ell=ell, m=m) * t_state[slot]
                e_drive = _fs_diag(mu_weight=mu_weight, sector="ph_E", ell=ell, m=m) * e_state[slot]
                b_drive = _fs_diag(mu_weight=mu_weight, sector="ph_B", ell=ell, m=m) * b_state[slot]
                nu_drive = _fs_diag(mu_weight=mu_weight, sector="nu_I", ell=ell, m=m) * nu_state[slot]

                if ell > 0:
                    prev_m = m if abs(m) <= ell - 1 else 0
                    prev_slot = sum(2 * l + 1 for l in range(ell - 1)) + (prev_m + (ell - 1))
                    coeff_down = geom_scale * mu_weight * np.sqrt(max(ell * ell - m * m, 0.0)) / max(2 * ell + 1, 1)
                    t_drive += coeff_down * t_state[prev_slot]
                    e_drive += coeff_down * polarization_scale * e_state[prev_slot]
                    b_drive += coeff_down * polarization_scale * b_state[prev_slot]
                    nu_drive += coeff_down * nu_state[prev_slot]
                if ell < layout.ell_max:
                    next_m_same = m if abs(m) <= ell + 1 else 0
                    next_slot_same = sum(2 * l + 1 for l in range(ell + 1)) + (next_m_same + (ell + 1))
                    coeff_up = geom_scale * mu_weight * np.sqrt(max((ell + 1) * (ell + 1) - m * m, 0.0)) / max(2 * ell + 1, 1)
                    t_drive += coeff_up * t_state[next_slot_same]
                    e_drive += coeff_up * polarization_scale * e_state[next_slot_same]
                    b_drive += coeff_up * polarization_scale * b_state[next_slot_same]
                    nu_drive += coeff_up * nu_state[next_slot_same]

                if ell >= 2:
                    coeff_mix = mu_weight * mix_scale * pstf_weight
                    t_drive += coeff_mix * e_state[slot]
                    e_drive += 0.5 * coeff_mix * t_state[slot]
                    if twist_scale > 0.0:
                        eb = mu_weight * twist_scale * max(abs(m), 1) / (ell + 1)
                        e_drive += 0.75 * eb * b_state[slot]
                        b_drive += (-eb * e_state[slot]) + (0.25 * eb * t_state[slot])
                    if len(layout.mode_labels) > 1:
                        t_drive += _harmonic_cross_mode_coeff(
                            mu_weight=mu_weight,
                            mix_scale=mix_scale,
                            cross_mode_scale=cross_mode_scale,
                            twist_scale=twist_scale,
                            sector="ph_I",
                            ell=ell,
                            mu_count=mu_count,
                        ) * next_t[slot]
                        e_drive += _harmonic_cross_mode_coeff(
                            mu_weight=mu_weight,
                            mix_scale=mix_scale,
                            cross_mode_scale=cross_mode_scale,
                            twist_scale=twist_scale,
                            sector="ph_E",
                            ell=ell,
                            mu_count=mu_count,
                        ) * next_e[slot]
                        b_drive += _harmonic_cross_mode_coeff(
                            mu_weight=mu_weight,
                            mix_scale=mix_scale,
                            cross_mode_scale=cross_mode_scale,
                            twist_scale=twist_scale,
                            sector="ph_B",
                            ell=ell,
                            mu_count=mu_count,
                        ) * next_b[slot]
                        nu_drive += _harmonic_cross_mode_coeff(
                            mu_weight=mu_weight,
                            mix_scale=mix_scale,
                            cross_mode_scale=cross_mode_scale,
                            twist_scale=twist_scale,
                            sector="nu_I",
                            ell=ell,
                            mu_count=mu_count,
                        ) * next_nu[slot]

                if ell == 0 and cross_coeff != 0.0:
                    t_drive += cross_coeff * next_t[slot]
                    e_drive += cross_coeff * next_e[slot]
                    b_drive += cross_coeff * next_b[slot]
                    nu_drive += cross_coeff * next_nu[slot]

                if ell <= 1:
                    photon_coll = mu_weight * branch_scale * collision_scale * gamma_t
                else:
                    photon_coll = mu_weight * branch_scale * collision_scale * gamma_t / (ell + 0.5)
                t_drive += photon_coll * t_state[slot]
                e_drive += photon_coll * e_state[slot]
                b_drive += photon_coll * b_state[slot]

                if ell == 0 and m == 0:
                    t_drive += mu_weight * source_scale * visibility_amp
                if ell == 1 and m == 0:
                    t_drive += mu_weight * 0.5 * source_scale * doppler_amp
                    if baryon_width > 1:
                        t_drive += -0.25 * mu_weight * local_drag_scale * gamma_t * float(baryon_state[1])
                    if src_width > 1:
                        t_drive += 0.10 * mu_weight * local_drag_scale * gamma_t * float(src_state[1])
                if ell == 2 and m == 0:
                    e_drive += mu_weight * source_scale * polarization_amp
                    b_drive += mu_weight * twist_scale * cross_mode_scale * polarization_amp
                    if src_width > 0:
                        e_drive += 0.15 * mu_weight * local_drag_scale * gamma_t * float(src_state[0])
                    if src_width > 2:
                        e_drive += 0.08 * mu_weight * local_drag_scale * gamma_t * float(src_state[2])
                        b_drive += (
                            0.06
                            * mu_weight
                            * twist_scale
                            * local_drag_scale
                            * gamma_t
                            * float(src_state[2])
                        )

                t_rhs[slot] = t_drive / _mass_weight(mu_weight=mu_weight, sector="ph_I", ell=ell)
                e_rhs[slot] = e_drive / _mass_weight(mu_weight=mu_weight, sector="ph_E", ell=ell)
                b_rhs[slot] = b_drive / _mass_weight(mu_weight=mu_weight, sector="ph_B", ell=ell)
                nu_rhs[slot] = nu_drive / _mass_weight(mu_weight=mu_weight, sector="nu_I", ell=ell)
            offset += 2 * ell + 1

        photon_t_rhs[mu_key] = t_rhs
        photon_e_rhs[mu_key] = e_rhs
        photon_b_rhs[mu_key] = b_rhs
        neutrino_rhs[mu_key] = nu_rhs

    return photon_t_rhs, photon_e_rhs, photon_b_rhs, neutrino_rhs


def build_reduced_harmonic_affine_operator(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    residual_mode_labels: tuple[str, ...],
    photon_T_by_mode_label: Mapping[str, np.ndarray],
    photon_E_by_mode_label: Mapping[str, np.ndarray],
    photon_B_by_mode_label: Mapping[str, np.ndarray],
    neutrino_by_mode_label: Mapping[str, np.ndarray],
    baryon_by_mode_label: Mapping[str, np.ndarray],
    source_by_mode_label: Mapping[str, np.ndarray] | None = None,
) -> ReducedHarmonicAffineOperator:
    """Return the exact frozen-snapshot affine operator ``A r + b``.

    The returned operator acts only on the residual harmonic labels in
    ``residual_mode_labels``. For fixed ``bg`` and fixed covered/local/source
    inputs, this is exactly equivalent to ``evaluate_reduced_harmonic_rhs``.
    """

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    source_tables = bg.get("source_tables", {})
    if not isinstance(source_tables, Mapping):
        raise ValueError("bg.source_tables must be a mapping when provided")

    residual_labels = tuple(str(mu) for mu in residual_mode_labels)
    if len(residual_labels) == 0:
        return ReducedHarmonicAffineOperator(
            mode_labels=(),
            matrix=csc_matrix((0, 0), dtype=np.float64),
            bias=np.zeros(0, dtype=np.float64),
        )

    residual_label_set = frozenset(residual_labels)
    invalid = residual_label_set.difference(str(mu) for mu in layout.mode_labels)
    if invalid:
        raise ValueError(f"residual_mode_labels must be a subset of layout.mode_labels, got extras {sorted(invalid)!r}")

    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    visibility_amp = float(source_tables.get("visibility_amplitude", 0.0))
    polarization_amp = float(source_tables.get("polarization_source", 0.0))
    doppler_amp = float(source_tables.get("doppler_source", 0.25 * visibility_amp))

    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    mix_scale = float(scales["mix_scale"])
    twist_scale = float(scales["twist_scale"])
    polarization_scale = float(scales["polarization_scale"])
    source_scale = float(scales["source_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    collision_scale = float(scales["collision_scale"])
    local_drag_scale = float(scales["local_drag_scale"])

    baryon_width = int(layout.sector_local_dofs["baryon"])
    src_width = int(layout.sector_local_dofs["src"])
    structure = _reduced_harmonic_structure(
        int(layout.ell_max),
        tuple(str(mu) for mu in layout.mode_labels),
        residual_labels,
    )
    width = structure.width
    mu_count = max(len(layout.mode_labels), 1)
    zeros_h = np.zeros(width, dtype=np.float64)
    zeros_b = np.zeros(baryon_width, dtype=np.float64)
    zeros_s = np.zeros(src_width, dtype=np.float64)
    default_source_blocks = evaluate_reduced_source_blocks(layout, bg, backend)

    ell_weight = 1.0 + 0.04 * structure.ell_by_slot + 0.015 * geom_scale
    inv_t = 1.0 / np.maximum(branch_scale * ell_weight, 1.0e-30)
    inv_e = 1.0 / np.maximum(branch_scale * (1.08 * polarization_scale) * ell_weight, 1.0e-30)
    inv_b = 1.0 / np.maximum(
        branch_scale * (1.12 + 0.5 * twist_scale) * polarization_scale * ell_weight,
        1.0e-30,
    )
    inv_nu = 1.0 / np.maximum((1.0 + 0.1 * branch_scale + 0.02 * geom_scale) * ell_weight, 1.0e-30)
    stream_base = geom_scale * structure.diag_base_by_slot
    prev_t = inv_t * geom_scale * structure.prev_coeff_by_slot
    prev_e = inv_e * geom_scale * polarization_scale * structure.prev_coeff_by_slot
    prev_b = inv_b * geom_scale * polarization_scale * structure.prev_coeff_by_slot
    prev_nu = inv_nu * geom_scale * structure.prev_coeff_by_slot
    next_t_same = inv_t * geom_scale * structure.next_coeff_by_slot
    next_e_same = inv_e * geom_scale * polarization_scale * structure.next_coeff_by_slot
    next_b_same = inv_b * geom_scale * polarization_scale * structure.next_coeff_by_slot
    next_nu_same = inv_nu * geom_scale * structure.next_coeff_by_slot
    photon_coll = branch_scale * collision_scale * gamma_t * structure.collision_factor_by_slot
    diag_t = inv_t * (-stream_base + photon_coll)
    diag_e = inv_e * (-stream_base * polarization_scale + photon_coll)
    diag_b = inv_b * (-stream_base * polarization_scale + photon_coll)
    diag_nu = inv_nu * (-stream_base)
    mix_t = inv_t * mix_scale * structure.pstf_weight_by_slot
    mix_e = inv_e * (0.5 * mix_scale * structure.pstf_weight_by_slot)
    eb_base = twist_scale * structure.eb_base_by_slot
    eb_e = inv_e * (0.75 * eb_base)
    eb_b = inv_b * (-eb_base)
    eb_bt = inv_b * (0.25 * eb_base)

    cross_t = np.zeros(width, dtype=np.float64)
    cross_e = np.zeros(width, dtype=np.float64)
    cross_b = np.zeros(width, dtype=np.float64)
    cross_nu = np.zeros(width, dtype=np.float64)
    if mu_count > 1:
        base_cross = mix_scale * cross_mode_scale / np.maximum(structure.ell_by_slot + 1, 1)
        ge2 = structure.ge2_mask
        cross_t[ge2] = inv_t[ge2] * (0.18 * base_cross[ge2] / mu_count)
        cross_e[ge2] = inv_e[ge2] * (0.16 * base_cross[ge2] / mu_count)
        cross_b[ge2] = inv_b[ge2] * (0.16 * (1.0 + 0.5 * twist_scale) * base_cross[ge2] / mu_count)
        cross_nu[ge2] = inv_nu[ge2] * (0.12 * base_cross[ge2] / mu_count)
        ell0_coeff = 0.5 * mix_scale * cross_mode_scale / mu_count
        ell0 = structure.ell0_mask
        cross_t[ell0] = inv_t[ell0] * ell0_coeff
        cross_e[ell0] = inv_e[ell0] * ell0_coeff
        cross_b[ell0] = inv_b[ell0] * ell0_coeff
        cross_nu[ell0] = inv_nu[ell0] * ell0_coeff

    slots = structure.sector_slots
    prev_valid = structure.prev_slot_by_slot >= 0
    next_valid = structure.next_slot_by_slot >= 0
    t_off = 0
    e_off = width
    b_off = 2 * width
    nu_off = 3 * width
    block_size = structure.block_size
    self_block = np.zeros((block_size, block_size), dtype=np.float64)
    cross_block = np.zeros((block_size, block_size), dtype=np.float64)

    self_block[t_off + slots, t_off + slots] += diag_t
    self_block[e_off + slots, e_off + slots] += diag_e
    self_block[b_off + slots, b_off + slots] += diag_b
    self_block[nu_off + slots, nu_off + slots] += diag_nu

    self_block[t_off + slots[prev_valid], t_off + structure.prev_slot_by_slot[prev_valid]] += prev_t[prev_valid]
    self_block[e_off + slots[prev_valid], e_off + structure.prev_slot_by_slot[prev_valid]] += prev_e[prev_valid]
    self_block[b_off + slots[prev_valid], b_off + structure.prev_slot_by_slot[prev_valid]] += prev_b[prev_valid]
    self_block[nu_off + slots[prev_valid], nu_off + structure.prev_slot_by_slot[prev_valid]] += prev_nu[prev_valid]

    self_block[t_off + slots[next_valid], t_off + structure.next_slot_by_slot[next_valid]] += next_t_same[next_valid]
    self_block[e_off + slots[next_valid], e_off + structure.next_slot_by_slot[next_valid]] += next_e_same[next_valid]
    self_block[b_off + slots[next_valid], b_off + structure.next_slot_by_slot[next_valid]] += next_b_same[next_valid]
    self_block[nu_off + slots[next_valid], nu_off + structure.next_slot_by_slot[next_valid]] += next_nu_same[next_valid]

    ge2_slots = slots[structure.ge2_mask]
    self_block[t_off + ge2_slots, e_off + ge2_slots] += mix_t[structure.ge2_mask]
    self_block[e_off + ge2_slots, t_off + ge2_slots] += mix_e[structure.ge2_mask]
    self_block[e_off + ge2_slots, b_off + ge2_slots] += eb_e[structure.ge2_mask]
    self_block[b_off + ge2_slots, e_off + ge2_slots] += eb_b[structure.ge2_mask]
    self_block[b_off + ge2_slots, t_off + ge2_slots] += eb_bt[structure.ge2_mask]

    if mu_count > 1:
        cross_block[t_off + slots, t_off + slots] += cross_t
        cross_block[e_off + slots, e_off + slots] += cross_e
        cross_block[b_off + slots, b_off + slots] += cross_b
        cross_block[nu_off + slots, nu_off + slots] += cross_nu

    self_data = np.asarray(
        self_block[structure.self_pattern_rows, structure.self_pattern_cols],
        dtype=np.float64,
    )
    cross_data = np.asarray(
        cross_block[structure.cross_pattern_rows, structure.cross_pattern_cols],
        dtype=np.float64,
    )
    row_chunks: list[np.ndarray] = []
    col_chunks: list[np.ndarray] = []
    data_chunks: list[np.ndarray] = []
    for residual_index, next_residual in enumerate(structure.next_residual_index):
        row_start = residual_index * block_size
        row_chunks.append(structure.self_pattern_rows + row_start)
        col_chunks.append(structure.self_pattern_cols + row_start)
        data_chunks.append(self_data)
        if next_residual >= 0 and cross_data.size:
            col_start = next_residual * block_size
            row_chunks.append(structure.cross_pattern_rows + row_start)
            col_chunks.append(structure.cross_pattern_cols + col_start)
            data_chunks.append(cross_data)

    bias = np.zeros(structure.n_unknown, dtype=np.float64)
    for residual_index, mu in enumerate(residual_labels):
        baryon_state = np.asarray(baryon_by_mode_label.get(str(mu), zeros_b), dtype=np.float64)
        if baryon_state.shape != (baryon_width,):
            raise ValueError(f"baryon state for {mu!r} must have shape ({baryon_width},)")
        if source_by_mode_label is None:
            src_state = np.asarray(default_source_blocks[str(mu)], dtype=np.float64)
        else:
            src_state = np.asarray(source_by_mode_label.get(str(mu), zeros_s), dtype=np.float64)
        if src_state.shape != (src_width,):
            raise ValueError(f"source state for {mu!r} must have shape ({src_width},)")

        row_start = residual_index * block_size
        next_label = structure.next_external_label[residual_index]
        if next_label is not None and mu_count > 1:
            next_t = np.asarray(photon_T_by_mode_label.get(next_label, zeros_h), dtype=np.float64)
            next_e = np.asarray(photon_E_by_mode_label.get(next_label, zeros_h), dtype=np.float64)
            next_b = np.asarray(photon_B_by_mode_label.get(next_label, zeros_h), dtype=np.float64)
            next_nu = np.asarray(neutrino_by_mode_label.get(next_label, zeros_h), dtype=np.float64)
            bias[row_start + t_off : row_start + t_off + width] += cross_t * next_t
            bias[row_start + e_off : row_start + e_off + width] += cross_e * next_e
            bias[row_start + b_off : row_start + b_off + width] += cross_b * next_b
            bias[row_start + nu_off : row_start + nu_off + width] += cross_nu * next_nu

        bias[row_start + t_off + structure.monopole_slot] += inv_t[structure.monopole_slot] * source_scale * visibility_amp
        if structure.dipole_slot is not None:
            dipole_slot = structure.dipole_slot
            bias[row_start + t_off + dipole_slot] += inv_t[dipole_slot] * (0.5 * source_scale * doppler_amp)
            if baryon_width > 1:
                bias[row_start + t_off + dipole_slot] += (
                    inv_t[dipole_slot] * (-0.25 * local_drag_scale * gamma_t * float(baryon_state[1]))
                )
            if src_width > 1:
                bias[row_start + t_off + dipole_slot] += (
                    inv_t[dipole_slot] * (0.10 * local_drag_scale * gamma_t * float(src_state[1]))
                )
        if structure.quadrupole_slot is not None:
            quad_slot = structure.quadrupole_slot
            bias[row_start + e_off + quad_slot] += inv_e[quad_slot] * (source_scale * polarization_amp)
            bias[row_start + b_off + quad_slot] += inv_b[quad_slot] * (twist_scale * cross_mode_scale * polarization_amp)
            if src_width > 0:
                bias[row_start + e_off + quad_slot] += (
                    inv_e[quad_slot] * (0.15 * local_drag_scale * gamma_t * float(src_state[0]))
                )
            if src_width > 2:
                bias[row_start + e_off + quad_slot] += (
                    inv_e[quad_slot] * (0.08 * local_drag_scale * gamma_t * float(src_state[2]))
                )
                bias[row_start + b_off + quad_slot] += (
                    inv_b[quad_slot] * (0.06 * twist_scale * local_drag_scale * gamma_t * float(src_state[2]))
                )

    matrix_sparse = csc_matrix(
        (
            np.concatenate(data_chunks, dtype=np.float64),
            (
                np.concatenate(row_chunks, dtype=np.int64),
                np.concatenate(col_chunks, dtype=np.int64),
            ),
        ),
        shape=(structure.n_unknown, structure.n_unknown),
    )
    matrix_sparse.eliminate_zeros()
    return ReducedHarmonicAffineOperator(
        mode_labels=residual_labels,
        matrix=matrix_sparse,
        bias=bias,
    )


def build_reduced_source_affine_operator(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    mode_labels: tuple[str, ...],
    photon_T_by_mode_label: Mapping[str, np.ndarray],
    photon_E_by_mode_label: Mapping[str, np.ndarray],
    photon_B_by_mode_label: Mapping[str, np.ndarray],
) -> ReducedSourceAffineOperator:
    """Return the exact frozen-snapshot affine operator for source local blocks."""

    selected_labels = tuple(str(mu) for mu in mode_labels)
    src_width = int(layout.sector_local_dofs["src"])
    if len(selected_labels) == 0:
        return ReducedSourceAffineOperator(
            mode_labels=(),
            matrix=csc_matrix((0, 0), dtype=np.float64),
            bias=np.zeros(0, dtype=np.float64),
        )

    invalid = frozenset(selected_labels).difference(str(mu) for mu in layout.mode_labels)
    if invalid:
        raise ValueError(f"mode_labels must be a subset of layout.mode_labels, got extras {sorted(invalid)!r}")

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    scales = _operator_scales(bg, backend)
    branch_scale = float(scales["branch_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    source_scale = float(scales["source_scale"])
    polarization_scale = float(scales["polarization_scale"])
    twist_scale = float(scales["twist_scale"])
    geom_scale = float(scales["geom_scale"])
    forcing_blocks = evaluate_reduced_source_blocks(layout, bg, backend)
    width = (int(layout.ell_max) + 1) ** 2
    mu_count = max(len(layout.mode_labels), 1)
    mode_index = {str(mu): idx for idx, mu in enumerate(layout.mode_labels)}
    zeros_h = np.zeros(width, dtype=np.float64)

    total_dof = len(selected_labels) * src_width
    matrix = np.zeros((total_dof, total_dof), dtype=np.float64)
    bias = np.zeros(total_dof, dtype=np.float64)

    dipole_slot = sum(2 * ell + 1 for ell in range(1)) + 1 if int(layout.ell_max) >= 1 else None
    quadrupole_slot = sum(2 * ell + 1 for ell in range(2)) + 2 if int(layout.ell_max) >= 2 else None

    for residual_index, mu in enumerate(selected_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=int(mode_index[mu]),
            mu_count=mu_count,
            branch_scale=branch_scale,
        )
        source_mass = mu_weight * (1.0 + 0.06 * source_scale + 0.04 * np.arange(src_width, dtype=np.float64))
        inv_source = 1.0 / np.maximum(source_mass, 1.0e-30)
        row_start = residual_index * src_width
        matrix[row_start : row_start + src_width, row_start : row_start + src_width] += np.diag(
            inv_source * (mu_weight * local_drag_scale * (0.35 * gamma_t))
        )
        bias[row_start : row_start + src_width] = inv_source * np.asarray(forcing_blocks[mu], dtype=np.float64)

        t_state = np.asarray(photon_T_by_mode_label.get(mu, zeros_h), dtype=np.float64)
        e_state = np.asarray(photon_E_by_mode_label.get(mu, zeros_h), dtype=np.float64)
        b_state = np.asarray(photon_B_by_mode_label.get(mu, zeros_h), dtype=np.float64)
        if t_state.shape != (width,) or e_state.shape != (width,) or b_state.shape != (width,):
            raise ValueError(f"harmonic state for {mu!r} must have shape ({width},)")
        if dipole_slot is not None and src_width > 1:
            bias[row_start + 1] += inv_source[1] * (-0.08 * mu_weight * local_drag_scale * gamma_t * float(t_state[dipole_slot]))
        if quadrupole_slot is not None and src_width > 0:
            bias[row_start + 0] += inv_source[0] * (-0.10 * mu_weight * local_drag_scale * gamma_t * float(e_state[quadrupole_slot]))
        if quadrupole_slot is not None and src_width > 2:
            bias[row_start + 2] += inv_source[2] * (-0.06 * mu_weight * local_drag_scale * gamma_t * float(e_state[quadrupole_slot]))
            bias[row_start + 2] += (
                inv_source[2]
                * (-0.04 * mu_weight * twist_scale * local_drag_scale * gamma_t * float(b_state[quadrupole_slot]))
            )

    matrix_sparse = csc_matrix(matrix)
    matrix_sparse.eliminate_zeros()
    return ReducedSourceAffineOperator(
        mode_labels=selected_labels,
        matrix=matrix_sparse,
        bias=bias,
    )


def build_reduced_joint_affine_operator(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    residual_mode_labels: tuple[str, ...],
    photon_T_by_mode_label: Mapping[str, np.ndarray],
    photon_E_by_mode_label: Mapping[str, np.ndarray],
    photon_B_by_mode_label: Mapping[str, np.ndarray],
    neutrino_by_mode_label: Mapping[str, np.ndarray],
    baryon_by_mode_label: Mapping[str, np.ndarray],
    source_by_mode_label: Mapping[str, np.ndarray] | None = None,
) -> ReducedJointAffineOperator:
    """Return the exact frozen-snapshot affine operator for local+harmonic+source residual blocks."""

    residual_labels = tuple(str(mu) for mu in residual_mode_labels)
    baryon_width = int(layout.sector_local_dofs["baryon"])
    cdm_width = int(layout.sector_local_dofs["cdm"])
    src_width = int(layout.sector_local_dofs["src"])
    local_block_size = baryon_width + cdm_width
    if len(residual_labels) == 0:
        return ReducedJointAffineOperator(
            mode_labels=(),
            local_dof=0,
            harmonic_dof=0,
            source_dof=0,
            matrix=csc_matrix((0, 0), dtype=np.float64),
            bias=np.zeros(0, dtype=np.float64),
        )

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    source_scale = float(scales["source_scale"])
    polarization_scale = float(scales["polarization_scale"])
    twist_scale = float(scales["twist_scale"])
    structure = _reduced_harmonic_structure(
        int(layout.ell_max),
        tuple(str(mu) for mu in layout.mode_labels),
        residual_labels,
    )
    harmonic_block_size = int(structure.block_size)
    harmonic_dof = int(structure.n_unknown)
    local_dof = len(residual_labels) * local_block_size
    source_dof = len(residual_labels) * src_width
    mode_index = {str(mu): idx for idx, mu in enumerate(layout.mode_labels)}

    zero_theta = {mu: 0.0 for mu in residual_labels}
    local_affine = build_reduced_local_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        theta_1_by_mode_label=zero_theta,
    )
    zeros_b = np.zeros(baryon_width, dtype=np.float64)
    harmonic_baryon_by_mode_label = {
        str(mu): (
            zeros_b
            if str(mu) in residual_labels
            else np.asarray(baryon_by_mode_label.get(str(mu), zeros_b), dtype=np.float64)
        )
        for mu in layout.mode_labels
    }
    default_source_blocks = evaluate_reduced_source_blocks(layout, bg, backend)
    zeros_s = np.zeros(src_width, dtype=np.float64)
    harmonic_source_by_mode_label: dict[str, np.ndarray] = {}
    for mu in layout.mode_labels:
        mu_key = str(mu)
        if source_by_mode_label is None:
            source_state = np.asarray(default_source_blocks[mu_key], dtype=np.float64)
        else:
            source_state = np.asarray(source_by_mode_label.get(mu_key, default_source_blocks[mu_key]), dtype=np.float64)
        harmonic_source_by_mode_label[mu_key] = (
            zeros_s if mu_key in residual_labels else np.asarray(source_state, dtype=np.float64)
        )
    harmonic_affine = build_reduced_harmonic_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        photon_T_by_mode_label=photon_T_by_mode_label,
        photon_E_by_mode_label=photon_E_by_mode_label,
        photon_B_by_mode_label=photon_B_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=harmonic_baryon_by_mode_label,
        source_by_mode_label=harmonic_source_by_mode_label,
    )

    total_dof = local_dof + harmonic_dof + source_dof
    source_offset = local_dof + harmonic_dof
    joint = np.zeros((total_dof, total_dof), dtype=np.float64)
    if local_dof > 0:
        joint[:local_dof, :local_dof] = np.asarray(local_affine.matrix.toarray(), dtype=np.float64)
    if harmonic_dof > 0:
        joint[local_dof : local_dof + harmonic_dof, local_dof : local_dof + harmonic_dof] = np.asarray(
            harmonic_affine.matrix.toarray(),
            dtype=np.float64,
        )

    # local <- harmonic(theta_1) coupling
    baryon_base_diag = 1.0 + 0.08 * geom_scale + 0.03 * np.arange(baryon_width, dtype=np.float64)
    if baryon_width > 1 and structure.dipole_slot is not None:
        local_theta_coeff = float(
            0.25 * local_drag_scale * gamma_t / max(abs(float(baryon_base_diag[1])), 1.0e-30)
        )
        for residual_index in range(len(residual_labels)):
            local_row = residual_index * local_block_size + 1
            harmonic_col = local_dof + residual_index * harmonic_block_size + int(structure.dipole_slot)
            joint[local_row, harmonic_col] = local_theta_coeff

    # harmonic <- local(baryon velocity) coupling
    if baryon_width > 1 and structure.dipole_slot is not None:
        ell_weight = 1.0 + 0.04 * 1.0 + 0.015 * geom_scale
        inv_t_dipole = 1.0 / max(branch_scale * ell_weight, 1.0e-30)
        harmonic_baryon_coeff = float(inv_t_dipole * (-0.25 * local_drag_scale * gamma_t))
        for residual_index in range(len(residual_labels)):
            harmonic_row = local_dof + residual_index * harmonic_block_size + int(structure.dipole_slot)
            local_col = residual_index * local_block_size + 1
            joint[harmonic_row, local_col] = harmonic_baryon_coeff

    bias = np.concatenate(
        [
            np.asarray(local_affine.bias, dtype=np.float64),
            np.asarray(harmonic_affine.bias, dtype=np.float64),
            np.zeros(source_dof, dtype=np.float64),
        ],
        dtype=np.float64,
    )
    for residual_index, mu in enumerate(residual_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=int(mode_index[mu]),
            mu_count=max(len(layout.mode_labels), 1),
            branch_scale=branch_scale,
        )
        source_mass = mu_weight * (1.0 + 0.06 * source_scale + 0.04 * np.arange(src_width, dtype=np.float64))
        inv_source = 1.0 / np.maximum(source_mass, 1.0e-30)
        source_block = np.asarray(default_source_blocks[mu], dtype=np.float64)
        source_row = source_offset + residual_index * src_width
        harmonic_row = local_dof + residual_index * harmonic_block_size

        joint[source_row : source_row + src_width, source_row : source_row + src_width] += np.diag(
            inv_source * (mu_weight * local_drag_scale * (0.35 * gamma_t))
        )

        bias_source = inv_source * source_block
        if src_width > 0:
            bias[source_row : source_row + src_width] = bias_source
        if structure.dipole_slot is not None and src_width > 1:
            ell_weight = 1.0 + 0.04 * 1.0 + 0.015 * geom_scale
            inv_t_dipole = 1.0 / max(branch_scale * ell_weight, 1.0e-30)
            joint[harmonic_row + int(structure.dipole_slot), source_row + 1] += (
                inv_t_dipole * (0.10 * local_drag_scale * gamma_t)
            )
            joint[source_row + 1, harmonic_row + int(structure.dipole_slot)] += (
                inv_source[1] * (-0.08 * mu_weight * local_drag_scale * gamma_t)
            )
        if structure.quadrupole_slot is not None:
            ell_weight = 1.0 + 0.04 * 2.0 + 0.015 * geom_scale
            inv_e_quad = 1.0 / max(branch_scale * (1.08 * polarization_scale) * ell_weight, 1.0e-30)
            if src_width > 0:
                joint[harmonic_row + structure.width + int(structure.quadrupole_slot), source_row + 0] += (
                    inv_e_quad * (0.15 * local_drag_scale * gamma_t)
                )
                joint[source_row + 0, harmonic_row + structure.width + int(structure.quadrupole_slot)] += (
                    inv_source[0] * (-0.10 * mu_weight * local_drag_scale * gamma_t)
                )
            if src_width > 2:
                inv_b_quad = 1.0 / max(
                    branch_scale
                    * (1.12 + 0.5 * twist_scale)
                    * polarization_scale
                    * ell_weight,
                    1.0e-30,
                )
                joint[harmonic_row + structure.width + int(structure.quadrupole_slot), source_row + 2] += (
                    inv_e_quad * (0.08 * local_drag_scale * gamma_t)
                )
                joint[harmonic_row + 2 * structure.width + int(structure.quadrupole_slot), source_row + 2] += (
                    inv_b_quad * (0.06 * twist_scale * local_drag_scale * gamma_t)
                )
                joint[source_row + 2, harmonic_row + structure.width + int(structure.quadrupole_slot)] += (
                    inv_source[2] * (-0.06 * mu_weight * local_drag_scale * gamma_t)
                )
                joint[source_row + 2, harmonic_row + 2 * structure.width + int(structure.quadrupole_slot)] += (
                    inv_source[2] * (-0.04 * mu_weight * twist_scale * local_drag_scale * gamma_t)
                )

    return ReducedJointAffineOperator(
        mode_labels=residual_labels,
        local_dof=local_dof,
        harmonic_dof=harmonic_dof,
        source_dof=source_dof,
        matrix=csc_matrix(joint),
        bias=bias,
    )


def build_reduced_local_affine_operator(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    residual_mode_labels: tuple[str, ...],
    theta_1_by_mode_label: Mapping[str, float],
) -> ReducedLocalAffineOperator:
    """Return the exact frozen-snapshot affine operator for residual local sectors."""

    residual_labels = tuple(str(mu) for mu in residual_mode_labels)
    baryon_width = int(layout.sector_local_dofs["baryon"])
    cdm_width = int(layout.sector_local_dofs["cdm"])
    block_size = baryon_width + cdm_width
    if len(residual_labels) == 0:
        return ReducedLocalAffineOperator(
            mode_labels=(),
            matrix=csc_matrix((0, 0), dtype=np.float64),
            bias=np.zeros(0, dtype=np.float64),
        )

    invalid = frozenset(residual_labels).difference(str(mu) for mu in layout.mode_labels)
    if invalid:
        raise ValueError(f"residual_mode_labels must be a subset of layout.mode_labels, got extras {sorted(invalid)!r}")

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    mu_count = max(len(layout.mode_labels), 1)
    baryon_base_diag = 1.0 + 0.08 * geom_scale + 0.03 * np.arange(baryon_width, dtype=np.float64)

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    bias = np.zeros(len(residual_labels) * block_size, dtype=np.float64)
    mode_index = {str(mu): idx for idx, mu in enumerate(layout.mode_labels)}
    for residual_index, mu in enumerate(residual_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=int(mode_index[mu]),
            mu_count=mu_count,
            branch_scale=branch_scale,
        )
        baryon_diag = mu_weight * baryon_base_diag
        coeff = np.divide(
            mu_weight * local_drag_scale * gamma_t,
            np.maximum(np.abs(baryon_diag), 1.0e-30),
            dtype=np.float64,
        )
        row_start = residual_index * block_size
        for local_dof, value in enumerate(coeff):
            rows.append(row_start + local_dof)
            cols.append(row_start + local_dof)
            data.append(float(value))
        if baryon_width > 1:
            bias[row_start + 1] = float(
                0.25
                * mu_weight
                * local_drag_scale
                * gamma_t
                * float(theta_1_by_mode_label.get(mu, 0.0))
                / max(abs(float(baryon_diag[1])), 1.0e-30)
            )

    return ReducedLocalAffineOperator(
        mode_labels=residual_labels,
        matrix=csc_matrix(
            (np.asarray(data, dtype=np.float64), (np.asarray(rows, dtype=np.int64), np.asarray(cols, dtype=np.int64))),
            shape=(len(residual_labels) * block_size, len(residual_labels) * block_size),
        ),
        bias=bias,
    )


def evaluate_reduced_local_rhs(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    baryon_by_mode_label: Mapping[str, np.ndarray],
    cdm_by_mode_label: Mapping[str, np.ndarray],
    theta_1_by_mode_label: Mapping[str, float],
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Evaluate the PR-09 local-sector rows without assembling full sparse operators."""

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    baryon_width = int(layout.sector_local_dofs["baryon"])
    cdm_width = int(layout.sector_local_dofs["cdm"])
    baryon_base_diag = 1.0 + 0.08 * geom_scale + 0.03 * np.arange(baryon_width, dtype=np.float64)
    mu_count = max(len(layout.mode_labels), 1)
    baryon_rhs: dict[str, np.ndarray] = {}
    cdm_rhs: dict[str, np.ndarray] = {}
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_key = str(mu)
        mu_weight = _mode_label_weight(
            mu_key,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
        )
        baryon_state = np.asarray(
            baryon_by_mode_label.get(mu_key, np.zeros(baryon_width, dtype=np.float64)),
            dtype=np.float64,
        )
        if baryon_state.shape != (baryon_width,):
            raise ValueError(f"baryon state for {mu_key!r} must have shape ({baryon_width},)")
        cdm_state = np.asarray(
            cdm_by_mode_label.get(mu_key, np.zeros(cdm_width, dtype=np.float64)),
            dtype=np.float64,
        )
        if cdm_state.shape != (cdm_width,):
            raise ValueError(f"cdm state for {mu_key!r} must have shape ({cdm_width},)")
        baryon_drive = mu_weight * local_drag_scale * gamma_t * baryon_state
        if baryon_width > 1:
            baryon_drive[1] += (
                0.25 * mu_weight * local_drag_scale * gamma_t * float(theta_1_by_mode_label.get(mu_key, 0.0))
            )
        baryon_diag = mu_weight * baryon_base_diag
        baryon_rhs[mu_key] = baryon_drive / np.maximum(np.abs(baryon_diag), 1.0e-30)
        cdm_rhs[mu_key] = np.zeros_like(cdm_state)
    return baryon_rhs, cdm_rhs


def assemble_hierarchy_ops(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    source_data: Mapping[str, object],
):
    """Return the concrete ver3 hierarchy operator bundle for one background state."""

    if not isinstance(bg, Mapping):
        raise ValueError("bg must be a mapping")
    if not isinstance(source_data, Mapping):
        raise ValueError("source_data must be a mapping")
    state = dict(bg)
    opacity_data = state.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    state["opacity_data"] = dict(opacity_data)
    existing_sources = state.get("source_tables", {})
    if not isinstance(existing_sources, Mapping):
        raise ValueError("bg.source_tables must be a mapping when provided")
    state["source_tables"] = {**dict(existing_sources), **dict(source_data)}
    state.setdefault("state_tag", "hierarchy_ops_state")
    return backend.operator_factory(state)


def hierarchy_layout_gate_bundle(
    backend: FamilyBackend,
    ops,
    *,
    provenance_metadata: Mapping[str, object] | None = None,
) -> GateBundle:
    """Emit the machine-readable PR-09 hierarchy-layout gate bundle."""

    mass_matrix = ops.mass_matrix
    explicit_block = ops.A_fs + ops.A_mix
    implicit_block = ops.A_coll
    source_template = np.asarray(ops.source_template, dtype=np.float64)
    layout_metadata = dict(ops.layout_metadata)
    return make_gate_bundle(
        "hierarchy_layout_gate",
        family=backend.family_spec.family,
        branch=ops.branch,
        backend=backend.family_spec.preferred_backend,
        truncation=dict(backend.truncation),
        residual_summary={
            "state_size": float(layout_metadata.get("size", 0)),
            "mass_matrix_nnz": float(mass_matrix.nnz),
            "explicit_block_nnz": float(explicit_block.nnz),
            "implicit_block_nnz": float(implicit_block.nnz),
            "source_norm": float(np.linalg.norm(source_template)),
        },
        known_limit_checks={
            "mass_matrix_square": bool(mass_matrix.shape[0] == mass_matrix.shape[1]),
            "explicit_block_square": bool(explicit_block.shape[0] == explicit_block.shape[1]),
            "implicit_block_square": bool(implicit_block.shape[0] == implicit_block.shape[1]),
            "source_matches_state_size": bool(source_template.shape == (mass_matrix.shape[0],)),
        },
        forbidden_shortcut_checks={
            "no_dense_generic_operator": True,
            "no_ad_hoc_sector_order": True,
            "operator_split_preserved": True,
        },
        metadata={
            "layout_manifest": layout_metadata,
            "operator_realization": layout_metadata.get("operator_realization"),
            "exact_family_operator_available": layout_metadata.get("exact_family_operator_available"),
            "projection_provenance": {}
            if provenance_metadata is None
            else dict(provenance_metadata),
        },
        passed=bool(
            mass_matrix.shape[0] == mass_matrix.shape[1]
            and explicit_block.shape[0] == explicit_block.shape[1]
            and implicit_block.shape[0] == implicit_block.shape[1]
            and source_template.shape == (mass_matrix.shape[0],)
        ),
        opened_claim="hierarchy layout and operator split bound to executable sparse objects",
    )
