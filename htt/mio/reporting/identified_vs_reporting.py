"""mio.reporting.identified_vs_reporting — semantic split registry.

This is the active MIO copy of the "identified vs reporting" classification
used by figure F25 and any reporting path that must avoid promoting
ceiling-dependent summaries into likelihood-owned quantities.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "QuantityType",
    "QuantityClassification",
    "QUANTITY_REGISTRY",
    "classify_quantity",
    "split_posterior_report",
    "enforce_identified_only",
    "IdentifiedVsReportingSplitter",
]


class QuantityType(Enum):
    IDENTIFIED = "identified"
    REPORTING = "reporting"


@dataclass(frozen=True)
class QuantityClassification:
    """Classification metadata for one posterior-like quantity."""

    name: str
    symbol: str
    quantity_type: QuantityType
    depends_on: tuple[str, ...] = ()
    ceiling_dependent: bool = False
    comparator_dependent: bool = False
    physical_interpretation: str = ""
    warning: str = ""


QUANTITY_REGISTRY: dict[str, QuantityClassification] = {
    "beta": QuantityClassification(
        name="beta",
        symbol=r"\beta",
        quantity_type=QuantityType.IDENTIFIED,
        physical_interpretation="Tilt rapidity (peculiar velocity / c).",
    ),
    "Sigma2": QuantityClassification(
        name="Sigma2",
        symbol=r"\Sigma^2",
        quantity_type=QuantityType.IDENTIFIED,
        physical_interpretation="Normalised shear scalar.",
    ),
    "Omega_K": QuantityClassification(
        name="Omega_K",
        symbol=r"\Omega_K",
        quantity_type=QuantityType.IDENTIFIED,
        physical_interpretation="Curvature density parameter.",
    ),
    "x": QuantityClassification(
        name="x",
        symbol="x",
        quantity_type=QuantityType.REPORTING,
        depends_on=("Sigma2", "beta", "Omega_K"),
        comparator_dependent=True,
        physical_interpretation="Comparator-conditioned master defect.",
        warning="Comparator choice changes x; cross-comparator BF is forbidden.",
    ),
    "F": QuantityClassification(
        name="F",
        symbol=r"\mathcal{F}",
        quantity_type=QuantityType.REPORTING,
        depends_on=("x",),
        ceiling_dependent=True,
        comparator_dependent=True,
        physical_interpretation="Normalised departure coordinate.",
        warning="Physical interpretation requires MIO ceiling certification.",
    ),
    "Q": QuantityClassification(
        name="Q",
        symbol="Q",
        quantity_type=QuantityType.REPORTING,
        depends_on=("x",),
        ceiling_dependent=True,
        physical_interpretation="Departure significance under an adopted ceiling.",
        warning="PPC is forbidden on Q; it is ceiling-dependent.",
    ),
    "Pi": QuantityClassification(
        name="Pi",
        symbol=r"\Pi",
        quantity_type=QuantityType.REPORTING,
        depends_on=("Q",),
        ceiling_dependent=True,
        physical_interpretation="Threshold exceedance probability.",
        warning="Threshold- and ceiling-dependent reporting quantity.",
    ),
    "v_tilt": QuantityClassification(
        name="v_tilt",
        symbol=r"v_{\rm tilt}",
        quantity_type=QuantityType.REPORTING,
        depends_on=("beta",),
        physical_interpretation="Exploratory bridge tilt velocity.",
        warning="Bridge quantity; do not promote to identified status.",
    ),
    "delta_H": QuantityClassification(
        name="delta_H",
        symbol=r"\Delta H",
        quantity_type=QuantityType.REPORTING,
        depends_on=("beta",),
        physical_interpretation="Exploratory scale-dependent Hubble correction.",
        warning="Bridge quantity; do not promote to identified status.",
    ),
}


def classify_quantity(name: str) -> QuantityClassification:
    """Return the canonical classification for a named quantity."""
    if name not in QUANTITY_REGISTRY:
        raise KeyError(
            f"Unknown quantity '{name}'. Available: {sorted(QUANTITY_REGISTRY)}"
        )
    return QUANTITY_REGISTRY[name]


def split_posterior_report(quantities: dict[str, dict]) -> dict[str, dict[str, dict]]:
    """Split a report into identified-only and reporting-only blocks."""
    identified: dict[str, dict] = {}
    reporting: dict[str, dict] = {}
    for name, summary in quantities.items():
        cls = QUANTITY_REGISTRY.get(
            name,
            QuantityClassification(
                name=name,
                symbol=name,
                quantity_type=QuantityType.REPORTING,
                warning="Not in canonical registry — treated as reporting.",
            ),
        )
        entry = {
            **summary,
            "_classification": cls.quantity_type.value,
            "_warning": cls.warning,
        }
        if cls.quantity_type == QuantityType.IDENTIFIED:
            identified[name] = entry
        else:
            reporting[name] = entry
    return {"identified": identified, "reporting": reporting}


def enforce_identified_only(quantities: dict[str, dict]) -> dict[str, dict]:
    """Strip a mixed report down to the identified-only block."""
    return split_posterior_report(quantities)["identified"]


class IdentifiedVsReportingSplitter:
    """Stateful audit helper for identified/reporting access patterns."""

    def __init__(self) -> None:
        self._accessed_identified: set[str] = set()
        self._accessed_reporting: set[str] = set()

    def get_identified(self, name: str, report: dict[str, dict]) -> dict:
        cls = classify_quantity(name)
        if cls.quantity_type != QuantityType.IDENTIFIED:
            raise ValueError(
                f"Quantity '{name}' is {cls.quantity_type.value}, not identified."
            )
        self._accessed_identified.add(name)
        return report.get(name, {})

    def get_reporting(self, name: str, report: dict[str, dict]) -> dict:
        classify_quantity(name)
        self._accessed_reporting.add(name)
        return report.get(name, {})

    def audit(self) -> dict[str, list[str]]:
        return {
            "identified_accessed": sorted(self._accessed_identified),
            "reporting_accessed": sorted(self._accessed_reporting),
            "leakage": sorted(
                self._accessed_identified & self._accessed_reporting
            ),
        }
