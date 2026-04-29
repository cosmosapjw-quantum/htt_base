JOURNAL-GRADE AUDIT — BASS Low-ℓ Bianchi Einstein–Boltzmann Solver
Audit scope: htt/bass/ only. Conclusions follow code, dispatch tables, gates, and tests; documentation claims are treated as hypotheses, not evidence.

1. CLAIM RECONSTRUCTION (PHASE 0)
#	Reconstructed claim	Provisional tag
C1	1+3 PSTF / tetrad low-ℓ formulation is the authority path	partially implemented (PSTF tower layout present pack_unpack.py:19, pstf_tensor.py; but Python primary path does not yet match Rust MB-95 anchor — Δ ≈ +2.04×10¹⁰ μK² on D₂; xfail at test_d2_pstf_closure.py)
C2	All 11 Bianchi families supported	registry/interface only for 8 of 11 (real full-mode coverage only FLRW, I, V, IX; II/III/IV/VI₀/VI_h/VII₀/VII_h/VIII raise NotImplementedError on off-axis modes)
C3	Background geometry validated for all 11 types (Wainwright–Ellis shear sources)	clearly implemented (shear_sources.py:98-360, registry :368-381, factories einstein_bianchi.py:605-618)
C4	Orthogonal + globally tilted backgrounds	partially implemented — orthogonal full; global tilt is policy-fixed by default; dynamic-rapidity owner gated behind tilt_background_owner (CLAUDE.md §1)
C5	Local boost = output-only post-processing, separated from global tilt	clearly implemented (observer/observer_boost.py:24-89, adapters.py:18-73, discriminator.py) — but no runtime guard against in-solver misuse
C6	Exact electron-frame Thomson collision (non-perturbative (1−v_e·n))	clearly implemented for axisymmetric tilt (collision/electron_frame.py:139-160, 244-292, tilted_visibility.py:201-222); regression-armored against the retracted /k patch
C7	Low-ℓ projected hierarchy (Tier B) end-to-end	clearly implemented for FLRW limit only (Python pipeline compute_flrw_d_ell runs; Bianchi LoS for II–VIII restricted to axis-aligned subset)
C8	Family-specific spatial backends (Bessel / hyperbolic / Wigner-D / collocation)	partial — FLRW/I Bessel, V hyperbolic-Legendre, IX Wigner-D dedicated; II/III/IV/VI₀/VI_h/VII₀/VII_h/VIII fall back to SolvableCollocationPropagator on restricted k-subsets (los/family_propagators/init.py:54-86)
C9	Family-specific IC provenance	weakly evidenced — zero_IC bootstrap shared across families; only Type V has a dedicated tilted-anchor factory; IC-provenance gate is in the ladder but no cross-family discriminating test
C10	Deterministic / stochastic / boost split in outputs	partially implemented — split structure present in forward/ver3_output_archive.py output_split_gate_bundle(); stochastic component is zero-filled placeholder; deterministic + boost are real
C11	Harmonic-level outputs (a_lm + T/Q/U maps)	partially implemented — forward/map_producer.py produces a_lm and HEALPix maps via inverse SHT (alm_to_map_TQU), but B-mode is flrw_zero_only sentinel and stochastic injection is absent
C12	Validation gate before fitting	clearly implemented — 14-stage GATE_LADDER in validation/ver3_gate_stop.py; hard_gate_before_fitting is called from inference/live_binding.py:219 and raises FittingBlockedError from inference/planck_likelihood.py:204,213,225 and inference/__main__.py:393
C13	Observables/statistics layer with covariance-aware likelihood	partial — dense a_lm Gaussian (statistics.py:51-77, 118-183), per-ℓ Gaussian fallback (:80-91); map-domain χ² absent; only Planck 2018 Plik low-ℓ TT real-data path
C14	Optimization (joint dense workspace, numba prep) preserves physics	honest but weakly evidenced — workspace pre-alloc (7aff3af) is bit-equal by construction (fill(0.0) ≡ np.zeros); numba is POC-only; no benchmark fairness regression test exists
What is solver-ready / output-ready / statistics-ready / dev-only / interface-only:

Solver-ready: FLRW limit forward model (Python pipeline runs end-to-end, but D₂ anchor unmet); orthogonal Bianchi I, V, IX backgrounds.
Output-ready: a_lm + D_ℓ for FLRW, I, V, IX; HEALPix maps for these via map_producer.py.
Statistics-ready: NONE — test_d2_pstf_closure.py is xfail; the gate ladder will block fitting until the FLRW closure passes (and gate flags are flipped by upstream tests/runners).
Dev-only: II/III/IV/VI₀/VI_h/VII₀/VII_h/VIII restricted-mode collocation; massive-neutrino branch; reionization-tanh; numba JIT.
Interface-only: stochastic ΛCDM realization injection; B-mode primordial source; dynamic-rapidity tilt evolution; map-domain likelihood.
2. EXECUTABLE PIPELINE RECONSTRUCTION (PHASE 1)
Actual end-to-end FLRW path that runs today:

Config / runtime control — bass.runtime.ver2_execution (cosmological cutoffs {12,16,20,30,40}); tilt_background_owner defaults to policy-fixed.
Family selection — closure/nabla_dispatch.py resolves (family, k_vec) → operator or raises NotImplementedError("FB-2.x") for off-axis modes.
Geometry / background init — background/einstein_bianchi.py:605-618 COSMOLOGY_FACTORY; shear_sources.py per family.
Family-specific backend — los/family_propagators/__init__.py: dedicated for FLRW, I, V, IX; collocation fallback otherwise.
Perturbation IC — hierarchy/ic.py:48-114 zero_IC; family-specific IC provenance is thin (registry-tagged, not solver-discriminating).
Hierarchy + transport — hierarchy/integrator.py LSODA, rtol=1e-6/atol=1e-12, max_step_factor=1000; inline TCA DAE-relaxation at ℓ=2 m=0 only.
Collision (authority path) — collision/electron_frame.py calls ThomsonPSTFCollisionOperator.evaluate_tower() after exact axisymmetric boost-in/boost-out around tilted_visibility.boost_factor.
Visibility / recombination — recombination/history_visibility.py HyRec table; reionization tanh disabled by default.
LoS — los/los_grid_builder.build_los_grid (Round-15 P0 closed); family propagators above.
Spectrum assembly — spectrum/flrw_pipeline.py:1147 compute_flrw_d_ell; D_ℓ in μK² with T_CMB=2.72548K but SSoT drift open (bass_py still 2.7255).
Output split — forward/ver3_output_archive.py output_split_gate_bundle: deterministic ✓, stochastic = zero-filled, boost ✓.
Map producer — forward/map_producer.py alm_to_map_TQU (healpy soft dep).
Likelihood / inference — inference/planck_likelihood.py with whitelisted datasets {synthetic_gaussian, synthetic_with_bianchi_template, planck2018_plik_low_l_tt_only}.
Fitting gate — validation/ver3_gate_stop.GATE_LADDER (14 gates), called by inference/live_binding.py:219; raises FittingBlockedError.
Drivers — inference/drivers/{dynesty_driver, emcee_driver}.py.
Profiling/benchmark — scripts/v5_round17_perf_*.py, no fairness regression test.
Missing connections / placeholders:

D_2 anchor closure (FLRW Python primary): not closed. The whole gate ladder is therefore dependent on the upstream FLRW closure flipping geometry_diagnostics_gate / production_cutoff_gate to True under genuine bit-identity, which they currently are not.
Stochastic ΛCDM injection: zero-filled.
Map-space likelihood: absent.
Bianchi LoS for non-{I,V,IX} families is collocation-fallback only.
3. PHYSICS IMPLEMENTATION AUDIT (PHASE 2)
3.1 Formalism-to-code fidelity
PSTF tower packing exists (pack_unpack.py:19, pstf_tensor.py) — full (2ℓ+1) slots allocated but only m=0 used in TCA closure (integrator.py:492 _ell2_m0_slot_offset). The m=0 → m∈{-2..+2} migration is openly deferred (CLAUDE.md PR-S13(b)).
T_CMB drift open: htt.core.ssot.C.T0_uK = 2.7255e6 is inconsistent with T0_K = 2.72548 in the same SSOT file; bass_py/.../planck_mes_bounds.py still uses 2.7255. Anti-regression guard exists; coordinated fix deferred.
Doppler /k retraction — the regression-armor test test_sharp_visibility_doppler_analytic_protects_no_over_k_patch enforces the canonical (g v_b)' form. Good.
3.2 Background physics
All 11 family shear sources implemented and tagged VALIDATED (shear_sources.py:98-360, 368-381). Class A/B Wainwright-Ellis formulas explicit. Type IX has recollapse event dispatch.
Tilted background: BianchiCosmology carries beta, v_hat_e; dynamic-rapidity owner exists (nonperturbative_tilt_rhs) but is gated; policy-fixed default means tilt does not feed back into the integrator RHS in production.
Codazzi-consistent tilt — present at construction; not exercised dynamically in default runs.
3.3 Transport / collision
Exact electron-frame Thomson: confirmed non-perturbative (electron_frame.py:139-160, tilted_visibility.py); axisymmetric boost-in / collision / boost-out structure (:244-292).
Polarization basis: E-mode is full PSTF rank-2 hierarchy with proper spin-2 streaming coefficients (polarization.py:74-225, emode_hierarchy.py:1-66); B-mode infrastructure present in tilted electron path (electron_frame.py:270-292); no primordial-GW B source.
Tilt-dependent Γ_T: only via electron tilt B(η,e) = γ_e(1+v_e·ê) (tilted_visibility.py:224-239). Baryon-bulk-velocity coupling to Γ_T is not present.
Visibility + reionization: HyRec scalar; reionization disabled by default; extend_table_with_reionization exists but isn't invoked in production.
3.4 Perturbation / hierarchy
Low-ℓ Θ_ℓ, E_ℓ towers present; B_ℓ tower exists in tilted-electron branch only; B is zero by construction for FLRW Bessel projector (sentinel b_mode_output_support="flrw_zero_only").
Neutrino sector: massless homogeneous fluid, Π_ν ≡ 0 (no anisotropic stress); massive branch has phase-space grid but is gated by Sigma_mnu.
TCA: inline DAE-relaxation, not pre-phase. Smoothness verified at threshold (test_tca_switch_smoothness.py).
Family-induced mode mixing: present at the propagator level for V (hyperbolic-Legendre) and IX (Wigner-D); for II/III/IV/VI₀/VI_h/VII₀/VII_h/VIII it's the collocation fallback restricted to axis-aligned subsets — mode mixing not exercised for these families.
IC provenance: weak — cross-family discriminating regression absent.
3.5 Classification
Fully implemented: exact Thomson, E-mode PSTF transport, all-11 shear sources, TCA inline relaxation, observer-boost separation, GATE ladder + FittingBlockedError, HyRec visibility, output-archive bundle structure.
Partially implemented: Bianchi LoS (4 of 11 full); polarization (E full, B per-family thin); tilt (policy-fixed default); cosmological m≠0 closure.
Weak / absent: stochastic injection; primordial-GW B source; baryon-tilt Γ_T; map-domain likelihood; reionization; massive-ν free-streaming shear.
Implemented but not validated: D_2 closure on Python primary; family-specific IC provenance; full-azimuthal m∈{-2..+2} closures.
4. FAMILY / TILT / BOOST COVERAGE AUDIT (PHASE 3)
4.1 11-family matrix (V = ✓, R = registry-only, X = absent, S = restricted-subset)
Family	Registry	Background	Backend	IC	Perturbation	Output	Stat-usable
FLRW	✓	✓	✓ Bessel	✓	✓	✓	✗ (D_2 not closed)
I	✓	✓	✓ Bessel	✓	✓	✓	✗
II	✓	✓	S k=(k₁,0,0)	✓	S collocation	S	✗
III	✓	✓	S k₂=0	✓	S collocation	S	✗
IV	✓	✓	S k₂=0, no FLRW limit	✓	S collocation	S	✗
V	✓	✓	✓ hyperbolic-Legendre	✓ (tilted-anchor)	✓	✓	✗
VI₀	✓	✓	S k₂=0	✓	S	S	✗
VI_h	✓	✓	S k₂=0	✓	S	S	✗
VII₀	✓	✓	S n₁=n₃ AND k∥e₂	✓	S	S	✗
VII_h	✓	✓	S k₂=0	✓	S	S	✗
VIII	✓	✓	S k=(k₁,0,0) Cartan	✓	S	S	✗
IX	✓	✓	✓ Wigner-D S³	✓	✓	✓	✗
Verdict: registry + background-shear are genuinely 11-broad; perturbation/output are 4-broad.

4.2 Orthogonal / global-tilt / local-boost separation
Background state: BianchiCosmology carries policy-fixed (beta, v_hat_e); orthogonal = beta=0.
Perturbation state: tilt enters only as parametric coupling through the electron-frame collision factor; not as a dynamical d.o.f. in production.
Output map / harmonics: deterministic alm produced from forward solver; observer boost applied as a separate kernel apply_observer_boost(Cl_frame, boost, L_max) (observer/adapters.py:18-73) — strictly post-processing.
Statistics layer: discriminator routes ObserverHypothesis separately from background hypothesis.
4.3 Forbidden-pattern checks
❌ No evidence that observer boost is misused as a substitute for global tilt — module dataclasses are explicitly disjoint (observer_boost.py:27-31: "must not subclass, alias, or silently coerce the cosmological tilt surface").
⚠️ No runtime assertion prevents future misuse; segregation is by discipline, not by guard.
⚠️ Type IV has no FLRW limit by construction — current registry treats it as a falsifiability probe; safe so long as no auto-FLRW recovery test is asserted on it.
⚠️ Development cutoffs {4,6,8} and cosmological {12,16,20,30,40} are co-resident; gate production_cutoff_gate exists but the gate flag is set by upstream tests, not enforced at runtime against pipeline calls — this is a soft gate.
5. OBSERVABLES / STATISTICS READINESS (PHASE 4)
5.1 Primary outputs
D_ℓ / C_ℓ for TT/EE/TE: spectrum/cl_assembly.py real.
a_lm for T/E/B: deterministic via forward solver; archived via output_split_gate_bundle.
T(n̂), Q(n̂), U(n̂) HEALPix maps: forward/map_producer.alm_to_map_TQU (real, soft dep on healpy).
5.2 Comparison hierarchy
Deterministic template sanity: yes (tests in forward/test_map_producer.py, test_ver3_output_archive.py).
Spectral per-ℓ Gaussian: likelihood/cosmological_frame.py:193 _spectral_log_prob.
Harmonic dense Gaussian: :228 _harmonic_log_prob — gated by harmonic_gaussian_ready.
Map-domain χ²: absent.
Covariance: dense blocks (TT, EE, TE, BB) supported; off-diagonal scaffolding in spectrum/off_diagonal_covariance.py.
5.3 Fitting gate
Gate ladder (14 gates) genuinely enforced. Trace: inference/__main__.py:393 catches FittingBlockedError; live_binding.py:81,219,328 raises it; planck_likelihood.py:204,213,225 raises it. This is real enforcement, not theatrical.
However: gate flags themselves are populated by upstream test/runner outputs. With the FLRW D_2 xfail, no Bianchi run today should be able to flip all 14 gates green. That is the intended posture: the gate ladder is open precisely because the closure isn't done.
5.4 Overclaim risk
Manuscript-level claims (docs/manuscript/) reference a Phase-1 anchor of D_2 = 1002.086744 μK²; this is currently the Rust path only. Anything that quotes this number as a Python-PSTF achievement is overclaim until test_d2_pstf_closure.py flips to xpass.
Honest envelope ("4 families full-mode, 8 families axis-aligned subsets") is documented in CLAUDE.md §1 — must be repeated in any external-facing report, not just in internal notes.
6. NUMERICAL MATURITY (PHASE 5)
Integrator: scipy LSODA, rtol=1e-6, atol=1e-12, max_step ≈ 14 Mpc (resolves recombination FWHM ~19 Mpc). Adequate for low-ℓ.
Stiffness: LSODA auto-switches; TCA inline relaxation supplements at Γ_T/H > threshold (default 100). Smoothness audited.
Convergence tests: validation/test_production_cutoff_convergence.py exists and exercises compute_flrw_d_ell cutoff stability — narrow but real.
FLRW recovery: fails Δ ≈ +2.04×10¹⁰ μK² at construction-fixed test (the previously latent test-bug — L_max_tower=4 vs ell_max_transfer=8 — was fixed; the test now fails honestly, which is a maturity gain).
Round-17 P2 linear-probe diagnostic: D_2(probe=1) = 6.4×10³ μK² vs anchor 1002 → factor ≈6.4 residual after primordial-amplitude flooring is disabled. Triangulated to V5_ROUND12-14 D-2 boundary issue (Lowell §13.2 seed valid only k·η_init ≪ 1; >50% of R17 k-grid violates this).
Workspace optimization: byte-equivalent (fill(0.0) ≡ np.zeros); 1.80× cumulative parallel speedup reported.
Maturity verdict: stable in narrow regime (FLRW orthogonal, fixed-tilt, low-ℓ, axis-aligned subsets). NOT publication-grade numerics on the Python primary path until D_2 closure lands.
7. OPTIMIZATION HONESTY (PHASE 6)
Optimization	Same eqs?	Same frame?	Same tol?	Same output?	Same fitting gate?	Verdict
Joint dense workspace pre-alloc (Tier 2D, 7aff3af)	✓	✓	✓	✓ bit-equal	✓	honest, physics-preserving
_operator_scales last-call cache (25b3731)	✓	✓	✓	bit-equal claim	✓	plausibly honest — no fairness test found
Python micro-opt + harmonic_affine perm cache (4ef59a2)	✓	✓	✓	FLRW: no-op (claimed)	✓	honest for FLRW, untested off-FLRW
Numba toolchain prep (f629e9c)	n/a	n/a	n/a	POC bit-equal 1000/1000	n/a	prep only, not deployed
1.80× cumulative parallel (87d6775)	depends on parts above	—	—	—	—	provisional — no committed cross-tolerance regression test
Forbidden-pattern probes:

❌ No evidence of mock spectrum tuning.
❌ No evidence of dev-cutoff masquerading as prod (cutoffs are listed in disjoint tuples).
❌ No evidence of shortcut frame transformation (the /k patch was retracted with regression armor).
⚠️ Missing: same-physics A/B regression suite for workspace and cache optimizations. Optimizations are bit-equal by construction, but a committed regression test would harden this.
8. DOCS / TESTS / RELEASE HONESTY (PHASE 7)
~3,200 individual def test_* functions across 186 files. 287 Round-16 baseline pass in 15.8 s — mostly unit/smoke.
End-to-end physics validation: compute_flrw_d_ell driven tests (xfail on D_2), production-cutoff convergence, TCA switch smoothness, Doppler /k regression armor, sharp-visibility analytic oracles. Real, but narrow.
Family-specific backend regression: present for I, V, IX (dedicated propagator tests); for II/III/IV/VI₀/VI_h/VII₀/VII_h/VIII the test surface is mostly dispatch-validation (does it raise OutOfScope correctly), not output validation.
Output-level validation: map_producer, ver3_output_archive have direct tests. Solid.
Statistics gate validation: validation/test_ver3_gate_stop.py exists and verifies the gate blocks when output_split is missing — good.
Optimization fairness test: absent.
Docs vs code consistency:
CLAUDE.md §1 honest envelope is consistent with the dispatch tables. Good.
docs/manuscript/ cites D_2 = 1002.086744 μK² — fair on the Rust path; would be overclaim if attributed to PSTF primary today.
Round-17 retraction of /k mandate is documented and code-armored. Good.
Release honesty stance: today, only "background-ready (11-family) + perturbation/output-ready (FLRW, I, V, IX) + gated statistics-blocked" can be honestly claimed. Anything stronger — Bianchi data fitting, full-azimuthal closure, full-family LoS — is ahead of the code.

9. CoVe + CONTRASTIVE VERIFICATION (PHASE 8)
9A. CoVe — synthesis-shaking questions and answers
Does the fitting gate actually run when you invoke a Planck likelihood? — Yes. live_binding.py:219 calls hard_gate_before_fitting; failure raises FittingBlockedError caught by __main__.py:393.
Is D_2 = 1002.086744 μK² achieved on the Python path? — No. test_d2_pstf_closure.py is xfail; gap ≈ +2.04×10¹⁰ μK².
Can a user fit Bianchi parameters today? — No — only synthetic-Gaussian and synthetic-with-template (whitelist) and planck2018_plik_low_l_tt_only; and with all 14 gates green, which is not the present state.
Is global tilt evolved dynamically? — No by default. tilt_background_owner defaults to policy-fixed; dynamic owner exists but is gated.
Are off-axis Bianchi modes computable for II–VIII? — No. nabla_dispatch.py raises NotImplementedError("FB-2.x"/"FB-5.2").
Does observer boost touch the integrator? — No. apply_observer_boost operates on Cl arrays post-assembly.
Is the exact electron-frame Thomson the production default? — Yes in electron_frame.py; non-perturbative; regression-armored.
Is the m=0→m∈{-2..+2} migration done? — No. Storage allocates 2ℓ+1 slots; physics-critical TCA closure uses m=0.
Is stochastic ΛCDM injected in the deterministic/stochastic/boost split? — No, zero-filled placeholder.
Is reionization active? — No (mode default disabled).
Are neutrinos carrying anisotropic stress? — No. Reduced fluid; Π_ν ≡ 0.
Is Type IV's missing FLRW limit a bug? — No, it is by construction, used as a falsifiability probe.
Is the optimization claim "1.80× cumulative parallel" same-physics? — By construction yes, but no committed fairness regression test.
Are the 11-family shear sources just stubs? — No, they are explicit Wainwright-Ellis formulas with VALIDATED tags and regressions in shear_sources.py.
CoVe net effect: synthesis stands; tightens C2 (registry/background broad, output narrow), C9 (IC provenance is weak), C14 (workspace is bit-equal but fairness untested).

9B. Contrastive H1 / H2 / H3
H1 (well-closed, mostly publication-grade): contradicted by D_2 xfail, 8/11 axis-aligned restriction, missing fairness test, scalar reionization, zero-filled stochastic, m=0-only closure.
H2 (strong exploratory + major revision needed for family/observables/gate honesty/optim honesty): consistent with all evidence.
H3 (premature, can't be called solver-ready or stat-ready): contradicted by genuine 11-family background validation, real fitting gate enforcement, real exact Thomson, real PSTF E-tower, real dispatch discipline.
Selected: H2 — strong exploratory solver with disciplined architecture; major revision required before headline statistics claims.

Per-axis verdicts:

Physics implementation: H2 (strong but uneven).
Family support: closer to H3 (broad registry, narrow solver).
Tilt/boost separation: H1 (well-closed by design).
Output/statistics readiness: H2 leaning H3 (gate is real but blocked; B/stochastic absent).
Numerical maturity: H2 (FLRW Python primary not yet closed; Rust anchor is the only validated source).
Optimization honesty: H1 leaning H2 (bit-equal by construction, lacks committed fairness test).
Docs / release honesty: H1 (CLAUDE.md envelope is admirably honest; risk lives in any external-facing summaries that omit it).
10. RANKED RISK LEDGER (P0 → P3)
P0 — blocks any data-fitting headline

R1: D_2 = 1002.086744 μK² not achieved on Python primary; xfail at test_d2_pstf_closure.py:45-50. All Bianchi statistical inference is parked behind this.
R2: Family LoS coverage is 4/11 (FLRW, I, V, IX); fitting any anomaly attributed to II–VIII would silently invoke restricted-mode subsets only.
P1 — blocks publication of specific subsystems

R3: m=0-only closure in TCA / hierarchy critical paths; full-azimuthal m∈{-2..+2} deferred (integrator.py:492). Off-axis polarization claims are not yet defensible.
R4: T_CMB SSoT drift open: T0_uK = 2.7255e6 vs T0_K = 2.72548 in same SSOT class; coordinated fix deferred.
R5: Stochastic ΛCDM injection is zero-filled placeholder — anything claiming "deterministic + stochastic + boost split" must qualify "stochastic = placeholder."
R6: Tilt is policy-fixed by default; any tilt-evolution claim requires explicit tilt_background_owner=dynamic.
P2 — blocks numerical-maturity claim hardening

R7: No committed optimization fairness regression test (workspace, scale-cache, harmonic-affine cache). Bit-equality holds by construction but is not test-armored.
R8: Reionization is disabled by default; tanh model exists but is not wired into the production pipeline.
R9: IC provenance gate is in the ladder but lacks cross-family discriminating regression — zero_IC is shared; risk of silent IC-content drift across families.
P3 — soft hygiene

R10: Observer-boost segregation relies on architectural discipline; no runtime guard rejects in-solver application.
R11: Numba JIT roadmap documented; not yet implemented; any future commit must add a same-physics regression.
R12: Type IV has no FLRW limit — must remain quarantined as a falsifiability probe in any documentation.
R13: Massive-neutrino fluid assumes Π_ν=0; sub-percent E-mode work would require free-streaming shear.
11. TOP-12 LOAD-BEARING RISKS
D_2 Python primary closure (R1) — single most load-bearing item.
Family LoS coverage 4/11 (R2) — caps any Bianchi-headline claim.
m=0-only closure (R3) — caps polarization claims.
Statistical fitting gate green-flip dependency on D_2 (chain of R1+R2+R3).
T_CMB drift (R4) — caps any precision-comparison claim.
Stochastic placeholder (R5) — caps "split" claim.
Policy-fixed tilt default (R6) — caps tilt-evolution claim.
No committed optimization fairness test (R7) — caps speedup claims.
IC-provenance discriminating regression missing (R9) — caps cross-family fairness claim.
Reionization disabled (R8) — caps recombination-history claim beyond standard.
Massive-ν / N_eff handling (R13) — caps high-precision claim.
Observer-boost runtime guard absent (R10) — long-tail correctness risk.
12. MINIMAL PATCH / OPTIMIZATION PLAN (≤12)
#	Patch	Failure mode it blocks	Where	Difficulty	Expected gain	Required-before claiming
P1	Close FLRW D_2 Python primary (Round-17 P2 sub-tracks (a)-switch → (c) → (b) → D-2)	Statistical fitting gate cannot legitimately flip green	spectrum/flrw_pipeline.py, IC seed _seed_formulae	high (multi-week)	unblocks all stat claims	solver-ready, statistics-ready, publication-grade
P2	Add cross-family IC-provenance discriminating regression	silent IC drift between families	hierarchy/ic.py + new validation/test_ic_provenance_regression.py	medium	tightens IC gate	family-broad solver-ready
P3	Add committed optimization fairness regression (same physics, same tol, A/B output)	undetected bit-drift from caches/JIT	new runtime/test_opt_fairness.py exercising compute_flrw_d_ell w/ and w/o caches	low-medium	hardens 1.80× claim	optimization-honest
P4	Resolve T_CMB drift (set both T0_K = 2.72548 and T0_uK consistently)	precision-comparison overclaim	htt/core/ssot.py, bass_py/.../planck_mes_bounds.py	low	closes SSoT inconsistency	publication-grade
P5	Replace stochastic-zero-fill with explicit NotImplementedStochasticChannel sentinel + gate flag	silent overclaim of "split"	forward/ver3_output_archive.py	low	honesty	output-ready
P6	Add runtime guard in apply_observer_boost rejecting in-solver metadata tags	future misuse	observer/adapters.py	low	architectural hardening	solver-ready (long-tail)
P7	Add explicit assertion E_0 == E_1 == 0 in E-mode RHS entry	latent spin-2 violation	collision/polarization.py	low	catches future regressions	output-ready (E)
P8	Add production_cutoff_gate runtime check at compute_flrw_d_ell entry rejecting L_max ∈ DEV_CUTOFFS	dev-cutoff sneaking into prod	spectrum/flrw_pipeline.py:1147	low	hardens gate	statistics-ready
P9	Document and test the off-axis NotImplementedError surface (ensure OutOfScopeError raised consistently across II–VIII; tighten to public exception type)	accidental silent fallback to FLRW kernel	closure/nabla_dispatch.py (consolidate error types)	low	clarity	family-broad output-ready
P10	Add map-domain χ² runner (uses existing alm_to_map_TQU) gated by independent map_likelihood_gate	bottleneck for full Bianchi anomaly fitting	new inference/map_likelihood.py	medium	enables map-level comparison	full statistics-ready
P11	Land the m=0 → m∈{-2..+2} closure migration (PR-S13(b)) and add azimuthal-mode regression	polarization off-axis correctness	hierarchy/integrator.py:492 family	high (3-5d)	unblocks polarization claims	publication-grade polarization
P12	Lift the Type IV/VII no-FLRW-limit caveat to a prominent README/manuscript line and add a CI-checked NOTE in bianchi_types.py:641-646	misuse as if it has FLRW recovery	docs + bianchi_types.py	low	clarity	release-ready
13. FINAL VERDICTS
A. Physics implementation: strongly implemented with caveats — exact Thomson, PSTF E, all-11 shear sources, TCA-relaxation are real and disciplined; closure breadth is narrow.

B. Family coverage: broad but uneven — 11/11 background, 4/11 full-mode LoS, 8/11 axis-aligned subsets. Closer to "broad registry, narrow solver" than to "genuinely broad support."

C. Observables / statistics: output-ready only, gated stat-ready not yet attained — gate ladder is real and enforced; closure (D_2) blocks legitimate fitting today.

D. Numerical maturity: narrow stable regime — LSODA + TCA-smooth + cutoff convergence is solid in FLRW, low-ℓ, axis-aligned subsets; D_2 Python primary not closed.

E. Optimization honesty: largely physics-preserving, weakly armored — bit-equality holds by construction; no committed fairness regression yet.

F. Overall code verdict: serious low-ℓ solver package with major revision needed before any data-fitting headline. Best-supported hypothesis: H2.

14. HEADLINE CLAIMS — ALLOWED vs NOT ALLOWED
Allowed (today)

"11 Bianchi families have validated background geometry and shear-source registry."
"Exact non-perturbative electron-frame Thomson scattering is the production default; the retracted Doppler /k patch is regression-armored."
"Local-observer boost is structurally separated from cosmological tilt and applied as post-processing."
"Forward-model outputs are split into deterministic / stochastic / boost archives, with a 14-stage gate ladder enforcing FittingBlockedError before any likelihood evaluation."
"TCA is implemented as inline DAE-relaxation (no pre-phase), with a switch-smoothness regression."
"FLRW, I, V, IX have full-mode LoS coverage; II/III/IV/VI₀/VI_h/VII₀/VII_h/VIII are restricted to axis-aligned subsets per FB-2.2 / FB-2.3 (NotImplementedError on off-axis modes)."
"Recent runtime optimizations (joint workspace, scale cache) are bit-equal by construction; cumulative ~1.80× parallel speedup."
Not yet allowed

"PSTF primary achieves D_2 = 1002.086744 μK² bit-identically." (Rust path only; Python primary xfails.)
"Bianchi parameters are fittable to Planck data." (Gate ladder is intentionally blocked.)
"Full-azimuthal m∈{-2..+2} closure." (Deferred.)
"Stochastic ΛCDM realizations are injected." (Zero-filled placeholder.)
"Reionization-included visibility." (Disabled by default.)
"Dynamic global-tilt evolution in production." (Policy-fixed default.)
"Map-domain likelihood." (Absent.)
"B-mode primordial polarization output." (flrw_zero_only sentinel.)
"1.80× speedup is regression-test-armored for same-physics." (No committed fairness test.)
Internal/dev-only

Numba JIT plan, m∈{-2..+2} migration, real-time reionization, massive-ν free-streaming shear, off-axis FB-5.2 dispatch.
Hard-gate before any data fitting

D_2 Python primary closure; 14-gate ladder green; T_CMB SSoT drift fix; explicit stochastic channel (or sentinel); production-cutoff runtime check.
15. ONE-LINE REASON
Architecture and discipline are real and admirable; the FLRW Python-primary D_2 closure has not landed and family LoS coverage is 4/11 — so call this a serious low-ℓ Bianchi solver package whose statistics layer is correctly gated shut until that closure and a few honesty patches land.