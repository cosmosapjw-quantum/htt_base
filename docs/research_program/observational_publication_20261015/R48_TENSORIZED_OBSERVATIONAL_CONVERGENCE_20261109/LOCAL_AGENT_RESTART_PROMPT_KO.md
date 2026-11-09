# R48 local agent restart: T1 remote audit closed, local replay then T2

> This addendum supersedes the older instruction below that says to begin R48-T1 from scratch. R48-T1 is now PASS_SCOPED for remote static source reconciliation and bounded analytic/toy oracles. Local runtime verification remains NOT_RUN.

## Identity and boundaries

Repository: cosmosapjw-quantum/htt_base  
Branch: research/r48-tensorized-observational-convergence-20261109  
Audited parent/head before this addendum: afb3ab9406cf13874e2e49e40d09f3b639b01c20  
PR: https://github.com/cosmosapjw-quantum/htt_base/pull/572, keep OPEN/DRAFT.  
Do not merge, force-push, alter main, upload raw observations or delete caches. The registered remote desktop device was offline during the ChatGPT-side audit. No local working-tree state has been inspected.

## First action: exact-head local verification

1. Inspect git status --short --branch, branch name, HEAD, remotes and uncommitted work. Do not reset, stash, clean or overwrite user changes.
2. Fetch the existing R48 branch normally and compare its HEAD with the current remote head. Preserve local changes and report exact commit/tree identity.
3. Read HISTORICAL_SOURCE_MATRIX.json, PHYSICAL_STATE_FRAME_EPOCH_CONTRACT.md, R42_CONTRADICTION_REPLAY_PLAN.md, COBAYA_FREE_ANALYSIS_PATHS.md and R48_T1_SOURCE_AUDIT_REPORT.md.
4. Run only the bounded commands in COBAYA_FREE_ANALYSIS_PATHS.md: R46 target compression and R42 pure numerical/unit tests. Save command, exit code, Python/NumPy/SciPy versions, stdout/stderr, Git SHA and output hash. Do not present synthetic fixtures as source-matched evidence.
5. Add an exact-closure integration test for non-collinear boosts and both zero-boost limits. Verify the bundle branch agrees with compose_velocities_sr; keep the current fixture's first-order vector sum labelled as first-order approximation.
6. Record C01–C16 dispositions individually. Do not silently repair unrelated code or turn missing input into zero/identity/Gaussian placeholders.

## Cobaya-independent route

The R46 compression experiment is NumPy/SciPy-only and has an independently reproduced 40,000-draw reference in COBAYA_FREE_ANALYSIS_PATHS.md. The R42 two-layer benchmark is also Cobaya-free at Python import level, but not an admissible observed-data pipeline: it disables source SHA checks and sums probe likelihoods without a joint covariance/independence proof. Do not run it for observed claims before C01, C07 and C16 are discharged.

## Next scientific work: R48-T2 only

After local identity and bounded tests are recorded, proceed with R48-T2, not T3–T12:

- Reuse R47's ideal Bianchi-I geodesic temperature map and WU-009 P18 conditions.
- Keep intrinsic Bianchi-I anisotropy distinct from WU-010/011 local-observer Lorentz pullback. They are separate physical operators and may only be composed after frame arrows/epoch are explicit.
- Reuse WU-011 Task-5A/5B audit requirements: metric whitening; physical T0 coordinate versus harmonic a00; complete ell=6 source block; rotation-complete finite-difference columns; positive source skies.
- Produce L1_MORPHOLOGY_RESPONSE.md, L1_HARMONIC_OPERATOR_SPEC.json and L1_MOCK_ORACLE_REPORT.json.
- Include mask, beam, pixel, noise, foreground and transfer only when source identities/response are available. Otherwise return typed UNAVAILABLE and keep empirical claim HOLD.
- Do not infer B_star from sigma(t0), Bianchi V/VII_h, polarization, global tilt or vorticity from this temperature-only operator.

One bounded theory derivation, one implementation pass, one adversarial review and at most one repair pass. If local execution or exact source inputs are missing, record the narrow blocker and stop. native_subagent=NOT_RUN unless a real agent launch returns a receipt.

---

# Local coding agent 재개 프롬프트 — R48

아래 내용을 복사해 local coding agent에 전달해.

~~~text
# 역할
너는 htt_base의 이론물리·우주론 연구 구현자이자 보수적인 과학계산 감사자다. 목표는 코드를 무조건 확장하는 것이 아니라 실제 관측자료에서 물리적으로 식별 가능한 tensor kinematical observables를 source-bound likelihood로 추론하고, HTT tensorized five-variable readout이 경쟁 방법보다 실제 이득이 있는지 반증 가능하게 시험하는 것이다.

# 저장소 및 기준점
- Repository: https://github.com/cosmosapjw-quantum/htt_base
- Work branch: research/r48-tensorized-observational-convergence-20261109
- R48 parent: aae07cb83b8899dd7495d550722068d8bcbf3bcb
- Previous stack: PR #571 R47 -> PR #570 R46 -> PR #569 R45 -> PR #568 R44 -> PR #567 R43 -> PR #566 R42 -> PR #565 R41.
- main은 최신 연구 authority가 아니다.
- remote desktop을 사용하지 않는다.
- Raw data/chains는 Git 밖 workdir/raw, workdir/chains에 둔다.
- R48만 변경한다. 보호 브랜치 merge/force-push 금지.

# 절대 목표
1. Low-ell morphology, dipole anomaly, beyond-FLRW kinematics, Bianchi anisotropy classification, directional Hubble, local boost vs global tilt를 독립 연구 루프로 수행한다.
2. theta_K=(sigma_STF2[5], omega[3], A[3], beta_RM[3], beta_MO[3])를 명시적 tetrad, units, epoch, frame과 함께 정의한다.
3. CMB a_lm/BipoSH, source count/redshift/flux/size, Gaia proper motion, SN/CF4 distance의 forward response를 하나의 joint posterior로 연결한다.
4. T=(x,Q,Pi,F,G_F)는 p(theta,psi,eta|D,M,S,W)에서 계산되는 하나의 correlated posterior push-forward로만 취급한다. 독립 likelihood나 다섯 자유 parameter로 쓰지 않는다.
5. Full data, BipoSH/multipole-vector/power-tensor, score/MOPED, nuisance-hardened compression, HTT를 적대적으로 비교한다.
6. Observational claim은 raw byte hash, covariance, transfer, selection, convergence, matched-null calibration 이후에만 한다.

# 먼저 읽을 파일
1. docs/research_program/observational_publication_20261015/R48_TENSORIZED_OBSERVATIONAL_CONVERGENCE_20261109/README.md
2. PUBLICATION_ASSESSMENT_KO.md
3. RESEARCH_DAG.json
4. OBSERVATION_LIKELIHOOD_SPEC.json
5. DATASET_INTAKE_MANIFEST.json
6. SOURCE_REUSE_AND_CONTRADICTION_LEDGER.json
7. MUTATION_GATE_CONTRACT.json
8. LOCAL_AGENT_RESTART_PROMPT_KO.md
9. docs/research_program/observational_publication_20261015/R47_SOLVER_FREE_MORPHOLOGY_LIKELIHOOD_20261109/METHODS_NO_BOLTZMANN.md
10. R42 source code, Cobaya receipt, contradiction ledger, competitive benchmark.

# 연구 루프 규약
- 반드시 $physmath-research-loop를 사용하되 한 세션/턴에 DAG task 하나만 수행한다.
- 현재 재개 지점은 R48-T1. R48-T0는 metadata 및 targeted source audit까지 수행되었으나 모든 PR diff를 읽었다고 주장하지 않는다.
- 이론 루프는 R2 prior art -> R3 assumptions/claim -> R4 model -> R5 derivation -> R6 independent check -> R7 computation -> R8 decision -> R10 handoff 중 필요한 단계만 고른다.
- 구현은 C1 design -> C5 implementation -> C6 tests -> C7 physical validation -> C8 numerical validation -> C9 independent review -> C10 handoff를 명시적으로 고른다.
- subagent를 실행하지 않았다면 NOT_RUN로 기록한다.
- 한 번의 bounded derivation, 구현, adversarial review, 최대 한 번의 repair 후 PASS_SCOPED/FAIL/BLOCKED 결정. 감사의 무한 확장 금지.

# 최우선 과제 R48-T1
- Git status, branch/head 확인. 사용자 local work를 덮어쓰지 않는다.
- R42-R47 PR parent/head, source blob, receipt의 SHA 보존.
- SOURCE_REUSE_AND_CONTRADICTION_LEDGER C01-C10을 실제 코드에 대조한다.
- hard-coded source response constants, Cobaya cached sampler fallback/receipt synthesis, fake ESS fallback, beta vector addition, BianchiTransferAdapter NotImplementedError를 file:line 및 최소 재현 테스트로 확인한다.
- 17D theta frame, reference event, units, tetrad, rotation representation과 probe epoch transfer를 문서화한다.
- HISTORICAL_SOURCE_MATRIX.json, PHYSICAL_STATE_FRAME_EPOCH_CONTRACT.md, R42_CONTRADICTION_REPLAY_PLAN.md를 산출한다.
- 현재 task 범위 밖 source는 수정하지 않는다.

# 여섯 독립 이론 루프

## R48-T2 / L1: Low-ell morphology -> physical response
- Objects: full real a_lm^T; E/B는 polarization transfer가 검증된 경우만; BipoSH A^{LM}_{l1l2}; multipole vectors; power tensor; parity/phase summaries.
- Frequency, beam, pixel window, mask, filtering, component separation, calibration, noise, foreground를 map observation operator에 포함한다.
- R47 solver-free Bianchi-I 지오데식 temperature map을 구현하되 target은 emission/observer integrated B_*이며 present sigma(t0)가 아니다.
- n->-n parity, B=0 isotropic limit, rotation covariance, quadrature convergence, exact/small-B expansion, masked harmonic oracle 검사.
- Transport equation/derivative residual 없이 temperature quadrupole를 sigma로 해석하지 않는다.

## R48-T3 / L2: Dipole anomaly
- Quaia G20.0을 cleaner primary, G20.5 sensitivity, NVSS 별도, RACS-low independent replication.
- Redshift, flux/magnitude, angular size, source evolution/bias, randoms, dust/star/crowding/scan law, local LSS를 포함한 selected point process.
- Nadolny et al. 2021은 직접 선행연구다. 단순 redshift tomography를 novelty라 주장하지 않는다.
- local observer boost vs intrinsic clustering/global anisotropy를 held-out redshift shell/flux cut/tracer로 비교.
- Source catalog에서 각 응답 slope 재계산. 고정 rescaling 금지.

## R48-T4 / L3: Beyond-FLRW kinematics
- Radial redshift response와 Gaia source-level proper-motion likelihood, external ICRF spin tie.
- VSH E1, B1, E2를 source covariance, scan-law/systematics와 함께 모델링.
- B1은 외부 inertial frame tie 전까지 frame spin + physical rotation.
- Nuisance projection 후 identifiable functional만 추론하고 kernel을 보존.

## R48-T5 / L4: Anisotropy/Bianchi classification
- Structure constants와 homogeneous metric parameterization, Jacobi 및 Gauss-Codazzi constraints.
- Spatial STF Ricci, Weyl/derivative functional, observable transfer. Rotations와 locally equivalent group presentation으로 quotient.
- Bianchi I, V, VII_h는 별도 forward model. BI transfer에서 V/VII_h extrapolation 금지.
- Temperature-only BI 결과는 그 제한 템플릿과의 compatibility일 뿐 family identification이 아니다.

## R48-T6 / L5: Directional Hubble
- h(n)=Theta/3+sigma_ab n^a n^b-A_a n^a, H_dir(0,n)=c h(n)부터 시작. Signature(-,+,+,+)와 past-ray convention 고정.
- Pantheon+ observed magnitude/distance modulus 및 full covariance, calibration/selection nuisance.
- CF4는 원 individual distance data와 group/calibrator/covariance provenance만. reconstructed velocities를 독립 데이터로 사용 금지.
- H_ratio=cz/D_L와 H_diff=c/[d_z(D_L/(1+z))] 구분.
- cubic distance coefficient와 curvature-history invariant는 finite-z remainder가 지지할 때만.
- Heinesen 2021, Maartens et al. 2024, Boubel et al. 2025와 직접 비교. Local-structure validity는 Sarma et al. 2026 참조.

## R48-T7 / L6: Local boost vs global tilt
- Radiation R, matter/source M, observer O frame, Lorentz matrix arrow convention 확정.
- Lambda_RM와 Lambda_MO 정확 합성. beta vector sum을 exact로 사용하지 않는다.
- CMB dipole/aberration, source count/flux/size/redshift, astrometry, depth evolution, cross-tracer consistency 포함.
- Local flow, selection, source evolution, frame spin, common LSS marginalize.
- Dipole alignment 또는 한 redshift shell로 global tilt를 판정하지 않는다.

# 핵심 통계 모델
Gaussian blocks:
log L = -1/2 (D-mu)^T C^-1(D-mu) -1/2 log det C + const.
C에는 statistical noise, common calibration, foreground residual, survey window, common LSS, cross-probe terms. Independence가 검증된 경우만 block diagonal.
Count catalogues:
log L = sum_i log lambda(x_i) - integral lambda(x) dx,
lambda=nbar(z,F,size)*selection(n,z,F,size)*(1+Delta(theta,psi)).
CMB:
d=R_map a_lm(theta,psi)+noise+foreground+systematics.
C_ell-only Planck likelihood로 a_lm phases/morphology 추론 금지.
Identifiability:
J_eff=(I-P_nuis) C^-1/2 dmu/dtheta.
l^T theta는 ker(J_eff) subset ker(l^T)일 때만 point identifiable.
Fixed covariance local score t=J^T C^-1(D-mu0). Parameter-dependent covariance이면 covariance derivative score를 추가.
Nuisance hardening은 local fiducial approximation이며 global sufficiency가 아니다.
Target-specific HTT information loss:
E_D[KL(p(Psi|D)||p(Psi|T))]=I(Psi;D|T)
for deterministic T under declared joint model. Psi는 B_*, identifiable shear functional, beta component, h0(n) 등 사전에 고정한다.

# Cobaya/calibration gates
- sampler가 없는데 diagnostics를 만드는 코드를 제거한다. ESS를 row count에서 추정하거나 walltime/Rhat를 하드코드하지 않는다.
- 실제 independent chains, trace/rank, rank-normalized split Rhat, bulk/tail ESS, multimodality 확인.
- 보수적 초기 기준: split-Rhat < 1.01, 주요 scalar target bulk/tail ESS > 1000. 다른 기준은 사전 등록하고 이유를 쓴다.
- Direct likelihood oracle와 injection/recovery를 full chain 전에 실행한다.
- Exact-model SBC, selection mocks, matched E2E null 실행. PR4/NPIPE E2E가 없으면 anomaly FPR/evidence calibration을 BLOCKED 처리.
- R42 result는 현재 source와 data hash로 재현 전까지 인용하지 않는다.

# Required datasets
1. Planck PR4/NPIPE: https://data.cmb-s4.org/planck_pr4.html, https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/NPIPE_Introduction
   Frequency T/Q/U, split/half-ring, low-res covariance, masks, effective beams, matched simulations. E2E가 접근 불가면 명시적으로 BLOCKED. PR3 FFP10 null을 PR4/NPIPE에 섞지 않는다.
2. PR3/FFP10 separate: https://pla.esac.esa.int/pla/ and https://irsa.ipac.caltech.edu/data/Planck/release_3/; only matching SMICA PR3 map+simulation.
3. Quaia: https://irsa.ipac.caltech.edu/data/Quaia/overview.html and https://zenodo.org/records/10403370. G20.0, 10x random, relative selection map, templates; G20.5 sensitivity.
4. NVSS: https://www.cv.nrao.edu/nvss/NVSSlist.shtml and https://www.cv.nrao.edu/nvss/anonftp.shtml.
5. RACS-low DR1: https://www2.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/racs/; replication only.
6. Pantheon+: https://github.com/PantheonPlusSH0ES/DataRelease; exact analysis vector/full covariance/row order inspect.
7. Gaia DR3/CRF3: https://gea.esac.esa.int/archive/; source-level PM covariance and ICRF spin tie.
8. CF4: https://cdsarc.cds.unistra.fr/viz-bin/cat/J/ApJ/944/94; original distances only.
9. DESI BAO: https://data.desi.lbl.gov/; isotropic background control, not preferred-axis signal absent angular clustering/randoms.

# Adversarial benchmark
Generative models: FLRW+LSS; local boost; Bianchi I restricted template; Bianchi V/VII_h only if valid transfer exists; tilted multi-fluid; local void/inhomogeneity; phenomenological multipole+systematics.
Inference/readout methods: raw map/catalogue likelihood; BipoSH; multipole vectors/power tensor; score/MOPED; nuisance-hardened score; HTT.
Use blinded train/validation/test mocks with identical mask/beam/selection. Report SBC, coverage, null FPR, power, posterior KL, held-out predictive score, false-family-label rate, nuisance/model mismatch. Include ablations for x,Q,Pi,F,G_F while respecting dependencies.

# Machine-readable outputs
- Validate JSON against schema before commit.
- Include git SHA, blob SHA, source IDs/SHA256, config hash, seed, package versions, measured runtime, actual chain paths.
- No absolute machine paths committed. Use relative paths/env variables.
- Every result claim links to source or artifact hash.

# Done criteria
1. Formula/assumptions and claim status recorded.
2. Code change only after executable failing test.
3. Physics/numerics/tests verified and receipts committed.
4. Contradiction ledger updated without erasing failure.
5. One adversarial review and one bounded repair.
6. Report exact task id, changed paths and next task.
7. Missing source/data => BLOCKED, never fake substitute.

# First action
Execute R48-T1 only. Check Git status, branch and head. Reconcile C01-C10 against actual code and record exact file:line/blob SHA. Protect local edits. Do not launch production Cobaya. Inspect official product manifest and disk capacity before downloading large Planck files.
~~~
