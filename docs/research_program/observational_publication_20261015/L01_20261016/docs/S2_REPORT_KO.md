# HTT 여섯 논문 P2/L01: 실제 Planck T/E/B finite-image 검산과 spin2 mask leakage

2026-10-16 KST · 6개 논문/42노드 PUBLICATION_DAG 정본에 연결되는 논문 P2 준비 단계, 원래 소유자의 dirty checkout 변경 없음.

## 1. 실제 데이터에 근거한 성과

기존 Loop5 NPZ의 원본을 SHA-256으로 인증하고 스핀-2 64성분의 모든 메타데이터 순서와 원본 split 차이를 **독립 재생**했다.

| 실제 source | 실수 low-ell 계수 | NSIDE64 공통 mask 픽셀 | source 해석 |
|---|---:|---:|---|
| Temperature: SMICA HM/OE, NILC HM, full/noSZ | 각 32 (\ell=2–5) | 26,846 / 49,152 | 동일 한 하늘의 9개 처리본 |
| Q/U → joint E/B: SMICA HM/OE, NILC HM, full | 각 64 (\ell=2–5) | 30,021 / 49,152 | 동일 한 하늘의 8개 처리본 |
| SMICA noSZ full polarization | 제공되지 않음 | 해당 없음 | `UNKNOWN/NOT_DELIVERED`, 0으로 채우지 않음 |

주의: 위 표에서 `\ell` 표기는 고정된 multipole index \(\ell\)을 의미한다. 배열의 실수 spin order는 각 \(\ell\)마다 \(E_{m0},E_{m1c},E_{m1s},\ldots,B_{m0},\ldots\)이다.

실제 E/B 계수 처리 차이 (단위 µK, 물리적 CMB 분산 추정 아님):

| 같은 하늘 대비 | E 32계수 노름 | B 32계수 노름 | 결합 64계수 노름 |
|---|---:|---:|---:|
| SMICA HM half difference | 0.365530 | 0.228889 | 0.431280 |
| SMICA OE half difference | 0.258912 | 0.229318 | 0.345864 |
| SMICA HM mean – OE mean | 0.081408 | 0.121014 | 0.145848 |
| NILC HM mean – SMICA HM mean | 0.319908 | 0.664335 | 0.737348 |
| SMICA full – SMICA HM mean | 0.480429 | 0.343808 | 0.590775 |

동일 물리 하늘의 8개 편광 처리 행렬(8×64)의 행평균 제거 후 rank는 **7**이었다. 이는 처리 차이 차원이지 7개의 독립한 CMB 실현을 뜻하지 않는다. FFP10의 자료는 6개 처리 × 300개 같은 latent sky로 분류했으며 독립 실현 수를 1,800개로 늘리지 않았다.

SMICA full만의 \(\ell=2\) 유한 투영계수는 \(C_2^{EE,fit}=0.0881122\), \(C_2^{BB,fit}=0.0956766\), \(C_2^{EB,fit}=-0.0441829\) µK²다. 이 수치는 **cut-sky truncated joint-Q/U LS sample-image**이며 physical EE/BB/EB power-spectrum estimator 또는 parity-violation test가 아니다. 독립 noise law와 high-spin tail 통제가 없다.

동일 온도 mask의 실제 \(\ell=6–32\) 높은 harmonic 누출행렬 \(K_T\in\mathbb R^{32\times1053}\) 연산자 노름은 **2.4328695605629203**. 이는 실제 source-mask geometry의 finite-block 계산이다. \(\ell>32\) 온도 잔여, 실제 하늘 고차 계수 norm, 빔/성분분리 유효전달은 여전히 UNKNOWN.

## 2. 샌드박스가 새로 검증한 spin-2 누출 기작

완전 구면 대신 768개 Fibonacci 각도 중 700개를 선택한 순수 **manufactured spin-2 Q/U 하늘**을 구성했다. 낮은 \(\ell=2–5\) 64실수모드와 고차 \(\ell=6–8\) 90모드를 사용한다. 이는 HEALPix NSIDE64 source mask가 아니며, Planck 수치가 아니다.

| manufactured 선택 | \(\kappa(S_L)\) | \(\|K_{L,H}\|_2\) | \(\|K_{B\leftarrow E}\|_2\) |
|---|---:|---:|---:|
| 모든 768개 점 | 1.00204 | 0.004703 | 0.002523 |
| 높은 z값 700개 | 4.12592 | 3.053247 | 1.529809 |
| 높은 x값 700개 | 4.12678 | 3.060389 | 1.553707 |

두 700-점 mask의 행렬 자체 Frobenius 거리 \(\|K_z-K_x\|_F=7.04322\)이다. 따라서 **같은 공통-mask 픽셀 개수는 동일한 E/B 응답행렬을 보장하지 않는다**. 코드가 진짜 spin-2 Wigner-d를 사용한 기저를 만들고 Q/U를 결합한다는 사실은 파라미터 수, colatitude, parity, 무차원 조화함수와 고정 spin-frame에서 검증했다. 다만 healpy native real `alm2map_spin` 정의와의 각 원소 byte/numerical identity를 독립 재현한 것은 아니다.

고차 spin하늘 \(h\neq0\)에 대해 \(S_Hh-S_LK_{LH}h\)를 구성하면 동일한 선형 OLS 저차 fitting 결과에 아무 변화가 없음을 합성 주입으로 확인했다. 이는 유한 계수의 low-ell projection이 unmodelled spin2 high modes를 결정하지 못한다는 **정확한 선형대수 반례**이며, 실제 외부 관측의 전역 no-go가 아니다.

## 3. 과학적 판정 및 논문 DAG

- P2/L01의 **유한 온도 source-response, 실제 유한 편광 계수, scalar/spin mask source 선택 계약, spin-2 parity와 finite truncation underdetermination**은 `COMPLETED_SCOPED_PREPHYSICAL_SUBRESULT`.
- 반면 full actual POL mask pixel operator \(A_P\)와 high-mode \(S_H\)를 실제 source on-disk mask에서 결합하지 못했다. source-geometry \(K^P_{LH}\)도 실제 데이터가 아닌 synthetic에서만 검산했다. beam/compsep/foreground/E2E/source-selected split covariance도 없다.
- 따라서 **정본 DAG `P2/L01` 상태 `pending`을 유지**하고 `existing_evidence`와 `next_action`만 신규 source-bound 단계 진척으로 덧붙인다. `L02`는 X03도 필요해 여전히 waiting, `L03`은 X01 및 released matched E2E null 입력 부족으로 blocked.
- P2의 null/multiple-choice inference, physical lowE/BB likelihood, parity violation, primordial B, geometry/Bianchi inference나 신규 anomaly p-value는 **모두 NOT_ADMITTED**. 6개 논문 모두 `NOT_READY_TO_SUBMIT` 유지한다.

## 4. 검증 범위 및 다음 로컬 실행

Source SHA 4개 입력 고정, 원본 Loop5와 Loop9 JSON SHA 고정. 샌드박스 **17 tests PASS**, 원본과 동일한 E/B split의 5개 값 검산, SciPy spherical harmonic 독립 scalar limit, parity, masked QR-vs-SVD and direct independent least-squares, 같은 선택수의 다른 mask 반례, high-mode projection null fibre, local reproducibility fixture. **신선한 native 독립 reviewer NOT_RUN**.

다음 로컬 작업은 `src/run_local_replay.py`로 이미 존재하는 소스들을 SHA 검사하여 S2 결과 재생하고, Loop5 `htt_multisplit_lowell.spin2_design_real` 및 원본 Planck Pol mask를 **실제로** 사용해 \(\ell=6\ldots8\) source-specific spin2 \(K^P_{LH}\)를 계산하는 것이다. 올바른 native healpy E/B convention 수치교차검산 없이는 이번 합성 코드의 국소 spin convention을 Planck와 같다고 선언하지 마라. 저장할 정보: low spin 64x90 K, E←B/B←E 블록, mask source SHA, cut-sky injection, exact source T/Pol mask identity, beam/E2E unknown warning. 결괏값 없으면 `pending`과 `NOT_RUN` 유지.

주요 원전: [Planck 2018 IV](https://doi.org/10.1051/0004-6361/201833881), [Planck 2018 VII](https://doi.org/10.1051/0004-6361/201935201), [Hivon et al. MASTER](https://doi.org/10.1086/338126). 기존 기법과 견준 완전한 X02 novelty comparator는 이번 L01에서 수행하지 않았다.
