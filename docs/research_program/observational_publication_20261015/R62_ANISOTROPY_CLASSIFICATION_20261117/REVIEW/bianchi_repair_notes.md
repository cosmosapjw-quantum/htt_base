# R62 R5/C5 bounded physics repair return

Base: c118982e56ee50d68dd0446aa10f16ffe65bd02b. Owner: `/root/r62_bianchi_constraints`. Parent selected design: `/workspace/scratch/d9b8ed2ee1cd/R62_DESIGN.md`, section C. No remote production mutation was performed. Full proposed source copies and tests are under `r62_bianchi_proposed/`; the parent is the sole repository writer.

## Deliverables

- `r62_bianchi_repair.patch`: unified patch with repository-relative paths; SHA-256 `7167032c7d77df82d4cd45ca02388bcc7050e2aceb8bfd9a00461611e717d72b`.
- `r62_bianchi_repair_manifest.json`: baseline and proposed hashes for all four files.
- `r62_bianchi_constraints_r3.md`: exact operator/rank/source/units contract and original counterexample receipt (SHA-256 `d6b975f1bc1328111039e3697998bbf942f08cd32f9c2390c7e442254d0977d6`).

The three original source copies were compared against remote SHA-256 results and match byte-for-byte: tilted_bianchi_state.py `cff836456026ce89cf61da44400510c8c3724e8ea57c6de7a567e13905b15717`; convention_bridge.py `037f53787f42edcbc047e2871df9f21f4d66219955fff7f570315c9ed52e7c0c`; bianchi_similarity.py `c221bd5d9c2242d8ec1724fa0e88805f60ed5377c06d9cc303fd3b1d5a5fdb64`.

## Changed behavior

1. `momentum_constraint_map(algebra)` constructs the actual 3x5 STF divergence matrix, SVD singular values, numerical rank, range projector and consistent truncated pseudoinverse. Its rank threshold is `rtol*max(smax,||a||,||n||)`. Including the structure scale avoids interpreting rotated isotropic-n roundoff as rank three, and preserves nonzero uniform-scale invariance. The absolute effective threshold is returned for interpretation near a rank boundary.
2. The constructor checks the requested family against the existing algebra classifier, with the existing flat `FLRW -> I` convention. It evaluates the actual total momentum's range and projects shear with the same pseudoinverse. Rank-zero and rank-two restrictions remain enforced; the canonical IX representative no longer vetoes anisotropic IX. Canonical registry values, field names, old test expectations and historical receipts remain intact. Text now states the representative scope.
3. The active R49 `D sigma + kappa q=0` convention is documented in the adjacent helper and constructor. The known opposite-sign implementation in legacy `constraints.py:122` is not edited; downstream legacy paths need separate explicit treatment. This return does not certify that legacy implementation.
4. The moment Jacobian uses `2*[beta,nhat beta,nhat^2 beta]^T` at the actual beta. `moment_rank` and its condition number retain their squared-component-map meanings. `stabilizer_orbit_dimension` is a named read-only alias for the existing serialized `continuous_azimuth_degeneracy_dof`; old stored schemas remain readable. The latter is documented as gauge freedom in the simultaneous SO(3) quotient, rather than different orbit classes.

## Scope of the new regressions

The test file covers the exact positive-dust IX counterexample; existing I/flat-FLRW/isotropic-IX rejection in both modes; repeated-eigenvalue IX range and STF kernel preservation; exceptional VI_{-1/9}; nonzero structure scaling; SO(3) covariance and isotropic/repeated numerical strata; the untilted Type-V kernel example and violated-kernel rejection; the same-shear Class-A family construction; family/algebra mismatch; zero, axis, planar, and generic velocity Jacobians; occupied repeated eigenspaces; and a stabilizer rotation preserving the orbit moments.

These are conditional initial-slice and diagnostic checks. Source-positive dust was constructed explicitly. No native transfer, full cosmological evolution, family identification from apparent shear, or statistical confidence is asserted.

## Actual validation status and parent execution

Observed before this implementation: the exact-base public constraint evaluator accepted the nonisotropic IX example with Gauss residual 8.88e-16 and Codazzi residual 2.78e-17 while its constructor rejected it. The zero-tilt Jacobian field incorrectly reported rank three. Details are in the R3 note.

Observed after scratch implementation: Python AST parsed all four proposed Python files; a local four-case Jacobian prototype (zero, one, two, three occupied distinct axes) matched ranks 0,1,2,3. These are construction checks, not the affected-suite pass. Integration tests, source acceptance, and independent review remain parent-owned C6/C7/C8 work. No pytest suite was run by this child at this stage.

Suggested affected suite after parent application, in the authorized checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -m pytest -p no:cacheprovider -q tests/r62/test_bianchi_state_constraints.py tests/r49/test_gbi01_convention_bridge.py tests/r49/test_gbi02_tilted_state_and_constraints.py htt/bass/diagnostics/test_bianchi_similarity.py
```

SSOT trace: `docs/SSOT_POLICY.md` section 16 lists Bianchi tilt conventions as a future centralized entry; section 17.3 distinguishes geometric tetrad shear from synchronous-gauge scalar shear, and section 17.7 requires Bianchi-specific scope. The implementation reuses the existing BASS exact divergence and common orthonormal STF basis; it defines no duplicate physical constants or new broad SSOT registry. Required repo physics-math-audit and scientific-code-validation skills were read. No CAS four-axis or scientific publication pass is claimed. Parent-reported Wolfram exact algebra is complementary evidence to be attached by its owner, not a child-observed execution receipt.

Next action: parent applies the patch only against the pinned original file hashes, executes the affected suite, resolves any concrete failures in this one bounded repair episode, and incorporates the exact R3 construction into its conditional Bianchi interpretation. No additional review layer or full historical rerun is requested.
