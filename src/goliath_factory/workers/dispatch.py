"""Dispatch mfg DomainProgram actions to in-process handlers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final

from goliath_factory.workers.cmm_import import handle_cmm_import_file
from goliath_factory.workers.machine_ingest import handle_machine_ingest_observation
from goliath_factory.workers.pm_due_scan import handle_pm_due_scan
from goliath_factory.workers.spc_summarize import handle_spc_summarize

HandlerFn = Callable[[dict[str, Any], dict[str, Any] | None], dict[str, Any]]

ACTION_CAPABILITY: Final[dict[str, str]] = {
    "mfg.maint.pm_due_scan": "mfg.maint",
    "mfg.spc.summarize": "mfg.spc",
    "mfg.cmm.import_file": "mfg.cmm",
    "mfg.machine.ingest_observation": "mfg.machine",
}

_ACTION_HANDLERS: Final[dict[str, HandlerFn]] = {
    "mfg.maint.pm_due_scan": lambda payload, ctx=None: handle_pm_due_scan(payload, context=ctx),
    "mfg.spc.summarize": lambda payload, ctx=None: handle_spc_summarize(payload, context=ctx),
    "mfg.cmm.import_file": lambda payload, ctx=None: handle_cmm_import_file(payload, context=ctx),
    "mfg.machine.ingest_observation": lambda payload, ctx=None: handle_machine_ingest_observation(
        payload, context=ctx
    ),
}


def known_action_names() -> frozenset[str]:
    return frozenset(_ACTION_HANDLERS)


def capability_for_action(action_name: str) -> str:
    return ACTION_CAPABILITY[action_name]


def handle(
    action_name: str,
    input_json: dict[str, Any] | None = None,
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {} if input_json is None else dict(input_json)
    handler = _ACTION_HANDLERS[action_name]
    return handler(payload, context)
