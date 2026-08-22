"""Pinned Ed25519 validation for a future observed-lane authorization.

The repository contains public trust anchors only. This module never issues an
authorization, handles a human private key, consumes a nonce, or opens an
observed payload. A validated object is cache evidence: every authority use
must reparse and reverify its signed receipt against the current admission,
clean candidate, trusted public key, and evaluation time.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Mapping, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from common.data_identity import (
    AdmissionStatus,
    DataIdentityError,
    LaneAdmissionDecision,
    LaneSpec,
    build_not_authorized_receipt,
    canonical_sha256,
    lane_registry_from_mapping,
    replay_lane_admission_decision,
)


AUTHORIZATION_SCHEMA = "common.human_execution_authorization_receipt.v3"
VALIDATED_AUTHORIZATION_SCHEMA = (
    "common.validated_human_execution_authorization_cache.v2"
)
CANDIDATE_IDENTITY_SCHEMA = "common.clean_candidate_identity.v1"
AUTHORITY_REGISTRY_SCHEMA = "common.human_authority_registry.v1"
AUTHORIZATION_DOMAIN = "lane_data_execution"
MAX_AUTHORIZATION_TTL = timedelta(seconds=1800)

_RAW_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_OBJECT = re.compile(r"^[0-9a-f]{40}$")
_NONCE = re.compile(r"^nonce:v1:[0-9a-f]{64}$")
_LANE_REGISTRY_RELATIVE_PATH = Path(
    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
_AUTHORITY_REGISTRY_RELATIVE_PATH = Path(
    "docs/research_program/post_pr275/human_authority_registry.json"
)
_LANE_ORDER = ("PLANCK", "CF4", "HSC_KIDS", "ACT", "DESI", "JWST_SN")
_SCOPES_BY_LANE = {
    "PLANCK": "admitted_planck_observed_execution",
    "CF4": "admitted_cf4_observed_execution",
    "HSC_KIDS": "admitted_hsc_kids_observed_execution",
    "ACT": "admitted_act_observed_execution",
    "DESI": "admitted_desi_observed_execution",
    "JWST_SN": "admitted_jwst_sn_observed_execution",
}
_TRUSTED_GIT = Path("/usr/bin/git")
_TRUSTED_GIT_ENV = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_LITERAL_PATHSPECS": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_NO_LAZY_FETCH": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "LC_ALL": "C",
    "LANG": "C",
}
EXTERNAL_TRUST_ROOT_PUBLIC_KEY = Path(
    "/etc/htt/trust/root_authority_ed25519.pub"
)
EXTERNAL_TRUST_ROOT_FINGERPRINT = Path(
    "/etc/htt/trust/root_authority_ed25519.pub.sha256"
)
TRUSTED_LAUNCHER = Path("/usr/local/libexec/htt-auth-launcher")


class HumanExecutionAuthorizationError(ValueError):
    """Raised when authorization evidence is incomplete, stale, or forged."""


class ExternalTrustedLauncherRequired(HumanExecutionAuthorizationError):
    """Raised because candidate code cannot establish execution authority."""


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise HumanExecutionAuthorizationError(
            f"{field} must be a non-empty canonical string"
        )
    return value


def _sha256_identity(value: object, field: str) -> str:
    text = _text(value, field)
    if not text.startswith("sha256:") or _RAW_SHA256.fullmatch(text[7:]) is None:
        raise HumanExecutionAuthorizationError(
            f"{field} must be a lowercase sha256 identity"
        )
    return text


def _git_object(value: object, field: str) -> str:
    text = _text(value, field)
    if _GIT_OBJECT.fullmatch(text) is None:
        raise HumanExecutionAuthorizationError(
            f"{field} must be a lowercase git object id"
        )
    return text


def _utc(value: object, field: str) -> tuple[str, datetime]:
    text = _text(value, field)
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise HumanExecutionAuthorizationError(
            f"{field} is not a canonical UTC timestamp"
        ) from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != text:
        raise HumanExecutionAuthorizationError(
            f"{field} is not a canonical UTC timestamp"
        )
    return text, parsed


def _trusted_now_utc() -> datetime:
    """Return the process host's UTC clock for a live authority decision."""

    return datetime.now(timezone.utc)


def _trusted_evaluation_time() -> tuple[str, datetime]:
    """Normalize the private clock seam; callers cannot supply evaluation time."""

    observed = _trusted_now_utc()
    if not isinstance(observed, datetime) or observed.tzinfo is None:
        raise HumanExecutionAuthorizationError(
            "trusted authorization clock must return a timezone-aware datetime"
        )
    evaluated = observed.astimezone(timezone.utc)
    return evaluated.strftime("%Y-%m-%dT%H:%M:%SZ"), evaluated


def _nonce(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise HumanExecutionAuthorizationError(
            "nonce must equal nonce:v1 followed by 64 lowercase hex characters"
        )
    text = value
    if _NONCE.fullmatch(text) is None:
        raise HumanExecutionAuthorizationError(
            "nonce must equal nonce:v1 followed by 64 lowercase hex characters"
        )
    return text


def _canonical_bytes(payload: Mapping[str, object]) -> bytes:
    try:
        return json.dumps(
            dict(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise HumanExecutionAuthorizationError(
            "authorization payload is not canonical finite JSON"
        ) from exc


def _strict_json_bytes(raw: bytes, *, field: str) -> Mapping[str, object]:
    if type(raw) is not bytes:
        raise HumanExecutionAuthorizationError(f"{field} must be exact bytes")

    def no_duplicate(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise HumanExecutionAuthorizationError(
                    f"{field} contains duplicate key {key!r}"
                )
            result[key] = value
        return result

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=no_duplicate,
            parse_constant=lambda token: (_ for _ in ()).throw(
                HumanExecutionAuthorizationError(
                    f"{field} contains non-finite constant {token}"
                )
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise HumanExecutionAuthorizationError(
            f"{field} is not strict UTF-8 JSON"
        ) from exc
    if not isinstance(value, Mapping):
        raise HumanExecutionAuthorizationError(f"{field} must contain a mapping")
    _canonical_bytes(value)
    return value


def _exact_mapping(
    payload: object, *, expected: frozenset[str], field: str
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping) or set(payload) != expected:
        raise HumanExecutionAuthorizationError(f"{field} fields drifted")
    return payload


def _record_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise HumanExecutionAuthorizationError(
            "exact_admission_record_ids must be an ordered sequence"
        )
    records = tuple(
        _sha256_identity(item, "exact_admission_record_ids") for item in value
    )
    if not records or len(records) != len(set(records)):
        raise HumanExecutionAuthorizationError(
            "exact_admission_record_ids must be non-empty and unique"
        )
    return records


def _canonical_base64(value: object, *, field: str, byte_length: int) -> bytes:
    text = _text(value, field)
    try:
        decoded = base64.b64decode(text, validate=True)
    except (ValueError, TypeError) as exc:
        raise HumanExecutionAuthorizationError(
            f"{field} must be canonical base64"
        ) from exc
    if len(decoded) != byte_length or base64.b64encode(decoded).decode("ascii") != text:
        raise HumanExecutionAuthorizationError(
            f"{field} must encode exactly {byte_length} bytes"
        )
    return decoded


def _git(repo_root: Path, *args: str) -> str:
    """Run the system Git with no caller-selected executable or Git environment."""

    if (
        not _TRUSTED_GIT.is_absolute()
        or not _TRUSTED_GIT.is_file()
        or _TRUSTED_GIT.is_symlink()
        or not os.access(_TRUSTED_GIT, os.X_OK)
    ):
        raise HumanExecutionAuthorizationError(
            "trusted system Git executable is unavailable"
        )
    try:
        completed = subprocess.run(
            [
                str(_TRUSTED_GIT),
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.untrackedCache=false",
                "-C",
                str(repo_root),
                *args,
            ],
            check=False,
            capture_output=True,
            env=_TRUSTED_GIT_ENV,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HumanExecutionAuthorizationError(
            "candidate git identity cannot be inspected"
        ) from exc
    if completed.returncode != 0:
        raise HumanExecutionAuthorizationError(
            "candidate git identity cannot be inspected"
        )
    return completed.stdout.rstrip("\n")


def _git_bytes(repo_root: Path, *args: str) -> bytes:
    """Binary counterpart of :func:`_git` using the same trusted boundary."""

    if (
        not _TRUSTED_GIT.is_absolute()
        or not _TRUSTED_GIT.is_file()
        or _TRUSTED_GIT.is_symlink()
        or not os.access(_TRUSTED_GIT, os.X_OK)
    ):
        raise HumanExecutionAuthorizationError(
            "trusted system Git executable is unavailable"
        )
    try:
        completed = subprocess.run(
            [
                str(_TRUSTED_GIT),
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.untrackedCache=false",
                "-C",
                str(repo_root),
                *args,
            ],
            check=False,
            capture_output=True,
            env=_TRUSTED_GIT_ENV,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HumanExecutionAuthorizationError(
            "candidate Git object cannot be inspected"
        ) from exc
    if completed.returncode != 0:
        raise HumanExecutionAuthorizationError(
            "candidate Git object cannot be inspected"
        )
    return completed.stdout


@dataclass(frozen=True)
class CandidateIdentityV1:
    """Recheckable identity of one clean, attached Git candidate."""

    repo_root: Path
    branch: str
    commit: str
    tree: str
    candidate_identity_id: str

    def as_payload(self) -> dict[str, object]:
        return {
            "schema": CANDIDATE_IDENTITY_SCHEMA,
            "branch": self.branch,
            "commit": self.commit,
            "tree": self.tree,
            "candidate_identity_id": self.candidate_identity_id,
        }


def build_clean_candidate_identity(repo_root: Path) -> CandidateIdentityV1:
    """Derive commit/tree from a clean attached worktree; never trust strings."""

    if not isinstance(repo_root, Path) or not repo_root.is_absolute():
        raise HumanExecutionAuthorizationError(
            "candidate repository root must be an absolute Path"
        )
    try:
        resolved = repo_root.resolve(strict=True)
    except OSError as exc:
        raise HumanExecutionAuthorizationError(
            "candidate repository root is unavailable"
        ) from exc
    if resolved != repo_root or _git(repo_root, "rev-parse", "--show-toplevel") != str(
        repo_root
    ):
        raise HumanExecutionAuthorizationError(
            "candidate repository root is not canonical"
        )
    branch = _text(
        _git(repo_root, "symbolic-ref", "--quiet", "--short", "HEAD"),
        "candidate branch",
    )
    commit = _git_object(_git(repo_root, "rev-parse", "HEAD"), "candidate commit")
    tree = _git_object(
        _git(repo_root, "rev-parse", "HEAD^{tree}"), "candidate tree"
    )
    if _git(repo_root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise HumanExecutionAuthorizationError("candidate repository is dirty")
    unsigned = {
        "schema": CANDIDATE_IDENTITY_SCHEMA,
        "branch": branch,
        "commit": commit,
        "tree": tree,
    }
    return CandidateIdentityV1(
        repo_root=repo_root,
        branch=branch,
        commit=commit,
        tree=tree,
        candidate_identity_id=canonical_sha256(unsigned),
    )


def revalidate_clean_candidate_identity(
    candidate: CandidateIdentityV1,
) -> CandidateIdentityV1:
    if type(candidate) is not CandidateIdentityV1:
        raise HumanExecutionAuthorizationError(
            "candidate identity must be factory-derived"
        )
    observed = build_clean_candidate_identity(candidate.repo_root)
    if observed.as_payload() != candidate.as_payload():
        raise HumanExecutionAuthorizationError("candidate identity is stale or forged")
    return observed


def _candidate_relative_path(value: object, field: str) -> str:
    text = _text(value, field)
    path = Path(text)
    if (
        path.is_absolute()
        or text != path.as_posix()
        or text.startswith(".")
        or ".." in path.parts
        or any(character in text for character in ("\x00", "\n", "\r", ":"))
    ):
        raise HumanExecutionAuthorizationError(
            f"{field} must be a canonical candidate-relative path"
        )
    return text


def read_candidate_blob(
    candidate: CandidateIdentityV1, relative_path: object
) -> bytes:
    """Read immutable bytes addressed by ``candidate.commit:path``.

    Worktree pathname reads are deliberately excluded from trust-bearing
    registry, provider, configuration, and environment bindings.
    """

    checked = revalidate_clean_candidate_identity(candidate)
    relative = _candidate_relative_path(relative_path, "candidate blob path")
    object_name = f"{checked.commit}:{relative}"
    object_type = _git(checked.repo_root, "cat-file", "-t", object_name)
    if object_type != "blob":
        raise HumanExecutionAuthorizationError(
            "candidate resource is not a regular Git blob"
        )
    return _git_bytes(checked.repo_root, "cat-file", "blob", object_name)


def candidate_blob_binding(
    candidate: CandidateIdentityV1, relative_path: object
) -> dict[str, str]:
    relative = _candidate_relative_path(relative_path, "candidate blob path")
    raw = read_candidate_blob(candidate, relative)
    return {
        "path": relative,
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
    }


def lane_spec_content_id(lane_spec: LaneSpec) -> str:
    if type(lane_spec) is not LaneSpec:
        raise HumanExecutionAuthorizationError(
            "lane_spec must be the exact PR-289 LaneSpec type"
        )
    return canonical_sha256(
        {
            "schema": "common.human_execution_authorization_lane_spec_binding.v1",
            "lane_spec": lane_spec.as_payload(),
        }
    )


def replay_complete_lane_admission(
    *,
    lane_spec: LaneSpec,
    admission_decision: LaneAdmissionDecision,
    candidate_identity: CandidateIdentityV1,
) -> LaneAdmissionDecision:
    """Replay one complete decision against the candidate's exact PR-289 lane."""

    if type(lane_spec) is not LaneSpec:
        raise HumanExecutionAuthorizationError(
            "lane_spec must be the exact PR-289 LaneSpec type"
        )
    if type(admission_decision) is not LaneAdmissionDecision:
        raise HumanExecutionAuthorizationError(
            "admission_decision must be the exact PR-289 LaneAdmissionDecision type"
        )
    try:
        registry = lane_registry_from_mapping(
            _strict_json_bytes(
                read_candidate_blob(
                    candidate_identity, _LANE_REGISTRY_RELATIVE_PATH.as_posix()
                ),
                field="PR-289 lane registry Git blob",
            )
        )
        registered_lane = registry.lane(lane_spec.lane_id)
    except DataIdentityError as exc:
        raise HumanExecutionAuthorizationError(
            "registered PR-289 lane registry is unavailable"
        ) from exc
    if lane_spec.as_payload() != registered_lane.as_payload():
        raise HumanExecutionAuthorizationError(
            "lane_spec is not the registered exact PR-289 lane"
        )
    if (
        admission_decision.lane_id != lane_spec.lane_id
        or admission_decision.product_id != lane_spec.product_id
        or admission_decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY
    ):
        raise HumanExecutionAuthorizationError(
            "authorization requires a complete admitted PR-289 lane"
        )
    try:
        replayed = replay_lane_admission_decision(
            admission_decision.as_payload(), registry=registry
        )
        pr289_receipt = build_not_authorized_receipt(lane_spec, replayed)
    except DataIdentityError as exc:
        raise HumanExecutionAuthorizationError("admission replay failed") from exc
    if pr289_receipt.status.value != "NOT_AUTHORIZED":
        raise HumanExecutionAuthorizationError(
            "PR-289 receipt unexpectedly promoted authorization"
        )
    return replayed


def admitted_data_identity(decision: LaneAdmissionDecision) -> str:
    if type(decision) is not LaneAdmissionDecision:
        raise HumanExecutionAuthorizationError(
            "data identity requires the exact PR-289 LaneAdmissionDecision type"
        )
    if decision.lane_admission_bundle_id is None or not decision.records:
        raise HumanExecutionAuthorizationError("admission has no data identity")
    return canonical_sha256(
        {
            "schema": "common.admitted_data_identity.v1",
            "lane_admission_bundle_id": decision.lane_admission_bundle_id,
            "records": [
                {
                    "record_id": record.record_id,
                    "component_id": record.component_id,
                    "content_sha256": record.content_sha256,
                }
                for record in decision.records
            ],
        }
    )


def admitted_covariance_identity(decision: LaneAdmissionDecision) -> str:
    if type(decision) is not LaneAdmissionDecision:
        raise HumanExecutionAuthorizationError(
            "covariance identity requires the exact PR-289 LaneAdmissionDecision type"
        )
    rows = [
        {
            "record_id": record.record_id,
            "component_id": record.component_id,
            "component_ordinal": record.component_ordinal,
            "content_sha256": record.content_sha256,
            "covariance_id": record.covariance_id,
        }
        for record in decision.records
        if "covariance" in record.component_id.casefold()
        and record.covariance_status == "REGISTERED"
    ]
    if not rows:
        raise HumanExecutionAuthorizationError(
            "admitted lane has no registered covariance component"
        )
    return canonical_sha256(
        {"schema": "common.admitted_covariance_identity.v1", "records": rows}
    )


@dataclass(frozen=True)
class HumanExecutionAuthorizationReceiptV1:
    authorization_id: str
    lane_id: str
    exact_admission_record_ids: tuple[str, ...]
    lane_admission_bundle_id: str
    analysis_plan_id: str
    required_human_gate_id: str
    authorized_scope: str
    authorization_domain: str
    model_contract_content_id: str
    runtime_environment_receipt_id: str
    computed_response_rank_receipt_id: str
    normalization_evidence_id: str
    execution_plan_content_id: str
    candidate_commit: str
    candidate_tree: str
    issued_at_utc: str
    expires_at_utc: str
    nonce: str
    signer_key_id: str
    authorization_signature_ed25519: str

    @classmethod
    def from_mapping(
        cls, payload: Mapping[str, object]
    ) -> "HumanExecutionAuthorizationReceiptV1":
        checked = _exact_mapping(
            payload,
            field="authorization receipt",
            expected=frozenset(
                {
                    "schema",
                    "authorization_id",
                    "lane_id",
                    "exact_admission_record_ids",
                    "lane_admission_bundle_id",
                    "analysis_plan_id",
                    "required_human_gate_id",
                    "authorized_scope",
                    "authorization_domain",
                    "model_contract_content_id",
                    "runtime_environment_receipt_id",
                    "computed_response_rank_receipt_id",
                    "normalization_evidence_id",
                    "execution_plan_content_id",
                    "candidate_commit",
                    "candidate_tree",
                    "issued_at_utc",
                    "expires_at_utc",
                    "nonce",
                    "signer_key_id",
                    "authorization_signature_ed25519",
                }
            ),
        )
        if checked["schema"] != AUTHORIZATION_SCHEMA:
            raise HumanExecutionAuthorizationError(
                "authorization receipt schema drifted"
            )
        _canonical_base64(
            checked["authorization_signature_ed25519"],
            field="authorization_signature_ed25519",
            byte_length=64,
        )
        receipt = cls(
            authorization_id=_sha256_identity(
                checked["authorization_id"], "authorization_id"
            ),
            lane_id=_text(checked["lane_id"], "lane_id"),
            exact_admission_record_ids=_record_ids(
                checked["exact_admission_record_ids"]
            ),
            lane_admission_bundle_id=_sha256_identity(
                checked["lane_admission_bundle_id"], "lane_admission_bundle_id"
            ),
            analysis_plan_id=_text(checked["analysis_plan_id"], "analysis_plan_id"),
            required_human_gate_id=_text(
                checked["required_human_gate_id"], "required_human_gate_id"
            ),
            authorized_scope=_text(checked["authorized_scope"], "authorized_scope"),
            authorization_domain=_text(
                checked["authorization_domain"], "authorization_domain"
            ),
            model_contract_content_id=_sha256_identity(
                checked["model_contract_content_id"], "model_contract_content_id"
            ),
            runtime_environment_receipt_id=_sha256_identity(
                checked["runtime_environment_receipt_id"],
                "runtime_environment_receipt_id",
            ),
            computed_response_rank_receipt_id=_sha256_identity(
                checked["computed_response_rank_receipt_id"],
                "computed_response_rank_receipt_id",
            ),
            normalization_evidence_id=_sha256_identity(
                checked["normalization_evidence_id"], "normalization_evidence_id"
            ),
            execution_plan_content_id=_sha256_identity(
                checked["execution_plan_content_id"], "execution_plan_content_id"
            ),
            candidate_commit=_git_object(
                checked["candidate_commit"], "candidate_commit"
            ),
            candidate_tree=_git_object(checked["candidate_tree"], "candidate_tree"),
            issued_at_utc=_utc(checked["issued_at_utc"], "issued_at_utc")[0],
            expires_at_utc=_utc(checked["expires_at_utc"], "expires_at_utc")[0],
            nonce=_nonce(checked["nonce"]),
            signer_key_id=_text(checked["signer_key_id"], "signer_key_id"),
            authorization_signature_ed25519=_text(
                checked["authorization_signature_ed25519"],
                "authorization_signature_ed25519",
            ),
        )
        if receipt.authorization_id != canonical_sha256(receipt.unsigned_payload()):
            raise HumanExecutionAuthorizationError(
                "authorization_id does not bind the unsigned receipt"
            )
        return receipt

    @classmethod
    def from_bytes(cls, raw: bytes) -> "HumanExecutionAuthorizationReceiptV1":
        return cls.from_mapping(
            _strict_json_bytes(raw, field="authorization receipt")
        )

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": AUTHORIZATION_SCHEMA,
            "lane_id": self.lane_id,
            "exact_admission_record_ids": list(self.exact_admission_record_ids),
            "lane_admission_bundle_id": self.lane_admission_bundle_id,
            "analysis_plan_id": self.analysis_plan_id,
            "required_human_gate_id": self.required_human_gate_id,
            "authorized_scope": self.authorized_scope,
            "authorization_domain": self.authorization_domain,
            "model_contract_content_id": self.model_contract_content_id,
            "runtime_environment_receipt_id": self.runtime_environment_receipt_id,
            "computed_response_rank_receipt_id": self.computed_response_rank_receipt_id,
            "normalization_evidence_id": self.normalization_evidence_id,
            "execution_plan_content_id": self.execution_plan_content_id,
            "candidate_commit": self.candidate_commit,
            "candidate_tree": self.candidate_tree,
            "issued_at_utc": self.issued_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "nonce": self.nonce,
            "signer_key_id": self.signer_key_id,
        }

    def signed_payload(self) -> dict[str, object]:
        return {"authorization_id": self.authorization_id, **self.unsigned_payload()}

    def as_payload(self) -> dict[str, object]:
        return {
            **self.signed_payload(),
            "authorization_signature_ed25519": self.authorization_signature_ed25519,
        }


@dataclass(frozen=True)
class ValidatedHumanExecutionAuthorization:
    """Non-authoritative cache of a prior validation event."""

    signed_receipt_bytes: bytes
    receipt: HumanExecutionAuthorizationReceiptV1
    replayed_lane_spec_content_id: str
    replayed_admission_bundle_id: str
    validated_candidate_identity_id: str
    validated_at_utc: str
    validation_content_id: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": VALIDATED_AUTHORIZATION_SCHEMA,
            "signed_receipt_sha256": "sha256:"
            + hashlib.sha256(self.signed_receipt_bytes).hexdigest(),
            "authorization_id": self.receipt.authorization_id,
            "replayed_lane_spec_content_id": self.replayed_lane_spec_content_id,
            "replayed_admission_bundle_id": self.replayed_admission_bundle_id,
            "validated_candidate_identity_id": self.validated_candidate_identity_id,
            "validated_at_utc": self.validated_at_utc,
        }

    def as_payload(self) -> dict[str, object]:
        return {
            **self.unsigned_payload(),
            "validation_content_id": self.validation_content_id,
        }


def validate_authorization_execution_bindings(
    receipt: HumanExecutionAuthorizationReceiptV1,
    *,
    model_contract_content_id: object,
    runtime_environment_receipt_id: object,
    computed_response_rank_receipt_id: object,
    normalization_evidence_id: object,
    execution_plan_content_id: object,
) -> None:
    """Compare signed plan/runtime/model bindings without granting authority."""

    if type(receipt) is not HumanExecutionAuthorizationReceiptV1:
        raise HumanExecutionAuthorizationError(
            "authorization binding check requires the exact receipt type"
        )
    expected = (
        _sha256_identity(model_contract_content_id, "model_contract_content_id"),
        _sha256_identity(
            runtime_environment_receipt_id, "runtime_environment_receipt_id"
        ),
        _sha256_identity(
            computed_response_rank_receipt_id,
            "computed_response_rank_receipt_id",
        ),
        _sha256_identity(normalization_evidence_id, "normalization_evidence_id"),
        _sha256_identity(execution_plan_content_id, "execution_plan_content_id"),
    )
    observed = (
        receipt.model_contract_content_id,
        receipt.runtime_environment_receipt_id,
        receipt.computed_response_rank_receipt_id,
        receipt.normalization_evidence_id,
        receipt.execution_plan_content_id,
    )
    if observed != expected:
        raise HumanExecutionAuthorizationError(
            "authorization execution/model plan binding mismatched"
        )

@dataclass(frozen=True)
class _TrustedAuthority:
    lane_id: str
    key_id: str
    public_key: bytes
    gate_id: str
    scope: str


def _load_trusted_authority(
    lane_spec: LaneSpec, candidate_identity: CandidateIdentityV1
) -> _TrustedAuthority:
    # Candidate-resident code and registry bytes cannot establish their own
    # trust root.  PR-304 deliberately has no authority-producing path: a
    # root-owned launcher must verify the externally signed registry and must
    # directly control nonce consumption and process start in the later
    # transaction.  Keeping this rejection inside the legacy diagnostic API
    # prevents an ACTIVE row committed by an attacker from becoming authority.
    del lane_spec, candidate_identity
    raise ExternalTrustedLauncherRequired(
        "external trusted launcher validation is required; "
        "candidate-local authority registry is diagnostic only"
    )


def _load_candidate_local_authority_for_diagnostics(
    lane_spec: LaneSpec, candidate_identity: CandidateIdentityV1
) -> _TrustedAuthority:
    """Parse candidate-local public metadata without granting authority."""

    payload = _strict_json_bytes(
        read_candidate_blob(
            candidate_identity, _AUTHORITY_REGISTRY_RELATIVE_PATH.as_posix()
        ),
        field="human authority registry Git blob",
    )
    checked = _exact_mapping(
        payload,
        field="human authority registry",
        expected=frozenset({"schema", "lane_order", "authorities"}),
    )
    if checked["schema"] != AUTHORITY_REGISTRY_SCHEMA:
        raise HumanExecutionAuthorizationError("human authority registry drifted")
    lane_order = checked["lane_order"]
    authorities = checked["authorities"]
    if (
        isinstance(lane_order, (str, bytes))
        or not isinstance(lane_order, Sequence)
        or tuple(lane_order) != _LANE_ORDER
        or not isinstance(authorities, Mapping)
        or tuple(authorities) != _LANE_ORDER
    ):
        raise HumanExecutionAuthorizationError(
            "human authority lane inventory drifted"
        )
    row = _exact_mapping(
        authorities[lane_spec.lane_id],
        field="human authority row",
        expected=frozenset(
            {"status", "key_id", "public_key_base64", "gate_id", "scope"}
        ),
    )
    if (
        row["gate_id"] != lane_spec.required_human_gate_id
        or row["scope"] != _SCOPES_BY_LANE[lane_spec.lane_id]
    ):
        raise HumanExecutionAuthorizationError(
            "human authority gate or scope drifted"
        )
    if row["status"] != "ACTIVE":
        raise HumanExecutionAuthorizationError(
            "trusted human signer is not active for lane"
        )
    key_id = _text(row["key_id"], "authority key_id")
    public_key = _canonical_base64(
        row["public_key_base64"], field="authority public_key_base64", byte_length=32
    )
    return _TrustedAuthority(
        lane_id=lane_spec.lane_id,
        key_id=key_id,
        public_key=public_key,
        gate_id=lane_spec.required_human_gate_id,
        scope=_SCOPES_BY_LANE[lane_spec.lane_id],
    )


def _validate_signed_authorization(
    *,
    signed_receipt_bytes: bytes,
    lane_spec: LaneSpec,
    admission_decision: LaneAdmissionDecision,
    candidate_identity: CandidateIdentityV1,
    evaluated: datetime,
) -> tuple[
    HumanExecutionAuthorizationReceiptV1,
    LaneAdmissionDecision,
    CandidateIdentityV1,
]:
    candidate = revalidate_clean_candidate_identity(candidate_identity)
    replayed = replay_complete_lane_admission(
        lane_spec=lane_spec,
        admission_decision=admission_decision,
        candidate_identity=candidate,
    )
    receipt = HumanExecutionAuthorizationReceiptV1.from_bytes(signed_receipt_bytes)
    if signed_receipt_bytes != _canonical_bytes(receipt.as_payload()):
        raise HumanExecutionAuthorizationError(
            "authorization receipt bytes are not canonical"
        )
    expected_record_ids = tuple(record.record_id for record in replayed.records)
    if receipt.lane_id != lane_spec.lane_id:
        raise HumanExecutionAuthorizationError(
            "authorization lane does not match replayed admission"
        )
    if receipt.exact_admission_record_ids != expected_record_ids:
        raise HumanExecutionAuthorizationError(
            "authorization record ordering or membership drifted"
        )
    if receipt.lane_admission_bundle_id != replayed.lane_admission_bundle_id:
        raise HumanExecutionAuthorizationError(
            "authorization admission bundle drifted"
        )
    if receipt.analysis_plan_id != lane_spec.analysis_plan_id:
        raise HumanExecutionAuthorizationError("authorization analysis plan drifted")
    if receipt.required_human_gate_id != lane_spec.required_human_gate_id:
        raise HumanExecutionAuthorizationError("authorization human gate drifted")
    if receipt.authorization_domain != AUTHORIZATION_DOMAIN:
        raise HumanExecutionAuthorizationError(
            "authorization domain is not registered"
        )
    if receipt.authorized_scope != _SCOPES_BY_LANE.get(lane_spec.lane_id):
        raise HumanExecutionAuthorizationError(
            "authorization scope is not registered for the lane"
        )
    if (
        receipt.candidate_commit != candidate.commit
        or receipt.candidate_tree != candidate.tree
    ):
        raise HumanExecutionAuthorizationError(
            "authorization candidate identity does not match clean Git state"
        )
    _, issued = _utc(receipt.issued_at_utc, "issued_at_utc")
    _, expires = _utc(receipt.expires_at_utc, "expires_at_utc")
    if expires <= issued:
        raise HumanExecutionAuthorizationError(
            "authorization interval is empty or reversed"
        )
    if expires - issued > MAX_AUTHORIZATION_TTL:
        raise HumanExecutionAuthorizationError(
            "authorization TTL exceeds 1800 seconds"
        )
    if issued > evaluated:
        raise HumanExecutionAuthorizationError(
            "authorization issue time is in the future"
        )
    if not issued <= evaluated < expires:
        raise HumanExecutionAuthorizationError(
            "authorization is expired at evaluation"
        )
    authority = _load_trusted_authority(lane_spec, candidate)
    if receipt.signer_key_id != authority.key_id:
        raise HumanExecutionAuthorizationError(
            "authorization signer is not the independently trusted human signer"
        )
    signature = _canonical_base64(
        receipt.authorization_signature_ed25519,
        field="authorization_signature_ed25519",
        byte_length=64,
    )
    try:
        Ed25519PublicKey.from_public_bytes(authority.public_key).verify(
            signature, _canonical_bytes(receipt.signed_payload())
        )
    except (InvalidSignature, ValueError) as exc:
        raise HumanExecutionAuthorizationError(
            "authorization Ed25519 signature is forged or mismatched"
        ) from exc
    return receipt, replayed, candidate


def validate_human_execution_authorization(
    *,
    signed_receipt_bytes: bytes,
    lane_spec: LaneSpec,
    admission_decision: LaneAdmissionDecision,
    candidate_identity: CandidateIdentityV1,
) -> ValidatedHumanExecutionAuthorization:
    """Validate a signed receipt and return non-authoritative cache evidence."""

    evaluated_at_utc, evaluated = _trusted_evaluation_time()
    receipt, replayed, candidate = _validate_signed_authorization(
        signed_receipt_bytes=signed_receipt_bytes,
        lane_spec=lane_spec,
        admission_decision=admission_decision,
        candidate_identity=candidate_identity,
        evaluated=evaluated,
    )
    unsigned = {
        "schema": VALIDATED_AUTHORIZATION_SCHEMA,
        "signed_receipt_sha256": "sha256:"
        + hashlib.sha256(signed_receipt_bytes).hexdigest(),
        "authorization_id": receipt.authorization_id,
        "replayed_lane_spec_content_id": lane_spec_content_id(lane_spec),
        "replayed_admission_bundle_id": replayed.lane_admission_bundle_id,
        "validated_candidate_identity_id": candidate.candidate_identity_id,
        "validated_at_utc": evaluated_at_utc,
    }
    return ValidatedHumanExecutionAuthorization(
        signed_receipt_bytes=signed_receipt_bytes,
        receipt=receipt,
        replayed_lane_spec_content_id=str(unsigned["replayed_lane_spec_content_id"]),
        replayed_admission_bundle_id=str(unsigned["replayed_admission_bundle_id"]),
        validated_candidate_identity_id=candidate.candidate_identity_id,
        validated_at_utc=evaluated_at_utc,
        validation_content_id=canonical_sha256(unsigned),
    )


def revalidate_cached_human_execution_authorization(
    *,
    cached: ValidatedHumanExecutionAuthorization,
    lane_spec: LaneSpec,
    admission_decision: LaneAdmissionDecision,
    candidate_identity: CandidateIdentityV1,
) -> HumanExecutionAuthorizationReceiptV1:
    """Reverify signed bytes; cached fields are never execution authority."""

    if type(cached) is not ValidatedHumanExecutionAuthorization:
        raise HumanExecutionAuthorizationError(
            "authorization cache must use the exact PR-304 cache type"
        )
    signed_receipt_bytes = getattr(cached, "signed_receipt_bytes", None)
    if type(signed_receipt_bytes) is not bytes:
        raise HumanExecutionAuthorizationError(
            "authorization cache lacks signed receipt bytes"
        )
    _, evaluated = _trusted_evaluation_time()
    receipt, _, _ = _validate_signed_authorization(
        signed_receipt_bytes=signed_receipt_bytes,
        lane_spec=lane_spec,
        admission_decision=admission_decision,
        candidate_identity=candidate_identity,
        evaluated=evaluated,
    )
    return receipt


__all__ = [
    "AUTHORIZATION_DOMAIN",
    "AUTHORIZATION_SCHEMA",
    "CandidateIdentityV1",
    "EXTERNAL_TRUST_ROOT_FINGERPRINT",
    "EXTERNAL_TRUST_ROOT_PUBLIC_KEY",
    "ExternalTrustedLauncherRequired",
    "HumanExecutionAuthorizationError",
    "HumanExecutionAuthorizationReceiptV1",
    "MAX_AUTHORIZATION_TTL",
    "TRUSTED_LAUNCHER",
    "ValidatedHumanExecutionAuthorization",
    "admitted_covariance_identity",
    "admitted_data_identity",
    "build_clean_candidate_identity",
    "candidate_blob_binding",
    "lane_spec_content_id",
    "replay_complete_lane_admission",
    "read_candidate_blob",
    "revalidate_cached_human_execution_authorization",
    "revalidate_clean_candidate_identity",
    "validate_human_execution_authorization",
    "validate_authorization_execution_bindings",
]
