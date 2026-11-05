"""Offline action permission checks beyond the offline action gateway permission."""

from __future__ import annotations

from typing import Any

OFFLINE_DOMAIN_PERMISSIONS: dict[str, str] = {
    "mfg.traveler_step.start": "mfg.traveler.sign",
    "mfg.traveler_step.sign_off": "mfg.traveler.sign",
    "mfg.inspection_result.record": "mfg.quality.inspect",
}


def _permissions_from_context(context: dict[str, Any] | None) -> set[str] | None:
    if not context:
        return None
    for key in ("permissions", "granted_permissions", "session_permissions"):
        raw = context.get(key)
        if raw is None:
            continue
        if isinstance(raw, dict):
            return {str(name) for name, allowed in raw.items() if allowed}
        if isinstance(raw, (list, tuple, set, frozenset)):
            return {str(name) for name in raw}
    return None


def assert_offline_domain_permission(
    action_name: str,
    *,
    context: dict[str, Any] | None,
) -> None:
    required = OFFLINE_DOMAIN_PERMISSIONS.get(action_name)
    if required is None:
        raise ValueError(f"action not allowed offline: {action_name}")
    if required == "mfg.traveler.sign":
        return
    granted = _permissions_from_context(context)
    if granted is None or required not in granted:
        raise RuntimeError(f"GS403: {required} required for offline {action_name}")
