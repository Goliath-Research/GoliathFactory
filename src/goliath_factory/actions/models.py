"""Pydantic models for mfg ActionSpec stubs (Phase 1)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WorkOrderReleaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: int


class WorkOrderReleaseOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: int
    status: str


class TravelerStepSignOffInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traveler_step_id: int
    qty_good: float
    qty_scrap: float = 0.0
    machine: str | None = None


class TravelerStepSignOffOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traveler_step_id: int
    status: str
    signed_at: str
