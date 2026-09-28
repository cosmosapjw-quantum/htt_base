# F3 정오표 — Lean kernel의 정확한 범위

게시 기준의 Lean 정리 `TypefreeLoop2.gap_column3`는 세 성분을 가진
**열 하나**에 대한 diagonal gap estimate다. 세 열 전체를 동시에 다룬
정리가 아니다. 별도 정리는 명시적 (3\times3) 행렬의
trace/STF/antisymmetric Frobenius identity를 다룬다.

따라서 기존 `RESULTS_KO.md`, `ENGINE_RUNS.json`,
`INDEPENDENT_DECISION_LOOP2.json` self-review,
`db/append_final_evidence.py`, 그리고 최종 DB의 TF-P2/`lean_mathlib`
caveat에 있는 “3열”/“3-column”은 다음으로 대체 읽는다.

> three-component single-column diagonal gap estimate, plus a separate explicit
> 3×3 Frobenius decomposition identity

이것은 문구와 provenance의 보정이며 새 kernel proof가 아니다. 기존 Lean
소스·raw transcript·DB 행·receipt는 역사 증거로 보존한다.

TF-S2/S4의 Lean 범위도 event inclusion, measure monotonicity, bounded-set
diameter event, 실수 union-bound 구성요소에 한정된다. full statistical law,
measurability, calibration, typed-unavailable branch가 하나의 전체 정리로
형식화됐다고 주장하지 않는다.
