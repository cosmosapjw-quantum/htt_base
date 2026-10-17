# L01: 원본 SMICA Q/U의 공통-window 유한 대역 분해

2026-10-17 Asia/Seoul. Parent `4f32e21852e4672613b7cca07acdf45f15023d3e`, Draft PR #559. Active publication node L01. 이번 작업은 기존 입력복구 루프를 반복하지 않고 R5 구성적 계산과 C5 구현, 그 산출물의 C6 국소검증을 수행하는 하나의 bounded work unit이다. 원래 42-node publication DAG와 READY는 변경하지 않는다.

## 1. 복구 종료 근거와 범위

사용자 native stdout에서 다음을 확인했다. 이는 사용자 보고 실행 근거이며 이 세션의 원본 FITS 직접 실행이 아니다.

- 정확한 parent HEAD에서 `PASS_EXACT_HEAD_CLEAN_IMPORTS`.
- `L01_R8_C8_TWO_MASK_STABILITY_20261017/tests`에서 **41 passed in 2.54s**. 앞서 재구성 환경의 80-test 언급과 동일한 collection이 아니다. 현 로컬 기준 수치는 41이다.
- HM1/HM2/OE1/OE2 각 603,990,720 bytes, 기존 SHA 유지, `EXISTING_REUSED`, `COMPLETE_DECLARED_HDU_STRUCTURE`.
- full 2,013,312,960 bytes, SHA256 `60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac`, `DOWNLOADED_FITS_FRAMING_VALID`, 전체 HDU 구조 검증 완료.
- 사라진 `/mnt/sn850x2t/htt_base_e2e/lean-shared/htt-lean-shared.py`는 별개 checkout-hook/helper 문제다. 이번 Python 점검과 테스트는 이후 정상 종료했다. 이 작업에서 Lean 설치·hook·Git 전역 설정을 변경하지 않는다.

따라서 source intake와 import recovery는 사용자 실행 범위에서 닫고 실제 Q/U 데이터 처리 경로로 이동한다. 다운로드를 재요청하지 않는다.

## 2. 정의와 컨벤션

각 product s에 대해 공개 `Q_STOKES,U_STOKES`를 p_s=(Q_s,U_s)로 둔다. 단위는 K_CMB, 원본은 NSIDE2048 NESTED Galactic, POLCCONV=COSMO다. `_INP` 열을 선택하지 않고 I_STOKES도 이 spin-2 분석에는 사용하지 않는다.

세 개의 기존 source-pinned native PMASK 각각을 0.5에서 strict threshold한 교집합을 W_N으로 고정한다. 이 **동일한** W_N을 full/HM1/HM2/OE1/OE2 모두에 적용한다. W_N 밖은 명시적으로 0, 안의 nonfinite/BAD_DATA는 오류다. product마다 유효 화소를 조용히 삭제하지 않는다.

T_L은 native RING 지도에 대한 `healpy.map2alm_spin(...,spin=2,lmax=L,mmax=L)`의 유한 quadrature transform이다. S_J^64는 대역 J의 계수를 NSIDE64 RING Q/U로 합성하는 `alm2map_spin` 연산이다. 여기서는 정확한 continuum inverse나 true-sky reconstruction이라고 주장하지 않는다.

```
a_tilde_s = T_L W_N p_s
p_filtered_s = S_[2:L]^64 a_tilde_s
```

`a_tilde`는 **공통 window를 곱한 전달된 지도의 pseudo E/B 계수**다. foreground/noise/beam과 W_N의 E/B mixing을 포함한다. cosmic E/B 또는 physical high-ell coefficient와 동일시하지 않는다.

기존 coarse output support M_c,M_t는 변경하지 않는다. 각 native mask를 NSIDE64로 평균한 뒤 threshold하고 binary intersection하는 이전 정책과 exact RING64 mask SHA를 재확인한다. 이는 W_N을 만든 뒤 downgrade한 mask와 일반적으로 다르며, 두 정책을 구분해 기록한다.

## 3. 정확한 유한 대역 항등식

L0=S_[2:5]^64, H0=S_[6:8]^64라 하자. 두 coarse mask에 대해

```
P_i = (L0^T M_i L0)^(-1) L0^T M_i
K_i = P_i H0,   i=c,t
```

이며 L0의 selected-row rank가 full이라고 가정한다. 기존 K_i(64 x 90)는 새로 생성하지 않고 source-pinned NPZ를 재사용한다. 선형성과 P_i L0=I에서

```
y_i,s = P_i p_filtered_s
      = a_tilde_s,[2:5]
        + K_i a_tilde_s,[6:8]
        + P_i S_[9:L]^64 a_tilde_s,[9:L].
```

마지막 항을 r_i,s^(9:L)로 정의하면

```
y_t,s - y_c,s = (K_t-K_c) a_tilde_s,[6:8]
                + (r_t,s^(9:L)-r_c,s^(9:L)).
```

이는 동일 window, 동일 harmonic convention 및 동일 필터 L에서 정확한 대수 항등식이다. 데이터에 따라 두 대역 기여는 보강되거나 상쇄될 수 있으므로 norm을 더해 실제 차이라고 표시하지 않는다. 전체 벡터와 각 대역 벡터를 모두 저장한다.

계수 배열은 기존과 동일하게 ell별 E(m0,cos1,sin1,...), B(...)이며 m>0에서 a_lm=(c_cos-i c_sin)/sqrt(2)다. stored K times packed coefficient와 **별도 mid-band map synthesis 후 projection**을 대조한다. 이 검사는 단순히 같은 벡터를 더하는 closure보다 강한 convention 검산이다.

Wolfram의 정확 유리수 제조 예제에서 P L0=I, projected total=(8/3,29/3), tail contribution=(7/3,28/3), band-sum identity=True를 확인했다. 이는 실제 Planck 수치가 아니다.

## 4. 수치·물리 해석 제한

1. 이 구현의 기본 L=32이고 16,32,64,128을 지원한다. 계산된 9..L 대역 항은 처음으로 실제 processed-map 값으로 평가할 수 있지만 **ell>L tail bound가 아니다**. L 확대 결과가 비슷해도 continuum 또는 infinite-tail convergence를 자동 선언하지 않는다.
2. Q/U를 단순 `ud_grade`로 평균하지 않는다. 그 함수는 mask coverage에는 재사용하되 Q/U는 spin-2 transform/synthesis 경로를 쓴다. 원본 해상도에서 native window를 적용하므로 sharp mask의 Gibbs/mixing 효과도 처리법의 일부다.
3. 전달된 Q/U에는 이미 instrument/component-separation response가 들어 있다. 여기에 POL_BEAM을 다시 곱하면 double-beam이 된다. 본 데이터 경로는 beam을 다시 적용하거나 deconvolve하지 않는다. 기존 `l01_r9c9_same_sky_beam.py --smica-full`은 별도의 조건부 diagonal-beam **기하 연산자** 계산으로 그대로 사용한다. W_N과 beam이 일반적으로 가환한다고 가정하지 않는다.
4. HM/OE half-difference는 (a_1-a_2)/2로 만들고 동일 projector를 쓴다. 이 선형 차이가 자동으로 pure noise가 되거나 HM/OE가 독립 표본이 되는 것은 아니다. source-matched FFP10, 실제 split response, foreground/systematics와 공동 공분산은 여전히 L03의 문제다.
5. closure 오차는 K_CMB 스케일에 상대적으로 검사한다. 두 mask의 거의 같은 low-mode를 뺄 때 분모를 작은 차이만으로 정하면 roundoff를 물리적 tail로 잘못 판정할 수 있어, 차이 closure는 원래 두 output의 크기도 roundoff reference로 사용한다. 이 기준은 physical uncertainty나 formal error enclosure가 아니다.

## 5. 코드 재사용과 실행 상태

새 코드 `L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_smica_processed_bands.py`는 기존 import bridge, FITS structural checker, native PMASK reader, packed E/B convention, low spin-2 design, original K verifier를 직접 import한다. 기존 코드나 source hashes를 덮어쓰지 않는다. 저차 QR을 두 mask별로 한 번만 구성하고 각 product와 대역에 재사용한다. 거대한 high-l design matrix를 저장하지 않고 실제 계수 벡터를 직접 합성한다.

원본 full/split FITS는 읽기 전용 memmap으로 접근하고 한 번에 한 product를 처리한다. product별 pseudo-alm NPZ와 band JSON을 checkpoint한다. 재개 시 source SHA, native window SHA, L, 코드·dependency SHA, healpy version, NPZ 바이트를 확인하고 불일치 시 별도 output 위치를 요구한다. 결과는 관측 amplitude를 담지만 p-value는 만들지 않는다.

현재 이 세션의 native full 2GB FITS, 원본 K NPZ, healpy SHT 실행은 NOT_RUN이다. NumPy/SciPy를 이용한 국소 구현 검증과 실제 Git blob으로 확인한 dependency 사용을 구분해서 기록한다. Native subagent dispatch는 제공되지 않아 NOT_RUN이며 별도 reviewer를 가장하지 않는다.

## 6. 출처

- Planck 2018 IV, primary component-separation and data limitations: https://arxiv.org/abs/1807.06208
- Planck 2018 VII, matched simulations and large-scale polarization: https://arxiv.org/abs/1906.02552
- Official full SMICA header, Q/U units/convention/beam: https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/previews/COM_CMB_IQU-smica_2048_R3.00_full/header.txt
- healpy map2alm_spin contract: https://healpy.readthedocs.io/en/stable/generated/healpy.sphtfunc.map2alm_spin.html
- healpy alm2map_spin RING synthesis: https://healpy.readthedocs.io/en/stable/generated/healpy.sphtfunc.alm2map_spin.html
- ud_grade averaging and power-spectrum warning: https://healpy.readthedocs.io/en/stable/generated/healpy.pixelfunc.ud_grade.html

R5 publication boundary: formal 6-paper DAG remains 14/42 (P1 1/6; P2 0/6; P3 2/6; P4 1/6; P5 1/5; P6 2/6; COMMON 7/7), READY L01/S02; all six NOT_READY_TO_SUBMIT. This work adds L01 progress without certifying L03 or replacing a physical likelihood.
