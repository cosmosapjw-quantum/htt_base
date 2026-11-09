# HTT R45 local-agent 재개 프롬프트

이 작업은 R44 이론 및 mock 결과를 재실행하는 것이 아니다. 유한 모형 posterior의 압축 정보손실 항등식과 synthetic 검증은 R45 산출물로 존재한다. 첫 행동은 원격 브랜치의 정확한 상태를 clean checkout하고 테스트를 재현하는 것이다. 현재 ChatGPT 연결 Desktop Commander 장치는 오프라인이므로 이 대화에서 로컬 디스크를 직접 갱신하지 않았다.

## 저장소와 기준

- Repository: `cosmosapjw-quantum/htt_base`
- R44 parent branch: `research/r44-bayes-factor-design-20261109`
- R44 parent commit: `98f7dc75f7eba287bd566bddc17920ba8ae45925`
- R45 branch: `research/r45-model-posterior-information-loss-20261109`
- Expected R45 head: 이 문서가 포함된 PR/branch의 최신 GitHub head SHA로 checkout 시점에 확정한다.
- `main` 직접 push/merge 금지. raw survey data, maps, MCMC chain은 Git에 올리지 않는다.

## R45 이론 계약

유한 모델 인덱스 `M`, `pi_m>0`, 모델별 원자료 law `P_m`, 모든 모델에서 공통인 결정론적 요약 `S=T(Y)`에 대해

`L_M = E KL[p(M|Y)||p(M|S)] = I(M;Y|S) = I(M;Y)-I(M;S)`.

또한 `L_M = sum_m pi_m {KL(P_m||Pbar)-KL(P_m^S||Pbar^S)}`. `L_M=0` iff `M ⟂ Y | S`, 즉 model posterior/pairwise posterior odds가 보존된다. 자연로그 및 TV=`0.5 L1` convention을 쓴다. Pinsker/Jensen은 `E TV <= sqrt(L_M/2)`이고 optimal 0–1 model risk는 deterministic compression 후 감소할 수 없다.

연속 모형 매개변수 `Theta_M`를 포함한 joint posterior는

`I((M,Theta_M);Y|S) = I(M;Y|S) + I(Theta_M;Y|M,S)`

로 분해된다. 첫 항이 0이라고 둘째 항이 0인 것은 아니다. 둘째 항이 0이어도 첫 항은 양수일 수 있다. 이 distinction은 변경 금지.

## 첫 실행: clean checkout과 tests

```bash
git fetch origin
git checkout research/r45-model-posterior-information-loss-20261109
git reset --hard <verified-remote-head>
python -m compileall -q scripts/r45 tests/r45
pytest -q tests/r45
python scripts/r45/run_model_posterior_information_loss.py --seed 20261109 --replications 60000 --output /tmp/R45_MOCK_RESULTS_REPLAY.json
cmp docs/research_program/observational_publication_20261015/R45_MODEL_POSTERIOR_INFORMATION_LOSS_20261109/R45_MOCK_RESULTS.json /tmp/R45_MOCK_RESULTS_REPLAY.json
```

재현 output exact bytes가 다르면 자동으로 실패라 하지 말고 원인(환경/library/serialization/numerical)과 semantic numerical parity를 구분한다. 단, deterministic JSON 재현 계약에서 byte mismatch는 별도로 기록한다. 이 단계에서 source/test 실패를 진단하고, 기존 결과를 덮어쓰기 전에 원인을 보존한다.

## 다음 연구 목적: HTT five-variable summary에 적용

1. `M`은 실제 competitor registry의 모델 family label이고, `Theta_M`은 그 모델의 물리 매개변수다. 우선 R42/R44 model likelihood registry와 원자료 observation contract를 읽고, 모델군·parameterization을 잠근다.
2. `Y`는 공통 raw observation vector와 likelihood contract다. 모델마다 서로 다른 `Y` 또는 model-specific likelihood로 숫자만 비교하지 않는다.
3. `S=T(Y)`는 현재 `T=(x,Q,Pi,F,G_F)`의 공동 posterior/compatibility push-forward다. 다섯 성분을 독립 likelihood factor로 곱하지 않는다.
4. `I(M;Y|T)`와 `I(Theta_M;Y|M,T)`를 따로 추정할 수 있는 simulation-based estimator / exact tractable submodel을 설계한다. Exact likelihood ratio vector는 finite model posterior의 상한 대조군으로 사용한다.
5. Parameter-dependent covariance, mask/window, selection, calibration, foreground and cross-shell covariance를 likelihood registry에서 보존한다. Mean-only scores를 충분통계로 선언하지 않는다.
6. R44의 17D physical chart order `(sigma_STF5, omega_axial3, A_polar3, beta_RM3, beta_MO3)`와 `T=(x,Q,Pi,F,G_F)` 의미를 유지한다.
7. `Pi` empirical path에는 source-matched null samples가 필요하고, `G_F`에는 실제 shell vectors와 full cross-shell data covariance가 필요하다. Random Gaussian fallback은 SYNTHETIC_ONLY 또는 UNAVAILABLE이다.
8. R42 Cobaya callsite가 `matched_null_samples`, `shell_data_vectors`, `cross_shell_data_cov` 전달 여부를 source로 확인한다. Stale chain reuse, `verify_sha=False`, hard-coded `t_run`, unjustified `n_data_eff` 문제는 기존 R44 handoff대로 유지한다.
9. empirical claims / Bianchi identification은 실제 data provenance, physical transfer, likelihood parity, chain diagnostics, SBC와 posterior predictive checks가 확인되기 전까지 HOLD.

## 산출물과 반환

- clean checkout SHA + source/test Git blob identities
- compileall/pytest logs, exact exit codes
- deterministic replay identity and numerical discrepancies
- model registry and common observation contract
- posterior-loss estimator derivation, uncertainty estimator, calibration mocks
- per-model `I(M;Y|T)` and within-model `I(Theta_M;Y|M,T)` diagnostics
- source hashes, likelihood/covariance/selection/transfer versions
- unresolved gate, one exact next action

Native subagent dispatch는 실제 host capability가 제공될 때만 사용한다. Multiprocessing/role-play를 native delegation으로 부르지 않는다. No real data/physical transfer means no empirical inference claim.
