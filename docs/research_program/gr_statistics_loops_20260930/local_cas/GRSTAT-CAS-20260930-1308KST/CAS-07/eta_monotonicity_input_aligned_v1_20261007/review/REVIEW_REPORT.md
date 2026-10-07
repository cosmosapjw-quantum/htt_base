# CAS-07-M01 independent review

Final verdict: `PASS_FINITE_COMPONENT_REVIEW`.

The initial review returned `NEEDS_REPAIR`: the xAct expression contracted a
generic scalar named `etaScalar[]` without connecting it to the admitted eta
function. The single repair binds the one-dimensional positive-Euclidean-frame
gradient components to `D[etaPositive[t,k],t]`, obtains the derivative-square
contraction, and proves it nonzero for `k>0,t>0`. The same reviewer reran the
Wolfram source at exit 0 and found no new issue.

The initial independent review also directly checked the final scalar proofs in
SymPy, Sage 10.9, bundled Singular 4.4.1/44100, and Lean 4.31.0 with mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. Lean compiled the whole piecewise
theorem and reported only `propext`, `Classical.choice`, and `Quot.sound`.

This review covers only the CAS-07-M01 scalar analytic prerequisite. It does not
establish the remaining finite-distance theorem or scientific admission. The
scientific status remains `HOLD`.
