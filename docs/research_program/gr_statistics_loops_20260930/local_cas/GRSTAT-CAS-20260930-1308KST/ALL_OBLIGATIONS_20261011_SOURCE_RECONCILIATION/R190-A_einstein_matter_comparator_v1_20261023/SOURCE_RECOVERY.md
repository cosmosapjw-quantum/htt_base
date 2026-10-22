# R190-A source recovery — Einstein–matter comparator problem (PR-190)

Repository HEAD at recovery: `d256ed4669b1ded62fa0db606929af108160ccf6`
(branch `research/htt-open-input-theory-20261018`). Card snapshot
`a30d84c7918b54238a48fa62e2ef482f7e6d36fa` (ancestor of HEAD). Card copied to
`raw/card_R190-A.json` (sha256 `4cb8e2bc8be179be3168002f5cf443bb0e344395124f33628c98efa4e0bea9d3`,
package zip sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`).
All reads were read-only; no git state was changed.

## 1. Card-listed sources (sha256 at HEAD)

| source | sha256 | relevant lines |
|---|---|---|
| `docs/codex_handoff/pr_backlog.yaml` | `5cf688f2…b935` | PR-186 5656–5723, PR-187 5724–~5790, PR-189 5859–5930, PR-190 5931–6003 |
| `docs/PR_DELTAS/pr-190.md` | `28c864d8…f358f463` | whole file: `BLOCKED_INPUT_AND_EXECUTION_SPECIFICATION`, four "exact missing inputs" |
| `docs/codex_handoff/remaining_pr_crosswalk.csv` | `92b7332a…b3496` | line 24 (PR-190 partial remainder), line 6 |
| `docs/codex_handoff/REMAINING_PR_EXECUTION_PLAN_KO.md` | `fdffc914…2924f` | 138–142 |
| `htt/src/common/revival_sharpness_ladder.py` | `84498bac…7caa` | 13 (`STAGES`), 34–39 (no stage without lower stages), 61–75 (global `BLOCKED`) |

`docs/codex_handoff/pr_status.yaml:505-511`: PR-190 `BLOCKED_WITH_RECEIPT`,
`success_dependency_satisfied: false`, scientific status `OPEN`.

## 2. Roadmap anchor and backlog statements (verbatim targets)

- `htt_post_v10_strengthening_plan_20260721/03_POST_V10_STRENGTHENING_PR_ROADMAP_20260721.md`
  (sha256 `869e11f9…a306`) lines 239–267, PR-190 SPEC: "lower/upper endpoint와 모든 interior
  comparator 값이 동일 frame/convention의 Einstein–matter solution class에서 실현된다";
  decisive falsifier line 244 (Gauss/momentum/Jacobi/matter conservation/evolution, sign-corner
  must equal the optimiser's); do-list 246–249 (Bianchi I/V/III/KS exact initial data, local
  development + constraint propagation, connected components); forbidden 251–252 (constraint
  witness is not a cosmological solution; **withdrawn W² endpoint must not be swapped for a
  shear endpoint**); PASS gates 256–260 (e-fold gate at 258) (symbolic constraint residual exactly 0 at each
  endpoint; numerical development with normalized constraint < 1e-10 over **≥ 5 e-fold-equivalent
  interval**; energy conditions/domain/signature; relative gap < 1e-10; 100 interior points or a
  connectedness proof); kill 262–264 (any frame mismatch; singular local development; stopping
  at algebraic/initial-data level).
- Same file 117–121 (PR-186 W² convention), 147–151 (PR-187 frame/type, signed carrier
  S₊³×ℝ, `W_n²`, `W_u²` as separate types, line 155), 209–217 (PR-189 joint feasible set incl.
  "Einstein constraints … as equality/inequality"), 874–875 (no authoritative comparator
  number before PR-186/187).
- `htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md:45-53`
  (T-PHYSICAL-SHARPNESS: "exact initial data + local existence + constraint propagation +
  continuation").
- `htt_post_v10_strengthening_plan_20260721/01_HOSTILE_REFEREE_STEELMAN.md:33-37` (H04: with
  c=(+,−,+,+) the lower endpoint must make W² large and positive components small; v10
  carried a Bianchi-I *shear* corner as the lower endpoint, contradicting the prior withdrawal),
  `:39-43` (H05 product box vs joint).

## 3. Recovered problem (verbatim definitions with citations)

**Comparator.** `SECTORS = (Sigma2, W2, Omega_tilt, Omega_k)`,
`COMPARATOR_SIGNS = (+1,−1,+1,+1)`, `x_C = c·g`
(`htt/obsstat/egs3_graded_comparator.py:48-50`, sha256 `3332c3af…b6c6`; CLAUDE.md §1).
PR-187 signed carrier: positive block {Σ², W², Ω_tilt} ≥ 0, ΔΩ_k ∈ ℝ
(`htt/src/common/frame_typed_algebra.py:27-31,189-205`, sha256 `802d3a90…3286`).

**Registered box and sign corners (open-curvature branch).**
`htt/obsstat/egs3_linearized_realization.py:97-110` (sha256 `91c85e49…05cf5`):
reachable Σ² = 12/100, Ω_tilt = 3/100; null W² ∈ [0, 4/100], Ω_k ∈ [0, 2/100];
"Minimizing x_C uses (W² = 4/100, Ω_k = 0) → 11/100; maximizing x_C uses (W² = 0,
Ω_k = 2/100) → 17/100". `REGISTERED_ENDPOINTS` lower = (12,4,3,0)/100, upper = (12,0,3,2)/100.
Identified interval [11/100, 17/100]: `htt/obsstat/egs3_interior_family.py:89-90`.
Branch discipline (Ω_k ∈ [0,U_k] on the open branch): `htt/obsstat/egs3_identified_set.py:49-51`.

**Declared Einstein–matter solution class (constraint level).**
`htt/obsstat/egs3_nonlinear_realization.py` (sha256 `adf839ec…44795`):
- 22–43: homogeneous Bianchi I (a_i = n_i = 0) for Ω_k = 0 and Bianchi V (class B,
  a_i = (a,0,0), isotropic ³R = −6a² ⇒ Ω_k = a²/H²) for Ω_k > 0; diagonal trace-free shear;
  antipodal tilt pair (±β); Gauss closed by Ω_Λ.
- 33–38, 102–107: exact (0i) momentum constraint `3 a_b σ^{ab} + κ q^a = 0`; for diagonal σ and
  a_i ∥ x only the x-component `a σ_1` survives. 202–206: the coefficient 3 is
  convention-dependent; the load-bearing fact is `a_bσ^{ab} ∝ σ_1`.
- 79–80: per-stream flux `q = (μ+p) sinh β cosh β`, tilt `(1+w) Ω_m sinh²β`.
- 109–111: Σ² = σ_abσ^ab/(6H²) (transverse shear diag(0,s,−s) ⇒ Σ² = s²/(3H²)).
- 136–140: Gauss in normalized form `Ω_m + Ω_Λ + Ω_k + Ω_tilt + Σ² − W² = 1`, Ω_m = 3/10;
  207–208: Gauss closure by Ω_Λ is bookkeeping, not an independent constraint.
- Metric ansatz and congruences: `htt/obsstat/egs3_king_ellis_frame.py:9-17`
  (sha256 `608b4cf9…b236`): `ds² = −dt² + a1² dx² + a2² e^{2sx} dy² + a3² e^{2sx} dz²`, s ∈ {0,1};
  `n^a` = slice normal ∂_t; `u^a` = group-invariant tilted matter congruence. Lines 20–21:
  "Frobenius: omega[n] = 0 exact". Lines 51–54: Frobenius argument for the slice-normal
  comparator congruence untouched by KE-OBS.
- **Comparator congruence:** `docs/research_program/egs3/CLAIM_LEDGER.yaml:280` — "the
  comparator W^2 stays defined on the slice normal, re-attribution to the matter congruence is a
  registered interpretive question NOT a claim".

**Withdrawn W² endpoint.** `docs/research_program/egs3/tickets/t3_king_ellis.yaml`
(sha256 `15adeac4…1e0`) 82–91: "LOWER-ENDPOINT W^2 WITHDRAWN … comparator W² is defined on the
slice normal n^a; a Bianchi-I homogeneous-slice normal is hypersurface-orthogonal, so
Frobenius forces ω_ab[n] = 0"; 151–165: withdrawal upgraded to dynamical within the
group-invariant perfect-fluid class; "no W² = 4/100 value is asserted".
`docs/research_program/THEOREM_REGISTRY.yaml` (sha256 `266374ab…f315`) 491–510 (T3-full
level 2 genuine only for the upper endpoint), 511–525 (T3-int level 1; segment I inherits the
Frobenius gap), 777–805 (KE-DYN, level 3 within the registered ansatz class only).

**Sharpness taxonomy.** `THEOREM_REGISTRY.yaml:15-18` (1 algebraic-box, 2 constraint-surface
endpoint attainability, 3 dynamical); `revival_sharpness_ladder.py:13` four stages
`algebraic, constraint, local, global`, 34–39 (lower stages required), 61–75 (global
`BLOCKED`: native solver).

**PR history (read-only).** Commit `bae6ac2df15c95ee1e71a3e49b859c0added192d`
("PR-190: Record typed comparator attainability refutation", 2026-08-03) is **NOT an ancestor
of HEAD** (it lives on other branches). Read via `git show`:
`docs/research_program/strengthening/pr190_spec.yaml:49-51` (normalized invariants
`Sigma2 = (3/2)‖σ/Θ‖_F²`, `W2 = 3‖ω/Θ‖²`, Θ = 3H), 58–61 (congruence rule: hypersurface-normal
⇒ ω[n] = 0; nonzero W² there is a contradiction, not a free rotational mode), 63–92
(targets incl. interior challenge x_C = 12/100 with W² = 3/100), 95–103 (four separate levels);
`…/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` (sets the spatial derivative to 0
**by definition**; this task replaces that with a derived Frobenius lemma). The ancestor
history (`227098b47`, `a30d84c79`) records only the input blocker.

## 4. PR-186 / PR-187 convention-authority cross-check (acceptance item)

| item | authority | consumers checked | result |
|---|---|---|---|
| W² normalization | `htt/src/common/w2_convention.py:6,10` (sha256 `39b15209…bcac`): W² = ω_abω^ab/(6H²) = ω_aω^a/(3H²); Θ=3H, √(ω_abω^ab)/Θ ≤ B ⇒ W² ≤ 3B²/2 | nonlinear realization Gauss (−W²) 139; unmerged spec `W2 = 3‖ω/Θ‖²` | consistent; Lean C1–C5 prove the identities universally (not by `native_decide` on witnesses as in `formal_pr186/Pr186W2/Basic.lean`) |
| Σ² normalization | same convention family; `egs3_nonlinear_realization.py:109-111` σ_abσ^ab/(6H²); `egs3_linearized_realization.py:116-128` | unmerged spec `(3/2)‖σ/Θ‖_F²` | consistent (Lean C6) |
| frame of W² | PR-187 roadmap 155 (`W_n²`, `W_u²` separate types); CLAIM_LEDGER:280 (comparator W² on slice normal) | KE-DYN rotating development lives in the u-frame (THEOREM_REGISTRY 777–805) | u-frame vorticity cannot be substituted (frame mismatch kill); Lean types the candidate codomain as n-frame |
| pair density | PR-187 `frame_typed_algebra.py:216-231` (`fixed_total_density=True` default: pair = single; per-stream: ×2) | `egs3_nonlinear_realization.py:80-88` and `egs3_linearized_realization.py:22-24` use the **per-stream additive** form `2(1+w)Ω_m sinh²β` while the Gauss bookkeeping (139) counts Ω_m once | **label mismatch recorded**: both labels describe the same n-frame excess energy only if Ω_m is per-stream in the tilt formula and total (=2×per-stream) in Gauss. Lean C8–C10 derive the stream stress-energy and prove which label pairs are consistent and that the mixed reading double-counts. The comparator *values* are unaffected (Ω_tilt is a target); the rapidity β the candidate map assigns depends on the declared label. |
| sign-corner | `egs3_linearized_realization.py:97-100`, H04 | interior family 17–31 | lower corner = (Σ_lo, W_hi, T_lo, K_lo), unique argmin (Lean A5) |

Existing formal assets: `formal_pr186/Pr186W2/Basic.lean`, `formal_pr187/Pr187Frame/Basic.lean`,
`formal_pr189/Pr189Joint/Basic.lean` (core Lean, all closed by `native_decide`). They are **not
imported**: `native_decide` is forbidden in this task's axiom policy and they contain only
finite witness checks. No accepted reviewed Lean module from earlier reconciliation units
matches this class (G06-A/B are TOV/P(X) static spherically symmetric; G05-B is a germ
construction), so `raw/imports` contains only this task's own olean.

## 5. What remains unrecovered (exact items)

1. **Evolution system in closed form for the declared class** (needed for the local and global
   predicates). Searched: `htt/obsstat/egs3_king_ellis_dynamics.py` (KE-DYN; derives a 7×7
   first-principles system symbolically at runtime, numerical development only),
   `htt/obsstat/egs3_bianchi_v_dynamics.py`, `egs3_bianchi_v_constraint.py:24-28` ("NOT an
   integration of the Hewitt–Wainwright dynamical system"), THEOREM_REGISTRY 777–805. The
   system exists only as SymPy code generated at run time, not as a stated equation set.
   Status: **open proof obligation** (transcribe the system + prove constraint propagation +
   Picard–Lindelöf), not an external blocker. Lean defines the predicates generically over a
   typed `EvolSys`.
2. **Registered evolution interval.** Recovered: "≥ 5 e-fold-equivalent interval" (roadmap 258).
   The e-fold functional of a concrete `EvolSys` is part of item 1.
3. **Named external blocker (genuine owner choice):** whether the comparator W² is re-attributed
   from the slice normal n to the matter congruence u (CLAIM_LEDGER:280, t3_king_ellis.yaml
   160–165 "registered interpretive question, not a claim"). Under the current source
   definition (slice normal) the lower endpoint and every x_C < 15/100 are refuted at the
   constraint level (Lean). A re-attribution would be a new definition, i.e. a different
   PR-190 statement; it cannot be chosen by the author. Unlock: owner-registered definition
   change with frame bridge (PR-187 registry) and a new frozen target.
4. Λ sign: the source closes Gauss with Ω_Λ as bookkeeping (`egs3_nonlinear_realization.py:207-208`)
   and states no sign condition; the Lean domain therefore does not constrain Λ. On the
   registered box the candidate has Ω_Λ ∈ [53/100, 55/100] > 0 (proved).
