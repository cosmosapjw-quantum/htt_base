# CAS-07-M01 delta

This unit proves the original scalar prerequisite

`0 <= eta(Kc,s) <= eta(Kc,L) < 1`

for `Kc >= 0`, `0 < s <= L`, with the final strict inequality conditional on
the supplied small-distortion assumption `eta(Kc,L) < 1`. The `Kc=0` branch is
literal and separate; the positive branch uses the principal real square root.

The frozen contract and input hashes are respectively
`b5a49f066f95a010607eb800d323094d5d4050c986c3cb26f78bba022977cc70`
and `89949f14b9671720a7df7e73ab2bdf2e8cede8ed7937a86ea531635f29259400`.
Parent-observed sequential execution returned `CAS_4AXIS_PASS` for Wolfram+xAct,
SymPy, Sage+Singular, and Lean+mathlib. The same independent reviewer returned
`NEEDS_REPAIR` for an initially unbound xAct scalar, then
`PASS_FINITE_COMPONENT_REVIEW` after the single targeted binding repair.

Validation:

- `.agent-harness/scripts/cas_gate.py run-adjudicate ...`: exit 0,
  `CAS_4AXIS_PASS`, four PASS axes, zero errors.
- Wolfram 15.0.0 and xTensor 1.3.0: actual eta-gradient contraction bound to
  the analytic derivative and nonzero on `Kc>0,t>0`.
- SymPy 1.14.0: exact positive-term sums and 80-digit ancillary vectors.
- Sage 10.9 and bundled Singular 4.4.1/44100: universal analytic chain plus
  exact polynomial identities; raw Singular diagnostics inspected.
- Lean 4.31.0, mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`:
  full piecewise theorem compiled without `sorry`, `admit`, `native_decide`, or
  a target axiom; only `propext`, `Classical.choice`, and `Quot.sound` printed.

The owner directed execution without the absent global CUH-G harness. Four
engines ran sequentially and no runner consumed sibling artifacts, but one Host
context authored the axes; that correlation is recorded. This finite component
does not prove the remaining finite-distance theorem, physics, observations, or
scientific admission. Scientific status remains `HOLD`.
