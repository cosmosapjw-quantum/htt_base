# Type-free Loop 2 correction and scoped closeout

이 디렉터리는 게시 기준 `de3ab20219c46c2b14f1d2ec6bb87508c331634d`에
대한 additive correction이다. 기존 `typefree_loop2_20260928/`, 원 ZIP,
SQLite/gzip, raw engine transcript와 receipt를 덮어쓰지 않는다.

- `ERRATA_F1_W1_KO.md`: 무제약 선형/affine domain과 일반 feasible set을 구분한다.
- `ERRATA_F3_LEAN_SCOPE_KO.md`: `gap_column3`의 단일 열 범위를 바로잡는다.
- `db/safe_append.py`: source 불변·alias 거부·preflight reservation을 갖춘 후속 migration이다.
- `EXTERNAL_AUDIT_RECORD.json`: 제공된 원 감사의 해시·판정·F1–F4를 고정한 closeout record다.
- `INDEPENDENT_REVIEW_STATUS.json`: fresh reviewer가 등록됐지만 실행되지 않은 경계를 기록한다.
- `PR_DISPOSITION.json`, `ISSUE_DISPOSITION.json`: 분류와 실제 원격 처리를 분리한다.
- `CLAIM_CLOSEOUT.json`: 출처, 수기 유도, 형식화, 실행 admission, 관측 admission을 분리한다.

이 패키지는 `claim-tiered observational/statistical framework`의 제한된 이론
정오표다. native solver 결과, family-level identification, MIO-owned posterior,
또는 관측 검출을 주장하지 않는다.
