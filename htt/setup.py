"""Setuptools entrypoint with a fail-closed, hermetic wheel staging area."""
from __future__ import annotations

import os
from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.errors import SetupError


_PROJECT_ROOT = Path(__file__).resolve().parent
_BUILD_ROOT = Path(os.path.abspath(_PROJECT_ROOT / "build"))


class HermeticBuildPy(build_py):
    """Discard only project-local generated staging before copying sources.

    Setuptools intentionally reuses ``build/lib``.  That cache can retain a
    deleted Python module and silently ship it in a later wheel.  A wheel build
    therefore starts with a fresh staging directory, while source files and
    caches outside this project's own ``build`` tree are never touched.
    """

    def _checked_build_lib(self) -> Path:
        candidate = Path(self.build_lib)
        if not candidate.is_absolute():
            candidate = _PROJECT_ROOT / candidate
        candidate = Path(os.path.abspath(candidate))
        try:
            relative = candidate.relative_to(_BUILD_ROOT)
        except ValueError as exc:
            raise SetupError(
                f"refusing to clean build_lib outside {_BUILD_ROOT}: {candidate}"
            ) from exc

        cursor = _BUILD_ROOT
        for part in ("", *relative.parts):
            if part:
                cursor /= part
            if cursor.is_symlink():
                raise SetupError(f"refusing to clean symlinked build path: {cursor}")
        return candidate

    def run(self) -> None:
        if getattr(self, "editable_mode", False):
            super().run()
            return
        build_lib = self._checked_build_lib()
        if build_lib.exists() and not build_lib.is_dir():
            raise SetupError(f"build_lib is not a directory: {build_lib}")
        if build_lib.exists() and not self.dry_run:
            shutil.rmtree(build_lib)
        super().run()


setup(cmdclass={"build_py": HermeticBuildPy})
