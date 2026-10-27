# R36-07 continuing positive-intensity envelope research

This is research by `/root/r36_foreground_fresh_review`, requested gpt-6-astra/xhigh, observed runtime UNKNOWN. The author contributed the new method and is not its independent reviewer. It continues the same R36-07 issue. It does not amend the sealed partial candidate `34ac36b0...2129cc9`, its independent review, the frozen implementation contract, the input HOLD, or any original R31/R32/original42 acceptance.

## 1. Exact conditional source model and units

Set nu0=30 GHz, Tcmb=2.7255 K, beta0=-3 in Rayleigh-Jeans temperature convention, delta=beta-beta0, and t=log(nu/nu0). Let b0=dB_nu0(Tcmb)/dT in W m^-2 Hz^-1 sr^-1 K^-1. A reference-intensity measure mu(dn,ddelta)>=0 has units K_CMB times solid angle; its polarized measure eta is complex with |deta|<=dmu. This is a statement about emitter total variation, not the magnitude of a signed harmonic integral. Intensity is

    I_nu(dn) = b0 (nu/nu0)^(-1) integral exp(t delta) mu(dn,ddelta).

The -1 exponent is beta0+2: the RJ-to-specific-intensity factor must not be omitted. The complex reference polarization is Q+iU, Galactic COSMO, with the same spin frame as the original candidate. Thermodynamic conversion at another frequency uses dB_nu/dT, not a new RJ approximation. 1 MJy/sr = 10^-20 W m^-2 Hz^-1 sr^-1.

This model is conditional on a positive, unabsorbed, common power-law emitter decomposition across the source and target bands, and the same reference emitter sky across their observing epochs or an explicit bound on temporal changes. The acquired far-infrared data do not prove that synchrotron has such a decomposition up to 1.85 THz. Other positive intensity components make a total-intensity upper constraint conservative. Unmodelled polarized components do not disappear and need their own bound.

## 2. Finite passbands: no delta-frequency approximation is needed

For a positive source passband R_j(nu) and reported-intensity normalization N_j, define

    H_j(delta) = (b0/N_j) integral R_j(nu) (nu/nu0)^(-1) exp[t(nu) delta] dnu,
    m_j = H_j(0),
    dw_j = R_j(nu) (nu/nu0)^(-1) dnu / integral R_j(nu) (nu/nu0)^(-1) dnu,
    tbar_j = integral t(nu) dw_j.

Jensen's inequality gives H_j(delta)>=m_j exp(tbar_j delta) for every real delta, not just a finite test grid. A certified positive lower response may replace R_j on any nonzero subband, with the actual calibration N_j retained. A conservative upper bound on N_j may be used for a lower H_j. No assertion of zero out-of-band response is needed when omitted response is nonnegative. Signed lobes or unknown subtraction require a separate lower bound.

Let a=-tbar_minus>0 and b=tbar_plus>0. Suppose the measured, positive source functionals have simultaneous upper bounds Z_minus and Z_plus and quantitative angular response domination constants kappa_minus,kappa_plus>0. Then

    integral exp(-a delta) dmu <= J_minus = Z_minus/(kappa_minus m_minus),
    integral exp( b delta) dmu <= J_plus  = Z_plus /(kappa_plus  m_plus).

These statements also hold for coupled angle/frequency responses if their aggregate kernel is bounded below by kappa_j H_j(delta) on every consumed sky/spectral atom. Source weights must be fixed independently of target residuals, or uncertainty must be simultaneous over their selection.

For DIRBE 240 um, calibration assumes nu I_nu constant, N=integral R(nu) nu_c/nu dnu. The chosen beta0=-3 baseline therefore gives m=b0 nu0/nu_c exactly for that complete positive passband. The acquired rounded Pass3B response table, with an explicitly chosen piecewise-linear-in-frequency interpolant, gives tbar=3.709985311039402 and m=0.6488586304557223 MJy/sr per K_CMB30. These numerical table integrals are not an empirical response-uncertainty certificate. The table has positive entries from 663.867 to 1839.748 GHz; the interpolant extends to neighboring zero entries, 658.721 to 1854.119 GHz. Its normalization is 4.988996648457449e11 Hz; the paper's rounded effective width is 4.95e11 Hz. This small difference is not silently forced to equivalence.

## 3. Whole-line moment and exponential envelopes

For k>=1, max_{u>=0} u^k exp(-c u)=[k/(e c)]^k. Splitting delta into two half-lines proves

    M_k := integral |delta|^k dmu
        <= [k/(e a)]^k J_minus + [k/(e b)]^k J_plus.

This is a valid explicit envelope, not a claim that the coefficients solve the sharp two-constraint moment optimization. No compact beta support, truncated grid, or prior tail cutoff enters the proof. For k=0, the simple bound is J_minus+J_plus. A sharper mass bound follows by Holder:

    M_0 <= J_minus^[b/(a+b)] J_plus^[a/(a+b)].

More generally, for -a<=t<=b,

    integral exp(t delta) dmu <= J_minus^[(b-t)/(a+b)] J_plus^[(a+t)/(a+b)] := E(t).

Outside this interval these two exponential constraints alone do not control arbitrary exponential targets: for example put mass exp(-b d) at delta=d and let d->infinity for t>b. A wider actual source passband can contain additional information; failure of this sufficient Jensen envelope outside its interval is not a proof that the full passband constraints fail.

All factorial complex moments satisfy ||integral delta^k deta/k!|| <= M_k/k!. Polarization cancellation cannot increase this total-variation upper bound.

## 4. Harmonic mapping and the existing metric

For a common full-sky retained harmonic operator L(n) mapping the two real Stokes components to E2,E3,B2,B3 in the existing 24-coordinate convention, the spin addition theorem gives

    L(n)^T L(n) = [sum_{l=2,3}(2l+1)/(4pi)] I_2 = (3/pi) I_2.

Thus ||L||op=sqrt(3/pi)=0.977205... everywhere. For the 12 B coordinates alone the norm is sqrt(3/(2pi)). A mask of magnitude at most one preserves this upper bound. The reproducer independently constructs all 24 synthesis bases with healpy/libsharp at NSIDE4 and checks the identity at every pixel; maximum error is 6.66e-16. This is a small analytical fixture, not a rerun of the seven native maps or their noise.

For synchrotron rows 0,1,5 in the frozen nine-moment order, the component contribution obeys

    rho_syn <= sqrt(3/pi) sqrt[(D_0 M_0)^2 + (D_1 M_1)^2 + (D_5 M_2/2)^2].

The exact stored D is consumed from the existing ACTUAL_GEOMETRY.npz. The result bounds only these three rows. Dust rows, omitted polarized components, and response/Taylor errors are separate. It is not the full physical nine-row rho.

Different native band beams and masks require a conservative bound on their actual retained kernels or direct positive response domination. Exact full beam equality is unnecessary. A normalized, positive, rotation-invariant full-sky convolution preserves the global flux, whatever its beam width; this suffices when its actual applicability and absolute calibration are established. Masked discarded high modes cannot be reconstructed by dividing only low-l beam factors.

## 5. Exact total-variation Taylor remainder

Write r_2(t delta)=exp(t delta)-1-t delta-(t delta)^2/2. For any -a<=t<=b,

    integral |r_2(t delta)| dmu <= E(t)+M_0+|t| M_1+t^2 M_2/2.

This finite bound includes the endpoints. For -a<t<b, Taylor's integral/Lagrange remainder gives the alternative

    integral |r_2(t delta)| dmu
      <= |t|^3/6 { [3/(e[a-max(-t,0)])]^3 J_minus
                   +[3/(e[b-max(t,0)])]^3 J_plus }.

The smaller bound may be used. A cubic-bound denominator tending to zero at an endpoint does not make the exact endpoint remainder unbounded. At t=0 the exact remainder is zero. A native target passband must integrate the positive absolute bound with its actual spectral response and thermodynamic normalization; the reproducer's seven nominal-frequency examples are explicitly illustrations, not native-band results.

Frequency-independent complex polarization weights give the displayed moment expansion. If phases or polarization fractions vary with frequency, their deviation from the reference weight needs an additional term. The trivial difference bound |p(nu)-p(nu0)|<=2, when each fraction has modulus <=1, yields a finite but possibly very large extra contribution 2E(t) times the baseline conversion. It does not justify ignoring Faraday/depolarization physics or calling a small Taylor remainder measured.

## 6. Source measurements and uncertainty accounting

Actual new public data acquired and hashed:

* Retained-source Haslam destriped-only: 3,145,728 finite NSIDE512 pixels, mean 34.7769775348 K_RJ, delivered equal-area integral 437.020388549 K_RJ sr.
* Haslam nofilt: same complete pixel count, mean 34.7842074411 K_RJ, integral 437.111242231 K_RJ sr. The difference is a processing comparison, not an uncertainty bound. No CMB/monopole or positive source subtraction was performed here.
* Unsubtracted DIRBE 240 um annual map: all 393,216 pixel IDs exactly once, positive observation counts everywhere, zodiacal-light-removal flag false, mean 23.1160536644 MJy/sr. There are 956 negative noise-dominated pixels; they are retained. The uniform nominal-area sum is 290.484897489 MJy. CSC pixels are approximately equal-area, so this is an explicitly chosen sum, not an exact physical sphere integral.

For any fixed nonnegative pixel weights q and correctly specified mean-zero released errors with marginal standard deviations sigma_i, unknown cross-pixel PSD completions obey sigma(q^T e)<=sum q_i sigma_i. Cantelli gives a one-sided probability-alpha margin sqrt[(1-alpha)/alpha] sum q_i sigma_i. This requires neither cross-pixel independence nor a Gaussian assumption, but it does require valid marginal second moments and any bias to be separately controlled. DIRBE's StdDev is already the standard deviation of the weighted mean. Dividing again by the observation count would be wrong.

For the chosen DIRBE uniform sum, the worst-correlation sigma is 14.158... MJy (exact value in NUMERIC_RESEARCH.json); its conditional 95% Cantelli noise margin is about 61.7 MJy. The paper supplies 11.6% absolute-gain and 2 nW m^-2 sr^-1 offset error estimates at 240 um, the latter 0.160110... MJy/sr. They are common systematic terms and cannot be reduced by sky-pixel count. The Haslam source reports approximately 10% calibration and 3 K zero-level accuracy. These estimates must be translated through a declared joint error model or validated intervals, not relabeled as deterministic guarantees.

If the true statistic z, gain g>=g_min>0, additive calibration allowance B, map-processing loss allowance L, and random error e satisfy y >= g z-B-L+e, then on a one-sided event -e<=u,

    z <= (y+B+L+u)/g_min.

One can allocate coverage across noise, gain and offset by a union bound; no independence is needed. A gain lower bound reaching zero yields no finite upper bound. A conservative source uncertainty model is a legitimate explicit model choice, not a requirement for an exact calibration oracle. Its assumptions and confidence level must be reported. No such newly qualified joint model is claimed by the illustrative numbers below.

## 7. Actual conditional calculation, and why it is not an operational radius

Temporarily assume (only for sensitivity arithmetic) that the two delivered sums are exact positive full-sky fluxes, both kappa values equal one, Haslam is monochromatic at 408 MHz, and the pure power-law decomposition extends across both source bands. Then a=4.29768548624, J_minus=0.00112534268278 K_CMB30 sr, J_plus=447.685957856 K_CMB30 sr. The envelope gives M0<=1.139241318, M1<=44.39230983, M2<=17.60763121 in the respective dimensionless-index moments of K_CMB30 sr, hence rho_syn<=7.898526172 K_CMB. This is finite and highly non-discriminating. It is not a measured contamination budget; no original identified-response curve is relabeled physical and no original noise calculation was rerun.

The public source intake substantially improves the earlier absence of a higher-frequency all-sky absolute product. However, the actual source documentation supplies limitations which matter to a bound over arbitrary positive emitting measures:

1. Haslam is assembled from several surveys. A nominal-frequency label is not a calibrated monochromatic functional for arbitrarily large beta. A lower positive passband response, with calibration conversion, suffices; the exact passband shape is not required. Retaining sources avoids the large source-removal defect, but scan/baselevel/interpolation and destriping uncertainty still need a conservative aggregate loss allowance or a qualified global-flux interpretation.
2. DIRBE annual pixels average robustly processed weekly observations. Its supplement describes varying subpixel centroids/orientations and pixel-dependent PSFs, and advises individual observations for point-source photometry. Thus complete populated output pixels plus unit-normalized individual beams do not by themselves prove that this chosen map sum lower-bounds every positive sky atom with kappa=1. An aggregate lower response or controlled loss bound could resolve this without an exact beam model. No actual sky hole is claimed.
3. Published absolute gain/offset information is present. The missing numerical payload is a source-to-true-functional upper bound including the relevant processing/response uncertainty under a declared statistical model, not a blanket demand for noiseless data.

For a precise counterexample to the insufficient angular implication, let two observation kernels have rows (1-e,e) and (1-2e,2e), 0<e<1/2. Every entry is positive, both kernels are unit-normalized, and the sky mu=(0,1/e) produces data (1,2). Yet the sky mass is 1/e and can grow arbitrarily across this family. The missing quantity is a numerical lower column-sum bound, not positivity or populated outputs. At fixed known e the mass bound is finite. This example does not assert that actual DIRBE beams equal these kernels.

The previously inspected FIRAS 6067x43 spectra remain another possible source route. Thirty-one S7 pixel centres beyond 3.5 degrees are not proof of a beam hole; the representative Moon profile is not the integrated scan kernel. Its signed spectral/calibration and aggregate spatial response must enter a positive-functional certificate. The unresolved C^2-versus-diagonal-covariance numerical relation is not made an equivalence gate here. Neither the old FIRAS intake nor the seven-band noise products were rerun.

## 8. Spectral remainders and unrestricted dust: explicit counterexamples

The synchrotron theorem cannot be promoted to a general curved-spectrum theorem. On separated lower and upper source bands, take a positive smooth spectrum normalized around t=0,

    f_A(t)=A exp[-k_A t^2],  k_A=2 log(A)/d^2,

where d>0 is their minimum log-frequency distance from zero. Both source responses are <=1/A after positive baseline weighting, but f_A(0)=A. The reproducer integrates this witness through the actual DIRBE tabulation. This is an arbitrary positive smooth-spectral counterexample, not a claim that the standard optically thin synchrotron electron kernel can realize every such spectrum. If that physical kernel or a curvature bound is adopted, it must be analyzed in its own class. Unbounded absorption can also hide source-band intensity, but the frozen contract already excludes absorption; this is a reminder of scope, not an additional demanded gate. Any allowed attenuation needs a nonzero lower response or a separately bounded hidden contribution.

For normalized modified blackbody intensity at nu_d=353 GHz,

    S(nu;beta,T)=(nu/nu_d)^(beta+3) expm1(h nu_d/kT)/expm1(h nu/kT).

Two different failures of an unrestricted dust extension occur:

* At fixed beta and fixed reference amplitude, T->infinity gives S->(nu/nu_d)^(beta+2). Every finite passband response stays bounded, while the frozen coordinate t_d=(T-20)/20 and its second factorial moment t_d^2/2 diverge. Thus even perfectly measured finite source intensities do not bound this particular temperature-moment norm. This is a coordinate-specific obstruction; it does not prove every direct observable bound is impossible.
* Let x=h nu_d/(kT)->infinity and beta=x-3. For r=nu/nu_d away from one, log S=x[log r-(r-1)]+o(x), strictly negative and linear in x. Choose reference amplitude A=x. Haslam and the entire acquired DIRBE 240 um support lie away from 353 GHz, so both responses vanish exponentially while A diverges. A positive broad target band containing 353 GHz is also unbounded: Laplace's method gives integral A S dnu ~ nu_d sqrt(2 pi x). The numeric witness uses actual DIRBE quadrature and preserves logarithms instead of underflowing to false zeros.

These are statements about the mathematical MBB family with arbitrary beta and T>0, not assertions that arbitrarily cold/hot grains exist. A physical thermal-equilibrium or grain-survival model may exclude them. The needed input is a justified restriction or tail-moment/response-domination inequality for the admitted emitter class, not necessarily a compact rectangular prior. The current source files alone do not supply it. Merely choosing typical dust temperature/index scatter would not exclude line-of-sight tails.

## 9. Precise next checkpoint for the same R36-07 issue

The new method removes a mandatory compact-beta gate for a declared power-law synchrotron class. It does not complete the nine-moment physical radius. The minimal resumable payload is:

* Two calibrated positive source upper functionals with finite uncertainty bounds and an aggregate spatial/spectral lower response, or directly a dual inequality dominating the required moment weights. A global flux-preserving response plus absolute-flux uncertainty can replace detailed angular beams. Haslam lower-passband support and DIRBE map-processing/aggregate response are the concrete source gaps for this implementation.
* A declared physically supported synchrotron spectral class across the bracket, or bounded curvature/phase/attenuation deviations, with stationarity across the source/target epochs or a variability allowance. Source measurements plus this condition must not be described as a measured spectral extrapolation.
* A dust/other-component domination or tail bound sufficient for the exact consumed moment coordinates and their TV remainder, or an explicitly authorized change to a direct observable formulation which is actually bounded. The two MBB witnesses explain why this cannot be filled by setting an arbitrary finite radius.
* A conservative native-target response norm/direct domination if connecting the new component bound to the existing actual-Y observable; preserve the original native noise results exactly.

No production repair contract is issued because its physical input fields would still be unfilled. This research result and reproducer are a concrete source/math handoff tied to the same issue. A different reviewer must evaluate this newly authored method before scientific use. Original acceptance remains false; qualified products remain empty.

## Primary source references

* NASA LAMBDA, [retained-source Haslam products](https://lambda.gsfc.nasa.gov/product/foreground/fg_2014_haslam_408_get.html) and [product description](https://lambda.gsfc.nasa.gov/product/foreground/fg_2014_haslam_408_info.html).
* Remazeilles et al., [2015 improved Haslam map](https://arxiv.org/abs/1411.3628), calibration and processing sections. Haslam et al., [The All-Sky 408 MHz Survey](https://doi.org/10.1017/S0074180900074623), absolute calibration description.
* NASA LAMBDA, [DIRBE annual map](https://lambda.gsfc.nasa.gov/product/cobe/c_anual_avskymap.html), [Pass3B response table](https://lambda.gsfc.nasa.gov/data/cobe/dirbe/ancil/spec_resp/DIRBE_SYSTEM_SPECTRAL_RESPONSE_TABLE.ASC), [Explanatory Supplement v2.3](https://lambda.gsfc.nasa.gov/data/cobe/dirbe/doc/des_v2_3.pdf), sections 5.2, 5.3, 5.6.6 and Table 5.7-14.
* Hauser et al., [1998 DIRBE CIB study](https://arxiv.org/abs/astro-ph/9806167), section 2.1 and Tables 1-2, for absolute gain/offset estimates and calibration convention. Its CIB dark-sky upper limit is not substituted for a total Galactic flux bound.

SOURCE_INTAKE.json binds the actual downloaded bytes and transport outcomes. NUMERIC_RESEARCH.json contains the measured statistics, conditional calculations and falsifier values. The source PDF downloaded from the extensionless arXiv URL is named `9806167.html` by the generic downloader; it is PDF content, correctly read by pdftotext. No content format is inferred from that suffix.
