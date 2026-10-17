# L01: 잔차 가시성 판정 종료와 알려진 저차 E/B 입력 검증

2026-10-17 Asia/Seoul. Parent `82cbb6d844f7e8faca181d39493449c8fd92dc2b`, 기존 Draft PR #559. 범위는 사용자 native visibility 결과의 R8 판정과 L01의 다음 미완료 paired known-source injection 계산(C7 및 구현 지원)이다. 전체 10단계 재시작이나 물리적 null 승인이 아니다.

## 1. 닫힌 질문과 다음 과제

사용자는 `PASS_NATIVE_RESIDUAL_VISIBILITY_ACCOUNTING`을 보고했다. 경로는 `/mnt/extdrive/workdir/htt_open_data/provenance/L01_NATIVE_RESIDUAL_VISIBILITY_20261017T143222Z.json`이다. 이 수치는 사용자 stdout이며 이 샌드박스가 원본 보고서를 실행한 결과가 아니다.

| 공간 | 유지 수치 rank | 유지 입력 에너지 비 | 미해결 목표 norm 비 | 입력 norm 희석 | 특이방향 인자 |
|---|---:|---:|---:|---:|---:|
| all | 64 | 4.7646760056311307e-7 | 1.1204870087950256e-15 | 1448.71618763943 | 5.227022311849014 |
| E | 32 | 1.8002411329587148e-7 | 9.060478683427182e-16 | 2356.8647431949535 | 4.023988146728137 |
| B | 32 | 2.426375799450568e-7 | 1.4053120839115612e-15 | 2030.116528789427 | 3.730509175742055 |

전체 유지 에너지 비는 0.0000476467600563%, 유지 norm 비는 0.0006902663258215다. 1448.71618763943 * 5.227022311849014 = 7572.471836328144로 전역 상계의 간극이 분해됐다. 주된 인자는 이 연산자의 행공간 성분과 전체 잔차 norm의 차이다. 수치 rank 선택 아래의 결과이며 형식적 rank 증명이나 잡음 에너지 분율은 아니다. E/B 입력 투영 부분공간은 겹칠 수 있으므로 에너지를 단순 합하지 않는다.

실제 비교 잔차(all 16.1764%, B 17.1684%)는 감소하지 않았다. 반복적인 상계/정규화 해석을 종료하고, 알려진 저차 입력에서 기존 처리 응답을 검증한다. L128 재실행이나 cutoff 자동 확대는 하지 않는다.

## 2. 기존 통계량과 source window

A는 같은 native NSIDE2048 픽셀 중심의 실수 spin-2 E/B ell2..5 기저(64열)다. 각 ell에서 E(m0,cos1,sin1,...), B(...) 순서이며 계수 단위는 K_CMB, frame은 Galactic/COSMO다. Q/U에 동일한 이진 마스크가 작용한다.

W는 원자료에 먼저 곱하는 native source window다. M_c,M_t는 기존 NSIDE64 셀의 합집합을 NESTED 자식으로 확장한 fit 영역으로 M_t<=M_c다. omega=4pi/Npix라 하면 저장된 Gram은 G_i=omega A^T M_i A이고 기존 통계량은 `G_i^-1 omega A^T M_i W x`다.

W로 0이 된 픽셀도 M_i 안이면 기존 Gram에는 들어간다. 따라서 이 통계량을 창이 없는 하늘 계수의 불편 추정량이라고 자동 해석하지 않는다. 기존 결과는 선언된 processed-map 통계량으로 보존한다.

## 3. 알려진 저차 입력의 정확한 전달

입력을 정확히 x_in=A c로 정의한다. 관측 pseudo 계수를 참값으로 대입하지 않는다. c_B=0인 순수 E를 포함한 64개 unit E/B 입력을 다룬다. 실제 하늘 전체가 ell<=5라는 가정이 아니라 delivered-map 저차 모형의 검증이다.

```
C_i = omega A^T M_i (I-W) A
R_i = G_i^-1 omega A^T M_i W A = I-G_i^-1 C_i
Delta R = R_t-R_c = G_c^-1 C_c-G_t^-1 C_t.
```

W=I-(I-W)를 대입하면 얻는다. E 입력에서 B 출력으로 가는 블록을 Delta R_BE라 하면 `||Delta B|| <= ||Delta R_BE|| ||c_E||`이며 최대 특이벡터에서 달성된다. Gain은 무차원이고 1 K_CMB 계수 probe는 선형 단위이지 실제 우주론적 진폭 가정이 아니다.

W가 M_c 전체에서 1이면 C_c=C_t=0, 각 R_i=I, Delta R=0이다. 이 유한 모형과 가역 design의 성질을 임의의 고차 하늘에 대한 pure E/B 복원으로 확대하지 않는다.

## 4. 비교 control과 새로운 추정량의 구분

같은 이진 W를 모델 WA에 반영하거나 fit 영역을 M_i W로 제한하면

```
Gbar_i = G_i-C_i
Rbar_i = Gbar_i^-1 omega A^T M_i W A = I
```

가 된다. 단 Gbar_i가 가역이며 수치적으로 사용 가능해야 한다. 이 결론은 정확한 ell2..5 모형에만 적용된다. 실제 고차 신호, 전경, 잡음이 있는 관측지도에 곧바로 불편 복원이라고 주장하지 않는다.

Matched control은 새 추정량이다. 이번 코드에서는 condition과 identity만 저장하고 원래 native/NSIDE64 결과를 교체하거나 correction으로 차감하지 않는다.

Wolfram의 정확한 4x2 제조 예제에서 R_c={{2/3,1/3},{1/3,2/3}}, R_t=I, Delta R={{1/3,-1/3},{-1/3,1/3}}, 두 matched response는 I였다. 이는 선형대수 예제이며 실제 E/B 관측값이 아니다. 별도 구면 검사는 실제 spin-2 기저를 사용한다.

## 5. 계산 경로와 재사용

새 `l01_windowed_low_injections.py`는 기존 `l01_native_residual_visibility`로 보고서의 코드/source/solver 일관성을 확인하고 저장된 G_i를 사용한다. 기존 producer의 `read_windows`로 3개 PMASK와 native window를 재구성한다. Observed I/Q/U FITS와 saved alm은 다시 읽지 않는다.

새 C_i는 M_c AND NOT W 픽셀에서만 누적한다. Boolean window 전체를 순회하지만 비싼 구면 기저 평가는 제외 픽셀 부분집합에만 수행한다. 기존 `spin2_finite.block_design`과 native NESTED 좌표를 사용하고, 64개 native 합성지도나 전체 50M-pixel design을 만들지 않는다. 행렬은 64x64다.

작은 차이는 `solve(Gc,Cc)-solve(Gt,Ct)`로 계산해 두 near-identity 행렬의 감산을 피한다. 기존 Gram condition 상한 1e8을 유지하고 nested/window moment의 Loewner ordering 및 scalar-Q/U 복소구조를 검사한다. 마지막에는 기존 all-m healpy/Wigner 비교를 NSIDE8에서 수행한다. 이는 작은 convention 합성이며 NSIDE2048 SHT가 아니다.

## 6. 실제 검증과 남은 범위

Python 3.13.5/NumPy 2.3.5에서 신규 **26/26 테스트 PASS**, compileall 및 subprocess --help PASS다. 구현 전 비영 Delta R을 0으로 반환한 행동 테스트가 실패(exit 1)했고 구현 후 같은 테스트가 통과했다. 나머지 모든 테스트에 개별 RED가 있었다고 주장하지 않는다.

기존 기저의 정확한 Git blob `2a168e0592d3245d3bf367d515a0d11ea5637341`과 일치하는 바이트를 사용했다. 300점 제조 구면 grid의 64개 unit E/B 입력에 대해 sparse-complement 공식과 직접 masked-data `numpy.linalg.lstsq`를 대조했다. Matched support의 직접 least-squares는 입력 identity를 복원했다. 제조 geometry의 Delta E-to-B gain=1.0814993262926094, 전체 gain=1.8695962954470167이며 Planck 수치가 아니다.

Inner Gram condition~209에서 단순 절대 4e-15 commutator 제한이 실패했다. 생산 코드의 허용오차를 넓히지 않고 `[G^-1 C,J]=G^-1([C,J]-[G,J]G^-1 C)`로 입력 commutator와 condition을 전파하는 산술 검사로 교정했다. 실제 commutator 잔차 5.93407800946113e-14, normal response identity 잔차 7.599491770609696e-16을 기록한다.

실제 Planck native C_i, 전체 native driver/독립 healpy 실행, 전체 저장소 CI는 NOT_RUN이다. 샌드박스에는 healpy가 없으며 외부 DNS 접근도 실패했다. 다른 기저로 바꿔 native 검증을 통과했다고 하지 않았다. Native subagent는 도구가 없어 NOT_RUN이다.

## 7. 기존 worktree에서 실행

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

새 데이터 다운로드는 필요 없다. 기존 source/report 식별자와 추정량을 보존한다. `gains.two_mask_difference.E_to_B_gain`은 알려진 ell2..5 E 입력에 대한 조건부 전달계수이지 관측된 B 잔차 중 E가 차지하는 비율이 아니다. `matched_controls`는 유한 저차 모형의 control이며 noise-debiased Planck 결과가 아니다.

## 8. 게시와 6개 논문 DAG

결과 판정, source commit `6e449ab904debf673ce4a68091450a58fcf38ec3`, test commit `601f783d164c980b28fe167d3e664f1067bba439`, 인계의 각 단계에서 공식 DAG는 14/42다. P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7. READY L01/S02. L01의 paired injections 중 저차 부분을 다루지만 selected T/E/B 전체 response, 고차 remainder와 L03 matched null은 완료되지 않았다. 여섯 논문은 NOT_READY_TO_SUBMIT이다.

## 원전

- HEALPix polarization convention: https://healpix.sourceforge.io/doc/html/intro_HEALPix_conventions.htm
- Planck 2018 IV: https://arxiv.org/abs/1807.06208
- Kim의 masked E/B reconstruction: https://www.aanda.org/articles/aa/full_html/2011/07/aa16733-11/aa16733-11.html
- Bunn의 E/B mixing: https://arxiv.org/abs/0811.0111

SciSpace는 원전 탐색에 사용했으며 중복 인덱스 날짜를 출판일로 사용하지 않았다. Exa와 공식 문서로 convention과 masking을 대조했다. 저차 response 식은 직접 유도/검산이며 문헌적 신규성이나 강한 no-go 정리 주장이 아니다.
