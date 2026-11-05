"""Accounting adapter interface for ERP / GL sync (no live credentials in-repo)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AccountingSyncResult:
    adapter: str
    ok: bool
    detail: dict[str, Any]


class AccountingAdapter(ABC):
    """Sync vendors, items, POs, and receipts to an external accounting system."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def health_check(self) -> AccountingSyncResult:
        """Verify configuration without mutating remote state."""

    @abstractmethod
    def push_purchase_order(self, payload: dict[str, Any]) -> AccountingSyncResult: ...

    @abstractmethod
    def push_receipt(self, payload: dict[str, Any]) -> AccountingSyncResult: ...
