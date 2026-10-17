# L01 C8: harmonic cutoff와 출력 적분 격자의 분리

2026-10-17 Asia/Seoul. Parent `04f633cafe857875baa9a7945e6b700821f52fbc`, 기존 Draft PR #559. 이번 작업은 현재 C8의 미완료 수치 검사 한 가지, 즉 고정된 저장 계수/마스크 영역에서 출력 격자를 세분화하는 검사를 구현하고 검증한다. 이미 게시된 L32/L64 target-angle 계산과 L128 실행을 반복했다고 주장하지 않는다. 원본 추정량의 정의나 scientific claim gate를 바꾸지 않는다.

## 입력 증거와 아직 없는 결과

현재 첨부 `Pasted text(20261017-091214).txt`의 SHA256은 `b093c190d7141dfa9d0ae2b2e0dbde056ab9721e268798ca5063a30933cac9a9`다. 같은 L32/L64 로그이며 새 L128 결과는 포함하지 않는다. 사용자 실행으로 확보된 full 결과는 공통 alm 상대 차이 `8.561315802988542e-18`, 목표 벡터 증분 norm `1.355381573182645e-8 K_CMB`, L32 목표 norm 기준 상대 변화 `0.18587413725820845`다. Parent roundoff scale 기준 `0.005219069850843344`와 혼동하지 않는다.

이 값은 기존 NSIDE64 output estimator의 유한 cutoff 의존성이다. 오류율, continuum residual 또는 물리 B-mode contamination으로 해석하지 않는다. 사용자 로컬의 L64/L128 summary 직접 읽기는 Desktop Commander 월간 한도로 차단되었고 재시도하지 않았다. L128 생성, 실제 target angle, 이번 새 native-grid replay는 이 세션에서 NOT_RUN이다.

## 1. 확인할 수치 문제

기존 파이프라인은 원해상도 windowed Q/U에서 pseudo-alm을 계산한 뒤, 유한 대역을 RING NSIDE64에 합성하고 두 mask별 low-ell least squares를 구한다. 이산 적분과 harmonic cutoff는 서로 다른 선택이다. 같은 cutoff를 유지해도 출력 sampling grid를 바꾸면 Gram 적분과 자료 moment가 변할 수 있다. 반대로 같은 격자에서 cutoff만 바꾼 기존 18.59% 결과는 그 격자에서 유효한 결과로 그대로 보존한다.

HEALPix 문서는 pixel-center harmonic quadrature가 근사임을 설명한다. 이를 근거로 기존 코드가 틀렸다고 판정하지는 않는다. 새 검사는 original discrete estimator에 대한 별도의 해상도 민감도/연속 영역 least-squares 비교다. 고정된 영역의 적분 극한이나 무한 harmonic tail을 두 격자만으로 인증하지 않는다.

## 2. 같은 영역을 유지하는 방법

원래 NSIDE64 binary output mask M_i를 HEALPix cell들의 합집합으로 해석한다. RING mask를 NESTED 순서로 바꾼 뒤, n/64=q에 대해 각 부모 값을 q^2개 자식 모두에 그대로 복제하고 다시 RING으로 바꾼다. 이렇게 하면 selection 면적이 정확히 같고 mask 경계가 바뀌지 않는다.

Native PMASK를 새 output NSIDE에서 다시 평균/threshold하는 방식은 사용하지 않는다. 그 방식은 영역 자체를 바꾸기 때문에 quadrature 차이와 mask 변화를 섞는다. Source native window W_N도 변하지 않는다. 저장된 window SHA와 원래 coarse-mask SHA를 기존 reader로 확인한다.

Q/U 값은 부모에서 자식으로 복제하지 않는다. 같은 저장된 spin-2 alm으로 각 output grid의 Q/U를 새로 합성한다. 따라서 서로 다른 local polarization frame의 Q/U를 스칼라처럼 평균하는 문제가 없다. Beam 재적용, deconvolution, inpainting, 새 native Q/U map2alm은 없다.

## 3. 정확한 유한 moment 항등식

고정된 cutoff L의 합성 Q/U를 f_L, low-ell design을 A_n, 선택 mask를 M_{i,n}라 하자. n은 output NSIDE이며 원래 low coefficient order와 단위 K_CMB를 유지한다. 두 Q/U row에 동일 mask를 사용한다. 각 pixel의 solid angle w_n=4 pi/(12 n^2)로

```
G_{i,n} = w_n A_n^T M_{i,n} A_n
b_{i,n,L} = w_n A_n^T M_{i,n} f_{L,n}
y_{i,n,L} = G_{i,n}^{-1} b_{i,n,L}
```

로 정의한다. 동일 n에서는 w_n이 해에서 상쇄되므로 기존 unweighted QR의 추정량과 같다. 그러나 서로 다른 n의 G,b를 비교할 때는 이 면적 정규화를 유지해야 한다.

G_n,G_m이 SPD이면 G_m y_m=b_m, G_n y_n=b_n에서 바로

```
y_m-y_n = G_m^{-1} [(b_m-b_n)-(G_m-G_n)y_n]
```

를 얻는다. 따라서

```
||y_m-y_n||_2 <= ||(b_m-b_n)-(G_m-G_n)y_n||_2 / lambda_min(G_m).
```

이것은 **이미 계산된 두 유한 격자 사이의 차이에 대한 상계**다. 미지의 continuum 오차, 물리 하늘 오차, 신뢰구간 또는 무한 tail 상계가 아니다. 구현에서 평가한 실수 상계는 floating-point 값이며 outward-rounded formal enclosure도 아니다.

Wolfram exact 예제 G0=[[2,1],[1,3]], G1=[[3,1],[1,4]], b0=(1,3), b1=(2,1)은 y0=(0,1), y1=(7/11,1/11), identity=True를 반환했다. 실제 Planck 수치가 아니다.

## 4. cutoff 변화가 격자를 바꿔도 유지되는가

D(n,L)=y_t(n,L)-y_c(n,L)라 하고, L=32,H=64, n=64,m=128을 기본 비교로 둔다.

```
Delta_L(n) = D(n,H)-D(n,L)
Delta_n(L) = D(m,L)-D(n,L)
I = Delta_L(m)-Delta_L(n) = Delta_n(H)-Delta_n(L).
```

새 출력의 `grid_cutoff_interaction`은 I의 norm과 기존 coarse-grid cutoff step norm 대비 비율을 E/B/all별로 기록한다. I가 작으면 이번 두 격자 사이에서 cutoff 증분이 비슷하다는 근거이고, 크면 cutoff 결과가 output discretization에도 민감하다는 근거다. 두 경우 모두 무한 n 또는 무한 L의 수렴을 자동으로 선언하지 않는다. 영 분모는 null이다.

기존 native input과 archived NSIDE64 vector들을 보존한다. 먼저 n=64에서 chunked moment solver와 archived QR 결과 벡터를 비교한다. 불일치하면 격자를 더 세분화하기 전에 중단한다. Norm만 비교하지 않는다. 높은 격자에서 얻은 y를 원래 추정량의 새 정답으로 자동 대체하지 않는다.

## 5. 구현과 실행된 검증

새 source `L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_fixed_region_grid_audit.py`는 기존 cutoff reader, source validator, native mask reader, Wigner low basis와 RING coordinate adapter를 재사용한다. Checkpoint의 producer 코드/의존성 SHA와 healpy 버전을 확인한 뒤 변경 없이 같은 saved alms를 쓴다. Scalar PMASK 세 파일만 다시 읽고, 이미 계산된 거대한 Q/U FITS는 다시 읽지 않는다.

Gram과 data moment를 pixel chunk별로 누적하여 거대한 전체 design/QR을 보관하지 않는다. 기본 chunk 16384 pixels, nside 64/128, 최대 허용 비교 64/128/256이다. 이 구현은 normal equations를 사용하므로 Gram condition>1e8은 거절하며 residual과 condition을 출력한다. 기존 QR 알고리즘이나 수용 기준을 바꾸지 않는다. Grids마다 G,b,y도 저장해 유한 identity를 재검산할 수 있다.

현재 샌드박스에서 **24 passed in 1.22s**, pytest exit 0, compileall exit 0, subprocess CLI --help exit 0을 확인했다. 검사에는 부모/자식 mask 영역·면적 보존, 잘못된 refinement 거절, chunked solve와 독립 np.linalg.lstsq 대조, moment identity와 bound, joint moment rescaling, 부정부호/비대칭/특이/ill-conditioned Gram 거절, NaN/shape, 저차 주입 회복, baseline vector 불일치, grid/cutoff mixed identity가 포함된다. 새 module/feature 존재 assertion의 RED 이후 구현·GREEN을 기록했다. 이것을 모든 개별 behavior가 별도의 RED를 거친 것이라고 과장하지 않는다.

추가 full-sky 제조 spin-2 control은 **같은 unit E_{6,0} field**를 유지하고 output nside만 8,16,32,64로 바꿨다. Continuum low ell2..5 projection은 orthogonality로 0이다. 실제 계산한 low leakage norm/input amplitude는

| NSIDE | leakage norm |
|---:|---:|
| 8 | 5.077146688938673e-4 |
| 16 | 1.1002771896649082e-4 |
| 32 | 2.6792044430298233e-5 |
| 64 | 6.654723972462154e-6 |

각 finite-grid moment identity 상대 잔차는 2.19e-17, 9.91e-17, 1.01e-16이었다. 이것은 실제 HEALPix RING 위치와 checked-in Wigner basis를 쓴 제조 구면 계산이다. **healpy native transform은 사용하지 않았으며 Planck grid error의 추정도 아니다.** 두 재사용 함수의 source bytes는 원격 Git blob과 같았다: spin2 `2a168e0592d3245d3bf367d515a0d11ea5637341`, coordinates `60cfc81887b0d88f5b590192062c50a2c47a0def`.

새 source/test Git blobs는 각각 `78dc850998b3b662fc8f91cbf3e53edc10f8241b`, `8fff92bc9c35cf2a76af0ba82a66017882822f5c`로 테스트한 바이트와 같다. 24개 검사와 이 제조 pilot은 native masked-map grid replay, full runner의 실제 healpy I/O 경로, 또는 전체 저장소 CI를 대체하지 않는다. 그 세 가지는 NOT_RUN이다. Native subagent도 host dispatch가 없어 NOT_RUN이다.

## 6. 지금 실행할 최소 경로

새 worktree/ZIP/다운로드 없이 현재 user-owned worktree를 갱신한다. L32/L64 checkpoint만 필요하고 L128 결과를 기다리지 않는다. 출력은 별도 파일이며 기존 summary와 source lock을 덮어쓰지 않는다.

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
python -m pytest -q "$S/tests/test_l01_fixed_region_grid_audit.py"
python "$S/src/l01_fixed_region_grid_audit.py" \
    --root "$ROOT" \
    --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
    --band-dirs "$ROOT/provenance/L01_SMICA_WINDOWED_QU_L32" "$ROOT/provenance/L01_SMICA_WINDOWED_QU_L64" \
    --nsides 64 128 \
    --out "$ROOT/provenance/L01_FIXED_REGION_GRID_$(date -u +%Y%m%dT%H%M%SZ).json"
SH
```

`baseline`은 old QR replay의 vector residual, `targets`는 같은 L에서 nside만 바꾼 변화, `interactions`의 `32_to_64_full`은 cutoff 증분이 grid refinement에 의해 얼마나 변했는지다. 같은 숫자 64/128을 사용하더라도 `cutoffs`와 `nsides`는 다른 축이다. 해시가 다르면 숫자 결과를 비교할 계약부터 확인하고 저장된 해시를 덮어써서 통과시키지 않는다.

## 7. 단계별 게시와 6개 논문 DAG

C8 이론적 검사 정의, source commit `c82860ef0036ce1e36f054b314aa585a587f3b08`, tests commit `c190f51bd94a16e6a75cd0b578bcf76185152936`, 국소검증·인계의 각 단계에서 공식 완료 수는 **14/42**다. P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7. READY L01/S02. All six NOT_READY_TO_SUBMIT. Original DAG blob `ac4a94c3da13f142eaab3b06b5275b58096c95e1`는 unchanged. 기존 native producer, source files, full/split checkpoints, canonical backlog, main을 변경하지 않았다.

이번 결과가 원래 L64 cutoff sensitivity를 폐기하지 않는다. 그 민감도가 선택한 output discretization에 얼마나 의존하는지 검사할 경로를 완성한 것이다. 실제 grid 비교 후에도 physical high-tail, joint simulation/null과 관측 유의성은 별도다.

## Primary references

- HEALPix approximate pixel-center quadrature and resolution guidance: https://healpix.sourceforge.io/doc/html/fac_anafast.htm
- Equal-area hierarchical pixel geometry: https://healpix.sourceforge.io/doc/html/intro_Geometric_Algebraic_Propert.htm
- Gorski et al., HEALPix framework, original article: https://arxiv.org/abs/astro-ph/0409513
- HEALPix conventions and sampled estimator: https://healpix.sourceforge.io/doc/html/intro_HEALPix_conventions.htm

Exa/SciSpace를 통해 원전/문서를 확인하고 Wolfram을 정확 유한 moment identity 검산에 사용했다. 검색 인덱스 날짜를 출판일로 사용하지 않았고, anafast의 bandlimited full-sky 정확도 설명을 이 masked least-squares 문제의 보편 정확도 보장으로 확대하지 않는다.
