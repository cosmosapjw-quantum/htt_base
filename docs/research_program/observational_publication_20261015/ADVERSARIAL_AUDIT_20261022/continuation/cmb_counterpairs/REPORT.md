# A22-07 — legacy counterpairs and ordered morphology on one processed sky

Owner obsstat; C0 PROCESSED_MAP_DIAGNOSTIC; transfer none. Code intake e638029f.
New statistic/model: signed ordered Wigner J234, largest power-tensor axis
alignment23 and component tensors, with phase/orientation/parity controls.
Next consumer A22-08; original L03/B02 remains input blocked. Review pending.

The donor blob16b1b623a4f74fe7690bde5fc95d29e6d8e1bc9a (PR365/internalPR257)
was read, and only `_apply_intervention_to_alm` algebra was ported. Three actions
are (-1)^ell, exp(-i*m*.41), and exp(i*sign(m)*m²*.37). The donor's larger workflow,
old p=.039, and branch-specific admissions were not imported. Function-level tests
extract the single frozen donor function and compare each transformed coefficient.
The existing current `htt/obsstat/lowell_poles.py` supplies the normalized tensor.
No wholesale branch merge or new inference ownership is involved.

[EXPERIMENT.json](EXPERIMENT.json) was written before any new observed morphology
score. A separate Astra theory task checked five synthetic real fields, arbitrary
SO3 rotations and the exact nonzero/phase witnesses before looking at observations.
It framed the statistic; a different fresh reviewer checks the final execution.

## Conventions and falsifiers

Use complete orthonormal Condon–Shortley coefficients with a_l,-m=(-1)^m conj(a_lm).
P_l=sum|a_lm|², C_l=P_l/(2l+1). Normalize each multipole first, then
J234=Im sum(3j(2,3,4;m2,m3,m4)*a2*a3*a4)/sqrt(P2*P3*P4).
The ordered columns are2,3,4. No zero-m Gaunt factor is included; it would erase
this odd-sum statistic. For a real field the contraction is pure imaginary,
proper-rotation invariant and parity odd. Exact fixture a20=1,a31=1,a3,-1=-1,
a41=i,a4,-1=i gives J=-sqrt(21)/42. Another fixture gives J(theta)=sqrt(14)/84*cos(2theta).
This is a finite algebraic statistic, not a complete invariant ring or family atlas.

For ell2/3 the trace-one angular-momentum power tensor has principal axis defined
by its largest eigenvalue. The top-minus-middle eigenvalue gap<=1e-10 abstains.
A23=|vmax2.vmax3|² is undefined in that case. Both tensors are stored separately
in xx,xy,xz,yy,yz,zz order. Abstention propagates to the joint score; no zero fill.
The chosen joint max_products max(|J|,A23) is descriptive, parity even and unscaled:
its components have unequal allowed ranges. It is not a parity discriminator.

Four focused tests passed in7.44s. Controls include exact donor equivalence,
reality and power, nonzero and nonlinear-phase identities, arbitrary-axis SO3
invariance and tensor covariance at1e-12, degenerate-axis abstention, wrong-sky and
wrong-mask rejection. Theory-task initial package import failed on missing common;
direct numerical-kernel loading resolved that local import without changing algebra.
The production implementation uses the direct numerical-kernel path explicitly.

## Source linkage and actual execution

The five products are full/hm1/hm2/oe1/oe2 from Planck PR3 R3.00 SMICA: one observed
sky, distinct source payloads and split identities. Source headers read here give
Galactic, NESTED2048, COSMO Q/U, K_CMB. The prior qualified native processing masks
Q/U by common AND-of-three PMASK>0.5 before spin harmonic analysis; NPZ fields are
E/B pseudoalms of that masked delivered Q/U. Their source/metadata/payload hashes,
common mask bfae5917211f8ecce2a99ee8b996e168dcc8df18e1a6e6d4bdee638063ae05d3,
recipe and product identities are frozen and checked. No raw multi-GB source was
rehash/reprocessed; retained pins and current headers were reused. Delivered beam
stays in place; no extra smoothing/deconvolution. Only E is scored, so no incorrect
scalar parity is imposed on polarization B.

| product, L32 | signed J234 | A23 | phase-control J234 |
|---|---:|---:|---:|
|full|-.01501419|.67950074|.02273250|
|hm1|.00901939|.94467353|-.01684278|
|hm2|-.08244880|.80919088|-.05852078|
|oe1|-.06672143|.92961485|-.05660585|
|oe2|.02447615|.70921829|.00346998|

All axes are defined. Parity flips J, proper rotations preserve J/A23 while rotating
tensor components, and nonlinear phase changes J on these products. Nonseparation
is an allowed outcome for other fields, not a forced failure. These interventions
act on processed output coefficients. They are not equivalent to physically
rotating/inverting the sky before a fixed asymmetric polarization mask.

The predeclared L32/L64/L128 cached-prefix comparison gives exactly zero J/A23
change on each product, with joint max .9446735266080256 at each cutoff. This is
uninformative about physical cutoff/high-mode leakage: the selected low-ell
coefficients are identical prefixes. It is neither a tail bound nor convergence
or null coverage. It motivates a separately specified changed-operator diagnostic
in A22-08, not an additional completed physical acceptance.

No calibrated p, null rank, independent-sky increase or Bianchi-family claim is
made. Matched processed total CMB+foreground+noise, weights/mask/beam/selection,
joint realization IDs, predeclared trials and adequate MC precision remain needed.
Four old PR3 split/eight-pair computations were not replayed; no PR4 NESTED field
was added to a RING residual.

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/cmb_counterpairs/test_morphology.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/cmb_counterpairs/morphology.py
```

[Result](RESULT.json), [figure](MORPHOLOGY.png). Requested parent Sol/high,
theory/reviewer Astra/xhigh; observed UNKNOWN. No solver/ODE or four-axis CAS claim.
