"""Cross-platform window lookup and focus switching logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

try:
    import pywinctl
except Exception as exc:  # pylint: disable=broad-except
    pywinctl = None
    _PYWINCTL_IMPORT_ERROR = exc
else:
    _PYWINCTL_IMPORT_ERROR = None

logger = logging.getLogger(__name__)


@dataclass
class WindowRef:
    """Serializable information used to restore a previous window."""

    title: str


class WindowManager:
    """Handles active window detection and focus transfer."""

    def __init__(self, codex_window_keywords: Iterable[str]) -> None:
        self._codex_keywords = [keyword.lower() for keyword in codex_window_keywords]
        self._saved_codex_window: Optional[WindowRef] = None

    def save_codex_window(self) -> None:
        """Capture the current Codex window for later restoration."""
        if pywinctl is None:
            logger.warning("Window backend unavailable: %s", _PYWINCTL_IMPORT_ERROR)
            return

        active = pywinctl.getActiveWindow()
        if not active:
            logger.warning("Unable to identify active window when saving Codex state.")
            return

        title = (active.title or "").strip()
        if self._is_codex_window(title):
            self._saved_codex_window = WindowRef(title=title)
            logger.info("Saved Codex window: %s", title)
            return

        matched = self._find_window_by_keywords(self._codex_keywords)
        if matched:
            self._saved_codex_window = WindowRef(title=matched.title)
            logger.info("Saved Codex window by search: %s", matched.title)
        else:
            logger.warning("Could not find a Codex window matching keywords.")

    def switch_to_target(self, target_keyword: str) -> bool:
        """Switch focus to a target app by title keyword."""
        if pywinctl is None:
            logger.warning("Window backend unavailable: %s", _PYWINCTL_IMPORT_ERROR)
            return False

        window = self._find_window_by_keywords([target_keyword.lower()])
        if not window:
            logger.error("Target application not found for keyword: %s", target_keyword)
            return False

        try:
            window.activate()
            logger.info("Switched to target application: %s", window.title)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to activate target window '%s': %s", window.title, exc)
            return False

    def restore_codex_window(self) -> bool:
        """Restore focus to the previously saved Codex window."""
        if pywinctl is None:
            logger.warning("Window backend unavailable: %s", _PYWINCTL_IMPORT_ERROR)
            return False

        if not self._saved_codex_window:
            logger.warning("No saved Codex window to restore.")
            return False

        windows = pywinctl.getWindowsWithTitle(self._saved_codex_window.title)
        if not windows:
            logger.warning("Saved Codex window no longer exists: %s", self._saved_codex_window.title)
            return False

        try:
            windows[0].activate()
            logger.info("Restored Codex window: %s", windows[0].title)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to restore Codex window: %s", exc)
            return False

    def _is_codex_window(self, title: str) -> bool:
        lowered = title.lower()
        return any(keyword in lowered for keyword in self._codex_keywords)

    @staticmethod
    def _find_window_by_keywords(keywords: Iterable[str]):
        if pywinctl is None:
            return None
        for window in pywinctl.getAllWindows():
            title = (window.title or "").lower()
            if any(keyword in title for keyword in keywords):
                return window
        return None
