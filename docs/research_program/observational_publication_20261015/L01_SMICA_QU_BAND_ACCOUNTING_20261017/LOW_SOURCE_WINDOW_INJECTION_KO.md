# L01: 잔차 가시성 판정 종료와 알려진 저차 E/B 입력 검증

2026-10-17 Asia/Seoul. Parent `82cbb6d844f7e8faca181d39493449c8fd92dc2b`, 기존 Draft PR #559. 이번 범위는 사용자 native visibility 결과의 R8 판정과 L01의 다음 미완료 paired known-source injection 계산(C7 및 그 구현 지원)이다. 새로운 전체 10단계 루프나 물리적 null 승인을 의미하지 않는다.

## 1. 이번 사용자 실행으로 닫힌 질문

사용자가 `PASS_NATIVE_RESIDUAL_VISIBILITY_ACCOUNTING`을 보고했다. 실제 입력은 `/mnt/extdrive/workdir/htt_open_data/provenance/L01_NATIVE_RESIDUAL_VISIBILITY_20261017T143222Z.json`에 저장되어 있다. 이 문서의 native 수치는 사용자 stdout이며 이 샌드박스에서 해당 파일을 직접 실행한 결과가 아니다.

| 공간 | 유지 수치 rank | 유지 입력 에너지/전체 잔차 에너지 | 미해결 목표 norm 비 | 입력 norm 희석 인자 | 특이방향 인자 |
|---|---:|---:|---:|---:|---:|
| all | 64 | 4.7646760056311307e-7 | 1.1204870087950256e-15 | 1448.71618763943 | 5.227022311849014 |
| E | 32 | 1.8002411329587148e-7 | 9.060478683427182e-16 | 2356.8647431949535 | 4.023988146728137 |
| B | 32 | 2.426375799450568e-7 | 1.4053120839115612e-15 | 2030.116528789427 | 3.730509175742055 |

전체의 유지 에너지 비는 0.0000476467600563%이고 유지 norm 비는 0.0006902663258215다. 1448.71618763943 * 5.227022311849014 = 7572.471836328144이므로 전역 잔차 상계가 느슨했던 이유가 수치적으로 분해됐다. 작은 특이방향 효과도 있지만, 주된 인자는 이 연산자가 감지하는 행공간 성분과 전체 입력 잔차 norm의 차이다. 수치 rank 선택 아래의 결과이지 형식적 rank 증명이나 잡음 에너지 분율은 아니다. E와 B의 입력 투영 부분공간은 겹칠 수 있어 개별 에너지를 단순 합하지 않는다.

기존 실제 비교 잔차(all 16.1764%, B 17.1684%)는 이 설명으로 감소하지 않는다. 반복적인 상계/정규화 진단을 종료하고, DAG L01이 요구하는 알려진 입력에 대한 응답 검증으로 넘어간다. L128 결과를 새로 만들거나 cutoff를 자동 확대하지 않는다.

## 2. 현재 fit과 source window는 서로 다른 객체

A를 동일 native NSIDE2048 픽셀 중심에서 평가한 실수 spin-2 E/B ell2..5 기저(64열)라 하자. 각 ell에서 E(m0,cos1,sin1,...), B(...) 순서다. 데이터 convention은 COSMO, Galactic이며 계수 단위는 K_CMB다. Q/U 행에는 동일한 이진 마스크가 작용한다.

- W: 실제 지도에 먼저 곱하는 native source window.
- M_c, M_t: 원래 NSIDE64 셀의 합집합을 NESTED 자식으로 확장한 fit 영역. M_t<=M_c.
- omega=4pi/Npix: 동일 픽셀 solid angle.
- G_i=omega A^T M_i A: 기존 native 보고서에 저장된 Gram.

이전 데이터 통계량은 `G_i^-1 omega A^T M_i W x`로 명시되어 있다. W로 0이 된 픽셀도 M_i 안이면 기존 Gram에는 들어가므로, 이것을 창이 없는 하늘 계수의 불편 추정량이라고 자동 해석하면 안 된다. 이전 계산은 선언한 processed-map 통계량으로 보존한다.

## 3. 직접 구성한 저차 입력과 응답식

관측된 계수를 추정해서 넣는 것이 아니라, 입력을 정확히 x_in=A c로 정의한다. c_B=0인 순수 E를 포함하는 64개의 단위 E/B 입력을 사용한다. 이는 알려진 delivered-map 저차 장이며 실제 하늘 전체가 ell<=5라는 가정이 아니다.

```
C_i = omega A^T M_i (I-W) A
R_i = G_i^-1 omega A^T M_i W A = I-G_i^-1 C_i
Delta R = R_t-R_c = G_c^-1 C_c-G_t^-1 C_t.
```

유도는 W=I-(I-W)를 대입하면 된다. 결과적으로 기존 두 마스크 차이는 입력 low vector c에 대해 Delta R c다. B selector와 E input selector로 Delta R_BE를 만들면 `||Delta B|| <= ||Delta R_BE|| ||c_E||`이고 최대 특이벡터에서 달성된다. gain은 무차원이다. 코드의 1 K_CMB unit coefficient는 선형 전달을 표시하는 단위 probe이지 우주론적 진폭 가정이 아니다.

특히 W가 M_c 영역 전체에서 1이면 C_c=C_t=0이며 각 R_i=I, Delta R=0이다. 부분 하늘에서도 정확한 유한 저차 model과 invertible design 아래에는 이 항등식이 성립한다. 임의의 고차 하늘까지 포함한 pure E/B 복원을 주장하는 것이 아니다.

## 4. 비교 control: window를 forward model에 반영

같은 이진 W를 모델 WA에 반영하거나 fit 영역을 M_i W로 제한하면

```
Gbar_i = G_i-C_i
Rbar_i = Gbar_i^-1 omega A^T M_i W A = I
```

가 성립한다. 단 Gbar_i가 가역이고 수치적으로 사용할 수 있어야 한다. 여기서 필요한 전제는 정확히 ell2..5 모형이라는 것이며, 고차 신호/전경/잡음이 들어 있는 실제 지도에 바로 적용해 unbiased cosmic coefficients라고 부를 수 없다.

이 비교 control은 새로운 추정량이다. 이번 코드에서는 원래 native/NSIDE64 결과를 덮어쓰거나 대체하지 않고 identity 및 condition만 저장한다. 실제 관측자료에 matched estimator를 적용하거나 이를 correction으로 차감하지 않는다.

Wolfram 정확 4x2 제조 예제에서 original R_c={{2/3,1/3},{1/3,2/3}}, R_t=I, Delta R={{1/3,-1/3},{-1/3,1/3}}를 얻었고 두 matched responses는 정확히 I였다. 이는 선형대수 예제이며 2성분을 실제 E/B 관측으로 해석하지 않는다. 아래 구면 검사는 실제 spin-2 기저를 별도로 사용한다.

## 5. 계산량과 기존 코드 재사용

새 `l01_windowed_low_injections.py`는 이전 native 보고서의 G_i를 재사용한다. 기존 `l01_native_residual_visibility`가 그 보고서의 코드/source/solver 항등식을 읽어 검증하고, 기존 producer의 `read_windows`로 3개 PMASK 원본과 native window를 확인한다. 원본 observed I/Q/U FITS와 saved alm은 읽지 않는다.

새로 필요한 C_i는 M_c AND NOT W 픽셀에서만 누적한다. 전체 Boolean window를 순회하지만 비싼 구면 기저 평가는 이 제외 픽셀 부분집합에만 수행한다. Q/U basis는 같은 `spin2_finite.block_design`을 사용하고, native NESTED 픽셀 중심은 healpy로 평가한다. 새 full 50M-pixel design이나 64개 native 합성지도를 만들지 않는다. C_i와 결과 행렬은 64x64다.

항등행렬 두 개의 작은 차이를 빼는 대신 `solve(Gc,Cc)-solve(Gt,Ct)`로 Delta R을 계산한다. 기존 condition 상한 1e8을 유지하고, nested/window moment의 Loewner ordering과 scalar-Q/U 복소구조를 검산한다. native driver의 마지막에는 기존 all-m healpy/Wigner 비교를 NSIDE8에서 수행한다. 이 작은 convention 합성은 native NSIDE2048 SHT가 아니다.

## 6. 실제 실행한 검사와 미실행 경계

샌드박스 Python 3.13.5/NumPy 2.3.5에서 새 테스트 **26/26 PASS**, compileall PASS, 별도 subprocess `--help` PASS. 구현 전 비영 known-source Delta R을 0으로 반환한 행동 테스트가 실패(exit 1)했고, 구현 후 같은 테스트가 통과했다. 나머지 회귀 항목 모두에 개별 RED가 있었다고 주장하지 않는다.

기존 기저의 정확한 Git blob `2a168e0592d3245d3bf367d515a0d11ea5637341`과 일치하는 바이트를 사용했다. 300점 제조 구면 grid의 64개 unit E/B 입력에 대해, sparse-complement 공식과 직접 masked-data `numpy.linalg.lstsq`를 대조했다. 모든 입력에서 맞았고 matched support 직접 least-squares는 입력 identity를 복원했다. 제조 geometry에서 Delta E-to-B gain=1.0814993262926094, Delta 전체 gain=1.8695962954470167이다. 이는 Planck 마스크 측정값이 아니다.

테스트 중 inner Gram condition~209에서 J-commutator의 절대 4e-15 제한이 실패했다. 생산 코드나 물리 gate를 넓히지 않고, `[G^-1 C,J]=G^-1([C,J]-[G,J]G^-1 C)`로 입력 commutator와 condition을 전파하는 정당한 산술 검사로 교정했다. 실제 잔차는 5.93407800946113e-14이며 response normal identity residual은 7.599491770609696e-16이다.

실제 Planck native C_i, 전체 native driver/독립 healpy convention 실행, 전체 저장소 CI는 이 세션에서 NOT_RUN이다. 샌드박스에는 healpy가 없고 외부 DNS가 차단되어 설치하지 못했다. 이미 검증된 수학 기저의 의미를 바꾸는 대체 모듈을 쓰지 않았다. Native subagent 도구는 없으므로 NOT_RUN이다.

## 7. 현재 worktree에서 실행

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
python -m pytest -q "$S/tests/test_l01_windowed_low_injections.py"
python "$S/src/l01_windowed_low_injections.py" \
  --root "$ROOT" \
  --native-report "$ROOT/provenance/L01_NATIVE_PIXEL_RESIDUAL_full_20261017T135250Z.json" \
  --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
  --chunk-pixels 8192 \
  --out "$ROOT/provenance/L01_LOW_SOURCE_WINDOW_RESPONSE_$(date -u +%Y%m%dT%H%M%SZ).json"
SH
```

新しいデータのダウンロードは不要。The source/report hashes and old estimator are preserved; no automatic source-lock repair is performed. In interpreting output, `gains.two_mask_difference.E_to_B_gain` is a measured conditional transfer coefficient for injected ell2..5 E inputs, not the E-origin fraction of the measured B residual. `matched_controls` is a finite low-model oracle, not a noise-debiased Planck result.

## 8. 단계별 게시와 DAG

결과 판정, source commit `6e449ab904debf673ce4a68091450a58fcf38ec3`, test commit `601f783d164c980b28fe167d3e664f1067bba439`, 인계의 각 단계에서 공식 DAG는 14/42다. P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7. READY L01/S02. L01의 source support/paired injections 중 명시된 저차 부분을 다루지만 selected T/E/B 전체 response, 고차 remainder 및 L03 matched null은 아직 완료되지 않았다. 여섯 논문은 NOT_READY_TO_SUBMIT이다.

## 원전 확인

- HEALPix polarization convention: https://healpix.sourceforge.io/doc/html/intro_HEALPix_conventions.htm
- Planck 2018 IV, 전달 편광 제품과 잡음/계통오차 한계: https://arxiv.org/abs/1807.06208
- Kim, masked E/B reconstruction discussion: https://www.aanda.org/articles/aa/full_html/2011/07/aa16733-11/aa16733-11.html
- Bunn, E/B mixing and ambiguous components: https://arxiv.org/abs/0811.0111

SciSpace는 원전 탐색에 사용했으며 중복 인덱스의 잘못된 날짜를 출판일로 사용하지 않았다. Exa와 공식 문서로 convention과 마스크 해석을 대조했다. 위 저차 response 항등식은 직접 유도/검산이며 문헌적 신규성이나 강한 no-go 정리 주장이 아니다.
