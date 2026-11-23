# R101 native polarized Thomson evolution

## Physical result and provenance

For radiation in a cold, unmagnetized electron rest frame, the finite-optical-depth propagator acts on every angular Stokes sample through nine integrated moments. Recovered BASS already implemented the homogeneous exponential in its real tensor carrier. R101 ports that solver into the current BASS package with an oriented I,Q,U,V interface, adds exact continuously forced cells, connects the angular maps to signed I/E/B/V multipoles, and evolves a joint noncommuting Fourier streaming/collision mode on a flat FLRW background. The same comparison identified and repaired the linear-polarization sign in the current native Mueller surface.

| Object | Identity or original source | Reuse |
|---|---|---|
| Tensor Thomson collision | [Portsmouth & Bertschinger, arXiv:astro-ph/0412094, Eqs. 140, 143, 163–164](https://arxiv.org/pdf/astro-ph/0412094) | Rest-frame gain from two screen projections, with elastic loss |
| CMB harmonic collision and baryon dipole | [Hu & White, Total Angular Momentum Method, Eq. 43](https://background.uchicago.edu/~whu/tamm/webversion/node19.html) | Linearized bulk-velocity source |
| Recovered BASS | `bianchi/q/polarization.py`, commit `ee298e24a6bac85bb11a81393f37499a8b0ddbe3`, SHA256 `44a2eb306d8870e70d6cb46c8f481bb30e58f64ffee4b9a055a0157a23e79e95` | `_split`, `kcal`, `collide`, and packing of antisymmetric components |
| Current HTT | `f8931fbef075d55c2c2a3caee8b8f5db5174b16b` | File identities in the rows below are Git blobs at this commit |
| Native direct/cached Mueller | `htt/bass/collision/electron_frame.py` · `83b5580a5ae132ad8563d0d95a788a5519d15878` | Screen validation and independent angular pairwise comparator. Both existing entry points shared the erroneous scattering frame |
| Current harmonic transport | `scripts/r97/bianchi_coupled_m_transport.py` · `a183b317817d2dd139e1761c1c5a584adfca476c`, R98 history · `13d976b97d52c7062145dc724f118e1ee7708428`, R100 · `957014db626508caac7ad1a8f49b2e488dc1d83e` | R100 uses R98's all-m builder and R97's collision matrix, adding an affine baryon dipole |
| Current sphere transforms | `htt/bass/transport/general_bianchi_transfer.py` · `16f6da1883a518ec918052582a36b536288240f4` | Actual GL grid, oriented spherical screen and signed scalar/spin transforms |
| Physics normalization | `docs/SSOT_POLICY.md` · `003422968f979b58dcdf2b35ce18ff383a1d7880`, §§4–5 | Local Thomson collision operator, with the positive forward scattering clock defined below |
| Recombination example | `htt/bass/recombination/fixtures/recombination_ref_planck2018.csv` · `7cee4cdf7365cb351efeaf970e97be304f748016` | Cumulative positive-to-the-past opacity kappa at every tabulated integer redshift from 950 to 1150 |

The legacy Lowell electron-frame specification is the catalogue object with SHA256 `2b8d372069e1418dfe8a7905c8a01b84e676dbc140a4809872f3c06f8505929b`. It supplies the Jones/coherency reference. The numerical baseline used here is the recovered executable BASS module above.

## Physical conventions and derivation

Use signature (−,+,+,+), a fixed orthonormal rest-frame triad, photon **propagation** directions n, and an oriented screen with u×v=n. In this frame J is a 3×3 Hermitian tensor with Jn=0. In the (u,v) basis its diagonal is ((I+Q)/2,(I−Q)/2) and J_uv=(U−iV)/2. The positive forward optical-depth increment is ds=n_e σ_T c dt in electron proper time. The attenuation variable is dimensionless and all Stokes components carry the same units. Elastic scattering acts independently at each photon frequency under the cold Thomson approximation ℏω ≪ m_e c².

Define P=1−nnᵀ, M=∫J dΩ and D(M)=(3/8π)PMP. Then

```math
dJ/ds=-J+D(M).
```

The sphere averages of n_i n_j and n_i n_j n_k n_l are δ_ij/3 and (δ_ijδ_kl+δ_ikδ_jl+δ_ilδ_jk)/15. Substituting these into the integrated gain gives

```math
\int D(M)\,d\Omega=\frac35 M+\frac1{10}M^T+\frac1{10}\operatorname{tr}(M)\,1.
```

Hence the trace, real STF and imaginary antisymmetric moments have gain eigenvalues b=1,7/10,1/2 with multiplicities 1,5,3. Every residual sky with M=0 damps at rate one per unit optical depth. The trace conserves ∫I dΩ. The V gain is (3/8π)n·∫n′V(n′)dΩ′, supported on the three dipole components. They decay at half rate while all other V modes decay at unit rate. V initially zero stays zero in source-free Thomson scattering.

For cell depth t, the homogeneous solution is

```math
H(t)J=e^{-t}J+D\!\left[\sum_b f_b(t)M_b\right],\qquad
f_b(t)=e^{-(1-b)t}\frac{-\operatorname{expm1}(-bt)}{b}.
```

This is the recovered BASS exponential. Its implementation uses three diagonal and three orthonormalized off-diagonal components of the real symmetric tensor, plus an axial vector for the imaginary antisymmetric part. Only the real 4-component sky is stored for the radiation itself. The cached angular design, directions and normalized weights occupy 176N bytes in float64. Mesh-dependent residuals in integrated moments are controlled separately from time evolution. The method checks normalized third- and fourth-order tensor moments, whose contractions also check the first two. Angular input must resolve the physical radiation moments. Degree-four exactness alone does not guarantee convergence for arbitrary unbandlimited skies.

Now take u∈[0,1] to be the cell time coordinate, and specify a constant integrated Stokes source F in dJ/du=t C(J)+F. With h(x)=−expm1(−x)/x and h(0)=1, integration yields

```math
J(1)=H(t)J(0)+h(t)F+
D\!\left[\sum_b\frac{h((1-b)t)-h(t)}{b}M_b(F)\right].
```

The coefficient difference starts at t/2 + (b−2)t²/6 + (b²−3b+3)t³/24. The implementation uses this expansion through t⁴ near zero. At t=0 the result is J+F. At large t a continuously forced, damped dipole tracks the supplied baryon velocity. For a signed temperature perturbation (δT/T) the example takes F_I=−ΔN nᵀ(σ/H)n + t n·v_b/c, with N=ln a and all other direct source components zero. This is first order in normal-frame shear and bulk velocity about isotropic radiation. For a blackbody bolometric fractional intensity the source coefficients would carry the usual factor of four. Applying identical normalization to I,Q,U,V makes the linear Thomson operator independent of this convention.

The exact affine action requires constant coefficients in a specified cell coordinate. A time-dependent scalar scattering rate can always be integrated into t in a source-free fixed-frame cell. With other source terms, their variation relative to the opacity clock must be resolved by cell subdivision. Angle-dependent optical depth in a tilted frame and shear advection of existing anisotropies require additional geometry and frame evolution.

## Noncommuting Fourier streaming and a stiff joint stage

Write the physical perturbation as Re[Sₖ(n)exp(+i k·x)] in comoving Mpc, with propagation directions and fixed screens in a flat FLRW tetrad. Redshift of the homogeneous brightness is factored out. Cell path length Δχ=cΔη has units of Mpc, and the complex dimensionless phase generator is Z(n)=−i Δχ k·n. The continuous frozen cell equation is dS/du=ZS+tC(S)+F. The angular Thomson matrix is real and extends linearly over the real and imaginary parts of the Fourier amplitudes. The associated Hermitian reality condition is between k and −k. Positivity of an isolated complex Fourier coefficient has no physical meaning.

Since Z and C generally do not commute, the exponential of their sum is not the product of separate exponentials. For the default scheme let h be a fractional cell step, γ=1−1/√2, A=Z+tC and R=(1−γhA)⁻¹. The two stages are Y₁=R(Y+γhF), Y₂=R[Y+((1−γ)/γ)(Y₁−Y)+γhF]. The final stage is the updated state. Order two follows from (1−γ)γ+γ=1/2 and the row sums. The scalar stability function [1+(1−2γ)z]/(1−γz)² tends to zero for stiff decay. The same discrete formula extends continuously to zero opacity and zero wavenumber. At finite step size it approximates the analytic solutions on those axes to second order. The optional symmetric split uses exact streaming and collision/source subflows, including an exact forced collisionless phase. [Alexander, SIAM J. Numer. Anal. 14, 1006–1021 (1977)](https://doi.org/10.1137/0714068)

Factor the gain as UV, mapping sky → nine moments with V and moments → sky with U. In this paragraph V denotes a moment map, distinct from the circular Stokes component. Then diag(d)−sC has D=diag(d+s) and low-rank correction −sUV. Its inverse acts by D⁻¹r+sD⁻¹U M, with

```math
[I-VU+V\,\operatorname{diag}(d/(d+s))\,U]M=VD^{-1}r .
```

For the symmetric carrier the matrix is 6×6. Its constant part, in orthonormal trace/STF coordinates, has diagonal (0,.3,.3,.3,.3,.3). For the axial carrier the matrix is 3×3 with constant part 0.5I. Computing the fraction d/(d+s) directly retains the small conserved pivot for large s. The trace row is scaled by this pivot before LU. On an isotropic sky the stage (1−sC)⁻¹ returns its input through s=10¹⁰⁰ at roundoff. This entails O(N) work and storage for N directions with fixed 6×6 and 3×3 factorizations per distinct cell step.

The 18-ray reference assembles the full complex, affine augmented pairwise Mueller matrix and exponentiates it independently. For k=(.33,−.47,.21) Mpc⁻¹, Δχ=3.1 Mpc, and t=2.4, default errors at 4, 8, 16 and 32 substeps are 0.01116, 0.002679, 0.000659 and 0.000164. A separate isotropic incident mode at t=1000 gives one-step error 0.8048 with symmetric splitting and 8.48×10⁻⁶ with the joint implicit method. At eight substeps the joint error is 1.05×10⁻¹². Relative performance depends on the initial fast components, source and wavevector. No uniform one-step precision follows from these fixtures.

The HyRec table exercise also propagates k=(.03,−.015,.011) Mpc⁻¹ by the joint method. Cell path lengths use trapezoids in cumulative opacity for dχ=dκ/(dκ/dχ), totaling 41.02159085 Mpc. At L=6, doubling the temporal resolution changes the most affected harmonic by 1.7440×10⁻¹⁰. The prescribed input/source yields final I,E,B,V harmonic norms of 5.594×10⁻⁵, 1.141×10⁻⁵, 4.077×10⁻⁶, and 2.960×10⁻⁵. This single Fourier mode on a fixed flat background exercises phase mixing and polarization, without fitting observational data.

## Physical defect in the current Mueller implementation

Take incoming n=x, outgoing n=z, and outgoing (u,v)=(x,y). The electric vector perpendicular to the scattering plane is y. The Jones map on unpolarized input yields I>0 and Q/I=−1, and U=V=0. The previous BASS raw/cached operator yielded Q/I=+1. Its regression checked |Q/I|. It selected an in-plane first axis and then applied the Mueller formula for a perpendicular first axis. For collinear rays it also chose unrelated axes on the incoming and outgoing screens.

The correction chooses the common normal of the two ray directions for the first axis. The projected Jones amplitudes in this frame are (1,μ), giving the positive 1−μ² cross-coupling in the existing Mueller formulas. The cross product is evaluated as n×[n′−sign(μ)n] so longitudinal cancellation stays small near collinear rays. At parallel or antiparallel incidence it selects one common physical transverse axis. An oblique ray pair at 10⁻¹⁴ rad agrees with direct Jones projection to 2.22×10⁻¹⁶. The existing sign-specific fixture, rotated forward/back scattering, a direct Jones 2×2 oracle, raw and cached IQU endpoints, and R100 harmonic quadrupoles exercise the correction. In the 18-direction random-sky regression the maximum generator defect fell from 0.41182509556189484 to 4.44×10⁻¹⁶.

## Executed evidence and limits

- Thirteen targeted unittest cases passed. Checks include the Jones matrix at six scattering angles, raw and cached angular endpoints, dense 4-Stokes affine matrix exponentiation, conservation, Stokes-cone positivity, rotation covariance, phase-space sampling, exact tangents of the homogeneous opacity flow, and the stiff limit.
- The R100-family comparator uses its actual R97 constructor, every complex TE/B signed-m slot through L=6, and a constant affine column with angular advection set to zero. It uses a populated initial state and source in every independent real component. There are 49 scalar I, 45 E, 45 B and 49 scalar V slots. Reality links ±m. The maximum error across I/E/B was 1.41×10⁻¹⁵. The V check against analytic damping was 8.25×10⁻¹⁶. This does not compare the complete R100 nonlinear fixed-point trajectory.
- The independently recovered BASS tensor implementation agreed to 4.45×10⁻¹⁶ through t=10⁴. A separate dense matrix exponential differed by 7.08×10⁻¹⁴ at t=10⁴ on the 32-ray quadrature. For exp(3.4 h·n) input the V error against the analytic Boltzmann integral fell from 5.52×10⁻² at N=18 to 1.78×10⁻¹⁵ at N=288.
- The HyRec-2 example used all 200 tabulated opacity increments from z=1150 to 950, total t=1.7710404. The initial sky, shear and bulk velocity are prescribed. The signed V dipole and E from an initially unpolarized linear channel are available as explicit coefficients. The physical opacity table is a reference input. This run tests the collision/source subproblem and makes no empirical CMB parameter estimate.
- At N=32, depth 10⁻⁸–10⁴, the measured native homogeneous action took roughly 20–27 μs, versus 0.53–1.53 ms for a freshly formed dense SciPy exponential and action. At N=8192 the cached angular arrays occupied 1,441,792 bytes and the native action took less than one millisecond. CPU timings are environment-dependent. A cached dense propagator at one fixed depth is a different performance experiment.
- In the selective-source environment, real pinned BASS functions/classes and the unchanged HyRec slice were executed with the new files. Full repository pytest and the complete all-family moving-frame evolution were not run here. The tests do not qualify an inhomogeneous or tilted all-family atlas, nonlinear atomic feedback, or any observational likelihood.

## Reproduction in the repository

```bash
PYTHONPATH=.:htt:htt/src python -m pytest htt/bass/collision/test_coherency.py htt/bass/collision/test_full_stokes_thomson.py htt/bass/transport/test_stokes_fourier.py -q
PYTHONPATH=.:htt:htt/src python -m scripts.r101.coherency_history
PYTHONPATH=.:htt:htt/src python -m scripts.r101.coherency_history --k-per-mpc .03 -.015 .011
OPENBLAS_NUM_THREADS=1 PYTHONPATH=.:htt:htt/src python -m scripts.r101.coherency_checks
```

The optional `--legacy-polarization` argument to the last command accepts the pinned recovered file. To connect a chemistry solver, pass chronological scalar rest-frame delta optical depths to `evolve_cells`. At β=0 the chemistry tangent of the homogeneous action is H(t)δS + δt C(H(t)S). A bulk or direction-dependent opacity calculation must use the collision kernel and angular measures in a consistent frame. The next physical integration is the angular and screen advection generated by a time-dependent non-FLRW Bianchi connection on the same trajectories as R100.
