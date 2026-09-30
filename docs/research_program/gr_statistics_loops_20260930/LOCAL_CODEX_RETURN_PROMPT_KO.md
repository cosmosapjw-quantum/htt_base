# 연구 스레드로 반환할 프롬프트

다음 빈칸을 실제 실행 결과로 채워 복붙한다. 미실행 항목은 미실행이라고 적는다.

```text
ROLE=RETURN_FROM_LOCAL_CAS
PROJECT=htt_base
TASK=GR_STATISTICS_20260930_CAS_REVALIDATION
SOURCE_PUBLICATION_COMMIT=<실제 입력 commit>
LOCAL_HEAD=<실제 검사 commit>
RUN_ID=<run_id>
RETURN_JSON=<LOCAL_CAS_RETURN.json 경로>
RAW_EVIDENCE_MANIFEST=<경로와 SHA-256>

실행한 task 및 네 축 결과:
<task별 Wolfram/xAct | SymPy | Sage/Singular | Lean/mathlib | aggregate>

실제로 닫힌 수학적 범위:
<claim별 finite algebra / analytical theorem / formal proof 범위>

새 반례·정정:
<있으면 최소 반례, 원 계약과 새 계약의 차이, 영향을 받는 claim; 없으면 없음>

미완료 및 blocker:
<수학적 실패 / 수치 불안정 / 구현 결함 / 환경·license·resource / 입력 부재를 분리>

과학적 상태:
- 기존 conditional/HOLD 변경: <없음 또는 별도 근거>
- novelty/관측 분석/Bianchi classification 승격: NO
- 실제 catalogue fit: NO
- raw failure와 이전 상태 보존: <실제 확인>

저장·게시 상태:
<로컬 파일만 / commit / push 여부, 실제 SHA와 provider acknowledgement>

이 결과를 원 계약·raw evidence·claim 범위와 대조하고, 반례가 있으면 정정부터 진행하라.
검증된 유한 성분을 전체 해석 정리나 관측 검출로 확대하지 말라.
다음 연구 또는 코드 이식에 사용할 수 있는 결과와 여전히 필요한 입력을 결정해줘.
```
