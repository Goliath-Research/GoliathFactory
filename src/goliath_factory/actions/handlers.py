"""In-process handlers for GoliathFactory domain actions."""

from __future__ import annotations

import json
from typing import Any

from goliath_app.inv.models import IssueStockStubInput

from goliath_factory.actions.models import (
    CapaCloseInput,
    CapaCloseOutput,
    DocumentApproveInput,
    DocumentApproveOutput,
    DocumentSubmitReviewInput,
    DocumentSubmitReviewOutput,
    FaiApproveInput,
    FaiApproveOutput,
    FaiStartInput,
    FaiStartOutput,
    AssetPmCompleteInput,
    AssetPmCompleteOutput,
    CmmRegisterUploadInput,
    CmmRegisterUploadOutput,
    DowntimeLogInput,
    DowntimeLogOutput,
    FsmaExport24hInput,
    FsmaExport24hOutput,
    FsmaRecordCteInput,
    FsmaRecordCteOutput,
    GaugeLockoutCheckInput,
    GaugeLockoutCheckOutput,
    InspectionResultRecordInput,
    InspectionResultRecordOutput,
    InvIssueToWorkOrderInput,
    InvIssueToWorkOrderOutput,
    LotCocGenerateInput,
    LotCocGenerateOutput,
    OfflineEnqueueInput,
    OfflineEnqueueOutput,
    OfflineSyncInput,
    OfflineSyncOutput,
    OfflineSyncResultItem,
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
from goliath_factory.inv.models import MfgIssueStockOutput, MfgReceiveStockInput, MfgReceiveStockOutput
from goliath_factory.db import connect, libpq_configured, user_id_from_context
from goliath_factory.offline import ALLOWED_OFFLINE_ACTIONS, MAX_PAYLOAD_BYTES
from goliath_factory.offline.permissions import assert_offline_domain_permission
from goliath_factory.offline.sync import apply_offline_submission


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


def handle_capa_close(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = CapaCloseInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_qual.sp_capa_close(%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    model.capa_id,
                    model.effectiveness_notes,
                    model.signature_meaning,
                    model.record_hash,
                ),
            )
            status = str(_fetch_one(cur, "sp_capa_close")[0])
        conn.commit()
    return CapaCloseOutput(capa_id=model.capa_id, status=status).model_dump(mode="json")


def handle_gauge_lockout_check(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = GaugeLockoutCheckInput.model_validate(payload)
    _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT fac_gauge.sp_lockout_check(%s)",
                (model.gauge_id,),
            )
            locked = bool(_fetch_one(cur, "sp_lockout_check")[0])
    return GaugeLockoutCheckOutput(gauge_id=model.gauge_id, locked_out=locked).model_dump(
        mode="json"
    )


def handle_fai_start(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = FaiStartInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT fac_qual.sp_fai_start(%s, %s, %s)",
                (user_id, model.work_order_id, model.inspection_plan_id),
            )
            fai_id = int(_fetch_one(cur, "sp_fai_start")[0])
        conn.commit()
    return FaiStartOutput(first_article_id=fai_id, status="in_progress").model_dump(mode="json")


def handle_fai_approve(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = FaiApproveInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT fac_qual.sp_fai_approve(%s, %s, %s, %s)",
                (
                    user_id,
                    model.first_article_id,
                    model.signature_meaning,
                    model.record_hash,
                ),
            )
            status = str(_fetch_one(cur, "sp_fai_approve")[0])
        conn.commit()
    return FaiApproveOutput(first_article_id=model.first_article_id, status=status).model_dump(
        mode="json"
    )


def handle_document_submit_review(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = DocumentSubmitReviewInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT fac_doc.sp_document_submit_review(%s, %s, %s)",
                (user_id, model.revision_id, model.change_summary),
            )
            status = str(_fetch_one(cur, "sp_document_submit_review")[0])
        conn.commit()
    return DocumentSubmitReviewOutput(revision_id=model.revision_id, status=status).model_dump(
        mode="json"
    )


def handle_document_approve(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = DocumentApproveInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_doc.sp_document_approve(%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    model.revision_id,
                    model.signature_meaning,
                    model.record_hash,
                    model.effective_on,
                ),
            )
            status = str(_fetch_one(cur, "sp_document_approve")[0])
        conn.commit()
    return DocumentApproveOutput(revision_id=model.revision_id, status=status).model_dump(
        mode="json"
    )


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


def handle_inv_stock_receive(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = MfgReceiveStockInput.model_validate(payload)
    user_id = model.user_id or _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT receipt_id, stock_lot_id, avg_unit_cost, trace_lot_id
                FROM fac_mfg_inv.sp_receive_with_inspection(
                  %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    model.organization_id,
                    user_id,
                    model.po_line_id,
                    model.bin_id,
                    model.qty,
                    model.lot_number,
                    model.unit_price_override,
                    model.site_id,
                ),
            )
            row = _fetch_one(cur, "sp_receive_with_inspection")
        conn.commit()
    return MfgReceiveStockOutput(
        receipt_id=int(row[0]),
        stock_lot_id=int(row[1]),
        avg_unit_cost=float(row[2]),
        trace_lot_id=int(row[3]) if row[3] is not None else None,
    ).model_dump(mode="json")


def handle_inv_stock_issue(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = IssueStockStubInput.model_validate(payload)
    user_id = model.user_id or _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT stock_move_id, qty_on_hand, genealogy_link_id
                FROM fac_mfg_inv.sp_issue_with_genealogy(
                  %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    model.organization_id,
                    user_id,
                    model.stock_lot_id,
                    model.qty,
                    model.ref_type,
                    model.ref_id,
                ),
            )
            row = _fetch_one(cur, "sp_issue_with_genealogy")
        conn.commit()
    return MfgIssueStockOutput(
        stock_move_id=int(row[0]),
        qty_on_hand=float(row[1]),
        genealogy_link_id=int(row[2]) if row[2] is not None else None,
    ).model_dump(mode="json")


def handle_inv_issue_to_work_order(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = InvIssueToWorkOrderInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT stock_move_id, qty_on_hand, genealogy_link_id
                FROM fac_mfg_inv.sp_issue_to_work_order(%s, %s, %s, %s, %s)
                """,
                (
                    model.organization_id,
                    user_id,
                    model.work_order_id,
                    model.stock_lot_id,
                    model.quantity,
                ),
            )
            row = _fetch_one(cur, "sp_issue_to_work_order")
        conn.commit()
    return InvIssueToWorkOrderOutput(
        work_order_id=model.work_order_id,
        stock_move_id=int(row[0]),
        qty_on_hand=float(row[1]),
        genealogy_link_id=int(row[2]) if row[2] is not None else None,
    ).model_dump(mode="json")


def handle_asset_pm_complete(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = AssetPmCompleteInput.model_validate(payload)
    user_id = _require_db_user(context)
    checklist_json = json.dumps(model.checklist) if model.checklist else None
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_maint.sp_pm_complete(%s, %s, %s, %s, %s::jsonb)
                """,
                (
                    user_id,
                    model.maintenance_order_id,
                    model.signature_meaning,
                    model.record_hash,
                    checklist_json,
                ),
            )
            next_due = _fetch_one(cur, "sp_pm_complete")[0]
        conn.commit()
    return AssetPmCompleteOutput(
        maintenance_order_id=model.maintenance_order_id,
        next_due_on=next_due,
    ).model_dump(mode="json")


def handle_downtime_log(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = DowntimeLogInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_maint.sp_log_downtime(
                  %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    user_id,
                    model.site_id,
                    model.asset_id,
                    model.work_center_id,
                    model.started_at,
                    model.ended_at,
                    model.reason_code,
                    model.comments,
                ),
            )
            event_id = int(_fetch_one(cur, "sp_log_downtime")[0])
        conn.commit()
    return DowntimeLogOutput(downtime_event_id=event_id).model_dump(mode="json")


def handle_cmm_register_upload(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = CmmRegisterUploadInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_qual.sp_register_cmm_upload(%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    model.site_id,
                    model.source_filename,
                    model.format,
                    model.storage_ref,
                ),
            )
            batch_id = int(_fetch_one(cur, "sp_register_cmm_upload")[0])
        conn.commit()
    return CmmRegisterUploadOutput(batch_id=batch_id, status="pending").model_dump(mode="json")


def handle_fsma_record_cte(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = FsmaRecordCteInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_trace.sp_fsma_record_cte(
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    user_id,
                    model.site_id,
                    model.cte_type,
                    model.event_at,
                    model.traceability_lot_code,
                    model.product_description,
                    model.lot_id,
                    model.quantity,
                    model.quantity_uom,
                    model.location_code,
                    model.reference_doc_type,
                    model.reference_doc_number,
                    model.genealogy_link_id,
                    model.source,
                ),
            )
            cte_id = int(_fetch_one(cur, "sp_fsma_record_cte")[0])
        conn.commit()
    return FsmaRecordCteOutput(cte_event_id=cte_id).model_dump(mode="json")


def handle_fsma_export_24h(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = FsmaExport24hInput.model_validate(payload)
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fac_trace.sp_fsma_export_traceability_csv(%s, %s, %s)
                """,
                (user_id, model.site_id, model.window_hours),
            )
            csv_text = str(_fetch_one(cur, "sp_fsma_export_traceability_csv")[0])
            cur.execute(
                """
                SELECT row_count FROM fac_trace.fsma_traceability_exports
                WHERE site_id = %s
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (model.site_id,),
            )
            count_row = cur.fetchone()
        conn.commit()
    row_count = int(count_row[0]) if count_row else csv_text.count("\n")
    if csv_text.startswith("event_at_utc"):
        row_count = max(0, row_count)
    filename = f"fsma_traceability_site{model.site_id}_{model.window_hours}h.csv"
    return FsmaExport24hOutput(
        site_id=model.site_id,
        window_hours=model.window_hours,
        row_count=row_count,
        csv_text=csv_text,
        filename=filename,
    ).model_dump(mode="json")


def handle_offline_enqueue(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = OfflineEnqueueInput.model_validate(payload)
    if model.action_name not in ALLOWED_OFFLINE_ACTIONS:
        raise ValueError(f"action not allowed offline: {model.action_name}")
    encoded = json.dumps(model.payload, separators=(",", ":"), sort_keys=True)
    if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError("offline payload exceeds size limit")
    user_id = _require_db_user(context)
    with connect() as conn:
        with conn.cursor() as cur:
            assert_offline_domain_permission(model.action_name, context=context, cur=cur)
            cur.execute(
                """
                SELECT outbox_id, status
                FROM fac_prod.sp_offline_enqueue(
                  %s, %s, %s, %s, %s, %s::jsonb, %s
                )
                """,
                (
                    user_id,
                    model.site_id,
                    model.client_device_id,
                    model.idempotency_key,
                    model.action_name,
                    model.payload,
                    model.captured_at,
                ),
            )
            outbox_id, status = _fetch_one(cur, "sp_offline_enqueue")
        conn.commit()
    return OfflineEnqueueOutput(outbox_id=int(outbox_id), status=str(status)).model_dump(mode="json")


def handle_offline_sync(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = OfflineSyncInput.model_validate(payload)
    user_id = _require_db_user(context)
    max_batch = max(1, min(model.max_batch, 50))
    results: list[OfflineSyncResultItem] = []
    synced = 0
    conflicts = 0
    sync_context: dict[str, Any] = dict(context or {})
    sync_context.setdefault("user_id", user_id)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, idempotency_key, action_name, payload_json, status
                FROM fac_prod.sp_offline_claim_pending(
                  %s, %s, %s, %s
                )
                """,
                (user_id, model.site_id, model.client_device_id, max_batch),
            )
            rows = cur.fetchall()
            for outbox_id, idem_key, action_name, payload_json, status in rows:
                if status == "synced":
                    continue
                try:
                    body = payload_json if isinstance(payload_json, dict) else json.loads(payload_json)
                    result = apply_offline_submission(
                        str(action_name),
                        body,
                        context=sync_context,
                        cur=cur,
                    )
                    cur.execute(
                        """
                        SELECT fac_prod.sp_offline_finish_item(
                          %s, %s, 'synced', %s::jsonb, NULL
                        )
                        """,
                        (user_id, outbox_id, json.dumps(result)),
                    )
                    synced += 1
                    results.append(
                        OfflineSyncResultItem(
                            outbox_id=int(outbox_id),
                            idempotency_key=str(idem_key),
                            status="synced",
                        )
                    )
                except Exception as exc:  # noqa: BLE001 — surface per-item offline failures
                    message = str(exc)
                    conflict = "409" in message or "already" in message.lower()
                    new_status = "conflict" if conflict else "rejected"
                    if conflict:
                        conflicts += 1
                    cur.execute(
                        """
                        SELECT fac_prod.sp_offline_finish_item(
                          %s, %s, %s, NULL, %s
                        )
                        """,
                        (user_id, outbox_id, new_status, message[:500]),
                    )
                    results.append(
                        OfflineSyncResultItem(
                            outbox_id=int(outbox_id),
                            idempotency_key=str(idem_key),
                            status=new_status,
                            conflict_reason=message[:500],
                        )
                    )
        conn.commit()
    return OfflineSyncOutput(
        processed=len(results),
        synced=synced,
        conflicts=conflicts,
        results=results,
    ).model_dump(mode="json")
