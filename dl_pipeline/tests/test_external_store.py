from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from external_store import (  # noqa: E402
    ENV_VAR,
    ExternalStoreUnavailable,
    _link_point,
    ensure_data_dir,
    ensure_data_parent,
    external_store_root,
)


@pytest.fixture()
def disks(tmp_path: Path) -> tuple[Path, Path]:
    """A fake repository workdir and a fake external store."""
    workdir = tmp_path / "repo" / "workdir"
    store = tmp_path / "nvme" / "workdir"
    workdir.mkdir(parents=True)
    store.mkdir(parents=True)
    return workdir, store


def test_link_point_uses_first_component() -> None:
    assert str(_link_point(Path("compact_products/desi"))) == "compact_products"


def test_link_point_goes_one_level_deeper_under_raw() -> None:
    assert str(_link_point(Path("raw/act_data/archives"))) == str(Path("raw/act_data"))


def test_link_point_refuses_raw_itself_and_local_only_dirs() -> None:
    assert _link_point(Path("raw")) is None
    assert _link_point(Path("logs")) is None
    assert _link_point(Path("logs/fetch")) is None
    assert _link_point(Path("raw/logs")) is None


def test_new_workdir_child_lands_on_the_external_store(disks) -> None:
    workdir, store = disks

    made = ensure_data_dir(workdir / "compact_products" / "desi", workdir=workdir, store=store)

    assert made.is_dir()
    assert (workdir / "compact_products").is_symlink()
    assert (workdir / "compact_products").readlink() == store / "compact_products"
    assert (store / "compact_products" / "desi").is_dir()


def test_new_raw_child_is_linked_one_level_deeper(disks) -> None:
    workdir, store = disks

    ensure_data_dir(workdir / "raw" / "planck_data", workdir=workdir, store=store)

    assert not (workdir / "raw").is_symlink(), "workdir/raw must stay a real directory"
    assert (workdir / "raw" / "planck_data").is_symlink()
    assert (store / "raw" / "planck_data").is_dir()


def test_local_only_directories_stay_in_the_repository(disks) -> None:
    workdir, store = disks

    ensure_data_dir(workdir / "logs", workdir=workdir, store=store)

    assert (workdir / "logs").is_dir()
    assert not (workdir / "logs").is_symlink()
    assert not (store / "logs").exists()


def test_paths_outside_workdir_are_created_in_place(tmp_path: Path, disks) -> None:
    workdir, store = disks
    elsewhere = tmp_path / "somewhere" / "else"

    ensure_data_dir(elsewhere, workdir=workdir, store=store)

    assert elsewhere.is_dir()
    assert not elsewhere.is_symlink()


def test_existing_real_directory_is_left_alone(disks) -> None:
    workdir, store = disks
    existing = workdir / "obs_bundle"
    existing.mkdir()

    ensure_data_dir(existing / "cmb" / "maps", workdir=workdir, store=store)

    assert not existing.is_symlink()
    assert (existing / "cmb" / "maps").is_dir()
    assert not (store / "obs_bundle").exists()


def test_second_call_reuses_the_existing_link(disks) -> None:
    workdir, store = disks

    ensure_data_dir(workdir / "downloads" / "act", workdir=workdir, store=store)
    ensure_data_dir(workdir / "downloads" / "planck", workdir=workdir, store=store)

    assert (workdir / "downloads").readlink() == store / "downloads"
    assert (store / "downloads" / "act").is_dir()
    assert (store / "downloads" / "planck").is_dir()


def test_broken_link_fails_closed_instead_of_refilling_the_system_disk(disks) -> None:
    workdir, store = disks
    (workdir / "raw").mkdir()
    (workdir / "raw" / "planck_ffp10").symlink_to(store / "gone")

    with pytest.raises(ExternalStoreUnavailable):
        ensure_data_dir(workdir / "raw" / "planck_ffp10" / "smica", workdir=workdir, store=store)


def test_without_a_store_everything_is_created_locally(disks) -> None:
    workdir, _ = disks

    ensure_data_dir(workdir / "raw" / "desi", workdir=workdir, store=None)

    assert (workdir / "raw" / "desi").is_dir()
    assert not (workdir / "raw" / "desi").is_symlink()


def test_ensure_data_parent_creates_only_the_parent(disks) -> None:
    workdir, store = disks

    dst = ensure_data_parent(
        workdir / "raw" / "act_data" / "dr6_data.fits", workdir=workdir, store=store
    )

    assert not dst.exists()
    assert (store / "raw" / "act_data").is_dir()
    assert (workdir / "raw" / "act_data").is_symlink()


def test_env_var_disables_the_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VAR, "")
    assert external_store_root() is None

    monkeypatch.setenv(ENV_VAR, "off")
    assert external_store_root() is None


def test_env_var_selects_an_explicit_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "elsewhere"))

    assert external_store_root() == tmp_path / "elsewhere"
