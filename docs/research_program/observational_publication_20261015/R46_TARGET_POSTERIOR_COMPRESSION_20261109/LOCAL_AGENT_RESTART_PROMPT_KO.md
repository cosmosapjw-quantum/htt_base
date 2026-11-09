# HTT R46 local-agent 재개 프롬프트

## 저장소 상태
- Repository: `cosmosapjw-quantum/htt_base`
- Parent R45 commit: `3a6d76a884214e309b69d6b548bc2277b25bbe88`
- Branch: `research/r46-target-posterior-compression-20261109`
- `main` 직접 수정/merge 금지.
- Local Desktop Commander device는 마지막 확인에서 OFFLINE. 이 문서는 Git branch handoff이며 workstation disk를 직접 변경하지 않았음.

## 첫 행동: clean checkout/replay
```bash
git fetch origin
git checkout research/r46-target-posterior-compression-20261109
git reset --hard <verified-origin-head>
python -m compileall -q scripts/r46 tests/r46
pytest -q tests/r46
python scripts/r46/run_target_posterior_compression.py --seed 20261109 --replications 40000 --output /tmp/R46_MOCK_RESULTS_REPLAY.json
cmp docs/research_program/observational_publication_20261015/R46_TARGET_POSTERIOR_COMPRESSION_20261109/R46_MOCK_RESULTS.json /tmp/R46_MOCK_RESULTS_REPLAY.json
```
Byte/content/structural/numerical/semantic identity를 구분한다. Byte mismatch만으로 scientific mismatch를 선언하지 않는다.

## R46 과학 계약
- `Psi=g(Lambda)`, common raw observation `Y`, common deterministic summary `S=T(Y)`.
- `E KL(P(Psi|Y)||P(Psi|S)) = I(Psi;Y|S)`.
- `I(Psi;Y|S) <= I(Lambda;Y|S)`; zero target loss iff `Psi independent of Y given S`.
- Square-loss risk gap: `R_S-R_Y=E Var(E(Psi|Y)|S)`.
- Gaussian linear model: `K=A^T Sigma H^T(H Sigma H^T+R)^(-1)`. A linear summary `S=B^T(Y-Hmu)` preserves the whole target posterior iff `row(K) subset row(B^T)`; minimum linear rank is `rank(K)`. Fixed-known prior/likelihood only.
- Target posterior preservation does not imply full latent posterior, model-index posterior or Bayes-factor preservation.
- Isotropic Gaussian norm summary preserves squared-radius posterior; anisotropic prior/noise can break it.

## HTT-specific obligations
1. Current 17D chart order remains `(sigma_STF5, omega_axial3, A_polar3, beta_RM3, beta_MO3)`.
2. R46 chart-space targets are synthetic linear functionals only, not physical invariants or empirical estimators.
3. Derive physical shear/vorticity/acceleration invariants from authoritative tensor basis, metric and STF Gram matrix. Do not apply Euclidean norms to arbitrary STF components without the Gram matrix.
4. Preserve `T=(x,Q,Pi,F,G_F)` as one joint posterior/compatibility push-forward, never independent likelihood factors.
5. Model-dependent covariance, selection, masks, windows, calibration, foreground or transfer functions must remain in the common likelihood contract.
6. Pi requires authentic matched-null samples; G_F requires actual shell vectors and full cross-shell data covariance. No random-Gaussian empirical fallback.
7. Cobaya chain reuse requires exact config/likelihood/source/code identity and full chain diagnostics. Keep R44/R45 stale-chain and covariance handoff cautions.
8. No observed-data, physical Bianchi, Cobaya production, empirical detection or family-identification claim until source-bound calibration gates pass.

## 다음 산출물
- `PHYSICAL_TARGET_REGISTRY.yaml`
- `STF_BASIS_GRAM_RECEIPT.json`
- `COMMON_RAW_OBSERVATION_CONTRACT.yaml`
- `HTT_PHYSICAL_TARGET_MAP.yaml`
- target/full-latent posterior-loss estimates, uncertainty and calibration
- source manifest, transfer/covariance/selection versions
- exact branch/head, commands, exit codes, test/replay receipts and one next action
