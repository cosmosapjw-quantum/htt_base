# L01: 실제 L32 분할 결과에서 대역 간섭과 L32/L64 유한 비교로

2026-10-17 Asia/Seoul. Parent `c58fcd380878a63fb6a362b311aa357c12ccaa1e`, existing Draft PR #559. Selected bounded work: R7/C7 data-based interpretation and finite-band scientific check, with executable C8 cutoff-comparison support. A new full ten-stage cycle, physical null admission, or independent-subagent review is not claimed.

## 1. 이번에 확보된 실제 근거

사용자 로컬 stdout에 근거한다. 실제 FITS/NPZ를 이 샌드박스에서 실행한 결과가 아니다. Full/HM1/HM2/OE1/OE2에서 `PASS_PROCESSED_MAP_BAND_CLOSURE`, 전체 L=32에서 `PASS_WINDOWED_QU_FINITE_BAND_ACCOUNTING`과 `PASS_SAME_WINDOW_SPLIT_SPECTRA`가 보고됐다. 합/반차/교차 항등식 잔차는 HM `1.976782990677601e-16`, OE `1.332377253196197e-16`이다.

아래 S_XY는 sum_{ell=2}^5 (2ell+1) Ctilde_ell^XY/(4 pi)다. 단위는 microK_CMB^2로 환산했으며 K^2에 10^12를 곱한다. 개별 C_ell, f_sky로 보정한 sky variance, noise-debiased cosmic spectrum과 동일시하지 않는다.

| 처리된 지도/차이 | S_EE [microK^2] | S_BB [microK^2] | S_EB [microK^2] |
|---|---:|---:|---:|
| Full | 0.0296324660 | 0.0199694198 | -0.00345519072 |
| HM 반차 | 0.00410035259 | 0.00280622191 | -0.000383812640 |
| OE 반차 | 0.00334224296 | 0.00138093104 | 0.000111577288 |
| Full - HM 평균 | 0.00801898066 | 0.00385384044 | -0.00133288267 |
| Full - OE 평균 | 0.00836560453 | 0.00323981212 | -0.00146133537 |

계산된 BB/full BB 비는 순서대로 HM 반차 0.1405259610, OE 반차 0.06915228656, full-HM 평균 0.1929871008, full-OE 평균 0.1622386704다. HM 반차 BB/OE 반차 BB=2.0321231301. Full-평균 잔차 BB/해당 반차 BB는 HM 1.3733199147, OE 2.3461070991이다. 이 비율은 진단량의 상대 크기이며 잡음 분율이 아니다. Full과 split 단순평균이 이 처리된 저차 계수에서 동일하다는 가정은 제공된 비영 잔차와 맞지 않는다. 원인은 전달 차이, 가중치, 잔류 성분, 잡음 중 하나로 자동 귀속할 수 없다.

정규화된 full EB `S_EB/sqrt(S_EE S_BB)=-0.1420382798`은 signed harmonic inner-product 진단이다. 음의 값만으로 parity violation/birefringence 또는 통계적 유의성을 추론하지 않는다. PSD Gram 불평등을 만족한다는 사실도 physical validation은 아니다.

원래 5개 FITS source pins, native PMASK 및 K는 그대로 유지한다. 데이터 재다운로드와 L32 native 재실행을 요구하지 않는다. 원시 수치와 계산은 `L32_NATIVE_RESULT_AND_CUTOFF_PROGRESS.json`에 보존한다.

## 2. 다음 판별량: 벡터 합과 power 합은 다르다

기존 고정 window에서 나온 pseudo 계수를 a_tilde로 둔다. 두 coarse mask 추정량 i=c,t의 기존 선형 분해는

```
y_i(L) = a_tilde_[2:5] + K_i a_tilde_[6:8] + r_i(9:L)
d(L) = y_t(L)-y_c(L) = m(L)+t(L)
m(L) = (K_t-K_c) a_tilde_[6:8]
t(L) = r_t(9:L)-r_c(9:L).
```

E 또는 B 계수만 선택하는 직교 선택행렬 R_X에 대해 d_X=R_X d, m_X=R_X m, t_X=R_X t로 정의한다. 그러면

```
||d_X||^2 = ||m_X||^2 + ||t_X||^2 + 2 m_X^T t_X.
```

이를 통해 6..8과 9..L 대역의 보강/상쇄를 직접 계산한다. 간섭항은 signed이며 삭제하지 않는다. 두 성분이 모두 비영일 때

```
rho_X = (m_X^T t_X)/(||m_X|| ||t_X||),
eta_X = ||d_X||/(||m_X||+||t_X||)
```

이고 정확한 산술에서 -1<=rho_X<=1, 0<=eta_X<=1이다. 영벡터일 때 정의되지 않는 rho나 eta는 JSON null로 둔다. 이 rho는 확률적 noise correlation 추정치가 아니라 두 결정론적 벡터의 정렬도다.

Wolfram 정확 제조 예제 m=(3,4), t=(-2,-4)는 25+20-44=1을 반환했다. 개별 대역 에너지 25와 20을 더해 실제 효과 45라고 보고하면 틀린다. 새 검사는 모든 제품과 HM/OE 반차, full-minus-split-mean에 대해 같은 선형 조합을 적용한다.

이 계수 norm 제곱은 K_CMB^2 단위를 갖지만 1절의 (2ell+1)/(4pi)-weighted pseudo-spectrum 대역합 자체는 아니다. 출력에서 `LOW64_REAL_COEFFICIENT_NORM_NOT_PSEUDOCL_BAND_POWER`로 구별한다.

현재 사용자가 붙인 stdout에는 저차 pseudo-spectrum 대역합만 있고, m/t 벡터와 간섭항은 없다. 따라서 실제 간섭의 크기나 부호는 여기서 추정하지 않는다. 다음 코드가 기존 저장된 `summary.json` 및 제품별 결과 벡터를 읽어 계산한다.

## 3. L32/L64 비교에서 실제 검사하는 것

같은 자료, native window, source pins, 코드/의존성 SHA, healpy 버전, output NSIDE64를 유지하고 오직 lmax만 L에서 H로 바꾼다. 두 producer contract가 lmax 외에 다르면 비교를 거절한다. 낮은 cutoff의 packed alm 배열은 높은 cutoff 배열의 prefix가 아니므로 반드시 (ell,m)으로 다시 색인한다.

```
e_overlap = a_tilde^(H)_[2:L] - a_tilde^(L)_[2:L]
d(H)-d(L) = [m(H)-m(L)] + [t(H)-t(L)].
```

첫 식은 공통 모드의 수치 재현성, 두 번째는 실제 추정량 벡터의 유한 cutoff 변화다. norm의 차이만 보지 않고 벡터 차이 norm을 저장한다. 크기가 같은 두 벡터 (1,0), (0,1)도 차이 norm은 sqrt(2)이며, 이에 대한 Wolfram 계산과 회귀 테스트가 있다.

T_L은 동일한 native map의 특정 출력 계수 집합을 계산하므로, 정확한 같은 quadrature에서 공통 모드는 lmax 선택에 독립적이다. 따라서 매우 작은 e_overlap은 수치 일관성이지 독립적인 물리 검증이 아니다. 실제 SHT 구현의 roundoff/algorithm 변화는 그 잔차에 나타날 수 있다.

`t(H)-t(L)`은 새 대역 L+1..H뿐 아니라 겹치는 9..L 모드의 수치 변화도 포함한다. 코드가 이를 순수 추가대역 투영이라고 부르지 않는다. 새 대역 alm 자체의 norm은 별도로 제공하지만 그 양만으로 mask-projected tail을 대신하지 않는다.

가장 중요한 범위 구분: a_tilde_ell은 이미 native window가 곱해진 전달 지도의 pseudo 계수이다. 마스크 결합 때문에 원래 지도의 더 높은 ell'도 출력 저차 ell에 기여할 수 있다. L64 일치나 작은 33..64 기여가 physical ell>64 tail 상계를 입증하지 않는다. `convergence_certified=false`, `infinite_tail_bound=NOT_ESTABLISHED`를 유지한다.

## 4. 구현과 실제 검증

새 source: `L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_cutoff_band_diagnostics.py`.
새 tests: 같은 stage의 `tests/test_l01_cutoff_band_diagnostics.py`.

기존 `l01_split_checkpoint_spectra.py`를 직접 import하여 source-bound checkpoint reader, alm validation, 스펙트럼 정규화, no-overwrite JSON writer를 재사용한다. 기존 reader는 샌드박스에 보존한 바이트의 Git blob `96beda7c788519c40aaa11f502046b7d79726ca3`로 원격과 일치함을 확인했다. Native producer와 기존 reader를 수정하지 않았다.

새 코드는 별도 SHT/FITS 읽기 없이 저장된 결과를 검증한다. 같은 run의 summary.results와 제품별 record.result의 일치, band closure, 두 마스크의 공통 low term 소거, 저장된 delta와 mask별 차이를 확인한다. 이는 독립적으로 alms에서 projection을 다시 합성했다는 뜻이 아니며 출력에도 `projections_independently_recomputed=false`로 명시한다. checkpoint의 무결성/귀속과 진짜 관측 우도 검증은 다르다.

현재 런타임에서 **32 passed in 1.40s**, compileall 및 독립 subprocess --help를 확인했다. Python 3.13.5, NumPy 2.3.5, pytest 9.0.2. 신규 테스트는 영/평행/직교/반평행 벡터, 단위 스케일 1..1e-100, 상대 closure, m-major cutoff 재색인, 같은 norm/다른 벡터, 공통 계수 변화, 5-product JSON/NPZ 통합, metadata/byte 손상, 경로/덮어쓰기 거절을 다룬다. Native HEALPix 변환, 실제 L32 vector budget, 실제 L64 비교 및 전체 저장소 CI는 이 세션에서 NOT_RUN이다.

Source commit `df2fd82d24e92915437d6c1c85c24a7fbda3f869`; test commit `767692dd7c095b613f669c07c289f4cb54c462ec`. 두 파일은 테스트한 바이트와 원격 Git blob이 일치한다. 새 code blob `a4fb584a1d830bf9260634886f911b81f15adce1`, test blob `985a65d4849afa7bdcadd9c6893ece4727794312`. Native subagent 도구가 없어 NOT_RUN, 순차 실행만 수행했다. 이전 80개 재구성 테스트나 전체 저장소 테스트 수로 합산하지 않는다.

## 5. 기존 worktree에서 실행

새 worktree/ZIP/다운로드 없이 기존 사용자 소유 worktree를 갱신한다. 로컬 수정이 있으면 보존하고 중단한다. 첫 번째 진단은 기존 L32 checkpoint만 사용한다. 그 다음 L64 native 처리는 기존 producer로 별도 폴더에 한 번 수행한다. 기존 L32 폴더는 덮어쓰지 않는다.

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

新規資料は不要。If a producer code/source contract or incomplete checkpoint fails validation, preserve it and inspect the specific mismatch instead of changing stored hashes. The default same-code continuation above does not alter any source lock.

## 6. 단계별 DAG와 출처

R7/C7 실제 L32 결과 판정, C7/C8 진단기 구현, 국소 구현 검증 및 게시의 매 단계에서 canonical DAG는 **14/42**다. P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7. READY L01/S02; six papers NOT_READY_TO_SUBMIT. L01은 실제 processed data를 얻었지만 full physical high-tail/selected TEB transport가 완료되지 않았다. L03의 matched simulation law는 별도다. Canonical 245-card backlog와 main은 변경하지 않는다.

Primary sources consulted through SciSpace, Exa and the public primary pages:
- Planck 2018 IV, component-separated polarization and complex noise properties: https://arxiv.org/abs/1807.06208
- Planck 2018 VII, residual systematics and source-matched large-angle tests: https://arxiv.org/abs/1906.02552
- ESA Planck Legacy Archive CMB maps, odd/even noise correlations and split masks: https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps
- Native map2alm_spin API: https://healpy.readthedocs.io/en/latest/generated/healpy.sphtfunc.map2alm_spin.html

SciSpace index dates were not used as publication dates. Mathematical identities above are direct derivations/finite checks, not new no-go theorems or claims of novel literature results.
