# Four physical research goals: internal theory study, 28 October 2026

Read `output/FOUR_GOALS_REPORT.md` for the integrated study and
`output/RESEARCH_DECISION.md` for contribution priorities and prior-art comparisons.
The separate PDF renders the report in 37 pages with six scientific figures.
`output/OPTICAL_BRIDGE_INSERTIONS.md` contains the two proposed English additions
to the supplied optical manuscript. The manuscript itself was not edited.

The source branch was checked at
`7f3f49a6b6d95b6ae0323d5bebd3afce0067b1a7` on
`research/htt-adaptive-methods-20261023`, repository
`cosmosapjw-quantum/htt_base`. Source receipts preserve exact paths and identities.
Two user-supplied PDFs, the pinned R36 geometry fixture, and reused research
interpretations are included. Full texts of third-party publications are excluded;
the lane notes retain citations and what was read.

## Contents

- `lanes/`: four theory reports, the finite photon-count experiment, the joint
  physical-error construction, numerical JSON, and the independent review.
- `code/`: six production scripts plus an independently implemented reviewer.
- `figures/`: six figures in PNG and vector PDF formats.
- `sources/`: provenance, qualified earlier results, user attachments and tool receipts.
- `RESEARCH_UNITS.json`: proposed next research units, required physical inputs,
  actual operations, validation conditions and interpretation boundaries.
- `RESULT_SUMMARY.json`: concise machine-readable outcomes.
- `ARTIFACT_MANIFEST.json`: SHA-256 and sizes for the packaged files, plus the
  separately delivered rendered report.

The current finite theory units are complete. The next observational adapters
are proposed work, not completed observations. No native solver, ODE evolution,
raw-catalogue refit, repository push, or live DAG/controller mutation was performed.
No original scientific acceptance criterion or completion count was promoted.

## Reproduce the numerical checks

Unpack into a new directory before rerunning: scripts intentionally write their
result JSON and figures. Preserve the delivered review and execution receipts;
rerunning `review_checks.py` regenerates its numerical checks but not the reviewer's
later explanatory annotations. All scripts resolve inputs relative to this bundle.

The executed environment was Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0 and
Matplotlib 3.10.8. SymPy is not required. Exact angular checks use standard-library
`fractions.Fraction`. Monte Carlo counts and seeds are recorded in each result JSON.

```bash
export OPENBLAS_NUM_THREADS=1
python code/goal1_thomson_response.py
python code/goal2_kinematic_design.py
python code/goal3_classification.py
python code/goal4_cbl.py
python code/fibre_info.py --draws 100000
python code/joint_remainder.py
python code/review_checks.py
```

Goal 3 checks the Git blob identity of the bundled `R36_GEOMETRY_TABLE.json`.
The remaining finite numerical scripts require no catalogue download or remote
service. Wolfram, Exa and SciSpace records document the actual source/algebra checks;
they need not be called again to run these scripts.

The sign-discrimination result was corrected to handle exact likelihood-ratio ties
with equal-prior randomized assignment. The updated result is 98.086%, with 155 ties
in 100,000 trials. `sources/fibre_info_SIGN_REPAIR.json` preserves the older receipt
and the isolated correction; the integrated report uses only the corrected result.

## Render the report

Pandoc, XeLaTeX and DejaVu fonts are required for rendering; PyMuPDF is required
only for the mechanical page check. From the bundle root:

```bash
python assemble_report.py
cd output
pandoc FOUR_GOALS_REPORT.md --from=markdown+tex_math_single_backslash+tex_math_dollars --pdf-engine=xelatex -V mainfont='DejaVu Serif' -V sansfont='DejaVu Sans' -V monofont='DejaVu Sans Mono' -V documentclass=article --toc --toc-depth=1 -o HTT_FOUR_GOALS_FIBRE_20261028.pdf
cd ..
python code/check_pdf_layout.py
```

The source ZIP omits the separately supplied rendered report, QA page images,
Python caches, and third-party article copies. It includes the user's two original
PDFs. `ARTIFACT_MANIFEST.json` does not hash itself or the enclosing ZIP.
