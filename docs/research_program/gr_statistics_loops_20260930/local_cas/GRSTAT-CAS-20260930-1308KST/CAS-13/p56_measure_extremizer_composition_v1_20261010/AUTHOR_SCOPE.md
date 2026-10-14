# T02 author scope: conditional measure composition

The pinned Lean kernel checked `CAS13MeasureComposition.p5_p6_measure_composition`
with exit code 0. Independent review is pending. The exact source SHA-256 is
`02f09b7f8ec332418d002a80e8f6b1f292a203ada30e01645f940eee9c0df56b`.

The theorem type is
`LowerComposition 5 ∧ UpperComposition 5 ∧ LowerComposition 6 ∧ UpperComposition 6`.
The compiler prints the complete definitions of both composition propositions and
`Admissible` in `RAW/compile_attempt_03.stdout`; these expose all quantifiers,
support, integrability, moment and contact hypotheses.

## Assumptions and conventions

The variables are real and dimensionless, following the admitted C02/C03 inputs.
There is no spacetime, tetrad, transfer, or harmonic convention in this theorem.
`moment μ p` is the real Bochner integral `∫ x : ℝ, x^p ∂μ` against an actual
`MeasureTheory.Measure ℝ`. An arbitrary input measure must be a probability measure
supported almost everywhere on its stated closed interval, and the third, fourth,
and p-th power functions must be integrable. Thus an undefined integral is not
silently used as a moment. Third and fourth moments are explicitly fixed.

C03's lower or upper pointwise Hermite inequality is an explicit hypothesis on
the entire interval, not a derived polynomial sign fact here. The Hermite function
is exactly `c0 + c3*x^3 + c4*x^4`. Linearity and probability normalization prove
that its integral is `c0 + c3*m3 + c4*m4`.

The actual measure is
`twoDirac w a u = ENNReal.ofReal (1-w) • Measure.dirac a + ENNReal.ofReal w • Measure.dirac u`.
Its probability theorem requires `0 ≤ w` and `w ≤ 1`, so `ofReal` does not truncate
a negative weight. Its integral is proved to equal `(1-w)*f a + w*f u`; arbitrary
real-valued functions are integrable on this finite-support measure. The
attainment theorem uses the stated weighted third/fourth moment equations and
the two exact node contacts. The composition wrappers additionally require both
nodes to belong to the stated interval and prove `Admissible` for their measure.
This establishes probability normalization, support, all required integrability,
and moment matching, alongside the bound and attained equality.

## Physics/math audit verdict

| Item | Status | Scope |
|---|---|---|
| Probability normalization | Kernel checked | Nonnegative weights sum to one |
| Hermite integral | Kernel checked | Uses explicit third/fourth integrability and moment identities |
| Lower/upper signs | Conditional | Supplied C03 pointwise inequalities, transported with `integral_mono_ae` |
| Attainment | Kernel checked | Equality uses weighted moments and exact contacts |
| Interval feasibility | Kernel checked | Supplied node membership gives a.e. support |
| Boundary handling | No divided formula used | Endpoint weights are allowed in the generic finite-measure theorem; no strict C02 0/0 formula is substituted |
| General p scope | Conditional algebra only | Generic natural-number transport gives p=5,6 wrappers; no general-real-p Hermite certificate is asserted |
| Scientific implications | HOLD | No geometry, family, transfer or observational claim |

The controlling assumptions are present in the theorem statement. Dimensions and
sign orientation agree with the admitted dimensionless moment convention: lower
Hermite values integrate to a lower bound, and upper values to an upper bound.
Degenerate equal nodes or weights zero/one pose no measure-theoretic division;
the original strict-interior node formulas and their feasibility remain separate.
No extra C02/C03 theorem is claimed from merely reading their admitted inputs.

## Kernel execution and axiom audit

Exact cwd: `/home/cosmosapjw/lean_oracles/viii_oracle`.

Exact argv:

```text
/home/cosmosapjw/.elan/toolchains/leanprover--lean4---v4.31.0/bin/lake env lean /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/p56_measure_extremizer_composition_v1_20261010/MeasureComposition.lean
```

Observed Lean is 4.31.0, commit
`68218e876d2a38b1985b8590fff244a83c321783`; mathlib is at
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` in that build cwd.
The third attempt passed with empty stderr and no compiler warnings.
`#print axioms` for `twoDirac_probability`, `integral_twoDirac`,
`lower_transport`, `upper_transport`, `twoDirac_attainment`,
`twoDirac_admissible`, and the final composite theorem returned only
`[propext, Classical.choice, Quot.sound]` for each declaration.
The final source introduces no custom axiom, `sorry`, or `admit`.

The raw first and second compile failures remain in their original stdout/stderr
files. Attempt 1 found a function-elaboration mismatch in `integral_hermite`;
explicitly typed lambda integrability facts fixed it. Attempt 2 found the missing
`Measure.` qualifier on `ae_smul_measure`; the final source uses the qualified
name and the current `probReal_univ` lemma. These were proof/API failures, not
mathematical counterexamples. Hashes, exit codes, and exact theorem interfaces
are recorded in `RETURN.json`.

Requested author runtime, as explicitly supplied by the parent, is
`gpt-6.1-sol/high`. Observed author model/effort remain `UNKNOWN` because no direct
runtime observation was available. SymPy, SageMath/Singular, and Wolfram/xAct were
not needed for this packet's measure-theoretic proof obligation.

## Claim-tier implications and remaining holds

Safe statement: the successor's conditional p=5,6 probability-measure transport
and two-Dirac attainment family has compiled and has a clean standard-axiom audit.
`FORMALLY_CHECKED` status requires scoped independent review of the source hash
above. No independent review is self-issued in this author return.

C04 relative-minimax/global minimax was not used. Its historical acceptance,
historical four-axis adjudication, scientific admission, physical residual/error,
catalogue/covariance, and native Bianchi-family claims remain unchanged and HOLD.
The proof does not construct C02 interior nodes, solve C03 interpolation
coefficients, or manufacture missing physical evidence.

Only the four owned path classes from `DELEGATION_PACKET.json` were written.
Existing dirty/untracked files were preserved. No stage, commit, push, task-card
mutation, or external publication was performed. The final candidate is ready
for the parent's separate read-only reviewer; there is no author-side blocker.
