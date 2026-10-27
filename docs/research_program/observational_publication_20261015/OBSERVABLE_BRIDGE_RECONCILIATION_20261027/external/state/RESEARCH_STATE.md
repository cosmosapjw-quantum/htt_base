# RESEARCH_STATE

PROJECT: HTT observable-bridge research run (htt_base, commit a55036ad, PUBLICATION_ACCELERATION_20261025)
VERSION: 0.1
CURRENT_PHASE: evidence-acquisition
LAST_UPDATED: 2026-10-26
INTENSITY: deep (one full cycle in one session)

## Primary question

PRIMARY_RQ: Which follow-up research, external data products and theoretical foundations are required to connect the HTT mathematical/statistical results (STF morphology, contraction/chirality geometry, conditional identified sets, finite-window discrepancy frontiers, finite optical inverse, foreground-moment compensators, Bianchi algebraic images) to concrete, standard observables — and which of the 29 residual HOLDs can be cleared by obtainable data or established theory rather than by new contracts?

## Subquestions

- SQ-HK (local optical lane, P3/P6/P4; HOLDs H02,H04-H06,K03-K06,V04-V06,R23-CONGRUENCE): Does the HTT local magnitude field f = -kappa log(1+q), q(n) = d.n + S:nn (d = -A/(cH), S = sigma/H, kappa = 5/ln10) coincide with the leading orders of the covariant luminosity-distance multipole expansion (Heinesen 2021; Maartens et al. 2024)? Which published estimators (anisotropic-H0 multipoles from SNe/Tully-Fisher; minimum-variance bulk-flow/shear moments from PV catalogues) are the "familiar observables" for d and S, and what empirical PV/selection/calibration law do they already supply?
- SQ-L (Planck low-ell lane, P2; HOLDs L03-L06): Which released simulation sets give release-matched, same-realization FULL/HM/OE (or A/B) CMB+noise+foreground-residual genealogies with a fixed selection protocol, so that finite-MC rarity and look-elsewhere corrections of low-ell morphology statistics can be calibrated? Is PR4/NPIPE (600 sims, A/B splits) the obtainable resolution, and what does the "release-matched" requirement cost?
- SQ-B (Bianchi lane, P5; HOLDs B02-B05, R23-ATLAS): What all-m polarized T/E/B Bianchi transfer products (atlases, codes, likelihood pipelines) exist or can be built (ANICOSMO / Saadeh et al.; Pontzen-Challinor; own BASS solver), and what is the minimal family-identification experiment that does not require a native solver inside htt_base?
- SQ-K (astrometric lane, P6; HOLDs K03,K05): What is the proper-motion response of a quasar sky to sigma_ab, omega_a, A_a in a given frame (vector-spherical-harmonic glide/rotation/quadrupole), and which Gaia DR3/CRF3 and VLBI/ICRF3 products (VSH fits, covariance, NNR conventions) supply the nonradial law and cross-source covariance?
- SQ-SN (R23-SN, V04): Which Pantheon+/SH0ES release files (nominal SALT2 surface, .nml, FITRES binding) are publicly available to bind the four parity bounds, and what is the fallback?
- SQ-CF4 (R26 NO_GO, H02): What do the CF4 (Tully et al. 2023) table columns DMav/DMzp mean, is the frozen equation's 0.137 offset a convention error, and what group-calibration/PV-error law does CF4 publish?
- SQ-FG (bandpass lane, P2; R31 rank 0): Under which physically motivated foreground moment classes (Chluba-Hill-Abitbol moment expansion; Vacher et al.; Planck 2018 IV residuals) is the free second-order relaxation over-permissive, so that a bounded moment budget becomes an informative identified set?

## Scope

IN_SCOPE: literature acquisition with primary sources; claim audit; candidate bridge hypotheses; adversarial review; symbolic validation of bridge formulas; verification design; provisional decision; requirements list per HOLD.

OUT_OF_SCOPE: any new numerical run on raw sky maps or catalogues; changing original42 acceptances; native Boltzmann/ODE solver execution; novelty proof of the QO theorem; paper submission.

## Hypothesis status

ACTIVE_HYPOTHESES: (filled in hypothesis-space phase)

PROMOTED:

ON_HOLD:

REJECTED:

## Blockers

KEY_BLOCKERS: 29 residual HOLDs listed in POST_PUBLICATION_CHECKPOINT_20261026/README.md (copied verbatim into context).

MISSING_EVIDENCE: (filled in evidence-acquisition phase)

## Gate

CURRENT_COMPLETION_BAR: each SQ has at least one primary source or an explicit missing-evidence entry.

NEXT_GATE: claim-source-audit

NEXT_MINIMAL_ACTION: run arXiv/ADS/INSPIRE searches per SQ.

---
## Update 2026-10-26 (end of deep cycle, pending decision gate)

VERSION: 0.2
CURRENT_PHASE: decision-gate (independent subagent running) → closeout

PHASES_COMPLETED: evidence-acquisition (20 external sources, 11 internal evidence items; EVIDENCE_LEDGER.md), claim-source-audit (CLAIM_AUDIT.md; 4 demotions), hypothesis-space (6 families + reopened H-0; HYPOTHESIS_GRAPH.md), adversarial-review (subagent; review/ADVERSARIAL_REVIEW.md), physics-math-validation (T-01..T-11; VALIDATION.md; R32-01 Table I reproduced to ≤ 1e−6), verification-design (V-1..V-6; VERIFICATION_DESIGN.md), executed cheapest action V-1/8 (T-11).

ACTIVE_HYPOTHESES: H-0 (physical null: boost + bulk 1/z with mock covariance; added after review), H-1 (quadrupole half only), H-2, H-4, H-5
ON_HOLD (review roles): H-1 TRADEOFF, H-2 TRADEOFF, H-4 DEFENDED (conditional), H-5 NEEDS_MORE_EVIDENCE
INFORMATIVE_FAILURES: H-3 (astrometric bound on S), H-7 (𝔮_1 as sole depth law) → NEGATIVE_RESULTS N-001, N-002; also N-003 (d = −A/(cH) referent)

KEY_BLOCKERS (as refined by this cycle):
- B-1 The H03/P1/R32-05 covariance is a diagonal 250 km/s working metric; every "discrepancy", tail and η radius is conditional on it. A mock-derived correlated PV covariance is the single prerequisite shared by H-0, H-1, H-7 and by HOLDs H02/H04/H05/K04/V04.
- B-2 No CF4-independent velocity reconstruction reaches the outer windows (z ≳ 0.06); eigenframe tests are limited to 0.02–0.06.
- B-3 Atlas conventions (normalization, single-m frame, handedness, regular vs irregular, coupled vs decoupled) are unfixed; AniLoS execution not possible in this session.
- B-4 M-01 (NPIPE shared sky per index) unverified; PR4 lane redefines L03.
- B-5 Dimensional ρ for the bounded moment class needs an ℓ ≤ 5 foreground amplitude (sky consumption).

MISSING_EVIDENCE: M-01..M-07 (EVIDENCE_LEDGER.md) + M-08: regular/irregular and coupled/decoupled identity of the cached BIANCHI v1.1 fixture; M-09: CF4-footprint-aware mocks (method × sky) for H-1n.

NEXT_GATE: decision-gate result → DECISION_LOG.md → CLOSEOUT.md
NEXT_MINIMAL_ACTION: V-1 step 9 / H-0 cheapest discriminator (mock covariance + 1/z_w column refit of the saved 12 dipole coordinates).

---
## Update 2026-10-27 (cycle 1 closed)

VERSION: 1.0
CURRENT_PHASE: closeout complete → next cycle `research-contract` (V-0(b) mock-covariance contract)
29-HOLD source: `git show a55036ad:docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/POST_PUBLICATION_CHECKPOINT_20261026/README.md`

PROMOTED (to verification packages): H-0 (V-0; (a) executed as T-12, (b) pending), H-2 (V-2; manifest-first)
ON_HOLD / REOPENED: H-1 → H-1Q (quadrupole only), H-4 (M-01), H-5 (dimensional ρ)
REJECTED: H-3 (as package; law kept for K03), H-7 (standalone; 𝔮_1 column inside V-0)
HOLD MAPPING: DATA 5 / THEORY 2 / REDEF 16 / PROC 6 (review/DECISION_GATE.md §4)
DELIVERABLES: RESEARCH_RUN_REPORT.md; state/{EVIDENCE_LEDGER, CLAIM_AUDIT, HYPOTHESIS_GRAPH, VALIDATION, VERIFICATION_DESIGN, NEGATIVE_RESULTS, DECISION_LOG, CLOSEOUT}.md; review/{ADVERSARIAL_REVIEW, DECISION_GATE}.md; validation/{validate_bridges.py, results.json, t11_h03_tomography.py, t11_results.json}
NEXT_MINIMAL_ACTION: gate list item 2 (ledger repair: boost law quote, Maartens 2024 full text, H_2 normalization) and item 3 (M-01 documentation check); decisive item 7 (mocks through the exact operators) needs a data request.
