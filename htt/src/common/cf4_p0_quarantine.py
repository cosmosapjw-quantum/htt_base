"""Fail-closed quarantine for the two open CF4 P0 result paths.

PR-120 blocks propagation of the refuted CF4 numerical headlines.  It does
not repair either estimator, select an audit sensitivity as replacement
truth, or advance any scientific finding beyond ``OPEN``.  The same typed,
content-addressed validator is shared by producer wrappers, publication
freeze, and package builders.
"""

from __future__ import annotations

import copy
from enum import Enum
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import yaml

try:  # Python 3.11+
    from enum import StrEnum
except ImportError:  # pragma: no cover - exercised by the Python 3.10 replay

    class StrEnum(str, Enum):
        """Minimal stdlib-compatible fallback for the declared Python floor."""

        def __str__(self) -> str:
            return str(self.value)


from .package_binary_binding import (
    BINARY_SUFFIXES,
    is_binary_path,
    verify_package_binary_binding,
)


POLICY_RELATIVE_PATH = Path(
    "docs/research_program/long_horizon_rescue/cf4_p0_quarantine_policy.yaml"
)
INVENTORY_RELATIVE_PATH = Path("docs/generated/cf4_p0_quarantine_inventory.json")
BLOCK_RELATIVE_PATH = Path("docs/generated/cf4_p0_quarantine_block.json")
POLICY_SCHEMA = "htt.cf4_p0_quarantine_policy.v1"
INVENTORY_SCHEMA = "htt.cf4_p0_quarantine_inventory.v1"
BLOCK_SCHEMA = "htt.cf4_p0_quarantine_block.v1"
REPORT_SCHEMA = "htt.cf4_p0_quarantine_report.v1"
_EXPECTED_FINDINGS = (
    "C1-K5-MV-F1",
    "C3-K5-VCORR-ML-F1",
    "N-DATA-CF4-DOWNSTREAM",
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_BINARY_PUBLIC_SUFFIXES = BINARY_SUFFIXES
_CONTEXT_RADIUS = 512
_ARTIFACT_KEY_VARIANTS: Mapping[str, tuple[frozenset[str], ...]] = {
    "result_card_block_record": (
        frozenset(
            {
                "active_path",
                "artifact_id",
                "artifact_kind",
                "legacy_public_use",
                "legacy_reproduction_only_path",
                "producer",
            }
        ),
    ),
    "derived_result_card_block_record": (
        frozenset(
            {
                "active_path",
                "artifact_id",
                "artifact_kind",
                "legacy_public_use",
                "legacy_reproduction_only_path",
                "producer",
            }
        ),
        frozenset(
            {
                "active_json",
                "active_markdown",
                "artifact_id",
                "artifact_kind",
                "legacy_public_use",
                "legacy_reproduction_only",
                "producer",
            }
        ),
    ),
    "figure_manifest_block_record": (
        frozenset(
            {
                "active_path",
                "active_png_status",
                "artifact_id",
                "artifact_kind",
                "legacy_public_use",
                "legacy_reproduction_only_root",
                "producer",
            }
        ),
        frozenset(
            {
                "active_png",
                "active_png_status",
                "artifact_id",
                "artifact_kind",
                "legacy_public_use",
                "legacy_reproduction_only_root",
                "producer",
            }
        ),
    ),
    "figure_source_block_record": (
        frozenset(
            {
                "active_path",
                "active_png_status",
                "artifact_id",
                "artifact_kind",
                "legacy_public_use",
                "legacy_reproduction_only_root",
                "producer",
            }
        ),
        frozenset(
            {
                "active_png",
                "active_png_status",
                "artifact_id",
                "artifact_kind",
                "legacy_public_use",
                "legacy_reproduction_only_root",
                "producer",
            }
        ),
    ),
    "conditioned_method_diagnostic_block_record": (
        frozenset(
            {
                "active_json",
                "active_markdown",
                "allowed_use",
                "artifact_id",
                "artifact_kind",
                "caveats",
                "claim_tier",
                "covariance_status",
                "forbidden_uses",
                "generating_command",
                "git_commit_or_worktree_state",
                "implementation_scope",
                "legacy_public_use",
                "legacy_reproduction_only",
                "legacy_script",
                "method_definition",
                "null_mock_status",
                "observational_numeric_instantiation",
                "owner",
                "producer",
                "sky_support_status",
                "transfer_source",
            }
        ),
    ),
}
_CONDITIONED_ALLOWED_USES = frozenset(
    {
        "likelihood_schema_and_coverage_test_design_only",
        "reconstruction_conditioned_method_and_systematics_design_only",
        "treatment_conditioned_pair_statistic_and_systematics_design_only",
    }
)
_PROMOTION_STRING_RE = re.compile(
    r"(?i)(?:\bRESCUED\b|\bVALIDATED\b|\bCLOSED\b|"
    r"Bianchi.{0,40}(?:family\s+identified|geometry\s+detected)|"
    r"family[_ -]?identification.{0,40}(?:evidence|supported|validated|true))"
)
_EXPECTED_DETERMINISTIC_RELEASE_OUTPUTS: Mapping[str, Mapping[str, str]] = {
    "docs/generated/external_audit_package.zip": {
        "builder_path": "scripts/build_external_audit_package.py",
        "manifest_path": "docs/generated/external_audit_package_manifest.json",
        "check_command": (
            "scripts/codex_harness/run_pr122_source_only.sh "
            "scripts/build_external_audit_package.py --check"
        ),
    },
    "docs/generated/research_only_external_audit_package.zip": {
        "builder_path": "scripts/build_research_only_audit_package.py",
        "manifest_path": (
            "docs/generated/research_only_external_audit_package_manifest.json"
        ),
        "check_command": (
            "venv/bin/python scripts/build_research_only_audit_package.py --check"
        ),
    },
    "docs/generated/statistical_formalism_audit_package.zip": {
        "builder_path": "scripts/build_statistical_formalism_audit_package.py",
        "manifest_path": (
            "docs/generated/statistical_formalism_audit_package_manifest.json"
        ),
        "check_command": (
            "venv/bin/python scripts/build_statistical_formalism_audit_package.py --check"
        ),
    },
    "htt_base_research_evaluation_package.zip": {
        "builder_path": "scripts/build_research_evaluation_package.py",
        "manifest_path": "htt_base_research_evaluation_package_manifest.json",
        "check_command": (
            "venv/bin/python scripts/build_research_evaluation_package.py --check"
        ),
    },
}

_EXPECTED_CF4_P0_ACTIVE_ABSENT_PATHS: tuple[str, ...] = (
    "figures/parallel_track/fig_02_tilted_flrw_dictionary.png",
    "figures/parallel_track/fig_03_colin_beta_translation.png",
    "figures/parallel_track/fig_04_flrw_tilt_posterior.png",
    "figures/parallel_track/fig_10_cf4_beta_variants.png",
    "figures/conditioned_legacy/parallel-track__fig_02_tilted_flrw_dictionary.png",
    "figures/conditioned_legacy/parallel-track__fig_02_tilted_flrw_dictionary.manifest.json",
    "figures/conditioned_legacy/parallel-track__fig_03_colin_beta_translation.png",
    "figures/conditioned_legacy/parallel-track__fig_03_colin_beta_translation.manifest.json",
    "figures/conditioned_legacy/parallel-track__fig_04_flrw_tilt_posterior.png",
    "figures/conditioned_legacy/parallel-track__fig_04_flrw_tilt_posterior.manifest.json",
    "figures/conditioned_legacy/parallel-track__fig_10_cf4_beta_variants.png",
    "figures/conditioned_legacy/parallel-track__fig_10_cf4_beta_variants.manifest.json",
)


class CF4P0QuarantineError(ValueError):
    """Base error for a malformed or violated quarantine contract."""


class CF4P0PolicyError(CF4P0QuarantineError):
    """Raised when the policy or authoritative OPEN roots drift."""


class CF4P0QuarantineViolation(CF4P0QuarantineError):
    """Raised when active/public content carries a stale result."""


class LegacyReproductionRequired(CF4P0QuarantineViolation):
    """Raised unless a pinned legacy reproduction is explicitly requested."""


class ContentMode(StrEnum):
    """Typed package-entry semantics; bare payloads are always active/public."""

    ACTIVE_PUBLIC = "active_public"
    IMMUTABLE_HISTORICAL_EVIDENCE = "immutable_historical_evidence"
    GOVERNANCE_CONTROL = "governance_control"


@dataclass(frozen=True)
class QuarantineContent:
    """One content-addressed package payload with an explicit non-science mode."""

    content: str | bytes
    mode: ContentMode
    source_path: str
    source_sha256: str

    def __post_init__(self) -> None:
        try:
            mode = ContentMode(self.mode)
        except ValueError as exc:
            raise CF4P0PolicyError(
                f"unknown package content mode {self.mode!r}"
            ) from exc
        object.__setattr__(self, "mode", mode)
        object.__setattr__(
            self,
            "source_path",
            _normal_relative_path(self.source_path, "package content source_path"),
        )
        object.__setattr__(
            self,
            "source_sha256",
            _require_sha256(self.source_sha256, "package content source_sha256"),
        )


@dataclass(frozen=True)
class ReviewedActiveBinaryPinSnapshot:
    """One validated, build-local view of reviewed active-binary pins.

    The snapshot deliberately has no module-global cache. Package builders may
    reuse it only within one payload construction and must recheck the policy
    byte hash before returning the rows that consumed it.
    """

    policy_sha256: str
    pins: Mapping[str, tuple[str, str]]


@dataclass(frozen=True)
class QuarantineIssue:
    """One fail-closed repository or payload finding."""

    path: str
    code: str
    detail: str
    signature_id: str | None = None
    finding_ids: tuple[str, ...] = ()
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "code": self.code,
            "detail": self.detail,
            "signature_id": self.signature_id,
            "finding_ids": list(self.finding_ids),
            "line": self.line,
        }


@dataclass(frozen=True)
class QuarantineReport:
    """Serializable result shared by repository and release-package gates."""

    policy_sha256: str
    inventory_sha256: str | None
    block_sha256: str | None
    scanned_paths: tuple[str, ...]
    issues: tuple[QuarantineIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": REPORT_SCHEMA,
            "ok": self.ok,
            "policy_sha256": self.policy_sha256,
            "inventory_sha256": self.inventory_sha256,
            "block_sha256": self.block_sha256,
            "scanned_path_count": len(self.scanned_paths),
            "scanned_paths": list(self.scanned_paths),
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class CF4P0BlockRecord:
    """Validated canonical blocked-source payload."""

    payload: Mapping[str, Any]
    sha256: str

    @property
    def status(self) -> str:
        return str(self.payload["status"])

    @property
    def findings(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self.payload["findings"])

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(dict(self.payload))


def repository_root() -> Path:
    """Return the repository root from this installed source layout."""

    return Path(__file__).resolve().parents[3]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _require_sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise CF4P0PolicyError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _require_prefixed_sha256(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith("sha256:")
        or not _SHA256_RE.fullmatch(value.removeprefix("sha256:"))
    ):
        raise CF4P0PolicyError(f"{field} must be sha256:<64 lowercase hex>")
    return value


def _normal_relative_path(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CF4P0PolicyError(f"{field} must be a non-empty repository path")
    candidate = value.replace("\\", "/")
    pure = PurePosixPath(candidate)
    if pure.is_absolute() or ".." in pure.parts or candidate != pure.as_posix():
        raise CF4P0PolicyError(f"{field} must be a normalized relative path")
    return candidate


def _repo_relative(path: Path, root: Path, field: str = "path") -> str:
    root_absolute = Path(os.path.abspath(root))
    candidate = path if path.is_absolute() else root_absolute / path
    candidate_absolute = Path(os.path.abspath(candidate))
    try:
        relative = candidate_absolute.relative_to(root_absolute)
    except ValueError as exc:
        raise CF4P0PolicyError(f"{field} escapes the repository root") from exc
    return _normal_relative_path(relative.as_posix(), field)


def _assert_regular_nonsymlink(
    root: Path,
    relative: str,
    *,
    label: str,
) -> Path:
    """Require every repository-path component to be non-symlink and regular."""

    normalized = _normal_relative_path(relative, label)
    current = Path(os.path.abspath(root))
    for index, part in enumerate(PurePosixPath(normalized).parts):
        current = current / part
        try:
            info = current.lstat()
        except (FileNotFoundError, OSError) as exc:
            raise CF4P0PolicyError(f"{label} is missing: {normalized}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise CF4P0PolicyError(
                f"{label} cannot contain a symlink component: {normalized}"
            )
        if index < len(PurePosixPath(normalized).parts) - 1:
            if not stat.S_ISDIR(info.st_mode):
                raise CF4P0PolicyError(
                    f"{label} parent is not a directory: {normalized}"
                )
        elif not stat.S_ISREG(info.st_mode):
            raise CF4P0PolicyError(f"{label} must be a regular file: {normalized}")
    return current


def _assert_directory_nonsymlink(
    root: Path,
    relative: str,
    *,
    label: str,
) -> Path:
    """Require every component of one repository directory to be non-symlink."""

    normalized = _normal_relative_path(relative, label)
    if normalized == ".":
        return Path(os.path.abspath(root))
    current = Path(os.path.abspath(root))
    for part in PurePosixPath(normalized).parts:
        current = current / part
        try:
            info = current.lstat()
        except (FileNotFoundError, OSError) as exc:
            raise CF4P0PolicyError(f"{label} is missing: {normalized}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise CF4P0PolicyError(
                f"{label} cannot contain a symlink component: {normalized}"
            )
        if not stat.S_ISDIR(info.st_mode):
            raise CF4P0PolicyError(f"{label} must be a directory: {normalized}")
    return current


def _assert_path_absent_nonsymlink(
    root: Path,
    relative: str,
    *,
    label: str,
) -> None:
    """Require an exact path to be absent without trusting symlink parents."""

    normalized = _normal_relative_path(relative, label)
    current = Path(os.path.abspath(root))
    parts = PurePosixPath(normalized).parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            return
        except OSError as exc:
            raise CF4P0PolicyError(
                f"cannot inspect required-absent path {normalized}: {exc}"
            ) from exc
        if stat.S_ISLNK(info.st_mode):
            raise CF4P0PolicyError(
                f"{label} cannot contain a symlink component: {normalized}"
            )
        if index < len(parts) - 1:
            if not stat.S_ISDIR(info.st_mode):
                raise CF4P0PolicyError(
                    f"{label} parent is not a directory: {normalized}"
                )
            continue
        raise CF4P0PolicyError(f"{label} must remain absent: {normalized}")


def _read_regular_bytes(root: Path, relative: str, *, label: str) -> bytes:
    path = _assert_regular_nonsymlink(root, relative, label=label)
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CF4P0PolicyError(f"cannot read {label} {relative}: {exc}") from exc


def _read_regular_text(root: Path, relative: str, *, label: str) -> str:
    raw = _read_regular_bytes(root, relative, label=label)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CF4P0PolicyError(f"{label} is not UTF-8: {relative}") from exc


def _read_absolute_regular_bytes(path: Path, *, label: str) -> bytes:
    """Read an explicit absolute test/policy path without following any symlink."""

    absolute = Path(os.path.abspath(path))
    if not absolute.is_absolute():  # pragma: no cover - guarded by abspath
        raise CF4P0PolicyError(f"{label} must be absolute")
    current = Path(absolute.anchor)
    for index, part in enumerate(absolute.parts[1:]):
        current = current / part
        try:
            info = current.lstat()
        except (FileNotFoundError, OSError) as exc:
            raise CF4P0PolicyError(f"{label} is missing: {absolute}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise CF4P0PolicyError(
                f"{label} cannot contain a symlink component: {absolute}"
            )
        if index < len(absolute.parts[1:]) - 1:
            if not stat.S_ISDIR(info.st_mode):
                raise CF4P0PolicyError(f"{label} parent is not a directory: {absolute}")
        elif not stat.S_ISREG(info.st_mode):
            raise CF4P0PolicyError(f"{label} must be a regular file: {absolute}")
    try:
        return absolute.read_bytes()
    except OSError as exc:
        raise CF4P0PolicyError(f"cannot read {label} {absolute}: {exc}") from exc


def load_policy(
    repo_root: Path | str | None = None,
    *,
    policy_path: Path | str | None = None,
) -> tuple[Mapping[str, Any], str]:
    """Load and structurally validate the canonical quarantine policy."""

    root = Path(repo_root or repository_root()).resolve()
    path = Path(policy_path) if policy_path is not None else root / POLICY_RELATIVE_PATH
    if not path.is_absolute():
        path = root / path
    raw_policy = _read_absolute_regular_bytes(path, label="CF4 P0 quarantine policy")
    try:
        payload = yaml.safe_load(raw_policy.decode("utf-8"))
    except (UnicodeError, yaml.YAMLError) as exc:
        raise CF4P0PolicyError(f"cannot parse CF4 P0 quarantine policy: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise CF4P0PolicyError("CF4 P0 quarantine policy must contain a mapping")
    if payload.get("schema") != POLICY_SCHEMA:
        raise CF4P0PolicyError(f"policy schema must be {POLICY_SCHEMA!r}")
    if payload.get("implementation_scope") != "propagation_quarantine_only":
        raise CF4P0PolicyError("policy cannot claim estimator remediation")
    if payload.get("claim_tier") != "blocked":
        raise CF4P0PolicyError("CF4 P0 policy claim_tier must remain blocked")

    claim_level = payload.get("claim_level")
    if claim_level != {"scheme": "roadmap_rescue_v1", "level": "C1"}:
        raise CF4P0PolicyError("policy claim level must be roadmap_rescue_v1:C1")

    root_state = payload.get("root_state")
    if not isinstance(root_state, Mapping):
        raise CF4P0PolicyError("policy root_state must be a mapping")
    _require_sha256(root_state.get("sha256"), "root_state.sha256")
    findings = root_state.get("required_open_findings")
    if not isinstance(findings, Sequence) or isinstance(findings, (str, bytes)):
        raise CF4P0PolicyError("required_open_findings must be a sequence")
    ids = []
    for index, record in enumerate(findings):
        if not isinstance(record, Mapping):
            raise CF4P0PolicyError(f"required_open_findings[{index}] must be a mapping")
        finding_id = str(record.get("finding_id", ""))
        ids.append(finding_id)
        _require_sha256(
            record.get("source_sha256"),
            f"required_open_findings[{index}].source_sha256",
        )
    if tuple(ids) != _EXPECTED_FINDINGS:
        raise CF4P0PolicyError(
            f"policy findings must be exactly {list(_EXPECTED_FINDINGS)!r}"
        )

    scan = payload.get("scan")
    if not isinstance(scan, Mapping):
        raise CF4P0PolicyError("policy scan must be a mapping")
    roots = scan.get("roots")
    if roots != ["."]:
        raise CF4P0PolicyError(
            "scan.roots must be exactly ['.'] so root, src, dl_pipeline, prompts, "
            "configs, and reports cannot escape the active scan"
        )
    typed_top_level = scan.get("typed_historical_top_level_roots", ())
    if not isinstance(typed_top_level, Sequence) or isinstance(
        typed_top_level, (str, bytes)
    ):
        raise CF4P0PolicyError(
            "scan.typed_historical_top_level_roots must be a sequence"
        )
    normalized_typed_top_level = {
        _normal_relative_path(value, "scan.typed_historical_top_level_roots")
        for value in typed_top_level
    }
    if normalized_typed_top_level != {"legacy"} or len(typed_top_level) != 1:
        raise CF4P0PolicyError(
            "legacy is the only permitted typed historical top-level root"
        )
    for field in (
        "immutable_historical_paths",
        "generated_contract_paths",
        "mutation_corpus_paths",
        "support_paths",
    ):
        values = scan.get(field, ())
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise CF4P0PolicyError(f"scan.{field} must be a sequence")
        normalized_values = [
            _normal_relative_path(value, f"scan.{field}") for value in values
        ]
        if len(normalized_values) != len(set(normalized_values)):
            raise CF4P0PolicyError(f"scan.{field} contains duplicate paths")
        for relative in normalized_values:
            _assert_regular_nonsymlink(
                root,
                relative,
                label=f"scan.{field} entry",
            )
    historical_prefixes = scan.get("immutable_historical_prefixes", ())
    if not isinstance(historical_prefixes, Sequence) or isinstance(
        historical_prefixes, (str, bytes)
    ):
        raise CF4P0PolicyError("scan.immutable_historical_prefixes must be a sequence")
    normalized_prefixes: list[str] = []
    for value in historical_prefixes:
        if not isinstance(value, str) or not value.endswith("/"):
            raise CF4P0PolicyError(
                "immutable historical prefixes must declare a directory boundary"
            )
        normalized = _normal_relative_path(
            value.rstrip("/"), "scan.immutable_historical_prefixes"
        )
        if (
            len(PurePosixPath(normalized).parts) < 2
            and normalized not in normalized_typed_top_level
        ):
            raise CF4P0PolicyError(
                "immutable historical prefixes cannot exempt a broad active "
                "top-level root"
            )
        _assert_directory_nonsymlink(
            root,
            normalized,
            label="immutable historical prefix",
        )
        normalized_prefixes.append(normalized)
    if len(normalized_prefixes) != len(set(normalized_prefixes)):
        raise CF4P0PolicyError(
            "scan.immutable_historical_prefixes contains duplicate paths"
        )

    package_modes = payload.get("package_content_modes")
    if not isinstance(package_modes, Mapping):
        raise CF4P0PolicyError("package_content_modes must be a mapping")
    governance_paths = package_modes.get("governance_control_paths")
    if not isinstance(governance_paths, Sequence) or isinstance(
        governance_paths, (str, bytes)
    ):
        raise CF4P0PolicyError(
            "package_content_modes.governance_control_paths must be a sequence"
        )
    normalized_governance = [
        _normal_relative_path(value, "package_content_modes.governance_control_paths")
        for value in governance_paths
    ]
    if len(normalized_governance) != len(set(normalized_governance)):
        raise CF4P0PolicyError("governance control paths must be unique")
    rules = payload.get("stale_signatures")
    if not isinstance(rules, Sequence) or isinstance(rules, (str, bytes)):
        raise CF4P0PolicyError("stale_signatures must be a sequence")
    seen_rule_ids: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, Mapping):
            raise CF4P0PolicyError(f"stale_signatures[{index}] must be a mapping")
        rule_id = str(rule.get("id", ""))
        if not rule_id or rule_id in seen_rule_ids:
            raise CF4P0PolicyError("stale signature IDs must be unique and non-empty")
        seen_rule_ids.add(rule_id)
        finding_ids = tuple(str(value) for value in rule.get("finding_ids", ()))
        if not finding_ids or not set(finding_ids).issubset(_EXPECTED_FINDINGS):
            raise CF4P0PolicyError(
                f"stale signature {rule_id!r} has invalid finding IDs"
            )
        try:
            re.compile(str(rule["token_regex"]))
            re.compile(str(rule["context_regex"]))
        except (KeyError, re.error) as exc:
            raise CF4P0PolicyError(
                f"stale signature {rule_id!r} has invalid regex: {exc}"
            ) from exc

    inventory = payload.get("inventory")
    if not isinstance(inventory, Mapping):
        raise CF4P0PolicyError("policy inventory must be a mapping")
    required_absent = inventory.get("required_absent_active_paths")
    if required_absent != list(_EXPECTED_CF4_P0_ACTIVE_ABSENT_PATHS):
        raise CF4P0PolicyError(
            "inventory.required_absent_active_paths must be the exact frozen "
            "CF4 P0 figure and conditioned-manifest set"
        )
    for relative in required_absent:
        _assert_path_absent_nonsymlink(
            root,
            relative,
            label="required-absent active CF4 P0 path",
        )
    reviewed_sidecars = inventory.get("reviewed_active_binary_sidecars")
    if not isinstance(reviewed_sidecars, Mapping):
        raise CF4P0PolicyError(
            "inventory.reviewed_active_binary_sidecars must be a mapping"
        )
    for raw_binary_path, raw_record in reviewed_sidecars.items():
        binary_path = _normal_relative_path(
            raw_binary_path, "reviewed active binary path"
        )
        if not is_binary_path(binary_path):
            raise CF4P0PolicyError(
                f"reviewed active binary path has no gated binary suffix: {binary_path}"
            )
        if not isinstance(raw_record, Mapping) or set(raw_record) != {
            "sidecar_path",
            "sidecar_sha256",
            "artifact_sha256",
            "review_scope",
        }:
            raise CF4P0PolicyError(
                "each reviewed active binary record must contain exactly "
                "sidecar_path, sidecar_sha256, artifact_sha256, and review_scope"
            )
        sidecar_path = _normal_relative_path(
            raw_record["sidecar_path"],
            f"reviewed sidecar for {binary_path}",
        )
        if sidecar_path == binary_path:
            raise CF4P0PolicyError(
                f"reviewed sidecar must be distinct from binary: {binary_path}"
            )
        if _is_repository_exception(binary_path, payload):
            raise CF4P0PolicyError(
                f"reviewed sidecar pins are active/public only: {binary_path}"
            )
        sidecar_sha256 = _require_prefixed_sha256(
            raw_record["sidecar_sha256"],
            f"reviewed sidecar SHA-256 for {binary_path}",
        )
        artifact_sha256 = _require_prefixed_sha256(
            raw_record["artifact_sha256"],
            f"reviewed artifact SHA-256 for {binary_path}",
        )
        if raw_record["review_scope"] != "PR-120-reviewed-active-binary":
            raise CF4P0PolicyError(
                f"reviewed active binary {binary_path} has an invalid review_scope"
            )
        binary_bytes = _read_regular_bytes(
            root, binary_path, label="reviewed active binary"
        )
        sidecar_bytes = _read_regular_bytes(
            root, sidecar_path, label="reviewed active binary sidecar"
        )
        if "sha256:" + _sha256_bytes(binary_bytes) != artifact_sha256:
            raise CF4P0PolicyError(
                f"reviewed active binary artifact pin is stale: {binary_path}"
            )
        if "sha256:" + _sha256_bytes(sidecar_bytes) != sidecar_sha256:
            raise CF4P0PolicyError(
                f"reviewed active binary sidecar pin is stale: {sidecar_path}"
            )
        try:
            sidecar_payload = json.loads(sidecar_bytes)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise CF4P0PolicyError(
                f"reviewed active binary sidecar is invalid JSON: {sidecar_path}"
            ) from exc
        if not isinstance(sidecar_payload, Mapping):
            raise CF4P0PolicyError(
                f"reviewed active binary sidecar must be an object: {sidecar_path}"
            )
        nested_manifest = sidecar_payload.get("manifest")
        binding_payload = (
            nested_manifest if isinstance(nested_manifest, Mapping) else sidecar_payload
        )
        if binding_payload.get("artifact_path") != binary_path:
            raise CF4P0PolicyError(
                f"reviewed active binary sidecar path binding drifted: {sidecar_path}"
            )
        if str(binding_payload.get("artifact_sha256", "")).lower() != artifact_sha256:
            raise CF4P0PolicyError(
                f"reviewed active binary sidecar artifact digest drifted: {sidecar_path}"
            )
    deterministic_outputs = inventory.get("deterministic_release_outputs")
    if deterministic_outputs != _EXPECTED_DETERMINISTIC_RELEASE_OUTPUTS:
        raise CF4P0PolicyError(
            "inventory.deterministic_release_outputs must be the exact four "
            "self-containing release archives and their canonical closeout gates"
        )
    if set(reviewed_sidecars).intersection(deterministic_outputs):
        raise CF4P0PolicyError(
            "deterministic release outputs cannot use reviewed sidecar pins"
        )
    for output_path, record in deterministic_outputs.items():
        output_path = _normal_relative_path(
            output_path, "deterministic release output path"
        )
        if not is_binary_path(output_path):
            raise CF4P0PolicyError(
                f"deterministic release output must be a binary archive: {output_path}"
            )
        _assert_regular_nonsymlink(
            root, output_path, label="deterministic release output"
        )
        builder_path = _normal_relative_path(
            record["builder_path"], "deterministic release builder path"
        )
        manifest_path = _normal_relative_path(
            record["manifest_path"], "deterministic release manifest path"
        )
        _assert_regular_nonsymlink(
            root, builder_path, label="deterministic release builder"
        )
        manifest_bytes = _read_regular_bytes(
            root, manifest_path, label="deterministic release manifest"
        )
        try:
            manifest = json.loads(manifest_bytes)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise CF4P0PolicyError(
                f"deterministic release manifest is invalid: {manifest_path}: {exc}"
            ) from exc
        if (
            not isinstance(manifest, Mapping)
            or manifest.get("artifact_path") != output_path
        ):
            raise CF4P0PolicyError(
                f"deterministic release manifest does not name {output_path}"
            )
    pinned = inventory.get("pinned_paths")
    if not isinstance(pinned, Sequence) or isinstance(pinned, (str, bytes)):
        raise CF4P0PolicyError("inventory.pinned_paths must be a sequence")
    seen_paths: set[str] = set()
    active_consumer_paths: set[str] = set()
    for index, record in enumerate(pinned):
        if not isinstance(record, Mapping):
            raise CF4P0PolicyError(f"pinned_paths[{index}] must be a mapping")
        normalized = _normal_relative_path(record.get("path"), f"pinned_paths[{index}]")
        if normalized in seen_paths:
            raise CF4P0PolicyError(f"duplicate pinned path {normalized!r}")
        seen_paths.add(normalized)
        role = record.get("role")
        mode = record.get("mode")
        if not isinstance(role, str) or not role.strip():
            raise CF4P0PolicyError(f"pinned_paths[{index}] requires a role")
        if mode not in {
            "active_block_consumer",
            "validator_support",
            "mutation_corpus_only",
        }:
            raise CF4P0PolicyError(
                f"pinned_paths[{index}] has unsupported mode {mode!r}"
            )
        markers = record.get("required_markers", ())
        if not isinstance(markers, Sequence) or isinstance(markers, (str, bytes)):
            raise CF4P0PolicyError(
                f"pinned_paths[{index}].required_markers must be a sequence"
            )
        _assert_regular_nonsymlink(root, normalized, label="pinned inventory path")
        if mode == "active_block_consumer":
            active_consumer_paths.add(normalized)
    missing_release_builders = sorted(
        {str(record["builder_path"]) for record in deterministic_outputs.values()}
        - active_consumer_paths
    )
    if missing_release_builders:
        raise CF4P0PolicyError(
            "every deterministic release builder must be a pinned "
            f"active_block_consumer; missing={missing_release_builders!r}"
        )

    lineage_edges = inventory.get("lineage_edges")
    if not isinstance(lineage_edges, Sequence) or isinstance(
        lineage_edges, (str, bytes)
    ):
        raise CF4P0PolicyError("inventory.lineage_edges must be a sequence")
    seen_edge_ids: set[str] = set()
    covered_consumers: set[str] = set()
    for index, edge in enumerate(lineage_edges):
        if not isinstance(edge, Mapping):
            raise CF4P0PolicyError(f"lineage_edges[{index}] must be a mapping")
        edge_id = str(edge.get("edge_id", ""))
        if not edge_id or edge_id in seen_edge_ids:
            raise CF4P0PolicyError("lineage edge IDs must be unique and non-empty")
        seen_edge_ids.add(edge_id)
        endpoints = [
            _normal_relative_path(
                edge.get("from_path"), f"lineage_edges[{index}].from_path"
            )
        ]
        to_paths = edge.get("to_paths")
        if not isinstance(to_paths, Sequence) or isinstance(to_paths, (str, bytes)):
            raise CF4P0PolicyError(
                f"lineage_edges[{index}].to_paths must be a sequence"
            )
        endpoints.extend(
            _normal_relative_path(value, f"lineage_edges[{index}].to_paths")
            for value in to_paths
        )
        if len(endpoints) < 2 or len(endpoints[1:]) != len(set(endpoints[1:])):
            raise CF4P0PolicyError(
                f"lineage_edges[{index}] needs unique downstream paths"
            )
        for endpoint in endpoints:
            _assert_regular_nonsymlink(root, endpoint, label="lineage edge endpoint")
        covered_consumers.update(endpoints[1:])
        finding_ids = tuple(str(value) for value in edge.get("finding_ids", ()))
        if not finding_ids or not set(finding_ids).issubset(_EXPECTED_FINDINGS):
            raise CF4P0PolicyError(f"lineage edge {edge_id!r} has invalid finding IDs")
        if not str(edge.get("disposition", "")).strip():
            raise CF4P0PolicyError(f"lineage edge {edge_id!r} requires a disposition")

    missing_lineage = sorted(active_consumer_paths - covered_consumers)
    if missing_lineage:
        raise CF4P0PolicyError(
            "every active_block_consumer must be a downstream lineage endpoint; "
            f"missing={missing_lineage!r}"
        )

    return payload, _sha256_bytes(raw_policy)


def _validate_open_roots(
    root: Path, policy: Mapping[str, Any]
) -> tuple[Mapping[str, Any], str]:
    root_policy = policy["root_state"]
    canonical_rel = _normal_relative_path(
        root_policy["canonical_path"], "root_state.canonical_path"
    )
    mirror_rel = _normal_relative_path(
        root_policy["mirror_path"], "root_state.mirror_path"
    )
    canonical = root / canonical_rel
    mirror = root / mirror_rel
    expected_hash = _require_sha256(root_policy["sha256"], "root_state.sha256")
    canonical_bytes = _read_regular_bytes(
        root, canonical_rel, label="canonical remediation root"
    )
    mirror_bytes = _read_regular_bytes(
        root, mirror_rel, label="mirror remediation root"
    )
    if canonical_bytes != mirror_bytes:
        raise CF4P0PolicyError("remediation root mirror is not byte-identical")
    actual_hash = _sha256_bytes(canonical_bytes)
    if actual_hash != expected_hash:
        raise CF4P0PolicyError(
            f"remediation root hash drift: expected {expected_hash}, got {actual_hash}"
        )
    try:
        root_payload = yaml.safe_load(canonical_bytes.decode("utf-8"))
    except (UnicodeError, yaml.YAMLError) as exc:
        raise CF4P0PolicyError(f"cannot parse remediation root: {exc}") from exc
    if not isinstance(root_payload, Mapping):
        raise CF4P0PolicyError("remediation root must contain a mapping")
    census = root_payload.get("census")
    if not isinstance(census, Mapping):
        raise CF4P0PolicyError("remediation root census must be a mapping")
    if census.get("finding_count") != root_policy.get("finding_count"):
        raise CF4P0PolicyError("remediation finding count drifted")
    if census.get("rescued_count") != 0 or root_policy.get("rescued_count") != 0:
        raise CF4P0PolicyError("PR-120 requires zero RESCUED findings")
    if census.get("scientific_status_counts") != {
        "OPEN": root_policy.get("finding_count")
    }:
        raise CF4P0PolicyError("PR-120 requires the exact all-OPEN census")

    rows = root_payload.get("findings")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise CF4P0PolicyError("remediation root findings must be a sequence")
    by_id = {
        str(row.get("finding_id")): row for row in rows if isinstance(row, Mapping)
    }
    for required in root_policy["required_open_findings"]:
        finding_id = required["finding_id"]
        row = by_id.get(finding_id)
        if row is None:
            raise CF4P0PolicyError(f"missing authoritative finding {finding_id}")
        expected = {
            "scientific_status": "OPEN",
            "severity": required["severity"],
            "authoritative_source_state": required["authoritative_source_state"],
            "source_reference": required["source_reference"],
            "source_hash": f"sha256:{required['source_sha256']}",
            "claim_tier_ceiling": "blocked",
        }
        for field, value in expected.items():
            if row.get(field) != value:
                raise CF4P0PolicyError(
                    f"authoritative finding {finding_id} has {field}={row.get(field)!r}; "
                    f"expected {value!r}"
                )
        if row.get("execution_resolution") is not None:
            raise CF4P0PolicyError(
                f"authoritative finding {finding_id} unexpectedly has terminal resolution"
            )
    return root_payload, actual_hash


def _path_is_under(relative: str, prefixes: Sequence[str]) -> bool:
    pure = PurePosixPath(relative)
    for prefix in prefixes:
        normalized = _normal_relative_path(prefix, "path prefix")
        parent = PurePosixPath(normalized)
        if pure == parent or parent in pure.parents:
            return True
    return False


def _inventory_entry(
    root: Path,
    *,
    relative: str,
    role: str,
    mode: str,
    required_markers: Sequence[str] = (),
) -> Mapping[str, Any]:
    relative = _normal_relative_path(relative, "inventory entry path")
    path = _assert_regular_nonsymlink(root, relative, label="inventory entry")
    raw = _read_regular_bytes(root, relative, label="inventory entry")
    if required_markers:
        try:
            text = raw.decode("utf-8")
        except UnicodeError as exc:
            raise CF4P0PolicyError(
                f"cannot inspect required markers for {relative}: {exc}"
            ) from exc
        missing = [marker for marker in required_markers if marker not in text]
        if missing:
            raise CF4P0PolicyError(
                f"inventory entry {relative} lacks required markers {missing!r}"
            )
    return {
        "path": relative,
        "role": role,
        "mode": mode,
        "sha256": _sha256_bytes(raw),
        "size_bytes": len(raw),
        "public_use": mode == "active_block_consumer",
        "required_markers": list(required_markers),
    }


def _repository_candidate_paths(root: Path) -> tuple[str, ...]:
    """Enumerate tracked and non-ignored untracked paths from the repository root."""

    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise CF4P0PolicyError(
            f"cannot enumerate repository paths with Git: {exc}"
        ) from exc
    if completed.returncode != 0:
        raise CF4P0PolicyError(
            "exhaustive CF4 quarantine scan requires a readable Git worktree"
        )
    result: set[str] = set()
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            relative = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CF4P0PolicyError("repository contains a non-UTF-8 path") from exc
        result.add(_normal_relative_path(relative, "repository path"))
    return tuple(sorted(result))


def _active_binary_paths(root: Path, policy: Mapping[str, Any]) -> tuple[str, ...]:
    """Return every active/public binary outside typed historical lanes."""

    result: list[str] = []
    for relative in _repository_candidate_paths(root):
        # A symlink can never gain a historical or suffix-based exemption.
        _assert_regular_nonsymlink(root, relative, label="repository binary candidate")
        if _is_repository_exception(relative, policy):
            continue
        if is_binary_path(relative):
            result.append(relative)
    return tuple(result)


def _binary_inventory_entry(
    root: Path,
    relative: str,
    policy: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate an active binary without embedding self-referential output bytes."""

    deterministic = policy["inventory"]["deterministic_release_outputs"].get(relative)
    if isinstance(deterministic, Mapping):
        return {
            "path": relative,
            "role": "deterministic_release_output",
            "mode": "deterministic_release_output",
            "public_use": True,
            "required_markers": [],
            "builder_path": str(deterministic["builder_path"]),
            "manifest_path": str(deterministic["manifest_path"]),
            "check_command": str(deterministic["check_command"]),
            "byte_validation": "mandatory_deterministic_builder_check_at_closeout",
            "digest_exclusion_reason": "archive_embeds_canonical_inventory",
        }

    reviewed = policy["inventory"]["reviewed_active_binary_sidecars"].get(relative)
    explicit_manifest_path = None
    explicit_manifest_sha256 = None
    if isinstance(reviewed, Mapping):
        explicit_manifest_path = str(reviewed["sidecar_path"])
        explicit_manifest_sha256 = str(reviewed["sidecar_sha256"])
    try:
        binding = verify_package_binary_binding(
            root,
            relative,
            content_mode="active_public",
            explicit_manifest_path=explicit_manifest_path,
            explicit_manifest_sha256=explicit_manifest_sha256,
        )
    except (OSError, ValueError) as exc:
        raise CF4P0PolicyError(
            f"active/public binary lacks a valid independent binding: {relative}: {exc}"
        ) from exc
    if not isinstance(binding, Mapping):
        raise CF4P0PolicyError(
            f"active/public binary was not recognized by the binding gate: {relative}"
        )
    method = str(binding.get("method", ""))
    trusted_source = str(binding.get("trusted_source", ""))
    if not method or not trusted_source:
        raise CF4P0PolicyError(
            f"active/public binary binding metadata is incomplete: {relative}"
        )
    if isinstance(reviewed, Mapping):
        expected_authority = (
            f"reviewed-pin:{reviewed['sidecar_path']}@{reviewed['sidecar_sha256']}"
        )
        if trusted_source != expected_authority:
            raise CF4P0PolicyError(
                f"reviewed active binary pin is unused or mismatched: {relative}"
            )
    # Do not place the binary digest in this canonical inventory. Release ZIPs
    # can contain the inventory itself, so doing so would create an impossible
    # hash fixed point. The canonical path set and trust route are enumerated;
    # current bytes are revalidated by the independent binding gate on every run.
    entry = {
        "path": relative,
        "role": "active_public_binary",
        "mode": "active_public_binary",
        "public_use": True,
        "required_markers": [],
        "binding_gate": (
            "htt/src/common/package_binary_binding.py:verify_package_binary_binding"
        ),
        "binding_method": method,
        "trusted_source": trusted_source,
        "byte_validation": "dynamic_fail_closed_no_self_reference",
    }
    if isinstance(reviewed, Mapping):
        entry["reviewed_sidecar_path"] = str(reviewed["sidecar_path"])
        entry["reviewed_sidecar_sha256"] = str(reviewed["sidecar_sha256"])
        entry["reviewed_artifact_sha256"] = str(reviewed["artifact_sha256"])
        entry["review_scope"] = str(reviewed["review_scope"])
    return entry


def _walk_regular_tree(root: Path, relative_root: str) -> tuple[str, ...]:
    """Walk one typed tree without following or silently omitting symlinks."""

    normalized_root = _normal_relative_path(relative_root, "tree root")
    start = _assert_directory_nonsymlink(root, normalized_root, label="tree root")
    pending = [start]
    result: list[str] = []
    while pending:
        directory = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda value: value.name)
        except OSError as exc:
            raise CF4P0PolicyError(
                f"cannot enumerate tree {normalized_root}: {exc}"
            ) from exc
        for entry in entries:
            path = Path(entry.path)
            relative = _repo_relative(path, root, "tree entry")
            try:
                info = path.lstat()
            except OSError as exc:
                raise CF4P0PolicyError(
                    f"cannot inspect tree entry {relative}: {exc}"
                ) from exc
            if stat.S_ISLNK(info.st_mode):
                raise CF4P0PolicyError(
                    f"tree entry cannot be a symlink component: {relative}"
                )
            if stat.S_ISDIR(info.st_mode):
                pending.append(path)
            elif stat.S_ISREG(info.st_mode):
                result.append(relative)
            else:
                raise CF4P0PolicyError(
                    f"tree entry must be a regular file or directory: {relative}"
                )
    return tuple(sorted(result))


def build_inventory_payload(
    repo_root: Path | str | None = None,
    *,
    policy_path: Path | str | None = None,
) -> Mapping[str, Any]:
    """Build the deterministic hash-bound producer/consumer inventory."""

    root = Path(repo_root or repository_root()).resolve()
    policy, policy_hash = load_policy(root, policy_path=policy_path)
    _, root_hash = _validate_open_roots(root, policy)
    entries: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for record in policy["inventory"]["pinned_paths"]:
        relative = _normal_relative_path(record["path"], "pinned path")
        entries.append(
            _inventory_entry(
                root,
                relative=relative,
                role=str(record["role"]),
                mode=str(record["mode"]),
                required_markers=tuple(
                    str(v) for v in record.get("required_markers", ())
                ),
            )
        )
        seen.add(relative)

    for legacy_root in policy["legacy_output_roots"]:
        legacy_relative = _normal_relative_path(legacy_root, "legacy output root")
        for relative in _walk_regular_tree(root, legacy_relative):
            if relative in seen:
                continue
            entries.append(
                _inventory_entry(
                    root,
                    relative=relative,
                    role="frozen_numerical_reproduction",
                    mode="legacy_reproduction_only",
                )
            )
            seen.add(relative)

    for relative in _active_binary_paths(root, policy):
        if relative in seen:
            continue
        entries.append(_binary_inventory_entry(root, relative, policy))
        seen.add(relative)

    entries.sort(key=lambda value: str(value["path"]))
    lineage_edges = copy.deepcopy(policy["inventory"]["lineage_edges"])
    return {
        "schema": INVENTORY_SCHEMA,
        "owner": policy["owner"],
        "implementation_scope": policy["implementation_scope"],
        "claim_tier": policy["claim_tier"],
        "claim_level": policy["claim_level"],
        "transfer_source": policy["transfer_source"],
        "config_hash": policy_hash,
        "policy_path": POLICY_RELATIVE_PATH.as_posix(),
        "policy_sha256": policy_hash,
        "remediation_root_sha256": root_hash,
        "input_hashes": [
            f"{POLICY_RELATIVE_PATH.as_posix()}:sha256:{policy_hash}",
            f"{policy['root_state']['canonical_path']}:sha256:{root_hash}",
        ],
        "entries": entries,
        "entry_count": len(entries),
        "legacy_entry_count": sum(
            entry["mode"] == "legacy_reproduction_only" for entry in entries
        ),
        "active_block_consumer_count": sum(
            entry["mode"] == "active_block_consumer" for entry in entries
        ),
        "active_public_binary_count": sum(
            entry["mode"] == "active_public_binary" for entry in entries
        ),
        "deterministic_release_output_count": sum(
            entry["mode"] == "deterministic_release_output" for entry in entries
        ),
        "lineage_edges": lineage_edges,
        "lineage_edge_count": len(lineage_edges),
        "stale_signature_ids": [rule["id"] for rule in policy["stale_signatures"]],
        "sky_support_status": "not_applicable_to_propagation_quarantine",
        "null_mock_status": "not_applicable_quarantine_is_not_validation",
        "caveats": list(policy["caveats"]),
        "generating_command": (
            "PYTHONPATH=htt/src venv/bin/python -B "
            "scripts/codex_harness/quarantine_cf4_p0_consumers.py --write"
        ),
        "git_commit_or_worktree_state": (
            f"baseline_commit:{policy['baseline_commit']}; "
            "PR-120 worktree hashes are bound per inventory entry"
        ),
    }


def _build_block_payload(
    policy: Mapping[str, Any],
    *,
    policy_hash: str,
    inventory_hash: str,
    root_hash: str,
) -> Mapping[str, Any]:
    findings = []
    for record in policy["root_state"]["required_open_findings"]:
        findings.append(
            {
                "finding_id": record["finding_id"],
                "severity": record["severity"],
                "scientific_status": "OPEN",
                "claim_tier_ceiling": "blocked",
                "source_reference": record["source_reference"],
                "source_sha256": record["source_sha256"],
            }
        )
    return {
        "schema": BLOCK_SCHEMA,
        "status": "QUARANTINED_OPEN_FINDINGS",
        "owner": policy["owner"],
        "implementation_scope": policy["implementation_scope"],
        "claim_tier": policy["claim_tier"],
        "claim_level": policy["claim_level"],
        "transfer_source": policy["transfer_source"],
        "config_hash": policy_hash,
        "scientific_effect": "none",
        "findings": findings,
        "replacement_value": None,
        "replacement_policy": "forbidden_without_later_authenticated_adjudication",
        "public_use": True,
        "allowed_use": "blocked_source_record_only",
        "policy_path": POLICY_RELATIVE_PATH.as_posix(),
        "policy_sha256": policy_hash,
        "inventory_path": INVENTORY_RELATIVE_PATH.as_posix(),
        "inventory_sha256": inventory_hash,
        "remediation_root_path": policy["root_state"]["canonical_path"],
        "remediation_root_sha256": root_hash,
        "sky_support_status": "not_applicable_to_propagation_quarantine",
        "null_mock_status": "not_applicable_quarantine_is_not_validation",
        "input_hashes": [
            f"{POLICY_RELATIVE_PATH.as_posix()}:sha256:{policy_hash}",
            f"{INVENTORY_RELATIVE_PATH.as_posix()}:sha256:{inventory_hash}",
            f"{policy['root_state']['canonical_path']}:sha256:{root_hash}",
        ],
        "caveats": list(policy["caveats"]),
        "generating_command": (
            "PYTHONPATH=htt/src venv/bin/python -B "
            "scripts/codex_harness/quarantine_cf4_p0_consumers.py --write"
        ),
        "git_commit_or_worktree_state": (
            f"baseline_commit:{policy['baseline_commit']}; "
            "PR-120 worktree hashes are bound by the canonical inventory"
        ),
    }


def build_canonical_payloads(
    repo_root: Path | str | None = None,
    *,
    policy_path: Path | str | None = None,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    """Return deterministic inventory and block payloads without writing."""

    root = Path(repo_root or repository_root()).resolve()
    policy, policy_hash = load_policy(root, policy_path=policy_path)
    _, root_hash = _validate_open_roots(root, policy)
    inventory = build_inventory_payload(root, policy_path=policy_path)
    inventory_hash = _sha256_bytes(_canonical_json_bytes(inventory))
    block = _build_block_payload(
        policy,
        policy_hash=policy_hash,
        inventory_hash=inventory_hash,
        root_hash=root_hash,
    )
    return inventory, block


def render_inventory_markdown(payload: Mapping[str, Any]) -> str:
    """Render a deterministic review surface for the canonical inventory."""

    lines = [
        "# CF4 P0 quarantine consumer inventory",
        "",
        "This is a propagation-control artifact. It does not remediate or validate a CF4 result.",
        "",
        f"- Owner: `{payload['owner']}`",
        f"- Implementation scope: `{payload['implementation_scope']}`",
        f"- Claim tier: `{payload['claim_tier']}`",
        f"- Transfer source: `{payload['transfer_source']}`",
        f"- Config hash: `{payload['config_hash']}`",
        f"- Policy SHA-256: `{payload['policy_sha256']}`",
        f"- Remediation-root SHA-256: `{payload['remediation_root_sha256']}`",
        f"- Sky support: `{payload['sky_support_status']}`",
        f"- Null/mock status: `{payload['null_mock_status']}`",
        f"- Git/worktree state: `{payload['git_commit_or_worktree_state']}`",
        f"- Entries: `{payload['entry_count']}`",
        f"- Legacy-only entries: `{payload['legacy_entry_count']}`",
        f"- Dynamically bound active/public binaries: `{payload['active_public_binary_count']}`",
        f"- Deterministic release outputs: `{payload['deterministic_release_output_count']}`",
        f"- Producer/consumer lineage edges: `{payload['lineage_edge_count']}`",
        "",
        "| Path | Role | Mode | SHA-256 | Public use |",
        "|---|---|---|---|---|",
    ]
    for entry in payload["entries"]:
        if entry["mode"] == "deterministic_release_output":
            digest = "deterministic:mandatory_builder_--check"
        else:
            digest = entry.get(
                "sha256",
                f"dynamic:{entry.get('binding_method', 'fail_closed_gate')}",
            )
        lines.append(
            f"| `{entry['path']}` | `{entry['role']}` | `{entry['mode']}` | "
            f"`{digest}` | `{str(entry['public_use']).lower()}` |"
        )
    lines.extend(["", "## Producer/consumer lineage", ""])
    lines.extend(
        (
            f"- `{edge['edge_id']}`: `{edge['from_path']}` -> "
            + ", ".join(f"`{path}`" for path in edge["to_paths"])
            + f" (`{edge['disposition']}`)"
        )
        for edge in payload["lineage_edges"]
    )
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {value}" for value in payload["caveats"])
    lines.extend(["", "## Input hashes", ""])
    lines.extend(f"- `{value}`" for value in payload["input_hashes"])
    lines.extend(["", f"Generating command: `{payload['generating_command']}`", ""])
    return "\n".join(lines)


def render_block_markdown(payload: Mapping[str, Any]) -> str:
    """Render the canonical no-number blocked source record."""

    lines = [
        "# CF4 P0 blocked source record",
        "",
        "No CF4 numerical replacement is authorized. This record blocks propagation only.",
        "",
        f"- Status: `{payload['status']}`",
        f"- Owner: `{payload['owner']}`",
        f"- Implementation scope: `{payload['implementation_scope']}`",
        f"- Claim tier: `{payload['claim_tier']}`",
        f"- Transfer source: `{payload['transfer_source']}`",
        f"- Config hash: `{payload['config_hash']}`",
        f"- Inventory SHA-256: `{payload['inventory_sha256']}`",
        f"- Remediation-root SHA-256: `{payload['remediation_root_sha256']}`",
        f"- Sky support: `{payload['sky_support_status']}`",
        f"- Null/mock status: `{payload['null_mock_status']}`",
        f"- Git/worktree state: `{payload['git_commit_or_worktree_state']}`",
        "",
        "| Finding | Severity | Scientific status | Ceiling |",
        "|---|---|---|---|",
    ]
    for finding in payload["findings"]:
        lines.append(
            f"| `{finding['finding_id']}` | `{finding['severity']}` | "
            f"`{finding['scientific_status']}` | `{finding['claim_tier_ceiling']}` |"
        )
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {value}" for value in payload["caveats"])
    lines.extend(["", "## Input hashes", ""])
    lines.extend(f"- `{value}`" for value in payload["input_hashes"])
    lines.extend(["", f"Generating command: `{payload['generating_command']}`", ""])
    return "\n".join(lines)


def canonical_artifact_bytes(
    repo_root: Path | str | None = None,
    *,
    policy_path: Path | str | None = None,
) -> Mapping[str, bytes]:
    """Return all four deterministic generated artifact byte streams."""

    inventory, block = build_canonical_payloads(repo_root, policy_path=policy_path)
    return {
        INVENTORY_RELATIVE_PATH.as_posix(): _canonical_json_bytes(inventory),
        "docs/generated/cf4_p0_quarantine_inventory.md": render_inventory_markdown(
            inventory
        ).encode("utf-8"),
        BLOCK_RELATIVE_PATH.as_posix(): _canonical_json_bytes(block),
        "docs/generated/cf4_p0_quarantine_block.md": render_block_markdown(
            block
        ).encode("utf-8"),
    }


def _load_json_mapping(
    root: Path, path: Path, label: str
) -> tuple[Mapping[str, Any], bytes]:
    relative = _repo_relative(path, root, label)
    try:
        raw = _read_regular_bytes(root, relative, label=label)
        payload = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CF4P0PolicyError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise CF4P0PolicyError(f"{label} must be a JSON object")
    return payload, raw


def _validate_inventory(
    root: Path, policy: Mapping[str, Any], policy_hash: str
) -> tuple[Mapping[str, Any], str]:
    path = root / INVENTORY_RELATIVE_PATH
    inventory, raw = _load_json_mapping(root, path, "CF4 P0 inventory")
    if inventory.get("schema") != INVENTORY_SCHEMA:
        raise CF4P0PolicyError(f"inventory schema must be {INVENTORY_SCHEMA!r}")
    if inventory.get("policy_sha256") != policy_hash:
        raise CF4P0PolicyError("inventory policy hash is stale")
    expected = build_inventory_payload(root)
    expected_bytes = _canonical_json_bytes(expected)
    if raw != expected_bytes:
        raise CF4P0PolicyError(
            "inventory is stale or non-canonical; regenerate with the PR-120 CLI"
        )
    return inventory, _sha256_bytes(raw)


def load_block_record(
    repo_root: Path | str | None = None,
) -> CF4P0BlockRecord:
    """Load and validate the canonical block record and every bound hash."""

    root = Path(repo_root or repository_root()).resolve()
    policy, policy_hash = load_policy(root)
    _, root_hash = _validate_open_roots(root, policy)
    inventory, inventory_hash = _validate_inventory(root, policy, policy_hash)
    path = root / BLOCK_RELATIVE_PATH
    payload, raw = _load_json_mapping(root, path, "CF4 P0 block record")
    if payload.get("schema") != BLOCK_SCHEMA:
        raise CF4P0PolicyError(f"block schema must be {BLOCK_SCHEMA!r}")
    expected = _build_block_payload(
        policy,
        policy_hash=policy_hash,
        inventory_hash=inventory_hash,
        root_hash=root_hash,
    )
    if raw != _canonical_json_bytes(expected):
        raise CF4P0PolicyError("block record is stale or non-canonical")
    if payload.get("replacement_value") is not None:
        raise CF4P0PolicyError(
            "canonical block record cannot carry a replacement value"
        )
    if payload.get("status") != "QUARANTINED_OPEN_FINDINGS":
        raise CF4P0PolicyError(
            "canonical block record must retain OPEN quarantine status"
        )
    if (
        tuple(row["finding_id"] for row in payload.get("findings", ()))
        != _EXPECTED_FINDINGS
    ):
        raise CF4P0PolicyError("canonical block record finding roots drifted")
    if inventory.get("remediation_root_sha256") != root_hash:
        raise CF4P0PolicyError("inventory remediation root binding drifted")
    return CF4P0BlockRecord(payload=payload, sha256=_sha256_bytes(raw))


def quarantine_block_payload(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Return a deep copy of the validated canonical block payload."""

    return load_block_record(repo_root).to_dict()


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _scan_text(
    path: str,
    text: str,
    rules: Sequence[Mapping[str, Any]],
) -> tuple[QuarantineIssue, ...]:
    issues: list[QuarantineIssue] = []
    seen: set[tuple[str, int]] = set()
    for rule in rules:
        token = re.compile(str(rule["token_regex"]))
        context_rule = re.compile(str(rule["context_regex"]))
        for match in token.finditer(text):
            # Policy contexts reach 420 characters.  Keep a margin around the
            # token so a producer cannot evade quarantine by padding the
            # survey/finding name away from the numerical payload.
            start = max(0, match.start() - _CONTEXT_RADIUS)
            end = min(len(text), match.end() + _CONTEXT_RADIUS)
            context = text[start:end]
            if context_rule.search(context) is None:
                continue
            line = _line_number(text, match.start())
            key = (str(rule["id"]), line)
            if key in seen:
                continue
            seen.add(key)
            excerpt = " ".join(match.group(0).split())[:120]
            issues.append(
                QuarantineIssue(
                    path=path,
                    code="stale_cf4_p0_consumer",
                    detail=(
                        f"matched contextual signature {rule['id']!r}: {excerpt!r}"
                    ),
                    signature_id=str(rule["id"]),
                    finding_ids=tuple(str(value) for value in rule["finding_ids"]),
                    line=line,
                )
            )
    return tuple(issues)


def _artifact_issue(path: str, code: str, detail: str) -> QuarantineIssue:
    return QuarantineIssue(
        path=path,
        code=code,
        detail=detail,
        finding_ids=_EXPECTED_FINDINGS,
    )


def _validate_no_artifact_promotion(
    path: str,
    value: object,
    *,
    key_path: tuple[str, ...] = (),
) -> tuple[QuarantineIssue, ...]:
    """Recursively reject scientific/public promotion hidden below ``artifact``."""

    issues: list[QuarantineIssue] = []
    if isinstance(value, Mapping):
        for raw_key, nested in value.items():
            key = str(raw_key)
            normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
            nested_path = (*key_path, normalized)
            dotted = ".".join(nested_path)
            if normalized == "scientific_status" and nested not in {
                "OPEN",
                "QUARANTINED_OPEN_P0",
                "BLOCKED",
            }:
                issues.append(
                    _artifact_issue(
                        path,
                        "embedded_quarantine_promotion",
                        f"artifact field {dotted} cannot promote scientific status",
                    )
                )
            if "replacement" in normalized and nested is not None:
                issues.append(
                    _artifact_issue(
                        path,
                        "embedded_quarantine_promotion",
                        f"artifact field {dotted} cannot carry a replacement",
                    )
                )
            if normalized.endswith("public_use") and nested is not False:
                issues.append(
                    _artifact_issue(
                        path,
                        "embedded_quarantine_promotion",
                        f"artifact field {dotted} must remain false",
                    )
                )
            if normalized == "claim_tier" and nested != "blocked":
                issues.append(
                    _artifact_issue(
                        path,
                        "embedded_quarantine_promotion",
                        f"artifact field {dotted} must remain blocked",
                    )
                )
            if (
                "forbidden_uses" not in key_path
                and "family" in normalized
                and ("identification" in normalized or "identified" in normalized)
            ):
                issues.append(
                    _artifact_issue(
                        path,
                        "embedded_quarantine_promotion",
                        f"artifact field {dotted} cannot carry family-identification evidence",
                    )
                )
            issues.extend(
                _validate_no_artifact_promotion(
                    path,
                    nested,
                    key_path=nested_path,
                )
            )
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, nested in enumerate(value):
            issues.extend(
                _validate_no_artifact_promotion(
                    path,
                    nested,
                    key_path=(*key_path, str(index)),
                )
            )
    elif isinstance(value, str) and "forbidden_uses" not in key_path:
        if _PROMOTION_STRING_RE.search(value):
            issues.append(
                _artifact_issue(
                    path,
                    "embedded_quarantine_promotion",
                    "artifact text cannot assert rescue, validation, or family identification",
                )
            )
    return tuple(issues)


def _validate_artifact_path_value(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise CF4P0PolicyError(f"artifact {field} must be a repository-relative path")
    return _normal_relative_path(value, f"artifact {field}")


def _validate_artifact_schema(
    path: str,
    artifact: Mapping[str, Any],
) -> tuple[QuarantineIssue, ...]:
    """Validate one of the finite, non-promoting block-artifact schemas."""

    issues: list[QuarantineIssue] = list(
        _validate_no_artifact_promotion(path, artifact)
    )
    kind = artifact.get("artifact_kind")
    variants = _ARTIFACT_KEY_VARIANTS.get(str(kind))
    if variants is None:
        issues.append(
            _artifact_issue(
                path,
                "invalid_embedded_quarantine_artifact_schema",
                f"unknown artifact_kind {kind!r}",
            )
        )
        return tuple(issues)
    actual_keys = frozenset(str(value) for value in artifact)
    if actual_keys not in variants:
        allowed = [sorted(value) for value in variants]
        issues.append(
            _artifact_issue(
                path,
                "invalid_embedded_quarantine_artifact_schema",
                f"artifact keys {sorted(actual_keys)!r} do not match allowed variants {allowed!r}",
            )
        )

    artifact_id = artifact.get("artifact_id")
    if (
        not isinstance(artifact_id, str)
        or re.fullmatch(r"[A-Za-z0-9_.-]+", artifact_id) is None
    ):
        issues.append(
            _artifact_issue(
                path,
                "invalid_embedded_quarantine_artifact_schema",
                "artifact_id must be a non-empty safe identifier",
            )
        )
    if artifact.get("legacy_public_use") is not False:
        issues.append(
            _artifact_issue(
                path,
                "legacy_public_use_not_false",
                "embedded block artifact must set legacy_public_use=false",
            )
        )

    path_fields = (
        "active_path",
        "active_json",
        "active_png",
        "producer",
        "legacy_reproduction_only_path",
        "legacy_reproduction_only_root",
        "legacy_script",
    )
    for field in path_fields:
        if field not in artifact:
            continue
        try:
            value = _validate_artifact_path_value(artifact[field], field=field)
        except CF4P0PolicyError as exc:
            issues.append(
                _artifact_issue(
                    path,
                    "invalid_embedded_quarantine_artifact_schema",
                    str(exc),
                )
            )
            continue
        if field.startswith("legacy_") and not _path_is_under(
            value, ("legacy/cf4_p0",)
        ):
            issues.append(
                _artifact_issue(
                    path,
                    "invalid_embedded_quarantine_artifact_schema",
                    f"artifact {field} must stay under legacy/cf4_p0",
                )
            )
        if field == "producer" and not value.startswith("scripts/"):
            issues.append(
                _artifact_issue(
                    path,
                    "invalid_embedded_quarantine_artifact_schema",
                    "artifact producer must name an active scripts/ path",
                )
            )
    for field in ("active_markdown",):
        if field in artifact and artifact[field] is not None:
            try:
                _validate_artifact_path_value(artifact[field], field=field)
            except CF4P0PolicyError as exc:
                issues.append(
                    _artifact_issue(
                        path,
                        "invalid_embedded_quarantine_artifact_schema",
                        str(exc),
                    )
                )
    legacy_many = artifact.get("legacy_reproduction_only")
    if legacy_many is not None:
        if (
            not isinstance(legacy_many, Sequence)
            or isinstance(legacy_many, (str, bytes))
            or not legacy_many
        ):
            issues.append(
                _artifact_issue(
                    path,
                    "invalid_embedded_quarantine_artifact_schema",
                    "legacy_reproduction_only must be a non-empty path list",
                )
            )
        else:
            for index, value in enumerate(legacy_many):
                try:
                    relative = _validate_artifact_path_value(
                        value, field=f"legacy_reproduction_only[{index}]"
                    )
                except CF4P0PolicyError as exc:
                    issues.append(
                        _artifact_issue(
                            path,
                            "invalid_embedded_quarantine_artifact_schema",
                            str(exc),
                        )
                    )
                    continue
                if not _path_is_under(relative, ("legacy/cf4_p0",)):
                    issues.append(
                        _artifact_issue(
                            path,
                            "invalid_embedded_quarantine_artifact_schema",
                            "legacy_reproduction_only paths must stay under legacy/cf4_p0",
                        )
                    )

    if (
        str(kind).startswith("figure_")
        and artifact.get("active_png_status") != "ABSENT_BY_QUARANTINE"
    ):
        issues.append(
            _artifact_issue(
                path,
                "invalid_embedded_quarantine_artifact_schema",
                "blocked figure artifact must keep active_png_status=ABSENT_BY_QUARANTINE",
            )
        )

    if kind == "conditioned_method_diagnostic_block_record":
        exact_values = {
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat_method_and_systematics_only",
            "claim_tier": "blocked",
            "transfer_source": "none",
            "sky_support_status": "not_evaluated_on_active_path",
            "covariance_status": "not_bound_on_active_path",
            "null_mock_status": "not_bound_on_active_path",
            "git_commit_or_worktree_state": "content-addressed_by_canonical_block",
        }
        for field, expected in exact_values.items():
            if artifact.get(field) != expected:
                issues.append(
                    _artifact_issue(
                        path,
                        "invalid_embedded_quarantine_artifact_schema",
                        f"conditioned artifact {field} must be {expected!r}",
                    )
                )
        if artifact.get("allowed_use") not in _CONDITIONED_ALLOWED_USES:
            issues.append(
                _artifact_issue(
                    path,
                    "invalid_embedded_quarantine_artifact_schema",
                    "conditioned artifact allowed_use is not an approved method-only lane",
                )
            )
        forbidden = artifact.get("forbidden_uses")
        if (
            not isinstance(forbidden, Sequence)
            or isinstance(forbidden, (str, bytes))
            or "family_identification" not in forbidden
            or not all(isinstance(value, str) for value in forbidden)
        ):
            issues.append(
                _artifact_issue(
                    path,
                    "invalid_embedded_quarantine_artifact_schema",
                    "conditioned artifact must explicitly forbid family_identification",
                )
            )
        for field in ("caveats", "method_definition"):
            values = artifact.get(field)
            if (
                not isinstance(values, Sequence)
                or isinstance(values, (str, bytes))
                or not values
                or not all(isinstance(value, str) and value.strip() for value in values)
            ):
                issues.append(
                    _artifact_issue(
                        path,
                        "invalid_embedded_quarantine_artifact_schema",
                        f"conditioned artifact {field} must be a non-empty text list",
                    )
                )
        instantiation = artifact.get("observational_numeric_instantiation")
        expected_instantiation = {
            "replacement_value": None,
            "status": "QUARANTINED_OPEN_P0",
            "values": None,
        }
        if instantiation != expected_instantiation:
            issues.append(
                _artifact_issue(
                    path,
                    "invalid_embedded_quarantine_artifact_schema",
                    "observational_numeric_instantiation must remain the exact "
                    "no-value quarantine record",
                )
            )
    return tuple(issues)


def _validate_embedded_block_record(
    path: str,
    text: str,
    canonical: Mapping[str, Any],
    *,
    require_path_match: bool,
) -> tuple[QuarantineIssue, ...]:
    """Reject stale/spoofed copies of the no-number canonical block payload."""

    if BLOCK_SCHEMA not in text:
        return ()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return ()
    if not isinstance(payload, Mapping) or payload.get("schema") != BLOCK_SCHEMA:
        return ()
    issues: list[QuarantineIssue] = []
    for field, expected in canonical.items():
        if payload.get(field) != expected:
            issues.append(
                QuarantineIssue(
                    path=path,
                    code="stale_embedded_quarantine_block",
                    detail=f"embedded block field {field!r} is not canonical",
                    finding_ids=_EXPECTED_FINDINGS,
                )
            )
            break
    unknown = set(payload) - set(canonical) - {"artifact"}
    if unknown:
        issues.append(
            QuarantineIssue(
                path=path,
                code="unknown_embedded_quarantine_fields",
                detail=f"unexpected top-level fields: {sorted(unknown)!r}",
                finding_ids=_EXPECTED_FINDINGS,
            )
        )
    artifact = payload.get("artifact")
    if artifact is not None:
        if not isinstance(artifact, Mapping):
            issues.append(
                QuarantineIssue(
                    path=path,
                    code="invalid_embedded_quarantine_artifact",
                    detail="artifact identity must be a mapping",
                    finding_ids=_EXPECTED_FINDINGS,
                )
            )
        else:
            issues.extend(_validate_artifact_schema(path, artifact))
            active_path = artifact.get("active_path")
            active_json = artifact.get("active_json")
            artifact_id = artifact.get("artifact_id")
            filename = PurePosixPath(path).name
            figure_stem = filename.removesuffix(".source.json").removesuffix(
                ".manifest.json"
            )
            path_matches = (
                active_path == path
                or active_json == path
                or (
                    str(artifact.get("artifact_kind", "")).startswith("figure_")
                    and artifact_id == figure_stem
                )
            )
            if require_path_match and not path_matches:
                issues.append(
                    QuarantineIssue(
                        path=path,
                        code="embedded_quarantine_path_mismatch",
                        detail=(
                            "artifact active path/JSON/figure identity does not match "
                            "repository path"
                        ),
                        finding_ids=_EXPECTED_FINDINGS,
                    )
                )
    return tuple(issues)


def _validate_active_text_with_policy(
    path: str,
    text: str | bytes,
    *,
    policy: Mapping[str, Any],
) -> tuple[QuarantineIssue, ...]:
    normalized = _normal_relative_path(path, "active payload path")
    if isinstance(text, bytes):
        try:
            decoded = text.decode("utf-8")
        except UnicodeDecodeError as exc:
            if PurePosixPath(normalized).suffix.lower() in _BINARY_PUBLIC_SUFFIXES:
                return ()
            return (
                QuarantineIssue(
                    path=normalized,
                    code="non_utf8_public_payload",
                    detail=f"public text payload is not UTF-8: {exc}",
                ),
            )
    elif isinstance(text, str):
        decoded = text
    else:
        raise TypeError("active payload must be str or bytes")
    return _scan_text(normalized, decoded, policy["stale_signatures"])


def validate_active_text(
    path: str,
    text: str | bytes,
    *,
    repo_root: Path | str | None = None,
) -> tuple[QuarantineIssue, ...]:
    """Scan one active/public payload without applying repository exceptions."""

    root = Path(repo_root or repository_root()).resolve()
    policy, _ = load_policy(root)
    return _validate_active_text_with_policy(path, text, policy=policy)


def _is_repository_exception(relative: str, policy: Mapping[str, Any]) -> bool:
    scan = policy["scan"]
    if relative in set(scan.get("immutable_historical_paths", ())):
        return True
    if relative in set(scan.get("generated_contract_paths", ())):
        return True
    if relative in set(scan.get("mutation_corpus_paths", ())):
        return True
    if relative in set(scan.get("support_paths", ())):
        return True
    if _path_is_under(relative, policy.get("legacy_output_roots", ())):
        return True
    return any(
        _matches_policy_prefix(relative, str(prefix))
        for prefix in scan.get("immutable_historical_prefixes", ())
    )


def _matches_policy_prefix(relative: str, prefix: str) -> bool:
    """Match a declared directory boundary, never a same-string spoof path."""

    candidate = prefix.replace("\\", "/").rstrip("/")
    normalized = _normal_relative_path(candidate, "historical path prefix")
    path = PurePosixPath(relative)
    parent = PurePosixPath(normalized)
    return path == parent or parent in path.parents


def _is_typed_non_science_source(
    relative: str,
    policy: Mapping[str, Any],
    mode: ContentMode,
) -> bool:
    """Accept only policy-enumerated immutable or governance source paths."""

    scan = policy["scan"]
    if mode is ContentMode.IMMUTABLE_HISTORICAL_EVIDENCE:
        exact = set(scan.get("immutable_historical_paths", ()))
        prefixes = tuple(
            str(value) for value in scan.get("immutable_historical_prefixes", ())
        )
        return (
            relative in exact
            or any(_matches_policy_prefix(relative, prefix) for prefix in prefixes)
            or _path_is_under(relative, policy.get("legacy_output_roots", ()))
        )
    if mode is ContentMode.GOVERNANCE_CONTROL:
        # Package authority is exact and intentionally independent of repository
        # scan exceptions: status/DAG inputs stay scanned on their live paths.
        return relative in set(
            policy["package_content_modes"]["governance_control_paths"]
        )
    return False


def repository_content(
    repo_root: Path | str | None,
    source_path: Path | str,
    *,
    mode: ContentMode | str,
) -> QuarantineContent:
    """Load one hash-bound repository entry for typed package validation."""

    root = Path(repo_root or repository_root()).resolve()
    source = Path(source_path)
    if not source.is_absolute():
        source = root / source
    relative = _repo_relative(source, root, "package content source path")
    content = _read_regular_bytes(root, relative, label="typed package source")
    return QuarantineContent(
        content=content,
        mode=ContentMode(mode),
        source_path=relative,
        source_sha256=_sha256_bytes(content),
    )


def read_regular_text(
    repo_root: Path | str,
    relative_path: Path | str,
    encoding: str = "utf-8",
) -> str:
    """Read repository text only through a component-safe regular-file path."""

    root = Path(repo_root).resolve()
    relative = _normal_relative_path(
        Path(relative_path).as_posix(), "regular text path"
    )
    raw = _read_regular_bytes(root, relative, label="regular text source")
    try:
        return raw.decode(encoding)
    except (LookupError, UnicodeError) as exc:
        raise CF4P0PolicyError(
            f"cannot decode regular text source {relative} as {encoding}: {exc}"
        ) from exc


def read_regular_bytes(
    repo_root: Path | str,
    relative_path: Path | str,
) -> bytes:
    """Read repository bytes only through a component-safe regular-file path."""

    root = Path(repo_root).resolve()
    relative = _normal_relative_path(
        Path(relative_path).as_posix(), "regular bytes path"
    )
    return _read_regular_bytes(root, relative, label="regular bytes source")


def atomic_write_text(
    repo_root: Path | str,
    relative_path: Path | str,
    text: str,
) -> None:
    """Atomically replace repository text without following any symlink.

    The destination parent must already exist and every component must be a
    real directory. Bytes are flushed and fsynced in a same-directory temporary
    file before ``os.replace``; an existing destination must be regular and may
    never be a final or broken symlink.
    """

    if not isinstance(text, str):
        raise TypeError("atomic text payload must be str")
    root = Path(repo_root).resolve()
    relative = _normal_relative_path(
        Path(relative_path).as_posix(), "atomic text destination"
    )
    relative_parent = PurePosixPath(relative).parent.as_posix()
    parent = _assert_directory_nonsymlink(
        root,
        relative_parent,
        label="atomic text destination parent",
    )
    target = parent / PurePosixPath(relative).name
    mode = 0o644
    if os.path.lexists(target):
        try:
            info = target.lstat()
        except OSError as exc:
            raise CF4P0PolicyError(
                f"cannot inspect atomic text destination {relative}: {exc}"
            ) from exc
        if stat.S_ISLNK(info.st_mode):
            raise CF4P0PolicyError(
                f"atomic text destination cannot be a symlink: {relative}"
            )
        if not stat.S_ISREG(info.st_mode):
            raise CF4P0PolicyError(
                f"atomic text destination must be a regular file: {relative}"
            )
        mode = stat.S_IMODE(info.st_mode)

    descriptor = -1
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=parent,
        )
        temporary_path = Path(temporary_name)
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(text.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, target)
        temporary_path = None
        directory_descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as exc:
        raise CF4P0PolicyError(
            f"cannot atomically write text destination {relative}: {exc}"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def reviewed_active_binary_sidecar_pin(
    repo_root: Path | str | None,
    source_path: Path | str,
) -> tuple[str, str] | None:
    """Return the policy-reviewed ``(sidecar_path, sidecar_sha256)`` if present.

    The policy loader has already component-checked both files and verified the
    sidecar and artifact digests. HEAD-identical or otherwise unused pins remain
    rejected by :func:`build_inventory_payload`, where the binary helper's
    returned trust authority is compared with this explicit pin.
    """

    root = Path(repo_root or repository_root()).resolve()
    source = Path(source_path)
    if not source.is_absolute():
        source = root / source
    relative = _repo_relative(source, root, "reviewed active binary source")
    policy, _ = load_policy(root)
    record = policy["inventory"]["reviewed_active_binary_sidecars"].get(relative)
    if not isinstance(record, Mapping):
        return None
    return str(record["sidecar_path"]), str(record["sidecar_sha256"])


def reviewed_active_binary_sidecar_pin_snapshot(
    repo_root: Path | str | None,
) -> ReviewedActiveBinaryPinSnapshot:
    """Load and validate all reviewed pins once for one package build."""

    root = Path(repo_root or repository_root()).resolve()
    policy, policy_sha256 = load_policy(root)
    records = policy["inventory"]["reviewed_active_binary_sidecars"]
    pins = {
        str(source_path): (
            str(record["sidecar_path"]),
            str(record["sidecar_sha256"]),
        )
        for source_path, record in records.items()
    }
    return ReviewedActiveBinaryPinSnapshot(
        policy_sha256=policy_sha256,
        pins=MappingProxyType(pins),
    )


def assert_reviewed_active_binary_pin_snapshot_current(
    repo_root: Path | str | None,
    snapshot: ReviewedActiveBinaryPinSnapshot,
) -> None:
    """Fail if canonical policy bytes changed while a build used ``snapshot``."""

    root = Path(repo_root or repository_root()).resolve()
    policy_bytes = _read_absolute_regular_bytes(
        root / POLICY_RELATIVE_PATH,
        label="CF4 P0 quarantine policy snapshot recheck",
    )
    current_sha256 = _sha256_bytes(policy_bytes)
    if current_sha256 != snapshot.policy_sha256:
        raise CF4P0PolicyError(
            "CF4 P0 quarantine policy changed during package construction: "
            f"expected {snapshot.policy_sha256}, got {current_sha256}"
        )


def _is_exact_generated_contract_payload(
    root: Path,
    content: str | bytes,
    policy: Mapping[str, Any],
) -> bool:
    """Recognize an exact canonical control copied into a package archive.

    The generated inventory necessarily contains signature identifiers and
    legacy filenames that would be stale science in an ordinary public result.
    It is safe only when the packaged bytes are identical to one of the exact
    generated-contract paths already exempted by policy.  Any byte mutation
    falls back to the ordinary active/public scan.
    """

    content_bytes = content.encode("utf-8") if isinstance(content, str) else content
    for relative in policy["scan"].get("generated_contract_paths", ()):
        try:
            source_bytes = _read_regular_bytes(
                root,
                str(relative),
                label="generated contract source",
            )
            if source_bytes == content_bytes:
                return True
        except CF4P0PolicyError:
            continue
    return False


def _active_repository_paths(root: Path, policy: Mapping[str, Any]) -> tuple[str, ...]:
    """Enumerate every candidate; exceptions apply only after component checks."""

    del policy  # The caller must not apply content exceptions before path safety.
    return _repository_candidate_paths(root)


def validate_repository(
    repo_root: Path | str | None = None,
    *,
    additional_contents: Mapping[str, str | bytes | QuarantineContent] | None = None,
) -> QuarantineReport:
    """Validate hashes, OPEN roots, repository consumers, and release payloads.

    Bare ``additional_contents`` values are always active/public. A caller may
    opt a repository file into ``immutable_historical_evidence`` or
    ``governance_control`` only by supplying :class:`QuarantineContent`; its
    source path and SHA-256 must match a policy-enumerated repository file.
    """

    root = Path(repo_root or repository_root()).resolve()
    issues: list[QuarantineIssue] = []
    scanned: list[str] = []
    inventory_hash: str | None = None
    block_hash: str | None = None
    block_record: CF4P0BlockRecord | None = None
    try:
        policy, policy_hash = load_policy(root)
    except CF4P0QuarantineError as exc:
        return QuarantineReport(
            policy_sha256="unavailable",
            inventory_sha256=None,
            block_sha256=None,
            scanned_paths=(),
            issues=(
                QuarantineIssue(
                    path=POLICY_RELATIVE_PATH.as_posix(),
                    code="invalid_quarantine_policy",
                    detail=str(exc),
                ),
            ),
        )

    try:
        _validate_open_roots(root, policy)
    except CF4P0QuarantineError as exc:
        issues.append(
            QuarantineIssue(
                path=str(policy["root_state"]["canonical_path"]),
                code="invalid_open_finding_root",
                detail=str(exc),
                finding_ids=_EXPECTED_FINDINGS,
            )
        )
    try:
        _, inventory_hash = _validate_inventory(root, policy, policy_hash)
    except CF4P0QuarantineError as exc:
        issues.append(
            QuarantineIssue(
                path=INVENTORY_RELATIVE_PATH.as_posix(),
                code="invalid_quarantine_inventory",
                detail=str(exc),
            )
        )
    try:
        block_record = load_block_record(root)
        block_hash = block_record.sha256
    except CF4P0QuarantineError as exc:
        issues.append(
            QuarantineIssue(
                path=BLOCK_RELATIVE_PATH.as_posix(),
                code="invalid_quarantine_block",
                detail=str(exc),
                finding_ids=_EXPECTED_FINDINGS,
            )
        )

    max_bytes = int(policy["scan"]["max_text_bytes"])
    for relative in _active_repository_paths(root, policy):
        try:
            path = _assert_regular_nonsymlink(
                root,
                relative,
                label="active repository path",
            )
            if _is_repository_exception(relative, policy):
                continue
            scanned.append(relative)
            if is_binary_path(relative):
                # Current bytes were independently authenticated while the
                # canonical inventory was rebuilt/validated above.
                continue
            size = path.lstat().st_size
            if size > max_bytes:
                issues.append(
                    QuarantineIssue(
                        path=relative,
                        code="active_text_too_large_to_scan",
                        detail=f"{size} bytes exceeds scan limit {max_bytes}",
                    )
                )
                continue
            raw = _read_regular_bytes(root, relative, label="active repository text")
            text = raw.decode("utf-8")
        except (CF4P0PolicyError, UnicodeError, OSError) as exc:
            scanned.append(relative)
            issues.append(
                QuarantineIssue(
                    path=relative,
                    code="unsafe_or_unreadable_active_path",
                    detail=str(exc),
                )
            )
            continue
        issues.extend(_scan_text(relative, text, policy["stale_signatures"]))
        if block_record is not None:
            issues.extend(
                _validate_embedded_block_record(
                    relative,
                    text,
                    block_record.payload,
                    require_path_match=True,
                )
            )

    for logical_path, value in sorted((additional_contents or {}).items()):
        normalized = _normal_relative_path(logical_path, "additional content path")
        scanned.append(normalized)
        if isinstance(value, QuarantineContent):
            try:
                source_bytes = _read_regular_bytes(
                    root,
                    value.source_path,
                    label="typed package source",
                )
            except CF4P0PolicyError as exc:
                issues.append(
                    QuarantineIssue(
                        path=normalized,
                        code="typed_package_source_unreadable",
                        detail=f"{value.source_path}: {exc}",
                    )
                )
                continue
            content_bytes = (
                value.content.encode("utf-8")
                if isinstance(value.content, str)
                else value.content
            )
            if (
                source_bytes != content_bytes
                or _sha256_bytes(source_bytes) != value.source_sha256
            ):
                issues.append(
                    QuarantineIssue(
                        path=normalized,
                        code="typed_package_source_hash_mismatch",
                        detail=(
                            f"archive payload is not byte-identical to hash-bound source "
                            f"{value.source_path}"
                        ),
                    )
                )
                continue
            if value.mode is not ContentMode.ACTIVE_PUBLIC:
                if not _is_typed_non_science_source(
                    value.source_path, policy, value.mode
                ):
                    issues.append(
                        QuarantineIssue(
                            path=normalized,
                            code="unauthorized_non_science_content_mode",
                            detail=(
                                f"{value.source_path} is not policy-enumerated for "
                                f"{value.mode.value}"
                            ),
                        )
                    )
                continue
            content: str | bytes = value.content
        else:
            content = value
        if _is_exact_generated_contract_payload(root, content, policy):
            continue
        issues.extend(
            _validate_active_text_with_policy(normalized, content, policy=policy)
        )
        if block_record is not None:
            if isinstance(content, bytes):
                try:
                    embedded_text = content.decode("utf-8")
                except UnicodeDecodeError:
                    embedded_text = ""
            else:
                embedded_text = content
            issues.extend(
                _validate_embedded_block_record(
                    normalized,
                    embedded_text,
                    block_record.payload,
                    require_path_match=False,
                )
            )

    unique_issues: list[QuarantineIssue] = []
    seen_issues: set[tuple[Any, ...]] = set()
    for issue in issues:
        key = (issue.path, issue.code, issue.signature_id, issue.line, issue.detail)
        if key not in seen_issues:
            seen_issues.add(key)
            unique_issues.append(issue)
    unique_issues.sort(
        key=lambda value: (
            value.path,
            value.line or 0,
            value.code,
            value.signature_id or "",
        )
    )
    return QuarantineReport(
        policy_sha256=policy_hash,
        inventory_sha256=inventory_hash,
        block_sha256=block_hash,
        scanned_paths=tuple(sorted(set(scanned))),
        issues=tuple(unique_issues),
    )


def assert_repository_clean(
    repo_root: Path | str | None = None,
    *,
    additional_contents: Mapping[str, str | bytes | QuarantineContent] | None = None,
) -> QuarantineReport:
    """Return a clean report or raise one fail-closed violation."""

    report = validate_repository(repo_root, additional_contents=additional_contents)
    if not report.ok:
        first = report.issues[0]
        raise CF4P0QuarantineViolation(
            f"CF4 P0 quarantine rejected {len(report.issues)} issue(s); "
            f"first={first.path}:{first.line or 0} {first.code}: {first.detail}"
        )
    return report


def _load_inventory_entries(root: Path) -> Mapping[str, Mapping[str, Any]]:
    policy, policy_hash = load_policy(root)
    inventory, _ = _validate_inventory(root, policy, policy_hash)
    return {str(entry["path"]): entry for entry in inventory["entries"]}


def require_legacy_reproduction(
    *,
    enabled: bool,
    artifact_path: Path | str,
    repo_root: Path | str | None = None,
) -> None:
    """Authorize only an explicit, pinned output below ``legacy/cf4_p0``."""

    if enabled is not True:
        raise LegacyReproductionRequired(
            "CF4 numerical reproduction requires explicit --legacy-reproduction"
        )
    root = Path(repo_root or repository_root()).resolve()
    path = Path(artifact_path)
    if not path.is_absolute():
        path = root / path
    relative = _repo_relative(path, root, "legacy artifact path")
    policy, _ = load_policy(root)
    if not _path_is_under(relative, policy["legacy_output_roots"]):
        raise LegacyReproductionRequired(
            f"legacy reproduction output must stay under {policy['legacy_output_roots']!r}"
        )
    entries = _load_inventory_entries(root)
    entry = entries.get(relative)
    if (
        entry is None
        or entry.get("mode") != "legacy_reproduction_only"
        or entry.get("role") != "frozen_numerical_reproduction"
        or entry.get("public_use") is not False
    ):
        raise LegacyReproductionRequired(
            f"legacy artifact is not pinned in the canonical inventory: {relative}"
        )
    try:
        legacy_bytes = _read_regular_bytes(
            root, relative, label="legacy reproduction artifact"
        )
    except CF4P0PolicyError as exc:
        raise LegacyReproductionRequired(str(exc)) from exc
    if _sha256_bytes(legacy_bytes) != entry.get("sha256"):
        raise LegacyReproductionRequired(
            f"legacy artifact hash does not match the canonical inventory: {relative}"
        )


__all__ = [
    "BLOCK_RELATIVE_PATH",
    "BLOCK_SCHEMA",
    "CF4P0BlockRecord",
    "CF4P0PolicyError",
    "CF4P0QuarantineError",
    "CF4P0QuarantineViolation",
    "ContentMode",
    "INVENTORY_RELATIVE_PATH",
    "INVENTORY_SCHEMA",
    "LegacyReproductionRequired",
    "POLICY_RELATIVE_PATH",
    "QuarantineIssue",
    "QuarantineContent",
    "QuarantineReport",
    "atomic_write_text",
    "assert_repository_clean",
    "build_canonical_payloads",
    "build_inventory_payload",
    "canonical_artifact_bytes",
    "load_block_record",
    "load_policy",
    "quarantine_block_payload",
    "read_regular_bytes",
    "read_regular_text",
    "render_block_markdown",
    "render_inventory_markdown",
    "reviewed_active_binary_sidecar_pin",
    "repository_root",
    "repository_content",
    "require_legacy_reproduction",
    "validate_active_text",
    "validate_repository",
]
