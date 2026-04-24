# Next-Session Opener Prompt

_Session frozen at commit `bce0eb9` on 2026-04-24. Copy the block below into a fresh Claude Code session to resume._

---

## Opener (Korean, matches user's preferred style)

```
V5 gap-closure 작업을 이어서 할게. 이전 세션에서 V5-RUNTIME commit `bce0eb9`로
Blockers 1+2가 완전히 닫혔어 — residual-joint operator 재작성 + 8개 patch를
통해 λ_max(A_right) ≈ 1e-16 (machine precision) 달성, cosmological η=261→14147 Mpc
IMEX 130초에 완주. FLRW D_2 = 1002.086744 μK² bit-identical 유지, v5 handoff
baseline 1366/1366 통과.

docs/V5_RUNTIME_TRACK_DIAGNOSIS.md 를 먼저 읽어 전체 맥락과 남은 follow-up
items을 파악해줘. 특히 "Known remaining items (out of scope for this session)"
섹션의 5개 항목이 다음 세션 후보:

  1. Round-3 source-block audit — 세션 끝에 pattern-matched로 넣은 source block
     diagonal sign flip(패치 ❽)을 Ma-Bertschinger / Seljak-Zaldarriaga 수준의
     공식 유도로 확인. Round-1/2와 동일한 cross-session audit prompt 패턴.
  2. geom_scale replacement — 현재 placeholder (sqrt(Σn² + twist² + 0.25·|R| +
     |R_PSTF|² + |σ|²)). 비-Type-I family의 transport scale 정의에 필요.
  3. Non-Type-I _family_conditioned_kernel_law — 10 × 10 tuning constants
     (II, III, IV, V, VI_0, VI_h, VII_0, VII_h, VIII, IX). Round-2 Q-7.2 가
     "no first-principles scalar replacement"를 명시; matrix-valued family
     dependence 유도 필요.
  4. Blocker 3 — from_recombination(background_monitor, z_*) constructor 구현.
     이제 operator가 stable하므로 실제 recombination IC injection 가능.
  5. Extended regression full run — bass/runtime/test_ver2_tier_b_execution.py
     (1시간) + bass/validation/test_ver2_campaign_evidence.py. Pre-session에
     4+4 pre-existing failure가 있었음 — 이제 residual-joint가 stable하므로
     다수가 재통과할 것으로 예상.

다음 단계로 [A/B/C/D/E 중 하나 선택]을 진행하고 싶어:

  A. Round-3 source-block 감사 — prompt 작성 후 외부 Claude에 전달 → 답변
     받으면 적용 + verify. 이 세션 패턴 반복. 1-2 세션 소요.
  B. geom_scale 대체 — v5 §03A/§03B spec 읽고 backend mode eigenvalue / 
     transport scale 유도. 비-Type-I families 직접 영향.
  C. Non-Type-I family_law 유도 — 구조상수 기반 matrix-valued coupling.
     Type II, III, V, VII_0, VIII 최소 5개 family 검증. 장기 작업.
  D. Blocker 3 — from_recombination IC injection. 지금은 eta_initial=0.5 toy
     sentinel을 사용; 실제 recombination state에서 seeding하도록 수정. 
     SpeciesBackgroundRegistry.from_planck2018()에서 z_* ≈ 1089 근처 state 
     추출해서 IC로 injection.
  E. Extended regression 재확인 — 1시간 Tier-B suite 백그라운드 실행해서
     pre-existing failure 중 몇 개가 재통과하는지 확인. 먼저 이것부터 하면
     남은 실패 패턴으로 다음 세션 방향을 정할 수도 있음.

시작해줘.
```

Replace `[A/B/C/D/E 중 하나 선택]` with the desired option before sending.

---

## Quick reference for cold-start context

### What landed in commit `bce0eb9`

- **Blocker 1**: `multipole_cutoff` ∈ {4,6,8,12,16,20,30,40}; ceiling at 40.
- **Blocker 2**: 8-patch physics rewrite of `bass/hierarchy/ver3_layout_protocol.py`:
  1. `diag_base_by_slot = 0` (removes SO(3)-violating placeholder)
  2. Streaming coupling sign flip (weighted skew-adjoint, machine precision)
  3-4. Thomson damping sign fix (harmonic + local)
  5. Local↔harmonic cross coupling per Ma-Bertschinger eq 64-66
  6. T↔E quadrupole-only γ_T-proportional (KKS Π source)
  7. Hand-tuned scales → 0 or 1
  8. Source block diagonal sign flip (pattern-matched, needs Round-3)

### Fast verification after any code change (25 s total)

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
venv/bin/python scripts/v5_operator_fast_check.py                                           # 5 s
venv/bin/python -m pytest htt/bass/validation/test_d2_regression_anchor.py -q               # 1 s
cd htt && ../venv/bin/python -m pytest bass/los/ bass/transport/ bass/spectrum/ \
  bass/forward/ bass/validation/test_d2_regression_anchor.py \
  bass/validation/test_verification_pack.py bass/validation/test_ver3_gate_stop.py \
  bass/test_statistics.py bass/runtime/test_ver2_execution.py -q                            # 18 s
```

Success criteria:
- fast-check: `max Re(λ) < 1e-10` at both γ_T=0 and γ_T=1 across L_max ∈ {4,6,8,12,16}
- D_2 anchor: 6/6 pass, `D_2 = 1002.086744 μK²` unchanged
- handoff baseline: 1366 passed, 1 skipped

### Long-form verification (130 s) — cosmological IMEX

```python
# Inside htt/ with bass/ importable:
from bass.runtime import execute_tier_b_solver
# ...with eta_initial_mpc=261.0, eta_final_mpc=14147.0, L_max=8, FLRW β=0
# Expected: SUCCESS in ~130 s, reaches η=14147 Mpc, |T_last|_∞ bounded.
```

See `/tmp/imex_cosmo.py` (if still present) for the full working script; otherwise
reproduce from the `execute_tier_b_solver` call signature in
`htt/bass/runtime/test_ver2_tier_b_execution.py::test_execute_tier_b_solver_consumes_live_s1_s2_s3_hooks`
modified with cosmological η-range and Planck-2018 species (no `gamma_T_override`).

### Key file paths (unchanged from commit `bce0eb9`)

- `htt/bass/hierarchy/ver3_layout_protocol.py` — residual-joint operator (patches 1-8)
- `htt/bass/hierarchy/ver2_native_integrator.py` — IMEX + defensive ROS2 gates
- `htt/bass/runtime/ver2_execution.py` — cutoff validation + solver entry
- `scripts/v5_operator_fast_check.py` — 5 s spectrum verification
- `scripts/v5_runtime_spectral_audit.py` — 5-η snapshot audit
- `scripts/v5_runtime_operator_forensics.py` — FD/symmetry/L_max-sweep
- `docs/V5_RUNTIME_TRACK_DIAGNOSIS.md` — full session writeup
- `docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT{,_ROUND2}.md` — audit prompt templates
- `v5_residual_harmonic_algebraic_audit{,_round2}.md` — audit answers

### Important constraints (carry forward)

- **No toy / no surrogate**: per user directive (commit `85c2270` reversion).
  Every sign/coefficient change must be traceable to Ma-Bertschinger,
  KKS 1997, or Maartens-Ellis 1+3 kinetic theory.
- **D_2 bit-identity as safety gate**: FLRW invariant manifold implies
  `r_h(η_0) = 0` and `b_hh(η) ≡ 0`. Matrix-structure (A) changes are safe;
  bias (b) changes are NOT. D_2 anchor will immediately catch any leak.
- **project/ is gitignored**: planning docs, scoreboards, audit drafts
  go under `project/` and are local-only.
- **Audits are cross-session**: draft prompt → send to fresh Claude →
  receive answer as file → apply patches → verify. Pattern established
  by Round 1 + Round 2.

### Commit conventions

- Prefix: `V5-RUNTIME:` / `V5-SN:` / `docs:` / `AUDIT(tag):`
- Title under 70 chars
- Body explains Why and references findings
- Always trailer: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
- Do not skip hooks; resolve root causes
- Do not stage `CLAUDE.md` (gitignored) or anything under `project/`
