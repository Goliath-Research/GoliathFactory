"""CMM parser tests."""

from __future__ import annotations

from goliath_factory.cmm import parse_cmm_csv, parse_cmm_export


def test_parse_csv_rows() -> None:
    text = "characteristic_code,piece_number,measured_value\nDIA_1,1,10.005\n"
    result = parse_cmm_csv(text)
    assert len(result.rows) == 1
    assert result.rows[0].characteristic_code == "DIA_1"
    assert result.rows[0].measured_value == 10.005


def test_unsupported_format_warning() -> None:
    result = parse_cmm_export("", format="dmis_binary")
    assert result.rows == ()
    assert result.warnings
