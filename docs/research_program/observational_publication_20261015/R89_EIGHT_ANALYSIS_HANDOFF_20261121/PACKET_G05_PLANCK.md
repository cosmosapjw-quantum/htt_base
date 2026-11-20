# G05_PLANCK | Planck 저다중극·FFP null

**이 파일은 연구 작업 패킷이며 실행권한이나 START_LOCAL_AGENT 문서가 아니다.**
해당 7개 노드의 경계 안에서 source 재검증/기존 계산 재현/구체적 결과만 작성한다.
예측 소요시간: 30–180분. 이는 전체 물리 완료 시간이 아닌 계획 가정이다.

## 목표
Reuse L01/L02 signed-parity/processed-variant response and existing eight paired FFP pilot ID tests; classify what real release-matched null is missing.

## Source, blocking contracts
Existing same-sky processing/pilot FFP products; full release-matched Commander T/E/B exchangeable signal+noise+foreground null unavailable
STOP: Do not count nine processing variants as independent skies or eight pilot FFP pairs as a calibrated release-matched null; no rarity/p-value promotion

## 원본 R78 노드 및 판정
- L01 | R78=completed_scoped | action=REUSE_SCOPED_PRIOR_EVIDENCE | preflight=True
- SQ-CMB-NULL | R78=blocked_source | action=NO_FULL_SCIENCE_EXECUTION | preflight=True
- L03 | R78=pending | action=NO_FULL_SCIENCE_EXECUTION | preflight=True
- L02 | R78=completed_scoped | action=REUSE_SCOPED_PRIOR_EVIDENCE | preflight=True
- L04 | R78=pending | action=NO_FULL_SCIENCE_EXECUTION | preflight=True
- L05 | R78=pending | action=NO_FULL_SCIENCE_EXECUTION | preflight=True
- L06 | R78=pending | action=NO_FULL_SCIENCE_EXECUTION | preflight=True

## 그룹 간 선행 패키지
G01_COMMON
그룹 간 edge는 기존 R78의 hard edge 및 qualification overlay를 그대로 인용한다. 그룹의 numerical preflight가 완료되었다고 선행 과학 노드가 완료된 것은 아니다.

## 기존 코드 및 테스트
- code: htt/obsstat/analysis_lane.json
- code: htt/obsstat/p2p3_fast.py
- code: htt/obsstat/pre_dag_fast.py

최소 회귀 검증 명령 (기존 checkout):
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r83_p2p3_fast.py tests/obsstat/test_pre_dag_fast.py

## 새 결과 작성 경계
- 허용된 분석군별 결과 공간: docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G05_PLANCK/
- 원래 R78/R86/R87/R88 원본 DAG, raw source, published result, main, 기존 미추적 사용자 파일은 변경 금지.
- 실제 계산이 필요하면 해당 원본 runner의 argv/입력/생성물 소유권을 먼저 확인하고 명시된 한정 범위에서만 실행. 코드 확장은 작은 실제 버그 수정 외에는 수행하지 않는다.
- 기존 완료된 증거는 정확한 source ID로 재사용하고 반복 전체 계산은 생략.
- 출력: node별 {NOT_ATTEMPTED, REUSED_SCOPED, DIAGNOSTIC_COMPLETED_SCOPED, BLOCKED_INPUT, BLOCKED_DEPENDENCY, FAILED} 구분, 변경 파일, 테스트 명령·결과, source SHA, 남은 물리 결측, 다음 실제 조치.
- 절대 full 60-node science complete, true physical Pi, Bianchi family identified, release-matched null PASS, local agent START를 주장하지 않는다.
