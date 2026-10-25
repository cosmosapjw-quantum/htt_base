# Bounded quadrupole–octupole comparator

Date: 2026-10-25. Exactly three Exa search queries were used, followed by reading primary-paper pages. This closes the requested bounded comparison, not mathematical novelty. Existing `PUBLICATION_STRATEGY.md` remains unchanged.

The precise candidate is for real Euclidean STF tensors Q∈STF₂ and O∈STF₃, Frobenius norms, v=O:Q and chi=det[v,Qv,Q²v]:

The inverse-matrix image formula below assumes Q ≠ 0 and o ≥ 0. At Q = 0, the contraction image is {0} and chi = 0; the inverse is not used.

\[
\{O:Q:\|O\|_F=o\}=\{v:v^TM_Q^{-1}v\le o^2\},\quad
M_Q=\tfrac13\operatorname{tr}(Q^2)I+\tfrac25Q^2,
\]

\[
\max_{\|O\|=o}|\chi|
=\frac{|\prod_{i<j}(\lambda_j-\lambda_i)|\sqrt{\det M_Q}}{3\sqrt3}o^3,
\qquad
|\chi|\le\frac{4\sqrt2}{135}\|Q\|_F^6\|O\|_F^3.
\]

Thus the target includes an exact contraction image, fixed-Q optimum, global attained constant, and equality cases. The polynomial has bidegree (6,3) in (Q,O); a generic multipole pseudoscalar is not automatically this theorem.

## Relevant primary comparisons

**Desmorat et al., *Minimal Functional Bases for Elasticity Tensor Symmetry Classes*, [arXiv:2105.14930](https://ar5iv.labs.arxiv.org/html/2105.14930), Section 4, Remark 4.1.** The full author text gives the established third-order covariant a×a² and

\[
J_2^3-6J_3^2=12\|a\times a^2\|^2,
\quad J_2=\operatorname{tr}(a'^2),\quad J_3=\operatorname{tr}(a'^3).
\]

This is a close formula-level comparator: it packages precisely the discriminant/axis-degeneracy structure used in the retained proof. For trace-free Q, the manuscript Vandermonde identity V²=t³/2−3j² equals half that discriminant. Consequently, discriminant-based spectrum classification and generalized tensor cross products must be treated as established. The inspected section supplies neither the map O↦O:Q nor its fixed-norm ellipsoid/attained chirality constant. Derive the proportionality between the determinant and contraction of the conventional Q×Q² with v⊗³ using that paper's cross-product normalization before asserting a new invariant.

**Olive and Auffray, *Isotropic invariants of a completely symmetric third-order tensor*, J. Math. Phys. 55 (2014), [DOI:10.1063/1.4895466](https://doi.org/10.1063/1.4895466).** The primary abstract constructs an integrity basis through harmonic tensors and binary-form invariant theory. This establishes a substantial mathematical literature beyond CMB morphology. Its object is one completely symmetric rank-three tensor, whose harmonic decomposition contains rank three and rank one, rather than an independent STF₂⊕STF₃ pair. Only abstract/bibliographic content was obtained, so no claim about the absence of a formula in its full proof is justified. Its reference to Smith–Bao, *Isotropic invariants of traceless symmetric tensors of orders three and four* (1997), DOI 10.1016/S0020-7225(97)00048-7, is a specific follow-up; the direct fetch timed out and that paper is not treated as inspected evidence.

**Pisanty et al., *Chiral moments make chiral measures*, [arXiv:2603.26793v1](https://arxiv.org/html/2603.26793v1), Sections II–V and Appendices A, B, F.** This recent primary preprint constructs rotational pseudoscalars from tensor moments and generalized cross/triple products, including traceless moments, explicit polynomial kernels, and higher-degree constructions for two-multipole distributions. It therefore defeats any broad claim that tensor-moment chirality or a two-multipole pseudoscalar is unprecedented. Its displayed chi₂₂₃ examples use distinct/radially weighted quadrupoles and are trilinear in their arguments; its Appendix F uses octupole/hexadecapole covariants. These are not the displayed bidegree-(6,3) expression. The inspected formulas do not present the target contraction ellipsoid or constant 4√2/135. General families may nevertheless contain an algebraically related invariant, so degree/normalization and generator-reduction comparison remains necessary.

## Decision

The bounded search found **no exact sharp-bound match in the inspected material**. This is scoped retrieval evidence, not a novelty proof or a literature-wide absence statement. Keep the prospective contribution phrased as an explicit attained inequality with constructive equality cases and its same-frame optical realization; credit established covariants, discriminants and multipole pseudoscalars. Before a first-result claim, compare the exact bidegree-(6,3) polynomial against an STF₂⊕STF₃ integrity basis and check whether the optimization is already a known corollary. That focused comparison is the remaining novelty obligation; it does not prevent drafting or verifying the existing scientific result.
