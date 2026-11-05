"""PM due scan DomainProgram (claim backlog + wake on PM complete)."""

from __future__ import annotations

import json
from typing import Any

from goliath_factory.db import connect, libpq_configured


def handle_pm_due_scan(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not libpq_configured():
        return {"skipped": True, "reason": "database not configured"}
    site_id = int(payload["site_id"])
    within_days = int(payload.get("within_days", 7))
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM fac_maint.v_asset v
                WHERE v.site_id = %s
                  AND v.next_due_on IS NOT NULL
                  AND v.next_due_on <= (CURRENT_DATE + %s)
                """,
                (site_id, within_days),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("COUNT query returned no row")
            due_count = int(row[0])
            cur.execute(
                "SELECT fac_maint.sp_record_pm_scan_result(%s, %s, %s::jsonb)",
                (
                    site_id,
                    due_count,
                    json.dumps({"within_days": within_days}),
                ),
            )
        conn.commit()
    return {"site_id": site_id, "due_asset_count": due_count, "within_days": within_days}


def enqueue_pm_due_backlog(within_days: int = 7) -> int:
    if not libpq_configured():
        return 0
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT fac_maint.sp_enqueue_pm_due_backlog(%s)", (within_days,))
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("sp_enqueue_pm_due_backlog returned no row")
            count = int(row[0])
        conn.commit()
    return count
