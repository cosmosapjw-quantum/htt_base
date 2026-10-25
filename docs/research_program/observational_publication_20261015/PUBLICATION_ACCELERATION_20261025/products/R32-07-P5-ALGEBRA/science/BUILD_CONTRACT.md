# Literal build contract for R32-07-P5-ALGEBRA

The scientific content is frozen in `science/manuscript.md` and this contract. This is the scientific author's handoff to the controller-dispatched Sol/high builder. The builder owns the product's implementation, generated arrays/tables/figures, TeX plumbing, bounded validation and factual build report; it must not alter scientific formulas, domains, acceptance limits or prose conclusions. The science author owns only `science/`. There is one production writer at a time. No children, Git mutation, campaign-state mutation, ODE evolution, native solver, broad CAS replay, external atlas acquisition or source edits are authorized.

## Identity and exact sources

- Campaign identity: `2b9c0b11dab33758e0ad8c7711376ae29949a345e111df7820fcc8c7cac75ea4`, existing campaign R23-whole-42-solver-free.
- Task: `R32-07-P5-ALGEBRA`, attempt 1, execute phase.
- Packet: `1f2400c98c81ce56b5964beb1ba8c0c0b5d00452049470f22b188ed5bdd96154`.
- Input: `sha256:d6d2dc2c653bf3f611d0272d22cceb8562e1c277c76bdda1f50fbc91bc420a71`.
- Task-spec identity: `11ead068de6c2f1d1aea1adea92ef6b6fb135312c51dd47813828cd0da7544e5`.
- Frontier identity: `27b1e5df1ffbe44e31a69772db64138b0c2cc6902c009cef87d4b57cc4f3a508`.
- Preparation contract: `/mnt/extdrive/workdir/htt_open_data/r35_p4_p5_source_contract_intake/P5_BUILD_CONTRACT.md`, SHA-256 `fb65137ec8263f367554d0528c68ba1dd3b42ac0940141da8b7df9ac111f0733`.
- Preparation identity list: `/mnt/extdrive/workdir/htt_open_data/r35_p4_p5_source_contract_intake/P5_SOURCE_IDENTITIES.json`, SHA-256 `5587eecdc83ce4a0c43a53177f792dc425741bf707753a2ff4f784f811e7de92`.
- Read the actual ACK at `/mnt/extdrive/workdir/htt_open_data/r35_publication_acceleration_controller/P5_ACTUAL_ACK_GO.json` and the controller's builder-specific ownership message before writing.

All ten entries of the preparation identity list were hash-verified by the scientific author. The consumer must verify the list's own hash, its source entries, the preparation contract, and the repository EVIDENCE_MANIFEST hash. Source mismatches are immutable-input failures: retain the raw failure and return for interpretation. Do not overwrite them. Preserve copies of the exact source-identity list and preparation contract in the built product's `inputs/` so the consumer can run from retained repository source paths without the external preparation directory. They remain preparatory inputs, not new acceptance receipts. Include the source contributor `/root/r35_p4_p5_source_contract_intake` and science author `/root/rc_1f2400c98c81ce56` among authors/contributors excluded from independent review.

Use the existing repository checkout. Preserve all files outside the product. Build from the declared retained sources; no new physical source or probability law is needed. Reuse historical metric and source checks. Do not report the preparer's or scientific author's requested Astra/xhigh profile as observed runtime: their observed runtime is `UNKNOWN`.

## Required outputs and single bounded build

Implement a runnable algebraic consumer `build_product.py` at the product root. A single documented invocation from the repository root must regenerate the numerical artifacts and figures, and expose a validation-only mode to verify them without altering source inputs. Choose installed Python plotting/numerical tools and a locally available PDF route; no environment installation or repository-wide test suite is needed. The exact interpreter and commands actually used belong in the build report and raw logs. Preserve first failures. A code-only correction that leaves this scientific contract unchanged is within builder scope; scientific/tolerance/domain ambiguities return to the scientific author.

Produce:

1. `arrays.npz` with the arrays below, `joint_image.csv` with full row identities and all tensor/vector components, and `generated_table.csv` with the specified selected rows.
2. Six figures, each as PDF and a readable PNG preview, under `figures/`, with captions given below.
3. A fully rendered `manuscript.tex` and `manuscript.pdf` using the exact scientific prose/equations in `science/manuscript.md`; conversion/escaping/line-breaking are mechanical. Integrate the generated table and the six figures at the named sections. Keep novelty notes out of the manuscript. If the PDF route is unavailable, report the exact blocked tool/input rather than inventing a build.
4. `RESULT.json` with candidate-only scope, source binding, numerical outcomes and undefined sectors; `CLAIM_SOURCE_MAP.json` faithfully serializing the scientific claim table; `BUILD_REPORT.md`; `raw/` logs and a factual build receipt.
5. A finite artifact inventory with relative paths and SHA-256 identities consumed by the candidate/return, excluding itself and eventual controller-return/review files from its own identity preimage. Root will bind the actual candidate. Do not claim acceptance from inventory generation.

The science author will consume the completed build and write the controller return before the separate formal review. Set `acceptance_passed=false`, `original_acceptance_passed=false`, `promotes_original_acceptance=false`, `qualified_product=null`, and `proposed_qualified_product="bianchi_algebra_note"`. Use `status="CANDIDATE_BUILT_PENDING_INDEPENDENT_REVIEW"` only if all required outputs and checks actually succeed. Failed outputs remain failed; do not mark a partial gap report as the product. No 42-node completion is gained by this candidate.

## Literal algebra and domain behavior

All values are dimensionless binary64 unless explicitly documented otherwise. Variable names below are semantic, not a required coding style. Implement the manuscript formulas exactly:

- Domain: finite inputs; `0 < K <= 1`, `abs(beta) < 1`, `0 <= w <= 1`, `0 <= u <= 1`. `K>1` is `EMPTY_DOMAIN`; `K<=0`, `abs(beta)>=1`, nonfinite inputs, invalid (w) or (u) are `OUTSIDE_DOMAIN`. Do not replace invalid values by zero. Each invalid-domain return needs its status and reason. The display grids never approach machine singularities.
- `A=(1+w)^2*beta^2/(4*K*(1-beta^2)^2)`; `B=(1+w*beta^2)/(1-beta^2)`; `D=1-K`; `Omega_max=2*D/(B+sqrt(B*B+4*A*D))`.
- `Omega=u*Omega_max`; `z_s=(1+w)*Omega*beta/(2*sqrt(K)*(1-beta^2))`; `Sigma2=z_s*z_s`; `Omega_n=B*Omega`; `Omega_Lambda=D-B*Omega-A*Omega*Omega`. Keep the computed residual and its analytic status; do not clip a roundoff-level negative boundary value into another tuple.
- `E_tilt=(1+w)*Omega*beta^2/(1-beta^2)`; `flux=[0,0,(1+w)*Omega*beta/(1-beta^2)]`; `pressure=w*Omega+E_tilt/3`; `pi=E_tilt*diag(-1/3,-1/3,2/3)`; `shear=z_s*diag(-1,-1,2)`; `beta_chart=[0,0,beta]`.
- `Omega==0` has `matter_velocity_status="UNDEFINED_ABSENT_MATTER"`, physical beta null/masked, with `beta_chart` retained as a chart coordinate. Fluid tensor and flux are exactly zero, (z_s=0); this is a defined zero stress, not a fabricated missing field. For `Omega>0`, matter velocity is defined.
- Both full tensors are STF in the normal orthonormal axes `(x,y,z)`. Preserve signed `z_s`, all nine tensor components, and all three vector components. Do not store only norms or positive diagonal magnitudes. Positive `beta` corresponds to positive `z_s`.
- No matter-frame vorticity computation is specified. Store `normal_vorticity=0` with `HYPERSURFACE_ORTHOGONAL` and `matter_vorticity_status="NOT_DETERMINED"` with null value. Likewise (x_C,Q,F,\Pi,G_F) are null with the missing inputs listed in the claim map.

### Required finite arrays

Use the following grids without random sampling or numerical integration:

A. Heatmaps: (w=(0,1/3)); (K_j=0.02+0.96j/160), (j=0,ldots,160); (eta_k=-0.9+1.8k/180), (k=0,ldots,180). Evaluate (u=1) and keep (Omega_{max},z_s,Sigma^2,Omega_n,Omega_Lambda), full shear/stress/flux and status arrays. The physical meaning is the zero-(Lambda) boundary, allowing tiny residuals within the stated tolerance; keep raw values.

B. Joint curves: (K=(0.05,0.2,0.5,0.8)); (w=(0,1/3)); (eta=(0,\pm0.2,\pm0.5,\pm0.8)); (u=(0,1/4,1/2,3/4,1)). This is 280 full tuples. Store `K,w,beta_chart,u,Omega,Omega_max,z_s,Sigma2,Omega_n,Omega_Lambda,E_tilt,pressure`, all nine components of `shear` and `pi`, all three of `flux` and `beta_chart`, plus `matter_velocity_status`. The (u=0) rows preserve distinct chart labels but are physically vacuum with undefined matter velocity.

C. Fixed matter: (Omega=(0.1,0.3,0.6)), (w=(0,1/3)), and the K grid in A. Put (C=(1+w)Omega,a=C^2/(4K),b=C+a,d=1-K-Omega). For (d<0) mark `EMPTY_DOMAIN`, store a masked/null bound, and plot a gap, never zero. For (d\ge0), set (t_{max}=2d/(b+\sqrt{b^2+4ad})) and (v_{max}=\sqrt{t_{max}/(1+t_{max})}). Evaluate the boundary tensor tuple at both signs when (v_{max}>0), and at zero otherwise, directly using this fixed (Omega). Do not interpolate it from A or cap it at 0.9.

D. Envelopes: K grid in A; (w=(0,1/3,1)); compact (v_{max}=0.9). Set (r=(1+w)v_{max}/(1+wv_{max}^2)), (z_{max}=r(1-K)/(\sqrt{K+r^2(1-K)}+\sqrt K)), and compact squared envelope (z_{max}^2). Store also ((1-\sqrt K)^2), labelled `ULTRARELATIVISTIC_SUPREMUM_NOT_FINITE_BETA_STATE` for (0<K<1). Keep an endpoint case (K=1) separately. Verify agreement with (sqrt A\Omega_{max}), not only internal reuse of the same envelope formula.

E. Histories: (	au_j=j/200), (j=0,ldots,200), (L=(1/50)\operatorname{diag}(-1,-1,2)), (alpha=4/5). Store full arrays `B_A=tau*L`, `B_B=((1-alpha)*tau+alpha*tau^2)*L`, `shear_A_over_H=L`, `shear_B_over_H=(1-alpha+2*alpha*tau)*L`. The integral is the explicit primitive B, never numerical quadrature or an ODE. For (mu_j=-1+2j/400), (j=0,ldots,400), store both endpoint temperatures computed from each endpoint tensor as ([\exp(2b_x)(1-\mu^2)+\exp(2b_z)\mu^2]^{-1/2}), and the independent explicit formula in manuscript (27). Axisymmetry supplies all azimuths; the proof supplies all directions.

F. Error geometry: (r_j=0.02j/100), (j=0,ldots,100). Store separation (d_\sigma=\alpha\sqrt6\epsilon), threshold (r_*=d_\sigma/2), margin (d_\sigma-2r_j), and statuses `DISJOINT`, `TOUCHING`, `INTERSECT` using the exact analytical inequality. Add a separate exact-form threshold row identified symbolically, rather than relying on a floating equality branch on the grid. Do not attach p-values or confidence labels.

### Generated table

Select the eight (u=1,eta=+0.5) joint-image rows for (K=(0.05,0.2,0.5,0.8)) and (w=(0,1/3)). Columns: (K,w,Omega_{max},z_s,Sigma^2,Omega_n,Omega_Lambda). Emit 10-significant-digit CSV values and six-significant-digit manuscript values; avoid rounding a raw tiny residual into a claimed exact floating computation. The caption states that the boundary has analytically (Omega_Lambda=0) and lists the actual largest absolute residual from the validation record. These are parameter choices, not measured cosmological values.

## Literal captions and placement

1. Section 3, `figures/domain`: “Instantaneous LRS Bianchi V boundary images for one perfect fluid and nonnegative cosmological constant. Columns show the maximal rest-density parameter and its signed normalized shear at Ω_Λ=0; rows use (w=0) and (w=1/3). The displayed support is (0.02\le K\le0.98), (-0.9\le\beta\le0.9). The sign follows the oriented momentum constraint.” Use a 2 by 2 panel layout with K horizontal and beta vertical. Render math notation conventionally.
2. Section 3, `figures/joint_image`: “Coupled shear–density image curves at fixed curvature, tilt and equation of state. Each curve varies (u) from zero to one in (9), with signed mirror branches displayed. The terminal points have Ω_Λ=0. Scalar projection intervals cannot be recombined independently.” Use (\Omega) horizontal and (z_s) vertical, separate w panels, consistent color for K and line style for |β|; label zero branch. Plot the five specified u vertices connected by straight lines, which is exact because (z_s) is linear in (Omega).
3. Section 4.1, `figures/fixed_matter_tilt`: “Exact allowed tilt speed at fixed rest-density parameter and curvature. Curves use Ω=0.1, 0.3, 0.6 and the indicated equation of state. The boundary saturates the normal constraint with Ω_Λ=0. Gaps mark the empty domain (K+\Omega>1); the line at 0.9 marks only the heatmap display support.” Use K horizontal, bound vertical, separate w panels.
4. Section 4.2, `figures/shear_envelope`: “Sharp compact-support shear envelopes at |β|≤0.9 for (w=0,1/3,1), compared with the ultrarelativistic supremum ((1-\sqrt K)^2). For (0<K<1) the dashed limiting curve is approached at finite normal energy and vanishing rest density as |β|→1; it is not an attained finite-timelike state.” Use K horizontal and Sigma squared vertical; distinguish dashed supremum.
5. Section 5, `figures/history_temperature`: “Exact kinematic Bianchi I histories with equal final radiation. The signed (zz) shear components and (b_{zz}) histories differ, while their full final axisymmetric temperature functions coincide. The endpoint shear ratio is (9/5). The radiation equality follows from common endpoint deformation and collisionless transport, without an Einstein-perfect-fluid evolution assumption.” Use three panels for shear_zz/H versus tau, B_zz versus tau, T/T0 versus mu. Both coincident curves must remain represented in the legend (e.g. solid line and sparse markers).
6. Section 5, `figures/error_geometry`: “Deterministic separation of the history pair by an additional endpoint shear measurement. Equal closed Frobenius-error balls are disjoint for (r_{\mathrm{err}}<\alpha\sqrt6\epsilon/2), touch at equality, and intersect above it. The radius is a deterministic tensor-error allowance with no probability or confidence interpretation.” Plot the signed separation margin versus r and indicate the analytic threshold.

## Required checks and stopping rules

Record actual residual maxima and counts. The full-domain proof is manuscript Propositions 1–3, not the finite grid checks. Every affected generated array must satisfy:

| Check | Absolute tolerance or exact behavior |
|---|---|
| Normal Hamiltonian: (K+\Sigma^2+\Omega_n+\Omega_\Lambda-1) | (2\times10^{-12}) |
| Signed momentum: (2\sqrt K z_s-f_z) | (2\times10^{-12}) |
| STF traces and full norm identities | (2\times10^{-12}) |
| (Omega_{max}) polynomial: (A\Omega_{max}^2+B\Omega_{max}-D) | (2\times10^{-12}) |
| Fixed-(Omega) boundary Hamiltonian residual | (5\times10^{-12}) |
| Beta mirror parity: shear/flux odd, density/pressure/stress/Sigma2 even | (2\times10^{-12}) |
| Compact envelope agrees with (sqrt A\Omega_{max}) | (2\times10^{-12}) |
| Timelike nonzero-shear samples below the limiting envelope | no violation exceeding (2\times10^{-12}); label theoretical strictness from proof |
| (eta=0,K=1,Omega=0) branches | exact analytic semantics above, no forbidden divisions |
| Invalid (K=0,-0.1; |eta|=1,1.01; w=-0.1,1.1; u=-0.1,1.1), NaN/Inf | explicit outside-domain status or exception, never zero-fill |
| (K=1.1) and fixed (K+Omega>1) | EMPTY_DOMAIN |
| History endpoint deformation equality, temperature equality and explicit map | (2\times10^{-14}) |
| History shear endpoint ratio (9/5), squared norm ratio (81/25) | (2\times10^{-14}) |
| Exact angular checks: equator (e^epsilon), pole (e^{-2epsilon}) | (2\times10^{-14}) |
| History STF traces, full Frobenius separation | (2\times10^{-14}) |
| Error-radius endpoints and symbolic touching threshold | correct deterministic status, equality touches |

Include at least one deliberately negative (H_X/H=1+2z_s) accepted tuple, if one occurs on the declared grid; it confirms that mean expansion has not been replaced by three-direction expansion. If the grid has none, report that and use the explicit contract-approved edge tuple (K=0.02,w=1,\beta=-0.9,u=1). This is an algebraic check, not an evolution.

Use (K=1,eta=0.5,w=0,u=1) as the vacuum endpoint; use (K=0.2,eta=0,w=1/3,u=0.5) as a nonzero-density no-tilt branch. Do not globally use (eta=0) to infer shear freedom outside this sector. In general boundary roundoff is classified by the analytic parameterization; no hidden clipping or relaxed tolerance is allowed. A failure beyond these limits stops scientific completion and returns the raw case for interpretation.

Before claiming a PDF build, verify that the actual PDF exists and all six figure/table references resolve, then inspect rendered pages sufficiently to catch clipping, missing glyphs or unreadable plots. Report the exact build process and any warnings. A successful PDF build remains separate from scientific review.

## Required result semantics

Use `owner="manuscript"`, `scope="conditional instantaneous LRS Bianchi V algebra and exact kinematic Bianchi I radiation equivalence"`, and `claim_tier="conditional"` (the live repository `common/contracts.py` vocabulary). Use `transfer_source="none"` with `radiation_map="explicit analytic collisionless Bianchi I endpoint map"`. Set sky support to `NO_EMPIRICAL_SKY_ANALYTIC_FULL_SPHERE`, covariance/null to `NOT_APPLICABLE_DETERMINISTIC_NO_PROBABILITY_LAW`, and statistical law to `NOT_SUPPLIED_NO_PROBABILISTIC_CLAIM`. Store the display support, all units/frames, actual source identities, exact command, candidate artifacts and known source HEAD. An unknown current execution/runtime identity remains unknown.

Results distinguish `LRS_V_INSTANTANEOUS_CONSTRAINT_IMAGE`, `BIANCHI_I_KINEMATIC_FULL_TEMPERATURE_NONINJECTIVITY`, and `BIANCHI_V_EINSTEIN_FLUID_HISTORY_PAIR_NOT_ESTABLISHED`. The last is a branch-local stronger claim, not a blocker to the first two conditional results. No native solver or ODE is run, and no full x/Q/F/Pi/G_F carrier is manufactured.
