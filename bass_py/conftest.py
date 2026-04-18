"""
conftest.py — repo root

Placed at the root so pytest's auto-detection treats this directory as the
project rootdir. Its presence is sufficient for `from bass.X.Y import Z`
imports to resolve when the suite runs from the monorepo root.

Nothing else in this file; the package structure itself (bass/, tsc/ with
__init__.py at every level) does the heavy lifting.
"""
