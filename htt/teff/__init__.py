"""Legacy Teff compatibility and reproducibility surface.

The canonical package is ``teff``; ``htt.teff`` remains a legacy import alias.

Owner: TSC_LEGACY (compatibility/reproducibility only).  The historical
representative functions remain importable so frozen Teff-era calculations can
be reproduced, but this package is not an active scientific owner and must not
emit current scientific artifacts, posterior/evidence products, MIO
certificates, native-solver results, or family-identification claims.

The functions below reproduce the archived max-entropy representative and
nonlinear angular-response ledgers.  Historical submodules may preserve frozen
``owner: TEFF`` metadata as reproduction evidence, but that metadata cannot
authorize new work or revive ``TEFF`` ownership.  Any current consumer must
treat the output as a TSC_LEGACY legacy-reproduction artifact with explicit
caveats.

Claim discipline: legacy reproduction only; no current data, detection,
Bianchi-family/geometry, native-solver, posterior, likelihood, or ownership
claim.  The historical draft's transport-closure, boundary-conditioning,
global-diffeomorphism, and global-stability nonclaims remain nonclaims.
"""
from .representative import (  # noqa: F401
    RADIAL_CONSTANTS,
    radial_constant,
    radial_fingerprint,
    two_temperature_ratio,
    gram_ledger_psd,
    l2_staircase_monotone,
    equal_information_nonidentifiability,
    teff_representative_seal,
)

TEFF_LEGACY_IMPORT_COMPATIBLE = True
TEFF_ACTIVE_SCIENCE_OWNER = False
TEFF_OWNER = "TSC_LEGACY"
TEFF_IMPLEMENTATION_SCOPE = "tsc_legacy"
TEFF_CLAIM_TIER = "diagnostic_only"
TEFF_BUNDLE_KIND = "legacy_reproduction"
TEFF_DEPRECATION_STATUS = "legacy_reproduction_only"
TEFF_DEPRECATION_CAVEAT = (
    "Teff is retained only for frozen compatibility and reproducibility; "
    "historical TEFF-labelled payloads are not current-owner artifacts."
)

__all__ = [
    "RADIAL_CONSTANTS",
    "TEFF_ACTIVE_SCIENCE_OWNER",
    "TEFF_BUNDLE_KIND",
    "TEFF_CLAIM_TIER",
    "TEFF_DEPRECATION_CAVEAT",
    "TEFF_DEPRECATION_STATUS",
    "TEFF_IMPLEMENTATION_SCOPE",
    "TEFF_LEGACY_IMPORT_COMPATIBLE",
    "TEFF_OWNER",
    "equal_information_nonidentifiability",
    "gram_ledger_psd",
    "l2_staircase_monotone",
    "radial_constant",
    "radial_fingerprint",
    "teff_representative_seal",
    "two_temperature_ratio",
]
