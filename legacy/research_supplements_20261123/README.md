# Reused research supplements

This directory consolidates the reusable helpers and provenance from the four earlier studies. Production integrations live in `htt/bass/`, `htt/htt/htt/infer/`, and `scripts/r101/`; these supplement modules remain identified historical research utilities rather than duplicate production implementations.

- `FILE_CATALOGUE.json.gz`: 4,073 catalogue records, uncompressed JSON SHA-256 `732faefb69567b9a9bc6c394007a19e9606df9aaf6ed6a377c9d6caeac7c90f5`.
- Compressed SHA-256: `dd6e013fc8702e6451b8ec518b3d2405fd4528faf6b58946cc3c17b8f47f2254`.
- `COVERAGE.json`: earlier full/diff reading coverage, not an assertion of a new complete re-execution in R101.
- `COMPONENT_INDEX.json`, `EXACT_HELPER_PROVENANCE.json`, `CONSOLIDATION_DECISIONS.md`: component roles, exact versus adapted reuse, and decisions.
- `research_primitives.py`, `legacy_exact_helpers.py`, `response_primitives.py`: preserved reusable reference helpers. Consult their source and contracts before importing.

Catalogue `canonical_path` values identify the original delivery-bundle paths. Original archive members are not all installed at those paths in the owner checkout. R101 recovered the BASS/HYREC inputs actually required by the executed calculations using pinned git objects and official atomic files; `configs/r101/legacy_recovery.json` and the R101 resource receipt identify them. Production ports explicitly credit the recovered source. No duplicate 145 MB archive bundle is required to run the R101 modules.
