# HTT Theory Research Loop R1–R10: Qualified Sources + One Consistent Observation Law

2026-10-15 KST. Branch obs/solver-free-dossier-20261014, starting HEAD
13d8d85fa470d645d008986e8f77d8d0f70fdf54.
Continuation from previous HTT source-bound CMB/CF4 R/C studies.
The two task lanes are logically separate: external input acquisition
and independent construction of an internally coherent generative law.

## R1–R3: Questions, sources and scientific claim alignment

Planck core inputs: official PR3 full SMICA K_CMB HEALPix, confidence mask,
HM1/HM2 independently released *data products*, their HM missing-pixel
mask, effective beam transfer and input simulation genealogy. An actual
PR3 HM pair is NOT by itself an empirically calibrated noise likelihood:
split residuals can share foregrounds, calibration and processing.
Local SMICA full-map cache already includes 300 paired FFP10 CMB+noise
surrogates under the existing pipeline, not necessarily the physical
observed-sky null, nor simulated HM1/HM2 source-matched noise.

CF4 core inputs: 2023 release source CDS J/ApJ/944/94,
Table2 individuals (55,877), Table3 grouped methods and calibrations
(38,053 actual table rows), Table4 velocity frames/derived moduli
(38,053 actual table rows), and ReadMe source-level definitions.
Tully et al. ApJ 944, 94 DOI 10.3847/1538-4357/ac94d8
models inter-subsample distance-zero offsets with Bayesian calibration.
Duangchan et al. A&A 2026, aa56645-25, reconstructs CF4 flows and
magnitude-selection effects using 64 tailored mocks, explicitly notes
the approximation of its empirical selection prescription.
There is no authenticated full CF4 galaxy-by-galaxy published
joint selection/physical cross-method covariance law in the material
examined; the published summaries do not substitute for it.

The existing CF4 cohort 24 SNIa-only selected groups contains two
strongly related quantities DMsnIa (source-method group modulus on
arbitrary scale) and DMzp (group released calibrated combined modulus).
They must not be independently multiplied. In the **published three-decimal
representation**, DMzp-DMsnIa=-0.147 mag for 22 groups, while two
specific groups have -0.326 and -0.422 mag. This is direct evidence of
strong dependence at publication precision and evidence that a universal
group-level correction for all 24 is not established.

Relevant previous HTT established work:
- The exact local null-cone/optical first-jet image, inverse and fibre
  theorem for a source congruence under its precise near-vertex assumptions.
- Exact observer Lorentz thermodynamic Doppler pullback and angle flow.
- Proper mask and harmonic fit operator plus fixed high-mode nuisance
  quotient; simulated finite-rank conditional inference.
- Difference between preselection shared calibration and per-slot
  conditioned sampling laws (different physical experiments).

## R4–R5: Constructive, globally coherent hierarchy

Let G be one shared physical metric, congruence u, matter and radiation
evolution, including shear sigma_ab, expansion theta, acceleration A_a,
vorticity omega_a, and any allowed global Bianchi/tilt physics. A source
null geodesic and tetrad supply a total redshift z_i, dA_i and
dL_i for a matched emitting and observing frame. Etherington duality
requires

   dL_i = (1+z_i)^2 dA_i.

At a sufficiently small observer/source vertex, the previously proven
optical first-jet model may be used with its exact image constraints and
a separate controlled distance remainder. Finite z_i ~0.01–0.1
is NOT by itself a certified first-jet remainder domain.
The actual CF4 Vcmb is a **released frame-transformed recession
velocity proxy**; it is not a measured latent exact source redshift.
Without a physically fixed congruence and a source/observer frame
conversion, general GR coefficients must not be filled with fitted
catalogue harmonics merely because angular ranks are nonzero.

**CF4 generative model (symbolic physical target):**

For every source group i, integrate a latent emission distance r_i,
true total frame-aligned z_i, peculiar/source motion v_i and
method-level measurement/channel metadata m_i, conditional on G.
Given shared calibration eta drawn ONCE for all selected groups,
an absolute or method-specific distance-modulus measurement y_i has
a conditional emission density f_i(y_i | r_i,z_i,G,eta,m_i)
and a selected-slot probability Z_i(G,eta).
For a proposed preselection sampling process, selected-data
joint likelihood is

       p(y | S,G) =
       {∫ p(eta|G) Π_i f_i(y_i,S_i | G,eta) d eta}
       /{∫ p(eta|G) Π_i Z_i(G,eta) d eta}.

The above treats all fixed slots as a single jointly
selected experiment. The separate law

       ∫ p(eta|G) Π_i [f_i(y_i,S_i|G,eta)/Z_i(G,eta)]deta

is appropriate ONLY if eta is independently drawn from its original
prior and each slot is then conditioned for the declared process.
It is generally *not equal* to the first expression.
If actual eligibility/target selection on published DMzp is itself
a derived outcome of a correlated multi-method pipeline, the
correct f_i/S_i must be constructed upstream, not from post hoc
DMzp per-row shifts. No false empirical selection law was admitted.

**Exactly integrable Gaussian shared-offset submodel:**

If, for a registered measurement channel, y=m(G)+1*eta+eps,
eta~N(0,tau_eta^2), eps~N(0,D) independently, D=diag(sigma_i^2),
then y marginally follows

        N(m(G), C),   C=D+tau_eta^2 11^T.

The log determinant, inverse and log likelihood are given
exactly by matrix determinant lemma / Woodbury. The physical
calibration prior tau_eta, mean and cross-method dependence are
*inputs*, not inferred from the 24 release rows.

**Unanchored calibration-scale gauge:**
For the explicit low-redshift PROXY
    m_i(Hproxy)=25+5 log10(Vcmb_i/Hproxy)
(which is not an exact GR dL model), define
    x=(5/ln 10) ln(Hproxy/H_ref).
Then m(Hproxy)=m(H_ref)-x. If eta has no absolute external anchor,
    (eta,x) -> (eta+Delta,x+Delta)
leaves the observations unchanged. Profiled eta therefore yields
an Hproxy-invariant chi-squared exactly. An eta prior narrows this
gauge *because of that assumed external prior*; such narrowing is
not an independent H0 measurement.

**One internally coherent Planck observation law:**

Let the common physical radiation history G produce a true emitted
sky T_G and Planck-band foregrounds f_s. Each released split
s∈{HM1,HM2} is generated by a split-specific processing operator
P_s with common and split residuals:
    y_s = P_s[T_G,f_s,theta_inst] + n_s + c,
where c is shared residual calibration/systematics. For the
SAME finite 32-vector coordinate space and under a declared
Gaussian block covariance C_ij, define m=(y1+y2)/2 and
d=(y1-y2)/2. Their exact block moments are

    C_m=(C11+C22+C12+C21)/4
    C_d=(C11+C22-C12-C21)/4
    C_md=(C11-C12+C21-C22)/4.

If independent equal split noise Cn exists alongside common Cc,
then C11=C22=Cn+Cc, C12=C21=Cc and
    C_d=Cn/2,  C_m=Cn/2+Cc,  C_md=0.
Thus d is blind to Cc, so a small half difference cannot certify
small shared residual systematics. Without an external model for
C11,C22,C12, a single observed HM pair cannot estimate C_m or
be assigned a physical PTE. A Gaussian model is one coherent
submodel, not the only physical Planck law.

A unified Bianchi/HTT inference may ONLY combine Planck and CF4
after integrating jointly over a *shared* G and all necessary
cross-survey nuisance and source overlap, with Planck
processing/selection and CF4 preselection conditions kept
distinct. Multiplying dependent finite-rank diagnostics is not
a generative likelihood.

## R6–R8: Actual symbolic and data checks

Wolfram exact identities:
- n=3 C=D+tau²11^T determinant-lemma residual 0 and
  Woodbury inverse residual identically zero.
- A common shared split systematic Cc contributes to split-mean
  covariance but not half-difference covariance, exactly.
- Change H->H exp(t) together with eta->eta+5t/ln10
  leaves model mean unchanged. Correct log-base relation was checked.
- Prior loops: radial q-alias polynomial identity and GR
  boost Jacobian convention already independently checked.

Implemented SciPy/NumPy mathematical tests verify the
Gaussian marginal against dense multivariate normal,
two alternative selected conditioning laws, zero-variance
collapse, normalized no-truncation limit, proper error
dimension, absolute-scale gauge invariance, and source
split covariance / missing HEALPix coarse reduction.
These mathematical tests do not certify survey selection or
the true Planck noise law.

The real 24 CF4 method-group observations show:
- DMzp-DMsnIa=-0.147 mag in 22 records; -0.326 and -0.422
  in the remaining two to 0.001 release precision.
- Under scenario independent extra peculiar widths
  sigma_v=0,150,300,500 km/s, fitting a free common
  intercept makes the Hproxy profile chi-squared
  invariant under proxy H_ref changes. None is a physical
  H0 result.
- In a declared counterfactual per-method modulus selection
  interval [31,35.6], preselection and per-slot conditioning
  log likelihoods differ if shared tau_eta>0.
  This is a valid computational **model comparison of
  experiments**, not a measured CF4 selection probability.
- No change to PR179 prior H_ONLY and q-withheld admission.

Planck external-source intake:
- Official HM1, HM2 and independent HM-missing-pixel
  intensity mask identified at IRSA/Planck PR3; local
  source files qualified by their byte size and SHA-256
  (final receipt in loop4 Planck result).
- A split difference measured from a single real
  observing pair is not an E2E ensemble noise law.
  Results remain source-level/conditional diagnostics.

## R9–R10: Reusable law and next scientific inputs

The main new theorem-scale contributions are explicitly
**conditional mathematical constructions**, not novel
unrestricted relativity no-go results. Source provenance
and the physical sample-space assumptions are an essential
part of each equation above.

Next physical work after this bounded loop:
1. Admit/derive actual Planck HM correlated split and
   component-separated foreground/systematic covariance
   and transform its true full-sky boost/Bianchi source
   through split-specific P1,P2 with the documented masks.
2. Obtain event/object-level CF4 method calibration matrix
   and actual per-survey selection generators, avoiding
   reading the post-processed DMzp twice.
3. Derive a genuine finite-distance optical Jacobi
   remainder and source-congruence interface from HTT;
   then fit the shared physical state G across probes.
4. Preserve old blocked G08 native Bianchi atlas status
   independently of the completed mathematical/numeric
   input-intake and gauge-law experiments.

Research execution modes: native subagent NOT_RUN because
the current host has not exposed a native spawn/collect tool;
serial local scientific calculations and symbolic Wolfram
verification were used. Independent second researcher
review not claimed.

## Extended source evidence: entire CF4 group catalogue and Table2 calibrators

The source audit was carried beyond the original 24 groups.
For every one of 37,825 groups with positive DMav/e_DMav
in actual released Table3, DMzp-DMav = -0.147 mag at the
0.001 mag published resolution.
Another 228 groups have no positive DMav/e_DMav and instead
have a direct DMcal. All groups with positive DMcal total
336; 108 also have a DMav weighted group mean, of which
42 have SN Ia group observations too.
The group median DMcal-DMav among 108 overlaps is
about -0.133 mag; this is NOT an absolute zero-point
posterior, because released group calibrator uncertainties
and cross-method anchor covariance remain unspecified.

Table2 supplies individual galaxy marginal uncertainties:
in 55,877 records there are 446 TRGB, 69 Cepheid,
6 maser and 1,004 SNIa method fields with positive
reported uncertainty. These are published field counts,
not counts of independent calibration anchors.

Joining individual Table2 records to the Table3
group 1PGC identifier recovers direct TRGB/Cepheid/Maser
entries for 311 of 336 positive group DMcal rows.
25 groups have no matching individual entry under this
literal group join. Simple inverse-variance weighting
of matched individual method moduli matches the
published group DMcal within 0.001 mag for 257/311,
but the remaining group aggregation discrepancies
can be substantial. An independent event/source
membership and calibration error law must be
established before assigning physical probabilities.
Do not invent missing group data.

**Generalized multi-method shared calibration.** For an
unobserved physical same-congruence distance modulus
vector m(G), source-loading matrix Z and latent
multi-method offset eta with declared positive
semidefinite covariance K_eta:

    y=m(G)+Z eta+eps,
    eta~N(0,K_eta), eps~N(0,D),
    C=D+Z K_eta Z.T.

Let K_eta=L L.T. The determinant lemma and Woodbury
identity yield

 log|C|=log|D|+log|I+L.T Z.T D^-1 Z L|
 C^-1=D^-1-D^-1 ZL (I+L.T Z.T D^-1 ZL)^-1 L.T Z.T D^-1.

This is internally coherent for all supplied positive
diagonal D and PSD K_eta, including singular K_eta,
but the required real-world Z, calibration K_eta and
upstream method/source selection law have not been
authenticated by Table2/3/4 alone. The implemented
Gaussian submodel is checked against a dense oracle.
The k-dimensional actual CF4 selected-survey
normalizer is NOT yet implemented/admitted.


## External code-lane findings: reusability versus physical source law

The external literature/code audit identified
https://github.com/carronj/plancklens and its public Planck
SMICA PR3 FFP10 parameter example. It implements much of Planck
2018 lensing inverse variance filtering, QE response and simulation
mean field, but depends on release/site-specific data and is not a
validated common Planck HM1/HM2 foreground-plus-noise joint
likelihood, nor the desired Bianchi/observer-boost transfer.

https://github.com/harrydesmond/Volume_Prior/ includes
analyse_CF4.py with CF4 distance-prior and selection
experiments; these are relevant prior-art comparators. A
phenomenological source law is not by itself the actual
full-release calibrated cross-method sampling law.
The official Hawaii CF4 distance-velocity calculator API
is a model reconstruction and must never be imported as
independent observed peculiar-velocity truth.

This search narrowed the implementation options without
claiming unavailable source covariance has been recovered.
