# G13-C source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip:HTT_ALL_OBLIGATIONS_20261011/tasks/G13-C.json`
(package sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`; card bytes sha256
`e31d34b821f66ee3ec75558b3184b060a2464ec115277a65aac53529d7cfb15e`; card `source_snapshot`
`a30d84c7918b54238a48fa62e2ef482f7e6d36fa`). Repository HEAD at recovery:
`4dbe588698f15eb0a93df657d5bc7b5d0acd1e06` (branch `r2/02-cf4-provider-20261014`).

Interrupted-attempt status: the task directory T did not exist when this author started
(`ls …/CAS-13/g13c*` returned "No such file or directory"), so nothing was inherited or deleted.

## Card scope (translated from the Korean card text, not paraphrased beyond translation)

- title: "principal moment extremizer for every real p>4".
- scope_original: "the original all-real p>4 sharp interval theorem of S121–S125".
- existing_reuse: strict nodes/weights and the actual measure construction; the p=5/p=6 cases are reused
  only as separate verification examples.
- lean_steps: (1) for a>0 prove the real-power function, the needed smoothness and Wronskian-sequence
  positivity; (2) prove generalized Rolle / Hermite remainder or a direct Chebyshev moment-system theorem
  in the needed range; (3) obtain the support-wide sign of the lower/upper interpolants for every real
  p>4; (4) compose global extremality and attainment through the retained moments and actual measure
  integration; (5) extend the G13-B boundary and minimax results to the all-real-p theorem.
- acceptance: (i) a separate analytic implication from the Wronskian positivity calculation to the full
  moment theorem is proved; (ii) p is not restricted to naturals or a finite list; (iii) the final typed
  statement matches the original quantifiers, domain, measure and boundary branches; (iv) kernel build
  bound to the actual source/import identity, `#print axioms`, independent fresh review.
- pitfall: if the general Chebyshev theorem is absent from Mathlib, write the needed special theorem.
- tool_tasks: sympy "Wronskian 12p(p−3)(p−4)y^(p+1) and interpolation algebra candidates"; lean
  "generalized Rolle/ECT analytic lemma, real power, integral extrema".

## Recovered definitions (file:line)

| Item | Source | Used as |
|---|---|---|
| Common prior 0<a<b, probability π on [a,b], m_p=∫y^p dπ; same statistics/fugacity/normalization | `docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md:18-31` (sha256 `bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe`, equal to `cas/contracts/CAS-13.json:26`) | G13-B `NEFibre a b m3 m4` (`G13BBoundaryMinimax.lean:35-36`; probability measure, `∀ᵐ x, x ∈ Icc a b`, Bochner moments 3 and 4), imported unchanged; real moment `rmoment μ p = ∫ x, x ^ p ∂μ` (`Real.rpow`) from G13-B (`G13BBoundaryMinimax.lean:43`) |
| Oracle target m_p, p>4 | `TEFF_INTERVAL_SPEC.md:31` | `rmoment μ p` with `p : ℝ`, hypothesis `4 < p` |
| Strict interior S121 | `TEFF_INTERVAL_SPEC.md:35-40`; G13-A `CAS13C02.StrictInterior` (`g13a…/MeasureExtremizerBridge.lean:88-94`) | interior branch |
| Nodes S122 | `TEFF_INTERVAL_SPEC.md:42-50`; G13-B `LowerNode`/`UpperNode` (`g13b…/lean/G13BBoundaryMinimax.lean:55-63`); G13-A existence/uniqueness `lower_node_existsUnique`/`upper_node_existsUnique` (`MeasureExtremizerBridge.lean:223-276`) | reused unchanged |
| Weights / principal measures S123 | `TEFF_INTERVAL_SPEC.md:52-61`; G13-A `lowerWeight`, `upperWeight` (`MeasureExtremizerBridge.lean:278-279`), `lower_weight_moments`/`upper_weight_moments` (:281-350), `twoDirac` (:810-811) | reused unchanged |
| L_p, U_p S124 | `TEFF_INTERVAL_SPEC.md:75-81`; G13-B `lowerEnd`/`upperEnd` (`G13BBoundaryMinimax.lean:65-71`, real exponent) | reused unchanged |
| Target statement "L_p ≤ m_p ≤ U_p for every measure in the same retained-moment class, with equality attained by the displayed measures" | `TEFF_INTERVAL_SPEC.md:81`; Paper II Prop. 14, Eq. (124), p. 13 | `interior_real_bounds`, `interior_real_sharp` |
| Minimax S125 | `TEFF_INTERVAL_SPEC.md:83-93`; C04 `CAS-13/lean/Main.lean` `grstatTau`, `grstatEps`, `grstat_cas13_minimax` | imported unchanged; `RFibreMinimax` lifts it to the measure fibre with `rmoment` |
| Energy-only S126 | `TEFF_INTERVAL_SPEC.md:95-100`; G13-B `energyLower`, `energyUpper`, `endpoint_strict_nesting` | nesting extended to real p>4 |
| Wronskian SE2 `W(1,y^3,y^4,y^p)=12p(p−3)(p−4)y^{p+1}>0` and the warning that a Wronskian alone is not a proof | `TEFF_INTERVAL_SPEC.md:103-108`; Paper II App. E.1 Eq. (E2), p. 21 ("The functions 1, y³, y⁴, y^p form an extended Chebyshev system on a positive interval when p > 4 … The lower-order Wronskians are also positive. The principal-representation result [31] identifies the lower measure at {a,u} and the upper measure at {d,b}, proving the interval for all p > 4.") | T1 (Wronskian computation) and T2/T3 (separate analytic implication) |
| Interpolant Q = c0+c3y³+c4y⁴ with Q(a)=a^p, Q(u)=u^p, Q'(u)=p u^{p−1} | `TEFF_INTERVAL_SPEC.md:112-121` (stated there for p=5,6; Paper II App. E.1 p. 21 "We let Q_{p,a,u}(y)=c0+c3y³+c4y⁴ interpolate y^p at a, u and its first derivative at u") | `interp A U p` for real p; derived independently here (Cramer solve, determinant `interpDet A U = −(U−A)²(U²+2AU+3A²)`), not read from another axis |
| Upper certificate "replace (a,u) by (b,d)" | `TEFF_INTERVAL_SPEC.md:147`; Paper II p. 21 | `interp b d p` (simple node b, double node d) |
| Boundary data by limits / no 0/0 node formulas | `TEFF_INTERVAL_SPEC.md:152-153`; `cas/contracts/CAS-13.json:87,100,108`; Paper II p. 13 | boundary branches by direct rigidity (G13-B collapse theorems, card lean_step 2 alternative of G13-B), now stated with `rmoment` for every real p |
| Same prior | `TEFF_INTERVAL_SPEC.md:31`; `CAS-13.json:86,107,126` | every comparison theorem takes one (a,b) and one (m3,m4) |
| p=5,6 certificate is not a general-p proof | `TEFF_INTERVAL_SPEC.md:154`; `CAS-13.json:99,120` | the general proof below never uses the p=5,6 polynomial certificates; p=5,6 appear only via the ℕ-consistency corollary |
| Proposition 14 wording "For p > 4 and the class (119) with the data (121), L_p ≤ m_p, U_p ≥ m_p … The two bounds are attained by the indicated two-point measures" | Paper II p. 13, Eqs. (119)–(125) | frozen interior targets |

Paper source: `/home/cosmosapjw/Dropbox/teff_novel/TEFF_PAPER_II_revised.pdf`, sha256
`299870d7174ed560393c87e8dd6193643a614e7a1185ab1be2c5c2dc73c9b5f9` (equals `TEFF_INTERVAL_SPEC.md:9`).
Pages 13 and 20–21 were extracted read-only with `pdftotext -layout` into `/tmp/claude-1000/g13c/`
(scratch, not evidence). Other hashes: `cas/COMMON_SPEC.md` `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`
(equals `CAS-13.json:22`); `cas/contracts/CAS-13.json` `4e8bdb6c3d0c789e8dc7fbb647a982849ac13653bcabe41820c41be0c360b89b`;
`supplements/TEFF_POSITIVE_BRIDGE.md` `f04d96fe4b7dbee5fc946e10863d602c46399ca15723226ce6b63d4ab53ff21b`
(equals `CAS-13.json:32`; line 226 restates Prop. 14).

## Reused reviewed Lean sources (imported unchanged)

| Module | Path | sha256 | Review | olean sha256 (this T) |
|---|---|---|---|---|
| `Main` (C04) | `CAS-13/lean/Main.lean` | `5be0cd66d572f5d2523e052aaaff73f05cb2591e9102027f6409f44db396da97` | `c04_positive_interval_minimax_revalidation_v1_20261011/REVIEW.md` | `61488abac058025ef2191841f5d5f80132952ae92072d954dab646e26c14cb94` |
| `MeasureExtremizerBridge` (G13-A) | `CAS-13/g13a_measure_extremizer_bridge_v1_20261011/MeasureExtremizerBridge.lean` | `a64f6c3c8745eb5b4f2634d2bf4369b6df9f300ba098ba72b9d5bd16720fda12` | `g13a…/REVIEW.md` | `8c53c481cdd1cf7a885138529ebc5ec102187255b20efde554413f0f230f7122` |
| `G13BBoundaryMinimax` (G13-B) | `CAS-13/g13b_boundary_minimax_v1_20261013/lean/G13BBoundaryMinimax.lean` | `6d9a9d68bd279d677e0a501de04fb181de5c8071fee9616447c113570d8c6af1` (equals `g13b…/RETURN.json`) | `g13b…/REVIEW.md` PASS_WITH_NOTES | `1e5cf7c39e43c637ee15a8656b139e8d57cb26af3bbdb0f8c6164b2a98153e3c` |

All three were compiled from their original paths into `raw/imports/` by `raw/run_compile.py` (attempts
01–03, exit 0). The three oleans are bit-identical to the oleans in `g13b…/raw/imports/`. C04 and G13-A are
tracked in Git and unmodified; the G13-B directory is untracked in Git (reviewed artifact, hash bound
above).

## Mathematical route (recovered, then derived independently)

The source invokes the Karlin–Studden principal-representation theorem for the ECT system
{1, y³, y⁴, y^p}. Mathlib has no general Chebyshev-system theorem, so (card pitfall) the needed special
theorem is proved directly:

1. Residual g(y) = y^p − (c0 + c3y³ + c4y⁴) satisfies g'(y) = y²·H(y) for y>0 with
   H(y) = p y^{p−3} − 3c3 − 4c4 y (real-power smoothness).
2. The Wronskian identity gives (p·y^{p−3})'' · 12y⁶ = W(1,y³,y⁴,y^p)(y); hence W>0 on (0,∞) implies
   p·y^{p−3} is strictly convex on (0,∞) (Mathlib `strictConvexOn_of_deriv2_pos`), so H is strictly convex
   and has at most two zeros there. This is the "separate analytic implication" demanded by acceptance (i).
3. Generalized Rolle: g(a)=g(u)=0 gives a zero ξ∈(a,u) of g', so H(ξ)=H(u)=0; the sign pattern of the
   strictly convex H gives g increasing/decreasing/increasing and g ≥ 0 on [a,∞). Symmetrically for the
   upper interpolant at (d double, b simple), g ≤ 0 on (0,b].
4. Integration against any μ in the fibre uses only 1, m3, m4; equality at the principal two-point
   measures; mixtures give the exact range; C04 gives the minimax.

## Items not recovered / not attempted

- Uniqueness of the extremal measures (not part of S121–S125 or Prop. 14 text): not claimed.
- Weak-limit continuity of interior principal measures toward the boundary: not needed (boundary by
  rigidity, as in G13-B) and not claimed.
- Statistics-factor maps N,E ↔ m3,m4 and CMB observation kernels: outside this moment problem.
- Strict non-degeneracy L_p < U_p in the interior: not frozen, not claimed.
