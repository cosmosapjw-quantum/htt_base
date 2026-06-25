# PR07 Dependency-Ordered Schedule

Execution order, not elapsed time.

## Stage 0 — repair freeze ✅
PR07-001 & PR07-005 first (units, imports, gates); then PR07-002/003/004 in
parallel; PR07-006 after theorem wording stabilized. **All landed (rev-r116).**

## Stage 1 — theorem/method papers
- PAPER-A freeze (PR07-007): after PR07-002/004/005 + local xAct pass.
- PAPER-B freeze (PR07-008): after PR07-001/002/003/005 + independent dynamics
  reviewer sign-off.
Neither depends on the low-ℓ Bianchi-Boltzmann solver.

## Stage 2 — observational calibration
- K1: PR08-001 when PR4 E2E access exists (⛔).
- K5: PR08-002 mechanics done; PR08-003 waits for release-matched mock
  ownership (⛔).
- K6: PR08-004 waits for field realizations (⛔); PR08-005 adds an independent
  2MRS comparison (🔜 contract).
- PR08-006 joint artifact/pushforward only after all component owners and
  cross-covariances are registered.

## Stage 3 — future native solver 🧭
PR10-001..006 remain a separate project. PAPER-C/D stay blocked until exact FLRW
background, recombination/visibility, scalar transfer, collision/TCA and LOS
convergence gates pass. Old-Rust spectra/evidence/atlas are not admissible
substitutes. Four future xAct PRs feed PR10-001/005 (see `PR_LIST.md`).
