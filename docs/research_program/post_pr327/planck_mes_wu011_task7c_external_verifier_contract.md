# PMG-WU-011 Task-7C external-verifier contract

Date: 2026-09-03
Owner: OBSSTAT / PHYS-MATH / PHYS-MATH-CODE
Parent PR: #444
Parent head at branch creation: `e826f15da13dc8ebd86fc29fc03d4e92b4dcfe53`
Claim tier: diagnostic and proof-support only
Scientific terminal authorized: no
Merge authorized: no

## Purpose

Strengthen the continuum wide-mask response calculation with independently
downloaded numerical and proof-oriented packages. This node does not replace
the repository's HEALPix operator, fit an observer velocity, choose a physical
high-multipole prior, or promote the current continuum surjectivity candidate.

## Fixed conventions

```text
metric signature: (-,+,+,+)
outward sky direction: n = -e
active observer boost: +beta
beta = v/c
Doppler weight: d = 1
linearization: beta -> 0
fit band: ell = 0..5
retained band: ell = 2..5
high-source band: ell = 7..L
wide mask: 0 below mu=-3/4, 1/2+2 mu/3 for |mu|<3/4, 1 above mu=3/4
```

Source and retained harmonic coefficients have temperature dimension. The
linear response, Wigner coefficients, scientific stored-real metrics, and rank
certificates are dimensionless.

## Downloaded verifier axes

### V1 — WIGXJPF

Pin `pywigxjpf==1.13.3`. Verify its source-distribution SHA-256

```text
30122c9ab2775aa8a0531d01956892627f1c6e82ba65c3abf6b8fc4fb75c3aef
```

and compare registered integer Wigner 3j values against SymPy exact values.

### V2 — DUCC

Pin `ducc0==0.41.0`. Compare `ducc0.misc.wigner3j_int` with WIGXJPF and
SymPy, and use DUCC Gauss-Legendre nodes and weights in an independent direct
quadrature of the wide-mask continuum operator.

### V3 — SymPy exact algebra

Pin `sympy==1.14.0`. Construct the axisymmetric z-direction weighted normal
matrix and high-source response from exact rational polynomial integrals. At
`L=12`, exhibit one nonzero square minor for every `|m|=0..5` retained block.
This proves the complex block ranks `(4,4,4,3,2,1)` and the real-sky stored
rank `4+2(4+4+3+2+1)=32` for the z-direction continuum operator.

### V4 — python-flint / Arb

Pin `python-flint==0.9.0`. Convert the exact algebraic pivot minors to Arb
balls and require every determinant ball to exclude zero. This is a rigorous
ball-arithmetic check of the selected minors, not a proof of the physical
validity of the mask or response model.

### V5 — mpmath and SciPy

Pin `mpmath==1.4.1`, `scipy==1.18.1`, and `numpy==2.5.2`. Recompute the
z-direction blocks with high-precision quadrature and compare the smallest
singular values with the Wolfram reference. mpmath is an independent
arbitrary-precision numerical axis, not directed-rounding proof arithmetic.

## Required outputs

```text
package_download_sha256.txt
package_versions.json
wigner_crosscheck.json
sympy_exact_block_ranks.json
arb_pivot_minor_certificate.json
ducc_quadrature_crosscheck.json
external_verifier_summary.json
SHA256SUMS
```

## Acceptance

- all pinned packages download and import;
- WIGXJPF, DUCC, and SymPy agree on every registered Wigner 3j symbol within
  the declared double-precision envelope;
- SymPy exact algebra finds z-direction `L=12` real-sky rank 32;
- all selected Arb determinant balls exclude zero;
- DUCC/SciPy quadrature reproduces the z-direction Wolfram smallest singular
  value `0.00690566497969653698...` within a preregistered relative tolerance;
- artifacts are deterministic, manifest-bound, and preserve package hashes.

Any package installation failure, hash mismatch, exact-rank disagreement,
ball containing zero, or quadrature disagreement is a typed failed verifier
axis. Other axes may still be reported, but no aggregate PASS is allowed.

## Claim boundary

A PASS supports an independent z-direction continuum full-row-rank witness at
`L=12`. It does not by itself certify the other boost directions, the HEALPix
continuum bridge, a matrix-valued numerical-error envelope, an empirical beta,
a global matter tilt, a Bianchi family, or a scientific containment terminal.
