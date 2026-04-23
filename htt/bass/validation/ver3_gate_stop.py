"""ver3 PR-11 validation gate and fitting hard-stop helpers."""
from __future__ import annotations

from collections.abc import Iterator, Mapping as AbcMapping
from dataclasses import dataclass, field
from typing import Any, Mapping

__all__ = [
    "GATE_LADDER",
    "GateBundle",
    "GateDecision",
    "collect_gate_bundles",
    "make_gate_bundle",
    "summarize_gate_status",
    "hard_gate_before_fitting",
    "score_branch_readiness",
    "family_backend_gate_bundle_from_packs",
]


GATE_LADDER: tuple[str, ...] = (
    "authority_freeze",
    "tensor_helper_correctness",
    "family_registry_freeze",
    "geometry_diagnostics_gate",
    "matter_projection_gate",
    "background_core_gate",
    "exact_thomson_gate",
    "visibility_history_gate",
    "tilt_boost_separation_gate",
    "ic_provenance_gate",
    "family_backend_gate",
    "hierarchy_layout_gate",
    "production_cutoff_gate",
    "output_split_gate",
    "fitting_gate",
)


@dataclass(frozen=True)
class GateBundle:
    """Machine-readable evidence bundle for one opened gate."""

    gate_name: str
    family: str
    branch: str
    backend: str
    truncation: Mapping[str, object]
    residual_summary: Mapping[str, object]
    known_limit_checks: Mapping[str, object]
    forbidden_shortcut_checks: Mapping[str, object]
    metadata: Mapping[str, object]
    passed: bool = True
    opened_claim: str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_LADDER:
            raise ValueError(f"unknown gate_name {self.gate_name!r}")
        for field_name in ("family", "branch", "backend"):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must be non-empty")
        object.__setattr__(self, "truncation", dict(self.truncation))
        object.__setattr__(self, "residual_summary", dict(self.residual_summary))
        object.__setattr__(self, "known_limit_checks", dict(self.known_limit_checks))
        object.__setattr__(
            self,
            "forbidden_shortcut_checks",
            dict(self.forbidden_shortcut_checks),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))
        object.__setattr__(self, "passed", bool(self.passed))

    def as_payload(self) -> dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "family": self.family,
            "branch": self.branch,
            "backend": self.backend,
            "truncation": dict(self.truncation),
            "residual_summary": dict(self.residual_summary),
            "known_limit_checks": dict(self.known_limit_checks),
            "forbidden_shortcut_checks": dict(self.forbidden_shortcut_checks),
            "metadata": dict(self.metadata),
            "passed": bool(self.passed),
            "opened_claim": self.opened_claim,
        }


@dataclass(frozen=True)
class GateDecision(AbcMapping[str, Any]):
    """Machine-readable fitting gate decision with mapping compatibility."""

    gate_name: str
    allowed: bool
    required_gates: tuple[str, ...]
    missing_gates: tuple[str, ...]
    opened_gates: tuple[str, ...]
    gate_status: Mapping[str, str]
    bundle_gates: tuple[str, ...]
    bundle_payloads: Mapping[str, Mapping[str, Any]]
    reason: str
    residuals: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_status", dict(self.gate_status))
        object.__setattr__(self, "bundle_payloads", dict(self.bundle_payloads))
        object.__setattr__(self, "residuals", dict(self.residuals))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def as_payload(self) -> dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "allowed": bool(self.allowed),
            "required_gates": tuple(self.required_gates),
            "missing_gates": tuple(self.missing_gates),
            "opened_gates": tuple(self.opened_gates),
            "gate_status": dict(self.gate_status),
            "bundle_gates": tuple(self.bundle_gates),
            "bundle_payloads": dict(self.bundle_payloads),
            "reason": self.reason,
            "residuals": dict(self.residuals),
            "metadata": dict(self.metadata),
        }

    def __getitem__(self, key: str) -> Any:
        return self.as_payload()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.as_payload())

    def __len__(self) -> int:
        return len(self.as_payload())


_BUNDLE_KEYS = frozenset(
    {
        "gate_name",
        "family",
        "branch",
        "backend",
        "truncation",
        "residual_summary",
        "known_limit_checks",
        "forbidden_shortcut_checks",
        "metadata",
        "passed",
        "opened_claim",
    }
)


def make_gate_bundle(
    gate_name: str,
    *,
    family: str,
    branch: str,
    backend: str,
    truncation: Mapping[str, object],
    residual_summary: Mapping[str, object],
    known_limit_checks: Mapping[str, object],
    forbidden_shortcut_checks: Mapping[str, object],
    metadata: Mapping[str, object],
    passed: bool = True,
    opened_claim: str | None = None,
) -> GateBundle:
    return GateBundle(
        gate_name=gate_name,
        family=family,
        branch=branch,
        backend=backend,
        truncation=truncation,
        residual_summary=residual_summary,
        known_limit_checks=known_limit_checks,
        forbidden_shortcut_checks=forbidden_shortcut_checks,
        metadata=metadata,
        passed=passed,
        opened_claim=opened_claim,
    )


def _looks_like_bundle_payload(value: object) -> bool:
    return isinstance(value, Mapping) and any(key in value for key in _BUNDLE_KEYS)


def _coerce_gate_bundle(gate_name: str, value: object) -> GateBundle | None:
    if value is None or value is False:
        return None
    if isinstance(value, GateBundle):
        if value.gate_name != gate_name:
            raise ValueError(
                f"bundle gate_name {value.gate_name!r} does not match registry key {gate_name!r}"
            )
        return value
    if not _looks_like_bundle_payload(value):
        return None
    assert isinstance(value, Mapping)
    payload_gate = str(value.get("gate_name", gate_name))
    if payload_gate != gate_name:
        raise ValueError(
            f"bundle gate_name {payload_gate!r} does not match registry key {gate_name!r}"
        )
    return make_gate_bundle(
        payload_gate,
        family=str(value["family"]),
        branch=str(value["branch"]),
        backend=str(value["backend"]),
        truncation=dict(value.get("truncation", {})),
        residual_summary=dict(value.get("residual_summary", {})),
        known_limit_checks=dict(value.get("known_limit_checks", {})),
        forbidden_shortcut_checks=dict(value.get("forbidden_shortcut_checks", {})),
        metadata=dict(value.get("metadata", {})),
        passed=bool(value.get("passed", True)),
        opened_claim=(
            None if value.get("opened_claim") is None else str(value["opened_claim"])
        ),
    )


def collect_gate_bundles(gates: Mapping[str, object]) -> dict[str, GateBundle]:
    """Return the explicit machine-readable bundles present in a gate registry."""

    bundles: dict[str, GateBundle] = {}
    for gate in GATE_LADDER:
        bundle = _coerce_gate_bundle(gate, gates.get(gate))
        if bundle is not None:
            bundles[gate] = bundle
    return bundles


def _gate_map(gates: Mapping[str, object]) -> dict[str, bool]:
    bundles = collect_gate_bundles(gates)
    out: dict[str, bool] = {}
    for gate in GATE_LADDER:
        if gate in bundles:
            out[gate] = bool(bundles[gate].passed)
            continue
        out[gate] = bool(gates.get(gate, False))
    return out


def summarize_gate_status(gates: Mapping[str, object]) -> dict[str, str]:
    """Summarize the gate ladder as open/closed/unavailable."""

    gate_map = _gate_map(gates)
    out: dict[str, str] = {}
    lower_gate_closed = False
    for gate in GATE_LADDER:
        if lower_gate_closed:
            out[gate] = "unavailable"
            continue
        if gate_map[gate]:
            out[gate] = "open"
            continue
        out[gate] = "closed"
        lower_gate_closed = True
    return out


def hard_gate_before_fitting(
    gates: Mapping[str, object],
    residuals: Mapping[str, object] | None = None,
    metadata: Mapping[str, object] | None = None,
) -> GateDecision:
    """Return a machine-readable fitting hard-stop report."""
    gate_map = _gate_map(gates)
    gate_status = summarize_gate_status(gates)
    bundles = collect_gate_bundles(gates)
    required = GATE_LADDER[:-1]
    missing = tuple(gate for gate in required if not gate_map[gate])
    allowed = len(missing) == 0
    return GateDecision(
        gate_name="fitting_hard_stop",
        allowed=allowed,
        required_gates=required,
        missing_gates=missing,
        opened_gates=tuple(gate for gate, state in gate_map.items() if state),
        gate_status=gate_status,
        bundle_gates=tuple(gate for gate in GATE_LADDER if gate in bundles),
        bundle_payloads={
            gate: bundles[gate].as_payload() for gate in GATE_LADDER if gate in bundles
        },
        reason=(
            "all upstream gates open; fitting may evaluate"
            if allowed
            else "upstream gates missing; fitting prohibited"
        ),
        residuals={} if residuals is None else dict(residuals),
        metadata={} if metadata is None else dict(metadata),
    )


def score_branch_readiness(gates: Mapping[str, object]) -> int:
    """Map consecutive opened gates onto the ver3 readiness scoreboard."""
    gate_map = _gate_map(gates)
    consecutive = 0
    for gate in GATE_LADDER:
        if not gate_map[gate]:
            break
        consecutive += 1
    if consecutive == 0:
        return 0
    if consecutive <= 3:
        return 4
    if consecutive <= 10:
        return 6
    if consecutive <= len(GATE_LADDER) - 1:
        return 8
    return 10


def family_backend_gate_bundle_from_packs(
    family_residual_packs: Mapping[str, Any],
    *,
    gate_name: str = "family_backend_gate",
) -> GateBundle:
    """Build a ``family_backend_gate`` evidence bundle from per-family packs.

    Given the mapping returned by
    ``bass.los.families.residual_report.build_family_residual_packs``,
    collapse it into the single ``GateBundle`` shape consumed by
    ``hard_gate_before_fitting``.

    The bundle ``passed`` is the logical AND of every pack's ``passed``,
    plus a requirement that every family in ``KNOWN_FAMILIES`` is
    present. Missing families drive ``passed = False`` with their names
    recorded in ``metadata['missing_families']``.

    Parameters
    ----------
    family_residual_packs
        Mapping ``{family: ResidualPack | dict}``. If an entry has an
        ``as_payload()`` method it is called; otherwise the entry is
        treated as an already-serialized payload dict.

    Returns
    -------
    GateBundle
        Ready to drop into a ``gate_registry`` under the
        ``family_backend_gate`` key.
    """
    from bass.los.families import KNOWN_FAMILIES

    payload_by_family: dict[str, Mapping[str, Any]] = {}
    for family, pack in family_residual_packs.items():
        if hasattr(pack, "as_payload"):
            payload_by_family[family] = pack.as_payload()
        else:
            payload_by_family[family] = dict(pack)

    missing = tuple(sorted(set(KNOWN_FAMILIES) - set(payload_by_family)))
    all_passed = bool(payload_by_family) and all(
        bool(entry.get("passed", False)) for entry in payload_by_family.values()
    )
    passed = all_passed and not missing

    # Aggregate residual/shortcut evidence across families.
    aggregated_residuals: dict[str, object] = {}
    aggregated_shortcuts: dict[str, object] = {}
    for family, entry in payload_by_family.items():
        for label, value in entry.get("residual_values", {}).items():
            aggregated_residuals[f"{family}:{label}"] = value
        violations = entry.get("forbidden_shortcut_violations", [])
        if violations:
            aggregated_shortcuts[family] = list(violations)

    return make_gate_bundle(
        gate_name,
        family="+".join(sorted(payload_by_family)) or "unspecified",
        branch="aggregated_family_backend",
        backend="bass.los.families.residual_report",
        truncation={family: entry.get("metadata", {}).get("truncation_xi_max")
                    or entry.get("metadata", {}).get("truncation_half_width")
                    or entry.get("metadata", {}).get("radial_cutoff_R")
                    for family, entry in payload_by_family.items()},
        residual_summary=aggregated_residuals,
        known_limit_checks={
            family: entry.get("verification_crosscheck_pass", False)
            for family, entry in payload_by_family.items()
        },
        forbidden_shortcut_checks=aggregated_shortcuts,
        metadata={
            "family_count": len(payload_by_family),
            "missing_families": list(missing),
            "all_passed": all_passed,
            "per_family_passed": {
                family: bool(entry.get("passed", False))
                for family, entry in payload_by_family.items()
            },
        },
        passed=passed,
        opened_claim=(
            "all 11 families produced passing ResidualPacks"
            if passed
            else "family_backend_gate requires every KNOWN_FAMILIES pack to pass"
        ),
    )
