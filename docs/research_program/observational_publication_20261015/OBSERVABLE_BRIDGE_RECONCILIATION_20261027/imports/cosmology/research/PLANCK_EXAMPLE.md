# Pinned Planck PR3 E-mode morphology example

26 October 2026 · local-source verification plus a fresh ideal Gaussian benchmark. No map acquisition, repository refresh, processed-Planck null simulation or solver run. Source S1 is `PUBLICATION_ACCELERATION_20261025/evidence/baseline/output/HTT_research_compact_en.md` in the retained repository snapshot at `a55036ad09c53a9215dee3282e425d37cfb95443`. Its source note attributes the retained 29-page calculation to `10f3ea585c6608e794900efe7e4f8f42c0747a3b`. S1 §§4.1–4.2 and Appendix B contain the actual example.

## Verified carrier and numbers

“P” is **pinned-primary source**, and “C” is **cached-pilot source**; these are source labels, not names for two statistical methods. The chirality coordinate is separately denoted \(\mathcal C\). The requested rounded values match **P / cutoff 32 / secondary window 0° / FULL**:

| Quantity | Source value | Meaning |
|---|---:|---|
| \(r=j^2/t^3\) | 0.0582918 | Quadrupole shape; \(t=\operatorname{tr}Q^2\), \(j=\operatorname{tr}Q^3\) |
| \(\mathcal C\) | −0.0967707 | Signed, globally normalized quadrupole–octupole pseudoscalar |
| \(E(r)\) | 0.808141 | Fixed-quadrupole envelope divided by global envelope; not polarization E amplitude |
| \(U\) | 0.1197448 | Absolute utilization of the sharp fixed-quadrupole envelope |

S1 Appendix A gives \(E(r)^2=(1-6r)(1+3r/40)\), with \(0\le r\le1/6\). Thus \(U=|\mathcal C|/E(r)\); recomputing with the displayed rounded inputs gives approximately 0.8081411 and 0.1197448. This checks displayed-number consistency, not the original pseudoalm extraction. The cached-pilot **C / 32 / 0° / FULL** row is different: \(\mathcal C=-0.0967544\), \(r=0.0582656\), \(U=0.1197103\). The primary zero-window numbers repeat at cutoffs 64 and 128 because the retained low-order tensors coincide at stored precision. Here “32” is a processing cutoff, while the tensors being analysed are degrees two and three.

The input is a masked delivered QU polarization product, with **processed E pseudo-\(a_{\ell m}\)**. S1 specifies Galactic, Condon–Shortley real coordinates \((a_{\ell0},\sqrt2\Re a_{\ell m},-\sqrt2\Im a_{\ell m})\). Symmetry and trace freedom complete the STF arrays before contraction. This verifies an E-mode morphology carrier, not a temperature/intensity carrier.

## What “all stable at \(\rho=10^{-6}\)” means

Let \(\bar Q=Q/q_0\), \(\bar O=O/o_0\), with S1's exact computational scales \(q_0=o_0=10^{-5}\,\mathrm K_{\rm CMB}\). Use the **joint full-tensor Frobenius norm**
\[
 m^2=\|\bar Q\|_F^2+\|\bar O\|_F^2,\qquad
 \sqrt{\|\delta\bar Q\|_F^2+\|\delta\bar O\|_F^2}\le\rho m.
\]
This is a ball in \(\mathrm{STF}_2\oplus\mathrm{STF}_3\), not the unweighted Euclidean norm of twelve selected tensor entries, a sky-pixel error ball, or a measured calibration uncertainty. Full contractions include repeated entries with their multiplicities.

S1 §4.2, **equation (13)**, gives the sufficient certificate
\[
 \chi^2>36\rho^2(1+\rho)^{16}(m^2)^9,
 \qquad\chi=\det[v,\bar Qv,\bar Q^2v],\quad v=\bar O:\bar Q.
\]
The derivative bound is \(|D\chi[h]|\le6m^8\|h\|\). The source reports passing counts **60, 60, 39, 0, 0, 0** at relative radii **0, \(10^{-6}\), \(10^{-5}\), \(10^{-4}\), \(10^{-3}\), 0.05**, respectively. “All” means all **60 saved carriers**, each retaining its own sign throughout its specified perturbation ball. They comprise 15 primary product/cutoff combinations and 45 cached-pilot processing variations from **one observed sky**. Their signs are 15 positive and 45 negative; “all stable” does not mean all have the same sign or that processing cannot change a sign. Primary HM1, for example, has \(\mathcal C=+0.00876054\), unlike primary FULL. Failure of this sufficient certificate does not prove a reversal.

**Equation-number correction:** the accessible R32-01 science manuscript's **equation (35)** is an optical acceleration–shear/logarithmic-remainder determinant bound at fixed known shear. It is not the above joint Planck-carrier ball certificate. A historical equation (35) in an earlier report may be intended, but that numbering has not been verified from its original local document. Cite the formula and S1 §4.2/(13), rather than merging these two results.

## Historical \(U\)-CDF provenance: unverified

The historical **\(U\) CDF ≈63.1%** and its original null simulation sample size, seed, conditioning and processing support were **not found** in the retained local S1, associated source texts or available JSON records searched here. Their provenance therefore remains unresolved. A new independently specified benchmark, below, supports a percentile near that number without reconstructing the historical run.

S1 does contain a **different** reference comparison: a 4,096-draw pilot fixes a family-statistic transformation, then each of two constructed laws has **16,383 evaluation draws**. The shared-spatial-rotation and shared-Gram-preserving-orthogonal laws give add-one upper-tail ranks 0.4581298828125 and 0.45513916015625. Those are dependent-view family-statistic results, **not the CDF of this FULL-row \(U\)**. They cannot be substituted for 63.1%. Establishing the latter requires the original \(U\)-null result and its declared sampling law. A percentile under such a law would still be distinct from a calibrated cosmological anomaly probability.

### Newly derived ideal Gaussian benchmark

A separate analytic benchmark follows from the exact fixed-\(Q\) envelope. Fix a nonzero simple-spectrum quadrupole and an octupole of norm \(o>0\). Let \(C_Q:O\mapsto O:Q\), with singular vectors chosen so that \(v_i=s_i o z_i\) in a positively oriented quadrupole eigenbasis. Complete its three right singular vectors by four orthonormal kernel vectors. The normalized octupole has coordinates \(z\in S^6\). With \(V(\lambda)=\det[1,\lambda_i,\lambda_i^2]\),
\[
 |\chi|=|V(\lambda)|o^3s_1s_2s_3|z_1z_2z_3|,
 \quad\chi_{\max}=\frac{|V(\lambda)|o^3s_1s_2s_3}{3\sqrt3}.
\]
The second equality uses \(\max_{\sum z_i^2\le1}|z_1z_2z_3|=1/(3\sqrt3)\), attained at equal squared image coordinates with zero kernel. Therefore
\[
 U=3\sqrt3|z_1z_2z_3|.
\]
If the seven Frobenius-orthonormal octupole coefficients are independent equal-variance zero-mean Gaussians conditional on \(Q\), then \(z\) is uniform on \(S^6\). Thus \((z_1^2,z_2^2,z_3^2,\sum_{4}^{7}z_i^2)\) has Dirichlet parameters \((1/2,1/2,1/2,2)\), giving a **quadrupole-shape-independent ideal law** for \(U\). Its exact checks are
\[
 \mathbb E U=\frac{15\sqrt3}{64\pi},\qquad
 \mathbb E U^2=\frac3{77}.
\]
More generally, \(\mathbb E U^s=(3\sqrt3)^s\Gamma(7/2)\Gamma((1+s)/2)^3/[\Gamma(7/2+3s/2)\Gamma(1/2)^3]\) for \(s>-1\). This is a new derivation in the present verification, not a recovered historical simulation receipt. A numerical CDF evaluated under it must be labelled a new ideal benchmark. It does not model the masked Planck pseudoalm covariance or foreground/processing distribution. Random spatial rotations of one fixed octupole also do not generate the full uniform-\(S^6\) law.

The parent executed that benchmark in `cas/planck_hubble_controls.py`, with seed **20261026** and **\(N=2^{20}=1,048,576\)** independent normalized seven-dimensional Gaussian draws. At the displayed primary threshold **\(U=0.1197448\)**, **662,397** draws are at or below it:
\[
 \widehat F_U=0.6317110062,\qquad
 95\%\text{ binomial MC interval }[0.6307869539,0.6326343308].
\]
The empirical upper-tail fraction is 0.3682889938. The sample mean is 0.1291676618 versus exact 0.1292177099; the sample second moment is 0.0389441641 versus exact 0.0389610390. The actual source and result bytes were inspected here; results are in `cas/planck_hubble_results.json`. This newly executed **63.17% ideal-reference CDF** is compatible with the approximate 63.1% value. Its interval measures Monte Carlo sampling error under the declared mathematical law, not uncertainty in Planck processing or cosmological confidence. The historical receipt remains unverified, and the new ideal benchmark is not relabelled as a processed-Planck null.

## Scalar E, parity and physical interpretation

For a full-sky scalar E convention, \(E(n)=\sum a^E_{\ell m}Y_{\ell m}(n)\) is parity even: under inversion \(a^E_{\ell m}\mapsto(-1)^\ell a^E_{\ell m}\). Accordingly its quadrupole is even and octupole odd. The contraction determinant \(\mathcal C\) is invariant under proper rotations and changes sign under reflection; \(U\) discards that sign. A nonzero realized \(\mathcal C\) describes parity-odd morphology of that carrier. Statistical parity violation requires a calibrated ensemble test; nonzero values alone do not establish it. Masked pseudo-E additionally retains the actual E/B mixing and processing response.

Polarization E is not positive absolute thermodynamic temperature or Stokes intensity I. In particular, **\(I=C_\gamma E(n)^4\) is not a physical conversion**. The intensity-weighted kinetic stress \(\pi_{ab}=\int I(e)e_{\langle a}e_{b\rangle}d\Omega\) requires an intensity/spectral observation map, including polarization conventions when needed. These E-mode tensors, their chirality utilization and their deterministic sign certificate therefore constrain the stated polarization morphology. They do not themselves supply radiation anisotropic stress, congruence shear, vorticity or a Bianchi-family measurement.
