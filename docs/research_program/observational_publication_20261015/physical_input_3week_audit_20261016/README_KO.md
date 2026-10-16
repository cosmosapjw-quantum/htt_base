# HTT 3주 PR·공개 물리 입력 수용조건 연구 아카이브

일자: 2026-10-16 KST. SSOT: `cosmosapjw-quantum/htt_base` branch `research/htt-sixpaper-physical-input-gates-audit-20261016`; parent `c352bcfbf4d77b4a9bffc5c109b34d6cb01bff9e`.

- `PHYSICAL_INPUT_RESEARCH_KO.md`: 7개 gate의 수학·관측·수용조건 연결, 75개 PR metadata 전수와 선택적 코드 재사용 검토.
- `OPEN_DATA_GATE_MATRIX.json`: 7 node × 27 정확 입력 × 31 검증문항 및 public URL.
- `OPEN_DATA_RUNBOOK_KO.md`: CF4/Planck/AniCLASS/Gaia/Pantheon+/DESI/ACT 공개 data retrieval & source schema.
- `TEFF_HTT_BRIDGE_KO.md`: 사용자 첨부 두 draft의 정보이론적 결과를 spectral/forward identifiability에 연결. **원고 원본은 공개 repo/아카이브에 복제하지 않음.**
- `teff_optical_checks.py`: 두 개 positive MB 스펙트럼과 미식별 high-energy rates, Fisher weighted projection, optical rank 제조 예제.
- `test_scientific_checks.py`,`test_gate_requirements.py`: bounded unit/schema tests.
- `NUMERICAL_WITNESS.json`: reproducible numerical results.
- `build_gate_matrix.py`: exact machine-checkable input requirement construction.
- `MANIFEST_SHA256.json`: 모든 실제 payload digest, zip 자체 제외.
- 세 주 PR 75개 metadata의 원본 목록은 위 GitHub 브랜치 `THREE_WEEK_PR_INVENTORY.json`에 이미 게시됨. 이 ZIP에는 해당 GitHub 원본의 URL을 참고; 75개 각각의 코드 패치 전체 재현 묶음이 아님.

실행: `OPENBLAS_NUM_THREADS=1 python -m pytest -q test_scientific_checks.py test_gate_requirements.py` (Python + NumPy + SciPy + pytest). `OPENBLAS_NUM_THREADS=1 python teff_optical_checks.py`. 본 아카이브는 physical simulation, 75개 diff 재실행, 외부 real survey likelihood를 포함하지 않음.
