# L01: 실제 L32 분할 결과에서 대역 간섭과 L32/L64 유한 비교로

2026-10-17 Asia/Seoul. Parent `c58fcd380878a63fb6a362b311aa357c12ccaa1e`, 기존 Draft PR #559. 이번 bounded work는 R7/C7 데이터 기반 결과 해석과 대역 판별, 그리고 C8 유한 cutoff 비교를 위한 실행 가능한 진단기다. 새로운 전체 10단계 연구나 물리적 null 승인, 독립 subagent 검토를 주장하지 않는다.

## 1. 실제 L32 근거와 해석

사용자 로컬 stdout에서 full/HM1/HM2/OE1/OE2의 `PASS_PROCESSED_MAP_BAND_CLOSURE`, 전체 L=32의 `PASS_WINDOWED_QU_FINITE_BAND_ACCOUNTING`, 후처리의 `PASS_SAME_WINDOW_SPLIT_SPECTRA`가 보고됐다. 합/반차/교차 항등식 잔차는 HM `1.976782990677601e-16`, OE `1.332377253196197e-16`이다. 이 세션의 실제 FITS/NPZ 실행 결과는 아니다.

아래 S_XY는 sum_{ell=2}^5 (2ell+1) Ctilde_ell^XY/(4 pi)다. 단위는 microK_CMB^2이며 K^2에 10^12를 곱했다. 개별 C_ell, f_sky 보정 분산, noise-debiased cosmic spectrum과 다르다.

| 처리된 지도/차이 | S_EE [microK^2] | S_BB [microK^2] | S_EB [microK^2] |
|---|---:|---:|---:|
| Full | 0.0296324660 | 0.0199694198 | -0.00345519072 |
| HM 반차 | 0.00410035259 | 0.00280622191 | -0.000383812640 |
| OE 반차 | 0.00334224296 | 0.00138093104 | 0.000111577288 |
| Full - HM 평균 | 0.00801898066 | 0.00385384044 | -0.00133288267 |
| Full - OE 평균 | 0.00836560453 | 0.00323981212 | -0.00146133537 |

BB/full BB 비는 HM 반차 0.1405259610, OE 반차 0.06915228656, full-HM 평균 0.1929871008, full-OE 평균 0.1622386704다. HM 반차 BB/OE 반차 BB=2.0321231301. Full-평균 잔차 BB/해당 반차 BB는 HM 1.3733199147, OE 2.3461070991이다. 이 비율은 진단량의 상대 크기이며 잡음 분율이 아니다. Full과 split 단순평균이 이 처리된 저차 계수에서 동일하다는 가정은 비영 잔차와 맞지 않는다. 원인을 전달 차이, 가중치, 잔류 성분, 잡음 중 하나로 자동 귀속하지 않는다.

정규화된 full EB `S_EB/sqrt(S_EE S_BB)=-0.1420382798`은 signed harmonic inner-product 진단이다. 음의 값만으로 parity violation/birefringence 또는 통계적 유의성을 추론하지 않는다. PSD Gram 불평등의 만족도 physical validation은 아니다.

기존 5개 FITS source pins, native PMASK와 K는 그대로 유지한다. 데이터 재다운로드와 L32 native 재실행을 요구하지 않는다. 원시 수치와 계산은 `L32_NATIVE_RESULT_AND_CUTOFF_PROGRESS.json`에 보존한다.

## 2. 대역 벡터와 간섭항

기존 고정 window의 pseudo 계수를 a_tilde로 두면 두 coarse mask i=c,t의 선형 분해는

```
y_i(L) = a_tilde_[2:5] + K_i a_tilde_[6:8] + r_i(9:L)
d(L) = y_t(L)-y_c(L) = m(L)+t(L)
m(L) = (K_t-K_c) a_tilde_[6:8]
t(L) = r_t(9:L)-r_c(9:L).
```

E 또는 B 계수의 직교 선택행렬 R_X에 대해 d_X=R_X d, m_X=R_X m, t_X=R_X t라 하면

```
||d_X||^2 = ||m_X||^2 + ||t_X||^2 + 2 m_X^T t_X.
```

이 식으로 6..8과 9..L 대역의 보강/상쇄를 직접 계산한다. 간섭항은 signed이며 삭제하지 않는다. 두 성분이 모두 비영일 때

```
rho_X = (m_X^T t_X)/(||m_X|| ||t_X||)
eta_X = ||d_X||/(||m_X||+||t_X||)
```

이고 정확한 산술에서 -1<=rho_X<=1, 0<=eta_X<=1이다. 정의되지 않는 영벡터 비율은 JSON null로 둔다. 이 rho는 확률적 잡음 상관계수가 아니라 결정론적 벡터 정렬도다.

Wolfram 정확 제조 예제 m=(3,4), t=(-2,-4)는 25+20-44=1을 반환했다. 개별 대역 에너지를 합해 실제 효과를 45로 보고하면 틀린다. 새 검사는 모든 제품과 HM/OE 반차, full-minus-split-mean에 같은 선형 조합을 적용한다.

계수 norm 제곱은 K_CMB^2 단위지만 1절의 (2ell+1)/(4pi)-weighted pseudo-spectrum 대역합 자체는 아니다. 출력은 `LOW64_REAL_COEFFICIENT_NORM_NOT_PSEUDOCL_BAND_POWER`로 구별한다.

현재 제공된 stdout에는 저차 pseudo-spectrum 대역합만 있고 m/t 벡터와 간섭항은 없다. 실제 간섭의 크기나 부호를 여기서 추정하지 않는다. 새 코드가 기존 `summary.json` 및 제품별 결과 벡터를 읽어 계산한다.

## 3. 유한 cutoff 비교와 그 한계

같은 자료, native window, source pins, 코드/의존성 SHA, healpy 버전, output NSIDE64를 유지하고 lmax만 L에서 H로 바꾼다. 두 producer contract가 lmax 외에 다르면 비교를 거절한다. 낮은 cutoff의 packed alm은 높은 cutoff 배열의 prefix가 아니므로 (ell,m)으로 재색인한다.

```
e_overlap = a_tilde^(H)_[2:L] - a_tilde^(L)_[2:L]
d(H)-d(L) = [m(H)-m(L)] + [t(H)-t(L)].
```

첫 식은 공통 모드의 수치 재현성, 두 번째는 추정량 벡터의 유한 cutoff 변화다. Norm의 차이만 보지 않고 벡터 차이 norm을 저장한다. 크기가 같은 (1,0), (0,1)의 차이 norm은 sqrt(2)이며 이에 대한 Wolfram 계산과 회귀 테스트가 있다.

동일 quadrature로 계산하는 출력 공통 모드는 정확한 산술에서 lmax 선택에 독립적이다. 따라서 작은 e_overlap은 수치 일관성이지 독립적 물리 검증이 아니다. 실제 SHT 구현의 roundoff/algorithm 변화는 이 잔차에 나타날 수 있다.

`t(H)-t(L)`은 새 L+1..H 대역뿐 아니라 겹치는 9..L 모드의 수치 변화도 포함한다. 이를 순수 추가대역 투영이라고 부르지 않는다. 새 대역 alm norm을 별도로 제공하지만 mask-projected tail을 대신하지 않는다.

a_tilde_ell은 이미 native window가 곱해진 전달 지도의 pseudo 계수다. 마스크 결합 때문에 원래 지도의 더 높은 ell'도 출력 저차 ell에 기여할 수 있다. L64 일치나 작은 33..64 기여가 physical ell>64 tail 상계를 입증하지 않는다. `convergence_certified=false`, `infinite_tail_bound=NOT_ESTABLISHED`를 유지한다.

## 4. 구현과 검증 근거

Source: `L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_cutoff_band_diagnostics.py`.
Tests: 같은 stage의 `tests/test_l01_cutoff_band_diagnostics.py`.

기존 `l01_split_checkpoint_spectra.py`를 직접 import하여 source-bound checkpoint reader, alm validation, 스펙트럼 정규화, no-overwrite JSON writer를 재사용한다. 해당 reader의 보존 바이트 Git blob은 원격과 같은 `96beda7c788519c40aaa11f502046b7d79726ca3`다. Native producer와 기존 reader를 수정하지 않았다.

새 코드는 SHT/FITS 읽기 없이 같은 run의 summary.results와 제품별 record.result의 일치, band closure, 두 마스크의 공통 low term 소거, 저장 delta와 mask별 차이를 확인한다. Alms에서 projection을 독립 재합성한 것은 아니므로 `projections_independently_recomputed=false`다. Checkpoint 귀속/무결성과 관측 우도 검증은 다르다.

현재 런타임에서 **32 passed in 1.40s**, compileall과 subprocess --help를 확인했다. Python 3.13.5, NumPy 2.3.5, pytest 9.0.2. 영/평행/직교/반평행 벡터, 단위 스케일 1..1e-100, 상대 closure, m-major 재색인, 같은 norm/다른 벡터, 공통 계수 변화, 5-product JSON/NPZ 통합, metadata/byte 손상과 덮어쓰기 거절을 검사했다. Native HEALPix 변환, 실제 L32 vector budget, 실제 L64 비교, 전체 저장소 CI는 이 세션에서 NOT_RUN이다.

Source commit `df2fd82d24e92915437d6c1c85c24a7fbda3f869`; test commit `767692dd7c095b613f669c07c289f4cb54c462ec`. 테스트 바이트와 원격 Git blob이 일치한다. Code blob `a4fb584a1d830bf9260634886f911b81f15adce1`, test blob `985a65d4849afa7bdcadd9c6893ece4727794312`. Native subagent는 도구가 없어 NOT_RUN이며 순차 검증만 수행했다. 이전 80개 재구성 테스트나 전체 저장소 테스트 수로 합산하지 않는다.

## 5. 기존 worktree 실행

로컬 수정이 있으면 보존하고 중단한다. 첫 진단은 L32 checkpoint만 사용한다. 다음 L64 native 처리는 기존 producer로 별도 폴더에서 한 번 수행한다. 데이터 재다운로드나 L32 덮어쓰기는 없다.

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
python -m pytest -q "$S/tests/test_l01_cutoff_band_diagnostics.py"

L32="$ROOT/provenance/L01_SMICA_WINDOWED_QU_L32"
L64="$ROOT/provenance/L01_SMICA_WINDOWED_QU_L64"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
python "$S/src/l01_cutoff_band_diagnostics.py" \
  --band-dir "$L32" --out "$L32/band_diagnostics_$STAMP.json"

python "$S/src/l01_smica_processed_bands.py" \
  --root "$ROOT" \
  --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
  --out-dir "$L64" --lmax 64 --products full hm1 hm2 oe1 oe2

COMPARE="$ROOT/provenance/L01_L32_L64_diagnostics_$STAMP.json"
python "$S/src/l01_cutoff_band_diagnostics.py" \
  --band-dir "$L32" --higher-band-dir "$L64" --out "$COMPARE"
python - "$COMPARE" <<'PY'
import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
c=r['cutoff_comparison']
print(json.dumps({'status':c['status'],
  'full_common_modes':c['products']['full'],
  'full_projection_change':c['projected_contrast_changes']['full'],
  'convergence_certified':c['convergence_certified'],
  'infinite_tail_bound':c['infinite_tail_bound']},indent=2))
PY
SH
```

새 자료 다운로드는 필요하지 않다. Producer code/source 계약 또는 불완전 checkpoint 검증이 실패하면 기존 파일을 보존하고 해당 불일치를 조사한다. 저장 해시를 바꾸어 통과시키지 않는다. 위 동일-code 비교는 source lock을 변경하지 않는다.

## 6. 단계별 DAG와 출처

R7/C7 실제 L32 결과 판정, C7/C8 진단기 구현, 국소검증과 게시의 매 단계에서 canonical DAG는 **14/42**다. P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7. READY L01/S02; six papers NOT_READY_TO_SUBMIT. L01은 실제 processed data를 얻었지만 full physical high-tail/selected TEB transport는 완료되지 않았다. L03 matched simulation law는 별도이며 canonical 245-card backlog와 main을 변경하지 않는다.

SciSpace/Exa와 공개 원전으로 확인한 출처:
- Planck 2018 IV, component-separated polarization and noise: https://arxiv.org/abs/1807.06208
- Planck 2018 VII, residual systematics and large-angle tests: https://arxiv.org/abs/1906.02552
- ESA Planck Legacy Archive CMB maps, split correlations and masks: https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps
- Native map2alm_spin API: https://healpy.readthedocs.io/en/latest/generated/healpy.sphtfunc.map2alm_spin.html

검색 인덱스 날짜를 출판일로 사용하지 않았다. 수학적 항등식은 직접 유도/유한 검산이며 새로운 no-go 정리나 문헌적 신규성 주장으로 포장하지 않는다.
