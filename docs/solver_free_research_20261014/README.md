# Solver-free 관측 연구: dossier 적용과 출판 후보

2026-10-14, Asia/Seoul. 기존 PR #532의 추가 7개 commit/808개 변경 파일을 조사하고 실제 solver-free 추가 연구를 수행했다. 검토 기준은 `89621f4c9a6f63449813587a0fadeb13287f8e10`, 이번 branch는 `obs/solver-free-dossier-20261014`다. 전체 diff의 모든 파일을 독립 과학 검증했다는 뜻은 아니다. 현재 결론을 지탱하는 코드·result·후속 refinement를 읽고 영향을 받는 계산을 검증했다.

**주요 성과:** 선택 경계와 정규화의 미분, CLASS rank의 오차 민감도, Gaia의 회전 불변 bias support와 동시 신뢰영역, Union3 node-prior 가정 민감도, CF4 선택법칙 교차 실험. Native solver 구축과 ODE 적분은 없다. 실제 관측 계산·조건부 생성 실험·수학적 충분조건을 구별한다.

| 읽을 내용 | 파일 |
|---|---|
| 현재 결과·그림·한계 | [SCIENTIFIC_REPORT_KO.md](SCIENTIFIC_REPORT_KO.md) |
| 기존 방법론/실제 결과와 출판 기준 | [PUBLICATION_CANDIDATES.md](PUBLICATION_CANDIDATES.md), [JSON](PUBLICATION_CANDIDATES.json) |
| 앞으로 얻을 결과, solver 의존 여부 | [FUTURE_ANALYSES_KO.md](FUTURE_ANALYSES_KO.md) |
| 검토한 PR/commit과 수정 판단 | [REPO_REVIEW_KO.md](REPO_REVIEW_KO.md) |
| dossier에서 실제로 빌린 내용 | [Dossier_MAP](research/Dossier_MAP.md), [유도](research/THEOREM.md) |
| 10단계 이론·코딩 실행 기록 | [RESEARCH_LOOP_KO.md](RESEARCH_LOOP_KO.md) |
| subagent 개발 DAG / PR 작업 카드 | [DEVELOPMENT_DAG_KO.md](DEVELOPMENT_DAG_KO.md), [PLAN.json](PLAN.json) |
| 저비용 모델용 최소 문맥 | [CONTEXT_PACKET.json](CONTEXT_PACKET.json) |
| 복사해서 이어 실행할 지시 | [CODEX_HANDOFF_KO.md](CODEX_HANDOFF_KO.md) |
| 수행/검토/게시 단계 | [DELIVERY.json](DELIVERY.json), [독립 검토](review/INDEPENDENT_REVIEW.md) |

현재 자료는 방법론 원고를 발전시킬 구체적인 근거를 제공한다. 독창성과 충분한 실자료 validation을 모두 만족해 즉시 투고 가능하다는 판정은 아직 없다. 과거 HOLD/UNKNOWN, 실제 global tilt/history response, physical MES/Jacobi remainder, native family admission은 그대로다. 이 제약들은 별도의 solver-free 방법론·source 연구를 중단시키지 않는다.

```bash
python scripts/solver_free_task_packet.py --validate
python scripts/solver_free_task_packet.py --ready
```

이 명령은 agent에게 작업 JSON을 제공한다. 백그라운드 자율 실행 서비스나 예약 작업을 설치하지 않는다.
