# v15 Angular Calculus: novelty, comparators and publication strategy

Internal research assessment, 2026-10-26. Owner: `dipole_loop_20261026`. No source-paper changes, repository push, transport solver or new observational fit. The assessment concerns the supplied October 24 v15 manuscripts and the five internal HTT loops. It reports what was read and what each comparison supports; it does not claim a literature-wide priority search is complete.

The strongest present publication case is the **massive velocity-shell structure and its quantitative response**, followed by **observable-specific resolution certificates**. Ray-temperature calibration, exponential-family matching, entropy decomposition, blackbody mixing and Lorentz mode coupling have substantial direct precedents. The earlier Loop B dipole closure now has a particularly close 2026 comparator and should be presented as a rederivation or application. Loop A's positive shear-response operator offers a more promising bridge from v15's static entropy geometry to a physical inverse problem.

## What the manuscripts actually claim

Both abstracts, introductions and conclusions were read, along with I §§3, 3b, 3c, 4–5, Appendix D and II §§2, 6, 6b. Paper I defines an energy-calibrated temperature by maximum entropy on each radial momentum fiber, contracts the entropy to an angular functional, and separates spectral from angular information. Its more specific claims concern the positive Poisson factorization of massive velocity-dressed moments, strict inclusion of realizability sets, an interior inverse, and response-kernel sufficiency. Paper II adds number–energy calibration, massive thermochemical moment matching and the energy support of each angular rank.

Paper II's `02_effective_frame.tex` explicitly keeps the observer \(U\) fixed. Its “effective” quantities are calibrated \((T,\mu)\) fields. **It does not minimize an entropy over Lorentz observers or prove existence/uniqueness of a preferred observer.** Observer optimization would be a new research question. The title change from legacy Teff to Angular Calculus improves the statement of scope; it is not itself a scientific novelty claim.

The retained definitions matter. On a mass shell \(E^2=m^2c^4+c^2q^2\), \(v=cq/E\) is speed in units of \(c\). The physical leading rank-\(\ell\) score is \(v^\ell Z_{\ell m}\). The spherical Poisson operation satisfies \(\mathcal P_vZ_{\ell m}=v^\ell Z_{\ell m}\). This is a kinematically fixed shell operation, not an assumed scattering evolution. The global MB/FD inverse concerns the interior of the **dressed** moment set. The BE anisotropic critical completion remains conditional; the supplied manuscript does not establish existence for every anisotropic critical target.

## Search and reading record

Discovery used SciSpace's semantic paper index and Exa's primary-source search/fetch, accessed 2026-10-26. Saved query/fetch responses are `sources/LITERATURE_*.json`. Queries covered relativistic entropy matching, observer frames, velocity-weighted moments, Poisson kernels, realizability with heat flux, spectral distortions, angular resolution and recent radiation closures. Recent original work was checked through the current cutoff, including 2025 papers and 2026 preprints. The search is broad enough to identify immediate competitors, but sparse or irrelevant query returns are recorded as coverage limits, not evidence that a result is absent.

SciSpace's general observer-entropy query returned several weakly related Zenodo items; these were not used as scientific comparators. Exact primary titles and source texts were then checked through Exa. HTML conversion dates sometimes differ from original arXiv submission/publication dates; the arXiv IDs and publisher dates control the chronology.

| ID | Original source and locator | Reading performed here | Main comparison |
|---|---|---|---|
| L1 | Banach–Larecki (2001), [DOI 10.1016/S0378-4371(00)00625-7](https://doi.org/10.1016/S0378-4371(00)00625-7) | Primary publisher introduction excerpt, equations describing entropy decomposition; not full proof | Entropy split into finite-moment and unresolved-state contributions for relativistic classical/quantum gases |
| L2 | Banach–Larecki (2002), [DOI 10.1142/S0129055X02001223](https://doi.org/10.1142/S0129055X02001223) | Primary abstract and scope; full article unavailable in this pass | Fiducial-observer central moments, entropy-maximizing closure and observer dependence |
| L3 | Escobedo–Mischler–Valle (2005), [full primary PDF](https://www.numdam.org/item/BSMF_2005__133_1_87_0.pdf), DOI 10.24033/bsmf.2480 | Introduction, Theorems 1–2 and beginning of classical relativistic section; first 22k text characters | Rigorous number/momentum/energy entropy maximization, degenerate FD and generalized BE states |
| L4 | Lewis–Challinor (2002), [astro-ph/0203507](https://arxiv.org/abs/astro-ph/0203507), DOI 10.1103/PhysRevD.66.023531 | Main text through velocity hierarchy and frame/truncation discussion; Eqs. (10)–(19) specifically read | Existing exact \(v^{\ell+2i}\) hierarchy and stress-energy identification |
| L5 | Everett–Chattopadhyay–Heinz (2021), [2101.01130](https://arxiv.org/abs/2101.01130), DOI 10.1103/PhysRevC.103.064902 | Primary main-method excerpt including anisotropic maximum-entropy matching examples | Temperature/stress matching and positive anisotropic kinetic representatives |
| L6 | Chen–Huang–Yong–Zhang (2025), [2308.10083](https://arxiv.org/abs/2308.10083), DOI 10.1137/23M1620181 | Introduction, §2 Poisson-EQMOM ansatz, Fourier moments, global-inversion theorem discussion; first 24k characters | Positive Poisson-kernel angular reconstruction with \(r^{\vertk\vert}\) moments on \(S^1\) |
| L7 | Boccelli–McDonald (2022), [2208.07890](https://arxiv.org/abs/2208.07890), DOI 10.1063/5.0106214 | Primary PDF, introduction, moment definitions, realizability/heat-flux analysis and higher-dimensional discussion | Energy/pressure/heat-flux constraints from the relativistic Hamburger moment problem |
| L8 | Chluba–Sunyaev (2004), [astro-ph/0404067](https://arxiv.org/abs/astro-ph/0404067), DOI 10.1051/0004-6361:20041016 | Primary introduction and mixing/calibration analysis excerpt; first 42k characters | Mixed blackbodies, angular averaging, dipole-induced spectral structure |
| L9 | Pitrou–Stebbins (2014/2015 version), [1402.0968](https://arxiv.org/abs/1402.0968), DOI 10.1007/s10714-014-1806-z | Primary text including representation, frame properties and conclusion | Log-temperature spectral moments and frame-independent distortion coordinates |
| L10 | Chluba–Ravenni (2026), [2505.02080](https://arxiv.org/abs/2505.02080), [published paper](https://academic.oup.com/mnras/article/548/3/stag698/8653927), DOI 10.1093/mnras/stag698 | Introduction, operator construction, §4.1 dipole discussion and second-order expressions; publisher and arXiv excerpts | Frequency-differential boost operator and explicit low-multipole primordial-dipole degeneracy |
| L11 | Barenboim–Froustey–Pitrou–Sanchis (2026), [primary PDF](https://journals.aps.org/prd/pdf/10.1103/dq6j-fzz6), PRD 113, 063566 | Introduction, temperature-transform and orthonormal-polynomial constructions; primary conclusion in search excerpt | Number-density spectral coordinates, BE/FD distortion parameters, CMB/CνB applications |
| L12 | Abdelmalik–Cai–Pichard, [2304.01758](https://arxiv.org/abs/2304.01758) | Primary §§2–3 including polynomial ansatz and moment-inversion proof excerpt | Entropy/divergence radiation closures; its odd-power ansatz can be signed, unlike a positive occupation cone |
| L13 | Melon Fuksman et al. (2025), [2504.13999](https://arxiv.org/abs/2504.13999), DOI 10.1051/0004-6361/202554994 | Primary abstract, introduction and initial half-moment/multigroup method text | Existing joint angular/frequency refinement and crossing-beam improvement |
| L14 | Agrawal–Horel (2021), [JMLR 22(128)](https://jmlr.org/papers/v22/20-867.html), [2006.05973](https://arxiv.org/abs/2006.05973) | Original abstract and source metadata; not full theorem proof | General convex-dual divergence-to-observable bounds; limits broad “first entropy response bound” wording |
| L15 | Maartens–Gebbie–Ellis (1999), [astro-ph/9808163](https://arxiv.org/abs/astro-ph/9808163), DOI 10.1103/PhysRevD.59.083506 | Primary introduction/initial hierarchy text; Loop A's existing source-matched Eq. (71) audit reused | Nonlinear shear–radiation hierarchy is prior work; positive inverse reformulation is the candidate extension |
| L16 | Çokluk et al. (2026), [2608.16275v1](https://arxiv.org/abs/2608.16275v1) | Original abstract only | Current multipolar neutrino-emission application; emission-surface harmonics differ from a local momentum sphere |
| L17 | Kim et al. (2026), [2607.10364v1](https://arxiv.org/abs/2607.10364v1) | Primary introduction and method beginning; first 12k characters | Learned entropy/symmetric-Jacobian M1 closure; operational competitor for numerical accuracy, not v15's static theorem |
| L18 | Furuta (2004), [primary PDF](https://acta.hu/download.phtml?id=2785), *Acta Sci. Math.* 70, 319–337 | Definition 1, Theorem A and Theorem 3(i), plus surrounding introduction | Exact generalized Kantorovich constant and reverse power-mean inequality; the proposed sharp beam bound is a direct specialization |
| L19 | Gilardoni, [cs/0603097](https://arxiv.org/abs/cs/0603097) | Primary introduction and second-order Pinsker-type theorem/corollary text | Sharp scalar divergence-to-variation inequality underlying the new angular-entropy shear bound |
| L20 | Lam (2016), [1303.0326](https://arxiv.org/abs/1303.0326), DOI 10.1287/moor.2015.0776 | Primary introductory and optimization/asymptotic construction excerpt; first 18k characters | Entropy-budget robust expectation extrema, exponential tilts and square-root response width |
| L21 | Dupuis et al., [1503.05136](https://arxiv.org/abs/1503.05136), DOI 10.1137/15M1025645 | Primary introduction and information-bound construction excerpt; first 14k characters | Observable-specific information bounds and sensitivity; general method is established |
| L22 | Hauck–Levermore–Tits (2008), [author-hosted original PDF](https://user.eng.umd.edu/~andre/hlt.pdf), DOI 10.1137/070691139 | Introduction, moment problem, degeneracy definitions and theorem summaries; first 45k characters, not every proof | Equality-constrained entropy minimizers can fail for realizable moments; relaxed constraints, duality and degenerate-density geometry |

The full-text restrictions in L1–L2 and abstract-only status in L14/L16 bound the conclusions below. A source being in a manuscript bibliography does not establish that every relevant equation was compared; L6 and L7 in particular should be added to the nearest-comparator discussion if they are still absent from the active bibliography.

## Claim–comparator–difference matrix

Grades mean: **N0** established mechanism or special case; **N1** useful synthesis/translation; **N2** specific extension with a credible difference from inspected comparators; **N3 candidate** potentially substantial result requiring theorem-level priority and significance checks. They measure a publication hypothesis, not truth or acceptance. Confidence refers to the comparison performed, not to the mathematical correctness of all manuscript proofs.

| Physical/mathematical claim | Nearest comparator | Concrete retained difference | Grade and next priority check |
|---|---|---|---|
| Ray energy selects \(f^\sharp=\Phi(\beta(e)E)\), brightness temperature and susceptibility | L1–L3, established Planck/maximum-entropy closure | Complete angular function of ray-energy constraints, MB/BE/FD in one observer-conditioned treatment | N0 mechanism / N1 organization. Do not lead with “effective temperature” discovery. |
| Exact spectral–angular Bregman budget and nested information increments | L1, information-projection theory; L2 central-moment closure | Explicit radial contraction \(F'(\rho)=-\beta\), equality of lifted/contracted divergence, physical response witnesses | N1. The cancellation is a standard matched-score mechanism; assess utility through a new response certificate. |
| Massive \(v^{\ell+2i}\) scores | L4 Eq. (10), L2 | Manuscript maps conventions and units and computes thermal susceptibility | N0 hierarchy / N1 response implementation. The hierarchy itself is not new. |
| Shellwise \(\mathcal P_{v(E)}\) factorization, entropy contraction, strict dressed/directional moment-set inclusion | L4 plus L6, classical spherical Poisson theory | Physical shell radius fixed by dispersion; \(S^2\), number and energy blocks, FD cap, strict interiors. L6 uses fitted common radius and kernel mixtures on \(S^1\) for constant-speed dynamics. | N2, possibly N3 candidate as a combined theorem. Standard Poisson eigenvalues/Jensen are not the novelty. Compare exact moment cones, not just names. |
| \(\vertF\vert^2\le E^2-m^2c^4N^2\) at fixed population/energy | L7 and positive future-momentum geometry | Simple separating witness for the two v15 cones, with declared matching variables | N0 inequality mechanism / N1 use. L7 conditions also use pressure and can be stronger. FD cap can tighten the optimum; avoid unqualified sharpness. |
| Global finite-rank regular MB/FD inverse onto dressed interior | L2–L3, L5, L12 | Exact score/domain, positive shell control and boundary barrier for arbitrary finite rank; positive FD occupation range preserved | N2/N3 candidate. Need full L2 theorem-level comparison and explicit comparison with signed closure domain in L12. |
| Large-rank Fisher energy \(X_\ell=[(2\ell+1)z^2]^{1/3}\), weight \(X_\ell^{r+5/2}e^{-3X_\ell/2}\), chemical Schur suppression | L4 nonrelativistic truncation, L2 moment formalism; Laplace asymptotics generally | Explicit massive thermal shell selected by rank; cold \(\ell+3/2\) kinetic-energy branch, crossover, correction coefficients and validity conditions | N2, strongest specific asymptotic candidate in present search. No claim that saddle-point methods or hard-tail selection are new. |
| Finite coefficient-tail cutoff certificate | Existing entropy closures and L14 | The radial majorant contains physical velocity attenuation and thermal/chemical score blocks | N2 if turned into a usable tolerance or optimal allocation. Small Fisher weights alone are not an error certificate. |
| Fixed-moment response determined iff target kernel lies in measured span; positive indistinguishable witnesses | Classical moment/linear-functional duality, L14 | Concrete rate kernels, angular examples, occupation caps and energetic-tail obstruction | N0 mechanism / N1 examples. A sharp detector-specific uncertainty envelope is a stronger next result. |
| Beam mixing produces spectral residual; matching number/energy selects different thermal reference | L8–L9, L11 | Entropy-selected thermochemical calibration and a possible finite beam-range envelope | N1 currently; N2 candidate for calibrated finite acceptance/channel mismatch bounds. |
| Finite inverse-temperature cutoff leaks under boost; conditional information stability | L9–L10 and Dai–Chluba boost kernels | Explicit positive-patch information derivative/tail estimate, not merely harmonic boost formulas | N2 for the quantitative norm estimate; direct mode mixing is N0. Constants/regularity/sharpness need a useful application. |
| Loop B: nonlinear quadrupole spectral term is fixed by total observed dipole | L10 §4.1, Eq. (41)/Appendix B discussion; earlier Kamionkowski–Knox | STF presentation, nuisance-projected estimator and bounded intrinsic-quadrupole envelope | N0 physical closure / N1 conditional inference packaging. L10 explicitly reaches the same central conclusion. |
| Loop A: \(\mathcal L_I\) positive on shear with \(\lambda_{\min}(M_2)\) lower bound and bounded inverse error | L15 nonlinear hierarchy | Five-dimensional coercivity, angular-support criterion, exact operator assembled from brightness degrees 0/2/4 | N2 candidate. Priority search for this exact operator is incomplete; the transport hierarchy and coefficient are prior work. |
| Entropy defect \(\delta=1-\langle w^{3/4}\rangle\) gives \(\Vert\mathcal L_I-8\rho\mathrm{Id}/15\Vert\le\rho\sqrt{8\delta/3}\), threshold \(\delta<8/75\) | L19 scalar Pinsker inequality + Loop A finite tensor operator | Mass-matched centering and a finite radiative inverse-conditioning certificate without an amplitude ceiling | N1/N2 physical bridge. Neither the scalar inequality nor the threshold's universal sharpness is claimed new. |
| Sharp beam-range ratio \(R_{\min}(r)\) | L18 generalized Kantorovich, \(h=r^3,p=4/3\) | Application to fixed-fugacity number–energy calibration and beam-induced apparent population bias | N0 exact scalar specialization / N1 application; instrument-calibrated discrimination remains the potential N2 result. |

### The decisive Loop B correction to a novelty narrative

L10 states in its actual §4.1 that quadrupole spectral-distortion coefficients are precisely those of \((\beta_{\rm total}\cdot n)^2/2\). Monopole temperature differences are degenerate with the unknown reference temperature. It then explains that high-\(\ell\) aberration adds the assumption of an intrinsically statistically isotropic reference sky. This closely matches the earlier internal Loop B derivation. A publication should cite it directly, preserve the useful STF equation
\[
 K-(aa)_{\rm STF}=Q_{\rm intrinsic}-(dd)_{\rm STF}+O(\lambda^3),
\]
and place any contribution in calibrated partial identification, not a new resolution of the fundamental low-multipole question. In particular, if \(\|Q_{\rm intrinsic}\|\le q_{\max}\), its finite norm envelope is useful but depends on that external input. The calculation is sound research progress even when its principal physical conclusion has prior art.

## Four publication strategies and their first decisive tests

### Three standalone mathematical candidates already in v15

These are separate from the new bridge corollaries. Each can support a focused mathematical-physics claim if its proof survives independent review and the exact priority comparison is completed.

**M1 — positive physical shell factorization with strict realizability loss.** At every positive mass and finite \(L\ge1\), both the dressed joint number–energy moment set and its interior are strict subsets of the direction-only counterparts, for the three stated statistics. The map is explicit and preserves positivity/FD admissibility. Lewis–Challinor supplies the scores; classical Poisson theory supplies the harmonic extension; Chen et al. supplies a close positive Poisson-moment application. What remains a specific candidate contribution is their composition with dispersion-fixed radius, the joint two-block moment image and the strict-interior witness. The decisive written comparison should place the score definitions, state classes, sphere dimension and domain inclusions side by side. A proof of just the kernel eigenvalues or Jensen contraction would not establish this difference. The next strengthening is a quantitative distance between the two attainable sets at fixed \(N,E\), including the FD cap, rather than another abstract factorization statement.

**M2 — global regular calibration for the actual massive score family.** The candidate theorem is \(\nabla\mathcal A:\{\min B_1>0\}\to\operatorname{int}\mathcal R^{\rm dr}_{\rm MB/FD}\) a diffeomorphism for each finite \(L\), at every fixed \(z\ge0\). Convexity only gives a local inverse; the global assertion requires both the exact finite-potential domain and that the image is the entire realizability interior, not merely the image of the ansatz. V15's substantial step is the boundary barrier: when \(B_1\ge0\) touches zero at an angular minimum, its quadratic local growth admits caps of area comparable to \(E^{-1}\) with bounded exponent. Multiplication by radial density of states \(E^2\) leaves a divergent lower integral \(\int E\,dE\). The massive shell correction approaches the boundary field rapidly enough not to remove that divergence. This prevents finite-boundary escape, while interior witnesses control coefficient escape to infinity.

L22 explains why this step is essential: its ordinary unbounded-velocity polynomial moment families can have realizable densities whose equality-constrained entropy minimum is unattained. Thus general Levermore-style exponential ansatz plus a positive Gram matrix does not automatically prove M2. Conversely, standard convex-duality theory supplies the conclusion once the v15 family is proved steep/coercive: there is no new general inverse-function principle. The decisive comparison is to apply L22's exact domain/degeneracy criterion to these bounded-speed, at-most-linear-energy scores and determine whether M2 follows immediately as a previously covered corollary. The full L2 result is still needed because it uses relativistic central moments closer to these scores. Do not extend M2 to all BE critical targets or to \(L\to\infty\).

**M3 — quantitative energy localization and loss of population distinguishability at high rank.** The specific combined result is not just a cubic saddle. It includes \(M_{\ell,r}\)'s prefactor, first correction \(c_r(z)\), \(\bar E_\ell/(k_BT_*)=X_\ell+4/3+O(X_\ell^{-1})\), variance \(X_\ell/3+O(1)\), and chemical Schur complement \(M_{\ell,0}/(3X_\ell)\), together with the cold gamma-law branch and its validity conditions. Lewis–Challinor's velocity hierarchy and nonrelativistic truncation do not state this thermal Fisher localization in the inspected sections. The saddle-point technique is established; the candidate theorem is the explicit response/conditioning law for these scores. A decisive standalone result would prove a uniform error through a stated crossover window or turn the existing fixed-parameter asymptotics into certified finite-rank conditioning bounds. In particular, stronger energy selection comes with stretched-exponentially small weight: it does not imply high observational sensitivity. The manuscript's own finite-rank errors rule out relying on the leading asymptotic at every practical low cutoff.

M1/M2 have the strongest structural case; M3 has the clearest quantitative physical interpretation. Their current grades remain N2 to N3-candidate, not established priority. They should be presented as three precise results with shared notation, rather than multiplying every standard variational identity into an independent novelty claim.

### 1. Massive angular response as a theorem with an operational resolution rule

Lead with the linked result: physical velocity scores induce a positive shell map, restrict realizability, and select progressively harder but weaker Fisher response. The main reader benefit is knowing **which particle energies must be resolved for a chosen angular rank**, while maintaining a positive MB/FD reconstruction. This is more specific than proposing another entropy closure.

The first decisive comparison is a common-score experiment, not a new evolution code: choose \((z,\eta,L)\), compute v15's exact radial Fisher blocks, and compare direction-only and dressed reconstructions at the same retained number/energy scores. Report the smallest eigenvalue, the number–energy Schur complement, and one energy-weighted target error. For asymptotics, prove a uniform finite-parameter remainder across a stated \(\ell/z\) crossover window or retain exact quadrature where the asymptotics are inaccurate. A tolerance policy can then choose a radial grid and \(L\) from the existing finite coefficient-tail certificate.

The target difference from L6 is not “Poisson kernels improve positivity”: that is already explicit there. It is the dispersion-fixed shell family, its strict joint moment cone and the quantitative thermochemical response. Compare L7 at fixed pressure as well as without pressure so the simple flux envelope is not portrayed as strongest available. A useful pass condition is a reproducible reduction in target error or radial work at the same declared tolerance. Failure to improve the target still leaves a mathematical cone/inversion paper, but weakens numerical significance.

### 2. Observable-specific entropy uncertainty and channel design

Use I §5's kernel residual and II's rate examples to replace generic reconstruction quality by the interval for one physical response. On a compact detector band, let \(\phi_i\) be retained kernels, \(g\) a regular MB/BE/FD reference and \(K\) the target interaction kernel. With \(W=g(1+\xi g)\), project \(K\) off the \(\phi_i\) in the \(W\)-weighted inner product, obtaining \(r\). The local entropy geometry immediately predicts
\[
 \sup_{\delta f}\{|\langle K,\delta f\rangle|:
 \langle\phi_i,\delta f\rangle=0,\ D_H(g+\delta f\Vert g)\le\varepsilon\}
 =\sqrt{2\varepsilon\int Wr^2}+o(\sqrt\varepsilon),
\tag{N1}
\]
under a regular interior and finite-band expansion. This follows by writing \(\delta f=\sqrt W h\), using the quadratic entropy cost \(\|h\|^2/2\), and applying Cauchy–Schwarz in the constraint complement. It identifies the next useful channel by its overlap with the unresolved target, not by rank alone.

For a finite bound, set \(r_a=K-\sum a_i\phi_i\). Fenchel's inequality supplies, for either sign and any \(\lambda>0\),
\[
 \pm\Delta O\le\lambda\varepsilon+\lambda\int
 [h^*(h'(g)\pm r_a/\lambda)-h^*(h'(g))
       \mp gr_a/\lambda],d\Pi .\tag{N2}
\]
Minimize this bound over \(a,\lambda\) within its finite-potential domain. This is established convex-dual machinery, with L14/L20/L21 important comparators; the research contribution would be the physically constrained angular/spectral kernels, occupation domain and achieved rate uncertainty. The parallel project note `RESPONSE_FRONTIER.md`, now read through its main theorem, has already advanced beyond this proposal: it constructs the quantum Bregman extremizer at fixed number/energy, proves its exact three-point identity and executes an MB/BE/FD static toy. Its calibrated/raw local response-width ratios are approximately 0.703/0.710/0.674. These values quantify removal of the already calibrated score directions in an illustrative kernel; they are not instrument gains. The next decisive calculation is a charged-current neutrino or spectrometer response on a declared band, comparing number–energy alone, one extra width moment and one optimized channel, using L11's polynomial representation as an independent reconstruction baseline. Include noise and bandpass correlations. Do not claim an all-energy bound for kernels outside the supplied tail control.

### 3. Entropy-certified radiative shear stability

Combine v15's angular entropy with Loop A's coercive physical operator. This is a direct bridge from static information loss to a conditional geometric response. For unit-Frobenius STF \(S\), Loop A gives
\[
 \langle S,\mathcal L_I S\rangle
 =\int I(e)[2|Se|^2-(e^TSe)^2],d\Omega,
\quad0\le2|Se|^2-(e^TSe)^2\le1.
\]
Consequently \(\|\mathcal L_I-\mathcal L_J\|_{\rm op}\le\|I-J\|_1\). On a common positive brightness interval with contracted entropy curvature \(F''\ge\kappa_F>0\), v15 gives \(D_F(I\Vert J)\ge\kappa_F\|I-J\|_2^2/2\). Hence the explicit bridge is
\[
 \lambda_{\min}(\mathcal L_I)\ge
 \lambda_{\min}(\mathcal L_J)
 -\sqrt{8\pi D_F(I\Vert J)/\kappa_F}.
\tag{N3}
\]
The inequalities use full Cartesian Frobenius norms and unnormalized \(d\Omega\). A positive right side certifies the inverse conditioning scale; it does not supply the unmeasured transport residual.

The new project note `PAPER_I_REUSE.md`, now read through its proof and finite inverse certificate, obtains a stronger amplitude-unrestricted route to isotropic comparison. Put \(w=4\pi I/\rho\), \(\langle w\rangle=1\), \(\delta=1-\langle w^{3/4}\rangle\). Its L19 specialization is \(\langle|w-1|\rangle\le\sqrt{32\delta/3}\). Equal total energy allows the pointwise operator to be centered by \(\mathrm{Id}/2\), giving
\[
 \|\mathcal L_I-8\rho\mathrm{Id}/15\|_{\rm op}
 \le{\rho\over2}\langle|w-1|\rangle
 \le\rho\sqrt{8\delta/3}.
\tag{N3b}
\]
Thus \(\delta<8/75\) is a sufficient invertibility certificate. This combines a known scalar sharp inequality with a specific tensor response; its resulting tensor bound is conservative, and no optimal universal threshold is established. The existing finite example confirms that positivity can survive beyond this sufficient threshold. N3 remains useful around a general anisotropic representative when its amplitude domain is known.

The next decisive step is to compute the sharp worst-case five-dimensional eigenvalue over an actual bandpass-calibrated moment region and compare it with N3/N3b. A crucial simplification, proved and tested in the parallel `ENTROPIC_SHEAR_BRIDGE.md`, is that \(\mathcal L_I\) depends only on **brightness** degrees 0, 2 and 4: if those are exactly retained, its operator is already fixed and no entropy budget is needed for this part. Entropy bounds matter for the missing/reconstructed brightness directions and for imperfect measurements. Differentiate temperature and bolometric brightness; nonlinear \(T^4\) generates moments outside a truncated temperature fit. Compare with L15 explicitly, and retain Loop A's direct coefficient audit without presenting the old hierarchy as a new law.

### 4. Beam-calibrated thermochemical null diagnostics

Paper II's follow-up derivation provides a possible compact experimental paper. For massless matched rays, \(N'=D^3N\), \(E'=D^4E\), so \(Q=N^4/(\mathcal D E^3)\) and calibrated fugacity are weight-zero celestial scalars. A positive energy-independent beam mixing rays with common fugacity has
\[
 {Q_{\rm beam}\over Q(\eta_0)}
 ={\langle T^3\rangle^4\over\langle T^4\rangle^3}\le1.
\tag{N4}
\]
The upper inequality is a standard power-mean/Hölder consequence. The proposed sharp range-bound constant also has an **exact primary prior-art match**, rather than merely a similar proof. Set \(X=T^3/T_{\min}^3\in[1,r^3]\), where \(r=T_{\max}/T_{\min}\). Furuta's L18 Definition 1 and Theorem A give
\[
 \mathbb E[X^{4/3}]\le\mathsf K(r^3,4/3)(\mathbb E X)^{4/3},\quad
 \mathsf K(h,p)={h^p-h\over(p-1)(h-1)}
 \left[{(p-1)(h^p-1)\over p(h^p-h)}\right]^p.
\]
Cubing and inverting shows
\[
 {Q_{\rm beam}\over Q(\eta_0)}\ge\mathsf K(r^3,4/3)^{-3}
 ={256r^3(r^2+r+1)^3\over27(r^3+r^2+r+1)^4}.
\tag{N5}
\]
The exact substitution was checked in connected Wolfram Language: algebraic residual zero, limit \(r\to1\) equal to one, and value 0.513919707362 at \(r=2\). The source and execution are in `LITERATURE_BEAM_COMPARISON.json`. The scalar bound is therefore N0, an exact specialization of an established reverse-Jensen/Kantorovich inequality. This does not remove its physical use. The candidate contribution is the **calibrated bias envelope and null diagnostic** separating beam mixing from a surviving population perturbation, with statistics/domain/acceptance made explicit. L8–L9 already establish mixing distortions and frame properties; L11 offers modern number-density spectral coordinates.

The first decisive experiment is a synthetic measured response with unequal energy and number bandpasses, known beam and injected thermal plus chemical dipoles. Test whether the proposed ratio diagnostic retains any chemical direction after the calibrated beam/mismatch nuisance columns are projected out. Show both false-positive control for pure thermal mixing and sensitivity to chemical perturbations with the same energy map. No primordial-dipole identification follows from N4. The manuscript's current fixed-\(U\) calibration is sufficient; an entropy-minimizing Lorentz observer is unnecessary to this experiment.

## Integration with all five previous loops

| Previous loop | Role in the v15 extension | Observable or derivation that must be supplied |
|---|---|---|
| A: radiation/shear | Strongest direct kinetic-to-geometric bridge; strategy 3 | Joint bolometric degrees 0/2/4, derivative/flux residual and uncertainty; compare entropy-derived and actual operator eigenvalues |
| B: intrinsic dipole | Frame and calibration control; specific finite bounds remain useful | Common dipole/quadrupole covariance and an intrinsic-quadrupole envelope or calibrated angular velocity response; cite L10 |
| C: local kinematics | Independent radial/transverse shear closure to compare with a conditional radiative inverse | Same congruence, distances, clock, frame spin and source-slip calibration; static entropy does not supply these |
| D: homogeneous curvature | Target equivalence classes for any eventual geometric interpretation | STF spatial Ricci/Weyl-sensitive response; preserve II/VII0 witness and flat I/VII0 presentation equivalence |
| E: finite-redshift optics | Observation-window and remainder model for cross-channel comparison | Joint distance-jet coefficients, calibration and finite-distance bound; a kinetic angular entropy is not a replacement for the optical map |

The synthesis should therefore be written around a response problem, not around one universal scalar “degree of departure.” A useful eventual joint target is agreement between optical and radiative estimates of a common shear on their shared identifiable subspace. Matter curvature and tilt remain additional physical responses. There is no need to append all five loops to both v15 papers; use their results as an extension programme with named data dependencies.

## Recommended ordering and remaining priority work

For the supplied papers, foreground the shell-factorization/inverse and massive rank-energy results, with the exact nearest-comparator table made explicit. For a follow-up, pursue strategy 3's finite shear stability or strategy 2's target-rate uncertainty first: each has a concrete observable and a small decisive calculation. Strategy 4 is attractive if bandpass/beam calibration can be made quantitative. An entropy-selected Lorentz observer is a separate, lower-priority proposal: it first needs a declared objective, behaviour under rapidity escaping to infinity, and comparison with energy and statistical-isotropy frames. No such theorem is inherited from the present titles or section names.

The material comparison gaps are the full Banach–Larecki 2002 theorem text, precise matching-variable reduction of L7, and a sharper priority search for the exact Loop A coercivity operator and v15 high-rank correction coefficients. These gaps permit conditional publication planning while withholding “first,” “unique framework,” or universal absence claims. The existing positive constructions, coefficients and finite bounds remain mathematical results under their stated hypotheses regardless of their eventual novelty grade.
