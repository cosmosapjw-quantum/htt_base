# HTT R97 Scientific Execution Report

- R78 정본 SHA256: `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11` (60 nodes, 129 edges, `NEXT_ID=SQ-CF4`)
- `original_science_status_changed = false`, `actual_r97_physical_science_acceptance = false`

## 핵심 신규 과학 결과 (Units A-D)
- **Unit A / SQ-CF4 (P3)**: R36 `K4 == A@(d*I4)` 재구성 오차 `0.00e+00`; `K4 Sigma4 K4^T` 백색화 분산 중 `98.85%`가 `col(J7)` 내부에 존재; `table3` 수치 필드 기반 6채널 지원이 R27 `selected_support_7`과 `0` 불일치 확인 (`DirectCal`은 속도지표 겸유 9개 그룹 정의 차이 분리, `DMzp - DMav = -0.147` mag 전 35,968그룹 항등). 역분산 분할단위 `W7` 및 0.087 mag 공통 캘리브레이션 불확실도에서 1-sigma 부분식별 구간: R95 `[70.10, 75.75]`, R36 `[69.43, 75.04]` km/s/Mpc; 모수 추정 공분산 포함 내측->외측 Schur 18-dof reduced chi2 R36 `3.978` vs R95 `2.254` (`SQ-CF4 = BLOCKED_INPUT` 유지).
- **Unit B / Planck SMICA (P2)**: NSIDE=2048 Mask-Pol 해석적 Master E->B 비율 `0.04958` vs 8-draw pure-E MC `0.05399` (상대차 `8.172e-02`). 150/150 분리 교차검증에서 `TE->B` 누설 제거 후 heldout 분산비 `0.9960`, debias 60D rank p=`0.1722`. L=2 주입-복원 선형 기울기 `0.9332` (`commander_null_qualified = false`).
- **Unit C / Bianchi Coupled-m Spin-2 (P5)**: R49 4D 접속 `Gamma4`의 `+0.5` spin-1 eth/eth-bar 이류 + Sachs 스크린 회전을 `M_geo_exact` (발산항 포함)으로 m in {-2..2} (`L=8,16,32,60`) + all-m (`L=8,12`) 계층에 결합. 무손실 반-에르미트 오차 `1.43e-17`, 2D GL 스크린 회전 오라클 오차 `6.11e-17`, 실제 R49 4D 측지선 적분기 대비 상대오차 T/E/B=`4.31e-10`/`5.31e-10`/`7.94e-10`. `VI_{-1/9}` 예외류 (`h=-0.111111`)에서 순수 m=0 전단 시드로부터 m!=0 산란비 `2.4582e-01`, `L=60`에서 `B/E = 1.3949`, all-m(`L=12`, dim=499) `|m|>2` 누설비 `1.8906e-03` (`SQ-NATIVE`, `B02-B05` 미승격).
- **Unit D / P1, P4, P6, PHY-01..07**: P1 2,048 4창 결합분포에 95% 타원체 사중극 보정 불확실도 `0.00738` 전파 (w3 tail `[0.05]`: `[0.1221, 0.9624]`), 60노드 전체 원장 (`R97_60_NODE_EXECUTION_LEDGER.json`) 및 교차물리(`PHY-01..07`) 갱신 완료 (`physical_Pi=None, physical_GF=None, actual_normal_vorticity=None`).
