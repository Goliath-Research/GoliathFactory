"""Handler input validation (no database)."""

from __future__ import annotations

import pytest

from goliath_factory.actions.handlers import (
    handle_inspection_result_record,
    handle_traveler_step_sign_off,
)
from goliath_factory.db import libpq_configured


def test_sign_off_requires_database() -> None:
    if libpq_configured():
        pytest.skip("database configured")
    with pytest.raises(RuntimeError, match="database configuration"):
        handle_traveler_step_sign_off(
            {
                "traveler_step_id": 1,
                "qty_good": 1.0,
            },
            context={"user_id": 1},
        )


def test_inspection_record_requires_database() -> None:
    if libpq_configured():
        pytest.skip("database configured")
    with pytest.raises(RuntimeError, match="database configuration"):
        handle_inspection_result_record(
            {
                "characteristic_id": 1,
                "lot_id": 2,
                "measured_value": 1.0,
                "pass_fail": "pass",
            },
            context={"user_id": 1},
        )
