# Report A R3A — fresh source referee and contract audit

Date: `2026-09-04`  
Repository: `cosmosapjw-quantum/htt_base`  
Audited report source: `docs/research_reports/HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md`  
Audited manuscript blob: `be5e8459b51741eaac87e659c63524902ae4d40b`

## Verdict

```text
PASS_R3A_SCIENTIFIC_AND_STATISTICAL_SOURCE_REVIEW
/
SUPPORTED_RUNTIME_CONTRACT_NOT_EXECUTED
/
PDF_TYPESETTING_AND_VISUAL_AUDIT_PENDING
/
NO_PUBLICATION_OR_MERGE_AUTHORITY
```

The flattened R3 manuscript has a coherent theory/methods spine and preserves the evidence boundaries established by the R2 and R3 audits. No new P0 or P1 defect was found in the scientific or statistical source text. The report is not yet frozen because the focused Python contracts did not execute on a supported exact-head runner, no rendered PDF has been built and inspected, and the explicit release decision remains separate.

## 1. Scope and supersession

The report remains HTT-only. It does not restore scalar-only MES ranks or the withdrawn WU-006–008 tensor-rank, foreground, and carrier-injection interpretations. It contains no corrected tensorized Planck result, no empirical observer velocity, no boost subtraction, no global matter-frame tilt identification, no physical shear/vorticity estimate, no foreground cause, no Bianchi-family attribution, no finite-HEALPix no-go theorem, and no BASS/native-solver result.

The observational gate is explicit:

```text
CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE
CURRENT_OBSERVATIONAL_RESULT = NONE
PLANCK_OR_FFP10_EXECUTION = DEFERRED_BY_OWNER
```

## 2. Representation and orbit geometry

The stored-real carrier and STF norm identities are stated consistently:

\[
\|c_\ell\|^2=(2\ell+1)C_\ell,
\]

\[
Q:Q=\frac{75}{8\pi}C_2,
\qquad
O:O=\frac{245}{8\pi}C_3.
\]

The report distinguishes the nine-dimensional generic quotient of
`STF2(Q) direct-sum STF3(O)` from the fourteen-dimensional quotient of the unrelated `STF2 + four vectors` representation. It limits the Krylov theorem to the nonzero cyclic forward-image domain and records the normalized packet-image relation

\[
\bar O:\bar Q=\mathscr K_{QO}e_0,
\qquad
O:Q=A_QA_O\mathscr K_{QO}e_0.
\]

The signed-volume chirality claim is limited to the registered mirror pair and named compression. It is not extended to every conceivable bispectrum, a global invariant ring, or an all-strata orbit atlas.

The current SciSpace search again found adjacent tensor-invariant, orbit-space, and multipole-representation methods but no direct primary-source statement matching the exact `v=O:Q`, `K=[v,Qv,Q^2v]` reconstruction theorem. The manuscript therefore correctly retains `NOVELTY_UNRESOLVED` rather than treating search absence as proof of novelty.

## 3. Conditional MES functionals

The report uses the corrected PSTF normalization

\[
\epsilon_2=\frac1{T_0}\sqrt{\frac{75C_2}{8\pi}},
\qquad
\epsilon_3=\frac1{T_0}\sqrt{\frac{245C_3}{8\pi}},
\]

and keeps the shear/vorticity functions one-way and premise-conditioned. The residual dipole `epsilon_1` is an attribution scenario, not a measured intrinsic dipole. The scalar-to-tensor equivariance obstruction is stated without promoting the scalar functions into tensor observations or physical source estimates.

## 4. Finite-sample statistics

The R3L/R3F source now separates two different theorems.

1. `RA-STAT-001` uses joint exchangeability of the observation/reference rows and equivariance of the complete row analysis.
2. `RA-STAT-004` uses a declared null-invariant finite transformation group and ranks over the actual transformation orbit, or a valid identity-including conditional-Monte-Carlo transformation sample.

The proper-subgroup counterexample is correct:

\[
z^{(1)}=(10,0,-100,-100),
\qquad
z^{(2)}=(0,10,-100,-100),
\]

with probability `1/2` each. Ranking against all four coordinates yields p-values `1/4` and `1/2`, so

\[
\Pr(p_{\rm all}\le1/2)=1,
\]

whereas the actual two-element group orbit gives p-values `1/2` and `1` and is super-uniform. This supports the manuscript statement that subgroup invariance does not authorize arbitrary out-of-orbit reference rows.

The adaptive-selection fixture counts 24 permutations, not 24 independent rows. Its deterministic tie rules give the stated `12/12` and `6/18` splits and size excess `1/4`. Null fidelity, row-equivariant chart handling, deterministic ties, and dependence between shared evidence products remain explicit.

The current randomization-inference literature supports this distinction between exchangeable-row permutation ranks and tests over a null-invariant transformation orbit. It does not validate the project-specific reference pool automatically.

## 5. Local-observer and processed response

The photon-energy notation is now `E_gamma`, avoiding collision with the MES multipole amplitudes `epsilon_l`. The metric, sky-direction, and active-boost conventions are consistent:

\[
g_{ab}=(-,+,+,+),
\qquad n^a=-e^a,
\qquad \widetilde u^a=\gamma(u^a+\beta^a).
\]

The full-sky local-observer response, STF quadrupole-to-octupole map, Gram matrix, and condition bound remain within the accepted WU-010 scope. Local observer motion is not equated with global tilt.

The processed operator order is explicit. The report distinguishes the exact physical-monopole null, finite transform leakage, the low-source Jacobian, the high-source nuisance image, and the quotient-rank identity. It preserves the registered negative Task-7B result and the last finite-operator Task-7C result as `RANK_UNRESOLVED`, without replacing it by the continuum calculation.

## 6. Continuum and numerical-error boundary

The continuum wide-mask rank ladder and the `L=12` smallest singular values are reported with separate evidence grades: exact axial rational evidence and multi-engine high-precision numerical evidence in the five non-axial directions. The report explicitly states that continuum full row rank does not certify finite-HEALPix full row rank.

The numerical-error envelope

\[
\Gamma_E=N_{\rm fam}\sum_f r_f^2\sum_iE_{fi}E_{fi}^{T}
+\lambda_{\rm reg}^2I
\]

is presented as a conditional theorem for a frozen complete error-family class. The report does not assert that the current finite-HEALPix registry is complete. It also distinguishes robust rank from stable partial singular-subspace orientation and retains the perturbation-to-gap requirement.

## 7. Claim, citation, and bibliography authority

The flattened report contains a 30-row claim map including the distinct `RA-STAT-004` group-orbit theorem. The formal BibTeX file is named as the sole rendered bibliography authority, and the manual reference list has been removed. The report points to the 30-row citation matrix and the separate authority/execution provenance appendix.

All seventeen registered citation keys are used in the scientific source. Adjacent invariant-theory papers are not described as direct proofs of the Q/O Krylov theorem. Continuum and finite-HEALPix claims receive different labels.

## 8. Execution boundary

The focused workflow at commit `6ae924a98905c795de963ac57a371831fcb7074e` and one explicit retry both ended before runner assignment:

```text
workflow run: 33814103150
initial job:  100842264353
retry job:    100842443764
runner_id:    0
steps:        []
```

Therefore checkout, Python setup, dependency installation, YAML parsing, and pytest did not execute. This is `PRESTART_NO_EXECUTION`, not a passing or failing manuscript contract.

Fresh Wolfram evaluation of the subgroup receipt again returned upstream HTTP 502 in this pass and is not counted as a new Wolfram verification. The exact arithmetic statement remains supported by the prior Fraction receipt and direct derivation.

## 9. Remaining publication gates

### Required

1. Run the v3 ledger, citation-matrix, and flattened-manuscript contracts in a supported Python 3.12 environment.
2. Compute and bind the canonical sorted-ID SHA-256 from that execution.
3. Build a typeset PDF using the formal BibTeX authority.
4. Inspect equations, tables, line breaks, and bibliography rendering visually.
5. Freeze source, bibliography, PDF, ledger, provenance, and audit hashes.
6. Obtain the explicit owner publication/merge decision.

### Desirable but not Report-A prerequisites

- exact-head execution of PR #450 and PR #451;
- portable interval certification of all non-axial continuum ranks;
- completion of the finite-HEALPix numerical-error family and robust-rank programme.

These desirable upgrades must remain visible as unresolved evidence boundaries; they are not silently converted into completed claims.

## Final classification

```text
scientific_source: PASS
statistical_source: PASS
scope_and_claim_firewall: PASS
citation_and_provenance_structure: PASS
supported_runtime_contract: BLOCKED_BY_PRESTART_NO_EXECUTION
fresh_wolfram_replay: BLOCKED_BY_UPSTREAM_502
pdf_and_visual_audit: NOT_STARTED
publication_authority: NOT_GRANTED
```
