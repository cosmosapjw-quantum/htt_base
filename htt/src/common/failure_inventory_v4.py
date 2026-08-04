"""Exact JUnit failure classification for the PR-280 diagnostic inventory."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as importlib_metadata
import json
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from common.harness_profiles_v4 import FAILURE_BUCKETS, HarnessProfileError


RULE_SCHEMA = "htt.full_inventory_failure_rules.v4"
CLASSIFICATION_SCHEMA = "htt.full_inventory_classification.v4"
RECEIPT_SCHEMA = "htt.full_inventory_receipt.v4"
EVIDENCE_CANONICALIZATION = "repo_home_and_pytest_tmp_v1"
JUNIT_COUNT_OBSERVABILITY = {
    "pass_vs_xpass": "not_distinguishable_in_pytest_junitxml",
    "deselected": "not_represented_in_pytest_junitxml",
    "passing_subtests": "not_individually_represented_in_pytest_junitxml",
}
DEFAULT_JUNIT = Path("artifacts/full_inventory.xml")
DEFAULT_RULES = Path(
    "docs/research_program/post_pr275/full_inventory_v4_failure_rules.yaml"
)
DEFAULT_CLASSIFICATION = Path(
    "docs/research_program/post_pr275/full_inventory_v4_classification.json"
)
DEFAULT_RECEIPT = Path(
    "docs/research_program/post_pr275/full_inventory_v4_receipt.json"
)
DEFAULT_MANIFEST = Path(
    "docs/research_program/post_pr275/harness_profiles_v4.yaml"
)
CLASSIFIER_PATH = Path("htt/src/common/failure_inventory_v4.py")
_GIT_RE = re.compile(r"[0-9a-f]{40,64}\Z")


class FailureInventoryError(ValueError):
    """Raised when inventory evidence is incomplete, ambiguous, or stale."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _strict_keys(
    value: Mapping[str, object], *, required: set[str], label: str
) -> None:
    missing = required - set(value)
    unknown = set(value) - required
    if missing or unknown:
        raise FailureInventoryError(
            f"{label} keys mismatch: missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise FailureInventoryError(f"{label} must be a non-empty string")
    return value


def _text_sequence(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise FailureInventoryError(f"{label} must be a string sequence")
    rows = tuple(_text(item, label) for item in value)
    if not rows or len(rows) != len(set(rows)):
        raise FailureInventoryError(f"{label} must be non-empty and unique")
    return rows


@dataclass(frozen=True)
class JunitNonPass:
    case_identity: str
    outcome: str
    evidence_sha256: str
    evidence_excerpt: str


@dataclass(frozen=True)
class FailureRule:
    rule_id: str
    bucket: str
    case_identities: frozenset[str]
    outcomes: frozenset[str]
    evidence_sha256: frozenset[str]

    def matches(self, case: JunitNonPass) -> bool:
        return (
            case.case_identity in self.case_identities
            and case.outcome in self.outcomes
            and case.evidence_sha256 in self.evidence_sha256
        )


def _failure_evidence(child: ET.Element) -> str:
    message = child.attrib.get("message", "")
    body = child.text or ""
    return (message + "\n" + body).strip()


def _canonical_failure_evidence(value: str, repo_root: Path | None) -> str:
    normalized = value
    if repo_root is not None:
        normalized = normalized.replace(str(repo_root.resolve()), "<REPO_ROOT>")
    normalized = normalized.replace(str(Path.home().resolve()), "<HOME>")
    normalized = re.sub(
        r"/tmp/pytest-of-[^/\s:'\"]+/pytest-\d+",
        "<PYTEST_TMP>",
        normalized,
    )
    return normalized


def _case_outcomes(case: ET.Element) -> tuple[tuple[str, ET.Element], ...]:
    terminal = [
        (tag, child)
        for tag in ("error", "failure", "skipped")
        for child in case.findall(tag)
    ]
    outcomes: list[tuple[str, ET.Element]] = []
    for tag, child in terminal:
        outcome = (
            "xfailed"
            if tag == "skipped" and child.attrib.get("type") == "pytest.xfail"
            else tag
        )
        outcomes.append((outcome, child))
    return tuple(outcomes)


def parse_junit(
    path: str | Path,
    *,
    evidence_repo_root: str | Path | None = None,
) -> tuple[dict[str, int], tuple[JunitNonPass, ...]]:
    junit = Path(path)
    if junit.is_symlink() or not junit.is_file():
        raise FailureInventoryError("JUnit input is missing or non-regular")
    try:
        root = ET.fromstring(junit.read_bytes())
    except ET.ParseError as exc:
        raise FailureInventoryError("JUnit input is malformed") from exc
    if root.tag == "testsuite":
        suites = [root]
    elif root.tag == "testsuites":
        suites = list(root.findall("testsuite"))
    else:
        raise FailureInventoryError("JUnit root must be testsuite or testsuites")
    if len(suites) != 1:
        raise FailureInventoryError("JUnit input must contain exactly one test suite")
    suite = suites[0]
    all_suites = list(root.iter("testsuite"))
    if all_suites != [suite]:
        raise FailureInventoryError("JUnit input contains a nested or foreign test suite")
    suite_cases = list(suite.iter("testcase"))
    if list(root.iter("testcase")) != suite_cases:
        raise FailureInventoryError("JUnit input contains testcase outside selected suite")
    cases: list[JunitNonPass] = []
    counts: Counter[str] = Counter()
    identities: set[str] = set()
    for case in suite_cases:
        classname = _text(case.attrib.get("classname"), "JUnit classname")
        name = _text(case.attrib.get("name"), "JUnit case name")
        base_identity = f"{classname}::{name}"
        if base_identity in identities:
            raise FailureInventoryError(
                f"duplicate JUnit case identity: {base_identity}"
            )
        identities.add(base_identity)
        outcomes = _case_outcomes(case)
        counts["collected"] += 1
        if not outcomes:
            counts["passed_case_elements"] += 1
            continue
        if len(outcomes) > 1:
            counts["multi_outcome_containers"] += 1
        for ordinal, (outcome, child) in enumerate(outcomes, start=1):
            counts[outcome] += 1
            identity = (
                base_identity
                if len(outcomes) == 1
                else f"{base_identity}::subtest[{ordinal:03d}]"
            )
            evidence = _canonical_failure_evidence(
                _failure_evidence(child),
                None if evidence_repo_root is None else Path(evidence_repo_root),
            )
            first_line = evidence.splitlines()[0] if evidence else "<no-junit-message>"
            cases.append(
                JunitNonPass(
                    case_identity=identity,
                    outcome=outcome,
                    evidence_sha256=_sha256_bytes(evidence.encode("utf-8")),
                    evidence_excerpt=first_line[:300],
                )
            )
    counts["skipped"] += 0
    counts["xfailed"] += 0
    counts["passed_case_elements"] += 0
    counts["failure"] += 0
    counts["error"] += 0
    counts["multi_outcome_containers"] += 0
    declared_fields = {
        "failures": counts["failure"],
        "errors": counts["error"],
        "skipped": counts["skipped"] + counts["xfailed"],
    }
    for field, observed in declared_fields.items():
        raw = suite.attrib.get(field)
        try:
            declared = int(raw) if raw is not None else None
        except ValueError as exc:
            raise FailureInventoryError(
                f"JUnit suite {field} count is malformed"
            ) from exc
        if declared != observed:
            raise FailureInventoryError(
                f"JUnit suite {field}={declared} does not match cases={observed}"
            )
    raw_tests = suite.attrib.get("tests")
    try:
        declared_tests = int(raw_tests) if raw_tests is not None else None
    except ValueError as exc:
        raise FailureInventoryError("JUnit suite tests count is malformed") from exc
    if declared_tests is None or declared_tests < counts["collected"]:
        raise FailureInventoryError(
            "JUnit suite tests count is smaller than testcase elements"
        )
    counts["suite_declared_tests"] = declared_tests
    counts["subtest_extra_declared_units"] = declared_tests - counts["collected"]
    classified_subtest_outcomes = sum(
        "::subtest[" in case.case_identity for case in cases
    )
    if counts["subtest_extra_declared_units"] < classified_subtest_outcomes:
        raise FailureInventoryError(
            "JUnit suite declares fewer subtest units than represented outcomes"
        )
    return (
        {
            "collected": counts["collected"],
            "suite_declared_tests": counts["suite_declared_tests"],
            "subtest_extra_declared_units": counts["subtest_extra_declared_units"],
            "multi_outcome_containers": counts["multi_outcome_containers"],
            "passed_or_xpassed_case_elements": counts["passed_case_elements"],
            "failed": counts["failure"],
            "errors": counts["error"],
            "skipped": counts["skipped"],
            "xfailed": counts["xfailed"],
        },
        tuple(sorted(cases, key=lambda row: row.case_identity)),
    )


def load_rules(path: str | Path) -> tuple[FailureRule, ...]:
    rules_path = Path(path)
    if rules_path.is_symlink() or not rules_path.is_file():
        raise FailureInventoryError("failure-rule registry is missing or non-regular")
    payload = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise FailureInventoryError("failure-rule registry must be a mapping")
    _strict_keys(
        payload,
        required={"schema_version", "buckets", "rules"},
        label="failure-rule registry",
    )
    if payload["schema_version"] != RULE_SCHEMA:
        raise FailureInventoryError("unsupported failure-rule schema")
    if tuple(payload["buckets"]) != FAILURE_BUCKETS:
        raise FailureInventoryError("failure bucket vocabulary drifted")
    raw_rules = payload["rules"]
    if not isinstance(raw_rules, Sequence) or isinstance(raw_rules, (str, bytes)):
        raise FailureInventoryError("failure rules must be a sequence")
    rules: list[FailureRule] = []
    rule_ids: set[str] = set()
    identity_owner: dict[str, str] = {}
    for index, raw in enumerate(raw_rules):
        if not isinstance(raw, Mapping):
            raise FailureInventoryError(f"failure rule {index} must be a mapping")
        _strict_keys(
            raw,
            required={
                "rule_id",
                "bucket",
                "case_identities",
                "outcomes",
                "evidence_sha256",
                "rationale",
            },
            label=f"failure rule {index}",
        )
        rule_id = _text(raw["rule_id"], "rule_id")
        if rule_id in rule_ids:
            raise FailureInventoryError(f"duplicate failure rule: {rule_id}")
        rule_ids.add(rule_id)
        bucket = _text(raw["bucket"], "bucket")
        if bucket not in FAILURE_BUCKETS or bucket == "UNKNOWN_UNCLASSIFIED":
            raise FailureInventoryError(f"failure rule {rule_id} has invalid bucket")
        _text(raw["rationale"], "rationale")
        case_identities = frozenset(
            _text_sequence(raw["case_identities"], "case_identities")
        )
        outcomes = frozenset(_text_sequence(raw["outcomes"], "outcomes"))
        evidence_sha256 = frozenset(
            _text_sequence(raw["evidence_sha256"], "evidence_sha256")
        )
        if len(outcomes) != 1 or not outcomes <= {
            "failure",
            "error",
            "skipped",
            "xfailed",
        }:
            raise FailureInventoryError(
                f"failure rule {rule_id} must bind one valid outcome"
            )
        if len(evidence_sha256) != 1 or any(
            re.fullmatch(r"[0-9a-f]{64}", digest) is None
            for digest in evidence_sha256
        ):
            raise FailureInventoryError(
                f"failure rule {rule_id} must bind one SHA-256 evidence identity"
            )
        for identity in case_identities:
            if "::" not in identity:
                raise FailureInventoryError(
                    f"failure rule {rule_id} has malformed case identity"
                )
            if identity in identity_owner:
                raise FailureInventoryError(
                    f"case identity occurs in multiple rules: {identity}"
                )
            identity_owner[identity] = rule_id
        rules.append(
            FailureRule(
                rule_id=rule_id,
                bucket=bucket,
                case_identities=case_identities,
                outcomes=outcomes,
                evidence_sha256=evidence_sha256,
            )
        )
    return tuple(rules)


def classify_cases(
    cases: Sequence[JunitNonPass], rules: Sequence[FailureRule]
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    used_rule_cases: set[tuple[str, str]] = set()
    for case in cases:
        matches = [rule for rule in rules if rule.matches(case)]
        if len(matches) != 1:
            state = "unclassified" if not matches else "ambiguous"
            raise FailureInventoryError(
                f"{case.case_identity} is {state}; matches={[row.rule_id for row in matches]}"
            )
        rule = matches[0]
        used_rule_cases.add((rule.rule_id, case.case_identity))
        rows.append(
            {
                "case_identity": case.case_identity,
                "outcome": case.outcome,
                "evidence_sha256": case.evidence_sha256,
                "evidence_excerpt": case.evidence_excerpt,
                "rule_id": rule.rule_id,
                "bucket": rule.bucket,
            }
        )
    registered_rule_cases = {
        (rule.rule_id, identity)
        for rule in rules
        for identity in rule.case_identities
    }
    unused = registered_rule_cases - used_rule_cases
    if unused:
        raise FailureInventoryError(
            f"failure rule case identities are stale or unused: {sorted(unused)}"
        )
    return tuple(rows)


def _git_identity(repo_root: Path, commit: str | None = None) -> tuple[str, str]:
    source = commit or subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if not _GIT_RE.fullmatch(source):
        raise FailureInventoryError("source commit is malformed")
    tree = subprocess.run(
        ["git", "rev-parse", f"{source}^{{tree}}"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if tree.returncode != 0 or not _GIT_RE.fullmatch(tree.stdout.strip()):
        raise FailureInventoryError("source commit/tree is unavailable")
    return source, tree.stdout.strip()


def _git_file_sha256(repo_root: Path, commit: str, relative_path: Path) -> str:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise FailureInventoryError("git-bound input path must be repository-relative")
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative_path.as_posix()}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise FailureInventoryError(
            f"classification commit lacks input: {relative_path.as_posix()}"
        )
    return _sha256_bytes(completed.stdout)


def _execution_environment() -> dict[str, object]:
    executable = Path(sys.executable).resolve()
    if executable.is_symlink() or not executable.is_file():
        raise FailureInventoryError("inventory interpreter is missing or non-regular")
    versions: dict[str, str] = {}
    for distribution in ("pytest", "numpy", "scipy"):
        try:
            versions[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            versions[distribution] = "not-installed"
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_executable": str(executable),
        "python_executable_sha256": _sha256_file(executable),
        "platform": platform.platform(),
        "distribution_versions": versions,
    }


def build_inventory_artifacts(
    repo_root: str | Path,
    *,
    junit_path: str | Path = DEFAULT_JUNIT,
    rules_path: str | Path = DEFAULT_RULES,
    classification_path: str | Path = DEFAULT_CLASSIFICATION,
    receipt_path: str | Path = DEFAULT_RECEIPT,
    source_commit: str | None = None,
    evidence_repo_root: str | Path | None = None,
    pytest_exit_code: int,
) -> tuple[Path, Path]:
    root = Path(repo_root).resolve()
    junit = root / Path(junit_path)
    rules_file = root / Path(rules_path)
    classification_file = root / Path(classification_path)
    receipt_file = root / Path(receipt_path)
    counts, cases = parse_junit(
        junit,
        evidence_repo_root=(root if evidence_repo_root is None else evidence_repo_root),
    )
    if pytest_exit_code not in {0, 1}:
        raise FailureInventoryError(
            "full inventory must terminate normally with pytest exit code 0 or 1"
        )
    expected_exit_code = 1 if counts["failed"] or counts["errors"] else 0
    if pytest_exit_code != expected_exit_code:
        raise FailureInventoryError("pytest exit code does not reconcile with JUnit")
    rules = load_rules(rules_file)
    classified = classify_cases(cases, rules)
    bucket_counts = Counter(str(row["bucket"]) for row in classified)
    for bucket in FAILURE_BUCKETS:
        bucket_counts[bucket] += 0
    classification: dict[str, object] = {
        "schema_version": CLASSIFICATION_SCHEMA,
        "evidence_canonicalization": EVIDENCE_CANONICALIZATION,
        "junit_sha256": _sha256_file(junit),
        "rules_sha256": _sha256_file(rules_file),
        "nonpass_count": len(classified),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "unknown_count": bucket_counts["UNKNOWN_UNCLASSIFIED"],
        "active_core_count": bucket_counts["ACTIVE_CORE_REGRESSION"],
        "cases": list(classified),
    }
    classification["content_sha256"] = _sha256_bytes(
        _canonical_bytes(classification)
    )
    classification_file.parent.mkdir(parents=True, exist_ok=True)
    classification_file.write_text(
        json.dumps(classification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    execution_commit, execution_tree = _git_identity(root, source_commit)
    classification_commit, classification_tree = _git_identity(root)
    manifest = root / DEFAULT_MANIFEST
    receipt: dict[str, object] = {
        "schema_version": RECEIPT_SCHEMA,
        "evidence_canonicalization": EVIDENCE_CANONICALIZATION,
        "execution_source_commit": execution_commit,
        "execution_source_tree": execution_tree,
        "classification_source_commit": classification_commit,
        "classification_source_tree": classification_tree,
        "command_argv": [
            "python",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-o",
            "addopts=",
            "--junitxml=artifacts/full_inventory.xml",
        ],
        "root_addopts_cleared": True,
        "cache_provider_disabled": True,
        "pytest_exit_code": pytest_exit_code,
        "execution_completed": True,
        "junit_count_observability": JUNIT_COUNT_OBSERVABILITY,
        "source_layout_environment": {
            "PYTHONPATH": "htt/src:htt:htt/htt",
            "PYTEST_ADDOPTS": "unset",
            "PYTEST_PLUGINS": "unset",
        },
        "execution_environment": _execution_environment(),
        "waiver_id": None,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "profile_manifest_sha256": _sha256_file(manifest),
        "classifier_sha256": _sha256_file(root / CLASSIFIER_PATH),
        "junit_sha256": _sha256_file(junit),
        "classification_sha256": _sha256_file(classification_file),
        "rules_sha256": _sha256_file(rules_file),
        "counts": counts,
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "unknown_count": bucket_counts["UNKNOWN_UNCLASSIFIED"],
        "active_core_count": bucket_counts["ACTIVE_CORE_REGRESSION"],
        "claim_ceiling": "diagnostic_only",
        "scientific_status": "OPEN_UNCHANGED",
    }
    receipt["content_sha256"] = _sha256_bytes(_canonical_bytes(receipt))
    receipt_file.parent.mkdir(parents=True, exist_ok=True)
    receipt_file.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return classification_file, receipt_file


def _load_json_mapping(path: Path, label: str) -> Mapping[str, object]:
    if path.is_symlink() or not path.is_file():
        raise FailureInventoryError(f"{label} is missing or non-regular")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise FailureInventoryError(f"{label} must be a JSON mapping")
    return value


def _verify_content_hash(payload: Mapping[str, object], label: str) -> None:
    unsigned = dict(payload)
    expected = _text(unsigned.pop("content_sha256"), f"{label} content_sha256")
    if _sha256_bytes(_canonical_bytes(unsigned)) != expected:
        raise FailureInventoryError(f"{label} content hash mismatch")


def validate_inventory_artifacts(
    repo_root: str | Path,
    *,
    require_closeout_acceptance: bool = True,
) -> Mapping[str, object]:
    root = Path(repo_root).resolve()
    rules_file = root / DEFAULT_RULES
    classification_file = root / DEFAULT_CLASSIFICATION
    receipt_file = root / DEFAULT_RECEIPT
    rules = load_rules(rules_file)
    classification = _load_json_mapping(classification_file, "classification")
    receipt = _load_json_mapping(receipt_file, "receipt")
    _strict_keys(
        classification,
        required={
            "schema_version",
            "evidence_canonicalization",
            "junit_sha256",
            "rules_sha256",
            "nonpass_count",
            "bucket_counts",
            "unknown_count",
            "active_core_count",
            "cases",
            "content_sha256",
        },
        label="classification",
    )
    _strict_keys(
        receipt,
        required={
            "schema_version",
            "evidence_canonicalization",
            "execution_source_commit",
            "execution_source_tree",
            "classification_source_commit",
            "classification_source_tree",
            "command_argv",
            "root_addopts_cleared",
            "cache_provider_disabled",
            "pytest_exit_code",
            "execution_completed",
            "junit_count_observability",
            "source_layout_environment",
            "execution_environment",
            "waiver_id",
            "generated_at",
            "profile_manifest_sha256",
            "classifier_sha256",
            "junit_sha256",
            "classification_sha256",
            "rules_sha256",
            "counts",
            "bucket_counts",
            "unknown_count",
            "active_core_count",
            "claim_ceiling",
            "scientific_status",
            "content_sha256",
        },
        label="receipt",
    )
    if classification.get("schema_version") != CLASSIFICATION_SCHEMA:
        raise FailureInventoryError("classification schema mismatch")
    if receipt.get("schema_version") != RECEIPT_SCHEMA:
        raise FailureInventoryError("receipt schema mismatch")
    if classification.get("evidence_canonicalization") != EVIDENCE_CANONICALIZATION:
        raise FailureInventoryError("classification evidence canonicalization drifted")
    if receipt.get("evidence_canonicalization") != EVIDENCE_CANONICALIZATION:
        raise FailureInventoryError("receipt evidence canonicalization drifted")
    _verify_content_hash(classification, "classification")
    _verify_content_hash(receipt, "receipt")
    if receipt.get("waiver_id") is not None:
        raise FailureInventoryError("full inventory cannot use a waiver")
    if receipt.get("root_addopts_cleared") is not True:
        raise FailureInventoryError("full inventory inherited root addopts")
    if receipt.get("cache_provider_disabled") is not True:
        raise FailureInventoryError("full inventory used pytest cache provider")
    if receipt.get("execution_completed") is not True:
        raise FailureInventoryError("full inventory execution is incomplete")
    if receipt.get("junit_count_observability") != JUNIT_COUNT_OBSERVABILITY:
        raise FailureInventoryError("JUnit count observability contract drifted")
    if receipt.get("claim_ceiling") != "diagnostic_only":
        raise FailureInventoryError("inventory claim ceiling drifted")
    if receipt.get("scientific_status") != "OPEN_UNCHANGED":
        raise FailureInventoryError("inventory changed scientific status")
    expected_command = [
        "python",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-o",
        "addopts=",
        "--junitxml=artifacts/full_inventory.xml",
    ]
    if receipt.get("command_argv") != expected_command:
        raise FailureInventoryError("full-inventory command drifted")
    if receipt.get("source_layout_environment") != {
        "PYTHONPATH": "htt/src:htt:htt/htt",
        "PYTEST_ADDOPTS": "unset",
        "PYTEST_PLUGINS": "unset",
    }:
        raise FailureInventoryError("full-inventory environment drifted")
    execution_environment = receipt.get("execution_environment")
    if not isinstance(execution_environment, Mapping):
        raise FailureInventoryError("execution environment must be a mapping")
    _strict_keys(
        execution_environment,
        required={
            "python_implementation",
            "python_version",
            "python_executable",
            "python_executable_sha256",
            "platform",
            "distribution_versions",
        },
        label="execution environment",
    )
    for field in (
        "python_implementation",
        "python_version",
        "python_executable",
        "platform",
    ):
        _text(execution_environment[field], f"execution environment {field}")
    executable_sha = _text(
        execution_environment["python_executable_sha256"],
        "execution environment python executable sha256",
    )
    if re.fullmatch(r"[0-9a-f]{64}", executable_sha) is None:
        raise FailureInventoryError("execution environment executable hash is malformed")
    versions = execution_environment["distribution_versions"]
    if not isinstance(versions, Mapping) or set(versions) != {"pytest", "numpy", "scipy"}:
        raise FailureInventoryError("execution distribution versions are malformed")
    for distribution, version in versions.items():
        _text(version, f"execution distribution {distribution}")
    generated_at = _text(receipt.get("generated_at"), "generated_at")
    try:
        parsed_generated_at = datetime.fromisoformat(generated_at)
    except ValueError as exc:
        raise FailureInventoryError("generated_at must be ISO-8601") from exc
    if parsed_generated_at.tzinfo is None:
        raise FailureInventoryError("generated_at must include a timezone")
    if receipt.get("classification_sha256") != _sha256_file(classification_file):
        raise FailureInventoryError("receipt/classification hash mismatch")
    if receipt.get("rules_sha256") != _sha256_file(rules_file):
        raise FailureInventoryError("receipt/rules hash mismatch")
    if classification.get("rules_sha256") != _sha256_file(rules_file):
        raise FailureInventoryError("classification/rules hash mismatch")
    if receipt.get("junit_sha256") != classification.get("junit_sha256"):
        raise FailureInventoryError("receipt/classification JUnit hash mismatch")
    if receipt.get("profile_manifest_sha256") != _sha256_file(root / DEFAULT_MANIFEST):
        raise FailureInventoryError("profile manifest hash mismatch")
    if receipt.get("classifier_sha256") != _sha256_file(root / CLASSIFIER_PATH):
        raise FailureInventoryError("classifier source hash mismatch")
    for field in ("unknown_count", "active_core_count", "nonpass_count"):
        value = classification.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise FailureInventoryError(f"classification {field} must be non-negative")
    execution_commit = _text(
        receipt.get("execution_source_commit"), "execution_source_commit"
    )
    execution_tree = _text(
        receipt.get("execution_source_tree"), "execution_source_tree"
    )
    classification_commit = _text(
        receipt.get("classification_source_commit"), "classification_source_commit"
    )
    classification_tree = _text(
        receipt.get("classification_source_tree"), "classification_source_tree"
    )
    if _git_identity(root, execution_commit)[1] != execution_tree:
        raise FailureInventoryError("receipt execution commit/tree mismatch")
    if _git_identity(root, classification_commit)[1] != classification_tree:
        raise FailureInventoryError("receipt classification commit/tree mismatch")
    for relative, expected in (
        (DEFAULT_RULES, receipt.get("rules_sha256")),
        (DEFAULT_MANIFEST, receipt.get("profile_manifest_sha256")),
        (CLASSIFIER_PATH, receipt.get("classifier_sha256")),
    ):
        if _git_file_sha256(root, classification_commit, relative) != expected:
            raise FailureInventoryError(
                f"classification input differs from bound commit: {relative.as_posix()}"
            )
    cases = classification.get("cases")
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)):
        raise FailureInventoryError("classification cases must be a sequence")
    identities: set[str] = set()
    used_rule_cases: set[tuple[str, str]] = set()
    bucket_counts: Counter[str] = Counter()
    rules_by_id = {rule.rule_id: rule for rule in rules}
    outcome_counts: Counter[str] = Counter()
    for row in cases:
        if not isinstance(row, Mapping):
            raise FailureInventoryError("classification case must be a mapping")
        _strict_keys(
            row,
            required={
                "case_identity",
                "outcome",
                "evidence_sha256",
                "evidence_excerpt",
                "rule_id",
                "bucket",
            },
            label="classification case",
        )
        identity = _text(row["case_identity"], "case_identity")
        if identity in identities:
            raise FailureInventoryError(f"duplicate classified case: {identity}")
        identities.add(identity)
        bucket = _text(row["bucket"], "bucket")
        if bucket not in FAILURE_BUCKETS or bucket == "UNKNOWN_UNCLASSIFIED":
            raise FailureInventoryError(f"invalid classified bucket: {bucket}")
        outcome = _text(row["outcome"], "outcome")
        if outcome not in {"failure", "error", "skipped", "xfailed"}:
            raise FailureInventoryError(f"invalid classified outcome: {outcome}")
        evidence_sha = _text(row["evidence_sha256"], "evidence_sha256")
        if re.fullmatch(r"[0-9a-f]{64}", evidence_sha) is None:
            raise FailureInventoryError("classified evidence hash is malformed")
        case = JunitNonPass(
            case_identity=identity,
            outcome=outcome,
            evidence_sha256=evidence_sha,
            evidence_excerpt=_text(row["evidence_excerpt"], "evidence_excerpt"),
        )
        matches = [rule for rule in rules if rule.matches(case)]
        rule_id = _text(row["rule_id"], "rule_id")
        if len(matches) != 1 or matches[0].rule_id != rule_id:
            raise FailureInventoryError(
                f"classified case does not resolve to its exact rule: {identity}"
            )
        if rule_id not in rules_by_id or rules_by_id[rule_id].bucket != bucket:
            raise FailureInventoryError(
                f"classified case bucket differs from its rule: {identity}"
            )
        used_rule_cases.add((rule_id, identity))
        bucket_counts[bucket] += 1
        outcome_counts[outcome] += 1
    registered_rule_cases = {
        (rule.rule_id, identity)
        for rule in rules
        for identity in rule.case_identities
    }
    unused_rule_cases = registered_rule_cases - used_rule_cases
    if unused_rule_cases:
        raise FailureInventoryError(
            "classification leaves stale or unused rule case identities: "
            f"{sorted(unused_rule_cases)}"
        )
    for bucket in FAILURE_BUCKETS:
        bucket_counts[bucket] += 0
    expected_bucket_counts = dict(sorted(bucket_counts.items()))
    for label, raw_counts in (
        ("classification", classification.get("bucket_counts")),
        ("receipt", receipt.get("bucket_counts")),
    ):
        if (
            not isinstance(raw_counts, Mapping)
            or set(raw_counts) != set(FAILURE_BUCKETS)
            or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 0
                for value in raw_counts.values()
            )
        ):
            raise FailureInventoryError(f"{label} bucket counts are malformed")
    if classification.get("bucket_counts") != expected_bucket_counts:
        raise FailureInventoryError("classification bucket counts mismatch")
    if receipt.get("bucket_counts") != expected_bucket_counts:
        raise FailureInventoryError("receipt bucket counts mismatch")
    derived_scalars = {
        "unknown_count": expected_bucket_counts["UNKNOWN_UNCLASSIFIED"],
        "active_core_count": expected_bucket_counts["ACTIVE_CORE_REGRESSION"],
    }
    for field, derived in derived_scalars.items():
        if classification.get(field) != derived:
            raise FailureInventoryError(
                f"classification {field} differs from derived bucket count"
            )
        if receipt.get(field) != derived:
            raise FailureInventoryError(
                f"receipt {field} differs from derived bucket count"
            )
    if derived_scalars["unknown_count"] != 0:
        raise FailureInventoryError("UNKNOWN_UNCLASSIFIED is nonzero")
    if require_closeout_acceptance and derived_scalars["active_core_count"] != 0:
        raise FailureInventoryError("ACTIVE_CORE_REGRESSION is nonzero")
    if receipt.get("unknown_count") != classification.get("unknown_count"):
        raise FailureInventoryError("receipt unknown count mismatch")
    if receipt.get("active_core_count") != classification.get("active_core_count"):
        raise FailureInventoryError("receipt active-core count mismatch")
    for field in ("unknown_count", "active_core_count"):
        value = receipt.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise FailureInventoryError(f"receipt {field} must be non-negative")
    if classification["nonpass_count"] != len(cases):
        raise FailureInventoryError("classification nonpass count mismatch")
    counts = receipt.get("counts")
    expected_count_fields = {
        "collected",
        "suite_declared_tests",
        "subtest_extra_declared_units",
        "multi_outcome_containers",
        "passed_or_xpassed_case_elements",
        "failed",
        "errors",
        "skipped",
        "xfailed",
    }
    if not isinstance(counts, Mapping) or set(counts) != expected_count_fields:
        raise FailureInventoryError("receipt count fields mismatch")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in counts.values()
    ):
        raise FailureInventoryError("receipt counts must be non-negative integers")
    if counts["failed"] != outcome_counts["failure"]:
        raise FailureInventoryError("receipt failed count mismatch")
    if counts["errors"] != outcome_counts["error"]:
        raise FailureInventoryError("receipt error count mismatch")
    if counts["skipped"] != outcome_counts["skipped"]:
        raise FailureInventoryError("receipt skipped count mismatch")
    if counts["xfailed"] != outcome_counts["xfailed"]:
        raise FailureInventoryError("receipt xfailed count mismatch")
    subtest_rows = [
        str(row["case_identity"])
        for row in cases
        if "::subtest[" in str(row["case_identity"])
    ]
    subtest_containers = {
        identity.rsplit("::subtest[", 1)[0] for identity in subtest_rows
    }
    single_terminal_case_count = len(cases) - len(subtest_rows)
    expected_collected = (
        counts["passed_or_xpassed_case_elements"]
        + single_terminal_case_count
        + len(subtest_containers)
    )
    if counts["collected"] != expected_collected:
        raise FailureInventoryError("receipt testcase-element count does not reconcile")
    if counts["multi_outcome_containers"] != len(subtest_containers):
        raise FailureInventoryError("receipt multi-outcome container count mismatch")
    if counts["suite_declared_tests"] != (
        counts["collected"] + counts["subtest_extra_declared_units"]
    ):
        raise FailureInventoryError("receipt suite-declared count does not reconcile")
    if counts["subtest_extra_declared_units"] < len(subtest_rows):
        raise FailureInventoryError("receipt undercounts represented subtest outcomes")
    expected_exit_code = 1 if counts["failed"] or counts["errors"] else 0
    if receipt.get("pytest_exit_code") != expected_exit_code:
        raise FailureInventoryError("receipt pytest exit code mismatch")
    if (root / DEFAULT_JUNIT).is_file():
        junit = root / DEFAULT_JUNIT
        if _sha256_file(junit) != receipt.get("junit_sha256"):
            raise FailureInventoryError("live JUnit bytes mismatch receipt")
        _, live_cases = parse_junit(junit, evidence_repo_root=root)
        rebuilt = classify_cases(live_cases, rules)
        if list(rebuilt) != list(cases):
            raise FailureInventoryError("live JUnit classification mismatch")
    return receipt


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--junit", type=Path, default=DEFAULT_JUNIT)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--classification", type=Path, default=DEFAULT_CLASSIFICATION)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--source-commit")
    parser.add_argument("--evidence-repo-root", type=Path)
    parser.add_argument("--pytest-exit-code", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            if args.pytest_exit_code is None:
                raise FailureInventoryError("build requires --pytest-exit-code")
            built = build_inventory_artifacts(
                args.repo_root,
                junit_path=args.junit,
                rules_path=args.rules,
                classification_path=args.classification,
                receipt_path=args.receipt,
                source_commit=args.source_commit,
                evidence_repo_root=args.evidence_repo_root,
                pytest_exit_code=args.pytest_exit_code,
            )
            for path in built:
                print(path)
        else:
            validate_inventory_artifacts(args.repo_root)
            print("PR-280 inventory artifacts valid")
        return 0
    except (FailureInventoryError, HarnessProfileError, OSError, json.JSONDecodeError) as exc:
        print(f"failure inventory error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "CLASSIFICATION_SCHEMA",
    "DEFAULT_CLASSIFICATION",
    "DEFAULT_JUNIT",
    "DEFAULT_RECEIPT",
    "DEFAULT_RULES",
    "EVIDENCE_CANONICALIZATION",
    "FailureInventoryError",
    "FailureRule",
    "JunitNonPass",
    "RECEIPT_SCHEMA",
    "RULE_SCHEMA",
    "build_inventory_artifacts",
    "classify_cases",
    "load_rules",
    "parse_junit",
    "validate_inventory_artifacts",
]
