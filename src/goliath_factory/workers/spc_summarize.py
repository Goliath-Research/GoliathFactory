"""SPC summarize DomainProgram — writes fac_qual.spc_chart_points."""

from __future__ import annotations

from typing import Any, Literal

from goliath_factory.db import connect, libpq_configured
from goliath_factory.spc import compute_chart

ChartType = Literal["xbar_r", "imr"]


def handle_spc_summarize(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not libpq_configured():
        return {"skipped": True, "reason": "database not configured"}
    characteristic_id = int(payload["characteristic_id"])
    chart_type: ChartType = payload.get("chart_type", "xbar_r")
    subgroup_size = int(payload.get("subgroup_size", 5))
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ir.measured_value::float
                FROM fac_qual.inspection_results ir
                WHERE ir.characteristic_id = %s
                  AND ir.measured_value IS NOT NULL
                ORDER BY ir.recorded_at, ir.id
                """,
                (characteristic_id,),
            )
            values = [float(row[0]) for row in cur.fetchall()]
            points = compute_chart(chart_type, values, subgroup_size=subgroup_size)
            cur.execute(
                """
                DELETE FROM fac_qual.spc_chart_points
                WHERE characteristic_id = %s AND chart_type = %s
                """,
                (characteristic_id, chart_type),
            )
            for point in points:
                cur.execute(
                    """
                    INSERT INTO fac_qual.spc_chart_points (
                      characteristic_id,
                      chart_type,
                      point_index,
                      subgroup_label,
                      primary_value,
                      secondary_value,
                      center_line,
                      ucl,
                      lcl,
                      rule_violations
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        characteristic_id,
                        chart_type,
                        point.point_index,
                        point.subgroup_label,
                        point.primary_value,
                        point.secondary_value,
                        point.center_line,
                        point.ucl,
                        point.lcl,
                        ",".join(point.rule_violations) if point.rule_violations else None,
                    ),
                )
        conn.commit()
    return {
        "characteristic_id": characteristic_id,
        "chart_type": chart_type,
        "points_written": len(points),
    }


def enqueue_spc_backlog() -> int:
    if not libpq_configured():
        return 0
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT fac_qual.sp_enqueue_spc_backlog()")
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("sp_enqueue_spc_backlog returned no row")
            count = int(row[0])
        conn.commit()
    return count
