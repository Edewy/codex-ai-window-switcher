"""Optional system tray UI wrapper."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    import pystray
    from PIL import Image
except Exception:  # pylint: disable=broad-except
    pystray = None
    Image = None


class SystemTrayUI:
    """Minimal tray wrapper. Safe to ignore when unavailable."""

    def __init__(self, title: str) -> None:
        self.title = title
        self._icon = None

    def start(self) -> None:
        """Start tray icon when dependency exists."""
        if pystray is None or Image is None:
            logger.info("System tray disabled (pystray/pillow not installed).")
            return
        image = Image.new("RGB", (16, 16), color=(40, 140, 240))
        self._icon = pystray.Icon(self.title, image, self.title)
        self._icon.run_detached()

    def stop(self) -> None:
        """Stop tray icon if running."""
        if self._icon:
            self._icon.stop()
