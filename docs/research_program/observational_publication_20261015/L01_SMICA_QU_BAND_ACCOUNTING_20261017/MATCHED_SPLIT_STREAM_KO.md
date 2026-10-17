# L01: 실제 matched raw fit에서 동일 추정량의 HM/OE 비교로

2026-10-18 Asia/Seoul. Parent `e01bb3e28dad90d0a74ef7442f6adf9b7d791541`, 기존 Draft PR #559. 사용자가 게시한 `l01_matched_window_refit.py`를 다시 구현하거나 기존 관측 결과를 덮어쓰지 않는다. 이번 bounded work는 full matched fit의 결과 판정과 다음 paired-data 검사를 위한 shared native RHS 계산기다. 새로운 전체 10단계 연구나 physical null 승인은 아니다.

## 1. 새로 확보된 근거와 닫는 질문

사용자가 실제 full matched fit을 실행하고 e01bb3e2...를 게시했다. 원격 commit 및 파일 blob `845c4034bd5dacd684a3d83de29bde5179514dc9`를 확인했다. 출력 파일의 UTC 이름은 `20261017T220911Z`, 한국시각으로 2026-10-18 07:09:11이다. 원본 숫자는 사용자 stdout이며 이 세션의 Planck 재실행 수치가 아니다.

| 계수 공간 | 기존 contrast norm [K_CMB] | 새 matched contrast norm [K_CMB] | norm 비 | energy 비 |
|---|---:|---:|---:|---:|
| all | 8.221782224682223e-8 | 2.6627381325987786e-8 | 0.3238638606 | 0.1048878002 |
| E | 5.5635571016801396e-8 | 1.9036695841666248e-8 | 0.3421677084 | 0.1170787407 |
| B | 6.053472997085642e-8 | 1.8617777732894176e-8 | 0.3075553115 | 0.09459026963 |

기존/새 norm과 그 벡터차의 norm으로 계산한 계수공간 각도는 all 64.6776876도, E 68.8561838도, B 60.5376557도다. 이 각도는 sky axis나 polarization angle이 아니다. 에너지가 약 90% 작아진 것은 새로운 통계량의 영역간 차이가 작아진 것이지 물리적 오염이나 noise를 90% 제거했다는 뜻이 아니다. 기존 source window를 zero-fill 대상으로도 fit하던 목적함수와, source 지원영역에 맞춘 목적함수가 다르다.

중심화 분해의 첫째 항 energy/original energy는 all 0.8487401249, E 0.8800667354, B 0.8222789399다. 두 데이터 의존 항의 상호간섭도 존재하므로 이 값을 인과적 오염 분율로 부르지 않는다. Raw 결과와 계산은 `MATCHED_SPLIT_STREAM_PROGRESS_20261018.json`에 기록했다.

이제 동일한 비교를 새로운 raw matched 추정량으로 HM1/HM2/OE1/OE2에 적용한다. 이전 L32 pseudo-spectrum 반차/full 비를 새 estimator의 잡음 비로 재사용하지 않는다.

## 2. 정확한 영역·선형성 계약

고정된 native source window W, 두 중첩 fit 영역 Mc,Mt와 기존 저차 기저 A를 그대로 사용한다. 모든 지도에서 동일한 Uc=Mc W, Ut=Mt W를 적용한다. 실제 지원영역은 Uc 37,120,921픽셀, Ut 36,951,769픽셀이며, 제외되는 실제 source 영역 J=(Mc-Mt)W는 169,152픽셀이다. 지도의 값이 0이거나 작은지에 따라 지원영역을 다시 선택하지 않는다. 유효하지 않은 Q/U가 이 고정 영역 안에 있으면 중단한다.

```
Sc = Gc-Cc = omega A^T Uc A
St = Gt-Ct = omega A^T Ut A
bc^(p) = omega A^T Uc x^(p)
bJ^(p) = omega A^T J x^(p)
bt^(p) = bc^(p)-bJ^(p)
beta_i^(p) = Si^-1 bi^(p)
```

여기서 x^(p)는 전달된 원본 Q_STOKES/U_STOKES이며 inpainted 열이 아니다. 단위 K_CMB, Galactic, COSMO convention, native NESTED2048 픽셀을 유지한다. 별도 beam이나 harmonic cutoff를 새로 곱하지 않는다. 추정 계수는 ell2..5이지만 입력 자료를 ell<=5로 미리 절단하는 것은 아니다.

두 정상방정식을 빼면

```
St (beta_t-beta_c) = (Sc-St) beta_c-bJ
beta_t-beta_c = St^-1[(Sc-St) beta_c-bJ].
```

새 코드는 bJ를 직접 누적하므로 두 큰 RHS를 뺀 값에만 의존하지 않는다. 위 식과 두 fit 차이를 대조한다. 이 식은 데이터가 정확한 저차 모형이 아니어도 성립하는 유한 선형대수 항등식이다.

동일 고정 선형 연산자 T를 사용하므로

```
T[(x1-x2)/2] = (Tx1-Tx2)/2,
||a_plus||^2-||a_minus||^2 = a1^T a2.
```

각 지도 fit 뒤에 split 조합을 만드는 경로와, raw RHS를 조합한 뒤 fit하는 경로를 검사한다. Wolfram 유리수 예제에서 shell 항등식 잔차는 2x2 영행렬, 반차 선형성 잔차는 영벡터, 마지막 이차 항등식 잔차는 0이었다. 제조된 수치이며 실제 Planck 통계값이 아니다.

잡음 성분에 대한 공분산은 T(N11+N22-N12-N21)T^T/4다. N12를 0이라고 가정하지 않는다. 실제 지도 pair의 내적은 ensemble noise covariance가 아니다. Full-minus-HM/OE-mean도 함께 보존한다. 새로운 통계량을 작게 만드는 쪽으로 자료·마스크·회귀 차수를 자동 선택하지 않는다.

## 3. 구현: 한 번의 basis 순회, 여러 RHS

새 파일 `L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_matched_split_stream.py`는 현재 사용자의 `matched_pair`를 직접 import한다. 기존 `l01_matched_window_data`의 두 입력 report binding 및 source/response 검증, 기존 producer의 source hashes/PMASK reader/low basis, 기존 no-clobber JSON writer를 재사용한다. 모든 기존 소스·입력은 unchanged다.

- 한 chunk에서 basis를 한 번만 평가하고 5개 지도 RHS에 공통 적용한다. 지원영역 밖의 pixel은 basis 계산과 data read를 생략한다.
- Gram과 hole moments는 보고서에서 재사용한다. A^T A, native SHT 및 inverse synthesis를 다시 하지 않는다.
- Q/U는 big-endian float32 원본에서 strided read-only memmap으로 읽는다. 누적은 float64와 보정 합산을 사용한다.
- full도 새 다중 RHS pass에 포함해 기존 native raw RHS와 full matched vector를 재현해야 한다. 단순 norm 비교가 아니라 벡터 비교다.
- 최종 JSON에 공통/제외 shell RHS, 기존 Gram/hole matrices, 5개 지도의 fit coefficients 및 진단량을 남긴다. 다음 선형 조합 분석에서는 이 작은 보고서를 재사용할 수 있다.

출력 statistics에는 `matched_common`, `matched_three_way_intersection`, `matched_contrast`, `original_contrast`의 all/E/B norm과 coefficient energy가 있다. HM/OE 합·반차, full-minus-split-mean, ordered pair의 signed cross 내적도 저장한다. 이는 **REAL_LOW64_COEFFICIENT_INNER_PRODUCT_NOT_PSEUDOCL**이다. 기존 pseudo-spectrum 밴드합과 수치 분모를 섞지 않는다.

이 실행은 소규모 JSON 후처리만 하는 것은 아니다. 고정 Boolean mask 50,331,648개를 훑고 실제 Uc에서 basis를 평가하며 다섯 FITS를 재검증·읽는다. 그러나 새 파일 다운로드, 전체 design 저장, Gram 재계산과 SHT가 없다. 별도의 actual native speedup 배수는 측정하지 않았다.

## 4. 실제 검증과 미검증

이번 환경에서 새 코드/테스트 바이트와 byte-exact `l01_matched_window_refit.py`로 **39 passed in 2.51s**를 확인했다. Python 3.13.5, NumPy 2.3.5, pytest 9.0.2. Compileall, 별도 subprocess CLI help, 기존 refit self-test도 통과했다.

독립 `numpy.linalg.lstsq` 비교, explicit paired Q/U pixel integration, chunk-size 불변성, 1e-100..1e10 진폭, pure-low 공통 신호 소거, 64계수 E/B 선택, 직접 반차 fit, signed cross identity, NaN/UNSEEN 및 변경 support 거절, big-endian Q/U 열 읽기, source metadata 변화, symlink/덮어쓰기 거절을 다뤘다. 첫 RHS 비교는 zero stub에서 20/20 성분 불일치로 실패한 뒤 구현 후 같은 검사로 통과했다. 모든 후속 회귀검사마다 개별 RED를 기록했다고 주장하지 않는다.

새 source blob `b15421111bcc9ded93cd7b8a4af225f1fd405ee0`, tests blob `5b45738d149d6d357cb1671448f69f4eeccc3486`, 재사용 refit blob `845c4034bd5dacd684a3d83de29bde5179514dc9`를 실제 테스트한 바이트와 대조했다. **Native healpy/FITS 전체 adapter, 실제 5개 지도 scan, 전체 저장소 CI는 여기서 NOT_RUN**이다. Desktop Commander는 이번 호출에서도 월간 사용 한도를 반환했다. Native subagent 도구가 없어 `native_subagent: NOT_RUN`; 순차 작업만 수행했다.

### 별도 CI 상태

기준 commit e01bb3e2의 PR merge `59032d115f82faf2d0553c13bb9124b8af0dbad1`, workflow run 39073886643을 읽었다. Python package smoke와 Rust compile은 success다. Repository contracts job 117516940576에서는 mirror check는 통과했지만 strict rescue validator가 다음 기존 카드를 미등록으로 거절했다.

```
PR-SF-CF4-PRECISION
PR-SF-GAIA-CORRELATION
PR-SF-METHODS-MANUSCRIPT
PR-SOLVER-FREE-DOSSIER
```

이는 native matched-fit test 실패가 아니라 전역 backlog 등록 문제다. 무시하여 CI PASS로 보고하지 않으며, 이 bounded L01 작업에서 whitelist를 느슨하게 하거나 기존 전역 DAG 카드를 수정하지 않았다. 후속 전역 저장소 계약 수정은 별도로 필요하다.

## 5. 동일 worktree의 실행 명령

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
python -m pytest -q "$S/tests/test_l01_matched_split_stream.py"
python "$S/src/l01_matched_split_stream.py" \
  --root "$ROOT" \
  --native-report "$ROOT/provenance/L01_NATIVE_PIXEL_RESIDUAL_full_20261017T135250Z.json" \
  --injection-report "$ROOT/provenance/L01_LOW_SOURCE_WINDOW_RESPONSE_20261017T150345Z.json" \
  --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
  --chunk-pixels 8192 \
  --out "$ROOT/provenance/L01_NATIVE_MATCHED_SPLITS_$(date -u +%Y%m%dT%H%M%SZ).json"
SH
```

먼저 `full_native_moment_replay`와 support counts를 확인한다. 그 다음 `matched_contrast.B.norms_K_CMB`의 full/HM_half_difference/OE_half_difference/full_minus_HM_mean/full_minus_OE_mean을 비교한다. 원래 보고한 full norm이 baseline에서 재현되지 않으면 새 split 결과를 승인하지 않는다. 보고서에 근거한 source/window 계약 불일치를 감춰서 이어가지 않는다.

## 6. 단계별 게시와 DAG

R8 실제 결과 판정, L01 C7 paired-data 계산 구현과 국소검증을 수행했다. 코드 commit `7eb5d90749541ae5b1a7c2920c449f34fa390592`; 테스트 commit `125fa3d34f90f56bea07fc4041ae08bc839cbf31`. 단계별 native 결과, 테스트 범위, CI failure 및 파생값은 같은 디렉터리 `MATCHED_SPLIT_STREAM_PROGRESS_20261018.json`에 있다.

매 단계에서 publication DAG는 P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7, 합계 **14/42 completed_scoped**, 28 pending이다. READY L01/S02; 모든 논문 NOT_READY_TO_SUBMIT. Full matched fit의 수치 실행은 닫혔으나 새 split 결과, 고차 모형/전달 가정과 L03 matched null은 미완료다. Source original, canonical publication DAG 및 전역 backlog는 이번 변경 대상이 아니다.

## Primary literature consulted

- Planck 2018 IV, sections 3.2/4.4: HMHD의 장기 systematics 민감도와 OEHD의 noise tracer 역할은 구분된다. 이 프로젝트의 새 회귀 통계량에서 그대로 calibrated null이라고 가정하지 않는다. https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html
- Copi et al., low-multipole reconstruction의 noise-free 정리와 실제 noisy/foreground data 적용을 구분하는 비교 문헌. https://arxiv.org/abs/1103.3505
- IRSA PR3 CMB 제품 설명과 split caveats. https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html

SciSpace는 문헌 발견, Exa와 공식 논문은 내용 확인, Wolfram은 유한 정확 행렬 검산에 사용했다. 새 통계적 유의성, E/B purification 또는 문헌적 신규성 정리는 주장하지 않는다.
