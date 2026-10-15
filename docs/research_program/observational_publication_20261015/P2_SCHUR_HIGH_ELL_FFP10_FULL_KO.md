# HTT P2 L01: 실제 Planck 마스크의 고다중극 Schur 응답과 전체 FFP10

2026-10-15 KST. 부모 commit 5fbc0fbbe850c14620363b709f6e62962c3f147c. 실제 과학 입력은 하나의 Planck PR3 SMICA K1 temperature sky, source-verified 999 FFP10 CMB-only, 300 FFP10 noise-only이다. CMB+noise 300개는 같은 ID를 한 번씩 짝지었으며 제3의 독립 모의집합이 아니다. 26846 NSIDE64 RING T mask 픽셀, original NSIDE2048 NESTED Planck common/HM/OE의 검증된 교집합만 사용한다. 원본 소스 체크섬 86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb. 동일 하늘의 나머지 9개 Planck 처리 제품도 서로 독립 cosmological sky가 아니다.

## 1. 실제 구성적 이론: 고다중극 nuisance 제거

온도 real Ylm l0..5는 36개, l6..12는 133개 모드를 유지한다. 선택된 관측창에서 G=X_M^T X_M를 블록 분할하면 restricted low-only 적합과 joint low+high 적합은 다음 정확한 항등식을 만족한다.

GLL(a_L_restricted-a_L_joint)=GLH a_H_joint
a_L_restricted-a_L_joint=(GLL^-1 GLH) a_H_joint.

고차 nuisance를 profile한 저차 Gram은 S=GLL-GLH GHH^-1 GHL. 이는 가정된 mask와 유한 조화기저의 선형대수적 결과다. Wolfram exact block case 항등식=0, 독립적인 Schur solver 및 native source injection 테스트 검증. Gaussian CMB 물리 likelihood나 ell>=13 sky 상한은 아니다.

실제 selected sky Gram의 full design condition 24.44251178, Schur/GLL 일반화 정보 고유값 min **0.022328226**, median **0.653179274**, max **0.998186531**. 이 수치는 전체 Planck cosmological Fisher 정보의 보존율이 아니라, uniform masked OLS의 36D 저차 Gram에 대한 source-conditional nuisance 정보 비율이다. l6..12 -> fitted l2/3 masked leakage operator 2-norm **1.658653009**.

## 2. 실제 Planck SMICA의 형태 변화와 전체 source 코호트

Legacy Teff 원문 방향 온도 모멘트 F4와 현대 O(3) 정규화 왜도 s3, 첨도 k4는 동일한 l2/3(5+7) Planck harmonic의 함수다. Legacy filling F, signed Gauss x, Q, Pi, G_F와 다르며 추가 likelihood가 아니다. 실제 하나의 observed SMICA K1 source에서 simultaneous fit ellmax:

| ellmax | s3 | k4 |
|---|---:|---:|
| 5 | -0.1015251124 | 3.1595082720 |
| 8 | 0.0840567851 | 3.0786767081 |
| 10 | 0.1628644897 | 3.1782870419 |
| 12 | 0.4127413464 | 3.4062327211 |

observed lmax12 minus5: s3=**+0.5142664588**, k4=**+0.2467244492**. 이는 동일 지도에서 nuisance 정의를 바꾼 추정량 차이이며 실제 intrinsic non-Gaussian CMB 검출이 아니다.

999 CMB-only, 300 noise-only, 300 same-ID paired CMB+noise에서 lmax12 minus5의 RMS source shift:

| source | RMS s3 shift | RMS k4 shift | median 12D real coefficient movement [microK] |
|---|---:|---:|---:|
| CMB-only 999 | .2772466244 | .3357400491 | 53.60666 |
| noise-only 300 | .4005024550 | .3648559109 | .79974 |
| CMB+noise 300 | .2989018430 | .3342367194 | 53.15685 |

모의군에서 실제 SMICA의 |shift| 이상 사례 수(사후 선택한 탐색적 기술통계): s3 74/999 CMB, 74/300 noise, 32/300 paired. k4 442/999 CMB, 141/300 noise, 130/300 paired. **이들은 Planck p-value가 아니다.** 통계량과 lmax를 이미 실제 하늘을 보고 정했고, end-to-end component-separated foreground/beam/noise 교환가능성 및 전체 trials family는 검증되지 않았다.

Schur identity relative max residual: 관측 source 4.0676e-16, CMB999 3.3101e-15, noise300 2.22045e-15. 이전 실제 SMICA source eps2/3 및 먼저 실행했던 48 FFP10 lmax5→12 source 차이도 동일 입력에서 직접 재현했다.

## 3. beam source 정책

Planck Collaboration IV (2020) doi:10.1051/0004-6361/201833881는 SMICA/NILC/Commander의 서로 다른 component-separation source, 추가 smoothing 및 native pixel-window 처리와 복잡한 source noise를 기술한다. 이번 연구는 실험적 비교를 위해 nominal 5 arcmin Gaussian beam과 HEALPix nside64 pixel window의 isotropic 곱만 선언한다. 이는 released SMICA native effective transfer, irregular masked nested downsampling 또는 physical deconvolution이 아니다.

At ell12, B_ell Gaussian=0.999970245, P_ell(64)=0.998226603, product=0.998196901. Nominal transfer 기여를 algebraic K operator에 반영할 때 l6..12→l2/3 operator norm은 1.658653009에서 **1.657595260**으로 -0.064% 변화한다. 따라서 이 유한 계산에서는 nominal beam 시나리오 변화보다 mask/high-l nuisance 선택이 더 큰 민감도의 원인이다. 이 진술은 unknown ell>=13 및 실제 source beam/systematic으로 확장하지 않는다.

## 4. 독립 CF4 및 여섯 논문 연구 DAG

P3 독립 실제 CF4 35,970 group redshift-dependent Hubble source baseline은 기존 H02 결과에서 보존한다: observed far-near logH=-0.0727872412, flat-LCDM isotropic source response=-0.0455738112, residual=-0.0272134300. 동일 Planck 데이터를 추가 독립 joint likelihood로 중복 사용하거나 physical beta/shear, x,Q,Pi를 추정했다고 주장하지 않는다. P4 V01 exact event-local boost 계약은 보존하지만 V02 physical global-tilt discrimination에는 source-qualified L01과 global-tilt history transport가 필요하다.

이 결과는 P2 L01의 실제 소스 및 수치해석 근거를 전진시키지만, release-qualified polarization E/B, beam, foreground, higher-mode ell>=13, all-trial end-to-end Planck null이 없어 해당 노드를 계속 PENDING으로 둔다. 기존 L03 external blocked, V02 waiting. 전체 완료 진행률 **9/42=21.43%**, ready6, externally blocked7, waiting20, 여섯 논문 manuscript gate **0/6**.

## 5. 파일·검증·재현

Production code: htt/obsstat/masked_schur_highl_temperature.py. Executable: scripts/run_htt_schur_highl_ffp10_full.py. Tests: tests/obsstat/test_masked_schur_highl_temperature.py, tests/obsstat/test_htt_l01_schur_ffp10_source.py. Canonical source result: results/L01_schur_999cmb_300noise_v2/ (result.json, source_lowell_nested_999plus300.npz, masked morphology plot, short Korean result). Source FFP10 original raw bank은 read-only; v1 & 48+12 smoke create-only receipts retained. v2 checks same source realization ID pairing, exact legacy morphology movement and no-physical-null flags. v1/v2 scientific outputs identical after excluding runtime and v2-specific pairing/descriptive rank fields.

Local measured runtime v1 ~19.15 s, peak RSS 683,868 KiB with OpenBLAS=2 on the user host; hardware-dependent result. No native subagent spawn interface exposed, native_subagent NOT_RUN; local Codex NOT_USED. Original owner checkout 57 dirty scientific files remain unchanged. Next physical work: true SMICA effective beam/filter, matched independent source FFP10 residual foreground/noise systematics and polarization, ell>12 response bound, predeclared morphology familywise trial calibration, then only conditional physical claim assessment.
