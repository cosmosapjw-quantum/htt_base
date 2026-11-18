# R68 • 물리적 설명을 중심으로 재구성한 5변수 연구

2026-11-18. 기반: htt_base R67 commit 8089721e9ba74d79dadbb53d3158a5f76e9f96bf.

- THEORY_AND_PROOFS_KO.md: 아홉 경로의 발산적 재구성, 여덟 개의 수리통계·기하학 정리와 증명, 일곱 연구 주제 특화, 관측량의 물리적 의미론.
- TOPIC_SPECIALIZATIONS.json: 일곱 연구 주제별 x/Q/Π/F/G_F의 대상, 단위·framing·null law·필수 데이터 상태.
- R68_NUMERICAL_CHECKS.json: 실제 R66 finite-band PR3/PR4 radiation stress의 positive-cone gauge 및 signed shape, 별도 white STF5 Gaussian 85,000개에서 unknown-axis null.
- scripts/r68/fiveview_geometry.py: 기하 계산, 선형 target 식별 안정도, nuisance score profile, transport covariance, source-checked R66 readout.
- tests/test_r68_fiveview_geometry.py: 구현·기하 및 취약한 경계 조건 14개 focused regression.
- REVIEW/independent_read_only_review.md + REVIEW/review_closure.json: 1회 독립 검토 NEEDS_REPAIR, 후속 4건 부모 소유 한정 수리 후 표적 검증. 두 번째 독립 심사 PASS는 주장하지 않음.
- PROVENANCE.json + VALIDATION.md: 기준 commit, R66 입력 byte identity, 코드 identity와 성공/제약 기록.

결론: 다섯 뷰의 임의 재표현은 full likelihood 정보를 늘리지 못한다. 실제 개선은 signed 정보를 잃는 축약보다 손실을 회복하거나, 새로운 관측 응답으로 nuisance kernel을 제거할 때만 발생한다. 물리적 explanation에는 radiation positivity Q, orbit shape, frame-covariant depth, nonregular Π와 명시적인 occupancy F가 기여한다. 기존 P1–P6 DAG와 투고상태는 변경하지 않음.
