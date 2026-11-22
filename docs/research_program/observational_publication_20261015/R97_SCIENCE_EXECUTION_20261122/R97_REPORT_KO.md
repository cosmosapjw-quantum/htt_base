# HTT R97 Scientific Execution Report (F1-F8 Remediated)

- R78 정본 SHA256: `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11` (60 nodes, 129 edges, `NEXT_ID=SQ-CF4`)
- `original_science_status_changed = false`, `actual_r97_physical_science_acceptance = false`

## 핵심 교정 결과 (Units A-D, F1-F8 반영)
- **Unit A / SQ-CF4 (P3, F3/F7)**: `K4 in col(J7)` 백색화 분산 포함률 binary `S7` `98.85%` / IVW `W7` `99.51%` (모델 동일성 미주장). 고정 설계 잔차 근사 0.087 mag 1-sigma `H0` `[ 70.10, 75.75 ]` vs 실제 원천 modulus 재적합 `delta=+-0.087 mag` (고정 가중치 R95 `[70.0621, 75.9072]`, `q` 불변 오차 `6.29e-15`, 가중치 갱신 `[70.0651, 75.9038]`). DirectCal 대비(`e_SNIa - e_DirectCal`) 무정규화 분산=0, rank6/rank7 95% 반폭 구분 (`SQ-CF4 = BLOCKED_INPUT`).
- **Unit B / Planck SMICA (P2, F5/F6)**: MASTER 동일 추정대상 `ratio_of_means`: 이론 `0.04958` vs `N=512` band-limited MC `0.04948` (SE `0.00025`, 상대차 `0.0018`). ID 우선 분할 + train-only 가중치 + 2048 OLS 일치 후 SMICA heldout rank p: raw `0.1589` (23/150 초과), ridge `0.1656` (24/150 초과), heldout B 분산비 `0.9960` (95% bootstrap CI `[0.9910036341169466, 1.0006316184701747]`). L=2 주입-복원: 단일부호 `0.9332` (이차 `[1,sqrt(A),A]` 교차항 반영), 대칭쌍 `+-sqrt(A)` `1.0000` (`commander_null_qualified = false`).
- **Unit C / Bianchi Coupled-m Spin-2 (P5, F1/F2/F8)**: Thomson $T_2-E_2$ 부호를 `+sqrt(6)/10`으로 교정(m=-2..2 signed 각도구적 최대오차 `8.88e-15`), sparse augmented `expm_multiply` 시간전파 도입(`L=60` `VI_-1/9` `B/E = 1.467240`, 재평가 r=1->r=4 `B/E` 상대차 `1.16e-02`), admissible `VII_h` oracle (`|n@a|=0.0e+00`, T/E/B=`2.41e-09/1.67e-09/3.24e-09`) (`SQ-NATIVE`, `B02-B05` 미승격).
- **Unit D / P1, P4, P6, PHY-01..07 (F4)**: P1 4창 signed 9-vector 전파(반례 재현 `1972/2048 > 1971/2048`), 보수적 삼각부등식 outer bound w3 `[0.0005, 1.0000]`, 전역 최적성 인증(min gap `0.2468`) per-draw sharp bound w3 `[0.1318, 0.9639]`, common witness `[0.1338, 0.9629]` (`physical_Pi=None, physical_GF=None, actual_normal_vorticity=None`).
