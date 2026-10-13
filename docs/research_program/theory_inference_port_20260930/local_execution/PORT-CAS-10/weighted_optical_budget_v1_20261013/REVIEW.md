# P10-A — independent review (stress-gap body and weighted optical budget)

Reviewer: fresh-context read-only subagent. Requested runtime gpt-6-astra/ultra (unavailable); observed runtime claude-opus-5-5. The reviewer is not the author.

**Verdict: PASS_WITH_NOTES. No blocking finding.**

## Checks

### Source anchors

All anchors verified:

- `typefree_physical_budgets.py`:
  - `:68` — `budget = c*d/gap`
  - `:73` — the Q diagonal
  - `:90-118` — `weak_response_budget`; it raises when `kinematic_bound` is missing; `:115` sets `error = l*v + bound*perturbation + numerical`; `:118` sets `s + wp − (b − a)`
- TF-P2 (lines 21–29) and TF-W1 (lines 198–213).
- `TF_W1_INPUT_KO.md:44`.
- Contract, PORT_MAP and `formalism_mapping`.
- GR-04 `Proof.lean` encodings, which are re-declared verbatim.

### W1 — B*

- B* = c d*/δ* > 0.
- Python fixture: B*(2,2,4) = 1.
- Units are 1/time.

### W2 — Q and the shear basis

- Q weights match `:73` and the contract.
- The shear basis is the Frobenius-orthonormal set diag(1,−1,0)/√2, diag(−1,−1,2)/√6, (E_ij+E_ji)/√2. It is genuine because σ is built traceless and symmetric.
- Rate and quadratic-form identities: numerically, 20,000 random instances deviate by at most 5.6e−16.
- A pure rotation and pure shears each give a gauge of exactly 1.

### W2e — stress-gap body

- The premise `gap·jet = −c·D` is TF-P2 written in L's eigen-triad. Its general form is GR-04's `projected_eigen_derivative`.
- The premise is not circular: the result also needs the gap lower bound, the derivative bound, and the rate identity.
- The premise is non-vacuous. A Lean instance attains a quadratic form of exactly 1, so the bound is sharp.
- Python: the maximum gauge over 20,000 instances is 0.99717.

### W3 — integration by parts

- Product rule via `HasDerivAt.smul`.
- Vector integration by parts derived from the fundamental theorem of calculus.
- The scalar absolutely-continuous version is Mathlib's `integral_mul_deriv_eq_deriv_mul`.

### W4 — K_w sign

- K_w = I_ws + I_w′m − (w_b m_b − w_a m_a), matching the contract, `:118` and the source.
- Toy problems with a bump window and a linear window match Python to 4.4e−16.
- Flipping the endpoint sign is detected: 16.77 instead of 7.29.

### W5 — remainder budget

- The proof uses the a.e. bound on k.
- The K_w identity is derived from the balance before εnum is added.
- Toy errors stay within the radius: 0.41 ≤ 1.27 and 1.39 ≤ 3.61.

### W6 — negative controls

- W6a is genuine: without a k bound there is no finite radius, and Python's ValueError fires.
- W6c (endpoint sign) is genuine.
- W6b is weak.

### Other checks

- **Circularity:** none.
- **Integrity:** all hashes match. Failed compiles 01 and 02 are kept; 03 and 04 exit 0. Frozen statements appear verbatim, and FROZEN_TARGETS was written at 20:13:41, before the first compile.
- **Axioms:** all 18 theorems use only propext, Classical.choice and Quot.sound. No sorry.
- **Independent recompile:** exit 0 with identical warnings. The reviewer's audit (non-vacuity, saturation, 18 axiom checks) exits 0.

## Notes

- **N1 (wording, corrected in RETURN.json):** the w-side hypothesis is at least as general as C¹. For vector-valued m, the proof requires HasDerivAt on [[a,b]], which is stronger than the source's absolute continuity. The absolutely-continuous case is covered only per scalar component (W4b/W5c).
- **N2:** V must be computed from the supplied Â when the coefficient is uncertain.
- **N3:** the d* = 0 `ZERO_BODY` branch is not formalized.
- **N4:** the following are premises, not proofs: diagonalizing L into an eigen-triad, gauge invariance under rotation of the triad, and the bridge from an actual stress to the typed premise.
- **N5:** the Wolfram/xAct, SymPy and Sage tool axes were NOT_RUN.
- **N6:** warnings are cosmetic.
- **N7:** W6b is weak.

## Not proved

- An actual-stress provider for the premise, including the diagonalization bridge.
- Physical values of d*, δ*, L, M_k and εnum.
- Vector-valued absolutely-continuous integration by parts.
- The d* = 0 branch.
- Triad invariance.
- Quadrature accuracy.
- A universal MES anchor.
- Full PORT-CAS-10.
- Scientific admission (HOLD).
