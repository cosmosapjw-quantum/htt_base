# AUDIT_PHASE_FB7_2026-04-20

**Banner**: actual-work closeout for FB-7 spectrum/HTT/cosmological-frame likelihood

## Phase summary

- Scope completed:
  - `htt/bass/spectrum/lowell_los.py` (FB-7.1)
  - `htt/bass/spectrum/off_diagonal_covariance.py` (FB-7.2)
  - `htt/bass/likelihood/htt_decomposition.py` (FB-7.3)
  - `htt/bass/likelihood/cosmological_frame.py` (FB-7.4)
  - `htt/bass/likelihood/planck2018_flrw_match.py` (FB-7.5)
- New gallery topic rendered:
  `figures/physics_gallery/19_htt_likelihood/`
- Manuscript updated:
  `docs/manuscript/ch06_pipeline.tex`,
  `docs/manuscript/ch07_results.tex`,
  `docs/manuscript/references.bib`
- Rotation updated:
  `docs/lowell_bianchi/extended_coverage/DEVELOPMENT_LOG_FB3_TO_FB7.md`,
  `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md`
- Successor log check:
  `docs/lowell_bianchi/extended_coverage/DEVELOPMENT_LOG_FB8_ONWARD.md`
  already existed, so no new header plant was needed.

## Required-reading close

- Read and used:
  - `docs/audits/AUDIT_PHASE_FB_META7_2026-04-20.md`
  - `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7`
  - `htt/docs/lowell_bianchi_solver_reference_PR_WBS.md`
  - `htt/bass/los/` scaffolding
  - `docs/manuscript/ch06_pipeline.tex`
  - `docs/manuscript/ch07_results.tex`
- Prompt-path gap remains explicit:
  `docs/lowell_bianchi/lowell_bianchi_solver_reference.md` is absent in
  this worktree. The local internal stand-in remained
  `htt/docs/lowell_bianchi_solver_reference_PR_WBS.md`; no invented
  Lowell locator was cited as if it existed on disk.

## Verification ledger

| Check | Command | Result |
|---|---|---|
| Syntax | `venv/bin/python -m py_compile scripts/make_physics_gallery.py` | PASS |
| FB-7 targeted tests | `venv/bin/python -m pytest htt/bass/spectrum/test_fb71_lowell_los_skeleton.py htt/bass/spectrum/test_fb72_off_diagonal_covariance_skeleton.py htt/bass/likelihood/test_fb73_htt_decomposition_skeleton.py htt/bass/likelihood/test_fb74_cosmological_frame_skeleton.py htt/bass/likelihood/test_fb75_planck2018_flrw_match_skeleton.py -q` | `133 passed in 1.99s` |
| Topic-19 render | `venv/bin/python scripts/make_physics_gallery.py --only 19_htt_likelihood` | PASS; 5/5 PNGs rendered |
| Full regression | `cd htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` | `3871 passed, 21 skipped, 26 warnings in 180.02s` |

Warnings at phase close remained the pre-existing recombination-range
runtime warnings and Laguerre-basis overflow warnings already present in
the baseline suite; no new FB-7-specific warning signature appeared.

## §FB-7.1

### FB-7.1 — line-of-sight matrix propagator

- **Channel A (implementation)**:
  `build_lowell_line_of_sight_propagator(...)` now ships a real all-type
  LOS transfer bundle with
  `transfer_T/E/B`, `propagator_matrix`, `mode_coupling_matrix`,
  preferred-axis metadata, and the explicit Limber stationary-phase
  diagnostics.
- **Channel B (source / carry closure)**:
  the original carry in
  `docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md §10`
  item 2 reads:
  “**Limber `η_sp` sign**. The line-of-sight Limber approximation path
  uses an η sign convention opposite to the integrator's. Reserved for
  FB-7 (line-of-sight propagator).”
  This is now closed explicitly by
  `eta_sp = eta_0 - (ell + 1/2)/k`, with the old sign retained only as
  `limber_eta_sp_sign="legacy_negative"` for audit comparison.
- **Channel C (verification)**:
  the FB-7.1 tests pin the corrected sign, direct-source visibility
  gating, Type-I zero-B behavior, and stable bundle shapes; the new
  gallery heatmap is
  `plot_19_01_los_propagator_heatmap.png`.

## §FB-7.2

### FB-7.2 — diagonal plus off-diagonal covariance

- **Channel A (implementation)**:
  `assemble_bianchi_spectrum_covariance(...)` now produces
  `C_ell^{TT,EE,TE,BB}`, `D_ell`, per-mode diagonals, off-diagonal
  blocks, and optional dense / sparse derived views from the same block
  data.
- **Channel B (alternatives table)**:

| Strategy | Status in FB-7.2 | Rationale |
|---|---|---|
| `m_decoupled_blocks` | **Picked / default** | Matches the shipped `m ∈ {0,\pm2}` LOS structure and the META-7 decision |
| `dense_matrix` | Derived view only | Available for consumers that need an explicit dense covariance, but not the default storage |
| `wigner_d_sparse` | Derived view only | Available as a sparse export without changing the underlying audited construction |

- **Channel C (verification)**:
  FB-7.2 tests verify the Type-I off-diagonal covariance vanishes
  identically, that the dense and sparse exports agree with the block
  representation, and that the Bianchi-IX off-diagonal slice is finite
  and symmetric. The gallery artifact is
  `plot_19_02_offdiag_covariance_IX.png`.

## §FB-7.3

### FB-7.3 — HTT decomposition and P0 triad

- **Channel A (implementation)**:
  `build_htt_decomposition(...)` now keeps the P0 triad explicit:
  prior alignment, tangency response, and β-gate status remain visible
  at the decomposition boundary. The return bundle exposes
  `resolved_axis`, `dominant_axis`, `tangent_axis`, `triad_status`,
  `effective_amplitude`, and the directional score grid consumed by the
  likelihood.
- **Channel B (derivation cross-check)**:
  the prompt-supplied Lowell `§14.2` file is still absent locally, so
  the internal Lowell derivation cannot be cited verbatim. The actual
  implementation therefore kept that gap explicit and cross-checked the
  visible triad logic against the local internal solver reference
  (`htt/docs/lowell_bianchi_solver_reference_PR_WBS.md`) plus the
  Bianchi-polarization bookkeeping in Pontzen-Challinor 2007.
- **Channel C (verification)**:
  FB-7.3 tests pin the prior-lock, tangency-fallback, β-gate-blocked,
  and tangent-realigned branches, and the gallery artifact
  `plot_19_03_htt_p0_triad.png` shows the three-panel resolution
  directly.

## §FB-7.4

### FB-7.4 — direction-dependent cosmological-frame likelihood

- **Channel A (implementation)**:
  `CosmologicalFrameLikelihood` now evaluates a direction-dependent
  `log_prob(...)` and a grid-valued `directional_surface(...)` using the
  FB-7.3 decomposition plus spectra-side residual terms.
- **Channel B (scope pin)**:

| Row | Status | Evidence |
|---|---|---|
| cosmological-frame scope pin | PASS | Module docstring states “Bianchi rest frame only”; observer-motion keys are rejected eagerly; every FB-7.4 test docstring repeats that observer-motion marginalisation is deferred to `bass.likelihood.observer_frame_adapter` in FB-8 |

- **Channel C (verification)**:
  FB-7.4 tests verify rejection of observer-frame parameters, axis
  parsing from both vectors and angular coordinates, tier-dependent
  masking, and directional-surface output shape. The gallery artifact is
  `plot_19_04_direction_likelihood_contours.png`.

## §FB-7.5

### FB-7.5 — Planck-2018 FLRW-limit match

- **Channel A (fixture provenance)**:
  `data/camb_ref_planck2018.npz` was used as the sole numeric oracle.
  The implemented validator reports the local fixture metadata
  `camb_version = 1.6.6`, `lensed = False`, and `omk = 0.0`, consistent
  with the Planck-2018 V / VI provenance split carried from META-7.
- **Channel B (implementation + evidence outputs)**:
  `validate_planck2018_flrw_limit_match(...)` now composes the FB-7.3
  HTT decomposition and the FB-7.4 cosmological-frame likelihood into a
  single `ln_B` scalar per Bianchi type versus FLRW. The explicit
  FLRW-limit gate is satisfied for Types I, V, and VII_0:
  `|ln_B| < 0.1` and `|ln_B| <= 2 * mc_error`.
  The six no-limit rows
  `{II, III, IV, VI_0, VI_h, VIII}` are marked
  `NO_FLRW_LIMIT_EXPLICIT`; no row is silently dropped.
- **Channel C (verification)**:
  FB-7.5 tests cover missing-fixture failure, all 11 returned rows,
  Planck arXiv-id preservation, row-lookup integrity, explicit no-limit
  labeling, and the FLRW-limit tolerance for
  `{I, V, VII_0}`. The gallery artifact is
  `plot_19_05_lnB_11types_vs_FLRW.png`.

## Manuscript + gallery close

- `ch06_pipeline.tex` gained:
  - `\section{Line-of-sight propagator}`
  - `\section{Direction-dependent likelihood}`
- `ch07_results.tex` gained:
  - `\section{Bayesian evidence across the 11-type Bianchi classification}`
  - 11-row FB-7.5 summary table
  - Topic-19 bar-chart figure inclusion
- `references.bib` gained:
  - `SeljakZaldarriaga1996`
  - `LewisChallinor2006`
  - `Planck2018V`
- `figures/physics_gallery/README.md` was refreshed to include the new
  topic and to reconcile the stale topic inventory with the current
  rendered set.

## Validation checklist

- [x] 5 skeletons implemented.
- [x] Phase-0 Limber-sign carry closed in FB-7.1.
- [x] FB-7.4 cosmological-frame scope pin in audit + code docstring.
- [x] FB-7.5 FLRW-limit `|ln_B| < 0.1` for I / V / VII_0.
- [x] Gallery topic 19 rendered.
- [x] ch06 + ch07 sections added; bibliography updated.
- [x] Audit + dev-log + NEXT_SESSION rotated.

## Phase close

FB-7 is closed locally at the actual-work boundary with the spectrum,
HTT, cosmological-frame likelihood, and Planck-2018 FLRW-limit matcher
implemented and verified.

- Full-suite state at close:
  `3871 passed, 21 skipped`
- Observer-frame composition remains the intentional FB-8 gap.
- No silent fallback remains on the FB-7.5 row ledger: every row either
  passes directly or is marked `NO_FLRW_LIMIT_EXPLICIT`.
