"""Pydantic models for mfg ActionSpec inputs and outputs."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkOrderReleaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: int


class WorkOrderReleaseOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: int
    status: str


class TravelerStepStartInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traveler_step_id: int
    machine: str | None = None


class TravelerStepStartOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traveler_step_id: int
    status: str


class TravelerStepSignOffInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traveler_step_id: int
    qty_good: float
    qty_scrap: float = 0.0
    machine: str | None = None
    signature_meaning: str = Field(default="Operation complete")
    record_hash: str | None = None


class TravelerStepSignOffOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traveler_step_id: int
    status: str
    signed_at: str


class InspectionResultRecordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    characteristic_id: int
    lot_id: int | None = None
    work_order_id: int | None = None
    piece_number: int = 1
    measured_value: float | None = None
    pass_fail: Literal["pass", "fail"] | None = None
    gauge_id: int | None = None
    signature_meaning: str = Field(default="Inspection recorded")
    record_hash: str | None = None


class InspectionResultRecordOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inspection_result_id: int
    pass_fail: str


class NcrOpenInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    defect_code: str
    description: str
    part_revision_id: int | None = None
    lot_id: int | None = None
    work_order_id: int | None = None
    containment: str | None = None


class NcrOpenOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ncr_id: int
    status: str


class NcrDispositionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ncr_id: int
    disposition: Literal["use_as_is", "rework", "scrap", "rtv"]
    signature_meaning: str
    record_hash: str | None = None


class NcrDispositionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ncr_id: int
    disposition: str
    status: str


class LotCocGenerateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lot_id: int


class LotCocGenerateOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lot_id: int
    document: dict[str, Any]


class InvIssueToWorkOrderInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: int
    work_order_id: int
    stock_lot_id: int
    quantity: float


class InvIssueToWorkOrderOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: int
    stock_move_id: int
    qty_on_hand: float
    genealogy_link_id: int | None = None


class CapaCloseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capa_id: int
    effectiveness_notes: str
    signature_meaning: str = Field(default="CAPA closed — effectiveness verified")
    record_hash: str | None = None


class CapaCloseOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capa_id: int
    status: str


class GaugeLockoutCheckInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gauge_id: int


class GaugeLockoutCheckOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gauge_id: int
    locked_out: bool


class DocumentSubmitReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: int
    change_summary: str | None = None


class DocumentSubmitReviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: int
    status: str


class DocumentApproveInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: int
    signature_meaning: str = Field(default="Controlled document approved")
    record_hash: str | None = None
    effective_on: date | None = None


class DocumentApproveOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: int
    status: str


class FaiStartInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: int
    inspection_plan_id: int | None = None


class FaiStartOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_article_id: int
    status: str


class FaiApproveInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_article_id: int
    signature_meaning: str = Field(default="First article approved — run released")
    record_hash: str | None = None


class FaiApproveOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_article_id: int
    status: str


class AssetPmCompleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    maintenance_order_id: int
    signature_meaning: str = Field(default="Preventive maintenance completed")
    record_hash: str
    checklist: dict[str, bool] | None = None


class AssetPmCompleteOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    maintenance_order_id: int
    next_due_on: date | None = None


class DowntimeLogInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    asset_id: int | None = None
    work_center_id: int | None = None
    started_at: datetime
    ended_at: datetime | None = None
    reason_code: str
    comments: str | None = None


class DowntimeLogOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    downtime_event_id: int


class CmmRegisterUploadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    source_filename: str
    format: str = "csv"
    storage_ref: str | None = None


class CmmRegisterUploadOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: int
    status: str = "pending"


class MaintPmDueScanInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    within_days: int = 7


class MaintPmDueScanOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    due_asset_count: int


class SpcSummarizeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    characteristic_id: int
    chart_type: str = "xbar_r"
    subgroup_size: int = 5


class SpcSummarizeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    characteristic_id: int
    points_written: int


class CmmImportFileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: int
    site_id: int
    source_filename: str
    format: str = "csv"
    storage_ref: str | None = None


class CmmImportFileOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: int
    rows_inserted: int
