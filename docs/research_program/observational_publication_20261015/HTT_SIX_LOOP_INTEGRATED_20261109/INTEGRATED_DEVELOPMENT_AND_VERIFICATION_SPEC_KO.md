# HTT six-loop 통합 연구·개발 규약

기준일: 2026-11-09 (Asia/Seoul)  
Repository: cosmosapjw-quantum/htt_base  
Canonical branch: research/r48-tensorized-observational-convergence-20261109  
Canonical HEAD at integration: 7ea9826cf62988dc5405e9a88e905619071ae0f6  
Canonical DAG: INTEGRATED_SIX_LOOP_DAG.json

## 1. 통합 범위와 과학적 목표

최근 PR #565–#572는 여덟 개의 독립 프로젝트가 아니라 R41 publication gate → R42 six-loop/competitor architecture → R43 local identifiability → R44 Bayes-factor sufficiency → R45 finite-model posterior loss → R46 target-posterior compression → R47 restricted solver-free Bianchi-I morphology → R48 tensorized state/source/frame contract와 Bianchi geometry diagnostics로 이어지는 stacked checkpoint 계열이다.

원래 여섯 주제의 의미를 유지한다.

1. L1 low-ell morphology and physical observable operators
2. L2 CMB/source-count dipole and cross-tracer redshift/selection decomposition
3. L3 beyond-FLRW kinematical tensor functionals and inverse problem
4. L4 anisotropy/Bianchi algebra, geometry, local equivalence and family identifiability
5. L5 directional Hubble observables and optical distance-redshift jets
6. L6 local observer boost versus global radiation-matter tilt

R43–R46은 일곱 번째/여덟 번째 관측 주제가 아니다. 여섯 loop가 공유하는 identifiability, model evidence, posterior information loss와 target compression foundation이다. R47 Bianchi-I endpoint map은 L1/L4에 걸친 제한된 물리 응답 후보이고, R48 geometry-only Bianchi classifier/mock은 L4의 기하·대수 진단일 뿐 실제 관측 transfer가 아니다.

## 2. 통합 권위와 상태 의미

실행 순서와 acceptance의 유일한 권위는 INTEGRATED_SIX_LOOP_DAG.json이다. 이 문서는 설계·규약 설명이며, R41–R48 과거 DAG 파일은 immutable historical inputs로 유지한다.

과거 DAG의 COMPLETE_VALIDATED 문자열을 현재 empirical PASS로 자동 변환하지 않는다. R41 여섯 loop의 "complete"는 당시 publication/design/theory gate 범위에 한정한다. R42 이후 실제 데이터 다운로드, parser, response operator, matched null, full covariance, production sampler 수행 여부는 각각 별도로 확인한다.

상태:
- PASS_SCOPED: 적힌 범위의 수학/설계/코드 작업 통과. 타 단계로 승격 금지.
- PASS_SOURCE_BOUND: 정확한 source bytes/release, parser, selection, mask/window, covariance, forward operator가 고정된 단일 채널 결과.
- PASS_CALIBRATED: source-bound result와 authentic matched-null, SBC/coverage/PPC/systematics calibration 통과.
- PASS_EMPIRICAL: 사전등록 독립 holdout/replication과 adversarial competitor 통과. 주장별로만 적용.
- BLOCKED: 필요한 input/권한/runtime/operator 부재. 독립 task는 계속.
- HOLD: 데이터/이론이 주장 승격을 지지하지 않거나 반증/degeneracy가 남음.
- DEFERRED_SCOPE: 이 실행 epoch에서 의도적으로 보류.
- SUPERSEDED: 더 나은 후속 task/contract로 대체.
- QUARANTINED: 역사적 산출물은 보존하되 현행 claim evidence로 사용 금지.
- NOT_RUN: 수행하지 않았거나 receipt 없음. 성공/실패로 말하지 않음.

각 task는 필요하면 theory/operator/source/calibration/inference/claim 단계를 별도로 기록한다.

## 3. Source authority, provenance, claim evidence

Source precedence:
1. live Git branch/ref, exact commit/tree, repository source/test
2. integrated DAG와 claim ledger의 최신 branch version
3. 실제 local source bytes 및 execution receipts
4. official release documentation, original derivations, peer-reviewed literature
5. 이전 PR 보고서 및 historical DAG
6. 대화·메모리·AI 요약

낮은 권위의 자료와 높은 권위의 자료가 충돌하면 contradiction ledger에 둘 다 보존한다. 모델 기억, PR 설명, YAML의 "complete" 문자열만으로 실행 여부를 추론하지 않는다.

재사용 주장에는 claim_id, text, state, evidence_state, scope, source_ref, commit_sha, blob_sha, line/section, run_id, input_hashes, limitations, supersedes, next_gate를 기록한다. 출처 미확인은 UNRESOLVED_SOURCE 또는 NOT_RUN.

Actual data manifest에는 source ID, survey/release, official URL, retrieval UTC timestamp, exact local path, byte size, SHA256 from downloaded bytes, format/schema, row ID/order, units/frame, selection/mask/window/beam/transfer, parser commit, random/null ensemble, statistical/systematic covariance, overlap/calibration, validation command/exit/logs가 필요하다.

Raw data/chains/credentials는 Git에 넣지 않는다. 기본 local layout: workdir/raw/observational/<release>/<dataset>/. 파일명/DOI/URL/manifest만으로 실제 byte identity를 주장하지 않는다. 같은 하늘의 reprocessing/frequency products를 독립 sky로 세지 않는다.

Missing data behavior:
- authentic matched null이 없으면 Pi=SYNTHETIC_ONLY 또는 UNAVAILABLE.
- real shell data vector/full cross-shell data covariance가 없으면 G_F.data_covariance=UNAVAILABLE.
- physical response가 없으면 operator=UNAVAILABLE 또는 EXTERNAL_TRANSFER_CONDITIONAL.
- source가 없는 채널은 BLOCKED/HOLD로 두되 독립 이론 task는 계속한다.

## 4. 물리·수학 설계 규약

### 4.1 Physical state

\[
\theta_K=(\sigma_{ab}/H,\ \omega_a/H,\ A_a/(cH),\ \beta_{RM},\ \beta_{MO})
\in\mathbb R^{5+3+3+3+3}.
\]
sigma는 spatial STF rank-2, omega axial vector, A polar vector, beta_RM radiation-to-matter, beta_MO matter-to-observer다. Chart order, basis, sign, normalization 변경은 명시적 migration 없이는 금지한다.

### 4.2 STF5

Cartesian trace-free chart:
\[
(S_{xx},S_{yy},S_{xy},S_{xz},S_{yz}),\quad S_{zz}=-S_{xx}-S_{yy}.
\]
Frobenius Gram:
\[
G_{\rm STF5}=\begin{pmatrix}
2&1&0&0&0\\1&2&0&0&0\\0&0&2&0&0\\0&0&0&2&0\\0&0&0&0&2
\end{pmatrix}.
\]
Norm/rank/Fisher/prior/eigenvalue/orthogonality는 이 Gram 또는 선언된 orthonormal STF chart로 계산한다. Component-wise Euclidean norm은 금지.

### 4.3 Frames and epochs

방사선 R, 물질 M, 관측자 O, source S, catalogue/instrument C를 type-distinct로 유지한다. 각 observable은 source congruence, observer congruence, tetrad/orientation, reference event/epoch, transport/evolution map, frame arrows, sign, unit을 선언한다. Exact ordered Lorentz composition을 사용하고 non-collinear boost의 Wigner rotation을 보존한다. beta_RM, beta_MO, local peculiar motion, global fluid tilt, frame spin을 같은 양으로 부르지 않는다.

### 4.4 Observation operator

모든 carrier는 tensor rank, symmetry, SO(3)/O(3) representation, parity, basis, units, frame, epoch, redshift support, source/release, selection, mask/window, transfer, covariance identity를 가진다. 코드에 숫자가 있다는 사실은 물리 operator의 증거가 아니다. 모든 response constant는 유도/official calibration이 있거나 nuisance/mock constant로 type되어야 한다.

### 4.5 Five-variable semantics

T=(x,Q,Pi,F,G_F)는 한 common posterior/compatibility law의 joint push-forward다.
- x: sample-wise physical tensor functionals and observed/predicted carriers.
- Q: source-backed anchor/gauge/margin/availability state. UNAVAILABLE 허용.
- Pi: posterior, authentic matched-null, predictive law에 조건부인 exceedance.
- F: 명시적 집합의 directional support/occupancy 및 meaningful anchor. Equal-area sphere convergence 포함.
- G_F: redshift/distance depth path, full cross-shell dependence, data/posterior covariance 분리.

다섯 marginal을 곱해 likelihood를 만들지 않는다. 각 draw의 stable sample_id를 resampling/splitting/aggregation 전 과정에서 보존한다.

### 4.6 Identifiability and information

Fixed-covariance Gaussian mean model:
\[
J_{\rm eff}=(I-P_\eta)C^{-1/2}J_\theta.
\]
Target phi(theta)는 local point-identifiable only if:
\[
\ker(J_{\rm eff})\subseteq\ker(D\phi).
\]
C가 parameter-dependent이면:
\[
F_{ij}=\mu_{,i}^{T}C^{-1}\mu_{,j}
+\frac12\operatorname{tr}(C^{-1}C_{,i}C^{-1}C_{,j}).
\]
Non-Gaussian point-process는 실제 score/Hessian 또는 simulation-based identifiability를 사용한다. Singular value/rank에는 physical/prior parameter metric을 선언한다.

R44 BF sufficiency, R45 finite model posterior loss, R46 target posterior loss는 서로 다른 estimand다. Target sufficiency → full parameter sufficiency → model evidence sufficiency로 승격하지 않는다.

## 5. Six-loop contracts

각 loop는 다음 minimum records를 만든다: ASSUMPTIONS.md, DERIVATION.md, OPERATOR_SPEC.json, SOURCE_MANIFEST.json, COMPETITOR_MATRIX.json, NULL_AND_CALIBRATION.json, TEST_RECEIPT.json, CLAIM_LEDGER.json, NEXT_TASK.json.

### L1 low-ell morphology
Observables: a_lm T/E/B, stored-real morphology tensors, BipoSH/off-diagonal covariance. Deterministic template와 stochastic covariance response를 분리한다. Planck mask/beam/pixel/frequency/foreground/noise operator는 data와 simulation에 동일 적용한다. R47 BI map은 isotropic sharp last-scattering + collisionless assumptions의 conditional temperature response다. E/B physical transfer나 current shear로 바꾸지 않는다. Acceptance: pixel-vs-harmonic direct oracle, rotation/parity, quadrature convergence, mask/beam injection, same-release MC calibration.

### L2 source dipole
NVSS, Quaia, RACS를 서로 다른 point process로 둔다. Mask, flux/magnitude cut, spectral index, redshift/evolution, source size, random catalogue, completeness, local structure가 들어간다. Fixed response scale 금지. Missing response는 UNAVAILABLE. Acceptance: selection replay, random/null injection, held-out tracer/cut, overlap/cross-covariance.

### L3 kinematic tensors
Gaia DR3/CRF3 source-level astrometry, full proper-motion covariance, scan law/source selection, epoch, ICRF spin tie. E1/B1/E2는 estimator/carrier 이름이지 자동으로 physical vector-field measurements가 아니다. Acceptance: VSH injection/recovery, frame-spin nuisance projection, identifiable target subspace.

### L4 Bianchi
Abstract Lie-algebra label, metric Lie-algebra orbit, local-isometry class, simply-transitive group presentation을 분리한다. 필요시 Jacobi/Gauss-Codazzi/ADM constraints 적용. Geometry-only Ricci/tilt fingerprint는 BASS solver/physical family transfer가 아니다. Bianchi-I endpoint map은 V/VIIh가 아니다. Family ID는 validated family-specific response, competitor separation, calibrated posterior predictive evidence가 있어야 한다.

### L5 directional Hubble
Local H(n)과 finite-z optical jet을 구별한다. Observer/source congruence, sign, unit, redshift and remainder를 선언한다. Pantheon+ full covariance/row order/calibration 필수. CF4는 conditional. DESI compressed BAO는 background control only.

### L6 boost vs tilt
R/M/O arrows, exact ordered Lorentz composition, Wigner rotation. CMB/count/size/redshift/astrometry별 별도 response. Local flow, intrinsic dipole, selection, calibration, frame spin nuisance projection. One dipole never proves global tilt.

## 6. Generative-model vs readout-method benchmark

두 축을 분리한다.
- Physical generative models: FLRW+LSS, local boost, tilted multi-fluid, Bianchi I/V/VIIh with valid transfer, local inhomogeneity, phenomenological anisotropic metric/systematics.
- Inference/readout methods: full harmonic/pixel likelihood, BipoSH, multipole vectors/power tensor, multi-tracer dipoles, Gaia VSH, hierarchical PV/GP, nuisance-hardened score compression, conventional posterior/convex-depth, HTT joint push-forward.

Each comparison declares common data subset, likelihood, priors/nuisance, selection, covariance, missing channels and compute cost. A shear proxy is never Bianchi.

## 7. Coding and verification

TDD loop:
1. Read exact source/test at HEAD.
2. Add smallest failing test.
3. Derive expected output independently (equation/direct oracle/CAS).
4. Implement the smallest patch.
5. Run targeted tests, compile, schema validation.
6. Run injection/limit/invariance tests.
7. Store exact versions, command, stdout/stderr, exit code and hashes.
8. Independent reviewer is read-only.
9. One bounded repair pass; if still failed preserve receipt and classify failure.

Minimum numerical checks:
- zero anisotropy/boost/tilt, isotropic FLRW, small-parameter asymptotic;
- rotation/parity/basis/tetrad transformations;
- STF Gram;
- exact SR closure/Wigner rotation;
- direct pixel/harmonic/point-process oracle;
- SPD and evidenced cross-probe/cross-shell covariance;
- nuisance rank/kernel/conditioning and threshold sensitivity;
- prior-predictive SBC/PPC/coverage/MCSE;
- same-release matched null;
- actual Cobaya chain, rank-normalized split Rhat, bulk/tail ESS;
- true held-out refits, normalized model evidence.

Local commands (only run paths that exist on exact checkout):
~~~bash
git fetch origin
git status --short --branch
git branch --show-current
git rev-parse HEAD
git rev-parse HEAD^{tree}
python -m compileall -q htt scripts tests
pytest -q tests/r43 tests/r44 tests/r45 tests/r46 tests/r48 htt/bass/diagnostics
python scripts/codex_harness/validate_pr_dag.py
pytest -q tests/contracts/test_research_program_dag.py tests/contracts/test_revision_research_program.py
~~~
Missing path = NOT_APPLICABLE/NOT_RUN, not invented. Targeted tests before broad PR04; optional Cobaya/Astropy collection failures are separate.

## 8. Mutation gates

G0 identity/worktree: repo, branch, HEAD/tree, clean status, PR state, file/blob SHA. Dirty or mismatch => stop writes.
G1 theory: definitions, assumptions, units, boundary/initial conditions, frame/epoch, derivation.
G2 likelihood: normalization, selection, masks/windows, covariance/cross-probe, systematics, duplicate-data-factor audit.
G3 minimal mutation: failing test first, small diff, API compatibility, rollback.
G4 numerical verification: direct oracle, injection, convergence, MCSE, SBC/PPC and actual chain diagnostics.
G5 claim/publication: claim ledger, raw-source manifest, matched null, heldout and independent review.

Forbidden: push main/R47 parent; force push/rewrite; merge/close/mark ready/release without explicit instruction; reset/clean/stash dirty worktree; delete evidence/failures; commit raw data/chains/credentials/private paths; bypass SHA checks; fabricate sampler receipts; cached-chain fallback; magic coefficients; fake physical transfer.

If branch moves, refetch/compare/reconcile. Do not force retry a rejected lease.

## 9. Anti-drift/hallucination self-audit

Before every task handoff answer:
1. Exact branch/commit/tree and clean status?
2. Which file/blob/line or official source supports each claim?
3. Is each number derived, source measured, synthetic, conjectural or unknown?
4. Which commands actually ran, with exit codes/run IDs/log paths?
5. Which contradictions/failures remain?
6. Were units, frame arrows, epoch, STF Gram and covariance preserved?
7. Did I confuse generative theory and readout method?
8. Did I turn an idealized mock into observation?
9. Did I infer completion from PR/DAG/file presence or memory?
10. Does every PASS have exact-head receipt and acceptance evidence?

Unknown stays UNKNOWN. Use evidence tags: ESTABLISHED, LITERATURE_SUPPORTED, DERIVED, CAS_CHECKED, NUMERICALLY_CHECKED, IMPLEMENTATION_VERIFIED, SOURCE_VERIFIED, CALIBRATED, EMPIRICAL_VALIDATED, CONJECTURAL, UNRESOLVED, BLOCKED, NOT_RUN, QUARANTINED.

Never say verified/passed/converged/observed/detected/identified/complete/publication-ready without a corresponding receipt.

## 10. Handoff output

Return exact branch/HEAD/tree/worktree, task ID/status, changed files+hashes, derivation/source/convention, exact commands/exit/tests/CI, actual source bytes/hashes, passed/failed/not-run/blocked, failure class, claim IDs, remaining uncertainty and one next task ID/resume command. Native subagents = NOT_RUN unless actual task ID + returned artifact exist.
