# Next Session Bootstrap Prompt (self-updating)

**How to use this file**:

1. A fresh Claude Code session copies the ````bash` fenced "Current handoff prompt" block (§2) and pastes it as the first message
2. That agent works through the tasks specified in the prompt
3. **Before the final commit**, the agent executes §3 "End-of-session self-update procedure" — replacing the §2 block with the next session's bootstrap prompt
4. The updated file is committed alongside the session's code

This way the file is a **living handoff contract**: one always-current prompt + a persistent recipe for rotating it.

**Last rotated**: 2026-04-20 (**FB-4.1 actual-work → FB-4.2 actual-work**; the Layer-B Thomson seed is landed locally and the handoff advances to the E↔B rotation replacement)
**Last audited**: 2026-04-20 — see `docs/audits/AUDIT_PHASE_FB4_2026-04-20.md`
**Current target session**: **FB-4.2 actual-work** — replace the tilted E↔B skeleton using the canonical Phase FB-4 prompt
**Phase status**: FB-4.1 is complete locally. The current close-gate suite reaches `3425 passed + 72 skipped + 3 errors`; the only remaining whole-suite blocker is the missing `data/camb_ref_planck2018.npz` fixture at LB-6-19/20/21.
**Phase-boundary audit prompt**: `docs/audits/AUDIT_PROMPT.md` (run before every next-phase commit)

---

## 1. Self-updating contract (STABLE — do not modify per session)

Every agent that consumes §2 inherits this contract:

- The **last substantive action before final commit** is to update this file's §2 block so the next agent can bootstrap themselves
- Update the "Last rotated" timestamp at the top of this file
- Update the "Current target session" line
- The update recipe is in §4 (Template library); pick the template corresponding to the NEXT LB-N session
- Commit message for the final commit MUST include a line mentioning the next-session handoff (e.g. "+ rotate NEXT_SESSION_PROMPT for LB-N+1")
- If the next session is not obvious (unexpected scope change, blocker discovered), replace §2 with an explicit "BLOCKED" prompt describing what the following agent needs to unblock before coding resumes

This contract is **non-negotiable**. Skipping it breaks the chain.

---

## 2. Current handoff prompt (ROTATE at end of each session)

Copy the block below into a fresh Claude Code session:

```text
# FB-4.2 actual-work — paste the Phase FB-4 prompt and execute only the second rotation

Phase FB-4.1 actual-work is now closed locally.

Before starting FB-4.2, read:
- `docs/audits/AUDIT_PHASE_FB4_2026-04-20.md`
- `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-4`
- `docs/manuscript/ch05_teff_corrections.tex §sec:tilted-thomson-layer-b`
- `docs/manuscript/ch04_bianchi_bounds.tex` (Robustness paragraph)
- `scripts/make_physics_gallery.py` Topic 10 addition `plot_10_04_thomson_beta_sweep_Dl`
- `figures/physics_gallery/10_collision_and_visibility/04_thomson_beta_sweep_Dl.png`

FB-4.1 carry-forward pins:
- Layer-B runtime changes live only in `htt/bass/collision/`; `htt/`
  remains intentionally unstaged by contract.
- The shipped Layer-B boost is axis-aligned only; arbitrary-direction
  Wigner-d rotation is still reserved for **FB-5.2**.

Regression anchor:
- `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
  → `3425 passed, 72 skipped, 3 errors`
- The 3 errors are still the pre-existing CAMB fixture blocker at
  `bass/integration/test_lowell_bianchi.py::TestLBCAMBMatch::{LB_6_19,LB_6_20,LB_6_21}`
  because `data/camb_ref_planck2018.npz` is missing in the dirty worktree.

Next action:
- Paste the canonical **FB-4 actual-work** prompt as the first user
  message, but execute only the FB-4.2 rotation. Do not reopen FB-4.1.
```

---

<!-- Prior (FB-META-9) handoff prompt (archived 2026-04-20). -->

<details>
<summary>Previous FB-META-9 handoff prompt (archived 2026-04-20)</summary>

```text
# FB-META-9 — paste the Phase FB-9 META prompt

Phase FB-8 closed with seven committed skeleton plants and the audited
baseline now stands at `3,403 passing + 60 skipped`.

Start the next session by pasting the canonical Phase FB-9 META prompt
as the first user message. Do not reuse the older FB-META-8 handoff
text; the next phase should begin from a fresh prompt.

Important carry-forward scope pin:
- The observer-frame layer is now skeleton-planted across
  `bass.observer` and `bass.likelihood.observer_frame_adapter`.
- The load-bearing distinction `(beta_cosmo, v_hat_cosmo) != (beta_obs,
  v_hat_obs)` is pinned in code, docs, and the FB-8 audit.

Relevant carry-forward anchors:
- Repo root: `/home/cosmosapjw/Dropbox/bianchi/htt_base`
- Latest audited Phase FB-8 artifact:
  `docs/audits/AUDIT_PHASE_FB_META8_2026-04-20.md`
- Observer-frame package:
  `htt/bass/observer/`
- Observer-frame likelihood wrapper:
  `htt/bass/likelihood/observer_frame_adapter.py`
- Successor development log:
  `docs/lowell_bianchi/extended_coverage/DEVELOPMENT_LOG_FB8_ONWARD.md`
- Explicit source gaps preserved in the FB-8 audit:
  EMM 2012 `§5.2` preview, the prompt's `Wald 1984` locator, and the
  missing on-disk Lowell `§14` reference.
- Latest audited Phase FB-7 close note:
  `docs/audits/AUDIT_PHASE_FB_META7_2026-04-20.md`
- BASS likelihood package:
  `htt/bass/likelihood/`
- Latest regression anchor:
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
  → `3403 passed, 60 skipped`
```

</details>

<!-- Prior (FB-3.3) handoff prompt (archived 2026-04-20). -->

<details>
<summary>Previous FB-3.3 handoff prompt (archived 2026-04-20)</summary>

```text
# FB-3.3 — Einstein + tilt coupling (additive completion of `accel_from_tilt`) + first boost-kernel `B(η, ê)` projection (Phase FB-3 third rotation)

## 프로젝트 컨텍스트

- **Repo root**: /home/cosmosapjw/Dropbox/bianchi/htt_base
- **bass-py 소스 트리**: `htt_base/htt/` (has `bass/`, `tsc/`, `mio/`, `workspace/`, `conftest.py`, `pyproject.toml`)
- **venv**: `htt_base/venv/bin/python` (주의: `venv/bin/pip` shebang → `../venv/bin/python -m pip ...` 로 우회; FB-2.3 P3 env carry-forward, post-FB devops 에서 rebuild 예정)
- **테스트 명령**: `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 3,189 passing + 1 skipped (FB-3.2 직후; §FB-3.2 supplement in `docs/audits/AUDIT_PHASE_FB3_2026-04-19.md`)
- **완료된 단계**: LB-0 … LB-6 + LB audits P2/P3 cleanup + Phase FB-0 + Phase FB-1 + Phase FB-2 + **FB-3.1** + **FB-3.2 (tilt kinematic adapters + driver wire-up)**:
  - FB-3.1 (`bass/species/tilted.py::TiltedSpeciesBackground`: β=0 bit-identical; EMM §5.4 eqs (5.12)-(5.13) exact at β>0; FB02-F1 resolved)
  - **FB-3.2** (`bass/hierarchy/tilt_kinematics.py::{accel_from_tilt, vorticity_from_tilt}`: β=0 `np.zeros(3)` short-circuit; β>0 emits `A^a = γ² v^a` (EMM eq 5.14 species-specific piece) and `ω^a = (1/2) a × v` for Class B (Pontzen-Challinor 2009 §2); β=0 adapter-fed driver byte-identical to FB-2.4 anchor on 12 labels; 57 new tests; baseline 3,132 → 3,189)
- **현재 phase**: **Full Bianchi Coverage (FB) — Phase FB-3 "Tilted sector non-perturbative β" (FB-3.3, third rotation)**.
- **전체 로드맵**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-3`
- **Carry-forward P2/P3 (알고만 있을 것, 절대 건드리지 말 것)**:
  - F3 (doc-only) → `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² rescale → **FB-5 / FB-6 예약**
  - FB11-F1 → W-E Table 11.1 fixed-point coords → **FB-5 / FB-6 예약**
  - FB12-F1 → IX isotropic S_+ residual (W-E pathology) → **FB-5 / FB-6 예약**
  - FB12-F3 → `bianchi_ix_recollapse_event` ↔ `_hubble_squared` 결합 → **FB-5 / FB-6 예약**
  - FB13-κ-calibration → VII_h Pontzen-Challinor spiral κ → **FB-5 / FB-6 예약**
  - **FB-2.1 P2** → complex-dtype `nabla_dispatch` → `hierarchy_rhs_photon` real-dtype driver wire-up → **FB-5.1 예약**
  - **FB-2.3 P3 (env)** → `venv/bin/pip` shebang stale → post-FB devops
  - **FB-3.1 P2 (β-gate)** → velocity vs rapidity parametrisation formal unification audit → **FB-3.5 예약**
  - **FB-3.2 P2 (new)** → Class A vorticity harmonic-mode piece `ε^{abc} ∇̃_b v_c` → **FB-5.1 예약** (perturbation sector wire-up with complex-dtype dispatch)
  - **FB-5.2** → off-axis helical Wigner rotation for 비-axis-aligned subset

## 이 세션의 작업 범위 (FB-3.3 — Einstein + tilt coupling + boost-kernel seed)

**Goal**: FB-3.2 이 `accel_from_tilt` 의 species-specific 피스 (`γ² v^a`) 를 배치했다. FB-3.3 는 **나머지 두 피스를 additively 완성** 하고, 동시에 PSTF multipole 에 대한 **first non-perturbative boost kernel projection** 을 seed 한다:

1. **Einstein + tilt coupling** — `accel_from_tilt` 의 else-branch 를 다음 exact form 으로 확장:

       A^a = γ² [ v̇^a + (Θ/3) v^a + σ^a_b v^b ]     (EMM 2012 eq 5.17)

   FB-3.3 surface 에서 `v̇^a = 0` (constant-β 가정, ∂v/∂τ = 0 at background); 따라서 실제 확장은 `(Θ/3) v^a + σ^a_b v^b` 두 piece. 이는 background Θ(η) 와 σ_ab(η) 를 소비하므로 adapter signature 를 `accel_from_tilt(tilted, eta, *, bg_table=None, tetrad_state=None)` 로 확장 (kwargs 기본값 None → FB-3.2 output 과 bit-identical).

2. **Tilted-shear feedback** — `TiltedSpeciesBackground` 가 누적한 β>0 energy density `ρ̃` 가 Bianchi Einstein equations 의 RHS 에 들어가 σ_ab 의 trajectory 를 수정한다. FB-3.3 에서는 이 feedback 을 `bass/background/einstein_bianchi.py::rhs_bianchi` 에 **optional** 하게 넣고, β=0 경로 bit-identical 유지.

3. **Boost-kernel `B(η, ê)` seed** — LB-4 `TiltedVisibility` 가 저장하는 rapidity `β_rapidity = atanh|v_e|` 과 FB-3.2 velocity `β` 사이의 composition rule `v_e = β · v̂_e` 를 FB-3.3 에서 단일 함수로 통합. `bass/hierarchy/boost_kernel.py` (새) 에 axi-symmetric PSTF boost projection 의 seed 함수 `boost_project_axisymmetric(Pi_ell, beta, v_hat_e)` 를 배치. FB-3.5 reparametrisation audit 대비 formalism 고정.

4. **Gallery**: FB-3.2 는 no-op 이었으나 FB-3.3 는 β>0 trajectory (11 types × β ∈ {0, 0.05, 0.1}) 를 생성할 수 있는 첫 rotation. gallery_06_tilt_boost 확장 후보.

### 기준이 되는 문헌 타깃

- King-Ellis 1973 §3-§4 (exact tilt 4-acceleration, eq 37-40)
- Ellis-Maartens-MacCallum 2012 §5.4-§5.5, §14.3 (Einstein + tilt; shear evolution under tilt)
- Pontzen-Challinor 2009 §2-§3 (Class B tilted cosmology + vorticity feedback)
- Pontzen-Challinor 2011 §3 (boost kernel on PSTF moments; axi-symmetric case)
- lowell §7-§8 (tilt + transport SSOT)

### 구체 작업 항목

1. **사전 읽기**:
   - `docs/audits/AUDIT_PHASE_FB3_2026-04-19.md §FB-3.2` (carry-forward)
   - `bass/hierarchy/tilt_kinematics.py` (FB-3.2 surface)
   - `bass/hierarchy/hierarchy_rhs.py::proper_shear_at_eta` (σ(η) consumer pattern)
   - `bass/background/einstein_bianchi.py::rhs_bianchi`
   - `bass/collision/tilted_visibility.py` (rapidity surface)
   - `docs/audits/AUDIT_PROMPT.md` (phase-supplement audit — self-invoke)

2. **`accel_from_tilt` 확장**:
   - 새 kwargs: `bg_table=None`, `tetrad_state=None`
   - 두 kwargs 가 None 이면 FB-3.2 output 과 bit-identical (anchor 보존)
   - 둘 다 supplied 되면 `γ² v^a + (Θ/3) γ² v^a + γ² σ^a_b v^b` 를 return; Θ(η) = `bg_table.interp_Theta(eta)`, σ_ab(η) = `proper_shear_at_eta(eta, tetrad_state, a)`
   - ValueError 로 malformed input (shape guards) 보호

3. **Tilted-shear feedback** (optional, FB-3.3 에서 기본 off):
   - `rhs_bianchi(..., tilted_species=None)` kwarg 추가; None 이면 기존 FLRW/Bianchi trajectory bit-identical; supplied 되면 `ρ̃` 를 Ω_m / Ω_r 대신 사용

4. **`boost_kernel.py` seed**:
   - `boost_project_axisymmetric(Pi_ell, beta, v_hat_e) → Pi_ell_boosted`
   - `beta=0` → input identically return
   - `|v̂_e × e_z| > tol` 이면 **NotImplementedError** (off-axis → FB-5.2); FB-3.3 은 axi-symmetric subset only
   - PSTF invariants 보존 (sym_trace_free 후 check)

5. **Validation tests** (≥ 20):
   - `accel_from_tilt` bg_table+tetrad_state 없는 호출 → FB-3.2 output 과 `np.array_equal`
   - `accel_from_tilt` 두 kwargs 모두 supplied + β=0 → zeros
   - β>0 × 3 sample η 에서 closed-form 검증
   - `rhs_bianchi` β=0 bit-identical (기존 trajectory regression)
   - `boost_project_axisymmetric(β=0)` = input identity
   - `boost_project_axisymmetric(β>0)` PSTF invariant 보존
   - off-axis v̂_e → NotImplementedError

6. **Audit**: `AUDIT_PHASE_FB3_2026-04-19.md` 에 §FB-3.3 supplement 추가

7. **Gallery**: β>0 trajectory 생성 시 `plots/physics_gallery/06_tilt_boost/05_hierarchy_beta_sweep.png` 신설; no-op 이면 audit 에 명시

8. `NEXT_SESSION_PROMPT.md §2` 를 **FB-3.4** (full tilted trajectory integrator + β>0 end-to-end regression + Thomson Layer A / B 접합) bootstrap 으로 rotate

### FB-3.3 non-goals (선 밑에 고정)

- **Off-axis helical Wigner rotation** → **FB-5.2**
- **β-gate reparametrisation (velocity ↔ rapidity formal unification)** → **FB-3.5**
- **Thomson kernel Layer B (full Lorentz on collision)** → **FB-4**
- **k ≠ 0 perturbation sector** → **FB-5**
- **Complex-dtype `nabla_dispatch` harmonic-mode wire-up** → **FB-5.1**

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_FB3_2026-04-19.md §FB-3.2` (carry-forward + P2 ledger)
2. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-3`
3. `bass/hierarchy/tilt_kinematics.py` (FB-3.2 surface)
4. `bass/hierarchy/hierarchy_rhs.py::proper_shear_at_eta` (σ(η) spline consumer)
5. `bass/background/einstein_bianchi.py::rhs_bianchi`
6. `bass/collision/tilted_visibility.py` (rapidity surface for FB-3.5 prep)
7. King-Ellis 1973 §3-§4; EMM 2012 §5.4-§5.5; Pontzen-Challinor 2009 §2-§3
8. `docs/audits/AUDIT_PROMPT.md` (self-invoke)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (King-Ellis 1973 + EMM 2012 §5.4 / §5.5 / §14.3 + Pontzen-Challinor 2009 + lowell §7)
3. PSTF invariants preserved; Ellis convention 유지; **β=0 경로 bit-identical** against FB-3.2 anchor
4. No silent fallbacks — missing kwargs → FB-3.2 identical; out-of-range inputs → explicit ValueError; off-axis v̂_e → NotImplementedError (FB-5.2 defer)
5. Determinism
6. **FB-3 phase in progress** — FB-3.3 는 FB-3.2 의 additive 확장; 새 surface 가 기존 anchor 를 흔들면 안 됨

## 검증 체크리스트 (최종 commit 전)

- [ ] `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 3,189 + 신규 테스트)
- [ ] `accel_from_tilt(tilted, eta)` (no bg_table/tetrad_state) output 이 FB-3.2 commit 과 `np.array_equal`
- [ ] `accel_from_tilt(tilted, eta, bg_table=..., tetrad_state=...)` at β=0 → zeros
- [ ] `rhs_bianchi(..., tilted_species=None)` trajectory 가 기존 anchor 와 bit-identical
- [ ] `boost_project_axisymmetric(Pi, β=0)` = input identity
- [ ] off-axis v̂_e → NotImplementedError
- [ ] `AUDIT_PHASE_FB3_*` §FB-3.3 supplement 추가
- [ ] Gallery 재생성 또는 no-op 명시
- [ ] `NEXT_SESSION_PROMPT.md §2` → **FB-3.4** bootstrap 으로 rotate
- [ ] 최종 commit 메시지: `FB-3.3: Einstein+tilt accel completion + boost-kernel seed` + `+ rotate NEXT_SESSION_PROMPT for FB-3.4`

## 진행 순서

1. `docs/audits/AUDIT_PROMPT.md` self-invoke (pre-session scan)
2. FB-3.2 `accel_from_tilt` / `vorticity_from_tilt` surface 재확인
3. `accel_from_tilt` 에 bg_table / tetrad_state kwargs 추가 + additive 완성
4. `rhs_bianchi` 에 optional `tilted_species` kwarg 추가 + β=0 bit-identical 유지
5. `boost_kernel.py` seed + axi-symmetric projection + off-axis NotImplementedError
6. ≥20 new tests
7. Full regression green
8. Audit supplement + gallery 검토
9. `NEXT_SESSION_PROMPT.md §2` → FB-3.4 rotate
10. commit

시작하세요. 본 세션은 **Phase FB-3 의 세 번째 rotation (FB-3.3 Einstein+tilt coupling + boost-kernel seed)** — FB-3.2 의 species-specific acceleration piece 에 background kinematic pieces (Θ×v, σ×v) 를 additively 얹고, PSTF boost projection 의 axi-symmetric seed 를 배치. β=0 anchor (FB-3.2, baseline 3,189) 은 non-negotiable.
```

</details>

---

<!-- Prior (FB-3.2) handoff prompt (saved for reference only; do not re-run). -->

<details>
<summary>Previous FB-3.2 handoff prompt (archived 2026-04-19)</summary>

```text
# FB-3.2 — tilt-projected `v^a` / `ω^a` / `A^a` wire-up into `hierarchy_rhs_photon` (Phase FB-3 second rotation)

## 프로젝트 컨텍스트

- **Repo root**: /home/cosmosapjw/Dropbox/bianchi/htt_base
- **bass-py 소스 트리**: `htt_base/htt/` (has `bass/`, `tsc/`, `mio/`, `workspace/`, `conftest.py`, `pyproject.toml`)
- **venv**: `htt_base/venv/bin/python` (주의: `venv/bin/pip` shebang → `../venv/bin/python -m pip ...` 로 우회; FB-2.3 P3 env carry-forward, post-FB devops 에서 rebuild 예정)
- **테스트 명령**: `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 3,132 passing + 1 skipped (FB-3.1 직후; Phase FB-3 entry sealed. 감사 로그: `docs/audits/AUDIT_PHASE_FB3_2026-04-19.md` §FB-3.1 + Phase FB-3 entry declaration)
- **완료된 단계**: LB-0 … LB-6 + LB audits P2/P3 cleanup + Phase FB-0 전체 + Phase FB-1 전체 + Phase FB-2 전체 + **FB-3.1 (species-level tilt wrapper + FB02-F1 resolved)**:
  - FB-0.1..0.3 (Ellis convention flip + tilt-field surface + LB-6 F2 seal)
  - FB-1.1..1.4 (`SOURCE_STATUS` all VALIDATED + `anisotropic_3_curvature` non-None for all 11 types; gallery 03..13)
  - FB-2.1..2.4 (∇̃ dispatch across 11 types + T1/T2 Ricci coupling + T4-T7 structural pin + driver routing)
  - **FB-3.1** (`bass/species/tilted.py::TiltedSpeciesBackground(base, β, v̂_e)`: β=0 bit-identical short-circuit across photon/neutrino/baryon/CDM/Λ × 3 v̂_e sweep; EMM §5.4 eqs (5.12)-(5.13) exact at β>0; eager guards β<0 / β≥1 / non-finite β / non-unit v̂_e; FB02-F1 resolved via `00_conventions §2` cross-reference table; 24 new tests; baseline 3,108 → 3,132)
- **현재 phase**: **Full Bianchi Coverage (FB) — Phase FB-3 "Tilted sector non-perturbative β" (FB-3.2, second rotation)**.
- **전체 로드맵**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-3`
- **Carry-forward P2/P3 (알고만 있을 것, 절대 건드리지 말 것)**:
  - F3 (doc-only) → `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² rescale → **FB-5 / FB-6 예약**
  - FB11-F1 → W-E Table 11.1 fixed-point coords → **FB-5 / FB-6 예약**
  - FB12-F1 → IX isotropic S_+ residual (W-E pathology) → **FB-5 / FB-6 예약**
  - FB12-F3 → `bianchi_ix_recollapse_event` ↔ `_hubble_squared` 결합 → **FB-5 / FB-6 예약**
  - FB13-κ-calibration → VII_h Pontzen-Challinor spiral κ → **FB-5 / FB-6 예약**
  - **FB-2.1 P2** → complex-dtype `nabla_dispatch` → `hierarchy_rhs_photon` real-dtype driver wire-up → **FB-5.1 예약**
  - **FB-2.3 P3 (env)** → `venv/bin/pip` shebang stale → post-FB devops
  - **FB-3.1 P2 (new)** → β-parametrisation split (velocity `TiltedSpeciesBackground` vs rapidity `TiltedVisibility`) — composition rule `v_e(η) = β × v̂_e` unifies; formal unification audit **FB-3.5 예약**
  - **FB-3.1 P2 (new)** → overlap with `bass.tilt.species_tilt.TiltedSpeciesParams` (Y-Block v-vector API) — prefer `TiltedSpeciesBackground` in new code or compose explicitly; 이 세션 (FB-3.2) 에서 결정 필요
  - **FB-5.2** → off-axis helical Wigner rotation for 비-axis-aligned subset

## 이 세션의 작업 범위 (FB-3.2 — tilt-projected `v^a` / `ω^a` / `A^a` wire-up)

**Goal**: FB-3.1 이 `TiltedSpeciesBackground.v_vector(η)` 를 노출했다. FB-2.4 가 `hierarchy_rhs_photon` 에 `accel_vector` / `vorticity_vector` kwargs 를 구조적으로 열어 놓았다. FB-3.2 는 이 두 표면을 **연결** 한다:

1. **Driver-level tilt adapter** — `TiltedSpeciesBackground` (per-species) → per-η `(A^a, ω^a)` 3-vectors 를 추출하는 adapter 함수. King-Ellis 1973 §4 에서 `A^a` 는 species 공통 (실질적 tilt 가속도) + species-specific 부분으로 split; `ω^a` 는 Bianchi-type-dependent (Class A 에서 n_ab 가 들어가고 Class B 에서 a_α 추가).
2. **`hierarchy_rhs_photon` wire-up** — FB-2.4 에서 구조적으로만 pinned 되어 있던 `accel_vector` / `vorticity_vector` kwargs 를 **실질적으로** T4/T5/T6 coupling 에 라우팅. β=0 경로 bit-identical 유지 (FB-2.4 anchor 재검증).
3. **Per-type regression sweep** — 11 Bianchi types × β ∈ {0, 0.01, 0.1} 에서 hierarchy_rhs 가 예외 없이 finite; β=0 에서 FB-2.4 결과와 bit-identical.
4. **P2 overlap resolution** — `bass.tilt.species_tilt.TiltedSpeciesParams` vs `bass.species.tilted.TiltedSpeciesBackground` 의 역할을 문서화 (composition rule 포함). 실제 driver 는 `TiltedSpeciesBackground` 를 consume.

FB-3.2 는 **wire-up only** — boost kernel `B(η, ê)` projection 은 **FB-3.3** (wigner-D axi-symmetric) 에서; tilt-driven 배경 shear feedback 은 **FB-3.3**; β-gate reparametrisation 은 **FB-3.5**.

### 기준이 되는 문헌 타깃

- King-Ellis 1973 §3-§4 (tilted 4-velocity + induced acceleration / vorticity)
- Ellis-Maartens-MacCallum 2012 §5.3, §5.4 (frame-split kinematics)
- lowell_bianchi_solver_reference.md §7 (tilt SSOT)
- Pontzen-Challinor 2009 §2 (vorticity in Class B tilted cosmologies)

### 구체 작업 항목

1. **사전 읽기**:
   - `docs/audits/AUDIT_PHASE_FB3_2026-04-19.md §9` (FB-3.2 carry-forward 참고)
   - `bass/hierarchy/hierarchy_rhs.py::hierarchy_rhs_photon` — FB-2.4 에서 추가된 `accel_vector` / `vorticity_vector` kwargs 의 정확한 slot
   - `bass/species/tilted.py` (FB-3.1 surface)
   - `bass/tilt/species_tilt.py` (Y-Block — `decompose_tilted_species` full `(μ, q, p_iso, π)` 출력; FB-3.2 가 `q` 를 consume 하는지 결정)
   - `bass/background/einstein_bianchi.py::BianchiCosmology.beta` / `v_hat_e`

2. **Adapter 도입**: `bass/species/tilted.py` 에 (혹은 새 `bass/hierarchy/tilt_kinematics.py`):
   - `accel_from_tilt(tilted: TiltedSpeciesBackground, eta: float) -> np.ndarray[(3,)]`
   - `vorticity_from_tilt(tilted, eta, structure) -> np.ndarray[(3,)]`
   - β=0 → zeros(3) bit-identical

3. **Driver wire-up**: FB-2.4 의 `hierarchy_rhs_photon(..., accel_vector=..., vorticity_vector=...)` 가 실제로 T4/T5/T6 RHS 에 합류하는 경로 열기. **보호**: β=0 / 미지정 → FB-2.4 regression bit-identical.

4. **Validation tests** (≥ 15):
   - β=0 × 11 types bit-identical against FB-2.4 anchor
   - β > 0 × FLRW / Type I 에서 T4/T5/T6 의 유한성 + sign convention (EMM §6.4: vorticity evolution equation)
   - `accel_from_tilt` / `vorticity_from_tilt` unit tests (shape, β=0 zero)
   - P2 overlap: `TiltedSpeciesBackground.v_vector(η)` 과 `TiltedSpeciesParams.v` 의 등가성 check

5. **Audit**: `docs/audits/AUDIT_PHASE_FB3_2026-04-19.md` 에 §FB-3.2 supplement 추가 (또는 새 `AUDIT_PHASE_FB3_supplement_<date>.md`)

6. **Gallery**: FB-3.2 는 hierarchy 에 actual 변화를 도입하므로 plot 재생성 후보. 만약 FB-2.4 gallery 가 `hierarchy_rhs` 기반이 아니면 no-op.

7. `NEXT_SESSION_PROMPT.md §2` 를 **FB-3.3** (non-perturbative boost kernel `B(η, ê)` + Wigner-D axi-symmetric PSTF projection) bootstrap 으로 rotate.

### FB-3.2 non-goals (선 밑에 고정)

- **Non-perturbative boost kernel `B(η, ê)` projection on PSTF moments** → **FB-3.3**
- **Einstein + tilt 결합 (배경 shear feedback)** → **FB-3.3** (tilt-driven shear source)
- **β-gate reparametrisation** → **FB-3.5**
- **Thomson kernel Layer B (full Lorentz)** → **FB-4**
- **k ≠ 0 perturbation sector** → **FB-5**

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_FB3_2026-04-19.md` §9 (FB-3.2 carry-forward + β-parametrisation note)
2. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-3`
3. `docs/lowell_bianchi/00_conventions.md §2` (v̂_e SSOT — FB02-F1 resolved)
4. `bass/hierarchy/hierarchy_rhs.py::hierarchy_rhs_photon` (FB-2.4 `accel_vector` / `vorticity_vector` slots)
5. `bass/species/tilted.py` (FB-3.1 surface)
6. `bass/tilt/species_tilt.py` (Y-Block full decomposition)
7. King-Ellis 1973 §3-§4; EMM 2012 §5.3-§5.4; lowell §7
8. `docs/audits/AUDIT_PROMPT.md` (phase-supplement audit — self-invoke)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (King-Ellis 1973 + EMM 2012 §5.4 / §6.4 + lowell §7)
3. PSTF invariants preserved; Ellis convention 유지; **β=0 경로 bit-identical** against FB-2.4 anchor
4. No silent fallbacks — missing kwargs → FB-2.4 identical; out-of-range inputs → explicit ValueError
5. Determinism
6. **FB-3 phase in progress** — Phase FB-3 entry (FB-3.1) 은 sealed; 이 세션은 FB-3.2 (wire-up)

## 검증 체크리스트 (최종 commit 전)

- [ ] `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 3,132 + 신규 테스트)
- [ ] β=0 × 11 types hierarchy_rhs_photon 출력이 FB-2.4 commit (d7d25da) 와 bit-identical
- [ ] `accel_from_tilt` / `vorticity_from_tilt` shape + β=0 zero 보장
- [ ] P2 overlap (`TiltedSpeciesBackground` vs `TiltedSpeciesParams`) composition rule 문서화
- [ ] `AUDIT_PHASE_FB3_*` supplement 또는 §FB-3.2 추가
- [ ] Gallery 재생성 또는 no-op 명시
- [ ] `NEXT_SESSION_PROMPT.md §2` → **FB-3.3** bootstrap 으로 rotate
- [ ] 최종 commit 메시지: `FB-3.2: tilt-projected v/ω/A wire-up into hierarchy_rhs_photon` + `+ rotate NEXT_SESSION_PROMPT for FB-3.3`

## 진행 순서

1. `docs/audits/AUDIT_PROMPT.md` self-invoke (pre-session scan)
2. `hierarchy_rhs_photon` 의 FB-2.4 `accel_vector` / `vorticity_vector` kwargs 정확히 확인
3. `accel_from_tilt` / `vorticity_from_tilt` adapter 설계 + 구현
4. driver wire-up (β=0 bit-identical guard 먼저)
5. β=0 × 11 types regression + β > 0 × FLRW / I finite test + adapter unit tests
6. P2 overlap 문서화
7. Full regression green
8. Audit supplement + gallery 검토
9. `NEXT_SESSION_PROMPT.md §2` → FB-3.3 rotate
10. commit

시작하세요. 본 세션은 **Phase FB-3 의 두 번째 rotation (FB-3.2 wire-up)** — FB-3.1 의 species-level `v^a` surface 를 FB-2.4 의 driver slot 으로 연결한다. β=0 bit-identical anchor (FB-2.4, commit d7d25da) 은 non-negotiable.
```

</details>

---

<!-- Prior (FB-3.1) handoff prompt (saved for reference only; do not re-run). -->

<details>
<summary>Previous FB-3.1 handoff prompt (archived 2026-04-19)</summary>

```text
# FB-3.1 — `TiltedSpeciesBackground(base, beta, v̂_e)` abstraction + orthogonal β → 0 limit recovery (Phase FB-3 entry)

(original prompt text preserved; see
`docs/audits/AUDIT_PHASE_FB3_2026-04-19.md` §FB-3.1 + Phase FB-3
entry declaration for the completion summary — 24 new tests,
baseline 3,108 → 3,132; `bass/species/tilted.py::TiltedSpeciesBackground`
with β=0 bit-identical short-circuit across all LB-1 species × 3 v̂_e
sweep; FB02-F1 resolved via `00_conventions §2` v̂_e cross-reference
table pinning `V_HAT_E_DEFAULT = (1,0,0)` SSOT)
```

</details>

<!-- ARCHIVED_FB31_BEGIN_ORIG -->

<details>
<summary>Previous FB-3.1 handoff prompt — full body (archived 2026-04-19)</summary>

```text
# FB-3.1 — `TiltedSpeciesBackground(base, beta, v̂_e)` abstraction + orthogonal β → 0 limit recovery (Phase FB-3 entry)

## 프로젝트 컨텍스트

- **Repo root**: /home/cosmosapjw/Dropbox/bianchi/htt_base
- **bass-py 소스 트리**: `htt_base/htt/` (has `bass/`, `tsc/`, `mio/`, `workspace/`, `conftest.py`, `pyproject.toml`)
- **venv**: `htt_base/venv/bin/python` (주의: `venv/bin/pip` shebang → `../venv/bin/python -m pip ...` 로 우회; FB-2.3 P3 env carry-forward, post-FB devops 에서 rebuild 예정)
- **테스트 명령**: `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 3,108 passing + 1 skipped (FB-2.4 직후; Phase FB-2 closed. 감사 로그: `docs/audits/AUDIT_PHASE_FB2_2026-04-19.md` §FB-2.1..FB-2.4 + Phase FB-2 exit declaration)
- **완료된 단계**: LB-0 … LB-6 + LB audits P2/P3 cleanup + **Phase FB-0 전체 + Phase FB-1 전체 + Phase FB-2 전체**:
  - FB-0.1..0.3 (Ellis convention flip + tilt-field surface + LB-6 F2 seal)
  - FB-1.1..1.4 (`SOURCE_STATUS` all VALIDATED + `anisotropic_3_curvature` non-None for all 11 types; gallery 03..13)
  - FB-2.1 (FLRW / I / V / VII_0 / IX 의 harmonic-mode ∇̃; 35 new tests)
  - FB-2.2 (Class A II / VI_0 / VIII axis-aligned ∇̃ + T1/T2 optional `aniso_ricci_tensor` hook + FB14-F1 h-scaling calibration; 24 new tests)
  - FB-2.3 (Class B III / IV / VI_h / VII_h axis-aligned ∇̃ on abelian (e_1, e_3) 2-plane + Harrison-V twist offset `a²/(1+|h|)` + T1 Ricci auto-activation; 27 new tests)
  - FB-2.4 (driver-level `aniso_ricci_tensor` routing into T1/T2 via `aniso_ricci_at_eta` + T4/T5/T6 structural-forwarding pin + F3 docstring correction + 12-label regression sweep; 25 new tests). **Phase FB-2 complete — 111 tests across 4 sessions; baseline 2,997 → 3,108.**
- **현재 phase**: **Full Bianchi Coverage (FB) — Phase FB-3 "Tilted sector non-perturbative β" (session count TBD)**. 본 세션이 Phase FB-3 의 첫 rotation (FB-3.1).
- **전체 로드맵**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §5 FB-3.1`
- **Carry-forward P2/P3 (알고만 있을 것, 절대 건드리지 말 것)**:
  - FB02-F1 → `00_conventions.md §2` 에 `v̂_e` default cross-reference → **본 세션에서 처리 (FB-3.1 예약됨)**
  - F3 (doc-only) → `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² = σ²/H² EMM/Wainwright rescale → **FB-5 / FB-6 예약** (current value consumed by `htt.core.bounds` / `comparator_policy`; rename would cascade)
  - FB11-F1 → W-E Table 11.1 fixed-point *coordinates* fixed-N 에서 직접 도달 불가 → **FB-5 / FB-6 예약**
  - FB12-F1 → IX isotropic leading-order *shear-source* residual `S_+ = +(2/3) n² ℋ²` (W-E pathology) — **FB-5 / FB-6 예약**
  - FB12-F3 → `bianchi_ix_recollapse_event` 는 `_hubble_squared` 에 coupling → **FB-5 / FB-6 예약**
  - FB13-κ-calibration → VII_h Pontzen-Challinor spiral κ 정량 보정 → **FB-5 / FB-6 예약**
  - **FB-2.1 P2** → complex-dtype `nabla_dispatch` 를 `hierarchy_rhs_photon` real-dtype driver 에 wire-up 은 **FB-5.1 예약** (harmonic-mode amplitude state machine 과 함께)
  - **FB-2.3 P3 (env)** → `venv/bin/pip` shebang stale → post-FB devops
  - **FB-5.2** → 모든 비-axis-aligned subset (II / VI_0 / VIII / VII_0 / VII_h / III / IV / VI_h) 의 generic off-axis helical Wigner rotation

## 이 세션의 작업 범위 (FB-3.1 — `TiltedSpeciesBackground(base, beta, v̂_e)` abstraction + orthogonal β → 0 limit recovery)

**Goal**: Phase FB-2 가 orthogonal β=0 에 대한 curved-space T-term wire-up 을 완성했다. Phase FB-3 는 tilt parameter `β` 를 non-perturbative 하게 도입한다. FB-3.1 은 이 phase 의 첫 rotation 으로, `TiltedSpeciesBackground(base, beta, v̂_e)` 라는 wrapper-style abstraction 을 도입해서:

1. **Tilt interface 정비** — `BianchiCosmology` 에는 이미 `beta` / `v_hat_e` 필드가 있다 (FB-0.2). FB-3.1 은 이 필드들을 consume 하는 species-level wrapper 를 만든다: `TiltedSpeciesBackground` 는 기존 `SpeciesBackground` (photon / neutrino 등) 에 tilt-projection 을 overlay 해서 `(ρ̃, ρ̃ + p̃, v^a, v^a v^b)` 를 return 한다.
2. **β → 0 limit recovery** — `TiltedSpeciesBackground(base, beta=0, v̂_e=any)` 는 `base` 를 **bit-identical** 으로 재현 (orthogonal 경로 preservation).
3. **`v̂_e` default cross-reference (FB02-F1)** — `00_conventions.md §2` 에 `v̂_e = (0, 0, 1)` default 를 공식화하고, `TiltedSpeciesBackground` 가 이 default 를 consumed 하는지 증거.
4. **Validation tests (≥ 10)** — β=0 bit-identical pin × multiple species + `v̂_e` normalization guard + 차원 check.

FB-3.1 은 **abstraction only** — Boltzmann hierarchy 에 tilt-coupled T4/T5/T6 커플링을 전달하는 작업은 **FB-3.2 예약**. Phase FB-2 가 driver signature 를 `accel_vector` / `vorticity_vector` 로 이미 열어 놓았으므로 FB-3.2 에서 tilt-projected vectors 를 이 signature 에 넣기만 하면 된다.

### 기준이 되는 문헌 타깃

- King-Ellis 1973 §2-§3 (tilted cosmology kinematic split)
- Ellis-Maartens-MacCallum 2012 §5.4 (tilted four-velocity u^a = u_0^a + v^a + ...)
- lowell_bianchi_solver_reference.md §7 (tilt SSOT)

Tilt convention:

    u^a(total) = γ (u_0^a + v^a),   v^a = β v̂^a,
    γ = (1 − β²)^{−1/2}

with `|v̂| = 1` enforced at the boundary. For species we carry the tilt-projected energy density and momentum separately:

    ρ̃ = γ² (ρ + p) − p,
    q̃^a = γ² (ρ + p) v^a  (heat-flux surrogate at β > 0)

### 구체 작업 항목

1. **문헌 + 현 코드 재확인 (먼저, 코딩 전)**:
   - King-Ellis 1973 §2-§3 / EMM 2012 §5.4 / lowell §7
   - `bass/background/einstein_bianchi.py::BianchiCosmology` — `beta` / `v_hat_e` 필드의 현 사용 여부 (FB-0.2)
   - `bass/species/` directory — 기존 `SpeciesBackground` 추상 어디에 있는지, photon / neutrino / baryon / CDM 각 species 의 `(ρ, p, w)` attribute 확인
   - `docs/lowell_bianchi/00_conventions.md §2` — `v̂_e` default 현 상태 (FB02-F1)
   - `docs/audits/AUDIT_PROMPT.md` (Phase FB-3 entry self-invoke)

2. **`TiltedSpeciesBackground` 도입** (new module e.g. `bass/species/tilted.py`):
   - dataclass `TiltedSpeciesBackground(base: SpeciesBackground, beta: float, v_hat_e: Tuple[float, float, float])`
   - `beta` validation (0 ≤ β < 1)
   - `v_hat_e` 정규화 guard (`|v̂_e| == 1 ± 1e-12`)
   - Expose `rho_tilde(eta)`, `p_tilde(eta)`, `v_vector(eta)` (at β=0 these reduce to base.rho, base.p, zeros(3))
   - `γ = (1 − β²)^{−1/2}` property

3. **FB02-F1 해소**:
   - `00_conventions.md §2` 에 `v̂_e = (0, 0, 1)` default 를 명시하고 cross-reference 추가 (`BianchiCosmology.v_hat_e`, `TiltedSpeciesBackground.v_hat_e`, `hierarchy_rhs_photon`)
   - 테스트: `TiltedSpeciesBackground(..., v̂_e=(0,0,1))` 가 convention default 와 일치

4. **Validation tests** (≥ 10):
   - β=0 bit-identical: `TiltedSpeciesBackground(photon, β=0, v̂_e=any)` ≡ photon
   - β=0 bit-identical for 각 species (photon/neutrino/baryon/CDM)
   - β > 0 finite at test points; γ > 1 ok; `ρ̃ > ρ` 증가 check
   - `|v̂_e| != 1` → ValueError
   - β ≥ 1 → ValueError
   - FB02-F1 convention cross-reference test (`v̂_e default == (0, 0, 1)`)

5. **Audit**: `docs/audits/AUDIT_PHASE_FB3_2026-04-XX.md` 신설 — Phase FB-3 entry declaration + FB-3.1 §1..§10

6. `NEXT_SESSION_PROMPT.md §2` 를 **FB-3.2** (tilt-projected ω/A vectors → `hierarchy_rhs_photon` 에 forward; VII_h vorticity 활성화) bootstrap 으로 rotate

### FB-3.1 non-goals (선 밑에 고정)

- **tilt-projected T4/T5/T6 hierarchy 연결** → **FB-3.2**
- **β evolution equation integration** → FB-4 (Einstein + tilt 결합)
- **k ≠ 0 perturbation sector** → FB-5
- **κ-calibration / W-E Table 11.1 / IX S_+ residual** → FB-5 / FB-6
- **complex-dtype `nabla_dispatch` wire-up** → FB-5.1

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_FB2_2026-04-19.md` (Phase FB-2 exit declaration 포함; FB-3 handoff section)
2. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §5 FB-3.1`
3. `docs/lowell_bianchi/00_conventions.md §2` (v̂_e default; FB02-F1)
4. `bass/background/einstein_bianchi.py::BianchiCosmology` (beta / v_hat_e 필드)
5. `bass/species/` (기존 `SpeciesBackground` 추상)
6. King-Ellis 1973 §2-§3; Ellis-Maartens-MacCallum 2012 §5.4; lowell §7
7. `docs/audits/AUDIT_PROMPT.md` (phase-entry audit template — self-invoke)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (King-Ellis 1973 + EMM 2012 §5.4 + lowell §7 인용)
3. PSTF invariants preserved; Ellis convention 유지; **β=0 경로 bit-identical**
4. No silent fallbacks — `|v̂_e| != 1` 는 explicit ValueError
5. Determinism
6. **FB-3 phase entry** — 본 세션이 Phase FB-3 의 첫 rotation; Phase FB-2 exit 을 정본 baseline 으로 고정

## 검증 체크리스트 (최종 commit 전)

- [ ] `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 3,108 + 신규 테스트)
- [ ] `TiltedSpeciesBackground(base, β=0, v̂_e=any)` 는 모든 species 에 대해 bit-identical
- [ ] `|v̂_e| != 1` → ValueError; β ≥ 1 → ValueError
- [ ] FB02-F1 해소 — `00_conventions.md §2` 에 v̂_e default 명시 + cross-reference
- [ ] `docs/audits/AUDIT_PHASE_FB3_2026-04-XX.md` 신설 + Phase FB-3 entry declaration
- [ ] `docs/audits/AUDIT_PROMPT.md` self-invoke 완료
- [ ] (선택) Gallery PNG 생성; no-op 이면 audit 에 명시
- [ ] `NEXT_SESSION_PROMPT.md §2` → **FB-3.2** bootstrap 으로 rotate
- [ ] 최종 commit 메시지: `FB-3.1: TiltedSpeciesBackground abstraction + β→0 limit recovery (Phase FB-3 entry)` + `+ rotate NEXT_SESSION_PROMPT for FB-3.2`

## 진행 순서

1. `docs/audits/AUDIT_PROMPT.md` self-invoke (pre-phase scan)
2. 현 `BianchiCosmology` β / v̂_e 필드 + `bass/species/` 추상 읽기
3. `TiltedSpeciesBackground` dataclass + validation
4. β=0 bit-identical pin 테스트 + v̂_e normalisation guard + FB02-F1 cross-reference
5. 전체 회귀 green 확인
6. `AUDIT_PHASE_FB3_2026-04-XX.md` 신설 + Phase FB-3 entry declaration
7. `NEXT_SESSION_PROMPT.md §2` rotate to FB-3.2
8. commit

시작하세요. 본 세션은 **Phase FB-3 의 첫 rotation (FB-3.1 entry)** — Phase FB-2 에서 driver 를 curved-space T-term 으로 완성했고, 이제 β tilt parameter 를 non-perturbative 하게 species-level 에 도입한다. FB-3.1 은 abstraction + β=0 limit recovery 만 — tilt-projected hierarchy 연결은 FB-3.2 에서.
```

</details>

<!-- ARCHIVED_FB31_END_ORIG -->

---

<!-- Prior (FB-2.4) handoff prompt (saved for reference only; do not re-run). -->

<details>
<summary>Previous FB-2.4 handoff prompt (archived 2026-04-19)</summary>

```text
# FB-2.4 — T4-T7 hierarchy wire-up + driver-level `aniso_ricci_tensor` routing (Phase FB-2 exit)

(original prompt text preserved; see
`docs/audits/AUDIT_PHASE_FB2_2026-04-19.md` FB-2.4 supplement + Phase
FB-2 exit declaration for the completion summary — 25 new tests,
baseline 3,083 → 3,108; `hierarchy_rhs_photon` now routes
`tetrad_state.aniso_3_curvature` into T1/T2 via the new
`aniso_ricci_at_eta` helper; T4/T5/T6 kinematic kwargs pinned as
structurally wired; F3 docstring correction applied;
`shear_magnitude_sq` dimensionless rescale deferred to FB-5/6)
```

</details>

<!-- Prior (FB-2.3) handoff prompt (saved for reference only; do not re-run). -->

<details>
<summary>Previous FB-2.3 handoff prompt (archived 2026-04-19)</summary>

```text
# FB-2.3 — Class B III / IV / VI_h / VII_h ∇̃ twist-coupled dispatch + T1/T2 Ricci-hook activation

(original prompt text preserved; see
`docs/audits/AUDIT_PHASE_FB2_2026-04-19.md` FB-2.3 supplement for the
completion summary — 27 new tests, baseline 3,056 → 3,083)
```

</details>

<!-- Prior (FB-2.2) handoff prompt (saved for reference only; do not re-run). -->

<details>
<summary>Previous FB-2.2 handoff prompt (archived 2026-04-19)</summary>

```text
# FB-2.2 — Class A II / VI_0 / VIII ∇̃ + spatial Ricci T1/T2 wire-up + FB14-F1 twist correction

(original prompt text preserved; see
`docs/audits/AUDIT_PHASE_FB2_2026-04-19.md` FB-2.2 supplement for the
completion summary)
```

</details>

<!-- Prior (FB-2.1) handoff prompt (saved for reference only; do not re-run). -->

<details>
<summary>Previous FB-2.1 handoff prompt (archived 2026-04-19)</summary>

```text
# FB-2.1 — `∇̃` operator dispatch table (FLRW / I / V / VII_0 / IX harmonic-mode decomposition)

(original prompt text preserved; see
`docs/audits/AUDIT_PHASE_FB2_2026-04-19.md` for the completion summary)
```

</details>

<details>
<summary>Previous FB-1.4 handoff prompt (archived 2026-04-19)</summary>

```text
# FB-1.4 — `anisotropic_3_curvature` 11-type consolidation (Phase FB-1 exit)

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,904 passing + 1 skipped (FB-1.3 직후; 감사 로그: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` — FB-1.1 + FB-1.2 + FB-1.3 섹션, FB-1.4 placeholder 예약됨)
- **완료된 단계**: LB-0 … LB-6 + LB audits P2/P3 cleanup + **Phase FB-0 전체** + **FB-1.1 + FB-1.2 + FB-1.3**:
  - FB-0.1..0.3 (Ellis convention flip + tilt-field surface + LB-6 F2 seal)
  - FB-1.1 (Class A I/II/VI₀/VII₀ SOURCE_STATUS → VALIDATED; 4 gallery PNGs 03..06; `TestClassAFixedPoints` 61 runs)
  - FB-1.2 (Class A VIII/IX SOURCE_STATUS → VALIDATED + `solve_bianchi_background(events=...)` + `bianchi_ix_recollapse_event(cosmo, floor)`; 2 gallery PNGs 07..08; `TestClassAFixedPoints` +47 = 108 total)
  - FB-1.3 (Class B III/IV/VI_h/VII_h SOURCE_STATUS → VALIDATED + V reference refresh + P-C spiral signature pins; 4 gallery PNGs 09..12; `TestClassBFixedPoints` 104 runs). **모든 9개 PROVISIONAL 소스 이제 VALIDATED**.
- **현재 phase**: **Full Bianchi Coverage (FB) — Phase FB-1 "Per-type background validation" (4 sessions)** 의 마지막 4/4 번째. 본 세션 끝나면 Phase FB-1 가 **완전 종료** 되고 Phase FB-2 (hierarchy RHS T-term wire-up) 로 넘어간다.
- **전체 로드맵**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.4`
- **Carry-forward P2 (알고만 있을 것, 절대 건드리지 말 것)**:
  - F3 → `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² normalisation → **FB-2.4 예약**
  - FB02-F1 → `00_conventions.md §2` 에 `v̂_e` default cross-reference → **FB-3.1 예약**
  - FB11-F1 → W-E Table 11.1 fixed-point *coordinates* 는 fixed-N 프레임워크에서 직접 도달 불가 → **FB-5 / FB-6 cross-type continuity 예약**
  - FB12-F1 → IX isotropic leading-order residual `S_+ = +(2/3) n² ℋ²` — W-E pathology → **FB-5 / FB-6 예약**
  - FB12-F3 → `bianchi_ix_recollapse_event` 는 `_hubble_squared` 에 coupling → **FB-5 / FB-6 예약**
  - **FB13-κ-calibration (new, FB-1.3)** → VII_h Pontzen-Challinor spiral κ 정량 보정 → **FB-5 / FB-6 예약** (본 세션은 무관)

## 이 세션의 작업 범위 (FB-1.4 — anisotropic_3_curvature 11-type consolidation)

**Goal**: `bass/background/tetrad_state.py::anisotropic_3_curvature` 함수가 현재 I / V / VII_0 / FLRW 4타입만 zeros 반환 + 나머지 8타입에 대해 `None, 'unavailable'` 을 반환하는 부분을 II / III / IV / VI_0 / VI_h / VII_h / VIII / IX 에 대해 **explicit per-type** ³R_{ab}^{aniso} 공식으로 대체. 이 함수는 `build_tetrad_state` 가 호출해서 `TetradBackgroundState.aniso_3_curvature` 필드를 채우는 경로이며, FB-2 의 hierarchy T1/T2 spatial-Ricci 커플링이 이 필드를 consumer 로 쓴다 (FB-2.2 에서).

### 기준이 되는 문헌 타깃

Ellis-Maartens-MacCallum 2012 §14.3 + Wainwright-Ellis §3.2:

    ³R_{ab} = 2 N_a^c N_{bc} − N_c^c N_{ab} + (2/(1−h)) a^c a_{(a} δ_{b)c}  [simplified]
             − (1/2) N_cd N^{cd} δ_{ab} − N_{ab}^2 contributions (Class A)

Tetrad-aligned PSTF projection에서 trace-free 부분만 취하면 각 type 별로 closed form.

### 구체 작업 항목

1. **문헌 재확인 (먼저, 코딩 전)**:
   - Ellis-Maartens-MacCallum 2012 §14.3 Table 14.3 ³R_{ab} expressions (per Class A / Class B)
   - Wainwright-Ellis §3.2 per-type 3-Ricci 분해
   - `bass/background/tetrad_state.py::anisotropic_3_curvature` 현 구현 + `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` §FB-1.3 §6 carry-forward 목록
   - FB-2 가 이 함수를 consumer 로 쓰므로 **return signature** (tensor, status) 유지 필수

2. **`anisotropic_3_curvature` 확장**: 8 개 PROVISIONAL 타입에 대해 tetrad-aligned PSTF 투영의 trace-free symmetric ³R_{ab}^{aniso} 구체 공식 구현. 타입별 핵심 공식:
   - **II (e(1,1)의 Heisenberg)**: `N_ab = diag(n_1, 0, 0)`; ³R_{ab}^{aniso} ∝ N_1²
   - **III (= VI_{h=-1})**: VI_h 에 dispatch
   - **IV ((0, 0, +), a ≠ 0)**: twist A + N_3
   - **VI_0 ((+, 0, −), a = 0)**: diff N_1 − N_3 dependence
   - **VI_h ((+, 0, −), a ≠ 0)**: h-dependent twist + N_i mixing
   - **VII_h ((+, 0, +), a ≠ 0, h > 0)**: identical structure to VI_h with n_3 > 0
   - **VIII (sl(2,ℝ))**: (N_1 < 0, N_2 > 0, N_3 > 0) contributions
   - **IX (so(3), Mixmaster)**: all-positive N_i

3. **Validation 테스트 (`test_tetrad_state.py::TestAnisotropic3Curvature`)**:
   - 각 타입 × (structure parameter) × (a grid) 에서 ³R_{ab}^{aniso} 가 (i) finite, (ii) symmetric, (iii) trace-free, (iv) FLRW 한계에서 → 0 을 확인
   - IX isotropic (n_1 = n_2 = n_3) 에서 ³R_{ab}^{aniso} = 0 exactly (FB12-F1 과 독립적으로 — 공간 곡률은 isotropic)
   - II axisymmetric limit 에서 예상 tensor 구조 매치
   - `status` 문자열이 모든 11 type 에 대해 `'unavailable'` 이 아님을 확인

4. **Gallery 확장 (선택, no-op 허용)**:
   - 만약 visualisation 이 meaningful 하면 `plots/physics_gallery/11_integrator/13_fb14_anisotropic_3curvature_per_type.png` 추가
   - ³R_{ab}^{aniso} 의 determinant 또는 eigenvalue scaling 을 11 type 에 대해 비교
   - FB-1.4 가 no-op visual 이면 audit log 에 명시

5. **Audit append**: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 에 **FB-1.4 supplement** 섹션 append (§1..§10 template). **FB-1.4 는 Phase FB-1 exit** 이므로 audit 이 phase-complete 선언 포함 필수.

6. `NEXT_SESSION_PROMPT.md §2` 를 **FB-2.1** (`∇̃` operator dispatch table — FLRW / I / V / VII_0 / IX harmonic-mode decomposition; `bass/hierarchy/contractions.py::NotImplementedError` 해소) bootstrap 으로 rotate.

### FB-1.4 non-goals (선 밑에 고정)

- **Hierarchy RHS T4–T7 wire-up** 은 FB-2.4 (본 세션은 `anisotropic_3_curvature` return 만, hierarchy consumer 호출은 건드리지 않음)
- **∇̃ operator dispatch** 는 FB-2.1 (본 세션과 무관)
- **Tilted sector (β ≠ 0)** 은 FB-3 (β=0 유지)
- **k ≠ 0 perturbation sector** 는 FB-5
- **F3 / FB02-F1 / FB11-F1 / FB12-F1 / FB12-F3 / FB13-κ carry-forwards**: 건드리지 말 것

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` §FB-1.3 + §10 + FB-1.4 placeholder (본 세션이 append 할 곳; Phase FB-1 exit 선언 포함)
2. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.4` + §3 Target state (Phase FB-1 exit criteria)
3. `bass/background/tetrad_state.py::anisotropic_3_curvature` 현 구현 + 주변 `build_tetrad_state` consumer
4. `bass/background/test_tetrad_state.py` 기존 테스트 (본 세션은 `TestAnisotropic3Curvature` 새 클래스)
5. Ellis-Maartens-MacCallum 2012 §14.3 Table 14.3 (per-type ³R_{ab} expressions); Wainwright-Ellis §3.2
6. `docs/audits/AUDIT_PROMPT.md` (phase-boundary audit template — 본 세션 전에 self-invoke)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (Ellis-Maartens-MacCallum §14.3 + Wainwright-Ellis §3.2 인용 필수)
3. PSTF invariants preserved; Ellis convention (FB-0.1) 유지
4. No silent fallbacks — `status` 는 각 type 에 대해 구체 문자열 반환 (e.g., `'type_ii_heisenberg'`, `'type_ix_so3'`)
5. Determinism
6. **Phase FB-1 exit contract**: 본 세션 성공 후 `anisotropic_3_curvature` 가 모든 11 type 에 대해 non-None tensor 반환. 이게 Phase FB-2 의 선결 조건.
7. **Gallery PNG (선택)**: 추가하면 눈으로 확인 후 commit; no-op 이면 audit 에 명시.

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 2,904 + 신규 테스트)
- [ ] `TestAnisotropic3Curvature::*` green — 모든 11 type 에 대해 symmetric / trace-free / finite pinned
- [ ] `anisotropic_3_curvature(sc)` for every type in `ALL_BIANCHI_TYPES` returns non-None tensor + status string ≠ `'unavailable'`
- [ ] `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 에 FB-1.4 supplement append (§1..§10) + **Phase FB-1 exit** 선언
- [ ] `docs/audits/AUDIT_PROMPT.md` self-invoke 로 P0/P1 스캔 완료 (결과 audit log FB-1.4 §6 에 기록)
- [ ] (선택) `plots/physics_gallery/11_integrator/13_fb14_*.png` 생성 + 시각적 inspection; no-op 이면 audit 에 명시
- [ ] `NEXT_SESSION_PROMPT.md §2` → **FB-2.1** (`∇̃` operator dispatch table) bootstrap 으로 rotate
- [ ] 최종 commit 메시지: `FB-1.4: anisotropic_3_curvature 11-type consolidation (Phase FB-1 exit)` + `+ rotate NEXT_SESSION_PROMPT for FB-2.1`

## 진행 순서

1. `docs/audits/AUDIT_PROMPT.md` self-invoke (pre-phase scan)
2. FB plan §4 FB-1.4 + Ellis-Maartens-MacCallum §14.3 + 현 `tetrad_state.py` 섹션 읽기
3. 각 Bianchi type 에 대해 ³R_{ab}^{aniso} 공식을 종이로 확인 (sanity)
4. `anisotropic_3_curvature` 에 8 type × explicit formula 구현
5. `TestAnisotropic3Curvature` 에 per-type + symmetric/trace-free/finite 테스트 추가
6. (선택) Gallery 1 PNG 추가
7. 각 PNG Read tool 로 inspect → physics 검증 (있으면)
8. `AUDIT_PHASE_FB1_2026-04-19.md` 에 FB-1.4 supplement append + Phase FB-1 exit 선언
9. 전체 회귀 green 확인
10. `NEXT_SESSION_PROMPT.md §2` rotate to FB-2.1
11. commit

시작하세요. 본 세션은 **Phase FB-1 의 마지막 rotation** — 9개 소스가 이미 VALIDATED 이므로 남은 것은 tetrad-layer 의 ³R_{ab}^{aniso} 11-type consolidation. FB-2 hierarchy T-term wire-up 이 이 함수를 consumer 로 쓰므로 FB-1.4 가 **Phase FB-2 의 선결 조건**. 세션 완료 시 Phase FB-1 전체 (4 sub-phases) 가 닫히고 Phase FB-2 로 전환된다.
```

</details>

---

<!-- Prior (FB-1.3) handoff prompt (saved for reference only; do not re-run). -->

<details>
<summary>Previous FB-1.3 handoff prompt (archived 2026-04-19)</summary>

```text
# FB-1.3 — Class B background validation (III / IV / V / VI_h / VII_h) + Pontzen-Challinor VII_h spiral match

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,800 passing + 1 skipped (FB-1.2 직후; 감사 로그: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` — FB-1.1 + FB-1.2 섹션, FB-1.3/1.4 placeholder 예약됨)
- **완료된 단계**: LB-0 … LB-6 + LB audits P2/P3 cleanup + **Phase FB-0 전체** + **FB-1.1 + FB-1.2**:
  - FB-0.1..0.3 (Ellis convention flip + tilt-field surface + LB-6 F2 seal)
  - FB-1.1 (Class A I/II/VI₀/VII₀ SOURCE_STATUS → VALIDATED; 4 gallery PNGs 03..06; `TestClassAFixedPoints` 61 runs)
  - FB-1.2 (Class A VIII/IX SOURCE_STATUS → VALIDATED + `solve_bianchi_background(events=...)` + `bianchi_ix_recollapse_event(cosmo, floor)`; 2 gallery PNGs 07..08; `TestClassAFixedPoints` +47 runs = 108 total)
- **현재 phase**: **Full Bianchi Coverage (FB) — Phase FB-1 "Per-type background validation" (4 sessions)** 의 3/4 번째
- **전체 로드맵**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.3`
- **Carry-forward P2 (알고만 있을 것, 절대 건드리지 말 것)**:
  - F3 → `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² normalisation → **FB-2.4 예약**
  - FB02-F1 → `00_conventions.md §2` 에 `v̂_e` default cross-reference → **FB-3.1 예약**
  - FB11-F1 → W-E Table 11.1 fixed-point *coordinates* 는 fixed-N 프레임워크에서 직접 도달 불가 → **FB-5 / FB-6 cross-type continuity**; 본 세션도 formula-level validation 유지, Hubble-normalised coordinate chasing 금지
  - FB12-F1 (new, FB-1.2) → IX 은 isotropic limit 에서 leading-order residual `S_+ = +(2/3) n² ℋ²` (W-E 의 pathology) 가 있음; full resolution 은 **FB-5 / FB-6** Mixmaster / BKL 동적 시스템에서. 본 세션 Class B 는 이와 무관하지만 정보로 보관.
  - FB12-F3 → `bianchi_ix_recollapse_event` 는 `_hubble_squared(a, cosmo)` 에 coupling; FB-5 의 vacuum-IX H² 변경 시 event detector 재도출 필요 → **FB-5 / FB-6 예약** (본 세션 Class B 에는 영향 없음)

## 이 세션의 작업 범위 (FB-1.3 — Class B: III / IV / V / VI_h / VII_h)

**Goal**: `bass/transport/shear_sources.py` 의 Class B 5 타입 소스를 W-E §18 + Pontzen-Challinor 2009 (VII_h spiral) 에 대해 per-type 검증하고 `SOURCE_STATUS` 를 `PROVISIONAL → VALIDATED` 로 승격. Class B 의 구분되는 특징: twist parameter `a` ≠ 0 + Jacobi constraint `n_2 = 0`. VII_h 은 spiral coupling (`ω_spiral × Σ_⊥`) 이 추가되는 principal CMB type 이므로 sign + magnitude 양쪽을 Pontzen-Challinor literature fixture 에 맞춰야 함.

### 기준이 되는 문헌 타깃

| 타입 | 해석해 / 수치 타깃 | 테스트 앵커 |
|---|---|---|
| III | III = VI_{h=-1} (특수 케이스). `source_III` 는 `source_VIh` 에 dispatch. h = -1 일 때 formula 유효성 pin. | `test_type_III_dispatches_to_VIh_at_h_minus_1` |
| IV | (0, 0, +) with a > 0. S^{WE}_+ = -(2/3) N_3² + (2/3) A². S^{WE}_- = 0. Cosmologically marginal (no FLRW limit). | `test_type_IV_WE_source_formula` |
| V | (0, 0, 0) with a > 0. Open FLRW (k=-1). S = (0, 0) shear-specifically (A² 는 curvature 로 흡수). 이미 VALIDATED; FB-1.3 은 benchmark reference 업데이트 + explicit formula pin만. | `test_type_V_shear_zero_pin` (regression) |
| VI_h | (+, 0, −) with a > 0, h ∈ (-∞,-1)∪(-1,0). S^{WE}_+ = -(2/3)(n_1-n_3)² + (2/3)A²/(1+\|h\|). S^{WE}_- = -(2/√3)(n_1+n_3)(n_1-n_3). | `test_type_VIh_WE_source_formula` |
| VII_h | **principal CMB type**. (+, 0, +) with a > 0, h > 0. W-E: S^{WE}_+ = -(2/3)(n_1-n_3)² + (2/3)A²/(1+h), S^{WE}_- = +(2/√3)(n_1+n_3)(n_1-n_3). **+ spiral coupling** `ω_spiral = √(\|n_1 n_3\|) × √h × ℋ` applied via `+ω × Σ_-` to dSp, `−ω × Σ_+` to dSm. **Pontzen-Challinor 2009 near-FLRW spiral signature**: rotation in (Σ_+, Σ_-) plane preserves Σ_+² + Σ_-² up to W-E decay. | `test_type_VIIh_WE_source_formula_and_spiral_signature` + `test_type_VIIh_spiral_rotation_conserves_amplitude` |
| 공통 | `compute_shear_source` signature / Ellis conformal ℋ² lift (FB-0.1) / Σ-independence (except VII_h) 보존 | 기존 `TestDimensionalConsistency` / `TestVII_h_Spiral` 유지 + 확장 |

### 구체 작업 항목

1. **문헌 재확인 (먼저, 코딩 전)**:
   - Wainwright-Ellis 1997 §18 Table 11.1 Class B rows + §6 Class B algebras (III = VI_{-1}, IV = Bianchi-IV, V = k<0 FLRW, VI_h 전반, VII_h)
   - Pontzen & Challinor, *PRD* 79, 103518 (2009) — VII_h spiral signature in CMB; `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` FB12-F1 의 교훈 (formula-level validation)
   - `bass/transport/shear_sources.py::source_{III,IV,V,VIh,VIIh}` 현 구현 + SOURCE_STATUS PROVISIONAL 주석

2. **Validation 테스트 5개 추가** (III + IV + V regression + VI_h + VII_h):
   - `bass/transport/test_shear_sources.py::TestClassBFixedPoints` 새 클래스:
     - `test_type_III_dispatches_to_VIh_at_h_minus_1`: III factory 가 h=-1 의 VI_h 와 동일한 결과를 내는지 rel 1e-12 pin
     - `test_type_IV_WE_source_formula`: (n_3, A, ℋ) grid 에서 공식 rel 1e-12 match
     - `test_type_V_shear_zero_pin`: (A, ℋ) grid 에서 S_± = 0 exactly (regression)
     - `test_type_VIh_WE_source_formula`: (n_1, n_3, A, h, ℋ) grid 에서 공식 rel 1e-12 match; h-dependent prefactor 확인
     - `test_type_VIIh_WE_source_formula_and_spiral_signature`: W-E piece (Σ=0) rel 1e-12 + spiral piece (Σ≠0 - Σ=0) antisymmetric coupling + `ω_spiral ∝ √h` scaling
     - `test_type_VIIh_spiral_rotation_conserves_amplitude`: Spiral-only (Σ=0 baseline 제거) 상황에서 `(Σ_+, Σ_-)` 의 회전으로 인한 `Σ_+² + Σ_-²` amplitude invariant — Pontzen-Challinor 의 rotation 시그니처
   - Tolerance: 공식 rel 1e-12; FB-1.1/1.2 precedent 준수. `_CALH_GRID` 재활용.

3. **SOURCE_STATUS 승격**: III / IV / VI_h / VII_h 을 `"PROVISIONAL"` → `"VALIDATED"` 로 변경. V 은 이미 VALIDATED 이므로 reference / benchmark 필드만 FB-1.3 cross-ref 로 업데이트.

4. **Gallery 확장** (FB-1.3 의 non-no-op visual — 예상 3-4 PNG):
   - `plots/physics_gallery/11_integrator/09_fb13_classB_typeIV_WE_source.png`: IV 의 N_3²/A² twist 구조
   - `plots/physics_gallery/11_integrator/10_fb13_classB_typeVIh_WE_attractor.png`: VI_h h-dependent prefactor 시각화
   - `plots/physics_gallery/11_integrator/11_fb13_classB_typeVIIh_spiral.png`: VII_h spiral signature — (Σ_+, Σ_-) plane rotation trace (Pontzen-Challinor 2009 의 CMB 시그니처와 qualitative match)
   - (optional) `12_fb13_classB_typeV_shear_zero.png`: V 의 shear-vanishing + A²-in-curvature visualisation (regression 성격)
   - `scripts/make_physics_gallery.py` 에 `plot_11_09`..`plot_11_12` 추가 + CATALOG 등록
   - 각 PNG 눈으로 확인 (Read tool)

5. **Audit append**: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 에 **FB-1.3 supplement** 섹션 append (§1..§10 template).

6. `NEXT_SESSION_PROMPT.md §2` 를 **FB-1.4** (`anisotropic_3_curvature` 11-type consolidation — `tetrad_state.py` ³R_{ab}^{aniso} explicit per type; Phase FB-1 exit) bootstrap 으로 rotate.

### FB-1.3 non-goals (선 밑에 고정)

- **VII_h spiral coefficient κ 의 quantitative calibration 은 FB-5/FB-6** — 본 세션은 sign + scaling (∝ √h) + rotation 시그니처 pin 만
- **`anisotropic_3_curvature` 11-type 구현은 FB-1.4** — 본 세션은 shear source 만
- **Hierarchy RHS T4-T7 wire-up** 은 FB-2
- **Tilted sector** 은 FB-3 (β=0 유지)
- **Class B full Hewitt-Wainwright reduction** (Δ, Ñ 변수) 은 FB-5/FB-6
- **F3 / FB02-F1 / FB11-F1 / FB12-F1 / FB12-F3 carry-forwards**: 건드리지 말 것

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` §FB-1.2 + §10 + FB-1.3 placeholder (본 세션이 append 할 곳)
2. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.3`
3. `bass/transport/shear_sources.py::{source_III, source_IV, source_V, source_VIh, source_VIIh}` (현 구현 + SOURCE_STATUS PROVISIONAL 주석)
4. `bass/transport/test_shear_sources.py::TestClassAFixedPoints` + `TestVII_h_Spiral` + `TestDimensionalConsistency` (FB-1.2 precedent; 본 세션은 새 `TestClassBFixedPoints` 클래스)
5. Wainwright-Ellis 1997 §18 Table 11.1 Class B rows + §6; Pontzen & Challinor 2009 Sec. III (VII_h spiral)
6. `docs/audits/AUDIT_PROMPT.md` (phase-boundary audit template — 본 세션 전에 self-invoke)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (W-E §18 + Pontzen-Challinor 2009 §III 인용 필수 for VII_h)
3. PSTF invariants preserved; Ellis convention (FB-0.1) 유지
4. No silent fallbacks
5. Determinism
6. **VALIDATED 승격은 수치 검증 후에만**; PROVISIONAL 유지가 안전한 default
7. **Gallery PNG 는 눈으로 확인 후 commit**; physics 이상 시 즉시 in-session fix
8. **FB11-F1 + FB12-F1 교훈**: fixed-point coordinate chasing 금지, formula-level pin + qualitative signature (spiral rotation) 이 operative contract

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 2,800 + 신규 테스트)
- [ ] `TestClassBFixedPoints::test_type_{III,IV,V,VIh,VIIh}_*` green
- [ ] `shear_sources.SOURCE_STATUS["III"|"IV"|"VI_h"|"VII_h"]` 모두 `"VALIDATED"` + cross-ref 주석 (V 는 reference 업데이트)
- [ ] `plots/physics_gallery/11_integrator/{09..1N}_fb13_classB_*.png` 생성 + 시각적 inspection 완료
- [ ] `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 에 FB-1.3 supplement append (§1..§10)
- [ ] `docs/audits/AUDIT_PROMPT.md` self-invoke 로 P0/P1 스캔 완료 (결과 audit log FB-1.3 §6 에 기록)
- [ ] `NEXT_SESSION_PROMPT.md §2` → **FB-1.4** (`anisotropic_3_curvature` 11-type consolidation) bootstrap 으로 rotate
- [ ] 최종 commit 메시지: `FB-1.3: Class B background validation + VII_h spiral signature match` + `+ rotate NEXT_SESSION_PROMPT for FB-1.4`

## 진행 순서

1. `docs/audits/AUDIT_PROMPT.md` self-invoke (pre-phase scan)
2. FB plan §4 FB-1.3 + Pontzen-Challinor 2009 §III + shear_sources Class B 섹션 읽기
3. 각 Class B type 에 대해 `compute_shear_source` 를 REPL 로 먼저 돌려 behaviour 확인 (특히 VII_h spiral 회전)
4. `TestClassBFixedPoints` 에 테스트 6개 추가 (rel 1e-12 formula + spiral signature)
5. `SOURCE_STATUS` III/IV/VI_h/VII_h 승격 + cross-ref 주석 (V reference 업데이트)
6. Gallery 3-4 PNG 추가
7. 각 PNG Read tool 로 inspect → physics 검증
8. `AUDIT_PHASE_FB1_2026-04-19.md` 에 FB-1.3 supplement append
9. 전체 회귀 green 확인
10. `NEXT_SESSION_PROMPT.md §2` rotate to FB-1.4
11. commit

시작하세요. 본 세션은 **Class B 완주** — FB-1.2 의 formula-level pinning 방식을 Class B (twist-coupled) 에 확장하고, VII_h 의 Pontzen-Challinor spiral 시그니처를 qualitative 하게 (sign + scaling + rotation 보존) 고정합니다. FB-1.4 가 Phase FB-1 의 마지막 rotation 이며 `anisotropic_3_curvature` 로 닫힙니다.
```

</details>

---

<!-- Prior (FB-1.2) handoff prompt (saved for reference only; do not re-run). -->

<details>
<summary>Previous FB-1.2 handoff prompt (archived 2026-04-19)</summary>

```text
# FB-1.2 — Class A VIII / IX background validation + Bianchi IX recollapse event

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,753 passing + 1 skipped (FB-1.1 직후; 감사 로그: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` — FB-1.1 섹션, FB-1.2/1.3/1.4 placeholder 예약됨)
- **완료된 단계**: LB-0 … LB-6 + LB audits P2/P3 cleanup + **Phase FB-0 전체** + **FB-1.1**:
  - FB-0.1..0.3 (Ellis convention flip + tilt-field surface + LB-6 F2 seal)
  - FB-1.1 (Class A I/II/VI₀/VII₀ SOURCE_STATUS → VALIDATED; 4 new gallery PNGs `plots/physics_gallery/11_integrator/{03..06}_fb11_classA_*.png`; `TestClassAFixedPoints` 61 parametrised runs)
- **현재 phase**: **Full Bianchi Coverage (FB) — Phase FB-1 "Per-type background validation" (4 sessions)** 의 2/4 번째
- **전체 로드맵**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.2`
- **Carry-forward P2 (알고만 있을 것, 절대 건드리지 말 것)**:
  - F3 → `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² normalisation → **FB-2.4 예약**
  - FB02-F1 → `00_conventions.md §2` 에 `v̂_e` default cross-reference → **FB-3.1 예약**
  - FB11-F1 (new, FB-1.1) → W-E Table 11.1 fixed-point *coordinates* 는 fixed-N 프레임워크에서 직접 도달 불가 — **FB-5 / FB-6 cross-type continuity 에서 재검토**. 본 세션 FB-1.2 도 formula-level validation 에 집중, Hubble-normalised coordinate chasing 금지.

## 이 세션의 작업 범위 (FB-1.2 — Class A 나머지: VIII + IX)

**Goal**: `bass/transport/shear_sources.py` 의 Class A 남은 2 타입 (VIII / IX) 배경 소스를 literature ground truth 에 대해 per-type 검증하고 `SOURCE_STATUS` 를 `PROVISIONAL → VALIDATED` 로 승격. 동시에 Bianchi IX recollapse 처리를 위한 `solve_ivp` event detection (FB plan D5 "event-terminated" 옵션) 을 `einstein_bianchi.solve_bianchi_background` 에 도입.

### 기준이 되는 문헌 타깃

| 타입 | 해석해 / 수치 타깃 | 테스트 앵커 |
|---|---|---|
| VIII | Wainwright-Ellis §18 Table 11.1 row "VIII" (sl(2,ℝ) algebra, one negative eigenvalue). Ellis conformal source (현 구현) `S^{WE}_+ = -(2/3)[2N₁² - N₂² - N₃² + N₂N₃]`, `S^{WE}_- = (2/√3)[N₂² - N₃²]`. **Leading-order near-FLRW** form — full nonlinear Mixmaster dispatch 는 FB-5 로 유지. |
| IX | W-E §18 Table 11.1 row "IX" (so(3), Mixmaster, recollapse). Ellis conformal source `S^{WE}_+ = -(2/3)[2N₁² - N₂² - N₃² - N₂N₃]`, `S^{WE}_- = (2/√3)[N₂² - N₃²]`. Isotropic limit n₁ = n₂ = n₃ 에서 `S_± = 0` 확인 (W-E 가 지적한 pathology 유의 — current impl 에서 `2n² - n² - n² - n² = -n² ≠ 0` 이 되어 완전히 0 은 아님; FB-1.2 에서 이 값이 small 한지 확인만). |
| 공통 | `rho_shear ∝ 1/a⁶` (shear energy monotonic decay on non-recollapsing branches); `compute_shear_source` return signature / sign structure 변경 없음. |
| 추가 (IX 전용) | **Bianchi IX recollapse**: `solve_ivp(event=IX_recollapse)` 를 도입. 이벤트 정의: `a'(η) = a × ℋ → 0` 점 (즉 ℋ(a) = 0 지점 in vacuum; Planck-2018 FLRW background 에서는 Ωm + ΩΛ > 0 이므로 ℋ > 0 항상 — 실 recollapse 는 vacuum IX 에만 발생, 즉 non-representative fixture 에서 synthetic 하게 트리거). **FB-1.2 의 event branch 는 integrator 가 NaN/inf 없이 event 를 감지하고 종료하는지 smoke 만** — 실제 production IX 는 FB-5 / FB-6 에서. |

### 구체 작업 항목

1. **문헌 재확인 (먼저, 코딩 전)**:
   - Wainwright-Ellis 1997 §18 Table 11.1 VIII / IX rows + §6 sl(2,ℝ) / so(3) algebra 확인
   - Bianchi IX Mixmaster literature: BKL oscillation (Belinsky-Khalatnikov-Lifshitz 1970) — 본 세션은 axisymmetric smoke 만, full BKL oscillation 은 FB-5/FB-6 deferred
   - `lowell_bianchi_solver_reference.md §18` — anisotropic fixed-point additional notes
   - `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` FB11-F1 의 "formula-level validation" 프레이밍 준수

2. **Validation 테스트 2개 추가** (VIII + IX):
   - `bass/transport/test_shear_sources.py::TestClassAFixedPoints` 클래스에 append:
     - `test_type_VIII_WE_source_formula_and_signs`: (n1, n2, n3) 파라미터 grid 에서 S_+ / S_- 공식이 W-E Table 11.1 VIII 에 대해 rel 1e-12 match. Σ-independence pin. `n1 < 0` 조건 (sl(2,ℝ) algebra) 유지.
     - `test_type_IX_WE_source_formula_and_isotropic_near_limit`: 공식 match + isotropic n₁=n₂=n₃ 에서 `S_±` 가 small (W-E 의 알려진 pathology) — `|S_+| < 10 × (2/3) n² × ℋ²` band 같은 것 허용; 완전 zero 주장 안 함.
   - Tolerance: 공식 rel 1e-12; FB-1.1 precedent 준수. 기존 `_CALH_GRID` 재활용.

3. **`solve_ivp(event=IX_recollapse)` 도입** (production-safe smoke):
   - `bass/background/einstein_bianchi.py::solve_bianchi_background` 에 optional `event=recollapse_event` 인자 추가 (default None = 기존 동작; Type IX default factory 가 event 를 set). Event 정의: `ℋ → 0` 또는 `a' ≤ 0`. `solve_ivp` 의 `events=` 파라미터 사용.
   - Test: `test_bianchi_IX_recollapse_event_fires_on_synthetic_vacuum_background`. FLRW 배경이 대체로 확장 중이므로 synthetic vacuum (H ∝ sqrt(-k/a²)) 시나리오를 작게 시뮬 — 또는 `a_end = small` 로 짧은 window 테스트만. Realistic Bianchi IX 는 FB-5/FB-6 이라 명시.

4. **SOURCE_STATUS 승격**: VIII / IX 을 `"PROVISIONAL"` → `"VALIDATED"` 로 변경. 각 entry 에 FB-1.2 audit cross-ref 주석 추가.

5. **Gallery 확장** (FB-1.2 의 두 번째 non-no-op visual):
   - `plots/physics_gallery/11_integrator/07_fb12_classA_typeVIII_WE_attractor.png`: VIII S_+ / S_- 트라젝토리 + W-E formula 시각화
   - `plots/physics_gallery/11_integrator/08_fb12_classA_typeIX_recollapse_trace.png`: IX 배경 trace + (event branch on 에서) event-fire 시점 표시
   - `scripts/make_physics_gallery.py` 에 `plot_11_07_fb12_classA_typeVIII_WE_attractor` / `plot_11_08_fb12_classA_typeIX_recollapse_trace` 추가 + CATALOG 등록
   - 각 PNG 눈으로 확인 (Read tool) — physics 이상 시 즉시 in-session fix

6. **Audit append**: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 에 **FB-1.2 supplement** 섹션 append (§1..§10 template).

7. `NEXT_SESSION_PROMPT.md §2` 를 **FB-1.3** (Class B: III / IV / V / VI_h / VII_h — twist-coupled source, Pontzen-Challinor VII_h spiral 매치) bootstrap 으로 rotate.

### FB-1.2 non-goals (선 밑에 고정)

- **Class B (III / IV / V / VI_h / VII_h)** 는 FB-1.3 — twist-coupled source, Pontzen-Challinor spiral 매치 필요
- **`anisotropic_3_curvature`** 11-type 구현은 FB-1.4
- **Hierarchy RHS T4-T7 wire-up** 은 FB-2 (배경만 본 세션)
- **Tilted sector** 은 FB-3 (β=0 유지)
- **Bianchi IX full BKL oscillation / Mixmaster**: FB-5 / FB-6 (본 세션은 event-branch smoke 만)
- **W-E fixed-point *coordinates* (Σ̂_+ → specific values)** 추구 금지 — FB11-F1 deferred 이므로 formula-level pin 만 수행
- **F3 carry (`shear_magnitude_sq`)** 는 FB-2.4
- **FB02-F1 carry (`00_conventions §2` 교차참조)** 는 FB-3.1
- **Spectrum extraction / C_ℓ** 은 FB-7

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` §FB-1.1 + §10 + FB-1.2 placeholder (본 세션이 append 할 곳)
2. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.2` + §6 D5 (Bianchi IX recollapse 처리 옵션 — (a) event-terminated solve_ivp 가 권장)
3. `bass/transport/shear_sources.py::source_VIII, source_IX` (현 구현 + SOURCE_STATUS PROVISIONAL 주석)
4. `bass/transport/test_shear_sources.py::TestClassAFixedPoints` (FB-1.1 precedent; 본 세션이 동일 클래스에 VIII/IX 추가)
5. `bass/background/einstein_bianchi.py::solve_bianchi_background` (ODE integrator — event 파라미터 추가 지점)
6. Wainwright-Ellis 1997 §18 Table 11.1 VIII/IX rows + §6 (sl(2,ℝ) / so(3) algebra)
7. `docs/audits/AUDIT_PROMPT.md` (phase-boundary audit template — 본 세션 전에 self-invoke)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (W-E §18 Table 11.1 row VIII / IX 인용 필수; BKL reference optional)
3. PSTF invariants preserved; Ellis convention (FB-0.1) 유지
4. No silent fallbacks — event-branch 는 `None` default 에서 이전 거동 유지
5. Determinism
6. **VALIDATED 승격은 수치 검증 후에만**. PROVISIONAL 상태 유지가 항상 허용되는 안전한 default. **FB11-F1 의 교훈: fixed-point coordinate chasing 금지**, formula-level pin 이 operative contract.
7. **Gallery PNG 는 눈으로 확인 후 commit**. Physics-이상 (예: IX event 가 realistic 배경에서 잘못 발화, VIII S_+ 가 sign 반전) 은 즉시 in-session fix.

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 2,753 + 신규 테스트)
- [ ] `TestClassAFixedPoints::test_type_VIII_*` / `test_type_IX_*` green
- [ ] `test_bianchi_IX_recollapse_event_*` green (synthetic fixture)
- [ ] `shear_sources.SOURCE_STATUS["VIII"]` / `["IX"]` 모두 `"VALIDATED"` + cross-ref 주석
- [ ] `plots/physics_gallery/11_integrator/{07_fb12_classA_typeVIII_WE_attractor.png, 08_fb12_classA_typeIX_recollapse_trace.png}` 생성 + 시각적 inspection 완료
- [ ] `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 에 FB-1.2 supplement append (§1..§10)
- [ ] `docs/audits/AUDIT_PROMPT.md` self-invoke 로 P0/P1 스캔 완료 (결과 audit log FB-1.2 §6 에 기록)
- [ ] `NEXT_SESSION_PROMPT.md §2` → **FB-1.3** (Class B III/IV/V/VI_h/VII_h; twist-coupled source, Pontzen-Challinor spiral) bootstrap 으로 rotate
- [ ] 최종 commit 메시지: `FB-1.2: Class A VIII/IX background validation + Bianchi IX recollapse event` + `+ rotate NEXT_SESSION_PROMPT for FB-1.3`

## 진행 순서

1. `docs/audits/AUDIT_PROMPT.md` self-invoke (pre-phase scan)
2. FB plan §4 FB-1.2 + §6 D5 + W-E §18 Table 11.1 VIII/IX rows + shear_sources 소스 구현 읽기
3. VIII / IX 각각에 대해 `solve_bianchi_background` trajectory 를 Jupyter-style REPL 로 먼저 돌려 behaviour 확인
4. `TestClassAFixedPoints` 에 VIII / IX 테스트 추가 (rel 1e-12 formula pin)
5. `solve_bianchi_background` 에 `events=` 파라미터 추가 + synthetic vacuum-IX recollapse smoke test
6. `SOURCE_STATUS` VIII / IX 승격 + cross-ref 주석
7. Gallery 2 PNG 추가 (`scripts/make_physics_gallery.py` 에 `plot_11_07`, `plot_11_08`)
8. 각 PNG Read tool 로 inspect → physics 검증
9. `AUDIT_PHASE_FB1_2026-04-19.md` 에 FB-1.2 supplement append
10. 전체 회귀 green 확인
11. `NEXT_SESSION_PROMPT.md §2` rotate to FB-1.3
12. commit

시작하세요. 본 세션은 **Class A 완주** — FB-1.1 의 formula-level pinning 방식을 그대로 VIII / IX 에 확장하고, Bianchi IX 의 recollapse 처리를 위한 event-detection 인프라를 도입합니다. FB11-F1 의 교훈 (fixed-N 프레임워크에서 self-similar coordinate chasing 금지) 을 반드시 준수: W-E Table 11.1 "asymptotic" 언어는 formula-match 로 구체화, dynamical system 재매개화는 FB-5/FB-6 으로 유지.
```

</details>

---

## 3. End-of-session self-update procedure

At the end of a session, before the final commit:

### Step 1 — Determine the next session target

- If the current session's tasks all completed successfully → next target is the subsequent LB-N per README.md §3 "Session sequence"
- If a task partially completed → next target is the same LB-N with the remaining items
- If a blocker was discovered → next target is "unblock: {description}" with an explicit issue list

### Step 2 — Pick the right template from §4

Each LB-N → LB-(N+1) transition has a pre-written template in §4 below. Copy the matching template.

### Step 3 — Customize the template with session-specific numbers

Fill in:

- **baseline test count** (after this session's commits): run `pytest bass/ tsc/ -q` and read the tail line
- **updated "완료된 작업" list** (what's now green and shouldn't be re-done)
- **anything surprising from the session** (performance cliffs, physics subtleties, solver quirks) — add as a "Session N notes" block

### Step 4 — Replace §2 with the customized template

Edit this file. Only §2 rotates; §1, §3, §4 stay intact.

### Step 5 — Update the header

Change:

- `Last rotated: {old date}` → `Last rotated: {today ISO}`
- `Current target session: {old}` → `Current target session: LB-(N+1) {topic}`

### Step 6 — Final commit

Include this file in the final commit of the session. Commit message example:

```text
LB-N: {session accomplishment}

{body}

+ rotate NEXT_SESSION_PROMPT for LB-(N+1)
```

---

## 4. Template library (§2 replacements for each LB-N → LB-(N+1) transition)

### 4.1 After LB-1 → bootstrap for LB-2 (PSTF multipole hierarchy)

```text
# Phase LB 구현 계속 — LB-2 PSTF multipole hierarchy

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: {FILL IN}
- **완료된 세션**: LB-0 (external-code guard), LB-1 (species backgrounds γ/ν/b/c/Λ)

## 우선 읽어야 할 문서

1. `docs/lowell_bianchi/README.md` §3 (dependency graph)
2. `docs/lowell_bianchi/00_conventions.md` §5 (PSTF packing), §4 (Σ² normalisation)
3. `docs/lowell_bianchi/02_multipole_hierarchy_spec.md` — 이 세션 스펙
4. 참조: `lowell_bianchi_solver_reference.md` §6 (9-term hierarchy 원본)

## 이 세션의 작업 (LB-2는 2 세션 분량 ~1200 LoC — 첫 파트)

`02_multipole_hierarchy_spec.md §12` Implementation checklist 앞 절반:

- `bass/hierarchy/` 서브패키지 생성
- `PSTFTensor`, `PSTFHierarchyState` + packed-full 변환 (Clebsch-Gordan ℓ≤8 사전계산)
- `sym_trace_free` utility
- T1~T9 중 T1, T2, T3, T8, T9 (orthogonal Bianchi에서 활성화되는 subset)
- 테스트 H-01 ~ H-17

두 번째 파트 (다음 세션)에서:
- T4, T5, T6, T7 나머지 term (tilted/vorticity/Bianchi-curved 용)
- `hierarchy_rhs_photon` driver
- 통합 테스트 H-18 ~ H-26

LB-2 범위 제약:
- **Orthogonal Bianchi I, V, VII_0만 대상** — 나머지 type은 NotImplementedError
- **collision은 LB-4 hook으로 남김** — LB-2에서는 K_{A_ℓ} 인터페이스만 정의
- **closure는 HardCut만 구현** — 나머지 (FreeStream/PowerLaw/TCA) 는 LB-3

## 핵심 원칙 (고정)

1. 외부 코드 금지
2. Non-perturbative everywhere
3. Citation in every docstring (Ellis §4.5-4.6, lowell §6 인용 필수)
4. PSTF tensors always STF
5. No silent fallbacks
6. FLRW limit test 필수

## 검증 체크리스트 (최종 commit 전)

- [ ] 전체 회귀 green
- [ ] 신규 테스트 spec 수치 타깃 일치
- [ ] Cite map 준수
- [ ] NEXT_SESSION_PROMPT.md §2 교체 (LB-2 두번째 파트 또는 LB-3용, 완료도에 따라)
- [ ] 최종 commit 메시지에 "+ rotate NEXT_SESSION_PROMPT" 포함

## 진행 순서

1. 스펙 3개 읽기 (README, 00_conventions, 02_hierarchy)
2. Subpackage 레이아웃 생성
3. PSTFTensor + 변환 행렬 → 테스트 H-01..H-08
4. Term 함수 T1/T2/T3/T8/T9 → 테스트 H-13..H-16
5. 부분 회귀 확인
6. NEXT_SESSION_PROMPT.md §2 교체
7. commit

이 세션이 LB-2 전체를 끝낼 수 있으면 그대로 진행하고, 끝나면 LB-3용 prompt로 교체.
```

### 4.2 After LB-2 → bootstrap for LB-3 (closure & truncation)

```text
# Phase LB 구현 계속 — LB-3 closure & truncation

## 프로젝트 컨텍스트
- Repo/venv/테스트 명령 (§4.1과 동일, baseline count만 갱신)
- **현재 baseline**: {FILL IN}
- **완료**: LB-0, LB-1, LB-2

## 우선 읽어야 할 문서
1. `docs/lowell_bianchi/03_closure_truncation_spec.md`
2. (기 완료) LB-2의 `bass/hierarchy/pstf_tensor.py`, `hierarchy_rhs.py`
3. (기 구현) `bass/closure/quadrupole_tca.py` (W6-04) — TCAClosure가 재사용

## 이 세션의 작업 (~500 LoC + 300 LoC tests, 1 세션)

03_closure_truncation_spec.md §11 Implementation checklist 전체:

- `bass/hierarchy/closure.py` — ClosureStrategy Protocol + HardCut/FreeStream/PowerLaw/TCA
- `bass/hierarchy/closure_diagnostics.py` — measure_closure_error
- `build_default_closure` factory
- 테스트 C-01 ~ C-16

LB-3 범위 제약:
- TCA closure는 W6-04 `solve_tca_closure` 재사용 (재구현 금지)
- 새 physics 안 함 — closure만
- Stiffness handling 안 함 (LB-5)

## 핵심 원칙 + 검증 체크리스트 (§4.1과 동일)

## 진행 순서
(§4.1과 동일, NEXT_SESSION_PROMPT는 LB-4용으로 교체)
```

### 4.3 After LB-3 → bootstrap for LB-4 (Thomson collision + tilted visibility)

```text
# Phase LB 구현 계속 — LB-4 Thomson PSTF collision + lowell §11.3 tilted visibility

## 프로젝트 컨텍스트
- **현재 baseline**: {FILL IN}
- **완료**: LB-0..LB-3

## 우선 읽어야 할 문서
1. `docs/lowell_bianchi/04_thomson_collision_spec.md` — §8 (tilted visibility Layer A in-scope) 주의
2. `lowell_bianchi_solver_reference.md §11.1-§11.3` (scalar x_e 유지 + direction-dep boost 원칙)
3. (기 완료) LB-1 `bass/species/baryon.py` (`tau_dot`, `visibility`), LB-2 `bass/hierarchy/*`, LB-3 `closure.py`
4. (기 구현) `bass/collision/thomson_tensor.py` (W3), `bass/closure/quadrupole_tca.py` (W6-04), Y-Block `bass.tilt.species_tilt`
5. 참조: `lowell §4, §9.2, §11.3`

## 이 세션의 작업 (~600 LoC + 450 LoC tests, 1 세션)

04_thomson_collision_spec.md §11 Implementation checklist 전체:

- `bass/collision/polarization.py` — PolarizationHierarchyState, E-mode source
- `bass/collision/thomson_pstf.py` — ThomsonPSTFCollisionOperator (orthogonal PSTF kernel)
- `bass/collision/tilted_visibility.py` — **lowell §11.3 Layer A**: TiltedVisibility wrapper에서 Γ̃_T, κ̃, g̃ 를 scalar × 비선형 Lorentz boost factor B(η, e) = cosh β + sinh β (ê·v̂_e) 로 제공
- 테스트 TC-01 ~ TC-16 + TV-01 ~ TV-08 (총 24+개)

LB-4 범위 제약:
- **PSTF kernel 자체의 full Lorentz boost는 LB-4b**로 분리 유지 (LB-1b tilted species registry 의존)
- Tilted visibility는 **Layer A만** — scalar 보정인자 제공, hierarchy moment projection은 LB-4b
- B-mode는 LB-4c
- 2nd-order v_e² 보정 금지 (LB-4d)
- **Non-perturbative β 엄수**: `1 + v_e · e` 선형근사 금지. 반드시 `cosh β + sinh β (ê·v̂_e)` 형태 유지 (TV-04, TV-07이 lint로 강제)
- **scalar x_e(η), T_m(η) 재계산 금지** — `BaryonBackground` LB-1 HyRec fixture 유지 (lowell §11.1)

## (나머지 §4.1과 동일, NEXT_SESSION_PROMPT는 LB-5용으로)
```

### 4.4 After LB-4 → bootstrap for LB-5 (unified integrator)

```text
# Phase LB 구현 계속 — LB-5 unified background + hierarchy integrator

## 프로젝트 컨텍스트
- **현재 baseline**: {FILL IN}
- **완료**: LB-0..LB-4

## 우선 읽어야 할 문서
1. `docs/lowell_bianchi/05_integrator_spec.md`
2. LB-1..LB-4 결과물 (species, hierarchy, closure, collision)
3. `bass/background/einstein_bianchi.py` (기존 FLRW limit)

## 이 세션의 작업 (~500 LoC + 400 LoC tests)

05_integrator_spec.md §11 Implementation checklist 전체:

- `bass/hierarchy/pack_unpack.py` — state vector utilities
- `bass/hierarchy/aux_state.py` — IntegratorAuxState
- `bass/hierarchy/ic.py` — IC constructors (zero IC baseline)
- `bass/hierarchy/neutrino_reduced.py` — 4-scalar ν fluid RHS
- `bass/hierarchy/event_detection.py` — 임계 η 이벤트
- `bass/hierarchy/integrator.py` — LowellBianchiIntegrator main driver
- 테스트 I-01 ~ I-18

LB-5 범위 제약:
- k = 0 (배경만)
- L_max = 6 기본
- 아직 tilted 안 함 (v_species = 0)

## (나머지 §4.1과 동일, NEXT_SESSION_PROMPT는 LB-6용으로)
```

### 4.5 After LB-5 → bootstrap for LB-6 (integration regression)

```text
# Phase LB 구현 계속 — LB-6 Kolb thermal history + CAMB geometry 회귀

## 프로젝트 컨텍스트
- **현재 baseline**: {FILL IN}
- **완료**: LB-0..LB-5

## 우선 읽어야 할 문서
1. `docs/lowell_bianchi/06_integration_tests_spec.md`
2. LB-5 `LowellBianchiIntegrator` 결과

## 이 세션의 작업 (~400 LoC tests, 1 세션)

06_integration_tests_spec.md §11 Implementation checklist 전체:

- `bass/integration/test_lowell_bianchi.py` 신규
- LB-6-01 ~ LB-6-24 테스트
- Kolb thermal history 매치 (z_eq=3400, z_*=1089.94)
- CAMB geometry 매치 (η_* ≈ 13873, η_0 ≈ 14153)
- Bianchi I shear-decay 불변량

실패 시 diagnostic playbook (§12) 참조. 각 실패 테스트는 정확히 한 LB-N 세션으로 역추적 가능.

## 세션 완료 시 다음 할 일

LB-6 전부 green이면:
- `NEXT_SESSION_PROMPT.md §2`를 **Phase LB 완료 + post-LB 단계 기획** 용으로 교체
- Phase LB 전체 요약 commit ("Phase LB complete: low-ℓ Bianchi solver bedrock verified")

LB-6 부분 실패면:
- 실패한 테스트별로 diagnostic playbook 적용
- `NEXT_SESSION_PROMPT.md §2`를 "LB-N re-open to fix {specific failure}" 로 교체

## (나머지 §4.1과 동일)
```

### 4.6 After LB-6 → bootstrap for post-LB phase

```text
# Phase LB 완료 → post-LB 단계 기획 세션

## 프로젝트 컨텍스트
- **현재 baseline**: {FILL IN}
- **완료**: LB-0..LB-6 전체. Low-ℓ Bianchi solver bedrock 검증 완료

## 이 세션의 작업 (설계만, 코딩 없음)

다음 중 하나를 선택해서 상세 design docs 작성:

**옵션 A — Line-of-sight projection + C_ℓ 추출** (lowell §7 matrix propagator)
- `bass/spectrum/lowell_cl_projection.py` 설계
- PSTF hierarchy 결과 → C_ℓ^{TT,EE,TE} 추출
- CAMB FLRW limit 매치 < 5% 목표

**옵션 B — Perturbation sector** (lowell §9, §13)
- 스칼라 perturbation equations을 PSTF hierarchy에 얹기
- CAMB regular adiabatic seed IC
- Tilted boost rule (§13.5)

**옵션 C — Direction-dependent likelihood** (lowell §14)
- HTT 재설계 (§3의 P0 3종 해결)
- 3-mode operational structure 구현

각 옵션별 `docs/lowell_bianchi/` 하위 새 spec 디렉토리 생성, 세션 분해, 의존성 그래프 작성.

## (나머지 §4.1과 동일, NEXT_SESSION_PROMPT는 선택된 옵션의 첫 세션용)
```

---

## 5. Meta-notes for long-term maintenance

**When Phase LB is fully done** (LB-6 green):
- `NEXT_SESSION_PROMPT.md` rotates into post-LB territory (lowell §7, §9, §13, §14)
- This file can either continue (§4 grows with post-LB templates) or be renamed / archived
- Recommendation: keep it as the single rotating handoff for **all** multi-session work; add new template sections as needed

**When handing off between humans**:
- §2 is the "start here" block — a colleague can read only §2 and bootstrap
- §1, §3 are the mechanism; read once, ignore afterwards
- §4 is reference — consult only when rotating

**When something unexpected happens**:
- Scope change / blocker / external event → write a free-form §2 that explicitly says "BLOCKED — next agent needs to handle X before resuming LB-N"
- Do not try to hide the anomaly in a normal-looking prompt

**Commit discipline**:
- Every commit that includes a §2 rotation must have "+ rotate NEXT_SESSION_PROMPT" in its commit message — this makes the handoff auditable via git log
