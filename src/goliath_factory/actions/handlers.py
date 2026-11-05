"""In-process handlers for GoliathFactory domain actions."""

from __future__ import annotations

import json
from typing import Any

from goliath_factory.actions.models import (
    InspectionResultRecordInput,
    InspectionResultRecordOutput,
    InvIssueToWorkOrderStubInput,
    InvIssueToWorkOrderStubOutput,
    InvReceiveStubInput,
    InvReceiveStubOutput,
    LotCocGenerateInput,
    LotCocGenerateOutput,
    NcrDispositionInput,
    NcrDispositionOutput,
    NcrOpenInput,
    NcrOpenOutput,
    TravelerStepSignOffInput,
    TravelerStepSignOffOutput,
    TravelerStepStartInput,
    TravelerStepStartOutput,
    WorkOrderReleaseInput,
    WorkOrderReleaseOutput,
)
from goliath_factory.db import connect, libpq_configured, user_id_from_context


def _require_db_user(context: dict[str, Any] | None) -> int:
    user_id = user_id_from_context(context)
    if user_id is None or not libpq_configured():
        raise RuntimeError("action requires authenticated user and database configuration")
    return user_id


def _fetch_one(cur, label: str) -> tuple[Any, ...]:
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"{label} returned no row")
    return row


def handle_work_order_release(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = WorkOrderReleaseInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT fac_prod.sp_work_order_release(%s, %s)",
                (user_id, model.work_order_id),
            )
            status = str(_fetch_one(cur, "sp_work_order_release")[0])
        conn.commit()
    return WorkOrderReleaseOutput(work_order_id=model.work_order_id, status=status).model_dump(
        mode="json"
    )


def handle_traveler_step_start(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = TravelerStepStartInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT fac_prod.sp_traveler_step_start(%s, %s, %s)",
                (user_id, model.traveler_step_id, model.machine),
            )
            status = str(_fetch_one(cur, "sp_traveler_step_start")[0])
        conn.commit()
    return TravelerStepStartOutput(traveler_step_id=model.traveler_step_id, status=status).model_dump(
        mode="json"
    )


def handle_traveler_step_sign_off(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = TravelerStepSignOffInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_prod.sp_traveler_step_sign_off(
                  %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    user_id,
                    model.traveler_step_id,
                    model.qty_good,
                    model.qty_scrap,
                    model.machine,
                    model.signature_meaning,
                    model.record_hash,
                ),
            )
            signed_at = _fetch_one(cur, "sp_traveler_step_sign_off")[0]
        conn.commit()
    return TravelerStepSignOffOutput(
        traveler_step_id=model.traveler_step_id,
        status="complete",
        signed_at=signed_at.isoformat() if hasattr(signed_at, "isoformat") else str(signed_at),
    ).model_dump(mode="json")


def handle_inspection_result_record(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = InspectionResultRecordInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_qual.sp_inspection_result_record(
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    user_id,
                    model.characteristic_id,
                    model.lot_id,
                    model.work_order_id,
                    model.piece_number,
                    model.measured_value,
                    model.pass_fail,
                    model.gauge_id,
                    model.signature_meaning,
                    model.record_hash,
                ),
            )
            result_id = int(_fetch_one(cur, "sp_inspection_result_record")[0])
        conn.commit()
    pass_fail = model.pass_fail or "pass"
    return InspectionResultRecordOutput(
        inspection_result_id=result_id,
        pass_fail=pass_fail,
    ).model_dump(mode="json")


def handle_ncr_open(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = NcrOpenInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_qual.sp_ncr_open(
                  %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    user_id,
                    model.site_id,
                    model.defect_code,
                    model.description,
                    model.part_revision_id,
                    model.lot_id,
                    model.work_order_id,
                    model.containment,
                ),
            )
            ncr_id = int(_fetch_one(cur, "sp_ncr_open")[0])
        conn.commit()
    return NcrOpenOutput(ncr_id=ncr_id, status="open").model_dump(mode="json")


def handle_ncr_disposition(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = NcrDispositionInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_qual.sp_ncr_disposition(%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    model.ncr_id,
                    model.disposition,
                    model.signature_meaning,
                    model.record_hash,
                ),
            )
            disposition = str(_fetch_one(cur, "sp_ncr_disposition")[0])
        conn.commit()
    return NcrDispositionOutput(
        ncr_id=model.ncr_id,
        disposition=disposition,
        status="dispositioned",
    ).model_dump(mode="json")


def handle_lot_coc_generate(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = LotCocGenerateInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT fac_trace.sp_lot_coc_generate(%s, %s)",
                (user_id, model.lot_id),
            )
            raw = _fetch_one(cur, "sp_lot_coc_generate")[0]
        conn.commit()
    if isinstance(raw, str):
        document = json.loads(raw)
    elif isinstance(raw, dict):
        document = raw
    else:
        document = dict(raw) if raw is not None else {}
    return LotCocGenerateOutput(lot_id=model.lot_id, document=document).model_dump(mode="json")


def handle_inv_receive_stub(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = InvReceiveStubInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_inv_hooks.sp_receive_with_inspection(%s, %s, %s, %s, %s)
                """,
                (user_id, model.site_id, model.item_ref, model.quantity, model.lot_number),
            )
            detail = _fetch_one(cur, "sp_receive_with_inspection")[0]
        conn.commit()
    if isinstance(detail, str):
        detail = json.loads(detail)
    return InvReceiveStubOutput(
        status=str(detail.get("status", "stub")),
        dependency=str(detail.get("dependency", "GoliathApp inv module")),
        detail=detail,
    ).model_dump(mode="json")


def handle_inv_issue_to_work_order_stub(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = InvIssueToWorkOrderStubInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_inv_hooks.sp_issue_to_work_order(%s, %s, %s, %s)
                """,
                (user_id, model.work_order_id, model.stock_lot_ref, model.quantity),
            )
            detail = _fetch_one(cur, "sp_issue_to_work_order")[0]
        conn.commit()
    if isinstance(detail, str):
        detail = json.loads(detail)
    return InvIssueToWorkOrderStubOutput(
        status=str(detail.get("status", "stub")),
        dependency=str(detail.get("dependency", "GoliathApp inv module")),
        detail=detail,
    ).model_dump(mode="json")
