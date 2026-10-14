# G05-A — independent review (Lorentz neighbourhood and strict DEC)

**Reviewer:** fresh-context read-only subagent. Requested runtime was gpt-6-astra/ultra (unavailable); observed runtime was claude-opus-5-5. The reviewer is not the author.

**Verdict: PASS_WITH_NOTES. No blocking finding.**

## Checks

### Einstein tensor is derived, not postulated
- `pd` is `fderiv`, `ginv` is the actual inverse, and Γ, ∂Γ and Ric follow the COMMON_SPEC convention R^a_bcd = ∂_cΓ^a_db − ….
- `Ein_conf` reduces the general definition to the EF2 conformal formula.
- φ_a and φ_ab are shown to be true partial derivatives.

### Origin values
- Hand check: φ_00 = −2b, φ_ii = −b, □φ = −b, so G(0) = diag(6b, 0, 0, 0).
- T_00 = (6b − Λ)/κ and T_ii = Λ/κ.
- An independent sympy computation confirms both the formula and G(0).

### Strict DEC
- The pairing form is T(V, W) > 0 for nonzero future g-causal V and W.
- At the origin this is equivalent to the source's type-I criterion ε > |p|. The substitution is recorded.
- The time orientation is consistent, and the condition is not vacuous.

### Member-dependent radius
- A4, B1 and B2 assert `∃ r > 0` separately for each member; there is no uniform radius.
- `strictDEC_nhds` uses the actual g(x)-cone with explicit widening and explicit margins. The algebra was checked.
- `stress_continuousAt` is proved (inverse written as adjugate/det, C² entries).

### Cubic family
- `Ein_eq_of_jet` is proved. Its hypotheses hold: ∂H(0) = 0 and ∂∂H(0) = 0 because H is a homogeneous cubic.
- Hence T(0) has the same diagonal values as the conformal family.
- Numerical check: T(0) = diag(3.5, 2.5, 2.5, 2.5) and ∂_0 G_0i(0) = q_i, consistent with EF3.
- The base metric e^{2φ_0}η matches EF3.
- The B1 `Lorentzian` predicate is a correct (1,3)-inertia test for symmetric g and implies nondegeneracy.
- Numerical radius probe for one member: margin +0.66 at radius 0.02, −0.59 at 0.1. This is consistent with an existential radius.

### Negative control
- At Λ = 3b, V = (1, 1, 0, 0) and W = (1, −1, 0, 0) give T(V, W) = 0.
- No strict-open argument is made at the weak boundary.

### Receipts and toolchain
- All hashes match.
- Failed compiles 01_A and 03_B are kept; 02_A, 04_B and 05_audit exit 0.
- 90/90 theorems use only propext, Classical.choice and Quot.sound. No forbidden tokens.
- H, J and H_from_third_jet are textually identical to the accepted CAS05C03.lean, with binder renames only for `sdelta`, `delta` and `sum4`.
- Independent rebuild: A, B and the audit all exit 0, and the audit stdout is identical.

## Notes

- **N1.** B2 does not state nondegeneracy on the ball as a separate conjunct; it follows from the `Lorentzian` conjunct.
- **N2.** The pairing-form ⇔ type-I equivalence away from the origin is not formalized (it needs the Hawking–Ellis classification and the IFT).
- **N3.** A1 does not restate the B1 predicate for gConf; this is trivial.
- **N4.** Probes `raw/probes/P1` and `P2` were compiled outside the harness. They are not deliverables, and nothing imports them.
- **N5.** "Verbatim" means verbatim up to binder renaming.

## Not proved

- A uniform or explicit radius.
- The EF-RADIUS obstruction at s = 3b/|λ|.
- Type-I away from the origin, or an isolated eigenframe (IFT).
- Persistence at or beyond Λ = 3b.
- CAS-05 C02/C03 obligations.
- Four-axis acceptance and the full CAS-05 parent.
- Scientific admission (HOLD).
