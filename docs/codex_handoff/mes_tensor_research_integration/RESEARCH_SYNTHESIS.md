# MES tensor, tilt and inference research: integration disposition

## What supersedes what

The current codex_emergency report and external-referee adjudication supersede the old WU-006–008 success labels. The historical stored real harmonic carrier remains a numerical input; the old Q/O contractions, tensor ranks, foreground inferences and carrier-domain injection interpretations do not become valid merely because the old files replay.

Two different normalization errors must remain separate:

1. Stored harmonics use `(a_l0, sqrt(2) Re(a_lm), -sqrt(2) Im(a_lm))`. Applying unscaled-complex STF formulas directly to these coefficients changes shape and rotation behavior.
2. Original MES epsilon is a PSTF temperature-tensor norm. It differs from sky RMS by `sqrt((2l+1)!!/l!)`. Retaining the original MES coefficient triple while substituting sky RMS changes the physical normalization and the relative quadrupole/octupole mixture.

Correcting either error is correctness work, not discovery of a new physical theorem. Previously computed scalar-function ranks may be retained as historical computational results, not automatically as corrected original-MES physical statements.

## Implemented additive bridge

`common.mes_krylov_completion` supplies a scale-explicit generic proper-rotation orbit representation. It keeps two amplitudes and sixteen contractions of the corresponding unit tensors. Reconstruction is valid only in a declared cyclic, numerically conditioned chart. Degenerate rows retain their full tensors instead of receiving invented axes or being removed from a null ensemble.

The sixteen values are the two Q traces, three moments of `v=O:Q`, the signed Krylov determinant, and ten symmetric contractions of O with `[v,Qv,Q^2v]`. Ordinary power and cubic bispectrum distinguish neither all nine generic orbit coordinates nor the explicit mirror witness. The sixteen contractions are an overcomplete generic representation, not sixteen independent measurements and not a global invariant-ring claim.

`rebuild_mes_tensor_carriers.py` reads only the original arrays from pinned Git blobs, projects the actual stored basis using an independent spherical-integration oracle, verifies radial and scalar power identities, applies the explicit PSTF MES function and emits corrected tensors with pending evidence. It neither imports the withdrawn WU feature implementation nor computes a favored replacement anomaly rank.

## Coverage of the research seeds

### Representation and invariant theory (A01–A14)

A01–A02 are the representation gate. A03 requires distinguishing O(3) from SO(3); pure-octupole even invariants omit chirality. A04 explains the old eight-coordinate insufficiency. A05–A09 support the cyclic reconstruction and canonical representative. A10's global-frame claim and A11's ordinary-bispectrum equivalence are rejected. A12–A14 motivate a later, separately registered quotient-score test; no kernel or null score is selected after observing the corrected ranks here.

### MES geometry and dynamics (B01–B22)

B01 determines epsilon normalization. B02–B10 supply the cubic/moment/Gram geometry underlying the algebra. B11–B12 are congruence- and equation-dependent dynamics, not new observed velocities. B13–B16 describe support functions and bounded semialgebraic response domains. B17–B20 give conditional history-to-endpoint constraints; the stronger noncommuting bounds use Frobenius constant sqrt(6) and cubic constant 6. Their matrix-flow reachability is not Einstein–matter existence. B21 requires two-sided set control for Hausdorff stability. B22 forbids manufacturing direction from scalar ceilings.

### Boost, ideal inverse and noisy estimation (C01–C18)

C01–C06 support the seed boost-response projector; the sharp condition-number bound is 5/3. C07 must distinguish unrestricted intrinsic octupole from a response-orthogonal residual. C08–C11 provide the ideal positive-quadratic inverse, requiring absolute positive temperature including monopole and dipole, not only the retained low-ell carrier. C12–C14 give model-adequacy implications, not unique causal attribution. C15–C17 concern an explicitly specified noise/model mismatch; inverse-square moments under untruncated Gaussian temperature noise cannot be assumed finite. C18 remains an undefined generalization rather than a proved polarization theorem.

The seed inverse implementation is a synthetic research reference. It is not installed as a new obsstat-owned physical-inference API in this change. HTT retains physical inference ownership, and native BASS delivery is not replaced by an analytic toy.

### Low-z and remote fields (D01–D08)

These results require actual response, survey selection, noise and nuisance inputs. A full-rank radial affine model identifies bulk, expansion and shear but not solid rotation. Shell-response diversity can remove a local/global rank degeneracy only under the specified response model. Optical-depth freedoms can restore amplitude nonidentification. Shared CMB realizations require a dependence-aware design, but paired contrast is not uniquely mandatory. No new remote-field adapter, data acquisition or observational claim is created here.

### Statistics and adaptive evidence (E01–E16)

The finite-rank machinery is established statistics applied under explicit joint exchangeability and equivariance. It is not unconditional validation of every frozen reference sample. Decreasing transformations exchange one-sided tails. Data-dependent selection may be valid if the entire operation is symmetric and properly conditioned. Wasserstein-only threshold guarantees, treating bounded bodies as cones, free confidence-set intersections and independence products of shared-data evidence are not admitted. E05 remains a classification proposal, not an exhaustive theorem. The source proof ledger is author-derived analytic/CAS evidence, not a proof-assistant or independent-referee certificate.

## Required next order

1. Run the additive unit and synthetic Git-object integration tests on the actual checkout.
2. Execute the pinned-input map-free representation repair locally. Preserve all rows and source arrays. Its only terminal is pending independent review.
3. After review, rerun old frozen scientific questions with corrected semantics in a new output namespace, without tuning expected results.
4. Register a separate generic-orbit/physical-response statistic and nuisance-aware power study. The withdrawn injection registry is not reusable without basis correction.
5. Treat a noisy observation versus CMB-only simulations as descriptive sensitivity until a faithful joint null is supplied.
6. Pursue MES reachability and ideal Bianchi inverse as separate conditional theory lines. Physical identifiability expands only with a verified response and data model.

## Operational boundaries

No Actions query/run/status gate. No raw maps, new downloads, environment repair, native-solver substitution or research merge. The external-fusion operational inventory remains C0 reachability evidence. Newly downloaded Commander candidates do not bypass their scientific admission gate. Worktree cleanup and recovered user files are outside this change.

## Verification truthfulness

A file, a contract or this prose does not certify a test result. Consult the actual per-command execution receipt for source scope and return codes. Partial source-projection tests do not prove full repository integration. Neither the prototype nor the local representation runner may self-attest independent review or a scientific SUCCEEDED terminal.
