"""MTConnect sample adapter (stub)."""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree


def parse_mtconnect_sample(xml_text: str) -> dict[str, Any]:
    """Parse a minimal MTConnect Streams sample document.

    Returns normalized fields for ``fac_maint.sp_machine_record_observation``.
    Documented ``incomplete_edges`` when required elements are missing.
    """
    incomplete: list[str] = []
    root = ElementTree.fromstring(xml_text)
    device_id = None
    availability = None
    execution = None
    for elem in root.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag == "DeviceStream" and device_id is None:
            device_id = elem.attrib.get("name")
        if tag == "Availability" and elem.text and availability is None:
            availability = elem.text.strip()
        if tag in ("Execution", "ProgramExecution") and elem.text and execution is None:
            execution = elem.text.strip()
    if not device_id:
        incomplete.append("device_id")

    if availability is None:
        incomplete.append("availability")
    if execution is None:
        incomplete.append("execution_state")

    return {
        "device_id": device_id,
        "availability": availability,
        "execution_state": execution,
        "incomplete_edges": incomplete,
        "raw_payload": {"format": "mtconnect", "xml_length": len(xml_text)},
    }
