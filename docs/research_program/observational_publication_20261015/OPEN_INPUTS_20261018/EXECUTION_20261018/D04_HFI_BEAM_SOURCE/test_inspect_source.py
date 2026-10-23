"""Small synthetic parser/control fixtures; no scientific campaign allocation."""
import importlib.util
import io
from pathlib import Path
import sys
import tarfile

from astropy.io.fits import Header

spec = importlib.util.spec_from_file_location("hfi_source_intake", Path(__file__).with_name("inspect_source.py"))
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def header(cards):
    return Header(cards).tostring().encode("ascii")


def fixture_tar(members, fmt=tarfile.PAX_FORMAT):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=fmt) as archive:
        for name, payload, kind in members:
            item = tarfile.TarInfo(name)
            item.type = kind
            item.size = len(payload)
            if kind == tarfile.SYMTYPE:
                item.linkname = "../../never-follow"
            archive.addfile(item, io.BytesIO(payload))
    buffer.seek(0)
    return buffer


def test_all_hdus_heap_sizing_and_document_duplicate_names():
    primary = header([("SIMPLE", True), ("BITPIX", 8), ("NAXIS", 0)])
    table = header([("XTENSION", "BINTABLE"), ("BITPIX", 8), ("NAXIS", 2),
                    ("NAXIS1", 8), ("NAXIS2", 3), ("PCOUNT", 7), ("GCOUNT", 1),
                    ("TFIELDS", 1), ("TTYPE1", "WINDOW"), ("TFORM1", "1D"),
                    ("TUNIT1", "dimensionless"), ("EXTNAME", "WIN"),
                    ("COMMENT", "spectrum window, not amplitude transfer")])
    final = header([("XTENSION", "IMAGE"), ("BITPIX", 8), ("NAXIS", 0),
                    ("PCOUNT", 0), ("GCOUNT", 1), ("EXTNAME", "LAST")])
    payload = primary + table + b"\0" * 2880 + final
    stream = fixture_tar([("unsafe/../sample.fits", payload, tarfile.REGTYPE),
                          ("README", b"release R3.01\n", tarfile.REGTYPE),
                          ("README", b"a second literal member\n", tarfile.REGTYPE),
                          ("link", b"", tarfile.SYMTYPE)])
    result = module.inspect_stream(stream)
    assert result["coverage"] == "COMPLETE_PERMITTED_METADATA_INSPECTION"
    assert result["resources"]["decompressed_bytes_including_skip"] == len(stream.getvalue())
    hdus = result["members"][0]["fits_headers"]
    assert len(hdus) == 3 and hdus[1]["data_bytes"] == 31
    assert hdus[2]["member_byte_offset"] == 8640
    assert result["members"][1]["literal_name"] == result["members"][2]["literal_name"]
    assert result["members"][1]["ordinal"] != result["members"][2]["ordinal"]
    assert result["members"][3]["inspection"] == "NONREGULAR_NOT_FOLLOWED"


def test_byte_cap_charges_skipped_data_and_preserves_first_header():
    payload = header([("SIMPLE", True), ("BITPIX", 8), ("NAXIS", 1), ("NAXIS1", 200000)])
    payload += b"\0" * module.padded(200000, 2880)
    result = module.inspect_stream(fixture_tar([("large.fits", payload, tarfile.REGTYPE)]),
                                   module.Limits(decompressed=10000))
    assert result["coverage"] == "INTAKE_INCOMPLETE"
    assert "decompressed-byte limit" in result["obstruction"]["message"]
    assert result["resources"]["decompressed_bytes_including_skip"] <= 10000
    assert len(result["members"][0]["fits_headers"]) == 1


def test_member_metadata_and_wall_caps_are_incomplete():
    members = [("README", b"a" * 6000, tarfile.REGTYPE)] * 2
    for limits, reason in [(module.Limits(members=1), "member-count"),
                           (module.Limits(metadata=100), "metadata limit"),
                           (module.Limits(item=1000), "per-item"),
                           (module.Limits(seconds=0), "wall-time")]:
        result = module.inspect_stream(fixture_tar(members), limits)
        assert result["coverage"] == "INTAKE_INCOMPLETE"
        assert reason in result["obstruction"]["message"]


def test_nested_compression_and_bad_fits_are_incomplete():
    for name, payload in [("nested.gz", b"\x1f\x8b" + b"\0" * 4000),
                          ("bad.fits", b"not a fits file")]:
        result = module.inspect_stream(fixture_tar([(name, payload, tarfile.REGTYPE)]))
        assert result["coverage"] == "INTAKE_INCOMPLETE"


def test_pax_literal_and_effective_names_are_indexed():
    name = "long/" * 40 + "README"
    result = module.inspect_stream(fixture_tar([(name, b"release declaration", tarfile.REGTYPE)]))
    assert result["coverage"] == "COMPLETE_PERMITTED_METADATA_INSPECTION"
    assert result["members"][0]["inspection"] == "TAR_EXTENSION_METADATA"
    assert result["members"][1]["effective_name"] == name


def test_invalid_fits_span_is_not_silent_eof():
    payload = header([("SIMPLE", True), ("BITPIX", 8), ("NAXIS", 1), ("NAXIS1", 10000)])
    result = module.inspect_stream(fixture_tar([("sample.fits", payload, tarfile.REGTYPE)]))
    assert result["coverage"] == "INTAKE_INCOMPLETE"
    assert "span exceeds" in result["obstruction"]["message"]
