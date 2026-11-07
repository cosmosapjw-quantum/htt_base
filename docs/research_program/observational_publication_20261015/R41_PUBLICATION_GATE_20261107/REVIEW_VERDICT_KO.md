# R41 publication-gate review (2026-11-07, Asia/Seoul)

## Scope and evidence boundary

This is a GitHub-only review. No Remote Desktop, local filesystem, local dataset, Cobaya execution, Python test, FITS readback, or local SHA-256 verification was performed in this session.

- Repository: `cosmosapjw-quantum/htt_base`
- Reviewed active base: `research/r39-observational-identifiability-20261107`
- Base commit: `b819983d479aa1a950d5c162804d74b9b154954b`
- Base tree: `ec83057d4460603f7ae63fee6e25c05170ec34ea`
- Default `main`: `f1007dd3e41c07eccd64024dd6b44fb5a40a3612` (2026-10-04; not the current observational research head)
- This review's child branch is additive and does not edit historical R38/R39/R40 artifacts.

The repository's `EXTENDED_DATA_INVENTORY.json` records local paths and hashes, but a GitHub manifest is not proof that those files exist or have those bytes on the current machine. All such local-file assertions remain `LOCAL_CLAIM_NOT_RECHECKED` here.

## Executive verdict

**Publication status: HOLD for an empirical or detection paper; CONTINUE for a narrowly scoped methods paper.**

The strongest viable novelty candidate is not a new scalar anisotropy score, a new directional-Hubble expansion, or a Bianchi identification. Those topics already have substantial prior art. The candidate is a **source-conditioned, multi-probe observation-operator framework that reports only tensor-valued physical functionals identifiable after selection, transfer, correlated covariance, and nuisance projection**.

That contribution is not yet demonstrated. R41 should establish it through a fair scalar-(x_C) vs tensor-(x) benchmark and actual source-bound likelihoods. Until then the tensor advantage is a hypothesis, not a result.

Claim ceiling for the current branch: **C0 / design-and-audit only**. This review does not promote any R38/R39/R40 posterior, rank, BIC, LOOCV, or data-verification claim.

## PR and legacy coverage actually completed

A GitHub REST enumeration returned **561 PR records** (unique numbers 2–564): 131 open, 430 closed, of which 79 were merged. All 561 records were enumerated for title, state, timestamps, head/base refs and SHAs. This is a metadata census, not 561 full code reviews.

The R39 legacy audit itself reports 32 selected PR bodies and 17 full diffs reviewed. This review reused that index and inspected the current R38/R39/R40 lineage, key R40 theory dossiers, the joint likelihood and inference-engine source. It did **not** read every line of every historical PR diff or every legacy document. Do not describe it as a full byte-for-byte audit of the entire project history.

Relevant historical sequence:
- PRs #548–#550: open draft work on shared selection/nulls, physical input gates and CF4 source recovery.
- PRs #553–#559: open draft work on Planck spin-2/mask stability, same-sky identification, and source recovery.
- PR #560: open six-paper goal/DAG draft.
- PR #561: open report-first 42-node campaign.
- PRs #562–#564: closed/merged convergence and observable-bridge work.
- R38 commit `05e9d53449bd02973848da3306f72f63edd7fc54`; R39 commit `b819983d479aa1a950d5c162804d74b9b154954b`.
The current R39 lineage is 123 commits ahead of R38 and R38 is not ahead of R39.

## Contradictions that invalidate prior empirical claims

R39 `README_KO.md`, `PR_LEGACY_AUDIT.md`, `CODE_AUDIT_AND_REPAIR.md`, and `DATA_AND_COBAYA_PLAN.md` state that local observational replay and Cobaya sampling were not performed within the scoped R39 work and that local data-file claims still require replay. In contrast, R39 `EXECUTION_REPORT_R39.md` and `INDEPENDENT_REVIEW_R39.md`, plus R40 `ADVERSARIAL_AUDIT_R40_CONVERGENCE.md`, describe local file rehashes, seven empirical channels, MCMC, LOOCV and release readiness.

The R40 report itself records:
- `max(Rhat)-1 = 0.1593` with named parameters above 1.13, while the posterior bundle says `converged: false`;
- an SNe held-out `chi2/dof = 69.7` caused by not reconditioning the SN offset in that fold, later narrated as resolved;
- a joint block-diagonal cross-probe covariance without an empirically established independence demonstration.

The code inspection below independently shows defects in the advertised inference path. Therefore the reported posteriors, BIC rankings, Fisher information gain, LOOCV adequacy, empirical-zero-stub assertion and local file verification are **QUARANTINED** until recreated from exact source rows and correct likelihoods.

## Critical static code findings

Source: `htt/htt/htt/infer/tensor_joint_multiprobe_likelihood.py` and `htt/htt/htt/infer/tensor_five_variable_inference.py` at the base commit above. Line numbers below refer to that exact source revision.

| Finding | Source locus | Consequence | Required disposition |
|---|---|---|---|
| Model comparison evaluates fixed parameter points, not fitted maxima | `tensor_five_variable_inference.py:437-458, 503-521` | Reported AIC/BIC/approximate Bayes factors are not valid model-selection scores | Fit each hypothesis with declared priors and nuisance treatment; use nested evidence or correctly optimized likelihood; otherwise return `NOT_COMPUTED` |
| The held-out folds are not refitted | `tensor_five_variable_inference.py:353-435` | The procedure is not leave-one-probe-out predictive validation; SN nuisance conditioning is not fold-specific | Refit on each training fold and evaluate held-out predictive density; use real PSIS-LOO only with a validated implementation |
| “PSIS” tail statistic is a hand-built weight heuristic | `tensor_five_variable_inference.py:390-426` | Clipping a heuristic Pareto estimate at 0.70 is not PSIS diagnostics | Use ArviZ/validated PSIS-LOO or exact refits; preserve raw warnings |
| MCMC not converged in existing audit | R40 audit and `tensor_five_variable_inference.py:227-230` | `Rhat-1=0.1593` violates even the code's own 0.05 threshold | Do not use its posterior as production inference; use Cobaya and rank-normalized split-Rhat/ESS/trace checks |
| MCMC is a fixed-proposal custom Metropolis despite adaptive naming | `tensor_five_variable_inference.py:171-230` | Hard-coded start, local-Fisher proposal and incomplete multi-modal diagnostics | Retain only as a toy/reference test; production posterior through Cobaya with tested sampler configuration |
| CMB forward response is a hand-set `tau=0.054` template | `tensor_joint_multiprobe_likelihood.py:448-505` | Not a Planck T/E/B map likelihood or calibrated anisotropic transfer | Replace with source-bound map/harmonic likelihood and explicit `TransferFunctionSpec`; fail closed if transfer unavailable |
| Quaia G<20.5 carrier and covariance response are partly hard-coded | `tensor_joint_multiprobe_likelihood.py:516-571` | The second magnitude-cut data vector and LSS covariance are not source-derived | Read both samples and masks/selection/randoms; calculate shot and clustering covariance from catalogues/mocks |
| Radio RACS-low vector is fabricated in code | `tensor_joint_multiprobe_likelihood.py:589-631` | A fixed amplitude, direction and error are treated as measured data | Derive from RACS-low DR1 catalogue and its selection/mask; keep NVSS/RACS calibration and sky overlap explicit |
| Gaia VSH response factors are unexplained constants | `tensor_joint_multiprobe_likelihood.py:641-690` | `0.92` and `0.18` do not constitute a derived observation operator | Derive source-level VSH design and covariance, calibrate spin/glide/systematics; distinguish frame spin from vorticity |
| SN distance is a low-z truncated expansion and uses a suspicious q0 prescription | `tensor_joint_multiprobe_likelihood.py:749-763` | The series is not safe over the full Pantheon+ redshift range; `q0=0.5 Om-0.7` is not the general FLRW relation | Use exact background distance integral for FLRW baselines; use a separately derived local anisotropic expansion only inside its convergence domain |
| Acceleration enters with an arbitrary factor | `tensor_joint_multiprobe_likelihood.py:756-763, 813-820` | `1e-3` has no established dimensional mapping from physical (A_a) to (delta H/H) | Normalize consistently, e.g. with (A/(cH)), after deriving the chosen observer/emitter convention |
| CF4 uses deterministic stride thinning and diagonal errors | `tensor_joint_multiprobe_likelihood.py:773-820` | Loses sky/redshift/method structure and ignores correlated distance/flow uncertainties | Use full catalogue or preregistered weighted stratified sample; retain group/method/calibrator covariance and correct observable units |
| Joint covariance is block diagonal by construction | `tensor_joint_multiprobe_likelihood.py:1006-1031` | Shared sky/LSS/selection/calibration correlations are omitted | Estimate cross-covariance or state a justified conditional independence approximation and demonstrate robustness |
| “Zero-stub” check only tests non-zero arrays and non-identity covariance | `tensor_joint_multiprobe_likelihood.py:401-447, 1036-1040` | It cannot prove source authenticity, row order, selection, units or estimator lineage | Add a source manifest binding actual catalogue/map identities, row IDs, estimator config, covariance and transformation chain |
| Tensor/scalar Fisher comparison uses one arbitrary fiducial orientation and an arbitrary pseudodeterminant threshold | `tensor_five_variable_inference.py:536-610` | Reported rank/information “gain” is coordinate-, scale- and threshold-dependent | Compare matched models in a shared prior-whitened parameter metric with matched priors, same likelihood, same nuisance projection and held-out predictive score |
| Five-variable state builder uses first-order velocity addition and hard-coded geometry/expansion scalars | `tensor_five_variable_inference.py:280-350` | State does not consistently inherit exact frame closure or sampled background parameters | Use exact ordered Lorentz composition with Wigner rotation; source `DeltaOmega_k` and all normalizations from the state/config |
| Fixed nuisance priors / flat Schur marginalization need normalization review | `tensor_joint_multiprobe_likelihood.py:333-394` and each probe class | Improper flat nuisance priors cannot be silently used for Bayes factors across models with differing nuisance structure | Use proper common priors or report likelihood-only comparisons; document determinants and units |

These are static code findings. No local tests or execution were run here.

## Six-loop research conclusions

### Loop 1 — low-ℓ morphology and physical observables

Preserve separate branches for (i) deterministic anisotropic templates and (ii) anisotropic covariance/BipoSH response. Use (a_{ell m}^{T,E,B}), STF multipoles and mask-aware transfer operators; carry frequency, beam, pixel window, mask, polarization convention and Monte Carlo covariance. Low-ℓ axes, octupole/quadrupole alignment and morphology invariants are diagnostics/compatibility tests, not a Bianchi family identifier. The claimed “complete ring of eight invariants” requires a genuine invariant-theory proof; until then call it a selected invariant feature set.

### Loop 2 — CMB dipole anomaly

Separate the measured thermodynamic temperature dipole, Doppler modulation, aberration, intrinsic radiation dipole, source-count dipoles and astrometric glide. The independent Doppler/aberration route to an intrinsic CMB dipole already has published Planck-era prior art. A new contribution must be a source-conditioned joint frame-closure test, with frequency conversion, mask, foreground and selection response included. Radio/quasar number-count dipoles need a realistic selection functional, not one universal Ellis–Baldwin coefficient.

### Loop 3 — beyond-FLRW kinematics

Use a dimensionless and typed state, for example
[
artheta=(sigma_{ab}/H,;omega_a/H,;A_a/(cH),;eta_{RM}^a,;eta_{MO}^a).
]
Keep the five STF shear components in a declared chart/Gram metric; label polar vectors vs axial vectors/pseudovectors, frame and sign conventions. The current pointwise 17-component vector is a state chart, not by itself a complete physical description: derivatives, source congruence, transport, light-cone mapping and transfer must enter the observation operator.

### Loop 4 — anisotropy classification / Bianchi spaces

Retain the Lie-algebra classification and Jacobi restriction (n^{ab}a_b=0), with class A/B as algebraic structure. Separate algebraic compatibility, dynamical solution, and observed morphology. Before a native low-ℓ Bianchi transfer atlas exists, use external solvers only as explicitly external/transfer-conditional references; do not create synthetic “native” output and do not identify a family from (x,Q,Pi,F,G_F), axes or BipoSH alone.

### Loop 5 — directional Hubble observable

At leading local order, for a specified observer congruence and direction convention,
[
H_{m loc}(hat n)=H+sigma_{ab}n^a n^b-rac{A_a n^a}{c}
]
(up to the sign convention for (A_a) and photon direction). The direct scalar contraction of the antisymmetric vorticity tensor vanishes, (n^a n^bomega_{ab}=0). This **does not** establish that vorticity is absent from every higher-order distance coefficient; derivatives, transport and propagation terms require an order-by-order derivation. Existing covariant cosmography already derives multipole expansions of general (d_L(z,hat n)) to (O(z^3)), with later work extending to snap/(O(z^4)). Novelty must therefore be the identifiable multi-probe tensor-functional extraction, not the directional-Hubble expansion itself.

Buchert convention must be explicit. With (sigma^2=	frac12sigma_{ab}sigma^{ab}),
[
mathcal Q_D=rac23(langle	heta^2angle_D-langle	hetaangle_D^2)-2langlesigma^2angle_D
=6,{m Var}_D(H)-langlesigma_{ab}sigma^{ab}angle_D.
]
If (x_D=langlesigma_{ab}sigma^{ab}angle_D/(6H_D^2)), the shear term is (-6H_D^2x_D); if (x_D=langlesigma^2angle_D/(6H_D^2)), it is (-12H_D^2x_D). Do not mix these definitions.

### Loop 6 — local boost vs global tilt

Compare at least four models: isotropic/LSS baseline, local observer boost, dynamical global relative tilt, and mixture plus survey systematics. A local boost is one Lorentz-frame map, common in physical velocity across probes but with probe-specific response and selection. A global tilt is a relative congruence/state whose redshift evolution must follow specified dynamical equations and transfer; it is not required to be monotonically depth-varying by definition. A Volterra kernel is a phenomenological memory ansatz until its kernel/source is derived or calibrated from the relevant dynamics. A shared preferred axis is insufficient. Gaia's (B_1) spin mode is degenerate with reference-frame spin, while (E_1) glide contains secular aberration/acceleration response; calibrate the reference frame separately.

## Mathematical spot checks completed

- Wolfram symbolic expansion of the standard Buchert definition returned (6,{m Var}(H)-2sigma^2), consistent with the convention above.
- For (S=egin{pmatrix}a&d&e\\d&b&f\\e&f&-a-b\end{pmatrix}), Wolfram returned
  [
  S_{ij}S_{ij}=2(a^2+ab+b^2+d^2+e^2+f^2).
  ]
  Therefore the Frobenius Gram matrix in the chart ((S_{xx},S_{yy},S_{xy},S_{xz},S_{yz})) is
  [
  G_{STF5}=\begin{pmatrix}2&1&0&0&0\\1&2&0&0&0\\0&0&2&0&0\\0&0&0&2&0\\0&0&0&0&2\end{pmatrix}.
  ]
  This is a symbolic CAS check, not a repository test or independent proof of any downstream implementation.

## Candidate methodological contribution and novelty gate

Let the source-conditioned data vector for probe (p) be
[
d_p=mathcal O_p(artheta,psi,eta_p;mathcal S_p,mathcal W_p)+n_p,
qquad dsimmathcal N(mathcal O,C),
]
where (mathcal S_p) binds release, selected rows, units/frame and catalog/map identity; (mathcal W_p) binds mask, beam, selection and estimator window; (eta_p) contains calibration/foreground/selection/frame nuisance terms; and (C) is the joint covariance including justified cross-probe blocks.

With (W=C^{-1/2}), nuisance design (N=partial_etamathcal O), and physical Jacobian (J=partial_arthetamathcal O), define a nuisance-orthogonal whitened response
[
J_{m eff}=(I-P_{WN})WJ.
]
For a requested physical functional (phi(artheta)), local identifiability requires
[
ker J_{m eff}subseteqker Dphi.
]
Report identifiable functionals/quotient directions, not a naked rank. Scale parameters with a fixed physical/prior metric before comparing singular values. The tensor-(x) proposal is valuable only if, relative to scalar (x_C) and established alternatives, it yields stable additional *physical functionals* with improved calibrated coverage or out-of-sample predictive performance on the same source-bound experiment.

This is a candidate method, not a claim of priority. Closest competitors include general covariant cosmography, expansion-rate multipole analyses, field-level multi-probe likelihoods, hierarchical peculiar-velocity inference, CMB Doppler/aberration estimators, and Bianchi polarized transfer calculations.

## What this review authorizes

- Add a new R41 research DAG, source manifest, claim ledger and implementation/restart contract on a child branch of the exact R39 commit.
- Local agent may inspect the primary checkout and retrieve official data in bounded stages.
- Production code edits, actual Cobaya sampling, model-comparison claims, data-derived numerical results, manuscript promotion and Bianchi family claims remain blocked until their relevant gates pass.
- No historical R38/R39/R40 document is deleted or silently rewritten.


## Recent competing evidence that narrows the novelty claim

The local directional-expansion branch has direct, recent competing results that must be treated as primary baselines rather than generic background:

- Heinesen's general luminosity-distance multipole expansion already gives a model-independent expansion through third order in redshift, with 9, 25 and 61 degrees of freedom at successive orders. It establishes that a direction-dependent Hubble/cosmographic expansion is not a novelty by itself: https://arxiv.org/abs/2010.06534
- Kalbouneh et al. (2025/2026) analyse Cosmicflows-4 and Pantheon+ over 0.01<z<0.1, reconstruct a local expansion-rate fluctuation field and its redshift evolution, and report few-percent anisotropic fluctuations: https://arxiv.org/abs/2510.02510
- A separate 2026 analysis of CF4 Tully-Fisher and Pantheon+ with joint distance-relation calibration, distance marginalization and linear-theory peculiar velocities reports a non-zero CF4 zero-point dipole but explicitly compares evidence: https://academic.oup.com/mnras/article/546/2/staf2048/8436862
- Conversely, a 2025 Pantheon+ analysis reports frame-dependent low-z dipolar variation: https://link.springer.com/article/10.1140/epjc/s10052-025-14222-w

These studies do not settle the physical interpretation; their differing samples, frames, calibrations and velocity treatments make a controlled same-source forward-model comparison more important. The HTT contribution must therefore be a reproducible **identifiable tensor-functional and cross-probe discrimination** result, not simply another dipole fit or a claim that the Hubble law is direction dependent.

Similarly, Planck-era work already independently estimates Doppler modulation and aberration, accounting for beaming/noise/masks and intensity-to-temperature conversion systematics, and used these to constrain an intrinsic CMB dipole. This is an essential baseline for R41 Loop 2:
- https://journals.aps.org/prd/abstract/10.1103/PhysRevD.104.063503
- https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.127.101301

There is also pre-existing anisotropic Boltzmann machinery: ABSolve computes deterministic Bianchi-induced CMB temperature and polarization signals for several near-isotropic families (including I, V, VII_0 and VII_h). The R41 distinction is not that polarized Bianchi transfer has never been implemented; rather, the repository must not call an external solver native, and it must compare any external transfer against a future independently validated native implementation: https://academic.oup.com/mnras/article/462/2/1802/2589609
