"""Pluggable accounting adapters (QuickBooks Online, ERPNext)."""

from goliath_factory.accounting.interface import AccountingAdapter, AccountingSyncResult

__all__ = ["AccountingAdapter", "AccountingSyncResult"]
