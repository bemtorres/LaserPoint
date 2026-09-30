from __future__ import annotations

import math
import sys
from collections import deque
from typing import Deque, Tuple

from PySide6.QtCore import QPointF, Qt, QElapsedTimer, QTimer
from PySide6.QtGui import QColor, QCursor, QPainter
from PySide6.QtWidgets import QWidget

from .config import Config
from .render import halo_radius, paint_laser

TRACK_MS = 12
TRAIL_MS = 150
SPEED_REF = 2200.0
MAX_TRAIL = 48


class LaserOverlay(QWidget):
    def __init__(self, cfg: Config, parent: QWidget | None = None) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        super().__init__(parent, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._cfg = cfg
        self._color = QColor(cfg["color"])
        self._shape = str(cfg["shape"])
        self._shadow = float(cfg["shadow"])
        self._opacity = float(cfg["opacity"]) / 100.0
        self._boost = float(cfg["speed_boost"]) / 100.0
        self._trail_on = bool(cfg["trail"])
        self._fade_ms = int(cfg["fade_ms"])
        self._base_radius = float(cfg["size"])
        self._radius = self._base_radius
        self._speed = 0.0
        self._alpha = 0.0
        self._active = False
        self._fading = False
        self._fade_start = 0
        self._last_pos: QPointF | None = None
        self._last_ms = 0
        self._trail: Deque[Tuple[QPointF, float, int]] = deque()
        self._clock = QElapsedTimer()
        self._clock.start()
        self._timer = QTimer(self)
        self._timer.setInterval(TRACK_MS)
        self._timer.timeout.connect(self._tick)
        self.apply_config()
        self._apply_native_flags()

    def _apply_native_flags(self) -> None:
        try:
            win_id = int(self.winId())
        except Exception:
            return
        if sys.platform == "win32" and win_id:
            import ctypes

            user32 = ctypes.windll.user32
            gwl_exstyle = -20
            ws_ex_transparent = 0x00000020
            ws_ex_toolwindow = 0x00000080
            ws_ex_noactivate = 0x08000000
            ws_ex_layered = 0x00080000
            style = user32.GetWindowLongW(win_id, gwl_exstyle)
            user32.SetWindowLongW(
                win_id,
                gwl_exstyle,
                style | ws_ex_transparent | ws_ex_toolwindow | ws_ex_noactivate | ws_ex_layered,
            )
        elif sys.platform == "darwin" and win_id:
            try:
                import objc

                view = objc.objc_object(c_void_p=win_id)
                window = view.window()
                if window is not None:
                    window.setIgnoresMouseEvents_(True)
                    window.setCanBecomeKeyWindow_(False)
                    window.setCanBecomeMainWindow_(False)
            except Exception:
                pass

    def apply_config(self) -> None:
        self._color = QColor(self._cfg["color"])
        self._shape = str(self._cfg["shape"])
        self._shadow = float(self._cfg["shadow"])
        self._opacity = float(self._cfg["opacity"]) / 100.0
        self._boost = float(self._cfg["speed_boost"]) / 100.0
        self._trail_on = bool(self._cfg["trail"])
        self._fade_ms = int(self._cfg["fade_ms"])
        self._base_radius = float(self._cfg["size"])
        max_radius = self._base_radius * (1.0 + self._boost)
        side = int(2 * (halo_radius(max_radius, self._shadow) + 30))
        side = max(280, min(1200, side))
        if side != self.width() or side != self.height():
            self.setFixedSize(side, side)
        self.update()

    @property
    def is_active(self) -> bool:
        return self._active and not self._fading

    def activate(self) -> None:
        self._active = True
        self._fading = False
        self._alpha = 1.0
        self._speed = 0.0
        self._radius = self._base_radius
        self._last_pos = None
        self._trail.clear()
        self.show()
        self._timer.start()
        self._tick()

    def deactivate(self) -> None:
        if not self._active:
            return
        if self._fade_ms <= 0:
            self._stop()
            return
        self._fading = True
        self._fade_start = self._clock.msecsSinceReference()

    def force_hide(self) -> None:
        self._stop()

    def _stop(self) -> None:
        self._active = False
        self._fading = False
        self._alpha = 0.0
        self._trail.clear()
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        now = self._clock.msecsSinceReference()
        pos = QCursor.pos()
        point = QPointF(pos)
        if self._last_pos is None:
            self._last_pos = point
            self._last_ms = now
        else:
            dt = max(6.0, float(now - self._last_ms))
            dx = point.x() - self._last_pos.x()
            dy = point.y() - self._last_pos.y()
            distance = math.hypot(dx, dy)
            instant = distance / dt * 1000.0
            self._speed = self._speed * 0.65 + instant * 0.35
            if self._trail_on and distance > 0.4:
                factor = min(1.0, self._speed / 2400.0)
                self._trail.append((point, factor, int(now)))
                while len(self._trail) > MAX_TRAIL:
                    self._trail.popleft()
            self._last_pos = point
            self._last_ms = now
        alive: Deque[Tuple[QPointF, float, int]] = deque()
        for trail_point, factor, born in self._trail:
            if now - born <= TRAIL_MS:
                alive.append((trail_point, factor, born))
        self._trail = alive
        boost01 = min(self._speed / SPEED_REF, 1.0) if self._boost > 0 else 0.0
        target = self._base_radius * (1.0 + boost01 * self._boost)
        self._radius += (target - self._radius) * 0.4
        if self._fading:
            elapsed = float(now - self._fade_start)
            self._alpha = max(0.0, 1.0 - elapsed / max(1.0, float(self._fade_ms)))
            if self._alpha <= 0.0:
                self._stop()
                return
        else:
            self._alpha = 1.0
        side = self.width()
        x = int(pos.x() - side / 2)
        y = int(pos.y() - side / 2)
        if x != self.x() or y != self.y():
            self.move(x, y)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        cursor = QPointF(QCursor.pos())
        origin = QPointF(float(self.x()), float(self.y()))
        center = cursor - origin
        trail = [
            (point - origin, factor, max(0.0, 1.0 - (self._clock.msecsSinceReference() - born) / TRAIL_MS))
            for point, factor, born in self._trail
        ]
        paint_laser(
            painter,
            center,
            self._color,
            self._radius,
            self._shadow,
            self._shape,
            alpha=self._alpha * self._opacity,
            trail=trail,
        )
