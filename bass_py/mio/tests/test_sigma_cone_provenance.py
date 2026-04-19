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

import numpy as np

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


def test_promoted_set_is_frozen_and_contains_catwise():
    """W14D5 post-condition: CatWISE is the first A36a.5 promotion."""
    assert isinstance(PROMOTED_SIGMA_CONE_PROBES, frozenset)
    assert "CatWISE" in PROMOTED_SIGMA_CONE_PROBES


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


def test_hj02a_caller_caveats_preserved_alongside_placeholder_tags():
    """A caller-supplied caveat is kept and the placeholder tags appear
    exactly once even if the caller also supplied them."""
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
