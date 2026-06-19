import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/inventory_external_research_inputs.py"
ARCHIVE_DIR = ROOT / "docs/audits/external_research_inputs_2026-06-20"
ARCHIVE_MANIFEST = ARCHIVE_DIR / "ARCHIVE_MANIFEST.md"
INVENTORY_JSON = ARCHIVE_DIR / "input_inventory.json"
INVENTORY_MD = ARCHIVE_DIR / "input_inventory.md"
RESPONSE_MATRIX = ROOT / "docs/generated/external_research_input_response_matrix.md"
INPUT_NAMES = {
    "RESEARCH_AUDIT_REPORT.md",
    "publishable_data_analysis_program.zip",
    "htt_publishable_novel_analysis_program_2026-06-19.zip",
    "htt_beyond_mes_egs_theorem_program_2026-06-19.zip",
    "egs_theorem_program.zip",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_inventory_module():
    spec = importlib.util.spec_from_file_location("external_research_inventory", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_external_research_input_inventory_check_mode_passes():
    result = subprocess.run(
        [
            "venv/bin/python",
            "scripts/inventory_external_research_inputs.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_external_research_input_inventory_hashes_entries_and_archive_copies():
    payload = json.loads(INVENTORY_JSON.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "htt.external_research_input_inventory.v1"
    assert payload["owner"] == "COMMON"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "none"
    assert payload["archive_directory"] == "docs/audits/external_research_inputs_2026-06-20"
    assert payload["archive_manifest"] == "docs/audits/external_research_inputs_2026-06-20/ARCHIVE_MANIFEST.md"
    assert payload["canonical_sources"] == {
        "manuscript_audit": "RESEARCH_AUDIT_REPORT.md",
        "data_analysis_program": "htt_publishable_novel_analysis_program_2026-06-19.zip",
        "theorem_program": "htt_beyond_mes_egs_theorem_program_2026-06-19.zip",
    }
    assert {item["name"] for item in payload["inputs"]} == INPUT_NAMES
    assert len(payload["input_hashes"]) == len(INPUT_NAMES)

    for item in payload["inputs"]:
        source = ROOT / item["source_path"]
        archived = ROOT / item["archive_path"]
        assert source.exists(), item["name"]
        assert archived.exists(), item["archive_path"]
        assert item["sha256"] == _sha256(source) == _sha256(archived)
        assert item["size_bytes"] == source.stat().st_size == archived.stat().st_size
        assert item["source_role"].startswith("external_")
        assert item["selected_documents"]
        assert item["supersession_note"]
        assert item["external_input_status"] == "raw_external_input_hash_preserved"
        if item["name"].endswith(".zip"):
            with ZipFile(source) as archive:
                names = sorted(archive.namelist())
                file_count = sum(not name.endswith("/") for name in names)
                dir_count = sum(name.endswith("/") for name in names)
            assert item["zip"]["entry_count"] == len(names)
            assert item["zip"]["file_entry_count"] == file_count
            assert item["zip"]["directory_entry_count"] == dir_count
            assert item["zip"]["entries"] == names
            assert item["zip"]["top_level_summary"]
        else:
            assert item["zip"] is None

    inventory_text = INVENTORY_MD.read_text(encoding="utf-8")
    manifest_text = ARCHIVE_MANIFEST.read_text(encoding="utf-8")
    assert "diagnostic/proposed inputs" in inventory_text
    assert "not publication evidence" in inventory_text
    assert "no native low-ell solver output" in inventory_text
    assert "no Bianchi family identification" in inventory_text
    assert "raw external audit/proposal inputs" in inventory_text
    assert "raw external audit/proposal inputs" in manifest_text
    assert "not repo-authored" in manifest_text
    assert "native-transfer outputs" in manifest_text


def test_external_research_input_response_matrix_contains_required_actions():
    text = RESPONSE_MATRIX.read_text(encoding="utf-8")
    for token in [
        "audit minor revisions",
        "formalism harmonization",
        "CF4++ traceability",
        "local/global joint rest-frame program",
        "finite mock",
        "rank",
        "Fisher",
        "null",
        "PPC",
        "theorem program P0",
        "theorem program P1",
        "theorem program P2",
        "kill-switches",
    ]:
        assert token in text
    assert "claim_tier: diagnostic_only" in text
    assert "transfer_source: none" in text


def test_external_research_input_inventory_check_mode_fails_when_stale(tmp_path, monkeypatch):
    module = _load_inventory_module()
    payload = module.build_payload()
    stale_manifest = tmp_path / "ARCHIVE_MANIFEST.md"
    stale_json = tmp_path / "input_inventory.json"
    stale_md = tmp_path / "input_inventory.md"
    stale_matrix = tmp_path / "external_research_input_response_matrix.md"
    stale_manifest.write_text(module.render_archive_manifest(payload), encoding="utf-8")
    stale_json.write_text(module.json_text(payload).replace("COMMON", "STALE", 1), encoding="utf-8")
    stale_md.write_text(module.render_inventory_markdown(payload), encoding="utf-8")
    stale_matrix.write_text(module.render_response_matrix(payload), encoding="utf-8")

    monkeypatch.setattr(module, "ARCHIVE_MANIFEST", stale_manifest)
    monkeypatch.setattr(module, "INVENTORY_JSON", stale_json)
    monkeypatch.setattr(module, "INVENTORY_MD", stale_md)
    monkeypatch.setattr(module, "RESPONSE_MATRIX", stale_matrix)

    assert module.check_outputs(payload) == 1


def test_external_research_input_inventory_rejects_symlink_archive_destinations(tmp_path, monkeypatch):
    module = _load_inventory_module()
    out_dir = tmp_path / "archive"
    out_dir.mkdir()
    monkeypatch.setattr(module, "OUT_DIR", out_dir)
    monkeypatch.setattr(module, "ARCHIVE_MANIFEST", out_dir / "ARCHIVE_MANIFEST.md")
    monkeypatch.setattr(module, "INVENTORY_JSON", out_dir / "input_inventory.json")
    monkeypatch.setattr(module, "INVENTORY_MD", out_dir / "input_inventory.md")
    monkeypatch.setattr(
        module,
        "RESPONSE_MATRIX",
        tmp_path / "external_research_input_response_matrix.md",
    )
    payload = module.build_payload()
    first = payload["inputs"][0]
    archived = Path(first["archive_path"])
    if not archived.is_absolute():
        archived = ROOT / archived
    outside_target = tmp_path / "outside.md"
    outside_target.write_text("do not overwrite", encoding="utf-8")
    archived.symlink_to(outside_target)

    try:
        module._copy_inputs(payload)
    except RuntimeError as exc:
        assert "symlink" in str(exc)
    else:
        raise AssertionError("expected symlink archive destination rejection")
    assert outside_target.read_text(encoding="utf-8") == "do not overwrite"


def test_external_research_input_inventory_avoids_forbidden_claims():
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (INVENTORY_JSON, INVENTORY_MD, RESPONSE_MATRIX)
    )
    forbidden = [
        "Bianchi geometry " + "detected",
        "Bianchi family " + "identified",
        "model-independent truth " + "certificate",
        "MIO " + "posterior",
        "TSC full " + "solver",
        "Teff full polarisation " + "closure",
        "external transfer validated as " + "native",
        "native solver " + "result",
        "family " + "identified",
        "geometry " + "detected",
        "truth " + "certificate",
    ]
    for phrase in forbidden:
        assert phrase not in text
