# Local Coding Agent 재개 프롬프트 — R47 Solver-free Morphology Likelihood

너는 `cosmosapjw-quantum/htt_base` 저장소의 이론·관측·수치 코딩 연구 담당자다. 이 프롬프트는 이 저장소의 장기 이력과 R41–R46의 stacked branch 상태를 보존하면서, 여섯 연구축을 실제 관측 likelihood로 연결하기 위한 제한된 실행 지시다.

## 0. 절대 기준

- Repository: `cosmosapjw-quantum/htt_base`
- Active branch: `research/r47-solverfree-morphology-likelihood-20261109`
- Parent commit at branch creation: `66b4bce6151a5fc19f317b02221b724223354fd6` (R46)
- R47 계획 폴더: `docs/research_program/observational_publication_20261015/R47_SOLVER_FREE_MORPHOLOGY_LIKELIHOOD_20261109/`
- 먼저 현재 HEAD와 working tree, remote, PR 상태를 읽고 기록하라. 이 프롬프트의 parent SHA는 branch creation parent이지 현재 R47 head라고 가정하면 안 된다.
- 사용자가 remote desktop 사용을 금지했다. GitHub가 저장소와 변경의 기준이다. 로컬 작업은 사용자가 허용한 local coding agent에서만 수행하되, 원격 데스크톱을 조작하지 않는다.
- Raw data, simulation maps, catalogues, chains는 Git에 넣지 않는다. Raw는 `workdir/raw/r47/`, derived는 `workdir/derived/r47/`, chains는 `workdir/chains/r47/`에 저장한다.
- R42–R46은 아직 open/draft stacked PR이었다. merge 여부를 추정하지 말고 현재 GitHub에서 다시 확인한다.

## 1. 첫 실행 명령과 identity receipt

1. `git status --short --branch`, `git rev-parse HEAD`, `git ls-remote origin refs/heads/research/r47-solverfree-morphology-likelihood-20261109` 실행.
2. 정확한 R47 head를 clean fetch/checkout한다. 사용자의 uncommitted files를 버리거나 `reset --hard`, `clean -fdx`를 하지 않는다.
3. R41–R46 각 PR의 base/head SHA와 현재 branch relation을 GitHub에서 확인한다. R47 branch는 R46 head에서 만들어졌으므로 이전 stacked branches를 임의로 merge하지 않는다.
4. 이 R47 폴더의 JSON들을 strict parse하고 파일 hash를 계산한다. 먼저 작성된 handoff 내용은 연구 요구사항이지 실제 실행 영수증이 아니다.
5. 아래 R47-T1부터 하나씩 수행한다. 각 turn을 끝내면 해당 return artifacts를 만들고 push하며, 다음 turn을 임의로 넘어가지 말고 결과를 사용자에게 보고한다.

## 2. 과거 이론·코드 재사용 감사 (R47-T1)

관련 PR/레거시 자료를 중요도와 dependency 기준으로 조사한다. 모든 unrelated PR diff를 무작정 읽는 대신 다음을 우선한다.

- R41/R42 publication gate, source lock, claim ledger, six loop reports, competitor registry, sampler config와 Cobaya receipt.
- R43 functional identifiability and mock experiments.
- R44 Bayes-factor sufficiency and c-optimal redshift design.
- R45 finite-model posterior information-loss theorem and mocks.
- R46 target-specific posterior compression theorem and mocks.
- 2026-10-26 `HTT_FIVE_THEORY_LOOPS.pdf`, 특히 Loops A–E와 internal referee review.
- K1 FFP10/NPIPE download guide 및 low-ell morphology pipeline.
- Bianchi/MES, EGS3, R9 tensorized framework, local-global discrimination, CF4/Pantheon+/Gaia/Quaia/NVSS adapters.
- 현재 실제 코드 경로 `htt/src/common/`, `htt/htt/htt/infer/`, `htt/bass/`, `scripts/r41/`, `scripts/r42/`, `tests/`.

반드시 산출:
- `PR_LEGACY_COVERAGE.csv`: PR 번호, base/head SHA, changed files reviewed, science claims reused, disposition.
- `SOURCE_REUSE_LEDGER.json`: each reused equation/code/data product with exact commit/blob identity and direct/conditional/partial/unverified classification.
- `CONTRADICTION_LEDGER.yaml`: manuscript claim vs actual implementation, run receipt, source file, status and minimal repair.
- `R47_T1_AUDIT.md`: publishability verdict for empirical and methods tracks separately.

이미 확인된 재현 blocker:
- R42 Cobaya receipt has ESS=53 with `ess_passed=false`; R42 SBC reports uncalibrated scenarios.
- R42 Planck observation file is a 743-byte `observed_lowell_EB.npz`, not a raw (T/Q/U) map-level likelihood input.
- R42 Cobaya config has `verify_sha: false`.
- R42 `full_observable_x_bundle.py` still contains default coefficients including `0.92`, `0.18`, `3.6625`, `3.3200`, and a simplified CMB construction. Trace all consumers before deciding whether any are proxies or production.
- R42 `BianchiTransferAdapter` currently raises `NotImplementedError` for transfer evaluation.
These defects block promotion of those empirical numbers; they do not refute the entire tensorized framework.

## 3. Solver-free Bianchi-I temperature model (R47-T2)

Use `METHODS_NO_BOLTZMANN.md` as the hypothesis to test, not an unquestioned truth. Derive from first principles:

[
ds^2=-c^2dt^2+g_{ij}(t)dx^idx^j,quad
g_{ij}=a^2[e^{2B}]_{ij},quad B^T=B, mathrm{tr}B=0.
]

Spatial translation Killing vectors imply conserved (p_i). With present metric (g_{ij}(t_0)=delta_{ij}), observer-frame direction (n_i=p_i/E_0), show
[
E^2=g^{ij}p_ip_j,qquad
T_0(n)/ar T_0=[n^Te^{-2B_*}n]^{-1/2}.
]

Check:
- direction vs photon propagation convention and sign;
- metric/energy units and scale-factor normalization;
- exact Planck occupation-number invariance;
- (B_*=0), first-order STF limit, eigenvalue permutations, parity and rotation;
- whether non-commuting metric evolution affects only (B_*) mapping or the endpoint formula;
- relation between (B_*) and (int sigma dt) only under a stated commuting/principal-axis convention;
- thin last-scattering and collisionless-after-emission assumptions;
- history non-identifiability and inability to infer (sigma(t_0)) without dynamics.
Do not create a false general no-go theorem. If the formula is corrected, update the derivation and preserve the failed form in the error log.

## 4. Map/harmonic likelihood and implementation (R47-T3)

Read existing harmonic convention, STF bridge, observation operators, source-bound Planck adapter, five-variable state, and Cobaya modules before editing.

Implement an exact or numerically convergent projection:
[
a^B_{ell m}(B_*)=int dOmega,Y_{ell m}^*(n)
{[n^Te^{-2B_*}n]^{-1/2}-1}.
]

The map likelihood must include:
- mean template and stochastic CMB separately;
- exact ordered observer boosts and Wigner rotation where relevant;
- mask, beam, pixel window, map filtering and frequency response as one observation operator;
- noise, foreground and calibration covariance;
- full non-diagonal covariance after cut-sky processing;
- a clear label that SI stochastic covariance on Bianchi-I background is phenomenological unless physically computed.
Do not call a C_ell-only low-ell likelihood phase/morphology complete.
Do not invent B/E polarization prediction from the temperature-only geodesic map. For this model, E/B geometric prediction is unavailable.

Compare three routes:
1. Bianchi-I exact geodesic temperature mean + declared stochastic covariance.
2. General anisotropic Gaussian/BipoSH covariance likelihood, not assigned Bianchi type by default.
3. Precomputed external Bianchi transfer bank/emulator (ABSolve/AniLoS/AniCLASS) labelled external/transfer-conditional.
Use the simplest complete code path first. No duplicate wrapper for a production operator that already exists.

## 5. Planck PR4/NPIPE acquisition (R47-T4)

Use the official sources:
- ESA PLA: https://pla.esac.esa.int/pla/
- NASA LAMBDA release index: https://lambda.gsfc.nasa.gov/product/planck/curr/planck_prod_irsa.html
- CMB-S4 NPIPE portal: https://data.cmb-s4.org/planck_pr4.html
- Full-sky maps: https://data.cmb-s4.org/planck_pr4-fullsky.html
- Half-ring maps: https://data.cmb-s4.org/planck_pr4-half_ring.html
- Low-resolution maps/noise: https://data.cmb-s4.org/planck_pr4-lowres.html
- QuickPol effective beams: https://data.cmb-s4.org/planck_pr4-quickpol.html

Stage data by small manifests first, then exact channels/splits. The portal indexes frequency maps at 030, 044, 070, 100, 143, 217, 353 and higher-frequency channels, hit maps and white-noise products. Obtain masks and component/foreground products appropriate to the chosen analysis. Check full/half-ring map consistency and NPIPE transfer functions; large-scale E-mode response is not automatically unity. Retrieve end-to-end simulations if available through official authenticated route; if not, mark empirical FPR/SBC gate BLOCKED rather than substituting independent Gaussian maps.

A separately labelled FFP10/PR3 SMICA validation lane may use the historical K1 guide, but it is never combined with PR4/NPIPE as a matched simulation set.

## 6. Six independent observable loops, each on its own turn

The theory loops are independent research units. Do not combine them into one omnibus fit.

### L1 — Low-ell morphology to physical observables (R47-T2 through R47-T5)
Execute in stages: derive the solver-free Bianchi-I geodesic temperature map (T2), implement the harmonic/map likelihood (T3), acquire and verify Planck PR4/NPIPE (T4), then run the observed CMB likelihood and calibration (T5). Target (B_*) first; present (sigma_{ab}(t_0)) only after an admitted history model.

### L2 — Dipole anomaly (R47-T6)
Use Quaia DR1 parent catalogue/randoms/selection, NVSS flux/coverage and RACS-low replication. Estimate count dipoles by redshift/flux/spectral subset. Model source evolution, local structure, masks and cross-catalogue dependence. No fixed magnitude-cut rescaling.

### L3 — Beyond-FLRW kinematics (R47-T7)
Use Gaia DR3 source-level proper motions/full covariance, CRF3/VLBI tie and qualified radial observables. Estimate the nuisance-projected identifiable subspace of (	heta=(sigma_{ab},omega_a,A_a,eta_{RM},eta_{MO})). Preserve the B1 frame-spin kernel.

### L5 — Directional Hubble expansion (R47-T8)
Use Pantheon+ full distance-modulus likelihood and CF4 only if the original distance likelihood, covariance, group/selection model and row identity are qualified. Estimate (h_0(hat n)), (h_1(hat n)), and higher distance-jet coefficients only where finite-redshift remainders are controlled.

### L6 — Local boost versus global tilt (R47-T9)
Combine CMB aberration/modulation, redshift/flux/size tracer response, Gaia E1 and directional distances with one shared frame/state model. Determine (eta_{MO}) and (eta_{RM}) identifiability after nuisance projection; one dipole is not a decomposition.

### L4 — Bianchi anisotropy classification (R47-T10)
Combine the Bianchi-I geodesic template, R47-T7 kinematic region, R47-T8 optical coefficients, and existing Loop-D structure-constant/Ricci/Gauss-Codazzi compatibility. Use Bianchi V/VIIh transfer only from a validated external provider. Distinguish geometry equivalence from different simply transitive presentations.

### Integration (R47-T11 and R47-T12)
Only after the independent loops close, run the two-layer generative-model × readout benchmark, target-posterior information-loss analysis, matched SBC/PPC/FPR/power and held-out predictions; then perform one bounded independent review and make separate empirical/methods publication decisions.

## 7. R47-T5 sampler and inference controls

- Fit each generative model separately with the same data, masks, selection, covariance and common subset.
- Use Cobaya MCMC for posterior sampling only after the likelihood has passed fixtures. Evidence requires a separately converged supported nested sampler and proper normalized priors.
- Require rank-normalized split-(hat R), bulk and tail ESS, trace/rank plots, autocorrelation, multimode occupancy, prior/proposal sensitivity and checkpoint-resume test. Thresholds are frozen before observing results.
- Run SBC and matched prior-predictive simulations, coverage, FPR, power, PPC and holdout by frequency/split/probe/depth. No calibration claim from the same simulations used to tune the statistic unless the dependence is modeled.
- Compare R46 target-posterior information loss for predeclared physical estimands. The HTT (T=(x,Q,Pi,F,G_F)) bundle is a single push-forward and is not multiplied into the likelihood.

## 8. Mutation and anti-drift rules

Use `LOCAL_AGENT_IO_CONTRACT.json` as authoritative. In brief:
- exact branch/head receipt before mutation;
- source files and raw data immutable;
- active turn write set only;
- failing test before behavior change where feasible;
- theory and implementation tests separate;
- no PASS without command/exit/receipt;
- update claim ledger only after its gate passes;
- push only active branch and keep PR draft;
- no force push, merge, data replacement or silent schema changes.

Before each commit, run an anti-drift self-audit:
1. Did the implementation preserve the user's physical question?
2. Is every model response derived or explicitly phenomenological/unavailable?
3. Did any summary become an extra independent likelihood factor?
4. Are frame, units, signs, selection, covariance and map operators pinned?
5. Are source bytes and exact covariance row/order identities recorded?
6. Are R42 numerical claims still quarantined until replay?
7. Did any CMB phase/morphology claim accidentally use C_ell-only likelihood?
8. Did any Bianchi family claim outrun its own curvature/transfer response?
9. Are all non-identifiable kernel directions preserved?
10. Are the changed paths limited to this turn's write set?

## 9. Stop and return payload

At the end of each numbered turn, return:
- exact Git SHA/branch and changed files;
- source/input hashes and row/mask/covariance mapping;
- equations → functions → outputs trace;
- test commands, environment, stdout/stderr and actual exit codes;
- science-validation and numerical-validation statuses separately;
- claims promoted, retained, quarantined or blocked;
- actual blocker and smallest next action;
- next turn identifier only.

Do not report the task complete merely because docs or a mock run exists. The user wants publishable, observable results; the empirical path remains open until the above gates are executed.
