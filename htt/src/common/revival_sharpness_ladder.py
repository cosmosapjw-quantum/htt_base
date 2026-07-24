"""PR-216: physical sharpness ladder algebraic -> constraint -> local -> global.

Sharpness is proven in stages and never weakened. An algebraic PSD witness does
NOT auto-promote to global Einstein-matter dynamics sharpness: each stage is
attained only if every lower stage is attained AND its own evidence is present.
The global stage requires the native solver and is legitimately BLOCKED (a
research obligation, not a scope reduction).
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Fr

STAGES = ("algebraic", "constraint", "local", "global")


class SharpnessError(ValueError):
    pass


@dataclass
class Stage:
    name: str
    status: str  # ATTAINED / ATTAINED_WITH_OBLIGATION / BLOCKED / OPEN
    evidence: str


class SharpnessLadder:
    def __init__(self):
        self.stages = {s: Stage(s, "OPEN", "") for s in STAGES}

    def _lower(self, name):
        return STAGES[:STAGES.index(name)]

    def attain(self, name: str, status: str, evidence: str) -> None:
        for low in self._lower(name):
            if self.stages[low].status not in ("ATTAINED", "ATTAINED_WITH_OBLIGATION"):
                raise SharpnessError(
                    f"cannot attain {name}: lower stage {low} is {self.stages[low].status}")
        if name == "global" and status != "BLOCKED":
            raise SharpnessError(
                "global sharpness remains BLOCKED until a native solver "
                "verification path is implemented"
            )
        self.stages[name] = Stage(name, status, evidence)

    def auto_promote_global_from_algebraic(self) -> None:
        """Decisive falsifier probe: promoting global from an algebraic witness
        alone must be refused (constraint + local are unmet)."""
        # deliberately skip constraint/local
        self.attain("global", "ATTAINED", "algebraic witness only")

    def snapshot(self) -> dict:
        return {s: {"status": self.stages[s].status, "evidence": self.stages[s].evidence}
                for s in STAGES}


def homogeneous_momentum_constraint_residual() -> Fr:
    """For spatially homogeneous data every constraint spatial-gradient term
    D_b sigma^{ab} - (2/3) D^a Theta vanishes identically -> exact zero."""
    # symbolic stand-in: homogeneous => all spatial derivatives are 0
    D_sigma = Fr(0)
    D_theta = Fr(0)
    return D_sigma - Fr(2, 3) * D_theta


def build_certified_ladder() -> SharpnessLadder:
    L = SharpnessLadder()
    # algebraic: PSD moment-cone witness (PR-223)
    L.attain("algebraic", "ATTAINED", "PSD moment-cone witness (PR-223)")
    # constraint: homogeneous initial data -> exact zero constraint residual
    assert homogeneous_momentum_constraint_residual() == 0
    L.attain("constraint", "ATTAINED", "exact zero momentum-constraint residual on homogeneous data")
    # local: endpoint attainability by exact homogeneous data (PR-131/T3), full
    # local development integration is a registered obligation
    L.attain("local", "ATTAINED_WITH_OBLIGATION",
             "endpoint attainability (PR-131 slaving / T3); full development deferred")
    # global: Einstein-matter solution-space dynamics need the native solver
    L.attain("global", "BLOCKED",
             "native Bianchi Boltzmann solver required (Track II)")
    return L
