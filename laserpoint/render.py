from __future__ import annotations

from typing import Iterable, Sequence, Tuple

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient

TrailPoint = Tuple[QPointF, float, float]


def glow_radius(radius: float, shadow: float) -> float:
    return radius * (1.0 + 1.2 * (shadow / 100.0)) + radius * 0.25


def halo_radius(radius: float, shadow: float) -> float:
    return glow_radius(radius, shadow) * 1.35


def _with_alpha(color: QColor, alpha: int) -> QColor:
    out = QColor(color)
    out.setAlpha(max(0, min(255, int(alpha))))
    return out


def _draw_halo(painter: QPainter, center: QPointF, color: QColor, radius: float, shadow: float) -> None:
    strength = shadow / 100.0
    if strength <= 0.02 or radius <= 0:
        return
    r = halo_radius(radius, shadow)
    gradient = QRadialGradient(center, r)
    gradient.setColorAt(0.0, _with_alpha(color, int(110 * strength)))
    gradient.setColorAt(0.55, _with_alpha(color, int(55 * strength)))
    gradient.setColorAt(1.0, _with_alpha(color, 0))
    painter.setBrush(gradient)
    painter.drawEllipse(center, r, r)


def _draw_dot(painter: QPainter, center: QPointF, color: QColor, radius: float, shadow: float) -> None:
    r = glow_radius(radius, shadow)
    strength = shadow / 100.0
    gradient = QRadialGradient(center, r)
    mid = 0.9 - 0.55 * strength
    gradient.setColorAt(0.0, _with_alpha(color, 255))
    gradient.setColorAt(max(0.08, mid), _with_alpha(color, 255 - int(45 * strength)))
    gradient.setColorAt(1.0, _with_alpha(color, 0))
    painter.setBrush(gradient)
    painter.drawEllipse(center, r, r)
    core = _with_alpha(color.lighter(165), 215)
    painter.setBrush(core)
    painter.drawEllipse(center, radius * 0.42, radius * 0.42)


def _draw_ring(painter: QPainter, center: QPointF, color: QColor, radius: float, shadow: float) -> None:
    r = glow_radius(radius, shadow)
    strength = shadow / 100.0
    gradient = QRadialGradient(center, r)
    gradient.setColorAt(0.0, _with_alpha(color, 0))
    gradient.setColorAt(0.38, _with_alpha(color, 0))
    gradient.setColorAt(0.58, _with_alpha(color, 255))
    gradient.setColorAt(0.78, _with_alpha(color, 235 - int(70 * strength)))
    gradient.setColorAt(1.0, _with_alpha(color, 0))
    painter.setBrush(gradient)
    painter.drawEllipse(center, r, r)
    painter.setPen(QPen(_with_alpha(color.lighter(175), 200), max(1.2, radius * 0.12), Qt.PenStyle.SolidLine))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(center, radius * 0.5, radius * 0.5)


def _draw_cross(painter: QPainter, center: QPointF, color: QColor, radius: float, shadow: float) -> None:
    length = glow_radius(radius, shadow) * 1.1
    strength = shadow / 100.0
    base = max(2.0, radius * 0.34)
    layers = (
        (base * (2.4 + strength * 1.4), int(45 + 65 * strength)),
        (base * 1.6, 130),
        (base, 245),
    )
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setCapStyle(Qt.PenCapStyle.RoundCap)
    for width, alpha in layers:
        pen = QPen(_with_alpha(color, alpha), width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QPointF(center.x() - length, center.y()), QPointF(center.x() + length, center.y()))
        painter.drawLine(QPointF(center.x(), center.y() - length), QPointF(center.x(), center.y() + length))
    pen = QPen(_with_alpha(color.lighter(175), 200), max(1.4, base * 0.4), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(QPointF(center.x() - length * 0.55, center.y()), QPointF(center.x() + length * 0.55, center.y()))
    painter.drawLine(QPointF(center.x(), center.y() - length * 0.55), QPointF(center.x(), center.y() + length * 0.55))


def _draw_trail(
    painter: QPainter,
    trail: Iterable[TrailPoint],
    color: QColor,
    radius: float,
    shadow: float,
) -> None:
    for point, factor, life in trail:
        r = radius * (0.35 + 0.65 * factor) * 0.9
        r = max(1.0, r)
        gradient = QRadialGradient(point, r)
        gradient.setColorAt(0.0, _with_alpha(color, int(170 * life)))
        gradient.setColorAt(1.0, _with_alpha(color, 0))
        painter.setBrush(gradient)
        painter.drawEllipse(point, r, r)


def paint_laser(
    painter: QPainter,
    center: QPointF,
    color: QColor,
    radius: float,
    shadow: float,
    shape: str = "dot",
    alpha: float = 1.0,
    trail: Sequence[TrailPoint] = (),
) -> None:
    if radius <= 0 or alpha <= 0.0:
        return
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setOpacity(max(0.0, min(1.0, alpha)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if trail:
        _draw_trail(painter, trail, color, radius, shadow)
    _draw_halo(painter, center, color, radius, shadow)
    if shape == "ring":
        _draw_ring(painter, center, color, radius, shadow)
    elif shape == "cross":
        _draw_cross(painter, center, color, radius, shadow)
    else:
        _draw_dot(painter, center, color, radius, shadow)
    painter.restore()
