from __future__ import annotations

import mio.coherence as coherence
import mio.coherence.directional as directional
import mio.coherence.redshift_binned as redshift_binned
import mio.interface as interface
import mio.interface.manifest as manifest
import mio.interface.mio_certificate as mio_certificate
import mio.interface.probe_name_registry as probe_name_registry
import mio.interface.sigma_cone_provenance as sigma_cone_provenance


def test_coherence_root_exports_directional_entrypoints() -> None:
    assert coherence.DIRECTIONAL_ARTEFACT_FILENAME == directional.ARTEFACT_FILENAME
    assert coherence.DirectionalProbe is directional.DirectionalProbe
    assert coherence.STANDARD_PROBES is directional.STANDARD_PROBES
    assert coherence.resultant_vector is directional.resultant_vector
    assert coherence.pairwise_separations is directional.pairwise_separations
    assert coherence.coherence_chi2 is directional.coherence_chi2
    assert coherence.isotropy_pvalue is directional.isotropy_pvalue
    assert (
        coherence.emit_directional_coherence_artefact
        is directional.emit_directional_coherence_artefact
    )
    assert coherence.to_directional_mio_certificate is directional.to_mio_certificate
    assert "DirectionalProbe" in coherence.__all__
    assert "to_directional_mio_certificate" in coherence.__all__


def test_coherence_root_exports_redshift_entrypoints() -> None:
    assert coherence.REDSHIFT_ARTEFACT_FILENAME == redshift_binned.ARTEFACT_FILENAME
    assert coherence.RedshiftBinnedProbe is redshift_binned.RedshiftBinnedProbe
    assert coherence.STANDARD_Z_PROBES is redshift_binned.STANDARD_Z_PROBES
    assert coherence.DEFAULT_Z_BINS is redshift_binned.DEFAULT_Z_BINS
    assert (
        coherence.EXACT_ENUMERATION_MAX_PERMUTATIONS
        == redshift_binned.EXACT_ENUMERATION_MAX_PERMUTATIONS
    )
    assert coherence.ZBinResult is redshift_binned.ZBinResult
    assert coherence.assign_probes_to_bins is redshift_binned.assign_probes_to_bins
    assert coherence.per_bin_resultants is redshift_binned.per_bin_resultants
    assert coherence.total_drift_deg is redshift_binned.total_drift_deg
    assert (
        coherence.pairwise_bin_separations
        is redshift_binned.pairwise_bin_separations
    )
    assert coherence.drift_pvalue is redshift_binned.drift_pvalue
    assert (
        coherence.emit_redshift_coherence_artefact
        is redshift_binned.emit_redshift_coherence_artefact
    )
    assert coherence.to_redshift_mio_certificate is redshift_binned.to_mio_certificate
    assert "RedshiftBinnedProbe" in coherence.__all__
    assert "to_redshift_mio_certificate" in coherence.__all__


def test_interface_root_exports_manifest_and_certificate_helpers() -> None:
    assert interface.MioPrerequisites is manifest.MioPrerequisites
    assert interface.MioReadiness is manifest.MioReadiness
    assert interface.assess_mio_readiness is manifest.assess_mio_readiness
    assert interface.build_mio_manifest is manifest.build_mio_manifest
    assert interface.merge_domain_caveats is manifest.merge_domain_caveats
    assert interface.build_mio_certificate is mio_certificate.build_mio_certificate
    assert interface.certificate_to_payload is mio_certificate.certificate_to_payload
    assert "build_mio_certificate" in interface.__all__
    assert "build_mio_manifest" in interface.__all__


def test_interface_root_exports_registry_and_sigma_cone_helpers() -> None:
    assert interface.REGISTERED_PROBE_IDS is probe_name_registry.REGISTERED_PROBE_IDS
    assert interface.is_registered_probe_id is probe_name_registry.is_registered_probe_id
    assert (
        interface.PLACEHOLDER_CAVEAT_SUFFIX
        == sigma_cone_provenance.PLACEHOLDER_CAVEAT_SUFFIX
    )
    assert (
        interface.PROMOTED_SIGMA_CONE_PROBES
        is sigma_cone_provenance.PROMOTED_SIGMA_CONE_PROBES
    )
    assert (
        interface.placeholder_caveats_for
        is sigma_cone_provenance.placeholder_caveats_for
    )
    assert (
        interface.is_sigma_cone_promoted
        is sigma_cone_provenance.is_promoted
    )
    assert "REGISTERED_PROBE_IDS" in interface.__all__
    assert "is_sigma_cone_promoted" in interface.__all__
