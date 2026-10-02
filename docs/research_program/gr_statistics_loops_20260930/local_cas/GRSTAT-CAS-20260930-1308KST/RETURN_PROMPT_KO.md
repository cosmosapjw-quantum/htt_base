# 연구 스레드 반환 프롬프트

```text
ROLE=RETURN_FROM_LOCAL_CAS
PROJECT=htt_base
TASK=GR_STATISTICS_20260930_CAS_REVALIDATION
SOURCE_PUBLICATION_COMMIT=11602167b64e4f0c50c1f57c37fe9df2292f9725
LOCAL_HEAD=11602167b64e4f0c50c1f57c37fe9df2292f9725
RUN_ID=GRSTAT-CAS-20260930-1308KST
RETURN_JSON=/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/LOCAL_CAS_RETURN.json
RAW_EVIDENCE_MANIFEST=/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/RAW_EVIDENCE_MANIFEST.json SHA-256=cf902736a422ca81673f02be74f9d537d9ab5150f4f0ede3fb613741be73280b

실행한 task 및 네 축 결과 (Wolfram/xAct | SymPy | Sage/Singular | Lean/mathlib | aggregate):
CAS-01 | PASS | PASS | PASS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-03 | PASS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-10 | PASS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-14 | PASS | MISALIGNED_ASSUMPTIONS | PASS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-15 | PASS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-05 | PASS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-06 | PASS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-04 | PASS | MISALIGNED_ASSUMPTIONS | PASS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-02 | PASS | PASS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-07 | PASS | PASS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-17 | PASS | PASS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-08 | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-09 | PASS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-11 | FAIL | MISALIGNED_ASSUMPTIONS | PASS | MISALIGNED_ASSUMPTIONS | CAS_FAIL
CAS-12 | PASS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-13 | PASS | MISALIGNED_ASSUMPTIONS | PASS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT
CAS-16 | PASS | MISALIGNED_ASSUMPTIONS | PASS | MISALIGNED_ASSUMPTIONS | CAS_CONFLICT

실제로 닫힌 수학적 범위:
- 17개 계약 모두 네 축의 실제 실행을 관찰했다. 계약 전체의 statement-faithful CAS_4AXIS_PASS는 0개다.
- CAS-13-C04의 양의 구간 상대 minimax 정리는 Lean 4.31/mathlib에서 sorryAx 없이 증명됐다. 다른 축의 C04 PASS 검사는 끝점 항등식 또는 더 약한 부등식에 머물러, 네 축 닫힘이나 일반 real p>4 정리로 승격하지 않는다.
- 여러 유한 대수 항등식의 축별 검사 결과는 RETURN_JSON과 원시 로그에 보존했다. 계약 단위 수학적 닫힘은 주장하지 않는다.

새 반례·정정:
- CAS-03-C03: D=diag(1,1,-2)는 det(D)=-2로 가역이나 H=tr(D)/3=0이다. 원 계약의 잘린 역행렬 식은 H^2로 나누므로 해당 영역에서 정의되지 않는다. 정확한 역행렬 관계의 반례는 아니다. 원 게시 계약은 수정하지 않았고 CAS-03/CORRECTION.md에 차이를 기록했다.

미완료 및 blocker:
- CAS-11 Wolfram은 RecursionLimit로 결과를 내지 못했고 wrapper는 JSON 표식 부재를 list index out of range로 보고했다. CAS_FAIL은 실행/구현 실패이며 수학적 반례가 아니다.
- CAS-01의 Wolfram 검사는 u를 rest frame으로 고정했고, Singular 호출은 구면 ideal 생성자를 자기 ideal로 환원한다. CAS-13-C04의 Sage/SymPy/Wolfram PASS도 전체 minimax 하한을 각각 증명하지 않는다. HOST_FIDELITY_FINDINGS.md 참조.
- CAS-03 slope family, CAS-08 네 판정 기준 등 일부 입력/정의가 계약·허용 명세에 부족하다. Lean은 CAS-13-C04 외 성분의 전체 증명을 완료하지 않았다. 각 계약의 추가 해석적 의무도 남아 있다.
- 등록한 독립 Astra/xhigh 읽기 전용 검토자는 CLIENT_INHERITED_SANDBOX_MISMATCH로 실행이 거부됐다. 독립 검토 완료를 주장하지 않는다.

과학적 상태:
- 기존 conditional/HOLD 변경: 없음. 원문 39개 SHA-256 일치, 기존 실패 기록 및 HOLD 보존.
- novelty/관측 분석/Bianchi classification 승격: NO
- 실제 catalogue fit: NO
- raw failure와 이전 상태 보존: YES

저장·게시 상태:
- 로컬 결과 파일만 저장. commit: NO; push: NO; 원격 게시 확인: 해당 없음.

이 결과를 원 계약·raw evidence·claim 범위와 대조하고, CAS-03 반례에 대한 계약 정정을 먼저 결정하라. 검증된 유한 성분을 전체 해석 정리나 관측 검출로 확대하지 말라. 다음 연구 또는 코드 이식에 사용할 수 있는 결과와 여전히 필요한 입력을 결정해줘.
```
