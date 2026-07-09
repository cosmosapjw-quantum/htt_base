"""htt.teff -- active max-entropy Effective-Temperature representative lane (v8).

Owner: TEFF (active, diagnostic-only). This package implements the rigorous
theory of the draft "Maximum-Entropy Effective-Temperature Representatives and
Nonlinear Angular Response Ledgers", which supersedes the frozen Teff-characteristics
Papers I-V. It is DISTINCT from the frozen TSC_LEGACY reproduction surface
(htt/tsc, PR-030): the legacy surface stays a legacy-reproduction owner, while the
new representative theorems are owned here as an active-but-diagnostic-only lane.

It reuses the existing computational substrate (tsc.charts.laguerre_basis spectral
moments, the zeta(4) radial integrals) but adds the genuinely new objects: the
max-entropy representative theorem's radial constants a_xi, the (n,k) insertion
ledger's radial fingerprints c_p, the SO(3) Gram ledgers + exact L^2 staircase, and
the equal-information nonidentifiability theorem with its two-temperature anchor.

Claim discipline (TEFF owner ceiling = diagnostic_only): representation theory +
exact closed forms only. No data claim, no detection, no Bianchi-family/geometry
identification, no native-solver-produced claim, no posterior/likelihood claim. The
draft's own explicit nonclaims (transport closure, boundary conditioning near
realizability loss, global two-field diffeomorphism, global-in-time stability) are
NOT asserted here.
"""
from htt.teff.representative import (  # noqa: F401
    RADIAL_CONSTANTS,
    radial_constant,
    radial_fingerprint,
    two_temperature_ratio,
    gram_ledger_psd,
    l2_staircase_monotone,
    equal_information_nonidentifiability,
    teff_representative_seal,
)

TEFF_OWNER = "TEFF"
TEFF_CLAIM_TIER = "diagnostic_only"
TEFF_BUNDLE_KIND = "teff_representative"
