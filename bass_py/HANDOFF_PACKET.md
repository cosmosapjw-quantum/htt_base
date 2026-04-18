# BASS_py Integration — RESEARCH HANDOFF PACKET v1.0
## Session: 2026-04-17 ~ 2026-04-18 (compacted)
## Target: Resume in fresh thread without context loss

---

## 1. 초압축 요약 (TL;DR)

| Field | Status |
|-------|--------|
| **Project** | bass_py (low-ℓ Bianchi tilt detector) — companion to bass_rs thesis code |
| **Current phase** | W8 phase, 2/3 prompts complete; W8-03 next |
| **Overall progress** | 10 / 24 prompts = **41.7%** of full W6–W15 roadmap |
| **Tests** | 1,637 passing, 0 failing, 0 P0/P1 findings |
| **Critical recent result** | τ_reion = 0.054108 vs Planck 2018 0.054 (Δ=0.0001, <0.2%) |
| **Next immediate action** | W8-03 visibility source g·Π (Document 12 ceiling item 2/3) |
| **Estimated remaining** | 7–10 more sessions (conservative 10–12) |

---

## 2. 핵심 문제설정

### 2.1 Thesis context (Jiwon, Soongsil OMEG)
"Tetrad-Based Departure Decomposition for FLRW Departure in Bianchi Anisotropic Cosmologies"

Master identity extending MES kinematic bound hierarchy across all 9 Bianchi types:
$$x_C = \Sigma^2_{\rm std} - W^2_{\rm std} + \Omega_{\rm tilt} + \Omega_{k,{\rm aniso}}$$

Three-bound hierarchy $B_\sigma > B_\omega > B_{\dot u}$.

Key production result (established): $\ln B({\rm FLRW\_tilt}) = +26.40$, $\beta = 1.360\times 10^{-3}$, $F_{\rm Bayes} = 0.093 \pm 0.025$.

### 2.2 bass_py scope (this project)

- **Low-ℓ (≤30)** special-purpose CMB solver (**inverse of MES**)
- **Direction-dependent likelihood generator** (not an all-ℓ C_ℓ pipeline)
- Global tilt vs local boost (W_R ≈ 200 Mpc patch) discrimination
- **Companion** to Rust bass_rs (~18k LoC, production track)
- **First-data-exposure** version (Python for inference/validation before Rust)
- **Honest-scope documentation mandatory** — scope limits declared in every module

### 2.3 Success criteria (each prompt)

- Pure-function/dataclass design; W3 gating for σ² reduction operations
- Physical sign assertions (v1.2 pattern) on all algebraic inverses
- Cross-module cross-checks at machine precision
- Banned vocabulary scan CLEAN
- Full regression 0 failures

---

## 3. 확정 / 조건부 / 폐기된 결론

### 3.1 ✅ CONFIRMED (ESTABLISHED tier)

| Result | Magnitude | Verification |
|--------|-----------|--------------|
| W6-04 TCA closure formula (sign-corrected v1.2) | — | 4-way cross-check at machine precision (1.30e-16) |
| Polarization amplification factor at tight coupling | 4/3 exactly | Test verified (independent script) |
| Spin-2 streaming α^E_ℓ, β^E_ℓ (PSTF form) | Analytic | Pontzen-Challinor 2007 Eq. 5.2 cross-referenced |
| W7-02 + W7-01 joint fixed-point ≡ W6-04 | rel 1.28e-11 | 14-iteration geometric convergence (spectral radius ~1/6) |
| HyRec-2 sandbox reproducibility | 25ms/run | No external lib dependencies (no GSL/HDF5/FFTW) |
| $z_*$ (last scattering, κ=1) | **1089.89** | Planck 2018 ref 1089.95±0.27 (0.06 agreement) |
| $x_e(z=1075)$ | **0.11335** | User memory ref 0.1137 (0.3% agreement) |
| $\tau̇(z=1100)$ | **0.0684 /Mpc** | CAMB/CLASS literature range [0.05, 0.10] |
| $\tau_{\rm reion}$ with Planck 2018 defaults | **0.054108** | Planck 2018 ref 0.054±0.007 (Δ=0.0001) |
| Asymptotic $x_e^{\rm rei}$ limits | $1+f_{He}$ and $1+2f_{He}$ | Analytical + test verified |
| κ integration needs $\dot\tau_{\rm conf}/H$ (no (1+z)) | — | Caught pre-module during ref generation |

### 3.2 🟡 CONDITIONAL (domain-specific)

| Statement | Condition |
|-----------|-----------|
| W5-A `damping_rate` = Hubble only | *interim contract v1.2*; Thomson via W6-02/W7-02 wrappers exclusively; full DampingProfile retrofit scheduled end-of-W7 (not yet executed) |
| $T_m$ extension at z < 1 = adiabatic-cooled const | acceptable because $T_m$ not used in Thomson opacity; post-reion photo-heating (~10⁴ K) not modeled; irrelevant for W8-03+ |
| `polter_camb` ↔ PSTF Π normalization | declared but not pinned; W10-02 task |
| $m \neq 0$ Wigner normalization in W5-C | declared in docstring, inert for axisymmetric tests used so far; needs fix before m≠0 activation |
| Reionization tanh amplitude HeI+H combined at same z_rei | standard CAMB convention; not separately resolved |

### 3.3 ❌ DEPRECATED / REJECTED

| Idea | Reason rejected |
|------|----------------|
| κ integrand $\dot\tau_{\rm conf}/((1+z)H)$ | Wrong: (1+z) cancels. Correct form $\dot\tau_{\rm conf}/H$. Caught pre-module. |
| TCA inverse formula with sign $\Gamma_T M X = -S$ | Wrong sign; correct form is $+S$. W6-04 v1.2 patch (sign assertion mandatory going forward). |
| Test design "trivial dynamics with non-zero source" (W7-01) | Structurally impossible — source $\propto \Gamma_T$ auto-zeros. Test replaced with correct zero-state behavior. |
| Tight rtol on values of small magnitude (W7-02, W8-02) | Machine precision ~1e-16 absolute; small values give rel ~1e-7. Use atol+rtol combo. |
| Initial expectation z_* unchanged by reionization | Wrong: reion adds τ_reion to κ(z=0), shifts z_* DOWN by ~5. Corrected test range. |

---

## 4. 수식/논증 상태

### 4.1 Fully derived and verified

**W6-04 TCA closure** (v1.2 sign-corrected):
$$\Gamma_T \begin{pmatrix} 9/10 & \sqrt{6}/10 \\ 3/(5\sqrt{6}) & 2/5 \end{pmatrix}\begin{pmatrix}\Theta_2\\E_2\end{pmatrix} = \begin{pmatrix}S_T\\S_E\end{pmatrix}$$

Subleading limit ($S_E=0$): $E_2/\Theta_2 = -\sqrt{6}/4$.

**Spin-2 streaming (Pontzen-Challinor 2007 Eq. 5.2, axisymm m=0)**:
$$\alpha^E_\ell = \sqrt{\ell^2-4}/(2\ell+1), \quad \beta^E_\ell = \sqrt{(\ell+1)^2-4}/(2\ell+1)$$
Boundary: $\alpha^E_2 = 0$ (spin-2 minimum).

**E-mode ℓ=2 effective damping** (from collision formula):
$\Gamma^E_2 = (2/5)\Gamma_T$, cross-source $S^E_2 = -(3/(5\sqrt{6}))\Gamma_T \Theta_2$.

**Θ-mode ℓ=2 effective damping** (W7-02):
$\Gamma^{\Theta}_2 = (9/10)\Gamma_T$, cross-source $S^\Theta_2 = -(\sqrt{6}/10)\Gamma_T E_2$.

**Reionization tanh** (standard CAMB):
$$x_e^{\rm rei}(z) = \tfrac{1+f_{He}}{2}[1 + \tanh((y_H-y)/\Delta y_H)] + \tfrac{f_{He}}{2}[1 + \tanh((y_{HeII}-y)/\Delta y_{HeII})]$$
$y=(1+z)^{3/2}$, $\Delta y = (3/2)(1+z_{\rm rei})^{1/2}\Delta z$, $f_{He}=Y_{He}/(4(1-Y_{He}))$.

### 4.2 Partially derived / awaiting completion

| Item | Status |
|------|--------|
| LOS source $g\cdot\Pi$ full formula | **W8-03 TODO** |
| FLRW Bessel baseline transfer | W9-01 TODO |
| Bianchi extension of LOS source | W11+ |
| PSTF Π ↔ CAMB polter normalization constant | declared; pinned at W10-02 |

### 4.3 Critical cross-checks (recorded)

1. **4-way TCA agreement** (W6-04 / W7-01 / W7-02 / joint fixed-point): ✅ machine precision
2. **Planck 2018 $z_* = 1089.95 \pm 0.27$** vs our **1089.89**: ✅
3. **Planck 2018 $\tau_{\rm reion} = 0.054 \pm 0.007$** vs our **0.054108**: ✅
4. **HyRec $x_e(z=1075) \approx 0.1137$** vs our **0.11335**: ✅ (0.3% off, cosmology variant)

---

## 5. 코드/수치/데이터 상태

### 5.1 Module ledger (bass/ packages)

| Module | Lines | Tests | Status | Role |
|--------|-------|-------|--------|------|
| `background/bianchi_types` | — | — | VALIDATED (pre-session) | Bianchi I metric |
| `background/einstein_bianchi` | — | — | VALIDATED (pre-session) | — |
| `perturbation/baryon_fluid` | ~350 | 52 | **VALIDATED W6-01** | ρ_b, v_b, Thomson drag |
| `perturbation/cdm_fluid` | ~280 | 37 | **VALIDATED W6-03** | ρ_c, v_c (no coupling) |
| `transport/multipole_hierarchy` (W5-A) | 387 | 108 | VALIDATED | Θ hierarchy framework |
| `transport/dipole_driven_hierarchy` (W6-02) | 422 | 70 | **VALIDATED W6-02** | Photon ℓ=1 wrapper |
| `transport/emode_hierarchy` (W7-01) | 403 | 62 | **VALIDATED W7-01** | Spin-2 E-mode hierarchy |
| `transport/implicit_hierarchy` | — | — | VALIDATED (pre-session) | Rodas5P |
| `transport/bianchi_i_hierarchy` | — | — | VALIDATED (pre-session) | — |
| `closure/quadrupole_tca` (W6-04) | 433 | ~50 | **VALIDATED v1.2** | Algebraic TCA, sign-fixed |
| `closure/polter_recoupling` (W7-02) | 336 | 42 | **VALIDATED W7-02** | Θ↔E Thomson loop |
| `collision/thomson_tensor` | — | — | VALIDATED (pre-session) | Σ_2 coefficients |
| `recombination/recombination_ingest` (W8-01) | 483 | 52 | **VALIDATED W8-01** | HyRec CSV parser + splines |
| `recombination/reionization` (W8-02) | 439 | 47 | **VALIDATED W8-02** | Tanh reion, τ=0.054 |
| Other (runtime/, tilt/, observational/, validation/) | — | ~500 | VALIDATED (pre-session) | — |

**Total**: 22 bass/ modules, **1,637 tests**, full regression ~40s.

### 5.2 Reference data

| File | Size | Purpose |
|------|------|---------|
| `bass/recombination/fixtures/recombination_ref_planck2018.csv` | 520 KB | Production reference (8,000 rows, z=1..8000) |
| `hyrec2_xe_planck2018_default.dat` | 367 KB | Raw HyRec-2 output (bundled in outputs) |
| `hyrec2_input_planck2018_default.dat` | 2.2 KB | HyRec input cosmology |
| `generate_ref_table.py` | 8 KB | Sandbox regeneration script (correct (1+z)) |
| `hyrec2_SESSION_NOTES.md` | 1.7 KB | Reproducibility notes |

### 5.3 Sandbox capabilities established

| Capability | Runtime | Dependencies |
|-----------|---------|--------------|
| HyRec-2 clone + compile | ~1 min | gcc only (standard Ubuntu) |
| HyRec-2 execution | **25 ms/run** | libm only (no GSL/HDF5/FFTW) |
| Reference table regeneration | ~1 sec | numpy only |
| Full bass+tsc regression | ~40 sec | pytest + numpy + scipy |

**Important**: external data downloads not required for any session. Sandbox self-reproduces HyRec reference at will.

### 5.4 Version/roadmap state

- **MASTER_PROMPT_LIST version**: v1.2 (frozen this session with W6-04 sign fix + polter arithmetic typo fix)
- **W3 gating**: CanonicalDecision + require_allow_reduction present in runtime/
- **Banned vocab scanner**: must be run on every new module; LIST: delve, crucial, multifaceted, nuanced, landscape, underscore, leveraging, facilitates, pivotal, elucidate, aforementioned, plethora, paradigm, intricate, tapestry, foster, interestingly, clearly, obviously, moreover, furthermore, additionally, consequently, "as can be seen", "in conclusion", "it is important to note"

---

## 6. Figure / 문서 상태

### 6.1 Session packets (all 9-section format)

| Packet | Status | Key claim |
|--------|--------|-----------|
| `WEEK6_01_PACKET.md` | Complete | Baryon fluid + Thomson drag |
| `WEEK6_02_PACKET.md` | Complete | Photon ℓ=1 dipole drive wrapper |
| `WEEK6_03_PACKET.md` | Complete | CDM fluid |
| `WEEK6_04_PACKET.md` | **v1.2** | TCA algebraic closure (sign-corrected) |
| `PATCH_v1_2_PACKET.md` | Complete | Sign fix batch + new pattern codification |
| `WEEK7_01_PACKET.md` | Complete | E-mode spin-2 hierarchy |
| `WEEK7_02_PACKET.md` | Complete | Polter recoupling, 4-way cross-check |
| `WEEK8_01_PACKET.md` | Complete | HyRec ingest, z_*=1089.89 |
| `WEEK8_02_PACKET.md` | Complete | Tanh reion, τ=0.054108 |

### 6.2 Design documents (pre-session, still canonical)

- `MASTER_PROMPT_LIST_bass_py_v1_2.md` — full 21-prompt roadmap W3→W15
- `CANONICAL_DECISION_DESIGN.md` — W3 gating system
- `BASS_PY_INTEGRATION_v4_1_MERGED.md` — integration architecture
- `L0_PRECISION_REPORT.md` — baseline precision targets

### 6.3 Thesis LaTeX (pre-session, not modified this session)

`ch01..ch11` + `main.tex` + `references.bib` in /mnt/project/. No changes to manuscript content this session (only result capture). Manuscript retrofit deferred (Option: end-of-W8 or later; currently W7 results not yet integrated into ch05).

---

## 7. 주요 논쟁점 / reviewer risk

### 7.1 High-risk review vectors

| Risk | Likelihood | Mitigation status |
|------|------------|-------------------|
| **W6-04 sign error pre-v1.2** could still be latent in W5 or W4 modules | Low | Systematic sign assertion pattern deployed; full re-audit scheduled per packet |
| `DampingProfile` interim contract confusing | Medium | v1.2 patch explicitly documented; W7+ refactor scheduled |
| polter ↔ Π normalization not pinned | Medium | Declared as W10-02 task; blocker for CAMB cross-check |
| Sobolev cancellation justification for FLRW recomb reuse | Medium | Memory shows 5 validity conditions A1–A5; current usage within scope, but "theorem" label was overclaim |
| AniCLASS structural exclusion of Bianchi I (all ν_m = 0) | None (architectural, not bug) | Declared in memory; no action |
| Tsagas fast-growth mechanism | Killed by Clarkson-Maartens (arXiv:2603.14511, no rebuttal) | Khronon is sole surviving dipole source |
| ch05 manuscript still has pre-v1.2 sign conventions | High (if thesis submission) | **ch05 sign retrofit is open task, not yet done** |

### 7.2 Low-risk but noteworthy

- $m=\pm 2$ Wigner normalization in W5-C: declared, inert for axisymmetric tests. Fix before m≠0 activation.
- W6-02 `v_b → v_e` rename for full-tilt generality: cosmetic W12.
- MASTER_PROMPT_LIST "(3/30)ζ" typo (correct: (2/15)ζ): fixed in v1.2.

---

## 8. 미해결 과제 (P0~P3)

### P0 (이번 스레드 종료 시 즉시 필요)
- 없음. W8-02까지 모두 validated, 0 P0/P1 findings.

### P1 (다음 스레드 1번째 턴 내)
1. **W8-03 (visibility source g·Π)** — Document 12 ceiling item 2/3
   - Combine W8-02 $g(\eta)$ + W7-02 Π to build LOS source
   - Target: ~350 lines, ~40 tests
   - Dependencies: W7-02 ✓, W8-02 ✓ (all satisfied)
   - Estimated 1 full-session prompt

### P2 (다음 2-3 스레드 내)
2. **W8-03 지원**: integrator layer에 이 source를 받도록 준비
3. **polter_camb ↔ Π pinning** (W10-02 pre-work): 상수 정해야 C_ℓ 비교 가능
4. **DampingProfile full retrofit to W5-A**: 현재 interim contract 해소
5. **η(z) conversion utility**: W8-01이 z-space; integrator는 η-space 필요
6. **W9-01 (FLRW Bessel baseline)**: 대형 prompt, line-of-sight integration 출발점

### P3 (백로그, 시간 여유 시)
7. **ch05 manuscript retrofit**: W6-04 sign fix 반영 (지금은 틀린 부호로 적혀있을 가능성)
8. **W5-C m=±2 normalization fix**
9. **W6-02 `v_b → v_e` cosmetic rename**
10. **bass_rs `hyrec_emla.rs` h0_cgs unit bug fix**: sandbox로 우회 가능, 긴급도 낮음
11. **VER06 SSOT rerun** (lnZ/lnB JSON inconsistency 해결) — 진행 중인 thesis production에만 필요

---

## 9. 다음 스레드 시작용 즉시 실행 계획

### 9.1 첫 3턴 (세션 시작 → W8-03 착수)

**Turn 1 (user)**: CONTINUATION BRIEF (섹션 11) 붙여넣기 + "W8-03 시작" 요청

**Turn 2 (Claude, 예상)**:
- Project knowledge search로 session state 확인
- W7-02 polter API + W8-02 visibility API 재확인 (project_knowledge_search "polter_recoupling" / "reionization")
- W8-03 물리 재유도:
  - Source at recombination: $S_T^{\rm LOS}(\eta) = g(\eta)\cdot \Pi_T(\eta) + \text{Doppler} + \text{ISW}$
  - Source for polarization: $S_E^{\rm LOS}(\eta) = g(\eta)\cdot \Pi_E(\eta)$ with polter-specific Π
  - Scope declaration (full LOS vs partial; m=0 axisymmetric only)
- 설계 sketch 제시 → 승인 대기

**Turn 3 (user)**: "승인"

**Turn 4 (Claude)**: W8-03 구현 + test + packet → 제출

### 9.2 W8-03 후 세션별 계획 (conservative 10 sessions remaining)

| Session | Prompts | 주요 risk |
|---------|---------|-----------|
| S+1 (now) | W8-03 | LOS integration sign conventions |
| S+2 | W9-01 (FLRW Bessel) | Bessel transfer function normalization |
| S+3 | W9-02 (Bianchi matrix propagator) | numerical stiffness |
| S+4 | W10-01 (C_ℓ TT/EE) | polter ↔ Π normalization pin needed |
| S+5 | **W10-02 V1 CAMB gate** | Tier A<5% — likely 1–2 retry iterations |
| S+6 | W11-01, W11-02 | C_ℓ(n̂), BiPoSH |
| S+7 | **W11-03 V2 bass_rs gate** | soft-optional but debugging time possible |
| S+8 | W12, W13 prompts | tilt + patch physics |
| S+9 | W14, W15-01 | 3-signature separator, sky geometry |
| S+10 | **W15-02, W15-03 V6 gate** | final inference + mock calibration |

**Buffer**: +2 sessions for V-gate retries and physics bug cycles.

---

## 10. 유지해야 할 규약/컨벤션

### 10.1 v1.2 mandatory patterns (every new module)

1. **Physical sign assertions**: Every algebraic inverse/steady-state must include `assert quantity > 0` or `assert quantity < 0` against externally-known physical sign. Ratio-only tests are **sign-blind** and insufficient.

2. **Cross-module cross-check**: Where two modules compute the same quantity by independent paths, write explicit cross-check test at machine precision. (W6-04 ↔ W7-01 ↔ W7-02 ↔ joint fixed-point is the gold-standard template.)

3. **Analytic derivation BEFORE code**: Derive matrix/formula on paper in packet §3 before coding. W6-04 success pattern: zero first-attempt failures when this is done.

4. **Non-invasive wrapping**: Extensions import W5-A functions, delegate when trivial config, guarantee bit-exactness with dedicated `is_trivial → W5-A identical` tests (pattern from W6-02, W7-02).

5. **Scope declaration in docstring**: Every module has explicit "Not in scope (deferred)" section listing deferred features with target prompt.

### 10.2 SSOT discipline

- All constants in canonical source files (ssot.py, obs_defaults.json, d2_convention.rs).
- Anti-regression guards for critical invariants (e.g., D₂ convention in d2_convention.rs with 7 tests).
- Version-stamp all sign-conventions in module docstring.

### 10.3 Code style / banned vocab

Banned: delve, crucial, multifaceted, nuanced, landscape, underscore, leveraging, facilitates, pivotal, elucidate, aforementioned, plethora, paradigm, intricate, tapestry, foster, interestingly, clearly, obviously, moreover, furthermore, additionally, consequently, "as can be seen", "in conclusion", "it is important to note"

Run on every new module + test + packet before delivery.

### 10.4 Workflow rhythm

1. Module + test pair in single turn
2. Run full test → diagnose failures → patch
3. Full regression (bass/+tsc/+ownership_freeze)
4. Banned vocab scan
5. 9-section PACKET.md (physics, tests, cross-checks, score card, next)
6. Copy to /mnt/user-data/outputs/
7. `present_files` tool
8. Status summary + request approval

### 10.5 Language

- **Korean** for high-level discussion, decisions, planning
- **English** for technical code, tests, packets, docstrings
- User switches freely; Claude mirrors

### 10.6 Terminology

- "Departure parameter" is mandatory (not "defect") — thesis-wide convention

---

## 11. CONTINUATION BRIEF (새 스레드에 그대로 붙여넣기)

```
[CONTINUATION BRIEF — bass_py integration, 2026-04-18 → new session]

현재 상태 요약:
- W6 phase (4/4) + W7 phase (2/2) + W8 phase (2/3) 완료
- Total 1,637 tests passing, 0 failures, 0 P0/P1 findings
- bass/ 22 modules, 룬타임 ~40s
- MASTER_PROMPT_LIST v1.2 (W6-04 sign fix 반영)

최근 핵심 결과:
- τ_reion = 0.054108 (Planck 2018 0.054±0.007과 Δ=0.0001 일치)
- z_* = 1089.89 without reion, 1085.17 with reion
- W6-04 ↔ W7-01 ↔ W7-02 ↔ joint fixed-point 4-way machine-precision agreement
- HyRec-2 sandbox 컴파일 + 25ms/run, 외부 라이브러리 불필요

활성 v1.2 patterns (모든 새 모듈 필수):
1. Physical sign assertions (externally-known sign으로)
2. Cross-module cross-check at machine precision
3. Analytic derivation BEFORE code
4. Non-invasive wrapping pattern
5. Scope declaration with deferred items

다음 작업: W8-03 (visibility source g·Π)
- Document 12 ceiling item 2/3
- W7-02 polter Π + W8-02 visibility g(η) 결합
- LOS source at recombination
- 목표 ~350 lines, ~40 tests
- 의존성 전부 충족됨 (W7-02, W8-02 validated)

Handoff packet files (이 스레드에서 업로드):
- handoff_core.zip — 이번 세션 packets + 설계 문서
- handoff_modules.zip — 이번 세션 새 모듈 + tests
- handoff_data.zip — HyRec reference CSV + HyRec-2 sandbox 아티팩트

작업 방식 컨벤션 유지:
- 한국어 고수준 논의, 영어 기술 실행
- 승인 후에만 코드 진행 (user approval gate)
- 매 prompt당 module+test+packet 9-section 납품
- Banned vocab scan 실행
- 독립 검증 script로 machine-precision cross-check 확인

W8-03 착수 승인 기다리는 상태.
```

---

## 12. 파일 업로드 전략

이 세션에서 생성된 모든 artifacts를 3개 zip으로 분할:

| zip | 내용 | 크기 (예상) | 용도 |
|-----|------|------------|------|
| `handoff_core.zip` | 세션 패킷 9개 + 설계 docs | ~200 KB | 인수인계 컨텍스트 |
| `handoff_modules.zip` | 새 모듈 (W6-01~W8-02) + test suites | ~500 KB | 재생 가능성 확인용 |
| `handoff_data.zip` | HyRec CSV + session notes + generator | ~900 KB | 수치 재현 |

총 ~1.6 MB. 대화형 인터페이스에서는 한 번에 업로드 가능.

**권장 업로드 순서 (새 세션 시작 시)**:
1. `handoff_core.zip`만 업로드하고 CONTINUATION BRIEF 붙여넣기 → Claude 상태 확인
2. 필요 시 `handoff_modules.zip`, `handoff_data.zip` 추가 업로드

단, `/mnt/project/` 디렉토리에 이미 저장된 pre-session 파일들 (MASTER_PROMPT_LIST_v1_2.md, DOC-*, 설계안 등)은 자동 지속됩니다. 위 3개 zip은 **이번 세션에서 새로 추가된 것들**만 포함.

---

**End of handoff packet.**

Generated: 2026-04-18  
Session duration: compacted (multiple sub-sessions)  
Author-of-record: Claude (Opus 4.7) on behalf of Jiwon
