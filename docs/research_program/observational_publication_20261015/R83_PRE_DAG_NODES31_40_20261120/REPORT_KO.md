# R83 C10 | R78 31–40번 pre-DAG coding closure, 2026-11-20

**Outcome:** SOURCE_CONDITIONAL_SOFTWARE_PREPARATION_VERIFIED_AND_R83_C9_C10_SEALED. 이는 R78 L03/L04, H02 또는 출판 과학 주장의 완료가 아니다. 기존 R78 60개 node / 129개 edge / 원래 42개 science payload SHA256 e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d 및 NEXT_ID SQ-CF4 유지. Owner는 stage-scoped Git push를 승인했으며 무관한 dirty/untracked 파일을 보존한다.

## 1. 재개한 미완성 R83의 정확한 범위

R83 C1–C8까지는 기존 브랜치에 이미 공개돼 있었고 C9/C10 Git commit, C9_REVIEW, C10_NODE_MATRIX, PROVENANCE, REPORT, HANDOFF가 없었다. 로컬에 남아 있던 tests/obsstat/test_r83_p2p3_fast.py의 **추가 3개 테스트**는 원래 12개 source 테스트를 확장하여 Planck L03 파일의 8개 동일 ID-paired pilot, H03 독립 실행 CLI, 인증되지 않은 Fortran 캐시 바이너리 처리에 대한 회귀를 도입했다. 별도 미추적 scripts/r83/run_h03_fast.py는 source SHA를 확인하고 실제 원래 35,970 CF4 source를 읽어 네 창의 4×9 계수와 전체 36×36 working covariance를 비교하는 create-only preflight였다. 두 변경 모두 R83 scope에 해당하고 수치 검산 후 **C9 scoped commit** ea1e5b11f8cde9a5cffdb23bd749e006415e3b4d에 포함했다. 다른 미추적 데이터·코드 및 원래 R78/Planck 원본 파일은 건드리지 않았다.

기계 판독 노드별 정본: C10_NODE_MATRIX.json. Ordinal 31=S06, 32=L01, 33=L02, 34=L03, 35=L04, 36=L05, 37=L06, 38=H01, 39=H02, 40=H03. S06/L06은 paper gate HOLD, L01/L02는 기존 Planck source-conditional scoped evidence, L03–L05는 동일 pilot ID와 rank/tie/negative-control 계산만, H01/H03은 원본 CF4 working angular estimator, H02는 true PV/selection/calibration covariance가 별도 필요하다. 원래 과학 상태는 어떠한 것도 변경하지 않았다.

## 2. 검증한 물리·수치 식과 원자료

동일 group-source CF4 35,970개, original z centers (.025,.040,.060,.080), Gaussian Δz=.012, 9D signed STF5 H03 source design X, observational response y=cz (c=299792.458 km/s). Diagonal working scatter sigma_i와 각 창 w_ij 아래:
\[
F_j=X^\top\operatorname{diag}(w_j)X,\quad
b_j=X^\top\operatorname{diag}(w_j)y,\quad
C_{jk}^{\mathrm{working}}=F_j^{-1}X^\top\operatorname{diag}(w_jw_k\sigma_i^2)XF_k^{-1}.
\]
공유된 동일 35,970 source의 cross-window block을 포함한 36×36 covariance이며 **네 독립 sky / 독립 four-window likelihood는 아니다**. H03 원래 archived 4×9와 C36를 재검산했다. 새 C9 standalone CLI는 인증된 Fortran12를 선택해 archived theta 최대 절댓값 차이 4.203970505045618×10^-11 km s^-1 Mpc^-1, C36 차이 1.054989429150055×10^-13 (km s^-1 Mpc^-1)^2, cross-window first 9×9 block norm >0.1을 확인했다. C8의 원래 QR 대비 5.64× core benchmark와 **CLI 통합 측정 시간은 비교 범위가 다르다**. 이번 CLI 한 번의 kernel call 시간 0.009872226s은 새 기록으로만 보존한다.

Planck 실제 L02에는 same physical sky T/E/B field 25 rows 및 24 within-sky product comparisons가 있다. L02의 B axial STF chirality는 O(3)-even이므로 음수 부호를 그대로 유지하고 T/E의 O(3)-odd chirality와 혼동하지 않는다. L03의 8개 FFP pilot paired simulation ID × 5 processing variant=40 rows는 **독립 40 MC가 아니다**. 한 pilot pair를 pseudo-observation으로 두고 나머지 7개를 rank denominator로 계산한 1/8 resolution은 계산 구조의 테스트이고 Planck 실제 anomaly p값이 아니다. physical_p_value=None, genuine source-matched T/E/B null은 미확보로 유지한다.

## 3. 신선한 C9 검증 결과

- 기존 Git HEAD에서 추출한 원 R83 테스트: 12 PASS / 0 FAIL.
- 로컬에서 발견된 추가 테스트 포함 R83: 15 PASS / 0 FAIL.
- 새 R83 + 원 H03 세 개 source suite + L02 original statistic + L03 original apply family의 여섯 파일: **50 PASS / 0 FAIL**.
- source input C7 hash 전부 실제 byte SHA와 일치, 원본 C7 historical result를 재생성해 덮어쓰지 않음.
- C9 standalone run_h03_fast --output은 /tmp에 새 파일로만 출력, 원래 archive, 원래 selected source, science R78는 수정하지 않음.
- R78 validate_unified.py --strict-authority: 32/32 PASS.
- Cached Fortran/source SHA 실패 때 안전한 NumPy fallback과 source-specific code test PASS.
- Full repository clean checkout 및 실제 Planck full end-to-end calibrated MC는 NOT_RUN. 이번 C9는 기존 원본·추가 테스트가 한 로컬 checkout에서 실행된 수치 준비 검증이다.

## 4. C10 판단, 남은 데이터 의존 및 인계

**코딩 준비 패키지 R83의 31–40번 노드는 C9/C10 봉인**을 수용한다. 그러나 L03 matching null 부재, H02 real correlated source C, S06/L06 paper gate 미해결을 그대로 유지한다. R78의 SQ-CF4 ready_scoped도 source-lineage bounded diagnostic의 자격이지 source-PV/selection/zero-point covariance와 heldout을 이미 완성했다는 뜻이 아니다. C10은 R83 C10_NODE_MATRIX.json, PROVENANCE.json, REPORT_KO.md, HANDOFF_KO.md와 기존 PLAN_KO.md에 보존된다. R86 readiness overlay에서는 R83 10-node 코드 stage만 6/6 sealed로 갱신하고 BLOCK_LOCAL_AGENT_START를 유지한다. P0-B SQ-CF4 물리 covariance/heldout, P0-C 60-node fail-closed read-only packet adapter는 다음 단계에서 별도로 실제 수행해야 한다.

**완료 기준의 정확한 경계:** source-conditional H03 4×9/C36 + Planck signed T/E/B pilot bookkeeping and calibrated native fallback 구현은 scoped implementation-verified; full physical GR/kinetic and cosmological hypothesis significance remains unresolved. 물리적 판정의 PASS나 출판 제출을 생성하지 않는다.
