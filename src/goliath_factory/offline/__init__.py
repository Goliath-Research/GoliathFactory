"""Offline tablet queue limits and allowed actions."""

from __future__ import annotations

from goliath_factory.offline.policy import (
    ALLOWED_OFFLINE_ACTIONS,
    MAX_PAYLOAD_BYTES,
    MAX_QUEUE_AGE_DAYS,
    MAX_QUEUE_PER_DEVICE,
)

__all__ = [
    "ALLOWED_OFFLINE_ACTIONS",
    "MAX_QUEUE_AGE_DAYS",
    "MAX_PAYLOAD_BYTES",
    "MAX_QUEUE_PER_DEVICE",
]
