# Joint selection bounds and the released two-redshift observable

Owner: htt. Scope: C0, DERIVED/CONDITIONAL finite inverse-problem statements.
Transfer source: none (selection), restricted analytic endpoint optics (distance).
This work consumes the original scientific DAG without changing its acceptances.
No new physical transfer, likelihood fit, native solver or historical CAS admission
is asserted. Framing/derivation: `legacy_theory_20261022`, requested Astra/xhigh;
observed UNKNOWN. Independent review is recorded separately.

## 1. Normalized joint selection uncertainty

Legacy #533 supplied catalogue-level normalization; #552/#553 supplied coupled
event support on retained joint draws. Combine them without treating overlapping
windows as independent observations. Let each atom i contain a **complete joint
state**, its original draw ID, all windows and shared calibration variables.
Reference weights satisfy p_i>0 and sum p_i=1. Positive **unnormalized importance
weights** r specify a target law on the same support:

\[
 q_i(r)=p_i r_i/Z(r),\qquad Z(r)=\sum_i p_i r_i,
 \quad r\in\mathcal R=\{a\le r\le b,\ Br\le d,\ Er=f\},
 \quad 0<a_i\le b_i<\infty.
\]

Assume this polytope is nonempty. Weights r are dimensionless; the normalized
Radon–Nikodym ratio is q_i/p_i=r_i/Z, not r_i itself. For a population
selected law P_S(i) proportional to s_i P(i), r_i=1/s_i; an empirical selected
catalogue alone does not establish that population law or its coverage. For
posterior/reference atoms, r is proportional to the full target/reference joint
density ratio. Its unnormalized target kernel includes prior, shared calibration
and any state-dependent catalogue-level selection normalizer; the remaining common
normalization is Z. If bounds are instead supplied for the **normalized** density
ratio, the additional equality p^Tr=1 must be imposed. For example p=(.3,.7),
event=(1,0), normalized ratios in [.5,2] give [.15,.6]; unconstrained unnormalized
weights in that box give [3/31,12/19]. These are distinct sensitivity classes.
Inverse detection probabilities cannot simply be assigned to working Gaussian
draws. Source-qualified bounds on these joint importance weights remain missing
for the physical application.

For a strict event g>tau, binary certified brackets e^-<=1_E<=e^+ give

\[
 L=\min_{r\in\mathcal R}\frac{(p\odot e^-)^Tr}{p^Tr},\qquad
 U=\max_{r\in\mathcal R}\frac{(p\odot e^+)^Tr}{p^Tr}.
\]

These are outer bounds. They are sharp for the relaxed class in which unknown
events can be completed independently of r. A common physical parameter coupling
event values and weights may narrow them. For a closed attainable scalar interval
[l_i,u_i], e^-_i=1[l_i>tau], e^+_i=1[u_i>tau]; equality is nonexceedance.
Nonattained endpoints require separate endpoint logic.

Set t=1/(p^Tr), y=tr. Each endpoint is the linear program

\[
 \operatorname{min/max}(p\odot e^{\mp})^Ty,\quad
 p^Ty=1,\quad at\le y\le bt,\quad By\le dt,\quad Ey=ft,\quad t\ge0.
\]

**Proof.** Positivity gives 0<p^Ta<=Z<=p^Tb. Every admissible r yields a feasible
(y,t) with identical objective. Conversely t=0 would force y=0, contradicting
p^Ty=1. Thus r=y/t recovers every feasible transformed point and its objective.
Compactness gives attained extrema. Event bracketing gives containment; arbitrary
compatible completions give sharpness for the relaxed class. This is the standard
[Charnes–Cooper transformation](https://iiif.library.cmu.edu/file/Cooper_box00010_fld00009_bdl0001_doc0001/Cooper_box00010_fld00009_bdl0001_doc0001.pdf),
Eqs. (2.1)–(3), Theorem 1. Bounded-selection sensitivity is established literature,
including [Aronow–Lee](https://doi.org/10.1093/biomet/ass064); only its publisher
abstract was accessible in this intake. No mathematical priority claim is made.

For box-only uncertainty and D={e^-=1}, P={e^+=1}, monotonicity yields

\[
 L=\frac{\sum_Dp_i a_i}{\sum_Dp_i a_i+\sum_{D^c}p_i b_i},\qquad
 U=\frac{\sum_Pp_i b_i}{\sum_Pp_i b_i+\sum_{P^c}p_i a_i}.
\]

Numerator and denominator share the same weights. An unsupported target mass
at most delta, with unrestricted event membership, extends the interval to
[(1-delta)L, delta+(1-delta)U]. With no justified support bound delta=1, the
answer is [0,1]. Undefined physical Q remains an unresolved **domain**, with any
event completion reported conditionally; this construction does not define Q.

For p=(1/5,3/10,1/2), e^-=(0,1,0), e^+=(0,1,1), r in [1/2,2]^3,
the exact interval is [3/31,16/17]. The witnesses are (2,1/2,2) and (1/2,2,2).
Requiring r1=r2=r3 instead gives [3/10,4/5]. Adding unsupported mass<=1/10
to the box result gives [27/310,161/170]. Independent stdlib Fraction enumeration
by the theorist and the parent Wolfram call agree; [WOLFRAM_CHECK.json](WOLFRAM_CHECK.json)
preserves the latter. This is finite algebra verification, not four-axis admission.

The new consumer [selection/](selection/) reuses existing S02 aggregate event
masses from 2,048 joint draws. A Gamma sweep assumes r_i in [1/Gamma,Gamma],
giving L/(L+Gamma^2(1-L)) and Gamma^2 U/(Gamma^2 U+1-U). These are sensitivity
assumptions, not measured selection bounds. The original physical [0,1] remains.
No old draw generation, LP campaign or catalogue fit is repeated.

## 2. Pantheon+ two-redshift operator

The pinned author likelihood in [data/REPORT.md](data/REPORT.md) uses
D_cat=(1+zHD)(1+zHEL)D_A(zHD), with zHD>0.01 for its SN-only branch.
For flat FLRW, D_cat=(1+z_H)chi(z_D), z_H=zHEL, z_D=zHD. Holding the background
H(z), chi(z) fixed while varying the catalogue/endpoint fields, chi'=c/H gives

\[
 \partial_\theta\ln D_{cat}=
 \frac{\partial_\theta z_H}{1+z_H}
 +\frac{c\,\partial_\theta z_D}{H(z_D)\chi(z_D)},\qquad
 \partial_\theta[m_{corr}-5\log_{10}D_{cat}]
 =\partial_\theta m_{corr}-\frac5{\ln10}\partial_\theta\ln D_{cat}.
\]

If theta also varies background cosmological parameters, add the explicit
(partial_theta chi at fixed z_D)/chi term. The derivatives specify an experiment:
varying a physical state and regenerating
catalogue corrections differs from conditioning on fixed released fields. With
fixed measured fields, these field derivatives are zero. This chain rule alone
does not provide the physical derivatives of the PV correction or standardization.

For the restricted bolometric endpoint model of FRONTIER_20261020, use signature
(-,+,+,+), dimensionless beta=v/c, sourceward n and a common unperturbed z.
Write s=n·beta_s, o=n·beta_o, zeta_H=delta z_H/(1+z), zeta_D=delta z_D/(1+z),
k_m=(ln10/5) delta m_correction and A=c(1+z)/(H chi). The raw bolometric
log-distance perturbation at fixed background emission radius is 2s-o. Subtracting
the catalogue distance perturbation gives

\[
 R=2s-o+k_m-\zeta_H-A\zeta_D.
\]

If z_H is the uncorrected heliocentric observed redshift, zeta_H=s-o, hence
R=s-A zeta_D+k_m. Writing zeta_D=s-r-p, with r the reference-observer radial
velocity and p the subtracted estimated source-PV redshift perturbation, gives

\[
 R=(1-A)s+Ar+Ap+k_m.
\]

When z_D=z_H and k_m=0 this reduces to (1-A)s+Ao, the original same-observer
formula. All terms are dimensionless; multiply R by 5/ln10 for magnitude residual.
This bolometric idealization does not establish how released SALT2 standardized
band magnitudes transform. The source-qualified responses k_m and zeta_D and
normal/CMB relation are still needed. The old redshift-only source-model K is a
different operator. Fixed public Pantheon total covariance is consumed once;
no additional stochastic PV term is permitted without a qualified decomposition.

Wolfram gives zero symbolic residual for the chain rule and endpoint substitution.
The existing 651-row zCMB projection is retained as its original fiducial result;
645 rows differ in zHD and 556 pass the released SN-only zHD cut. These source
checks motivate a new contract; they do not retroactively change that experiment.

## 3. What would close the physical obligations

F07 needs a justified joint ratio/selection set, full contributors/overlap, shared
calibration/velocity law and supported mass. H02/S02/S04/K04 stay open. F04 needs
the physical response of the actual two-redshift and standardized-magnitude
pipeline, selection, and finite optical/calibration/flow remainder. Its existing
rank does not establish physical identifiability. B02/V03 still require a source-
qualified polarized all-m/global-history transfer; K03 needs physical nonradial
response and joint PM/NNR/clock errors. All original DAG states remain unchanged.
