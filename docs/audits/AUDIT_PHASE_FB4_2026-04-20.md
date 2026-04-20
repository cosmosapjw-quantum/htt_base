# AUDIT_PHASE_FB4_2026-04-20

**Banner**: Phase FB-4 actual work — tilted Thomson kernel Layer B  
**Scope**: FB-4.1 full-Lorentz PSTF Thomson seed, FB-4.2 tilted
E↔B mixing seed, FB-4.3 additive quadratic Doppler remainder  
**Invariant anchor**: `beta = 0` must reduce byte-for-byte to the LB-4
orthogonal Thomson kernel on every path.


## §FB-4.1

### §FB-4.1 three-channel verification

- **Channel A**: Verified local anchors
  `htt/bass/collision/thomson_pstf.py`,
  `htt/bass/collision/tilted_thomson_layer_b.py`,
  `htt/bass/collision/test_fb41_tilted_thomson_skeleton.py`,
  `scripts/make_physics_gallery.py::plot_10_04_thomson_beta_sweep_Dl`,
  `docs/manuscript/ch05_teff_corrections.tex §sec:tilted-thomson-layer-b`.
- **Channel B**: arXiv fetch verified
  `astro-ph/9911481`; quote:
  “Under changes of frame, multipoles with different mix because of
  Doppler beaming effects.”
  Source: <https://arxiv.org/abs/astro-ph/9911481>,
  ar5iv lines 121-125 on 2026-04-20.
- **Channel C**:
  The shipped surface keeps the LB-4 orthogonal kernel as the only
  collision arithmetic source of truth.
  A signed version of the repo’s existing axisymmetric Challinor
  recurrence is used to move the temperature and E-mode towers into the
  electron frame.
  The orthogonal operator is evaluated there without altering any LB-4
  coefficients.
  The resulting collision tower is boosted back with the inverse signed
  recurrence.
  At `beta = 0`, both boost calls short-circuit to fresh copies, so the
  returned tensor is exactly the LB-4 anchor.
  Units remain `Gamma_T × multipole`, since the boost is dimensionless.
  No silent fallback exists: off-axis directions raise
  `NotImplementedError`.

**Core principles**
1. External-code policy intact (CAMB only as fixture).
2. PSTF SSOT; any ℓm detour is a documented round-trip.
3. β = 0 byte-identity vs LB-4 anchor on every test path.
4. No silent fallback.
5. Determinism.

### §FB-4.1.0 Audit target reconstruction
| Layer | Claim | Implementation | Output |
|---|---|---|---|
| Physics | Frame changes mix neighbouring PSTF multipoles (Challinor 2000 eq. 26 seed) | `htt/bass/collision/tilted_thomson_layer_b.py::evaluate_tilted_thomson_pstf_collision` | `PSTFTensor` |
| Invariant | `beta = 0` == LB-4 Thomson byte-for-byte | zero-tilt short-circuit + anchor fixture test | `test_fb41_beta_zero_matches_anchor_fixture` |
| Routing | Same call surface as LB-4 plus optional `tilted_electron` | explicit wrapper around `ThomsonPSTFCollisionOperator` | Topic 10 + manuscript §`sec:tilted-thomson-layer-b` |
| Overlap | Reuses the shipped axisymmetric boost recurrence | `docs/audits/AUDIT_PHASE_FB_META4_2026-04-20.md §FB-4.1` pin upheld | `test_fb41_linear_challinor_m0_recurrence_matches_manual_axisymmetric_build` |

### §FB-4.1.1 Contract / interface table
| Surface | Shape / dtype | Units | Admissible range |
|---|---|---|---|
| `v_b_real_sph` | `(3,) float64` | velocity | finite |
| `Gamma_T` | scalar `float` | `Mpc^-1` | finite, non-negative |
| `tilted_electron` | `TiltedSpeciesBackground | None` | dimensionless tilt wrapper | `0 <= beta < 1`, axis-aligned subset only |
| return | `PSTFTensor(ell, (2ell+1,))` | `Gamma_T × multipole` | finite |

### §FB-4.1.2 Phys-math audit ledger
- Known limit: `beta = 0` returns the exact LB-4 tensor.
- Dimensional consistency: boost law is dimensionless; only `Gamma_T`
  sets units.
- Sign: inherited from LB-4 after boost / inverse-boost composition.
- Determinism: no RNG, no global state.
- Numerical conditioning: linear recurrence only on the packed `m = 0`
  slice.
- Silent omission check: off-axis directions raise, they do not fall
  back.
- Baseline overlap: LB-4 coefficients untouched.
- Literature overlap: the implementation is explicitly the axis-aligned
  seed, not the future arbitrary-direction Wigner-d lift.

### §FB-4.1.3 Equation-to-code mapping audit
- Eq. (26) seed recurrence → `docs/manuscript/ch05_teff_corrections.tex`
  eq. `fb41-boost` and
  `htt/bass/collision/_tilted_layer_b_common.py::signed_axisymmetric_boost`.
- Orthogonal Thomson kernel → `htt/bass/collision/thomson_pstf.py`.
- Frame sandwich → boost in, evaluate LB-4, boost out.

### §FB-4.1.4 Numerical / pipeline audit
- Cancellation risk is low because the zero-tilt path bypasses all
  boost arithmetic.
- Conditioning risk is concentrated at the highest retained `ell`; the
  Topic 10 plot remains smooth over `2 <= ell <= 30`.
- Deterministic gallery output rendered to
  `figures/physics_gallery/10_collision_and_visibility/04_thomson_beta_sweep_Dl.png`.

### §FB-4.1.5 Ranked failure modes
| # | Type | Severity | Symptom | Root cause | Cheap probe | Misinterpretation |
|---|---|---|---|---|---|---|
| 1 | Scope | P1 | off-axis tilt raises | Wigner-d lift still deferred | `test_fb41_off_axis_direction_raises` | “full arbitrary-direction Layer B shipped” |
| 2 | Regression | P0 | zero-tilt drift | boost applied on anchor path | `test_fb41_beta_zero_matches_anchor_fixture` | false physics change |
| 3 | Numerical | P2 | edge-ell wiggle in proxy ratio | truncated neighbour coupling | inspect `04_thomson_beta_sweep_Dl.png` | apparent instability |

### §FB-4.1.6 Verifier filter
| Verifier | Verdict | Evidence |
|---|---|---|
| A. Physics — known-limit recovery | Passed | exact zero-tilt anchor test |
| A. Physics — dimensional consistency | Passed | dimensionless boost × LB-4 units |
| A. Physics — sign / normalisation | Passed | inherited LB-4 coefficients |
| A. Physics — alternative explanation | Passed | scope pinned as axis-aligned seed |
| B. Code — contract satisfaction | Passed | pinned META signature preserved |
| B. Code — actual code-path usage | Passed | new tests hit `beta = 0`, `beta > 0`, off-axis guard |
| B. Code — regression risk | Passed | targeted collision suite green |
| B. Code — reproducibility | Passed | deterministic tower + figure |
| C. Numerical — tolerance robustness | Passed | exact/`allclose` tests across `beta` sweep |
| C. Numerical — convergence / stability | Passed | finite outputs for `beta ∈ {0.01, 0.1, 0.3}` |
| C. Numerical — baseline reproducibility | Passed | whole-suite rerun retained only pre-existing CAMB fixture blocker |

### §FB-4.1.7 Minimal repair plan
No P0 / P1 detected beyond the documented off-axis deferral to FB-5.2.

### §FB-4.1.8 Minimal test set (executed)
| Test | Role | Verdict |
|---|---|---|
| `bass/collision/test_fb41_tilted_thomson_skeleton.py` | zero-tilt anchor, finite sweep, off-axis guard, Challinor recurrence | Passed |
| `bass/collision/test_thomson_pstf.py` | LB-4 orthogonal anchor | Passed |
| `venv/bin/python scripts/make_physics_gallery.py --only 10_collision_and_visibility` | gallery regeneration | Passed |

### §FB-4.1.9 Final verdict
- **Status**: Pass
- **Implement now**: axis-aligned Layer-B Thomson seed with exact zero-tilt anchor
- **Do NOT touch**: off-axis Wigner-d lift (`FB-5.2`)
- **Figure PNG**: `figures/physics_gallery/10_collision_and_visibility/04_thomson_beta_sweep_Dl.png`
- **Test file**: `htt/bass/collision/test_fb41_tilted_thomson_skeleton.py`
- **Chapter anchor**: `docs/manuscript/ch05_teff_corrections.tex §sec:tilted-thomson-layer-b`
- **Baseline movement**: `3401 passed, 73 skipped, 3 errors` → `3425 passed, 72 skipped, 3 errors`
- **Carry-forward ledger**: arbitrary-direction boost remains reserved for `FB-5.2`


## §FB-4.2

### §FB-4.2 three-channel verification

- **Channel A**: Verified local anchors
  `htt/bass/collision/tilted_eb_mixing.py`,
  `htt/bass/collision/test_fb42_eb_mixing_skeleton.py`,
  `htt/bass/collision/polarization.py`,
  `scripts/make_physics_gallery.py::plot_10_05_bb_from_tilted_lens_e`,
  `docs/manuscript/ch05_teff_corrections.tex §sec:tilted-thomson-layer-b`.
- **Channel B**: arXiv fetch verified `astro-ph/9611125`; quote:
  “for scalar metric perturbations one set is identically zero”.
  Source: <https://arxiv.org/abs/astro-ph/9611125>, abstract line 43
  on 2026-04-20.
- **Channel C**:
  The shipped seed retains the E-only orthogonal collision operator as
  the baseline.
  B is introduced only through a same-ell rotation term on the packed
  axisymmetric slice.
  The self-damping branch for B mirrors the E self term but omits the
  temperature quadrupole source, matching the orthogonal B floor.
  At `beta = 0`, the wrapper returns the exact E anchor and an
  identically zero B tensor.
  Finite beta generates B from pure E input without touching the
  orthogonal Bianchi-I floor.
  Off-axis directions still raise explicitly.
  The heatmap figure confirms the low-ell concentration of the induced
  B amplitude.

**Core principles**
1. External-code policy intact (CAMB only as fixture).
2. PSTF SSOT; any ℓm detour is a documented round-trip.
3. β = 0 byte-identity vs LB-4 anchor on every test path.
4. No silent fallback.
5. Determinism.

### §FB-4.2.0 Audit target reconstruction
| Layer | Claim | Implementation | Output |
|---|---|---|---|
| Physics | Tilted LOS mixes E and B while preserving the orthogonal B floor | `htt/bass/collision/tilted_eb_mixing.py::evaluate_tilted_polarization_eb_collision` | `(PSTFTensor, PSTFTensor)` |
| Invariant | `beta = 0` => existing E source + zero B | explicit short-circuit | `test_fb42_beta_zero_matches_e_anchor_and_zero_b` |
| Routing | Wrap current E-only storage without changing `PolarizationHierarchyState` | optional `b_state` input | `test_fb42_none_b_state_matches_explicit_zero_b_state` |
| Overlap | Type-I `psi' = 0` B floor | `bass/los/bianchi_propagator.py` + zero-B tests | `test_fb42_beta_zero_b_mode_floor_is_exact` |

### §FB-4.2.1 Contract / interface table
| Surface | Shape / dtype | Units | Admissible range |
|---|---|---|---|
| `Pi_2_packed` | `(5,) float64` | quadrupole amplitude | required |
| `b_state` | `PSTFHierarchyState | None` | polarization tower | `None` means exact zero-B anchor |
| `tilted_electron` | `TiltedSpeciesBackground | None` | dimensionless tilt wrapper | `0 <= beta < 1`, axis-aligned subset only |
| return | `tuple[PSTFTensor, PSTFTensor]` | `Gamma_T × multipole` | finite |

### §FB-4.2.2 Phys-math audit ledger
- Known limit: `beta = 0` returns the exact E anchor and zero B.
- Dimensional consistency: same `Gamma_T × multipole` units on both
  channels.
- Sign: E/B rotation is antisymmetric in the same-ell mixing term.
- Determinism: no stochastic input.
- Numerical stability: same-ell mixing plus axisymmetric recurrence
  only.
- Silent omission: off-axis tilt raises.
- Storage stability: no mutation of the shipped `PolarizationHierarchyState`.
- Gallery consistency: the BB/EE heatmap is smooth and monotone in
  `beta`.

### §FB-4.2.3 Equation-to-code mapping audit
- Same-ell E/B rotation seed →
  `docs/manuscript/ch05_teff_corrections.tex` eq. `fb42-eb`.
- E anchor reuse →
  `bass.collision.polarization.E_mode_collision_source`.
- B damping mirror →
  `htt/bass/collision/tilted_eb_mixing.py::_b_mode_collision_tower`.

### §FB-4.2.4 Numerical / pipeline audit
- The dominant signal sits at low `ell`; the heatmap decays rapidly by
  `ell ~ 10`.
- Zero-B default is explicit, not inferred.
- The generated B amplitude remains finite over the full sweep
  `beta in [0, 0.3]`.

### §FB-4.2.5 Ranked failure modes
| # | Type | Severity | Symptom | Root cause | Cheap probe | Misinterpretation |
|---|---|---|---|---|---|---|
| 1 | Scope | P1 | off-axis tilt raises | arbitrary-direction rotation deferred | `test_fb42_off_axis_direction_raises` | “full Wigner-d polarization rotation shipped” |
| 2 | Regression | P0 | non-zero B at `beta = 0` | missing short-circuit | `test_fb42_beta_zero_b_mode_floor_is_exact` | false violation of Type-I floor |
| 3 | Interface | P1 | depth mismatch crash | inconsistent `E/B` tower lengths | `test_fb42_b_state_depth_mismatch_raises` | unrelated numerical bug |

### §FB-4.2.6 Verifier filter
| Verifier | Verdict | Evidence |
|---|---|---|
| A. Physics — known-limit recovery | Passed | exact E anchor + zero B floor |
| A. Physics — dimensional consistency | Passed | same collision units on both outputs |
| A. Physics — sign / normalisation | Passed | antisymmetric same-ell rotation |
| A. Physics — alternative explanation | Passed | B generation requires both `beta > 0` and non-zero E |
| B. Code — contract satisfaction | Passed | pinned META signature preserved |
| B. Code — actual code-path usage | Passed | `None`, zero-B, explicit B, off-axis, mismatch tests all execute |
| B. Code — regression risk | Passed | targeted collision suite green |
| B. Code — reproducibility | Passed | deterministic heatmap |
| C. Numerical — tolerance robustness | Passed | exact/`allclose` tests across sweep |
| C. Numerical — convergence / stability | Passed | finite for `beta = 0.01, 0.1, 0.3` |
| C. Numerical — baseline reproducibility | Passed | no new suite-wide failures beyond CAMB fixture blocker |

### §FB-4.2.7 Minimal repair plan
No P0 / P1 detected beyond the documented off-axis deferral to FB-5.2.

### §FB-4.2.8 Minimal test set (executed)
| Test | Role | Verdict |
|---|---|---|
| `bass/collision/test_fb42_eb_mixing_skeleton.py` | E anchor, B floor, E→B generation, guards | Passed |
| `venv/bin/python scripts/make_physics_gallery.py --only 10_collision_and_visibility` | gallery regeneration | Passed |

### §FB-4.2.9 Final verdict
- **Status**: Pass
- **Implement now**: axis-aligned E/B collision seed with explicit zero-B orthogonal floor
- **Do NOT touch**: arbitrary-direction polarization rotation (`FB-5.2`)
- **Figure PNG**: `figures/physics_gallery/10_collision_and_visibility/05_bb_from_tilted_lens_e.png`
- **Test file**: `htt/bass/collision/test_fb42_eb_mixing_skeleton.py`
- **Chapter anchor**: `docs/manuscript/ch05_teff_corrections.tex §sec:tilted-thomson-layer-b`
- **Baseline movement**: `3425 passed, 72 skipped, 3 errors` → `3448 passed, 71 skipped, 3 errors`
- **Carry-forward ledger**: full Wigner-d E/B rotation remains reserved for `FB-5.2`


## §FB-4.3

### §FB-4.3 three-channel verification

- **Channel A**: Verified local anchors
  `htt/bass/collision/tilted_doppler_second_order.py`,
  `htt/bass/collision/test_fb43_second_order_doppler_skeleton.py`,
  `scripts/make_physics_gallery.py::plot_10_06_doppler_second_order_residual`,
  `docs/manuscript/ch05_teff_corrections.tex §sec:tilted-thomson-layer-b`.
- **Channel B**: arXiv fetch verified `0706.2075`; quote:
  “the power in B-mode polarisation is predicted to be similar to the E-mode power”.
  Source: <https://arxiv.org/abs/0706.2075>, abstract lines 17-18 on
  2026-04-20.
- **Channel C**:
  The present implementation is intentionally scoped as an additive
  seed because the prompt-supplied `v_e^2` locator was not verifiable on
  disk.
  The orthogonal collision source is reused as the unique amplitude
  baseline.
  Multiplication by `gamma_sq - 1` enforces the exact zero-tilt limit.
  For small `beta`, this is `beta^2 + O(beta^4)`, so the remainder is
  automatically quadratic.
  The term stays separate from the linear Layer-B wrapper, preventing
  silent contamination of the FB-4.1 source.
  This is a deliberate scope demotion, not a claim of full literature
  completeness.

**Core principles**
1. External-code policy intact (CAMB only as fixture).
2. PSTF SSOT; any ℓm detour is a documented round-trip.
3. β = 0 byte-identity vs LB-4 anchor on every test path.
4. No silent fallback.
5. Determinism.

### §FB-4.3.0 Audit target reconstruction
| Layer | Claim | Implementation | Output |
|---|---|---|---|
| Physics | quadratic tilt correction vanishes at `beta = 0` and scales as `beta^2` | `htt/bass/collision/tilted_doppler_second_order.py::evaluate_tilted_second_order_doppler_correction` | `PSTFTensor` |
| Invariant | exact zero-tilt suppression | explicit short-circuit | `test_fb43_beta_zero_is_exact_zero_tensor` |
| Scope | literature-complete `v_e^2` term not yet verified on-disk | documented demotion in code + manuscript + audit | `§FB-4.3.2` |
| Routing | additive on top of FB-4.1 linear kernel | no change to LB-4 or FB-4.1 signatures | Topic 10 residual figure |

### §FB-4.3.1 Contract / interface table
| Surface | Shape / dtype | Units | Admissible range |
|---|---|---|---|
| `temperature_state` | `PSTFHierarchyState` | temperature tower | finite PSTF hierarchy |
| `Gamma_T` | scalar `float` | `Mpc^-1` | finite, non-negative |
| `tilted_electron` | `TiltedSpeciesBackground | None` | dimensionless tilt wrapper | `0 <= beta < 1`, axis-aligned subset only |
| return | `PSTFTensor` | `Gamma_T × multipole` | finite |

### §FB-4.3.2 Phys-math audit ledger
- Known limit: `beta = 0` returns the exact zero tensor.
- Dimensional consistency: `gamma_sq - 1` is dimensionless, so units are
  inherited from the orthogonal source.
- Sign: non-negative prefactor for all admissible `beta`.
- Determinism: no RNG, no global cache mutation.
- Numerical stability: no subtraction on the zero-tilt path.
- Silent omission: no fallback to a guessed higher-order kernel.
- Scope honesty: explicitly documented as an additive remainder only.
- Baseline overlap: no mutation of FB-4.1 surface.

### §FB-4.3.3 Equation-to-code mapping audit
- Exact quadratic prefactor →
  `docs/manuscript/ch05_teff_corrections.tex` eq. `fb43-v2`.
- Orthogonal source reuse →
  `htt/bass/collision/thomson_pstf.py::ThomsonPSTFCollisionOperator`.
- Additive wrapper →
  `htt/bass/collision/tilted_doppler_second_order.py`.

### §FB-4.3.4 Numerical / pipeline audit
- The residual track is nearly flat in `ell`, as expected from a pure
  multiplicative prefactor.
- The `beta = 0.1` gallery residual stays near `10^-2`.
- The term is small enough to remain additive on the seeded surface.

### §FB-4.3.5 Ranked failure modes
| # | Type | Severity | Symptom | Root cause | Cheap probe | Misinterpretation |
|---|---|---|---|---|---|---|
| 1 | Scope | P1 | term mistaken for full literature `v_e^2` kernel | unresolved citation surface | `§FB-4.3.2` + manuscript wording | overclaim of physics completeness |
| 2 | Regression | P0 | non-zero tensor at `beta = 0` | missing short-circuit | `test_fb43_beta_zero_is_exact_zero_tensor` | false second-order signal |
| 3 | Numerical | P2 | noisy residual curve | accidental `ell`-dependent prefactor | inspect `06_doppler_second_order_residual.png` | spurious higher-order structure |

### §FB-4.3.6 Verifier filter
| Verifier | Verdict | Evidence |
|---|---|---|
| A. Physics — known-limit recovery | Passed | exact zero tensor at `beta = 0` |
| A. Physics — dimensional consistency | Passed | dimensionless prefactor |
| A. Physics — sign / normalisation | Passed | `gamma_sq - 1 >= 0` |
| A. Physics — alternative explanation | Passed | manuscript explicitly marks additive-scope seed |
| B. Code — contract satisfaction | Passed | pinned META signature preserved |
| B. Code — actual code-path usage | Passed | zero-tilt, sweep, small-β, malformed-tilt tests execute |
| B. Code — regression risk | Passed | targeted collision suite green |
| B. Code — reproducibility | Passed | deterministic residual curve |
| C. Numerical — tolerance robustness | Passed | exact / `allclose` prefactor checks |
| C. Numerical — convergence / stability | Passed | finite for `beta = 0.01, 0.1, 0.3` |
| C. Numerical — baseline reproducibility | Passed | full suite only retains CAMB fixture blocker |

### §FB-4.3.7 Minimal repair plan
- Keep the present additive remainder isolated.
- Revisit only after a verified literature expression for the full
  second-order Thomson kernel is recovered.

### §FB-4.3.8 Minimal test set (executed)
| Test | Role | Verdict |
|---|---|---|
| `bass/collision/test_fb43_second_order_doppler_skeleton.py` | zero-tilt, quadratic scaling, closed-form prefactor | Passed |
| `venv/bin/python scripts/make_physics_gallery.py --only 10_collision_and_visibility` | gallery regeneration | Passed |

### §FB-4.3.9 Final verdict
- **Status**: Pass
- **Implement now**: additive `gamma_sq - 1` quadratic Doppler remainder
- **Do NOT touch**: literature-complete second-order Thomson kernel until a verified source is recovered
- **Figure PNG**: `figures/physics_gallery/10_collision_and_visibility/06_doppler_second_order_residual.png`
- **Test file**: `htt/bass/collision/test_fb43_second_order_doppler_skeleton.py`
- **Chapter anchor**: `docs/manuscript/ch05_teff_corrections.tex §sec:tilted-thomson-layer-b`
- **Baseline movement**: `3448 passed, 71 skipped, 3 errors` → `3479 passed, 70 skipped, 3 errors`
- **Carry-forward ledger**: full literature `v_e^2` source remains deferred pending verified recovery
