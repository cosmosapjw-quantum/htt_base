#!/usr/bin/env python3
"""Generate the PR-275 proof atlas, synthetic plot, and replication pack.

The source theorem registry and the four downstream evidence layers remain
separate by construction.  Evidence-layer verdicts never rewrite source proof
status.  The only plot consumes the registered PR-273 synthetic diagnostic
pack; PR-274 admitted no observed input.
"""

from __future__ import annotations

import argparse
from collections import Counter
from io import BytesIO
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import sys
from typing import Mapping, Sequence

import yaml


os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/htt-pr275-matplotlib-cache")


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/vector_tensor/pr275_spec.yaml"
RUNNER = ROOT / "scripts/codex_harness/run_pr275_report.py"
REPORT_DIR = ROOT / "docs/research_program/vector_tensor/report"
ATLAS_JSON = REPORT_DIR / "PROOF_ATLAS.json"
ATLAS_MD = REPORT_DIR / "PROOF_ATLAS.md"
ANALYSIS_JSON = REPORT_DIR / "SYNTHETIC_CASE_ANALYSIS.json"
FIGURE = REPORT_DIR / "fig_pr275_synthetic_case_diagnostics.png"
FIGURE_MANIFEST = (
    REPORT_DIR / "fig_pr275_synthetic_case_diagnostics.manifest.json"
)
REPLICATION = REPORT_DIR / "REPLICATION_PACKAGE.json"
REPORT = REPORT_DIR / "VECTOR_TENSOR_PROGRAM_REPORT.md"


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects ambiguous duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    loader.flatten_mapping(node)
    result: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise RuntimeError("PR-275 YAML mapping key is not hashable") from exc
        if duplicate:
            raise RuntimeError(f"duplicate PR-275 YAML mapping key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _reject_json_constant(value: str) -> object:
    raise RuntimeError(f"non-finite JSON constant is forbidden: {value}")


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise RuntimeError(f"duplicate PR-275 JSON key: {key!r}")
        result[key] = value
    return result


def _load_yaml(path: Path) -> Mapping[str, object]:
    payload = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    if not isinstance(payload, Mapping):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a mapping")
    return payload


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_json_object,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(payload, Mapping):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain an object")
    return payload


def _repo_file(relative_text: object, *, label: str) -> Path:
    if not isinstance(relative_text, str) or not relative_text:
        raise RuntimeError(f"{label} path must be non-empty text")
    relative = PurePosixPath(relative_text)
    if relative.is_absolute() or ".." in relative.parts or "\\" in relative_text:
        raise RuntimeError(f"{label} path must remain repository-relative")
    root = ROOT.resolve(strict=True)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RuntimeError(f"{label} path traverses a symlink")
    path = root.joinpath(*relative.parts).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise RuntimeError(f"{label} path is not a regular repository file")
    return path


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


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


def _content_id(payload: Mapping[str, object]) -> str:
    body = {key: value for key, value in payload.items() if key != "content_id"}
    encoded = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + _sha256_bytes(encoded)


def _with_content_id(payload: dict[str, object]) -> dict[str, object]:
    payload["content_id"] = _content_id(payload)
    return payload


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return _sha256_bytes(encoded)


def _counts(values: Sequence[object]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def _require_mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{label} must be a mapping")
    return value


def _require_records(value: object, *, label: str) -> list[Mapping[str, object]]:
    if not isinstance(value, list) or not all(
        isinstance(record, Mapping) for record in value
    ):
        raise RuntimeError(f"{label} must be a list of mappings")
    return list(value)


def _verify_frozen_inputs(
    spec: Mapping[str, object],
) -> tuple[dict[str, Mapping[str, object]], dict[str, str]]:
    frozen = _require_mapping(spec.get("frozen_inputs"), label="frozen_inputs")
    sources: dict[str, Mapping[str, object]] = {}
    hashes: dict[str, str] = {}
    for label, raw_record in frozen.items():
        record = _require_mapping(raw_record, label=f"frozen input {label}")
        path = _repo_file(record.get("path"), label=f"frozen input {label}")
        expected = record.get("sha256")
        actual = _sha256(path)
        if not isinstance(expected, str) or actual != expected:
            raise RuntimeError(
                f"frozen input {label} drifted: {actual} != {expected}"
            )
        relative = str(record["path"])
        hashes[relative] = "sha256:" + actual
        if path.suffix == ".json":
            sources[str(label)] = _load_json(path)
        elif path.suffix in {".yaml", ".yml"}:
            sources[str(label)] = _load_yaml(path)
    return sources, dict(sorted(hashes.items()))


def _source_rows(
    signatures: Mapping[str, object],
    spec: Mapping[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    groups = _require_mapping(signatures.get("source_groups"), label="source_groups")
    contract = _require_mapping(spec.get("counting_contract"), label="counting_contract")
    exact_partitions = _require_mapping(
        contract.get("exact_source_partitions"), label="exact_source_partitions"
    )
    aliases = _require_mapping(contract.get("cardinality_aliases"), label="cardinality_aliases")
    if signatures.get("cardinality_aliases", {}).get("requested_pillar_T_65") != aliases.get(
        "requested_pillar_T_65"
    ):
        raise RuntimeError("requested_pillar_T_65 alias drifted")
    if signatures.get("cardinality_aliases", {}).get("requested_pillar_S_58") != aliases.get(
        "requested_pillar_S_58"
    ):
        raise RuntimeError("requested_pillar_S_58 alias drifted")

    rows: list[dict[str, object]] = []
    summaries: dict[str, object] = {}
    seen: set[str] = set()
    for group_name in ("legacy_signature_inventory", "proposal_registry_rows"):
        group = _require_mapping(groups.get(group_name), label=group_name)
        entries = _require_records(group.get("entries"), label=f"{group_name}.entries")
        expected_count = group.get("expected_count")
        if len(entries) != expected_count:
            raise RuntimeError(f"{group_name} count drifted")
        partition_counts = _counts([entry.get("source_partition") for entry in entries])
        declared = {
            str(key): int(value)
            for key, value in _require_mapping(
                exact_partitions.get(group_name), label=f"{group_name} partitions"
            ).items()
        }
        if partition_counts != dict(sorted(declared.items())):
            raise RuntimeError(f"{group_name} partition counts drifted")
        for entry in entries:
            entry_id = entry.get("entry_id")
            if not isinstance(entry_id, str) or not entry_id or entry_id in seen:
                raise RuntimeError(f"duplicate or invalid source obligation id: {entry_id!r}")
            seen.add(entry_id)
            if entry.get("proof_adjudication_status") != "NOT_ADJUDICATED":
                raise RuntimeError(f"source proof status promoted: {entry_id}")
            rows.append(
                {
                    "entry_id": entry_id,
                    "source_group": group_name,
                    "source_partition": entry.get("source_partition"),
                    "statement": entry.get("statement"),
                    "statement_identity_sha256": entry.get("statement_identity_sha256"),
                    "source_status": entry.get("source_status"),
                    "proof_adjudication_status": entry.get("proof_adjudication_status"),
                    "proof_class": entry.get("proof_class"),
                    "registry_owner": entry.get("registry_owner"),
                    "scientific_owner": entry.get("scientific_owner"),
                    "claim_ceiling": entry.get("claim_ceiling"),
                }
            )
        summaries[group_name] = {
            "row_count": len(entries),
            "partition_counts": partition_counts,
            "source_status_counts": _counts([entry.get("source_status") for entry in entries]),
            "proof_class_counts": _counts([entry.get("proof_class") for entry in entries]),
            "proof_adjudication_status_counts": _counts(
                [entry.get("proof_adjudication_status") for entry in entries]
            ),
        }
    if len(rows) != contract.get("source_obligation_count"):
        raise RuntimeError("source obligation count drifted")
    return rows, summaries


def _vt_program_rows(
    intake: Mapping[str, object],
    spec: Mapping[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if intake.get("status") != "REGISTERED":
        raise RuntimeError("vector/tensor programme intake is not registered")
    boundary = _require_mapping(
        intake.get("claim_boundary"), label="programme intake claim boundary"
    )
    if (
        boundary.get("scientific_status_effect") != "none"
        or boundary.get("claim_ceiling") != "diagnostic_only"
        or boundary.get("theorem_count_claim") != "FORBIDDEN_FROM_RAW_CARDINALITY"
    ):
        raise RuntimeError("vector/tensor programme claim boundary drifted")
    programme = _require_mapping(
        intake.get("vt_theorem_obligations"), label="vt_theorem_obligations"
    )
    entries = _require_records(programme.get("entries"), label="VT programme entries")
    source_expected = {
        str(key): int(value)
        for key, value in _require_mapping(
            programme.get("expected_counts"), label="VT programme expected counts"
        ).items()
    }
    contract_expected = {
        str(key): int(value)
        for key, value in _require_mapping(
            spec["status_contract"].get("vt_programme_partition"),
            label="VT programme partition contract",
        ).items()
    }
    if source_expected != contract_expected:
        raise RuntimeError("VT programme partition contract disagrees with intake")

    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    partitions: list[str] = []
    proof_status = spec["status_contract"].get(
        "source_proof_adjudication_status"
    )
    if proof_status != "NOT_ADJUDICATED":
        raise RuntimeError("unsupported PR-275 source proof status")
    for entry in entries:
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id or entry_id in seen:
            raise RuntimeError(f"duplicate or invalid VT programme id: {entry_id!r}")
        seen.add(entry_id)
        if entry_id.startswith("VT-T"):
            partition = "VT-T"
            expected_class = "TC"
        elif entry_id.startswith("VT-S"):
            partition = "VT-S"
            expected_class = "ST"
        else:
            raise RuntimeError(f"invalid VT programme partition: {entry_id}")
        partitions.append(partition)
        if (
            entry.get("proof_class") != expected_class
            or entry.get("registration_status") != "REGISTERED_OBLIGATION"
            or entry.get("claim_ceiling") != "diagnostic_only"
        ):
            raise RuntimeError(f"VT programme contract drifted: {entry_id}")
        title = entry.get("title")
        source_status = entry.get("source_status")
        if not isinstance(title, str) or not title.strip():
            raise RuntimeError(f"VT programme title is missing: {entry_id}")
        if not isinstance(source_status, str) or not source_status.strip():
            raise RuntimeError(f"VT programme source status is missing: {entry_id}")
        rows.append(
            {
                "entry_id": entry_id,
                "source_group": "vt_programme_obligations",
                "source_partition": partition,
                "title": title,
                "source_record_sha256": _canonical_sha256(entry),
                "proof_class": entry.get("proof_class"),
                "registry_owner": entry.get("registry_owner"),
                "scientific_owner": entry.get("scientific_owner"),
                "dependencies": entry.get("dependencies"),
                "evidence_path": entry.get("evidence_path"),
                "source_status": source_status,
                "registration_status": entry.get("registration_status"),
                "proof_adjudication_status": proof_status,
                "claim_ceiling": entry.get("claim_ceiling"),
            }
        )
    partition_counts = _counts(partitions)
    if partition_counts != dict(sorted(source_expected.items())):
        raise RuntimeError("VT programme partition counts drifted")
    return rows, {
        "row_count": len(rows),
        "row_count_is_proved_theorem_count": False,
        "partition_counts": partition_counts,
        "source_status_counts": _counts([row["source_status"] for row in rows]),
        "proof_adjudication_status_counts": _counts(
            [row["proof_adjudication_status"] for row in rows]
        ),
    }


def _source_reference_index(
    *,
    source_rows: list[dict[str, object]],
    vt_rows: list[dict[str, object]],
    signatures: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    index: dict[str, dict[str, object]] = {}
    for registry_id, rows in (
        ("theorem_signatures_v3", source_rows),
        ("vt_programme_intake", vt_rows),
    ):
        for row in rows:
            entry_id = str(row["entry_id"])
            if entry_id in index:
                raise RuntimeError(f"duplicate proof source reference: {entry_id}")
            index[entry_id] = {
                "registry_id": registry_id,
                "entry_id": entry_id,
                "source_group": row["source_group"],
                "source_partition": row["source_partition"],
                "proof_adjudication_status": row["proof_adjudication_status"],
            }

    oracle = _require_mapping(signatures.get("oracle"), label="v3 oracle")
    links = _require_records(oracle.get("statement_links"), label="v3 oracle links")
    if len(links) != oracle.get("proposition_count"):
        raise RuntimeError("v3 oracle link count drifted")
    for link in links:
        proposition_id = link.get("proposition_id")
        entry_id = link.get("entry_id")
        if (
            not isinstance(proposition_id, str)
            or proposition_id in index
            or not isinstance(entry_id, str)
            or entry_id not in index
            or link.get("proof_effect") != "none"
        ):
            raise RuntimeError(f"invalid v3 oracle source link: {proposition_id!r}")
        target = index[entry_id]
        index[proposition_id] = {
            "registry_id": "theorem_signatures_v3_oracle_alias",
            "entry_id": entry_id,
            "alias_id": proposition_id,
            "source_group": target["source_group"],
            "source_partition": target["source_partition"],
            "proof_adjudication_status": target["proof_adjudication_status"],
        }
    return index


def _evidence_layer(
    *,
    layer_id: str,
    records: list[Mapping[str, object]],
    record_id_field: str,
    verdict_field: str,
    reference_index: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    normalized: list[dict[str, object]] = []
    seen: set[str] = set()
    for record in records:
        record_id = record.get(record_id_field)
        if not isinstance(record_id, str) or not record_id or record_id in seen:
            raise RuntimeError(f"{layer_id} has duplicate or invalid record id")
        seen.add(record_id)
        verdict = record.get(verdict_field)
        if not isinstance(verdict, str) or not verdict:
            raise RuntimeError(f"{layer_id} record {record_id} lacks a verdict")
        obligation_id = record.get("obligation_id", record.get("theorem_id"))
        if not isinstance(obligation_id, str) or obligation_id not in reference_index:
            raise RuntimeError(
                f"{layer_id} record {record_id} has unresolved obligation {obligation_id!r}"
            )
        source_reference = dict(reference_index[obligation_id])
        proof_status = record.get(
            "source_proof_adjudication_status",
            source_reference["proof_adjudication_status"],
        )
        if proof_status != source_reference["proof_adjudication_status"]:
            raise RuntimeError(
                f"{layer_id} record {record_id} disagrees with source proof status"
            )
        relation = record.get(
            "relation_to_source", record.get("source_disposition")
        )
        if not isinstance(relation, str) or not relation:
            raise RuntimeError(f"{layer_id} record {record_id} lacks source relation")
        if record.get("claim_ceiling") != "diagnostic_only":
            raise RuntimeError(f"{layer_id} record {record_id} changed claim ceiling")
        normalized.append(
            {
                "record_id": record_id,
                "obligation_id": obligation_id,
                "verdict": verdict,
                "source_proof_adjudication_status": proof_status,
                "source_reference": source_reference,
                "relation_to_source": relation,
                "claim_ceiling": record.get("claim_ceiling"),
            }
        )
    return {
        "layer_id": layer_id,
        "record_count": len(normalized),
        "record_count_is_theorem_count": False,
        "verdict_counts": _counts([record["verdict"] for record in normalized]),
        "records": normalized,
    }


def build_proof_atlas(
    *,
    spec: Mapping[str, object],
    sources: Mapping[str, Mapping[str, object]],
    source_hashes: Mapping[str, str],
) -> dict[str, object]:
    signatures = sources["theorem_signatures_v3"]
    if signatures.get("proof_adjudication_status") != "NOT_ADJUDICATED":
        raise RuntimeError("v3 source registry proof status was promoted")
    source_rows, source_summaries = _source_rows(signatures, spec)
    vt_rows, vt_summary = _vt_program_rows(sources["programme_intake"], spec)
    reference_index = _source_reference_index(
        source_rows=source_rows,
        vt_rows=vt_rows,
        signatures=signatures,
    )

    proposal = sources["proposal_registry"]
    proposal_entries = _require_records(proposal.get("entries"), label="proposal entries")
    if len(proposal_entries) != 58:
        raise RuntimeError("proposal registry row count drifted")
    proposal_ids = [record.get("id") for record in proposal_entries]
    if any(not isinstance(entry_id, str) or not entry_id for entry_id in proposal_ids):
        raise RuntimeError("proposal registry contains an invalid id")
    if len(set(proposal_ids)) != len(proposal_ids):
        raise RuntimeError("proposal registry contains duplicate ids")
    signature_proposal_rows = [
        record
        for record in source_rows
        if record["source_group"] == "proposal_registry_rows"
    ]
    proposal_contract = [
        (
            record.get("id"),
            record.get("pillar"),
            record.get("status"),
            record.get("statement"),
        )
        for record in proposal_entries
    ]
    signature_contract = [
        (
            record["entry_id"],
            record["source_partition"],
            record["source_status"],
            record["statement"],
        )
        for record in signature_proposal_rows
    ]
    if proposal_contract != signature_contract:
        raise RuntimeError(
            "proposal registry rows disagree with the frozen v3 source registry"
        )
    proposal_rows = [
        {
            "id": record.get("id"),
            "pillar": record.get("pillar"),
            "section": record.get("section"),
            "source_status": record.get("status"),
            "statement": record.get("statement"),
        }
        for record in proposal_entries
    ]

    t_core = _evidence_layer(
        layer_id="pillar_t_core",
        records=_require_records(sources["pillar_t_core"].get("records"), label="T core records"),
        record_id_field="proof_id",
        verdict_field="verdict",
        reference_index=reference_index,
    )
    t_cas = _evidence_layer(
        layer_id="pillar_t_cas",
        records=_require_records(sources["pillar_t_cas"].get("records"), label="T CAS records"),
        record_id_field="obligation_id",
        verdict_field="verdict",
        reference_index=reference_index,
    )
    s_core = _evidence_layer(
        layer_id="pillar_s_core",
        records=_require_records(sources["pillar_s_core"].get("records"), label="S core records"),
        record_id_field="obligation_id",
        verdict_field="verdict",
        reference_index=reference_index,
    )
    s_inference = _evidence_layer(
        layer_id="pillar_s_inference",
        records=_require_records(
            sources["pillar_s_inference"].get("records"), label="S inference records"
        ),
        record_id_field="theorem_id",
        verdict_field="validation_status",
        reference_index=reference_index,
    )
    for layer in (t_core, t_cas, s_core, s_inference):
        for record in layer["records"]:
            if record["source_proof_adjudication_status"] != "NOT_ADJUDICATED":
                raise RuntimeError(
                    f"{layer['layer_id']} promoted source status for {record['record_id']}"
                )

    cas = sources["cas_adjudication"]
    aggregate = cas.get("aggregate_status")
    if aggregate != spec["status_contract"]["cas_aggregate_allowed"]:
        raise RuntimeError("CAS aggregate status drifted")
    if sources["pillar_t_cas"].get("aggregate_cas_verdict") != aggregate:
        raise RuntimeError("Pillar-T CAS aggregate disagrees with adjudication")
    if cas.get("missing_axes") != [] or cas.get("exceptions_applied") != []:
        raise RuntimeError("CAS aggregate is not an exception-free four-axis result")

    admission = sources["pr274_admission_result"]
    admission_contract = spec["data_admission_contract"]
    if (
        admission.get("status") != admission_contract["required_status"]
        or admission.get("admitted_count") != admission_contract["required_admitted_count"]
        or admission.get("pilot_executed") is not admission_contract["required_pilot_executed"]
    ):
        raise RuntimeError("PR-274 data-admission boundary drifted")

    payload: dict[str, object] = {
        "schema": "htt.pr275.proof_atlas.v1",
        "atlas_id": "PR275-GENERATED-PROOF-ATLAS-V1",
        "owner": "COMMON",
        "contributors": ["HTT", "MIO", "OBSSTAT"],
        "scope": "pre-solver generated proof-status atlas",
        "artifact_mode": "generated_report_diagnostic",
        "claim_ceiling": "diagnostic_only",
        "source_status_promotion": False,
        "counting_rule": spec["counting_contract"]["semantic_guard"],
        "cardinality_aliases": dict(spec["counting_contract"]["cardinality_aliases"]),
        "source_obligation_registry": {
            "row_count": len(source_rows),
            "row_count_is_proved_theorem_count": False,
            "group_summaries": source_summaries,
            "proof_adjudication_status_counts": _counts(
                [record["proof_adjudication_status"] for record in source_rows]
            ),
            "records": source_rows,
        },
        "vt_programme_registry": {
            **vt_summary,
            "proof_status_rule": (
                "REGISTERED programme obligations remain NOT_ADJUDICATED; "
                "evidence records never promote these source rows."
            ),
            "records": vt_rows,
        },
        "proposal_registry": {
            "row_count": len(proposal_rows),
            "row_count_is_proved_theorem_count": False,
            "pillar_counts": _counts([record["pillar"] for record in proposal_rows]),
            "source_status_counts": _counts(
                [record["source_status"] for record in proposal_rows]
            ),
            "records": proposal_rows,
        },
        "evidence_layers": {
            layer["layer_id"]: layer
            for layer in (t_core, t_cas, s_core, s_inference)
        },
        "cas_adjudication": {
            "aggregate_status": aggregate,
            "axis_statuses": cas.get("axis_statuses"),
            "missing_axes": cas.get("missing_axes"),
            "exceptions_applied": cas.get("exceptions_applied"),
            "claim_promotion_cas_eligible": cas.get("claim_promotion_cas_eligible"),
            "source_status_effect": "none",
        },
        "data_admission": {
            "status": admission.get("status"),
            "admitted_count": admission.get("admitted_count"),
            "pilot_executed": admission.get("pilot_executed"),
            "observed_data_figure_allowed": False,
        },
        "source_identities": dict(source_hashes),
        "allowed_use": [
            "registry status audit",
            "evidence-layer gap analysis",
            "synthetic diagnostic reporting",
        ],
        "forbidden_use": [
            "proved-theorem count inferred from raw rows",
            "source theorem promotion",
            "observed-data inference",
            "native solver or morphology-atlas validation",
            "geometry or Bianchi family identification",
        ],
        "caveats": [
            f"All {len(source_rows)} v3 source obligations remain NOT_ADJUDICATED.",
            f"All {len(vt_rows)} VT programme obligations remain NOT_ADJUDICATED.",
            "Evidence-layer verdicts are scoped records, not source theorem promotions.",
            "The 65 and 58 labels are cardinality aliases, not literal proof pillars.",
        ],
    }
    return _with_content_id(payload)


def build_synthetic_analysis(
    *,
    spec: Mapping[str, object],
    pack: Mapping[str, object],
    pack_sha256: str,
) -> dict[str, object]:
    contract = spec["synthetic_analysis_contract"]
    if pack.get("pack_id") != contract["source_pack"]:
        raise RuntimeError("PR-273 diagnostic pack identity drifted")
    if pack.get("observed_data") is not False:
        raise RuntimeError("synthetic analysis cannot consume observed data")
    cases = _require_records(pack.get("case_results"), label="PR-273 case results")
    verdicts = _require_records(pack.get("case_verdicts"), label="PR-273 case verdicts")
    expected_ids = list(contract["exact_case_ids"])
    if [case.get("case_id") for case in cases] != expected_ids:
        raise RuntimeError("PR-273 synthetic case membership/order drifted")
    verdict_ids = [record.get("case_id") for record in verdicts]
    if verdict_ids != expected_ids:
        raise RuntimeError("PR-273 case-verdict membership/order drifted")
    for record in verdicts:
        scenario = record.get("scenario")
        if not isinstance(scenario, str) or not scenario.strip():
            raise RuntimeError(
                f"PR-273 case verdict {record.get('case_id')!r} lacks a scenario"
            )
    scenario_by_id = {record.get("case_id"): record.get("scenario") for record in verdicts}

    def finite_abs_max(values: object, *, label: str) -> float:
        if not isinstance(values, list):
            raise RuntimeError(f"{label} must be a list")
        finite: list[float] = []
        for value in values:
            if value is None:
                continue
            number = float(value)
            if not math.isfinite(number):
                raise RuntimeError(f"{label} contains a non-finite value")
            finite.append(abs(number))
        if not finite:
            raise RuntimeError(f"{label} has no finite value")
        return max(finite)

    summaries: list[dict[str, object]] = []
    for case in cases:
        case_id = str(case["case_id"])
        summaries.append(
            {
                "case_id": case_id,
                "scenario": scenario_by_id[case_id],
                "partition": case.get("partition"),
                "max_finite_abs_x": finite_abs_max(
                    case.get("x_values"), label=f"{case_id}.x_values"
                ),
                "max_finite_abs_q": finite_abs_max(
                    case.get("q_values"), label=f"{case_id}.q_values"
                ),
                "depth_mean_normalized_score": float(
                    case.get("depth_mean_normalized_score")
                ),
                "depth_alert": case.get("depth_alert"),
                "missing_functional": case.get("missing_functional"),
                "geometry_status": case.get("geometry_status"),
                "local_global_status": case.get("local_global_status"),
                "compatibility_status": case.get("compatibility_status"),
            }
        )
    partition_counts = _counts([row["partition"] for row in summaries])
    declared_partition_counts = {
        str(key): int(value) for key, value in contract["exact_partitions"].items()
    }
    if partition_counts != dict(sorted(declared_partition_counts.items())):
        raise RuntimeError("PR-273 partition counts drifted")
    threshold = float(pack.get("depth_alert_threshold"))
    if not math.isfinite(threshold) or threshold <= 0:
        raise RuntimeError("depth alert threshold is invalid")

    payload: dict[str, object] = {
        "schema": "htt.pr275.synthetic_case_analysis.v1",
        "analysis_id": "PR275-SYNTHETIC-CASE-DIAGNOSTICS-V1",
        "owner": "COMMON",
        "scope": "registered PR-273 synthetic case summary",
        "artifact_mode": "synthetic_diagnostic",
        "claim_ceiling": "diagnostic_only",
        "plot_category": "VALIDATION",
        "observed_data": False,
        "source_pack": {
            "path": "docs/research_program/vector_tensor/integration/PR273_DIAGNOSTIC_PACK.json",
            "sha256": "sha256:" + pack_sha256,
            "content_id": pack.get("content_id"),
            "config_identity": pack.get("config_identity"),
            "seed": pack.get("seed"),
            "transfer_source": pack.get("transfer_source"),
        },
        "quantity_definitions": {
            "max_finite_abs_x": "maximum absolute finite x coordinate per registered synthetic case",
            "max_finite_abs_q": "maximum absolute finite Q coordinate per registered synthetic case",
            "depth_mean_normalized_score": "registered PR-273 depth-coherence diagnostic score",
            "missing_functional": "at least one registered functional channel is unavailable",
        },
        "units": {
            "max_finite_abs_x": "dimensionless registered normalized diagnostic coordinate",
            "max_finite_abs_q": "dimensionless registered normalized stress coordinate",
            "depth_mean_normalized_score": "dimensionless normalized score",
            "missing_functional": "categorical boolean; no numeric unit",
            "case_id": "categorical",
        },
        "categorical_encodings": {
            "missing_functional": {
                "source_type": "boolean",
                "true_marker": "x",
                "panel": "B",
                "data_coordinate_anchor": "depth_mean_normalized_score",
                "label": "missing functional",
                "label_position": "display-only point offset from the data anchor",
                "display_offset_has_data_semantics": False,
            }
        },
        "normalization": {
            "x_q": "finite absolute maximum within each case; no cross-case rescaling",
            "depth": "PR-273 registered mean_normalized_score; no PR-275 refit",
        },
        "frame": "registered per-case JointAnisotropyState conventions; plotted magnitudes only",
        "coordinates": "categorical case ID ordered C01 through C05",
        "depth_alert_threshold": threshold,
        "partition_counts": partition_counts,
        "case_summaries": summaries,
        "allowed_use": [
            "synthetic pipeline validation",
            "held-out diagnostic comparison",
            "missing-channel and depth-confounding illustration",
        ],
        "forbidden_use": [
            "observed-data inference",
            "proof or readiness evidence",
            "geometry detection",
            "Bianchi family identification or ranking",
        ],
        "caveats": [
            "Five deterministic synthetic cases are not a population sample.",
            "The x and Q maxima are descriptive coordinates, not estimators.",
            "A depth alert is a registered synthetic diagnostic flag only.",
        ],
    }
    return _with_content_id(payload)


def build_figure_bytes(analysis: Mapping[str, object]) -> bytes:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    rows = analysis["case_summaries"]
    case_ids = [str(row["case_id"]) for row in rows]
    x_values = np.asarray([float(row["max_finite_abs_x"]) for row in rows])
    q_values = np.asarray([float(row["max_finite_abs_q"]) for row in rows])
    depth = np.asarray([float(row["depth_mean_normalized_score"]) for row in rows])
    missing = np.asarray([bool(row["missing_functional"]) for row in rows])
    positions = np.arange(len(case_ids), dtype=float)
    threshold = float(analysis["depth_alert_threshold"])

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.0,
            "axes.titlesize": 10.5,
            "axes.labelsize": 9.5,
            "legend.fontsize": 8.2,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 5.8), dpi=160)
    fig.patch.set_facecolor("white")

    width = 0.34
    axes[0].axvspan(2.5, 4.5, color="#f0f0f0", zorder=0)
    axes[0].bar(
        positions - width / 2,
        x_values,
        width,
        label=r"max finite $|x|$",
        color="#3b78b5",
        edgecolor="white",
        linewidth=0.6,
    )
    axes[0].bar(
        positions + width / 2,
        q_values,
        width,
        label=r"max finite $|Q|$",
        color="#e18a2d",
        edgecolor="white",
        linewidth=0.6,
    )
    axes[0].axvline(2.5, color="#777777", linestyle="--", linewidth=0.9)
    axes[0].text(
        3.5,
        0.985,
        "HELD-OUT",
        transform=axes[0].get_xaxis_transform(),
        ha="center",
        va="top",
        color="#666666",
        fontsize=7.5,
    )
    y_top = max(float(x_values.max()), float(q_values.max())) * 1.22
    axes[0].set_ylim(0.0, y_top)
    axes[0].set_xticks(positions, case_ids)
    axes[0].set_ylabel("dimensionless registered coordinate")
    axes[0].set_title("A  Synthetic departure-coordinate magnitudes", loc="left", fontweight="bold")
    axes[0].grid(axis="y", color="#d9d9d9", linewidth=0.6, alpha=0.8)
    axes[0].legend(loc="upper left", frameon=False)

    axes[1].axvspan(2.5, 4.5, color="#f0f0f0", zorder=0)
    colors = ["#4c9b75" if value <= threshold else "#c94c4c" for value in depth]
    axes[1].bar(positions, depth, width=0.58, color=colors, edgecolor="white", linewidth=0.6)
    axes[1].axhline(threshold, color="#8b1a1a", linestyle="--", linewidth=1.2, label=f"registered alert threshold = {threshold:g}")
    axes[1].axvline(2.5, color="#777777", linestyle="--", linewidth=0.9)
    axes[1].text(
        3.5,
        0.985,
        "HELD-OUT",
        transform=axes[1].get_xaxis_transform(),
        ha="center",
        va="top",
        color="#666666",
        fontsize=7.5,
    )
    for index, value in enumerate(depth):
        axes[1].annotate(
            f"{value:g}",
            xy=(index, value),
            xytext=((8, 3) if missing[index] else (0, 3)),
            textcoords="offset points",
            ha=("left" if missing[index] else "center"),
            va="bottom",
            fontsize=8,
        )
        if missing[index]:
            axes[1].scatter(
                index,
                value,
                marker="x",
                s=55,
                color="#b22222",
                linewidth=1.8,
                clip_on=False,
                label="missing functional (categorical)",
            )
            axes[1].annotate(
                "missing functional",
                xy=(index, value),
                xytext=(0, 18),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7.5,
                color="#8b1a1a",
            )
    axes[1].set_ylim(0.0, max(depth.max() * 1.15, threshold * 1.35))
    axes[1].set_xticks(positions, case_ids)
    axes[1].set_ylabel("dimensionless normalized depth score")
    axes[1].set_title("B  Depth-confounding diagnostic", loc="left", fontweight="bold")
    axes[1].grid(axis="y", color="#d9d9d9", linewidth=0.6, alpha=0.8)
    axes[1].legend(loc="upper left", frameon=False)

    fig.suptitle(
        "Registered PR-273 synthetic case diagnostics",
        x=0.06,
        y=0.985,
        ha="left",
        fontsize=13,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.018,
        "VALIDATION • diagnostic_only • five fixed synthetic cases • no observed data",
        ha="center",
        fontsize=8.5,
        color="#444444",
    )
    fig.subplots_adjust(left=0.08, right=0.985, bottom=0.12, top=0.86, wspace=0.28)
    buffer = BytesIO()
    fig.savefig(
        buffer,
        format="png",
        dpi=160,
        facecolor="white",
        metadata={
            "Title": "PR-275 registered synthetic case diagnostics",
            "Author": "COMMON",
            "Description": "VALIDATION diagnostic_only synthetic analysis",
            "Software": f"matplotlib {matplotlib.__version__}",
            "Creation Time": "2026-08-01T00:00:00Z",
        },
    )
    plt.close(fig)
    return buffer.getvalue()


def build_figure_manifest(
    *,
    analysis: Mapping[str, object],
    analysis_bytes: bytes,
    figure_bytes: bytes,
    source_hashes: Mapping[str, str],
) -> dict[str, object]:
    import matplotlib

    payload: dict[str, object] = {
        "schema": "htt.plot_provenance_manifest.v1",
        "figure_id": "PR275-SYNTHETIC-CASE-DIAGNOSTICS-FIGURE-V1",
        "figure_path": "docs/research_program/vector_tensor/report/fig_pr275_synthetic_case_diagnostics.png",
        "figure_sha256": "sha256:" + _sha256_bytes(figure_bytes),
        "source_json": {
            "path": "docs/research_program/vector_tensor/report/SYNTHETIC_CASE_ANALYSIS.json",
            "sha256": "sha256:" + _sha256_bytes(analysis_bytes),
            "content_id": analysis.get("content_id"),
        },
        "owner": "COMMON",
        "scope": "registered PR-273 synthetic-case validation plot",
        "artifact_mode": "synthetic_diagnostic",
        "plot_category": "VALIDATION",
        "categories": ["VALIDATION"],
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "observed_data": False,
        "sky_support_status": "synthetic_not_applicable",
        "covariance_status": "registered_synthetic_case_inputs",
        "null_mock_status": "not_a_null_significance_plot",
        "quantities": analysis.get("quantity_definitions"),
        "units": analysis.get("units"),
        "normalization": analysis.get("normalization"),
        "frame": analysis.get("frame"),
        "coordinates": analysis.get("coordinates"),
        "categorical_encodings": analysis.get("categorical_encodings"),
        "seed": analysis["source_pack"]["seed"],
        "generator": {
            "path": "scripts/vector_tensor/build_pr275_proof_atlas.py",
            "sha256": "sha256:" + _sha256(Path(__file__)),
            "command": "python -B scripts/vector_tensor/build_pr275_proof_atlas.py",
            "matplotlib_version": matplotlib.__version__,
        },
        "source_artifacts": dict(source_hashes),
        "allowed_use": analysis.get("allowed_use"),
        "forbidden_use": analysis.get("forbidden_use"),
        "caveats": analysis.get("caveats"),
    }
    return _with_content_id(payload)


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def build_atlas_markdown(atlas: Mapping[str, object]) -> str:
    source = atlas["source_obligation_registry"]
    vt_programme = atlas["vt_programme_registry"]
    proposal = atlas["proposal_registry"]
    lines = [
        "# Generated Vector/Tensor Proof Atlas",
        "",
        "This file is generated from machine-readable source registries. Raw rows are not theorem counts, and evidence-layer verdicts do not promote source obligations.",
        "",
        "## Counting and source-status boundary",
        "",
        f"- Source obligation rows: `{source['row_count']}`.",
        f"- Source proof status distribution: `{json.dumps(source['proof_adjudication_status_counts'], sort_keys=True)}`.",
        f"- Legacy 65 alias: `{atlas['cardinality_aliases']['requested_pillar_T_65']}`.",
        f"- Proposal 58 alias: `{atlas['cardinality_aliases']['requested_pillar_S_58']}`.",
        f"- Proposal rows: `{proposal['row_count']}` with pillars `{json.dumps(proposal['pillar_counts'], sort_keys=True)}`.",
        f"- VT programme obligations: `{vt_programme['row_count']}` with partitions `{json.dumps(vt_programme['partition_counts'], sort_keys=True)}`; raw cardinality is not a proved-theorem count.",
        "",
        "## Evidence-layer status summary",
        "",
        "| Layer | Evidence records | Verdict distribution | Source promotion |",
        "| --- | ---: | --- | --- |",
    ]
    for layer in atlas["evidence_layers"].values():
        lines.append(
            f"| `{layer['layer_id']}` | {layer['record_count']} | `{json.dumps(layer['verdict_counts'], sort_keys=True)}` | forbidden |"
        )
    lines.extend(
        [
            "",
            "## CAS aggregate",
            "",
            f"- Aggregate: `{atlas['cas_adjudication']['aggregate_status']}`.",
            "- Scope: exact registered CAS obligations only; source theorem rows remain `NOT_ADJUDICATED`.",
            "",
            "## Source obligations",
            "",
            "| ID | Source group | Partition | Proof class | Source status | Proof adjudication | Statement |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in source["records"]:
        lines.append(
            "| `{entry_id}` | `{source_group}` | `{source_partition}` | `{proof_class}` | `{source_status}` | `{proof_adjudication_status}` | {statement} |".format(
                **{key: _escape(value) for key, value in record.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Registered VT programme obligations",
            "",
            "| ID | Partition | Proof class | Source status | Proof adjudication | Title |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in vt_programme["records"]:
        lines.append(
            "| `{entry_id}` | `{source_partition}` | `{proof_class}` | `{source_status}` | `{proof_adjudication_status}` | {title} |".format(
                **{key: _escape(value) for key, value in record.items()}
            )
        )
    lines.extend(["", "## Proposal registry rows", "", "| ID | Pillar | Section | Source status |", "| --- | --- | --- | --- |"])
    for record in proposal["records"]:
        lines.append(
            f"| `{_escape(record['id'])}` | `{_escape(record['pillar'])}` | `{_escape(record['section'])}` | `{_escape(record['source_status'])}` |"
        )
    for layer in atlas["evidence_layers"].values():
        lines.extend(
            [
                "",
                f"## Evidence layer: {layer['layer_id']}",
                "",
                "| Record | Obligation | Resolved source | Evidence verdict | Source proof status | Relation to source |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for record in layer["records"]:
            lines.append(
                f"| `{_escape(record['record_id'])}` | `{_escape(record['obligation_id'])}` | `{_escape(record['source_reference']['registry_id'])}:{_escape(record['source_reference']['entry_id'])}` | `{_escape(record['verdict'])}` | `{_escape(record['source_proof_adjudication_status'])}` | {_escape(record['relation_to_source'])} |"
            )
    lines.extend(
        [
            "",
            "## Data-admission boundary",
            "",
            f"- Status: `{atlas['data_admission']['status']}`.",
            f"- Admitted inputs: `{atlas['data_admission']['admitted_count']}`.",
            f"- Pilot executed: `{str(atlas['data_admission']['pilot_executed']).lower()}`.",
            "- No observed-data figure is authorized.",
            "",
        ]
    )
    return "\n".join(lines)


def build_replication_package(
    *,
    spec: Mapping[str, object],
    sources: Mapping[str, Mapping[str, object]],
    source_hashes: Mapping[str, str],
    generated_hashes: Mapping[str, str],
    atlas: Mapping[str, object],
    analysis: Mapping[str, object],
) -> dict[str, object]:
    import matplotlib
    import numpy

    prereg = sources["pr272_preregistration"]["preregistration"]
    workflow_identities = {
        str(path.relative_to(ROOT)): "sha256:" + _sha256(path)
        for path in (SPEC, Path(__file__).resolve(), RUNNER)
    }
    payload: dict[str, object] = {
        "schema": "htt.pr275.replication_package.v1",
        "package_id": "PR275-REPLICATION-PACKAGE-V1",
        "owner": "COMMON",
        "scope": "local exact replay and registered synthetic reproducibility",
        "claim_ceiling": "diagnostic_only",
        "observed_data": False,
        "provenance_grades": spec["replication_contract"],
        "commands": [
            "python -B scripts/vector_tensor/build_pr275_proof_atlas.py --check",
            "python -B scripts/codex_harness/run_pr275_report.py focused",
            "python -B scripts/codex_harness/run_pr275_report.py adjacent",
            "python -B scripts/codex_harness/run_pr275_report.py smoke",
            "python scripts/check_claim_language.py",
            "python scripts/claim_lint_research_surfaces.py",
            "python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml",
            "python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml",
            "PYTHONPATH=htt/src:htt python -m pytest --collect-only -q",
            "PYTHONPATH=htt/src:htt python -m pytest -m smoke -q",
            "PYTHONPATH=htt/src:htt python -m pytest -q",
        ],
        "environment": {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "numpy_version": numpy.__version__,
            "matplotlib_version": matplotlib.__version__,
            "pyyaml_version": yaml.__version__,
            "source_layout": "PYTHONPATH=htt/src:htt",
        },
        "source_identities": dict(source_hashes),
        "workflow_identities": dict(sorted(workflow_identities.items())),
        "generated_artifact_identities": dict(generated_hashes),
        "seeds": {
            "pr272_master_seed": prereg["random_stream"]["master_seed"],
            "pr272_seed_family": prereg["random_stream"]["seed_family"],
            "pr273_seed": analysis["source_pack"]["seed"],
        },
        "tolerances_and_acceptance": {
            "pr272_nominal_coverage": prereg["confidence"]["nominal_coverage"],
            "pr272_family_confidence": prereg["confidence"]["family_confidence"],
            "pr272_retain_lower_bound": prereg["confidence"]["retain_lower_bound"],
            "pr272_rank_tolerance": prereg["composition"]["rank_tolerance"],
            "pr273_depth_alert_threshold": analysis["depth_alert_threshold"],
            "pr273_config_identity": analysis["source_pack"]["config_identity"],
        },
        "content_identities": {
            "proof_atlas": atlas["content_id"],
            "synthetic_analysis": analysis["content_id"],
        },
        "git_and_worktree_identity": {
            "frozen_parent_candidate": spec["frozen_parent_candidate"],
            "final_closeout_commit": "recorded in docs/PR_DELTAS/pr-275.md after generation; excluded here to avoid self-reference",
            "generator_identity": "sha256:" + _sha256(Path(__file__)),
        },
        "caveats": [
            "Exact replay grade applies to the declared local source identities and environment.",
            "Synthetic reproducibility is not observed-data validation.",
            "Source obligation rows remain NOT_ADJUDICATED.",
            "No native solver or morphology atlas is present.",
            "No Bianchi family identification or ranking is authorized.",
        ],
        "forbidden_use": [
            "source theorem promotion",
            "observed-data inference",
            "native solver validation",
            "geometry or Bianchi family identification",
        ],
    }
    return _with_content_id(payload)


def build_program_report(
    *,
    atlas: Mapping[str, object],
    analysis: Mapping[str, object],
    manifest: Mapping[str, object],
    replication: Mapping[str, object],
) -> str:
    source = atlas["source_obligation_registry"]
    vt_programme = atlas["vt_programme_registry"]
    layers = atlas["evidence_layers"]
    cases = analysis["case_summaries"]
    lines = [
        "# Vector/Tensor MES Proof Programme — Generated Status Report",
        "",
        "Generated source: `PROOF_ATLAS.json`, `SYNTHETIC_CASE_ANALYSIS.json`, the registered evidence layers, and `REPLICATION_PACKAGE.json`. No manuscript number is assigned.",
        "",
        "## Programme status",
        "",
        f"The v3 signature registry contains {source['row_count']} source obligations, all retaining source proof status `NOT_ADJUDICATED`. The programme intake separately contains {vt_programme['row_count']} VT obligations; these are rendered `NOT_ADJUDICATED` because registration alone confers no proof status and no promotion gate is applied. The requested 65 and 58 labels are cardinality aliases, not literal proof-pillar theorem counts. Evidence records below resolve to a registered source row or oracle alias and do not promote it.",
        "",
        f"VT programme partition: `{json.dumps(vt_programme['partition_counts'], sort_keys=True)}`. Its raw row count is not a proved-theorem count.",
        "",
        "| Evidence layer | Records | Derived verdict distribution |",
        "| --- | ---: | --- |",
    ]
    for layer in layers.values():
        lines.append(
            f"| `{layer['layer_id']}` | {layer['record_count']} | `{json.dumps(layer['verdict_counts'], sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "## CAS status",
            "",
            f"The registered aggregate is `{atlas['cas_adjudication']['aggregate_status']}` with no missing axis or exception. Its scope is the exact registered CAS obligations; source proof status remains unchanged.",
            "",
            "## Data-admission result",
            "",
            f"PR-274 reports `{atlas['data_admission']['status']}` with {atlas['data_admission']['admitted_count']} admitted inputs and `pilot_executed={str(atlas['data_admission']['pilot_executed']).lower()}`. Therefore this report contains no admitted-data analysis or observed-data figure.",
            "",
            "## Plot summary",
            "",
            "Figure `fig_pr275_synthetic_case_diagnostics.png` compares the five fixed PR-273 synthetic cases. Panel A shows finite absolute x and Q coordinate maxima; Panel B shows the registered depth-coherence score and alert threshold. The shaded region marks the held-out partition, and the cross marks the missing-channel case.",
            "",
            "## Quantity plotted",
            "",
            "Panel A plots `max_finite_abs_x` and `max_finite_abs_q`, both dimensionless registered normalized diagnostic coordinates. Panel B plots the dimensionless `depth_mean_normalized_score`; the horizontal line is the preregistered threshold. No fitted population parameter or proof count is plotted.",
            "",
            "## Data/script/manifest provenance",
            "",
            f"The source JSON is `SYNTHETIC_CASE_ANALYSIS.json` (file identity `{manifest['source_json']['sha256']}`), derived from the exact PR-273 diagnostic pack at seed `{analysis['source_pack']['seed']}`. The generator is `scripts/vector_tensor/build_pr275_proof_atlas.py`; the figure manifest is `fig_pr275_synthetic_case_diagnostics.manifest.json` (canonical content identity `{manifest['content_id']}`). Its exact file identity is recorded separately in `REPLICATION_PACKAGE.json`.",
            "",
            "## Category and claim tier",
            "",
            "Category: `VALIDATION` (exactly one category). Artifact mode: `synthetic_diagnostic`. Claim tier: `diagnostic_only`. Transfer source: `none`.",
            "",
            "## Interpretation",
            "",
            "The fixed cases exercise scalar-limit, tensor-only, missing-channel, local/global-degenerate, and mask/depth-confounded paths. C05 crosses the registered depth alert threshold; C03 retains a missing functional channel. The C03 cross is anchored at its actual depth score of zero; its text uses a display-only point offset and carries no numerical y meaning. These are pipeline-behavior diagnostics on the registered synthetic benchmark.",
            "",
            "## What this plot does not show",
            "",
            "It does not show observed sky or survey data, a population estimate, posterior odds, model evidence, theorem proof counts, native transfer validation, geometry detection, or Bianchi family identification/ranking.",
            "",
            "## Missing validation before publication",
            "",
            "Observed-data publication would require separately admitted inputs, exact mask/covariance/transfer contracts, claim-dependent null/prior/PPC/LOOCV evidence, the native low-ell solver and morphology atlas where applicable, and independent external review. None is supplied here.",
            "",
            "## Synthetic case table",
            "",
            "| Case | Scenario | Partition | max finite abs x | max finite abs Q | Depth score | Missing channel |",
            "| --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in cases:
        lines.append(
            f"| `{row['case_id']}` | `{row['scenario']}` | `{row['partition']}` | {row['max_finite_abs_x']:.6g} | {row['max_finite_abs_q']:.6g} | {row['depth_mean_normalized_score']:.6g} | `{str(row['missing_functional']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Replication package",
            "",
            f"`REPLICATION_PACKAGE.json` (`{replication['content_id']}`) records commands, environment versions, frozen source identities, exact PR-275 spec/generator/runner workflow identities, generated artifact hashes, PR-272 seed/tolerance contracts, the PR-273 seed/config identity, caveats, and the diagnostic-only claim ceiling.",
            "",
            "## Claim boundary",
            "",
            "This is a claim-tiered observational/statistical framework status report and synthetic validation summary. Source theorems remain unadjudicated; MIO remains diagnostic-only; HTT retains model-dependent inference ownership. Native solver/atlas and family-identification claims remain outside scope.",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs() -> dict[Path, bytes]:
    spec = _load_yaml(SPEC)
    if spec.get("pr_id") != "PR-275" or spec.get("claim_ceiling") != "diagnostic_only":
        raise RuntimeError("PR-275 spec identity or claim ceiling drifted")
    sources, source_hashes = _verify_frozen_inputs(spec)
    atlas = build_proof_atlas(spec=spec, sources=sources, source_hashes=source_hashes)
    atlas_json = _json_bytes(atlas)
    atlas_md = build_atlas_markdown(atlas).encode("utf-8")

    pack_path = _repo_file(
        spec["frozen_inputs"]["pr273_diagnostic_pack"]["path"],
        label="PR-273 diagnostic pack",
    )
    analysis = build_synthetic_analysis(
        spec=spec,
        pack=sources["pr273_diagnostic_pack"],
        pack_sha256=_sha256(pack_path),
    )
    analysis_json = _json_bytes(analysis)
    figure = build_figure_bytes(analysis)
    manifest = build_figure_manifest(
        analysis=analysis,
        analysis_bytes=analysis_json,
        figure_bytes=figure,
        source_hashes=source_hashes,
    )
    manifest_json = _json_bytes(manifest)

    generated_hashes = {
        "docs/research_program/vector_tensor/report/PROOF_ATLAS.json": "sha256:" + _sha256_bytes(atlas_json),
        "docs/research_program/vector_tensor/report/PROOF_ATLAS.md": "sha256:" + _sha256_bytes(atlas_md),
        "docs/research_program/vector_tensor/report/SYNTHETIC_CASE_ANALYSIS.json": "sha256:" + _sha256_bytes(analysis_json),
        "docs/research_program/vector_tensor/report/fig_pr275_synthetic_case_diagnostics.png": "sha256:" + _sha256_bytes(figure),
        "docs/research_program/vector_tensor/report/fig_pr275_synthetic_case_diagnostics.manifest.json": "sha256:" + _sha256_bytes(manifest_json),
    }
    replication = build_replication_package(
        spec=spec,
        sources=sources,
        source_hashes=source_hashes,
        generated_hashes=generated_hashes,
        atlas=atlas,
        analysis=analysis,
    )
    replication_json = _json_bytes(replication)
    report = build_program_report(
        atlas=atlas,
        analysis=analysis,
        manifest=manifest,
        replication=replication,
    ).encode("utf-8")
    return {
        ATLAS_JSON: atlas_json,
        ATLAS_MD: atlas_md,
        ANALYSIS_JSON: analysis_json,
        FIGURE: figure,
        FIGURE_MANIFEST: manifest_json,
        REPLICATION: replication_json,
        REPORT: report,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that all committed PR-275 outputs are current",
    )
    args = parser.parse_args(argv)
    outputs = build_outputs()
    if args.check:
        stale: list[str] = []
        for path, expected in outputs.items():
            if not path.is_file() or path.read_bytes() != expected:
                stale.append(path.relative_to(ROOT).as_posix())
        if stale:
            raise RuntimeError("stale PR-275 generated outputs: " + ", ".join(stale))
        print("OK: PR-275 proof atlas, plot, report, and replication pack are current")
        return 0
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path, payload in outputs.items():
        path.write_bytes(payload)
        print(
            "WROTE "
            f"{path.relative_to(ROOT)} "
            f"sha256:{_sha256_bytes(payload)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
