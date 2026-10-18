# H02 실제 source geometry의 calibration-envelope 실행

2026-10-18. 수행: R5/R7 + C5/C6의 bounded 후속 계산. Canonical DAG·main·기존 source를 바꾸지 않았다.

## 결과

방법별 실제 관측 중심값은 확보되지 않았다. 보존된 H02 JSON에는 35,970개 선택 그룹으로 계산한 각 방법 Gram 행렬의 최소·최대 고유값과 pooled conditional SE가 있지만, 방법별 계수 b_m, centered XᵀWy 및 전체 G_m은 없다. 따라서 데이터가 요구하는 최소 calibration δ, 실제 공통 계수 구간 및 anisotropy detection은 **계산하지 않았다**.

대신 이 실제 source geometry와 명시된 uncertainty 가정 아래, 사전 지정한 Euclidean-unit coefficient contrast c에 대한 동시 오차 반경을 계산했다. 4개 방법에 대해 Gaussian marginal을 가정한 95% familywise bound의 임계값은 z_(1−.05/8)=2.4977054744이다. 방법 사이 독립성은 요구하지 않는다.

| 방법 | 실제 선택 그룹 수 | q_m (δ=0) | δ=.01에서 q_m+δ | δ=.02에서 q_m+δ | δ=.05에서 q_m+δ |
|---|---:|---:|---:|---:|---:|
| FP | 26,916 | .041383 | .051383 | .061383 | .091383 |
| TF | 7,614 | .036338 | .046338 | .056338 | .086338 |
| SN | 700 | .041242 | .051242 | .061242 | .091242 |
| OTHER | 740 | .056050 | .066050 | .076050 | .106050 |

단위는 raw shape8 coefficient contrast의 mag이다. δ는 |cᵀgamma_m|≤δ인 **contrast calibration envelope**이며, 모든 sky direction에서의 brightness bound나 관측된 calibration 수치가 아니다. 방향·기저에 무관한 physical amplitude로 해석할 수 없다.

TF가 이 spectral worst-direction upper bound에서는 가장 작다. 이는 실제 특정 contrast의 오차 순위가 아니다. 다른 방법의 실제 방향별 variance는 더 작을 수 있으나, eigenvector가 없으므로 이를 확인할 수 없다. 실제 interval centers가 들어오면 교집합은 더 좁거나 공집합일 수 있다.

Gaussian marginal을 가정하지 않고 유한 marginal variance bound만 유지하면 Chebyshev+union bound의 q_m은 FP .148192, TF .130128, SN .147689, OTHER .200713 mag이다. 이 값에도 실제 CF4 marginal variance가 G_m^-1로 보정됐다는 근거는 별도로 필요하다.

## 수학적 연결

H02 raw basis:

    X(n)=(nx,ny,nz,nx²−nz²,ny²−nz²,2nxny,2nxnz,2nynz).

방법별 intercept를 제거한 working model을

    bvec_m = beta + gamma_m + epsilonvec_m,
    E[epsilonvec_m | fixed selected design] = 0,
    Cov(epsilonvec_m | fixed selected design) = G_m^-1

로 둔다. 두 noise law 모두 위 zero-mean 가정이 필요하다. 알려진 bounded mean bias는 calibration delta에 흡수할 수 있지만, 임의의 미지 bias는 covariance만으로 제한할 수 없다. Variance-only는 centered finite-variance를 뜻한다.

이 marginal covariance는 실제 source의 e_DMzp를 diagonal Gaussian fitting weight로 사용한 **working-law assumption**이다. 원 catalogue의 selection·shared calibration·peculiar field covariance가 검증되었다는 뜻은 아니다.

사전 지정한 ||c||₂=1에서 theta=cᵀbeta, b_m=cᵀbvec_m이고

    1/lambda_max(G_m) <= Var(cᵀepsilonvec_m) <= 1/lambda_min(G_m).

Gaussian marginal이면 q_m=z_(1−alpha/(2M))/sqrt(lambda_min(G_m)). 방법별 tail이 alpha/M 이하이므로 arbitrary cross-method dependence에도 P(모든 m에서 |epsilon_m|≤q_m)≥1−alpha. Variance-only 방식은 q_m=sqrt(M/alpha)/sqrt(lambda_min(G_m))이며 동일한 union bound가 성립한다.

미리 지정한 K개 contrasts를 함께 보고하면 comparisons=M K를 사용한다. 결과 JSON/CSV는 K=1과 K=8을 모두 담는다. K=8은 고정된 8개 contrast family이며, 연속된 모든 방향이나 관측 후 선택한 축에 대한 동시 보장이 아니다.

|gamma_m|≤δ와 오차 event가 성립하면

    theta ∈ ∩_m [b_m−δ−q_m, b_m+δ+q_m].

그 scalar box model에서 교집합은 sharp하다. 각 가능한 theta에 대해 gamma_m=clip(b_m−theta,−δ,δ), epsilon_m=b_m−theta−gamma_m가 witness를 준다. 실제 calibration/error 사이 추가 coupling이 있다면 box intersection은 outer set이다. 공집합은 common estimand·bound·noise law의 결합을 반박하며 FLRW를 단독 반박하지 않는다.

이번 실행에는 b_m이 없으므로 q_m+δ frontier만 저장한다. 관측 중심을 0이나 toy 수치로 채우지 않았다. 앞 문서의 제조 witness는 endpoint API unit test로만 남겼다.

## 실행과 검증

환경: /opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3, NumPy2.3.5, Matplotlib3.10.8.

이 디렉터리에서:

```bash
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 calibration_frontier.py
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest -v test_calibration_frontier.py
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 plot_calibration_frontier.py
```

최종 8 tests PASS, 생성 runner exit0, 64개 scenario rows. Tests는 rotated SPD Gram의 spectral inequality와 saturating eigendirection, Gaussian/Chebyshev familywise budgets, scalar interval witness/empty case, source corruption과 nonfinite/domain failures를 확인한다. 최초 test는 scenario row-count 기대값 128을 잘못 적어 1건 실패했다; 실제 2 laws×2 contrast families×4 methods×4 δ=64로 고친 뒤 통과했다. 실패를 계산값 변경이나 tolerance 완화로 숨기지 않았다.

부모의 독립 검토에서 --source가 숫자 bytes를 검증하지 않고 SOURCE_BLOB을 표시하는 결함이 발견됐다. 최종 reader는 raw bytes의 실제 Git blob SHA-1을 계산해 a2116a1f281300b488b5661ac5d28678801734d3와 일치해야만 실행한다. 원 NPZ label을 그대로 둔 채 eigenvalue를 바꾼 JSON을 reject하는 regression을 추가했다. Dictionary-only compute는 identity validation 미수행으로 표시하고, pinned file runner만 PINNED_GIT_BLOB_MATCH를 기록한다.

Plot PNG를 직접 확인했다. source geometry를 사용한 uncertainty radius와 실제 관측 interval을 명시적으로 구별한다. PNG/PDF는 같은 plotting code 출력이다.

## 출처와 정확한 다음 입력

GitHub commit 967ef7c8f0b132ecaaba343045d333d4ebf299c1의
docs/research_program/observational_publication_20261015/H02_L03_20261017/results/H02_ACTUAL_SELECTED_SOURCE_FISHER.json.

Original selected-source NPZ SHA256: 86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c. 이번 실행은 그 NPZ를 재구성하거나 다시 fit하지 않고, pinned committed JSON의 보존된 spectra를 사용한다.

실제 중심 있는 intersection/R_min 계산에 필요한 최소 추가자료는 같은 H02 shape8/window/intercept estimator의 방법별 bvec_m 또는 G_m과 X_mᵀW_m y_m이다. Exact contrast variance에는 full G_m 또는 cᵀG_m^-1c가 필요하다. 관측-level confidence claim에는 selected law와 marginal error/calibration bounds의 validation이 필요하다. 이 입력들이 없는 상태는 source-ready coding과 실제 inference 사이의 정확한 경계로 남긴다.

H02 physical gate와 여섯 논문의 submission state는 바꾸지 않는다.

