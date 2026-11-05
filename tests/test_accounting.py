"""Accounting adapter stub tests."""

from __future__ import annotations

from goliath_factory.accounting.erpnext import ErpNextAdapter
from goliath_factory.accounting.quickbooks_online import QuickBooksOnlineAdapter


def test_qbo_health_check_without_env() -> None:
    result = QuickBooksOnlineAdapter().health_check()
    assert result.adapter == "quickbooks_online"
    assert result.ok is False


def test_erpnext_health_check_without_env() -> None:
    result = ErpNextAdapter().health_check()
    assert result.adapter == "erpnext"
    assert result.ok is False
