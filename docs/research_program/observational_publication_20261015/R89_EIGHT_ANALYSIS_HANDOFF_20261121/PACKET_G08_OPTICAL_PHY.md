# G08_OPTICAL_PHY | Optical 전달·cross-cov·PHY-01..07

**이 파일은 연구 작업 패킷이며 실행권한이나 START_LOCAL_AGENT 문서가 아니다.**
해당 10개 노드의 경계 안에서 source 재검증/기존 계산 재현/구체적 결과만 작성한다.
예측 소요시간: 30–120분. 이는 전체 물리 완료 시간이 아닌 계획 가정이다.

## 목표
Reuse R77 PHY theorem/geometry kernels and source-typed optical/cross-probe constraints; only advance independently supported partial cases.

## Source, blocking contracts
Finite-z Sachs/Jacobi/common-congruence transfer, photon higher moments, independent normal-frame sources and joint cross-source covariance/null unavailable
STOP: No spontaneous construction of physical transfer, cosmic Pi/G_F, joint independent null, or physical cross-paper confirmation

## 원본 R78 노드 및 판정
- SQ-PHOTON-FLUX | R78=blocked_source | action=NO_FULL_SCIENCE_EXECUTION | preflight=True
- PHY-02 | R78=theory_verified_physical_data_pending | action=THEORY_ONLY_EXTERNAL_DATA_PENDING | preflight=True
- SQ-OPTICAL | R78=pending_conditional | action=NO_FULL_SCIENCE_EXECUTION | preflight=True
- PHY-01 | R78=theory_verified_physical_data_pending | action=THEORY_ONLY_EXTERNAL_DATA_PENDING | preflight=True
- PHY-05 | R78=theory_verified_physical_data_pending | action=THEORY_ONLY_EXTERNAL_DATA_PENDING | preflight=True
- PHY-06 | R78=theory_verified_physical_data_pending | action=THEORY_ONLY_EXTERNAL_DATA_PENDING | preflight=True
- PHY-03 | R78=theory_verified_physical_data_pending | action=THEORY_ONLY_EXTERNAL_DATA_PENDING | preflight=True
- PHY-04 | R78=theory_verified_physical_data_pending | action=THEORY_ONLY_EXTERNAL_DATA_PENDING | preflight=True
- PHY-07 | R78=theory_verified_physical_data_pending | action=THEORY_ONLY_EXTERNAL_DATA_PENDING | preflight=True
- SQ-CROSS-COV | R78=pending_dependency | action=NO_FULL_SCIENCE_EXECUTION | preflight=True

## 그룹 간 선행 패키지
G02_CF4, G03_GAIA, G04_RADIO_FRAME, G05_PLANCK, G07_BIANCHI
그룹 간 edge는 기존 R78의 hard edge 및 qualification overlay를 그대로 인용한다. 그룹의 numerical preflight가 완료되었다고 선행 과학 노드가 완료된 것은 아니다.

## 기존 코드 및 테스트
- code: htt/obsstat/analysis_lane.json
- code: htt/obsstat/phy_fast.py
- code: htt/obsstat/pre_dag_fast.py

최소 회귀 검증 명령 (기존 checkout):
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r81_phy_fast.py tests/obsstat/test_r85_p5p6_fast.py

## 새 결과 작성 경계
- 허용된 분석군별 결과 공간: docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G08_OPTICAL_PHY/
- 원래 R78/R86/R87/R88 원본 DAG, raw source, published result, main, 기존 미추적 사용자 파일은 변경 금지.
- 실제 계산이 필요하면 해당 원본 runner의 argv/입력/생성물 소유권을 먼저 확인하고 명시된 한정 범위에서만 실행. 코드 확장은 작은 실제 버그 수정 외에는 수행하지 않는다.
- 기존 완료된 증거는 정확한 source ID로 재사용하고 반복 전체 계산은 생략.
- 출력: node별 {NOT_ATTEMPTED, REUSED_SCOPED, DIAGNOSTIC_COMPLETED_SCOPED, BLOCKED_INPUT, BLOCKED_DEPENDENCY, FAILED} 구분, 변경 파일, 테스트 명령·결과, source SHA, 남은 물리 결측, 다음 실제 조치.
- 절대 full 60-node science complete, true physical Pi, Bianchi family identified, release-matched null PASS, local agent START를 주장하지 않는다.
