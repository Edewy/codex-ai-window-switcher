"""Codex AI auto window switcher entry point."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
import time
from pathlib import Path

from ai_monitor import AIEvent, AIMonitor
from config_manager import ConfigManager
from system_tray import SystemTrayUI
from window_manager import WindowManager

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
    parser = argparse.ArgumentParser(description="Codex AI automatic window switcher")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    args = parser.parse_args()

    configure_logging()
    logger = logging.getLogger("main")

    config = ConfigManager(Path(args.config)).load()
    manager = WindowManager(config.codex_window_keywords)
    monitor = AIMonitor(
        api_endpoints=config.api_endpoints,
        poll_interval_seconds=config.poll_interval_seconds,
        request_timeout_seconds=config.request_timeout_seconds,
    )
    tray = SystemTrayUI(title="Codex Auto Switcher")

    stop_event = threading.Event()

    # TARGET_APP_CONFIG: Choose target app name from config.json target_apps list.
    primary_target = config.target_apps[0].get("window_keyword", "")

    def handle_event(event: AIEvent) -> None:
        if event == AIEvent.REQUEST_STARTED:
            manager.save_codex_window()
            if primary_target:
                manager.switch_to_target(primary_target)
            else:
                logger.warning("No target app configured; skipping switch.")
            return

        if event in {
            AIEvent.RESPONSE_COMPLETED,
            AIEvent.USER_REVIEW_REQUIRED,
            AIEvent.PERMISSION_REQUIRED,
            AIEvent.ERROR,
        }:
            manager.restore_codex_window()

    def stop_handler(*_) -> None:
        stop_event.set()

    monitor.on_event(handle_event)

    if keyboard:
        logger.info("Registering hotkey: %s", config.hotkey)
        keyboard.add_hotkey(config.hotkey, lambda: manager.restore_codex_window())
    else:
        logger.warning("keyboard package unavailable; hotkey disabled.")

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    tray.start()
    monitor.start()
    logger.info("Codex auto switcher started.")

    try:
        while not stop_event.is_set():
            time.sleep(0.2)
    finally:
        monitor.stop()
        tray.stop()
        if keyboard:
            keyboard.unhook_all_hotkeys()
        logger.info("Codex auto switcher stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
