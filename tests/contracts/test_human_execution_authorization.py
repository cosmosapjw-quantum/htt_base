from __future__ import annotations

import base64
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import inspect
import io
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
from types import SimpleNamespace

import numpy as np
import pytest

from common.data_identity import (
    _build_registered_native_profile,
    AdmissionStatus,
    build_not_authorized_receipt,
    canonical_sha256,
    compute_source_locator_identity,
    evaluate_lane_identity,
    load_lane_registry,
)
import common.human_execution_authorization as authorization
from common.human_execution_authorization import (
    AUTHORIZATION_DOMAIN,
    AUTHORIZATION_SCHEMA,
    CandidateIdentityV1,
    EXTERNAL_TRUST_ROOT_FINGERPRINT,
    EXTERNAL_TRUST_ROOT_PUBLIC_KEY,
    HumanExecutionAuthorizationError,
    HumanExecutionAuthorizationReceiptV1,
    TRUSTED_LAUNCHER,
    ValidatedHumanExecutionAuthorization,
    admitted_covariance_identity,
    admitted_data_identity,
    build_clean_candidate_identity,
    revalidate_cached_human_execution_authorization,
    read_candidate_blob,
    validate_authorization_execution_bindings,
    validate_human_execution_authorization,
)
from htt.infer.bayesian_production import (
    LaneReadinessStatus,
    ObservationalLaneDescriptor,
    ProductionBayesianError,
    assess_lane_readiness,
    bind_production_model_contract,
    build_posterior_consumer_plan,
    build_production_model_contract,
    build_sampler_posterior_lineage,
    capture_runtime_environment_receipt,
    revalidate_bound_production_model_contract,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = (
    ROOT
    / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
STALE_RECEIPT = ROOT / "docs/generated/pr289_data_identity_v2_receipt.json"
EVALUATED = "2026-08-22T12:00:00Z"
VALID_NONCE = "nonce:v1:" + hashlib.sha256(b"pr304-hostile-test-nonce").hexdigest()
TRUSTED_KEY_ID = "H-ACT-OWNER-ED25519-V1"
TEST_PUBLIC_KEY = bytes(range(32))
TEST_SIGNATURE = bytes(range(64))


def _canonical(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _candidate_repo(tmp_path: Path) -> tuple[CandidateIdentityV1, SimpleNamespace]:
    repo = (tmp_path / "candidate").resolve()
    repo.mkdir()
    _git(repo, "init", "-b", "pr304-test-candidate")
    _git(repo, "config", "user.name", "PR304 Test")
    _git(repo, "config", "user.email", "pr304-test@example.invalid")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "tag.gpgsign", "false")
    _git(repo, "config", "core.hooksPath", "/dev/null")
    source = repo / "provider.py"
    source.write_text(
        "def log_likelihood(theta):\n"
        "    return -float((theta * theta).sum())\n\n"
        "def prior_transform(unit):\n"
        "    return unit\n\n"
        "def replicate_generator(theta, rng):\n"
        "    return theta + rng.normal(size=len(theta))\n\n"
        "def discrepancy(observed, replicated):\n"
        "    return float((observed - replicated).sum())\n",
        encoding="utf-8",
    )
    (repo / "provider-config.json").write_text(
        '{"model":"act-contract-test","version":1}\n', encoding="utf-8"
    )
    runtime = capture_runtime_environment_receipt(("numpy", "cryptography"))
    (repo / "environment.lock").write_text(
        json.dumps(
            {
                "schema": "htt.runtime_environment_contract.v1",
                "required_packages": ["numpy", "cryptography"],
                "expected_receipt": runtime.as_payload(),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "response-matrix.json").write_text(
        json.dumps(
            {
                "schema": "htt.response_matrix.v1",
                "feature_order": ["act-amplitude"],
                "parameter_order": ["amplitude"],
                "matrix": [[1.0]],
                "singular_value_threshold": 1.0e-12,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "normalization-evidence.json").write_text(
        json.dumps(
            {
                "schema": "htt.normalization_evidence.v1",
                "likelihood": {
                    "status": "ANALYTICALLY_NORMALIZED",
                    "identity": "sha256:" + "1" * 64,
                    "method_id": "analytic-gaussian-v1",
                },
                "prior": {
                    "status": "ANALYTICALLY_NORMALIZED",
                    "identity": "sha256:" + "2" * 64,
                    "method_id": "unit-cube-transform-v1",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "execution-plan.json").write_text(
        json.dumps(
            {
                "schema": "htt.execution_plan.v1",
                "lane_id": "H-ACT",
                "model_id": "act-admission-bound-test-model",
                "entrypoint": "provider.py:log_likelihood",
                "argv": ["--mode", "sampler"],
                "output_root": "docs/generated/observed_runs/act-test",
                "run_mode": "sampler",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "provider-manifest.json").write_text(
        json.dumps(
            {
                "schema": "htt.provider_manifest.v1",
                "provider_path": "provider.py",
                "dependency_paths": [],
                "configuration_path": "provider-config.json",
                "environment_contract_path": "environment.lock",
                "response_matrix_path": "response-matrix.json",
                "normalization_evidence_path": "normalization-evidence.json",
                "execution_plan_path": "execution-plan.json",
                "exports": {
                    "log_likelihood": "log_likelihood",
                    "prior_transform": "prior_transform",
                    "replicate_generator": "replicate_generator",
                    "discrepancies": {"amplitude": "discrepancy"},
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    candidate_registry = repo / REGISTRY.relative_to(ROOT)
    candidate_registry.parent.mkdir(parents=True)
    shutil.copyfile(REGISTRY, candidate_registry)
    authority_registry = (
        repo
        / "docs/research_program/post_pr275/human_authority_registry.json"
    )
    shutil.copyfile(
        ROOT / "docs/research_program/post_pr275/human_authority_registry.json",
        authority_registry,
    )
    _git(repo, "add", "--all")
    _git(repo, "commit", "-m", "test candidate")
    provider = SimpleNamespace(
        source_path="provider.py",
        manifest_path="provider-manifest.json",
    )
    return build_clean_candidate_identity(repo), provider


def _commit_json_mutation(
    candidate: CandidateIdentityV1,
    relative_path: str,
    mutate,
    *,
    message: str,
) -> CandidateIdentityV1:
    path = candidate.repo_root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    _git(candidate.repo_root, "add", "--", relative_path)
    _git(candidate.repo_root, "commit", "-m", message)
    return build_clean_candidate_identity(candidate.repo_root)


def _admitted_act(tmp_path: Path, *, payload_tag: str = "baseline"):
    registry = load_lane_registry(REGISTRY)
    lane = registry.lane("ACT")
    root = (tmp_path / "act-input").resolve()
    root.mkdir(parents=True)
    components: list[dict[str, object]] = []
    for ordinal, component_id in enumerate(lane.expected_component_sequence):
        relative = f"components/{ordinal:02d}-{component_id}.bin"
        path = root / relative
        path.parent.mkdir(exist_ok=True)
        raw = f"ACT:{payload_tag}:{component_id}:{ordinal}\n".encode("ascii")
        path.write_bytes(raw)
        components.append(
            {
                "component_id": component_id,
                "relative_path": relative,
                "byte_size": len(raw),
                "content_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    evidence: dict[str, object] = {
        "schema": "common.data_identity_evidence.v2",
        "lane_id": lane.lane_id,
        "product_id": lane.product_id,
        "source_locator_identity": "pending",
        "release_name": "ACT registered product",
        "release_version": "ACT-v1",
        "release_identity": "docs:pr304/act-release-v1",
        "license_identity": "spdx:CC-BY-4.0",
        "license_status": "BOUND",
        "units_contract_id": "units:ACT:v1",
        "coordinate_frame_id": "frame:ACT:v1",
        "sign_orientation_convention_id": "sign:ACT:v1",
        "directional_convention_id": "direction:ACT:v1",
        "harmonic_convention_id": "harmonic:ACT:v1",
        "mask_id": "mask:ACT:v1",
        "selection_id": "selection:ACT:v1",
        "sky_support_id": "sky:ACT:v1",
        "covariance_id": "covariance:ACT:v1",
        "covariance_status": "REGISTERED",
        "null_ensemble_id": "null:ACT:v1",
        "null_ensemble_status": "REGISTERED",
        "transfer_source": "none",
        "transfer_function_spec_id": "none",
        "transfer_provenance_status": "NOT_APPLICABLE",
        "sky_support_status": "REGISTERED",
        "native_identity_profile": {},
    }
    evidence["native_identity_profile"] = _build_registered_native_profile(
        lane, components, evidence
    )
    evidence["source_locator_identity"] = compute_source_locator_identity(
        lane_id=lane.lane_id,
        product_id=lane.product_id,
        components=components,
        evidence_bindings=evidence,
    )
    evidence_path = root / "identity/evidence.json"
    evidence_path.parent.mkdir()
    evidence_path.write_text(
        json.dumps(evidence, sort_keys=True) + "\n", encoding="utf-8"
    )
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id=lane.lane_id,
        descriptor={
            "root": str(root),
            "evidence_relative_path": "identity/evidence.json",
            "evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            "components": components,
            "acquisition_status": "COMPLETE",
            "name_only": False,
        },
        inspected_at_utc="2026-08-22T11:00:00Z",
    )
    assert decision.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY
    return lane, decision


def _activate_candidate_authority(
    candidate: CandidateIdentityV1,
    public_key: bytes,
) -> CandidateIdentityV1:
    assert len(public_key) == 32

    def activate(payload: dict[str, object]) -> None:
        authorities = payload["authorities"]
        assert isinstance(authorities, dict)
        row = authorities["ACT"]
        assert isinstance(row, dict)
        row.update(
            {
                "status": "ACTIVE",
                "key_id": TRUSTED_KEY_ID,
                "public_key_base64": base64.b64encode(public_key).decode("ascii"),
            }
        )

    return _commit_json_mutation(
        candidate,
        "docs/research_program/post_pr275/human_authority_registry.json",
        activate,
        message="activate candidate-controlled authority",
    )


def _signed_receipt(
    lane,
    decision,
    candidate: CandidateIdentityV1,
    public_key_fixture: bytes,
    *,
    signer_key_id: str = TRUSTED_KEY_ID,
    **overrides: object,
) -> bytes:
    assert len(public_key_fixture) == 32
    unsigned: dict[str, object] = {
        "schema": AUTHORIZATION_SCHEMA,
        "lane_id": lane.lane_id,
        "exact_admission_record_ids": [record.record_id for record in decision.records],
        "lane_admission_bundle_id": decision.lane_admission_bundle_id,
        "analysis_plan_id": lane.analysis_plan_id,
        "required_human_gate_id": lane.required_human_gate_id,
        "authorized_scope": "admitted_act_observed_execution",
        "authorization_domain": AUTHORIZATION_DOMAIN,
        "model_contract_content_id": "sha256:" + "3" * 64,
        "runtime_environment_receipt_id": "sha256:" + "4" * 64,
        "computed_response_rank_receipt_id": "sha256:" + "5" * 64,
        "normalization_evidence_id": "sha256:" + "6" * 64,
        "execution_plan_content_id": "sha256:" + "7" * 64,
        "candidate_commit": candidate.commit,
        "candidate_tree": candidate.tree,
        "issued_at_utc": "2026-08-22T11:45:00Z",
        "expires_at_utc": "2026-08-22T12:15:00Z",
        "nonce": VALID_NONCE,
        "signer_key_id": signer_key_id,
    }
    unsigned.update(overrides)
    authorization_id = canonical_sha256(unsigned)
    signed = {"authorization_id": authorization_id, **unsigned}
    return _canonical(
        {
            **signed,
            "authorization_signature_ed25519": base64.b64encode(
                TEST_SIGNATURE
            ).decode("ascii"),
        }
    )


def _validate(raw: bytes, lane, decision, candidate: CandidateIdentityV1):
    return validate_human_execution_authorization(
        signed_receipt_bytes=raw,
        lane_spec=lane,
        admission_decision=decision,
        candidate_identity=candidate,
    )


@pytest.fixture(autouse=True)
def _fixed_trusted_authorization_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed = datetime.strptime(EVALUATED, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    monkeypatch.setattr(authorization, "_trusted_now_utc", lambda: fixed)


def _bound_model(lane, decision, candidate: CandidateIdentityV1, provider):
    base = build_production_model_contract(
        lane_id="H-ACT",
        model_id="act-admission-bound-test-model",
        parameter_schema={"amplitude": {"support": "real", "role": "signal"}},
        likelihood_identity="sha256:" + "1" * 64,
        prior_identity="sha256:" + "2" * 64,
        data_identity=admitted_data_identity(decision),
        covariance_identity=admitted_covariance_identity(decision),
        block_ids=("act-block-a", "act-block-b"),
        discrepancy_ids=("amplitude",),
    )
    return bind_production_model_contract(
        contract=base,
        lane_spec=lane,
        admission_decision=decision,
        candidate_identity=candidate,
        provider_manifest_path=Path(provider.manifest_path),
    )


def test_admission_identity_helpers_reject_foreign_duck_types() -> None:
    foreign = SimpleNamespace(
        lane_admission_bundle_id="sha256:" + "0" * 64,
        records=(),
    )
    for helper in (admitted_data_identity, admitted_covariance_identity):
        with pytest.raises(
            HumanExecutionAuthorizationError,
            match="exact PR-289 LaneAdmissionDecision",
        ):
            helper(foreign)


def test_candidate_local_ed25519_receipt_cannot_create_authority_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = TEST_PUBLIC_KEY
    candidate = _activate_candidate_authority(candidate, signer)
    raw = _signed_receipt(lane, decision, candidate, signer)
    with pytest.raises(
        HumanExecutionAuthorizationError, match="external trusted launcher"
    ):
        _validate(raw, lane, decision, candidate)
    assert build_clean_candidate_identity(candidate.repo_root) == candidate


def test_candidate_tree_supplies_lane_and_public_authority_registries(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    replayed = authorization.replay_complete_lane_admission(
        lane_spec=lane,
        admission_decision=decision,
        candidate_identity=candidate,
    )
    assert replayed.lane_admission_bundle_id == decision.lane_admission_bundle_id

    signer = TEST_PUBLIC_KEY
    raw = _signed_receipt(lane, decision, candidate, signer)
    with pytest.raises(
        HumanExecutionAuthorizationError, match="external trusted launcher"
    ):
        _validate(raw, lane, decision, candidate)


def test_auth_trust_001_rejects_arbitrary_self_signed_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    attacker = TEST_PUBLIC_KEY
    raw = _signed_receipt(
        lane,
        decision,
        candidate,
        attacker,
        signer_key_id="ATTACKER-SELF-SIGNED-ED25519",
    )
    with pytest.raises(
        HumanExecutionAuthorizationError, match="external trusted launcher"
    ):
        _validate(raw, lane, decision, candidate)


def test_auth_trust_002_rejects_registered_signer_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    original = TEST_PUBLIC_KEY
    raw = _signed_receipt(lane, decision, candidate, original)
    with pytest.raises(
        HumanExecutionAuthorizationError, match="external trusted launcher"
    ):
        _validate(raw, lane, decision, candidate)


def test_production_registry_is_fail_closed_pending_human_provisioning(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    attacker = TEST_PUBLIC_KEY
    with pytest.raises(
        HumanExecutionAuthorizationError, match="external trusted launcher"
    ):
        _validate(
            _signed_receipt(lane, decision, candidate, attacker),
            lane,
            decision,
            candidate,
        )


@pytest.mark.parametrize(
    ("mutation", "match"),
    (
        (lambda payload: payload.__setitem__("lane_id", "PLANCK"), "lane does not match"),
        (
            lambda payload: payload.__setitem__(
                "exact_admission_record_ids",
                list(reversed(payload["exact_admission_record_ids"])),
            ),
            "ordering or membership",
        ),
        (
            lambda payload: payload.__setitem__(
                "exact_admission_record_ids", payload["exact_admission_record_ids"][:-1]
            ),
            "ordering or membership",
        ),
        (
            lambda payload: payload.__setitem__(
                "exact_admission_record_ids",
                [payload["exact_admission_record_ids"][0]] * 2,
            ),
            "unique",
        ),
        (
            lambda payload: payload.__setitem__(
                "lane_admission_bundle_id", "sha256:" + "0" * 64
            ),
            "admission bundle",
        ),
        (lambda payload: payload.__setitem__("analysis_plan_id", "plan:wrong"), "analysis plan"),
        (lambda payload: payload.__setitem__("required_human_gate_id", "H-WRONG"), "human gate"),
        (lambda payload: payload.__setitem__("authorized_scope", "unknown_scope"), "scope"),
        (lambda payload: payload.__setitem__("authorization_domain", "unknown_domain"), "domain"),
        (lambda payload: payload.__setitem__("candidate_commit", "c" * 40), "candidate identity"),
        (lambda payload: payload.__setitem__("candidate_tree", "d" * 40), "candidate identity"),
    ),
)
def test_rejects_resigned_binding_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
    match: str,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = TEST_PUBLIC_KEY
    baseline = json.loads(_signed_receipt(lane, decision, candidate, signer))
    unsigned = {
        key: value
        for key, value in baseline.items()
        if key
        not in {"authorization_id", "authorization_signature_ed25519", "schema"}
    }
    mutation(unsigned)
    raw = _signed_receipt(lane, decision, candidate, signer, **unsigned)
    with pytest.raises(HumanExecutionAuthorizationError, match=match):
        _validate(raw, lane, decision, candidate)


@pytest.mark.parametrize(
    ("issued", "expires", "match"),
    (
        ("2026-08-22T12:01:00Z", "2026-08-22T12:10:00Z", "future"),
        ("2026-08-22T11:29:00Z", "2026-08-22T11:59:00Z", "expired"),
        ("2026-08-22T11:00:00Z", "2026-08-22T11:30:01Z", "TTL"),
        (EVALUATED, EVALUATED, "empty or reversed"),
    ),
)
def test_rejects_invalid_time_intervals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    issued: str,
    expires: str,
    match: str,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = TEST_PUBLIC_KEY
    raw = _signed_receipt(
        lane,
        decision,
        candidate,
        signer,
        issued_at_utc=issued,
        expires_at_utc=expires,
    )
    with pytest.raises(HumanExecutionAuthorizationError, match=match):
        validate_human_execution_authorization(
            signed_receipt_bytes=raw,
            lane_spec=lane,
            admission_decision=decision,
            candidate_identity=candidate,
        )


@pytest.mark.parametrize(
    "bad_nonce",
    (
        "short",
        " nonce:v1:" + "a" * 64,
        "nonce:v1:" + "A" * 64,
        "nonce:v1:" + "a" * 63,
        "nonce:v1:" + "0" * 63 + "g",
    ),
)
def test_auth_nonce_001_rejects_noncanonical_nonce(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    bad_nonce: str,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = TEST_PUBLIC_KEY
    with pytest.raises(HumanExecutionAuthorizationError, match="nonce:v1"):
        _validate(
            _signed_receipt(lane, decision, candidate, signer, nonce=bad_nonce),
            lane,
            decision,
            candidate,
        )


def test_auth_nonce_002_accepts_canonical_shape_without_claiming_entropy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = TEST_PUBLIC_KEY

    raw = _signed_receipt(
        lane,
        decision,
        candidate,
        signer,
        nonce="nonce:v1:" + "ab" * 32,
    )
    with pytest.raises(HumanExecutionAuthorizationError, match="external trusted launcher"):
        _validate(raw, lane, decision, candidate)


def test_auth_json_001_rejects_duplicate_and_noncanonical_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = TEST_PUBLIC_KEY
    raw = _signed_receipt(lane, decision, candidate, signer)
    duplicate = raw.replace(
        b'{"analysis_plan_id"',
        b'{"nonce":"nonce:v1:' + b"b" * 64 + b'","analysis_plan_id"',
        1,
    )
    with pytest.raises(HumanExecutionAuthorizationError, match="duplicate key"):
        _validate(duplicate, lane, decision, candidate)
    with pytest.raises(HumanExecutionAuthorizationError, match="not canonical"):
        _validate(raw + b"\n", lane, decision, candidate)


def test_auth_candidate_001_rejects_fake_and_dirty_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = TEST_PUBLIC_KEY
    raw = _signed_receipt(lane, decision, candidate, signer)
    forged = CandidateIdentityV1(
        repo_root=candidate.repo_root,
        branch=candidate.branch,
        commit="a" * 40,
        tree="b" * 40,
        candidate_identity_id="sha256:" + "c" * 64,
    )
    with pytest.raises(HumanExecutionAuthorizationError, match="stale or forged"):
        _validate(raw, lane, decision, forged)
    (candidate.repo_root / "dirty-untracked.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(HumanExecutionAuthorizationError, match="dirty"):
        _validate(raw, lane, decision, candidate)


def test_auth_cap_001_and_002_forged_cache_is_not_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    attacker = TEST_PUBLIC_KEY
    attacker_raw = _signed_receipt(lane, decision, candidate, attacker)
    parsed = HumanExecutionAuthorizationReceiptV1.from_bytes(attacker_raw)
    assert not hasattr(authorization, "_VALIDATION_TOKEN")
    forged = ValidatedHumanExecutionAuthorization(
        signed_receipt_bytes=attacker_raw,
        receipt=parsed,
        replayed_lane_spec_content_id="sha256:" + "1" * 64,
        replayed_admission_bundle_id=decision.lane_admission_bundle_id,
        validated_candidate_identity_id=candidate.candidate_identity_id,
        validated_at_utc=EVALUATED,
        validation_content_id="sha256:" + "2" * 64,
    )
    with pytest.raises(
        HumanExecutionAuthorizationError, match="external trusted launcher"
    ):
        revalidate_cached_human_execution_authorization(
            cached=forged,
            lane_spec=lane,
            admission_decision=decision,
            candidate_identity=candidate,
        )
    raw_forged = object.__new__(ValidatedHumanExecutionAuthorization)
    object.__setattr__(raw_forged, "signed_receipt_bytes", attacker_raw)
    with pytest.raises(
        HumanExecutionAuthorizationError, match="external trusted launcher"
    ):
        revalidate_cached_human_execution_authorization(
            cached=raw_forged,
            lane_spec=lane,
            admission_decision=decision,
            candidate_identity=candidate,
        )


def test_auth_time_001_rejects_cache_after_expiry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = TEST_PUBLIC_KEY
    raw = _signed_receipt(lane, decision, candidate, signer)
    cache = ValidatedHumanExecutionAuthorization(
        signed_receipt_bytes=raw,
        receipt=HumanExecutionAuthorizationReceiptV1.from_bytes(raw),
        replayed_lane_spec_content_id="sha256:" + "1" * 64,
        replayed_admission_bundle_id=decision.lane_admission_bundle_id,
        validated_candidate_identity_id=candidate.candidate_identity_id,
        validated_at_utc=EVALUATED,
        validation_content_id="sha256:" + "2" * 64,
    )
    expired = datetime(2026, 8, 22, 12, 16, tzinfo=timezone.utc)
    monkeypatch.setattr(authorization, "_trusted_now_utc", lambda: expired)
    with pytest.raises(HumanExecutionAuthorizationError, match="expired"):
        revalidate_cached_human_execution_authorization(
            cached=cache,
            lane_spec=lane,
            admission_decision=decision,
            candidate_identity=candidate,
        )


def test_auth_time_002_public_authority_apis_reject_caller_backdating() -> None:
    for authority_use in (
        validate_human_execution_authorization,
        revalidate_cached_human_execution_authorization,
        assess_lane_readiness,
    ):
        assert "evaluated_at_utc" not in inspect.signature(authority_use).parameters


def test_auth_pr289_001_rejects_not_authorized_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = TEST_PUBLIC_KEY
    pr289 = build_not_authorized_receipt(lane, decision)
    with pytest.raises(HumanExecutionAuthorizationError, match="fields drifted"):
        _validate(_canonical(pr289.as_payload()), lane, decision, candidate)


def test_rejects_refused_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, admitted = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = TEST_PUBLIC_KEY
    refused = evaluate_lane_identity(
        registry=load_lane_registry(REGISTRY),
        lane_id="ACT",
        descriptor=None,
        inspected_at_utc="2026-08-22T11:00:00Z",
    )
    assert refused.status is AdmissionStatus.REJECTED_NOT_PRESENT
    with pytest.raises(HumanExecutionAuthorizationError, match="complete admitted"):
        _validate(
            _signed_receipt(lane, admitted, candidate, signer),
            lane,
            refused,
            candidate,
        )


def test_readiness_keeps_bound_model_blocked_for_external_trusted_launcher(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    model = _bound_model(lane, decision, candidate, provider)
    descriptor = ObservationalLaneDescriptor("H-ACT", ("provider.py",))
    result = assess_lane_readiness(
        descriptor,
        model_contract=model,
        admission_decision=decision,
        candidate_identity=candidate,
    )
    assert result.status is LaneReadinessStatus.BLOCKED_HUMAN_AUTHORIZATION
    assert result.blocked_reasons == ("external_trusted_launcher_required",)
    assert result.observed_data_executed is False
    assert model.lane_admission_bundle_id == decision.lane_admission_bundle_id
    assert model.ordered_admission_record_ids == tuple(
        record.record_id for record in decision.records
    )
    assert model.admitted_covariance_identity == admitted_covariance_identity(
        decision
    )
    assert model.runtime_environment_receipt_id is not None
    assert model.computed_response_rank_receipt_id is not None
    assert model.normalization_evidence_id is not None
    assert model.execution_plan_content_id is not None


def test_model_bind_001_rejects_bundle_a_model_b(
    tmp_path: Path,
) -> None:
    lane_a, decision_a = _admitted_act(
        tmp_path / "admission-a", payload_tag="bundle-a"
    )
    lane_b, decision_b = _admitted_act(
        tmp_path / "admission-b", payload_tag="bundle-b"
    )
    candidate, provider = _candidate_repo(tmp_path)
    model_a = _bound_model(lane_a, decision_a, candidate, provider)
    assert decision_a.lane_admission_bundle_id != decision_b.lane_admission_bundle_id
    with pytest.raises(ProductionBayesianError, match="binding failed"):
        assess_lane_readiness(
            ObservationalLaneDescriptor("H-ACT", ("provider.py",)),
            model_contract=model_a,
            admission_decision=decision_b,
            candidate_identity=candidate,
        )
    assert lane_a.as_payload() == lane_b.as_payload()


def test_model_bind_002_rejects_covariance_mismatch(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    base = build_production_model_contract(
        lane_id="H-ACT",
        model_id="wrong-covariance-model",
        parameter_schema={"amplitude": {"support": "real"}},
        likelihood_identity="sha256:" + "1" * 64,
        prior_identity="sha256:" + "2" * 64,
        data_identity=admitted_data_identity(decision),
        covariance_identity="sha256:" + "0" * 64,
        block_ids=("a", "b"),
        discrepancy_ids=("amplitude",),
    )
    with pytest.raises(ProductionBayesianError, match="covariance identity"):
        bind_production_model_contract(
            contract=base,
            lane_spec=lane,
            admission_decision=decision,
            candidate_identity=candidate,
            provider_manifest_path=Path(provider.manifest_path),
        )


def test_model_provider_001_code_change_invalidates_contract_identity(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    bound = _bound_model(lane, decision, candidate, provider)
    lineage = build_sampler_posterior_lineage(
        contract=bound,
        samples=np.asarray([[0.0], [1.0], [2.0]]),
        normalized_weights=np.asarray([0.2, 0.3, 0.5]),
        sampler_settings={
            "nlive": 200,
            "dlogz": 0.1,
            "bound": "multi",
            "sample": "rwalk",
            "seed": 7,
        },
        resampling_rule="systematic",
    )
    source = candidate.repo_root / "provider.py"
    source.write_text(source.read_text(encoding="utf-8") + "\n# provider-v2\n", encoding="utf-8")
    _git(candidate.repo_root, "add", "--", "provider.py")
    _git(candidate.repo_root, "commit", "-m", "change provider bytes")
    new_candidate = build_clean_candidate_identity(candidate.repo_root)
    with pytest.raises(ProductionBayesianError, match="stale or forged"):
        revalidate_bound_production_model_contract(
            contract=bound,
            lane_spec=lane,
            admission_decision=decision,
            candidate_identity=new_candidate,
        )
    new_provider = SimpleNamespace(
        source_path="provider.py",
        manifest_path="provider-manifest.json",
    )
    rebound = _bound_model(lane, decision, new_candidate, new_provider)
    assert rebound.contract_content_id != bound.contract_content_id
    with pytest.raises(ProductionBayesianError, match="does not bind"):
        build_posterior_consumer_plan(
            contract=rebound,
            lineage=lineage,
            ppc_discrepancy_ids=("amplitude",),
            loo_block_ids=("act-block-a", "act-block-b"),
        )


def test_model_inmem_001_rejects_callable_substituted_behind_clean_filename(
    tmp_path: Path,
) -> None:
    """A forged co_filename cannot substitute runtime code for the Git blob."""

    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    source = candidate.repo_root / "provider.py"
    namespace: dict[str, object] = {}
    exec(
        compile(
            "def log_likelihood(theta):\n    return 123456.0\n",
            str(source),
            "exec",
        ),
        namespace,
    )
    with pytest.raises(ProductionBayesianError, match="factory-loaded"):
        build_production_model_contract(
            lane_id="H-ACT",
            model_id="malicious-in-memory-substitution",
            parameter_schema={"amplitude": {"support": "real"}},
            likelihood_identity="sha256:" + "1" * 64,
            prior_identity="sha256:" + "2" * 64,
            data_identity=admitted_data_identity(decision),
            covariance_identity=admitted_covariance_identity(decision),
            block_ids=("a", "b"),
            discrepancy_ids=("amplitude",),
            log_likelihood=namespace["log_likelihood"],
        )


def test_model_inmem_002_rejects_provider_default_runtime_state(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    source = candidate.repo_root / "provider.py"
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "def log_likelihood(theta):",
            "def log_likelihood(theta, scale=1.0):",
        ),
        encoding="utf-8",
    )
    _git(candidate.repo_root, "add", "--", "provider.py")
    _git(candidate.repo_root, "commit", "-m", "add forbidden provider default")
    changed = build_clean_candidate_identity(candidate.repo_root)

    with pytest.raises(ProductionBayesianError, match="unbound runtime state"):
        _bound_model(lane, decision, changed, provider)


def test_provider_validation_never_executes_candidate_blob(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    marker = tmp_path / "provider-executed.txt"
    source = candidate.repo_root / "provider.py"
    source.write_text(
        source.read_text(encoding="utf-8")
        + f"\nnp.savetxt({str(marker)!r}, [1.0])\n",
        encoding="utf-8",
    )
    _git(candidate.repo_root, "add", "--", "provider.py")
    _git(candidate.repo_root, "commit", "-m", "add forbidden top-level effect")
    changed = build_clean_candidate_identity(candidate.repo_root)

    with pytest.raises(ProductionBayesianError, match="execution is deferred"):
        _bound_model(lane, decision, changed, provider)
    assert not marker.exists()


def test_runtime_env_001_rejects_live_environment_contract_mismatch(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    changed = _commit_json_mutation(
        candidate,
        "environment.lock",
        lambda payload: payload["expected_receipt"].__setitem__(
            "python_version", "0.0.0"
        ),
        message="forge runtime environment",
    )

    with pytest.raises(ProductionBayesianError, match="live runtime differs"):
        _bound_model(lane, decision, changed, provider)


def test_runtime_receipt_binds_executable_and_numpy_native_bytes() -> None:
    receipt = capture_runtime_environment_receipt(("numpy", "cryptography"))
    assert receipt.python_executable_sha256.startswith("sha256:")
    assert len(receipt.python_executable_sha256) == 71
    assert len(receipt.native_extension_sha256) == 1
    name, identity = next(iter(receipt.native_extension_sha256.items()))
    assert name in {
        "numpy._core._multiarray_umath",
        "numpy.core._multiarray_umath",
    }
    assert identity.startswith("sha256:") and len(identity) == 71


def test_response_rank_001_rejects_rank_assertion_without_computed_support(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    changed = _commit_json_mutation(
        candidate,
        "response-matrix.json",
        lambda payload: payload.__setitem__("matrix", [[0.0]]),
        message="make response rank deficient",
    )

    with pytest.raises(ProductionBayesianError, match="computed response rank"):
        _bound_model(lane, decision, changed, provider)


def test_response_rank_rejects_nonnumeric_matrix_as_typed_contract_error(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    changed = _commit_json_mutation(
        candidate,
        "response-matrix.json",
        lambda payload: payload.__setitem__("matrix", [["not-a-number"]]),
        message="malform response matrix",
    )

    with pytest.raises(ProductionBayesianError, match="response matrix"):
        _bound_model(lane, decision, changed, provider)


def test_normalization_001_rejects_boolean_substitute_for_bound_evidence(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    changed = _commit_json_mutation(
        candidate,
        "normalization-evidence.json",
        lambda payload: payload["likelihood"].__setitem__(
            "status", "CALLER_ASSERTED_TRUE"
        ),
        message="forge normalization status",
    )

    with pytest.raises(ProductionBayesianError, match="does not bind the model"):
        _bound_model(lane, decision, changed, provider)


def test_execution_plan_001_rejects_authorization_for_another_plan(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    model = _bound_model(lane, decision, candidate, provider)
    raw = _signed_receipt(
        lane,
        decision,
        candidate,
        TEST_PUBLIC_KEY,
        model_contract_content_id=model.contract_content_id,
        runtime_environment_receipt_id=model.runtime_environment_receipt_id,
        computed_response_rank_receipt_id=model.computed_response_rank_receipt_id,
        normalization_evidence_id=model.normalization_evidence_id,
        execution_plan_content_id="sha256:" + "0" * 64,
    )
    receipt = HumanExecutionAuthorizationReceiptV1.from_bytes(raw)

    with pytest.raises(
        HumanExecutionAuthorizationError, match="plan binding mismatched"
    ):
        validate_authorization_execution_bindings(
            receipt,
            model_contract_content_id=model.contract_content_id,
            runtime_environment_receipt_id=model.runtime_environment_receipt_id,
            computed_response_rank_receipt_id=model.computed_response_rank_receipt_id,
            normalization_evidence_id=model.normalization_evidence_id,
            execution_plan_content_id=model.execution_plan_content_id,
        )


@pytest.mark.parametrize(
    "entrypoint",
    (
        "provider.py:discrepancy",
        "provider.py:log_likelihood_extra",
        "provider.py:undeclared_helper",
    ),
    ids=("wrong-export", "suffix-collision", "undeclared-helper"),
)
def test_execution_plan_entrypoint_rejects_non_manifest_sampler_exports(
    tmp_path: Path,
    entrypoint: str,
) -> None:
    """A sampler plan cannot select another symbol in the provider module."""

    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    changed = _commit_json_mutation(
        candidate,
        "execution-plan.json",
        lambda payload: payload.__setitem__("entrypoint", entrypoint),
        message="change sampler entrypoint",
    )

    with pytest.raises(
        ProductionBayesianError,
        match="entrypoint does not equal the registered sampler export",
    ):
        _bound_model(lane, decision, changed, provider)


def test_execution_plan_exact_manifest_sampler_export_is_accepted(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)

    model = _bound_model(lane, decision, candidate, provider)

    assert model.execution_plan_content_id is not None


def test_provider_dependency_blob_change_invalidates_bound_contract(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    dependency = candidate.repo_root / "provider-dependency.txt"
    dependency.write_text("dependency-v1\n", encoding="utf-8")
    manifest = candidate.repo_root / provider.manifest_path
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["dependency_paths"] = ["provider-dependency.txt"]
    manifest.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    _git(
        candidate.repo_root,
        "add",
        "--",
        "provider-dependency.txt",
        provider.manifest_path,
    )
    _git(candidate.repo_root, "commit", "-m", "bind provider dependency")
    bound_candidate = build_clean_candidate_identity(candidate.repo_root)
    bound = _bound_model(lane, decision, bound_candidate, provider)

    dependency.write_text("dependency-v2\n", encoding="utf-8")
    _git(candidate.repo_root, "add", "--", "provider-dependency.txt")
    _git(candidate.repo_root, "commit", "-m", "change provider dependency")
    changed_candidate = build_clean_candidate_identity(candidate.repo_root)
    with pytest.raises(ProductionBayesianError, match="stale or forged"):
        revalidate_bound_production_model_contract(
            contract=bound,
            lane_spec=lane,
            admission_decision=decision,
            candidate_identity=changed_candidate,
        )


def test_posterior_obs_001_and_002_stay_blocked_without_pr305_terminal(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    model = _bound_model(lane, decision, candidate, provider)
    lineage = build_sampler_posterior_lineage(
        contract=model,
        samples=np.asarray([[0.0], [1.0], [2.0]]),
        normalized_weights=np.asarray([0.2, 0.3, 0.5]),
        sampler_settings={
            "nlive": 200,
            "dlogz": 0.1,
            "bound": "multi",
            "sample": "rwalk",
            "seed": 7,
        },
        resampling_rule="systematic",
    )
    plan = build_posterior_consumer_plan(
        contract=model,
        lineage=lineage,
        ppc_discrepancy_ids=("amplitude",),
        loo_block_ids=("act-block-a", "act-block-b"),
    )
    result = assess_lane_readiness(
        ObservationalLaneDescriptor("H-ACT", ("provider.py",)),
        model_contract=model,
        admission_decision=decision,
        candidate_identity=candidate,
        posterior_lineage=lineage,
        posterior_consumer_plan=plan,
    )
    assert result.status is LaneReadinessStatus.BLOCKED_SAMPLER_TERMINAL
    assert result.blocked_reasons == (
        "pr305_observed_run_terminal_contract_unavailable",
    )
    assert result.observed_data_executed is False


def test_readiness_treats_candidate_cache_as_non_authoritative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    attacker = TEST_PUBLIC_KEY
    model = _bound_model(lane, decision, candidate, provider)
    descriptor = ObservationalLaneDescriptor("H-ACT", ("provider.py",))
    attacker_raw = _signed_receipt(
        lane,
        decision,
        candidate,
        attacker,
        model_contract_content_id=model.contract_content_id,
        runtime_environment_receipt_id=model.runtime_environment_receipt_id,
        computed_response_rank_receipt_id=model.computed_response_rank_receipt_id,
        normalization_evidence_id=model.normalization_evidence_id,
        execution_plan_content_id=model.execution_plan_content_id,
    )
    forged = ValidatedHumanExecutionAuthorization(
        signed_receipt_bytes=attacker_raw,
        receipt=HumanExecutionAuthorizationReceiptV1.from_bytes(attacker_raw),
        replayed_lane_spec_content_id="sha256:" + "1" * 64,
        replayed_admission_bundle_id=decision.lane_admission_bundle_id,
        validated_candidate_identity_id=candidate.candidate_identity_id,
        validated_at_utc=EVALUATED,
        validation_content_id="sha256:" + "2" * 64,
    )
    result = assess_lane_readiness(
        descriptor,
        model_contract=model,
        admission_decision=decision,
        validated_human_authorization=forged,
        candidate_identity=candidate,
    )
    assert result.status is LaneReadinessStatus.BLOCKED_HUMAN_AUTHORIZATION
    assert result.blocked_reasons == ("external_trusted_launcher_required",)


def test_a3_ephemeral_001_interpreter_alias_replay_leaves_stale_path_absent(
    tmp_path: Path,
) -> None:
    assert not STALE_RECEIPT.exists()
    archive = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    assert archive.returncode == 0, archive.stderr.decode("utf-8", errors="replace")
    disposable = (tmp_path / "archive-root").resolve()
    disposable.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as handle:
        members = handle.getmembers()
        assert all(
            not member.name.startswith("/") and ".." not in Path(member.name).parts
            for member in members
        )
        handle.extractall(disposable, filter="data")
    receipt = disposable / "docs/generated/pr289_data_identity_v2_receipt.json"
    interpreters = (Path("/usr/bin/python"), Path("/usr/bin/python3"))
    assert all(executable.is_file() for executable in interpreters), (
        "A3-EPHEMERAL-001 requires both registered interpreter aliases"
    )
    try:
        built = subprocess.run(
            [
                str(interpreters[0]),
                "-B",
                "scripts/codex_harness/run_pr289_data_identity_v2.py",
                "build",
            ],
            cwd=disposable,
            check=False,
            capture_output=True,
            text=True,
        )
        assert built.returncode == 0, built.stderr
        expected = hashlib.sha256(receipt.read_bytes()).hexdigest()
        observed: list[str] = []
        for executable in interpreters:
            checked = subprocess.run(
                [
                    str(executable),
                    "-B",
                    "scripts/codex_harness/run_pr289_data_identity_v2.py",
                    "check",
                ],
                cwd=disposable,
                check=False,
                capture_output=True,
                text=True,
            )
            assert checked.returncode == 0, checked.stderr
            observed.append(hashlib.sha256(receipt.read_bytes()).hexdigest())
        assert observed == [expected, expected]
    finally:
        shutil.rmtree(disposable)
    assert not disposable.exists()
    assert not STALE_RECEIPT.exists()


def test_git_env_001_candidate_identity_ignores_path_selected_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A PATH-prepended fake git must not control candidate identity."""

    candidate, _ = _candidate_repo(tmp_path)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", str(fake_bin))

    assert build_clean_candidate_identity(candidate.repo_root) == candidate


def test_git_env_002_candidate_identity_ignores_git_environment_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ambient Git repository/object/index overrides must be scrubbed."""

    candidate, _ = _candidate_repo(tmp_path)
    attacker = tmp_path / "attacker"
    attacker.mkdir()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        monkeypatch.setenv(name, str(attacker))

    assert build_clean_candidate_identity(candidate.repo_root) == candidate


def test_trust_root_001_candidate_local_active_key_is_never_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A candidate-controlled key and matching signature cannot self-authorize."""

    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    attacker = TEST_PUBLIC_KEY
    candidate = _activate_candidate_authority(candidate, attacker)

    with pytest.raises(
        HumanExecutionAuthorizationError,
        match="external trusted launcher",
    ):
        _validate(
            _signed_receipt(lane, decision, candidate, attacker),
            lane,
            decision,
            candidate,
        )


def test_trust_root_002_external_launcher_and_pending_signature_contract() -> None:
    assert TRUSTED_LAUNCHER == Path("/usr/local/libexec/htt-auth-launcher")
    assert EXTERNAL_TRUST_ROOT_PUBLIC_KEY == Path(
        "/etc/htt/trust/root_authority_ed25519.pub"
    )
    assert EXTERNAL_TRUST_ROOT_FINGERPRINT == Path(
        "/etc/htt/trust/root_authority_ed25519.pub.sha256"
    )
    sidecar = json.loads(
        (
            ROOT
            / "docs/research_program/post_pr275/human_authority_registry.signature.json"
        ).read_text(encoding="utf-8")
    )
    registry = ROOT / sidecar["registry_path"]
    assert sidecar["status"] == "PENDING_EXTERNAL_ROOT_SIGNATURE"
    assert sidecar["authority_granted"] is False
    assert sidecar["root_authority_key_id"] is None
    assert sidecar["registry_signature_ed25519"] is None
    assert sidecar["registry_sha256"] == (
        "sha256:" + hashlib.sha256(registry.read_bytes()).hexdigest()
    )


def test_ci_coverage_001_runs_every_pr304_policy_command_on_pull_requests() -> None:
    policy = json.loads(
        (
            ROOT
            / "docs/research_program/post_pr275/pr304_publication_policy.json"
        ).read_text(encoding="utf-8")
    )
    workflow = (ROOT / ".github/workflows/repository-integrity.yml").read_text(
        encoding="utf-8"
    )
    assert "pull_request:" in workflow
    pinned_minimal_install = (
        "python -m pip install 'pytest>=8,<9' 'PyYAML>=6,<7' 'numpy>=1.26,<3'"
    )
    editable_runtime_install = "python -m pip install -e './htt'"
    assert pinned_minimal_install in workflow
    assert editable_runtime_install in workflow
    assert workflow.index(pinned_minimal_install) < workflow.index(
        editable_runtime_install
    )
    for row in policy["required_commands"]:
        command = shlex.join(row["argv"])
        assert command in workflow, f"missing PR-304 CI command: {row['id']}"


def test_trust_toctou_001_worktree_authority_registry_swap_is_rejected(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    raw = _signed_receipt(lane, decision, candidate, TEST_PUBLIC_KEY)
    registry = (
        candidate.repo_root
        / "docs/research_program/post_pr275/human_authority_registry.json"
    )
    registry.write_text("{}\n", encoding="utf-8")

    with pytest.raises(HumanExecutionAuthorizationError, match="dirty"):
        _validate(raw, lane, decision, candidate)


def test_lane_toctou_001_worktree_lane_registry_swap_is_rejected(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    registry = candidate.repo_root / REGISTRY.relative_to(ROOT)
    registry.write_text("{}\n", encoding="utf-8")

    with pytest.raises(HumanExecutionAuthorizationError, match="dirty"):
        authorization.replay_complete_lane_admission(
            lane_spec=lane,
            admission_decision=decision,
            candidate_identity=candidate,
        )


def test_provider_toctou_001_worktree_resource_swap_is_rejected(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    (candidate.repo_root / "provider-config.json").write_text(
        '{"model":"attacker"}\n', encoding="utf-8"
    )

    with pytest.raises(ProductionBayesianError, match="replay"):
        _bound_model(lane, decision, candidate, provider)


def test_candidate_blob_reader_returns_commit_bytes_not_pathname_bytes(
    tmp_path: Path,
) -> None:
    candidate, _ = _candidate_repo(tmp_path)
    expected = (candidate.repo_root / "provider.py").read_bytes()
    assert read_candidate_blob(candidate, "provider.py") == expected
