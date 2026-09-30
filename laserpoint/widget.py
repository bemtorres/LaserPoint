from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QToolButton, QWidget

from .icons import glyph_icon

BUTTON_STYLE = """
QToolButton {
    background: transparent;
    border: none;
    border-radius: 13px;
    padding: 0px;
}
QToolButton:hover { background: rgba(255, 255, 255, 45); }
QToolButton:pressed { background: rgba(255, 255, 255, 80); }
"""


class ControlBar(QWidget):
    toggle_requested = Signal()
    settings_requested = Signal()
    color_requested = Signal()
    hide_requested = Signal()

    def __init__(self, color: str = "#ff3b30", active: bool = False, parent: QWidget | None = None) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        super().__init__(parent, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowType.WindowTitleHint, False)
        self._color = QColor(color)
        self._active = active
        self._drag_offset: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self._btn_power = self._make_button("power")
        self._btn_color = self._make_button("palette")
        self._btn_settings = self._make_button("sliders")
        self._btn_close = self._make_button("close")

        self._btn_power.clicked.connect(self.toggle_requested)
        self._btn_color.clicked.connect(self.color_requested)
        self._btn_settings.clicked.connect(self.settings_requested)
        self._btn_close.clicked.connect(self.hide_requested)

        layout.addWidget(self._btn_power)
        layout.addWidget(self._btn_color)
        layout.addWidget(self._btn_settings)
        layout.addWidget(self._btn_close)

        self.setStyleSheet(BUTTON_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.set_color(self._color)
        self.set_active(active)

    def _make_button(self, kind: str) -> QToolButton:
        button = QToolButton(self)
        button.setFixedSize(26, 26)
        button.setAutoRaise(True)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setIconSize(QSize(18, 18))
        button.setProperty("glyph", kind)
        return button

    def sizeHint(self):  # type: ignore[no-untyped-def]
        return QSize(140, 42)

    def set_color(self, color) -> None:
        self._color = QColor(color)
        active_color = "#ff5a52" if self._active else "#cfd2d8"
        self._btn_color.setIcon(glyph_icon("palette", self._color.name(), 40))
        self._btn_power.setIcon(glyph_icon("power", active_color, 40))

    def set_active(self, active: bool) -> None:
        self._active = active
        active_color = self._color.name() if active else "#cfd2d8"
        self._btn_power.setIcon(glyph_icon("power", active_color, 40))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(22, 24, 30, 240))
        painter.drawRoundedRect(self.rect(), 13, 13)
        painter.setPen(QPen(QColor(255, 255, 255, 28)))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 13, 13)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)
