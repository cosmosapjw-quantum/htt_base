# Current optical paper

The qualified repaired baseline is extended by the conditional appendix in `repair_01/report/main.pdf`.

Current cached-source assembly/check: `python3 repair_01/report/r36_optical/publication_overlay.py assemble|check --contract repair_01/report/r36_optical/EDITOR_CONTRACT.json --repo REPO --output-root REPO`. Build with `latexmk -pdf -interaction=nonstopmode -halt-on-error -cd -outdir=r36_optical/build repair_01/report/main.tex`, then copy the new build PDF to main.pdf. Historical build_source.py recreates the old paper.

Source qualification, manuscript review, installation and scientific admission remain separate. Missing empirical covariance, source/frame transfer and physical error bounds remain unavailable.
