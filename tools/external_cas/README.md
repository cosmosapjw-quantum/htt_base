# WU-011 external CAS / numerical-algebra verification axis

This directory is an isolated audit axis for PMG-WU-011 Task-7C.  It was
branched from `e826f15da13dc8ebd86fc29fc03d4e92b4dcfe53` and is deliberately
separate from Draft PR #444's production branch.

## Fixed physical and numerical contract

- metric signature: `(-,+,+,+)`;
- outward sky direction: `n_hat=-e`;
- active observer boost: `+beta`, with `beta=v/c`;
- thermodynamic-temperature Doppler weight: `d=1`;
- first-order response at `beta=0`;
- wide axisymmetric mask
  `w(mu)=0` below `-3/4`, `1/2+2 mu/3` on `(-3/4,3/4)`, and `1` above `3/4`;
- weighted joint fit over `ell=0..5`, retaining `ell=2..5`;
- high-source band `ell=7..L`;
- identity transfer.

The output carrier has dimension 32.  A full-row-rank high-source response
therefore supplies a continuum deterministic-nuisance surjectivity candidate,
not an empirical velocity fit or a physical Bianchi attribution.

## Independent axes

### Java Algebra System (JAS)

`WU011JASExact.java` uses JAS `BigRational` arithmetic and exact polynomial
integration.  It works in unnormalised associated-Legendre blocks.  The omitted
spherical-harmonic normalisations are nonzero diagonal row/column scalings and
therefore do not alter rank.

The registered exact z-axis expectations are

```text
L=8  stored-real rank 20
L=9  stored-real rank 27
L=12 stored-real rank 32
```

At `L=12`, every retained `|m|=0..5` block must have a nonzero full-row pivot
minor.  The program emits the exact rational minors.

### GNU Octave

`wu011_octave_verify.m` performs direct piecewise Gauss-Legendre and Fourier
quadrature.  It builds spherical harmonics and angular derivatives pointwise,
applies the first-order boost generator for all six registered directions,
solves the weighted joint fit, and computes the continuum singular spectrum.
It does not read a Python/Wolfram/SciPy response matrix.

### Julia

`wu011_julia_verify.jl` independently implements the same direct continuum
quadrature using only Julia standard libraries.  It has a separate
associated-Legendre recurrence, harmonic builder, joint solve, and SVD.

Both numerical axes must return rank 32 at `L=12` and reproduce the frozen
smallest singular values within their registered numerical tolerance:

```text
X/Y:       0.010490334912761
Z:         0.006905664979696537
diagonals: 0.008510322776380
```

## Claim boundary

A successful workflow establishes an additional implementation-independent
cross-check of the continuum wide-mask operator.  It does **not** by itself
certify the finite HEALPix operator, complete the matrix-valued numerical-error
envelope, admit Planck data, fit `beta`, identify global tilt, attribute a
Bianchi family, or authorize merge/release.

Failures are preserved.  The three jobs are separate so that one unavailable
runtime or package does not hide the status of the other axes.
