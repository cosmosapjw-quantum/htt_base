"""Declarative PR-280 execution profiles and smoke-receipt bindings.

The profile manifest controls process execution only.  A passing profile does
not grant scientific, data-admission, native-solver, CAS, or publication
authority.  Generic DAG ``smoke_tested`` readiness is derived only from a
strict binding to the existing ``common.pytest_execution_evidence.v2``
receipt; this module does not introduce a second test-execution authority.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from common.evidence_graph import (
    EvidenceGraphError,
    TestExecution,
    verify_pytest_environment_inputs,
    verify_pytest_selector_inputs,
)


PROFILE_SCHEMA_VERSION = "htt.harness_profiles.v4"
RECEIPT_REGISTRY_SCHEMA_VERSION = "htt.harness_receipt_bindings.v4"

REQUIRED_PROFILE_IDS = frozenset(
    {
        "exact",
        "current-active",
        "scientific",
        "package",
        "data:planck",
        "data:cf4",
        "data:hsc-kids",
        "data:act",
        "data:desi",
        "data:jwst",
        "formal:wolfram-xact",
        "formal:sympy",
        "formal:sage-singular",
        "formal:lean",
        "publication",
        "full-inventory",
        "collect",
        "smoke",
        "fast",
        "active-import",
    }
)
FAILURE_BUCKETS = (
    "ACTIVE_CORE_REGRESSION",
    "STALE_EXPECTATION",
    "MISSING_HISTORICAL_ARTIFACT",
    "LEGACY_BYTE_REPLAY_FAILURE",
    "OPTIONAL_EXTERNAL_TOOL",
    "DATA_NOT_ADMITTED",
    "NATIVE_NOT_AVAILABLE",
    "CF4_QUARANTINE",
    "PUBLICATION_DEBT",
    "UNKNOWN_UNCLASSIFIED",
)
_PROFILE_KINDS = frozenset({"pytest", "import_probe", "tool_probe"})
_PYTEST_PROFILE_IDS = REQUIRED_PROFILE_IDS - {
    "active-import",
    "formal:wolfram-xact",
    "formal:sympy",
    "formal:sage-singular",
    "formal:lean",
}
_WAIVER_POLICIES = frozenset({"forbidden", "registered_non_receipt"})
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_GIT_OBJECT_RE = re.compile(r"[0-9a-f]{40,64}\Z")


class HarnessProfileError(ValueError):
    """Raised when a manifest or receipt binding is not admissible."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strict_keys(
    value: Mapping[str, object],
    *,
    required: set[str],
    optional: set[str] | None = None,
    label: str,
) -> None:
    allowed = required | (optional or set())
    missing = required - set(value)
    unknown = set(value) - allowed
    if missing or unknown:
        raise HarnessProfileError(
            f"{label} keys mismatch: missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HarnessProfileError(f"{label} must be a non-empty string")
    return value


def _text_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise HarnessProfileError(f"{label} must be a sequence of strings")
    rows = tuple(_text(item, label) for item in value)
    if len(rows) != len(set(rows)):
        raise HarnessProfileError(f"{label} contains duplicates")
    return rows


@dataclass(frozen=True)
class HarnessProfile:
    profile_id: str
    kind: str
    lane: str
    selectors: tuple[str, ...]
    pytest_args: tuple[str, ...]
    modules: tuple[str, ...]
    tools: tuple[str, ...]
    smoke_status_eligible: bool
    receipt_eligible: bool
    waiver_policy: str
    claim_ceiling: str
    allowed_use: str

    def __post_init__(self) -> None:
        if self.kind not in _PROFILE_KINDS:
            raise HarnessProfileError(
                f"profile {self.profile_id} has unknown kind {self.kind!r}"
            )
        expected_kind = (
            "import_probe"
            if self.profile_id == "active-import"
            else "tool_probe"
            if self.profile_id.startswith("formal:")
            else "pytest"
            if self.profile_id in _PYTEST_PROFILE_IDS
            else None
        )
        if expected_kind is not None and self.kind != expected_kind:
            raise HarnessProfileError(
                f"profile {self.profile_id} must have kind {expected_kind}"
            )
        if self.waiver_policy not in _WAIVER_POLICIES:
            raise HarnessProfileError(
                f"profile {self.profile_id} has unknown waiver policy"
            )
        if self.claim_ceiling != "diagnostic_only":
            raise HarnessProfileError(
                f"profile {self.profile_id} exceeds diagnostic-only claim ceiling"
            )
        if self.kind == "pytest":
            if self.modules or self.tools:
                raise HarnessProfileError(
                    f"pytest profile {self.profile_id} cannot declare modules/tools"
                )
        elif self.kind == "import_probe":
            if not self.modules or self.selectors or self.pytest_args or self.tools:
                raise HarnessProfileError(
                    f"import profile {self.profile_id} must declare only modules"
                )
            for specification in self.modules:
                module, separator, origin = specification.partition("=")
                if (
                    not separator
                    or not module
                    or not origin
                    or origin.startswith("/")
                    or ".." in Path(origin).parts
                ):
                    raise HarnessProfileError(
                        f"import profile {self.profile_id} has malformed module origin"
                    )
        elif self.kind == "tool_probe":
            if not self.tools or self.selectors or self.pytest_args or self.modules:
                raise HarnessProfileError(
                    f"tool profile {self.profile_id} must declare only tools"
                )
        if self.smoke_status_eligible:
            if self.profile_id != "smoke" or self.kind != "pytest":
                raise HarnessProfileError(
                    "only the explicit smoke pytest profile may set smoke readiness"
                )
            if not self.receipt_eligible or self.waiver_policy != "forbidden":
                raise HarnessProfileError(
                    "smoke readiness requires receipt eligibility and no waiver"
                )
        if self.profile_id in {"smoke", "fast"}:
            if self.kind != "pytest" or not self.selectors:
                raise HarnessProfileError(
                    f"{self.profile_id} must use explicit pytest selectors"
                )
            if any("::" not in selector for selector in self.selectors):
                raise HarnessProfileError(
                    f"{self.profile_id} must use explicit pytest node IDs"
                )
            if any(arg == "-m" or arg.startswith("-m=") for arg in self.pytest_args):
                raise HarnessProfileError(
                    f"{self.profile_id} cannot use marker-only selection"
                )
        if self.profile_id in {"publication", "full-inventory"}:
            if self.waiver_policy != "forbidden":
                raise HarnessProfileError(
                    f"{self.profile_id} forbids every waiver"
                )
        if self.profile_id == "full-inventory" and (
            self.selectors
            or self.pytest_args != ("--junitxml=artifacts/full_inventory.xml",)
            or self.receipt_eligible
        ):
            raise HarnessProfileError(
                "full-inventory must execute the exact cache-free JUnit command"
            )
        if self.profile_id == "collect" and (
            self.selectors or self.pytest_args != ("--collect-only", "-q")
        ):
            raise HarnessProfileError("collect profile command drifted")
        if self.profile_id.startswith(("data:", "formal:")):
            if self.smoke_status_eligible or self.receipt_eligible:
                raise HarnessProfileError(
                    f"{self.profile_id} cannot transfer generic test authority"
                )
            if self.waiver_policy != "forbidden":
                raise HarnessProfileError(
                    f"{self.profile_id} cannot use a focused waiver"
                )

    def pytest_command(self, python: str) -> list[str]:
        if self.kind != "pytest":
            raise HarnessProfileError(f"{self.profile_id} is not a pytest profile")
        return [
            python,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-o",
            "addopts=",
            *self.pytest_args,
            *self.selectors,
        ]


@dataclass(frozen=True)
class HarnessProfileManifest:
    path: Path
    manifest_id: str
    profiles: Mapping[str, HarnessProfile]
    changed_surface_routes: tuple["ChangedSurfaceRoute", ...]
    sha256: str

    def profile(self, profile_id: str) -> HarnessProfile:
        try:
            return self.profiles[profile_id]
        except KeyError as exc:
            raise HarnessProfileError(f"unknown profile: {profile_id}") from exc

    def profiles_for_paths(self, paths: Sequence[str]) -> tuple[str, ...]:
        selected: set[str] = set()
        for path in paths:
            if not isinstance(path, str) or not path or path.startswith("/"):
                raise HarnessProfileError("changed paths must be repository-relative")
            for route in self.changed_surface_routes:
                if route.matches(path):
                    selected.update(route.profiles)
        return tuple(sorted(selected))


@dataclass(frozen=True)
class ChangedSurfaceRoute:
    route_id: str
    path_regex: str
    profiles: tuple[str, ...]

    def __post_init__(self) -> None:
        try:
            re.compile(self.path_regex)
        except re.error as exc:
            raise HarnessProfileError(
                f"changed-surface route {self.route_id} has invalid regex"
            ) from exc

    def matches(self, path: str) -> bool:
        return re.fullmatch(self.path_regex, path) is not None


def load_profile_manifest(
    path: str | Path,
    *,
    repo_root: str | Path | None = None,
    verify_paths: bool = True,
) -> HarnessProfileManifest:
    resolved = Path(path)
    if resolved.is_symlink() or not resolved.is_file():
        raise HarnessProfileError(f"profile manifest is missing or non-regular: {path}")
    raw = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise HarnessProfileError("profile manifest must be a mapping")
    _strict_keys(
        raw,
        required={
            "schema_version",
            "manifest_id",
            "profiles",
            "changed_surface_routes",
        },
        label="profile manifest",
    )
    if raw["schema_version"] != PROFILE_SCHEMA_VERSION:
        raise HarnessProfileError("unsupported harness profile schema")
    rows = raw["profiles"]
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise HarnessProfileError("profiles must be a sequence")
    profiles: dict[str, HarnessProfile] = {}
    for index, raw_row in enumerate(rows):
        if not isinstance(raw_row, Mapping):
            raise HarnessProfileError(f"profile row {index} must be a mapping")
        _strict_keys(
            raw_row,
            required={
                "profile_id",
                "kind",
                "lane",
                "selectors",
                "pytest_args",
                "modules",
                "tools",
                "smoke_status_eligible",
                "receipt_eligible",
                "waiver_policy",
                "claim_ceiling",
                "allowed_use",
            },
            label=f"profile row {index}",
        )
        profile = HarnessProfile(
            profile_id=_text(raw_row["profile_id"], "profile_id"),
            kind=_text(raw_row["kind"], "kind"),
            lane=_text(raw_row["lane"], "lane"),
            selectors=_text_tuple(raw_row["selectors"], "selectors"),
            pytest_args=_text_tuple(raw_row["pytest_args"], "pytest_args"),
            modules=_text_tuple(raw_row["modules"], "modules"),
            tools=_text_tuple(raw_row["tools"], "tools"),
            smoke_status_eligible=raw_row["smoke_status_eligible"],
            receipt_eligible=raw_row["receipt_eligible"],
            waiver_policy=_text(raw_row["waiver_policy"], "waiver_policy"),
            claim_ceiling=_text(raw_row["claim_ceiling"], "claim_ceiling"),
            allowed_use=_text(raw_row["allowed_use"], "allowed_use"),
        )
        if not isinstance(profile.smoke_status_eligible, bool) or not isinstance(
            profile.receipt_eligible, bool
        ):
            raise HarnessProfileError("profile eligibility fields must be booleans")
        if profile.profile_id in profiles:
            raise HarnessProfileError(f"duplicate profile id: {profile.profile_id}")
        profiles[profile.profile_id] = profile
    if set(profiles) != REQUIRED_PROFILE_IDS:
        raise HarnessProfileError(
            "profile id partition mismatch: "
            f"missing={sorted(REQUIRED_PROFILE_IDS - set(profiles))}, "
            f"unknown={sorted(set(profiles) - REQUIRED_PROFILE_IDS)}"
        )
    formal = {
        profile_id for profile_id in profiles if profile_id.startswith("formal:")
    }
    if formal != {
        "formal:wolfram-xact",
        "formal:sympy",
        "formal:sage-singular",
        "formal:lean",
    }:
        raise HarnessProfileError("formal profile axes are incomplete")
    raw_routes = raw["changed_surface_routes"]
    if not isinstance(raw_routes, Sequence) or isinstance(raw_routes, (str, bytes)):
        raise HarnessProfileError("changed_surface_routes must be a sequence")
    routes: list[ChangedSurfaceRoute] = []
    route_ids: set[str] = set()
    for index, raw_route in enumerate(raw_routes):
        if not isinstance(raw_route, Mapping):
            raise HarnessProfileError(f"changed-surface route {index} must be a mapping")
        _strict_keys(
            raw_route,
            required={"route_id", "path_regex", "profiles"},
            label=f"changed-surface route {index}",
        )
        route = ChangedSurfaceRoute(
            route_id=_text(raw_route["route_id"], "route_id"),
            path_regex=_text(raw_route["path_regex"], "path_regex"),
            profiles=_text_tuple(raw_route["profiles"], "route profiles"),
        )
        if route.route_id in route_ids:
            raise HarnessProfileError(f"duplicate changed-surface route: {route.route_id}")
        unknown_profiles = set(route.profiles) - set(profiles)
        if unknown_profiles:
            raise HarnessProfileError(
                f"route {route.route_id} names unknown profiles: {sorted(unknown_profiles)}"
            )
        route_ids.add(route.route_id)
        routes.append(route)
    if not routes:
        raise HarnessProfileError("at least one changed-surface route is required")
    if verify_paths:
        root = Path(repo_root) if repo_root is not None else resolved.parents[3]
        for profile in profiles.values():
            for selector in profile.selectors:
                relative = selector.split("::", 1)[0]
                candidate = root / relative
                if candidate.is_symlink() or not candidate.is_file():
                    raise HarnessProfileError(
                        f"profile {profile.profile_id} selector is missing: {relative}"
                    )
    return HarnessProfileManifest(
        path=resolved,
        manifest_id=_text(raw["manifest_id"], "manifest_id"),
        profiles=profiles,
        changed_surface_routes=tuple(routes),
        sha256=sha256_file(resolved),
    )


@dataclass(frozen=True)
class VerifiedSmokeReceipt:
    pr_id: str
    profile_id: str
    evidence_ref: str
    execution_ref: str
    candidate_commit: str
    candidate_tree: str


def _git_tree(repo_root: Path, commit: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"{commit}^{{tree}}"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise HarnessProfileError(f"candidate commit is unavailable: {commit}")
    tree = completed.stdout.strip()
    if not _GIT_OBJECT_RE.fullmatch(tree):
        raise HarnessProfileError("candidate tree identity is malformed")
    return tree


def _git_file_sha256(repo_root: Path, commit: str, relative_path: str) -> str:
    if relative_path.startswith("/") or ".." in Path(relative_path).parts:
        raise HarnessProfileError("receipt contains an unsafe repository path")
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise HarnessProfileError(
            f"candidate commit does not contain receipt input: {relative_path}"
        )
    return hashlib.sha256(completed.stdout).hexdigest()


def _receipt_repo_bindings(payload: Mapping[str, object]) -> dict[str, str]:
    rows: list[object] = []
    rows.extend(payload.get("selector_inputs", ()))
    environment = payload.get("environment_contract")
    if not isinstance(environment, Mapping):
        raise HarnessProfileError("pytest evidence lacks environment contract")
    pytest_environment = environment.get("pytest")
    if not isinstance(pytest_environment, Mapping):
        raise HarnessProfileError("pytest evidence lacks pytest environment")
    config_file = pytest_environment.get("config_file")
    if config_file is not None:
        rows.append(config_file)
    for key in ("plugins", "conftests"):
        values = pytest_environment.get(key)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise HarnessProfileError(f"pytest evidence {key} must be a sequence")
        for value in values:
            if isinstance(value, Mapping) and "source" in value:
                rows.append(value["source"])
            else:
                rows.append(value)
    origins = environment.get("import_origins")
    if not isinstance(origins, Sequence) or isinstance(origins, (str, bytes)):
        raise HarnessProfileError("pytest evidence import origins must be a sequence")
    for value in origins:
        if not isinstance(value, Mapping) or "source" not in value:
            raise HarnessProfileError("pytest evidence import origin is malformed")
        rows.append(value["source"])
    bindings: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping) or row.get("scope") != "repo":
            continue
        relative = _text(row.get("path"), "repository input path")
        digest = _text(row.get("sha256"), "repository input sha256")
        if not _SHA256_RE.fullmatch(digest):
            raise HarnessProfileError("repository input sha256 is malformed")
        prior = bindings.setdefault(relative, digest)
        if prior != digest:
            raise HarnessProfileError(
                f"receipt has conflicting hashes for repository input: {relative}"
            )
    if not bindings:
        raise HarnessProfileError("pytest evidence has no repository-bound inputs")
    return bindings


def _verify_candidate_receipt_inputs(
    *,
    repo_root: Path,
    candidate_commit: str,
    manifest: HarnessProfileManifest,
    evidence_payload: Mapping[str, object],
) -> None:
    try:
        manifest_relative = manifest.path.resolve().relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise HarnessProfileError("profile manifest is outside the repository") from exc
    bindings = _receipt_repo_bindings(evidence_payload)
    prior_manifest_sha = bindings.setdefault(manifest_relative, manifest.sha256)
    if prior_manifest_sha != manifest.sha256:
        raise HarnessProfileError(
            "pytest receipt conflicts with the registered profile manifest"
        )
    mismatches = [
        relative
        for relative, expected in sorted(bindings.items())
        if _git_file_sha256(repo_root, candidate_commit, relative) != expected
    ]
    if mismatches:
        raise HarnessProfileError(
            f"pytest receipt inputs do not match candidate commit: {mismatches}"
        )


def _validate_smoke_invocation(invocation: Sequence[str]) -> None:
    forbidden_controls = {
        "-m",
        "-k",
        "--lf",
        "--last-failed",
        "--ff",
        "--failed-first",
        "--sw",
        "--stepwise",
        "--deselect",
        "--ignore",
        "--ignore-glob",
        "--maxfail",
        "-n",
    }
    forbidden_prefixes = (
        "-m=",
        "-k=",
        "--deselect=",
        "--ignore=",
        "--ignore-glob=",
        "--maxfail=",
    )
    expected_control_values = {
        "-p": ("common.pytest_execution_evidence", "no:cacheprovider"),
        "-o": ("addopts=",),
        "--rootdir": (".",),
        "-c": ("pytest.ini",),
    }
    actual_control_values: dict[str, tuple[str, ...]] = {}
    for control, expected in expected_control_values.items():
        values: list[str] = []
        for index, value in enumerate(invocation):
            if value != control:
                continue
            if index + 1 >= len(invocation):
                raise HarnessProfileError(
                    "pytest evidence violates smoke execution controls"
                )
            values.append(invocation[index + 1])
        actual_control_values[control] = tuple(values)
        if actual_control_values[control] != expected:
            raise HarnessProfileError(
                "pytest evidence violates smoke execution controls"
            )
    concatenated_short_controls = any(
        value.startswith(("-c", "-k", "-m", "-n", "-o", "-p"))
        and value not in {"-c", "-k", "-m", "-n", "-o", "-p"}
        and not value.startswith("--")
        for value in invocation
    )
    override_ini_controls = any(
        value == "--override-ini" or value.startswith("--override-ini=")
        for value in invocation
    )
    if (
        forbidden_controls.intersection(invocation)
        or any(value.startswith(forbidden_prefixes) for value in invocation)
        or concatenated_short_controls
        or override_ini_controls
        or any(value.startswith("--rootdir=") for value in invocation)
        or invocation.count("--import-mode=importlib") != 1
        or any(
            value == "--import-mode" or value.startswith("--import-mode=")
            for value in invocation
            if value != "--import-mode=importlib"
        )
    ):
        raise HarnessProfileError("pytest evidence violates smoke execution controls")


def _validate_smoke_execution(
    profile: HarnessProfile, execution: TestExecution
) -> None:
    _validate_smoke_invocation(execution.command)
    expected = tuple(sorted(profile.selectors))
    if (
        tuple(execution.collected_test_ids) != expected
        or tuple(execution.executed_test_ids) != expected
    ):
        raise HarnessProfileError(
            "pytest evidence does not execute every registered smoke node exactly once"
        )


def _repo_file(repo_root: Path, raw_path: object, label: str) -> Path:
    relative = Path(_text(raw_path, label))
    if relative.is_absolute() or ".." in relative.parts:
        raise HarnessProfileError(f"{label} must be repository-relative")
    path = repo_root / relative
    if path.is_symlink() or not path.is_file():
        raise HarnessProfileError(f"{label} is missing or non-regular")
    return path


def validate_smoke_receipt_registry(
    registry_path: str | Path,
    *,
    manifest: HarnessProfileManifest,
    repo_root: str | Path,
) -> dict[str, VerifiedSmokeReceipt]:
    root = Path(repo_root).resolve()
    path = Path(registry_path)
    if path.is_symlink() or not path.is_file():
        raise HarnessProfileError("smoke receipt registry is missing or non-regular")
    try:
        path.resolve().relative_to(root)
    except ValueError as exc:
        raise HarnessProfileError("smoke receipt registry is outside the repository") from exc
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise HarnessProfileError("smoke receipt registry must be a mapping")
    _strict_keys(
        payload,
        required={"schema_version", "manifest_path", "records"},
        label="smoke receipt registry",
    )
    if payload["schema_version"] != RECEIPT_REGISTRY_SCHEMA_VERSION:
        raise HarnessProfileError("unsupported smoke receipt registry schema")
    manifest_path = _repo_file(root, payload["manifest_path"], "manifest_path")
    if manifest_path.resolve() != manifest.path.resolve():
        raise HarnessProfileError("smoke receipt registry names another manifest")
    rows = payload["records"]
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise HarnessProfileError("smoke receipt records must be a sequence")
    verified: dict[str, VerifiedSmokeReceipt] = {}
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise HarnessProfileError(f"smoke receipt row {index} must be a mapping")
        _strict_keys(
            raw,
            required={
                "pr_id",
                "profile_id",
                "profile_manifest_sha256",
                "evidence_path",
                "evidence_sha256",
                "candidate_commit",
                "candidate_tree",
                "waiver_id",
                "created_at",
                "binding_sha256",
            },
            label=f"smoke receipt row {index}",
        )
        pr_id = _text(raw["pr_id"], "pr_id")
        if pr_id in verified:
            raise HarnessProfileError(f"duplicate smoke receipt for {pr_id}")
        profile_id = _text(raw["profile_id"], "profile_id")
        profile = manifest.profile(profile_id)
        if not profile.smoke_status_eligible or not profile.receipt_eligible:
            raise HarnessProfileError(
                f"profile {profile_id} is not eligible for smoke readiness"
            )
        if raw["waiver_id"] is not None:
            raise HarnessProfileError("waived execution cannot set smoke readiness")
        manifest_sha = _text(raw["profile_manifest_sha256"], "manifest sha256")
        if manifest_sha != manifest.sha256:
            raise HarnessProfileError("profile manifest hash mismatch")
        evidence = _repo_file(root, raw["evidence_path"], "evidence_path")
        evidence_sha = _text(raw["evidence_sha256"], "evidence sha256")
        if not _SHA256_RE.fullmatch(evidence_sha) or sha256_file(evidence) != evidence_sha:
            raise HarnessProfileError("pytest evidence hash mismatch")
        candidate_commit = _text(raw["candidate_commit"], "candidate_commit")
        candidate_tree = _text(raw["candidate_tree"], "candidate_tree")
        if not _GIT_OBJECT_RE.fullmatch(candidate_commit):
            raise HarnessProfileError("candidate commit identity is malformed")
        if _git_tree(root, candidate_commit) != candidate_tree:
            raise HarnessProfileError("candidate commit/tree binding mismatch")
        created_at = _text(raw["created_at"], "created_at")
        try:
            parsed_created_at = datetime.fromisoformat(created_at)
        except ValueError as exc:
            raise HarnessProfileError("created_at must be an ISO-8601 timestamp") from exc
        if parsed_created_at.tzinfo is None:
            raise HarnessProfileError("created_at must include a timezone")
        unsigned = dict(raw)
        binding_sha = _text(unsigned.pop("binding_sha256"), "binding_sha256")
        expected_binding_sha = hashlib.sha256(_canonical_bytes(unsigned)).hexdigest()
        if binding_sha != expected_binding_sha:
            raise HarnessProfileError("smoke receipt binding hash mismatch")
        try:
            evidence_payload = json.loads(evidence.read_text(encoding="utf-8"))
            if not isinstance(evidence_payload, Mapping):
                raise HarnessProfileError("pytest evidence must be a JSON mapping")
            execution = TestExecution.from_pytest_evidence(evidence_payload)
            verify_pytest_selector_inputs(root, evidence_payload)
            verify_pytest_environment_inputs(root, evidence_payload)
        except (EvidenceGraphError, json.JSONDecodeError) as exc:
            raise HarnessProfileError("pytest evidence failed strict validation") from exc
        if not execution.is_authoritative:
            raise HarnessProfileError("pytest evidence is not an all-pass execution")
        if tuple(evidence_payload["selector_argv"]) != profile.selectors:
            raise HarnessProfileError("pytest evidence selectors mismatch profile")
        _verify_candidate_receipt_inputs(
            repo_root=root,
            candidate_commit=candidate_commit,
            manifest=manifest,
            evidence_payload=evidence_payload,
        )
        _validate_smoke_execution(profile, execution)
        verified[pr_id] = VerifiedSmokeReceipt(
            pr_id=pr_id,
            profile_id=profile_id,
            evidence_ref=evidence_sha,
            execution_ref=execution.execution_ref,
            candidate_commit=candidate_commit,
            candidate_tree=candidate_tree,
        )
    return verified


def _contains_pair(values: Sequence[str], first: str, second: str) -> bool:
    return any(
        values[index] == first and values[index + 1] == second
        for index in range(len(values) - 1)
    )


def make_smoke_binding_record(
    *,
    pr_id: str,
    profile_id: str,
    manifest: HarnessProfileManifest,
    evidence_path: str,
    evidence_sha256: str,
    candidate_commit: str,
    candidate_tree: str,
    created_at: str,
) -> dict[str, object]:
    """Create a sealed registry row; validation remains a separate operation."""

    row: dict[str, object] = {
        "pr_id": _text(pr_id, "pr_id"),
        "profile_id": _text(profile_id, "profile_id"),
        "profile_manifest_sha256": manifest.sha256,
        "evidence_path": _text(evidence_path, "evidence_path"),
        "evidence_sha256": _text(evidence_sha256, "evidence_sha256"),
        "candidate_commit": _text(candidate_commit, "candidate_commit"),
        "candidate_tree": _text(candidate_tree, "candidate_tree"),
        "waiver_id": None,
        "created_at": _text(created_at, "created_at"),
    }
    row["binding_sha256"] = hashlib.sha256(_canonical_bytes(row)).hexdigest()
    return row


__all__ = [
    "FAILURE_BUCKETS",
    "ChangedSurfaceRoute",
    "HarnessProfile",
    "HarnessProfileError",
    "HarnessProfileManifest",
    "PROFILE_SCHEMA_VERSION",
    "RECEIPT_REGISTRY_SCHEMA_VERSION",
    "REQUIRED_PROFILE_IDS",
    "VerifiedSmokeReceipt",
    "load_profile_manifest",
    "make_smoke_binding_record",
    "sha256_file",
    "validate_smoke_receipt_registry",
]
