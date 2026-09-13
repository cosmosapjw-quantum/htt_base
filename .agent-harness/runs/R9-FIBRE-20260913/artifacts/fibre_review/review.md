# R9 fixed ambient fibre review

Verdict: no blocking defect reproduced in the assigned fixed-ϰ, interior-fibre numerical comparison.

The source freezes Cartesian `q`, `v`, and the unit STF3 direction `a` before it obtains the reference STF3 SVD basis.  Each basis then receives both `L_is = B_sijk q_jk` and `a_s = B_sijk a`; the reconstruction back to Cartesian components is checked.  This is the required fixed-ambient target, rather than preservation of old SVD coordinates.

I independently evaluated the F3 formula with explicit Cartesian entries and 80-decimal `Decimal` arithmetic, without NumPy, the saved basis, or `fixed_contraction_support`.  With full Frobenius contractions and `M = diag(8/5, 8/5, 1)`, it gives `eta = 0.0684375` and support `0.974542207044862226475458456798749697...`.  Its difference from the stored `0.9745422070448619` is about `3.27e-16`, below the frozen `1e-10` tolerance.  The direct construction has STF trace residual at most `1e-80`, unit-norm/contraction/objective residuals at the displayed Decimal precision, and a nonzero kernel component.

The saved system and lowell payloads have identical case, reference, all 35 comparison rows, tolerance, and negative control.  Their recorded source hashes match the current runner, saved-basis constructor, and production helper.  Their worst support/witness/contraction/norm/objective errors are respectively `4.44e-16`, `7.89e-16`, `3.07e-16`, `4.44e-16`, and `4.44e-16`.  The negative control changes the ambient target while retaining coordinates and changes support by `-0.06902074514451273`, far above `100 * 1e-10` as required.  It correctly retains the old `1.407526/1.113440` targets as incomparable and keeps the inherited tolerance unchanged.

The production helper is used with `q_is_fixed=True`, resolves this interior fibre, and returns the reconstructed witness checked against the Cartesian reference.  The focused regression suite passed `3/3` in this review.  The existing evidence records two source-bound successful 35-representation executions and a separate 38-test receipt.

This review confirms only the diagnostic floating-point comparison.  It does not establish a certified bound, uncertain-`q` result, eta-boundary result, scientific claim, or four-axis CAS admission.  No registered launch receipt exists for this assignment, so launch provenance remains `unverified`.
