from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPolygonF, QRadialGradient, QPixmap

TRAY_KINDS = ("dot", "ring", "bolt", "star", "cursor")


def _canvas(size: int) -> tuple[QPixmap, QPainter]:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    return pixmap, painter


def _outline(color: QColor = QColor(0, 0, 0, 150)) -> QColor:
    return QColor(color)


def tray_icon(kind: str, color) -> QIcon:
    color = QColor(color)
    pixmap, painter = _canvas(128)
    outline = _outline()
    center = 64.0
    if kind == "ring":
        painter.setPen(QPen(outline, 30, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(center, center), 38, 38)
        painter.setPen(QPen(color, 18, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawEllipse(QPointF(center, center), 38, 38)
    elif kind == "bolt":
        polygon = QPolygonF(
            [
                QPointF(78, 14),
                QPointF(38, 70),
                QPointF(58, 70),
                QPointF(48, 114),
                QPointF(92, 56),
                QPointF(68, 56),
            ]
        )
        painter.setPen(QPen(outline, 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(outline)
        painter.drawPolygon(polygon)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(polygon)
    elif kind == "star":
        outer, inner = 52.0, 22.0
        points = []
        for index in range(10):
            angle = math.radians(-90 + index * 36)
            radius = outer if index % 2 == 0 else inner
            points.append(
                QPointF(center + radius * math.cos(angle), center + radius * math.sin(angle))
            )
        polygon = QPolygonF(points)
        painter.setPen(QPen(outline, 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(outline)
        painter.drawPolygon(polygon)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(polygon)
    elif kind == "cursor":
        polygon = QPolygonF(
            [
                QPointF(34, 20),
                QPointF(34, 102),
                QPointF(56, 82),
                QPointF(70, 112),
                QPointF(86, 104),
                QPointF(72, 76),
                QPointF(98, 74),
            ]
        )
        painter.setPen(QPen(outline, 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(outline)
        painter.drawPolygon(polygon)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(polygon)
    else:
        gradient = QRadialGradient(QPointF(center, center), 58)
        glow = QColor(color)
        glow.setAlpha(210)
        edge = QColor(color)
        edge.setAlpha(0)
        gradient.setColorAt(0.0, glow)
        gradient.setColorAt(0.45, glow)
        gradient.setColorAt(1.0, edge)
        painter.setBrush(gradient)
        painter.drawEllipse(QPointF(center, center), 58, 58)
        painter.setPen(QPen(outline, 7, Qt.PenStyle.SolidLine))
        painter.setBrush(color)
        painter.drawEllipse(QPointF(center, center), 30, 30)
    painter.end()
    return QIcon(pixmap)


def glyph_icon(kind: str, color="#e9eaee", size: int = 64) -> QIcon:
    color = QColor(color)
    pixmap, painter = _canvas(size)
    painter.setPen(QPen(color, size * 0.11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    margin = size * 0.22
    rect = QRectF(margin, margin, size - margin * 2, size - margin * 2)
    if kind == "power":
        painter.drawArc(rect, 60 * 16, -300 * 16)
        painter.drawLine(
            QPointF(size / 2, size * 0.1), QPointF(size / 2, size * 0.46)
        )
    elif kind == "palette":
        painter.setPen(QPen(QColor(0, 0, 0, 160), size * 0.06))
        painter.setBrush(color)
        painter.drawEllipse(QPointF(size / 2, size / 2), size * 0.3, size * 0.3)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 220))
        painter.drawEllipse(QPointF(size * 0.42, size * 0.4), size * 0.08, size * 0.08)
        painter.drawEllipse(QPointF(size * 0.62, size * 0.58), size * 0.07, size * 0.07)
    elif kind == "sliders":
        for index, position in enumerate((0.3, 0.5, 0.7)):
            y = size * position
            painter.drawLine(QPointF(size * 0.2, y), QPointF(size * 0.8, y))
            knob_x = size * (0.35 + 0.15 * index)
            painter.setBrush(QColor(24, 26, 32))
            painter.drawEllipse(QPointF(knob_x, y), size * 0.07, size * 0.07)
            painter.setBrush(Qt.BrushStyle.NoBrush)
    elif kind == "close":
        painter.drawLine(QPointF(size * 0.3, size * 0.3), QPointF(size * 0.7, size * 0.7))
        painter.drawLine(QPointF(size * 0.7, size * 0.3), QPointF(size * 0.3, size * 0.7))
    elif kind == "check":
        painter.drawLine(QPointF(size * 0.25, size * 0.52), QPointF(size * 0.44, size * 0.7))
        painter.drawLine(QPointF(size * 0.44, size * 0.7), QPointF(size * 0.76, size * 0.3))
    painter.end()
    return QIcon(pixmap)


def app_icon(color="#ff3b30") -> QIcon:
    return tray_icon("dot", color)
