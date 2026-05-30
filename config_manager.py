"""Configuration loading and validation for Codex AI window switcher."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Runtime configuration values."""

    codex_window_keywords: List[str]
    target_apps: List[Dict[str, str]]
    api_endpoints: Dict[str, str]
    poll_interval_seconds: float
    request_timeout_seconds: float
    hotkey: str


DEFAULT_CONFIG = {
    "codex_window_keywords": ["Codex", "codex"],
    # TARGET_APP_CONFIG: Add, remove, or rename target applications here.
    "target_apps": [
        {"name": "Browser", "window_keyword": "Chrome"},
        {"name": "IDE", "window_keyword": "Code"},
    ],
    "api_endpoints": {
        "status": "http://127.0.0.1:8765/status",
        "events": "http://127.0.0.1:8765/events",
    },
    "poll_interval_seconds": 1.0,
    "request_timeout_seconds": 3.0,
    "hotkey": "ctrl+alt+c",
}


class ConfigManager:
    """Load and persist JSON configuration."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def ensure_exists(self) -> None:
        """Create an example config file if missing."""
        if self.config_path.exists():
            return

        logger.info("Config file not found, creating default: %s", self.config_path)
        self.config_path.write_text(
            json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self) -> AppConfig:
        """Load configuration from disk and merge with defaults."""
        self.ensure_exists()
        with self.config_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        merged = {**DEFAULT_CONFIG, **raw}
        merged["api_endpoints"] = {
            **DEFAULT_CONFIG["api_endpoints"],
            **raw.get("api_endpoints", {}),
        }

        target_apps = raw.get("target_apps", DEFAULT_CONFIG["target_apps"])
        if not isinstance(target_apps, list) or not target_apps:
            raise ValueError("Configuration 'target_apps' must be a non-empty list.")

        return AppConfig(
            codex_window_keywords=list(merged["codex_window_keywords"]),
            target_apps=list(target_apps),
            api_endpoints=dict(merged["api_endpoints"]),
            poll_interval_seconds=float(merged["poll_interval_seconds"]),
            request_timeout_seconds=float(merged["request_timeout_seconds"]),
            hotkey=str(merged["hotkey"]),
        )
