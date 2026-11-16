#!/usr/bin/env python3
"""Bring node R54-THM (merged with the closed local work) into the working branch of the local session.

Run from the repository root, on the working branch, at a safe checkpoint (clean tree, no process of yours running):

    git fetch origin +refs/heads/research/r54-theorems-20261116:refs/remotes/origin/research/r54-theorems-20261116
    git show origin/research/r54-theorems-20261116:scripts/r54/handoff_merge.py | python - apply
    (resolve the hand-written files that `apply` lists, if any, and `git add` them)
    python scripts/r54/handoff_merge.py finish

Commands
    preflight          read-only: reports ALREADY_APPLIED, FAST_FORWARD, MERGE, MERGE_IN_PROGRESS or BLOCKED with the reason
    apply              preflight, then fast-forward or `git merge --no-ff --no-commit`, then resolve-generated, then status
    resolve-generated  conflicted generated documents, the mutation receipt and the mirrors: take one side (they are rebuilt by `finish`)
    status             conflicted hand-written files, each with the rule that applies
    finish             mirror sync, mutation receipt, builder, DAG validator, mirror check, tests/r54; prints HANDOFF OK

The script never commits, never pushes, never deletes work and never resolves a hand-written file. It does not import the
contract builder, because that file may itself be in conflict while this script runs.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REL = "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116"
SOURCE_BRANCH = "research/r54-theorems-20261116"
SOURCE_REF = "refs/remotes/origin/" + SOURCE_BRANCH
#: commit of the restart prompt that the running local session was started from
START_COMMIT = "35a28e20cb66096c358296755c04db9cfa4a7ca6"
PROTECTED_BRANCHES = ("main", "master", "research/r50-observed-convergence-20261115", SOURCE_BRANCH, "HEAD")
FETCH = f"git fetch origin +refs/heads/{SOURCE_BRANCH}:{SOURCE_REF}"
#: outputs of `build_r54_contract.py build`; tests/r54/test_r54_handoff.py keeps this list equal to the builder's
GENERATED_NAMES = ("RESEARCH_DAG.json", "LOCAL_AGENT_CONTRACT.json", "MUTATION_GATES.json", "SELF_AUDIT_PROTOCOL.json",
                   "ADVERSARIAL_BENCHMARK_SPEC.json", "PR4_BYPASS_CONTRACT.json", "HISTORY_AUDIT.json", "HANDOFF_UPDATE.json",
                   "state/HYPOTHESES.json", "state/RESEARCH_STATE.md", "state/EVIDENCE_LEDGER.md", "state/HYPOTHESIS_GRAPH.md",
                   "state/DECISION_LOG.md", "state/NEGATIVE_RESULTS.md", "R54_REPORT_KO.md", "THEORY_LOOPS.md",
                   "LOCAL_AGENT_RESTART_PROMPT.txt", "LOCAL_AGENT_HANDOFF_UPDATE.txt", "README.md",
                   "MANUSCRIPT_CLAIM_TABLE_R54.md", "FINAL_DECISION_R57.md")
GENERATED = tuple(f"{REL}/{name}" for name in GENERATED_NAMES)
RECEIPT = f"{REL}/MUTATION_GATE_RECEIPT.json"
MIRRORS = ("machine_readable/pr_status.yaml", "machine_readable/pr_backlog.yaml", "machine_readable/pr_backlog.json")
BACKUP_SUFFIX = ".r54_mutation_backup"
#: directories in which the mutation receipt rewrites a source file
BACKUP_DIRS = ("htt/htt/htt/infer", "scripts/r54")
#: paths that the update leaves untouched relative to START_COMMIT; an update that touches one of them is refused
UNTOUCHED = (REL + "/RESULTS", REL + "/INDEPENDENT_REVIEW.json", REL + "/R57_DECISION_REVIEW.json", REL + "/DEVIATIONS.json",
             "scripts/r54/run_r54_cmb_type1.py", "scripts/r54/run_r54_lowz_frames.py", "scripts/r54/run_r54_cf4_exact.py",
             "scripts/r54/run_r54_l01_te_calibration.py", "scripts/r54/run_r54_l02_pr4_bypass.py", "scripts/r54/run_r54_l03_counts.py",
             "scripts/r54/run_r54_l04_cf4_survey.py", "scripts/r54/run_r54_l06_joint.py", "scripts/r54/run_r54_l07_benchmark.py",
             "htt/htt/htt/infer/r54_tensor_five_view.py", "htt/htt/htt/infer/r54_type1_thomson.py", "htt/htt/htt/infer/r54_lcdm_body.py",
             "htt/htt/htt/infer/r54_distance_estimators.py", "htt/htt/htt/infer/r54_calibration.py", "htt/htt/htt/infer/r54_counts.py",
             "htt/htt/htt/infer/r54_joint.py", "htt/htt/htt/infer/r54_pr4_bypass.py", "htt/htt/htt/infer/r54_survey.py",
             "tests/r54/test_r54_modules.py", "tests/r54/test_r54_conventions.py", "tests/r54/test_r54_calibration.py", "tests/r54/test_r54_survey.py",
             "tests/r54/test_r54_counts.py", "tests/r54/test_r54_pr4_bypass.py", "tests/r54/test_r54_joint.py",
             "docs/codex_handoff/pr_backlog.yaml", "docs/codex_handoff/pr_backlog.json")
RESERVED = "evidence E50-E69, gates MG-30..MG-35, hypotheses H-T1 H-T2 H-T6 H-T7 H-T8 H-T9, cloud node R54-THM"
RULES = {
    "scripts/r54/build_r54_contract.py": "keep BOTH sides. Reserved by this update: " + RESERVED + ". If you used one of these ids, renumber YOUR entry "
                                         "to the next free id above the reserved ranges and update its citations. For an evidence row edited on both sides keep the claim text of "
                                         "this update and the stronger verification status.",
    "tests/r54/test_r54_results_binding.py": "keep BOTH sides; no test may be deleted or weakened. Where both sides changed the same assertion keep the "
                                             "version of this update and re-add your own additional assertions below it.",
    "tests/r54/test_r54_modules.py": "this update does not change the file; keep your side.",
    "tests/r54/test_r54_theorems.py": "new in this update; if you created a file of the same name, rename yours.",
    "tests/r54/test_r54_handoff.py": "new in this update; if you created a file of the same name, rename yours.",
    "docs/codex_handoff/pr_status.yaml": "keep both sides (your status moves and the note line of this update); `finish` rewrites the mirrors.",
    f"{REL}/INDEPENDENT_REVIEW.json": "this update does not change the file; keep your side.",
    f"{REL}/THEOREMS.md": "new in this update; keep the version of this update and re-apply your own edit, if any, as an appended line.",
}
DEFAULT_RULE = "this update does not touch the file: stop and report the conflict instead of guessing."


def repo_root() -> Path:
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit("BLOCKED: run this command inside the htt_base repository")
    return Path(res.stdout.strip())


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def lines(root: Path, *args: str) -> list[str]:
    res = git(root, *args)
    if res.returncode != 0:                                  # never read a failed query as "clean" (review finding R54-A1-11)
        raise SystemExit(f"BLOCKED: git {' '.join(args)} failed: {res.stderr.strip()[:300]}")
    return [ln for ln in res.stdout.splitlines() if ln.strip()]


def classify(path: str) -> str:
    """'generated', 'receipt' or 'mirror' (all rebuilt by `finish`); anything else is 'hand_written' and is never resolved here."""
    if path in GENERATED:
        return "generated"
    if path == RECEIPT:
        return "receipt"
    return "mirror" if path in MIRRORS else "hand_written"


def rule_for(path: str) -> str:
    return "rebuilt by `finish`; run `resolve-generated`" if classify(path) != "hand_written" else RULES.get(path, DEFAULT_RULE)


def backups(root: Path) -> list[str]:
    """Safety copies left behind by a mutation receipt that was killed."""
    return sorted(str(p.relative_to(root)) for d in BACKUP_DIRS for p in (root / d).glob(f"*{BACKUP_SUFFIX}"))


def unmerged(root: Path) -> list[str]:
    return lines(root, "diff", "--name-only", "--diff-filter=U")


def merging(root: Path) -> bool:
    return git(root, "rev-parse", "--verify", "--quiet", "MERGE_HEAD").returncode == 0


def is_ancestor(root: Path, old: str, new: str) -> bool:
    return git(root, "merge-base", "--is-ancestor", old, new).returncode == 0


def preflight(root: Path, start: str = START_COMMIT, source: str = SOURCE_REF) -> tuple[str, list[str]]:
    """State of the working branch relative to the update and the reasons; read-only."""
    if git(root, "rev-parse", "--verify", "--quiet", source + "^{commit}").returncode != 0:
        return "BLOCKED", [f"the update is not fetched; run: {FETCH}"]
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branch in PROTECTED_BRANCHES:                         # the guards run before the open-merge state (review finding R54-A1-03)
        return "BLOCKED", [f"current branch is '{branch}'; check out your working branch (the update is never merged into this one)"]
    if not is_ancestor(root, start, "HEAD"):
        return "BLOCKED", [f"your branch does not contain the R54 start commit {start[:8]}; stop and report"]
    if merging(root):
        merge_head = git(root, "rev-parse", "MERGE_HEAD").stdout.strip()
        if merge_head != git(root, "rev-parse", source + "^{commit}").stdout.strip():
            return "BLOCKED", ["a merge of another commit is open; finish or abort it (`git merge --abort`) before applying the update"]
        return "MERGE_IN_PROGRESS", ["a merge is open; continue with `status` and `finish`, or `git merge --abort` to start again"]
    if is_ancestor(root, source, "HEAD"):
        return "ALREADY_APPLIED", ["your branch already contains the update"]
    dirty = lines(root, "status", "--porcelain", "--untracked-files=no")
    if dirty:
        return "BLOCKED", ["tracked files have uncommitted changes; commit them first (card id as prefix):"] + dirty[:20]
    left = backups(root)
    if left:
        return "BLOCKED", ["a mutation receipt was interrupted; run `python scripts/r54/build_r54_contract.py mutation-receipt` once, then retry:"] + left
    base = git(root, "merge-base", "HEAD", source).stdout.strip()
    touched = lines(root, "diff", "--name-only", base, source, "--", *UNTOUCHED)
    if touched:
        return "BLOCKED", ["unexpected: the update changes files that it declares untouched; stop and report:"] + touched
    if is_ancestor(root, "HEAD", source):
        return "FAST_FORWARD", ["the update already contains every commit of your branch; it can be fast-forwarded"]
    both = sorted(set(lines(root, "diff", "--name-only", base, "HEAD")) & set(lines(root, "diff", "--name-only", base, source)))
    return "MERGE", ["files changed on both sides (a conflict is possible only in these):"] + [f"  [{classify(p)}] {p}" for p in both]


def resolve_generated(root: Path) -> list[str]:
    """Take one side for conflicted generated files; they are rebuilt by `finish`. Returns the files it resolved."""
    done = []
    for path in unmerged(root):
        if classify(path) == "hand_written":
            continue
        if git(root, "checkout", "--theirs", "--", path).returncode != 0 and git(root, "checkout", "--ours", "--", path).returncode != 0:
            raise SystemExit(f"BLOCKED: cannot take either side of {path}; stop and report")
        if git(root, "add", "--", path).returncode != 0:
            raise SystemExit(f"BLOCKED: git add failed for {path}")
        done.append(path)
    return done


def status(root: Path) -> list[str]:
    left = unmerged(root)
    print(f"merge in progress: {merging(root)}; unmerged files: {len(left)}")
    for path in left:
        print(f"  [{classify(path)}] {path}\n      rule: {rule_for(path)}")
    return left


def apply(root: Path, start: str = START_COMMIT, source: str = SOURCE_REF) -> str:
    state, why = preflight(root, start, source)
    print("\n".join(why))
    if state in ("BLOCKED", "ALREADY_APPLIED"):
        return state
    if state == "FAST_FORWARD":
        res = git(root, "merge", "--ff-only", source)
        if res.returncode != 0:
            print(res.stdout + res.stderr)
            return "BLOCKED"
        return "FAST_FORWARDED"
    if state == "MERGE":
        res = git(root, "merge", "--no-ff", "--no-commit", source)
        if not merging(root):                       # git refused before it started (for example an untracked file in the way)
            print(res.stdout + res.stderr)
            return "BLOCKED"
    resolved = resolve_generated(root)
    print(f"generated files resolved by taking one side (rebuilt by `finish`): {len(resolved)}")
    return "MERGE_CONFLICTS" if status(root) else "MERGE_READY"


def finish_blockers(root: Path) -> list[str]:
    """Reasons why the verification must not start; empty when the tree is ready."""
    out = [f"unmerged: {p} ({rule_for(p)})" for p in unmerged(root)]
    marks = git(root, "grep", "-n", "-E", "^(<<<<<<<|>>>>>>>) ", "--", "scripts/r54", "tests/r54", "htt/htt/htt/infer", REL, "docs/codex_handoff", "machine_readable")
    if marks.returncode > 1:                                 # 1 means no match; above 1 is an error (review finding R54-A1-11)
        out.append(f"git grep for conflict markers failed: {marks.stderr.strip()[:200]}")
    out += [f"conflict marker left in {ln}" for ln in marks.stdout.splitlines()[:20]]
    out += [f"interrupted mutation receipt: {p} (run the receipt once; it restores the source)" for p in backups(root)]
    return out


def finish(root: Path) -> int:
    blockers = finish_blockers(root)
    if blockers:
        print("HANDOFF FAILED before verification:\n  " + "\n  ".join(blockers))
        return 2
    env = dict(os.environ, PYTHONPATH="htt/src:htt:.")
    steps = (("mirror sync", [sys.executable, "scripts/codex_harness/sync_pr_dag_mirrors.py", "--write"]),
             ("mutation receipt", [sys.executable, "scripts/r54/build_r54_contract.py", "mutation-receipt"]),
             ("build", [sys.executable, "scripts/r54/build_r54_contract.py", "build"]),
             ("dag", [sys.executable, "scripts/codex_harness/validate_pr_dag.py", "docs/codex_handoff/pr_backlog.yaml", "--status",
                      "docs/codex_handoff/pr_status.yaml", "--strict-rescue-slice"]),
             ("mirror check", [sys.executable, "scripts/codex_harness/sync_pr_dag_mirrors.py", "--check"]),
             ("tests", [sys.executable, "-m", "pytest", "tests/r54", "-q", "-p", "no:cacheprovider"]))
    for name, cmd in steps:
        res = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True)
        tail = ((res.stdout.strip() or res.stderr.strip()).splitlines() or [""])[-1]
        print(f"[{name}] exit {res.returncode}: {tail[:160]}")
        if res.returncode != 0:
            print(res.stdout[-3000:] + "\n" + res.stderr[-2000:])
            print(f"HANDOFF FAILED at step '{name}'. Fix the cause; never delete or weaken a test or a gate. Then run `finish` again.")
            return 1
    for path in (*GENERATED, RECEIPT, *MIRRORS):                      # stage what the steps above rewrote, nothing else
        if (root / path).is_file():
            res = git(root, "add", "--", path)
            if res.returncode != 0:                                   # review finding R54-A1-04: never report OK over a failed stage
                print(f"[stage] exit {res.returncode}: {res.stderr.strip()[:160]}")
                print(f"HANDOFF FAILED at step 'stage' ({path}). Fix the cause (for example a stale .git/index.lock), then run `finish` again.")
                return 1
    open_merge, staged = merging(root), lines(root, "diff", "--cached", "--name-only")
    print("HANDOFF OK")
    unstaged = lines(root, "diff", "--name-only")
    if unstaged:                                                      # typically a result file of a finished node that received the new keys
        print("tracked files with changes that are not staged (git add each one that belongs to this update before you commit):\n  " + "\n  ".join(unstaged))
    if open_merge or staged or unstaged:
        print('next: git commit -m "PR-R54-TENSOR-FRAME-TOMOGRAPHY: merge R54-THM addendum and handoff update"   then   git push origin HEAD')
    else:
        print("next: nothing to commit; git push origin HEAD")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("preflight", "apply", "resolve-generated", "status", "finish"))
    command = ap.parse_args().command
    root = repo_root()
    if command == "preflight":
        state, why = preflight(root)
        print("\n".join(why) + f"\nRESULT: {state}")
        return 2 if state == "BLOCKED" else 0
    if command == "apply":
        state = apply(root)
        print(f"RESULT: {state}")
        return 2 if state == "BLOCKED" else 0
    if command == "resolve-generated":
        print(f"resolved: {len(resolve_generated(root))}; hand-written files left: {len(unmerged(root))}")
        return 0
    if command == "status":
        status(root)
        return 0
    return finish(root)


if __name__ == "__main__":
    raise SystemExit(main())
