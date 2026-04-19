"""
tests/test_baryon_only_policy.py
=================================

Day 4 test suite covering:
  §1 — SpeciesMetadata canonical table sanity
  §2 — SpeciesRegistry construction + basic queries
  §3 — Invariant I1-I3: non-tilt species have v=0
  §4 — Invariant I4: tight-coupling v_electron = v_baryon
  §5 — Invariant I5: only baryon+electron can carry tilt
  §6 — set_velocity_if_allowed: attempted violations raise
  §7 — set_tilt: coherent update preserves invariants
  §8 — Factory functions
  §9 — Role queries (tilt_carriers, thomson, Teff)
  §10 — Paper I statistics (ξ) and Teff-type queries
  §11 — Direction normalization

Run
---
    pytest test_baryon_only_policy.py -v
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.tilt.baryon_only_policy import (
    Species, Statistics, TeffRepresentation, SpeciesMetadata,
    SPECIES_METADATA,
    SpeciesRegistry, BaryonOnlyPolicyViolation,
    make_flrw_registry, make_tilted_registry, activate_baryon_tilt,
)


CF4_BETA = 1.36e-3  # Production CF4 tilt value


# ═══════════════════════════════════════════════════════════════
# §1 — Metadata table sanity
# ═══════════════════════════════════════════════════════════════

class TestSpeciesMetadata:
    def test_all_species_have_metadata(self):
        for sp in Species:
            assert sp in SPECIES_METADATA, f"Species {sp} missing metadata"

    def test_photons_are_bose_einstein(self):
        assert SPECIES_METADATA[Species.GAMMA].statistics == Statistics.BE
        assert SPECIES_METADATA[Species.GAMMA].xi == +1

    def test_all_neutrinos_are_fermi_dirac(self):
        for sp in (Species.NU_E, Species.NU_E_BAR, Species.NU_X, Species.NU_X_BAR):
            assert SPECIES_METADATA[sp].statistics == Statistics.FD
            assert SPECIES_METADATA[sp].xi == -1

    def test_cdm_baryon_electron_are_classical(self):
        for sp in (Species.CDM, Species.BARYON, Species.ELECTRON):
            assert SPECIES_METADATA[sp].statistics == Statistics.MB
            assert SPECIES_METADATA[sp].xi == 0

    def test_teff_types_correct(self):
        """Paper I: photons one-field; Paper II: neutrinos two-field; others NONE."""
        assert SPECIES_METADATA[Species.GAMMA].teff_type == TeffRepresentation.ONE_FIELD
        for sp in (Species.NU_E, Species.NU_E_BAR, Species.NU_X, Species.NU_X_BAR):
            assert SPECIES_METADATA[sp].teff_type == TeffRepresentation.TWO_FIELD
        for sp in (Species.CDM, Species.BARYON, Species.ELECTRON):
            assert SPECIES_METADATA[sp].teff_type == TeffRepresentation.NONE

    def test_thomson_participants_are_gamma_and_electron(self):
        """Thomson: γ ↔ e⁻. Not baryons directly (via electrons)."""
        assert SPECIES_METADATA[Species.GAMMA].has_thomson_coupling
        assert SPECIES_METADATA[Species.ELECTRON].has_thomson_coupling
        assert not SPECIES_METADATA[Species.BARYON].has_thomson_coupling
        for sp in (Species.CDM, Species.NU_E, Species.NU_X):
            assert not SPECIES_METADATA[sp].has_thomson_coupling

    def test_only_baryon_and_electron_carry_tilt(self):
        for sp in Species:
            expected = sp in (Species.BARYON, Species.ELECTRON)
            assert SPECIES_METADATA[sp].can_carry_tilt == expected, (
                f"Species {sp.value}: can_carry_tilt mismatch"
            )


# ═══════════════════════════════════════════════════════════════
# §2 — Registry construction
# ═══════════════════════════════════════════════════════════════

class TestRegistryConstruction:
    def test_default_construction_is_flrw(self):
        """Default registry has β̄=0 → all species at rest."""
        reg = SpeciesRegistry()
        for sp in Species:
            assert reg.get_velocity_magnitude(sp) == 0.0

    def test_construction_with_tilt(self):
        reg = SpeciesRegistry(
            beta_bar=CF4_BETA, direction=np.array([1.0, 0.0, 0.0]),
        )
        assert math.isclose(reg.get_velocity_magnitude(Species.BARYON), CF4_BETA)
        assert math.isclose(reg.get_velocity_magnitude(Species.ELECTRON), CF4_BETA)

    def test_all_species_present_in_registry(self):
        reg = SpeciesRegistry()
        assert len(reg.list_species()) == 8  # 5 types: γ, 4× ν, CDM, baryon, e⁻

    def test_zero_direction_raises(self):
        with pytest.raises(ValueError, match="nonzero"):
            SpeciesRegistry(beta_bar=1e-3, direction=np.zeros(3))

    def test_direction_is_normalized(self):
        """Even with non-unit direction input, velocity magnitude = β̄."""
        reg = SpeciesRegistry(
            beta_bar=1e-3, direction=np.array([3.0, 4.0, 0.0]),  # |d|=5
        )
        assert math.isclose(reg.get_velocity_magnitude(Species.BARYON), 1e-3)


# ═══════════════════════════════════════════════════════════════
# §3 — Invariants I1-I3 (non-tilt species v=0)
# ═══════════════════════════════════════════════════════════════

class TestInvariantsI1_I3:
    def test_cdm_velocity_zero(self):
        reg = make_tilted_registry(CF4_BETA)
        assert reg.get_velocity_magnitude(Species.CDM) == 0.0

    def test_gamma_velocity_zero(self):
        reg = make_tilted_registry(CF4_BETA)
        assert reg.get_velocity_magnitude(Species.GAMMA) == 0.0

    def test_all_neutrinos_velocity_zero(self):
        reg = make_tilted_registry(CF4_BETA)
        for sp in (Species.NU_E, Species.NU_E_BAR, Species.NU_X, Species.NU_X_BAR):
            assert reg.get_velocity_magnitude(sp) == 0.0

    def test_invariant_persists_after_large_beta(self):
        """Even for β̄ → 1 (unphysical but algebraically allowed), CDM still at rest."""
        reg = make_tilted_registry(0.5)
        assert reg.get_velocity_magnitude(Species.CDM) == 0.0
        assert reg.get_velocity_magnitude(Species.GAMMA) == 0.0


# ═══════════════════════════════════════════════════════════════
# §4 — Invariant I4 (tight-coupling)
# ═══════════════════════════════════════════════════════════════

class TestInvariantI4_TightCoupling:
    def test_electron_equals_baryon(self):
        reg = make_tilted_registry(CF4_BETA)
        v_b = reg.get_velocity(Species.BARYON)
        v_e = reg.get_velocity(Species.ELECTRON)
        assert np.allclose(v_b, v_e)

    def test_magnitudes_match(self):
        reg = make_tilted_registry(2e-3)
        assert math.isclose(
            reg.get_velocity_magnitude(Species.BARYON),
            reg.get_velocity_magnitude(Species.ELECTRON),
        )

    def test_tight_coupling_survives_direction_change(self):
        reg = SpeciesRegistry(
            beta_bar=1e-3, direction=np.array([0.0, 1.0, 0.0]),
        )
        v_b = reg.get_velocity(Species.BARYON)
        v_e = reg.get_velocity(Species.ELECTRON)
        assert np.allclose(v_b, v_e)
        # Direction is along +ŷ
        assert math.isclose(v_b[1], 1e-3)


# ═══════════════════════════════════════════════════════════════
# §5 — Invariant I5 (only baryon+electron tilt)
# ═══════════════════════════════════════════════════════════════

class TestInvariantI5_OnlyBaryonsCarry:
    def test_tilt_carriers_list(self):
        reg = make_tilted_registry(CF4_BETA)
        carriers = reg.tilt_carriers()
        assert set(carriers) == {Species.BARYON, Species.ELECTRON}

    def test_non_tilt_species_list(self):
        reg = make_tilted_registry(CF4_BETA)
        non_tilt = reg.non_tilt_species()
        expected = {Species.GAMMA, Species.NU_E, Species.NU_E_BAR,
                    Species.NU_X, Species.NU_X_BAR, Species.CDM}
        assert set(non_tilt) == expected

    def test_validate_passes_on_clean_init(self):
        reg = make_tilted_registry(CF4_BETA)
        reg.validate_baryon_only_invariant()  # should not raise


# ═══════════════════════════════════════════════════════════════
# §6 — Attempted policy violations raise
# ═══════════════════════════════════════════════════════════════

class TestPolicyViolations:
    def test_setting_cdm_velocity_raises(self):
        reg = make_flrw_registry()
        with pytest.raises(BaryonOnlyPolicyViolation, match="cdm"):
            reg.set_velocity_if_allowed(Species.CDM, np.array([1e-3, 0.0, 0.0]))

    def test_setting_photon_velocity_raises(self):
        reg = make_flrw_registry()
        with pytest.raises(BaryonOnlyPolicyViolation, match="gamma"):
            reg.set_velocity_if_allowed(Species.GAMMA, np.array([1e-3, 0.0, 0.0]))

    def test_setting_neutrino_velocity_raises(self):
        reg = make_flrw_registry()
        with pytest.raises(BaryonOnlyPolicyViolation, match="nu_e"):
            reg.set_velocity_if_allowed(Species.NU_E, np.array([1e-3, 0.0, 0.0]))

    def test_setting_zero_velocity_for_cdm_is_ok(self):
        """Zero velocity is always allowed (trivially satisfies policy)."""
        reg = make_flrw_registry()
        reg.set_velocity_if_allowed(Species.CDM, np.zeros(3))
        assert reg.get_velocity_magnitude(Species.CDM) == 0.0

    def test_setting_baryon_velocity_updates_electron_too(self):
        """Tight-coupling: setting v_baryon auto-updates v_electron."""
        reg = make_flrw_registry()
        new_v = np.array([2e-3, 0.0, 0.0])
        reg.set_velocity_if_allowed(Species.BARYON, new_v)
        assert np.allclose(reg.get_velocity(Species.BARYON), new_v)
        assert np.allclose(reg.get_velocity(Species.ELECTRON), new_v)

    def test_setting_electron_velocity_updates_baryon_too(self):
        """Tight-coupling is symmetric."""
        reg = make_flrw_registry()
        new_v = np.array([0.0, 3e-3, 0.0])
        reg.set_velocity_if_allowed(Species.ELECTRON, new_v)
        assert np.allclose(reg.get_velocity(Species.ELECTRON), new_v)
        assert np.allclose(reg.get_velocity(Species.BARYON), new_v)


# ═══════════════════════════════════════════════════════════════
# §7 — set_tilt: coherent update
# ═══════════════════════════════════════════════════════════════

class TestSetTilt:
    def test_set_tilt_updates_baryon_and_electron(self):
        reg = make_flrw_registry()
        reg.set_tilt(beta_bar=5e-3, direction=np.array([0.0, 0.0, 1.0]))
        assert math.isclose(reg.get_velocity_magnitude(Species.BARYON), 5e-3)
        assert math.isclose(reg.get_velocity_magnitude(Species.ELECTRON), 5e-3)

    def test_set_tilt_preserves_other_species_at_rest(self):
        reg = make_flrw_registry()
        reg.set_tilt(beta_bar=5e-3)
        for sp in reg.non_tilt_species():
            assert reg.get_velocity_magnitude(sp) == 0.0

    def test_set_tilt_preserves_direction_if_not_given(self):
        reg = SpeciesRegistry(beta_bar=1e-3, direction=np.array([0.0, 1.0, 0.0]))
        reg.set_tilt(beta_bar=2e-3)  # no direction given
        v_b = reg.get_velocity(Species.BARYON)
        # Should still point along +ŷ
        assert math.isclose(v_b[1], 2e-3, abs_tol=1e-15)

    def test_zero_direction_in_set_tilt_raises(self):
        reg = make_flrw_registry()
        with pytest.raises(ValueError, match="nonzero"):
            reg.set_tilt(beta_bar=1e-3, direction=np.zeros(3))


# ═══════════════════════════════════════════════════════════════
# §8 — Factory functions
# ═══════════════════════════════════════════════════════════════

class TestFactories:
    def test_make_flrw_registry(self):
        reg = make_flrw_registry()
        assert reg.beta_bar == 0.0
        for sp in Species:
            assert reg.get_velocity_magnitude(sp) == 0.0

    def test_make_tilted_registry_default_direction(self):
        reg = make_tilted_registry(CF4_BETA)
        v_b = reg.get_velocity(Species.BARYON)
        assert math.isclose(v_b[0], CF4_BETA)
        assert math.isclose(v_b[1], 0.0)
        assert math.isclose(v_b[2], 0.0)

    def test_make_tilted_registry_custom_direction(self):
        direction = np.array([1.0, 1.0, 0.0]) / math.sqrt(2)
        reg = make_tilted_registry(1e-3, direction=direction)
        v_b = reg.get_velocity(Species.BARYON)
        assert math.isclose(np.linalg.norm(v_b), 1e-3)

    def test_activate_baryon_tilt_produces_new_registry(self):
        reg1 = make_flrw_registry()
        reg2 = activate_baryon_tilt(reg1, beta_bar=2e-3)
        assert reg1.beta_bar == 0.0
        assert reg2.beta_bar == 2e-3
        # reg1 unchanged
        assert reg1.get_velocity_magnitude(Species.BARYON) == 0.0


# ═══════════════════════════════════════════════════════════════
# §9 — Role queries
# ═══════════════════════════════════════════════════════════════

class TestRoleQueries:
    def test_thomson_participants(self):
        reg = make_flrw_registry()
        thomson = reg.thomson_participants()
        assert set(thomson) == {Species.GAMMA, Species.ELECTRON}

    def test_species_with_teff_all(self):
        reg = make_flrw_registry()
        all_teff = reg.species_with_teff()  # no filter
        # photons (one-field) + 4 neutrinos (two-field) = 5 species
        assert len(all_teff) == 5
        assert Species.GAMMA in all_teff

    def test_species_with_teff_one_field(self):
        reg = make_flrw_registry()
        one_field = reg.species_with_teff(TeffRepresentation.ONE_FIELD)
        assert one_field == [Species.GAMMA]

    def test_species_with_teff_two_field(self):
        reg = make_flrw_registry()
        two_field = reg.species_with_teff(TeffRepresentation.TWO_FIELD)
        assert len(two_field) == 4  # 4 neutrino flavours
        for sp in two_field:
            assert sp.name.startswith("NU_")


# ═══════════════════════════════════════════════════════════════
# §10 — Paper I statistics + metadata query
# ═══════════════════════════════════════════════════════════════

class TestPaperIStatistics:
    def test_get_xi_photons(self):
        reg = make_flrw_registry()
        assert reg.get_xi(Species.GAMMA) == +1  # BE

    def test_get_xi_neutrinos(self):
        reg = make_flrw_registry()
        assert reg.get_xi(Species.NU_E) == -1  # FD

    def test_get_xi_cdm(self):
        reg = make_flrw_registry()
        assert reg.get_xi(Species.CDM) == 0  # MB

    def test_metadata_access(self):
        reg = make_flrw_registry()
        meta = reg.metadata(Species.GAMMA)
        assert meta.species == Species.GAMMA
        assert meta.statistics == Statistics.BE
        assert meta.has_thomson_coupling


# ═══════════════════════════════════════════════════════════════
# §11 — Summary report
# ═══════════════════════════════════════════════════════════════

class TestSummary:
    def test_flrw_summary(self):
        reg = make_flrw_registry()
        report = reg.summary()
        assert report['policy'] == 'baryon-only'
        assert report['beta_bar'] == 0.0
        for mag in report['velocity_magnitudes'].values():
            assert mag == 0.0

    def test_tilted_summary(self):
        reg = make_tilted_registry(CF4_BETA)
        report = reg.summary()
        assert report['beta_bar'] == CF4_BETA
        assert math.isclose(
            report['velocity_magnitudes']['baryon'], CF4_BETA,
        )
        assert math.isclose(
            report['velocity_magnitudes']['electron'], CF4_BETA,
        )
        assert report['velocity_magnitudes']['cdm'] == 0.0
        assert report['velocity_magnitudes']['gamma'] == 0.0

    def test_summary_includes_tilt_carrier_labels(self):
        reg = make_tilted_registry(1e-3)
        report = reg.summary()
        assert set(report['tilt_carriers']) == {'baryon', 'electron'}
        assert set(report['thomson_participants']) == {'gamma', 'electron'}
