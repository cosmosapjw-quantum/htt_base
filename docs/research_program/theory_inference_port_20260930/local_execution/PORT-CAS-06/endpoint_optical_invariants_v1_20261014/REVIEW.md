# P06-A — independent review (verbatim final report of a fresh read-only reviewer)

## P06-A independent review: endpoint optical invariants of one physical ray (`endpoint_optical_invariants_v1_20261014`)

**Verdict: PASS_WITH_NOTES.** I found no blocking finding. Card lean_step 2 (aberration sphere Jacobian) is met only in a chart, and that limit must be carried as a recorded scope limit. Scientific admission stays **HOLD**.

Reviewer: Claude Opus 5.5 (model id `claude-opus-5-5`). I am a fresh, read-only reviewer and did not author this work. The only files I wrote are under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/p06-a_rerun/`.

T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-06/endpoint_optical_invariants_v1_20261014`

### Per-check table

| # | Check | Status | Evidence |
|---|---|---|---|
| 0 | Card identity | PASS | `unzip -p … tasks/P06-A.json \| sha256sum` gives `debd1cd7…0b15`; the zip hashes to `2d0b6da9…af6f`. Both match SOURCE_RECOVERY and AUTHOR_RETURN. |
| 1a | Source citations | PASS | I recomputed sha256 for every cited file and all match: CAS_CONTRACT `904d95fe…`, PORT_MAP `d0050aa3…`, `relativistic_kinematics.py` `9ae767f9…`, T5 pack `4fab2be9…`, observations_findings `a4d21f94…`, prior_stats_findings `7be6983b…`, CLAIMS `9750221f…`, COMMON_SPEC `4714827e…`, `endpoint_temperature.wl` `5f0e5c2c…`. I read each cited line range and the content says what is claimed: T5 lines 15-17 `p=(ε/c)(u−n)`; 22-26 `ũ=γ(u+β)`; 40-48 `D=γ(1+β·n)=1/(γ(1−β·ñ))`; 50-61 ε/T invariance; 63-67 `dΩ̃=D⁻²dΩ`. obs_findings line 17 sourceward `D=γ(1+β·n)`; 25-27 `dA′=D dA`, `dL′=dL/D` "for … reciprocity". prior_stats §3.3 gives `a>|b|`, `β=−b/a`, `T0=(a²−|b|²)^{-1/2}`. One line range is a cosmetic mismatch: `inverse_temperature_boost` is at lines 235-245 of the py file. |
| 1b | Frozen targets predate the first compile | PASS (timestamp only) | Frozen at 21:42:46Z (file mtime 06:42 KST) → first receipt (import) 21:43:29Z → first main compile 21:44:18Z. The directory is untracked in git, so the order is shown only by the in-document timestamp and mtimes. There is no cryptographic anchor. |
| 1c | Statement faithfulness (frozen vs final) | PASS | My own parser compared 86 declarations (16 defs, 70 theorems) after whitespace normalisation: no mismatches. The author's `frozen_statements.lean.txt` and `final_statements.lean.txt` are also byte-identical. Diffs of failed attempts 04-07 against 08 touch proofs only, plus the `open scoped Matrix` preamble. |
| 1d | Doppler direction convention (sign of β·n) | PASS | Lean: `photon E n = E(1,−n)` with n sourceward. `energy (fourVelocity β) k = γ(1+β·n)E` (`energy_new`), which matches T5, obs_findings:17 and the implementation (`relativistic_kinematics.py:229` `d=u[0]+u[1:]@n`, with `u=γ(1,β)`). My Lean check: `doppler 0 0 (3/5) 0 0 1 = 2 > 1` (observer moving toward the source sees a blueshift) and `=1/2` for the opposite ray. `inverse_temperature_boost(a,b)` returns `(γ(−b/a)/a, −b/a)`; `inverse_temperature_inversion` proves this equals `1/√(a²−|b|²)`. |
| 1e | Acceptance 1: same physical ray, remapped direction fixed | PASS | One fixed null `k`. `same_ray_components` gives `Bst(Binv k)=k`. `newComp_observer` gives `Binv u′=e0`. `newDir_formula` shows the new-tetrad direction of the same `k` equals the closed-form `aberr`. `aberr_unit` and `aberr_surjective` are proved. By hand: `h=γ²/(γ+1)=(γ−1)/β²`, so `aberr = [n+γβ+(γ−1)(β̂·n)β̂]/D`, the standard aberration formula. |
| 1f | lean_step 2: sphere Jacobian ↔ area/solid-angle definitions | CONCERN (scope limit, non-blocking) | See "Card lean_step 2" below. |
| 1g | lean_step 3: `(1+z′)dA′=(1+z)dA` | PASS | `endpoint_optical_same_ray` uses the same `Es`, and the energies come from the same `k`. It reuses the reviewed `endpoint_product_invariant`. |
| 1h | lean_step 4: reciprocity explicit, `dL′=dL/D` | PASS | `hrecOld` and `hrecNew` are explicit hypotheses in each frame. `dL′` is a free variable, so nothing is circular. By hand: `(1+z)²/D²·D·dA = dL/D`. |
| 1i | Scalar inverse-T affine law, `a²−|b|²=1/T0²` | PASS | `inverse_temperature_affine`, `affine_coeff_domain`, `isotropic_blackbody_criterion` (an iff, on the unit sphere) and `boosted_isotropic_sky`. These match TBO-07 and INDEPENDENT_DECISION (`β_O/R=−b/a`). |
| 1j | Boundaries z=0, β=0 | PASS | `boundary_beta_zero` (D=1, identity frame change, n′=n, Jacobian 1, z/dA/dL fixed), `temperature_beta_zero`, `boundary_z_zero`. The composite theorem needs `0<|β|` because the chart axis is undefined at β=0. I proved the β=0 composite myself from `boundary_beta_zero` (`ReviewAudit.lean`, exit 0), so nothing is lost at the boundary. |
| 1k | Pitfall: no polarization or spin-2 | PASS | No spin-2 or polarization object exists in the Lean. Only the scalar `planckOcc` occupation is used, and the comments and `not_claimed` exclude it. |
| 1l | Negative controls | PASS (note) | `distinct_ray_counterexample`, conjunct 4: mixing D of ray n=−ẑ (1/2) for z with D of ray n=+ẑ (2) for dA gives a product of 4, not 1. That is a genuine control, at the algebra level. Conjuncts 1-2 are an observer-replacement control, not a different-ray control. My Python rerun reproduces the product of 4. |
| 2 | No hypothesis assumes its conclusion; no vacuity | PASS (notes) | I instantiated the composite theorems at β=(0,0,3/5), n=ẑ, with `ℓ=√s` and `μ=β·n/ℓ` given by `rfl` (`endpoint_optical_same_ray`, `endpoint_luminosity_same_ray`). I showed `hocc` is satisfiable with T′=D·T0. Note: in `temperature_transform`, `hocc` is equivalent to `E′/T′=E/T0` (by injectivity). That is the source's physics premise (T5:50-61) stated honestly. The non-trivial content is the reciprocal-Doppler affine form. |
| 3a | Hash integrity | PASS | All 9 receipts: recomputed `source/stdout/stderr` sha256 equal the recorded values. Exit codes: 01-03 = 0, 04-06 = 1 (failed attempts kept), 07-09 = 0. `lean/P06AOptics.lean` = `732fbbfd…` and is identical to `compile_08` source. `AxiomAudit.lean` = `956988d1…` and is identical to `compile_09`. Import sources are unchanged: PortCas01 `e289039f…`, PassiveTensorBridge `49f37140…`, EndpointScalarInvariant `6e2ba677…`. |
| 3b | Forbidden constructs | PASS | `grep -nE 'sorry\|admit\|native_decide\|axiom\|set_option\|sorryAx\|maxHeartbeats\|unsafe\|implemented_by\|extern'` on `T/lean/P06AOptics.lean` found nothing (rc=1). |
| 3c | Axioms | PASS | Author `compile_09`: 70/70 theorems use only `[propext, Classical.choice, Quot.sound]`. My independent audit agrees: 70/70 identical, 0 deviating. |
| 4 | Independent recompile | PASS | I copied the 4 sources to `p06-a_rerun/src` and, from `/home/cosmosapjw/lean_oracles/viii_oracle` (toolchain v4.31.0, mathlib `fabf563a…`, confirmed from `lean-toolchain` and `lake-manifest.json`), ran `lake env bash -c "LEAN_PATH=$S/imports:$LEAN_PATH lean -R $S/src -o $S/imports/<M>.olean $S/src/<M>.lean"` for PortCas01, PassiveTensorBridge, EndpointScalarInvariant and P06AOptics. All exit 0. The only output is the `φ` unused-variable lint at line 450. PortCas01 and PassiveTensorBridge oleans are byte-identical to the author's. The EndpointScalarInvariant and P06AOptics oleans differ only because the olean embeds the absolute source path; a second rebuild of EndpointScalarInvariant was deterministic (`870cb973…` both times). My audit `p06-a_rerun/src/ReviewAudit.lean` (sha256 `a8e6be2f…`) prints axioms for all 70 public theorems and runs the instantiation, β=0 and sign checks above. Exit 0. |
| 5 | Monte Carlo / numerics | PASS | `python3 -I p06-a_rerun/mc_check.py` calls the repository's own `endpoint_boost`, `inverse_temperature_boost` and `lorentz_boost` (seed 20261014, 3000 random cases with \|β\|<0.95). Results in the table below. |

Monte Carlo maximum absolute deviations:

| Quantity | Max deviation |
|---|---|
| D from energy ratio vs closed form | 8.9e-16 |
| New-tetrad direction vs `aberr` | 2.1e-15 |
| Null preserved | 1.8e-13 |
| Bst·Binv k = k | 1.8e-14 |
| Reciprocal D | 3.0e-15 |
| `endpoint_boost` d vs D | 1.8e-15 |
| (1+z′)dA′ − (1+z)dA | 1.4e-14 |
| dL′ − dL/D | 7.4e-13 |
| Finite-difference S²→S² Jacobian determinant × D² − 1 (relative) | 4.7e-10 |
| Inverse-T affine law | 1.3e-15 |
| a² − \|b\|² − 1/T0² | 1.9e-15 |
| T0 and β recovered by `inverse_temperature_boost` | 4.4e-15 / 2.2e-16 |

Global check of `dΩ = D² dΩ′` with 4e6 samples, β=0.6ẑ:

| Cap | MC old solid angle | MC ∫D² dΩ′ | Exact (by hand) |
|---|---|---|---|
| +ẑ, half-angle 0.5 | 2.6038 | 2.5944 | 2.5994 |
| −ẑ, half-angle 0.5 | 0.2001 | 0.2011 | 0.2015 |

Both caps agree with the exact values within Monte Carlo noise.

### Card lean_step 2 (aberration Jacobian)

What is proved:
- `dμ′/dμ = D⁻²` (`ab_hasDerivAt`).
- `μ ↦ μ′` is a bijection of [−1,1] with fixed endpoints and an explicit inverse.
- For every g continuous on [−1,1], `∫g(μ′)D⁻²dμ = ∫g dμ′`, plus the φ-iterated form, the band form and total 4π.
- `chart_link` shows the general-β closed form has polar cosine `ab ℓ μ` and that the component perpendicular to β̂ is rescaled by 1/D > 0, so the azimuth is unchanged.
- `areaDist dS (J·dΩ) = D·areaDist dS dΩ` with the same dS.

What is not proved:
- `dΩ = dμ dφ` (Archimedes) is taken as a convention.
- The azimuth φ is never defined as a function on S².
- The 2-D Jacobian is assembled from the chart's product structure, not as a determinant.
- There is no statement against Mathlib's sphere surface measure (`Measure.toSphere`).
- In the composite theorem, the new solid angle is defined as `deriv (ab ℓ) μ * dΩ`.

Judgement: D⁻² is a coordinate-independent density, and the chart computation is mathematically correct; my finite-difference determinant and the global cap test agree with it. But the card's "실제 측도·미분 연결까지" (connecting to the actual measure and differential) is only met in a chart. The limit was fixed at freeze time (FROZEN_TARGETS "Honest scope limits") and is listed in `not_claimed`. So it is a declared strengthening-free scope limit, not a silent weakening. It must stay recorded as one.

### Blocking findings
None.

### Non-blocking notes
1. Record lean_step 2 as "chart-level (β̂-polar) Jacobian and change of variables; S²-measure form open". Unlock: a new frozen target that states the pushforward of the S² surface measure under `aberr` has density D⁻², via `Measure.toSphere`.
2. `endpoint_optical_same_ray` requires β ≠ 0. The β=0 composite follows from `boundary_beta_zero`, as verified in `ReviewAudit.lean`. Adding it as a stated corollary would make acceptance 2 explicit.
3. `dL′` has no independent flux definition. The result is exactly the card's "reciprocity explicit" route, and `T′=D·T0` is close to definitional given `hocc`. Neither is a defect, but prose should not present them as derivations of reciprocity or of occupation invariance.
4. The first two conjuncts of `distinct_ray_counterexample` are an observer-replacement control, not a distinct-ray control.
5. The card's `tool_tasks` (wolfram_xact, sympy, sage_singular) have no receipts in this unit. The Lean proofs formally cover the same algebra and the domain conditions (D>0, inverse boost), and the numerics are evidence only.
6. Freeze-before-compile rests on the in-document timestamp and mtimes, because the unit is untracked in git.
7. Cosmetic: the line range cited for `inverse_temperature_boost` is slightly off, and `total_solid_angle` triggers an unused-`φ` lint.
8. The author's `observed_runtime` is UNKNOWN.

### Not proved / not claimed (carry forward)
- Scientific admission: **HOLD**.
- Chart-free S² surface-measure (`Measure.toSphere`) form of `dΩ′=D⁻²dΩ`, and the identity `dΩ=dμdφ`.
- Derivation of reciprocity or transparency (hypotheses only).
- Derivation of Planck occupation invariance (hypothesis only).
- Polarization, spin-2, or frequency-dependent intensity transfer.
- Distinct-ray comparison (negative control only).
- Curved-space propagation, source motion, real data.
- Wolfram, sympy and sage tool tasks of the card.
- Publication state and full PORT-CAS-06 / four-axis acceptance.

### Proposed VALIDATION_MATRIX scientific row (I did not edit it)
`P06-A | endpoint optical invariants, same ray | PASS_WITH_NOTES (independent review, claude-opus-5-5) | 70/70 theorems, axioms {propext, Classical.choice, Quot.sound}; independent recompile exit 0; statements = frozen; MC vs endpoint_boost / inverse_temperature_boost ≤ 1e-12 abs, Jacobian determinant ≤ 5e-10 rel | scope limits: β̂-polar chart Jacobian (no S² measure), reciprocity and Planck occupation as hypotheses, scalar only, β≠0 composite with β=0 piecewise | scientific_admission HOLD`

### Files
- Card: `/home/cosmosapjw/Dropbox/bianchi/htt_base/HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (member `tasks/P06-A.json`)
- Reviewed: `T/lean/P06AOptics.lean`, `T/FROZEN_TARGETS.md`, `T/SOURCE_RECOVERY.md`, `T/AUTHOR_RETURN.json`, `T/raw/compile_0[1-9]_*.{json,source.lean,stdout,stderr}`, `T/raw/AxiomAudit.lean`
- Implementation: `/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/src/common/relativistic_kinematics.py`
- In `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/p06-a_rerun/`:
  - `src/ReviewAudit.lean`
  - `review_audit.out`
  - `rerun_*.out`
  - `imports/*.olean`
  - `mc_check.py`

