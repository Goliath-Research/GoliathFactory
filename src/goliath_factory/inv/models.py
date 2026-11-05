"""Compatible overrides of GoliathApp inv action models (subclass required for catalog merge)."""

from __future__ import annotations

from typing import Optional

from goliath_app.inv.models import (
    IssueStockStubInput,
    IssueStockStubOutput,
    ReceiveStockInput,
    ReceiveStockOutput,
)


class MfgReceiveStockInput(ReceiveStockInput):
    """Optional site for ``fac_trace`` lot creation on receipt."""

    site_id: Optional[int] = None


class MfgReceiveStockOutput(ReceiveStockOutput):
    trace_lot_id: Optional[int] = None


class MfgIssueStockOutput(IssueStockStubOutput):
    genealogy_link_id: Optional[int] = None
