#!/usr/bin/env python3
"""R54-A2: priority and attribution record of the theorems of R54-THM (no data, no numbers).

Writes RESULTS/R54_A2_ATTRIBUTION.json with novelty_checks for H-T6 and H-T8 and evidence_verification for the rows E51, E54 and
E63 to E69, in the formats of RESULTS/R54_L07_BENCHMARK.json. The records state what was read (web search and the primary pages named
in each note); a row is VERIFIED only when its claim was read in the primary source, IDENTIFIER_ONLY when only the bibliographic record
(and at most an abstract that does not carry the claim) was seen.

    python scripts/r54/run_r54_a2_attribution.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REL = "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116"
OUT = ROOT / REL / "RESULTS" / "R54_A2_ATTRIBUTION.json"
CHECK_DATE = "2026-11-16"
ROWS = ("E51", "E54", "E63", "E64", "E65", "E66", "E67", "E68", "E69")

NOVELTY_CHECKS = {
    "H-T6": {
        "question": "an identifiability or selection-rule statement for the kinematic variables by irreducible block (multipole, parity), including null channels",
        "searches": [
            "kinematic Hubble expansion multipoles irreducible decomposition identifiability parity vorticity not observable scalar observables selection rule (extended search)",
            "Gaia quasar proper motions vector spherical harmonics rotation glide anisotropic expansion E-mode quadrupole degeneracy identifiability",
            "cosmography Hubble multipoles dipole quadrupole luminosity distance parity even odd selection rule rotation not observable in distances Heinesen",
        ],
        "nearest_prior_art": [
            "arXiv:2010.06534 Heinesen 2020 (multipole decomposition of the general luminosity-distance Hubble law into a finite set of multipole coefficients; abstract read, "
            "no statement on vorticity seen)",
            "E50 Darling 2014 (anisotropic expansion as a curl-free E-mode proper-motion quadrupole)",
            "E51 Darling, Truebenbach, Paine 2018, sections 2.3 and 2.4 (a rotating universe appears as a B-mode proper-motion dipole; anisotropic expansion as an E-mode quadrupole)",
            "Mignard & Klioner 2012 vector spherical harmonics as used in E51 and Gaia frame papers (rotation = toroidal l=1, glide = spheroidal l=1)",
            "E18, E25 (patterns already published per observable)",
        ],
        "novelty": "LOW (searched): every per-observable pattern is published (E-mode quadrupole for shear, B-mode dipole for rotation, finite multipole content of the Hubble law); "
                   "the block-diagonal rank criterion per (multipole, parity) with the null channels stated as one theorem was not found in the searches run; it is Schur's lemma "
                   "applied to known patterns and is cited as an attributed synthesis, not as a new result",
    },
    "H-T8": {
        "question": "a statement on the number of sign changes of a shear history hidden from the temperature and E quadrupoles",
        "searches": [
            "Bianchi I shear history CMB quadrupole temperature E-mode polarization sign change hidden shear unconstrained (extended search)",
            "anisotropic expansion shear CMB temperature quadrupole cancellation time-dependent shear changes sign visibility polarization constraint",
        ],
        "nearest_prior_art": [
            "arXiv:2601.22351 Battye & Moss 2026, How isotropic is dark energy? (a Bianchi I shear history with a vanishing line-of-sight integral meets the temperature "
            "quadrupole bound by construction; per the search summary, sign-changing shear cancels the temperature integral while the polarization condition is visibility "
            "weighted and left to future work; no count of sign changes; only the abstract was read on the page)",
            "E03 Pontzen & Challinor 2007 (Bianchi CMB polarization; the quadrupole gives the tightest bound and some anisotropic models avoid it)",
            "E46 Basko & Polnarev 1980 (T and E quadrupole kernels)",
            "E68 Karlin & Studden 1966 (sign changes of functions annihilated by a Chebyshev system; textbook, not read)",
        ],
        "novelty": "LOW-MODERATE (searched): that a sign-changing shear can hide from the temperature quadrupole is published (Battye & Moss 2026); the lower bounds of one sign "
                   "change (T alone) and two (T and E) and the absence of an upper bound on any norm without a sign or family restriction were not found in the searches run; "
                   "the argument is the standard Chebyshev-system count (E68) on the classical kernels (E46) and is cited as an attributed re-derivation",
    },
}

EVIDENCE_VERIFICATION = {
    "E51": {"status": "VERIFIED", "source": "https://arxiv.org/abs/1807.06670 (full text, sections 2.3 and 2.4)",
            "note": "section 2.3 Rotation: a rotation of the universe 'would manifest as a B-mode dipole in the proper motion vector field'; section 2.4: triaxial "
                    "anisotropic expansion is an E-mode VSH quadrupole; the reading of the B-mode dipole as rotation is the paper's own"},
    "E54": {"status": "VERIFIED", "source": "https://projecteuclid.org/euclid.aos/1176350597",
            "note": "Gleser & Hwang, Ann. Statist. 15(4), 1351-1362 (1987), doi:10.1214/aos/1176350597; abstract: no confidence interval with positive confidence and "
                    "finite expected length for key parameters of errors-in-variables and related models, extended to confidence sets"},
    "E63": {"status": "IDENTIFIER_ONLY", "source": "https://www.scilit.net/publications/08a699e9b9ee4400aff189c505cc07f7",
            "note": "Kristian & Sachs, ApJ 143, 379 (1966), Observations in Cosmology: bibliographic record confirmed; the series expansion about the observer is known "
                    "here only from secondary sources; the paper was not read"},
    "E64": {"status": "VERIFIED", "source": "https://doi.org/10.1093/biomet/40.1-2.87",
            "note": "Scheffe, Biometrika 40, 87-110 (1953), A method for judging all contrasts in the analysis of variance: simultaneous inference for all linear contrasts"},
    "E65": {"status": "IDENTIFIER_ONLY", "source": "textbook (Springer, 3rd ed. 2005)",
            "note": "Lehmann & Romano, Testing Statistical Hypotheses: not read in this check; the claim is standard but rests on memory"},
    "E66": {"status": "IDENTIFIER_ONLY", "source": "textbook (Wiley 1982)",
            "note": "Muirhead, Aspects of Multivariate Statistical Theory: not read in this check"},
    "E67": {"status": "IDENTIFIER_ONLY", "source": "https://msp.org/pjm/1958/8-1/p14.xhtml",
            "note": "Sion, Pacific J. Math. 8(1), 171-176 (1958), doi:10.2140/pjm.1958.8.171: minimax theorem for quasi-concave-convex functions confirmed at the "
                    "publisher; Rockafellar, Convex Analysis (1970) not read, so the polar-body part of the row stays unverified"},
    "E68": {"status": "IDENTIFIER_ONLY", "source": "textbook (Interscience 1966)",
            "note": "Karlin & Studden, Tchebycheff Systems: not read in this check"},
    "E69": {"status": "IDENTIFIER_ONLY",
            "source": "https://www.cambridge.org/core/journals/econometric-theory/article/revising-beliefs-in-nonidentified-models/3EF418D43ADAAAF012398C49E4517AFD",
            "note": "Poirier, Econometric Theory 14(4), 483-509 (1998): identifier confirmed; the abstract states that some quantities have identical marginal prior and "
                    "posterior; the conditional-prior statement used by the row was not read in the full text"},
}


def main() -> int:
    if set(EVIDENCE_VERIFICATION) != set(ROWS):
        raise SystemExit("evidence rows of R54-A2 incomplete")
    payload = {
        "schema": "htt.r54.a2_attribution/1",
        "node": "R54-A2",
        "check_date": CHECK_DATE,
        "claim_tier": "C0",
        "status": "DONE_SCOPED_C0",
        "rows_checked": list(ROWS),
        "novelty_checks": NOVELTY_CHECKS,
        "evidence_verification": EVIDENCE_VERIFICATION,
        "limitations": [
            "web search and the primary pages named in each note only; no library access to the textbooks; a row stays IDENTIFIER_ONLY unless its claim was read in the source",
            "a search that finds nothing is not proof of absence; both novelty fields say 'searched' and the theorems are cited as attributed re-derivations",
        ],
        "provenance": {"script": "scripts/r54/run_r54_a2_attribution.py",
                       "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
