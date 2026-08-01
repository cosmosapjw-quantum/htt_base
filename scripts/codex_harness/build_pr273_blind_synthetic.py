#!/usr/bin/env python3
"""Build the deterministic PR-273 blind synthetic diagnostic pack."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
for source_root in (ROOT, ROOT / "htt/src", ROOT / "htt"):
    value = str(source_root)
    if value not in sys.path:
        sys.path.insert(0, value)

from common.blind_synthetic_contract import (  # noqa: E402
    BLIND_SYNTHETIC_ALLOWED_USE,
    BLIND_SYNTHETIC_FORBIDDEN_USE,
    BlindSyntheticContractError,
    build_blind_synthetic_adjudication,
    build_blind_synthetic_challenge,
    canonical_sha256,
    replay_blind_synthetic_submission,
)
from htt.infer.vector_tensor_blind_integration import (  # noqa: E402
    ANALYZER_ID,
    DEPTH_ALERT_THRESHOLD,
    analyze_blind_challenge,
)


SPEC = ROOT / "docs/research_program/vector_tensor/pr273_spec.yaml"
CHALLENGE = (
    ROOT
    / "docs/research_program/vector_tensor/integration/PR273_CHALLENGE.json"
)
TRUTH_VAULT = (
    ROOT
    / "docs/research_program/vector_tensor/integration/PR273_TRUTH_VAULT.json"
)
SUBMISSION = (
    ROOT
    / "docs/research_program/vector_tensor/integration/"
    "PR273_ANALYST_SUBMISSION.json"
)
ADJUDICATION = (
    ROOT
    / "docs/research_program/vector_tensor/integration/PR273_ADJUDICATION.json"
)
DIAGNOSTIC_PACK = (
    ROOT
    / "docs/research_program/vector_tensor/integration/"
    "PR273_DIAGNOSTIC_PACK.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def _verify_frozen_inputs(spec: MappingLike) -> None:
    for name, record in spec["frozen_inputs"].items():
        path = ROOT / record["path"]
        actual = _sha256(path)
        if actual != record["sha256"]:
            raise RuntimeError(
                f"frozen input {name} drifted: {actual} != {record['sha256']}"
            )


MappingLike = dict[str, object]


def _expect_killed(name: str, operation) -> tuple[str, str]:
    try:
        operation()
    except BlindSyntheticContractError:
        return name, "KILLED"
    raise RuntimeError(f"declared mutation survived: {name}")


def _mutation_results(
    *,
    challenge_payload: MappingLike,
    challenge,
    submission_payload: MappingLike,
    submission,
    truth_payload: MappingLike,
    truth_raw: bytes,
    truth_sha: str,
    expected_submission_content_id: str,
) -> dict[str, str]:
    killed: list[tuple[str, str]] = []

    def truth_field() -> None:
        payload = copy.deepcopy(challenge_payload)
        payload["cases"][0]["label"] = "SYNTHETIC_SENTINEL"
        build_blind_synthetic_challenge(payload)

    killed.append(_expect_killed("TRUTH_FIELD_IN_CHALLENGE", truth_field))

    def truth_in_case_id() -> None:
        payload = copy.deepcopy(challenge_payload)
        payload["cases"][0]["case_id"] = "SYNTHETIC_SENTINEL"
        payload["partitions"]["development"][0] = "SYNTHETIC_SENTINEL"
        build_blind_synthetic_challenge(payload)

    _expect_killed("TRUTH_FIELD_IN_CHALLENGE", truth_in_case_id)

    def observed_flag() -> None:
        payload = copy.deepcopy(challenge_payload)
        payload["observed_data"] = True
        build_blind_synthetic_challenge(payload)

    killed.append(_expect_killed("OBSERVED_DATA_FLAG", observed_flag))

    def partition_extra() -> None:
        payload = copy.deepcopy(challenge_payload)
        payload["partitions"]["aux"] = []
        build_blind_synthetic_challenge(payload)

    _expect_killed("CHALLENGE_AFTER_SUBMISSION", partition_extra)

    def changed_challenge() -> None:
        payload = copy.deepcopy(challenge_payload)
        payload["cases"][0]["state"]["sigma_stf5"][0] += 0.001
        changed = build_blind_synthetic_challenge(payload)
        build_blind_synthetic_adjudication(
            adjudication_id="PR273-MUTATION-CHALLENGE",
            challenge=changed,
            submission=submission,
            truth_vault_raw=truth_raw,
            expected_truth_vault_sha256=truth_sha,
            expected_submission_content_id=expected_submission_content_id,
            mutation_results={
                name: "KILLED" for name in challenge.declared_mutations
            },
        )

    killed.append(
        _expect_killed("CHALLENGE_AFTER_SUBMISSION", changed_challenge)
    )

    def changed_submission() -> None:
        payload = copy.deepcopy(submission_payload)
        payload["scenario"] = "SYNTHETIC_SENTINEL"
        replay_blind_synthetic_submission(
            payload,
            expected_content_id=expected_submission_content_id,
        )

    killed.append(
        _expect_killed("SUBMISSION_AFTER_SEAL", changed_submission)
    )

    def resealed_partition_submission() -> None:
        payload = copy.deepcopy(submission_payload)
        payload["case_results"][3]["partition"] = "development"
        body = {
            key: value for key, value in payload.items() if key != "content_id"
        }
        payload["content_id"] = canonical_sha256(body)
        replay_blind_synthetic_submission(
            payload,
            expected_content_id=expected_submission_content_id,
        )

    _expect_killed("SUBMISSION_AFTER_SEAL", resealed_partition_submission)

    def resealed_valid_submission() -> None:
        payload = copy.deepcopy(submission_payload)
        payload["case_results"][0]["depth_alert"] = not payload[
            "case_results"
        ][0]["depth_alert"]
        body = {
            key: value for key, value in payload.items() if key != "content_id"
        }
        payload["content_id"] = canonical_sha256(body)
        replay_blind_synthetic_submission(
            payload,
            expected_content_id=expected_submission_content_id,
        )

    _expect_killed("SUBMISSION_AFTER_SEAL", resealed_valid_submission)

    def changed_commitment() -> None:
        build_blind_synthetic_adjudication(
            adjudication_id="PR273-MUTATION-TRUTH-COMMITMENT",
            challenge=challenge,
            submission=submission,
            truth_vault_raw=truth_raw,
            expected_truth_vault_sha256="0" * 64,
            expected_submission_content_id=expected_submission_content_id,
            mutation_results={
                name: "KILLED" for name in challenge.declared_mutations
            },
        )

    killed.append(
        _expect_killed("TRUTH_VAULT_COMMITMENT", changed_commitment)
    )

    def changed_interpreted_truth() -> None:
        payload = copy.deepcopy(truth_payload)
        payload["expected_cases"][0]["scenario"] = "SYNTHETIC_SENTINEL"
        mutated_raw = _json_bytes(payload)
        build_blind_synthetic_adjudication(
            adjudication_id="PR273-MUTATION-INTERPRETED-TRUTH",
            challenge=challenge,
            submission=submission,
            truth_vault_raw=mutated_raw,
            expected_truth_vault_sha256=truth_sha,
            expected_submission_content_id=expected_submission_content_id,
            mutation_results={
                name: "KILLED" for name in challenge.declared_mutations
            },
        )

    _expect_killed("TRUTH_VAULT_COMMITMENT", changed_interpreted_truth)
    return dict(killed)


def build() -> tuple[MappingLike, MappingLike, MappingLike]:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    _verify_frozen_inputs(spec)

    # BLIND_ANALYSIS: truth bytes are intentionally not read before this point.
    challenge_payload = json.loads(CHALLENGE.read_text(encoding="utf-8"))
    challenge = build_blind_synthetic_challenge(challenge_payload)
    submission = analyze_blind_challenge(challenge)
    submission_payload = submission.as_payload()
    registered_adjudication = spec["analysis_protocol"]["stages"][1]
    expected_submission_content_id = registered_adjudication[
        "frozen_submission_content_id"
    ]
    replay_blind_synthetic_submission(
        submission_payload,
        expected_content_id=expected_submission_content_id,
    )

    # REGISTERED_ADJUDICATION: the sealed submission now exists in memory.
    truth_raw = TRUTH_VAULT.read_bytes()
    truth_payload = json.loads(truth_raw)
    truth_sha = hashlib.sha256(truth_raw).hexdigest()
    mutations = _mutation_results(
        challenge_payload=challenge_payload,
        challenge=challenge,
        submission_payload=submission_payload,
        submission=submission,
        truth_payload=truth_payload,
        truth_raw=truth_raw,
        truth_sha=truth_sha,
        expected_submission_content_id=expected_submission_content_id,
    )
    adjudication = build_blind_synthetic_adjudication(
        adjudication_id="PR273-REGISTERED-ADJUDICATION-V1",
        challenge=challenge,
        submission=submission,
        truth_vault_raw=truth_raw,
        expected_truth_vault_sha256=spec["frozen_inputs"]["truth_vault"][
            "sha256"
        ],
        expected_submission_content_id=expected_submission_content_id,
        mutation_results=mutations,
    )
    adjudication_payload = adjudication.as_payload()
    pack = {
        "schema": "htt.pr273.blind_synthetic_diagnostic_pack.v1",
        "pack_id": "PR273-BLIND-SYNTHETIC-DIAGNOSTIC-PACK-V1",
        "owner": "HTT",
        "contributors": ["COMMON", "OBSSTAT", "MIO"],
        "scope": "pre-solver registered synthetic integration",
        "artifact_mode": "synthetic_diagnostic",
        "config_identity": canonical_sha256(spec),
        "seed": challenge.seed,
        "transfer_source": challenge.transfer_source,
        "claim_ceiling": challenge.claim_ceiling,
        "observed_data": False,
        "analysis_stage_truth_accessed": False,
        "analyzer_id": ANALYZER_ID,
        "challenge_content_id": challenge.content_id,
        "submission_content_id": submission.content_id,
        "adjudication_content_id": adjudication.content_id,
        "depth_alert_threshold": DEPTH_ALERT_THRESHOLD,
        "case_count": len(challenge.cases),
        "held_out_case_count": len(dict(challenge.partitions)["held_out"]),
        "case_results": list(submission.case_results),
        "adjudication_status": adjudication.status,
        "case_verdicts": list(adjudication.case_verdicts),
        "mutation_results": mutations,
        "required_pipeline": spec["case_contract"]["required_pipeline"],
        "scalar_successor_mapping": spec["case_contract"][
            "scalar_successor_mapping"
        ],
        "allowed_use": list(BLIND_SYNTHETIC_ALLOWED_USE),
        "forbidden_use": list(BLIND_SYNTHETIC_FORBIDDEN_USE),
        "caveats": [
            "synthetic cases only",
            "orbit completeness remains unproven",
            "finite matched-null Pi profile only",
            "G_F is represented by the typed depth-path successor, not a scalar",
            "no observed data, native low-ell solver, or morphology atlas was used"
        ],
    }
    pack["content_id"] = canonical_sha256(pack)
    return submission_payload, adjudication_payload, pack


def _write_or_check(path: Path, payload: MappingLike, *, check: bool) -> None:
    expected = _json_bytes(payload)
    if check:
        if not path.exists() or path.read_bytes() != expected:
            raise RuntimeError(f"generated artifact drifted: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(expected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    submission, adjudication, pack = build()
    for path, payload in (
        (SUBMISSION, submission),
        (ADJUDICATION, adjudication),
        (DIAGNOSTIC_PACK, pack),
    ):
        _write_or_check(path, payload, check=args.check)
    print(
        "PR-273 blind synthetic build PASS: "
        f"{pack['case_count']} cases, "
        f"{pack['held_out_case_count']} held out, "
        f"{len(pack['mutation_results'])} mutations killed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
