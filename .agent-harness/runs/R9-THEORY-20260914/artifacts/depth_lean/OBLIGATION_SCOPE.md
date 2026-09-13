# Lean depth-obligation scope

`DepthCore.lean` compiles under the pinned core-Lean project. It assumes both
explicit legitimate algebraic premises used by the recursion:
`a + b - b = a` and `a - b + b = a`. It proves both compositions for finite
homogeneous trajectories, residual surjectivity, and reconstruction
equivalence. It also proves both compositions for finite time-dependent
transports over a homogeneous state type. The source defines typed dependent
block paths, residual blocks, and their time-dependent reconstruction and
extraction maps, and proves the residual-after-reconstruction composition for
those arbitrary finite dependent blocks. The reverse dependent-block
composition was attempted but does not compile; its raw diagnostic is retained.
It contains no `sorry`, `admit`, target axiom, or unsafe replacement.

This does not discharge D1: the only PSD-related helper is an abstract
Int-valued pullback-positivity implication; there is no real matrix,
covariance, expectation, cross-block, or general-dimensional PSD theorem.
It does not discharge D3: the required two-sided arbitrary-block result is
incomplete, and rectangular real matrices, block-triangular determinant, and
full singular joint-law/support preservation are absent. It does not discharge D2
or D4: an actual `import Mathlib` probe fails with unknown module prefix
`Mathlib`; no finite-dimensional Gaussian, image support, Moore--Penrose
inverse, spectral whitening, chi-square, conditional Gaussian, Schur
complement, or independence formalization is available in this project.

The runner emits `false` for every contract obligation and a nonempty
`domain_assumption_diff` for each proposition. Successful compilation is
evidence only for the stated helper lemmas and definitions. It is not a PASS
for any D1--D4 contract or for the complete Gaussian depth law.
