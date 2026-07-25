"""PR-127 cancellation-preserving graded/PSD-cone non-identification.

Formalizes, for the DECLARED registered response map only (the three-channel
design over the graded comparator ``g = (Sigma2, W2, Omega_tilt,
DeltaOmega_k)``):

- the exact kernel and rank (two independent exact engines — SymPy and
  SageMath QQ — must agree; one-engine claims are blocked);
- the ambient carrier (the DIAGONAL section of ``S_+^3`` — the
  componentwise-nonnegative orthant — times the signed ``R`` axis): the
  three quadratic moments are
  nonnegative while the signed ``DeltaOmega_k`` axis is NEVER PSD-projected
  (clipping it destroys registered cancellation witnesses and is rejected);
- constructive set-valued equivalence witnesses: pairs of distinct carrier
  states with identical response outputs (point non-identification along
  the kernel directions);
- the comparator-level physical subset ``A_C_comparator_level``: a witness
  is labeled ``physical`` only with a VERIFIED constraint assignment
  (exact parent identity + matter positivity + the registered domain box);
  momentum/Gauss fixtures are deferred to the dynamical PRs (disclosed);
  otherwise the witness stays ``algebraic_only``;
- the added-observable rank API: an extra row raises the rank iff it lies
  outside the registered row span (verified on both engines).

Formal non-identification of the declared response map at
roadmap_rescue_v1:C2 — NEVER an isotropy statement, and silent about any
other response map, transfer, mask, or window.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Mapping, Sequence

SCHEMA_VERSION = "pr127.graded_nonid.v1"

SECTORS = ("Sigma2", "W2", "Omega_tilt", "DeltaOmega_k")

# The DECLARED registered response map (exact rational transcription of
# htt/obsstat/egs3_graded_comparator.py::channel_response_design).
RESPONSE_ROWS: tuple[tuple[Fraction, ...], ...] = (
    (Fraction(1), Fraction(0), Fraction(0), Fraction(0)),
    (Fraction(0), Fraction(0), Fraction(1), Fraction(0)),
    (Fraction(0), Fraction(0), Fraction(1), Fraction(0)),
)

EXPECTED_RANK = 2
EXPECTED_KERNEL_BASIS = (
    (Fraction(0), Fraction(1), Fraction(0), Fraction(0)),   # e_W2
    (Fraction(0), Fraction(0), Fraction(0), Fraction(1)),   # e_DeltaOmega_k
)


class GradedNonIdError(ValueError):
    """Raised on any non-identification-governance violation."""


# ---------------------------------------------------------------------------
# engine 1: SymPy exact rank/kernel
# ---------------------------------------------------------------------------

def sympy_rank_kernel(rows: Sequence[Sequence[Fraction]]) -> dict:
    import sympy as sp

    matrix = sp.Matrix([[sp.Rational(x) for x in row] for row in rows])
    kernel = matrix.nullspace()
    return {
        "engine": "sympy",
        "rank": int(matrix.rank()),
        "kernel_basis": sorted(
            tuple(str(sp.nsimplify(entry)) for entry in vec)
            for vec in kernel
        ),
    }


# ---------------------------------------------------------------------------
# engine 2: SageMath QQ exact rank/kernel (subprocess)
# ---------------------------------------------------------------------------

def sage_rank_kernel(rows: Sequence[Sequence[Fraction]],
                     extra_probe_rows: Sequence[Sequence[Fraction]] = ()
                     ) -> dict:
    """One sage invocation computing base rank/kernel plus the rank with
    each probe row appended. Returns parsed JSON."""
    payload = {
        "rows": [[str(x) for x in row] for row in rows],
        "probes": [[str(x) for x in row] for row in extra_probe_rows],
    }
    script = (
        "import json\n"
        "from sage.all import QQ, matrix\n"
        f"data = json.loads({json.dumps(json.dumps(payload))})\n"
        "base = matrix(QQ, [[QQ(x) for x in row] for row in data['rows']])\n"
        "kernel = base.right_kernel().basis()\n"
        "probe_ranks = []\n"
        "for row in data['probes']:\n"
        "    stacked = base.stack(matrix(QQ, [[QQ(x) for x in row]]))\n"
        "    probe_ranks.append(int(stacked.rank()))\n"
        "print(json.dumps({'engine': 'sage_qq', 'rank': int(base.rank()),\n"
        "  'kernel_basis': sorted(tuple(str(e) for e in v) for v in kernel),\n"
        "  'probe_ranks': probe_ranks}))\n"
    )
    completed = subprocess.run(["sage", "-c", script], capture_output=True,
                               text=True, timeout=600, check=False)
    for line in reversed(completed.stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise GradedNonIdError(
        f"sage engine produced no result (exit {completed.returncode}): "
        f"{completed.stderr[-300:]}"
    )


def require_registered_kernel(claimed_basis: Sequence[Sequence]) -> None:
    """The REAL kernel-claim validator: a claimed kernel basis must equal
    the registered two-engine-agreed basis exactly (as a set of exact
    rational vectors). A dropped or extra direction is rejected."""
    normalized = sorted(tuple(str(Fraction(str(e))) for e in vec)
                        for vec in claimed_basis)
    expected = sorted(tuple(str(x) for x in vec)
                      for vec in EXPECTED_KERNEL_BASIS)
    if normalized != expected:
        raise GradedNonIdError(
            f"claimed kernel basis {normalized} != registered agreed basis "
            f"{expected}"
        )


def require_engine_agreement(results: Sequence[Mapping]) -> dict:
    """The exit gate: BOTH engines present, ranks equal, kernels equal.

    A claim carried by one engine (or with disagreeing engines) is blocked.
    """
    engines = {str(r.get("engine")) for r in results}
    if engines != {"sympy", "sage_qq"}:
        raise GradedNonIdError(
            f"rank/kernel claims require BOTH exact engines; got {sorted(engines)}"
        )
    ranks = {int(r["rank"]) for r in results}
    if len(ranks) != 1:
        raise GradedNonIdError(f"engines disagree on rank: {sorted(ranks)}")
    normalized = {
        json.dumps(sorted(tuple(str(Fraction(e)) for e in vec)
                          for vec in r["kernel_basis"]))
        for r in results
    }
    if len(normalized) != 1:
        raise GradedNonIdError("engines disagree on the kernel basis")
    return {"rank": ranks.pop(), "engines": sorted(engines)}


# ---------------------------------------------------------------------------
# ambient carrier + witnesses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CarrierPoint:
    """A point of the ambient carrier: the DIAGONAL section of S_+^3 (the
    componentwise-nonnegative orthant over the three quadratic moments)
    times the signed R axis. Off-diagonal PSD structure is reserved for
    the native-solver superset; the response map is undefined there."""

    sigma2: Fraction
    w2: Fraction
    omega_tilt: Fraction
    delta_omega_k: Fraction

    def __post_init__(self) -> None:
        for name in ("sigma2", "w2", "omega_tilt", "delta_omega_k"):
            value = getattr(self, name)
            if isinstance(value, bool):
                raise GradedNonIdError(
                    f"{name} must be numeric, not a boolean"
                )
            object.__setattr__(self, name, Fraction(value))
        for name in ("sigma2", "w2", "omega_tilt"):
            if getattr(self, name) < 0:
                raise GradedNonIdError(
                    f"{name} is a quadratic moment and must be nonnegative"
                )

    def vector(self) -> tuple[Fraction, ...]:
        return (self.sigma2, self.w2, self.omega_tilt, self.delta_omega_k)

    def x_c(self) -> Fraction:
        """The master comparator combination (cancellation diagnostics)."""
        return (self.sigma2 - self.w2 + self.omega_tilt
                + self.delta_omega_k)

    def response(self) -> tuple[Fraction, ...]:
        return tuple(
            sum(coef * comp for coef, comp in zip(row, self.vector()))
            for row in RESPONSE_ROWS
        )


def forbid_psd_projection(original: CarrierPoint,
                          transformed: CarrierPoint) -> None:
    """The signed DeltaOmega_k axis is never PSD-projected: any transform
    that changes the signed component (e.g. clipping a negative value to 0)
    destroys registered cancellation witnesses and is rejected."""
    if transformed.delta_omega_k != original.delta_omega_k:
        raise GradedNonIdError(
            "PSD projection of the signed DeltaOmega_k axis is forbidden: "
            f"{original.delta_omega_k} -> {transformed.delta_omega_k} "
            "(cancellation witnesses must be preserved)"
        )


def validate_witness_pair(a: CarrierPoint, b: CarrierPoint) -> dict:
    """A set-valued equivalence witness: distinct carrier points with
    IDENTICAL response outputs; their difference must lie in the kernel."""
    if a.vector() == b.vector():
        raise GradedNonIdError("witness pair must be distinct states")
    if a.response() != b.response():
        raise GradedNonIdError(
            "witness pair must be response-indistinguishable"
        )
    difference = tuple(x - y for x, y in zip(a.vector(), b.vector()))
    for row in RESPONSE_ROWS:
        if sum(c * d for c, d in zip(row, difference)) != 0:
            raise GradedNonIdError("witness difference is not in the kernel")
    return {
        "difference": [str(d) for d in difference],
        "response_output": [str(v) for v in a.response()],
    }


# Registered comparator-level A_C domain box: density parameters and
# departures are bounded fractional quantities. Momentum/Gauss constraint
# fixtures are NOT implemented at this comparator level — they are owned by
# the LRS/KS dynamical PRs (PR-131+) and this label is therefore
# A_C_comparator_level, never a full physical-constraint certificate.
A_C_DOMAIN_BOX = {
    "omega_m": (Fraction(0), Fraction(1)),
    "omega_l": (Fraction(-2), Fraction(2)),
    "omega_k_total": (Fraction(-1), Fraction(1)),
    "departures_max": Fraction(1),
}


def constraint_assignment(point: CarrierPoint, *, omega_m: Fraction,
                          omega_l: Fraction,
                          omega_k_total: Fraction) -> dict:
    """A_C_comparator_level membership: the parent identity must hold
    EXACTLY, matter positivity holds, and every quantity lies in the
    registered domain box — an unbounded nuisance dial can no longer
    promote an absurd state. Momentum/Gauss fixtures are deferred to the
    dynamical PRs (disclosed); without a verified assignment the witness
    stays algebraic_only."""
    raw_assignment = (omega_m, omega_l, omega_k_total)
    if any(isinstance(value, bool) for value in raw_assignment):
        raise GradedNonIdError(
            "constraint assignment values must be numeric, not booleans"
        )
    omega_m, omega_l, omega_k_total = (
        Fraction(value) for value in raw_assignment
    )
    lo, hi = A_C_DOMAIN_BOX["omega_m"]
    if not (lo <= omega_m <= hi):
        raise GradedNonIdError(
            f"matter positivity/box violated (Omega_m = {omega_m})"
        )
    lo, hi = A_C_DOMAIN_BOX["omega_l"]
    if not (lo <= omega_l <= hi):
        raise GradedNonIdError(f"Omega_L outside the registered box: {omega_l}")
    lo, hi = A_C_DOMAIN_BOX["omega_k_total"]
    if not (lo <= omega_k_total <= hi):
        raise GradedNonIdError(
            f"Omega_k_total outside the registered box: {omega_k_total}"
        )
    cap = A_C_DOMAIN_BOX["departures_max"]
    for name in ("sigma2", "w2", "omega_tilt"):
        if getattr(point, name) > cap:
            raise GradedNonIdError(
                f"departure {name} outside the registered box"
            )
    if abs(point.delta_omega_k) > cap:
        raise GradedNonIdError("delta_omega_k outside the registered box")
    identity = (omega_m + omega_l + omega_k_total + point.omega_tilt
                + point.sigma2 - point.w2)
    if identity != 1:
        raise GradedNonIdError(
            f"parent identity violated: sum = {identity} != 1"
        )
    return {
        "label": "physical",
        "level": "A_C_comparator_level",
        "deferred_constraints": "momentum_and_gauss_fixtures_owned_by_PR-131_plus",
        "assignment": {"Omega_m": str(omega_m), "Omega_L": str(omega_l),
                       "Omega_k_total": str(omega_k_total)},
    }


def witness_label(point: CarrierPoint,
                  assignment: Mapping | None) -> str:
    """physical ONLY with a verified assignment; anything else is
    algebraic_only (fail-closed)."""
    if assignment is None:
        return "algebraic_only"
    verdict = constraint_assignment(
        point,
        omega_m=Fraction(str(assignment["Omega_m"])),
        omega_l=Fraction(str(assignment["Omega_L"])),
        omega_k_total=Fraction(str(assignment["Omega_k_total"])),
    )
    return verdict["label"]


# ---------------------------------------------------------------------------
# added-observable rank API
# ---------------------------------------------------------------------------

def added_row_raises_rank(row: Sequence[Fraction],
                          sage_probe_rank: int) -> bool:
    """TRUE iff the added row lies outside the registered row span,
    verified on BOTH engines (SymPy live; the sage probe rank is supplied
    from the one-shot sage run and cross-checked here)."""
    stacked = tuple(RESPONSE_ROWS) + (tuple(Fraction(x) for x in row),)
    sympy_result = sympy_rank_kernel(stacked)
    if sympy_result["rank"] != sage_probe_rank:
        raise GradedNonIdError(
            f"engines disagree on the probe rank: sympy "
            f"{sympy_result['rank']} vs sage {sage_probe_rank}"
        )
    return sympy_result["rank"] > EXPECTED_RANK


# ---------------------------------------------------------------------------
# language lint
# ---------------------------------------------------------------------------

_FORBIDDEN_TEXT = (
    "non-identification proves isotropy", "isotropy established",
    "identification impossible in nature", "proves isotropy",
    "establishes isotropy", "isotropy proven",
    "Bianchi geometry detected", "Bianchi family identified",
    "finding rescued", "validated as native",
)


def lint_nonid_text(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_TEXT:
        if phrase.lower() in lowered:
            raise GradedNonIdError(
                f"non-identification language violation: {phrase!r}"
            )
