"""QuickBooks Online adapter stub (OAuth + REST — configure via environment)."""

from __future__ import annotations

import os
from typing import Any

from goliath_factory.accounting.interface import AccountingAdapter, AccountingSyncResult


class QuickBooksOnlineAdapter(AccountingAdapter):
    """
    Environment variables (never commit secrets):

    - ``MFG_QBO_CLIENT_ID`` — Intuit app client id
    - ``MFG_QBO_CLIENT_SECRET`` — Intuit app client secret
    - ``MFG_QBO_REFRESH_TOKEN`` — OAuth refresh token for the company
    - ``MFG_QBO_REALM_ID`` — QuickBooks company (realm) id
    - ``MFG_QBO_ENV`` — ``sandbox`` or ``production`` (default sandbox)
    """

    @property
    def name(self) -> str:
        return "quickbooks_online"

    def _configured(self) -> bool:
        return all(
            os.environ.get(key)
            for key in (
                "MFG_QBO_CLIENT_ID",
                "MFG_QBO_CLIENT_SECRET",
                "MFG_QBO_REFRESH_TOKEN",
                "MFG_QBO_REALM_ID",
            )
        )

    def health_check(self) -> AccountingSyncResult:
        if not self._configured():
            return AccountingSyncResult(
                adapter=self.name,
                ok=False,
                detail={"reason": "missing MFG_QBO_* environment variables"},
            )
        return AccountingSyncResult(
            adapter=self.name,
            ok=True,
            detail={"realm_id": os.environ["MFG_QBO_REALM_ID"], "mode": "stub_ready"},
        )

    def push_purchase_order(self, payload: dict[str, Any]) -> AccountingSyncResult:
        check = self.health_check()
        if not check.ok:
            return check
        return AccountingSyncResult(
            adapter=self.name,
            ok=True,
            detail={"action": "push_purchase_order", "stub": True, "payload_keys": list(payload)},
        )

    def push_receipt(self, payload: dict[str, Any]) -> AccountingSyncResult:
        check = self.health_check()
        if not check.ok:
            return check
        return AccountingSyncResult(
            adapter=self.name,
            ok=True,
            detail={"action": "push_receipt", "stub": True, "payload_keys": list(payload)},
        )
