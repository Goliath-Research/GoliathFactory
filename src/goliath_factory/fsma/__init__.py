"""FSMA 204 traceability export helpers."""

from __future__ import annotations

import csv
import io
from typing import Iterable, Mapping


FSMA_CSV_HEADER = (
    "event_at_utc",
    "cte_type",
    "traceability_lot_code",
    "product_description",
    "quantity",
    "quantity_uom",
    "location_code",
    "reference_doc_type",
    "reference_doc_number",
    "lot_number",
    "lot_id",
    "source",
)


def rows_to_traceability_csv(rows: Iterable[Mapping[str, object]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(FSMA_CSV_HEADER)
    for row in rows:
        writer.writerow(
            [
                row.get("event_at_utc") or row.get("event_at") or "",
                row.get("cte_type", ""),
                row.get("traceability_lot_code", ""),
                row.get("product_description", ""),
                row.get("quantity", ""),
                row.get("quantity_uom", ""),
                row.get("location_code", ""),
                row.get("reference_doc_type", ""),
                row.get("reference_doc_number", ""),
                row.get("lot_number", ""),
                row.get("lot_id", ""),
                row.get("source", ""),
            ]
        )
    return buffer.getvalue()
