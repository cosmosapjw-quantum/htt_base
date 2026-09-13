# Fixed ambient STF fibre comparison

Owner: common numerical validation. Scope: R9 revision 2 F3 numerical
reproduction, **DIAGNOSTIC_ONLY**; no transfer source or scientific admission.
Starting commit: `af5fe14a60658ff7926e58ea512bd3014aeba2ba`.

The old `reference_comparison.json` correctly left two different random
SVD-coordinate functionals incomparable. This comparison fixes the actual
Cartesian STF3 tensor **a**, unit STF2 **q**, and contraction **v** first.
Each orthonormal basis receives `a_s = B_s:a` and `L_is = B_sijk q_jk`.
Changing coordinates now preserves the target, including the reconstructed
ambient maximizing tensor. The old results and original reference runner stay
unchanged; the original ambient random target was not recovered.

The existing production `fixed_contraction_support` is exercised through its
existing interface. A separate Cartesian reference constructs the adjoint as
`STF(v tensor q)`, without an SVD or nullspace basis, and uses the fixed F3
metric `M = I + 6 q^2/5`. All products are full Frobenius products. The case is
an interior, fixed-q fibre with a nonzero kernel component of a; its maximizer
is unique. This does not cover uncertain q or certify the eta=1 boundary.

The same q, v and ambient a are stored in `system.json` and `lowell.json`.
Thirty-five representations comprise the original SVD, sign changes, a
permutation, and 32 orthogonal rotations. Randomness changes only the coordinate
basis. A negative control freezes the old coordinates while changing the basis;
the changed ambient target produces a different support, exposing the prior
comparison's failure mechanism. The inherited absolute tolerance is `1e-10`.

Both existing environments execute the same source locally:

- Python 3.12.3 / NumPy 2.4.2;
- Python 3.11.15 / NumPy 2.4.6.

The support is `0.9745422070448619` in both environments. The largest support
error against the Cartesian reference is `4.44e-16`, and largest reconstructed
ambient witness error is `7.90e-16`. `comparison.json`, `execution.json`, and
raw stdout/stderr preserve the measured values and commands. These are finite
floating-point checks, not certified bounds, proof of all basis changes, or
four-axis CAS. They do not validate a survey law or spend alpha.

Run from the repository root, always with a new output filename:

```bash
OPENBLAS_NUM_THREADS=1 python3 -B scripts/observed_runs/check_r9_ambient_fibre.py --output /tmp/r9-ambient-new.json
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/r9 htt/src/common/test_r9_depth_path.py htt/src/common/test_r9_tensor_functionals.py
```

The user explicitly removed separate-worktree verification before/after push.
Validation runs in this worktree; delivery checks only the pushed remote ref.
All original HOLDs, quarantines and alpha allocations remain unchanged.
