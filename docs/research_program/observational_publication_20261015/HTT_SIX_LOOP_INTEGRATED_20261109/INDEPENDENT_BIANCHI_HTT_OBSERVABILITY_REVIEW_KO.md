# R48-T23 Bianchi → HTT 관측가능성 mock 검토 (독립성: NOT_RUN)

날짜: 2026-11-11. **이 검토는 mock/DAG를 작성·정리한 같은 세션의 에이전트가 수행했으므로 "독립 검토"가 아니다.** 실제 독립 reviewer 에이전트 ID와 반환 산출물이 없으므로 DAG의 독립성 요건은 NOT_RUN으로 둔다. 아래는 재유도·재실행으로 확인한 사실과 발견된 결함이다.

## 확인된 사실 (재유도/재실행)
- 정확한 head `707f01bca`에서 compileall exit 0, `tests/r48` 5개 + `htt/bass/diagnostics` 49개 = 54개 통과 (Python 3.12.3).
- mock을 기록된 seed 20261109 / 30000 / 12000 / 512로 재실행: committed `BIANCHI_FIVEVAR_MOCK_REPORT.json`의 부동소수 값 27개 전부가 1e-9 상대 오차로 일치. 단, committed JSON의 key 배치가 스크립트 출력과 달라 변환 단계가 문서화되어 있지 않다.
- 구조 상수 `C^c_ab = ε_abd n^dc`에서 Koszul 접속을 만들어 (metric 호환·torsion-free를 assert) class A 운동량 구속과 3-Ricci를 독립 계산:
  - 3-Ricci 고유값은 mock의 `ricci_A`와 6개 type(I, II, VI0/VII0-like, VIII-like, IX(1,1,1), IX(2,1,1)) 모두에서 정확히 일치. 선택된 II/IX 쌍은 `[-0.5,-0.5,0.5]` 대 `[0,0,2]`로 다르다.
  - 운동량 구속은 mock `momentum_A`가 유도값의 **부호만 반대**(차이 8.9e-16). 구조 상수 방향·K_ab 부호 규약에 의한 부호 문제이며, 커널(1,1,1)·rank·II/IX 동일 M 같은 구조적 결론은 부호와 무관하다. 부호가 들어가는 양(β_NM의 부호)을 문헌과 비교하기 전에 규약을 선언해야 한다.
  - det J_B 닫힌 꼴과 J_A의 커널 (1,1,1)은 기호 계산으로 정확, 일반 rank는 2와 3.
  - tilt 역변환 `Γ²β=|M|/w`는 1.7e-14 이내.
  - 곡률 oracle의 label 정보량: 적분 0.47976 nats, Monte Carlo 0.47993, mock 보고값 0.47892 (MC 오차 범위), MAP 정확도 0.9121 대 0.9122.

## 발견된 결함
- **T23-D1 (PROVENANCE)**: mock 출력의 `verification` 블록이 하드코딩되어 있다 (`python: 3.13.5`, `local_pytest: 5`, `local_pytest_status: PASS`). 이번 실행은 Python 3.12.3이고 스크립트는 테스트를 실행하지 않는다. 실행하지 않은 통과와 버전을 단정하는 필드이므로 수정 대상(별도 브랜치).
- **T23-D2 (PROVENANCE)**: committed 결과 JSON과 스크립트 출력의 구조 차이(R45/R46과 동일 패턴).
- **T23-D3 (THEORY, 표기)**: 운동량 구속 부호 규약이 mock과 문서에 선언되어 있지 않다.

## 한계 / 유지되는 상태
- 곡률 센서는 이상화된 oracle이며 (σ²=0.375) 실제 곡률 측정이 아니다. 노이즈를 2배로 하면 MAP 정확도가 0.75로 떨어진다 (BIANCHI_OBSERVABILITY_SENSITIVITY_REPORT.json).
- 응답 척도 1.25/0.80은 mock 상수이며 보정값이 아니다.
- class B(V/VIIh)는 sweep하지 않았다. 프레임 닫힘 `β_RO=0`은 collinear 역 boost에서만 성립하며 여기서 재유도하지 않았다.
- GitHub Actions 상태와 broad PR04 테스트는 이번에 확인하지 않았다.
- 어떤 claim도 승격하지 않는다 (claim ceiling C0).
