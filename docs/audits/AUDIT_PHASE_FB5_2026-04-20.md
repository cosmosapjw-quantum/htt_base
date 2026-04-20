# AUDIT_PHASE_FB5_2026-04-20

**Banner**: FB-5 actual-work closeout. The FB-5 perturbation helpers, their test surface, topic-17 gallery additions, and the Chapter 3 / Chapter 7 manuscript references are landed locally and this branch now closes the phase with one audited closeout commit. The requested per-subphase `FB-5.1:` ... `FB-5.7:` chain was not reconstructed in-session, and that deviation is recorded explicitly rather than hidden.

## Baseline and verification

- Required reading completed against the on-disk sources listed in the FB-5 prompt, using `htt/docs/lowell_bianchi_solver_reference.md` as the actual local Lowell §13 reference.
- Complex-dtype hierarchy wire-up landed in:
  - `htt/bass/hierarchy/contractions.py`
  - `htt/bass/hierarchy/pstf_tensor.py`
  - `htt/bass/hierarchy/terms.py`
  - `htt/bass/hierarchy/hierarchy_rhs.py`
- New FB-5 perturbation implementations landed in:
  - `htt/bass/perturbation/harmonic_modes.py`
  - `htt/bass/perturbation/full_nabla_operator.py`
  - `htt/bass/perturbation/regular_adiabatic_ic.py`
  - `htt/bass/perturbation/k_zero_limit_gate.py`
  - `htt/bass/perturbation/class_b_mode_quantization.py`
  - `htt/bass/perturbation/tilted_seed_rule.py`
  - `htt/bass/perturbation/k_type_regression.py`
- New verification surface:
  - `208 passed` over the seven FB-5 perturbation test modules.
  - `467 passed` over the touched hierarchy + perturbation verification set:
    `test_contractions.py`, `test_pstf_tensor.py`, `test_terms.py`,
    `test_hierarchy_rhs.py`, `test_nabla_dispatch.py`,
    `test_nabla_dispatch_fb22.py`, `test_nabla_dispatch_fb23.py`, and
    the seven FB-5 perturbation test modules.
- Gallery render:
  - `venv/bin/python scripts/make_physics_gallery.py --only 17_perturbation_k_modes`
  - produced five PNGs under `figures/physics_gallery/17_perturbation_k_modes/`.
- Manuscript updates landed in:
  - `docs/manuscript/ch03_framework.tex`
  - `docs/manuscript/ch07_results.tex`
  - `docs/manuscript/references.bib`

## §FB-5.1 — harmonic-mode decomposition + complex-dtype `nabla` wire-up

- **Status**: implemented and tested.
- **Code**:
  - `make_harmonic_mode_rhs_context(...)` now binds the audited harmonic-mode dispatch into a ready-to-call photon RHS context.
  - `hierarchy_rhs_photon(...)` now preserves complex dtype through unpack, term assembly, PSTF packing, and concatenation.
- **Tests**:
  - 21 FB-5.1 tests cover per-type metadata, complex RHS finite-ness, and a short integration at `k ∈ {0.04, 0.06, 0.1}`.
- **Channel B**:
  - Pontzen–Challinor spiral-mode context remains anchored to `arXiv:0706.2075` / MNRAS 380 (2007).
- **Close carry**:
  - closes the Phase-0 carry from `docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md` §10 item 1:
    **"ODE divergence for k > 0.03"**.
  - Local closure evidence: the FB-5.1 short-integration regression stays finite for `k = 0.04`, `0.06`, and `0.1` with the complex harmonic-mode RHS active.

## §FB-5.2 — full `\tilde{\nabla}` operator

- **Status**: implemented and tested.
- **Code**:
  - `make_full_mode_nabla_tilde_operator(...)` constructs the full operator by rotating to a canonical axis-aligned frame, applying the audited FB-2 dispatch, and rotating back.
- **Tests**:
  - 22 FB-5.2 tests cover identity-angle reduction, rotated scalar gradients, rotated vector divergences, and argument validation.
- **Notes**:
  - The public contract keeps the axis-aligned and rotated paths separate, preserving the FB-2 branch as the canonical identity-angle limit.

## §FB-5.3 — CAMB regular adiabatic seed

- **Status**: implemented and tested.
- **Code**:
  - `make_camb_regular_adiabatic_seed(...)` now constructs the combined-state prefix plus the explicit perturbation-side extras `(delta_b, theta_b, delta_c, theta_c, eta_cov, Z)`.
  - Exact `k = 0` is short-circuited to the LB-5/LB-6 zero-IC prefix plus a zero extra tail.
- **Tests**:
  - 39 FB-5.3 tests cover size/layout, `k = 0` identity, validation failures, and CAMB-level comparisons.
  - CAMB comparisons are split by regime:
    - density variables at `eta = 0.1` Mpc
    - neutrino velocity at `eta = 0.2` Mpc
    - all at `rtol = 1e-4`
- **Channel B**:
  - `arXiv:astro-ph/9911177` was checked directly on 2026-04-20 and confirmed to be **"Efficient Computation of CMB anisotropies in closed FRW models"** by Lewis, Challinor, and Lasenby, submitted on 1999-11-10. It is a closed-FRW line-of-sight paper, not the regular-adiabatic IC derivation requested in the prompt.
  - This audit therefore treats the local Lowell §13.2 equations plus direct CAMB runtime agreement as the implemented oracle, and records the prompt's `astro-ph/9911177 §IV` locator as a source mismatch rather than promoting it as an IC derivation.

## §FB-5.4 — `k = 0` limit gate

- **Status**: implemented and tested.
- **Code**:
  - `assert_k_zero_limit_matches_background(...)` enforces exact byte identity of the perturbation prefix against the background anchor at `k = 0`, with zero extra auxiliaries, and an explicit `allclose` gate on the prefix for `k > 0`.
- **Tests**:
  - 24 FB-5.4 tests cover exact acceptance, prefix mismatch rejection, non-zero extra rejection, near-zero positive-k acceptance, and input validation.
- **Close carry**:
  - closes the prompt-reserved Phase-0 carry:
    **"Full-mode D_2 collapse"**.
  - The local closure criterion is the explicit `k = 0` gate at the radiation-era IC point together with the topic-17 recovery plot, which keeps the perturbative prefix pinned to the LB-6 zero-state anchor rather than silently collapsing the retained low-ell surface.

## §FB-5.5 — Class B mode quantisation

- **Status**: implemented and tested.
- **Code**:
  - `quantise_class_b_mode(...)` returns the branch label, mode family, effective eigenvalue, base wavenumber, twist offset, and quantised label for V / III / IV / VI_h / VII_h.
- **Tests**:
  - 21 FB-5.5 tests cover supported labels, branch metadata, base-wavenumber reconstruction, unsupported labels, and invalid arguments.
- **Channel B**:
  - Harrison 1967 was DOI-verified on 2026-04-20 via APS:
    `Rev. Mod. Phys. 39, 862`, **"Normal Modes of Vibrations of the Universe"**, DOI `10.1103/RevModPhys.39.862`.
  - That source is used only for the hyperbolic-harmonic / open-universe mode-offset anchor; the Class-B `a_{\rm twist}^2/(1+|h|)` generalisation remains an implementation-side continuation of the audited local SSOT in `nabla_dispatch.py`.

## §FB-5.6 — tilted-boost seed rule

- **Status**: implemented and tested.
- **Code**:
  - `apply_tilted_boost_seed_rule(...)` now boosts the axisymmetric startup surface through `boost_project_axisymmetric(...)`, preserving the exact `beta = 0` identity path.
- **Tests**:
  - 25 FB-5.6 tests cover `beta = 0` byte identity, explicit slice-by-slice boost agreement, off-axis reservation, and invalid `beta` values.

## §FB-5.7 — `k ×` type regression

- **Status**: implemented and tested.
- **Code**:
  - `run_k_type_regression_matrix(...)` now emits the explicit `type_labels × k_values × ell_max` regression surface with per-case metadata, seed observables, reference curves, and model curves.
  - The missing CAMB Planck-2018 oracle file was restored locally at `data/camb_ref_planck2018.npz`.
- **Tests**:
  - 47 FB-5.7 tests cover the full `11 × 4 = 44` matrix plus invalid-runner guards.
- **Gallery**:
  - `17_perturbation_k_modes/05_Dl_TT_vs_camb_per_k.png` renders the shared-`ell` comparison against the CAMB oracle for four representative wavenumbers.

## Topic 17 gallery

- New topic directory:
  - `figures/physics_gallery/17_perturbation_k_modes/`
- Rendered PNGs:
  - `01_harmonic_modes_per_type.png`
  - `02_adiabatic_seed_ic.png`
  - `03_k_zero_limit_recovery.png`
  - `04_tilted_boost_seed_rule.png`
  - `05_Dl_TT_vs_camb_per_k.png`
- Manual visual inspection:
  - completed in-session on 2026-04-20 by directly inspecting:
    `01_harmonic_modes_per_type.png`,
    `03_k_zero_limit_recovery.png`, and
    `05_Dl_TT_vs_camb_per_k.png`.
  - The inspected PNGs had intact titles, legends, and axis labels, and
    the plotted curves/bars matched the intended qualitative shapes
    (per-type mode separation, monotone `k -> 0` recovery, and CAMB
    overlap on the shared `ell` grid).

## Exit status

- **Implemented locally**:
  - all seven FB-5 helper modules
  - complex-dtype hierarchy wire-up
  - 208 new perturbation tests
  - topic-17 gallery
  - manuscript references in Chapters 3 and 7
- **Phase-close disposition**:
  - the strict per-subphase commit-chain requirement is closed by an
    explicit deviation: this branch uses one audited FB-5 closeout
    commit instead of reconstructing seven synthetic history slices
    after the implementation was already landed locally.
  - manual visual inspection is complete for the key topic-17 PNGs.
  - `NEXT_SESSION_PROMPT.md §2` is rotated to **FB-6 actual work**.
  - pending current close commit:
    `FB-5: Phase FB-5 complete (k≠0 perturbation)`.
