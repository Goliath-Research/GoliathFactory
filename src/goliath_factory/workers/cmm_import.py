"""CMM import DomainProgram — parse CSV stub into inspection results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from goliath_factory.cmm import parse_cmm_export
from goliath_factory.db import connect, libpq_configured


def handle_cmm_import_file(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not libpq_configured():
        return {"skipped": True, "reason": "database not configured"}
    batch_id = int(payload["batch_id"])
    site_id = int(payload["site_id"])
    storage_ref = payload.get("storage_ref")
    file_format = str(payload.get("format", "csv"))
    text = _load_text(storage_ref)
    parsed = parse_cmm_export(text, format=file_format)
    inserted = 0
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE fac_qual.cmm_import_batches
                SET status = 'processing', rows_parsed = %s
                WHERE id = %s
                """,
                (len(parsed.rows), batch_id),
            )
            for row in parsed.rows:
                cur.execute(
                    """
                    SELECT ic.id
                    FROM fac_qual.inspection_characteristics ic
                    JOIN fac_qual.inspection_plans ip ON ip.id = ic.inspection_plan_id
                    WHERE ip.site_id = %s AND ic.characteristic_code = %s
                    LIMIT 1
                    """,
                    (site_id, row.characteristic_code),
                )
                char_row = cur.fetchone()
                if char_row is None:
                    continue
                characteristic_id = int(char_row[0])
                lot_id = None
                if row.lot_number:
                    cur.execute(
                        """
                        SELECT id FROM fac_trace.lots
                        WHERE site_id = %s AND lot_number = %s
                        LIMIT 1
                        """,
                        (site_id, row.lot_number),
                    )
                    lot_hit = cur.fetchone()
                    lot_id = int(lot_hit[0]) if lot_hit else None
                cur.execute(
                    """
                    INSERT INTO fac_qual.inspection_results (
                      characteristic_id,
                      lot_id,
                      piece_number,
                      measured_value,
                      pass_fail
                    )
                    VALUES (%s, %s, %s, %s, 'pass')
                    """,
                    (characteristic_id, lot_id, row.piece_number, row.measured_value),
                )
                inserted += 1
            if parsed.warnings and inserted == 0:
                status = "failed"
            elif parsed.rows and inserted == 0:
                status = "failed"
            else:
                status = "completed"
            error_summary = "; ".join(parsed.warnings) if parsed.warnings else None
            if status == "failed" and not error_summary and parsed.rows and inserted == 0:
                error_summary = "no matching inspection characteristics for parsed rows"
            cur.execute(
                """
                UPDATE fac_qual.cmm_import_batches
                SET
                  status = %s,
                  rows_inserted = %s,
                  error_summary = %s,
                  processed_at = now()
                WHERE id = %s
                """,
                (
                    status,
                    inserted,
                    error_summary,
                    batch_id,
                ),
            )
        conn.commit()
    return {
        "batch_id": batch_id,
        "rows_parsed": len(parsed.rows),
        "rows_inserted": inserted,
        "warnings": list(parsed.warnings),
    }


def _load_text(storage_ref: str | None) -> str:
    if not storage_ref:
        return ""
    path = Path(storage_ref)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    if storage_ref.strip().startswith("{"):
        data = json.loads(storage_ref)
        if isinstance(data, dict) and "csv" in data:
            return str(data["csv"])
    return storage_ref
