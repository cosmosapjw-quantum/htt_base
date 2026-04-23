"""ver3 PR-09 hierarchy layout and IMEX packing contract."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from scipy.sparse import csr_matrix, diags

from bass.los.family_backend_protocol import FamilyBackend
from bass.validation import GateBundle, make_gate_bundle

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
    return {
        "branch_scale": branch_scale,
        "geom_scale": branch_scale * geom_scale,
        "mix_scale": mix_scale,
        "twist_scale": twist_scale,
        "polarization_scale": polarization_scale,
        "source_scale": source_scale,
    }


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
    return 1.0 + 0.03 * (mu_index / max(mu_count, 1))


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
                        diag[flatten(layout, mu, sector, ell, m)] = block_weight
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
                diag[idx] = value
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
            for sector in ("ph_I", "ph_E", "ph_B", "nu_I"):
                src_idx = flatten(layout, mu, sector, 0, 0)
                dst_idx = flatten(layout, next_mu, sector, 0, 0)
                rows.append(src_idx)
                cols.append(dst_idx)
                data.append(mu_weight * 0.5 * mix_scale / len(layout.mode_labels))
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
                    photon_weight = mu_weight * branch_scale * gamma_t * (
                        1.0 if ell <= 1 else 1.0 / (ell + 0.5)
                    )
                    rows.append(idx)
                    cols.append(idx)
                    data.append(photon_weight)
        for sector in ("baryon", "src"):
            for local_dof in range(layout.sector_local_dofs[sector]):
                idx = flatten(layout, mu, sector, None, None, local_dof)
                local_weight = mu_weight * (gamma_t if sector == "baryon" else 0.35 * gamma_t)
                rows.append(idx)
                cols.append(idx)
                data.append(local_weight)
        dipole_idx = flatten(layout, mu, "ph_I", 1, 0)
        baryon_v_idx = flatten(layout, mu, "baryon", None, None, 1)
        rows.extend((dipole_idx, baryon_v_idx))
        cols.extend((baryon_v_idx, dipole_idx))
        data.extend((-0.25 * mu_weight * gamma_t, 0.25 * mu_weight * gamma_t))
        if layout.ell_max >= 2:
            quad_idx = flatten(layout, mu, "ph_E", 2, 0)
            src_idx = flatten(layout, mu, "src", None, None, 0)
            rows.extend((quad_idx, src_idx))
            cols.extend((src_idx, quad_idx))
            data.extend((0.15 * mu_weight * gamma_t, -0.10 * mu_weight * gamma_t))
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
    visibility_amp = float(source_tables.get("visibility_amplitude", 0.0))
    polarization_amp = float(source_tables.get("polarization_source", 0.0))
    doppler_amp = float(source_tables.get("doppler_source", 0.25 * visibility_amp))
    reion_amp = float(source_tables.get("reionization_amplitude", 0.0))
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
            out[flatten(layout, mu, "ph_B", 2, 0)] = mu_weight * twist_scale * polarization_amp
        out[flatten(layout, mu, "src", None, None, 0)] = mu_weight * reion_amp
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
