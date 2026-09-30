# Local Codex 후속 인계: C04 검토 연결만 마무리

ROLE=LOCAL_C04_REVIEW_DISPATCH_CLOSEOUT
PROJECT=htt_base
REPO=/home/cosmosapjw/Dropbox/bianchi/htt_base
SOURCE_RUN=GRSTAT-C04-CERT-20260930-1530KST
SOURCE_PUBLICATION_COMMIT=08429842d1e18671676c0deae925c5bcf9946de2
CONTRACT_SHA256=0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63
EXISTING_REVIEW_LAUNCH=cl_000fce20034122657b6cdf509703df23

C04는 동일 원자 계약으로 네 축 실행을 마쳤고 raw aggregate는 CAS_4AXIS_PASS다. 과거 conflict는 그대로 보존한다. 이 작업은 엔진 재실행이 아니라 미청구 reviewer launch의 지원된 첫 dispatch 연결을 해결하는 작업이다.

1. 기존 checkout과 현재 선택된 global authority를 사용한다. 현재 run의 REVIEW_ROUTING.json, REVIEW_REQUEST.json, review_inspect.stdout.log를 읽고 현재 지원된 inspect를 사용한다. 기존 task/run/launch IDs, 비용·실패 기록을 유지한다.
2. 기록상 launch는 already_claimed=false, bound_child_id=null, DIRECT_UNCLAIMED_LAUNCH다. 현재 상태도 그러한지 확인하고, 등록 정보와 실제 spawn 요청의 입력·cwd·task_name/launch 연결을 지원된 CLI/help/schema와 대조한다. null task_name이 원인이라고 미리 단정하지 않는다.
3. 지원된 절차로 기존 launch의 첫 dispatch를 수행한다. workspace_job.json을 새로 만들거나 plan-continuation을 호출하지 않는다. 재등록 반복, hook 비활성화, 정책 수정, 다른 이름의 reviewer로 비용 기록을 우회하지 않는다. 상태가 바뀌어 이미 청구되었으면 중복 dispatch하지 않는다.
4. reviewer에는 정확한 계약, 소스, 실행 근거를 제공하되 Host의 수용 의견이나 이 문서의 결론을 독립 검토의 입력 근거로 주입하지 않는다. reviewer 완료는 실제 child 결과와 runtime 관측으로만 기록한다. 작성자 모델이 불명확한 부분은 UNKNOWN으로 유지한다.
5. 검토에서 구체적 수학/소스 문제가 나오면 그 범위만 처리한다. 문제가 없고 검토가 완료되면 C04 원자 성분의 검토 완료 상태만 추가한다. 새 문제가 없는데 네 엔진을 다시 실행하지 않는다. 지원된 dispatch가 계속 차단되면 정확한 요청·거절·inspect 결과를 남겨 운영 차단으로 반환한다.

반환: 기존 launch의 처리 결과, 실제 reviewer 관측 또는 차단 사유, C04 범위 내 findings, 변경한 파일, source/raw manifest, 과거 기록 보존 여부. 등록 검토 성공을 CAS-13 전체·관측 fit·novelty·Bianchi 분류 승격으로 확대하지 않는다. 새 push는 이 인계의 필수 작업이 아니다.

다음 과학 작업은 별도 단위의 CAS11-C02 유한 Gram 정리다. 첨부 NEXT_FINITE_GRAM_DERIVATION_KO.md는 Host의 후속 이론 자료이고, 새 blind 축 작성자에게 주는 중립 입력 계약을 자동으로 대체하지 않는다. 이 C04 검토 연결 작업에 CAS11 구현·네 축 실행 또는 전체 17개 재실행을 섞지 않는다.
