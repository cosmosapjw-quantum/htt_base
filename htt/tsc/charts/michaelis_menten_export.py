"""
tsc/charts/michaelis_menten_export.py  (TSC-05, Week 7)
========================================================

Route B Michaelis-Menten SSOT mirror on the tsc side.

The W10-01 Route B sentinel

    D_2(Sigma^2) = C_1 Sigma^2 / (1 + C_2 Sigma^2),
        C_1 = 1.753e7,   C_2 = 6.825e5,
        D_2(Sigma^2 = 1e-8) ≈ 0.174112 μK^2

is authored by ``bass.spectrum.cl_assembly`` (``ROUTE_B_C1``,
``ROUTE_B_C2``). TSC-05 mirrors the constants with:

* a freeze on the literal values (anti-regression against bass);
* a scalar/array evaluator that does NOT import bass (so downstream
  chart scripts can pull in *only* the tsc stack);
* a JSON export with a frozen schema so the mirror is auditable
  without Python.

Role in the cross-repo topology
-------------------------------
bass_rs (Rust) publishes the authoritative constants in
``bass_rs/d2_convention.rs``. ``bass.spectrum.cl_assembly`` mirrors
them in Python. TSC-05 is the tsc-side mirror, enforced consistent
with the bass-side literal via
:func:`assert_mirror_matches_bass_ssot` — invoked by the
``test_tsc_mm_constants_match_bass_ssot`` regression.

Any change to the authoritative Rust SSOT must propagate to both
mirror sites and update the sentinel D_2 literal. The tests in this
module catch drift in either direction.

Public API
----------
* :data:`ROUTE_B_C1`, :data:`ROUTE_B_C2` --- frozen mirror literals.
* :data:`ROUTE_B_D2_AT_SIGMA2_1EM8` --- derived sentinel value.
* :data:`T_CMB_K_MIRROR` --- Fixsen 2009 value cross-referenced with
  ``bass.observational.planck_mes_bounds.T_CMB_K`` so a T_CMB drift
  on the bass side is caught here too.
* :data:`SCHEMA_VERSION` --- frozen JSON schema version tag.
* :class:`MichaelisMentenExport` --- frozen dataclass holding the
  constants, provenance, and sentinel value.
* :func:`d2_route_b(sigma_sq)` --- scalar/array evaluator.
* :func:`michaelis_menten_coefficients()` --- convenience
  :class:`MichaelisMentenExport` constructor.
* :func:`export_as_dict()` / :func:`export_as_json()` --- schema-frozen
  dict / JSON serialisation.
* :func:`assert_mirror_matches_bass_ssot()` --- regression anchor
  used by the TSC-05 hero test.

References
----------
``bass_rs/d2_convention.rs`` --- authoritative SSOT (Rust).
``bass.spectrum.cl_assembly`` --- Python mirror on the bass side.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Union

import numpy as np

__all__ = [
    "ROUTE_B_C1",
    "ROUTE_B_C2",
    "ROUTE_B_D2_AT_SIGMA2_1EM8",
    "T_CMB_K_MIRROR",
    "SCHEMA_VERSION",
    "MichaelisMentenExport",
    "d2_route_b",
    "michaelis_menten_coefficients",
    "export_as_dict",
    "export_as_json",
    "assert_mirror_matches_bass_ssot",
]


# ---------------------------------------------------------------------------
# Frozen SSOT mirror
# ---------------------------------------------------------------------------

#: Michaelis-Menten numerator coefficient. Literal mirror of
#: ``bass.spectrum.cl_assembly.ROUTE_B_C1``; frozen.
ROUTE_B_C1: float = 1.753e7

#: Michaelis-Menten denominator coefficient. Literal mirror of
#: ``bass.spectrum.cl_assembly.ROUTE_B_C2``; frozen.
ROUTE_B_C2: float = 6.825e5

#: Sentinel D_2(Sigma^2 = 1e-8) in μK^2. Computed from the
#: Michaelis-Menten formula with the frozen C_1, C_2 literals.
ROUTE_B_D2_AT_SIGMA2_1EM8: float = (
    ROUTE_B_C1 * 1.0e-8 / (1.0 + ROUTE_B_C2 * 1.0e-8)
)

#: Fixsen 2009 CMB monopole temperature. Cross-referenced with
#: ``bass.observational.planck_mes_bounds.T_CMB_K``. The MM export
#: does not itself consume T_CMB, but the tsc-side chart scripts
#: report D_2 in μK^2 so a T_CMB drift would silently rescale any
#: derived amplitude. Frozen here as the anti-drift anchor.
T_CMB_K_MIRROR: float = 2.7255

#: Schema version for :func:`export_as_json`. Bump only on
#: schema-breaking changes.
SCHEMA_VERSION: str = "TSC-05/v1"


# ---------------------------------------------------------------------------
# Export dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MichaelisMentenExport:
    """Frozen bundle of the Route B MM SSOT for tsc-side consumers.

    Attributes
    ----------
    C1, C2
        Michaelis-Menten coefficients.
    D2_at_sigma2_1em8
        Sentinel value ``D_2(Sigma^2 = 1e-8)`` in μK^2.
    T_CMB_K
        Fixsen 2009 monopole. Provenance-only here.
    schema_version
        Freeze tag for the JSON export schema.
    ssot_source
        Textual reference naming the authoritative source of truth.
    provenance
        Free-form dict for downstream consumers to attach extras.
    """

    C1: float
    C2: float
    D2_at_sigma2_1em8: float
    T_CMB_K: float = T_CMB_K_MIRROR
    schema_version: str = SCHEMA_VERSION
    ssot_source: str = "bass_rs/d2_convention.rs"
    provenance: Mapping[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Evaluators
# ---------------------------------------------------------------------------


def d2_route_b(
    sigma_sq: Union[float, np.ndarray],
    *,
    C1: float = ROUTE_B_C1,
    C2: float = ROUTE_B_C2,
) -> Union[float, np.ndarray]:
    """Evaluate ``D_2(Sigma^2) = C_1 Sigma^2 / (1 + C_2 Sigma^2)``.

    Parameters
    ----------
    sigma_sq
        Dimensionless shear amplitude squared; must be non-negative.
        Scalar or numpy array.
    C1, C2
        Override the frozen literal mirror. Defaults to the SSOT
        values. The TSC-05 regression gate uses the defaults.

    Returns
    -------
    float or np.ndarray
        Matches the shape dispatch of ``sigma_sq``.
    """
    if C1 <= 0.0:
        raise ValueError(f"C1 must be > 0; got {C1}")
    if C2 <= 0.0:
        raise ValueError(f"C2 must be > 0; got {C2}")

    arr = np.asarray(sigma_sq, dtype=float)
    if np.any(arr < 0.0):
        raise ValueError("sigma_sq must be >= 0 (negative entry found)")
    if not np.all(np.isfinite(arr)):
        raise ValueError("sigma_sq must be finite")

    result = C1 * arr / (1.0 + C2 * arr)
    if np.isscalar(sigma_sq):
        return float(result)
    return result


# ---------------------------------------------------------------------------
# Export constructor + serialisers
# ---------------------------------------------------------------------------


def michaelis_menten_coefficients(
    *,
    provenance: Mapping[str, Any] | None = None,
) -> MichaelisMentenExport:
    """Build a :class:`MichaelisMentenExport` from the frozen SSOT mirror."""
    return MichaelisMentenExport(
        C1=float(ROUTE_B_C1),
        C2=float(ROUTE_B_C2),
        D2_at_sigma2_1em8=float(ROUTE_B_D2_AT_SIGMA2_1EM8),
        T_CMB_K=float(T_CMB_K_MIRROR),
        schema_version=SCHEMA_VERSION,
        ssot_source="bass_rs/d2_convention.rs",
        provenance=dict(provenance) if provenance else {},
    )


def export_as_dict(
    export: MichaelisMentenExport | None = None,
) -> dict[str, Any]:
    """Return the frozen-schema dict view of the MM export.

    Parameters
    ----------
    export
        Optional precomputed :class:`MichaelisMentenExport`; when
        omitted a fresh instance is built from the SSOT mirror.
    """
    e = export if export is not None else michaelis_menten_coefficients()
    return {
        "schema_version": str(e.schema_version),
        "ssot_source": str(e.ssot_source),
        "coefficients": {
            "C1": float(e.C1),
            "C2": float(e.C2),
        },
        "sentinel": {
            "sigma_sq": 1.0e-8,
            "D2_microK_sq": float(e.D2_at_sigma2_1em8),
        },
        "T_CMB_K": float(e.T_CMB_K),
        "provenance": {str(k): v for k, v in (e.provenance or {}).items()},
    }


def export_as_json(
    path: str | Path | None = None,
    *,
    export: MichaelisMentenExport | None = None,
    indent: int = 2,
) -> str:
    """Serialise the MM export as JSON.

    When ``path`` is given, also writes the JSON to disk.
    Returns the JSON string either way.
    """
    payload = export_as_dict(export)
    s = json.dumps(payload, indent=indent, sort_keys=True)
    if path is not None:
        Path(path).write_text(s, encoding="utf-8")
    return s


# ---------------------------------------------------------------------------
# Regression guard
# ---------------------------------------------------------------------------


def assert_mirror_matches_bass_ssot(rtol: float = 0.0) -> None:
    """Compare the tsc-side MM mirror against the bass-side SSOT.

    Raises :class:`AssertionError` on any discrepancy.

    Parameters
    ----------
    rtol
        Relative tolerance. Default ``0.0`` (bit-identity, since both
        sides hold the SSOT as a Python literal). A nonzero tolerance
        is only sensible if either side has switched to a runtime
        computation of the coefficients.
    """
    # Lazy import so the tsc stack stays importable without bass on
    # path for callers that only need the evaluator.
    from bass.spectrum.cl_assembly import (
        ROUTE_B_C1 as bass_C1,
        ROUTE_B_C2 as bass_C2,
        ROUTE_B_D2_AT_SIGMA2_1EM8 as bass_D2,
    )
    from bass.observational.planck_mes_bounds import T_CMB_K as bass_TCMB

    for label, tsc_val, bass_val in (
        ("ROUTE_B_C1", ROUTE_B_C1, float(bass_C1)),
        ("ROUTE_B_C2", ROUTE_B_C2, float(bass_C2)),
        ("ROUTE_B_D2_AT_SIGMA2_1EM8",
         ROUTE_B_D2_AT_SIGMA2_1EM8, float(bass_D2)),
        ("T_CMB_K", T_CMB_K_MIRROR, float(bass_TCMB)),
    ):
        abs_err = abs(tsc_val - bass_val)
        scale = max(abs(tsc_val), abs(bass_val), 1.0)
        rel_err = abs_err / scale
        if rel_err > rtol:
            raise AssertionError(
                f"TSC-05 SSOT drift on {label}: tsc={tsc_val!r}, "
                f"bass={bass_val!r}, rel_err={rel_err:.3e} > "
                f"rtol={rtol:.3e}. Update both sides in lock-step."
            )
