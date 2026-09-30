from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QColorDialog

from . import APP_NAME, autostart
from .config import Config
from .hotkey import HotkeyManager, display_hotkey
from .overlay import LaserOverlay
from .settings import SettingsDialog
from .tray import TrayController
from .widget import ControlBar


class LaserApp(QObject):
    def __init__(self, app: QApplication, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.app = app
        self.cfg = Config()
        self.overlay = LaserOverlay(self.cfg)
        self.hotkey = HotkeyManager(self)
        self.tray = TrayController(self.cfg)
        self.bar = ControlBar(str(self.cfg["color"]), False)
        self._dialog: Optional[SettingsDialog] = None
        self._closed = False

        self.hotkey.activated.connect(self._on_hotkey_press)
        self.hotkey.deactivated.connect(self._on_hotkey_release)
        self.hotkey.failed.connect(self._on_hotkey_failed)

        self.tray.settings_requested.connect(self.open_settings)
        self.tray.color_requested.connect(self.quick_color)
        self.tray.toggle_requested.connect(self.set_persistent)
        self.tray.widget_toggled.connect(self.set_widget_visible)
        self.tray.autostart_toggled.connect(self.set_autostart)
        self.tray.quit_requested.connect(self.quit)

        self.bar.toggle_requested.connect(self.toggle)
        self.bar.settings_requested.connect(self.open_settings)
        self.bar.color_requested.connect(self.quick_color)
        self.bar.hide_requested.connect(lambda: self.set_widget_visible(False))

        bar_pos = self.cfg["bar_pos"]
        if isinstance(bar_pos, (list, tuple)) and len(bar_pos) == 2:
            try:
                self.bar.move(int(bar_pos[0]), int(bar_pos[1]))
            except (TypeError, ValueError):
                pass

        self._sync_autostart()
        self.hotkey.set_hotkey(str(self.cfg["hotkey"]))
        self.tray.show()
        if bool(self.cfg["show_widget"]):
            self.bar.show()

        if not bool(self.cfg["started_before"]):
            self.tray.notify(
                APP_NAME,
                "Listo. Atajo: %s — menú en la bandeja del sistema."
                % display_hotkey(str(self.cfg["hotkey"])),
            )
            self.cfg["started_before"] = True
            self.cfg.save()

    @property
    def mode(self) -> str:
        return str(self.cfg["mode"])

    def _on_hotkey_press(self) -> None:
        if self.mode == "toggle":
            self.toggle()
        else:
            self.activate()

    def _on_hotkey_release(self) -> None:
        if self.mode == "hold":
            self.deactivate()

    def _on_hotkey_failed(self, message: str) -> None:
        self.tray.notify(APP_NAME, message, 7000)

    def activate(self) -> None:
        self.overlay.activate()
        self.tray.set_power_checked(True)
        self.bar.set_active(True)

    def deactivate(self) -> None:
        self.overlay.deactivate()
        self.tray.set_power_checked(False)
        self.bar.set_active(False)

    def toggle(self) -> None:
        if self.overlay.is_active:
            self.deactivate()
        else:
            self.activate()

    def set_persistent(self, checked: bool) -> None:
        if checked:
            self.activate()
        else:
            self.deactivate()

    def quick_color(self) -> None:
        chosen = QColorDialog.getColor(
            QColor(str(self.cfg["color"])), None, "Color del puntero"
        )
        if chosen.isValid():
            self.apply_values({"color": chosen.name()})

    def set_widget_visible(self, visible: bool) -> None:
        self.apply_values({"show_widget": bool(visible)})

    def set_autostart(self, enabled: bool) -> None:
        self.apply_values({"autostart": bool(enabled)})

    def apply_values(self, values: Dict[str, Any]) -> None:
        previous_autostart = bool(self.cfg["autostart"])
        self.cfg.update(values)
        self.overlay.apply_config()
        self.hotkey.set_hotkey(str(self.cfg["hotkey"]))
        self.tray.refresh_icon(str(self.cfg["color"]), str(self.cfg["tray_icon"]))
        self.bar.set_color(str(self.cfg["color"]))
        self.tray.set_widget_checked(bool(self.cfg["show_widget"]))
        if bool(self.cfg["show_widget"]):
            self.bar.show()
        else:
            self.bar.hide()
        if bool(self.cfg["autostart"]) != previous_autostart:
            if not autostart.set_enabled(bool(self.cfg["autostart"])):
                self.cfg["autostart"] = autostart.is_enabled()
                self.tray.notify(APP_NAME, "No se pudo configurar el inicio automático.")
        self.tray.set_autostart_checked(bool(self.cfg["autostart"]))
        self.cfg.save()

    def _sync_autostart(self) -> None:
        try:
            wanted = bool(self.cfg["autostart"])
            if autostart.is_enabled() != wanted:
                autostart.set_enabled(wanted)
        except Exception:
            pass

    def open_settings(self) -> None:
        if self._dialog is not None and self._dialog.isVisible():
            self._dialog.raise_()
            self._dialog.activateWindow()
            return
        dialog = SettingsDialog(self.cfg)
        self._dialog = dialog
        dialog.applied.connect(self.apply_values)
        dialog.exec()
        if self._dialog is dialog:
            self._dialog = None

    def smoke_settings(self) -> None:
        dialog = SettingsDialog(self.cfg)
        self._dialog = dialog
        dialog.show()
        QTimer.singleShot(500, dialog.close)

    def quit(self) -> None:
        self.shutdown()
        self.app.quit()

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            pos = self.bar.pos()
            self.cfg["bar_pos"] = [int(pos.x()), int(pos.y())]
        except Exception:
            pass
        self.cfg.save()
        self.hotkey.stop()
        self.overlay.force_hide()
        self.bar.hide()
        self.tray.hide()
