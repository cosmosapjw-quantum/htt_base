# PR-176 primary-source record: tilted-frame divergence response

- Accessed: 2026-07-20 UTC
- Primary source: C. G. Tsagas, M. I. Kadiltzoglou, and K. Asvesta,
  *The deceleration parameter in `tilted' Friedmann universes: Newtonian vs
  relativistic treatment*, arXiv:2105.09267v2.
- Abstract page: https://arxiv.org/abs/2105.09267
- Versioned source archive: https://arxiv.org/e-print/2105.09267v2
- Downloaded source-archive SHA-256:
  `5f169d4f377b8c96db288d9c1c2fbc80659c69383bcc005de66d2edaef77b0bf`
- Extracted `paper.tex` SHA-256:
  `6000430718e560e7bfbc847a81c3fbf47098d906033b64000ca38416db483791`

## Equation authority used by PR-176

The source defines the peculiar expansion scalar as the spatial divergence
of the peculiar velocity.  Its Eq. `Rlhqs1` gives the relativistic
tilted-frame deceleration response before the scale-dominant reduction.  In
the nearly-flat limit it contains a signed term proportional to
`(theta/H)` and a scale-dependent term proportional to
`(lambda_H/lambda)^2 (theta/H)`.  Its Eq. `Rlhqs2` gives the further
Einstein-de Sitter, scale-dominant form with coefficient `1/9`.

The paper defines `lambda` as a physical mode wavelength.  PR-176 therefore
registers `lambda=2R` when a catalogue ball is specified by its physical
radius `R`.  This diameter convention is a sensitivity convention, not an
inference that the finite catalogue window is one harmonic mode.

## Scope firewall

PR-176 does not import a bulk-flow amplitude as a divergence measurement and
does not substitute the legacy ad-hoc closure
`theta/H = beta * lambda_H/d`.  It measures a raw-catalogue affine trace
coefficient first.  The two signed mappings corresponding to `Rlhqs1` and
`Rlhqs2` require separately authenticated response bridges and a matched
cross-channel covariance before they can support a q-channel falsifier.
Neither bridge is set to unity or inferred from this paper alone.

This record authenticates formulas and conventions only.  It does not
validate the physical applicability of the perturbative tilted-FLRW model to
CF4, establish apparent acceleration, or identify a cosmology, geometry,
Bianchi family, or transfer function.
