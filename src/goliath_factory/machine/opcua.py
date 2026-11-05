"""OPC UA normalized observation stub (no live server connection)."""

from __future__ import annotations

from typing import Any


def parse_opcua_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize a JSON observation pushed by an edge collector.

    Expected keys (all optional): ``asset_tag``, ``availability``, ``execution_state``,
    ``observed_at``, ``node_ids``. Missing mappings are listed in ``incomplete_edges``.
    """
    incomplete: list[str] = []
    asset_tag = payload.get("asset_tag")
    if not asset_tag:
        incomplete.append("asset_tag")

    availability = payload.get("availability")
    if availability is None:
        incomplete.append("availability")

    execution = payload.get("execution_state")
    if execution is None:
        incomplete.append("execution_state")

    node_ids = payload.get("node_ids")
    if not node_ids:
        incomplete.append("opc_node_ids")

    return {
        "asset_tag": asset_tag,
        "availability": availability,
        "execution_state": execution,
        "incomplete_edges": incomplete,
        "raw_payload": {"format": "opcua", "payload": payload},
    }
