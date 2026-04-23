"""Aggregate per-family ResidualPack runner (S6).

Given a single (eta_grid, k_grid, visibility_fn, source_builder)
observer surface, generate a transport bundle for each registered
family, extract its ``residual_pack_from_bundle``, and emit a
``family_residual_packs: dict[str, ResidualPack]`` mapping ready to drop
into ``ver3_output_archive`` and ``ver3_gate_stop.hard_gate_before_fitting``.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping

import numpy as np

from bass.background.bianchi_types import (
    flrw_constants,
    type_i_constants,
    type_ii_constants,
    type_iii_constants,
    type_iv_constants,
    type_ix_constants,
    type_v_constants,
    type_vi0_constants,
    type_vih_constants,
    type_vii0_constants,
    type_viih_constants,
    type_viii_constants,
)
from bass.los.families import KNOWN_FAMILIES
from bass.statistics import ResidualPack, merge_residual_packs
from bass.transport.exact_transport import ExactTransportBundle


__all__ = (
    "FAMILY_STRUCTURE_FACTORIES",
    "build_family_residual_packs",
    "merge_family_residual_packs",
    "default_family_residual_report",
)


#: Maps family label → zero-argument factory returning a nominal
#: StructureConstants for that family. Used as the default invocation
#: surface when the runner is asked to generate a report for every
#: registered family.
#:
#: The structure parameters are chosen small (``n, a ≲ 1e-5``) so the
#: anchor-limit residuals for families that admit an FLRW limit
#: (I, V, VII_0, VII_h, IX) sit inside their tolerance bands. Types
#: without an FLRW limit (II, III, IV, VI_0, VI_h, VIII) are free to
#: use any finite value; the structural residuals (translator /
#: seed / branch / chart_order) are insensitive to the magnitude.
FAMILY_STRUCTURE_FACTORIES: dict[str, Callable[[], object]] = {
    "I": type_i_constants,
    "II": lambda: type_ii_constants(n1=1.0e-6),
    "III": lambda: type_iii_constants(n1=1.0e-6),
    "IV": lambda: type_iv_constants(n3=1.0e-6, a_twist=1.0e-6),
    "V": lambda: type_v_constants(a_twist=1.0e-6),
    "VI_0": lambda: type_vi0_constants(n1=1.0e-6, n3=-1.0e-6),
    "VI_h": lambda: type_vih_constants(n1=1.0e-6, n3=-2.0e-7, a_twist=1.0e-6),
    "VII_0": lambda: type_vii0_constants(n1=1.0e-6, n3=1.0e-6),
    "VII_h": lambda: type_viih_constants(n1=1.0e-6, n3=1.0e-6, a_twist=1.0e-7),
    "VIII": lambda: type_viii_constants(n1=-1.0e-6, n2=1.0e-6, n3=1.0e-6),
    "IX": lambda: type_ix_constants(n=1.0e-6),
}


def build_family_residual_packs(
    *,
    eta_grid_mpc: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell_max: int,
    visibility_fn: Callable[[float], float],
    source_builder: Callable[[float, float], Mapping[str, object]],
    families: tuple[str, ...] | None = None,
    structure_factories: Mapping[str, Callable[[], object]] | None = None,
) -> dict[str, ResidualPack]:
    """Produce one ``ResidualPack`` per requested family.

    Parameters
    ----------
    families : tuple[str, ...] | None
        Subset of family labels to include. Defaults to every family in
        ``KNOWN_FAMILIES`` (i.e. all 11 Bianchi families — FLRW is not
        emitted because the facade handles it directly).
    structure_factories : Mapping | None
        Override for the nominal structure factories. Unspecified
        families fall back to ``FAMILY_STRUCTURE_FACTORIES``.

    Returns
    -------
    dict[str, ResidualPack]
        Keyed by family label; every kernel's
        ``residual_pack_from_bundle(bundle)`` output.
    """
    selected = tuple(families) if families is not None else tuple(KNOWN_FAMILIES)
    factories = dict(FAMILY_STRUCTURE_FACTORIES)
    if structure_factories:
        factories.update(dict(structure_factories))

    packs: dict[str, ResidualPack] = {}
    for family in selected:
        if family not in KNOWN_FAMILIES:
            raise KeyError(f"Unknown Bianchi family '{family}'")
        if family not in factories:
            raise KeyError(f"No structure factory registered for family '{family}'")
        structure = factories[family]()
        kernel = KNOWN_FAMILIES[family]
        bundle: ExactTransportBundle = kernel.build_transport_bundle(
            structure=structure,
            eta_grid_mpc=eta_grid_mpc,
            k_grid_mpc=k_grid_mpc,
            ell_max=ell_max,
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
        pack = kernel.residual_pack_from_bundle(bundle)
        packs[family] = pack
    return packs


def merge_family_residual_packs(
    packs: Mapping[str, ResidualPack],
) -> ResidualPack:
    """Collapse per-family packs into a single merged pack (label-namespaced)."""
    if not packs:
        raise ValueError("merge_family_residual_packs needs at least one pack")
    return merge_residual_packs(packs.values())


def default_family_residual_report(
    *,
    eta_grid_mpc: np.ndarray | None = None,
    k_grid_mpc: np.ndarray | None = None,
    ell_max: int = 6,
) -> dict[str, ResidualPack]:
    """Convenience: use a canonical observer surface and emit every pack.

    The canonical surface:
    * eta ∈ [40, 420] Mpc (65 samples) — matches the Wave A/B test grids
    * k ∈ {0.05, 0.08, 0.12} Mpc⁻¹
    * ell_max = 6
    * Gaussian visibility peaked at η = 220 Mpc
    * Gaussian source profile peaked at η = 210 Mpc
    """
    if eta_grid_mpc is None:
        eta_grid_mpc = np.linspace(40.0, 420.0, 65)
    if k_grid_mpc is None:
        k_grid_mpc = np.array([0.05, 0.08, 0.12], dtype=float)

    def _vis(eta: float) -> float:
        return float(np.exp(-0.5 * ((eta - 220.0) / 35.0) ** 2))

    def _src(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * ((eta - 210.0) / 40.0) ** 2))
        return {
            "temperature": env * (1.0 + 0.1 * k),
            "temperature_anisotropy": 0.2 * env,
            "polarization": 0.35 * env,
            "b_mode": 0.0,
        }

    return build_family_residual_packs(
        eta_grid_mpc=eta_grid_mpc,
        k_grid_mpc=k_grid_mpc,
        ell_max=ell_max,
        visibility_fn=_vis,
        source_builder=_src,
    )


# Silence the flrw_constants reference (imported for symmetry / future use).
_ = flrw_constants
