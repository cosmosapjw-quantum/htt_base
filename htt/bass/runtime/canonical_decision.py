"""
bass/runtime/canonical_decision.py  (Week 3 Day 1, merged v4.1)
===============================================================

Single owner of allow/block verdicts across bass-py. Per
`CANONICAL_DECISION_DESIGN.md` §1 and execution plan v3 §7 A1, every downstream
consumer that needs to know "is this mode/species/timestep usable?" routes the
question through `make_canonical_decision(...)`.

No alternative validation path is sanctioned. Callers that implement their own
ad-hoc `allow/block` logic constitute a P0 ownership violation — caught by
`test_ownership_freeze.py` at W3D5.

This module's three inputs (design spec §2):
  - `beta_policy_pass`          — VT-07 frame-attribution-corrected safe route
  - `sigma_min_above_floor`     — Sobolev validity floor on Σ²
  - `source_Dge2_gate_pass`     — Paper I Teff chart faithfulness (tangency)

On D1 the first two are accepted as pre-computed `(bool, dict)` tuples; their
production gate functions (`beta_policy_gate`, `sigma_min_gate`) land at D2.
The third gate (`source_Dge2_gate`) is implemented here because its dependency
(`TangencyResult` from W2D3) is already available.

Spec version contract: `SPEC_VERSION = "v1.0-w3d1"`. A mismatch at construction
raises. W6 entry may bump to v1.1 after a formal re-audit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, FrozenSet, Mapping, Optional, Tuple

# Import from current (pre-freeze) location. After W3D5 freeze commit:
#   from tsc.diagnostics.tangency import TangencyResult
from tsc.diagnostics.tangency import TangencyResult

from bass.runtime.validation_labels import ValidationLabel, derive_labels


# ============================================================================
# Section 1 - Version pin
# ============================================================================

SPEC_VERSION: str = "v1.0-w3d1"
"""Contract version pin. Bump on any shape change to CanonicalDecision."""


# ============================================================================
# Section 2 - Exception type
# ============================================================================

class CanonicalBlockError(RuntimeError):
    """Raised by consumers when `allow_reduction=False` blocks a step.

    Consumers raise this so that callers up the stack can catch a single
    exception type rather than multi-branch on bool returns. The
    `decision` attribute carries the full `CanonicalDecision` for logging.
    """

    def __init__(
        self, message: str, decision: "CanonicalDecision"
    ) -> None:
        super().__init__(message)
        self.decision = decision


# ============================================================================
# Section 3 - CanonicalDecision dataclass (frozen, version-pinned)
# ============================================================================

def _freeze_diagnostics(
    diagnostics: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Return a read-only view of the diagnostics dict tree.

    We do *not* deep-copy — the intent is only to prevent accidental top-level
    mutation. Nested mutable objects are still mutable by anyone who already
    holds a reference; tests assert only the top-level contract.
    """
    return MappingProxyType(dict(diagnostics))


@dataclass(frozen=True)
class CanonicalDecision:
    """Single allow/block verdict owner.

    Constructors other than `make_canonical_decision` are allowed only in
    tests; see `test_canonical_decision.py::test_factory_is_canonical_path`
    for the enforcing check.

    Attributes
    ----------
    spec_version : str
        Must equal `SPEC_VERSION` at construction time.
    beta_policy_pass : bool
        VT-07 safe-route outcome.
    sigma_min_above_floor : bool
        Sobolev validity check on Σ².
    source_Dge2_gate_pass : bool
        Paper I Teff chart faithfulness (`TangencyResult.is_tangent`).
    allow_reduction : bool
        Equals AND of the three pass bools. No other logic.
    emitted_labels : frozenset[ValidationLabel]
        Derived deterministically from the three pass bools + diagnostics.
    diagnostics : Mapping[str, Any]
        Read-only wrapper of per-input diagnostic dicts.

    Post-init enforces:
      * spec_version == SPEC_VERSION
      * allow_reduction == AND(three gates)
      * emitted_labels is a frozenset (and matches `derive_labels` output)
    """
    spec_version: str
    beta_policy_pass: bool
    sigma_min_above_floor: bool
    source_Dge2_gate_pass: bool
    allow_reduction: bool
    emitted_labels: FrozenSet[ValidationLabel]
    diagnostics: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.spec_version != SPEC_VERSION:
            raise ValueError(
                f"spec_version mismatch: got {self.spec_version!r}, "
                f"expected {SPEC_VERSION!r}"
            )

        expected_allow = (
            self.beta_policy_pass
            and self.sigma_min_above_floor
            and self.source_Dge2_gate_pass
        )
        if self.allow_reduction != expected_allow:
            raise ValueError(
                f"allow_reduction must equal AND(three gates): "
                f"got {self.allow_reduction}, expected {expected_allow}"
            )

        if not isinstance(self.emitted_labels, frozenset):
            raise TypeError(
                f"emitted_labels must be a frozenset of ValidationLabel, "
                f"got {type(self.emitted_labels).__name__}"
            )
        for label in self.emitted_labels:
            if not isinstance(label, ValidationLabel):
                raise TypeError(
                    f"emitted_labels contains non-ValidationLabel entry: "
                    f"{label!r}"
                )

        # Labels must match the deterministic derivation from the three bools
        # + diagnostics. This catches manual label injection.
        expected_labels = derive_labels(
            self.beta_policy_pass,
            self.sigma_min_above_floor,
            self.source_Dge2_gate_pass,
            self.diagnostics,
        )
        if self.emitted_labels != expected_labels:
            raise ValueError(
                f"emitted_labels inconsistent with derive_labels: "
                f"got {set(self.emitted_labels)}, "
                f"expected {set(expected_labels)}"
            )


# ============================================================================
# Section 4 - source_Dge2 gate wrapper
# ============================================================================

def source_Dge2_gate(
    tangency_result: TangencyResult,
) -> Tuple[bool, dict]:
    """Wrap `TangencyResult.is_tangent` as a gate.

    The Paper I Teff chart is faithful iff the tangency residual
    `relative_residual < 1e-6` (W2D3 established threshold). This wrapper is
    a ~10-line adapter so that `make_canonical_decision` never touches the
    `TangencyResult` object directly.

    Parameters
    ----------
    tangency_result : TangencyResult
        Output of `tangency.compute_D_diagnostic(...)`.

    Returns
    -------
    (passed, diagnostics) : tuple[bool, dict]
        * `passed` : the `is_tangent` verdict.
        * `diagnostics` : flat dict with the three numbers consumers need.
    """
    diagnostics = {
        "D": float(tangency_result.D),
        "relative_residual": float(tangency_result.relative_residual),
        "fraction_on_manifold": float(tangency_result.fraction_on_manifold),
    }
    return bool(tangency_result.is_tangent), diagnostics


# ============================================================================
# Section 5 - Factory
# ============================================================================

def make_canonical_decision(
    beta_result: Tuple[bool, dict],
    sigma_result: Tuple[bool, dict],
    tangency_result: TangencyResult,
) -> CanonicalDecision:
    """Sole sanctioned construction path for `CanonicalDecision`.

    Parameters
    ----------
    beta_result : (bool, dict)
        Output of `beta_policy_gate(...)`. On D1 this can come from a manual
        call or a stub; on D2 the gate function lands in `baryon_only_policy`.
    sigma_result : (bool, dict)
        Output of `sigma_min_gate(...)`. On D1 this is manual / stubbed;
        D2 introduces `bass/runtime/sigma_floor.py`.
    tangency_result : TangencyResult
        Output of `tangency.compute_D_diagnostic(...)`. Unwrapped here via
        `source_Dge2_gate`.

    Returns
    -------
    CanonicalDecision
        Immutable, version-pinned, labels already derived.

    Raises
    ------
    TypeError
        Input shapes are wrong.
    ValueError
        Input dicts carry nonsensical bool/float fields.
    """
    beta_pass, beta_diag = _unpack_gate_result(beta_result, "beta")
    sigma_pass, sigma_diag = _unpack_gate_result(sigma_result, "sigma")
    source_pass, source_diag = source_Dge2_gate(tangency_result)

    diagnostics = {
        "beta": beta_diag,
        "sigma": sigma_diag,
        "source": source_diag,
    }

    labels = derive_labels(
        beta_policy_pass=beta_pass,
        sigma_min_above_floor=sigma_pass,
        source_Dge2_gate_pass=source_pass,
        diagnostics=diagnostics,
    )

    return CanonicalDecision(
        spec_version=SPEC_VERSION,
        beta_policy_pass=beta_pass,
        sigma_min_above_floor=sigma_pass,
        source_Dge2_gate_pass=source_pass,
        allow_reduction=(beta_pass and sigma_pass and source_pass),
        emitted_labels=labels,
        diagnostics=_freeze_diagnostics(diagnostics),
    )


def _unpack_gate_result(
    result: Tuple[bool, dict],
    label: str,
) -> Tuple[bool, dict]:
    """Validate shape of a `(bool, dict)` gate tuple and pass through."""
    if not isinstance(result, tuple) or len(result) != 2:
        raise TypeError(
            f"{label}_result must be a (bool, dict) tuple, got "
            f"{type(result).__name__}"
        )
    passed, diag = result
    if not isinstance(passed, bool):
        raise TypeError(
            f"{label}_result[0] must be bool, got {type(passed).__name__}"
        )
    if not isinstance(diag, dict):
        raise TypeError(
            f"{label}_result[1] must be dict, got {type(diag).__name__}"
        )
    return passed, diag


# ============================================================================
# Section 6 - Consumer convenience
# ============================================================================

def require_allow_reduction(
    decision: CanonicalDecision,
    context: Optional[str] = None,
) -> None:
    """Raise `CanonicalBlockError` if the decision disallows reduction.

    Consumers call this at the entry of any code path that assumes the
    reduction is valid. The error's `decision` attribute carries full
    diagnostics for logging.
    """
    if not decision.allow_reduction:
        msg = "canonical decision blocks reduction"
        if context:
            msg = f"{context}: {msg}"
        raise CanonicalBlockError(msg, decision)
