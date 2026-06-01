"""Configuration loading and validation for multi-session AI window switcher."""

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

    sessions: List["SessionConfig"]
    poll_interval_seconds: float
    request_timeout_seconds: float
    hotkey: str


@dataclass
class SessionConfig:
    """Configuration for a single AI session."""

    name: str
    enabled: bool
    ai_window_keywords: List[str]
    target_apps: List[Dict[str, str]]
    api_endpoints: Dict[str, str]


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
    "sessions": [
        {
            "name": "Codex",
            "enabled": True,
            "ai_window_keywords": ["Codex", "codex"],
            "target_apps": [
                {"name": "Browser", "window_keyword": "Chrome"},
                {"name": "IDE", "window_keyword": "Code"},
            ],
            "api_endpoints": {
                "status": "http://127.0.0.1:8765/status",
                "events": "http://127.0.0.1:8765/events",
            },
        }
    ],
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
        sessions = self._load_sessions(raw, merged)
        return AppConfig(
            sessions=sessions,
            poll_interval_seconds=float(merged["poll_interval_seconds"]),
            request_timeout_seconds=float(merged["request_timeout_seconds"]),
            hotkey=str(merged["hotkey"]),
        )

    def _load_sessions(self, raw: Dict, merged: Dict) -> List[SessionConfig]:
        """Load either new multi-session or legacy single-session configuration."""
        raw_sessions = raw.get("sessions")
        if isinstance(raw_sessions, list) and raw_sessions:
            return [self._load_single_session(session_raw, idx) for idx, session_raw in enumerate(raw_sessions, start=1)]

        logger.info("Using legacy single-session configuration format.")
        return [
            SessionConfig(
                name="Codex",
                enabled=True,
                ai_window_keywords=list(merged["codex_window_keywords"]),
                target_apps=self._validated_target_apps(raw.get("target_apps", DEFAULT_CONFIG["target_apps"])),
                api_endpoints={
                    **DEFAULT_CONFIG["api_endpoints"],
                    **raw.get("api_endpoints", {}),
                },
            )
        ]

    def _load_single_session(self, session_raw: Dict, index: int) -> SessionConfig:
        if not isinstance(session_raw, dict):
            raise ValueError(f"Configuration 'sessions[{index - 1}]' must be an object.")

        name = str(session_raw.get("name", f"Session-{index}")).strip() or f"Session-{index}"
        ai_keywords = session_raw.get("ai_window_keywords", session_raw.get("codex_window_keywords", []))
        if not isinstance(ai_keywords, list) or not ai_keywords:
            raise ValueError(f"Configuration 'sessions[{index - 1}].ai_window_keywords' must be a non-empty list.")

        api_endpoints = {
            **DEFAULT_CONFIG["api_endpoints"],
            **session_raw.get("api_endpoints", {}),
        }
        target_apps = self._validated_target_apps(
            session_raw.get("target_apps", DEFAULT_CONFIG["target_apps"])
        )
        return SessionConfig(
            name=name,
            enabled=bool(session_raw.get("enabled", True)),
            ai_window_keywords=[str(item) for item in ai_keywords if str(item).strip()],
            target_apps=target_apps,
            api_endpoints=api_endpoints,
        )

    @staticmethod
    def _validated_target_apps(target_apps: object) -> List[Dict[str, str]]:
        if not isinstance(target_apps, list) or not target_apps:
            length_display = len(target_apps) if isinstance(target_apps, list) else "N/A"
            raise ValueError(
                "Configuration 'target_apps' must be a non-empty list, "
                f"got type={type(target_apps).__name__}, length={length_display}."
            )
        return list(target_apps)
