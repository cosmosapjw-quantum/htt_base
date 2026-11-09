# HTT R44 Local Agent 재개 프롬프트

아래 내용을 새로운 local-agent 작업에 그대로 전달한다. R44 mock/proof는 이미 완료된 선행 산출물이며, 여기서부터는 **실제 source-bound likelihood / 데이터 provenance / Cobaya 실행**으로 넘어간다. 동일 mock을 재실행해 새로운 결과처럼 보고하거나 R43/R44 이론 루프를 처음부터 반복하지 않는다.

---

## 역할과 저장소 기준

너는 `cosmosapjw-quantum/htt_base`의 이론·관측 우주론 분석 agent다.

- Parent branch: `research/r43-theory-identifiability-mock-20261109`
- Parent commit: `8e70c15da595ecfcd25e097e44fbd13f3aa59903`
- R44 branch: `research/r44-bayes-factor-design-20261109` (현재 PR 기준 SHA는 사용자가 제공한 handoff/최신 GitHub 조회로 확정)
- 작업 대상: R44 후속 DAG `LOCAL_AGENT_EXECUTION_DAG.yaml`의 `R44-LA-00`부터 시작한다.
- `main` 직접 push/merge 금지. R44 branch에 이어서 작업하고 새 변경은 별도 commit/PR에 둔다.
- Remote Desktop 사용 금지. 승인된 로컬 shell/Python/Git 및 GitHub 경로만 사용한다.
- survey raw data, MCMC chain, 대형 map/simulation 파일은 Git에 commit하지 않는다. manifest, parser, likelihood, tests, compact result, checksums만 commit한다.

## 과학적 고정 계약

물리 chart는
\[
\theta_K=(\sigma_{ab}/H,\;\omega_a/H,\;A_a/(cH),\;\beta_{RM},\;\beta_{MO})
\in\mathbb R^{5+3+3+3+3}
\]
의 17차원이다. 다섯 출력
\[
T=(x,Q,\Pi,F,G_F)
\]
은 하나의 공통 posterior/compatibility law의 joint push-forward다. 다섯 독립 parameter 또는 likelihood factor가 아니며 `p(x)p(Q)p(Pi)p(F)p(G_F)`로 factorize하지 않는다. scalar `x_C`는 보조 ablation이며 메인 경쟁대상이 아니다.

비교할 physical generative model은 FLRW+LSS/null, local observer boost, radiation-matter/global tilt, 물리적 Bianchi transfer family, full HTT kinematic model이다. Bianchi shear proxy를 실제 Bianchi solution/transfer로 부르지 않는다. readout 비교는 raw posterior, BipoSH, multipole vectors, multi-tracer dipole, Gaia VSH, score/nuisance-hardened compression, convex depth, HTT tensor five-variable를 포함한다.

## R43/R44에서 이미 성립한 결과와 재사용 범위

1. R43: nuisance-projected efficient Fisher의 regular local functional-identifiability criterion `ker(I_eff) subset ker(D phi)`를 유도했고, global fibre identification과 구분했다.
2. R43: deterministic readout의 score contraction/data-processing inequality를 유도했다.
3. R44: 공통 covariance Gaussian submodel family에서는 `q=X^T C^{-1}(y-mu)`가 모든 competitor Bayes factor를 보존한다. 고정 full-chart reference posterior `N(m,V)`는 `q=V^{-1}m-B^{-1}b`를 복원한다. 이 조건에서 `V`가 fixed이면 `m` 단독도 충분하다.
4. R44: model-dependent covariance의 경우 동일한 q를 갖는 두 mock 데이터가 서로 다른 log-BF를 갖는 counterexample를 구성했다.
5. R44: anisotropic observation metric은 동일한 vector norm에 서로 다른 model evidence를 허용한다. `beta_MO` mean vector만으로는 `M1 local boost`와 `M2 global tilt+boost`를 비교할 수 없는 counterexample를 구성했다.
6. R44: `delta=beta_RM-beta_MO`에 대한 c-optimal redshift/anchor design이 D-optimal design과 다른 목적을 최적화함을 synthetic design에서 보였다.

이 결과들은 모두 이론/합성 근거다. 실제 우주론 관측량에 대한 evidence가 아니다. 정확한 수식·가정·숫자는 R44 `R44_THEORY_AND_MOCK_RESULTS_KO.md`, `R44_MOCK_SPEC.yaml`, `R44_MOCK_RESULTS.json`을 원문으로 읽는다.

## 실행 순서

### A. 시작 시 상태 확인

1. 최신 `R44` branch head, PR state, R43 parent를 GitHub에서 조회한다. 기존 SHA를 추정하지 않는다.
2. `R44_THEORY_AND_MOCK_RESULTS_KO.md`, `R44_MOCK_SPEC.yaml`, `R44_MOCK_RESULTS.json`, `LOCAL_AGENT_EXECUTION_DAG.yaml`, `LOCAL_AGENT_IO_CONTRACT.yaml`을 읽는다.
3. R44의 local code checks를 해당 환경에서 재실행해 현재 설치 상태를 확인한다. 이미 검증된 numerical output을 필요 없이 다시 만들지 않는다.
4. 변경 전 current source identity를 기록한다. 특히 `scripts/r42/run_cobaya_joint_inference.py`, `scripts/r42/run_r42_two_layer_benchmark.py`, `htt/src/common/htt_five_variable_state.py`, source-bound observation operators, transfer registry를 본다.

### B. R42 실행 provenance의 결함을 실제로 고친다

R42에서 발견된 것은 capability가 아니라 실행 경로 문제다.

- `construct_r42_five_variable_state(...)` API는 `matched_null_samples`, `shell_data_vectors`, `cross_shell_data_cov`를 받지만 현재 Cobaya runner 호출은 이 인자들을 넘기지 않는다.
- 해당 Cobaya receipt는 `has_data_covariance=false`, `effective_sample_size=53`, `ess_passed=false`를 기록한다.
- `run_cobaya_joint_inference.py`는 기존 chain이 있으면 존재 여부만으로 sampling을 skip하고 `t_run=553.24`를 하드코딩하는 branch가 있다. chain/config/data/code hashes가 일치하지 않으면 stale reuse다.
- two-layer benchmark operator는 여러 곳에서 `verify_sha=False`로 생성된다.
- BIC `n_data_eff=1_720_000`은 유효 독립 자료수의 근거가 없으면 BIC로 보고하지 않는다.
- optimizer가 `-loglike + penalty`를 최소화하면 unpenalized MLE/loglike라고 표기하지 않는다.
- SBC는 prior에서 data를 생성하고 실제 posterior를 sampling해야 한다. truth 주변 Gaussian cloud를 posterior라고 부르지 않는다.
- hard-coded FPR/power, source id를 checksum으로 간주하는 검사, 임의 Gaussian Pi null을 empirical-calibrated라고 부르는 코드를 제거한다.

`Pi`는 source-matched Planck FFP/NPIPE end-to-end MC, catalogue randoms/selection, Gaia scan-law/systematic null 등 실제 law input이 없으면 `SYNTHETIC_ONLY` 또는 `UNAVAILABLE`로 반환한다. empirical claim path에서 random Gaussian fallback을 금지한다.

`G_F`에는 실제 shell별 observed functional vectors와 전체 cross-shell observational covariance를 전달한다. posterior push-forward covariance와 data covariance를 구별하고 각각 source/receipt를 남긴다. 실제 covariance가 없으면 `has_data_covariance=false` 및 unavailable status를 보존한다.

### C. 실제 데이터와 source provenance

R42의 `SOURCE_LOCK_MANIFEST.json`와 공식 release 기록을 출발점으로 삼는다. 최소 후보는 Planck PR4/NPIPE, Gaia DR3/CRF3, Quaia DR1, NVSS, RACS-low DR1, Pantheon+/DES-SN5YR, Cosmicflows-4 등이다. 범위와 실제 접근 가능 여부는 파일 단위로 검증한다.

각 다운로드마다 `LOCAL_AGENT_IO_CONTRACT.yaml`에 정의된 source manifest 필드를 채운다. 실제 byte SHA-256, byte size, release/version, retrieval time, schema, rows, coordinate frame/units, mask/window, selection, random/null ensemble, covariance, calibration/foreground, transfer version, parser commit을 기록한다. source manifest 파일이 있다고 실제 byte identity를 검증한 것은 아니다.

### D. model/evidence 계약

R44 exact-BF theorem을 적용할 때 아래 조건을 모두 확인한다.

- 같은 raw observation vector/selection contract를 사용한다.
- nuisance integration 이후 common known base covariance를 쓴다.
- 모든 competitor의 mean response가 하나의 고정 chart X의 submodel로 들어간다.
- posterior/readout map이 model label마다 달라지지 않는 common statistic이다.
- prior와 design metadata가 고정되어 있다.

조건을 못 맞추면 theorem을 강제로 적용하지 말고 model-specific likelihood/covariance/selection을 적분해 비교한다. 그때 fixed-C score q만으로 evidence가 복원된다고 주장하지 않는다. covariance alternative의 residual quadratic form과 selection normalization을 포함한다.

### E. real c-optimal design

R44의 synthetic `g(z)=z/(z+0.12)`를 물리 response로 사용하지 않는다. 실제 operator, redshift selection, cross-shell covariance로 `I_eff(w)`를 구성한다. 먼저 data-only identifiability rank와 prior-regularized precision을 분리한다. 목표 `delta=beta_RM-beta_MO`에 대해 `c^T I_eff(w)^+ c`를 최소화하고 D-optimal 및 standard uniform design과 비교한다. independent observer-velocity/reference-frame anchor의 정보원과 calibration covariance를 명시한다. 다른 target(예: shear, omega/frame spin, acceleration)에는 별도 `c`와 observable operator를 사용한다.

### F. Cobaya / SBC / predictive validation

- source-bound likelihood callable을 실제 Cobaya에서 실행한다. MCMC code를 hand-coded MH로 대체한 뒤 Cobaya라고 표기하지 않는다.
- stale chain은 config, code commit, likelihood, data manifest hash가 전부 일치할 때만 재사용한다.
- rank-normalized split-Rhat, bulk ESS, tail ESS를 parameter별로 보고한다. Rhat 수치 하나로 종료하지 않는다.
- SBC는 각 반복에서 prior draw -> generative likelihood data draw -> 실제 posterior sampler -> rank 계산 순서다.
- null/FPR, power, interval coverage, posterior predictive, held-out probe/shell predictive는 서로 다른 지표로 보고한다.
- model evidence는 sampler/estimator를 명시하고 prior-volume sensitivity와 반복-run uncertainty를 기록한다.

## 반드시 반환할 것

1. branch/commit/tree SHA 및 exact diff summary
2. data byte manifest와 actual SHA256
3. likelihood/transfer/covariance/selection contract와 code path mapping
4. 실제 Cobaya config, chain hashes, per-parameter diagnostics
5. empirical Pi null provenance 및 G_F data covariance provenance
6. M0/M1/M2/Bianchi/HTT competitor 결과, model evidence와 held-out predictive metrics
7. real c-optimal 대 D-optimal design과 target-specific uncertainty
8. tests/build/runtime receipts, 실패 원인과 정확한 blocker
9. claim ledger와 publication decision 변경 내용
10. unfinished tasks, 정확한 resume command와 local file paths

어떤 실제 data/solver/chain을 실행하지 못했다면 `NOT_RUN`, `INPUT_MISSING`, `RUNTIME_BLOCKED` 등 정확한 상태로 기록한다. 합성 결과를 관측 결과로 승격하지 않는다.

---
