"""Pydantic models for mfg ActionSpec inputs and outputs."""

from __future__ import annotations

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


class InvReceiveStubInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: int
    item_ref: str
    quantity: float
    lot_number: str | None = None


class InvReceiveStubOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    dependency: str
    detail: dict[str, Any]


class InvIssueToWorkOrderStubInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: int
    stock_lot_ref: str
    quantity: float


class InvIssueToWorkOrderStubOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    dependency: str
    detail: dict[str, Any]
