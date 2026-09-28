# R4 claim-source ledger

고정 handoff H = `5702024e06eff4979087f07f86ee7131d13961ac`.
병렬 affine branch P = `5a3825f903546891fd90e3d708481707d59babf4`.
각 source의 exact Git blob/byte/SHA-256은 `read_ledger_v4.json`에 있다.

| ID | 주장 | source·근거 | 근거의 한계 |
|---|---|---|---|
| H01 | 2,003개 평탄화 tree 목록, 18,885 고유 blob | census/history_census_summary.json, history_tree_receipts.json, delta_verification.json | 고정 182 refs의 관측 이력; raw Git tree modes 미보존 |
| H02 | 신규 51·누적 213 전문 읽기 | coverage.json, read_ledger_cumulative.json | 부분·delta-only 제외; 독립 재독 중복 제외 |
| G01 | v8 signed quotient 수리 | H: egs3_gf_interval_v8.py, gf_interval_v8_seal.json | affine box·독립 잔여구간·양수 분모 |
| G02 | v9 zero-endpoint/T2G 수리 및 실제 caller | H: egs3_fractional_program.py, run_egs3_v9_seals.py, Makefile, ticket | 일반 관측 feasible set·coverage는 별도 |
| G03 | 별도 exact LP witness 존재 | H: sage/egs3_v9_fractional.sage, fractional_program_sage_seal.json | 저장 3 fixtures/15 checks; 미재실행 |
| C01 | 공유 correlated mocks 존재 | H: cf4_forward_simulator.py, cf4_growth_covariance.py, pr148_joint_covariance.json | 설정 생성모형의 covariance |
| C02 | affine GLS·full C·trace 제거 rank | P: cf4_current_stack.py, test_cf4_current_stack.py, observed runner | fixed design·known SPD C 조건부; 관측 실행 미확인 |
| C03 | score(0)로 MLE 판정 실패 | H: cf4_growth_covariance.py: amplitude_mle; 직접 유도 | 실제 CF4 영향 크기는 미계산 |
| C04 | 유한 U와 objective branch bound | 직접 유도, 독립 수학 검토 기록 | floating point enclosure 필요; 위치오차 인증 아님 |
| C05 | nested WLS 차의 crosscov·rank 문제 | H: compare_vectors, run_pr145_velocity_estimators.py, pr145_bulk_flow_report.json | 고정 공통 W·표본·설계에서 rank≤1 |
| C06 | 405 주변 출력 거부 | H: run_pr145_velocity_estimators.py:134 | 분기 존재 확인; 재시도·조작 증거 없음 |
| C07 | toy grouping과 실제 likelihood의 차이 | H: cf4_forward_simulator.py, pr146_coverage_report.json | 이 toy 결함은 P의 affine operator에 전가하지 않음 |
| C08 | Gaussian/Bonferroni 구간의 coverage 미확인 | H: pr148_fsigma8_by_depth.json, pr148_growth_difference_bound.json 및 source | 저장 숫자; 관측 coverage 보증 아님 |
| C09 | current-stack 관측 execution 미확인 | P의 runbook·lane registry·PR313, 별도 ref PR291 receipt/PR314 audit | 외부 output directory·임의명 모든 JSON 미검색 |
| N01 | N1/N4의 문헌·정의 귀속 미일치 | H: A14_N1/A14_N4 + 외부 원논문 | 유사 저자 연구가 존재하나 적힌 제목/값에 귀속 불가 |
| N02 | 대칭 scan profile의 full-sky dipole=0 | antipodal parity의 직접 증명 | 실제 WISE 완전대칭 주장 아님 |
| N03 | N2 생성 Cov=0, metadata rho=.3 | H: mask_leakage.py; 조건부 독립성 증명 | fixed baseline·fixed contamination |
| N04 | N5 rho parameter는 sampling 제어 안 함 | H: clustering.py | 실제 A_common 공유 상관은 존재 |
| N05 | saturated proxy와 공통 beta likelihood 불일치 | H: runner.py, 선형 Gaussian projection 증명 | 실제 BF에 대한 일률 상계 주장 아님 |
| N06 | Pi proxy는 MES posterior 아님 | H: runner.py, common_interface.py | 해당 proxy classifier trigger rate는 정의됨 |
| N07 | union product는 일반 보수 상계 아님 | H: common_interface.py; 배반 사건 반례 | family 분포들의 joint 실험 정의 필요 |
| N08 | PR062의 mock별 union 진전과 경험적 응답 | H: selection_response_depth.py, survey_axis_coherence.py | 관측 selection/covariance 값 평가 없음 |
| R01 | bandpass·redshift boundary가 응답에 필요 | 외부 원문과 직접 선형 전개 | local boost·표본 경계 정의역 |

보존 source의 status 라벨만을 이유로 과학적 판정을 부여한 항목은 없다.
