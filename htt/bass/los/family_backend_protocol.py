"""ver3 PR-08 family backend protocol for BASS LOS / backend ownership.

This module freezes backend-contract surfaces only. It does not claim that
all family-specific numerics are implemented; it records the backend,
translator, and seed provenance contract in machine-readable form.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from bass.background.bianchi_types import FamilySpec, get_family_spec

__all__ = [
    "NativeLabelCard",
    "SeedRequest",
    "SeedPack",
    "ModeOps",
    "FamilyBackend",
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
        family = self.family_spec.family
        return {
            "native_label_name": _NATIVE_LABELS[family],
            "parity_flag": None,
            "helicity_flag": None,
            "branch_flag": self._branch_flag(),
            "h_parameter": self.family_spec.algebra.h_parameter,
            "directional_tag": self._directional_tag(),
            "coordinate_order": self._coordinate_order(),
            "chart": self._chart(),
        }

    def operator_factory(self, background_state: Mapping[str, object]) -> ModeOps:
        branch = str(background_state.get("branch", "orthogonal"))
        if branch not in {"orthogonal", "tilted"}:
            raise ValueError(f"unknown branch {branch!r}")
        if not self.family_spec.algebra.supports_branch(branch):
            raise ValueError(f"{self.family_spec.family} does not support branch {branch!r}")
        metadata = {
            "family": self.family_spec.family,
            "class_label": self.family_spec.class_label,
            "isotropic_anchor": self.family_spec.isotropic_anchor,
            "orthogonal_global_tilt_local_boost_split": self.family_spec.orthogonal_global_tilt_local_boost_split,
            "constraint_policy_required": self.family_spec.algebra.branch_policy.constraint_policy_required,
            "h_parameter": self.family_spec.algebra.h_parameter,
            "background_state_tag": background_state.get("state_tag", "background_state"),
        }
        return ModeOps(
            family=self.family_spec.family,
            branch=branch,
            chart=self._chart(),
            backend_name=self.family_spec.preferred_backend,
            operator_kernel_family=_OPERATOR_KERNELS[self.family_spec.family],
            truncation=dict(self.truncation),
            boundary_policy=str(self.chart_options.get("boundary_policy", _BOUNDARY_POLICIES[self.family_spec.family])),
            seed_provenance_mode="isotropic_anchor_continuation"
            if self.family_spec.ic_provenance_status == "strong"
            else "template_card_family_adapted",
            release_status="backend-contract-complete",
            metadata=metadata,
        )

    def seed_factory(self, seed_request: SeedRequest) -> SeedPack:
        allowed = _SEED_MODES[self.family_spec.family]
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
            "amp_ref": float(seed_request.amplitude_reference),
            "chart": self._chart(),
        }
        residual_summary = {
            "seed_regularity_status": "not_executed",
            "translator_roundtrip_status": "required",
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
        return {
            "chart_model_name": self._chart(),
            "native_mode_labels": _NATIVE_LABELS[self.family_spec.family],
            "parity_flag": None,
            "helicity_flag": None,
            "branch_flag": self._branch_flag(),
            "truncation_metadata": dict(self.truncation),
            "boundary_policy": str(self.chart_options.get("boundary_policy", _BOUNDARY_POLICIES[self.family_spec.family])),
            "seed_provenance_mode": self.family_spec.ic_provenance_status,
            "release_status": "backend-contract-complete",
            "h_parameter": self.family_spec.algebra.h_parameter,
            "orthogonal_global_tilt_local_boost_split": self.family_spec.orthogonal_global_tilt_local_boost_split,
            "preferred_backend": self.family_spec.preferred_backend,
            "generic_fallback": self.family_spec.generic_fallback,
        }


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
