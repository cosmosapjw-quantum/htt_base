# MES R4 재현 패킷

읽기 순서:
1. MES_R4_REPORT_KO.md — 결과와 사용 범위.
2. INDEPENDENT_REVIEW.md — 실제 독립 판정 및 검토 대상 해시.
3. closure_derivation.md — Lie 구조상수·metric·tilt jet의 상세 유도.
4. verification/ — Wolfram 입력과 수정 전/후 실제 출력.
5. state/RESEARCH_STATE.json, RESEARCH_DAG_AND_NEXT_PROMPT_KO.md — 열린 조건과 다음 bounded 작업.

이 패킷은 이론 유도와 lightweight CAS의 결과다. 새 실제 관측 percentage, catalog fit, cosmological ODE/PDE/Boltzmann evolution, 생산 코드 변경은 포함하지 않는다. 실제 관측으로 기준보다 좁은 구간을 얻는 목표는 unresolved로 남아 있다.

기하학적 정상 congruence 결과와 일반 tilted/local-observable 결과는 조건이 다르다. 특히 normal branch의 A=ω=0, Gaia의 reference-spin convention, β의 값과 βdot를 혼동하지 않는다.

MANIFEST.sha256은 이 패킷의 각 파일 identity다. Scientific validity는 유도와 독립 판정이 담당한다. 원 R3 입력은 inputs/R3_REPORT_KO.md로 보존한다. 원 repo는 지정된 commit에서 읽기만 했으며 native pending/assignment나 production branch를 변경하지 않았다.
