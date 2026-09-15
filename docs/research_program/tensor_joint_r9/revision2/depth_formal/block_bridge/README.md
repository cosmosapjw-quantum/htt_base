# D3 deterministic block-matrix bridge

Owner: common/HTT research; revision 2; transfer source none; diagnostic-only
formalization. Base e71b3375789460b6abf5c72bbc52b95801fa894d is a descendant of
user base bc5e028d16c10a8a60080a59f5cd6adaf7595238. This formalizes the existing
D3 result, not a new theorem. The original `CAS_D3.json` version 1 and its hash
remain unchanged; `STATUS.json` binds the source and executed evidence.

## Assumptions and exact obligations

Use ordered finite blocks R^(d_j), arbitrary natural d_j, finite depth n>=0,
and fixed real rectangular K_j of size d_(j+1) by d_j. Zero-size blocks are also
allowed by the code, which is stronger than the original positive-size domain.
No K_j is assumed invertible, square, orthogonal or stochastic. Compatible
feature units are retained; no physical frame, velocity or shear is inferred.

| Original D3 obligation | Formal source declarations | Evidence and ceiling |
|---|---|---|
| Actual T=(Y0,HY) in full block coordinates | Ix, coupling, transform, contrastMatrix; transform_step, contrast_one, contrast_recursion | General compiled matrix/residual identities. |
| Both inverse directions | Previous Recursion.lean pathEquiv; current transform_bijective via both nonsingular matrix inverse identities | Previous typed result preserved; current matrix map independently compiled by Host, not an independent reviewer. |
| det T=1, arbitrary block sizes | determinant_one | Induction over finite depth using lower block-triangular determinant. |
| H is onto; ker H is precisely homogeneous propagation | contrast_surjective, transform_propagated, kernel_iff_propagated | General compiled statements, without a full-rank assumption on any K. |
| Depth 0 | zero_depth_contrasts; determinant_one at n=0 | Empty residual space is a singleton; its zero-row H is onto and all initial states lie in its kernel. |
| Full transformed law, support, mean and covariance | Existing D1 generic moment formulas plus D3 deterministic map | Joint measurable/topological bridge is still not formalized. No complete D3 or FORMAL_DEPTH admission. |

## Proof, not a finite matrix experiment

`Ix d s n` is the ordered nested sum of the coordinate indices of every block,
starting at s. At each level the matrix is

    T_(s,n+1) = [[I, 0], [J(-K_s), T_(s+1,n)]],

where J injects into only the first block of the remaining coordinates. Thus
its determinant is det(I) det(T_tail)=1 by induction, including depth zero.
`contrast_one` and `contrast_recursion` prove that deleting the initial rows
produces exactly all Y_(j+1)-K_j Y_j. These equalities guard against confusing
the recursively nested coordinates with a different triangular operator.

A unit determinant gives both matrix inverse compositions and hence bijectivity.
Any desired contrast vector z is obtained by applying the inverse to (0,z),
proving H surjective. Define propagation recursively by a, K_s a, K_(s+1)K_s a,
etc. Its T-image is exactly (a,0): all negative transport terms cancel the next
propagated block. If H y=0, retaining y0 gives T y=(y0,0); injectivity then gives
y=propagated(y0). Conversely the propagated trajectory has zero contrasts.
No target identity is assumed as an axiom.

The full-law continuation is mathematically separate: in finite dimensions T
and its inverse are continuous linear maps. For any Borel measure mu,
(T_inverse)_*(T_*mu)=mu, and supp(T_*mu)=T(supp mu). For finite second moments
the already proved D1 formulas apply to the entire T, including initial/residual
cross blocks. These are the next formal obligations, not currently compiled
probability theorems in this file. Singular measures need no artificial jitter.
D2 additionally needs the Gaussian affine support and pseudoinverse chi-square
law; D4 needs conditioning on the entire past and its singular-law branches.

## Execution and preserved failures

Use the existing mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f built for
repo-pinned Lean v4.31.0. No package or dependency manifest was changed.

```text
python3 docs/research_program/tensor_joint_r9/revision2/depth_formal/block_bridge/compile.py <fresh-directory-under-this-evidence-directory>
```

`attempt01` preserves the missing Real import error; autoImplicit=false prevented
an accidental abstract replacement. `attempt02` exposed a reducibility issue
between nested index types and typeclass instances. `attempt03` records the
related tactic goals; making the coordinate alias reducible and explicitly
reducing function applications fixed these. `attempt04` records a now-redundant
rfl and a first-row rewrite requiring explicit indices. `attempt05` compiled the
core bridge; `attempt06` additionally compiled the exact all-depth residual
recursion. Both successful sources contain no sorry/admit/target axioms; final
printed dependencies are propext, Classical.choice and Quot.sound only.
Failed compiler elaboration generated sorryAx internally; its nonzero exits and
raw transcripts are retained and never used as accepted evidence.

No old DESI, SDSS, CF3, fixed-ambient or moving-q experiment was replayed.
Independent CAS authors' old scripts do not import this new source. Their
sixteen actual D1-D4 engine executions and raw CAS_FAIL remain unchanged;
no new four-axis run or acceptance is asserted. Existing current child
registrations have null bindings, and the exact prior hook failure is retained.
No renamed child, new registration or policy bypass was used.

## Prior moving-q result and source statuses

The unchanged MQ1/MQ2 research note at 9ca515ad gives, with A=3 sqrt(2/5),
`d_H <= 2 A epsilon + sqrt(2 A) sqrt(epsilon)` for two nonempty fibres, and
`d_H <= A[2+sqrt((1-delta)/delta)] epsilon` when both eta<=1-delta.
Its source table links T5 WU010 at af5d79ad, contraction-fibre S54 at d5a5444b
and fixed-q support/boundary S55 at c09fa9f1, retaining original directly-derived,
noncanonical statuses. MQ1/MQ2 retain their scoped independent research review;
no uncertain-q CAS, novelty or observational acceptance is added here.

The same ambient full Frobenius convention, eta<1/eta=1/eta>1 branches,
nonconvex fibre distinction, raw-Q amplitude lower bound and Q=0 branch remain
unchanged. Full selected observation law, physical response and common
state-jet-anchor coverage stay UNAVAILABLE. All HOLD/quarantine/STOP_INVALID,
unresolved outcomes and alpha allocations remain unchanged.
