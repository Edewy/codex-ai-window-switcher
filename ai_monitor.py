"""AI status polling and high-level event dispatch."""

from __future__ import annotations

import logging
import threading
import time
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional

import requests

logger = logging.getLogger(__name__)


class AIEvent(str, Enum):
    """Supported monitor events."""

    REQUEST_STARTED = "request_started"
    RESPONSE_COMPLETED = "response_completed"
    USER_REVIEW_REQUIRED = "user_review_required"
    PERMISSION_REQUIRED = "permission_required"
    ERROR = "error"


class AIMonitor:
    """Poll configured endpoints and emit AI lifecycle events."""

    def __init__(
        self,
        api_endpoints: Dict[str, str],
        poll_interval_seconds: float,
        request_timeout_seconds: float,
    ) -> None:
        self.api_endpoints = api_endpoints
        self.poll_interval_seconds = poll_interval_seconds
        self.request_timeout_seconds = request_timeout_seconds
        self._callbacks: List[Callable[[AIEvent], None]] = []
        self._last_status = None
        self._running = False
        self._thread = None  # type: Optional[threading.Thread]

    def on_event(self, callback: Callable[[AIEvent], None]) -> None:
        """Register an event callback."""
        self._callbacks.append(callback)

    def start(self) -> None:
        """Start background polling."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("AI monitor started.")

    def stop(self) -> None:
        """Stop background polling."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("AI monitor stopped.")

    def _run_loop(self) -> None:
        while self._running:
            try:
                self._poll_once()
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Polling failed: %s", exc)
                self._emit(AIEvent.ERROR)
            time.sleep(self.poll_interval_seconds)

    def _poll_once(self) -> None:
        status_json = self._fetch_json(self.api_endpoints.get("status"))
        events_json = self._fetch_json(self.api_endpoints.get("events"))

        current_status = status_json.get("status")
        if current_status == "processing" and self._last_status != "processing":
            self._emit(AIEvent.REQUEST_STARTED)

        if current_status == "completed" and self._last_status != "completed":
            self._emit(AIEvent.RESPONSE_COMPLETED)

        self._last_status = current_status

        if events_json.get("needs_user_review"):
            self._emit(AIEvent.USER_REVIEW_REQUIRED)
        if events_json.get("permission_required"):
            self._emit(AIEvent.PERMISSION_REQUIRED)
        if events_json.get("error"):
            self._emit(AIEvent.ERROR)

    def _fetch_json(self, url: str) -> Dict:
        if not url:
            return {}
        try:
            response = requests.get(url, timeout=self.request_timeout_seconds)
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.RequestException as exc:
            logger.debug("Request failed for %s: %s", url, exc)
            return {}

    def _emit(self, event: AIEvent) -> None:
        logger.info("AI event emitted: %s", event.value)
        for callback in list(self._callbacks):
            callback(event)

    @property
    def running(self) -> bool:
        """Whether monitoring is currently active."""
        return self._running

    @property
    def last_status(self) -> Optional[str]:
        """Most recently observed status value."""
        return self._last_status

    def simulate_events(self, events: Iterable[AIEvent]) -> None:
        """Helper method for local manual verification."""
        for event in events:
            self._emit(event)
