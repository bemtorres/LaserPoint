from __future__ import annotations

import math
from typing import Any, Dict

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .config import DEFAULTS, Config
from .hotkey import display_hotkey, parse_hotkey
from .icons import TRAY_KINDS, app_icon, tray_icon
from .render import paint_laser

TRAY_LABELS = {
    "dot": "Punto",
    "ring": "Anillo",
    "bolt": "Rayo",
    "star": "Estrella",
    "cursor": "Cursor",
}

SHAPE_LABELS = {
    "dot": "Punto relleno",
    "ring": "Anillo",
    "cross": "Cruz",
}

MODE_LABELS = {
    "hold": "Mantener pulsado",
    "toggle": "Alternar (encender/apagar)",
}


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(value.value)


class PreviewWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(120)
        self._color = QColor("#ff3b30")
        self._size = 26.0
        self._shadow = 70.0
        self._shape = "dot"
        self._opacity = 1.0
        self._boost = 1.2
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._animate)
        self._timer.start()

    def set_values(
        self,
        color: str,
        size: int,
        shadow: int,
        shape: str,
        opacity: int,
        boost: int,
    ) -> None:
        self._color = QColor(color)
        self._size = float(size)
        self._shadow = float(shadow)
        self._shape = shape
        self._opacity = opacity / 100.0
        self._boost = boost / 100.0
        self.update()

    def _animate(self) -> None:
        self._phase += 0.16
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(16, 17, 21))
        painter.drawRoundedRect(self.rect(), 10, 10)
        pulse = 0.85 + 0.15 * math.sin(self._phase)
        speed_pulse = 0.12 * (1.0 + self._boost / 2.0) * math.sin(self._phase * 0.6)
        radius = max(4.0, self._size * (1.0 + speed_pulse) * pulse)
        center = self.rect().center()
        painter.setPen(QPen(QColor(255, 255, 255, 30)))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 10, 10)
        paint_laser(
            painter,
            center,
            self._color,
            radius,
            self._shadow,
            self._shape,
            alpha=self._opacity,
        )


class HotkeyEdit(QLineEdit):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.value = ""
        self.setMinimumWidth(230)
        self.setPlaceholderText("Pulsa una combinación de teclas…")

    def set_value(self, text: str) -> None:
        self.value = text
        self.setText(display_hotkey(text) if text else "")

    @staticmethod
    def _mods_list(modifiers: Qt.KeyboardModifiers) -> list[str]:
        mods: list[str] = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            mods.append("ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            mods.append("alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            mods.append("shift")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            mods.append("cmd")
        return mods

    @staticmethod
    def _key_name(key: int) -> str | None:
        if ord("a") <= key <= ord("z"):
            return chr(key)
        if ord("0") <= key <= ord("9"):
            return chr(key)
        if _int(Qt.Key.Key_F1) <= key <= _int(Qt.Key.Key_F24):
            return "f%d" % (key - _int(Qt.Key.Key_F1) + 1)
        mapping = {
            _int(Qt.Key.Key_Space): "space",
            _int(Qt.Key.Key_Escape): "escape",
            _int(Qt.Key.Key_Tab): "tab",
            _int(Qt.Key.Key_Backspace): "backspace",
            _int(Qt.Key.Key_Return): "enter",
            _int(Qt.Key.Key_Enter): "enter",
            _int(Qt.Key.Key_Insert): "insert",
            _int(Qt.Key.Key_Delete): "delete",
            _int(Qt.Key.Key_Home): "home",
            _int(Qt.Key.Key_End): "end",
            _int(Qt.Key.Key_PageUp): "pageup",
            _int(Qt.Key.Key_PageDown): "pagedown",
            _int(Qt.Key.Key_Left): "left",
            _int(Qt.Key.Key_Right): "right",
            _int(Qt.Key.Key_Up): "up",
            _int(Qt.Key.Key_Down): "down",
            _int(Qt.Key.Key_Print): "printscreen",
            _int(Qt.Key.Key_ScrollLock): "scrolllock",
            _int(Qt.Key.Key_Pause): "pause",
            _int(Qt.Key.Key_CapsLock): "capslock",
            _int(Qt.Key.Key_Minus): "-",
            _int(Qt.Key.Key_Equal): "=",
            _int(Qt.Key.Key_BracketLeft): "[",
            _int(Qt.Key.Key_BracketRight): "]",
            _int(Qt.Key.Key_Backslash): "\\",
            _int(Qt.Key.Key_Semicolon): ";",
            _int(Qt.Key.Key_Apostrophe): "'",
            _int(Qt.Key.Key_Comma): ",",
            _int(Qt.Key.Key_Period): ".",
            _int(Qt.Key.Key_Slash): "/",
            _int(Qt.Key.Key_QuoteLeft): "`",
        }
        return mapping.get(key)

    @staticmethod
    def _is_modifier(key: int) -> bool:
        modifiers = (
            _int(Qt.Key.Key_Control),
            _int(Qt.Key.Key_Shift),
            _int(Qt.Key.Key_Alt),
            _int(Qt.Key.Key_Meta),
            _int(Qt.Key.Key_AltGr),
            _int(Qt.Key.Key_Super_L),
            _int(Qt.Key.Key_Super_R),
            _int(Qt.Key.Key_Hyper_L),
            _int(Qt.Key.Key_Hyper_R),
        )
        return key in modifiers

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.isAutoRepeat():
            event.accept()
            return
        key = event.key()
        mods = self._mods_list(event.modifiers())
        if self._is_modifier(key):
            pending = "+".join(mods)
            self.setText((pending + " + …") if pending else "…")
            event.accept()
            return
        if key == _int(Qt.Key.Key_Escape):
            self.set_value("")
            event.accept()
            return
        base = self._key_name(key)
        if base is None:
            event.accept()
            return
        text = "+".join(mods + [base])
        try:
            parse_hotkey(text)
        except ValueError:
            event.accept()
            return
        self.set_value(text)
        event.accept()


class SettingsDialog(QDialog):
    applied = Signal(dict)

    def __init__(self, cfg: Config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("LaserPoint — Configuración")
        self.setWindowIcon(app_icon(cfg["color"]))
        self.setMinimumWidth(560)
        self._cfg = cfg
        self._color = QColor(str(cfg["color"]))

        root = QVBoxLayout(self)
        self._preview = PreviewWidget()
        root.addWidget(self._preview)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs)
        self._tabs.addTab(self._build_appearance_tab(), "Apariencia")
        self._tabs.addTab(self._build_motion_tab(), "Movimiento y tiempo")
        self._tabs.addTab(self._build_system_tab(), "Atajo y sistema")

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.RestoreDefaults
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Aceptar")
        self._buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        self._buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).setText(
            "Valores predeterminados"
        )
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        self._buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self._on_restore
        )
        root.addWidget(self._buttons)

        self._load_values(cfg.data)
        self._sync()

    def _build_appearance_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setSpacing(10)

        self._btn_color = QPushButton()
        self._btn_color.setFixedWidth(140)
        self._btn_color.setFixedHeight(28)
        self._btn_color.clicked.connect(self._pick_color)
        form.addRow("Color del puntero:", self._btn_color)

        self._combo_shape = QComboBox()
        for key, label in SHAPE_LABELS.items():
            self._combo_shape.addItem(label, key)
        self._combo_shape.currentIndexChanged.connect(self._sync)
        form.addRow("Forma:", self._combo_shape)

        self._row_size, self._slider_size, self._spin_size = self._slider_row(8, 80, " px")
        self._spin_size.valueChanged.connect(self._sync)
        self._slider_size.valueChanged.connect(self._sync)
        form.addRow("Tamaño base:", self._row_size)

        self._row_shadow, self._slider_shadow, self._spin_shadow = self._slider_row(0, 100, "%")
        self._spin_shadow.valueChanged.connect(self._sync)
        self._slider_shadow.valueChanged.connect(self._sync)
        form.addRow("Sombra / resplandor:", self._row_shadow)

        self._row_opacity, self._slider_opacity, self._spin_opacity = self._slider_row(30, 100, "%")
        self._spin_opacity.valueChanged.connect(self._sync)
        self._slider_opacity.valueChanged.connect(self._sync)
        form.addRow("Opacidad:", self._row_opacity)

        self._check_trail = QCheckBox("Mostrar rastro de movimiento")
        form.addRow("Rastro:", self._check_trail)
        self._check_trail.toggled.connect(self._sync)

        self._combo_icon = QComboBox()
        self._combo_icon.setIconSize(QSize(28, 28))
        self._repopulate_icons()
        form.addRow("Icono (bandeja):", self._combo_icon)
        self._combo_icon.currentIndexChanged.connect(self._sync)
        return tab

    def _build_motion_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setSpacing(10)

        self._row_boost, self._slider_boost, self._spin_boost = self._slider_row(0, 200, "%")
        self._spin_boost.valueChanged.connect(self._sync)
        self._slider_boost.valueChanged.connect(self._sync)
        form.addRow("Aumento al mover rápido:", self._row_boost)
        hint = QLabel("El puntero crece según la velocidad con la que mueves el ratón.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #8b8f98;")
        form.addRow("", hint)

        self._row_fade, self._slider_fade, self._spin_fade = self._slider_row(0, 3000, " ms", 50)
        self._spin_fade.valueChanged.connect(self._sync)
        self._slider_fade.valueChanged.connect(self._sync)
        form.addRow("Tiempo de desaparición:", self._row_fade)

        self._combo_mode = QComboBox()
        for key, label in MODE_LABELS.items():
            self._combo_mode.addItem(label, key)
        form.addRow("Modo del atajo:", self._combo_mode)
        return tab

    def _build_system_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setSpacing(10)

        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._edit_hotkey = HotkeyEdit()
        self._btn_default_hotkey = QPushButton("Predeterminado")
        self._btn_default_hotkey.clicked.connect(
            lambda: self._edit_hotkey.set_value(str(DEFAULTS["hotkey"]))
        )
        layout.addWidget(self._edit_hotkey, 1)
        layout.addWidget(self._btn_default_hotkey)
        form.addRow("Atajo global:", row)
        hint = QLabel(
            "Haz clic en el campo y pulsa la combinación. Se usa para activar "
            "y desactivar el puntero desde cualquier programa."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #8b8f98;")
        form.addRow("", hint)

        self._check_autostart = QCheckBox("Iniciar automáticamente con el sistema")
        form.addRow("Inicio:", self._check_autostart)

        self._check_widget = QCheckBox("Mostrar la barra flotante de control")
        form.addRow("Barra flotante:", self._check_widget)
        return tab

    def _slider_row(
        self, minimum: int, maximum: int, suffix: str = "", step: int = 1
    ) -> tuple[QWidget, QSlider, QSpinBox]:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSingleStep(step)
        spin.setSuffix(suffix)
        spin.setFixedWidth(86)
        layout.addWidget(slider, 1)
        layout.addWidget(spin)
        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)
        return row, slider, spin

    def _repopulate_icons(self) -> None:
        current = self._combo_icon.currentData() if self._combo_icon.count() else "dot"
        self._combo_icon.blockSignals(True)
        self._combo_icon.clear()
        for kind in TRAY_KINDS:
            self._combo_icon.addItem(
                tray_icon(kind, self._color), TRAY_LABELS.get(kind, kind), kind
            )
        index = self._combo_icon.findData(current)
        self._combo_icon.setCurrentIndex(index if index >= 0 else 0)
        self._combo_icon.blockSignals(False)

    def _pick_color(self) -> None:
        chosen = QColorDialog.getColor(self._color, self, "Color del puntero")
        if chosen.isValid():
            self._color = chosen
            self._repopulate_icons()
            self._sync()

    def _load_values(self, data: Dict[str, Any]) -> None:
        self._color = QColor(str(data.get("color", DEFAULTS["color"])))
        self._combo_shape.setCurrentIndex(
            max(0, self._combo_shape.findData(str(data.get("shape", DEFAULTS["shape"]))))
        )
        self._spin_size.setValue(int(data.get("size", DEFAULTS["size"])))
        self._spin_shadow.setValue(int(data.get("shadow", DEFAULTS["shadow"])))
        self._spin_opacity.setValue(int(data.get("opacity", DEFAULTS["opacity"])))
        self._check_trail.setChecked(bool(data.get("trail", DEFAULTS["trail"])))
        self._repopulate_icons()
        index = self._combo_icon.findData(str(data.get("tray_icon", DEFAULTS["tray_icon"])))
        self._combo_icon.setCurrentIndex(index if index >= 0 else 0)
        self._spin_boost.setValue(int(data.get("speed_boost", DEFAULTS["speed_boost"])))
        self._spin_fade.setValue(int(data.get("fade_ms", DEFAULTS["fade_ms"])))
        self._combo_mode.setCurrentIndex(
            max(0, self._combo_mode.findData(str(data.get("mode", DEFAULTS["mode"]))))
        )
        self._edit_hotkey.set_value(str(data.get("hotkey", DEFAULTS["hotkey"])))
        self._check_autostart.setChecked(bool(data.get("autostart", DEFAULTS["autostart"])))
        self._check_widget.setChecked(bool(data.get("show_widget", DEFAULTS["show_widget"])))

    def _sync(self, *_args: Any) -> None:
        self._btn_color.setStyleSheet(
            "background-color: %s; color: %s; border: 1px solid #55585f; "
            "border-radius: 6px; font-weight: bold; padding: 4px;"
            % (self._color.name(), "#111114" if self._color.lightness() > 140 else "#f2f3f5")
        )
        self._btn_color.setText(self._color.name().upper())
        self._preview.set_values(
            self._color.name(),
            self._spin_size.value(),
            self._spin_shadow.value(),
            str(self._combo_shape.currentData()),
            self._spin_opacity.value(),
            self._spin_boost.value(),
        )

    def values(self) -> Dict[str, Any]:
        return {
            "color": self._color.name(),
            "shape": str(self._combo_shape.currentData()),
            "size": self._spin_size.value(),
            "shadow": self._spin_shadow.value(),
            "opacity": self._spin_opacity.value(),
            "trail": self._check_trail.isChecked(),
            "tray_icon": str(self._combo_icon.currentData()),
            "speed_boost": self._spin_boost.value(),
            "fade_ms": self._spin_fade.value(),
            "mode": str(self._combo_mode.currentData()),
            "hotkey": self._edit_hotkey.value,
            "autostart": self._check_autostart.isChecked(),
            "show_widget": self._check_widget.isChecked(),
        }

    def _on_restore(self) -> None:
        self._load_values(DEFAULTS)
        self._sync()

    def _on_accept(self) -> None:
        if not self._edit_hotkey.value:
            self._edit_hotkey.set_value(str(DEFAULTS["hotkey"]))
        try:
            parse_hotkey(self._edit_hotkey.value)
        except ValueError:
            return
        self.applied.emit(self.values())
        self.accept()
