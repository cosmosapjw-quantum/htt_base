from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

import common.evidence_graph as evidence_graph_module
from common.evidence_graph import (
    ClaimClosure,
    EvidenceAxes,
    EvidenceEdge,
    EvidenceEdgeKind,
    EvidenceGraph,
    EvidenceGraphError,
    EvidenceNode,
    EvidenceNodeKind,
    EvidenceReceipt,
    EvidenceReceiptBody,
    EvidenceStatus,
    ProcessResult,
    ReceiptDependency,
    ReceiptDependencyKind,
    TestCaseResult as EvidenceTestCaseResult,
    TestExecution as EvidenceTestExecution,
    TestOutcome as EvidenceTestOutcome,
    authority_registry_content_ref,
    issue_evidence_receipt,
    load_exact_evidence_graph,
    load_exact_evidence_receipt,
    validate_receipt_lineage,
    verify_pytest_selector_inputs,
)
from common.remediation_state import (
    AuthorityError,
    AuthorityRegistry,
    PrincipalRecord,
    ScientificStatus,
)


ISSUED_AT = datetime(2026, 7, 16, 0, 0, tzinfo=timezone.utc)
EVALUATED_AT = datetime(2026, 7, 16, 1, 0, tzinfo=timezone.utc)
SCOPE = "PR-122:claim-evidence-graph"
_GLOBAL_VERIFIER_POLICY = {"allow": False}
_GLOBAL_VERIFIER_ALIAS_POLICY: list[object] = []


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _content_address(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _pytest_environment_contract_fixture(
    live_root: Path | None = None,
) -> dict[str, object]:
    def binding(relative: str, label: str) -> dict[str, str]:
        if live_root is None:
            digest = _digest(label)
        else:
            path = live_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{label}\n", encoding="utf-8")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {"scope": "repo", "path": relative, "sha256": digest}

    config_values: dict[str, object] = {}
    plugin_source = binding("environment/plugin.py", "evidence-plugin")
    pytest_source = binding("environment/pytest.py", "pytest-runner")
    contract: dict[str, object] = {
        "schema_version": "common.pytest_execution_environment.v1",
        "interpreter": {
            "implementation": "CPython",
            "version": "3.12.0",
            "cache_tag": "cpython-312",
            "executable": binding("environment/python", "python-executable"),
            "isolated": True,
            "safe_path": True,
            "user_site_enabled": False,
        },
        "sys_path": [{"scope": "repo", "path": "."}],
        "pytest": {
            "version": "9.0.2",
            "rootdir": ".",
            "import_mode": "importlib",
            "config_file": binding("pytest.ini", "pytest-config"),
            "config_values": config_values,
            "config_values_sha256": _content_address(config_values),
            "plugins": [
                {
                    "module": "common.pytest_execution_evidence",
                    "qualname": "<module>",
                    "source": plugin_source,
                }
            ],
            "conftests": [],
        },
        "import_origins": [
            {"module": "pytest", "source": pytest_source},
            {
                "module": "common.pytest_execution_evidence",
                "source": plugin_source,
            },
        ],
        "excluded_import_origins": [],
        "bytecode_policy": {
            "dont_write_bytecode": True,
            "pycache_prefix_status": "isolated_empty_external",
            "loaded_cache_files": [],
        },
        "startup_policy": {
            "no_site": True,
            "automatic_pth_processing": "disabled_by_no_site",
            "pyvenv_cfg_activation": "disabled_by_no_site",
        },
        "hidden_controls": {
            "pytest_addopts": None,
            "pytest_plugins": None,
            "pytest_disable_plugin_autoload": "1",
            "pythonpath_status": "unset",
        },
    }
    contract["environment_ref"] = _content_address(contract)
    return contract


def _axes(
    *,
    process: ProcessResult = ProcessResult.PASS,
    evidence: EvidenceStatus = EvidenceStatus.PRESENT,
    science: ScientificStatus = ScientificStatus.OPEN,
) -> EvidenceAxes:
    return EvidenceAxes(process, evidence, science)


def _test_execution(
    outcomes: tuple[EvidenceTestOutcome, ...] = (
        EvidenceTestOutcome.PASSED,
        EvidenceTestOutcome.PASSED,
    ),
) -> EvidenceTestExecution:
    ids = tuple(
        f"tests/test_contract.py::test_{index}" for index in range(len(outcomes))
    )
    results = tuple(
        EvidenceTestCaseResult(test_id, outcome)
        for test_id, outcome in zip(ids, outcomes, strict=True)
    )
    return EvidenceTestExecution(
        framework="pytest",
        selector="tests/test_contract.py",
        command=("python", "-m", "pytest", "-q", "tests/test_contract.py"),
        collected_test_ids=ids,
        executed_test_ids=ids,
        results=results,
        reported_collected_count=len(ids),
        reported_executed_count=len(ids),
    )


def _node(
    kind: EvidenceNodeKind,
    label: str,
    *,
    axes: EvidenceAxes | None = None,
    execution: EvidenceTestExecution | None = None,
    metadata: dict[str, object] | None = None,
) -> EvidenceNode:
    if axes is None:
        axes = _axes()
    digest = execution.execution_ref if execution is not None else _digest(label)
    return EvidenceNode(
        kind=kind,
        label=label,
        content_sha256=digest,
        axes=axes,
        metadata={"owner": "COMMON", **(metadata or {})},
        test_execution=execution,
    )


def _clean_graph(
    *,
    claim_science: ScientificStatus = ScientificStatus.EVIDENCE_READY,
    test_execution: EvidenceTestExecution | None = None,
) -> tuple[EvidenceGraph, EvidenceNode]:
    execution = test_execution or _test_execution()
    test_process, test_evidence = execution.axes
    claim = _node(
        EvidenceNodeKind.CLAIM,
        "claim:pr122-mechanics",
        axes=_axes(science=claim_science),
        metadata={"claim_level": "roadmap_rescue_v1:C1"},
    )
    producer = _node(EvidenceNodeKind.PRODUCER, "producer:fixture")
    input_node = _node(EvidenceNodeKind.INPUT, "input:fixture")
    config = _node(EvidenceNodeKind.CONFIG, "config:fixture")
    environment = _node(EvidenceNodeKind.ENVIRONMENT, "environment:fixture")
    test = _node(
        EvidenceNodeKind.TEST,
        "test:fixture",
        execution=execution,
        axes=_axes(process=test_process, evidence=test_evidence),
    )
    artifact = _node(EvidenceNodeKind.ARTIFACT, "artifact:fixture")
    consumer = _node(EvidenceNodeKind.CONSUMER, "consumer:fixture")
    nodes = (claim, producer, input_node, config, environment, test, artifact, consumer)
    edges = (
        EvidenceEdge(
            EvidenceEdgeKind.PRODUCED_BY, claim.node_ref, producer.node_ref, {}
        ),
        EvidenceEdge(
            EvidenceEdgeKind.USES_INPUT, producer.node_ref, input_node.node_ref, {}
        ),
        EvidenceEdge(
            EvidenceEdgeKind.USES_CONFIG, producer.node_ref, config.node_ref, {}
        ),
        EvidenceEdge(
            EvidenceEdgeKind.USES_ENVIRONMENT,
            producer.node_ref,
            environment.node_ref,
            {},
        ),
        EvidenceEdge(EvidenceEdgeKind.CHECKED_BY, producer.node_ref, test.node_ref, {}),
        EvidenceEdge(EvidenceEdgeKind.GENERATES, test.node_ref, artifact.node_ref, {}),
        EvidenceEdge(
            EvidenceEdgeKind.CONSUMED_BY, artifact.node_ref, consumer.node_ref, {}
        ),
    )
    return EvidenceGraph(nodes=nodes, edges=edges), claim


def _replace_node(
    graph: EvidenceGraph, old: EvidenceNode, new: EvidenceNode
) -> EvidenceGraph:
    return EvidenceGraph(
        nodes=tuple(
            new if node.node_ref == old.node_ref else node for node in graph.nodes
        ),
        edges=tuple(
            EvidenceEdge(
                edge.kind,
                new.node_ref if edge.source_ref == old.node_ref else edge.source_ref,
                new.node_ref if edge.target_ref == old.node_ref else edge.target_ref,
                edge.metadata,
            )
            for edge in graph.edges
        ),
    )


def _principal(
    principal_id: str,
    *,
    roles: tuple[str, ...],
    verifier: str,
    aliases: tuple[str, ...] = (),
    independence_class: str = "internal_non_author",
) -> PrincipalRecord:
    return PrincipalRecord(
        principal_id=principal_id,
        identity_fingerprint=_digest(f"principal:{principal_id}"),
        aliases=aliases,
        allowed_roles=roles,
        allowed_scopes=(SCOPE,),
        independence_class=independence_class,
        valid_from="2026-01-01T00:00:00+00:00",
        valid_until="2027-01-01T00:00:00+00:00",
        revoked=False,
        verifier=verifier,
    )


def _registry(
    *,
    author_id: str = "author-A",
    adjudicator_id: str = "adjudicator-B",
    adjudicator_roles: tuple[str, ...] = ("adjudicator",),
    adjudicator_independence_class: str = "internal_non_author",
) -> tuple[AuthorityRegistry, PrincipalRecord, PrincipalRecord]:
    verifier_name = "sha256_test_attestation_v1"
    author = _principal(author_id, roles=("author",), verifier=verifier_name)
    adjudicator = _principal(
        adjudicator_id,
        roles=adjudicator_roles,
        verifier=verifier_name,
        independence_class=adjudicator_independence_class,
    )

    def verify(principal: PrincipalRecord, payload: bytes, attestation: str) -> bool:
        expected = hashlib.sha256(
            principal.identity_fingerprint.encode("ascii") + payload
        ).hexdigest()
        return attestation == expected

    registry = AuthorityRegistry(
        (author, adjudicator), verifiers={verifier_name: verify}
    )
    return registry, author, adjudicator


def _receipt(
    graph: EvidenceGraph,
    claim: EvidenceNode,
    *,
    registry_rows: (
        tuple[AuthorityRegistry, PrincipalRecord, PrincipalRecord] | None
    ) = None,
    dependencies: tuple[ReceiptDependency, ...] = (),
) -> tuple[EvidenceReceipt, AuthorityRegistry]:
    registry, author, adjudicator = registry_rows or _registry()
    body = EvidenceReceiptBody.from_graph(
        graph,
        claim_ref=claim.node_ref,
        author=author.principal_id,
        author_identity_fingerprint=author.identity_fingerprint,
        adjudicator=adjudicator.principal_id,
        adjudicator_identity_fingerprint=adjudicator.identity_fingerprint,
        authority_registry_ref=authority_registry_content_ref(registry),
        scope=SCOPE,
        issued_at=ISSUED_AT,
        dependencies=dependencies,
    )
    receipt = issue_evidence_receipt(
        body,
        attestation_factory=lambda payload: hashlib.sha256(
            adjudicator.identity_fingerprint.encode("ascii") + payload
        ).hexdigest(),
    )
    return receipt, registry


def test_clean_graph_is_deterministic_closed_and_round_trips() -> None:
    graph, claim = _clean_graph()
    closure = graph.closure(claim.node_ref)

    assert isinstance(closure, ClaimClosure)
    assert closure.process_result is ProcessResult.PASS
    assert closure.evidence_statuses == (EvidenceStatus.PRESENT,)
    assert closure.scientific_status is ScientificStatus.EVIDENCE_READY
    assert closure.mechanics_closed is True
    assert closure.package_eligible is True
    assert (
        graph.graph_ref
        == EvidenceGraph(
            nodes=tuple(reversed(graph.nodes)), edges=tuple(reversed(graph.edges))
        ).graph_ref
    )
    assert EvidenceGraph.from_record(graph.to_record()).graph_ref == graph.graph_ref


def test_graph_record_hash_mismatch_is_rejected() -> None:
    graph, _claim = _clean_graph()
    record = graph.to_record()
    claim_record = next(
        row for row in record["nodes"] if row["kind"] == "claim"  # type: ignore[union-attr]
    )
    claim_record["content_sha256"] = _digest("tampered")

    with pytest.raises(EvidenceGraphError, match="node_ref does not match"):
        EvidenceGraph.from_record(record)


def test_graph_dependency_cycle_is_rejected() -> None:
    graph, _claim = _clean_graph()
    first = _node(EvidenceNodeKind.PRODUCER, "producer:cycle-a")
    second = _node(EvidenceNodeKind.PRODUCER, "producer:cycle-b")
    edges = (
        *graph.edges,
        EvidenceEdge(EvidenceEdgeKind.DEPENDS_ON, first.node_ref, second.node_ref, {}),
        EvidenceEdge(EvidenceEdgeKind.DEPENDS_ON, second.node_ref, first.node_ref, {}),
    )

    with pytest.raises(EvidenceGraphError, match="dependency cycle"):
        EvidenceGraph(nodes=(*graph.nodes, first, second), edges=edges)


def test_decoy_edge_kinds_cannot_replace_the_checked_evidence_chain() -> None:
    graph, claim = _clean_graph()
    producer = next(
        node for node in graph.nodes if node.kind is EvidenceNodeKind.PRODUCER
    )
    test = next(node for node in graph.nodes if node.kind is EvidenceNodeKind.TEST)
    artifact = next(
        node for node in graph.nodes if node.kind is EvidenceNodeKind.ARTIFACT
    )
    edges = tuple(
        edge
        for edge in graph.edges
        if not (
            edge.kind is EvidenceEdgeKind.GENERATES
            and edge.source_ref == test.node_ref
            and edge.target_ref == artifact.node_ref
        )
    ) + (
        EvidenceEdge(
            EvidenceEdgeKind.GENERATES,
            producer.node_ref,
            artifact.node_ref,
            {"role": "decoy producer artifact"},
        ),
    )
    decoy = EvidenceGraph(nodes=graph.nodes, edges=edges)

    closure = decoy.closure(claim.node_ref)

    assert closure.process_result is ProcessResult.NOT_RUN
    assert closure.evidence_status is EvidenceStatus.MISSING
    assert closure.mechanics_closed is False
    assert any(
        item.endswith("checked_by->generates->consumed_by")
        for item in closure.missing_edge_kinds
    )


def test_test_execution_reconciles_identities_and_counts() -> None:
    with pytest.raises(EvidenceGraphError, match="identity-derived count"):
        EvidenceTestExecution(
            framework="pytest",
            selector="tests/test_one.py",
            command=("pytest", "tests/test_one.py"),
            collected_test_ids=("tests/test_one.py::test_one",),
            executed_test_ids=("tests/test_one.py::test_one",),
            results=(
                EvidenceTestCaseResult(
                    "tests/test_one.py::test_one", EvidenceTestOutcome.PASSED
                ),
            ),
            reported_collected_count=1,
            reported_executed_count=0,
        )

    with pytest.raises(EvidenceGraphError, match="reconcile exactly"):
        EvidenceTestExecution(
            framework="cargo-test",
            selector="solver_anchor",
            command=("cargo", "test", "solver_anchor"),
            collected_test_ids=("solver_anchor",),
            executed_test_ids=("solver_anchor",),
            results=(
                EvidenceTestCaseResult("different_test", EvidenceTestOutcome.PASSED),
            ),
            reported_collected_count=1,
            reported_executed_count=1,
        )


def test_pytest_plugin_evidence_adapter_recomputes_all_identity_buckets() -> None:
    passed = "tests/test_one.py::test_pass"
    skipped = "tests/test_one.py::test_skip"
    selectors = ["tests/test_one.py"]
    collected = [passed, skipped]
    executed = [passed, skipped]
    payload: dict[str, object] = {
        "schema_version": "common.pytest_execution_evidence.v2",
        "runner": "pytest",
        "runner_version": "9.0.2",
        "python_version": "3.12.0",
        "python_implementation": "CPython",
        "platform": "linux",
        "rootdir": ".",
        "selector_argv": selectors,
        "normalized_invocation_argv": ["-q", "tests/test_one.py"],
        "selector_hash": _content_address(selectors),
        "selector_inputs": [
            {
                "scope": "repo",
                "path": "tests/test_one.py",
                "sha256": _digest("source"),
            }
        ],
        "environment_contract": _pytest_environment_contract_fixture(),
        "collected_node_ids": collected,
        "collected_node_ids_hash": _content_address(collected),
        "executed_node_ids": executed,
        "executed_node_ids_hash": _content_address(executed),
        "passed_node_ids": [passed],
        "failed_node_ids": [],
        "skipped_node_ids": [skipped],
        "xfailed_node_ids": [],
        "xpassed_node_ids": [],
        "counts": {
            "collected": 2,
            "executed": 2,
            "passed": 1,
            "failed": 0,
            "skipped": 1,
            "xfailed": 0,
            "xpassed": 0,
        },
        "exit_status": 0,
        "process_result": "passed",
        "caveats": ["process evidence only"],
    }
    payload["content_sha256"] = _content_address(payload)

    execution = EvidenceTestExecution.from_pytest_evidence(payload)

    assert execution.collected_count == 2
    assert execution.executed_count == 2
    assert execution.source_receipt_sha256 == payload["content_sha256"]
    assert execution.axes == (ProcessResult.NOT_RUN, EvidenceStatus.SKIPPED)
    assert execution.is_authoritative is False

    bad_counts = json.loads(json.dumps(payload))
    bad_counts["counts"]["executed"] = 1
    bad_counts.pop("content_sha256")
    bad_counts["content_sha256"] = _content_address(bad_counts)
    with pytest.raises(EvidenceGraphError, match="count executed"):
        EvidenceTestExecution.from_pytest_evidence(bad_counts)


def test_zero_collection_skip_and_xfail_are_distinct_non_authority() -> None:
    zero = _test_execution(())
    skipped = _test_execution((EvidenceTestOutcome.SKIPPED,))
    xfailed = _test_execution((EvidenceTestOutcome.XFAIL,))

    assert zero.axes == (ProcessResult.NOT_RUN, EvidenceStatus.MISSING)
    assert skipped.axes == (ProcessResult.NOT_RUN, EvidenceStatus.SKIPPED)
    assert xfailed.axes == (ProcessResult.FAIL, EvidenceStatus.XFAIL)
    assert not zero.is_authoritative
    assert not skipped.is_authoritative
    assert not xfailed.is_authoritative

    graph, claim = _clean_graph(test_execution=zero)
    closure = graph.closure(claim.node_ref)
    assert closure.mechanics_closed is False
    assert EvidenceStatus.MISSING in closure.evidence_statuses


def test_xpass_is_explicit_invalid_non_authority() -> None:
    xpassed = _test_execution((EvidenceTestOutcome.XPASS,))

    assert xpassed.axes == (ProcessResult.FAIL, EvidenceStatus.INVALID)
    assert xpassed.is_authoritative is False


def test_process_pass_and_blocked_evidence_remain_orthogonal() -> None:
    axes = EvidenceAxes(
        ProcessResult.PASS,
        EvidenceStatus.BLOCKED,
        ScientificStatus.BLOCKED,
    )
    graph, claim = _clean_graph()
    blocked_artifact = _node(
        EvidenceNodeKind.ARTIFACT,
        "artifact:blocked-but-process-passed",
        axes=axes,
    )
    old_artifact = next(
        node for node in graph.nodes if node.kind is EvidenceNodeKind.ARTIFACT
    )
    mutated = _replace_node(graph, old_artifact, blocked_artifact)
    closure = mutated.closure(claim.node_ref)

    assert closure.process_result is ProcessResult.PASS
    assert closure.evidence_status is EvidenceStatus.BLOCKED
    assert closure.mechanics_closed is False
    assert closure.package_eligible is False


def test_blocked_supporting_science_cannot_hide_behind_green_process_evidence() -> None:
    graph, claim = _clean_graph()
    old_artifact = next(
        node for node in graph.nodes if node.kind is EvidenceNodeKind.ARTIFACT
    )
    blocked_artifact = _node(
        EvidenceNodeKind.ARTIFACT,
        "artifact:science-blocked-only",
        axes=_axes(science=ScientificStatus.BLOCKED),
    )
    mutated = _replace_node(graph, old_artifact, blocked_artifact)
    closure = mutated.closure(claim.node_ref)

    assert closure.process_result is ProcessResult.PASS
    assert closure.evidence_status is EvidenceStatus.PRESENT
    assert closure.mechanics_closed is True
    assert ScientificStatus.BLOCKED in closure.scientific_statuses
    assert closure.package_eligible is False
    with pytest.raises(EvidenceGraphError, match="blocked/falsified/abandoned"):
        closure.require_package_eligible()


def test_test_node_cannot_spoof_execution_axes_or_hash() -> None:
    execution = _test_execution((EvidenceTestOutcome.XFAIL,))
    with pytest.raises(EvidenceGraphError, match="axes do not match"):
        _node(
            EvidenceNodeKind.TEST,
            "test:spoof",
            execution=execution,
            axes=_axes(),
        )
    with pytest.raises(EvidenceGraphError, match="must equal"):
        EvidenceNode(
            kind=EvidenceNodeKind.TEST,
            label="test:bad-hash",
            content_sha256=_digest("not-the-execution"),
            axes=_axes(process=ProcessResult.FAIL, evidence=EvidenceStatus.XFAIL),
            metadata={},
            test_execution=execution,
        )


@pytest.mark.parametrize(
    "metadata",
    [
        {"ready_for_claims": True},
        {"nested": {"releaseEligible": True}},
        {"claim-ready": False},
    ],
)
def test_caller_supplied_readiness_fields_are_forbidden(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(EvidenceGraphError, match="readiness field is forbidden"):
        _node(EvidenceNodeKind.ARTIFACT, "artifact:spoof", metadata=metadata)


@pytest.mark.parametrize(
    "metadata",
    [
        {"ppc_passed": True},
        {"bayes_factor": 100.0},
        {"nested": {"pseudo_ppc": 0.01}},
    ],
)
def test_caller_supplied_statistical_gate_scalars_are_forbidden(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(EvidenceGraphError, match="statistical gate field"):
        _node(EvidenceNodeKind.ARTIFACT, "artifact:pseudo-stat", metadata=metadata)


def test_receipt_exact_binding_authority_and_round_trip() -> None:
    graph, claim = _clean_graph()
    receipt, registry = _receipt(graph, claim)

    closure = receipt.validate_for_package(graph, registry, evaluated_at=EVALUATED_AT)
    assert closure.package_eligible is True
    assert (
        EvidenceReceipt.from_record(receipt.to_record()).receipt_id
        == receipt.receipt_id
    )
    disclosure = receipt.audit_disclosure()
    assert disclosure["authority_status"] == "REQUIRES_TRUSTED_REGISTRY_VALIDATION"
    assert "scientific validation" in disclosure["caveat"]


def test_claim_release_requires_positive_terminal_external_adjudication() -> None:
    graph, claim = _clean_graph(claim_science=ScientificStatus.RESCUED)
    rows = _registry(
        adjudicator_roles=("adjudicator", "scientific_status_promoter"),
        adjudicator_independence_class="independent_external",
    )
    receipt, registry = _receipt(graph, claim, registry_rows=rows)

    closure = receipt.validate_for_release(graph, registry, evaluated_at=EVALUATED_AT)
    assert closure.claim_release_eligible is True


def test_authority_registry_ref_binds_same_name_verifier_implementation() -> None:
    verifier_name = "same-name-verifier"
    principal = _principal(
        "author-only",
        roles=("author",),
        verifier=verifier_name,
    )

    def strict_verifier(
        _principal: PrincipalRecord, _payload: bytes, attestation: str
    ) -> bool:
        return attestation == "strict"

    def permissive_verifier(
        _principal: PrincipalRecord, _payload: bytes, _attestation: str
    ) -> bool:
        return True

    strict = AuthorityRegistry((principal,), verifiers={verifier_name: strict_verifier})
    permissive = AuthorityRegistry(
        (principal,), verifiers={verifier_name: permissive_verifier}
    )
    assert authority_registry_content_ref(strict) != authority_registry_content_ref(
        permissive
    )


def test_authority_registry_ref_binds_verifier_callable_state() -> None:
    verifier_name = "stateful-verifier"
    principal = _principal("author-only", roles=("author",), verifier=verifier_name)

    def closure_factory(allow: bool):
        def verify(
            _principal: PrincipalRecord, _payload: bytes, _attestation: str
        ) -> bool:
            return allow

        return verify

    def default_factory(allow: bool):
        def verify(
            _principal: PrincipalRecord,
            _payload: bytes,
            _attestation: str,
            decision: bool = allow,
        ) -> bool:
            return decision

        return verify

    def kwdefault_factory(allow: bool):
        def verify(
            _principal: PrincipalRecord,
            _payload: bytes,
            _attestation: str,
            *,
            decision: bool = allow,
        ) -> bool:
            return decision

        return verify

    def registry_ref(verifier: object) -> str:
        return authority_registry_content_ref(
            AuthorityRegistry((principal,), verifiers={verifier_name: verifier})
        )

    closure_denied = closure_factory(False)
    closure_allowed = closure_factory(True)
    default_denied = default_factory(False)
    default_allowed = default_factory(True)
    kwdefault_denied = kwdefault_factory(False)
    kwdefault_allowed = kwdefault_factory(True)
    assert closure_denied.__code__ is closure_allowed.__code__
    assert default_denied.__code__ is default_allowed.__code__
    assert kwdefault_denied.__code__ is kwdefault_allowed.__code__
    assert registry_ref(closure_denied) != registry_ref(closure_allowed)
    assert registry_ref(default_denied) != registry_ref(default_allowed)
    assert registry_ref(kwdefault_denied) != registry_ref(kwdefault_allowed)

    def global_policy_verifier(
        _principal: PrincipalRecord, _payload: bytes, _attestation: str
    ) -> bool:
        return _GLOBAL_VERIFIER_POLICY["allow"]

    denied_ref = registry_ref(global_policy_verifier)
    _GLOBAL_VERIFIER_POLICY["allow"] = True
    try:
        allowed_ref = registry_ref(global_policy_verifier)
    finally:
        _GLOBAL_VERIFIER_POLICY["allow"] = False
    assert denied_ref != allowed_ref


def test_caller_declared_verifier_ref_cannot_replace_semantic_binding() -> None:
    verifier_name = "declared-ref-verifier"
    principal = _principal("author-only", roles=("author",), verifier=verifier_name)

    def factory(allow: bool):
        def verify(
            _principal: PrincipalRecord, _payload: bytes, _attestation: str
        ) -> bool:
            return allow

        verify.__htt_verifier_ref__ = _digest("same caller declaration")
        return verify

    denied = AuthorityRegistry((principal,), verifiers={verifier_name: factory(False)})
    allowed = AuthorityRegistry((principal,), verifiers={verifier_name: factory(True)})
    assert authority_registry_content_ref(denied) != authority_registry_content_ref(
        allowed
    )


def test_authority_registry_ref_binds_graph_wide_alias_topology() -> None:
    verifier_name = "alias-topology-verifier"
    principal = _principal("author-only", roles=("author",), verifier=verifier_name)

    def factory(shared: bool):
        closure_value = _GLOBAL_VERIFIER_ALIAS_POLICY if shared else []
        default_value = closure_value if shared else []
        kwdefault_value = closure_value if shared else []

        def verify(
            _principal: PrincipalRecord,
            _payload: bytes,
            _attestation: str,
            marker: object = default_value,
            *,
            kwmarker: object = kwdefault_value,
        ) -> bool:
            return (
                closure_value is marker
                and marker is kwmarker
                and kwmarker is _GLOBAL_VERIFIER_ALIAS_POLICY
                and verify.policy is _GLOBAL_VERIFIER_ALIAS_POLICY
            )

        verify.policy = closure_value if shared else []
        return verify

    shared = factory(True)
    distinct = factory(False)
    assert shared.__code__ is distinct.__code__
    assert shared(principal, b"payload", "attestation") is True
    assert distinct(principal, b"payload", "attestation") is False
    shared_registry = AuthorityRegistry((principal,), verifiers={verifier_name: shared})
    distinct_registry = AuthorityRegistry(
        (principal,), verifiers={verifier_name: distinct}
    )
    shared_ref = authority_registry_content_ref(shared_registry)
    distinct_ref = authority_registry_content_ref(distinct_registry)
    assert shared_ref != distinct_ref
    assert shared_ref == authority_registry_content_ref(shared_registry)
    assert shared_ref == authority_registry_content_ref(
        AuthorityRegistry((principal,), verifiers={verifier_name: factory(True)})
    )
    assert distinct_ref == authority_registry_content_ref(
        AuthorityRegistry((principal,), verifiers={verifier_name: factory(False)})
    )


def test_unverifiable_verifier_state_is_rejected() -> None:
    verifier_name = "opaque-state-verifier"
    principal = _principal("author-only", roles=("author",), verifier=verifier_name)
    opaque_policy = object()

    def verify(_principal: PrincipalRecord, _payload: bytes, _attestation: str) -> bool:
        return opaque_policy is not None

    registry = AuthorityRegistry((principal,), verifiers={verifier_name: verify})
    with pytest.raises(EvidenceGraphError, match="unverifiable state"):
        authority_registry_content_ref(registry)

    class CallerDeclaredOpaqueVerifier:
        __htt_verifier_ref__ = _digest("opaque caller declaration")

        def __call__(
            self,
            _principal: PrincipalRecord,
            _payload: bytes,
            _attestation: str,
        ) -> bool:
            return True

    declared_only = AuthorityRegistry(
        (principal,), verifiers={verifier_name: CallerDeclaredOpaqueVerifier()}
    )
    with pytest.raises(EvidenceGraphError, match="must be a Python function"):
        authority_registry_content_ref(declared_only)


def test_fabricated_attestation_and_wrong_exact_graph_fail() -> None:
    graph, claim = _clean_graph()
    receipt, registry = _receipt(graph, claim)
    forged = EvidenceReceipt(receipt.body, _digest("fabricated-attestation"))

    with pytest.raises(AuthorityError, match="attestation verification failed"):
        forged.validate(graph, registry, evaluated_at=EVALUATED_AT)

    other_graph, _other_claim = _clean_graph(
        claim_science=ScientificStatus.ADJUDICATION_PENDING
    )
    with pytest.raises(EvidenceGraphError, match="exact graph"):
        receipt.validate(other_graph, registry, evaluated_at=EVALUATED_AT)


def test_author_and_adjudicator_must_be_distinct_before_signing() -> None:
    graph, claim = _clean_graph()
    _registry_value, author, _adjudicator = _registry()
    closure = graph.closure(claim.node_ref)

    with pytest.raises(EvidenceGraphError, match="distinct identities"):
        EvidenceReceiptBody(
            graph_ref=graph.graph_ref,
            claim_ref=claim.node_ref,
            closure_ref=closure.closure_ref,
            node_refs=closure.node_refs,
            edge_refs=closure.edge_refs,
            process_result=closure.process_result,
            evidence_status=closure.evidence_status,
            evidence_statuses=closure.evidence_statuses,
            scientific_status=closure.scientific_status,
            authority_registry_ref=authority_registry_content_ref(_registry_value),
            author=author.principal_id,
            author_identity_fingerprint=author.identity_fingerprint,
            adjudicator=author.principal_id,
            adjudicator_identity_fingerprint=author.identity_fingerprint,
            scope=SCOPE,
            issued_at=ISSUED_AT,
        )


def test_blocked_science_is_disclosable_but_never_release_green() -> None:
    graph, claim = _clean_graph(claim_science=ScientificStatus.BLOCKED)
    receipt, registry = _receipt(graph, claim)

    assert receipt.audit_disclosure()["scientific_status"] == "BLOCKED"
    with pytest.raises(AuthorityError, match="scientific_status_promoter"):
        receipt.validate(graph, registry, evaluated_at=EVALUATED_AT)

    promoter_rows = _registry(
        adjudicator_roles=("adjudicator", "scientific_status_promoter")
    )
    trusted_receipt, trusted_registry = _receipt(
        graph, claim, registry_rows=promoter_rows
    )
    with pytest.raises(AuthorityError, match="independently authenticated"):
        trusted_receipt.validate(graph, trusted_registry, evaluated_at=EVALUATED_AT)

    external_rows = _registry(
        adjudicator_roles=("adjudicator", "scientific_status_promoter"),
        adjudicator_independence_class="independent_external",
    )
    external_receipt, external_registry = _receipt(
        graph, claim, registry_rows=external_rows
    )
    closure = external_receipt.validate(
        graph, external_registry, evaluated_at=EVALUATED_AT
    )
    assert closure.mechanics_closed is True
    assert closure.package_eligible is False
    with pytest.raises(EvidenceGraphError, match="claim release requires"):
        external_receipt.validate_for_release(
            graph, external_registry, evaluated_at=EVALUATED_AT
        )


def test_invalid_integrity_dominates_an_expected_policy_block() -> None:
    graph, claim = _clean_graph(claim_science=ScientificStatus.BLOCKED)
    blocked_claim = _node(
        EvidenceNodeKind.CLAIM,
        "claim:blocked-policy",
        axes=_axes(
            evidence=EvidenceStatus.BLOCKED,
            science=ScientificStatus.BLOCKED,
        ),
        metadata={"claim_level": "roadmap_rescue_v1:C1"},
    )
    graph = _replace_node(graph, claim, blocked_claim)
    artifact = next(
        node for node in graph.nodes if node.kind is EvidenceNodeKind.ARTIFACT
    )
    invalid_artifact = _node(
        EvidenceNodeKind.ARTIFACT,
        "artifact:invalid",
        axes=_axes(evidence=EvidenceStatus.INVALID),
    )
    invalid_graph = _replace_node(graph, artifact, invalid_artifact)
    invalid_claim = next(
        node for node in invalid_graph.nodes if node.kind is EvidenceNodeKind.CLAIM
    )
    closure = invalid_graph.closure(invalid_claim.node_ref)

    assert closure.evidence_status is EvidenceStatus.INVALID
    assert EvidenceStatus.BLOCKED in closure.evidence_statuses
    assert closure.mechanics_closed is False
    assert closure.package_eligible is False


def test_parent_and_independence_refs_are_content_addressed_and_fail_closed() -> None:
    graph, claim = _clean_graph()
    parent, registry = _receipt(graph, claim)
    author = registry.resolve("author-A", role="author", scope=SCOPE, at=ISSUED_AT)
    adjudicator = registry.resolve(
        "adjudicator-B", role="adjudicator", scope=SCOPE, at=ISSUED_AT
    )
    dependency = ReceiptDependency(ReceiptDependencyKind.PARENT, parent.receipt_id)
    child, _ = _receipt(
        graph,
        claim,
        registry_rows=(registry, author, adjudicator),
        dependencies=(dependency,),
    )
    index = {parent.receipt_id: parent, child.receipt_id: child}

    assert validate_receipt_lineage(index) == tuple(sorted(index))
    child.validate(
        graph,
        registry,
        evaluated_at=EVALUATED_AT,
        receipt_index=index,
        graph_index={graph.graph_ref: graph},
    )
    assert (
        dependency.dependency_ref
        == ReceiptDependency.from_record(dependency.to_record()).dependency_ref
    )

    independent = ReceiptDependency(
        ReceiptDependencyKind.INDEPENDENT, parent.receipt_id
    )
    reused_identity_child, _ = _receipt(
        graph,
        claim,
        registry_rows=(registry, author, adjudicator),
        dependencies=(independent,),
    )
    with pytest.raises(EvidenceGraphError, match="reuses an author/adjudicator"):
        validate_receipt_lineage(
            {
                parent.receipt_id: parent,
                reused_identity_child.receipt_id: reused_identity_child,
            }
        )


def test_distinct_correlated_internal_receipts_are_not_independent() -> None:
    graph, claim = _clean_graph()
    verifier_name = "sha256_test_attestation_v1"
    principals = (
        _principal("author-A", roles=("author",), verifier=verifier_name),
        _principal("adjudicator-B", roles=("adjudicator",), verifier=verifier_name),
        _principal("author-C", roles=("author",), verifier=verifier_name),
        _principal("adjudicator-D", roles=("adjudicator",), verifier=verifier_name),
    )

    def verify(principal: PrincipalRecord, payload: bytes, attestation: str) -> bool:
        return (
            attestation
            == hashlib.sha256(
                principal.identity_fingerprint.encode("ascii") + payload
            ).hexdigest()
        )

    registry = AuthorityRegistry(principals, verifiers={verifier_name: verify})
    parent, _ = _receipt(
        graph,
        claim,
        registry_rows=(registry, principals[0], principals[1]),
    )
    child, _ = _receipt(
        graph,
        claim,
        registry_rows=(registry, principals[2], principals[3]),
        dependencies=(
            ReceiptDependency(ReceiptDependencyKind.INDEPENDENT, parent.receipt_id),
        ),
    )
    with pytest.raises(AuthorityError, match="independently authenticated"):
        validate_receipt_lineage(
            {parent.receipt_id: parent, child.receipt_id: child},
            registry=registry,
            evaluated_at=EVALUATED_AT,
        )


def test_zero_collected_rust_target_is_explicit_non_authority() -> None:
    execution = EvidenceTestExecution(
        framework="cargo-test",
        selector="--test nonexistent_pr124_d2",
        command=("cargo", "test", "--test", "nonexistent_pr124_d2"),
        collected_test_ids=(),
        executed_test_ids=(),
        results=(),
        reported_collected_count=0,
        reported_executed_count=0,
    )
    assert execution.axes == (ProcessResult.NOT_RUN, EvidenceStatus.MISSING)
    assert execution.is_authoritative is False


def test_selector_source_drift_is_rechecked_at_consumption(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        evidence_graph_module,
        "verify_pytest_environment_inputs",
        lambda *_args, **_kwargs: _digest("environment"),
    )
    source = tmp_path / "test_selected.py"
    source.write_text("def test_selected():\n    assert True\n", encoding="utf-8")
    payload = {
        "selector_argv": ["test_selected.py"],
        "normalized_invocation_argv": ["-q", "test_selected.py"],
        "selector_inputs": [
            {
                "scope": "repo",
                "path": "test_selected.py",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        ],
        "environment_contract": _pytest_environment_contract_fixture(tmp_path),
    }
    assert verify_pytest_selector_inputs(tmp_path, payload) == (
        ("test_selected.py", payload["selector_inputs"][0]["sha256"]),
    )

    source.write_text("def test_selected():\n    assert False\n", encoding="utf-8")
    with pytest.raises(EvidenceGraphError, match="selector input hash drift"):
        verify_pytest_selector_inputs(tmp_path, payload)


def test_missing_parent_and_tampered_receipt_id_fail_closed() -> None:
    graph, claim = _clean_graph()
    parent, registry = _receipt(graph, claim)
    author = registry.resolve("author-A", role="author", scope=SCOPE, at=ISSUED_AT)
    adjudicator = registry.resolve(
        "adjudicator-B", role="adjudicator", scope=SCOPE, at=ISSUED_AT
    )
    child, _ = _receipt(
        graph,
        claim,
        registry_rows=(registry, author, adjudicator),
        dependencies=(
            ReceiptDependency(ReceiptDependencyKind.PARENT, parent.receipt_id),
        ),
    )
    with pytest.raises(EvidenceGraphError, match="is missing"):
        validate_receipt_lineage({child.receipt_id: child})

    record = child.to_record()
    record["body"]["receipt_id"] = _digest("tampered")  # type: ignore[index]
    with pytest.raises(EvidenceGraphError, match="receipt_id does not match"):
        EvidenceReceipt.from_record(record)


def test_receipt_self_reference_and_two_node_cycles_fail_closed() -> None:
    graph, claim = _clean_graph()
    base, _registry_value = _receipt(graph, claim)

    class ForgedAddressReceipt(EvidenceReceipt):
        @property
        def receipt_id(self) -> str:
            return self._forced_receipt_id  # type: ignore[attr-defined]

    def forged(body: EvidenceReceiptBody, forced_id: str) -> EvidenceReceipt:
        receipt = ForgedAddressReceipt(body, base.attestation)
        object.__setattr__(receipt, "_forced_receipt_id", forced_id)
        return receipt

    ref_a = _digest("cycle-a")
    ref_b = _digest("cycle-b")
    self_body = replace(
        base.body,
        dependencies=(ReceiptDependency(ReceiptDependencyKind.PARENT, ref_a),),
    )
    with pytest.raises(EvidenceGraphError, match="cannot depend on itself"):
        validate_receipt_lineage({ref_a: forged(self_body, ref_a)})

    body_a = replace(
        base.body,
        dependencies=(ReceiptDependency(ReceiptDependencyKind.PARENT, ref_b),),
    )
    body_b = replace(
        base.body,
        dependencies=(ReceiptDependency(ReceiptDependencyKind.PARENT, ref_a),),
    )
    with pytest.raises(EvidenceGraphError, match="dependency cycle"):
        validate_receipt_lineage(
            {ref_a: forged(body_a, ref_a), ref_b: forged(body_b, ref_b)}
        )


def test_registry_swap_and_fabricated_parent_attestation_fail() -> None:
    graph, claim = _clean_graph()
    parent, registry = _receipt(graph, claim)
    author = registry.resolve("author-A", role="author", scope=SCOPE, at=ISSUED_AT)
    adjudicator = registry.resolve(
        "adjudicator-B", role="adjudicator", scope=SCOPE, at=ISSUED_AT
    )
    child, _ = _receipt(
        graph,
        claim,
        registry_rows=(registry, author, adjudicator),
        dependencies=(
            ReceiptDependency(ReceiptDependencyKind.PARENT, parent.receipt_id),
        ),
    )
    forged_parent = EvidenceReceipt(parent.body, _digest("forged-parent"))
    index = {forged_parent.receipt_id: forged_parent, child.receipt_id: child}
    with pytest.raises(AuthorityError, match="attestation verification failed"):
        child.validate(
            graph,
            registry,
            evaluated_at=EVALUATED_AT,
            receipt_index=index,
            graph_index={graph.graph_ref: graph},
        )

    swapped_registry, _swapped_author, _swapped_adjudicator = _registry(
        adjudicator_id="adjudicator-C"
    )
    with pytest.raises(AuthorityError, match="authority_registry_ref"):
        parent.validate(graph, swapped_registry, evaluated_at=EVALUATED_AT)


def test_exact_repo_loaders_require_expected_content_addresses(tmp_path) -> None:
    graph, claim = _clean_graph()
    receipt, _registry_value = _receipt(graph, claim)
    graph_path = tmp_path / "graph.json"
    receipt_path = tmp_path / "receipt.json"
    graph_path.write_text(
        json.dumps(graph.to_record(), sort_keys=True), encoding="utf-8"
    )
    receipt_path.write_text(
        json.dumps(receipt.to_record(), sort_keys=True), encoding="utf-8"
    )

    assert (
        load_exact_evidence_graph(
            graph_path, expected_graph_ref=graph.graph_ref
        ).graph_ref
        == graph.graph_ref
    )
    assert (
        load_exact_evidence_receipt(
            receipt_path, expected_receipt_id=receipt.receipt_id
        ).receipt_id
        == receipt.receipt_id
    )
    with pytest.raises(EvidenceGraphError, match="expected_receipt_id"):
        load_exact_evidence_receipt(
            receipt_path, expected_receipt_id=_digest("wrong-receipt")
        )

    duplicate_key_path = tmp_path / "duplicate.json"
    duplicate_key_path.write_text(
        '{"body": {}, "body": {}, "attestation": "x"}', encoding="utf-8"
    )
    with pytest.raises(EvidenceGraphError, match="duplicate key"):
        load_exact_evidence_receipt(
            duplicate_key_path, expected_receipt_id=receipt.receipt_id
        )
