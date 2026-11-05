"""Deployment profile read from ``.goliath/factory-config.json`` (product config)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

CustomerProfile = Literal["precision_shop", "food_processor"]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG_PATH = _REPO_ROOT / ".goliath" / "factory-config.json"


class FactoryProductConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: int
    customerProfile: CustomerProfile


@lru_cache(maxsize=1)
def load_factory_config(path: Path | None = None) -> FactoryProductConfig:
    config_path = path or _DEFAULT_CONFIG_PATH
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return FactoryProductConfig.model_validate(raw)


def fsma_profile_enabled(path: Path | None = None) -> bool:
    return load_factory_config(path).customerProfile == "food_processor"
