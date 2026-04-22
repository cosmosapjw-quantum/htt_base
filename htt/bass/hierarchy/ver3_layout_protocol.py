"""ver3 PR-09 hierarchy layout and IMEX packing contract."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from scipy.sparse import csr_matrix, eye

from bass.los.family_backend_protocol import FamilyBackend

__all__ = [
    "SECTOR_ORDER",
    "HierarchyLayout",
    "build_hierarchy_layout",
    "build_layout_manifest",
    "flatten",
    "unflatten",
    "assemble_free_streaming_block",
    "assemble_mixing_block",
    "assemble_mass_matrix",
    "assemble_explicit_block",
    "assemble_implicit_block",
    "assemble_source_vector",
    "assemble_hierarchy_ops",
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


def _branch_scale(bg: Mapping[str, object]) -> float:
    return 1.15 if str(bg.get("branch", "orthogonal")) == "tilted" else 1.0


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
        "V": ("mu_open",),
        "VII_0": ("mu_hel",),
        "VII_h": ("mu_hel_h",),
        "IX": ("mu_compact",),
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
    return eye(layout.size, format="csr", dtype=np.float64)


def assemble_free_streaming_block(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> csr_matrix:
    layout = build_hierarchy_layout(backend, truncation)
    branch_scale = _branch_scale(bg)
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for mu in layout.mode_labels:
        for sector in layout.sector_order:
            if sector not in _HARMONIC_SECTORS:
                continue
            for ell in range(layout.ell_max + 1):
                for m in range(-ell, ell + 1):
                    idx = flatten(layout, mu, sector, ell, m)
                    rows.append(idx)
                    cols.append(idx)
                    data.append(-0.1 * branch_scale * (ell + 1))
                    if ell < layout.ell_max:
                        nxt = flatten(layout, mu, sector, ell + 1, m if abs(m) <= ell + 1 else 0)
                        rows.append(idx)
                        cols.append(nxt)
                        data.append(0.05 * branch_scale)
    return csr_matrix((data, (rows, cols)), shape=(layout.size, layout.size))


def assemble_mixing_block(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> csr_matrix:
    layout = build_hierarchy_layout(backend, truncation)
    mix_scale = 0.03 if backend.family_spec.class_label == "B" else 0.02
    branch_scale = _branch_scale(bg)
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for mu_index, mu in enumerate(layout.mode_labels):
        for ell in range(2, layout.ell_max + 1):
            for m in range(-ell, ell + 1):
                i_idx = flatten(layout, mu, "ph_I", ell, m)
                e_idx = flatten(layout, mu, "ph_E", ell, m)
                rows.extend((i_idx, e_idx))
                cols.extend((e_idx, i_idx))
                data.extend((mix_scale * branch_scale, 0.5 * mix_scale * branch_scale))
        if len(layout.mode_labels) > 1:
            next_mu = layout.mode_labels[(mu_index + 1) % len(layout.mode_labels)]
            src_idx = flatten(layout, mu, "ph_I", 0, 0)
            dst_idx = flatten(layout, next_mu, "ph_I", 0, 0)
            rows.append(src_idx)
            cols.append(dst_idx)
            data.append(0.25 * mix_scale * branch_scale)
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
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for mu in layout.mode_labels:
        for sector in ("ph_I", "ph_E", "ph_B"):
            for ell in range(layout.ell_max + 1):
                for m in range(-ell, ell + 1):
                    idx = flatten(layout, mu, sector, ell, m)
                    rows.append(idx)
                    cols.append(idx)
                    data.append(gamma_t)
        for sector in ("baryon", "src"):
            for local_dof in range(layout.sector_local_dofs[sector]):
                idx = flatten(layout, mu, sector, None, None, local_dof)
                rows.append(idx)
                cols.append(idx)
                data.append(gamma_t if sector == "baryon" else 0.5 * gamma_t)
    return csr_matrix((data, (rows, cols)), shape=(layout.size, layout.size))


def assemble_source_vector(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    source_tables: Mapping[str, object],
) -> np.ndarray:
    layout = build_hierarchy_layout(backend, truncation)
    out = np.zeros(layout.size, dtype=np.float64)
    visibility_amp = float(source_tables.get("visibility_amplitude", 0.0))
    polarization_amp = float(source_tables.get("polarization_source", 0.0))
    reion_amp = float(source_tables.get("reionization_amplitude", 0.0))
    for mu in layout.mode_labels:
        out[flatten(layout, mu, "ph_I", 0, 0)] = visibility_amp
        if layout.ell_max >= 2:
            out[flatten(layout, mu, "ph_E", 2, 0)] = polarization_amp
        out[flatten(layout, mu, "src", None, None, 0)] = reion_amp
    return out


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
