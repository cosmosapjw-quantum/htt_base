# External-Fusion Round-3 Package Validation

Validation date: 2026-07-22.  These are bundle-mechanics and transparent reference-DGP results, not observational or native-Bianchi scientific results.

## Structural inventory

- Proposed PRs: 36 (`PR-247`–`PR-282`).
- Hostile/advocate steelman pairs: 34.
- PASS gates: 288.
- FAIL/kill gates: 216.
- Track I: PR-247–PR-273.
- Track II: PR-274–PR-280, blocked without a real solver delivery receipt.
- Integration: PR-281–PR-282, conjunctively dependent on both track checkpoints.

## Executed checks

```text
pytest:                                  9 passed
reference demo scripts:                 10/10 exit 0
Track-II boundary without solver:       exit 3 BLOCKED_NATIVE_REQUIRED
clean temporary-repo overlay:           installed and 9 tests passed
clean overlay reference demos:          10/10 exit 0
```

## Selected transparent-reference results

- Pole rotation covariance: worst `1-|p_rot·R p| = 2.22e-16` over 100 cases.
- Reference shell-kernel conservation: relative shell-sum error `2.55e-08`; coarse/fine total difference `0.0`.
- Toy source-response matrix: rank 3 with singular values approximately `(49.95, 33.66, 8.46)`.
- Toy local/global/source classifier accuracy: `0.71`; this is deliberately not accepted as a physical calibration result.
- Reference-DGP binning stability: `EXPECTED_BLOCK_PHYSICAL_KERNEL_REQUIRED`; its large shift proves the physical CAMB/CLASS/readable-kernel gate is load-bearing.
- Optional external plugins: missing packages return explicit availability receipts and do not break the core suite.

## Interpretation

The dependency-free code validates SO(3) covariance, real-sky harmonic conventions, shell/cumulative object typing, source-superposition mechanics, set-valued coherent fractions, finite-dimensional response rank, e-value optional-stopping mechanics, and Track-I/Track-II isolation.  It does **not** validate a physical redshift decomposition of the CMB, kSZ/pSZ reconstruction, a global tilt, or a Bianchi family.  Those promotions are reserved for the PR-specific external-code, data and native-solver gates in the roadmap.
