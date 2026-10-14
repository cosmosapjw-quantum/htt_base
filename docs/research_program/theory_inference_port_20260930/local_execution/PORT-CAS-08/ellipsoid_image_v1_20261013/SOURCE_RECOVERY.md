# P08-B source recovery (PORT-CAS-08, ellipsoid quotient image)

Repository HEAD at recovery: `00e547daffbf2c8e2f444c5651203f3a32e99d74`
(branch `proof/cas15-ls-matrix-synthesis-20261008`). Recovery is read-only.

## Contract and port map

| Item | Location | sha256 |
|---|---|---|
| CAS-08 obligation | `docs/research_program/theory_inference_port_20260930/CAS_CONTRACT.json:99-108` | `904d95fe49402e9589f48bf4dcfdf69e4680a069693545580e4892e83c389fad` |
| PORT_MAP F4 | `docs/research_program/theory_inference_port_20260930/PORT_MAP.json:31-44` | `d0050aa349b56946d39bf2751e4f4687029c98e17203ed1740ab797ad44ce5e0` |
| Card | `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip:HTT_ALL_OBLIGATIONS_20261011/tasks/P08-B.json` | (zip member, not hashed separately) |

CAS-08 identity (verbatim): `z0=(B L)^+ (y-Bc); eta=||z0||^2; residual image factor=sqrt(1-eta)*P L N`;
assumptions: `compatible support; interior eta<1; exact algebra separate from numeric rank rule`.

PORT_MAP F4 APIs: `common.typefree_fibers.ellipsoid_quotient_gauge`,
`common.typefree_fibers.ellipsoid_fiber_image`,
`common.typefree_fibers.rational_polytope_fiber_support`; status
`IMPLEMENTED_CONDITIONAL_SUPPLIED_INPUT`; limit: "Ellipsoid EMPTY_SET is a floating
numerical conclusion, not a formal empirical exclusion certificate". SOURCE_TO_REPO.json has no
F4-specific row (only the `typefree_loop2_20260928` theory directory, line 476).

## Owning Python

File `htt/src/common/typefree_fibers.py`, sha256
`6f5f9a01b862a72ea0b4a034d3e10bc97276bc372a84f7e3b509d40b43947910`, last commit
`bc45fb9292a4cfb095d7b61d4e5c02a32fb39c5c`, clean in the working tree.

| Symbol | Meaning | file:line |
|---|---|---|
| ellipsoid `K` | `K = c + U^(1/2) * closed unit ball` | `typefree_fibers.py:137` (docstring) |
| `L` | `factor` from `_psd_factor(shape)`: eigenvectors of the PSD shape `U` with positive eigenvalues, scaled by `sqrt(lambda)`; an `n x r` matrix with `L L^T = U` | `typefree_fibers.py:18-31`, used at `:138` |
| `B` | `observation` (observation operator, `m x n`) | `typefree_fibers.py:140` |
| `P` | `projection` ("target operator", `q x n`, maps the ambient state to the target/physical parameters) | `typefree_fibers.py:141` |
| `c` | `center` (ellipsoid centre, default 0) | `typefree_fibers.py:145` |
| `y` | `observed_value` | `typefree_fibers.py:144` |
| `z0` | `_solve_range(B@factor, y-B@c)` returns `z = V_r Sigma_r^{-1} U_r^T b`, the SVD pseudoinverse solution `(B L)^+ (y - B c)` | `typefree_fibers.py:34-56` (line 48), call at `:148` |
| `N` | `kernel = right[rank:].T`: trailing right-singular vectors of `B L`, i.e. an orthonormal basis of `ker(B L)` (`N^T N = I`, range `N` = `ker(B L)`) | `typefree_fibers.py:43,56`; identity when `B L` has no rows / is zero, `:38,42` |
| `eta` | `float(z@z)` | `typefree_fibers.py:153` |
| boundary branches | `radius_sq = 1-eta`; floating `EMPTY_SET` if `< -error`, `BOUNDARY_NUMERICALLY_UNRESOLVED` if `abs <= error` | `typefree_fibers.py:154-163` |
| lift centre / factor | `lift_center = c + L z0`; `lift_factor = sqrt(1-eta) L N` | `typefree_fibers.py:164-165` |
| image centre / factor | `target_center = P lift_center`; `target_factor = P lift_factor = sqrt(1-eta) P L N` | `typefree_fibers.py:166,170` |
| support function | `h(u) = u.target_center + ||target_factor^T u||`, witness `lift_center + lift_factor (F^T u/||F^T u||)` | `typefree_fibers.py:126-133` |
| quotient gauge | `ellipsoid_quotient_gauge`: minimum gauge over `p x = value` is `||(p L)^+ value||`, `radius_sq = z.z` | `typefree_fibers.py:72-91` |
| incompatible support | `OUTSIDE_RESPONSE_RANGE -> EMPTY_SET` | `typefree_fibers.py:149-150` |

## Formal translation used in T

* `A := B * L`, `b := y - B *ᵥ c`, `X` any matrix with the four Penrose conditions
  `G08AWhitening.IsMoorePenrose A X` (exact, no SVD, no cutoff), `z0 := X *ᵥ b`,
  `η := z0 ⬝ᵥ z0`.
* Original bounded ellipsoid `K := {x | ∃ z, z ⬝ᵥ z ≤ 1 ∧ x = c + L *ᵥ z}` (closed unit ball of
  the latent space `Fin r → ℝ`, Euclidean dot product). This is the docstring set at line 137
  with `U^(1/2)` replaced by an arbitrary real `n x r` factor `L` (covers `factor` of
  `_psd_factor`, any rank).
* Fibre image `P '' (K ∩ {x | B *ᵥ x = y})`.
* `N : Matrix (Fin r) (Fin d) ℝ` with `Nᵀ * N = 1` and `∀ k, A *ᵥ k = 0 ↔ ∃ u, k = N *ᵥ u`
  (orthonormal parametrisation of `ker A`), mirroring `right[rank:].T`.
* The numeric tolerances at lines 22, 44, 51-52, 158 (floating rank rule, residual bound,
  boundary band) are deliberately NOT modelled: the Lean statements are exact-algebra, as the
  CAS-08 assumption "exact algebra separate from numeric rank rule" requires. No claim is made
  that the floating code computes these objects to any accuracy (`numerical SVD link` not
  claimed).
