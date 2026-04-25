# V5 Round-15 P1 PSTF Derivation — Cumulative Working Document

**Build mode:** cumulative. Each round appends to this document rather than replacing prior material.  
**Language standard:** English.  
**Scope:** documentation only; no production-code changes.  
**Current build:** R6 complete — R7 independent-audit corrections applied; R8 minor-edit pass complete; Appendices X/Y integrate parallel-cycle errata and supplementary analytical notes (2026-04-26).  
**Source bundle:** `v5_round15_p1_handoff_bundle.zip`, repo layout preserved.
**R7 correction basis:** `docs/audits/V5_ROUND15_P1_R7_INDEPENDENT_AUDIT.md`.
**Parallel-cycle errata:** Appendix X documents a parallel three-cycle external-LLM audit run (R8/R9/R10 in that run's numbering) that reached the *opposite* AF-1 verdict from R7. The R7 independent audit above is authoritative; Appendix X retains the false trail for traceability and methodology. Appendix Y preserves the genuinely new analytical content from that parallel run that survives independent of the retracted AF-1 chain.

## Executive Summary — R6 Master Verdict \(R7-Corrected\)

**Verdict.** BASS's transport hierarchy is genuinely PSTF/tetrad-native, and P1 should not be converted into a synchronous-gauge metric patch. The FLRW LoS projector/grid layer is structurally healthy. After the R7 independent audit, the native scalar FLRW source assembly has **one** unresolved formal contract, not three: the gauge/frame meaning of `theta0_g` entering the SW combination `theta0_g + psi`.

**Resolved by R7.** The Doppler source `(g v_b)'` is the standard `j_l`-only form for dimensionless peculiar velocity `v_b = theta_b/k`; no `1/k` patch is authorized. The temperature polter term `g Pi/4`, with `Pi = Theta_2 - sqrt(6) E_2`, is the canonical scalar temperature contribution in the collapsed `j_l` source; the spin-2 projection factor belongs to the separate E-mode branch and is already implemented through `e_mode_projection_factor`.

**Immediate code changes.** None are authorized by this documentation round. Do not add `h_S`, `h_dot`, `h_prime`, or `theta0_g_newtonian = theta0_g_synchronous + h_S_dot/6` to the PSTF runtime path. Do not add a Doppler `1/k` correction. Do not replace the temperature-side `Pi/4` term by a spin-projected radial factor.

**Required follow-up before full source correctness is claimed.** Close the `theta0_g` monopole source contract. Specifically, declare whether `photon_T_tower[:, slot(0,0)]` is already the Bardeen/Newtonian emission monopole compatible with the reconstructed `Psi`; if not, define a PSTF-native scalar time-shift `alpha` and apply the covariant correction `Theta_0 -> Theta_0 + H alpha`. Add the `theta0` convention test and the potential-invariance test. Sharp Doppler and polarization oracles should still be added, but as regression tests rather than unresolved-contract gates.

**Bianchi extension.** The correct Bianchi target is not reuse of the scalar FLRW `S_T j_l` source. It is a tetrad/PSTF matrix propagator with shear/curvature recoupling, tilted electron-frame collision/source/visibility, and downstream observer-side `a_{ell m}` or map-level likelihood output. Axisymmetric Bianchi I with an aligned tetrad is the restricted exception where `m=0` can remain sufficient; general tilted/non-axisymmetric Bianchi I and Bianchi II--IX require the all-`m` treatment.

**Follow-up priority.** The highest-priority code-adjacent task is now the monopole-frame diagnostic, not Doppler or polarization patching. The sharp Doppler oracle remains valuable because it protects the correct `(g v_b)'` convention against future regressions.

---


## Build Log

| Round | Status | Content |
|---|---:|---|
| R1 | complete | Grounded reading of repo state, frame/gauge conventions, empirical Round-15 P0 status, and formalization gaps. |
| R2 | complete | FLRW-limit PSTF line-of-sight source derivation, term audit against BASS projector/source code, and consistency check. |
| R3 | complete | \(\ell=0\) monopole convention audit and gauge/frame verdict. |
| R4 | complete | Bianchi tetrad-frame extension blueprint, including shear, all-m coupling, tilt, MES, and code-mapping consequences. |
| R5 | complete | CAMB-independent analytic and asymptotic LoS validation oracles for high-k projector/source testing. |
| R6 | complete | Master code-mapping table, executive summary, source-contract follow-up actions, and acceptance check. |
| R7 audit integration | complete | Incorporated independent-audit corrections: Doppler and temperature polter warnings retracted; monopole contract retained; Bianchi-I axisymmetry caveat added. |
| R7 | optional | Second-review audit prompt. |
| R8 minor-edit | complete | Document-hygiene pass after R7 PASS-with-minor-edits verdict. |
| Appendix X | complete | Errata: parallel three-cycle external-LLM audit run (R8/R9/R10 in that run's numbering) retracted; AF-1 verdict in that run was wrong; preserved for traceability. |
| Appendix Y | complete | Supplementary analytical notes salvaged from the retracted parallel run: (T,E) eigenvalue derivation, recombination $\dot\kappa$ values, $k_{\rm eq}$ formula, coupled residual-hierarchy estimate. Not part of R6 verdict chain. |

---

# R1 — Grounding in Repository State and Prior Work

## R1.0 Working Priority and Supersession Rule

This R1 pass reads the Round-15 P1 briefing as the controlling document. Earlier Round-12 through Round-15 notes describe a prospective “D-3 gauge fix” as if BASS internally carried a synchronous-gauge photon monopole and only needed a synchronous-to-Newtonian conversion. The P1 briefing explicitly supersedes that framing: the P1 task is not an immediate production-code patch, but an audit-first formalization of whether the PSTF-native \(\Theta_0\) convention is the correct input to the BASS line-of-sight source as written.

This document therefore uses the following priority order:

1. The Round-15 P1 hand-off controls the mission, constraints, and prompt sequence.
2. `docs/lowell_bianchi_solver_reference.md` is the central PSTF/tetrad design authority.
3. The CAMB↔BASS mapping note is used as a comparison oracle for the FLRW limit, not as a replacement formalism.
4. The code files are treated as the executable implementation anchor.
5. Earlier Round-12→15 diagnostic documents are historical evidence; claims contradicted by the P1 hand-off are retained as “previous diagnosis” rather than adopted as final theory.

No new derivation is attempted in R1. This section only establishes the shared state required before R2.

---

## R1.1 What Gauge / Frame the BASS PSTF Photon Hierarchy Lives In

1. **Primary formalism.** BASS is designed around a \(1+3\) covariant PSTF/tetrad representation, not around Newtonian or synchronous gauge as the primary state space. The central design document fixes the metric signature \((- + + +)\), decomposes spacetime with a fundamental observer congruence \(n^a\), and defines the standard kinematic split into acceleration, expansion, shear, and vorticity; see `docs/lowell_bianchi_solver_reference.md:25-47`.

2. **Frame split.** The intended Bianchi architecture separates the transport frame from the collision/source frame:
   \[
   \text{transport in }n^a\text{-frame},\qquad
   \text{collision/source/visibility in }u_e^a\text{-frame}.
   \]
   The same document states this explicitly and interprets it as the most stable way to cover both orthogonal and tilted Bianchi cases; see `docs/lowell_bianchi_solver_reference.md:49-63`.

3. **Radiation variables.** The radiation sector is expressed by PSTF temperature and polarization multipoles \(\Theta_{A_\ell}\), \(E_{A_\ell}\), and \(B_{A_\ell}\), with harmonic numerical coefficients \(\Theta_{\ell m},E_{\ell m},B_{\ell m}\); see `docs/lowell_bianchi_solver_reference.md:320-354`.

4. **Hierarchy-level implementation.** The actual photon RHS driver is PSTF-native. `htt/bass/hierarchy/hierarchy_rhs.py` describes itself as summing the nine-term PSTF multipole hierarchy \(T1+\cdots+T9-K\) at every \(\ell\), with photon and neutrino entry points; see `htt/bass/hierarchy/hierarchy_rhs.py:1-12`. It imports and applies the packed PSTF operators `apply_T1_expansion_packed`, `apply_T7_shear_up_packed`, `apply_T8_shear_same_packed`, and `apply_T9_shear_down_packed`; see `htt/bass/hierarchy/hierarchy_rhs.py:76-84`.

5. **Shear frame and units.** The hierarchy driver converts the tetrad state’s conformal shear \(\Sigma_{ab}=a\sigma_{ab}\) into proper-time shear \(\sigma_{ab}\) by dividing by \(a(\eta)\). If no tetrad state is supplied, the path is FLRW with \(\sigma_{ab}=0\); see `htt/bass/hierarchy/hierarchy_rhs.py:123-177`.

6. **No synchronous metric state in the integrator output.** The integrator’s public `IntegrationResult` contains `eta`, `a`, shear variables, photon temperature and E-mode towers, neutrino state, baryon/CDM local histories, and other bookkeeping; it does not expose a synchronous-gauge metric trace such as \(h_S\) or \(h_S'\). See `htt/bass/hierarchy/integrator.py:223-255` and the multipole accessors at `htt/bass/hierarchy/integrator.py:260-304`.

7. **FLRW source extraction does introduce Newtonian-gauge potentials as derived quantities.** The FLRW source extractor constructs the five `FLRWSourceTerms` needed by the LoS projector from the Tier-B PSTF output. Its docstring says it extracts Newtonian-gauge callables and derives \(\Phi\), \(\Psi\) from Einstein constraints; see `htt/bass/spectrum/tier_b_source_extraction.py:1-7` and `htt/bass/spectrum/tier_b_source_extraction.py:22-44`. It returns callables for \(\Theta_0^\gamma\), \(\Psi\), \(\dot\Phi+\dot\Psi\), \(v_b\), and \(\Pi\); see `htt/bass/spectrum/tier_b_source_extraction.py:123-159`.

8. **The critical R3 issue.** The extractor currently reads
   \[
   \Theta_0^\gamma = \texttt{t\_tower[:, slot(0,0)]}
   \]
   and forms \(\Pi=\Theta_2-\sqrt6 E_2\); see `htt/bass/spectrum/tier_b_source_extraction.py:225-236`. It then converts radiation monopoles to density contrasts via \(\delta_\gamma=4\Theta_0^\gamma\) and reconstructs \(\Phi,\Psi\) using Newtonian-gauge constraint algebra; see `htt/bass/spectrum/tier_b_source_extraction.py:254-306`. The unresolved formal question is not whether to expose a hidden synchronous \(h_S'\) variable; the unresolved question is whether the PSTF-native monopole entering \(\Theta_0+\Psi\) is already the gauge-coherent observable combination required by the LoS source. R3 must decide this algebraically.

9. **Line-of-sight projector state.** `htt/bass/los/flrw_bessel_projector.py` is only a projector/integrator: it does not evolve \(\Theta_0\), \(\Phi\), \(\Psi\), or \(v_b\). It assembles
   \[
   S_T(\eta)=g(\eta)[\Theta_0(\eta)+\Psi(\eta)+\Pi(\eta)/4]+e^{-\kappa(\eta)}[\dot\Phi(\eta)+\dot\Psi(\eta)] + \frac{d}{d\eta}[g(\eta)v_b(\eta)]
   \]
   and
   \[
   S_E(\eta)=-(\sqrt6/4)g(\eta)\Pi(\eta),
   \]
   as documented at `htt/bass/los/flrw_bessel_projector.py:23-30` and implemented at `htt/bass/los/flrw_bessel_projector.py:416-455` and `htt/bass/los/flrw_bessel_projector.py:458-472`.

**R1 verdict on frame/gauge state:** The hierarchy itself is PSTF/tetrad-native. The FLRW comparison layer reconstructs Newtonian-gauge potentials and feeds them to a canonical LoS source. The only genuinely dangerous convention boundary is the \(\ell=0\) monopole in the SW combination \(\Theta_0+\Psi\); this must be audited in R3. For \(\ell\ge1\), the existing documents consistently treat the PSTF multipoles as gauge-invariant around FRW, but R2/R3 should still cite the canonical references directly.

---

## R1.2 What `lowell_bianchi_solver_reference.md` Covers and What It Leaves Implicit

### Covered explicitly

1. **Global scope and physical approximation.** The design document is a self-contained low-\(\ell\) tetrad-based Bianchi CMB solver note. It aims to compute low-\(\ell\) TT/TE on exact orthogonal/tilted Bianchi backgrounds plus linear fluctuations, using anisotropic/frame-aware source evaluation, visibility weighting, transport, collision, and LoS propagation while retaining first-pass isotropic recombination/reionization microphysics; see `docs/lowell_bianchi_solver_reference.md:3-19`.

2. **Frame architecture.** It states the central rule: transport in \(n^a\), collision/source/visibility in \(u_e^a\); see `docs/lowell_bianchi_solver_reference.md:49-63`.

3. **Minimal low-\(\ell\) state.** It starts from \(\{\Theta_0,\Theta_1,\Theta_2,E_2\}\), with optional \(\{\Theta_3,E_3\}\), and recommends \(L=4\) as the minimum self-consistent cutoff, \(L=6\) as baseline, and \(L=8\) for convergence checks; see `docs/lowell_bianchi_solver_reference.md:64-86`.

4. **Exact Bianchi background variables.** It organizes the background around \(\alpha\), \(\beta_{ab}\), conformal shear \(\Sigma_{ab}\), anisotropic spatial curvature \({}^{(3)}R_{ab}\), and Bianchi structure constants \(C^i{}_{jk}\); see `docs/lowell_bianchi_solver_reference.md:90-115`.

5. **Radiation PSTF hierarchy.** It gives the exact energy-integrated brightness hierarchy with expansion, gradient/divergence, acceleration, vorticity, and shear terms. In orthogonal Bianchi, \(A_a=\omega_a=0\), leaving the expansion/streaming/shear/collision structure; see `docs/lowell_bianchi_solver_reference.md:358-393`.

6. **Why \(L=2\) is not self-consistent.** At \(\ell=2\), the hierarchy contains couplings to \(\Pi_{abcd}\), a same-rank shear term, and a monopole-to-quadrupole shear injection term \(-4\sigma_{ab}\Pi\). This is the explicit reason the note recommends \(L\ge4\); see `docs/lowell_bianchi_solver_reference.md:395-426`.

7. **Low-\(\ell\) LoS structure.** Instead of a single FLRW spherical-Bessel kernel, the Bianchi formal solution is a path-ordered, background-dependent matrix propagator acting on the multipole state and source history; see `docs/lowell_bianchi_solver_reference.md:430-460`.

8. **Generic redshift source.** The source-sector discussion starts from the generic energy-redshift law
   \[
   \frac{dE}{dv}=-\left[\frac13\Theta + A_a e^a + \sigma_{ab}e^ae^b\right]E^2,
   \]
   then separates background and fluctuation pieces. The minimal covariant source variables are \(\delta\Theta\), \(\delta A_a\), and \(\delta\sigma_{ab}\); see `docs/lowell_bianchi_solver_reference.md:464-502`.

9. **Photon collision/source convention.** The photon section defines the Thomson polarization source tensor and the convenient harmonic normalization
   \[
   \Pi^m=\Theta_2^m-\sqrt6 E_2^m,
   \]
   with collision terms for temperature and polarization multipoles; see `docs/lowell_bianchi_solver_reference.md:544-590`.

10. **Orthogonal vs tilted distinction.** Orthogonal Bianchi identifies the transport and electron frames in the background. Tilted Bianchi keeps transport in \(n^a\) while computing collision/source/visibility in the electron frame; it generates background momentum density, perturbation dipoles, direction-dependent visibility, and extra \(\ell\leftrightarrow\ell\pm1\) mixing in moment language; see `docs/lowell_bianchi_solver_reference.md:761-783`.

11. **Observer-side output and likelihood.** The solver evolves \(\Theta_{\ell m},E_{\ell m},B_{\ell m}\) internally but should output \(T,Q,U\) maps or observer-projected \(a_{\ell m}^{T,E,B}\). In exact Bianchi, a full covariance \(\langle a_{\ell m}^X a_{\ell' m'}^{Y*}\rangle\) is more honest than an isotropic \(C_\ell\)-only likelihood; see `docs/lowell_bianchi_solver_reference.md:948-1012`.

### Left implicit or not yet audit-ready

1. **No step-by-step FLRW LoS derivation.** The document contains the correct ingredients — PSTF hierarchy, matrix LoS structure, SW/ISW/redshift-source logic — but it does not explicitly derive the exact FLRW scalar source used by `build_temperature_source`, term by term, from the PSTF transport equation.

2. **No explicit \(\ell=0\) convention audit.** The note states the frame architecture and CAMB regular adiabatic seed target, but it does not prove how the PSTF monopole, Newtonian monopole, and CAMB/CDM-rest-frame monopole transform into each other.

3. **No final gauge-coherence proof for \(\Theta_0+\Psi\).** The crucial observable combination in the SW source is not yet proven to be convention-stable in the current BASS assembly.

4. **Bianchi LoS source terms remain structural.** The document says Bianchi requires a matrix propagator and redshift-source variables, but it does not yet give implementation-ready formulas for all shear-induced LoS terms, \(m=\pm2\) recoupling, tilted observer boost terms, or their code targets.

5. **No high-k analytic validation oracle.** The design document does not provide closed-form analytic high-k tests independent of CAMB internals.

6. **No master code-mapping table.** The note contains formal equations and architecture, but not a systematic derivation-to-file-to-line audit table.

---

## R1.3 CAMB / MB-95 / CLASS as Oracles, Not Primary Formalisms

The CAMB↔BASS mapping note makes three important points for later derivation rounds.

1. CAMB was built from the same broad \(1+3\) covariant PSTF lineage, and its internal intensity variables are identified with PSTF harmonic moments. The note states that CAMB’s `clxg`, `qg`, and `pig` correspond to \(I_0=\Delta_\gamma\), \(I_1=q_\gamma\), and \(I_2=\pi_\gamma\), with \(I_\ell=F_{\gamma\ell}^{MB}=4\Theta_\ell\); see `project/04_implementation_specs/...Guide_for_bass_rs.md:7-25`.

2. CAMB works in the CDM rest frame, equivalent to synchronous gauge with zero CDM velocity. The note says this explicitly and identifies the synchronous metric shear variable; see `project/04_implementation_specs/...Guide_for_bass_rs.md:23-25`.

3. The covariant hierarchy-to-CAMB mapping is presented as an exact harmonic reduction of the PSTF hierarchy, with the Fourier streaming coefficients arising from PSTF angular-momentum algebra; see `project/04_implementation_specs/...Guide_for_bass_rs.md:131-168`. The same note’s three-way table, however, says a gauge transformation is needed between the CDM-frame CAMB/CLASS side and a conformal-Newtonian comparison surface; see `project/04_implementation_specs/...Guide_for_bass_rs.md:186-204`.

For P1, this means CAMB/MB-95 can be used to cross-validate the FLRW limit, but the derivation must remain PSTF-native. The CAMB mapping is most valuable as a convention dictionary and sanity check, not as the governing language for Bianchi II–IX.

---

## R1.4 Empirical State of the FLRW-Limit BASS Implementation after Round-15 P0

1. **D-1 was an LoS grid pathology.** Before P0, the LoS quadrature reused a 64-point uniform integrator output grid spanning roughly \([261,14147]\,\mathrm{Mpc}\), with spacing \(\Delta\eta\approx220\,\mathrm{Mpc}\). This under-resolved the recombination visibility width of about \(19\,\mathrm{Mpc}\) and the Bessel period at moderate/high \(k\); see `docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md:7-19`.

2. **P0 introduced a per-\(k\) composite LoS grid.** The new grid has a recombination-refined zone with \(\Delta\eta\approx2.4\,\mathrm{Mpc}\) and a \(k\)-adapted oscillation zone with \(\Delta\eta=(2\pi/k)/8\); see `docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md:20-30`.

3. **The projector became resolution-independent.** A sweep over `n_per_oscillation ∈ {8,16,32,64,128}` and `n_per_recomb_fwhm ∈ {8,16,32,64}` showed stable post-fix ratios; for example, at \(k=10^{-2}\,\mathrm{Mpc}^{-1}\), \(\ell=2\), the ratio stayed around 0.832–0.833 across increasingly dense grids; see `docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md:60-67`.

4. **The decisive transcript confirms D-1 resolution but not full physical closure.** The median absolute ratio improved from 8.304 on the pre-fix uniform grid to 1.004 on the post-fix production grid, and the max-ratio defect dropped by about a factor of 14; see `docs/audits/v5_round15_p0_d1_fix_transcript_2026-04-25.txt:57-84`.

5. **Low-\(k\) cells become near-CAMB once the lower integration bound is artificially extended.** The `k_adapted_eta100` column, which isolates D-1 from the integrator \(\eta_{init}\) truncation, gives:

   | \((k,\ell)\) | CAMB direct | `k_adapted_eta100` | ratio |
   |---:|---:|---:|---:|
   | \((10^{-3},2)\) | \(+4.53897\times10^{-2}\) | \(+4.237\times10^{-2}\) | 0.933 |
   | \((10^{-3},3)\) | \(+2.65994\times10^{-2}\) | \(+2.617\times10^{-2}\) | 0.984 |
   | \((10^{-2},2)\) | \(+7.64686\times10^{-3}\) | \(+7.983\times10^{-3}\) | 1.044 |
   | \((10^{-2},3)\) | \(+7.06768\times10^{-3}\) | \(+7.058\times10^{-3}\) | 0.999 |

   These are the key empirical ratios for R2’s consistency check; see `docs/audits/v5_round15_p0_d1_fix_transcript_2026-04-25.txt:33-46` and the P0 summary at `docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md:75-82`.

6. **The strict 5% gate was not fully met because D-2 and source-convention/high-k issues remain.** The transcript states that D-1 is delivered, but the strict 5% gate is missed because the production BASS integrator starts at \(\eta\approx261\,\mathrm{Mpc}\), truncating part of the pre-recombination history. It also flags high-\(k\) residuals; see `docs/audits/v5_round15_p0_d1_fix_transcript_2026-04-25.txt:73-87`.

7. **Earlier D-3 diagnosis must be reinterpreted.** The P0 summary and Round-12→14 investigation still describe the high-\(k\) residual as a Newtonian/synchronous gauge mismatch and propose exposing \(h_S'\); see `docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md:113-119` and `docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:199-233`. The P1 briefing, however, explicitly changes the question: BASS does not use synchronous gauge internally, so the real task is an audit of the PSTF-native \(\ell=0\) monopole convention and the gauge coherence of \(\Theta_0+\Psi\).

8. **High-\(k\) CAMB-direct validation is not reliable as originally assumed.** The P1 briefing reports that even CAMB’s exposed `T_source` reproduces CAMB’s own direct `delta_p_l_k` only up to roughly \(k\lesssim10^{-2}\,\mathrm{Mpc}^{-1}\). At higher \(k\), CAMB’s exposed source path and internal integration path diverge, so R5 must build CAMB-independent analytic oracles.

**R1 empirical verdict:** The LoS projector and grid are now numerically healthy over the supplied source domain. At low \(k\), when the \(\eta_{init}\) truncation is artificially lifted, the PSTF→observable assembly agrees with the valid CAMB oracle at the few-percent level. This makes it plausible — but not yet proven — that the BASS FLRW source assembly is structurally correct. The proof is exactly R2/R3.

---

## R1.5 The Three Main Open Formalization Gaps

### Gap A — FLRW-limit PSTF LoS derivation

The current code assembles the standard-looking source
\[
S_T=g(\Theta_0+\Psi+\Pi/4)+e^{-\kappa}(\dot\Phi+\dot\Psi)+\frac{d}{d\eta}(gv_b),
\]
but the repo lacks a step-by-step derivation from the PSTF photon transport equation to this exact FLRW line-of-sight source while keeping PSTF variables primary. R2 must derive this, identify SW/ISW/Doppler/polarization-source terms, compare to `build_temperature_source`, and cross-check against MB-95/CAMB only as an oracle.

### Gap B — \(\ell=0\) monopole convention

For \(\ell\ge1\), PSTF multipoles around FRW can be treated as gauge-invariant in the standard covariant perturbation sense. The monopole \(\ell=0\), however, is density-like and therefore convention/frame dependent. R3 must trace the code path from seed to hierarchy to `IntegrationResult` to `tier_b_source_extraction.py:225`, then derive the relation among the PSTF monopole, Newtonian/longitudinal monopole, and CAMB/CDM-rest-frame monopole. The core question is whether the source combination \(\Theta_0+\Psi\) is already gauge coherent in the current BASS assembly.

### Gap C — Bianchi-essential tetrad extension

The lowell reference provides the structural Bianchi framework but not a coding-agent-ready extension of the FLRW LoS source. R4 must specify how shear \(\sigma_{ab}\), the T7/T8/T9 operators, \(m=\pm2\) channels, tilted observer frames, direction-dependent visibility, and the MES/x_C translation enter the formalism. The target is not a complete Bianchi II–IX implementation, but a modular blueprint that later PRs can implement one term at a time.

### Secondary but required gaps

1. **High-\(k\) analytic oracle.** Because CAMB’s exposed `T_source` is not a trustworthy high-\(k\) oracle, R5 must derive closed-form analytic test limits.
2. **Master code map.** R6 must link every derived term to file and line ranges, including LoS temperature source, polarization source, \(\Phi/\Psi\) constraints, \(\Pi=\Theta_2-\sqrt6E_2\), PSTF RHS operators, monopole identification, shear coupling, and \(m=\pm2\) family stubs.

---

## R1.6 Questions / Required Clarifications Before R2

R2 can proceed with explicit working assumptions if these are not answered, but these are the questions that should be carried forward:

1. **Which exact \(\Theta_\ell\) normalization should be treated as the final BASS documentation convention?** The code uses `theta0_g`, `theta1_g`, `theta2_g` directly from the packed tower and separately notes CAMB mappings such as \(I_\ell=4\Theta_\ell\). R2 should avoid silently mixing the lowell notation, CAMB \(I_\ell\), and any older bass_rs \((2\ell+1)\Theta_\ell\) convention.

2. **Should R2 cite external papers by exact equation number from direct source verification?** The prompt asks for equation-number citations from Challinor–Lasenby, Seljak–Zaldarriaga, KKS, MB-95, and related references. For an audit-ready derivation, R2 should verify those equation numbers from the papers rather than relying on memory or repo secondary notes.

3. **What is the intended authority relation between `tier_b_source_extraction.py` comments and the P1 briefing on the \(\ell=0\) question?** The extractor comments still label its output as Newtonian-gauge source terms and inherit Round-5 Q-16. R3 should decide whether those comments are correct, partially correct only for \(\ell\ge1\), or need documentation-only correction before any code change is considered.

---

## R1.7 Readiness for R2

R1 is complete. The next cumulative append should be **R2 — FLRW-limit PSTF LoS source derivation**. The R2 deliverable should:

1. derive the FLRW scalar LoS source from PSTF transport,
2. explicitly track normalization and frame conventions,
3. reconcile the result with `build_temperature_source`,
4. explain why the post-P0 low-\(k\) ratios are expected,
5. defer the final \(\ell=0\) convention verdict to R3 where necessary.


---

# R2 — FLRW-Limit PSTF Line-of-Sight Source Derivation

## R2.0 Scope, Conventions, and Immediate Verdict

This round derives the scalar FLRW line-of-sight (LoS) temperature source from the PSTF / 1+3 covariant hierarchy, then compares the result to the current BASS Python implementation. It does **not** settle the \(\ell=0\) gauge/frame convention; that is R3. It also does not propose production-code edits; any code follow-up belongs to R6 and later coding tracks.

**Metric and time convention.** I use the project convention \((- + + +)\), conformal time \(\eta\), scale factor \(a\), and a conformal Newtonian scalar metric written schematically as
\[
 ds^2=a^2(\eta)\left[-(1+2\Psi)d\eta^2+(1-2\Phi)\delta_{ij}dx^idx^j\right].
\]
With this sign convention the ordinary Sachs-Wolfe combination is \(\Theta_0+\Psi\), and the redshift/ISW driver is represented in BASS as \(\dot\Phi+\dot\Psi\). Literature using \(\phi,\psi\), \(\Phi_A,\Phi_H\), or the opposite spatial-potential sign may write the ISW part as \(\dot\Psi-\dot\Phi\); this is a convention translation, not by itself a physical discrepancy.

**PSTF normalization.** BASS stores temperature multipoles \(\Theta_{\ell m}\), not CAMB intensity multipoles \(I_\ell=4\Theta_\ell\). The source extractor confirms this by constructing \(\delta_\gamma=4\Theta_0\), \(v_\gamma=3\Theta_1\), and \(\Pi=\Theta_2-\sqrt6E_2\) from the packed PSTF towers (`htt/bass/spectrum/tier_b_source_extraction.py:225-259`). The LoS projector then consumes the five scalar callables \((\Theta_0,\Psi,\dot\Phi+\dot\Psi,v_b,\Pi)\) (`htt/bass/los/flrw_bessel_projector.py:308-342`).

**Immediate R2 verdict \(R7-corrected\).** The derivation supports the scalar SW/ISW/Doppler/polter structure used by BASS, subject to the R3 monopole-frame audit. The independent R7 audit corrected the earlier R2 over-warning about Doppler and temperature polarization:

1. **Doppler channel:** the canonical unintegrated scalar Doppler kernel is
   \[
   \Delta^T_{\ell,D}(k)=\int d\eta\,g(\eta)\,k v_b(\eta)\,j'_\ell(x),
   \qquad x=k(\eta_0-\eta),
   \]
   with dimensionless peculiar velocity `v_b = theta_b/k`. Since `d j_l(x)/d eta = -k j_l'(x)`, integration by parts gives the `j_l`-only source `(g v_b)'`. Therefore the current BASS source `d(g v_b)/d eta` requires **no** extra `1/k` correction.

2. **Temperature polarization / polter channel:** the collapsed scalar temperature source uses `g Pi/4` on the ordinary `j_l` kernel, with `Pi = Theta_2 - sqrt(6) E_2` in BASS convention. The spin-2 radial projection factor belongs to the separate E-mode source, not to the temperature-side `Pi/4` term.

Therefore R2 now leaves only one formal source-contract issue for R3: whether the `theta0_g` monopole entering `Theta_0 + Psi` is in the frame/gauge compatible with the Bardeen/Newtonian `Psi` reconstructed by the source extractor. This does not invalidate the Round-15 P0 grid result, which primarily validated the quadrature/projector grid by feeding CAMB's assembled `T_source` through `project_temperature_transfer`.


---

## R2.1 PSTF Transport Equation in the FLRW Scalar Limit

The exact energy-integrated PSTF intensity hierarchy used in the project is written in `docs/lowell_bianchi_solver_reference.md:358-393` as
\[
\begin{aligned}
\dot\Pi_{\langle A_\ell\rangle}
&+\frac43\Theta\Pi_{A_\ell}
+\tilde\nabla_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}
+\frac{\ell+1}{2\ell+3}\tilde\nabla^b\Pi_{A_\ell b} \\
&-\frac{(\ell+1)(\ell-2)}{2\ell+3}A^b\Pi_{A_\ell b}
+(\ell+3)A_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}
+\ell\omega^b\eta_{bc\langle a_\ell}\Pi_{A_{\ell-1}\rangle}{}^c \\
&-\frac{(\ell-1)(\ell+1)(\ell+2)}{(2\ell+3)(2\ell+5)}\sigma^{bc}\Pi_{A_\ell bc}
+\frac{5\ell}{2\ell+3}\sigma^b{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b}
-(\ell+2)\sigma_{\langle a_\ell a_{\ell-1}}\Pi_{A_{\ell-2}\rangle}
=K_{A_\ell}.
\end{aligned}
\]
This is the same structural hierarchy that the implementation decomposes into T1–T9 operators (`htt/bass/hierarchy/hierarchy_rhs.py:1-12`, `:343-540`).

For the **FLRW scalar limit** used by R2,
\[
\sigma_{ab}=0,\qquad \omega_a=0,\qquad A_a=0\quad\text{at background order},
\]
and spatial curvature is flat for the current BASS FLRW comparator. The scalar harmonic expansion reduces the PSTF tensors to \(m=0\) coefficients. In the flat scalar mode, the free-streaming part takes the familiar tridiagonal form
\[
\dot\Theta_\ell
+ k\left[\frac{\ell+1}{2\ell+1}\Theta_{\ell+1}
      -\frac{\ell}{2\ell+1}\Theta_{\ell-1}\right]
= C_\ell + G_\ell,
\]
where \(C_\ell\) is the Thomson collision term and \(G_\ell\) is the metric/redshift forcing term. Equivalently, in intensity normalization \(I_\ell=4\Theta_\ell\), the CAMB mapping note quotes the Challinor–Lasenby flat-space scalar harmonic reduction as
\[
\dot I^{(\ell)}_k
-\frac{k}{S}\left[\frac{\ell}{2\ell+1}I^{(\ell-1)}_k
-\frac{\ell+1}{2\ell+1}I^{(\ell+1)}_k\right]
+\frac43\frac{k}{S}A_k\delta_{\ell1}
-\frac{8}{15}\frac{k}{S}\sigma_k\delta_{\ell2}
=-n_e\sigma_T\left[I^{(\ell)}_k-\frac{4}{3}v_k\delta_{\ell1}-\frac{2}{15}\zeta_k\delta_{\ell2}\right]
\]
(`project/04_implementation_specs/...Guide_for_bass_rs.md:131-144`). This is the scalar, Fourier-expanded form of the PSTF transport equation; the apparent CAMB-like variables are just mode coefficients of PSTF tensors, not a change of primary formalism.

The Thomson term relevant for the source sector is also already encoded in the lowell reference:
\[
\left.\frac{D\Theta_\ell^m}{D\eta}\right|_{\rm coll}
=\Gamma_T\left[-\Theta_\ell^m(1-\delta_{\ell0})
+\frac{1}{10}\delta_{\ell2}(\Theta_2^m-\sqrt6E_2^m)
+\delta_{\ell1}\tilde u^m\right],
\]
with \(\Gamma_T=a n_ex_e\sigma_T>0\) and \(\Pi^m=\Theta_2^m-\sqrt6E_2^m\) (`docs/lowell_bianchi_solver_reference.md:554-590`). This is why the scalar visibility source must contain a monopole/SW part, a baryon-velocity/Doppler part, and a quadrupole/polarization part.

---

## R2.2 Integral Solution Before Collapsing Radial Channels

The scalar Boltzmann equation can be written symbolically along the photon ray as
\[
\frac{d}{d\eta}\left(\Theta+\Psi\right)
+\dot\kappa\left(\Theta-\Theta_{\rm coll}\right)
=\dot\Phi+\dot\Psi,
\]
where \(\dot\kappa\) here denotes the positive differential optical-depth rate in the project convention and \(g(\eta)=\dot\kappa e^{-\kappa}\) is positive visibility. After multiplying by the integrating factor \(e^{-\kappa}\) and projecting the plane wave onto radial functions, the observed scalar temperature multipole has the schematic PSTF/TAM form
\[
\Delta_\ell^T(k)=\int_0^{\eta_0}d\eta\,
\Big[
S_0(k,\eta)j_\ell(x)
+S_1(k,\eta)j_\ell^{(1)}(x)
+S_2(k,\eta)j_\ell^{(2)}(x)
\Big],
\qquad x=k(\eta_0-\eta).
\]
Here the physical pieces are
\[
S_0=g(\Theta_0+\Psi)+e^{-\kappa}(\dot\Phi+\dot\Psi),
\qquad S_1=g v_b,
\qquad S_2=gP.
\]
In BASS convention the scalar polarization source collapses to the temperature polter variable
\[
\Pi=\Theta_2-\sqrt6 E_2,
\]
with the temperature contribution \(g\Pi/4\) after the standard scalar LoS reduction.

Hu & White's total-angular-momentum integral solution makes the pre-collapse radial-channel structure explicit: monopole/gravity, velocity, and polarization source terms can be represented on distinct radial functions before integration by parts and basis identities are applied. The BASS FLRW projector, like the usual Seljak--Zaldarriaga / Lewis--Challinor / CAMB source form, uses the already-collapsed scalar source
\[
\boxed{S_T=g(\Theta_0+\Psi+\Pi/4)+e^{-\kappa}(\dot\Phi+\dot\Psi)+(g v_b)'}.
\]
The E-mode branch remains genuinely spin-2 and is projected separately with the \(j_\ell(x)/x^2\)-type factor implemented in `e_mode_projection_factor`.

---

## R2.3 Collapsing to a \(j_\ell\)-Only Source: Integration by Parts

For SW and ISW no radial-channel collapse is needed:
\[
\Delta_{\ell,\rm SW+ISW}^T(k)
=\int d\eta\,
\left[g(\Theta_0+\Psi)+e^{-\kappa}(\dot\Phi+\dot\Psi)\right]j_\ell(x).
\]
This directly maps to the first two scalar terms in BASS:
\[
\texttt{sw\_polter}\supset g(\Theta_0+\Psi),
\qquad
\texttt{isw}=e^{-\kappa}(\dot\Phi+\dot\Psi)
\]
(`htt/bass/los/flrw_bessel_projector.py:447-450`).

For Doppler, start from the canonical radial-kernel form
\[
\Delta_{\ell,D}^T(k)=\int d\eta\,g(\eta)\,k v_b(\eta)\,j_\ell'(x),
\qquad x=k(\eta_0-\eta),
\]
where `v_b` is the dimensionless peculiar velocity \(v_b=\theta_b/k\), and the leading \(k\) comes from the harmonic projection of \(\mathbf v_b\cdot\mathbf n\). Since
\[
\frac{d}{d\eta}j_\ell(x)=-k j_\ell'(x),
\]
we have
\[
\Delta_{\ell,D}^T(k)
=-\int d\eta\,g v_b\frac{d}{d\eta}j_\ell(x)
= -[g v_b j_\ell]_{0}^{\eta_0}
+\int d\eta\,\frac{d}{d\eta}(g v_b)j_\ell(x).
\]
The boundary term vanishes for ordinary visibility support and regular source histories. Therefore the collapsed \(j_\ell\)-only Doppler source is
\[
\boxed{S_{D,j\text{-only}}(\eta,k)=\frac{d}{d\eta}\big[g(\eta)v_b(\eta)\big]}
\]
with **no** extra \(1/k\). This matches `flrw_bessel_projector.py:451-455`. The R5 sharp-Doppler oracle \(\Delta_\ell^D=kV_*j_\ell'(x_*)\) is the direct regression test of this convention.

For the polarization temperature source, the canonical collapsed scalar channel is
\[
\boxed{S_{T,\Pi}=g\Pi/4},
\qquad \Pi=\Theta_2-\sqrt6E_2.
\]
The factor \(1/4\) and the companion E-mode coefficient \(-\sqrt6/4\) are fixed by the Thomson polarization tensor convention used in the BASS mapping. The separate E-mode branch is the one that requires the spin-2 radial projection factor; the temperature-side \(g\Pi/4\) term does not require an additional pre-projection of raw \(\Pi\).

---

## R2.4 Identification of the Four Physical Contributions

With the above qualifications, the FLRW scalar temperature source decomposes as follows.

### 1. Sachs-Wolfe / visibility monopole

\[
S_{\rm SW}=g(\eta)\,[\Theta_0(\eta,k)+\Psi(\eta,k)].
\]
Here \(\Theta_0\) is the photon temperature monopole in the source frame. In BASS it is read from the PSTF tower by `theta0_g = t_tower[:, _slot(0,0)]` (`tier_b_source_extraction.py:225`). The potential \(\Psi\) is a derived Newtonian-gauge/Bardeen-potential callable returned by the source extractor (`tier_b_source_extraction.py:291-318`). The combination \(\Theta_0+\Psi\) is the observable effective temperature at last scattering in the scalar FLRW limit. The remaining open issue is whether the BASS \(\Theta_0\) slot is already in the same gauge/frame as \(\Psi\); that is R3.

### 2. Integrated Sachs-Wolfe / metric redshift

\[
S_{\rm ISW}=e^{-\kappa(\eta)}[\dot\Phi(\eta,k)+\dot\Psi(\eta,k)]
\]
in the BASS potential-sign convention. The extractor constructs \(\Phi\) and \(\Psi\) from density, velocity, and anisotropic-stress constraints, then differentiates \(\Phi+\Psi\) using a fourth-order finite-difference stencil (`tier_b_source_extraction.py:275-306`). The projector multiplies this callable by \(e^{-\kappa}\) (`flrw_bessel_projector.py:449-450`).

### 3. Doppler / baryon velocity

Canonical radial-channel form:
\[
\Delta_{\ell,D}^T=\int d\eta\,g\,k v_b j_\ell'(x),
\]
with dimensionless \(v_b=\theta_b/k\). Collapsed \(j_\ell\)-only form:
\[
S_{D,j\text{-only}}=(g v_b)'.
\]
Current BASS Python code uses exactly this form:
\[
S_{D,\rm code}=(g v_b)'
\]
(`flrw_bessel_projector.py:451-455`). R7 therefore removes the earlier R2 caveat: no missing \(1/k\) is implied by the standard convention.

### 4. Polarization temperature source and E-mode source

BASS defines the PSTF scalar polter combination
\[
\Pi=\Theta_2-\sqrt6E_2
\]
(`tier_b_source_extraction.py:234-236`; `docs/lowell_bianchi_solver_reference.md:554-590`). The Python projector uses
\[
S_{T,\Pi}^{\rm code}=\frac14g\Pi,
\qquad
S_E^{\rm code}=-\frac{\sqrt6}{4}g\Pi
\]
(`flrw_bessel_projector.py:447-472`). R7 accepts this as the canonical scalar temperature/E-mode split under the BASS convention: \(g\Pi/4\) belongs to the temperature \(j_\ell\)-source, while the E branch is projected with the spin-2 factor.

---

## R2.5 Term-by-Term Comparison to Current BASS Implementation

| Physical term | PSTF/LoS result | Current BASS location | R2 status \(R7-corrected\) |
|---|---|---|---|
| Transfer integral | \(\Delta_\ell^T=\int S_Tj_\ell d\eta\) for a \(j_\ell\)-only source | `project_temperature_transfer`, `flrw_bessel_projector.py:499-546` | Correct for any already-assembled \(j_\ell\)-source. Round-15 P0 primarily validated this projector/grid path. |
| SW | \(g(\Theta_0+\Psi)\) | `build_temperature_source`, `:447-449`; source callables from `tier_b_source_extraction.py:313-318` | Structurally correct, pending R3 monopole convention. |
| ISW | \(e^{-\kappa}(\dot\Phi+\dot\Psi)\) in BASS sign convention | `build_temperature_source`, `:449-450`; derivative from `tier_b_source_extraction.py:304-306` | Structurally correct if potential sign convention is documented. |
| Doppler | radial-channel \(g k v_bj'_\ell\), equivalent after IBP to \((g v_b)'j_\ell\) | `build_temperature_source`, `:451-455` | Accepted by R7. No \(1/k\) patch. Add sharp-Doppler regression test. |
| Temperature polarization | collapsed scalar source \(g\Pi j_\ell/4\) | `build_temperature_source`, `:447-449`; raw \(\Pi\) from `tier_b_source_extraction.py:234-236` | Accepted by R7 under the BASS \(\Pi=\Theta_2-\sqrt6E_2\) convention. |
| E-mode source | \(-\sqrt6 g\Pi/4\) projected with spin-2 radial factor | `build_polarization_source`, `:458-472` and `project_polarization_transfer`, `:549-581` | Accepted structurally; keep sharp-polarization regression test. |
| \(\Phi,\Psi\) constraint extraction | Bardeen potentials from total density, momentum, anisotropic stress | `tier_b_source_extraction.py:275-306` | Algebraically plausible; R3 must check monopole/frame coherence, including how \(\delta\rho_\gamma=4\Theta_0\) enters the potential reconstruction. |

This table incorporates the R7 correction: Doppler and temperature polter are no longer unresolved contracts. The only remaining source-assembly contract is the frame/gauge of the \(\ell=0\) monopole entering \(\Theta_0+\Psi\).


---

## R2.6 Gauge / Frame Coherence and the \(\ell\ge1\) Result

In the PSTF covariant approach, anisotropy multipoles that vanish in the exact FRW background are gauge-invariant at first order by the Stewart-Walker logic. Hence \(\Theta_{A_\ell}\), \(E_{A_\ell}\), and \(B_{A_\ell}\) for \(\ell\ge1\) are safe covariant perturbation variables around FRW. This is the conceptual reason the hierarchy can remain PSTF-native while still matching the usual scalar-mode Boltzmann hierarchy in the FLRW limit.

The monopole is different: \(\Theta_0\) is density-like. It does not vanish in the background once interpreted as the fractional photon energy-density perturbation, and its perturbation value is frame/gauge dependent. Therefore R2 can only say:
\[
\Theta_0+\Psi
\]
should be the gauge-coherent observable last-scattering temperature combination, but R3 must prove that the `theta0_g` supplied by BASS is the member of that combination compatible with the derived \(\Psi\).

This is not a small bookkeeping detail. The source extractor explicitly combines a PSTF-tower monopole with Newtonian-gauge potentials reconstructed from constraints (`tier_b_source_extraction.py:225-318`). That may be correct because the constraints are written in a frame-invariant/Bardeen form; but it has to be shown, not assumed.

---

## R2.7 Reduction to MB-95 / CAMB / Lewis-Challinor as an Oracle

In the flat scalar FLRW limit, the PSTF hierarchy reduces to the same free-streaming recursion and Thomson collision structure used by MB-95/CAMB, after simple normalization changes:
\[
I_\ell=4\Theta_\ell,
\qquad
\delta_\gamma=4\Theta_0,
\qquad
v_\gamma=3\Theta_1,
\qquad
\Pi_{\rm BASS}=\Theta_2-\sqrt6E_2
\]
up to the polarization-basis map. The CAMB mapping note states the intensity-mode dictionary directly (`project/04_implementation_specs/...Guide_for_bass_rs.md:145-168`, `:186-204`).

The MB/CAMB line-of-sight source is gauge-invariant after integration even when the pointwise source function is written in a gauge-specific language. This happens because gauge transformations reshuffle terms among \(\Theta_0\), the metric potentials, Doppler, and time-delay/redshift pieces; after integration by parts and boundary cancellation, the final observed \(\Delta_\ell^T\) is invariant. This is the right way to use MB-95 and CAMB here: as FLRW oracles for the gauge-invariant transfer, not as the primary variables for Bianchi.

The R2 consequence for BASS is sharp:

- Passing **CAMB's already assembled `T_source`** through `project_temperature_transfer` tests the Bessel kernel and quadrature.
- It does **not** by itself test the remaining monopole-frame contract in BASS's native `build_temperature_source`, because that contract concerns whether `theta0_g` is the correct emission monopole compatible with reconstructed `Psi`.
- Comparing BASS native sources to CAMB native sources is meaningful only where CAMB's exposed `T_source` is itself a valid oracle. The P1 hand-off states that this is reliable only up to about \(k\lesssim10^{-2}\,\mathrm{Mpc}^{-1}\).

---

## R2.8 Consistency Check Against Round-15 P0 Evidence

The post-D-1 evidence remains important, but it should be interpreted with the above distinction.

1. The P0 grid fix changed the LoS grid from an under-resolved 64-point uniform grid to a recombination-refined and \(k\)-adapted grid. The decisive transcript shows that when CAMB's own `T_source` is passed through the BASS projector, the `k_adapted_eta100` ratios are close to CAMB direct at the valid low-\(k\) cells:
   \[
   (k,\ell)=(10^{-3},2):0.933,
   \quad (10^{-3},3):0.984,
   \quad (10^{-2},2):1.044,
   \quad (10^{-2},3):0.999.
   \]
   These numbers are expected if `project_temperature_transfer` correctly computes \(\int S_Tj_\ell d\eta\) once supplied with a valid source array.

2. The same evidence does not settle the R3 monopole-frame contract, because the decisive test's Step 3 feeds CAMB's assembled `T_source` directly into BASS's projector. It bypasses BASS's native decomposition into \(\Theta_0,\Psi,v_b,\Pi\).

3. The independent R7 audit accepts the standard Doppler and temperature-polter conventions. The remaining reason the P0 evidence is not a full source proof is the \(\ell=0\) monopole convention, not Doppler or polarization radial normalization.

4. The low-\(k\) native agreement, once \(\eta_{init}\) truncation is lifted, supports the idea that the dominant grid pathology is fixed and that the scalar source assembly is close. It is not yet a full formal proof of the monopole-frame contract.

---

## R2.9 R2 Deliverable Verdict

The FLRW PSTF derivation yields the following audit-ready verdict:

1. **Validated in R2:** The BASS projector `project_temperature_transfer` is the correct numerical object for a preassembled scalar \(j_\ell\)-source. The SW and ISW pieces of `build_temperature_source` match the expected scalar LoS structure under BASS's potential-sign convention.

2. **Deferred to R3:** The \(\ell=0\) monopole entering \(\Theta_0+\Psi\) must be audited. R2 cannot certify that a PSTF monopole read from `t_tower[:, slot(0,0)]` is automatically compatible with Newtonian-gauge potentials reconstructed from constraints.

3. **Resolved by R7:** The Doppler and temperature-polter terms match the standard collapsed scalar LoS convention. Doppler is \(g k v_b j_\ell'\) before integration by parts and \((g v_b)'j_\ell\) afterward; the temperature polter is \(g\Pi j_\ell/4\). Add regression tests, but do not patch these formulas.

4. **No production-code change in this round:** R2 only records the formal derivation and the audit findings. Any code-level change, if later confirmed, must preserve the Round-15 D-1 projector resolution independence and all Route-B / super-horizon anchor invariants.

R2 is complete. The next cumulative append should be **R3 — \(\ell=0\) monopole convention audit**.

---

# R3 — \(\ell=0\) Monopole Convention Audit

## R3.0 Scope and Verdict

R3 audits the only scalar variable in the FLRW LoS temperature source that is not protected by the usual Stewart-Walker argument: the photon monopole. The higher PSTF temperature and polarization multipoles vanish in the exact FRW background and are therefore safe first-order gauge-invariant perturbation variables. The monopole, however, is density-like. Since the background photon density is nonzero, the perturbation \(\delta\rho_\gamma/\rho_\gamma=4\Theta_0\) changes under a scalar frame/time-slicing shift.

The result is deliberately conservative.

1. **The old “D-3 gauge fix” formula must not be applied as a direct BASS patch.** The previous session-opener proposal
   \[
   \Theta_{0,N}=\Theta_{0,S}+h_S'/6
   \]
   is not a PSTF-native statement, does not correspond to a variable actually stored in the BASS integrator, and omits the full gauge-generator structure. BASS has no production `h_S`, `h_dot`, `h_prime`, `sync_h`, or metric-trace state in `htt/bass/`. A blind `h_S'/6` patch would therefore be both architecturally wrong and algebraically under-specified.

2. **The R3 prompt's parenthetical “BASS — radiation rest frame, comoving” is not supported by the code.** A radiation rest frame would set the photon dipole to zero by construction. BASS evolves a photon dipole and couples it to baryon/electron velocity through Thomson collision. The code-supported statement is weaker and cleaner: BASS stores a photon brightness monopole in the chosen tetrad/transport frame, with collision/source evaluation intended in the electron frame for the general tilted case.

3. **The source extractor reconstructs Bardeen/Newtonian potentials from a nearly gauge-invariant constraint combination.** The line
   \[
   \Phi \propto \delta\rho_{\rm tot}-3\mathcal H q_{\rm tot}/k
   \]
   in `tier_b_source_extraction.py:280-292` is the correct kind of density-plus-momentum combination for a Bardeen/comoving-density constraint, modulo BASS sign conventions.

4. **The weak link is not \(\Phi\) or \(\Psi\), but the separate \(\Theta_0\) entering \(\Theta_0+\Psi\).** If the tower monopole is already the Newtonian/Bardeen-frame photon temperature perturbation, then the SW part of the source is gauge-coherent. If the tower monopole is instead a CDM-comoving/synchronous-like monopole inherited from the CAMB regular seed, the current source is missing the scalar time-shift correction
   \[
   \Theta_{0,N}=\Theta_{0,{\cal F}}+\mathcal H\alpha_{{\cal F}\to N}.
   \]

5. **R3 cannot certify “no code correction needed.”** It can certify the narrower statement: **no synchronous-metric patch should be made before the variable contract is fixed.** The current documentation/code comments are insufficient to prove that `theta0_g = t_tower[:, slot(0,0)]` is the Newtonian-gauge monopole required by the LoS source. R6 must carry this as an unresolved source-contract issue.

This verdict is consistent with Round-15 P0: the P0 grid evidence proves that the projector is healthy once supplied with a valid source, and the low-\(k\) native agreement suggests there is no remaining order-of-magnitude monopole disaster. It does **not** prove the monopole convention correct at the source-assembly level.

---

## R3.1 Code Trace of the BASS Monopole

### R3.1.1 Seed construction and initial convention

`seed_compatibility.py` exposes a symbolic `RegularSeedState` with `delta_gamma`, `delta_baryon`, `delta_cdm`, `delta_nu`, and a common velocity-like scalar `theta_common`; see `seed_compatibility.py:67-79`. The physically motivated adiabatic branch sets
\[
\delta_\gamma:\delta_b:\delta_c:\delta_\nu=4/3:1:1:4/3,
\qquad
\theta_\gamma=\theta_b=\theta_c=\theta_\nu=0,
\]
and its own comment labels this as a synchronous-gauge super-horizon seed; see `seed_compatibility.py:168-176`.

The integrator configuration repeats the same warning: the flag `adiabatic_mode_seed` only toggles a canonical tracking placeholder, while the actual solver IC is supplied by `make_camb_regular_adiabatic_seed` from the Lowell §13.2 startup prescription; see `integrator.py:136-155`. The FLRW pipeline also states that the physical IC comes from `make_camb_regular_adiabatic_seed`; see `flrw_pipeline.py:133-147`.

**R3 implication.** The available bundle does not include `bass.perturbation.regular_adiabatic_ic.py`, so the actual packed IC cannot be inspected here. But all exposed comments point toward a CAMB/MB regular-mode startup, not an explicitly Newtonian-gauge monopole startup.

### R3.1.2 Packed seed projection

`project_packed_regular_seed` unpacks a CAMB regular adiabatic seed, builds a `RegularSeedState`, applies a constraint projection, and then rescales the photon dipole and neutrino/extra velocity slots by the projection scale; see `seed_compatibility.py:412-478`. The only explicit photon-tower mutation shown is

```python
combined.photon_T.tensors[1].components[1] *= scale
```

at `seed_compatibility.py:452`. There is no corresponding monopole conversion.

**R3 implication.** The seed-projection layer is frame-aware for tilt/velocity consistency, but it does not convert the photon monopole between synchronous/CDM-comoving and Newtonian/Bardeen slicing.

### R3.1.3 Hierarchy evolution

The combined RHS evolves the photon temperature hierarchy by calling `hierarchy_rhs_photon` on `state.photon_T.as_flat()` with Thomson collision auxiliary data; see `integrator.py:391-410`. The hierarchy driver itself is a PSTF multipole engine: its docstring says it evaluates the nine-term hierarchy and returns `dy/dη` in the same packing order; see `hierarchy_rhs.py:542-599`. In the general branch it applies expansion, gradient/divergence, acceleration, vorticity, and shear terms, plus collision; see `hierarchy_rhs.py:472-528`. In the homogeneous/no-gradient fast path, it still applies expansion and, if present, T7/T8/T9 shear couplings; see `hierarchy_rhs.py:421-448`.

There is no synchronous scalar metric variable in this RHS. The grep result over `htt/bass/` returns no production matches for `h_S`, `h_dot`, `h_prime`, `metric_trace`, or `sync_h`.

**R3 implication.** The hierarchy is not a synchronous-gauge Einstein-Boltzmann hierarchy in the MB-95 sense. But absence of synchronous metric variables does not automatically make \(\Theta_0\) Newtonian-gauge. It only means BASS has not stored the gauge generator needed to translate the monopole after the fact.

### R3.1.4 Integrator output

`IntegrationResult` stores `photon_T_tower`, `photon_E_tower`, `neutrino_tower`, baryon/CDM local histories, and diagnostic histories; see `integrator.py:223-255`. The helper `pi_ell_m` reads a packed photon temperature component directly from `photon_T_tower`; see `integrator.py:260-277`.

**R3 implication.** The output schema preserves a brightness tower and local matter histories. It does not preserve enough metric-gauge information to reconstruct a synchronous-to-Newtonian monopole correction of the old `h_S'/6` form.

### R3.1.5 Source extraction and LoS assembly

The FLRW source extractor reads

```python
theta0_g = t_tower[:, _slot(0, 0)]
```

at `tier_b_source_extraction.py:225`. It then sets
\[
\delta_\gamma=4\Theta_{0,\gamma},
\qquad
\delta_\nu=4\Theta_{0,\nu},
\qquad
v_\gamma=3\Theta_{1,\gamma},
\qquad
v_\nu=3\Theta_{1,\nu},
\]
following `tier_b_source_extraction.py:254-259`.

The potential reconstruction uses
\[
\Phi=\frac{4\pi G a^2}{k^2}
\left(\delta\rho_{\rm tot}-3\mathcal H\frac{q_{\rm tot}}{k}\right),
\]
implemented as `delta_rho_tot - 3.0 * calH * mom / k`; see `tier_b_source_extraction.py:275-292`. An anisotropic-stress correction constructs `psi = phi + psi_minus_phi`; see `tier_b_source_extraction.py:293-303`. The returned source bundle then passes the unshifted `theta0_g` and the reconstructed `psi` separately; see `tier_b_source_extraction.py:313-318`.

Finally, the LoS projector forms
\[
S_T\supset g(\Theta_0+\Psi+\Pi/4)
\]
at `flrw_bessel_projector.py:416-455`, specifically lines `:437-448`.

**R3 implication.** The code is gauge-coherent only if the `theta0_g` handed to the source is already the photon monopole in the same Bardeen/Newtonian frame as `psi`, or if the pair has been defined as a single gauge-invariant effective source before reaching `build_temperature_source`. The current code comments do not establish either condition.

---

## R3.2 PSTF-Native Scalar Frame Transformation

The clean way to state the monopole issue is not “synchronous versus Newtonian” at first. It is a frame/time-slicing comparison.

Let \({\cal F}\) be the frame/slicing in which the BASS tower monopole is defined, and let \(N\) denote the scalar Bardeen/Newtonian frame in which the LoS source is conventionally written. Let \(\alpha_{{\cal F}\to N}\) be the first-order scalar time displacement from \({\cal F}\) to \(N\). For any background scalar \(X\), the perturbation changes by the Lie derivative of the background:
\[
\delta X_N=\delta X_{\cal F}-X_0'\,\alpha_{{\cal F}\to N}
\]
up to the sign convention used to define \(\alpha\). In the convention used below, matching the standard MB/CAMB dictionary,
\[
\delta_i^N=\delta_i^{\cal F}+3(1+w_i)\mathcal H\alpha_{{\cal F}\to N},
\]
so for photons
\[
\delta_\gamma^N=\delta_\gamma^{\cal F}+4\mathcal H\alpha_{{\cal F}\to N},
\]
and therefore
\[
\boxed{\Theta_{0,\gamma}^N=\Theta_{0,\gamma}^{\cal F}+\mathcal H\alpha_{{\cal F}\to N}}.
\]

The scalar velocity potential transforms as
\[
v_i^N=v_i^{\cal F}+k\alpha_{{\cal F}\to N},
\]
when \(v_i\equiv\theta_i/k\). Hence the total density-momentum combination
\[
\delta\rho_{\rm com}
\equiv
\delta\rho_{\rm tot}-3\mathcal H\frac{q_{\rm tot}}{k}
\]
is invariant under the same scalar time shift:
\[
\delta\rho_{\rm tot}^N-3\mathcal H\frac{q_{\rm tot}^N}{k}
=\delta\rho_{\rm tot}^{\cal F}-3\mathcal H\frac{q_{\rm tot}^{\cal F}}{k}.
\]
This is precisely why the BASS potential reconstruction can be much safer than the separate SW monopole insertion: the constraint source can be written in a frame-invariant way, while \(\Theta_0\) alone cannot.

The Sachs-Wolfe emission combination transforms as
\[
\Theta_{0,\gamma}^N+\Psi_B
=
\Theta_{0,\gamma}^{\cal F}+\Psi_B+
\mathcal H\alpha_{{\cal F}\to N},
\]
where \(\Psi_B\) denotes the Bardeen/Newtonian potential. Thus a source assembly that uses \(\Psi_B\) but \(\Theta_0^{\cal F}\) is missing a term unless \(\alpha_{{\cal F}\to N}=0\) by construction.

This is the central R3 algebraic result.

---

## R3.3 Relation among BASS/PSTF, MB Newtonian, and MB Synchronous Monopoles

### R3.3.1 MB / CAMB conventions

The CAMB mapping note states that CAMB's `clxg` is the photon fractional density perturbation,
\[
\texttt{clxg}=I_0=\Delta_\gamma=F_{\gamma0}=4\Theta_0,
\]
see `project/04_implementation_specs/...Guide_for_bass_rs.md:13`. It also states that CAMB works in the CDM rest frame, equivalent to synchronous gauge with vanishing CDM velocity; see the same document at `:23-25`.

Let \(S\) denote this CDM-comoving synchronous frame, and \(N\) denote conformal Newtonian/longitudinal gauge. Then
\[
\boxed{\Theta_{0,\gamma}^{N}
=\Theta_{0,\gamma}^{S}+\mathcal H\alpha_{S\to N}}
\]
with
\[
\Theta_{0,\gamma}^{S}=\frac14\texttt{clxg}_{\rm CAMB}.
\]
The same transformation gives
\[
\delta_i^N=\delta_i^S+3(1+w_i)\mathcal H\alpha_{S\to N},
\qquad
v_i^N=v_i^S+k\alpha_{S\to N}.
\]
For CDM-comoving synchronous gauge, \(v_c^S=0\), so in a Newtonian comparison surface one may identify
\[
\alpha_{S\to N}=\frac{v_c^N}{k}
\]
if \(v_c^N\) is available with the same velocity convention.

In MB's metric variables this same scalar generator is commonly represented as
\[
\alpha_{S\to N}=\frac{h_S'+6\eta_S'}{2k^2},
\]
and the Bardeen potentials are written as
\[
\Psi_B=\alpha'+\mathcal H\alpha,
\qquad
\Phi_B=\eta_S-\mathcal H\alpha
\]
modulo notation/sign conventions for \(\Phi\) and \(\Psi\). These formulas are useful as an oracle dictionary only. They are not BASS runtime variables and should not be made primary in a tetrad/PSTF implementation.

### R3.3.2 BASS/PSTF monopole

The code-supported definition is
\[
\Theta_{0,\gamma}^{\rm BASS}
\equiv
\texttt{photon\_T\_tower[:, slot(0,0)]}.
\]
The formal meaning depends on the perturbative frame contract:

- If the tower is defined on the scalar frame \({\cal F}=N\), then
  \[
  \Theta_{0,\gamma}^{\rm BASS}=\Theta_{0,\gamma}^N,
  \]
  and the SW source \(g(\Theta_0+\Psi_B)\) is conventionally coherent.

- If the tower is defined on a CDM-comoving/synchronous-like frame \({\cal F}=S\), suggested by the CAMB regular seed comments, then
  \[
  \Theta_{0,\gamma}^{\rm BASS}=\Theta_{0,\gamma}^S,
  \]
  and the LoS source requires
  \[
  \Theta_{0,\gamma}^{\rm source}
  =\Theta_{0,\gamma}^{\rm BASS}+\mathcal H\alpha_{S\to N}.
  \]

- If the tower is intended as a covariant density-gradient variable rather than a local density perturbation, then `theta0_g` is misnamed for LoS use: the LoS source needs a local emission-temperature perturbation, not only a comoving-gradient amplitude. The current code treats it as a local monopole by setting \(\delta_\gamma=4\Theta_0\), so this third interpretation is not what the implementation currently does.

The present bundle does not prove which of the first two alternatives is enforced. It only shows that the old synchronous-metric patch is not directly available.

---

## R3.4 Does BASS Need a Correction to the \(\Theta_0\) Source Term?

### R3.4.1 Algebraic condition for no correction

No correction is needed if and only if the following source contract is true:

\[
\boxed{
\texttt{sources.theta\_0}(\eta)
=\Theta_{0,\gamma}^{N}(\eta,k)
\quad\text{or an exactly equivalent Bardeen-frame emission monopole.}
}
\]

Under this contract, `sources.psi` is \(\Psi_B\), and `build_temperature_source` correctly forms the Newtonian-gauge SW source
\[
S_{\rm SW}=g(\Theta_{0,\gamma}^N+\Psi_B).
\]

### R3.4.2 Algebraic condition for a required correction

If the tower monopole is instead defined in a frame \({\cal F}\neq N\), the required source-level correction is
\[
\boxed{
\Theta_{0,\gamma}^{\rm source}
=\Theta_{0,\gamma}^{\rm tower}
+\mathcal H\alpha_{{\cal F}\to N}.
}
\]

For a CDM-comoving/synchronous-like tower,
\[
\Theta_{0,\gamma}^{\rm source}
=\Theta_{0,\gamma}^{S}
+\mathcal H\alpha_{S\to N}.
\]
This is the proper form of the correction, not `h_S'/6`.

### R3.4.3 Why the old `h_S'/6` proposal is not acceptable

The old proposal is unacceptable for four independent reasons.

1. BASS does not store \(h_S\) or \(h_S'\) in `IntegrationResult`; see `integrator.py:223-255`.
2. The PSTF/tetrad architecture is meant to survive Bianchi II-IX, where a global synchronous-gauge scalar metric dictionary is not the right primary language.
3. The actual scalar generator is \(\alpha\), not \(h_S'\) alone. In the MB dictionary, \(\alpha\) involves \(h_S'+6\eta_S'\), not just \(h_S'\).
4. The correction to a temperature monopole is \(\mathcal H\alpha\), with dimensions and time-dependence fixed by the radiation background, not a bare metric derivative term.

### R3.4.4 Current R3 verdict on code change

R3 does **not** recommend an immediate production-code change. It recommends a source-contract decision:

- If the team declares and verifies that `photon_T_tower[:, slot(0,0)]` is already \(\Theta_0^N\), then no code correction is needed; only the documentation should state this explicitly and add a regression test.
- If the team declares that the tower is CAMB/CDM-comoving/synchronous-like, then `tier_b_source_extraction.py` needs a correction of the form \(\Theta_0\mapsto\Theta_0+\mathcal H\alpha\), but \(\alpha\) must be obtained from a PSTF-native scalar diagnostic, not by adding an `h_S'` state to the tetrad hierarchy. Two viable routes are: (i) carry forward the seed/common-velocity scalar `theta_common` from `seed_compatibility.py:67-79` and identify \(\alpha=\theta_{\rm common}/k\) only after its frame semantics are declared; or (ii) reconstruct \(\alpha\) from a tetrad-state local expansion perturbation \(\delta\Theta\), if such a history is exposed. Neither route is currently wired through `IntegrationResult`, so this is the actual R3 blocker.
- If the team cannot declare either, then the current implementation remains formally under-specified even if numerically close in the tested low-\(k\) cells.

---

## R3.5 Reconciliation with Round-15 P0 Empirical Evidence

The low-\(k\) Round-15 P0 numbers remain encouraging:
\[
(k,\ell)=(10^{-3},2):0.933,
\quad
(10^{-3},3):0.984,
\quad
(10^{-2},2):1.044,
\quad
(10^{-2},3):0.999
\]
for the `k_adapted_eta100` comparison reported in the P1 hand-off and P0 transcript.

R3 reconciles these data as follows.

1. **The projector/grid result is real.** The dominant D-1 quadrature defect was removed. The projector can integrate a valid scalar source over a valid LoS grid.

2. **The decisive projector test bypasses native source assembly.** When CAMB's exposed `T_source` is passed through the BASS projector, the test checks the quadrature and Bessel kernel, not the internal `theta0 + psi + pi/4 + doppler` decomposition.

3. **A monopole mismatch can be numerically subdominant in the tested regime.** At low \(k\), the correction \(\mathcal H\alpha\) may be partly degenerate with the constraint-reconstructed potential and with the remaining D-2 lower-bound truncation. The observed few-percent agreement is evidence against a catastrophic mismatch, not evidence for a completed convention proof.

4. **The source extractor may already be using a partially gauge-invariant route for potentials.** Since `phi` is reconstructed from a density-plus-momentum combination, the metric side of the SW term is likely much safer than the old Round-12/14 diagnosis assumed. This explains why the earlier “synchronous/Newtonian mismatch” diagnosis was too crude.

5. **High-\(k\) residuals cannot settle R3.** The P1 hand-off already states that CAMB's exposed `T_source` is not a trustworthy high-\(k\) oracle. Therefore high-\(k\) disagreement cannot be used to infer a unique monopole-gauge correction.

Thus the empirical evidence supports the following limited statement:

\[
\text{BASS is numerically close enough that the source contract is probably not wildly wrong,}
\]

but it does not support the stronger statement:

\[
\text{the \(\ell=0\) PSTF monopole convention has been formally certified.}
\]

---

## R3.6 Minimal Tests and Documentation Follow-Up

R3 proposes the following documentation/test targets for R6 and the later coding track. These are not production-code edits in R3.

### Test 1 — Synthetic scalar time-shift invariance of the constraint potential

Construct toy histories \(\delta_i(\eta)\), \(v_i(\eta)\), and an arbitrary scalar shift \(\alpha(\eta)\). Apply
\[
\delta_i\mapsto\delta_i+3(1+w_i)\mathcal H\alpha,
\qquad
v_i\mapsto v_i+k\alpha.
\]
Then verify that the code-level constraint combination
\[
\delta\rho_{\rm tot}-3\mathcal H q_{\rm tot}/k
\]
is invariant to numerical tolerance. This would validate the potential side of `tier_b_source_extraction.py:275-292` as a gauge-coherent Bardeen/comoving-density reconstruction.

### Test 2 — Synthetic scalar time-shift non-invariance of raw \(\Theta_0+\Psi\)

Using the same toy shift, verify that
\[
\Theta_0+\Psi_B
\]
changes by \(-\mathcal H\alpha\) or \(+\mathcal H\alpha\), depending on the chosen shift sign, unless the monopole is shifted consistently. This test should fail intentionally for an uncorrected non-Newtonian monopole and pass when the corrected
\[
\Theta_0^{\rm source}=\Theta_0^{\rm tower}+\mathcal H\alpha
\]
is used.

### Test 3 — Runtime source-contract diagnostic

For a low-\(k\) adiabatic run, compare three source constructions:

1. current `theta0_g + psi`,
2. explicitly Newtonian-transformed `theta0_g + calH * alpha + psi`, if \(\alpha\) can be inferred from a trusted velocity/shear diagnostic,
3. CAMB-exposed `T_source` in the low-\(k\) validity regime only.

The goal is not to tune BASS to CAMB. The goal is to identify whether the tower monopole behaves like \(\Theta_0^N\) or \(\Theta_0^S\) under a controlled convention comparison.

### Documentation correction

Add a source-contract paragraph to `tier_b_source_extraction.py` and `docs/V5_ROUND15_P1_PSTF_DERIVATION.md` stating:

> The LoS source requires a Bardeen/Newtonian-frame photon emission monopole, or an explicitly gauge-invariant emission-temperature combination. A raw PSTF \(\ell=0\) tower slot is acceptable only after the frame contract has identified it with that quantity. Higher multipoles do not share this ambiguity at first order around FRW.

---

## R3.7 R3 Verdict Table

| Question | R3 answer |
|---|---|
| Is \(\ell\ge1\) direct PSTF/MB identification safe around FRW? | Yes, at first order, because the anisotropy multipoles vanish in the FRW background. |
| Is \(\ell=0\) direct identification safe? | No. The monopole is density-like and frame/gauge dependent. |
| Is BASS's tower clearly in the radiation rest frame? | No. The code evolves a photon dipole and uses baryon/electron velocity; the tower is better described as a tetrad-frame brightness expansion. |
| Does BASS store the old synchronous metric variable needed for `h_S'/6`? | No. `IntegrationResult` has no such field, and production grep finds none. |
| Are the reconstructed potentials necessarily gauge-mixed? | Not necessarily. The density-plus-momentum constraint combination is the correct kind of Bardeen/comoving invariant. |
| Is `theta0_g + psi` formally certified? | Not yet. It is certified only if `theta0_g` is declared and verified to be \(\Theta_0^N\) or an equivalent gauge-invariant emission monopole. |
| Is an immediate code patch recommended? | No. First fix the source contract and add a diagnostic. If the tower is confirmed synchronous-like, apply \(\Theta_0\mapsto\Theta_0+\mathcal H\alpha\), not `h_S'/6`. |
| How should R6 classify this? | As a **source-contract issue**, not as a proven production bug and not as a solved no-op. |

---

## R3.8 Readiness for R4

R3 leaves the document in the following state for R4.

1. The FLRW SW/ISW projector structure is usable once the source variables are supplied in a coherent frame.
2. The \(\ell=0\) monopole remains the only scalar brightness multipole with a gauge/frame ambiguity.
3. The old synchronous-gauge patch path is rejected as the primary architecture.
4. The Bianchi extension must avoid carrying Newtonian/synchronous gauge language as primary. It should instead state source terms in tetrad-frame variables and, where a scalar FLRW comparison is needed, introduce the frame-displacement \(\alpha_{{\cal F}\to N}\) only as a comparison map.
5. R4 should therefore build the Bianchi blueprint around the normal/electron frame split, shear transport, \(m=\pm2\) recoupling, tilted source evaluation, and MES translation — not around a gauge-fixed scalar metric dictionary.

R3 is complete. The next cumulative append should be **R4 — Bianchi tetrad-frame extension blueprint**.

# R4 — Bianchi Tetrad-Frame Extension Blueprint

## R4.0 Scope and Verdict

R4 extends the R2/R3 FLRW result to the Bianchi track. It does **not** complete a type-by-type derivation for Bianchi II--IX. It gives the structure that a later coding agent can instantiate one Bianchi family at a time.

The verdict is:

1. **The Bianchi observable problem is a tetrad/matrix-propagator problem, not a Newtonian/synchronous gauge problem.** The scalar FLRW form
   \[
   \Delta_\ell^T(k)=\int d\eta\,S_T(\eta,k)j_\ell[k(\eta_0-\eta)]
   \]
   is only the isotropic reduction. In Bianchi, the state is
   \[
   \mathbf X=\{\Theta_{\ell m},E_{\ell m},B_{\ell m}\}_{\ell\le L},
   \]
   and the formal solution is a path-ordered propagator,
   \[
   \mathbf X(\eta_0)=\mathcal U_B(\eta_0,\eta_i)\mathbf X(\eta_i)
   +\int_{\eta_i}^{\eta_0}d\eta\,\mathcal U_B(\eta_0,\eta)\mathbf S(\eta),
   \]
   with
   \[
   \mathcal U_B(\eta_2,\eta_1)=
   \mathcal P\exp\!\int_{\eta_1}^{\eta_2}d\eta\,(\mathsf L_B+\mathsf C_T).
   \]

2. **The current code already has the correct shear-hierarchy call sites.** `hierarchy_rhs.py` samples proper-time \(\sigma_{ab}\), converts from stored conformal shear, and activates T7/T8/T9 when shear is nonzero. But the bundle does not include `packed_operators.py`, so R4 can audit the call-site architecture, not the packed-basis algebra.

3. **The \(m=\pm2\) channels are dynamically essential except in restricted aligned axisymmetry.** A shear or anisotropic-curvature STF tensor is rank 2. Its \(M=\pm2\) components recouple the \(m\)-sectors. The current FLRW source extractor reads only `slot(ell,0)` and is not a general Bianchi observable extractor. The restricted exception is axisymmetric Bianchi I with the tetrad aligned to the symmetry axis, where only \(M=0\) is active and an \(m=0\) extractor can remain sufficient.

4. **Tilt is a frame contract, not one extra Doppler term.** Transport can remain in the normal frame \(n^a\), but collision/source/visibility must be computed in the electron frame \(u_e^a\), then mapped back to the transport frame.

5. **MES and \(x_C\) are downstream compressions.** The solver should first produce direction-resolved \(a_{\ell m}^{T,E,B}\), spectra, or maps. Only then should those outputs be compressed into MES bounds or
   \[
   x_C=\Sigma_{\rm std}^2-W_{\rm std}^2+\Omega_{\rm tilt}+\Omega_{k,{\rm aniso}}.
   \]

---

## R4.1 Tetrad Architecture: from FLRW Kernels to Bianchi Propagators

The core rule from `lowell_bianchi_solver_reference.md:51-62` is

\[
\boxed{\text{transport in }n^a,\qquad \text{collision/source/visibility in }u_e^a.}
\]

For a photon,
\[
K^a=E(n^a+p^a),\qquad p^ap_a=1,\qquad p^an_a=0,
\]
and the Bianchi comoving energy \(\epsilon=Ee^\alpha\) obeys
\[
\epsilon'=-\epsilon\,\Sigma_{ij}p^ip^j.
\]
Thus, unlike FLRW, the **background itself** redshifts photons direction-dependently.

The exact angular transport has the schematic form
\[
\left[
\partial_\eta+\theta'\partial_\theta+\phi'\partial_\phi
-\Sigma_{ij}p^ip^j\partial_{\ln E}
\right]I=\mathcal C_I,
\]
with the spin-transport analogue for \(Q\pm iU\), including basis rotation. Harmonic/PSTF expansion gives
\[
\mathbf X'=\mathsf L_B[n]\mathbf X+\mathsf C_T[u_e]\mathbf X+\mathbf S_{\rm pert}[u_e].
\]

The FLRW Bessel projector is recovered only if

1. \(\sigma_{ab}=0\), \({}^{(3)}S_{ab}=0\), \(A_a=\omega_a=0\);
2. scalar/vector/tensor sectors decouple;
3. the source can be written using known radial functions \(j_\ell^{(s)}\);
4. the R3 source-frame contract supplies the correct emission monopole; the Doppler and temperature-polter radial conventions follow the standard collapsed scalar FLRW source.

Therefore a Bianchi LoS module should not call the scalar `project_temperature_transfer(... * j_l)` as its primary engine. The correct object is a coupled propagator over \((\ell,m,T/E/B)\).

---

## R4.2 Orthogonal Bianchi and the T7/T8/T9 Shear Terms

For energy-integrated brightness multipoles \(\Pi_{A_\ell}\), the 1+3 hierarchy reproduced in `lowell_bianchi_solver_reference.md:360-378` is

\[
\dot\Pi_{\langle A_\ell\rangle}
+\frac43\Theta\Pi_{A_\ell}
+\widetilde\nabla_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}
+\frac{\ell+1}{2\ell+3}\widetilde\nabla^b\Pi_{A_\ell b}
\]
\[
-\frac{(\ell+1)(\ell-2)}{2\ell+3}A^b\Pi_{A_\ell b}
+(\ell+3)A_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}
+\ell\omega^b\eta_{bc\langle a_\ell}\Pi_{A_{\ell-1}\rangle}{}^c
\]
\[
-\frac{(\ell-1)(\ell+1)(\ell+2)}{(2\ell+3)(2\ell+5)}
\sigma^{bc}\Pi_{A_\ell bc}
+\frac{5\ell}{2\ell+3}\sigma^b{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b}
-(\ell+2)\sigma_{\langle a_\ell a_{\ell-1}}\Pi_{A_{\ell-2}\rangle}
=K_{A_\ell}.
\]

In the orthogonal first pass,
\[
A_a=0,\qquad \omega_a=0,
\]
so the non-FLRW transport corrections are the three shear terms:

\[
T7_{A_\ell}
=-\frac{(\ell-1)(\ell+1)(\ell+2)}{(2\ell+3)(2\ell+5)}
\sigma^{bc}\Pi_{A_\ell bc},
\]
\[
T8_{A_\ell}
=\frac{5\ell}{2\ell+3}\sigma^b{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b},
\]
\[
T9_{A_\ell}
=-(\ell+2)\sigma_{\langle a_\ell a_{\ell-1}}\Pi_{A_{\ell-2}\rangle}.
\]

The code convention is that `hierarchy_rhs.py` builds `sum_T` and returns
\[
\Pi'_{A_\ell}=a(K_{A_\ell}-\sum_iT_i{}_{A_\ell}).
\]
So the formulas above are left-hand-side hierarchy terms; their conformal-time RHS signs follow from `a * (K - sum_T)`.

For \(\ell=2\),
\[
\dot\Pi_{\langle ab\rangle}
+\frac43\Theta\Pi_{ab}
+\widetilde\nabla_{\langle a}\Pi_{b\rangle}
+\frac37\widetilde\nabla^c\Pi_{abc}
-\frac4{21}\sigma^{cd}\Pi_{abcd}
+\frac{10}{7}\sigma^c{}_{\langle a}\Pi_{b\rangle c}
-4\sigma_{ab}\Pi
=K_{ab}.
\]
The term \(-4\sigma_{ab}\Pi\) on the left means that the isotropic monopole injects a quadrupole when moved to the RHS. This also shows why \(L=2\) is not a self-contained Bianchi truncation: the same equation couples to \(\Pi_{abcd}\) through T7. A minimally honest low-\(\ell\) Bianchi tower needs at least \(L=4\), with \(L=6\) or \(L=8\) as convergence checks.

### Bianchi-I specialization

For Bianchi I,
\[
{}^{(3)}S_{ab}=0,\qquad C^i{}_{jk}=0,\qquad A_a=\omega_a=0,\qquad \sigma_{ab}\neq0.
\]
Therefore spatial-curvature routing is inactive and T7/T8/T9 carry the anisotropic transport. However, “Bianchi-I is \(m=0\)-only” is true only in an axisymmetric/aligned reduction. For axisymmetric Bianchi I with the tetrad aligned to the symmetry axis, \(m=\pm2\) channels are identically zero and the scalar \(m=0\) extractor is sufficient. For non-axisymmetric or rotated Bianchi I, general tilted Bianchi I, and Bianchi II--IX, the \(m=\pm2\) channels are non-optional.

---

## R4.3 \(m=\pm2\) Recoupling

Expand shear and anisotropic spatial curvature as rank-2 objects:
\[
\sigma_{ab}(\eta)=\sum_{M=-2}^{2}\sigma_{2M}(\eta)Y^{2M}_{ab},
\qquad
{}^{(3)}S_{ab}(\eta)=\sum_{M=-2}^{2}S_{2M}(\eta)Y^{2M}_{ab}.
\]

The schematic shear part of the harmonic hierarchy is
\[
\Pi'_{\ell m}\supset
-a\sum_{M=-2}^{2}\sigma_{2M}
\left[
C^{(7)}_{\ell mM}\Pi_{\ell+2,m-M}
+C^{(8)}_{\ell mM}\Pi_{\ell,m-M}
+C^{(9)}_{\ell mM}\Pi_{\ell-2,m-M}
\right],
\]
where \(C^{(i)}\) are PSTF/Wigner recoupling coefficients. In angular-momentum notation,
\[
C^{(i)}_{\ell mM}\propto
\langle \ell',m-M;2,M\mid \ell,m\rangle\,\mathcal N_\ell^{(i)},
\]
with \(\ell'=\ell+2,\ell,\ell-2\) for T7/T8/T9.

The selection rule is
\[
\boxed{m=m_{\rm rad}+M.}
\]

Consequences:

1. If only \(\sigma_{20}\) is nonzero, each \(m\)-sector evolves independently.
2. If \(\sigma_{2,\pm1}\) or \(\sigma_{2,\pm2}\) is nonzero, scalar \(m=0\) data leak into vector/tensor-like sky channels.
3. Anisotropic curvature \(S_{2M}\) supplies another rank-2 recoupling channel for Bianchi II--IX.
4. Temperature, E, and B cannot be extracted from scalar \(m=0\) slots alone.

The correct Bianchi temperature transfer should be written schematically as
\[
\Delta_{\ell m}^{T}(k)
=\sum_{\lambda'}\int d\eta\,
\mathcal G^{T}_{\ell m;\lambda'}(\eta_0,\eta;k)S_{\lambda'}(\eta,k),
\]
where \(\lambda'=(\ell',m',T/E/B)\). For the lowest tensor-like channels,
\[
\Delta_{\ell,\pm2}^{T}(k)
=\int d\eta\,
\mathcal G^{TT}_{\ell,\pm2;2,\pm2}
\left[
\frac14\tilde g\,\tilde\Pi^{\pm2}
+S_{\rm redshift}^{\pm2}
+S_{\rm shear}^{\pm2}
\right]
+\text{couplings from other }\lambda'.
\]
Here
\[
\tilde\Pi^m=\tilde\Theta_2^m-\sqrt6\,\tilde E_2^m
\]
is the electron-frame quadrupole source.

For polarization,
\[
\Delta_{\ell m}^{E/B}
=\sum_{m'}\int d\eta\,
\mathcal G^{E/B,P}_{\ell m;2m'}
\left[-\frac{\sqrt6}{4}\tilde g\,\tilde\Pi^{m'}\right]
+\text{basis-rotation terms}.
\]
The basis-rotation terms are where Bianchi transport can generate \(E\leftrightarrow B\) mixing.

---

## R4.4 Tilted Observer and Electron-Frame Source Evaluation

Let
\[
u_e^a=\gamma_e(n^a+v_e^a),
\qquad \gamma_e=(1-v_e^2)^{-1/2}.
\]
The correct tilted-source workflow is

\[
\boxed{
n^a\text{-frame transport variables}
\xrightarrow{\mathcal B_{n\to e}}
u_e^a\text{-frame collision/source variables}
\xrightarrow{\mathcal C_T,\tilde g}
u_e^a\text{-frame source}
\xrightarrow{\mathcal B_{e\to n}}
n^a\text{-frame source}.}
\]

The visibility becomes direction-dependent. With the sign convention already used in `lowell_bianchi_solver_reference.md:730-747`,
\[
\tilde\Gamma_T(\eta,e)
=a\tilde n_e x_e\sigma_T\gamma_e(1+v_e\cdot e),
\]
\[
\tilde\kappa(\eta,e)=\int_\eta^{\eta_0}d\eta'\,\tilde\Gamma_T(\eta',e),
\qquad
\tilde g(\eta,e)=\tilde\Gamma_T(\eta,e)e^{-\tilde\kappa(\eta,e)}.
\]

The source is not simply \(g\Pi\), but
\[
\tilde g(\eta,\tilde e)\tilde\zeta_{ab}(\eta,\tilde e)\tilde e^a\tilde e^b,
\qquad
\tilde\zeta_{ab}=\frac34\tilde I_{ab}+\frac92\tilde E_{ab},
\]
projected back into the normal tetrad harmonics.

For small tilt,
\[
\tilde\Theta_{\ell m}
=\Theta_{\ell m}
+\sum_{\ell'm'}B^\Theta_{\ell m;\ell'm'}[v_e]\Theta_{\ell'm'}
+D^\Theta_{\ell m}[v_e]+O(v_e^2).
\]
R4 intentionally does not freeze the standalone sign of the kinematic dipole term here; the sign must be implemented together with the same photon-direction convention used in \(\tilde\Gamma_T\).

The covariant redshift source remains a normal-frame transport term:
\[
\frac{d}{d\eta}\delta\ln\epsilon
=-\left[
\frac13\delta\Theta+\delta A_ap^a+\delta\sigma_{ab}p^ap^b
\right]_{\rm along\ exact\ Bianchi\ ray}.
\]
Tilt therefore modifies the source/collision/visibility frame; it does not replace the Bianchi redshift operator.

---

## R4.5 MES and \(x_C\) Translation

The MES framework connects low-\(\ell\) covariant temperature multipoles to kinematic quantities. The local MES note gives, at leading almost-FLRW order,
\[
\tau_{ab}
=-\frac12\frac{\sigma_{ab}}{\Theta}
+\frac{1}{6\Theta^2}E_{ab}
-\frac{\kappa_G}{6\Theta^2}\pi_{ab}
+O(\epsilon^2),
\]
\[
\tau_a=\frac{1}{3\Theta}\left(\dot u_a-D_a\ln T_0\right)+O(\epsilon^2),
\]
and conservative bounds
\[
\frac{\sigma}{\Theta}\lesssim2\epsilon_2,\qquad
\frac{\omega}{\Theta}\lesssim\sqrt3\,\epsilon_2,\qquad
\frac{\dot u}{\Theta}\lesssim\max(3\epsilon_1^{\rm res},2\epsilon_2,\epsilon_3).
\]

The forward-model chain should be

\[
(\alpha,\beta_{ab},\Sigma_{ab},{}^{(3)}S_{ab},C^i{}_{jk},v_e^a)
\to
(\mathcal U_B,\mathbf S)
\to
\{a_{\ell m}^{T,E,B}\}
\to
\{C_\ell,\epsilon_\ell,\tau_{A_\ell}\}
\to
\{\sigma/\Theta,\omega/\Theta,\dot u/\Theta,\ldots\}.
\]

Only after that should the result be compressed into
\[
x_C=\Sigma_{\rm std}^2-W_{\rm std}^2+\Omega_{\rm tilt}+\Omega_{k,{\rm aniso}}.
\]

A provisional normalization is
\[
\Sigma_{\rm std}^2=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},
\qquad
W_{\rm std}^2=\frac{\omega_a\omega^a}{H^2},
\qquad
\Omega_{\rm tilt}\simeq\sinh^2\beta\simeq v_{\rm tilt}^2
\quad(\beta\ll1),
\]
while \(\Omega_{k,{\rm aniso}}\) should be fixed by a project-level SSoT from the STF spatial-curvature norm, e.g.
\[
\Omega_{k,{\rm aniso}}\propto
\frac{{}^{(3)}S_{ab}{}^{(3)}S^{ab}}{H^4}.
\]

R4 warning: \(x_C\) is not invertible. Equal \(x_C\) can hide different shear orientations, curvature handedness, tilt directions, and \(E/B\)-mixing histories. It is a summary statistic, not an observable generator.

---

## R4.6 Code-Mapping Tables

### R4.6.1 Tetrad transport and shear

| Formalism term | BASS file : line range | Status | Notes |
|---|---:|---|---|
| Normal/electron frame split | `docs/lowell_bianchi_solver_reference.md:51-62` | Documented | Should become a typed runtime source contract. |
| Exact photon redshift \(\epsilon'=-\epsilon\Sigma_{ij}p^ip^j\) | `docs/lowell_bianchi_solver_reference.md:233-265` | Documented | Needs production Bianchi ray/LoS implementation. |
| Bianchi matrix LoS form | `docs/lowell_bianchi_solver_reference.md:430-460` | Documented | Replaces scalar \(j_\ell\)-only LoS. |
| Covariant redshift perturbation source | `docs/lowell_bianchi_solver_reference.md:464-502` | Documented | Not present in the FLRW scalar source extractor. |
| Proper shear sampling | `htt/bass/hierarchy/hierarchy_rhs.py:127-177` | Implemented | Converts conformal shear to proper-time shear. |
| Anisotropic spatial-Ricci routing | `htt/bass/hierarchy/hierarchy_rhs.py:14-31`, `:212-260` | Partial hook | Depends on tetrad-state producer not included here. |
| Photon RHS driver | `htt/bass/hierarchy/hierarchy_rhs.py:343-540` | Implemented skeleton | Sums T1--T9 and collision. |
| T7/T8/T9 call sites | `htt/bass/hierarchy/hierarchy_rhs.py:437-446`, `:510-514` | Implemented call sites | Operator definitions absent from bundle; packed algebra not audited. |
| Integrator tower support | `htt/bass/hierarchy/integrator.py:223-253` | Partial | Stores T/E/B towers and by-mode labels. |

### R4.6.2 Observable extraction

| Formalism term | BASS file : line range | Status | Notes |
|---|---:|---|---|
| FLRW scalar source assembly | `htt/bass/los/flrw_bessel_projector.py:416-455` | Implemented, R2/R3 caveats | FLRW-only scalar reduction. |
| FLRW \(j_\ell\) projector | `htt/bass/los/flrw_bessel_projector.py:499-546` | Implemented | Not the full Bianchi projector. |
| FLRW E-mode projector | `htt/bass/los/flrw_bessel_projector.py:549-580` | Implemented | Bianchi requires E/B matrix propagation. |
| \(\Pi=\Theta_2-\sqrt6E_2\) readout | `htt/bass/spectrum/tier_b_source_extraction.py:225-237` | Implemented for \(m=0\) | Needs all-\(m\) generalization. |
| FLRW scalar potentials | `htt/bass/spectrum/tier_b_source_extraction.py:275-302` | FLRW oracle path | Should not become Bianchi primary. |
| Current scalar-only extraction | `htt/bass/spectrum/tier_b_source_extraction.py:225-259` | FLRW-only | Design limitation for Bianchi, not an FLRW bug. |
| `htt/bass/los/families/*` | Not included in hand-off bundle | Lookup-required / TODO | Briefing mentions stubs, but the zip did not include them. |

### R4.6.3 Tilt and MES

| Formalism term | BASS file : line range | Status | Notes |
|---|---:|---|---|
| Tilted visibility | `docs/lowell_bianchi_solver_reference.md:730-747` | Documented | No implementation visible in this bundle. |
| Orthogonal vs tilted distinction | `docs/lowell_bianchi_solver_reference.md:759-783` | Documented | Correctly frames tilt as source/collision/visibility-wide. |
| Minimal low-\(\ell\) evolution equation | `docs/lowell_bianchi_solver_reference.md:1018-1059` | Documented | Good SSoT for coding follow-up. |
| MES multipole-to-kinematic relations | `project/03_physics_notes/tomographic_MES_framework.md:47-80` | Documented | Downstream of forward observables. |
| \(x_C\) target identity | `docs/V5_ROUND15_P1_EXTERNAL_LLM_BRIEFING.md §1, §4.3` | Documented target | Needs one SSoT normalization for \(\Omega_{k,{\rm aniso}}\). |

---

## R4.7 Follow-Up Coding Consequences

R4 does not authorize production-code edits. It identifies later targets:

1. Do not add synchronous-gauge metric variables to make Bianchi work.
2. Generalize scalar `slot(ell,0)` extraction to all \((\ell,m)\).
3. Audit packed T7/T8/T9 operator definitions before claiming Bianchi readiness.
4. Implement Bianchi LoS as a matrix propagator or exact angular/ray transport module.
5. Add typed frame metadata to every source object: \(n^a\), \(u_e^a\), Newtonian/Bardeen comparison, or CAMB diagnostic.
6. Implement tilt as boost + visibility + collision/source subsystem.
7. Keep MES and \(x_C\) downstream of direction-resolved observables.

---

## R4.8 R4 Verdict Table

| Question | R4 answer |
|---|---|
| Can Bianchi II--IX be handled by a scalar Newtonian/synchronous source dictionary? | No. The primary structure must be tetrad/PSTF matrix propagation. |
| Are T7/T8/T9 the correct shear operators? | Yes at hierarchy/call-site level; packed operator algebra remains unaudited in this bundle. |
| Is Bianchi-I necessarily \(m=0\)-only? | No. Only restricted axisymmetric/aligned reductions are \(m=0\)-only. |
| What generates \(m=\pm2\)? | Rank-2 shear/curvature recoupling, basis rotation, and tilted source boosts. |
| Does the current FLRW extractor support Bianchi observables? | Only in the restricted FLRW / axisymmetric-aligned \(m=0\) cases. General Bianchi observables require all-\(m\) extraction and matrix propagation. |
| How should tilt enter? | Through electron-frame boost, direction-dependent visibility, collision/source tensor, then map back to \(n^a\). |
| How does this connect to MES/\(x_C\)? | MES and \(x_C\) are downstream compressions of generated observables. |
| What should R5 do next? | Build CAMB-independent analytic validation oracles for the FLRW projector/source limits. |

R4 is complete. The next cumulative append should be **R5 — High-k analytic validation oracle**.


---

# R5 — High-k Analytic Validation Oracle

## R5.0 Purpose, Scope, and Verdict

R5 constructs CAMB-independent validation targets for the FLRW line-of-sight projector and for isolated source branches. The purpose is not to reproduce the full CAMB transfer function. The purpose is to create analytic or semi-analytic input/output pairs for which BASS can be tested at large oscillation frequency without depending on CAMB's exposed `T_source` or `delta_p_l_k` internals.

The Round-15 hand-off already established the key empirical warning: the diagnostic identity
\[
\Delta^T_\ell(k)=\int d\eta\,T_{\rm source}(\eta,k)
             j_\ell[k(\eta_0-\eta)]
\]
works for CAMB's exposed source at low \(k\), but fails badly once \(k\gtrsim 3\times10^{-2}\,{\rm Mpc}^{-1}\). Therefore, high-\(k\) tests should not use CAMB as the oracle. They should use analytic toy sources whose exact or controlled-asymptotic transfers are known.

R5 verdict:

1. **The sharp-visibility Sachs--Wolfe oracle is exact and already implemented.** `sachs_wolfe_analytic_transfer` at `htt/bass/los/flrw_bessel_projector.py:614-638` is the correct exact oracle for a delta-function visibility with no Doppler, no ISW, and no polarization source.
2. **The pure Doppler branch has an exact impulse oracle.** Under the standard convention \(S_D=(gv_b)'\) accepted in R2.3/R2.4 after R7, the sharp limit gives \(\Delta^D_\ell=k v_{b*}j_\ell'(x_*)\). This is a sign and radial-kernel regression test for that convention.
3. **Finite-width Gaussian visibility is not generally an elementary exact closed form.** It is still useful, but should be labelled as either a narrow-width moment expansion or a high-frequency plane-wave/saddle oracle, not as a mathematically exact transfer for arbitrary \((k,\ell,\sigma)\).
4. **The acoustic toy is valuable for phase and damping tests.** It tests whether the projector preserves the acoustic phase and finite-visibility damping, not whether BASS has the correct physical recombination source.
5. **Limber ISW is optional and should not be a core low-\(\ell\) validation target.** It is a high-\(\ell\), smooth-window asymptotic. Since this project is low-\(\ell\)-heavy, exact ISW impulse or smooth Gaussian impulse tests are safer.
6. **R5 should produce unit-test targets, not production physics.** These oracles validate numerical projection, source-branch signs, and resolution behavior. They do not replace the R2/R3 source-contract audit.

---

## R5.1 Common Notation and Projector Contract

Use conformal time \(\eta\), present conformal time \(\eta_0\), and radial distance
\[
\chi(\eta)=\eta_0-\eta .
\]
For a source localized near \(\eta_*\), define
\[
\chi_* = \eta_0-\eta_*,\qquad x_* = k\chi_* .
\]
The implemented scalar temperature projector is
\[
\boxed{
\Delta^T_\ell(k)=\int_{\eta_{\rm min}}^{\eta_0}d\eta\,
S_T(\eta,k)j_\ell[k(\eta_0-\eta)]
}
\]
as implemented in `project_temperature_transfer` at `htt/bass/los/flrw_bessel_projector.py:499-546`.

The implemented scalar E-mode projector is
\[
\boxed{
\Delta^E_\ell(k)=\int d\eta\,S_E(\eta,k)P^E_\ell[k(\eta_0-\eta)]
}
\]
with \(\ell<2\) forced to zero, as implemented in `project_polarization_transfer` at `htt/bass/los/flrw_bessel_projector.py:549-580`.

For finite-width tests, define a normalized Gaussian visibility window
\[
g_\sigma(\eta)=\frac{1}{\sqrt{2\pi}\sigma}
\exp\left[-\frac{(\eta-\eta_*)^2}{2\sigma^2}\right],
\qquad
\int_{-\infty}^{\infty}g_\sigma(\eta)d\eta=1.
\]
Production visibility is not exactly Gaussian; this is a controlled toy source.

Two numerical resolution conditions should be enforced in every finite-width test:

\[
\Delta\eta \lesssim \frac{\sigma}{8},
\qquad
\Delta\eta \lesssim \frac{2\pi}{8k},
\]
so that both the visibility width and the Bessel oscillation are resolved. This mirrors the Round-15 P0 grid logic: recombination width and oscillation scale must be decoupled.

---

## R5.2 Oracle A — Exact Sharp-Visibility Sachs--Wolfe Source

### Assumptions

1. Visibility is a delta distribution:
   \[
   g(\eta)=\delta(\eta-\eta_*).
   \]
2. Only the scalar emission/gravity source is active:
   \[
   A_*=(\Theta_0+\Psi)_*.
   \]
3. No polarization source, no ISW source, no Doppler source:
   \[
   \Pi=0,
   \qquad
   \dot\Phi+\dot\Psi=0,
   \qquad
   v_b=0.
   \]

### Source

\[
S_T(\eta,k)=A_*\delta(\eta-\eta_*).
\]

### Exact transfer

\[
\boxed{
\Delta^{\rm SW}_\ell(k)=A_*j_\ell(x_*)
}
\]

This is exact for all \(k\), all \(\ell\), and all \(x_*\). It is already implemented as
`htt/bass/los/flrw_bessel_projector.py:614-638`.

### Recommended tests

| Test | Target | Regime | Suggested tolerance |
|---|---|---|---:|
| Direct analytic function | `sachs_wolfe_analytic_transfer` | all valid \(k,\ell\) | machine precision against `spherical_bessel_at` |
| Narrow Gaussian collapse | `project_temperature_transfer` fed with \(A_*g_\sigma\) | \(k\sigma\ll1\), grid resolves \(\sigma\) | \(10^{-3}\) or tighter |
| High-\(k\) oscillatory projector | same | \(k\chi_*\in[10,300]\), \(k\sigma\ll1\) | \(10^{-3}\) if grid follows P0 criteria |

### Failure interpretation

- A failure in the direct analytic function means the Bessel helper or argument convention is wrong.
- A failure in the narrow-Gaussian test with the direct analytic function passing means the quadrature/grid is not resolving the source or oscillatory kernel.
- This oracle does **not** validate the Doppler, ISW, or polarization source assembly.

---

## R5.3 Oracle B — Exact Sharp-Impulse ISW Source

### Assumptions

1. Visibility source is off:
   \[
   g(\eta)=0.
   \]
2. The only active term is an impulse in the Weyl-potential derivative:
   \[
   F_{\rm ISW}(\eta,k)
   =e^{-\kappa(\eta)}[\dot\Phi(\eta,k)+\dot\Psi(\eta,k)]
   =I_*\delta(\eta-\eta_I).
   \]
3. No SW, no Doppler, no polarization source.

### Exact transfer

\[
\boxed{
\Delta^{\rm ISW}_\ell(k)=I_*j_\ell[k(\eta_0-\eta_I)]
}
\]

This is mathematically identical to the sharp SW projector test but exercises the ISW branch of `build_temperature_source`, namely `isw = exp(-kappa_arr) * phi_psi_dot_arr` at `htt/bass/los/flrw_bessel_projector.py:449-450`.

### Recommended tests

| Test | Target | Regime | Suggested tolerance |
|---|---|---|---:|
| Direct source-array impulse | `project_temperature_transfer` | all \(k,\ell\) | set by discrete impulse normalization |
| Gaussian ISW impulse | `build_temperature_source` + projector | \(k\sigma\ll1\) | \(10^{-3}\) |
| Source isolation | `FLRWSourceTerms.with_isw_only` | all source branches zero except ISW | exact branch-level equality before projection |

### Failure interpretation

If SW impulse works but ISW impulse fails, the projector is probably healthy and the problem is in source-branch weighting, optical-depth convention, or array normalization.

---

## R5.4 Oracle C — Exact Sharp-Impulse Doppler Source

This is the most important R5 regression oracle because it protects the accepted standard Doppler convention against sign, derivative, and grid-resolution regressions.

### Assumptions

1. Only the Doppler branch is active.
2. BASS source convention is the one implemented in `build_temperature_source`:
   \[
   S_D(\eta,k)=\frac{d}{d\eta}[g(\eta)v_b(\eta)] .
   \]
3. In the sharp limit,
   \[
   g(\eta)=\delta(\eta-\eta_*),
   \qquad
   v_b(\eta)=V_*
   \]
   locally around \(\eta_*\).

### Derivation

Start from the implemented projector:
\[
\Delta^D_\ell(k)=\int d\eta\,
\frac{d}{d\eta}[g(\eta)V_*]
 j_\ell[k(\eta_0-\eta)] .
\]
Assuming the boundary term vanishes,
\[
\Delta^D_\ell(k)
= -V_*
\int d\eta\,g(\eta)
\frac{d}{d\eta}j_\ell[k(\eta_0-\eta)].
\]
Since
\[
\frac{d}{d\eta}j_\ell[k(\eta_0-\eta)]
=-k j_\ell'[k(\eta_0-\eta)],
\]
we obtain
\[
\boxed{
\Delta^D_\ell(k)=kV_*j_\ell'(x_*)
}
\]
for the BASS convention \(S_D=(gv_b)'\).

Useful exact recurrence relations are
\[
j_\ell'(x)=j_{\ell-1}(x)-\frac{\ell+1}{x}j_\ell(x)
=\frac{\ell}{x}j_\ell(x)-j_{\ell+1}(x).
\]
For \(\ell=0\),
\[
j_0'(x)=-j_1(x).
\]

### Recommended tests

| Test | Target | Regime | Suggested tolerance |
|---|---|---|---:|
| Analytic derivative recurrence | Bessel helper layer | all \(x>0\) | \(10^{-12}\) relative, away from zeros |
| Narrow Gaussian derivative | `build_temperature_source` Doppler branch + projector | \(k\sigma\ll1\) | \(10^{-3}\) to \(10^{-2}\), depending on numerical differentiation |
| Direct source-array derivative | projector only, with analytic \((gV)'\) array | \(k\chi_*\in[10,300]\) | \(10^{-3}\) with P0-style grid |
| Sign regression | compare against \(+kV_*j_\ell'(x_*)\), not the negative | all \(\ell\) | exact sign test |

### Failure interpretation

- If this test fails by a sign, the numerical derivative/source implementation is inconsistent with the accepted radial Doppler kernel; this would be a regression, not evidence for adding a `1/k` factor.
- If it fails only when using `build_temperature_source` but passes with a directly supplied analytic derivative source, the weak point is `np.gradient` at `htt/bass/los/flrw_bessel_projector.py:451-453`, not the projector.
- If it passes only for very small \(k\), the LoS grid still does not resolve the derivative source or the Bessel kernel.

### R2/R3 connection

This oracle does not settle whether the physical baryon velocity variable is the right gauge/frame velocity. It only settles whether the implemented source convention \(S_D=(gv_b)'\) is projected with the correct radial kernel and sign.

---

## R5.5 Oracle D — Sharp-Visibility Polarization Impulse

Although R5 is mostly about temperature validation, the same analytic strategy should be applied to the E-mode projector because `project_polarization_transfer` uses a separate radial projection factor.

### Assumptions

1. Polarization source is localized:
   \[
   \Pi(\eta)=\Pi_*\delta(\eta-\eta_*).
   \]
2. The BASS scalar polarization source convention is
   \[
   S_E(\eta)=-\frac{\sqrt6}{4}g(\eta)\Pi(\eta),
   \]
   as implemented at `htt/bass/los/flrw_bessel_projector.py:458-472`.
3. Temperature sources are not part of this oracle.

### Exact transfer

Let \(P^E_\ell(x)\) denote the radial E-mode projection factor implemented by `e_mode_projection_factor`. Then
\[
\boxed{
\Delta^E_\ell(k)=
-\frac{\sqrt6}{4}\Pi_* P^E_\ell(x_*),
\qquad \ell\ge2,
}
\]
and
\[
\boxed{
\Delta^E_0=\Delta^E_1=0 .
}
\]

### Recommended tests

| Test | Target | Regime | Suggested tolerance |
|---|---|---|---:|
| \(\ell<2\) zero test | `project_polarization_transfer` | all \(k\) | exact zero |
| Sharp impulse | `build_polarization_source` + projector | \(k\sigma\ll1\) | \(10^{-3}\) |
| Projection-factor regression | `e_mode_projection_factor` | compare known limiting forms | module-specific |

### Failure interpretation

A failure here is independent of the temperature SW/ISW/Doppler branch. It indicates either sign/prefactor mismatch in \(S_E\), a bug in the spin-2 radial projection factor, or insufficient grid resolution for the localized polarization source.

---

## R5.6 Oracle E — Finite-Width Gaussian SW Source: Moment Expansion

The hand-off asks for a Gaussian-visibility closed form. Strictly, the integral
\[
\int d\eta\,g_\sigma(\eta)j_\ell[k(\eta_0-\eta)]
\]
does not have a simple elementary closed form for arbitrary \(\ell\), \(k\sigma\), and \(k\chi_*\). Therefore, R5 should split it into two controlled analytic approximations.

First, when \(k\sigma\ll1\), the Gaussian acts as a moment operator on the Bessel kernel. Let
\[
S_T(\eta,k)=A_*g_\sigma(\eta).
\]
Writing \(\eta=\eta_*+\delta\), so \(x=k(\chi_* -\delta)\), the exact Gaussian expectation is formally
\[
\Delta_\ell^{\rm GSW}(k)=A_*
\left\langle j_\ell(x_*-k\delta)\right\rangle_{\delta\sim N(0,\sigma^2)}.
\]
Expanding in even Gaussian moments gives
\[
\boxed{
\Delta_\ell^{\rm GSW}(k)
=A_*\left[
 j_\ell(x_*)
 +\frac{(k\sigma)^2}{2}j_\ell''(x_*)
 +\frac{(k\sigma)^4}{8}j_\ell^{(4)}(x_*)
 +O((k\sigma)^6)
\right].
}
\]
This is not a high-\(k\sigma\) oracle; it is a narrow-visibility finite-width correction to the sharp SW oracle.

The second derivative can be evaluated without numerical differentiation using the spherical-Bessel equation
\[
x^2j_\ell''(x)+2xj_\ell'(x)+[x^2-\ell(\ell+1)]j_\ell(x)=0,
\]
so
\[
\boxed{
 j_\ell''(x)=
\left[\frac{\ell(\ell+1)}{x^2}-1\right]j_\ell(x)
-\frac{2}{x}j_\ell'(x).
}
\]
Higher derivatives may be generated recursively from the Bessel equation or by symbolic recurrence once and frozen into test helpers.

### Recommended tests

| Test | Target | Regime | Suggested tolerance |
|---|---|---|---:|
| second-order Gaussian moment | projector only | \(k\sigma\le0.05\) | \(10^{-4}\) |
| fourth-order Gaussian moment | projector only | \(k\sigma\le0.2\) | \(10^{-3}\) |
| convergence with \(\sigma\to0\) | projector only | decreasing \(\sigma\) | observed error scales as \((k\sigma)^2\) or \((k\sigma)^4\) depending oracle order |

---

## R5.7 Oracle F — Finite-Width Gaussian SW Source: High-Frequency Plane-Wave/Saddle Form

For high \(k\chi_*\) and fixed low \(\ell\), use the leading asymptotic form
\[
j_\ell(x)\simeq \frac{\sin(x-\ell\pi/2)}{x},
\qquad x\gg \ell(\ell+1)/2 .
\]
If \(\sigma\ll\chi_*\), the denominator can be frozen at \(x_*=k\chi_*\). Then
\[
\Delta_\ell^{\rm GSW}(k)
\simeq
\frac{A_*}{k\chi_*}
\int d\delta\,g_\sigma(\delta)
\sin[x_*-k\delta-\ell\pi/2].
\]
The Gaussian Fourier transform gives
\[
\boxed{
\Delta_\ell^{\rm GSW,asym}(k)
\simeq
\frac{A_*}{k\chi_*}
\exp\left[-\frac12(k\sigma)^2\right]
\sin\left(x_*-\frac{\ell\pi}{2}\right).
}
\]

This is the cleanest high-\(k\) finite-width oracle because it directly tests the expected exponential damping from finite recombination width.

### Regime of validity

Require
\[
k\chi_*\gg \ell^2,
\qquad
\sigma\ll\chi_*,
\qquad
\Delta\eta\lesssim\min(\sigma/8,2\pi/(8k)).
\]
For this project, with \(\ell\le10\), a practical test regime is
\[
k\chi_*\gtrsim 50,
\qquad
\sigma/\chi_*\lesssim10^{-2}.
\]
The damping factor becomes very small when \(k\sigma\gg1\); relative-error tests should avoid zeros and underflow, or switch to absolute tolerances.

### Recommended tests

| Test | Target | Regime | Suggested tolerance |
|---|---|---|---:|
| high-frequency Gaussian damping | projector only | \(k\chi_*\ge50\), \(\ell\le10\), \(k\sigma\in[0.2,3]\) | 1--3% away from zeros |
| phase preservation | projector only | same | phase error \(<0.05\) rad equivalent |
| width sweep | projector only | fixed \(k\), vary \(\sigma\) | log amplitude slope \(-k^2/2\) |

### Failure interpretation

If the narrow moment expansion passes but this high-frequency Gaussian test fails, the problem is probably oscillatory quadrature rather than source normalization.

---

## R5.8 Oracle G — Acoustic-Peak Toy Source

### Sharp-visibility acoustic toy

Let the source be a simple acoustic oscillator sampled at last scattering:
\[
S_T(\eta,k)=A\cos[k r_s(\eta_*)+\varphi]\delta(\eta-\eta_*),
\]
where \(r_s\) is the sound horizon. Then
\[
\boxed{
\Delta^{\rm ac,sharp}_\ell(k)=
A\cos[k r_s(\eta_*)+\varphi]j_\ell(k\chi_*).
}
\]
The acoustic extrema occur when
\[
k r_s(\eta_*)+\varphi\simeq n\pi,
\]
while the observed transfer is further modulated by \(j_\ell(k\chi_*)\). This oracle checks phase preservation, not physical peak amplitudes.

### Finite-Gaussian acoustic toy, high-frequency asymptotic

Let
\[
S_T(\eta,k)=A g_\sigma(\eta)
\cos[c_s k\eta+\varphi],
\]
with constant toy sound speed \(c_s\). In the high-frequency, frozen-denominator approximation,
\[
j_\ell[k(\eta_0-\eta)]\simeq
\frac{\sin[k\chi_* - k(\eta-\eta_*)-\ell\pi/2]}{k\chi_*}.
\]
Using \(\delta=\eta-\eta_*\), define
\[
A_\ell = k\chi_* -\frac{\ell\pi}{2},
\qquad
B = c_s k\eta_*+\varphi.
\]
Then
\[
\sin(A_\ell-k\delta)\cos(B+c_sk\delta)
=\frac12\left[
\sin(A_\ell+B+(c_s-1)k\delta)
+\sin(A_\ell-B-(1+c_s)k\delta)
\right].
\]
Averaging over the Gaussian gives
\[
\boxed{
\Delta^{\rm ac,G}_\ell(k)
\simeq
\frac{A}{2k\chi_*}
\left[
 e^{-\frac12(1-c_s)^2k^2\sigma^2}
 \sin\left(A_\ell+B\right)
+
 e^{-\frac12(1+c_s)^2k^2\sigma^2}
 \sin\left(A_\ell-B\right)
\right].
}
\]

This formula is useful because it contains two physically interpretable damping scales: a slowly varying co-propagating phase branch with \((1-c_s)k\sigma\), and a rapidly damped counter-propagating branch with \((1+c_s)k\sigma\).

### Recommended tests

| Test | Target | Regime | Suggested tolerance |
|---|---|---|---:|
| sharp acoustic phase | projector only | all \(k\), if source is implemented as analytic impulse | same as SW impulse |
| finite acoustic damping | projector only | \(k\chi_*\ge50\), \(\ell\le10\), \(\sigma/\chi_*\ll1\) | 3--5% |
| peak-location regression | generated \(\Delta_\ell(k)\) over a grid | compare extrema against \(kr_s+\varphi=n\pi\) after masking Bessel zeros | phase-level, not amplitude-level |

### Failure interpretation

This test separates three errors that CAMB comparisons tend to confound: acoustic-source phase, Bessel radial phase, and finite-width damping.

---

## R5.9 Oracle H — Pure Doppler Finite-Width Gaussian

The sharp Doppler oracle is exact. A finite-width version checks numerical differentiation and oscillatory projection together.

Let
\[
g(\eta)=g_\sigma(\eta),
\qquad
v_b(\eta)=V_*.
\]
Then
\[
S_D(\eta)=V_*g_\sigma'(\eta)
=-V_*\frac{\eta-\eta_*}{\sigma^2}g_\sigma(\eta).
\]
The exact integral is
\[
\Delta^D_\ell(k)=kV_*\left\langle
j_\ell'(x_*-k\delta)
\right\rangle_{\delta\sim N(0,\sigma^2)}.
\]
For \(k\sigma\ll1\),
\[
\boxed{
\Delta^D_\ell(k)=kV_*\left[
 j_\ell'(x_*)
 +\frac{(k\sigma)^2}{2}j_\ell'''(x_*)
 +O((k\sigma)^4)
\right].
}
\]
For high \(k\chi_*\) with frozen denominator,
\[
j_\ell'(x)\simeq
\frac{\cos(x-\ell\pi/2)}{x}
-\frac{\sin(x-\ell\pi/2)}{x^2},
\]
so the leading finite-width Doppler transfer is
\[
\boxed{
\Delta^{D,{\rm G,asym}}_\ell(k)
\simeq
V_*e^{-\frac12(k\sigma)^2}
\left[
\frac{\cos(x_*-\ell\pi/2)}{\chi_*}
-
\frac{\sin(x_*-\ell\pi/2)}{k\chi_*^2}
\right].
}
\]
The first term usually dominates at high \(k\chi_*\).

### Recommended tests

| Test | Target | Regime | Suggested tolerance |
|---|---|---|---:|
| direct analytic \(g'\) source | projector only | \(k\sigma\le0.1\) | \(10^{-3}\) |
| `np.gradient` derivative source | `build_temperature_source` | same | looser; \(10^{-2}\) initially |
| high-frequency Doppler damping | projector only | \(k\chi_*\ge50\), \(k\sigma\in[0.2,2]\) | 3--5% |

### Failure interpretation

A failure only in the `np.gradient` path indicates that a spline/analytic derivative may be needed for high-\(k\) tests, even if production accuracy is adequate in smooth regimes.

---

## R5.10 Oracle I — Smooth Pure ISW in the Limber Regime

This is optional and should not be the first R5 unit test because it is a high-\(\ell\), smooth-window approximation rather than a low-\(\ell\) exact identity.

Let
\[
\Delta^{\rm ISW}_\ell(k)=\int d\eta\,F(\eta,k)j_\ell[k(\eta_0-\eta)].
\]
Change variables to \(\chi=\eta_0-\eta\) and write \(W(\chi,k)=F(\eta_0-\chi,k)\):
\[
\Delta^{\rm ISW}_\ell(k)=\int d\chi\,W(\chi,k)j_\ell(k\chi).
\]
For \(\nu=\ell+1/2\), a standard leading Limber approximation gives
\[
\boxed{
\Delta^{\rm ISW,Limber}_\ell(k)
\simeq
\sqrt{\frac{\pi}{2\nu}}\frac{1}{k}
W\left(\frac{\nu}{k},k\right)
}
\]
when \(W\) is smooth on the oscillation scale and \(\ell\) is large.

### Recommended use

| Use | Recommendation |
|---|---|
| Default low-\(\ell\) BASS validation | Do not use as a pass/fail oracle. |
| High-\(\ell\) projector stress test | Useful if temporary \(\ell_{\max}\gtrsim30\) tests are allowed. |
| Tolerance | 5--10% at best for moderate \(\ell\), better only at genuinely high \(\ell\). |

### Failure interpretation

A failure of this oracle at \(\ell\le10\) is not meaningful. A failure at high \(\ell\) with a very smooth source can indicate radial argument, normalization, or oscillatory integration errors.

---

## R5.11 Bessel-Kernel Internal Identities

These tests do not validate physical sources, but they are cheap guards against kernel regressions.

### Sum rule

The code already includes `bessel_sum_rule` at `htt/bass/los/flrw_bessel_projector.py:641-660` for
\[
\boxed{
\sum_{\ell=0}^{\infty}(2\ell+1)j_\ell^2(x)=1.
}
\]
A finite partial sum should approach unity once \(\ell_{\max}\gtrsim x\) with a safety margin.

### Differential equation

Each computed \(j_\ell(x)\) should satisfy
\[
x^2j_\ell''(x)+2xj_\ell'(x)+[x^2-\ell(\ell+1)]j_\ell(x)=0.
\]
This is useful if derivative-based Doppler tests are added.

### Recurrence

Use both recurrences
\[
j_{\ell-1}(x)+j_{\ell+1}(x)=\frac{2\ell+1}{x}j_\ell(x),
\]
\[
j_\ell'(x)=j_{\ell-1}(x)-\frac{\ell+1}{x}j_\ell(x)
=\frac{\ell}{x}j_\ell(x)-j_{\ell+1}(x).
\]
These should be tested away from \(x=0\) and away from numerical underflow.

---

## R5.12 Proposed Unit-Test Matrix

| Oracle | Exact / asymptotic | Branch tested | Recommended status |
|---|---|---|---|
| A. Sharp SW | exact | projector + existing analytic helper | must add / keep |
| B. Sharp ISW | exact | ISW weighting + projector | must add |
| C. Sharp Doppler | exact | Doppler sign/radial derivative | must add as high-value regression; not a formula-patch gate |
| D. Sharp E polarization | exact with documented spin-2 projection factor | E-mode branch | should add as regression |
| E. Gaussian SW moment | controlled expansion | finite-width quadrature | should add |
| F. Gaussian SW high-frequency | asymptotic | high-\(k\) damping and phase | should add as stress test |
| G. Acoustic toy | exact sharp / asymptotic finite-width | acoustic phase + finite-width damping | should add |
| H. Gaussian Doppler | controlled expansion/asymptotic | derivative source + high-\(k\) Doppler | should add after C |
| I. Limber ISW | asymptotic high-\(\ell\) | smooth late source projection | optional, not low-\(\ell\) gate |
| Bessel identities | exact identities | kernel helper layer | must keep as low-cost regression |

---

## R5.13 Minimal Test Implementation Sketch

No production code should be changed in R5, but the future coding agent can implement the tests as follows.

### Sharp SW

```python
Delta_ref = sachs_wolfe_analytic_transfer(k, eta_star, A_star, config)
# Compare to direct projector fed by a normalized narrow Gaussian source.
```

### Sharp ISW

```python
sources = FLRWSourceTerms.with_isw_only(phi_dot_plus_psi_dot=I_star * narrow_gaussian)
S = build_temperature_source(eta_grid, sources, g_zero, kappa_zero)
Delta = project_temperature_transfer(k, S, eta_grid, config)
Delta_ref[ell] = I_star * spherical_jn(ell, k * (eta0 - eta_I))
```

### Sharp Doppler

```python
# Prefer a direct analytic derivative source first.
S_D = V_star * gaussian_derivative(eta_grid, eta_star, sigma)
Delta = project_temperature_transfer(k, S_D, eta_grid, config)
Delta_ref[ell] = k * V_star * spherical_jn_derivative(ell, x_star)
```

Then add a second test through `build_temperature_source` to check the numerical derivative implementation separately.

### Acoustic toy

```python
S = A * gaussian(eta_grid, eta_star, sigma) * np.cos(c_s * k * eta_grid + phase)
Delta = project_temperature_transfer(k, S, eta_grid, config)
Delta_ref = asymptotic_formula_R5_8(...)
```

Use masks near analytic zeros so relative errors do not explode.

---

## R5.14 R5 Verdict Table

| Question | R5 answer |
|---|---|
| Can CAMB direct be the high-\(k\) oracle? | No. Use analytic toy sources. |
| Is the existing sharp SW helper valid? | Yes; it is the exact delta-visibility oracle. |
| Is Gaussian visibility an exact closed-form oracle? | Not in elementary form for arbitrary parameters; use moment or high-frequency asymptotics. |
| What is the highest-priority new oracle? | The monopole-frame diagnostic is the formal gate; sharp Doppler \(\Delta^D_\ell=kV_*j_\ell'(x_*)\) is the highest-value regression oracle. |
| What validates high-\(k\) damping? | Gaussian SW/acoustic asymptotics with \(e^{-(k\sigma)^2/2}\)-type factors. |
| Should Limber ISW be a default low-\(\ell\) gate? | No. It is optional high-\(\ell\) stress testing. |
| Does R5 authorize code changes? | No. It supplies test targets for later coding-agent work. |
| What should R6 do next? | Build the master code-mapping table and executive summary, integrating R2--R5 caveats and proposed test oracles. |

R5 is complete. The next cumulative append should be **R6 — Master code-mapping table and executive summary**.

---

# R6 — Master Code-Mapping Table and Executive Summary

## R6.0 Scope of This Round

R6 consolidates R2--R5 into an audit-facing artifact. It does not introduce a new derivation, and it does not authorize production-code edits. Its job is to state the current verdict, list follow-up actions, and map every derivation claim to the relevant BASS source file and line range in the Round-15 P1 hand-off bundle.

Line numbers below refer to the files as shipped in `v5_round15_p1_handoff_bundle.zip`. They may shift after commit-level formatting changes; the semantic anchors should be preserved.

---

## R6.1 Master Verdict \(R7-corrected\)

The current BASS hierarchy is genuinely PSTF/tetrad-native at the transport level. The code does not carry a synchronous-gauge metric trace as a hidden runtime state, and P1 must not be turned into an `h_S'` or `h_S_dot/6` patch. The previous “D-3 gauge fix” framing is therefore superseded by a stricter source-contract audit.

The FLRW LoS projector itself is structurally healthy as a radial integrator: it evaluates scalar temperature sources against spherical-Bessel kernels and E-mode sources against the documented spin-2 projection factor. Round-15 P0's low-`k` recovery is consistent with this conclusion. However, that empirical recovery does not prove the remaining native BASS source-term contract, because the decisive P0 comparison primarily validated the LoS grid/projector path and because the CAMB exposed-source oracle is not reliable at high `k`.

After R7, **one** source contract remains unresolved before declaring the full native FLRW source assembly formally closed:

1. **Monopole contract.** `theta0_g = photon_T_tower[:, slot(0,0)]` must be explicitly declared and tested as the emission-frame monopole compatible with the Bardeen/Newtonian `Psi` entering `theta0_g + psi`. If the tower is synchronous-like or radiation-comoving in a different slicing, the correction must be the covariant equivalent of `Theta_0 -> Theta_0 + H alpha`, not a raw synchronous metric patch.

The Doppler and temperature-polter branches are accepted under the standard convention: `(g v_b)'` is the correct `j_l`-only Doppler source for dimensionless `v_b`, and `g Pi/4` is the canonical scalar temperature polter term. Their analytic oracles remain useful regression tests, not blockers for the source contract.

For Bianchi extension, the scalar FLRW `S_T * j_l` architecture is not the general target. The correct target is the matrix-propagator structure already described in the low-ell tetrad reference: all `m` channels when non-axisymmetric shear/curvature or tilt requires them, shear/curvature recoupling, tilt-dependent source/collision/visibility frames, and observer-side `a_{ell m}` or map-level output. Axisymmetric aligned Bianchi I is the restricted `m=0` exception.

---

## R6.2 Code-Level Follow-Up List \(R7-corrected\)

These are follow-up actions for a later coding/documentation track. They are not executed in P1.

### Required before any source-assembly correctness claim

1. **Add a source-contract note** near `extract_flrw_sources_from_tier_b` and `build_temperature_source` stating the exact frame/gauge meaning of `theta_0` and `psi`, with special attention to `theta0_g + psi`.
2. **Add a theta0 convention test** that compares a controlled Newtonian/Bardeen-frame fixture against the extracted `theta0_g + psi` SW source. This is the gate for the R3 monopole issue.
3. **Add a potential-invariance test** for the constraint reconstruction under a synthetic scalar time shift, especially because `delta_rho_gamma = 4 theta0_g` enters the reconstructed potentials.
4. **Document high-k validation limits**: do not use CAMB `delta_p_l_k` as the native BASS high-k oracle. Use the R5 analytic or asymptotic toy sources.

### Regression tests recommended, not source-contract gates

1. **Add the sharp Doppler oracle** from R5: for a normalized sharp source represented as `(g V)'`, require
   \[
   \Delta^D_\ell(k)=k V_* j'_\ell(x_*),\qquad x_*=k(\eta_0-\eta_*).
   \]
   This protects the correct convention. It must not be used to motivate a `1/k` patch unless the test is incorrectly constructed.
2. **Add the polarization oracle** exercising both the temperature polter term `g Pi/4` on `j_l` and the E-mode term `-(sqrt(6)/4) g Pi` on the spin-2 projection. This is a regression test, not a temperature-side radial-basis contract gate.
3. **Add sharp SW/ISW and Gaussian/acoustic toy oracles** as high-`k` projector/source stress tests independent of CAMB introspection.

### Conditional production changes

No production source formula should be patched merely from R6 or R7. A source formula patch is justified only if the monopole-frame tests fail after the source-contract definitions are written. The only plausible source correction currently authorized for investigation is a PSTF-native monopole transformation
\[
\Theta_0 \mapsto \Theta_0 + \mathcal H\alpha,
\]
where \(\alpha\) must be supplied by a declared PSTF/tetrad scalar diagnostic such as a tracked `theta_common` history or a reconstructed local expansion perturbation. Doppler and temperature-polter formula patches are explicitly not authorized.

### Explicit non-action

Do **not** add `h_S`, `h_dot`, `h_prime`, or `theta0_g_newtonian = theta0_g_synchronous + h_S_dot/6` to the BASS PSTF runtime path. Do **not** insert a Doppler `1/k` factor. Do **not** replace the temperature-side `Pi/4` by a spin-projected radial kernel.

---

## R6.3 Master Code-Mapping Table

| Derivation section | Formula / claim | BASS file : lines | Implementation status | Notes |
|---|---|---|---|---|
| R2 | Scalar FLRW temperature projection \(\Delta^T_\ell=\int d\eta\,S_T j_\ell[k(\eta_0-\eta)]\). | `htt/bass/los/flrw_bessel_projector.py:11-14`, `499-546` | Implemented | Projector/integrator is structurally clear. R5 oracles should protect this layer. |
| R2 | E-mode projection \(\Delta^E_\ell=\int d\eta\,S_E P^E_\ell\), with \(P^E_\ell\propto j_\ell/x^2\). | `htt/bass/los/flrw_bessel_projector.py:15-20`, `549-580` | Implemented / accepted | Projection factor exists and matches the standard spin-2 branch under the documented BASS convention. |
| R2 | `FLRWSourceTerms` requires five explicit callables: \(\Theta_0,\Psi,\dot\Phi+\dot\Psi,v_b,\Pi\). | `htt/bass/los/flrw_bessel_projector.py:31-41`, `320-337`, `344-390` | Implemented API | Good design: no silent omission of ISW/Doppler. Remaining variable contract is the monopole frame. |
| R2 | Temperature source assembly \(S_T=g(\Theta_0+\Psi+\Pi/4)+e^{-\kappa}(\dot\Phi+\dot\Psi)+(gv_b)'\). | `htt/bass/los/flrw_bessel_projector.py:23-30`, `416-455` | Implemented, conditionally accepted | Doppler and polter are accepted by R7. Remaining condition is the \(\Theta_0+\Psi\) monopole-frame contract. |
| R2 | Doppler source represented as `(g v_b)'` before projection with \(j_\ell\). | `htt/bass/los/flrw_bessel_projector.py:25-28`, `330-332`, `451-454` | Implemented / accepted | R7 verifies this is the standard collapsed source for dimensionless `v_b = theta_b/k`; no `1/k` patch. |
| R2 | Temperature polarization contribution represented as `g * Pi / 4`. | `htt/bass/los/flrw_bessel_projector.py:25`, `447-448`; `htt/bass/spectrum/tier_b_source_extraction.py:234-236` | Implemented / accepted | R7 verifies this is the canonical scalar temperature polter term under \(\Pi=\Theta_2-\sqrt6E_2\). |
| R2 | Scalar E source \(S_E=-(\sqrt6/4)g\Pi\). | `htt/bass/los/flrw_bessel_projector.py:29`, `458-472`, `588-607` | Implemented / accepted structurally | E branch has the expected spin-2 projector. Keep sharp-polarization regression test. |
| R2/R3 | \(\Pi=\Theta_2-\sqrt6 E_2\). | `htt/bass/spectrum/tier_b_source_extraction.py:80`, `225-236`; `docs/lowell_bianchi_solver_reference.md:554-586` | Implemented for scalar `m=0` extraction | Matches the repo convention. The map to external literature signs must be stated in docs. |
| R2/R3 | Newtonian/Bardeen potentials reconstructed from Einstein constraints. | `htt/bass/spectrum/tier_b_source_extraction.py:22-33`, `275-306`, `313-318` | Implemented, clarification required | Uses density/momentum/stress from the Tier-B output. Correctness depends on the monopole contract, especially the photon density contribution. |
| R3 | Monopole extraction `theta0_g = t_tower[:, slot(0,0)]`. | `htt/bass/spectrum/tier_b_source_extraction.py:83-85`, `208-236`, `254-256`, `313-318` | Unresolved source contract | This is the key R3 issue. Do not call it Newtonian, synchronous, or radiation-comoving without a declared transformation rule. |
| R3 | `IntegrationResult` stores PSTF towers and local species histories, but no synchronous metric trace. | `htt/bass/hierarchy/integrator.py:223-255`, `260-315` | Implemented storage | Supports the verdict that an `h_S` patch is the wrong remedy for P1. |
| R3 | FLRW regular seed / packed-seed compatibility bridge. | `htt/bass/hierarchy/seed_compatibility.py:151-212`, `374-409`, `412-478` | Partial / bridge layer | The file mentions synchronous-gauge super-horizon seed ratios in the adiabatic branch. That does not by itself prove the evolved `theta0_g` is the required LoS monopole. |
| R4 | Basic tetrad frame rule: transport in \(n^a\), collision/source/visibility in \(u_e^a\). | `docs/lowell_bianchi_solver_reference.md:23-63` | Design authority | This rule should be elevated into the final P1 doc as the non-negotiable Bianchi architecture. |
| R4 | PSTF radiation variables \(\Theta_{A_\ell},E_{A_\ell},B_{A_\ell}\) and harmonic coefficients. | `docs/lowell_bianchi_solver_reference.md:320-354` | Design authority | The code uses packed harmonic components; all-m support exists at the storage level. |
| R4 | Exact 1+3 brightness hierarchy with shear terms that couple \(\ell\to\ell\pm2\) and same rank. | `docs/lowell_bianchi_solver_reference.md:358-426` | Design authority | Justifies why low-ell Bianchi cannot be represented by an FLRW scalar source alone. |
| R4 | Photon/neutrino RHS driver imports T1/T7/T8/T9 packed operators. | `htt/bass/hierarchy/hierarchy_rhs.py:1-12`, `76-84`, `343-448`, `510-515` | Driver implemented; packed algebra not audited here | `packed_operators.py` was not included in the hand-off bundle, so R6 cannot certify the operator coefficients. |
| R4 | Proper shear conversion \(\sigma_{ab}=\Sigma_{ab}/a\). | `htt/bass/hierarchy/hierarchy_rhs.py:39-53`, `127-177`, `297-337` | Implemented | Important unit convention. Preserve in future Bianchi tests. |
| R4 | Anisotropic 3-Ricci routing into hierarchy. | `htt/bass/hierarchy/hierarchy_rhs.py:14-37`, `212-268`, `297-337`, `472-477` | Partial / structural hook | Useful for Bianchi II--IX, but full spatial-gradient/harmonic support is not established in P1. |
| R4 | Bianchi LoS as path-ordered matrix propagator, not scalar \(j_\ell\) projection. | `docs/lowell_bianchi_solver_reference.md:430-460` | Design only / TODO | Future implementation should live outside the FLRW scalar projector contract. |
| R4 | Generic redshift/SW/ISW source in anisotropic spacetime. | `docs/lowell_bianchi_solver_reference.md:464-502` | Design only / TODO | Needs conversion into an executable source vector \(\mathbf S_{\rm pert}\). |
| R4 | Tilted Bianchi source/collision/visibility frame correction. | `docs/lowell_bianchi_solver_reference.md:49-63`, `770-783`; `htt/bass/hierarchy/seed_compatibility.py:42-59`, `224-299` | Partial | Seed wrapper exists; full boosted source, visibility, and collision operators are TODO. |
| R4 | All-\(m\) storage and access. | `htt/bass/spectrum/tier_b_source_extraction.py:83-85`; `htt/bass/hierarchy/integrator.py:260-315`; `htt/bass/hierarchy/hierarchy_rhs.py:417-448`, `450-539` | Partial | Storage/RHS are all-m shaped, but FLRW source extraction uses scalar `m=0`. No `htt/bass/los/families/*` files were present in the hand-off bundle. |
| R4 | \(m=\pm2\) Bianchi channels. | Same all-m storage/RHS anchors above; expected family backends absent from bundle | TODO for general Bianchi; unnecessary in restricted aligned axisymmetry | Mandatory for non-axisymmetric shear/curvature and Bianchi II--IX; identically zero for aligned axisymmetric Bianchi I. |
| R4 | MES / departure compression \(x_C=\Sigma^2_{std}-W^2_{std}+\Omega_{tilt}+\Omega_{k,aniso}\). | `project/03_physics_notes/tomographic_MES_framework.md:47-80`, `295-311`, `315-330` | Documentation / downstream analysis | R4 verdict: use as post-forward-model compression, not as a replacement for directional observables. |
| R5 | Sharp SW analytic transfer \(\Delta^T_\ell=(\Theta_0+\Psi)_*j_\ell(x_*)\). | `htt/bass/los/flrw_bessel_projector.py:614-638` | Implemented | Keep as the first exact projector oracle. |
| R5 | Bessel sum rule and sign/finite guards. | `htt/bass/los/flrw_bessel_projector.py:641-660`, `726-760` | Implemented / partial guards | Add derivative recurrence tests when Doppler oracle is implemented. |
| R5 | High-k analytic oracles: sharp ISW, sharp Doppler, Gaussian SW, acoustic toy, Limber stress test. | Future test file, likely `htt/bass/los/test_flrw_bessel_projector.py` or equivalent | TODO | No test file was included in the hand-off bundle. These are the clean CAMB-independent replacements for invalid high-k CAMB introspection. |

---

## R6.4 Acceptance Criteria Check Against the Hand-Off

| Hand-off acceptance item | R6 status |
|---|---|
| Executive summary with verdict and code-level changes | Satisfied, with the caveat that P1 authorizes no production patch. Follow-up actions are listed instead. |
| FLRW-limit LoS derivation | Present in R2. R7 retracts Doppler/polarization caveats; remaining caveat is the monopole-frame contract. |
| \(\ell=0\) monopole convention audit | Present in R3. Verdict: unresolved source contract; no synchronous metric patch. |
| Bianchi-extension blueprint | Present in R4. Verdict: matrix propagator and all-m tetrad transport, not scalar FLRW source reuse. |
| Analytic oracle list | Present in R5. Exact and asymptotic status separated. |
| Master code-mapping table | Satisfied in R6. |
| Optional second-review prompt | Not yet written; proceed to R7 only if requested. |

---

## R6.5 Final R6 Verdict

R6 does **not** certify the current native BASS FLRW source assembly as fully correct. It certifies a narrower and more useful statement:

1. The **projector/grid layer** is structurally healthy and has clear analytic oracles.
2. The **PSTF/tetrad hierarchy layer** is the correct architectural basis for Bianchi extension.
3. The **source-extraction layer** has one unresolved contract: the monopole frame/gauge in `theta0_g + psi`. Doppler and temperature polter are accepted under the standard scalar LoS convention.
4. The correct next move is not an immediate formula patch. The correct next move is a monopole source-contract documentation pass plus the R3/R5 diagnostic and regression tests.

Once those tests exist, any needed monopole correction will be local and falsifiable rather than a speculative gauge patch.

R6 is complete. The next optional append is **R7 — second-review audit prompt**.


---

# R7 Independent-Audit Integration Note

The independent R7 audit verdict was **ACCEPTABLE WITH REQUIRED CORRECTIONS**. This revised document applies the required corrections directly rather than leaving them as an external addendum.

Applied corrections:

1. Retracted the R2/R6 claim that the Doppler source might be missing a \(1/k\) factor. The accepted convention is
   \[
   \int g k v_b j'_\ell d\eta = \int (g v_b)'j_\ell d\eta,
   \]
   for dimensionless \(v_b=\theta_b/k\).
2. Retracted the R2/R6 claim that the temperature-side \(g\Pi/4\) term is unresolved without a separate radial-basis pre-projection. The accepted convention is that \(g\Pi/4\) is the scalar temperature polter term; the spin-2 projection belongs to the separate E-mode branch.
3. Preserved and sharpened the R3 monopole-frame issue as the only remaining formal source contract.
4. Added the PSTF-native \(\alpha\) sourcing options: tracked `theta_common` semantics or reconstructed local-expansion perturbation \(\delta\Theta\).
5. Added the axisymmetric aligned Bianchi-I exception to the general \(m=\pm2\) requirement.
6. Reclassified sharp Doppler and polarization oracles as high-value regression tests, not evidence for speculative formula patches.

No production-code change is authorized by this integration note.

---

# Final Clean Pass — R8 Minor-Edit Integration

R8 returned **PASS WITH MINOR EDITS**. This final clean pass applies only document-hygiene edits: it removes a duplicated R2.5 header, removes doubled horizontal rules, fixes stale R5.0 Doppler wording so that the accepted `(g v_b)'` convention is no longer phrased conditionally, and fixes minor LaTeX rendering artifacts in the R5.0 CAMB-introspection identity. No substantive physics or code-mapping verdict is changed from the R7-corrected/R8-passed state.

---

# Appendix X — External LLM-cycle Errata (R8/R9/R10 Retracted)

**Status:** historical record only. Conclusions in this appendix have been retracted. Retained for traceability and as a methodological lesson.

This appendix documents a parallel three-cycle external-LLM audit run that occurred between R6 and the R7 independent-audit integration above. The parallel run reached **the opposite conclusion on AF-1** from the R7 audit: it identified BASS's Doppler `(g v_b)'` as missing a `1/k` factor and produced three iterative R-rounds (R8/R9/R10) refining that incorrect verdict. The authoritative R7 independent audit (above) supersedes this run on every disputed point; the present appendix preserves the false trail because the methodology lesson is non-trivial.

## X.1 Summary of the retracted claim chain

The parallel audit run claimed:

1. BASS's `flrw_bessel_projector.py:453` uses `doppler = np.gradient(gvb, eta_grid, edge_order=2)` without dividing by `k`.
2. Canonical CAMB Lewis–Challinor 2006 form is $(g v_b)'/k$.
3. Therefore BASS is "short a factor of $1/k$" and a one-line code fix appending `/ k` is required.

The supporting evidence cited was:

- `ver2_native_integrator.py:3086`: `baryon_labels=("delta_b", "v_b", "v_e", "drag_lock_residual")` — slot 1 is labelled `"v_b"`.
- `ver2_native_integrator.py:3047`: predictor-corrector forcing `forcing = 3 * drag * theta_1` — interpreted as evidence that the stored `v_b` is dimensional physical velocity, because (it was claimed) MB-95 divergence convention would require `3 * k * drag * theta_1`.
- `ver2_native_integrator.py:2979`: slip term stored as `3*theta_1 - v_b`.

## X.2 Why the chain was wrong

The R7 independent audit (now integrated above) and a direct re-reading of `seed_compatibility.py:210` (`theta_common = amp / 3.0`) show that BASS's `v_b` is the **dimensionless** quantity $v_b = \theta_b/k$, not dimensional physical velocity. The smoking-gun line is:

```python
# seed_compatibility.py:210, build_flrw_regular_seed
return RegularSeedState(
    amplitude=amp,
    delta_gamma=amp,
    delta_baryon=amp,
    delta_cdm=amp,
    delta_nu=amp,
    theta_common=amp / 3.0,           # <-- no k factor
    descriptor=descriptor or RegularSeedDescriptor(),
)
```

`theta_common` is set to `amp / 3.0` with **no factor of $k$ anywhere**, and `delta_baryon = amp` is dimensionless by construction. Therefore `theta_common` is itself dimensionless. The super-horizon adiabatic relation $\delta_b = 3 v_b/k \cdot k = 3 v_b$ in dimensionless form gives `theta_common = delta_baryon / 3 = amp / 3`, consistent only with `theta_common` storing $v_b = \theta/k$, not $\theta$ itself.

The labels `"v_b"` and `"theta_b"` are both used in different parts of the BASS codebase (`baryon_labels` tuple uses `"v_b"`; the seed-IC dict uses `"theta_b"`) for the *same dimensionless variable*. The label inconsistency was the trap. The retracted run mistook the labels for type information.

The EOM-forcing argument (`forcing = 3 * drag * theta_1` lacking a factor of $k$) is consistent with the dimensionless convention as well: in that convention $v_\gamma = 3\Theta_1$ with all quantities dimensionless, so the forcing is `3 * drag * theta_1` regardless of whether one calls the variable $v$ or $\theta$. The retracted run treated this as discriminating evidence when it discriminates nothing.

## X.3 Round-by-round retraction notice

| Round | Title | Status |
|---|---|---|
| R8 | "Audit-cycle response (post-R7, 2026-04-25)" | RETRACTED — AF-1 verdict was wrong; the polter eigenvalue correction (R2 §3 inline; eigenvalues $\{1, 3/10\}$ rather than $\{9/10, 0\}$) survives as a real correction, see Appendix Y §Y.1 |
| R9 | "Second-cycle audit response (post-second-audit, 2026-04-25)" | RETRACTED — the auditor accepted the wrong AF-1 verdict; the $\dot\kappa \approx 100$ Mpc⁻¹ correction (auditor flagged 1000× unit error; correct values $\sim 0.06$–$1$ Mpc⁻¹) survives as a real correction in the P1.5-A reconstruction, see Appendix Y §Y.2 |
| R10 | "Third-cycle audit response" | RETRACTED — the auditor's "Doppler<0.5%→anchor unaffected logic incomplete" flag was technically correct under the false premise that AF-1 was real; with AF-1 retracted, the rerun-required argument is moot |

## X.4 Methodology lesson

Three external-LLM audit cycles failed to catch the AF-1 dimensional mis-identification because **all three reviewers shared the assumption that variable labels carry type information in BASS's codebase**. The retracted run used the `"v_b"` label as evidence; all three reviewers validated that reading. The R7 independent audit (a fourth, parallel reviewer) caught the error by reading the seed-IC code path directly and noticing the missing $k$ factor in `theta_common = amp / 3.0`.

The methodological implication: convention/dimensional questions in mature codebases require **direct inspection of the construction site of the variable** (here: the regular-seed builder), not just the consumption site or the label text. Cross-cycle external review with shared assumptions does not surface this class of error; only an independent reviewer with a different reading path does.

This appendix preserves the failed chain because removing it would erase the methodological evidence and falsely suggest the integrated document was reached without dispute.

## X.5 What the retracted run got right

Not every retracted-cycle finding was wrong. The following corrections survive and are kept in Appendix Y:

- **Polter (T,E) eigenvalue derivation** — eigenvalues $\{1, 3/10\}$, with $\Pi^{\rm PSTF}$ as the slow eigenmode at rate $(3/10)\Gamma_T$. Originally claimed as $\{9/10, 0\}$; corrected algebraically. (Appendix Y §Y.1)
- **$\dot\kappa$ unit/magnitude reasoning** — recombination-zone $\dot\kappa$ is $\sim 0.06$–$1$ Mpc⁻¹, not the $\sim 100$ Mpc⁻¹ mistakenly used in an early draft of the coupled residual analysis. (Appendix Y §Y.2)
- **$k_{\rm eq}$ formula** — $k_{\rm eq} \approx 0.073\,\Omega_m h^2$ Mpc⁻¹ with the standard coefficient; mistakenly stated as $0.0104$ in an early draft. (Appendix Y §Y.3)
- **Operator coefficient corrections per lowell §6** — the displayed lowell §6 coefficients for T2/T3/T7/T8/T9 are now reflected in the master code-mapping (R6 above already had this).

These are real algebra/numerics catches, not retracted.

---

# Appendix Y — Supplementary Analytical Notes

**Status:** supplementary. Not part of the R6-certified verdict chain. These notes were developed in the retracted parallel cycle and contain genuinely new analytical content not duplicated in R1–R6 above. They are preserved here because the analysis itself is sound; only the conclusions about AF-1 in the parallel cycle were wrong.

## Y.1 Polter (T,E) eigenvalue derivation

The Thomson collision sub-block at $\ell = 2$ in the $(\Theta_2, E_2)$ basis, per lowell §9.2 / CL2000-II eq. 12:

$$
\frac{D\Theta_2}{d\tau}\bigg|_{\rm coll} = -\Gamma_T\Bigl[\tfrac{9}{10}\Theta_2 + \tfrac{\sqrt 6}{10}E_2\Bigr],
\qquad
\frac{DE_2}{d\tau}\bigg|_{\rm coll} = -\Gamma_T\Bigl[\tfrac{\sqrt 6}{10}\Theta_2 + \tfrac{2}{5}E_2\Bigr].
$$

Writing $d/d\tau (\Theta_2, E_2)^T = -\Gamma_T M (\Theta_2, E_2)^T$ with

$$
M = \begin{pmatrix} 9/10 & \sqrt 6/10 \\ \sqrt 6/10 & 2/5 \end{pmatrix},
$$

the eigenvalue problem is solved by:

- $\det M = (9/10)(2/5) - (\sqrt 6/10)^2 = 18/50 - 6/100 = 36/100 - 6/100 = 30/100 = 3/10$
- $\operatorname{tr} M = 9/10 + 2/5 = 13/10$
- Characteristic equation: $\lambda^2 - (13/10)\lambda + 3/10 = 0$
- Discriminant: $(13/10)^2 - 4(3/10) = 169/100 - 120/100 = 49/100$
- Eigenvalues: $\lambda = (13/10 \pm 7/10)/2 \in \{1,\ 3/10\}$

**Eigenvectors**:
- $\lambda = 1$ (fast): $\propto (\sqrt 6, 1)$, i.e., $\sqrt 6\,\Theta_2 + E_2$ relaxes at the full Thomson rate $\Gamma_T$.
- $\lambda = 3/10$ (slow): $\propto (1, -\sqrt 6)$, i.e., $\Pi^{\rm PSTF} = \Theta_2 - \sqrt 6\, E_2$ relaxes at $(3/10)\Gamma_T$.

**Numerical verification** (executed during this analysis):
```
M = [[0.9, sqrt(6)/10], [sqrt(6)/10, 0.4]]
eigenvalues: [0.3, 1.0]
eigenvector for lambda=0.3: (1, -sqrt(6))/norm   [matches Pi^PSTF]
eigenvector for lambda=1.0: (sqrt(6), 1)/norm    [matches Pi^fast]
```

**Physical significance**: the polter $\Pi^{\rm PSTF}$ that sources E-mode polarization at recombination is the **slow** eigenmode at rate $(3/10)\Gamma_T$, slower than the full Thomson rate by a factor of $\sim 3$. This slower relaxation is what allows the polarization quadrupole to persist long enough during the recombination tight-to-loose-coupling transition for observable E-mode generation. The "$9/10$" rate that appears in informal discussions of the polter is the **decoupled** $\Theta_2$-only diagonal rate (i.e., setting $E_2 \equiv 0$ artificially gives $D\Theta_2/d\tau = -(9/10)\Gamma_T \Theta_2$), distinct from the coupled-system eigenvalue.

This derivation is supplementary to R6's polter-acceptance verdict; R6 treats the convention $\Pi = \Theta_2 - \sqrt 6 E_2$ and the source $g\Pi/4$ as accepted, without requiring the eigenvalue analysis. Y.1 documents *why* this combination is the correct relaxation eigenvector and corrects an informal misstatement that occasionally appears in working notes.

## Y.2 Recombination-zone $\dot\kappa$ values

For numerical estimates that need the conformal-time optical-depth derivative, recompute from first principles rather than rely on memory:

$$
\dot\kappa(\eta) = a(\eta)\, n_e(\eta)\, \sigma_T,
$$

with $\sigma_T = 6.6525 \times 10^{-25}\,{\rm cm}^2$ and $n_e = x_e\, n_b$ where $n_b$ is the baryon number density. Standard $\Lambda$CDM ($\Omega_b h^2 = 0.0224$, $h = 0.674$) gives $n_b^{\rm today} \approx 2.5 \times 10^{-7}\,{\rm cm}^{-3}$, and the values across the recombination integration window are:

| Epoch | $z$ | $x_e$ | $\dot\kappa$ (Mpc⁻¹) | Regime |
|---|---|---|---|---|
| $\eta = 200$ Mpc | $\sim 1500$ | $0.8$ | $\sim 0.93$ | Deep tight coupling |
| $\eta_{\rm init} = 261$ Mpc | $\sim 1200$ | $0.5$ | $\sim 0.37$ | TC exit begins |
| $\eta_* = 282$ Mpc | $\sim 1090$ | $0.1$ | $\sim 0.06$ | Visibility peak |
| $\eta = 300$ Mpc | $\sim 1000$ | $0.02$ | $\sim 0.01$ | Free-streaming |

(Conformal time, in Mpc with $c = 1$.) These values matter for any back-reaction or tight-coupling-strength estimate around recombination and should be used in preference to memory-based estimates.

## Y.3 Matter-radiation equality scale

For matter-radiation equality, the canonical formula is

$$
k_{\rm eq} \approx 0.073\,\Omega_m h^2\,{\rm Mpc}^{-1}
$$

(Dodelson, *Modern Cosmology* 2nd ed. eq. 7.31). For standard $\Lambda$CDM with $\Omega_m h^2 \approx 0.143$, this gives $k_{\rm eq} \approx 0.010$ Mpc⁻¹, and $\eta_{\rm eq} \approx 110$ Mpc.

BASS's Round-15 P0 $\eta_{\rm init} = 261$ Mpc is therefore post-equality by a factor of $\approx 2.4$, which is the structural reason the four-cell low-$k$ anchor empirical agreement holds: by $\eta_{\rm init}$, sub-horizon modes ($k > k_{\rm eq}$) have already settled to their post-equality $\Phi$ values and no longer oscillate, so the constraint-reconstructed potentials in `tier_b_source_extraction.py:275-306` see a slowly-varying input. For modes with $k \lesssim k_{\rm eq}$ (super-horizon at $\eta_{\rm init}$), the standard adiabatic super-horizon transfer factor of $9/10$ has already been imprinted by $\eta_{\rm init}$.

This is an analytical context note for R3.5; R3.5 itself uses the empirical Round-15 P0 ratios without requiring this background.

## Y.4 Coupled monopole-dipole-quadrupole residual hierarchy (informal)

If one defines $\delta\Theta_\ell \equiv \Theta_\ell^{\rm BASS} - \Theta_\ell^{(N)}$ as the frame-residual between the BASS PSTF tower and the Newtonian-gauge target, the system satisfies

$$
\delta\Theta_0' + \tfrac{k}{3}\delta\Theta_1 = \dot\Phi,
$$

$$
\delta\Theta_1' - \tfrac{k}{3}\delta\Theta_0 + \tfrac{2k}{3}\delta\Theta_2 = -\tfrac{k}{3}\Psi - \dot\kappa\bigl[\delta\Theta_1 - \tfrac{1}{3}\delta v_b\bigr],
$$

assuming that the *intended* relation $\Theta_\ell^{\rm BASS} = \Theta_\ell^{(N)}$ holds for $\ell \ge 1$ at IC by the Stewart-Walker argument and that any deviation accumulates only through the missing metric sources. Around recombination with $\dot\kappa \in [0.06, 0.93]$ Mpc⁻¹ across the integration window and $|\Psi| \sim 10^{-5}$, $k = 10^{-2}$ Mpc⁻¹, the dipole quasi-static balance gives

$$
|\delta\Theta_1|_{\rm at\,\eta_*} \sim \frac{k|\Psi|}{3\dot\kappa_*} \sim \frac{10^{-2} \cdot 10^{-5}}{3 \cdot 0.06} \approx 6 \times 10^{-7},
$$

and the back-reaction onto $\delta\Theta_0$ over the integration window of width $\sim 21$ Mpc is

$$
|\delta\Theta_0^{\rm back}(\eta_*)| \sim \frac{k}{3}\,|\delta\Theta_1|\,\Delta\eta_{\rm rec} \sim \frac{10^{-2}}{3}\cdot 6\times 10^{-7}\cdot 21 \approx 4\times 10^{-8}.
$$

Compared to the leading $|\Phi(\eta_*) - \Phi(\eta_{\rm init})| \sim 5\%\cdot|\Phi_{\rm init}| \sim 5\times 10^{-7}$, the back-reaction is **of order $\sim 8\%$ of leading** in the worst case — about $1$–$2$ orders of magnitude below leading, not $4$ orders below as a draft erroneously claimed.

This estimate uses representative values for $\Psi$, $\dot\kappa$, and the integration window; a tight bound requires integration against the actual `visibility_history` at the specific $(k, \ell)$ anchor cells. The estimate confirms qualitative subdominance of the back-reaction but does **not** by itself resolve the R3 monopole contract — it operates inside the $\Theta_\ell^{\rm BASS} = \Theta_\ell^{(N)}$ working assumption, which is exactly what R3 says cannot yet be certified.

The coupled-hierarchy analysis is therefore *consistent with*, but not *evidence for*, the no-correction option in R3.4.4. R3.4.4's verdict that the source contract is unresolved supersedes this estimate.

## Y.5 Status of Appendix Y

Y.1, Y.2, Y.3, Y.4 are genuinely new analytical content not duplicated above. They were developed in the retracted parallel cycle but stand on their own merits. They do not modify any R6 verdict.

The retracted P1.5-D (tilt + m=±2 normalization) is **not** preserved here because R4.3 above (FINAL_CLEAN's main body) supplies a more general and more precise Wigner-coupling treatment that subsumes anything P1.5-D had to say.
