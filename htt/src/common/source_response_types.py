"""PR-133 source-response type system + non-bridge semantic guard.

Separates the pre-solver quantities into DISTINCT types with no
automatic coercion:

- ``observer_proxy`` (A_v): linear kinematic bulk-flow proxy, O(beta),
  ell = 1 — NOT physical;
- ``physical_tilt`` (Omega_tilt): physical peculiar-velocity tilt,
  O(beta), ell = 1;
- ``vorticity`` (W2), ``shear`` (Sigma), ``curvature``
  (Delta_Omega_k), ``background_geometry`` — physical.

A_v and Omega_tilt are distinct even though both are O(beta) in the
ell = 1 channel; the A_v -> Omega_tilt bridge is refused unless a
registered source-response equivalence edge with evidence exists
(non-bridge semantic guard). The harmonic boost is order-counted
exactly (A_v at O(beta), the kinematic quadrupole it deposits at
O(beta^2), ell = 2), the deprojection Sigma_tilde^2 = Sigma^2 -
alpha (Omega_tilt)^2 is verified ONLY as a synthetic local-boost
estimator property (false-positive removal, never a shear detection),
every candidate carries the HIGHEST rung it reaches on the ladder
algebraic_witness -> constraint_admissible -> local_dynamics_admissible
-> global_dynamics_admissible (no auto-promotion), and the response
graph keeps the ANALYTIC rank distinct from the observed rank — a
window collinearity surfaces the aligned-axis rank-1 exception
explicitly. A non-removed boost or a rank-deficient response yields
``non_identified``.

Pre-solver discrimination diagnostic only — no Bianchi family, global
tilt, or geometry is measured from any scalar value.
roadmap_rescue_v1:C2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from pathlib import Path
from typing import Mapping, Sequence

import sympy as sp

from common.graded_nonid import (
    EXPECTED_KERNEL_BASIS,
    EXPECTED_RANK,
    RESPONSE_ROWS,
    SECTORS,
)

SCHEMA_VERSION = "pr133.source_response_types.v1"

_REPO_ROOT = Path(__file__).resolve().parents[3]


class SourceResponseError(ValueError):
    """Raised on any type-firewall / ladder / graph violation."""


class NonIdentifiedError(SourceResponseError):
    """The fail-closed discrimination verdict."""


class QuantityType(str, Enum):
    OBSERVER_PROXY = "observer_proxy"        # A_v (kinematic, not physical)
    PHYSICAL_TILT = "physical_tilt"          # Omega_tilt
    VORTICITY = "vorticity"                  # W2
    SHEAR = "shear"                          # Sigma
    CURVATURE = "curvature"                  # Delta_Omega_k
    BACKGROUND_GEOMETRY = "background_geometry"


_TYPE_META = {
    QuantityType.OBSERVER_PROXY: {"symbol": "A_v", "order_in_beta": 1,
                                  "harmonic_channel": 1,
                                  "physical": False},
    QuantityType.PHYSICAL_TILT: {"symbol": "Omega_tilt",
                                 "order_in_beta": 1,
                                 "harmonic_channel": 1, "physical": True},
    QuantityType.VORTICITY: {"symbol": "W2", "order_in_beta": None,
                             "harmonic_channel": None, "physical": True},
    QuantityType.SHEAR: {"symbol": "Sigma", "order_in_beta": None,
                         "harmonic_channel": 2, "physical": True},
    QuantityType.CURVATURE: {"symbol": "Delta_Omega_k",
                             "order_in_beta": None,
                             "harmonic_channel": None, "physical": True},
    QuantityType.BACKGROUND_GEOMETRY: {"symbol": "geometry",
                                       "order_in_beta": None,
                                       "harmonic_channel": None,
                                       "physical": True},
}


@dataclass(frozen=True)
class TypedQuantity:
    """A value tagged with its source-response type AND its provenance.
    Cross-type arithmetic and ordering raise; same-type arithmetic
    returns a same-type quantity.

    SCOPE NOTE: Python cannot forbid a caller from directly
    constructing ``TypedQuantity(PHYSICAL_TILT, x)`` — that asserts a
    NEW physical_tilt value, it does not "bridge" a proxy. The firewall
    therefore enforces two things the type system CAN enforce: (1) no
    implicit cross-type arithmetic/ordering, and (2) a bridged value
    carries a ``bridged:<edge>`` provenance so a physical quantity
    claimed to descend from a proxy is auditable via
    ``require_declared_provenance``."""

    qtype: QuantityType
    value: Fraction
    provenance: str = "declared"

    def __post_init__(self) -> None:
        if not isinstance(self.qtype, QuantityType):
            raise SourceResponseError("qtype must be a QuantityType")
        object.__setattr__(self, "value", Fraction(self.value))
        if not str(self.provenance).strip():
            raise SourceResponseError("provenance must be non-empty")

    @property
    def symbol(self) -> str:
        return _TYPE_META[self.qtype]["symbol"]

    def _require_same(self, other: "TypedQuantity", op: str) -> None:
        if not isinstance(other, TypedQuantity):
            raise SourceResponseError(
                f"typed-quantity {op} needs another TypedQuantity")
        if other.qtype is not self.qtype:
            raise SourceResponseError(
                f"cross-type {op} refused: {self.qtype.value} vs "
                f"{other.qtype.value} — the type firewall blocks "
                "implicit coercion (route through a registered typed "
                "operation instead)")

    def _combined_provenance(self, other: "TypedQuantity") -> str:
        if self.provenance == other.provenance:
            return self.provenance
        if self.provenance == "declared":
            return other.provenance
        if other.provenance == "declared":
            return self.provenance
        raise SourceResponseError(
            "same-type arithmetic cannot combine different non-declared "
            "provenance references"
        )

    def __add__(self, other: "TypedQuantity") -> "TypedQuantity":
        self._require_same(other, "arithmetic")
        return TypedQuantity(
            self.qtype,
            self.value + other.value,
            provenance=self._combined_provenance(other),
        )

    def __sub__(self, other: "TypedQuantity") -> "TypedQuantity":
        self._require_same(other, "arithmetic")
        return TypedQuantity(
            self.qtype,
            self.value - other.value,
            provenance=self._combined_provenance(other),
        )

    def __lt__(self, other: "TypedQuantity") -> bool:
        self._require_same(other, "ordering")
        return self.value < other.value

    def __le__(self, other: "TypedQuantity") -> bool:
        self._require_same(other, "ordering")
        return self.value <= other.value

    def __gt__(self, other: "TypedQuantity") -> bool:
        self._require_same(other, "ordering")
        return self.value > other.value

    def __ge__(self, other: "TypedQuantity") -> bool:
        self._require_same(other, "ordering")
        return self.value >= other.value


# ---------------------------------------------------------------------------
# Non-bridge semantic guard
# ---------------------------------------------------------------------------

# Registered source-response equivalence edges. EMPTY: no A_v ->
# Omega_tilt bridge is authorized. An edge would require a reviewed
# equivalence proof; the registry stays empty at the pre-solver tier.
EQUIVALENCE_EDGES: dict[tuple[QuantityType, QuantityType], dict] = {}


def bridge(source: TypedQuantity, target_type: QuantityType,
           edge_reference: str | None = None) -> TypedQuantity:
    """Convert one typed quantity into another ONLY across a registered
    equivalence edge with an evidence pointer. The A_v -> Omega_tilt
    bridge is refused while the registry is empty. A successful bridge
    stamps a ``bridged:<edge>`` provenance so the result is auditable."""
    key = (source.qtype, target_type)
    edge = EQUIVALENCE_EDGES.get(key)
    if edge is None or not edge_reference or \
            edge.get("evidence") != edge_reference:
        raise SourceResponseError(
            f"bridge {source.qtype.value} -> {target_type.value} refused: "
            "no registered source-response equivalence edge with matching "
            "evidence (the observer proxy is never auto-identified with "
            "the physical tilt)")
    return TypedQuantity(target_type, source.value,
                         provenance=f"bridged:{edge_reference}")


def require_declared_provenance(quantity: TypedQuantity) -> None:
    """A physical quantity must carry a ``declared`` or a sanctioned
    ``bridged:<registered-edge>`` provenance. A value smuggled across
    types by direct reconstruction (which no type system can prevent)
    is caught HERE when its provenance names an unregistered bridge."""
    prov = str(quantity.provenance)
    if prov == "declared":
        return
    if prov.startswith("bridged:"):
        ref = prov.split(":", 1)[1]
        if any(edge.get("evidence") == ref
               for edge in EQUIVALENCE_EDGES.values()):
            return
    raise SourceResponseError(
        f"quantity {quantity.qtype.value} carries an unsanctioned "
        f"provenance {prov!r} — only 'declared' or a registered "
        "equivalence-edge bridge is admissible")


# ---------------------------------------------------------------------------
# Harmonic boost order counting (symbolic)
# ---------------------------------------------------------------------------

def legendre_p2(x):
    return (3 * x ** 2 - 1) / 2


def _pure_monomial_order(expr, beta) -> int:
    """The EXACT order of a coefficient that must be a pure beta^n
    monomial: reject any lower-order contamination (a beta^0 or other
    lower term). Returns n only if the polynomial has a single nonzero
    term at degree n; otherwise raises."""
    poly = sp.Poly(sp.expand(expr), beta)
    terms = [(monom[0], coeff) for monom, coeff in poly.terms()
             if coeff != 0]
    if len(terms) != 1:
        raise SourceResponseError(
            f"coefficient {sp.sstr(expr)} is not a pure beta monomial "
            f"(terms at degrees {[t[0] for t in terms]}) — lower-order "
            "contamination is rejected")
    return int(terms[0][0])


def harmonic_order_counting() -> dict:
    """Verify symbolically that the linear boost A_v enters the dipole
    at O(beta) and the kinematic quadrupole it deposits (the boost of a
    PURE MONOPOLE) enters at O(beta^2). The monopole T0 boosted by a
    velocity beta*mu carries angular power (1 + beta mu)^k; the mu^2
    term reduces via mu^2 = (2/3) P2(mu) + 1/3, so the P2 (ell = 2)
    coefficient is a pure O(beta^2) monomial. The order check demands a
    PURE monomial (no lower-order contamination), not merely a
    max-degree.

    Cross-reference (doppler_boost.py, ell = 2 returns
    (4/5) e2 beta + e1^2): the e1^2 term IS this monopole -> quadrupole
    O(beta^2) channel (e1 is the dipole ~ beta), while the (4/5) e2 beta
    term is the SEPARATE aberration of a pre-existing background
    quadrupole e2 and is a DIFFERENT channel (linear in beta only
    because a rest-frame quadrupole already exists). This toy models the
    pure-monopole kinematic-quadrupole channel (e2 = 0)."""
    beta, mu = sp.symbols("beta mu")
    # aberration/Doppler modulation of a PURE MONOPOLE to second order
    modulation = sp.expand((1 + beta * mu) ** 2)   # 1 + 2 beta mu + beta^2 mu^2
    dipole = modulation.coeff(mu, 1)
    mu2_coeff = modulation.coeff(mu, 2)
    p2_coefficient = sp.expand(mu2_coeff * sp.Rational(2, 3))
    dipole_order = _pure_monomial_order(dipole, beta)
    quad_order = _pure_monomial_order(p2_coefficient, beta)
    if dipole_order != 1:
        raise SourceResponseError(
            f"dipole boost order {dipole_order} != 1 (expected O(beta))")
    if quad_order != 2:
        raise SourceResponseError(
            f"kinematic quadrupole order {quad_order} != 2 "
            "(expected O(beta^2))")
    return {
        "dipole_coeff": sp.sstr(dipole),
        "quadrupole_P2_coeff": sp.sstr(p2_coefficient),
        "A_v_order_in_beta": 1,
        "kinematic_quadrupole_order_in_beta": 2,
        "mu2_identity": "mu^2 = (2/3) P2(mu) + 1/3",
        "doppler_crossref": "e1^2 term in doppler_boost.py ell=2 is this "
                            "O(beta^2) monopole->quadrupole channel; the "
                            "(4/5) e2 beta term is a separate pre-existing"
                            "-quadrupole aberration channel",
    }


def require_beta_order(quantity: str, claimed_order: int) -> None:
    """Kill a wrong beta-order declaration against the symbolic count."""
    counting = harmonic_order_counting()
    truth = {
        "A_v": counting["A_v_order_in_beta"],
        "kinematic_quadrupole":
            counting["kinematic_quadrupole_order_in_beta"],
    }
    if quantity not in truth:
        raise SourceResponseError(f"unknown boost quantity {quantity!r}")
    if claimed_order != truth[quantity]:
        raise SourceResponseError(
            f"{quantity} declared at O(beta^{claimed_order}) but the "
            f"symbolic order counting gives O(beta^{truth[quantity]})")


# ---------------------------------------------------------------------------
# Synthetic deprojection estimator property
# ---------------------------------------------------------------------------

def deprojected_shear(sigma2_naive: Fraction, omega_tilt: Fraction,
                      alpha: Fraction = Fraction(1)) -> Fraction:
    """Sigma_tilde^2 = Sigma^2 - alpha (Omega_tilt)^2 (registered
    alpha = 1). Kinematic constants folded into alpha."""
    return Fraction(sigma2_naive) - Fraction(alpha) * Fraction(
        omega_tilt) ** 2


def deprojection_estimator_property(alpha: Fraction = Fraction(1),
                                    ) -> dict:
    """Synthetic local-boost estimator property (NOT a detection, and
    ALGEBRAICALLY EXACT BY CONSTRUCTION — the pure-boost sky is defined
    as Sigma^2_naive = alpha (Omega_tilt)^2 and then subtracted, so the
    zero is a tautology that ILLUSTRATES the estimator's false-positive
    removal, not an independently falsifiable measurement):

    - pure-local-boost sky (Sigma^2_naive = alpha (Omega_tilt)^2, no
      physical shear): the deprojected reading is EXACTLY 0 at the
      declared second order (false-positive removal);
    - shear-only sky (Omega_tilt = 0): the deprojected reading equals
      Sigma^2 (no over-subtraction).
    """
    results: dict[str, list] = {"boost_removed_states": [],
                                "no_oversubtraction_states": []}
    for beta_num in (1, 3, 7):
        omega = Fraction(beta_num, 1000)          # Omega_tilt = kappa*beta
        sigma2_naive = Fraction(alpha) * omega ** 2
        boost_removed = deprojected_shear(sigma2_naive, omega, alpha)
        if boost_removed != 0:
            raise SourceResponseError(
                "pure local boost not removed at the declared order — "
                "deprojection estimator property fails")
        results["boost_removed_states"].append(
            {"omega_tilt": str(omega), "sigma_tilde2": str(boost_removed)})
    for sigma2 in (Fraction(1, 100), Fraction(17, 1000)):
        kept = deprojected_shear(sigma2, Fraction(0), alpha)
        if kept != sigma2:
            raise SourceResponseError(
                "shear-only sky over-subtracted — deprojection is not a "
                "clean estimator property")
        results["no_oversubtraction_states"].append(
            {"sigma2": str(sigma2), "sigma_tilde2": str(kept)})
    return {
        "alpha": str(Fraction(alpha)),
        "interpretation": "SYNTHETIC local-boost estimator property "
                          "(false-positive removal); never a shear "
                          "detection",
        "algebraic_status": "exact_by_construction_illustrative",
        **results,
    }


# ---------------------------------------------------------------------------
# Response ladder
# ---------------------------------------------------------------------------

class Rung(str, Enum):
    ALGEBRAIC_WITNESS = "algebraic_witness"
    CONSTRAINT_ADMISSIBLE = "constraint_admissible"
    LOCAL_DYNAMICS_ADMISSIBLE = "local_dynamics_admissible"
    GLOBAL_DYNAMICS_ADMISSIBLE = "global_dynamics_admissible"


_RUNG_ORDER = (Rung.ALGEBRAIC_WITNESS, Rung.CONSTRAINT_ADMISSIBLE,
               Rung.LOCAL_DYNAMICS_ADMISSIBLE,
               Rung.GLOBAL_DYNAMICS_ADMISSIBLE)


def _require_repo_evidence_file(pointer: str, rung: Rung) -> None:
    root = _REPO_ROOT.resolve()
    raw = Path(pointer)
    candidate = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SourceResponseError(
            f"evidence pointer {pointer!r} for rung {rung.value} resolves "
            "outside the repository"
        ) from exc
    if not candidate.is_file():
        raise SourceResponseError(
            f"evidence pointer {pointer!r} for rung {rung.value} does "
            "not resolve to a repo file — false citation is refused"
        )


def label_highest_rung(evidence: Mapping[Rung, str | None]) -> dict:
    """The highest rung reached is the last CONSECUTIVE rung whose
    evidence pointer is present AND resolves to a real repo file,
    starting at the base. A gap (or an unresolvable pointer) caps the
    candidate below the gap — no rung is auto-promoted, and a missing
    lower pointer blocks the higher ones."""
    reached = None
    for rung in _RUNG_ORDER:
        pointer = evidence.get(rung)
        if not pointer or not str(pointer).strip():
            break
        _require_repo_evidence_file(str(pointer), rung)
        reached = rung
    if reached is None:
        raise SourceResponseError(
            "no rung reached: even algebraic_witness needs an evidence "
            "pointer that resolves (the ladder never auto-promotes)")
    return {
        "highest_rung": reached.value,
        "evidence": {r.value: evidence.get(r) for r in _RUNG_ORDER
                     if evidence.get(r)},
    }


def require_rung_not_above(evidence: Mapping[Rung, str | None],
                           claimed_rung: Rung) -> None:
    """Reject a claim to a rung ABOVE the highest actually reached —
    the real auto-promotion kill (a mid-ladder gap with the top rung
    present must not certify the top)."""
    highest = label_highest_rung(evidence)["highest_rung"]
    highest_index = [r.value for r in _RUNG_ORDER].index(highest)
    claimed_index = _RUNG_ORDER.index(claimed_rung)
    if claimed_index > highest_index:
        raise SourceResponseError(
            f"claimed rung {claimed_rung.value} is above the highest "
            f"reached rung {highest} — auto-promotion past a gap is "
            "refused")


# ---------------------------------------------------------------------------
# Response graph: analytic vs observed rank + aligned-axis exception
# ---------------------------------------------------------------------------

# The response basis and rows ARE the PR-127 DECLARED response map
# (imported, not re-transcribed), so this PR cannot contradict the
# frozen rank-2 / kernel={W2, DeltaOmega_k} structural non-identification.
RESPONSE_AXES = SECTORS   # ("Sigma2", "W2", "Omega_tilt", "DeltaOmega_k")
ANALYTIC_RESPONSE_ROWS = RESPONSE_ROWS
# The two response directions that ARE active (the non-kernel axes):
# a window/mask collinearity between them is what can drop the rank.
_ACTIVE_AXES = ("Sigma2", "Omega_tilt")


def _exact_rank(rows: Sequence[Sequence[Fraction]]) -> int:
    return int(sp.Matrix([[sp.Rational(v) for v in row]
                          for row in rows]).rank())


def analytic_response_rank() -> int:
    rank = _exact_rank(ANALYTIC_RESPONSE_ROWS)
    if rank != EXPECTED_RANK:
        raise SourceResponseError(
            f"analytic response rank {rank} != the PR-127 frozen "
            f"EXPECTED_RANK {EXPECTED_RANK} — the response map drifted")
    return rank


def analytic_kernel() -> list[list[str]]:
    """The analytic non-identification kernel = the PR-127 frozen
    {e_W2, e_DeltaOmega_k} two-sector joint null (consistency anchor)."""
    return sorted([str(v) for v in row] for row in EXPECTED_KERNEL_BASIS)


def observed_response(window: Mapping | None = None) -> dict:
    """The observed response rank is a SEPARATE quantity from the
    analytic rank-2 map: a transfer/mask/window collinearity that
    aligns the two ACTIVE (non-kernel) response directions reduces it
    to rank 1. Any rank drop surfaces the aligned-axis rank-1 exception
    with the colliding axes named — never hidden."""
    rows = [list(row) for row in ANALYTIC_RESPONSE_ROWS]
    aligned_pairs = []
    if window:
        collinear = window.get("collinear_axes") or []
        for pair in collinear:
            i, j = (RESPONSE_AXES.index(pair[0]),
                    RESPONSE_AXES.index(pair[1]))
            # a window that makes axis j respond collinearly with axis i:
            # every row's axis-j entry is folded onto axis i, killing the
            # independent j-direction contribution.
            for row in rows:
                row[i] = row[i] + row[j]
                row[j] = Fraction(0)
            aligned_pairs.append(sorted(pair))
    observed_rank = _exact_rank(rows)
    analytic = analytic_response_rank()
    exception = None
    if observed_rank < analytic:
        exception = {
            "kind": "aligned_axis_rank_reduction",
            "analytic_rank": analytic,
            "observed_rank": observed_rank,
            "colliding_axes": aligned_pairs,
            "note": "window/mask collinearity dropped the observed rank "
                    "below the PR-127 analytic rank-2 map; the "
                    "aligned-axis rank-1 exception is surfaced, not hidden",
        }
    return {
        "analytic_rank": analytic,
        "analytic_kernel": analytic_kernel(),
        "observed_rank": observed_rank,
        "aligned_axis_exception": exception,
    }


def require_surfaced_exception(report: Mapping) -> None:
    """A rank-reduced observed response MUST carry the aligned-axis
    exception; omitting it is rejected."""
    if report["observed_rank"] < report["analytic_rank"] and \
            not report.get("aligned_axis_exception"):
        raise SourceResponseError(
            "observed rank is below the analytic rank but the "
            "aligned-axis exception is missing — hiding the exception "
            "is forbidden")


# ---------------------------------------------------------------------------
# Discrimination verdict
# ---------------------------------------------------------------------------

def discrimination_verdict(*, boost_removed: bool,
                           local_rank: int, global_rank: int,
                           full_rank: int) -> str:
    """non_identified whenever a pure local boost is not removed at the
    declared order OR the local/global response is rank-deficient."""
    if not isinstance(boost_removed, bool):
        raise SourceResponseError(
            "boost_removed must be an explicit boolean"
        )
    ranks = {
        "local_rank": local_rank,
        "global_rank": global_rank,
        "full_rank": full_rank,
    }
    if any(isinstance(rank, bool) or not isinstance(rank, int)
           for rank in ranks.values()):
        raise SourceResponseError(
            "discrimination ranks must be integers"
        )
    if full_rank < 1:
        raise SourceResponseError(
            "full_rank must be a positive target rank"
        )
    if not (0 <= local_rank <= full_rank
            and 0 <= global_rank <= full_rank):
        raise SourceResponseError(
            "local and global ranks must lie between zero and full_rank"
        )
    if not boost_removed:
        return "non_identified"
    if local_rank < full_rank or global_rank < full_rank:
        return "non_identified"
    return "discriminable_pre_solver"


# ---------------------------------------------------------------------------
# Caption gate
# ---------------------------------------------------------------------------

_FORBIDDEN_PHRASES = tuple(
    a + b for a, b in (
        ("bridge A_v", " to Omega_tilt"),
        ("measures the", " Bianchi family"),
        ("global tilt", " measured"),
        ("shear detected", " via deprojection"),
        ("aligned-axis exception", " suppressed"),
    )
)


def lint_caption(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_PHRASES:
        if phrase.lower() in lowered:
            raise SourceResponseError(
                "caption carries forbidden bridge/measurement/detection/"
                "suppression language")


def generate_caption() -> str:
    obs = observed_response({"collinear_axes": [("Sigma2", "Omega_tilt")]})
    text = (
        "[source_response] A_v (kinematic proxy, O(beta), ell=1) and "
        "Omega_tilt (physical tilt, O(beta), ell=1) are distinct types "
        "with no auto-bridge; the kinematic quadrupole enters at "
        "O(beta^2), ell=2, and is removed from the shear reading by the "
        f"synthetic deprojection. Analytic response rank "
        f"{obs['analytic_rank']} (the PR-127 frozen map, kernel = the "
        "W2/DeltaOmega_k joint null); under a Sigma2/Omega_tilt window "
        f"collinearity the observed rank drops to {obs['observed_rank']} "
        "and the aligned-axis rank-1 exception is surfaced. Pre-solver "
        "discrimination only; no scalar family/geometry measurement."
    )
    lint_caption(text)
    return text
