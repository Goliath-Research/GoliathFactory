"""ERPNext (Frappe) adapter stub — accounting-only REST integration."""

from __future__ import annotations

import os
from typing import Any

from goliath_factory.accounting.interface import AccountingAdapter, AccountingSyncResult


class ErpNextAdapter(AccountingAdapter):
    """
    Environment variables:

    - ``MFG_ERPNEXT_BASE_URL`` — e.g. https://erp.example.com
    - ``MFG_ERPNEXT_API_KEY`` — Frappe API key
    - ``MFG_ERPNEXT_API_SECRET`` — Frappe API secret
    """

    @property
    def name(self) -> str:
        return "erpnext"

    def _configured(self) -> bool:
        return all(
            os.environ.get(key)
            for key in (
                "MFG_ERPNEXT_BASE_URL",
                "MFG_ERPNEXT_API_KEY",
                "MFG_ERPNEXT_API_SECRET",
            )
        )

    def health_check(self) -> AccountingSyncResult:
        if not self._configured():
            return AccountingSyncResult(
                adapter=self.name,
                ok=False,
                detail={"reason": "missing MFG_ERPNEXT_* environment variables"},
            )
        return AccountingSyncResult(
            adapter=self.name,
            ok=True,
            detail={"base_url": os.environ["MFG_ERPNEXT_BASE_URL"], "mode": "stub_ready"},
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
