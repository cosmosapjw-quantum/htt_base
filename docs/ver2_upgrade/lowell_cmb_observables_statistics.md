# Low-\(\ell\) CMB observables and statistics interface

## Beyond-FLRW observer-side document

This document is intentionally separate from the solver-core document. The solver evolves covariant PSTF/tetrad variables. This observer-side layer receives solver output and turns it into sky-facing quantities, exploratory low-\(\ell\) statistics, and model-comparison objects. It contains no ADM equations, no background evolution equations, and no Planck-team interpretation language.

---

# 0. Scope

Input from the solver core:

\[
T(\hat n),\qquad Q(\hat n),\qquad U(\hat n)
\]

or equivalently

\[
a^T_{\ell m},\qquad a^E_{\ell m},\qquad a^B_{\ell m}.
\]

The observer layer may also receive deterministic template coefficients

\[
t^X_{\ell m}(\lambda),\qquad X\in\{T,E,B\},
\]

or an anisotropic covariance

\[
C^{XY}_{\ell m,\ell' m'}
=
\langle a^X_{\ell m}a^{Y*}_{\ell' m'}\rangle.
\]

Output from this document:

1. harmonic coefficients and maps,
2. low-\(\ell\) scalar summaries,
3. alignment and morphology statistics,
4. template-fit diagnostics,
5. null ensembles and look-elsewhere bookkeeping.

No statistic in this document is treated as uniquely privileged. The point is to expose beyond-FLRW signatures, not to force them into an FLRW-only \(C_\ell\) summary.

---

# 1. Harmonic conventions

Temperature:

\[
T(\hat n)=\sum_{\ell m}a^T_{\ell m}Y_{\ell m}(\hat n).
\]

Polarization:

\[
(Q\pm iU)(\hat n)
=
\sum_{\ell m}a^{\pm2}_{\ell m}\,{}_{\pm2}Y_{\ell m}(\hat n).
\]

E/B definition:

\[
a^E_{\ell m}=-\frac12(a^{2}_{\ell m}+a^{-2}_{\ell m}),
\qquad
a^B_{\ell m}=\frac{i}{2}(a^{2}_{\ell m}-a^{-2}_{\ell m}).
\]

Reality condition:

\[
a^X_{\ell,-m}=(-1)^m a^{X*}_{\ell m}.
\]

A run is invalid unless the harmonic normalization, spin-weight convention, pixel ordering, and coordinate frame are stored in metadata.

---

# 2. Isotropic and anisotropic covariance objects

The usual isotropic compression is

\[
C^{XY}_{\ell}
=\frac{1}{2\ell+1}\sum_m a^X_{\ell m}a^{Y*}_{\ell m}.
\]

For a genuinely anisotropic model this is not complete. The natural object is

\[
\mathsf C^{XY}_{\ell m,\ell' m'}
=\langle a^X_{\ell m}a^{Y*}_{\ell' m'}\rangle.
\]

The observer layer must therefore support both modes:

1. compressed isotropic summaries \(C_\ell\), useful for sanity checks;
2. full or sparse anisotropic covariance, useful for beyond-FLRW morphology.

A deterministic background contribution is represented as

\[
a^X_{\ell m}=a^{X,\rm rand}_{\ell m}+A t^X_{\ell m}(\lambda,R),
\]

where \(A\) is amplitude, \(\lambda\) are shape parameters, and \(R\in SO(3)\) is sky orientation.

---

# 3. Low-\(\ell\) statistics

## 3.1 Power at fixed multipole

\[
\widehat C_\ell^{TT}
=\frac1{2\ell+1}\sum_m |a^T_{\ell m}|^2.
\]

The quadrupole and octopole amplitudes are

\[
Q_2=\widehat C_2^{TT},\qquad Q_3=\widehat C_3^{TT}.
\]

## 3.2 Large-angle correlation statistic

Define

\[
C(\theta)=\sum_{\ell=2}^{L}
\frac{2\ell+1}{4\pi}\widehat C_\ell^{TT}P_\ell(\cos\theta).
\]

Then

\[
S_{1/2}=\int_{-1}^{1/2}[C(\theta)]^2d(\cos\theta).
\]

This statistic is sensitive to the chosen multipole range, mask treatment, monopole/dipole subtraction, and whether deterministic template components have been subtracted.

## 3.3 Angular-momentum dispersion axis

For each \(\ell\), define the axis maximizing

\[
D_\ell(\hat q)=
\sum_m m^2 |a_{\ell m}(\hat q)|^2.
\]

Here \(a_{\ell m}(\hat q)\) are coefficients after rotating the \(z\)-axis to \(\hat q\). The maximizing axis is

\[
\hat q_\ell=\arg\max_{\hat q}D_\ell(\hat q).
\]

Quadrupole-octopole alignment can then be summarized by

\[
A_{23}=|\hat q_2\cdot\hat q_3|.
\]

## 3.4 Planarity

A simple planarity score is

\[
P_\ell=
\frac{\max_m |a_{\ell m}|^2}{\sum_m |a_{\ell m}|^2}
\]

after rotating to the preferred axis. The exact definition used in code must be stored because multiple planarity conventions exist.

## 3.5 Parity asymmetry

Define even/odd powers over a chosen low-\(\ell\) range:

\[
P_+ = \sum_{\ell\in\mathcal L_+} w_\ell \widehat C_\ell,
\qquad
P_- = \sum_{\ell\in\mathcal L_-} w_\ell \widehat C_\ell.
\]

A parity statistic can be

\[
R_{\rm parity}=\frac{P_+}{P_-}
\]

or

\[
A_{\rm parity}=\frac{P_+-P_-}{P_++P_-}.
\]

The weights \(w_\ell\) and multipole range are part of the statistic definition, not post-processing details.

## 3.6 Hemispherical modulation

A phenomenological modulation model is

\[
T(\hat n)=[1+A_M(\hat p\cdot\hat n)]T_{\rm iso}(\hat n).
\]

Fit parameters:

\[
A_M,\qquad \hat p.
\]

This statistic is useful as a morphology diagnostic even when the solver backend is not literally a dipole-modulation model.

---

# 4. Template fitting

For a deterministic anisotropic template,

\[
\mathbf a_{\rm obs}
=\mathbf a_{\rm rand}+A\mathbf t_R(\lambda),
\]

where \(R\) rotates the template. Given a covariance \(\mathsf C\), the quadratic objective is

\[
\chi^2(A,R,\lambda)
=
(\mathbf a_{\rm obs}-A\mathbf t_R)^\dagger
\mathsf C^{-1}
(\mathbf a_{\rm obs}-A\mathbf t_R).
\]

For fixed \(R,\lambda\), the best-fit amplitude is

\[
\hat A
=
\frac{\mathbf t_R^\dagger \mathsf C^{-1}\mathbf a_{\rm obs}}
{\mathbf t_R^\dagger \mathsf C^{-1}\mathbf t_R}.
\]

Improvement statistic:

\[
\Delta\chi^2
=\chi^2(A=0)-\chi^2(\hat A,R,\lambda).
\]

The observer layer must record whether the scan searched over amplitude only, orientation only, shape only, or all of them.

---

# 5. Null ensembles and exploration bookkeeping

The observer layer must support at least three ensemble types:

1. isotropic Gaussian FLRW-like skies;
2. deterministic-template injections;
3. anisotropic covariance simulations.

For a statistic \(S\), the empirical tail probability is

\[
p=\frac{1+N(S_i\ge S_{\rm obs})}{1+N_{\rm sim}}
\]

for an upper-tail statistic. The inequality is reversed for lower-tail statistics.

For exploratory scans over many statistics, multipole cuts, orientations, or templates, the code must store the full scan volume. It does not need to suppress beyond-FLRW exploration; it simply has to make the exploration reproducible.

---

# 6. Interface contract with the solver core

The observer/statistics layer may assume only the following from the solver:

```python
@dataclass
class SolverCoreOutput:
    alm_T: complex array | None
    alm_E: complex array | None
    alm_B: complex array | None
    map_T: array | None
    map_Q: array | None
    map_U: array | None
    deterministic_template: dict | None
    anisotropic_covariance: sparse matrix | None
    metadata: dict
```

Required metadata:

- Bianchi type and algebra convention;
- tetrad-to-sky orientation convention;
- harmonic basis convention;
- \(E/B\) sign convention;
- multipole cutoff;
- whether output is deterministic, stochastic, or mixed;
- whether tilt was enabled;
- whether Thomson scattering was exact, approximate, or disabled.

---

# 7. Boundary rule

This document may define what is measured on the sky and how exploratory statistics are computed. It must not decide whether a Bianchi model is physically preferred. That interpretation belongs to a separate scientific analysis note.

The solver-core document remains responsible for the equations. This document remains responsible for observer-facing summaries.
