# Unit B representation execution — direct verification delivery

This increment implements amplitude-preserving rank2/rank3 multipole-vector conversion and descriptive same-row ablations. After account limits interrupted subagents, the owner explicitly authorized execution by other means. Host completed the Lean proof, directly ran the three other engines, reviewed the code, and checked distinct numerical references. **Direct verification passes; independent four-axis/production-review acceptance remains unfulfilled.** Full R8 remains incomplete. Original failures, axis drafts and CAS verdicts are preserved.

## Executed candidate results

The fixed seed81004 mock2 has 45 original tensor rows: ten random STF2/STF3 base pairs with octupole factors0/1/2 and `B_Q beta`, beta=(0.1,0,0); the fixed rational parity/relative-alignment witnesses; coincident vectors; and zero tensors. **44 rows reconstruct**, including exact zero with unidentified directions. The coincident-vector row remains `MULTIPLE_ROOT_UNRESOLVED` and both original tensors are preserved.

All four Unit-E observed PR3 component tensors reconstruct. The largest returned-array Frobenius reconstruction error upper bound is **1.1103061e-19 K** over successful mock irreps and **9.1664660e-20 K** over observed irreps. The certificate computes the exact dyadic squared difference of the input and returned arrays, then brackets its square root. This does not certify root isolation, physical response or measurement uncertainty.

For **990 mock pairs and six observed pairs**, tensor distance intervals overlap the reconstructed-tensor intervals after the conversion-error expansion. All corresponding kth-score intervals also overlap, with fixed q0=o0=1e-5K and k=ceil(sqrt(M-1)). An unavailable MV irrep falls back to its unchanged original tensor solely to retain the common comparison pool; the mock pool is explicitly **INCOMPLETE_ABLATION_TENSORS_RETAINED**, not a completed full-MV experiment. Observed conversion is numerically complete; its product law remains unavailable and no observed rank/p-value is computed.

The first fixed base tensor illustrates a lossy diagnostic: doubling O multiplies its squared norm by four while leaving f_B=0.6453688719659458 unchanged; the specified boost-image O gives f_B=1; O=0 gives undefined f_B. Full-MV carries amplitude and reconstructs full tensors, so no information gain over complete Q/O is asserted. Absolute cross-dot alignments, power and f_B have distinct method IDs. These are representation controls, not null-law calibration or anomaly detection.

Outputs are [mock2](execution_after_symmetry/mock2.json), [observed components](execution_after_symmetry/observed_components.json), their saved `*_rows.npz` arrays and [actual rendered figure](execution_after_symmetry/representation_controls.png). Parent opened the PNG. Timings are one execution with spectral caching, not a controlled speed comparison: mock conversion0.123s, original pool0.804s, reconstructed pool0.863s; observed conversion0.015s, pool0.082/0.088s.

The algorithm uses the complex bilinear null cone `n(z)=(1-z^2,i(1+z^2),2z)` and antipodal root pairing to propose unit vectors, then fits their amplitude. Near multiple roots, pairing failures or nonfinite reconstructed amplitudes return typed unresolved records. The representation basis follows [Copi–Huterer–Starkman](https://arxiv.org/abs/astro-ph/0310511v2) and [Katz–Weeks](https://arxiv.org/abs/astro-ph/0405631v2). Generic existence/uniqueness is a named literature theorem; this implementation does not claim a new proof or globally certified numerical root isolation.

## Verification and remaining scope

Missing-module RED is preserved. The first numerical test run had one repeated-root classification failure; the near-root refusal threshold was fixed before observed execution. The independent production reviewer then found finite tensor inputs whose required amplitude overflowed. Root added typed refusal and both-rank regression tests. Actual pool execution exposed non-bitwise symmetric rank3 reconstruction caused by floating operation order; canonical symmetric orbit assignment corrected it. The original failed log and pre-symmetry implementation are preserved. The latest selected command completed **14 tests in1.14s** (eight MV and six orbit tests), with no addopts deselection:

```bash
PYTHONPATH="$PWD/htt/htt:$PWD/htt/src:$PWD/htt:$PWD" PYTHONDONTWRITEBYTECODE=1 \
/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python -B -m pytest \
-o addopts='' --import-mode=importlib tests/r8/test_multipole_vectors.py \
tests/r8/test_orbit_bounds.py -q
```

The new limited O4 CAS contract hash is `430f325399b7caf0e7513cccec64e5bdae114ecafa5ce039747e373936c82f9d`. It covers STF2/STF3 trace/sign/permutation and null-cone contraction identities only. Wolfram+xAct, SymPy and Sage/Singular produced independent exact drafts. The initial Lean build failed because a solved identity permutation shifted the five remaining proof cases. Host preserved that draft, removed the already-solved branch in a separate copy, and compiled the proof successfully with the pinned Lean4.31.0/mathlib. Printed proof axioms contain no `sorryAx`. No theorem statement, test reference or tolerance was weakened.

Direct execution now gives **FOUR_ENGINE_CHECKS_PASS** for all three obligations. This is three blind drafts plus host-completed Lean; it is explicitly **not CAS_4AXIS_PASS** or a replacement for the old CAS_BLOCKED report. [Engine results](../../../../.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/engine_results.json) record commands, outputs and scope. Original account-limit and failed-build records remain.

The separate host-authored check uses 100-digit Decimal STF polynomials, a quadrupole eigenframe construction independent of the null-cone root method, and exact Fraction checks of saved error transport. **200 additional numerical cases pass**, both deliberate mutations (dropped amplitude and wrong trace coefficient) are detected, and all **990+6 saved pair intervals plus kth-score intervals** are rechecked. Maximum Decimal/reference disagreement is3.39e-21K and eigenframe disagreement1.36e-20K. This is an algorithmically distinct computational check, not an independent reviewer. Its reproducible source/result live in `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/verify_reference.py` and `reference_result.json`.

Host reviewed the conversion status/refusal path, amplitude normalization, exact dyadic reconstruction norm, symmetric tensor layout, common-row fallback labeling, pair-error triangle bound and score ordering against the governing interfaces. The earlier independent reviewer found amplitude overflow; its repair is covered by both-rank regression. The later bitwise-symmetry repair is covered by exact symmetry tests and actual saved-pool checks. Parent opened the actual plot again. Production source hashes in `reference_result.json` match the numerical producer records. Successful mock/observed numerical arrays were reused unchanged for direct closeout.

The original frozen B4 independence criterion is **not retrospectively marked met**. The user-authorized direct route permits this tested descriptive implementation delivery; the bounded original work unit closes with its independence ceiling unresolved. No generic root-isolation capability, empirical product law, actual CMB p-value or new physical constraint is issued. Independent acceptance may be sought later without discarding these results.

Run a new numerical attempt with `scripts/observed_runs/run_r8_representation_controls.py --run-dir <new-dir>` only when a relevant code change warrants it. Existing results can be reviewed directly. Units D/F and full G wiring/synthesis, plus previously documented A/C limitations, still remain.
