# HTT R9 theory-integrated plan — supporting evidence

Scope: fixed-source plan development, conditional derivations, exact counterexamples and bounded synthetic checks. No production, observation, formal admission, catalog status update, Git commit or remote push.

## Inputs
- R9 commit 5e4e899c0dfa2028d81a82ca68ccd11203947470, tree dbfcdc9abc2298534b65f50ae6a19ab0012aa999.
- Catalog commit 9b725899a25fa410e7c3686ce36afaa667d14646, tree 508500f4eadeafcdfb316978c4a05a6b238a13f7.
- SOURCE_MANIFEST.json: 18 source texts with path, ref, exact Git blob, byte length and SHA-256.
- Archive-embedded historical sources are catalog-held excerpts, not newly extracted full archives.

## Reproduction
Run from the extracted package root with Python 3.12; the second command also needs NumPy (observed 2.3.5):

    python research_review/exact_counterexamples.py
    python research_review/math_agent/check_extensions.py

These overwrite only their corresponding check JSON in the extracted copy. They are bounded algebra fixtures, not empirical mocks or production tests. The first command uses exact rational arithmetic; the Fisher fixture uses arbitrary integer blocks and a fixed noisy linear processor.

## Review
- catalog_agent/: full-list screening, 43 source-qualified excerpts and eight-family mapping.
- math_agent/: independent authored derivations and executed numerical corroboration.
- revision_review/: independent review of the assembled plan, including correction history.
- RESEARCH_RECORD.md: frozen question/methods and append-only evidence log.

The main Korean plan contains the adopted six work packages. Agent working reports contain additional exploration and are not independent proof-admission votes. Three explicit historical counterexamples are preserved without editing the original sources.
