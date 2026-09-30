# C04 로컬 반환 수용과 다음 이론 단계

기준 run: `GRSTAT-C04-CERT-20260930-1530KST`.
기준 게시 commit: `08429842d1e18671676c0deae925c5bcf9946de2`.
계약 version 3 / SHA-256: `0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63`.

## 결정

**C04 원자 수학 성분의 네 축 CAS 실행 검증을 수용한다.** 원시 aggregate `CAS_4AXIS_PASS`, `RUNNER_OBSERVED_EXECUTION`, `claim_promotion_cas_eligible=true`, `claim_promotion_cas_requirement=SATISFIED`를 서로 대응시켰다. 등록 독립 검토는 미완료이며 전체 과학적 승격은 하지 않는다. 이 둘을 이유로 관측된 CAS aggregate를 다시 `CAS_BLOCKED`나 과거 `CAS_CONFLICT`로 바꾸지 않는다. 과거 conflict는 원 run의 역사적 결과로 보존한다.

| 축 | 확인된 실행과 범위 |
|---|---|
| Wolfram/xAct 축 | 실제 수학 검사는 Wolfram의 세 보편 실수 양화식 Resolve. xAct 로드는 preflight 근거다. |
| SymPy | 정확한 QQ 항등식, 양의 분모, 명시된 순서·절댓값·최댓값 추론 연결. 변조 거절 7/7. |
| Sage/Singular | QQ 다항식과 libSingular 환원, 명시된 순서 추론 연결. 변조 거절 8/8. |
| Lean/mathlib | 보존된 `grstat_cas13_minimax`를 고정 `leanprover/lean4:v4.31.0`으로 새 실행한 runner 근거. 새 독립 저자 증명은 아니다. |

Python/SymPy 및 Sage의 작은 순서 추론 checker는 명시된 신뢰 경계를 가진다. 이를 Lean kernel 검증이나 독립적인 일반 양화사 제거기로 재분류하지 않는다. 이 대화에서는 엔진을 재실행하지 않았다.

## 확인한 원문 범위

두 첨부를 HTML 공백·Markdown escape만 복원하여 JSON으로 읽었고, 직접 취득한 `RETURN.json`, `RAW_EVIDENCE_MANIFEST.json`과 의미적 동일성을 확인했다. 첨부와 원본의 바이트 동일성은 주장하지 않는다. 원 manifest SHA-256은 `5eff1fdccddaa3c3be2f26cd16cd76002718fa2d231a503233d09ce478055b9a`다.

manifest에 든 37개 중 판정에 필요한 12개를 선택 취득하여 해시·크기를 확인했다. `ADJUDICATION.json`은 runner stdout과 바이트가 일치한다. 실행 spec, runner 기록, 두 자체검사 전체 출력, reviewer routing/inspect를 읽었다. 반환·새 manifest의 여섯 소스 hash는 이전에 확인한 보존 바이트와 일치하며 같은 소스를 다시 다운로드하지 않았다. 상세 범위는 `ACCEPTANCE_EVIDENCE.json`에 있다. 이 검토를 37개 전체 재검증이나 등록 독립 reviewer 완료라고 표기하지 않는다.

## 이제 사용할 수 있는 결과

실수 \(0<L\le U\), \(x\in[L,U]\)에 대해
\[
a_*={2LU\over L+U},\qquad r_*={U-L\over U+L}
\]
는 전 구간 상대손실 \(|a_*/x-1|\le r_*\)를 만족하며 양 끝에서 달성한다. 모든 실수 경쟁자 \(a\)에 대해
\[
r_*\le\max\{|a/L-1|,|a/U-1|\}
\]
이다. \(L=U>0\)도 포함한다. \(L,U,a_*\)는 같은 물리 단위, \(r_*\)는 무차원이다.

따라서 이 정리는 이미 정당화된 양의 구간을 받아 대표값과 최악 상대손실을 정의하는 순수 수학 인터페이스의 근거로 사용할 수 있다. 관측값에서 구간을 만드는 절차, 포함 확률, likelihood, 좌표·frame 변환, 부동소수점 안정성은 이 정리의 결론이 아니다. 부호가 있는 텐서 성분이나 0을 가로지르는 구간에 그대로 적용할 수 없다. CAS-13의 C01–C03과 관측적·물리적 의무는 열려 있다.

## 독립 검토 차단의 정확한 위치

등록 성공 launch는 `cl_000fce20034122657b6cdf509703df23`이다. native spawn은 PreToolUse `ROUTING_REGISTRATION_REQUIRED`로 거절되었고 child는 생성되지 않았다. 이어진 재등록의 `EXISTING_CHILD_NOT_CLOSED`는 실제 reviewer 실행의 증거가 아니다. 지원된 inspect는 `already_claimed=false`, `bound_child_id=null`, `DIRECT_UNCLAIMED_LAUNCH`, `prospective_issues=[]`를 보고한다.

따라서 다음 최소 조치는 **기존 미청구 launch의 첫 dispatch 연결을 지원된 인터페이스로 해결하는 것**이다. inspect가 안내한 대로 등록된 원 checkout에서 이 launch를 재사용하고, `workspace_job.json` 생성이나 `plan-continuation`, 무조건 재등록을 하지 않는다. 정확한 실패 원인은 dispatch 입력·현재 hook의 기대 입력을 대조하기 전에는 확정하지 않는다. 외부 source 검토가 비용·등록 정책을 우회하는 수단이 되어서는 안 된다. 이 운영상 차단 때문에 C04 수학 엔진을 다시 실행할 필요는 없다.

## 다음에 전개할 이론

다음 목표는 `CAS11-C02-FINITE-GRAM`의 임의 유한 차원 결과다. \(R=R^T\succeq0\), \(\varepsilon\ge0\)에 대해
\[
\forall a:\ |a^Te|^2\le2\varepsilon\,a^TRa
\quad\Longleftrightarrow\quad
e\in\operatorname{range}R,\qquad e^TR^\dagger e\le2\varepsilon
\]
를 직접 유도했다. 동결 C02는 순방향 목표이므로 역방향은 별도 확장으로 분리한다. \(R=0\), \(\varepsilon=0\), 특이 비영 행렬을 포함하며 \(\varepsilon\)나 0일 수 있는 이차형식으로 나누지 않는다. 상세 증명은 `NEXT_FINITE_GRAM_DERIVATION_KO.md`에 있다. 이번 유도의 근거 상태는 `DERIVED`이며 새 네 축 실행·형식 검증·신규성 판정은 없다.

물리적 적용에는 동일한 양의 내적에서 \(e_i=\langle r_i,z\rangle_W\), \(\|z\|_W^2\le2\varepsilon\)와 필요한 모멘트 소거를 별도로 증명해야 한다. C03의 사영·Gram 항등식만으로 이 연결이 생기지는 않는다. 이 결정론적 잔차 Gram을 관측 잡음 공분산으로 사용하지 않는다.

이번 반환 수용의 종료 조건은 충족됐다. C04의 반복 CAS 실행과 동일 소스 재검토는 끝내고, 등록 검토 연결은 운영상 후속으로 분리한다. 다른 17개 전체 재실행이나 catalogue fit은 요청하지 않는다. 이번 수용 문서는 새 산출물이며 저장소에 추가 push하지 않았다.
