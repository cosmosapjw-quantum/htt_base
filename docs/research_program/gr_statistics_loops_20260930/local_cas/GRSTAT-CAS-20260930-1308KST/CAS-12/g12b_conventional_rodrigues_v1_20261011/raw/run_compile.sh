#!/usr/bin/env bash
set -u
task=/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-12/g12b_conventional_rodrigues_v1_20261011
dep=/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-12/c02_all_degree_scalar_wrapper_v1_20261011/ScalarWrapper.lean
oracle=/home/cosmosapjw/lean_oracles/viii_oracle
label=$1
mode=$2
mkdir -p "$task/raw/imports"
cp "$task/lean/ConventionalRodrigues.lean" "$task/raw/${label}_source.lean"
src_hash=$(sha256sum "$task/raw/${label}_source.lean" | cut -d ' ' -f 1)
dep_hash=$(sha256sum "$dep" | cut -d ' ' -f 1)
cd "$oracle" || exit 99
case "$mode" in
  dep) cmd=(lake env lean -R "$(dirname "$dep")" -o "$task/raw/imports/ScalarWrapper.olean" "$dep") ;;
  source) cmd=(lake env bash -c "LEAN_PATH=$task/raw/imports:\$LEAN_PATH lean -R $task/lean -o $task/raw/imports/ConventionalRodrigues.olean $task/lean/ConventionalRodrigues.lean") ;;
  audit) cmd=(lake env bash -c "LEAN_PATH=$task/raw/imports:\$LEAN_PATH lean -R $task/raw $task/raw/AxiomAudit.lean") ;;
  *) exit 98 ;;
esac
argv_json=$(printf '%s\n' "${cmd[@]}" | jq -R . | jq -s .)
printf '%s\n' "$argv_json" > "$task/raw/${label}.argv.json"
"${cmd[@]}" > "$task/raw/${label}.stdout.log" 2> "$task/raw/${label}.stderr.log"
code=$?
jq -n --arg label "$label" --arg mode "$mode" --arg cwd "$oracle" \
  --arg source_sha256 "$src_hash" --arg accepted_source_sha256 "$dep_hash" \
  --argjson exit_code "$code" --argjson argv "$argv_json" \
  '{label:$label, mode:$mode, cwd:$cwd, argv:$argv, exit_code:$exit_code,
    source_snapshot_sha256:$source_sha256, accepted_source_sha256:$accepted_source_sha256}' \
  > "$task/raw/${label}.receipt.json"
exit "$code"
