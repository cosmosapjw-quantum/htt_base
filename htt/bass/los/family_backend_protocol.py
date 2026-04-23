"""ver3 PR-08 family backend protocol for BASS LOS / backend ownership.

This module freezes backend-contract surfaces only. It does not claim that
all family-specific numerics are implemented; it records the backend,
translator, and seed provenance contract in machine-readable form.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from bass.background.bianchi_types import FamilySpec, get_family_spec
from bass.validation import GateBundle, make_gate_bundle

__all__ = [
    "CollocationPolicy",
    "GeometryOps",
    "NativeLabelTranslatorCard",
    "FamilyTemplateCard",
    "NativeLabelCard",
    "SeedRequest",
    "SeedPack",
    "ModeOps",
    "FamilyBackend",
    "family_backend_gate_bundle",
    "build_backend",
]


_CHART_DEFAULTS: dict[str, str] = {
    "FLRW": "isotropic_trivial_chart",
    "I": "plane_wave_cartesian",
    "II": "nil_heisenberg",
    "III": "class_b_hyperbolic_branch",
    "IV": "solvable_group_chart",
    "V": "hyperbolic_open_chart",
    "VI_0": "class_a_solvable_intrinsic",
    "VI_h": "class_b_negative_h_chart",
    "VII_0": "helical_euclidean_chart",
    "VII_h": "helical_open_h_chart",
    "VIII": "sl2r_noncompact_chart",
    "IX": "wigner_d_compact_chart",
}

_REPO_ROOT = Path(__file__).resolve().parents[3]
_V5_VERIFICATION_PATH = _REPO_ROOT / "docs" / "bianchi_design_pack_v5" / "verification" / "crosscheck_results.json"


def _load_v5_verification_bundle() -> dict[str, object]:
    try:
        payload = json.loads(_V5_VERIFICATION_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {
            "crosscheck_pass": False,
            "load_status": "missing",
            "verification_reference": "docs/bianchi_design_pack_v5/verification/crosscheck_results.json",
        }
    except json.JSONDecodeError:
        return {
            "crosscheck_pass": False,
            "load_status": "invalid_json",
            "verification_reference": "docs/bianchi_design_pack_v5/verification/crosscheck_results.json",
        }
    payload["load_status"] = "loaded"
    payload["verification_reference"] = "docs/bianchi_design_pack_v5/verification/crosscheck_results.json"
    return payload


_V5_VERIFICATION_BUNDLE = _load_v5_verification_bundle()

_BOUNDARY_POLICIES: dict[str, str] = {
    "FLRW": "isotropic_regular",
    "I": "cartesian_regular",
    "II": "finite_domain_nil_edges_logged",
    "III": "truncated_hyperbolic_branch",
    "IV": "anisotropic_edge_metadata",
    "V": "open_hyperbolic_radial_cutoff",
    "VI_0": "mixed_sign_directional_refinement",
    "VI_h": "h_dependent_class_b_cutoff",
    "VII_0": "helical_euclidean_regular",
    "VII_h": "positive_h_open_cutoff",
    "VIII": "noncompact_truncation_with_residual_trend",
    "IX": "compact_group_regular",
}

_OPERATOR_KERNELS: dict[str, str] = {
    "FLRW": "flrw_scalar_validation",
    "I": "bianchi_i_matrix_exact",
    "II": "nil_intrinsic_template",
    "III": "class_b_hyperbolic_template",
    "IV": "solvable_group_template",
    "V": "class_b_open_matrix_approx",
    "VI_0": "class_a_axis_matrix_approx",
    "VI_h": "class_b_twist_axis_matrix_approx",
    "VII_0": "class_a_helical_matrix_approx",
    "VII_h": "class_b_helical_matrix_approx",
    "VIII": "class_a_semisimple_matrix_approx",
    "IX": "class_a_compact_matrix_approx",
}

_NATIVE_LABELS: dict[str, str] = {
    "FLRW": "mu_flrw",
    "I": "mu_cart",
    "II": "mu_nil",
    "III": "mu_hyp",
    "IV": "mu_solv",
    "V": "mu_open",
    "VI_0": "mu_VI0",
    "VI_h": "mu_VIh",
    "VII_0": "mu_VII0",
    "VII_h": "mu_VIIh",
    "VIII": "mu_sl2r",
    "IX": "mu_su2",
}

_DEFAULT_BRANCH_FLAGS: dict[str, str | None] = {
    "FLRW": "isotropic_anchor",
    "I": "isotropic_anchor",
    "II": "intrinsic",
    "III": "VI_-1_special",
    "IV": "intrinsic",
    "V": "isotropic_anchor",
    "VI_0": "intrinsic",
    "VI_h": "negative_h_branch",
    "VII_0": "isotropic_anchor",
    "VII_h": "positive_h_branch",
    "VIII": "noncompact_branch",
    "IX": "compact_anchor",
}

_SEED_MODES: dict[str, tuple[str, ...]] = {
    "FLRW": ("flrw_like_regular", "continued_anchor", "boosted_electron_frame"),
    "I": ("flrw_like_regular", "continued_anchor", "boosted_electron_frame"),
    "V": ("flrw_like_regular", "continued_anchor", "boosted_electron_frame"),
    "VII_0": ("flrw_like_regular", "continued_anchor", "boosted_electron_frame"),
    "VII_h": ("flrw_like_regular", "continued_anchor", "boosted_electron_frame"),
    "IX": ("flrw_like_regular", "continued_anchor", "boosted_electron_frame"),
    "II": ("frobenius", "local_regular", "collocation_projected"),
    "III": ("frobenius", "local_regular", "collocation_projected"),
    "IV": ("local_regular", "collocation_projected"),
    "VI_0": ("frobenius", "local_regular", "collocation_projected"),
    "VI_h": ("h_aware_frobenius", "h_aware_local_regular", "collocation_projected"),
    "VIII": ("local_regular", "group_adapted", "collocation_projected"),
}

_EDGE_METADATA_FIELDS: dict[str, tuple[str, ...]] = {
    "FLRW": ("regularity_domain",),
    "I": ("cartesian_domain",),
    "II": ("domain_edge", "truncation_edge", "edge_treatment"),
    "III": ("radial_cutoff", "branch_flag", "edge_treatment"),
    "IV": ("coordinate_order", "anisotropic_edge", "edge_treatment"),
    "V": ("radial_cutoff", "open_domain"),
    "VI_0": ("principal_direction_refinement", "directional_tag", "edge_treatment"),
    "VI_h": ("h", "branch_refinement", "edge_treatment"),
    "VII_0": ("helical_domain",),
    "VII_h": ("h", "radial_cutoff", "helical_domain"),
    "VIII": ("noncompact_cutoff", "branch_tag", "residual_trend"),
    "IX": ("compact_domain",),
}

_FAMILY_RESIDUALS: dict[str, tuple[str, ...]] = {
    "FLRW": ("isotropic_anchor_limit", "label_translator_roundtrip", "seed_regularity"),
    "I": ("cartesian_anchor_limit", "label_translator_roundtrip", "seed_regularity"),
    "II": ("nil_chart_regularity", "label_translator_roundtrip", "seed_regularity"),
    "III": ("class_b_branch_consistency", "hyperbolic_cutoff", "seed_branch_label_consistency"),
    "IV": ("chart_order", "edge_anisotropy", "seed_regularity"),
    "V": ("open_anchor_limit", "label_translator_roundtrip", "seed_regularity"),
    "VI_0": ("directional_truncation", "translator_directional_tag", "seed_regularity"),
    "VI_h": ("h_consistency", "branch_label", "cutoff_refinement"),
    "VII_0": ("helical_anchor_limit", "label_translator_roundtrip", "seed_regularity"),
    "VII_h": ("positive_h_anchor_limit", "label_translator_roundtrip", "seed_regularity"),
    "VIII": ("noncompact_truncation", "branch_tag", "seed_regularity"),
    "IX": ("compact_anchor_limit", "label_translator_roundtrip", "seed_regularity"),
}

_MUST_NOT_DO: dict[str, tuple[str, ...]] = {
    "FLRW": ("no_hidden_branch_choice",),
    "I": ("no_hidden_branch_choice", "no_local_boost_folded_into_backend"),
    "II": ("no_flrw_seed_reuse", "no_implicit_periodic_boundary", "no_unlabeled_branch_choice"),
    "III": ("no_open_flrw_seed_import_without_branch_justification", "no_dropping_special_branch_flag"),
    "IV": ("no_isotropic_radial_reduction", "no_chart_swap_without_translator_update"),
    "V": ("no_hidden_flrw_import_without_open_chart_metadata",),
    "VI_0": ("no_borrowing_type_i_or_vii_seeds", "no_isotropic_direction_compression"),
    "VI_h": ("no_using_vi0_seed_at_nonzero_h", "no_hiding_h_inside_generic_branch_label"),
    "VII_0": ("no_hidden_branch_choice", "no_local_boost_folded_into_backend"),
    "VII_h": ("no_hidden_h_branch_choice", "no_local_boost_folded_into_backend"),
    "VIII": ("no_compact_su2_reuse", "no_wigner_d_assumption_without_explicit_approximation_tag"),
    "IX": ("no_untracked_compact_basis_reordering",),
}

_COLLOCATION_NOTES: dict[str, tuple[str, ...]] = {
    "FLRW": ("anchor branch uses regular documented domain",),
    "I": ("cartesian regular branch with explicit storage ordering",),
    "II": ("finite domain truncation; no periodic closure by default",),
    "III": ("truncated hyperbolic domain with explicit class-B branch metadata",),
    "IV": ("finite truncation with anisotropic edge metadata and logged coordinate remap",),
    "V": ("open hyperbolic chart with explicit radial cutoff metadata",),
    "VI_0": ("mixed-sign directional bookkeeping with per-axis refinement",),
    "VI_h": ("h-dependent truncated class-B chart; h changes require branch refinement",),
    "VII_0": ("helical Euclidean-like anchor backend with explicit storage order",),
    "VII_h": ("positive-h open helical chart with explicit h metadata",),
    "VIII": ("noncompact truncation must log residual trend and cutoff strategy",),
    "IX": ("compact harmonic backend with explicit storage translator",),
}

_FROZEN_SEED_NORMALIZATION = {
    "amp_ref": "disc_L2_unit",
    "mu_ref": "native_cross_section_label",
    "inner_product": "<phi,psi>_h = sum_q w_q phi_q^* psi_q",
    "norm_rule": "<phi,phi>_h = 1",
    "phase_rule": "phi(q_anchor) in R_{>0}",
    "release_convention": "frozen_discrete_weighted_L2",
}

_FROZEN_COLLOCATION_DEFAULTS = {
    "weights": {
        "w0": "h/2",
        "wi": "h",
        "wN": "h/2",
    },
    "d1": "(f[i-2]-8*f[i-1]+8*f[i+1]-f[i+2])/(12*h)",
    "d2": "(-f[i-2]+16*f[i-1]-30*f[i]+16*f[i+1]-f[i+2])/(12*h**2)",
    "bcl": "(-3*f0+4*f1-f2)/(2*h)",
    "bcr": "(3*fN-4*fN1+fN2)/(2*h)",
}

_FROZEN_SOLVABLE_LOOKUP = {
    "II": {
        "K": "R\\{0}",
        "k0": "(0,k)",
        "rho": "Abs(k)",
        "nudot": "Abs(k)",
    },
    "III": {
        "K": "R x {+-1}",
        "k0": "(k2,k1)",
        "rho": "exp(-r)",
        "nudot": "1",
    },
    "IV": {
        "K": "R_+ x {+-1}",
        "k0": "(k2, k2*k1)",
        "rho": "exp(-2*r)*(1+k1)",
        "nudot": "1+k1",
    },
    "VI_0": {
        "K": "R_+ x Z4",
        "k0": "R_pi/2^k2 (1,k1)",
        "nudot": "1",
        "limit_note": "q=1 -> h=0^- VI_h limit",
    },
    "VII_h": {
        "K": "(-exp(pi*p),-1] U [1,exp(pi*p))",
        "k0": "(k,0)",
        "rho": "exp(-2*p*r)*Abs(k)",
        "nudot": "Abs(k)",
    },
}

_TYPE_VIII_LOOKUP = {
    "principal_series_labels": "(mu,s), -1/2 <= mu < 1/2, s>=0",
    "principal_series_measure": "(2*pi)^(-2) * s*sinh(2*pi*s)/(cosh(2*pi*s)+cos(2*pi*mu))",
    "discrete_series_labels": "D_lambda^+|D_lambda^-, lambda>=1/2",
    "discrete_series_measure": "(2*pi)^(-2) * (lambda - 1/2)",
    "mu0_reduction": "(2*pi)^(-2) * s*tanh(pi*s)",
    "mu_half_reduction": "(2*pi)^(-2) * s*coth(pi*s)",
    "branch_flags": ("principal", "discrete"),
}


def _class_b_bridge_payload(family_spec: FamilySpec) -> dict[str, object]:
    family = family_spec.family
    if family == "III":
        return {
            "special_branch": "VI_-1_special",
            "bridge_formula": "h = -((1-q)/(1+q))**2",
            "inverse_formula": "q = (1-sqrt(-h))/(1+sqrt(-h))",
            "resolved_value": {"q": 0.0, "h": -1.0},
        }
    if family == "VI_0":
        return {
            "limit_from": "VI_h",
            "bridge_formula": "h = -((1-q)/(1+q))**2",
            "inverse_formula": "q = (1-sqrt(-h))/(1+sqrt(-h))",
            "resolved_limit": {"q": 1.0, "h": 0.0},
        }
    if family == "VI_h":
        h = float(family_spec.algebra.h_parameter)
        root = math.sqrt(-h)
        q = (1.0 - root) / (1.0 + root)
        return {
            "bridge_formula": "h = -((1-q)/(1+q))**2",
            "inverse_formula": "q = (1-sqrt(-h))/(1+sqrt(-h))",
            "resolved_value": {"h": h, "q": q},
            "resolved_branch": "q_positive_branch" if q > 0.0 else "q_negative_branch",
        }
    if family == "VII_h":
        h = float(family_spec.algebra.h_parameter)
        p = math.sqrt(h)
        return {
            "bridge_formula": "h = p^2",
            "inverse_formula": "p = sqrt(h)",
            "resolved_value": {"h": h, "p": p},
            "resolved_branch": "positive_h_branch",
        }
    return {}


def _resolved_lookup_payload(family_spec: FamilySpec) -> dict[str, object]:
    family = family_spec.family
    payload: dict[str, object] = {
        "lookup_resolution_status": "frozen_v5_formula_set",
        "seed_normalization_convention": dict(_FROZEN_SEED_NORMALIZATION),
        "collocation_default_stencil": dict(_FROZEN_COLLOCATION_DEFAULTS),
    }
    class_b_bridge = _class_b_bridge_payload(family_spec)
    if class_b_bridge:
        payload["class_b_parameter_bridge"] = class_b_bridge
    if family in _FROZEN_SOLVABLE_LOOKUP:
        payload["frozen_backend_constants"] = dict(_FROZEN_SOLVABLE_LOOKUP[family])
    elif family == "VI_h":
        h = float(family_spec.algebra.h_parameter)
        root = math.sqrt(-h)
        q = (1.0 - root) / (1.0 + root)
        if q > 0.0:
            payload["frozen_backend_constants"] = {
                "K": "R_+ x Z4",
                "k0": "R_pi/2^k2 (1,k1)",
                "nudot": "q^(k2 mod 2)",
            }
        else:
            payload["frozen_backend_constants"] = {
                "K": "R/2piZ",
                "k0": "(cos(k), sin(k))",
                "nudot": "cos(k)^2 - q*sin(k)^2",
                "positive_rewrite": "u*sin(k)^2 + cos(k)^2 for q=-u, u>0",
            }
    elif family == "VIII":
        payload["type_viii_lookup"] = dict(_TYPE_VIII_LOOKUP)
    return payload


@dataclass(frozen=True)
class CollocationPolicy:
    domain_policy: str
    boundary_policy: str
    refinement_study_required: bool
    periodic_closure_allowed: bool
    edge_metadata_fields: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def as_payload(self) -> dict[str, object]:
        return {
            "domain_policy": self.domain_policy,
            "boundary_policy": self.boundary_policy,
            "refinement_study_required": self.refinement_study_required,
            "periodic_closure_allowed": self.periodic_closure_allowed,
            "edge_metadata_fields": list(self.edge_metadata_fields),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class NativeLabelTranslatorCard:
    family: str
    native_label_name: str
    parity_flag: str | None
    helicity_flag: str | None
    branch_flag: str | None
    h_parameter: float | None = None
    directional_tag: str | None = None
    coordinate_order: tuple[str, ...] | None = None
    chart: str | None = None

    def as_payload(self) -> dict[str, object]:
        return {
            "family": self.family,
            "native_label_name": self.native_label_name,
            "parity_flag": self.parity_flag,
            "helicity_flag": self.helicity_flag,
            "branch_flag": self.branch_flag,
            "h_parameter": self.h_parameter,
            "directional_tag": self.directional_tag,
            "coordinate_order": None if self.coordinate_order is None else list(self.coordinate_order),
            "chart": self.chart,
        }


@dataclass(frozen=True)
class FamilyTemplateCard:
    family: str
    preferred_chart: str
    operator_kernel_family: str
    preferred_backend: str
    generic_fallback: str
    collocation_policy: CollocationPolicy
    label_translator_card: NativeLabelTranslatorCard
    allowed_seed_provenance: tuple[str, ...]
    family_specific_residuals: tuple[str, ...]
    must_not_do: tuple[str, ...]
    analytic_normalization_status: str
    lookup_resolution_status: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def as_payload(self) -> dict[str, object]:
        return {
            "family": self.family,
            "preferred_chart": self.preferred_chart,
            "operator_kernel_family": self.operator_kernel_family,
            "preferred_backend": self.preferred_backend,
            "generic_fallback": self.generic_fallback,
            "collocation_policy": self.collocation_policy.as_payload(),
            "label_translator_card": self.label_translator_card.as_payload(),
            "allowed_seed_provenance": list(self.allowed_seed_provenance),
            "family_specific_residuals": list(self.family_specific_residuals),
            "must_not_do": list(self.must_not_do),
            "analytic_normalization_status": self.analytic_normalization_status,
            "lookup_resolution_status": self.lookup_resolution_status,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class NativeLabelCard:
    family: str
    native_label: str
    ell: int
    m: int
    sector: str
    parity_flag: str | None = None
    helicity_flag: str | None = None
    branch_flag: str | None = None
    h_parameter: float | None = None
    directional_tag: str | None = None
    coordinate_order: tuple[str, ...] | None = None
    chart: str | None = None

    def __post_init__(self) -> None:
        if self.ell < 0:
            raise ValueError("ell must be non-negative")
        if not self.native_label:
            raise ValueError("native_label must be non-empty")
        if not self.sector:
            raise ValueError("sector must be non-empty")
        if self.coordinate_order is not None and len(self.coordinate_order) == 0:
            raise ValueError("coordinate_order may be None or a non-empty tuple")


@dataclass(frozen=True)
class SeedRequest:
    branch: str
    seed_mode: str
    amplitude_reference: float = 1.0
    native_label: str = "mu0"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SeedPack:
    family: str
    branch: str
    chart: str
    seed_mode: str
    variables: Mapping[str, object]
    normalization: Mapping[str, object]
    residual_summary: Mapping[str, object]
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class ModeOps:
    family: str
    branch: str
    chart: str
    backend_name: str
    operator_kernel_family: str
    truncation: Mapping[str, object]
    boundary_policy: str
    seed_provenance_mode: str
    release_status: str
    mass_matrix: Any
    A_fs: Any
    A_mix: Any
    A_coll: Any
    source_template: Any
    layout_metadata: Mapping[str, object]
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class GeometryOps:
    family: str
    branch: str
    chart: str
    Gamma: Any
    ricci_tensor: Any
    ricci_scalar: float
    S_AB: Any
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class FamilyBackend:
    family_spec: FamilySpec
    truncation: Mapping[str, object]
    chart_options: Mapping[str, object]

    def _chart(self) -> str:
        return str(self.chart_options.get("chart", _CHART_DEFAULTS[self.family_spec.family]))

    def _branch_flag(self) -> str | None:
        return str(self.chart_options.get("branch_flag", _DEFAULT_BRANCH_FLAGS[self.family_spec.family])) if _DEFAULT_BRANCH_FLAGS[self.family_spec.family] is not None else None

    def _coordinate_order(self) -> tuple[str, ...] | None:
        value = self.chart_options.get("coordinate_order")
        if value is None:
            if self.family_spec.family == "IV":
                return ("x_noncompact", "y_shear", "z_twist")
            return None
        return tuple(str(x) for x in value)

    def _directional_tag(self) -> str | None:
        value = self.chart_options.get("directional_tag")
        if value is None:
            if self.family_spec.family == "VI_0":
                return "mixed_sign_axes"
            return None
        return str(value)

    def _label_template(self) -> dict[str, object]:
        translator = self.template_card().label_translator_card
        return {
            "native_label_name": translator.native_label_name,
            "parity_flag": translator.parity_flag,
            "helicity_flag": translator.helicity_flag,
            "branch_flag": translator.branch_flag,
            "h_parameter": translator.h_parameter,
            "directional_tag": translator.directional_tag,
            "coordinate_order": translator.coordinate_order,
            "chart": translator.chart,
        }

    def template_card(self) -> FamilyTemplateCard:
        family = self.family_spec.family
        chart = self._chart()
        boundary_policy = str(
            self.chart_options.get("boundary_policy", _BOUNDARY_POLICIES[family])
        )
        branch_flag = self._branch_flag()
        translator = NativeLabelTranslatorCard(
            family=family,
            native_label_name=_NATIVE_LABELS[family],
            parity_flag=None,
            helicity_flag=None,
            branch_flag=branch_flag,
            h_parameter=self.family_spec.algebra.h_parameter,
            directional_tag=self._directional_tag(),
            coordinate_order=self._coordinate_order(),
            chart=chart,
        )
        collocation = CollocationPolicy(
            domain_policy=boundary_policy,
            boundary_policy=boundary_policy,
            refinement_study_required=True,
            periodic_closure_allowed=False,
            edge_metadata_fields=_EDGE_METADATA_FIELDS[family],
            notes=_COLLOCATION_NOTES[family],
        )
        return FamilyTemplateCard(
            family=family,
            preferred_chart=chart,
            operator_kernel_family=_OPERATOR_KERNELS[family],
            preferred_backend=self.family_spec.preferred_backend,
            generic_fallback=self.family_spec.generic_fallback,
            collocation_policy=collocation,
            label_translator_card=translator,
            allowed_seed_provenance=_SEED_MODES[family],
            family_specific_residuals=_FAMILY_RESIDUALS[family],
            must_not_do=_MUST_NOT_DO[family],
            analytic_normalization_status=(
                "documented_anchor_normalization"
                if self.family_spec.isotropic_anchor
                else "frozen_discrete_weighted_l2_release_convention"
            ),
            lookup_resolution_status="frozen_v5_formula_set",
            metadata={
                "ic_provenance_status": self.family_spec.ic_provenance_status,
                "canonical_gauge": self.family_spec.canonical_gauge,
                "constraint_policy_required": self.family_spec.algebra.branch_policy.constraint_policy_required,
                "isotropic_anchor": self.family_spec.isotropic_anchor,
                "verification_bundle": dict(_V5_VERIFICATION_BUNDLE),
                "verification_crosscheck_pass": bool(
                    _V5_VERIFICATION_BUNDLE.get("crosscheck_pass", False)
                ),
                "verification_reference": str(
                    _V5_VERIFICATION_BUNDLE.get(
                        "verification_reference",
                        "docs/bianchi_design_pack_v5/verification/crosscheck_results.json",
                    )
                ),
                **_resolved_lookup_payload(self.family_spec),
            },
        )

    def operator_factory(self, background_state: Mapping[str, object]) -> ModeOps | tuple[GeometryOps, ModeOps]:
        from bass.hierarchy.ver3_layout_protocol import (
            assemble_free_streaming_block,
            assemble_implicit_block,
            assemble_mass_matrix,
            assemble_mixing_block,
            assemble_source_vector,
            build_hierarchy_layout,
            build_layout_manifest,
        )
        from bass.background.geometry import build_geometry

        branch = str(background_state.get("branch", "orthogonal"))
        if branch not in {"orthogonal", "tilted"}:
            raise ValueError(f"unknown branch {branch!r}")
        if not self.family_spec.algebra.supports_branch(branch):
            raise ValueError(f"{self.family_spec.family} does not support branch {branch!r}")
        opacity_data = background_state.get("opacity_data", {})
        if not isinstance(opacity_data, Mapping):
            raise ValueError("opacity_data must be a mapping when provided")
        source_tables = background_state.get("source_tables", {})
        if not isinstance(source_tables, Mapping):
            raise ValueError("source_tables must be a mapping when provided")
        layout = build_hierarchy_layout(self, self.truncation)
        template_card = self.template_card()
        geometry_contract = background_state.get("geometry")
        geometry = build_geometry(self.family_spec) if geometry_contract is None else geometry_contract
        metadata = {
            "family": self.family_spec.family,
            "class_label": self.family_spec.class_label,
            "isotropic_anchor": self.family_spec.isotropic_anchor,
            "orthogonal_global_tilt_local_boost_split": self.family_spec.orthogonal_global_tilt_local_boost_split,
            "constraint_policy_required": self.family_spec.algebra.branch_policy.constraint_policy_required,
            "h_parameter": self.family_spec.algebra.h_parameter,
            "background_state_tag": background_state.get("state_tag", "background_state"),
            "contract_release_status": "backend-contract-complete",
            "operator_payload_status": "geometry_opacity_coupled_sparse_blocks",
            "analytic_normalization_status": template_card.analytic_normalization_status,
            "lookup_resolution_status": template_card.lookup_resolution_status,
            "verification_crosscheck_pass": bool(
                template_card.metadata.get("verification_crosscheck_pass", False)
            ),
            "verification_reference": template_card.metadata.get("verification_reference"),
            "template_card": template_card.as_payload(),
        }
        ops = ModeOps(
            family=self.family_spec.family,
            branch=branch,
            chart=template_card.preferred_chart,
            backend_name=self.family_spec.preferred_backend,
            operator_kernel_family=template_card.operator_kernel_family,
            truncation=dict(self.truncation),
            boundary_policy=template_card.collocation_policy.boundary_policy,
            seed_provenance_mode="isotropic_anchor_continuation"
            if self.family_spec.ic_provenance_status == "strong"
            else "template_card_family_adapted",
            release_status="backend-operator-bound",
            mass_matrix=assemble_mass_matrix(background_state, self, self.truncation),
            A_fs=assemble_free_streaming_block(background_state, self, self.truncation),
            A_mix=assemble_mixing_block(background_state, self, self.truncation),
            A_coll=assemble_implicit_block(
                background_state,
                self,
                self.truncation,
                opacity_data,
            ),
            source_template=assemble_source_vector(
                background_state,
                self,
                self.truncation,
                source_tables,
            ),
            layout_metadata=build_layout_manifest(
                layout,
                self,
                self.truncation,
                background_state,
            ),
            metadata=metadata,
        )
        if bool(background_state.get("include_geometry", False)):
            geometry_ops = GeometryOps(
                family=self.family_spec.family,
                branch=branch,
                chart=template_card.preferred_chart,
                Gamma=geometry.Gamma,
                ricci_tensor=geometry.ricci_tensor,
                ricci_scalar=float(geometry.ricci_scalar),
                S_AB=geometry.S_AB,
                metadata={
                    "dual_route_status": geometry.dual_route_status,
                    "compact_formula_status": geometry.compact_formula_status,
                },
            )
            return geometry_ops, ops
        return ops

    def evaluate_reduced_local_rhs(
        self,
        background_state: Mapping[str, object],
        *,
        baryon_by_mode_label: Mapping[str, np.ndarray],
        cdm_by_mode_label: Mapping[str, np.ndarray],
        theta_1_by_mode_label: Mapping[str, float],
    ) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
        from bass.hierarchy.ver3_layout_protocol import (
            build_hierarchy_layout,
            evaluate_reduced_local_rhs,
        )

        layout = build_hierarchy_layout(self, self.truncation)
        return evaluate_reduced_local_rhs(
            layout,
            background_state,
            self,
            baryon_by_mode_label=baryon_by_mode_label,
            cdm_by_mode_label=cdm_by_mode_label,
            theta_1_by_mode_label=theta_1_by_mode_label,
        )

    def evaluate_reduced_harmonic_rhs(
        self,
        background_state: Mapping[str, object],
        *,
        photon_T_by_mode_label: Mapping[str, np.ndarray],
        photon_E_by_mode_label: Mapping[str, np.ndarray],
        photon_B_by_mode_label: Mapping[str, np.ndarray],
        neutrino_by_mode_label: Mapping[str, np.ndarray],
        baryon_by_mode_label: Mapping[str, np.ndarray],
        source_by_mode_label: Mapping[str, np.ndarray],
    ) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray]]:
        from bass.hierarchy.ver3_layout_protocol import (
            build_hierarchy_layout,
            evaluate_reduced_harmonic_rhs,
        )

        layout = build_hierarchy_layout(self, self.truncation)
        return evaluate_reduced_harmonic_rhs(
            layout,
            background_state,
            self,
            photon_T_by_mode_label=photon_T_by_mode_label,
            photon_E_by_mode_label=photon_E_by_mode_label,
            photon_B_by_mode_label=photon_B_by_mode_label,
            neutrino_by_mode_label=neutrino_by_mode_label,
            baryon_by_mode_label=baryon_by_mode_label,
            source_by_mode_label=source_by_mode_label,
        )

    def seed_factory(self, seed_request: SeedRequest) -> SeedPack:
        template_card = self.template_card()
        allowed = template_card.allowed_seed_provenance
        if seed_request.seed_mode not in allowed:
            raise ValueError(
                f"{self.family_spec.family} seed_mode {seed_request.seed_mode!r} not allowed; "
                f"allowed={allowed!r}"
            )
        variables = {
            "native_label": seed_request.native_label,
            "branch": seed_request.branch,
        }
        normalization = {
            "amp_ref": _FROZEN_SEED_NORMALIZATION["amp_ref"],
            "amplitude_reference_value": float(seed_request.amplitude_reference),
            "mu_ref": _FROZEN_SEED_NORMALIZATION["mu_ref"],
            "inner_product": _FROZEN_SEED_NORMALIZATION["inner_product"],
            "norm_rule": _FROZEN_SEED_NORMALIZATION["norm_rule"],
            "phase_rule": _FROZEN_SEED_NORMALIZATION["phase_rule"],
            "release_convention": _FROZEN_SEED_NORMALIZATION["release_convention"],
            "chart": self._chart(),
            "analytic_normalization_status": template_card.analytic_normalization_status,
            "lookup_resolution_status": template_card.lookup_resolution_status,
        }
        residual_summary = {
            "seed_regularity_status": "not_executed",
            "translator_roundtrip_status": "required",
            "required_family_residuals": list(template_card.family_specific_residuals),
            "forbidden_shortcut_checks": {
                "no_local_boost_folded_into_global_tilt": True,
                "no_unlabeled_branch_choice": True,
                "no_flrw_seed_reuse_for_intrinsic_family": self.family_spec.family
                not in {"II", "III", "IV", "VI_0", "VI_h", "VIII"},
            },
        }
        metadata = {
            "family": self.family_spec.family,
            "branch_flag": self._branch_flag(),
            "h_parameter": self.family_spec.algebra.h_parameter,
            "chart": self._chart(),
            "coordinate_order": self._coordinate_order(),
            "directional_tag": self._directional_tag(),
            "must_not_do": list(template_card.must_not_do),
            "lookup_resolution_status": template_card.lookup_resolution_status,
            "verification_crosscheck_pass": bool(
                template_card.metadata.get("verification_crosscheck_pass", False)
            ),
            "verification_reference": template_card.metadata.get("verification_reference"),
            "resolved_lookup": dict(template_card.metadata),
            **dict(seed_request.metadata),
        }
        return SeedPack(
            family=self.family_spec.family,
            branch=seed_request.branch,
            chart=self._chart(),
            seed_mode=seed_request.seed_mode,
            variables=variables,
            normalization=normalization,
            residual_summary=residual_summary,
            metadata=metadata,
        )

    def label_translator(self, native_labels: Iterable[NativeLabelCard]) -> tuple[dict[str, object], ...]:
        translated = []
        template = self._label_template()
        for card in native_labels:
            if card.family != self.family_spec.family:
                raise ValueError(
                    f"label family {card.family!r} does not match backend family {self.family_spec.family!r}"
                )
            translated.append(
                {
                    "family": card.family,
                    "storage_key": f"{card.sector}:{card.ell}:{card.m}:{card.native_label}",
                    "ell": card.ell,
                    "m": card.m,
                    "sector": card.sector,
                    "native_label": card.native_label,
                    "parity_flag": card.parity_flag if card.parity_flag is not None else template["parity_flag"],
                    "helicity_flag": card.helicity_flag if card.helicity_flag is not None else template["helicity_flag"],
                    "branch_flag": card.branch_flag if card.branch_flag is not None else template["branch_flag"],
                    "h_parameter": card.h_parameter if card.h_parameter is not None else template["h_parameter"],
                    "directional_tag": card.directional_tag if card.directional_tag is not None else template["directional_tag"],
                    "coordinate_order": card.coordinate_order if card.coordinate_order is not None else template["coordinate_order"],
                    "chart": card.chart if card.chart is not None else template["chart"],
                }
            )
        return tuple(translated)

    def _normalize_label_card(self, card: NativeLabelCard) -> NativeLabelCard:
        template = self._label_template()
        return NativeLabelCard(
            family=card.family,
            native_label=card.native_label,
            ell=card.ell,
            m=card.m,
            sector=card.sector,
            parity_flag=card.parity_flag if card.parity_flag is not None else template["parity_flag"],
            helicity_flag=card.helicity_flag if card.helicity_flag is not None else template["helicity_flag"],
            branch_flag=card.branch_flag if card.branch_flag is not None else template["branch_flag"],
            h_parameter=card.h_parameter if card.h_parameter is not None else template["h_parameter"],
            directional_tag=card.directional_tag if card.directional_tag is not None else template["directional_tag"],
            coordinate_order=card.coordinate_order if card.coordinate_order is not None else template["coordinate_order"],
            chart=card.chart if card.chart is not None else template["chart"],
        )

    def inverse_label_translator(
        self,
        storage_labels: Iterable[Mapping[str, object]],
    ) -> tuple[NativeLabelCard, ...]:
        restored = []
        for row in storage_labels:
            restored.append(
                NativeLabelCard(
                    family=str(row["family"]),
                    native_label=str(row["native_label"]),
                    ell=int(row["ell"]),
                    m=int(row["m"]),
                    sector=str(row["sector"]),
                    parity_flag=row.get("parity_flag"),
                    helicity_flag=row.get("helicity_flag"),
                    branch_flag=row.get("branch_flag"),
                    h_parameter=row.get("h_parameter"),
                    directional_tag=row.get("directional_tag"),
                    coordinate_order=tuple(row["coordinate_order"]) if row.get("coordinate_order") is not None else None,
                    chart=row.get("chart"),
                )
            )
        return tuple(restored)

    def backend_residuals(
        self,
        native_labels: Iterable[NativeLabelCard] | None = None,
    ) -> dict[str, object]:
        translator_roundtrip_residual = None
        if native_labels is not None:
            native_tuple = tuple(native_labels)
            storage = self.label_translator(native_tuple)
            restored = self.inverse_label_translator(storage)
            normalized = tuple(self._normalize_label_card(card) for card in native_tuple)
            translator_roundtrip_residual = 0 if normalized == restored else 1
        return {
            "translator_roundtrip_residual": translator_roundtrip_residual,
            "family": self.family_spec.family,
            "branch_flag_present": self._branch_flag() is not None,
            "h_metadata_present": self.family_spec.algebra.h_parameter is not None,
            "directional_tag_present": self._directional_tag() is not None,
            "coordinate_order_present": self._coordinate_order() is not None,
        }

    def required_metadata(self) -> dict[str, object]:
        template_card = self.template_card()
        return {
            "chart_model_name": template_card.preferred_chart,
            "native_mode_labels": template_card.label_translator_card.native_label_name,
            "parity_flag": template_card.label_translator_card.parity_flag,
            "helicity_flag": template_card.label_translator_card.helicity_flag,
            "branch_flag": template_card.label_translator_card.branch_flag,
            "truncation_metadata": dict(self.truncation),
            "boundary_policy": template_card.collocation_policy.boundary_policy,
            "seed_provenance_mode": self.family_spec.ic_provenance_status,
            "release_status": "backend-contract-complete",
            "h_parameter": self.family_spec.algebra.h_parameter,
            "orthogonal_global_tilt_local_boost_split": self.family_spec.orthogonal_global_tilt_local_boost_split,
            "preferred_backend": self.family_spec.preferred_backend,
            "generic_fallback": self.family_spec.generic_fallback,
            "lookup_resolution_status": template_card.lookup_resolution_status,
            "verification_crosscheck_pass": bool(
                template_card.metadata.get("verification_crosscheck_pass", False)
            ),
            "verification_reference": template_card.metadata.get("verification_reference"),
            "seed_normalization_convention": dict(_FROZEN_SEED_NORMALIZATION),
            "template_card": template_card.as_payload(),
        }


def family_backend_gate_bundle(
    backend: FamilyBackend,
    ops: ModeOps,
) -> GateBundle:
    """Emit the machine-readable PR-08 family-backend gate bundle."""

    template = backend.template_card()
    residuals = backend.backend_residuals()
    return make_gate_bundle(
        "family_backend_gate",
        family=backend.family_spec.family,
        branch=ops.branch,
        backend=backend.family_spec.preferred_backend,
        truncation=dict(backend.truncation),
        residual_summary={
            "translator_roundtrip_residual": (
                -1.0
                if residuals["translator_roundtrip_residual"] is None
                else float(residuals["translator_roundtrip_residual"])
            ),
            "family_specific_residual_count": float(len(template.family_specific_residuals)),
            "must_not_do_count": float(len(template.must_not_do)),
            "lookup_resolution_frozen": float(
                template.lookup_resolution_status == "frozen_v5_formula_set"
            ),
            "verification_crosscheck_pass": float(
                bool(template.metadata.get("verification_crosscheck_pass", False))
            ),
        },
        known_limit_checks={
            "operator_payload_bound": bool(ops.release_status == "backend-operator-bound"),
            "chart_frozen": bool(ops.chart == template.preferred_chart),
            "kernel_family_frozen": bool(ops.operator_kernel_family == template.operator_kernel_family),
            "verification_bundle_pass": bool(
                template.metadata.get("verification_crosscheck_pass", False)
            ),
        },
        forbidden_shortcut_checks={
            "no_local_boost_folded_into_backend": True,
            "translator_layer_present": True,
            "no_hidden_branch_choice": True,
        },
        metadata={
            "template_card": template.as_payload(),
            "layout_metadata": dict(ops.layout_metadata),
            "operator_payload_status": ops.metadata.get("operator_payload_status"),
            "lookup_resolution_status": template.lookup_resolution_status,
            "verification_reference": template.metadata.get("verification_reference"),
        },
        passed=bool(
            ops.release_status == "backend-operator-bound"
            and ops.operator_kernel_family == template.operator_kernel_family
            and template.lookup_resolution_status == "frozen_v5_formula_set"
            and bool(template.metadata.get("verification_crosscheck_pass", False))
        ),
        opened_claim="family backend contract bound to executable operator payload",
    )


def build_backend(
    family_spec: FamilySpec | str,
    truncation: Mapping[str, object],
    chart_options: Mapping[str, object] | None = None,
) -> FamilyBackend:
    """Build the ver3 family backend contract object."""

    spec = get_family_spec(family_spec) if isinstance(family_spec, str) else family_spec
    return FamilyBackend(
        family_spec=spec,
        truncation=dict(truncation),
        chart_options={} if chart_options is None else dict(chart_options),
    )
