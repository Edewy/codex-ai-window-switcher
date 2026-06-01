"""Multi-session AI auto window switcher entry point."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
import time
from pathlib import Path

from ai_monitor import AIEvent
from config_manager import ConfigManager
from session_manager import SessionManager
from system_tray import SystemTrayUI

try:
    import keyboard
except Exception:  # pylint: disable=broad-except
    keyboard = None


def configure_logging() -> None:
    """Initialize application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def main() -> int:
    """Application bootstrap and event loop."""
    parser = argparse.ArgumentParser(description="AI automatic window switcher")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    args = parser.parse_args()

    configure_logging()
    logger = logging.getLogger("main")

    config = ConfigManager(Path(args.config)).load()
    session_manager = SessionManager(config)
    tray = SystemTrayUI(title="AI Auto Switcher")

    stop_event = threading.Event()

    def stop_handler(*_) -> None:
        stop_event.set()

    def handle_session_event(session, event: AIEvent) -> None:
        logger.info("Session event %s: %s", session.name, event.value)
        tray.update_sessions_status(session_manager.status_by_session())

    session_manager.on_event(handle_session_event)

    if keyboard:
        logger.info("Registering hotkey: %s", config.hotkey)
        keyboard.add_hotkey(config.hotkey, session_manager.restore_all_windows)
        enabled_session_names = [session.name for session in config.sessions if session.enabled]
        for idx, session_name in enumerate(enabled_session_names, start=1):
            if idx > 9:
                break
            session_hotkey = f"ctrl+alt+{idx}"
            logger.info("Registering session hotkey %s -> %s", session_hotkey, session_name)
            keyboard.add_hotkey(
                session_hotkey,
                lambda name=session_name: session_manager.restore_session_window(name),
            )
    else:
        logger.warning("keyboard package unavailable; hotkey disabled.")

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    tray.start()
    session_manager.start_all()
    tray.update_sessions_status(session_manager.status_by_session())
    logger.info("AI auto switcher started. Active sessions: %s", session_manager.active_session_names())

    try:
        while not stop_event.is_set():
            time.sleep(0.2)
    finally:
        session_manager.stop_all()
        tray.stop()
        if keyboard:
            keyboard.unhook_all_hotkeys()
        logger.info("AI auto switcher stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
