# MES_GENERALIZED_TENSOR_R2 — read first

Start with MES_GENERALIZED_TENSOR_R2_KO.md (integrated Korean report), then INDEPENDENT_DECISION.md/.json for final admitted scope. This is a completed theoretical research loop, not actual all-kinematics CMB inference.

## Mathematical content

- agent_kinematics.md: exact local optical inverse for all 12 proper-time rate components, L2 stability, all-kinematic weak transport, finite boost/global tilt, generic Lie algebra.
- agent_statistics.md: rank-graded tensor normalization, projected feasible bodies, likelihood and tensor Q/F/Pi/G reductions.
- sources_agent/MES_BOUND_SOURCE_REVIEW.md: narrowly authorized MES source/code comparison; exact pinned repository identities in REPOSITORY_SOURCE_INDEX.json.
- RESEARCH_DAG.json and NEXT_RESEARCH_PROMPT_KO.md: remaining observational-contract work; no automatic handoff required.

## Reproduce the finite checks

From this directory, run:

```bash
python check_joint_operator_fraction.py
python agent_kinematics_checks.py
python statistics_checks.py
```

The first needs only Python standard library. The second needs NumPy. The third needs NumPy and SciPy. None evolves cosmological ODE/PDE/Boltzmann equations or accesses real CMB datasets. They overwrite their own result JSONs, so preserve a copy if comparing exact delivery bytes. Python 3.12.14 was used in this execution; package metadata accompanies results where recorded.

check_joint_operator.py is the preserved initial SymPy attempt and is not the recommended entry point; it failed because SymPy was absent. Successful equivalent exact Fraction implementation is separate. Original package failures and the Wolfram wrapper syntax failure are retained in state/ANOMALY_LEDGER.md and evidence. No failed Python package import was treated as runtime unavailability.

## Evidence and provenance

CANDIDATE_V1_IDENTITY.json records the first review target; V1 report/statistics copies are preserved. The independent reviewer found and corrected the likelihood constraint's reference translation: admissibility is k-k_ref in B, not k in B. V3 is the final reviewed candidate. Do not use the V1 copies as current science.

MANIFEST_SHA256.json hashes every delivered file except itself. The outer ZIP SHA and packaging check are supplied separately. These identities establish byte linkage, not mathematical proof. Source literature identities and read scope are explicit. The bundled Astra harness is the R1-authorized v4.0.0 package; its templates are not research execution evidence.

VIGILODE is not a dependency. No repo research other than MES-bound material was used. No repository changes or push were performed. Actual observations, a finite nonlinear MES theorem, full polarization response, physically useful residual bounds, and publication novelty remain open.
