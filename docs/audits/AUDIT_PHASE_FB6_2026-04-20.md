# AUDIT_PHASE_FB6_2026-04-20

**Banner**: Phase FB-6 actual-work closeout. The 22-configuration
regression harness is now real, the five named cross-type limits are
measured against declared tolerances, the CAMB / literature oracle rows
are active, topic 18 is rendered, and the manuscript + handoff surfaces
are rotated to the next phase.

## Baseline and verification

- Required reading completed against the local FB-6 scope:
  - `docs/audits/AUDIT_PHASE_FB_META6_2026-04-20.md`
  - `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-6`
  - `htt/bass/hierarchy/test_fb36_tilted_regression.py`
  - `htt/bass/integration/test_lowell_bianchi.py`
- The phase deliverable remains the test harness itself:
  - `htt/bass/integration/test_full_bianchi_coverage.py`
  - no separate production module was introduced for FB-6.
- New stable fixture inputs were added under:
  - `tests/fixtures/fb6/`
- Targeted verification commands:
  - `cd htt && ../venv/bin/python -m pytest bass/integration/test_full_bianchi_coverage.py -q`
    → `48 passed`
  - `cd htt && ../venv/bin/python -m pytest bass/integration/test_full_bianchi_coverage.py bass/integration/test_lowell_bianchi.py -q`
    → `72 passed, 1 skipped, 2 warnings`
  - `venv/bin/python scripts/make_physics_gallery.py --only 18_22_config_regression`
    → rendered four PNGs under `figures/physics_gallery/18_22_config_regression/`
- Expected warnings:
  - the retained recombination-table `z`-coverage runtime warning from
    `bass/species/registry.py` remains present and unchanged.

## §FB-6.1 — full 22-row type × tilt matrix

- **Status**: implemented and green.
- **Code surface**:
  - explicit `FB61_CONFIGURATION_CASES` matrix in
    `htt/bass/integration/test_full_bianchi_coverage.py`
  - cached runtime helpers built on the shipping stack:
    `solve_bianchi_background`, `build_tetrad_state`,
    `LowellBianchiIntegrator.run()`, and `hierarchy_rhs_photon(...)`
- **Per-row invariants**:
  - finite background outputs
  - finite hierarchy RHS at three sampled `η` slices
  - PSTF round-trip preservation on `ℓ ∈ {0, 2, L_max}`
  - finite low-`ℓ` `D_\ell^{TT}` proxy on `ℓ = 2,\dots,30`
- **Anchor rule**:
  - every orthogonal row re-runs the same RHS probe with and without
    explicit tilt vectors and asserts exact `np.array_equal(...)`
    byte identity at `β = 0`.
- **Outcome**:
  - all 22 explicit rows pass.
  - the phase keeps the matrix flat and literal; no generated
    `ALL_BIANCHI_TYPES × {"orthogonal","tilted"}` helper replaced the
    reviewed audit surface.

## §FB-6.2 — named continuity limits

- **Status**: implemented and green.
- **Code surface**:
  - `FB62_CONTINUITY_LIMIT_CASES`
  - `_FB62_LIMIT_CONFIG`
  - `test_fb62_cross_type_continuity_limits(...)`
- **Measured maximum relative trajectory mismatches**:
  - VII_h → VII_0 as `h → 0+`: `1.836e-07` vs `rtol = 1.0e-06`
  - VI_h → III as `h → -1`: `3.129e-04` vs `rtol = 5.0e-04`
  - VII_0 → I as `n → 0`: `0.0` vs `rtol = 1.0e-08`
  - V → I as `a → 0`: `0.0` vs `rtol = 1.0e-08`
  - IX → isotropic/BKL branch as `n → 0`: `1.669e-09` vs `rtol = 1.0e-06`
- **Implementation note**:
  - the final comparison uses a global-trajectory scale
    `max_abs_diff / max(|ref|)` rather than a pointwise `allclose`
    gate, which avoids false failures at exact-zero reference points
    while still enforcing the declared phase tolerances.

## §FB-6.3 — CAMB and literature oracles

- **Status**: implemented and green.
- **Channel A — CAMB fixture header check**:
  - `htt/bass/integration/test_lowell_bianchi.py` already consumes the
    same `data/camb_ref_planck2018.npz` fixture as the LB-6 oracle path.
  - the active FB-6 harness confirms:
    - `camb_version = 1.6.6`
    - `lensed = False`
    - `omk = 0.0`
    - `len(ell) = 29` covering `ℓ = 2,\dots,30`
- **CAMB-limit row metrics**:
  - Type I: `0.0`
  - Type V: `2.0e-06`
  - Type VII_0: `4.0e-06`
  - Type VII_h → 0: `4.0e-02`
  - Type IX isotropic limit: `6.0e-06`
  - all five remain within the phase gate `rtol ≤ 5%`.
- **Channel B — 2009 literature reference verification**:
  - direct arXiv verification on 2026-04-20 confirms that
    `arXiv:0901.2122` is:
    - **Title**: *Rogues' gallery: the full freedom of the Bianchi CMB anomalies*
    - **Author**: Andrew Pontzen
    - **Submission history**: submitted 2009-01-15, revised 2009-05-11
    - **Comments**: “7 pages, 3 figures”
  - this corrects the prompt's imprecise “Pontzen-Challinor 2009”
    wording: the 2009 figure-bearing paper is single-author Pontzen,
    while the earlier joint paper is `PontzenChallinor2007`
    (`arXiv:0706.2075`).
  - because the arXiv metadata states “3 figures”, the phase records the
    usable figure/section surface as **Figures 1 and 3 plus §IV**, not
    the prompt's “Fig. 4 + §IV”.
- **Literature-template metrics**:
  - VII_h vector temperature grid: correlation `0.996996`, mean `L1 = 0.016332`
  - VII_h regular-mode grid: correlation `0.997861`, mean `L1 = 0.013713`
  - IX closed quadrupole grid: correlation `0.988245`, mean `L1 = 0.037575`
  - VII_h off-diagonal `C_TT`: correlation `0.989145`, mean `L1 = 0.033467`
  - IX off-diagonal `C_TT`: correlation `0.996425`, mean `L1 = 0.025494`
  - all five satisfy the implemented qualitative gate
    `corr >= 0.97` and `mean |Δ| <= 0.12`.

## Gallery, manuscript, and bibliography

- **Gallery**:
  - added topic `18_22_config_regression`
  - rendered:
    - `plot_18_01_22_config_sigma2_decay.png`
    - `plot_18_02_cross_type_limits_grid.png`
    - `plot_18_03_Dl_TT_11_types_vs_camb.png`
    - `plot_18_04_pontzen_challinor_shape_match.png`
  - manual visual sanity check completed on representative panels:
    `plot_18_01`, `plot_18_03`, and `plot_18_04`
    (titles, legends, axis labels, and panel layouts intact).
- **Manuscript**:
  - `docs/manuscript/ch07_results.tex`
    - new section:
      `Full Bianchi coverage: 22-configuration regression`
    - includes FB-6.1 / FB-6.2 / FB-6.3 subsections, four figure
      inclusions, and three results tables.
  - `docs/manuscript/ch08_robustness.tex`
    - added the cross-type-limits robustness paragraph linking to FB-6.2.
- **Bibliography**:
  - added entries:
    - `WainwrightEllis1997`
    - `Pontzen2009`
    - `Planck2018VI`

## Phase close

- **Implemented locally**:
  - 22-row full-coverage harness
  - 5 named continuity-limit checks
  - 10 active CAMB / literature oracle rows
  - topic-18 gallery
  - Chapter-7 / Chapter-8 FB-6 results write-up
  - FB-6 audit, development-log append, and handoff rotation
- **Phase-close status**:
  - FB-6 is closed on this branch at milestone M5.
  - next-session handoff is rotated to
    `FB-7 actual work — paste the FB-7 prompt`.
- **Planned close commit**:
  - `FB-6: Phase FB-6 complete (M5 achieved — 22 configurations green)`
