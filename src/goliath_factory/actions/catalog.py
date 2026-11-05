"""Domain ActionSpec catalog for GoliathFactory."""

from __future__ import annotations

from goliath_app.actions.spec import ActionExposure, ActionLevel, ActionSpec

from goliath_factory.actions.models import (
    TravelerStepSignOffInput,
    TravelerStepSignOffOutput,
    WorkOrderReleaseInput,
    WorkOrderReleaseOutput,
)

ACTIONS: list[ActionSpec] = [
    ActionSpec(
        action_name="mfg.work_order.release",
        namespace="mfg",
        level=ActionLevel.DOMAIN,
        entity_code="work_order",
        display_name="Release work order",
        description="Review and release a work order to the shop floor (traveler activation).",
        exposure=ActionExposure.RBAC,
        required_permission="mfg.work_order.release",
        input_model=WorkOrderReleaseInput,
        output_model=WorkOrderReleaseOutput,
        schema_version="1",
        capability="mfg.prod",
        tool="mfg-work-order-release",
    ),
    ActionSpec(
        action_name="mfg.traveler_step.sign_off",
        namespace="mfg",
        level=ActionLevel.DOMAIN,
        entity_code="traveler_step",
        display_name="Sign off traveler step",
        description="Record quantities and sign off the current traveler operation step.",
        exposure=ActionExposure.RBAC,
        required_permission="mfg.traveler.sign",
        input_model=TravelerStepSignOffInput,
        output_model=TravelerStepSignOffOutput,
        schema_version="1",
        capability="mfg.prod",
        tool="mfg-traveler-sign-off",
    ),
]
