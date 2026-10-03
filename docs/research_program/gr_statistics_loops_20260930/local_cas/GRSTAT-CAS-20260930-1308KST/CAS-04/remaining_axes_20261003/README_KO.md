# GR-CAS-04 남은 유한 축 실행 기록

소유자: research_program. 범위: 원래 EF1/EF4 finite C01–C04의 남은 Sage/Singular·Lean 증명 snapshot. claim_tier: C0. transfer_source: none. scientific_admission: HOLD. 이 패키지는 전체 해석적 정리나 물리·관측 적용을 허용하지 않는다.

과학 계약 `058da4a8716fd06bc67100b8490df88a6783b780ac0ff66bf1221a02ab7e8741`과 frozen `cas_gate.py`를 변경하지 않았다. 기존 completion_20261003/RETURN.json의 STOP_BUDGET, aggregate/review NOT_RUN과 역사적 비용은 그대로이다. 원래 GR01 Lean lifecycle, GR11/C01, 별도 GR13/C04 review launch와 R9는 변경하지 않았다.

Sage/Singular: 독립 native 작성 후 두 실패를 보존했다. 첫 Singular 실행은 오류를 stdout에 출력하면서 exit 0을 반환했고 최초 PASS는 무효이다. 두 번째 실행은 sat 반환 ideal을 잘못 인덱싱해 INCONCLUSIVE였다. Host는 설치된 elim.lib 반환형을 확인하고 `[1]` 한 곳만 제거했다. 실제 Sage/Singular 실행에서 C01–C04와 SAT_EQUAL, INVERSE_PRODUCT, TWELVE_ROW_RESIDUALS가 통과했다. host_sage_api_repair/before/는 원래 소스·raw·결과를 보존하고 after/는 수정 후 실행을 보존한다. 작성자의 PROOF.md 앞부분 INCONCLUSIVE는 수정 전 기록이며 Host NOTE.md와 현재 AXIS_RESULT.json을 함께 읽어야 한다. Sage C01의 미분·투영과 C03의 순서·등호 iff는 명시된 handwritten derivation이며, 엔진은 inverse/saturation 및 exact SOS subcertificate를 검사했다. 이 모든 연결을 엔진만으로 증명했다고 기록하지 않는다.

Lean: 17개 compiler attempt의 소스와 raw를 보존했다. 최종 attempt 017은 v4.31.0 및 고정 mathlib에서 exit 0이었다. 여섯 complete theorem의 axiom 출력은 propext/Classical.choice/Quot.sound이며 sorryAx가 없다. 최종 source SHA256은 8a870e4e0178d8aa1dd1438dfb79b4764b01f05829be05c7e837f1ccc2088144이다. Kernel snapshot과 author 종료 lifecycle은 다르다. Parent는 완료 payload MESSAGE 직후 author를 interrupt했으며, terminal final과 registry closeout은 확인되지 않았다. transcript model/effort 관측은 gpt-6-sol/high이나 registry runtime은 UNVERIFIED이다. CLOSED로 기록하지 않는다.

SymPy/Wolfram: 이번에는 엔진이나 author를 재실행하지 않았다. 원래 all-true candidate의 수정된 source/raw identity를 대조하고 frozen stored-envelope checks만 실행했다. 최초 실패도 보존했다. SymPy 최초 실패 source identity는 UNKNOWN이다. candidate의 수학적 statement alignment는 독립 검토 대상으로 남겨 두었다.

실제 frozen stored adjudicate는 exit 2, primary CAS_BLOCKED, eligible=false를 반환했다. historical_aggregate_status CAS_4AXIS_PASS는 serialized envelope에서 계산한 참고 라벨이며 새 observed 4축 verdict가 아니다. frozen run-adjudicate는 네 축을 다시 실행하므로 기존 SymPy/Wolfram 재실행 금지 아래 사용하지 않았다. 독립 검토의 판정은 review/REVIEW.json과 REVIEW_REPORT.md에 별도로 기록한다.

이전 author 각 500,000 cap과 실제 SymPy 1,200,589 / Wolfram 656,286 tokens를 유지했다. 새 Sage 1,404,107 / Lean 8,325,491 cumulative total tokens에는 cached input이 포함된다. 새 planning 목표 1,600,000 / 3,200,000은 native resource_context에 연결되지 않은 soft target이었다. Lean 초과량도 보존했다. engine timeout은 실제 subprocess 경로에서 집행됐다. 통화 비용, 전체 역사적 사용량과 공유 Host 비용의 task별 배분은 NOT_MEASURED이다. old STOP_BUDGET를 다시 열거나 한도를 늘리지 않았다.

이전 Bonsai 문맥 3건/1,472 tokens와 별도로 이번 turn의 문맥 inference 2건/842 tokens를 actual inference ID/usage receipt로 확인했다. 두 문맥 candidate는 length 종료의 INCOMPLETE였고, 잘못된 HEAD/descriptor 요약은 원본 Git/runtime 기록으로 바로잡았다. local 과학 reasoning/prover LLM inference는 관측되지 않았다. Kimina의 해당 task qualification은 UNKNOWN이며 Pythagoras 대안은 NOT_ASSESSED이다. allocation이나 모델 목록을 inference나 qualification으로 취급하지 않는다.

남은 해석적 의무: smooth selected eigenfield existence/IFT, analytic spectral norm, EF6의 CAS05/06 local existence 연결. 다음 선택은 GR-CAS-05 입력 정합 대조이다. 기존 CAS05/06에는 계약이 참조하는 cubic H, displayed curvature/TOV 및 divergence 식의 누락 보고가 있어 현재 그대로 dispatch하지 않는다. NEXT_DEPENDENCY_INSPECTION.json의 다음 한 작업을 따른다.

독립 review launch cl_987ed74095c9e5a8e257c45e466ca961의 실제 runtime은 gpt-6-astra/xhigh였다. 최종 판정은 PUBLISHABLE_CONDITIONAL_MISSING_AXIS_EVIDENCE_WITH_FINDINGS이다. HIGH F1은 기존 Wolfram C04에서 실제 보존 stress의 투영과 별도 입력 Euler 식 사이의 연결 부재다. MEDIUM F2는 C01 raw boolean을 모든 미분·정규화 단계의 엔진 증명으로 확대하면 안 된다는 증거 해석 경계다. 새 Sage/Lean snapshot의 한정 게시를 권고했으나 whole-four-axis semantic acceptance=false, CAS_BLOCKED, eligibility=false, scientific HOLD와 Lean lifecycle 미확인을 유지한다.
