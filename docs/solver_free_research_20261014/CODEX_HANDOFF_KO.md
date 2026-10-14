# 복사해서 실행할 Codex handoff

```text
htt_base의 solver-free 연구를 중단 없이 이어라. 기존 checkout /home/cosmosapjw/Dropbox/bianchi/htt_base를 사용하고, draft PR #533, branch obs/solver-free-dossier-20261014의 최신 published HEAD을 먼저 확인하라. 새로운 clone/worktree/full repo copy를 만들지 말고 사용자 dirty files를 보존하라.

AGENTS.md, docs/harness/CURRENT_CODEX_RUNTIME.md, docs/solver_free_research_20261014/DELIVERY.json, PLAN.json, SCIENTIFIC_REPORT_KO.md를 읽어라. 다음 한 명령은 python scripts/solver_free_task_packet.py --ready 이다. 후보 task마다 실제 source/code/result를 선택적으로 읽고 스스로 다음 goal을 정해 실행하라. 현재 PR 하나 완료나 native atlas 부재를 전체 연구의 중단 이유로 삼지 마라.

이론은 physmath-research-loop R1–R10, 코드는 C1–C10의 실제 유도·계산·구현·검증 흐름을 사용하라. 같은 성공 계산/증명은 재사용하고 바뀐 입력과 영향을 받는 코드만 검사하라. 첨부 BASS dossier의 current-flux, finite-bin/selection, physical Gram/dual norm, finite-observation-error 정리는 활용하되 solver를 구축하거나 ODE를 적분하지 마라. 새로운 native Bianchi solver, background evolution replacement, native family identification은 금지한다.

SF07 Gaia PSD angular-correlation sensitivity, SF08 CF4 cross-law precision, SF09 방법론 원고는 scoped 완료됐다. 기존 result.json·그림·보고서와 독립review를 재사용하고 `--ready`의 현재 결과를 따른다. 새 READY가 없으면 아래 typed blocker에 필요한 실제 제품·계약을 획득/검증한 뒤 해당 task를 재개하라. source blocker는 공개문헌/제품자료/분석적유도로 해소를 시도하고, 해결 불가능한 입력을 정확히 기록한 뒤 다른readylane을 계속하라. SF10 Union3 exact prior binding과 SF11 Planck/CLASS joint law는 가정을 측정값으로 바꾸지 말고 실제 product-to-run 연결을 확보하라.

기존 방법론4개/실제결과11개/향후후보는 PUBLICATION_CANDIDATES와 FUTURE_ANALYSES를 따른다. 이번 새 Gaia/CLASS/Union3/selection/CF4 결과를 반영해 novelty comparison과 calibration을 보강하라. 기준미달을 test PASS로 덮지 말고 무엇을 더 계산해야 하는지 정하고 수행하라. null/negative 결과도 정확한 범위에서 보고하라. 기존 HOLD/UNKNOWN, active R9와 historical CAS 판정을 바꾸지 말고, source·selection·shared-sky/calibration dependency를 유지하라. 없는 physical tensor/MES denominator/remainder를0으로 채우지 마라.

부모 gpt-6.1-sol/high, 수치worker gpt-6.1-sol/high, 독립reviewer gpt-6-astra/xhigh를 권장한다. 단순 extraction만 gpt-6-luna/medium으로 낮추고 deterministic validator를 둬라. 부모 포함최대4agent, fresh bounded taskpacket, disjoint writer ownership, productionwriter1명, 독립검토1회와구체수선으로운영하라. requested/observed runtime을분리하고 관측불가면UNKNOWN을기록하라.

사용자는 연구·코드·그림·보고서·push를 이미 승인했다. 통상적인다음goal마다진행여부를묻지마라. main merge, 논문제출, 타인에게메시지전송은 별도승인없이하지마라. 컨텍스트경계에서goal/HEAD/inputhash/command/process PID/seed/batch/remaininginput을checkpoint하고 같은작업을이어라. 자동백그라운드서비스가설치됐다고주장하지마라. 실제외부입력/권한/런타임경계면그증거와정확한재개명령을남겨라. 최종에는현재결과·진행중작업·남은blocker·remotecommit/PR·복사가능한handoff를출력하라.
```

## 2026-10-14 solver-free continuation checkpoint

- Checkpoint source HEAD before SF09 manuscript publication: `36f7f48ad1f65a97a7eebfe68278f29353dcf54b` on `obs/solver-free-dossier-20261014`; draft PR #533. Resolve final remote ref with `git ls-remote origin refs/heads/obs/solver-free-dossier-20261014`. Existing checkout only; no process/PID remains running from the SF08 fixed campaign.
- SF07: `results/gaia_correlation/result.json`, saved 4,756-source M and 24 assumed PSD angular-covariance scenarios; source operator SHA `d5384f57138f4e8ea7b986153bf0133f846e9f7806bdf82b2cb7ac4d6a676c9f`; 21 targeted tests and scoped independent review. Commit `57d1c280d68559f6650f8488d4f503d2e2c7d287`. Empirical cross-source covariance and selected-cohort coverage remain unknown.
- SF08: `results/cf4_precision/result.json`, final contract SHA `2132be1b0b0eb014263bc601784c1d7a4f9af345a3a8abaec7c9eb5edb3a0b03`; original 32 plus 64 valid new catalogues, 128 new fits, fixed seed families in `SEED_DISJOINTNESS.json`; initial 22 excluded/overlap attempts and first failures retained. Targeted tests, four new-wrapper profile parity fits, 139 artifact hashes, separate scoped review. Commit `36f7f48ad1f65a97a7eebfe68278f29353dcf54b`. For a fresh batch, first declare a new contract: `OPENBLAS_NUM_THREADS=1 python scripts/run_solver_free_cf4_precision.py --repo . --declare /tmp/htt_sf08_new_contract.json`; then use its `--contract` and a new `--output`. Do not rewrite the archived contract to match a later HEAD.
- SF09: `METHODS_MANUSCRIPT.md` and `review/SF09_INDEPENDENT_REVIEW.md`; literature comparison, two scoped prose repairs and independent conditional-draft PASS. It reuses the SF08 result/plot. Publication submission and empirical law identification remain open. Requested author/worker `gpt-6.1-sol/high`, independent reviewers `gpt-6-astra/xhigh`; observed runtime metadata `UNKNOWN`.
- Next one command: `python scripts/solver_free_task_packet.py --ready`. The current typed blockers are SF10 exact Union3 generating prior/run configuration; SF11 FFP raw-vs-005a processing and joint split/systematic law; SF12 actual global-history/source-motion response and physical curvature/derivative/remainder envelopes; SF13 empirical survey selection, shared calibration covariance and object overlap/source-motion law; SF14 raw map splits with filtering/noise/response/mean-field/bias products. Missing quantities remain unknown rather than zero. Scientific admission and historical HOLD remain unchanged.

- 결과 데이터 원본 게시 확인: `DERIVED_RESULT_ORIGINALS.json`은 source commit `cc7cdcbfeb00b87a9acdf2cbd950f55a45447e42`의 836개 추적 JSON/NPZ/CSV 산출물(118,433,377 bytes)을 SHA-256과 Git blob ID로 고정한다. `workdir/raw`와 Gaia per-source 관측행 추출본 `qualified_rows.npz`는 새 인벤토리에서 제외한다. 이는 byte provenance이며 새로운 science admission이 아니다.
