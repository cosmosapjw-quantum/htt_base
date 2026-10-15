# HTT Loop8: 실제 CF4 STF2 nuisance-Schur 정보, 2026-10-15

## Authority, scope and input identity

The next READY task is C8-CF4-METHOD in the current local Loop7 DAG. This unit works in a separate git worktree. The original checkout, 55 untracked paths and two modified files are preserved.

- Parent branch: obs/solver-free-dossier-20261014; HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54; draft PR #533.
- New isolated branch: research/htt-cf4-schur-20261015.
- Source raw CF4 Table3 SHA-256 c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d.
- Source raw CF4 Table4 SHA-256 b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94.
- Reused Loop6 selected CF4 35,970 groups NPZ SHA-256 86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c.
- Selected group-ID SHA-256 f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88.
- The original, previously untracked Loop6 source module was copied byte-identically; SHA-256 843b19e464817d14455df68e9043a93cc71cc7449ab339052c3ddfe1c7298c19.
- Raw Table3/4 bytes were rehashed, but Loop6 selection itself was reused rather than independently rerun. Distinguish 38,053 lines parsed from this table release from the 38,065 groups cited in the original scientific paper's assembled catalogue.

Claim: CONDITIONAL_SOURCE_GAUSSIAN_OPERATOR_DIAGNOSTIC, not a physical Bianchi shear or global tilt estimate, cosmic isotropy detection or calibrated p-value. The released group data do not provide the required joint selection function, source-method covariance, cosmic velocity covariance or spacetime optical transfer.

## Exact mathematics

For y=B gamma+N eta+e with fixed positive D=Cov(e), gamma in R^5 the apparent STF2 coefficients and unrestricted eta the nuisance, set A=D^(-1/2) B, Z=D^(-1/2) N, and P=I-Q_Z Q_Z^T.

    F0=A^T A
    Fprofile=A^T P A=Fgg-Fgn Fnn^(-1) Fng
    gammahat=Fprofile^(-1) A^T P D^(-1/2) y
    Cov_working(gammahat)=Fprofile^(-1).

Five generalized eigenvalues Fprofile v=lambda F0 v fall in [0,1]. All five >0 means the five signal combinations are locally identified under the stated finite operator. The hypervolume inflation from unrestricted nuisance equals sqrt(det(F0)/det(Fprofile)). Computation uses column-scaled nuisance QR and 5x5 SPD Cholesky with O(np) working storage; no N_obs-by-N_obs inverse.

Derived covariance-absorption lemma: if D>0, N full rank, K positive semidefinite, and eta is freely profiled, adding C=D+N K N^T changes neither the nuisance-quotient precision nor Fprofile:

    C^(-1) - C^(-1)N(N^T C^(-1)N)^(-1)N^T C^(-1)
      = D^(-1)-D^(-1)N(N^T D^(-1)N)^(-1)N^T D^(-1).

Proof: orthogonally decompose any whitened residual into range(Z) and its complement. The extra Gaussian calibration covariance is entirely supported on range(Z), which is removed by unrestricted profiling, so the quotient precision is unchanged. The same follows from Woodbury plus the Schur identity. A constrained eta prior, missing selection-law response or correlated angular velocity outside range(N) INVALIDATES this cancellation claim.

Exact Wolfram 4x2 toy test with a rank-one nuisance and diagonal positive weights: Fprofile=[[42,-48],[-48,254]]/17, determinant 492/17, and both Schur and full GLS return gamma=(5,1) without numerical approximation.

## Actual results from authenticated selected real group rows

Declared model: z=Vcmb/c; Href=74.6 km/s/Mpc, Om=0.3153; z 0.01..0.10; fixed error floor 0.15 mag; independent velocity-width 250 km/s; method offsets/slopes and separate 3D bulk/3D angular dipole, then five apparent STF2 responses.

| Statistic | Result |
| --- | --- |
| Real source groups and parameters | 35,970 groups; 19 columns (14 nuisance, 5 STF) |
| Relative Schur information eigenvalues | 0.3715911, 0.4909143, 0.6606777, 0.9567284, 0.9896876 |
| Trace fraction after nuisance | 0.5948856774 |
| Apparent Frobenius STF norm | 0.03325774236 |
| Gaussian ellipsoid hypervolume inflation | 2.96023568 |
| Full QR coefficient / covariance maxabs difference | 1.21e-16 / 1.69e-20 |
| Delete-one-sky-region success | 12/12 rank five |
| Delete-one-sky-region nominal STF norm range | [0.02616145, 0.03852604] |
| Delete-one-sky-region worst-mode fraction range | [0.31309918, 0.41792305] |

17/17 source/cohort tasks completed. Weakest generalized eigenvalue with removed FP=0.673350, TF=0.269513, SN=0.339068, OTHER=0.355543. All subset analyses share objects from the same survey and are NOT independent observations.

Benchmark with identical preconstructed 35,970x19 design and 2 BLAS threads (8 interleaved warmed comparisons): baseline full QR median 0.028737s, Schur QR median 0.022597s, ratio 1.272, matched error 1.21e-16. Includes neither file IO nor source model construction nor inference physics; see performance.json.

## Primary literature and novelty ceiling

- Tully et al., Cosmicflows-4, ApJ 944:94 (2023), https://doi.org/10.3847/1538-4357/ac94d8 . Multiple distance calibrations and quoted large systematic uncertainty require explicit source terms.
- Boubel et al., Testing anisotropic Hubble expansion, https://arxiv.org/abs/2412.14607 . CF4 Tully-Fisher anisotropy and bulk-flow comparison, but different source/method law; their null quadrupole cannot be turned into our p-value.
- Salzano et al., Updates on dipolar anisotropy in local measurements of the Hubble constant from Cosmicflows-4, PDU 53, 102382 (2026), https://doi.org/10.1016/j.dark.2026.102382 . Local angular inferences change under velocity treatment.
- Wang et al., The peculiar velocity correlation function of the Cosmicflows-4 catalogue, MNRAS 548 (2026), https://doi.org/10.1093/mnras/stag677 . Actual survey covariance is nontrivial and sky sampling anisotropic.
- Internal PR255 already developed the general nuisance-Schur strategy (htt/src/common/anchored_response_geometry.py). This unit's new contribution is a source-specific executed conditional spectrum and method stability calculation, NOT priority for Schur algebra.

## Reproduction, tests and handoff

Worktree: /home/cosmosapjw/worktrees/htt-cf4-schur-20261015
Immutable input copy: /home/cosmosapjw/worktrees/htt-cf4-schur-20261015-inputs

    OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 PYTHONPATH=htt/src:htt python3 -m pytest tests/obsstat/test_cf4_schur_information.py -q
    OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 PYTHONPATH=htt/src:htt python3 scripts/run_htt_cf4_schur_20261015.py --input-npz docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz --parent-result docs/research_program/cf4_schur_loop8_20261015/inputs/loop6_result.json --output-dir docs/research_program/cf4_schur_loop8_20261015/results_REPLAY

Runner refuses mismatched source hashes and existing output directories. Results including data-bound JSON, plot and human-readable report are under results/. Physical release/claim status: HOLD. Native subagent dispatch: NOT_RUN (no delegation API exposed), local serial execution done directly, NOT local Codex.

Next: C8-OBS-MES-EPS real Planck/FFP source processing vs MES covariant epsilon assumptions is READY pending source identity. C8-REAL-JOINT and T8-GEOM-SOURCE remain blocked on true joint observation/transfer law.