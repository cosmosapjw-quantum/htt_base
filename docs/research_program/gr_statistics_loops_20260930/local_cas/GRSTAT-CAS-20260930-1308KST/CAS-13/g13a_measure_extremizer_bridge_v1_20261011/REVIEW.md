# Independent review — G13-A

Verdict: `PASS_SCOPED`.

The fresh read-only reviewer was requested as `gpt-6-astra/ultra`; observed
model and effort are both `UNKNOWN`.  The reviewed candidate is
`MeasureExtremizerBridge.lean` with SHA-256
`a64f6c3c8745eb5b4f2634d2bf4369b6df9f300ba098ba72b9d5bd16720fda12`.

No blocking finding was identified.  The final theorem has exactly the explicit
strict-interior hypothesis `CAS13C02.StrictInterior a b m3 m4`, derives both
nodes, interval membership, positive weights and retained moments, and leaves
none of those as a final theorem hypothesis.  It instantiates the C03 p=5 and
p=6 lower/upper half-line certificates on the positive interval, unfolds the
coefficient conversion from `hermite` to `q5`/`q6`, and reverses the contact
equalities only at the required attainment interface.

The result still quantifies over arbitrary `Admissible` `Measure ℝ`; its
transport and attainment use actual Bochner integrals, the actual `twoDirac`
definition, and its probability/support/integrability/moment obligations.
The lower nodes are `(a,u)` and upper nodes `(d,b)`, consistent with the
second-node weight convention.

The three frozen source hashes, contract hash, packet, compile receipt, and
exact-prefix axiom-audit source were checked.  The final audit reports only
`propext`, `Classical.choice`, and `Quot.sound`; it has no `sorryAx` or added
mathematical axiom.

After review, `git diff --check` required removal of one terminal blank line
from the candidate and audit source.  The reviewer independently confirmed that
restoring that line reproduces the reviewed hashes exactly, and that the final
audit source still has the exact final-candidate prefix.  The prior verdict is
therefore bound to the final candidate identity above; controller execution is
recorded in `raw/controller_final_binding.json`.

This verdict excludes non-strict boundary cases, general real exponents,
CAS13-C04 relative minimax, historical four-axis adjudication, and scientific
admission.  Scientific admission remains `HOLD`.
