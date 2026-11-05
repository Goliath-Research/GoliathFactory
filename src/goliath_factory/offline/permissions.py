"""Offline domain permission checks using the same RBAC source as portal semantic reads."""

from __future__ import annotations

from typing import Any

from goliath_factory.db import connect, libpq_configured, user_id_from_context

OFFLINE_DOMAIN_PERMISSIONS: dict[str, str] = {
    "mfg.traveler_step.start": "mfg.traveler.sign",
    "mfg.traveler_step.sign_off": "mfg.traveler.sign",
    "mfg.inspection_result.record": "mfg.quality.inspect",
}


def user_has_permission(
    user_id: int,
    permission: str,
    *,
    cur=None,
) -> bool:
    """Return whether ``user_id`` holds ``permission`` via portal RBAC."""
    if cur is not None:
        cur.execute(
            "SELECT portal.fn_semantic_session_has_permission(%s, %s)",
            (user_id, permission),
        )
        row = cur.fetchone()
        return bool(row and row[0])

    if not libpq_configured():
        raise RuntimeError("database configuration required for permission check")

    with connect() as conn:
        with conn.cursor() as cursor:
            return user_has_permission(user_id, permission, cur=cursor)


def assert_offline_domain_permission(
    action_name: str,
    *,
    context: dict[str, Any] | None,
    cur=None,
) -> None:
    required = OFFLINE_DOMAIN_PERMISSIONS.get(action_name)
    if required is None:
        raise ValueError(f"action not allowed offline: {action_name}")
    user_id = user_id_from_context(context)
    if user_id is None:
        raise RuntimeError("GS401: user required for offline permission check")
    if not user_has_permission(user_id, required, cur=cur):
        raise RuntimeError(f"GS403: {required} required for offline {action_name}")
