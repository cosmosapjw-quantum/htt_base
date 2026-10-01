# 로컬 순차 증명 검증 인계 — 2026-10-01

이 패키지는 이 스레드의 HTT/MES → Loop2 → 이론 이식 → GR·통계 연구 계보를 로컬 Codex가 순차 검증하도록 연결한다. Host용 문서이며 blind 축 작성자의 허용 입력이 아니다. 저장소 전체의 모든 과거 브랜치에 있는 정리를 새로 감사했다는 뜻은 아니다.

기준은 `main` `9f46363433723cc3b2dc75bab781274fe1b3df7d` / tree `482c4c50609dfed5081b69138f0b5fc8e4a4b74c`다. owner=`research_program`, claim tier=`non_claim_bearing`, transfer source=`none`. 이 패키지에서 새 CAS 실행·과학적 검증·독립 CAS 심사·관측 적합은 하지 않았다.

## 바로 읽을 문서

1. [로컬 시작 및 반환 handoff](LOCAL_CODEX_HANDOFF_KO.md)
2. [상세 증명 의무·실행 순서](PROOF_VERIFICATION_PLAN_KO.md)
3. [DAG 원본](PROOF_DAG.json) · [Mermaid DAG](PROOF_DAG.mmd)
4. [PR 현황과 향후 작업 목록](PR_LIST_KO.md) · [기계 판독 계획](PR_PLAN.json)
5. [기준 상태·출처·보존 확인](REPOSITORY_SNAPSHOT.json) · [이번 문서 검증](VALIDATION.json)

## 확인된 상태

| 항목 | 이번에 확인한 범위 |
|---|---|
| 선행 게시 | 지정 계보의 14개 commit이 기준 main의 조상. 중복 재게시할 누락 결과는 이 원격 범위에서 발견하지 못함. |
| 보존 | 702개 체크포인트와 Loop2 원본 디렉터리의 Git tree가 기존 게시 정체성과 일치. 원 외부 ZIP 복원 검증은 아님. |
| GR 범위 | 17개 계약의 61개 성분, 46개 주장 및 6개 교과서 대조. CAS-18은 별도 입력 HOLD. |
| 추가 범위 | 이론 이식의 12개 의무와 Loop2의 3개 bridge 그룹. 중복 부분은 진술 동치 확인 후 기존 증명을 인용. |
| CAS11-C02/C03 | 게시된 네 축 PASS + 독립 심사 PASS를 유한 성분으로 계승. 새 finding 없이 재실행하지 않음. |
| CAS11-C01 | v3 입력·라우팅 차단. v4는 제안이며 미채택. 실제 로컬 RETURN/raw가 원격에 없음. |
| CAS13-C04 | 성분 네 축 PASS; 기존 reviewer launch의 identity 차단은 유지. |
| PR | canonical 213개 카드와 현재 열린 GitHub PR 46개를 구분. 새 GitHub PR이나 브랜치는 만들지 않음. |

**사용자 로컬의 미커밋 파일까지 게시 완료한 것은 아니다.** C01 원본 `RETURN.json`과 등록 raw는 그 기계에서 확인·보존·허용된 범위로 게시해야 한다. 대화 요약으로 원본을 복원하지 않는다.

## 첫 행동

기존 `/home/cosmosapjw/Dropbox/bianchi/htt_base`에서 `git status --short --branch`를 실행한다. handoff를 받으려고 즉시 pull하지 말고 fetch + 고정 commit의 `git show`로 먼저 읽는다. 현재 실행 중인 HEAD 결합 작업을 확인한 다음 안전한 fast-forward 여부를 결정한다.

C01 계약 채택·지원 lifecycle이 해결되지 않으면 해당 노드만 보류하고, 기존 로컬 증거를 대조한 뒤 **GR-CAS-01**부터 의존성이 충족된 증명을 순차 진행한다. C04의 동일 blocker를 다시 시도하지 않는다. 전체 수학적 증명, 실행·검토, 게시, 물리적 입력 및 관측 적용은 각각 별도로 닫는다.
