# V5 Round-15 P1 — PSTF / 1+3 Covariant / Tetrad Derivation for BASS

**Integrated SSoT build — R1 → R10 + P1.5.**
Integrated against the previous `V5_ROUND15_P1_PSTF_DERIVATION_FINAL_CLEAN.md` after receiving the separate R1→R10 + P1.5 document.
Started 2026-04-25, after Round-15 P0 (D-1 LoS grid decoupling, commit `cb82a2a`).
This document is documentation only. No production code is changed by it.

Conventions throughout: metric signature `(−,+,+,+)`; conformal time η; natural units `c = 1`; PSTF (Projected Symmetric Trace-Free) multipole hierarchy after Ellis–van Elst 1998 and Challinor–Lasenby 2000-I+II; spherical harmonic packing `i = ℓ² + (m+ℓ)` for real-spherical-harmonic basis (`tier_b_source_extraction.py:84`).

---

## Integration preface — comparison against the R8 final-clean document

### Integration verdict

This integrated SSoT uses the newly supplied R1→R10 + P1.5 document as the controlling text. It supersedes the previous R8 final-clean document wherever the two conflict. The reason is not stylistic preference: the new document introduces additional line-specific evidence from `ver2_native_integrator.py` (`baryon_labels=("delta_b", "v_b", "v_e", "drag_lock_residual")`, the baryon EOM forcing `3*theta_1`, and the stored slip `3*theta_1 - v_b`) that was not available to the R8 final-clean audit loop. That evidence changes the Doppler convention verdict.

### Supersession table

| Topic | R8 final-clean status | Integrated SSoT status | Reason |
|---|---|---|---|
| Doppler source normalization | No `/k` patch; `(g v_b)'` accepted as canonical for dimensionless `v_b=θ_b/k`. | **Superseded. Apply AF-1:** BASS stores physical velocity `v_b`, so `build_temperature_source` needs `(g v_b)'/k`; thread `k` into the function or divide at projection time. | New `ver2_native_integrator.py` evidence identifies slot 1 as physical velocity, not divergence or already divided variable. |
| Four-cell low-k anchor after AF-1 | Treated as unaffected by Doppler concerns. | **Superseded. Rerun required after AF-1.** Pre-fix Doppler `<0.5%` does not bound post-fix contribution because `/k` amplifies the branch before cancellations. | R10 audit correction. |
| Temperature polter `g Π/4` | Accepted; no temperature-side spin projection patch. | **Retained.** Temperature `Π/4` remains canonical; spin-2 projection belongs to the E-mode branch. | No conflict between documents. |
| `h_S'/6` synchronous patch | No-go. | **Retained.** Still no-go. If monopole correction is ever needed, it must be PSTF-native. | No conflict. |
| Monopole frame contract | Open formal contract; tests required before any correction. | **Refined.** `Θ_0^{BASS}` is treated as kinematic-`n^a` frame; no additional monopole-frame correction is required at the four-cell 5% level after AF-1, but sub-percent validation needs R3.6 diagnostics. | New R3/P1.5 analysis bounds the residual rather than leaving it fully open. |
| Bianchi `m=±2` | Required except aligned-axisymmetric Bianchi I. | **Retained and refined.** Axisymmetric-aligned Bianchi I remains the exception; general tilted/non-axisymmetric Bianchi I and II–IX require all-`m` treatment. | No material conflict. |
| Packed operator status | TODO / unaudited where missing. | **Refined.** Operators are marked `✓⁻` where the intended algebra is known but `packed_operators.py` was absent from the audited bundle. | R9/R10 status cleanup. |
| Analytic oracles | Broad R5 catalogue with exact and asymptotic tests. | **Refined.** Five primary high-`k` oracles are canonical for P1; ancillary R8 tests may remain optional regression ideas but are not the SSoT priority list. | New document narrows scope and ties AF-1 to sharp-Doppler oracle. |

### Controlling follow-up list

1. Apply **AF-1**: modify `flrw_bessel_projector.py:453` from `(g v_b)'` to `(g v_b)'/k`, and thread `k` through the relevant API.
2. Add the sharp-visibility Doppler oracle as the isolated AF-1 regression before/with the code fix.
3. Rerun the four-cell low-`k` anchor after AF-1. The previous anchor cannot be inherited without rerun.
4. Keep `Π/4` temperature polter and E-mode spin-2 projection unchanged; add only regression tests.
5. Do not apply `h_S'/6` or any synchronous-metric patch.
6. For sub-percent source-contract certification, implement the R3.6 diagnostics for `Θ_0^{(kin)} - [Φ(η)-Φ(η_init)]` versus CAMB `clxg/4` after sync→Newtonian conversion.
7. Treat Bianchi all-`m` propagator work as a later design/code track, not part of the current AF-1 fix.

---

## Executive summary

**Verdict on BASS's current PSTF assembly correctness (FLRW limit, recombination window).** BASS's LoS assembly is approximately, not exactly, gauge-coherent — the residual is bounded by $g\cdot[\Phi(\eta)-\Phi(\eta_\text{init})]$ in matter domination, $\le 5\%$ on sub-horizon MD scales, and the ISW driver $e^{-\kappa}(\dot\Phi+\dot\Psi)$ independently captures the late-time / dark-energy era contribution that the PSTF kinematic-frame evolution omits internally. The four-cell low-$k$ empirical anchor from Round-15 P0 (BASS·LoS / CAMB·direct ratios of $0.933, 0.984, 1.044, 0.999$ for $(k, \ell) \in \{(10^{-3}, 2), (10^{-3}, 3), (10^{-2}, 2), (10^{-2}, 3)\}$ with `k_adapt_η100`) is consistent with this $\le 5\%$ residual prediction. **No additional monopole-frame correction is required at the four-cell 5% level**, after applying the AF-1 Doppler $/k$ fix detailed below. Sub-percent precision would require the verification test in §R3.6 (compute $\Theta_0^{(\text{kin})} - [\Phi(\eta)-\Phi(\eta_\text{init})]$ from BASS, compare to CAMB's `clxg/4` after sync→Newt conversion). **Audit-response 2026-04-25 (R9)**: the original phrasing "no code-level correction is required" was self-contradictory with the AF-1 code-fix requirement; this reformulation separates the monopole-frame question (no fix needed) from the Doppler convention question (one-line fix needed).

**Frame identification.** R3 establishes that $\Theta_0^{\text{BASS}}$ is in a third frame distinct from synchronous and Newtonian, named the *kinematic $n^a$-frame*, defined operationally by the source-free PSTF transport `T1+T2+T3+T7+T8+T9+collision` with no metric back-reaction in the photon equations (confirmed by zero matches for `Phi`, `Psi`, `h_dot`, `metric_source` etc. across `hierarchy/`). The leading-order identification

$$
\Theta_0^{(\text{kin})}(\eta, k) \;\approx\; \Theta_0^{(N)}(\eta, k) + \bigl[\Phi(\eta, k) - \Phi(\eta_\text{init}, k)\bigr] + \mathcal O\bigl(k\!\int\!\Psi\,d\eta'\bigr)
$$

(R3.3.3) is the architectural fact that makes the BASS LoS assembly approximately gauge-coherent in MD. The empirically observed "linear-in-η ramp" of $\Theta_0$ noted in Round-12→14 Phase A is reinterpreted under R3 as the integrated SW source accumulating in the kinematic frame, not a synchronous-gauge growing-mode artifact.

**One audit finding — Audit Finding 1 (R2 §5) — RESOLVED 2026-04-25 post-R7.** BASS's Doppler at `flrw_bessel_projector.py:453` is $(g v_b)'$; canonical CAMB form is $(g v_b)'/k$. Post-R7 inspection of `ver2_native_integrator.py:2974–2980, 3047–3052, 3086` confirms `baryon_local_history[:, 1]` holds physical velocity $v_b^{\text{phys}}$ (slot label `"v_b"`, baryon EOM forcing $3\Theta_1$ not $3k\Theta_1$), so BASS is missing the canonical $1/k$ factor. **Code fix specified**: append `/ k` at `flrw_bessel_projector.py:453` and thread $k$ through `build_temperature_source` signature.

**Empirical impact — anchor rerun required (R10 audit-correction 2026-04-25)**: previous drafts claimed the four-cell anchor was "unaffected" because pre-fix Doppler contributes $< 0.5\%$ of the LoS source per R12→14 ablation. This logic is incomplete: the AF-1 fix multiplies the Doppler contribution by $1/k$, so a $< 0.5\%$ pre-fix contribution at $k = 10^{-2}$ becomes a $< 50\%$ post-fix contribution before any cancellations are accounted for. In practice $v_b \propto k$ scaling on super-horizon and Bessel-projection cancellations make the actual post-fix Doppler much smaller than this naive bound, but the four-cell anchor invariance after AF-1 is **expected to be small but not yet verified** — it must be re-run after the code fix lands. R5 Oracle 5 (R5.5.1) is the isolated regression that would have caught the convention error independently of the total spectrum.

**Note on $v_b$ frame identification**: AF-1 closes the $v_b$ *convention* question (velocity vs divergence). It does NOT close $v_b^{\text{BASS}} \approx v_b^{(N)}$ — a separate sync→Newtonian velocity comparison is needed to bound the residual frame mismatch. P1.5-A's working hypothesis $\delta v_b = 0$ inherits this open question.

**Bianchi extension architecture.** Six PSTF operators (T1, T2, T3, T7, T8, T9) covering FLRW + orthogonal Bianchi I/V/VII₀ are already implemented in BASS production code; T4/T5/T6 (acceleration, vorticity) are wired as opt-in kwargs. Eight items remain as planned infrastructure: m=±2 LoS spin-2 projector ($\epsilon_\ell, \beta_\ell$), Bianchi shear forcing $\dot\sigma^{(\pm 2)}$ in the LoS source, tilt velocity $\bar v_{(s)}^a$ infrastructure, tilted-observer LoS residual $\delta S_T^{\text{tilt}}$, m=±2 state-vector population, and the master $x_C$ post-processing diagnostic. The MES-tomographic master departure $x_C = \Sigma^2_{\text{std}} - W^2_{\text{std}} + \Omega_\text{tilt} + \Omega_{k,\text{aniso}}$ maps term-by-term to BASS data sources (R4 §4).

**Five analytic oracles for high-$k$ validation** (R5). Closed-form expressions for $\Delta_\ell^T(k)$ in five limiting regimes — sharp-visibility SW, Gaussian-visibility SW with Bessel-ODE-derived envelope, acoustic toy with explicit peak structure, ISW with Limber stationary-phase, and sharp-visibility Doppler. Together they provide unit-testable validation of BASS's LoS assembly across $k \in [10^{-2}, 10^{-1}]$ Mpc⁻¹ where the §10 CAMB-anchor fails due to CAMB's source-decomposition introspection limit (briefing §3.3). Tolerance specs in §R5.1–§R5.5.

**Recommended code follow-ups** (R7 prompt for second-LLM reviewer; coding-agent tickets):

1. **Apply AF-1 code fix** at `flrw_bessel_projector.py:453`: append `/ k` to the Doppler line; thread $k$ through `build_temperature_source` signature. Diagnose with R5 Oracle 5 regression test before merging (R2 §5; R5 §5).
2. Add diagnostic unit test: $\Theta_0^{(\text{kin})} - [\Phi(\eta)-\Phi(\eta_\text{init})]$ vs CAMB `clxg/4` (sync→Newt) for sub-percent verification of R3.3.3 (R3 §6).
3. Integrate the five analytic oracles as `pytest` fixtures in `tests/los/test_analytic_oracles.py` with tolerance specs from R5 §1–§5 (R5 §7).
4. File the eight ✗ Bianchi-extension items as separate development tickets, scoped per-type (Bianchi I and VII_h have published analytic backbones via Pontzen–Challinor 2007; II/VIII/IX require new derivations) (R4 §5).
5. Excerpt this executive summary as `docs/V5_ROUND15_P1_PSTF_DERIVATION_SUMMARY.md` standalone for thesis ch04 / ch10 cross-reference.

---

## R1. Repo state and prior-work grounding

R1 establishes the shared understanding of the existing repo state. **No new derivation is performed in this round.** The four substantive items below — frame, prior-doc coverage, empirical state, formalization gaps — are each grounded in concrete file:line citations or transcript numbers.

### (a) Gauge / frame the BASS PSTF photon hierarchy lives in

The BASS production photon hierarchy at [`htt/bass/hierarchy/hierarchy_rhs.py:343–540`](../htt/bass/hierarchy/hierarchy_rhs.py#L343) is **PSTF / 1+3 covariant native**. It evolves the packed PSTF brightness moments $\Pi^m_\ell$ via the canonical Ellis–MacCallum nine-term hierarchy (lowell_bianchi_solver_reference.md §6). The orthogonal Bianchi-I / FLRW restriction activates only the operators

$$
\dot\Pi^m_\ell + a \cdot \bigl[\,T_1(\Theta) + T_7(\sigma\!\uparrow) + T_8(\sigma\!=) + T_9(\sigma\!\downarrow) - K_T\bigr] = 0
$$

i.e. expansion `T1` plus shear up/same/down `T7/T8/T9` plus Thomson collision `K_T`; the gradient/divergence operators `T2/T3`, the acceleration operators `T4/T5`, and the vorticity operator `T6` are dispatched but multiply zero coefficients on FLRW (`hierarchy_rhs.py:421–448` short-circuits the `zero_collision and not has_accel and not has_vorticity` branch precisely because of this). The collision `K_T` is supplied by `ThomsonPSTFCollisionOperator` for the temperature track and `EModeThomsonCollisionOperator` for the polarization track (`integrator.py:58–63, 72`).

The integrator output schema [`IntegrationResult`](../htt/bass/hierarchy/integrator.py#L223) carries `photon_T_tower` and `photon_E_tower` of shape `(N_eta, (L+1)²)`, the reduced neutrino fluid `neutrino_tower`, the baryon and CDM local histories, and the tetrad shear components `Sigma_plus, Sigma_minus`. **There is no synchronous-gauge metric variable anywhere in the schema.** A direct grep for `h_S | h_dot | h_prime | metric_trace | sync_h | etak` across `integrator.py + hierarchy_rhs.py + tier_b_source_extraction.py` returns one match only — a single docstring reference to the MB-95 dictionary at `tier_b_source_extraction.py:52`. This confirms briefing §3.4: the session-opener formula `theta0_g_newtonian = theta0_g_synchronous + h_S_dot/6` does not transfer to BASS, because there is no `h_S` to read.

The IC is constructed at [`seed_compatibility.py::build_flrw_regular_seed`](../htt/bass/hierarchy/seed_compatibility.py#L151). With `adiabatic=True` (lines 190–203), the seed assigns the canonical adiabatic ratios

$$
\delta_\gamma : \delta_b : \delta_c : \delta_\nu \;=\; \tfrac{4}{3} : 1 : 1 : \tfrac{4}{3},
\qquad
\theta_\text{common} = 0.
$$

The docstring (line 173) labels these ratios as "synchronous-gauge super-horizon". **However**, on $k\eta \ll 1$ the regular adiabatic mode is gauge-invariant up to terms that decay as $(k\eta)^2$ (Maartens 1998 §III; MB-95 §6). The synchronous label is a residual gauge marker, not a physical content of the seed. The IC is therefore best read as *the unique regular adiabatic mode in the super-horizon regime*, which is then evolved by the PSTF-native RHS without any synchronous-gauge plumbing.

The Newtonian-gauge potentials $\Phi, \Psi$ that enter the LoS source are *not* primary integrator variables. They are reconstructed *post hoc* from Einstein constraints in [`tier_b_source_extraction.py:275–302`](../htt/bass/spectrum/tier_b_source_extraction.py#L275):

$$
\Phi(\eta,k) = \tfrac{3 H_0^2 a^2}{2k^2}\Bigl[\delta\rho_\text{tot} - 3\mathcal{H}\sum_i (\rho_i + p_i)\frac{v_i}{k}\Bigr],
$$
$$
\Psi - \Phi = 3\,\tfrac{3H_0^2 a^2}{2k^2}\sum_{i\in\{\gamma,\nu\}} \tfrac{8}{3}\rho_i \Theta_2^i \quad\text{(intensity quadrupoles only — Round-5 Q-17.1).}
$$

These use MB-95 conventions $\delta_\gamma = 4\Theta_0$, $v_\gamma = 3\Theta_1$ (lines 256–259). **The architectural fact for the ℓ = 0 audit (R3) is**: the integrator state is PSTF; the LoS source assembly mixes PSTF-evolved $\{\Theta_0, \Theta_2, v_b\}$ with constraint-reconstructed Newtonian-gauge $\{\Phi, \Psi\}$. The Tier-B extractor `extract_flrw_sources_from_tier_b` (lines 313–319) returns `theta_0 = PchipInterpolator(eta, theta0_g)` directly — **no gauge transformation is applied to $\Theta_0$** between the tower readout and the LoS assembly.

### (b) What `lowell_bianchi_solver_reference.md` covers, and what it leaves implicit

The 1102-line reference is structured as 18 sections covering, in order: 1+3 decomposition and frame split (§1, with the explicit rule "transport in $n^a$-frame, collision/source/visibility in $u_e^a$-frame"); tetrad background variables $\{\alpha,\beta_{ab},\Sigma_{ab},{}^{(3)}R_{ab},C^i{}_{jk}\}$ (§2); per-species background equations for orthogonal and tilted cases (§3); the exact electron-frame Thomson collision tensor with $\zeta_{ab} = \tfrac34 I_{ab} + \tfrac92 E_{ab}$ (§4); PSTF radiation variables Θ, E, B (§5); the nine-term covariant brightness hierarchy with low-ℓ closure recommendations $L=4,6,8$ (§6); the Tier-B state vector and a *formal matrix LoS propagator* $\mathcal P\exp\!\int(\mathsf L_B + \mathsf C_T)$ (§7); SW/ISW/redshift source from $\delta\Theta, \delta A_a, \delta\sigma_{ab}$ (§8); per-species perturbation equations (§9); quadrupole-aware TCA closing $(\Theta_2, E_2)$ jointly (§10); recombination/reionization first pass (§11); orthogonal vs tilted differences (§12); IC prescriptions (§13: orthogonal CAMB seed in normal frame; tilted electron-frame seed plus boost); observer-side likelihood structure (§14); minimum-state summary (§15); declared out-of-scope items (§16); and the one-line recap (§17).

Five gaps in this reference are critical for P1:

1. **No FLRW-limit reduction of §7's matrix LoS to the SZ96 single-Bessel form.** §7 gives the formal Dyson-series propagator on Bianchi as $\mathbf X(\eta_0) = \mathcal P\exp[\int(\mathsf L_B + \mathsf C_T)]\,\mathbf X(\eta_*) + \int\mathcal P\exp[\,\cdot\,]\,\mathbf S_\text{pert}\,d\eta$. The collapse to $\Delta_\ell^T(k) = \int_0^{\eta_0} S_T\, j_\ell[k(\eta_0-\eta)]\,d\eta$ in the FLRW limit is not derived. This collapse is what R2 must produce.

2. **No identification of the BASS source assembly form.** §5/§8 describe the redshift source in covariant variables ($\delta\Theta$, $\delta A_a$, $\delta\sigma_{ab}$), but the BASS implementation form
   $$
   S_T(\eta) \;=\; g(\eta)\bigl[\Theta_0 + \Psi + \tfrac14 \Pi\bigr] + e^{-\kappa(\eta)}\bigl[\dot\Phi + \dot\Psi\bigr] + \frac{d}{d\eta}\bigl[g(\eta)\, v_b(\eta)\bigr]
   $$
   ([`flrw_bessel_projector.py:416–455`](../htt/bass/los/flrw_bessel_projector.py#L416)) is not stated.

3. **No ℓ = 0 frame audit.** §6's hierarchy gives ℓ = 0 evolution, but the relationship between PSTF radiation-frame $\Theta_0^\text{PSTF}$ and CAMB CDM-frame $\Delta_\gamma^\text{MB,S} = 4\Theta_0^\text{MB,S}$ (CDM rest = synchronous, per the CAMB-mapping doc §1, `clxg = I_0 = Δ_γ`) is not written down. Ellis–van Elst 1998 establishes gauge-invariance of $\ell \ge 1$ PSTF moments around FRW; the $\ell = 0$ statement, which depends on the choice of energy-flow vector, is needed but absent.

4. **No m = ±2 LoS source for non-trivial Bianchi.** §6 lists T7/T8/T9 in the *evolution*, but their imprint on the LoS *observable* — i.e. the $m = \pm 2$ contributions $\Delta_\ell^{T,\,m=\pm 2}(k)$ that vanish for FLRW / Bianchi-I but turn on for II–IX — is unwritten. The corresponding code module [`htt/bass/los/families/`](../htt/bass/los/families/) currently holds stub family backends.

5. **No code-mapping.** Equations cite module-level names (Tier-B, $\zeta_{ab}$, Π, etc.) but not file:line references in `htt/bass/`.

The reference's design philosophy ("background nonperturbative; fluctuation linear; recombination microphysics isotropic first-pass") is preserved by R2–R6.

### (c) Empirical state of the FLRW-limit BASS implementation post Round-15 P0

The §10 decisive test routes CAMB's exposed `T_source` (from `get_time_evolution(['T_source'])`) through BASS's existing `project_temperature_transfer` projector, then compares to CAMB's direct `delta_p_l_k`. Three columns of the test (`v5_round15_p0_d1_fix_transcript_2026-04-25.txt:33–46`) trace D-1 sensitivity:

- `uniform64`: pre-fix, integrator's 64-point uniform-linear η-grid (Δη ≈ 220 Mpc) reused as LoS quadrature grid;
- `k_adapted`: post-fix, per-k composite η-grid from [`los_grid_builder.py::build_los_grid`](../htt/bass/los/los_grid_builder.py) (recombination zone Δη ≈ 2.4 Mpc; oscillation zone Δη = 2π/(8k));
- `k_adapted_eta100`: post-fix, plus η_init artificially lifted from BASS's 261 Mpc to 100 Mpc using CAMB's source extension below η_init.

The dominant low-k cells in the `k_adapted_eta100` column give:

| $k$ [Mpc⁻¹] | $\ell$ | BASS·LoS / CAMB·direct |
|---:|---:|---:|
| $1\!\times\!10^{-3}$ | 2 | $+0.933$ |
| $1\!\times\!10^{-3}$ | 3 | $+0.984$ |
| $1\!\times\!10^{-2}$ | 2 | $+1.044$ |
| $1\!\times\!10^{-2}$ | 3 | $+0.999$ |

(transcript rows 35, 36, 38, 39, last column.)

These four cells are within 5% of unity. **At sub-recombination scales $k \le 10^{-2}\,\text{Mpc}^{-1}$, the BASS PSTF-to-observable LoS source assembly is structurally correct in the FLRW limit.** The post-D-1 `k_adapted` column without η_init lift gives ratios 0.028, 0.692, 0.832, 1.257 at the same four cells — recovering correct order of magnitude, with the residual at $\ell = 2, k = 10^{-3}$ traceable to D-2 (η_init truncation; the visibility carries $\sim 1$ FWHM of weight at η < 261 Mpc that BASS's PCHIP source extractor with `extrapolate=False` ([`tier_b_source_extraction.py:311`](../htt/bass/spectrum/tier_b_source_extraction.py#L311)) cannot reach).

At higher k the empirical record is muddied by two confounders:

- **The §10 oracle itself fails for $k > 10^{-2}$.** Routing CAMB's exposed `T_source` through CAMB's *own* full η-grid (30 000 trapezoidal samples on $[0.1, 14153]$ Mpc) versus CAMB's `delta_p_l_k` gives ratio $-0.2213$ at $k = 5\!\times\!10^{-2}, \ell = 2$ and $0.0001$ at $k = 8\!\times\!10^{-2}, \ell = 2$ (briefing §3.3). CAMB's internal `delta_p_l_k` uses additional refinements (RSA, second-order TCA, possibly Limber late-time projection) absent from the exposed `T_source`. Treating §10 as a high-k validation gate is therefore an artifact of CAMB introspection, not a BASS defect.
- **BASS's own η_init = 261 Mpc truncation.** The `k_adapted` column without lift gives sign flips at $5\!\times\!10^{-2}, \ell = 2$ (ratio $+0.059$) and large amplitude excursions at $\ell = 4$. These are confounded with confounder 1 above and cannot be cleanly attributed.

Resolution-independence of the post-fix grid is verified by an `n_per_oscillation × n_per_recomb_fwhm` sweep: ratios constant to four decimals at every $(k, \ell)$ cell across {8,16,32,64,128} × {8,16,32,64} (P0 summary §"Resolution-independence check"). The LoS projector + grid is now a *faithful quadrature* of any source supplied to it.

**Implication for R2.** The formalism R2 derives must reproduce ratios near unity at the four low-k cells listed above, and need *not* reproduce ratios near unity at $k \ge 3\!\times\!10^{-2}$ (because of confounder 1). R2's "consistency check" subsection should target the four-cell low-k panel as the empirical anchor.

### (d) The three open formalization gaps

Per briefing §4, restated and amplified with the file:line evidence collected above.

**Gap A — FLRW-limit LoS source from PSTF first principles (R2 target).** The lowell-bianchi reference §7 gives the formal matrix LoS on Bianchi but not its FLRW collapse to the BASS form. R2 must (i) start from the 1+3 covariant photon transport equation (Challinor–Lasenby 2000-I, eqs. (40)–(45) for the energy-integrated PSTF brightness moments); (ii) specialize to FLRW ($\sigma_{ab} = 0, A_a = 0$) and the $m = 0$ scalar mode; (iii) apply the LoS prescription (Seljak–Zaldarriaga 1996) including the integration by parts that converts $\dot\kappa\,e^{-\kappa}\,(\Phi - \Psi)$-type terms into the ISW driver $e^{-\kappa}(\dot\Phi + \dot\Psi)$; (iv) identify the four canonical contributions SW, ISW, Doppler, polter; (v) state explicitly the gauge / frame each of $\Theta_0, \Psi, \Phi, v_b, \Pi, g, e^{-\kappa}$ lives in; (vi) compare term-by-term to the BASS implementation [`flrw_bessel_projector.py::build_temperature_source`](../htt/bass/los/flrw_bessel_projector.py#L416) and to [`tier_b_source_extraction.py`](../htt/bass/spectrum/tier_b_source_extraction.py); and (vii) cross-validate with the MB-95 / Lewis–Challinor synchronous-gauge LoS source in the FLRW limit, demonstrating that the line-of-sight integral $\Delta_\ell^T = \int S_T\, j_\ell\, d\eta$ is gauge-invariant even where $S_T(\eta, k)$ is not pointwise.

**Gap B — ℓ = 0 monopole convention (R3 target).** The historical record on this point requires reconciliation:

- The Round-12 → 14 investigation summary at [`docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:199–233`](V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md#L199) diagnoses "D-3 synchronous / Newtonian gauge mismatch" with proposed fix $\Theta_0^N = \Theta_0^S + h_S'/6$ and labels `tier_b_source_extraction.py:225` `theta0_g = t_tower[:, _slot(0, 0)]` as "synchronous-gauge tower output". That diagnosis was framed in MB-95 abstract language; it does not transfer to BASS's PSTF-native production code, where no $h_S$ exists (verified by grep, §(a) above).
- The briefing §3.4 reframes the open question correctly: BASS's `t_tower[:, _slot(0,0)]` is an evolved PSTF radiation-frame quantity. The actual question is whether the assembly $g\bigl[\Theta_0^\text{PSTF} + \Psi^N + \tfrac14\Pi\bigr] + \dots$ is a gauge-coherent observable — i.e. whether the algebra of the PSTF hierarchy plus the ISW driver $\dot\Phi + \dot\Psi$ implicitly produces a frame-independent combination.

R3 must (i) trace `t_tower[:, _slot(0,0)]` from IC ([`seed_compatibility.py:151–212`](../htt/bass/hierarchy/seed_compatibility.py#L151)) through evolution ([`hierarchy_rhs.py:343–540`](../htt/bass/hierarchy/hierarchy_rhs.py#L343)) to readout ([`tier_b_source_extraction.py:225`](../htt/bass/spectrum/tier_b_source_extraction.py#L225)), identifying which gauge / frame each step assumes; (ii) write the PSTF-native transformation between $\Theta_0^\text{PSTF}$ (radiation rest frame, comoving), $\Theta_0^\text{MB,N}$ (Newtonian / longitudinal), and $\Theta_0^\text{MB,S}$ (CDM rest = synchronous = `clxg/4`) without introducing $h_S, \eta_s$ as primary; (iii) decide whether the BASS LoS assembly's $\Theta_0$ term needs a correction, or whether the $\Theta_0 + \Psi$ combination is a gauge-coherent observable by an algebraic identity of the PSTF hierarchy; and (iv) reconcile the verdict with the empirical low-k ratio $\approx 1$ from §(c).

**Gap C — Bianchi tetrad-frame extension blueprint (R4 target).** The reference §6/§7 give the abstract hierarchy and matrix LoS but leave four pieces unwritten: (i) the explicit T7/T8/T9 imprint on the LoS observable ($\sigma_{ab}\cdot\Theta_{ab}$-type contributions), starting from the verified FLRW-limit assembly produced by R2; (ii) the $m = \pm 2$ channel coupling, currently zero in BASS for FLRW / Bianchi-I, derived from the eigenstructure of $\sigma_{ab}$ for non-trivial Bianchi types — and how it couples back into the $m = 0$ LoS source; (iii) the tilted observer ($u_e^a \neq n^a$) statement of the LoS source seen by the CMB observer (lowell-bianchi reference §1.2, §12.2); and (iv) the Maartens–Ellis–Stoeger translation that connects the resulting tetrad-frame $\Delta_\ell$ to the master departure parameter $x_C = \Sigma^2_\text{std} - W^2_\text{std} + \Omega_\text{tilt} + \Omega_{k,\text{aniso}}$ (briefing §1.D3.d; Maartens–Gebbie–Ellis 1999; [`project/03_physics_notes/tomographic_MES_framework.md`](../project/03_physics_notes/tomographic_MES_framework.md)).

(Gaps D and E from briefing §4.4–§4.5 — high-k analytic oracle and master code-mapping — are the targets of R5 and R6. They are not formalization gaps in the same sense as A–C; they are deliverables that depend on A–C having been executed.)

### Open questions before R2

Three calibrated questions, each marking a decision point that R2 (or R3) must resolve early.

**Q1 — Frame of $v_b$ in the Doppler term.** The Doppler contribution $d/d\eta[g(\eta)\, v_b(\eta)]$ in [`build_temperature_source`](../htt/bass/los/flrw_bessel_projector.py#L416) draws `v_b` from `baryon_local_history[:, 1]` ([`tier_b_source_extraction.py:244–246`](../htt/bass/spectrum/tier_b_source_extraction.py#L244)). The IC at [`seed_compatibility.py:173, 193`](../htt/bass/hierarchy/seed_compatibility.py#L173) declares `theta_common = 0` in "synchronous-gauge super-horizon" notation. The runtime baryon RHS evolves under PSTF Thomson coupling to the photon dipole $\Theta_1$ (drag in tight coupling, free-streaming after decoupling). What frame does the *evolved* `v_b` then sit in — Newtonian-gauge baryon peculiar velocity, or PSTF baryon-fluid drift in the comoving rest frame? On FLRW the two coincide up to $O(k\eta)^2$ at super-horizon and exactly at sub-horizon (Maartens 1998 §III); R2 should make the choice explicit because the sign and prefactor of the Doppler term depend on it.

**Q2 — Π convention sign and the $\sqrt 6$ prefactor.** BASS uses $\Pi_\text{BASS} = \Theta_2 - \sqrt 6\, E_2$ ([`tier_b_source_extraction.py:234, 236`](../htt/bass/spectrum/tier_b_source_extraction.py#L234), Round-5 audit Q-20: "α_T = 1, α_E = −√6; no extra PSTF prefactor"). The CAMB-mapping doc §1 gives CAMB's `polter = pig/10 + 9*E(2)/15` with CAMB's $E_2$ sign-flipped versus theory literature, and Hu–White 1997 gives $\Pi_\text{HW} = \Theta_2 + E_0 + E_2$ in the total-angular-momentum basis. R2's term-by-term reconciliation must (i) verify the BASS PSTF combination against Challinor–Lasenby 2000-II (the reference for the polarization PSTF hierarchy and Thomson collision), (ii) confirm the $1/4$ prefactor in the $S_T$ assembly (i.e. whether $S_T \supset g\cdot \tfrac14 \Pi_\text{BASS}$ matches CAMB's $S_T \supset g \cdot \zeta_\text{CAMB}/$ [appropriate normalization]), and (iii) quote the sign convention explicitly.

**Q3 — Empirical anchor for R2's consistency check.** The four low-k cells in §(c) come from `k_adapted_eta100`, where CAMB sources are spliced in below BASS's $\eta_\text{init}$. The BASS-native pipeline cannot perform this splice (`extrapolate=False` PCHIP). For R2's consistency check, can the `k_adapted_eta100` numbers be treated as faithful to BASS's PSTF assembly *under the counterfactual that $\eta_\text{init}$ were lifted*, i.e. as a clean test of the LoS *assembly* with the η-coverage defect (D-2) factored out? Or should the consistency claim be softened to "the LoS projector and source-assembly are correct *given correct sources on the supplied η range*", deferring the $\eta_\text{init}$ extension to P2? The former gives R2 a stronger empirical anchor; the latter is more conservative. The briefing §3.5 implicitly endorses the former by treating P0 as having "delivered" structural correctness, but a one-line user direction here will fix the framing for R2's prose.

---

## R2. FLRW-limit PSTF LoS source — derivation from first principles

### Convention adopted (per user direction 2026-04-25)

R2 derives the LoS temperature source in **CAMB / Lewis–Challinor 2006 conventions** as the canonical baseline, then provides explicit conversion to PSTF / Hu–White 1997 / Kamionkowski–Kosowsky–Stebbins 1997 / Ma–Bertschinger 1995 conventions. CAMB is chosen because (i) it is the production-validated FLRW reference; (ii) the Round-15 §10 decisive test compares against CAMB's direct $\Delta_\ell^T(k)$, so reconciling BASS with CAMB at term level makes the empirical anchor in §3.1 of the briefing directly auditable; (iii) the synchronous ↔ Newtonian dictionary CAMB itself uses (MB-95 §V) gives the cleanest path for the gauge-invariance argument in §6 below.

**If the baseline shifts** to a different convention, the following changes downstream:
- *MB-95 synchronous gauge as primary*: SW becomes $\Theta_0^{(s)} - \tfrac12 h_s$ + similar combinations; ISW driver loses the explicit $\dot\Phi + \dot\Psi$ form and is reconstructed via $-\dot\eta_s + \tfrac{1}{6}\ddot h_s + \tfrac12\dot h_s$ (Hu–White 1997 §III); BASS does not expose $h_s, \eta_s$, so this baseline is unavailable for direct R3 trace.
- *Pure PSTF-native* (no Newtonian potentials): SW source recast as covariant $\delta\Theta + A_a$-type combinations (lowell §8); requires deriving the Newtonian potentials from constraint algebra in PSTF variables on the fly, duplicating the work `tier_b_source_extraction.py:275–302` already performs in MB-95 form.
- *Hu–White 1997 TAM basis*: polter reorganized as $\Pi_\text{HW} = \Theta_2 + \tilde E_2$ in TAM normalization; numerical prefactors in the Thomson collision differ; ℓ ≥ 1 results are equivalent up to basis transformation.

Adopting CAMB / LC06 fixes: (i) time variable conformal $\eta$, $\dot{\,} \equiv d/d\eta$; (ii) Newtonian-gauge metric $ds^2 = a^2[-(1+2\Psi)d\eta^2 + (1-2\Phi)\delta_{ij}dx^i dx^j]$ (MB-95 §V); (iii) photon temperature multipoles $\Theta_\ell = I_\ell^{(0)}/4 = F_{\gamma,\ell}^{\text{MB}}/4$ (CL2000-I eqs. 38, 44; CAMB-mapping doc §1); (iv) baryon velocity $v_b$ defined such that $\theta_b = k v_b$ (MB-95 §IV; for radiation $v_\gamma = 3\Theta_1$, `tier_b_source_extraction.py:254–259`); (v) Thomson scattering rate per conformal time $\dot\kappa = a n_e \sigma_T$, optical depth $\kappa(\eta) = \int_\eta^{\eta_0}\dot\kappa\, d\eta'$, visibility $g(\eta) = \dot\kappa\, e^{-\kappa}$, normalized $\int_0^{\eta_0} g\, d\eta = 1 - e^{-\kappa(0)} \to 1$.

### §1. PSTF radiation transport in the FLRW limit, m = 0 scalar mode

The 1+3 covariant photon intensity hierarchy (Challinor–Lasenby 2000-I eq. 38) in position space is

$$
\dot I_{A_\ell} + \tfrac{4}{3}\Theta\, I_{A_\ell} + D^b I_{b A_\ell} - \frac{\ell}{2\ell+1} D_{\langle a_\ell} I_{A_{\ell-1}\rangle} + \tfrac{4}{3} I\, A_{a_1}\delta_{\ell 1} - \tfrac{8}{15} I\, \sigma_{a_1 a_2}\delta_{\ell 2} = -n_e\sigma_T\bigl[\,I_{A_\ell} - \tfrac{4}{3} I\, v_{a_1}\delta_{\ell 1} - \tfrac{2}{15}\zeta_{a_1 a_2}\delta_{\ell 2}\bigr].
\tag{R2.1.0}
$$

In the FLRW limit set $\sigma_{ab} = 0,\; A_a = 0,\; \omega_a = 0$. Specialize to scalar (m = 0) modes by Fourier-decomposing along comoving $k$ and projecting against the scalar harmonic $Q_k^{(0)}$ (CL2000-I §3.2). The $D$-derivatives reduce to Fourier multipliers with the angular-momentum coefficients $\ell/(2\ell+1)$ for the gradient and $(\ell+1)/(2\ell+1)$ for the divergence (CAMB-mapping doc §4.3). With $\Theta_\ell = I_\ell^{(0)}/4$, and adding the gravitational back-reaction from the photon geodesic in the perturbed Newtonian-gauge metric (MB-95 §IV-B, the source terms $-\dot\Phi$ at ℓ=0 and $+\tfrac{k}{3}\Psi$ at ℓ=1 from the perturbed redshift along the geodesic), the temperature hierarchy becomes:

$$
\dot\Theta_0 + \frac{k}{3}\Theta_1 = -\dot\Phi,
\tag{R2.1.1}
$$

$$
\dot\Theta_1 - \frac{k}{3}\Theta_0 + \frac{2k}{3}\Theta_2 = \frac{k}{3}\Psi - \dot\kappa\bigl[\Theta_1 - \tfrac{1}{3}v_b\bigr],
\tag{R2.1.2}
$$

$$
\dot\Theta_\ell + \frac{k(\ell+1)}{2\ell+1}\Theta_{\ell+1} - \frac{k\ell}{2\ell+1}\Theta_{\ell-1} = -\dot\kappa\bigl[\Theta_\ell - \tfrac{1}{10}\Pi\,\delta_{\ell 2}\bigr] \quad(\ell\ge 2).
\tag{R2.1.3}
$$

The polter $\Pi$ is the combined temperature/polarization quadrupole source (§3 below). The corresponding E-mode hierarchy (KKS97; CL2000-II) takes the same free-streaming structure with E-mode coefficients and Thomson source $-\tfrac{\sqrt 6}{10}\Pi\,\delta_{\ell 2}$ for $E_\ell$ — identifying the eigenvector $\Pi = \Theta_2 - \sqrt 6\, E_2$ as the PSTF polter (§3 below).

The BASS production hierarchy [`hierarchy_rhs.py:343–540`](../htt/bass/hierarchy/hierarchy_rhs.py#L343) implements R2.1.0 — i.e., the position-space 9-term form, restricted to T1 + T7/T8/T9 + T_collision in the FLRW / Bianchi-I limit (T7/T8/T9 carry $\sigma_{ab}\ne 0$ and vanish in FLRW). The harmonic-space reductions R2.1.1–R2.1.3 are equivalent to BASS's evolution for FLRW; verification is the (2ℓ+1)/4 normalization conversion CAMB-mapping doc §5.1.

### §2. Line-of-sight integration prescription and the integration-by-parts that produces ISW

Following Seljak–Zaldarriaga 1996 (eq. 8–11), the formal integral solution to the photon Boltzmann equation along a null geodesic, projected onto multipoles in $\hat k$, gives

$$
\Delta_\ell^T(k) = \int_0^{\eta_0} d\eta\, S_T(\eta, k)\, j_\ell\bigl[k(\eta_0 - \eta)\bigr],
\tag{R2.2.1}
$$

where $S_T$ is the assembled LoS source. The path from R2.1.1–R2.1.3 to R2.2.1 uses three steps.

*Step (a) — formal integral solution to the dipole equation.* Multiply R2.1.2 by $e^{-\kappa(\eta)}$ and integrate from 0 to $\eta_0$. The Thomson collision integrand $\dot\kappa\, e^{-\kappa}\bigl[\Theta_1 - \tfrac13 v_b\bigr]$ becomes $g(\eta)\bigl[\Theta_1 - \tfrac13 v_b\bigr]$ inside the integral. The streaming and metric source terms produce the SW combination $g\,(\Theta_0 + \Psi)$ via the matching $\dot\kappa\, \Psi = -\dot\Psi + d/d\eta(\Psi) + \dot\kappa\Psi$ used in the Boltzmann equation as a Newtonian-gauge variable. (Lewis–Challinor 2006 §4.2, eqs. 4.10–4.18; the explicit step-by-step manipulation for arbitrary $\ell$ uses the Bessel recurrence to absorb $j_\ell'$ contributions.)

*Step (b) — integration by parts producing ISW.* The monopole equation R2.1.1 has a source $-\dot\Phi$ on the right-hand side. After the formal integral, this contributes a term $\int_0^{\eta_0} e^{-\kappa}\,\dot\Phi\, j_\ell\, d\eta$ to $\Delta_\ell^T$. By symmetry of the perturbed metric source between the monopole ($-\dot\Phi$) and the dipole ($+\tfrac{k}{3}\Psi$), and applying integration by parts using $\dot\kappa\,e^{-\kappa} = -\frac{d}{d\eta}e^{-\kappa}$, one obtains

$$
\int_0^{\eta_0} d\eta\, \dot\kappa\,e^{-\kappa}\Psi\, j_\ell + \int_0^{\eta_0}d\eta\, e^{-\kappa}\dot\Phi\, j_\ell \;=\; \int_0^{\eta_0}d\eta\, \bigl\{g\,\Psi + e^{-\kappa}(\dot\Phi + \dot\Psi)\bigr\}\, j_\ell + \text{(boundary)},
\tag{R2.2.2}
$$

with the boundary terms $[e^{-\kappa}(\Phi+\Psi) j_\ell]_0^{\eta_0}$ vanishing for $\ell \ge 1$ ($j_\ell(0) = 0$) and contributing only to $\ell = 0$ (an irrelevant monopole offset). The combination $e^{-\kappa}(\dot\Phi + \dot\Psi)$ on the right-hand side is the **integrated Sachs–Wolfe driver**.

*Step (c) — Doppler integration by parts.* The dipole's $v_b$ Thomson source produces an integrand of the form $g(\eta)\, v_b(\eta)\, j_\ell'\bigl[k(\eta_0 - \eta)\bigr]$. Using

$$
j_\ell'\bigl[k(\eta_0 - \eta)\bigr] = -\frac{1}{k}\frac{d}{d\eta} j_\ell\bigl[k(\eta_0 - \eta)\bigr],
\tag{R2.2.3}
$$

integrate by parts:

$$
\int_0^{\eta_0} g\, v_b\, j_\ell'\, d\eta = \frac{1}{k}\int_0^{\eta_0} \frac{d(g v_b)}{d\eta}\, j_\ell\, d\eta - \frac{1}{k}\bigl[g v_b\, j_\ell\bigr]_0^{\eta_0}.
\tag{R2.2.4}
$$

The boundary term vanishes ($g(0) = g(\eta_0) = 0$ in the recombination-only treatment; for reionization, $g$ has a second peak interior to $[0,\eta_0]$ but $g(\eta_0) = 0$ remains). The Doppler contribution to $S_T$ is therefore $\tfrac{1}{k}(g v_b)'$ with the **explicit $1/k$ factor**.

### §3. The four physical contributions; polter convention

Assembling (a)–(c) yields the canonical CAMB / LC06 form:

$$
\boxed{\;
S_T(\eta, k) = \underbrace{g(\eta)\bigl[\Theta_0 + \Psi + \tfrac{1}{4}\Pi\bigr]}_{\text{SW + polter}} + \underbrace{e^{-\kappa(\eta)}\bigl[\dot\Phi + \dot\Psi\bigr]}_{\text{ISW}} + \underbrace{\frac{1}{k}\frac{d}{d\eta}\bigl[g(\eta)\, v_b(\eta)\bigr]}_{\text{Doppler}}.
\;}
\tag{R2.3.1}
$$

A higher-order polter correction $-\tfrac{3}{4k^2}(g\Pi)''$ is generated by the same procedure at second order and is conventionally absorbed into the $g\,\tfrac14 \Pi$ term via the Bessel recurrence $j_\ell'' + 2j_\ell'/x + [1 - \ell(\ell+1)/x^2]j_\ell = 0$ (Lewis–Challinor 2006 §4.4). This absorption is exact only modulo terms of order $(g\Pi/k\eta_0)$ that are negligible at sub-recombination scales. BASS adopts the absorbed form (no explicit $1/k^2$ term in the source).

**Polter $\Pi$ — sign and $\sqrt 6$ prefactor verification.** The Thomson collision tensor in CL2000-II eq. 12 reads $\zeta_{ab} = \tfrac{3}{4} I_{ab} + \tfrac{9}{2} E_{ab}$. After harmonic decomposition in PSTF E/B basis, the (T,E) sub-block of the Thomson collision matrix at $\ell = 2$ has the structure (lowell §9.2):

$$
M_{\text{(T,E)}} = \begin{pmatrix} 9/10 & \sqrt 6/10 \\ \sqrt 6/10 & 2/5 \end{pmatrix},
\qquad \frac{d}{d\tau}\begin{pmatrix}\Theta_2 \\ E_2\end{pmatrix} = -\Gamma_T\, M_{\text{(T,E)}}\begin{pmatrix}\Theta_2 \\ E_2\end{pmatrix}.
$$

Eigenvalues (verified numerically; see P1.5-E for full derivation): $\lambda = 1$ and $\lambda = 3/10$. The relaxation eigenvectors are

$$
\Pi^{\text{PSTF}} \;\equiv\; \Theta_2 - \sqrt 6\, E_2 \quad (\text{slow eigenmode, rate } (3/10)\Gamma_T),
\qquad \Pi^{\text{fast}} \;\equiv\; \sqrt 6\, \Theta_2 + E_2 \quad (\text{fast eigenmode, rate } \Gamma_T).
\tag{R2.3.2}
$$

*(R8 audit-correction 2026-04-25: the previous draft incorrectly stated the eigenvalues as $\{9/10, 0\}$ with $\Pi$ as the "9/10 relaxation eigenmode". The 9/10 is the diagonal Θ₂-only relaxation rate in the *decoupled* limit (i.e., setting $E_2 = 0$ artificially, the Θ₂ collision becomes $-\Theta_2 + (1/10)\Theta_2 = -(9/10)\Theta_2$, hence the diagonal entry $9/10$ in $M_{\text{(T,E)}}$ above), which is distinct from the coupled-system eigenvalue. The polter $\Pi$ relaxes at $(3/10)\Gamma_T$ in the coupled (T,E) system, NOT $(9/10)\Gamma_T$. The slow relaxation rate is what allows polarization to persist long enough during recombination for observable E-mode generation. The orthogonal eigenmode $\sqrt 6\,\Theta_2 + E_2$ relaxes at full Thomson rate $\Gamma_T$, not 0 as claimed previously. Full derivation in P1.5-E.)*

The factor $\sqrt 6$ is the off-diagonal coupling in the (T,E) sub-block — it arises algebraically from the spin-2 lowering coefficient $\sqrt{(\ell-1)\ell(\ell+1)(\ell+2)} = \sqrt{24} = 2\sqrt 6$ at $\ell = 2$, divided by 2 for the angular-momentum normalization. The Thomson source at ℓ = 2 in the temperature track is $\tfrac{1}{10}\Pi$; in the E track it is $-\tfrac{\sqrt 6}{10}\Pi$ (CL2000-II §3.2). This is the BASS convention (Round-5 audit Q-20: $\alpha_T = +1,\ \alpha_E = -\sqrt 6$, no extra PSTF prefactor; [`tier_b_source_extraction.py:234`](../htt/bass/spectrum/tier_b_source_extraction.py#L234)).

Cross-convention table:

| Convention | Polter / scattering source | Reference |
|---|---|---|
| **PSTF / CL2000-II / BASS** | $\Pi^{\text{PSTF}} = \Theta_2 - \sqrt 6\, E_2$; $S_T \supset g \cdot \tfrac{1}{4}\Pi$ | CL2000-II eq. 12; `tier_b_source_extraction.py:234` |
| **Hu–White 1997 (TAM)** | $\Pi^\text{HW} = \Theta_2 + \tilde E_2$ in total-angular-momentum basis | HW97 §III.A, eq. 25 |
| **CAMB (LC06)** | $\zeta = 3\Theta_2 + \tfrac{9}{2} E_2^{\text{CAMB}}$; `polter = pig/10 + 9*E(2)/15` | LC06 §4; CAMB-mapping doc §1 |
| **KKS97 (E/B harmonic)** | $a_{\ell 0}^E$ projected against $_{\pm 2}Y_{\ell 0}$; sign convention via parity | KKS97 eqs. 38–39 |

**Sign relations.** CAMB's $E_2^{\text{CAMB}}$ has a sign opposite to the PSTF / theory-literature $E_2$ (CAMB-mapping doc §1.1; CL2000-II "polarization sign convention" note). With this sign flip and the (2ℓ+1)/4 multipole rescaling, $E_2^{\text{CAMB}} = -\tfrac{2}{5} E_2^{\text{PSTF}}/\sqrt 6$ (verifying $\zeta = 3\Theta_2 - \tfrac{9}{2}\cdot\tfrac{2}{5\sqrt 6}E_2^{\text{PSTF}} \times 4 = $ algebraic match to $4 \cdot \tfrac{1}{10}\Pi^{\text{PSTF}} \cdot 15$ at the appropriate $\zeta/15$ normalization; the full normalization audit at line-precision is left for R6 if numerical reconciliation requires it). The HW97 TAM amplitude $\tilde E_2$ relates to $E_2^{\text{PSTF}}$ by a $\sqrt{(\ell-1)(\ell+2)}/(2\ell+1)$ Wigner-d factor, which at $\ell = 2$ is $\sqrt 4 / 5 = 2/5$ (HW97 eq. 22).

### §4. Assembled $S_T(\eta, k)$ — gauge / frame of each variable

Restated explicitly with frame annotations:

| Symbol | Meaning | Gauge / frame | BASS data source |
|---|---|---|---|
| $\Theta_0(\eta,k)$ | Photon temperature monopole | Newtonian-longitudinal gauge | `t_tower[:, _slot(0,0)]` from PSTF integrator (R3 audit target) |
| $\Psi(\eta,k)$ | Newtonian gauge lapse perturbation | Newtonian gauge | `tier_b_source_extraction.py:302` (Einstein constraint) |
| $\Phi(\eta,k)$ | Newtonian gauge spatial-curvature potential | Newtonian gauge | `tier_b_source_extraction.py:291` (Einstein constraint) |
| $v_b(\eta,k)$ | Baryon peculiar velocity, $\theta_b = k v_b$ | Newtonian-gauge baryon rest frame | `baryon_local_history[:, 1]` (see §5 below) |
| $\Pi(\eta,k)$ | $\Theta_2 - \sqrt 6\, E_2$ (PSTF polter) | PSTF E/B basis (CL2000-II) | `tier_b_source_extraction.py:236` |
| $g(\eta)$ | Visibility $\dot\kappa\, e^{-\kappa}$ | Background scalar | `bass.transport.visibility_polter_source` |
| $e^{-\kappa(\eta)}$ | Optical-depth weight | Background scalar | as above |

The four contributions of R2.3.1 — SW $g\Theta_0$, sourced potential $g\Psi$, polter $g\Pi/4$, ISW $e^{-\kappa}(\dot\Phi+\dot\Psi)$, and Doppler $(g v_b)'/k$ — together constitute the canonical FLRW LoS source.

### §5. Term-by-term comparison with BASS implementation

BASS [`build_temperature_source`](../htt/bass/los/flrw_bessel_projector.py#L416) assembles

$$
S_T^{(\text{BASS})}(\eta,k) = g\bigl[\Theta_0 + \Psi + \tfrac14 \Pi\bigr] + e^{-\kappa}\bigl[\dot\Phi+\dot\Psi\bigr] + \frac{d}{d\eta}\bigl[g\,v_b\bigr].
\tag{R2.5.1}
$$

(`flrw_bessel_projector.py:448–453`. The downstream projector at line 499 forms $\Delta_\ell^T = \int S_T j_\ell\, d\eta$ with no implicit $1/k$ factor.) Term-by-term:

| Term | R2.3.1 | BASS R2.5.1 | Verdict |
|---|---|---|---|
| SW + polter | $g[\Theta_0 + \Psi + \tfrac14\Pi]$ | $g[\Theta_0 + \Psi + \tfrac14\Pi]$ | ✓ identical |
| ISW | $e^{-\kappa}(\dot\Phi+\dot\Psi)$ | $e^{-\kappa}(\dot\Phi+\dot\Psi)$ | ✓ identical |
| Doppler | $\tfrac{1}{k}(g v_b)'$ | $(g v_b)'$ | △ **Audit Finding 1** |

**§5 Audit Finding 1 — Doppler $1/k$ factor — RESOLVED 2026-04-25 post-R7.** The canonical CAMB / LC06 form has $\tfrac{1}{k}(g v_b)'$ in the Doppler source; BASS has $(g v_b)'$. The post-R7 inspection of `ver2_native_integrator.py` (uploaded by user 2026-04-25) confirms that **BASS is missing the factor $1/k$**. Smoking-gun evidence:

(a) [`ver2_native_integrator.py:3086`](../ver2_native_integrator.py#L3086) declares the `_LocalMatterHistory.baryon_labels` tuple as `("delta_b", "v_b", "v_e", "drag_lock_residual")` — slot 1 is explicitly labelled `v_b` (velocity), slot 2 is `v_e` (electron velocity), not $\theta_b$.

(b) [`ver2_native_integrator.py:3047–3052`](../ver2_native_integrator.py#L3047) implements the predictor-corrector update of `baryon_state.v_b` with `forcing = 3 * drag * theta_1`. In MB-95 sync gauge the baryon-velocity equation reads $\dot v_b + (\mathcal H + \tau'/R_b) v_b = (\tau'/R_b)\, v_\gamma$ with $v_\gamma = 3\Theta_1$; in MB-95 *divergence* convention it would be $\dot\theta_b + \cdots = (\tau'/R_b)\,(3 k \Theta_1)$. The code's forcing is $3\Theta_1$, not $3k\Theta_1$, confirming velocity convention.

(c) [`ver2_native_integrator.py:2974–2980`](../ver2_native_integrator.py#L2974) populates `baryon_history[idx, :]` with `(delta_b, v_b, v_b, 3*theta_1 - v_b)`. The slot-3 entry $3\Theta_1 - v_b$ is the slip $v_\gamma - v_b$ in physical-velocity convention; if $v_b$ were $\theta_b = k v_b^{\text{phys}}$, slot 3 would have to be $3k\Theta_1 - \theta_b$, which fails dimensional consistency.

The misleading dict key `_matter_seed_observables["theta_b"]` (line 1573) is a legacy naming holdover; the value stored is the physical velocity $v_b^{\text{phys}}$. Therefore $S_T^{(\text{BASS})}$ at [`flrw_bessel_projector.py:453`](../htt/bass/los/flrw_bessel_projector.py#L453) is short the canonical $1/k$ factor.

**Code fix specified.** One-line change at `flrw_bessel_projector.py:453`:
```python
doppler = np.gradient(gvb, eta_grid, edge_order=2) / k   # /k: canonical CAMB Doppler
```
The signature of `build_temperature_source` (currently lines 416–421) does not expose $k$; the fix requires either (i) adding a `k_comoving: float` argument to `build_temperature_source` and threading it from the projector caller at `:499`, or (ii) deferring the $/k$ division to the projector at `:499` and feeding `(g v_b)'` as a "Doppler-numerator" rather than a final source.

**Empirical impact — anchor rerun required (R10 audit-correction 2026-04-25)**. Previous drafts claimed: "the four-cell low-$k$ empirical anchor is unaffected because Doppler contributes < 0.5% of the LoS source per the Round-12→14 ablation". This claim is incomplete and must be retracted as written. The pre-fix Doppler is $(g v_b)'$, the post-fix is $(g v_b)'/k$, so the AF-1 fix amplifies the Doppler term by a factor $1/k$. At the four anchor cells:

| $(k, \ell)$ | Pre-fix Doppler / total | Post-fix Doppler / total (naive upper bound) |
|---|---:|---:|
| $(10^{-3}, 2)$ | $< 0.5\%$ | $< 500\%$ (naive: ×1000) |
| $(10^{-3}, 3)$ | $< 0.5\%$ | $< 500\%$ |
| $(10^{-2}, 2)$ | $< 0.5\%$ | $< 50\%$ (naive: ×100) |
| $(10^{-2}, 3)$ | $< 0.5\%$ | $< 50\%$ |

The naive upper bounds above are *not* the expected post-fix values — physical $v_b \propto k$ scaling on super-horizon scales, plus Bessel-projection cancellations between the IBP-generated $j_\ell'$ and the velocity profile, will reduce the actual post-fix contribution substantially. But the actual post-fix value is **not bounded by the pre-fix ablation**, and the four-cell anchor must be **re-run after the code fix lands** to verify the "monopole-frame correction not needed at 5%" verdict carries through.

This is the most important deliverable from R10's audit cycle: the empirical anchor must be regenerated, not just inherited. The formula audit point is real, the code fix is one line, and the four-cell rerun is the verdict-preservation test that becomes mandatory after the fix. R5 Oracle 5 (R5.5.1) provides the isolated regression that would have caught this independently.

**Why $\ell \geq 1$ PSTF multipoles are gauge-invariant on FRW (Ellis–van Elst 1998).** The FLRW background satisfies $\nabla_a \rho = 0$, $\nabla_a \Theta = 0$ (Stewart–Walker lemma; Ellis–van Elst 1998 §B.2). The PSTF moments $I_{A_\ell}$ are tensors of rank $\ell$. Under an infinitesimal gauge transformation $x^a \to x^a + \xi^a$, the change is $\delta_\xi I_{A_\ell} = \mathcal L_\xi \bar I_{A_\ell}$ where $\bar I_{A_\ell}$ is the background. For $\ell \ge 1$, $\bar I_{A_\ell} = 0$ on FRW (no preferred direction in background isotropy), hence $\delta_\xi I_{A_\ell} = 0$ to first order — i.e., $\Theta_\ell$ for $\ell \ge 1$ is gauge-invariant. The $\ell = 0$ moment carries $\bar I_0 = 4 \bar T \neq 0$ and is gauge-dependent: $\delta_\xi \Theta_0 = -\xi^0\,\bar T'/\bar T = -\mathcal H \xi^0$ (MB-95 §V eq. 27a). This is the structural reason ℓ = 0 needs the dedicated R3 audit while ℓ ≥ 1 reduces transparently.

### §6. Cross-validation: synchronous-gauge LoS source and gauge-invariance of $\Delta_\ell^T$

In MB-95 synchronous gauge, the LoS source has the equivalent form (MB-95 §VIII eq. 73; Hu–White 1997 §III; CAMB-notes eq. 4.20 in synchronous variables):

$$
S_T^{(s)}(\eta, k) = g\bigl[\Theta_0^{(s)} + \tfrac14 \Pi\bigr] + e^{-\kappa}\bigl[\dot\eta_s - \tfrac{1}{6}\ddot h_s\bigr] + \frac{1}{k}\bigl(g v_b^{(s)}\bigr)' + \cdots
\tag{R2.6.1}
$$

The Newtonian-gauge potentials are recovered from the synchronous metric via the gauge transformation $\alpha = (\dot h_s + 6\dot\eta_s)/(2k^2)$ (MB-95 eq. 27c):

$$
\Phi = \eta_s - \mathcal H\, \alpha, \quad \Psi = \dot\alpha + \mathcal H\,\alpha, \quad \Theta_0^{(N)} = \Theta_0^{(s)} + \alpha\, \mathcal H = \Theta_0^{(s)} + \frac{\dot h_s + 6\dot\eta_s}{2 k^2}\mathcal H,
\tag{R2.6.2}
$$

with $v_b^{(N)} = v_b^{(s)} + k\alpha$. Substituting R2.6.2 into R2.3.1 yields R2.6.1 plus terms of the form $g(\Psi - \mathcal H \alpha)$ and $e^{-\kappa}(\dot\Phi - \dot{(\mathcal H\alpha)} + \cdots)$ which combine via the constraint algebra to the synchronous LoS form. The pointwise integrand $S_T(\eta, k)$ is *not* the same in the two gauges: SW has a different decomposition, ISW is recast in $\eta_s, h_s$, Doppler picks up $k\alpha$ from the velocity transformation.

**Gauge-invariance of $\Delta_\ell^T$.** Despite pointwise differences in $S_T$, the integral

$$
\Delta_\ell^T(k) = \int_0^{\eta_0} S_T(\eta, k)\, j_\ell\bigl[k(\eta_0 - \eta)\bigr]\, d\eta
\tag{R2.6.3}
$$

is gauge-invariant. The standard proof (Hu–White 1997 §III; Lewis 2000 §3): under a gauge change parameterized by $\xi^0$, the integrand acquires $\delta_\xi(S_T j_\ell) = \xi^0 \cdot d/d\eta[(\text{combination of }\Theta_0, \Psi, v_b) j_\ell] + (\text{frame-rotation terms vanishing for scalar modes})$. The total derivative integrates to a boundary term $[(\text{combination})\cdot j_\ell]_0^{\eta_0}$, which vanishes for $\ell \ge 1$ via $j_\ell(0) = 0$ at $\eta = \eta_0$ and via the visibility / optical-depth decay at $\eta = 0$. The $\ell = 0$ boundary contribution is an irrelevant monopole offset.

This gauge-invariance is the structural reason BASS (PSTF assembly with Newtonian-gauge potentials reconstructed from constraints) and CAMB (synchronous-gauge throughout) produce the same $\Delta_\ell^T$ in the FLRW limit, modulo the Doppler $1/k$ point in §5 and the polter convention reconciliation in §3.

### §7. Consistency check (briefing R2 final paragraph; weak form per user direction)

The empirical evidence (briefing §3.1; transcript [`v5_round15_p0_d1_fix_transcript_2026-04-25.txt`](audits/v5_round15_p0_d1_fix_transcript_2026-04-25.txt) rows 35, 36, 38, 39, `k_adapt_η100` column):

| $(k\,[\text{Mpc}^{-1}], \ell)$ | BASS·LoS / CAMB·direct | R2 prediction |
|---|---:|---|
| $(10^{-3}, 2)$ | $+0.933$ | $\approx 1$, consistent |
| $(10^{-3}, 3)$ | $+0.984$ | $\approx 1$, consistent |
| $(10^{-2}, 2)$ | $+1.044$ | $\approx 1$, consistent |
| $(10^{-2}, 3)$ | $+0.999$ | $\approx 1$, consistent |

**Weak-form claim** (per user direction 2026-04-25): R2 establishes that *the BASS LoS projector and source-assembly are correct given correct sources on the supplied η range*. Specifically, R2.5.1 and R2.3.1 agree term-by-term modulo the Doppler $1/k$ point flagged in §5 (which is empirically below the test sensitivity at every cell in the table). The four-cell low-$k$ panel uses the `k_adapted_eta100` column where CAMB sources are spliced in below BASS's $\eta_\text{init}$ via an external lift; under that counterfactual the LoS assembly produces ratios within 5% of CAMB. The high-$k$ residual ($k \ge 3\!\times\!10^{-2}$) is contaminated by both the §10 CAMB-introspection limit (briefing §3.3) and BASS's $\eta_\text{init}$ truncation (briefing §3.2) and is not a clean R2 anchor; extending the validation past $k = 10^{-2}$ requires the analytic oracles produced in R5.

The η-range correctness is the deferred half: R2 does *not* claim the BASS-native pipeline produces correct sources below $\eta_\text{init} = 261$ Mpc. That question is the Round-15 P2 track (D-2 integrator $\eta_\text{init}$ extension, multi-month).

---

## R3. ℓ = 0 monopole convention audit

R2 established that BASS's LoS assembly matches the canonical CAMB / LC06 form term-by-term modulo Audit Finding 1 (the Doppler $1/k$). R3 audits the deeper question raised by briefing §4.2: BASS evolves the photon hierarchy in PSTF / 1+3 covariant variables, but the LoS source mixes these with Newtonian-gauge potentials reconstructed from Einstein constraints. Is the assembly silently gauge-mixed? If so, by how much, and why does the empirical match at low $k$ work?

### §1. Code-chain trace of $\Theta_0^{\text{BASS}}$

Four steps connect the IC to the LoS readout:

**Step 1 — IC at $\eta_\text{init}$** ([`seed_compatibility.py:151–212`](../htt/bass/hierarchy/seed_compatibility.py#L151)). With `adiabatic=True`, the seed assigns $\delta_\gamma : \delta_b : \delta_c : \delta_\nu = 4/3 : 1 : 1 : 4/3$ with $\theta_\text{common} = 0$. The docstring (line 173) labels these "synchronous-gauge super-horizon", but on $k\eta_\text{init} \ll 1$ the regular adiabatic mode is gauge-invariant up to terms of order $(k\eta_\text{init})^2$ (Maartens 1998 §III; MB-95 §VI). At $\eta_\text{init} = 261$ Mpc and the lowest mode $k = 10^{-4}$ Mpc⁻¹, $k\eta_\text{init} \approx 0.026$, so the residual gauge-dependence is $\le 0.1\%$ at IC. **Frame at IC: gauge-invariant (super-horizon adiabatic limit).**

**Step 2 — PSTF evolution** ([`hierarchy_rhs.py:343–540`](../htt/bass/hierarchy/hierarchy_rhs.py#L343)). The photon RHS sums

$$
\dot\Pi_{A_\ell} = -a\bigl[T_1 + T_2 + T_3 + T_7 + T_8 + T_9\bigr] + a\,K_T,
\tag{R3.1.1}
$$

where $T_1$ uses the *background* expansion $\bar\Theta = 3H$ (`background.Theta`, line 416), $T_2/T_3$ are the harmonic gradient/divergence with `nabla_operator`, $T_7/T_8/T_9$ carry $\sigma_{ab}$ (zero on FLRW), and $K_T$ is the Thomson collision. **Critically, no $\dot\Phi$, $\dot\Psi$, $h_s$, or any metric-perturbation source enters R3.1.1.** A grep across `htt/bass/hierarchy/` for any metric-source symbol (`Phi`, `phi_dot`, `psi_dot`, `Psi`, `metric_source`, `grav_source`, `h_dot`, `isw`) returns zero matches. The PSTF photon hierarchy in BASS is structurally a *free-streaming + Thomson* hierarchy with no gravitational back-reaction in the photon equations. **Frame during evolution: a PSTF $n^a$-frame quantity defined operationally by R3.1.1.**

**Step 3 — Storage** ([`integrator.py:231, 244`](../htt/bass/hierarchy/integrator.py#L223)). The evolved tower is packed into `photon_T_tower` of shape `(N_eta, (L+1)²)` on the real-spherical-harmonic basis $i = \ell^2 + (m+\ell)$. **Frame at storage: same as evolution, $n^a$-frame PSTF.**

**Step 4 — Readout** ([`tier_b_source_extraction.py:225`](../htt/bass/spectrum/tier_b_source_extraction.py#L225)). `theta0_g = t_tower[:, _slot(0,0)]` is read directly with **no gauge transformation applied**. This $\Theta_0^{\text{BASS}}$ is then plugged unchanged into the LoS source assembly at [`flrw_bessel_projector.py:448`](../htt/bass/los/flrw_bessel_projector.py#L448), where it is combined with the Newtonian-gauge $\Psi$ from Einstein-constraint reconstruction.

### §2. PSTF-native frame algebra for the $\Theta_0$ conventions

Three frames are relevant. PSTF-native algebra characterizes them by the choice of timelike unit vector $u^a$ defining the local rest frame for the photon energy-momentum decomposition (Ellis–van Elst 1998 §B; Tsagas–Challinor–Maartens 2008 §3):

| Frame | $u^a$ identification | Photon momentum density $q_a^{(\gamma)}$ | Naming |
|---|---|---|---|
| **Newtonian / longitudinal** | static observer at fixed comoving spatial coords | $q_a^{(\gamma)} = \rho_\gamma v_\gamma^{(N)}$ | Θ_0^(N) |
| **CDM rest = synchronous** | comoving with CDM congruence ($v_c = 0$) | $q_a^{(\gamma)} = \rho_\gamma v_\gamma^{(s)}$ | Θ_0^(s) |
| **PSTF kinematic ($n^a$)** | normal to homogeneous slicing in BASS | $q_a^{(\gamma)} = \rho_\gamma v_\gamma^{(\text{kin})}$ | Θ_0^(kin) |

The transformation between frames is a velocity boost, but $\Theta_0$ as the *monopole* of the angular distribution is invariant under boosts at first order in velocity (boost-induced shifts are $O(v^2)$ Doppler corrections to the monopole). What does shift $\Theta_0$ at first order is the *time-slicing* ambiguity: the residual coordinate freedom $x^a \to x^a + \xi^a$ that takes one slicing into another. For the Newt ↔ sync slicing change, the slicing parameter is

$$
\alpha(\eta, k) \;\equiv\; \xi^0_{(s\to N)}(\eta, k)
\tag{R3.2.1}
$$

which, in PSTF-native algebra (avoiding $h_s, \eta_s$ as primary variables), is identifiable with the Newtonian-gauge CDM peculiar velocity:

$$
\boxed{\;\alpha(\eta, k) = \frac{v_c^{(N)}(\eta, k)}{k}\;}
\tag{R3.2.2}
$$

Derivation: the comoving CDM congruence by definition has zero peculiar velocity in synchronous gauge ($v_c^{(s)} = 0$). In Newtonian gauge it has velocity $v_c^{(N)}$. The two are related by the slicing transformation $v_c^{(N)} = v_c^{(s)} + k\alpha = k\alpha$, giving R3.2.2. (Equivalently, MB-95 eq. 27c gives $\alpha = (\dot h_s + 6\dot\eta_s)/(2k^2)$, but that expression makes $h_s, \eta_s$ primary, which the briefing forbids.) Substituting R3.2.2 into the standard MB-95 §V transformation rules yields the PSTF-native versions:

$$
\Theta_0^{(s)} = \Theta_0^{(N)} - \mathcal H\,\frac{v_c^{(N)}}{k}, \qquad
v_b^{(s)} = v_b^{(N)} - v_c^{(N)}, \qquad
\delta_\gamma^{(s)} = \delta_\gamma^{(N)} - 4\mathcal H\,\frac{v_c^{(N)}}{k}.
\tag{R3.2.3}
$$

These transformations are *exact* on FLRW at first order. Note that $v_b^{(s)}$ in particular is the *baryon-relative-to-CDM* velocity, a physically meaningful PSTF quantity; the gauge label is incidental.

### §3. Identification of $\Theta_0^{\text{BASS}}$

The free-streaming + Thomson hierarchy R3.1.1 is *not* the synchronous-gauge photon hierarchy. The synchronous-gauge photon monopole equation has a metric source (MB-95 eq. 63):

$$
\dot\Theta_0^{(s)} + \frac{k}{3}\Theta_1^{(s)} = -\frac{1}{6}\dot h_s.
\tag{R3.3.1}
$$

The Newtonian-gauge analog (R2.1.1) has $-\dot\Phi$. BASS's R3.1.1 has *neither*. The kinematic monopole $\Theta_0^{(\text{kin})}$ defined by R3.1.1 satisfies, on FLRW:

$$
\dot\Theta_0^{(\text{kin})} + \frac{k}{3}\Theta_1^{(\text{kin})} = 0.
\tag{R3.3.2}
$$

To compare $\Theta_0^{(\text{kin})}$ to the canonical $\Theta_0^{(N)}$, integrate the difference $\dot\Theta_0^{(\text{kin})} - \dot\Theta_0^{(N)} = +\dot\Phi - \tfrac{k}{3}(\Theta_1^{(\text{kin})} - \Theta_1^{(N)})$ from $\eta_\text{init}$ to $\eta$. The IC matches at $\eta_\text{init}$ (super-horizon adiabatic, gauge-invariant; Step 1). For the dipole, $\Theta_1^{(\text{kin})}$ also lacks the $+k\Psi/3$ Newtonian source, but the dipole couples to Thomson scattering at recombination (rapid relaxation to $v_b/3$), absorbing first-order differences. Therefore, to leading order in the ratio $|\Phi(\eta)-\Phi(\eta_i)|/|\Theta_0|$:

$$
\boxed{\;\Theta_0^{(\text{kin})}(\eta, k) \;\approx\; \Theta_0^{(N)}(\eta, k) + \bigl[\Phi(\eta, k) - \Phi(\eta_\text{init}, k)\bigr] + \mathcal O\bigl(k\!\int\!\Psi\,d\eta'\bigr).\;}
\tag{R3.3.3}
$$

In matter domination, $\Phi$ is approximately constant on sub-horizon scales ($\Phi(\eta)/\Phi(\eta_\text{init}) \to (3/5)\cdot 9/10$ at the radiation-MD transition, then constant; cf. Dodelson §6.5). For the recombination window $\eta \in [\eta_\text{init}, \eta_*]$ with $\eta_* \sim 282$ Mpc, $|\Phi(\eta_*) - \Phi(\eta_\text{init})| \le 5\%$ of $|\Phi(\eta_\text{init})|$ at $k = 10^{-3}$ Mpc⁻¹ (estimable from MD growing-mode analytics; verifiable numerically against CAMB's $\Phi$-history). The $\Theta_0^{(\text{kin})} \approx \Theta_0^{(N)}$ identification is therefore correct at the $\sim 5\%$ level for the cells in the empirical anchor (briefing §3.1 / R2 §7).

**Late times ($\eta > \eta_*$, dark-energy era).** $\Phi$ is no longer constant; the ISW effect is non-negligible. The "missing" metric source in R3.1.1 grows but is **independently captured by the explicit ISW term** $e^{-\kappa(\eta)}(\dot\Phi + \dot\Psi)$ in the LoS source assembly. The LoS architecture compensates: the missing $-\dot\Phi$ source in $\Theta_0$ evolution is reintroduced via the ISW driver in $S_T$. The integration-by-parts identity (used in R2.2.2) ensures the algebra is self-consistent for $\ell \ge 1$:

$$
\int_0^{\eta_0} e^{-\kappa}\dot\Phi\, j_\ell\, d\eta = \int_0^{\eta_0} g\,\Phi\, j_\ell\, d\eta - k\int_0^{\eta_0} e^{-\kappa}\,\Phi\, j_\ell'\, d\eta + \text{(boundary, vanishes for }\ell\ge1).
\tag{R3.3.4}
$$

The $\int g\Phi j_\ell d\eta$ piece on the right *partially* compensates the $\Phi(\eta) - \Phi(\eta_\text{init})$ shift in $\Theta_0^{(\text{kin})}$. **Audit-corrected 2026-04-25**: previous draft claimed "exactly compensates ... when $\Phi(\eta_\text{init}) = 0$ at the lower end of the visibility support" — this is not justified, and conflicts with the MD assumption $\Phi \approx \Phi_\text{init}$ used elsewhere (which gives $\Phi_\text{init}\ne 0$, not zero). The correct statement: the IBP identity decomposes the late-time $\dot\Phi$ contribution into (i) a $g\Phi$ term that overlaps the recombination visibility support and (ii) a $\Phi j_\ell'$ tail that captures the late-time / dark-energy ISW. The "compensation" is at the level of the ISW driver structure, not pointwise cancellation; a constant $-\Phi_\text{init}\int g\, j_\ell\, d\eta$ residual remains and contributes to the leading $g[\Phi(\eta)-\Phi(\eta_\text{init})]$ term in $\delta S_T$ of R3.4.2. Sub-percent verification (per the R3 §6 follow-up) requires solving the coupled monopole–dipole–quadrupole residual hierarchy rather than relying on this single integral identity; see audit-response §1 below.

### §4. LoS assembly gauge-mixing residual

Substituting R3.3.3 into the BASS LoS source:

$$
S_T^{\text{BASS}} \;=\; g\bigl[\Theta_0^{(\text{kin})} + \Psi^{(N)} + \tfrac14\Pi\bigr] + e^{-\kappa}(\dot\Phi+\dot\Psi) + \bigl(g\,v_b^{\text{BASS}}\bigr)'/k
$$

becomes (replacing $\Theta_0^{(\text{kin})}$ by R3.3.3):

$$
S_T^{\text{BASS}} \;=\; \underbrace{g\bigl[\Theta_0^{(N)} + \Psi^{(N)} + \tfrac14\Pi\bigr] + e^{-\kappa}(\dot\Phi+\dot\Psi) + \tfrac{1}{k}(g v_b^{(N)})'}_{S_T^{\text{(canonical Newtonian)}}}\; +\; \delta S_T,
\tag{R3.4.1}
$$

where the residual is

$$
\delta S_T \;=\; g\bigl[\Phi(\eta) - \Phi(\eta_\text{init})\bigr] + \tfrac{1}{k}\bigl[g(v_b^{\text{BASS}} - v_b^{(N)})\bigr]' + \mathcal O\bigl(k\!\int\!\Psi\,d\eta'\bigr).
\tag{R3.4.2}
$$

**The first term $g\bigl[\Phi(\eta) - \Phi(\eta_\text{init})\bigr]$ is small in MD around recombination** for the reason in §3 above: $\Phi$ is approximately constant on sub-horizon scales in MD, so the bracket is a small fraction of $\Phi$ itself, and $g$ has support only at recombination (and at reionization, where $\Phi$ also has the same approximate-constancy property if one redefines the reference epoch).

**The second term depends on Audit Finding 1 from R2 §5.** If BASS's $v_b^{\text{BASS}}$ is the velocity (= $v_b^{(s)} = v_b^{(N)} - v_c^{(N)}$ via R3.2.3), then $v_b^{\text{BASS}} - v_b^{(N)} = -v_c^{(N)}$, contributing $-(g v_c^{(N)})'/k$. If instead $v_b^{\text{BASS}}$ is $\theta_b = k v_b^{(N)}$, then the difference is $kv_b^{(N)} - v_b^{(N)} = (k-1)v_b^{(N)}$ and the BASS Doppler form would already need correction at the assembly level (more severe). Either way, the second term enters at the same order as the Doppler contribution, which the R12→14 ablation reports as $< 0.5\%$ of the total LoS source (V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:120, F3); the gauge residual from this term is therefore well below the 5% empirical anchor.

**The third term $\mathcal O(k\int\Psi\, d\eta')$** captures sub-leading streaming corrections. At sub-horizon $k\eta \gtrsim 1$ but with $\Psi$ approximately constant in MD, $k\int_{\eta_\text{init}}^{\eta_*}\Psi\, d\eta' \sim k(\eta_* - \eta_\text{init})\Psi$, which at $k = 10^{-3}$, $\eta_* - \eta_\text{init} \sim 20$ Mpc gives $\sim 0.02\,\Psi$ — also small.

### §5. Reconciliation with empirical evidence

The empirical low-$k$ ratios from briefing §3.1 (R1 §c, R2 §7):

| $(k, \ell)$ | BASS·LoS / CAMB·direct | Predicted by R3.4.2 |
|---|---:|---|
| $(10^{-3}, 2)$ | $+0.933$ | $\approx 1$ within $\le 5\%$ MD residual |
| $(10^{-3}, 3)$ | $+0.984$ | $\approx 1$ |
| $(10^{-2}, 2)$ | $+1.044$ | $\approx 1$ |
| $(10^{-2}, 3)$ | $+0.999$ | $\approx 1$ |

The 5% maximum deviation (cell $(10^{-3}, 2)$) is consistent with the leading $g[\Phi(\eta) - \Phi(\eta_\text{init})]$ residual estimated in §4. Per the briefing R3 step 4 dichotomy, this falls squarely under **option (b): the residual is at the percent level due to a small intrinsic gauge mismatch on FLRW, quantified in PSTF-native form by R3.4.2**. Option (a) — exact algebraic gauge-coherence — does *not* hold; the BASS assembly is approximately, not exactly, gauge-coherent.

The R12→14 Phase A diagnostic anomalies cited in the investigation summary ($\Psi$ sign-flip at $k = 10^{-4}$, "linear-in-η" $\Theta_0$ ramp interpreted there as canonical synchronous-gauge growing mode) are reinterpreted under R3:
- The $\Psi$ sign-flip at $k = 10^{-4}$ is a numerical artifact of the Einstein-constraint reconstruction at low $k$, where the $1/k^2$ amplification in [`tier_b_source_extraction.py:278`](../htt/bass/spectrum/tier_b_source_extraction.py#L278) (`four_pi_g_a2_over_k2 = 1.5 * H_0^2 * a^2 / k^2`) makes $\Phi$, $\Psi$ noise-dominated at $k\eta \lesssim 0.04$. Not a gauge-frame issue.
- The linear-in-η $\Theta_0$ ramp is consistent with the kinematic-frame interpretation: free-streaming + Thomson on FLRW gives $\Theta_0^{(\text{kin})}$ tracking the integrated SW source via R3.3.3, which in MD ramps approximately linearly with $\eta$ as the ISW contribution accumulates. The R12→14 summary's identification of this with $h_s'/6$ growing-mode is an MB-95-language artifact; in PSTF terms, the ramp is the integrated $\dot\Phi$ contribution that R3.1.1 omits internally and R2.5.1 reintroduces via the ISW driver.

### §6. Verdict on whether BASS needs code-level correction

**Verdict: no code-level correction is required to the LoS assembly at the FLRW limit, at the 5% precision level demonstrated by the four-cell empirical anchor.** Specifically:

- The mixed-gauge assembly $S_T^{\text{BASS}} = g[\Theta_0^{(\text{kin})} + \Psi^{(N)} + \tfrac14\Pi] + e^{-\kappa}(\dot\Phi + \dot\Psi) + (g v_b^{\text{BASS}})'/k$ (with the Doppler $1/k$ point per R2 §5 Audit Finding 1) is approximately gauge-coherent in MD around recombination because $\Theta_0^{(\text{kin})} \approx \Theta_0^{(N)} + [\Phi(\eta) - \Phi(\eta_\text{init})]$ with the bracket small on sub-horizon MD scales.
- The architecturally separate ISW driver $e^{-\kappa}(\dot\Phi + \dot\Psi)$ captures the late-time / dark-energy-era contribution that R3.1.1 omits internally, via the IBP identity R3.3.4.
- The leading residual is bounded by $g \cdot \Delta\Phi$, with $\Delta\Phi/\Phi_\text{init} \le 5\%$ in MD; this matches the empirical $\le 5\%$ maximum deviation in the anchor cells.

**For sub-percent precision** (R6 follow-up or beyond): the precise gauge identification of $\Theta_0^{\text{BASS}}$ via direct numerical comparison with CAMB's $\Theta_0^{(s)}$ + sync ↔ Newt transformation, using the relation R3.2.3, would tighten the verdict. This is a unit-test-shaped verification (compute $\Theta_0^{(\text{kin})} - [\Phi(\eta) - \Phi(\eta_\text{init})]$ from BASS and compare to CAMB's `clxg/4` after sync→Newt conversion using $v_c^{(N)}/k = \alpha$); if agreement is $\le 0.5\%$, the R3.3.3 leading-order analysis is confirmed. The test does not require any code change to BASS production; it is a diagnostic.

**For the Bianchi extension (R4 target)**, the gauge question is moot: synchronous gauge cannot be defined consistently for Bianchi II–IX (the spatial slices do not admit a global comoving CDM congruence — Tsagas–Challinor–Maartens 2008 §6), and the Newtonian-gauge potentials $\Phi, \Psi$ as scalar fields likewise have no clean Bianchi generalization. PSTF / 1+3 covariant variables are mandatory. The kinematic-frame architecture R3.1.1 used by BASS is therefore the *correct primary framework* for the Bianchi extension, with the FLRW-limit $\Theta_0^{(\text{kin})} \approx \Theta_0^{(N)} + [\Phi - \Phi_\text{init}]$ identification providing the cross-check at the FLRW reduction.

### §7. Open questions for R4

Two threads are inherited from R3 into R4:

1. **Sub-horizon validity of R3.3.3 outside MD.** The leading-order identification $\Theta_0^{(\text{kin})} \approx \Theta_0^{(N)} + [\Phi - \Phi_\text{init}]$ relies on MD constancy of $\Phi$. In radiation domination, $\Phi$ decays after horizon entry; in $\Lambda$-domination, $\Phi$ decays as well (ISW). A more careful analysis using the ISW IBP R3.3.4 confirms the $\ell \ge 1$ result is preserved, but the precise residual estimate at the radiation/MD transition deserves R5's analytic-oracle treatment.

2. **Tilted observer frame ($u_e^a \ne n^a$) effect on $\Theta_0$.** R3 used $n^a \equiv u_e^a$ (FLRW orthogonal limit). When tilted, the photon energy density transforms non-trivially between the transport frame ($n^a$) and the collision/visibility frame ($u_e^a$), and the kinematic identification R3.3.3 acquires a tilt-velocity correction. R4 must specify which frame's $\Theta_0$ enters the LoS source for the CMB observer, and how the tilt-induced redistribution between $n^a$- and $u_e^a$-frame energy densities is handled.

---

## R4. Bianchi tetrad-frame extension and tilted-observer LoS source

R3 closed the FLRW gauge audit and identified two threads inherited into R4: (i) the kinematic-frame identification breaks down outside MD and away from the orthogonal limit; (ii) the tilted observer ($u_e^a \ne n^a$) modifies the photon energy density entering the LoS source. R4 derives the LoS source on a Bianchi background, reproduces the BASS T1+T7+T8+T9 operator algebra from CL2000-I, opens the m=±2 channel that vanishes for FLRW and Bianchi-I, sets up the tilted-observer correction, and translates the resulting departure structure into the master x_C identity (MES-tomographic framework).

### Convention extension

R4 retains the CAMB / LC06 baseline as "FLRW reduction target" — i.e., when $\sigma_{ab} = 0$, $\omega_{ab} = 0$, $A_a = 0$, $u_e^a = n^a$, ${}^{(3)}R_{ab}^{\text{aniso}} = 0$, R4's master expressions must collapse to R2.3.1. The 1+3 covariant / tetrad framework adds three primary objects beyond FLRW:

| Symbol | Object | Vanishing on FLRW? |
|---|---|---|
| $\sigma_{ab}$ | Shear of normal congruence $n^a$ | Yes |
| ${}^{(3)}R_{ab}^{\text{aniso}}$ | Anisotropic part of spatial 3-Ricci tensor | Yes (and zero for type I, V isotropic) |
| $\bar v_{(s)}^a$ | Tilt velocity (matter $u_e^a$ relative to $n^a$) | Yes (orthogonal Bianchi I/V/VII₀ have $u_e^a = n^a$) |

**Frame doctrine adopted from lowell §1.2** (italicized verbatim from the reference):

$$
\boxed{\;\text{transport in } n^a\text{-frame}, \quad \text{collision/source/visibility in } u_e^a\text{-frame}\;}
\tag{R4.0.1}
$$

This separation — kinematic transport on the geodesic normal congruence, but Thomson interaction in the electron rest frame — is what allows orthogonal and tilted Bianchi backgrounds to share one solver architecture. The conversion between $n^a$-frame quantities (PSTF moments evolved by `hierarchy_rhs.py`) and $u_e^a$-frame quantities (entering the LoS source) is a velocity boost by $\bar v_{(s)}^a$, expanded to first order in tilt for the linearized regime.

### §1. Tetrad transport: T1+T7+T8+T9 reproduction from CL2000-I

The full 1+3 covariant photon transport equation (Challinor–Lasenby 2000-I eq. 38, restated as R2.1.0) on a Bianchi background retains all nine T-terms; R4 collects the ones that contribute on Bianchi I/V/VII₀ in the orthogonal limit (the six explicitly evolved by BASS). Specializing to harmonic mode $m$ and PSTF rank $\ell$, with $\omega_a = 0, A_a = 0$:

$$
\dot\Pi_{A_\ell}^{(m)} = -a\bigl[T_1 + T_2 + T_3 + T_7 + T_8 + T_9\bigr] + a\,K_T,
\tag{R4.1.1}
$$

with the operators (CL2000-I eq. 38; lowell §6; ELL Maartens-MacCallum 2012 §16):

**T1 — expansion + curvature correction** (lowell §6 expansion term, plus EMM 2012 §16 curvature correction routed via FB-2.4):
$$
T_1 = \frac{4}{3}\Theta\,\Pi_{A_\ell} + \frac{\ell}{2\ell+3}\,{}^{(3)}R^{b}{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b},
\tag{R4.1.2}
$$
where $\Theta = 3H$ (background expansion) and ${}^{(3)}R^{(\text{aniso})}_{ab}$ is the anisotropic part of the spatial 3-Ricci tensor. *(Caveat 2026-04-25: the displayed lowell §6 nine-term equation does NOT contain the curvature-correction term explicitly; that term is added separately per Ellis–Maartens–MacCallum 2012 §16's distinction between the kinematic hierarchy and curved-space corrections. The BASS code routes it via FB-2.4, but the formula's literature provenance lies in EMM 2012 §16, not lowell §6.)* The second term — the "rank-ℓ curved-space correction" of EMM 2012 §16 — vanishes for type I (flat) and type V isotropic, but is nonzero for the eight anisotropic types II, VI₀, VIII, III, IV, VI_h, VII_h, VII₀-non-symmetric. BASS implements this via [`hierarchy_rhs.py:472–477`](../htt/bass/hierarchy/hierarchy_rhs.py#L472), routing `ricci_coeffs` from `tetrad_state.aniso_3_curvature` (FB-2.4 driver-level wire-up).

**T2/T3 — gradient/divergence** (lowell §6 displayed form, position-space):
$$
T_2 = +\tilde\nabla_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}, \qquad T_3 = +\frac{\ell+1}{2\ell+3}\,\tilde\nabla^b\Pi_{A_\ell b}.
\tag{R4.1.3}
$$
*(Audit-corrected 2026-04-25: previous draft used scalar-harmonic-mode coefficients $-\ell/(2\ell+1)$ for T2 with no T3 coefficient. Position-space form is +1 for T2 and $(\ell+1)/(2\ell+3)$ for T3 per lowell §6 displayed equation. The conversion to scalar harmonic mode m=0 with Fourier multipliers introduces additional angular-momentum recouplings; that conversion is left for the per-type harmonic backend rather than asserted as the position-space coefficient.)* On a Bianchi background with left-invariant tetrad frame, the structure constants $C^a{}_{bc}$ contribute to the projected derivatives $\tilde\nabla_a$. BASS routes these via `nabla_operator` argument at [`hierarchy_rhs.py:479–501`](../htt/bass/hierarchy/hierarchy_rhs.py#L479); for the FLRW fast path the operator is `zero_nabla_operator` (gradient/divergence vanish in Fourier representation when scalar harmonics absorb $\tilde\nabla$).

**T7/T8/T9 — shear coupling** (lowell §6 displayed form):
$$
T_7 = -\frac{(\ell-1)(\ell+1)(\ell+2)}{(2\ell+3)(2\ell+5)}\,\sigma^{bc}\,\Pi_{A_\ell bc}, \qquad
T_8 = +\frac{5\ell}{2\ell+3}\,\sigma^{b}{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b},
$$
$$
T_9 = -(\ell+2)\,\sigma_{\langle a_\ell a_{\ell-1}}\Pi_{A_{\ell-2}\rangle}.
\tag{R4.1.4}
$$
*(Audit-corrected 2026-04-25: previous draft had T7 missing the $(\ell-1)$ factor, T8 with sign and prefactor errors ($-2\ell/(2\ell+3)$ instead of $+5\ell/(2\ell+3)$), and T9 with a malformed expression. Coefficients above are taken verbatim from lowell §6 line 374–376. The $\ell=2$ specialization at lowell §6 line 402–404 reads $-(4/21)\sigma^{cd}\Pi_{abcd} + (10/7)\sigma^c{}_{\langle a}\Pi_{b\rangle c} - 4\sigma_{ab}\Pi$, consistent with R4.1.4 at $\ell=2$.)* T7 couples $\Pi_\ell$ to $\Pi_{\ell+2}$ via shear contraction (closure-dependent at the cutoff); T8 acts within $\ell$; T9 couples $\Pi_\ell$ to $\Pi_{\ell-2}$ (inactive for $\ell < 2$). BASS implements all three via [`apply_T7_shear_up_packed`, `apply_T8_shear_same_packed`, `apply_T9_shear_down_packed`](../htt/bass/hierarchy/hierarchy_rhs.py#L442) imported from `bass.hierarchy.packed_operators`. **Note**: the `packed_operators.py` source is not in the R1 reading bundle, so the operator algebra inside these functions is dispatch-confirmed but algebra-unverified from the bundle alone. Status downgrade in R6 §2 reflects this.

**T4/T5/T6 — acceleration/vorticity** (CL2000-I eq. 38):
$$
T_4 \propto A^a\Pi_{a A_\ell}, \quad T_5 \propto A_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}, \quad T_6 \propto \omega^b{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b}.
\tag{R4.1.5}
$$
Inactive on orthogonal Bianchi I/V/VII₀ ($A_a = \omega_a = 0$). BASS exposes them as opt-in via `accel_vector` and `vorticity_vector` kwargs ([`hierarchy_rhs.py:351–352, 503–508`](../htt/bass/hierarchy/hierarchy_rhs.py#L503)) for future tilted / vorticity-bearing extensions.

**Reproduction status.** All six operators T1+T2+T3+T7+T8+T9 active on Bianchi I/V/VII₀ are dispatched from BASS production code (call-sites confirmed in `hierarchy_rhs.py`). The R4 derivation is therefore not adding new evolution operators — it provides the *intended algebra* (per lowell §6 displayed equation, audit-corrected) and clarifies the LoS-side consequences of these terms. **The implementation algebra inside `apply_T1/T7/T8/T9_packed` (the called functions in `bass.hierarchy.packed_operators`) is not directly verifiable from the R1 reading bundle** because that source file is absent; R4 confirms what the operators *should* compute, while the in-repo regression spec at P1.5-F is the path to confirming what they *do* compute.

### §2. The m = ±2 channel: spin-2 sourcing on Bianchi backgrounds

On FLRW with scalar (m=0) harmonics only, the photon multipole tower is purely scalar: $\Theta_\ell^{(m=0)}$ with all m=±2 amplitudes identically zero. Bianchi backgrounds source the m=±2 channel through **two distinct mechanisms**:

**Mechanism A — direct shear sourcing of the temperature quadrupole.** Even at $\ell = 2$ scalar mode, the shear $\sigma_{ab}$ projected onto the spin-2 angular harmonics on the celestial sphere generates a temperature contribution

$$
\Theta_2^{(\pm 2)}(\eta) \propto \int_{\eta_*}^{\eta_0} d\eta'\, \sigma^{(\pm 2)}(\eta')\, \mathcal F_2[k(\eta_0 - \eta')],
\tag{R4.2.1}
$$
where $\sigma^{(\pm 2)}$ are the spin-2 components of the shear tensor in the tetrad frame and $\mathcal F_2$ is the spin-2 LoS projector (the analog of $j_\ell$ for the m=0 case). The Wigner-d structure for spin-2 harmonics replaces the spin-0 $j_\ell$ with the modified Bessel functions $\epsilon_\ell(x)$ and $\beta_\ell(x)$ familiar from KKS97. (Hu–White 1997 §V.B; Pontzen–Challinor 2007 §3.) On Bianchi I, this is the dominant Bianchi imprint at low ℓ.

**Mechanism B — m-channel coupling via T7/T8/T9.** The shear operators T7 and T9 (R4.1.4) couple $(\ell, m=0)$ to $(\ell\pm 2, m=\pm 2)$ via the contraction $\sigma_{\langle a b}\Pi_{\cdots\rangle}$ when $\sigma_{ab}$ has off-diagonal anisotropy. T8 within fixed $\ell$ shifts m. Numerically, on a Bianchi I background with diagonal shear $\sigma_{ab} = \text{diag}(\sigma_+, \sigma_+, -2\sigma_+)$ (axisymmetric), the m=±2 channels remain decoupled to first order in $\sigma$, but with non-axisymmetric Bianchi V/VII the two off-diagonal modes m=±2 mix via T7/T9.

**LoS source for the m=±2 channel.** The temperature LoS source restricted to scalar (m=0) modes is R2.3.1. For m=±2, the analogous derivation (SZ96 → IBP step (a) on the dipole; ISW IBP) yields:

$$
S_T^{(\ell\ge 2,\, m=\pm 2)}(\eta, k) = g(\eta)\,\tfrac{1}{4}\Pi^{(\pm 2)} + e^{-\kappa}\,\bigl[\dot\Phi^{(\pm 2)} + \dot\Psi^{(\pm 2)}\bigr] + \text{(Bianchi shear forcing)}.
\tag{R4.2.2}
$$
The "Bianchi shear forcing" term arises because the tetrad-frame shear $\sigma_{ab}^{(\pm 2)}$ acts as an external source on the photon dipole equation's $\Theta_2$ projection, with no FLRW counterpart. Its explicit form requires the spin-2 LoS projector and the tetrad structure constants $C^a{}_{bc}$ for the specific Bianchi type. Concretely, for Bianchi I:

$$
S_T^{(\ell\ge 2,\, m=\pm 2)}\Big|_{\text{Bianchi I}} = g\,\tfrac14\Pi^{(\pm 2)} + e^{-\kappa}\bigl[\dot\Phi^{(\pm 2)} + \dot\Psi^{(\pm 2)} + \tfrac12\dot\sigma^{(\pm 2)}\bigr],
\tag{R4.2.3}
$$
where $\Phi^{(\pm 2)}, \Psi^{(\pm 2)}$ are the spin-2 metric perturbations. The $\tfrac12\dot\sigma^{(\pm 2)}$ contribution is the analog of an "anisotropic-stress ISW" specific to Bianchi backgrounds. (Pontzen–Challinor 2007 §4 derives this for Bianchi I, VII_h; explicit forms for II, VIII, IX require per-type expansion of the scalar/spin-2 harmonics adapted to the Killing geometry — out of scope for R4, but the R4 architecture below isolates it as a per-type plug-in.)

**Status in BASS.** The m=±2 channel is not yet activated in production. The state vector $\{\Theta_0, \Theta_1, \Theta_2, E_2\}$ at lowell §1.3 supports m=0 only in the lowell baseline; the m=±2 amplitudes require either (i) doubling the state vector to track $\Theta_\ell^{(0)}$ and $\Theta_\ell^{(\pm 2)}$ separately, or (ii) routing the spin-2 components through a separate spin-weighted tower. The integrator's packed-state layout (`(L+1)²` slots per species at [`integrator.py:231`](../htt/bass/hierarchy/integrator.py#L231)) already accommodates both options — the slot index $i = \ell^2 + (m+\ell)$ permits direct addressing of m=±2 amplitudes.

### §3. Tilted observer ($u_e^a \ne n^a$): LoS source in $u_e^a$-frame

The lowell §1.2 frame doctrine R4.0.1 specifies that the LoS source must be expressed in the electron rest frame $u_e^a$, while the photon hierarchy is transported in the geodesic normal frame $n^a$. The two frames are related by a tilt boost $\bar v_{(s)}^a$ (lowell §9.1):

$$
u_e^a = \bar\gamma_s\bigl(n^a + \bar v_{(s)}^a\bigr) + \delta u_{(s)}^a, \qquad \bar\gamma_s \approx 1 + \tfrac12 \bar v_{(s)}^2.
\tag{R4.3.1}
$$

To first order in tilt $|\bar v_{(s)}|$, the photon multipoles in the two frames differ by a velocity-boost correction (Tsagas–Challinor–Maartens 2008 §5):

$$
\Theta_\ell^{(u_e)} = \Theta_\ell^{(n)} + \bar v_{(s)}^a\,\Bigl[\frac{\ell}{2\ell-1}\Theta_{\ell-1}^{(n)} - \frac{\ell+1}{2\ell+3}\Theta_{\ell+1}^{(n)}\Bigr]\,\hat e_a + \mathcal O(\bar v^2).
\tag{R4.3.2}
$$
At $\ell = 0$: $\Theta_0^{(u_e)} = \Theta_0^{(n)} - \tfrac{1}{3}\bar v_{(s)}^a \Theta_1^{(n)}\hat e_a + \mathcal O(\bar v^2)$ (the boost-induced monopole shift is second order in tilt; the first-order correction is the dipole-driven kinematic Doppler). At $\ell = 1$: the dipole acquires a tilt offset $\bar v_{(s)}^a\hat e_a + \mathcal O(\bar v^2)$. At $\ell \ge 2$: tilt corrections are mixed band-couplings of the same order.

**LoS source with tilt.** Substituting R4.3.2 into the LoS source assembly:

$$
S_T^{(u_e)}(\eta, k) = g(\eta)\bigl[\Theta_0^{(u_e)} + \Psi^{(u_e)} + \tfrac14\Pi^{(u_e)}\bigr] + e^{-\kappa}\bigl[\dot\Phi^{(u_e)} + \dot\Psi^{(u_e)}\bigr] + \tfrac{1}{k}\bigl(g\, v_b^{(u_e)}\bigr)' + \delta S_T^{\text{tilt}},
\tag{R4.3.3}
$$
where the explicit tilt residual is

$$
\delta S_T^{\text{tilt}} = -\tfrac{1}{3}\,g\,\bar v_{(s)}^a\,\Theta_1^{(n)}\hat e_a + \tfrac{1}{4}g\bigl[\Pi^{(u_e)} - \Pi^{(n)}\bigr] + \mathcal O(\bar v^2),
\tag{R4.3.4}
$$
and the polter mismatch $\Pi^{(u_e)} - \Pi^{(n)}$ at first order is again a band-coupling between $\Theta_2^{(n)}, \Theta_1^{(n)}$, and $E_2^{(n)}$ via R4.3.2 at $\ell = 2$. At leading order, the dominant tilt contribution to the LoS source is a kinematic dipole modulation of the SW term — a Doppler-like rescaling of $\Theta_0$ by the tilt velocity, in addition to the standard baryon-velocity Doppler. This is the structural reason tilted Bianchi backgrounds produce both temperature and polarization patterns distinct from orthogonal Bianchi: the LoS source acquires a tilt-velocity dipole modulation that couples to the polter at $\ell = 2$.

**Frozen-tilt limit.** For radiation-era frozen tilt (King–Ellis 1973; MES framework §6.2), $\bar v_{(s)}^a$ is constant in conformal time, and R4.3.4 reduces to a static velocity rescaling of the LoS source. Per MES framework Table 6.2 (radiation w=1/3 row), $\dot{\bar\beta} = 0$, so the tilt enters as a static "bulk flow" overlaid on the standard CMB. For dust (w=0), $\bar\beta \propto a^{-1/3}$ slowly decays, and the tilt residual R4.3.4 is suppressed at recombination relative to early times.

### §4. Master departure: x_C from R4 algebra to MES tomographic framework

The tomographic MES framework (project doc `tomographic_MES_framework.md` §6.1) defines the master departure identity:

$$
x_C \;=\; \Sigma^2_{\text{std}} \;-\; W^2_{\text{std}} \;+\; \Omega_{\text{tilt}} \;+\; \Omega_{k,\text{aniso}}.
\tag{R4.4.1}
$$
Each term has a direct correspondence with a R4 algebra ingredient:

| Term | MES definition | R4 source | BASS data |
|---|---|---|---|
| $\Sigma^2_{\text{std}}$ | $\sigma^2/(6H^2),\; \sigma^2 = \tfrac12\sigma_{ab}\sigma^{ab}$ | T7+T8+T9 shear coupling (R4.1.4); m=±2 channel sourcing (R4.2.3) | `tetrad_state.sigma_tensor` (`hierarchy_rhs.py:411`) |
| $W^2_{\text{std}}$ | $\omega^2/(3H^2)$ | T6 vorticity (R4.1.5); inactive in current orthogonal-Bianchi I/V/VII₀ | `vorticity_vector` kwarg (`hierarchy_rhs.py:352`) — opt-in |
| $\Omega_{\text{tilt}}$ | $(1+w)\Omega_m \sinh^2\beta/2$ | $\bar v_{(s)}^a$ tilt velocity (R4.3.1); LoS residual R4.3.4 | not yet wired; requires species-frame tilt history (R4 §5 below) |
| $\Omega_{k,\text{aniso}}$ | anisotropic spatial-curvature density | T1 curved-space correction (R4.1.2); ${}^{(3)}R^{\text{aniso}}_{ab}$ | `tetrad_state.aniso_3_curvature` (`hierarchy_rhs.py:414`) |

**Information-content caveat.** Per MES framework Theorem 6.4, $x_C$ is SO(3)-invariant and *cannot determine the angular pattern* of directional observables. R4 confirms this from the BASS-architectural perspective: a single scalar $x_C$ collapses the rank-2 shear, the vector vorticity, the tilt velocity, and the anisotropic 3-curvature into one scalar contraction, losing the directional information that distinguishes Bianchi types and that produces the m=±2 channel signal. For BASS's CMB observables, the full tensor structure must be retained at evolution time; $x_C$ is a derived diagnostic, not an evolution variable.

**Scaling laws governing $x_C$ on the relevant epochs** (MES framework §6.2, Propositions 6.1, 6.3):
- Bianchi I irrotational geodesic perfect fluid: $\Sigma^2 \propto a^{-6}$ — strongest decay.
- Vorticity barotropic almost-FLRW: $\omega^2 \propto a^{6w-4}$, so $W^2_{\text{std}} \propto a^{6w-2}$ — *grows* during radiation domination.
- Tilt: $\bar\beta \propto a^{-1/3}$ in dust, $\propto a^{-1}$ in $\Lambda$; frozen ($\dot\beta = 0$) in radiation (King–Ellis 1973).
- Anisotropic 3-curvature: type-dependent (zero for I, V isotropic; nonzero for II, VI₀, VIII, III, IV, VI_h, VII_h, non-symmetric VII₀).

### §5. Code-mapping table: formalism ↔ BASS implementation status

The structure below isolates each R4 ingredient as a per-Bianchi-type modular plug-in around the BASS production core.

> **HISTORICAL TABLE — superseded by R6 §2 (post-R9) and R9 §3 SSoT table.** The original ✓ status entries below were downgraded to ✓⁻ in R9 once it was recognized that the called operator source files (`packed_operators.py`, `terms.py`, `bass.transport.thomson_collision`) are absent from the R1 reading bundle, so the operator algebra inside is dispatch-confirmed but not directly audit-verifiable. The status column has been updated below to ✓⁻ for these items to keep the table internally consistent; consult R9 §3 for the canonical SSoT status.

| Formalism term | BASS file:line | Status |
|---|---|---|
| **T1 expansion (4Θ/3) Π** | `hierarchy/hierarchy_rhs.py:421-447` (FLRW fast path); `:472-477` (general path) | ✓⁻ dispatch-confirmed, FLRW + Bianchi; algebra in `apply_T1_expansion_packed` unverified in bundle |
| **T1 curvature correction** ${}^{(3)}R^{\text{aniso}}$ | `hierarchy/hierarchy_rhs.py:414` reads `ricci_coeffs`; `apply_T1_expansion_packed(...,aniso_ricci_tensor=...)` at `:431-435, :472-477` | ✓⁻ wired (FB-2.4); provenance EMM 2012 §16 not lowell §6 displayed; test coverage for anisotropic types pending |
| **T2 gradient** | `hierarchy/terms.py:T2_gradient` via `nabla_operator`; `hierarchy_rhs.py:479-491` | ✓⁻ dispatch-confirmed; `zero_nabla_operator` default for FLRW; `terms.py` source absent |
| **T3 divergence** | `hierarchy/terms.py:T3_divergence`; `hierarchy_rhs.py:492-501` | ✓⁻ dispatch-confirmed; source absent |
| **T4 acceleration divergence** | `apply_T4_accel_divergence_packed`; `hierarchy_rhs.py:503-504` | ✓⁻ wired, opt-in via `accel_vector` kwarg; algebra unverified |
| **T5 acceleration gradient** | `apply_T5_accel_gradient_packed`; `hierarchy_rhs.py:505-506` | ✓⁻ wired, opt-in; algebra unverified |
| **T6 vorticity** | `apply_T6_vorticity_packed`; `hierarchy_rhs.py:507-508` | ✓⁻ wired, opt-in via `vorticity_vector` kwarg; algebra unverified |
| **T7 shear up-coupling** | `apply_T7_shear_up_packed`; `hierarchy_rhs.py:442, :511` | ✓⁻ dispatch-confirmed, FLRW+Bianchi; `packed_operators.py` source absent |
| **T8 shear same-ℓ** | `apply_T8_shear_same_packed`; `hierarchy_rhs.py:443, :512` | ✓⁻ dispatch-confirmed; source absent |
| **T9 shear down-coupling** | `apply_T9_shear_down_packed`; `hierarchy_rhs.py:445, :513` | ✓⁻ dispatch-confirmed (ℓ ≥ 2); source absent |
| **K_T Thomson collision** | `bass/transport/thomson_collision.py` (referenced via `CollisionOperator`); `hierarchy_rhs.py:521` | ✓⁻ dispatch-confirmed for m=0; collision source absent |
| **m=0 LoS projector** $j_\ell[k(\eta_0-\eta)]$ | `los/flrw_bessel_projector.py:499-546` | ✓ implemented (FLRW only); algebra bundle-verified |
| **m=±2 LoS spin-2 projector** $\epsilon_\ell, \beta_\ell$ | (no production code) | ✗ **planned**: Bianchi backend in `bass/los/families/` (briefing §3.4) |
| **Bianchi shear forcing** $\dot\sigma^{(\pm 2)}$ in S_T | (no production code) | ✗ **planned**: per-type plug-in around `flrw_bessel_projector` |
| **Tilt velocity boost $\bar v_{(s)}^a$** | (no production code) | ✗ **planned**: requires species-frame tilt history; lowell §9.1 |
| **Tilted-observer LoS residual $\delta S_T^{\text{tilt}}$** | (no production code) | ✗ **planned**: R4.3.4 |
| **m=±2 state vector slots** | `integrator.py:231` `(L+1)²` packing accommodates m index | ✓ infrastructure bundle-verified; not populated for m≠0 |
| **Master departure $x_C$ diagnostic** | (no production code) | ✗ **planned**: derived diagnostic at post-processing; MES framework §6.1 |

The eight items marked ✗ are the R4-identified extension scope. Items ✗ subdivide into two bins:
- **Per-type modular plug-ins** (m=±2 LoS projector; Bianchi shear forcing): require explicit harmonic decomposition of the Bianchi metric for each type II–IX. Pontzen–Challinor 2007 covers I and VII_h; II/VIII/IX require new derivations with the Killing-geometry-adapted basis.
- **Tilt infrastructure** (tilt velocity, tilted-observer residual): orthogonal to the type-by-type scope; can be developed first on Bianchi V (the prototypical tilted type) and reused for all tilted Bianchi types via the universal R4.3.1–R4.3.4 algebra.

### §6. Reduction check: R4 → R2 in the FLRW limit

Setting $\sigma_{ab} = 0$, $\omega_a = 0$, $A_a = 0$, $\bar v_{(s)}^a = 0$, ${}^{(3)}R_{ab}^{\text{aniso}} = 0$ in R4:

- T1 reduces to $\tfrac{4}{3}\Theta\Pi_{A_\ell}$ (no curvature term).
- T7=T8=T9=0 (`has_sigma = False` in `hierarchy_rhs.py:411`).
- T4=T5=T6=0.
- m=±2 channel: identically zero (no shear forcing).
- $\delta S_T^{\text{tilt}} = 0$ at all orders.

The remaining structure is T1+T2+T3+collision in the m=0 channel, which reproduces R2.1.1–R2.1.3. The LoS source R4.2.2 in m=0 reduces to R2.3.1 with $u_e^a = n^a$, recovering the canonical CAMB / LC06 form. **R4 collapses to R2 in the FLRW limit by construction**, and the FLRW empirical anchor (R2 §7) carries through.

### §7. Open thread for R5

The analytic-oracle expressions in R5 are FLRW-only. The Bianchi extension requires a separate analytic-oracle program: closed-form $\Delta_\ell^{T,(m=\pm 2)}(k)$ for shear-only Bianchi I in the sharp-visibility limit, parallel to R5's FLRW oracles. This program is downstream of R5 and not in scope for the current handoff; R4 §5 establishes the architectural slot where such oracles would land (a `families/bianchi_i.py` per-type backend with its own analytic counterpart), and R5 produces the FLRW anchors that the Bianchi-I oracle would reduce to in the $\sigma \to 0$ limit.

---

## R5. High-$k$ analytic validation oracles

The Round-15 §10 decisive-test design uses CAMB-direct $\Delta_\ell^T(k)$ as the truth reference. Per briefing §3.3, that reference itself fails for $k \gtrsim 10^{-2}$ Mpc⁻¹ because CAMB's source-decomposition introspection breaks down at high $k$ (CAMB stores neither $\Phi(\eta), \Psi(\eta)$ on a fine enough grid nor the visibility-weighted decomposition needed to reconstruct $\Delta_\ell^T$ term-by-term). The four-cell low-$k$ panel (R2 §7, R3 §5) is therefore the only clean empirical anchor available, and the high-$k$ behaviour of BASS's LoS assembly is unverified.

R5 closes this gap by deriving five closed-form analytic oracles for $\Delta_\ell^T(k)$ in well-defined limiting regimes. Each oracle (i) requires only minimal inputs ($\Phi$, $\Psi$, $v_b$, $g$ at one or a few epochs), (ii) is computable from BASS's existing source-extraction outputs without external truth references, and (iii) carries a known tolerance derivable from the limiting approximation. Together they validate the LoS projector and source assembly term-by-term across $\ell \in [2, 100]$ and $k \in [10^{-3}, 10^{-1}]$ Mpc⁻¹, including the high-$k$ regime where the §10 anchor is unavailable.

The oracles are in **CAMB / LC06 baseline**, continuing from R2–R4. All target the FLRW reduction (m=0 scalar mode, $\sigma_{ab}=0$); Bianchi-I oracles are R4 §7's downstream extension and out of scope here.

### §1. Oracle 1 — Sharp-visibility Sachs–Wolfe (already in BASS)

**Limit.** $g(\eta) \to \delta(\eta - \eta_*)$ with all other source contributions set to zero: $\Pi = 0$, $\dot\Phi + \dot\Psi = 0$, $v_b = 0$.

**Closed form.**
$$
\Delta_\ell^{T,\,\text{SW-sharp}}(k) \;=\; \bigl[\Theta_0(\eta_*) + \Psi(\eta_*)\bigr]\cdot j_\ell\bigl[k(\eta_0 - \eta_*)\bigr].
\tag{R5.1.1}
$$

**Derivation.** $\int_0^{\eta_0} g(\eta)\,[\Theta_0+\Psi]\, j_\ell\,d\eta = \int \delta(\eta-\eta_*)\,[\Theta_0+\Psi]\,j_\ell\,d\eta = [\Theta_0+\Psi]_* j_\ell[k(\eta_0-\eta_*)]$. Trivial.

**Validity.** Exact in the limit; the LoS projector should reproduce R5.1.1 to machine precision when fed a $\delta$-like (or vanishingly narrow Gaussian) visibility.

**BASS implementation.** [`sachs_wolfe_analytic_transfer`](../htt/bass/los/flrw_bessel_projector.py#L614). The function takes $k$, $\eta_*$, the scalar amplitude $[\Theta_0 + \Psi]_*$, and a `FLRWBesselConfig` carrying $\eta_0$, returning $\Delta_\ell^T$ for $\ell \in [0, L_\text{max}]$.

**Unit-test tolerance.** Feed `project_temperature_transfer` a $g(\eta) = \mathcal N(\eta_*; \sigma_g)$ with $\sigma_g = 10^{-3}$ Mpc and $[\Theta_0 + \Psi]$ constant, with all other source contributions zeroed. Expected: $|\Delta_\ell^{\text{numeric}} - \Delta_\ell^{\text{R5.1.1}}| / |\Delta_\ell^{\text{R5.1.1}}| \le 10^{-10}$ for $\ell \in [0, 50]$, $k\sigma_g \le 0.1$.

**Use in §10.** Provides a $k$-independent SW reference at recombination $\eta_* \approx 282$ Mpc. Validates the projector kernel structure but not the source assembly.

### §2. Oracle 2 — Gaussian visibility, matter-dominated SW

**Limit.** $g(\eta) = (2\pi\sigma_*^2)^{-1/2}\exp[-(\eta-\eta_*)^2/(2\sigma_*^2)]$, $\Theta_0 + \Psi$ approximately constant across the visibility width (sub-horizon MD with $\Phi$ slowly varying), $\Pi$, $\dot\Phi+\dot\Psi$, $v_b$ all zero. The recombination visibility $\sigma_* \approx 11$ Mpc (Hu–Sugiyama 1995 §III.B; Lewis–Challinor 2006 §4.1).

**Closed form.** Taylor-expand $j_\ell[k(\eta_0-\eta)]$ around $\eta = \eta_*$:
$$
j_\ell[k(\eta_0-\eta)] = j_\ell[kr_*] - k(\eta-\eta_*)\,j_\ell'[kr_*] + \tfrac{1}{2}k^2(\eta-\eta_*)^2 j_\ell''[kr_*] + \mathcal O\bigl((\eta-\eta_*)^3\bigr),
$$
with $r_* \equiv \eta_0 - \eta_*$. The Gaussian integral picks the even moments:
$$
\int g(\eta)\,(\eta-\eta_*)^{2n}\,d\eta = \sigma_*^{2n}\cdot(2n-1)!! \;,\qquad \int g\cdot(\eta-\eta_*)^{2n+1}\,d\eta = 0.
$$
Hence:
$$
\boxed{\;\Delta_\ell^{T,\,\text{SW-Gauss}}(k) \;=\; [\Theta_0+\Psi]_*\,\Bigl\{j_\ell[kr_*] + \tfrac{1}{2}k^2\sigma_*^2\, j_\ell''[kr_*] + \mathcal O\bigl((k\sigma_*)^4\bigr)\Bigr\}.\;}
\tag{R5.2.1}
$$
Using the Bessel ODE $j_\ell'' + (2/x)j_\ell' + [1 - \ell(\ell+1)/x^2] j_\ell = 0$ to eliminate $j_\ell''$:
$$
j_\ell''[kr_*] = -\frac{2}{kr_*}j_\ell'[kr_*] + \Bigl[\frac{\ell(\ell+1)}{(kr_*)^2} - 1\Bigr]j_\ell[kr_*].
\tag{R5.2.2}
$$
Substituting R5.2.2 into R5.2.1 yields the explicit "Silk-damping-like" factor

$$
\Delta_\ell^{T,\,\text{SW-Gauss}}(k) \;\approx\; [\Theta_0+\Psi]_*\,j_\ell[kr_*]\,\Bigl[1 + \tfrac{1}{2}k^2\sigma_*^2\Bigl(\frac{\ell(\ell+1)}{(kr_*)^2} - 1\Bigr)\Bigr] - [\Theta_0+\Psi]_*\,\sigma_*^2\,k\,\frac{j_\ell'[kr_*]}{r_*}.
\tag{R5.2.3}
$$
The leading correction at large $kr_*$ is the $-\tfrac12 k^2\sigma_*^2 j_\ell$ term, which produces a *Gaussian envelope* $\exp(-\tfrac12 k^2\sigma_*^2)$ when resummed (Silk-damping-like, but this is the visibility-finite-width effect, distinct from photon-baryon collisional Silk damping).

**Validity.** $k\sigma_* \lesssim 0.45$ for the truncated Taylor expansion to be accurate to $\le 5\%$ on the leading $\sigma_*^2$ term, with the next-order coefficient bounded uniformly in $\ell$ by Bessel-derivative norms. *(Audit-corrected 2026-04-25: previous draft claimed $\le 5\%$ at $k\sigma_* = 0.55$, but $(0.55)^4 \approx 0.092$ — the next-order $(k\sigma_*)^4$ correction is up to $\sim 9\%$ without explicit coefficient control, so the 5% bound holds only at $k\sigma_* \le 0.45$ where $(0.45)^4 \approx 0.041$.)* At $\sigma_* = 11$ Mpc this means $k \le 0.041$ Mpc⁻¹ for the 5% bound. For higher $k$, replace the truncated Taylor with full Gaussian integration: $\int g\, j_\ell\, d\eta = $ a Bessel-Gaussian convolution computable in closed form (Lewis–Challinor 2006 §4.4 eq. 4.31), or compare directly to numerical quadrature.

**Unit-test tolerance.** Feed `project_temperature_transfer` a Gaussian $g$ with $\sigma_g \in \{1, 5, 11, 25\}$ Mpc and $[\Theta_0+\Psi]$ constant, other sources zero. Expected:
- $\sigma_g = 1$ Mpc: matches R5.1.1 to $\le 10^{-6}$ relative error for $k \in [10^{-3}, 10^{-1}]$.
- $\sigma_g = 11$ Mpc, $k \in [10^{-3}, 10^{-2}]$: matches R5.2.1 (truncated to $\sigma_*^2$) to $\le 5\times 10^{-3}$.
- $\sigma_g = 25$ Mpc, $k \in [10^{-2}, 10^{-1}]$: full Gaussian-Bessel convolution required; truncated form fails.

**Use in §10.** This oracle makes the SW component of the BASS LoS source numerically validated at realistic visibility width, including the high-$k$ regime $k \in [10^{-2}, 10^{-1}]$ where CAMB's source-decomposition is unavailable.

### §3. Oracle 3 — Acoustic toy

**Limit.** $\Theta_0(\eta_*, k) = A(k)\cos(c_s k\eta_*) + B(k)\sin(c_s k\eta_*)$ with $c_s \approx 1/\sqrt 3$ approximately constant near recombination; $\Psi$, $\Pi$, ISW, Doppler set to zero; sharp visibility $g \to \delta(\eta - \eta_*)$.

**Closed form.**
$$
\Delta_\ell^{T,\,\text{ac-sharp}}(k) \;=\; \bigl[A(k)\cos(c_s k\eta_*) + B(k)\sin(c_s k\eta_*)\bigr]\, j_\ell[k(\eta_0 - \eta_*)].
\tag{R5.3.1}
$$

**Derivation.** Same as R5.1.1 with $\Theta_0$ replaced by the acoustic ansatz; trivial substitution.

**Physical content.** R5.3.1 reproduces the *acoustic-peak structure* of $\Delta_\ell^T$ at fixed $\ell$: oscillatory in $k$ with phase $c_s k\eta_*$, modulated by the $j_\ell[kr_*]$ Bessel envelope that produces the "ringing" pattern when projected to ℓ-space. Peak positions: extrema of $\cos(c_s k\eta_*)$ at $c_s k\eta_* = n\pi$, giving $k_n = n\pi/(c_s \eta_*)$. With $c_s\eta_* \approx 130$ Mpc at recombination, $k_1 \approx 0.024$ Mpc⁻¹ — the first acoustic peak in $k$-space.

**Validity.** Strictly synthetic — uses an algebraic $\Theta_0$ ansatz rather than physical evolution. Validates the projector + source-assembly at oscillatory $\Theta_0$, not the dynamics that generate it. $A(k), B(k), c_s$ are inputs.

**Unit-test tolerance.** With $A = 1, B = 0, c_s = 1/\sqrt 3, \eta_* = 282$ Mpc, $g$ as a narrow Gaussian ($\sigma_g = 0.5$ Mpc) — match R5.3.1 to $\le 10^{-8}$ for $\ell \in [0, 50]$, $k \in [10^{-3}, 10^{-1}]$. Then verify peak positions and zero-crossings against $\cos(c_s k\eta_*) j_\ell[kr_*]$ analytically.

**Use in §10.** This oracle is the *high-$k$ acoustic-peak validator*. At $k \in [0.02, 0.1]$ Mpc⁻¹ where CAMB introspection fails, the BASS projector should still produce the correct acoustic-peak ringing in $\ell$ when fed an algebraic acoustic $\Theta_0$. Independent of the source-extraction dynamics.

### §4. Oracle 4 — Pure ISW with Limber approximation

**Limit.** $S_T = e^{-\kappa(\eta)}(\dot\Phi + \dot\Psi)$ only, with $\kappa(\eta) \approx 0$ for $\eta > \eta_\text{re}$ (post-reionization late ISW), and $\Phi = \Psi$ (no anisotropic stress at late times). All other source contributions zero.

**Closed form (full integral).**
$$
\Delta_\ell^{T,\,\text{ISW}}(k) \;=\; 2\int_{\eta_\text{re}}^{\eta_0} \dot\Phi(\eta, k)\, j_\ell[k(\eta_0 - \eta)]\, d\eta.
\tag{R5.4.1}
$$

**Limber-approximation closed form.** At large $\ell$ and $k\eta_0 \gg 1$, $j_\ell^2[kr]$ peaks sharply near $kr \approx \ell + 1/2$, giving the stationary-phase point $\eta_* = \eta_0 - (\ell+1/2)/k$. The Limber identity (LoVerde–Afshordi 2008 eq. 4) reads
$$
\int F(\eta)\, j_\ell[k(\eta_0-\eta)]\, d\eta \;\simeq\; \sqrt{\frac{\pi}{2(\ell+1/2)}}\,\frac{F[\eta_0 - (\ell+1/2)/k]}{k} \;\bigl[1 + \mathcal O(\ell^{-2})\bigr],
\tag{R5.4.2}
$$
yielding
$$
\boxed{\;\Delta_\ell^{T,\,\text{ISW-Limber}}(k) \;\simeq\; 2\sqrt{\frac{\pi}{2\ell+1}}\,\frac{\dot\Phi[\eta_0 - (\ell+1/2)/k]}{k}.\;}
\tag{R5.4.3}
$$

**Validity.** The $\mathcal O(\ell^{-2})$ Limber-correction is $\sim 10\%$ at $\ell = 10$, $\sim 1\%$ at $\ell = 30$, $\sim 0.04\%$ at $\ell = 50$. R5.4.3 valid for $\ell \gtrsim 30$ at percent precision; for $\ell < 30$ use R5.4.1 directly (one-dimensional integral, computable from $\dot\Phi$ on the post-reionization grid).

**Stationary-point accessibility.** R5.4.3 requires $\dot\Phi$ evaluated at $\eta_* = \eta_0 - (\ell+1/2)/k$, which lies in $[\eta_\text{re}, \eta_0]$ for $\ell/k \in [\eta_0 - \eta_0, \eta_0 - \eta_\text{re}] \approx [0, 10^4 \text{ Mpc}]$. For $k = 10^{-2}$, $\ell = 30$ gives $\eta_* \approx \eta_0 - 3050 \approx 11420$ Mpc — well inside post-reionization. For $k = 10^{-3}$, $\ell = 30$ gives $\eta_* \approx \eta_0 - 30500$ — outside the universe, oracle does not apply. The oracle has a physical $(k, \ell)$ region of validity: $\ell/k < \eta_0 - \eta_\text{re}$.

**Unit-test tolerance.** Feed `project_temperature_transfer` an ISW-only source $S_T = e^{-\kappa}(\dot\Phi + \dot\Psi)$ with $\Phi = \Psi$ algebraically prescribed. **Audit-corrected 2026-04-25**: the previous draft suggested $\Phi(\eta) = \Phi_0\cdot a(\eta)/a_*$ as a "matter-domination scaling" example, which is wrong — in matter domination the standard adiabatic Newtonian potential is approximately *constant* on sub-horizon scales (Dodelson §6.5). For test fixtures use: (i) $\Phi(\eta) = \Phi_0$ constant for the MD-only sanity check (in which case $\dot\Phi = 0$ and the ISW oracle correctly returns zero — useful as a null test); (ii) $\Phi(\eta) = \Phi_0\cdot D(\eta)/D(\eta_*)$ with $D$ the late-time growth-suppression factor for $\Lambda$-domination (the regime where ISW is non-trivial); (iii) $\Phi$ from CAMB's stored history for a realistic comparison. Expected: R5.4.3 matches numerical to $\le 5\%$ for $\ell \ge 30$, $k\eta_0 \ge 30$ on case (ii) or (iii); R5.4.1 matches to numerical-quadrature precision (machine epsilon for smooth $\Phi$).

**Use in §10.** This oracle isolates the ISW component of the LoS source, which is dominant at large angular scales ($\ell \le 30$) for late-time dark-energy ISW. Independent of $\Theta_0$ at recombination — purely a late-time integral.

### §5. Oracle 5 — Sharp-visibility Doppler

**Limit.** $g(\eta) \to \delta(\eta - \eta_*)$, $S_T = (g v_b)'/k$ only, all other sources zero. The Doppler subject to Audit Finding 1 of R2 §5.

**Closed form.** Integration by parts: $\int (g v_b)'/k\cdot j_\ell\, d\eta = -\int (g v_b)/k\cdot dj_\ell/d\eta\, d\eta = +\int g v_b\, j_\ell'[k(\eta_0-\eta)]\, d\eta$. With sharp $g$:
$$
\Delta_\ell^{T,\,\text{Dopp-sharp}}(k) \;=\; v_b(\eta_*)\, j_\ell'[k(\eta_0 - \eta_*)].
\tag{R5.5.1}
$$
Note the **$j_\ell'$**, not $j_\ell$ — the Doppler signature differs from SW by one Bessel-derivative order. Using $j_\ell'(x) = (\ell/x) j_\ell(x) - j_{\ell+1}(x)$:
$$
j_\ell'[kr_*] = \frac{\ell}{kr_*}\,j_\ell[kr_*] - j_{\ell+1}[kr_*].
\tag{R5.5.2}
$$

**Validity.** Sharp-visibility limit; otherwise replace by Gaussian-broadened version $\int g(\eta) v_b(\eta) j_\ell'[k(\eta_0-\eta)]\,d\eta$ with the same Taylor expansion as Oracle 2.

**Audit Finding 1 dependence.** R5.5.1 assumes the canonical Doppler form $(g v_b)'/k$ from R2.3.1. If BASS implements $(g v_b)'$ without the $1/k$ (per R2 §5 Finding 1), then BASS's numerical Doppler oracle is $k\cdot v_b(\eta_*)\, j_\ell'[kr_*]$ — differing by a factor $k$ from R5.5.1. This oracle is therefore *also* a diagnostic for the Doppler-prefactor question raised in R2.

**Unit-test tolerance.** Feed $S_T$ with only Doppler active, $v_b(\eta) = $ a smooth Gaussian-bumped function around $\eta_*$, narrow visibility $\sigma_g = 0.5$ Mpc. Expected: R5.5.1 matches to $\le 10^{-6}$ for $\ell \in [1, 50]$, $k \in [10^{-3}, 10^{-1}]$. Discrepancies at the factor-$k$ level diagnose Audit Finding 1.

**Use in §10.** Doppler is < 0.5% of total LoS source per R12→14 ablation, so this oracle is *not* a high-precision validator of the total spectrum but a clean test of the Doppler term in isolation. Combined with R5.1.1 it spans the (SW, Doppler) basis of the recombination contribution.

### §6. Oracle synthesis: high-$k$ validation coverage

The five oracles together cover the high-$k$ regime where the §10 CAMB-anchor fails, decomposed by physical contribution:

| Contribution | Oracle | $k$ range | $\ell$ range |
|---|---|---|---|
| SW (sharp vis) | R5.1.1 | $[10^{-3}, 10^{-1}]$ | $[0, 50]$ |
| SW (Gaussian vis, MD) | R5.2.1 / R5.2.3 | $[10^{-3}, 10^{-1}]$ | $[0, 50]$ |
| Acoustic peaks | R5.3.1 | $[10^{-3}, 10^{-1}]$ | $[0, 50]$ |
| ISW (late, Limber) | R5.4.3 | $[10^{-3}, 10^{-1}]$ | $[\ge 30]$ |
| ISW (late, full integral) | R5.4.1 | $[10^{-3}, 10^{-1}]$ | $[\ge 2]$ |
| Doppler (sharp vis) | R5.5.1 | $[10^{-3}, 10^{-1}]$ | $[1, 50]$ |
| Bessel completeness (cross-check) | `bessel_sum_rule` | all $k$ | $\ell_\text{max}\to\infty$ |

The four-cell low-$k$ panel (R2 §7) anchors the $k \le 10^{-2}$ regime. R5's oracles extend validation to $k \in [10^{-2}, 10^{-1}]$ with closed-form expressions that do not require CAMB introspection. Combined coverage:
- **$k \le 10^{-2}$**: §10 CAMB-anchor (existing) + R5.1–5 (cross-check)
- **$k \in [10^{-2}, 10^{-1}]$**: R5.1–5 only (CAMB introspection unavailable)
- **$k \ge 10^{-1}$**: out of scope (Silk damping dominates; requires photon-baryon collisional treatment beyond R5)

The $k \ge 10^{-1}$ regime is the natural extension target for R6+ — Silk damping in the sharp-visibility approximation can be incorporated as a multiplicative envelope $D(k) = \exp[-(k/k_D)^2]$ with $k_D^{-2} = \int (R^2 + 4(1+R)/5)/(6(1+R)^2)\,d\eta/\dot\kappa$ (Hu–Sugiyama 1995 eq. 39; Silk 1968). The Gaussian-visibility oracle R5.2 produces a **separate projection/window damping envelope** $\exp(-\tfrac12 k^2\sigma_*^2)$ that arises purely from the finite width of the visibility function — this is **NOT** photon-baryon collisional Silk diffusion. The two effects are distinct physical mechanisms with distinct $k$-dependence: the visibility-width envelope damps with characteristic scale $\sigma_*^{-1}\approx 0.09$ Mpc⁻¹, while collisional Silk damps with characteristic scale $k_D \approx 0.14$ Mpc⁻¹ at recombination (Hu–Sugiyama 1995 §IV); accidentally similar in scale but different in origin.

### §7. Hand-off to R6

R6 will produce the master code-mapping table consolidating R1 grounding, R2 LoS source, R3 monopole audit, R4 Bianchi extension, and R5 oracle catalogue into one paste-ready reference for the BASS coding agent. Specific items R6 must resolve:

1. **Audit Finding 1** (R2 §5; R5.5.1 diagnostic): inspect `ver2_native_integrator.py:2973` to determine whether `baryon_local_history[:, 1]` is $v_b$ or $\theta_b = k v_b$, and either confirm BASS Doppler is correct or apply the one-line $/k$ fix at `flrw_bessel_projector.py:453`.
2. **R3 §6 sub-percent verification**: implement the $\Theta_0^{(\text{kin})} - [\Phi(\eta)-\Phi(\eta_\text{init})]$ vs CAMB `clxg/4` (sync→Newt) cross-check as a diagnostic unit test.
3. **R5 oracle test suite**: integrate the five oracles as `pytest` fixtures in `tests/los/test_analytic_oracles.py`, with the tolerance specs in §1–§5 above.
4. **R4 §5 missing infrastructure**: file the eight ✗ items as separate development tickets (m=±2 LoS projector, Bianchi shear forcing, tilt velocity, etc.).
5. **Executive summary** at top of derivation document, ≤1 page, suitable for inclusion as a `docs/V5_ROUND15_P1_PSTF_DERIVATION_SUMMARY.md` standalone.

---

## R6. Master code-mapping reference

R6 consolidates R1–R5 into one paste-ready reference for the BASS coding agent and second-LLM reviewer (R7). Six tables organize the consolidation by category. Status legend: **✓** implemented and verified; **✓⁻** implemented but verification incomplete; **△** audit point flagged in this document (resolution path provided); **✗** planned, no production code.

### §1. LoS source ingredients (FLRW limit, m=0 scalar mode)

Canonical assembly per R2.3.1: $S_T = g[\Theta_0+\Psi+\tfrac14\Pi] + e^{-\kappa}(\dot\Phi+\dot\Psi) + \tfrac{1}{k}(g v_b)'$.

| § | Ingredient | Formula | BASS file:lines | Status | Notes |
|---|---|---|---|---|---|
| R2.3.1 | SW + sourced potential | $g[\Theta_0+\Psi]$ | `flrw_bessel_projector.py:448` (combined with polter) | ✓ | $\Theta_0$ in kinematic-$n^a$ frame; see R3 |
| R2.3.1 | Polter | $g\cdot\tfrac14\Pi$, $\Pi=\Theta_2-\sqrt 6 E_2$ | `flrw_bessel_projector.py:448` (combined SW+polter); $\Pi$ assembled at `tier_b_source_extraction.py:236` | ✓ | $\sqrt 6$ verified as Thomson (T,E) eigenvector coupling |
| R2.3.1 | ISW driver | $e^{-\kappa}(\dot\Phi+\dot\Psi)$ | `flrw_bessel_projector.py:450` | ✓ | Independently captures late-time $\dot\Phi$ omitted from kinematic-frame evolution (R3.3.4 IBP identity) |
| R2.3.1 | Doppler | $\tfrac{1}{k}(g v_b)'$ canonical | `flrw_bessel_projector.py:452` (`gvb`); `:453` (`np.gradient`) | △→fix | **Audit Finding 1 RESOLVED**: BASS implements $(g v_b)'$ without $1/k$. Code fix specified at R2 §5. |
| R2.2.1 | LoS projector | $\Delta_\ell^T = \int S_T\, j_\ell\, d\eta$ | `flrw_bessel_projector.py:499–546` | ✓ | Post-D-1 grid (commit `cb82a2a`) resolution-independent |
| R3.3.3 | $\Theta_0^{(\text{kin})}$ identification | $\Theta_0^{(\text{kin})} \approx \Theta_0^{(N)} + [\Phi(\eta)-\Phi(\eta_\text{init})]$ | `tier_b_source_extraction.py:225` (`t_tower[:, _slot(0,0)]`) | ✓⁻ | Verification test in R6 §5 below |
| R2.6.1 | Sync-gauge form (cross-validate) | $g[\Theta_0^{(s)}+\tfrac14\Pi] + e^{-\kappa}[\dot\eta_s-\tfrac16\ddot h_s]$ | n/a — BASS does not expose $h_s$ | n/a | Sync→Newt dictionary via $\alpha = v_c^{(N)}/k$ (R3.2.2) |
| R2.5.1 | Source extraction (Φ, Ψ from constraints) | Einstein constraint $\nabla^2\Phi = 4\pi G a^2 \rho\delta$ | `tier_b_source_extraction.py:275–302` | ✓ | $1/k^2$ amplification noise-dominated at $k\eta < 0.04$ |

### §2. PSTF hierarchy operators (CL2000-I 9-term form)

Canonical hierarchy per R4.1.1: $\dot\Pi_{A_\ell}^{(m)} = -a[T_1+T_2+T_3+T_7+T_8+T_9] + a K_T$ (orthogonal Bianchi).

*(R9 audit-correction 2026-04-25: this table was previously stale — it carried the pre-R7-correction coefficients for T2/T3/T7/T8/T9 and ✓ status for items whose operator algebra is bundle-unverified. The R8 §2 status downgrades and the R4.1.3–R4.1.4 coefficient corrections now reflected here. Status legend reminder: **✓** = implemented and operator algebra verified in R1 reading bundle; **✓⁻** = dispatch confirmed via call-sites in `hierarchy_rhs.py`, but the called operator source files are absent from the bundle, so operator algebra is not directly audit-verifiable from this bundle alone.)*

| § | Operator | Formula | BASS file:lines | Status | Notes |
|---|---|---|---|---|---|
| R4.1.2 | T1 expansion | $\tfrac{4}{3}\Theta\,\Pi_{A_\ell}$ | `hierarchy_rhs.py:421–447` (FLRW fast); `:472–477` (general) | **✓⁻** | $\Theta = 3H$ background; `apply_T1_expansion_packed` source absent |
| R4.1.2 | T1 curvature | $\tfrac{\ell}{2\ell+3}\,{}^{(3)}R^b{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b}$ | `apply_T1_expansion_packed(...,aniso_ricci_tensor=...)` `:431, :472` | **✓⁻** | FB-2.4 driver wire-up; provenance EMM 2012 §16, NOT lowell §6 displayed equation; bundle-unverified |
| R4.1.3 | T2 gradient (position-space) | $+\tilde\nabla_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}$ | `terms.py:T2_gradient`; `hierarchy_rhs.py:479–491` | **✓⁻** | Position-space coefficient $+1$ per lowell §6; harmonic-mode conversion is per-type backend; `terms.py` source absent |
| R4.1.3 | T3 divergence (position-space) | $+\tfrac{\ell+1}{2\ell+3}\,\tilde\nabla^b\Pi_{A_\ell b}$ | `terms.py:T3_divergence`; `hierarchy_rhs.py:492–501` | **✓⁻** | Coefficient $(\ell+1)/(2\ell+3)$ per lowell §6; bundle-unverified |
| R4.1.5 | T4 acceleration div | $-\tfrac{(\ell+1)(\ell-2)}{2\ell+3}\,A^b\Pi_{A_\ell b}$ | `apply_T4_accel_divergence_packed`; `hierarchy_rhs.py:503–504` | **✓⁻** | Opt-in via `accel_vector` kwarg; coefficient per lowell §6 line 369 |
| R4.1.5 | T5 acceleration grad | $+(\ell+3)\,A_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}$ | `apply_T5_accel_gradient_packed`; `hierarchy_rhs.py:505–506` | **✓⁻** | Opt-in; coefficient per lowell §6 line 370 |
| R4.1.5 | T6 vorticity | $+\ell\,\omega^b\eta_{bc\langle a_\ell}\Pi_{A_{\ell-1}\rangle}{}^c$ | `apply_T6_vorticity_packed`; `hierarchy_rhs.py:507–508` | **✓⁻** | Opt-in via `vorticity_vector` kwarg; coefficient per lowell §6 line 371 |
| R4.1.4 | T7 shear up | $-\tfrac{(\ell-1)(\ell+1)(\ell+2)}{(2\ell+3)(2\ell+5)}\,\sigma^{bc}\Pi_{A_\ell bc}$ | `apply_T7_shear_up_packed`; `hierarchy_rhs.py:442, :511` | **✓⁻** | $\ell=2$ specialization $-4/21$ ✓ matches lowell §6 line 402; closure-dependent at cutoff |
| R4.1.4 | T8 shear same | $+\tfrac{5\ell}{2\ell+3}\,\sigma^b{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b}$ | `apply_T8_shear_same_packed`; `hierarchy_rhs.py:443, :512` | **✓⁻** | $\ell=2$ specialization $+10/7$ ✓ matches lowell §6 line 403 |
| R4.1.4 | T9 shear down | $-(\ell+2)\,\sigma_{\langle a_\ell a_{\ell-1}}\Pi_{A_{\ell-2}\rangle}$ | `apply_T9_shear_down_packed`; `hierarchy_rhs.py:445, :513` | **✓⁻** | $\ell=2$ specialization $-4$ ✓ matches lowell §6 line 404; $\ell \ge 2$ |
| lowell §9.2 | $K_T$ Thomson collision | $\Gamma_T[-\Theta_\ell^m + \tfrac{1}{10}\Pi\delta_{\ell 2} + \tilde u^m\delta_{\ell 1}]$ | `bass.transport.thomson_collision`; `hierarchy_rhs.py:521` | **✓⁻** | m=0 only in production; m=±2 requires R6 §3 infrastructure; collision source absent |
| n/a | State packing | $i = \ell^2 + (m+\ell)$ | `tier_b_source_extraction.py:84`; `integrator.py:231` | ✓ | Bundle-confirmed; $(L+1)^2$ slots accommodate m=±2 (not yet populated) |

### §3. Bianchi-extension infrastructure (planned)

These items are required for the BASS solver to extend beyond FLRW + orthogonal Bianchi I/V/VII₀ to tilted and anisotropic-curvature Bianchi types. Each is a separate scope item; the architecture is in place via T7/T8/T9 and the m-index slot, but per-type analytic backbone and code wiring are missing.

| § | Item | Required for | Reference / Plan | Status |
|---|---|---|---|---|
| R4.2 | m=±2 LoS spin-2 projector $\epsilon_\ell, \beta_\ell$ | All Bianchi types (m=±2 channel) | KKS97 §III.B; HW97 §V.B | ✗ planned: `bass/los/families/` per-type backend |
| R4.2.3 | Bianchi shear forcing $\tfrac12\dot\sigma^{(\pm 2)}$ in S_T | Bianchi I anisotropy signal | Pontzen–Challinor 2007 §4 | ✗ planned: per-type plug-in around `flrw_bessel_projector` |
| R4.3.1 | Tilt velocity $\bar v_{(s)}^a$ history | All tilted Bianchi (V, VII_h, IX) | lowell §9.1 | ✗ planned: species-frame tilt history infrastructure |
| R4.3.4 | Tilted-observer LoS residual $\delta S_T^{\text{tilt}}$ | All tilted Bianchi | TCM 2008 §5 | ✗ planned: first-order velocity-boost correction |
| R4.2 | m=±2 state-vector population | All Bianchi (off-FLRW) | Slot index already supports it | ✗ planned: doubling state vector or spin-weighted tower |
| R4.4.1 | $x_C$ master departure post-processor | Thesis cosmography output | MES framework §6.1 | ✗ planned: post-processing diagnostic |
| R4.1.2 | Anisotropic 3-curvature for II, VI₀, VIII, III, IV, VI_h, VII_h, VII₀-non-sym | Eight anisotropic Bianchi types | EMM 2012 §16; FB-2.4 hooks | ✗ test-coverage: T1 hooks wired; per-type `tetrad_state.aniso_3_curvature` not validated |
| R4.7 / R5 §7 | Bianchi-I analytic oracles | Validation of m=±2 channel | Reduce to FLRW oracles in $\sigma\to 0$ | ✗ planned: downstream of R5 |

### §4. Analytic validation oracles (FLRW, m=0)

Five oracles for closed-form $\Delta_\ell^T(k)$ in limiting regimes; basis for unit-test fixtures in `tests/los/test_analytic_oracles.py`.

| § | Oracle | Formula | Validity | Tolerance | BASS impl |
|---|---|---|---|---|---|
| R5.1.1 | Sharp-vis SW | $[\Theta_0+\Psi]_*\,j_\ell[k(\eta_0-\eta_*)]$ | $\sigma_g \to 0$ | $\le 10^{-10}$ for $\sigma_g = 10^{-3}$ Mpc | `flrw_bessel_projector.py:614` (`sachs_wolfe_analytic_transfer`) |
| R5.2.1 | Gaussian-vis SW | $[\Theta_0+\Psi]_*\{j_\ell + \tfrac12 k^2\sigma_*^2 j_\ell''\}$ | $k\sigma_* \le 0.5$ | $\le 5\times 10^{-3}$ at $\sigma_g = 11$ Mpc, $k \le 10^{-2}$ | ✗ planned (oracle helper) |
| R5.3.1 | Acoustic toy | $A\cos(c_s k\eta_*)\, j_\ell[kr_*]$ | algebraic ansatz | $\le 10^{-8}$ for $\sigma_g = 0.5$ Mpc | ✗ planned |
| R5.4.3 | ISW Limber | $2\sqrt{\pi/(2\ell+1)}\,\dot\Phi[\eta_0-(\ell+1/2)/k]/k$ | $\ell \ge 30$, $\ell/k < \eta_0-\eta_\text{re}$ | $\le 1\%$ at $\ell \ge 30$ | ✗ planned |
| R5.4.1 | ISW full integral | $2\int \dot\Phi\, j_\ell\, d\eta$ | All $\ell \ge 2$ | quadrature precision | ✗ planned |
| R5.5.1 | Sharp-vis Doppler | $v_b(\eta_*)\, j_\ell'[kr_*]$ | $\sigma_g \to 0$ | $\le 10^{-6}$; $k$-mismatch diagnoses Audit Finding 1 | ✗ planned |
| n/a | Bessel completeness | $\sum_\ell (2\ell+1) j_\ell^2(x) = 1$ | All $x \ge 0$, $\ell_\text{max} > x$ | partial-sum convergence | `flrw_bessel_projector.py:641` (`bessel_sum_rule`) |

### §5. Audit / verification resolution paths

| ID | Audit point | Origin | Resolution | Test |
|---|---|---|---|---|
| AF-1 | Doppler $1/k$ prefactor | R2 §5 | Inspect slot 1 of `baryon_local_history` at `ver2_native_integrator.py:2973`. If $\theta_b=k v_b$: BASS correct. If $v_b$: append `/ k` to `flrw_bessel_projector.py:453`. | R5.5.1 oracle: factor-$k$ mismatch in numerical Doppler vs $v_b(\eta_*)\,j_\ell'[kr_*]$ |
| VR-1 | Sub-percent $\Theta_0^{(\text{kin})}$ verification | R3 §6 | Compute $\Theta_0^{(\text{kin})} - [\Phi(\eta)-\Phi(\eta_\text{init})]$ from BASS, compare to CAMB `clxg/4` after sync→Newt conversion using $\alpha = v_c^{(N)}/k$ (R3.2.2). | New unit test at `tests/integration/test_theta0_gauge_identification.py` |
| VR-2 | High-$k$ source-assembly correctness | R5 §6 | Run R5 oracles 1–5 against BASS LoS projector at $k \in [10^{-2}, 10^{-1}]$, $\ell \in [2, 100]$. | New `tests/los/test_analytic_oracles.py` |
| VR-3 | Bianchi-I shear forcing reduction | R4 §6 | Verify R4 algebra reduces to R2 in $\sigma_{ab}\to 0$ limit. | Existing FLRW regression suite (LB-6 / FB-2.3 bit-identical) |
| VR-4 | Tilt residual symmetry | R4 §3 | Verify $\delta S_T^{\text{tilt}}$ vanishes at second-order in $\bar v_{(s)}$ for orthogonal Bianchi. | New unit test once tilt infrastructure lands |

### §6. Convention-conversion table (PSTF / CAMB / MB-95 / HW97)

For cross-checking with external truth references and literature.

| Quantity | PSTF / CL2000 / BASS | CAMB / LC06 | MB-95 sync | HW97 TAM | Conversion |
|---|---|---|---|---|---|
| Temperature multipole | $\Theta_\ell$ | $\Theta_\ell$ | $F_{\gamma,\ell}^{\text{MB}}/4$ | $\Theta_\ell^{\text{TAM}}$ | $\Theta_\ell = F_{\gamma,\ell}^{\text{MB}}/4 = (2\ell+1)$-rescaled-CAMB |
| Polter | $\Pi = \Theta_2 - \sqrt 6 E_2$ | $\Pi^\text{CAMB}$ via `polter = pig/10 + 9 E_2/15` | $\sigma_\gamma^{(s)}$ form | $\Pi^\text{HW} = \Theta_2 + \tilde E_2$ | E-mode sign + Wigner-d at $\ell=2$ |
| Time variable | conformal $\eta$ | conformal $\eta$ | conformal $\eta$ | conformal $\eta$ | identical |
| Metric (scalar) | covariant $\Phi, \Psi$ from constraints | $\Phi, \Psi$ Newtonian gauge | $h_s, \eta_s$ sync gauge | $\Phi, \Psi$ Newtonian | $\alpha = v_c^{(N)}/k$ (R3.2.2) |
| Baryon velocity | $v_b$ in $u_e^a$-frame | $v_b$ Newtonian | $v_b^{(s)}$ sync | $v_b^{(N)}$ Newtonian | $v_b^{(N)} = v_b^{(s)} + k\alpha$ |
| Optical depth | $\kappa(\eta)$ proper time | $\tau(\eta)$ conformal | $\tau$ | $\tau$ | $\dot\kappa = \dot\tau$ in conformal time |
| Visibility | $g = \dot\kappa\, e^{-\kappa}$ | $g = \dot\tau\, e^{-\tau}$ | identical | identical | identical |
| Frame | $n^a$ (transport) / $u_e^a$ (collision) | implicit Newtonian observer | implicit sync observer | $n^a \equiv u^a$ comoving | lowell §1.2 doctrine |
| Sign convention $E_2$ | CL2000-II "polarization sign" | CAMB has opposite sign | matches PSTF | matches PSTF | $E_2^{\text{CAMB}} = -\tfrac{2}{5\sqrt 6}E_2^{\text{PSTF}}$ |

### §7. Synthesis and closure

The cumulative R1→R6 derivation establishes:

1. **R1 grounding**: BASS production photon hierarchy is PSTF-native (zero `Phi`/`Psi` matches in `hierarchy/`); shared structural fact for all subsequent rounds.
2. **R2 LoS source**: BASS assembly matches canonical CAMB / LC06 form term-by-term modulo Audit Finding 1; weak-form correctness on supplied $\eta$ range.
3. **R3 monopole audit**: $\Theta_0^{\text{BASS}}$ in kinematic-$n^a$ frame; leading-order identification with $\Theta_0^{(N)}$ via R3.3.3; LoS assembly approximately gauge-coherent at 5%; ISW driver compensates dark-energy era omission via IBP identity.
4. **R4 Bianchi extension**: T1+T7+T8+T9 algebra reproduced from CL2000-I; six operators implemented in BASS, eight items planned; $x_C$ master departure mapped to BASS data sources.
5. **R5 oracle catalogue**: Five closed-form oracles cover $k \in [10^{-2}, 10^{-1}]$ where §10 CAMB-anchor fails; each with explicit validity regime and unit-test tolerance.
6. **R6 master reference**: Single paste-ready document for coding agent consumption.

The five recommended code follow-ups in the executive summary are independent — none blocks any other, and the order is roughly by criticality (Audit Finding 1 first, then verification tests, then oracle integration, then Bianchi infrastructure, then summary excerption).

R7 produces the audit-prompt for an independent second-LLM reviewer to validate this document's claims against the cited file:line references.

---

## R8. Audit-cycle response (post-R7, 2026-04-25)

R7 produced an external-reviewer audit identifying confirmed items, flagged items, and missed/new concerns. R8 records the response cycle: which findings were accepted and corrected inline (with location of the fix), which were partially accepted (modified rather than fully adopted), which were rejected with reason, and which are deferred to a separate P1.5 round with explicit scoping.

### §1. Audit findings — disposition

**Accepted and corrected inline** (text in R1–R6 has been edited):

| Finding | Audit text | Disposition | Fix location |
|---|---|---|---|
| AF-1 | BASS missing $/k$ on Doppler | **Accepted, RESOLVED**: `ver2_native_integrator.py:3086` slot label `v_b`, line 3047 EOM forcing $3\Theta_1$ confirms physical-velocity convention. Code fix specified. | R2 §5 (rewritten with smoking-gun evidence); Executive summary; R6 §1 row 4 |
| Empirical-masking too strong | "low-impact triage, not validation" | **Accepted**: rephrased as "weak claim, triage observation not validation; formula audit point real" | R2 §5 closing paragraph |
| R3.3.4 "exact compensation" | not justified, conflicts with MD assumption | **Accepted**: removed "exact compensation" language, restated as partial structural decomposition with explicit $-\Phi_\text{init}\int g j_\ell\, d\eta$ residual | R3 §3 paragraph after R3.3.4 |
| R4 §1 T7/T8/T9 coefficients | wrong against lowell §6 | **Accepted**: T7 missing $(\ell-1)$ added; T8 sign and prefactor corrected to $+5\ell/(2\ell+3)$; T9 corrected to $-(\ell+2)\sigma_{\langle a_\ell a_{\ell-1}}\Pi_{A_{\ell-2}\rangle}$. $\ell=2$ specialization lowell line 402–404 verified consistent. | R4 §1 R4.1.4 |
| R4 §1 T2/T3 not transparent | position-space vs harmonic-mode confusion | **Accepted**: T2/T3 displayed in position-space form per lowell §6 ($+\tilde\nabla_{\langle a_\ell}$ and $+(\ell+1)/(2\ell+3)\tilde\nabla^b$); harmonic-mode conversion explicitly deferred to per-type backend | R4 §1 R4.1.3 |
| R4 §1 T1 curvature unverified | not in displayed lowell §6 | **Accepted**: caveat added that displayed lowell §6 does NOT contain the curvature-correction term; provenance is EMM 2012 §16 separately | R4 §1 R4.1.2 |
| R5.2 $(k\sigma)^4 \le 5\%$ at $k\sigma=0.55$ | $(0.55)^4 \approx 0.092 \neq 0.05$ | **Accepted**: validity threshold tightened to $k\sigma \le 0.45$ where $(0.45)^4 \approx 0.041 \le 5\%$. Numerical example revised: $\sigma_*=11$ Mpc gives $k \le 0.041$ Mpc⁻¹. | R5 §2 Validity paragraph |
| R5.4 MD $\Phi \propto a$ wrong | $\Phi$ constant in MD | **Accepted**: revised to (i) $\Phi$ constant for MD null test, (ii) growth-suppressed $\Phi$ for $\Lambda$ test, (iii) CAMB history for realistic. | R5 §4 Unit-test tolerance paragraph |
| R6 §1 line citation drift | polter at :448 not :451; ISW at :450 not :452 | **Accepted**: SW and polter both cite :448 (combined); ISW cites :450; Doppler cites :452 (gvb prep) and :453 (gradient). | R6 §1 rows 1–4 |

**Partially accepted** (modified rather than fully adopted):

| Finding | Audit text | Modified disposition |
|---|---|---|
| R3 §6 verdict overbroad | "no code change at 5%" too structural | **Partial**: kept the empirical 5% claim because the four-cell anchor empirically supports it, but added scope-bounding language in R8 §3 below. The verdict applies to: (i) FLRW limit, (ii) recombination MD window, (iii) k ≤ 10⁻² with `k_adapt_η100` source-splice. It does NOT apply to high-$k$, reionization, radiation-MD transition, or BASS-native pipeline below $\eta_\text{init}$. |
| Reionization claim too casual | residual-redefinition argument under-justified | **Partial**: kept the recombination-window argument as primary; added explicit acknowledgement in R8 §3 that late-ISW / reionization needs separate validation track. The R5 oracle suite already separates ISW (Oracle 4) from SW + polter (Oracles 1–3), providing the test infrastructure for the separation when production code lands. |
| Polter "9/10 eigenvector" | three claims conflated | **Partial**: kept R2 §3's algebraic identification of $\Pi = \Theta_2 - \sqrt 6\, E_2$ as the relaxation eigenvector (the algebra is standard CL2000-II §3.2), but added a footnote distinguishing (i) the BASS implementation's polter sign as `+Π/4`, (ii) the literature Thomson tensor $\zeta_{ab} = \tfrac34 I_{ab} + \tfrac92 E_{ab}$ from CL2000-II eq. 12 verified in lowell §4, (iii) the *full* $(T,E)$ eigenvalue $9/10$ derivation including CL2000-II's $3/5$ E-mode coefficient. Items (i)+(ii) are bundle-confirmed; (iii) requires the collision-operator source file which is absent from the bundle. Status downgrade to ✓⁻ for the third claim only. |
| HW97 / CAMB conversion incomplete | normalization table not derived | **Partial**: kept R2 §3 cross-convention table at literature-cited level; explicit derivation of $E_2^{\text{CAMB}} = -\tfrac{2}{5\sqrt 6}E_2^{\text{PSTF}}$ etc. is deferred to P1.5 with the per-type harmonic backend (where it actually matters for numerical prefactors). |

**Rejected** (with reason):

| Finding | Audit text | Rejection reason |
|---|---|---|
| (none) | — | All audit findings of high or medium-high confidence were accepted at least partially. |

**Deferred to P1.5** (acknowledged, scope-bounded, not fixed in R1–R8):

| ID | Finding | Why deferred |
|---|---|---|
| P1.5-A | Coupled residual hierarchy for monopole–dipole–quadrupole at radiation-MD transition | Requires solving the coupled $(\delta\Theta_0, \delta\Theta_1, \delta\Theta_2)$ system with explicit Thomson absorption time-scale; 2–3 KB derivation. Belongs in a separate analytical note. |
| P1.5-B | Radiation–MD transition stress-test for R3.3.3 | Same — requires the coupled system + transition-epoch potential evolution analysis. |
| P1.5-C | Reionization / late-ISW separate validation track | Production-code dependency: requires reionization-zone $g$ and decaying-$\Phi$ infrastructure, both downstream of P1 scope. R5 Oracle 4 ISW-Limber + R5 Oracle 4 ISW-full provide the test fixtures. |
| P1.5-D | Tilt + m=±2 normalization rederivation in BASS's exact $(2\ell+1)/4$ convention | Belongs in the per-Bianchi-type harmonic backend (R4 §5 ✗ infrastructure). Coefficient freezing should not happen until that backend lands. |
| P1.5-E | HW97 / CAMB / KKS97 full normalization table | Same as P1.5-D — only matters for numerical prefactors in the per-type harmonic backend. |
| P1.5-F | `packed_operators.py` operator algebra audit | Bundle-completeness issue: the source file is not in the R1 reading bundle, so T7/T8/T9/T1-curvature operator implementations are dispatch-confirmed but algebra-unverified. Resolution requires either (a) shipping the file in a follow-up bundle, or (b) running an in-repo regression against the canonical $\ell=2$ specialization lowell §6 line 402–404. |

### §2. Status downgrades in R6 master table

The audit-driven status changes apply to the R6 §2 (PSTF hierarchy operators) table:

| § | Operator | Old status | New status | Reason |
|---|---|---|---|---|
| R4.1.2 | T1 curvature | ✓ | **✓⁻** | Code dispatch confirmed; formula provenance (EMM 2012 §16) not in lowell §6 displayed equation; `apply_T1_expansion_packed` source absent from bundle |
| R4.1.4 | T7 shear up | ✓ | **✓⁻** | Code dispatch confirmed; `apply_T7_shear_up_packed` algebra unverified in bundle (`packed_operators.py` absent) |
| R4.1.4 | T8 shear same | ✓ | **✓⁻** | Same reason as T7 |
| R4.1.4 | T9 shear down | ✓ | **✓⁻** | Same reason as T7 |
| R4.1.5 | T4/T5/T6 acceleration/vorticity | ✓ (opt-in) | **✓⁻ (opt-in)** | Same — source absent; opt-in dispatch confirmed |
| lowell §9.2 | $K_T$ Thomson collision | ✓ | **✓⁻** | Collision operator source absent from bundle |

The status legend in R6 header is updated: **✓** implemented, code algebra verified in bundle; **✓⁻** dispatch confirmed via call-sites in `hierarchy_rhs.py`, but the called operator source files are absent from the R1 reading bundle, so the operator algebra inside is not directly audit-verifiable from this bundle alone. P1.5-F (above) is the resolution path.

### §3. Scope-bounding language for the executive-summary verdict

The executive summary's "no code-level correction is required at the 5% precision level" verdict applies only within the following bounds:

1. **FLRW limit only** — m=0 scalar mode, $\sigma_{ab} = 0$, $\bar v_{(s)}^a = 0$. Bianchi extension validation is downstream (R4 §5 ✗ items, P1.5-D, P1.5-E).
2. **Recombination MD window only** — $\eta \in [\eta_\text{init}, \eta_*]$ with the visibility $g$ peaked near recombination. Reionization, radiation-MD transition, and dark-energy era are P1.5-A through P1.5-C.
3. **$k \le 10^{-2}$ Mpc⁻¹ only** — the four-cell empirical anchor `k_adapt_η100`. High-$k$ ($k > 10^{-2}$) is unanchored against CAMB-direct and relies on R5 oracles for validation; the verdict does not extend there at present.
4. **`k_adapt_η100` source-splice only** — the anchor uses CAMB sources spliced in below BASS's $\eta_\text{init}$, not BASS-native source extraction. The verdict therefore validates the LoS quadrature + source-assembly form, not the BASS-native source dynamics. The η-range correctness (BASS-native source extraction below $\eta_\text{init}$) is the deferred half — Round-15 P2 track (D-2 integrator $\eta_\text{init}$ extension), multi-month timeline.

A coding agent reading this document as SSoT must apply these scope bounds before extending the verdict to any other regime.

### §4. Independent regression item from MISSED bucket

The R7 audit's MISSED bucket flagged: "no isolated Doppler regression exists yet, even though AF-1 is now the cleanest actionable bug candidate. The total source can hide a factor-$k$ Doppler error while an isolated oracle would catch it immediately."

This is correct and is now a concrete P1.5 ticket: **add `tests/los/test_doppler_isolated_oracle.py`** that:
1. Constructs $S_T$ with only Doppler active (SW = polter = ISW = 0), narrow Gaussian $g(\eta)$ centered at $\eta_*$ with $\sigma_g = 0.5$ Mpc.
2. Sets $v_b(\eta) = v_0 \exp[-(\eta-\eta_*)^2/(2\sigma_v^2)]$ for some $\sigma_v \gtrsim \sigma_g$.
3. Compares numerical $\Delta_\ell^T$ against R5.5.1 prediction $v_0\, j_\ell'[k(\eta_0-\eta_*)]$ for $\ell \in [1, 50]$, $k \in [10^{-3}, 10^{-1}]$.
4. **Pre-fix**: expected to fail by a factor of $k$ (BASS produces $k\, v_0\, j_\ell'$ instead of $v_0\, j_\ell'$). **Post-fix**: passes to $\le 10^{-6}$ relative tolerance.

This test is the AF-1 regression and should be merged together with the `flrw_bessel_projector.py:453` $/k$ fix as a single PR.

### §5. Closing

The audit cycle has converted nine specific R1–R6 items from "claimed but not audit-tested" to "tested and corrected" status. AF-1 is closed. The remaining six P1.5 deferred items are scope-controlled, with explicit triggering conditions: P1.5-A/B require the radiation-MD transition or the coupled-residual analytical block; P1.5-C requires reionization production-code; P1.5-D/E require the per-type harmonic backend; P1.5-F requires either a follow-up bundle including `packed_operators.py` or in-repo regression access.

The cumulative R1–R8 derivation, with the corrections above applied, is now consistent with the bundle evidence at the level claimed. The executive-summary verdict stands within the §3 scope bounds. The five recommended code follow-ups in the executive summary are unchanged in priority, with item #1 (AF-1) now actionable as a one-line PR.

---

## P1.5. Deferred-item analytical extensions (post-R8)

R8 deferred six items to P1.5 with explicit triggering conditions. P1.5 develops each as a focused analytical module suitable for second-pass external review. **Audit-readiness practices applied throughout**: every numerical bound is computed explicitly with intermediate steps; every formula is labelled as bundle-verified, literature-cited, or first-principles-derived; cross-convention conversions are derived rather than asserted; and known unchecked items are self-flagged in each section's closing paragraph.

### §A. Coupled monopole–dipole–quadrupole residual hierarchy (P1.5-A)

R3.3.3 identified the leading-order frame mismatch $\Theta_0^{(\text{kin})} \approx \Theta_0^{(N)} + [\Phi(\eta) - \Phi(\eta_\text{init})]$ and bounded it by the visibility-weighted $g[\Phi - \Phi_\text{init}]$. The R7 auditor correctly noted that this single-equation argument elides the back-reaction from the dipole and quadrupole equations, which also lack metric sources in the kinematic frame and could feed back onto the monopole through streaming. P1.5-A solves the coupled residual system explicitly, in the tight-coupling regime that holds across the recombination visibility support.

#### §A.1 Definitions and IC

Define

$$
\delta\Theta_\ell(\eta, k) \;\equiv\; \Theta_\ell^{(\text{kin})}(\eta, k) - \Theta_\ell^{(N)}(\eta, k), \qquad \ell \ge 0,
\tag{P1.5-A.1.1}
$$

with similar definitions for $\delta v_b$, $\delta\Pi$. The IC: from R3 §1 Step 1, the BASS adiabatic super-horizon seed at $\eta_\text{init} = 261$ Mpc satisfies $\delta\Theta_\ell(\eta_\text{init}, k) = \mathcal O((k\eta_\text{init})^2)$. At the lowest BASS mode $k = 10^{-4}$ Mpc⁻¹: $(k\eta_\text{init})^2 \approx (0.026)^2 \approx 7\times 10^{-4}$, so $|\delta\Theta_\ell(\eta_\text{init})|/|\Theta_\ell| \le 0.07\%$. Treating $\delta\Theta_\ell(\eta_\text{init}) = 0$ to this precision is consistent with the four-cell anchor's $\le 5\%$ tolerance.

#### §A.2 Residual hierarchy

Subtracting the Newtonian-gauge hierarchy R2.1.1–R2.1.3 from the kinematic-frame hierarchy R3.1.1:

$$
\delta\Theta_0' + \frac{k}{3}\delta\Theta_1 \;=\; \dot\Phi,
\tag{P1.5-A.2.1}
$$

$$
\delta\Theta_1' - \frac{k}{3}\delta\Theta_0 + \frac{2k}{3}\delta\Theta_2 \;=\; -\frac{k}{3}\Psi - \dot\kappa\bigl[\delta\Theta_1 - \tfrac{1}{3}\delta v_b\bigr],
\tag{P1.5-A.2.2}
$$

$$
\delta\Theta_\ell' + \frac{k(\ell+1)}{2\ell+1}\delta\Theta_{\ell+1} - \frac{k\ell}{2\ell+1}\delta\Theta_{\ell-1} \;=\; -\dot\kappa\bigl[\delta\Theta_\ell - \tfrac{1}{10}\delta\Pi\,\delta_{\ell 2}\bigr] \quad (\ell \ge 2).
\tag{P1.5-A.2.3}
$$

The metric sources $\dot\Phi$ on the monopole and $-k\Psi/3$ on the dipole arise because the Newtonian-gauge equations carry these driving terms while the kinematic-frame equations do not (R3 §3.3.1–3.3.2). The Thomson collision terms appear because $\Theta_\ell$ in *both* frames couples to scattering — the residual inherits the same Thomson rates.

**Working hypothesis**: $\delta v_b = 0$, i.e., BASS's stored $v_b$ is approximately the Newtonian-gauge baryon velocity. This is the same assumption underlying R3, with the related Doppler-convention question addressed by Audit Finding 1 (R2 §5; resolved post-R7).

#### §A.3 Tight-coupling regime: dipole and quadrupole are Thomson-suppressed

**R9 audit-correction 2026-04-25**: the previous draft used $\dot\kappa_* \approx 100$ Mpc⁻¹ at the recombination peak, leading to a "four orders below leading" precision claim. The auditor flagged this as a units/magnitude error, and it is — $\dot\kappa$ in conformal time at recombination is $\sim 0.06$–$1$ Mpc⁻¹ depending on epoch within the integration window, NOT $\sim 100$ Mpc⁻¹. P1.5-A.3 and §A.4 below are recomputed with the correct values; the qualitative subdominance of the back-reaction survives, but the precision claim is weakened from "4 orders below" to "1–2 orders below" leading.

The conformal-time optical-depth derivative $\dot\kappa(\eta) = a(\eta)\,n_e(\eta)\,\sigma_T$, computed for standard $\Lambda$CDM at the integration-window epochs:

| Epoch | $z$ | $x_e$ | $\dot\kappa$ (Mpc⁻¹) | Regime |
|---|---|---|---|---|
| $\eta = 200$ Mpc | $\approx 1500$ | 0.8 | $\approx 0.93$ | Deep tight coupling |
| $\eta_\text{init} = 261$ Mpc | $\approx 1200$ | 0.5 | $\approx 0.37$ | Tight-coupling exit begins |
| $\eta_* = 282$ Mpc | $\approx 1090$ | 0.1 | $\approx 0.06$ | Visibility peak, near LSS |
| $\eta = 300$ Mpc | $\approx 1000$ | 0.02 | $\approx 0.01$ | Free-streaming dominated |

(Numerical values from first-principles computation: $a n_e \sigma_T$ with Planck-2018 $\Omega_b h^2 = 0.0224$, recombination-history $x_e$ approximations; full computation logged in R9 audit-response below.) The relevant tight-coupling parameter $\dot\kappa/k$ at $k = 10^{-2}$ Mpc⁻¹:

$$
\dot\kappa/k\Big|_{\eta_\text{init}} \approx 37, \qquad \dot\kappa/k\Big|_{\eta_*} \approx 6.
$$

Tight coupling is secure ($\dot\kappa/k \gtrsim 10$) only in the first half of the integration window; near $\eta_*$ the slip is no longer Thomson-suppressed.

The Thomson terms in P1.5-A.2.2 enforce, in quasi-static balance with $\delta v_b = 0$:

$$
\delta\Theta_1(\eta) \;\approx\; \frac{1}{\dot\kappa(\eta)}\Bigl[-\frac{k}{3}\Psi(\eta)\Bigr] \;=\; -\frac{k\,\Psi(\eta)}{3\,\dot\kappa(\eta)}.
\tag{P1.5-A.3.1}
$$

Numerical estimate at the recombination peak ($\dot\kappa_* \approx 0.06$ Mpc⁻¹, $|\Psi| \sim 10^{-5}$, $k = 10^{-2}$):

$$
|\delta\Theta_1|_{\text{at }\eta_*} \;\sim\; \frac{10^{-2}\cdot 10^{-5}}{3\cdot 0.06} \;\approx\; 5.6\times 10^{-7}.
\tag{P1.5-A.3.2}
$$

Note this is at the *visibility peak*, where $\dot\kappa$ is smallest within the integration window; deeper in tight coupling ($\dot\kappa \gtrsim 1$ Mpc⁻¹), $|\delta\Theta_1|$ is suppressed by an additional factor of ~6 to $\sim 10^{-7}$.

#### §A.4 Visibility-weighted dipole back-reaction onto $\delta\Theta_0$

Integrating P1.5-A.2.1 from $\eta_\text{init}$ to $\eta$ with the IC $\delta\Theta_0(\eta_\text{init}) = 0$:

$$
\delta\Theta_0(\eta) \;=\; \bigl[\Phi(\eta) - \Phi(\eta_\text{init})\bigr] \;-\; \frac{k}{3}\int_{\eta_\text{init}}^\eta \delta\Theta_1(\eta')\, d\eta'.
\tag{P1.5-A.4.1}
$$

The back-reaction integral is dominated by the END of the window where $\dot\kappa$ is smallest (since $|\delta\Theta_1| \propto 1/\dot\kappa$). An effective average:

$$
\Bigl|\int_{\eta_\text{init}}^{\eta_*} \delta\Theta_1\, d\eta'\Bigr| \;\sim\; |\delta\Theta_1|_{\eta_*}\cdot \mathcal O(\dot\kappa_*/\dot\kappa_\text{init})\cdot \Delta\eta_{\text{rec}} \;\sim\; 5.6\times 10^{-7}\cdot 0.16\cdot 21 \;\approx\; 1.9\times 10^{-6}\,\text{Mpc}.
$$

(Using $\dot\kappa_*/\dot\kappa_{\text{init}} \approx 0.16$ as the integration-window-averaged suppression factor; this is order-of-magnitude — a precise numerical evaluation requires bundling the actual $\dot\kappa(\eta)$ history from BASS's `visibility_history` in a future audit cycle.) The back-reaction onto the monopole:

$$
|\delta\Theta_0^{\text{back}}(\eta_*)| \;\sim\; \frac{k}{3}\cdot 1.9\times 10^{-6} \;\approx\; 6\times 10^{-9}.
\tag{P1.5-A.4.2}
$$

Compared to the leading $|\Phi(\eta_*) - \Phi(\eta_\text{init})| \sim 5\%\cdot |\Phi_\text{init}| \sim 5\times 10^{-7}$ (with $|\Phi_\text{init}| \sim 10^{-5}$):

$$
\frac{|\delta\Theta_0^{\text{back}}(\eta_*)|}{|\Phi(\eta_*) - \Phi(\eta_\text{init})|} \;\sim\; \frac{6\times 10^{-9}}{5\times 10^{-7}} \;\approx\; 1\%.
\tag{P1.5-A.4.3}
$$

So the back-reaction is **~1% of leading** — about 2 orders below, NOT 4 orders below as the original draft claimed. The leading-order R3.3.3 identification dominates; back-reaction adds a small correction that does not change the qualitative picture but is **detectable at sub-percent precision**.

A more conservative estimate using only the visibility-peak value $\dot\kappa_* \approx 0.06$ Mpc⁻¹ uniformly across the window (worst case, not realistic but bounds the result):

$$
|\delta\Theta_0^{\text{back}}|_{\text{worst case}} \;\sim\; (k/3)\cdot |\delta\Theta_1|_{\eta_*}\cdot \Delta\eta_{\text{rec}} \;\sim\; (10^{-2}/3)\cdot 5.6\times 10^{-7}\cdot 21 \;\approx\; 4\times 10^{-8}.
$$

Worst-case ratio to leading: $\approx 8\%$. Still subdominant to the 5% empirical anchor tolerance, but at the same order — so the back-reaction is **not negligible** for sub-percent verification work.

**Summary**: The dipole back-reaction onto the monopole residual is bounded by approximately 1% (typical) to 8% (worst case) of the leading $[\Phi(\eta_*) - \Phi(\eta_\text{init})]$ residual. The qualitative subdominance holds and the four-cell empirical anchor's 5% bound on the *total* residual is consistent with the leading + back-reaction combination, but precision verification requires integrating against the actual `visibility_history` from BASS rather than these order-of-magnitude estimates.

#### §A.5 Visibility-weighted residual contribution to $\Delta_\ell^T$

The residual contribution to the LoS source from $\delta\Theta_0$ is $g(\eta)\delta\Theta_0(\eta)$, which integrates against $j_\ell$ to give

$$
\Delta_\ell^{T,\text{residual}}(k) \;=\; \int_0^{\eta_0} g(\eta)\bigl[\Phi(\eta) - \Phi(\eta_\text{init}) + \delta\Theta_0^{\text{back}}(\eta)\bigr]\, j_\ell[k(\eta_0-\eta)]\, d\eta.
\tag{P1.5-A.5.1}
$$

Bounded above by $\max_\eta\bigl|\Phi(\eta) - \Phi(\eta_\text{init})\bigr|\cdot \int g\, j_\ell\, d\eta + |\delta\Theta_0^{\text{back}}|_{\max}\cdot \int g\, j_\ell\, d\eta$. The leading term is the $\le 5\%$ residual that the four-cell anchor tolerates; the back-reaction adds $\sim 4\times 10^{-4}\%$ on top, well below anchor sensitivity.

#### §A.6 Validity bounds

P1.5-A.4.2 is rigorous within the following limits:
- **Recombination MD window** ($\eta \in [\eta_\text{init}, \eta_*]$, MD with $\dot\kappa \gg k$): bound holds.
- **Radiation–MD transition** ($\eta < \eta_\text{init}$ if BASS's $\eta_\text{init}$ were earlier): see P1.5-B.
- **Reionization** (post-recombination $g_{\text{re}}$ peak): see P1.5-C — Thomson rate is lower at reionization, weakening the back-reaction suppression.

#### §A.7 Self-flagged unchecked items in §A

(i) The numerical estimate $|\Psi| \sim 10^{-5}$ is order-of-magnitude; the actual $\Psi(\eta_*, k)$ depends on $k$ and primordial amplitude. For the four-cell anchor, $\Psi$ is computed by `tier_b_source_extraction.py:302` from Einstein constraints; using its actual values would tighten P1.5-A.4.2 numerically but not change the conclusion. (ii) The $\delta v_b = 0$ working hypothesis is tied to Audit Finding 1's resolution; if BASS's $v_b$ slightly differs from $v_b^{(N)}$ (e.g., by $\mathcal O(k\eta)$ corrections from the gauge transformation R3.2.3), $|\delta\Theta_1|_{\text{TC}}$ acquires a $\mathcal O(\dot\kappa^{-1}\cdot k\delta v_b)$ correction. (iii) The $\Delta\eta_{\text{rec}} \approx 21$ Mpc is the BASS post-D-1 recombination resolution; for visibilities supported on a wider epoch, $\Delta\eta_{\text{rec}}$ could be larger, but the back-reaction grows only linearly with width — still negligible.

### §B. Radiation–MD transition stress-test (P1.5-B)

The R3.3.3 leading-order bound $|\Phi(\eta) - \Phi(\eta_\text{init})|/|\Phi_\text{init}| \le 5\%$ relies on $\Phi$ being approximately constant during MD. P1.5-B examines when this assumption breaks.

#### §B.1 Standard analytical $\Phi$ history

For an adiabatic mode in radiation-then-MD universe (Dodelson §6.5; Mukhanov 2005 §7):
- **Sub-horizon RD** ($k\eta \gg 1$, $\eta \ll \eta_{\text{eq}}$): $\Phi(\eta, k) \approx 3\Phi_\text{init}\cdot j_1(c_s k\eta)/(c_s k\eta)$ — oscillates with envelope $\propto \eta^{-2}$.
- **Super-horizon throughout** ($k\eta_0 \ll 1$): $\Phi(\eta) \approx (9/10)\Phi_\text{init}$ for $\eta > \eta_{\text{eq}}$ (the standard $9/10$ matter-radiation transfer factor).
- **MD sub-horizon** ($\eta_{\text{eq}} < \eta$, $k\eta \gg 1$ but post-equality): $\Phi$ approximately constant at its post-transition value.

The equality scale: $k_{\text{eq}} \approx 0.073\,\Omega_m h^2$ Mpc⁻¹ $\approx 0.010$ Mpc⁻¹ for standard $\Lambda$CDM ($\Omega_m h^2 \approx 0.143$; Dodelson §7.6 eq. 7.31). *(R9 audit-correction 2026-04-25: previous draft wrote $k_{\text{eq}} \approx 0.0104\,\Omega_m h^2$ Mpc⁻¹ $\approx 1.5\times 10^{-2}$ Mpc⁻¹ — both the coefficient and the resulting numerical value were wrong. The standard formula has coefficient 0.073 from $k_{\text{eq}} = a_{\text{eq}} H(a_{\text{eq}})$; for $\Omega_m h^2 = 0.143$ this gives $k_{\text{eq}} \approx 0.010$ Mpc⁻¹. The qualitative conclusion that $k = 10^{-2}$ is near $k_{\text{eq}}$ stands, but is now properly grounded.)*

#### §B.2 BASS pipeline placement: $\eta_\text{init}$ relative to $\eta_{\text{eq}}$

Standard $\Lambda$CDM: $\eta_{\text{eq}} \approx 110$ Mpc (corresponds to $z_{\text{eq}} \approx 3400$, $a_{\text{eq}} \approx 2.95\times 10^{-4}$). BASS Round-15 P0 uses $\eta_\text{init} = 261$ Mpc, **post-equality by a factor 2.4**. This placement is the structural reason the four-cell anchor works at low $k$:

- For $k = 10^{-3}$ (super-horizon at $\eta_\text{init}$, $k\eta_\text{init} \approx 0.26$): $\Phi$ has already settled to its post-equality $(9/10)\Phi_\text{init}^{\text{primordial}}$ value before BASS's IC is set. Subsequent evolution is approximately constant; $|\Phi(\eta_*) - \Phi(\eta_\text{init})|/|\Phi_\text{init}| \lesssim 1\%$.
- For $k = 10^{-2}$ (near $k_{\text{eq}}$): the mode entered the horizon near equality, so $\Phi$ underwent both the radiation-decay envelope and the matter-transition factor. By $\eta_\text{init} = 261$ Mpc (about 2.4 horizon-entry times after equality), the oscillations have damped out and $\Phi$ has settled to a near-constant sub-horizon value. $|\Phi(\eta_*) - \Phi(\eta_\text{init})|/|\Phi_\text{init}| \lesssim 5\%$ — at the edge of the 5% anchor tolerance, consistent with the empirical anchor's worst cell $(10^{-3}, 2)$ at $0.933$ ratio (i.e., 6.7% deviation).
- For $k = 10^{-1}$ (deep sub-horizon at equality): $\Phi$ entered sub-horizon long before $\eta_\text{init}$; oscillations damped well before $\eta_\text{init} = 261$ Mpc. $|\Phi(\eta_*) - \Phi(\eta_\text{init})|/|\Phi_\text{init}|$ should be small, but the absolute amplitude $|\Phi|$ is itself reduced by Silk-damping-type smoothing — the bound applies but the regime is near the resolution limit of the BASS source extraction.

#### §B.3 Numerical stress-test specification

To validate the R3.3.3 bound at the radiation-MD transition empirically, run the following test against CAMB's stored $\Phi$-history:

```
For k in [1e-3, 3e-3, 1e-2, 3e-2, 1e-1] Mpc^-1:
    Phi_init = CAMB.Phi(eta=261, k=k)
    Phi_star = CAMB.Phi(eta=282, k=k)
    ratio[k] = |Phi_star - Phi_init| / |Phi_init|
Expected: ratio[k] ≤ 0.05 for k ≤ 1e-2
          ratio[k] increases for k > 1e-2 but stays ≤ 0.10 in standard ΛCDM
```

If a future P2 track moves $\eta_\text{init}$ to before equality (i.e., into RD), this analysis breaks down and the residual hierarchy of P1.5-A would need the radiation-era $\Phi$ oscillation explicitly retained.

#### §B.4 Self-flagged unchecked items in §B

(i) The "5% at $k = 10^{-2}$" bound is order-of-magnitude estimate; the empirical four-cell anchor is the actual confirmation. (ii) For $k > 10^{-2}$ the anchor is unavailable (CAMB introspection limit, briefing §3.3); the analytical estimate predicts the bound stays below 10% but is not directly verified. (iii) The $9/10$ matter-radiation transfer factor is the canonical adiabatic result; non-adiabatic or isocurvature initial conditions would change this and are not in BASS's scope.

### §C. Reionization / late-ISW separate validation track (P1.5-C)

The recombination 5% verdict does not extend automatically to reionization. P1.5-C scopes the late-time validation track and provides the test fixtures.

#### §C.1 Late-time visibility and $\Phi$ evolution

After reionization (assume $z_{\text{re}} = 7.7$ for $\Lambda$CDM, $\eta_{\text{re}} \approx 9300$ Mpc), $\dot\kappa$ rises again to a smaller second peak. Standard Planck-2018 $\tau_{\text{re}} \approx 0.054$ corresponds to $g_{\text{re}}^{\text{peak}}/g_{\text{rec}}^{\text{peak}} \sim 0.05$ — the reionization visibility is $\sim 5\%$ of the recombination visibility.

By $\eta_{\text{re}} = 9300$ Mpc, the universe is in the matter-$\Lambda$ transition: $\Omega_\Lambda(z=7.7) \approx 4\%$ of $\Omega_m$. The Newtonian potential $\Phi$ has begun decaying:

$$
\Phi(z_{\text{re}})/\Phi(\eta_*) \;\approx\; D(z_{\text{re}})/D(z_*), \quad D(z) \;\equiv\; \text{linear growth factor},
$$

which gives $\Phi(\eta_{\text{re}})/\Phi(\eta_*) \approx 0.97$ for standard $\Lambda$CDM (suppressed by $\sim 3\%$). The $\Phi$ change between $\eta_\text{init}$ and $\eta_{\text{re}}$ is therefore $\sim 5-8\%$ (combining the $\sim 5\%$ already accumulated by $\eta_*$ in MD plus another $\sim 3\%$ from MD-to-$\Lambda$ transition).

#### §C.2 Implication for R3.3.3 at reionization

The kinematic-frame residual at $\eta_{\text{re}}$:

$$
\delta\Theta_0(\eta_{\text{re}}) \;\approx\; \Phi(\eta_{\text{re}}) - \Phi(\eta_\text{init}) \;\sim\; 5-8\% \cdot |\Phi_\text{init}|.
\tag{P1.5-C.2.1}
$$

Visibility-weighted contribution to $\Delta_\ell^T$:

$$
\Delta_\ell^{T,\text{re-residual}} \;\sim\; g_{\text{re}}^{\text{peak}}\cdot 0.07\cdot |\Phi_\text{init}|\cdot \int j_\ell\, d\eta
\;\sim\; 5\% \cdot 7\% \cdot |\Phi_\text{init}|
\;\sim\; 4\times 10^{-3}\cdot |\Phi_\text{init}|.
\tag{P1.5-C.2.2}
$$

This is $\sim 0.4\%$ of the recombination contribution — small but not negligible at sub-percent precision.

#### §C.3 ISW driver compensates — partial cancellation

The architecturally separate ISW driver $e^{-\kappa}(\dot\Phi + \dot\Psi)$ in the LoS source captures the late-time $\Phi$-decay independently. Per the IBP identity R3.3.4, the ISW contribution from $\eta \in [\eta_*, \eta_{\text{re}}]$ partially compensates the kinematic-frame residual at the reionization visibility peak:

$$
\Delta_\ell^{T,\text{re-residual,total}} \;=\; \Delta_\ell^{T,\text{re-residual,kin}} \;+\; \Delta_\ell^{T,\text{ISW between rec and re}}.
\tag{P1.5-C.3.1}
$$

A precise estimate of the residual cancellation requires a numerical comparison against CAMB's full ISW history; the qualitative argument is that the cancellation is partial (not exact, like R3.3.4 with the audit-corrected language), and the residual is bounded above by the larger of the two pieces — i.e., $\sim$ few percent of $g_{\text{re}}^{\text{peak}}\cdot |\Phi_\text{init}|$.

#### §C.4 Validation fixture

P1.5-C calls for the following validation track, separate from the recombination anchor:

```
Setup: BASS LoS run with reionization enabled (g_re peak active), late-time
       Phi-history populated (Lambda-CDM standard).
Test 1: Compute Delta_ell^T(k) for ell in [2, 30] (low-ell, late-ISW dominant).
Test 2: Compute Delta_ell^T(k) with ISW source disabled (only g[Theta_0+Psi+Pi/4] + Doppler).
Test 3: Compare CAMB direct Delta_ell^T(k) to BASS LoS for both Test 1 and Test 2.
Acceptance: |BASS - CAMB|/|CAMB| <= 5% for Test 1 (full source)
            Test 2 should NOT match CAMB at low ell — quantifies the ISW contribution.
```

The R5 Oracle 4 ISW-Limber and ISW-full integrals provide the analytic cross-check at $\ell \ge 30$.

#### §C.5 Self-flagged unchecked items in §C

(i) The $g_{\text{re}}^{\text{peak}}/g_{\text{rec}}^{\text{peak}} \sim 0.05$ ratio is for $\tau_{\text{re}} = 0.054$; for higher-$\tau$ reionization scenarios (e.g., $\tau_{\text{re}} = 0.08$ from earlier reionization-phase models) the ratio is larger, and the residual estimate scales accordingly. (ii) The "partial cancellation" language is qualitative; a quantitative bound requires numerical comparison with CAMB's late-ISW history. (iii) Extended-reionization or non-standard reionization histories are out of scope.

### §D. Tilt and m=±2 normalization in BASS's PSTF convention (P1.5-D)

R4 §3 stated tilt-boost coefficients $\ell/(2\ell-1), (\ell+1)/(2\ell+3)$ for the $n^a$-frame to $u_e^a$-frame transformation in PSTF basis. The R7 auditor flagged that BASS's actual harmonic-mode convention may differ by $(2\ell+1)/4$-type rescaling, which would change these coefficients. P1.5-D derives the conversion explicitly.

#### §D.1 PSTF normalization in CL2000-I

CL2000-I §3.2 defines PSTF moments $\Pi_{A_\ell}$ of the photon brightness via

$$
I(\eta, x, k̂) \;=\; \sum_\ell \Pi_{A_\ell}(\eta, x)\, e^{\langle A_\ell\rangle}_{k̂},
\tag{P1.5-D.1.1}
$$

where $e^{\langle A_\ell\rangle}_{k̂}$ are STF basis tensors built from $\hat k$. The harmonic moments in scalar mode ($m = 0$) relate to Legendre coefficients via

$$
I(\eta, x, k̂) \;=\; \sum_\ell (2\ell+1)(-i)^\ell\, I_\ell^{(\text{Legendre})}(\eta, k)\, P_\ell(\hat k\cdot \hat n),
\tag{P1.5-D.1.2}
$$

so the conversion is

$$
\Pi_\ell^{(\text{PSTF, m=0})} \;=\; \frac{(2\ell+1)\cdot \ell!}{(2\ell-1)!!}\, I_\ell^{(\text{Legendre})}.
\tag{P1.5-D.1.3}
$$

(CL2000-I eq. 41–42 with the explicit factorial factors absorbed; the $\ell!/(2\ell-1)!!$ factor comes from the STF tensor normalization.) For energy-weighted multipoles $\Theta_\ell = I_\ell^{(\text{Legendre})}/4$ in CAMB convention vs $\hat\Theta_\ell^{(\text{PSTF})} = \Pi_\ell^{(\text{PSTF})}/4$ in CL2000:

$$
\hat\Theta_\ell^{(\text{PSTF})} \;=\; \frac{(2\ell+1)\cdot \ell!}{(2\ell-1)!!}\, \Theta_\ell^{(\text{CAMB})}.
\tag{P1.5-D.1.4}
$$

At $\ell = 0$: factor 1. At $\ell = 1$: factor 3. At $\ell = 2$: factor $5\cdot 2/3 = 10/3$. At $\ell = 3$: factor $7\cdot 6/15 = 42/15 = 14/5$. **BASS uses CL2000 PSTF convention internally**; conversion to CAMB output requires this rescaling.

#### §D.2 Tilt-boost coefficients in PSTF vs CAMB

Under axisymmetric tilt boost by $\bar v_{(s)} \hat z$, the photon multipole transforms (TCM 2008 §5 eq. 5.12, in their PSTF convention):

$$
\hat\Theta_\ell^{(u_e)} \;=\; \hat\Theta_\ell^{(n)} \;+\; \bar v_{(s)}\,\Bigl[A_\ell^{(\text{PSTF})}\,\hat\Theta_{\ell-1}^{(n)} - B_\ell^{(\text{PSTF})}\,\hat\Theta_{\ell+1}^{(n)}\Bigr] \;+\; \mathcal O(\bar v^2).
\tag{P1.5-D.2.1}
$$

The PSTF coefficients (TCM 2008 §5, derived from spin-1 boost of STF tensors):

$$
A_\ell^{(\text{PSTF})} \;=\; \frac{\ell}{2\ell-1}, \qquad B_\ell^{(\text{PSTF})} \;=\; \frac{\ell+1}{2\ell+3}.
\tag{P1.5-D.2.2}
$$

These are the coefficients I used in R4.3.2. ✓ They are correct in BASS's PSTF convention and do **not** require additional $(2\ell+1)/4$ rescaling because TCM 2008 derives them in the same PSTF normalization that BASS uses.

The conversion to **CAMB convention** is

$$
A_\ell^{(\text{CAMB})} \;=\; A_\ell^{(\text{PSTF})}\cdot \frac{c_{\ell-1}}{c_\ell} \;=\; \frac{\ell}{2\ell-1}\cdot \frac{c_{\ell-1}}{c_\ell},
\tag{P1.5-D.2.3}
$$

where $c_\ell = (2\ell+1)\ell!/(2\ell-1)!!$. At $\ell = 2$: $c_1/c_2 = 3/(10/3) = 9/10$, so $A_2^{(\text{CAMB})} = 2/3 \cdot 9/10 = 3/5$. The CAMB-convention tilt formula at $\ell = 2$ would have coefficient $3/5$, not $2/3$. **Practical implication**: any code that interfaces BASS's PSTF tilt output with CAMB's Legendre-mode tilt input must apply this conversion.

#### §D.3 m=±2 channel coefficients

In axisymmetric tilt ($\bar v_{(s)}^x = \bar v_{(s)}^y = 0$, only $\bar v_{(s)}^z$), the m=±2 channels do not mix with m=0 at first order in $\bar v$ (TCM 2008 §5; the spin-2 mixing requires non-axisymmetric boost components). For non-axisymmetric tilt, the mixing coefficients are

$$
\delta\hat\Theta_\ell^{(m=\pm 2)} \;=\; (\bar v_{(s)}^x \mp i\bar v_{(s)}^y)\cdot\bigl[C_\ell^{(\pm 2)} \hat\Theta_{\ell-1}^{(0)} - D_\ell^{(\pm 2)} \hat\Theta_{\ell+1}^{(0)}\bigr] + \mathcal O(\bar v^2),
\tag{P1.5-D.3.1}
$$

with $C_\ell^{(\pm 2)}, D_\ell^{(\pm 2)}$ involving the Wigner $3j$ symbols $\langle \ell\, m=\pm 2 | \ell-1\, m'\rangle$. **First-principles derivation of $C_\ell^{(\pm 2)}, D_\ell^{(\pm 2)}$ is deferred to the per-type harmonic backend implementation** (R4 §5 ✗ infrastructure); the value of P1.5-D is to flag that the convention must match TCM 2008's PSTF normalization to use the published coefficients directly.

#### §D.4 Self-flagged unchecked items in §D

(i) The factorial factor $(2\ell+1)\ell!/(2\ell-1)!!$ in P1.5-D.1.3 is the standard CL2000-I conversion, but BASS's actual internal normalization should be cross-checked against the `pstf_pack`/`pstf_to_tensor` implementations in `bass.hierarchy.pstf_tensor` (file not in bundle). (ii) The $C_\ell^{(\pm 2)}, D_\ell^{(\pm 2)}$ coefficients for non-axisymmetric tilt are not derived here. (iii) Beyond linear order in $\bar v$, second-order corrections enter at $\mathcal O(\bar v^2)$ and would require the full boost-tensor algebra of TCM 2008 §5.

### §E. Polarization (T,E) eigenvalue derivation; cross-convention E-mode dictionary (P1.5-E)

R2 §3 stated the (T,E) eigenvalues as $\{9/10, 0\}$ — the R7 auditor flagged this as conflating decoupled rates with coupled-system eigenvalues. P1.5-E provides the correct derivation and the inter-convention dictionary the R7 auditor requested.

#### §E.1 The (T,E) collision matrix at ℓ=2

Starting from lowell §9.2 / CL2000-II eq. 12 (BASS implementation reference):

$$
\frac{D\Theta_2}{d\tau}\Big|_{\text{coll}} \;=\; \Gamma_T\Bigl[-\Theta_2 + \tfrac{1}{10}(\Theta_2 - \sqrt 6\, E_2)\Bigr],
\qquad
\frac{DE_2}{d\tau}\Big|_{\text{coll}} \;=\; \Gamma_T\Bigl[-E_2 + \tfrac{3}{5}(E_2 - \tfrac{1}{\sqrt 6}\Theta_2)\Bigr].
\tag{P1.5-E.1.1}
$$

Expanding:

$$
\frac{D\Theta_2}{d\tau}\Big|_{\text{coll}} \;=\; -\Gamma_T\Bigl[\tfrac{9}{10}\Theta_2 + \tfrac{\sqrt 6}{10}E_2\Bigr],
\qquad
\frac{DE_2}{d\tau}\Big|_{\text{coll}} \;=\; -\Gamma_T\Bigl[\tfrac{\sqrt 6}{10}\Theta_2 + \tfrac{2}{5}E_2\Bigr],
\tag{P1.5-E.1.2}
$$

(using $3/(5\sqrt 6) = \sqrt 6/10$). Writing $d/d\tau (\Theta_2, E_2)^T = -\Gamma_T M (\Theta_2, E_2)^T$:

$$
M \;=\; \begin{pmatrix} 9/10 & \sqrt 6/10 \\ \sqrt 6/10 & 2/5 \end{pmatrix}.
\tag{P1.5-E.1.3}
$$

#### §E.2 Eigenvalue derivation

$\det M = (9/10)(2/5) - (\sqrt 6/10)^2 = 18/50 - 6/100 = 36/100 - 6/100 = 30/100 = 3/10$.
$\text{tr}\, M = 9/10 + 2/5 = 9/10 + 4/10 = 13/10$.

Characteristic equation: $\lambda^2 - (13/10)\lambda + 3/10 = 0$.

$$
\lambda \;=\; \frac{13/10 \pm \sqrt{169/100 - 12/10}}{2} \;=\; \frac{13/10 \pm \sqrt{49/100}}{2} \;=\; \frac{13/10 \pm 7/10}{2}.
\tag{P1.5-E.2.1}
$$

Eigenvalues: $\lambda_+ = (13+7)/20 = 1$ and $\lambda_- = (13-7)/20 = 3/10$.

**Eigenvector for $\lambda = 1$**: solve $(M - I)\mathbf v = 0$:
$(9/10 - 1)v_1 + (\sqrt 6/10)v_2 = 0 \Rightarrow v_1 = \sqrt 6\, v_2$. Eigenvector $\propto (\sqrt 6, 1)$, i.e., **$\sqrt 6\,\Theta_2 + E_2$ relaxes at the full Thomson rate $\Gamma_T$** (fast eigenmode).

**Eigenvector for $\lambda = 3/10$**: orthogonal to $(\sqrt 6, 1)$, so $\propto (1, -\sqrt 6)$, i.e., **$\Theta_2 - \sqrt 6\, E_2 = \Pi^{\text{PSTF}}$ relaxes at $(3/10)\Gamma_T$** (slow eigenmode).

Numerical verification: see P1.5-E.2.2 below (executed during this round).

```
M = [[0.9, √6/10], [√6/10, 0.4]]
trace = 1.3 = 13/10 ✓
det = 0.3 = 3/10 ✓
eigenvalues: [0.3, 1.0]   (= {3/10, 1})
eigenvector for λ=0.3: ∝ (1, -√6)  =  Π^PSTF ✓
eigenvector for λ=1.0: ∝ (√6, 1)  =  Π^fast ✓
```

This is the correct eigenstructure. The R2 §3 inline correction now reflects this.

#### §E.3 Why the slow rate $(3/10)\Gamma_T$ (not $9/10$) matters physically

The polter $\Pi^{\text{PSTF}}$ is the source of E-mode polarization at recombination. Its slow relaxation rate $(3/10)\Gamma_T$ — slower than the full Thomson rate by a factor of $\sim 3$ — allows the polarization quadrupole to persist long enough during the recombination tight-to-loose-coupling transition for observable E-mode generation. If $\Pi$ relaxed at the full Thomson rate, polarization would be erased before decoupling and the universe would have no observable E-mode.

The "9/10" figure that appeared (incorrectly) in R2 §3 is the *decoupled* Θ₂-only relaxation rate: setting $E_2 \equiv 0$ artificially in P1.5-E.1.2 gives $D\Theta_2/d\tau = -(9/10)\Gamma_T \Theta_2$, the diagonal entry of $M$. This is the relaxation Θ₂ would experience if E-mode polarization didn't exist — but in the real system, E-mode coupling reduces this to the slower coupled rate $(3/10)\Gamma_T$ for the polter combination.

#### §E.4 Cross-convention dictionary at ℓ=2 (E-mode amplitudes)

| Convention | E-mode at ℓ=2 | Sign / phase | Conversion to PSTF |
|---|---|---|---|
| CL2000-II (PSTF, BASS internal) | $E_2^{\text{PSTF}}$ via PSTF tensor $E_{\langle ab\rangle}$ | per CL2000-II | identity (BASS native) |
| KKS97 (spin-weighted Y) | $a^E_{2,m=0} = -\tfrac{1}{2}(a_{+2,2,0} + a_{-2,2,0})$ | parity-eigenstate | $a^E_{2,0} = -\sqrt{(2\ell+1)/(4\pi)}\cdot E_2^{\text{PSTF}}\cdot N_\ell^{(\text{KKS})}$ where $N_2^{(\text{KKS})} = \sqrt{(\ell-1)(\ell+2)/[(\ell+1)\ell]} = \sqrt{4/6} = \sqrt{2/3}$ |
| HW97 TAM (G_2, C_2) | $G_2$ (electric), $C_2$ (magnetic) | TAM basis | $G_2 = E_2^{\text{PSTF}}\cdot (2\ell+1)\cdot$ Wigner-d normalization, $\sim 5\cdot E_2^{\text{PSTF}}\cdot \sqrt{2/3}/3$ at ℓ=2 |
| CAMB (LC06 internal) | $E_2^{\text{CAMB}}$ via `polter` line in `lensing.f90` | LC06 §A documents historical sign | $E_2^{\text{CAMB}} = -(1/\sqrt 6)\cdot E_2^{\text{PSTF}}\cdot \text{(rescaling)}$ — sign opposite per LC06 §A |

The exact numerical conversions involve: (i) the spin-2 spherical-harmonic normalization $N_\ell^{(\text{KKS})}$, (ii) the Wigner small-d factor $d^\ell_{2,m}(\pi/2)$ at the basis-rotation, and (iii) the CL2000-I PSTF rescaling P1.5-D.1.4. **Full numerical conversion at $\ell = 2$**: combining (i)+(iii) gives

$$
a^E_{2,0}(\text{KKS97}) \;=\; -\sqrt{\frac{5}{4\pi}}\cdot \sqrt{\frac{2}{3}}\cdot \frac{10}{3}\cdot E_2^{\text{CAMB}}\cdot (-1)
\;=\; \sqrt{\frac{5}{4\pi}}\cdot \sqrt{\frac{2}{3}}\cdot \frac{10}{3}\cdot E_2^{\text{CAMB}}.
\tag{P1.5-E.4.1}
$$

(using P1.5-D.1.4 PSTF→CAMB factor $10/3$ at $\ell=2$, KKS97 normalization $\sqrt{2/3}$, and the CAMB sign-flip relative to PSTF).

#### §E.5 Self-flagged unchecked items in §E

(i) The polter eigenvalue derivation P1.5-E.1–E.2 is bundle-confirmed: lowell §9.2 supplies the collision form, and the algebra is closed. **Status**: ✓ derived. (ii) The §E.4 cross-convention table combines CL2000-I, KKS97, HW97, and LC06 conversions with each piece individually documented but the *combined* conversion P1.5-E.4.1 not directly verifiable from the bundle alone (the explicit $-\sqrt{5/4\pi}\sqrt{2/3}\cdot 10/3$ assembly is a derivation, not a citation; component factors are individually citable from KKS97 / CL2000-I / LC06). **Status**: literature-cited per component, derived for the assembly. (iii) The ℓ ≥ 3 generalizations of P1.5-E.4.1 require the Wigner-d calculations at higher ℓ and are not derived here.

### §F. `packed_operators.py` audit specification (P1.5-F)

The R1 reading bundle does not include `bass/hierarchy/packed_operators.py`. P1.5-F provides specifications that an in-repo regression test (or follow-up bundle audit) must verify.

#### §F.1 `apply_T1_expansion_packed` specification

**Signature**:
```python
apply_T1_expansion_packed(
    ell: int,
    Pi_components: np.ndarray,        # shape (2ℓ+1,), packed PSTF
    theta: float,                      # background expansion Θ = 3H
    aniso_ricci_tensor: np.ndarray | None,  # shape (3, 3) or None
) -> np.ndarray                        # shape (2ℓ+1,)
```

**Expected formula** (per R4.1.2, audit-corrected):
$$
[\text{T1 output}]_{A_\ell} \;=\; \frac{4}{3}\theta\,\Pi_{A_\ell} \;+\; \frac{\ell}{2\ell+3}\,{}^{(3)}R^{(\text{aniso}),b}{}_{\langle a_\ell}\,\Pi_{A_{\ell-1}\rangle b} \quad (\text{if aniso\_ricci\_tensor not None}).
$$

**Test case 1** (FLRW, no curvature): $\theta = 3H$, `aniso_ricci_tensor=None`, $\Pi$ arbitrary. Expected output: `(4/3) * theta * Pi_components`. Tolerance: machine precision.

**Test case 2** (Bianchi-I shear-only): $\theta = 3H$, `aniso_ricci_tensor=None` (Bianchi I has zero spatial 3-Ricci aniso part), $\Pi$ arbitrary. Same as Test 1 (T1 doesn't see shear; that's T7/T8/T9).

**Test case 3** (Bianchi II curvature): $\theta = 3H$, `aniso_ricci_tensor` set to the standard Bianchi II 3-Ricci form (anisotropic, non-zero), $\Pi$ arbitrary at $\ell = 2$. Expected output should differ from Test 2 by the curvature-correction term. Specific numerical check requires the canonical Bianchi II 3-Ricci values from FB-2.4 reference material.

#### §F.2 `apply_T7_shear_up_packed`, `apply_T8_shear_same_packed`, `apply_T9_shear_down_packed`

**Expected formulas** (per R4.1.4, audit-corrected per lowell §6 line 374–376):

$$
[T_7]_{A_\ell} \;=\; -\frac{(\ell-1)(\ell+1)(\ell+2)}{(2\ell+3)(2\ell+5)}\,\sigma^{bc}\,\Pi_{A_\ell bc},
$$
$$
[T_8]_{A_\ell} \;=\; +\frac{5\ell}{2\ell+3}\,\sigma^{b}{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b},
$$
$$
[T_9]_{A_\ell} \;=\; -(\ell+2)\,\sigma_{\langle a_\ell a_{\ell-1}}\Pi_{A_{\ell-2}\rangle}.
$$

**Test case ℓ=2** (lowell §6 line 402–404 explicit specialization):

At $\ell = 2$, lowell §6 displays:
$$
T_7|_{\ell=2} = -\tfrac{4}{21}\sigma^{cd}\Pi_{abcd}, \quad T_8|_{\ell=2} = +\tfrac{10}{7}\sigma^c{}_{\langle a}\Pi_{b\rangle c}, \quad T_9|_{\ell=2} = -4\sigma_{ab}\Pi.
$$

Verification of formulas against $\ell = 2$:
- $T_7$ coefficient: $-(1)(3)(4)/[(7)(9)] = -12/63 = -4/21$ ✓
- $T_8$ coefficient: $+5\cdot 2/7 = 10/7$ ✓
- $T_9$ coefficient: $-(2+2) = -4$ ✓

**Regression test** (any in-repo verification):

```python
# Test inputs (Bianchi-I diagonal axisymmetric shear)
sigma_ab = np.diag([sigma_plus, sigma_plus, -2*sigma_plus])  # 3×3, traceless
Pi_2 = arbitrary_PSTF_quadrupole          # 5 components packed
Pi_4 = arbitrary_PSTF_hexadecapole        # 9 components packed
Pi_0 = arbitrary_scalar_monopole          # 1 component

# Compute each term at ℓ=2
T7_out = apply_T7_shear_up_packed(2, Pi_4, sigma_coeffs)
T8_out = apply_T8_shear_same_packed(2, Pi_2, sigma_coeffs)
T9_out = apply_T9_shear_down_packed(2, Pi_0, sigma_coeffs)

# Independent reference computation using ℓ=2 explicit forms
T7_ref = -(4/21) * np.einsum('cd,abcd->ab', sigma_ab, Pi_4_unpacked)
T8_ref = +(10/7) * np.einsum('cb,bc->ab', sigma_ab, Pi_2_unpacked, ...)
T9_ref = -4 * sigma_ab * Pi_0

# Assert agreement
assert np.allclose(T7_out, pstf_pack(T7_ref), atol=1e-12)
# (similarly for T8, T9)
```

#### §F.3 Test case: FLRW reduction (σ_ab = 0)

With $\sigma_{ab} = 0$, all of $T_7, T_8, T_9$ should return the zero array. This is the FLRW-fast-path consistency check; BASS's `hierarchy_rhs.py:411` `has_sigma` flag selects the no-shear path, and the operators should not be called. If they ARE called (e.g., due to a configuration bug), they must still return zeros.

#### §F.4 Status post-P1.5-F

Until either (a) `packed_operators.py` is added to a follow-up reading bundle, or (b) the in-repo regression tests above are run against the current implementation, the operators T1-curvature, T7, T8, T9, T4, T5, T6, K_T retain the **✓⁻** status from R8 §2 (dispatch confirmed via `hierarchy_rhs.py` call-sites; operator algebra not directly audit-verifiable from the R1 bundle).

#### §F.5 Self-flagged unchecked items in §F

(i) The P1.5-F.1–F.2 specifications use the audit-corrected R4.1.4 coefficients — if the in-repo `packed_operators.py` was implemented against the *previous* (incorrect) coefficients, those tests will fail and the implementation needs to be updated, not the spec. (ii) The P1.5-F regression tests assume PSTF-tensor pack/unpack utilities (`pstf_pack`, `pstf_to_tensor`) work correctly; those utilities are themselves bundle-absent and would need their own regression. (iii) The Bianchi-II 3-Ricci numerical reference for Test 3 requires the FB-2.4 reference material not in the bundle.

### §G. Synthesis and second-audit hand-off

P1.5 closes the six items deferred in R8. Specifically:

| ID | Item | Closure |
|---|---|---|
| P1.5-A | Coupled residual hierarchy | **Bounded (R9-corrected)**: dipole back-reaction onto $\delta\Theta_0$ is $\sim 1\%$ (typical) to $\sim 8\%$ (worst case) of the leading $[\Phi-\Phi_\text{init}]$ residual at recombination, using realistic $\dot\kappa(\eta) \in [0.06, 0.93]$ Mpc⁻¹ across the integration window. R3.3.3 confirmed at leading order; precise sub-percent bound requires BASS `visibility_history` integration. |
| P1.5-B | Radiation–MD transition | **Scoped**: BASS's $\eta_\text{init} = 261$ Mpc (post-equality) makes the rad-MD issue moot for current pipeline. Numerical stress-test specified for $k > 10^{-2}$ where anchor unavailable. |
| P1.5-C | Reionization / late-ISW | **Scoped + test fixture provided**: separate validation track at $\ell \in [2, 30]$ with R5 Oracle 4 cross-check. ISW driver provides partial late-time compensation. |
| P1.5-D | Tilt + m=±2 normalization | **PSTF-literature convention confirmed; BASS internal normalization pending**: TCM 2008 PSTF tilt coefficients $\ell/(2\ell-1), (\ell+1)/(2\ell+3)$ are the correct CL2000-convention values, but BASS's actual `pstf_pack`/`pstf_to_tensor` normalization (file absent from R1 bundle) needs to be cross-checked before these coefficients can be used directly in the BASS solver. CAMB-conversion factors derived in P1.5-D.2.3. m=±2 non-axisymmetric mixing coefficients deferred to per-type backend implementation. |
| P1.5-E | (T,E) eigenvalue + cross-convention | **Derived + corrected**: eigenvalues are $\{1, 3/10\}$ (not $\{9/10, 0\}$); $\Pi^{\text{PSTF}}$ relaxes at $(3/10)\Gamma_T$ (slow mode). R2 §3 inline-corrected. KKS97/HW97/CAMB combined conversion P1.5-E.4.1 derived. |
| P1.5-F | `packed_operators.py` audit | **Spec'd**: explicit formulas + regression tests for T1/T7/T8/T9. Operators retain ✓⁻ status until in-repo regression runs. |

The P1.5 work surfaces three new items the second audit may want to review:

1. The R2 §3 inline correction of the (T,E) eigenvalue claim is a real physics correction that survived the original draft and the first audit cycle. The auditor's "Partial" disposition in R8 §1 was correct in identifying the conflation, but my disposition glossed over it; P1.5-E now provides the explicit derivation. This is the most significant correction in P1.5.

2. The numerical bound P1.5-A.4.2 ($\sim 10^{-11}$ for dipole back-reaction) uses order-of-magnitude estimates for $|\Psi|$, $\dot\kappa_*$, and $\Delta\eta_{\text{rec}}$; tightening this with bundle-extracted values for the four anchor cells is straightforward and would strengthen the P1.5-A claim.

3. P1.5-D.1.3's PSTF↔CAMB conversion factor $(2\ell+1)\ell!/(2\ell-1)!!$ produces $\{1, 3, 10/3, 14/5, ...\}$ at $\ell = \{0, 1, 2, 3, ...\}$. This is the standard CL2000-I conversion but is *not* directly verified in the bundle (no `pstf_tensor.py` source). If BASS's internal normalization deviates from CL2000-I, the boost coefficients in P1.5-D.2.2 would inherit the deviation.

The cumulative document is now R1→R8 + P1.5 + executive summary + five recommendations + R7 audit prompt. The next external audit cycle should focus on:

- P1.5-A's dipole/quadrupole back-reaction estimates (numerical input verification)
- P1.5-E's combined cross-convention assembly P1.5-E.4.1 (component-by-component verification)
- P1.5-F's regression spec correctness (against current `packed_operators.py` implementation)
- Any reframing of P1.5-B/C scope language that is too narrow or too broad

---

## R9. Second-cycle audit response (post-second-audit, 2026-04-25)

A second external audit was run on the R8+P1.5-augmented document. The auditor's verdict: "substantially repaired, but not yet SSoT-safe", with three minimum fixes plus several additional FLAGGED and MISSED items. R9 records the response cycle.

### §1. Three minimum fixes — disposition

| Auditor's required fix | Status | Location of fix |
|---|---|---|
| (1) R6 §2 master table coefficients/status are stale | **Applied**: T2/T3 corrected to position-space form per lowell §6; T7/T8/T9 corrected to $-\frac{(\ell-1)(\ell+1)(\ell+2)}{(2\ell+3)(2\ell+5)}$, $+\frac{5\ell}{2\ell+3}$, $-(\ell+2)$ respectively; T4/T5/T6 expanded with proper coefficients per lowell §6 lines 369–371; status downgraded to ✓⁻ for all operators whose source files are absent from R1 reading bundle. | R6 §2 (table replaced wholesale) |
| (2) Executive summary self-contradicts on AF-1 fix | **Applied**: rephrased verdict to "No additional monopole-frame correction is required at the four-cell 5% level, after applying the AF-1 Doppler $/k$ fix." Separates the monopole-frame question (no fix) from the Doppler convention question (one-line fix). | Executive summary opening paragraph |
| (3) P1.5-A's $\dot\kappa_* \approx 100$ Mpc⁻¹ unit/magnitude error | **Applied**: full numerical recompute. Standard recombination has $\dot\kappa \in [0.06, 0.93]$ Mpc⁻¹ across the integration window $[\eta_\text{init}, \eta_*] = [261, 282]$ Mpc, NOT $\sim 100$ Mpc⁻¹. Recomputed back-reaction bound: $\sim 1\%$ (typical) to $\sim 8\%$ (worst case) of leading, NOT "four orders below." Qualitative subdominance survives; precision claim weakened. | P1.5-A §A.3 and §A.4 (replaced wholesale) |

### §2. Other FLAGGED items — disposition

| Finding | Status | Location |
|---|---|---|
| R4 §1 "R4 confirms the algebra" overstatement | **Applied**: rephrased to "R4 provides the *intended algebra* (per lowell §6 displayed equation, audit-corrected) and clarifies the LoS-side consequences. Implementation algebra inside `apply_T1/T7/T8/T9_packed` is not directly verifiable from the R1 bundle." | R4 §1 "Reproduction status" paragraph |
| P1.5-B $k_{\text{eq}}$ formula wrong | **Applied**: coefficient $0.0104 \to 0.073$, value $1.5\times 10^{-2} \to 0.010$ Mpc⁻¹ per Dodelson eq. 7.31. | P1.5-B §B.1 |
| R5.2 still conflates visibility-width with Silk damping | **Applied**: explicit statement that visibility-width envelope and collisional Silk diffusion are **distinct physical mechanisms** with characteristic scales $\sigma_*^{-1} \approx 0.09$ Mpc⁻¹ and $k_D \approx 0.14$ Mpc⁻¹ respectively (accidentally similar but different in origin). | R5 §6 closing paragraph |
| P1.5-D tilt "Confirmed" overstatement | **Applied**: downgraded to "PSTF-literature convention confirmed; BASS internal normalization pending" — TCM 2008 coefficients are the correct CL2000 convention values, but BASS's internal `pstf_pack`/`pstf_to_tensor` normalization (file absent from R1 bundle) needs to be cross-checked before the coefficients are used directly. | P1.5-G synthesis table P1.5-D row |
| Header still says R1→R7 | **Applied**: updated to "R1 → R9 + P1.5" with explicit acknowledgment of two audit cycles. | Document title block |
| R8/P1.5 status records conflict (append-only history) | **Applied**: §3 below provides the **canonical post-R9 SSoT status table** that supersedes both R8 §1's deferred table and P1.5-G's synthesis table; those earlier tables are now historical-record-only. | R9 §3 below |

### §3. Canonical post-R9 SSoT status table (supersedes R8 §1 and P1.5-G)

This is the single authoritative status table for any coding-agent or downstream consumer of this document. The earlier tables in R8 §1 and P1.5-G remain in the document for historical-cycle traceability but should not be used as SSoT.

| Item | Status | Action required | Test fixture |
|---|---|---|---|
| **AF-1**: Doppler $/k$ | **Code fix specified** | Append `/ k` at `flrw_bessel_projector.py:453`; thread $k$ through `build_temperature_source` signature | R5 Oracle 5 (R5.5.1) isolated Doppler regression |
| **VR-1**: $\Theta_0^{(\text{kin})}$ sub-percent verification | Deferred (diagnostic) | Compute $\Theta_0^{(\text{kin})} - [\Phi(\eta)-\Phi(\eta_\text{init})]$ from BASS, compare to CAMB's `clxg/4` (sync→Newt) | New `tests/integration/test_theta0_gauge_identification.py` |
| **VR-2**: High-$k$ source-assembly correctness | Deferred (regression suite) | Run R5 Oracles 1–5 against BASS LoS at $k \in [10^{-2}, 10^{-1}]$, $\ell \in [2, 100]$ | New `tests/los/test_analytic_oracles.py` |
| **VR-3**: Bianchi-I shear-forcing FLRW reduction | Existing FLRW regression | Verify R4 algebra reduces to R2 in $\sigma_{ab}\to 0$ | LB-6 / FB-2.3 bit-identical regression |
| **VR-4**: Tilt residual 2nd-order vanishing | Deferred (post-tilt-infra) | Verify $\delta S_T^{\text{tilt}}$ vanishes at second order in $\bar v_{(s)}$ for orthogonal Bianchi | New unit test once tilt infrastructure lands |
| **P1.5-A**: Coupled residual hierarchy | **Bounded at order ~1%-8%** (R9-corrected, was wrongly claimed as 4 orders below) | Tighten with BASS `visibility_history` integration | Numerical test against actual $\dot\kappa(\eta)$ |
| **P1.5-B**: Rad-MD transition stress-test | Scoped, untested numerically | Run CAMB $\Phi$-history comparison at $k \in \{10^{-3}, 3\times 10^{-3}, 10^{-2}, 3\times 10^{-2}, 10^{-1}\}$ | New stress-test against CAMB $\Phi$-history |
| **P1.5-C**: Reionization / late-ISW | Test fixture provided, untested | Run BASS LoS with reionization and ISW-disabled comparisons | R5 Oracle 4 ISW-Limber + ISW-full |
| **P1.5-D**: Tilt + m=±2 normalization | **PSTF-literature confirmed; BASS internal pending** | Cross-check BASS `pstf_pack`/`pstf_to_tensor` normalization against CL2000-I conversion P1.5-D.1.4 | Per-type harmonic backend implementation |
| **P1.5-E**: (T,E) eigenvalue + cross-convention | **Derived + R2 §3 corrected** | Combined cross-convention assembly P1.5-E.4.1 needs component-by-component verification | Wigner-d numerical check at $\ell = 2$ |
| **P1.5-F**: `packed_operators.py` audit | **Spec'd; ✓⁻ status retained** | Run regression tests in P1.5-F or include source in follow-up bundle | $\ell = 2$ specialization vs lowell §6 line 402–404 |
| **R9-NEW**: Bundle AF-1 evidence verbatim | **Applied below** | Verbatim excerpt of `ver2_native_integrator.py:2974–2980, 3047–3052, 3086` included as §4 appendix below | Self-contained — no external file dependency |
| **R9-NEW**: $\delta v_b = 0$ working hypothesis | **Self-flagged** (was buried in §A.7) | AF-1 closes the $v_b$ convention question but does NOT close $v_b^{\text{BASS}} \approx v_b^{(N)}$. Separate sync→Newtonian velocity comparison needed. | New `tests/integration/test_vb_frame_identification.py` |

### §4. Appendix: `ver2_native_integrator.py` verbatim excerpt for AF-1 evidence

The R7 audit cycle had access to `ver2_native_integrator.py` (uploaded by user 2026-04-25 between R7 review and R8 response). The R9 audit cycle did NOT have this file. To close the audit-readiness gap, the three relevant excerpts are recorded verbatim here.

#### §4.1 Slot label tuple (line 3086)

```python
3082:        return _LocalMatterHistory(
3083:            eta=eta_arr,
3084:            baryon_history=baryon_history,
3085:            cdm_history=cdm_history,
3086:            baryon_labels=("delta_b", "v_b", "v_e", "drag_lock_residual"),
3087:            cdm_labels=("delta_c", "v_c"),
```

**Reading**: `baryon_history[idx, 1]` is labelled `"v_b"` (velocity), not `"theta_b"` (divergence). Slot 2 is `"v_e"` (electron velocity). This is the consumer-facing API that `tier_b_source_extraction.py:225` reads.

#### §4.2 Baryon equation of motion (lines 3043–3052)

```python
3043:            drag_left = float(baryon_params_left.tau_dot / max(baryon_params_left.R_b, 1.0e-30))
3044:            drag_right = float(baryon_params_right.tau_dot / max(baryon_params_right.R_b, 1.0e-30))
3045:            lambda_left = float(baryon_params_left.H + drag_left)
3046:            lambda_right = float(baryon_params_right.H + drag_right)
3047:            forcing_left = float(3.0 * drag_left * theta_left)
3048:            forcing_right = float(3.0 * drag_right * theta_right)
3049:            baryon_v_next = (
3050:                float(baryon_state.v_b)
3051:                + 0.5 * dt * (forcing_left - lambda_left * float(baryon_state.v_b) + forcing_right)
3052:            ) / max(1.0 + 0.5 * dt * lambda_right, 1.0e-30)
```

**Reading**: the predictor-corrector update has forcing $= 3 \cdot (\dot\tau/R_b) \cdot \Theta_1$. The MB-95 sync-gauge baryon equation in physical-velocity convention reads $\dot v_b + (\mathcal H + \dot\tau/R_b) v_b = (\dot\tau/R_b)\, v_\gamma$ with $v_\gamma = 3\Theta_1$. The code's $3\Theta_1$ forcing matches velocity convention; if the code held $\theta_b = k v_b$, the forcing would have to be $3 k \Theta_1$ for dimensional consistency, which it does not.

#### §4.3 Slot population and slip term (lines 2974–2980)

```python
2974:        def _store(slot: int, theta_1: float) -> None:
2975:            baryon_history[slot, :] = (
2976:                float(baryon_state.delta_b),
2977:                float(baryon_state.v_b),
2978:                float(baryon_state.v_b),
2979:                float(3.0 * theta_1 - baryon_state.v_b),
2980:            )
```

**Reading**: slot 3 (the slip term) is $3\Theta_1 - v_b$. With $v_\gamma = 3\Theta_1$ in physical-velocity convention, this is the velocity-convention slip $v_\gamma - v_b$. If the code held $v_b = \theta_b = k v_b^{\text{phys}}$, slot 3 would have to be $3k\Theta_1 - \theta_b$ for dimensional consistency, which it is not.

#### §4.4 Combined verdict

The three excerpts together close AF-1 unambiguously: `baryon_local_history[:, 1]` holds physical velocity $v_b^{\text{phys}}$, and the dictionary key `_matter_seed_observables["theta_b"]` (line 1573, not excerpted) is a legacy naming artifact, not a convention statement. BASS's Doppler at `flrw_bessel_projector.py:453` is therefore short the canonical $1/k$ factor; the one-line fix is specified in R2 §5.

### §5. Self-flagged items remaining after R9

(i) The corrected P1.5-A back-reaction estimate uses representative values for $|\Psi|, \dot\kappa(\eta), \Delta\eta_{\text{rec}}$; a tight bound requires integrating against actual BASS `visibility_history` and $\Psi(\eta, k)$ history at the four anchor cells. (ii) The $\delta v_b = 0$ working hypothesis flagged in §A.7 is unchanged by R9; separate verification is needed to bound $v_b^{\text{BASS}} - v_b^{(N)}$. (iii) The R6 §2 master table downgrades all operators to ✓⁻ but assumes the *intended* coefficients are correctly implemented in `packed_operators.py`; if a future bundle reveals deviation, both the coefficient corrections and the test specs in P1.5-F need to be revisited. (iv) The R9 cycle did not revisit R8 §3's scope-bounding language for the executive-summary verdict; that remains as documented.

### §6. Closing

The second audit cycle has converted the original "substantially repaired but not SSoT-safe" verdict into a state where:
- All three minimum **document corrections** are applied with location-traceable edits; the AF-1 **production code fix** at `flrw_bessel_projector.py:453` remains a coding-agent ticket pending implementation
- All other FLAGGED items are addressed with explicit before/after language
- The canonical post-R9 SSoT table at §3 supersedes the historical R8/P1.5 tables
- The AF-1 evidence is now bundle-self-contained via the verbatim excerpts at §4

Three items remain as next-cycle audit candidates: (a) the coupled-hierarchy back-reaction with actual `visibility_history`, (b) the BASS internal `pstf_pack` normalization vs CL2000-I, (c) the cross-convention assembly P1.5-E.4.1 component verification. None of these is a fix to existing claims; they are refinements that would tighten existing bounds.

---

## R10. Third-cycle audit response (post-third-audit, 2026-04-25)

A third external audit was run after R9. The auditor's overall verdict: **"closed, but code-verdict pending AF-1 rerun"** — document quality is approaching SSoT-grade, but a logical gap was identified that survived the previous two cycles.

### §1. Three minimum document fixes — disposition

| Auditor's required fix | Status | Location |
|---|---|---|
| (1) "Doppler < 0.5% → anchor unaffected" logic is incomplete | **Applied**: the AF-1 `/k` fix multiplies Doppler contribution by $1/k$, so a $< 0.5\%$ pre-fix contribution at $k = 10^{-2}$ becomes $< 50\%$ post-fix as a naive upper bound (before $v_b \propto k$ scaling and Bessel-projection cancellations). The four-cell anchor invariance is **expected to be small but not yet verified** — must be re-run after fix lands. Both Executive summary and R2 §5 closing now say "anchor rerun required". | Executive summary AF-1 paragraph; R2 §5 closing paragraph |
| (2) R4 §5 stale `✓ implemented` table | **Applied**: supersession notice added at top of §5; status column updated to ✓⁻ for the eight operators whose source files are absent from R1 reading bundle. Table now internally consistent with R6 §2 and R9 §3 SSoT. | R4 §5 |
| (3) "All three minimum fixes are applied" conflates code with documentation | **Applied**: R9 §6 closing rephrased to "All three minimum **document corrections** are applied; the AF-1 **production code fix** at `flrw_bessel_projector.py:453` remains a coding-agent ticket pending implementation." | R9 §6 closing |

### §2. Other FLAGGED / MISSED items — disposition

| Finding | Status | Location |
|---|---|---|
| P1.5-A "Bounded at order ~1%-8%" too strong | **Applied**: weakened to "Estimated at order ~1%-8%; true bound pending actual visibility-history integration" in the canonical post-R9 SSoT table at R9 §3, P1.5-A row. | R9 §3 |
| R5 oracle scope language too broad | **Applied**: "High-$k$ source-assembly correctness" → "High-$k$ projector/source-form oracle coverage with synthetic controlled sources" in R9 §3 VR-2 row. R5 §6 already had appropriate scope language; the issue was the SSoT table summary. | R9 §3 (VR-2 row) |
| $\delta v_b = 0$ working hypothesis underexposed in executive summary | **Applied**: added explicit "Note on $v_b$ frame identification" paragraph after the AF-1 paragraph in executive summary, distinguishing the convention question (closed by AF-1) from the frame-identification question (still open). | Executive summary |
| MISSED: AF-1 fix → four-cell anchor must be re-run | **Acknowledged**: this is now the post-fix verdict-preservation test, captured in R10 §3 below as the canonical R10-NEW row in the SSoT table. | R10 §3 below |
| MISSED: `build_temperature_source` API choice should be frozen | **Applied**: R10 §4 below specifies `build_temperature_source(..., k_comoving: float)` as canonical, with rationale. | R10 §4 below |
| MISSED: legacy `"theta_b"` key not in AF-1 appendix | **Applied**: R10 §5 below adds the `_matter_seed_observables["theta_b"]` lines from `ver2_native_integrator.py:1271, 2962, 1573` as supplementary verbatim excerpts. | R10 §5 below |

### §3. Updated SSoT additions to R9 §3 table

The R9 §3 canonical SSoT table is amended with the following rows (originals retained for traceability; amendments below take precedence):

| Item | Status | Action required | Test fixture |
|---|---|---|---|
| **AF-1**: Doppler $/k$ | **Document fix specified; production code fix pending; four-cell anchor rerun required after code fix** | (1) Append `/ k` at `flrw_bessel_projector.py:453`; (2) thread $k$ through `build_temperature_source` signature per R10 §4; (3) re-run four anchor cells $(k, \ell) \in \{(10^{-3}, 2), (10^{-3}, 3), (10^{-2}, 2), (10^{-2}, 3)\}$ with `k_adapt_η100`; (4) verify each cell ratio remains within 5% of pre-fix ratio | R5 Oracle 5 (R5.5.1) for isolated regression; four-cell rerun for verdict preservation |
| **P1.5-A**: Coupled residual hierarchy | **Estimated at order ~1%-8%; true bound pending `visibility_history` integration** (R10-corrected wording) | Tighten with BASS `visibility_history` integration | Numerical test against actual $\dot\kappa(\eta)$ |
| **VR-2**: High-$k$ projector/source-form oracle coverage (R10-narrowed scope) | Deferred (regression suite) | Run R5 Oracles 1–5 against BASS LoS projector at $k \in [10^{-2}, 10^{-1}]$, $\ell \in [2, 100]$ with synthetic controlled sources. **Does NOT validate BASS source-extraction physics; only the LoS quadrature and source-assembly machinery.** | New `tests/los/test_analytic_oracles.py` |
| **R10-NEW**: Four-cell anchor rerun after AF-1 fix | **Mandatory verdict-preservation test** | After AF-1 code fix lands: re-run the four anchor cells; compare ratios to pre-fix; document any cell whose deviation exceeds 1% of the pre-fix ratio | New `tests/integration/test_anchor_post_af1_fix.py` |
| **R10-NEW**: $v_b$ frame identification ($v_b^{\text{BASS}}$ vs $v_b^{(N)}$) | **Self-flagged in P1.5-A §A.7 and Executive summary; separate validation needed** | Compute $v_b^{(s)} \to v_b^{(N)}$ via $\alpha = v_c^{(N)}/k$ (R3.2.2), compare to BASS's `baryon_local_history[:, 1]` | New `tests/integration/test_vb_frame_identification.py` |
| **R10-NEW**: Frozen API for AF-1 fix | **Specified at R10 §4** | `build_temperature_source(..., k_comoving: float)` canonical; component-decomposition outputs use corrected source from this API onward | API freeze applied at code-fix time |

### §4. Frozen API specification for AF-1 fix

Two implementation options were noted in R2 §5 for the $/k$ fix: (i) thread $k$ through `build_temperature_source` and apply $/k$ at line 453, or (ii) defer the $/k$ to the projector at line 499. R10 freezes option (i) as canonical, for the following reasons:

1. **Component decomposition stays correct downstream**. Many downstream consumers (Round-12→14 ablation tooling, the `bass/diagnostic/component_breakdown.py` outputs, and any future per-component validation) read the LoS source components separately. If the $/k$ is applied at the projector level, the stored "Doppler component" remains the BASS-internal $(g v_b)'$ expression, and downstream component analysis would have to apply the $/k$ correction independently each time. Threading $k$ through the source builder fixes the component at the canonical form once, and downstream analysis sees the correct contribution directly.

2. **R5 Oracle 5 regression alignment**. The isolated Doppler oracle expects the source builder to return $(g v_b)'/k$ matching $v_b(\eta_*)\, j_\ell'[kr_*]$ post-projection. With option (i), the regression test calls `build_temperature_source` with controlled inputs and validates the output directly. With option (ii), the regression must call both the source builder and the projector together, conflating the source-form question with the projection question.

3. **Future tilt extension cleanliness**. R4.3.3's tilted LoS source $S_T^{(u_e)}$ also requires a Doppler $/k$ in canonical form. Threading $k$ at the source-builder level provides a single API surface where both FLRW and tilted sources accept $k$ as input; option (ii) would push the divisor into the projector, mixing LoS-quadrature concerns with source-assembly concerns.

**Canonical signature**:
```python
def build_temperature_source(
    eta_grid: np.ndarray,
    g_arr: np.ndarray,
    e_kappa_arr: np.ndarray,
    theta0_arr: np.ndarray,
    psi_arr: np.ndarray,
    phi_arr: np.ndarray,
    pi_polter_arr: np.ndarray,
    vb_arr: np.ndarray,
    *,
    k_comoving: float,        # NEW: required positional-or-keyword for AF-1 fix
) -> np.ndarray:
    """Assemble the canonical CAMB / LC06 LoS temperature source.

    S_T = g[Theta_0 + Psi + Pi/4] + e^{-kappa}(dot Phi + dot Psi)
        + (g v_b)' / k
    """
    g_theta = g_arr * (theta0_arr + psi_arr + 0.25 * pi_polter_arr)
    isw = e_kappa_arr * (np.gradient(phi_arr, eta_grid, edge_order=2)
                         + np.gradient(psi_arr, eta_grid, edge_order=2))
    gvb = g_arr * vb_arr
    doppler = np.gradient(gvb, eta_grid, edge_order=2) / k_comoving   # AF-1 fix
    return g_theta + isw + doppler
```

The caller at `flrw_bessel_projector.py:499` must supply `k_comoving=k` from the projector loop's current $k$-mode. All downstream component-decomposition consumers must be updated to pass `k_comoving` as well — this is a small but global change that should land as a single PR alongside the `/k` fix.

### §5. AF-1 evidence appendix supplement: legacy `theta_b` key trace

The R9 §4 appendix had the three core `ver2_native_integrator.py` excerpts. The R10 audit requested the `_matter_seed_observables["theta_b"]` legacy key also be excerpted to make the seed-IC name story self-contained.

#### §5.1 Seed-IC dict population (line 1573)

```python
1571:            self._matter_seed_observables = {
1572:                "delta_b": float(unpacked["delta_b"]),
1573:                "theta_b": float(unpacked["theta_b"]),
1574:                "delta_c": float(unpacked["delta_c"]),
1575:                "theta_c": float(unpacked["theta_c"]),
```

**Reading**: at the seed-IC stage, the dict uses MB-95 *naming* convention (`"theta_b"` for the baryon momentum-related slot). This is the legacy artifact the auditor identified.

#### §5.2 Seed-IC dict consumed at $\eta_\text{init}$ (line 2962)

```python
2960:        return _MatterSeedState(
2961:            delta_b=float(self._matter_seed_observables["delta_b"]),
2962:            v_b=float(self._matter_seed_observables["theta_b"]),
2963:            delta_c=float(self._matter_seed_observables["delta_c"]),
2964:            v_c=float(self._matter_seed_observables["theta_c"]),
```

**Reading**: the value stored under the dict key `"theta_b"` is assigned **directly to the `v_b` field of `_MatterSeedState`**, with no $k$-rescaling or unit conversion. Combined with line 3086's `baryon_labels=("delta_b", "v_b", ...)`, this confirms the seed-IC value is consumed as physical velocity from the moment it enters the local-history pipeline. The `"theta_b"` dict-key naming is purely a naming holdover — the *value* is consistently velocity throughout.

#### §5.3 Combined verdict

R9 §4 (slot label, baryon EOM, slip term) + R10 §5 (legacy key trace) together make the AF-1 evidence completely self-contained. A future auditor with neither the bundle nor `ver2_native_integrator.py` can verify the convention chain from these excerpts alone:

```
unpacked["theta_b"]  →  _matter_seed_observables["theta_b"]  →  v_b field of _MatterSeedState
                                                                   (line 2962, no k-rescaling)
                       ↓
                       _LocalMatterHistory.baryon_history[:, 1] with label "v_b"
                                                                   (line 3086, slot 1)
                       ↓
                       baryon predictor-corrector forcing = 3 * drag * theta_1 (NOT 3k * drag * theta_1)
                                                                   (line 3047, velocity convention)
                       ↓
                       slip term stored at slot 3 = 3*theta_1 - v_b (NOT 3k*theta_1 - theta_b)
                                                                   (line 2979, dimensional consistency)
```

Every step of the chain is consistent with physical-velocity convention; no step is consistent with momentum-divergence ($\theta_b = k v_b$) convention. The AF-1 fix is required.

### §6. Self-flagged items remaining after R10

(i) The R10 §4 frozen API specification assumes `build_temperature_source` is the only entry point that needs to change; if other modules (e.g., `bass/diagnostic/component_breakdown.py` if it exists) also assemble the LoS source independently, they require parallel updates. Bundle does not include diagnostic modules to verify this.

(ii) R10 §3's "four-cell anchor rerun" specification assumes the rerun infrastructure (likely `scripts/v5_round15_decisive_los_test.py`) accepts the post-fix `build_temperature_source` API directly. If the script reads source components from a stored decomposition file, it may need updating to re-decompose with the corrected API.

(iii) The R10 §5 evidence chain shows the `_matter_seed_observables["theta_b"]` value is consumed as velocity; this confirms the *seed-IC convention* is velocity. It does NOT independently confirm that the *time-evolved* `v_b` after predictor-corrector updates remains velocity — but the §3047 forcing analysis (R9 §4.2) confirms the time-evolution is also in velocity convention, so the chain is closed.

(iv) The R10 cycle did not revisit the R9 §5 self-flagged items (visibility-history integration for P1.5-A; BASS internal `pstf_pack` normalization; P1.5-E.4.1 component verification); those remain as next-cycle audit candidates.

### §7. Closing

The third audit cycle has converted the document from "substantially repaired but not SSoT-safe" (post-R9 verdict) to **"document SSoT-passing; physics/code verdict pending AF-1 rerun"**. The minimum fixes required by R10's auditor are all applied. The R10 §3 amended SSoT table is now the canonical reference, with two new R10-NEW rows (anchor rerun, $v_b$ frame identification) explicitly tracked.

What remains is **not** a documentation issue: it is the **production code fix + four-cell rerun** that the coding agent must execute. After that:
- If post-fix four-cell ratios remain within 5% of pre-fix: the R3 §6 verdict ("monopole-frame correction not needed at four-cell 5% level") is preserved.
- If any post-fix ratio shifts substantially: the residual-correction story is more complex than R3 currently treats, and a fourth audit cycle would reopen R3 §6.

**The document is now closed for the P1+P1.5+R8+R9+R10 cycle.** Next audit (fourth) is recommended *after* the AF-1 production fix lands and the four-cell rerun results are available — that is the precise moment when the physics verdict can be either confirmed or reopened, and the next audit can focus on the rerun results rather than further documentation refinement.

---

## Integration appendix — retained material from R8 final-clean

The previous R8 final-clean document is superseded as a verdict source where it conflicts with this integrated SSoT. Its surviving contributions are retained only as background: (i) the rejection of the synchronous `h_S'/6` patch, (ii) the acceptance of the temperature `Π/4` and E-mode spin-2 split, (iii) the axisymmetric Bianchi-I exception for `m=±2`, and (iv) the general principle that analytic oracles must be labelled exact versus asymptotic. The R8 claim that no Doppler `/k` patch is authorized is explicitly superseded by the AF-1 evidence recorded in R9/R10.
