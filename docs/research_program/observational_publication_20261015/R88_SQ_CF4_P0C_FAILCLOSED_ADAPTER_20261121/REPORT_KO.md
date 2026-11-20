# R88 | P0-C: R78 60-node SQ-CF4 읽기 전용 실행 계약 어댑터

2026-11-21 KST. **Software P0-C COMPLETED_SCOPED; science SQ-CF4 BLOCKED_INPUT; agent START 금지 유지.**

## 코드와 실행 계약

- 구현: scripts/r88/run_p0c.py. 사용자 선택 --node SQ-CF4 --dry-run만 허용하고 소스 검사 후 JSON 패킷을 표준출력으로만 출력한다. 실제 데이터 분석, subprocess, worker/agent dispatch, 파일 기록, science DAG state 변경 기능은 없다.
- 원본 science SSOT: R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json SHA-256 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11; 역사적 42-node payload SHA-256 e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d.
- readiness overlay: R86_PRE_EXEC_READINESS_20261120/EXECUTION_READINESS_DAG.json SHA-256 2f6cb20f541100d5db8d53a1745ad627e5729e83afff48e4585745a56b30a467. R87 actual source result SHA-256 c357670dadaada250f75f3a41959d712add11b3d4c45f00bfbc46f4dc3fdc199. Parent checkout HEAD 73906628b1fd9777af66c532cc00373d80f0460f.
- 60 unique IDs, 129 hard edges, 유효 위상 순서, 42+11+7 분류, R86 original node/edge 동일성, 기존 42 science state, E1/X01/H01 predecessor completed_scoped, R79-R85 여섯 C10 SHA seal 및 R83 10-node 봉인을 확인한다. B02, S02, SQ-GAIA, 미등록 노드, 다른 observer frame, source SHA drift는 fail-closed. 그래프 전체를 자동 실행할 수 없다.
- CF4 원자료 table3, table4, ReadMe 및 35,970 selected groups NPZ의 pinned SHA-256을 현재 장치에서 다시 계산해 모두 일치함을 확인했다. 파일이 없으면 MISSING_BLOCKED_INPUT으로 남기며, 존재하지만 바이트가 변경됐으면 패킷 생성을 거부한다. 방향은 ICRS J2000, 적색편이는 CMB frame이다. normal-frame optical transport를 적용하지 않는다.
- R87에서 검증된 38,053 released / 35,970 selected groups, 7 methods, 926 original overlaps, 922 error-bearing multi-method groups, residual method network rank 5를 source 진단으로만 읽는다. Published moduli는 이미 global MCMC intercalibration을 거쳤기 때문에 group-disjoint RA heldout을 upstream independent null로 승격하지 않는다.
- 필요한 physical covariance C=N_stat+S_PV+J_cal Sigma_cal J_cal^T+C_selection. 뒤의 세 항 및 upstream-independent heldout/coverage가 결측이므로 해당 항, qualified null, physical Pi는 null, 최종 패킷 status는 BLOCKED_INPUT. N_stat는 조건부 working diagonal이다.

## 실제 실행·검증

재현 명령 (repo root):

    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/r88/run_p0c.py --node SQ-CF4 --dry-run

- 새 P0-C 및 R86 unit: **32 passed**, 0 failed.
- R79–R88 관련 9개 테스트 파일: **146 passed, 10 skipped**, 0 failed. 전체 repository CI는 아니다.
- R78 strict authority: **32/32 checks PASS**. R86 read-only audit: 60 nodes/129 edges/C10 6-of-6 sealed, agent BLOCKED_NOT_DISPATCHED.
- 부정 테스트: R78/R86 SHA 위조, table3 source byte drift/missing, R83 C10 seal 위조, 부적절한 frame, B02/S02/unknown node, --dry-run 누락, hard edge 변조, 파일 기록 여부.
- 이는 한정된 software integrity·실행 경계 검증이지 실제 물리적 covariance/null acceptance가 아니다. 독립 native subagent review는 현재 호스트에서 NOT_RUN으로 기록한다.

## 다음 단계

R78 science NEXT_ID는 **SQ-CF4 그대로**다. 완전한 물리학적 게이트에는 pre-intercalibration zero-point posterior/Jacobian, 독립 source-matched PV covariance/field realizations, survey selection law, upstream-independent heldout/mock null이 필요하다. 결측을 유지할 경우 R78이 이미 정한 다른 source-ready frontier인 **SQ-GAIA**의 한정 source 진단으로 넘어가는 것이 가능한 다음 실제 연구 단계다. P0-D ID를 임의로 생성하거나 60-node local agent START를 발행하지 않는다. R78/R86/R87 원본, 역사적 42 science states, main 및 원자료는 변경하지 않는다.
