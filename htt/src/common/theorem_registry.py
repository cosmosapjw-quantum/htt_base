"""Diagnostic theorem-obligation registry for the REV-R084 program slice."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from common.enum_compat import StrEnum

DEFAULT_THEOREM_CAVEAT = (
    "Theorem entries are synthetic/manufactured verification obligations only; "
    "they are not observational validation, HTT evidence, MIO certificates, "
    "native solver validation, or geometry/family claims."
)


class TheoremStatus(StrEnum):
    ANALYTIC = "analytic"
    CONVENTION_CONDITIONAL = "convention_conditional"
    PROGRAM_THEOREM = "program_theorem"
    OBSERVATIONAL_BLOCKED = "observational_blocked"


class ProofStatus(StrEnum):
    ASSUMPTION_RECORDED = "assumption_recorded"
    CONVENTION_CONDITIONAL = "convention_conditional"
    PROGRAM_OBLIGATION = "program_obligation"
    OBSERVATIONAL_BLOCKED = "observational_blocked"


def _non_empty(value: object, field_name: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _tuple_of_text(values: Sequence[object], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence")
    result = tuple(_non_empty(value, field_name) for value in values)
    if not result:
        raise ValueError(f"{field_name} must contain at least one entry")
    return result


def _status(value: object) -> TheoremStatus:
    try:
        return TheoremStatus(str(value))
    except ValueError as exc:
        allowed = ", ".join(status.value for status in TheoremStatus)
        raise ValueError(f"status must be one of: {allowed}") from exc


def _proof_status(value: object) -> ProofStatus:
    try:
        return ProofStatus(str(value))
    except ValueError as exc:
        allowed = ", ".join(status.value for status in ProofStatus)
        raise ValueError(f"proof_status must be one of: {allowed}") from exc


@dataclass(frozen=True)
class TheoremEntry:
    theorem_id: str
    title: str
    status: str | TheoremStatus
    assumptions: Sequence[str]
    kill_switches: Sequence[str]
    allowed_use: Sequence[str]
    forbidden_use: Sequence[str]
    test_file: str
    generated_artifact_ids: Sequence[str]
    proof_status: str | ProofStatus = ProofStatus.PROGRAM_OBLIGATION
    implementation_test_status: str = "synthetic_manufactured_only"
    claim_status: str = "diagnostic_observational_use_blocked"
    harmonic_convention_status: str = "not_applicable"
    kl_to_temperature_bridge_status: str = "not_applicable"
    owner: str = "COMMON"
    implementation_scope: str = "common"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    production_claim_allowed: bool = False
    observation_claim_allowed: bool = False
    native_solver_result: bool = False
    consumable_as_htt_evidence: bool = False
    consumable_as_mio_certificate: bool = False
    consumable_as_family_identification: bool = False
    caveats: Sequence[str] = field(default_factory=lambda: (DEFAULT_THEOREM_CAVEAT,))

    def __post_init__(self) -> None:
        object.__setattr__(self, "theorem_id", _non_empty(self.theorem_id, "theorem_id"))
        object.__setattr__(self, "title", _non_empty(self.title, "title"))
        object.__setattr__(self, "status", _status(self.status))
        object.__setattr__(self, "proof_status", _proof_status(self.proof_status))
        object.__setattr__(
            self,
            "implementation_test_status",
            _non_empty(self.implementation_test_status, "implementation_test_status"),
        )
        if self.implementation_test_status != "synthetic_manufactured_only":
            raise ValueError("implementation_test_status must remain synthetic_manufactured_only")
        object.__setattr__(self, "claim_status", _non_empty(self.claim_status, "claim_status"))
        if self.claim_status != "diagnostic_observational_use_blocked":
            raise ValueError("claim_status must remain diagnostic_observational_use_blocked")
        for field_name in ("assumptions", "kill_switches", "allowed_use", "forbidden_use", "generated_artifact_ids", "caveats"):
            object.__setattr__(self, field_name, _tuple_of_text(getattr(self, field_name), field_name))
        test_file = _non_empty(self.test_file, "test_file")
        if not test_file.startswith("tests/"):
            raise ValueError("test_file must be a tests/ path")
        object.__setattr__(self, "test_file", test_file)
        object.__setattr__(
            self,
            "harmonic_convention_status",
            _non_empty(self.harmonic_convention_status, "harmonic_convention_status"),
        )
        object.__setattr__(
            self,
            "kl_to_temperature_bridge_status",
            _non_empty(self.kl_to_temperature_bridge_status, "kl_to_temperature_bridge_status"),
        )
        if self.owner != "COMMON":
            raise ValueError("TheoremEntry owner must be COMMON")
        if self.implementation_scope != "common":
            raise ValueError("TheoremEntry implementation_scope must be common")
        if self.claim_tier != "diagnostic_only":
            raise ValueError("TheoremEntry claim_tier must be diagnostic_only")
        if self.transfer_source != "none":
            raise ValueError("TheoremEntry transfer_source must be none")
        if self.native_solver_result:
            raise ValueError("TheoremEntry native_solver_result must be false")
        for field_name in (
            "production_claim_allowed",
            "observation_claim_allowed",
            "consumable_as_htt_evidence",
            "consumable_as_mio_certificate",
            "consumable_as_family_identification",
        ):
            if bool(getattr(self, field_name)):
                raise ValueError(f"TheoremEntry {field_name} must be false")

    def as_payload(self) -> dict[str, Any]:
        return {
            "theorem_id": self.theorem_id,
            "title": self.title,
            "status": self.status.value,
            "proof_status": self.proof_status.value,
            "implementation_test_status": self.implementation_test_status,
            "claim_status": self.claim_status,
            "assumptions": list(self.assumptions),
            "kill_switches": list(self.kill_switches),
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
            "test_file": self.test_file,
            "generated_artifact_ids": list(self.generated_artifact_ids),
            "harmonic_convention_status": self.harmonic_convention_status,
            "kl_to_temperature_bridge_status": self.kl_to_temperature_bridge_status,
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "transfer_source": self.transfer_source,
            "production_claim_allowed": self.production_claim_allowed,
            "observation_claim_allowed": self.observation_claim_allowed,
            "native_solver_result": self.native_solver_result,
            "consumable_as_htt_evidence": self.consumable_as_htt_evidence,
            "consumable_as_mio_certificate": self.consumable_as_mio_certificate,
            "consumable_as_family_identification": self.consumable_as_family_identification,
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class TheoremRegistry:
    entries: tuple[TheoremEntry, ...]

    def __post_init__(self) -> None:
        ids = [entry.theorem_id for entry in self.entries]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate theorem_id in registry")
        object.__setattr__(self, "entries", tuple(sorted(self.entries, key=lambda item: item.theorem_id)))

    def ids(self) -> tuple[str, ...]:
        return tuple(entry.theorem_id for entry in self.entries)

    def all(self) -> tuple[TheoremEntry, ...]:
        return self.entries

    def get(self, theorem_id: str) -> TheoremEntry:
        for entry in self.entries:
            if entry.theorem_id == theorem_id:
                return entry
        raise KeyError(theorem_id)

    def required_kill_switches(self) -> tuple[str, ...]:
        switches = {
            switch for entry in self.entries for switch in entry.kill_switches
        }
        return tuple(sorted(switches))

    def blocked_observational_uses(self) -> dict[str, str]:
        return {
            entry.theorem_id: "synthetic/manufactured verification only; observational use blocked"
            for entry in self.entries
        }

    def to_payload(self) -> list[dict[str, Any]]:
        return [entry.as_payload() for entry in self.entries]


def _entry(
    theorem_id: str,
    title: str,
    status: TheoremStatus,
    proof_status: ProofStatus,
    assumptions: Iterable[str],
    kill_switches: Iterable[str],
    allowed_use: Iterable[str],
    forbidden_use: Iterable[str],
    test_file: str,
    artifacts: Iterable[str],
    *,
    harmonic_convention_status: str = "not_applicable",
    kl_to_temperature_bridge_status: str = "not_applicable",
) -> TheoremEntry:
    return TheoremEntry(
        theorem_id=theorem_id,
        title=title,
        status=status,
        proof_status=proof_status,
        assumptions=tuple(assumptions),
        kill_switches=tuple(kill_switches),
        allowed_use=tuple(allowed_use),
        forbidden_use=tuple(forbidden_use),
        test_file=test_file,
        generated_artifact_ids=tuple(artifacts),
        harmonic_convention_status=harmonic_convention_status,
        kl_to_temperature_bridge_status=kl_to_temperature_bridge_status,
    )


def default_theorem_registry() -> TheoremRegistry:
    return TheoremRegistry(
        (
            _entry(
                "S1",
                "Angular KL multipole bound",
                TheoremStatus.CONVENTION_CONDITIONAL,
                ProofStatus.CONVENTION_CONDITIONAL,
                (
                    "positive angular density fixture",
                    "declared synthetic harmonic normalization",
                    "no observed CMB temperature bridge",
                ),
                (
                    "unbounded_multipole_bridge_blocks_s2_observational_use",
                    "harmonic_convention_not_bound_blocks_kl_bound_use",
                ),
                ("synthetic density multipole smoke checks",),
                ("observed temperature multipole bound", "S2 observational use"),
                "tests/bass/test_boltzmann_memory_bounds.py",
                ("theorem_extension_registry",),
                harmonic_convention_status="declared_synthetic_density_only",
                kl_to_temperature_bridge_status="not_bound",
            ),
            _entry(
                "S3",
                "Dynamic comparison budget barrier",
                TheoremStatus.PROGRAM_THEOREM,
                ProofStatus.PROGRAM_OBLIGATION,
                ("same channel/operator/frame synthetic budget", "positive collision gap"),
                (
                    "collision_gap_nonpositive_blocks_exponential_forgetting_language",
                    "channel_operator_mismatch_blocks_dynamic_budget_certification",
                ),
                ("synthetic dynamic budget barrier checks",),
                ("observational denominator certification", "HTT likelihood evidence"),
                "tests/mio/test_dynamic_budget.py",
                ("theorem_extension_registry",),
            ),
            _entry(
                "S4",
                "Bound-to-Pi domination",
                TheoremStatus.PROGRAM_THEOREM,
                ProofStatus.PROGRAM_OBLIGATION,
                ("samplewise diagnostic bound dominates samples", "Pi is threshold exceedance only"),
                ("samplewise_bound_violation_blocks_pi_domination",),
                ("synthetic exceedance domination checks",),
                ("truth probability", "posterior probability", "HTT evidence"),
                "tests/mio/test_dynamic_budget.py",
                ("theorem_extension_registry",),
            ),
            _entry(
                "S5",
                "Finite-cover bound",
                TheoremStatus.CONVENTION_CONDITIONAL,
                ProofStatus.CONVENTION_CONDITIONAL,
                ("finite synthetic cover", "declared metric/mask/Lipschitz provenance for physical cover use"),
                ("metric_mask_lipschitz_not_bound_blocks_physical_cover_use",),
                ("synthetic finite-cover union checks",),
                ("physical light-cone cover claim without mask and metric provenance",),
                "tests/mio/test_dynamic_budget.py",
                ("theorem_extension_registry",),
            ),
            _entry(
                "G2",
                "Boosted-radiation orbit and almost-EGS gates",
                TheoremStatus.OBSERVATIONAL_BLOCKED,
                ProofStatus.OBSERVATIONAL_BLOCKED,
                (
                    "pure Lorentz boost fixture",
                    "no data-facing residual without full provenance gate stack",
                ),
                (
                    "acceleration_temp_gradient_block_missing_blocks_flrw_egs_promotion",
                    "derivative_weyl_diagnostics_missing_blocks_almost_egs_promotion",
                    "bianchi_i_assumptions_missing_blocks_g4_exact_flow_use",
                    "data_residual_provenance_not_bound_blocks_data_facing_residual",
                ),
                ("synthetic boost-orbit and almost-EGS gate checks",),
                ("intrinsic geometry detection", "family ranking", "data-facing residual claim"),
                "tests/bass/test_egs_rigidity_theorems.py",
                ("theorem_extension_registry",),
            ),
            _entry(
                "G5",
                "Slope degeneracy classification",
                TheoremStatus.OBSERVATIONAL_BLOCKED,
                ProofStatus.OBSERVATIONAL_BLOCKED,
                ("synthetic slope pairs", "equation-of-state singularity guard"),
                (
                    "stiff_fluid_singularity_blocks_g3_inversion",
                    "slope_degeneracy_blocks_slope_only_source_discrimination",
                ),
                ("synthetic slope-degeneracy classification",),
                ("slope-only source discrimination", "local/global origin ranking"),
                "tests/bass/test_egs_rigidity_theorems.py",
                ("theorem_extension_registry",),
            ),
            _entry(
                "B4",
                "Visibility cancellation no-go",
                TheoremStatus.CONVENTION_CONDITIONAL,
                ProofStatus.CONVENTION_CONDITIONAL,
                ("positive kernel fixture", "sign/phase coherent source", "positive collision gap"),
                (
                    "collision_gap_nonpositive_blocks_exponential_forgetting_language",
                    "source_rank_near_zero_blocks_inverse_source_claim",
                    "line_of_sight_sign_phase_incoherence_blocks_source_upper_bound",
                    "visibility_gap_kernel_mask_not_bound_blocks_source_upper_bound",
                ),
                ("synthetic memory and visibility cancellation checks",),
                ("inverse source claim", "observed line-of-sight upper bound"),
                "tests/bass/test_boltzmann_memory_bounds.py",
                ("theorem_extension_registry",),
            ),
        )
    )


def default_theorem_extension_registry() -> TheoremRegistry:
    return default_theorem_registry()
