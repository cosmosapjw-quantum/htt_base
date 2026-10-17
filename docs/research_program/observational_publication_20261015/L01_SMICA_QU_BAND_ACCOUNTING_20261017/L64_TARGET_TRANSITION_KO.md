# L01: L32/L64 결과 판정과 목표 계수의 진폭·방향 안정성

2026-10-17 Asia/Seoul. Parent `c0e6555512b24957a064ec654e3d36bd6a6f8390`, 기존 Draft PR #559. 이번 실행 범위는 첨부된 L32/L64 native 결과에 대한 R8 판정과 C8 목표량 안정성 진단이다. Source lock, native producer, 기존 cutoff/reader, 공식 42-node publication DAG는 변경하지 않는다.

## 1. 첨부 실행 결과와 직접 따라오는 결론

첨부 `Pasted text(20261017-091214).txt`의 SHA256은 `b093c190d7141dfa9d0ae2b2e0dbde056ab9721e268798ca5063a30933cac9a9`다. 사용자 실행 결과와 이 세션의 검산을 구별한다. 사용자 로그는 다음을 보고했다.

- parent commit에서 exact clean HEAD/import gate 통과, 당시 32개 테스트 통과.
- full/HM1/HM2/OE1/OE2 모두 L64 band closure 통과.
- Full의 공통 ell<=32 계수 차이 norm 1.1698100408045762e-23 K_CMB, 상대 L2 8.561315802988542e-18.
- Full의 저차 추정량 차이 d64-d32 norm 1.355381573182645e-8 K_CMB.
- 이 변화는 d32 norm의 0.18587413725820845이지만 parent roundoff-reference scale의 0.005219069850843344다.
- B 성분의 변화 norm 제곱 7.601518135674755e-17 K_CMB^2, E 성분은 1.0769073953555862e-16 K_CMB^2다. 출력된 mid-band 증분 에너지는 0이다.

따라서 공통 모드의 수치 재현성과 목표 d의 cutoff 안정성을 구분해야 한다. 18.5874%는 두 finite cutoff 간 변화이지 참값에 대한 오차율이 아니다. Parent scale로 나눈 0.5219%는 roundoff 정규화 기준이며 d 자체의 정확도를 뜻하지 않는다. 임의의 새 허용오차를 만들어 PASS/FAIL을 판정하지 않는다.

L32 full B-budget은 mid=7.282519758111296e-16, tail=1.2249910522040206e-15, signed interference=9.776253084869412e-16, total=2.9308683365020923e-15 K_CMB^2다. 간섭항은 total의 33.356166%로 양의 보강이다. OE 반차 간섭항은 -1.5020562313033273e-16이고 total 2.6893085335391457e-16의 -55.852879%로 상쇄다. 이는 계수 norm 제곱의 에너지 분해이며, 확률적 source fraction이나 이전 pseudo-Cl 대역 power와 동일한 양이 아니다.

L64 비교 stdout의 low_B_coefficient_budgets/lmax=32는 코드가 기준인 low run을 출력한 것이다. L64 계산이 잘못 L32로 실행됐다는 증거가 아니다. 실제 L64 energy나 d32와 d64의 내적은 stdout에 없으므로 변화 방향 또는 energy 증가를 추정하지 않는다.

## 2. 구성적 유도: 에너지 변화와 방향 변화를 분리

한 고정 계수 공간(all, E 또는 B)에서 x=d_L, y=d_H, e=y-x, n=||x||>0라 하자. 모두 같은 실수 정규직교 계수 convention을 사용한다. 정의는

```
r = ||e||/n
alpha = <x,e>/n^2
e_perp = e-alpha*x
beta = ||e_perp||/n.
```

<x,e_perp>=0이므로 r^2=alpha^2+beta^2다. y=(1+alpha)x+e_perp를 제곱하면 정확히

```
||y||^2/||x||^2 = 1+2alpha+r^2 = (1+alpha)^2+beta^2.
```

양쪽 벡터가 비영일 때 계수공간 각도는 `theta=atan2(beta,1+alpha)`다. 이것은 하늘의 방향축 회전각, 편광각 또는 birefringence angle이 아니다. 원래 하늘의 통계적 의미를 별도 정의하기 전에는 그 어떤 각도와도 동일시하지 않는다.

Wolfram에서 x=(3,4), e=(1,-2)에 대해 alpha=-1/5, beta^2=4/25, r^2=1/5를 얻었고 에너지 항등식을 정확 검산했다. 이 예제는 native Planck 결과가 아니다.

### Norm만 있을 때의 날카로운 범위

정확히 ||e||=r||x||를 알면 양방향 삼각부등식으로

```
|1-r| <= ||y||/||x|| <= 1+r.
```

따라서 energy ratio는 [(1-r)^2,(1+r)^2] 안이다. r<1이면 x.y>0이고 x를 y 방향에 직교 투영한 길이 n sin(theta)는 ||e|| 이하이므로 `theta<=asin(r)`다. x=(1,0), y=(1-r^2,r*sqrt(1-r^2))는 ||y-x||=r 및 sin(theta)=r를 만족하여 이 상계가 달성 가능함을 보인다. Wolfram r=3/5 검산에서 두 조건을 확인했다. 신뢰구간이 아니라 같은 finite step의 결정론적 기하 상계다.

첨부 scalar만 사용해 다음을 직접 계산했다.

| 계수 공간 | r | 가능한 energy ratio | coefficient-angle 상계 |
|---|---:|---|---:|
| all E/B | 0.1858741373 | [0.6628009204, 1.4062974694] | 10.71210076 deg |
| B only | 0.1610467680 | [0.7038425255, 1.3480295974] | 9.267659589 deg |

이 범위에서 실제 energy ratio와 실제 각도를 선택하려면 저장된 x,y 벡터를 읽어야 한다. 새 코드가 그 계산을 한다. 거의 0인 baseline에는 상대값을 억지로 정하지 않고 null을 출력한다. Exact zero endpoint에는 각도를 정의하지 않는다.

## 3. 다음 finite step와 tail 주장 경계

d32,d64,d128을 같은 원본/코드/window/출력 grid로 계산하면 두 증분 e1=d64-d32, e2=d128-d64의 norm 비와 정렬도를 기록할 수 있다. e1=0이면 비율은 정의되지 않는다. e1가 작거나 0이었다고 미래 증분도 작다고 판정하지 않는다.

가정으로 모든 미래 증분에 대해 ||e_(j+k)||<=q^k||e_j||, 0<=q<1을 증명하거나 외부적으로 정당화했다면 삼각부등식과 기하급수 합으로 ||d_infinity-d_j||<=q/(1-q)||e_j||가 성립한다. 하지만 관측된 한 번의 ||e2||/||e1||는 이 모든 k에 대한 전제를 증명하지 않는다. 새 코드는 경험적 비만 출력하고 미래 contraction bound, extrapolated limit, infinite-tail certificate를 만들지 않는다.

현재 native producer의 L=128은 기존 허용범위의 마지막 값이다. 이번 인계는 L128 한 번의 추가 finite 비교까지이며 L256 이상으로 자동 확대하지 않는다. L128 결과 후에도 target 변화가 남으면 finite diagnostic 범위를 고정할지, estimator/window/고차 source 가정의 변경을 별도 연구할지 결정해야 한다. 원래 estimator를 바꾸면서 같은 관측량의 수렴이라고 표시해서는 안 된다.

## 4. 구현 재사용과 실제 검증

새 파일은 `L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_target_transition.py`, 테스트는 같은 stage의 `tests/test_l01_target_transition.py`다. 기존 `l01_cutoff_band_diagnostics.py`의 load_run/compare_runs/low_indices와 기존 checkpoint reader/writer를 직접 재사용한다. Scalar summary에서 실제 내적을 복원하지 않고 원래 저장된 벡터를 읽는다. 새 코드에는 FITS 읽기, SHT, 데이터 다운로드 또는 새 beam 처리가 없다.

현재 샌드박스 테스트에 사용한 기존 cutoff와 reader의 전체 바이트 Git blob은 원격과 각각 `a4fb584a1d830bf9260634886f911b81f15adce1`, `96beda7c788519c40aaa11f502046b7d79726ca3`로 일치한다. 신규 코드 Git blob `4fc3da000f3dfec0c69b3573229f379a449c84ad`, 테스트 `0cc137a2b89f18574e352ee1ce1661ec9a9c2855`다. Source commit `99a4745681e3baa6a4bd70fc230cf514beedbde1`, test commit `238a7ba5b9c0fc29d2d0796f44ddd33206956af1`.

새 기능 부재를 검사하는 test의 실패를 먼저 확인한 뒤 구현했다. 실제 마지막 실행은 **27 passed in 2.92s**, compileall과 standalone CLI help PASS다. Python3.13.5, NumPy2.3.5, pytest9.0.2. Radial/transverse decomposition, sharp-angle witness, 같은 norm/다른 방향, shrink/grow/sign reversal, zero cases, orthogonal basis change, 1e-100..1e100 공통 scale, 두/세 cutoff의 5-product checkpoint integration, source byte/window 불일치와 덮어쓰기 거절을 검사했다. 통합 fixture는 archive protocol을 시험하며 실제 map-to-vector physical correspondence를 주장하지 않는다.

실제 사용자 checkpoint의 새로운 각도/energy ratio 및 L128 native 계산은 이 세션에서 NOT_RUN이다. Remote Desktop 실행은 현재 월간 quota로 차단됐으며 재시도하지 않았다. Whole-repository CI와 native subagent도 NOT_RUN이다. 원본 파일·기존 결과·Git hook·사용자 소유권 설정을 변경하지 않았다.

## 5. 기존 worktree 실행: 먼저 기존 두 cutoff만 읽기

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
python -m pytest -q "$S/tests/test_l01_target_transition.py"
L32="$ROOT/provenance/L01_SMICA_WINDOWED_QU_L32"
L64="$ROOT/provenance/L01_SMICA_WINDOWED_QU_L64"
L128="$ROOT/provenance/L01_SMICA_WINDOWED_QU_L128"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)

# Read-only two-cutoff geometry; no native reprocessing.
python "$S/src/l01_target_transition.py" \
  --band-dirs "$L32" "$L64" \
  --out "$ROOT/provenance/L01_TARGET_GEOMETRY_L32_L64_$STAMP.json"

# One new native cutoff, with the unchanged producer and separate checkpoints.
python "$S/src/l01_smica_processed_bands.py" \
  --root "$ROOT" \
  --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
  --out-dir "$L128" --lmax 128 --products full hm1 hm2 oe1 oe2

python "$S/src/l01_target_transition.py" \
  --band-dirs "$L32" "$L64" "$L128" \
  --out "$ROOT/provenance/L01_TARGET_GEOMETRY_L32_L64_L128_$STAMP.json"
SH
```

출력 full_transitions에는 cutoff별 all/E/B 실제 energy ratio, relative increment, alpha/beta, coefficient angle이 있고, full_empirical_steps에는 두 증분의 경험적 norm 비와 정렬도가 있다. 모든 제품과 분할/잔차 조합의 결과는 JSON에 저장한다. Existing producer contract는 동일하게 유지된다. 재개 시 불완전하거나 계약이 다른 checkpoint를 발견하면 보존하고 조사하며, 해시를 교체하여 통과시키지 않는다.

## 6. 단계별 publication DAG

R8 판정, C8 구현, C8 국소 검증·게시의 각 단계 후 **14/42 completed_scoped**를 유지한다. P1 1/6; P2 0/6; P3 2/6; P4 1/6; P5 1/5; P6 2/6; COMMON 7/7. READY L01/S02. L01의 cutoff 정량 결과는 진척이지만 L03의 실제 physical null 또는 submission admission이 아니다. Main merge와 canonical backlog 변경은 없다. Machine-readable evidence는 같은 폴더의 `L64_TARGET_TRANSITION_PROGRESS.json`에 있다.

## 7. 외부 근거와 직접 유도 구분

Planck 원 논문의 실제 편광 계통오차/시뮬레이션 caveat와 healpy API 계약은 아래 원전에 근거한다. 위 벡터 항등식과 sharp bounds는 이 문서의 직접 유도 및 Wolfram/NumPy 검산이며 새로운 우주론적 결과나 no-go 정리로 주장하지 않는다. SciSpace/Exa 검색은 보조 탐색에 사용했고 요청한 문서와 무관한 검색 결과를 근거로 채택하지 않았다.

- Planck 2018 VII, 원 논문: https://arxiv.org/abs/1906.02552
- healpy map2alm_spin 공식 문서: https://healpy.readthedocs.io/en/latest/generated/healpy.sphtfunc.map2alm_spin.html
