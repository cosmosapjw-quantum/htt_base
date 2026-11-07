# Local coding agent restart prompt: HTT R41

이 문서를 로컬 coding agent에게 그대로 전달해 실제 코드·데이터·Cobaya 작업을 시작한다. 목표는 새 계획을 계속 늘리는 것이 아니라, R39/R40의 미검증 empirical claims를 격리하고 source-bound likelihood와 실제 관측 분석으로 수렴하는 것이다.

## 역할과 필수 경계

너는 GR/우주론/계산물리/베이지안 추론을 다루는 senior scientific coding agent다. 사용자 지시: Remote Desktop 금지, GitHub와 로컬 primary checkout만 사용, 실제 데이터 다운로드·분석·Cobaya 실행은 가능한 범위에서 수행하고 실제 실행증거로 보고한다.

다음은 절대 위반하지 않는다.
- 과거 R38/R39/R40 로그·리포트·원자료 manifest를 덮어쓰거나 실패 로그를 고치지 않는다.
- 실제 데이터·실행 로그·posterior가 없으면 만들거나 추정하지 않는다.
- hash inventory에 적힌 경로/해시를 실제 파일 검증으로 간주하지 않는다.
- native subagent 기능이 없으면 역할극이나 별도 프로세스를 subagent라고 부르지 않는다. 실제 호출이 없으면 native_subagent=NOT_RUN로 기록하고 serial 수행한다.
- 외부 Bianchi solver를 native BASS output으로 바꾸어 표시하거나 native low-ell solver 결과를 만들어내지 않는다.
- main, R38, R39 historical branch에는 직접 push하지 않는다. R41 branch에서만 작업하고 merge하지 않는다.

## 1. Git 출발점과 mutation scope

Repository: https://github.com/cosmosapjw-quantum/htt_base

Primary checkout:
 /home/cosmosapjw/Dropbox/bianchi/htt_base

작업 branch:
 research/r41-publication-gate-20261107

Parent branch:
 research/r39-observational-identifiability-20261107

Parent commit:
 b819983d479aa1a950d5c162804d74b9b154954b

R41 research documents:
 docs/research_program/observational_publication_20261015/R41_PUBLICATION_GATE_20261107/
 - REVIEW_VERDICT_KO.md
 - RESEARCH_DAG.yaml
 - DATA_SOURCE_MANIFEST.yaml
 - MUTATION_GATES.yaml
 - CLAIM_LEDGER.json
 - LOCAL_AGENT_PROMPT_KO.md

먼저 다음을 실행하고 결과를 보존한다.

  cd /home/cosmosapjw/Dropbox/bianchi/htt_base
  git status --short --branch
  git rev-parse --show-toplevel
  git remote -v
  git branch --show-current
  git rev-parse HEAD
  git log -1 --oneline --decorate

그 다음:
1. dirty changes를 파일별로 기록한다. dirty 상태에서 reset, clean, overwrite checkout, stash -u 금지.
2. origin이 위 저장소인지 확인한다.
3. git fetch origin research/r41-publication-gate-20261107
4. 안전할 때만 R41 branch를 tracking checkout한다. 충돌 시 사용자 변경을 보존하고 blocker로 보고한다.
5. git merge-base --is-ancestor b819983d479aa1a950d5c162804d74b9b154954b HEAD 로 ancestry 확인.
6. R41 branch에만 commit/push. force-push 금지. PR은 draft로 유지, merge 금지.

먼저 root 및 package AGENTS.md를 읽고 다음 repo-local skill을 적용한다.
.agents/skills/htt-dag-orchestrator/SKILL.md
.agents/skills/htt-physics-math-audit/SKILL.md
.agents/skills/htt-xqpi-fg-formalism/SKILL.md
.agents/skills/htt-observable-statistics/SKILL.md
.agents/skills/htt-local-global-discrimination/SKILL.md
.agents/skills/htt-statistical-hardening/SKILL.md
.agents/skills/htt-transfer-provenance/SKILL.md
.agents/skills/htt-scientific-code-validation/SKILL.md
.agents/skills/htt-claim-firewall/SKILL.md
.agents/skills/htt-claim-provenance-ledger/SKILL.md

R41의 RESEARCH_DAG.yaml은 science DAG이고, canonical software PR DAG는 docs/codex_handoff/pr_backlog.yaml 및 pr_status.yaml이다. 기존 dependency를 우회하지 않는다. Assurance-only PR을 반복하지 말고 실제 observable/likelihood/data execution을 전진시킨다.

## 2. 현재 발견된 blockers: 생산 코드 수정 전제

핵심 소스:
- htt/htt/htt/infer/tensor_joint_multiprobe_likelihood.py
- htt/htt/htt/infer/tensor_five_variable_inference.py
- htt/src/common/relativistic_velocity_closure.py
- htt/src/common/kinematic_response.py
- htt/src/common/stf_metric_bridge.py
- htt/src/common/full_observable_x_bundle.py
- owning tests/

상세 line-level findings는 REVIEW_VERDICT_KO.md를 기준으로 한다. 가장 큰 문제:

A. 과거 통계 결과 격리
- R40 MCMC max(Rhat)-1=0.1593, posterior converged=false. 미수렴 posterior다.
- run_hypothesis_competition은 H0/Hloc/Htilt/Hmix 각각을 최적화하지 않고 0 또는 hard-coded theta에서 계산한다. 이 BIC/AIC/Bayes-factor 해석을 사용하지 않는다.
- run_loocv는 training fold별 재적합 없이 full-data fiducial을 held-out에 평가한다. 정당한 LOOCV predictive adequacy가 아니다.
- hand-built Pareto tail statistic과 k<=0.70 clip은 검증된 PSIS-LOO가 아니다.
- R39 README/DATA_AND_COBAYA_PLAN/CODE_AUDIT와 EXECUTION_REPORT/INDEPENDENT_REVIEW 사이에 local data/hash/Cobaya 실행 여부 상충이 있다. source replay 전까지 과거 수치 결과는 QUARANTINED.

B. Source-bound single-probe response
- CMB: tau=0.054를 곱하는 10-vector pseudo-response는 Planck T/E/B likelihood가 아니다. 실제 map/harmonic operator, frequency, mask, beam, pixel window, split/noise/MC covariance를 구성한다. 전이가 없으면 NOT_IMPLEMENTED로 fail closed.
- Quaia: G<20.5 고정 amplitude/direction, 0.35*min_eig*I LSS covariance, slope 3.50/3.30 고정값 제거. 실제 catalog/selection/randoms로 재추정.
- Radio: RACS amplitude 0.018, error 0.004, direction(245,35) hardcode 제거. 실제 RACS-low DR1 catalog를 사용.
- Gaia: 0.92/0.18 response factor 제거. Source-level VSH design, astrometric covariance, frame-spin/glide nuisance를 유도·검증.
- SNe: q0=0.5*Omega_m-0.7을 일반식으로 사용하지 않는다. 무시 가능한 radiation의 표준 FLRW 예에서 q0=Omega_m/2-Omega_Lambda이며 sampled curvature/background에 따라 식을 재유도한다. 넓은 z 구간은 정확한 D_L 적분을 사용하며 low-z Taylor를 전체 sample에 외삽하지 않는다.
- Acceleration: (n.A)*1e-3 같은 임의 scale 금지. physical A에서 delta H/H는 일반적으로 A/(cH) 정규화가 나타나지만, 계수/부호는 채택한 congruence와 photon 방향 convention에서 유도한다.
- CF4: dmzp의 정확한 의미가 distance modulus인지 zero-point residual인지 먼저 확인한다. deterministic stride thinning과 diagonal-only covariance는 production likelihood에 사용하지 않는다. Group/method/calibrator/systematic covariance를 보존한다.
- DESI compressed BAO는 background DM/rd, DH/rd, DV/rd only. Directional H(z,n) 데이터처럼 사용하지 않는다.
- Joint likelihood: block-diagonal covariance를 사실로 가정하지 않는다. Shared LSS/footprint/selection/calibration cross covariance를 추정하거나 explicit independence approximation으로 두고 sensitivity 분석한다.
- assert_zero_stub은 source authenticity, row order, selection, units, estimator provenance를 증명하지 못한다. source manifests를 실제 데이터로 검증한다.

C. Typed state
- ThetaKinematic.beta_RO의 exact two-frame composition과 state builder의 beta_RM+beta_MO first-order sum을 혼용하지 않는다.
- Non-collinear ordered boosts는 frame order와 Wigner rotation을 보존한다.
- five-variable builder의 hardcoded delta_omega_k=0.005, expansion_scalar=0.21 제거; sampled psi와 실제 response를 사용한다.
- STF5 chart (Sxx,Syy,Sxy,Sxz,Syz), Szz=-Sxx-Syy는 Euclidean chart가 아니다. Frobenius Gram 또는 orthonormal STF chart를 사용한다.
- Tensor/scalar Fisher comparison에서 fiducial sigma의 한 방향, 단일 epsilon, 임의 pseudo-det cutoff를 사용하지 않는다.

## 3. 물리 및 likelihood contract

Metric signature (-,+,+,+). c는 명시적으로 유지한다. Dimensionless physical state:
vartheta=(sigma_ab/H, omega_a/H, A_a/(cH), beta_RM^a, beta_MO^a)
where sigma is STF rank-2 (5), omega axial vector (3), A polar vector (3), betas dimensionless velocities (3+3). 17 components are a state chart, not a complete physical model. Evolution, source/observer congruence, light-cone mapping, transfer and nuisance belong in the forward operator.

Specified observer congruence and direction convention에서 leading local coefficient:
H_loc(n)=H+sigma_ab n^a n^b-A_a n^a/c.
Physical A의 A/c는 inverse-time 단위다. Acceleration sign는 photon/direction convention에 의존한다. n^a n^b omega_ab=0은 antisymmetric vorticity의 direct leading scalar contraction이 사라진다는 뜻뿐이다. 모든 higher-order distance coefficient에서 vorticity가 absent라는 정리는 아니다.

Buchert convention sigma^2=(1/2)sigma_ab sigma^ab:
Q_D=(2/3)(<theta^2>-<theta>^2)-2<sigma^2>
=6 Var_D(H)-<sigma_ab sigma^ab>_D.
sigma^2와 sigma_ab sigma^ab를 섞어 x_D coefficient를 쓰지 않는다.

STF5 chart의 Frobenius Gram:
G=[[2,1,0,0,0],[1,2,0,0,0],[0,0,2,0,0],[0,0,0,2,0],[0,0,0,0,2]].

Observation operator:
d_p=O_p(vartheta,psi,eta_p;S_p,W_p)+n_p, d~N(O,C).
S_p binds exact release, source rows/order, selection, epoch, units and frame. W_p binds mask, beam, pixel response, transfer and estimator window. C is the full joint covariance, including justified cross-probe blocks or a tested conditional-independence approximation.

W=C^(-1/2), N=dO/deta, J=dO/dvartheta:
J_eff=(I-P_(WN)) WJ.
For differentiable physical target phi(vartheta), local identifiability requires ker(J_eff) subset ker(D phi). Report identifiable functionals/quotient, not naked rank. Declare physical/prior parameter metric before singular-value/Fisher comparisons. Local identifiability is not global identifiability.

## 4. Six theory loops: separate research, shared contract

1. Low-ell morphology: deterministic template and stochastic anisotropic covariance/BipoSH must be separate. Use a_lm^(T,E,B), mask/beam/frequency/component controls and matched end-to-end MC. Morphology/axis is compatibility, not Bianchi identification.
2. Dipole anomaly: separate thermodynamic CMB dipole, Doppler modulation, aberration, intrinsic radiation dipole, Quaia/NVSS/RACS count dipoles and Gaia glide. Model survey-specific selection/redshift/flux/LSS.
3. Kinematics: derive each physical state-to-observable response from tetrad/optical equations. Keep units, parity, frame order, redshift, source congruence explicit.
4. Bianchi: enforce Jacobi n^{ab}a_b=0. Separate Lie algebra class, dynamical solution and sky transfer. External transfer remains external/conditional. Never fabricate native transfer.
5. Directional Hubble: local leading H_loc(n) is not novelty by itself. Compare against covariant d_L multipoles through O(z^3), later snap/O(z^4) and recent CF4/SN directional-rate analyses. Exact distance integrals for broad z; local series only in validated domain.
6. Local boost vs global tilt: fit isotropic+LSS baseline, local Lorentz boost, dynamically sourced global relative tilt, and mixture. Do not define global tilt as necessarily monotonic with z. Volterra memory is only an ansatz until sourced. Gaia B1 is degenerate with frame spin; E1 contains acceleration/glide.

## 5. Official data sources and exact products

First inspect local files and EXTENDED_DATA_INVENTORY, but verify actual bytes. Download only missing required products. Keep data outside Git, preferably:
 /mnt/extdrive/workdir/htt_open_data/
 /mnt/extdrive/workdir/raw/observational_bundles/

Official sources:
- Planck PR4: https://data.cmb-s4.org/planck_pr4.html and https://pla.esac.esa.int/pla/ . Retrieve required NPIPE frequency T/Q/U maps, split maps, low-res products, masks, effective beams, pixel windows, noise/FFP MC. Don't bulk download all products blindly.
- Quaia: https://irsa.ipac.caltech.edu/data/Quaia/overview.html ; DOI https://doi.org/10.26131/IRSA640 . Full catalogue, selection/completeness, randoms, redshift/flux/quality fields; derive G<20.0 and G<20.5 from same release.
- NVSS: https://www.cv.nrao.edu/nvss/anonftp.shtml ; https://www.cv.nrao.edu/nvss/NVSSlist.shtml . CATALOG.FIT, relevant maps, completeness/coverage and flux selection. Respect declination footprint.
- RACS-low DR1: https://www2.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/racs/ ; original archive https://data.csiro.au/ . Common-resolution mosaicked source catalogue, tile footprints, rms/noise/completeness. Use original tiles where mosaic/selection bias needs investigation.
- Gaia DR3/CRF3: https://gea.esac.esa.int/archive/ ; docs https://gea.esac.esa.int/archive/documentation/GDR3/ . Query gaiadr3.agn_cross_id, gaia_crf3_xm, frame_rotator_source, commanded_scan_law and matched gaia_source astrometry/covariance. Record epoch J2016.0, ICRS/CRF3, TCB.
- Pantheon+: https://github.com/PantheonPlusSH0ES/DataRelease . Full table, full STAT+SYS covariance, exact row order, calibrators/anchors, z-frame and peculiar-velocity corrections.
- DES-SN5YR: https://github.com/des-science/DES-SN5YR . Dovekie release data/covariance/selection/mocks. Check sample overlap/shared calibration with Pantheon+ before combining.
- Cosmicflows-4: https://cdsarc.cds.unistra.fr/viz-bin/cat/J/ApJ/944/94 ; mirror https://vizier.cfa.harvard.edu/viz-bin/VizieR?-source=J/ApJ/944/94 . Individual galaxy/group tables, methods, calibrators, error/covariance, footprint. Define dmzp semantics before model mapping.
- DESI DR2: https://data.desi.lbl.gov/doc/papers/dr2/ ; BAO likelihood products https://github.com/CobayaSampler/bao_data/tree/master/desi_bao_dr2 . Use mean/cov/redshift metadata as background-only.
- Cobaya docs: https://github.com/CobayaSampler/cobaya/blob/master/docs/likelihoods.rst ; https://github.com/CobayaSampler/cobaya/blob/master/docs/cosmo_external_likelihood_class.rst ; https://github.com/CobayaSampler/cobaya/blob/master/docs/sampler_mcmc.rst .

For each real file record: release/product, official URL/DOI, access date/licence, local path, stat size, actual sha256sum, FITS/CSV schema, row count/map nside, units, coordinate frame/epoch, exact cuts and source IDs, covariance identity/order, transform script+commit, and status separately as DOWNLOADED/PARSED/VALIDATED/USED_IN_RUN. Do not commit raw data to Git.

## 6. Execution DAG: build results, not more plans

Stage A: inspect actual local data and validate one source-bound probe. Check exact Lorentz composition (collinear/non-collinear/inverse/rest/Wigner), STF5 metric, source record, covariance and units. Select the first complete probe based on validated local availability and reference reproducibility.

Stage B: build independent operators:
1. Planck low-ell map/harmonic pipeline.
2. Quaia/NVSS/RACS selection-aware count/dipole.
3. Gaia source-level VSH and frame-spin/glide calibration.
4. Pantheon+/CF4 exact distance/PV likelihood.
5. DESI background-only BAO.

Stage C: joint inference:
- Estimate cross-probe covariance or justify and stress-test independence.
- Implement HTT-owned Cobaya external Likelihood class with initialize/logp, proper input params, correct provider requirements and explicit priors.
- Fit one probe first, then pairwise, then joint.
- Fit H0/Hloc/Htilt/Hmix independently with proper priors. Use nested evidence or correctly optimized likelihood scores. No fixed-point BIC.
- Exact-fold refits or validated PSIS-LOO. Nuisance parameters must be refit/marginalized per fold.
- PPC, simulation-based calibration, coverage, injection recovery and null FPR/FNR.

Stage D: fair tensor novelty benchmark:
Compare tensor x, scalar x_C, independent probe multipoles, standard covariant cosmography, boost-only/tilt-only, and hierarchical peculiar-velocity methods. Same data, mask/window, covariance, calibration, nuisance, prior measure and sample split. Compare stable identifiable physical functionals, coverage, predictive scores, FPR/FNR, mask/prior sensitivity and complexity. Tensorization wins only if a physical functional or calibrated prediction improves at controlled complexity. If not, explicitly report no advantage.

Adversarial nulls: footprint, dust/extinction, foreground residual, flux/redshift selection, shot noise, LSS/bulk flow, Gaia frame spin/scan law, calibration offsets, transfer mismatch. Preregister FPR<=0.05 including multiplicity. If it fails, withdraw/soften detection claim.

Stage E: Bianchi:
No native solver fabrication. Build adapter only. Genuine external solver must preserve exact version/config/units/convention and TransferFunctionSpec, with output labelled external-transfer-conditional. Family ID stays blocked until a native low-ell family-specific polarized transfer atlas, matched masks/beams/covariance and equivalence-class separation exist.

## 7. Cobaya and sampler acceptance

Build a package-level external Likelihood class. Load source once in initialize(); verify manifest/covariance; return normalized log-likelihood; declare parameters/derived quantities; use Theory provider when standard background predictions are required. Save YAML, versions, seed, source IDs, logs and chains.

Use proper priors for model evidence. Improper flat nuisance priors cannot be silently compared across different nuisance dimensions. Use at least four independent chains or justify a nested sampler for multimodality/evidence. Require rank-normalized split-Rhat<=1.01 and bulk/tail ESS>=1000 for headline parameters, plus stationarity/trace/PPC. If failing, set posterior status NOT_CONVERGED and don't publish a posterior summary.

## 8. Test contract and anti-drift audit

Use the project's actual interpreter and the narrowest falsifying tests first. Run syntax/import, targeted owner tests, physical limits and affected package tests. Example commands must be adapted after inspecting real test locations; never report a command that wasn't run.

Required tests:
- STF5 matrix Frobenius norm vs Gram and rotation invariance.
- Exact boost composition/inverse and non-collinear Wigner rotation.
- FLRW, local-boost-only, global-tilt-only, shear-only and zero-vorticity limits.
- Units/parameter chart invariance.
- Analytic vs finite-difference Jacobian step convergence.
- Covariance symmetry/positive definiteness/conditioning/row order/source ID.
- Mask/beam/selection injection recovery and matched null.
- Equivalent frame/chart likelihood invariance.
- Deterministic reproducibility for identical config/seed.

Before each commit, answer YES/NO:
1. Did I hardcode a measured amplitude, axis, uncertainty, slope or transfer coefficient?
2. Did I mix synthetic/null/mock and observed data?
3. Are units, signs, tetrad/frame, epoch, harmonic convention and redshift frame explicit?
4. Did I use Euclidean STF coordinates without Gram?
5. Did I assume zero cross covariance without tests?
6. Did I call fixed-point score BIC/evidence or full-MAP held-out scoring LOOCV?
7. Did I promote non-converged sampler or missing input?
8. Did I infer vorticity from Gaia B1 without reference-frame spin control?
9. Did I infer Bianchi family from morphology/axis/x/Q/Pi/F/GF?
10. Did I call external transfer native?
11. Did I say file/hash verified without hashing actual bytes?
12. Did claim strength exceed evidence?

Any YES blocks the related claim.

## 9. Commit and return format

One meaningful scientific capability per commit. Preserve raw logs. Don't make process-only PRs. Push only to R41. Don't merge. Return a JSON receipt shaped as:

{
 "schema":"htt.r41.local_run_receipt/1",
 "branch":"research/r41-publication-gate-20261107",
 "base_commit":"b819983d479aa1a950d5c162804d74b9b154954b",
 "head_commit":null,
 "objective":"",
 "native_subagent":"NOT_RUN|RUN",
 "subagent_receipts":[],
 "source_products":[],
 "downloads":[{"release":"","path":"","bytes":0,"sha256_actual":"","rows":null,"status":"DOWNLOADED|PARSED|VALIDATED|USED_IN_RUN"}],
 "code_changes":[],
 "commands":[{"command":"","cwd":"","exit_code":null,"log":"","result":"PASS|FAIL|NOT_RUN"}],
 "sampler":{"name":"","version":"","chains":0,"rhat_max":null,"ess_bulk_min":null,"ess_tail_min":null,"status":"NOT_RUN|NOT_CONVERGED|CONVERGED"},
 "identified_functionals":[],
 "model_comparison":{"models":[],"method":"","scores":null,"status":"NOT_RUN"},
 "adversarial_nulls":[],
 "claim_updates":[],
 "remaining_blockers":[],
 "next_single_action":""
}

Classify failures precisely: theory, statistical/model specification, numerical, implementation, runtime/environment, missing input/provenance, or authorization.

Stop after the first complete source-bound probe has reproduced a published/official baseline and passed calibrated null tests: report measured result and one next dependency. Do not extend the DAG only to make it longer. Correct non-detection is a valid result.
