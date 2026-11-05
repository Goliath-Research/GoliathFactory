"""Offline tablet policy constants (no handler imports)."""

from __future__ import annotations

from typing import Final

ALLOWED_OFFLINE_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "mfg.traveler_step.start",
        "mfg.traveler_step.sign_off",
        "mfg.inspection_result.record",
    }
)

MAX_QUEUE_PER_DEVICE = 100
MAX_PAYLOAD_BYTES = 65_536
MAX_QUEUE_AGE_DAYS = 7
