# Solver dossier와 저적색편이 입력

## 원문의 식과 R105 실행 경로

아래 경로는 모두 Dropbox 루트 기준이다. Dropbox 메타데이터에서 rev와 크기를 읽고, 워크스테이션 PDF의 SHA-256과 해당 본문을 대조했다. October BASS Vol II와 September Mathematical Verification Vol II는 다른 문서다.

| 경로 | Dropbox rev | 바이트 | 파일 SHA-256 |
|---|---|---:|---|
| /dossier/Dossier_II_Kinetic_Transport.pdf | 65dd5afc2e7920af03d47 | 410288 | 8e4a20c228cb4f6760d258b9ecafb142423a7140698d45871b0151593feef075 |
| /dossier/Dossier_III_Atomic_Processes.pdf | 65dd5afd21dc40af03d47 | 567097 | 8d513df88fe8607d519115c30861657b7327dbcc81aceabf192edf76bb0164c5 |
| /dossier/Dossier_IV_Reionization.pdf | 65dd5afd21dc50af03d47 | 518162 | 2efa8872985f152153a31ec2766c67b2b87dca9b83bd8c6d12d7a7024e1cb75a |
| /dossier/Dossier_VII_Observation.pdf | 65dd5afc2e7940af03d47 | 330223 | 562db108b9a6ce5a80e60d3c1303a89b65580168b06b2a6c45d62e11196034ad |
| /bianchi/Mathematical_Verification_Dossier_III_Recombination.pdf | 65b3f27c2fcdb0af03d47 | 202544 | b43c4c525aa395c0e29b4bf8daaa1f111eb4c4868ebc6defdc0019d47c8aebdd |
| /bianchi/Mathematical_Verification_Dossier_IV_Reionization.pdf | 65b3f28aea0640af03d47 | 194625 | 43f11627926201750bbd5eae148d45daf2913b33eb82ec47e61a083c9b85accd |

- **광자와 유체의 같은 운동량.** II §1.4 (1.25–1.29)는 법선 광자의 에너지·방향 변화와 스크린 수송을, (1.32–1.38)은 helicity 성분과 각 모드 결합을 정한다. (1.39)의 에너지 모멘트에는 전단 일 −σ:πγ와 class-B 항 2a·qγ가 있다. R105의 native optical refinement는 이 기존 각도 연산자와 전자계 산란을 유지하며 각 SDIRK stage에 해당하는 양의 광학 셀 깊이를 적분한다. 두 코드의 최종 하늘/유체 q/E 차이는 모멘트 일관성에 대한 유한 수치 진단이다. 일반적인 4-운동량 보존 오차 한계나 각 Bianchi 계열의 유일성을 주지는 않는다. 산란항의 Doppler 인자는 II (1.42)와 IV §1.6 (1.45)에 있다. 고유 전자밀도와 같은 Γ를 이중 계수하지 않는다.
- **REC/REI가 주는 양.** September REC §9 (40–42)는 초 단위 등각시간에서 dτ/dη=−ac n_e σ_T와 유한 구간의 가시도 적분을 준다. September REI §8 (24–26)는 밀도 가중 H/He 전하를, §11 (36)은 등방 광학깊이 적분을 준다. IV §1.7 (1.49–1.51)은 물질 고유 나이와 광선 시계의 변환이다. `ReiMaterialHistory`는 제공받은 공변속도 0의 궤적에서 HII·HeII·HeIII 전하와 양의 q_op=c σ_T n_e/H를 사용한다. BASS III (1.73) 뒤의 표와 설명은 primordial HYREC가 천체물리적 재이온화를 제외한다고 밝힌다.
- **고정된 관측 적색편이.** IV §1.9 (1.63–1.66)의 움직이는 방출 사건, §1.10 (1.74–1.78)의 고정 관측방향 Killing 주파수·1차 전단 응답이 `ReiObserverRays.log_frequency_ratio/evaluate`와 `REC_OBSERVER_REDSHIFT.json`에 직접 대응한다. VII §1.1 (1.2–1.3)은 스크린 기저·측정자의 선택을, §1.3 (1.7)은 Bianchi I 축 운동량에 의한 독립적인 주파수 예를 제공한다. R105는 평균 z=4의 법선 관측자와 단조인 과거 광선 구간에서 계산한다. IV §1.11 (1.83–1.84)은 꺾이는 적색편이에서 모든 역상을 합하는 추가 확장을 정식화한다.

## 오늘까지 필요한 입력과 계산 가능한 민감도

서명된 재료는 다섯 q_ref 사례 각각에서 평균 z=20→4를 덮는다. Git blob ce22a6b6d94aabf1bffcc3b5c472316cac1983d4의 크기는 891928바이트, SHA-256은 f4bc0046d79faf2cd13ae7ed78135503306c7d76c11580e4601a757c407bc83d이다. +0.01의 전체 원시 정규화 표도 공개 manifest상 312238행, 62611024바이트로 같은 z=4에서 끝난다. z<4의 해당 donor release나 그 다운로드 크기는 확인되지 않았다. 실제 연속 계산에는 사례별 z=4 종료 restart(가스 조성과 온도, 각도·에너지별 광자 재고, a,b,H,s, proper-time clock), 이후의 H/He 이온화 광원·원자 반응·팽창 조건, z=0까지 재생한 n_e(t), 기하와 경계 일치가 필요하다. 알려진 [다섯 이력의 고정 버전](https://github.com/cosmosapjw-quantum/rei_bianchi/blob/56dc609ea9b801c88d3364aed3eee140b3a20d46/research/rei_igm_sync_20261116/approximation_validity/incremental_fifth/results_five/five_case_abundances.csv.gz)과 [전체 표 manifest](https://github.com/cosmosapjw-quantum/rei_bianchi/blob/56dc609ea9b801c88d3364aed3eee140b3a20d46/research/rei_igm_sync_20261116/approximation_validity/incremental_fifth/results_five/FIFTH_FULL_ABUNDANCE_MANIFEST.json).

현재 코드만으로 **모든 사례에 공통인 등방 foreground 가정**은 수치화할 수 있다. 워크스테이션에서 ZERO 원본의 n_H0=1.898198450714027×10⁻⁷ cm⁻³, He/H=0.08130135170951498, H0=67.4 km s⁻¹ Mpc⁻¹, Ω_m=0.315 및 Ω_r=0.000092로 FLRW를 두고, `bass.recombination.reionization.tanh_reionization_xe`를 적분했다. 두 모델 모두 z_H=7.67, Δz_H=0.5다. HeII→HeIII를 켠 모델은 z_He=3.5, Δz_He=0.5다. 양의 적분은 c σ_T n_H0 ∫₀⁴[(1+z)² x_e/H(z)]dz이다.

| 조건부 전경 | τ(0→4) | 먼 신호의 무산란 전송 exp(−τ) | 가정한 x_e(4) |
|---|---:|---:|---:|
| H와 1차 He 이온화 | 0.02112795923 | 0.9790936725 | 1.08129889 |
| 2차 He 이온화 포함 | 0.02243045425 | 0.9778192380 | 1.09053405 |

적응 적분과 2049점 사다리꼴 차이는 두 조건에서 8.05×10⁻¹⁰ 이하이다. ZERO donor의 x_e(4)=1.08339435이므로 접점에서 두 조건 모두 다른 이력을 준다. 공통 τ를 더하면 같은 접점에서 출발한 광자의 기존 τ 각도차는 유지되고 z=4 이전 last-scattering 확률밀도는 표의 전달률만큼 작아진다. 오늘 관측자의 적색편이·각도 선택, 전경 자체의 산란 재방출 또는 편광 생성에는 추가 계산이 필요하다.

**반증 가능한 로컬 검산.** 실제 +0.01의 z=4 restart가 복원되면 마지막 두 native 출력 간격만 먼저 재생한다. 초기 시각과 종단에서 a, b, 각 H/He 분율·온도·proper n_e와 원본의 cohort 재고를 같은 프레임에서 비교한다. 이후 z=4→0의 정밀도를 한 번 올려서 proper-time 적분 c σ_T∫n_e dt와 N 적분 ∫c σ_T n_e/H dN을 동일한 끝점에서 비교한다. 그 차이가 refinement와 함께 줄지 않으면 단위·시계·경계의 불일치를 추적한다. z=4에서 위 tanh 전경의 전하 편차도 함께 반환하면 연속 donor와 공통 스크린의 가정을 직접 판별할 수 있다.
