"""Machine monitoring adapter stubs (MTConnect / OPC UA)."""

from __future__ import annotations

from goliath_factory.machine.mtconnect import parse_mtconnect_sample
from goliath_factory.machine.opcua import parse_opcua_payload

__all__ = ["parse_mtconnect_sample", "parse_opcua_payload"]
