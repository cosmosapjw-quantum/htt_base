#!/usr/bin/env python3
"""Build and validate the PR-260 vector/tensor programme intake registry."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Mapping, Sequence

import yaml


REPO = Path(__file__).resolve().parents[2]
PLAN_PATH = Path(
    "docs/research_program/"
    "HTT_VECTOR_TENSOR_MES_TWO_PILLAR_UPGRADE_PLAN_20260730.md"
)
PROGRAM_PATH = Path(
    "docs/research_program/vector_tensor/"
    "VECTOR_TENSOR_PROOF_PROGRAM_V1.yaml"
)
PROPOSAL_PATH = Path(
    "docs/research_program/vector_tensor/"
    "proof_registry_two_pillars.yaml"
)
LEGACY_PATH = Path("docs/research_program/THEOREM_REGISTRY.yaml")
SIGNATURES_PATH = Path("docs/research_program/THEOREM_SIGNATURES_V2.yaml")
OUTPUT_PATH = Path(
    "docs/research_program/vector_tensor/"
    "PROGRAM_INTAKE_REGISTRY_V1.yaml"
)

PROGRAM_SCHEMA = "htt.vector_tensor_proof_program.draft.v1"
PROPOSAL_SCHEMA = "htt.proof_registry.two_pillars.v1"
INTAKE_SCHEMA = "htt.vector_tensor_program_intake.v1"
PROOF_CLASSES = frozenset({"U", "TC", "ST"})
VT_THEOREM_ROUTES = {
    **{
        f"VT-T{index}": ("COMMON_PHYSICS", ["PR-268", "PR-269"])
        for index in (1, 2, 3, 4, 9, 10)
    },
    **{
        f"VT-T{index}": ("COMMON_PHYSICS", ["PR-268", "PR-269", "PR-270"])
        for index in (5, 6, 7, 8, 11, 12, 13, 14)
    },
    **{
        f"VT-S{index}": ("HTT_STATISTICS", ["PR-268", "PR-271"])
        for index in (1, 2, 4, 7, 8)
    },
    **{
        f"VT-S{index}": ("HTT_STATISTICS", ["PR-268", "PR-271", "PR-272"])
        for index in (3, 5, 6, 9, 10, 11, 12, 13, 14)
    },
}
PR_EXTENSION_ORDER = (
    "PR-261",
    "PR-262",
    "PR-263",
    "PR-264",
    "PR-265",
    "PR-266",
    "PR-267",
    "PR-268",
    "PR-269",
    "PR-271",
    "PR-270",
    "PR-272",
    "PR-273",
    "PR-274",
    "PR-275",
)
PR_EXTENSION_DEPENDENCIES = {
    "PR-261": ["PR-260", "PR-249", "PR-256"],
    "PR-262": ["PR-261", "PR-254"],
    "PR-263": ["PR-261", "PR-257"],
    "PR-264": ["PR-262", "PR-263"],
    "PR-265": ["PR-264", "PR-250"],
    "PR-266": ["PR-264"],
    "PR-267": [
        "PR-263",
        "PR-265",
        "PR-266",
        "PR-255",
        "PR-256",
        "PR-258",
    ],
    "PR-268": ["PR-262", "PR-263", "PR-267"],
    "PR-269": ["PR-268"],
    "PR-270": ["PR-269"],
    "PR-271": ["PR-268"],
    "PR-272": ["PR-271"],
    "PR-273": ["PR-270", "PR-272"],
    "PR-274": ["PR-273"],
    "PR-275": ["PR-274"],
}
SOURCE_IDENTITIES = {
    "A1": (
        "docs/research_program/vector_tensor/VECTOR_TENSOR_UPGRADE_REVIEW.md",
        "f66d426ee711239f620fff10d4fc7ce04d267282c05afc8c6181be4fe7a8513a",
    ),
    "A2": (
        "docs/research_program/vector_tensor/vector_tensor_mes_upgrade_blueprint.md",
        "113cd5a40b352c099fbab8a6e884655fbeba4d579f482fdb56cc4343b31d1ab2",
    ),
    "A3": (
        str(PROGRAM_PATH),
        "75d8ac2f40aeb501d046d9c35f56f9bb4e393e191e90eb024cd7b44800682a55",
    ),
    "A4": (
        "docs/research_program/vector_tensor/"
        "STAT_FOUNDATIONS_TENSOR_UPGRADE_20260730.md",
        "f2593ecc293be2a8b4d5e20be0abd545e6ad07026f9b8c713d11ff341721c8d3",
    ),
    "A5": (
        "docs/research_program/vector_tensor/"
        "PROOF_REGISTRY_TWO_PILLARS_20260730.md",
        "bd05a0fe26b15effa9450c4281c90e9496498ae92f9f08c3018f6e8671db54be",
    ),
    "A6": (
        str(PROPOSAL_PATH),
        "2dbe47f44b3920318acd78b1f636ca0ba1dc051358da483ea98db2ba6a719c9a",
    ),
    "A7": (
        "docs/research_program/vector_tensor/"
        "tensor_foundations_oracle_proposal.py",
        "f716cb1bd36930428339f8a7906862f31e9b8a0b5796083bc392bb1811599daf",
    ),
    "A8": (
        "docs/research_program/vector_tensor/"
        "TENSOR_UPGRADE_TWO_PILLARS_SUMMARY_KO.md",
        "5e213beacdee58c1b5116ee4cc98b146ae0d451a936ad058e6aaf27ab6e89981",
    ),
}


class ProgramIntakeError(ValueError):
    """Raised when a source or generated intake violates PR-260."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_sha256(value: object) -> str:
    return _sha256_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _load_yaml(path: Path) -> Mapping[str, object]:
    absolute = REPO / path
    if absolute.is_symlink() or not absolute.is_file():
        raise ProgramIntakeError(f"required source is not a regular file: {path}")
    value = yaml.safe_load(absolute.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ProgramIntakeError(f"source root must be a mapping: {path}")
    return value


def _table_cells(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _plan_blocks() -> tuple[
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
]:
    text = (REPO / PLAN_PATH).read_text(encoding="utf-8")
    legacy_block = text.split(
        "## Appendix B. frozen 65-ID legacy migration inventory", 1
    )[1]
    upper_block = text.split("### A.1 상위 업그레이드 제안", 1)[1].split(
        "### A.2", 1
    )[0]

    legacy: dict[str, dict[str, str]] = {}
    for line in legacy_block.splitlines():
        cells = _table_cells(line)
        if len(cells) < 5 or cells[1] not in {"T", "S"}:
            continue
        entry_id = cells[0]
        if entry_id in {"ID", "---"}:
            continue
        legacy[entry_id] = {
            "primary_pillar": cells[1],
            "legacy_status": cells[2].strip("`"),
            "v2_signature_status": cells[3].strip("`"),
            "title": cells[4],
        }

    obligations: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        cells = _table_cells(line)
        if not cells:
            continue
        match = re.fullmatch(r"(TC-\d{2}|ST-\d{2})\s+(.+)", cells[0])
        if match is None or len(cells) < 5:
            continue
        obligation_id, title = match.groups()
        obligations[obligation_id] = {
            "title": title,
            "target": cells[1],
            "prerequisites": cells[2],
            "owner_route": cells[3],
            "consumer_test": cells[4],
        }
    for line in upper_block.splitlines():
        cells = _table_cells(line)
        if len(cells) < 5 or re.fullmatch(r"U\d+", cells[0]) is None:
            continue
        obligations[cells[0]] = {
            "title": cells[2],
            "target": cells[3],
            "prerequisites": cells[1],
            "owner_route": "COMMON programme intake",
            "consumer_test": cells[4],
        }
    return legacy, obligations, {"plan": {"sha256": _sha256_file(REPO / PLAN_PATH)}}


def _list_of_mappings(
    value: object, *, field: str
) -> tuple[Mapping[str, object], ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or any(not isinstance(row, Mapping) for row in value)
    ):
        raise ProgramIntakeError(f"{field} must be a list of mappings")
    return tuple(value)


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProgramIntakeError(f"{field} must be a non-empty string")
    return value.strip()


def _extract_dependencies(*values: str) -> list[str]:
    found: list[str] = []
    for value in values:
        for item in re.findall(r"PR-\d+", value):
            if item not in found:
                found.append(item)
    return found or ["PR-260"]


def _source_identities() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source_id, (relative, source_sha) in SOURCE_IDENTITIES.items():
        path = REPO / relative
        if path.is_symlink() or not path.is_file():
            raise ProgramIntakeError(f"tracked source missing: {relative}")
        rows.append(
            {
                "source_id": source_id,
                "tracked_path": relative,
                "source_attachment_sha256": source_sha,
                "tracked_sha256": _sha256_file(path),
                "normalization": (
                    "registered_wrapper"
                    if source_id in {"A3", "A6"}
                    else "git_conflict_sentinel_normalized_with_note"
                    if source_id == "A1"
                    else "content_preserved_with_terminal_lf"
                ),
            }
        )
    return rows


def build_payload() -> dict[str, object]:
    program = _load_yaml(PROGRAM_PATH)
    proposal = _load_yaml(PROPOSAL_PATH)
    legacy_registry = _load_yaml(LEGACY_PATH)
    signatures = _load_yaml(SIGNATURES_PATH)
    legacy_rows, obligations, plan_evidence = _plan_blocks()

    if program.get("schema") != PROGRAM_SCHEMA:
        raise ProgramIntakeError("vector/tensor programme schema drifted")
    if program.get("status") != "REGISTERED":
        raise ProgramIntakeError("vector/tensor programme is not REGISTERED")
    if proposal.get("schema") != PROPOSAL_SCHEMA:
        raise ProgramIntakeError("two-pillar proposal schema drifted")
    if proposal.get("registration_status") != "REGISTERED":
        raise ProgramIntakeError("two-pillar proposal is not REGISTERED")

    signature_rows = _list_of_mappings(
        signatures.get("entries"), field="THEOREM_SIGNATURES_V2.entries"
    )
    legacy_source_rows = _list_of_mappings(
        legacy_registry.get("entries"), field="THEOREM_REGISTRY.entries"
    )
    proposal_rows = _list_of_mappings(
        proposal.get("entries"), field="proof registry entries"
    )
    legacy_by_id = {
        _nonempty(row.get("id"), "legacy id"): row for row in legacy_source_rows
    }

    legacy_entries: list[dict[str, object]] = []
    for row in signature_rows:
        entry_id = _nonempty(row.get("id"), "signature id")
        legacy_id = _nonempty(row.get("legacy_id"), f"{entry_id}.legacy_id")
        crosswalk = legacy_rows.get(legacy_id)
        if crosswalk is None:
            raise ProgramIntakeError(
                f"legacy signature lacks Appendix-B partition: {legacy_id}"
            )
        legacy_source = legacy_by_id.get(legacy_id)
        if legacy_source is None:
            raise ProgramIntakeError(f"legacy registry lacks {legacy_id}")
        primary_pillar = crosswalk["primary_pillar"]
        legacy_entries.append(
            {
                "id": entry_id,
                "source_id": legacy_id,
                "title": _nonempty(row.get("title"), f"{entry_id}.title"),
                "source_partition": primary_pillar,
                "proof_class": "TC" if primary_pillar == "T" else "ST",
                "registry_owner": "COMMON",
                "scientific_owner": _nonempty(
                    legacy_source.get("owner"), f"{legacy_id}.owner"
                ),
                "dependencies": ["PR-124", "PR-125"],
                "evidence_path": f"{SIGNATURES_PATH}#{entry_id}",
                "source_status": _nonempty(
                    row.get("signature_status"), f"{entry_id}.signature_status"
                ),
                "registration_status": "REGISTERED_SOURCE_RECORD",
                "claim_ceiling": "diagnostic_only",
            }
        )

    proposal_entries: list[dict[str, object]] = []
    proposal_owner = {
        "I": "COMMON_PHYSICS",
        "II": "HTT_STATISTICS",
        "BRIDGE": "COMMON",
    }
    proposal_dependencies = {
        "I": ["PR-268", "PR-269", "PR-270"],
        "II": ["PR-268", "PR-271", "PR-272"],
        "BRIDGE": ["PR-268"],
    }
    for row in proposal_rows:
        entry_id = _nonempty(row.get("id"), "proposal id")
        source_pillar = _nonempty(
            row.get("pillar"), f"{entry_id}.source pillar"
        )
        if source_pillar not in proposal_owner:
            raise ProgramIntakeError(
                f"{entry_id}: unsupported source pillar {source_pillar}"
            )
        proof_class = {
            "I": "TC",
            "II": "ST",
            "BRIDGE": "U",
        }[source_pillar]
        proposal_entries.append(
            {
                "id": entry_id,
                "source_partition": source_pillar,
                "proof_class": proof_class,
                "registry_owner": "COMMON",
                "scientific_owner": proposal_owner[source_pillar],
                "dependencies": proposal_dependencies[source_pillar],
                "evidence_path": f"{PROPOSAL_PATH}#{entry_id}",
                "statement_identity_sha256": _canonical_sha256(row),
                "source_status": _nonempty(
                    row.get("status"), f"{entry_id}.status"
                ),
                "registration_status": "REGISTERED_PROPOSAL_ROW",
                "claim_ceiling": "diagnostic_only",
            }
        )

    obligation_entries: list[dict[str, object]] = []
    for obligation_id in sorted(
        obligations,
        key=lambda value: (
            {"U": 0, "TC": 1, "ST": 2}[
                "TC" if value.startswith("TC-") else
                "ST" if value.startswith("ST-") else "U"
            ],
            int(re.search(r"\d+", value).group()),
        ),
    ):
        row = obligations[obligation_id]
        proof_class = (
            "TC" if obligation_id.startswith("TC-")
            else "ST" if obligation_id.startswith("ST-")
            else "U"
        )
        obligation_entries.append(
            {
                "id": obligation_id,
                "title": row["title"],
                "proof_class": proof_class,
                "registry_owner": "COMMON",
                "owner_route": row["owner_route"],
                "dependencies": _extract_dependencies(
                    row["target"],
                    row["prerequisites"],
                    row["owner_route"],
                ),
                "source_target": row["target"],
                "prerequisites": row["prerequisites"],
                "consumer_test": row["consumer_test"],
                "evidence_path": f"{PLAN_PATH}#{obligation_id}",
                "registration_status": "REGISTERED_OBLIGATION",
                "claim_ceiling": "diagnostic_only",
            }
        )

    theorem_groups = program.get("theorems")
    if not isinstance(theorem_groups, Mapping):
        raise ProgramIntakeError("programme theorems must be a mapping")
    vt_t = _list_of_mappings(
        theorem_groups.get("pillar_T"), field="programme pillar_T"
    )
    vt_s = _list_of_mappings(
        theorem_groups.get("pillar_S"), field="programme pillar_S"
    )
    vt_rows = []
    for proof_class, rows in (("TC", vt_t), ("ST", vt_s)):
        for row in rows:
            theorem_id = _nonempty(row.get("id"), "VT theorem id")
            try:
                scientific_owner, dependencies = VT_THEOREM_ROUTES[theorem_id]
            except KeyError as exc:
                raise ProgramIntakeError(
                    f"{theorem_id}: no registered owner/dependency route"
                ) from exc
            vt_rows.append(
                {
                    "id": theorem_id,
                    "title": _nonempty(row.get("title"), "VT theorem title"),
                    "proof_class": proof_class,
                    "registry_owner": "COMMON",
                    "scientific_owner": scientific_owner,
                    "dependencies": dependencies,
                    "evidence_path": f"{PROGRAM_PATH}#{theorem_id}",
                    "source_status": _nonempty(
                        row.get("status"), "VT theorem status"
                    ),
                    "proof_mode": _nonempty(
                        row.get("proof_mode"), "VT theorem proof_mode"
                    ),
                    "registration_status": "REGISTERED_OBLIGATION",
                    "claim_ceiling": "diagnostic_only",
                }
            )

    payload: dict[str, object] = {
        "schema": INTAKE_SCHEMA,
        "status": "REGISTERED",
        "authority": "PR-260",
        "registered_on": "2026-07-30",
        "source_schemas": {
            "programme": PROGRAM_SCHEMA,
            "two_pillar_proposal": PROPOSAL_SCHEMA,
            "legacy_signatures": signatures.get("schema"),
        },
        "claim_boundary": {
            "scientific_status_effect": "none",
            "claim_ceiling": "diagnostic_only",
            "theorem_count_claim": "FORBIDDEN_FROM_RAW_CARDINALITY",
            "native_solver_result": False,
            "family_identification": False,
            "observational_use": False,
        },
        "source_identities": _source_identities(),
        "cardinality_aliases": {
            "requested_pillar_T_65": "legacy_signature_inventory",
            "requested_pillar_S_58": "proposal_registry_rows",
            "semantic_guard": (
                "These are cardinality aliases only. Scientific routing uses "
                "source_partition: legacy 65 = 31 T + 34 S; proposal 58 = "
                "30 I + 24 II + 4 BRIDGE."
            ),
        },
        "legacy_signature_inventory": {
            "expected_count": 65,
            "source_partition_counts": {"T": 31, "S": 34},
            "entries": legacy_entries,
        },
        "proposal_registry_rows": {
            "expected_count": 58,
            "source_partition_counts": {"I": 30, "II": 24, "BRIDGE": 4},
            "entries": proposal_entries,
        },
        "obligation_classes": {
            "expected_counts": {"U": 9, "TC": 20, "ST": 25},
            "entries": obligation_entries,
        },
        "vt_theorem_obligations": {
            "expected_counts": {"VT-T": 14, "VT-S": 14},
            "entries": vt_rows,
        },
        "canonical_objects": list(program.get("canonical_objects", [])),
        "canonical_dag_extension": list(PR_EXTENSION_ORDER),
        "canonical_dag_dependencies": PR_EXTENSION_DEPENDENCIES,
        "source_plan_evidence": plan_evidence,
    }
    validate_payload(payload)
    return payload


def _entry_rows(
    payload: Mapping[str, object], section: str
) -> tuple[Mapping[str, object], ...]:
    value = payload.get(section)
    if not isinstance(value, Mapping):
        raise ProgramIntakeError(f"{section} must be a mapping")
    return _list_of_mappings(value.get("entries"), field=f"{section}.entries")


def validate_payload(payload: Mapping[str, object]) -> None:
    if payload.get("schema") != INTAKE_SCHEMA:
        raise ProgramIntakeError("intake schema drifted")
    if payload.get("status") != "REGISTERED":
        raise ProgramIntakeError("intake status must be REGISTERED")

    legacy = _entry_rows(payload, "legacy_signature_inventory")
    proposal = _entry_rows(payload, "proposal_registry_rows")
    obligations = _entry_rows(payload, "obligation_classes")
    vt_rows = _entry_rows(payload, "vt_theorem_obligations")
    if len(legacy) != 65 or len(proposal) != 58:
        raise ProgramIntakeError("exact 65/58 source membership is required")
    legacy_ids = [_nonempty(row.get("id"), "legacy entry id") for row in legacy]
    proposal_ids = [
        _nonempty(row.get("id"), "proposal entry id") for row in proposal
    ]
    if len(set(legacy_ids)) != 65 or len(set(proposal_ids)) != 58:
        raise ProgramIntakeError("65/58 memberships must be internally unique")
    if set(legacy_ids) & set(proposal_ids):
        raise ProgramIntakeError("legacy and proposal memberships must be disjoint")

    def counts(rows: Sequence[Mapping[str, object]], field: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for row in rows:
            key = _nonempty(row.get(field), field)
            result[key] = result.get(key, 0) + 1
        return result

    if counts(legacy, "source_partition") != {"T": 31, "S": 34}:
        raise ProgramIntakeError("legacy source partition must be 31 T / 34 S")
    if counts(proposal, "source_partition") != {
        "I": 30,
        "II": 24,
        "BRIDGE": 4,
    }:
        raise ProgramIntakeError(
            "proposal source partition must be 30 I / 24 II / 4 BRIDGE"
        )
    if counts(obligations, "proof_class") != {"U": 9, "TC": 20, "ST": 25}:
        raise ProgramIntakeError("obligation classes must be 9 U / 20 TC / 25 ST")
    if counts(vt_rows, "proof_class") != {"TC": 14, "ST": 14}:
        raise ProgramIntakeError("VT obligations must be 14 TC / 14 ST")

    all_ids = legacy_ids + proposal_ids + [
        _nonempty(row.get("id"), "obligation id") for row in obligations
    ] + [_nonempty(row.get("id"), "VT id") for row in vt_rows]
    if len(all_ids) != len(set(all_ids)):
        raise ProgramIntakeError("legacy/proposal/U-TC-ST/VT identifiers overlap")

    for section, rows in (
        ("legacy", legacy),
        ("proposal", proposal),
        ("obligation", obligations),
        ("VT", vt_rows),
    ):
        for row in rows:
            if row.get("proof_class") not in PROOF_CLASSES:
                raise ProgramIntakeError(f"{section} entry has invalid proof class")
            _nonempty(
                row.get("registry_owner"), f"{section}.registry_owner"
            )
            _nonempty(row.get("evidence_path"), f"{section}.evidence_path")
            dependencies = row.get("dependencies")
            if (
                not isinstance(dependencies, Sequence)
                or isinstance(dependencies, (str, bytes))
                or not dependencies
            ):
                raise ProgramIntakeError(f"{section} dependencies must be nonempty")
            if row.get("claim_ceiling") != "diagnostic_only":
                raise ProgramIntakeError(f"{section} claim ceiling drifted")

    aliases = payload.get("cardinality_aliases")
    if not isinstance(aliases, Mapping):
        raise ProgramIntakeError("cardinality aliases must be a mapping")
    if aliases.get("requested_pillar_T_65") != "legacy_signature_inventory":
        raise ProgramIntakeError("65-entry cardinality alias was reinterpreted")
    if aliases.get("requested_pillar_S_58") != "proposal_registry_rows":
        raise ProgramIntakeError("58-entry cardinality alias was reinterpreted")
    guard = _nonempty(aliases.get("semantic_guard"), "semantic_guard")
    for token in ("31 T", "34 S", "30 I", "24 II", "4 BRIDGE"):
        if token not in guard:
            raise ProgramIntakeError(
                f"cardinality semantic guard omits source partition {token}"
            )

    vt_t_ids = {
        _nonempty(row.get("id"), "VT-T id")
        for row in vt_rows
        if row.get("proof_class") == "TC"
    }
    vt_s_ids = {
        _nonempty(row.get("id"), "VT-S id")
        for row in vt_rows
        if row.get("proof_class") == "ST"
    }
    if vt_t_ids != {f"VT-T{i}" for i in range(1, 15)}:
        raise ProgramIntakeError("VT-T identifiers drifted")
    if vt_s_ids != {f"VT-S{i}" for i in range(1, 15)}:
        raise ProgramIntakeError("VT-S identifiers drifted")
    if tuple(payload.get("canonical_dag_extension", ())) != PR_EXTENSION_ORDER:
        raise ProgramIntakeError("canonical extension order drifted")
    if payload.get("canonical_dag_dependencies") != PR_EXTENSION_DEPENDENCIES:
        raise ProgramIntakeError("canonical extension dependencies drifted")


def render_payload(payload: Mapping[str, object]) -> str:
    return yaml.safe_dump(
        dict(payload),
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    rendered = render_payload(build_payload())
    output = REPO / OUTPUT_PATH
    if args.write:
        output.write_text(rendered, encoding="utf-8")
        print(OUTPUT_PATH)
        return 0
    if not output.is_file():
        print(f"missing generated intake registry: {OUTPUT_PATH}")
        return 1
    if output.read_text(encoding="utf-8") != rendered:
        print(f"generated intake registry drifted: {OUTPUT_PATH}")
        return 1
    print(
        "OK: PR-260 programme intake "
        "(65 legacy, 58 proposal rows, U9/TC20/ST25)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
