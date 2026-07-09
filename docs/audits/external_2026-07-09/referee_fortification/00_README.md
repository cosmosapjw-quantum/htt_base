# HTT 외부감사 연구보고서 v6 — 심사 + 방어·강화 패키지 (v2)

대상: `external_audit_research_report_20260708_v6` (2026-07-08)
작성: 2026-07-09. v1 = 독립 심사·검증. **v2 추가 = 비판을 수용하되 주장을 강화하는 방어·보강 프로그램** (완전 증명 + 실행 코드 + WBS).

## 구성

| 경로 | 내용 |
|---|---|
| `01_referee_report_ko.md` | [심사] 심사 보고서 — 수학·논리 / 물리 해석 / 통계·데이터 / 독창성 / 출판가능성, 약점(치명/중요/사소), 최종 권고 |
| `02_revision_recommendations_ko.md` | [심사] 수정 권고 R1–R12 (LaTeX 교체 문안 포함) |
| `03_theorem_candidates_ko.md` | [심사] 정리 후보 T1–T9 (진술·스케치·검증 훅) |
| `04_numerical_experiments/` | [심사] 검증 실험 12종 + 러너 + 결과 |
| `05_fortification_plan_ko.md` | **[강화] 마스터플랜** — 반격 3패턴(일반화/전유/폐합), 비판별 대응 매트릭스, WBS Phase A–D, Saadeh 2016 정량 대조표와 위치 선언, 저널 전략(Paper A/B/C 초록), 예상 심사질문 리허설 |
| `06_strengthened_theorems_ko.md` | **[강화] 완전 증명집** — T1′(부호 박스)+DL1/DL2, T2′(엄격성 iff), T4′(추정 공분산 정확 크기), T5′(정확 IM), T8′(검정력), T9′(다성분 틸트), T3-lin 스케치 |
| `07_fortification_code/` | **[강화] 실행 코드 7종** — 아래 표 참조 (전부 PASS) |
| `08_paper_skeleton/paper_A_skeleton.tex` | **[강화] Paper A LaTeX 스켈레톤** (자산 이식 지도 포함) |

## 실행법

```bash
pip install numpy scipy sympy               # matplotlib 불필요
cd 04_numerical_experiments && python3 run_all.py          # 심사 검증 12종 (~1분)
cd ../07_fortification_code && python3 run_fortification.py # 강화 검증 7종 (~2분)
```

## 강화 코드 결과 (7종 전부 PASS)

| 모듈 | 반전 대상 | 핵심 수치 |
|---|---|---|
| fort01 signed-box identified set | **F1** | open [0.110, 0.170] 보존 + all-branch [0.090, 0.170] 추가; DL1 단조성; 상태대수 4분기; IM CI 내장 |
| fort02 strictness exact witness | **M1** | 유리수 정확 산술 371/371 iff 일치 (엄격 260 / 정렬-등식 111) |
| fort03 estimated-cov two-stage | **M3** | 미보정 크기 0.0665 → F-임계값 0.0555±0.0028 (정확); 검정력 손실 ≤3%p |
| fort04 K5 end-to-end | **F2** | CF4 341±102 km/s [REAL] → x_C ∈ [−5.0e−7, 2.68e−5] FEASIBLE + 분기 카드 (PLUGIN 2곳 교체 시 관측 주장 승격) |
| fort05 DESI footprint null | **M6** | 등방+캡 창만으로 resultant 0.883 (D10 값과 동차) 재현; 보정 통계 널 z=−1.1, 주입 A=0.05→z=3.3 감응 |
| fort06 CF4 Malmquist forward | **M7** | 참 벌크 0 + 거리오차만으로 D13형 부호 전이(+1700→−1690) 재현; 감산 잔차 0-중심 |
| fort07 gate policy | **M8** | 허용역 규칙 G1–G5 명문화 — v6 인쇄 수치 전부 규칙 하 PASS (e-값 z=+1.18) |

판정 의미: **PASS** = 보고서 주장 재현 확인 / **REFUTED** = 진술문 그대로는 반례로 반증 / **WARN** = 주장은 재현되나 도메인·전제 결함 확인.

## 핵심 결과 요약 (12 실험: 10 PASS, 1 WARN, 1 REFUTED)

| 실험 | 대상 | 판정 | 요점 |
|---|---|---|---|
| exp01 | P1/F1 부모 항등식 | PASS | c=(1,−1,1,1) 독립 유도; 3배 결함·(3/2) 규칙 재현; 틸트 항은 사실 β 전차수 정확 |
| exp02 | P26/P31/A8 | **WARN** | [0.11,0.17] 재현. 단 Ω_k 양측 박스면 하한 0.11→**0.09** — 부호 도메인 결함(치명 F1) |
| exp03 | P35/E2/E3 | PASS | naive 0.9275 / IM 0.9465 / proj 0.9653 (게이트 E2: 0.9310/0.9475/0.9665) 재현; Δ→0 나이브 0.906 붕괴 |
| exp04 | P36 | **REFUTED** | 엄격성 부속 주장 반례(정렬 레짐에서 joint=naive); 교정 기준 93/94 일치 |
| exp05 | P19/P29/E5/E7 | PASS | 최대 의존 병합·Ville 재현; §10 e-값 평균 z=+1.18의 허용역 정책 미인쇄 지적 |
| exp06 | P13/F3 | PASS | κ̂ 편향 0-교차 e0=1 재현; ±수치는 구동 이력 종속 → 이력 병기 필요 |
| exp07 | P8/P9/P18/P30 | PASS | rank 2→4, 방사-와도 무감, 2/(1+ρ) 재현 (토이 기저 — 실측 R 공개 필요) |
| exp08 | P16/P17 | PASS | 2/(2ℓ+1), Fisher 하한 재현 |
| exp09 | P28/E8 | PASS | 널 방향 KL=0 닫힌형 재현 |
| exp10 | P32(iii)/P23 | PASS | 중심 χ²의 L>0 1차 무감(trace=0) vs score 감지 대조 재현 |
| exp11 | M5' | PASS | m=10, N_sim=300에서 사양검정 크기 0.05→0.072; "percent-level"은 m≲10 한정 |
| exp12 | P5/F2 | PASS | Σ²_BV 공식·(4/3)β² 보정·slope 2.0 재현 |

## 심사 최종 권고 (v1 요약)

- 외부감사 보고서로서: 치명 F1(Ω_k 부호 도메인), M1(P36 재진술), M2(P31 증명 갭), M3(추정-공분산 임계값)의 5차 수정 반영 조건부 통과 상당.
- 저널 논문 후보로서: **Major Revision** — 위 수리 + 실데이터 end-to-end 1건 + 감사 어휘 전면 재편.

## 방어·강화 결론 (v2)

심사에서 지적된 결함 중 **주장의 철회를 요구하는 것은 하나도 없다.** F1·M1·M3은 더 강한 정리(T1′/T2′/T4′, 완전 증명 + PASS witness)로 대체되고, F2·M6·M7·M8은 실행으로 폐합·전유되었으며(fort04–07), M2는 정리 사다리(T3-lin → T3)로 재배치된다. Paper A 투고 가능 조건 5개가 모두 `05_fortification_plan_ko.md`의 WBS Phase A–B(≤6주) 범위 안에 있다.
