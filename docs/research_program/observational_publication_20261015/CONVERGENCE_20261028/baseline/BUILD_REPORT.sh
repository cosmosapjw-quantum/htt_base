#!/usr/bin/env bash
set -euo pipefail
# Preserve frozen manuscript/PDF hashes; build into an explicit new output directory.
HTT_BUILD_SOURCE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
HTT_BUILD_OUTPUT=${1:?Usage: BUILD_REPORT.sh /absolute/new-output-directory}
mkdir -p -- "$HTT_BUILD_OUTPUT"
HTT_BUILD_OUTPUT=$(cd -- "$HTT_BUILD_OUTPUT" && pwd)
if [[ "$HTT_BUILD_OUTPUT" == "$HTT_BUILD_SOURCE" ]]; then
  echo "Choose a new output directory; the source baseline is frozen." >&2
  exit 2
fi
cd -- "$HTT_BUILD_SOURCE"
pandoc BASELINE_REPORT.md --from=markdown+tex_math_single_backslash --standalone -V mainfont="DejaVu Serif" -V sansfont="DejaVu Sans" -V monofont="DejaVu Sans Mono" --pdf-engine=xelatex -o "$HTT_BUILD_OUTPUT/BASELINE_REPORT.pdf"
pandoc BASELINE_REPORT.md --from=markdown+tex_math_single_backslash --standalone -V mainfont="DejaVu Serif" -V sansfont="DejaVu Sans" -V monofont="DejaVu Sans Mono" -t latex -o "$HTT_BUILD_OUTPUT/BASELINE_REPORT.tex"
