# R195-A source recovery

Written on resume (2026-10-23). A previous run wrote `FROZEN_TARGETS.md` and
`raw/run_compile.py` on 2026-10-14 and was then cut off by a rate limit before
writing this file, any compile receipt, or any Lean source. All citations below
were re-read on resume from HEAD `a8fd176305fb475947a46f9dacb651805d323741`
(read-only; no state-changing git was run).

## Card

`HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (sha256
`2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`), member
`HTT_ALL_OBLIGATIONS_20261011/tasks/R195-A.json`: scope "B_W=v0+finite-k residual를
window·spectrum·gauge/frame 및 remainder와 함께 증명한다"; reuse "PR222 multi-window
stochastic bridge mechanics; 직대입 B/c는 재사용하지 않는다"; acceptance "finite-k
residual가 모델에 실제 포함", "correlated windows의 cross terms 보존"; pitfalls "B/c를
바로 homogeneous β로 대입 금지", "bridge failure를 Ω_tilt=0로 해석하지 않음";
consumed exports PR-187 (frame/velocity conventions) and PR-222 (multi-window law).

## Recovered definitions (file:line)

| item | source (file:line) | recovered content | Lean carrier |
|---|---|---|---|
| windowed bulk-flow decomposition target | `docs/codex_handoff/pr_backlog.yaml:6298-6352` (sha256 listed below), target 6316-6317 | "windowed bulk-flow vector B_W는 homogeneous mode v_0와 finite-k residual의 합이며 Ω_tilt(v_0)로의 bridge는 window, power spectrum, gauge/frame, remainder를 포함한다" | T1/T1n/T4 |
| kill / forbidden | `pr_backlog.yaml:6333` (kill: finite-k residual 미모델링), `6345-6346` | no B/c→β substitution; bridge failure ≠ Ω_tilt=0 | T7 negative controls |
| roadmap spec + actions | `htt_post_v10_strengthening_plan_20260721/03_POST_V10_STRENGTHENING_PR_ROADMAP_20260721.md:392-419` (sha256 listed below) | "velocity field를 k=0/super-sample/finite-k modes로 분해", "survey window functional과 gauge-invariant large-scale velocity 정의를 결속", "finite-window remainder" | T1, T6, T5 |
| audit criticism H07 | `htt_post_v10_strengthening_plan_20260721/01_HOSTILE_REFEREE_STEELMAN.md:51-55` | finite-window bulk flow is a function of long-wavelength realization and survey window; direct v/c→β→Ω_tilt conflates local mode, observer boost, homogeneous tilt | T7 nonidentification |
| theorem candidate | `htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md:105-113` | "B_W=v0+δ_W에서 homogeneous mode identified set과 finite-window remainder bound"; route "Gaussian random fields/window operators" | T1, T5 |
| PR-222 multi-window mechanics | `pr_backlog.yaml:8209-8233`; `htt/src/common/revival_bulk_bridge.py:1-43` (sha256 listed below); `docs/PR_DELTAS/pr-222.md:1-15` | forward operator rows = windows, cols = homogeneous components (`W` at :14), correlated covariance `C = diag + off*ones` (:18, :30) i.e. cross-window terms kept; GLS through the operator; "not a point substitution" (:3-4) | T4 (rows = window m with projection `L m`, full cross-covariance for every pair) |
| PR-187 frame tags | `htt/src/common/frame_typed_algebra.py:28` `FRAMES = ("n","u","obs")`, `:53-54` no default frame, `:142-143` registered bridges obs→u, u→n; `docs/PR_DELTAS/pr-187.md` | frame is a type index; cross-frame arithmetic only through registered bridges | `Frame`, `Rem fr κ`, `ObsModel fr` |
| source-declared estimator (CF4) | `git show a40e5382a:scripts/cf4_bulkflow_lcdm_variance.py` (REV-R195 commit; blob sha256 `b4a2d2eb576cf1ac366d725c023994abd0c8313fca21bd0fac8114cec20c1e2a`) lines 24-27 | `B = A^{-1} b`, `A = Σ_i w_i n_i n_iᵀ`, `b = Σ_i w_i u_i n_i` | amendment A1 (`cf4_window_normalized`, `cf4_estimator_decomposition`) |
| estimator covariance | same blob lines 29-31 | `Cov_CV(B) = A^{-1} M A^{-1}`, `M_ij = Σ_mn w_m w_n n_{m,i} n_{n,j} <v_m v_n>` | T2 (configuration-space law, no stationarity needed) |
| velocity spectrum (source-declared) | same blob lines 33-36 | `<v_m v_n> = (H0 f)^2 ∫ d^3k/(2π)^3 [P(k)/k^2] (n_m·k̂)(n_n·k̂) e^{ik·(x_m-x_n)}` | instance of the matrix spectral density `p i j` in amendment A2 (not derived) |
| units / prefactor / 1-D dispersion | same blob lines 44-50; `htt/obsstat/velocity_power.py:9-13` (sha256 listed below) | Mpc/h, prefactor (100 f)^2, f = Ω_m^0.55; σ_v,1d^2 = (100 f)^2/(6π^2)∫P dk | not claimed (numerics) |
| Gorski radial/transverse closed form | `htt/obsstat/velocity_power.py:74-105`; `htt/obsstat/cf4_velocity_estimators.py:110-134` (sha256 listed below) | Ψ_∥, Ψ_⊥ correlation used for C_ab | not claimed |
| WLS bulk-flow estimator (current code) | `htt/src/common/bulkflow_estimator.py:6-21` (sha256 listed below) | `V̂ = A^{-1} b`, `A = Σ w_i n̂_i n̂_iᵀ`, `b = Σ w_i u_i n̂_i`; weight factors native·selection/σ² | A1 |
| frame of the raw observable | `scripts/build_external_audit_report_v10.py:1547` | `v = V_3k − H0 D`, CMB frame | `Frame` tag only |
| crosswalk / plan | `docs/codex_handoff/remaining_pr_crosswalk.csv:29`; `docs/codex_handoff/REMAINING_PR_EXECUTION_PLAN_KO.md:137-141` | "general finite-volume bulk-flow to homogeneous-tilt bridge theorem", "no point substitution or independent Gaussian fill"; finite examples are not general closure | T7 is labelled witness, not closure |

Full sha256 of the cited files at HEAD:

```
5cf688f233967f762778fa9d6636850c212cee16fb848a17eb8006fb63f3b935  docs/codex_handoff/pr_backlog.yaml
92b7332ae1338361b95853ce79bb664e9d9dbe4ce1385844de2420d495a3b496  docs/codex_handoff/remaining_pr_crosswalk.csv
fdffc914abfea93fc4158af3ed1364fa84772a0e0c0266346a5e9423fec2924f  docs/codex_handoff/REMAINING_PR_EXECUTION_PLAN_KO.md
869e11f94007a9aea5f68c65e42f73850d9b78c815421289c2b0907abe79a306  htt_post_v10_strengthening_plan_20260721/03_POST_V10_STRENGTHENING_PR_ROADMAP_20260721.md
c0ca15f080da4c04212543af2f4f464ceb3a59b303adfc68c7bad761966680e7  htt_post_v10_strengthening_plan_20260721/01_HOSTILE_REFEREE_STEELMAN.md
0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3  htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md
a0c6735417218150d57107ccaa27de3004b575350a9a7703e59b7f71e367171d  htt/src/common/revival_bulk_bridge.py
392b01380e26e63fc09f15c5713749e6705ce654bcfd55e334b8fb9b1b4752c8  docs/PR_DELTAS/pr-222.md
5d6aba83b351a49a5461fab4f500e1abbf2deba4077d47a4ed95276050f4c450  docs/PR_DELTAS/pr-187.md
802d3a9054dedc0a38bd28ec345dddc67c942f9ff9dec4370ebaf5d092aa3286  htt/src/common/frame_typed_algebra.py
db80eee98bae1cb05b5b135c01db738b3c6c44427690a86589f7013224f3a976  htt/src/common/bulkflow_estimator.py
e085286b696bd39be30ac4cf3be940dbced0db92080f237cbf5b39d24c287108  htt/obsstat/velocity_power.py
0c70dc8c9872d4be12c6b5df2cd5e884bdf9d64a26ac4d7f9d0eb015a092edd6  htt/obsstat/cf4_velocity_estimators.py
b4a2d2eb576cf1ac366d725c023994abd0c8313fca21bd0fac8114cec20c1e2a  git show a40e5382a:scripts/cf4_bulkflow_lcdm_variance.py
fcfd1208db27931d5ea0a3ed968c1a1bccd91b7e4598533b95512b4cda6ec00a  scripts/cf4_bulkflow_lcdm_variance.py (HEAD: PR-120 quarantine stub)
2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f  HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip
```

## Items not recoverable as definitions (recorded, not invented)

- **Gauge-invariant large-scale velocity definition.** Roadmap :398 asks to bind
  the window functional to a "gauge-invariant large-scale velocity"; no source in
  the repo defines it (searched `docs/research_program/**`, `htt/src/common`,
  `htt/obsstat`, `scripts/`, PR-187 delta). Only the frame tag (CMB frame,
  report v10 :1547; tags n/u/obs, frame_typed_algebra.py:28) is source-declared.
  Lean therefore carries the frame as a type index and claims no gauge
  invariance. Unlock: a source-declared gauge-invariant velocity definition.
- **Mapping v0 → Ω_tilt / β.** Owned by R194-A/B (card optional_reuse); not used.
- **Bochner's theorem.** The source asserts the spectral representation from
  P(k); existence of a spectral density is taken as an explicit hypothesis `hK`.
- **Selection / calibration remainder magnitudes.** No source model; only their
  typed additive placement is formalized.

## Imports

No earlier unit's Lean source is imported: the sibling units
(R191-A, R192-A, s02_*) formalize unrelated objects, and PR-222's Lean axis is a
rank/determinant fact for a fixed 4x3 matrix that the general theorems here do not
consume. `raw/imports/` holds only this module's own `.olean`.
