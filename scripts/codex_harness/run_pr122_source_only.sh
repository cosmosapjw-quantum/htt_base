#!/bin/sh
# Launch the PR-122 evidence producer/consumers before Python can process site
# startup hooks or workspace bytecode.  This is a bound trust surface, not an
# authorization token: the target programs also verify the runtime flags,
# explicit paths, empty cache, hidden controls, target identity, and this
# launcher's content hash.

set -eu
PATH=/usr/bin:/bin
export PATH

die() {
    printf '%s\n' "$*" >&2
    exit 64
}

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
SELF="$SELF_DIR/$(basename -- "$0")"
ROOT=$(CDPATH= cd -- "$SELF_DIR/../.." && pwd -P)
EXPECTED_SELF="$ROOT/scripts/codex_harness/run_pr122_source_only.sh"

[ "$SELF" = "$EXPECTED_SELF" ] || die "PR-122 launcher path is noncanonical"
[ -f "$SELF" ] && [ ! -L "$SELF" ] || die "PR-122 launcher is not a regular file"
[ "$#" -ge 1 ] || die "usage: run_pr122_source_only.sh TARGET [ARG ...]"

TARGET_REL=$1
shift
case "$TARGET_REL" in
    scripts/codex_harness/build_claim_evidence_graph.py | \
    scripts/check_publication_claim_freeze.py | \
    scripts/build_external_audit_package.py)
        ;;
    *)
        die "target is not in the PR-122 source-only allowlist: $TARGET_REL"
        ;;
esac

TARGET="$ROOT/$TARGET_REL"
[ -f "$TARGET" ] && [ ! -L "$TARGET" ] || die "PR-122 target is not a regular file"

PYTHON="$ROOT/venv/bin/python"
[ -x "$PYTHON" ] && [ ! -L "$ROOT/venv" ] || die "canonical PR-122 Python is unavailable"

SITE_PACKAGES=
SITE_COUNT=0
for candidate in "$ROOT"/venv/lib/python*/site-packages; do
    if [ -d "$candidate" ] && [ ! -L "$candidate" ]; then
        SITE_PACKAGES=$candidate
        SITE_COUNT=$((SITE_COUNT + 1))
    fi
done
[ "$SITE_COUNT" -eq 1 ] || \
    die "expected exactly one regular canonical venv site-packages directory"

CACHE=$(mktemp -d "/tmp/htt-pr122-pycache.XXXXXX") || \
    die "could not allocate PR-122 source-only cache"

cleanup() {
    status=$?
    trap - 0
    residue=$(find "$CACHE" -mindepth 1 -print -quit 2>/dev/null || true)
    if [ -n "$residue" ]; then
        printf '%s\n' "PR-122 source-only cache is not empty: $CACHE" >&2
        status=97
    elif ! rmdir "$CACHE"; then
        printf '%s\n' "could not remove empty PR-122 source-only cache: $CACHE" >&2
        status=98
    fi
    exit "$status"
}
trap cleanup 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

LAUNCHER_SHA256=$(sha256sum "$SELF") || die "could not hash PR-122 launcher"
LAUNCHER_SHA256=${LAUNCHER_SHA256%% *}

export HTT_PR122_SOURCE_ONLY_PREFIX="$CACHE"
export HTT_PR122_SOURCE_ONLY_LAUNCHER_SHA256="$LAUNCHER_SHA256"
export HTT_PR122_SOURCE_ONLY_SITE_PACKAGES="$SITE_PACKAGES"
export HTT_PR122_SOURCE_ONLY_TARGET="$TARGET_REL"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
unset PYTHONHOME PYTHONPATH PYTHONSTARTUP PYTHONUSERBASE
unset PYTEST_ADDOPTS PYTEST_PLUGINS

BOOTSTRAP='import os,runpy,sys
root,site_packages,target,*args=sys.argv[1:]
sys.path[:0]=[root+"/htt/src",root+"/htt",site_packages]
os.chdir(root)
sys.argv=[target,*args]
runpy.run_path(target,run_name="__main__")'

cd "$ROOT"
"$PYTHON" \
    -I \
    -S \
    -B \
    -X "pycache_prefix=$CACHE" \
    -c "$BOOTSTRAP" \
    "$ROOT" "$SITE_PACKAGES" "$TARGET" "$@"
