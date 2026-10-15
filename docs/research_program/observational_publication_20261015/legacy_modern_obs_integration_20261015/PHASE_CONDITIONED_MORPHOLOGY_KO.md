# P2 L02 | Planck 저다중극 power 고정 조건부 형태 모형

일자: 2026-10-15 KST. Legacy × modern × observations 통합 commit 4b30c9acd8554178db177e2f75293dfcd1fe8b68에 기반한 연구 루프. 본 보고서의 수치 결과는 관측 source-conditioned 및 이상적 Gaussian phase 모형에 속한다. Planck 공식 PTE, cosmological anisotropy 검출, physical shear/tilt posterior가 아니다.

## 원본 연구 아이디어 보존과 새 유도

Legacy TeffMomentMap은 방향 온도장 Theta(n)=Teff(n)/T0 및 bolometric F4=<Theta^4>를 연구했다. 현대 exact STF/Gaunt 구현은 실제 온도 저다중극 l2 5개, l3 7개 orthonormal real a_lm에 대해 t=Theta-1의 2,3,4차 모멘트를 계산한다. 이 F4는 MIO/statistical certified filling fraction F, signed x, Q 또는 Pi와 다른 함수이며 새 독립 likelihood로 곱할 수 없다.

Gaussian statistically isotropic full-sky ideal null에서 a_l ~ N(0,C_l I_{2l+1}). 각 l의 관측된 노름 R_l=||a_l||을 고정하면, 두 계수 벡터 방향은 독립적인 균등 단위구면 S4, S6을 따른다. 구면조화 addition theorem과 uniform sphere fourth tensor moment로부터

    v_l=R_l^2/(4*pi*T0^2)
    E[s3 | R2,R3]=0
    E[k4 | R2,R3]=
       3[(5/7)*v2^2+(7/9)*v3^2+2*v2*v3]/(v2+v3)^2.

여기서 s3=<t^3>/<t^2>^(3/2), k4=<t^4>/<t^2>^2. 순수 l2의 평균 k4=15/7, 순수 l3의 평균 k4=7/3이며 Wolfram symbolics 및 16,384회 Monte Carlo로 독립 수치 확인. 양의 전체 진폭 변화에 대해 s3,k4 scale invariant.

이 이론의 정확성은 FULL SKY Gaussian independent per-ell 원본 계수에 대한 것이며, 실제 마스크로 적합한 Planck 소스 계수의 물리적 조건부 null 동치성을 보증하지 않는다.

## 실제 3개 자료 모델

1. 실제 Planck 2018 SMICA_FULL 동일 하늘 한 개와 그 외 여덟 온도 처리 산출물. 원본 계수의 SHA256는 900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459.
2. 이상적인 Gaussian phase-only 모델: SMICA_FULL 관측 R2=37.76504492 microK, R3=50.48870376 microK 고정, seed 20261015, phase realizations 16,384. 실제 관측하지 않은 가상의 랜덤 harmonic coefficient orientations.
3. 실제 FFP10 CMB-only 999 source realization IDs: 소스 캐시 SHA 86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb. 원래 temperature source common mask, NSIDE64 RING selected 26,846픽셀과 l0..5 simultaneous real harmonic OLS를 적용한 후, 각 simulation의 l2/l3 norm을 실제 SMICA_FULL의 R2/R3로 각각 재정규화했다. 각 simulation phase 방향은 보존되며 서로 다른 map 처리 결과를 독립 실현으로 추가하지 않는다.

## 숫자

SMICA_FULL s3=-0.10157208795, k4=3.15955214630.
정확한 이상적 조건부 평균 k4=2.61555343705.

| Statistic | 16,384 ideal phase | 999 FFP10 mask source phase |
|---|---:|---:|
| mean s3 | 0.002126651 | 0.002213968 |
| std s3 | 0.287284862 | 0.288145928 |
| mean k4 | 2.616938879 | 2.618053883 |
| std k4 | 0.322828575 | 0.328748125 |
| fraction s3 <= observed | 0.369202 | 0.391391 |
| fraction k4 <= observed | 0.946106 | 0.943944 |

두 경험적 CDF의 최댓값 차이: s3=0.0262914892, k4=0.0231924429. FFP10 source amplitude-reweighted k4 평균과 이론 기댓값 차이는 0.00250044548, 이상적 phase Monte Carlo 평균과의 차이는 0.00138544245.

Raw/reweight되지 않은 FFP10 cohort의 k4 평균은 2.551135606으로 다르다. 원본 source군에서 l2/l3 진폭비의 분포를 섞으면, 실제 observed C2/C3 조건부 형태 분포와 구별해야 함을 확인했다.

이 수치는 서로 다른 두 SOURCE-CONDITIONAL 분포의 기술적 유사도를 의미한다. 실제 SMICA_FULL k4의 약 94.4% 누적 위치를 Planck 공식 anomaly p로 해석하지 않는다. 이미 데이터를 본 다음 s3/k4를 채택했으므로 retrospective이고, 실제 beam/foreground/HM/OE/noise, l>=6 high-mode response를 반영한 exchangeable end-to-end null은 미증명이다.

## 여섯 논문 DAG 진행

이번 루프에서 X03을 여섯 논문 전부의 retrospective selection history 및 future admission contract inventory로 범위 한정 완료했다. 그러나 prospective_confirmatory_registration_created는 false이며, 새로운 독립 맹검 소스의 사전등록이나 calibrated Planck null을 대신하지 않는다. P2 L02는 위 수치/이론 근거를 추가했지만 L01 physical source transfer 및 L03 null adequacy가 미완성이므로 완료 상태로 승격하지 않았다.

전체 42개: 범위 한정 완료 8 (19.05%), 즉시 실행 가능 7, 외부 입력 필요 7, 의존성 대기 20. 논문 제출 최종 gate 0/6. 앞으로 progress 명령은 python3 scripts/htt_publication_progress.py 이며 스냅샷은 DAG_PROGRESS_20261015_phase_null.json이다.

재현 자료: teff_phase_conditioned_null.py, run_htt_phase_conditioned_morphology.py, tests/test_teff_phase_conditioned_null.py 및 real-source tests; 결과 디렉터리 planck_fixed_C2C3_phase_v1 및 독립 REPLAY를 포함한다. FFP10 source cohort 원본은 수정하지 않았고, source release의 다른 스레드 PR531/PR532 결과와도 중복 likelihood로 결합하지 않았다.

주요 비교 문헌: Planck Collaboration 2018 results VII, A&A 641 A7 (2020), doi:10.1051/0004-6361/201935201; Oliveira 등, Phys. Dark Universe 30 100608 (2020), doi:10.1016/j.dark.2020.100608. Planck low-ell multipole vector SI 결론, trial-family 선택과 마스크 문제는 새 원고의 신규성 기준으로 사용한다.

다음 유의미한 과제는 P2의 동일 l2,l3 morphology score에서 물리적으로 적격한 noise, beam, foreground 및 mask/하이모드 forward response와 독립적인 simulation law 확보와 재현/coverage 검증이다. 이후에만 실제 observational morphology likelihood 또는 beyond-FLRW/Bianchi 모델 대조로 확장할 수 있다.
