#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

HARNESS_SCRIPTS = Path(__file__).resolve().parents[2] / ".agent-harness" / "scripts"
if str(HARNESS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(HARNESS_SCRIPTS))

from _harness import (  # noqa: E402
    evaluate_stack_eligibility,
    load_stacked_execution_status,
    resolve_candidate_activation_base,
)

if __package__:  # Package import used by pytest and library callers.
    from .premise_anchor_gates import (
        claim_contracts_for_backlog,
        validate_premise_anchor_intake,
    )
    from .pr167_intake_contract import validate_pre_intake_receipt
    from .sync_pr_dag_mirrors import check_mirrors
else:  # Direct script execution places this directory on sys.path.
    from premise_anchor_gates import (
        claim_contracts_for_backlog,
        validate_premise_anchor_intake,
    )
    from pr167_intake_contract import validate_pre_intake_receipt
    from sync_pr_dag_mirrors import check_mirrors


RESCUE_FIRST_PR = 119
RESCUE_LAST_PR = 166
ADVOCATE_FIRST_PR = 167
ADVOCATE_LAST_PR = 184
RESCUE_CARD_COUNT = RESCUE_LAST_PR - RESCUE_FIRST_PR + 1
RESCUE_PRE_ADVOCATE_CARD_COUNT = 113
RESCUE_WITH_ADVOCATE_CARD_COUNT = 131
RESCUE_REQUIRED_FIELDS = {
    "id",
    "wave",
    "title",
    "owner",
    "contributors",
    "adjudicator_role",
    "implementation_scopes",
    "depends",
    "dependency_contracts",
    "targets",
    "files",
    "tests",
    "dod",
    "kill",
    "cost",
    "claim_tier_ceiling",
    "claim_level",
    "forbidden",
    "anti_drift",
    "roadmap_anchor",
    "activation_state",
    "scientific_status_on_intake",
}
RESCUE_ACTIVE_OWNERS = {"COMMON", "HTT", "MIO", "BASS", "OBSSTAT"}
RESCUE_FORBIDDEN_OWNERS = {"TSC", "TSC_LEGACY", "TEFF", "MANUSCRIPT", "BASS_PY"}
RESCUE_IMPLEMENTATION_SCOPES = {
    "common",
    "htt",
    "mio",
    "bass_py",
    "canonical_BASS",
    "obsstat",
}
RESCUE_EDGE_MODES = {
    "requires_success",
    "requires_terminal_receipt",
    "requires_adjudicated_claim_set",
}
RESCUE_CLAIM_LEVELS = {
    "roadmap_rescue_v1": {f"C{index}" for index in range(7)},
    "not_applicable_governance_v1": {"NOT_APPLICABLE"},
}
RESCUE_EXECUTION_RESOLUTIONS = {
    "COMPLETED_SUCCESS",
    "COMPLETED_FAILED_WITH_RECEIPT",
    "BLOCKED_WITH_RECEIPT",
    "ABANDONED_WITH_RECEIPT",
}
ADVOCATE_EXECUTION_LANES = {"defensible", "hypothesis_only", "needs_native"}
ADVOCATE_ACTIVATION_STATES = {"PENDING", "NEEDS_NATIVE"}
TYPED_DORMANT_ACTIVATION_STATES = {"DORMANT_EXTERNAL", "NEEDS_NATIVE"}
BACKGROUND_EXECUTION_CONTRACTS = {
    "PR-151": {
        "kind": "acquisition",
        "allowed_phase": "acquire",
        "partial_scientific_use": "forbidden",
    }
}
ADVOCATE_REQUIRED_FIELDS = RESCUE_REQUIRED_FIELDS | {
    "execution_lane",
    "scientific_artifact_mode",
    "execution_authorization",
    "public_use",
    "spec_first_required",
}
ADVOCATE_CARD_CONTRACTS = {
    "PR-167": (["PR-119", "PR-154"], "defensible", "PENDING"),
    "PR-168": (["PR-124", "PR-167"], "defensible", "PENDING"),
    "PR-169": (["PR-126", "PR-127", "PR-167"], "defensible", "PENDING"),
    "PR-170": (["PR-124", "PR-126", "PR-167"], "defensible", "PENDING"),
    "PR-171": (["PR-125", "PR-167"], "defensible", "PENDING"),
    "PR-172": (["PR-123", "PR-167"], "defensible", "PENDING"),
    "PR-173": (["PR-135", "PR-167"], "defensible", "PENDING"),
    "PR-174": (["PR-167"], "hypothesis_only", "PENDING"),
    "PR-175": (["PR-124", "PR-167", "PR-174"], "hypothesis_only", "PENDING"),
    "PR-176": (["PR-133", "PR-144", "PR-146", "PR-148", "PR-167", "PR-173"], "defensible", "PENDING"),
    "PR-177": (["PR-152", "PR-167", "PR-173"], "defensible", "PENDING"),
    "PR-178": (["PR-151", "PR-155", "PR-156", "PR-157", "PR-158", "PR-167"], "defensible", "PENDING"),
    "PR-179": (["PR-134", "PR-135", "PR-139", "PR-144", "PR-167", "PR-173"], "defensible", "PENDING"),
    "PR-180": (["PR-134", "PR-149", "PR-150", "PR-167", "PR-172", "PR-173", "PR-184"], "defensible", "PENDING"),
    "PR-181": (["PR-140", "PR-141", "PR-143", "PR-155", "PR-167", "PR-173", "PR-251"], "defensible", "PENDING"),
    "PR-182": (["PR-167"], "hypothesis_only", "PENDING"),
    "PR-183": (["PR-159", "PR-160", "PR-161", "PR-167"], "needs_native", "NEEDS_NATIVE"),
    "PR-184": (["PR-172"], "defensible", "PENDING"),
}
ADVOCATE_HYPOTHESIS_ONLY_ARTIFACTS = {
    "PR-171",
    "PR-174",
    "PR-175",
    "PR-182",
    "PR-183",
}
ADVOCATE_REGISTERED_NOT_SCHEDULED = {"PR-174", "PR-175", "PR-182"}
ADVOCATE_EXPLICIT_APPROVED_SEQUENCE = {"PR-168", "PR-169", "PR-170", "PR-171"}

# --- Post-v10 strengthening wave (PR-185..208, Waves 28..34) ---------------
# Formal intake of the external-audit strengthening roadmap
# (htt_post_v10_strengthening_plan_20260721). Registered atomically; the
# scheduled subset (DAG_SCHEDULABLE or later explicit user authorization) is this
# session's owner-approved parallel-to-PR-151 scope, the rest are
# REGISTERED_NOT_SCHEDULED / NATIVE_BLOCKED with typed dependency edges.
STRENGTHEN_FIRST_PR = 185
STRENGTHEN_LAST_PR = 208
STRENGTHEN_CARD_COUNT = STRENGTHEN_LAST_PR - STRENGTHEN_FIRST_PR + 1
# (depends, execution_lane, activation_state, execution_authorization)
STRENGTHEN_CARD_CONTRACTS = {
    "PR-185": (["PR-184"], "defensible", "PENDING", "DAG_SCHEDULABLE"),
    "PR-186": (["PR-185"], "defensible", "PENDING", "DAG_SCHEDULABLE"),
    "PR-187": (["PR-186"], "defensible", "PENDING", "DAG_SCHEDULABLE"),
    "PR-188": (["PR-185", "PR-186", "PR-187"], "defensible", "PENDING", "DAG_SCHEDULABLE"),
    "PR-189": (["PR-187", "PR-188"], "defensible", "PENDING", "DAG_SCHEDULABLE"),
    "PR-190": (["PR-187", "PR-189", "PR-249"], "defensible", "PENDING", "EXPLICIT_USER_AUTHORIZED"),
    "PR-191": (["PR-187", "PR-190"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-192": (["PR-187", "PR-191"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-193": (["PR-186", "PR-187", "PR-191", "PR-248"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-194": (["PR-187", "PR-193"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-195": (["PR-187", "PR-194"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-196": (["PR-159", "PR-160", "PR-161", "PR-187", "PR-194", "PR-195"], "needs_native", "NEEDS_NATIVE", "NATIVE_BLOCKED"),
    "PR-197": (["PR-188"], "defensible", "PENDING", "DAG_SCHEDULABLE"),
    "PR-198": (["PR-197", "PR-194"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-199": (["PR-194", "PR-197", "PR-198"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-200": (["PR-189", "PR-197"], "defensible", "PENDING", "DAG_SCHEDULABLE"),
    "PR-201": (["PR-144", "PR-145", "PR-146", "PR-147", "PR-195", "PR-200"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-202": (["PR-149", "PR-150", "PR-197", "PR-198", "PR-199"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-203": (["PR-151", "PR-197", "PR-200"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-204": (["PR-152", "PR-177", "PR-197", "PR-200"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-205": (["PR-189", "PR-190", "PR-193", "PR-195", "PR-196", "PR-200", "PR-201", "PR-202", "PR-203", "PR-204", "PR-252"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-206": (["PR-196", "PR-201", "PR-202", "PR-203", "PR-204", "PR-205", "PR-181"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-207": (["PR-186", "PR-189", "PR-191", "PR-192", "PR-193", "PR-199", "PR-200", "PR-205", "PR-206"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
    "PR-208": (["PR-157", "PR-158", "PR-207"], "defensible", "PENDING", "REGISTERED_NOT_SCHEDULED"),
}
# Non-success typed edges inside the strengthening slice.
STRENGTHEN_TERMINAL_RECEIPT_EDGES = {("PR-203", "PR-151")}
STRENGTHEN_ADJUDICATED_EDGES = {("PR-208", "PR-157"), ("PR-208", "PR-158")}
STRENGTHEN_CAS_CARDS = {
    "PR-186", "PR-187", "PR-189", "PR-190", "PR-191", "PR-192", "PR-193", "PR-194",
}
STRENGTHEN_SCHEDULED = {
    pr for pr, contract in STRENGTHEN_CARD_CONTRACTS.items()
    if contract[3] in {"DAG_SCHEDULABLE", "EXPLICIT_USER_AUTHORIZED"}
}
# --- Legacy-revival round-2 dual-track wave (PR-209..246) ------------------
# Formal intake of htt_legacy_revival_round2_20260721 (round-2 sits on the
# round-1 strengthening package = prior_round1/ = PR-185..208). Track I
# (PR-209..228) is solver-independent and DAG_SCHEDULABLE this session; Track II
# (PR-229..242) and Integration (PR-243..246) are native-blocked (NEEDS_NATIVE,
# solver_gate_required) and REGISTERED_NOT_SCHEDULED. The track boundary is
# one-directional: no Track-I card may depend on a Track-II/Integration card.
REVIVAL_FIRST_PR = 209
REVIVAL_LAST_PR = 246
REVIVAL_CARD_COUNT = REVIVAL_LAST_PR - REVIVAL_FIRST_PR + 1
REVIVAL_TRACK_I = {f"PR-{n}" for n in range(209, 229)}
REVIVAL_TRACK_II = {f"PR-{n}" for n in range(229, 243)}
REVIVAL_INTEGRATION = {f"PR-{n}" for n in range(243, 247)}
# Pinned dependency edges (the load-bearing DAG structure); lane/activation/
# authorization/solver_gate are derived from track so card and validator cannot
# drift. PR-226 binds PR-151's acquisition terminal receipt (DESI mock lane).
REVIVAL_DEPENDS = {
    "PR-209": [], "PR-210": ["PR-209"], "PR-211": ["PR-210"],
    "PR-212": ["PR-210", "PR-211"], "PR-213": ["PR-209"],
    "PR-214": ["PR-209", "PR-211", "PR-213"], "PR-215": ["PR-210", "PR-211", "PR-212"],
    "PR-216": ["PR-212", "PR-215"], "PR-217": ["PR-211", "PR-212", "PR-214"],
    "PR-218": ["PR-209", "PR-210", "PR-214"], "PR-219": ["PR-210", "PR-212", "PR-215"],
    "PR-220": ["PR-214", "PR-219"], "PR-221": ["PR-213", "PR-219", "PR-220"],
    "PR-222": ["PR-210", "PR-212", "PR-219"], "PR-223": ["PR-210", "PR-212"],
    "PR-224": ["PR-212", "PR-222"], "PR-225": ["PR-215", "PR-219", "PR-220"],
    # PR-226 deps follow the roadmap DAG (12_TRACK_DAG.json); the DESI
    # official-mock lane's wait on PR-151 is a card-internal scientific blocker
    # (run_pr226 refuses any DESI number until PR-151 is terminal), not a
    # structural DAG edge -- so PR-226's other three lanes can close.
    "PR-226": ["PR-221", "PR-222", "PR-224", "PR-225"],
    "PR-227": ["PR-209", "PR-214", "PR-226"], "PR-228": ["PR-227"],
    "PR-229": ["PR-214", "PR-218", "PR-223"], "PR-230": ["PR-229"],
    "PR-231": ["PR-229", "PR-230"], "PR-232": ["PR-230", "PR-231"],
    "PR-233": ["PR-232"], "PR-234": ["PR-233"], "PR-235": ["PR-231", "PR-233", "PR-223"],
    "PR-236": ["PR-232", "PR-234", "PR-235"], "PR-237": ["PR-231", "PR-234", "PR-236"],
    "PR-238": ["PR-236", "PR-237", "PR-219"], "PR-239": ["PR-218", "PR-236"],
    "PR-240": ["PR-222", "PR-226", "PR-235", "PR-236"],
    "PR-241": ["PR-234", "PR-237", "PR-238", "PR-240"], "PR-242": ["PR-239", "PR-241"],
    "PR-243": ["PR-228", "PR-242"], "PR-244": ["PR-243"], "PR-245": ["PR-244"],
    "PR-246": ["PR-245"],
}
# PR-226's DESI wait on PR-151 is a card-internal scientific blocker, not a
# structural DAG edge (see REVIVAL_DEPENDS["PR-226"]); no terminal-receipt edges.
REVIVAL_TERMINAL_RECEIPT_EDGES: set[tuple[str, str]] = set()
REVIVAL_CAS_CARDS = {"PR-222", "PR-223"}

# --- Process-integrity interruption card (PR-247, Wave 42) -----------------
# This is an internal DAG work unit, not a GitHub pull request.  It is
# deliberately outside the scientific revival slices and carries no scientific
# claim level.  Its explicit intake prevents urgent harness work from bypassing
# the same DAG/status authority it is repairing.
PROCESS_INTEGRITY_CARD_CONTRACTS = {
    "PR-247": {
        "depends": ["PR-124", "PR-167"],
        "change_set_id": "CS-PR247-PUBLICATION-INTEGRITY-P0",
        "publication_group_id": "PG-PR247-PUBLICATION-INTEGRITY-P0",
        "execution_lane": "defensible",
        "activation_state": "PENDING",
        "execution_authorization": "EXPLICIT_USER_AUTHORIZED",
    }
}

# --- Statistical-foundation reconstruction (PR-248..252, Waves 43..47) ----
# These cards separate signed Gauss/Friedmann coordinates, typed anchor
# stress, identified estimands, finite-covariance inference, and orbit/model
# discrepancy.  They are an atomic intake but remain five sequential internal
# change sets and at most one externally published PR at a time.
FOUNDATION_FIRST_PR = 248
FOUNDATION_LAST_PR = 252
FOUNDATION_CARD_CONTRACTS = {
    "PR-248": {
        "depends": ["PR-124", "PR-168", "PR-187", "PR-247"],
        "owner": "COMMON",
        "change_set_id": "CS-PR248-TYPED-MES-AUTHORITY",
        "publication_group_id": "PG-PR248-TYPED-MES-AUTHORITY",
    },
    "PR-249": {
        "depends": ["PR-127", "PR-136", "PR-187", "PR-189", "PR-248"],
        "owner": "COMMON",
        "change_set_id": "CS-PR249-DEPARTURE-CONTRACTS",
        "publication_group_id": "PG-PR249-DEPARTURE-CONTRACTS",
    },
    "PR-250": {
        "depends": ["PR-137", "PR-189", "PR-200", "PR-225", "PR-249"],
        "owner": "HTT",
        "change_set_id": "CS-PR250-PARTIAL-ID-COVARIANCE",
        "publication_group_id": "PG-PR250-PARTIAL-ID-COVARIANCE",
    },
    "PR-251": {
        "depends": ["PR-216", "PR-219", "PR-250"],
        "owner": "HTT",
        "change_set_id": "CS-PR251-ORBIT-NONLINEARITY",
        "publication_group_id": "PG-PR251-ORBIT-NONLINEARITY",
    },
    "PR-252": {
        "depends": ["PR-251"],
        "owner": "COMMON",
        "change_set_id": "CS-PR252-FOUNDATION-INTEGRATION",
        "publication_group_id": "PG-PR252-FOUNDATION-INTEGRATION",
    },
}
FOUNDATION_DEPENDENCY_OVERLAY = {
    "schema": "htt.pr_dependency_overlay.v1",
    "authority": "PR-248",
    "rationale": (
        "Preserve receipt-sealed historical cards while applying the "
        "owner-authorized statistical-foundation replan."
    ),
    "additions": {
        "PR-155": ["PR-250", "PR-251"],
        "PR-156": ["PR-251"],
        "PR-157": ["PR-252"],
    },
}

# --- Premise-anchored response geometry (PR-253..258, Waves 48..53) ------
# PR-253 is a distinct atomic replan layered on top of the receipt-sealed
# statistical-foundation intake.  It extends the dependency overlay without
# attributing new edges retroactively to PR-248.
PREMISE_ANCHOR_CARD_CONTRACTS = {
    "PR-253": {
        "depends": ["PR-252"],
        "owner": "COMMON",
        "change_set_id": "CS-PR253-BASELINE-REPLAN",
        "publication_group_id": "PG-PR253-BASELINE-REPLAN",
        "forbidden": [
            "No PR-151 partial data, FLRW-departure result, or family-identification claim."
        ],
        "anti_drift": [
            "Proposed attachment numbers remain unverified inputs until independently regenerated."
        ],
    },
    "PR-254": {
        "depends": ["PR-253", "PR-216", "PR-217", "PR-225"],
        "owner": "COMMON",
        "change_set_id": "CS-PR254-ANCHOR-GEOMETRY",
        "publication_group_id": "PG-PR254-ANCHOR-GEOMETRY",
        "claim_contracts": claim_contracts_for_backlog(),
        "forbidden": [
            "No converse MES theorem, automatic e-value, or FLRW proximity claim."
        ],
        "anti_drift": [
            "MES may finish as ONE_ANCHOR_AMONG_FAMILY without making the benchmark fail."
        ],
    },
    "PR-255": {
        "depends": ["PR-254", "PR-219", "PR-251"],
        "owner": "HTT",
        "change_set_id": "CS-PR255-RESPONSE-GEOMETRY",
        "publication_group_id": "PG-PR255-RESPONSE-GEOMETRY",
        "forbidden": [
            "No native-solver, geometry-detection, or family-identification claim."
        ],
        "anti_drift": [
            "Held-out or matched-injection reuse invalidates candidate attribution."
        ],
    },
    "PR-256": {
        "depends": ["PR-255", "PR-222", "PR-251"],
        "owner": "HTT",
        "change_set_id": "CS-PR256-VELOCITY-FRAMES",
        "publication_group_id": "PG-PR256-VELOCITY-FRAMES",
        "forbidden": [
            "No observed DESI/CMB result, global-tilt detection, or geometry claim."
        ],
        "anti_drift": [
            "Analytic and synthetic responses remain hypothesis_only with non-native transfer provenance."
        ],
    },
    "PR-257": {
        "depends": ["PR-255", "PR-251"],
        "owner": "OBSSTAT",
        "change_set_id": "CS-PR257-LOWELL-MORPHOLOGY",
        "publication_group_id": "PG-PR257-LOWELL-MORPHOLOGY",
        "forbidden": [
            "No complete invariant-basis, cosmological detection, or family-identification claim without the declared proof and native gates."
        ],
        "anti_drift": [
            "OBSSTAT owns features and nulls; HTT alone owns held-out model/source comparison."
        ],
    },
    "PR-258": {
        "depends": ["PR-256", "PR-257", "PR-219"],
        "owner": "HTT",
        "change_set_id": "CS-PR258-OPEN-SET-INTEGRATION",
        "publication_group_id": "PG-PR258-OPEN-SET-INTEGRATION",
        "forbidden": [
            "No FLRW-departure detection, native-solver validation, or Bianchi-family identification."
        ],
        "anti_drift": [
            "Strong J1/J2 conjectures and blocked native steps remain outside validated manuscript results."
        ],
    },
}
PREMISE_ANCHOR_DEPENDENCY_OVERLAY = {
    "schema": "htt.pr_dependency_overlay.v1",
    "authority": "PR-253",
    "rationale": (
        "Preserve receipt-sealed historical cards while applying the "
        "owner-authorized statistical-foundation and premise-anchor replans."
    ),
    "additions": {
        "PR-155": ["PR-250", "PR-251", "PR-255"],
        "PR-156": ["PR-251", "PR-256", "PR-257"],
        "PR-157": ["PR-252"],
        "PR-181": ["PR-255", "PR-256", "PR-257"],
        "PR-193": ["PR-254"],
        "PR-205": ["PR-254", "PR-255"],
    },
}
PREMISE_ANCHOR_CARD_SEMANTIC_SHA256 = {
    "PR-253": "06af832de9b936a12e587d9242d57a7507e3013c20e124ab32315008a613e11f",
    "PR-254": "cc4a201550c8b34832ab93d5136379f38a8bb7bb8cc2d2728c9dc75eb1fa4321",
    "PR-255": "9222695858d24e6d9abb4fed865ab29e7cce5cffe945083bef318ad456f9a640",
    "PR-256": "e30ec0f706f817e827a80da054dcdf93d1ac9f932ee79eeb184874688533cd6a",
    "PR-257": "49030111c83160e40c366669eab1524d2db485e4956dccb5c44e34f47cf40adf",
    "PR-258": "364880c01495ee2be26fd573dca065d322040cb58c10d359750e3a8dbc69018a",
}

# --- Vector/tensor MES and proof programme (PR-259..275, Waves 54..66) ----
# PR-259/260 are the chronology/bootstrap pair.  PR-260 atomically registers
# the remaining PR-261..275 extension without changing any theorem status.
VECTOR_TENSOR_CARD_CONTRACTS = {
    "PR-259": {"depends": ["PR-258"], "owner": "COMMON"},
    "PR-260": {"depends": ["PR-259"], "owner": "COMMON"},
    "PR-261": {
        "depends": ["PR-260", "PR-249", "PR-256"],
        "owner": "COMMON",
    },
    "PR-262": {
        "depends": ["PR-261", "PR-254"],
        "owner": "COMMON",
    },
    "PR-263": {
        "depends": ["PR-261", "PR-257"],
        "owner": "OBSSTAT",
    },
    "PR-264": {"depends": ["PR-262", "PR-263"], "owner": "MIO"},
    "PR-265": {"depends": ["PR-264", "PR-250"], "owner": "MIO"},
    "PR-266": {"depends": ["PR-264"], "owner": "OBSSTAT"},
    "PR-267": {
        "depends": [
            "PR-263",
            "PR-265",
            "PR-266",
            "PR-255",
            "PR-256",
            "PR-258",
        ],
        "owner": "COMMON",
    },
    "PR-268": {
        "depends": ["PR-262", "PR-263", "PR-267"],
        "owner": "COMMON",
    },
    "PR-269": {"depends": ["PR-268"], "owner": "COMMON"},
    "PR-270": {"depends": ["PR-269"], "owner": "COMMON"},
    "PR-271": {"depends": ["PR-268"], "owner": "HTT"},
    "PR-272": {"depends": ["PR-271"], "owner": "HTT"},
    "PR-273": {"depends": ["PR-270", "PR-272"], "owner": "HTT"},
    "PR-274": {"depends": ["PR-273"], "owner": "OBSSTAT"},
    "PR-275": {"depends": ["PR-274"], "owner": "COMMON"},
}
VECTOR_TENSOR_BOOTSTRAP_IDS = {"PR-259", "PR-260"}
VECTOR_TENSOR_FULL_IDS = set(VECTOR_TENSOR_CARD_CONTRACTS)
VECTOR_TENSOR_REQUIRED_FIELDS = ADVOCATE_REQUIRED_FIELDS | {
    "capability",
    "inputs",
    "outputs",
    "track",
    "solver_gate_required",
}

# --- Post-275 re-adjudication and reexecution (PR-276..294, Waves 67..74) --
# PR-276 consumes the terminal PR-190 refutation without reopening either
# historical requires-success edge.  The remaining cards are registered as one
# prospective programme; data execution still needs its lane-specific human
# authorization receipt.
POST275_CARD_CONTRACTS = {
    "PR-276": {
        "owner": "COMMON",
        "dependencies": [("PR-190", "requires_terminal_receipt")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-277": {
        "owner": "COMMON",
        "dependencies": [("PR-276", "requires_success")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-278": {
        "owner": "COMMON",
        "dependencies": [("PR-277", "requires_success")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-279": {
        "owner": "COMMON",
        "dependencies": [("PR-278", "requires_success")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-280": {
        "owner": "COMMON",
        "dependencies": [("PR-279", "requires_success")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-281": {
        "owner": "COMMON",
        "dependencies": [("PR-280", "requires_terminal_receipt")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-282": {
        "owner": "OBSSTAT",
        "dependencies": [("PR-280", "requires_terminal_receipt")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-283": {
        "owner": "HTT",
        "dependencies": [("PR-280", "requires_terminal_receipt")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-284": {
        "owner": "HTT",
        "dependencies": [("PR-280", "requires_terminal_receipt")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-285": {
        "owner": "COMMON",
        "dependencies": [("PR-280", "requires_terminal_receipt")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-286": {
        "owner": "HTT",
        "dependencies": [("PR-280", "requires_terminal_receipt")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-287": {
        "owner": "HTT",
        "dependencies": [
            ("PR-281", "requires_success"),
            ("PR-282", "requires_success"),
            ("PR-283", "requires_success"),
            ("PR-284", "requires_success"),
            ("PR-285", "requires_success"),
            ("PR-286", "requires_success"),
        ],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-288": {
        "owner": "HTT",
        "dependencies": [("PR-280", "requires_terminal_receipt")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-289": {
        "owner": "COMMON",
        "dependencies": [("PR-280", "requires_terminal_receipt")],
        "authorization": "EXPLICIT_USER_AUTHORIZED",
    },
    "PR-290": {
        "owner": "HTT",
        "dependencies": [
            ("PR-202", "requires_success"),
            ("PR-287", "requires_success"),
            ("PR-288", "requires_success"),
            ("PR-289", "requires_success"),
        ],
        "authorization": "HUMAN_GATE_REQUIRED",
    },
    "PR-291": {
        "owner": "HTT",
        "dependencies": [
            ("PR-201", "requires_success"),
            ("PR-287", "requires_success"),
            ("PR-289", "requires_success"),
        ],
        "authorization": "HUMAN_GATE_REQUIRED",
    },
    "PR-292": {
        "owner": "OBSSTAT",
        "dependencies": [
            ("PR-287", "requires_success"),
            ("PR-289", "requires_success"),
        ],
        "authorization": "HUMAN_GATE_REQUIRED",
    },
    "PR-293": {
        "owner": "HTT",
        "dependencies": [
            ("PR-287", "requires_success"),
            ("PR-288", "requires_success"),
            ("PR-289", "requires_success"),
        ],
        "authorization": "HUMAN_GATE_REQUIRED",
    },
    "PR-294": {
        "owner": "HTT",
        "dependencies": [
            ("PR-155", "requires_terminal_receipt"),
            ("PR-156", "requires_terminal_receipt"),
            ("PR-181", "requires_terminal_receipt"),
            ("PR-205", "requires_terminal_receipt"),
            ("PR-206", "requires_terminal_receipt"),
            ("PR-158", "requires_terminal_receipt"),
            ("PR-178", "requires_terminal_receipt"),
            ("PR-290", "requires_terminal_receipt"),
            ("PR-291", "requires_terminal_receipt"),
            ("PR-292", "requires_terminal_receipt"),
            ("PR-203", "requires_terminal_receipt"),
            ("PR-204", "requires_terminal_receipt"),
            ("PR-293", "requires_terminal_receipt"),
        ],
        "authorization": "REGISTERED_NOT_SCHEDULED",
    },
}
POST275_FULL_IDS = set(POST275_CARD_CONTRACTS)
POST275_REQUIRED_FIELDS = VECTOR_TENSOR_REQUIRED_FIELDS | {
    "change_set_id",
    "publication_group_id",
}
PR280_ROOT_CAUSE_CARD_CONTRACTS = {
    "PR-295": {
        "owner": "BASS",
        "capability": "external_camb_oracle_separated_from_production_runtime",
        "failure_node": (
            "htt.bass.validation.test_external_code_policy::"
            "test_no_external_code_imports_in_production"
        ),
        "claim_level": {
            "scheme": "not_applicable_governance_v1",
            "level": "NOT_APPLICABLE",
        },
    },
    "PR-296": {
        "owner": "BASS",
        "capability": (
            "python_pstf_d2_nonregression_restored_without_baseline_laundering"
        ),
        "failure_node": (
            "htt.bass.spectrum.test_d2_pstf_progressive_closure::"
            "test_python_pstf_closure_does_not_regress"
        ),
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
    },
    "PR-297": {
        "owner": "COMMON",
        "capability": (
            "repo_scoped_handoff_installer_closes_registered_context_dependencies"
        ),
        "failure_node": (
            "scripts.codex_harness.test_codex_assets::"
            "test_installer_copies_repo_scoped_assets_with_project_harness_config"
        ),
        "claim_level": {
            "scheme": "not_applicable_governance_v1",
            "level": "NOT_APPLICABLE",
        },
    },
}
PR280_ROOT_CAUSE_FULL_IDS = set(PR280_ROOT_CAUSE_CARD_CONTRACTS)
PR280_DIRECT_CONSUMERS = {
    "PR-281",
    "PR-282",
    "PR-283",
    "PR-284",
    "PR-285",
    "PR-286",
    "PR-288",
    "PR-289",
}
POST275_HUMAN_GATES = {
    "PR-290": ("H-PLANCK", "admitted_planck_observed_execution"),
    "PR-291": ("H-CF4", "admitted_cf4_observed_execution"),
    "PR-292": ("H-HSC-KiDS", "admitted_hsc_kids_observed_execution"),
    "PR-293": ("H-JWST", "admitted_jwst_sn_observed_execution"),
}
POST275_DEPENDENCY_OVERLAY = {
    "schema": "htt.pr_dependency_overlay.v1",
    "authority": "PR-276",
    "rationale": (
        "Preserve receipt-sealed historical cards while applying the "
        "owner-authorized statistical-foundation, premise-anchor, and "
        "post-275 reexecution replans."
    ),
    "additions": {
        "PR-155": ["PR-250", "PR-251", "PR-255"],
        "PR-156": ["PR-251", "PR-256", "PR-257"],
        "PR-157": ["PR-252", "PR-278"],
        "PR-181": ["PR-255", "PR-256", "PR-257"],
        "PR-191": ["PR-285"],
        "PR-192": ["PR-285"],
        "PR-193": ["PR-254", "PR-285"],
        "PR-194": ["PR-285"],
        "PR-195": ["PR-285"],
        "PR-198": ["PR-281", "PR-282", "PR-287", "PR-288", "PR-289"],
        "PR-201": ["PR-283", "PR-284", "PR-287", "PR-289"],
        "PR-204": ["PR-287", "PR-288", "PR-289"],
        "PR-205": ["PR-254", "PR-255"],
        "PR-207": ["PR-294"],
        "PR-281": ["PR-295", "PR-296", "PR-297"],
        "PR-282": ["PR-295", "PR-296", "PR-297"],
        "PR-283": ["PR-295", "PR-296", "PR-297"],
        "PR-284": ["PR-295", "PR-296", "PR-297"],
        "PR-285": ["PR-295", "PR-296", "PR-297"],
        "PR-286": ["PR-295", "PR-296", "PR-297"],
        "PR-288": ["PR-295", "PR-296", "PR-297"],
        "PR-289": ["PR-295", "PR-296", "PR-297"],
    },
}


def _revival_track(pr_id: str) -> str:
    n = int(pr_id.split("-")[1])
    if pr_id in REVIVAL_TRACK_I or 209 <= n <= 228:
        return "I"
    if 229 <= n <= 242:
        return "II"
    return "INTEGRATION"


def _revival_expected(pr_id: str) -> tuple[str, str, str, str, bool]:
    """(execution_lane, activation_state, execution_authorization, track, solver_gate)."""
    track = _revival_track(pr_id)
    if track == "I":
        return ("defensible", "PENDING", "DAG_SCHEDULABLE", track, False)
    return ("needs_native", "NEEDS_NATIVE", "NATIVE_BLOCKED", track, True)


ADVOCATE_TITLE_OVERRIDES = {
    "PR-174": "SW-only real-space anisotropic ray-integration mechanics (hypothesis_only)",
    "PR-175": "Cross-engine Bianchi invariant mechanics from structure constants (hypothesis_only)",
    "PR-177": "ACT DR6 in-band kappa off-diagonal modulation diagnostic (release-simulation-conditional)",
    "PR-182": "Solver-free parity theorem and handedness reference-signal registry (hypothesis_only)",
    "PR-183": "Native-dependent low-ell T/E coherence hypothesis-test interface",
}
ADVOCATE_RECEIPT = (
    Path(__file__).resolve().parents[2]
    / "docs/generated/pr167_pre_intake_semantic_receipt.json"
)
ADVOCATE_TRANSACTION_JOURNAL = (
    Path(__file__).resolve().parents[2]
    / ".agent-harness/generated/pr167_intake_write_journal.json"
)
PREMISE_ANCHOR_INTAKE = (
    Path(__file__).resolve().parents[2]
    / "docs/research_program/premise_anchor/pr253_input_intake.yaml"
)
RESCUE_SEMANTIC_CLAIM_FIELDS = (
    "title",
    "targets",
    "dod",
    "kill",
    "claim_impact",
    "forbidden",
    "anti_drift",
)
BARE_ACTIVE_CLAIM_LEVEL_RE = re.compile(
    r"(?<![A-Za-z0-9_:])C([0-6])(?!-[A-Za-z0-9])\b"
)
PR150_EXECUTION_CONSTRAINT = {
    "recorded_on": "2026-07-15",
    "authority": "explicit_user_instruction",
    "pr3_ffp10_e2e_download": "COMPLETE",
    "pr4_npipe_e2e_download": "NOT_STARTED",
    "pr4_npipe_all_downloads": "FORBIDDEN",
    "pr4_npipe_reduction": "SKIP_ENTIRELY",
    "pr4_data_analysis": "SKIP_ENTIRELY",
    "pr4_numeric_figure_combined_outputs": "FORBIDDEN",
    "original_joint_pr3_pr4_c3_gate_satisfied": False,
}
PR150_FORBIDDEN = [
    "PR4/NPIPE 데이터는 full-frequency, component-separated, single-channel, subset-stream, partial-range 등 어떤 형태로도 다운로드하지 않는다. 기존 또는 외부 PR4 payload도 intake·reduction·cache·analysis에 사용하지 않는다. PR4/NPIPE numeric result, table, figure, p-value, method comparison, PR3+PR4 combined output을 생성하지 않는다. 허용되는 PR4 산출물은 비수치 SKIPPED_BY_USER_SCOPE receipt뿐이다."
]
PR150_SEMANTIC_CONTRACT = {
    "dod": [
        "PR3/FFP10 E2E 입력은 다운로드 완료 상태로 intake하고 PR-149에서 freeze한 동일 mask/transfer/statistic/max-scan 경로로 exchangeable pooled-rank calibration을 수행한다. PR4/NPIPE는 full-frequency, component-separated, single-channel, subset-stream, partial-range를 포함한 어떤 데이터도 다운로드하지 않고 reduction·분석도 전부 실행하지 않는다.",
        "PR3 input license/hash manifest, observed/null byte-equivalent runner, finite-rank intervals, method-wise/global scan, Tier-1/Tier-2 retention receipt와 faithful-cache gate. PR4 관련 산출물은 비수치 SKIPPED_BY_USER_SCOPE receipt만 만들고 PR4/NPIPE 수치·표·그림·p-value·method comparison·PR3+PR4 결합 결과를 생성하지 않는다.",
    ],
    "kill": (
        "PR3 E2E input/support가 없거나 observed/null path가 다르면 scientific status는 "
        "BLOCKED로 유지한다. PR4/NPIPE payload를 종류·채널·subset·부분 범위와 무관하게 "
        "다운로드하거나 reduction/분석에 사용하거나, PR4 수치·표·그림·결합 산출물을 만들거나, "
        "PR4가 없는 상태를 joint PR3+PR4 calibration으로 대체하거나 original "
        "roadmap_rescue_v1:C3 gate 통과로 기록하면 실패다. PR3 raw는 faithful-cache gate "
        "GREEN 전 삭제하지 않는다."
    ),
    "claim_impact": (
        "PR3/FFP10-E2E-conditional morphology diagnostic roadmap_rescue_v1:C2 only; "
        "PR4/NPIPE systematics comparison and original joint roadmap_rescue_v1:C3 claim "
        "remain unavailable."
    ),
    "forbidden": PR150_FORBIDDEN,
    "anti_drift": [
        "원 로드맵은 PR4를 필수 추가분석으로 정의하지만 2026-07-15 사용자 지시에 따라 PR4/NPIPE의 모든 다운로드·reduction·데이터 분석과 수치·표·그림·결합 산출물을 전부 스킵한다. 이 scope reduction은 PR4를 optional evidence로 재해석하지 않으며, PR4 의존 결론은 BLOCKED/미판정으로 남긴다."
    ],
}


@dataclass(frozen=True)
class DagInfo:
    prs: tuple[dict[str, Any], ...]
    ids: tuple[str, ...]
    order: tuple[str, ...]
    prereqs: dict[str, tuple[str, ...]]
    children: dict[str, tuple[str, ...]]

    @property
    def edge_count(self) -> int:
        return sum(len(deps) for deps in self.prereqs.values())


def load_yaml(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("backlog YAML must contain a mapping")
    return payload


def _duplicate_values(values: list[str]) -> list[str]:
    return sorted({value for value in values if values.count(value) > 1})


def _stable_topological_order(ids: list[str], prereqs: dict[str, list[str]]) -> list[str]:
    indeg = {pr_id: 0 for pr_id in ids}
    children: dict[str, list[str]] = defaultdict(list)
    for pr_id in ids:
        for dep in prereqs[pr_id]:
            children[dep].append(pr_id)
            indeg[pr_id] += 1

    q = deque([pr_id for pr_id in ids if indeg[pr_id] == 0])
    order: list[str] = []
    while q:
        current = q.popleft()
        order.append(current)
        for child in children[current]:
            indeg[child] -= 1
            if indeg[child] == 0:
                q.append(child)

    if len(order) != len(ids):
        cycle = [pr_id for pr_id, degree in indeg.items() if degree > 0]
        raise ValueError(f"cycle detected involving: {cycle}")
    return order


def _validate_policy_order(
    policy_order: list[str],
    ids: list[str],
    prereqs: dict[str, list[str]],
) -> list[str]:
    if len(policy_order) != len(set(policy_order)):
        raise ValueError(
            f"duplicate policy.topological_order ids: {_duplicate_values(policy_order)}"
        )

    idset = set(ids)
    policy_set = set(policy_order)
    missing = sorted(idset - policy_set)
    unknown = sorted(policy_set - idset)
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing ids: {missing}")
        if unknown:
            parts.append(f"unknown ids: {unknown}")
        raise ValueError("policy.topological_order coverage mismatch: " + "; ".join(parts))

    rank = {pr_id: index for index, pr_id in enumerate(policy_order)}
    violations = [
        f"{dep}->{pr_id}"
        for pr_id, deps in prereqs.items()
        for dep in deps
        if rank[dep] >= rank[pr_id]
    ]
    if violations:
        raise ValueError(
            "policy.topological_order violates dependency order: "
            + ", ".join(violations)
        )
    return policy_order


def validate_backlog(data: dict[str, Any]) -> DagInfo:
    prs_obj = data.get("prs", [])
    if not isinstance(prs_obj, list):
        raise ValueError("prs must be a list")
    prs = []
    for index, pr in enumerate(prs_obj):
        if not isinstance(pr, dict):
            raise ValueError(f"prs[{index}] must be a mapping")
        if not isinstance(pr.get("id"), str) or not pr["id"]:
            raise ValueError(f"prs[{index}] missing string id")
        depends = pr.get("depends", [])
        if depends is None:
            depends = []
        if not isinstance(depends, list) or not all(isinstance(d, str) for d in depends):
            raise ValueError(f"{pr['id']} depends must be a list of strings")
        if len(depends) != len(set(depends)):
            raise ValueError(
                f"{pr['id']} duplicate dependency ids: {_duplicate_values(depends)}"
            )
        prs.append(pr)

    ids = [pr["id"] for pr in prs]
    duplicate_ids = _duplicate_values(ids)
    if duplicate_ids:
        raise ValueError(f"duplicate PR ids: {duplicate_ids}")

    idset = set(ids)
    premise_ids = set(PREMISE_ANCHOR_CARD_CONTRACTS)
    present_premise_ids = idset & premise_ids
    if present_premise_ids and present_premise_ids != premise_ids:
        raise ValueError(
            "premise-anchor intake must be atomic; "
            f"missing={sorted(premise_ids - present_premise_ids)}"
        )
    present_vector_tensor_ids = idset & VECTOR_TENSOR_FULL_IDS
    if present_vector_tensor_ids not in (
        set(),
        VECTOR_TENSOR_BOOTSTRAP_IDS,
        VECTOR_TENSOR_FULL_IDS,
    ):
        raise ValueError(
            "vector/tensor intake must be either the PR-259/260 bootstrap or "
            "the complete PR-259..275 programme; "
            f"present={sorted(present_vector_tensor_ids)}"
        )
    present_post275_ids = idset & POST275_FULL_IDS
    if present_post275_ids and present_post275_ids != POST275_FULL_IDS:
        raise ValueError(
            "post-275 intake must register PR-276..294 atomically; "
            f"missing={sorted(POST275_FULL_IDS - present_post275_ids)}"
        )
    present_pr280_root_cause_ids = idset & PR280_ROOT_CAUSE_FULL_IDS
    if (
        present_pr280_root_cause_ids
        and present_pr280_root_cause_ids != PR280_ROOT_CAUSE_FULL_IDS
    ):
        raise ValueError(
            "PR-280 root-cause intake must register PR-295..297 atomically; "
            f"missing={sorted(PR280_ROOT_CAUSE_FULL_IDS - present_pr280_root_cause_ids)}"
        )
    if present_pr280_root_cause_ids and present_post275_ids != POST275_FULL_IDS:
        raise ValueError("PR-280 root-cause intake requires the full post-275 programme")
    prereqs = {pr["id"]: list(pr.get("depends") or []) for pr in prs}
    missing_deps = sorted({dep for deps in prereqs.values() for dep in deps if dep not in idset})
    if missing_deps:
        raise ValueError(f"missing dependency ids: {missing_deps}")

    policy_raw = data.get("policy")
    if policy_raw is not None and not isinstance(policy_raw, dict):
        raise ValueError("policy must be a mapping")
    policy = policy_raw or {}
    overlay = policy.get("dependency_overlays")
    if overlay is not None:
        if not isinstance(overlay, dict):
            raise ValueError("policy.dependency_overlays must be a mapping")
        additions = overlay.get("additions")
        if not isinstance(additions, dict):
            raise ValueError(
                "policy.dependency_overlays.additions must be a mapping"
            )
        for pr_id, added_deps in additions.items():
            if pr_id not in idset:
                raise ValueError(
                    f"dependency overlay has unknown target id: {pr_id!r}"
                )
            if (
                not isinstance(added_deps, list)
                or not all(isinstance(dep, str) for dep in added_deps)
                or len(added_deps) != len(set(added_deps))
            ):
                raise ValueError(
                    f"dependency overlay for {pr_id} must be a unique string list"
                )
            unknown = sorted(set(added_deps) - idset)
            if unknown:
                raise ValueError(
                    f"dependency overlay for {pr_id} has unknown ids: {unknown}"
                )
            duplicate = sorted(set(added_deps) & set(prereqs[pr_id]))
            if duplicate:
                raise ValueError(
                    f"dependency overlay for {pr_id} duplicates card edges: {duplicate}"
                )
            prereqs[pr_id].extend(added_deps)

    computed_order = _stable_topological_order(ids, prereqs)
    policy_order = policy.get("topological_order")
    if policy_order is not None:
        if not isinstance(policy_order, list) or not all(
            isinstance(pr_id, str) for pr_id in policy_order
        ):
            raise ValueError("policy.topological_order must be a list of PR ids")
        order = _validate_policy_order(policy_order, ids, prereqs)
    else:
        order = computed_order

    children: dict[str, list[str]] = {pr_id: [] for pr_id in ids}
    for pr_id, deps in prereqs.items():
        for dep in deps:
            children[dep].append(pr_id)

    return DagInfo(
        prs=tuple(prs),
        ids=tuple(ids),
        order=tuple(order),
        prereqs={pr_id: tuple(deps) for pr_id, deps in prereqs.items()},
        children={pr_id: tuple(children[pr_id]) for pr_id in ids},
    )


def _pr_range(first: int, last: int) -> list[str]:
    return [f"PR-{number:03d}" for number in range(first, last + 1)]


def _require_string_list(card: dict[str, Any], field: str) -> list[str]:
    value = card.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{card['id']} {field} must be a list of strings")
    return value


def _require_nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)


def _validate_rescue_status(status: dict[str, Any], info: DagInfo) -> None:
    list_fields = (
        "completed",
        "blocked",
        "skipped",
        "pending",
        "dormant_external",
        "background_in_progress",
    )
    states: dict[str, list[str]] = {}
    for field in list_fields:
        value = status.get(field, []) or []
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"status {field} must be a list of PR ids")
        if len(value) != len(set(value)):
            raise ValueError(f"status {field} contains duplicate PR ids")
        states[field] = value

    in_progress = status.get("in_progress")
    if in_progress is not None and not isinstance(in_progress, str):
        raise ValueError("status in_progress must be a PR id or null")

    membership: dict[str, list[str]] = defaultdict(list)
    for field, values in states.items():
        for pr_id in values:
            membership[pr_id].append(field)
    if in_progress is not None:
        membership[in_progress].append("in_progress")

    unknown = sorted(set(membership) - set(info.ids))
    if unknown:
        raise ValueError(f"status contains unknown PR ids: {unknown}")
    overlap = {pr_id: fields for pr_id, fields in membership.items() if len(fields) != 1}
    if overlap:
        raise ValueError(f"status orchestration states overlap: {overlap}")
    missing = sorted(set(info.ids) - set(membership))
    if missing:
        raise ValueError(f"status orchestration coverage missing PR ids: {missing}")

    cards = {card["id"]: card for card in info.prs}
    dormant_expected = {
        pr_id
        for pr_id, card in cards.items()
        if card.get("activation_state") in TYPED_DORMANT_ACTIVATION_STATES
    }
    dormant_actual = set(states["dormant_external"])
    if dormant_actual != dormant_expected:
        raise ValueError(
            "dormant_external must be derived from typed activation_state; "
            f"missing={sorted(dormant_expected - dormant_actual)}, "
            f"unexpected={sorted(dormant_actual - dormant_expected)}"
        )

    lane_status = status.get("execution_lane", {}) or {}
    if not isinstance(lane_status, dict) or not all(
        isinstance(pr_id, str) and isinstance(lane, str)
        for pr_id, lane in lane_status.items()
    ):
        raise ValueError("status execution_lane must be a PR-id to lane mapping")
    card_lanes = {
        pr_id: str(card["execution_lane"])
        for pr_id, card in cards.items()
        if "execution_lane" in card
    }
    if lane_status != card_lanes:
        raise ValueError("status execution_lane must exactly match typed advocate card lanes")
    invalid_lanes = sorted(set(lane_status.values()) - ADVOCATE_EXECUTION_LANES)
    if invalid_lanes:
        raise ValueError(f"status execution_lane contains invalid lanes: {invalid_lanes}")
    background_contracts = status.get("background_execution_contracts", {}) or {}
    expected_background_contracts = (
        BACKGROUND_EXECUTION_CONTRACTS
        if states["background_in_progress"] == ["PR-151"]
        else {}
    )
    if background_contracts != expected_background_contracts:
        raise ValueError(
            "status background_execution_contracts must retain the exact PR-151 "
            "acquire-only authorization"
        )
    if states["background_in_progress"] not in ([], ["PR-151"]):
        raise ValueError("only PR-151 may be a background acquisition")

    resolutions = status.get("execution_resolutions", {}) or {}
    if not isinstance(resolutions, dict):
        raise ValueError("status execution_resolutions must be a mapping")
    rescue_ids = {
        pr_id for pr_id in info.ids if int(pr_id[-3:]) >= RESCUE_FIRST_PR
    }
    terminal = set(states["completed"]) | set(states["blocked"]) | set(states["skipped"])
    expected_resolutions_by_bucket = {
        **{pr_id: {"COMPLETED_SUCCESS"} for pr_id in states["completed"]},
        **{
            pr_id: {"BLOCKED_WITH_RECEIPT", "COMPLETED_FAILED_WITH_RECEIPT"}
            for pr_id in states["blocked"]
        },
        **{pr_id: {"ABANDONED_WITH_RECEIPT"} for pr_id in states["skipped"]},
    }
    for pr_id, receipt in resolutions.items():
        if pr_id not in rescue_ids:
            raise ValueError(f"execution resolution is restricted to rescue cards: {pr_id}")
        if pr_id not in terminal:
            raise ValueError(f"non-terminal PR has execution resolution: {pr_id}")
        if not isinstance(receipt, dict):
            raise ValueError(f"execution resolution for {pr_id} must be a mapping")
        resolution = receipt.get("resolution")
        if resolution not in RESCUE_EXECUTION_RESOLUTIONS:
            raise ValueError(f"invalid execution resolution for {pr_id}: {resolution!r}")
        expected_resolutions = expected_resolutions_by_bucket[pr_id]
        if resolution not in expected_resolutions:
            raise ValueError(
                f"{pr_id} terminal bucket requires one of "
                f"{sorted(expected_resolutions)}, "
                f"found {resolution!r}"
            )
        receipt_pointer = receipt.get("receipt")
        if not isinstance(receipt_pointer, str) or not receipt_pointer.strip():
            raise ValueError(f"{pr_id} execution resolution receipt pointer must be nonempty")
    terminal_rescue = terminal & rescue_ids
    missing_receipts = sorted(terminal_rescue - set(resolutions))
    if missing_receipts:
        raise ValueError(
            "terminal rescue cards require execution resolution receipts: "
            f"{missing_receipts}"
        )


def validate_long_horizon_rescue_slice(
    data: dict[str, Any],
    info: DagInfo,
    *,
    status: dict[str, Any] | None = None,
) -> None:
    """Validate the PR-119..166 intake without treating DAG state as science."""

    expected_ids = set(_pr_range(RESCUE_FIRST_PR, RESCUE_LAST_PR))
    advocate_ids = set(_pr_range(ADVOCATE_FIRST_PR, ADVOCATE_LAST_PR))
    actual_ids = set(info.ids)
    actual_rescue_ids = actual_ids & expected_ids
    if actual_rescue_ids != expected_ids:
        raise ValueError(
            "strict rescue slice must contain exactly PR-119..PR-166; "
            f"missing={sorted(expected_ids - actual_rescue_ids)}"
        )
    actual_advocate_ids = actual_ids & advocate_ids
    if actual_advocate_ids and actual_advocate_ids != advocate_ids:
        raise ValueError(
            "PR-167 advocate intake must be atomic; "
            f"missing={sorted(advocate_ids - actual_advocate_ids)}"
        )
    strengthen_ids = set(_pr_range(STRENGTHEN_FIRST_PR, STRENGTHEN_LAST_PR))
    actual_strengthen_ids = actual_ids & strengthen_ids
    if actual_strengthen_ids and not actual_advocate_ids:
        raise ValueError(
            "strengthening wave (PR-185+) requires the advocate slice to be present"
        )
    if actual_strengthen_ids and actual_strengthen_ids != strengthen_ids:
        raise ValueError(
            "post-v10 strengthening intake must be atomic; "
            f"missing={sorted(strengthen_ids - actual_strengthen_ids)}"
        )
    revival_ids = set(_pr_range(REVIVAL_FIRST_PR, REVIVAL_LAST_PR))
    actual_revival_ids = actual_ids & revival_ids
    if actual_revival_ids and not actual_strengthen_ids:
        raise ValueError(
            "legacy-revival wave (PR-209+) requires the strengthening slice to be present"
        )
    if actual_revival_ids and actual_revival_ids != revival_ids:
        raise ValueError(
            "legacy-revival round-2 intake must be atomic; "
            f"missing={sorted(revival_ids - actual_revival_ids)}"
        )
    process_ids = set(PROCESS_INTEGRITY_CARD_CONTRACTS)
    actual_process_ids = actual_ids & process_ids
    if actual_process_ids and not actual_revival_ids:
        raise ValueError(
            "process-integrity interruption cards require the full revival slice"
        )
    if actual_process_ids and actual_process_ids != process_ids:
        raise ValueError(
            "process-integrity interruption intake must be atomic; "
            f"missing={sorted(process_ids - actual_process_ids)}"
        )
    foundation_ids = set(FOUNDATION_CARD_CONTRACTS)
    actual_foundation_ids = actual_ids & foundation_ids
    if actual_foundation_ids and not actual_process_ids:
        raise ValueError(
            "statistical-foundation cards require the process-integrity card"
        )
    if actual_foundation_ids and actual_foundation_ids != foundation_ids:
        raise ValueError(
            "statistical-foundation intake must be atomic; "
            f"missing={sorted(foundation_ids - actual_foundation_ids)}"
        )
    premise_anchor_ids = set(PREMISE_ANCHOR_CARD_CONTRACTS)
    actual_premise_anchor_ids = actual_ids & premise_anchor_ids
    if actual_premise_anchor_ids and actual_foundation_ids != foundation_ids:
        raise ValueError(
            "premise-anchor cards require the full statistical-foundation slice"
        )
    if actual_premise_anchor_ids and actual_premise_anchor_ids != premise_anchor_ids:
        raise ValueError(
            "premise-anchor intake must be atomic; "
            f"missing={sorted(premise_anchor_ids - actual_premise_anchor_ids)}"
        )
    vector_tensor_ids = set(VECTOR_TENSOR_CARD_CONTRACTS)
    actual_vector_tensor_ids = actual_ids & vector_tensor_ids
    if actual_vector_tensor_ids and actual_premise_anchor_ids != premise_anchor_ids:
        raise ValueError(
            "vector/tensor programme requires the full premise-anchor slice"
        )
    if actual_vector_tensor_ids not in (
        set(),
        VECTOR_TENSOR_BOOTSTRAP_IDS,
        VECTOR_TENSOR_FULL_IDS,
    ):
        raise ValueError(
            "vector/tensor intake must be either the PR-259/260 bootstrap or "
            "the complete PR-259..275 programme; "
            f"present={sorted(actual_vector_tensor_ids)}"
        )
    post275_ids = set(POST275_CARD_CONTRACTS)
    actual_post275_ids = actual_ids & post275_ids
    if actual_post275_ids and actual_vector_tensor_ids != VECTOR_TENSOR_FULL_IDS:
        raise ValueError(
            "post-275 programme requires the full PR-259..275 vector/tensor programme"
        )
    if actual_post275_ids and actual_post275_ids != post275_ids:
        raise ValueError(
            "post-275 intake must be atomic; "
            f"missing={sorted(post275_ids - actual_post275_ids)}"
        )
    pr280_root_cause_ids = set(PR280_ROOT_CAUSE_CARD_CONTRACTS)
    actual_pr280_root_cause_ids = actual_ids & pr280_root_cause_ids
    if actual_pr280_root_cause_ids and actual_post275_ids != post275_ids:
        raise ValueError("PR-280 root-cause cards require the full post-275 slice")
    if (
        actual_pr280_root_cause_ids
        and actual_pr280_root_cause_ids != pr280_root_cause_ids
    ):
        raise ValueError(
            "PR-280 root-cause intake must be atomic; "
            f"missing={sorted(pr280_root_cause_ids - actual_pr280_root_cause_ids)}"
        )
    if actual_foundation_ids:
        policy = data.get("policy") or {}
        expected_overlay = (
            POST275_DEPENDENCY_OVERLAY
            if actual_post275_ids
            else (
                PREMISE_ANCHOR_DEPENDENCY_OVERLAY
                if actual_premise_anchor_ids
                else FOUNDATION_DEPENDENCY_OVERLAY
            )
        )
        if policy.get("dependency_overlays") != expected_overlay:
            raise ValueError(
                "statistical-foundation or premise-anchor dependency overlay drifted"
            )
    expected_total = (
        RESCUE_WITH_ADVOCATE_CARD_COUNT
        if actual_advocate_ids
        else RESCUE_PRE_ADVOCATE_CARD_COUNT
    )
    if actual_strengthen_ids:
        expected_total += STRENGTHEN_CARD_COUNT
    if actual_revival_ids:
        expected_total += REVIVAL_CARD_COUNT
    if actual_process_ids:
        expected_total += len(PROCESS_INTEGRITY_CARD_CONTRACTS)
    if actual_foundation_ids:
        expected_total += len(FOUNDATION_CARD_CONTRACTS)
    if actual_premise_anchor_ids:
        expected_total += len(PREMISE_ANCHOR_CARD_CONTRACTS)
    expected_total += len(actual_vector_tensor_ids)
    expected_total += len(actual_post275_ids)
    expected_total += len(actual_pr280_root_cause_ids)
    if len(info.ids) != expected_total:
        raise ValueError(
            f"strict rescue slice expects {expected_total} total cards, found {len(info.ids)}"
        )

    if actual_advocate_ids:
        if ADVOCATE_TRANSACTION_JOURNAL.exists():
            raise ValueError(
                "PR-167 advocate intake has an uncommitted write journal"
            )
        if not ADVOCATE_RECEIPT.is_file():
            raise ValueError("PR-167 advocate intake requires its pre-intake semantic receipt")
        try:
            receipt = json.loads(ADVOCATE_RECEIPT.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"PR-167 semantic receipt is unreadable: {exc}") from exc
        validate_pre_intake_receipt(
            receipt,
            backlog=data,
            status=status,
            expected_baseline_commit="fe7abb6aa01fdfaf0440956bd8727ddc9e1be8e7",
            expected_backlog_sha256="9693706872a5e13514c0eb3e4ca9dab9a281359edac4cda9877d26dae8c68f07",
            expected_status_sha256="fcd81fc2d904ff8ed360f1055688bb122b4006ea1ca0e570c0b39cf6486f8759",
            expected_roadmap_sha256="caaab4b7255181e75093a5b662f4febf278330db07dad7cdce65e44c6587b361",
        )

    cards = {card["id"]: card for card in info.prs}
    for pr_id in _pr_range(RESCUE_FIRST_PR, RESCUE_LAST_PR):
        card = cards[pr_id]
        missing_fields = sorted(RESCUE_REQUIRED_FIELDS - set(card))
        if missing_fields:
            raise ValueError(f"{pr_id} missing rescue-card fields: {missing_fields}")
        owner = card.get("owner")
        if owner in RESCUE_FORBIDDEN_OWNERS or owner not in RESCUE_ACTIVE_OWNERS:
            raise ValueError(f"{pr_id} has forbidden or unknown active owner: {owner!r}")
        contributors = _require_string_list(card, "contributors")
        invalid_contributors = sorted(set(contributors) - RESCUE_ACTIVE_OWNERS)
        if invalid_contributors:
            raise ValueError(f"{pr_id} has invalid contributors: {invalid_contributors}")
        scopes = _require_string_list(card, "implementation_scopes")
        if not scopes or set(scopes) - RESCUE_IMPLEMENTATION_SCOPES:
            raise ValueError(f"{pr_id} has invalid implementation scopes: {scopes}")

        depends = _require_string_list(card, "depends")
        contracts = card.get("dependency_contracts")
        if not isinstance(contracts, list) or not all(
            isinstance(contract, dict) for contract in contracts
        ):
            raise ValueError(f"{pr_id} dependency_contracts must be a list of mappings")
        upstreams = [contract.get("upstream_id") for contract in contracts]
        if upstreams != depends:
            raise ValueError(
                f"{pr_id} typed dependency projection must exactly match depends: "
                f"{upstreams!r} != {depends!r}"
            )
        for contract in contracts:
            if set(contract) != {"upstream_id", "mode"}:
                raise ValueError(f"{pr_id} dependency contract has unknown fields: {contract}")
            if contract["mode"] not in RESCUE_EDGE_MODES:
                raise ValueError(f"{pr_id} has invalid dependency mode: {contract['mode']!r}")

        claim_level = card.get("claim_level")
        if not isinstance(claim_level, dict) or set(claim_level) != {"scheme", "level"}:
            raise ValueError(f"{pr_id} claim_level must contain explicit scheme and level")
        scheme = claim_level.get("scheme")
        level = claim_level.get("level")
        if scheme not in RESCUE_CLAIM_LEVELS or level not in RESCUE_CLAIM_LEVELS[scheme]:
            raise ValueError(f"{pr_id} has invalid versioned claim level: {claim_level}")
        if card.get("scientific_status_on_intake") != "OPEN":
            raise ValueError(f"{pr_id} scientific status must remain OPEN on intake")
        expected_activation = (
            "DORMANT_EXTERNAL" if int(pr_id[-3:]) >= 159 else "PENDING"
        )
        if card.get("activation_state") != expected_activation:
            raise ValueError(
                f"{pr_id} activation_state must remain {expected_activation}, "
                f"found {card.get('activation_state')!r}"
            )
        for field in RESCUE_SEMANTIC_CLAIM_FIELDS:
            if field not in card:
                raise ValueError(f"{pr_id} missing semantic claim field: {field}")
            for prose in _iter_strings(card[field]):
                match = BARE_ACTIVE_CLAIM_LEVEL_RE.search(prose)
                if match:
                    raise ValueError(
                        f"{pr_id} {field} contains unqualified roadmap claim level "
                        f"{match.group(0)!r}"
                    )

    terminal_receipt_cards = {
        pr_id
        for pr_id in expected_ids
        if any(
            contract["mode"] == "requires_terminal_receipt"
            for contract in cards[pr_id]["dependency_contracts"]
        )
    }
    if terminal_receipt_cards != {"PR-157"}:
        raise ValueError(
            "requires_terminal_receipt is aggregation-only and restricted to PR-157; "
            f"found {sorted(terminal_receipt_cards)}"
        )
    adjudicated_cards = {
        pr_id
        for pr_id in expected_ids
        if any(
            contract["mode"] == "requires_adjudicated_claim_set"
            for contract in cards[pr_id]["dependency_contracts"]
        )
    }
    if adjudicated_cards != {"PR-158", "PR-166"}:
        raise ValueError(
            "adjudicated-claim edges must be restricted to PR-158 and PR-166; "
            f"found {sorted(adjudicated_cards)}"
        )
    external = cards["PR-159"].get("external_dependency_contracts")
    if external != [
        {
            "upstream_id": "AUTHENTICATED_NATIVE_DELIVERY",
            "mode": "requires_authenticated_external_receipt",
            "scope": "native_low_ell_delivery",
        }
    ]:
        raise ValueError(
            "PR-159 must retain the authenticated native-delivery gate with exact "
            "native_low_ell_delivery scope"
        )

    pr150_constraint = cards["PR-150"].get("execution_constraints")
    if pr150_constraint != PR150_EXECUTION_CONSTRAINT:
        raise ValueError("PR-150 must preserve the explicit PR3-complete/PR4-skip constraint")
    for field, expected in PR150_SEMANTIC_CONTRACT.items():
        if cards["PR-150"].get(field) != expected:
            raise ValueError(
                "PR-150 must unconditionally forbid all PR4/NPIPE download, reduction, "
                "analysis, and numeric/figure/combined outputs; canonical semantic "
                f"field drifted: {field}"
            )
    if cards["PR-150"].get("claim_level") != {
        "scheme": "roadmap_rescue_v1",
        "level": "C2",
    }:
        raise ValueError("PR-150 cannot retain the original joint PR3+PR4 C3 ceiling")

    if actual_advocate_ids:
        for pr_id in _pr_range(ADVOCATE_FIRST_PR, ADVOCATE_LAST_PR):
            card = cards[pr_id]
            missing_fields = sorted(ADVOCATE_REQUIRED_FIELDS - set(card))
            if missing_fields:
                raise ValueError(f"{pr_id} missing advocate-card fields: {missing_fields}")
            expected_depends, expected_lane, expected_activation = ADVOCATE_CARD_CONTRACTS[pr_id]
            if card.get("depends") != expected_depends:
                raise ValueError(
                    f"{pr_id} dependencies drifted: {card.get('depends')!r} != {expected_depends!r}"
                )
            contracts = card.get("dependency_contracts")
            if not isinstance(contracts, list) or [
                contract.get("upstream_id") for contract in contracts if isinstance(contract, dict)
            ] != expected_depends:
                raise ValueError(f"{pr_id} typed dependency projection drifted")
            terminal_receipt_edges = {
                ("PR-178", "PR-151"),
                # PR-184 replan (2026-07-21): the failed PR-172 edge is
                # consumed as a terminal receipt; success flows through
                # the PR-184 remediation card instead.
                ("PR-180", "PR-172"),
                ("PR-184", "PR-172"),
            }
            expected_modes = [
                "requires_terminal_receipt"
                if (pr_id, dep) in terminal_receipt_edges
                else "requires_success"
                for dep in expected_depends
            ]
            actual_modes = [
                contract.get("mode") for contract in contracts if isinstance(contract, dict)
            ]
            if actual_modes != expected_modes:
                raise ValueError(f"{pr_id} typed dependency modes drifted")
            if card.get("execution_lane") != expected_lane:
                raise ValueError(f"{pr_id} execution_lane must be {expected_lane}")
            if card.get("activation_state") != expected_activation:
                raise ValueError(f"{pr_id} activation_state must be {expected_activation}")
            expected_artifact_mode = (
                "hypothesis_only"
                if pr_id in ADVOCATE_HYPOTHESIS_ONLY_ARTIFACTS
                else "standard_internal"
            )
            if card.get("scientific_artifact_mode") != expected_artifact_mode:
                raise ValueError(
                    f"{pr_id} scientific_artifact_mode must be {expected_artifact_mode}"
                )
            if pr_id in ADVOCATE_REGISTERED_NOT_SCHEDULED:
                expected_authorization = "REGISTERED_NOT_SCHEDULED"
            elif pr_id == "PR-183":
                expected_authorization = "NATIVE_BLOCKED"
            elif pr_id in ADVOCATE_EXPLICIT_APPROVED_SEQUENCE:
                expected_authorization = "EXPLICIT_APPROVED_SEQUENCE"
            else:
                expected_authorization = "DAG_SCHEDULABLE"
            if card.get("execution_authorization") != expected_authorization:
                raise ValueError(
                    f"{pr_id} execution_authorization must be {expected_authorization}"
                )
            if pr_id in ADVOCATE_TITLE_OVERRIDES and card.get("title") != ADVOCATE_TITLE_OVERRIDES[pr_id]:
                raise ValueError(f"{pr_id} claim-safe title override drifted")
            if card.get("public_use") is not False or card.get("spec_first_required") is not True:
                raise ValueError(f"{pr_id} must remain spec-first and public_use=false on intake")
            if expected_lane not in ADVOCATE_EXECUTION_LANES:
                raise ValueError(f"{pr_id} has unknown execution lane")
            if expected_activation not in ADVOCATE_ACTIVATION_STATES:
                raise ValueError(f"{pr_id} has unknown activation state")
            for field in RESCUE_SEMANTIC_CLAIM_FIELDS:
                for prose in _iter_strings(card.get(field)):
                    match = BARE_ACTIVE_CLAIM_LEVEL_RE.search(prose)
                    if match:
                        raise ValueError(
                            f"{pr_id} {field} contains unqualified roadmap claim level {match.group(0)!r}"
                        )

        for pr_id in ("PR-168", "PR-169", "PR-170", "PR-171", "PR-175", "PR-182"):
            cas = cards[pr_id].get("cas_contract")
            if cas != {
                "schema": "htt.cas_contract.v2",
                "required_axes": [
                    "wolfram_xact",
                    "sympy_high_precision",
                    "sage_singular",
                    "lean_mathlib",
                ],
                "missing_axis_outcome": "CAS_BLOCKED",
                "result_blinding": "required_until_adjudication",
            }:
                raise ValueError(f"{pr_id} must preregister the blind four-axis CAS contract")
            theory_prose = " ".join(_iter_strings(cards[pr_id])).lower()
            if any(
                weak in theory_prose
                for weak in ("dual-engine", "two-engine", "two engine", "두 engine")
            ):
                raise ValueError(
                    f"{pr_id} exact-math acceptance prose collapses the four-axis contract"
                )

        if "every canonical PR-000--166 card (expected count 113)" not in " ".join(
            _iter_strings(cards["PR-167"])
        ):
            raise ValueError("PR-167 must preserve the exact 113-card pre-intake prefix")

        required_claim_phrases = {
            "PR-173": "numerically unresolved at the current Monte Carlo budget",
            "PR-176": "structurally distinct from monopole leakage",
            "PR-177": "ACT-release-simulation-conditional modulation candidate or null",
            "PR-179": "Selection/systematics-conditional raw-catalogue directional statistic",
            "PR-180": "consistency result",
        }
        for pr_id, phrase in required_claim_phrases.items():
            if phrase.lower() not in " ".join(_iter_strings(cards[pr_id])).lower():
                raise ValueError(f"{pr_id} is missing its required downclaim phrase: {phrase}")

        external = cards["PR-183"].get("external_dependency_contracts")
        if external != [
            {
                "upstream_id": "AUTHENTICATED_NATIVE_DELIVERY",
                "mode": "requires_authenticated_external_receipt",
                "scope": "native_low_ell_delivery",
            }
        ]:
            raise ValueError("PR-183 must retain the typed authenticated native-delivery gate")

    if actual_strengthen_ids:
        _validate_strengthen_slice(cards)

    if actual_revival_ids:
        _validate_revival_slice(cards)

    if actual_process_ids:
        _validate_process_integrity_slice(cards)

    if actual_foundation_ids:
        _validate_foundation_slice(cards)
    if actual_premise_anchor_ids:
        _validate_premise_anchor_slice(cards)
        validate_premise_anchor_intake(load_yaml(PREMISE_ANCHOR_INTAKE))
        check_mirrors()
    if actual_vector_tensor_ids:
        _validate_vector_tensor_slice(cards, actual_vector_tensor_ids)
    if actual_post275_ids:
        _validate_post275_slice(cards)
    if actual_pr280_root_cause_ids:
        _validate_pr280_root_cause_slice(cards)

    if status is not None:
        _validate_rescue_status(status, info)


def _validate_revival_slice(cards: dict[str, Any]) -> None:
    """Validate the atomic legacy-revival round-2 intake (PR-209..246).

    Track I (PR-209..228) is solver-independent and DAG_SCHEDULABLE; Track II
    (PR-229..242) and Integration (PR-243..246) are native-blocked. Dependency
    edges are pinned from REVIVAL_DEPENDS; lane/activation/authorization/
    solver_gate are derived from the track so card and validator cannot drift.
    The track boundary is enforced one-directional: no Track-I card may depend
    on a Track-II/Integration card.
    """
    for pr_id in _pr_range(REVIVAL_FIRST_PR, REVIVAL_LAST_PR):
        card = cards[pr_id]
        missing_fields = sorted((ADVOCATE_REQUIRED_FIELDS | {"track", "solver_gate_required"}) - set(card))
        if missing_fields:
            raise ValueError(f"{pr_id} missing revival-card fields: {missing_fields}")
        expected_depends = REVIVAL_DEPENDS[pr_id]
        if card.get("depends") != expected_depends:
            raise ValueError(
                f"{pr_id} dependencies drifted: {card.get('depends')!r} != {expected_depends!r}"
            )
        contracts = card.get("dependency_contracts")
        if not isinstance(contracts, list) or [
            contract.get("upstream_id") for contract in contracts if isinstance(contract, dict)
        ] != expected_depends:
            raise ValueError(f"{pr_id} typed dependency projection drifted")
        expected_modes = [
            "requires_terminal_receipt" if (pr_id, dep) in REVIVAL_TERMINAL_RECEIPT_EDGES
            else "requires_success"
            for dep in expected_depends
        ]
        actual_modes = [c.get("mode") for c in contracts if isinstance(c, dict)]
        if actual_modes != expected_modes:
            raise ValueError(f"{pr_id} typed dependency modes drifted")
        lane, activation, authz, track, gate = _revival_expected(pr_id)
        if card.get("track") != track:
            raise ValueError(f"{pr_id} track must be {track}")
        if card.get("execution_lane") != lane:
            raise ValueError(f"{pr_id} execution_lane must be {lane}")
        if card.get("activation_state") != activation:
            raise ValueError(f"{pr_id} activation_state must be {activation}")
        if card.get("execution_authorization") != authz:
            raise ValueError(f"{pr_id} execution_authorization must be {authz}")
        if card.get("solver_gate_required") is not gate:
            raise ValueError(f"{pr_id} solver_gate_required must be {gate}")
        if card.get("scientific_status_on_intake") != "OPEN":
            raise ValueError(f"{pr_id} scientific status must remain OPEN on intake")
        if card.get("scientific_artifact_mode") != "standard_internal":
            raise ValueError(f"{pr_id} scientific_artifact_mode must be standard_internal")
        if card.get("public_use") is not False or card.get("spec_first_required") is not True:
            raise ValueError(f"{pr_id} must remain spec-first and public_use=false on intake")
        # one-directional track boundary: Track-I never depends on Track-II/Integration
        if track == "I":
            for dep in expected_depends:
                if dep in REVIVAL_TRACK_II or dep in REVIVAL_INTEGRATION:
                    raise ValueError(
                        f"{pr_id} (Track I) has an illegal dependency on native card {dep}"
                    )
        # CAS cards carry the five-axis v3 contract
        if pr_id in REVIVAL_CAS_CARDS:
            cas = card.get("cas_contract") or {}
            if cas.get("required_axes") != [
                "wolfram_xact", "sympy_high_precision", "sage_singular",
                "lean_mathlib", "rocq_stdlib",
            ]:
                raise ValueError(f"{pr_id} must carry the five-axis CAS v3 contract")


def _validate_process_integrity_slice(cards: dict[str, Any]) -> None:
    """Validate non-scientific process cards added after the frozen roadmap."""

    for pr_id, expected in PROCESS_INTEGRITY_CARD_CONTRACTS.items():
        card = cards[pr_id]
        if card.get("depends") != expected["depends"]:
            raise ValueError(f"{pr_id} process-integrity dependencies drifted")
        contracts = card.get("dependency_contracts")
        expected_contracts = [
            {"upstream_id": dep, "mode": "requires_success"}
            for dep in expected["depends"]
        ]
        if not isinstance(contracts, list) or contracts != expected_contracts:
            raise ValueError(f"{pr_id} typed dependency projection drifted")
        for field in (
            "change_set_id",
            "publication_group_id",
            "execution_lane",
            "activation_state",
            "execution_authorization",
        ):
            if card.get(field) != expected[field]:
                raise ValueError(
                    f"{pr_id} {field} drifted: "
                    f"{card.get(field)!r} != {expected[field]!r}"
                )
        if card.get("owner") != "COMMON":
            raise ValueError(f"{pr_id} process-integrity owner must be COMMON")
        if card.get("implementation_scopes") != ["common"]:
            raise ValueError(f"{pr_id} implementation scope must be common")
        if card.get("claim_level") != {
            "scheme": "not_applicable_governance_v1",
            "level": "NOT_APPLICABLE",
        }:
            raise ValueError(f"{pr_id} must carry the non-scientific claim level")
        if card.get("claim_tier_ceiling") != "diagnostic_only":
            raise ValueError(f"{pr_id} claim tier must remain diagnostic_only")
        if card.get("scientific_artifact_mode") != "governance_diagnostic":
            raise ValueError(
                f"{pr_id} scientific_artifact_mode must be governance_diagnostic"
            )
        if card.get("scientific_status_on_intake") != "OPEN":
            raise ValueError(f"{pr_id} scientific status must remain OPEN")
        if (
            card.get("public_use") is not False
            or card.get("spec_first_required") is not True
            or card.get("solver_gate_required") is not False
            or card.get("track") != "PROCESS"
        ):
            raise ValueError(
                f"{pr_id} must remain internal, spec-first, solver-independent PROCESS work"
            )


def _validate_foundation_slice(cards: dict[str, Any]) -> None:
    """Validate the atomic, claim-limited PR-248..252 foundation intake."""

    for pr_id, expected in FOUNDATION_CARD_CONTRACTS.items():
        card = cards[pr_id]
        missing_fields = sorted(
            (ADVOCATE_REQUIRED_FIELDS | {"track", "solver_gate_required"})
            - set(card)
        )
        if missing_fields:
            raise ValueError(
                f"{pr_id} missing statistical-foundation fields: {missing_fields}"
            )
        if card.get("depends") != expected["depends"]:
            raise ValueError(
                f"{pr_id} dependencies drifted: "
                f"{card.get('depends')!r} != {expected['depends']!r}"
            )
        contracts = card.get("dependency_contracts")
        expected_contracts = [
            {
                "upstream_id": dep,
                "mode": (
                    "requires_terminal_receipt"
                    if pr_id == "PR-248" and dep == "PR-168"
                    else "requires_success"
                ),
            }
            for dep in expected["depends"]
        ]
        if not isinstance(contracts, list) or contracts != expected_contracts:
            raise ValueError(f"{pr_id} typed dependency projection drifted")
        for field in ("owner", "change_set_id", "publication_group_id"):
            if card.get(field) != expected[field]:
                raise ValueError(
                    f"{pr_id} {field} drifted: "
                    f"{card.get(field)!r} != {expected[field]!r}"
                )
        if (
            card.get("execution_lane") != "defensible"
            or card.get("activation_state") != "PENDING"
            or card.get("execution_authorization") != "EXPLICIT_USER_AUTHORIZED"
        ):
            raise ValueError(f"{pr_id} execution-state contract drifted")
        if (
            card.get("scientific_status_on_intake") != "OPEN"
            or card.get("public_use") is not False
            or card.get("spec_first_required") is not True
            or card.get("solver_gate_required") is not False
            or card.get("track") != "FOUNDATION"
        ):
            raise ValueError(
                f"{pr_id} must remain internal, OPEN, spec-first FOUNDATION work"
            )
        if card.get("claim_level") not in (
            {"scheme": "roadmap_rescue_v1", "level": "C1"},
            {"scheme": "roadmap_rescue_v1", "level": "C2"},
        ):
            raise ValueError(f"{pr_id} has an invalid claim-limited foundation level")
        if card.get("claim_tier_ceiling") not in {"conditional", "diagnostic_only"}:
            raise ValueError(f"{pr_id} has an invalid foundation claim ceiling")
        for field in RESCUE_SEMANTIC_CLAIM_FIELDS:
            for prose in _iter_strings(card.get(field)):
                match = BARE_ACTIVE_CLAIM_LEVEL_RE.search(prose)
                if match:
                    raise ValueError(
                        f"{pr_id} {field} contains unqualified roadmap claim level "
                        f"{match.group(0)!r}"
                    )


def _validate_premise_anchor_slice(cards: dict[str, Any]) -> None:
    """Validate the atomic, claim-limited PR-253..258 methodology intake."""

    for pr_id, expected in PREMISE_ANCHOR_CARD_CONTRACTS.items():
        card = cards[pr_id]
        missing_fields = sorted(
            (ADVOCATE_REQUIRED_FIELDS | {"track", "solver_gate_required"})
            - set(card)
        )
        if missing_fields:
            raise ValueError(
                f"{pr_id} missing premise-anchor fields: {missing_fields}"
            )
        if card.get("depends") != expected["depends"]:
            raise ValueError(
                f"{pr_id} dependencies drifted: "
                f"{card.get('depends')!r} != {expected['depends']!r}"
            )
        expected_contracts = [
            {"upstream_id": dep, "mode": "requires_success"}
            for dep in expected["depends"]
        ]
        if card.get("dependency_contracts") != expected_contracts:
            raise ValueError(f"{pr_id} typed dependency projection drifted")
        for field in (
            "owner",
            "change_set_id",
            "publication_group_id",
            "forbidden",
            "anti_drift",
        ):
            if card.get(field) != expected[field]:
                raise ValueError(
                    f"{pr_id} {field} drifted: "
                    f"{card.get(field)!r} != {expected[field]!r}"
                )
        if "claim_contracts" in expected and card.get("claim_contracts") != expected[
            "claim_contracts"
        ]:
            raise ValueError(f"{pr_id} conjecture claim contracts drifted")
        if (
            card.get("execution_lane") != "defensible"
            or card.get("activation_state") != "PENDING"
            or card.get("execution_authorization") != "EXPLICIT_USER_AUTHORIZED"
        ):
            raise ValueError(f"{pr_id} execution-state contract drifted")
        if (
            card.get("scientific_status_on_intake") != "OPEN"
            or card.get("public_use") is not False
            or card.get("spec_first_required") is not True
            or card.get("solver_gate_required") is not False
            or card.get("track") != "FOUNDATION"
        ):
            raise ValueError(
                f"{pr_id} must remain internal, OPEN, spec-first FOUNDATION work"
            )
        if card.get("claim_level") not in (
            {"scheme": "roadmap_rescue_v1", "level": "C1"},
            {"scheme": "roadmap_rescue_v1", "level": "C2"},
        ):
            raise ValueError(f"{pr_id} has an invalid premise-anchor claim level")
        if card.get("claim_tier_ceiling") not in {
            "conditional",
            "diagnostic_only",
        }:
            raise ValueError(f"{pr_id} has an invalid premise-anchor claim ceiling")
        semantic_bytes = json.dumps(
            card,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        if (
            hashlib.sha256(semantic_bytes).hexdigest()
            != PREMISE_ANCHOR_CARD_SEMANTIC_SHA256[pr_id]
        ):
            raise ValueError(f"{pr_id} semantic card identity drifted")
        for field in RESCUE_SEMANTIC_CLAIM_FIELDS:
            for prose in _iter_strings(card.get(field)):
                match = BARE_ACTIVE_CLAIM_LEVEL_RE.search(prose)
                if match:
                    raise ValueError(
                        f"{pr_id} {field} contains unqualified roadmap claim level "
                        f"{match.group(0)!r}"
                    )


def _validate_vector_tensor_slice(
    cards: dict[str, Any], present_ids: set[str]
) -> None:
    """Validate bootstrap or full PR-259..275 vector/tensor programme intake."""

    for pr_id in sorted(present_ids, key=lambda value: int(value.split("-")[1])):
        card = cards[pr_id]
        expected = VECTOR_TENSOR_CARD_CONTRACTS[pr_id]
        missing_fields = sorted(VECTOR_TENSOR_REQUIRED_FIELDS - set(card))
        if missing_fields:
            raise ValueError(
                f"{pr_id} missing vector/tensor programme fields: {missing_fields}"
            )
        if card.get("depends") != expected["depends"]:
            raise ValueError(
                f"{pr_id} vector/tensor dependencies drifted: "
                f"{card.get('depends')!r} != {expected['depends']!r}"
            )
        expected_contracts = [
            {"upstream_id": dependency, "mode": "requires_success"}
            for dependency in expected["depends"]
        ]
        if card.get("dependency_contracts") != expected_contracts:
            raise ValueError(
                f"{pr_id} vector/tensor dependency contracts drifted"
            )
        if card.get("owner") != expected["owner"]:
            raise ValueError(
                f"{pr_id} vector/tensor owner drifted: "
                f"{card.get('owner')!r} != {expected['owner']!r}"
            )
        for field in ("capability", "inputs", "outputs", "tests", "forbidden"):
            value = card.get(field)
            if field == "capability":
                _require_nonempty_string(value, f"{pr_id}.{field}")
            else:
                _require_string_list(card, field)
        _require_nonempty_string(card.get("kill"), f"{pr_id}.kill")
        if (
            card.get("execution_lane") != "defensible"
            or card.get("activation_state") != "PENDING"
            or card.get("execution_authorization")
            != "EXPLICIT_USER_AUTHORIZED"
        ):
            raise ValueError(f"{pr_id} vector/tensor execution state drifted")
        if (
            card.get("scientific_status_on_intake") != "OPEN"
            or card.get("public_use") is not False
            or card.get("solver_gate_required") is not False
            or card.get("claim_tier_ceiling") != "diagnostic_only"
        ):
            raise ValueError(
                f"{pr_id} must remain internal, OPEN, solver-independent, "
                "and diagnostic-only"
            )
        expected_track = (
            "FOUNDATION" if pr_id in VECTOR_TENSOR_BOOTSTRAP_IDS
            else "VECTOR_TENSOR"
        )
        if card.get("track") != expected_track:
            raise ValueError(f"{pr_id} track must be {expected_track}")
        if pr_id != "PR-259" and card.get("spec_first_required") is not True:
            raise ValueError(f"{pr_id} must remain spec-first")
        forbidden_text = " ".join(_iter_strings(card.get("forbidden"))).lower()
        for boundary in ("native", "family-identification"):
            if boundary not in forbidden_text:
                raise ValueError(
                    f"{pr_id} forbidden actions omit the {boundary} boundary"
                )


def _validate_post275_slice(cards: dict[str, Any]) -> None:
    """Validate the atomic PR-276..294 post-275 execution programme."""

    spec_path = (
        Path(__file__).resolve().parents[2]
        / "docs/research_program/post_pr275/pr276_spec.yaml"
    )
    spec = load_yaml(spec_path)
    if spec.get("schema") != "htt.post_pr275.reconciliation.v1":
        raise ValueError("PR-276 reconciliation spec schema drifted")
    if spec.get("status") != "REGISTERED":
        raise ValueError("PR-276 reconciliation spec must be REGISTERED")
    gate_rows = spec.get("defined_scientific_gates")
    if not isinstance(gate_rows, list) or [row.get("gate_id") for row in gate_rows] != [
        f"G{index}" for index in range(1, 9)
    ]:
        raise ValueError("PR-276 must register exactly the defined G1..G8 gates")
    if spec.get("undefined_gate_ids_forbidden") != ["G9", "G10", "G11", "G12"]:
        raise ValueError("PR-276 undefined-gate correction drifted")
    if spec.get("scope", {}).get("prospective_pr_ids") != _pr_range(276, 294):
        raise ValueError("PR-276 prospective ID inventory drifted")
    if spec.get("scope", {}).get("pr280_root_cause_successor_ids") != [
        "PR-295",
        "PR-296",
        "PR-297",
    ]:
        raise ValueError("PR-280 root-cause successor inventory drifted")
    if spec.get("scope", {}).get(
        "current_registered_total_after_pr280_root_cause_intake"
    ) != 244:
        raise ValueError("PR-280 root-cause card count drifted")

    for pr_id in _pr_range(276, 294):
        card = cards[pr_id]
        expected = POST275_CARD_CONTRACTS[pr_id]
        missing_fields = sorted(POST275_REQUIRED_FIELDS - set(card))
        if missing_fields:
            raise ValueError(
                f"{pr_id} missing post-275 programme fields: {missing_fields}"
            )
        expected_contracts = [
            {"upstream_id": upstream_id, "mode": mode}
            for upstream_id, mode in expected["dependencies"]
        ]
        if card.get("depends") != [row["upstream_id"] for row in expected_contracts]:
            raise ValueError(f"{pr_id} post-275 dependencies drifted")
        if card.get("dependency_contracts") != expected_contracts:
            raise ValueError(f"{pr_id} post-275 dependency modes drifted")
        if card.get("owner") != expected["owner"]:
            raise ValueError(f"{pr_id} post-275 owner drifted")
        if card.get("execution_authorization") != expected["authorization"]:
            raise ValueError(f"{pr_id} execution authorization drifted")
        for field in ("capability", "kill", "change_set_id", "publication_group_id"):
            _require_nonempty_string(card.get(field), f"{pr_id}.{field}")
        for field in (
            "inputs",
            "outputs",
            "contributors",
            "implementation_scopes",
            "targets",
            "files",
            "tests",
            "dod",
            "forbidden",
            "anti_drift",
        ):
            _require_string_list(card, field)
        if (
            card.get("activation_state") != "PENDING"
            or card.get("execution_lane") != "defensible"
            or card.get("scientific_status_on_intake") != "OPEN"
            or card.get("public_use") is not False
            or card.get("spec_first_required") is not True
            or card.get("solver_gate_required") is not False
            or card.get("claim_tier_ceiling") != "diagnostic_only"
        ):
            raise ValueError(
                f"{pr_id} must remain PENDING, internal, OPEN, spec-first, "
                "solver-independent, and diagnostic-only"
            )
        forbidden_text = " ".join(_iter_strings(card.get("forbidden"))).lower()
        for boundary in ("native", "family-identification"):
            if boundary not in forbidden_text:
                raise ValueError(
                    f"{pr_id} forbidden actions omit the {boundary} boundary"
                )

    for pr_id, (gate_id, scope) in POST275_HUMAN_GATES.items():
        if cards[pr_id].get("external_execution_gates") != [
            {
                "gate_id": gate_id,
                "mode": "requires_human_execution_authorization",
                "scope": scope,
            }
        ]:
            raise ValueError(f"{pr_id} lane-specific human gate drifted")
    if cards["PR-280"].get("external_execution_gates") != [
        {
            "gate_id": "G-CI-H",
            "mode": "requires_human_ruleset_change_authorization",
            "scope": "github_ruleset_mutation_only",
        }
    ]:
        raise ValueError("PR-280 GitHub-ruleset human gate drifted")

    if cards["PR-276"].get("claim_level") != {
        "scheme": "not_applicable_governance_v1",
        "level": "NOT_APPLICABLE",
    }:
        raise ValueError("PR-276 must remain non-scientific governance work")
    if cards["PR-277"].get("claim_level") != cards["PR-276"].get("claim_level"):
        raise ValueError("PR-277 capability bookkeeping must remain non-scientific")
    if cards["PR-278"].get("claim_level") != cards["PR-276"].get("claim_level"):
        raise ValueError("PR-278 adjudication bookkeeping must remain non-scientific")
    if cards["PR-279"].get("claim_level") != cards["PR-276"].get("claim_level"):
        raise ValueError("PR-279 reverse trace must remain non-scientific")
    if cards["PR-280"].get("claim_level") != cards["PR-276"].get("claim_level"):
        raise ValueError("PR-280 harness evidence must remain non-scientific")

    # The negative PR-190 result is terminal evidence, not a success.  PR-276
    # may consume it, while the two historical success-only consumers stay
    # closed until an explicit versioned supersession.
    for downstream in ("PR-191", "PR-205"):
        contracts = cards[downstream].get("dependency_contracts") or []
        matching = [
            row
            for row in contracts
            if isinstance(row, dict) and row.get("upstream_id") == "PR-190"
        ]
        if matching != [{"upstream_id": "PR-190", "mode": "requires_success"}]:
            raise ValueError(f"{downstream} must retain its closed PR-190 success edge")


def _validate_pr280_root_cause_slice(cards: dict[str, Any]) -> None:
    """Validate the exact one-failure-type PR-295..297 interruption slice."""

    spec_path = (
        Path(__file__).resolve().parents[2]
        / "docs/research_program/post_pr275/pr276_spec.yaml"
    )
    amendment = load_yaml(spec_path).get("pr280_root_cause_amendment")
    if not isinstance(amendment, dict):
        raise ValueError("PR-280 root-cause amendment is missing")
    if amendment.get("historical_prospective_scope_unchanged") != "PR-276..PR-294":
        raise ValueError("PR-276 historical prospective scope was rewritten")
    if amendment.get("direct_consumers") != sorted(PR280_DIRECT_CONSUMERS):
        raise ValueError("PR-280 direct-consumer stop set drifted")
    if amendment.get("required_successors_for_each_direct_consumer") != [
        "PR-295",
        "PR-296",
        "PR-297",
    ]:
        raise ValueError("PR-280 root-cause success set drifted")
    successor_specs = amendment.get("successors")
    successor_dependencies = amendment.get("successor_dependencies")
    if not isinstance(successor_specs, dict) or not isinstance(
        successor_dependencies, dict
    ):
        raise ValueError("PR-280 successor spec or dependencies are malformed")

    seen_failure_nodes: set[str] = set()
    for pr_id, expected in PR280_ROOT_CAUSE_CARD_CONTRACTS.items():
        card = cards[pr_id]
        missing_fields = sorted(POST275_REQUIRED_FIELDS - set(card))
        if missing_fields:
            raise ValueError(
                f"{pr_id} missing PR-280 root-cause fields: {missing_fields}"
            )
        expected_contracts = [
            {"upstream_id": "PR-280", "mode": "requires_terminal_receipt"}
        ]
        if card.get("depends") != ["PR-280"]:
            raise ValueError(f"{pr_id} must depend only on terminal PR-280")
        if card.get("dependency_contracts") != expected_contracts:
            raise ValueError(f"{pr_id} terminal-receipt dependency drifted")
        if successor_dependencies.get(pr_id) != expected_contracts:
            raise ValueError(f"{pr_id} successor dependency spec drifted")
        if card.get("owner") != expected["owner"]:
            raise ValueError(f"{pr_id} root-cause owner drifted")
        if card.get("capability") != expected["capability"]:
            raise ValueError(f"{pr_id} root-cause capability drifted")
        if card.get("claim_level") != expected["claim_level"]:
            raise ValueError(f"{pr_id} root-cause claim level drifted")
        failure_node = expected["failure_node"]
        if failure_node in seen_failure_nodes:
            raise ValueError("one active-core failure maps to multiple successors")
        seen_failure_nodes.add(failure_node)
        spec_row = successor_specs.get(pr_id)
        if not isinstance(spec_row, dict) or spec_row.get("failure_node") != failure_node:
            raise ValueError(f"{pr_id} exact failure-node binding drifted")
        if failure_node not in " ".join(_iter_strings(card.get("inputs"))):
            raise ValueError(f"{pr_id} input omits its exact active-core node")
        for field in (
            "inputs",
            "outputs",
            "contributors",
            "implementation_scopes",
            "targets",
            "files",
            "tests",
            "dod",
            "forbidden",
            "anti_drift",
        ):
            _require_string_list(card, field)
        for field in ("kill", "change_set_id", "publication_group_id"):
            _require_nonempty_string(card.get(field), f"{pr_id}.{field}")
        if (
            card.get("activation_state") != "PENDING"
            or card.get("execution_lane") != "defensible"
            or card.get("execution_authorization") != "REGISTERED_NOT_SCHEDULED"
            or card.get("scientific_status_on_intake") != "OPEN"
            or card.get("public_use") is not False
            or card.get("spec_first_required") is not True
            or card.get("solver_gate_required") is not False
            or card.get("claim_tier_ceiling") != "diagnostic_only"
            or card.get("track") != "POST275_ROOT_CAUSE"
        ):
            raise ValueError(f"{pr_id} root-cause intake boundaries drifted")
        forbidden_text = " ".join(_iter_strings(card.get("forbidden"))).lower()
        for boundary in ("native", "family-identification"):
            if boundary not in forbidden_text:
                raise ValueError(f"{pr_id} omits the {boundary} boundary")


def _validate_strengthen_slice(cards: dict[str, Any]) -> None:
    """Validate the atomic post-v10 strengthening intake (PR-185..208).

    External novelty and internal readiness are independent axes: every card
    entered OPEN / spec-first / public_use=false with an exploratory internal
    ceiling, regardless of its external novelty. PR-190 is the explicit
    post-275 execution amendment and carries a theorem-candidate ceiling
    without granting theorem capability. Typed dependency edges,
    lanes, activation and authorization are pinned from
    STRENGTHEN_CARD_CONTRACTS so card and validator cannot drift.
    """

    for pr_id in _pr_range(STRENGTHEN_FIRST_PR, STRENGTHEN_LAST_PR):
        card = cards[pr_id]
        missing_fields = sorted(ADVOCATE_REQUIRED_FIELDS - set(card))
        if missing_fields:
            raise ValueError(f"{pr_id} missing strengthen-card fields: {missing_fields}")
        expected_depends, expected_lane, expected_activation, expected_authz = (
            STRENGTHEN_CARD_CONTRACTS[pr_id]
        )
        if card.get("depends") != expected_depends:
            raise ValueError(
                f"{pr_id} dependencies drifted: {card.get('depends')!r} != {expected_depends!r}"
            )
        contracts = card.get("dependency_contracts")
        if not isinstance(contracts, list) or [
            contract.get("upstream_id") for contract in contracts if isinstance(contract, dict)
        ] != expected_depends:
            raise ValueError(f"{pr_id} typed dependency projection drifted")
        expected_modes = []
        for dep in expected_depends:
            if (pr_id, dep) in STRENGTHEN_TERMINAL_RECEIPT_EDGES:
                expected_modes.append("requires_terminal_receipt")
            elif (pr_id, dep) in STRENGTHEN_ADJUDICATED_EDGES:
                expected_modes.append("requires_adjudicated_claim_set")
            else:
                expected_modes.append("requires_success")
        actual_modes = [
            contract.get("mode") for contract in contracts if isinstance(contract, dict)
        ]
        if actual_modes != expected_modes:
            raise ValueError(f"{pr_id} typed dependency modes drifted")
        if card.get("execution_lane") != expected_lane:
            raise ValueError(f"{pr_id} execution_lane must be {expected_lane}")
        if card.get("activation_state") != expected_activation:
            raise ValueError(f"{pr_id} activation_state must be {expected_activation}")
        if card.get("execution_authorization") != expected_authz:
            raise ValueError(f"{pr_id} execution_authorization must be {expected_authz}")
        if card.get("scientific_status_on_intake") != "OPEN":
            raise ValueError(f"{pr_id} scientific status must remain OPEN on intake")
        if card.get("scientific_artifact_mode") != "standard_internal":
            raise ValueError(f"{pr_id} scientific_artifact_mode must be standard_internal")
        if card.get("public_use") is not False or card.get("spec_first_required") is not True:
            raise ValueError(f"{pr_id} must remain spec-first and public_use=false on intake")
        expected_ceiling = "theorem_candidate" if pr_id == "PR-190" else "exploratory"
        if card.get("claim_tier_ceiling") != expected_ceiling:
            raise ValueError(
                f"{pr_id} claim ceiling must be {expected_ceiling} (readiness axis)"
            )
        claim_level = card.get("claim_level")
        if claim_level != {"scheme": "roadmap_rescue_v1", "level": "C1"}:
            raise ValueError(f"{pr_id} intake claim level must be roadmap_rescue_v1:C1")
        owner = card.get("owner")
        if owner in RESCUE_FORBIDDEN_OWNERS or owner not in RESCUE_ACTIVE_OWNERS:
            raise ValueError(f"{pr_id} has forbidden or unknown active owner: {owner!r}")
        for field in RESCUE_SEMANTIC_CLAIM_FIELDS:
            for prose in _iter_strings(card.get(field)):
                match = BARE_ACTIVE_CLAIM_LEVEL_RE.search(prose)
                if match:
                    raise ValueError(
                        f"{pr_id} {field} contains unqualified roadmap claim level "
                        f"{match.group(0)!r}"
                    )
        if pr_id in STRENGTHEN_CAS_CARDS:
            cas = card.get("cas_contract")
            if pr_id == "PR-190":
                if cas != {
                    "schema": "htt.cas_contract.v3",
                    "required_axes": [
                        "wolfram_xact",
                        "sympy",
                        "sage_singular",
                        "lean",
                    ],
                    "optional_non_gating_axes": ["rocq"],
                    "missing_axis_outcome": "CAS_BLOCKED",
                    "result_blinding": "required_until_adjudication",
                }:
                    raise ValueError(
                        "PR-190 must use the canonical blind four-axis contract; "
                        "Rocq is optional and non-gating"
                    )
                continue
            # v3 (policy repair ADJ-CAS-ROCQ-AXIS-001): Rocq (Coq) joins Lean as
            # a second kernel-independent proof-assistant lineage -> a five-axis
            # blind CAS contract.
            if cas != {
                "schema": "htt.cas_contract.v3",
                "required_axes": [
                    "wolfram_xact",
                    "sympy_high_precision",
                    "sage_singular",
                    "lean_mathlib",
                    "rocq_stdlib",
                ],
                "missing_axis_outcome": "CAS_BLOCKED",
                "result_blinding": "required_until_adjudication",
            }:
                raise ValueError(f"{pr_id} must preregister the blind five-axis CAS contract")
            theory_prose = " ".join(_iter_strings(card)).lower()
            if any(weak in theory_prose for weak in ("dual-engine", "two-engine", "two engine")):
                raise ValueError(
                    f"{pr_id} exact-math acceptance prose collapses the multi-axis contract"
                )


def render_mermaid(info: DagInfo) -> str:
    titles = {pr["id"]: str(pr.get("title", "")) for pr in info.prs}
    lines = ["flowchart TD"]
    for pr_id in info.order:
        node_id = pr_id.replace("-", "_")
        title = html.escape(titles.get(pr_id, ""), quote=True)
        lines.append(f'  {node_id}["{pr_id}<br/>{title}"]')
    for pr_id in info.order:
        for dep in info.prereqs[pr_id]:
            lines.append(f"  {dep.replace('-', '_')} --> {pr_id.replace('-', '_')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("backlog")
    parser.add_argument("--status", metavar="PATH")
    parser.add_argument("--strict-rescue-slice", action="store_true")
    parser.add_argument("--write-mermaid", metavar="PATH")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--work-unit",
        help="report selected AUTO_STACKED_PR eligibility separately from DAG validity",
    )
    parser.add_argument(
        "--candidate-ref",
        default="HEAD",
        help="activation candidate ref used for exact sealed-head eligibility",
    )
    args = parser.parse_args(argv)

    eligibility = None
    try:
        data = load_yaml(args.backlog)
        info = validate_backlog(data)
        if args.strict_rescue_slice:
            status = load_yaml(args.status) if args.status else None
            validate_long_horizon_rescue_slice(data, info, status=status)
        if args.write_mermaid:
            Path(args.write_mermaid).write_text(render_mermaid(info), encoding="utf-8")
        if args.work_unit:
            if not args.status:
                raise ValueError("--work-unit requires --status")
            repo = Path(args.backlog).resolve().parents[2]
            status = load_stacked_execution_status(repo)
            candidate_sha = resolve_candidate_activation_base(
                repo,
                status,
                work_unit_id=args.work_unit,
                candidate_ref=args.candidate_ref,
            )
            eligibility = evaluate_stack_eligibility(
                status,
                work_unit_id=args.work_unit,
                candidate_sha=candidate_sha,
            )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "total": len(info.ids),
                    "edges": info.edge_count,
                    "topological_order": list(info.order),
                    "selected_work_unit": (
                        {
                            "work_unit_id": args.work_unit,
                            **eligibility,
                        }
                        if eligibility is not None
                        else None
                    ),
                },
                indent=2,
            )
        )
    else:
        print(f"OK: {len(info.ids)} PRs, DAG valid")
        print("topological_order=" + ",".join(info.order))
        if eligibility is not None:
            if eligibility["eligible"]:
                print(f"eligibility=ELIGIBLE work_unit={args.work_unit}")
            else:
                print(
                    "eligibility=INELIGIBLE/DEFERRED "
                    f"work_unit={args.work_unit} retry_budget=0 assurance_budget=0"
                )
                for error in eligibility["errors"]:
                    print(f"eligibility_reason={error}")
    if eligibility is not None and not eligibility["eligible"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
