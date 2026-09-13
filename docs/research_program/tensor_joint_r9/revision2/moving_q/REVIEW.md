# MQ1/MQ2 independent review and root disposition

Scoped independent review PASS. The exact reviewed research note and source
remain unchanged; the note's pre-review wording is superseded by this disposition.
Root accepts MQ1/MQ2 as directly derived, independently reviewed mathematical
research under their stated nonempty-unit-fibre assumptions. This is neither
four-axis admission, novelty acceptance nor an observational/physical result.

The reviewer independently checked the T5 normalization, the nonunit STF
operator bound, cross-projection norm, unit-kernel-sphere Hausdorff bound,
orthogonal centre decomposition, radial square-root estimate, delta dependence,
sharpness reuse and raw-Q amplitude assumptions. No mathematical repair was
required. Its full report and strict result envelope are
`.agent-harness/runs/R9-THEORY-20260914/artifacts/moving_q_review/REVIEW_REPORT.md`
and `results/moving_q_review.json` in that same run.

Independent numerical evidence used a seven-dimensional Moore-Penrose
construction, 100 random unit-q checks, 80 nonunit normal-matrix checks, and
80 fibre pairs with 2048 sampled directions per side. No bound violation was
observed. These samples are lower distance witnesses, not numerical certificates
of the whole-set upper bound. Actual commands and captured output are preserved
in that review's `independent_checks_transcript.txt`; the evidence closeout did
not repeat the searches. The reviewer also reproduced the new 360-pair source
result; no prior DESI/SDSS/CF3 or fixed-ambient baseline was replayed.

The first new runner failed when JSON serialized NumPy boolean flags. Its source,
partial JSON and raw failure are preserved as `*_attempt1*`. The repair changes
only flag serialization and serializes before creating the output file. All
mathematical constants, cases, seed and the inherited 1e-10 tolerance are intact.
The final execution passed. This was an implementation failure, not a
counterexample or a reason to relax the analytical statement.

| Proposition / component | Direct proof | Numeric evidence | Four-axis machine admission | Independent review | Scientific admission |
|---|---|---|---|---|---|
| MQ1 global moving-q bound | Derived | Component and witness checks pass | Not performed / not claimed | Scoped PASS | HOLD |
| MQ2 interior Lipschitz bound | Derived | Interior witnesses pass | Not performed / not claimed | Scoped PASS | HOLD |
| Boundary 1/2 exponent | Prior S55 example reused | Four radial checks | Prior status unchanged | Reuse and scope checked | HOLD |
| Raw-Q normalization | Derived identity with both amplitudes >=a0>0 | Undefined-Q guard; independent analytic check | Not performed / not claimed | Scoped PASS | HOLD |

The rigorous upper bounds are the analytic set arguments. Exact replay of a
floating-point output and independent review are separate evidence grades.
The fixed-q support formula does not reconstruct the nonconvex unit fibre.
No plug-in q, epsilon regularization at Q=0, or empty-fibre finite comparison
has been admitted. Shared state-jet-anchor coverage and the full observed
selection/FP/group/CF3 law remain unavailable; alpha consumption is zero.
