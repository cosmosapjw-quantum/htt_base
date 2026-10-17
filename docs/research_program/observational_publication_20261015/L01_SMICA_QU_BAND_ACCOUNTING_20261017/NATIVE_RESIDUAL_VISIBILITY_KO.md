# L01 native residual: 측정된 목표량 오차와 느슨한 전역 상계의 분리

2026-10-17 Asia/Seoul. Parent `93cb3e80fa31f28dd197fc98aa183c6d8270ba2a`, existing Draft PR #559. 이번 선택 범위는 R8 실제 native 결과 판정과 C8 저장된 작은 행렬의 잔차 분해다. 새로운 native SHT, L256 sweep, 전체 연구 루프나 독립 subagent 검토를 수행하지 않는다.

## 1. 실제 결과와 닫힌 실행 단위

사용자 stdout에 따르면 native NSIDE2048에서 full의 L128 재합성과 실제 windowed Q/U를 비교한 실행이 `PASS_NATIVE_PIXEL_RESIDUAL_ACCOUNTING`으로 끝났다. Closure residual은 `1.0993426895676539e-15`다. 직접 자료의 두 마스크 추정량 차이를 d, 재합성 비교량을 s라 하면 다음 값이 보고됐다. 이것은 전체 B sky power나 cosmic B의 오차율이 아니다.

| 성분 | norm(d) [K_CMB] | norm(s) [K_CMB] | norm(d-s) [K_CMB] | 상대 잔차 |
|---|---:|---:|---:|---:|
| all | 8.221782224682224e-8 | 7.900694579457522e-8 | 1.329984597427508e-8 | 0.16176353995789672 |
| E | 5.5635571016801396e-8 | 5.319923000534819e-8 | 8.299104732795775e-9 | 0.1491690402582464 |
| B | 6.053472997085645e-8 | 5.841180882856657e-8 | 1.0392822695183816e-8 | 0.17168363846980547 |

이는 이제 같은 native 격자의 두 유한 계산 사이에서 측정한 잔차다. 이전 L32/L64/L128 cutoff 증분과 분모가 같지 않다. Native 비교량이 cosmic truth이거나 원래 NSIDE64 추정량을 대체한다고 해석하지 않는다.

상계/측정 잔차 비는 all 7572.4718, E 9483.9958, B 7573.3683이다. 모든 성분의 bound/gain에서 같은 common-region map norm `1.1986647545415914e-4 K_CMB`가 복원된다. 이는 sqrt(pixel solid angle)로 가중한 지도 L2 norm이지 픽셀당 RMS나 측정된 순수 잡음 진폭이 아니다.

세 norm만으로 cos(theta)=(norm(d)^2+norm(s)^2-norm(d-s)^2)/(2 norm(d) norm(s))를 계산할 수 있다. 계수공간의 각도는 all 9.18498789도, E 8.36258366도, B 9.81475863도이며 재합성/직접 에너지 비는 각각 0.9234185795, 0.9143355238, 0.9310909199다. 각도는 하늘 회전각/편광각이 아니다.

**판정:** native 비교 실행 단위는 사용자 근거로 닫는다. L128의 목표 잔차는 측정되어 있으며 약 16~17%로 남는다. 전역 잔차 norm 상계가 매우 크다는 이유로 픽셀/SHT 계산을 반복하거나 이를 물리 오차막대로 사용하지 않는다. 원인은 아직 잡음/전경/마스크/처리효과 중 하나로 귀속되지 않았다.

## 2. 유한 연산자가 감지하는 입력 성분

기존 이진 중첩 영역 M_t<=M_c, 고정 real low-ell basis A, pixel solid angle omega를 유지한다.

```
G_i = omega A^T M_i A
P_i = G_i^-1 sqrt(omega) A^T M_i
D = P_t-P_c
H = D D^T = G_t^-1-G_c^-1
z = sqrt(omega) M_c (f-f_L)
e = d_direct-d_reconstructed = D z.
```

G_c,G_t는 가역이고 유한 선형대수에서 H는 양의 준정부호다. H^+를 Moore-Penrose pseudoinverse라 하면

```
z_visible = D^T H^+ e
Pi_visible = D^T H^+ D
||z_visible||^2 = e^T H^+ e
D(z-z_visible)=0
||z||^2 = ||z_visible||^2 + ||z-z_visible||^2.
```

근거: D=U Sigma V^T의 얇은 SVD를 사용하면 H=U Sigma^2 U^T이고 Pi_visible=V V^T다. 따라서 Pi_visible은 range(D^T)로의 직교 projector이고 나머지는 ker(D)에 속한다. 같은 e를 만드는 입력 중 z_visible이 최소 norm이다. 지도 크기의 D를 저장하지 않고 기존 64x64 H와 e로 에너지를 계산할 수 있다. 원전의 최소 norm 성질을 이 연산자에 적용한 것이며 새로운 정리라는 주장은 아니다.

전역 상계가 느슨한 정도는, nonzero visible 성분에 대해

```
(kappa ||z||)/||e|| = (||z||/||z_visible||) * (kappa/kappa_eff)
kappa=sqrt(lambda_max(H)), kappa_eff=||e||/||z_visible||.
```

첫 인자는 추정량이 보지 못하는 입력 성분에 의한 norm 증가, 두 번째는 최대 특이값 방향과 실제 잔차 방향의 차이다. **큰 상계 간극만으로 첫 인자가 지배한다고 결론 내릴 수 없다.**

Wolfram exact example: D=diag(1,2) 뒤에 영열을 붙인 2x3 행렬, z=(1,1,10000). 실제 목표 오차는 sqrt(5), 전체 입력 에너지는 100000002, 감지되는 입력 에너지는 정확히 2이며 projector 멱등성과 Pythagoras 항등식이 성립했다. 반대로 D=diag(1,0.001), z=(0,1)은 kernel 에너지 없이도 상계/실제=1000이다. 두 경우 모두 회귀 검사에 포함했다. Planck에서 어느 경우가 지배하는지는 stdout norm만으로 알 수 없으므로 저장된 H,e에서 계산한다.

## 3. 숫자로 역행렬을 만드는 범위

새 코드가 유지하는 H 고유값 기준은 `max(4*inherited_psd_roundoff_allowance, 256*n*eps*lambda_max)`다. 상속된 allowance는 기존 native comparator의 inverse-Gram 계산 스케일에서 온 부동소수점 진단값이며 엄밀한 구간 인증이 아니다.

유지된 고유쌍 (lambda_j,u_j)에 대해서만 sum_j (u_j^T e)^2/lambda_j를 계산한다. 작은 양의 고유값을 버린 경우 남은 입력 에너지를 전부 물리적 영공간으로 부르지 않는다. `unresolved_target_fraction`과 retained numeric rank를 같이 출력한다. 코드의 두 gap factor 곱은 **retained target**에 대한 식이며, 원래 e와의 차이도 보존한다. 작은 고유값을 지워 유의성이나 잔차를 개선하는 기능은 없다.

E와 B selector R_X를 각각 적용할 때 입력 projector의 범위는 서로 겹칠 수 있다. 그러므로 E-visible energy와 B-visible energy를 더해 all-visible energy로 쓰지 않는다. 이 연산자 기준의 입력 분해는 Bunn/Lewis의 pure E/pure B/ambiguous sky decomposition과도 다른 객체다.

## 4. 삭제 영역에 대한 추가 정확한 관계

M_s=M_c-M_t, G_s=G_c-G_t, b_s=b_c-b_t라 두면 common fit 잔차의 removed-region moment는

```
h_s = b_s-G_s*y_c = omega A^T M_s (f-A*y_c)
G_t*(y_t-y_c) = -h_s.
```

G_c*y_c=b_c와 G_t*y_t=b_t를 빼면 바로 얻는다. 코드에서는 실제 저장된 raw/reconstructed/residual 세 RHS에 이를 적용하고 각 normal equation도 다시 확인한다. 추가 지도를 읽거나 removed-region의 새 물리적 통계를 측정한 것은 아니다. Wolfram 유리수 예제의 residual은 정확히 (0,0), 독립 삭제-row 행렬 계산과의 Python 비교도 통과했다.

## 5. 실행 근거와 코드 재사용

Source `src/l01_native_residual_visibility.py`, tests `tests/test_l01_native_residual_visibility.py`, 모두 기존 `L01_R8_C8_TWO_MASK_STABILITY_20261017` 아래에 추가했다. 기존 `l01_native_residual_projection.py`의 `nested_dual_gram`, `compare_states`, array checks를 직접 재사용한다. Native 파일은 수정하지 않았다.

새 source/test 및 그대로 복원한 native dependency로 **41 passed in 2.66s**, compileall와 standalone subprocess --help를 확인했다. Python3.13.5/NumPy2.3.5/pytest9.0.2. Native dependency 전체 Git blob은 `14621d017c2c221701699873cece8659cbdd5b21`로 원격과 동일하다. Source Git blob `c64fa5bf7491ebe0ced17e85673da507c0921983`, test blob `a2fbaa8e032fd89f9972c1d7148374ce9b775514`도 테스트 바이트와 원격이 일치한다.

시험 범위: 직접 rectangular D에 대한 pseudoinverse oracle, singular/degenerate 행렬, input scale 1e-100..1e100, 작은 고유값, 중복 E/B 입력 공간, 두 가지 느슨한 상계 기작, 삭제-row identity, 64x64 제조 native-report CLI roundtrip, source/window/code/schema/data 변조 거절, JSON byte 변화와 semantic 동일성, no-overwrite. 최초 실제 RED는 최소 에너지 2를 기대하는 검사가 0을 반환한 불일치였다. 모든 후속 검사 각각에 RED가 있었다고 주장하지 않는다.

현재 사용자 원본 JSON의 실제 H/e를 읽는 Remote Desktop 호출은 월간 usage limit으로 실패했다. 따라서 **실제 retained energy/rank/factor 분해 값은 NOT_RUN**이며 다음 로컬 명령으로 얻는다. 전체 repo CI와 native SHT 재실행도 이번 테스트 수에 포함하지 않는다. Native subagent 도구가 없어 NOT_RUN; 독립 모델 검토를 가정하지 않는다. 예전 사용자 repo의 41-test collection과 이번 새 41-test collection은 서로 다른 검사 집합이다.

## 6. 같은 worktree에서 보고서 하나만 읽기

```bash
bash <<'SH'
set -euo pipefail
WT="$HOME/worktrees/htt_l01_r10c10_clean_20261017"
BR=research/htt-sixpaper-p2-l01-r10c10-runtime-recovery-20261017
ROOT=/mnt/extdrive/workdir/htt_open_data
P=docs/research_program/observational_publication_20261015
S="$P/L01_R8_C8_TWO_MASK_STABILITY_20261017"
state=$(git -C "$WT" status --porcelain)
if [[ -n "$state" ]]; then
  printf 'STOP: local changes preserved.\n%s\n' "$state" >&2
  exit 2
fi
git -C "$WT" fetch origin "$BR"
git -C "$WT" switch --detach "origin/$BR"
cd "$WT"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python "$P/L01_R10_C10_RUNTIME_RECOVERY_20261017/scripts/l01_checkout_guard.py"
python -m pytest -q "$S/tests/test_l01_native_residual_visibility.py"
python "$S/src/l01_native_residual_visibility.py" \
  --native-report "$ROOT/provenance/L01_NATIVE_PIXEL_RESIDUAL_full_20261017T135250Z.json" \
  --out "$ROOT/provenance/L01_NATIVE_RESIDUAL_VISIBILITY_$(date -u +%Y%m%dT%H%M%SZ).json"
SH
```

출력에서 retained rank, retained input energy fraction, unresolved output fraction, input norm dilution, spectral orientation factor를 함께 읽는다. 결과는 감도 진단이며 새로운 noise fraction, p-value, pure B 또는 유한 잔차 수정값이 아니다. Input byte digest는 provenance로 기록하되 JSON의 whitespace/key order 차이만으로 numerical identity를 부정하지 않는다. 원본 FITS의 source pin과 지원하는 native producer version은 유지한다.

## 7. 진행 및 후속 과학 경계

R8 사용자 native 결과 판정, C8 코드 commit `aedfead07f3788c944fd23ecec2e04962d2f6fc4`, tests commit `168a6ff180de41875003f0cdecdf080e9bb66d05`, 결과·유도·실행 인계의 매 단계에서 canonical publication DAG는 14/42다. P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7; READY L01/S02, 모두 NOT_READY_TO_SUBMIT. Canonical DAG, 245-card backlog와 main은 변경하지 않는다.

이 실행 단위로 native 유한 비교가 측정되었다는 사실은 닫는다. 상계를 작게 만들기 위해 더 큰 cutoff/격자 계산을 자동 요청하지 않는다. Residual visibility가 확인되어도 실제 noise/foreground/transfer 원인 구분 및 L03 source-matched null은 별도의 물리적 근거가 필요하다. Native 직접 비교량이 원래 NSIDE64 목표를 자동 대체하지 않는다.

Primary references: SciPy `pinv` documentation (https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.pinv.html), E. Darve numerical linear algebra minimum-norm/SVD notes (https://ericdarve.github.io/NLA/content/LS_using_SVD.html), Bunn et al. PRD67 023501 (https://arxiv.org/abs/astro-ph/0207338), Lewis PRD68 083509 with updated v4 (https://arxiv.org/abs/astro-ph/0305545). SciSpace used for discovery, Exa for primary numerical-source retrieval; public sources were checked separately. No new mathematical novelty claim.
