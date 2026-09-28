"""PR-124 typed MES theorem/convention authority (the delivered successor
``mes.typed-successor.pr124`` that PR-122 reserved).

This module carries, per MES branch:

- the exact coefficient triple (strings of exact rationals);
- the source authority (arXiv/DOI or scan authority, page/equation, and the
  SHA-256 of the archived primary-source bytes where accessible);
- the convention translation (eps definitions, SAG observer-motion
  convention, C1/C2 reduction, W^2 normalization);
- the REAL independent derivation lineages with the inflation-exclusion
  rule (same implementation fingerprint collapses; a second engine never
  adds a lineage);
- the physical assumption uncertainty as its own field.

It also implements the authority *verifier*: authorization is derived from
exact receipt bytes (the generated PR-124 artifacts), never from
caller-supplied status strings. ``MesAuthorityVerification`` can only be
instantiated by running the full byte-level verification; the PR-122
successor pointer requires that instance to become AVAILABLE.

Claim discipline: this authority is domain/frame-conditional derived
mechanics at roadmap_rescue_v1:C1. It validates no observed scientific
result, changes no remediation disposition, and never turns engine
agreement into derivation independence (they are reported separately).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

SCHEMA_VERSION = "pr124.mes_theorem_authority.v1"

AUTHORITY_TABLE_PATH = "docs/generated/pr124_mes_authority_table.json"
CAS_CONTRACT_PATH = (
    "docs/generated/pr124_cas/CAS_CONTRACT_PR124_MES_GEODESIC.json"
)
CAS_ADJUDICATION_PATH = "docs/generated/pr124_cas_adjudication.json"
D2_RECEIPT_PATH = "docs/generated/pr124_d2_authority_receipt.json"
LINEAGE_RECEIPT_PATH = "docs/generated/pr124_lineage_receipt.json"

MINIMUM_LINEAGES_FOR_VERIFIED = 2

ARCHIVED_PRIMARY_SOURCES = {
    "mesa": {
        "path": "docs/audits/mes_primary_sources/mesa_astro-ph_9501016_PRD51_1525.txt",
        "sha256": "d500ffeef60f1f006393b7b2a21823b51bc4c9c9b41b7fb983f0393ce800217e",
        "citation": "Maartens, Ellis & Stoeger 1995a, PRD 51, 1525 (arXiv:astro-ph/9501016)",
    },
    "companion": {
        "path": "docs/audits/mes_primary_sources/companion_astro-ph_9510126_deltaT.txt",
        "sha256": "7ae6cf9288027338829d9964138596c2b909d49471193fa008d1c966eaab9765",
        "citation": "Maartens, Ellis & Stoeger 1996 companion (arXiv:astro-ph/9510126)",
    },
    "sag1997": {
        "path": "docs/audits/mes_primary_sources/sag1997_astro-ph_9904346_ApJ476_435.tex",
        "sha256": "00bb2c7c485ffb14433a90dae2d5d7709fbecd9c4eef986ec27d72f7dae5370e",
        "citation": "Stoeger, Araujo & Gebbie 1997, ApJ 476, 435 (arXiv:astro-ph/9904346)",
    },
}

CONVENTION_TRANSLATION = {
    "eps_definition": (
        "eps_L are the covariant CMB temperature multipole bound amplitudes "
        "of the linearized almost-EGS hierarchy (MESa eqs 51/52 context)"
    ),
    "eps1_attribution": (
        "SAG observer-motion convention: the observed CMB dipole is the "
        "observer's peculiar motion, so the residual cosmological dipole "
        "bound is eps1 = 0 (SAG 1997 eq 12; MESa notes the same limit)"
    ),
    "c1_c2_reduction": (
        "C1: a spatial-gradient bound is <= the same-order time-derivative "
        "bound; C2: k-th time derivatives reduce by (1/(Theta t_R))^k with "
        "Theta t_R ~ 3; net factor (1/3)^d per total derivative order d"
    ),
    "w2_normalization": "W^2 = omega_ab omega^ab / (6 H^2) (registered code convention)",
    "ceiling_map": "W2_max = (3/2) B_omega^2; Sigma2_max = (3/2) B_sigma^2",
}

# Registered derivation lineages. ``implementation_fingerprint`` is the
# inflation-exclusion key: identical fingerprints collapse to ONE lineage
# regardless of how many engines re-evaluate them.
BRANCHES: dict[str, dict] = {
    "MES_G_SIGMA": {
        "congruence": "geodesic",
        "status": "VERIFIED",
        "coefficients_exact": ("5/3", "3", "3/7"),
        "sources": [
            {**ARCHIVED_PRIMARY_SOURCES["mesa"], "equation": "eq (59); raw eq (51)"},
        ],
        "lineages": [
            {
                "lineage_id": "mesa_published_eq59",
                "kind": "published_paper",
                "implementation_fingerprint": "arXiv:astro-ph/9501016:eq59",
            },
            {
                "lineage_id": "in_repo_c1c2_reduction_from_eq51",
                "kind": "in_repo_reduction",
                "implementation_fingerprint": (
                    "htt/obsstat/egs3_mes_rederivation.py::reduce_raw_bound(_RAW_SIGMA)"
                ),
                "source_path": "htt/obsstat/egs3_mes_rederivation.py",
                "source_sha256": (
                    "8051e61e01cc7d2a6d321677d9027f6b2aa2ce5fe740abd59ae1754030f4ec6f"
                ),
            },
        ],
        "physical_assumption_uncertainty": (
            "C2 is an order-of-magnitude estimate (Theta t_R ~ 3); the bound "
            "is linear almost-EGS and diagonal-combination conditional"
        ),
    },
    "MES_G_OMEGA": {
        "congruence": "geodesic",
        "status": "VERIFIED",
        "coefficients_exact": ("10/3", "2/15", "0"),
        "sources": [
            {**ARCHIVED_PRIMARY_SOURCES["mesa"], "equation": "eq (60); raw eq (52)"},
            {**ARCHIVED_PRIMARY_SOURCES["sag1997"], "equation": "eq (4)"},
        ],
        "lineages": [
            {
                "lineage_id": "mesa_published_eq60",
                "kind": "published_paper",
                "implementation_fingerprint": "arXiv:astro-ph/9501016:eq60",
            },
            {
                "lineage_id": "sag1997_published_eq4",
                "kind": "external_citing_source",
                "implementation_fingerprint": "arXiv:astro-ph/9904346:eq4",
            },
            {
                "lineage_id": "in_repo_c1c2_reduction_from_eq52",
                "kind": "in_repo_reduction",
                "implementation_fingerprint": (
                    "htt/obsstat/egs3_mes_rederivation.py::reduce_raw_bound(_RAW_OMEGA_MESA)"
                ),
                "source_path": "htt/obsstat/egs3_mes_rederivation.py",
                "source_sha256": (
                    "8051e61e01cc7d2a6d321677d9027f6b2aa2ce5fe740abd59ae1754030f4ec6f"
                ),
            },
        ],
        "physical_assumption_uncertainty": (
            "same C1/C2 regime as the shear branch; geodesic congruence "
            "(u_dot = 0) is load-bearing — the triple does not survive tilt"
        ),
    },
    "MES_G_ACCEL": {
        "congruence": "geodesic",
        "status": "VERIFIED_STRUCTURAL",
        "coefficients_exact": ("0", "0", "0"),
        "sources": [
            {**ARCHIVED_PRIMARY_SOURCES["mesa"], "equation": "p.123 (geodesic flow, u_dot = 0)"},
            {**ARCHIVED_PRIMARY_SOURCES["sag1997"], "equation": "assumption set (no acceleration bound)"},
        ],
        "lineages": [
            # A structural ABSENCE claim (no acceleration bound) has no raw
            # published bound to reduce, so only distinct PUBLICATIONS count
            # as lineages here — an in-repo restatement re-citing MESa p.123
            # is the same origin and would inflate the count.
            {
                "lineage_id": "mesa_geodesic_assumption",
                "kind": "published_paper",
                "implementation_fingerprint": "arXiv:astro-ph/9501016:p123-geodesic",
            },
            {
                "lineage_id": "sag1997_geodesic_assumption_set",
                "kind": "external_citing_source",
                "implementation_fingerprint": (
                    "arXiv:astro-ph/9904346:assumption-set-no-accel-bound"
                ),
            },
        ],
        "physical_assumption_uncertainty": (
            "structural: u_dot = 0 removes the dipole acceleration source, "
            "so no acceleration ceiling exists on the geodesic branch "
            "(A^2 = 0); both lineages are publications carrying the geodesic "
            "assumption set (SAG 1997 is Stoeger-coauthored — correlated "
            "authorship disclosed)"
        ),
    },
    "MES_NG_OMEGA": {
        "congruence": "non_geodesic",
        "status": "UNVERIFIED_PRINT_ONLY",
        "coefficients_exact": ("3/4", "2", "2/7"),
        "sources": [
            {
                "path": None,
                "sha256": None,
                "citation": "Maartens, Ellis & Stoeger 1995b, PRD 51, 5942 (print-only; no accessible archive)",
                "equation": "registered as Thm 3.2 / eq 3.12 numbering of an in-house reconstruction; appears in no accessible source",
            },
        ],
        "lineages": [
            {
                "lineage_id": "mesb_print_only",
                "kind": "published_paper",
                "implementation_fingerprint": "PRD-51-5942:print-only",
            },
        ],
        "physical_assumption_uncertainty": (
            "non-geodesic (tilted) congruence; the registered triple is not "
            "reconstructable from any accessible source and the in-house "
            "reconstruction was REFUTED (rev-r190); never a live ceiling"
        ),
    },
    "MES_NG_ACCEL": {
        "congruence": "non_geodesic",
        "status": "UNVERIFIED_PRINT_ONLY",
        "coefficients_exact": ("3/4", "1", "3/14"),
        "sources": [
            {
                "path": None,
                "sha256": None,
                "citation": "Maartens, Ellis & Stoeger 1995b, PRD 51, 5942 (print-only; no accessible archive)",
                "equation": "no acceleration bound appears in any accessible primary source",
            },
        ],
        "lineages": [
            {
                "lineage_id": "mesb_print_only",
                "kind": "published_paper",
                "implementation_fingerprint": "PRD-51-5942:print-only",
            },
        ],
        "physical_assumption_uncertainty": (
            "both accessible primary papers are geodesic; an acceleration "
            "ceiling has no accessible derivation at all"
        ),
