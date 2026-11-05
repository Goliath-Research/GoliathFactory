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
