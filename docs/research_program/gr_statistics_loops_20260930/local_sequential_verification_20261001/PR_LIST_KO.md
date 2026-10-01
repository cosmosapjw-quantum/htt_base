# PR 현황과 순차 작업·게시 계획

기준 commit: `9f46363433723cc3b2dc75bab781274fe1b3df7d`. 이 문서의 **PLAN ID**, 저장소 canonical **PR-ID**, GitHub **#번호**는 서로 다르다. 이 요청에서는 문서를 기존 main에 게시하며 새 branch/PR 생성·merge·close는 하지 않는다.

## 1. canonical DAG

현재 213개 카드: completed 159, blocked 4, pending 21, dormant_external 28, background_in_progress 1, foreground in_progress 0. 기존 validator로 DAG를 검사했으며 canonical과 `machine_readable` 두 YAML 쌍은 동일하다. **159는 완료된 증명 수가 아니다.** 기존 `PR-GR-STATISTICS-CAS-HANDOFF` 완료는 연구자료·계약 게시의 완료다.

이번 패키지는 그 카드 아래 후속 증명 실행을 정리한 보충 문서다. canonical 카드의 상태를 바꾸지 않는다. 로컬에서 별도 새 canonical 카드를 실제 채택할 경우에만 `$htt-dag-orchestrator` 절차, 상태 mirror, PR_DELTA, validator를 함께 갱신한다. 미실행 계획을 completed 목록에 넣지 않는다.

| 기존 카드 | 기준 상태 | 이번 작업과의 관계 |
|---|---|---|
| PR-MES-I1-I2-MATERIALIZE | completed | 702개 보존 자료의 provenance |
| PR-TYPEFREE-INFERENCE-PORT | completed | 조건부 코드 이식·테스트; 12개 CAS 의무는 별도 |
| PR-GR-STATISTICS-CAS-HANDOFF | completed | 46개 claim·17개 계약의 게시; 증명 완료와 별도 |
| PR-MES-R7-SOURCE-IMAGE | blocked | 이 문서로 활성화하지 않음 |
| PR-R9-DEPTH-MATHLIB | blocked | 현재 R9 task/예산을 보존 |
| PR-172, PR-247 | blocked | 원 카드의 blocker를 유지 |
| PR-151 | background_in_progress | 별도 실행권·자원 상태 유지 |

## 2. 제안하는 작업 단위

한 줄은 독립적으로 검토·게시 가능한 최소한의 실질 증명 단위다. 실제 PR 번호를 배정한 것이 아니다. 인접 단위는 입력·독립성·리뷰 scope가 맞을 때 묶을 수 있다. 각 단계마다 내용 없는 문서 commit을 만들지 않는다. 전체 node별 세부 산출물·acceptance·stop은 [PR_PLAN.json](PR_PLAN.json)에 있다.

| 순번 | PLAN ID | 내용 | 의존 / 특수 조건 |
|---|---|---|---|
| 1 | PLAN-INTAKE | 기존 로컬 raw·계약·task를 대조하고 미게시 증거를 회수 | 독립/원본 증거 우선 |
| 2 | PLAN-GR-11 | Bregman·moment 잔차 ellipsoid | 독립/원본 증거 우선; C01 v4 needs explicit adoption plus supported same-task/routing; C02/C03 preserved without rerun. |
| 3 | PLAN-GR-01 | 광학 역산·가속도·국소 1-jet | 독립/원본 증거 우선 |
| 4 | PLAN-GR-03 | 측지 고유공간·퇴화·임의 shear 역산 | PLAN-GR-01; CAS03 corrected seven contracts supersede no historical evidence; finish domain alignment before four-axis execution. |
| 5 | PLAN-GR-10 | 형태 정보·스칼라 보완·cutout 한계 | PLAN-GR-01 |
| 6 | PLAN-GR-14 | 두 방향 미분에 의한 와도 복원 | PLAN-GR-01 |
| 7 | PLAN-GR-15 | 복사 weak residual·commutator·복수 채널 | PLAN-GR-01, PLAN-GR-14 |
| 8 | PLAN-GR-05 | 자유 물질류의 conformal·cubic metric germ | 독립/원본 증거 우선 |
| 9 | PLAN-GR-06 | 고정 EOS TOV·고정 P(X) 작용 | 독립/원본 증거 우선 |
| 10 | PLAN-GR-04 | 에너지계 rate budget·Euler 제약 | PLAN-GR-05, PLAN-GR-06 |
| 11 | PLAN-GR-02 | 광학 역산의 유한 안정성 | PLAN-GR-01 |
| 12 | PLAN-GR-07 | 유한거리 Jacobi·Taylor 인증 | PLAN-GR-01 |
| 13 | PLAN-GR-17 | orbit tilt·scale·conformal·관측자 변환 | PLAN-GR-01, PLAN-GR-07 |
| 14 | PLAN-GR-08 | 신뢰영역 coverage·측지성 판정 | PLAN-GR-01, PLAN-GR-07 |
| 15 | PLAN-GR-09 | 설계 rank·radial alias·잔차 여유 | PLAN-GR-01, PLAN-GR-07 |
| 16 | PLAN-GR-12 | 충돌 adjoint·BE envelope·미분 경계 | PLAN-GR-11 |
| 17 | PLAN-GR-13 | 열적 cubic 응답·number-conditioned 구간 | PLAN-GR-11; C04 PASS preserved; reviewer remains parked until supported lifecycle change. C01-C03 interval obligations can only run under their own valid prerequisite scope. |
| 18 | PLAN-GR-16 | 제한된 Thomson norm·곱 구적 | PLAN-GR-15 |
| 19 | PLAN-PORT-CAS-01 | Lorentz metric and inverse, absolute redshift intercept mass shell | 독립/원본 증거 우선 |
| 20 | PLAN-PORT-CAS-02 | Hubble null-form and geodesic lift | 독립/원본 증거 우선 |
| 21 | PLAN-PORT-CAS-03 | Velocity-jet physical kinematics | 독립/원본 증거 우선 |
| 22 | PLAN-PORT-CAS-04 | Fluid and Codazzi arithmetic | 독립/원본 증거 우선 |
| 23 | PLAN-PORT-CAS-05 | Spacelike orbit curvature and invariant tensor derivative | 독립/원본 증거 우선 |
| 24 | PLAN-PORT-CAS-06 | Endpoint optical invariants | 독립/원본 증거 우선 |
| 25 | PLAN-PORT-CAS-07 | Finite measure with undefined atoms | 독립/원본 증거 우선 |
| 26 | PLAN-PORT-CAS-08 | Ellipsoid quotient and affine fiber | 독립/원본 증거 우선 |
| 27 | PLAN-PORT-CAS-09 | Signed joint depth transform | 독립/원본 증거 우선 |
| 28 | PLAN-PORT-CAS-10 | Conditional P2/W1 | 독립/원본 증거 우선 |
| 29 | PLAN-PORT-CAS-11 | Dense Gaussian GLS and deterministic remainder | 독립/원본 증거 우선 |
| 30 | PLAN-PORT-CAS-12 | Two-state full Gaussian law comparison | 독립/원본 증거 우선 |
| 31 | PLAN-LOOP2-BRIDGES | Loop2 좁은 Lean 범위와 수기 bridge 정리 | 독립/원본 증거 우선 |
| 32 | PLAN-CLOSEOUT | 증명 범위 종합·미해결 목록·최종 로컬 반환 | 독립/원본 증거 우선 |

`PLAN-CLOSEOUT`은 모든 노드 PASS를 가정하지 않는 보고 단위다. 각 노드가 완료·차단·범위 밖 중 어디에 있는지 disposition을 기다린다. 물리적 입력이 없는 것과 증명이 실패한 것을 구분한다. 다섯 개 canonical PR을 실제 완료했을 때만 원 five-PR progress 규칙을 적용하고, 과학 진척은 닫힌 명제와 남은 가정으로 설명한다.

## 3. 이 스레드와 가까운 GitHub PR

최신 원격 상태를 읽었다. 과거 `PR_DISPOSITION.json`의 예측·당시 상태보다 아래 관측이 최신이다. `closed`와 `merged`도 구별한다. #469는 별도 target branch에 merged되었으며 그 사실만으로 main 포함을 단정하지 않는다.

| GitHub PR | 제목 | 현재 상태 | head → base |
|---|---|---|---|
| [#471](https://github.com/cosmosapjw-quantum/htt_base/pull/471) | Loop 2 corrections and current Codex harness modernization | merged | `changeset/typefree-loop2-closeout-20260929` → `main` |
| [#470](https://github.com/cosmosapjw-quantum/htt_base/pull/470) | PR-248: Integrate optical mapping DAG and Local Codex research handoff | closed | `research/htt-optical-mapping-r10-20260919-r1` → `research/tensor-joint-r9-design-20260912` |
| [#469](https://github.com/cosmosapjw-quantum/htt_base/pull/469) | Bind PR-315 replay runtime and verify repeated byte determinism | merged | `fix/pr315-portable-determinism-issue445` → `changeset/planck-mes-wu011-processed-local-boost-response-20260902` |
| [#468](https://github.com/cosmosapjw-quantum/htt_base/pull/468) | PR-248: R9 physics/statistics research and model-to-observation design | closed | `research/tensor-joint-r9-design-20260912` → `implementation/tensor-joint-r8-20260909` |
| [#467](https://github.com/cosmosapjw-quantum/htt_base/pull/467) | R8: certified tensor ranks and joint physical inference design | closed | `research/tensor-joint-r8-design-20260908` → `implementation/tensor-joint-r7-20260908` |
| [#466](https://github.com/cosmosapjw-quantum/htt_base/pull/466) | R7: connect tensor MES, owned assets and branching Local Codex research design | closed | `research/tensor-joint-r7-design-20260908` → `handoff/htt-lowell-postreview-20260907-r1` |
| [#465](https://github.com/cosmosapjw-quantum/htt_base/pull/465) | HTT: GPT-5.6 universal continuation packet — 2026-09-07 | closed | `handoff/htt-lowell-postreview-20260907-r1` → `research/htt-referee-seeded-program-20260907-r1` |
| [#464](https://github.com/cosmosapjw-quantum/htt_base/pull/464) | HTT: source/data review addendum to recovered PR462/463 theory-first plan | open | `research/htt-review-seeded-theory-plan-20260907-r1` → `docs/htt-pedagogical-render-20260907-r1` |
| [#463](https://github.com/cosmosapjw-quantum/htt_base/pull/463) | HTT: complete PR462 planning with unified three-contract DAG and additional code findings | closed | `research/htt-referee-seeded-program-20260907-r1` → `docs/htt-pedagogical-render-20260907-r1` |
| [#462](https://github.com/cosmosapjw-quantum/htt_base/pull/462) | Post-review research: quantitative nuisance information and theory-first redshift programme | open | `research/htt-postreview-theory-first-20260907-r1` → `docs/htt-pedagogical-render-20260907-r1` |
| [#461](https://github.com/cosmosapjw-quantum/htt_base/pull/461) | Report A: Assemble and verify the complete pedagogical exposition | closed | `docs/htt-pedagogical-render-20260907-r1` → `docs/htt-report-a-pedagogical-20260907-r1` |
| [#460](https://github.com/cosmosapjw-quantum/htt_base/pull/460) | Report A: introductory self-contained teaching edition | closed | `docs/htt-report-a-pedagogical-20260907-r1` → `docs/htt-tensorized-mes-response-synthesis-20260903` |
| [#459](https://github.com/cosmosapjw-quantum/htt_base/pull/459) | Report A R3: Render complete evidence-integrated review edition | open | `docs/htt-report-a-r3-render-20260907-r1` → `docs/htt-tensorized-mes-response-synthesis-20260903` |

## 4. 현재 열린 GitHub PR 전체 46개

목록은 상태 inventory다. 열린 PR을 이번 캠페인의 선행조건이나 자동 merge 대상으로 전환하지 않는다. old branch의 코드 동치·latest-base CI·review 완료는 각각 별도 확인해야 한다. 특히 관측/Planck/HSC/CF4 실행은 현재 증명 인계 범위 밖이다.

| PR | 제목 | target branch |
|---|---|---|
| [#464](https://github.com/cosmosapjw-quantum/htt_base/pull/464) | HTT: source/data review addendum to recovered PR462/463 theory-first plan | `docs/htt-pedagogical-render-20260907-r1` |
| [#462](https://github.com/cosmosapjw-quantum/htt_base/pull/462) | Post-review research: quantitative nuisance information and theory-first redshift programme | `docs/htt-pedagogical-render-20260907-r1` |
| [#459](https://github.com/cosmosapjw-quantum/htt_base/pull/459) | Report A R3: Render complete evidence-integrated review edition | `docs/htt-tensorized-mes-response-synthesis-20260903` |
| [#458](https://github.com/cosmosapjw-quantum/htt_base/pull/458) | PR450: Repair approved seed parent and real coverage layout; replay frozen source | `validation/pr450-main-local-source-replay-20260907-r1` |
| [#457](https://github.com/cosmosapjw-quantum/htt_base/pull/457) | PR450: Return exact baseline NONPASS and source-parent mismatch evidence | `analysis/pr408-wu001-registered-survivor-triage-20260903` |
| [#456](https://github.com/cosmosapjw-quantum/htt_base/pull/456) | PR451: Publish completed native decoder validation for MAIN | `repair/qo-krylov-packet-image-syzygy-20260903` |
| [#455](https://github.com/cosmosapjw-quantum/htt_base/pull/455) | HTT T2: restore three tokens and repair bounded assertions (local 80 PASS) | `implementation/htt-authority-citation-reconciliation-20260905-r1` |
| [#454](https://github.com/cosmosapjw-quantum/htt_base/pull/454) | T9 authority: Reconcile citation pin and preserve NONPASS replay | `review/htt-r4a1er-local-result-scope-20260905-r1` |
| [#453](https://github.com/cosmosapjw-quantum/htt_base/pull/453) | R4A1ER: Review local R2 supporting lemmas and remaining obligations | `review/htt-k2fr-returned-repair-20260905-r1` |
| [#452](https://github.com/cosmosapjw-quantum/htt_base/pull/452) | K2FR: Publish verified Report A repair and noncanonical evidence | `docs/htt-tensorized-mes-response-synthesis-20260903` |
| [#451](https://github.com/cosmosapjw-quantum/htt_base/pull/451) | Fix: certify Q/O packet image and stabilize the STF3 decoder | `changeset/mes-tensor-research-integration-20260830` |
| [#450](https://github.com/cosmosapjw-quantum/htt_base/pull/450) | A2: mechanically compile the registered theory-survivor source surface | `changeset/pr406-audit-theory-promotion-contract-hardening-20260825` |
| [#447](https://github.com/cosmosapjw-quantum/htt_base/pull/447) | audit: verify WU-011 continuum response with Octave, JAS, and Julia | `changeset/planck-mes-wu011-processed-local-boost-response-20260902` |
| [#446](https://github.com/cosmosapjw-quantum/htt_base/pull/446) | research: add independent Task-7C external verifier axes | `changeset/planck-mes-wu011-processed-local-boost-response-20260902` |
| [#444](https://github.com/cosmosapjw-quantum/htt_base/pull/444) | research: processed local-boost response through Task-7C A4 local execution audit | `analysis/planck-mes-wu011-processed-local-boost-response-20260902` |
| [#443](https://github.com/cosmosapjw-quantum/htt_base/pull/443) | Design: PMG-WU-011 processed cut-sky local-boost response | `changeset/planck-mes-wu010-local-boost-adapter-20260901` |
| [#442](https://github.com/cosmosapjw-quantum/htt_base/pull/442) | research: add exact local-boost pullback and STF response adapter | `changeset/planck-mes-wu009-full-replay-theorem-reconciliation-20260830` |
| [#441](https://github.com/cosmosapjw-quantum/htt_base/pull/441) | Draft: PMG-WU-009 theorem reconciliation and full-replay handoff | `changeset/planck-mes-wu008-injection-power-20260829` |
| [#438](https://github.com/cosmosapjw-quantum/htt_base/pull/438) | PMG-WU-007: reviewed SMICA CMB-only 999 robustness complete | `changeset/planck-mes-wu006-admission-staging-20260829` |
| [#434](https://github.com/cosmosapjw-quantum/htt_base/pull/434) | PMG-WU-006: reviewed local admission complete; map-free result preserved | `changeset/planck-mes-paired300-evidence-repair-v2-20260828` |
| [#432](https://github.com/cosmosapjw-quantum/htt_base/pull/432) | PMG-WU-007 preflight: data acquisition closed, local execution handoff ready | `changeset/planck-mes-observable-irrep-analysis-20260829` |
| [#431](https://github.com/cosmosapjw-quantum/htt_base/pull/431) | PMG-WU-006: executed observable irrep-orbit analysis; upstream admission pending | `changeset/planck-mes-paired300-irrep-carrier-20260828` |
| [#430](https://github.com/cosmosapjw-quantum/htt_base/pull/430) | PMG-WU-005 bounded repair: remote guards GREEN, local evidence rebind pending | `changeset/planck-mes-paired300-irrep-carrier-20260828` |
| [#428](https://github.com/cosmosapjw-quantum/htt_base/pull/428) | Retire pre-statistical publication surfaces | `changeset/planck-mes-irrep-data-intake-20260828` |
| [#427](https://github.com/cosmosapjw-quantum/htt_base/pull/427) | Connector smoke: PMG-WU-005 import / push / PR / merge | `connector-smoke/pmg-wu005-import-push-merge-20260828-base` |
| [#426](https://github.com/cosmosapjw-quantum/htt_base/pull/426) | PMG-WU-005: preserve the paired-300 low-ell harmonic carrier | `changeset/planck-mes-irrep-data-intake-20260828` |
| [#424](https://github.com/cosmosapjw-quantum/htt_base/pull/424) | PMG-WU-004: completed read-only local Planck/FFP10 intake | `changeset/planck-mes-coordinate-mechanism-audit-20260828` |
| [#422](https://github.com/cosmosapjw-quantum/htt_base/pull/422) | PMG-WU-003: execute map-free coordinate mechanism audit | `changeset/planck-mes-global-formalism-adapters-20260827` |
| [#421](https://github.com/cosmosapjw-quantum/htt_base/pull/421) | PMG-WU-002: apply typed global-formalism adapters | `analysis/planck-mes-extended-data-execution-20260826` |
| [#417](https://github.com/cosmosapjw-quantum/htt_base/pull/417) | Plan: execute irrep-global Planck MES formalism with carrier-preserving finite-null analysis | `changeset/pr324-mes-methodology-stack-20260826` |
| [#416](https://github.com/cosmosapjw-quantum/htt_base/pull/416) | Planck MES Paper A: finite-null low-ℓ morphology draft | `analysis/mes-methodology-stack-integration-20260826` |
| [#415](https://github.com/cosmosapjw-quantum/htt_base/pull/415) | EXPLORATORY PR-315: implement joint cut-sky low-ell estimator | `analysis/mes-methodology-stack-integration-20260826` |
| [#414](https://github.com/cosmosapjw-quantum/htt_base/pull/414) | Integrate repaired data stack with MES methodology recovery | `changeset/pr321-hsc-s19a-sacc-fast-analysis-20260825` |
| [#412](https://github.com/cosmosapjw-quantum/htt_base/pull/412) | PR-321: bind official HSC S19A/Y3 fiducial SACC readiness | `changeset/pr320-hsc-kids-cross-covariance-20260825` |
| [#411](https://github.com/cosmosapjw-quantum/htt_base/pull/411) | Audit: recover MES methodology spine and compile observed-data integration plan | `changeset/pr320-hsc-kids-cross-covariance-20260825` |
| [#410](https://github.com/cosmosapjw-quantum/htt_base/pull/410) | PR-320: derive paired HSC-KiDS joint covariance | `changeset/pr319-jwst-2mrs-neural-field-20260825` |
| [#409](https://github.com/cosmosapjw-quantum/htt_base/pull/409) | PR-319: bind the 2024 2MRS neural velocity field | `changeset/pr318-desi-input-preparation-20260825` |
| [#407](https://github.com/cosmosapjw-quantum/htt_base/pull/407) | Audit: harden PR-406 theory-promotion repair plan | `changeset/pr316-theory-promotion-ledger-repair-plan-20260824` |
| [#406](https://github.com/cosmosapjw-quantum/htt_base/pull/406) | PR-316 plan: reproducible theory-candidate ledger and typed evidence repair | `analysis/theory-promotion-audit-20260824` |
| [#405](https://github.com/cosmosapjw-quantum/htt_base/pull/405) | AUDIT: reconcile observation-independent theory candidates | `changeset/pr300-one-command-observational-readiness-20260821` |
| [#404](https://github.com/cosmosapjw-quantum/htt_base/pull/404) | PR-315 plan: adversarial audit and joint cut-sky Planck robustness contract | `changeset/pr314-planck-pr3-attended-analysis-20260824` |
| [#403](https://github.com/cosmosapjw-quantum/htt_base/pull/403) | PR-314: run and replay existing Planck SMICA diagnostic | `changeset/pr300-one-command-observational-readiness-20260821` |
| [#388](https://github.com/cosmosapjw-quantum/htt_base/pull/388) | PR-291: recover CF4 native-profile preactivation | `changeset/pr290-planck-native-replay-recovery-20260811` |
| [#387](https://github.com/cosmosapjw-quantum/htt_base/pull/387) | PR-290: recover native Planck preactivation replay | `changeset/pr289-native-data-identity-recovery-20260811` |
| [#386](https://github.com/cosmosapjw-quantum/htt_base/pull/386) | PR-289: recover native data identity semantics | `changeset/pr288-bayesian-evidence-recovery-20260811` |
| [#385](https://github.com/cosmosapjw-quantum/htt_base/pull/385) | PR-288: recover bounded Bayesian semantics | `research/pr04-multicomponent` |

## 5. 게시 규칙

사용자 변경과 raw 로그의 bytes를 보존한다. 한 bounded unit의 HEAD 결합 launch 처리·지원된 종결을 끝낸 뒤 결과·검토·필요한 코드만 명시적 경로로 stage한다. `git add -A`, reset/clean/stash, 강제 push, 대량 branch 통합은 하지 않는다. 원격이 전진했으면 diff를 확인하고 합의된 정상 경로로 통합하며 새 HEAD가 기존 검토 범위에 미치는 영향을 확인한다.

정상 non-force push는 provider 성공과 원격 ref/commit/tree의 R1으로 닫는다. 불필요한 redownload/reclone과 자기 commit hash를 넣기 위한 연쇄 commit은 만들지 않는다. R1은 restore 검증이나 과학적 PASS가 아니다. CI는 실제 status를 적고, 관측된 run이 없으면 “CI run 없음”으로 적는다.
