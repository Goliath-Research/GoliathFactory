"""Phase 5 unit tests (no database)."""

from __future__ import annotations

import pytest

from goliath_factory.actions.catalog import ACTIONS
from goliath_factory.config import load_factory_config
from goliath_factory.fsma import FSMA_CSV_HEADER, rows_to_traceability_csv
from goliath_factory.machine import parse_mtconnect_sample, parse_opcua_payload
from goliath_factory.offline.sync import ALLOWED_OFFLINE_ACTIONS
from goliath_factory.workers.dispatch import known_action_names
from goliath_factory.workers.machine_ingest import handle_machine_ingest_observation


def test_factory_config_default_profile() -> None:
    cfg = load_factory_config()
    assert cfg.customerProfile == "precision_shop"


def test_fsma_actions_registered() -> None:
    names = {a.action_name for a in ACTIONS}
    assert "mfg.fsma.record_cte" in names
    assert "mfg.fsma.export_24h" in names


def test_offline_actions_registered() -> None:
    names = {a.action_name for a in ACTIONS}
    assert "mfg.offline.enqueue" in names
    assert "mfg.offline.sync" in names
    assert "mfg.traveler_step.sign_off" in ALLOWED_OFFLINE_ACTIONS


def test_machine_dispatch_registered() -> None:
    assert "mfg.machine.ingest_observation" in known_action_names()


def test_mtconnect_parser_incomplete_edges() -> None:
    parsed = parse_mtconnect_sample("<MTConnectStreams/>")
    assert "device_id" in parsed["incomplete_edges"]
    assert "availability" in parsed["incomplete_edges"]


def test_mtconnect_parser_reads_samples() -> None:
    xml = """
    <MTConnectStreams>
      <DeviceStream name="MILL-1">
        <Availability>UNAVAILABLE</Availability>
        <Execution>ACTIVE</Execution>
      </DeviceStream>
    </MTConnectStreams>
    """
    parsed = parse_mtconnect_sample(xml)
    assert parsed["device_id"] == "MILL-1"
    assert parsed["availability"] == "UNAVAILABLE"
    assert parsed["incomplete_edges"] == []


def test_opcua_parser_flags_missing_nodes() -> None:
    parsed = parse_opcua_payload({"asset_tag": "MILL-1"})
    assert "availability" in parsed["incomplete_edges"]
    assert "opc_node_ids" in parsed["incomplete_edges"]


def test_fsma_csv_helper_sorted_header() -> None:
    csv_text = rows_to_traceability_csv(
        [
            {
                "event_at_utc": "2026-01-01T12:00:00Z",
                "cte_type": "shipping",
                "traceability_lot_code": "TLC-1",
                "product_description": "Berries",
            }
        ]
    )
    lines = csv_text.strip().split("\n")
    assert lines[0].split(",") == list(FSMA_CSV_HEADER)
    assert "shipping" in lines[1]


def test_offline_permission_denies_inspection_without_rbac(monkeypatch: pytest.MonkeyPatch) -> None:
    from goliath_factory.offline import permissions

    monkeypatch.setattr(permissions, "user_has_permission", lambda *_a, **_k: False)
    with pytest.raises(RuntimeError, match="mfg.quality.inspect"):
        permissions.assert_offline_domain_permission(
            "mfg.inspection_result.record",
            context={"user_id": 1},
        )


def test_offline_permission_allows_inspection_with_rbac(monkeypatch: pytest.MonkeyPatch) -> None:
    from goliath_factory.offline import permissions

    def _grant(user_id: int, permission: str, *, cur=None) -> bool:
        assert user_id == 42
        assert permission == "mfg.quality.inspect"
        return True

    monkeypatch.setattr(permissions, "user_has_permission", _grant)
    permissions.assert_offline_domain_permission(
        "mfg.inspection_result.record",
        context={"user_id": 42},
    )


def test_offline_permission_denies_traveler_without_rbac(monkeypatch: pytest.MonkeyPatch) -> None:
    from goliath_factory.offline import permissions

    monkeypatch.setattr(permissions, "user_has_permission", lambda *_a, **_k: False)
    with pytest.raises(RuntimeError, match="mfg.traveler.sign"):
        permissions.assert_offline_domain_permission(
            "mfg.traveler_step.sign_off",
            context={"user_id": 7},
        )


def test_offline_permission_allows_traveler_with_rbac(monkeypatch: pytest.MonkeyPatch) -> None:
    from goliath_factory.offline import permissions

    monkeypatch.setattr(
        permissions,
        "user_has_permission",
        lambda _uid, perm, **_: perm == "mfg.traveler.sign",
    )
    permissions.assert_offline_domain_permission(
        "mfg.traveler_step.start",
        context={"user_id": 7},
    )


def test_machine_ingest_demo_mode() -> None:
    out = handle_machine_ingest_observation(
        {
            "site_id": 1,
            "asset_id": 1,
            "source_protocol": "mtconnect",
            "mtconnect_xml": "<MTConnectStreams><DeviceStream name='A'/></MTConnectStreams>",
        }
    )
    assert out["demo"] is True
    assert out["observation_id"] == 0
