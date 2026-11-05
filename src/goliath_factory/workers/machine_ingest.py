"""DomainProgram handler: ingest MTConnect/OPC UA observation stubs."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from goliath_factory.actions.models import MachineIngestObservationInput, MachineIngestObservationOutput
from goliath_factory.db import connect, libpq_configured
from goliath_factory.machine import parse_mtconnect_sample, parse_opcua_payload


def _require_db_user(context: dict[str, Any] | None) -> int:
    if not context or context.get("user_id") is None:
        raise RuntimeError("database configuration requires user_id in context")
    return int(context["user_id"])


def handle_machine_ingest_observation(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = MachineIngestObservationInput.model_validate(payload)
    if not libpq_configured():
        parsed = _parse_without_db(model)
        return MachineIngestObservationOutput(
            observation_id=0,
            downtime_event_id=None,
            incomplete_edges=parsed["incomplete_edges"],
            demo=True,
        ).model_dump(mode="json")

    user_id = _require_db_user(context)
    parsed = _parse_without_db(model)
    observed_at = model.observed_at or datetime.utcnow()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_maint.sp_machine_record_observation(
                  %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::text[]
                )
                """,
                (
                    user_id,
                    model.site_id,
                    model.asset_id,
                    model.source_protocol,
                    observed_at,
                    parsed.get("availability"),
                    parsed.get("execution_state"),
                    json.dumps(parsed.get("raw_payload", {})),
                    parsed.get("incomplete_edges", []),
                ),
            )
            row_id = cur.fetchone()
            if row_id is None:
                raise RuntimeError("sp_machine_record_observation returned no row")
            observation_id = int(row_id[0])
            cur.execute(
                """
                SELECT downtime_event_id
                FROM fac_maint.machine_observations
                WHERE id = %s
                """,
                (observation_id,),
            )
            row = cur.fetchone()
        conn.commit()
    downtime_id = int(row[0]) if row and row[0] is not None else None
    return MachineIngestObservationOutput(
        observation_id=observation_id,
        downtime_event_id=downtime_id,
        incomplete_edges=list(parsed.get("incomplete_edges", [])),
        demo=False,
    ).model_dump(mode="json")


def _parse_without_db(model: MachineIngestObservationInput) -> dict[str, Any]:
    if model.source_protocol == "mtconnect":
        if not model.mtconnect_xml:
            raise ValueError("mtconnect_xml required for mtconnect protocol")
        return parse_mtconnect_sample(model.mtconnect_xml)
    if model.opcua_payload is None:
        raise ValueError("opcua_payload required for opcua protocol")
    return parse_opcua_payload(model.opcua_payload)
