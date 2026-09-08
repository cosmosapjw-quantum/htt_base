"""Source binding for the restricted R3 provider, separate from native BASS.

The photon/optical donor is a required physical implementation input. A missing
archive closes only this provider; H dust oracles and direct experiments remain
executable. No perfect-fluid photon replacement is supplied here.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
from common.r7_contracts import UnsupportedObservable


REVIEW87_MEMBERS={
    "bianchi/matter/freestream.py":"b03aeed2cfcdaa5baf45fdab626941905674e2385bc06d1173a4b8c39ebf8bb4",
    "bianchi/matter/kinetic_einstein.py":"59f1c49539d35061d17490944ace63c48addce0e44e3d1a0f39f8f40b363d93b",
    "bianchi/rays/optical.py":"c6b83f73e0c65fe21c31291bdefdcc25c4c1ed6e497be85785075b5e137a1026",
}


@dataclass(frozen=True)
class RestrictedR3Provider:
    source_root: Path | None = None
    provider_id: str = "R3_COUNTERSTREAM_DUST_COLLISIONLESS_PLANCK_LRS_BI"

    def source_status(self):
        rows={}
        for member,expected in REVIEW87_MEMBERS.items():
            path=Path(self.source_root)/member if self.source_root is not None else None
            if path is None or not path.is_file(): rows[member]="SOURCE_UNAVAILABLE"
            else:
                actual=hashlib.sha256(path.read_bytes()).hexdigest()
                rows[member]="BOUND" if actual==expected else "IMMUTABLE_SOURCE_MISMATCH"
        return rows

    def capabilities(self):
        # Binding these original members is necessary, not sufficient: their
        # old background wrapper still needs the N7/N9/N10 stress-history adapter
        # and actual Jacobi/conservation validation before any channel opens.
        return ()

    def _unavailable(self,channel):
        missing={p:s for p,s in self.source_status().items() if s!="BOUND"}
        if missing: raise UnsupportedObservable(f"{self.provider_id}:{channel}: selected review87 source unavailable: {missing}")
        raise UnsupportedObservable(f"{self.provider_id}:{channel}: original donor bound; R3 stress-history adaptation and reference validation not executed")

    def predict_harmonics(self,parameters,initial_conditions,observer): return self._unavailable("harmonics")
    def predict_distance(self,parameters,source,observer,direction,redshift): return self._unavailable("distance")
    def radiation_jet(self,event): return self._unavailable("radiation_jet")
