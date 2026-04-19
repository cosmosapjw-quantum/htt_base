"""A36a.5 placeholder-caveat emission tests (W14D5).

Plan: docs/INDEPENDENT_TRACKS_NEXT_SESSION.md §2 Days 5-6 Week 14.
Parent: `docs/dossier/A36a_sigma_cone_literature.md` §A36a.5.

Covers three surfaces:
    (1) The `sigma_cone_provenance` helper itself — frozen promoted-set,
        deterministic output, suffix contract.
    (2) The HJ-02a producer (`mio.coherence.directional.to_mio_certificate`)
        attaches the per-probe placeholder tags for the non-promoted probes.
    (3) The HJ-02b producer (`mio.coherence.redshift_binned.to_mio_certificate`)
        attaches the same tags for the same non-promoted set.

Post-W14D5 expected promoted set = {"CatWISE"}. Post-W14D6 the set will
extend to {"CatWISE", "BiPoSH"}; this file's assertions are written so
W14D6 only needs a one-line change in the expected-flagged set.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from mio.coherence.directional import STANDARD_PROBES, resultant_vector
from mio.coherence.directional import to_mio_certificate as to_cert_hj02a
from mio.coherence.redshift_binned import (
    STANDARD_Z_PROBES,
    per_bin_resultants,
    total_drift_deg,
)
from mio.coherence.redshift_binned import to_mio_certificate as to_cert_hj02b
from mio.interface.sigma_cone_provenance import (
    PLACEHOLDER_CAVEAT_SUFFIX,
    PROMOTED_SIGMA_CONE_PROBES,
    is_promoted,
    placeholder_caveats_for,
)

A36A_YAML_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docs" / "dossier" / "A36a_sigma_cone_literature.yaml"
)


def test_promoted_set_is_frozen_and_contains_catwise():
    """W14D5 post-condition: CatWISE is the first A36a.5 promotion."""
    assert isinstance(PROMOTED_SIGMA_CONE_PROBES, frozenset)
    assert "CatWISE" in PROMOTED_SIGMA_CONE_PROBES


def test_promoted_set_contains_biposh_post_w14d6():
    """W14D6 post-condition: BiPoSH is the second A36a.5 promotion.

    W14D6 lands BiPoSH as the second retirement per A36a.5 last line
    (A36a.5 `Promotion log` row). The remaining three probes — CMB,
    Radio, CF4pp — stay flagged because their delta from literature
    is non-trivial even when the code value is conservative.
    """
    assert "BiPoSH" in PROMOTED_SIGMA_CONE_PROBES
    # CMB / Radio / CF4pp remain flagged.
    assert "CMB" not in PROMOTED_SIGMA_CONE_PROBES
    assert "Radio" not in PROMOTED_SIGMA_CONE_PROBES
    assert "CF4pp" not in PROMOTED_SIGMA_CONE_PROBES


def test_placeholder_caveats_for_five_standard_probes_excludes_promoted():
    """Input = five SSOT probes → output drops every PROMOTED name."""
    names = [p.name for p in STANDARD_PROBES]
    tags = placeholder_caveats_for(names)
    expected = sorted(
        f"{n}{PLACEHOLDER_CAVEAT_SUFFIX}"
        for n in names
        if n not in PROMOTED_SIGMA_CONE_PROBES
    )
    assert tags == expected


def test_placeholder_caveats_for_is_deterministic_and_sorted():
    """Output is ASCII-alphabetical regardless of input order / duplicates."""
    a = placeholder_caveats_for(["Radio", "CMB", "CF4pp", "Radio"])
    b = placeholder_caveats_for(["CF4pp", "CMB", "Radio"])
    assert a == b == sorted(a)


def test_placeholder_caveats_suffix_contract():
    """Every emitted tag ends in the module-level suffix."""
    for tag in placeholder_caveats_for(p.name for p in STANDARD_PROBES):
        assert tag.endswith(PLACEHOLDER_CAVEAT_SUFFIX)


def test_is_promoted_rejects_typos():
    """Strict equality; no case folding."""
    assert is_promoted("CatWISE") is True
    assert is_promoted("catwise") is False
    assert is_promoted("CatWISE ") is False


def test_hj02a_certificate_carries_placeholder_tags_for_non_promoted_probes():
    """`mio.coherence.directional.to_mio_certificate` now emits A36a.5 tags.

    After W14D5 the certificate for the five SSOT probes carries one
    placeholder tag per *non*-promoted probe — so CatWISE has no tag
    and the other four probes each produce one.
    """
    resultant = resultant_vector(STANDARD_PROBES)
    cert = to_cert_hj02a(STANDARD_PROBES, p_iso=0.001, resultant=resultant)
    expected_flagged = {
        p.name for p in STANDARD_PROBES if p.name not in PROMOTED_SIGMA_CONE_PROBES
    }
    expected_tags = {f"{n}{PLACEHOLDER_CAVEAT_SUFFIX}" for n in expected_flagged}
    assert expected_tags.issubset(set(cert.domain_caveats))
    # CatWISE is promoted → must NOT appear with the placeholder suffix.
    assert f"CatWISE{PLACEHOLDER_CAVEAT_SUFFIX}" not in cert.domain_caveats


def test_hj02b_certificate_carries_placeholder_tags_for_non_promoted_probes():
    """Symmetric check on the HJ-02b producer. Uses a minimal integration
    path (no Monte-Carlo) to keep the test fast."""
    results = per_bin_resultants(STANDARD_Z_PROBES)
    drift = total_drift_deg(results)
    cert = to_cert_hj02b(
        STANDARD_Z_PROBES, results, p_drift=0.5, total_drift=drift
    )
    expected_flagged = {
        p.name
        for p in STANDARD_Z_PROBES
        if p.name not in PROMOTED_SIGMA_CONE_PROBES
    }
    expected_tags = {f"{n}{PLACEHOLDER_CAVEAT_SUFFIX}" for n in expected_flagged}
    assert expected_tags.issubset(set(cert.domain_caveats))
    assert f"CatWISE{PLACEHOLDER_CAVEAT_SUFFIX}" not in cert.domain_caveats


def test_hj02a_certificate_caveat_count_equals_flagged_set_with_no_caller_caveats():
    """W14 R2 / W15D5 — over-emission guard.

    The W14D5 issubset assertions (`test_hj02a_certificate_carries_
    placeholder_tags_for_non_promoted_probes`) catch under-emission but
    pass silently on over-emission. When no caller caveats are supplied,
    the certificate's `domain_caveats` must equal the placeholder set
    exactly: one tag per non-promoted probe, alphabetical, no extras.

    A regression that emitted (e.g.) `"CatWISE_sigma_cone_plan_placeholder"`
    despite CatWISE being promoted, or duplicated a tag, would slip past
    the W14D5 issubset check; this test fails it.
    """
    resultant = resultant_vector(STANDARD_PROBES)
    cert = to_cert_hj02a(STANDARD_PROBES, p_iso=0.001, resultant=resultant)
    expected_flagged = {
        p.name for p in STANDARD_PROBES if p.name not in PROMOTED_SIGMA_CONE_PROBES
    }
    expected_tags = sorted(
        f"{n}{PLACEHOLDER_CAVEAT_SUFFIX}" for n in expected_flagged
    )
    assert sorted(cert.domain_caveats) == expected_tags
    assert len(cert.domain_caveats) == len(expected_flagged)


def test_hj02a_caller_caveats_preserved_alongside_placeholder_tags():
    """A caller-supplied caveat is kept and the placeholder tags appear
    exactly once even if the caller also supplied them.

    W16D1 (W15 F1) — union-equality clause. The W15D5 no-caller-caveats
    over-emission guard (`test_hj02a_certificate_caveat_count_equals_
    flagged_set_with_no_caller_caveats`) exercises only the empty-caller
    path; an over-emission coexisting with caller-supplied caveats
    would pass the dedup-count check below. The trailing
    `set(cert.domain_caveats) == set(caller_caveats) | expected_tags`
    assertion closes that residual: extra placeholder tags on a
    caller-caveats path now fail the test.
    """
    resultant = resultant_vector(STANDARD_PROBES)
    caller_caveats = ["masked_sky_partial", "Radio_sigma_cone_plan_placeholder"]
    cert = to_cert_hj02a(
        STANDARD_PROBES,
        p_iso=0.1,
        resultant=resultant,
        domain_caveats=caller_caveats,
    )
    caveats = cert.domain_caveats
    assert "masked_sky_partial" in caveats
    # Dedup: "Radio_sigma_cone_plan_placeholder" appears exactly once.
    assert caveats.count("Radio_sigma_cone_plan_placeholder") == 1
    # W16D1 (W15 F1) — union-equality: no tag outside of
    # caller_caveats ∪ expected placeholder set survives.
    expected_flagged = {
        p.name for p in STANDARD_PROBES if p.name not in PROMOTED_SIGMA_CONE_PROBES
    }
    expected_tags = {f"{n}{PLACEHOLDER_CAVEAT_SUFFIX}" for n in expected_flagged}
    assert set(caveats) == set(caller_caveats) | expected_tags


def test_standard_probes_sigma_code_matches_a36a_yaml():
    """W16D3 (W14 R3 / W13 F4) — A36a.3 literature-Δ YAML sidecar parity.

    The `A36a_sigma_cone_literature.yaml` sidecar mirrors §A36a.3 in a
    machine-readable form. This test guards the dossier-↔-code invariant
    on two axes:

    (1) Code parity. The `sigma_code_deg` column must equal the live
        `STANDARD_PROBES[*].sigma_cone_deg` value per PROBE_ID. A σ edit
        in `mio.coherence.directional` that forgets to update the YAML
        (or vice versa) fails here.
    (2) YAML internal self-consistency. For every row
        `|sigma_code_deg − sigma_lit_deg| == |delta_deg|`; an arithmetic
        typo in the human-written YAML trips this immediately.

    Scalar-reduction convention: three probes (Radio, CF4pp, BiPoSH)
    have literature σ quoted as a range in §A36a.2; the YAML records
    the midpoint as `sigma_lit_deg` and keeps the full range in the
    optional `sigma_lit_range_deg: [min, max]` field (not consumed
    here). See YAML header comment for the full edit protocol.
    """
    data = yaml.safe_load(A36A_YAML_PATH.read_text(encoding="utf-8"))
    rows = data["probes"]
    assert len(rows) == 5, f"expected 5 A36a.3 rows, got {len(rows)}"

    yaml_by_id = {r["probe_id"]: r for r in rows}
    code_by_id = {p.name: p.sigma_cone_deg for p in STANDARD_PROBES}
    assert set(yaml_by_id.keys()) == set(code_by_id.keys()), (
        f"PROBE_ID set mismatch: yaml={sorted(yaml_by_id)} "
        f"vs code={sorted(code_by_id)}"
    )

    for probe_id, row in yaml_by_id.items():
        # (1) code parity
        assert row["sigma_code_deg"] == code_by_id[probe_id], (
            f"{probe_id}: YAML sigma_code_deg={row['sigma_code_deg']} "
            f"vs STANDARD_PROBES sigma_cone_deg={code_by_id[probe_id]}"
        )
        # (2) internal self-consistency
        c, lit, delta = (
            row["sigma_code_deg"],
            row["sigma_lit_deg"],
            row["delta_deg"],
        )
        assert abs(abs(c - lit) - abs(delta)) < 1e-9, (
            f"{probe_id}: |{c} − {lit}| = {abs(c - lit)} ≠ |{delta}|"
        )
