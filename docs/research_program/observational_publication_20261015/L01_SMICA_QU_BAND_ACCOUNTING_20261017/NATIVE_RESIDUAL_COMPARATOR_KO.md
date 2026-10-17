# L01: L128 및 격자 결과 판정, native-pixel 잔차 비교

2026-10-17 Asia/Seoul. Parent HEAD `a46c1530b24b78752863ba59f599ae89f7ca2fc4`, 기존 Draft PR #559. 이번 bounded scope는 R8의 새 실측 실행 결과 해석과 C8의 cutoff 문제에 대한 직접 native-pixel 비교 경로다. 자동 L256 확대나 새 전체 연구 루프가 아니다. 기존 추정량과 모든 checkpoint를 보존한다.

## 1. 실제로 확보된 결과

근거: 사용자 첨부 `Pasted text(20261017-131244).txt`, SHA256 `6c5e0646f3b8ce253fb81b2ab4928595a0fb416eabf89881741f8426e6ecdbd3`. 이 세션에서 원본 Planck 데이터를 재실행한 결과가 아니다.

L128 full/HM1/HM2/OE1/OE2는 모두 대역 closure를 통과했고, 32/64/128 target geometry 및 64/128 출력 격자 비교가 보고됐다. L32->64와 L64->128의 full 목표량 상대 증분은 0.1858741373, 0.1614656525다. 두 번째 증분의 E/B 계수 에너지 비는 각각 1.2496739366, 1.2076147092, 전체는 1.2263208960이다. B 증분의 연속 norm 비는 0.9896704502로 거의 감소하지 않았다. 두 증분의 B 정렬도는 -0.3793822701이다. 작은 norm 변화와 방향 변화는 별도이며, 전체 계수공간 각도는 32->64에서 10.7071289도, 64->128에서 6.56837462도다. 이 각도는 하늘 회전이나 편광 회전각이 아니다.

NSIDE64->128에서 full 목표량 변화는 고정 L32에서 0.00198436585, 고정 L64에서 0.00400428304다. Cutoff 증분에 대한 grid/cutoff interaction norm 비는 all 0.01983921482, E 0.01901951728, B 0.02094563830이다. 이는 두 격자 사이의 차이이지 연속극한 오차의 상계가 아니다.

### 이 국소 격자 질문은 닫을 수 있다

Coarse 격자의 x=D(64,32), e=D(64,64)-D(64,32)와, fine 격자의 x'=x+g, e'=e+i를 쓰면

```
(||e||-||i||)/(||x||+||g||) <= ||e'||/||x'||
||e'||/||x'|| <= (||e||+||i||)/(||x||-||g||)
```

가 성립한다. 이번 수치에서는 모든 분모와 아래쪽 분자가 양수다. 첨부 scalar로 직접 계산한 fine 격자 상대 cutoff 변화의 허용범위는 all [0.1818257315,0.1899386420], E [0.2080012796,0.2168807427], B [0.1573485316,0.1647603136]이다. 따라서 *이 두 격자 사이에서* 앞선 cutoff 민감도를 grid step만으로 지울 수 없다. 이 판단을 무한 해상도/무한 대역 또는 물리적 유의성으로 확대하지 않는다.

## 2. 다음 계산의 선택

L256을 자동으로 추가하는 대신, 원래 source window W를 적용한 전달 지도 f=W x를 native NSIDE2048에서 직접 낮은 기저에 투영한다. 동일 native 격자에서 저장된 L128 pseudo-alm을 한 번 역변환한 f_L과 비교한다. 이 경로에는 새 map2alm, 데이터 다운로드, beam 재적용, inpainting 또는 분할 잡음의 독립성 가정이 없다.

중요한 구분:

- W는 원래 세 native PMASK의 교집합으로, 데이터 f에 한 번 적용한다.
- M_c, M_t는 기존 NSIDE64 common 및 three-way 선택 픽셀들의 합집합 영역이다. Native NESTED 자식은 부모의 M 값을 그대로 상속한다. M_t<=M_c.
- Gram에는 M만 적용한다. W를 Gram에 추가로 곱해 선택 영역을 몰래 바꾸지 않는다.
- f_L=S_L a_tilde를 합성한 다음 W를 다시 곱하지 않는다. 재합성은 이미 W x에서 얻은 계수로부터 이루어진다.
- 낮은 기저는 ell2..5의 기존 64개 real E/B 계수다. 직접 RHS는 모든 native pixel 값을 읽으며 입력 f를 사전 harmonic cutoff하지 않는다. 따라서 64개 fit coefficients를 출력한다는 사실은 입력의 높은 모드가 없다는 가정이 아니다.

이것은 **새 native-pixel 비교 추정량**이다. 기존 NSIDE64 추정량을 바꾸거나 그 해시를 교체하지 않는다. Direct input projection은 finite delivered-map target이며 cosmic E/B를 복원하는 추정량으로 인증하지 않는다.

## 3. 정확한 finite-pixel 정리와 유도

각 공간 화소의 solid angle omega=4pi/Npix를 두 Q/U 행에도 동일하게 적용한다. A는 native 중심에서 평가한 저차 design이며 M_i는 두 성분에 동일하게 적용하는 binary diagonal matrix다. Gram이 가역적이라 가정한다.

```
G_i = omega A^T M_i A
y_i(f) = G_i^-1 omega A^T M_i f
z = sqrt(omega) f
P_i = G_i^-1 sqrt(omega) A^T M_i
y_i=P_i z; D=P_t-P_c.
```

M_i^2=M_i, M_t M_c=M_t를 사용하면

```
P_i P_i^T = G_i^-1
P_t P_c^T = G_t^-1 (omega A^T M_t A) G_c^-1 = G_c^-1
P_c P_t^T = G_c^-1
D D^T = G_t^-1-G_c^-1.
```

따라서 H=G_t^-1-G_c^-1은 positive semidefinite이고, 거대한 pixel-domain operator를 만들지 않고 64x64 행렬로 그 norm을 계산할 수 있다. 계수 부분집합을 선택하는 행렬 R_X에 대해

```
kappa_X^2 = lambda_max(R_X H R_X^T)
||R_X D z|| <= kappa_X ||M_c z||.
```

이는 임의의 common-region 입력에 대한 sharp operator norm이다. 최대 특이벡터 입력이 상계를 포화한다. Actual raw-minus-reconstruction residual r=f-f_L을 쓰면

```
d_direct-d_L_native = D sqrt(omega) r
||R_X(d_direct-d_L_native)|| <= kappa_X sqrt(omega sum_{p in common}(r_Q,p^2+r_U,p^2)).
```

좌변은 두 moment 해의 차이뿐 아니라 r 자체의 moment를 별도로 누적하여 대조한다. 우변에 사용되는 residual norm도 전체 native pixel을 stream하며 계산한다. 이는 실제 residual map에 대한 finite-dimensional bound이지 관측하지 않은 cosmic high-ell tail의 상계가 아니다. r에는 band truncation 외에도 native analysis/synthesis의 quadrature 차이가 포함될 수 있다.

Wolfram의 exact rational 예제에서 H={{25/51,-20/51},{-20/51,16/51}}, 고유값 {41/51,0}, D D^T-H=0, D A=0을 얻었다. 앞선 sqrt(1/3) 표현 평가에서는 Wolfram 메시지가 발생했으므로 최종 재검산은 omega=1의 유리수 예제로 기록한다. 이는 동일 항등식의 검산이며 관측 Planck 수치가 아니다.

수치 구현은 float64 행렬 고유값을 사용하므로 방향 반올림을 갖춘 verified interval bound라고 주장하지 않는다. 작은 antisymmetric/negative-eigenvalue roundoff를 분리해 기록하고, 큰 위반은 거절한다. Gram condition 제한은 기존 격자 진단기의 1e8을 유지한다.

## 4. 기존 결과와 새 비교량의 연결

같은 L을 써서

```
d_direct_native - d_archived_64(L)
 = [d_direct_native - d_native(L)]
 + [d_native(L) - d_archived_64(L)].
```

첫 항은 같은 native 격자에서 실제 f와 재합성 f_L의 차이다. 두 번째는 같은 f_L에 대한 출력 격자 변경이다. 새 JSON은 세 벡터를 별도 필드로 저장한다. 두 항의 합을 순수 spectral-tail error로 부르지 않는다.

연속극한, 미측정된 물리적 source, noise debiasing, foreground 모델, matched FFP10 null은 여전히 미검증이다. 새 경로는 그 문제를 푼 척하는 대신 현재 제공된 finite pixel data에 대해 harmonic L 외삽 없이 계산 가능한 비교량을 만든 것이다.

## 5. 구현·검증 상태

`src/l01_native_residual_projection.py`는 기존 `l01_fixed_region_grid_audit.Moments/solve`, 기존 source/PMASK/checkpoint 검증, 기존 low design, source FITS header reader와 JSON writer를 재사용한다. 기존 모듈은 수정하지 않았다. 기본 product는 full 하나다. 다른 네 분할도 같은 --product 선택으로 따로 계산할 수 있지만 자동 batch sweep을 하지 않는다.

저장된 L128 계수를 native 격자로 한 번 합성한다. 그 다음 strided NESTED FITS Q/U를 chunk 8192개씩 읽어 raw, reconstructed, residual의 세 RHS를 함께 누적한다. Gram 두 개는 각 chunk에서 한 번씩 계산한다. Native source의 stat와 source SHA, 고정 영역 면적, nesting, 입력 window, checkpoint code identity를 확인한다. 원본이나 checkpoint를 덮어쓰지 않는다. Native basis 전체를 Npix x 64로 저장하지 않는다.

이번 실제 검사: **27 passed in 0.85s**, compileall 성공, standalone --help 성공. Python 3.13.5, NumPy 2.3.5. 새 수치 커널은 직접 만든 pixel operator의 SVD와 독립 비교, sharpness witness, 같은 영역의 zero gain, 잘못된 Gram/입력, W 재적용 금지, low-design injection, zero residual, 1..1e-100 진폭 스케일, 계수 부분집합 gain, 덮어쓰기 금지를 검사했다. 모듈 존재 RED를 구현 전에 관측했으나 모든 테스트별 개별 RED를 주장하지 않는다.

Native `run()` 전체의 FITS/healpy 실행과 실제 Planck 값, 전체 저장소 CI는 **NOT_RUN**이다. 이 샌드박스에는 healpy/astropy가 없다. 테스트 통과를 native producer나 science gate의 통과로 확대하지 않는다. Native subagent는 현 도구에 dispatch가 없어 NOT_RUN이며, serial 작업만 수행했다.

Source commit `e75e8ab71d10fb7a297c1a06bc602d2135afcd24`, test commit `2add66924a332b2ae9110156079525424ac590ac`.
Source SHA256 `4259df97ce6aeed6a0a1653ef62438604f27f7de045f067fc510e608c09d2209`, Git blob `14621d017c2c221701699873cece8659cbdd5b21`.
Test SHA256 `cbd7476e7dfda8a3b0420aacaa01d55035c21d7d18a95326d79730f445569edc`, Git blob `90ef357a42b3600c06d92ee61b2f275d01c5a4b3`.
원격 blob과 테스트한 local bytes가 일치한다.

## 6. 같은 worktree에서 실행

L32/L64/L128의 forward SHT는 다시 하지 않는다. 기존 완료된 L128 checkpoint와 full FITS를 사용한다. 새로운 결과 이름을 만들며 기존 로컬 변경사항이 있으면 중단한다.

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
python -m pytest -q "$S/tests/test_l01_native_residual_projection.py"
OUT="$ROOT/provenance/L01_NATIVE_PIXEL_RESIDUAL_full_$(date -u +%Y%m%dT%H%M%SZ).json"
python "$S/src/l01_native_residual_projection.py" \
 --root "$ROOT" \
 --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
 --band-dir "$ROOT/provenance/L01_SMICA_WINDOWED_QU_L128" \
 --product full --chunk-pixels 8192 --out "$OUT"
SH
```

`components.all/E/B`의 direct norm, reconstructed norm, measured residual norm 및 finite residual-map norm bound를 확인한다. 재현된 residual identity가 통과해야 PASS다. Bound는 매우 느슨할 수 있으므로 실제 측정된 residual norm과 분리해서 읽는다. 출력 `relative_residual_to_direct`는 이 native comparison target에 대한 상대값이며 기존 18.59%의 분모와 다르다.

## 7. 단계별 DAG와 출처

R8 새 결과 판정, C8 native 비교 구현, 국소검증/게시의 각 단계 후 canonical publication DAG는 **14/42**를 유지한다. P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7. READY L01/S02, six papers NOT_READY_TO_SUBMIT. Canonical DAG와 245-card backlog, main은 변경하지 않는다. 기존 관측량을 바꿔 L01 완료를 우회하지 않는다.

원전 확인:
- HEALPix approximate quadrature and bandlimit caveats: https://healpix.sourceforge.io/doc/html/fac_anafast.htm
- Mask discontinuities and harmonic leakage: Kim, A&A 531 A32 (2011), https://arxiv.org/abs/1010.2636
- Pixel-domain EB leakage correction is a separate qualified method, not our low-fit comparator: Liu et al., PRD 100 023538 (2019), https://arxiv.org/abs/1811.04691
- Planck 2018 IV source processing/noise: https://arxiv.org/abs/1807.06208

문헌은 Exa/SciSpace로 탐색한 뒤 원 arXiv/공식 HEALPix 페이지로 대조했다. 위 finite linear-algebra 항등식은 직접 유도이며 문헌적 신규성이나 새로운 no-go 정리로 주장하지 않는다.
