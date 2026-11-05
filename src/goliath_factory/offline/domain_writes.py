"""Run offline-capable domain writes on an existing database cursor (no commit)."""

from __future__ import annotations

from typing import Any

from goliath_factory.actions.models import (
    InspectionResultRecordInput,
    InspectionResultRecordOutput,
    TravelerStepSignOffInput,
    TravelerStepSignOffOutput,
    TravelerStepStartInput,
    TravelerStepStartOutput,
)


def _fetch_one(cur, label: str) -> tuple[Any, ...]:
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"{label} returned no row")
    return row


def traveler_step_start_on_cursor(
    cur,
    user_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    model = TravelerStepStartInput.model_validate(payload)
    cur.execute(
        "SELECT fac_prod.sp_traveler_step_start(%s, %s, %s)",
        (user_id, model.traveler_step_id, model.machine),
    )
    status = str(_fetch_one(cur, "sp_traveler_step_start")[0])
    return TravelerStepStartOutput(traveler_step_id=model.traveler_step_id, status=status).model_dump(
        mode="json"
    )


def traveler_step_sign_off_on_cursor(
    cur,
    user_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    model = TravelerStepSignOffInput.model_validate(payload)
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
    return TravelerStepSignOffOutput(
        traveler_step_id=model.traveler_step_id,
        status="complete",
        signed_at=signed_at.isoformat() if hasattr(signed_at, "isoformat") else str(signed_at),
    ).model_dump(mode="json")


def inspection_result_record_on_cursor(
    cur,
    user_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    model = InspectionResultRecordInput.model_validate(payload)
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
    pass_fail = model.pass_fail or "pass"
    return InspectionResultRecordOutput(
        inspection_result_id=result_id,
        pass_fail=pass_fail,
    ).model_dump(mode="json")
