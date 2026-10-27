# NEGATIVE_RESULTS

## N-001  Astrometric bound on the HTT shear tensor (H-3)

ATTEMPT: Use Gaia DR3 CRF3 / VLBA quasar proper motions through the E2 direction-drift law μ(n) = −H ⊥(S·n) to bound Ŝ_app independently of distances.
WHY_IT_WAS_TRIED: K03/K05 ask for a "nonradial response" and a "source-matched ω/curl response"; proper motions are the only nonradial kinematic observable.
RESULT: Law exists (Darling 2014; Marcori et al. 2018; validated T-04: rms H‖S‖_F/√5 = 0.22 μas/yr for ‖S‖_F = 0.0327). No usable bound in any regime.
WHY_IT_FAILED: (i) If S is the window-scale (≲ 300 h⁻¹ Mpc) kinematic shear measured by CF4, Gpc quasars are outside the sheared congruence and the distance-independent E2 response does not apply; galaxies inside the window have random transverse PV noise ≳ the signal and no μas/yr Gaia proper motions. (ii) If S is a global (Bianchi) shear, the astrometric reach (≈ 7 % VLBI now; ≈ 0.03 optimistic Gaia DR5) is 8–9 orders of magnitude weaker than the CMB bound (σ/H)_0 ≲ 1e−10 (Saadeh 2016). Gaia DR3 ℓ = 2 power is systematics-dominated (√P2^E ≈ 9 μas/yr).
WHAT_IT_RULES_OUT: astrometry as a route to K03's "independent source qualification" for the CF4-scale S; any plan to spend the cached 1.6 M-row CRF3 sample on an S bound. K03 can be closed with the literature law plus an explicit no-sensitivity statement. Vorticity via proper motions is observable only relative to a dynamical frame (unquantified, M-04).
WHETHER_TO_REVISIT: only if a Bianchi-scale (global) S were ever claimed at ≳ 1 % from other data (not the case).

## N-002  Second-order cosmography (𝔮_1) as the sole depth law for the H03 window dipoles (H-7)

ATTEMPT: Interpret the R32-03 depth-slope design column as Heinesen's O(z²) deceleration dipole 𝔮_1 and explain the 12-coordinate discrepancy T = 23.40 with it.
WHY_IT_WAS_TRIED: H04/V04 ask for a "physical radial law"; Heinesen 2021 supplies one with 25 d.o.f. at O(z²), including a·ω and σ·ω couplings.
RESULT: Already refuted as the sole law by the repo's own depth-slope result (rank 3, T_⊥ = 15.316 > τ = 12.59); functional form mismatched: a 𝔮_1 dipole grows ∝ z whereas the CF4 dipole falls with depth (2.19 ± 0.13 → 0.25 ± 0.25 ×10⁻², Kalbouneh 2026), as an observer-boost / shell-bulk-flow 1/z term does.
WHY_IT_FAILED: wrong dominant mechanism; vorticity couplings are products of small quantities with no observational content; a 9-parameter joint fit on 12 coordinates reaches τ by parameter count, not by mechanism.
WHAT_IT_RULES_OUT: 𝔮_1 as the explanation of the H03 residual; "vorticity through second-order radial terms" as a selling point. It remains a legitimate subdominant column in a joint design {constant dipole, 1/z_w boost/bulk, z_w 𝔮_1}, testable cross-dataset against Pantheon+ q_dip only.
WHETHER_TO_REVISIT: yes, as a column in the H-0 physical-null fit, not as a hypothesis of its own.

## N-003  HTT dipole coefficient d = −A/(cH) as a ΛCDM observable (H-1 dipole half)

ATTEMPT: Give the HTT local dipole d a ΛCDM referent as "gravitational acceleration of the peculiar-velocity field".
RESULT: Mis-specified. Heinesen's O(z) dipole is −e·a with a the 4-acceleration of the emitter congruence, which vanishes identically for geodesic dust (smoothed or not). The ΛCDM referent of an observed Hubble dipole is the observer boost relative to the source frame plus the shell bulk flow (Heinesen §5; Maartens et al. 2024), a 1/z effect.
WHAT_IT_RULES_OUT: reading the P1/H03 "calibration dipole" or "constant rate dipole" columns as a measurement of A_a; treating d as a physical acceleration in the P6 inverse without a non-geodesic source model.
WHETHER_TO_REVISIT: only for non-geodesic (pressure-supported or tilted) source congruences, which must then be modelled explicitly.

## N-004  (literature) Free second-order foreground-moment relaxation

ATTEMPT (R31, repo): seven-frequency identifiability with a free nine-moment class.
RESULT: target rank 0 (E-I06); Vacher et al. 2022 independently find the β-2 scheme degenerate with the CMB.
WHAT_IT_RULES_OUT: free second-order moment classes as a foreground model for low-ℓ identifiability; only bounded classes (H-5) or parametric separation remain.

## N-005  (procedural) Executing the public AniLoS code inside this session

ATTEMPT: smoke test `Anilos(...).tensor_solver(); alm_tensor(10)` after `pip install .` of the cloned repository.
RESULT: blocked by the session's execution policy on externally downloaded code (classy installed from PyPI succeeded; AniLoS install/run denied).
WHAT_IT_RULES_OUT: nothing scientific; the run must be done by the owner in an external environment (V-2 step 8).
