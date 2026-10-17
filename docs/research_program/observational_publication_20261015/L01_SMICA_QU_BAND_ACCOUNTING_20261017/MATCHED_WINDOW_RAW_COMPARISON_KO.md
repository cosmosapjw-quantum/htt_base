# L01: 알려진 저차 입력 검증에서 실제 raw-moment matched fit으로

작성일 2026-10-18 Asia/Seoul. Parent HEAD `439742aee61f3643b7c47a2dea4bca7577271198`, 기존 Draft PR #559. 이번 선택 범위: R8 사용자 known-source 결과 판정과 C7의 다음 유한 관측 비교, 이를 위한 구현/국소 검증. 전체 10단계 재시작이나 cosmic B 검출, canonical node 완료 승격을 의미하지 않는다.

## 1. 입력 근거와 닫힌 검사

사용자 stdout의 `PASS_FINITE_LOW_SOURCE_WINDOW_RESPONSE`를 근거로 한다. 이 세션에서 native PMASK를 실행한 결과가 아니다.

| 영역 | original spatial pixels | W=0 spatial pixels | M W retained pixels | E-to-B unit gain |
|---|---:|---:|---:|---:|
| common | 39,248,896 | 2,127,975 | 37,120,921 | 0.20866730120935176 |
| three_way_intersection | 37,943,296 | 991,527 | 36,951,769 | 0.06506690981363904 |

두 영역 차이의 E-to-B gain은 0.1513398412986336, all gain은 0.2927791006910198이다. 이것은 단위 저차 입력의 연산자 응답이지 실제 B 오염 분율이 아니다. 제외 비율은 original fit 기준 common 5.4217448562%, inner 2.6131809951%다. Matched support의 공간 픽셀 수 차이는 169,152다. 면적이 비슷해도 연산자/계수 응답이 같다는 결론은 나오지 않는다.

Matched Gram의 보고된 condition은 각각 4.913539510790986, 4.993878787744807이며 저차 identity max abs는 6.66e-16, 5.55e-16이다. 따라서 정확한 ell2..5 모형의 식별성 검사는 닫고 실제 raw moment에 그 별도 추정량을 적용하는 비교로 진행한다. 원본 FITS, 이전 NSIDE64/native 추정량과 보고서는 그대로 보존한다.

원래 L32/64/128 기록은 유한 cutoff 변화 및 격자 민감도에 관한 이력이다. 이번 입력은 그 기록을 대체하지 않으며, 이전 native residual 16.18% all / 17.17% B를 보정 완료로 바꾸지 않는다.

## 2. 목적함수로 보는 기존 추정량과 새 control의 차이

A는 동일한 real spin-2 ell2..5 64열 기저, x는 delivered Q/U, W는 binary native source window, M_i는 Q/U에 동일한 binary fit 영역이다. W와 M_i는 대각행렬로 commute하며 M_t<=M_c다. Pixel solid angle omega는 공통이다. G_i=omega A^T M_i A, C_i=omega A^T M_i(I-W)A, S_i=G_i-C_i라 하자.

기존 zero-filled 목적함수와 matched 목적함수는 정확히

```
F_old,i(c) = omega ||M_i(Wx-Ac)||^2
F_match,i(c) = omega ||M_i W(x-Ac)||^2
F_old,i(c) = F_match,i(c) + c^T C_i c.
```

마지막 식은 M_i W와 M_i(I-W)의 지원 영역이 서로소인 것에서 나온다. 즉 기존 fit은 W=0인 픽셀에서 예측 Ac도 0에 가깝도록 하는 양의 준정부호 이차 penalty를 포함한다. 원래 추정량이 windowed-map 통계량이라면 이는 정의에 따른 계산이지 구현 오류가 아니다. Window 이전의 유한 저차 모형을 fit하는 경우에는 M_i W를 사용한 별도 추정량과 비교할 수 있다. Penalty 제거가 실제 cosmic B 오차를 줄인다는 보장은 없다.

기존 native 보고서의 raw RHS는 이미

```
b_i = omega A^T M_i W x
```

이므로 픽셀을 다시 읽지 않고

```
y_i = solve(G_i,b_i)
beta_i = solve(S_i,b_i)
R_i = solve(G_i,S_i)
y_i = R_i beta_i
```

를 계산한다. 실제로 M_i W 영역의 selected-pixel least squares와 beta_i가 일치함을 독립 np.linalg.lstsq로 검증했다. S_i가 수치적으로 식별되지 않으면 중단하고, pinv나 정규화 강도를 자동 조절하여 통과시키지 않는다.

원래 같은 native 보고서의 재합성 RHS는 omega A^T M_i f_L이다. f_L은 W 밖에서도 비영이므로 이것을 그대로 S_i^-1에 넣으면 M_i W fit과 다르다. 이번 코드는 **raw column 0만** 사용한다. 재합성/잔차 열이 바뀌고 raw 열이 같을 때 결과가 같다는 회귀 검사가 있다.

## 3. 두 영역 차이의 대칭적 분해

DeltaR=R_t-R_c, Rmean=(R_t+R_c)/2, delta_beta=beta_t-beta_c, beta_mean=(beta_t+beta_c)/2라 두면

```
d_old = y_t-y_c = DeltaR beta_mean + Rmean delta_beta.
```

첫 항은 두 응답의 차이에 의한 algebraic term, 두 번째는 matched fit의 차이를 old 좌표로 옮긴 항이다. 어느 한 영역을 기준으로 삼지 않는 대칭적 표현이다. 양쪽 모두 관측자료에 의존하는 beta로 계산하므로 독립적인 물리적 오염 원인 분해가 아니다. 고차 신호, 전경, 잡음이 이 beta에 들어 있다.

각 all/E/B selector에서 두 항을 u,v라 두면

```
||d_old||^2 = ||u||^2 + ||v||^2 + 2 u^T v.
```

코드는 signed interference를 보존하고, fitted beta와 old y, 원래 차이, matched 차이, 두 분해 항을 전부 저장한다. 에너지는 K_CMB^2 단위의 low real-coefficient norm이며 pseudo-C_ell 대역합이 아니다. matched/old norm 비가 1보다 작아질 것이라고 가정하지 않는다.

Wolfram 정확 유리수 예제에서 old contrast=(-1/3,13/12), matched contrast=(-10/51,-5/34), 응답 항=(-107/816,77/68), matched-difference 항=(-55/272,-5/102)를 얻었고 합의 잔차는 정확히 (0,0)이다. 이는 제조 예제이며 실제 Planck 수치가 아니다.

목적함수 tradeoff도 원자료 norm 없이 계산할 수 있다. delta_i=y_i-beta_i라 하면

```
F_match,i(y_i)-F_match,i(beta_i) = delta_i^T S_i delta_i >= 0
F_old,i(beta_i)-F_old,i(y_i) = delta_i^T G_i delta_i >= 0.
```

Wolfram은 두 식과 목적함수 분해 모두 정확히 0 잔차를 반환했다. 코드가 저장하는 loss gap은 각 정의의 최소화 효과이지 물리적 정확도 개선량이 아니다.

## 4. 알려진 모드 복원과 실제 하늘의 구분

x=A c_*+h이면

```
beta_i = c_* + S_i^-1 omega A^T M_i W h.
```

h에는 모형 밖의 harmonic 모드와 전경/잡음/계통 잔차가 들어갈 수 있다. 정확한 저차 입력 h=0에서는 beta_i=c_*이고 두 영역 차이가 0이다. h가 full-domain 저차 기저에 직교하더라도 masked-domain에서는 기여할 수 있다. 이 반례도 회귀 검사에 포함했다. 따라서 이번 기능은 full-sky E/B purification, 물리적 high-ell tail 상계 또는 calibrated Planck null을 제공하지 않는다.

만일 old 추정량의 실제 joint covariance Sigma_y가 외부에서 주어진다면 T_i=S_i^-1 G_i와 block T=diag(T_c,T_t)에 대해 Sigma_beta=T Sigma_y T^T다. 자료가 같은 하늘이므로 교차공분산을 버리면 안 된다. 이번 입력에는 qualified covariance가 없으므로 noise covariance/p-value는 null로 유지한다. condition~5 또는 bounded response inverse만으로 noise calibration이 되지는 않는다.

## 5. 실행 검증과 코드 재사용

새 파일:
- `L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_matched_window_data.py`
- 같은 stage의 `tests/test_l01_matched_window_data.py`

기존 `l01_windowed_low_injections.response_from_holes`, `l01_native_residual_visibility`의 원본 검증/JSON reader/no-clobber writer, `l01_native_residual_projection`을 변경 없이 사용한다. 샌드박스에서 보존한 세 dependency의 전체 바이트 Git blob이 현재 원격과 일치한다. 별도 전체 clone/worktree 또는 새 사용자 checkout은 만들지 않았다.

실제 실행: Python 3.13.5, NumPy 2.3.5, pytest 9.0.2; **36 passed in 2.07s**, compileall와 standalone CLI 통과. n=2/5/16/64 직접 selected-pixel lstsq oracle, 전체 window/동일 영역, omitted-mode 반례, scale 1e-100..1e100, singular Gram·비유한 값·형상 거절, 완전한 제조 native/injection JSON 쌍의 CLI, raw-only 열 선택, 입력보존/출력 no-clobber, byte/content 분류를 검사했다. 전체 저장소 CI와 실제 사용자 JSON의 계산은 NOT_RUN이다.

알려진 입력에서 zero stub을 쓰면 결과 (0,0)이 정답 (2,-3)과 다르다는 RED를 실제 관찰한 뒤 구현했다. 목적함수 loss-gap 필드에 대한 별도 RED/green도 관찰했다. 모든 후속 회귀 항목마다 개별 RED를 수행했다고 주장하지 않는다.

초기 Wolfram 예제의 부적절한 보조 비교식은 폐기하고 올바른 selected rows의 LeastSquares oracle로 재실행했다. 최종 rational identity와 oracle만 이 문서의 근거다. SciSpace/Exa는 discovery에 사용했으며 무관한 비표준 논문이나 잘못된 검색 인덱스 날짜를 근거로 삼지 않았다.

원격 Desktop Commander read_file은 월간 quota로 차단됐고 재시도/재연결하지 않았다. Native subagent dispatch 도구가 없어 순차 실행했으며 independent-subagent review는 NOT_RUN이다. 실제 matched norm은 전달된 gain/condition scalar만으로 결정할 수 없어 아래 native JSON 후처리에 남겨둔다.

## 6. 기존 worktree에서 두 JSON만 읽는 명령

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
python -m pytest -q "$S/tests/test_l01_matched_window_data.py"
python "$S/src/l01_matched_window_data.py" \
  --native-report "$ROOT/provenance/L01_NATIVE_PIXEL_RESIDUAL_full_20261017T135250Z.json" \
  --injection-report "$ROOT/provenance/L01_LOW_SOURCE_WINDOW_RESPONSE_20261017T150345Z.json" \
  --out "$ROOT/provenance/L01_MATCHED_WINDOW_RAW_$(date -u +%Y%m%dT%H%M%SZ).json"
SH
```

Native FITS, PMASK, alm 또는 SHT를 다시 읽거나 계산하지 않는다. 출력 components에서 old/matched contrast norm, response term과 matched term의 energy, signed interference를 확인한다. 상세 fit_metadata에는 각각의 beta_i와 objective loss gap이 저장된다.

원본 보고서를 임의로 바꾸지 않는다. JSON 공백/키 순서만 바뀐 사본을 사용해야 하는 경우 `--linked-native-report ORIGINAL_JSON`으로 injection이 실제 참조한 바이트를 제공하면 현재 사본과 canonical JSON 내용 동일성을 확인한다. 링크 SHA가 다르고 원본이 없으면 `BYTE_MISMATCH__SEMANTICS_UNRESOLVED`, canonical 내용까지 다르면 `CANONICAL_CONTENT_MISMATCH`로 분리한다. 숫자·단위·source window가 변한 보고서를 재포장 차이로 승인하지 않는다. Immutable FITS의 SHA lock은 그대로다.

## 7. 단계별 게시와 6개 논문 DAG

R8 known-source 결과 판정, C7 raw-data 비교 구현, 국소 검증 및 인계의 매 단계에서 14/42를 유지한다. Source commit `c33cc444c9defabaf958e12c82f1f4ec34ae987b`, test commit `6c7bd1fcaf6ea3d4715aad773144b90cabf5b1a3`. 새 소스 Git blob `2b7453997162e30edeb6803ca0d4d274ec2c8bd3`, tests `6b966d03d14b8d420e267e7a91c8759e7fe74496`는 테스트한 바이트와 일치한다.

P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7. READY L01/S02, 여섯 논문 NOT_READY_TO_SUBMIT. 원래 NSIDE64/native estimator, observed residual과 canonical backlog/main을 교체하지 않는다. 실제 matched 결과가 작아져도 이것만으로 L01 전체나 L03 physical null을 완료 처리하지 않는다.

Primary context: Planck 2018 IV https://arxiv.org/abs/1807.06208 ; original full text https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html ; matrix-based cut-sky purification comparator https://arxiv.org/abs/1603.05976 . 이 문서의 선형 항등식은 직접 유도와 제조 검산이며 문헌적 신규성 주장이나 물리적 no-go 정리가 아니다.
