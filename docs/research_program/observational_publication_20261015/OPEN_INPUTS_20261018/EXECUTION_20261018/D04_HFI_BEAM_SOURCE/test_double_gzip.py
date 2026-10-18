"""Approved small synthetic format-amendment controls; no official source read."""
import gzip
import io

from inspect_double_gzip import SharedMeter, inspect_two_layers
from test_inspect_source import fixture_tar
import tarfile


def payload():
    return fixture_tar([("README", b"release fixture, not official evidence", tarfile.REGTYPE)]).getvalue()


def test_valid_double_gzip_charges_both_layers_and_prior():
    tar = payload()
    inner = gzip.compress(tar)
    result = inspect_two_layers(io.BytesIO(gzip.compress(inner)), SharedMeter(prior=1536))
    assert result["coverage"] == "COMPLETE_PERMITTED_METADATA_INSPECTION"
    assert result["gzip_trailers"] == "BOTH_LAYERS_EOF_CRC_VALIDATED"
    assert result["two_layer_resources"]["outer_gzip_decoded"] == len(inner)
    assert result["two_layer_resources"]["inner_gzip_decoded"] == len(tar)
    assert result["two_layer_resources"]["cumulative_decompressed_bytes_all_layers"] == len(inner) + len(tar) + 1536


def test_corrupt_inner_gzip_trailer_is_incomplete():
    inner = bytearray(gzip.compress(payload()))
    inner[-8] ^= 1
    result = inspect_two_layers(io.BytesIO(gzip.compress(inner)))
    assert result["coverage"] == "INTAKE_INCOMPLETE"
    assert "CRC check failed" in result["obstruction"]["message"]


def test_corrupt_outer_gzip_trailer_is_incomplete():
    outer = bytearray(gzip.compress(gzip.compress(payload())))
    outer[-8] ^= 1
    result = inspect_two_layers(io.BytesIO(outer))
    assert result["coverage"] == "INTAKE_INCOMPLETE"
    assert "CRC check failed" in result["obstruction"]["message"]


def test_invalid_tar_checksum_is_incomplete():
    tar = bytearray(payload())
    tar[0] ^= 1
    result = inspect_two_layers(io.BytesIO(gzip.compress(gzip.compress(tar))))
    assert result["coverage"] == "INTAKE_INCOMPLETE"
    assert "checksum" in result["obstruction"]["message"]


def test_third_compression_layer_is_rejected():
    result = inspect_two_layers(io.BytesIO(gzip.compress(gzip.compress(gzip.compress(payload())))))
    assert result["coverage"] == "INTAKE_INCOMPLETE"
    assert "third compression layer rejected" in result["obstruction"]["message"]


def test_shared_cumulative_cap_includes_reservations_and_prior():
    meter = SharedMeter(cap=1536 + 10000, prior=1536)
    result = inspect_two_layers(io.BytesIO(gzip.compress(gzip.compress(payload()))), meter)
    assert result["coverage"] == "INTAKE_INCOMPLETE"
    assert "shared two-layer" in result["obstruction"]["message"]
    assert result["two_layer_resources"]["cumulative_decompressed_bytes_all_layers"] <= 11536
    assert meter.reserved == 0
