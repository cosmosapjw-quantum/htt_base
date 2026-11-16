# R54 final decision (PR-R57, 2026-11-16)

**Decision: BOUNDED_NOTE_EXTENDED.** Claim tier C0. The programme stops here; no further research or audit-only loop is opened.

## Independent decision-gate review

Reviewer: decision-gate reviewer (physmath-research-harness:decision-gate-reviewer) (independent of the author). Recommended decision: BOUNDED_NOTE_EXTENDED (conditional on RC-01 to RC-03).

| row group | evidence | validity | novelty | testability | robustness | risk |
|---|---|---|---|---|---|---|
| Benchmark | PROMOTE | HOLD | REJECT | PROMOTE | HOLD | PROMOTE |
| CF4 estimator and body | PROMOTE | PROMOTE | HOLD | PROMOTE | PROMOTE | HOLD |
| CF4 survey zero point, hemisphere step, excess | PROMOTE | HOLD | HOLD | PROMOTE | HOLD | HOLD |
| Counts | PROMOTE | REJECT | REJECT | HOLD | HOLD | REJECT |
| Joint frames and identification | PROMOTE | HOLD | HOLD | HOLD | HOLD | HOLD |
| L1 E lane | HOLD | REJECT | REJECT | PROMOTE | REJECT | REJECT |
| L1 T lane | PROMOTE | PROMOTE | HOLD | PROMOTE | PROMOTE | PROMOTE |
| L1 functionals and calibration | PROMOTE | PROMOTE | HOLD | PROMOTE | PROMOTE | HOLD |
| R54 contribution as a whole | PROMOTE | HOLD | HOLD | PROMOTE | HOLD | HOLD |

Required changes and their resolution:
- RC-01 (critical): Relabel the E lane DIAGNOSTIC for the manuscript; quote no Sigma_E or T+E number as a limit. Resolution: APPLIED: claim-table row 'L1 E lane' (diagnostic; circular floor), report section 7.3 note, R54-L06 E_lane string, R54-L07 B01 reason; the R54-L02 rule outcome stays recorded in its result as computed.
- RC-02 (critical): H-L2a from REJECT to HOLD (kill criterion power >= 0.8 not evaluated; power 0.20); quote the mock-only tails. Resolution: APPLIED: hypothesis override H-L2a = HOLD from this review record; claim row 'L2 counts' lists both tails, the power and the reproductions.
- RC-03 (critical): Mark the R53 rows built on the R36/H03/R52 CF4 operator and the unlabelled R53 shear bound as superseded. Resolution: APPLIED: three 'supersedes' rows in MANUSCRIPT_CLAIM_TABLE_R54.md; the R53 file itself is outside the allowlist and is not edited (DV-L08-1).
- RC-04 (major): Add a row for the constant CF4 quadrupole (H-L5h). Resolution: APPLIED: row 'L5 CF4 constant quadrupole (H-L5h)', HOLD, not for the abstract.
- RC-05 (major): Separate the pooled polar LCDM-only tail with its caveats; the five-view Pi only under the same restriction. Resolution: APPLIED: row 'L6 pooled polar tail'.
- RC-06 (major): Survey zero point: degenerate with the FP hemisphere step; north fractions; white versus body z. Resolution: APPLIED: row 'L5 CF4 survey zero point'. The published CF4 FP calibration is not cited (not verified in this session).
- RC-07 (major): B01 to NOT_REPRODUCED and tighter tolerance; B02 NOT_COMPARABLE; B09 labelled re-derivation. Resolution: PARTLY APPLIED: B02 rescored NOT_COMPARABLE; B09 labelled 're-derivation (identity)'; B01 keeps REPRODUCED under the spec's factor-10 tolerance because changing a tolerance after the result is forbidden; its reason now states 3x weaker, FFP10-only E covariance, DIAGNOSTIC E lane.
- RC-08 (minor): Present shear: calibrated L01 values; T+E only with the DIAGNOSTIC label. Resolution: APPLIED.
- RC-09 (minor): Hemisphere step: the scan tail belongs to the method-level step; FP_SDSS southern count; z-half split. Resolution: APPLIED.
- RC-10 (minor): Excess row: 'not supported by the decision check' instead of 'rejected'. Resolution: APPLIED; H-L5a keeps the decision recorded by its R54-L04 decision check (REJECT as a statement of excess over the body), with the wording note in the table.
- RC-11 (minor): Reconcile E-lane and H-L2a statuses in the report. Resolution: APPLIED: section 7.7 records the review overrides; sections 1-6 are the cloud record and stay as written.
- RC-12 (minor): Novelty entries for H-L5f and the exact body; do not cite E35. Resolution: APPLIED: R54-L07 novelty_checks H-L5f (LOW, E41/E37; E36 NOT_FOUND); E35 keeps its NOT_FOUND note.

## Basis

- R54 corrects the R53 bounded note: the CF4 linear estimator is biased, the exact pair-sum body is wider than the ideal-sky body, and a present-day shear needs a model label; without these corrections the R53 note would print superseded CF4 numbers.
- What survives is C0 and diagnostic: an experiment-stable T lane, CF4 catalogue-level diagnostics whose class depends on the zero-point model, and an unresolved hemisphere step and constant quadrupole.
- The E lane is DIAGNOSTIC for the manuscript; the count excess is HOLD (underpowered); no Sigma_E, count or pooled-tail number enters the abstract.
- The benchmark has no WIN and the novelty checks are LOW or LOW-MODERATE, so neither a methods-advantage nor a new-signal framing is used.
- Strongest argument against: the new content is thin (re-derived kernels, a known estimator bias, reproduced count dipoles); a referee may ask for no paper. The note is kept only as a correction-and-diagnostics extension of the R53 note.
- No further research or audit-only loop is opened (stop rule of RESEARCH_DAG.json).

## Bound numbers

- Benchmark: WIN 0, TIE 2, LOSS 0, NOT_COMPARABLE 7.
- CF4: robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL; hemisphere step class UNRESOLVED; FP survey offset -0.074 +- 0.026 mag.
- Counts: calibrated excess tails 0.309 (Quaia), 0.421 (NVSS).
- CMB: T lane PIPELINE_STABLE; E lane CLAIMABLE only with a floor 10.6x the FFP10 B2 variance; LOO intervals SUPERSEDED.
- Joint frames: tilt closure p = 0.0865; omega unidentified.

Claim rows: MANUSCRIPT_CLAIM_TABLE_R54.md. Every number above is generated from RESULTS/*.json.
