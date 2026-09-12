# R8 full execution: scientific results and remaining limits

Owner: HTT / obsstat / restricted BASS benchmark. Scope: internal, non-claim-bearing research synthesis.
Design: PR #467; implementation branch `implementation/tensor-joint-r8-20260909`.

All **24 nodes and 52 action handlers** have terminal results. There are no unimplemented handlers.
This completes the requested implementation/execution pass. **Full scientific acceptance is not achieved**:
independent CAS obligations, observed sampling/response laws and the held mixture diagnostic remain as specified.
No merge or canonical scientific promotion is included.

## What the executed data show

- **Orbit bounds:** 30 saved pools were continued without deleting rows or changing targets, scales, seeds or alpha. 7,186 pair upper bounds improved. 5 pools are conservative non-rejections; 25 remain unresolved; 0 reject. These are computed synthetic statistics, without a qualified observed CMB pool. Exact pair trees, row banks and cumulative accounting are saved for resumption. Old checkpoints lacked trees; their enclosure banks and work counts were retained, and only newly visited pairs started trees. The 60-second cooperative checkpoints completed their last indivisible operation after the deadline: observed refinement times 60.000–61.904 s. These overruns are disclosed; this is not a hard real-time guarantee. Whole-scope caps remain unexhausted.
- **Representation:** 44/45 mock tensors reconstruct; the coincident-vector refusal retains its tensor row. All four observed component tensors reconstruct. Full-tensor/full-MV enclosures overlap after reconstruction error transport; lossy summaries offer no demonstrated representation information gain.
- **DESI released Gaussian summary:** the unchanged standalone conditional 95% qiso interval is **[0.9462387032, 1.0195221801]**. The integrated run separately uses alpha=1/80 for this component. CMB, CF4 and distance-calibration allocations remain unused whole domains; no budget is reassigned.
- **Union3:** official release documentation resolves the 23x23 layout into 22 redshift/modulus nodes and their precision matrix. The original UNITY1.5 compression gives **Omega_m=0.3559244**, profile chi-square **23.9580098**, with a free common distance-modulus offset in flat LCDM. This is a released approximate Gaussian scenario, not an exact finite-sample acceptance or an anisotropic R3 likelihood. The matrix's tiny antisymmetric part drops out of the quadratic identically; its symmetric part is positive definite. No posterior samples were treated as independent observed draws.
- **CF4 / JWST / raw DESI:** actual release tables, source members and FITS metadata were inspected. Missing selected sampling/covariance/response premises prevent stronger laws. Published error bars alone do not fill them. The earlier 38,053-position flow controls and four PR3 component controls are preserved as descriptive evidence.
- **Conditional physical image:** 204 finite and 34 unrestricted support queries remain valid within their stated fixture domains. Missing observed radiation/derivative laws leave the empirical physical region unrestricted. No empirical x_C, F or G_F bound is fabricated.
- **Restricted R3:** all 54 histories and 432 forward/reverse-ray pairs were executed. 36 histories at tolerances 1e-8 / 1e-10 pass; 18 coarse histories fail the unchanged convergence/residual criteria. All 432 optical tests pass their criterion, but only 288 rays associated with passing histories are eligible as numerical benchmark outputs. Wrong rapidity and pi-scale controls are detected. The normal thermal sky has even parity and zero coherent odd multipoles. Fixed benchmark predictions have no attached observed likelihood. The radiation derivative jet is explicitly unavailable.
- **Mixture simulator:** the frozen mu=-1 cell has 64/1000 rejections and upper bound 0.0911411 above 0.085. The adapter stays held. Analytic iid continuous-rank size is 0.05; a finite diagnostic fluctuation is possible, but does not override the held result. Seeds and criteria were not changed.

## Methods and interpretation

SO(3) orbit distances use q0=o0=1e-5 K and k=ceil(sqrt(M-1)). Optimizers provide only feasible upper witnesses, which are recomputed with exact rational quaternion rotations. Lower bounds retain exact root isolation and outward arithmetic. Bounds, not optimized point distances, enter ranks; inclusive ties and unresolved states remain conservative.

R3 follows the coupled LRS Bianchi-I two-antipodal-dust-stream + initially isotropic collisionless Planck-photon + Lambda model in `R3_MODEL_REFERENCE.md` N1–N29. Units are c=H_i=1, 8piG/(3c^2)=1. The fixed six kappa/zeta cases run from a=1 to a=2 at three quadrature orders and three tolerances. An independent observer boost and positive-stream source frame are retained. Full four-vector screens and Jacobi matrices propagate with the actual stress history; reverse rays are numerically integrated. Evidence is limited to the fixed, weak-anisotropy benchmark endpoints, not arbitrary parameters or a global caustic theorem.

The three selected review87 members match their declared hashes. Their Bose moments and screen basis were actually exercised as donor comparisons. No license file is declared in that supplied archive; the new wrapper does not vendor it or assert a redistribution license. The existing dust and physical anisotropic-stress conventions are retained.

The [Union3 release README](https://github.com/rubind/union3_release/blob/f5c387349b68f3535fdabf0fbc4f45cd407f9084/README.md) specifies the compression; [Rubin et al., arXiv:2311.12098](https://arxiv.org/abs/2311.12098) describes UNITY. The [Bianchi-I optics reference](https://arxiv.org/abs/1410.8473) supplies the Sachs/Jacobi context. These sources do not validate this implementation by citation alone.

## Deliverables and reproducibility

- [Eight-page scientific figure report](R8_scientific_synthesis.pdf), [figure source bindings](figure_manifest.json).
- [Executed campaign](campaign/summary.json), [dry plan](dry_plan.json).
- [Targeted test log](tests.log), [direct review and limitations](REVIEW.md).
- [Orbit continuation](../orbit_continuation/summary.json), [R3 grid and optics](../restricted_history/results.json), [product intake](../law_followup/products.json), [mixture diagnosis](../law_followup/mixture_diagnosis.json).

Run commands are recorded in `EXECUTION.md`. Initial failures, old incomplete results and original input files are retained. Tests and numerical checks are separate from independent four-axis CAS acceptance and scientific admission. There is no native Bianchi family identification, empirical CMB rank, MIO posterior or truth certificate in these outputs.
