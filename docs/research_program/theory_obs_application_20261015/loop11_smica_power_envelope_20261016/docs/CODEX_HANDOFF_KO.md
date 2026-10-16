# htt_base / C8 finite power envelope, Codex zero-download handoff

**원래 dirty checkout을 보존하라.** 기존 경로 `/home/cosmosapjw/Dropbox/bianchi/htt_base`. AGENTS.md 필독, 새 clone/worktree·강제 checkout·reset/clean 금지. PR #536/#537을 원본 기하학 증거로 사용하고, 본 draft의 `loop11_smica_power_envelope_20261016` 파일들은 읽기 전용으로 검토한다. 원래 코드에 덮어쓰기 전에 git diff, source SHA와 팀 소유권을 확인하라.

1. PR #537 head `f85bb82ecdb308596dd283aa495dbcc01324facf`를 먼저 확인하고, 그 `code/run_local_source.py`가 실제 로컬 Planck PR3 full SMICA common mask, HM/OE masks, K1 reduced cache와 원본 PR #536 `K6..16` SHA를 인증하는지 점검하라. 
2. 실제 `C8-SMICA-ELL17-32-FINITE-TAIL`의 36x800/12x800/32x800 finite operator를 원본 파일들에서 계산해 source-locked JSON과 NPZ로 저장하라. 로컬 사용자가 이미 가진 raw FITS를 별도로 다운로드하라고 요구하지 마라. 기존 dirty 파일을 보존하고 create-only 결과 경로를 사용한다.
3. 본 PR의 `src/finite_power_envelope.py`는 source-locked 6..16의 완결된 실험 계약이다. 이를 물리 모델로 자동 승격하지 않고, 새로 계산한 17..32 행렬의 정확한 열 구조·SHA·source mask 동일성을 확인한 뒤 공분산/ellipsoid 전파를 확장하라.
4. `C_l`는 진짜 empirical/forecast 입력과 **가상 시나리오**를 분리한다. Cov(a_H) cross-shell/cross-product, high-mode amplitudes, beam, foreground 및 E2E 물리 입력이 없다면 UNKNOWN으로 유지하고 조건부 결과만 생성한다.
5. `python -m pytest -q -p no:cacheprovider tests/test_power_envelope.py` 12개 source-bound/synthetic 테스트를 먼저 재실행하라. 해당 테스트는 `source/` 임베디드 NPZ가 없으면 동일 repo Loop9 기존 파일을 SHA lock으로 자동 검색한다. 파일 다운로드나 원본 복사 없이 실행하라. 로컬 후속 과제에서 PR537의 실제 source input gate / self-response check를 별도 수행하라.
6. 물리적 EGS/Bianchi admission은 계속 HOLD. 완료 시 실제 command exit/result SHA, 독립 review 요청설정과 관측 runtime을 분리하고, DAG 및 mirror를 함께 갱신한다. 백업 성공 증거 이후 새로운 stacked draft PR로 publish하되 main merge는 하지 마라.

이 스레드의 GitHub 자료에 있는 실제 행렬 NPZ가 부족할 때는 기존 로컬 `docs/research_program/theory_obs_application_20261015/loop9_smica_finite_response/results/response_v1/baseline_response_matrices.npz`를 사용하라. 예상 SHA `a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007`.

과학적 분리: mask-geometric finite response ≠ actual sky leakage ≠ physical covariant EGS epsilon ≠ Bianchi geometry-frame shear/tilt. 독립 reviewer 도구가 없으면 NOT_RUN을 기록하라.
