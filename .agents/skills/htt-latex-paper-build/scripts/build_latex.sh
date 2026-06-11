#!/usr/bin/env bash
set -u
MAIN="${1:-}"
if [ -z "$MAIN" ]; then
  if [ -f "main.tex" ]; then MAIN="main.tex"; elif [ -f "main(2).tex" ]; then MAIN="main(2).tex"; else MAIN="$(find . -maxdepth 3 -name '*.tex' | head -n 1)"; fi
fi
if [ -z "$MAIN" ]; then echo "No .tex file found."; exit 2; fi
mkdir -p docs/harness/latex_build_logs
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="docs/harness/latex_build_logs/build_${STAMP}.log"
echo "Building: $MAIN" | tee "$LOG"
if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -halt-on-error "$MAIN" 2>&1 | tee -a "$LOG"; STATUS=${PIPESTATUS[0]}
elif command -v pdflatex >/dev/null 2>&1; then
  pdflatex -interaction=nonstopmode -halt-on-error "$MAIN" 2>&1 | tee -a "$LOG"; STATUS1=${PIPESTATUS[0]}
  pdflatex -interaction=nonstopmode -halt-on-error "$MAIN" 2>&1 | tee -a "$LOG"; STATUS2=${PIPESTATUS[0]}
  if [ "$STATUS1" -eq 0 ] && [ "$STATUS2" -eq 0 ]; then STATUS=0; else STATUS=1; fi
else
  echo "No latexmk or pdflatex found." | tee -a "$LOG"; STATUS=2
fi
python3 "$(dirname "$0")/check_latex_log.py" "$LOG" || true
exit "$STATUS"
