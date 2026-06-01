"""Single AI session runtime orchestration."""

from __future__ import annotations

import logging
import threading
from typing import Callable, List

from ai_monitor import AIEvent, AIMonitor
from config_manager import SessionConfig
from window_manager import WindowManager


class AISession:
    """Owns monitor/window manager and event handling for one AI assistant."""

    def __init__(
        self,
        config: SessionConfig,
        poll_interval_seconds: float,
        request_timeout_seconds: float,
    ) -> None:
        self.config = config
        self.name = config.name
        self.logger = logging.getLogger(f"session.{self.name}")
        self.window_manager = WindowManager(config.ai_window_keywords)
        self.monitor = AIMonitor(
            api_endpoints=config.api_endpoints,
            poll_interval_seconds=poll_interval_seconds,
            request_timeout_seconds=request_timeout_seconds,
        )
        self._target_keywords = [
            app.get("window_keyword", "").strip()
            for app in config.target_apps
            if app.get("window_keyword", "").strip()
        ]
        self._callbacks: List[Callable[["AISession", AIEvent], None]] = []
        self._lock = threading.RLock()
        self.monitor.on_event(self._handle_event)

    def on_event(self, callback: Callable[["AISession", AIEvent], None]) -> None:
        self._callbacks.append(callback)

    def start(self) -> None:
        with self._lock:
            self.monitor.start()
            self.logger.info("Session started.")

    def stop(self) -> None:
        with self._lock:
            self.monitor.stop()
            self.logger.info("Session stopped.")

    def restore_ai_window(self) -> bool:
        with self._lock:
            return self.window_manager.restore_codex_window()

    def _handle_event(self, event: AIEvent) -> None:
        with self._lock:
            self.logger.info("Handling event: %s", event.value)
            if event == AIEvent.REQUEST_STARTED:
                self.window_manager.save_codex_window()
                if not self._target_keywords:
                    self.logger.warning("No target app configured; skipping switch.")
                else:
                    switched = any(
                        self.window_manager.switch_to_target(keyword)
                        for keyword in self._target_keywords
                    )
                    if not switched:
                        self.logger.warning("No configured target window could be activated.")
            elif event in {
                AIEvent.RESPONSE_COMPLETED,
                AIEvent.USER_REVIEW_REQUIRED,
                AIEvent.PERMISSION_REQUIRED,
                AIEvent.ERROR,
            }:
                self.window_manager.restore_codex_window()

            for callback in list(self._callbacks):
                callback(self, event)
