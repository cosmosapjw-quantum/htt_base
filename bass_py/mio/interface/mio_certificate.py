"""mio.interface.mio_certificate — MioCertificate generator API.

Skeleton landed Week 6 Day 1 (MIO-BOOT-01). Full
`build_mio_certificate(...)` implementation lands Week 6 Day 2
(MIO-HJ-06a, plan §12.4).

The schema contract lives at `workspace.contracts.mio_certificate` —
this module only exposes the *generator* that auto-populates
provenance fields (git_commit, config_hash) and enforces G19
(rejects any `posterior`-keyword argument).
"""
from __future__ import annotations
