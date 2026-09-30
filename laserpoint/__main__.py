from __future__ import annotations

import sys
from typing import List, Optional

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from . import APP_ID, APP_NAME, __version__
from .app import LaserApp
from .config import config_dir
from .icons import app_icon


def _hide_dock_icon() -> None:
    if sys.platform != "darwin":
        return
    try:
        from AppKit import NSApp

        NSApp.setActivationPolicy_(1)
    except Exception:
        pass


def main(argv: Optional[List[str]] = None) -> int:
    args = list(sys.argv if argv is None else argv)
    smoke = "--smoke-test" in args
    if smoke:
        args.remove("--smoke-test")
    if "--version" in args:
        print("%s %s" % (APP_NAME, __version__))
        return 0

    app = QApplication(args)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName("LaserPoint")
    app.setDesktopFileName(APP_ID)
    app.setQuitOnLastWindowClosed(False)

    lock = QLockFile(str(config_dir() / "instance.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(250):
        QMessageBox.information(
            None,
            APP_NAME,
            "%s ya está en ejecución.\nBusca su icono en la bandeja del sistema." % APP_NAME,
        )
        return 0

    _hide_dock_icon()
    controller = LaserApp(app)
    app.setWindowIcon(app_icon(str(controller.cfg["color"])))

    if smoke:
        print("hotkey=%s" % (controller.hotkey.hotkey or "<none>"))
        QTimer.singleShot(250, controller.overlay.activate)
        QTimer.singleShot(850, controller.overlay.deactivate)
        QTimer.singleShot(1150, controller.smoke_settings)
        QTimer.singleShot(
            1750,
            lambda: print(
                "tray=%s active=%s bar=%s"
                % (
                    controller.tray.tray.isVisible(),
                    controller.overlay.is_active,
                    controller.bar.isVisible(),
                )
            ),
        )
        QTimer.singleShot(2000, app.quit)

    code = app.exec()
    controller.shutdown()
    lock.unlock()
    return int(code)
