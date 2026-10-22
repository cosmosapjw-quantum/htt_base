# G13-B source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip:HTT_ALL_OBLIGATIONS_20261011/tasks/G13-B.json`
(package sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`; card bytes sha256
`6d9687595999e1ffe1af419b2f727e81467209f4a606f1c1425571c24c84ade6`; card `source_snapshot`
`a30d84c7918b54238a48fa62e2ef482f7e6d36fa`). Repository HEAD at recovery: `ece41e7c75fe47a697436bdf1bb47d28edaec5b7`.

Interrupted-attempt status: the task directory T did not exist when this author started
(`ls` returned "No such file or directory"); no partial SOURCE_RECOVERY, FROZEN_TARGETS, Lean source or
raw receipt from an earlier attempt was present, so nothing was inherited or deleted.

## Card scope (verbatim)

- scope_original: "S124–S126의 boundary limits, same-prior energy-only sharp interval, positive minimax."
- lean_steps: (1) classify lower-boundary Dirac and upper-boundary endpoint mixture of the moment
  feasible region; (2) boundary extrema via weak convergence of interior principal measures **or direct
  moment rigidity**; (3) for p>4 energy-only lower bound by convexity/Jensen and upper bound by chord
  majorant; (4) number–energy fibre ⊆ energy-only fibre for the same support/statistics/fugacity and
  interval nesting; (5) compose 0<L≤U and attainment with the C04 minimax including the L=U branch.
- acceptance: no 0/0 node evaluation at u=a, d=b; energy-only advantage stated only under the same
  prior; final typed statements match original quantifier/domain/measure/boundary branch.
- pitfall: general-p sharpness is limited to p=5,6 until G13-C.

## Recovered definitions (file:line)

| Item | Source | Used as |
|---|---|---|
| Common prior: 0<a<b, probability π on [a,b], m_p=∫y^p dπ, fixed statistics ξ, common log-fugacity η0, one normalization, one T_*; m3,m4 have the statistics factors removed | `docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md:18-31` (sha256 `bc055d39…0fe`, equal to the hash recorded in `cas/contracts/CAS-13.json` identity) | `NEFibre a b m3 m4`, `EFibre a b m4`: probability measures on ℝ with `∀ᵐ x, x ∈ Icc a b` and actual Bochner moments. ξ, η0, normalization, T_* enter only via the common factors removed from m3,m4 (spec :29; paper Eq. (120) "All multiplicative statistics and dimensional factors cancel"), so "same prior" = same (a,b) and same retained m4 in both fibres. |
| Strict interior S121 | `TEFF_INTERVAL_SPEC.md:35-40`; Lean `CAS13C02.StrictInterior` in G13-A source `MeasureExtremizerBridge.lean:88-94` | interior branch; `chord a b m3` copies the S121 right-hand side exactly as in `StrictInterior.upper` |
| Nodes u,d S122 | `TEFF_INTERVAL_SPEC.md:42-50`; G13-A `lower_node_existsUnique` / `upper_node_existsUnique` (`MeasureExtremizerBridge.lean:223-276`) | `LowerNode`/`UpperNode` predicates are verbatim the G13-A node conditions |
| Weights / principal measures S123 | `TEFF_INTERVAL_SPEC.md:52-61`; G13-A `lowerWeight`/`upperWeight` (:278-279), `twoDirac` (:810-811, weight on second node) | reused unchanged |
| L_p, U_p S124 | `TEFF_INTERVAL_SPEC.md:75-81` | `lowerEnd a m3 u p`, `upperEnd b m3 d p` (real exponent, `Real.rpow`); for p=5,6 bridged to ℕ powers by `Real.rpow_natCast` |
| Minimax S125 | `TEFF_INTERVAL_SPEC.md:83-93`; C04 `lean/Main.lean` `grstatTau`, `grstatEps`, `grstat_cas13_minimax` | imported unchanged; `FibreMinimax` lifts it to the measure fibre |
| Energy-only interval S126 | `TEFF_INTERVAL_SPEC.md:95-100` | `energyLower m4 p = m4^(p/4)`, `energyUpper a b m4 p` (verbatim formula) |
| Boundary rule | `TEFF_INTERVAL_SPEC.md:152-153`; `cas/contracts/CAS-13.json:87,100,108` ("MOM-BOUNDARY indeterminateform forbidden", "Boundary data by measurelimits, not0/0 nodes") | boundary branches are proved by direct moment rigidity of actual measures; no node formula is evaluated at u=a or d=b; negative control N1 exhibits the Lean junk value 0 of the 0/0 ratio |
| Same-prior rule | `TEFF_INTERVAL_SPEC.md:31`; `CAS-13.json:86,107,126` ("MOM-PRIOR samecomparisonprior") | all comparison theorems take one (a,b); negative control N2 shows nesting fails across different supports |
| Feasible region / boundary classification | Paper II App. E.1 p. 20: "Convexity of Y^{4/3} and its endpoint chord give Eq. (121), with equality corresponding respectively to a single temperature and an endpoint mixture." | T1, T2 |
| Exact minimax on the class via mixtures | Paper II App. E.1 p. 21: "Intermediate rates are available by mixtures of the two feasible extremal measures, so this is the exact minimax value on the stated class."; `supplements/TEFF_POSITIVE_BRIDGE.md:226` | `SharpInterval` image equality and T5 |
| Boundary data by limits | Paper II p. 13 after Eq. (125): "Boundary data are obtained by limits of the measures, not by evaluating indeterminate node formulas." | T2 uses the card's alternative "direct moment rigidity" (lean_steps item 2) instead of weak limits |
| Energy-only interval statement | Paper II p. 13 Eq. (126) "With only m4 retained under the same prior" | T3 |

Paper source: `/home/cosmosapjw/Dropbox/teff_novel/TEFF_PAPER_II_revised.pdf`, sha256
`299870d7174ed560393c87e8dd6193643a614e7a1185ab1be2c5c2dc73c9b5f9` (equals the hash in
TEFF_INTERVAL_SPEC.md:9). Pages 13–14 and 20–21 were extracted read-only with `pdftotext -layout`
into `/tmp/claude-1000/g13b/` (scratch, not part of the evidence).

## Reused reviewed Lean sources (imported unchanged)

| Module | Path | sha256 | Review |
|---|---|---|---|
| `Main` (C04) | `CAS-13/lean/Main.lean` | `5be0cd66d572f5d2523e052aaaff73f05cb2591e9102027f6409f44db396da97` | `c04_positive_interval_minimax_revalidation_v1_20261011/REVIEW.md` PASS_SCOPED |
| `MeasureExtremizerBridge` (G13-A) | `CAS-13/g13a_measure_extremizer_bridge_v1_20261011/MeasureExtremizerBridge.lean` | `a64f6c3c8745eb5b4f2634d2bf4369b6df9f300ba098ba72b9d5bd16720fda12` | `g13a…/REVIEW.md` PASS_SCOPED (bound to this final hash) |

Both are tracked in Git at HEAD and unmodified in the working tree. They are compiled from their original
paths into `raw/imports/*.olean` by `raw/run_compile.py` (attempts 01, 02), never copied or edited.

## Items not recovered / not attempted

- General real p>4 sharpness of [L_p,U_p] (Chebyshev principal representation): owned by G13-C; not
  claimed. Only endpoint-value nesting against the energy-only interval is proved for real p>4.
- Weak-convergence continuity of the interior principal measures toward the boundary: not needed
  (card allows direct rigidity) and not claimed.
- Statistics-factor maps N,E ↔ m3,m4 (polylog factors I^ξ_r(η0)): outside this moment problem; the
  spec states the retained m3,m4 already have the factors removed.

## Resume addendum (2026-10-13T20:50Z UTC, resuming author)

Provenance correction: this task was attempted first by an API worker and then by an in-session subagent,
both cut off by credit/rate limits. The statement above that "T did not exist" is the first-writing
author's own observation at its start; it is kept verbatim. Everything in T before attempt 04
(SOURCE_RECOVERY.md body, FROZEN_TARGETS.md sha256 `dc34b809502ec6be55eb66fe1becb930743217dbc4f95136147e6cb29d8a11a0`,
mtime 2026-10-13T11:51Z, lean/G13BBoundaryMinimax.lean draft mtime 11:58Z, raw/run_compile.py, receipts 01–03)
was produced by that interrupted earlier attempt. FROZEN_TARGETS.md was written before any proof compile
(receipts 01–02 are unchanged-import compiles, 03 is a `#check`-only API probe) and is kept unchanged.

The resuming author re-checked the frozen statements against the card (lean_steps 1–5, acceptance, pitfall)
and TEFF_INTERVAL_SPEC.md S121–S126 and lines 148–156 (sha256 `bc055d39…0fe`, unchanged) and found them
faithful: boundary branches use direct moment rigidity (card lean_step 2 alternative), no 0/0 node
evaluation, energy-only comparisons share one (a,b) and one m4, interior sharpness only for p = 5, 6.
A whitespace-normalized textual comparison of all 26 frozen theorem signatures and 14 frozen definitions
against the compiled source found no differences.

Resume-time repository HEAD: `4dbe588698f15eb0a93df657d5bc7b5d0acd1e06` (earlier attempt recorded `ece41e7c…`).
Both imported sources are still tracked and clean in the working tree, with the hashes listed above.

Resume edits to the draft (only proof scripts changed; no statement changed):
attempt 04 failed on the unknown Mathlib name `div_add_div_same` (two places, `chordE_le`/`chordE_lt`)
and a consumed hypothesis `hreg` in `region_exact`; replaced by `ring` and by `have h3 := hreg.1`.
Attempt 05 compiled (exit 0); attempt 06 axiom audit (exit 0).
