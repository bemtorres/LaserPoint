from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .config import Config
from .icons import tray_icon


class TrayController(QObject):
    settings_requested = Signal()
    color_requested = Signal()
    toggle_requested = Signal(bool)
    widget_toggled = Signal(bool)
    autostart_toggled = Signal(bool)
    quit_requested = Signal()

    def __init__(self, cfg: Config, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cfg = cfg
        self._menu = QMenu()
        self._action_power = self._menu.addAction("Puntero encendido")
        self._action_power.setCheckable(True)
        self._action_power.setChecked(False)
        self._action_power.triggered.connect(self.toggle_requested)
        self._action_settings = self._menu.addAction("Configuración…")
        self._action_settings.triggered.connect(self.settings_requested)
        self._action_color = self._menu.addAction("Cambiar color…")
        self._action_color.triggered.connect(self.color_requested)
        self._menu.addSeparator()
        self._action_widget = self._menu.addAction("Barra flotante")
        self._action_widget.setCheckable(True)
        self._action_widget.setChecked(bool(cfg["show_widget"]))
        self._action_widget.triggered.connect(self.widget_toggled)
        self._action_autostart = self._menu.addAction("Iniciar con el sistema")
        self._action_autostart.setCheckable(True)
        self._action_autostart.setChecked(bool(cfg["autostart"]))
        self._action_autostart.triggered.connect(self.autostart_toggled)
        self._menu.addSeparator()
        self._action_quit = self._menu.addAction("Salir")
        self._action_quit.triggered.connect(self.quit_requested)
        self._tray = QSystemTrayIcon()
        self._tray.setContextMenu(self._menu)
        self._tray.setToolTip("LaserPoint")
        self._tray.activated.connect(self._on_activated)
        self.refresh_icon(str(cfg["color"]), str(cfg["tray_icon"]))

    @property
    def tray(self) -> QSystemTrayIcon:
        return self._tray

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def refresh_icon(self, color: str, kind: str) -> None:
        self._tray.setIcon(tray_icon(kind, QColor(color)))
        self._action_color.setIcon(tray_icon("dot", QColor(color)))

    def set_power_checked(self, checked: bool) -> None:
        self._action_power.setChecked(checked)

    def set_widget_checked(self, checked: bool) -> None:
        self._action_widget.setChecked(checked)

    def set_autostart_checked(self, checked: bool) -> None:
        self._action_autostart.setChecked(checked)

    def notify(self, title: str, message: str, milliseconds: int = 5000) -> None:
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, milliseconds)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self.toggle_requested.emit(not self._action_power.isChecked())
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()
