# Reviewed public-SN source candidate backup

Current status: FORMALLY_QUALIFIED_RELEASED_MAGNITUDE_CONDITIONAL_COMPARATOR. Actual formal review packet53df9b5a78c6543c23f0210f25b330efbd23cfe1b7c804ff0b550263c209fe50 was recorded with acceptance_met=true and qualified_products=[public_sn_anisotropy_result] for unchanged candidateefeb05dfe755f47c48c994d1684312659277816a3f7294f6d76f63f27f9f046c. Exact formal RETURN/raw/ACK017/NEXT017 and preformal reader/status history are in ../independent_review/formal_binding_01/. Only the released-magnitude fixed-background conditional comparator is qualified. Selected490/705 raw covariance blocks remain exactly symmetric and positive definite, consumed once without an added duplicate PV term. The full1701 source covariance defect remains FAILED_OUTSIDE_CONSUMED_SUPPORT,389pairs and cause UNKNOWN; no source repair or full-covariance certification is implied. No nominal SALT2 parity, absoluteH0, physical sky-frame/boost, native solver or original42 promotion follows. All16 survey deletions, source/repair decision and first failures remain unchanged; the frozen note line49 erratum below is still consumed without rewriting the note.

## Command erratum for frozen RESEARCH_NOTE.md line49

Use the repository root as cwd (`/home/cosmosapjw/Dropbox/bianchi/htt_base` in the original environment). The original sealed note and manifest remain untouched. Interpreter and script paths were resolved by the publisher; no fits, tests or plots were rerun.

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-08-PUBLIC-SN/consumer.py
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-08-PUBLIC-SN/test_consumer.py
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-08-PUBLIC-SN/survey_robustness.py
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-08-PUBLIC-SN/plot_result.py
```

SOURCE_MAP.json maps historical absolute paths to repository copies. OMITTED_INPUTS.json preserves excluded observational source identities. Reacquire Pantheon+SH0ES from the pinned public DataRelease commit c447f0fea703fcd0fff57de5000947b5ca81286b, Pantheon+_Data/4_DISTANCES_AND_COVAR/Pantheon+SH0ES.dat and Pantheon+SH0ES_STAT+SYS.cov, verifying the archived hashes. Paths in frozen code/receipts are historical cache aliases; configure the original locations for exact replay. Author, executor and independent reviewer remain distinct from this mechanical publisher.
