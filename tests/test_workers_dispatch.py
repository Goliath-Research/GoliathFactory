"""Worker dispatch tests."""

from __future__ import annotations

from goliath_factory.workers.dispatch import (
    capability_for_action,
    handle,
    known_action_names,
)


def test_known_worker_actions() -> None:
    names = known_action_names()
    assert "mfg.maint.pm_due_scan" in names
    assert "mfg.spc.summarize" in names


def test_capability_mapping() -> None:
    assert capability_for_action("mfg.maint.pm_due_scan") == "mfg.maint"
    assert capability_for_action("mfg.cmm.import_file") == "mfg.cmm"
    assert capability_for_action("mfg.machine.ingest_observation") == "mfg.machine"


def test_pm_scan_without_db() -> None:
    out = handle("mfg.maint.pm_due_scan", {"site_id": 1})
    assert out.get("skipped") is True
