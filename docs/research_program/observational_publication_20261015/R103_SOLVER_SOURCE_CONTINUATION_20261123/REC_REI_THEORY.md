# REC/REI transport in a tilted homogeneous background

## Physical definition and construction

Use an orthonormal normal tetrad with signature (−,+,+,+), synchronous normal proper time, increasing N=ln(a) and propagation direction e. The code takes beta=v/c. H and the geometric rates below use seconds⁻¹. In the native VER2 convention the spatial structure constants have the vector term a_i δ^k_j−a_j δ^k_i, so the divergence of a homogeneous spatial beta is −2 a·beta. The code's a has time-rate units (it includes c when the frame coefficients are per unit length).

Write D=Gamma n_H,rest. Baryon number conservation div(n_H,rest u_b)=0 gives
dD/dt+3HD−2D a·beta=0.
Thus d ln(D exp(3N))/dN=2(a/H)·beta. We integrate the PCHIP interpolant of this last signed source backward from today's hydrogen density. With a=0 or a·beta=0 the comoving normal-frame anchor is constant. The baryon congruence expansion is Theta_b=Gamma[3H + d ln(Gamma)/dt − 2 a·beta]. It obeys d ln(n_H,rest)/dτ_b=−Theta_b. For an independent implementation, the native projected 4D derivative of u_b supplies the expansion, shear and acceleration. The spatial legs of the rotation-free boost project the native covariant 4D shear and acceleration into the baryon-rest orthonormal basis. beta′ on history nodes comes from the cubic derivative in N. The code interpolates the measured rest-frame dimensionless rates and log H between nodes; Picard pass one has the original FLRW seed, pass two consumes pass one's full history. HYREC starts at a Saha redshift beyond the first target node, where the background endpoint rates are held fixed and the comoving density uses the first flux slope. The high-z extension is a prescribed initial approximation.

For a photon travelling along e in the baryon frame the frequency gradient entering the local Sobolev model is K(e)=Theta_b/3 + sigma_b:ee + (A_b/c)·e. The last term arises from contracting the acceleration term in the decomposition of the 4D velocity gradient with the two null directions. With positive K(e) on the whole sphere the local escape depth is tau(e)=C/K(e), with C=3 A_Lya lambda_Lya³ n_1s/(8π). Average P(t)=(1−exp(−t))/t over directions and invert the monotonic equation P(C/H_eff)=⟨P(C/K)⟩. The inversion is bracketed between the extremal angular depths. For deep optical thickness, P(t)=1/t up to the exponentially small residual and the average recovers Theta_b/3. At finite depth the differential of the implicit equation gives
d ln(H_eff)/d ln(n_1s) = 1−⟨t P′(t)⟩/[t_eff P′(t_eff)].
The Radau state Jacobian includes this response to the neutral fraction; P′ is evaluated using t P′(t)=exp(−t)−P(t).

The minimum gradient can occur between angular samples. If the eigenvalue lower bound H_b+lambda_min(sigma)−|A_b|/c is inconclusive, minimize K on the unit sphere. With acceleration b in the eigensystem of sigma, the concave dual function is H_b+lambda−sum b_j²/[4(s_j−lambda)] for lambda≤s_min. The derivative gives a decreasing secular constraint as a function of s_min−lambda. When b is orthogonal to the minimum eigenspace and the interior components have norm ≤1 at lambda=s_min, the minimum includes a component in this eigenspace. The code covers that endpoint and fails explicitly near a zero minimum. Direction sign changes require transfer beyond this single-resonance closure.

The Thomson monopole rate per e-fold is q=c sigma_T n_e,rest Gamma/H. The ray rate for normal-tetrad propagation e is q(1−beta·e). There is one Gamma in the density conversion; the moving collision operator receives the monopole to avoid applying the angular factor twice. A PCHIP interpolant through nonnegative rates has no negative interior extrema between nodes. Each output interval is split at every internal input knot. A two-point Gauss rule integrates each cubic piece exactly up to floating-point evaluation. Local sums avoid subtracting large past integrals when a late cell is very thin. With the observer at the last edge, the probability of the last scattering in cell j is exp(−tau_near)[−expm1(−delta_tau_j)]. The sum plus the unscattered transmission equals one on any finite interval. The equality is conditional on the interpolated opacity. Resolution of the physical ionization history is a separate numerical question.

## Executed checks and scope

`REC_REI_RESULT.json` records the class-B constant-flux orbit, the analytic directional slab, a positive opacity with large cubic undershoot, a late depth of 10⁻²⁰, two physically sampled histories, and native two-Picard FLRW and Bianchi V controls at ell_max=2 with 24 cells. Tests additionally cover analytic accelerated FLRW, sign-changing gradients at the unsampled pole, the trust-region hard case, and the finite-depth neutral Jacobian. The legacy table test checks the HYREC Planck2018 profile with its original tolerances. At uniform delta-z=5 the trapezoid on pointwise visibility gives 0.978426; resolving z≤18 at delta-z=0.1 gives 1.000014. Both finite-bin integrals normalize to roundoff. These tests do not calibrate patchy reionization, the redshift-domain end extension, a population prior or family identification. The independent H-only finite-rate chemistry adapter retains its documented class-A assumptions. No source-null view or physical detection probability follows from these controls.

The conserved-current sign follows the project's build_structure_tensor_with_sign and independently the homogeneous divergence relation in Pereira & Pitrou, section II (https://arxiv.org/abs/1909.13688). The local directional scattering measure is in Dropbox BASS Vol IV §1.6 and mathematical verification dossiers III/IV. Archived dossier paths and object revs are in the main handoff. The finite-history mass equation and numerical interpolation method are derived here.

Run from the existing checkout with the project's Python environment:

```sh
PYTHONPATH=htt:htt/src:htt/htt OPENBLAS_NUM_THREADS=1 python -m unittest bass.recombination.test_baryon_visibility -v
PYTHONPATH=htt:htt/src:htt/htt OPENBLAS_NUM_THREADS=1 python -m pytest htt/bass/recombination/test_tilted_hyrec.py -q
PYTHONPATH=htt:htt/src:htt/htt OPENBLAS_NUM_THREADS=1 python scripts/r103/rec_rei_result.py --out /tmp/r103_rec_rei_result.json
```

The SHA-256-verified R101 HYREC tables must be installed under data/external/r101_legacy_recovery/hyrec_atomic for the last two commands. The exact hashes are in the JSON result and the native table loader.

## Measured Radau rate-path optimization

Previously every call to the state RHS constructed the full 2×2 Jacobian and all four channel sensitivities and discarded them. The integrator now evaluates the shared base rate on those calls and computes the derivatives only on Radau Jacobian requests. On the 478-node history above, using the same tables, interpolation, initial state, tolerances and one OpenBLAS thread, the three old wall times were 1.788, 2.063, 1.928 s and the three new times were 0.613, 0.602, 0.558 s in the cloud runtime. Ratios of medians give 3.20× for this history. All five arrays (x_e, T_m, kappa, visibility, opacity_per_efold) were byte-identical as float64 values in array comparison across the six runs. Benchmark order was old/new/new/old/old/new. This measurement isolates the RHS optimization against the new R103 physics before this refactor.
