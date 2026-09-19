# 이 스레드로 돌아올 MAIN 검토 prompt

아래 블록을 이 스레드에 붙여 넣으십시오. 이 파일은 source/results commit
dcc5c7c215c671dc8036771e520bcafa4056cd65에 대한 복귀 안내이며, 아래 RETURN_TREE는 그 source commit의 tree입니다.

```text
ROLE=MAIN_RETURN_REVIEW
PROJECT=HTT
WORK_UNIT=HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH
RETURN_COMMIT=dcc5c7c215c671dc8036771e520bcafa4056cd65
RETURN_TREE=ef6bb19ea87c0fd6fcc0a45d1f46522be39c567c
RETURN_ENTRY=https://github.com/cosmosapjw-quantum/htt_base/blob/dcc5c7c215c671dc8036771e520bcafa4056cd65/docs/research_program/optical_mapping_r10_20260919/local_execution/RETURN_TO_MAIN.md
TESTED_SOURCE=dcc5c7c215c671dc8036771e520bcafa4056cd65
COMPLETED_ACTIONS=OP-00 source/tree/manifest verified; OP-01 documented conventions; OP-02..05 finite optical fixture executed with scope limitations; OP-06 Cartesian/packed/public-RHS T9 mismatch confirmed; R9 pinned reuse and finite joint-law discriminator
BLOCKED_ACTIONS=independent review CLIENT_WORKTREE_MISMATCH; OP-07 FORMAL_T9 absent; OP-09/11 no formal optical admission; R9 observed methods not qualified here; OP-06 mixed-CG normalization unresolved
PRESERVED_FAILURE=https://github.com/cosmosapjw-quantum/htt_base/blob/dcc5c7c215c671dc8036771e520bcafa4056cd65/docs/research_program/optical_mapping_r10_20260919/local_execution/t9_attempt03.log
REVIEW_BLOCKER=https://github.com/cosmosapjw-quantum/htt_base/blob/dcc5c7c215c671dc8036771e520bcafa4056cd65/docs/research_program/optical_mapping_r10_20260919/local_execution/review_blocker.json
T9_DIAGNOSIS=confirmed for ell2 isotropic Cartesian/packed/public photon RHS; mixed normalization unresolved; no production patch
OBSERVED_METHODS=none

반환 문서·원 source/diff·실행근거를 읽고 각 결론의 범위와 잔여 과학 문제를 판정하라.
계획 완료나 node exit를 science PASS로 승격하지 않는다. 기존 R8/R9 결과를 전부
재실행하지 않는다. 원래 Q/O 형태·관측 응답·공유 보정·조건부 물리해석에 무엇이
추가됐는지 설명하고, 미해결 문제가 막는 정확한 consumer와 다음 최소 연구를 정하라.

독립 검수는 실행되지 않았다. Native client를 아래 정확한 worktree에서 열어야
한다. subprocess cwd나 prompt 수정으로 child identity를 대신하지 말라. 원 checkout의
EXTERNAL-FUSION active run과 dirty 변경은 보존하라.
/mnt/sn850x2t/htt_base_e2e/HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH/worktree
미전달 registration cl_57e1777283bfeda24c9ae6dcdb579394와
HTT-R10-OPTICAL-LOCAL-20260920/optical_review assignment를 먼저 확인하고,
같은 미실행 review를 중복 child 없이 재개 가능한지 판정하라. 이 checkpoint의
bounded acceptance는 review 미실행 때문에 STOP_INVALID로 종료되었으며, science
FAIL 일반화는 금지한다. 재개할 검수/수리의 범위를 명시적으로 고정하라.

반복 불필요: optical maximum residual 5.998090912839871e-12; 5 pytest passed;
T9 10 cases residual 2 and intentional exit 1. 필요한 changed cell만 재검증하라.
최소 검증 명령 (위 worktree cwd):
python3 -m pytest docs/research_program/optical_mapping_r10_20260919/local_execution/test_optical_fixture.py -q

T9 수정은 현재 source·kinetic reference의 scope를 보존하고 FORMAL_T9의 네 축
admission과 mixed normalization을 해결한 뒤 최소 candidate로 하라. 전체 RHS 부호
반전은 금지한다. R9 제품법칙/관측 경로는 광학/T9 readiness와 독립적으로 진행하라.
```
