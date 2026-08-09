# Harness Realignment, Gate Discharge Protocol, and Real-Data Re-Execution Campaign

**Document id:** `HARNESS-GATE-REDO-v1` · **Date:** 2026-08-02 · **Intended home:** `docs/research_program/`
**Audited revision:** HEAD `7214ef7` (`research/pr04-multicomponent`); PR-248…PR-275 merged
**Predecessors (adopted, in-repo):** `STAT_FOUNDATIONS_REVIEW_20260727` (typed foundation), `STAT_FOUNDATIONS_JUSTIFICATION_20260728`, `STAT_FOUNDATIONS_TENSOR_UPGRADE_20260730` + `tensor_foundations_oracle.py` + `proof_registry_two_pillars.yaml` (all incorporated verbatim as PR-259…275)
**Companion artefact:** `gate_disposition_and_redo_campaign.yaml` (machine-readable mirror)

**Claim posture.** Pre-solver planning document. Nothing here is a detection, a Bianchi-family identification, a geometry measurement, or a native-solver validation. It proposes deltas; owning code, contracts, CAS adjudications, and `AGENTS.md` remain authoritative. Every relaxation below is framed as the repo's own machinery already requires: a *meta-finding* carrying new evidence, an explicit discharge condition, and the review that authorizes it (`.agent-harness/context/FROZEN_DECISIONS.md`: "a proposed reversal is a meta-finding with new evidence and an explicit reopen condition"; `LONG_HORIZON_RESCUE_PR_ROADMAP` C0–C6 preamble: "더 강하게 바꾸려면 별도 claim-firewall review가 필요하다").

---

## 0. The one finding that orders everything else

`AGENTS.md:145`, verbatim:

> "After two consecutive assurance-only PRs, stop governance expansion. The next PR must deliver a named downstream scientific capability, data execution/integration, experiment, or interpretable result. Another harness/correctness repair counts only when a reproduced high-severity defect directly blocks that named task."

PR-268 through PR-275 are **eight consecutive assurance/proof/governance PRs** — theorem registry v3, Pillar-T core proofs, Pillar-T CAS, Pillar-S core, Pillar-S inference, blind synthetic integration, a data-admission preflight that admitted **zero of six** candidates, and a generated proof atlas. Not one produced a scientific result on data. The repo's own brake has been open for six PRs.

This is not a criticism of that work — the typed foundation is now genuinely complete and machine-checked, which is exactly what makes the next move safe. It is a sequencing verdict: **the correct next unit of work is not another gate, registry, or proof card. It is the re-execution campaign of Part IV.** The harness realignment (Part II) and the gate-discharge protocol (Part III) are the minimum enabling corrections — they are stale-state repairs and a discharge *protocol*, not governance expansion, and each is justified below by a reproduced defect that directly blocks the campaign. Everything in this document is arranged so that its center of gravity is real-data science, because the repository is now telling you, in its own enforced rule, that it must be.

---

## Part I — Incorporation audit of the tensor upgrade

The delivered package (spec + oracle + two-pillar registry) was incorporated, and incorporated *well*: the oracle landed byte-for-byte (`diff` of the proposal against `htt/src/common/tensor_foundations_oracle.py` is empty; all twelve `TF-*` propositions present), the two-pillar registry is hash-bound and loaded by `theorem_signatures_v3.py`, and the proof atlas (PR-275) subsumes and generalizes the two-pillar split into a three-axis structure (I/II pillars + 28 VT obligations + four evidence layers). The owner also went beyond the delivered PR-259…265 sequencing, adding PR-266…275, and deviated in several places that are, on audit, **defensible hardening** — most importantly a *conservative* one: `generic_orbit_separation_status` was kept `UNPROVEN` even after the catalogue-v3 four-axis CAS passed, with a dedicated CAS obligation (`vt_t8_global_separation_not_promoted`) forbidding the promotion the delivered spec would have permitted.

### I.1 Faithful

| Delivered | Landed as | Verdict |
| --- | --- | --- |
| Three-layer state (`CongruenceKinematics` incl. acceleration + `acceleration_normalization` enum, `VelocityFrameBundle`, `JointAnisotropyState` with mandatory `beta_semantic_role`) | `joint_anisotropy_state.py` | LANDED-FAITHFUL + hardening (added `GeometryState` fourth layer; `acceleration_normalization`↔`units_convention` cross-check) |
| Functional identity + `(x_φ, Q_φ, F_φ, Π_φ, G_{F,φ})` family with the §2.3 well-posedness table | `tensor_functionals.py` (PR-262) + `tensor_departure_statistics.py` (PR-264) | LANDED-FAITHFUL; `F_φ` mechanically refused for signed/pseudoscalar functionals; canonical `G_F` preserved |
| `ConditionalExceedanceSurface` (5 sampling laws, 5 conditioning sources, envelope, `OPTIMIZER_REQUIRED`) | `conditional_exceedance.py` (PR-265) | LANDED-FAITHFUL + hardening; the Bauer-principle trap the spec warned about is closed correctly (upper-quasi-convex-only routes to `OPTIMIZER_REQUIRED`) |
| Oracle TF-01…TF-12 | `tensor_foundations_oracle.py` | LANDED byte-exact |
| Two-pillar registry + proof atlas | `proof_registry_two_pillars.yaml` + `THEOREM_SIGNATURES_V3.yaml` + `report/PROOF_ATLAS.{md,json}` | LANDED-FAITHFUL, generalized |
| `ε_g` (acceleration Euler-slaving gradient bound) left unregistered | placeholder-only, `gradient_regularity_registered=false`, `numerical_ceiling_authorized=false` | LANDED-FAITHFUL — the prerequisite is honored by omission; no acceleration number ships anywhere |

### I.2 Six remaining gaps (the concrete residue of the upgrade)

These are the items the delivered spec prescribed that did **not** land or landed weaker. They are the natural content of a small "upgrade-completion" card, but note the governance brake: bundle them into the first *scientific* wave rather than shipping them as another standalone assurance PR.

1. **`WEAKLY_IDENTIFIED` never wired into the runtime gate.** The runtime `SourceSeparationGateStatus` (`open_set_response_classes.py:76-81`) is `{NOT_APPLICABLE, SEPARABLE_CANDIDATE, NON_IDENTIFIED, SUM_ONLY, MISSING_RESPONSE_PROVIDER}` — it lacks `WEAKLY_IDENTIFIED`; `NOT_APPLICABLE` occupies the slot the delivered spec assigned to the weak-ID state, and `IdentificationStatus.WEAKLY_IDENTIFIED` (`statistical_foundations.py:64`) has zero enum-qualified call sites in the runtime path. (The concept *is* named in the oracle — `tensor_foundations_oracle.py:984,1009` compute and label it, and TF-10's docstring states the full-rank-tiny-angle state "must not be reported as `SUM_ONLY`" — so the gap is the missing runtime wiring, not a missing idea.) In production the full-rank-but-tiny-principal-angle cell still lands in `SUM_ONLY`; PR-272 added a partial substitute (whitened weak-ID abstention) but not the status. **This gap directly blocks greenfield G8** (real local/global separation), so wiring it *counts* under the brake.
2. **No Jacobian-rank acceptance test gates catalogue-v3 construction.** The 9/12/15 transcendence-degree check exists only inside the oracle (TF-06), not as a construction-time rejection in `orbit_catalogue_v3.py`. A functionally incomplete catalogue can be built today.
3. **`uncovered_directions` missing from `AnisotropyTypeReport`.** The honesty field naming what the registered response cannot reach was not surfaced, though the null-space is available in `orbit_nonlinearity.py`. Blocks the "abstain honestly" half of G7.
4. **No reverse-martingale/Doob object binds to `DepthPath`.** The ZoA path (PR-266) is structurally nested but not sequentially calibrated; PR-271's finite tower identity is an exact-`Fraction` conditional-expectation check, not the Doob-bounded sequential object. Blocks G4's free calibration.
5. **Parity-sign combination refuses the dependent case instead of performing it.** PR-271's `exact_parity_sign_test` is a pooled exact binomial gated on `uniform_conditional_sign_vector`; the prescribed arbitrary-dependence arithmetic-mean e-value merge (`egs3_evalue_merge.py`, extant) is not wired to the parity lane. This is defensible (refusal is conservative) but leaves cross-rung parity power on the table.
6. **No (H2) estimator P-equivariance audit.** The parity-sign test's equivariance premise is a caller-asserted boolean, not an audited property of the estimator+mask+weighting. Real selection functions are not `b→−b` symmetric, so this must become an executed audit before G3 runs on real `a_lm`.

Two hygiene items also carry over: the PR-270 CAS adjudication sits outside `docs/generated/` (breaking the `*_cas_adjudication.json` glob convention), and `pr-270.md:3` still reads `REPAIRED_CANDIDATE_PENDING_FINAL_BOUND_REVIEW` while `:256` records `COMPLETED_SUCCESS`.

**Audit verdict.** Incorporation is faithful and, where it deviated, defensibly hardened. The six gaps are real but small, and — crucially — every one of them is a *prerequisite of a specific greenfield real-data analysis*, so closing them is scientific-capability work, not governance. Fold them into Wave R1.

---

## Part II — Harness realignment

The harness is mostly clean — `AGENTS.md`, `.codex/`, `harness_templates/`, `prompts/`, and most of `docs/codex_handoff/` carry no stale scalar-formalism text. The staleness is concentrated in a few high-traffic surfaces that a fresh agent reads *first*, and in two generated artifacts that are now factually behind HEAD. Each edit below names the reproduced failure it prevents (per `AGENTS.md:144`, no artifact without a consuming decision and a prevented failure).

### II.1 Stale text edits (do, don't annotate)

**H1 — `CLAUDE.md` §1 (line 23) and §5 (lines 55–60).** §1 presents `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}` as *the* comparator; PR-248/249 demoted it to a `LegacyProjectionReport` whose `forbidden_use` includes `claim-tier promotion`. §5 lists `ln B=+26.40`, `β=1.360e-3`, `F_Bayes=0.093±0.025`, `D_2=1002.086744 μK²` as "compatibility anchors." *Prevented failure:* an agent landing on `CLAUDE.md` first re-derives the pre-typed picture and re-exports `x_C` as the primary object. *Edit:* rewrite §1 to state that the primary object is `JointAnisotropyState`/the functional family, `x_C` is the `φ=⟨c,·⟩` legacy projection under BC1/BC2; keep §5 values but retag them explicitly `BC1_LEGACY_PROJECTION, forbidden: claim-tier promotion` and point to the typed owners (`MESAnchorSpec`, `tensor_departure_statistics`). The file's own header already says it is "not a second source of truth," so this is a correction, not a new artifact.

**H2 — `docs/codex_handoff/02_long_range_PR_backlog.md` (lines 426–427, 440, 820–837, 946) and its `docs/` twin.** The x_C kill rule ("Reject if x_C is exported without comparator/frame metadata") is now strictly weaker than PR-249's `LegacyProjectionReport` immutability; the "scalar Q/F/Pi vs morphology" framing predates the typed sector-stress model. *Prevented failure:* a backlog-driven agent implements the weaker rule and bypasses the type. *Edit:* replace the x_C kill line with a pointer to the `LegacyProjectionReport` BC1/BC2 contract; mark the Wave-9 "full-covariance MES synthetic programme" line superseded by PR-255/PR-271.

### II.2 Symbol/decision gaps (add the row the type already earns)

**H3 — `.agent-harness/context/SYMBOLS.md`.** The single canonical symbol table injected into every subagent lists eight evidence/graph objects and **none** of the PR-248…261 types. *Prevented failure:* every spawned subagent works without knowing `MESAnchorSpec`, `DepartureState`, `JointAnisotropyState`, `SectorStress`, `IdentifiedDepartureSet`, `LegacyProjectionReport`, `AnisotropyTypeReport`, `ConditionalExceedanceSurface` exist, and reinvents or contradicts them. *Edit:* add those eight rows (they are all tested and stable).

**H4 — `.agent-harness/context/FROZEN_DECISIONS.md`.** No PR-248…275 decision row exists; latest is `D-PR177-*`. *Edit:* add `D-TYPED-FOUNDATION` (records that the scalar→typed migration is frozen, reopen condition = a proof that BC1 is violated) so the migration cannot be silently reverted, and `D-GOVERNANCE-BRAKE-2026-08` (records that eight assurance PRs have run and the next substantive PR must be scientific per `AGENTS.md:145`).

*Justification basis for H3/H4.* These two add rows, so they are authorized by the `AGENTS.md:144` carve-out (a consuming decision — every subagent's correctness — plus a concrete prevented failure), not by the `:145` brake, which governs PR sequencing and would demand a *reproduced high-severity defect* for a harness repair. H1/H2/H5/H6 are corrections/regenerations of existing surfaces and add nothing.

**H5 — Rebuild the context pack.** `.agent-harness/context/CONTEXT_INDEX.json` `built_at: 2026-07-23` predates PR-248…275. *Prevented failure:* `AGENTS.md §1` mandates `build_context_pack.py` before spawning subagents; the current pack cannot inject any typed symbol. *Edit:* re-run `build_context_pack.py` after H3/H4.

### II.3 Regenerate the stale generated ledgers (blocking prerequisite for everything downstream)

**H6 — `docs/generated/claim_ledger.json` and `docs/generated/status_matrix.md` are frozen at `source_commit 60022d7a` = PR-252.** They contain 199 rows ending at `codex_dag.PR-252` and do not cover PR-253…275. *Scope, corrected:* these are *generated mirrors*; the canonical `pr_status.yaml` (which `CLAUDE.md` names authoritative) already carries `COMPLETED_SUCCESS` for PR-253…275, and the adjudication/science waves read the canonical ledgers, not this snapshot. So H6 is **not** a universal blocker — it specifically affects the publication/audit-package consumers that read these generated files (`check_publication_claim_freeze.py`, the external/research audit-package builders). *Prevented failure:* a publication-freeze or audit-package build scores the typed lane as nonexistent. *Edit:* regenerate at HEAD before any publication-freeze or audit-package step; a pure regeneration, not a claim change. (Priority: do it before Part III/IV *reporting*, not before their *execution*.)

### II.4 Prune the redundant string-blacklist doubles (optional, low priority)

Several forbidden-phrase string blacklists are now redundant with type-level `forbidden_use` (e.g. `filling_fraction._FORBIDDEN_F_METADATA_TERMS` vs `LegacyProjectionReport.forbidden_use`; the `BLOCKED_UNTYPED_DENOMINATOR` string status vs a typed enum). These can be retired *only* when the type provably covers every path the string caught — a test-backed change, deferrable, and explicitly **not** urgent. Listed for completeness; do not prioritize over science.

---

## Part III — Gate discharge & promotion protocol

The gate population splits cleanly, and the split is the whole protocol. Roughly three-quarters are **type-enforced invariants** — anti-laundering rules, ownership firewalls, refuted-theorem bans — that no evidence can or should discharge. The remaining quarter are **evidence-conditional blockers** that discharge on named events. The protocol's job is to (a) never touch the first class, (b) give the second class a disciplined, auditable discharge path, and (c) identify the one gate whose discharge is *pure process* and therefore available now.

### III.0 The meta-rule every discharge obeys

A gate discharge is a `FROZEN_DECISIONS`-style meta-finding with four mandatory fields: **gate id**, **discharge evidence** (the artifact/receipt that satisfies the gate's own stated exit condition, verbatim), **new state**, **authorizing review** (which reviewer/CAS/adjudicator signs it). A discharge that cannot fill all four is not admissible. Strengthening the C0–C6 mapping additionally requires a separate claim-firewall review (roadmap preamble). This protocol never weakens a gate; it records when a gate's *own* exit condition has been met.

### III.1 Never relax — the structural class (enumerated so the campaign never trips them)

The `egs_oneway` 26-phrase converse ban (backed by a sealed counterexample family), the `P36`/`T2p` retractions, the refuted non-geodesic MES triples, `LegacyProjectionReport` BC1/BC2 immutability, the MIO/HTT/OBSSTAT ownership `forbidden_use` lists, `ANISOTROPY_TYPE_FAMILY_GATE = BLOCKED_PRE_NATIVE_ATLAS`, the three `ORBIT_V3_*_UNPROVEN` pins, `_state_payload` content-addressing, the CAS five-state/no-majority rule, the 12 strict `pdf_claim_lint` names, `CLAIM_GATES` rows 1/3/4/6, and the 24 anti-laundering kill rules of PR-248…275. These encode a proved impossibility, a refutation, or an architecture boundary. **The campaign is designed to operate entirely within them** — it never needs one relaxed.

### III.2 Tier 0 — dischargeable NOW (bookkeeping; no evidence event required)

| Gate | Discharge evidence (already exists) | New state |
| --- | --- | --- |
| `9.25e-6` as an active cross-sector denominator | PR-248 F2 already removed active cross-sector filling; typed `LEGACY_S2A_CATWISE_SIGMA2` | retire the now-redundant surrounding string blacklist (Tier-0 hygiene) |
| `filling_fraction._FORBIDDEN_F_METADATA_TERMS` | `LEGACY_REPRODUCTION_ONLY=True` + `LegacyProjectionReport.forbidden_use` supersede it | mark redundant-with-type (H2.4) |
| `BLOCKED_PLATFORM_OR_LICENSE` / `BLOCKED_{SAGE,WOLFRAM,LEAN}_*` / `BLOCKED_CAMB_UNAVAILABLE` (~110 sites) | `AGENTS.md:253` already classifies engine non-install as a platform blocker, not a science exception | install toolchain → discharge mechanically; no claim-firewall review needed |
| Harness staleness H1–H6 | Part II | edit/regenerate |
| The 2 open `pdf_claim_lint` findings | `BLOCKERS.md:88` names the fix as manuscript text or hash-bound exemption | manuscript-text fix |
| 6 stale-generated-artifact contract failures | `BLOCKERS.md:75-92` names the durable fix (drop `git_commit_or_worktree_state` from emitted artifacts) | a one-shot refactor card |

### III.3 Tier A — the highest-leverage move: per-lane independent adjudication (PR-157 split)

This is the crown of the protocol. Three facts, all self-verified:

1. The adjudication ledger records **20 families `PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION`**, **62 `dual_axis_claim_ledger` rows all `EVIDENCE_READY` with `independence_gate: open`**, and states the limit verbatim: *"adjudication capacity spend-limited"* — i.e. process, not evidence.
2. PR-157 has never run and is transitively pinned behind PR-151 (`background_in_progress`), PR-155, PR-156 (`pending`).
3. **PR-157's own kill rule (`pr_backlog.yaml:3887`) permits per-lane resolution:** *"PR-143–156 중 terminal receipt가 하나라도 없거나 … 해당 lane은 미판정 또는 downclaimed/rebuild_required/blocked로 유지한다."* A lane lacking a terminal receipt stays **미판정 (unadjudicated)** — it does **not** block the other lanes.

**Therefore:** the 20 families whose evidence is ready and whose upstream PRs *do* carry terminal receipts can be adjudicated **now**, per-lane, leaving `D-DESI` (blocked on PR-151) and any other receipt-incomplete lane `미판정`. This is fully inside PR-157's kill rule; it is not a relaxation, it is the intended per-lane semantics that the all-or-nothing reading obscured.

**Proposed action (a genuine scientific-capability step, brake-compliant):** commission the independent non-author panel on the subset `{families with terminal receipts AND independence_gate open}`. Their upstream cards are PR-125…152/177…227, all `COMPLETED_SUCCESS` in `pr_status.yaml` (the one exception, PR-192, is one of T-OMK's three cards; the other two are terminal), so the 20 are receipt-complete and independent of the pending PR-151/155/156 lanes — the per-lane split is real, not aspirational. Expected unlock: up to 20 families move from `EVIDENCE_READY / independence:open` to `conditional` (or `validated` candidate where the C-ladder permits). Staying put (8 families, with a recorded reason each): `D-DESI` (blocked on PR-151), the three `BLOCKED_ON_NATIVE_SOLVER` families, the three `GENUINELY_INCOMPLETE` families, and `M-DUALAXIS` (`PROCESS_GATE_NO_LITERATURE_AXIS`). One nuance: PR-157 *as a monolithic DAG node* stays blocked (its `dependency_contracts` require terminal receipts from all 14 upstreams incl. PR-151/155/156); the action here is a per-lane process step the kill rule explicitly authorizes, not a completion of PR-157. This single action has the highest ratio of claim-envelope movement to effort in the entire repository, and it needs no data and no solver.

*Guard:* the panel must be genuinely non-author (the ledger header: "the Independence gate is never fake-passed"); a `blocked/abandoned` receipt closes aggregation for its lane but can never become a rescue vote (PR-157 kill rule). The 102-row criticism matrix stays `0 rescued` for any lane touching the CF4 P0.

### III.4 Tier B — event-gated (discharge condition is a named future event)

| Event | Gates it discharges | Where it sits |
| --- | --- | --- |
| **PR-151 terminal** (all 1025 mock records pass checksum + compact-random auth + rehash) | `D-DESI`, `BLOCKED_ON_PR151_TERMINAL`, the DESI official-mock lane, and it unpins PR-155→156→157 | acquisition `background_in_progress`; **note the estimand is BGS_BRIGHT-21.5, 0.1≤z≤0.4 — a different sample from the measured BGS_ANY dipole, so a new result, not a recalibration** |
| **CF4 P0 five-way conjunction** (authenticated lineage + nonlinear release-matched mocks + nuisance-orthogonal E2E coverage + all-consumer regeneration + non-author adjudication) | `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP`, `BLOCKED_UPSTREAM`/PR08-006, the entire `cf4_p0_quarantine`, 5 `QUARANTINED_OPEN_P0` rows, the obs_defaults channel-c exclusion, `CLAIM_GATES` row 2 | conjunctive; no partial credit |
| **CF4 WF residual covariance / operator** | `BLOCKED_MISSING_FIELD_REALIZATIONS` (K6 definitive ensemble) | rev-r198 already has the real-field measurement; only the operator is missing |
| **Native low-ℓ Bianchi–Boltzmann solver + atlas (PR10)** | `AWAITING_NATIVE_LOWELL_SOLVER`, `BLOCKED_PRE_NATIVE_ATLAS`, `BLOCKED_NATIVE_REQUIRED` (83 sites), the 9 `blocked`-ceiling cards PR-159…166+183, C5/C6, 3 `BLOCKED_ON_NATIVE_SOLVER` families | the hard claim ceiling; EGS3-B1 is a partial (one-mode) discharge and also gates `FOUND-EQUIV` |
| **Reviewed write to `PR274_DATA_IDENTITY_REGISTRY.yaml` + execution authorization** | PR-274 `NO_ADMITTED_DATA_PILOT` → admits a real dataset; unlocks the entire typed observed-data lane (G1–G11) | the single gate between the typed foundation and its first real number |
| **PR4/NPIPE authenticated inputs + explicit user direction** (`D-PR4-SKIP` reopen) | residual half of `BLOCKED_MISSING_PR4_E2E_ACCESS` | user-decision-gated |
| **B-projector repair** | PR-172 `BLOCKED_METAMORPHIC_RELATION_VIOLATION` (the one `blocked` card in `pr_status`) | a code fix |

### III.5 What the protocol explicitly does **not** do

It does not lower any claim-tier ceiling, weaken any `forbidden_use`, promote any `UNPROVEN` status, rehabilitate the refuted MES triple, or authorize a family label without the native atlas. Every Tier-B discharge turns a synthetic stand-in into a calibrated measurement and *never* authorizes a Bianchi-family, geometry, or native-solver claim — this is `BLOCKERS.md`'s own invariant, preserved.

---

## Part IV — Real-data re-execution campaign

Two structural facts bound the whole campaign and must be settled before any wave runs. First, **`legacy/` and `workdir/` are untracked and absent from the checkout** — every "byte-frozen" CF4 P0 artifact and every E2E cache exists only as a hash, so re-execution requires re-acquiring those trees. Second, **the typed lane currently holds zero real-data results** (PR-274 admitted 0 of 6; PR-275 is 5 synthetic cases). The campaign's purpose is to move real numbers from the V1/V2 lanes into the typed lane under BC1 (old numbers preserved as legacy projections) and to run the greenfield analyses the typed foundation newly enables.

Of ~45 real-data (or real-data-adjacent) artifacts back-traced, the classification is: **~20 REDO-REQUIRED, ~14 REDO-UPGRADE, ~5 PRESERVE, ~6 BLOCKED.** The companion YAML enumerates the artifacts by wave (not as a single 45-row disposition table); the waves below organize the work.

### Wave R0 — prerequisites (no science yet; unblocks everything)

R0 is the enabling layer and is the only wave that is pure infrastructure. (a) Regenerate `claim_ledger.json`/`status_matrix.md` at HEAD (H6). (b) Re-acquire or re-locate the `legacy/`+`workdir/` trees and re-verify against their committed hashes; without this, no REDO of any CF4/E2E number is reproducible. (c) Close the six upgrade gaps of §I.2 that gate specific greenfield analyses (`WEAKLY_IDENTIFIED` wiring, Jacobian-rank acceptance, `uncovered_directions`, DepthPath Doob object, parity e-value merge, estimator P-equivariance audit). (d) Populate `PR274_DATA_IDENTITY_REGISTRY.yaml` for the one dataset R1 starts with, via the reviewed authority change PR-274 requires. R0 is brake-compliant because every item directly unblocks a named R1/R3 analysis.

### Wave R1 — REDO-UPGRADE: recompute sound results under typed contracts (BC1 preserves the old numbers)

These 14 results are computationally sound but scalar/componentwise; recomputing them as `SectorStress` + `ConditionalExceedanceSurface` + partial-ID intervals produces the typed lane's *first real numbers*, with BC1 keeping every legacy value as a legacy projection. None needs a blocked event. Priority order (by leverage and readiness):

1. **K1 low-ℓ (PR-150 pooled rank `p=0.039`, bootstrap `[0.0263, 0.0532]`; BipoSH SI `p=0.681/0.649`; even-L `p=0.195`; PR-180 boost residual `p=0.854`)** → recompute per-sector `s_Σ/s_ω/s_β` on the real Planck PR3 `a_lm` (greenfield G1 rides this), and re-express the boost residual through the exact parity-sign lane (G3). The bootstrap straddling α=0.05 is exactly the case the typed envelope reports honestly.
2. **DESI dipole (`D=9.49e-3`, `13.55σ` above shot noise, `p=0.90` vs ΛCDM)** → typed as an amplitude `SectorStress` + Fieller interval; BC1-preserve the numbers.
3. **ACT DR6 lensing (`p=0.35`, UL `<3.28e-6`)** → typed exceedance surface.
4. **PR-179 H-only (`2/20000`), PR-153 JWST distance consistency (`Δ=−0.008±0.018 mag`)** → typed conditioning.
5. **K6 per-cell CR → correlated-residual CR** (already superseded by rev-r198 on the real field; recompute the posterior as `s_ω` sector stress, PRESERVE the `curl/div=0.0089` structural no-go).
6. **Result packs A/B/C** → regenerate as typed `x_φ/Q_φ/Π_φ` + `SectorStress` crosswalks.

### Wave R2 — REDO-REQUIRED: results condemned by defect, not merely vintage

These ~20 cannot be BC1-preserved as science because the estimator itself is defective; they must be re-derived, not re-typed. The gating defect is **`D-STAT-BAYES-SEMANTICS`**: the shared-cause "Bayes factor" is a fitted log-likelihood difference that shipped as `+29.7` and reproduces as `−1035.461` at HEAD, with degenerate nulls at `−3893…−3899` and plug-in residuals mislabeled PPC/LOOCV (`atomic_finding_ledger.json:343,373`). *Scope note:* the finding's literal `impact_object` is the shared-cause Bayes factor; extending "condemned" to the whole V1 chain (the `ln B` ladder, `F_Bayes`, `Q̄`, the Π_HTT table, the ch07/ch08 tables) is a methodological *inference* — the same nested-sampling/fitted-likelihood machinery produced them — not a second finding. The conservative disposition follows regardless: they stay legacy-only pending the fix. Its decisive falsifier (stated in the finding) is the prerequisite for the whole evidence lane: **register normalized priors and likelihoods, and reproduce the marginal evidence with two independent engines.** Until that lands, the entire V1 Bayesian chain (`ln B=+26.40`, `β=1.360e-3`, `F_Bayes=0.093±0.025`, `Q̄=0.092 [0.035,0.19]`, the Π_HTT table, and the ch07/ch08 evidence/decomposition/scenario/PPC/robustness tables) stays legacy-only. R2 therefore has two sub-steps: **R2a** — fix the estimator (two-engine normalized marginal evidence) — and **R2b** — recompute the lane, where the typed successor is *not* a Bayes factor but a `SectorStress` + `ConditionalExceedanceSurface` + partial-ID envelope + `AnisotropyTypeReport` abstention. Also in R2: the one genuinely defective K1 surface (`lowell_morphology_real_map_report.json`: `diagonal_fiducial_cl_only` + no mask deconvolution + look-elsewhere tracked-not-corrected), which must be recomputed with a proper covariance and mask deconvolution.

### Wave R3 — greenfield: typed analyses never run on real data (G1–G12)

Gated on PR-274 admission (R0d). These are the analyses the whole upgrade was *for*: per-sector stress on real Planck multipoles (G1), conditional exceedance envelopes (G2), exact parity-sign tests on real low-ℓ `a_lm` (G3), depth-path coherence on CF4 (G4), the orbit-invariant catalogue on real `(σ,ω,β)` estimates (G5), Fieller partial-ID on a real estimand (G6), the abstaining `AnisotropyTypeReport` (G7), typed local/global separation on real CF4+DESI (G8), and the rest. G1–G3 ride R1's admitted Planck dataset; G4–G8 wait on the CF4/DESI events of Tier B.

### Wave R4 — BLOCKED lane (execute when the Tier-B event fires)

The six hard-blocked items, each paired to its event: CF4 amplitude/fσ8/global-tilt chain (CF4 5-way), PR-151 official-mock DESI result (PR-151 terminal — *new sample, not a recalibration*), ACT RDN0 (QE pipeline), K6 definitive ensemble (WF operator), PR-179 `q_cat` block (response-identifiability), PR08-006 join (upstream CF4 P0). No work now beyond keeping the typed interfaces ready to consume them.

### Campaign sequencing and the brake

```
R0 (prereqs, unblocks) ─┬─> R1 (typed real numbers, BC1)  ──> Tier-A adjudication of R1 lanes
                        ├─> R2a (fix evidence estimator) ──> R2b (re-derive evidence lane)
                        └─> R3 (greenfield, on R0d admission)
Tier-B events, as they fire ──> R4
```

R0 and R1 together are the "named downstream scientific capability" the governance brake demands; they should be the next PR wave, ahead of any further proof/registry card. R2a is the single most valuable correctness fix in the corpus (it condemns or rescues the entire evidence lane). Tier-A per-lane adjudication (III.3) can run in parallel with R0/R1 since it needs no data.

---

## Appendix — verification receipts (2026-08-02, HEAD `7214ef7`)

`AGENTS.md:145` governance brake quoted verbatim; PR-268…275 titles confirmed all assurance/proof/governance (8 consecutive). `docs/generated/claim_ledger.json` `"source_commit": "60022d7a"` = PR-252 (stale vs HEAD). `CLAUDE.md:23` carries `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}` as the project-identity comparator; `:55-60` the four historical anchors. PR-157 kill rule `pr_backlog.yaml:3887-3889` confirmed to permit per-lane `미판정` (the Tier-A basis). Incorporation, gate-inventory, and real-data back-trace details are the three read-only sweeps summarized in Parts I, III, IV; per-artifact and per-gate rows are in `gate_disposition_and_redo_campaign.yaml`.
