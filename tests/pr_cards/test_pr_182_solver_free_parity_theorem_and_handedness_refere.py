"""PR-182 card gates: solver-free parity theorem + handedness registry.

Backlog DoD: (1) blind four-axis parity identity contract + a
no-data-adjudication reference-signal schema; (2) the theorem registers
only a future native-atlas test vector — no present-data sign comparison
may rank, identify, or adjudicate a family. Kill: any shipped-data
family label/rank/handedness conclusion, production/manuscript consumer,
or pre-native data sign comparison blocks the card.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))

from common.pr182_parity_registry import (  # noqa: E402
    DataAdjudicationAttempt,
    REGISTRY_ENTRIES,
    get_reference_entry,
    registry_payload,
)

SPEC = REPO / "docs/research_program/long_horizon_rescue/pr182_spec.yaml"
ERRATUM = REPO / "docs/research_program/long_horizon_rescue/pr182_spec_erratum.yaml"
CONTRACT = REPO / "docs/generated/pr182_cas/CAS_CONTRACT_PR182_PARITY_V2.json"
ADJUDICATION = REPO / "docs/generated/pr182_cas_adjudication.json"
CARD = REPO / "docs/generated/pr182_result_card.json"
AXES = ("sympy", "sage_singular", "wolfram_xact", "lean")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _card() -> dict:
    return json.loads(CARD.read_text())


def test_spec_frozen_and_card_binds_spec_and_contract() -> None:
    card = _card()
    assert card["metadata"]["spec_sha256"] == _sha(SPEC)
    assert card["metadata"]["contract_sha256"] == _sha(CONTRACT)
    assert "frozen_before_result: true" in SPEC.read_text()


def test_hypothesis_only_gates() -> None:
    meta = _card()["metadata"]
    assert meta["scientific_artifact_mode"] == "hypothesis_only"
    assert meta["public_use"] is False
    assert meta["transfer_source"] == "none"
    assert meta["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C1"}


def test_four_axis_adjudication_is_bound_and_passing() -> None:
    adjudication = json.loads(ADJUDICATION.read_text())
    assert adjudication["contract_sha256"] == _sha(CONTRACT)
    assert adjudication["aggregate_status"] == "CAS_4AXIS_PASS"
    assert set(adjudication["axis_statuses"]) == set(AXES)
    assert all(v == "PASS" for v in adjudication["axis_statuses"].values())
    card = _card()
    assert card["terminal"] == (
        "PARITY_IDENTITIES_CAS_4AXIS_PASS_REGISTRY_REGISTERED"
    )
    assert card["cas"]["adjudication_sha256"] == _sha(ADJUDICATION)


def test_envelopes_bound_blind_and_obligation_uniform() -> None:
    contract = json.loads(CONTRACT.read_text())
    obligations = set(contract["target"]["exact_test_obligations"])
    contract_sha = _sha(CONTRACT)
    shared_computed: dict[str, set] = {}
    for axis in AXES:
        env = json.loads(
            (REPO / f"docs/generated/pr182_cas/axis_result_{axis}.json").read_text()
        )
        assert env["contract_sha256"] == contract_sha, axis
        assert env["status"] == "PASS", axis
        assert set(env["checks"]) == obligations, axis
        assert all(env["checks"].values()), axis
        assert env["sibling_results_read"] == [], axis
        expected = contract["target"]["expected_exact_values"]
        for key, value in expected.items():
            assert env["computed"].get(key) == value, f"{axis}:{key}"
            shared_computed.setdefault(key, set()).add(env["computed"][key])
    for key, values in shared_computed.items():
        assert len(values) == 1, f"cross-engine disagreement on {key}: {values}"


def test_contract_source_pins_match_live_files() -> None:
    contract = json.loads(CONTRACT.read_text())
    for axis_block in contract["axes"].values():
        for ref in axis_block["sources"]:
            assert _sha(REPO / ref["path"]) == ref["sha256"], ref["path"]


def _cas_gate(args: list[str], tmp_path: Path, name: str) -> tuple[int, dict]:
    out = tmp_path / name
    proc = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / ".agent-harness/scripts/cas_gate.py"),
            *args,
            "--out",
            str(out),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.returncode, json.loads(out.read_text())


def test_three_axes_can_never_pass(tmp_path: Path) -> None:
    """Live cas_gate mutation: dropping one axis yields CAS_BLOCKED."""
    results = [
        f"docs/generated/pr182_cas/axis_result_{axis}.json"
        for axis in AXES
        if axis != "lean"
    ]
    code, payload = _cas_gate(
        [
            "adjudicate",
            "--historical-replay",
            "--contract",
            "docs/generated/pr182_cas/CAS_CONTRACT_PR182_PARITY_V2.json",
            "--results",
            *results,
        ],
        tmp_path,
        "adj3.json",
    )
    assert payload["aggregate_status"] == "CAS_BLOCKED"
    assert payload["historical_aggregate_status"] == "CAS_BLOCKED"
    assert payload["claim_promotion_cas_eligible"] is False
    assert "lean" in payload["missing_axes"]
    assert code != 0


def test_committed_adjudication_is_reproducible(tmp_path: Path) -> None:
    """Re-running cas_gate over the sealed envelopes reproduces the verdict."""
    results = [
        f"docs/generated/pr182_cas/axis_result_{axis}.json" for axis in AXES
    ]
    code, payload = _cas_gate(
        [
            "adjudicate",
            "--historical-replay",
            "--contract",
            "docs/generated/pr182_cas/CAS_CONTRACT_PR182_PARITY_V2.json",
            "--results",
            *results,
        ],
        tmp_path,
        "adj4.json",
    )
    committed = json.loads(ADJUDICATION.read_text())
    assert code != 0
    assert payload["aggregate_status"] == "CAS_BLOCKED"
    assert payload["historical_aggregate_status"] == committed["aggregate_status"]
    assert payload["claim_promotion_cas_eligible"] is False
    assert payload["axis_statuses"] == committed["axis_statuses"]
    assert payload["contract_sha256"] == committed["contract_sha256"]


def test_wolfram_parser_rejects_tampered_checks_and_missing_xact() -> None:
    """Parser-level mutations: a False check or a lost xAct receipt kill PASS."""
    sys.path.insert(0, str(REPO / "scripts" / "codex_harness"))
    from run_pr182_cas_axes import _parse_axis_json  # noqa: PLC0415

    genuine = (
        REPO / "docs/generated/pr182_cas/axis_result_wolfram_xact.json"
    )
    tail = json.loads(genuine.read_text())["transcript_tail"]
    assert _parse_axis_json("wolfram_xact", tail)["all_pass"] is True
    tampered = tail.replace(
        '"parity_involution_exact" -> True',
        '"parity_involution_exact" -> False',
    )
    parsed = _parse_axis_json("wolfram_xact", tampered)
    assert parsed["checks"]["parity_involution_exact"] is False
    no_xact = tail.replace("PR182_XACT True", "PR182_XACT False")
    assert _parse_axis_json("wolfram_xact", no_xact)["all_pass"] is False


def test_stale_contract_binding_is_rejected(tmp_path: Path) -> None:
    """Live cas_gate mutation: a tampered contract invalidates envelopes."""
    tampered_rel = "docs/generated/pr182_cas/.tmp_contract_tampered_test.json"
    tampered = REPO / tampered_rel
    contract = json.loads(CONTRACT.read_text())
    contract["target"]["expected_exact_values"]["fixed_space_dim"] = "2"
    tampered.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    try:
        proc = subprocess.run(
            [
                str(REPO / "venv/bin/python"),
                "-B",
                str(REPO / ".agent-harness/scripts/cas_gate.py"),
                "check-axis",
                "--contract",
                tampered_rel,
                "--result",
                "docs/generated/pr182_cas/axis_result_sympy.json",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        tampered.unlink(missing_ok=True)
    assert proc.returncode != 0
    assert "different contract hash" in proc.stdout


def test_sympy_axis_mutations_are_detected(tmp_path: Path) -> None:
    """Perturbed parity matrix and wrong-kernel mutants must fail."""
    source = (REPO / "htt/src/common/pr182_sympy_axis.py").read_text()
    mutants = {
        "parity": source.replace(
            "sp.Matrix([[1, 0], [0, -1]])", "sp.Matrix([[1, 0], [0, 1]])"
        ),
        "kernel": source.replace(
            "sp.sqrt(1 - beta**2) / (1 - beta * mu)",
            "1 / (sp.sqrt(1 - beta**2) * (1 - beta * mu))",
        ),
    }
    for name, text in mutants.items():
        assert text != source, f"mutation {name} did not apply"
        mutant = tmp_path / f"mutant_{name}.py"
        mutant.write_text(text)
        proc = subprocess.run(
            [str(REPO / "venv/bin/python"), "-B", str(mutant)],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=300,
        )
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        assert payload["all_pass"] is False, f"mutation {name} survived"


def test_registry_records_refutation_and_refuses_data_adjudication() -> None:
    refuted = get_reference_entry("bianchi_VII_h_helical_roadmap_relation")
    assert refuted["status"] == "ROADMAP_REFERENCE_RELATION_REFUTED_BY_I2_I3"
    assert "parity-EVEN" in refuted["falsifier_semantics"]
    candidate = get_reference_entry(
        "bianchi_VII_h_helical_signed_component_candidate"
    )
    assert candidate["status"] == "FUTURE_NATIVE_ATLAS_TEST_VECTOR"
    assert candidate["adjudication"] == "FORBIDDEN_PRE_NATIVE"
    axisym = get_reference_entry("mirror_symmetric_axisymmetric_configurations")
    assert "VII_0" in axisym["falsifier_semantics"]
    assert "excluded" in axisym["falsifier_semantics"]
    with pytest.raises(DataAdjudicationAttempt):
        get_reference_entry(
            "bianchi_VII_h_helical_signed_component_candidate",
            observed=[0.1, -0.2],
        )
    with pytest.raises(DataAdjudicationAttempt):
        get_reference_entry(
            "bianchi_VII_h_helical_signed_component_candidate", observed=0.3
        )
    with pytest.raises(DataAdjudicationAttempt):
        get_reference_entry("pure_boost", eb_over_tb=[1.0])
    with pytest.raises(KeyError):
        get_reference_entry("not_a_registered_family")


def test_registry_has_no_data_api_and_no_production_consumer() -> None:
    payload = registry_payload()
    assert payload["data_ingestion_api"] == "none"
    assert len(REGISTRY_ENTRIES) == 4
    module_text = (REPO / "htt/src/common/pr182_parity_registry.py").read_text()
    for token in ("astropy", "healpy", "fits", "loadtxt", "read_csv", "np.load"):
        assert token not in module_text
    excluded_parts = {
        "venv", ".venv", ".git", "__pycache__", ".lake", "legacy",
        "tests", "workdir", "node_modules", "target",
    }
    allowed = {
        "htt/src/common/pr182_parity_registry.py",
        "scripts/codex_harness/run_pr182_parity_registry.py",
        "docs/research_program/long_horizon_rescue/pr182_spec.yaml",
        "docs/research_program/long_horizon_rescue/pr182_spec_erratum.yaml",
        "docs/generated/pr182_result_card.json",
        "docs/PR_DELTAS/pr-182.md",
        "CHANGELOG.md",
    }
    consumers = []
    for suffix in ("*.py", "*.tex", "*.rs"):
        for path in sorted(REPO.rglob(suffix)):
            rel = path.relative_to(REPO).as_posix()
            if set(Path(rel).parts) & excluded_parts:
                continue
            if rel in allowed or rel.startswith("docs/generated/pr182_"):
                continue
            if "pr182_parity_registry" in path.read_text(errors="replace"):
                consumers.append(rel)
    assert consumers == []


def test_status_not_pending_and_lane_is_hypothesis_only() -> None:
    status = (REPO / "docs/codex_handoff/pr_status.yaml").read_text()
    pending_block = status.split("pending:")[1].split("dormant_external:")[0]
    assert "PR-182" not in pending_block
    assert "PR-182: hypothesis_only" in status


def test_result_card_is_byte_current_under_read_only_check() -> None:
    proc = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/run_pr182_parity_registry.py"),
            "--check",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True and payload["read_only"] is True
