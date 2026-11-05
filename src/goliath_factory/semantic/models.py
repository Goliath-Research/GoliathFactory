"""Pydantic row and parameter models for the mfg semantic namespace."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class PartRevisionRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part_revision_id: int
    organization_id: int
    part_number: str
    revision: str
    material_spec: Optional[str] = None
    customer: Optional[str] = None
    effectivity_start: Optional[date] = None
    effectivity_end: Optional[date] = None


class RoutingRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    routing_id: int
    part_revision_id: int
    part_number: str
    part_revision: str
    status: str
    revision_label: str
    routing_operation_id: Optional[int] = None
    seq: Optional[int] = None
    operation_code: Optional[str] = None
    description: Optional[str] = None
    work_center_id: Optional[int] = None
    work_center_code: Optional[str] = None
    site_id: Optional[int] = None


class WorkOrderRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: int
    site_id: int
    part_number: str
    part_revision: str
    part_revision_id: int
    routing_id: Optional[int] = None
    quantity: float
    output_lot_id: Optional[int] = None
    due_date: Optional[date] = None
    status: str


class TravelerStepRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traveler_step_id: int
    work_order_id: int
    traveler_id: int
    routing_operation_id: Optional[int] = None
    seq: int
    operation_code: str
    status: str
    operator_user_id: Optional[int] = None
    machine: Optional[str] = None
    qty_good: Optional[float] = None
    qty_scrap: Optional[float] = None
    signed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    signer_user_id: Optional[int] = None
    signature_meaning: Optional[str] = None
    record_hash: Optional[str] = None
    site_id: int


class LotRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lot_id: int
    site_id: int
    lot_number: str
    kind: str
    heat_number: Optional[str] = None
    cert_ref: Optional[str] = None
    created_at: Optional[datetime] = None


class GenealogyRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lot_id: int
    lot_number: str
    kind: str
    depth: int
    direction: str
    link_kind: Optional[str] = None
    related_lot_id: Optional[int] = None
    related_lot_number: Optional[str] = None


class WorkOrderListParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    status: Optional[str] = None
    due_before: Optional[date] = None


class TravelerStepByWorkOrderParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: int


class LotGenealogyParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lot_id: int
    direction: Literal["forward", "backward"] = "forward"


class InspectionPlanRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inspection_plan_id: int
    site_id: int
    part_revision_id: int
    part_number: str
    part_revision: str
    plan_name: str
    plan_status: str
    characteristic_id: Optional[int] = None
    seq: Optional[int] = None
    characteristic_code: Optional[str] = None
    description: Optional[str] = None
    nominal: Optional[float] = None
    tolerance_plus: Optional[float] = None
    tolerance_minus: Optional[float] = None
    unit: Optional[str] = None


class InspectionResultRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inspection_result_id: int
    characteristic_id: int
    characteristic_code: str
    lot_id: Optional[int] = None
    lot_number: Optional[str] = None
    piece_number: int
    measured_value: Optional[float] = None
    pass_fail: str
    inspector_user_id: Optional[int] = None
    recorded_at: Optional[datetime] = None
    site_id: int


class NcrRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ncr_id: int
    site_id: int
    lot_id: Optional[int] = None
    lot_number: Optional[str] = None
    work_order_id: Optional[int] = None
    defect_code: str
    description: str
    containment: Optional[str] = None
    status: str
    opened_at: Optional[datetime] = None
    disposition: Optional[str] = None


class AuditLogRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: int
    site_id: Optional[int] = None
    entity_type: str
    entity_id: int
    action_name: str
    actor_user_id: Optional[int] = None
    signature_meaning: Optional[str] = None
    record_hash: Optional[str] = None
    created_at: Optional[datetime] = None


class InspectionPlanByPartParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    part_revision_id: int


class InspectionResultByLotParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lot_id: int


class NcrListOpenParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    status: Optional[str] = None


class AuditByEntityParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: str
    entity_id: int
    site_id: Optional[int] = None


class CapaRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capa_id: int
    site_id: int
    capa_number: str
    title: str
    root_cause: Optional[str] = None
    status: str
    opened_at: Optional[datetime] = None
    source_ncr_count: int
    open_action_count: int


class CapaListOpenParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    status: Optional[str] = None


class GaugeRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gauge_id: int
    site_id: int
    gauge_tag: str
    gauge_type: str
    location: Optional[str] = None
    next_cal_due_on: Optional[date] = None
    locked_out: bool
    status: str


class GaugeDueCalibrationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    within_days: int = 30


class DocumentRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: int
    site_id: int
    doc_number: str
    title: str
    doc_type: str
    revision_id: Optional[int] = None
    revision: Optional[str] = None
    status: Optional[str] = None
    effective_on: Optional[date] = None


class DocumentListParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    status: Optional[str] = None


class FirstArticleRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_article_id: int
    site_id: int
    work_order_id: int
    part_number: str
    part_revision: str
    status: str
    result_count: int
    qa_approved_at: Optional[datetime] = None


class FirstArticleByWorkOrderParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: int


class AssetRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: int
    site_id: int
    asset_tag: str
    description: Optional[str] = None
    work_center_code: Optional[str] = None
    pm_schedule_name: Optional[str] = None
    next_due_on: Optional[date] = None
    interval_days: Optional[int] = None
    downtime_hours_30d: Optional[float] = None
    status: str


class AssetPmDueParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    within_days: int = 30


class SpcSeriesRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    characteristic_id: int
    characteristic_code: str
    site_id: int
    chart_type: str
    point_index: int
    subgroup_label: Optional[str] = None
    primary_value: float
    secondary_value: Optional[float] = None
    center_line: Optional[float] = None
    ucl: Optional[float] = None
    lcl: Optional[float] = None
    rule_violations: Optional[str] = None


class SpcSeriesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    characteristic_id: int
    chart_type: Literal["xbar_r", "imr"] = "xbar_r"


class FsmaCteRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cte_event_id: int
    site_id: int
    cte_type: str
    event_at: datetime
    lot_id: Optional[int] = None
    lot_number: Optional[str] = None
    traceability_lot_code: str
    product_description: str
    quantity: Optional[float] = None
    quantity_uom: Optional[str] = None
    location_code: Optional[str] = None
    reference_doc_type: Optional[str] = None
    reference_doc_number: Optional[str] = None
    genealogy_link_id: Optional[int] = None
    recorded_by_user_id: Optional[int] = None
    recorded_at: Optional[datetime] = None
    source: str


class FsmaCteByLotParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lot_id: int


class FsmaCteInWindowParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    hours: int = 24
