"""Idempotent Factory NavTree registration via portal.sp_nav_register_node."""

from __future__ import annotations

import os
import sys

NAV_SPEC = (
    ("Factory", None, 25, "mfg_root", "mfg"),
    ("Work orders", "Factory", 10, "mfg_work_orders", "mfg.work_order.list_open"),
    ("Shop floor (traveler)", "Factory", 20, "mfg_shop_floor", "mfg.traveler_step.by_work_order"),
    ("Quality", "Factory", 25, "mfg_quality", "mfg"),
    ("Inspections", "Quality", 10, "mfg_inspections", "mfg.inspection_result.by_lot"),
    ("NCR / CAPA", "Quality", 20, "mfg_ncr", "mfg.ncr.list_open"),
    ("First article (FAI)", "Quality", 30, "mfg_fai", "mfg.fai.by_work_order"),
    ("Document control", "Quality", 40, "mfg_documents", "mfg.document.list"),
    ("Gauges", "Factory", 28, "mfg_gauges", "mfg.gauge.due_calibration"),
    ("Maintenance", "Factory", 29, "mfg_maintenance", "mfg.asset.pm_due"),
    ("SPC", "Quality", 35, "mfg_spc", "mfg.spc.series"),
    ("Traceability", "Factory", 30, "mfg_traceability", "mfg.lot.genealogy"),
    ("FSMA trace (204)", "Factory", 31, "mfg_fsma_trace", "mfg.fsma.cte_in_window"),
    ("Inventory & purchasing", "Factory", 35, "mfg_inv", "inv.item.list"),
    ("Receiving", "Factory", 36, "mfg_receiving", "inv.stock.receive"),
)


def _connect():
    import psycopg

    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ.get("PGPASSWORD"),
    )


def _ensure_node_info(cur, name: str, frame_key: str) -> int:
    cur.execute(
        """
        SELECT "Id" FROM portal."NodeInfos" WHERE "Name" = %s
        """,
        (name,),
    )
    row = cur.fetchone()
    if row:
        info_id = int(row[0])
        cur.execute(
            """
            UPDATE portal."NodeInfos"
            SET "FrameKey" = %s
            WHERE "Id" = %s AND "FrameKey" IS DISTINCT FROM %s
            """,
            (frame_key, info_id, frame_key),
        )
        return info_id
    cur.execute(
        """
        INSERT INTO portal."NodeInfos" ("Name", "Singleton", "TypeId", "FrameKey")
        VALUES (%s, true, 1, %s)
        RETURNING "Id"
        """,
        (name, frame_key),
    )
    return int(cur.fetchone()[0])


def _find_node(cur, caption: str, parent_id: int | None) -> int | None:
    if parent_id is None:
        cur.execute(
            """
            SELECT "ID" FROM portal."NavTree"
            WHERE "Caption" = %s AND "ParentID" IS NULL
            """,
            (caption,),
        )
    else:
        cur.execute(
            """
            SELECT "ID" FROM portal."NavTree"
            WHERE "Caption" = %s AND "ParentID" = %s
            """,
            (caption, parent_id),
        )
    row = cur.fetchone()
    return int(row[0]) if row else None


def seed(conn) -> int:
    created = 0
    node_ids: dict[str, int] = {}
    with conn.cursor() as cur:
        for caption, parent_caption, seq, info_name, frame_key in NAV_SPEC:
            parent_id = node_ids.get(parent_caption) if parent_caption else None
            info_id = _ensure_node_info(cur, info_name, frame_key or info_name)
            existing = _find_node(cur, caption, parent_id)
            if existing is not None:
                node_ids[caption] = existing
                continue
            cur.execute(
                """
                SELECT node_id FROM portal.sp_nav_register_node(%s, %s, %s::smallint, %s)
                """,
                (parent_id, caption, seq, info_id),
            )
            node_ids[caption] = int(cur.fetchone()[0])
            created += 1
    conn.commit()
    return created


def main() -> int:
    if not os.environ.get("PGHOST"):
        print("Set PGHOST/PGDATABASE/PGUSER for goliath-factory-seed-nav", file=sys.stderr)
        return 2
    with _connect() as conn:
        n = seed(conn)
    print(f"Registered {n} new Factory NavTree nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
