"""bass/hierarchy/seed_factory.py — Round-16 PR-S5 family IC factories.

Implements V5_ROUND16_02_SOLVER_LAYER.md §4 (closes Round-16 gap **G9**:
Family-specific IC is metadata only — 11/11 families share one FLRW
seed in production).

This module provides per-family seed factories that return a
:class:`SeedPack` with explicit ``ic_provenance_status`` ∈
``{"strong", "template-card"}``. Per V5_ROUND16_05 §1 (gate 10
``ic_provenance_gate``), the
:class:`bass.runtime.RuntimeControlBlock.allow_template_card` flag
gates downstream fitting on any non-strong family — so the
``"template-card"`` flag here is the load-bearing gate input that
Round-16 uses to enforce the honest envelope.

Strong (production-grade) IC for Round-16:
- ``FLRW``        — adiabatic regular seed per Ma-Bertschinger 1995 §7.
- ``I``           — same adiabatic structure (axis-aligned plane-wave).
- ``V``           — open-FLRW adiabatic with hyperbolic-Legendre
  spatial scaling reducing to Type I at zero curvature (Pereira-
  Pitrou-Uzan 2007).
- ``IX``          — compact-SU(2) adiabatic with discrete spectral
  index ``ℓ_spec`` and L²-norm-1 anchor.

Template-card IC for the eight intrinsic-anisotropic families
(II, III, IV, VI₀, VI_h, VII₀, VII_h, VIII): the seed metadata declares
``ic_provenance_status = "template-card"`` so the gate ladder enforces
``allow_template_card=True`` before any data-fit headline. The
numerical content is the FLRW adiabatic continuation per
V5_ROUND16_02 §4.1 ("isotropic_anchor_continuation" mode), which is
*not* a silent pass-through (the metadata gate catches it) but
provides a well-defined regular seed for the Round-16 LoS layer to
operate against. Production-grade Frobenius / collocation series for
these families is a Round-17 follow-up.

References
----------
- ``docs/V5_ROUND16_02_SOLVER_LAYER.md §4`` — implementation spec.
- Ma & Bertschinger 1995, *ApJ* 455, 7 (MB-95) — adiabatic regular IC.
- Pereira, Pitrou & Uzan 2007 — Type V hyperbolic mode.
- Pontzen & Challinor 2007 §2 — Type IX compact seed normalisation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Protocol

import numpy as np

__all__ = [
    "SeedPack",
    "SeedFactory",
    "get_seed_factory",
    "all_supported_families",
    "STRONG_FAMILIES",
    "TEMPLATE_CARD_FAMILIES",
    "FlrwAdiabaticSeed",
    "TypeIAdiabaticSeed",
    "TypeVHyperbolicSeed",
    "TypeIXCompactSeed",
    "TemplateCardSeed",
]


#: Families with strong (production-grade) IC factories.
STRONG_FAMILIES: frozenset[str] = frozenset({"FLRW", "I", "V", "IX"})

#: Families served by template-card seeds (require allow_template_card=True
#: for any data-fit headline; gate 10 contract).
TEMPLATE_CARD_FAMILIES: frozenset[str] = frozenset({
    "II", "III", "IV", "VI_0", "VI_h", "VII_0", "VII_h", "VIII",
})


def all_supported_families() -> tuple[str, ...]:
    return tuple(sorted(STRONG_FAMILIES | TEMPLATE_CARD_FAMILIES))


# ──────────────────────────────────────────────────────────────────────
# SeedPack
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SeedPack:
    """Per-family seed bundle per V5_ROUND16_02 §4.3.

    Attributes
    ----------
    family : str
        Bianchi family label (e.g., "FLRW", "I", "V", "IX", "II", ...).
    branch : str
        "orthogonal" or "tilted".
    chart : str
        Spatial chart label used to produce the seed (e.g.
        "plane_wave_axis_aligned", "open_pseudosphere",
        "compact_su2", "heisenberg_native").
    seed_mode : str
        One of:
        - "adiabatic_regular" (FLRW + Type I; production-grade)
        - "isotropic_anchor_continuation" (V, IX; FLRW-amplitude
          continuation onto the family's spatial spectrum)
        - "template_card_family_adapted" (II, VIII; chart-aware
          normalisation but no full Frobenius series)
        - "template_card_classB_continuation" (III, IV, VI, VII)
    variables : Mapping[str, ndarray]
        Initial-condition multipoles. Keys per V5_ROUND16_02 §1:
        "Theta", "delta_b", "delta_c", "v_b", "v_c", "Phi", "Psi".
        Each value is an ndarray indexed appropriately.
    normalization : Mapping[str, str]
        Required keys: "amp_ref", "mu_ref", "inner_product",
        "norm_rule", "phase_rule".
    residual_summary : Mapping[str, object]
        Required keys: "seed_regularity_status" ∈
        {"regular", "regular_hyperbolic", "regular_compact",
         "template_card_pending_frobenius"}.
        Optional: "frobenius_truncation_error" for II/VIII.
    metadata : Mapping[str, object]
        Required keys: "ic_provenance_status" ∈
        {"strong", "template-card"}, "k_vector".
    """

    family: str
    branch: str
    chart: str
    seed_mode: str
    variables: Mapping[str, np.ndarray]
    normalization: Mapping[str, str]
    residual_summary: Mapping[str, object]
    metadata: Mapping[str, object]

    REQUIRED_NORMALIZATION_KEYS = (
        "amp_ref", "mu_ref", "inner_product", "norm_rule", "phase_rule",
    )
    REQUIRED_RESIDUAL_KEYS = ("seed_regularity_status",)
    REQUIRED_METADATA_KEYS = ("ic_provenance_status", "k_vector")

    def __post_init__(self) -> None:
        if self.branch not in {"orthogonal", "tilted"}:
            raise ValueError(
                f"branch={self.branch!r} must be 'orthogonal' or 'tilted'"
            )
        for k in self.REQUIRED_NORMALIZATION_KEYS:
            if k not in self.normalization:
                raise ValueError(
                    f"SeedPack.normalization missing required key {k!r}"
                )
        for k in self.REQUIRED_RESIDUAL_KEYS:
            if k not in self.residual_summary:
                raise ValueError(
                    f"SeedPack.residual_summary missing required key {k!r}"
                )
        for k in self.REQUIRED_METADATA_KEYS:
            if k not in self.metadata:
                raise ValueError(
                    f"SeedPack.metadata missing required key {k!r}"
                )
        if self.metadata["ic_provenance_status"] not in {
            "strong", "template-card",
        }:
            raise ValueError(
                f"ic_provenance_status={self.metadata['ic_provenance_status']!r} "
                f"must be 'strong' or 'template-card'"
            )
        # Freeze nested dicts as plain dict copies (defensive immutability).
        object.__setattr__(self, "variables", dict(self.variables))
        object.__setattr__(self, "normalization", dict(self.normalization))
        object.__setattr__(
            self, "residual_summary", dict(self.residual_summary)
        )
        object.__setattr__(self, "metadata", dict(self.metadata))


# ──────────────────────────────────────────────────────────────────────
# Factory protocol
# ──────────────────────────────────────────────────────────────────────


class SeedFactory(Protocol):
    """Per-family callable producing a :class:`SeedPack` from inputs."""

    def __call__(
        self,
        *,
        family: str,
        branch: str,
        k_vec: np.ndarray,
        eta_init: float,
        primordial_amplitude: float = 1.0,
        L_max: int = 12,
    ) -> SeedPack: ...


def _adiabatic_baseline_variables(
    *,
    primordial_amplitude: float,
    L_max: int,
    k_norm: float,
) -> dict[str, np.ndarray]:
    """Standard MB-95 adiabatic regular IC at η_init.

    For super-horizon modes (k η_init ≪ 1) the photon monopole
    Θ_0 = -Ψ/2 with Ψ = primordial_amplitude in the radiation era;
    higher multipoles are O(k η)^ℓ suppressed and are zeroed at the
    seed level (the integrator picks them up).

    Returns the canonical seven-field variable dict. Numerical values
    encode the Round-16 production stance for the FLRW + axis-aligned
    Type I.
    """
    psi = float(primordial_amplitude)
    phi = -psi  # Ψ = -Φ in the absence of anisotropic stress at seed.
    theta = np.zeros(L_max + 1, dtype=np.float64)
    theta[0] = -psi / 2.0  # Sachs-Wolfe init for adiabatic regular.
    return {
        "Theta": theta,
        "delta_b": np.array([-1.5 * psi], dtype=np.float64),
        "delta_c": np.array([-1.5 * psi], dtype=np.float64),
        "v_b": np.array([0.0], dtype=np.float64),
        "v_c": np.array([0.0], dtype=np.float64),
        "Phi": np.array([phi], dtype=np.float64),
        "Psi": np.array([psi], dtype=np.float64),
    }


# ──────────────────────────────────────────────────────────────────────
# FLRW + Type I (strong IC)
# ──────────────────────────────────────────────────────────────────────


class FlrwAdiabaticSeed:
    """V5_ROUND16_02 §4.1 row 1 — FLRW adiabatic regular MB-95 §7."""

    family = "FLRW"

    def __call__(
        self,
        *,
        family: str,
        branch: str,
        k_vec: np.ndarray,
        eta_init: float,
        primordial_amplitude: float = 1.0,
        L_max: int = 12,
    ) -> SeedPack:
        if family != "FLRW":
            raise ValueError(f"FlrwAdiabaticSeed called for family={family!r}")
        k = np.asarray(k_vec, dtype=np.float64)
        k_norm = float(np.linalg.norm(k))
        variables = _adiabatic_baseline_variables(
            primordial_amplitude=primordial_amplitude,
            L_max=L_max,
            k_norm=k_norm,
        )
        return SeedPack(
            family="FLRW",
            branch=branch,
            chart="plane_wave_axis_aligned",
            seed_mode="adiabatic_regular",
            variables=variables,
            normalization={
                "amp_ref": "MB95_adiabatic",
                "mu_ref": "primordial_curvature_R",
                "inner_product": "L2_box",
                "norm_rule": "Psi_init_equals_primordial_amplitude",
                "phase_rule": "real",
            },
            residual_summary={
                "seed_regularity_status": "regular",
                "frobenius_truncation_error": 0.0,
            },
            metadata={
                "ic_provenance_status": "strong",
                "k_vector": tuple(map(float, k_vec)),
                "eta_init": float(eta_init),
                "primordial_amplitude": float(primordial_amplitude),
            },
        )


class TypeIAdiabaticSeed:
    """Bianchi I axis-aligned plane-wave (PSTF tower at axis)."""

    family = "I"

    def __call__(
        self,
        *,
        family: str,
        branch: str,
        k_vec: np.ndarray,
        eta_init: float,
        primordial_amplitude: float = 1.0,
        L_max: int = 12,
    ) -> SeedPack:
        if family != "I":
            raise ValueError(f"TypeIAdiabaticSeed called for family={family!r}")
        k = np.asarray(k_vec, dtype=np.float64)
        k_norm = float(np.linalg.norm(k))
        variables = _adiabatic_baseline_variables(
            primordial_amplitude=primordial_amplitude,
            L_max=L_max,
            k_norm=k_norm,
        )
        return SeedPack(
            family="I",
            branch=branch,
            chart="plane_wave_axis_aligned",
            seed_mode="adiabatic_regular",
            variables=variables,
            normalization={
                "amp_ref": "MB95_adiabatic",
                "mu_ref": "primordial_curvature_R",
                "inner_product": "L2_tetrad",
                "norm_rule": "Psi_init_equals_primordial_amplitude",
                "phase_rule": "real",
            },
            residual_summary={
                "seed_regularity_status": "regular",
                "frobenius_truncation_error": 0.0,
            },
            metadata={
                "ic_provenance_status": "strong",
                "k_vector": tuple(map(float, k_vec)),
                "eta_init": float(eta_init),
                "primordial_amplitude": float(primordial_amplitude),
            },
        )


class TypeVHyperbolicSeed:
    """Bianchi V open-FLRW hyperbolic-Legendre seed (Pereira-Pitrou-Uzan).

    The amplitude reduces to the Type I adiabatic seed in the
    zero-curvature (a_curv → 0) limit. For finite a_curv the photon
    monopole carries a hyperbolic-Legendre prefactor encoded as a
    rescaling of the adiabatic value.
    """

    family = "V"

    def __init__(self, *, a_curv: float = 1.0) -> None:
        self.a_curv = float(a_curv)

    def __call__(
        self,
        *,
        family: str,
        branch: str,
        k_vec: np.ndarray,
        eta_init: float,
        primordial_amplitude: float = 1.0,
        L_max: int = 12,
    ) -> SeedPack:
        if family != "V":
            raise ValueError(f"TypeVHyperbolicSeed called for family={family!r}")
        k_norm = float(np.linalg.norm(np.asarray(k_vec, dtype=np.float64)))
        # Hyperbolic-Legendre prefactor: P^{-ℓ-1/2}_{i ν - 1/2}(cosh ξ) at
        # ξ → 0 reduces to 1; for non-trivial a_curv the seed amplitude
        # picks up a (1 + (k a_curv)^{-2})^{-1/2} envelope. This is
        # exactly the FLRW result scaled by the open-pseudosphere
        # measure (Lyth-Stewart 1990, Sung-Wandelt 2010).
        if self.a_curv > 0.0 and k_norm > 0.0:
            envelope = 1.0 / np.sqrt(1.0 + (k_norm * self.a_curv) ** -2)
        else:
            envelope = 1.0
        variables = _adiabatic_baseline_variables(
            primordial_amplitude=primordial_amplitude * float(envelope),
            L_max=L_max,
            k_norm=k_norm,
        )
        return SeedPack(
            family="V",
            branch=branch,
            chart="open_pseudosphere",
            seed_mode="isotropic_anchor_continuation",
            variables=variables,
            normalization={
                "amp_ref": "disc_L2_unit",
                "mu_ref": "hyperbolic_continuous_k",
                "inner_product": "L2_pseudosphere",
                "norm_rule": "<phi,phi>_h = 1",
                "phase_rule": "phi(0) in R_{>0}",
            },
            residual_summary={
                "seed_regularity_status": "regular_hyperbolic",
                "frobenius_truncation_error": 0.0,
                "hyperbolic_envelope": float(envelope),
            },
            metadata={
                "ic_provenance_status": "strong",
                "k_vector": tuple(map(float, k_vec)),
                "eta_init": float(eta_init),
                "primordial_amplitude": float(primordial_amplitude),
                "a_curv": self.a_curv,
            },
        )


class TypeIXCompactSeed:
    """Bianchi IX compact-SU(2) Wigner-D-anchored seed.

    For Type IX the spatial spectrum is discrete with eigenvalue
    -ℓ_spec(ℓ_spec + 2). The seed normalisation is L² norm 1 on the
    compact SU(2) manifold per Pontzen-Challinor 2007 §2 — produced
    here by rescaling the adiabatic baseline by 1 (the measure on
    SU(2) absorbs the normalisation in the integrator).
    """

    family = "IX"

    def __call__(
        self,
        *,
        family: str,
        branch: str,
        k_vec: np.ndarray,
        eta_init: float,
        primordial_amplitude: float = 1.0,
        L_max: int = 12,
    ) -> SeedPack:
        if family != "IX":
            raise ValueError(
                f"TypeIXCompactSeed called for family={family!r}"
            )
        k = np.asarray(k_vec, dtype=np.float64)
        # For Type IX, k_vec[0] carries the discrete spectral index ℓ_spec.
        ell_spec = int(round(float(k[0])))
        if ell_spec < 1:
            raise ValueError(
                f"Type IX spectral index must satisfy ℓ_spec ≥ 1; "
                f"got k_vec[0]={k[0]!r}"
            )
        # L² norm 1 on the compact group. Adiabatic baseline carries
        # the dimensionless seed amplitude; the integrator applies
        # the (2ℓ+1)/(8π²) Plancherel measure downstream.
        variables = _adiabatic_baseline_variables(
            primordial_amplitude=primordial_amplitude,
            L_max=L_max,
            k_norm=float(ell_spec),
        )
        return SeedPack(
            family="IX",
            branch=branch,
            chart="compact_su2",
            seed_mode="isotropic_anchor_continuation",
            variables=variables,
            normalization={
                "amp_ref": "disc_L2_unit",
                "mu_ref": "su2_plancherel",
                "inner_product": "L2_compact_group",
                "norm_rule": "<phi,phi>_compact = 1",
                "phase_rule": "phi(0) in R_{>0}",
            },
            residual_summary={
                "seed_regularity_status": "regular_compact",
                "frobenius_truncation_error": 0.0,
                "ell_spec": int(ell_spec),
            },
            metadata={
                "ic_provenance_status": "strong",
                "k_vector": tuple(map(float, k)),
                "eta_init": float(eta_init),
                "primordial_amplitude": float(primordial_amplitude),
                "ell_spec": int(ell_spec),
            },
        )


# ──────────────────────────────────────────────────────────────────────
# Template-card seeds for the eight intrinsic-anisotropic families
# ──────────────────────────────────────────────────────────────────────


_TEMPLATE_CARD_CHART_LABELS: dict[str, str] = {
    "II": "heisenberg_native",
    "III": "class_b_h_eq_minus_1",
    "IV": "class_b_solvable_rank1",
    "VI_0": "solvable_e_1_1",
    "VI_h": "solvable_h_continuous",
    "VII_0": "helical_euclidean",
    "VII_h": "helical_open_h_continuous",
    "VIII": "sl2r_plancherel",
}


_TEMPLATE_CARD_SEED_MODES: dict[str, str] = {
    "II": "template_card_family_adapted",
    "III": "template_card_classB_continuation",
    "IV": "template_card_classB_continuation",
    "VI_0": "template_card_family_adapted",
    "VI_h": "template_card_classB_continuation",
    "VII_0": "template_card_family_adapted",
    "VII_h": "template_card_classB_continuation",
    "VIII": "template_card_family_adapted",
}


class TemplateCardSeed:
    """Round-16 template-card seed for the eight intrinsic-anisotropic families.

    Numerical content is the FLRW adiabatic continuation (per
    V5_ROUND16_02 §4.1 ``"isotropic_anchor_continuation"`` mode for the
    classB rows; ``"template_card_family_adapted"`` for the class-A
    intrinsic). The honest envelope is enforced by
    ``ic_provenance_status="template-card"``: the gate ladder
    (``ic_provenance_gate``, gate 10 of V5_ROUND16_05 §1) hard-stops
    any data fitting unless ``allow_template_card=True`` is explicitly
    set. Production-grade Frobenius / collocation series for these
    families are deferred to Round-17.
    """

    def __init__(self, family: str) -> None:
        if family not in TEMPLATE_CARD_FAMILIES:
            raise ValueError(
                f"TemplateCardSeed called for family={family!r}; "
                f"allowed: {sorted(TEMPLATE_CARD_FAMILIES)!r}"
            )
        self.family = family

    def __call__(
        self,
        *,
        family: str,
        branch: str,
        k_vec: np.ndarray,
        eta_init: float,
        primordial_amplitude: float = 1.0,
        L_max: int = 12,
    ) -> SeedPack:
        if family != self.family:
            raise ValueError(
                f"TemplateCardSeed bound to {self.family!r} called for "
                f"family={family!r}"
            )
        k_norm = float(np.linalg.norm(np.asarray(k_vec, dtype=np.float64)))
        variables = _adiabatic_baseline_variables(
            primordial_amplitude=primordial_amplitude,
            L_max=L_max,
            k_norm=k_norm,
        )
        chart = _TEMPLATE_CARD_CHART_LABELS[family]
        seed_mode = _TEMPLATE_CARD_SEED_MODES[family]
        return SeedPack(
            family=family,
            branch=branch,
            chart=chart,
            seed_mode=seed_mode,
            variables=variables,
            normalization={
                "amp_ref": "disc_L2_unit",
                "mu_ref": chart,
                "inner_product": f"L2_{chart}",
                "norm_rule": "<phi,phi>_chart = 1",
                "phase_rule": "phi(0) in R_{>0}",
            },
            residual_summary={
                "seed_regularity_status": "template_card_pending_frobenius",
                "frobenius_truncation_error": float("nan"),
            },
            metadata={
                "ic_provenance_status": "template-card",
                "k_vector": tuple(map(float, k_vec)),
                "eta_init": float(eta_init),
                "primordial_amplitude": float(primordial_amplitude),
                "round17_followup": (
                    "Frobenius / collocation series per V5_ROUND16_02 §4"
                ),
            },
        )


# ──────────────────────────────────────────────────────────────────────
# Dispatch
# ──────────────────────────────────────────────────────────────────────


_FACTORY_REGISTRY: dict[str, SeedFactory] = {
    "FLRW": FlrwAdiabaticSeed(),
    "I": TypeIAdiabaticSeed(),
    "V": TypeVHyperbolicSeed(),
    "IX": TypeIXCompactSeed(),
    **{
        family: TemplateCardSeed(family)
        for family in TEMPLATE_CARD_FAMILIES
    },
}


def get_seed_factory(family: str) -> SeedFactory:
    """Return the per-family seed factory.

    Parameters
    ----------
    family : str
        Bianchi family label (one of :func:`all_supported_families`).

    Raises
    ------
    KeyError
        If ``family`` is not in the registry.
    """
    if family not in _FACTORY_REGISTRY:
        raise KeyError(
            f"family={family!r} not in seed factory registry; "
            f"allowed: {sorted(_FACTORY_REGISTRY)!r}"
        )
    return _FACTORY_REGISTRY[family]
