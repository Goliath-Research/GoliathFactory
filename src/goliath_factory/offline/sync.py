"""Offline tablet sync: idempotent outbox replay into domain actions."""

from __future__ import annotations

from typing import Any

from goliath_factory.db import user_id_from_context
from goliath_factory.offline.domain_writes import (
    inspection_result_record_on_cursor,
    traveler_step_sign_off_on_cursor,
    traveler_step_start_on_cursor,
)
from goliath_factory.offline.permissions import assert_offline_domain_permission
from goliath_factory.offline.policy import ALLOWED_OFFLINE_ACTIONS


def apply_offline_submission(
    action_name: str,
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None,
    cur=None,
) -> dict[str, Any]:
    if action_name not in ALLOWED_OFFLINE_ACTIONS:
        raise ValueError(f"action not allowed offline: {action_name}")
    assert_offline_domain_permission(action_name, context=context, cur=cur)

    if cur is not None:
        user_id = user_id_from_context(context)
        if user_id is None:
            raise RuntimeError("action requires authenticated user and database configuration")
        cursor_handlers = {
            "mfg.traveler_step.start": traveler_step_start_on_cursor,
            "mfg.traveler_step.sign_off": traveler_step_sign_off_on_cursor,
            "mfg.inspection_result.record": inspection_result_record_on_cursor,
        }
        return cursor_handlers[action_name](cur, user_id, payload)

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
