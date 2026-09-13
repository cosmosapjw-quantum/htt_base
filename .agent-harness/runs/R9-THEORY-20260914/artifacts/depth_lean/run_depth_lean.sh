#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  printf '%s\n' '{"checks":{},"domain_assumption_diff":["expected exactly one proposition identifier"],"counterexample":null}'
  exit 64
fi

case "$1" in
  D1|D3|D2|D4) ;;
  *)
    printf '%s\n' '{"checks":{},"domain_assumption_diff":["expected exactly one of D1,D3,D2,D4"],"counterexample":null}'
    exit 64
    ;;
esac

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)
cd "$repo_root/formal"
exec lake env lean --run ../.agent-harness/runs/R9-THEORY-20260914/artifacts/depth_lean/DepthCore.lean "$1"
