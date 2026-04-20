# AUDIT_PHASE_FB9_2026-04-20

**Banner**: actual-work closeout for FB-9 massive-neutrino species

## Phase summary

- Scope completed:
  - `htt/bass/species/massive_neutrino/phase_space.py` (FB-9.1)
  - `htt/bass/species/massive_neutrino/background.py` (FB-9.2)
  - `htt/bass/species/registry.py` (FB-9.3)
  - `htt/bass/hierarchy/hierarchy_rhs.py` (FB-9.4)
  - `htt/bass/species/test_tilted_massive_neutrino_compose.py` (FB-9.5 harness)
  - `scripts/generate_class_massive_neutrino_fixtures.py`,
    `scripts/make_physics_gallery.py`, docs/manuscript/gallery updates
    (FB-9.6)
- New frozen-oracle fixtures shipped:
  `data/class_massive_neutrino_fixtures/{0.06,0.12,0.24}.npz`
- New gallery topic rendered:
  `figures/physics_gallery/15_massive_neutrino/`
- Manuscript updated:
  `docs/manuscript/ch11_error_hierarchy.tex`,
  `docs/manuscript/ch08_robustness.tex`,
  `docs/manuscript/ch01_introduction.tex`,
  `docs/manuscript/references.bib`
- Species spec updated:
  `docs/lowell_bianchi/01_species_background_spec.md`
- Rotation updated:
  `docs/lowell_bianchi/extended_coverage/DEVELOPMENT_LOG_FB8_ONWARD.md`,
  `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`,
  `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md`

## Required-reading close

- Read and used:
  - `docs/audits/AUDIT_PHASE_FB_META9_2026-04-20.md`
  - `docs/lowell_bianchi/extended_coverage/FB9_MASSIVE_NEUTRINO_SDD.md`
  - `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`
  - `docs/lowell_bianchi/01_species_background_spec.md`
  - `htt/bass/species/base.py`
  - `htt/bass/species/neutrino.py`
  - `htt/bass/species/registry.py`
  - `docs/manuscript/ch08_robustness.tex`
  - `docs/manuscript/ch11_error_hierarchy.tex`
- Scope guard preserved:
  `SpeciesLabel.NEUTRINO` remains the only neutrino enum label, the
  degenerate-mass approximation is the only shipped positive-mass model,
  and the `Sigma_mnu = 0` production path stays on the original LB-1
  `NeutrinoBackground`.

## Verification ledger

| Check | Command | Result |
|---|---|---|
| Syntax | `venv/bin/python -m py_compile scripts/generate_class_massive_neutrino_fixtures.py scripts/make_physics_gallery.py` | PASS |
| CLASS fixture generation | `venv/bin/python scripts/generate_class_massive_neutrino_fixtures.py` | PASS; 3/3 NPZ oracles rendered with provenance fields |
| Topic-15 render | `venv/bin/python scripts/make_physics_gallery.py --only 15_massive_neutrino` | PASS; 4/4 PNGs rendered |
| FB-9 targeted tests | `cd htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/species/test_fb91_phase_space_grid_skeleton.py bass/species/test_fb92_massive_neutrino_background_skeleton.py bass/species/test_fb93_registry_massive_neutrino_skeleton.py bass/hierarchy/test_fb94_massive_neutrino_hierarchy_skeleton.py bass/species/test_tilted_massive_neutrino_compose.py bass/species/test_fb96_docs_gallery_skeleton.py -q` | `165 passed, 1 warning in 1.83s` |
| Full regression | `cd htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` | `4269 passed, 8 skipped, 2 warnings in 161.26s` |

The two remaining warnings are the known recombination-table support-gap
warnings and are unchanged in kind from the pre-FB-9 baseline.

## §FB-9.1

### FB-9.1 — `phase_space_grid` and determinism

- **LB-1 anchor clause**:
  `Sigma_mnu = 0` does not route through the new phase-space helper in
  production; the massless registry path remains on the LB-1 analytic
  `NeutrinoBackground`.
- **Channel A (implementation)**:
  `phase_space_grid(mass_eV, N_q=15)` now returns deterministic
  float64 Gauss-Laguerre nodes and Fermi-Dirac-weighted quadrature
  weights. The massless energy moment recovers `7 pi^4 / 120` and the
  number-density moment recovers `(3/2) zeta(3)` to the declared test
  tolerances.
- **Channel B (source anchor)**:
  the shipped grid keeps the FB-9 local `N_q = 15` contract while the
  audit remains explicit that CLASS’s internal non-cold-relic machinery
  is broader than a single hard-coded quadrature rule.
- **Channel C (verification)**:
  the FB-9.1 tests pin determinism, positivity, monotonic nodes,
  moment recovery, and convergence-budget behaviour at
  `N_q in {10, 15, 30}`.

## §FB-9.2

### FB-9.2 — `MassiveNeutrinoBackground.rho_rest` / `.p_rest`

- **LB-1 anchor clause**:
  an explicitly constructed `MassiveNeutrinoBackground(..., mass_eV=0)`
  returns the exact LB-1 massless formulas for `rho_rest`, `p_rest`,
  `dot_rho`, and `temperature`.
- **Channel A (implementation)**:
  `MassiveNeutrinoBackground` now evaluates `rho(a)` and `p(a)` from
  the Fermi-Dirac phase-space integrals, caches the thermodynamic
  history on the shared FLRW `a` grid, and exposes
  `w(a)`, `free_streaming_velocity(a)`, and `free_streaming_wavenumber(a)`.
- **Channel B (source anchor)**:
  the positive-mass normalization follows the three-degenerate-`ncdm`
  split `N_eff ~= 3 x 1.0132 + 0.00441`, so the background uses the
  effective `T_ncdm/T_gamma ~= 0.71611` and the corresponding
  `3.0396 / 3.044` rescaling required to match the standard
  CLASS/CAMB Planck-2018 setup.
- **Channel C (verification)**:
  the three frozen CLASS fixtures at `Sigma_mnu = 0.06, 0.12, 0.24 eV`
  all match `rho(a)`, `p(a)`, and `w(a)` on the shared BASS `eta`
  grid to better than `rtol = 1e-4`, and each NPZ carries a provenance
  header, CLASS version, precision JSON, and generator-script SHA-256.

## §FB-9.3

### FB-9.3 — registry integration and `Sigma_mnu = 0` byte identity

- **LB-1 anchor clause**:
  `SpeciesBackgroundRegistry.from_planck2018(Sigma_mnu=0.0)` keeps the
  exact LB-1 `NeutrinoBackground` construction, byte-for-byte.
- **Channel A (implementation)**:
  the registry signature now accepts `Sigma_mnu: float = 0.0` and
  dispatches internally to `MassiveNeutrinoBackground` only when the
  sum is strictly positive. No new enum label was added.
- **Channel B (source anchor)**:
  the degenerate approximation is enforced centrally at the registry
  (`mass_eV = Sigma_mnu / 3.0`) so downstream code does not need to
  know how the FB-9 split is implemented.
- **Channel C (verification)**:
  the FB-9.3 tests pin byte-identical `rho_rest` / `p_rest` for all
  species at `Sigma_mnu = 0`, confirm that the neutrino slot remains a
  `NeutrinoBackground` in that branch, and verify that positive mass
  changes the neutrino slot only.

## §FB-9.4

### FB-9.4 — hierarchy wire-up and free-streaming regression

- **LB-1 anchor clause**:
  `hierarchy_rhs_neutrino` stays byte-identical at `Sigma_mnu = 0`,
  and the dedicated FB-9.4 regression now captures every
  `hierarchy_rhs_*` output on a fixed seeded state under that anchor.
- **Channel A (implementation)**:
  the hierarchy driver accepts an optional `neutrino_background` and,
  when it is a positive-mass `MassiveNeutrinoBackground`, scales the
  free-streaming operator by the effective `q / epsilon` factor.
- **Channel B (source anchor)**:
  the audit target is the standard free-streaming scale rather than a
  new perturbation-family split: the massive branch must recover the
  known `k_fs(a)` behaviour and the large-`k` `-8 f_nu` suppression
  proxy without applying the mass term twice.
- **Channel C (verification)**:
  the FB-9.4 tests keep the zero-mass byte anchor green, recover the
  quoted `k_fs(today)` rule-of-thumb within 10%, and pin both the
  large- and small-`k` limits of the leading-order suppression proxy.

## §FB-9.5

### FB-9.5 — `TiltedSpeciesBackground` composition over a massive-ν base

- **LB-1 anchor clause**:
  the tilt wrapper itself remains unchanged; `beta = 0` still
  short-circuits exactly onto the base species output.
- **Channel A (implementation)**:
  FB-9.5 lands as a harness-only sub-phase: no production code changes,
  only the composition tests over a `MassiveNeutrinoBackground` base.
- **Channel B (source anchor)**:
  the EMM rest-to-tilted algebra used by FB-3 is species-generic, so
  the audit target is composition honesty rather than a new massive-ν
  tilt formula.
- **Channel C (verification)**:
  the FB-9.5 tests pin `beta = 0` byte identity, verify the boosted
  `rho_tilde / p_tilde` formulas at `beta > 0`, and confirm that the
  tilt velocity itself does not pick up spurious mass dependence.

## §FB-9.6

### FB-9.6 — docs, gallery, fixtures, and manuscript closeout

- **LB-1 anchor clause**:
  every docs surface repeats the same invariant explicitly:
  `Sigma_mnu = 0` remains the LB-1 massless path.
- **Channel A (implementation)**:
  Topic `15_massive_neutrino/` is now rendered with four PNGs, the
  gallery READMEs are updated, the species spec documents the real
  phase-space and `w(a)` interpolation contract, Chapter 11 gains the
  massive-neutrino systematic section, Chapter 8 cross-references that
  systematic, Chapter 1 points forward to it, and the bibliography now
  carries the three phase-specific massive-neutrino references.
- **Channel B (source anchor)**:
  the CLASS generator stays outside production and writes only frozen
  NPZ oracles; runtime code imports no external Boltzmann solver.
- **Channel C (verification)**:
  the FB-9.6 docs/gallery harness is now real and passes at
  `9 passed`; it checks the four Topic-15 PNGs, the species-spec
  section, the Chapter-11 / Chapter-8 / Chapter-1 wording, and the
  rendered-gallery bookkeeping.

## Validation checklist

- [x] Six skeletons implemented.
- [x] Full-suite byte-identity at `Sigma_mnu = 0` demonstrated.
- [x] `rho(a)` matches the CLASS fixture at three `Sigma_mnu` values,
      `rtol = 1e-4`.
- [x] Free-streaming `k_fs` recovery within 10%.
- [x] Gallery topic 15 rendered.
- [x] `ch11` + `ch08` manuscript edits + bibliography update landed.
- [x] `01_species_background_spec.md` massive-neutrino section added.
- [x] Audit + dev-log + plan + NEXT_SESSION rotation updated.

## Phase close

FB-9 is closed locally at the actual-work boundary with the
massive-neutrino phase-space grid, the positive-mass background
thermodynamics, registry dispatch, hierarchy free-streaming modifier,
FB-3 tilt-composition harness, CLASS oracle fixtures, Topic-15 gallery,
and the manuscript/spec closeout all implemented and verified.

- Full-suite state at close:
  `4269 passed, 8 skipped, 2 warnings`
- Gallery state at close:
  Topic 15 rendered with 4/4 PNGs.
- Documentation state at close:
  species spec, manuscript, bibliography, audit, dev log, plan, and
  next-session handoff all updated to the FB-9 actual-work boundary.
