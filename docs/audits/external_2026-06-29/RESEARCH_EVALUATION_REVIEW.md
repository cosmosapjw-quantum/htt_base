# Critical & Constructive Research Review — BASS / HTT Departure-Decomposition Program

Reviewer stance: expert cosmology + statistics, no prior project knowledge, research content only. Inputs read in order: `docs/final_report/main.pdf` (23 pp.), `docs/generated/egs_results_table.md` (14 proven + 3 data), the K1/K5/K6 discharge JSONs, `pr08_006_joint_artifact.json`, `docs/research_program/BLOCKERS.md`. Citations are to PDF line numbers (extracted text), result-table rows, and JSON paths.

---

## 1. Verdict

**MINOR REVISIONS.**

This is a strong, unusually honest program that has reached a coherent, near-publishable state: a *methods + identifiability + bounds* paper whose headline — a measured rank-2 graded comparator with a proven two-sector no-go and named re-opening channels — is defensible **without** a native low-ℓ solver. The theorem suite is internally consistent and (where claimed) Wolfram/gate-verified; the three real-data discharges (K1/K5/K6) are each calibrated and carry accurate caveats; no hard boundary is violated (no family ID, no geometry detection, no native-validation, no physical-vorticity claim, no MIO-as-odds). The revisions below are about **precision of the no-go claims** (one substantive: the two blind sectors are not on equal footing) and a few calibration/representation caveats — not about any invalidated result.

## 2. Minimal Defensible Claim

Using only `{low-ℓ CMB temperature, radial peculiar velocities}` and no native anisotropic Boltzmann solver, the four-sector FLRW-departure comparator `g=(Σ²,W²,Ω_tilt,Ω_k)` is **data-rank-2**: the shear sector `Σ²` (through the CMB quadrupole) and the tilt sector `Ω_tilt` (through the bulk-flow dipole) are the only reachable directions, while the vorticity sector `W²` is a **genuine structural null** (radial velocities satisfy `n·Ω·n≡0`; CMB temperature is curl-blind at EGS order) and the anisotropic-curvature sector `Ω_k` has **no leading-EGS-order channel** in these two probes. On real data the reachable sectors give a model-independent CF4 bulk flow `|B|≈341±102 km/s` (error cosmic-variance-dominated; release-matched-mock coverage 0.67 vs 0.19 measurement-only) and a low-ℓ CMB morphology statistic whose **global look-elsewhere-corrected** p-value under an isotropic ΛCDM null is `0.097` (SMICA) / `0.121` (Commander) — consistent with isotropy and *not* an E2E-calibrated detection. The vorticity sector is a structural no-go on the curl-suppressed CF4 Wiener field (vorticity ≤0.6% of shear, injection-validated). The conditional EGS-type theorems (quadrupole–filling identity, multi-ℓ Fisher floor and its finite-k profile, two-sided shear bracket, Volterra depth-memory, vorticity re-opening) hold under their stated hypotheses. No Bianchi family is identified, no geometry detected, no scalar promoted.

## 3. Novelty Assessment

**Yes — this is a genuine, publishable contribution without the native solver.** Three things are individually novel and jointly coherent:
1. **A rank-aware, provenance-bound identifiability result for the departure comparator** — phrasing "which anisotropy sectors current data can even constrain" as a response-map rank statement (rank 2 of 4) with two sectors in the null. Identifiability-first framing is uncommon in the Bianchi-constraint literature and is the right move when a solver is absent.
2. **A two-sector no-go** with *named re-opening channels* (transverse velocities, CMB B-modes) — a no-go that tells an observer exactly what new data would break it is more useful than a bare null.
3. **The Π-as-e-value calibration** (EGS3-A3) and the **Fisher-floor finite-k profile** (EGS3-B1) are the freshest analytic pieces: an e-value certificate with a Markov error rate upgrades the exceedance curve from "not a probability" to an anytime-valid object, and the k-profile makes the sub-0.632 floor a *physical* (finite-k) statement rather than a toy.

**Strongest honest framing:** "A model-independent, rank-aware identifiability + calibration framework for FLRW-departure sectors, with conditional EGS-type theorems and a measured rank-2 comparator carrying a proven two-sector no-go." Pitch it as a methods/limits paper (PRD/JCAP methods), not an anisotropy-constraint paper. The one framing risk is overselling the **Ω_k** half of the no-go (see §5/§8).

## 4. Fatal Blockers

**None.** No stated result is invalidated. Specifically: K1 is correctly held at `measured_partial` (ΛCDM null, look-elsewhere only; E2E null open); K5/K6 are calibrated/structural and carry their caveats; PR08-006 fails-closed the blind sectors (never zeroed); every figure manifest carries `family_identification:false`/`native_solver_result:false`. The hard boundaries are respected.

## 5. Theorem Audit

| Item | Status | Issue | Required fix |
|---|---|---|---|
| EGS3-A1 graded rank-2 (`Σ²,Ω_tilt` reachable; `W²,Ω_k` null) | **Needs precision** | The two null sectors are conflated. `W²` is a *genuine, order-independent* null (algebraic `n·Ω·n≡0`; curl/Weyl loophole). `Ω_k` is only a *leading-EGS-order* "no channel" (`pr08_006_joint_artifact.json:sectors.Omega_k`, "at leading EGS order"). Anisotropic curvature **does** source low-ℓ CMB at higher order (ISW, lensing, the full Bianchi transfer), so `Ω_k`-blindness is truncation-dependent, not structural | (a) Show the `Ω_k` response column is a *genuine zero* in both channels at leading order, **not merely collinear with the `Σ²` column** (degeneracy ≠ blindness; the rank-2 count is the same but the physics differs). (b) State explicitly that `Ω_k` re-opens beyond leading EGS order / with the native transfer, unlike `W²`. Relabel "joint null `{W²,Ω_k}`" → "structural null `{W²}` + leading-order no-channel `{Ω_k}`" |
| NT-A1 quadrupole–filling identity | OK | Closure-conditional `a₂=κΣ`; `F_shear∝D₂`, `→0` in EGS limit; Wolfram-verified (`egs_results_table` NT-A1) | None |
| NT-A3 single-sky dispersion | OK (fixed) | Now correctly "one estimator; **NOT** a universal CR floor" (`egs_results_table` NT-A3) — the prior mislabel is corrected | None |
| NT2-A1 multi-ℓ Fisher–CR floor + EGS3-B1 k-profile | OK, with caveat | Floor `0.632(ℓ=2)→0.424(L=20)`; EGS3-B1 makes it a finite-k profile from a *single* shear-sourced mode through a real visibility (PDF 600–608). The floor value still depends on the response `r_ℓ`, now physical-but-single-mode | State that the sub-0.632 floor is a *single-mode, finite-k* statement; the full-response floor needs the mode integral (the native transfer). Honest as written; make the single-mode scope explicit in the abstract |
| NT2-A2 octupole saturation | OK | Tail `ℓ>3` converges; "no single extra multipole closes the floor" | None |
| EGS3-A3 Π as a calibrated e-value | OK, minor | `E=1[x>t]/α` has unit null mean ⇒ Markov `P(E≥1/β)≤β` (PDF 596–599). Valid e-value. But `α` is the registered-null exceedance; if estimated from the 2000-GRF ensemble it carries MC error | Use a finite-null-corrected `α` (e.g. `(k+1)/(n+1)`) so the e-value remains conservative under MC error in `α`; state the null is GRF-ΛCDM (so the certificate inherits that null's idealisation) |
| EGS3-A4 Rao–Blackwell sufficiency | OK | `Var_RB ≤ Var_raw`; `(a₂,a₃,dipole)` sufficient for the reachable subspace | None |
| NT2-B1 + EGS3-B4 two-sided bracket | OK | Lower bound `Σ≥a₂κ/(1+R)>0` excludes zero shear-filling; nondegeneracy `C_up·κ·(1+R)>1` → `12/7>1` for `κ=4/21,C_up=9` (verified independently, see addendum) | Carry the exact MES upper constant `C_up` (currently a documented 9); state the bracket on real `a₂,a₃` |
| EGS3-B2 Volterra depth-memory | OK | Volterra integral with kernel `exp(−3∫H)` = ODE + Grönwall; `max|Volterra−ODE|≈2.9×10⁻⁶` | None |
| NT2-B3 / EGS3-B3 vorticity re-opening | OK | Radial blind `n·Ω·n≡0` (max `2.2×10⁻¹⁶`); transverse channel rank 3 re-opens; B-modes named | None — this is the model for how the `Ω_k` claim should also be made precise |
| EGS3-PSD cone redesign | OK as representation; one gap | `x_C=tr(CM)`, `M=diag(g)⪰0`, bit-identical (PDF 575–583). Faithful for the reachable, non-negative sectors and the bracket cone-shell. But `M⪰0` needs `g≥0` componentwise; with the comparator's `−W²` sign and a possibly **signed `Ω_k`**, PSD-ness is convention-dependent | State the sign convention: `C=diag(+,−,+,+)` carries the signs and `M=diag(Σ²,W²,Ω_tilt,Ω_k)` needs each entry `≥0` — so `Ω_k≥0` must be a convention (or the blind-sector fail-closed sidesteps it). Note (as the PDF does) that this is representation-only and does not front the production diagnostic |

## 6. Statistics Audit

| Item | Status | Issue | Required fix |
|---|---|---|---|
| K1 null + look-elsewhere | OK (honest) | ΛCDM-GRF null (2000), six registered statistics, frozen max-scan, `+1` global rank; SMICA global `p=0.097`, Commander `0.121` (`k1_global_maxscan.json`). Individual statistics are marginal (parity 0.025, `S_{1/2}` 0.045, planarity 0.042) but the global p is null. Caveats explicit: "not FFP10/NPIPE E2E; no instrument noise/systematics/foregrounds" | (a) Note the **component-separation spread** (0.097 vs 0.121, ~25%) as a foreground/method-sensitivity caveat — do **not** average them. (b) Keep the E2E null as the gating next step (§7). The look-elsewhere max-scan is valid |
| K5 coverage + cosmic-variance | OK | `|B|=341±102 km/s`; error CV-dominated (102 vs 5 km/s measurement); CV-inclusive coverage 0.67 vs 0.19 meas-only (`k5_cf4_release_coverage.json`). The 0.19→0.67 jump correctly shows the error is CV-dominated and the ΛCDM-prior CV term restores nominal coverage | (a) State the **ΛCDM bulk-flow expectation** (~150–250 km/s at the effective depth) so `341` reads as consistent-but-high, not anomalous. (b) Flag that CV coverage is **conditional on the fiducial ΛCDM per-component `σ_cv` prior** (the JSON says so) — a non-ΛCDM CV prior would change coverage. (c) Selection/Malmquist enter only through the distance-error model; note residual selection is not fully forward-modelled |
| K6 no-go logic | OK | Vorticity/shear ≤0.0055 at all radii; injected solid-body rotation recovered to machine precision ⇒ `structural_no_go=True` (`k6_cf4_curl_posterior.json`). "No-go, not detection" is the honest reading: the WF field is curl-suppressed *by construction*, and the injection shows the estimator *can* see curl, so the small ratio is a property of the field | Minor: the injection tests *one* curl mode (solid-body); state that estimator curl-sensitivity is demonstrated for the solid-body mode, and that the structural suppression is the WF prior's, not a vorticity measurement |
| PR08-006 rank + fail-closed | OK | Data rank 2 (`Ω_tilt` measured, `Σ²` partial); `W²,Ω_k` fail-closed (never zeroed); no collapsed `x_C`; `mio_as_odds:false`, `scalar_to_family_promotion:false` (`pr08_006_joint_artifact.json`). The assembly is correct and honest | Carry the §5 `Ω_k` relabel into the artifact note (`Ω_k` = leading-order no-channel, not the same null as `W²`) |
| Identifiability rank argument | Needs the §5 fix | The rank-2 *count* is correct; the *characterization* of the null needs the genuine-zero-vs-degenerate check for `Ω_k` and the order-dependence statement | As in §5 (EGS3-A1) |

## 7. Constructive Roadmap (smallest set to publish each piece)

1. **Make the `Ω_k` no-go precise (highest priority, cheap).** Add the explicit response-map columns for all four sectors in both channels at leading EGS order, and show `Ω_k`'s column is either a genuine zero or collinear with `Σ²` (state which). Add one sentence that `Ω_k` re-opens beyond leading order. This converts the weakest claim into a correct, sharper one and protects the headline.
2. **K1 E2E null (the one real gating measurement).** Acquire the public FFP10 (`dx12_v3_{method}_{cmb,noise}_mc_*`, 999+300 per method) or PR4/NPIPE (~300 A/B) component-separated maps via the PLA portal / NERSC (the program already documents this in `K1_E2E_DOWNLOAD_GUIDE.md` and the downstream pipeline is built). The E2E run must show the global p **with instrument+foreground+mask systematics**; report whether `0.097` moves. Until then K1 stays `measured_partial`. *(The blocker is correctly diagnosed as portal-only access, and cobaya was correctly ruled out as `C_ℓ`-level, not maps.)*
3. **K6 curl posterior (upgrade the no-go).** Run the Hoffman–Ribak CR ensemble on the real CF4 3D WF field (mechanics ready, `constrained_realizations.curl_posterior`) to replace "≤0.6%" with a realization-conditioned vorticity posterior (median + 16/84) — turning the structural no-go into a posterior-quantified no-go.
4. **K5 mock realism.** Validate the Bias-Gaussianization mocks against an N-body/2LPT CF4-selection mock for the bulk-flow covariance; report coverage under a non-ΛCDM CV prior to show robustness.
5. **Theorem generalizations.** (i) Fisher floor: do the mode integral over the shear power to get the full-response floor (beyond single-mode EGS3-B1). (ii) Bracket: quote `C_up` from the exact MES inequality, not the documented 9. (iii) Vorticity re-opening: forecast the transverse-velocity / B-mode sensitivity needed to actually reach `W²`.

## 8. Claim-Tier Corrections and Safe Claims

**Exact wording to change**
- `egs_results_table.md` EGS3-A1 + `pr08_006_joint_artifact.json` — replace "joint null `['W2','Omega_k']`" → "structural null `{W²}` (order-independent) **plus** leading-EGS-order no-channel `{Ω_k}` (re-opens at higher order; degeneracy-with-`Σ²` excluded)".
- PDF §Axis-B / EGS3-B1 — append to the floor statement: "this sub-0.632 floor is a **single-mode, finite-k** result; the full-response floor requires the shear-power mode integral."
- `k5_*` / PDF K5 — append: "`|B|≈341±102 km/s` is consistent with the ΛCDM bulk-flow expectation at this depth; the cosmic-variance coverage is conditional on a fiducial ΛCDM `σ_cv` prior."
- `k1_*` / PDF K1 — append: "global p is component-separation dependent (SMICA 0.097, Commander 0.121); neither is E2E-calibrated."
- EGS3-A3 — state the e-value null is GRF-ΛCDM and use a finite-null-corrected `α`.

**Claims that are safe as stated**
- The comparator is **data-rank-2** from these two channels; `W²` is a genuine structural null (radial `n·Ω·n≡0`, curl/Weyl-blind), with named re-opening channels (transverse velocities, B-modes).
- NT-A1 quadrupole–filling identity; NT-A3 as a single-estimator dispersion (explicitly **not** a universal floor); NT2-A1 multi-ℓ Fisher floor `<0.632` (single-mode/finite-k); NT2-A2 octupole saturation; NT2-B1+EGS3-B4 two-sided bracket excluding zero shear-filling; EGS3-B2 Volterra depth-memory with a Grönwall envelope.
- EGS3-A3 Π as a calibrated e-value with a Markov error rate (under the registered GRF-ΛCDM null); EGS3-A4 Rao–Blackwell sufficiency; EGS3-PSD as a faithful **representation** (bit-identical, representation-only).
- K5 `|B|≈341±102 km/s`, error cosmic-variance-dominated, CV-inclusive coverage nominal — a model-independent kinematic descriptor.
- K6 a **structural no-go** on a curl-suppressed field (vorticity ≤0.6% of shear, injection-validated) — not a vorticity measurement.
- K1 a **global look-elsewhere-corrected** low-ℓ morphology p under an isotropic ΛCDM null (`0.097`/`0.121`), consistent with isotropy, **not** an E2E-calibrated detection.
- PR08-006 a measured rank-2 comparator with fail-closed blind sectors (never zeroed), no collapsed scalar, no MIO-as-odds, no scalar→family.
- No native low-ℓ solver, no Bianchi family, no detected geometry.

---

*Bottom line: a genuinely publishable methods/identifiability/bounds program. One substantive revision (make the `Ω_k` half of the no-go precise — it is not the same kind of null as `W²`), one real gating measurement (the K1 E2E null), and a handful of calibration caveats stand between this and submission. The honesty discipline (fail-closed sectors, ΛCDM-null labelling, structural-no-go framing, the corrected NT-A3) is exemplary and should be preserved.*
