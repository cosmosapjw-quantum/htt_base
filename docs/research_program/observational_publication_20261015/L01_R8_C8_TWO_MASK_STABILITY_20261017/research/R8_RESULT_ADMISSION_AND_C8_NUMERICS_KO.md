# HTT 여섯 논문 DAG: L01 R8/C8 실제 POL geometry 차이 판정과 재현 수치 안정성

2026-10-17 Asia/Seoul. Parent: GitHub Draft PR #556 HEAD `cdfb86b8b9fb3238061136ea0f90d668dc49de94`. Canonical `PUBLICATION_DAG.json` Git blob SHA-1 `ac4a94c3da13f142eaab3b06b5275b58096c95e1`. This work is source-conditioned **finite geometry**, not an observable polarization B power spectrum or Planck anomaly significance.

## R8 1. 관측 입력·실제 영수증과 계산되지 않은 것

User-local execution on 2026-10-17, as directly pasted in conversation:

- `39 passed, 1 warning` for prior R7/C7 test suite, and payload SHA `17/17 PASS`.
- CLI `PASS_FINITE_GEOMETRY_SPECTRAL_AUDIT`, native receipt JSON SHA256 `7b4763afe8e5d30a02be296b0d4f7281a30f4e80937975dcda5f929643c2a7b6`.
- Planck PR3 polarization Galactic NESTED NSIDE2048 masks processed as RING NSIDE64 with fixed threshold .5 **after** each `ud_grade`, followed by Boolean triple intersection. `K_common` and `K_triple` are both real 64-by-90 finite geometry responses: low ell2..5 (64 real E/B coordinates), high ell6..8 (90 real E/B coordinates).
- Original user-reported native response NPZ SHA pins: common `a45acd13c079bd871b6704dc6d4952ee6294db0f3f50403978abbd7606f06969`, triple `3df2b8f2624ea7c831f72979788f08c176e3eaff661865d7759a9434c5ae9a59`.
- `||K_common||₂ = 1.2813681702334279`, `||K_triple||₂ = 1.2993976990506202`, **actual user-local full-matrix** `||K_triple-K_common||₂ = 0.43962877239085046` (all dimensionless in normalized coefficient basis). Source masks: 38,329 and 37,054 selected of 49,152 RING64 pixels.
- `--all-m-spin-check` was requested by the user CLI that reported success; per-seed details require the existing spectral receipt JSON. The single Matplotlib Axes3D import warning does not invalidate these finite linear-algebra results.
- **Inaccessible here:** both actual NPZ files and original native FITS (no independently executed in-sandbox 64x90 full spectral decomposition). Their real SVD, E->B block norms, delta rank, machine/backend repeatability and runtime are to be computed by the supplied C8 program on the already existing local files. Do not invent these values.

## R8 2. Exactly attainable two-mask contrast with a common high-ell source

Define `ΔK=K_t−K_c`. For the *same* real 90-component high-ell vector `h` with an **externally assumed** Euclidean coefficient bound `||h||₂≤R`, the low-ell difference is `Δy=ΔK h` and

\[
\sup_{\|h\|_2\le R}\|\Delta y\|_2
 =R\,\sigma_{\max}(\Delta K)=(0.43962877239085046)R.
\]

This is an exact finite-dimensional theorem attained by a top right singular vector times R. There is no measured or source-qualified `R` yet. If `h` has thermodynamic temperature harmonic units, R and Δy share those units; the K operator is dimensionless. If high-ell E and B coefficient balls differ, this joint ball assumption must be replaced with explicitly constrained blocks.

For any chosen *fixed* unit real low coefficient contrast `v`, the sharp signed interval is

\[
  v^\mathsf T\Delta y \in
 [-R\|\Delta K^\mathsf T v\|_2,\;R\|\Delta K^\mathsf T v\|_2].
\]

The E-only to B-only sensitivity is `ΔK_BE = P_{B,L} ΔK P_{E,H}^T` of shape 32x45. For an **externally assumed** E-coefficient ball `||h_E||≤R_E`, the exact maximum low-B difference is `R_E ||ΔK_BE||₂`. Without physical `R_E` or actual normalized component-separated Q/U coefficients, this cannot be interpreted as realized leakage.

The scalar norm difference lower bound, `|1.2993976990506202−1.2813681702334279|=0.01802952881719233`, accounts for only `4.1010802635%` of the measured full operator-difference norm; in fact `0.43962877239085046/1.2813681702334279=0.34309325188775597`. These numbers compare **linear maps** under the same coefficient-space Euclidean metric. They do not give relative realized B amplitudes, a p-value, or an error budget.

Because both K operators intertwine the same real E/B complex structures `J_L,J_H`, so does ΔK. Consequently the 64 real singular values of ΔK occur as pairs, and a 32x45 complex SVD supplies a strongly independent numerical check in this fixed basis. Algebraic validity requires identical Q/U scalar mask weights, consistent orientation and full-column rank of the low design for both masks.

**Ell>8 firewall:** For the actual sky write `Δy = ΔK_{6:8} h_{6:8} + ΔK_{>8}h_{>8} + Δr_systematic`. Without quantified bounds on the last two terms, no finite universal *physical* high-ell leakage bound follows from the finite `0.43962877` norm. In particular no bound on observed `B`, tensor-to-scalar ratio `r`, or cosmological anomaly is admitted.

## C8 3. Numerical-stability and performance method

`src/l01_mask_difference_stability.py` reads (i) original v2 native mask JSON, (ii) the R7/C7 full spectral receipt JSON, and (iii) the **same two SHA-pinned original NPZ**. Reject a new input identity, changed geometry policy, missing claimed native R7/C7 norm or wrong physical gate. Check numerical agreement of NumPy real singular values, SciPy real singular values and SciPy reduced 32x45 complex singular values. Independently check top singular-vector saturation, E-only to B-only top-vector saturation, a predeclared low-B unit contrast and paired singular values.

Report matrix ranks only as *numerical* ranks using a documented machine-precision criterion. Weyl's inequality supplies a **conditional** stability certificate for an externally justified bound `||E||₂≤epsilon` on the error of the computed difference matrix:

\[
  |\sigma_j(\Delta K+E)-\sigma_j(\Delta K)|\le\epsilon.
\]

Full row rank is robust if its smallest singular value is strictly greater than epsilon. No `epsilon` is invented from the source hash, the singular-value decomposition's agreement or physical priors. If no externally justified bound is supplied, output `NOT_CERTIFIED_NO_EXTERNAL_OPERATOR_ERROR_BOUND`. Independent repeated SVD is an agreement diagnostic, not an a posteriori theorem about forward error.

The code measures very small real 64x90 and complex 32x45 SVD wall-times at matched numerical task and precision, explicitly reporting host-sensitive medians without claiming speedup. `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` minimize nondeterministic scheduling at this scale.

## R8 admission and paper DAG

**Admitted for specified use:** real-source-conditioned finite Planck PR3 POL mask geometry, their two operator norms, sharp two-mask difference scalar norm and conditional coefficient-space theorem. Source evidence status `USER_REPORTED_NATIVE_LOG` rather than assistant-recomputed FITS/NPZ. Theoretical theorem status `DERIVED`, manufactured local C8 math tests `IMPLEMENTATION_VERIFIED`, real-sky physical claim `UNRESOLVED`. No need for an additional provenance approval gate to study this conditional geometry.

**Not admitted:** actual Planck E/B sky contamination, ell>8 tail bound, Q/U map processing, beam/foreground leakage, FFP10 exchangeable null, Bianchi family inference, anomalous significance. Canonical L01 remains `pending` until a matched T/E/B/beam/physical null can be established. More precise E/B leakage model should compare Planck 2018 VII and pure B/pseudo-C_l literature. This finite coefficient-space OLS response is a different estimator from pseudo-C_l.

### Stage-by-stage DAG record

| Step | New outcome | Verification | Official 6-paper DAG |
|---|---|---|---|
| R8 | Actual user-local ΔK norm accepted as geometry-only and sharp same-source ball theorem; R unknown | Analytic; Wolfram exact complex-doublet manufactured check | 14/42 |
| C8 | Source-pinned NPZ/readback, real/complex/backends SVD comparisons, sharpness witnesses, Weyl conditional stability and small SVD time measurement | New + existing sandbox pytest, native local run pending | 14/42 |

Per-paper official count: P1 1/6; P2 0/6; P3 2/6; P4 1/6; P5 1/5; P6 2/6; COMMON 7/7. READY L01,S02; all six NOT_READY_TO_SUBMIT. The official 42-node DAG and the 245-card unrelated project backlog are unchanged.

## Primary literature context (not claims imported wholesale)

- Planck Collaboration, *Planck 2018 results. VII. Isotropy and statistics of the CMB*, A&A 641 A7 (2020), arXiv:1906.02552: large-angle polarization residual-systematics, FFP10 and physically qualified null.
- Smith & Zaldarriaga, *A general solution to the E-B mixing problem*, Phys Rev D 76, 043001 (2007), arXiv:astro-ph/0610059: pure pseudo-C_l/ambiguous E/B control, distinct from the finite OLS here.
- *Towards ending the partial sky E-B ambiguity in CMB observations*, arXiv:2007.09928: astrophysical E-mode information outside masks and leakage, another genuinely different estimator and source contract.

No new no-go theorem or empirical posterior claimed. The mathematical difference-operator theorem and numerical tests are incremental method construction; novelty remains subject to the six-paper X02 comparator and physical-source replication.

### Actual bounded sandbox verification

With Python 3.13.5 / NumPy 2.3.5 / SciPy 1.17.0, BLAS thread counts set to one, **50 pytest cases passed**: 39 reused parent tests + 11 new C8 tests. Fresh finite native-geometry mask regression in the new tests constructs two real spin-2 design operators and checks the delta sharpness witness. A true observed Planck NPZ C8 analysis is NOT_RUN here. NumPy and SciPy may call the same LAPACK kernels: agreement is an implementation consistency check, not independent numerical certification. The unrelated Matplotlib Axes3D warning in the user's local environment requires no action for these tests.
