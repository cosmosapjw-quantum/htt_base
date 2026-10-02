# CAS-01 Lean axis proof map

This independent Lean/mathlib axis is bound to `EXECUTION_CONTRACT.json` SHA-256
`edc2df3348528a699b987ae1893ab76630e96b9915d11117db7916d005c406f1`
and `COMMON_SPEC.md` SHA-256
`4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`.
`Main.lean` uses `Fin 4 → ℝ` vectors, covariant `Fin 4 → Fin 4 → ℝ` forms,
`eps = (-1,1,1,1)`, and derivative-first `Q_ab`. `g`, `eval`, `cov`,
`contractL`, and `flat` retain the indicated index variance. The proof contains
no `sorry`, `admit`, or new target axiom. The exact executed source hashes,
Lean version, argv, cwd, exit, and full stdout/stderr are in `AXIS_RESULT.json`
and the raw `*.stdout`, `*.stderr`, `*.exit` files.

| Component | Exact compiled statements | Semantic alignment |
|---|---|---|
| CAS-01-C01 | `B_unit`, `B_shift`, `B_symmetric`, `null_cone_kernel` | Generic real symmetric source `S`, unit timelike `u`; `B(u,u)=0` and invariance under `S+a g`. The symmetric null-cone kernel is eliminated from the universal sourceward sphere hypothesis using six axial and six rational mixed sphere points. |
| CAS-01-C02 | `C02_from_symmetric_source`, `Q_right_null`, `Q_symmetric_part`, `Q_left_acceleration`, `projected_eq_D`, `sigma_spatial`, `sigma_tracefree` | Generic future-unit `u`, symmetric `S`, spatial skew `W`, `c>0`. The wrapper derives the `B(u,u)=0` premise from C01. `Q u=0`, `sym Q=B`, and `c Q^T u=2c B u`; the mixed projector `δ_a^b+u_a u^b` gives `D=hBh`, `theta=tr_g B`, and spatial STF `sigma=D-theta h/3`. |
| CAS-01-C03 | `C03_B_rest`, `rest_H_decomposition`, `traceg_rest`, `cov_rest`, `general_sourceward_harmonics` | `rest=(1,0,0,0)`, `K=(-1,n)`, `|n|²=1`, `A_i=2c B_i0`, `theta=B_11+B_22+B_33`; the exact sourceward sign is `-A_i n_i/c`. The separately constructed general symmetric `S` has `S_00=h0`, `S_0i=-h1_i/2`, and STF spatial `h2`, yielding `h0+h1·n+h2:nn`. |
| CAS-01-C04 | `C04_from_symmetric_source`, `fullNormalized_origin`, `fullNormalized_coordinate_derivative` | `fullSeed_b(x)=u_b^raised+Σ_a x^a eps_b Q_ab/c` realizes `v^b=u^b+c^-1 g^{bd}Q_ad x^a`. `fullNormalized` uses the positive `Real.sqrt(-g(v,v))`. For every coordinate index `a,b`, `HasDerivAt` along `x=t e_a` at `t=0` has value `eps_b Q_ab/c`; the value at zero is `u`. The proof differentiates the normalization and uses `Q u=0`; it does not assume the derivative formula. |

The `#print axioms` output for every required target is parsed by `run.py`.
Only Lean/mathlib's `propext`, `Classical.choice`, and `Quot.sound` occur. A
component boolean becomes true only after exit zero, frozen identity/hash
checks, presence of every required theorem's axiom printout, and absence of
other axioms. `check-axis` validates the stored envelope, separately from the
executed compiler evidence.

Analytic Jacobi vertex Taylor order and screen invariance remain **OPEN**.
Smooth timelike neighborhood, local flow, and source extension remain **OPEN**.
The finite/local component result does not establish the larger optical
theorem or scientific admission. `compiler_failure.*` preserves an intermediate
compiler failure during this construction; its source hash at that failure was
not recorded, and the final `lean.*` files identify the executed final source.
