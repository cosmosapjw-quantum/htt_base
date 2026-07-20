"""PR-182 handedness reference-signal registry (hypothesis_only).

The registry stores FUTURE-NATIVE-ATLAS test vectors only. It has NO
data-ingestion API: entries are fixed schema constants, and the single
accessor refuses anything that resembles data. No present-data sign
comparison may rank, identify, or adjudicate a Bianchi family through
this module; a detected data-adjudication attempt raises immediately
(kill condition BLOCKED_DATA_ADJUDICATION_DETECTED).
"""

from __future__ import annotations

from typing import Any

SCHEMA = "htt.pr182.handedness_reference_registry.v1"

ADJUDICATION_FORBIDDEN = "FORBIDDEN_PRE_NATIVE"
STATUS_FUTURE_NATIVE = "FUTURE_NATIVE_ATLAS_TEST_VECTOR"
STATUS_RELATION_REFUTED = "ROADMAP_REFERENCE_RELATION_REFUTED_BY_I2_I3"
BLOCKED_DATA_ADJUDICATION = "BLOCKED_DATA_ADJUDICATION_DETECTED"

REGISTRY_ENTRIES: tuple[dict[str, str], ...] = (
    {
        "family_label": "bianchi_VII_h_helical_roadmap_relation",
        "reference_relation": "sign(EB/TB) = sign(x_h) [roadmap #pr-182]",
        "status": STATUS_RELATION_REFUTED,
        "adjudication": ADJUDICATION_FORBIDDEN,
        "falsifier_semantics": (
            "REFUTED at registry level by the card's own CAS-verified "
            "identities: I2 proves an orientation reversal flips TB and EB "
            "TOGETHER, so the ratio EB/TB is parity-EVEN and carries no "
            "handedness information, and I3 shows the structure-tensor "
            "orientation flip maps the VII_h representative to its mirror "
            "while the conventional h (hence any x_h built from it) is "
            "orientation-even. The roadmap-registered relation therefore "
            "cannot bind as a handedness discriminant on ANY data, native "
            "or otherwise. Retained as a registered negative result."
        ),
    },
    {
        "family_label": "bianchi_VII_h_helical_signed_component_candidate",
        "reference_relation": (
            "sign(TB) (equivalently sign(EB)) against a REGISTERED signed "
            "handedness template convention"
        ),
        "status": STATUS_FUTURE_NATIVE,
        "adjudication": ADJUDICATION_FORBIDDEN,
        "falsifier_semantics": (
            "Replacement candidate for the refuted ratio relation: the "
            "individual parity-odd cross-correlations DO flip sign under "
            "orientation reversal (I2), so a signed TB (or EB) template "
            "convention can carry handedness on an authenticated native "
            "atlas ONLY. A mismatch refutes the helical hypothesis at "
            "registry level; a match is corroboration only, never "
            "identification. The template-sign convention itself must be "
            "registered before any native evaluation."
        ),
    },
    {
        "family_label": "mirror_symmetric_axisymmetric_configurations",
        "reference_relation": "B == 0 (parity identity I1)",
        "status": STATUS_FUTURE_NATIVE,
        "adjudication": ADJUDICATION_FORBIDDEN,
        "falsifier_semantics": (
            "Valid ONLY for mirror-symmetric axisymmetric configurations "
            "(the m=0 sector fixed by the reflection): honest scope is "
            "Bianchi I/V/IX and the registered axis-aligned mode subsets "
            "of III/VII_0 per the FB-2.2/FB-2.3 envelope. Generic VII_0 "
            "(and III) spiral configurations are NOT mirror-symmetric and "
            "are excluded; per-family axisymmetry is a geometric premise "
            "verified by no CAS axis here. Never evaluated on shipped "
            "data by this module."
        ),
    },
    {
        "family_label": "pure_boost",
        "reference_relation": (
            "parity-odd TB/EB zero for the temperature Doppler kernel "
            "chain (I4 with I1/I2)"
        ),
        "status": STATUS_FUTURE_NATIVE,
        "adjudication": ADJUDICATION_FORBIDDEN,
        "falsifier_semantics": (
            "Scope: the registered chain covers the temperature Doppler "
            "kernel (axisymmetric mu-only structure to O(beta^3)); spin-2 "
            "aberration of polarization is NOT covered by the registered "
            "identities. Never evaluated on shipped data by this module."
        ),
    },
)

ATTRIBUTION = (
    "The axisymmetric-to-E-only / helical-to-parity-odd split is "
    "CONFIRMATORY of Pontzen & Challinor 2007, MNRAS 380, 1387 "
    "(arXiv:0706.2075; identifier transcribed from the public record, "
    "not verified against print). The card's registered outcome is the "
    "REFUTATION of the roadmap's sign(EB/TB)=sign(x_h) relation plus a "
    "signed-component replacement candidate; neither is a family "
    "identification."
)


class DataAdjudicationAttempt(RuntimeError):
    """Raised when anything data-like is routed into the registry."""


def _reject_data_like(value: Any, label: str) -> None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    raise DataAdjudicationAttempt(
        f"{BLOCKED_DATA_ADJUDICATION}: registry accessor received a "
        f"non-scalar argument {label!r}; the PR-182 registry has no data "
        "path and never adjudicates a family from shipped data"
    )


def get_reference_entry(
    family_label: str, observed: Any = None, **extra: Any
) -> dict[str, str]:
    """Return one registered reference entry by label.

    ``observed`` and keyword extras exist ONLY so misuse is detectable:
    anything data-like raises :class:`DataAdjudicationAttempt`.
    """
    _reject_data_like(observed, "observed")
    if observed is not None:
        raise DataAdjudicationAttempt(
            f"{BLOCKED_DATA_ADJUDICATION}: an 'observed' value was supplied; "
            "the registry never compares reference relations against data"
        )
    for key, value in extra.items():
        _reject_data_like(value, key)
        raise DataAdjudicationAttempt(
            f"{BLOCKED_DATA_ADJUDICATION}: unexpected argument {key!r}; the "
            "registry accessor accepts a family label only"
        )
    for entry in REGISTRY_ENTRIES:
        if entry["family_label"] == family_label:
            return dict(entry)
    raise KeyError(f"unregistered family label: {family_label}")


def registry_payload() -> dict[str, Any]:
    """Serializable registry block for the result card."""
    return {
        "schema": SCHEMA,
        "entries": [dict(entry) for entry in REGISTRY_ENTRIES],
        "attribution": ATTRIBUTION,
        "data_ingestion_api": "none",
        "adjudication_policy": ADJUDICATION_FORBIDDEN,
    }
