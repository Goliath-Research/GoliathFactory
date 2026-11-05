"""Offline tablet sync: idempotent outbox replay into domain actions."""

from __future__ import annotations

from typing import Any

from goliath_factory.offline.policy import ALLOWED_OFFLINE_ACTIONS


def apply_offline_submission(
    action_name: str,
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    if action_name not in ALLOWED_OFFLINE_ACTIONS:
        raise ValueError(f"action not allowed offline: {action_name}")

    from goliath_factory.actions.handlers import (
        handle_inspection_result_record,
        handle_traveler_step_sign_off,
        handle_traveler_step_start,
    )

    handlers = {
        "mfg.traveler_step.start": handle_traveler_step_start,
        "mfg.traveler_step.sign_off": handle_traveler_step_sign_off,
        "mfg.inspection_result.record": handle_inspection_result_record,
    }
    return handlers[action_name](payload, context=context)
