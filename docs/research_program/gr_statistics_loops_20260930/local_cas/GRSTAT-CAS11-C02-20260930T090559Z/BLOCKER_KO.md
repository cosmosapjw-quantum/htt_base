# CAS11-C02 새 검증: BLOCKED_POLICY

RUN_ID: `GRSTAT-CAS11-C02-20260930T090559Z`
BASE_HEAD: `42a3320b03428bce9457e999ddef18135244a425`
BASE_TREE: `dd01582529c998f68c9ac9b739e6f39d58e24f96`

계약·원 입력 7개와 환경 alias 해시는 모두 일치했다. 기존 handoff만 fast-forward 반영했다.

## 실행 blocker

등록된 fresh-context Wolfram, SymPy, Sage 작성자의 apply_patch가 모두 다음 오류로 거부됐다.

```text
AUTHOR_ROUTE_REQUIRED: Before this parent patch, run the supplied author-route command for these exact paths with a useful local candidate receipt or a concrete local exclusion
```

현재 authority의 author_routing.check_edit는 is_child 상태를 면제하지만 실제 등록된 자식에게 parent 쓰기 게이트가 적용됐다. 이는 관측된 등록/쓰기 거부의 불일치이며 내부 원인은 이번 범위에서 수리하지 않았다. 별도 task·launch 생성이나 정책 변경으로 우회하지 않았다.

Wolfram 작성자는 Host 중단 메시지 수신 전에 shell로 finite_gram.wl 하나를 저장했다. 이는 거부 후 대체 도구 쓰기였으며 미수용 후보로만 보존한다. 그 소스는 실행하지 않았다. SymPy/Sage는 거부 후 대체 쓰기를 하지 않았다. 축별 scalar 탐색/preflight는 전체 정리의 실행이나 PASS가 아니다.

## 판정 분리

- 네 축: BLOCKED_POLICY, 전체 범위 NOT_RUN.
- run-adjudicate: 미실행. raw aggregate: null, 범위 수용: BLOCKED.
- 독립 reviewer: 미등록·미실행.
- 작성자 등록의 validator_argv는 null이므로 runtime 완료만 증명하며 검증 수용이 아니다. 원 계약/runner pins는 별도 기록했다.
- Lean launch `cl_5e39fc6af15cd91b0753690877580da3`: 등록만 되었고 claim/child/exit가 없다. 이 미실행 예약을 임의 종결하지 않았다.
- 기존 reconcile-unbound CLI는 실제 PRE_SPAWN 거부와 원 tool claim을 요구한다. 미dispatch Lean에 해당하는 거부 증거를 만들 수 없다.

## 반환 및 다음 작업

관련 파일은 로컬에만 보존한다. pending Lean launch가 있으므로 HEAD를 유지하고 commit/push/R1은 수행하지 않았다. 지원된 기존 등록 child의 author-route 인식 경로 및 미dispatch launch의 처리 경로가 마련된 뒤 같은 RUN_ID·launch·BASE_HEAD·비용으로 재개한다. 이 작업에서 harness 소스 수리나 C04 lifecycle 변경은 하지 않는다.

C04 CAS PASS/reviewer 미완료, CAS-11 전체 미종결, 과학적 HOLD는 그대로다. 물리 closure·관측 분석·Bianchi 분류·novelty 승격은 없다.
