# AUDIT_PHASE_FB4_2026-04-20

**Banner**: Phase FB-4 actual work — tilted Thomson kernel Layer B  
**Scope**: FB-4.1 full-Lorentz PSTF Thomson seed  
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
