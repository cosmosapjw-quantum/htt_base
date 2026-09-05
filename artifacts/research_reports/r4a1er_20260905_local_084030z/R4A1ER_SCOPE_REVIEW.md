# R4A1ER — local R2 receipt and manuscript scope review

**Verdict: R4A1ER_REVIEWED_R2_PASS_SUPPORTING_LEMMAS_ONLY.**

The submitted local run is accepted as the existing R2 supporting-domain CAS evidence component. Its four lemmas transfer to the specified parts of revision 2 under the same stated assumptions. This review makes no whole-manuscript, empirical, canonical, scientific-publication or merge decision.

The reviewer did not perform the local R4A1E execution. This is a separate source/evidence review, **not blind**: the reviewer saw the submitted verdict and receipts and had prior K2FR context. The two axis programs share their disclosed preparation session; distinct engines do not make their source authorship independent.

## Receipt and execution evidence

- Actual uploaded ZIP: R4A1E_LOCAL_EXISTING_R2_20260905T084030Z.zip, SHA-256 **04f61775c35af3d4894742c32efb7d40780188d91323556dd5fff56095267332**. DELIVERY.sha256 also correctly binds the separately supplied result YAML. Safe extraction and CRC passed; all 61 internal checksums cover the 62-member archive except SHA256SUMS itself.
- Execution source: **581d50cb8b8be61ca8ead538d0bf7d75420f9037**, tree **435de757e124410c6f59bd56e709c4af18c8d3ad**. All 18 complete source payloads fetched through GitHub match the archived before/after manifests. All 16 contract-registered bindings match their actual bytes.
- Contract: CAS-R4A1NF-DOMAIN-R2, version 2, SHA-256 **9e7520e23021430e581a1b27eb5af52c6f3eba6a6fdd4c21614b60249778ffa4**. The source-binding and parent-adjudication receipts use this same hash.
- Original binding receipt SHA-256: **98b4dea32a8c0cb9986f18b6ce298fecef01f057a68feeb7abd97fc1d3a33510**.
- Original adjudication receipt SHA-256: **c2a10f7097db8e2c83e706ba9ee598f3acd03829d54faa704c8544835554cc06**.

| Recorded axis | Version | Actual execution record |
| --- | --- | --- |
| SymPy | CPython 3.12.3; SymPy 1.14.0; mpmath 1.3.0 | parent-launched child; exit 0; no timeout; four checks true |
| Lean | 4.31.0, compiler 68218e876d2a38b1985b8590fff244a83c321783 | parent-launched wrapper and theorem elaboration; exit 0; no timeout; four checks true |
| mathlib | fabf563a7c95a166b8d7b6efca11c8b4dc9d911f | actual dependency checkout recorded at pin; all nine Lake dependencies match their declared commits |

The parent and PATH-resolved child Python records identify the same CPython environment; no worktree-local venv masks the probe. Lean wrapper constants are corroborated by native version output and actual dependency records, rather than accepted as version measurements alone.

The original source-binding receipt precedes the parent run. The parent command is run-adjudicate, not stored-result adjudicate. SymPy ran at 08:45:31–08:45:32 UTC and Lean at 08:45:32–08:45:36 UTC on 2026-09-05, within unchanged 600/3600-second limits. Both payloads contain exactly the four registered obligation names, empty domain_assumption_diff and null counterexample. The raw aggregate is PASS, with no missing axis, applied exception or error. The SymPy 80-digit residual is a supplemental numerical cancellation check; exact symbolic identities and the ordered positivity implication carry the registered result.

The pinned runner launches actual subprocesses and derives status from their exits and complete parsed stdout payloads. The pinned Lean wrapper runs the theorem source with warningAsError and emits success only after successful elaboration; its source rejects sorry, native_decide and added source axioms. No fresh CAS process was launched by this review.

Parent redirected stdout/stderr/exit files are complete. Child evidence is limited to the original parent payloads and the last 2000 characters of stdout/stderr, plus bounded probe tails. No separate full child transcript exists. Matching existing mathlib caches were reused; four representative fingerprints are recorded. This is not a fresh full mathlib build, exhaustive cache validation or remote security attestation.

The 18 before/after source records and source checks agree. Existing-checkout head, status and tracked-diff records are unchanged. This verifies the returned records against pinned GitHub source; it does not pretend that this reviewer accessed the user's workstation or hashed every installed package/data file.

## Precise transfer to revision 2

The R2 contract still binds the older R3 manuscript blob **16f8fdd4db4dac384c5c64a8d3f86e0dbbf62e34**, the convention registry, domain appendix and T8. Revision-2 manuscript blob **99a3f75c67ece3cfb00179bfd61787f47cb7e7ac** is a separate reviewed consumer, not a substituted contract input.

### 1. photon_null_decomposition → Section 2.1

With signature \((-,+,+,+)\), \(u\cdot u=-1\), \(u\cdot e=0\), \(e\cdot e=1\), and \(p^a=(E_\gamma/c)(u^a+e^a)\),

\[
p\cdot p=(E_\gamma/c)^2(-1+2\cdot0+1)=0.
\]

The manuscript uses these same assumptions and retains \(c>0\), positive measured energy and future orientation. Lean checks the real scalar contraction after substitution. Neither its source nor this receipt formalizes a Lorentzian manifold, global observer existence or null-geodesic dynamics.

### 2. observer_measured_photon_energy → Section 2.1

\[
-c\,p\cdot u=-E_\gamma(u\cdot u+e\cdot u)=E_\gamma.
\]

The scalar contraction matches the manuscript's energy definition without changing the sky convention \(n=-e\). The factors retain momentum units for \(p\) and energy units for \(E_\gamma\). The dimensional cancellation and geometric instantiation are explicit source reasoning; the Lean theorem itself is the scalar identity \(-((-1)+0)-1=0\).

### 3. boosted_observer_unit_timelike → normalization in Section 8.1

For \(u\cdot\beta_{\rm obs}=0\), \(0\le\beta_{\rm obs}^2<1\), positive \(\gamma=(1-\beta_{\rm obs}^2)^{-1/2}\), and \(\widetilde u=\gamma(u+\beta_{\rm obs})\),

\[
\widetilde u\cdot\widetilde u
=\gamma^2(-1+\beta_{\rm obs}^2)=-1.
\]

The Lean premise gamma2*(1-beta2)=1 is instantiated by the manuscript's Lorentz factor. The admissible use is this normalization only. It does not verify the d=1 temperature pullback, aberration generator, global matter-frame tilt or physical kinematical response. In particular, Section 8.2's \(B_Q^*B_Q=3M_Q\), adjoint, inverse and conditioning bound are not among the four obligations.

### 4. regularized_error_envelope_positive_definite → regularization in Section 11.1

In the registered real coordinate metric, set

\[
P=N_{\rm fam}\sum_f r_f^2\sum_iE_{fi}E_{fi}^{T}\succeq0,
\qquad \Gamma_E=P+\lambda_{\rm reg}^2 I,
\qquad \lambda_{\rm reg}>0.
\]

Each compatible \(E_{fi}E_{fi}^{T}\) is PSD and the finite family coefficients are nonnegative. Hence, for nonzero \(x\),

\[
x^T\Gamma_E x=x^TPx+\lambda_{\rm reg}^2\|x\|^2>0.
\]

This is the exact generic Matrix.PosDef theorem elaborated by Lean. SymPy supplies a generic 2-by-2 Gram identity and the dimension-independent ordered scalar implication. The manuscript-to-generic-P substitution is source-level reasoning. The finite-dimensional inverse square root follows from positive definiteness; its existence is not a separately exported Lean theorem in this module.

All envelope terms retain squared response units and the coordinate metric remains material. This PASS does not check the family-wise Loewner bound, compensated scaling, zero-family implementation, holdout coverage, robust rank or actual finite-HEALPix error membership. Section 11.1's prior phrase “not presented as a newly kernel-checked proof” remains untouched; this separate receipt supplies only the limited generic regularization evidence.

## Still-applicable original obligations

| Original obligation | Current disposition |
| --- | --- |
| R2 source binding, both required axes and paired receipts | Discharged for this local R2 evidence component by the reviewed original records |
| T9 v4 supported-runtime authority/cross-surface replay and canonical sorted-ID hash binding | Separate obligation remains open; the R2 run does not execute it |
| PR450 exact registered-survivor replay and independent review | Open: head ba84912bea165896ec8f0c0e5793b47d1736f512; dedicated job 100677692359 has runner_id=0, steps=[] |
| PR451 exact packet-image/conditioned-decoder execution and independent review | Open: head 9f7d06dec0fce1c3a8a53fa5372c84d9c679c037; dedicated job 100686355554 has runner_id=0, steps=[] |
| R4A1V0 immutable third-party Action pins before publication freeze | Still listed and applicable: the formal workflow retains version tags |
| PR444 A4 byte-exact implementation/registry-provenance seal | Remains relevant to implementation acceptance; current PR retains source-equivalent evidence and a prestart execution boundary |
| Actual finite-HEALPix error-class completeness and partial-subspace projector control | Unresolved; generic PosDef does not close these scientific admission premises |
| K5 typesetting | Already delivered; no rebuild or repetition is indicated |
| Remaining source/authority reconciliation, final referee and owner acceptance | Separate downstream decision; no automatic closure or promotion |

A concrete authority mismatch remains: **R4A1_SUPPORTED_RUNTIME_AUTHORITY_CONTRACT_V3.yaml** still expects citation blob **3fbaa2f97522cca6d0ad60e0c96655d293ca0d74**, while the already repaired source contains **5087d39edf094f3adf7d72eed3061521ecf0b78d**. This older authority contract is distinct from the correctly bound CAS-R4A1NF-DOMAIN-R2. The discussion thread must explicitly reconcile the authority contract with the authorized repair before selecting its existing replay. This review does not repin, bypass or execute the old authority contract.

Fresh PR450/451 reads retain their exact original heads and their dedicated jobs have no executed steps. Their prior source-equivalent results retain their original evidence grades. PR444's current source/evidence boundary is also retained; no new finite-operator requirement is imposed on the successful R2 component.

The original K2FR bundle, five structural findings and separate scope annex remain immutable. This R2 record addresses neither the Q/O reconstruction nor finite-null validity, full physical response, forty-claim validation, finite-HEALPix containment or observations. Optional R3 axes do not become required for this fixed R2 contract merely because they are available.

Recommendation: accept the local R2 receipt as the four supporting-domain evidence component with the limited transfers above; return the named remaining-authority questions to the discussion thread. Canonical remains T9 v4/30; candidate remains 40. Scientific publication and merge authority remain false.

## Evidence publication boundary

Only exact new local receipts, relevant execution text and this bounded review may be added under the new run's noncanonical evidence prefix. The child branch starts from 581d50cb8b8be61ca8ead538d0bf7d75420f9037 and targets review/htt-k2fr-returned-repair-20260905-r1. Existing PR449/452 source and original evidence are not edited. Final commit/tree/PR and complete payload readback are returned in the separate publication receipt.
