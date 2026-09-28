# 반환 인계 — Type-free Loop 2 보정·종료

상태는 `CLOSED_SCOPED_WITH_EXTERNAL_BLOCKERS`다. 현재 권위 포인터는
`docs/research_program/TYPEFREE_LOOP2_CURRENT.md`이며, 기존 40개 게시 근거와
역사 DB/raw는 그대로 보존됐다.

## 완료된 것

1. F1의 kernel 필요충분조건을 무제약 유한차원 선형/affine variation으로
   한정하고, 일반 (K)에서는 fibre image를 직접 평가하도록 보정했다.
2. F2 후속 migration을 구현했다. alias·기존 출력·중간 실패를 fail-closed로
   처리하고 실제 549 MB DB에서 역사 20개 테이블과 Loop 2 evidence/lineage
   19행을 모두 보존했다. 새 correction 3행과 review 2행만 추가했다.
3. F3의 “3열”을 “3성분 단일 열 + 별도 3×3 identity”로 바로잡았다.
4. 57개 PR을 분류했다. 이미 main에 도달한 8개와 근거 있게 대체된 #468,
   #470을 comment 후 닫았고, 실제 merge를 했다고 표현하지 않았다.
5. #448은 동일 #444 head의 attempt 3에서 runner와 8단계가 모두 실행·성공해
   닫았다.
6. #469의 stale 설치 문자열 검사는 branch commit `f621a581…`에서 실제 pin과
   순서를 검사하도록 고쳤다. 두 exact-head 실행이 서로 다른 projection을
   내어 #445와 #469는 열어 두었다.

## 남은 외부 blocker

- 실제 author model/effort attestation이 없어 등록된 fresh independent reviewer를
  launch하지 않았다. router 선택과 host 실행 증거를 혼동하지 않는다.
- #445: run 36444766290 attempt 1의 `2dbe0061…`/1222 bytes와 attempt 2의
  `8b0aadf1…`/1221 bytes 차이를 설명·제거하고, 같은 head에서 독립 성공 2회를
  얻어야 한다.
- W1의 source/time law, joint anchor/likelihood, 두 depth response와 native
  low-ell morphology atlas가 없다. 따라서 관측 admission은 계속 HOLD다.

## 재개 시 단일 다음 행동

#445의 두 canonical ASCII preimage에서 달라진 floating fields의 생성 경로를
추적한다. frozen feature/package SHA, expected projection SHA, PR-304 명령,
환경 pin이나 비교 대상을 바꾸지 않는다. Loop 2 이론 마감을 새 solver/관측
캠페인의 선행조건으로 되돌리지 않는다.
