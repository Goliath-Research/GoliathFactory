"""CMM / inspection file import parsers (stub)."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass


@dataclass(frozen=True)
class CmmParsedRow:
    characteristic_code: str
    piece_number: int
    measured_value: float
    lot_number: str | None = None


@dataclass(frozen=True)
class CmmParseResult:
    rows: tuple[CmmParsedRow, ...]
    format: str
    warnings: tuple[str, ...]


def parse_cmm_csv(text: str) -> CmmParseResult:
    """Parse a minimal CSV export (characteristic_code, piece_number, measured_value[, lot_number])."""
    warnings: list[str] = []
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return CmmParseResult(rows=(), format="csv", warnings=("empty file",))
    normalized = {name.strip().lower(): name for name in reader.fieldnames}
    for required in ("characteristic_code", "piece_number", "measured_value"):
        if required not in normalized:
            warnings.append(f"missing column {required}")
            return CmmParseResult(rows=(), format="csv", warnings=tuple(warnings))
    rows: list[CmmParsedRow] = []
    for line_no, row in enumerate(reader, start=2):
        try:
            code = row[normalized["characteristic_code"]].strip()
            piece = int(row[normalized["piece_number"]])
            value = float(row[normalized["measured_value"]])
        except (KeyError, TypeError, ValueError):
            warnings.append(f"skip line {line_no}: invalid row")
            continue
        lot_key = normalized.get("lot_number")
        lot_number = row[lot_key].strip() if lot_key and row.get(lot_key) else None
        rows.append(
            CmmParsedRow(
                characteristic_code=code,
                piece_number=piece,
                measured_value=value,
                lot_number=lot_number or None,
            )
        )
    return CmmParseResult(rows=tuple(rows), format="csv", warnings=tuple(warnings))


def parse_cmm_export(text: str, *, format: str = "csv") -> CmmParseResult:
    fmt = format.lower()
    if fmt in ("csv", "pcdmis_csv"):
        return parse_cmm_csv(text)
    return CmmParseResult(
        rows=(),
        format=fmt,
        warnings=(f"unsupported format {format!r} (see docs/cmm-import.md)",),
    )
