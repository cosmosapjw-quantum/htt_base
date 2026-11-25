# R118-B: 비단조 주파수 전달

판정: IMPLEMENTATION_VERIFIED_SCOPED. BASS c92de4e007bf03e6a4ebcc0a217c36390ba540a2 (tree 72c0c7117f2ba8d42de3550cb98738ccaf89472c). REC f67be237187372f4d89fe8c021819a38261b14eb 유지, REI 및 R78 미변경. 이전 R117의 strong-probe 실패를 정밀 원자계산으로 해소했다는 주장이 아니다.

## 구현 및 검증

- 이동 log-frequency ray mesh에 polarized occupation coherency를 직접 저장. 기하 전파는 frequency remapping 없이 수행. 냉 Thomson은 재료계에서 동일 주파수의 각 ray를 결합.
- Union resolvent projection과 projected finite-volume generator를 별도로 제공. 후자는 BE/SDIRK2의 모든 stage에서 동일한 generator를 사용한다. CLI의 새 frequency 경로 기본값은 projected이며 기존 bolometric/spectral-moment 경로는 그대로 유지.
- 유한 폭 Gaussian prescribed true absorption/emission. Sobolev 역기울기 또는 drift clipping 없음. 선형 보간 속도 knot 분할, 유한체적 평균 opacity, 지수 transmission, 명시적 경계 및 projection ledger. 실제 공명 재분배와 atomic population feedback은 미구현.
- 245 Rust + 3 example tests, 65/65 수정 후 실행 성공(53 union, 12 projected), 4,360 collision events/subcells, 2,424 line cells, 160 legacy byte equality + 3 default/explicit parity. 초기 base angular grid 제약 실패 4건 보존 후 수정. 18-ray 16-bin dense angular-frequency oracle 최대 절대 성분차 2.3315e-14. 독립 line oracle 13 cases.
- 최대 number collision defect 3.1371e-15, preprojection material energy defect 4.9853e-16, line number defect 1.7101e-15, normal energy balance defect 3.8199e-15, FV stage residual 3.3363e-16. Class B trapezoidal number continuity 3.4369e-11. 최대 projection material-energy defect 2.5825e-3는 별도 수치 오차이며 열교환으로 해석 금지.
- Projected fixed-frequency 시간 수렴 차분비 4.0186, 4.0089. Union 별도 mesh의 후기 차분비 0.8001: resolvent projection의 order degradation 기록. Cold B4 absolute gap 128..1024 bins에서 7.752e-3 -> 1.226e-4.
- 1024-bin analytic line-signal weighted L1 relative errors monotone 4.2370e-5, turning 5.3934e-5. 좁은 line sigma=.0005 사례 4.3751e-4. Quadratic tangency integral sigma^(-1/2) scaling은 Wolfram과 독립 SciPy 검산.

## 실제 초기 strong-tilt 냉각력 history

z_emit=2800, beta=(.1,.03,0), shear=.03, eta_end=.025, 64 steps. R117 원래 실패한 REC closure를 끄고 원본 HYREC table xe가 소유하는 opacity로 accepted cold recoil trajectory를 다시 계산했다. 이 history 위에 10.2 eV 중심, log width .02, strength .03, source 0인 예시 Gaussian line 적용. 실제 원자 line coefficient가 아니다. drift range [-105.4502,99.5447], 16/32 rays 부호 반전, 72-ray 확인 36/72. Union line number -2.0311688867e-7 (2048 bins), material energy -1.1741644190e-6, 누적 material projection energy +1.8866553732e-4. Projected 1024 bins -2.0638421498e-7 vs union -2.0627202514e-7. 1024->2048 line signal ~1.55% 변화와 projection error의 signal 초과 때문에 실제 열 및 population feedback은 허용하지 않는다.

## 출처 및 인계

BASS 연구 폴더 research/r118b_frequency_transfer 에 수치 결과, source hashes, binary SHA256, raw compressed logs, 독립 검산 스크립트, 검증 스크립트와 실패 기록이 있다. 원시 trajectory/occupation TSV는 workstation Downloads의 bass_r118b_frequency_final, bass_r118b_dense_final, bass_r118b_projected_refine, bass_r118b_regression, bass_r118b_frequency_trial에 보존. R117/R118-A 기준 출력으로 재현 가능. Native subagent 독립 심사는 도구가 없어 미수행. 대신 독립 행렬 및 characteristic 적분 검산을 수행했다.

다음 ID: R118-C-CONSERVATIVE-RESONANCE-REDISTRIBUTION-01. Number-energy 동시 보존 spectral reconstruction, 경계 flux 정량화, calibrated resonance redistribution 및 detailed balance를 우선한다. Atomic population 및 thermal/recoil coupling은 해당 조건을 검증한 뒤 수행. 관측 likelihood, HeIII 전이, 장시간 high-l 검증은 별도 미해결 의무.
