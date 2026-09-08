# HTT R8 — certified morphology and joint physical sets

2026-09-08 · physics/statistics research and Local Codex design successor.

**Base:** `b7172ad904eb357fcce78eb9c5b7164d1e86a9e6`, on `implementation/tensor-joint-r7-20260908`. This is a formal research replan after the R7 implementation and its evidence-binding repair. R7 results and its frozen DAG remain historical records. R8 does not mark their unfinished work complete.

이번 연구의 중심은 **계산이 일부 미해결이거나 자료의 오차 정보가 불완전해도, 정당한 과학적 결론까지 도달하는 방법**이다. 새 수학적 유도는 조건을 명시한 해석적 결과이고, 구현·CAS·mock·실자료 실행은 워크스테이션 Local Codex의 다음 작업이다.

| 새 결과 | 이어지는 과학 작업 |
|---|---|
| SO(3) 거리의 불변량 하한과 적응적 회전 셀 | 큰 CMB pool의 모든 하한이 0이 되는 R7 계산 경로 개선 |
| 구간 순위 `p_lower ≤ p_exact ≤ p_upper` | 모든 거리를 정밀하게 풀기 전에도 보수적 검정과 명시적 미해결 결과 |
| 완전 multipole-vector 표현과 tensor 표현의 정보 동등성 | 표현의 새로움과 통계량·안정성·비용의 실제 개선을 구분하는 ablation |
| 불완전한 공분산에서 주변법칙의 공동 신뢰영역 | CF4/JWST 등 한 자료의 누락이 전체 통합 분석을 멈추지 않는 추론 |
| 나머지항을 포함한 tensorized MES 공동집합 | shear·vorticity·tilt·깊이차를 동일 물리 상태에서 조건부로 제약 |
| 미분 closure의 민감도 곡면과 비식별 증명 | 관측된 형태와 물리 해석에 필요한 추가 가정을 수치적으로 구분 |

Read [SCIENTIFIC_CONTRACT.md](SCIENTIFIC_CONTRACT.md), [THEORY.md](THEORY.md), [DESIGN.md](DESIGN.md), then [LOCAL_CODEX_PLAN.md](LOCAL_CODEX_PLAN.md). The executable work graph is [campaign_dag.json](campaign_dag.json); its structural checker is [validate_campaign.py](validate_campaign.py). [VALIDATION_MATRIX.md](VALIDATION_MATRIX.md) fixes oracle cases and release criteria. [ASSET_REUSE.md](ASSET_REUSE.md) connects owned data, old code and external donors. [HARNESS_UPDATE.md](HARNESS_UPDATE.md) proposes narrowly scoped operational changes. [state/CLOSEOUT.md](state/CLOSEOUT.md) records what actually happened here.

**Inherited evidence:** b7172ad9 records E1–E6 software checks: 51 host tests, the same 51 independent checks, plus 9 additional reviewer tests. Those records were read, not rerun here. The local native stop-hook outcome remains `REJECTED_WRONG_CHECKOUT_RUN_CONTEXT`, distinct from the technical repair acceptance. The earlier DESI qiso interval `[0.9462387032298103, 1.019522180137995]` remains a historical conditional Gaussian result; it is not a new R8 analysis or an anisotropic constraint.

The supplied original-named physmath research/coding ZIPs both identify version **3.1.0**. Their identities are recorded in the evidence ledger. Files named `(3).zip` were not available at this turn's supplied paths, so byte identity to that filename is not asserted. Their research/design procedures are applied to the available 3.1.0 packages.

The design is deliberately branch-local: morphology, marginal/joint laws, physical closure and supported transfer providers each produce their own scientific outcome. A failed model can be rejected; a missing product stays unavailable; a numerical enclosure can remain unresolved. None is silently converted into evidence for a competitor. The synthesis always consumes their receipts, including negative outcomes.
