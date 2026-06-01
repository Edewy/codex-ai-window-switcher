"""Thread-safe manager for multiple AI sessions."""

from __future__ import annotations

import logging
import threading
from typing import Callable, Dict, List

from ai_monitor import AIEvent
from ai_session import AISession
from config_manager import AppConfig, SessionConfig


class SessionManager:
    """Lifecycle management for all configured AI sessions."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._lock = threading.RLock()
        self._sessions: Dict[str, AISession] = {}
        self._session_configs: Dict[str, SessionConfig] = {session.name: session for session in config.sessions}
        self._callbacks: List[Callable[[AISession, AIEvent], None]] = []
        self.logger = logging.getLogger(__name__)

    def on_event(self, callback: Callable[[AISession, AIEvent], None]) -> None:
        self._callbacks.append(callback)

    def start_all(self) -> None:
        with self._lock:
            for session in self._config.sessions:
                if session.enabled:
                    self.enable_session(session.name)

    def stop_all(self) -> None:
        with self._lock:
            for name in list(self._sessions.keys()):
                self.disable_session(name)

    def enable_session(self, name: str) -> bool:
        with self._lock:
            if name in self._sessions:
                return False
            session_config = self._session_configs.get(name)
            if not session_config:
                return False
            session = AISession(
                config=session_config,
                poll_interval_seconds=self._config.poll_interval_seconds,
                request_timeout_seconds=self._config.request_timeout_seconds,
            )
            session.on_event(self._forward_event)
            session.start()
            self._sessions[name] = session
            self.logger.info("Session enabled: %s", name)
            return True

    def disable_session(self, name: str) -> bool:
        with self._lock:
            session = self._sessions.pop(name, None)
            if not session:
                return False
            session.stop()
            self.logger.info("Session disabled: %s", name)
            return True

    def restore_session_window(self, name: str) -> bool:
        with self._lock:
            session = self._sessions.get(name)
            if not session:
                return False
            return session.restore_ai_window()

    def restore_all_windows(self) -> bool:
        with self._lock:
            restored = False
            for session in self._sessions.values():
                restored = session.restore_ai_window() or restored
            return restored

    def active_session_names(self) -> List[str]:
        with self._lock:
            return list(self._sessions.keys())

    def status_by_session(self) -> Dict[str, str]:
        with self._lock:
            return {
                name: (session.monitor.last_status or "unknown")
                for name, session in self._sessions.items()
            }

    def _forward_event(self, session: AISession, event: AIEvent) -> None:
        for callback in list(self._callbacks):
            callback(session, event)
