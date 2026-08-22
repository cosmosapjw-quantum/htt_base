from __future__ import annotations

import base64
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import inspect
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
from types import SimpleNamespace

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
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
    HumanExecutionAuthorizationError,
    HumanExecutionAuthorizationReceiptV1,
    ValidatedHumanExecutionAuthorization,
    admitted_covariance_identity,
    admitted_data_identity,
    build_clean_candidate_identity,
    revalidate_cached_human_execution_authorization,
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
LANE_ORDER = ("PLANCK", "CF4", "HSC_KIDS", "ACT", "DESI", "JWST_SN")
GATES = {
    "PLANCK": "H-PLANCK",
    "CF4": "H-CF4",
    "HSC_KIDS": "H-HSC-KiDS",
    "ACT": "H-ACT",
    "DESI": "H-DESI",
    "JWST_SN": "H-JWST",
}
SCOPES = {
    lane: f"admitted_{lane.casefold()}_observed_execution" for lane in LANE_ORDER
}
SCOPES["HSC_KIDS"] = "admitted_hsc_kids_observed_execution"
SCOPES["JWST_SN"] = "admitted_jwst_sn_observed_execution"


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
    (repo / "environment.lock").write_text(
        "python=3.12\nnumpy=test-fixture\n", encoding="utf-8"
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
    namespace: dict[str, object] = {"np": np, "__file__": str(source)}
    exec(compile(source.read_bytes(), str(source), "exec"), namespace)
    provider = SimpleNamespace(
        log_likelihood=namespace["log_likelihood"],
        prior_transform=namespace["prior_transform"],
        replicate_generator=namespace["replicate_generator"],
        discrepancy=namespace["discrepancy"],
        config_path="provider-config.json",
        environment_path="environment.lock",
    )
    return build_clean_candidate_identity(repo), provider


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


def _install_authority_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    public_key: bytes,
    *,
    key_id: str = TRUSTED_KEY_ID,
) -> Path:
    authorities = {
        lane: {
            "status": "PENDING_HUMAN_PROVISIONING",
            "key_id": None,
            "public_key_base64": None,
            "gate_id": GATES[lane],
            "scope": SCOPES[lane],
        }
        for lane in LANE_ORDER
    }
    authorities["ACT"] = {
        "status": "ACTIVE",
        "key_id": key_id,
        "public_key_base64": base64.b64encode(public_key).decode("ascii"),
        "gate_id": GATES["ACT"],
        "scope": SCOPES["ACT"],
    }
    path = tmp_path / "human-authority-registry.json"
    path.write_text(
        json.dumps(
            {
                "schema": "common.human_authority_registry.v1",
                "lane_order": list(LANE_ORDER),
                "authorities": authorities,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(authorization, "_authority_registry_path", lambda _: path)
    return path


def _public_bytes(private_key: Ed25519PrivateKey) -> bytes:
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def _signed_receipt(
    lane,
    decision,
    candidate: CandidateIdentityV1,
    private_key: Ed25519PrivateKey,
    *,
    signer_key_id: str = TRUSTED_KEY_ID,
    **overrides: object,
) -> bytes:
    unsigned: dict[str, object] = {
        "schema": AUTHORIZATION_SCHEMA,
        "lane_id": lane.lane_id,
        "exact_admission_record_ids": [record.record_id for record in decision.records],
        "lane_admission_bundle_id": decision.lane_admission_bundle_id,
        "analysis_plan_id": lane.analysis_plan_id,
        "required_human_gate_id": lane.required_human_gate_id,
        "authorized_scope": "admitted_act_observed_execution",
        "authorization_domain": AUTHORIZATION_DOMAIN,
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
    signature = private_key.sign(_canonical(signed))
    return _canonical(
        {
            **signed,
            "authorization_signature_ed25519": base64.b64encode(signature).decode(
                "ascii"
            ),
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
        response_rank=1,
        likelihood_normalized=True,
        prior_normalized=True,
        log_likelihood=provider.log_likelihood,
        prior_transform=provider.prior_transform,
        replicate_generator=provider.replicate_generator,
        discrepancies={"amplitude": provider.discrepancy},
    )
    return bind_production_model_contract(
        contract=base,
        lane_spec=lane,
        admission_decision=decision,
        candidate_identity=candidate,
        provider_configuration_path=Path(provider.config_path),
        provider_environment_path=Path(provider.environment_path),
    )


def test_validates_pinned_ed25519_receipt_as_non_authoritative_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(signer))
    raw = _signed_receipt(lane, decision, candidate, signer)
    cache = _validate(raw, lane, decision, candidate)
    assert isinstance(cache, ValidatedHumanExecutionAuthorization)
    assert cache.signed_receipt_bytes == raw
    assert cache.receipt.nonce == VALID_NONCE
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

    signer = Ed25519PrivateKey.generate()
    raw = _signed_receipt(lane, decision, candidate, signer)
    with pytest.raises(HumanExecutionAuthorizationError, match="not active"):
        _validate(raw, lane, decision, candidate)


def test_auth_trust_001_rejects_arbitrary_self_signed_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    trusted = Ed25519PrivateKey.generate()
    attacker = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(trusted))
    raw = _signed_receipt(
        lane,
        decision,
        candidate,
        attacker,
        signer_key_id="ATTACKER-SELF-SIGNED-ED25519",
    )
    with pytest.raises(HumanExecutionAuthorizationError, match="trusted human signer"):
        _validate(raw, lane, decision, candidate)


def test_auth_trust_002_rejects_registered_signer_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    original = Ed25519PrivateKey.generate()
    replacement = Ed25519PrivateKey.generate()
    raw = _signed_receipt(lane, decision, candidate, original)
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(replacement))
    with pytest.raises(HumanExecutionAuthorizationError, match="signature"):
        _validate(raw, lane, decision, candidate)


def test_production_registry_is_fail_closed_pending_human_provisioning(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    attacker = Ed25519PrivateKey.generate()
    with pytest.raises(HumanExecutionAuthorizationError, match="not active"):
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
    signer = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(signer))
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
    signer = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(signer))
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
        "nonce:v1:" + "ab" * 32,
    ),
)
def test_auth_nonce_001_rejects_noncanonical_nonce(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    bad_nonce: str,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(signer))
    with pytest.raises(HumanExecutionAuthorizationError, match="nonce:v1"):
        _validate(
            _signed_receipt(lane, decision, candidate, signer, nonce=bad_nonce),
            lane,
            decision,
            candidate,
        )


def test_auth_json_001_rejects_duplicate_and_noncanonical_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(signer))
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
    signer = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(signer))
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
    trusted = Ed25519PrivateKey.generate()
    attacker = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(trusted))
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
    with pytest.raises(HumanExecutionAuthorizationError, match="signature"):
        revalidate_cached_human_execution_authorization(
            cached=forged,
            lane_spec=lane,
            admission_decision=decision,
            candidate_identity=candidate,
        )
    raw_forged = object.__new__(ValidatedHumanExecutionAuthorization)
    object.__setattr__(raw_forged, "signed_receipt_bytes", attacker_raw)
    with pytest.raises(HumanExecutionAuthorizationError, match="signature"):
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
    signer = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(signer))
    cache = _validate(
        _signed_receipt(lane, decision, candidate, signer),
        lane,
        decision,
        candidate,
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
    signer = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(signer))
    pr289 = build_not_authorized_receipt(lane, decision)
    with pytest.raises(HumanExecutionAuthorizationError, match="fields drifted"):
        _validate(_canonical(pr289.as_payload()), lane, decision, candidate)


def test_rejects_refused_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, admitted = _admitted_act(tmp_path)
    candidate, _ = _candidate_repo(tmp_path)
    signer = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(signer))
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


def test_readiness_reverifies_signed_authorization_and_bound_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    signer = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(signer))
    cache = _validate(
        _signed_receipt(lane, decision, candidate, signer),
        lane,
        decision,
        candidate,
    )
    model = _bound_model(lane, decision, candidate, provider)
    descriptor = ObservationalLaneDescriptor("H-ACT", ("provider.py",))
    result = assess_lane_readiness(
        descriptor,
        model_contract=model,
        admission_decision=decision,
        validated_human_authorization=cache,
        candidate_identity=candidate,
    )
    assert result.status is LaneReadinessStatus.READY_TO_START_SAMPLER
    assert result.observed_data_executed is False
    assert model.lane_admission_bundle_id == decision.lane_admission_bundle_id
    assert model.ordered_admission_record_ids == tuple(
        record.record_id for record in decision.records
    )
    assert model.admitted_covariance_identity == admitted_covariance_identity(
        decision
    )


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
        response_rank=1,
        likelihood_normalized=True,
        prior_normalized=True,
        log_likelihood=provider.log_likelihood,
        prior_transform=provider.prior_transform,
        replicate_generator=provider.replicate_generator,
        discrepancies={"amplitude": provider.discrepancy},
    )
    with pytest.raises(ProductionBayesianError, match="covariance identity"):
        bind_production_model_contract(
            contract=base,
            lane_spec=lane,
            admission_decision=decision,
            candidate_identity=candidate,
            provider_configuration_path=Path(provider.config_path),
            provider_environment_path=Path(provider.environment_path),
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
    namespace: dict[str, object] = {"np": np, "__file__": str(source)}
    exec(compile(source.read_bytes(), str(source), "exec"), namespace)
    new_provider = SimpleNamespace(
        log_likelihood=namespace["log_likelihood"],
        prior_transform=namespace["prior_transform"],
        replicate_generator=namespace["replicate_generator"],
        discrepancy=namespace["discrepancy"],
        config_path="provider-config.json",
        environment_path="environment.lock",
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


def test_readiness_rejects_forged_cache_and_expired_cached_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane, decision = _admitted_act(tmp_path)
    candidate, provider = _candidate_repo(tmp_path)
    trusted = Ed25519PrivateKey.generate()
    attacker = Ed25519PrivateKey.generate()
    _install_authority_registry(tmp_path, monkeypatch, _public_bytes(trusted))
    model = _bound_model(lane, decision, candidate, provider)
    descriptor = ObservationalLaneDescriptor("H-ACT", ("provider.py",))
    attacker_raw = _signed_receipt(lane, decision, candidate, attacker)
    forged = ValidatedHumanExecutionAuthorization(
        signed_receipt_bytes=attacker_raw,
        receipt=HumanExecutionAuthorizationReceiptV1.from_bytes(attacker_raw),
        replayed_lane_spec_content_id="sha256:" + "1" * 64,
        replayed_admission_bundle_id=decision.lane_admission_bundle_id,
        validated_candidate_identity_id=candidate.candidate_identity_id,
        validated_at_utc=EVALUATED,
        validation_content_id="sha256:" + "2" * 64,
    )
    with pytest.raises(ProductionBayesianError, match="just-in-time"):
        assess_lane_readiness(
            descriptor,
            model_contract=model,
            admission_decision=decision,
            validated_human_authorization=forged,
            candidate_identity=candidate,
        )
    valid = _validate(
        _signed_receipt(lane, decision, candidate, trusted),
        lane,
        decision,
        candidate,
    )
    expired = datetime(2026, 8, 22, 12, 16, tzinfo=timezone.utc)
    monkeypatch.setattr(authorization, "_trusted_now_utc", lambda: expired)
    with pytest.raises(ProductionBayesianError, match="just-in-time"):
        assess_lane_readiness(
            descriptor,
            model_contract=model,
            admission_decision=decision,
            validated_human_authorization=valid,
            candidate_identity=candidate,
        )


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
