# 01 — HANDOFF MASTER

Mode: `/handoff: hybrid`  
As of: `2026-09-07T19:05+09:00`  
Repository: `cosmosapjw-quantum/htt_base`

# 1. 초압축 요약

- **FACT** — HTT는 low-ell CMB의 quadrupole/octupole tensor morphology를 보존하면서 local-observer response, high-mode nuisance assumptions, redshift/depth information이 physical/frame quantities를 어디까지 식별하는지 연구한다.
- **FACT** — 29쪽 R3와 55쪽 pedagogical report는 noncanonical 문서 산출물로 완료됐다. 현재 연구 SSOT는 PR #463 `0e2d6e3a890ae44303440e8534fb6080d1dac881`의 master+DAG다.
- **FACT** — PR #464 `fa86d940f6d954af554bae5b577d5eb465aa2ae1`는 source/data addendum이며 별도 programme가 아니다.
- **OPEN/P1** — `M1_CMB_MODEL`, `M2_REDSHIFT_MODEL`, `M3_EXPERIMENT`가 미완. `execution_release=false`; `THEORY_FREEZE`와 Local Codex C0–C5는 시작되지 않았다.
- **FACT** — 기존 K2/K2FR, R2 four-lemma, authority/T2 80 PASS, exact-source Q/O decoder 28 PASS, PR450 source replay 90 PASS+double replay는 각자의 제한된 scope에서 재사용한다.
- **CONDITIONAL** — PR462 T1–T10은 durable direct derivations이나 새 native test/CAS/Monte Carlo receipt는 아니다.
- **FACT** — canonical ledger T9 v4/30, candidate 40, PR284 DEFERRED, finite-pixel containment/error-class unresolved.
- **최우선 행동** — fresh-read PR463/464 후 `M1_CMB_MODEL`을 완결한다. 새 plan이나 Local Codex dispatch를 만들지 않는다.

# 2. 핵심 문제설정

| 항목 | 현재 정의 |
|---|---|
| Primary objective | Q/O observable morphology, local-observer response, nuisance assumptions, redshift/depth information을 한 inference programme으로 연결하되 observable/physical/frame/nuisance/identification을 분리 |
| Input objects | STF2 `Q_ab`, STF3 `O_abc`; absolute CMB maps/harmonics; high-mode source/nuisance; PR3/FFP10 candidate products; selected CF4/DESI data; covariance/selection/window metadata |
| Target outputs | morphology diagnostics; declared response-coordinate constraints/identified sets; bounded/stochastic nuisance comparisons; supported redshift bulk/symmetric-affine/pole functionals; calibrated synthetic/observed result or typed abstention |
| Governing assumptions | explicit frame labels, map preprocessing/units, declared nuisance model and joint law, matched nulls, explicit approximation branch; MES-improvement branch only inside its stated first-order radiation model |
| Success criterion | M1/M2/M3 close science -> THEORY_FREEZE -> Local C0–C5 returns reproducible code/evidence -> MAIN states claim ceiling |
| Failure criterion | missing product, invalid null, singular/unidentified response, uncontained numerical error, model inadequacy, or need to change protected science; these are typed outcomes, not forced PASS |
| Explicitly excluded scope | new native Bianchi solver/family atlas; empirical global tilt without response; new remote kSZ/pSZ acquisition; general nonlinear almost-EGS theorem; automatic survey acquisition; merge/public disclosure |
| Adjacent-track interfaces | BASS/REC/REI remain separate. HTT local boost processing cannot stand in for global/electron tilt or background/provider evidence |

## Math/physics conventions

- Spacetime signature `(-,+,+,+)`; spatial orientation `epsilon_123=+1`.
- Keep `c` explicit unless a declared adapter converts every relevant rate consistently.
- Accepted outward sky convention: `n=-e`.
- `Q_ab`, `O_abc` have temperature units; `q=Q/A_Q`, `o=O/A_O` are unit shapes when amplitudes are nonzero.
- Default spatial tensor norm is full Euclidean Frobenius contraction.
- Physical velocity variable is `beta=v/c`; frame labels `RO`, `RM`, `MO` are part of the semantic type.
- No global initial/boundary condition exists for the programme. Each finite experiment must freeze map preprocessing, mask, source cutoff, covariance, survey windows and approximation regime.

## Runtime architecture

`MAIN science -> THEORY_FREEZE -> Local C0 integration -> C1 implementation -> (C2 synthetic || C3 selected-data intake) -> C4 observed analysis -> C5 Git return -> MAIN result review`.

No new-campaign production command is canonical yet because M3 is not closed.

# 3. 확정 / 조건부 / 폐기 ledger

## A. 확정 결론

| ID | Claim | Evidence | Valid scope | Consequence |
|---|---|---|---|---|
| F01 | 29p R3 and 55p pedagogical reports are complete noncanonical artifacts | PR459/461 receipts + MAIN artifact acceptance | document production | do not rerender/reopen |
| F02 | Active programme SSOT is PR463 master+DAG | fresh GitHub/Atlassian readback | current programme | start from M1/M2/M3 |
| F03 | PR464 is addendum/crosswalk, not competing plan | PR464 + latest Confluence/Jira | source/data support | no third programme |
| F04 | Q/O exact-source registered suite = 28/28 PASS | PR451/456 evidence | named numerical contract | reuse donor, do not overgeneralise |
| F05 | authority/T2 repaired suite = 80 PASS | PR455 | source/contract regression | earlier 37/3 is history |
| F06 | PR450 repair/replay = 90 PASS + two byte-identical real Git-object replays, 37 rows=36+1 deferred | PR458 | source-disposition extraction | stale “unsealed” text superseded |
| F07 | R2 formal run proves only four named supporting lemmas | PR453 | scalar contractions/normalisation/positive regularisation | no broad formal promotion |
| F08 | registered axial continuum operator has exact minimal full-row-rank cutoff `L=10` | direct deduction from accepted exact minors | axial continuum | `L=12` valid but nonminimal |
| F09 | radial local-affine observation kills antisymmetric rigid rotation: `n^T Omega n=0` | direct algebra | local low-z radial model | vorticity unsupported without another response |
| F10 | inspected DESI moment response is `3 Cov_R(n)`, not identity generally; inspected path has equatorial/Galactic mismatch | source inspection + direct derivation | inspected default path | existing estimator not science-ready |
| F11 | canonical T9 v4/30, candidate 40, PR284 deferred remain | current durable state | governance/science ledger | no silent promotion |

## B. 조건부 결론 / working hypotheses

| ID | Statement | Assumptions | Evidence level | Confirm/falsify |
|---|---|---|---|---|
| C01 | `f_B ~ Beta(3/2,2)` | fixed Q; spherical 7D Gaussian or uniform-sphere direction | direct analytic derivation | synthetic draws from exactly this law |
| C02 | improved shear/vorticity ceilings | explicit first-order geodesic collisionless radiation + derivative envelopes | direct derivation | use as regression under same premises only |
| C03 | joint high-mode Gaussian conditioning/Fisher formula | declared joint Gaussian means/covariance | standard/direct derivation | M1 freezes actual blocks; C2 checks |
| C04 | soft-mask response norm may vanish while algebraic rank stays full | declared finite-band soft-mask path + bounded resolvent | direct derivation | targeted synthetic epsilon sweep |
| C05 | bounded pair ambiguity uses radius `2R` | fixed linear model and ellipsoidal source bound | direct linear algebra | exact regression after C1 |

## C. 폐기된 결론 / 경로

| ID | Deprecated item | Why | Reusable residue |
|---|---|---|---|
| D01 | scalar-only MES observational-rank methodology | tensorised physical/observable programme supersedes it | history only |
| D02 | local boost = global tilt | physically different frame lane | local `beta_RO` oracle |
| D03 | `L=12` is minimal | exact deduction gives 10 | L12 larger full-rank example |
| D04 | RMS 0.8435 | inconsistent with stated formula/inputs | corrected model result |
| D05 | deterministic slack must be preselected | not required by deterministic Weyl bound | preserve error-enclosure justification |
| D06 | CF4 quarantined headline outputs | prior scientific failure classes | raw inputs reusable under new model |
| D07 | file count = null-realisation count | products/files are dependent/multipart | use unique matched IDs |
| D08 | mandatory WORK_THREAD/manual ZIP | replaced by direct MAIN<->Local Git route | historical evidence remains |

`DO NOT REINTRODUCE: D01–D08 without new conflicting evidence.`

# 4. 수식 / 논증 상태

Full ledger is `04_EQUATION_ARGUMENT_LEDGER.md`. Load-bearing current equations:

1. `L_Q O=O:Q`, `B_Q beta=3 STF(beta⊗Q)`, `B_Q*=3L_Q`, `B_Q*B_Q=3M_Q`, `M_Q=(Q:Q)I+(6/5)Q^2`.
2. Ideal projection law: `f_B=||P_Q O||^2/||O||^2 ~ Beta(3/2,2)` only under the spherical conditional null.
3. `Cov(beta_hat|Q)=tau^2/3 M_Q^{-1}`; fixed-amplitude analogue `A_O^2/21 M_Q^{-1}`.
4. `tr M_q^{-1}=90/(40+3 s3^2)`, `s3^2 in [0,1/6]`, giving the corrected illustrative RMS range.
5. First-order radiation-model shear: `sigma_ab=-dot(vartheta_<ab>)-D_<a vartheta_b>-(3/7)D^c vartheta_abc`; sharp STF derivative-contraction norm `sqrt(7/5)`.
6. First-order vorticity: `omega_ab=-3/Theta dot C_ab-C_ab-(6/(5Theta))D_[a D^c vartheta_b]c`.
7. Error-whitened rank: if `Delta Delta^T <= Gamma`, then `s_m(WK_true)>=s_m(WK_obs)-1`.
8. Bounded nuisance minimum cost: `c(d)^2=d^T(KSK^T)^+d`; pairwise allowed-state ambiguity uses `2R`.
9. Joint Gaussian conditioning: Schur complement `C_y|z=C_yy-C_yz C_zz^{-1} C_zy`; when covariance is parameter-independent, conditional response `A_c=A_y-C_yz C_zz^{-1}A_z`.
10. Soft mask: `K_e=-e P(I-e M_FF)^(-1)V_b = O(e)` when the resolvent is bounded.
11. DESI weak-dipole self-normalised moment: `E[Dhat]=3 Cov_R(n)d`; uniform northern hemisphere gives `diag(1,1,1/4)`.

Notation warning: the companion contraction vector often called `v=o:q` is **not** physical velocity. Rename if it coexists with `beta`.

# 5. 코드 / 수치 / 데이터 상태

See `05_CODE_NUMERICS_DATA_LEDGER.md`.

Repository roles:

- private repo: `https://github.com/cosmosapjw-quantum/htt_base`
- default code branch `research/pr04-multicomponent` @ `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`
- active programme PR463 @ `0e2d6e3a890ae44303440e8534fb6080d1dac881`
- accepted decoder donor `9f7d06dec0fce1c3a8a53fa5372c84d9c679c037`
- exact boost donor `29427a1f7f2c5d46e43ffe03053c4ac13e969228`
- processed response donor `de73549c16ac6ceb63f924c86611e0a5ceb4711d`
- local checkout clean/dirty/untracked state in MAIN: `UNKNOWN`.

Data inventory (owner metadata): `W=/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir`, `E=/mnt/sn850x2t/htt_base_e2e`, 179 bundles, 456,933 paths, ~1.499 TB logical content. Do not rescan/re-hash globally.

Primary current candidates: PR3 SMICA + genuinely product-matched FFP10; selected raw CF4 distance/group information; DESI catalogues/randoms/mocks. Empty NPIPE path is not a complete PR4 input. Posterior draws, file counts, lensing kappa and correlated reconstructions are not substitutes for matched nulls/independent data.

# 6. Figure / 문서 상태

See `06_FIGURE_DOCUMENT_LEDGER.md`.

- No active C2/C4 observed-analysis figure set exists yet.
- R3 29p and pedagogical 55p are preserved completed artifacts.
- Future figures require frozen M3 source, exact input manifest, units/frame, uncertainty law, generation code and caption claim ceiling.

# 7. Reviewer risks

See `07_RISK_REGISTER.md`. Highest risks: identification inflation; incomplete M1 joint law; local/global conflation; continuum→finite-pixel overreach; DESI frame/window defects; CF4 calibration/correlation misuse; trace/rank used as information; numerical error-enclosure completeness; post-hoc scientific choices; process/test counts mistaken for scientific correctness.

# 8. P0–P3 backlog

See `08_P0_P3_BACKLOG.md`.

- P0: fresh state readback, one writer, keep execution release closed.
- P1: M1, M2, M3, then actual C0–C5 campaign.
- P2: focused native oracle tests used by implementation, selected finite-error statement, scientific figure audit, post-result article.
- P3: canonical/merge/public release, PR4 expansion, new surveys, native Bianchi/global-response extensions.

# 9. 즉시 실행 계획

See `09_RESTART_PLAN.md`.

Exact first action: fresh-read PR463 master/DAG and PR464 addendum; if unchanged, **write M1_CMB_MODEL**, not another plan. Do not dispatch Local Codex until M3 closes and `THEORY_FREEZE` is published.

# 10. 유지 규약

See `10_CONVENTIONS.md`.

Core workflow: MAIN does science/specification and review; Local Codex does workstation-dependent execution after freeze. One source writer. In-scope evidence-driven repair may iterate without repeated approval. Scientific model/prior/statistic changes return to MAIN. Non-force Git push/Draft PR, immutable readable returns; no automatic merge/ready/public visibility change.

# 11. Fresh-thread continuation brief

Use `02_CONTINUATION_BRIEF.md`. It is standalone, paste-ready and ends with the required instruction:

> Treat the attached handoff packet and inspected durable artifacts as the current source of truth. Reconstruct the canonical state before beginning new speculative work. Do not infer missing evidence from transcript summaries, and do not reopen deprecated branches unless new evidence creates a direct conflict with the current state.


---

## R7 successor design — 2026-09-08

사용자의 연구·코딩 설계 및 GitHub 게시 요청에 따라 [Tensor Joint R7](../../research_program/tensor_joint_r7/README.md)을 후속 실행 설계로 추가한다. [Local Codex plan](../../research_program/tensor_joint_r7/LOCAL_CODEX_PLAN.md), [26-node campaign DAG](../../research_program/tensor_joint_r7/campaign_dag.json), [보유 관측자료·외부 코드 연결](../../research_program/tensor_joint_r7/OWNED_ASSETS.md)을 함께 읽는다.

이 추가는 위 2026-09-07 snapshot의 완료 상태·관측 수치·M1/M2/M3/THEORY_FREEZE 기록을 변경하지 않는다. 후속 작업의 scheduling은 R7의 분기별 capability·law·method-validation 조건을 따른다. 전역 native 가설의 성공을 모든 분석의 전제로 두지 않으며, 결측·기각·비식별·계산 실패를 구분해 독립된 자료/방법 경로와 최종 과학적 합성을 계속한다. 과학적 전제나 입력 검증을 생략하는 release는 아니다.

이번 게시 범위는 검토된 해석적 연구와 설계·DAG 구조 검증이다. Production 구현, CAS, 합성/실자료 분석은 워크스테이션 Local Codex가 실행한다. 이전 무효화 DESI PR-151 수치는 재사용하지 않고 PR4/NPIPE 획득·분석 제외를 유지한다. 새 캠페인은 기존 numeric PR card 완료로 계산하지 않으며, 기존 canonical/mirror PR 상태는 보존한다. 실제 완료·미완료 근거는 [R7 closeout](../../research_program/tensor_joint_r7/state/CLOSEOUT.md)에 있다.

