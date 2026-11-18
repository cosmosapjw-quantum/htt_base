# R67: Seven-axis observational fusion, theory stages R1–R10
Date: 2026-11-18. Baseline commit 1d833bbe0e6c70a42f2d0af002c2e6a7cfcd0593. Metric signature (-,+,+,+); sourceward n; physical c retained. Seven **research axes**, but only six paper tracks in the original P1–P6 DAG: tensorized five-variable inference, CMB low-ell morphology, radio dipole anomaly, beyond-FLRW kinematics, Bianchi morphology/classification, redshift-direction Hubble factor, and local boost versus global tilt. These seven observables are NOT seven independent likelihood factors.

## R1 — Research target
Construct one typed observable-to-physical likelihood with actual source/selection/cross-covariance checks, and test whether existing data can increase identification of a physical anisotropy rather than inflate signal-to-noise by multiplying correlated summaries. The first actual source-qualified experiment is **same-group CF4 distance-method subtraction**, which eliminates the common physical distance. A second independent observer-frame diagnostic uses actual Gaia-CRF3 proper motions. Stronger tilt/Bianchi inference is conditional.

## R2 — Internal history and primary references
- P1/R39/R58/R60: signed STF, five-view functional and full covariance; P2/R66: actual Commander PR3/PR4 radiation-stress proxy, DQ quotient, unresolved full Commander temperature MC; dipole/R65: NVSS peak/integrated count dipoles and common-source covariance.
- P6/R61: kinematic conditional confidence regions and finite-depth response; P5/R62: actual anisotropy-shape compatibility, survey-induced apparent noncommutativity, conditional Bianchi constraints; P3/R64: original 36D → 68/72D CF4 response and method-dependent H_D precision; P4/R63: observer/radiation/matter/normal frame, conditional compensated history has practically no CF4 discrimination power.
- Tully et al. CF4 https://arxiv.org/abs/2209.11238 already use same-group overlap for relative method zero points; this device is NOT novel. Stiskalek, Desmond and Lavaux (MNRAS 2026) https://academic.oup.com/mnras/article/546/2/staf2048/8436862 find apparent H0 dipole may capture local flow/systematics. Makarov, Heinesen and Schücker (CQG 2026) https://iopscience.iop.org/article/10.1088/1361-6382/ae76b3 already use Gaia degree-2 quasar proper motions for axisymmetric Bianchi I; their expected redshift trend was not securely confirmed. Bianchi polarization transfer comparators: https://arxiv.org/abs/0706.2075 and https://arxiv.org/abs/1605.07178 .
- The preceding read-only /mnt/extdrive/workdir census was truncated after 219,893 files (79 directories pending). Actual CF4 original tables, Gaia/ICRF, Planck/Cosmoglobe, Pantheon+ covariance, HSC mock, radio/HI and DESI/Fuji data exist, but presence ≠ source-qualified likelihood.

## R3 — Typed physical quantities and source provenance
Data types include CF4 log distance, true signed STF components, radio count dipole, observed Gaia proper-motion E/B field, CMB radiation stress and weak-lensing spin-2. Do not identify CMB photon stress with current matter shear, weak-lensing shear with congruence shear, Gaia observer *acceleration* with observer *velocity*, or an E/B proper-motion frame effect with cosmological vorticity. All of them require a source congruence, observer frame, epoch, map/selection operator and shared stochastic law. x,Q,Pi,F,G_F are dependent views of one admitted experiment, never multiplied. F denotes occupancy with declared measure/body; G_F needs actual radial depth.

## R4 — Distinct fusion hypotheses and ranking
A. **CF4 method-differential angular calibration × H(z,n) × local kinematics (P1+P3+P6):** same-group relative calibration quotient; executed, high leverage.
B. **Gaia/ICRF proper motions × CF4 bulk × radio counts × CMB observer frame (P4+P6+P2+dipole):** Gaia l=1 E/B executed; no physical joint history or covariance, so physical boost/tilt posterior blocked.
C. **CMB signed radiation-stress × tensor orbit × Bianchi geometry (P2+P5+P6):** existing R66/R62 outputs; source transport/recombination/polarized transfer required before a Bianchi family likelihood.
D. **HSC/KiDS lensing spin2 × source Hubble/redshift × spacetime kinematics:** local data confirmed; forward optical/shear map and cross-tracer covariance unresolved, so no joint fit made.
These are genuinely different data and failure mechanisms; only A and Gaia's distinct observer diagnostic B have executable models.

## R5 — Group-common-distance quotient, derivation
For group g, method m ∈ {FP,TF,SN}, write
  y_gm = μ_g^phys + f_g^T b_m + ε_gm,
  f_g = (1,u,u²,n_x,n_y,n_z, E_A:n n),
  u = [ln D_g - mean(ln D)] / sd(ln D).
μ_g^phys contains common geometry and common line-of-sight flow; b_m is method-dependent calibration, NOT physical shear. Fix b_FP=0 as method-label gauge, NOT an absolute distance anchor.

Given a declared within-group working C_g=diag(s_gm²), set v_g=C_g^(-1/2)1/||C_g^(-1/2)1|| and U_g^T v_g=0, U_g^T U_g=I. Then
  z_g=U_g^T C_g^(-1/2)y_g,   X'_g=U_g^T C_g^(-1/2)X_g.
Each group gives k_g−1 common-distance-free contrasts, and the normal information is F=sum_g X'_g^T X'_g. If all 3 methods present, TWO contrasts, not three independent pair differences. For d=(μ_TF−μ_FP, μ_SN−μ_FP),
  Cov(d)=[[s_TF²+s_FP², s_FP²],[s_FP²,s_SN²+s_FP²]].
Wolfram exact symbolic identity confirms covariance-aware differences equal the group nuisance-projection precision for arbitrary positive variances:
  W−W1(1^T W1)^(-1)1^T W = D^T(D C_g D^T)^(-1)D.
The nullspace of F consists of δb such that f_g^T(δb_m−δb_m')=0 for every observed pair. A connected method graph is necessary but not sufficient for full angular/radial coefficient rank: actual n and D coverage must span. In the observed CF4 group overlap, 998 groups including 92 triples give 1090 independent contrast coordinates, rank22/22 for TF and SN relative to FP, each 3 radial + 8 signed angular coefficients.

For a fixed observed z, Δln H_app=−ln(10)Δμ/5 is a **relative apparent** Hubble response, never direct physical Θ/3 or instantaneous shear.

## R6 — Adversarial inference and counterexamples
- One-method groups give zero contrasts; three-method groups give two independent coordinates. Treating three pair differences as independent spuriously boosts information (counterexample to naive product).
- The published CF4 method moduli are already registered by upstream joint calibration; the present diagonal C_g does **not** model their shared upstream errors. Gaussian naive χ² and group-wild Rademacher tails are diagnostic under declared symmetric independent-group score assumptions, not a calibrated cosmic-isotropy null.
- Method overlap selection spans unequal sky/distance footprints; nominal rank says nothing about direct physical identifiability. Radial polynomial 0–3 and large-residual controls therefore must be shown without using a posthoc selection to upgrade significance.
- The Gaia E/B design corresponds to quasar apparent angular drift with frame rotation and observer acceleration; its l=1 field is not a matter velocity gradient. Frame and redshift-qualified l=2 responses are separate.
- CMB release PR3 and PR4 are one sky; CF4 32D/68D and group original are same sources; unconditional independent multiplication is invalid.
- Bianchi labels require spatial structure, Einstein constraints, matter/tilt and photon polarization transfer, not signed STF eigenspectrum alone.

## R7 — Actual discriminating calculations
CF4 group table3/table4 identities and full source hashes are in RESULTS. Pair overlaps: FP–TF 694, FP–SN202, TF–SN286. With 32,768 group-Rademacher bootstrap draws and 3 radial nuisance coefficients: exploratory signed 8-angular contrast p-values (0.145076, 0.176051, 0.873539). Naive fixed-Gaussian 8-df χ² tails are (0.019972, 0.018136, 0.621494). Group-network 16-angular test is exploratory p=0.244896, naive working p=0.026805. Original 2048-draw and independent8192-draw diagnostics preserved. FP–TF radial-order degree0/1/2/3 wild p~0.0713/0.1367/0.1376/0.1508. This is a finite-model robustness result, not a finding of a cosmological anisotropy.
Gaia full CRF3 contains 1,614,173 PMs; after quality cuts 1,580,645. Actual l=1 E amplitude5.5672, B amplitude4.2895 μas/year, six-coefficient rank6/6. Sourcewise formal errors0.26–0.30 μas/year; 192-sky-patch diagnostic errors0.62–0.99 μas/year, with substantial north–south variations. These are observed reference-frame coefficients, NOT global tilt or spacetime ω. Files: RESULTS/CF4_METHOD_CONTRAST.json, RESULTS/GAIA_EB_FRAME.json, RESULTS/RADIAL_ROBUSTNESS.json.

## R8 — Scientific evaluation
A meaningful empirical negative/limiting result is available: apparent relative CF4 method angular differences with naive ~2% χ² tails do NOT persist as strong evidence under the declared group-wild law, while three-method connected relative coefficients remain algebraically identified. Gaia gives another actual observed vector field and shows a materially wider spatial-patch error diagnostic than sourcewise formal errors. Both show why adding sources or parameters does not itself establish an independent physical anisotropy. Same-group zero-point comparison (Tully) and quasar VSH (Klioner, Makarov et al.) are prior art. Independent novelty will require a calibrated cross-systematic covariance, a new shared physical transfer, or a same-source material improvement in bias/coverage, not representation/packaging alone. Current P1–P6 submission flags remain NOT_READY_TO_SUBMIT.

## R9 — Computational physical likelihood and identification
For common physical θ, separate probe means m_p(θ,γ_p) and covariance blocks C_pq. Do not set C_pq=0 for shared sources without evidence. Given J=d m/dθ and nuisance N, the local projected Fisher is
  F_eff=J^T[C^(-1)−C^(-1)N(N^T C^(-1)N)^+N^T C^(-1)]J.
A derived nonlinear physical φ(θ) is locally identifiable only when ker(J_eff) ⊆ ker(Dφ). Code in scripts/r67/likelihood_contract.py rejects a shared-source independent product without cross covariance, a frame/epoch/physical-referent mismatch, or an explicitly unqualified response. A user-supplied qualification flag does not certify actual source physics. MIO reports Q/Pi/F/G are downstream summaries, not a second likelihood.

## R10 — Bounded scientific decision
Priority1: Use original CF4 overlapping method groups plus the R64 source-window response to incorporate empirically justified method/selection covariance; close whether apparent directional H is stable or calibration-limited.
Priority2: Qualify Gaia proper-motion scanning/reference-frame systematics and VLBA correlation, then test if any source- and redshift-matched physical observer-versus-matter parameter actually gains Fisher rank. No boost-vs-tilt detection without a shared response.
Priority3: Qualify actual Commander scalar-temperature MC and one restricted physical Bianchi polarization/optical transfer before combining CMB stress with anisotropic history.
Data nodes are conditionally activated by measured insufficiency or missing source contracts; no automatic downloads, solver fabrication, PR3/PR4 double counting, or unbounded review loops. Original42 scientific gates and original six paper acceptance conditions remain unchanged.

### R6 code-review counterexamples (post-analysis)
The independent review established a four-row rank-1 duplicated radial-column case in which full-column QR incorrectly shrank the true score improvement 4 to 2.2222; the repair rejects deficient X0. A joint C=I4 with two probe marginals C1=C2=4I2 was previously accepted, although inconsistent; the repair enforces marginal block agreement and source covariance provenance. These are finite implementation/contract counterexamples, **not failures of the actual rank22 CF4 or rank6 Gaia calculations**. The one-line signed relation ΔlnH=−(ln10/5)Δμ and nonnegative RMS conversion were separated.
